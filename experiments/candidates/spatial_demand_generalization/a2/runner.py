"""Run the fixed A2 paired ordinary layout-training comparison."""
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

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.spatial_demand_generalization.a2.adapter import make_envs
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, FitSpec, config_dict
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.models import strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, NORMALIZERS, capture_parameters, digest_agent, finite, jsonable, model_modules,
    native_components, optimizer_counts, parameter_motion, preserve_rng,
    seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


OBJECT_ID = "s1_spatial_coverage_a2"
TAG = "s1_spatial_coverage_a2_s260925101"
SEED = 260925101
CONFIG_SEED = 260999999
TRAINING_WORLD_BASE = 261000000
FINAL_ROLLOUT = 45
EVALUATION_ORDER = ("uniform", "cluster", "hotspot")
WORLD_SEED_BASES = {"uniform": 262000000, "cluster": 262010000, "hotspot": 262020000}
SCHEDULES = {"U": (6,) * 45, "M": (6,) * 45}
PRODUCTION_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=(6,), eval_lanes=32,
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


ARMS = {name: Arm(name) for name in ("U", "M")}


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(), Path(__file__).resolve().with_name("__init__.py"),
        Path(__file__).resolve().with_name("adapter.py"),
        REPOSITORY_ROOT / "scripts/run_spatial_demand_generalization_a2.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/__init__.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b02/probe.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/ordinary_control_b13/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/local_ordinary_b16/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
        REPOSITORY_ROOT / "configs/config_1.py",
        REPOSITORY_ROOT / "envs/pettingzoo/env_adapter.py",
        REPOSITORY_ROOT / "envs/pettingzoo/scenario1.py",
        REPOSITORY_ROOT / "envs/pettingzoo/uav_env.py",
        REPOSITORY_ROOT / "hmasd/agent.py", REPOSITORY_ROOT / "hmasd/utils.py",
    )


def _source_hashes() -> dict[str, str]:
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): b15.file_sha256(path)
        for path in _source_paths()
    }


