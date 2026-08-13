from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np

from .config import (
    AUDIT_STATES_PER_DURATION, AUDIT_WARMUP_STEPS, N_AGENTS, SCORED_REGIMES,
    TARGET_WORD_PATTERNS, TRAIN_WORD_PATTERNS, V_STAR, word,
)
from .dgp import (
    PhysicalState, class_for_episode, gaps, joint_action_from_index, primitive_step,
    reset_from_raw, rollout_interval,
)
from .actor import exact_cycle_actor
from .model import SCDMPModel


@dataclass(frozen=True)
class AuditInstance:
    global_index: int
    duration: int
    dynamics_class: str
    word_row: int
    slot_offset: int
    severity: str
    state: PhysicalState
    target_word: tuple[str, ...]
    reverse_word: tuple[str, ...]


@dataclass(frozen=True)
class ScoredEpisode:
    arm: str
    algorithm_seed: int
    regime: str
    episode_index: int
    initial_word_row: int
    dynamics_class: str
    normalized_return: float
    failure: int
    collision_steps: int
    minimum_gap: float
    clipping_steps: int
    position_error_rms: float
    worst_agent_position_error: float
    velocity_error_rms: float
    joint_action_changes: int
    scalar_action_changes: int
    energy_proxy: float
    boundary_latency_seconds: float
    boundary_count: int
    boundary_message_count: int


def audit_instances(algorithm_seed: int) -> tuple[list[AuditInstance], int]:
    rows: list[AuditInstance] = []
    microsteps = 0
    mild_e = np.asarray((-0.06, 0.02, 0.06, -0.02), dtype=np.float64)
    mild_v = np.asarray((0.17, 0.23, 0.19, 0.21), dtype=np.float64)
    severe_e = np.asarray((-0.18, 0.06, 0.18, -0.06), dtype=np.float64)
    severe_v = np.asarray((0.10, 0.30, 0.14, 0.26), dtype=np.float64)
    q_base = np.asarray((1.0, -1.0, 1.0, -1.0), dtype=np.float64)
    for duration_block, duration in enumerate((6, 12)):
        for local_index in range(AUDIT_STATES_PER_DURATION):
            global_index = 32 * duration_block + local_index
            class_index = local_index // 16
            dynamics_class = "REAL" if class_index == 0 else "SHAM"
            word_row = (local_index % 16) // 4
            slot_offset = local_index % 4
            severity_index = (word_row + slot_offset) % 2
            base_e, base_v = (mild_e, mild_v) if severity_index == 0 else (severe_e, severe_v)
            state = PhysicalState(
                e=np.roll(base_e, -slot_offset), v=np.roll(base_v, -slot_offset),
                q=np.roll(q_base, -slot_offset),
            )
            for boundary_index in range(12):
                warmup_row = (word_row + boundary_index) % 4
                warmup_word = word(TRAIN_WORD_PATTERNS[4][warmup_row], dynamics_class)
                action_index = (global_index + 31 * algorithm_seed + boundary_index) % 81
                state = rollout_interval(
                    state, joint_action_from_index(action_index), warmup_word,
                ).terminal
                microsteps += 4
            target = word(TARGET_WORD_PATTERNS[duration][word_row], dynamics_class)
            rows.append(AuditInstance(
                global_index=global_index, duration=duration,
                dynamics_class=dynamics_class, word_row=word_row,
                slot_offset=slot_offset,
                severity="MILD" if severity_index == 0 else "SEVERE",
                state=state, target_word=target, reverse_word=tuple(reversed(target)),
            ))
    return rows, microsteps


def scored_reset_tapes(algorithm_seed: int) -> dict[str, tuple[PhysicalState, ...]]:
    tapes: dict[str, tuple[PhysicalState, ...]] = {}
    for regime_index, regime in enumerate(SCORED_REGIMES):
        bit_generator = np.random.PCG64(750_000 + 1_000 * algorithm_seed + regime_index)
        tapes[regime] = tuple(reset_from_raw(bit_generator) for _ in range(32))
    return tapes


def _segments(regime: str) -> tuple[tuple[int, int, int, bool], ...]:
    if regime == "fixed_4":
        return ((0, 240, 4, False),)
    if regime == "fixed_8":
        return ((0, 240, 8, False),)
    if regime == "fixed_6":
        return ((0, 240, 6, True),)
    if regime == "fixed_12":
        return ((0, 240, 12, True),)
    if regime == "switch_6_to_12":
        return ((0, 120, 6, True), (120, 240, 12, True))
    if regime == "switch_12_to_6":
        return ((0, 120, 12, True), (120, 240, 6, True))
    raise ValueError(f"unknown scored regime: {regime}")


