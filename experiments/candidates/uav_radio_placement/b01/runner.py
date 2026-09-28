"""One fixed complete native H/G/R panel with retained per-world evidence."""

from __future__ import annotations

import json
import multiprocessing
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_availability.b04.runner import PairingObserver, _effective_s2
from experiments.candidates.energy_relay_availability.b04.transit_hold import battery_tail_readings
from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from .readout import ARMS, summarize


DIRECTION = "uav_radio_placement"
HORIZON = 3000
SEEDS = tuple(range(36092801, 36092809))


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for arm in ARMS for seed in SEEDS]


def _plain(value):
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


class PlacementObserver(PairingObserver):
    def __init__(self, raw):
        super().__init__(raw)
        self.physical_xyz = []
        self.proposals = []
        self.submitted = []
        self.velocities = []
        self.consumed_wh = []

    @contextmanager
    def attach(self, controller):
        with super().attach(controller):
            self.physical_xyz.append(self.raw.uav_positions.copy())
            yield

    def on_step(self, *, t, proposal_t, submitted_t, **kwargs):
        super().on_step(t=t)
        self.physical_xyz.append(self.raw.uav_positions.copy())
        self.proposals.append(np.asarray(proposal_t).copy())
        self.submitted.append(np.asarray(submitted_t).copy())
        self.velocities.append(self.raw.last_actual_velocities.copy())
        self.consumed_wh.append(self.raw.last_energy_consumed_wh.copy())

    def as_arrays(self):
        return {**super().as_arrays(),
                "physical_xyz_m": np.asarray(self.physical_xyz, dtype=np.float64),
                "proposal_actions": np.asarray(self.proposals, dtype=np.float32),
                "submitted_actions": np.asarray(self.submitted, dtype=np.float32),
                "actual_velocity_mps": np.asarray(self.velocities, dtype=np.float64),
                "consumed_wh": np.asarray(self.consumed_wh, dtype=np.float64)}


