"""Two fixed B04 fits removing only the low-level entropy coefficient."""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import random
import resource
import sys
import time
import traceback
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    capture_parameters,
    digest_agent,
    finite,
    jsonable,
    model_modules,
    native_components,
    optimizer_counts,
    parameter_motion,
    preserve_rng,
    reset_all,
    save_checkpoint,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_entropy_b04"
EVALUATION_SEED_BASE = 1_200_000
CONTROL_SOURCE_SHA = "89486d32ea569728f39d6e21b53f8a7c8854e74c"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class TrainingCell:
    index: int
    key: str
    arm: str
    law: str
    seed: int
    tag: str
    control_tag: str
    control_cell_key: str
    control_summary_sha256: str
    expected_initial_digest: str


CELLS = (
    TrainingCell(
        1, "h6_zero", "H6", "clip", 942201, "s1_entropy_b04_h6_zero_s942201",
        "s1_action_law_b03_h6_clip_s942201", "h6_clip",
        "55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921",
        "50f3d5305a2d6a94a1543d7b5111654c7b154f4a9c1b71b59474c4deb36038ac",
    ),
    TrainingCell(
        2, "set_zero", "SET", "clip", 943201, "s1_entropy_b04_set_zero_s943201",
        "s1_action_law_b03_set_clip_s943201", "set_clip",
        "2621fc884d2d6a9ea909ee4f483b4df1c2d9d6f8767826ef730b952a360422e3",
        "8f19743fe8fd5a09aa998bf90ab73bdbc3de599a8f58b791610fbb628d2f97c2",
    ),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}


@dataclass(frozen=True)
class ControlBinding:
    """Exact completed B03 artifact identity used by one B04 cell."""

    path: Path
    sha256: str
    tag: str
    cell_key: str
    expected_initial_digest: str


def production_control_binding(cell: TrainingCell) -> ControlBinding:
    return ControlBinding(
        path=(REPOSITORY_ROOT / "runs" / DIRECTION / cell.control_tag / "summary.json"),
        sha256=cell.control_summary_sha256,
        tag=cell.control_tag,
        cell_key=cell.control_cell_key,
        expected_initial_digest=cell.expected_initial_digest,
    )


def map_training_actions(raw_actions: np.ndarray, law: str) -> np.ndarray:
    if law == "raw":
        return raw_actions.copy()
    if law == "clip":
        return np.clip(raw_actions, -1.0, 1.0)
    raise ValueError(f"unknown B04 action law {law!r}")


def make_b04_config(arm: str, envs: list[Any], seed: int, spec: FitSpec) -> Any:
    """Apply the sole treatment after the unchanged frozen config construction."""
    config = make_config(arm, envs, seed, spec)
    config.lambda_l = 0.0
    config.lambda_l_initial = 0.0
    config.lambda_l_final = 0.0
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    return config


def b04_config_dict(config: Any) -> dict[str, Any]:
    result = config_dict(config)
    result.update(
        lambda_l_initial=float(config.lambda_l_initial),
        lambda_l_final=float(config.lambda_l_final),
        use_entropy_annealing=bool(config.use_entropy_annealing),
        use_entropy_targets=bool(config.use_entropy_targets),
    )
    return result


def _read_control(
    binding: ControlBinding, cell: TrainingCell, record: dict[str, Any],
) -> dict[str, Any]:
    record.update(
        path=str(binding.path), expected_sha256=binding.sha256,
        expected_source_sha=CONTROL_SOURCE_SHA, expected_tag=binding.tag,
        expected_cell_key=binding.cell_key,
        expected_initial_parameter_normalizer_digest=binding.expected_initial_digest,
    )
    payload = binding.path.read_bytes()
    observed_sha = hashlib.sha256(payload).hexdigest()
    record["observed_sha256"] = observed_sha
    record["summary_bytes_match"] = observed_sha == binding.sha256
    if not record["summary_bytes_match"]:
        raise ValueError("B04 control summary SHA-256 mismatch")
    control = json.loads(payload)
    identity = {
        "status": control.get("status"),
        "object_id": control.get("object_id"),
        "launch_sha": control.get("launch_sha"),
        "tag": control.get("tag"),
        "arm": control.get("arm"),
        "training_action_law": control.get("training_action_law"),
        "seed": control.get("seed"),
        "cell_key": control.get("cell", {}).get("key"),
        "cell_tag": control.get("cell", {}).get("tag"),
    }
    expected = {
        "status": "complete", "object_id": "s1_action_law_b03",
        "launch_sha": CONTROL_SOURCE_SHA, "tag": binding.tag, "arm": cell.arm,
        "training_action_law": "clip", "seed": cell.seed,
        "cell_key": binding.cell_key, "cell_tag": binding.tag,
    }
    record["observed_identity"] = identity
    record["identity_match"] = identity == expected
    if not record["identity_match"]:
        raise ValueError("B04 control status/source/cell identity mismatch")
    observed_digest = control.get("observed_initial_parameter_normalizer_digest")
    record["control_initial_digest"] = observed_digest
    record["control_initial_digest_match"] = observed_digest == binding.expected_initial_digest
    if not record["control_initial_digest_match"]:
        raise ValueError("B04 control initial parameter/normalizer digest mismatch")
    return control


