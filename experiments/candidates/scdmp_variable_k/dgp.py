from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .config import (
    E_BOUND, GAP_FAILURE, N_AGENTS, POSITION_STEP, TOKEN_COEFFICIENTS,
    TRAIN_WORD_PATTERNS, V_BOUND, V_STAR, WIND_ACCELERATION, ACTION_ACCELERATION,
    word,
)
from .rng import raw_word, u0


@dataclass(frozen=True)
class PhysicalState:
    e: np.ndarray
    v: np.ndarray
    q: np.ndarray

    def clone(self) -> "PhysicalState":
        return PhysicalState(self.e.copy(), self.v.copy(), self.q.copy())


@dataclass(frozen=True)
class IntervalOutcome:
    initial: PhysicalState
    terminal: PhysicalState
    action: tuple[int, int, int, int]
    word: tuple[str, ...]
    node_rewards: np.ndarray
    edge_rewards: np.ndarray
    total_reward: float
    collision_steps: int
    clipping_steps: int
    minimum_gap: float
    state_trace: tuple[PhysicalState, ...] | None = None
    node_reward_trace: tuple[np.ndarray, ...] | None = None
    edge_reward_trace: tuple[np.ndarray, ...] | None = None


def reset_from_raw(bit_generator: np.random.PCG64) -> PhysicalState:
    raw_q = raw_word(bit_generator)
    raw_e = [raw_word(bit_generator) for _ in range(N_AGENTS)]
    raw_v = [raw_word(bit_generator) for _ in range(N_AGENTS)]
    rotation = raw_q % N_AGENTS
    q_base = np.asarray((1.0, -1.0, 1.0, -1.0), dtype=np.float64)
    q = np.roll(q_base, -rotation)
    e_raw = np.asarray(
        [np.float64(-0.20) + np.float64(0.40) * u0(value) for value in raw_e],
        dtype=np.float64,
    )
    v = np.asarray(
        [np.float64(0.10) + np.float64(0.20) * u0(value) for value in raw_v],
        dtype=np.float64,
    )
    mean_e = (((e_raw[0] + e_raw[1]) + e_raw[2]) + e_raw[3]) / np.float64(4.0)
    return PhysicalState(e=e_raw - mean_e, v=v, q=q)


def gaps(state: PhysicalState) -> np.ndarray:
    return np.float64(1.0) + np.roll(state.e, -1) - state.e


def primitive_step(
    state: PhysicalState, action: Sequence[int], token: str,
) -> tuple[PhysicalState, np.ndarray, np.ndarray, bool, bool, float]:
    rho, sigma = TOKEN_COEFFICIENTS[token]
    u = np.asarray(action, dtype=np.float64)
    v_next = np.clip(
        np.float64(rho) * state.v
        + np.float64(ACTION_ACCELERATION) * u
        + np.float64(WIND_ACCELERATION * sigma) * state.q,
        np.float64(-V_BOUND), np.float64(V_BOUND),
    )
    e_next = np.clip(
        state.e + np.float64(POSITION_STEP) * (v_next - np.float64(V_STAR)),
        np.float64(-E_BOUND), np.float64(E_BOUND),
    )
    terminal = PhysicalState(e=e_next, v=v_next, q=state.q.copy())
    terminal_gaps = gaps(terminal)
    clipped = bool(np.any(np.abs(e_next) == np.float64(E_BOUND)))
    collided = bool(np.any(terminal_gaps < np.float64(GAP_FAILURE)))
    node = (
        np.float64(0.25)
        - np.float64(0.50 / 4.0) * np.square(e_next)
        - np.float64(0.25 / 4.0) * np.square(v_next - np.float64(V_STAR))
        - np.float64(0.02 / 4.0) * np.square(u)
        - np.float64(0.25 / 4.0) * (np.abs(e_next) == np.float64(E_BOUND))
    )
    edge = (
        -np.float64(0.75 / 4.0) * np.square(terminal_gaps - np.float64(1.0))
        -np.float64(2.00 / 4.0) * (terminal_gaps < np.float64(GAP_FAILURE))
    )
    return terminal, node, edge, collided, clipped, float(np.min(terminal_gaps))


def rollout_interval(
    initial: PhysicalState, action: Sequence[int], context_word: Sequence[str],
    *, capture_trace: bool = False,
) -> IntervalOutcome:
    state = initial.clone()
    node_rewards = np.zeros(N_AGENTS, dtype=np.float64)
    edge_rewards = np.zeros(N_AGENTS, dtype=np.float64)
    collision_steps = 0
    clipping_steps = 0
    minimum_gap = float(np.min(gaps(state)))
    state_trace: list[PhysicalState] = []
    node_trace: list[np.ndarray] = []
    edge_trace: list[np.ndarray] = []
    for token in context_word:
        state, node, edge, collided, clipped, step_minimum = primitive_step(state, action, token)
        if capture_trace:
            state_trace.append(state.clone())
            node_trace.append(node.copy())
            edge_trace.append(edge.copy())
        node_rewards += node
        edge_rewards += edge
        collision_steps += int(collided)
        clipping_steps += int(clipped)
        minimum_gap = min(minimum_gap, step_minimum)
    return IntervalOutcome(
        initial=initial.clone(), terminal=state, action=tuple(int(x) for x in action),
        word=tuple(context_word), node_rewards=node_rewards, edge_rewards=edge_rewards,
        total_reward=float(np.sum(node_rewards) + np.sum(edge_rewards)),
        collision_steps=collision_steps, clipping_steps=clipping_steps,
        minimum_gap=minimum_gap,
        state_trace=tuple(state_trace) if capture_trace else None,
        node_reward_trace=tuple(node_trace) if capture_trace else None,
        edge_reward_trace=tuple(edge_trace) if capture_trace else None,
    )