def save_a2_checkpoint(agent: Any, out: Path, rollout: int, config: Any,
                       launch_sha: str, arm: Arm) -> dict[str, Any]:
    """Persist evaluation weights with the A2 identity; there is no resume contract."""
    path = out / f"checkpoint_{rollout:02d}.pt"
    payload = {
        "schema": 1, "direction": "spatial_demand_generalization",
        "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key,
        "launch_sha": launch_sha, "rollout": rollout,
        "config": config_dict(config),
        "modules": {name: module.state_dict() for name, module in model_modules(agent).items()},
        "normalizers": {
            name: jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None else None
            for name in NORMALIZERS
        },
        "usage": "Evaluation weights; no training resume contract or optimizer restoration.",
    }
    partial = path.with_suffix(".pt.partial")
    with partial.open("wb") as stream:
        torch.save(payload, stream)
        stream.flush()
        os.fsync(stream.fileno())
    partial.replace(path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return {
        "path": path.name, "sha256": b15.file_sha256(path), "bytes": path.stat().st_size,
        "direction": payload["direction"], "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key,
        "rollout": rollout,
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


def training_families(arm: str, rollout_zero: int, lanes: int) -> tuple[str, ...]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm}")
    if arm == "U":
        return ("uniform",) * lanes
    # Reduced technical specs keep the 16-slot rule without changing production exposure.
    return tuple("uniform" if (lane + rollout_zero) % 16 < 8 else "cluster"
                 for lane in range(lanes))


def _training_worlds(spec: FitSpec, rollout: int, arm: Arm, training_base: int):
    rollout_zero = rollout - 1
    seeds = [training_base + 1000 * rollout_zero + lane for lane in range(spec.train_lanes)]
    families = training_families(arm.key, rollout_zero, spec.train_lanes)
    rng_before = b03._rng_digest()
    with preserve_rng():
        envs = make_envs(families, seeds, spec.horizon)
        pairs = [env.reset(seed=seed) for env, seed in zip(envs, seeds)]
    if b03._rng_digest() != rng_before:
        raise ValueError("A2 training world construction/reset changed learner RNG")
    b11._assert_native_envs(envs, 6)
    states = np.stack([info["state"] for observation, info in pairs])
    observations = np.stack([observation for observation, info in pairs])
    record = {
        "rollout": rollout, "n": 6, "lane_world_seeds": seeds,
        "families": np.asarray(families, dtype="U8"),
        "states": states.copy(), "observations": observations.copy(),
        "uav_positions": np.stack([np.asarray(env.env.env.uav_positions).copy() for env in envs]),
        "user_positions": np.stack([np.asarray(env.env.env.user_positions).copy() for env in envs]),
        "global_rng_before": rng_before, "global_rng_after": b03._rng_digest(),
        "explicit_seeded_reset": True,
    }
    return envs, states, observations, record


def _write_training_world(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    """Commit one complete reset before any environment step can run."""
    arrays = {
        name: np.asarray(value) for name, value in row.items()
        if name in ("rollout", "n", "lane_world_seeds", "families", "states", "observations",
                    "uav_positions", "user_positions", "global_rng_before", "global_rng_after")
    }
    for name, value in arrays.items():
        if value.dtype == object or (np.issubdtype(value.dtype, np.floating) and not np.isfinite(value).all()):
            raise ValueError(f"A2 invalid reset scene {name}")
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


def _write_partial_evaluation_trace(
    path: Path, trace: Mapping[str, np.ndarray], observed: np.ndarray, recorded: np.ndarray,
) -> dict[str, Any]:
    """Keep all available arrays while distinguishing observed and fully recorded transitions."""
    arrays = {name: np.asarray(value) for name, value in trace.items()}
    arrays["observed_transition_mask"] = observed
    arrays["recorded_transition_mask"] = recorded
    if any(value.dtype == object for value in arrays.values()):
        raise ValueError("A2 partial trace contains an object array")
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
    def finite_sums(value: np.ndarray, mask: np.ndarray) -> list[float | None]:
        totals = np.where(mask, value, 0).sum(axis=0)
        return [float(total) if np.isfinite(total) else None for total in totals]

    return {
        "path": path.relative_to(path.parent.parent).as_posix(),
        "sha256": b15.file_sha256(path), "bytes": path.stat().st_size,
        "format": "NumPy npz with allow_pickle=False",
        "observed_transitions": int(observed.sum()),
        "recorded_transitions": int(recorded.sum()),
        "observed_unrecorded_transitions": int((observed & ~recorded).sum()),
        "scalar_returns_observed_by_world": finite_sums(arrays["scalar_reward"], observed),
        "component_sums_recorded_by_world": {
            name: finite_sums(arrays[name], recorded)
            for name in COMPONENTS
        },
        "nonfinite_fields": [name for name, value in arrays.items()
                             if np.issubdtype(value.dtype, np.floating) and not np.isfinite(value).all()],
        "unobserved_array_rows_are_not_measurements": True,
    }


def collect_complete_episode(
    agent: Any, envs: list[Any], states: np.ndarray, observations: np.ndarray,
    input_dones: np.ndarray, arm: Arm, rollout: int, n: int,
    summary: dict[str, Any], spec: FitSpec,
    optimizer_before: Mapping[str, int], families: tuple[str, ...],
    *, training_step_hook: Callable[[dict[str, Any]], None] | None = None,
    first_transition_hook: Callable[[], None] | None = None,
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
        finite((raw_actions, data), "A2 training policy output")
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
            if not summary["fit_started"]:
                summary["fit_started"] = True
                summary["counts"]["fits"] = 1
            exposure = summary["training_exposure_by_n"][str(n)]
            exposure["team_steps"] += 1
            exposure["uav_steps"] += n
            exposure["episodes"] += int(done)
            family_exposure = summary["training_exposure_by_family"][families[lane]]
            family_exposure["team_steps"] += 1
            family_exposure["episodes"] += int(done)
            parts = native_components(info, reward, n)
            for name in COMPONENTS:
                component_sums[name][lane] += parts[name]
            b03._observe_motion(
                telemetry, native, before, raw_actions[lane], executed[lane], after,
                rollout=rollout, t=t, lane=lane, reward=reward, components=parts,
            )
            next_states.append(info["next_state"])
            next_observations.append(obs)
            if summary["counts"]["training_team_steps"] == 1 and first_transition_hook is not None:
                first_transition_hook()
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
            raise ValueError("A2 buffer did not retain raw sampled actions")
        if not np.array_equal(agent.rollout_buffer.log_probs[t], logprob_before):
            raise ValueError("A2 buffer did not retain original old log-probabilities")
        states, observations, dones = next_states, next_observations, next_dones
        steps += 1
        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
            raise ValueError("unexpected A2 training terminal boundary")
    if not dones.all():
        raise ValueError("A2 complete collector missed terminal boundary")
    telemetry["decision_step_indices_zero_based"] = sorted(decision_steps)
    telemetry["native_component_means_per_world"] = {
        name: (values / spec.horizon).tolist() for name, values in component_sums.items()
    }
    if not all((telemetry["diagnostic_rng_unchanged"], telemetry["policy_output_unchanged"],
                telemetry["old_logprob_unchanged"])):
        raise ValueError("A2 action mapping diagnostics changed policy/RNG data")
    if telemetry["executed_min"] < -1.0 or telemetry["executed_max"] > 1.0:
        raise ValueError("A2 clipped execution exceeded action bounds")
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
        raise ValueError("A2 actual PPO update yielded no recurrent minibatches")
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


def reset_world_runtime(agent: Any, lanes: int) -> dict[str, Any]:
    """Clear completed-world runtime without replacing the fixed-N learner or sampler."""
    if np.any(agent.rollout_buffer.env_lengths):
        raise ValueError("A2 runtime reset requires the consumed buffer to be cleared")
    model_before = digest_agent(agent)
    optimizer_before = b15._optimizer_state_digest(agent)
    optimizer_ids_before = _optimizer_ids(agent)
    sampler_before = b15._sampler_digest(agent)
    rng_before = b03._rng_digest()
    normalizers_before = _normalizers(agent)
    training_before = bool(agent.training)
    parameter_ids_before = {
        name: [id(parameter) for parameter in module.parameters()]
        for name, module in model_modules(agent).items()
    }
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
    parameter_ids_after = {
        name: [id(parameter) for parameter in module.parameters()]
        for name, module in model_modules(agent).items()
    }
    checks = {
        "runtime_reset_lanes": lanes,
        "parameter_objects_preserved": parameter_ids_before == parameter_ids_after,
        "parameter_values_preserved": model_before == digest_agent(agent),
        "optimizer_objects_preserved": optimizer_ids_before == _optimizer_ids(agent),
        "optimizer_state_preserved": optimizer_before == b15._optimizer_state_digest(agent),
        "sampler_rng_preserved": sampler_before == b15._sampler_digest(agent),
        "global_rng_preserved": rng_before == b03._rng_digest(),
        "normalizers_preserved": normalizers_before == _normalizers(agent),
        "training_mode_preserved": training_before == bool(agent.training),
        "buffer_empty": bool(not np.any(agent.rollout_buffer.env_lengths)),
        "hidden_state_fresh_allocation": agent.actor_hidden_np is None and agent.critic_hidden_np is None,
    }
    if not all(checks[key] for key in checks if key.endswith("_preserved")) or \
            not checks["buffer_empty"] or not checks["hidden_state_fresh_allocation"]:
        raise ValueError(f"A2 runtime boundary invariant failed: {checks}")
    return checks


def _evaluate_stage(
    learner: Any, arm: Arm, stage: int, out: Path, summary: dict[str, Any],
    spec: FitSpec, publish: Callable[[str], None], world_seed_bases: Mapping[int, int],
) -> None:
    isolation_before = b15._isolation_snapshot(learner, [])
    with preserve_rng():
        for family in EVALUATION_ORDER:
            n = 6
            base = world_seed_bases[family]
            seeds = list(range(base, base + spec.eval_lanes))
            seed_rng(base + 51)
            envs = make_envs((family,) * spec.eval_lanes, seeds, spec.horizon)
            target, inference, hooks = None, None, []
            trace = observed_mask = recorded_mask = None
            storage_calls = 0
            original_store = None
            row = {
                "status": "running", "arm": arm.key, "policy_stage": stage,
                "after_rollout": stage, "test_n": n, "family": family,
                "world_seeds": seeds,
                "runtime_seed": base + 51, "execution_law": "clip",
                "steps": 0, "episodes": 0, "resets": 0, "policy_step_calls": 0,
            }
            summary["panels"].append(row)
            publish(f"stage {stage} evaluation N={n} starting")
            try:
                b11._assert_native_envs(envs, n)
                config = b16.make_b16_config(arm, envs, replace(spec, train_n=n), expected_n=n)
                target = b16.build_local_agent(
                    config, str(out / "raw/evaluation_logs" / f"stage{stage:02d}_{family}"),
                )
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != digest_agent(learner):
                    raise ValueError("A2 evaluation target did not strictly load learner")
                normals_before = _normalizers(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("A2 evaluation attempted training storage")

                target.store_transition_batch = MethodType(reject_store, target)
                inference = b16._InferenceCounter(target, n)
                rng_before_reset = b03._rng_digest()
                pairs = [env.reset(seed=seed) for env, seed in zip(envs, seeds)]
                rng_after_reset = b03._rng_digest()
                if rng_after_reset != rng_before_reset:
                    raise ValueError("A2 evaluation reset changed evaluator RNG")
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
                reset_scene = {
                    "rollout": stage, "n": n, "lane_world_seeds": seeds,
                    "families": np.asarray((family,) * spec.eval_lanes, dtype="U8"),
                    "states": states.copy(), "observations": observations.copy(),
                    "uav_positions": np.stack([np.asarray(env.env.env.uav_positions).copy() for env in envs]),
                    "user_positions": np.stack([np.asarray(env.env.env.user_positions).copy() for env in envs]),
                    "global_rng_before": rng_before_reset, "global_rng_after": rng_after_reset,
                }
                scene_path = out / "raw" / f"evaluation_reset_stage{stage:02d}_{family}.npz"
                row["reset_scene"] = _write_training_world(scene_path, reset_scene)
                publish(f"stage {stage} {family} reset complete")
                trace = b15._new_panel_trace(spec, n)
                observed_mask = np.zeros((spec.horizon, spec.eval_lanes), dtype=bool)
                recorded_mask = np.zeros((spec.horizon, spec.eval_lanes), dtype=bool)
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
                        finite((raw, data), "A2 deterministic evaluation output")
                        inference.observe_choices(data)
                        raw_before = raw.copy()
                        executed = b03.map_training_actions(raw, "clip")
                        if not np.array_equal(raw, raw_before):
                            raise ValueError("A2 evaluation mapping changed raw actions")
                        trace["raw_actions"][t], trace["executed_actions"][t] = raw, executed
                        action_min = min(action_min, float(executed.min()))
                        action_max = max(action_max, float(executed.max()))
                        next_states, next_observations = [], []
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            observed_mask[t, lane] = True
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_uav_steps"] += n
                            summary["counts"]["evaluation_episodes"] += int(done)
                            trace["scalar_reward"][t, lane] = reward
                            trace["next_states"][t, lane] = info["next_state"]
                            trace["next_observations"][t, lane] = obs
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                sums[name][lane] += parts[name]
                            b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                            next_states.append(info["next_state"])
                            next_observations.append(obs)
                            dones[lane] = done
                            recorded_mask[t, lane] = True
                        states, observations = np.stack(next_states), np.stack(next_observations)
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected A2 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("A2 evaluation missed terminal boundary")
                means = {name: values / spec.horizon for name, values in sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
                if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    j, native_j, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("A2 native J/component identity failed")
                service = trace["served_user_counts"].mean(axis=0)
                eligibility = trace["eligible_user_counts"].mean(axis=0)
                unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
                if not np.allclose(service, 50 * means["coverage_reward"], atol=ATOL, rtol=RTOL) or not np.allclose(
                    unserved, eligibility - service, atol=ATOL, rtol=RTOL,
                ):
                    raise ValueError("A2 service identities failed")
                inference_counts = inference.finish(spec)
                if inference.data["set_snapshot_refresh_steps"] or inference.data["set_snapshot_lane_refreshes"]:
                    raise ValueError("A2 LOCAL1 evaluation used a central actor snapshot")
                after = digest_agent(target)
                if any(calls.values()) or storage_calls or after != before:
                    raise ValueError("A2 evaluation optimized, stored, or changed parameters")
                if _normalizers(target) != normals_before or np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("A2 evaluation changed normalizers or training storage")
                trace_path = out / "raw" / f"trace_stage{stage:02d}_{family}.npz"
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
                write_json(out / f"panel_stage{stage:02d}_{family}.json", row)
                publish(f"stage {stage} evaluation N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                if trace is not None and observed_mask is not None and recorded_mask is not None:
                    partial_path = out / "raw" / f"partial_trace_stage{stage:02d}_{family}.npz"
                    try:
                        row["partial_trace"] = _write_partial_evaluation_trace(
                            partial_path, trace, observed_mask, recorded_mask,
                        )
                    except Exception as trace_exc:
                        row["partial_trace_write_failure"] = (
                            f"{type(trace_exc).__name__}: {trace_exc}"
                        )
                else:
                    row["partial_trace_status"] = "unavailable_before_trace_allocation"
                write_json(out / f"panel_stage{stage:02d}_{family}.json", row)
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
        raise ValueError("A2 evaluation changed learner, optimizer, sampler, runtime, or RNG")


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
        "evaluation_uav_steps": stages * spec.eval_lanes * spec.horizon * len(EVALUATION_ORDER) * 6,
        "evaluation_episodes": stages * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_resets": stages * len(EVALUATION_ORDER) * spec.eval_lanes,
        "evaluation_policy_step_calls": stages * len(EVALUATION_ORDER) * spec.horizon,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _stage_readings(panels: list[dict[str, Any]], final_stage: int) -> dict[str, Any]:
    joined = {(row["policy_stage"], row["family"]): row for row in panels}
    expected = {(stage, n) for stage in (0, final_stage) for n in EVALUATION_ORDER}
    if set(joined) != expected:
        raise ValueError("A2 arm readings require exact stage0/final panels")
    by_n = {}
    for n in EVALUATION_ORDER:
        initial, final = joined[(0, n)], joined[(final_stage, n)]
        if initial["world_seeds"] != final["world_seeds"]:
            raise ValueError("A2 stage0/final worlds differ")
        if initial["initial_world_identity"] != final["initial_world_identity"]:
            raise ValueError("A2 stage0/final physical arrays differ")
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
    return {"by_family": by_n}


def run_arm(
    out: Path, arm: Arm, schedule: tuple[int, ...], launch_sha: str,
    admission: Mapping[str, Any], spec: FitSpec, *, command_start: float,
    expected_initialization: Mapping[str, Any] | None = None,
    expected_initial_traces: Mapping[str, str] | None = None,
    common_stage0_panels: list[dict[str, Any]] | None = None,
    training_base: int = TRAINING_WORLD_BASE,
    world_seed_bases: Mapping[int, int] = WORLD_SEED_BASES,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    if len(schedule) != spec.rollouts:
        raise ValueError("A2 arm schedule length mismatch")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    expected = _expected_arm_counts(schedule, spec, common_stage0=common_stage0_panels is not None)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key,
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
        "inherited_source_commit": "bfb4fd356a01024ef04c967c4768263f114e5a17",
        "training_exposure_by_family": {
            family: {"lanes_started": 0, "team_steps": 0, "episodes": 0}
            for family in ("uniform", "cluster")
        },
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
            config_envs = make_envs(("uniform",) * spec.train_lanes,
                                    [CONFIG_SEED + lane for lane in range(spec.train_lanes)], spec.horizon)
        try:
            seed_rng(arm.seed)
            config = b16.make_b16_config(arm, config_envs, replace(spec, train_n=6), expected_n=6)
        finally:
            for env in config_envs:
                env.close()
        summary["initial_config"] = b16._config_record(config)
        write_json(out / "config.json", {
            "object_id": OBJECT_ID, "tag": TAG, "arm": arm.key, "seed": arm.seed,
            "launch_sha": launch_sha, "schedule": list(schedule), "spec": vars(spec),
            "config": summary["initial_config"], "evaluation_order": list(EVALUATION_ORDER),
            "world_seed_bases": dict(world_seed_bases),
            "config_constructor_seed": CONFIG_SEED,
            "training_world_seed_formula": f"{training_base} + 1000 * (rollout - 1) + lane",
            "training_family_rule": "U all uniform; M uniform iff (lane + rollout_zero) % 16 < 8",
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
                    raise ValueError(f"A2 U/M initial {key} mismatch")
            summary["initialization_matches_U"] = True
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        optimizer_call_counts, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = optimizer_call_counts
        initial_parameters = capture_parameters(agent)
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        checkpoint = save_a2_checkpoint(agent, out / "raw", 0, config, launch_sha, arm)
        summary["checkpoints"].append({**checkpoint, "relative_to_arm": f"raw/{checkpoint['path']}"})
        if common_stage0_panels is None:
            _evaluate_stage(agent, arm, 0, out, summary, spec, publish, world_seed_bases)
            summary["initial_evaluation_trace_sha256"] = {
                str(n): b15.file_sha256(out / "raw" / f"trace_stage00_{n}.npz")
                for n in EVALUATION_ORDER
            }
        else:
            if expected_initialization is None or expected_initial_traces is None:
                raise ValueError("A2 common initial stage requires identity evidence")
            summary["common_stage0"] = {
                "owner": "U", "panel_paths": [f"../U/panel_stage00_{n}.json" for n in EVALUATION_ORDER],
                "trace_sha256": dict(expected_initial_traces), "reused_after_full_initial_identity": True,
                "new_environment_steps": 0,
            }
        summary["status"] = "training"
        publish("training starts")

        input_dones = np.zeros(spec.train_lanes, dtype=bool)
        for rollout, n in enumerate(schedule, start=1):
            rollout_start = time.perf_counter()
            exposure = summary["training_exposure_by_n"][str(n)]
            exposure["rollouts_started"] += 1
            optimizer_before = optimizer_call_counts.copy()
            envs, states, observations, world = _training_worlds(spec, rollout, arm, training_base)
            reset_path = out / "raw" / f"training_reset_r{rollout:02d}_n{n}.npz"
            reset_identity = _write_training_world(reset_path, world)
            summary.setdefault("training_reset_scenes", []).append(reset_identity)
            for family in world["families"]:
                summary["training_exposure_by_family"][str(family)]["lanes_started"] += 1
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
                    summary, spec, optimizer_before, tuple(map(str, world["families"])),
                    training_step_hook=training_step_hook,
                    first_transition_hook=lambda: publish(f"rollout {rollout} first transition"),
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
            finite(losses, "A2 training losses")
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
                raise ValueError("A2 optimizer calls disagree with actual recurrent minibatches")
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
                input_dones = np.ones(spec.train_lanes, dtype=bool)
                reset_checks = reset_world_runtime(agent, spec.train_lanes)
                summary["boundaries"].append({"after_rollout": rollout,
                    "next_entry_dones_all_true": bool(input_dones.all()),
                    **reset_checks})
            publish(f"rollout {rollout} N={n} updated")

        checkpoint = save_a2_checkpoint(agent, out / "raw", spec.rollouts, config, launch_sha, arm)
        summary["checkpoints"].append({**checkpoint, "relative_to_arm": f"raw/{checkpoint['path']}"})
        summary["checkpoint_semantics"] = (
            "initial/final evaluation weights and normalizers only; no resume or optimizer-restoration claim"
        )
        _evaluate_stage(agent, arm, spec.rollouts, out, summary, spec, publish, world_seed_bases)
        if summary["counts"] != expected:
            raise ValueError(f"A2 {arm.key} exposure mismatch: {summary['counts']} != {expected}")
        if spec == PRODUCTION_SPEC:
            family_counts = summary["training_exposure_by_family"]
            expected_family = {"U": (720, 0), "M": (360, 360)}[arm.key]
            if tuple(family_counts[f]["lanes_started"] for f in ("uniform", "cluster")) != expected_family:
                raise ValueError("A2 production family exposure differs from fixed schedule")
            if tuple(family_counts[f]["team_steps"] for f in ("uniform", "cluster")) != \
                    tuple(lanes * spec.horizon for lanes in expected_family):
                raise ValueError("A2 production family transitions differ from fixed schedule")
        expected_boundaries = spec.rollouts - 1
        if len(summary["boundaries"]) != expected_boundaries:
            raise ValueError("A2 missing atomic rollout boundary records")
        if any(optimizer_call_counts[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("A2 optimized a disabled module")
        expected_minibatches = sum(row["sampler"]["recurrent_minibatches"] for row in summary["rollouts"])
        if optimizer_call_counts["discoverer_actor"] != expected_minibatches or \
                optimizer_call_counts["discoverer_critic"] != expected_minibatches:
            raise ValueError("A2 aggregate optimizer/minibatch accounting mismatch")
        if spec == PRODUCTION_SPEC and optimizer_call_counts["discoverer_actor"] != 101_250:
            raise ValueError("A2 production optimizer exposure differs from fixed contract")
        for name in ("discoverer_actor", "discoverer_critic"):
            if optimizer_call_counts[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"A2 learner module did not move: {name}")
        summary["stage_readings"] = _stage_readings(
            (common_stage0_panels or []) + summary["panels"], spec.rollouts,
        )
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_config"] = b16._config_record(agent.config)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if not summary["source_hashes_unchanged"]:
            raise ValueError("A2 source changed during arm execution")
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
        str(n): b15.file_sha256(out / arm / "raw" / f"trace_stage00_{n}.npz")
        for n in EVALUATION_ORDER
    }


def _paired_readings(u_summary: Mapping[str, Any], m_summary: Mapping[str, Any],
                     final_stage: int) -> dict[str, Any]:
    initial = {row["family"]: row for row in u_summary["panels"] if row["policy_stage"] == 0}
    u_panels = {row["family"]: row for row in u_summary["panels"] if row["policy_stage"] == final_stage}
    m_panels = {row["family"]: row for row in m_summary["panels"] if row["policy_stage"] == final_stage}
    if set(initial) != set(u_panels) or set(initial) != set(m_panels) or set(initial) != set(EVALUATION_ORDER):
        raise ValueError("A2 missing exact family panels")
    by_family = {}
    for family in EVALUATION_ORDER:
        row0, u_row, m_row = initial[family], u_panels[family], m_panels[family]
        if not (row0["world_seeds"] == u_row["world_seeds"] == m_row["world_seeds"]):
            raise ValueError("A2 paired world seeds differ")
        if not (row0["initial_world_identity"] == u_row["initial_world_identity"] ==
                m_row["initial_world_identity"]):
            raise ValueError("A2 actual evaluation reset geometry differs")
        quantities = [b15._quantities(row) for row in (row0, u_row, m_row)]
        for q, row in zip(quantities, (row0, u_row, m_row)):
            q["height"] = np.asarray(row["uav_height_means_per_world"])
        q0, qu, qm = quantities
        worlds = row0["world_seeds"]
        by_family[family] = {
            "world_seeds": worlds,
            "initial": {key: b15._stats(value, worlds) for key, value in q0.items()},
            "final_U": {key: b15._stats(value, worlds) for key, value in qu.items()},
            "final_M": {key: b15._stats(value, worlds) for key, value in qm.items()},
            "final_M_minus_U": {key: b15._stats(qm[key] - qu[key], worlds) for key in qu},
            "U_minus_initial": {key: b15._stats(qu[key] - q0[key], worlds) for key in qu},
            "M_minus_initial": {key: b15._stats(qm[key] - q0[key], worlds) for key in qm},
            "adverse_J_or_S_worlds": [
                {"world_seed": worlds[i], "delta_J": float(qm["J"][i] - qu["J"][i]),
                 "delta_S": float(qm["S"][i] - qu["S"][i])}
                for i in range(len(worlds)) if qm["J"][i] <= qu["J"][i] or qm["S"][i] <= qu["S"][i]
            ],
        }
    signs = {quantity: by_family["hotspot"]["final_M_minus_U"][quantity]["mean"] > 0
             for quantity in ("J", "S")}
    return {"by_family": by_family, "primary_hotspot_signs": signs,
            "primary_joint_directional_prediction_met": all(signs.values())}


def _common_training_world_identity(out: Path, rollouts: int, lanes: int) -> dict[str, Any]:
    matches = []
    for index in range(1, rollouts + 1):
        name = f"training_reset_r{index:02d}_n6.npz"
        with np.load(out / "U/raw" / name, allow_pickle=False) as source:
            u = {key: source[key].copy() for key in source.files}
        with np.load(out / "M/raw" / name, allow_pickle=False) as source:
            m = {key: source[key].copy() for key in source.files}
        lane_mask = m["families"] == "uniform"
        if len(lane_mask) != lanes:
            raise ValueError("A2 training lane count changed")
        fields = {key: bool(np.array_equal(u[key][lane_mask], m[key][lane_mask]))
                  for key in ("lane_world_seeds", "states", "observations", "uav_positions", "user_positions")}
        matches.append({"rollout": index, "uniform_lanes": np.nonzero(lane_mask)[0].tolist(),
                        "fields": fields, "all_equal": all(fields.values())})
    if not matches or not all(row["all_equal"] for row in matches):
        raise ValueError("A2 common-family training reset worlds differ between U and M")
    return {"matched_rollouts": matches, "all_equal": True}


def run_batch(
    out: Path, launch_sha: str, admission: Mapping[str, Any],
    spec: FitSpec = PRODUCTION_SPEC, *, command_start: float | None = None,
    schedules: Mapping[str, tuple[int, ...]] = SCHEDULES,
    technical_seed: int | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"A2 output basename must be {TAG}")
    if launch_sha != admission.get("sha"):
        raise ValueError("A2 launch SHA disagrees with admission")
    if technical_seed is not None and spec == PRODUCTION_SPEC:
        raise ValueError("A2 production seed is fixed")
    if spec != PRODUCTION_SPEC and technical_seed is None:
        raise ValueError("A2 reduced technical spec needs a distinct technical seed")
    seed = SEED if technical_seed is None else int(technical_seed)
    if technical_seed == SEED:
        raise ValueError("A2 technical seed must differ from production")
    training_base = TRAINING_WORLD_BASE if technical_seed is None else TRAINING_WORLD_BASE + 10_000_000
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
                f"existing A2 scientific output; reconcile the original attempt: {scientific}"
            )
    if spec == PRODUCTION_SPEC and dict(schedules) != SCHEDULES:
        raise ValueError("A2 production schedules are fixed")
    if tuple(spec.test_ns) != (6,) or tuple(spec.panels) != (0, spec.rollouts):
        raise ValueError("A2 requires the fixed evaluation order and initial/final stages")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    batch: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": "spatial_demand_generalization", "tag": TAG,
        "seed": seed, "launch_sha": launch_sha, "admission": dict(admission),
        "status": "running", "arm_order": ["U", "M"],
        "arms": {name: {"status": "unstarted", "fit_started": False} for name in ("U", "M")},
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
        for index, name in enumerate(("U", "M")):
            batch["arms"][name] = {"status": "running", "fit_started": False}
            publish()
            code = run_arm(
                out / name, replace(ARMS[name], seed=seed), tuple(schedules[name]), launch_sha, admission, spec,
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
                    remaining = ("U", "M")[index + 1]
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
            if name == "U":
                first_initialization = json.loads(
                    (out / "U/raw/initialization.json").read_text(encoding="utf-8")
                )
                first_initial_traces = arm_summary["initial_evaluation_trace_sha256"]
                first_initial_panels = [row for row in arm_summary["panels"] if row["policy_stage"] == 0]
            else:
                f_traces = _initial_trace_identity(out, "U")
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
                    raise ValueError("A2 U/M initial identity or full trace mismatch")
                batch["common_training_world_identity"] = _common_training_world_identity(
                    out, spec.rollouts, spec.train_lanes,
                )
        u_summary = json.loads((out / "U/summary.json").read_text(encoding="utf-8"))
        m_summary = json.loads((out / "M/summary.json").read_text(encoding="utf-8"))
        if sum(row["counts"]["panels"] for row in (u_summary, m_summary)) != 9 and spec == PRODUCTION_SPEC:
            raise ValueError("A2 production requires exactly nine actual evaluation panels")
        batch["readings"] = _paired_readings(u_summary, m_summary, spec.rollouts)
        aggregate_available_counts()
        batch["source_hashes_after"] = _source_hashes()
        batch["source_hashes_unchanged"] = batch["source_hashes_before"] == batch["source_hashes_after"]
        if not batch["source_hashes_unchanged"]:
            raise ValueError("A2 source changed during paired batch")
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