def _compare_control_config(
    candidate: dict[str, Any], control: dict[str, Any], record: dict[str, Any],
) -> None:
    old = control.get("config", {})
    differing = {
        key: {"control": old.get(key), "candidate": candidate.get(key)}
        for key in old
        if key != "lambda_l" and candidate.get(key) != old.get(key)
    }
    record["config_differences_excluding_treatment"] = differing
    record["control_lambda_l"] = old.get("lambda_l")
    record["candidate_lambda_l"] = candidate.get("lambda_l")
    if differing or old.get("lambda_l") != .05 or candidate.get("lambda_l") != 0.0:
        raise ValueError("B04 control/candidate config differs outside fixed treatment")


_INITIAL_PANEL_FIELDS = (
    "after_rollout", "training_team_steps", "test_n", "world_seeds",
    "execution_law", "status", "steps", "episodes", "J", "scalar_returns",
    "component_means", "optimizer_calls", "frozen_weights_and_normalizers",
    "executed_action_bounds",
)


def _initial_panel_evidence(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {key: row[key] for key in _INITIAL_PANEL_FIELDS}
        for row in summary.get("panels", []) if row.get("after_rollout") == 0
    ]


def _first_collection_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "training_scalar_returns": row["training_scalar_returns"],
        "action_motion_telemetry": row["action_motion_telemetry"],
    }


def _require_pre_update_control_match(
    summary: dict[str, Any], control: dict[str, Any], record: dict[str, Any],
) -> None:
    initial_match = _initial_panel_evidence(summary) == _initial_panel_evidence(control)
    active = summary["_active_training_rollout"]
    observed_first = {
        "training_scalar_returns": active["scalar_returns"],
        "action_motion_telemetry": active["action_motion_telemetry"],
    }
    expected_first = _first_collection_evidence(control["rollouts"][0])
    first_match = observed_first == expected_first
    record["initial_per_world_outputs_match"] = initial_match
    record["first_pre_update_collection_match"] = first_match
    record["pre_update_match"] = initial_match and first_match
    if not record["pre_update_match"]:
        raise ValueError("B04 initial evaluation or first pre-update collection mismatch")


