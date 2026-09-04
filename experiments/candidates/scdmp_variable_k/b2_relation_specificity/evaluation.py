from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict

import numpy as np

from ..dgp import PhysicalState, class_for_episode, joint_action_from_index, reset_from_raw, rollout_interval
from ..evaluation import AuditInstance, ScoredEpisode, run_scored_episode
from ..config import TARGET_WORD_PATTERNS, TRAIN_WORD_PATTERNS, word
from .config import ARMS, SCORED_REGIMES
from .model import SCDMPModel


def audit_instances(algorithm_seed: int) -> tuple[list[AuditInstance], int]:
    rows: list[AuditInstance] = []
    mild_e = np.asarray((-0.08, 0.03, 0.08, -0.03), dtype=np.float64)
    mild_v = np.asarray((0.16, 0.24, 0.18, 0.22), dtype=np.float64)
    severe_e = np.asarray((-0.21, 0.07, 0.21, -0.07), dtype=np.float64)
    severe_v = np.asarray((0.08, 0.32, 0.12, 0.28), dtype=np.float64)
    q_base = np.asarray((1.0, -1.0, 1.0, -1.0), dtype=np.float64)
    microsteps = 0
    for duration_block, duration in enumerate((6, 12)):
        for local in range(32):
            global_index = duration_block * 32 + local
            dynamics_class = "REAL" if local < 16 else "SHAM"
            word_row = (local % 16) // 4
            slot_offset = local % 4
            severe = (word_row + slot_offset) % 2 == 1
            state = PhysicalState(np.roll(severe_e if severe else mild_e, -slot_offset),
                                  np.roll(severe_v if severe else mild_v, -slot_offset),
                                  np.roll(q_base, -slot_offset))
            for boundary in range(12):
                warm_word = word(TRAIN_WORD_PATTERNS[4][(word_row + boundary) % 4], dynamics_class)
                action_index = (global_index + 37 * (algorithm_seed - 100) + boundary) % 81
                state = rollout_interval(state, joint_action_from_index(action_index), warm_word).terminal
                microsteps += 4
            target = word(TARGET_WORD_PATTERNS[duration][word_row], dynamics_class)
            rows.append(AuditInstance(global_index, duration, dynamics_class, word_row, slot_offset,
                "SEVERE" if severe else "MILD", state, target, tuple(reversed(target))))
    return rows, microsteps


def scored_reset_tapes(algorithm_seed: int) -> dict[str, tuple[PhysicalState, ...]]:
    result: dict[str, tuple[PhysicalState, ...]] = {}
    for regime_index, regime in enumerate(SCORED_REGIMES):
        bg = np.random.PCG64(850_000 + 1_000 * algorithm_seed + regime_index)
        result[regime] = tuple(reset_from_raw(bg) for _ in range(32))
    return result


def evaluate_scored(algorithm_seed: int, models: dict[str, SCDMPModel],
    resource_check: Callable[[], None] | None = None) -> tuple[list[ScoredEpisode], int]:
    tapes = scored_reset_tapes(algorithm_seed)
    rows: list[ScoredEpisode] = []
    for regime in SCORED_REGIMES:
        for episode_index, reset in enumerate(tapes[regime]):
            if resource_check is not None:
                resource_check()
            for arm in ARMS:
                rows.append(run_scored_episode(model=models[arm], arm=arm,
                    algorithm_seed=algorithm_seed, regime=regime,
                    episode_index=episode_index, reset_state=reset))
    return rows, len(ARMS) * len(SCORED_REGIMES) * 32 * 240


def serialize_scored(rows: list[ScoredEpisode]) -> list[dict[str, object]]:
    return [asdict(r) for r in rows]
