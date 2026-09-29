"""One bounded S-only B05 batch, preserving native failures and exact controls."""

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

from .binding import ROOT, ORIGINALS, bind_controls, bind_source, verify_original_manifest, verify_pair
from .episode import ServiceShiftEpisode
from .readout import HORIZON, PANELS, SEEDS, plan, summarize

DIRECTION = "uav_persistent_service"
BATCH = "b05_service_shifts_a01"
REPO = Path(__file__).resolve().parents[4]


def worker(payload):
    job, out_string = payload
    if job not in plan():
        raise ValueError("undeclared B05 evaluation world")
    import torch

    torch.set_num_threads(1)
    faulthandler.enable()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw = out/"raw"/f"{stem}.npz"
    progress = out/"raw"/f"{stem}.progress.json"
    started, cpu_started = time.monotonic(), _cpu_seconds()
    episode = None
    row = job | {"status": "failed", "episode_constructed": False}
    try:
        episode = ServiceShiftEpisode(job["seed"])
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


def run(out: Path, launch_sha: str, workers: int = 4, *, repo: Path = REPO):
    if workers not in (1, 2, 3, 4):
        raise ValueError("B05 permits one through four single-thread workers")
    jobs = plan()
    out = Path(out).resolve()
    old_roots = [ROOT/spec["tag"] for spec in ORIGINALS.values()]
    if any(out == root or out.is_relative_to(root) for root in old_roots):
        raise ValueError("B05 output cannot enter a retained-control root")
    source = bind_source(repo)
    controls, binding = bind_controls()
    if any((out/name).exists() for name in (
            "config.json", "perworld.json", "summary.json", "manifest.json", "source-binding.json",
            "control-refs.json", "control-readings.json", "raw")):
        raise FileExistsError("B05 scientific artifacts already exist")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out/"raw").mkdir()
    _write_json(out/"source-binding.json", source)
    _write_json(out/"control-refs.json", binding)
    _write_json(out/"control-readings.json", [controls[s] for s in SEEDS])
    _write_json(out/"config.json", {
        "direction": DIRECTION, "batch": BATCH, "launch_sha": launch_sha,
        "jobs": jobs, "arms_new": ["S"], "seeds": SEEDS, "panels": PANELS,
        "horizon": HORIZON, "macro_steps": 30, "forecast_steps": 1200,
        "fits": 0, "optimizer_updates": 0, "max_new_native_transitions": len(SEEDS)*HORIZON,
        "evaluation_workers": workers, "numeric_threads_per_worker": 1,
        "shield": asdict(PRODUCTION_PARAMS), "original_control_jobs": 16,
        "original_control_native_steps_already_paid": 192000,
        "mission_service_denominator": HORIZON, "late_window": [6000, 12000],
        "fixed_bins": 3000, "final_reserve_window": [11700, 12000],
        "selection": "4a188a330; completed independent review eefe34dc6",
        "estimand": "S minus exact frozen R; exposed development worlds"})
    rows, submitted, pool_errors, pairing = [], [], [], {}
    order = [job["job_key"] for job in jobs]
    _write_json(out/"perworld.json", rows)
    _write_json(out/"summary.json", summarize(rows, controls, pairing))

    def on_result(row):
        if row["status"] == "completed":
            witness = verify_pair(out, row, controls[row["seed"]])
            pairing[row["seed"]] = witness
            if witness["status"] != "verified":
                row.update(status="incompatible_comparator", comparison_failure=witness)
        rows.append(row)
        rows.sort(key=lambda item: order.index(item["job_key"]))
        _write_json(out/"perworld.json", rows)
        _write_json(out/"summary.json", summarize(rows, controls, pairing))

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
    summary = summarize(rows, controls, pairing)
    orphans = orphan_raw_files(out, rows)
    rehash = {}
    for panel, spec in ORIGINALS.items():
        try:
            manifest = verify_original_manifest(ROOT/spec["tag"], spec)
            rehash[panel] = {"status": "verified", "artifacts": len(manifest["artifacts"]),
                             "bytes": manifest["storage_bytes"]}
        except BaseException as error:
            rehash[panel] = {"status": "failed", "error": f"{type(error).__name__}: {error}"}
    if runner_error or pool_errors or orphans or any(x["status"] != "verified" for x in rehash.values()):
        summary.update(status="incomplete", contrasts={}, panel_contrasts={}, use_rule={"status": "unresolved"})
    progress = [json.loads(path.read_text()) for path in sorted((out/"raw").glob("*.progress.json"))]
    completed = {row["job_key"]: row["actual_length"] for row in rows
                 if row.get("native_completed") and "actual_length" in row}
    observed = {item["job_key"]: item["steps"] for item in progress}
    for row in rows:
        observed[row["job_key"]] = max(observed.get(row["job_key"], 0),
                                        row.get("partial_observed_steps", 0), completed.get(row["job_key"], 0))
    summary.update(
        launch_sha=launch_sha, submitted_jobs=submitted,
        unstarted_jobs=[job["job_key"] for job in jobs if job["job_key"] not in submitted],
        actual_native_steps_completed_worlds=sum(completed.values()),
        known_native_step_lower_bound=sum(observed.values()),
        known_episode_constructions=sum(bool(row.get("episode_constructed")) for row in rows),
        submitted_without_construction_witness=[key for key in submitted
            if key not in {row["job_key"] for row in rows if "episode_constructed" in row}],
        fits_started=0, optimizer_steps=0, original_completion_rehash=rehash,
        runner_error=runner_error, pool_errors=pool_errors, orphan_raw=orphans,
        parent_wall_seconds=time.monotonic()-started, parent_cpu_seconds=_cpu_seconds()-cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        evaluation_worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        evaluation_worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
    _write_json(out/"summary.json", summary)
    paths = [out/name for name in ("config.json", "perworld.json", "summary.json",
                                    "source-binding.json", "control-refs.json", "control-readings.json")]
    paths += list((out/"raw").glob("*"))
    artifacts = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                 for path in sorted(paths) if path.is_file()}
    _write_json(out/"manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                     "storage_bytes": sum(item["bytes"] for item in artifacts.values())})
    return summary
