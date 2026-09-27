"""One B01-initialised shield-inactive BC fit and exposed-world evaluation.

The B01 source root is an immutable external artifact on wsl_4070. The entry
point has no source-root override. Isolated tests may pass an internal fixture
root and pins; no source bytes are copied into B02 output.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from experiments.candidates.energy_relay_imitation.b01 import study as b01
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, optimizer_steps, seed_everything, sha256_file,
)
from hmasd.agent import HMASDAgent
from experiments.candidates.energy_relay_benchmark.b02.configuration import config_dict


SOURCE_ROOT = Path("/home/wu/projects/HMASD/runs/energy_relay_imitation/b01_bc_a01")
SOURCE_SHA = "b8cf9d3aace3ac4b386d03190b5a6310ee90acae"
SUMMARY_SHA256 = "ab6c8a3bcaa138434843b70915e7e0bb755551cefd8e673f1a18b2cfb760421e"
INITIAL_SHA256 = "360ab5575f69fe08a5025d61421d0cf51bf1d8702a7b17802b9f94dbe8334b88"
INITIAL_FINGERPRINT = "cb5c15e6d6fbf4e35affb0e33dd9f59915856e5167b8b6a474825324b85cb701"
SELECTED_AGENT_EXPOSURES = 4_846_860
FULL_AGENT_EXPOSURES = 7_680_000
REPLAY_AGENT_EXPOSURES = 1_536_000


@dataclass(frozen=True)
class SourcePins:
    source_sha: str = SOURCE_SHA
    summary_sha256: str = SUMMARY_SHA256
    initial_sha256: str = INITIAL_SHA256
    initial_fingerprint: str = INITIAL_FINGERPRINT


def _verified_file(path: Path, *, expected_sha: str, expected_bytes: int | None = None) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"pinned B01 input absent: {path}")
    size = path.stat().st_size
    if expected_bytes is not None and size != expected_bytes:
        raise ValueError(f"pinned B01 input byte count changed: {path}")
    actual = sha256_file(path)
    if actual != expected_sha:
        raise ValueError(f"pinned B01 input SHA-256 changed: {path}")
    return {"path": str(path), "sha256": actual, "bytes": size}


def validate_source(root: Path, *, pins: SourcePins = SourcePins(),
                    train_worlds=b01.TRAIN_WORLDS, eval_worlds=b01.EVAL_WORLDS,
                    horizon: int = b01.HORIZON) -> tuple[dict, dict]:
    """Verify source summary, record/checkpoint and every raw teacher input."""
    if set(train_worlds) & set(eval_worlds):
        raise ValueError("B01 train/evaluation worlds overlap")
    if any(957001 <= seed <= 957032 for seed in (*train_worlds, *eval_worlds)):
        raise ValueError("sealed holdout worlds are forbidden")
    root = Path(root).resolve(strict=True)
    summary_path = root / "summary.json"
    summary_receipt = _verified_file(summary_path, expected_sha=pins.summary_sha256)
    baseline = json.loads(summary_path.read_text(encoding="utf-8"))
    if baseline.get("status") != "COMPLETE" or baseline.get("launch_sha") != pins.source_sha:
        raise ValueError("pinned B01 summary is incomplete or has another source SHA")
    expected_panels = {"teacher_train": tuple(train_worlds),
                       "teacher_eval": tuple(eval_worlds),
                       "initial_eval": tuple(eval_worlds),
                       "final_eval": tuple(eval_worlds)}
    for panel, worlds in expected_panels.items():
        info = baseline.get("panels", {}).get(panel, {})
        rows = info.get("rows", [])
        if (info.get("planned") != len(worlds) or info.get("completed") != len(worlds)
                or len(rows) != len(worlds) or {row.get("seed") for row in rows} != set(worlds)
                or any(row.get("failed") or row.get("actual_length") != horizon for row in rows)):
            raise ValueError(f"pinned B01 {panel} panel is incomplete or has wrong worlds")
    checkpoint = baseline["checkpoints"]["initial"]
    record = checkpoint["record"]
    artifact = checkpoint["artifact"]
    if (record.get("object_id") != "ENERGY-RELAY-IMITATION-B01"
            or record.get("checkpoint") != "initial"
            or record.get("launch_sha") != pins.source_sha
            or record.get("training_seed") != b01.MODEL_SEED
            or record.get("agent_pt_sha256") != pins.initial_sha256
            or record.get("policy_fingerprint") != pins.initial_fingerprint
            or record.get("optimizer_updates") != 0
            or record.get("agent_transition_exposures") != 0
            or record.get("agent_pt") != "agent.pt"
            or artifact.get("path") != "checkpoints/initial/agent.pt"
            or artifact.get("sha256") != pins.initial_sha256
            or artifact.get("bytes") != record.get("agent_pt_bytes")
            or record.get("config") != config_dict(b01.make_config(horizon=horizon))
            or any(value != 0 for value in record.get("optimizer_steps", {}).values())
            or record.get("optimizer_steps", {}).get("low_actor") != 0):
        raise ValueError("pinned B01 initial checkpoint record differs from fixed initialisation")
    record_path = root / "checkpoints" / "initial" / "record.json"
    if not record_path.is_file():
        raise FileNotFoundError(f"pinned B01 checkpoint record absent: {record_path}")
    if json.loads(record_path.read_text(encoding="utf-8")) != record:
        raise ValueError("B01 initial record file differs from pinned summary")
    record_receipt = {"path": str(record_path), "sha256": sha256_file(record_path),
                      "bytes": record_path.stat().st_size}
    initial_receipt = _verified_file(root / artifact["path"],
                                     expected_sha=pins.initial_sha256,
                                     expected_bytes=record["agent_pt_bytes"])
    raw_receipts = {}
    for panel in ("teacher_train", "teacher_eval"):
        raw_receipts[panel] = {}
        for row in baseline["panels"][panel]["rows"]:
            seed = row["seed"]
            raw = row.get("raw", {})
            relative = f"raw/{panel}/{seed}.npz"
            if raw.get("path") != relative or not isinstance(raw.get("bytes"), int):
                raise ValueError(f"B01 raw locator mismatch: {panel}/{seed}")
            raw_receipts[panel][str(seed)] = _verified_file(
                root / relative, expected_sha=raw["sha256"], expected_bytes=raw["bytes"])
    source = {"root": str(root), "source_launch_sha": pins.source_sha,
              "summary": summary_receipt, "initial_record": record_receipt,
              "initial_checkpoint": initial_receipt,
              "initial_policy_fingerprint": pins.initial_fingerprint,
              "raw_inputs": raw_receipts}
    return baseline, source


def _loaded_initial(root: Path, record: dict, config, *, device: torch.device,
                    log_dir: Path) -> HMASDAgent:
    path = root / "checkpoints" / "initial" / "agent.pt"
    if sha256_file(path) != record["agent_pt_sha256"]:
        raise ValueError("B01 initial checkpoint changed after source validation")
    seed_everything(b01.MODEL_SEED, device)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=device)
    agent.load_model(str(path))
    if initialization_fingerprint(agent) != record["policy_fingerprint"]:
        raise RuntimeError("restored B01 initial fingerprint differs")
    steps = optimizer_steps(agent)
    if steps != record["optimizer_steps"] or any(steps.values()) or agent.discoverer_actor_optimizer.state:
        raise RuntimeError("restored B01 initial actor optimizer is not at step zero")
    agent.train(True)
    return agent


def _save_final(agent, config, out: Path, launch_sha: str, fit: dict, source: dict) -> dict:
    directory = out / "checkpoints" / "final"
    directory.mkdir()
    path = directory / "agent.pt"
    agent.save_model(path)
    record = {"object_id": "ENERGY-RELAY-IMITATION-B02", "programme": "SET-BC-inactive-loss",
              "launch_sha": launch_sha, "checkpoint": "final", "training_seed": b01.MODEL_SEED,
              "optimizer_updates": fit["updates"],
              "agent_transition_exposures": fit["agent_transition_exposures"],
              "selected_loss_agent_exposures": fit["selected_loss_agent_exposures"],
              "policy_fingerprint": initialization_fingerprint(agent),
              "optimizer_steps": optimizer_steps(agent), "config": config_dict(config),
              "source_initial_checkpoint_sha256": source["initial_checkpoint"]["sha256"],
              "agent_pt": "agent.pt", "agent_pt_sha256": sha256_file(path),
              "agent_pt_bytes": path.stat().st_size}
    b01._write_json(directory / "record.json", record)
    return {"record": record, "artifact": b01._artifact(path, out)}


def _paired(baseline: dict, revised: dict, worlds=b01.EVAL_WORLDS) -> dict:
    names = ("teacher_eval", "initial_eval", "final_eval")
    old = {name: {row["seed"]: row for row in baseline["panels"][name]["rows"]}
           for name in names}
    new = {row["seed"]: row for row in revised["panels"]["final_eval"]["rows"]}
    if (set(new) != set(worlds) or any(set(panel) != set(worlds) for panel in old.values())
            or any(row.get("failed") for row in new.values())):
        raise RuntimeError("B02 paired reading requires a complete 32-world final panel")
    fields = {"qos_per_step": "qos_per_step", "raw_native_J": "raw_native_J",
              "return_cost_raw": "return_constraint_cost_raw_sum",
              "minimum_battery": "episode_minimum_battery_ratio",
              "cutoff_penalty": "cutoff_event_penalty_sum",
              "depletion_penalty": "depletion_event_penalty_sum",
              "cutoff_events": "cutoff_event_count_sum",
              "depletion_events": "depletion_event_count_sum"}
    process_fields = ("charger_input_wh", "charging_uav_steps", "feedback_mode_uav_steps",
                      "feedback_entry_count", "feedback_exit_count", "guard_checked_actions",
                      "guard_blocked_actions")
    phase_fields = ("first_service_step", "first_entry_step", "first_input_step",
                    "steps_pre_entry", "steps_entry_to_input", "steps_post_input",
                    "qos_per_step_pre_entry", "qos_per_step_entry_to_input",
                    "qos_per_step_post_input")
    rows = []
    for seed in worlds:
        original = old["final_eval"][seed]
        current = new[seed]
        row = {"seed": seed, "b01_zero_service": original["zero_service"],
               "revised_zero_service": current["zero_service"]}
        for name, field in fields.items():
            row[f"teacher_{name}"] = old["teacher_eval"][seed][field]
            row[f"initial_{name}"] = old["initial_eval"][seed][field]
            row[f"b01_bc_{name}"] = original[field]
            row[f"revised_{name}"] = current[field]
            row[f"revised_minus_b01_bc_{name}"] = current[field] - original[field]
        for field in process_fields:
            row[f"b01_bc_{field}"] = original[field]
            row[f"revised_{field}"] = current[field]
            row[f"revised_minus_b01_bc_{field}"] = current[field] - original[field]
        for field in phase_fields:
            row[f"b01_bc_{field}"] = original[field]
            row[f"revised_{field}"] = current[field]
        rows.append(row)
    def stats(key):
        values = np.asarray([row[key] for row in rows], dtype=np.float64)
        mean = float(values.mean())
        se = float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None
        return {"mean": mean, "world_se": se,
                "descriptive_95pct_interval": [mean - 1.96 * se, mean + 1.96 * se]
                if se is not None else None}
    return {"worlds": rows, "conditional_on_one_initialisation_and_exposed_worlds": True,
            "phase_caveat": "policy-dependent pre-entry, entry-to-input and post-input windows are descriptive, not matched causal phases; first-service means exclude never-served worlds",
            "revised_minus_b01_bc": {name: stats(f"revised_minus_b01_bc_{name}")
                                     for name in fields},
            "revised_zero_service_worlds": [row["seed"] for row in rows
                                             if row["revised_zero_service"]],
            "new_zero_service_worlds": [row["seed"] for row in rows
                                         if row["revised_zero_service"] and not row["b01_zero_service"]],
            "service_loss_worlds": [row["seed"] for row in rows
                                    if row["revised_minus_b01_bc_qos_per_step"] < 0],
            "J_loss_worlds": [row["seed"] for row in rows
                              if row["revised_minus_b01_bc_raw_native_J"] < 0],
            "return_cost_increase_worlds": [row["seed"] for row in rows
                                            if row["revised_minus_b01_bc_return_cost_raw"] > 0],
            "revised_minimum_battery_lower_tail": sorted(
                (new[seed]["episode_minimum_battery_ratio"], seed) for seed in worlds)[:8]}


def run_batch(*, out: Path, launch_sha: str, seed: int = b01.MODEL_SEED,
              source_root: Path = SOURCE_ROOT, pins: SourcePins = SourcePins()) -> dict:
    """Validate immutable B01 inputs, fit once, evaluate one endpoint, replay once."""
    b01.validate_worlds()
    if (seed != b01.MODEL_SEED or len(launch_sha) != 40
            or any(ch not in "0123456789abcdef" for ch in launch_sha)):
        raise ValueError("B02 requires fixed seed and a full lowercase launch SHA")
    # Validation precedes any B02 output creation or scientific use of B01 arrays.
    started = time.perf_counter()
    baseline, source = validate_source(source_root, pins=pins)
    source_validation_seconds = time.perf_counter() - started
    out = Path(out)
    if out.exists():
        if not out.is_dir():
            raise FileExistsError(f"B02 output is not a directory: {out}")
        conflicts = [path.name for path in out.iterdir()
                     if path.name in b01.SCIENTIFIC_OUTPUTS or not b01._native_launcher_file(path)]
        if conflicts:
            raise FileExistsError(f"B02 output contains prior or unknown content: {sorted(conflicts)}")
    out.mkdir(parents=True, exist_ok=True)
    for name in ("raw", "checkpoints", "logs", "per_world"):
        (out / name).mkdir()
    (out / "raw" / "final_eval").mkdir()
    summary = {"status": "INCOMPLETE", "stage": "fit", "launch_sha": launch_sha,
               "started_at_monotonic": started, "source": source,
               "source_validation_seconds": source_validation_seconds,
               "counts": {"episodes_planned": 32, "episodes_completed": 0,
                          "episodes_failed": 0, "native_episodes_completed": 0,
                          "environment_transitions": 0, "environment_transitions_upper_bound": 0,
                          "environment_transitions_exact": True,
                          "failed_worlds_unknown_environment_work": 0,
                          "optimizer_updates": 0, "agent_transition_exposures": 0,
                          "selected_loss_agent_exposures": 0, "skipped_optimizer_chunks": 0,
                          "replay_agent_transitions": 0, "fits_started": 0},
               "failures": [], "panels": {}, "checkpoints": {}, "costs": {}}
    b01._write_json(out / "config.json", {
        "direction": "energy_relay_imitation", "attempt": "b02", "launch_sha": launch_sha,
        "source": source, "model_seed": b01.MODEL_SEED, "order_seed": b01.ORDER_SEED,
        "train_worlds": b01.TRAIN_WORLDS, "exposed_eval_worlds": b01.EVAL_WORLDS,
        "horizon": b01.HORIZON, "workers": b01.WORKERS, "threads_per_worker": 1,
        "thread_environment": {name: os.environ.get(name) for name in b01.THREAD_ENV},
        "epochs": b01.EPOCHS, "episodes_per_group": b01.GROUP, "tbptt": b01.CHUNK,
        "loss_mask": "valid * not recorded shield-active", "loss_denominator": "selected agent-steps * 4",
        "empty_mask": "forward/carry/detach, clear gradients, skip optimizer step",
        "fitting_device": "cuda", "evaluation_device": "cpu",
        "production_shield": {"enter": b01.PRODUCTION_PARAMS.enter_margin,
                              "exit": b01.PRODUCTION_PARAMS.exit_margin},
        "environment_transition_count_semantics": (
            "environment_transitions counts known completed native episode steps; unknown "
            "failed-world work is bounded above by HORIZON per attempted world")})
    b01._write_json(out / "summary.json", summary)
    try:
        torch.set_num_threads(1)
        if not torch.cuda.is_available():
            raise RuntimeError("configured CUDA fitting device unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        config = b01.make_config()
        initial_record = baseline["checkpoints"]["initial"]["record"]
        agent = _loaded_initial(Path(source["root"]), initial_record, config,
                                device=torch.device("cuda"), log_dir=out / "logs")
        summary["counts"]["fits_started"] = 1
        b01._write_json(out / "summary.json", summary)
        summary["fit"] = b01._fit(agent, config, out, summary,
                                  input_root=Path(source["root"]), loss_mask="shield_inactive",
                                  input_hashes=source["raw_inputs"]["teacher_train"])
        fit = summary["fit"]
        if (fit["agent_transition_exposures"] != FULL_AGENT_EXPOSURES
                or fit["selected_loss_agent_exposures"] != SELECTED_AGENT_EXPOSURES
                or fit["updates"] > 1_920):
            raise RuntimeError("B02 fit exposure differs from fixed retained demonstrations")
        summary["checkpoints"]["final"] = _save_final(agent, config, out, launch_sha, fit, source)
        del agent
        torch.cuda.empty_cache()
        summary["stage"] = "evaluation"
        b01._write_json(out / "summary.json", summary)
        record = summary["checkpoints"]["final"]["record"]
        jobs = [b01.Job("final_eval", world,
                        str(out / "checkpoints" / "final" / "agent.pt"),
                        str(out / "checkpoints" / "final" / "record.json"),
                        record["agent_pt_sha256"], record["policy_fingerprint"])
                for world in b01.EVAL_WORLDS]
        if not b01._run_panel(out, jobs, summary):
            raise RuntimeError("B02 final evaluation panel incomplete")
        summary["stage"] = "offline_replay"
        # Revalidate all source bytes at the second scientific-use boundary.
        revalidation_started = time.perf_counter()
        baseline_again, source_again = validate_source(source_root, pins=pins)
        summary["source_revalidation_seconds"] = time.perf_counter() - revalidation_started
        if source_again != source or baseline_again != baseline:
            raise RuntimeError("pinned B01 source changed before offline replay")
        replay_started = time.perf_counter()
        for panel in ("teacher_train", "teacher_eval"):
            summary.setdefault("offline_mse", {})[panel] = b01._replay_checkpoint(
                out, summary["checkpoints"]["final"], panel, summary,
                input_root=Path(source["root"]), input_hashes=source["raw_inputs"][panel])
        summary["offline_replay_seconds"] = time.perf_counter() - replay_started
        summary["paired_readout"] = _paired(baseline, summary)
        counts = summary["counts"]
        if (counts["episodes_completed"] != 32 or counts["episodes_failed"]
                or counts["environment_transitions"] > 96_000
                or counts["replay_agent_transitions"] != REPLAY_AGENT_EXPOSURES):
            raise RuntimeError("B02 actual counts violate fixed endpoint budget")
        summary["status"] = "COMPLETE"
        summary["stage"] = "complete"
    except Exception as exc:
        summary["status"] = "FAILED"
        summary["failures"].append({"stage": summary["stage"],
                                    "error": f"{type(exc).__name__}: {exc}"})
        b01._progress(out, {"event": "study_failed", "stage": summary["stage"]})
    summary["costs"] = b01._costs(out, started)
    summary["costs"]["max_observed_world_worker_peak_rss_kib"] = max(
        (int(row.get("worker_peak_rss_kib", 0)) for panel in summary["panels"].values()
         for row in panel["rows"] if not row.get("failed")), default=None)
    summary.pop("started_at_monotonic")
    b01._write_json(out / "summary.json", summary)
    return summary
