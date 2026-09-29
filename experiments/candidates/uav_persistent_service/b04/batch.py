"""Admitted R-only B04 panel against exact read-only original B02 controls."""

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
from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_persistent_service.b03.episode import LongMissionEpisode
from experiments.candidates.uav_persistent_service.constants import POLICY_SEED

from .binding import (HORIZON, ORIGINAL_ROOT, OLD_SOURCE, R_SOURCE, SEEDS,
                      bind_original, bind_source, verify_manifest)
from .readout import enrich_old_rows, plan, summarize, verify_new_triplet


DIRECTION = "uav_persistent_service"
BATCH = "b04_original_worlds_a01"
WORKERS = 4
MAX_NEW_NATIVE_STEPS = len(SEEDS)*HORIZON
REPO = Path(__file__).resolve().parents[4]


def worker(payload):
    job, out_string = payload
    if job not in plan():
        raise ValueError("undeclared B04 R evaluation world")
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
        episode = LongMissionEpisode(job["seed"], "R")
        while not episode.done:
            episode.macro_step(episode.controller.ordinary_action())
            _write_json(progress, job | {"status": "running", "steps": episode.t})
        row = episode.row() | job | {"native_completed": True, "episode_constructed": True}
        row.update(episode.save(raw, complete=True))
        _write_json(progress, job | {"status": "completed", "steps": episode.t})
    except BaseException as error:
        row = job | {"status": "failed", "error_type": type(error).__name__,
                     "error": str(error), "traceback": traceback.format_exc(),
                     "episode_constructed": episode is not None,
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


def compact_old_refs(binding: dict) -> dict:
    fields = ("job_key", "arm", "seed", "actual_length", "raw_path", "raw_sha256",
              "raw_bytes", "decisions_path", "decisions_sha256",
              "initial_state_sha256", "ground_bs_sha256", "user_xy_trace_sha256",
              "rng_state_stream_sha256")
    return {"root": binding["root"], "source_sha": OLD_SOURCE,
            "manifest_sha256": binding["manifest_sha256"],
            "config_sha256": binding["artifacts"]["config.json"]["sha256"],
            "perworld_sha256": binding["artifacts"]["perworld.json"]["sha256"],
            "summary_sha256": binding["artifacts"]["summary.json"]["sha256"],
            "rows": [{field: binding["rows"][key][field] for field in fields}
                     for seed in SEEDS for key in (f"O_H/{seed}", f"P/{seed}")]}


def run(out: Path, launch_sha: str, workers: int = WORKERS,
        *, old_root: Path = ORIGINAL_ROOT, repo: Path = REPO):
    if workers != WORKERS:
        raise ValueError("B04 requires four single-thread workers")
    jobs = plan()
    if len(jobs) != 8 or len({job["job_key"] for job in jobs}) != 8:
        raise ValueError("B04 fixed R plan differs")
    if Path(old_root) != ORIGINAL_ROOT:
        raise ValueError("B04 original-control root cannot be changed")
    out = Path(out).resolve()
    if out == old_root or out.is_relative_to(old_root):
        raise ValueError("B04 output cannot enter original-control root")

    # All source and original-evidence reads precede output creation or native construction.
    source = bind_source(repo)
    binding = bind_original(old_root)
    config = make_eval_config(HORIZON, POLICY_SEED)
    if config.time_step != 1.0:
        raise ValueError("B04 native step time differs from original station reconstruction")
    old_rows = enrich_old_rows(old_root, binding,
                               station_z=float(config.height_range[0]),
                               time_step_s=float(config.time_step))
    if any((out/name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json",
            "source-binding.json", "control-refs.json", "raw")):
        raise FileExistsError("B04 scientific artifacts already exist")

    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out/"raw").mkdir()
    _write_json(out/"source-binding.json", source)
    _write_json(out/"control-refs.json", compact_old_refs(binding))
    _write_json(out/"config.json", {
        "direction": DIRECTION, "batch": BATCH, "launch_sha": launch_sha,
        "jobs": jobs, "arms_new": ["R"], "seeds": SEEDS, "horizon": HORIZON,
        "macro_steps": 30, "fits": 0, "optimizer_updates": 0,
        "max_new_native_transitions": MAX_NEW_NATIVE_STEPS,
        "evaluation_workers": workers, "numeric_threads_per_worker": 1,
        "shield": asdict(PRODUCTION_PARAMS),
        "retained_R_source": R_SOURCE, "original_control_source": OLD_SOURCE,
        "original_control_root": str(old_root),
        "original_manifest_sha256": binding["manifest_sha256"],
        "original_control_jobs": 16, "original_control_native_steps_already_paid": 192000,
        "original_station_provenance": "native post xyz plus original legal-decoded station xy at native floor z",
        "original_station_z_m": float(config.height_range[0]),
        "mission_service_denominator": HORIZON,
        "late_window": [6000, 12000], "fixed_bins": 3000,
        "final_reserve_window": [11700, 12000]})
    rows, submitted, pool_errors, pairing = [], [], [], {}
    _write_json(out/"perworld.json", rows)
    _write_json(out/"summary.json", summarize(rows, old_rows, pairing))
    order = [job["job_key"] for job in jobs]

    def on_result(row):
        if row["status"] == "completed":
            witness = verify_new_triplet(old_root, out, old_rows, row)
            pairing[row["seed"]] = witness
            if witness["status"] != "verified":
                row["native_completed"] = True
                row["status"] = "incompatible_comparator"
                row["comparison_failure"] = witness
        rows.append(row)
        rows.sort(key=lambda item: order.index(item["job_key"]))
        _write_json(out/"perworld.json", rows)
        _write_json(out/"summary.json", summarize(rows, old_rows, pairing))

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
    summary = summarize(rows, old_rows, pairing)
    orphans = orphan_raw_files(out, rows)
    old_completion_rehash = None
    try:
        _, old_completion_rehash = verify_manifest(old_root)
    except BaseException as error:
        old_completion_rehash = {"status": "failed", "error_type": type(error).__name__,
                                 "error": str(error)}
    if runner_error or pool_errors or orphans or old_completion_rehash.get("status") == "failed":
        summary.update(status="incomplete", contrasts={})
    progress = [json.loads(path.read_text())
                for path in sorted((out/"raw").glob("*.progress.json"))]
    native_completed = {row["job_key"]: row["actual_length"] for row in rows
                        if row.get("native_completed") and "actual_length" in row}
    native_completed_steps = sum(native_completed.values())
    progress_steps = {item["job_key"]: item["steps"] for item in progress}
    lower_bound = native_completed_steps + sum(
        max(progress_steps.get(row["job_key"], 0), row.get("partial_observed_steps", 0))
        for row in rows if row["job_key"] not in native_completed)
    lower_bound += sum(item["steps"] for item in progress
                       if item["job_key"] not in native_completed
                       and item["job_key"] not in {row["job_key"] for row in rows})
    summary.update(
        launch_sha=launch_sha, submitted_jobs=submitted,
        unstarted_jobs=[job["job_key"] for job in jobs if job["job_key"] not in submitted],
        actual_native_steps_completed_worlds=native_completed_steps,
        known_native_step_lower_bound=lower_bound,
        known_episode_constructions=sum(bool(row.get("episode_constructed")) for row in rows),
        submitted_without_construction_witness=[key for key in submitted
            if key not in {row["job_key"] for row in rows if "episode_constructed" in row}],
        fits_started=0, optimizer_steps=0,
        original_control_native_steps_already_paid=192000,
        original_completion_rehash=old_completion_rehash,
        runner_error=runner_error, pool_errors=pool_errors, orphan_raw=orphans,
        parent_wall_seconds=time.monotonic()-started,
        parent_cpu_seconds=_cpu_seconds()-cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        evaluation_worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        evaluation_worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
    _write_json(out/"summary.json", summary)
    paths = [out/name for name in ("config.json", "perworld.json", "summary.json",
                                    "source-binding.json", "control-refs.json")]
    paths += list((out/"raw").glob("*"))
    artifacts = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                 for path in sorted(paths) if path.is_file()}
    _write_json(out/"manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                       "storage_bytes": sum(item["bytes"] for item in artifacts.values())})
    return summary
