"""Train one fixed ordinary SET B11 cell and evaluate its final policy at N8 then N6."""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, FitSpec, config_dict, make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, NORMALIZERS, OPTIMIZERS, capture_parameters, digest_agent, finite,
    jsonable, model_modules, native_components, optimizer_counts, parameter_motion,
    preserve_rng, save_checkpoint, seed_rng, write_json,
)


OBJECT_ID = "s1_training_condition_b11"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SEED = 963201
TRAINING_ENV_SEED_BASE = 964201
EVALUATION_WORLD_BASE = 1_645_000
FINAL_ROLLOUT = 45
EVALUATION_ORDER = (8, 6)


@dataclass(frozen=True)
class TrainingCell:
    key: str
    train_n: int
    tag: str
    arm: str = "SET"
    law: str = "clip"
    seed: int = SEED
    lambda_l: float = .05


CELLS = (
    TrainingCell("t6", 6, "s1_training_condition_b11_t6_s963201"),
    TrainingCell("t8", 8, "s1_training_condition_b11_t8_s963201"),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}
B11_BASE_SPEC = replace(
    DEFAULT_SPEC, test_ns=EVALUATION_ORDER, eval_lanes=32, panels=(FINAL_ROLLOUT,),
)


def spec_for(cell: TrainingCell, base: FitSpec = B11_BASE_SPEC) -> FitSpec:
    return replace(base, train_n=cell.train_n, test_ns=EVALUATION_ORDER, panels=(base.rollouts,))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _config_record(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def _assert_config(config: Any, cell: TrainingCell, expected_n: int) -> None:
    if str(config.count_arm) != "SET" or cell.arm != "SET" or cell.law != "clip":
        raise ValueError("B11 requires ordinary SET with bounded physical execution")
    if int(config.n_agents) != expected_n or int(config.n_uavs) != expected_n:
        raise ValueError(f"B11 config has wrong physical roster for N={expected_n}")
    if int(config.k) != 10 or bool(config.use_central_snapshot_in_flat_actor) is not True:
        raise ValueError("B11 SET information route or k10 clock changed")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B11 requires the native Gaussian action distribution")
    if any(float(value) != .05 for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )) or bool(config.use_entropy_annealing) or bool(config.use_entropy_targets):
        raise ValueError("B11 fixed .05 entropy endpoints/flags changed")


def make_b11_config(
    cell: TrainingCell, envs: list[Any], spec: FitSpec, *, expected_n: int | None = None,
) -> Any:
    config = make_config("SET", envs, cell.seed, spec)
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = cell.lambda_l
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    _assert_config(config, cell, spec.train_n if expected_n is None else expected_n)
    return config


def _assert_agent_entropy(agent: Any, cell: TrainingCell) -> dict[str, Any]:
    observed = {
        "config_lambda_l": float(agent.config.lambda_l),
        "effective_lambda_l": float(agent.low_level_entropy_coef),
        "lambda_l_initial": float(agent.config.lambda_l_initial),
        "lambda_l_final": float(agent.config.lambda_l_final),
        "entropy_targets_enabled": bool(agent.use_entropy_targets),
        "entropy_annealing_enabled": bool(agent.use_entropy_annealing),
    }
    expected = {
        "config_lambda_l": cell.lambda_l, "effective_lambda_l": cell.lambda_l,
        "lambda_l_initial": cell.lambda_l, "lambda_l_final": cell.lambda_l,
        "entropy_targets_enabled": False, "entropy_annealing_enabled": False,
    }
    if observed != expected:
        raise ValueError("B11 effective learner entropy treatment changed")
    return observed


def _assert_native_envs(envs: list[Any], expected_n: int) -> None:
    for env in envs:
        native = env.env.env
        if int(native.n_uavs) != expected_n or int(native.n_users) != 50:
            raise ValueError("B11 native environment roster changed")
        if int(native.max_connections) != 10 or float(native.min_sinr) != 0.0:
            raise ValueError("B11 native c10/SINR threshold contract changed")


