"""B07 native H3000 original/feedback evaluation with physical energy accounting."""

from __future__ import annotations

import copy
import json
import resource
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import (
    _json_default,
    _sync_agent,
    _terminal_kind,
    active_config,
    initialization_fingerprint,
    make_env,
    optimizer_steps,
    preserved_rng,
    seed_everything,
    sha256_file,
)
from ..b04.evaluation import TRACE_FIELDS, metric_row
from ..b06.feedback import PRODUCTION_LAYOUT, apply_feedback, decode_legal_observations
from ..b06.native import (
    PRODUCTION_BINDINGS,
    _normalizer_snapshot,
    _required_array,
    _same_snapshot,
    _verify_prefixes,
    verify_source,
)


OBJECT_ID = "UAV-SERVICE-AUXILIARY-B07-H3000-FEEDBACK"
TRAINING_HORIZON = 1500
EVALUATION_HORIZON = 3000
BATTERY_CAPACITY_WH = 160.0
PANELS = {
    "development": tuple(range(937001, 937009)),
    "final": tuple(range(938001, 938033)),
}
EXPECTED_CONFIG_DIFF_FIELDS = {
    "batch_size",
    "buffer_size",
    "episode_length",
    "high_level_buffer_size",
    "low_level_buffer_size",
    "max_steps",
    "num_envs",
}


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, default=_json_default, allow_nan=False) + "\n")


def _json_active(config) -> dict[str, Any]:
    return json.loads(json.dumps(active_config(config)), parse_constant=str)


def derive_evaluation_config(
    saved_training_config,
    *,
    training_horizon: int = TRAINING_HORIZON,
    evaluation_horizon: int = EVALUATION_HORIZON,
):
    """Make the one-lane H3000 evaluator without mutating saved H1500 identity."""

    if (
        int(saved_training_config.episode_length) != int(training_horizon)
        or int(saved_training_config.max_steps) != int(training_horizon)
    ):
        raise ValueError("saved source config does not have the fixed training horizon")
    if int(evaluation_horizon) <= int(training_horizon):
        raise ValueError("evaluation horizon must extend the fixed training horizon")
    saved_before = _json_active(saved_training_config)
    evaluation = copy.deepcopy(saved_training_config)
    evaluation.episode_length = int(evaluation_horizon)
    evaluation.max_steps = int(evaluation_horizon)
    evaluation.num_envs = 1
    evaluation.calculate_and_set_buffer_sizes()
    saved_after = _json_active(saved_training_config)
    if saved_before != saved_after:
        raise RuntimeError("deriving H3000 mutated the saved training config")
    evaluation_active = _json_active(evaluation)
    differences = {
        key: {"saved_training": saved_before.get(key), "evaluation": evaluation_active.get(key)}
        for key in sorted(set(saved_before) | set(evaluation_active))
        if saved_before.get(key) != evaluation_active.get(key)
    }
    if set(differences) != EXPECTED_CONFIG_DIFF_FIELDS:
        raise ValueError(f"unexpected H3000 evaluation config differences: {differences}")
    if (
        evaluation.episode_length != evaluation_horizon
        or evaluation.max_steps != evaluation_horizon
        or evaluation.num_envs != 1
        or evaluation.n_agents != 8
        or evaluation.obs_dim != 365
        or evaluation.action_dim != 4
        or evaluation.k != 10
        or evaluation.lambda_return != 2.0
        or evaluation.battery_capacity_wh != BATTERY_CAPACITY_WH
        or evaluation.use_obsnorm
        or evaluation.use_statenorm
    ):
        raise ValueError("derived evaluator violates the fixed B07 native contract")
    return evaluation, {
        "saved_training_horizon": int(training_horizon),
        "evaluation_horizon": int(evaluation_horizon),
        "saved_training_active": saved_before,
        "evaluation_active": evaluation_active,
        "differences": differences,
        "storage_note": "derived evaluator buffers exist but receive no transition insertion or update",
    }


def verify_training_source(
    root: Path, binding, *, expected_spec=None, training_horizon: int = TRAINING_HORIZON
):
    checked = verify_source(root, binding, expected_spec=expected_spec)
    config = checked["config"]
    if (
        int(config.episode_length) != int(training_horizon)
        or int(config.max_steps) != int(training_horizon)
    ):
        raise ValueError(f"{binding.block} source is not the fixed training-horizon identity")
    if checked["spec"].episode_length != int(training_horizon):
        raise ValueError(f"{binding.block} source specification horizon changed")
    return checked


