"""Run the fixed B18 paired ordinary roster-training comparison."""
from __future__ import annotations

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

from hmasd.utils import RolloutBuffer
from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
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


OBJECT_ID = "s1_ordinary_roster_training_b18"
TAG = "s1_ordinary_roster_training_b18_b1_s1004101"
SEED = 1_004_101
TRAINING_WORLD_BASE = 3_044_100
FINAL_ROLLOUT = 45
EVALUATION_ORDER = (5, 7, 6, 4, 8)
WORLD_SEED_BASES = {4: 2_245_400, 5: 2_245_500, 6: 2_245_600,
                    7: 2_245_700, 8: 2_245_800}
SCHEDULES = {"F": (6,) * 45, "M": (4, 6, 8) * 15}
PRODUCTION_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=EVALUATION_ORDER, eval_lanes=32,
    panels=(0, FINAL_ROLLOUT),
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ATOL = 1e-7
RTOL = 1e-6


@dataclass(frozen=True)
class Arm:
    key: str
    arm: str = "LOCAL1"
    seed: int = SEED
    lambda_l: float = .05


ARMS = {name: Arm(name) for name in ("F", "M")}


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(), Path(__file__).resolve().with_name("__init__.py"),
        REPOSITORY_ROOT / "scripts/run_agent_count_ordinary_roster_training_b18.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/local_ordinary_b16/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
        REPOSITORY_ROOT / "hmasd/agent.py", REPOSITORY_ROOT / "hmasd/utils.py",
    )


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
    agent = b16.build_local_agent(config, str(out / "initialization_logs" / "local1"))
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


def _training_worlds(spec: FitSpec, rollout: int, n: int) -> tuple[list[Any], np.ndarray,
                                                                        np.ndarray, dict[str, Any]]:
    base = TRAINING_WORLD_BASE + 100 * int(rollout)
    rng_before = b03._rng_digest()
    with preserve_rng():
        envs = make_envs(spec.train_lanes, base, n, spec.horizon)
        pairs = [env.reset(seed=base + lane) for lane, env in enumerate(envs)]
    if b03._rng_digest() != rng_before:
        raise ValueError("B18 training world construction/reset changed learner RNG")
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


