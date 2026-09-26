"""B06 fixed-checkpoint original/observation-feedback native evaluation."""

from __future__ import annotations

import copy
import json
import resource
import time
from dataclasses import asdict, dataclass
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
    make_config,
    make_env,
    optimizer_steps,
    preserved_rng,
    seed_everything,
    sha256_file,
)
from ..b04.evaluation import TRACE_FIELDS, metric_row
from ..b04.native import B04Spec, production_spec as b04_production_spec
from ..b05.native import B05Spec, production_spec as b05_production_spec
from .feedback import PRODUCTION_LAYOUT, apply_feedback, decode_legal_observations


OBJECT_ID = "UAV-SERVICE-AUXILIARY-B06-FEEDBACK"
PANELS = {
    "development": tuple(range(937001, 937009)),
    "final": tuple(range(938001, 938033)),
}
COMMON_ARRAY_SUFFIXES = ("seed", "native_reward", "metrics", "actions", "ends")


@dataclass(frozen=True)
class SourceBinding:
    block: str
    object_id: str
    seed: int
    summary_sha256: str
    checkpoint_sha256: str
    training_sha: str
    final_policy_sha256: str


PRODUCTION_BINDINGS = (
    SourceBinding(
        block="B04",
        object_id="UAV-SERVICE-RISK-B04",
        seed=914021,
        summary_sha256="ab814a3e1d1861bcc8413c15c828dd39ed25c55106b1a71a6dc76a267f7bff78",
        checkpoint_sha256="403908c044ee1c1952e36102959fbe53ab365d4845bacb17acbb7953d1a5def6",
        training_sha="914fc484368cc6c41af211b169c45b02e4a10425",
        final_policy_sha256="3fee4d9c751aac8dd3c0b5d84839624da63ca22a93f05f744647b1dc8f111408",
    ),
    SourceBinding(
        block="B05",
        object_id="UAV-SERVICE-RISK-B05",
        seed=914173,
        summary_sha256="1af4318fdd21d5723054b12d8b89f99688d32190b4d89933074ce2913d9e12c9",
        checkpoint_sha256="1a6a2b6c191d3dc74ac244b474dc6071905c71d6a973eea78a97e94e6fbcceb8",
        training_sha="3de3e3f71c747e2422656126b52ae88beafb562a",
        final_policy_sha256="22ade2e3aa948330acb4916445277edab0611a5159a1bef7beade8d1aefadc79",
    ),
)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, default=_json_default, allow_nan=False) + "\n")


def _normalizer_snapshot(agent: HMASDAgent) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer"):
        normalizer = getattr(agent, name, None)
        if normalizer is None:
            result[name] = None
            continue
        result[name] = {
            field: np.asarray(getattr(normalizer, field)).copy()
            for field in ("mean", "var", "count")
            if hasattr(normalizer, field)
        }
    return result