def energy_ledger(raw_env, pre_battery: np.ndarray, pre_charging: np.ndarray) -> dict[str, np.ndarray]:
    """Read and verify the native postdecision physical energy ledger."""

    n_agents = int(raw_env.n_uavs)
    pre = np.asarray(pre_battery, dtype=np.float64)
    post = np.asarray(raw_env.uav_battery_ratios, dtype=np.float64).copy()
    consumed = np.asarray(raw_env.last_energy_consumed_wh, dtype=np.float64).copy()
    charger_input = np.asarray(raw_env.last_energy_charged_wh, dtype=np.float64).copy()
    native_net = np.asarray(raw_env.last_net_energy_charged_wh, dtype=np.float64).copy()
    before_charging = np.asarray(pre_charging, dtype=bool)
    charging = np.asarray(raw_env.uav_charging, dtype=bool).copy()
    for name, value in {
        "pre_battery": pre,
        "post_battery": post,
        "consumed_wh": consumed,
        "charger_input_wh": charger_input,
        "native_net_charge_wh": native_net,
    }.items():
        if value.shape != (n_agents,) or not np.isfinite(value).all():
            raise ValueError(f"invalid native energy ledger field {name}")
    capacity = float(raw_env.battery_capacity_wh)
    if not np.isfinite(capacity) or capacity != BATTERY_CAPACITY_WH:
        raise ValueError("native physical battery capacity is not the fixed 160 Wh")
    signed_stored = (post - pre) * capacity
    unclipped = charger_input - consumed
    expected_post_unclipped = pre + unclipped / capacity
    expected_post = np.clip(expected_post_unclipped, 0.0, 1.0)
    if not np.allclose(post, expected_post, rtol=0.0, atol=2e-12):
        raise RuntimeError("native pre/consume/input/clip energy accounting does not close")
    expected_native_net = np.maximum(0.0, unclipped)
    if not np.allclose(native_net, expected_native_net, rtol=0.0, atol=2e-12):
        raise RuntimeError("native clipped-positive net-charge field changed semantics")
    residual = signed_stored - unclipped
    upper_clipped = expected_post_unclipped > 1.0
    lower_clipped = expected_post_unclipped < 0.0
    eligible = np.asarray(raw_env.last_charging_eligible, dtype=bool).copy()
    arrival = np.asarray(raw_env.last_charging_arrival, dtype=bool).copy()
    wait_age = np.asarray(raw_env.charging_wait_steps, dtype=np.int64).copy()
    station_distance_before = np.asarray(
        raw_env.last_min_station_distance_before, dtype=np.float64
    ).copy()
    station_distance_after = np.asarray(
        raw_env.last_min_station_distance_after, dtype=np.float64
    ).copy()
    for name, value in {
        "eligible": eligible,
        "arrival": arrival,
        "wait_age": wait_age,
        "native_station_distance_before_m": station_distance_before,
        "native_station_distance_after_m": station_distance_after,
    }.items():
        if value.shape != (n_agents,):
            raise ValueError(f"invalid native charging event field {name}")
    return {
        "physical_pre_battery": pre,
        "physical_post_battery": post,
        "battery_capacity_wh": np.full(n_agents, capacity, dtype=np.float64),
        "consumed_wh": consumed,
        "charger_input_wh": charger_input,
        "native_clipped_positive_net_charge_wh": native_net,
        "signed_stored_energy_delta_wh": signed_stored,
        "unclipped_stored_energy_delta_wh": unclipped,
        "capacity_clipping_residual_wh": residual,
        "upper_capacity_clipped": upper_clipped,
        "lower_capacity_clipped": lower_clipped,
        "charging_eligible": eligible,
        "charging_capture": eligible,
        "charging_arrival": arrival,
        "charging_admitted": charging,
        "charging_wait_age": wait_age,
        "native_station_distance_before_m": station_distance_before,
        "native_station_distance_after_m": station_distance_after,
        "charge_started": charging & ~before_charging,
        "charge_ended": ~charging & before_charging,
        "uav_charging": charging,
    }


def _service_free_intervals(values: np.ndarray) -> list[dict[str, Any]]:
    free = np.asarray(values) <= 0.0
    padded = np.concatenate(([False], free, [False])).astype(np.int8)
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    stops = np.flatnonzero(changes == -1)
    return [
        {
            "start": int(start),
            "stop": int(stop),
            "actual_steps": int(stop - start),
            "left_censored": bool(start == 0),
            "right_censored": bool(stop == len(free)),
        }
        for start, stop in zip(starts, stops, strict=True)
    ]


