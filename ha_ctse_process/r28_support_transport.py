"""Reward-off paired transport probe for the frozen R28 support envelope."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

from .r27_g2_analysis import late_action_features
from .r27_g2_collector import (
    ACTION_DIM,
    BRANCH_STEPS,
    N_AGENTS,
    N_SKILLS,
    _assert_finite_evidence,
    _focal_failed,
    _require_observation,
    _state_from_info,
    prefix_policy_seed_for_reset,
    prefix_steps_for_reset,
    validate_agent_source_contract,
)
from .r27_g2_runtime import (
    R27G2ContractError,
    capture_environment_rng_state,
    capture_global_rng_state,
    capture_module_state,
    capture_runtime_snapshot,
    capture_value_norm_state,
    global_rng_states_equal,
    module_states_equal,
    restore_runtime_snapshot,
    rng_states_equal,
    value_norm_states_equal,
)
from .r28_g1_reward import DURATION_STEPS, STREAM_WIDTH


SCHEMA = "r28-forced-execution-pair-v1"
EXPERIMENT_ID = "EXP-20260713-r28-forced-execution-support-transport"
MODES = ("deterministic", "stochastic")
NOISE_SEED_BASE = 28_100
PAIR_COUNT = len(MODES) * N_SKILLS


@dataclass(frozen=True)
class R28SupportTransportArtifact:
    reset_id: int
    reset_seed: int
    prefix_policy_seed: int
    prefix_steps: int
    focal_agent: int
    natural_roster: np.ndarray
    policy_noise_seed: int
    epsilon: np.ndarray
    replay_equal: np.ndarray
    step_valid: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    focal_failure: np.ndarray
    global_rng_unchanged: np.ndarray
    pre_tanh_mean: np.ndarray
    log_standard_deviation: np.ndarray
    deterministic_action: np.ndarray
    executed_action: np.ndarray
    feature_valid: np.ndarray
    features: np.ndarray
    support: np.ndarray
    support_distance: np.ndarray
    support_threshold: np.ndarray
    support_distance_ratio: np.ndarray
    support_abs_z: np.ndarray
    module_state_equal: bool
    value_norm_state_equal: bool

    def write(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            destination,
            schema=np.asarray(SCHEMA),
            experiment_id=np.asarray(EXPERIMENT_ID),
            reset_id=np.asarray(self.reset_id, dtype=np.int64),
            reset_seed=np.asarray(self.reset_seed, dtype=np.int64),
            prefix_policy_seed=np.asarray(self.prefix_policy_seed, dtype=np.int64),
            prefix_steps=np.asarray(self.prefix_steps, dtype=np.int64),
            focal_agent=np.asarray(self.focal_agent, dtype=np.int64),
            natural_roster=self.natural_roster,
            modes=np.asarray(MODES),
            target_labels=np.arange(N_SKILLS, dtype=np.int64),
            duration_steps=np.asarray(DURATION_STEPS, dtype=np.int64),
            policy_noise_seed=np.asarray(self.policy_noise_seed, dtype=np.int64),
            epsilon=self.epsilon,
            replay_equal=self.replay_equal,
            step_valid=self.step_valid,
            terminated=self.terminated,
            truncated=self.truncated,
            focal_failure=self.focal_failure,
            global_rng_unchanged=self.global_rng_unchanged,
            pre_tanh_mean=self.pre_tanh_mean,
            log_standard_deviation=self.log_standard_deviation,
            deterministic_action=self.deterministic_action,
            executed_action=self.executed_action,
            feature_valid=self.feature_valid,
            features=self.features,
            support=self.support,
            support_distance=self.support_distance,
            support_threshold=self.support_threshold,
            support_distance_ratio=self.support_distance_ratio,
            support_abs_z=self.support_abs_z,
            module_state_equal=np.asarray(self.module_state_equal),
            value_norm_state_equal=np.asarray(self.value_norm_state_equal),
        )
        return destination

    @classmethod
    def read(cls, path: str | Path) -> "R28SupportTransportArtifact":
        with np.load(Path(path), allow_pickle=False) as payload:
            if str(payload["schema"].item()) != SCHEMA:
                raise R27G2ContractError("R28 transport artifact schema mismatch")
            if str(payload["experiment_id"].item()) != EXPERIMENT_ID:
                raise R27G2ContractError("R28 transport experiment identity mismatch")
            if tuple(str(item) for item in payload["modes"].tolist()) != MODES:
                raise R27G2ContractError("R28 transport mode order mismatch")
            values = {
                name: payload[name].copy()
                for name in (
                    "natural_roster",
                    "epsilon",
                    "replay_equal",
                    "step_valid",
                    "terminated",
                    "truncated",
                    "focal_failure",
                    "global_rng_unchanged",
                    "pre_tanh_mean",
                    "log_standard_deviation",
                    "deterministic_action",
                    "executed_action",
                    "feature_valid",
                    "features",
                    "support",
                    "support_distance",
                    "support_threshold",
                    "support_distance_ratio",
                    "support_abs_z",
                )
            }
            return cls(
                reset_id=int(payload["reset_id"].item()),
                reset_seed=int(payload["reset_seed"].item()),
                prefix_policy_seed=int(payload["prefix_policy_seed"].item()),
                prefix_steps=int(payload["prefix_steps"].item()),
                focal_agent=int(payload["focal_agent"].item()),
                policy_noise_seed=int(payload["policy_noise_seed"].item()),
                module_state_equal=bool(payload["module_state_equal"].item()),
                value_norm_state_equal=bool(payload["value_norm_state_equal"].item()),
                **values,
            )


def _allocate(reset_id: int, prefix_steps: int) -> dict[str, Any]:
    pair_shape = (len(MODES), N_SKILLS)
    step_shape = (*pair_shape, BRANCH_STEPS)
    action_shape = (*step_shape, N_AGENTS, ACTION_DIM)
    feature_shape = (*pair_shape, len(DURATION_STEPS))
    return {
        "reset_id": int(reset_id),
        "reset_seed": int(reset_id) + 1,
        "prefix_policy_seed": prefix_policy_seed_for_reset(reset_id),
        "prefix_steps": int(prefix_steps),
        "focal_agent": int(reset_id) % N_AGENTS,
        "natural_roster": np.full(N_AGENTS, -1, dtype=np.int64),
        "policy_noise_seed": NOISE_SEED_BASE + int(reset_id),
        "epsilon": np.zeros((BRANCH_STEPS, N_AGENTS, ACTION_DIM), dtype=np.float32),
        "replay_equal": np.zeros(pair_shape, dtype=np.bool_),
        "step_valid": np.zeros(step_shape, dtype=np.bool_),
        "terminated": np.zeros(step_shape, dtype=np.bool_),
        "truncated": np.zeros(step_shape, dtype=np.bool_),
        "focal_failure": np.zeros(step_shape, dtype=np.bool_),
        "global_rng_unchanged": np.zeros(step_shape, dtype=np.bool_),
        "pre_tanh_mean": np.full(action_shape, np.nan, dtype=np.float32),
        "log_standard_deviation": np.full(action_shape, np.nan, dtype=np.float32),
        "deterministic_action": np.full(action_shape, np.nan, dtype=np.float32),
        "executed_action": np.full(action_shape, np.nan, dtype=np.float32),
        "feature_valid": np.zeros(feature_shape, dtype=np.bool_),
        "features": np.full((*feature_shape, STREAM_WIDTH), np.nan, dtype=np.float32),
        "support": np.zeros(feature_shape, dtype=np.bool_),
        "support_distance": np.full(feature_shape, np.nan, dtype=np.float64),
        "support_threshold": np.full(feature_shape, np.nan, dtype=np.float64),
        "support_distance_ratio": np.full(feature_shape, np.nan, dtype=np.float64),
        "support_abs_z": np.full(
            (*feature_shape, STREAM_WIDTH), np.nan, dtype=np.float64
        ),
        "module_state_equal": False,
        "value_norm_state_equal": False,
    }


def _stochastic_action(live: dict[str, Any], epsilon: np.ndarray, device: Any) -> np.ndarray:
    mean = torch.as_tensor(live["pre_tanh_mean"], dtype=torch.float32, device=device)
    logstd = torch.as_tensor(
        live["log_standard_deviation"], dtype=torch.float32, device=device
    )
    noise = torch.as_tensor(epsilon, dtype=torch.float32, device=device)
    with torch.no_grad():
        action = torch.tanh(mean + torch.exp(logstd) * noise)
    result = action.detach().cpu().numpy().astype(np.float32)
    if result.shape != (N_AGENTS, ACTION_DIM) or not np.isfinite(result).all():
        raise R27G2ContractError("R28 stochastic transport action is malformed")
    return result


def collect_support_transport_reset(
    *,
    env_factory: Callable[[], Any],
    agent: Any,
    scorer: Any,
    reset_id: int,
) -> R28SupportTransportArtifact:
    """Collect one paired deterministic/stochastic forced-hold reset."""

    reset_id = int(reset_id)
    validate_agent_source_contract(agent)
    prefix_steps = prefix_steps_for_reset(reset_id)
    values = _allocate(reset_id, prefix_steps)
    initial_module_state = capture_module_state(agent)
    initial_value_norm_state = capture_value_norm_state(agent)

    prefix_env = env_factory()
    try:
        obs, info = prefix_env.reset(seed=values["reset_seed"])
        obs = _require_observation(obs)
        state = _state_from_info(info)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(N_AGENTS)]
        random.seed(values["prefix_policy_seed"])
        np.random.seed(values["prefix_policy_seed"])
        torch.manual_seed(values["prefix_policy_seed"])
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(values["prefix_policy_seed"])

        prefix_actions: list[np.ndarray] = []
        for step in range(prefix_steps):
            with torch.no_grad():
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=step,
                    k=10,
                    env_id=0,
                    deterministic=False,
                )
            action, _logp, _value = agent.act_low(
                obs, env_id=0, deterministic=False, state=state
            )
            action = np.asarray(action, dtype=np.float32)
            if action.shape != (N_AGENTS, ACTION_DIM):
                raise R27G2ContractError("R28 transport prefix action shape mismatch")
            prefix_actions.append(action.copy())
            next_obs, reward, terminated, truncated, next_info = prefix_env.step(action)
            _assert_finite_evidence(reward, f"transport.prefix[{step}].reward")
            if bool(terminated or truncated):
                raise R27G2ContractError("R28 transport prefix ended before branchpoint")
            obs = _require_observation(next_obs, obs_dim=obs.shape[1])
            state = _state_from_info(next_info)

        canonical_obs = obs.copy()
        canonical_state = state.copy()
        canonical_runtime = capture_runtime_snapshot(agent)
        canonical_environment_rng = capture_environment_rng_state(prefix_env)
        values["natural_roster"] = np.asarray(
            agent.active_skills[0], dtype=np.int64
        ).copy()
    finally:
        prefix_env.close()

    noise_rng = np.random.default_rng(values["policy_noise_seed"])
    values["epsilon"] = noise_rng.standard_normal(
        (BRANCH_STEPS, N_AGENTS, ACTION_DIM)
    ).astype(np.float32)

    for mode_id, mode in enumerate(MODES):
        for target_skill in range(N_SKILLS):
            env = env_factory()
            try:
                replay_obs, replay_info = env.reset(seed=values["reset_seed"])
                replay_obs = _require_observation(
                    replay_obs, obs_dim=canonical_obs.shape[1]
                )
                replay_state = _state_from_info(replay_info)
                for prefix_action in prefix_actions:
                    replay_obs, _reward, terminated, truncated, replay_info = env.step(
                        prefix_action
                    )
                    if bool(terminated or truncated):
                        raise R27G2ContractError(
                            "R28 transport replay ended before branchpoint"
                        )
                    replay_obs = _require_observation(
                        replay_obs, obs_dim=canonical_obs.shape[1]
                    )
                    replay_state = _state_from_info(replay_info)
                replay_equal = bool(
                    np.array_equal(replay_obs, canonical_obs)
                    and np.array_equal(replay_state, canonical_state)
                    and rng_states_equal(
                        capture_environment_rng_state(env), canonical_environment_rng
                    )
                )
                values["replay_equal"][mode_id, target_skill] = replay_equal
                if not replay_equal:
                    raise R27G2ContractError(
                        "R28 transport branchpoint replay is not exact"
                    )
                restore_runtime_snapshot(agent, canonical_runtime)

                for step in range(BRANCH_STEPS):
                    global_before = capture_global_rng_state()
                    live = agent.r27_g2_audit_step(
                        replay_obs,
                        env_id=0,
                        state=replay_state,
                        focal_agent=values["focal_agent"],
                        focal_skill=target_skill,
                        focal_inactive_film=False,
                    )
                    deterministic = np.asarray(
                        live["deterministic_action"], dtype=np.float32
                    )
                    executed = (
                        deterministic
                        if mode == "deterministic"
                        else _stochastic_action(
                            live, values["epsilon"][step], agent.device
                        )
                    )
                    values["pre_tanh_mean"][mode_id, target_skill, step] = live[
                        "pre_tanh_mean"
                    ]
                    values["log_standard_deviation"][mode_id, target_skill, step] = live[
                        "log_standard_deviation"
                    ]
                    values["deterministic_action"][mode_id, target_skill, step] = deterministic
                    values["executed_action"][mode_id, target_skill, step] = executed

                    next_obs, reward, terminated, truncated, next_info = env.step(executed)
                    _assert_finite_evidence(
                        reward,
                        f"transport.{mode}.label[{target_skill}].step[{step}].reward",
                    )
                    values["step_valid"][mode_id, target_skill, step] = True
                    values["terminated"][mode_id, target_skill, step] = bool(terminated)
                    values["truncated"][mode_id, target_skill, step] = bool(truncated)
                    values["focal_failure"][mode_id, target_skill, step] = _focal_failed(
                        next_info, values["focal_agent"]
                    )
                    values["global_rng_unchanged"][mode_id, target_skill, step] = (
                        global_rng_states_equal(
                            global_before, capture_global_rng_state()
                        )
                    )
                    if not values["global_rng_unchanged"][
                        mode_id, target_skill, step
                    ]:
                        raise R27G2ContractError(
                            "R28 transport branch consumed global RNG state"
                        )
                    if bool(
                        terminated
                        or truncated
                        or values["focal_failure"][mode_id, target_skill, step]
                    ):
                        break
                    replay_obs = _require_observation(
                        next_obs, obs_dim=canonical_obs.shape[1]
                    )
                    replay_state = _state_from_info(next_info)
            finally:
                env.close()

    row_slots: list[tuple[int, int, int]] = []
    row_features: list[np.ndarray] = []
    for mode_id in range(len(MODES)):
        for target_skill in range(N_SKILLS):
            for duration_id, endpoint in enumerate(DURATION_STEPS):
                if not bool(
                    np.all(values["step_valid"][mode_id, target_skill, :endpoint])
                    and not np.any(
                        values["terminated"][mode_id, target_skill, :endpoint]
                        | values["truncated"][mode_id, target_skill, :endpoint]
                        | values["focal_failure"][mode_id, target_skill, :endpoint]
                    )
                ):
                    continue
                window = values["deterministic_action"][
                    mode_id,
                    target_skill,
                    endpoint - 10 : endpoint,
                    values["focal_agent"],
                ]
                feature = late_action_features(window).astype(np.float32)
                values["feature_valid"][mode_id, target_skill, duration_id] = True
                values["features"][mode_id, target_skill, duration_id] = feature
                row_slots.append((mode_id, target_skill, duration_id))
                row_features.append(feature)

    if not row_features:
        raise R27G2ContractError("R28 transport reset produced no complete windows")
    labels = np.asarray([slot[1] for slot in row_slots], dtype=np.int64)
    durations = np.asarray([slot[2] for slot in row_slots], dtype=np.int64)
    support_result = scorer.evaluate_support(
        np.asarray(row_features, dtype=np.float32), labels, durations
    )
    for row, (mode_id, target_skill, duration_id) in enumerate(row_slots):
        slot = (mode_id, target_skill, duration_id)
        values["support"][slot] = support_result.support[row]
        values["support_distance"][slot] = support_result.distances[row]
        values["support_threshold"][slot] = support_result.thresholds[row]
        values["support_distance_ratio"][slot] = support_result.distance_ratio[row]
        values["support_abs_z"][slot] = support_result.abs_z[row]

    restore_runtime_snapshot(agent, canonical_runtime)
    values["module_state_equal"] = module_states_equal(
        initial_module_state, capture_module_state(agent)
    )
    values["value_norm_state_equal"] = value_norm_states_equal(
        initial_value_norm_state, capture_value_norm_state(agent)
    )
    if not (values["module_state_equal"] and values["value_norm_state_equal"]):
        raise R27G2ContractError("R28 transport probe mutated model or ValueNorm state")
    return R28SupportTransportArtifact(**values)


__all__ = [
    "EXPERIMENT_ID",
    "MODES",
    "R28SupportTransportArtifact",
    "SCHEMA",
    "collect_support_transport_reset",
]
