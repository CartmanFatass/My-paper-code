"""Fixed S7-S2/H3000 paired comparison of five/ten-step and one-step scoring."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import resource
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    make_eval_config,
    evaluate_world,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds,
    _rss_kib,
    _sha256,
    _write_json,
    execute_bounded,
    orphan_raw_files,
)
from experiments.candidates.energy_relay_availability.b05.readout import (
    summarize,
)
from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    H1_CENTRAL_10,
    TransitHoldController,
    battery_tail_readings,
)

from experiments.candidates.energy_relay_availability.b05.one_step import OneStepHoldController


DIRECTION = "energy_relay_availability"
BATCH = "B05"
HORIZON = 3000
SEEDS = tuple(range(28092801, 28092833))
SEALED = set(range(957001, 957033))
ARMS = ("five_ten", "one_step")
_CONFIG = None


def plan() -> list[dict]:
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for arm in ARMS for seed in SEEDS]


def validate_plan(jobs: list[dict]) -> None:
    expected = plan()
    if set(SEEDS) & SEALED:
        raise ValueError("B05 seed list overlaps sealed worlds")
    if jobs != expected or len(jobs) != 64:
        raise ValueError("B05 requires the fixed 64-job paired S7-S2 panel")


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return {"dtype": value.dtype.str, "shape": list(value.shape),
                "values": value.tolist()}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(),
                                                                  key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"unsupported RNG state value {type(value).__name__}")


def _rng_state_bytes(raw) -> bytes:
    rng = getattr(raw, "np_random", None)
    if rng is None or not hasattr(rng, "get_state"):
        raise TypeError("S2 environment must expose its RandomState stream")
    return json.dumps(_jsonable(rng.get_state()), sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _update_array_digest(digest, name: str, values: np.ndarray) -> None:
    array = np.ascontiguousarray(values)
    digest.update(name.encode("utf-8"))
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(np.asarray(array.shape, dtype="<i8").tobytes())
    digest.update(array.tobytes())


class PairingObserver:
    """Verify that the planner's isolated scoring leaves exogenous S2 paths unchanged."""

    def __init__(self, raw):
        self.raw = raw
        self.user_xy = []
        self._rng_digest = None
        self._user_digest = None
        self._initial_state_sha256 = None

    def attach(self, controller):
        from contextlib import contextmanager

        @contextmanager
        def attached():
            self._rng_digest = hashlib.sha256()
            self._user_digest = hashlib.sha256()
            rng_state = _rng_state_bytes(self.raw)
            self._rng_digest.update(len(rng_state).to_bytes(8, "little"))
            self._rng_digest.update(rng_state)
            first_users = np.asarray(self.raw.user_positions, dtype=np.float64)[:, :2].copy()
            self.user_xy.append(first_users)
            _update_array_digest(self._user_digest, "t0_user_xy_m", first_users)
            initial = hashlib.sha256()
            for name in ("user_positions", "uav_positions", "charging_station_positions",
                         "uav_battery_ratios"):
                _update_array_digest(initial, name, np.asarray(getattr(self.raw, name)))
            initial.update(rng_state)
            self._initial_state_sha256 = initial.hexdigest()
            yield

        return attached()

    def on_step(self, *, t, **kwargs):
        user_xy = np.asarray(self.raw.user_positions, dtype=np.float64)[:, :2].copy()
        self.user_xy.append(user_xy)
        _update_array_digest(self._user_digest, f"t{int(t) + 1}_user_xy_m", user_xy)
        rng_state = _rng_state_bytes(self.raw)
        self._rng_digest.update(len(rng_state).to_bytes(8, "little"))
        self._rng_digest.update(rng_state)

    def as_arrays(self) -> dict[str, np.ndarray]:
        return {"user_xy_m": np.asarray(self.user_xy, dtype=np.float64)}

    def digests(self) -> dict[str, str]:
        return {
            "initial_state_sha256": self._initial_state_sha256,
            "user_xy_trace_sha256": self._user_digest.hexdigest(),
            "rng_state_stream_sha256": self._rng_digest.hexdigest(),
        }


def _config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = make_eval_config(HORIZON, policy_seed=0)
    return _CONFIG