def _canonical_config(actual: Any) -> Any:
    config = copy.deepcopy(actual)
    config.n_agents = config.n_uavs = 6
    config.calculate_and_set_buffer_sizes()
    config.discriminator_batch_size = config.batch_size
    config.validate_config()
    _assert_config(config, CELL_BY_KEY["t6"], 6)
    return config


def _normalizer_manifest(agent: Any) -> dict[str, Any]:
    return {
        name: jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None else None
        for name in NORMALIZERS
    }


def _tensor_manifest(agent: Any) -> dict[str, Any]:
    result = {}
    for module_name, module in model_modules(agent).items():
        for name, tensor in module.state_dict().items():
            value = tensor.detach().cpu().contiguous()
            raw = value.numpy()
            result[f"{module_name}.{name}"] = {
                "shape": list(raw.shape), "dtype": str(raw.dtype),
                "sha256": hashlib.sha256(raw.tobytes()).hexdigest(),
            }
    return result


def _optimizer_ownership(agent: Any, forbidden_ids: set[int]) -> dict[str, Any]:
    rows = {}
    for name in OPTIMIZERS:
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is None:
            rows[name] = None
            continue
        actual = [id(parameter) for group in optimizer.param_groups for parameter in group["params"]]
        expected_module = {
            "coordinator": agent.skill_coordinator,
            "discoverer_actor": agent.skill_discoverer.actor,
            "discoverer_critic": agent.skill_discoverer.critic,
            "team_discriminator": getattr(agent, "team_discriminator", None),
            "individual_discriminator": getattr(agent, "individual_discriminator", None),
        }[name]
        expected = [] if expected_module is None else [
            id(parameter) for parameter in expected_module.parameters() if parameter.requires_grad
        ]
        exact = len(actual) == len(set(actual)) and set(actual) == set(expected)
        no_forbidden = not bool(set(actual) & forbidden_ids)
        empty = len(optimizer.state) == 0
        rows[name] = {
            "parameter_count": len(actual), "target_parameters_exactly_once": exact,
            "no_canonical_parameters": no_forbidden, "state_is_empty": empty,
        }
        if not exact or not no_forbidden or not empty:
            raise ValueError(f"B11 target-owned fresh optimizer invariant failed: {name}")
    return rows


def _buffer_initial_record(agent: Any) -> dict[str, Any]:
    buffer = agent.rollout_buffer
    record = {
        "num_steps": int(buffer.num_steps), "num_envs": int(buffer.num_envs),
        "n_agents": int(buffer.n_agents),
        "env_lengths": np.asarray(buffer.env_lengths).tolist(),
        "last_t_per_env": np.asarray(buffer.last_t_per_env).tolist(),
        "sampler_seed": int(agent.rollout_sampler_seed),
        "sampler_state": jsonable(buffer.get_sampler_rng_state()),
    }
    if any(record["env_lengths"]) or any(value != -1 for value in record["last_t_per_env"]):
        raise ValueError("B11 target rollout buffer is not fresh")
    return record