def class_for_episode(episode_index: int) -> str:
    return "REAL" if episode_index % 8 < 4 else "SHAM"


def scheduled_word(
    duration: int, dynamics_class: str, episode_index: int, boundary_index: int,
) -> tuple[str, ...]:
    row = (episode_index % 4 + boundary_index) % 4
    return word(TRAIN_WORD_PATTERNS[duration][row], dynamics_class)


def joint_action_from_index(index: int) -> tuple[int, int, int, int]:
    if not 0 <= index < 81:
        raise ValueError("joint-action index must be in [0,80]")
    digits: list[int] = []
    remainder = index
    for place in (27, 9, 3, 1):
        digit, remainder = divmod(remainder, place)
        digits.append((-1, 0, 1)[digit])
    return tuple(digits)  # type: ignore[return-value]


def joint_action_index(action: Sequence[int]) -> int:
    digit = {-1: 0, 0: 1, 1: 2}
    return sum(digit[int(value)] * place for value, place in zip(action, (27, 9, 3, 1)))


def terminal_potential(state: PhysicalState) -> float:
    node = (
        -np.float64(0.25 / 4.0) * np.square(state.e)
        -np.float64(0.125 / 4.0) * np.square(state.v - np.float64(V_STAR))
    )
    state_gaps = gaps(state)
    edge = (
        -np.float64(0.375 / 4.0) * np.square(state_gaps - np.float64(1.0))
        -np.float64(1.00 / 4.0) * (state_gaps < np.float64(GAP_FAILURE))
    )
    return float(np.sum(node) + np.sum(edge))


def factorized_true_panel(
    state: PhysicalState, context_word: Sequence[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """Exact fixed-degree 81-action panel from 12 independent node trajectories.

    The dynamics are node-separable under a held action.  Each directed-edge
    reward and terminal potential is therefore obtained from the cached pair of
    adjacent node trajectories, without advancing a joint-action candidate.
    """
    duration = len(context_word)
    terminal = np.empty((N_AGENTS, 3, 2), dtype=np.float64)
    node_reward = np.zeros((N_AGENTS, 3), dtype=np.float64)
    e_trace = np.empty((N_AGENTS, 3, duration), dtype=np.float64)
    for slot in range(N_AGENTS):
        for action_index, action in enumerate((-1, 0, 1)):
            e_value = np.float64(state.e[slot])
            v_value = np.float64(state.v[slot])
            q_value = np.float64(state.q[slot])
            u_value = np.float64(action)
            for offset, token in enumerate(context_word):
                rho, sigma = TOKEN_COEFFICIENTS[token]
                v_value = np.clip(
                    np.float64(rho) * v_value
                    + np.float64(ACTION_ACCELERATION) * u_value
                    + np.float64(WIND_ACCELERATION * sigma) * q_value,
                    np.float64(-V_BOUND), np.float64(V_BOUND),
                )
                e_value = np.clip(
                    e_value + np.float64(POSITION_STEP) * (v_value - np.float64(V_STAR)),
                    np.float64(-E_BOUND), np.float64(E_BOUND),
                )
                e_trace[slot, action_index, offset] = e_value
                node_reward[slot, action_index] += (
                    np.float64(0.25)
                    - np.float64(0.50 / 4.0) * np.square(e_value)
                    - np.float64(0.25 / 4.0) * np.square(v_value - np.float64(V_STAR))
                    - np.float64(0.02 / 4.0) * np.square(u_value)
                    - np.float64(0.25 / 4.0) * np.float64(abs(e_value) == np.float64(E_BOUND))
                )
            terminal[slot, action_index] = (e_value, v_value)
    edge_reward = np.zeros((N_AGENTS, 3, 3), dtype=np.float64)
    for slot in range(N_AGENTS):
        neighbor = (slot + 1) % N_AGENTS
        for left_action in range(3):
            for right_action in range(3):
                gap_trace = (
                    np.float64(1.0) + e_trace[neighbor, right_action]
                    - e_trace[slot, left_action]
                )
                accumulated = np.float64(0.0)
                for gap_value in gap_trace:
                    accumulated += (
                        -np.float64(0.75 / 4.0)
                        * np.square(gap_value - np.float64(1.0))
                        -np.float64(2.00 / 4.0)
                        * np.float64(gap_value < np.float64(GAP_FAILURE))
                    )
                edge_reward[slot, left_action, right_action] = accumulated
    node_score = node_reward.copy()
    node_score += -np.float64(0.25 / 4.0) * np.square(terminal[..., 0])
    node_score += -np.float64(0.125 / 4.0) * np.square(
        terminal[..., 1] - np.float64(V_STAR)
    )
    edge_score = edge_reward.copy()
    for slot in range(N_AGENTS):
        neighbor = (slot + 1) % N_AGENTS
        terminal_gap = (
            np.float64(1.0) + terminal[neighbor, :, 0][None, :]
            - terminal[slot, :, 0][:, None]
        )
        edge_score[slot] += (
            -np.float64(0.375 / 4.0) * np.square(terminal_gap - np.float64(1.0))
            -np.float64(1.00 / 4.0) * (terminal_gap < np.float64(GAP_FAILURE))
        )
    return terminal, node_reward, edge_reward, node_score, edge_score, N_AGENTS * 3 * duration
