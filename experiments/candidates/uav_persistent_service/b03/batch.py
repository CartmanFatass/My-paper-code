"""One admitted, fixed zero-fit B03 native panel."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import faulthandler
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS

from .episode import HORIZON, LongMissionEpisode
from .readout import ARMS, SEEDS, plan, summarize, verify_pair


DIRECTION = "uav_persistent_service"
BATCH = "b03_reassignment_a01"
WORKERS = 4
MAX_NATIVE_STEPS = len(ARMS)*len(SEEDS)*HORIZON


def choose_action(episode):
    return 0 if episode.external_arm == "P" else episode.controller.ordinary_action()


def worker(payload):
    job, out_string = payload
    if job not in plan():
        raise ValueError("undeclared B03 evaluation world")
    import torch

    torch.set_num_threads(1)
    faulthandler.enable()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw = out/"raw"/f"{stem}.npz"
    progress = out/"raw"/f"{stem}.progress.json"
    started, cpu_started = time.monotonic(), _cpu_seconds()
    episode = None
    try:
        episode = LongMissionEpisode(job["seed"], job["arm"])
        while not episode.done:
            episode.macro_step(choose_action(episode))
            _write_json(progress, job | {"status": "running", "steps": episode.t})
        row = episode.row() | job
        row.update(episode.save(raw, complete=True))
        _write_json(progress, job | {"status": "completed", "steps": episode.t})
    except BaseException as error:
        row = job | {"status": "failed", "error_type": type(error).__name__,
                     "error": str(error), "traceback": traceback.format_exc(),
                     "partial_observed_steps": episode.t if episode is not None else 0}
        _write_json(progress, job | {"status": "failed", "steps": row["partial_observed_steps"]})
        if episode is not None and episode.t:
            partial = raw.with_suffix(".partial.npz")
            if not partial.exists():
                try:
                    row.update(episode.save(partial, complete=False))
                except BaseException as save_error:
                    row["partial_save_error"] = f"{type(save_error).__name__}: {save_error}"
    finally:
        if episode is not None:
            try:
                episode.close()
            except BaseException as close_error:
                row["status"] = "failed"
                row["close_error"] = f"{type(close_error).__name__}: {close_error}"
    for field in ("raw_path", "decisions_path"):
        if field in row:
            row[field] = str(Path(row[field]).relative_to(out))
    return row | {"worker_wall_seconds": time.monotonic()-started,
                  "worker_cpu_seconds": _cpu_seconds()-cpu_started,
                  "worker_peak_rss_kib": _rss_kib()}


def run(out: Path, launch_sha: str, workers: int = WORKERS):
    if workers != WORKERS:
        raise ValueError("B03 requires the fixed four single-thread workers")
    jobs = plan()
    if len(jobs) != 24 or len({job["job_key"] for job in jobs}) != 24:
        raise ValueError("B03 fixed plan differs")
    out = Path(out).resolve()
    if any((out/name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError("B03 scientific artifacts already exist")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out/"raw").mkdir()
    _write_json(out/"config.json", {
        "direction": DIRECTION, "batch": BATCH, "launch_sha": launch_sha,
        "jobs": jobs, "seeds": SEEDS, "arms": ARMS, "horizon": HORIZON,
        "macro_steps": 30, "fits": 0, "optimizer_updates": 0,
        "max_native_transitions": MAX_NATIVE_STEPS, "evaluation_workers": workers,
        "numeric_threads_per_worker": 1, "shield": asdict(PRODUCTION_PARAMS),
        "O_H": "retained O with controller/readout max_steps bound to H12000",
        "P": "unchanged TransitHold with controller/readout H12000 clock",
        "R": "O_H plus finite load/deadline cross-basin transfer",
        "arrival_detector": "retained strict decoded <=20 m; no repair",
        "mission_service_denominator": HORIZON, "late_window": [6000, 12000],
        "fixed_bins": 3000, "final_reserve_window": [11700, 12000]})
    rows, submitted, pool_errors, pairing = [], [], [], {}
    _write_json(out/"perworld.json", rows)
    _write_json(out/"summary.json", summarize(rows, pairing=pairing))
    order = [job["job_key"] for job in jobs]

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: order.index(item["job_key"]))
        if row["status"] == "completed":
            seed = row["seed"]
            group = {item["arm"]: item for item in rows
                     if item["seed"] == seed and item["status"] == "completed"}
            if len(group) == 3:
                pairing[seed] = verify_pair(out, group)
        _write_json(out/"perworld.json", rows)
        _write_json(out/"summary.json", summarize(rows, pairing=pairing))

    runner_error = None
    try:
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, workers, lambda job: (job, str(out)), on_result,
                submitted, worker_fn=worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    indexed = {row["job_key"]: row for row in rows if row["status"] == "completed"}
    for seed in SEEDS:
        group = {arm: indexed[f"{arm}/{seed}"] for arm in ARMS if f"{arm}/{seed}" in indexed}
        if len(group) == 3:
            pairing[seed] = verify_pair(out, group)
    summary = summarize(rows, pairing=pairing)
    orphans = orphan_raw_files(out, rows)
    if runner_error or pool_errors or orphans:
        summary.update(status="incomplete", contrasts={})
    progress = [json.loads(path.read_text())
                for path in sorted((out/"raw").glob("*.progress.json"))]
    completed = {row["job_key"]: row["actual_length"] for row in rows
                 if row["status"] == "completed"}
    progress_steps = {item["job_key"]: item["steps"] for item in progress}
    native_lower_bound = sum(completed.values()) + sum(
        max(progress_steps.get(row["job_key"], 0), row.get("partial_observed_steps", 0))
        for row in rows if row["job_key"] not in completed)
    native_lower_bound += sum(item["steps"] for item in progress
                              if item["job_key"] not in completed
                              and item["job_key"] not in {row["job_key"] for row in rows})
    summary.update(
        launch_sha=launch_sha, submitted_jobs=submitted,
        unstarted_jobs=[job["job_key"] for job in jobs if job["job_key"] not in submitted],
        actual_native_steps=native_lower_bound if summary["status"] == "complete" else None,
        known_native_step_lower_bound=native_lower_bound,
        fits_started=0, optimizer_steps=0, runner_error=runner_error,
        pool_errors=pool_errors, orphan_raw=orphans,
        parent_wall_seconds=time.monotonic()-started,
        parent_cpu_seconds=_cpu_seconds()-cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        evaluation_worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        evaluation_worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
    _write_json(out/"summary.json", summary)
    paths = [out/name for name in ("config.json", "perworld.json", "summary.json")]
    paths += list((out/"raw").glob("*"))
    artifacts = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                 for path in sorted(paths) if path.is_file()}
    _write_json(out/"manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                       "storage_bytes": sum(item["bytes"] for item in artifacts.values())})
    return summary
