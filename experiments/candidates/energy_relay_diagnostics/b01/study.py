"""Fixed, admitted B01 diagnostic batch on two retained SET checkpoints.

No plan override is exposed. Each spawned process evaluates one H3000 world and writes its
single raw NPZ; only compact rows cross the process boundary. A failed cell is recorded and
never retried. The caller must complete launch admission before importing this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import stat
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_diagnostics.b01.collector import evaluate_collector_task
from experiments.candidates.energy_relay_diagnostics.b01.instrumentation import ActionInputRecorder
from experiments.candidates.energy_relay_diagnostics.b01.readout import (
    action_reading, arrays_digest, read_panels,
)


DIRECTION = "energy_relay_diagnostics"
HORIZON = 3000
POLICY_SEED = 925031
DEV_WORLDS = tuple(range(955001, 955033))
FULL_WORLDS = (955001, 955005, 955016, 955021)
SOURCE_SHA = "759927b5e8caa0ba5bd8ba505ab5388985f6a2fa"
CONFIG_SHA256 = "1b05078fb6e8b898b61bc2829899be615b47a094385169e8acf391ab84de62db"
OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B02"
PROGRAMME = "SET-shield-on-1.2M"
PINS = {
    "c00": {
        "agent_pt_sha256": "9d5806c1ff9d0f94ef4487543104b78ea718c05dc51f10babe808a34087f73f9",
        "policy_fingerprint": "58a6a8a13217c8126a4eca73d02cbfa610433005a21e8e68756559318c9bf333",
        "rollout": 0, "transitions": 0,
    },
    "c03": {
        "agent_pt_sha256": "80b2bdadddb76a4c03fe9fea8ae9fb1317a136363d28dec0d8fae350745dcce4",
        "policy_fingerprint": "4667fdc9df9486167a9820ffc3433a5c6d4b8fe568b21e6fbc3c1326aca4ff3b",
        "rollout": 100, "transitions": 600_000,
    },
}
ACTION_KEYS = (
    "proposal_t", "submitted_t", "actor_mean_raw", "actor_scale_raw",
    "own_xyz_t", "own_xyz_t1", "held_source_t", "held_age",
)
PANEL_LAYOUT = (
    ("c00_eval_stochastic_d0", "c00", "stochastic", 0, False, DEV_WORLDS),
    ("c03_eval_stochastic_d0", "c03", "stochastic", 0, False, DEV_WORLDS),
    ("c03_eval_deterministic", "c03", "deterministic", None, False, DEV_WORLDS),
    ("c03_eval_stochastic_d1", "c03", "stochastic", 1, False, DEV_WORLDS),
    ("c00_collector_stochastic_d0", "c00", "stochastic", 0, True, FULL_WORLDS),
    ("c03_collector_stochastic_d0", "c03", "stochastic", 0, True, FULL_WORLDS),
)


@dataclass(frozen=True)
class Job:
    panel: str
    checkpoint: str
    seed: int
    action_mode: str
    draw: int | None
    collector: bool
    capture_inputs: bool


def fixed_plan() -> tuple[Job, ...]:
    jobs = []
    for panel, checkpoint, mode, draw, collector, worlds in PANEL_LAYOUT:
        for seed in worlds:
            capture_inputs = (panel in ("c03_eval_deterministic", "c03_eval_stochastic_d0")
                              and seed in FULL_WORLDS)
            jobs.append(Job(panel, checkpoint, seed, mode, draw, collector,
                            capture_inputs))
    return tuple(jobs)


_ALLOWED_JOBS = frozenset(fixed_plan())


def validate_job(job: Job) -> None:
    if 957001 <= int(job.seed) <= 957032:
        raise ValueError("sealed holdout is forbidden in diagnostics")
    if job not in _ALLOWED_JOBS:
        raise ValueError(f"world/panel outside frozen diagnostic plan: {job!r}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_checkpoints(root: Path) -> dict[str, dict[str, Any]]:
    """Read only c00/c03 record and model files; refuse all mismatches before output."""
    root = Path(root).resolve(strict=True)
    records = {}
    for name, pin in PINS.items():
        directory = root / name
        record_path, agent_path = directory / "record.json", directory / "agent.pt"
        if not record_path.is_file() or not agent_path.is_file():
            raise ValueError(f"{name} needs record.json and agent.pt")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        expected = {
            "object_id": OBJECT_ID, "programme": PROGRAMME, "launch_sha": SOURCE_SHA,
            "checkpoint": name, "agent_pt": "agent.pt", "training_seed": POLICY_SEED,
            **pin,
        }
        mismatches = {key: (record.get(key), value) for key, value in expected.items()
                      if record.get(key) != value}
        if mismatches:
            raise ValueError(f"{name} checkpoint record differs from pinned identity: {mismatches}")
        config = record.get("config")
        if not isinstance(config, dict):
            raise ValueError(f"{name} checkpoint has no config object")
        config_hash = hashlib.sha256(json.dumps(
            config, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        if config_hash != CONFIG_SHA256:
            raise ValueError(f"{name} config digest differs from pinned B02 config")
        actual_hash = _sha256_file(agent_path)
        if actual_hash != pin["agent_pt_sha256"]:
            raise ValueError(f"{name} agent.pt actual SHA-256 differs from pinned checkpoint")
        actual_bytes = agent_path.stat().st_size
        if record.get("agent_pt_bytes") != actual_bytes:
            raise ValueError(f"{name} agent.pt size differs from record")
        records[name] = {"record": record, "directory": str(directory),
                         "agent_pt_sha256": actual_hash, "agent_pt_bytes": actual_bytes,
                         "config_sha256": config_hash}
    return records


def _native_signature(arrays: dict) -> dict[str, tuple[str, tuple[int, ...]]]:
    return {key: (np.asarray(value).dtype.str, tuple(np.asarray(value).shape[1:]))
            for key, value in arrays.items()}


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"non-compact JSON value: {type(value).__name__}")


def _write_json(path: Path, value) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2, allow_nan=False,
                         default=_json_default).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(payload)
    os.replace(temporary, path)


def _append_progress(out: Path, event: dict) -> None:
    with (out / "progress.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, allow_nan=False,
                                default=_json_default) + "\n")


def _run_job(job: Job, records: dict, out: str, threads: int) -> dict:
    validate_job(job)
    checkpoint = records[job.checkpoint]
    directory = Path(checkpoint["directory"])
    task = ev.WorldTask(
        controller="L", seed=job.seed, params=PRODUCTION_PARAMS, horizon=HORIZON,
        policy_seed=POLICY_SEED, threads=threads, device="cpu",
        checkpoint=str(directory / "agent.pt"),
        expected_checkpoint_sha256=checkpoint["agent_pt_sha256"],
        expected_policy_fingerprint=PINS[job.checkpoint]["policy_fingerprint"],
        checkpoint_record=str(directory / "record.json"), log_dir=str(Path(out) / "logs"),
        action_mode=job.action_mode, draw=job.draw,
    )
    if job.collector:
        result = evaluate_collector_task(task, capture_inputs=job.capture_inputs)
    else:
        result = ev.evaluate_task(
            task, observer_factory=lambda _: ActionInputRecorder(
                capture_inputs=job.capture_inputs,
                capture_held_snapshot=job.capture_inputs),
        )
    row = dict(result["row"])
    if row.get("failed") or row.get("actual_length", 0) < 1 or row["actual_length"] > HORIZON:
        raise RuntimeError(f"{job.panel}/{job.seed} has no valid complete native episode")
    observations = result["observation"]
    if not all(key in observations for key in ACTION_KEYS):
        raise RuntimeError("actor/action observation is incomplete")
    reading = action_reading(result)
    native_digest = arrays_digest(result["arrays"])
    action_digest = arrays_digest({key: observations[key] for key in ACTION_KEYS})
    signature = _native_signature(result["arrays"])
    raw = {**result["arrays"], **{f"obs_{key}": value for key, value in observations.items()}}
    relative = Path("raw") / job.panel / f"{job.seed}.npz"
    destination = Path(out) / relative
    with destination.open("xb") as stream:
        np.savez_compressed(stream, **raw)
    row.update(
        checkpoint=job.checkpoint,
        checkpoint_sha256=checkpoint["agent_pt_sha256"],
        policy_fingerprint=PINS[job.checkpoint]["policy_fingerprint"],
        config_sha256=checkpoint["config_sha256"],
        original_training_sha=SOURCE_SHA,
        new_optimizer_updates=0,
        new_updates=0,
        native_digest=native_digest,
        action_digest=action_digest,
        raw_path=relative.as_posix(),
        raw_sha256=_sha256_file(destination),
        raw_bytes=destination.stat().st_size,
        raw_allocated_bytes=destination.stat().st_blocks * 512,
        native_signature=signature,
        **reading,
    )
    return row


def _costs(started: float, out: Path, rows: list[dict]) -> dict:
    parent = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    allocated = 0
    telemetry_error = None
    try:
        for path in out.rglob("*"):
            info = path.stat()
            if stat.S_ISREG(info.st_mode):
                allocated += info.st_blocks * 512
    except OSError as exc:
        # Cost telemetry must not abort collection or invalidate native outcomes.
        allocated = None
        telemetry_error = type(exc).__name__
    return {
        "parent_wall_seconds": time.perf_counter() - started,
        "parent_cpu_user_seconds": parent.ru_utime,
        "parent_cpu_system_seconds": parent.ru_stime,
        "parent_peak_rss_kib": parent.ru_maxrss,
        "children_cpu_user_seconds": children.ru_utime,
        "children_cpu_system_seconds": children.ru_stime,
        "children_peak_rss_kib_max_child": children.ru_maxrss,
        "max_world_observed_worker_peak_rss_kib": max(
            (int(row.get("worker_peak_rss_kib", 0)) for row in rows), default=None),
        "raw_logical_bytes": sum(int(row.get("raw_bytes", 0)) for row in rows),
        "raw_allocated_bytes": sum(int(row.get("raw_allocated_bytes", 0)) for row in rows),
        "output_allocated_bytes": allocated,
        "output_bytes_telemetry": "measured" if telemetry_error is None else "resources_unmeasured",
        "output_bytes_telemetry_error": telemetry_error,
    }


def run_batch(*, checkpoint_root: Path, out: Path, launch_sha: str,
              workers: int = 4, threads: int = 1) -> dict:
    """Run the fixed 136-world, zero-fit protocol after caller admission."""
    if workers < 1 or threads < 1 or workers * threads > (os.cpu_count() or 1):
        raise ValueError("workers x threads must be positive and within os.cpu_count()")
    if len(launch_sha) != 40 or any(ch not in "0123456789abcdef" for ch in launch_sha):
        raise ValueError("launch_sha must be a lowercase full Git SHA")
    jobs = fixed_plan()
    if len(jobs) != 136 or len(set(jobs)) != len(jobs):
        raise RuntimeError("frozen diagnostic plan does not contain 136 distinct episodes")
    for job in jobs:
        validate_job(job)
    records = validate_checkpoints(checkpoint_root)
    out = Path(out)
    if out.exists() and not out.is_dir():
        raise FileExistsError(f"diagnostic output is not a directory: {out}")
    science_paths = ("config.json", "summary.json", "progress.jsonl", "raw", "per_world",
                     "panels", "logs")
    existing = [name for name in science_paths if (out / name).exists()]
    if existing:
        raise FileExistsError(f"diagnostic science output already exists: {existing}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir()
    (out / "raw").mkdir()
    (out / "per_world").mkdir()
    (out / "panels").mkdir()
    for name, *_ in PANEL_LAYOUT:
        (out / "raw" / name).mkdir()
        (out / "per_world" / name).mkdir()
    started = time.perf_counter()
    config = {
        "direction": DIRECTION, "launch_sha": launch_sha, "horizon": HORIZON,
        "policy_seed": POLICY_SEED, "device": "cpu", "workers": workers, "threads": threads,
        "fits": 0, "new_optimizer_updates": 0,
        "checkpoint_root": str(Path(checkpoint_root).resolve()),
        "checkpoint_pins": {name: {"record": item["record"],
                                   "agent_pt_sha256": item["agent_pt_sha256"],
                                   "config_sha256": item["config_sha256"]}
                            for name, item in records.items()},
        "plan": [asdict(job) for job in jobs],
    }
    _write_json(out / "config.json", config)
    summary = {"status": "INCOMPLETE", "launch_sha": launch_sha,
               "counts": {"episodes_planned": len(jobs), "episodes_completed": 0,
                          "episodes_failed": 0, "actual_transitions": 0, "steps": 0,
                          "new_optimizer_updates": 0, "new_updates": 0, "fits": 0},
               "failures": [], "panels": {}, "costs": {}}
    _write_json(out / "summary.json", summary)
    rows_by_panel = {name: [] for name, *_ in PANEL_LAYOUT}
    all_rows = []
    schema = None
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as pool:
        futures = {pool.submit(_run_job, job, records, str(out), threads): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                row = future.result()
                signature = row.pop("native_signature")
                if schema is None:
                    schema = signature
                elif signature != schema:
                    raise ValueError("native keys/dtypes/shapes differ between evaluator and collector")
                rows_by_panel[job.panel].append(row)
                all_rows.append(row)
                summary["counts"]["episodes_completed"] += 1
                summary["counts"]["actual_transitions"] += int(row["actual_length"])
                summary["counts"]["steps"] += int(row["actual_length"])
                _write_json(out / "per_world" / job.panel / f"{job.seed}.json", row)
                _append_progress(out, {"event": "world_complete", "panel": job.panel,
                                       "seed": job.seed, "actual_length": row["actual_length"]})
            except Exception as exc:
                failure = {"panel": job.panel, "seed": job.seed,
                           "error": f"{type(exc).__name__}: {exc}"}
                summary["failures"].append(failure)
                summary["counts"]["episodes_failed"] += 1
                _write_json(out / "per_world" / job.panel / f"{job.seed}.json", failure)
                _append_progress(out, {"event": "world_failed", **failure})
            summary["costs"] = _costs(started, out, all_rows)
            _write_json(out / "summary.json", summary)
    for name, *_ in PANEL_LAYOUT:
        rows = sorted(rows_by_panel[name], key=lambda row: row["seed"])
        _write_json(out / "panels" / f"{name}.json", rows)
        summary["panels"][name] = {"completed": len(rows),
                                   "planned": sum(job.panel == name for job in jobs)}
    complete = {name: sorted(rows, key=lambda row: row["seed"])
                for name, rows in rows_by_panel.items()
                if len(rows) == summary["panels"][name]["planned"]}
    try:
        summary["readout"] = read_panels(complete, raw_root=out)
    except Exception as exc:
        failure = {"phase": "readout", "error": f"{type(exc).__name__}: {exc}"}
        summary["failures"].append(failure)
        _append_progress(out, {"event": "readout_failed", **failure})
    summary["status"] = ("COMPLETE" if summary["counts"]["episodes_completed"] == len(jobs)
                         and not summary["failures"] else "FAILED")
    summary["costs"] = _costs(started, out, all_rows)
    _write_json(out / "summary.json", summary)
    return summary
