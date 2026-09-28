"""Fixed S7-S2 B01 batch with bounded submission and retained failure evidence."""

from __future__ import annotations

import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_availability.b05.runner import PairingObserver
from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    HeuristicController, TRACE_FIELDS, TRACE_TIMING, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

from .readout import enrich_world, summarize

DIRECTION = "uav_energy_coordination"
BATCH = "b01_analytical_coordination_a01"
HORIZON = 3000
SEEDS = tuple(range(31092801, 31092809))
ARMS = ("H", "I", "C")
COST_KEYS = ("score_requests", "model_evaluations", "service_snapshots", "event_count",
             "phase_count", "planner_wall_seconds")
DECISION_FIELDS = ("planner_step", "planner_horizon", "planner_sample_times",
                   "planner_selected_positions", "planner_selected_batteries",
                   "planner_selected_qos", "planner_selected_risk", "planner_incumbent_score",
                   "planner_selected_score", "planner_goals", "planner_station_ids",
                   "planner_score_requests", "planner_model_evaluations",
                   "planner_service_snapshots", "planner_event_count")


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def validate_plan(jobs):
    if jobs != plan() or len(jobs) != 24 or len(set(SEEDS)) != 8:
        raise ValueError("B01 requires the fixed 24-job, eight-seed panel")


class CoordinationObserver(PairingObserver):
    """Read-only native trace; nothing gathered here enters a planner proposal."""

    def __init__(self, raw):
        super().__init__(raw)
        self.trace = {key: [] for key in (
            "proposed_actions", "submitted_actions", "actual_velocities_mps",
            "actual_xyz_post_m", "actual_energy_input_wh", "actual_energy_consumed_wh",
            "actual_user_delivered_ratio", "selected_goals", "selected_station_ids",
            "observed_native_metrics", "observed_native_reward", "observed_battery_ratio")}

    def on_step(self, *, t, proposal_t, submitted_t, controller, **kwargs):
        super().on_step(t=t)
        raw = self.raw
        # This read-only copy survives a later planner failure before the shared
        # evaluator can return its own in-memory reward/metric/battery arrays.
        native = {**raw._energy_metrics_dict(), **raw.last_constrained_reward_metrics}
        self.trace["observed_native_metrics"].append(
            np.asarray([native[field] for field in TRACE_FIELDS], dtype=np.float64))
        self.trace["observed_native_reward"].append(float(native["scenario7_reward"]))
        self.trace["observed_battery_ratio"].append(raw.uav_battery_ratios.copy())
        demand = np.asarray(raw.last_reward_demand_bps, dtype=np.float64)
        delivered = np.asarray(raw.last_delivered_traffic_bps, dtype=np.float64)
        if demand.ndim != 1 or not np.all(demand > 0) or demand.shape != delivered.shape:
            raise ValueError("native user delivery trace lacks positive demand")
        self.trace["proposed_actions"].append(np.asarray(proposal_t, dtype=np.float32).copy())
        self.trace["submitted_actions"].append(np.asarray(submitted_t, dtype=np.float32).copy())
        self.trace["actual_velocities_mps"].append(np.asarray(raw.last_actual_velocities, dtype=np.float64).copy())
        self.trace["actual_xyz_post_m"].append(np.asarray(raw.uav_positions, dtype=np.float64).copy())
        self.trace["actual_energy_input_wh"].append(np.asarray(raw.last_energy_charged_wh, dtype=np.float64).copy())
        self.trace["actual_energy_consumed_wh"].append(np.asarray(raw.last_energy_consumed_wh, dtype=np.float64).copy())
        self.trace["actual_user_delivered_ratio"].append(delivered / demand)
        goals = getattr(controller, "goals", None)
        if goals is None:
            targets = np.asarray(controller.targets_xy, dtype=np.float64)
            goals = np.column_stack((targets, np.where(np.isfinite(targets).all(axis=1),
                                                 100.0, np.nan)))
        self.trace["selected_goals"].append(np.asarray(goals, dtype=np.float64).copy())
        stations = getattr(controller, "station_ids", None)
        self.trace["selected_station_ids"].append(
            np.asarray(stations, dtype=np.int16).copy() if stations is not None
            else np.full(8, -1, dtype=np.int16))

    def as_arrays(self):
        return {**super().as_arrays(),
                **{key: np.asarray(value) for key, value in self.trace.items()}}


