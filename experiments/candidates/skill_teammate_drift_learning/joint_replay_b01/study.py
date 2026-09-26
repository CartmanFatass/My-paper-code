"""Finite tabular host for the B01 joint-trajectory replay comparison.

The module has no publication or admission side effects.  The direction runner owns
those boundaries; this file owns only collection, replay, and exact evaluation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Mapping

import numpy as np


OBJECT = "STDL_JOINT_REPLAY_B01"
ARMS = ("joint_is", "fingerprint", "recent", "uniform")
LEFT = 0
RIGHT = 1
HOLD = 0
MOVE_LEFT = -1
MOVE_RIGHT = 1
N_POSITIONS = 5
N_JOINT_STATES = N_POSITIONS * N_POSITIONS


@dataclass(frozen=True)
class Config:
    """Frozen B01 defaults; ordinary smaller values support correctness fixtures."""

    version_names: tuple[str, ...] = ("A", "B")
    ego_move_probabilities: tuple[float, ...] = (0.8, 0.6)
    teammate_right_probabilities: tuple[float, ...] = (0.8, 0.2)
    teammate_move_probability: float = 0.8
    version_schedule: tuple[str, ...] = ("A", "B", "A", "B", "A")
    episodes_per_block: int = 60
    macros_per_episode: int = 10
    macro_duration: int = 3
    gamma: float = 0.95
    epsilon: float = 0.2
    alpha: float = 0.025
    batch_size: int = 32
    recent_capacity: int = 300
    evaluation_interval: int = 10
    primary_evaluation_episodes: tuple[int, ...] = (
        70, 80, 90, 130, 140, 150, 190, 200, 210, 250, 260, 270,
    )
    initialization: str = "zero"

    @property
    def total_episodes(self) -> int:
        return len(self.version_schedule) * self.episodes_per_block

    @property
    def total_macros(self) -> int:
        return self.total_episodes * self.macros_per_episode


def validate_config(config: Config) -> None:
    n_versions = len(config.version_names)
    if n_versions == 0 or len(set(config.version_names)) != n_versions:
        raise ValueError("version_names must be nonempty and unique")
    if len(config.ego_move_probabilities) != n_versions:
        raise ValueError("one ego move probability is required per version")
    if len(config.teammate_right_probabilities) != n_versions:
        raise ValueError("one teammate goal probability is required per version")
    if not config.version_schedule or any(
        name not in config.version_names for name in config.version_schedule
    ):
        raise ValueError("version_schedule must contain only named versions")
    probability_fields = (
        *config.ego_move_probabilities,
        *config.teammate_right_probabilities,
        config.teammate_move_probability,
        config.epsilon,
    )
    if any(not 0.0 < value < 1.0 for value in probability_fields):
        raise ValueError("all behavior and exploration probabilities need full support")
    if config.episodes_per_block <= 0 or config.macros_per_episode <= 0:
        raise ValueError("episode and macro counts must be positive")
    if config.macro_duration <= 0 or config.batch_size <= 0:
        raise ValueError("macro duration and batch size must be positive")
    if config.recent_capacity <= 0 or config.evaluation_interval <= 0:
        raise ValueError("replay and evaluation intervals must be positive")
    if not 0.0 < config.gamma <= 1.0 or config.alpha <= 0.0:
        raise ValueError("gamma and alpha must be positive, with gamma at most one")
    if config.alpha * config.batch_size > 0.8 + 1e-15:
        raise ValueError("alpha * batch_size must preserve the B01 0.8 step bound")
    if config.initialization not in ("zero", "reward_upper"):
        raise ValueError("initialization must be 'zero' or 'reward_upper'")
    if any(
        episode <= 0
        or episode > config.total_episodes
        or episode % config.evaluation_interval
        for episode in config.primary_evaluation_episodes
    ):
        raise ValueError("primary episodes must be scheduled evaluation panels")


def version_index(config: Config, episode: int) -> int:
    if episode < 0 or episode >= config.total_episodes:
        raise IndexError("episode outside configured schedule")
    name = config.version_schedule[episode // config.episodes_per_block]
    return config.version_names.index(name)


def primitive_action_probability(
    position: int, goal: int, action: int, move_probability: float
) -> float:
    """Probability of an actual primitive action under one endpoint controller."""
    if position not in range(N_POSITIONS) or goal not in (LEFT, RIGHT):
        raise ValueError("invalid position or endpoint goal")
    if not 0.0 <= move_probability <= 1.0:
        raise ValueError("move_probability must lie in [0, 1]")
    target = 0 if goal == LEFT else N_POSITIONS - 1
    if position == target:
        return 1.0 if action == HOLD else 0.0
    move = MOVE_LEFT if goal == LEFT else MOVE_RIGHT
    if action == move:
        return move_probability
    if action == HOLD:
        return 1.0 - move_probability
    return 0.0


def apply_primitive_action(position: int, action: int) -> int:
    if position not in range(N_POSITIONS) or action not in (MOVE_LEFT, HOLD, MOVE_RIGHT):
        raise ValueError("invalid primitive state/action")
    next_position = position + action
    if next_position not in range(N_POSITIONS):
        raise ValueError("primitive action leaves the line")
    return next_position


def native_service_reward(ego_position: int, teammate_position: int) -> float:
    """Half the number of distinct endpoints occupied after a primitive move."""
    occupied = int(ego_position == 0 or teammate_position == 0)
    occupied += int(
        ego_position == N_POSITIONS - 1 or teammate_position == N_POSITIONS - 1
    )
    return 0.5 * occupied


def trajectory_likelihood(
    *,
    teammate_goal: int,
    ego_goal: int,
    pre_positions: np.ndarray,
    primitive_actions: np.ndarray,
    ego_move_probability: float,
    teammate_right_probability: float,
    teammate_move_probability: float,
) -> dict[str, float]:
    """Evaluate every factor in the recorded conditional macro likelihood."""
    positions = np.asarray(pre_positions)
    actions = np.asarray(primitive_actions)
    if positions.shape != actions.shape or positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError("pre_positions/actions must both have shape [ticks, 2]")
    if teammate_goal not in (LEFT, RIGHT) or ego_goal not in (LEFT, RIGHT):
        raise ValueError("macro goals must be LEFT or RIGHT")
    goal_probability = (
        teammate_right_probability
        if teammate_goal == RIGHT
        else 1.0 - teammate_right_probability
    )
    ego_probability = 1.0
    teammate_probability = 1.0
    for tick in range(positions.shape[0]):
        ego_probability *= primitive_action_probability(
            int(positions[tick, 0]), ego_goal, int(actions[tick, 0]), ego_move_probability
        )
        teammate_probability *= primitive_action_probability(
            int(positions[tick, 1]),
            teammate_goal,
            int(actions[tick, 1]),
            teammate_move_probability,
        )
    total = goal_probability * ego_probability * teammate_probability
    return {
        "teammate_goal": float(goal_probability),
        "ego_primitive": float(ego_probability),
        "teammate_primitive": float(teammate_probability),
        "total": float(total),
    }


def primitive_transition_matrix(
    ego_goal: int,
    teammate_goal: int,
    ego_move_probability: float,
    teammate_move_probability: float,
) -> np.ndarray:
    """One-tick joint-position transition matrix for fixed endpoint goals."""
    matrix = np.zeros((N_JOINT_STATES, N_JOINT_STATES), dtype=np.float64)
    for ego_position in range(N_POSITIONS):
        for teammate_position in range(N_POSITIONS):
            row = ego_position * N_POSITIONS + teammate_position
            for ego_action in (MOVE_LEFT, HOLD, MOVE_RIGHT):
                ego_probability = primitive_action_probability(
                    ego_position, ego_goal, ego_action, ego_move_probability
                )
                if ego_probability == 0.0:
                    continue
                for teammate_action in (MOVE_LEFT, HOLD, MOVE_RIGHT):
                    teammate_probability = primitive_action_probability(
                        teammate_position,
                        teammate_goal,
                        teammate_action,
                        teammate_move_probability,
                    )
                    if teammate_probability == 0.0:
                        continue
                    next_ego = apply_primitive_action(ego_position, ego_action)
                    next_teammate = apply_primitive_action(
                        teammate_position, teammate_action
                    )
                    column = next_ego * N_POSITIONS + next_teammate
                    matrix[row, column] += ego_probability * teammate_probability
    if not np.allclose(matrix.sum(axis=1), 1.0, rtol=0.0, atol=2e-16):
        raise RuntimeError("primitive transition matrix is not stochastic")
    return matrix


@lru_cache(maxsize=None)
def macro_model(config: Config, current_version: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-ego-goal/per-teammate-goal exact three-tick matrices and rewards.

    The teammate goal axis is deliberately retained.  Callers mix that axis once
    per macro segment, after composing all primitive ticks.
    """
    validate_config(config)
    if current_version not in range(len(config.version_names)):
        raise ValueError("unknown version index")
    transition = np.zeros(
        (2, 2, N_JOINT_STATES, N_JOINT_STATES), dtype=np.float64
    )
    reward = np.zeros((2, 2, N_JOINT_STATES), dtype=np.float64)
    post_reward = np.array(
        [native_service_reward(i // N_POSITIONS, i % N_POSITIONS)
         for i in range(N_JOINT_STATES)],
        dtype=np.float64,
    )
    ego_probability = config.ego_move_probabilities[current_version]
    for ego_goal in (LEFT, RIGHT):
        for teammate_goal in (LEFT, RIGHT):
            one_tick = primitive_transition_matrix(
                ego_goal,
                teammate_goal,
                ego_probability,
                config.teammate_move_probability,
            )
            distribution = np.eye(N_JOINT_STATES, dtype=np.float64)
            accumulated = np.zeros(N_JOINT_STATES, dtype=np.float64)
            discount = 1.0
            for _tick in range(config.macro_duration):
                distribution = distribution @ one_tick
                accumulated += discount * (distribution @ post_reward)
                discount *= config.gamma
            transition[ego_goal, teammate_goal] = distribution
            reward[ego_goal, teammate_goal] = accumulated
    transition.setflags(write=False)
    reward.setflags(write=False)
    return transition, reward


@lru_cache(maxsize=None)
def _mixed_macro_model(
    config: Config, current_version: int
) -> tuple[np.ndarray, np.ndarray]:
    transition, reward = macro_model(config, current_version)
    right_probability = config.teammate_right_probabilities[current_version]
    goal_probabilities = np.array(
        [1.0 - right_probability, right_probability], dtype=np.float64
    )
    mixed_transition = np.einsum("g,agij->aij", goal_probabilities, transition)
    mixed_reward = np.einsum("g,agi->ai", goal_probabilities, reward)
    mixed_transition.setflags(write=False)
    mixed_reward.setflags(write=False)
    return mixed_transition, mixed_reward


def greedy_policy(q_values: np.ndarray) -> np.ndarray:
    """Left-tie-breaking greedy policy for one unconditioned Q table."""
    q_values = np.asarray(q_values)
    if q_values.ndim != 4 or q_values.shape[1:] != (5, 5, 2):
        raise ValueError("q_values must have shape [remaining, 5, 5, 2]")
    return np.argmax(q_values, axis=-1).astype(np.int8)


def exact_policy_evaluation(
    q_values: np.ndarray, config: Config, current_version: int
) -> dict[str, Any]:
    """Evaluate the frozen greedy high-level policy by finite backward DP."""
    q_values = np.asarray(q_values, dtype=np.float64)
    expected_shape = (config.macros_per_episode + 1, 5, 5, 2)
    if q_values.shape != expected_shape:
        raise ValueError(f"q_values must have shape {expected_shape}")
    policy = greedy_policy(q_values)
    transition, reward = _mixed_macro_model(config, current_version)
    continuation = config.gamma ** config.macro_duration
    values = np.zeros((config.macros_per_episode + 1, N_JOINT_STATES))
    for remaining in range(1, config.macros_per_episode + 1):
        actions = policy[remaining].reshape(-1)
        for state in range(N_JOINT_STATES):
            action = int(actions[state])
            values[remaining, state] = reward[action, state] + continuation * (
                transition[action, state] @ values[remaining - 1]
            )
    discounted_return = float(values[config.macros_per_episode].mean())
    primitive_horizon = config.macros_per_episode * config.macro_duration
    normalizer = sum(config.gamma ** tick for tick in range(primitive_horizon))
    return {
        "discounted_service_return": discounted_return,
        "normalized_service_return": discounted_return / normalizer,
        "policy": policy.tolist(),
        "values": values,
    }


def bellman_residual(
    q_values: np.ndarray, config: Config, current_version: int
) -> tuple[float, float]:
    """Mean and maximum absolute current-version optimality residual."""
    q_values = np.asarray(q_values, dtype=np.float64)
    transition, reward = _mixed_macro_model(config, current_version)
    continuation = config.gamma ** config.macro_duration
    residuals = []
    for remaining in range(1, config.macros_per_episode + 1):
        next_values = q_values[remaining - 1].max(axis=-1).reshape(-1)
        for action in (LEFT, RIGHT):
            target = reward[action] + continuation * (transition[action] @ next_values)
            observed = q_values[remaining, :, :, action].reshape(-1)
            residuals.append(np.abs(observed - target))
    combined = np.concatenate(residuals)
    return float(combined.mean()), float(combined.max())


def exact_optimal_evaluation(config: Config, current_version: int) -> dict[str, Any]:
    """Backward-DP informational optimum; the learner never receives this model."""
    transition, reward = _mixed_macro_model(config, current_version)
    continuation = config.gamma ** config.macro_duration
    values = np.zeros((config.macros_per_episode + 1, N_JOINT_STATES))
    policy = np.zeros(
        (config.macros_per_episode + 1, N_JOINT_STATES), dtype=np.int8
    )
    for remaining in range(1, config.macros_per_episode + 1):
        action_values = reward + continuation * np.einsum(
            "aij,j->ai", transition, values[remaining - 1]
        )
        policy[remaining] = np.argmax(action_values, axis=0).astype(np.int8)
        values[remaining] = action_values.max(axis=0)
    discounted_return = float(values[config.macros_per_episode].mean())
    primitive_horizon = config.macros_per_episode * config.macro_duration
    normalizer = sum(config.gamma ** tick for tick in range(primitive_horizon))
    return {
        "discounted_service_return": discounted_return,
        "normalized_service_return": discounted_return / normalizer,
        "policy": policy.reshape(config.macros_per_episode + 1, 5, 5).tolist(),
        "values": values,
    }


def common_random_slots(config: Config, seed: int) -> dict[str, np.ndarray]:
    """Generate arm-invariant addressed environment and exploration randomness."""
    validate_config(config)
    roots = np.random.SeedSequence(int(seed)).spawn(5)
    reset_rng, goal_rng, explore_rng, explore_action_rng, primitive_rng = (
        np.random.default_rng(root) for root in roots
    )
    episode_shape = (config.total_episodes, config.macros_per_episode)
    return {
        "reset_positions": reset_rng.integers(
            0, N_POSITIONS, size=(config.total_episodes, 2), dtype=np.int8
        ),
        "teammate_goal_uniform": goal_rng.random(episode_shape),
        "exploration_uniform": explore_rng.random(episode_shape),
        "exploration_action_uniform": explore_action_rng.random(episode_shape),
        # Last axes are agent and that agent's selected endpoint action.
        "primitive_uniform": primitive_rng.random(
            (*episode_shape, config.macro_duration, 2, 2)
        ),
    }


def replay_eligible_indices(
    arm: str,
    collection_versions: np.ndarray,
    *,
    current_version: int,
    current_index: int,
    recent_capacity: int,
) -> np.ndarray:
    """Return the arm's lawful replay population after collecting current_index."""
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    versions = np.asarray(collection_versions)
    if current_index < 0 or current_index >= len(versions):
        raise IndexError("current_index outside collected versions")
    if arm == "fingerprint":
        eligible = np.flatnonzero(
            versions[: current_index + 1] == current_version
        ).astype(np.int32)
    elif arm == "recent":
        low = max(0, current_index + 1 - recent_capacity)
        eligible = np.arange(low, current_index + 1, dtype=np.int32)
    else:
        eligible = np.arange(current_index + 1, dtype=np.int32)
    if eligible.size == 0:
        raise RuntimeError("replay population is empty")
    return eligible


def simultaneous_q_update(
    q_values: np.ndarray,
    *,
    remaining: np.ndarray,
    ego_position: np.ndarray,
    teammate_position: np.ndarray,
    action: np.ndarray,
    reward: np.ndarray,
    next_remaining: np.ndarray,
    next_ego_position: np.ndarray,
    next_teammate_position: np.ndarray,
    terminal: np.ndarray,
    weights: np.ndarray,
    alpha: float,
    continuation_discount: float,
    table_indices: np.ndarray | None = None,
) -> None:
    """Apply pre-update TD targets and grouped simultaneous Q-entry updates.

    ``weights`` are already globally minibatch-normalized.  Their TD
    contributions are summed, then divided by each entry's *unweighted*
    occurrence count.  In particular, a singleton entry keeps its weight.
    """
    arrays = [
        remaining, ego_position, teammate_position, action, reward,
        next_remaining, next_ego_position, next_teammate_position, terminal, weights,
    ]
    size = len(np.asarray(remaining))
    if any(len(np.asarray(value)) != size for value in arrays):
        raise ValueError("all minibatch fields must have equal length")
    if size == 0 or not np.all(np.isfinite(weights)) or np.any(np.asarray(weights) < 0):
        raise ValueError("weights must be a nonempty finite nonnegative vector")
    fingerprint = table_indices is not None
    if fingerprint and len(np.asarray(table_indices)) != size:
        raise ValueError("table_indices must match the minibatch")

    sums: dict[tuple[int, ...], float] = {}
    counts: dict[tuple[int, ...], int] = {}
    for index in range(size):
        table = int(table_indices[index]) if fingerprint else None
        if fingerprint:
            old = q_values[table]
        else:
            old = q_values
        if bool(terminal[index]):
            bootstrap = 0.0
        else:
            bootstrap = float(
                old[
                    int(next_remaining[index]),
                    int(next_ego_position[index]),
                    int(next_teammate_position[index]),
                ].max()
            )
        key_tail = (
            int(remaining[index]), int(ego_position[index]),
            int(teammate_position[index]), int(action[index]),
        )
        key = ((table,) + key_tail) if fingerprint else key_tail
        old_value = float(old[key_tail])
        target = float(reward[index]) + continuation_discount * bootstrap
        contribution = float(weights[index]) * (target - old_value)
        sums[key] = sums.get(key, 0.0) + contribution
        counts[key] = counts.get(key, 0) + 1
    for key, contribution in sums.items():
        q_values[key] += alpha * contribution / counts[key]


def _transition_storage(config: Config) -> dict[str, np.ndarray]:
    count = config.total_macros
    duration = config.macro_duration
    return {
        "episode": np.empty(count, dtype=np.int16),
        "macro_in_episode": np.empty(count, dtype=np.int8),
        "global_macro": np.arange(count, dtype=np.int32),
        "collection_version": np.empty(count, dtype=np.int8),
        "episode_reset_positions": np.empty(
            (config.total_episodes, 2), dtype=np.int8
        ),
        "teammate_goal_uniform": np.empty(count, dtype=np.float64),
        "exploration_uniform": np.empty(count, dtype=np.float64),
        "exploration_action_uniform": np.empty(count, dtype=np.float64),
        "primitive_uniform": np.empty(
            (count, duration, 2, 2), dtype=np.float64
        ),
        "remaining": np.empty(count, dtype=np.int8),
        "start_positions": np.empty((count, 2), dtype=np.int8),
        "ego_goal": np.empty(count, dtype=np.int8),
        "teammate_goal": np.empty(count, dtype=np.int8),
        "teammate_goal_behavior_probability": np.empty(count, dtype=np.float64),
        "pre_positions": np.empty((count, duration, 2), dtype=np.int8),
        "primitive_actions": np.empty((count, duration, 2), dtype=np.int8),
        "post_positions": np.empty((count, duration, 2), dtype=np.int8),
        "primitive_behavior_probabilities": np.empty(
            (count, duration, 2), dtype=np.float64
        ),
        "primitive_rewards": np.empty((count, duration), dtype=np.float64),
        "macro_reward": np.empty(count, dtype=np.float64),
        "next_positions": np.empty((count, 2), dtype=np.int8),
        "next_remaining": np.empty(count, dtype=np.int8),
        "terminal": np.empty(count, dtype=np.bool_),
        "behavior_ego_primitive_likelihood": np.empty(count, dtype=np.float64),
        "behavior_teammate_primitive_likelihood": np.empty(count, dtype=np.float64),
        "behavior_trajectory_likelihood": np.empty(count, dtype=np.float64),
        "replay_indices": np.empty((count, config.batch_size), dtype=np.int32),
        "replay_sample_versions": np.empty((count, config.batch_size), dtype=np.int8),
        "replay_sample_ages": np.empty((count, config.batch_size), dtype=np.int32),
        "replay_raw_ratios": np.empty((count, config.batch_size), dtype=np.float64),
        "replay_normalized_weights": np.empty(
            (count, config.batch_size), dtype=np.float64
        ),
        "replay_table_indices": np.full(
            (count, config.batch_size), -1, dtype=np.int8
        ),
    }


def _selected_q(q_values: np.ndarray, arm: str, current_version: int) -> np.ndarray:
    return q_values[current_version] if arm == "fingerprint" else q_values


def initialize_q_values(config: Config, arm: str) -> np.ndarray:
    """Construct the one-time Q initialization without consulting the host model."""
    validate_config(config)
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    q_shape = (config.macros_per_episode + 1, 5, 5, 2)
    base = np.zeros(q_shape, dtype=np.float64)
    if config.initialization == "reward_upper":
        for remaining in range(1, config.macros_per_episode + 1):
            primitive_horizon = config.macro_duration * remaining
            upper = sum(config.gamma ** tick for tick in range(primitive_horizon))
            base[remaining].fill(upper)
    if arm == "fingerprint":
        return np.stack(
            [base.copy() for _version in config.version_names], axis=0
        )
    return base


def collection_diagnostics(
    q_values: np.ndarray,
    initial_q_values: np.ndarray,
    *,
    arm: str,
    current_version: int,
    transitions: Mapping[str, np.ndarray],
    stop: int,
) -> dict[str, float | int | None]:
    """Audit current-version collection and table coverage through ``stop`` macros."""
    if stop < 0 or stop > len(transitions["collection_version"]):
        raise ValueError("collection diagnostic stop is outside transition storage")
    versions = transitions["collection_version"][:stop]
    selected_indices = np.flatnonzero(versions == current_version)
    current_q = _selected_q(q_values, arm, current_version)
    initial_q = _selected_q(initial_q_values, arm, current_version)
    greedy = np.argmax(current_q[1:], axis=-1)
    changed = np.count_nonzero(current_q[1:] != initial_q[1:])
    if selected_indices.size == 0:
        return {
            "current_version_sample_count": 0,
            "collected_right_fraction": None,
            "distinct_state_action_entries": 0,
            "both_actions_state_time_cells": 0,
            "greedy_right_fraction_nonterminal_cells": float(
                np.mean(greedy == RIGHT)
            ),
            "changed_current_table_nonterminal_q_entries": int(changed),
        }

    # Cast before arithmetic so identifiers remain safe if a fixture widens time.
    remaining = transitions["remaining"][selected_indices].astype(np.int64)
    positions = transitions["start_positions"][selected_indices].astype(np.int64)
    actions = transitions["ego_goal"][selected_indices].astype(np.int64)
    state_time_ids = (
        (remaining * np.int64(N_POSITIONS) + positions[:, 0])
        * np.int64(N_POSITIONS)
        + positions[:, 1]
    )
    state_action_ids = state_time_ids * np.int64(2) + actions
    left_cells = np.unique(state_time_ids[actions == LEFT])
    right_cells = np.unique(state_time_ids[actions == RIGHT])
    both_actions = np.intersect1d(left_cells, right_cells, assume_unique=True)
    return {
        "current_version_sample_count": int(selected_indices.size),
        "collected_right_fraction": float(np.mean(actions == RIGHT)),
        "distinct_state_action_entries": int(np.unique(state_action_ids).size),
        "both_actions_state_time_cells": int(both_actions.size),
        "greedy_right_fraction_nonterminal_cells": float(
            np.mean(greedy == RIGHT)
        ),
        "changed_current_table_nonterminal_q_entries": int(changed),
    }


def _weight_diagnostics(
    transitions: Mapping[str, np.ndarray], start: int, stop: int, current_version: int,
    recent_capacity: int,
) -> dict[str, float | int | None]:
    if stop <= start:
        return {
            "sample_uses": 0,
            "raw_ratio_mean": None,
            "normalized_weight_max": None,
            "effective_sample_size": None,
            "sample_age_mean": None,
            "sample_age_max": None,
            "older_sample_fraction": None,
            "older_weight_share": None,
            "outside_recent_window_weight_share": None,
            "compatible_version_fraction": None,
            "compatible_version_weight_share": None,
        }
    raw = transitions["replay_raw_ratios"][start:stop].reshape(-1)
    weights = transitions["replay_normalized_weights"][start:stop].reshape(-1)
    ages = transitions["replay_sample_ages"][start:stop].reshape(-1)
    versions = transitions["replay_sample_versions"][start:stop].reshape(-1)
    total_weight = float(weights.sum())
    old = ages > 0
    outside = ages >= recent_capacity
    compatible = versions == current_version
    return {
        "sample_uses": int(weights.size),
        "raw_ratio_mean": float(raw.mean()),
        "normalized_weight_max": float(weights.max()),
        "effective_sample_size": float(total_weight ** 2 / np.square(weights).sum()),
        "sample_age_mean": float(ages.mean()),
        "sample_age_max": int(ages.max()),
        "older_sample_fraction": float(old.mean()),
        "older_weight_share": float(weights[old].sum() / total_weight),
        "outside_recent_window_weight_share": float(
            weights[outside].sum() / total_weight
        ),
        "compatible_version_fraction": float(compatible.mean()),
        "compatible_version_weight_share": float(
            weights[compatible].sum() / total_weight
        ),
    }


def _record_panel(
    curves: dict[str, list[Any]], q_values: np.ndarray,
    initial_q_values: np.ndarray, arm: str, config: Config, episode: int,
    current_version: int, transitions: Mapping[str, np.ndarray], weight_start: int,
) -> None:
    selected = _selected_q(q_values, arm, current_version)
    evaluation = exact_policy_evaluation(selected, config, current_version)
    mean_residual, max_residual = bellman_residual(selected, config, current_version)
    weight_stop = episode * config.macros_per_episode
    diagnostics = _weight_diagnostics(
        transitions, weight_start, weight_stop, current_version, config.recent_capacity
    )
    curves["evaluation_episode"].append(int(episode))
    curves["version_index"].append(int(current_version))
    curves["discounted_service_return"].append(
        evaluation["discounted_service_return"]
    )
    curves["normalized_service_return"].append(
        evaluation["normalized_service_return"]
    )
    curves["bellman_residual_mean"].append(mean_residual)
    curves["bellman_residual_max"].append(max_residual)
    curves["optimal_normalized_service_return"].append(
        exact_optimal_evaluation(config, current_version)[
            "normalized_service_return"
        ]
    )
    curves["policy"].append(evaluation["policy"])
    curves["q_l2_movement"].append(
        float(np.linalg.norm(q_values - initial_q_values))
    )
    curves["q_changed_entries"].append(
        int(np.count_nonzero(q_values != initial_q_values))
    )
    curves["q_initial_l2_norm"].append(float(np.linalg.norm(initial_q_values)))
    curves["weight_diagnostics"].append(diagnostics)
    curves["collection_diagnostics"].append(
        collection_diagnostics(
            q_values,
            initial_q_values,
            arm=arm,
            current_version=current_version,
            transitions=transitions,
            stop=weight_stop,
        )
    )


def _json_config(config: Config) -> dict[str, Any]:
    value = asdict(config)
    return {key: list(item) if isinstance(item, tuple) else item for key, item in value.items()}


def run_fit(
    config: Config, *, arm: str, seed: int, object_name: str = OBJECT
) -> dict[str, Any]:
    """Run one deterministic-addressed B01 fit without any file or launch effects."""
    validate_config(config)
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    if not isinstance(object_name, str) or not object_name:
        raise ValueError("object_name must be a nonempty string")

    q_values = initialize_q_values(config, arm)
    initial_q_values = q_values.copy()
    transitions = _transition_storage(config)
    slots = common_random_slots(config, int(seed))
    transitions["episode_reset_positions"][:] = slots["reset_positions"]
    replay_root = np.random.SeedSequence([int(seed), 0xB01, 0x5EED])
    replay_rng = np.random.default_rng(replay_root)
    continuation_discount = config.gamma ** config.macro_duration
    curves: dict[str, list[Any]] = {
        "evaluation_episode": [],
        "version_index": [],
        "discounted_service_return": [],
        "normalized_service_return": [],
        "bellman_residual_mean": [],
        "bellman_residual_max": [],
        "optimal_normalized_service_return": [],
        "policy": [],
        "q_l2_movement": [],
        "q_changed_entries": [],
        "q_initial_l2_norm": [],
        "weight_diagnostics": [],
        "collection_diagnostics": [],
    }

    initial_version = version_index(config, 0)
    _record_panel(
        curves, q_values, initial_q_values, arm, config, 0, initial_version,
        transitions, 0
    )
    last_panel_macro = 0
    for episode in range(config.total_episodes):
        current_version = version_index(config, episode)
        ego_move_probability = config.ego_move_probabilities[current_version]
        teammate_right_probability = config.teammate_right_probabilities[current_version]
        ego_position, teammate_position = (
            int(value) for value in slots["reset_positions"][episode]
        )
        for macro in range(config.macros_per_episode):
            index = episode * config.macros_per_episode + macro
            remaining = config.macros_per_episode - macro
            actor_q = _selected_q(q_values, arm, current_version)
            greedy_action = int(
                np.argmax(actor_q[remaining, ego_position, teammate_position])
            )
            if slots["exploration_uniform"][episode, macro] < config.epsilon:
                ego_goal = int(
                    slots["exploration_action_uniform"][episode, macro] >= 0.5
                )
            else:
                ego_goal = greedy_action
            teammate_goal = int(
                slots["teammate_goal_uniform"][episode, macro]
                < teammate_right_probability
            )
            transitions["episode"][index] = episode
            transitions["macro_in_episode"][index] = macro
            transitions["collection_version"][index] = current_version
            transitions["teammate_goal_uniform"][index] = slots[
                "teammate_goal_uniform"
            ][episode, macro]
            transitions["exploration_uniform"][index] = slots[
                "exploration_uniform"
            ][episode, macro]
            transitions["exploration_action_uniform"][index] = slots[
                "exploration_action_uniform"
            ][episode, macro]
            transitions["primitive_uniform"][index] = slots["primitive_uniform"][
                episode, macro
            ]
            transitions["remaining"][index] = remaining
            transitions["start_positions"][index] = (ego_position, teammate_position)
            transitions["ego_goal"][index] = ego_goal
            transitions["teammate_goal"][index] = teammate_goal

            macro_reward = 0.0
            primitive_discount = 1.0
            for tick in range(config.macro_duration):
                transitions["pre_positions"][index, tick] = (
                    ego_position, teammate_position
                )
                ego_target = 0 if ego_goal == LEFT else N_POSITIONS - 1
                if ego_position == ego_target:
                    ego_action = HOLD
                else:
                    ego_move = MOVE_LEFT if ego_goal == LEFT else MOVE_RIGHT
                    ego_action = (
                        ego_move
                        if slots["primitive_uniform"][episode, macro, tick, 0, ego_goal]
                        < ego_move_probability
                        else HOLD
                    )
                teammate_target = (
                    0 if teammate_goal == LEFT else N_POSITIONS - 1
                )
                if teammate_position == teammate_target:
                    teammate_action = HOLD
                else:
                    teammate_move = (
                        MOVE_LEFT if teammate_goal == LEFT else MOVE_RIGHT
                    )
                    teammate_action = (
                        teammate_move
                        if slots["primitive_uniform"][
                            episode, macro, tick, 1, teammate_goal
                        ] < config.teammate_move_probability
                        else HOLD
                    )
                transitions["primitive_actions"][index, tick] = (
                    ego_action, teammate_action
                )
                transitions["primitive_behavior_probabilities"][index, tick] = (
                    primitive_action_probability(
                        ego_position, ego_goal, ego_action, ego_move_probability
                    ),
                    primitive_action_probability(
                        teammate_position,
                        teammate_goal,
                        teammate_action,
                        config.teammate_move_probability,
                    ),
                )
                ego_position = apply_primitive_action(ego_position, ego_action)
                teammate_position = apply_primitive_action(
                    teammate_position, teammate_action
                )
                transitions["post_positions"][index, tick] = (
                    ego_position, teammate_position
                )
                reward = native_service_reward(ego_position, teammate_position)
                transitions["primitive_rewards"][index, tick] = reward
                macro_reward += primitive_discount * reward
                primitive_discount *= config.gamma

            behavior = trajectory_likelihood(
                teammate_goal=teammate_goal,
                ego_goal=ego_goal,
                pre_positions=transitions["pre_positions"][index],
                primitive_actions=transitions["primitive_actions"][index],
                ego_move_probability=ego_move_probability,
                teammate_right_probability=teammate_right_probability,
                teammate_move_probability=config.teammate_move_probability,
            )
            if behavior["total"] <= 0.0:
                raise RuntimeError("collected trajectory has zero behavior likelihood")
            transitions["teammate_goal_behavior_probability"][index] = behavior[
                "teammate_goal"
            ]
            transitions["behavior_ego_primitive_likelihood"][index] = behavior[
                "ego_primitive"
            ]
            transitions["behavior_teammate_primitive_likelihood"][index] = behavior[
                "teammate_primitive"
            ]
            transitions["behavior_trajectory_likelihood"][index] = behavior["total"]
            transitions["macro_reward"][index] = macro_reward
            transitions["next_positions"][index] = (ego_position, teammate_position)
            next_remaining = remaining - 1
            terminal = next_remaining == 0
            transitions["next_remaining"][index] = next_remaining
            transitions["terminal"][index] = terminal

            eligible = replay_eligible_indices(
                arm,
                transitions["collection_version"],
                current_version=current_version,
                current_index=index,
                recent_capacity=config.recent_capacity,
            )
            replay_indices = replay_rng.choice(
                eligible, size=config.batch_size, replace=True
            ).astype(np.int32, copy=False)
            transitions["replay_indices"][index] = replay_indices
            sample_versions = transitions["collection_version"][replay_indices]
            transitions["replay_sample_versions"][index] = sample_versions
            transitions["replay_sample_ages"][index] = index - replay_indices
            ratios = np.ones(config.batch_size, dtype=np.float64)
            if arm == "joint_is":
                for sample_offset, sample in enumerate(replay_indices):
                    collection_version = int(sample_versions[sample_offset])
                    # Exact equality is a required stable-version identity.
                    if collection_version == current_version:
                        ratios[sample_offset] = 1.0
                        continue
                    current = trajectory_likelihood(
                        teammate_goal=int(transitions["teammate_goal"][sample]),
                        ego_goal=int(transitions["ego_goal"][sample]),
                        pre_positions=transitions["pre_positions"][sample],
                        primitive_actions=transitions["primitive_actions"][sample],
                        ego_move_probability=ego_move_probability,
                        teammate_right_probability=teammate_right_probability,
                        teammate_move_probability=config.teammate_move_probability,
                    )
                    ratios[sample_offset] = (
                        current["total"]
                        / transitions["behavior_trajectory_likelihood"][sample]
                    )
            if not np.all(np.isfinite(ratios)) or np.any(ratios <= 0.0):
                raise RuntimeError("joint likelihood ratios lost common support")
            weights = ratios / ratios.mean() if arm == "joint_is" else ratios
            transitions["replay_raw_ratios"][index] = ratios
            transitions["replay_normalized_weights"][index] = weights
            table_indices = sample_versions if arm == "fingerprint" else None
            if table_indices is not None:
                transitions["replay_table_indices"][index] = table_indices
            simultaneous_q_update(
                q_values,
                remaining=transitions["remaining"][replay_indices],
                ego_position=transitions["start_positions"][replay_indices, 0],
                teammate_position=transitions["start_positions"][replay_indices, 1],
                action=transitions["ego_goal"][replay_indices],
                reward=transitions["macro_reward"][replay_indices],
                next_remaining=transitions["next_remaining"][replay_indices],
                next_ego_position=transitions["next_positions"][replay_indices, 0],
                next_teammate_position=transitions["next_positions"][replay_indices, 1],
                terminal=transitions["terminal"][replay_indices],
                weights=weights,
                alpha=config.alpha,
                continuation_discount=continuation_discount,
                table_indices=table_indices,
            )
            terminal_changed = (
                np.any(q_values[:, 0] != 0.0)
                if arm == "fingerprint"
                else np.any(q_values[0] != 0.0)
            )
            if terminal_changed:
                raise RuntimeError("terminal Q row changed")

        completed_episodes = episode + 1
        if completed_episodes % config.evaluation_interval == 0:
            _record_panel(
                curves,
                q_values,
                initial_q_values,
                arm,
                config,
                completed_episodes,
                current_version,
                transitions,
                last_panel_macro,
            )
            last_panel_macro = completed_episodes * config.macros_per_episode

    if curves["evaluation_episode"][-1] != config.total_episodes:
        final_version = version_index(config, config.total_episodes - 1)
        _record_panel(
            curves,
            q_values,
            initial_q_values,
            arm,
            config,
            config.total_episodes,
            final_version,
            transitions,
            last_panel_macro,
        )

    panel_by_episode = {
        episode: value for episode, value in zip(
            curves["evaluation_episode"], curves["normalized_service_return"]
        )
    }
    primary_complete = all(
        episode in panel_by_episode for episode in config.primary_evaluation_episodes
    )
    primary_values = (
        [panel_by_episode[episode] for episode in config.primary_evaluation_episodes]
        if primary_complete else []
    )
    q_change = q_values - initial_q_values
    movement = {
        "initial_q_l2": float(np.linalg.norm(initial_q_values)),
        "initial_q_l2_norm": float(np.linalg.norm(initial_q_values)),
        "initial_q_nonzero_entries": int(np.count_nonzero(initial_q_values)),
        "final_q_l1_movement": float(np.abs(q_change).sum()),
        "final_q_l2_movement": float(np.linalg.norm(q_change)),
        "final_q_linf_movement": float(np.abs(q_change).max()),
        "final_changed_q_entries": int(np.count_nonzero(q_change)),
        "final_q_nonzero_entries": int(np.count_nonzero(q_values)),
        "q_entries": int(q_values.size),
        "terminal_q_linf": float(
            np.abs(q_values[:, 0]).max()
            if arm == "fingerprint" else np.abs(q_values[0]).max()
        ),
    }
    summary = {
        "object": object_name,
        "status": "COMPLETE",
        "arm": arm,
        "seed": int(seed),
        "config": _json_config(config),
        "counts": {
            "episodes": config.total_episodes,
            "macro_transitions": config.total_macros,
            "primitive_transitions": config.total_macros * config.macro_duration,
            "minibatch_updates": config.total_macros,
            "replay_sample_uses": config.total_macros * config.batch_size,
            "evaluation_panels": len(curves["evaluation_episode"]),
            "evaluation_episodes_simulated": 0,
            "evaluation_parameter_updates": 0,
        },
        "movement": movement,
        "primary_adaptation_endpoint": {
            "episodes": list(config.primary_evaluation_episodes),
            "complete": primary_complete,
            "normalized_service_returns": primary_values,
            "mean_normalized_service_return": (
                float(np.mean(primary_values)) if primary_values else None
            ),
        },
        "optimal_informational_reference": {
            name: {
                "discounted_service_return": exact_optimal_evaluation(config, index)[
                    "discounted_service_return"
                ],
                "normalized_service_return": exact_optimal_evaluation(config, index)[
                    "normalized_service_return"
                ],
            }
            for index, name in enumerate(config.version_names)
        },
        "final_collection_diagnostics": curves["collection_diagnostics"][-1],
        "final_normalized_service_return": curves["normalized_service_return"][-1],
    }
    if any(value.dtype == object for value in transitions.values()):
        raise RuntimeError("transition output contains an object array")
    return {
        "summary": summary,
        "curves": curves,
        "transitions": transitions,
        "q_values": q_values,
    }