def build_control_comparisons(
    summary: dict[str, Any], control: dict[str, Any], spec: FitSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    controls = {
        (int(row["after_rollout"]), int(row["test_n"])): row
        for row in control.get("panels", []) if row.get("status") == "complete"
    }
    comparisons = []
    for candidate in summary["panels"]:
        key = (int(candidate["after_rollout"]), int(candidate["test_n"]))
        old = controls.get(key)
        if candidate.get("status") != "complete" or old is None:
            raise ValueError(f"B04 missing complete matched control panel {key}")
        if candidate["world_seeds"] != old["world_seeds"]:
            raise ValueError(f"B04 candidate/control world mismatch at panel {key}")
        candidate_j = np.asarray(candidate["J"], dtype=np.float64)
        control_j = np.asarray(old["J"], dtype=np.float64)
        if candidate_j.shape != control_j.shape:
            raise ValueError(f"B04 candidate/control J width mismatch at panel {key}")
        components = {}
        for name in COMPONENTS:
            candidate_values = np.asarray(candidate["component_means"][name], dtype=np.float64)
            control_values = np.asarray(old["component_means"][name], dtype=np.float64)
            if candidate_values.shape != control_values.shape:
                raise ValueError(f"B04 candidate/control {name} width mismatch at panel {key}")
            delta = candidate_values - control_values
            components[name] = {
                "lambda0_per_world": candidate_values.tolist(),
                "lambda05_control_per_world": control_values.tolist(),
                "lambda0_minus_lambda05_per_world": delta.tolist(),
                "lambda0_minus_lambda05_mean": float(delta.mean()),
            }
        delta_j = candidate_j - control_j
        comparisons.append({
            "after_rollout": key[0], "test_n": key[1],
            "world_seeds": candidate["world_seeds"],
            "lambda0_J_per_world": candidate_j.tolist(),
            "lambda05_control_J_per_world": control_j.tolist(),
            "E_J_lambda0_minus_lambda05_per_world": delta_j.tolist(),
            "E_J_lambda0_minus_lambda05_mean": float(delta_j.mean()),
            "component_comparisons": components,
        })
    expected = len(spec.panels) * len(spec.test_ns)
    if len(comparisons) != expected:
        raise ValueError("B04 control comparison panel count incomplete")
    final_rollout = max(int(value) for value in spec.panels)
    final_rows = {
        int(row["test_n"]): row
        for row in comparisons if int(row["after_rollout"]) == final_rollout
    }
    if set(final_rows) != set(map(int, spec.test_ns)):
        raise ValueError("B04 final control comparison N panel incomplete")
    final = {
        "after_rollout": final_rollout,
        "by_test_n": {
            str(n): {
                "E_J_lambda0_minus_lambda05_mean": final_rows[n][
                    "E_J_lambda0_minus_lambda05_mean"
                ],
                "E_coverage_lambda0_minus_lambda05_mean": final_rows[n][
                    "component_comparisons"
                ]["coverage_reward"]["lambda0_minus_lambda05_mean"],
            }
            for n in sorted(final_rows)
        },
        "unseen_n4_n8_equal_weight_E_J": float(np.mean([
            final_rows[n]["E_J_lambda0_minus_lambda05_mean"] for n in (4, 8)
        ])) if 4 in final_rows and 8 in final_rows else None,
        "scope": "within-package lambda0 minus frozen lambda0.05 control; cross-package Q is external",
    }
    return jsonable(comparisons), jsonable(final)


def _rng_digest() -> str:
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(state[0].encode("ascii"))
    digest.update(state[1].tobytes())
    digest.update(repr(state[2:]).encode("ascii"))
    digest.update(torch.get_rng_state().cpu().numpy().tobytes())
    return digest.hexdigest()


_RUNTIME_FIELDS = (
    "env_timers", "env_team_skills", "env_agent_skills", "env_log_probs",
    "env_hidden_states", "env_prev_hidden_states", "env_reward_sums",
    "env_pending_high_level", "env_skill_ages", "env_skill_duration_remaining",
    "env_skill_duration_target", "actor_hidden_np", "critic_hidden_np",
    "prev_actor_hidden_np", "prev_critic_hidden_np", "_hidden_state_array_valid",
    "_central_snapshot_states", "_central_snapshot_obs", "_central_snapshot_valid",
)


def runtime_state_digest(agent: Any) -> str:
    digest = hashlib.sha256()
    for name in _RUNTIME_FIELDS:
        if hasattr(agent, name):
            digest.update(name.encode("utf-8"))
            digest.update(pickle.dumps(copy.deepcopy(getattr(agent, name)), protocol=5))
    buffer = getattr(agent, "rollout_buffer", None)
    if buffer is not None and hasattr(buffer, "get_sampler_rng_state"):
        digest.update(b"rollout_buffer.sampler_rng")
        digest.update(pickle.dumps(buffer.get_sampler_rng_state(), protocol=5))
    return digest.hexdigest()


def raw_sigma(agent: Any) -> list[float]:
    action_out = agent.skill_discoverer.actor.act.action_out
    if type(action_out).__name__ != "DiagGaussian":
        raise ValueError("B04 requires the unchanged raw DiagGaussian action distribution")
    bias = action_out.logstd._bias.detach().cpu().reshape(-1)
    return torch.exp(bias).tolist()


def raw_log_sigma(agent: Any) -> list[float]:
    action_out = agent.skill_discoverer.actor.act.action_out
    if type(action_out).__name__ != "DiagGaussian":
        raise ValueError("B04 requires the unchanged raw DiagGaussian action distribution")
    return action_out.logstd._bias.detach().cpu().reshape(-1).tolist()


def analytic_raw_entropy(log_sigma: list[float]) -> float:
    if len(log_sigma) != 3:
        raise ValueError("B04 requires three Gaussian action coordinates")
    return float(sum(log_sigma) + 1.5 * math.log(2.0 * math.pi * math.e))


def logstd_optimizer_contract(agent: Any) -> dict[str, Any]:
    parameter = agent.skill_discoverer.actor.act.action_out.logstd._bias
    optimizer_ids = {
        id(item)
        for group in agent.discoverer_actor_optimizer.param_groups
        for item in group["params"]
    }
    result = {
        "requires_grad": bool(parameter.requires_grad),
        "included_exactly_once": sum(
            id(item) == id(parameter)
            for group in agent.discoverer_actor_optimizer.param_groups
            for item in group["params"]
        ) == 1,
    }
    if not all(result.values()) or id(parameter) not in optimizer_ids:
        raise ValueError("B04 logstd must remain trainable in the actor optimizer")
    return result


def assert_agent_entropy_contract(agent: Any) -> dict[str, Any]:
    result = {
        "config_lambda_l": float(agent.config.lambda_l),
        "effective_lambda_l": float(agent.low_level_entropy_coef),
        "entropy_targets_enabled": bool(agent.use_entropy_targets),
        "entropy_annealing_enabled": bool(agent.use_entropy_annealing),
    }
    if result != {
        "config_lambda_l": 0.0,
        "effective_lambda_l": 0.0,
        "entropy_targets_enabled": False,
        "entropy_annealing_enabled": False,
    }:
        raise ValueError("B04 effective low-level entropy treatment changed")
    return result


def failure_entropy_snapshot(agent: Any) -> dict[str, Any]:
    """Return JSON-safe scale evidence even after a nonfinite optimizer failure."""
    try:
        tensor = agent.skill_discoverer.actor.act.action_out.logstd._bias.detach().cpu()
        flat = tensor.reshape(-1).to(dtype=torch.float64)
        finite_mask = torch.isfinite(flat)
        log_sigma = [float(value) if bool(ok) else None for value, ok in zip(flat, finite_mask)]
        sigma_tensor = torch.exp(flat)
        sigma_mask = torch.isfinite(sigma_tensor)
        sigma = [
            float(value) if bool(log_ok and sigma_ok) else None
            for value, log_ok, sigma_ok in zip(sigma_tensor, finite_mask, sigma_mask)
        ]
        valid = bool(finite_mask.all() and sigma_mask.all()) and len(log_sigma) == 3
        return {
            "valid": valid,
            "raw_sigma": sigma,
            "raw_log_sigma": log_sigma,
            "analytic_raw_entropy": (
                analytic_raw_entropy([float(value) for value in log_sigma])
                if valid else None
            ),
            "missing_reason": None if valid else "nonfinite_or_wrong_width_logstd_after_failure",
        }
    except Exception as exc:
        return {
            "valid": False, "raw_sigma": None, "raw_log_sigma": None,
            "analytic_raw_entropy": None,
            "missing_reason": f"{type(exc).__name__}: {exc}",
        }


def _new_motion() -> dict[str, Any]:
    return {
        "team_steps": 0, "raw_coordinate_violations": 0, "raw_uav_violations": 0,
        "raw_team_step_violations": 0, "raw_excess_sum": 0.0, "raw_excess_max": 0.0,
        "raw_attempted_l2_sum": 0.0, "executed_attempted_l2_sum": 0.0,
        "realized_l2_sum": 0.0, "boundary_truncated_coordinates": 0,
        "boundary_visited_coordinates": 0, "executed_min": float("inf"),
        "executed_max": float("-inf"), "diagnostic_rng_unchanged": True,
        "policy_output_unchanged": True, "old_logprob_unchanged": True,
        "position_storage_dtypes": [], "first_overrange_witness": None,
    }


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": int(numerator), "denominator": int(denominator),
            "rate": float(numerator / denominator) if denominator else None}


