"""Run the fixed B20 paired ordinary roster-training comparison."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable, Mapping

import numpy as np
import torch

from hmasd.utils import RolloutBuffer
from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.bindings import (
    BLOCKS, EVALUATION_ORDER, FINAL_ROLLOUT, OBJECT_ID, PRODUCTION_SPEC_VALUES,
    SCHEDULES, SOURCE_RELATIVE_PATHS, WORLD_SEED_BASES, Block,
)
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, FitSpec,
)
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.models import strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, capture_parameters, digest_agent, finite, jsonable, model_modules,
    native_components, optimizer_counts, parameter_motion, preserve_rng, save_checkpoint,
    seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


PRODUCTION_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=EVALUATION_ORDER, eval_lanes=32,
    panels=(0, FINAL_ROLLOUT),
)
if jsonable(vars(PRODUCTION_SPEC)) != PRODUCTION_SPEC_VALUES:
    raise ValueError("B20 fixed production spec differs from block bindings")
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ATOL = 1e-7
RTOL = 1e-6


@dataclass(frozen=True)
class Arm:
    key: str
    seed: int
    arm: str = "LOCAL1"
    lambda_l: float = .05


def _source_paths() -> tuple[Path, ...]:
    return tuple(REPOSITORY_ROOT / relative for relative in SOURCE_RELATIVE_PATHS)


def _source_hashes() -> dict[str, str]:
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): b15.file_sha256(path)
        for path in _source_paths()
    }


def _optimizer_ids(agent: Any) -> dict[str, int | None]:
    return {
        name: None if getattr(agent, name + "_optimizer", None) is None
        else id(getattr(agent, name + "_optimizer"))
        for name in b15.OPTIMIZERS
    }


def _normalizers(agent: Any) -> dict[str, Any]:
    return b11._normalizer_manifest(agent)


def _tensor_manifest(agent: Any) -> dict[str, Any]:
    return b11._tensor_manifest(agent)


def _array_identity(value: Any) -> dict[str, Any]:
    array = np.ascontiguousarray(value)
    return {
        "shape": list(array.shape), "dtype": str(array.dtype),
        "sha256": hashlib.sha256(array.tobytes()).hexdigest(),
    }


def _initialization(arm: Arm, config: Any, out: Path) -> tuple[Any, dict[str, Any]]:
    agent = b16.build_local_agent(config, str(out / "raw/initialization_logs" / "local1"))
    parameter_ids: set[int] = set()
    ownership = b11._optimizer_ownership(agent, parameter_ids)
    evidence = {
        "method": "fresh_canonical_n6_b16_local1_construction",
        "canonical_n": 6,
        "parameter_normalizer_digest": digest_agent(agent),
        "tensor_manifest": _tensor_manifest(agent),
        "normalizers": _normalizers(agent),
        "optimizer_ownership": ownership,
        "optimizer_object_ids": _optimizer_ids(agent),
        "optimizer_state_digest": b15._optimizer_state_digest(agent),
        "post_initialization_rng_digest": b03._rng_digest(),
        "initial_buffer": b11._buffer_initial_record(agent),
        "runtime_digest": b03.runtime_state_digest(agent),
        "actual_config": b16._config_record(config),
    }
    return agent, evidence


def _training_worlds(spec: FitSpec, rollout: int, n: int, training_base: int) -> tuple[list[Any], np.ndarray,
                                                                        np.ndarray, dict[str, Any]]:
    base = training_base + 100 * int(rollout)
    rng_before = b03._rng_digest()
    with preserve_rng():
        envs = make_envs(spec.train_lanes, base, n, spec.horizon)
        pairs = [env.reset(seed=base + lane) for lane, env in enumerate(envs)]
    if b03._rng_digest() != rng_before:
        raise ValueError("B20 training world construction/reset changed learner RNG")
    b11._assert_native_envs(envs, n)
    states = np.stack([info["state"] for observation, info in pairs])
    observations = np.stack([observation for observation, info in pairs])
    record = {
        "rollout": int(rollout), "n": int(n),
        "lane_world_seeds": list(range(base, base + spec.train_lanes)),
        "states": states.copy(), "observations": observations.copy(),
        "uav_positions": np.stack([
            np.asarray(env.env.env.uav_positions).copy() for env in envs
        ]),
        "user_positions": np.stack([
            np.asarray(env.env.env.user_positions).copy() for env in envs
        ]),
        "global_rng_before": rng_before, "global_rng_after": b03._rng_digest(),
        "explicit_seeded_reset": True,
    }
    return envs, states, observations, record


def _write_training_world(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    """Commit one complete reset before any environment step can run."""
    arrays = {
        name: np.asarray(value) for name, value in row.items()
        if name in ("rollout", "n", "lane_world_seeds", "states", "observations",
                    "uav_positions", "user_positions", "global_rng_before", "global_rng_after")
    }
    for name, value in arrays.items():
        if value.dtype == object or (np.issubdtype(value.dtype, np.floating) and not np.isfinite(value).all()):
            raise ValueError(f"B20 invalid reset scene {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".npz.partial")
    with partial.open("wb") as stream:
        np.savez(stream, **arrays)
        stream.flush()
        os.fsync(stream.fileno())
    partial.replace(path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return {
        "path": path.relative_to(path.parent.parent).as_posix(),
        "sha256": b15.file_sha256(path), "bytes": path.stat().st_size,
        "rollout": row["rollout"], "n": row["n"],
        "explicit_seeded_reset": True, "no_throwaway_terminal_reset": True,
    }


def collect_complete_episode(
    agent: Any, envs: list[Any], states: np.ndarray, observations: np.ndarray,
    input_dones: np.ndarray, arm: Arm, rollout: int, n: int,
    summary: dict[str, Any], spec: FitSpec,
    optimizer_before: Mapping[str, int],
    *, training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any], np.ndarray]:
    """Collect exactly one episode per lane without resetting terminal environments."""
    telemetry = b03._new_motion()
    returns = np.zeros(spec.train_lanes, dtype=np.float64)
    component_sums = {name: np.zeros(spec.train_lanes, dtype=np.float64) for name in COMPONENTS}
    decision_steps: set[int] = set()
    steps = np.zeros(spec.train_lanes, dtype=np.int64)
    dones = np.asarray(input_dones, dtype=bool).copy()
    summary["_active_training_rollout"] = {
        "rollout": rollout, "n": n, "phase": "collecting",
        "_telemetry": telemetry, "component_sums": component_sums,
        "scalar_returns": returns,
        "optimizer_calls_before_update": dict(optimizer_before),
    }
    for t in range(spec.horizon):
        raw_actions, _, data = agent.step(
            states, observations, steps, dones, deterministic=False,
            return_step_data=True, build_infos=False,
        )
        finite((raw_actions, data), "B20 training policy output")
        raw_before = raw_actions.copy()
        logprob_before = np.asarray(data["action_logprobs"]).copy()
        rng_before = b03._rng_digest()
        executed = b03.map_training_actions(raw_actions, "clip")
        telemetry["diagnostic_rng_unchanged"] &= rng_before == b03._rng_digest()
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
            rewards[lane], next_dones[lane] = reward, done
            returns[lane] += reward
            summary["counts"]["training_team_steps"] += 1
            summary["counts"]["training_uav_steps"] += n
            summary["counts"]["training_episodes"] += int(done)
            exposure = summary["training_exposure_by_n"][str(n)]
            exposure["team_steps"] += 1
            exposure["uav_steps"] += n
            exposure["episodes"] += int(done)
            parts = native_components(info, reward, n)
            for name in COMPONENTS:
                component_sums[name][lane] += parts[name]
            b03._observe_motion(
                telemetry, native, before, raw_actions[lane], executed[lane], after,
                rollout=rollout, t=t, lane=lane, reward=reward, components=parts,
            )
            next_states.append(info["next_state"])
            next_observations.append(obs)
            if training_step_hook is not None:
                training_step_hook({"arm": arm.key, "rollout": rollout, "n": n,
                                    "t": t, "lane": lane, "summary": summary})
        next_states, next_observations = np.stack(next_states), np.stack(next_observations)
        agent.store_transition_batch(
            states=states, next_states=next_states.copy(), observations=observations,
            next_observations=next_observations.copy(), actions=raw_actions, rewards=rewards,
            dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data,
        )
        summary["counts"]["stored_team_steps"] += spec.train_lanes
        summary["training_exposure_by_n"][str(n)]["stored_team_steps"] += spec.train_lanes
        if not np.array_equal(agent.rollout_buffer.actions[t], raw_before):
            raise ValueError("B20 buffer did not retain raw sampled actions")
        if not np.array_equal(agent.rollout_buffer.log_probs[t], logprob_before):
            raise ValueError("B20 buffer did not retain original old log-probabilities")
        states, observations, dones = next_states, next_observations, next_dones
        steps += 1
        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
            raise ValueError("unexpected B20 training terminal boundary")
    if not dones.all():
        raise ValueError("B20 complete collector missed terminal boundary")
    telemetry["decision_step_indices_zero_based"] = sorted(decision_steps)
    telemetry["native_component_means_per_world"] = {
        name: (values / spec.horizon).tolist() for name, values in component_sums.items()
    }
    if not all((telemetry["diagnostic_rng_unchanged"], telemetry["policy_output_unchanged"],
                telemetry["old_logprob_unchanged"])):
        raise ValueError("B20 action mapping diagnostics changed policy/RNG data")
    if telemetry["executed_min"] < -1.0 or telemetry["executed_max"] > 1.0:
        raise ValueError("B20 clipped execution exceeded action bounds")
    finished = b03._finish_motion(telemetry, n)
    summary["_active_training_rollout"] = {
        "rollout": rollout, "n": n, "phase": "collected",
        "action_motion_telemetry": finished,
        "native_component_sums": jsonable(component_sums),
        "scalar_returns": returns.tolist(),
        "optimizer_calls_before_update": dict(optimizer_before),
    }
    return states, observations, dones, finished, returns


def _audited_update(
    agent: Any, last_states: np.ndarray, last_observations: np.ndarray,
    dones: np.ndarray, spec: FitSpec, active: dict[str, Any], exposure: dict[str, int],
) -> tuple[Any, dict[str, Any]]:
    buffer = agent.rollout_buffer
    original = buffer.get_discoverer_sampler
    sizes: list[int] = []
    num_actual_steps = int(buffer._get_full_rollout_data()["num_actual_steps"])
    expected_chunk = min(int(agent.config.k), num_actual_steps)
    effective_steps = (
        num_actual_steps if num_actual_steps < int(agent.config.k)
        else (num_actual_steps // int(agent.config.k)) * int(agent.config.k)
    )
    audit = {
        "status": "running", "recurrent_minibatches": 0, "sequence_batch_sizes": sizes,
        "time_chunk_lengths": [], "configured_time_chunk_length": int(agent.config.k),
        "num_actual_time_steps": num_actual_steps, "effective_time_steps": effective_steps,
        "dropped_time_tail_steps": num_actual_steps - effective_steps,
        "full_sequence_batch_size": spec.sequence_batch_size,
    }
    active["sampler_audit_partial"] = audit
    exposure["dropped_time_tail_steps"] += num_actual_steps - effective_steps

    def audited(*args: Any, **kwargs: Any):
        iterator = original(*args, **kwargs)
        if iterator is None:
            return
        for batch in iterator:
            sizes.append(int(batch["observations"].shape[1]))
            audit["time_chunk_lengths"].append(int(batch["observations"].shape[0]))
            audit["recurrent_minibatches"] = len(sizes)
            exposure["recurrent_minibatches_yielded"] += 1
            exposure["sampled_sequences_yielded"] += sizes[-1]
            exposure["short_sequence_tail_batches"] += int(sizes[-1] < spec.sequence_batch_size)
            yield batch

    buffer.get_discoverer_sampler = audited
    try:
        losses = agent.update(
            last_values=np.zeros((spec.train_lanes, int(agent.config.n_agents)), dtype=np.float32),
            dones=dones.copy(), steps_in_buffer=spec.horizon,
            last_state=last_states.copy(), last_observations=last_observations.copy(),
        )
    finally:
        buffer.get_discoverer_sampler = original
    if not sizes:
        raise ValueError("B20 actual PPO update yielded no recurrent minibatches")
    result = {
        "recurrent_minibatches": len(sizes), "sequence_batch_sizes": sizes,
        "full_sequence_batch_size": spec.sequence_batch_size,
        "short_tail_batches": sum(size < spec.sequence_batch_size for size in sizes),
        "minimum_sequence_batch_size": min(sizes), "maximum_sequence_batch_size": max(sizes),
        "sampled_sequences": int(sum(sizes)),
        "time_chunk_lengths": audit["time_chunk_lengths"],
        "configured_time_chunk_length": int(agent.config.k),
        "observed_time_chunk_length": expected_chunk,
        "num_actual_time_steps": num_actual_steps, "effective_time_steps": effective_steps,
        "dropped_time_tail_steps": num_actual_steps - effective_steps,
    }
    audit.update(result, status="complete")
    return losses, result


def adapt_roster(agent: Any, new_n: int, spec: FitSpec) -> dict[str, Any]:
    """Atomically replace count-shaped runtime after the old-N update."""
    old_n = int(agent.config.n_agents)
    if np.any(agent.rollout_buffer.env_lengths):
        raise ValueError("B20 roster adapter requires the consumed buffer to be cleared")
    parameter_ids_before = {
        name: [id(parameter) for parameter in module.parameters()]
        for name, module in model_modules(agent).items()
    }
    digest_before = digest_agent(agent)
    optimizer_ids_before = _optimizer_ids(agent)
    optimizer_state_before = b15._optimizer_state_digest(agent)
    normalizers_before = _normalizers(agent)
    rng_before = b03._rng_digest()
    sampler_state = agent.rollout_buffer.get_sampler_rng_state()
    sampler_digest_before = b15._sampler_digest(agent)
    training_mode = bool(agent.training)
    old_buffer_id = id(agent.rollout_buffer)

    agent.config.n_agents = int(new_n)
    agent.config.n_uavs = int(new_n)
    agent.config.calculate_and_set_buffer_sizes()
    agent.skill_coordinator.value_heads_obs.n_agents = int(new_n)
    old = agent.rollout_buffer
    replacement = RolloutBuffer(
        num_steps=int(agent.config.rollout_length), num_envs=int(agent.config.num_envs),
        n_agents=int(new_n), obs_dim=int(agent.config.obs_dim), action_dim=int(agent.config.action_dim),
        gru_hidden_size=int(agent.config.gru_hidden_size), n_Z=int(agent.config.n_Z),
        n_z=int(agent.config.n_z), state_dim=int(agent.config.state_dim),
        action_space_type=str(agent.config.action_space_type),
        compact_dim=getattr(old, "compact_dim", 0), sampler_seed=int(agent.rollout_sampler_seed),
        d2_enabled=bool(agent.d2_enabled), central_snapshot=bool(agent.use_central_snapshot),
    )
    replacement.set_sampler_rng_state(sampler_state)
    agent.rollout_buffer = replacement

    for name in (
        "env_reward_sums", "env_timers", "env_team_skills", "env_agent_skills",
        "env_log_probs", "env_hidden_states", "env_prev_hidden_states",
        "env_pending_high_level", "env_skill_ages", "env_skill_duration_remaining",
        "env_skill_duration_target", "env_team_ages", "env_d2_last_decision",
        "d2_open_agent_segments", "d2_open_team_segments", "episode_team_skill_counts",
        "high_level_samples_by_env", "force_high_level_collection", "env_reward_thresholds",
    ):
        value = getattr(agent, name, None)
        if isinstance(value, dict):
            value.clear()
    agent.current_team_skill = None
    agent.current_agent_skills = None
    agent.episode_agent_skill_counts = []
    agent._hidden_batch_capacity = 0
    agent.actor_hidden_np = agent.critic_hidden_np = None
    agent.prev_actor_hidden_np = agent.prev_critic_hidden_np = None
    agent._hidden_state_array_valid = None
    agent._central_snapshot_capacity = 0
    agent._central_snapshot_states = agent._central_snapshot_obs = None
    agent._central_snapshot_valid = None
    if hasattr(agent, "env_state_manager"):
        with agent.env_state_manager.lock:
            agent.env_state_manager.states.clear()
            agent.env_state_manager.access_times.clear()
    agent.train(training_mode)

    parameter_ids_after = {
        name: [id(parameter) for parameter in module.parameters()]
        for name, module in model_modules(agent).items()
    }
    checks = {
        "old_n": old_n, "new_n": int(new_n), "old_buffer_id": old_buffer_id,
        "new_buffer_id": id(replacement), "buffer_replaced": old_buffer_id != id(replacement),
        "parameter_objects_preserved": parameter_ids_before == parameter_ids_after,
        "parameter_values_preserved": digest_before == digest_agent(agent),
        "optimizer_objects_preserved": optimizer_ids_before == _optimizer_ids(agent),
        "optimizer_state_preserved": optimizer_state_before == b15._optimizer_state_digest(agent),
        "normalizers_preserved": normalizers_before == _normalizers(agent),
        "training_mode_preserved": bool(agent.training) == training_mode,
        "global_rng_preserved": b03._rng_digest() == rng_before,
        "sampler_rng_preserved": b15._sampler_digest(agent) == sampler_digest_before,
        "shared_value_head_n_agents": int(agent.skill_coordinator.value_heads_obs.n_agents),
        "config_n_agents": int(agent.config.n_agents),
        "buffer_n_agents": int(agent.rollout_buffer.n_agents),
        "buffer_empty": bool(not np.any(agent.rollout_buffer.env_lengths)),
        "next_entry_hidden_state_zero_by_fresh_allocation": True,
    }
    required = [value for key, value in checks.items() if key.endswith("_preserved")]
    if not all(required) or not checks["buffer_replaced"] or not checks["buffer_empty"]:
        raise ValueError(f"B20 roster boundary invariant failed: {checks}")
    if not all(checks[key] == int(new_n) for key in (
        "shared_value_head_n_agents", "config_n_agents", "buffer_n_agents",
    )):
        raise ValueError(f"B20 roster metadata did not rebind: {checks}")
    return checks


def _world_seed(n: int, world_seed_bases: Mapping[int, int]) -> int:
    if int(n) not in world_seed_bases:
        raise ValueError(f"B20 has no evaluation worlds for N={n}")
    return world_seed_bases[int(n)]


def _evaluate_stage(
    learner: Any, arm: Arm, stage: int, out: Path, summary: dict[str, Any],
    spec: FitSpec, publish: Callable[[str], None], world_seed_bases: Mapping[int, int],
) -> None:
    isolation_before = b15._isolation_snapshot(learner, [])
    with preserve_rng():
        for n in EVALUATION_ORDER:
            base = _world_seed(n, world_seed_bases)
            seed_rng(base + 51)
            envs = make_envs(spec.eval_lanes, base, n, spec.horizon)
            target, inference, hooks = None, None, []
            storage_calls = 0
            original_store = None
            row = {
                "status": "running", "arm": arm.key, "policy_stage": stage,
                "after_rollout": stage, "test_n": n,
                "world_seeds": list(range(base, base + spec.eval_lanes)),
                "runtime_seed": base + 51, "execution_law": "clip",
                "steps": 0, "episodes": 0, "resets": 0, "policy_step_calls": 0,
            }
            summary["panels"].append(row)
            publish(f"stage {stage} evaluation N={n} starting")
            try:
                b11._assert_native_envs(envs, n)
                config = b16.make_b16_config(arm, envs, replace(spec, train_n=n), expected_n=n)
                target = b16.build_local_agent(
                    config, str(out / "raw/evaluation_logs" / f"stage{stage:02d}_n{n}"),
                )
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != digest_agent(learner):
                    raise ValueError("B20 evaluation target did not strictly load learner")
                normals_before = _normalizers(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("B20 evaluation attempted training storage")

                target.store_transition_batch = MethodType(reject_store, target)
                inference = b16._InferenceCounter(target, n)
                pairs = [env.reset() for env in envs]
                row["resets"] = len(pairs)
                summary["counts"]["evaluation_resets"] += len(pairs)
                states = np.stack([info["state"] for observation, info in pairs])
                observations = np.stack([observation for observation, info in pairs])
                row["initial_world_identity"] = {
                    "states": _array_identity(states),
                    "observations": _array_identity(observations),
                    "uav_positions": _array_identity(np.stack([
                        np.asarray(env.env.env.uav_positions) for env in envs
                    ])),
                    "user_positions": _array_identity(np.stack([
                        np.asarray(env.env.env.user_positions) for env in envs
                    ])),
                }
                trace = b15._new_panel_trace(spec, n)
                trace["initial_states"], trace["initial_observations"] = states.copy(), observations.copy()
                trace["initial_uav_positions"] = np.stack([
                    np.asarray(env.env.env.uav_positions).copy() for env in envs
                ])
                trace["initial_user_positions"] = np.stack([
                    np.asarray(env.env.env.user_positions).copy() for env in envs
                ])
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                sums = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                action_min, action_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        trace["states"][t], trace["observations"][t] = states, observations
                        raw, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        row["policy_step_calls"] += 1
                        summary["counts"]["evaluation_policy_step_calls"] += 1
                        finite((raw, data), "B20 deterministic evaluation output")
                        inference.observe_choices(data)
                        raw_before = raw.copy()
                        executed = b03.map_training_actions(raw, "clip")
                        if not np.array_equal(raw, raw_before):
                            raise ValueError("B20 evaluation mapping changed raw actions")
                        trace["raw_actions"][t], trace["executed_actions"][t] = raw, executed
                        action_min = min(action_min, float(executed.min()))
                        action_max = max(action_max, float(executed.max()))
                        next_states, next_observations = [], []
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_uav_steps"] += n
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                sums[name][lane] += parts[name]
                            b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                            next_states.append(info["next_state"])
                            next_observations.append(obs)
                            dones[lane] = done
                        states, observations = np.stack(next_states), np.stack(next_observations)
                        trace["next_states"][t], trace["next_observations"][t] = states, observations
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B20 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B20 evaluation missed terminal boundary")
                means = {name: values / spec.horizon for name, values in sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
                if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    j, native_j, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("B20 native J/component identity failed")
                service = trace["served_user_counts"].mean(axis=0)
                eligibility = trace["eligible_user_counts"].mean(axis=0)
                unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
                if not np.allclose(service, 50 * means["coverage_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    unserved, eligibility - service, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("B20 service identities failed")
                inference_counts = inference.finish(spec)
                if inference.data["set_snapshot_refresh_steps"] or inference.data["set_snapshot_lane_refreshes"]:
                    raise ValueError("B20 LOCAL1 evaluation used a central actor snapshot")
                after = digest_agent(target)
                if any(calls.values()) or storage_calls or after != before:
                    raise ValueError("B20 evaluation optimized, stored, or changed parameters")
                if _normalizers(target) != normals_before or np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B20 evaluation changed normalizers or training storage")
                trace_path = out / "raw" / f"trace_stage{stage:02d}_n{n}.npz"
                trace_identity = b11._write_trace(trace_path, trace)
                trace_identity["relative_to_arm"] = trace_path.relative_to(out).as_posix()
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    uav_height_means_per_world=trace["uav_heights"].mean(axis=(0, 2)).tolist(),
                    component_means=jsonable(means), service_arrays={
                        "E_eligible_users_per_step": eligibility.tolist(),
                        "S_served_users_per_step": service.tolist(),
                        "U_eligible_unserved_users_per_step": unserved.tolist(),
                    }, optimizer_calls=calls.copy(), training_storage_calls=storage_calls,
                    frozen_weights_and_normalizers=True,
                    parameter_normalizer_digest_before=before,
                    parameter_normalizer_digest_after=after,
                    normalizers_before=normals_before, normalizers_after=_normalizers(target),
                    executed_action_bounds={"minimum": action_min, "maximum": action_max},
                    inference_counts=inference_counts, trace=trace_identity,
                    config=b16._config_record(config), post_transition_semantics=True,
                )
                summary["counts"]["panels"] += 1
                summary["counts"]["evaluation_optimizer_calls"] += sum(calls.values())
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                publish(f"stage {stage} evaluation N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                raise
            finally:
                if inference is not None:
                    inference.close()
                if target is not None and original_store is not None:
                    target.store_transition_batch = original_store
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    isolation_after = b15._isolation_snapshot(learner, [])
    preservation = {
        "before": isolation_before, "after": isolation_after,
        **{name + "_preserved": isolation_before[name] == isolation_after[name]
           for name in isolation_before},
    }
    summary["stage_isolation"][str(stage)] = preservation
    if not all(value for key, value in preservation.items() if key.endswith("_preserved")):
        raise ValueError("B20 evaluation changed learner, optimizer, sampler, runtime, or RNG")


def _expected_arm_counts(schedule: tuple[int, ...], spec: FitSpec, *, common_stage0: bool = False) -> dict[str, int]:
    training = spec.rollouts * spec.train_lanes * spec.horizon
    stages = 1 if common_stage0 else 2
    evaluation = stages * len(EVALUATION_ORDER) * spec.eval_lanes * spec.horizon
    return {
        "fits": 1, "training_team_steps": training, "stored_team_steps": training,
        "training_uav_steps": spec.train_lanes * spec.horizon * sum(schedule),
        "training_episodes": spec.rollouts * spec.train_lanes,
        "updates": spec.rollouts, "training_policy_step_calls": spec.rollouts * spec.horizon,
        "panels": stages * len(EVALUATION_ORDER), "evaluation_team_steps": evaluation,
        "evaluation_uav_steps": stages * spec.eval_lanes * spec.horizon * sum(EVALUATION_ORDER),
        "evaluation_episodes": stages * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_resets": stages * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_policy_step_calls": stages * len(EVALUATION_ORDER) * spec.horizon,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _stage_readings(panels: list[dict[str, Any]], final_stage: int) -> dict[str, Any]:
    joined = {(row["policy_stage"], row["test_n"]): row for row in panels}
    expected = {(stage, n) for stage in (0, final_stage) for n in EVALUATION_ORDER}
    if set(joined) != expected:
        raise ValueError("B20 arm readings require exact stage0/final panels")
    by_n = {}
    for n in EVALUATION_ORDER:
        initial, final = joined[(0, n)], joined[(final_stage, n)]
        if initial["world_seeds"] != final["world_seeds"]:
            raise ValueError("B20 stage0/final worlds differ")
        if initial["initial_world_identity"] != final["initial_world_identity"]:
            raise ValueError("B20 stage0/final physical arrays differ")
        worlds = initial["world_seeds"]
        q0, qf = b15._quantities(initial), b15._quantities(final)
        q0["height"], qf["height"] = (
            np.asarray(initial["uav_height_means_per_world"]),
            np.asarray(final["uav_height_means_per_world"]),
        )
        by_n[str(n)] = {
            "world_seeds": worlds,
            "stage0": {key: b15._stats(value, worlds) for key, value in q0.items()},
            "stage45": {key: b15._stats(value, worlds) for key, value in qf.items()},
            "stage45_minus_stage0": {
                key: b15._stats(qf[key] - q0[key], worlds) for key in q0
            },
        }
    return {"by_test_n": by_n, "cross_n_aggregate": None}


def run_arm(
    out: Path, block: Block, arm: Arm, schedule: tuple[int, ...], launch_sha: str,
    admission: Mapping[str, Any], spec: FitSpec, *, command_start: float,
    training_base: int, world_seed_bases: Mapping[int, int],
    expected_initialization: Mapping[str, Any] | None = None,
    expected_initial_traces: Mapping[str, str] | None = None,
    common_stage0_panels: list[dict[str, Any]] | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    if len(schedule) != spec.rollouts:
        raise ValueError("B20 arm schedule length mismatch")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    expected = _expected_arm_counts(schedule, spec, common_stage0=common_stage0_panels is not None)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": out.parent.name,
        "block": block.number, "arm": arm.key,
        "seed": arm.seed, "launch_sha": launch_sha, "admission": dict(admission),
        "status": "initializing", "fit_started": False, "failure": None,
        "schedule": list(schedule), "spec": jsonable(vars(spec)), "panels": [],
        "checkpoints": [], "rollouts": [], "boundaries": [], "stage_isolation": {},
        "counts": {key: 0 for key in expected}, "expected_counts": expected,
        "training_exposure_by_n": {
            str(n): {
                "rollouts_started": 0, "rollouts_updated": 0,
                "team_steps": 0, "uav_steps": 0, "stored_team_steps": 0,
                "episodes": 0, "outer_updates_complete": 0,
                "recurrent_minibatches_yielded": 0, "sampled_sequences_yielded": 0,
                "short_sequence_tail_batches": 0, "dropped_time_tail_steps": 0,
                "discoverer_actor_optimizer_calls": 0,
                "discoverer_critic_optimizer_calls": 0,
            }
            for n in sorted(set(schedule))
        },
        "source_hashes_before": _source_hashes(),
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["arm_wall_seconds"] = time.perf_counter() - started
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        write_json(out / "summary.json", summary)

    agent = None
    envs: list[Any] = []
    hooks: list[Any] = []
    optimizer_call_counts: dict[str, int] = {}
    (out / "raw").mkdir(exist_ok=True)
    publish("arm admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        # Config dimensions are established from a non-training canonical N6 constructor.
        with preserve_rng():
            config_envs = make_envs(spec.train_lanes, training_base, 6, spec.horizon)
        try:
            seed_rng(arm.seed)
            config = b16.make_b16_config(arm, config_envs, replace(spec, train_n=6), expected_n=6)
        finally:
            for env in config_envs:
                env.close()
        summary["initial_config"] = b16._config_record(config)
        write_json(out / "config.json", {
            "object_id": OBJECT_ID, "tag": out.parent.name,
            "block": block.number, "arm": arm.key, "seed": arm.seed,
            "launch_sha": launch_sha, "schedule": list(schedule), "spec": vars(spec),
            "config": summary["initial_config"], "evaluation_order": list(EVALUATION_ORDER),
            "world_seed_bases": dict(world_seed_bases),
            "training_world_seed_formula": f"{training_base} + 100 * rollout + lane",
        })
        agent, initialization = _initialization(arm, config, out)
        agent.train(True)
        write_json(out / "raw/initialization.json", initialization)
        summary["initialization"] = {
            "parameter_normalizer_digest": initialization["parameter_normalizer_digest"],
            "optimizer_state_digest": initialization["optimizer_state_digest"],
            "post_initialization_rng_digest": initialization["post_initialization_rng_digest"],
            "runtime_digest": initialization["runtime_digest"],
            "raw": {"path": "raw/initialization.json",
                    "sha256": b15.file_sha256(out / "raw/initialization.json"),
                    "bytes": (out / "raw/initialization.json").stat().st_size},
        }
        if expected_initialization is not None:
            for key in ("parameter_normalizer_digest", "tensor_manifest", "normalizers",
                        "optimizer_ownership", "optimizer_state_digest",
                        "post_initialization_rng_digest", "initial_buffer",
                        "runtime_digest", "actual_config"):
                if initialization[key] != expected_initialization[key]:
                    raise ValueError(f"B20 F/M initial {key} mismatch")
            summary["initialization_matches_F"] = True
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        optimizer_call_counts, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = optimizer_call_counts
        initial_parameters = capture_parameters(agent)
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        checkpoint = save_checkpoint(agent, out / "raw", 0, config, launch_sha)
        summary["checkpoints"].append({**checkpoint, "relative_to_arm": f"raw/{checkpoint['path']}"})
        if common_stage0_panels is None:
            _evaluate_stage(agent, arm, 0, out, summary, spec, publish, world_seed_bases)
            summary["initial_evaluation_trace_sha256"] = {
                str(n): b15.file_sha256(out / "raw" / f"trace_stage00_n{n}.npz")
                for n in EVALUATION_ORDER
            }
        else:
            if expected_initialization is None or expected_initial_traces is None:
                raise ValueError("B20 common initial stage requires identity evidence")
            summary["common_stage0"] = {
                "owner": "F", "panel_paths": [f"../F/panel_stage00_n{n}.json" for n in EVALUATION_ORDER],
                "trace_sha256": dict(expected_initial_traces), "reused_after_full_initial_identity": True,
                "new_environment_steps": 0,
            }
        if schedule[0] != 6:
            invariant = adapt_roster(agent, schedule[0], spec)
            summary["boundaries"].append({
                "after_rollout": 0, "kind": "canonical_initialization_to_first_training_roster",
                **invariant,
            })
        summary["status"] = "training"
        publish("training starts")

        input_dones = np.zeros(spec.train_lanes, dtype=bool)
        for rollout, n in enumerate(schedule, start=1):
            rollout_start = time.perf_counter()
            exposure = summary["training_exposure_by_n"][str(n)]
            exposure["rollouts_started"] += 1
            optimizer_before = optimizer_call_counts.copy()
            envs, states, observations, world = _training_worlds(spec, rollout, n, training_base)
            reset_path = out / "raw" / f"training_reset_r{rollout:02d}_n{n}.npz"
            reset_identity = _write_training_world(reset_path, world)
            summary.setdefault("training_reset_scenes", []).append(reset_identity)
            summary["_active_training_rollout"] = {
                "rollout": rollout, "n": n, "phase": "reset_complete",
                "reset_scene": reset_identity,
                "optimizer_calls_before_update": optimizer_before,
            }
            publish(f"rollout {rollout} N={n} reset complete")
            active_counter = b16._InferenceCounter(agent, n)
            counted = b15._CountingAgent(agent, summary["counts"], summary, active_counter)
            counted.optimizer_before = optimizer_before
            summary["_active_training_rollout"]["phase"] = "collecting"
            publish(f"rollout {rollout} N={n} collecting")
            try:
                last_states, last_observations, dones, motion, returns = collect_complete_episode(
                    counted, envs, states, observations, input_dones, arm, rollout, n,
                    summary, spec, optimizer_before,
                    training_step_hook=training_step_hook,
                )
            finally:
                active_counter.close()
            summary["fit_started"] = True
            summary["counts"]["fits"] = 1
            publish(f"rollout {rollout} N={n} collected")
            summary["_active_training_rollout"].update(
                phase="updating", optimizer_calls_before_update=optimizer_before,
            )
            publish(f"rollout {rollout} N={n} updating")
            losses, sampler = _audited_update(
                agent, last_states, last_observations, dones, spec,
                summary["_active_training_rollout"], exposure,
            )
            summary["counts"]["updates"] += 1
            exposure["outer_updates_complete"] += 1
            exposure["rollouts_updated"] += 1
            finite(losses, "B20 training losses")
            optimizer_delta = {
                name: optimizer_call_counts[name] - optimizer_before[name]
                for name in optimizer_call_counts
            }
            exposure["discoverer_actor_optimizer_calls"] += optimizer_delta[
                "discoverer_actor"
            ]
            exposure["discoverer_critic_optimizer_calls"] += optimizer_delta[
                "discoverer_critic"
            ]
            summary["_active_training_rollout"]["optimizer_calls_accounted"] = dict(
                optimizer_delta
            )
            if optimizer_delta["discoverer_actor"] != sampler["recurrent_minibatches"] or \
                    optimizer_delta["discoverer_critic"] != sampler["recurrent_minibatches"]:
                raise ValueError("B20 optimizer calls disagree with actual recurrent minibatches")
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "n": n, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": optimizer_delta, "optimizer_total": optimizer_call_counts.copy(),
                "sampler": sampler, "parameter_motion": motion_parameters,
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            training_path = out / "raw/training.jsonl"
            with training_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            summary["training_stream"] = {
                "path": "raw/training.jsonl", "bytes": training_path.stat().st_size,
                "sha256": b15.file_sha256(training_path),
                "completed_rows": len(summary["rollouts"]) + 1,
                "digest_scope": "SHA256 of the first 'bytes' bytes at this completed-row frontier",
            }
            summary["rollouts"].append({
                key: value for key, value in row.items()
                if key not in ("action_motion_telemetry", "sampler", "training_scalar_returns", "losses")
            } | {"sampler": {key: value for key, value in sampler.items()
                              if key not in ("sequence_batch_sizes", "time_chunk_lengths")},
                 "raw_row": "raw/training.jsonl"})
            summary["parameter_motion"] = motion_parameters
            agent.clear_buffers()
            for env in envs:
                env.close()
            envs = []
            summary.pop("_active_training_rollout", None)
            if rollout < spec.rollouts:
                invariant = adapt_roster(agent, schedule[rollout], spec)
                summary["boundaries"].append({"after_rollout": rollout, **invariant})
                input_dones = np.ones(spec.train_lanes, dtype=bool)
            publish(f"rollout {rollout} N={n} updated")

        checkpoint = save_checkpoint(agent, out / "raw", spec.rollouts, config, launch_sha)
        summary["checkpoints"].append({**checkpoint, "relative_to_arm": f"raw/{checkpoint['path']}"})
        summary["checkpoint_semantics"] = (
            "initial/final evaluation weights and normalizers only; no resume or optimizer-restoration claim"
        )
        _evaluate_stage(agent, arm, spec.rollouts, out, summary, spec, publish, world_seed_bases)
        if summary["counts"] != expected:
            raise ValueError(f"B20 {arm.key} exposure mismatch: {summary['counts']} != {expected}")
        expected_boundaries = spec.rollouts - 1 + int(schedule[0] != 6)
        if len(summary["boundaries"]) != expected_boundaries:
            raise ValueError("B20 missing atomic rollout boundary records")
        if any(optimizer_call_counts[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B20 optimized a disabled module")
        expected_minibatches = sum(row["sampler"]["recurrent_minibatches"] for row in summary["rollouts"])
        if optimizer_call_counts["discoverer_actor"] != expected_minibatches or \
                optimizer_call_counts["discoverer_critic"] != expected_minibatches:
            raise ValueError("B20 aggregate optimizer/minibatch accounting mismatch")
        if spec == PRODUCTION_SPEC and optimizer_call_counts["discoverer_actor"] != 101_250:
            raise ValueError("B20 production optimizer exposure differs from fixed contract")
        for name in ("discoverer_actor", "discoverer_critic"):
            if optimizer_call_counts[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B20 learner module did not move: {name}")
        summary["stage_readings"] = _stage_readings(
            (common_stage0_panels or []) + summary["panels"], spec.rollouts,
        )
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_config"] = b16._config_record(agent.config)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B20 source changed during arm execution")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                active["_telemetry"] = b03._finish_motion(active["_telemetry"], int(active["n"]))
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = optimizer_call_counts.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0))
                for name, count in optimizer_call_counts.items()
            }
            accounted = active.get("optimizer_calls_accounted", {})
            n_key = str(active["n"])
            summary["training_exposure_by_n"][n_key][
                "discoverer_actor_optimizer_calls"
            ] += active["optimizer_delta_observed"].get("discoverer_actor", 0) - int(
                accounted.get("discoverer_actor", 0)
            )
            summary["training_exposure_by_n"][n_key][
                "discoverer_critic_optimizer_calls"
            ] += active["optimizer_delta_observed"].get("discoverer_critic", 0) - int(
                accounted.get("discoverer_critic", 0)
            )
            summary["incomplete_rollout"] = jsonable(active)
        summary["fit_started"] = summary["counts"]["training_team_steps"] > 0
        summary["counts"]["fits"] = int(summary["fit_started"])
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "arm_wall_seconds": time.perf_counter() - started,
            "command_wall_seconds": time.perf_counter() - command_start,
            "cpu_user_seconds_process_cumulative": usage.ru_utime,
            "cpu_system_seconds_process_cumulative": usage.ru_stime,
            "peak_rss_kib_process_cumulative": usage.ru_maxrss,
            "rss_scope": "paired scientific process Linux RUSAGE_SELF; cumulative across arms",
            "resources_unmeasured": ["peak_scratch_bytes", "other_processes"],
        }
        publish(summary["status"])
    return return_code

def _initial_trace_identity(out: Path, arm: str) -> dict[str, str]:
    return {
        str(n): b15.file_sha256(out / arm / "raw" / f"trace_stage00_n{n}.npz")
        for n in EVALUATION_ORDER
    }


def _paired_readings(
    f_summary: Mapping[str, Any], m_summary: Mapping[str, Any], final_stage: int,
) -> dict[str, Any]:
    f_panels = {(row["policy_stage"], row["test_n"]): row for row in f_summary["panels"]}
    m_panels = {(row["policy_stage"], row["test_n"]): row for row in m_summary["panels"]}
    by_n = {}
    for n in EVALUATION_ORDER:
        f_row, m_row = f_panels[(final_stage, n)], m_panels[(final_stage, n)]
        if f_row["world_seeds"] != m_row["world_seeds"]:
            raise ValueError("B20 final paired worlds differ")
        fq, mq = b15._quantities(f_row), b15._quantities(m_row)
        fq["height"], mq["height"] = (
            np.asarray(f_row["uav_height_means_per_world"]),
            np.asarray(m_row["uav_height_means_per_world"]),
        )
        worlds = f_row["world_seeds"]
        by_n[str(n)] = {
            "world_seeds": worlds,
            "final_F": {key: b15._stats(value, worlds) for key, value in fq.items()},
            "final_M": {key: b15._stats(value, worlds) for key, value in mq.items()},
            "final_M_minus_F": {
                key: b15._stats(mq[key] - fq[key], worlds) for key in fq
            },
            "adverse_J_or_S_worlds": [
                {"world_seed": worlds[index], "delta_J": float(mq["J"][index] - fq["J"][index]),
                 "delta_S": float(mq["S"][index] - fq["S"][index])}
                for index in range(len(worlds))
                if mq["J"][index] - fq["J"][index] <= 0 or mq["S"][index] - fq["S"][index] <= 0
            ],
            "quality_height_tradeoff_worlds": [
                {"world_seed": worlds[index],
                 "delta_Q": float(mq["Q"][index] - fq["Q"][index]),
                 "delta_height": float(mq["height"][index] - fq["height"][index]),
                 "delta_P": float(mq["P"][index] - fq["P"][index])}
                for index in range(len(worlds))
                if (mq["Q"][index] - fq["Q"][index])
                * (mq["height"][index] - fq["height"][index]) > 0
            ],
        }
    signs = {
        f"D{n}{quantity}": by_n[str(n)]["final_M_minus_F"][quantity]["mean"] > 0
        for n in (5, 7) for quantity in ("J", "S")
    }
    return {"by_test_n": by_n, "primary_signs": signs,
            "primary_joint_directional_prediction_met": all(signs.values()),
            "cross_n_aggregate": None}


def _common_n6_training_world_identity(out: Path, schedules: Mapping[str, tuple[int, ...]]) -> dict[str, Any]:
    matched = []
    for index, (f_n, m_n) in enumerate(zip(schedules["F"], schedules["M"]), start=1):
        if f_n != 6 or m_n != 6:
            continue
        name = f"training_reset_r{index:02d}_n6.npz"
        with np.load(out / "F/raw" / name, allow_pickle=False) as source:
            f = {key: source[key].copy() for key in source.files}
        with np.load(out / "M/raw" / name, allow_pickle=False) as source:
            m = {key: source[key].copy() for key in source.files}
        fields = {key: np.array_equal(f[key], m[key]) for key in
                  ("lane_world_seeds", "states", "observations", "uav_positions", "user_positions")}
        matched.append({"rollout": index, "fields": fields, "all_equal": all(fields.values())})
    if not matched or not all(row["all_equal"] for row in matched):
        raise ValueError("B20 common N6 training reset worlds differ between F and M")
    return {"matched_rollouts": matched, "all_equal": True}


def run_batch(
    out: Path, launch_sha: str, admission: Mapping[str, Any], block: int,
    spec: FitSpec = PRODUCTION_SPEC, *, command_start: float | None = None,
    schedules: Mapping[str, tuple[int, ...]] = SCHEDULES,
    technical_seed: int | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if type(block) is not int or block not in BLOCKS:
        raise ValueError("B20 block must be exactly 1, 2, or 3")
    selected = BLOCKS[block]
    if technical_seed is not None and type(technical_seed) is not int:
        raise ValueError("B20 technical seed must be an integer")
    if technical_seed is not None and spec == PRODUCTION_SPEC:
        raise ValueError("B20 production seed is fixed")
    tag = selected.tag if technical_seed is None else f"technical_{selected.tag}_s{technical_seed}"
    if out.name != tag:
        raise ValueError(f"B20 output basename must be {tag}")
    if launch_sha != admission.get("sha"):
        raise ValueError("B20 launch SHA disagrees with admission")
    if spec != PRODUCTION_SPEC and technical_seed is None:
        raise ValueError("B20 reduced technical spec needs a distinct technical seed")
    seed = selected.seed if technical_seed is None else technical_seed
    if technical_seed in {item.seed for item in BLOCKS.values()}:
        raise ValueError("B20 technical seed must differ from all production blocks")
    training_base = selected.training_world_base if technical_seed is None else selected.training_world_base + 10_000_000
    world_seed_bases = WORLD_SEED_BASES if technical_seed is None else {
        n: base + 10_000_000 for n, base in WORLD_SEED_BASES.items()
    }
    admission_owned = {
        "launch-manifest.json", "launch-status.json", "admission-preflight.json",
        "stdout.log", "stderr.log",
    }
    if out.exists():
        scientific = [path.name for path in out.iterdir() if path.name not in admission_owned]
        if scientific:
            raise ValueError(
                f"existing B20 scientific output; reconcile the original attempt: {scientific}"
            )
    if spec == PRODUCTION_SPEC and dict(schedules) != SCHEDULES:
        raise ValueError("B20 production schedules are fixed")
    if tuple(spec.test_ns) != EVALUATION_ORDER or tuple(spec.panels) != (0, spec.rollouts):
        raise ValueError("B20 requires the fixed evaluation order and initial/final stages")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    batch: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION, "tag": tag,
        "block": block, "production_contract": technical_seed is None,
        "training_world_base": training_base, "evaluation_world_bases": dict(world_seed_bases),
        "seed": seed, "launch_sha": launch_sha, "admission": dict(admission),
        "status": "running", "arm_order": ["F", "M"],
        "arms": {name: {"status": "unstarted", "fit_started": False} for name in ("F", "M")},
        "source_hashes_before": _source_hashes(),
    }

    def publish() -> None:
        batch["wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", batch)

    publish()
    first_initialization = None
    first_initial_traces = None
    first_initial_panels = None

    def aggregate_available_counts() -> None:
        rows = [
            row["counts"] for row in batch["arms"].values()
            if isinstance(row, Mapping) and isinstance(row.get("counts"), Mapping)
        ]
        keys = set().union(*(row.keys() for row in rows)) if rows else set()
        batch["counts"] = {key: sum(int(row.get(key, 0)) for row in rows) for key in keys}

    try:
        for index, name in enumerate(("F", "M")):
            batch["arms"][name] = {"status": "running", "fit_started": False}
            publish()
            code = run_arm(
                out / name, selected, Arm(name, seed), tuple(schedules[name]), launch_sha, admission, spec,
                command_start=command_start, expected_initialization=first_initialization,
                expected_initial_traces=first_initial_traces,
                common_stage0_panels=first_initial_panels,
                training_base=training_base, world_seed_bases=world_seed_bases,
                agent_setup_hook=agent_setup_hook, training_step_hook=training_step_hook,
            )
            arm_summary = json.loads((out / name / "summary.json").read_text(encoding="utf-8"))
            batch["arms"][name] = {
                "status": arm_summary["status"], "fit_started": arm_summary["fit_started"],
                "counts": arm_summary["counts"], "summary": f"{name}/summary.json",
            }
            aggregate_available_counts()
            if code != 0:
                if index + 1 < 2:
                    remaining = ("F", "M")[index + 1]
                    batch["arms"][remaining] = {
                        "status": "unstarted", "fit_started": False,
                        "reason": f"stopped after failed arm {name}",
                    }
                    (out / remaining).mkdir(exist_ok=True)
                    write_json(out / remaining / "summary.json", batch["arms"][remaining])
                batch.update(status="failed", failure=f"arm {name} failed; remaining arm unstarted")
                batch["source_hashes_after"] = _source_hashes()
                batch["source_hashes_unchanged"] = (
                    batch["source_hashes_before"] == batch["source_hashes_after"]
                )
                publish()
                return 1
            if name == "F":
                first_initialization = json.loads(
                    (out / "F/raw/initialization.json").read_text(encoding="utf-8")
                )
                first_initial_traces = arm_summary["initial_evaluation_trace_sha256"]
                first_initial_panels = [row for row in arm_summary["panels"] if row["policy_stage"] == 0]
            else:
                f_traces = _initial_trace_identity(out, "F")
                m_initialization = json.loads(
                    (out / "M/raw/initialization.json").read_text(encoding="utf-8")
                )
                batch["initial_identity"] = {
                    **{key + "_equal": first_initialization[key] == m_initialization[key]
                       for key in ("parameter_normalizer_digest", "tensor_manifest", "normalizers",
                                   "optimizer_ownership", "optimizer_state_digest",
                                   "post_initialization_rng_digest", "initial_buffer",
                                   "runtime_digest", "actual_config")},
                    "common_stage0_trace_sha256": f_traces,
                    "common_stage0_reused_without_new_steps": arm_summary["common_stage0"]["new_environment_steps"] == 0,
                }
                if not all(value for key, value in batch["initial_identity"].items()
                           if key.endswith("_equal")):
                    raise ValueError("B20 F/M initial identity or full trace mismatch")
                batch["common_n6_training_world_identity"] = _common_n6_training_world_identity(
                    out, schedules,
                )
        f_summary = json.loads((out / "F/summary.json").read_text(encoding="utf-8"))
        m_summary = json.loads((out / "M/summary.json").read_text(encoding="utf-8"))
        if sum(row["counts"]["panels"] for row in (f_summary, m_summary)) != 9 and spec == PRODUCTION_SPEC:
            raise ValueError("B20 production requires exactly nine actual evaluation panels")
        batch["readings"] = _paired_readings(f_summary, m_summary, spec.rollouts)
        aggregate_available_counts()
        batch["source_hashes_after"] = _source_hashes()
        batch["source_hashes_unchanged"] = batch["source_hashes_before"] == batch["source_hashes_after"]
        if not batch["source_hashes_unchanged"]:
            raise ValueError("B20 source changed during paired batch")
        batch["status"] = "complete"
        return_code = 0
    except Exception as exc:
        batch.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        batch["resources"] = {
            "wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "paired scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes", "other_processes"],
        }
        publish()
    return return_code
