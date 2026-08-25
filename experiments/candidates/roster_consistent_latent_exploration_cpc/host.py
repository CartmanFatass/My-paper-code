from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import EVAL_SIZES, REGISTERED
from .rng import generator

SENSOR, RELAY = 0, 1
LEFT, RIGHT, HOLD = 0, 1, 2
MISSING_CLUE = 0


@dataclass(frozen=True)
class EpisodeBatch:
    n: int
    handoff: bool
    target: np.ndarray
    initial_roles: np.ndarray
    initial_clues: np.ndarray
    post_roles: np.ndarray
    post_clues: np.ndarray
    replaced: np.ndarray


@dataclass(frozen=True)
class Outcomes:
    value: np.ndarray
    mission: np.ndarray
    fragmentation: np.ndarray
    pre_accuracy: np.ndarray
    post_accuracy: np.ndarray
    pre_validity: np.ndarray
    post_validity: np.ndarray


def handoff_counts(n: int) -> tuple[int, int]:
    if n == 5:
        return 1, 1
    if n == 7:
        return 2, 1
    if n == 9:
        return 2, 2
    raise ValueError("N must be one of 5, 7, 9")


def make_episode_batch(
    permit: ProductionPermit,
    phase: str,
    seed: int,
    n: int,
    handoff: bool,
    start: int,
    size: int,
) -> EpisodeBatch:
    require_active_permit(permit)
    if n not in EVAL_SIZES or size <= 0:
        raise ValueError("invalid CPC episode batch")
    target = np.empty(size, dtype=np.int64)
    roles = np.empty((size, n), dtype=np.int64)
    clues = np.empty((size, n), dtype=np.int64)
    replaced = np.zeros((size, n), dtype=bool)
    base_roles = np.asarray([SENSOR] * math.ceil(n / 2) + [RELAY] * math.floor(n / 2), dtype=np.int64)
    sensor_remove, relay_remove = handoff_counts(n)
    for local, episode in enumerate(range(start, start + size)):
        target_rng = generator(permit, phase, seed, n, handoff, episode, "target")
        target[local] = int(target_rng.integers(0, 2))
        order = generator(permit, phase, seed, n, handoff, episode, "role_permutation").permutation(n)
        roles[local] = base_roles[order]
        correctness = generator(permit, phase, seed, n, handoff, episode, "clues").random(n) < REGISTERED.clue_accuracy
        signed_target = 1 if target[local] == RIGHT else -1
        clues[local] = np.where(correctness, signed_target, -signed_target)
        if handoff:
            for role, count in ((SENSOR, sensor_remove), (RELAY, relay_remove)):
                slots = np.flatnonzero(roles[local] == role)
                chosen = generator(
                    permit, phase, seed, n, handoff, episode, "handoff", int(role),
                ).choice(slots, size=count, replace=False)
                replaced[local, chosen] = True
    post_clues = clues.copy()
    post_clues[replaced] = MISSING_CLUE
    return EpisodeBatch(
        n=n, handoff=handoff, target=target, initial_roles=roles,
        initial_clues=clues, post_roles=roles.copy(), post_clues=post_clues,
        replaced=replaced,
    )


def _validity(roles: np.ndarray, actions: np.ndarray) -> np.ndarray:
    used_sensor = np.stack(
        [((roles == SENSOR) & (actions == corridor)).any(axis=1) for corridor in (LEFT, RIGHT)], axis=1,
    )
    used_relay = np.stack(
        [((roles == RELAY) & (actions == corridor)).any(axis=1) for corridor in (LEFT, RIGHT)], axis=1,
    )
    return (~used_sensor | used_relay).all(axis=1)


def evaluate_outcomes(batch: EpisodeBatch, pre: np.ndarray, post: np.ndarray) -> Outcomes:
    pre = np.asarray(pre, dtype=np.int64)
    post = np.asarray(post, dtype=np.int64)
    if pre.shape != (len(batch.target), batch.n) or post.shape != pre.shape:
        raise ValueError("action tensors must match the episode batch")
    if np.any((pre < LEFT) | (pre > HOLD)) or np.any((post < LEFT) | (post > HOLD)):
        raise ValueError("actions must be LEFT, RIGHT, or HOLD")
    target = batch.target[:, None]
    pre_accuracy = (pre == target).sum(axis=1) / float(batch.n)
    post_accuracy = (post == target).sum(axis=1) / float(batch.n)
    pre_validity = _validity(batch.initial_roles, pre)
    post_validity = _validity(batch.post_roles, post)
    quorum = math.ceil(0.60 * batch.n)
    pre_target_roles = np.stack([
        ((batch.initial_roles == role) & (pre == target)).sum(axis=1) for role in (SENSOR, RELAY)
    ], axis=1)
    post_target_roles = np.stack([
        ((batch.post_roles == role) & (post == target)).sum(axis=1) for role in (SENSOR, RELAY)
    ], axis=1)
    pre_target = ((pre == target).sum(axis=1) >= quorum) & (pre_target_roles > 0).all(axis=1)
    post_target = ((post == target).sum(axis=1) >= quorum) & (post_target_roles > 0).all(axis=1)
    mission = pre_validity & post_validity & pre_target & post_target
    value = (REGISTERED.value_mission_weight * mission.astype(np.float64)
             + REGISTERED.value_pre_accuracy_weight * pre_accuracy
             + REGISTERED.value_post_accuracy_weight * post_accuracy
             + REGISTERED.value_pre_validity_weight * pre_validity
             + REGISTERED.value_post_validity_weight * post_validity)
    left_count = (pre == LEFT).sum(axis=1)
    right_count = (pre == RIGHT).sum(axis=1)
    valid_majority = left_count != right_count
    majority = np.where(left_count > right_count, LEFT, RIGHT)
    fragmentation = np.where(
        valid_majority,
        1.0 - (post == majority[:, None]).sum(axis=1) / float(batch.n),
        1.0,
    )
    return Outcomes(
        value=value, mission=mission, fragmentation=fragmentation,
        pre_accuracy=pre_accuracy, post_accuracy=post_accuracy,
        pre_validity=pre_validity, post_validity=post_validity,
    )


def scripted_oracle_actions(batch: EpisodeBatch) -> tuple[np.ndarray, np.ndarray]:
    action = np.broadcast_to(batch.target[:, None], (len(batch.target), batch.n)).copy()
    return action, action.copy()