def construct_common_initialized_agent(
    actual_config: Any, log_root: Path,
    *, build_fn: Callable[[Any, str], Any] = build_agent,
) -> tuple[Any, dict[str, Any]]:
    """Build canonical N6, then a true-N target without advancing canonical post-init RNG."""
    canonical_config = _canonical_config(actual_config)
    canonical = build_fn(canonical_config, str(Path(log_root) / "canonical_n6"))
    canonical_manifest = _tensor_manifest(canonical)
    canonical_normalizers = _normalizer_manifest(canonical)
    canonical_digest = digest_agent(canonical)
    canonical_parameter_ids = {
        id(parameter) for module in model_modules(canonical).values() for parameter in module.parameters()
    }
    canonical_post_rng = b03._rng_digest()
    target = None
    with preserve_rng():
        target = build_fn(actual_config, str(Path(log_root) / f"target_n{actual_config.n_agents}"))
        strict_sync(target, canonical)
    if b03._rng_digest() != canonical_post_rng:
        raise ValueError("B11 target construction changed canonical post-init RNG stream")
    target.train(True)
    if _tensor_manifest(target) != canonical_manifest:
        raise ValueError("B11 synchronized target tensors differ from canonical N6 tensors")
    if _normalizer_manifest(target) != canonical_normalizers or digest_agent(target) != canonical_digest:
        raise ValueError("B11 synchronized target normalizers/digest differ from canonical N6")
    ownership = _optimizer_ownership(target, canonical_parameter_ids)
    buffer_record = _buffer_initial_record(target)
    sampler_reference = jsonable(canonical.rollout_buffer.get_sampler_rng_state())
    if buffer_record["sampler_state"] != sampler_reference:
        raise ValueError("B11 true-N target sampler state differs from canonical seeded sampler")
    runtime = b03.runtime_state_digest(target)
    evidence = {
        "canonical_n": 6, "target_n": int(actual_config.n_agents),
        "canonical_post_initialization_rng_digest": canonical_post_rng,
        "returned_rng_digest": b03._rng_digest(),
        "parameter_normalizer_digest": canonical_digest,
        "tensor_manifest": canonical_manifest,
        "normalizers": canonical_normalizers,
        "target_optimizer_ownership": ownership,
        "target_initial_buffer": buffer_record,
        "target_fresh_runtime_digest": runtime,
        "canonical_config": _config_record(canonical_config),
        "actual_config": _config_record(actual_config),
    }
    del canonical
    return target, evidence


def _panel_world_seed(n: int) -> int:
    if n not in EVALUATION_ORDER:
        raise ValueError(f"B11 has no evaluation panel at N={n}")
    return EVALUATION_WORLD_BASE + 100 * n


def _trace_path(out: Path, n: int) -> Path:
    return out / f"trace_45_n{n}.npz"


