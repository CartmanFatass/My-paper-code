"""Registered task-blind statistics for R48-SBRS-G0.

The gate compares the same forced non-incumbent skill with and without a
focal actor recurrent-state reset.  It contains no policy update, reward
signal, spectral fit, classifier, or environment-specific process field.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r48-sbrs-g0"
SCHEMA_VERSION = 1
SOURCE_CHECKPOINT = Path(
    "logs/r30_alice_bob_paired_64k_20260714_163908/"
    "runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt"
)

SOURCE_TOTAL_STEPS = 64_000
SOURCE_UPDATE = 50
SOURCE_SEED = 47_041
INNOVATION_SEED = 68_041
BOOTSTRAP_SEED = 62_048
BOOTSTRAP_REPETITIONS = 10_000

N_AGENTS = 2
N_SKILLS = 4
K0 = 10
EPISODE_STEPS = 80
WORLD_SIZE = 8.0
CONTEXTS = 64
TARGETS_PER_CONTEXT = 3
REPLICAS = 2
ARMS = ("carry_hidden", "reset_on_set")
BRANCH_HORIZON = 40
BRANCHES_PER_ARM = CONTEXTS * TARGETS_PER_CONTEXT * REPLICAS
TOTAL_BRANCHES = len(ARMS) * BRANCHES_PER_ARM
FORCED_BRANCH_STEPS = TOTAL_BRANCHES * BRANCH_HORIZON
NATURAL_SOURCE_STEPS = CONTEXTS * EPISODE_STEPS
PROCESS_DIM = 4
EPSILON = 1e-8

HORIZONS = {
    "h10": np.arange(0, 10, dtype=np.int64),
    "h40_late": np.arange(30, 40, dtype=np.int64),
}


def task_blind_process_trajectory(
    position_frames: np.ndarray, focal_agent: int
) -> np.ndarray:
    """Return the registered 40 by 4 normalized position-only process."""

    positions = np.asarray(position_frames, dtype=np.float64)
    if positions.shape != (BRANCH_HORIZON + 1, N_AGENTS, 2):
        raise ValueError(
            "R48 position frames must have shape "
            f"[{BRANCH_HORIZON + 1},{N_AGENTS},2]"
        )
    focal = int(focal_agent)
    if focal not in (0, 1):
        raise ValueError("R48 focal agent must be 0 or 1")
    teammate = 1 - focal
    normalized = positions / WORLD_SIZE
    focal_delta = normalized[1:, focal] - normalized[0, focal]
    relative = normalized[:, teammate] - normalized[:, focal]
    relative_delta = relative[1:] - relative[0]
    return np.concatenate([focal_delta, relative_delta], axis=-1).astype(
        np.float32
    )


def trajectory_distance(
    left: np.ndarray, right: np.ndarray, time_indices: np.ndarray
) -> float:
    delta = np.asarray(left, dtype=np.float64)[time_indices] - np.asarray(
        right, dtype=np.float64
    )[time_indices]
    return float(np.mean(np.sum(np.square(delta), axis=-1)))


def between_within_statistics(
    trajectories: np.ndarray,
    target_skills: np.ndarray,
    time_indices: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute context-level B/W and target-skill conditional B/W."""

    values = np.asarray(trajectories, dtype=np.float64)
    targets = np.asarray(target_skills, dtype=np.int64)
    expected = (
        len(ARMS),
        values.shape[1],
        TARGETS_PER_CONTEXT,
        REPLICAS,
        BRANCH_HORIZON,
        PROCESS_DIM,
    )
    if values.shape != expected:
        raise ValueError(f"R48 trajectory shape mismatch: {values.shape} != {expected}")
    if targets.shape != (values.shape[1], TARGETS_PER_CONTEXT):
        raise ValueError("R48 target-skill table shape mismatch")

    contexts = values.shape[1]
    between = np.zeros((len(ARMS), contexts), dtype=np.float64)
    within = np.zeros((len(ARMS), contexts), dtype=np.float64)
    between_by_skill = np.full(
        (len(ARMS), contexts, N_SKILLS), np.nan, dtype=np.float64
    )
    within_by_skill = np.full_like(between_by_skill, np.nan)

    for arm in range(len(ARMS)):
        for context in range(contexts):
            pair_distances: list[float] = []
            for left in range(TARGETS_PER_CONTEXT):
                for right in range(left + 1, TARGETS_PER_CONTEXT):
                    for replica in range(REPLICAS):
                        pair_distances.append(
                            trajectory_distance(
                                values[arm, context, left, replica],
                                values[arm, context, right, replica],
                                time_indices,
                            )
                        )
            between[arm, context] = float(np.mean(pair_distances))

            within_values = [
                trajectory_distance(
                    values[arm, context, target, 0],
                    values[arm, context, target, 1],
                    time_indices,
                )
                for target in range(TARGETS_PER_CONTEXT)
            ]
            within[arm, context] = float(np.mean(within_values))

            for target_index, skill in enumerate(targets[context]):
                conditional_between: list[float] = []
                for other in range(TARGETS_PER_CONTEXT):
                    if other == target_index:
                        continue
                    for replica in range(REPLICAS):
                        conditional_between.append(
                            trajectory_distance(
                                values[arm, context, target_index, replica],
                                values[arm, context, other, replica],
                                time_indices,
                            )
                        )
                between_by_skill[arm, context, int(skill)] = float(
                    np.mean(conditional_between)
                )
                within_by_skill[arm, context, int(skill)] = within_values[target_index]

    return {
        "between": between,
        "within": within,
        "between_by_skill": between_by_skill,
        "within_by_skill": within_by_skill,
    }


