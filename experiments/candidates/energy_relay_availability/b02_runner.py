"""Fixed B02 paired S4 fault-on batch and durable single-copy native traces."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from .b02_controller import ARMS, B02Controller, response_lags
from .b02_readout import summarize
from .configuration import HORIZON, make_config, make_env
from .events import FaultObserver, event_windows
from .runner import (_cpu_seconds, _rss_kib, _sha256, _write_json,
                     execute_bounded, orphan_raw_files)


SEEDS = tuple(range(969001, 969033))
SEALED = set(range(957001, 957033))


def plan() -> list[dict]:
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for arm in ARMS for seed in SEEDS]


def validate_plan(jobs: list[dict]) -> None:
    if any(job.get("seed") in SEALED for job in jobs):
        raise ValueError("sealed world is forbidden")
    if jobs != plan() or len(jobs) != 64:
        raise ValueError("B02 requires the immutable 64-job paired plan")


def _event_arrays(events: dict) -> dict[str, np.ndarray]:
    result = {}
    for kind in ("onset", "recovery"):
        for field in ("t", "uav", "pre_length", "post_length", "post60_length",
                      "pre_mean", "post_mean", "delta20", "post60_mean",
                      "full_20", "full_60", "overlaps_other_event"):
            values = [item[field] for item in events[kind]["rows"]]
            dtype = bool if field in ("full_20", "full_60", "overlaps_other_event") else (
                np.int32 if field in ("t", "uav", "pre_length", "post_length",
                                      "post60_length") else np.float64)
            result[f"event_{kind}_{field}"] = np.asarray(
                [np.nan if value is None and dtype is np.float64 else
                 -1 if value is None and dtype is np.int32 else
                 False if value is None else value for value in values], dtype=dtype)
    return result


def _worker(payload: tuple[dict, str, int]) -> dict:
    job, out_string, threads = payload
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    env = observer = controller = None
    out = Path(out_string)
    raw_path = out / "raw" / (job["job_key"].replace("/", "_") + ".npz")
    try:
        if job not in plan() or job["seed"] in SEALED:
            raise ValueError("world outside B02 fixed plan")
        import torch

        torch.set_num_threads(int(threads))
        config = make_config(HORIZON)
        env = make_env(config, job["seed"], True)
        controller = B02Controller(job["arm"])
        observer = FaultObserver(env.env)
        row, steps = evaluate_world(controller, env, config, job["seed"],
                                    PRODUCTION_PARAMS, observer=observer)
        fault = observer.as_arrays()
        decisions = controller.as_arrays()
        length = row["actual_length"]
        if (not decisions or any(len(value) != length for value in decisions.values())
                or any(len(value) != length for value in fault.values())
                or len(steps["metrics"]) != length):
            raise ValueError("B02 decision/fault/native trace length disagreement")
        if not np.array_equal(decisions["available"], fault["pre_available"]):
            raise ValueError("controller availability differs from legal observation trace")
        if not np.array_equal(decisions["regular_replan"],
                              np.arange(length) % 30 == 0):
            raise ValueError("B02 regular clock moved")
        if not np.array_equal(decisions["executed_replan"],
                              decisions["regular_replan"] | decisions["extra_replan"]):
            raise ValueError("B02 executed plan flags disagree")
        if not np.array_equal(decisions["plan_call_count"],
                              np.cumsum(decisions["executed_replan"])):
            raise ValueError("B02 cumulative plan-call count disagrees")
        if job["arm"] == "clock30" and decisions["extra_replan"].any():
            raise ValueError("clock30 acquired an extra plan")
        response = response_lags(decisions, fault["post_available"][-1])
        events = event_windows(steps["metrics"][:, 0], fault)
        event_summary = {kind: {key: value for key, value in events[kind].items()
                                if key != "rows"} for kind in ("onset", "recovery")}
        event_summary.update(expiry_count=events["expiry_count"],
                             refault_count=events["refault_count"])
        fault_digest = hashlib.sha256()
        for field in ("pre_timer", "post_timer"):
            value = np.ascontiguousarray(fault[field], dtype=np.int16)
            fault_digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
            fault_digest.update(value.tobytes())
        if raw_path.exists():
            raise FileExistsError(raw_path)
        response_arrays = {
            f"response_{key}": np.asarray([item[key] if item[key] is not None else -1
                                            for item in response["rows"]], dtype=np.int32)
            for key in ("decision", "lag", "observed_decisions")}
        response_arrays.update({
            f"response_{key}": np.asarray([item[key] for item in response["rows"]], dtype=bool)
            for key in ("right_censored", "terminal_observation_only")})
        np.savez_compressed(raw_path, **steps,
                            **{f"fault_{key}": value for key, value in fault.items()},
                            **{f"decision_{key}": value for key, value in decisions.items()},
                            **_event_arrays(events), **response_arrays,
                            metric_fields=np.asarray(TRACE_FIELDS))
        row.update(job)
        row.update(status="completed", events=event_summary,
                   fault_trace_sha256=fault_digest.hexdigest(),
                   plan_call_count=int(decisions["executed_replan"].sum()),
                   regular_plan_count=int(decisions["regular_replan"].sum()),
                   extra_plan_count=int(decisions["extra_replan"].sum()),
                   availability_change_decisions=int(decisions["availability_changed"].sum()),
                   coincident_trigger_count=int(decisions["coincident_trigger"].sum()),
                   response_changes=response["changes"],
                   response_complete=response["complete_lags"],
                   response_censored=response["censored_lags"],
                   terminal_changes=response["terminal_changes"],
                   world_mean_response_lag=response["world_mean_lag"],
                   planning_cpu_seconds=float(decisions["plan_cpu_seconds"].sum()),
                   planning_wall_seconds=float(decisions["plan_wall_seconds"].sum()),
                   raw_path=str(raw_path.relative_to(out)),
                   raw_sha256=_sha256(raw_path), raw_bytes=raw_path.stat().st_size,
                   worker_wall_seconds=time.monotonic() - started,
                   worker_cpu_seconds=_cpu_seconds() - cpu_started,
                   worker_peak_rss_kib=_rss_kib())
        return row
    except BaseException as error:
        partial = {}
        if raw_path.exists():
            partial = {"incomplete_raw_path": str(raw_path.relative_to(out)),
                       "incomplete_raw_sha256": _sha256(raw_path),
                       "incomplete_raw_bytes": raw_path.stat().st_size}
        elif observer is not None and observer.rows["post_timer"]:
            try:
                path = out / "raw" / (job["job_key"].replace("/", "_") + "_partial.npz")
                arrays = {f"fault_{key}": value for key, value in observer.as_arrays().items()}
                if controller is not None and controller.decision_rows:
                    arrays.update({f"decision_{key}": value
                                   for key, value in controller.as_arrays().items()})
                np.savez_compressed(path, **arrays)
                partial = {"partial_path": str(path.relative_to(out)),
                           "partial_sha256": _sha256(path), "partial_bytes": path.stat().st_size,
                           "partial_observed_steps": len(observer.rows["post_timer"])}
            except BaseException as partial_error:
                partial = {"partial_preservation_error": repr(partial_error)}
        return {**job, **partial, "status": "failed", "error_type": type(error).__name__,
                "error": str(error), "traceback": traceback.format_exc(),
                "worker_wall_seconds": time.monotonic() - started,
                "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                "worker_peak_rss_kib": _rss_kib()}
    finally:
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def run(out: Path, launch_sha: str, workers: int = 4, threads: int = 1) -> dict:
    jobs = plan()
    validate_plan(jobs)
    if workers < 1 or threads != 1:
        raise ValueError("B02 requires positive workers and one numeric thread per worker")
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B02 scientific artifacts already exist: {out}")
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)  # Native launcher has already created metadata.
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    rows = []
    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows, expected_keys))
    config = make_config(HORIZON)
    probe = make_env(config, SEEDS[0], True)
    try:
        raw = probe.env
        effective = {key: getattr(raw, key) for key in
                     ("energy_stage", "n_uavs", "n_users", "n_ground_bs",
                      "n_charging_stations", "user_movement_model", "user_max_speed",
                      "cluster_migration_speed", "max_steps", "battery_capacity_wh",
                      "failure_enabled", "uav_failure_probability", "uav_failure_min_active")}
        for key in ("cluster_pause_time_range", "user_pause_time_range",
                    "uav_failure_duration_range"):
            effective[key] = list(getattr(raw, key))
        effective["charging_station_capacity"] = raw.charging_station_capacity[:2].tolist()
        effective["adapter_shape"] = list(probe.observation_space.shape)
    finally:
        probe.close()
    _write_json(out / "config.json", {
        "direction": "energy_relay_availability", "batch": "B02",
        "launch_sha": launch_sha, "horizon": HORIZON, "jobs": jobs,
        "workers": workers, "threads": threads, "fits": 0, "optimizer_updates": 0,
        "shield": asdict(PRODUCTION_PARAMS),
        "controller": variant("H1", information="local").record(),
        "regular_replan_period": 30,
        "availability_trigger": "current legal eight-UAV available vector differs from previous decision",
        "terminal_change": "last post-transition observation has no next decision; right-censored",
        "legal_availability": "nonfailed and battery above service cutoff; charging separate",
        "event_windows": {"pre": 20, "post": 20, "post_recovery": 60},
        "observation_layout": S7S2_LAYOUT.record(), "effective_raw": effective,
        "config": {key: getattr(config, key) for key in
                   ("experiment_preset", "energy_stage", "num_envs", "episode_length",
                    "max_steps", "k", "lambda_return", "use_obsnorm", "use_statenorm")},
    })
    submitted = []
    pool_errors = []
    runner_error = None

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, expected_keys))

    try:
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs)),
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, min(workers, len(jobs)),
                lambda job: (job, str(out), threads), on_result, submitted,
                worker_fn=_worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows, expected_keys)
    summary["submitted_jobs"] = submitted
    summary["unstarted_jobs"] = [key for key in expected_keys if key not in submitted]
    orphan = orphan_raw_files(out, rows)
    summary["orphan_raw"] = orphan
    if orphan or runner_error:
        summary["status"] = "incomplete"
    if pool_errors:
        summary["pool_errors"] = pool_errors
    if runner_error:
        summary["runner_error"] = runner_error
    completed_steps = sum(row["actual_length"] for row in rows
                          if row["status"] == "completed")
    partial_steps = sum(row.get("partial_observed_steps", 0) for row in rows)
    summary.update(launch_sha=launch_sha, fits=0, optimizer_updates=0,
                   completed_transitions=completed_steps,
                   partial_observed_transitions=partial_steps,
                   known_transition_lower_bound=completed_steps + partial_steps,
                   actual_transitions=completed_steps if summary["status"] == "complete" else None,
                   parent_wall_seconds=time.monotonic() - started,
                   parent_cpu_seconds=_cpu_seconds() - cpu_started,
                   parent_peak_rss_kib=_rss_kib(),
                   worker_peak_rss_kib_max=max((r["worker_peak_rss_kib"] for r in rows
                                                if "worker_peak_rss_kib" in r), default=None),
                   worker_cpu_seconds_sum=sum(r.get("worker_cpu_seconds", 0) for r in rows),
                   worker_wall_seconds_sum=sum(r.get("worker_wall_seconds", 0) for r in rows))
    _write_json(out / "summary.json", summary)
    manifest = {"launch_sha": launch_sha, "artifacts": {
        name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
        for name in ("config.json", "perworld.json", "summary.json")},
        "raw": {r["job_key"]: {"path": r["raw_path"], "sha256": r["raw_sha256"],
                              "bytes": r["raw_bytes"]} for r in rows if r["status"] == "completed"},
        "partial": {r["job_key"]: {"path": r["partial_path"], "sha256": r["partial_sha256"],
                                  "bytes": r["partial_bytes"]} for r in rows if "partial_path" in r},
        "incomplete_raw": {r["job_key"]: {"path": r["incomplete_raw_path"],
                                         "sha256": r["incomplete_raw_sha256"],
                                         "bytes": r["incomplete_raw_bytes"]} for r in rows
                           if "incomplete_raw_path" in r},
        "orphan_raw": orphan}
    manifest["storage_bytes"] = sum(item["bytes"] for item in manifest["artifacts"].values()) + sum(
        item["bytes"] for item in (*manifest["raw"].values(), *manifest["partial"].values(),
                                   *manifest["incomplete_raw"].values(), *orphan))
    _write_json(out / "manifest.json", manifest)
    if runner_error is not None:
        raise RuntimeError("B02 worker pool failed; incomplete evidence is preserved")
    return summary