def _window_summary(rewards, metrics, diagnostics, start: int, stop: int):
    actual_stop = min(int(stop), len(rewards))
    if start >= actual_stop:
        return {"start": start, "stop": start, "actual_steps": 0,
                "raw_native_J": None, "qos_sum": None, "throughput_mbps_sum": None,
                "return_cost_sum": None, "minimum_battery_ratio": None}
    segment = slice(start, actual_stop)
    return {
        "start": start,
        "stop": actual_stop,
        "actual_steps": actual_stop - start,
        "raw_native_J": float(rewards[segment].sum()),
        "qos_sum": float(metrics[segment, TRACE_FIELDS.index("qos_satisfaction_ratio")].sum()),
        "throughput_mbps_sum": float(
            metrics[segment, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")].sum()
        ),
        "return_cost_sum": float(
            metrics[segment, TRACE_FIELDS.index("return_constraint_cost")].sum()
        ),
        "minimum_battery_ratio": float(diagnostics["physical_post_battery"][segment].min()),
    }


def episode_summary(seed: int, rewards: np.ndarray, metrics: np.ndarray,
                    ends: np.ndarray, diagnostics: dict[str, np.ndarray],
                    *, planned_horizon: int = EVALUATION_HORIZON):
    length = int(len(rewards))
    qos = metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
    throughput = metrics[:, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")]
    intervals = _service_free_intervals(qos)
    initial_battery = diagnostics["episode_initial_physical_battery"]
    battery_values = np.concatenate((initial_battery, diagnostics["physical_post_battery"].reshape(-1)))
    margin_values = np.concatenate((
        diagnostics["pre_legal_margin"][0],
        diagnostics["physical_post_return_margin"].reshape(-1),
    ))
    mode_durations = []
    for agent_index in range(diagnostics["mode"].shape[1]):
        values = diagnostics["mode"][:, agent_index]
        padded = np.concatenate(([False], values, [False])).astype(np.int8)
        changes = np.diff(padded)
        starts = np.flatnonzero(changes == 1)
        stops = np.flatnonzero(changes == -1)
        mode_durations.append((stops - starts).astype(int).tolist())
    entry_steps = np.flatnonzero(diagnostics["entry"].any(axis=1))
    override_steps = np.flatnonzero(diagnostics["command_changed"].any(axis=1))
    realized_motion = np.linalg.norm(diagnostics["actual_displacement_m"], axis=2) > 1e-7
    blocked_override = diagnostics["command_changed"] & ~realized_motion
    row: dict[str, Any] = {
        "seed": int(seed),
        "actual_length": length,
        "terminal_type": _terminal_kind(bool(ends[-1, 0]), bool(ends[-1, 1])),
        "raw_native_J": float(rewards.sum()),
        "native_J_per_actual_step": float(rewards.mean()),
        "cumulative_qos": float(qos.sum()),
        "qos_per_actual_step": float(qos.mean()),
        "planned_window_qos": float(qos.sum() / planned_horizon),
        "cumulative_throughput_mbps": float(throughput.sum()),
        "throughput_mbps_per_actual_step": float(throughput.mean()),
        "planned_window_throughput_mbps": float(throughput.sum() / planned_horizon),
        "qos_p10": float(np.quantile(qos, 0.1)),
        "throughput_mbps_p10": float(np.quantile(throughput, 0.1)),
        "zero_service_episode": bool(np.all(qos == 0.0)),
        "service_free_intervals": intervals,
        "service_free_interval_count": len(intervals),
        "maximum_service_free_interval_steps": max(
            (item["actual_steps"] for item in intervals), default=0
        ),
        "right_censored_service_free_interval": bool(
            intervals and intervals[-1]["right_censored"]
        ),
        "episode_minimum_battery_ratio": float(battery_values.min()),
        "episode_minimum_return_margin": float(margin_values.min()),
        "members_with_charger_input": int(
            np.any(diagnostics["charger_input_wh"] > 0.0, axis=0).sum()
        ),
        "members_with_positive_stored_delta": int(
            np.any(diagnostics["signed_stored_energy_delta_wh"] > 0.0, axis=0).sum()
        ),
        "charging_eligible_uav_steps": int(diagnostics["charging_eligible"].sum()),
        "charging_capture_uav_steps": int(diagnostics["charging_capture"].sum()),
        "charging_admitted_uav_steps": int(diagnostics["charging_admitted"].sum()),
        "charging_arrival_count": int(diagnostics["charging_arrival"].sum()),
        "charge_start_count": int(diagnostics["charge_started"].sum()),
        "charge_end_count": int(diagnostics["charge_ended"].sum()),
        "total_consumed_wh": float(diagnostics["consumed_wh"].sum()),
        "total_charger_input_wh": float(diagnostics["charger_input_wh"].sum()),
        "total_native_clipped_positive_net_charge_wh": float(
            diagnostics["native_clipped_positive_net_charge_wh"].sum()
        ),
        "total_signed_stored_energy_delta_wh": float(
            diagnostics["signed_stored_energy_delta_wh"].sum()
        ),
        "total_capacity_clipping_residual_wh": float(
            diagnostics["capacity_clipping_residual_wh"].sum()
        ),
        "upper_capacity_clipping_events": int(diagnostics["upper_capacity_clipped"].sum()),
        "lower_capacity_clipping_events": int(diagnostics["lower_capacity_clipped"].sum()),
        "feedback_mode_uav_steps": int(diagnostics["mode"].sum()),
        "feedback_entry_count": int(diagnostics["entry"].sum()),
        "feedback_exit_count": int(diagnostics["exit"].sum()),
        "command_override_uav_steps": int(diagnostics["command_changed"].sum()),
        "realized_motion_uav_steps": int(realized_motion.sum()),
        "blocked_override_uav_steps": int(blocked_override.sum()),
        "negative_return_margin_uav_steps": int(
            (diagnostics["physical_post_return_margin"] < 0.0).sum()
        ),
        "maximum_simultaneous_modes": int(diagnostics["mode"].sum(axis=1).max(initial=0)),
        "first_mode_entry_step": int(entry_steps[0]) if entry_steps.size else None,
        "first_command_override_step": int(override_steps[0]) if override_steps.size else None,
        "mode_durations_by_uav": mode_durations,
        "first_half": _window_summary(rewards, metrics, diagnostics, 0, 1500),
        "second_half": _window_summary(rewards, metrics, diagnostics, 1500, 3000),
        "descriptive_250_step_bins": [
            _window_summary(rewards, metrics, diagnostics, start, start + 250)
            for start in range(0, planned_horizon, 250)
        ],
    }
    for column, field in enumerate(TRACE_FIELDS):
        row[f"{field}_sum"] = float(metrics[:, column].sum())
        row[f"{field}_per_actual_step"] = float(metrics[:, column].mean())
    return row


def aggregate_worlds(worlds: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "raw_native_J", "native_J_per_actual_step", "actual_length",
        "cumulative_qos", "qos_per_actual_step", "planned_window_qos",
        "cumulative_throughput_mbps", "throughput_mbps_per_actual_step",
        "planned_window_throughput_mbps", "qos_p10", "throughput_mbps_p10",
        "episode_minimum_battery_ratio", "total_consumed_wh", "total_charger_input_wh",
        "total_native_clipped_positive_net_charge_wh", "total_signed_stored_energy_delta_wh",
        "total_capacity_clipping_residual_wh",
        "episode_minimum_return_margin",
    )
    result = {
        f"mean_{field}": float(np.mean([world[field] for world in worlds]))
        for field in fields
    }
    result.update(
        actual_episode_attempts=len(worlds),
        actual_transitions=sum(world["actual_length"] for world in worlds),
        terminated_episodes=sum(world["terminal_type"] == "terminated" for world in worlds),
        truncated_episodes=sum(world["terminal_type"] == "truncated" for world in worlds),
        zero_service_episodes=sum(world["zero_service_episode"] for world in worlds),
        minimum_episode_battery_ratio=min(world["episode_minimum_battery_ratio"] for world in worlds),
        p10_episode_minimum_battery_ratio=float(np.quantile(
            [world["episode_minimum_battery_ratio"] for world in worlds], 0.1
        )),
        maximum_service_free_interval_steps=max(
            world["maximum_service_free_interval_steps"] for world in worlds
        ),
        worlds_with_charger_input=sum(world["members_with_charger_input"] > 0 for world in worlds),
        worlds_with_positive_stored_delta=sum(
            world["members_with_positive_stored_delta"] > 0 for world in worlds
        ),
        first_mode_entry_step_observed_worlds=sum(
            world["first_mode_entry_step"] is not None for world in worlds
        ),
        mean_first_mode_entry_step=(
            float(np.mean([
                world["first_mode_entry_step"] for world in worlds
                if world["first_mode_entry_step"] is not None
            ]))
            if any(world["first_mode_entry_step"] is not None for world in worlds)
            else None
        ),
    )
    return result


def _native_raw_env(env):
    raw = getattr(env, "env", None)
    required = (
        "uav_battery_ratios", "last_energy_consumed_wh", "last_energy_charged_wh",
        "last_net_energy_charged_wh", "last_charging_eligible", "charging_wait_steps",
        "last_charging_arrival", "last_min_station_distance_before",
        "last_min_station_distance_after",
    )
    if raw is None or any(not hasattr(raw, name) for name in required):
        raise TypeError("B07 requires the native energy-aware environment ledger")
    return raw


def _partial_payload(
    seed, rewards, metrics, actions, ends, rows, raw_rows, initial_battery, exc
):
    payload = {
        "seed": np.asarray(seed),
        "native_reward": np.asarray(rewards, dtype=np.float64),
        "metrics": np.asarray(metrics, dtype=np.float64),
        "actions": np.asarray(actions, dtype=np.float32),
        "ends": np.asarray(ends, dtype=bool),
        "episode_initial_physical_battery": np.asarray(initial_battery, dtype=np.float64),
        "incomplete": np.asarray(True),
        "failure_type": np.asarray(type(exc).__name__),
        "failure_message": np.asarray(str(exc)),
    }
    payload.update({key: np.asarray(value) for key, value in rows.items()})
    payload.update({key: np.asarray(value) for key, value in raw_rows.items()})
    return payload


def evaluate_world(evaluator, env, config, seed: int, mode: str, *, progress=None,
                   partial_sink=None):
    if mode not in {"O", "F"}:
        raise ValueError("mode must be O or F")
    evaluator.reset_env_state(0)
    if progress is not None:
        progress("attempt", 1)
    observations, info = env.reset(seed=int(seed))
    observations = np.asarray(observations, dtype=np.float32)
    state = np.asarray(info["state"], dtype=np.float32)
    raw = _native_raw_env(env)
    initial_battery = np.asarray(raw.uav_battery_ratios, dtype=np.float64).copy()
    pre_positions = _required_array(info["state_info"], "uav_positions", (8, 3)).copy()
    previous_done = np.ones(1, dtype=bool)
    feedback_modes = np.zeros(8, dtype=bool)
    rewards: list[float] = []
    metrics: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    ends: list[tuple[bool, bool]] = []
    diagnostic_keys = (
        "pre_legal_margin", "post_legal_margin", "pre_legal_battery", "post_legal_battery",
        "post_legal_available", "physical_pre_battery", "physical_post_battery",
        "physical_post_return_margin", "battery_capacity_wh", "consumed_wh",
        "charger_input_wh", "native_clipped_positive_net_charge_wh",
        "signed_stored_energy_delta_wh", "unclipped_stored_energy_delta_wh",
        "capacity_clipping_residual_wh", "upper_capacity_clipped", "lower_capacity_clipped",
        "mode_before", "mode", "entry", "exit", "selected_station",
        "station_distance_m", "station_vector_m", "original_action", "submitted_action",
        "command_changed", "pre_position_m", "post_position_m", "actual_displacement_m",
        "uav_dock_requests", "uav_target_stations", "charging_eligible", "charging_capture",
        "charging_arrival",
        "charging_admitted", "charging_wait_age", "charge_started", "charge_ended",
        "native_station_distance_before_m", "native_station_distance_after_m",
        "uav_charging", "station_occupancy", "station_queue_lengths",
        "agent_skills", "team_skills", "skill_changed",
    )
    rows: dict[str, list[np.ndarray]] = {key: [] for key in diagnostic_keys}
    raw_rows: dict[str, list[np.ndarray]] = {key: [] for key in (
        "raw_reward_info_metrics", "raw_physical_pre_battery",
        "raw_physical_post_battery", "raw_energy_consumed_wh",
        "raw_charger_input_wh", "raw_native_clipped_positive_net_charge_wh",
        "raw_charging_eligible", "raw_charging_arrival", "raw_charging_wait_age",
        "raw_native_station_distance_before_m", "raw_native_station_distance_after_m",
    )}
    terminated = truncated = False
    try:
      for step in range(int(config.episode_length)):
        original, _, step_data = evaluator.step(
            state[None], observations[None], np.asarray([step]), previous_done,
            deterministic=True, return_step_data=True, build_infos=False,
        )
        original = np.asarray(original[0], dtype=np.float32)
        margins, batteries, stations, distances, vectors = decode_legal_observations(observations)
        mode_before = feedback_modes.copy()
        if mode == "F":
            decision = apply_feedback(observations, original, feedback_modes)
            feedback_modes = decision.modes
            entered, exited = decision.entered, decision.exited
            submitted = decision.submitted_actions
        else:
            entered = np.zeros(8, dtype=bool)
            exited = np.zeros(8, dtype=bool)
            submitted = original.copy()
        physical_pre_battery = np.asarray(raw.uav_battery_ratios, dtype=np.float64).copy()
        pre_charging = np.asarray(raw.uav_charging, dtype=bool).copy()
        next_obs, reward, terminated, truncated, next_info = env.step(submitted)
        if progress is not None:
            progress("transition", 1)
        reward_info = next_info["reward_info"]
        rewards.append(float(reward))
        actions.append(submitted.copy())
        ends.append((bool(terminated), bool(truncated)))
        raw_values = {
            "raw_reward_info_metrics": np.asarray([
                reward_info.get(field, np.nan) for field in TRACE_FIELDS
            ]),
            "raw_physical_pre_battery": physical_pre_battery,
            "raw_physical_post_battery": np.asarray(raw.uav_battery_ratios).copy(),
            "raw_energy_consumed_wh": np.asarray(raw.last_energy_consumed_wh).copy(),
            "raw_charger_input_wh": np.asarray(raw.last_energy_charged_wh).copy(),
            "raw_native_clipped_positive_net_charge_wh": np.asarray(
                raw.last_net_energy_charged_wh
            ).copy(),
            "raw_charging_eligible": np.asarray(raw.last_charging_eligible).copy(),
            "raw_charging_arrival": np.asarray(raw.last_charging_arrival).copy(),
            "raw_charging_wait_age": np.asarray(raw.charging_wait_steps).copy(),
            "raw_native_station_distance_before_m": np.asarray(
                raw.last_min_station_distance_before
            ).copy(),
            "raw_native_station_distance_after_m": np.asarray(
                raw.last_min_station_distance_after
            ).copy(),
        }
        for key, value in raw_values.items():
            raw_rows[key].append(np.asarray(value).copy())
        ledger = energy_ledger(raw, physical_pre_battery, pre_charging)
        metrics.append(metric_row(reward, reward_info))
        post_positions = _required_array(next_info["state_info"], "uav_positions", (8, 3)).copy()
        try:
            post_margin, post_battery, _, _, _ = decode_legal_observations(
                np.asarray(next_obs, dtype=np.float32)
            )
            post_available = np.ones(8, dtype=bool)
        except ValueError:
            if not (terminated or truncated):
                raise
            post_margin = np.full(8, np.nan, dtype=np.float32)
            post_battery = np.full(8, np.nan, dtype=np.float32)
            post_available = np.zeros(8, dtype=bool)
        values = {
            "pre_legal_margin": margins,
            "post_legal_margin": post_margin,
            "pre_legal_battery": batteries,
            "post_legal_battery": post_battery,
            "post_legal_available": post_available,
            **ledger,
            "physical_post_return_margin": np.asarray(raw.uav_return_energy_margins).copy(),
            "mode_before": mode_before,
            "mode": feedback_modes.copy(),
            "entry": entered,
            "exit": exited,
            "selected_station": stations,
            "station_distance_m": distances,
            "station_vector_m": vectors,
            "original_action": original,
            "submitted_action": submitted,
            "command_changed": np.any(original != submitted, axis=1),
            "pre_position_m": pre_positions,
            "post_position_m": post_positions,
            "actual_displacement_m": post_positions - pre_positions,
            "uav_dock_requests": np.asarray(raw.uav_dock_requests).copy(),
            "uav_target_stations": np.asarray(raw.uav_target_stations).copy(),
            "station_occupancy": np.asarray(raw.station_occupancy).copy(),
            "station_queue_lengths": np.asarray(raw.station_queue_lengths).copy(),
            "agent_skills": np.asarray(step_data["agent_skills"][0]),
            "team_skills": np.asarray(step_data["team_skills"][0]),
            "skill_changed": np.asarray(step_data["skill_changed"][0]),
        }
        for key in diagnostic_keys:
            rows[key].append(np.asarray(values[key]).copy())
        observations = np.asarray(next_obs, dtype=np.float32)
        state = np.asarray(next_info["next_state"], dtype=np.float32)
        pre_positions = post_positions
        previous_done[:] = terminated or truncated
        if previous_done[0]:
            break
      if not previous_done[0]:
          raise RuntimeError("H3000 evaluation did not reach native termination/truncation")
    except Exception as exc:
        if partial_sink is not None:
            partial_sink(_partial_payload(
                seed, rewards, metrics, actions, ends, rows, raw_rows,
                initial_battery, exc
            ))
        raise
    reward_array = np.asarray(rewards, dtype=np.float64)
    metric_array = np.asarray(metrics, dtype=np.float64)
    action_array = np.asarray(actions, dtype=np.float32)
    end_array = np.asarray(ends, dtype=bool)
    diagnostics = {key: np.asarray(value) for key, value in rows.items()}
    diagnostics.update({key: np.asarray(value) for key, value in raw_rows.items()})
    diagnostics["episode_initial_physical_battery"] = initial_battery
    diagnostics["joint_team_qos"] = metric_array[:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
    diagnostics["joint_team_throughput_mbps"] = metric_array[
        :, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")
    ]
    try:
        world = episode_summary(
            seed, reward_array, metric_array, end_array, diagnostics,
            planned_horizon=int(config.episode_length),
        )
    except Exception as exc:
        if partial_sink is not None:
            partial_sink(_partial_payload(
                seed, rewards, metrics, actions, ends, rows, raw_rows,
                initial_battery, exc
            ))
        raise
    return world, reward_array, metric_array, action_array, end_array, diagnostics


def evaluate_panel(agent, config, seeds, device: torch.device, *, policy_seed: int,
                   mode: str, log_dir: Path, trace_path: Path, progress=None):
    arrays: dict[str, np.ndarray] = {"metric_fields": np.asarray(TRACE_FIELDS)}
    worlds: list[dict[str, Any]] = []
    original_policy = initialization_fingerprint(agent)
    original_steps = optimizer_steps(agent)
    original_normalizers = _normalizer_snapshot(agent)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    def persist_failure(exc):
        arrays["partial_failure_type"] = np.asarray(type(exc).__name__)
        arrays["partial_failure_message"] = np.asarray(str(exc))
        np.savez_compressed(trace_path, **arrays)

    try:
        with preserved_rng():
            seed_everything(policy_seed, device)
            evaluator = HMASDAgent(copy.deepcopy(config), log_dir=str(log_dir), device=device)
            _sync_agent(agent, evaluator)
            evaluator.train(False)
            evaluator_policy = initialization_fingerprint(evaluator)
            evaluator_steps = optimizer_steps(evaluator)
            evaluator_normalizers = _normalizer_snapshot(evaluator)
            if evaluator_policy != original_policy:
                raise RuntimeError("H3000 evaluation policy differs from restored checkpoint")
            for episode_index, seed in enumerate(tuple(int(value) for value in seeds)):
                result = None
                partial = None
                env = None

                def retain_partial(payload):
                    nonlocal partial
                    partial = payload

                try:
                    env = make_env(config, seed)
                    result = evaluate_world(
                        evaluator, env, config, seed, mode, progress=progress,
                        partial_sink=retain_partial,
                    )
                    world, rewards, metrics, actions, ends, diagnostics = result
                    prefix = f"episode_{episode_index}_"
                    arrays.update({
                        prefix + "seed": np.asarray(seed),
                        prefix + "native_reward": rewards,
                        prefix + "metrics": metrics,
                        prefix + "actions": actions,
                        prefix + "ends": ends,
                    })
                    arrays.update({prefix + key: value for key, value in diagnostics.items()})
                    worlds.append(world)
                    if progress is not None:
                        progress("world", copy.deepcopy(world))
                except Exception:
                    if partial is not None:
                        prefix = f"episode_{episode_index}_"
                        arrays.update({prefix + key: value for key, value in partial.items()})
                    raise
                finally:
                    if env is not None:
                        env.close()
            if (
                initialization_fingerprint(evaluator) != evaluator_policy
                or optimizer_steps(evaluator) != evaluator_steps
                or not _same_snapshot(_normalizer_snapshot(evaluator), evaluator_normalizers)
            ):
                raise RuntimeError("H3000 evaluation mutated evaluator state")
        if (
            initialization_fingerprint(agent) != original_policy
            or optimizer_steps(agent) != original_steps
            or not _same_snapshot(_normalizer_snapshot(agent), original_normalizers)
        ):
            raise RuntimeError("H3000 evaluation mutated restored checkpoint state")
        panel_result = {
            "worlds": worlds,
            "aggregate": aggregate_worlds(worlds),
            "actual_transitions": sum(world["actual_length"] for world in worlds),
            "new_optimizer_updates": 0,
            "new_fits": 0,
            "policy_sha256_before_after": original_policy,
            "optimizer_steps_before_after": original_steps,
            "normalizers_immutable": True,
        }
    except Exception as exc:
        persist_failure(exc)
        raise
    np.savez_compressed(trace_path, **arrays)
    panel_result["trace_sha256"] = sha256_file(trace_path)
    return panel_result, arrays


def paired_summary(original: dict[str, Any], feedback: dict[str, Any]):
    if [row["seed"] for row in original["worlds"]] != [row["seed"] for row in feedback["worlds"]]:
        raise RuntimeError("H3000 paired world ordering mismatch")
    fields = (
        "raw_native_J", "native_J_per_actual_step", "actual_length", "cumulative_qos",
        "qos_per_actual_step", "planned_window_qos", "cumulative_throughput_mbps",
        "throughput_mbps_per_actual_step", "planned_window_throughput_mbps",
        "return_constraint_cost_sum", "return_constraint_cost_raw_sum",
        "episode_minimum_battery_ratio", "maximum_service_free_interval_steps",
        "total_signed_stored_energy_delta_wh", "total_charger_input_wh",
    )
    rows = []
    for old, new in zip(original["worlds"], feedback["worlds"], strict=True):
        effects = {field: float(new[field] - old[field]) for field in fields}
        rows.append({
            "seed": old["seed"],
            "O_actual_length": old["actual_length"],
            "F_actual_length": new["actual_length"],
            "effects_F_minus_O": effects,
            "new_zero_service_episode": bool(new["zero_service_episode"] and not old["zero_service_episode"]),
            "removed_zero_service_episode": bool(old["zero_service_episode"] and not new["zero_service_episode"]),
            "losses": {
                "raw_native_J": effects["raw_native_J"] < 0.0,
                "cumulative_qos": effects["cumulative_qos"] < 0.0,
                "cumulative_throughput": effects["cumulative_throughput_mbps"] < 0.0,
                "actual_length": effects["actual_length"] < 0.0,
            },
        })
    aggregate = {}
    for field in fields:
        values = np.asarray([row["effects_F_minus_O"][field] for row in rows])
        aggregate[field + "_F_minus_O_mean"] = float(values.mean())
        aggregate[field + "_F_minus_O_median"] = float(np.median(values))
        aggregate[field + "_F_minus_O_min"] = float(values.min())
        aggregate[field + "_F_minus_O_max"] = float(values.max())
    aggregate.update(
        new_zero_service_episodes=sum(row["new_zero_service_episode"] for row in rows),
        removed_zero_service_episodes=sum(row["removed_zero_service_episode"] for row in rows),
        worlds_with_lower_native_J=sum(row["losses"]["raw_native_J"] for row in rows),
        worlds_with_lower_cumulative_qos=sum(row["losses"]["cumulative_qos"] for row in rows),
        worlds_with_earlier_end=sum(row["losses"]["actual_length"] for row in rows),
    )
    return {"worlds": rows, "aggregate": aggregate}


def run_native(*, b04_source: Path, b05_source: Path, out: Path, launch_sha: str,
               device_name: str = "cuda", threads: int = 4,
               _fixture_bindings=None, _fixture_specs=None,
               _training_horizon=TRAINING_HORIZON, _evaluation_horizon=EVALUATION_HORIZON):
    fixture = _fixture_bindings is not None
    bindings = tuple(_fixture_bindings or PRODUCTION_BINDINGS)
    if not fixture and (device_name != "cuda" or threads != 4):
        raise ValueError("B07 production requires CUDA and exactly four Torch threads")
    if len(bindings) != 2 or {item.block for item in bindings} != {"B04", "B05"}:
        raise ValueError("B07 requires exactly the fixed B04 and B05 N checkpoints")
    roots = {"B04": Path(b04_source), "B05": Path(b05_source)}
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json")):
        raise FileExistsError(f"output already contains B07 scientific records: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "status": "INCOMPLETE",
        "failure": None,
        "launch_sha": launch_sha,
        "device": device_name,
        "requested_torch_threads": threads,
        "new_fits": 0,
        "new_optimizer_updates": 0,
        "independent_training_replications": 0,
        "historical_training_sources": 2,
        "counts": {"episode_attempts": 0, "evaluation_transitions": 0, "member_step_observations": 0},
        "blocks": {},
        "artifacts": {},
    }
    write_json(out / "summary.json", summary)
    try:
        device = torch.device(device_name)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B07 requires Torch FP32 default dtype")
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        torch.set_num_threads(threads)
        if torch.get_num_threads() != threads:
            raise RuntimeError("Torch did not retain the fixed thread count")
        if device.type == "cuda":
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            if torch.backends.cuda.matmul.allow_tf32 or torch.backends.cudnn.allow_tf32:
                raise RuntimeError("B07 requires TF32 disabled")
        checked = {}
        evaluation_configs = {}
        config_reports = {}
        for binding in bindings:
            expected = None if _fixture_specs is None else _fixture_specs[binding.block]
            checked[binding.block] = verify_training_source(
                roots[binding.block], binding, expected_spec=expected,
                training_horizon=_training_horizon,
            )
            evaluation_configs[binding.block], config_reports[binding.block] = derive_evaluation_config(
                checked[binding.block]["config"], training_horizon=_training_horizon,
                evaluation_horizon=_evaluation_horizon,
            )
        write_json(out / "config.json", {
            "object_id": OBJECT_ID,
            "launch_sha": launch_sha,
            "device": device_name,
            "torch_threads": threads,
            "torch_default_dtype": str(torch.get_default_dtype()),
            "tf32": False,
            "modes": ["O", "F"],
            "panels": PANELS if not fixture else {
                block: {"development": checked[block]["spec"].eval_seeds,
                        "final": checked[block]["spec"].final_seeds}
                for block in checked
            },
            "training_horizon": _training_horizon,
            "evaluation_horizon": _evaluation_horizon,
            "battery_capacity_wh": BATTERY_CAPACITY_WH,
            "feedback_layout": asdict(PRODUCTION_LAYOUT),
            "sources": {
                binding.block: {
                    "root": str(roots[binding.block]),
                    "summary_sha256": binding.summary_sha256,
                    "checkpoint_sha256": binding.checkpoint_sha256,
                    "training_sha": binding.training_sha,
                    "final_policy_sha256": binding.final_policy_sha256,
                    "config_sha256": checked[binding.block]["summary"]["config_sha256"],
                    "retained_trace_sha256": {
                        panel: checked[binding.block]["summary"]["artifacts"][
                            str(path.relative_to(roots[binding.block]))
                        ] for panel, path in checked[binding.block]["traces"].items()
                    },
                    "source_semantic_reconciliation": checked[binding.block][
                        "semantic_config_reconciliation"
                    ],
                    "evaluation_config_derivation": config_reports[binding.block],
                }
                for binding in bindings
            },
        })
        summary["config_sha256"] = sha256_file(out / "config.json")

        for binding in bindings:
            source = checked[binding.block]
            eval_config = evaluation_configs[binding.block]
            seed_everything(binding.seed, device)
            agent = HMASDAgent(
                source["config"], log_dir=str(out / binding.block / "loader"), device=device
            )
            agent.load_model(source["checkpoint"])
            agent.train(False)
            if initialization_fingerprint(agent) != binding.final_policy_sha256:
                raise ValueError(f"{binding.block} restored policy identity mismatch")
            block_result = {
                "source_summary_sha256": binding.summary_sha256,
                "source_checkpoint_sha256": binding.checkpoint_sha256,
                "source_config_sha256": source["summary"]["config_sha256"],
                "source_retained_trace_sha256": {
                    panel: source["summary"]["artifacts"][
                        str(path.relative_to(roots[binding.block]))
                    ] for panel, path in source["traces"].items()
                },
                "source_semantic_config_reconciliation": source[
                    "semantic_config_reconciliation"
                ],
                "policy_seed": binding.seed,
                "training_horizon": _training_horizon,
                "evaluation_horizon": _evaluation_horizon,
                "evaluation_config_differences": config_reports[binding.block]["differences"],
                "modes": {}, "paired": {}, "prefix_verification": {},
                "h1500_reproduction_claimed": False,
            }
            summary["blocks"][binding.block] = block_result
            active_record = None

            def progress(kind, value):
                if kind == "attempt":
                    summary["counts"]["episode_attempts"] += int(value)
                elif kind == "transition":
                    summary["counts"]["evaluation_transitions"] += int(value)
                    summary["counts"]["member_step_observations"] += int(value) * 8
                elif kind == "world":
                    active_record.setdefault("completed_worlds", []).append(value)
                else:
                    raise ValueError(f"unknown B07 progress kind {kind}")

            panel_arrays = {}
            for panel, seeds in (
                ("development", source["spec"].eval_seeds),
                ("final", source["spec"].final_seeds),
            ):
                for mode in ("O", "F"):
                    trace = out / binding.block / "trajectories" / f"{panel}_{mode}.npz"
                    block_result["modes"].setdefault(mode, {})[panel] = {
                        "status": "INCOMPLETE", "trace": str(trace.relative_to(out)),
                        "completed_worlds": [],
                    }
                    active_record = block_result["modes"][mode][panel]
                    write_json(out / "summary.json", summary)
                    try:
                        result, arrays = evaluate_panel(
                            agent, eval_config, seeds, device, policy_seed=binding.seed,
                            mode=mode, log_dir=out / binding.block / f"evaluation_{panel}_{mode}",
                            trace_path=trace, progress=progress,
                        )
                    except Exception:
                        if trace.exists():
                            relative = str(trace.relative_to(out))
                            digest = sha256_file(trace)
                            summary["artifacts"][relative] = digest
                            active_record["partial_trace_sha256"] = digest
                        raise
                    panel_arrays[(panel, mode)] = arrays
                    block_result["modes"][mode][panel] = {"status": "COMPLETE", **result}
                    summary["artifacts"][str(trace.relative_to(out))] = result["trace_sha256"]
                    write_json(out / "summary.json", summary)
                block_result["prefix_verification"][panel] = _verify_prefixes(
                    panel_arrays[(panel, "O")], panel_arrays[(panel, "F")], seeds
                )
                block_result["paired"][panel] = paired_summary(
                    block_result["modes"]["O"][panel], block_result["modes"]["F"][panel]
                )
                write_json(out / "summary.json", summary)
            del agent
        expected_attempts = 160 if not fixture else sum(
            2 * (len(checked[item.block]["spec"].eval_seeds)
                 + len(checked[item.block]["spec"].final_seeds))
            for item in bindings
        )
        if summary["counts"]["episode_attempts"] != expected_attempts:
            raise RuntimeError("B07 episode-attempt count mismatch")
        if not fixture and summary["counts"]["evaluation_transitions"] > 480000:
            raise RuntimeError("B07 exceeded its fixed transition upper bound")
        summary.update(
            status="COMPLETE", torch_threads=torch.get_num_threads(), tf32_disabled=True,
            h1500_reproduction_claimed=False, all_pre_intervention_prefixes_verified=True,
        )
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update(
            wall_seconds=time.time() - started,
            cpu_user_seconds=usage.ru_utime - cpu_started.ru_utime,
            cpu_system_seconds=usage.ru_stime - cpu_started.ru_stime,
            peak_rss_kib=int(usage.ru_maxrss),
            rss_scope="B07 runner process high-water mark",
        )
        summary["output_bytes"] = 0
        for _ in range(5):
            write_json(out / "summary.json", summary)
            measured = sum(path.stat().st_size for path in out.rglob("*") if path.is_file())
            if measured == summary["output_bytes"]:
                break
            summary["output_bytes"] = measured
        write_json(out / "summary.json", summary)
