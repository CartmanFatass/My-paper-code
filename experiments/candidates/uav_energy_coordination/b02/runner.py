"""Bounded native I/P collection with paired, adverse-inclusive readout."""

from __future__ import annotations

import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
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
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_energy_coordination.b01.readout import enrich_world, summarize
from experiments.candidates.uav_energy_coordination.b01.runner import (
    CoordinationObserver, _effective_s2,
)

from .controller import COST_KEYS, FrozenController, source_records

DIRECTION = "uav_energy_coordination"
BATCH = "b02_i_vs_p_a01"
HORIZON = 3000
SEEDS = tuple(range(41092801, 41092809))
ARMS = ("I", "P")
INTERPRETATION = (
    "I and P are distinct complete native packages with different clocks, models and costs; "
    "signed native gains and risk/compute are read separately, without a mechanism attribution"
)


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def validate_plan(jobs):
    if (ARMS != ("I", "P") or SEEDS != tuple(range(41092801, 41092809))
            or HORIZON != 3000 or jobs != plan() or len(jobs) != 16):
        raise ValueError("B02 requires the fixed 16-job eight-seed I/P panel")


def _summarize(rows, expected_keys):
    return summarize(rows, SEEDS, expected_keys, arms=ARMS, comparisons=(("I", "P"),),
                     interpretation=INTERPRETATION)


def _known_costs(controller):
    costs = dict(controller.costs)
    if set(costs) != set(COST_KEYS):
        raise ValueError("B02 controller cost fields differ from contract")
    result = {key: float(value) for key, value in costs.items()}
    if any(not np.isfinite(value) or value < 0 for value in result.values()):
        raise ValueError("B02 controller cost is nonfinite or negative")
    return result


def _check_world_costs(arm, costs):
    if costs["primitive_forecast_steps"] != 0:
        raise ValueError("B02 frozen programs must use zero primitive forecast steps")
    if arm == "I":
        if (costs["score_requests"] > 7350 or costs["service_snapshots"] > 22050
                or costs["decision_clocks"] > 50):
            raise ValueError("I exceeded its fixed per-world work bound")
    elif (costs["score_requests"] > 2700 or costs["p_shared_baseline_snapshots"] > 300
          or costs["service_snapshots"] > 5700 or costs["decision_clocks"] > 300):
        raise ValueError("P exceeded its fixed per-world work bound")


def _p_readings(arrays):
    fallback = np.asarray(arrays["transit_fallback"])
    candidates = np.asarray(arrays["transit_candidate_count"], dtype=np.int64)
    selected = np.asarray(arrays["transit_selected_hold_uav"], dtype=np.int64)
    gains = np.asarray(arrays["transit_selected_proxy_gain"], dtype=np.float64)
    active = fallback == ""
    return {
        "P_planner_windows": int(len(fallback)),
        "P_active_windows": int(np.count_nonzero(active)),
        "P_fallback_windows": int(np.count_nonzero(~active)),
        "P_candidate_scores": int(np.sum(candidates[active])),
        "P_selected_hold_windows": int(np.count_nonzero(selected >= 0)),
        "P_selected_hold_near_tie_windows": int(np.count_nonzero(
            (selected >= 0) & (gains > 0) & (gains <= 1e-12))),
    }