def _write_training_worlds(path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    arrays: dict[str, Any] = {
        "rollout": np.asarray([row["rollout"] for row in records], dtype=np.int64),
        "n": np.asarray([row["n"] for row in records], dtype=np.int64),
        "lane_world_seeds": np.asarray([row["lane_world_seeds"] for row in records], dtype=np.int64),
        "global_rng_before": np.asarray([row["global_rng_before"] for row in records], dtype="S64"),
        "global_rng_after": np.asarray([row["global_rng_after"] for row in records], dtype="S64"),
    }
    # Variable-N observations/UAV arrays are named by rollout; fixed-width state/user arrays stack.
    arrays["states"] = np.stack([row["states"] for row in records])
    arrays["user_positions"] = np.stack([row["user_positions"] for row in records])
    for row in records:
        suffix = f"r{row['rollout']:02d}_n{row['n']}"
        arrays[f"observations_{suffix}"] = row["observations"]
        arrays[f"uav_positions_{suffix}"] = row["uav_positions"]
    identity = b11._write_trace(path, arrays)
    identity.update(reset_calls_per_lane=len(records), explicit_seeded_reset=True,
                    no_throwaway_terminal_reset=True)
    return identity


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
        finite((raw_actions, data), "B18 training policy output")
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
            raise ValueError("B18 buffer did not retain raw sampled actions")
        if not np.array_equal(agent.rollout_buffer.log_probs[t], logprob_before):
            raise ValueError("B18 buffer did not retain original old log-probabilities")
        states, observations, dones = next_states, next_observations, next_dones
        steps += 1
        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
            raise ValueError("unexpected B18 training terminal boundary")
    if not dones.all():
        raise ValueError("B18 complete collector missed terminal boundary")
    telemetry["decision_step_indices_zero_based"] = sorted(decision_steps)
    telemetry["native_component_means_per_world"] = {
        name: (values / spec.horizon).tolist() for name, values in component_sums.items()
    }
    if not all((telemetry["diagnostic_rng_unchanged"], telemetry["policy_output_unchanged"],
                telemetry["old_logprob_unchanged"])):
        raise ValueError("B18 action mapping diagnostics changed policy/RNG data")
    if telemetry["executed_min"] < -1.0 or telemetry["executed_max"] > 1.0:
        raise ValueError("B18 clipped execution exceeded action bounds")
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
        raise ValueError("B18 actual PPO update yielded no recurrent minibatches")
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
        raise ValueError("B18 roster adapter requires the consumed buffer to be cleared")
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
        raise ValueError(f"B18 roster boundary invariant failed: {checks}")
    if not all(checks[key] == int(new_n) for key in (
        "shared_value_head_n_agents", "config_n_agents", "buffer_n_agents",
    )):
        raise ValueError(f"B18 roster metadata did not rebind: {checks}")
    return checks


def _world_seed(n: int) -> int:
    if int(n) not in WORLD_SEED_BASES:
        raise ValueError(f"B18 has no evaluation worlds for N={n}")
    return WORLD_SEED_BASES[int(n)]


def _evaluate_stage(
    learner: Any, arm: Arm, stage: int, out: Path, summary: dict[str, Any],
    spec: FitSpec, publish: Callable[[str], None],
) -> None:
    isolation_before = b15._isolation_snapshot(learner, [])
    with preserve_rng():
        for n in EVALUATION_ORDER:
            base = _world_seed(n)
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
                    config, str(out / "evaluation_logs" / f"stage{stage:02d}_n{n}"),
                )
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != digest_agent(learner):
                    raise ValueError("B18 evaluation target did not strictly load learner")
                normals_before = _normalizers(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("B18 evaluation attempted training storage")

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
                        finite((raw, data), "B18 deterministic evaluation output")
                        inference.observe_choices(data)
                        raw_before = raw.copy()
                        executed = b03.map_training_actions(raw, "clip")
                        if not np.array_equal(raw, raw_before):
                            raise ValueError("B18 evaluation mapping changed raw actions")
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
                            raise ValueError("unexpected B18 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B18 evaluation missed terminal boundary")
                means = {name: values / spec.horizon for name, values in sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
                if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    j, native_j, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("B18 native J/component identity failed")
                service = trace["served_user_counts"].mean(axis=0)
                eligibility = trace["eligible_user_counts"].mean(axis=0)
                unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
                if not np.allclose(service, 50 * means["coverage_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    unserved, eligibility - service, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("B18 service identities failed")
                inference_counts = inference.finish(spec)
                if inference.data["set_snapshot_refresh_steps"] or inference.data["set_snapshot_lane_refreshes"]:
                    raise ValueError("B18 LOCAL1 evaluation used a central actor snapshot")
                after = digest_agent(target)
                if any(calls.values()) or storage_calls or after != before:
                    raise ValueError("B18 evaluation optimized, stored, or changed parameters")
                if _normalizers(target) != normals_before or np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B18 evaluation changed normalizers or training storage")
                trace_path = out / f"trace_stage{stage:02d}_n{n}.npz"
                trace_identity = b11._write_trace(trace_path, trace)
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
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
        raise ValueError("B18 evaluation changed learner, optimizer, sampler, runtime, or RNG")


def _expected_arm_counts(schedule: tuple[int, ...], spec: FitSpec) -> dict[str, int]:
    training = spec.rollouts * spec.train_lanes * spec.horizon
    evaluation = 2 * len(EVALUATION_ORDER) * spec.eval_lanes * spec.horizon
    return {
        "fits": 1, "training_team_steps": training, "stored_team_steps": training,
        "training_uav_steps": spec.train_lanes * spec.horizon * sum(schedule),
        "training_episodes": spec.rollouts * spec.train_lanes,
        "updates": spec.rollouts, "training_policy_step_calls": spec.rollouts * spec.horizon,
        "panels": 2 * len(EVALUATION_ORDER), "evaluation_team_steps": evaluation,
        "evaluation_uav_steps": 2 * spec.eval_lanes * spec.horizon * sum(EVALUATION_ORDER),
        "evaluation_episodes": 2 * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_resets": 2 * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_policy_step_calls": 2 * len(EVALUATION_ORDER) * spec.horizon,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _stage_readings(panels: list[dict[str, Any]], final_stage: int) -> dict[str, Any]:
    joined = {(row["policy_stage"], row["test_n"]): row for row in panels}
    expected = {(stage, n) for stage in (0, final_stage) for n in EVALUATION_ORDER}
    if set(joined) != expected:
        raise ValueError("B18 arm readings require exact stage0/final panels")
    by_n = {}
    for n in EVALUATION_ORDER:
        initial, final = joined[(0, n)], joined[(final_stage, n)]
        if initial["world_seeds"] != final["world_seeds"]:
            raise ValueError("B18 stage0/final worlds differ")
        if initial["initial_world_identity"] != final["initial_world_identity"]:
            raise ValueError("B18 stage0/final physical arrays differ")
        worlds = initial["world_seeds"]
        q0, qf = b15._quantities(initial), b15._quantities(final)
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
    out: Path, arm: Arm, schedule: tuple[int, ...], launch_sha: str,
    admission: Mapping[str, Any], spec: FitSpec, *, command_start: float,
    expected_initialization: Mapping[str, Any] | None = None,
    expected_initial_traces: Mapping[str, str] | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    if len(schedule) != spec.rollouts:
        raise ValueError("B18 arm schedule length mismatch")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    expected = _expected_arm_counts(schedule, spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key,
        "seed": SEED, "launch_sha": launch_sha, "admission": dict(admission),
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
    world_records: list[dict[str, Any]] = []
    publish("arm admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        # Config dimensions are established from a non-training canonical N6 constructor.
        with preserve_rng():
            config_envs = make_envs(spec.train_lanes, TRAINING_WORLD_BASE, 6, spec.horizon)
        try:
            seed_rng(SEED)
            config = b16.make_b16_config(arm, config_envs, replace(spec, train_n=6), expected_n=6)
        finally:
            for env in config_envs:
                env.close()
        summary["initial_config"] = b16._config_record(config)
        write_json(out / "config.json", {
            "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key, "seed": SEED,
            "launch_sha": launch_sha, "schedule": list(schedule), "spec": vars(spec),
            "config": summary["initial_config"], "evaluation_order": list(EVALUATION_ORDER),
            "world_seed_bases": WORLD_SEED_BASES,
            "training_world_seed_formula": "3044100 + 100 * rollout + lane",
        })
        agent, initialization = _initialization(arm, config, out)
        agent.train(True)
        summary["initialization"] = initialization
        if expected_initialization is not None:
            for key in ("parameter_normalizer_digest", "tensor_manifest", "normalizers"):
                if initialization[key] != expected_initialization[key]:
                    raise ValueError(f"B18 F/M initial {key} mismatch")
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
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        _evaluate_stage(agent, arm, 0, out, summary, spec, publish)
        initial_traces = {
            str(n): b15.file_sha256(out / f"trace_stage00_n{n}.npz")
            for n in EVALUATION_ORDER
        }
        summary["initial_evaluation_trace_sha256"] = initial_traces
        if expected_initial_traces is not None:
            summary["initial_evaluation_traces_match_F"] = initial_traces == dict(
                expected_initial_traces
            )
            if not summary["initial_evaluation_traces_match_F"]:
                raise ValueError("B18 F/M full initial evaluation traces differ before M training")
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
            envs, states, observations, world = _training_worlds(spec, rollout, n)
            world_records.append(world)
            optimizer_before = optimizer_call_counts.copy()
            active_counter = b16._InferenceCounter(agent, n)
            counted = b15._CountingAgent(agent, summary["counts"], summary, active_counter)
            counted.optimizer_before = optimizer_before
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
            losses, sampler = _audited_update(
                agent, last_states, last_observations, dones, spec,
                summary["_active_training_rollout"], exposure,
            )
            summary["counts"]["updates"] += 1
            exposure["outer_updates_complete"] += 1
            exposure["rollouts_updated"] += 1
            finite(losses, "B18 training losses")
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
                raise ValueError("B18 optimizer calls disagree with actual recurrent minibatches")
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "n": n, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": optimizer_delta, "optimizer_total": optimizer_call_counts.copy(),
                "sampler": sampler, "parameter_motion": motion_parameters,
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["rollouts"].append(row)
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

        summary["training_reset_trace"] = _write_training_worlds(
            out / "training_reset_scenes.npz", world_records,
        )
        summary["checkpoints"].append(save_checkpoint(
            agent, out, spec.rollouts, config, launch_sha,
        ))
        summary["checkpoint_semantics"] = (
            "initial/final evaluation weights and normalizers only; no resume or optimizer-restoration claim"
        )
        _evaluate_stage(agent, arm, spec.rollouts, out, summary, spec, publish)
        if summary["counts"] != expected:
            raise ValueError(f"B18 {arm.key} exposure mismatch: {summary['counts']} != {expected}")
        expected_boundaries = spec.rollouts - 1 + int(schedule[0] != 6)
        if len(summary["boundaries"]) != expected_boundaries:
            raise ValueError("B18 missing atomic rollout boundary records")
        if any(optimizer_call_counts[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B18 optimized a disabled module")
        expected_minibatches = sum(row["sampler"]["recurrent_minibatches"] for row in summary["rollouts"])
        if optimizer_call_counts["discoverer_actor"] != expected_minibatches or \
                optimizer_call_counts["discoverer_critic"] != expected_minibatches:
            raise ValueError("B18 aggregate optimizer/minibatch accounting mismatch")
        if spec == PRODUCTION_SPEC and optimizer_call_counts["discoverer_actor"] != 101_250:
            raise ValueError("B18 production optimizer exposure differs from fixed contract")
        for name in ("discoverer_actor", "discoverer_critic"):
            if optimizer_call_counts[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B18 learner module did not move: {name}")
        summary["stage_readings"] = _stage_readings(summary["panels"], spec.rollouts)
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_config"] = b16._config_record(agent.config)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B18 source changed during arm execution")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
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
        if world_records and "training_reset_trace" not in summary:
            try:
                summary["training_reset_trace"] = _write_training_worlds(
                    out / "training_reset_scenes.npz", world_records,
                )
                summary["training_reset_trace"]["partial"] = True
            except Exception as trace_exc:
                summary["training_reset_trace_failure"] = (
                    f"{type(trace_exc).__name__}: {trace_exc}"
                )
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
        str(n): b15.file_sha256(out / arm / f"trace_stage00_n{n}.npz")
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
            raise ValueError("B18 final paired worlds differ")
        fq, mq = b15._quantities(f_row), b15._quantities(m_row)
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
        }
    signs = {
        f"D{n}{quantity}": by_n[str(n)]["final_M_minus_F"][quantity]["mean"] > 0
        for n in (5, 7) for quantity in ("J", "S")
    }
    return {"by_test_n": by_n, "primary_signs": signs,
            "primary_joint_directional_prediction_met": all(signs.values()),
            "cross_n_aggregate": None}


def _common_n6_training_world_identity(out: Path, schedules: Mapping[str, tuple[int, ...]]) -> dict[str, Any]:
    with np.load(out / "F/training_reset_scenes.npz", allow_pickle=False) as source:
        f = {name: source[name].copy() for name in source.files}
    with np.load(out / "M/training_reset_scenes.npz", allow_pickle=False) as source:
        m = {name: source[name].copy() for name in source.files}
    matched = []
    for index, (f_n, m_n) in enumerate(zip(schedules["F"], schedules["M"]), start=1):
        if f_n != 6 or m_n != 6:
            continue
        suffix = f"r{index:02d}_n6"
        fields = {
            "lane_world_seeds": np.array_equal(
                f["lane_world_seeds"][index - 1], m["lane_world_seeds"][index - 1]
            ),
            "states": np.array_equal(f["states"][index - 1], m["states"][index - 1]),
            "observations": np.array_equal(
                f[f"observations_{suffix}"], m[f"observations_{suffix}"]
            ),
            "uav_positions": np.array_equal(
                f[f"uav_positions_{suffix}"], m[f"uav_positions_{suffix}"]
            ),
            "user_positions": np.array_equal(
                f["user_positions"][index - 1], m["user_positions"][index - 1]
            ),
        }
        matched.append({"rollout": index, "fields": fields, "all_equal": all(fields.values())})
    if not matched or not all(row["all_equal"] for row in matched):
        raise ValueError("B18 common N6 training reset worlds differ between F and M")
    return {"matched_rollouts": matched, "all_equal": True}


def run_batch(
    out: Path, launch_sha: str, admission: Mapping[str, Any],
    spec: FitSpec = PRODUCTION_SPEC, *, command_start: float | None = None,
    schedules: Mapping[str, tuple[int, ...]] = SCHEDULES,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B18 output basename must be {TAG}")
    admission_owned = {
        "launch-manifest.json", "launch-status.json", "admission-preflight.json",
        "stdout.log", "stderr.log",
    }
    if out.exists():
        scientific = [path.name for path in out.iterdir() if path.name not in admission_owned]
        if scientific:
            raise ValueError(
                f"existing B18 scientific output; reconcile the original attempt: {scientific}"
            )
    if spec == PRODUCTION_SPEC and dict(schedules) != SCHEDULES:
        raise ValueError("B18 production schedules are fixed")
    if tuple(spec.test_ns) != EVALUATION_ORDER or tuple(spec.panels) != (0, spec.rollouts):
        raise ValueError("B18 requires the fixed evaluation order and initial/final stages")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    batch: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION, "tag": TAG,
        "seed": SEED, "launch_sha": launch_sha, "admission": dict(admission),
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
                out / name, ARMS[name], tuple(schedules[name]), launch_sha, admission, spec,
                command_start=command_start, expected_initialization=first_initialization,
                expected_initial_traces=first_initial_traces,
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
                first_initialization = arm_summary["initialization"]
                first_initial_traces = arm_summary["initial_evaluation_trace_sha256"]
            else:
                f_traces = _initial_trace_identity(out, "F")
                m_traces = _initial_trace_identity(out, "M")
                batch["initial_identity"] = {
                    "parameter_normalizer_digest_equal": first_initialization[
                        "parameter_normalizer_digest"
                    ] == arm_summary["initialization"]["parameter_normalizer_digest"],
                    "tensor_manifest_equal": first_initialization["tensor_manifest"] == arm_summary[
                        "initialization"
                    ]["tensor_manifest"],
                    "normalizers_equal": first_initialization["normalizers"] == arm_summary[
                        "initialization"
                    ]["normalizers"],
                    "full_initial_evaluation_trace_sha256_F": f_traces,
                    "full_initial_evaluation_trace_sha256_M": m_traces,
                    "full_initial_evaluation_traces_equal": f_traces == m_traces,
                }
                if not all(value for key, value in batch["initial_identity"].items()
                           if key.endswith("_equal")):
                    raise ValueError("B18 F/M initial identity or full trace mismatch")
                batch["common_n6_training_world_identity"] = _common_n6_training_world_identity(
                    out, schedules,
                )
        f_summary = json.loads((out / "F/summary.json").read_text(encoding="utf-8"))
        m_summary = json.loads((out / "M/summary.json").read_text(encoding="utf-8"))
        batch["readings"] = _paired_readings(f_summary, m_summary, spec.rollouts)
        aggregate_available_counts()
        batch["source_hashes_after"] = _source_hashes()
        batch["source_hashes_unchanged"] = batch["source_hashes_before"] == batch["source_hashes_after"]
        if not batch["source_hashes_unchanged"]:
            raise ValueError("B18 source changed during paired batch")
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