def _decision_arrays(controller) -> dict[str, np.ndarray]:
    records = (controller.heuristic.decision_records
               if isinstance(controller, TransitHoldController) else [])
    count = len(records)
    holds = np.full((count, 9), -99, dtype=np.int16)
    scores = np.full((count, 9), np.nan, dtype=np.float64)
    point_qos = {step: np.full((count, 9), np.nan, dtype=np.float64)
                 for step in (0, 1, 5, 10)}
    selected_gain = np.full(count, np.nan, dtype=np.float64)
    for row_idx, record in enumerate(records):
        for candidate_idx, item in enumerate(record["candidate_scores"][:9]):
            holds[row_idx, candidate_idx] = int(item["hold_uav"])
            scores[row_idx, candidate_idx] = float(item["integrated_qos"])
            for step, values in point_qos.items():
                if f"qos_{step}" in item:
                    values[row_idx, candidate_idx] = float(item[f"qos_{step}"])
            if int(item["hold_uav"]) == int(record["selected_hold_uav"]):
                selected_gain[row_idx] = (float(item["integrated_qos"])
                                         - float(record["candidate_scores"][0]["integrated_qos"]))
    return {
        "planner_step": np.asarray([r["step"] for r in records], dtype=np.int32),
        "planner_h1_targets_xy": np.asarray(
            [r["h1_targets_xy"] for r in records], dtype=np.float64),
        "planner_selected_hold_uav": np.asarray(
            [r["selected_hold_uav"] for r in records], dtype=np.int16),
        "planner_candidate_count": np.asarray([r["candidate_count"] for r in records], dtype=np.int8),
        "planner_snapshot_calls": np.asarray([r["snapshot_calls"] for r in records], dtype=np.int16),
        "planner_fallback": np.asarray([r["fallback"] or "" for r in records], dtype="U40"),
        "planner_candidate_hold_uav": holds,
        "planner_candidate_integrated_qos": scores,
        **{f"planner_candidate_qos_{step}": values for step, values in point_qos.items()},
        "planner_selected_proxy_gain": selected_gain,
    }