def _write_trace(path: Path, arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    checked, schema = {}, {}
    for name, value in arrays.items():
        array = np.asarray(value)
        if array.dtype == object or (
            np.issubdtype(array.dtype, np.floating) and not np.isfinite(array).all()
        ):
            raise ValueError(f"B11 trace {name} is nonnumeric/nonfinite")
        checked[name] = array
        schema[name] = {"shape": list(array.shape), "dtype": str(array.dtype)}
    partial = path.with_suffix(".npz.partial")
    with partial.open("wb") as stream:
        np.savez(stream, **checked)
    partial.replace(path)
    return {
        "path": str(path), "native_relative_path": path.name,
        "sha256": file_sha256(path), "bytes": path.stat().st_size,
        "format": "NumPy npz with allow_pickle=False", "arrays": schema,
    }


def _new_trace(spec: FitSpec, n: int) -> dict[str, np.ndarray]:
    base = (spec.horizon, spec.eval_lanes)
    return {
        "scalar_reward": np.zeros(base, dtype=np.float64),
        **{name: np.zeros(base, dtype=np.float64) for name in COMPONENTS},
        "eligible_links": np.zeros((*base, n, 50), dtype=bool),
        "connections": np.zeros((*base, n, 50), dtype=bool),
        "per_uav_eligible_counts": np.zeros((*base, n), dtype=np.int16),
        "per_uav_connection_counts": np.zeros((*base, n), dtype=np.int16),
        "eligible_user_counts": np.zeros(base, dtype=np.int16),
        "served_user_counts": np.zeros(base, dtype=np.int16),
        "eligible_unserved_user_counts": np.zeros(base, dtype=np.int16),
        "connected_quality_sum": np.zeros(base, dtype=np.float64),
        "uav_heights": np.zeros((*base, n), dtype=np.float64),
    }


def _observe_post_transition(
    trace: dict[str, np.ndarray], t: int, lane: int, env: Any,
    scalar: float, parts: dict[str, float], n: int,
) -> None:
    native = env.env.env
    sinr = np.asarray(native.sinr_matrix, dtype=np.float64)
    connections = np.asarray(native.connections, dtype=bool)
    if sinr.shape != (n, 50) or connections.shape != (n, 50):
        raise ValueError("B11 native SINR/connection matrix shape mismatch")
    eligible = sinr >= float(native.min_sinr)
    if np.any(connections & ~eligible):
        raise ValueError("B11 native connection is below the actual threshold")
    if np.any(connections.sum(axis=0) > 1) or np.any(connections.sum(axis=1) > 10):
        raise ValueError("B11 unique-user or c10 capacity invariant failed")
    eligible_users = eligible.any(axis=0)
    served_users = connections.any(axis=0)
    quality_sum = float(np.clip(
        (sinr[connections] - float(native.min_sinr)) / 30.0, 0.0, 1.0,
    ).sum())
    served = int(served_users.sum())
    heights = np.asarray(native.uav_positions, dtype=np.float64)[:, 2]
    height_penalty = (
        (float(heights.mean()) - float(native.height_range[0]))
        / (float(native.height_range[1]) - float(native.height_range[0])) * .1
    )
    checks = {
        "coverage_reward": served / 50.0,
        "quality_reward": quality_sum / max(served, 1),
        "energy_penalty": height_penalty,
    }
    if any(not np.isclose(parts[key], value, atol=1e-10, rtol=0.0) for key, value in checks.items()):
        raise ValueError("B11 service/quality/height trace differs from native components")
    trace["scalar_reward"][t, lane] = scalar
    for name in COMPONENTS:
        trace[name][t, lane] = parts[name]
    trace["eligible_links"][t, lane] = eligible
    trace["connections"][t, lane] = connections
    trace["per_uav_eligible_counts"][t, lane] = eligible.sum(axis=1)
    trace["per_uav_connection_counts"][t, lane] = connections.sum(axis=1)
    trace["eligible_user_counts"][t, lane] = int(eligible_users.sum())
    trace["served_user_counts"][t, lane] = served
    trace["eligible_unserved_user_counts"][t, lane] = int((eligible_users & ~served_users).sum())
    trace["connected_quality_sum"][t, lane] = quality_sum
    trace["uav_heights"][t, lane] = heights


def evaluate_final(
    learner: Any, cell: TrainingCell, out: Path, summary: dict[str, Any], spec: FitSpec,
    publish: Callable[[str], None],
) -> None:
    learner_model_before = digest_agent(learner)
    learner_runtime_before = b03.runtime_state_digest(learner)
    learner_rng_before = b03._rng_digest()
    with preserve_rng():
        for n in EVALUATION_ORDER:
            world_seed = _panel_world_seed(n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            _assert_native_envs(envs, n)
            target, hooks = None, []
            calls = {name: 0 for name in OPTIMIZERS}
            storage_calls = 0
            optimizer_counts_reported = False
            row = {
                "after_rollout": spec.rollouts,
                "training_team_steps": spec.rollouts * spec.train_lanes * spec.horizon,
                "test_n": n, "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "execution_law": "clip", "status": "running", "steps": 0,
                "episodes": 0, "resets": 0, "policy_step_calls": 0,
                "training_storage_calls": 0,
            }
            summary["panels"].append(row)
            publish(f"final evaluation N={n} starting")
            try:
                config = make_b11_config(cell, envs, replace(spec, train_n=n), expected_n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"n{n}"))
                strict_sync(target, learner)
                target.train(False)
                target_entropy = _assert_agent_entropy(target, cell)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != learner_model_before:
                    raise ValueError("B11 evaluation target did not exactly load current learner")
                normals_before = _normalizer_manifest(target)
                runtime_before = b03.runtime_state_digest(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("B11 evaluation attempted training storage")

                target.store_transition_batch = MethodType(reject_store, target)
                pairs = []
                for lane, env in enumerate(envs):
                    target.reset_env_state(lane)
                    pairs.append(env.reset())
                    row["resets"] += 1
                    summary["counts"]["evaluation_resets"] += 1
                states = np.stack([info["state"] for observation, info in pairs])
                observations = np.stack([observation for observation, info in pairs])
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                component_sums = {
                    name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS
                }
                trace = _new_trace(spec, n)
                trace["initial_states"] = states.copy()
                trace["initial_observations"] = observations.copy()
                executed_min, executed_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        raw_actions, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        row["policy_step_calls"] += 1
                        summary["counts"]["evaluation_policy_step_calls"] += 1
                        finite((raw_actions, data), "B11 evaluation policy output")
                        raw_before = raw_actions.copy()
                        executed = b03.map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("B11 evaluation clip mutated raw policy output")
                        executed_min = min(executed_min, float(executed.min()))
                        executed_max = max(executed_max, float(executed.max()))
                        next_states, next_observations = [], []
                        for lane, env in enumerate(envs):
                            observation, reward, terminated, truncated, info = env.step(executed[lane])
                            done = bool(terminated or truncated)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_uav_steps"] += n
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                component_sums[name][lane] += parts[name]
                            _observe_post_transition(trace, t, lane, env, reward, parts, n)
                            next_states.append(info["next_state"])
                            next_observations.append(observation)
                            dones[lane] = done
                        states, observations = np.stack(next_states), np.stack(next_observations)
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B11 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B11 evaluation missed fixed terminal boundary")
                means = {name: values / spec.horizon for name, values in component_sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
                if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6) or not np.allclose(
                    j, native_j, atol=1e-7, rtol=1e-6,
                ):
                    raise ValueError("B11 final native J/component identity failed")
                if any(calls.values()) or storage_calls or digest_agent(target) != before:
                    raise ValueError("B11 evaluation optimized, stored, or changed target parameters")
                if _normalizer_manifest(target) != normals_before:
                    raise ValueError("B11 evaluation changed target normalizers")
                if np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B11 evaluation populated training rollout storage")
                trace_identity = _write_trace(_trace_path(out, n), trace)
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means),
                    eligibility_service={
                        "eligible_users_per_step": trace["eligible_user_counts"].mean(axis=0).tolist(),
                        "served_users_per_step": trace["served_user_counts"].mean(axis=0).tolist(),
                        "eligible_unserved_users_per_step": trace[
                            "eligible_unserved_user_counts"
                        ].mean(axis=0).tolist(),
                        "per_uav_eligible_per_step": trace[
                            "per_uav_eligible_counts"
                        ].mean(axis=0).tolist(),
                        "per_uav_connections_per_step": trace[
                            "per_uav_connection_counts"
                        ].mean(axis=0).tolist(),
                    },
                    optimizer_calls=calls.copy(), training_storage_calls=storage_calls,
                    frozen_weights_and_normalizers=True,
                    parameter_normalizer_digest_before=before,
                    parameter_normalizer_digest_after=digest_agent(target),
                    normalizers_before=normals_before,
                    normalizers_after=_normalizer_manifest(target),
                    runtime_digest_before=runtime_before,
                    runtime_digest_after=b03.runtime_state_digest(target),
                    runtime_evolved=runtime_before != b03.runtime_state_digest(target),
                    executed_action_bounds={"minimum": executed_min, "maximum": executed_max},
                    trace=trace_identity, config=_config_record(config),
                    effective_entropy_contract=target_entropy,
                    post_transition_semantics=True,
                    actual_sinr_threshold=float(envs[0].env.env.min_sinr),
                    max_connections_per_uav=int(envs[0].env.env.max_connections),
                    height_range=[float(value) for value in envs[0].env.env.height_range],
                    n_users=int(envs[0].env.env.n_users),
                )
                summary["counts"]["panels"] += 1
                write_json(out / f"panel_45_n{n}.json", row)
                publish(f"final evaluation N={n} complete")
                target.store_transition_batch = original_store
            except Exception as exc:
                row["optimizer_calls"] = calls.copy()
                row["training_storage_calls"] = storage_calls
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_45_n{n}.json", row)
                raise
            finally:
                if not optimizer_counts_reported:
                    summary["counts"]["evaluation_optimizer_calls"] += sum(calls.values())
                    optimizer_counts_reported = True
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    learner_model_after = digest_agent(learner)
    learner_runtime_after = b03.runtime_state_digest(learner)
    learner_rng_after = b03._rng_digest()
    preservation = {
        "parameter_normalizer_digest_before": learner_model_before,
        "parameter_normalizer_digest_after": learner_model_after,
        "runtime_digest_before": learner_runtime_before,
        "runtime_digest_after": learner_runtime_after,
        "global_rng_digest_before": learner_rng_before,
        "global_rng_digest_after": learner_rng_after,
        "model_preserved": learner_model_before == learner_model_after,
        "runtime_preserved": learner_runtime_before == learner_runtime_after,
        "global_rng_preserved": learner_rng_before == learner_rng_after,
    }
    summary["final_evaluation_learner_isolation"] = preservation
    if not all(preservation[key] for key in (
        "model_preserved", "runtime_preserved", "global_rng_preserved",
    )):
        raise ValueError("B11 evaluation changed learner model/runtime/global RNG")