def _world_extra(row, steps, observer, records, raw, arm):
    expected = list(range(0, row["actual_length"], 30))
    if [record["step"] for record in records] != expected:
        raise ValueError("spatial planner did not keep the fixed 30-step clock")
    query_bound = 100 if arm == "R" else 1
    if any(not 0 <= record["query_count"] <= query_bound for record in records):
        raise ValueError("spatial planner exceeded its fixed query budget")
    arrays = observer.as_arrays()
    displacements = np.diff(arrays["physical_xyz_m"], axis=0)
    if displacements.shape != (row["actual_length"], 8, 3):
        raise ValueError("native physical trajectory is incomplete")
    row.update(battery_tail_readings(steps["battery"], reserve_ratio=raw.return_reserve_ratio,
                                    service_cutoff_ratio=raw.service_cutoff_threshold))
    qos = steps["metrics"][:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
    zeros = qos == 0.0
    edges = np.diff(np.concatenate(([False], zeros, [False])).astype(np.int8))
    gaps = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
    row.update(
        xy_path_m=float(np.linalg.norm(displacements[:, :, :2], axis=-1).sum()),
        xyz_path_m=float(np.linalg.norm(displacements, axis=-1).sum()),
        consumed_wh=float(arrays["consumed_wh"].sum()),
        negative_margin_uav_step_fraction=float(np.mean(steps["return_margin"] < 0)),
        zero_service_steps=int(zeros.sum()), longest_zero_service_gap=int(gaps.max(initial=0)),
        planner_windows=len(records),
        service_snapshot_calls=sum(record["query_count"] for record in records),
        planner_cpu_seconds=sum(record["planner_cpu_seconds"] for record in records),
        planner_wall_seconds=sum(record["planner_wall_seconds"] for record in records),
        selected_static_qos_mean=float(np.mean([record["selected_qos"] for record in records])),
    )
    for index, (lo, hi) in enumerate(((0, 1000), (1000, 2000), (2000, 3000))):
        window = slice(lo, min(hi, row["actual_length"]))
        if len(qos[window]):
            row[f"fixed_third_{index}_qos"] = float(qos[window].mean())
            row[f"fixed_third_{index}_J"] = float(steps["reward"][window].sum())
    for baseline in ("H", "G"):
        valid = [record for record in records if record.get(f"initial_{baseline}_qos") is not None]
        if arm == "R" and valid:
            gains = [record["selected_qos"] - record[f"initial_{baseline}_qos"] for record in valid]
            row[f"same_snapshot_selected_minus_{baseline}_qos"] = float(np.mean(gains))
            row[f"same_snapshot_strict_gain_over_{baseline}_windows"] = sum(gap > 1e-10 for gap in gains)


def _simulate_world(job, out, threads, config=None):
    from .placement import PlacementController
    import torch

    started, cpu_started = time.monotonic(), _cpu_seconds()
    env = model_env = observer = controller = None
    raw_path = Path(out) / "raw" / f"{job['arm']}_{job['seed']}.npz"
    try:
        torch.set_num_threads(threads)
        config = make_eval_config(HORIZON, policy_seed=0) if config is None else config
        env = make_env(config, job["seed"])
        model_env = make_env(config, 0)
        model_env.reset(seed=0)
        raw = env.env
        if (raw.energy_stage != "S2" or raw.routing_protocol != "widest_path"
                or raw.failure_enabled or env.observation_space.shape != (8, 365)):
            raise ValueError("environment differs from the fixed S7-S2 placement contract")
        controller = PlacementController(job["arm"], env, model_env)
        observer = PlacementObserver(raw)
        row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                    observer=observer)
        if len(observer.user_xy) != row["actual_length"] + 1:
            raise ValueError("exogenous trajectory is incomplete")
        records = controller.decision_records
        _world_extra(row, steps, observer, records, raw, job["arm"])
        if not row["service_snapshot_calls"] == controller.snapshot_calls_started == controller.snapshot_calls_completed:
            raise ValueError("successful model invocation accounting differs from retained queries")
        row.update(observer.digests())
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **steps, **observer.as_arrays(),
                            metric_fields=np.asarray(TRACE_FIELDS),
                            planner_records_json=np.asarray(json.dumps(_plain(records), allow_nan=False,
                                                                       separators=(",", ":"))))
        return {**row, **job, "status": "completed", "raw_path": str(raw_path.relative_to(out)),
                "raw_sha256": _sha256(raw_path), "raw_bytes": raw_path.stat().st_size,
                "worker_wall_seconds": time.monotonic() - started,
                "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                "worker_peak_rss_kib": _rss_kib()}
    except BaseException as error:
        partial = {}
        if observer is not None and observer.physical_xyz and not raw_path.exists():
            try:
                partial_path = raw_path.with_name(raw_path.stem + "_partial.npz")
                np.savez_compressed(partial_path, **observer.as_arrays(),
                                    planner_records_json=np.asarray(json.dumps(_plain(
                                        controller.decision_records if controller else []))))
                partial = {"partial_path": str(partial_path.relative_to(out)),
                           "partial_sha256": _sha256(partial_path),
                           "partial_bytes": partial_path.stat().st_size,
                           "partial_observed_steps": max(0, len(observer.user_xy) - 1)}
            except BaseException as preserve_error:
                partial = {"partial_preservation_error": repr(preserve_error)}
        elif raw_path.exists():
            partial = {"incomplete_raw_path": str(raw_path.relative_to(out)),
                       "incomplete_raw_sha256": _sha256(raw_path),
                       "incomplete_raw_bytes": raw_path.stat().st_size}
        return {**job, **partial, "status": "failed", "error_type": type(error).__name__,
                "error": str(error), "traceback": traceback.format_exc(),
                "service_snapshot_calls": controller.snapshot_calls_started if controller else 0,
                "service_snapshot_calls_completed": controller.snapshot_calls_completed if controller else 0,
                "query_cost_scope": "exact started invocations in this caught worker; a raised invocation may be partial",
                "worker_wall_seconds": time.monotonic() - started,
                "worker_cpu_seconds": _cpu_seconds() - cpu_started, "worker_peak_rss_kib": _rss_kib()}
    finally:
        for instance in (env, model_env):
            if instance is not None:
                instance.close()


def _worker(payload):
    job, out, threads = payload
    if job not in plan():
        return {**job, "status": "failed", "error": "job outside frozen placement plan"}
    return _simulate_world(job, Path(out), threads)


def run(out, launch_sha, workers=2, threads=1):
    if workers != 2 or threads != 1:
        raise ValueError("B01 requires two workers with one numeric thread each")
    jobs = plan()
    out = Path(out)
    if any((out / name).exists() for name in ("config.json", "perworld.json", "summary.json", "raw")):
        raise FileExistsError(f"scientific outputs already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    config = make_eval_config(HORIZON, policy_seed=0)
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B01", "launch_sha": launch_sha,
        "horizon": HORIZON, "world_seeds": SEEDS, "jobs": jobs,
        "workers": workers, "threads_per_worker": threads, "fits": 0, "optimizer_updates": 0,
        "clock_steps": 30, "arms": {
            "H": "original H1 central kmeans6+relay2 and Hungarian hysteresis",
            "G": "eight deterministic kmeans starts, minimum SSE, otherwise H1",
            "R": "native static QoS, four layouts plus two 6-direction per-member sweeps"},
        "search": {"xy_steps_m": [500, 125], "z_steps_m": [50, 25],
                   "qos_tolerance": 1e-10, "travel_tolerance_m": 1e-6,
                   "max_queries_R_per_clock": 100, "max_radio_queries_batch": 81600},
        "information": "current central user/BS xy at clock30, current legal UAV geometry/energy",
        "model": "separate fixed-config seed0 native model; current-user/current-battery fresh association",
        "limitations": "static targets omit transit, future users, association history and energy dynamics",
        "shield": {"enter_margin": 0.0, "exit_margin": 0.05},
        "effective_native": _effective_s2(config, SEEDS[0]),
        "pairing": "initial state, complete user trajectory and native RNG stream digests",
    })
    rows, submitted, pool_errors, runner_error = [], [], [], None
    expected_keys = [job["job_key"] for job in jobs]

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, SEEDS, expected_keys))

    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], SEEDS, expected_keys))
    try:
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(executor, jobs, workers,
                lambda job: (job, str(out), threads), on_result, submitted, worker_fn=_worker)
    except BaseException as error:
        runner_error = {"error": str(error), "traceback": traceback.format_exc()}
    summary = summarize(rows, SEEDS, expected_keys)
    orphan = orphan_raw_files(out, rows)
    completed = sum(row.get("actual_length", 0) for row in rows if row["status"] == "completed")
    partial = sum(row.get("partial_observed_steps", 0) for row in rows)
    summary.update(launch_sha=launch_sha, fits=0, optimizer_updates=0, submitted_jobs=submitted,
                   unstarted_jobs=[key for key in expected_keys if key not in submitted],
                   completed_native_steps=completed, partial_observed_steps=partial,
                   known_step_lower_bound=completed + partial, orphan_raw=orphan,
                   runner_error=runner_error, pool_errors=pool_errors,
                   parent_wall_seconds=time.monotonic() - started,
                   parent_cpu_seconds=_cpu_seconds() - cpu_started, parent_peak_rss_kib=_rss_kib(),
                   worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
                   worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows),
                   worker_peak_rss_kib_max=max((row.get("worker_peak_rss_kib", 0) for row in rows), default=0),
                   service_snapshot_calls=sum(row.get("service_snapshot_calls", 0) for row in rows))
    if orphan or runner_error or pool_errors or summary["service_snapshot_calls"] > 81600:
        summary["status"] = "incomplete"
    summary["query_cost_scope"] = ("exact completed model invocations" if summary["status"] == "complete"
        else "known invocation lower bound across reported workers; abrupt worker loss may leave unmeasured queries")
    _write_json(out / "summary.json", summary)
    manifest = {"launch_sha": launch_sha,
                "artifacts": {name: {"sha256": _sha256(out / name), "bytes": (out / name).stat().st_size}
                              for name in ("config.json", "perworld.json", "summary.json")},
                "raw": {row["job_key"]: {"path": row["raw_path"], "sha256": row["raw_sha256"],
                                          "bytes": row["raw_bytes"]} for row in rows if row.get("raw_path")},
                "partial": {row["job_key"]: {"path": row["partial_path"], "sha256": row["partial_sha256"],
                                              "bytes": row["partial_bytes"]} for row in rows if row.get("partial_path")},
                "incomplete_raw": {row["job_key"]: {"path": row["incomplete_raw_path"],
                    "sha256": row["incomplete_raw_sha256"], "bytes": row["incomplete_raw_bytes"]}
                    for row in rows if row.get("incomplete_raw_path")}, "orphan_raw": orphan}
    _write_json(out / "manifest.json", manifest)
    return summary