def _finish_motion(row: dict[str, Any], n: int) -> dict[str, Any]:
    coord = row["team_steps"] * n * 3
    uav = row["team_steps"] * n
    result = dict(row)
    result["raw_coordinate_violations"] = _rate(row["raw_coordinate_violations"], coord)
    result["raw_uav_violations"] = _rate(row["raw_uav_violations"], uav)
    result["raw_team_step_violations"] = _rate(
        row["raw_team_step_violations"], row["team_steps"]
    )
    result["boundary_truncated_coordinates"] = _rate(row["boundary_truncated_coordinates"], coord)
    result["boundary_visited_coordinates"] = _rate(row["boundary_visited_coordinates"], coord)
    result["raw_excess_mean_per_coordinate"] = row["raw_excess_sum"] / coord if coord else None
    result["raw_attempted_l2_mean_per_uav_step"] = row["raw_attempted_l2_sum"] / uav if uav else None
    result["executed_attempted_l2_mean_per_uav_step"] = (
        row["executed_attempted_l2_sum"] / uav if uav else None
    )
    result["realized_l2_mean_per_uav_step"] = row["realized_l2_sum"] / uav if uav else None
    if not row["team_steps"]:
        result["executed_min"] = result["executed_max"] = None
    return jsonable(result)


def _observe_motion(
    telemetry: dict[str, Any], native: Any, before: np.ndarray,
    raw_action: np.ndarray, executed_action: np.ndarray, after: np.ndarray,
    *, rollout: int, t: int, lane: int, reward: float, components: dict[str, float],
) -> None:
    violations = np.abs(raw_action) > 1.0
    excess = np.maximum(np.abs(raw_action) - 1.0, 0.0)
    raw_attempt = raw_action * native.max_speed * native.time_step
    executed_attempt = executed_action * native.max_speed * native.time_step
    unbounded = before + executed_attempt
    bounds_low = np.asarray([0.0, 0.0, native.height_range[0]], dtype=before.dtype)
    bounds_high = np.asarray(
        [native.area_size, native.area_size, native.height_range[1]], dtype=before.dtype
    )
    predicted = np.clip(unbounded, bounds_low, bounds_high)
    tolerance = 8 * np.finfo(before.dtype).eps * max(1.0, float(native.area_size))
    if not np.allclose(after, predicted, atol=tolerance, rtol=8 * np.finfo(before.dtype).eps):
        raise ValueError("native movement differs from B04 executed-action prediction")
    truncated = unbounded != predicted
    visited = np.isclose(after, bounds_low, atol=tolerance, rtol=0.0) | np.isclose(
        after, bounds_high, atol=tolerance, rtol=0.0
    )
    telemetry["team_steps"] += 1
    dtype_name = str(before.dtype)
    if dtype_name not in telemetry["position_storage_dtypes"]:
        telemetry["position_storage_dtypes"].append(dtype_name)
    telemetry["raw_coordinate_violations"] += int(violations.sum())
    telemetry["raw_uav_violations"] += int(violations.any(axis=1).sum())
    telemetry["raw_team_step_violations"] += int(violations.any())
    telemetry["raw_excess_sum"] += float(excess.sum())
    telemetry["raw_excess_max"] = max(telemetry["raw_excess_max"], float(excess.max()))
    telemetry["raw_attempted_l2_sum"] += float(np.linalg.norm(raw_attempt, axis=1).sum())
    telemetry["executed_attempted_l2_sum"] += float(np.linalg.norm(executed_attempt, axis=1).sum())
    telemetry["realized_l2_sum"] += float(np.linalg.norm(after - before, axis=1).sum())
    telemetry["boundary_truncated_coordinates"] += int(truncated.sum())
    telemetry["boundary_visited_coordinates"] += int(visited.sum())
    telemetry["executed_min"] = min(telemetry["executed_min"], float(executed_action.min()))
    telemetry["executed_max"] = max(telemetry["executed_max"], float(executed_action.max()))
    if violations.any() and telemetry["first_overrange_witness"] is None:
        telemetry["first_overrange_witness"] = {
            "rollout": rollout, "step_index_zero_based": t, "lane": lane,
            "raw_action": raw_action.tolist(), "executed_action": executed_action.tolist(),
            "position_before": before.tolist(), "position_after": after.tolist(),
            "predicted_position_after": predicted.tolist(), "reward": float(reward),
            "native_components": components,
        }