def _effective_s2(env):
    raw = env.env
    expected = {"energy_stage": "S2", "n_uavs": 8, "n_users": 30,
                "n_ground_bs": 1, "n_charging_stations": 2,
                "routing_protocol": "widest_path", "max_steps": HORIZON,
                "battery_capacity_wh": 160.0, "failure_enabled": False}
    for key, value in expected.items():
        if getattr(raw, key) != value:
            raise ValueError(f"native S7-S2 {key} differs from fixed contract")
    if env.observation_space.shape != (8, 365) or env.action_space.shape != (8, 4):
        raise ValueError("native S7-S2 adapter shape differs")
    return expected | {"return_reserve_ratio": float(raw.return_reserve_ratio),
                       "service_cutoff_threshold": float(raw.service_cutoff_threshold),
                       "charging_station_capacity": raw.charging_station_capacity[:2].tolist()}


def _decisions(controller, arm, length):
    if arm == "H":
        return {}
    arrays = controller.decision_arrays()
    if not set(DECISION_FIELDS).issubset(arrays):
        raise ValueError("analytical decision trace lacks B01 required fields")
    arrays = {key: np.asarray(value) for key, value in arrays.items()}
    clocks = np.asarray(arrays["planner_step"], dtype=np.int64)
    if (len(clocks) > 50 or not np.array_equal(clocks, np.arange(0, length, 60))
            or len(controller.plan_input_steps) != len(clocks)
            or not np.array_equal(controller.plan_input_steps, clocks)):
        raise ValueError("analytical replan clocks exceed or differ from B01 contract")
    if len(controller.decision_records) != len(clocks):
        raise ValueError("analytical decision record count differs from clocks")
    expected_horizon = np.minimum(600, HORIZON - clocks)
    if not np.array_equal(arrays["planner_horizon"], expected_horizon):
        raise ValueError("analytical horizon differs from remaining native steps")
    if not np.array_equal(arrays["planner_sample_times"], expected_horizon[:, None] *
                          np.asarray([1, 2, 3])[None, :] // 3):
        raise ValueError("analytical sample times differ from three right endpoints")
    expected_shapes = {"planner_selected_positions": (len(clocks), 3, 8, 3),
                       "planner_selected_batteries": (len(clocks), 3, 8),
                       "planner_selected_qos": (len(clocks), 3),
                       "planner_selected_risk": (len(clocks), 3),
                       "planner_goals": (len(clocks), 8, 3),
                       "planner_station_ids": (len(clocks), 8)}
    for key, shape in expected_shapes.items():
        if arrays[key].shape != shape:
            raise ValueError(f"{key} shape differs from B01 contract")
    bound = 147 if arm == "I" else 146
    requested = np.asarray(arrays["planner_score_requests"], dtype=np.int64)
    evaluated = np.asarray(arrays["planner_model_evaluations"], dtype=np.int64)
    snapshots = np.asarray(arrays["planner_service_snapshots"], dtype=np.int64)
    if (requested.shape != (len(clocks),) or np.any(requested > bound)
            or np.any(requested < evaluated) or np.any(evaluated < 0)
            or np.any(snapshots != 3 * evaluated)):
        raise ValueError("analytical search exceeds per-clock score/snapshot bound")
    for key, values in arrays.items():
        if values.dtype.kind == "O":
            raise ValueError(f"object-valued decision array {key} is not NPZ-safe")
    return arrays


def _costs(controller, arm, decisions):
    costs = {key: 0 for key in COST_KEYS} if arm == "H" else dict(controller.costs)
    if set(costs) != set(COST_KEYS) or any(not np.isfinite(float(value)) or float(value) < 0
                                           for value in costs.values()):
        raise ValueError("planner cost contract differs or contains non-finite values")
    if arm != "H":
        mapping = {"score_requests": "planner_score_requests",
                   "model_evaluations": "planner_model_evaluations",
                   "service_snapshots": "planner_service_snapshots",
                   "event_count": "planner_event_count"}
        for key, array_key in mapping.items():
            if int(costs[key]) != int(np.sum(decisions[array_key])):
                raise ValueError(f"{key} differs from decision trace total")
    return costs


def _aggregate_costs(rows):
    """Completed clocks remain known work even if their world later failed."""
    totals = {key: sum(row.get("costs", row.get("known_completed_clock_costs", {})).get(key, 0)
                       for row in rows) for key in COST_KEYS}
    unknown = [row["job_key"] for row in rows
               if row["status"] in ("failed", "unreconciled")]
    return totals, unknown


def _worker(payload):
    job, out_string, threads = payload
    out = Path(out_string)
    raw_path = out / "raw" / f"{job['arm']}_{job['seed']}.npz"
    progress_path = out / "raw" / f"{job['arm']}_{job['seed']}.progress.json"
    started, cpu_started = time.monotonic(), _cpu_seconds()
    env = controller = observer = None
    steps = None
    completed_steps = 0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "running"})

    try:
        if job not in plan() or threads != 1:
            raise ValueError("world outside fixed plan or numeric thread contract")
        import torch

        torch.set_num_threads(threads)
        config = make_eval_config(HORIZON, 0)
        env = make_env(config, job["seed"])
        effective = _effective_s2(env)
        if job["arm"] == "H":
            controller = HeuristicController(variant("H1", information="central", replan_period=30), env)
        else:
            from .controller import AnalyticalController

            controller = AnalyticalController(job["arm"], env, config)
        observer = CoordinationObserver(env.env)
        row, steps = evaluate_world(controller, env, config, job["seed"],
                                    PRODUCTION_PARAMS, progress=progress, observer=observer)
        observed = observer.as_arrays()
        if (not np.array_equal(observed["observed_native_metrics"], steps["metrics"])
                or not np.allclose(observed["observed_native_reward"], steps["reward"],
                                   rtol=0, atol=1e-12)
                or not np.allclose(observed["observed_battery_ratio"], steps["battery"],
                                   rtol=0, atol=3e-8)):
            raise ValueError("failure-preserving native trace differs from shared evaluator")
        if not 1 <= row["actual_length"] <= HORIZON:
            raise ValueError("native episode length exceeds fixed B01 horizon")
        if completed_steps != row["actual_length"] or any(
                len(value) != row["actual_length"] for key, value in observed.items()
                if key != "user_xy_m") or len(observed["user_xy_m"]) != row["actual_length"] + 1:
            raise ValueError("native and observer lengths differ")
        decisions = _decisions(controller, job["arm"], row["actual_length"])
        costs = _costs(controller, job["arm"], decisions)
        row = enrich_world(row, steps, observed, decisions,
                           reserve_ratio=effective["return_reserve_ratio"],
                           cutoff_ratio=effective["service_cutoff_threshold"],
                           time_step=float(config.time_step))
        row.update(job, status="completed", **observer.digests(),
                   effective_config=effective, costs=costs,
                   plan_input_steps=list(controller.plan_input_steps))
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **steps, **observed, **decisions,
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
                  "worker_peak_rss_kib": _rss_kib()}
        if controller is not None and hasattr(controller, "costs"):
            try:
                record["known_completed_clock_costs"] = {
                    key: float(value) for key, value in controller.costs.items()}
                record["in_progress_clock_costs"] = "unknown after failure"
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
                decision_arrays = {}
                if controller is not None and hasattr(controller, "decision_arrays"):
                    try:
                        decision_arrays = {key: np.asarray(value) for key, value in
                                           controller.decision_arrays().items()}
                        if any(value.dtype.kind == "O" for value in decision_arrays.values()):
                            raise ValueError("partial planner trace contains object arrays")
                    except BaseException as decision_error:
                        record["decision_preservation_error"] = repr(decision_error)
                        decision_arrays = {}
                preserved = {} if steps is None else dict(steps)
                preserved.update(observer.as_arrays())
                preserved.update(decision_arrays)
                np.savez_compressed(partial, **preserved, metric_fields=np.asarray(TRACE_FIELDS))
                record.update(partial_path=str(partial.relative_to(out)),
                              partial_sha256=_sha256(partial), partial_bytes=partial.stat().st_size,
                              native_evaluator_arrays_returned=steps is not None)
        except BaseException as preservation_error:
            record["partial_preservation_error"] = repr(preservation_error)
        return record
    finally:
        if controller is not None and hasattr(controller, "close"):
            try:
                controller.close()
            except BaseException:
                pass
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def run(out: Path, launch_sha: str, workers: int = 2, threads: int = 1):
    jobs = plan()
    validate_plan(jobs)
    if workers < 1 or threads != 1:
        raise ValueError("B01 requires positive workers and one numeric thread")
    out = Path(out)
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B01 scientific artifacts already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], SEEDS, expected_keys))
    probe = make_env(make_eval_config(HORIZON, 0), SEEDS[0])
    try:
        effective = _effective_s2(probe)
    finally:
        probe.close()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": BATCH, "launch_sha": launch_sha,
        "horizon": HORIZON, "seeds": list(SEEDS), "arms": list(ARMS), "jobs": jobs,
        "workers": workers, "threads_per_worker": threads, "fits": 0,
        "optimizer_updates": 0, "max_episodes": 24, "max_transitions": 72000,
        "max_plan_requests": 117200, "max_service_snapshots": 351600,
        "shield": asdict(PRODUCTION_PARAMS),
        "H": variant("H1", information="central", replan_period=30).record(),
        "analytical_replan_period": 60, "trace_timing": TRACE_TIMING,
        "analytical_forecast_seconds": 600,
        "analytical_sample_rule": "three equal-interval right endpoints, truncated to remaining horizon",
        "analytical_score": "sum(interval_seconds * (native_snapshot_qos - 2*capped_return_cost)) - 5*new_cutoff - 10*new_depletion",
        "analytical_cycle_rule": "one nominal return visit, fluid lowest-Wh station input, no second forecast recharge",
        "analytical_information": "current central user/BS xy at planning clocks plus legal energy/geometry and own observation history; no live model copy",
        "observation_layout": S7S2_LAYOUT.record(), "effective_raw": effective,
        "pairing": "same seed; initial state, full user path and native RNG stream hashed",
        "forecast_reading": "held itinerary versus realized closed-loop replanning discrepancy",
    })
    rows, submitted, pool_errors = [], [], []

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, SEEDS, expected_keys))

    runner_error = None
    try:
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, workers, lambda job: (job, str(out), threads),
                on_result, submitted, worker_fn=_worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows, SEEDS, expected_keys)
    orphans = orphan_raw_files(out, rows)
    completed = sum(row["actual_length"] for row in rows if row["status"] == "completed")
    partial = sum(row.get("partial_observed_steps", 0) for row in rows if row["status"] != "completed")
    total_costs, unknown_cost_jobs = _aggregate_costs(rows)
    if total_costs["score_requests"] > 117200 or total_costs["service_snapshots"] > 351600:
        summary["cost_bound_error"] = "batch planner budget exceeded"
    if completed + partial > 72000:
        summary["transition_bound_error"] = "known transitions exceed fixed B01 budget"
    summary.update(
        launch_sha=launch_sha, fits=0, optimizer_updates=0, submitted_jobs=submitted,
        unstarted_jobs=[key for key in expected_keys if key not in submitted],
        completed_transitions=completed, partial_observed_transitions=partial,
        known_transition_lower_bound=completed + partial,
        actual_transitions=completed if summary["status"] == "complete" else None,
        total_actual_costs=total_costs, orphan_raw=orphans,
        planner_costs_status="known_lower_bound" if unknown_cost_jobs or orphans else "complete_for_submitted_jobs",
        unknown_planner_cost_jobs=unknown_cost_jobs,
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
    if (orphans or pool_errors or runner_error or "cost_bound_error" in summary
            or "transition_bound_error" in summary):
        summary["status"] = "incomplete"
        summary["actual_transitions"] = None
        for contrast in summary["contrasts"].values():
            contrast["status"] = "descriptive_unverified_run"
            for endpoint in contrast["endpoints"].values():
                endpoint["t95_descriptive"] = None
    _write_json(out / "summary.json", summary)
    artifacts = {name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
                 for name in ("config.json", "perworld.json", "summary.json")}
    raw = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
           for path in sorted((out / "raw").iterdir()) if path.is_file()}
    _write_json(out / "manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                        "raw": raw,
                                        "storage_bytes": sum(item["bytes"] for item in
                                                             (*artifacts.values(), *raw.values()))})
    return summary
