"""Immutable paired S4 energy-allocation batch and one-copy native traces."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import resource
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from .b03_energy_cost import B03Controller, B03_ARMS, S4_ENERGY_MODEL
from .b03_readout import summarize
from .configuration import HORIZON, make_config, make_env
from .events import FaultObserver
from .runner import (_cpu_seconds, _rss_kib, _sha256, _write_json,
                     execute_bounded, orphan_raw_files)


SEEDS = tuple(range(970001, 970033))
SEALED = set(range(957001, 957033))
INITIAL_FAULT_SEEDS = set(range(965001, 965033)) | set(range(966001, 966033))
PREVIOUS_B02_SEEDS = set(range(969001, 969033))
ALL_ARMS = B03_ARMS


def plan() -> list[dict]:
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for arm in ALL_ARMS for seed in SEEDS]


def validate_plan(jobs: list[dict]) -> None:
    if set(SEEDS) & (SEALED | INITIAL_FAULT_SEEDS | PREVIOUS_B02_SEEDS):
        raise ValueError("B03 seed list overlaps sealed or previously used direction worlds")
    expected = plan()
    if jobs != expected or len(jobs) != 64:
        raise ValueError("B03 requires the immutable 64-job paired plan")


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
    if rng is None:
        raise AttributeError("S4 environment exposes no np_random stream")
    if hasattr(rng, "bit_generator"):
        state = rng.bit_generator.state
    elif hasattr(rng, "get_state"):
        state = rng.get_state()
    else:
        raise TypeError("unsupported S4 environment RNG interface")
    return json.dumps(_jsonable(state), sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _update_array_digest(digest, name: str, values: np.ndarray) -> None:
    array = np.ascontiguousarray(values)
    digest.update(name.encode("utf-8"))
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(np.asarray(array.shape, dtype="<i8").tobytes())
    digest.update(array.tobytes())


class B03Observer(FaultObserver):
    """Read-only exogenous path/RNG fingerprints plus B02 native fault diagnostics."""

    def __init__(self, raw):
        super().__init__(raw)
        self.user_xy: list[np.ndarray] = []
        self.pre_battery: list[np.ndarray] = []
        self.post_battery: list[np.ndarray] = []
        self.pre_return_threshold: list[np.ndarray] = []
        self.post_return_threshold: list[np.ndarray] = []
        self.pre_return_margin: list[np.ndarray] = []
        self.post_return_margin: list[np.ndarray] = []
        self._rng_digest = None
        self._user_digest = None
        self._initial_state_sha256 = None
        self._initial_rng_state_sha256 = None
        self._failure_trace_sha256 = None

    def attach(self, controller):
        from contextlib import contextmanager

        @contextmanager
        def attached():
            self._rng_digest = hashlib.sha256()
            self._user_digest = hashlib.sha256()
            rng_state = _rng_state_bytes(self.raw)
            self._initial_rng_state_sha256 = hashlib.sha256(rng_state).hexdigest()
            self._rng_digest.update(len(rng_state).to_bytes(8, "little"))
            self._rng_digest.update(rng_state)
            initial = hashlib.sha256()
            for name in ("user_positions", "uav_positions", "charging_station_positions",
                         "uav_battery_ratios", "uav_failure_timers"):
                if not hasattr(self.raw, name):
                    raise AttributeError(f"S4 reset state lacks {name}")
                _update_array_digest(initial, name, np.asarray(getattr(self.raw, name)))
            initial.update(rng_state)
            self._initial_state_sha256 = initial.hexdigest()
            first_users = np.asarray(self.raw.user_positions, dtype=np.float64)[:, :2].copy()
            self.user_xy.append(first_users)
            _update_array_digest(self._user_digest, "t0_user_xy_m", first_users)
            try:
                with super(B03Observer, self).attach(controller):
                    yield
            finally:
                failure = hashlib.sha256()
                base = super(B03Observer, self).as_arrays()
                for key in ("pre_timer", "post_timer"):
                    _update_array_digest(failure, key, base[key])
                self._failure_trace_sha256 = failure.hexdigest()

        return attached()

    def on_step(self, *, t, observations_t, observations_t1, **kwargs):
        super().on_step(t=t, observations_t=observations_t,
                        observations_t1=observations_t1, **kwargs)
        pre = own_energy(observations_t)
        post = own_energy(observations_t1)
        self.pre_battery.append(pre["battery"].copy())
        self.post_battery.append(post["battery"].copy())
        self.pre_return_threshold.append(pre["return_threshold"].copy())
        self.post_return_threshold.append(post["return_threshold"].copy())
        self.pre_return_margin.append(pre["return_margin"].copy())
        self.post_return_margin.append(post["return_margin"].copy())
        user_xy = np.asarray(self.raw.user_positions, dtype=np.float64)[:, :2].copy()
        self.user_xy.append(user_xy)
        _update_array_digest(self._user_digest, f"t{int(t) + 1}_user_xy_m", user_xy)
        rng_state = _rng_state_bytes(self.raw)
        self._rng_digest.update(len(rng_state).to_bytes(8, "little"))
        self._rng_digest.update(rng_state)

    def as_arrays(self) -> dict[str, np.ndarray]:
        result = super().as_arrays()
        result.update({
            "user_xy_m": np.asarray(self.user_xy, dtype=np.float64),
            "pre_battery": np.asarray(self.pre_battery, dtype=np.float32),
            "post_battery": np.asarray(self.post_battery, dtype=np.float32),
            "pre_return_threshold": np.asarray(self.pre_return_threshold, dtype=np.float32),
            "post_return_threshold": np.asarray(self.post_return_threshold, dtype=np.float32),
            "pre_return_margin": np.asarray(self.pre_return_margin, dtype=np.float32),
            "post_return_margin": np.asarray(self.post_return_margin, dtype=np.float32),
        })
        return result

    def digests(self) -> dict[str, str]:
        if any(value is None for value in (self._rng_digest, self._user_digest,
                                           self._initial_state_sha256,
                                           self._initial_rng_state_sha256,
                                           self._failure_trace_sha256)):
            raise RuntimeError("B03 observer digests are unavailable before completed readout")
        return {
            "initial_state_sha256": self._initial_state_sha256,
            "initial_rng_state_sha256": self._initial_rng_state_sha256,
            "user_xy_trace_sha256": self._user_digest.hexdigest(),
            "rng_state_stream_sha256": self._rng_digest.hexdigest(),
            "failure_trace_sha256": self._failure_trace_sha256,
        }


def _check_energy_model(raw) -> dict:
    expected = {
        "p0_w": S4_ENERGY_MODEL.p0_w,
        "pi_w": S4_ENERGY_MODEL.pi_w,
        "u_tip_mps": S4_ENERGY_MODEL.u_tip_mps,
        "v0_mps": S4_ENERGY_MODEL.v0_mps,
        "k3": S4_ENERGY_MODEL.k3,
        "vertical_w_per_mps": S4_ENERGY_MODEL.vertical_w_per_mps,
        "battery_capacity_wh": S4_ENERGY_MODEL.battery_capacity_wh,
        "return_reserve_ratio": S4_ENERGY_MODEL.reserve_ratio,
        "limp_home_speed_mps": S4_ENERGY_MODEL.limp_home_speed_mps,
        "max_speed": S4_ENERGY_MODEL.horizontal_speed_mps,
        "max_vertical_speed_mps": S4_ENERGY_MODEL.vertical_speed_mps,
    }
    attrs = {"p0_w": "P0", "pi_w": "Pi", "u_tip_mps": "U_tip",
             "v0_mps": "v0", "k3": "k3", "vertical_w_per_mps": "P_z_coeff",
             "battery_capacity_wh": "battery_capacity_wh",
             "return_reserve_ratio": "return_reserve_ratio",
             "limp_home_speed_mps": "limp_home_speed_mps",
             "max_speed": "max_speed", "max_vertical_speed_mps": "max_vertical_speed_mps"}
    actual = {key: float(getattr(raw, attrs[key])) for key in expected}
    mismatch = {key: {"expected": value, "actual": actual[key]}
                for key, value in expected.items()
                if not np.isclose(value, actual[key], rtol=0.0, atol=1e-12)}
    if mismatch:
        raise ValueError(f"B03 S4 energy-model constants differ from native: {mismatch}")
    for horizontal, vertical in ((0.0, 0.0), (3.0, 0.0), (30.0, 0.0), (7.5, 2.5)):
        modeled = float(S4_ENERGY_MODEL.power_w(horizontal, vertical))
        native = float(raw._calculate_power_consumption(horizontal, vertical))
        if not np.isclose(modeled, native, rtol=0.0, atol=1e-12):
            raise ValueError("B03 power function does not match native S4")
    return actual


def _world_risk_readings(row: dict, steps: dict, observer_arrays: dict) -> dict:
    battery = np.asarray(observer_arrays["post_battery"], dtype=np.float64)
    threshold = np.asarray(observer_arrays["post_return_threshold"], dtype=np.float64)
    margins = np.asarray(steps["return_margin"], dtype=np.float64)
    post_margins = np.asarray(observer_arrays["post_return_margin"], dtype=np.float64)
    if battery.shape != (row["actual_length"], 8) or threshold.shape != battery.shape:
        raise ValueError("B03 legal energy-trace lengths differ from the native episode")
    denom = float(battery.size)
    return {
        "mean_return_margin_at_decision": float(margins.mean()),
        "minimum_return_margin_at_decision": float(margins.min()),
        "negative_return_margin_uav_step_fraction": float(np.mean(margins < 0.0)),
        "mean_return_margin_post_step": float(post_margins.mean()),
        "minimum_return_margin_post_step": float(post_margins.min()),
        "below_dynamic_return_threshold_uav_step_fraction": float(
            np.sum(battery <= threshold) / denom),
        "below_fixed_reserve_uav_step_fraction": float(
            np.mean(battery <= S4_ENERGY_MODEL.reserve_ratio)),
        "service_cutoff_uav_step_fraction": float(np.mean(battery <= 0.02)),
        "depleted_uav_step_fraction": float(np.mean(battery <= 0.0)),
        "failed_uav_step_fraction": float(
            np.sum(observer_arrays["post_failed"]) / denom),
        "failed_uav_step_count": int(np.sum(observer_arrays["post_failed"])),
        "team_steps_with_failure_fraction": float(
            np.mean(np.any(observer_arrays["post_failed"], axis=1))),
    }


def _serialize_assignment_records(controller: B03Controller) -> str:
    return json.dumps(controller.assignment_records, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _simulate_world(job: dict, out: Path, threads: int, horizon: int) -> dict:
    """Run one cell; exposed separately so tests can use nonpanel short worlds."""
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    env = observer = controller = None
    raw_path = out / "raw" / (job["job_key"].replace("/", "_") + ".npz")
    try:
        import torch

        torch.set_num_threads(int(threads))
        config = make_config(int(horizon))
        env = make_env(config, int(job["seed"]), True)
        raw = env.env
        native_energy_constants = _check_energy_model(raw)
        controller = B03Controller(job["arm"])
        observer = B03Observer(raw)
        row, steps = evaluate_world(controller, env, config, int(job["seed"]),
                                    PRODUCTION_PARAMS, observer=observer)
        fault = observer.as_arrays()
        decisions = controller.as_arrays()
        length = row["actual_length"]
        if (not decisions or any(len(value) != length for value in decisions.values())
                or any(len(value) != length for key, value in fault.items()
                       if key != "user_xy_m")
                or fault["user_xy_m"].shape != (length + 1, 30, 2)
                or len(steps["metrics"]) != length):
            raise ValueError("B03 decision/fault/exogenous/native trace length disagreement")
        if not np.array_equal(decisions["available"], fault["pre_available"]):
            raise ValueError("B03 controller availability differs from legal observation trace")
        regular = np.arange(length) % 30 == 0
        if (not np.array_equal(decisions["regular_replan"], regular)
                or not np.array_equal(decisions["executed_replan"], regular)
                or decisions["extra_replan"].any()
                or not np.array_equal(decisions["plan_call_count"], np.cumsum(regular))):
            raise ValueError("B03 changed the frozen 30-step replanning clock")
        if controller.b03_arm == "distance_hysteresis" and controller.assignment_records:
            raise ValueError("distance baseline unexpectedly logged energy assignment costs")
        if controller.b03_arm == "energy_fraction" and not controller.assignment_records:
            raise ValueError("energy assignment did not execute")
        if raw_path.exists():
            raise FileExistsError(raw_path)
        digests = observer.digests()
        risk = _world_risk_readings(row, steps, fault)
        assignment_json = _serialize_assignment_records(controller)
        row.update(job)
        row.update(status="completed", native_energy_constants=native_energy_constants,
                   **digests, **risk,
                   energy_plan_count=len(controller.assignment_records),
                   assigned_mission_count=sum(len(item["selected"])
                                              for item in controller.assignment_records),
                   predicted_negative_reserve_slack_count=sum(
                       item["predicted_reserve_slack_wh"] < 0.0
                       for plan_item in controller.assignment_records
                       for item in plan_item["selected"]),
                   raw_path=str(raw_path.relative_to(out)),
                   worker_wall_seconds=time.monotonic() - started,
                   worker_cpu_seconds=_cpu_seconds() - cpu_started,
                   worker_peak_rss_kib=_rss_kib())
        np.savez_compressed(
            raw_path, **steps,
            **{f"fault_{key}": value for key, value in fault.items()},
            **{f"decision_{key}": value for key, value in decisions.items()},
            assignment_records_json=np.asarray(assignment_json),
            metric_fields=np.asarray(TRACE_FIELDS),
            initial_state_sha256=np.asarray(digests["initial_state_sha256"]),
            initial_rng_state_sha256=np.asarray(digests["initial_rng_state_sha256"]),
            user_xy_trace_sha256=np.asarray(digests["user_xy_trace_sha256"]),
            failure_trace_sha256=np.asarray(digests["failure_trace_sha256"]),
            rng_state_stream_sha256=np.asarray(digests["rng_state_stream_sha256"]))
        row.update(raw_sha256=_sha256(raw_path), raw_bytes=raw_path.stat().st_size)
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
                data = observer.as_arrays()
                if controller is not None and controller.decision_rows:
                    data.update({f"decision_{key}": value
                                 for key, value in controller.as_arrays().items()})
                    data["assignment_records_json"] = np.asarray(
                        _serialize_assignment_records(controller))
                for key in ("initial_state_sha256", "initial_rng_state_sha256"):
                    value = getattr(observer, f"_{key}", None)
                    if value is not None:
                        data[key] = np.asarray(value)
                np.savez_compressed(path, **data)
                partial = {"partial_path": str(path.relative_to(out)),
                           "partial_sha256": _sha256(path),
                           "partial_bytes": path.stat().st_size,
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


def _worker(payload: tuple[dict, str, int]) -> dict:
    job, out_string, threads = payload
    if job not in plan() or job["seed"] in SEALED:
        return {**job, "status": "failed", "error_type": "ValueError",
                "error": "world outside B03 fixed plan"}
    return _simulate_world(job, Path(out_string), threads, HORIZON)


def _effective_s4(config, seed: int) -> dict:
    env = make_env(config, seed, True)
    try:
        raw = env.env
        values = {key: getattr(raw, key) for key in
                  ("energy_stage", "n_uavs", "n_users", "n_ground_bs",
                   "n_charging_stations", "user_movement_model", "user_max_speed",
                   "cluster_migration_speed", "max_steps", "battery_capacity_wh",
                   "failure_enabled", "uav_failure_probability", "uav_failure_min_active",
                   "return_reserve_ratio", "limp_home_speed_mps", "max_speed",
                   "max_vertical_speed_mps", "P0", "Pi", "U_tip", "v0", "k3",
                   "P_z_coeff")}
        for key in ("cluster_pause_time_range", "user_pause_time_range",
                    "uav_failure_duration_range"):
            values[key] = list(getattr(raw, key))
        values["charging_station_capacity"] = raw.charging_station_capacity[:2].tolist()
        values["adapter_shape"] = list(env.observation_space.shape)
        return values
    finally:
        env.close()


def run(out: Path, launch_sha: str, workers: int = 4, threads: int = 1) -> dict:
    jobs = plan()
    validate_plan(jobs)
    if workers < 1 or threads != 1:
        raise ValueError("B03 requires positive workers and one numeric thread per worker")
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"B03 scientific artifacts already exist: {out}")
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)  # Native launcher created its own records.
    (out / "raw").mkdir()
    expected_keys = [job["job_key"] for job in jobs]
    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], expected_keys, list(SEEDS)))
    config = make_config(HORIZON)
    effective = _effective_s4(config, SEEDS[0])
    _write_json(out / "config.json", {
        "direction": "energy_relay_availability", "batch": "B03",
        "launch_sha": launch_sha, "horizon": HORIZON, "jobs": jobs,
        "workers": workers, "threads": threads, "fits": 0, "optimizer_updates": 0,
        "arms": {"distance_hysteresis": variant("H1", information="local").record(),
                 "energy_fraction": {"base": variant("H1", information="local").record(),
                                     "assignment_cost": "(outbound_wh + 30s hover_wh + min legal-station return_wh) / max(battery_wh - 16Wh, 1e-6)",
                                     "hysteresis": {
                                         "equivalent_distance_m": 300.0,
                                         "energy_wh": float(
                                             10.0 * S4_ENERGY_MODEL.power_w(30.0, 0.0) / 3600.0),
                                         "cost_fraction": "energy_wh / max(usable_wh, 1e-6)",
                                         "applied_to": "nearest generated target matching previous target",
                                     },
                                     "target_height_m": 100.0}},
        "energy_model": asdict(S4_ENERGY_MODEL) | {"k3": S4_ENERGY_MODEL.k3},
        "legal_information": "pooled H_local observations; no raw environment inputs to controller",
        "pairing": "same seed per arm; initial, user, failure and RNG-state traces hashed and compared",
        "shield": asdict(PRODUCTION_PARAMS),
        "observation_layout": {"dim": 365, "n_uavs": 8, "stations": 2},
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
        _write_json(out / "summary.json", summarize(rows, expected_keys, list(SEEDS)))

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
    summary = summarize(rows, expected_keys, list(SEEDS))
    summary["submitted_jobs"] = submitted
    summary["unstarted_jobs"] = [key for key in expected_keys if key not in submitted]
    orphan = orphan_raw_files(out, rows)
    summary["orphan_raw"] = orphan
    if orphan or runner_error:
        summary["status"] = "incomplete"
    if pool_errors:
        summary["pool_errors"] = pool_errors
    completed_steps = sum(row["actual_length"] for row in rows
                          if row.get("status") == "completed")
    partial_steps = sum(row.get("partial_observed_steps", 0) for row in rows)
    summary.update(
        launch_sha=launch_sha, fits=0, optimizer_updates=0,
        completed_transitions=completed_steps,
        partial_observed_transitions=partial_steps,
        known_transition_lower_bound=completed_steps + partial_steps,
        actual_transitions=completed_steps if summary["status"] == "complete" else None,
        parent_wall_seconds=time.monotonic() - started,
        parent_cpu_seconds=_cpu_seconds() - cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in rows
                                     if "worker_peak_rss_kib" in row), default=None),
        worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
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
                if row.get("status") == "completed"},
        "partial": {row["job_key"]: {"path": row["partial_path"],
                                    "sha256": row["partial_sha256"],
                                    "bytes": row["partial_bytes"]} for row in rows
                    if "partial_path" in row},
        "incomplete_raw": {row["job_key"]: {"path": row["incomplete_raw_path"],
                                           "sha256": row["incomplete_raw_sha256"],
                                           "bytes": row["incomplete_raw_bytes"]} for row in rows
                           if "incomplete_raw_path" in row},
        "orphan_raw": orphan,
    }
    manifest["storage_bytes"] = sum(item["bytes"] for item in manifest["artifacts"].values()) \
        + sum(item["bytes"] for item in (*manifest["raw"].values(),
                                          *manifest["partial"].values(),
                                          *manifest["incomplete_raw"].values(), *orphan))
    _write_json(out / "manifest.json", manifest)
    if runner_error is not None:
        raise RuntimeError("B03 worker pool failed; incomplete evidence is preserved")
    return summary