def _assert_config_contract(
    config: Any, cell: TrainingCell, *, expected_n: int = 6,
) -> None:
    if float(config.lambda_l) != 0.0:
        raise ValueError("B04 must retain low-level entropy coefficient zero")
    if bool(config.use_entropy_targets) or bool(config.use_entropy_annealing):
        raise ValueError("B04 entropy targets and annealing must remain disabled")
    if float(config.lambda_l_initial) != 0.0 or float(config.lambda_l_final) != 0.0:
        raise ValueError("B04 low-level entropy endpoints must remain zero")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B04 must retain the raw Gaussian action distribution")
    if int(config.k) != 10 or int(config.n_agents) != expected_n:
        raise ValueError(f"B04 requires N{expected_n} and k10 for this phase")
    if str(config.count_arm) != cell.arm:
        raise ValueError("B04 package/config mismatch")


def _panel_world_seed(rollout: int, n: int) -> int:
    return EVALUATION_SEED_BASE + rollout * 1000 + n * 100


def evaluate_panel(
    learner: Any, cell: TrainingCell, rollout: int, out: Path,
    summary: dict[str, Any], spec: FitSpec, publish: Callable[[str], None],
) -> None:
    learner_model_before = digest_agent(learner)
    learner_runtime_before = runtime_state_digest(learner)
    learner_rng_before = _rng_digest()
    with preserve_rng():
        for n in spec.test_ns:
            world_seed = _panel_world_seed(rollout, n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, hooks = None, []
            row = {
                "after_rollout": rollout,
                "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "execution_law": "clip",
                "status": "running", "steps": 0, "episodes": 0,
            }
            summary["panels"].append(row)
            publish(f"evaluation {rollout} N={n} starting")
            try:
                config = make_b04_config(cell.arm, envs, cell.seed, spec)
                _assert_config_contract(config, cell, expected_n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"r{rollout}_n{n}"))
                assert_agent_entropy_contract(target)
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                target_before = digest_agent(target)
                states, observations = reset_all(envs)
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                components = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                executed_min, executed_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        raw_actions, _, _data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        finite((raw_actions, _data), "B04 evaluation policy output")
                        raw_before = raw_actions.copy()
                        executed = map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("evaluation mapping mutated policy actions")
                        executed_min = min(executed_min, float(executed.min()))
                        executed_max = max(executed_max, float(executed.max()))
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                components[name][lane] += parts[name]
                            states[lane], observations[lane] = info["next_state"], obs
                            dones[lane] = done
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B04 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B04 evaluation missed fixed terminal boundary")
                j = n * returns / spec.horizon
                means = {name: value / spec.horizon for name, value in components.items()}
                if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6):
                    raise ValueError("B04 evaluation native J/component identity failed")
                if any(calls.values()) or digest_agent(target) != target_before:
                    raise ValueError("B04 evaluation modified target parameters/normalizers")
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means), optimizer_calls=calls.copy(),
                    frozen_weights_and_normalizers=True,
                    executed_action_bounds={"minimum": executed_min, "maximum": executed_max},
                    config=b04_config_dict(config),
                )
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                publish(f"evaluation {rollout} N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                raise
            finally:
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    if digest_agent(learner) != learner_model_before:
        raise ValueError("B04 evaluation modified learner parameters/normalizers")
    if runtime_state_digest(learner) != learner_runtime_before:
        raise ValueError("B04 evaluation modified learner runtime state")
    if _rng_digest() != learner_rng_before:
        raise ValueError("B04 evaluation modified learner/global RNG state")


def collect_rollout(
    agent: Any, envs: list[Any], states: np.ndarray, observations: np.ndarray,
    steps: np.ndarray, dones: np.ndarray, cell: TrainingCell, rollout: int,
    summary: dict[str, Any], spec: FitSpec,
    *, optimizer_calls_before: dict[str, int] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any], np.ndarray]:
    telemetry = _new_motion()
    returns = np.zeros(spec.train_lanes, dtype=np.float64)
    component_sums = {
        name: np.zeros(spec.train_lanes, dtype=np.float64) for name in COMPONENTS
    }
    decision_steps: set[int] = set()
    summary["_active_training_rollout"] = {
        "rollout": rollout,
        "phase": "collecting",
        "_telemetry": telemetry,
        "component_sums": component_sums,
        "scalar_returns": returns,
        "optimizer_calls_before_update": dict(optimizer_calls_before or {}),
    }
    for t in range(spec.horizon):
        raw_actions, _, data = agent.step(
            states, observations, steps, dones, deterministic=False,
            return_step_data=True, build_infos=False,
        )
        finite((raw_actions, data), "B04 training policy output")
        raw_before = raw_actions.copy()
        logprob_before = np.asarray(data["action_logprobs"]).copy()
        rng_before = _rng_digest()
        executed = map_training_actions(raw_actions, cell.law)
        telemetry["diagnostic_rng_unchanged"] &= rng_before == _rng_digest()
        telemetry["policy_output_unchanged"] &= np.array_equal(raw_actions, raw_before)
        telemetry["old_logprob_unchanged"] &= np.array_equal(
            np.asarray(data["action_logprobs"]), logprob_before
        )
        if np.asarray(data["skill_changed"]).any():
            decision_steps.add(t)
        next_states, next_observations = [], []
        rewards = np.zeros(spec.train_lanes, dtype=np.float64)
        next_dones = np.zeros(spec.train_lanes, dtype=bool)
        for lane, env in enumerate(envs):
            native = env.env.env
            before = np.asarray(native.uav_positions).copy()
            obs, reward, term, trunc, info = env.step(executed[lane])
            after = np.asarray(native.uav_positions).copy()
            done = bool(term or trunc)
            rewards[lane] = reward
            next_dones[lane] = done
            returns[lane] += reward
            summary["counts"]["training_team_steps"] += 1
            summary["counts"]["training_episodes"] += int(done)
            parts = native_components(info, reward, spec.train_n)
            for name in COMPONENTS:
                component_sums[name][lane] += parts[name]
            _observe_motion(
                telemetry, native, before, raw_actions[lane], executed[lane], after,
                rollout=rollout, t=t, lane=lane, reward=reward, components=parts,
            )
            next_states.append(info["next_state"])
            next_observations.append(obs)
            if training_step_hook is not None:
                training_step_hook({"rollout": rollout, "t": t, "lane": lane,
                                    "summary": summary, "telemetry": telemetry})
        next_states = np.stack(next_states)
        next_observations = np.stack(next_observations)
        agent.store_transition_batch(
            states=states, next_states=next_states.copy(), observations=observations,
            next_observations=next_observations.copy(), actions=raw_actions, rewards=rewards,
            dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data,
        )
        summary["counts"]["stored_team_steps"] += spec.train_lanes
        if not np.array_equal(agent.rollout_buffer.actions[t], raw_actions):
            raise ValueError("B04 buffer did not retain raw sampled actions")
        if not np.array_equal(agent.rollout_buffer.log_probs[t], logprob_before):
            raise ValueError("B04 buffer did not retain original old log-probabilities")
        witness = telemetry["first_overrange_witness"]
        if witness is not None and witness["step_index_zero_based"] == t:
            lane = int(witness["lane"])
            witness.update(
                transition_indexing=(
                    "action[t] and old_logprob[t] map state/position[t] to "
                    "state/position[t+1]; indices are zero-based"
                ),
                old_logprob=logprob_before[lane].tolist(),
                stored_raw_action=agent.rollout_buffer.actions[t, lane].tolist(),
                stored_old_logprob=agent.rollout_buffer.log_probs[t, lane].tolist(),
                stored_action_exact=bool(np.array_equal(
                    agent.rollout_buffer.actions[t, lane], raw_before[lane]
                )),
                stored_old_logprob_exact=bool(np.array_equal(
                    agent.rollout_buffer.log_probs[t, lane], logprob_before[lane]
                )),
            )
        for lane, env in enumerate(envs):
            if next_dones[lane]:
                obs, info = env.reset()
                next_states[lane], next_observations[lane] = info["state"], obs
                agent.reset_env_state(lane)
                steps[lane] = 0
                summary["counts"]["terminal_resets"] += 1
            else:
                steps[lane] += 1
        states, observations, dones = next_states, next_observations, next_dones
        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
            raise ValueError("unexpected B04 training terminal boundary")
    if not dones.all():
        raise ValueError("B04 training rollout missed full episodes")
    telemetry["decision_step_indices_zero_based"] = sorted(decision_steps)
    telemetry["native_component_means_per_world"] = {
        name: (values / spec.horizon).tolist() for name, values in component_sums.items()
    }
    if not all((telemetry["diagnostic_rng_unchanged"], telemetry["policy_output_unchanged"],
                telemetry["old_logprob_unchanged"])):
        raise ValueError("B04 mapping/diagnostics mutated policy data or consumed RNG")
    if cell.law == "clip" and (telemetry["executed_min"] < -1.0 or telemetry["executed_max"] > 1.0):
        raise ValueError("B04 clipped training law exceeded declared action bounds")
    finished = _finish_motion(telemetry, spec.train_n)
    summary["_active_training_rollout"] = {
        "rollout": rollout,
        "phase": "collected",
        "action_motion_telemetry": finished,
        "native_component_sums": jsonable(component_sums),
        "scalar_returns": returns.tolist(),
    }
    return states, observations, steps, dones, finished, returns


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec = DEFAULT_SPEC,
    *, command_start: float | None = None,
    control_binding: ControlBinding | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != cell.tag:
        raise ValueError(f"B04 output basename must be fixed tag {cell.tag}")
    if (out / "summary.json").exists():
        raise ValueError("existing B04 scientific summary; reconcile original attempt")
    if 0 not in spec.panels:
        raise ValueError("B04 requires the initial evaluation panel for control binding")
    if control_binding is None:
        control_binding = production_control_binding(cell)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if command_start is None:
        command_start = started
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": cell.arm, "training_action_law": cell.law,
        "seed": cell.seed, "tag": cell.tag, "launch_sha": launch_sha, "admission": admission,
        "status": "initializing", "fit_started": False, "failure": None,
        "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [], "rollouts": [],
        "control_comparisons": [],
        "expected_initial_parameter_normalizer_digest": control_binding.expected_initial_digest,
        "control_binding": {},
        "counts": {"training_team_steps": 0, "stored_team_steps": 0,
                   "training_episodes": 0, "terminal_resets": 0, "updates": 0,
                   "evaluation_team_steps": 0, "evaluation_episodes": 0},
        "evaluation_action_law": "clip",
        "transition_indexing": (
            "action[t] and old_logprob[t] map state/position[t] to "
            "state/position[t+1]; indices are zero-based"
        ),
        "evaluation_seed_base": EVALUATION_SEED_BASE,
        "reward_units": {"training": "native R / train_N=6",
                         "J": "test_N * scalar_return / horizon"},
        "entropy_measurement": {
            "analytic_raw_gaussian": "sum(log_sigma)+1.5*log(2*pi*e)",
            "aligned_exposure": "rollout r uses before-update value; after45 is final policy",
            "legacy_action_entropy_at_lambda0_is_measurement": False,
        },
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                    "thread_environment": {name: os.environ.get(name) for name in
                        ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}},
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    envs, agent, hooks, calls, control = [], None, [], {}, None
    try:
        control = _read_control(control_binding, cell, summary["control_binding"])
        torch.set_num_threads(spec.torch_threads)
        seed_rng(cell.seed)
        envs = make_envs(spec.train_lanes, cell.seed, spec.train_n, spec.horizon)
        config = make_b04_config(cell.arm, envs, cell.seed, spec)
        _assert_config_contract(config, cell)
        summary["config"] = b04_config_dict(config)
        _compare_control_config(summary["config"], control, summary["control_binding"])
        summary["action_distribution"] = {
            "kind": str(getattr(config, "continuous_action_distribution", "gaussian")),
            "lambda_l": float(config.lambda_l),
            "entropy_targets_enabled": bool(config.use_entropy_targets),
            "entropy_annealing_enabled": bool(config.use_entropy_annealing),
            "mapping_is_environment_only": True,
        }
        write_json(out / "config.json", {"launch_sha": launch_sha, "cell": vars(cell),
                                         "spec": vars(spec), "config": summary["config"]})
        agent = build_agent(config, str(out / "learner_logs"))
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["effective_entropy_contract"] = assert_agent_entropy_contract(agent)
        summary["logstd_optimizer_contract"] = logstd_optimizer_contract(agent)
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        observed_initial = digest_agent(agent)
        summary["observed_initial_parameter_normalizer_digest"] = observed_initial
        summary["initial_digest_matches_expected"] = (
            observed_initial == control_binding.expected_initial_digest
        )
        if not summary["initial_digest_matches_expected"]:
            raise ValueError("B04 initial parameter/normalizer digest mismatch")
        summary["initial_raw_sigma"] = raw_sigma(agent)
        summary["initial_raw_log_sigma"] = raw_log_sigma(agent)
        summary["initial_analytic_raw_entropy"] = analytic_raw_entropy(
            summary["initial_raw_log_sigma"]
        )
        agent.train(True)
        if 0 in spec.panels:
            summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
            evaluate_panel(agent, cell, 0, out, summary, spec, publish)
        states, observations = reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        publish("training starts")
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = calls.copy()
            sigma_before = raw_sigma(agent)
            states, observations, steps, dones, motion, returns = collect_rollout(
                agent, envs, states, observations, steps, dones, cell, rollout, summary, spec,
                optimizer_calls_before=optimizer_before,
                training_step_hook=training_step_hook,
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating",
                raw_sigma_before_update=sigma_before,
                raw_log_sigma_before_update=raw_log_sigma(agent),
                optimizer_calls_before_update=optimizer_before,
            )
            if rollout == 1:
                _require_pre_update_control_match(
                    summary, control, summary["control_binding"]
                )
                publish("control matched before first update")
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon, last_state=states.copy(),
                last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B04 training losses")
            _assert_config_contract(agent.config, cell)
            assert_agent_entropy_contract(agent)
            motion_parameters = parameter_motion(agent, initial_parameters)
            log_sigma_after = raw_log_sigma(agent)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: calls[name] - optimizer_before[name] for name in calls},
                "optimizer_total": calls.copy(), "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before, "raw_sigma_after_update": raw_sigma(agent),
                "raw_log_sigma_before_update": summary["_active_training_rollout"][
                    "raw_log_sigma_before_update"
                ],
                "raw_log_sigma_after_update": log_sigma_after,
                "analytic_raw_entropy_before_update": analytic_raw_entropy(
                    summary["_active_training_rollout"]["raw_log_sigma_before_update"]
                ),
                "analytic_raw_entropy_after_update": analytic_raw_entropy(log_sigma_after),
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["rollouts"].append(row)
            summary["parameter_motion"] = motion_parameters
            agent.clear_buffers()
            summary.pop("_active_training_rollout", None)
            publish(f"rollout {rollout} updated")
            if rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_panel(agent, cell, rollout, out, summary, spec, publish)
        expected_training = spec.rollouts * spec.train_lanes * spec.horizon
        expected_eval = len(spec.panels) * len(spec.test_ns) * spec.eval_lanes * spec.horizon
        if summary["counts"]["training_team_steps"] != expected_training:
            raise ValueError("B04 training exposure incomplete")
        if summary["counts"]["stored_team_steps"] != expected_training:
            raise ValueError("B04 stored exposure incomplete")
        if summary["counts"]["evaluation_team_steps"] != expected_eval:
            raise ValueError("B04 evaluation exposure incomplete")
        required = ("discoverer_actor", "discoverer_critic") + (
            ("coordinator", "team_discriminator", "individual_discriminator")
            if cell.arm == "H6" else ()
        )
        for name in required:
            if calls[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required B04 learner module did not update: {name}")
        if cell.arm == "SET" and any(
            calls[name] for name in ("coordinator", "team_discriminator", "individual_discriminator")
        ):
            raise ValueError("SET unexpectedly updated disabled skill modules")
        summary["control_comparisons"], summary["final_control_comparison"] = (
            build_control_comparisons(summary, control, spec)
        )
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = raw_sigma(agent)
        summary["final_raw_log_sigma"] = raw_log_sigma(agent)
        summary["final_analytic_raw_entropy"] = analytic_raw_entropy(
            summary["final_raw_log_sigma"]
        )
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = _finish_motion(
                    telemetry, spec.train_n
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = calls.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0)) for name, count in calls.items()
            }
            if agent is not None:
                active["entropy_observed_after_failure"] = failure_entropy_snapshot(agent)
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_fit_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