def _worker(payload):
    job, out_string, threads = payload
    out = Path(out_string)
    raw_path = out / "raw" / f"{job['arm']}_{job['seed']}.npz"
    progress_path = out / "raw" / f"{job['arm']}_{job['seed']}.progress.json"
    started, cpu_started = time.monotonic(), _cpu_seconds()
    env = controller = observer = native_steps = None
    completed_steps = 0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "running"})

    try:
        if job not in plan() or threads != 1:
            raise ValueError("world outside fixed B02 plan or numeric thread contract")
        import torch

        torch.set_num_threads(threads)
        config = make_eval_config(HORIZON, 0)
        env = make_env(config, job["seed"])
        effective = _effective_s2(env)
        controller = FrozenController(job["arm"], env, config)
        observer = CoordinationObserver(env.env)
        row, native_steps = evaluate_world(controller, env, config, job["seed"],
                                           PRODUCTION_PARAMS, progress=progress, observer=observer)
        observed = observer.as_arrays()
        if (not np.array_equal(observed["observed_native_metrics"], native_steps["metrics"])
                or not np.allclose(observed["observed_native_reward"], native_steps["reward"],
                                   rtol=0, atol=1e-12)
                or not np.allclose(observed["observed_battery_ratio"], native_steps["battery"],
                                   rtol=0, atol=3e-8)):
            raise ValueError("failure-preserving native trace differs from shared evaluator")
        if not 1 <= row["actual_length"] <= HORIZON:
            raise ValueError("native episode length exceeds B02 horizon")
        if completed_steps != row["actual_length"] or any(
                len(value) != row["actual_length"] for key, value in observed.items()
                if key != "user_xy_m") or len(observed["user_xy_m"]) != row["actual_length"] + 1:
            raise ValueError("native and read-only observer lengths differ")
        decisions = controller.validate_trace(row["actual_length"])
        decisions = {key: np.asarray(value) for key, value in decisions.items()}
        if any(value.dtype.kind == "O" for value in decisions.values()):
            raise ValueError("B02 decision trace contains object arrays")
        costs = _known_costs(controller)
        _check_world_costs(job["arm"], costs)
        row = enrich_world(row, native_steps, observed, decisions,
                           reserve_ratio=effective["return_reserve_ratio"],
                           cutoff_ratio=effective["service_cutoff_threshold"],
                           time_step=float(config.time_step))
        if job["arm"] == "P":
            row.update(_p_readings(decisions))
        row.update(job, status="completed", **observer.digests(), effective_config=effective,
                   costs=costs, plan_input_steps=list(controller.plan_input_steps))
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **native_steps, **observed, **decisions,
                            metric_fields=np.asarray(TRACE_FIELDS))
        row.update(raw_path=str(raw_path.relative_to(out)), raw_sha256=_sha256(raw_path),
                   raw_bytes=raw_path.stat().st_size)
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "completed"})
        return row | {"worker_wall_seconds": time.monotonic() - started,
                      "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                      "worker_peak_rss_kib": _rss_kib()}
    except BaseException as error:
        record = {**job, "status": "failed", "error_type": type(error).__name__,
                  "error": str(error), "traceback": traceback.format_exc(),
                  "partial_observed_steps": completed_steps,
                  "worker_wall_seconds": time.monotonic() - started,
                  "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                  "worker_peak_rss_kib": _rss_kib(),
                  "in_progress_clock_costs": "unknown after failure"}
        if controller is not None:
            try:
                record["known_completed_clock_costs"] = _known_costs(controller)
            except BaseException as cost_error:
                record["cost_preservation_error"] = repr(cost_error)
        try:
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "failed"})
            if raw_path.exists():
                record.update(incomplete_raw_path=str(raw_path.relative_to(out)),
                              incomplete_raw_sha256=_sha256(raw_path),
                              incomplete_raw_bytes=raw_path.stat().st_size)
            elif observer is not None and observer.user_xy:
                partial = raw_path.with_name(raw_path.stem + "_partial.npz")
                decisions = {}
                if controller is not None:
                    try:
                        decisions = {key: np.asarray(value) for key, value in
                                     controller.decision_arrays().items()}
                        if any(value.dtype.kind == "O" for value in decisions.values()):
                            raise ValueError("partial B02 decision array has object dtype")
                    except BaseException as decision_error:
                        record["decision_preservation_error"] = repr(decision_error)
                        decisions = {}
                np.savez_compressed(partial, **(native_steps or {}), **observer.as_arrays(),
                                    **decisions, metric_fields=np.asarray(TRACE_FIELDS))
                record.update(partial_path=str(partial.relative_to(out)),
                              partial_sha256=_sha256(partial), partial_bytes=partial.stat().st_size,
                              partial_native_steps=(len(native_steps["reward"])
                                                    if native_steps is not None else None))
        except BaseException as preservation_error:
            record["partial_preservation_error"] = repr(preservation_error)
        return record
    finally:
        if controller is not None:
            try:
                controller.close()
            except BaseException:
                pass
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def _cost_totals(rows):
    totals = {arm: {key: 0.0 for key in COST_KEYS} for arm in ARMS}
    incomplete = []
    for row in rows:
        cost = row.get("costs") if row.get("status") == "completed" else row.get(
            "known_completed_clock_costs")
        if cost is None:
            incomplete.append(row["job_key"])
            continue
        for key in COST_KEYS:
            totals[row["arm"]][key] += float(cost[key])
        if row.get("status") != "completed":
            incomplete.append(row["job_key"])
    return totals, incomplete