def _interval(replicates: np.ndarray, point: float) -> dict[str, float]:
    samples = np.asarray(replicates, dtype=np.float64)
    return {
        "lower_95": float(np.quantile(samples, 0.025)),
        "mean": float(point),
        "upper_95": float(np.quantile(samples, 0.975)),
    }


def bootstrap_gate_metrics(
    statistics: dict[str, np.ndarray],
    samples: np.ndarray,
) -> dict[str, Any]:
    """Use one paired context resample for every registered arm metric."""

    between = np.asarray(statistics["between"], dtype=np.float64)
    within = np.asarray(statistics["within"], dtype=np.float64)
    indices = np.asarray(samples, dtype=np.int64)
    if between.shape != (len(ARMS), CONTEXTS) or within.shape != between.shape:
        raise ValueError("R48 formal B/W arrays must have one row per arm and context")
    if indices.shape != (BOOTSTRAP_REPETITIONS, CONTEXTS):
        raise ValueError("R48 bootstrap sample table shape mismatch")

    boot_b = between[:, indices].mean(axis=-1)
    boot_w = within[:, indices].mean(axis=-1)
    boot_rho = boot_b / (boot_w + EPSILON)

    point_b = between.mean(axis=1)
    point_w = within.mean(axis=1)
    point_rho = point_b / (point_w + EPSILON)
    carry = ARMS.index("carry_hidden")
    reset = ARMS.index("reset_on_set")

    return {
        "rho": {
            arm: _interval(boot_rho[index], point_rho[index])
            for index, arm in enumerate(ARMS)
        },
        "rho_reset_over_carry": _interval(
            boot_rho[reset] / boot_rho[carry],
            point_rho[reset] / point_rho[carry],
        ),
        "within_reset_over_carry": _interval(
            boot_w[reset] / (boot_w[carry] + EPSILON),
            point_w[reset] / (point_w[carry] + EPSILON),
        ),
        "between_reset_over_carry": _interval(
            boot_b[reset] / (boot_b[carry] + EPSILON),
            point_b[reset] / (point_b[carry] + EPSILON),
        ),
        "between_mean": {
            arm: float(point_b[index]) for index, arm in enumerate(ARMS)
        },
        "within_mean": {
            arm: float(point_w[index]) for index, arm in enumerate(ARMS)
        },
    }


def per_skill_rho(
    statistics: dict[str, np.ndarray], arm: str
) -> dict[str, float]:
    arm_index = ARMS.index(arm)
    between = np.asarray(statistics["between_by_skill"], dtype=np.float64)[arm_index]
    within = np.asarray(statistics["within_by_skill"], dtype=np.float64)[arm_index]
    result: dict[str, float] = {}
    for skill in range(N_SKILLS):
        mask = np.isfinite(between[:, skill]) & np.isfinite(within[:, skill])
        if not np.any(mask):
            result[str(skill)] = math.nan
            continue
        result[str(skill)] = float(
            between[mask, skill].mean() / (within[mask, skill].mean() + EPSILON)
        )
    return result


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value