def run_scored_episode(
    *, model: SCDMPModel, arm: str, algorithm_seed: int, regime: str,
    episode_index: int, reset_state: PhysicalState,
) -> ScoredEpisode:
    dynamics_class = class_for_episode(episode_index)
    state = reset_state.clone()
    total_reward = np.float64(0.0)
    collision_steps = 0
    clipping_steps = 0
    minimum_gap = float(np.min(gaps(state)))
    squared_e: list[np.ndarray] = []
    squared_v_error: list[np.ndarray] = []
    absolute_e: list[np.ndarray] = []
    energy_sum = 0.0
    primitive_agent_count = 0
    boundary_latency = 0.0
    boundary_count = 0
    joint_action_changes = 0
    scalar_action_changes = 0
    previous_action: tuple[int, int, int, int] | None = None
    for _start, _stop, duration, target in _segments(regime):
        segment_boundary = 0
        for _boundary_start in range(_start, _stop, duration):
            patterns = TARGET_WORD_PATTERNS if target else TRAIN_WORD_PATTERNS
            row = (episode_index % 4 + segment_boundary) % 4
            context_word = word(patterns[duration][row], dynamics_class)
            action, _score, latency = exact_cycle_actor(model, state, context_word)
            boundary_latency += latency
            boundary_count += 1
            if previous_action is not None:
                joint_action_changes += int(action != previous_action)
                scalar_action_changes += sum(
                    int(current != previous) for current, previous in zip(action, previous_action)
                )
            previous_action = action
            for token in context_word:
                state, node, edge, collided, clipped, step_minimum = primitive_step(state, action, token)
                total_reward += np.sum(node) + np.sum(edge)
                collision_steps += int(collided)
                clipping_steps += int(clipped)
                minimum_gap = min(minimum_gap, step_minimum)
                squared_e.append(np.square(state.e))
                squared_v_error.append(np.square(state.v - np.float64(V_STAR)))
                absolute_e.append(np.abs(state.e))
                energy_sum += sum(value * value for value in action)
                primitive_agent_count += N_AGENTS
            segment_boundary += 1
    stacked_e = np.stack(squared_e)
    stacked_v = np.stack(squared_v_error)
    stacked_absolute_e = np.stack(absolute_e)
    return ScoredEpisode(
        arm=arm, algorithm_seed=algorithm_seed, regime=regime,
        episode_index=episode_index, initial_word_row=episode_index % 4,
        dynamics_class=dynamics_class,
        normalized_return=float(total_reward / np.float64(240.0)),
        failure=int(collision_steps > 0 or clipping_steps > 0),
        collision_steps=collision_steps, minimum_gap=minimum_gap,
        clipping_steps=clipping_steps,
        position_error_rms=float(np.sqrt(np.mean(stacked_e))),
        worst_agent_position_error=float(np.max(stacked_absolute_e)),
        velocity_error_rms=float(np.sqrt(np.mean(stacked_v))),
        joint_action_changes=joint_action_changes,
        scalar_action_changes=scalar_action_changes,
        energy_proxy=float(energy_sum / primitive_agent_count),
        boundary_latency_seconds=boundary_latency,
        boundary_count=boundary_count,
        boundary_message_count=N_AGENTS * boundary_count,
    )


def evaluate_scored_pair(
    algorithm_seed: int, models: dict[str, SCDMPModel],
    resource_check: Callable[[], None] | None = None,
) -> tuple[list[ScoredEpisode], int]:
    tapes = scored_reset_tapes(algorithm_seed)
    rows: list[ScoredEpisode] = []
    microsteps = 0
    for regime in SCORED_REGIMES:
        for episode_index, reset_state in enumerate(tapes[regime]):
            if resource_check is not None:
                resource_check()
            for arm in ("SCDMP", "SCDMP-NOCOMP"):
                rows.append(run_scored_episode(
                    model=models[arm], arm=arm, algorithm_seed=algorithm_seed,
                    regime=regime, episode_index=episode_index, reset_state=reset_state,
                ))
                microsteps += 240
    return rows, microsteps


def scored_rows_as_dicts(rows: list[ScoredEpisode]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def audit_denominators() -> dict[str, int]:
    return {
        "physical_states_per_seed": 64,
        "reversal_twins_per_seed": 64,
        "word_state_instances_per_seed": 128,
        "word_state_action_rollouts_per_seed": 128 * 81,
        "real_word_state_instances_per_seed": 64,
        "real_action_panels_per_seed": 64 * 81,
        "sham_word_state_instances_per_seed": 64,
        "sham_action_panels_per_seed": 64 * 81,
    }
