"""Fixed B01 S4 batch; workers write one native compressed trace per world."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import resource
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import asdict
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from .configuration import AvailableH1Controller, HORIZON, make_config, make_env
from .events import FaultObserver, event_windows
from .readout import summarize


DIRECTION = "energy_relay_availability"
SEEDS = {"fault_off": tuple(range(965001, 965033)),
         "fault_on": tuple(range(966001, 966033))}
CONTROLLERS = ("H_local", "H_central")
SEALED = set(range(957001, 957033))


def plan() -> list[dict]:
    return [{"condition": condition, "controller": controller, "seed": seed,
             "job_key": f"{condition}/{controller}/{seed}"}
            for condition, seeds in SEEDS.items()
            for controller in CONTROLLERS for seed in seeds]


def validate_plan(jobs: list[dict]) -> None:
    if any(job.get("seed") in SEALED for job in jobs):
        raise ValueError("sealed world is forbidden")
    expected = plan()
    if jobs != expected or len(jobs) != 128:
        raise ValueError("B01 requires the immutable 128-job S4 plan")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def _rss_kib() -> int:
    # Linux ru_maxrss is KiB; this runner's declared execution node is WSL Linux.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _cpu_seconds() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return float(usage.ru_utime + usage.ru_stime)


def _worker(payload: tuple[dict, str, int]) -> dict:
    job, out_string, threads = payload
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    env = None
    observer = None
    raw_path = Path(out_string) / "raw" / (job["job_key"].replace("/", "_") + ".npz")
    try:
        if job not in plan() or job["seed"] in SEALED:
            raise ValueError("world outside B01 fixed plan")
        import torch

        torch.set_num_threads(int(threads))
        config = make_config(HORIZON)
        env = make_env(config, job["seed"], job["condition"] == "fault_on")
        controller = AvailableH1Controller(
            "local" if job["controller"] == "H_local" else "central", env=env)
        observer = FaultObserver(env.env)
        row, steps = evaluate_world(controller, env, config, job["seed"],
                                    PRODUCTION_PARAMS, observer=observer)
        observed = observer.as_arrays()
        qos = steps["metrics"][:, 0]
        if len(qos) != row["actual_length"] or any(len(value) != len(qos)
                                                      for value in observed.values()):
            raise ValueError("observer/native trace length disagreement")
        events = event_windows(qos, observed)
        # The raw trace is the sole detailed copy. JSON keeps world-level event denominators.
        event_summary = {kind: {key: value for key, value in events[kind].items()
                                if key != "rows"} for kind in ("onset", "recovery")}
        event_summary.update(expiry_count=events["expiry_count"],
                             refault_count=events["refault_count"])
        if raw_path.exists():
            raise FileExistsError(raw_path)
        event_arrays = {}
        for kind in ("onset", "recovery"):
            event_rows = events[kind]["rows"]
            for field in ("t", "uav", "pre_length", "post_length", "post60_length",
                          "pre_mean", "post_mean", "delta20", "post60_mean",
                          "full_20", "full_60", "overlaps_other_event"):
                values = [item[field] for item in event_rows]
                dtype = bool if field in ("full_20", "full_60", "overlaps_other_event") else (
                    np.int32 if field in ("t", "uav", "pre_length", "post_length",
                                          "post60_length") else np.float64)
                event_arrays[f"event_{kind}_{field}"] = np.asarray(
                    [np.nan if value is None and dtype is np.float64 else
                     -1 if value is None and dtype is np.int32 else
                     False if value is None else value for value in values], dtype=dtype)
        np.savez_compressed(raw_path, **steps,
                            **{f"fault_{key}": value for key, value in observed.items()},
                            **event_arrays, metric_fields=np.asarray(TRACE_FIELDS))
        row.update(job)
        row.update(status="completed", events=event_summary,
                   raw_path=str(raw_path.relative_to(Path(out_string))),
                   raw_sha256=_sha256(raw_path), raw_bytes=raw_path.stat().st_size,
                   worker_wall_seconds=time.monotonic() - started,
                   worker_cpu_seconds=_cpu_seconds() - cpu_started,
                   worker_peak_rss_kib=_rss_kib())
        return row
    except BaseException as error:
        # A failed world is explicit. No retry and no zero-valued surrogate row.
        partial = {}
        if raw_path.exists():
            partial = {"incomplete_raw_path": str(raw_path.relative_to(Path(out_string))),
                       "incomplete_raw_sha256": _sha256(raw_path),
                       "incomplete_raw_bytes": raw_path.stat().st_size}
        elif observer is not None and observer.rows["post_timer"]:
            try:
                path = Path(out_string) / "raw" / (job["job_key"].replace("/", "_") + "_partial.npz")
                np.savez_compressed(path, **observer.as_arrays())
                partial = {"partial_path": str(path.relative_to(Path(out_string))),
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


def execute_bounded(executor, jobs: list[dict], workers: int, payload,
                    on_result, submitted: list[str] | None = None,
                    worker_fn=None) -> tuple[list[str], list[dict]]:
    """Never queue more than worker capacity; stop after the first technical failure."""
    remaining = iter(jobs)
    pending = {}
    if submitted is None:
        submitted = []
    errors = []
    stopped = False
    if worker_fn is None:
        worker_fn = _worker

    def submit_one():
        nonlocal stopped
        try:
            job = next(remaining)
        except StopIteration:
            return False
        submitted.append(job["job_key"])
        try:
            future = executor.submit(worker_fn, payload(job))
        except BaseException as error:
            on_result({**job, "status": "unreconciled",
                       "error_type": type(error).__name__, "error": str(error)})
            errors.append({"job_key": job["job_key"], "error_type": type(error).__name__,
                           "error": str(error)})
            stopped = True
            return False
        pending[future] = job
        return True

    for _ in range(min(workers, len(jobs))):
        if stopped or not submit_one():
            break
    while pending:
        done, _ = wait(tuple(pending), return_when=FIRST_COMPLETED)
        for future in done:
            job = pending.pop(future)
            try:
                row = future.result()
            except BaseException as error:
                row = {**job, "status": "unreconciled", "error_type": type(error).__name__,
                       "error": str(error)}
                errors.append({"job_key": job["job_key"], "error_type": type(error).__name__,
                               "error": str(error)})
            on_result(row)
            if row["status"] != "completed":
                stopped = True
        if stopped:
            # A submitted job may still be waiting inside the executor. Cancel only
            # those not started; running jobs finish and their evidence is collected.
            for future, job in list(pending.items()):
                if future.cancel():
                    pending.pop(future)
                    on_result({**job, "status": "cancelled",
                               "error": "cancelled after terminal batch failure"})
        else:
            while len(pending) < workers and submit_one():
                pass
    return submitted, errors


def orphan_raw_files(out: Path, rows: list[dict]) -> list[dict]:
    """Inventory every compressed file without treating an unreturned trace as complete."""
    referenced = {row[key] for row in rows for key in
                  ("raw_path", "partial_path", "incomplete_raw_path") if key in row}
    return [{"path": str(path.relative_to(out)), "sha256": _sha256(path),
             "bytes": path.stat().st_size, "status": "unreconciled"}
            for path in sorted((out / "raw").glob("*.npz"))
            if str(path.relative_to(out)) not in referenced]


def run(out: Path, launch_sha: str, workers: int = 4, threads: int = 1) -> dict:
    jobs = plan()
    validate_plan(jobs)
    if workers < 1 or threads != 1:
        raise ValueError("B01 requires positive worker count and one numeric thread per worker")
    # hmasd_launch creates this directory and its own status/log files before admission.
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B01 scientific artifacts already exist: {out}")
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], expected_keys))
    config = make_config(HORIZON)
    effective = {}
    for condition, seed in (("fault_off", SEEDS["fault_off"][0]),
                            ("fault_on", SEEDS["fault_on"][0])):
        probe = make_env(config, seed, condition == "fault_on")
        try:
            raw = probe.env
            effective[condition] = {key: getattr(raw, key) for key in
                                    ("energy_stage", "n_uavs", "n_users", "n_ground_bs",
                                     "n_charging_stations", "user_movement_model", "user_max_speed",
                                     "cluster_migration_speed", "max_steps", "battery_capacity_wh",
                                     "failure_enabled", "uav_failure_probability",
                                     "uav_failure_min_active")}
            effective[condition]["cluster_pause_time_range"] = list(raw.cluster_pause_time_range)
            effective[condition]["user_pause_time_range"] = list(raw.user_pause_time_range)
            effective[condition]["uav_failure_duration_range"] = list(raw.uav_failure_duration_range)
            effective[condition]["charging_station_capacity"] = raw.charging_station_capacity[:2].tolist()
            effective[condition]["adapter_shape"] = list(probe.observation_space.shape)
        finally:
            probe.close()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B01", "launch_sha": launch_sha,
        "horizon": HORIZON, "jobs": jobs, "workers": workers, "threads": threads,
        "fits": 0, "optimizer_updates": 0, "shield": asdict(PRODUCTION_PARAMS),
        "controllers": {name: variant("H1", information=name.removeprefix("H_")).record()
                        for name in CONTROLLERS},
        "legal_availability": "not native failed and battery above service cutoff; charging separate",
        "event_windows": {"pre": 20, "post": 20, "post_recovery": 60},
        "observation_layout": S7S2_LAYOUT.record(),
        "effective_raw": effective,
        "config": {key: getattr(config, key) for key in
                   ("experiment_preset", "energy_stage", "num_envs", "episode_length",
                    "max_steps", "k", "lambda_return", "use_obsnorm", "use_statenorm")},
    })
    rows = []
    args = [(job, str(out), threads) for job in jobs]
    # ProcessPoolExecutor does not replace a crashed worker. A broken pool is terminal.
    context = multiprocessing.get_context("spawn")
    runner_error = None
    submitted = []
    pool_errors = []

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, expected_keys))

    try:
        with ProcessPoolExecutor(max_workers=min(workers, len(args)), mp_context=context) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, min(workers, len(args)),
                lambda job: (job, str(out), threads), on_result, submitted)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows, expected_keys)
    summary["submitted_jobs"] = submitted
    summary["unstarted_jobs"] = [key for key in expected_keys if key not in submitted]
    orphan_raw = orphan_raw_files(out, rows)
    summary["orphan_raw"] = orphan_raw
    if orphan_raw:
        summary["status"] = "incomplete"
    if pool_errors:
        summary["pool_errors"] = pool_errors
    completed_transitions = sum(row["actual_length"] for row in rows
                                if row["status"] == "completed")
    partial_transitions = sum(row.get("partial_observed_steps", 0) for row in rows)
    summary.update(launch_sha=launch_sha, fits=0, optimizer_updates=0,
                   completed_transitions=completed_transitions,
                   partial_observed_transitions=partial_transitions,
                   known_transition_lower_bound=completed_transitions + partial_transitions,
                   actual_transitions=completed_transitions if summary["status"] == "complete"
                   else None,
                   parent_wall_seconds=time.monotonic() - started,
                   parent_cpu_seconds=_cpu_seconds() - cpu_started,
                   parent_peak_rss_kib=_rss_kib(),
                   worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in rows
                                                if "worker_peak_rss_kib" in row),
                                               default=None),
                   worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
                   worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
    if runner_error is not None:
        summary["runner_error"] = runner_error
        summary["status"] = "incomplete"
        summary["actual_transitions"] = None
    _write_json(out / "summary.json", summary)
    manifest = {"launch_sha": launch_sha, "artifacts": {
        name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
        for name in ("config.json", "perworld.json", "summary.json")},
        "raw": {row["job_key"]: {"path": row["raw_path"], "sha256": row["raw_sha256"],
                                "bytes": row["raw_bytes"]} for row in rows
                if row["status"] == "completed"},
        "partial": {row["job_key"]: {"path": row["partial_path"],
                                    "sha256": row["partial_sha256"],
                                    "bytes": row["partial_bytes"]} for row in rows
                    if "partial_path" in row},
        "incomplete_raw": {row["job_key"]: {"path": row["incomplete_raw_path"],
                                           "sha256": row["incomplete_raw_sha256"],
                                           "bytes": row["incomplete_raw_bytes"]} for row in rows
                           if "incomplete_raw_path" in row},
        "orphan_raw": orphan_raw}
    manifest["storage_bytes"] = sum(item["bytes"] for item in manifest["artifacts"].values()) + sum(
        item["bytes"] for item in (*manifest["raw"].values(), *manifest["partial"].values(),
                                   *manifest["incomplete_raw"].values(),
                                   *manifest["orphan_raw"]))
    _write_json(out / "manifest.json", manifest)
    if runner_error is not None:
        raise RuntimeError("B01 worker pool failed; incomplete evidence is preserved")
    return summary