def _simulate_world(job: dict, out: Path, threads: int) -> dict:
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    env = observer = controller = None
    raw_path = out / "raw" / (job["job_key"].replace("/", "_") + ".npz")
    try:
        import torch

        torch.set_num_threads(int(threads))
        config = _config()
        env = make_env(config, int(job["seed"]))
        raw = env.env
        if (raw.energy_stage != "S2" or raw.routing_protocol != "widest_path"
                or bool(raw.failure_enabled) or env.observation_space.shape != (8, 365)):
            raise ValueError("effective environment differs from the fixed S7-S2 contract")
        if job["arm"] == "five_ten":
            controller = TransitHoldController(env)
        elif job["arm"] == "one_step":
            controller = OneStepHoldController(env)
        else:
            raise ValueError(f"unknown B05 arm {job['arm']}")
        observer = PairingObserver(raw)
        row, steps = evaluate_world(controller, env, config, int(job["seed"]),
                                    PRODUCTION_PARAMS, observer=observer)
        if (len(observer.user_xy) != row["actual_length"] + 1
                or len(steps["metrics"]) != row["actual_length"]):
            raise ValueError("S2 trace and native episode lengths disagree")
        decisions = _decision_arrays(controller)
        if isinstance(controller, TransitHoldController):
            records = controller.heuristic.decision_records
            expected_steps = list(range(0, int(row["actual_length"]),
                                        H1_CENTRAL_10.replan_period))
            actual_steps = [int(record["step"]) for record in records]
            if actual_steps != expected_steps:
                raise ValueError("transit selector changed the exact H_central@10 decision clock")
            if any(record["candidate_count"] > 9 for record in records):
                raise ValueError("transit selector exceeded its nine-plan neighborhood")
            for record in records:
                expected_calls = (1 + 2 * record["candidate_count"]
                                  if job["arm"] == "five_ten" else record["candidate_count"])
                if record["fallback"] is not None:
                    expected_calls = 0
                if record["snapshot_calls"] != expected_calls:
                    raise ValueError("scoring calls differ from the fixed arm contract")
            row["selected_hold_windows"] = sum(
                record["selected_hold_uav"] >= 0 for record in records)
            gains = decisions["planner_selected_proxy_gain"]
            selected = decisions["planner_selected_hold_uav"] >= 0
            row["selected_hold_near_tie_windows"] = int(
                np.count_nonzero(selected & (gains > 0.0) & (gains <= 1e-12)))
            row["planner_windows"] = len(records)
            row["planner_active_windows"] = sum(
                record["fallback"] is None for record in records)
            row["service_snapshot_calls"] = controller.heuristic.service_snapshot_calls
            row["candidate_plan_evaluations"] = sum(
                record["candidate_count"] for record in records
                if record["fallback"] is None)
            row["hold_selection_by_uav"] = {
                str(uav): sum(record["selected_hold_uav"] == uav for record in records)
                for uav in range(8)}
        else:
            decisions = {}
            row.update(selected_hold_windows=0, planner_windows=0,
                       planner_active_windows=0, service_snapshot_calls=0,
                       candidate_plan_evaluations=0,
                       hold_selection_by_uav={str(uav): 0 for uav in range(8)})
        row.update(battery_tail_readings(
            steps["battery"],
            reserve_ratio=float(raw.return_reserve_ratio),
            service_cutoff_ratio=float(raw.service_cutoff_threshold),
        ))
        row.update(observer.digests())
        row.update(job)
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **steps, **observer.as_arrays(), **decisions,
                            metric_fields=np.asarray(TRACE_FIELDS))
        row.update(status="completed", raw_path=str(raw_path.relative_to(out)),
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
        elif observer is not None and observer.user_xy:
            partial_path = raw_path.with_name(raw_path.stem + "_partial.npz")
            try:
                np.savez_compressed(partial_path, **observer.as_arrays())
                partial = {"partial_path": str(partial_path.relative_to(out)),
                           "partial_sha256": _sha256(partial_path),
                           "partial_bytes": partial_path.stat().st_size,
                           "partial_observed_steps": len(observer.user_xy) - 1}
            except BaseException as preserve_error:
                partial = {"partial_preservation_error": repr(preserve_error)}
        return {**job, **partial, "status": "failed",
                "error_type": type(error).__name__, "error": str(error),
                "traceback": traceback.format_exc(),
                "worker_wall_seconds": time.monotonic() - started,
                "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                "worker_peak_rss_kib": _rss_kib()}
    finally:
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def _worker(payload: tuple[dict, str, int]) -> dict:
    job, out_string, threads = payload
    if job not in plan() or job["seed"] in SEALED:
        return {**job, "status": "failed", "error_type": "ValueError",
                "error": "world outside B05 fixed plan"}
    return _simulate_world(job, Path(out_string), threads)


def _effective_s2(config, seed: int) -> dict:
    env = make_env(config, int(seed))
    try:
        raw = env.env
        result = {key: getattr(raw, key) for key in
                  ("energy_stage", "n_uavs", "n_users", "n_ground_bs", "n_charging_stations",
                   "routing_protocol", "max_steps", "battery_capacity_wh", "failure_enabled",
                   "return_reserve_ratio", "service_cutoff_threshold",
                   "enable_soft_handover", "serving_set_size", "max_speed", "time_step")
                  if hasattr(raw, key)}
        result["adapter_shape"] = list(env.observation_space.shape)
        result["area_size_m"] = float(raw.area_size)
        return result
    finally:
        env.close()


def run(out: Path, launch_sha: str, workers: int = 4, threads: int = 1) -> dict:
    jobs = plan()
    validate_plan(jobs)
    if workers < 1 or threads != 1:
        raise ValueError("B05 requires positive workers and one numeric thread per worker")
    out = Path(out)
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B05 scientific artifacts already exist: {out}")
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], SEEDS, expected_keys))
    config = _config()
    effective = _effective_s2(config, SEEDS[0])
    _write_json(out / "config.json", {
        "direction": DIRECTION,
        "batch": BATCH,
        "design": "same H1 hold neighborhood ranked by five/ten-step versus one-step native service",
        "launch_sha": launch_sha,
        "horizon": HORIZON,
        "world_seeds": list(SEEDS),
        "jobs": jobs,
        "workers": int(workers),
        "threads_per_worker": int(threads),
        "fits": 0,
        "optimizer_updates": 0,
        "arms": {
            "five_ten": {
                "base": H1_CENTRAL_10.record(),
                "scorer": "unchanged B04 TransitHoldController",
                "prediction_steps": [0, 5, 10],
                "score": "(QoS_0 + 2*QoS_5 + QoS_10)/4",
                "snapshots_per_active_window": "1 + 2*candidate_count",
            },
            "one_step": {
                "base": H1_CENTRAL_10.record(),
                "scorer": "same native model at nominal one-step positions",
                "prediction_steps": [1],
                "score": "QoS_1",
                "snapshots_per_active_window": "candidate_count",
            },
        },
        "common_planner": {
            "alternatives": "all-move plus one hold per assigned currently available UAV",
            "hold_duration_steps": 10,
            "assignment_memory": "H1 target history retained separately from temporary hold targets",
            "tie_rule": "float64 strict greater-than; baseline-first and identical candidate order",
            "near_tie_diagnostic": "selected positive score gain <= 1e-12; no tolerance in selection",
        },
        "legal_information": (
            "central current user/BS xy at each 10-step replan plus legal own UAV positions, "
            "battery/availability and return-mode records"),
        "model_information": (
            "both arms use the same static S2 native radio, association, routing and scalar "
            "demand model; intrinsic scoring computation differs. "
            "No future user waypoints, future RNG or live association history is used."),
        "service_proxy": {
            "scores": {"five_ten": "(QoS_0 + 2*QoS_5 + QoS_10)/4", "one_step": "QoS_1"},
            "future_user_positions": "fixed at current legal central snapshot",
            "association": "fresh native association at each snapshot; live hidden serving history reset",
            "routing_and_delivery": "existing native widest_path/radio/end-to-end methods",
            "unavailable_uav": "position held in forecast; current legal battery availability used",
            "return_shield": "skip hold selection while a mode is active or a current entry is due; "
                             "production shield remains on every real action",
            "backhaul_guard": "unchanged native guard on every real action; future guard interventions "
                             "are not shadow-simulated",
            "rng": "projection runs on an isolated environment copy and does not advance episode RNG",
            "limits": "snapshot proxy; no future user/failure, charging or battery transition",
        },
        "declared_upper_bound": {
            "candidate_plans_per_window": 9,
            "windows_per_arm": 9600,
            "candidate_plans_per_arm": 86400,
            "five_ten_snapshots": 182400,
            "one_step_snapshots": 86400,
            "total_service_snapshots": 268800,
            "native_episodes": 64,
            "native_transitions": 192000,
        },
        "pairing": "same world seed; initial state, user-position path and environment RNG stream hashed",
        "shield": {"enter_margin": PRODUCTION_PARAMS.enter_margin,
                   "exit_margin": PRODUCTION_PARAMS.exit_margin},
        "observation_layout": S7S2_LAYOUT.record(),
        "effective_raw": effective,
        "config": {key: getattr(config, key) for key in
                   ("experiment_preset", "energy_stage", "num_envs", "episode_length",
                    "max_steps", "k", "lambda_return", "use_obsnorm", "use_statenorm")},
    })
    rows: list[dict] = []
    submitted: list[str] = []
    pool_errors: list[dict] = []
    runner_error = None

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows, SEEDS, expected_keys))

    try:
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs)),
                                 mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, min(workers, len(jobs)),
                lambda job: (job, str(out), threads), on_result, submitted,
                worker_fn=_worker,
            )
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows, SEEDS, expected_keys)
    summary["submitted_jobs"] = submitted
    summary["unstarted_jobs"] = [key for key in expected_keys if key not in submitted]
    orphan = orphan_raw_files(out, rows)
    summary["orphan_raw"] = orphan
    if orphan or runner_error or pool_errors:
        summary["status"] = "incomplete"
    completed = sum(int(row.get("actual_length", 0)) for row in rows
                    if row.get("status") == "completed")
    partial = sum(int(row.get("partial_observed_steps", 0)) for row in rows)
    summary.update(
        launch_sha=launch_sha,
        fits=0,
        optimizer_updates=0,
        completed_transitions=completed,
        partial_observed_transitions=partial,
        known_transition_lower_bound=completed + partial,
        actual_transitions=completed if summary["status"] == "complete" else None,
        parent_wall_seconds=time.monotonic() - started,
        parent_cpu_seconds=_cpu_seconds() - cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        worker_peak_rss_kib_max=max((row.get("worker_peak_rss_kib", 0) for row in rows),
                                    default=None),
        worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0.0) for row in rows),
        worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0.0) for row in rows),
    )
    if pool_errors:
        summary["pool_errors"] = pool_errors
    if runner_error is not None:
        summary["runner_error"] = runner_error
        summary["status"] = "incomplete"
        summary["actual_transitions"] = None
    _write_json(out / "summary.json", summary)
    manifest = {
        "launch_sha": launch_sha,
        "artifacts": {name: {"sha256": _sha256(out / name),
                             "bytes": (out / name).stat().st_size}
                      for name in ("config.json", "perworld.json", "summary.json")},
        "raw": {row["job_key"]: {"path": row["raw_path"], "sha256": row["raw_sha256"],
                                "bytes": row["raw_bytes"]} for row in rows
                if row.get("raw_path") and row.get("raw_sha256")},
        "partial": {row["job_key"]: {"path": row["partial_path"],
                                    "sha256": row["partial_sha256"],
                                    "bytes": row["partial_bytes"]} for row in rows
                    if row.get("partial_path")},
        "incomplete_raw": {row["job_key"]: {"path": row["incomplete_raw_path"],
                                           "sha256": row["incomplete_raw_sha256"],
                                           "bytes": row["incomplete_raw_bytes"]} for row in rows
                           if row.get("incomplete_raw_path")},
        "orphan_raw": orphan,
    }
    manifest["storage_bytes"] = sum(item["bytes"] for item in manifest["artifacts"].values()) + sum(
        item["bytes"] for item in (*manifest["raw"].values(), *manifest["partial"].values(),
                                   *manifest["incomplete_raw"].values(), *orphan))
    _write_json(out / "manifest.json", manifest)
    if runner_error is not None:
        raise RuntimeError("B05 worker pool failed; partial evidence was preserved")
    return summary
