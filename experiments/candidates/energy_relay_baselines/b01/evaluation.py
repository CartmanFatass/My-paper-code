"""Owned c00/c06 development evaluation using benchmark B01's controller L."""

from __future__ import annotations

import json
import os
import resource
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    L_CONTROLLER_INFORMATION, SAMPLE_SEED_RULE, TRACE_TIMING, WorldTask, aggregate,
    learner_eval_config, make_eval_config, run_tasks, trace_arrays,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import panel_name
from experiments.candidates.energy_relay_benchmark.b02.training import new_agent
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, optimizer_steps, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import append_progress, write_summary

from .configuration import (
    DEVELOPMENT_WORLDS, DIRECTION, EVALUATED_CHECKPOINTS, MODES, OBJECT_ID,
    PROGRAMME, B02Spec, checkpoint_rollouts, config_dict, make_b02_config,
)

STOCHASTIC_DRAW = 0
HORIZON = 3000


def check_worlds(worlds: Iterable[int], *, expected=DEVELOPMENT_WORLDS) -> tuple[int, ...]:
    worlds = tuple(worlds)
    if worlds != tuple(expected):
        raise ValueError("world list must be exactly the fixed development panel in order")
    return worlds


def validate_checkpoint(*, checkpoint_dir: Path, spec: B02Spec,
                        expected_checkpoint_sha256: str, expected_source_sha: str,
                        horizon: int, validation_scratch: Path) -> dict[str, Any]:
    """Reject foreign/tampered runs and restore the fingerprint before output creation."""
    checkpoint_dir = Path(checkpoint_dir).resolve()
    name = checkpoint_dir.name
    if name not in EVALUATED_CHECKPOINTS:
        raise ValueError("checkpoint must be owned c00 or c06")
    record_path = checkpoint_dir / "record.json"
    if not record_path.is_file():
        raise ValueError("checkpoint record.json is required")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    expected_config = config_dict(make_b02_config(spec))
    if (record.get("object_id"), record.get("direction"), record.get("programme")) != (
            OBJECT_ID, DIRECTION, PROGRAMME):
        raise ValueError("checkpoint record has wrong object/direction/programme identity")
    if record.get("config") != expected_config:
        raise ValueError("recorded config differs from the exact SET recipe")
    if record.get("training_seed") != spec.seed:
        raise ValueError("checkpoint has wrong training seed")
    if record.get("launch_sha") != expected_source_sha:
        raise ValueError("training launch SHA differs from declared source")
    schedule = checkpoint_rollouts(spec)
    index = 0 if name == "c00" else len(schedule)
    rollout = 0 if index == 0 else schedule[-1]
    if (record.get("checkpoint"), record.get("rollout"), record.get("transitions")) != (
            name, rollout, rollout * spec.transitions_per_rollout):
        raise ValueError("checkpoint name, rollout or transitions disagrees with schedule")
    if record.get("agent_pt") != "agent.pt":
        raise ValueError("checkpoint must name agent.pt")
    agent_pt = checkpoint_dir / "agent.pt"
    if not agent_pt.is_file() or agent_pt.stat().st_size != record.get("agent_pt_bytes"):
        raise ValueError("checkpoint bytes differ from record")
    if (record.get("agent_pt_sha256") != expected_checkpoint_sha256
            or sha256_file(agent_pt) != expected_checkpoint_sha256):
        raise ValueError("checkpoint SHA-256 differs from record")
    fingerprint = record.get("policy_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError("invalid policy fingerprint")
    if name == "c00" and any(record.get("optimizer_steps", {}).values()):
        raise ValueError("c00 has optimizer updates")
    if name == "c06" and (record.get("optimizer_steps", {}).get("low_actor", 0) <= 0
                           or record.get("optimizer_steps", {}).get("low_critic", 0) <= 0):
        raise ValueError("c06 lacks low-level optimizer updates")
    config = learner_eval_config(make_eval_config(int(horizon), spec.seed), record)
    with tempfile.TemporaryDirectory(prefix="baseline-validation-",
                                     dir=validation_scratch) as temporary:
        agent, _ = new_agent(config, device=torch.device("cpu"),
                             log_dir=Path(temporary), seed=spec.seed)
        agent.load_model(str(agent_pt))
        if initialization_fingerprint(agent) != fingerprint:
            raise ValueError("restored policy fingerprint differs from checkpoint record")
        if optimizer_steps(agent) != record.get("optimizer_steps"):
            raise ValueError("restored optimizer steps differ from checkpoint record")
    return record


def evaluate_checkpoint(*, checkpoint_dir: Path, out: Path, spec: B02Spec,
                        launch_sha: str, expected_checkpoint_sha256: str,
                        expected_source_sha: str,
                        worlds: Iterable[int] = DEVELOPMENT_WORLDS,
                        expected_worlds=DEVELOPMENT_WORLDS, workers: int = 1,
                        threads: int = 2, device_name: str = "cpu",
                        horizon: int = HORIZON, argv=None) -> dict[str, Any]:
    """Two mode panels, using benchmark B01's unchanged worker and aggregation."""
    worlds = check_worlds(worlds, expected=expected_worlds)
    if workers < 1 or threads < 1 or workers * threads > (os.cpu_count() or 1):
        raise ValueError("workers x threads must fit the CPU")
    out = Path(out)
    checkpoint_dir = Path(checkpoint_dir).resolve()
    if out.resolve() == checkpoint_dir.parent.parent:
        raise ValueError("evaluation output must differ from training output")
    record = validate_checkpoint(checkpoint_dir=checkpoint_dir, spec=spec,
                                 expected_checkpoint_sha256=expected_checkpoint_sha256,
                                 expected_source_sha=expected_source_sha, horizon=horizon,
                                 validation_scratch=out.parent)
    checkpoint = record["checkpoint"]
    root = out / "checkpoint-eval"
    if root.exists():
        raise FileExistsError(f"evaluation scientific output already exists: {root}")
    run_dir = root / f"{checkpoint}_{'-'.join(MODES)}"
    names = {mode: panel_name(checkpoint, mode) for mode in MODES}
    existing = [path for path in (run_dir, *(root / "panels" / f"{name}.json"
                                        for name in names.values()),
                                   *(root / "traces" / f"{name}.npz"
                                     for name in names.values())) if path.exists()]
    if existing:
        raise FileExistsError(f"checkpoint evaluation output already exists: {existing}")
    for directory in (run_dir, root / "panels", root / "traces", root / "logs"):
        directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "direction": DIRECTION, "programme": PROGRAMME,
        "status": "INCOMPLETE", "failure": None, "launch_sha": launch_sha,
        "checkpoint": checkpoint, "policy_seed": spec.seed, "final": False,
        "checkpoint_sha256": expected_checkpoint_sha256,
        "checkpoint_source_sha": expected_source_sha,
        "worlds": list(worlds), "modes": list(MODES),
        "counts": {"episodes_completed": 0, "steps": 0, "panels_completed": 0,
                   "failed_worlds": 0, "new_optimizer_updates": 0},
        "record_optimizer_steps": record["optimizer_steps"],
        "panels": {}, "artifacts": {},
    }
    write_summary(run_dir / "config.json", {
        "object_id": OBJECT_ID, "direction": DIRECTION, "programme": PROGRAMME,
        "launch_sha": launch_sha, "argv": list(sys.argv if argv is None else argv),
        "checkpoint_dir": str(checkpoint_dir), "record": record,
        "checkpoint_sha256": expected_checkpoint_sha256,
        "checkpoint_source_sha": expected_source_sha,
        "worlds": list(worlds), "final": False, "modes": list(MODES),
        "panel_names": names, "feedback": asdict(PRODUCTION_PARAMS),
        "horizon": int(horizon), "policy_seed": spec.seed,
        "stochastic_draw": STOCHASTIC_DRAW, "sample_seed_rule": SAMPLE_SEED_RULE,
        "trace_timing": TRACE_TIMING,
        "controller_information": L_CONTROLLER_INFORMATION, "device": device_name,
        "workers": int(workers), "threads": int(threads), "os_cpu_count": os.cpu_count(),
    })
    summary["artifacts"]["config.json"] = sha256_file(run_dir / "config.json")
    write_summary(run_dir / "summary.json", summary)
    try:
        for mode in MODES:
            name = names[mode]
            panel_started = time.perf_counter()
            draw = STOCHASTIC_DRAW if mode == "stochastic" else None
            tasks = [WorldTask(
                controller="L", seed=seed, params=PRODUCTION_PARAMS, horizon=int(horizon),
                policy_seed=spec.seed, threads=int(threads), device=device_name,
                checkpoint=str(checkpoint_dir / "agent.pt"),
                expected_checkpoint_sha256=record["agent_pt_sha256"],
                expected_policy_fingerprint=record["policy_fingerprint"],
                log_dir=str(root / "logs"), action_mode=mode, draw=draw,
                checkpoint_record=str(checkpoint_dir / "record.json")) for seed in worlds]

            def advance(result):
                row = result["row"]
                summary["counts"]["episodes_completed"] += 1
                summary["counts"]["steps"] += int(row.get("actual_length", 0))
                summary["counts"]["failed_worlds"] += int(bool(row.get("failed")))
                append_progress(run_dir, {"event": "world_end", "panel": name,
                                          "seed": row["seed"],
                                          "failed": bool(row.get("failed"))},
                                dict(summary["counts"]))

            results = run_tasks(tasks, workers, on_result=advance)
            rows = [result["row"] for result in results]
            identities = {json.dumps(result["identity"], sort_keys=True) for result in results}
            panel = {
                "name": name, "controller": "L", "checkpoint": checkpoint,
                "rollout": record["rollout"], "transitions": record["transitions"],
                "controller_information": L_CONTROLLER_INFORMATION,
                "params": asdict(PRODUCTION_PARAMS), "action_mode": mode,
                "draw": draw, "policy_seed": spec.seed, "final": False,
                "worlds": rows, "aggregate": aggregate(rows),
                "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                "policy_identity": [json.loads(item) for item in sorted(identities)],
                "wall_seconds": time.perf_counter() - panel_started,
            }
            if draw is not None:
                panel["sample_seeds"] = {str(row["seed"]): row.get("sample_seed") for row in rows}
            panel_path = root / "panels" / f"{name}.json"
            trace_path = root / "traces" / f"{name}.npz"
            write_summary(panel_path, panel)
            np.savez_compressed(trace_path, **trace_arrays(results))
            for path in (panel_path, trace_path):
                summary["artifacts"][str(path.relative_to(root))] = sha256_file(path)
            summary["panels"][name] = {key: panel[key] for key in panel if key != "worlds"}
            summary["counts"]["panels_completed"] += 1
            write_summary(run_dir / "summary.json", summary)
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        summary.update(wall_seconds=time.perf_counter() - started,
                       peak_rss_kib={"runner": int(own.ru_maxrss),
                                     "largest_worker": int(children.ru_maxrss)},
                       torch_threads_parent=torch.get_num_threads())
        write_summary(run_dir / "summary.json", summary)
