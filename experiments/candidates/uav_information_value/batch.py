"""Fixed six-program S2 batch, with native traces and terminal failure preservation."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict
import faulthandler
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, TRACE_TIMING, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy, variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

from .controllers import ARMS, canonical_legal_users, make_controller
from .readout import summarize


DIRECTION = "uav_information_value"
HORIZON = 3000
SEEDS = tuple(range(28100101, 28100133))


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def validate_plan(jobs):
    if jobs != plan() or len(jobs) != 192 or len(set(SEEDS)) != 32:
        raise ValueError("B01 requires the fixed six-program 32-world panel")


def effective_config(env, horizon):
    raw = env.env
    expected = {
        "energy_stage": "S2", "n_uavs": 8, "n_users": 30, "n_ground_bs": 1,
        "n_charging_stations": 2, "user_movement_model": "rpgm", "user_max_speed": 3.0,
        "cluster_migration_speed": 3.0, "battery_capacity_wh": 160.0,
        "failure_enabled": False, "uav_failure_probability": 0.0,
        "observation_radius": 1500.0, "max_steps": int(horizon),
    }
    for key, value in expected.items():
        if getattr(raw, key) != value:
            raise ValueError(f"native S2 {key} differs from fixed contract")
    if not np.array_equal(raw.charging_station_capacity[:2], [1, 1]):
        raise ValueError("native station capacity differs")
    if (env.n_uavs, env.obs_dim, env.action_space.shape) != (8, 365, (8, 4)):
        raise ValueError("native adapter shape differs")
    return expected | {
        "charging_station_capacity": raw.charging_station_capacity[:2].tolist(),
        "cluster_pause_time_range": list(raw.cluster_pause_time_range),
        "user_pause_time_range": list(raw.user_pause_time_range),
        "charging_station_layout": raw.charging_station_layout,
        "charging_station_jitter_m": raw.charging_station_jitter_m,
    }


class InformationObserver:
    """Read-only decision-time diagnostics; no environment or policy feedback."""

    def __init__(self, arm):
        self.arm = arm
        self.bs_present = []
        self.bs_seen = []
        self.plans = []
        self.first_seen = None

    def attach(self, controller):
        return nullcontext()

    def on_step(self, *, t, observations_t, controller, **unused):
        present = observed_bs_xy(observations_t, S7S2_LAYOUT) is not None
        if present and self.first_seen is None:
            self.first_seen = int(t)
        seen = self.first_seen is not None
        self.bs_present.append(present)
        self.bs_seen.append(seen)
        if t % 30:
            return
        plan_data = controller.heuristic.last_plan
        current_users = canonical_legal_users(observations_t, S7S2_LAYOUT, 0.5)
        diagnostics = getattr(controller, "diagnostics", [])
        memory_used = bool(diagnostics[-1]["memory_used"]) if diagnostics else False
        self.plans.append({
            "step": int(t), "legal_user_count": len(current_users),
            "supplied_user_count": len(plan_data["users"]),
            "legal_bs_present": present, "bs_seen_so_far": seen,
            "known_bs_omitted": bool(seen and plan_data["bs_xy"] is None),
            "legal_bs_absent_after_seen": bool(seen and not present),
            "memory_used": memory_used, "search": bool(plan_data["search"]),
        })

    def arrays(self):
        arrays = {
            "info_bs_present": np.asarray(self.bs_present, dtype=bool),
            "info_bs_seen": np.asarray(self.bs_seen, dtype=bool),
        }
        if self.plans:
            arrays.update({f"info_plan_{field}": np.asarray([row[field] for row in self.plans])
                           for field in self.plans[0]})
        return arrays

    def reading(self):
        return {
            "first_legal_bs_step": self.first_seen,
            "legal_bs_present_steps": sum(self.bs_present),
            "plan_count": len(self.plans),
            **{f"{field}_plans": sum(row[field] for row in self.plans)
               for field in ("known_bs_omitted", "legal_bs_absent_after_seen", "memory_used", "search")},
            "mean_legal_user_count_at_plan": float(np.mean([r["legal_user_count"] for r in self.plans]))
            if self.plans else None,
            "mean_supplied_user_count_at_plan": float(np.mean([r["supplied_user_count"] for r in self.plans]))
            if self.plans else None,
        }


def worker(payload):
    job, out_string, threads = payload
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw_path = out / "raw" / f"{stem}.npz"
    progress_path = out / "raw" / f"{stem}.progress.json"
    env, observer = None, None
    completed_steps = 0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            _write_json(progress_path, {**job, "steps": completed_steps})

    try:
        if job not in plan() or threads != 1:
            raise ValueError("worker received an undeclared job or thread count")
        import torch
        from experiments.candidates.energy_relay_benchmark.b01.heuristic import _lsa

        faulthandler.enable()
        torch.set_num_threads(threads)
        if _lsa is None or torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B01 requires SciPy assignment and native Torch FP32")
        config = make_eval_config(HORIZON, 0)
        env = make_env(config, job["seed"])
        effective = effective_config(env, HORIZON)
        controller = make_controller(job["arm"], env)
        observer = InformationObserver(job["arm"])
        row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                    observer=observer, progress=progress)
        if len(observer.bs_present) != row["actual_length"] or completed_steps != row["actual_length"]:
            raise RuntimeError("native, observer and progress counts differ")
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **steps, **observer.arrays(), metric_fields=np.asarray(TRACE_FIELDS))
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "completed"})
        row.update(job, status="completed", effective_config=effective, **observer.reading(),
                   raw_path=str(raw_path.relative_to(out)), raw_sha256=_sha256(raw_path),
                   raw_bytes=raw_path.stat().st_size)
        return row | {
            "worker_wall_seconds": time.monotonic() - started,
            "worker_cpu_seconds": _cpu_seconds() - cpu_started, "worker_peak_rss_kib": _rss_kib(),
        }
    except BaseException as error:
        record = {**job, "status": "failed", "error_type": type(error).__name__, "error": str(error),
                  "traceback": traceback.format_exc(), "partial_observed_steps": completed_steps,
                  "worker_wall_seconds": time.monotonic() - started,
                  "worker_cpu_seconds": _cpu_seconds() - cpu_started, "worker_peak_rss_kib": _rss_kib()}
        try:
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "failed"})
            if raw_path.exists():
                record.update(incomplete_raw_path=str(raw_path.relative_to(out)),
                              incomplete_raw_sha256=_sha256(raw_path), incomplete_raw_bytes=raw_path.stat().st_size)
            elif observer is not None and observer.bs_present:
                partial = out / "raw" / f"{stem}.partial.npz"
                np.savez_compressed(partial, **observer.arrays())
                record.update(partial_path=str(partial.relative_to(out)), partial_sha256=_sha256(partial),
                              partial_bytes=partial.stat().st_size)
        except BaseException as preservation_error:
            record["partial_preservation_error"] = repr(preservation_error)
        return record
    finally:
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def run(out, launch_sha, workers=4, threads=1):
    jobs = plan()
    validate_plan(jobs)
    if not 1 <= workers <= 4 or threads != 1:
        raise ValueError("B01 permits one to four workers, one numeric thread each")
    out = Path(out)
    if any((out / name).exists() for name in ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"scientific artifacts already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B01", "launch_sha": launch_sha, "jobs": jobs,
        "horizon": HORIZON, "fits": 0, "optimizer_updates": 0, "workers": workers, "threads": threads,
        "max_transitions": len(jobs) * HORIZON, "shield": asdict(PRODUCTION_PARAMS),
        "common_h1": variant("H1", information="local").record(),
        "observation_layout": S7S2_LAYOUT.record(),
        "trace_timing": TRACE_TIMING, "pairing": "common initial seeds, not identical closed-loop trajectories",
        "user_preprocessing": "all point-set arms sort raw xy hits, then greedy merge within 0.5m",
        "historical_local_identity": "not exact: original local merges in observer order before sorting",
        "arms": {"L": "pooled legal users/legal BS", "U": "true current users/legal BS",
                 "B": "pooled legal users/true BS", "F": "true users/true BS; canonicalized",
                 "R": "original H_central", "H_BS": "legal users/once-legally-seen static BS memory"},
    })
    rows, submitted, pool_errors = [], [], []
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows, jobs))

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, jobs))

    runner_error = None
    try:
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(executor, jobs, workers, lambda job: (job, str(out), threads),
                                             on_result, submitted, worker_fn=worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows, jobs)
    orphans = orphan_raw_files(out, rows)
    progress_records = [json.loads(path.read_text()) for path in sorted((out / "raw").glob("*.progress.json"))]
    progress_by_key = {record["job_key"]: record["steps"] for record in progress_records}
    completed = {row["job_key"]: row["actual_length"] for row in rows if row["status"] == "completed"}
    partial_steps = sum(count for key, count in progress_by_key.items() if key not in completed)
    if orphans or runner_error or pool_errors:
        summary["status"] = "incomplete"
    summary.update(
        launch_sha=launch_sha, fits=0, optimizer_updates=0, submitted_jobs=submitted,
        unstarted_jobs=[key for key in expected_keys if key not in submitted],
        completed_transitions=sum(completed.values()), partial_observed_transitions=partial_steps,
        known_transition_lower_bound=sum(completed.values()) + partial_steps,
        actual_transitions=sum(completed.values()) if summary["status"] == "complete" else None,
        orphan_raw=orphans, runner_error=runner_error, pool_errors=pool_errors,
        parent_wall_seconds=time.monotonic() - started, parent_cpu_seconds=_cpu_seconds() - cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows),
        worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in rows if "worker_peak_rss_kib" in row), default=None),
        worker_resources_unmeasured=[row["job_key"] for row in rows if "worker_cpu_seconds" not in row],
    )
    if summary["status"] != "complete":
        summary["contrasts"] = {}
    _write_json(out / "summary.json", summary)
    artifacts = {name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
                 for name in ("config.json", "perworld.json", "summary.json")}
    raw_manifest = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                    for path in sorted((out / "raw").iterdir()) if path.is_file()}
    _write_json(out / "manifest.json", {
        "launch_sha": launch_sha, "artifacts": artifacts, "raw": raw_manifest,
        "storage_bytes": sum(item["bytes"] for item in (*artifacts.values(), *raw_manifest.values())),
    })
    return summary