def _same_snapshot(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.keys() != right.keys():
        return False
    for name in left:
        if left[name] is None or right[name] is None:
            if left[name] is not right[name]:
                return False
            continue
        if left[name].keys() != right[name].keys():
            return False
        if any(not np.array_equal(left[name][key], right[name][key]) for key in left[name]):
            return False
    return True


def _spec_from_config(config_data: dict[str, Any], binding: SourceBinding):
    values = dict(config_data["spec"])
    for key in ("eval_seeds", "final_seeds", "eval_rollouts", "fact_seeds"):
        values[key] = tuple(values[key])
    cls = B04Spec if binding.block == "B04" else B05Spec
    return cls(**values)


def _production_spec(binding: SourceBinding):
    if binding.block == "B04":
        return b04_production_spec(binding.seed)
    if binding.block == "B05":
        return b05_production_spec(binding.seed)
    raise ValueError(f"unknown production source block {binding.block}")


def verify_source(root: Path, binding: SourceBinding, *, expected_spec=None):
    """Verify a complete retained N run and every B06-consumed artifact."""

    root = Path(root)
    if sha256_file(root / "summary.json") != binding.summary_sha256:
        raise ValueError(f"{binding.block} summary identity mismatch")
    summary = json.loads((root / "summary.json").read_text())
    identity = (summary.get("object_id"), summary.get("status"), summary.get("arm"), summary.get("seed"))
    if identity != (binding.object_id, "COMPLETE", "N", binding.seed):
        raise ValueError(f"{binding.block} source run identity/status mismatch")
    if summary.get("launch_sha") != binding.training_sha:
        raise ValueError(f"{binding.block} source launch SHA mismatch")
    if summary.get("final_policy_sha256") != binding.final_policy_sha256:
        raise ValueError(f"{binding.block} final policy identity mismatch")

    config_path = root / "config.json"
    checkpoint_path = root / "checkpoint_final" / "agent.pt"
    if sha256_file(config_path) != summary.get("config_sha256"):
        raise ValueError(f"{binding.block} config identity mismatch")
    if sha256_file(checkpoint_path) != binding.checkpoint_sha256:
        raise ValueError(f"{binding.block} checkpoint identity mismatch")
    if summary.get("artifacts", {}).get("checkpoint_final/agent.pt") != binding.checkpoint_sha256:
        raise ValueError(f"{binding.block} checkpoint is not the summary-bound artifact")

    config_data = json.loads(config_path.read_text())
    spec = _spec_from_config(config_data, binding)
    fixture = expected_spec is not None
    fixed_spec = _production_spec(binding) if not fixture else expected_spec
    if spec != fixed_spec or config_data.get("arm") != "N":
        raise ValueError(f"{binding.block} source is not the fixed N production specification")
    if not fixture and (
        spec.eval_seeds != PANELS["development"] or spec.final_seeds != PANELS["final"]
    ):
        raise ValueError(f"{binding.block} source world panels changed")
    current_config = make_config(spec)
    expected_active = json.loads(json.dumps(active_config(current_config)), parse_constant=str)
    recorded_active = config_data.get("active")
    active_mismatches = {
        key: (recorded_active.get(key), expected_active.get(key))
        for key in set(recorded_active) | set(expected_active)
        if recorded_active.get(key) != expected_active.get(key)
    }
    allowed_path_difference = {
        "scenario7_baseline_metrics_path"
    } if (
        not fixture
        and recorded_active.get("scenario7_comparison_gate_enabled") is False
        and recorded_active.get("scenario7_run_physical_feasibility_check") is False
    ) else set()
    if set(active_mismatches) - allowed_path_difference:
        raise ValueError(f"{binding.block} active config semantics mismatch: {active_mismatches}")

    checkpoint_data = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = copy.deepcopy(checkpoint_data.get("config"))
    del checkpoint_data
    if config is None:
        raise ValueError(f"{binding.block} checkpoint lacks its complete saved config")
    checkpoint_active = json.loads(json.dumps(active_config(config)), parse_constant=str)
    if checkpoint_active != recorded_active:
        raise ValueError(f"{binding.block} checkpoint config differs from digest-bound config.json")
    if (
        config.obs_dim != PRODUCTION_LAYOUT.observation_dim
        or config.n_agents != PRODUCTION_LAYOUT.n_uavs
        or config.action_dim != 4
        or (not fixture and config.episode_length != 1500)
        or config.k != 10
        or config.lambda_return != 2.0
        or config.use_obsnorm
        or config.use_statenorm
    ):
        raise ValueError(f"{binding.block} policy/environment contract mismatch")
    expected_device = "cuda" if not fixture else summary.get("device")
    expected_threads = 4 if not fixture else spec.threads
    if summary.get("device") != expected_device or summary.get("torch_threads") != expected_threads:
        raise ValueError(f"{binding.block} source training device/thread contract mismatch")
    if summary.get("counts", {}).get("transitions") != spec.transitions:
        raise ValueError(f"{binding.block} source training exposure mismatch")

    traces = {
        "development": root / "trajectories" / "evaluation_30.npz",
        "final": root / "trajectories" / "evaluation_final.npz",
    }
    for panel, path in traces.items():
        relative = str(path.relative_to(root))
        recorded = summary.get("artifacts", {}).get(relative)
        if not recorded or sha256_file(path) != recorded:
            raise ValueError(f"{binding.block} retained {panel} trajectory identity mismatch")
        source_panel = summary["evaluations"]["30"] if panel == "development" else summary["final_evaluation"]
        expected_seeds = spec.eval_seeds if panel == "development" else spec.final_seeds
        if tuple(row["seed"] for row in source_panel["worlds"]) != expected_seeds:
            raise ValueError(f"{binding.block} retained {panel} world ordering mismatch")
    return {"summary": summary, "config_data": config_data, "spec": spec,
            "config": config, "checkpoint": checkpoint_path, "traces": traces,
            "semantic_config_reconciliation": {
                "differences": active_mismatches,
                "allowed_unused_fields": sorted(allowed_path_difference),
                "comparison_gate_enabled": recorded_active.get("scenario7_comparison_gate_enabled"),
                "physical_feasibility_check_enabled": recorded_active.get(
                    "scenario7_run_physical_feasibility_check"
                ),
                "evaluation_uses_checkpoint_saved_config": True,
            }}


def _required_array(mapping: dict[str, Any], key: str, shape: tuple[int, ...] | None = None):
    if key not in mapping:
        raise KeyError(f"native telemetry is missing {key}")
    value = np.asarray(mapping[key])
    if shape is not None and value.shape != shape:
        raise ValueError(f"native telemetry {key} has shape {value.shape}, expected {shape}")
    if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
        raise FloatingPointError(f"native telemetry {key} is non-finite")
    return value


def _episode_summary(seed: int, rewards: np.ndarray, metrics: np.ndarray,
                     ends: np.ndarray, diagnostics: dict[str, np.ndarray]):
    length = int(rewards.shape[0])
    battery_values = np.concatenate((
        diagnostics["pre_legal_battery"][0],
        diagnostics["physical_post_battery"].reshape(-1),
    ))
    margin_values = np.concatenate((
        diagnostics["pre_legal_margin"][0],
        diagnostics["physical_post_return_margin"].reshape(-1),
    ))
    mode_durations = []
    for agent_index in range(diagnostics["mode"].shape[1]):
        values = diagnostics["mode"][:, agent_index]
        padded = np.concatenate(([False], values, [False])).astype(np.int8)
        changes = np.diff(padded)
        starts, stops = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)
        mode_durations.append((stops - starts).astype(int).tolist())
    override_steps = np.flatnonzero(diagnostics["command_changed"].any(axis=1))
    entry_steps = np.flatnonzero(diagnostics["entry"].any(axis=1))
    realized_motion = np.linalg.norm(diagnostics["actual_displacement_m"], axis=2) > 1e-7
    blocked_override = diagnostics["command_changed"] & ~realized_motion
    row: dict[str, Any] = {
        "seed": int(seed),
        "raw_native_J": float(rewards.sum()),
        "native_J_per_step": float(rewards.mean()),
        "actual_length": length,
        "terminal_type": _terminal_kind(bool(ends[-1, 0]), bool(ends[-1, 1])),
        "episode_minimum_battery_ratio": float(np.min(battery_values)),
        "episode_minimum_return_margin": float(np.min(margin_values)),
        "zero_service_episode": bool(
            np.all(metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")] == 0.0)
        ),
        "mode_uav_steps": int(diagnostics["mode"].sum()),
        "entry_count": int(diagnostics["entry"].sum()),
        "exit_count": int(diagnostics["exit"].sum()),
        "command_override_uav_steps": int(diagnostics["command_changed"].sum()),
        "realized_motion_uav_steps": int(realized_motion.sum()),
        "blocked_override_uav_steps": int(blocked_override.sum()),
        "negative_return_margin_uav_steps": int(
            (diagnostics["physical_post_return_margin"] < 0.0).sum()
        ),
        "return_cost_saturated_steps": int(
            (metrics[:, TRACE_FIELDS.index("return_constraint_cost")] >= 1.0).sum()
        ),
        "maximum_simultaneous_modes": int(diagnostics["mode"].sum(axis=1).max(initial=0)),
        "first_mode_entry_step": int(entry_steps[0]) if entry_steps.size else None,
        "first_command_override_step": int(override_steps[0]) if override_steps.size else None,
        "mode_durations_by_uav": mode_durations,
    }
    for column, field in enumerate(TRACE_FIELDS):
        row[f"{field}_sum"] = float(metrics[:, column].sum())
        row[f"{field}_per_step"] = float(metrics[:, column].mean())
    bins = []
    for start in range(0, 1500, 250):
        stop = min(start + 250, length)
        if start >= length:
            bins.append({"start": start, "stop": start, "steps": 0})
            continue
        bins.append({
            "start": start,
            "stop": stop,
            "steps": stop - start,
            "raw_native_J": float(rewards[start:stop].sum()),
            "qos_satisfaction_ratio_mean": float(
                metrics[start:stop, TRACE_FIELDS.index("qos_satisfaction_ratio")].mean()
            ),
            "delivered_end_to_end_throughput_mbps_mean": float(
                metrics[start:stop, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")].mean()
            ),
            "return_constraint_cost_mean": float(
                metrics[start:stop, TRACE_FIELDS.index("return_constraint_cost")].mean()
            ),
            "return_constraint_cost_raw_mean": float(
                metrics[start:stop, TRACE_FIELDS.index("return_constraint_cost_raw")].mean()
            ),
            "mode_uav_steps": int(diagnostics["mode"][start:stop].sum()),
        })
    row["descriptive_250_step_bins"] = bins
    return row


def _aggregate_worlds(worlds: list[dict[str, Any]]) -> dict[str, Any]:
    nullable_timings = {"first_mode_entry_step", "first_command_override_step"}
    scalar_fields = [
        key for key, value in worlds[0].items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and key not in {"seed", "actual_length"} | nullable_timings
    ]
    result = {f"mean_{key}": float(np.mean([row[key] for row in worlds])) for key in scalar_fields}
    for key in nullable_timings:
        observed = [row[key] for row in worlds if row[key] is not None]
        result[f"{key}_observed_worlds"] = len(observed)
        result[f"mean_{key}"] = float(np.mean(observed)) if observed else None
        result[f"minimum_{key}"] = min(observed) if observed else None
        result[f"maximum_{key}"] = max(observed) if observed else None
    result.update(
        primary_native_J_mean=result["mean_raw_native_J"],
        actual_episode_attempts=len(worlds),
        actual_transitions=sum(row["actual_length"] for row in worlds),
        minimum_episode_battery_ratio=min(row["episode_minimum_battery_ratio"] for row in worlds),
        p10_episode_minimum_battery_ratio=float(np.quantile(
            [row["episode_minimum_battery_ratio"] for row in worlds], 0.1
        )),
        worst_episode_return_margin=min(row["episode_minimum_return_margin"] for row in worlds),
        zero_service_episodes=sum(row["zero_service_episode"] for row in worlds),
    )
    return result


def _evaluate_panel(agent: HMASDAgent, config, seeds, device: torch.device, *,
                    policy_seed: int, mode: str, log_dir: Path, trace_path: Path,
                    progress=None):
    if mode not in {"O", "F"}:
        raise ValueError("mode must be O or F")
    arrays: dict[str, np.ndarray] = {"metric_fields": np.asarray(TRACE_FIELDS)}
    worlds: list[dict[str, Any]] = []
    original_policy = initialization_fingerprint(agent)
    original_steps = optimizer_steps(agent)
    original_normalizers = _normalizer_snapshot(agent)
    with preserved_rng():
        seed_everything(policy_seed, device)
        eval_config = copy.deepcopy(config)
        eval_config.num_envs = 1
        eval_config.calculate_and_set_buffer_sizes()
        evaluator = HMASDAgent(eval_config, log_dir=str(log_dir), device=device)
        _sync_agent(agent, evaluator)
        evaluator.train(False)
        evaluator_policy = initialization_fingerprint(evaluator)
        evaluator_steps = optimizer_steps(evaluator)
        evaluator_normalizers = _normalizer_snapshot(evaluator)
        if evaluator_policy != original_policy:
            raise RuntimeError("evaluation policy copy differs from restored checkpoint")

        for episode_index, seed in enumerate(tuple(int(value) for value in seeds)):
            env = make_env(eval_config, seed)
            rewards: list[float] = []
            metrics: list[np.ndarray] = []
            submitted_actions: list[np.ndarray] = []
            ends: list[tuple[bool, bool]] = []
            diagnostic_lists: dict[str, list[np.ndarray]] = {key: [] for key in (
                "pre_legal_margin", "post_legal_margin", "pre_legal_battery",
                "post_legal_battery", "post_legal_available",
                "physical_post_return_margin", "physical_post_battery",
                "mode_before", "mode", "entry", "exit", "selected_station",
                "station_distance_m", "station_vector_m", "original_action",
                "submitted_action", "command_changed", "pre_position_m",
                "post_position_m", "actual_displacement_m", "uav_charging",
                "uav_dock_requests", "uav_target_stations", "station_occupancy",
                "station_queue_lengths", "agent_skills", "team_skills", "skill_changed",
            )}
            charger_input_wh: list[float] = []
            try:
                evaluator.reset_env_state(0)
                if progress is not None:
                    progress("attempt", 1)
                observations, info = env.reset(seed=seed)
                observations = np.asarray(observations, dtype=np.float32)
                state = np.asarray(info["state"], dtype=np.float32)
                pre_positions = _required_array(info["state_info"], "uav_positions", (config.n_agents, 3)).copy()
                previous_done = np.ones(1, dtype=bool)
                feedback_modes = np.zeros(config.n_agents, dtype=bool)
                terminated = truncated = False
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
                        entered = np.zeros(config.n_agents, dtype=bool)
                        exited = np.zeros(config.n_agents, dtype=bool)
                        submitted = original.copy()
                    next_obs, reward, terminated, truncated, next_info = env.step(submitted)
                    if progress is not None:
                        progress("transition", 1)
                    reward_info = next_info["reward_info"]
                    rewards.append(float(reward))
                    metrics.append(metric_row(reward, reward_info))
                    submitted_actions.append(submitted.copy())
                    ends.append((bool(terminated), bool(truncated)))
                    post_positions = _required_array(
                        next_info["state_info"], "uav_positions", (config.n_agents, 3)
                    ).copy()
                    try:
                        post_legal_margin, post_legal_battery, _, _, _ = (
                            decode_legal_observations(np.asarray(next_obs, dtype=np.float32))
                        )
                        post_legal_available = np.ones(config.n_agents, dtype=bool)
                    except ValueError:
                        if not (terminated or truncated):
                            raise
                        post_legal_margin = np.full(config.n_agents, np.nan, dtype=np.float32)
                        post_legal_battery = np.full(config.n_agents, np.nan, dtype=np.float32)
                        post_legal_available = np.zeros(config.n_agents, dtype=bool)
                    values = {
                        "pre_legal_margin": margins,
                        "post_legal_margin": post_legal_margin,
                        "pre_legal_battery": batteries,
                        "post_legal_battery": post_legal_battery,
                        "post_legal_available": post_legal_available,
                        "physical_post_return_margin": _required_array(
                            reward_info, "uav_return_energy_margins", (config.n_agents,)
                        ),
                        "physical_post_battery": _required_array(
                            reward_info, "uav_battery_ratios", (config.n_agents,)
                        ),
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
                        "uav_charging": _required_array(reward_info, "uav_charging", (config.n_agents,)),
                        "uav_dock_requests": _required_array(reward_info, "uav_dock_requests", (config.n_agents,)),
                        "uav_target_stations": _required_array(reward_info, "uav_target_stations", (config.n_agents,)),
                        "station_occupancy": _required_array(reward_info, "charging_station_occupancy", (2,)),
                        "station_queue_lengths": _required_array(reward_info, "charging_station_queue_lengths", (2,)),
                        "agent_skills": np.asarray(step_data["agent_skills"][0]),
                        "team_skills": np.asarray(step_data["team_skills"][0]),
                        "skill_changed": np.asarray(step_data["skill_changed"][0]),
                    }
                    for key, value in values.items():
                        diagnostic_lists[key].append(np.asarray(value).copy())
                    charger_input_wh.append(float(reward_info["step_charger_input_wh"]))
                    observations = np.asarray(next_obs, dtype=np.float32)
                    state = np.asarray(next_info["next_state"], dtype=np.float32)
                    pre_positions = post_positions
                    previous_done[:] = terminated or truncated
                    if previous_done[0]:
                        break
                if not previous_done[0]:
                    raise RuntimeError("evaluation did not reach native termination/truncation")
            except Exception as exc:
                if rewards:
                    partial_prefix = f"episode_{episode_index}_"
                    arrays.update({
                        partial_prefix + "seed": np.asarray(seed),
                        partial_prefix + "native_reward": np.asarray(rewards, dtype=np.float64),
                        partial_prefix + "metrics": np.asarray(metrics, dtype=np.float64),
                        partial_prefix + "actions": np.asarray(submitted_actions, dtype=np.float32),
                        partial_prefix + "ends": np.asarray(ends, dtype=bool),
                        partial_prefix + "incomplete": np.asarray(True),
                        partial_prefix + "failure_type": np.asarray(type(exc).__name__),
                        partial_prefix + "failure_message": np.asarray(str(exc)),
                    })
                    arrays.update({
                        partial_prefix + key: np.asarray(value)
                        for key, value in diagnostic_lists.items()
                    })
                    arrays[partial_prefix + "step_charger_input_wh"] = np.asarray(
                        charger_input_wh, dtype=np.float64
                    )
                if len(arrays) > 1:
                    trace_path.parent.mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(trace_path, **arrays)
                raise
            finally:
                env.close()

            reward_array = np.asarray(rewards, dtype=np.float64)
            metric_array = np.asarray(metrics, dtype=np.float64)
            action_array = np.asarray(submitted_actions, dtype=np.float32)
            end_array = np.asarray(ends, dtype=bool)
            diagnostics = {key: np.asarray(value) for key, value in diagnostic_lists.items()}
            diagnostics["step_charger_input_wh"] = np.asarray(charger_input_wh, dtype=np.float64)
            worlds.append(_episode_summary(seed, reward_array, metric_array, end_array, diagnostics))
            prefix = f"episode_{episode_index}_"
            arrays.update({
                prefix + "seed": np.asarray(seed),
                prefix + "native_reward": reward_array,
                prefix + "metrics": metric_array,
                prefix + "actions": action_array,
                prefix + "ends": end_array,
            })
            arrays.update({prefix + key: value for key, value in diagnostics.items()})
            if progress is not None:
                progress("world", copy.deepcopy(worlds[-1]))

        if (
            initialization_fingerprint(evaluator) != evaluator_policy
            or optimizer_steps(evaluator) != evaluator_steps
            or not _same_snapshot(_normalizer_snapshot(evaluator), evaluator_normalizers)
        ):
            raise RuntimeError("fixed-policy evaluation mutated evaluator state")
    if (
        initialization_fingerprint(agent) != original_policy
        or optimizer_steps(agent) != original_steps
        or not _same_snapshot(_normalizer_snapshot(agent), original_normalizers)
    ):
        raise RuntimeError("fixed-policy evaluation mutated restored checkpoint state")
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(trace_path, **arrays)
    return {
        "worlds": worlds,
        "aggregate": _aggregate_worlds(worlds),
        "actual_transitions": sum(row["actual_length"] for row in worlds),
        "new_optimizer_updates": 0,
        "new_fits": 0,
        "policy_sha256_before_after": original_policy,
        "optimizer_steps_before_after": original_steps,
        "normalizers_immutable": True,
        "trace_sha256": sha256_file(trace_path),
    }, arrays


def _compare_retained_original(old_path: Path, current: dict[str, np.ndarray]) -> dict[str, Any]:
    checked: list[str] = []
    with np.load(old_path, allow_pickle=False) as retained:
        if not np.array_equal(retained["metric_fields"], current["metric_fields"]):
            raise RuntimeError("original metric field schema does not reproduce")
        checked.append("metric_fields")
        episode_indices = sorted(
            int(key.split("_")[1]) for key in retained.files if key.endswith("_seed")
        )
        for episode_index in episode_indices:
            for suffix in COMMON_ARRAY_SUFFIXES:
                key = f"episode_{episode_index}_{suffix}"
                if key not in current or not np.array_equal(retained[key], current[key]):
                    raise RuntimeError(f"original retained array does not reproduce: {key}")
                checked.append(key)
    return {"matched": True, "comparison": "array_equal", "checked_arrays": checked,
            "retained_trace_sha256": sha256_file(old_path)}


def _verify_prefixes(original: dict[str, np.ndarray], feedback: dict[str, np.ndarray], seeds):
    rows = []
    for episode_index, seed in enumerate(seeds):
        prefix = f"episode_{episode_index}_"
        changed = feedback[prefix + "command_changed"].any(axis=1)
        changed_steps = np.flatnonzero(changed)
        first = int(changed_steps[0]) if changed_steps.size else None
        actor_stop = len(changed) if first is None else first + 1
        transition_stop = len(changed) if first is None else first
        checks = {
            "actor_actions": np.array_equal(
                original[prefix + "original_action"][:actor_stop],
                feedback[prefix + "original_action"][:actor_stop],
            ),
            "pre_legal_margin": np.array_equal(
                original[prefix + "pre_legal_margin"][:actor_stop],
                feedback[prefix + "pre_legal_margin"][:actor_stop],
            ),
            "pre_legal_battery": np.array_equal(
                original[prefix + "pre_legal_battery"][:actor_stop],
                feedback[prefix + "pre_legal_battery"][:actor_stop],
            ),
            "pre_position_m": np.array_equal(
                original[prefix + "pre_position_m"][:actor_stop],
                feedback[prefix + "pre_position_m"][:actor_stop],
            ),
            "agent_skills": np.array_equal(
                original[prefix + "agent_skills"][:actor_stop],
                feedback[prefix + "agent_skills"][:actor_stop],
            ),
            "team_skills": np.array_equal(
                original[prefix + "team_skills"][:actor_stop],
                feedback[prefix + "team_skills"][:actor_stop],
            ),
            "skill_changed": np.array_equal(
                original[prefix + "skill_changed"][:actor_stop],
                feedback[prefix + "skill_changed"][:actor_stop],
            ),
            "native_reward": np.array_equal(
                original[prefix + "native_reward"][:transition_stop],
                feedback[prefix + "native_reward"][:transition_stop],
            ),
            "metrics": np.array_equal(
                original[prefix + "metrics"][:transition_stop],
                feedback[prefix + "metrics"][:transition_stop],
            ),
            "ends": np.array_equal(
                original[prefix + "ends"][:transition_stop],
                feedback[prefix + "ends"][:transition_stop],
            ),
        }
        if not all(checks.values()):
            raise RuntimeError(f"paired pre-intervention prefix mismatch for world {seed}")
        rows.append({"seed": int(seed), "first_command_change_step": first,
                     "verified_transition_prefix_steps": transition_stop, "checks": checks})
    return rows


def _paired_summary(original: dict[str, Any], feedback: dict[str, Any]):
    if [row["seed"] for row in original["worlds"]] != [row["seed"] for row in feedback["worlds"]]:
        raise RuntimeError("paired world ordering mismatch")
    keys = (
        "raw_native_J", "qos_satisfaction_ratio_sum",
        "qos_satisfaction_ratio_per_step",
        "delivered_end_to_end_throughput_mbps_sum",
        "delivered_end_to_end_throughput_mbps_per_step",
        "return_constraint_cost_sum", "return_constraint_cost_per_step",
        "return_constraint_cost_raw_sum", "return_constraint_cost_raw_per_step",
        "cutoff_event_count_sum",
        "depletion_event_count_sum", "episode_minimum_battery_ratio",
        "episode_minimum_return_margin",
    )
    rows = []
    for old, new in zip(original["worlds"], feedback["worlds"], strict=True):
        effects = {key: float(new[key] - old[key]) for key in keys}
        rows.append({
            "seed": old["seed"],
            "O_actual_length": old["actual_length"],
            "F_actual_length": new["actual_length"],
            "effects_F_minus_O": effects,
            "new_zero_service_episode": bool(new["zero_service_episode"] and not old["zero_service_episode"]),
            "removed_zero_service_episode": bool(old["zero_service_episode"] and not new["zero_service_episode"]),
            "retained_zero_service_episode": bool(old["zero_service_episode"] and new["zero_service_episode"]),
            "losses": {
                "native_J": effects["raw_native_J"] < 0.0,
                "qos": effects["qos_satisfaction_ratio_sum"] < 0.0,
                "throughput": effects["delivered_end_to_end_throughput_mbps_sum"] < 0.0,
                "minimum_battery": effects["episode_minimum_battery_ratio"] < 0.0,
                "minimum_return_margin": effects["episode_minimum_return_margin"] < 0.0,
            },
        })
    aggregate: dict[str, Any] = {}
    for key in keys:
        values = np.asarray([row["effects_F_minus_O"][key] for row in rows], dtype=np.float64)
        aggregate[key + "_F_minus_O_mean"] = float(values.mean())
        aggregate[key + "_F_minus_O_median"] = float(np.median(values))
        aggregate[key + "_F_minus_O_min"] = float(values.min())
        aggregate[key + "_F_minus_O_max"] = float(values.max())
        aggregate[key + "_F_minus_O_amplitude"] = float(values.max() - values.min())
    aggregate.update(
        new_zero_service_episodes=sum(row["new_zero_service_episode"] for row in rows),
        removed_zero_service_episodes=sum(row["removed_zero_service_episode"] for row in rows),
        retained_zero_service_episodes=sum(row["retained_zero_service_episode"] for row in rows),
        worlds_with_lower_native_J=sum(row["losses"]["native_J"] for row in rows),
        worlds_with_lower_qos=sum(row["losses"]["qos"] for row in rows),
        worlds_with_lower_throughput=sum(row["losses"]["throughput"] for row in rows),
    )
    return {"worlds": rows, "aggregate": aggregate}


def run_native(*, b04_source: Path, b05_source: Path, out: Path, launch_sha: str,
               device_name: str = "cuda", threads: int = 4,
               _fixture_bindings=None, _fixture_specs=None):
    """Run the one fixed B06 batch; underscored fixture inputs are test-only."""

    fixture = _fixture_bindings is not None
    bindings = tuple(_fixture_bindings or PRODUCTION_BINDINGS)
    if not fixture and (device_name != "cuda" or threads != 4):
        raise ValueError("B06 production requires CUDA and exactly four Torch threads")
    if len(bindings) != 2 or {item.block for item in bindings} != {"B04", "B05"}:
        raise ValueError("B06 requires exactly the fixed B04 and B05 source blocks")
    roots = {"B04": Path(b04_source), "B05": Path(b05_source)}
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json")):
        raise FileExistsError(f"output already contains B06 scientific records: {out}")
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
        "counts": {"episode_attempts": 0, "evaluation_transitions": 0, "agent_step_observations": 0},
        "blocks": {},
        "artifacts": {},
    }
    write_json(out / "summary.json", summary)
    try:
        device = torch.device(device_name)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B06 requires the default Torch dtype to remain float32")
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        torch.set_num_threads(threads)
        if torch.get_num_threads() != threads:
            raise RuntimeError("Torch did not retain the fixed thread count")
        if device.type == "cuda":
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            if torch.backends.cuda.matmul.allow_tf32 or torch.backends.cudnn.allow_tf32:
                raise RuntimeError("B06 requires TF32 disabled")

        checked = {}
        for binding in bindings:
            expected = None if _fixture_specs is None else _fixture_specs[binding.block]
            checked[binding.block] = verify_source(roots[binding.block], binding, expected_spec=expected)
        write_json(out / "config.json", {
            "object_id": OBJECT_ID,
            "launch_sha": launch_sha,
            "device": device_name,
            "torch_threads": threads,
            "tf32": False,
            "torch_default_dtype": str(torch.get_default_dtype()),
            "modes": ["O", "F"],
            "panels": PANELS,
            "horizon": 1500 if not fixture else checked["B04"]["spec"].episode_length,
            "feedback_layout": asdict(PRODUCTION_LAYOUT),
            "sources": {
                binding.block: {
                    "root": str(roots[binding.block]),
                    "summary_sha256": binding.summary_sha256,
                    "checkpoint_sha256": binding.checkpoint_sha256,
                    "training_sha": binding.training_sha,
                    "final_policy_sha256": binding.final_policy_sha256,
                    "config_sha256": checked[binding.block]["summary"]["config_sha256"],
                    "semantic_config_reconciliation": checked[binding.block][
                        "semantic_config_reconciliation"
                    ],
                    "retained_trace_sha256": {
                        panel: checked[binding.block]["summary"]["artifacts"][str(path.relative_to(roots[binding.block]))]
                        for panel, path in checked[binding.block]["traces"].items()
                    },
                }
                for binding in bindings
            },
        })
        summary["config_sha256"] = sha256_file(out / "config.json")

        for binding in bindings:
            source = checked[binding.block]
            seed_everything(binding.seed, device)
            agent = HMASDAgent(source["config"], log_dir=str(out / binding.block / "loader"), device=device)
            agent.load_model(source["checkpoint"])
            agent.train(False)
            if initialization_fingerprint(agent) != binding.final_policy_sha256:
                raise ValueError(f"{binding.block} restored policy identity mismatch")
            block_result: dict[str, Any] = {
                "source_summary_sha256": binding.summary_sha256,
                "source_checkpoint_sha256": binding.checkpoint_sha256,
                "source_config_sha256": source["summary"]["config_sha256"],
                "source_retained_trace_sha256": {
                    panel: source["summary"]["artifacts"][
                        str(path.relative_to(roots[binding.block]))
                    ]
                    for panel, path in source["traces"].items()
                },
                "policy_seed": binding.seed,
                "modes": {},
                "paired": {},
                "original_reproduction": {},
                "prefix_verification": {},
            }
            summary["blocks"][binding.block] = block_result
            write_json(out / "summary.json", summary)
            panel_arrays: dict[tuple[str, str], dict[str, np.ndarray]] = {}

            active_panel_record = None

            def record_progress(kind, amount):
                if kind == "attempt":
                    summary["counts"]["episode_attempts"] += int(amount)
                elif kind == "transition":
                    summary["counts"]["evaluation_transitions"] += int(amount)
                    summary["counts"]["agent_step_observations"] += (
                        int(amount) * source["config"].n_agents
                    )
                elif kind == "world":
                    active_panel_record.setdefault("completed_worlds", []).append(amount)
                else:
                    raise ValueError(f"unknown B06 progress kind {kind}")

            for panel, seeds in (
                ("development", source["spec"].eval_seeds),
                ("final", source["spec"].final_seeds),
            ):
                for mode in ("O", "F"):
                    trace = out / binding.block / "trajectories" / f"{panel}_{mode}.npz"
                    block_result["modes"].setdefault(mode, {})[panel] = {
                        "status": "INCOMPLETE", "trace": str(trace.relative_to(out))
                    }
                    active_panel_record = block_result["modes"][mode][panel]
                    write_json(out / "summary.json", summary)
                    try:
                        result, arrays = _evaluate_panel(
                            agent, source["config"], seeds, device, policy_seed=binding.seed,
                            mode=mode, log_dir=out / binding.block / f"evaluation_{panel}_{mode}",
                            trace_path=trace, progress=record_progress,
                        )
                    except Exception:
                        if trace.exists():
                            relative = str(trace.relative_to(out))
                            summary["artifacts"][relative] = sha256_file(trace)
                            block_result["modes"][mode][panel]["partial_trace_sha256"] = (
                                summary["artifacts"][relative]
                            )
                        raise
                    panel_arrays[(panel, mode)] = arrays
                    block_result["modes"][mode][panel] = {"status": "COMPLETE", **result}
                    relative = str(trace.relative_to(out))
                    summary["artifacts"][relative] = result["trace_sha256"]
                    write_json(out / "summary.json", summary)
                    if mode == "O":
                        # A retained-array mismatch invalidates the paired cell and
                        # stops before any dependent feedback evaluation.
                        block_result["original_reproduction"][panel] = (
                            _compare_retained_original(
                                source["traces"][panel], panel_arrays[(panel, "O")]
                            )
                        )
                        write_json(out / "summary.json", summary)
                block_result["prefix_verification"][panel] = _verify_prefixes(
                    panel_arrays[(panel, "O")], panel_arrays[(panel, "F")], seeds
                )
                block_result["paired"][panel] = _paired_summary(
                    block_result["modes"]["O"][panel], block_result["modes"]["F"][panel]
                )
                write_json(out / "summary.json", summary)
            del agent

        expected_attempts = 160 if not fixture else sum(
            2 * (len(checked[item.block]["spec"].eval_seeds) + len(checked[item.block]["spec"].final_seeds))
            for item in bindings
        )
        if summary["counts"]["episode_attempts"] != expected_attempts:
            raise RuntimeError("B06 episode-attempt count mismatch")
        if not fixture and summary["counts"]["evaluation_transitions"] > 240000:
            raise RuntimeError("B06 exceeded its fixed transition upper bound")
        summary.update(
            status="COMPLETE",
            torch_threads=torch.get_num_threads(),
            tf32_disabled=True,
            all_original_arrays_reproduced=True,
            all_pre_intervention_prefixes_verified=True,
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
            rss_scope="B06 runner process high-water mark",
        )
        summary["output_bytes"] = 0
        for _ in range(5):
            write_json(out / "summary.json", summary)
            measured = sum(path.stat().st_size for path in out.rglob("*") if path.is_file())
            if measured == summary["output_bytes"]:
                break
            summary["output_bytes"] = measured
        write_json(out / "summary.json", summary)