class _CountingAgent:
    def __init__(self, agent: Any, counts: dict[str, int], summary: dict[str, Any]):
        self._agent, self._counts, self._summary = agent, counts, summary
        self.optimizer_before: dict[str, int] = {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def step(self, *args: Any, **kwargs: Any) -> Any:
        active = self._summary.get("_active_training_rollout")
        if active is not None:
            active.setdefault("optimizer_calls_before_update", self.optimizer_before.copy())
        result = self._agent.step(*args, **kwargs)
        self._counts["training_policy_step_calls"] += 1
        return result


def _expected_counts(spec: FitSpec) -> dict[str, int]:
    training = spec.rollouts * spec.train_lanes * spec.horizon
    evaluation = len(EVALUATION_ORDER) * spec.eval_lanes * spec.horizon
    return {
        "fits": 1, "training_team_steps": training,
        "stored_team_steps": training, "training_agent_rows": training * spec.train_n,
        "training_episodes": spec.rollouts * spec.train_lanes,
        "terminal_resets": spec.rollouts * spec.train_lanes,
        "updates": spec.rollouts,
        "training_policy_step_calls": spec.rollouts * spec.horizon,
        "panels": len(EVALUATION_ORDER), "evaluation_team_steps": evaluation,
        "evaluation_uav_steps": spec.eval_lanes * spec.horizon * sum(EVALUATION_ORDER),
        "evaluation_episodes": len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_resets": len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_policy_step_calls": len(EVALUATION_ORDER) * spec.horizon,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _expected_production_optimizer_calls(cell: TrainingCell) -> dict[str, int]:
    low = 101_250 if cell.train_n == 6 else 135_000
    return {
        "coordinator": 0, "discoverer_actor": low, "discoverer_critic": low,
        "team_discriminator": 0, "individual_discriminator": 0,
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts/run_agent_count_training_condition_b11.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec, *, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if cell not in CELLS or out.name != cell.tag:
        raise ValueError("B11 accepts only the fixed T6/T8 cell and matching output tag")
    if spec.train_n != cell.train_n or tuple(spec.test_ns) != EVALUATION_ORDER \
            or tuple(spec.panels) != (spec.rollouts,):
        raise ValueError("B11 spec must bind actual train N and final-only N8 then N6 evaluation")
    if (out / "summary.json").exists():
        raise ValueError("existing B11 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": "SET", "training_action_law": "clip",
        "seed": cell.seed, "tag": cell.tag, "launch_sha": launch_sha,
        "admission": admission, "status": "initializing", "fit_started": False,
        "failure": None, "spec": jsonable(vars(spec)), "panels": [],
        "checkpoints": [], "rollouts": [], "counts": {key: 0 for key in expected},
        "expected_counts": expected,
        "training_world_seeds": list(range(
            TRAINING_ENV_SEED_BASE, TRAINING_ENV_SEED_BASE + spec.train_lanes,
        )),
        "evaluation_order": list(EVALUATION_ORDER), "evaluation_action_law": "clip",
        "source_hashes_before": _source_hashes(),
        "reward_units": {
            "training": f"native R / train_N={cell.train_n}",
            "J": "test_N * scalar_return / horizon",
            "service": "users per post-transition step",
        },
        "transition_indexing": (
            "action[t] and original old_logprob[t] map state/position[t] to post-transition t+1"
        ),
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    envs, agent, hooks, calls = [], None, [], {name: 0 for name in OPTIMIZERS}
    publish("admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        envs = make_envs(spec.train_lanes, TRAINING_ENV_SEED_BASE, cell.train_n, spec.horizon)
        _assert_native_envs(envs, cell.train_n)
        seed_rng(cell.seed)
        config = make_b11_config(cell, envs, spec)
        summary["config"] = _config_record(config)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(cell), "spec": vars(spec),
            "config": summary["config"],
        })
        agent, initialization = construct_common_initialized_agent(
            config, out / "initialization_logs",
        )
        summary["common_initialization"] = initialization
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        summary["observed_initial_parameter_normalizer_digest"] = digest_agent(agent)
        summary["effective_entropy_contract_initial"] = _assert_agent_entropy(agent, cell)
        summary["initial_raw_sigma"] = b03.raw_sigma(agent)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        pairs = [env.reset() for env in envs]
        states = np.stack([info["state"] for observation, info in pairs])
        observations = np.stack([observation for observation, info in pairs])
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        summary["counts"]["fits"] = 1
        publish("training starts")
        counted = _CountingAgent(agent, summary["counts"], summary)
        b03_cell = b03.TrainingCell(1, cell.key, "SET", "clip", cell.seed, cell.tag)
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = calls.copy()
            counted.optimizer_before = optimizer_before
            sigma_before = b03.raw_sigma(agent)
            states, observations, steps, dones, motion, returns = b03.collect_rollout(
                counted, envs, states, observations, steps, dones, b03_cell, rollout,
                summary, spec, training_step_hook=training_step_hook,
            )
            summary["counts"]["training_agent_rows"] = (
                summary["counts"]["training_team_steps"] * cell.train_n
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, cell.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B11 training losses")
            _assert_config(agent.config, cell, cell.train_n)
            entropy_after = _assert_agent_entropy(agent, cell)
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: calls[name] - optimizer_before[name] for name in calls},
                "optimizer_total": calls.copy(), "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b03.raw_sigma(agent),
                "effective_entropy_contract_after_update": entropy_after,
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
        summary["checkpoints"].append(save_checkpoint(
            agent, out, spec.rollouts, config, launch_sha,
        ))
        evaluate_final(agent, cell, out, summary, spec, publish)
        if summary["counts"] != expected:
            raise ValueError(f"B11 exposure mismatch: {summary['counts']} != {expected}")
        if calls["discoverer_actor"] <= 0 or calls["discoverer_critic"] <= 0:
            raise ValueError("B11 SET actor/critic optimizer did not run")
        if any(calls[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B11 SET unexpectedly updated disabled skill modules")
        for name in ("discoverer_actor", "discoverer_critic"):
            if summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B11 required learner module did not move: {name}")
        if spec == spec_for(cell) and calls != _expected_production_optimizer_calls(cell):
            raise ValueError("B11 production optimizer exposure differs from fixed contract")
        if len(summary["checkpoints"]) != 2 or [row["path"] for row in summary["checkpoints"]] != [
            "checkpoint_00.pt", f"checkpoint_{spec.rollouts:02d}.pt",
        ]:
            raise ValueError("B11 checkpoint contract requires untrained and final only")
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["effective_entropy_contract_final"] = _assert_agent_entropy(agent, cell)
        summary["final_raw_sigma"] = b03.raw_sigma(agent)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B11 source bytes changed during fit")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary["counts"]["training_agent_rows"] = (
            summary["counts"]["training_team_steps"] * cell.train_n
        )
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b03._finish_motion(
                    telemetry, cell.train_n,
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = calls.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: value - int(before.get(name, 0)) for name, value in calls.items()
            }
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
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