def run(out: Path, launch_sha: str, workers: int = 2, threads: int = 1):
    jobs = plan()
    validate_plan(jobs)
    if workers != 2 or threads != 1:
        raise ValueError("B02 requires two workers and one numeric thread")
    out = Path(out)
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B02 scientific artifacts already exist: {out}")
    sources = source_records()
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", _summarize([], expected_keys))
    probe = make_env(make_eval_config(HORIZON, 0), SEEDS[0])
    try:
        effective = _effective_s2(probe)
    finally:
        probe.close()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": BATCH, "launch_sha": launch_sha,
        "horizon": HORIZON, "seeds": list(SEEDS), "arms": list(ARMS), "jobs": jobs,
        "workers": workers, "threads_per_worker": threads, "fits": 0,
        "optimizer_updates": 0, "max_episodes": 16, "max_transitions": 48000,
        "I_max_score_requests": 58800, "I_max_service_snapshots": 176400,
        "P_max_candidate_scores": 21600, "P_max_shared_q0_snapshots": 2400,
        "P_max_service_snapshots": 45600, "combined_max_service_snapshots": 222000,
        "primitive_forecast_steps": 0, "source_records": sources,
        "declared_source_input_bytes": sum(
            (Path(__file__).resolve().parents[4] / name).stat().st_size
            for name in sources["sha256"]),
        "cost_meanings": {"score_requests": "I requested whole plans or P candidate plan scores",
                          "service_snapshots": "actual native scorer/routing calls including P shared q0",
                          "p_shared_baseline_snapshots": "one native q0 per active P decision clock",
                          "decision_tick_wall_seconds": "wall time in controller decisions; includes fallback clocks",
                          "controller_wall_seconds": "full proposal wall including P projections/deep copies",
                          "worker_wall_seconds": "whole native world, summed separately from invocation elapsed"},
        "shield": asdict(PRODUCTION_PARAMS), "trace_timing": TRACE_TIMING,
        "observation_layout": S7S2_LAYOUT.record(), "effective_raw": effective,
        "pairing": "same seed; initial state, full user path and native RNG stream hashed",
        "comparison": "complete I minus complete P, native J/service/risk and separate compute",
    })
    rows, submitted, pool_errors = [], [], []

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", _summarize(rows, expected_keys))

    runner_error = None
    try:
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(executor, jobs, workers,
                                             lambda job: (job, str(out), threads),
                                             on_result, submitted, worker_fn=_worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = _summarize(rows, expected_keys)
    orphan = orphan_raw_files(out, rows)
    completed = sum(int(row["actual_length"]) for row in rows if row["status"] == "completed")
    partial = sum(int(row.get("partial_observed_steps", 0)) for row in rows
                  if row["status"] != "completed")
    totals, unknown_cost_jobs = _cost_totals(rows)
    bound_errors = []
    if (totals["I"]["score_requests"] > 58800
            or totals["I"]["service_snapshots"] > 176400):
        bound_errors.append("I work bound exceeded")
    if (totals["P"]["score_requests"] > 21600
            or totals["P"]["p_shared_baseline_snapshots"] > 2400
            or totals["P"]["service_snapshots"] > 45600):
        bound_errors.append("P work bound exceeded")
    if sum(totals[arm]["service_snapshots"] for arm in ARMS) > 222000:
        bound_errors.append("combined service snapshot bound exceeded")
    if completed + partial > 48000:
        bound_errors.append("known native transitions exceeded B02 budget")
    summary.update(
        launch_sha=launch_sha, fits=0, optimizer_updates=0, submitted_jobs=submitted,
        unstarted_jobs=[key for key in expected_keys if key not in submitted],
        completed_transitions=completed, partial_observed_transitions=partial,
        known_transition_lower_bound=completed + partial,
        actual_transitions=completed if summary["status"] == "complete" else None,
        total_actual_costs_lower_bound=totals, unknown_or_incomplete_cost_jobs=unknown_cost_jobs,
        cost_bound_errors=bound_errors, orphan_raw=orphan,
        pool_errors=pool_errors, runner_error=runner_error,
        elapsed_invocation_seconds=time.monotonic() - started,
        parent_cpu_seconds=_cpu_seconds() - cpu_started, parent_peak_rss_kib=_rss_kib(),
        worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows),
        worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in rows
                                    if "worker_peak_rss_kib" in row), default=None),
        worker_resources_unmeasured=[row["job_key"] for row in rows
                                     if "worker_cpu_seconds" not in row or "worker_peak_rss_kib" not in row],
    )
    if orphan or pool_errors or runner_error or bound_errors:
        summary["status"] = "incomplete"
        summary["actual_transitions"] = None
        contrast = summary["contrasts"]["I-P"]
        contrast["status"] = "descriptive_unverified_run"
        for endpoint in contrast["endpoints"].values():
            endpoint["t95_descriptive"] = None
    _write_json(out / "summary.json", summary)
    artifacts = {name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
                 for name in ("config.json", "perworld.json", "summary.json")}
    raw = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
           for path in sorted((out / "raw").iterdir()) if path.is_file()}
    _write_json(out / "manifest.json", {
        "launch_sha": launch_sha, "artifacts": artifacts, "raw": raw,
        "storage_bytes": sum(item["bytes"] for item in (*artifacts.values(), *raw.values())),
    })
    return summary
