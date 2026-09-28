"""One admitted 32-pair S2 station-prior batch, retaining native outcomes and tails."""

from __future__ import annotations

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
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_information_value.batch import InformationObserver, effective_config
from experiments.candidates.uav_information_value.controllers import make_controller as make_reference
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

from .controller import StationPriorController
from .readout import ARMS, RESERVE_RATIO, battery_reading, summarize


DIRECTION = "uav_information_value"
HORIZON = 3000
SEEDS = tuple(range(28100201, 28100233))


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def validate_plan(jobs):
    if jobs != plan() or len(jobs) != 64 or len(set(SEEDS)) != 32:
        raise ValueError("B02 requires the fixed two-program 32-world panel")


def make_controller(arm):
    if arm == "H_BS":
        return make_reference("H_BS")
    if arm == "P_BS":
        return StationPriorController()
    raise ValueError(f"unknown B02 arm {arm!r}")


def check_config(env, horizon):
    result = effective_config(env, horizon)
    raw = env.env
    expected = {"area_size": 8000.0, "charging_station_layout": "service_anchored",
                "charging_station_jitter_m": 960.0, "return_reserve_ratio": RESERVE_RATIO}
    for key, value in expected.items():
        if getattr(raw, key) != value:
            raise ValueError(f"B02 native {key} differs from fixed contract")
    return result | expected


class PriorObserver(InformationObserver):
    """Read-only activation and exact native post-step risk; never policy inputs."""

    def __init__(self, arm, raw_env):
        super().__init__(arm)
        self.raw_env = raw_env
        self.native_battery = []
        self.prior_bs_xy = None

    def on_step(self, **kwargs):
        self.native_battery.append(np.asarray(self.raw_env.uav_battery_ratios, dtype=np.float64).copy())
        super().on_step(**kwargs)
        if kwargs["t"] % 30:
            return
        controller = kwargs["controller"]
        diagnostic = controller.diagnostics[-1]
        prior_used = bool(diagnostic.get("prior_used", False))
        row = self.plans[-1]
        if prior_used and row["bs_seen_so_far"]:
            raise RuntimeError("inferred BS used after a genuine legal sighting")
        row.update(prior_used=prior_used, relay_count=len(controller.heuristic.last_plan["relays"]))
        row["bs_input_source"] = diagnostic.get(
            "bs_input_source", "observed-current" if row["legal_bs_present"] else
            "observed-memory" if row["bs_seen_so_far"] else "absent")
        prior = getattr(controller, "prior_bs_xy", None)
        self.prior_bs_xy = None if prior is None else np.asarray(prior).tolist()

    def arrays(self):
        return super().arrays() | {"info_native_battery": np.asarray(self.native_battery, dtype=np.float64)}

    def reading(self):
        prior_steps = [row["step"] for row in self.plans if row["prior_used"]]
        return super().reading() | battery_reading(self.native_battery) | {
            "prior_bs_xy": self.prior_bs_xy,
            "prior_used_plans": len(prior_steps),
            "first_prior_use_step": prior_steps[0] if prior_steps else None,
            "relay_plans": sum(row["relay_count"] > 0 for row in self.plans),
            "mean_relay_count_at_plan": float(np.mean([row["relay_count"] for row in self.plans]))
            if self.plans else None,
        }


def worker(payload):
    job, out_string, threads = payload
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw_path = out / "raw" / f"{stem}.npz"
    progress_path = out / "raw" / f"{stem}.progress.json"
    env, observer, native_steps = None, None, None
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
            raise RuntimeError("B02 requires SciPy assignment and native Torch FP32")
        config = make_eval_config(HORIZON, 0)
        env = make_env(config, job["seed"])
        effective = check_config(env, HORIZON)
        controller = make_controller(job["arm"])
        observer = PriorObserver(job["arm"], env.env)
        row, native_steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                           observer=observer, progress=progress)
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **native_steps, **observer.arrays(), metric_fields=np.asarray(TRACE_FIELDS))
        if (len(observer.bs_present) != row["actual_length"]
                or len(observer.native_battery) != row["actual_length"]
                or completed_steps != row["actual_length"]):
            raise RuntimeError("native, observer and progress counts differ")
        readings = observer.reading()
        if readings["native_minimum_battery_ratio"] != row["episode_minimum_battery_ratio"]:
            raise RuntimeError("native battery trace and reward-info minimum differ")
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "completed"})
        row.update(job, status="completed", effective_config=effective, **readings,
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
            elif native_steps is not None or (observer is not None and observer.bs_present):
                partial = out / "raw" / f"{stem}.partial.npz"
                arrays = native_steps if native_steps is not None else observer.arrays()
                np.savez_compressed(partial, **arrays)
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
        raise ValueError("B02 permits one to four workers, one numeric thread each")
    out = Path(out)
    if any((out / name).exists() for name in ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"scientific artifacts already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B02", "launch_sha": launch_sha, "jobs": jobs,
        "horizon": HORIZON, "fits": 0, "optimizer_updates": 0, "workers": workers, "threads": threads,
        "max_transitions": len(jobs) * HORIZON, "shield": asdict(PRODUCTION_PARAMS),
        "common_h1": variant("H1", information="local").record(),
        "observation_layout": S7S2_LAYOUT.record(), "trace_timing": TRACE_TIMING,
        "native_battery_timing": "exact raw uav_battery_ratios after each native transition; observer only",
        "pairing": "common initial seeds, not identical closed-loop trajectories",
        "user_preprocessing": "canonical legal raw xy hits; sort then greedy merge within 0.5m",
        "h_bs_source_commit": "ee9c6c8aca0ee13e3d7a02416ff4acf85766f274",
        "arms": {"H_BS": "unchanged legal users/once-legally-seen static BS memory",
                 "P_BS": "H_BS plus reset-frozen station prior before any legal BS sighting"},
        "prior": {"formula": "clip((station0_xy - 0.3 * station1_xy) / 0.7, 0, 8000)",
                  "source": "first valid observer for each legal station ID at reset decision",
                  "missing": "no inferred BS if either finite valid station record is absent",
                  "priority": "genuine current/remembered legal BS supersedes prior permanently"},
        "risk_reading": {"reserve_ratio": RESERVE_RATIO,
                         "default_replacement_blockers": "additional paired cutoff/depletion or final reserve UAV count",
                         "other_tradeoffs": "higher mean return cost or worse panel battery minimum"},
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
        summary["practical_risk"] = {}
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
