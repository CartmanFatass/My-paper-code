"""Terminal contextual host for the B03 joint-response existence test.

Environment/evaluator truth is kept outside the learner.  Learners see only the
declared current controller context and collected skill, joint outcome, and reward.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from math import gcd
from typing import Any

import numpy as np


OBJECT = "STDL_JOINT_RESPONSE_B03"
ARMS = (
    "joint_response",
    "fingerprint_full",
    "fingerprint_recent",
    "uniform",
    "recent",
    "additive_response",
)
SAFE = 0
COOPERATIVE = 1
SOURCE = 0
TARGET = 1
SAFE_REWARD_MEAN = 0.60
LOW_COOPERATIVE_REWARD_MEAN = 0.05
HIGH_COOPERATIVE_REWARD_MEAN = 0.95
PRIOR_MEAN = 0.5
ENDPOINT_WINDOW = 64


@dataclass(frozen=True)
class Config:
    source_macros: int = 2048
    target_macros: int = 256
    skill_ticks: int = 3
    recent_window: int = 64
    prior_strength: float = 2.0
    source_schedule: str = "product"

    @property
    def total_macros(self) -> int:
        return self.source_macros + self.target_macros


def validate_config(config: Config) -> None:
    if config.source_macros <= 0 or config.target_macros <= 0:
        raise ValueError("source_macros and target_macros must be positive")
    if config.skill_ticks <= 0 or config.recent_window <= 0:
        raise ValueError("skill_ticks and recent_window must be positive")
    if not np.isfinite(config.prior_strength) or config.prior_strength <= 0.0:
        raise ValueError("prior_strength must be finite and positive")
    if config.source_schedule not in ("product", "permuted"):
        raise ValueError("source_schedule must be product or permuted")
    if config.source_schedule == "permuted" and gcd(37, config.source_macros) != 1:
        raise ValueError("permuted source_macros must be coprime to 37")


def completion_probability_to_tick_probability(
    completion_probability: np.ndarray | float, skill_ticks: int
) -> np.ndarray:
    """Invert u = 1 - (1-p)^ticks for the closed-loop one-step skill."""
    completion = np.asarray(completion_probability, dtype=np.float64)
    if skill_ticks <= 0 or np.any(completion <= 0.0) or np.any(completion >= 1.0):
        raise ValueError("completion probabilities must lie in (0, 1)")
    return 1.0 - np.power(1.0 - completion, 1.0 / skill_ticks)


def joint_probabilities(u: float, v: float) -> np.ndarray:
    """Outcome probabilities in fixed order 00, 01, 10, 11."""
    if not 0.0 < u < 1.0 or not 0.0 < v < 1.0:
        raise ValueError("completion probabilities must lie in (0, 1)")
    return np.array(
        [(1.0 - u) * (1.0 - v), (1.0 - u) * v, u * (1.0 - v), u * v],
        dtype=np.float64,
    )


def context_schedule(config: Config) -> dict[str, np.ndarray]:
    """Return the fixed source product curve followed by the target rectangle path."""
    validate_config(config)
    source_index = np.arange(config.source_macros, dtype=np.float64)
    source_u = 0.25 + 0.55 * (source_index + 0.5) / config.source_macros
    source_v = 0.16 / source_u
    if config.source_schedule == "permuted":
        permutation = (37 * np.arange(config.source_macros)) % config.source_macros
        source_v = source_v[permutation]
    target_index = np.arange(config.target_macros, dtype=np.float64)
    target_u = 0.82 + 0.10 * (target_index + 0.5) / config.target_macros
    target_v = 0.84 + 0.10 * (target_index + 0.5) / config.target_macros
    u = np.concatenate((source_u, target_u))
    v = np.concatenate((source_v, target_v))
    phase = np.concatenate(
        (
            np.full(config.source_macros, SOURCE, dtype=np.int8),
            np.full(config.target_macros, TARGET, dtype=np.int8),
        )
    )
    phase_index = np.concatenate(
        (
            np.arange(config.source_macros, dtype=np.int32),
            np.arange(config.target_macros, dtype=np.int32),
        )
    )
    return {
        "u": u,
        "v": v,
        "p": completion_probability_to_tick_probability(u, config.skill_ticks),
        "q": completion_probability_to_tick_probability(v, config.skill_ticks),
        "phase": phase,
        "phase_index": phase_index,
    }


def conditional_reward_probability(skill: int, x: int, y: int) -> float:
    """Environment/evaluator reward law; never passed into learner methods."""
    if skill == SAFE:
        return SAFE_REWARD_MEAN
    if skill != COOPERATIVE or x not in (0, 1) or y not in (0, 1):
        raise ValueError("invalid skill or terminal outcome")
    return (
        HIGH_COOPERATIVE_REWARD_MEAN
        if x == 1 and y == 1
        else LOW_COOPERATIVE_REWARD_MEAN
    )


def exact_skill_values(u: float, v: float) -> np.ndarray:
    """Evaluator-only expected rewards for safe and cooperative skills."""
    return np.array(
        [SAFE_REWARD_MEAN, LOW_COOPERATIVE_REWARD_MEAN + 0.90 * u * v],
        dtype=np.float64,
    )


def simulate_terminal_macro(
    *,
    skill: int,
    p: float,
    q: float,
    primitive_uniform: np.ndarray,
    reward_uniform: float,
) -> dict[str, np.ndarray | float | int]:
    """Execute the physical three-tick closed-loop macro and sampled reward."""
    uniforms = np.asarray(primitive_uniform, dtype=np.float64)
    if uniforms.ndim != 2 or uniforms.shape[1] != 2:
        raise ValueError("primitive_uniform must have shape [ticks, 2]")
    if skill not in (SAFE, COOPERATIVE) or not 0.0 < p < 1.0 or not 0.0 < q < 1.0:
        raise ValueError("invalid skill or primitive success probability")
    if not 0.0 <= reward_uniform < 1.0:
        raise ValueError("reward_uniform must lie in [0, 1)")
    ticks = uniforms.shape[0]
    pre_positions = np.empty((ticks, 2), dtype=np.int8)
    actions = np.zeros((ticks, 2), dtype=np.int8)
    post_positions = np.empty((ticks, 2), dtype=np.int8)
    positions = np.zeros(2, dtype=np.int8)
    probabilities = (p, q)
    for tick in range(ticks):
        pre_positions[tick] = positions
        if skill == COOPERATIVE:
            for agent in range(2):
                if positions[agent] == 0 and uniforms[tick, agent] < probabilities[agent]:
                    actions[tick, agent] = 1
                    positions[agent] = 1
        post_positions[tick] = positions
    x, y = (int(value) for value in positions)
    reward_probability = conditional_reward_probability(skill, x, y)
    reward = int(reward_uniform < reward_probability)
    return {
        "pre_positions": pre_positions,
        "primitive_actions": actions,
        "post_positions": post_positions,
        "outcomes": positions.copy(),
        "reward_probability": reward_probability,
        "reward": reward,
    }


def common_random_slots(config: Config, seed: int) -> dict[str, np.ndarray]:
    """Arm-independent, separately addressed collection randomness."""
    validate_config(config)
    roots = np.random.SeedSequence(int(seed)).spawn(3)
    skill_rng, primitive_rng, reward_rng = (np.random.default_rng(root) for root in roots)
    return {
        "skill_uniform": skill_rng.random(config.total_macros),
        "primitive_uniform": primitive_rng.random(
            (config.total_macros, config.skill_ticks, 2)
        ),
        # Reward draws are addressed by macro, skill, X, and Y.
        "reward_uniform_slots": reward_rng.random((config.total_macros, 2, 2, 2)),
    }


def _saturated_feature(skill: int, u: float, v: float) -> np.ndarray:
    if skill == SAFE:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    return joint_probabilities(u, v)


def _additive_feature(skill: int, x_or_u: float, y_or_v: float) -> np.ndarray:
    if skill == SAFE:
        return np.array([1.0, 0.0, 0.0], dtype=np.float64)
    return np.array([1.0, x_or_u, y_or_v], dtype=np.float64)


class _Learner:
    """Small sufficient-statistic learner with no evaluator access."""

    def __init__(self, arm: str, config: Config):
        if arm not in ARMS:
            raise ValueError(f"arm must be one of {ARMS}")
        self.arm = arm
        self.config = config
        self.updates = 0
        self.solves = 0
        self.window: deque[tuple[int, np.ndarray, float, int]] = deque()
        self.counts: np.ndarray
        self.reward_sums: np.ndarray
        self.xtx: np.ndarray | None = None
        self.xty: np.ndarray | None = None
        self.coefficients: np.ndarray | None = None
        if arm == "joint_response":
            self.counts = np.zeros((2, 2, 2), dtype=np.int64)
            self.reward_sums = np.zeros((2, 2, 2), dtype=np.float64)
        elif arm in ("uniform", "recent"):
            self.counts = np.zeros(2, dtype=np.int64)
            self.reward_sums = np.zeros(2, dtype=np.float64)
        else:
            dimension = 3 if arm == "additive_response" else 4
            self.counts = np.zeros(2, dtype=np.int64)
            self.reward_sums = np.zeros(2, dtype=np.float64)
            self.xtx = np.zeros((2, dimension, dimension), dtype=np.float64)
            self.xty = np.zeros((2, dimension), dtype=np.float64)
            prior = (
                np.array([PRIOR_MEAN, 0.0, 0.0], dtype=np.float64)
                if dimension == 3
                else np.full(4, PRIOR_MEAN, dtype=np.float64)
            )
            self.prior_coefficients = prior
            self.coefficients = np.repeat(prior[None, :], 2, axis=0)

    def _posterior_means(self) -> np.ndarray:
        return (
            self.reward_sums + self.config.prior_strength * PRIOR_MEAN
        ) / (self.counts + self.config.prior_strength)

    def predict_raw(self, u: float, v: float) -> np.ndarray:
        if self.arm == "joint_response":
            means = self._posterior_means()
            return np.array(
                [means[SAFE, 0, 0], joint_probabilities(u, v) @ means[COOPERATIVE].reshape(-1)],
                dtype=np.float64,
            )
        if self.arm in ("uniform", "recent"):
            return self._posterior_means().astype(np.float64, copy=True)
        if self.arm in ("fingerprint_full", "fingerprint_recent"):
            return np.array(
                [
                    _saturated_feature(SAFE, u, v) @ self.coefficients[SAFE],
                    _saturated_feature(COOPERATIVE, u, v) @ self.coefficients[COOPERATIVE],
                ],
                dtype=np.float64,
            )
        return np.array(
            [
                _additive_feature(SAFE, u, v) @ self.coefficients[SAFE],
                _additive_feature(COOPERATIVE, u, v) @ self.coefficients[COOPERATIVE],
            ],
            dtype=np.float64,
        )

    def estimate_vector(self) -> np.ndarray:
        if self.arm in ("joint_response", "uniform", "recent"):
            return self._posterior_means().reshape(-1).copy()
        return self.coefficients.reshape(-1).copy()

    def _solve(self, skill: int) -> None:
        dimension = self.xtx.shape[-1]
        matrix = self.xtx[skill] + self.config.prior_strength * np.eye(dimension)
        rhs = (
            self.xty[skill]
            + self.config.prior_strength * self.prior_coefficients
        )
        self.coefficients[skill] = np.linalg.solve(matrix, rhs)
        self.solves += 1

    def update(
        self, *, skill: int, x: int, y: int, u: float, v: float, reward: int
    ) -> int:
        """Consume only one legal collected observation; return new solve count."""
        solves_before = self.solves
        if self.arm == "joint_response":
            self.counts[skill, x, y] += 1
            self.reward_sums[skill, x, y] += reward
        elif self.arm in ("uniform", "recent"):
            if self.arm == "recent" and len(self.window) == self.config.recent_window:
                old_skill, _feature, old_reward, _index = self.window.popleft()
                self.counts[old_skill] -= 1
                self.reward_sums[old_skill] -= old_reward
            self.counts[skill] += 1
            self.reward_sums[skill] += reward
            if self.arm == "recent":
                self.window.append(
                    (skill, np.empty(0, dtype=np.float64), float(reward), self.updates)
                )
        else:
            feature = (
                _additive_feature(skill, x, y)
                if self.arm == "additive_response"
                else _saturated_feature(skill, u, v)
            )
            changed_skills = {skill}
            if (
                self.arm == "fingerprint_recent"
                and len(self.window) == self.config.recent_window
            ):
                old_skill, old_feature, old_reward, _index = self.window.popleft()
                self.xtx[old_skill] -= np.outer(old_feature, old_feature)
                self.xty[old_skill] -= old_feature * old_reward
                self.counts[old_skill] -= 1
                self.reward_sums[old_skill] -= old_reward
                changed_skills.add(old_skill)
            self.xtx[skill] += np.outer(feature, feature)
            self.xty[skill] += feature * reward
            self.counts[skill] += 1
            self.reward_sums[skill] += reward
            if self.arm == "fingerprint_recent":
                self.window.append((skill, feature.copy(), float(reward), self.updates))
            for changed_skill in sorted(changed_skills):
                self._solve(changed_skill)
        self.updates += 1
        return self.solves - solves_before

    def export_state(self) -> dict[str, np.ndarray]:
        state = {
            "counts": self.counts.copy(),
            "reward_sums": self.reward_sums.copy(),
            "estimate": self.estimate_vector(),
            "updates": np.array([self.updates], dtype=np.int64),
            "regression_solves": np.array([self.solves], dtype=np.int64),
        }
        if self.xtx is not None:
            state.update(
                xtx=self.xtx.copy(),
                xty=self.xty.copy(),
                coefficients=self.coefficients.copy(),
            )
        if self.arm in ("recent", "fingerprint_recent"):
            dimension = 0 if self.arm == "recent" else 4
            state["window_skill"] = np.array(
                [item[0] for item in self.window], dtype=np.int8
            )
            state["window_features"] = np.array(
                [item[1] for item in self.window], dtype=np.float64
            ).reshape(len(self.window), dimension)
            state["window_reward"] = np.array(
                [item[2] for item in self.window], dtype=np.float64
            )
            state["window_update_index"] = np.array(
                [item[3] for item in self.window], dtype=np.int64
            )
        return state


def _empty_transitions(config: Config, schedule: dict[str, np.ndarray], slots: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    count = config.total_macros
    return {
        "macro_index": np.arange(count, dtype=np.int32),
        "phase": schedule["phase"].copy(),
        "phase_index": schedule["phase_index"].copy(),
        "u": schedule["u"].copy(),
        "v": schedule["v"].copy(),
        "p": schedule["p"].copy(),
        "q": schedule["q"].copy(),
        "skill_uniform": slots["skill_uniform"].copy(),
        "primitive_uniform": slots["primitive_uniform"].copy(),
        "reward_uniform_slots": slots["reward_uniform_slots"].copy(),
        "collection_skill": np.empty(count, dtype=np.int8),
        "pre_positions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        "primitive_actions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        "post_positions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        "outcomes": np.empty((count, 2), dtype=np.int8),
        "reward_probability": np.empty(count, dtype=np.float64),
        "reward_uniform": np.empty(count, dtype=np.float64),
        "reward": np.empty(count, dtype=np.int8),
    }


def _phase_support(transitions: dict[str, np.ndarray], start: int, stop: int) -> dict[str, Any]:
    skills = transitions["collection_skill"][start:stop]
    outcomes = transitions["outcomes"][start:stop]
    cooperative = outcomes[skills == COOPERATIVE]
    cooperative_counts = np.zeros((2, 2), dtype=np.int64)
    for x, y in cooperative:
        cooperative_counts[int(x), int(y)] += 1
    reachable = {
        (int(skill), int(x), int(y))
        for skill, (x, y) in zip(skills, outcomes)
    }
    return {
        "sample_count": int(stop - start),
        "skill_counts": np.bincount(skills, minlength=2).astype(int).tolist(),
        "cooperative_joint_outcome_counts": cooperative_counts.tolist(),
        "cooperative_joint_outcomes_observed": int(np.count_nonzero(cooperative_counts)),
        "skill_outcome_cells_observed": int(len(reachable)),
        "distinct_contexts": int(
            np.unique(
                np.column_stack((transitions["u"][start:stop], transitions["v"][start:stop])),
                axis=0,
            ).shape[0]
        ),
    }


def _endpoint(curves: dict[str, list[Any]], start: int, stop: int) -> tuple[float, float]:
    native = np.asarray(curves["expected_native_return"][start:stop], dtype=np.float64)
    error = np.asarray(curves["value_mae"][start:stop], dtype=np.float64)
    return float(native.mean()), float(error.mean())


def run_fit(
    config: Config,
    *,
    arm: str,
    seed: int,
    object_name: str = OBJECT,
) -> dict[str, Any]:
    """Run one B03 fit with pre-update exact evaluation and shared sampled data."""
    validate_config(config)
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    if not isinstance(object_name, str) or not object_name:
        raise ValueError("object_name must be a nonempty string")

    schedule = context_schedule(config)
    slots = common_random_slots(config, int(seed))
    transitions = _empty_transitions(config, schedule, slots)
    learner = _Learner(arm, config)
    initial_estimate = learner.estimate_vector()
    source_estimate = None
    source_solve_count = 0
    source_phase_solves = 0
    target_phase_solves = 0
    curves: dict[str, list[Any]] = {
        "macro_index": [],
        "phase": [],
        "phase_index": [],
        "u": [],
        "v": [],
        "p": [],
        "q": [],
        "raw_predictions": [],
        "clipped_predictions": [],
        "true_values": [],
        "greedy_action": [],
        "expected_native_return": [],
        "value_mae": [],
        "collection_skill": [],
        "outcomes": [],
        "sampled_reward": [],
        "learner_updates_before_panel": [],
        "regression_solves_before_panel": [],
    }

    for index in range(config.total_macros):
        u = float(schedule["u"][index])
        v = float(schedule["v"][index])
        raw = learner.predict_raw(u, v)
        clipped = np.clip(raw, 0.0, 1.0)
        truth = exact_skill_values(u, v)
        greedy_action = int(clipped[COOPERATIVE] > clipped[SAFE])
        native_return = float(truth[greedy_action])
        value_mae = float(np.abs(clipped - truth).mean())

        skill = int(slots["skill_uniform"][index] >= 0.5)
        p = float(schedule["p"][index])
        q = float(schedule["q"][index])
        # Reward slot selection follows only the physical sampled skill/outcome.
        if skill == SAFE:
            preliminary_x = preliminary_y = 0
        else:
            preliminary_x = int(np.any(slots["primitive_uniform"][index, :, 0] < p))
            preliminary_y = int(np.any(slots["primitive_uniform"][index, :, 1] < q))
        reward_uniform = float(
            slots["reward_uniform_slots"][
                index, skill, preliminary_x, preliminary_y
            ]
        )
        observed = simulate_terminal_macro(
            skill=skill,
            p=p,
            q=q,
            primitive_uniform=slots["primitive_uniform"][index],
            reward_uniform=reward_uniform,
        )
        x, y = (int(value) for value in observed["outcomes"])
        if (x, y) != (preliminary_x, preliminary_y):
            raise RuntimeError("reward addressing disagreed with physical outcome")

        curves["macro_index"].append(index)
        curves["phase"].append(int(schedule["phase"][index]))
        curves["phase_index"].append(int(schedule["phase_index"][index]))
        curves["u"].append(u)
        curves["v"].append(v)
        curves["p"].append(p)
        curves["q"].append(q)
        curves["raw_predictions"].append(raw.tolist())
        curves["clipped_predictions"].append(clipped.tolist())
        curves["true_values"].append(truth.tolist())
        curves["greedy_action"].append(greedy_action)
        curves["expected_native_return"].append(native_return)
        curves["value_mae"].append(value_mae)
        curves["collection_skill"].append(skill)
        curves["outcomes"].append([x, y])
        curves["sampled_reward"].append(int(observed["reward"]))
        curves["learner_updates_before_panel"].append(learner.updates)
        curves["regression_solves_before_panel"].append(learner.solves)

        transitions["collection_skill"][index] = skill
        transitions["pre_positions"][index] = observed["pre_positions"]
        transitions["primitive_actions"][index] = observed["primitive_actions"]
        transitions["post_positions"][index] = observed["post_positions"]
        transitions["outcomes"][index] = observed["outcomes"]
        transitions["reward_probability"][index] = observed["reward_probability"]
        transitions["reward_uniform"][index] = reward_uniform
        transitions["reward"][index] = observed["reward"]

        new_solves = learner.update(
            skill=skill,
            x=x,
            y=y,
            u=u,
            v=v,
            reward=int(observed["reward"]),
        )
        if schedule["phase"][index] == SOURCE:
            source_phase_solves += new_solves
        else:
            target_phase_solves += new_solves
        if index + 1 == config.source_macros:
            source_estimate = learner.estimate_vector()
            source_solve_count = learner.solves

    if source_estimate is None:
        raise RuntimeError("source phase did not complete")
    final_estimate = learner.estimate_vector()
    learner_state = learner.export_state()
    target_start = config.source_macros
    target_stop = config.total_macros
    window = min(ENDPOINT_WINDOW, config.target_macros)
    primary_native, primary_error = _endpoint(
        curves, target_start, target_start + window
    )
    full_native, full_error = _endpoint(curves, target_start, target_stop)
    late_native, late_error = _endpoint(curves, target_stop - window, target_stop)
    source_support = _phase_support(transitions, 0, target_start)
    target_support = _phase_support(transitions, target_start, target_stop)
    summary = {
        "object": object_name,
        "status": "COMPLETE",
        "arm": arm,
        "seed": int(seed),
        "config": asdict(config),
        "counts": {
            "source_macros": config.source_macros,
            "target_macros": config.target_macros,
            "total_macros": config.total_macros,
            "primitive_ticks": config.total_macros * config.skill_ticks,
            "sampled_reward_labels": config.total_macros,
            "learner_updates": learner.updates,
            "evaluation_panels": config.total_macros,
            "evaluation_sampled_rewards": 0,
            "evaluation_learner_updates": 0,
            "regression_solves": learner.solves,
        },
        "primary_target_panel_count": window,
        "primary_native_return": primary_native,
        "primary_value_mae": primary_error,
        "full_target_panel_count": config.target_macros,
        "full_target_native_return": full_native,
        "full_target_value_mae": full_error,
        "late_target_panel_count": window,
        "late_target_native_return": late_native,
        "late_target_value_mae": late_error,
        "source_support": source_support,
        "target_support": target_support,
        "source_estimate_l2_movement": float(
            np.linalg.norm(source_estimate - initial_estimate)
        ),
        "target_estimate_l2_movement": float(
            np.linalg.norm(final_estimate - source_estimate)
        ),
        "source_regression_solve_count": int(source_phase_solves),
        "target_regression_solve_count": int(target_phase_solves),
        "source_cumulative_regression_solve_count": int(source_solve_count),
    }
    if learner.updates != config.total_macros:
        raise RuntimeError("learner update count mismatch")
    if any(array.dtype == object for array in transitions.values()):
        raise RuntimeError("transition output contains an object array")
    if any(array.dtype == object for array in learner_state.values()):
        raise RuntimeError("learner state contains an object array")
    return {
        "summary": summary,
        "curves": curves,
        "transitions": transitions,
        "learner_state": learner_state,
    }
