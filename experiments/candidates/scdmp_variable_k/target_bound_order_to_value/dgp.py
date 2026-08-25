from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

from .config import ACTIONS, EVENT_TO_INDEX


@dataclass(frozen=True)
class Rollout:
    terminal: np.ndarray
    reward: float
    failed: bool
    states: tuple[np.ndarray, ...]
    rewards: tuple[float, ...]


def words(k: int, sigma: int, gamma: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if k < 4 or k % 2 or sigma not in (-1, 1) or gamma not in (-1, 1):
        raise ValueError("word requires even k>=4 and signs in {-1,+1}")
    h = k // 2 - 1
    forward = ("C",) * h + (f"S{'+' if sigma > 0 else '-'}",) \
        + ("C",) * (k - 2 - h) + (f"G{'+' if gamma > 0 else '-'}",)
    return forward, tuple(reversed(forward))


def factor_words(k: int, sigma: int, gamma: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    h = k // 2 - 1
    p = ("C",) * h + (f"S{'+' if sigma > 0 else '-'}",) + ("C",) * h
    q = (f"G{'+' if gamma > 0 else '-'}",)
    return p, q


def event_indices(word: tuple[str, ...]) -> np.ndarray:
    return np.asarray([EVENT_TO_INDEX[event] for event in word], dtype=np.int64)


def _failed(state: np.ndarray) -> bool:
    return bool(np.max(np.abs(state[5:])) > 1.35 or abs(float(state[2])) > 0.95)


def transition(state: np.ndarray, action: tuple[int, int, int, int], event: str) \
        -> tuple[np.ndarray, float, bool]:
    x = np.asarray(state, dtype=np.float64)
    if x.shape != (9,):
        raise ValueError("payload state must have nine coordinates")
    if _failed(x):
        return x.copy(), -1.0, True
    y, v, psi, omega, b, z_fl, z_fr, z_rl, z_rr = map(float, x)
    u_fl, u_fr, u_rl, u_rr = action
    sigma = 1 if event == "S+" else -1 if event == "S-" else 0
    gamma = 1 if event == "G+" else -1 if event == "G-" else 0
    b_next = float(np.clip(b + sigma * 0.4, -0.8, 0.8))
    force = (u_fl + u_fr + u_rl + u_rr) / 4.0
    moment = (u_fl - u_fr + u_rl - u_rr) / 4.0
    v_next = 0.8 * v + 0.4 * force + 0.5 * gamma
    omega_next = 0.8 * omega + 0.4 * moment + 0.1 * b_next + 1.5 * gamma * b_next
    y_next = y + v_next
    psi_next = psi + omega_next
    z_next = (
        0.8 * z_fl + 0.2 * (y_next + psi_next - b_next) - 0.4 * u_fl,
        0.8 * z_fr + 0.2 * (y_next - psi_next - b_next) - 0.4 * u_fr,
        0.8 * z_rl + 0.2 * (-y_next + psi_next + b_next) - 0.4 * u_rl,
        0.8 * z_rr + 0.2 * (-y_next - psi_next + b_next) - 0.4 * u_rr,
    )
    terminal = np.asarray(
        (y_next, v_next, psi_next, omega_next, b_next, *z_next), dtype=np.float64,
    )
    q = (
        y_next ** 2 + 0.35 * v_next ** 2 + 1.4 * psi_next ** 2
        + 0.45 * omega_next ** 2 + 0.30 * float(np.mean(np.square(z_next)))
        + 0.12 * float(np.mean(np.square(action)))
    )
    reward = 1.0 - q
    reward -= 2.5 * max(0.0, max(abs(value) for value in z_next) - 1.0) ** 2
    reward -= 3.0 * max(0.0, abs(psi_next) - 0.7) ** 2
    return terminal, float(reward), _failed(terminal)


def rollout(state: np.ndarray, action: tuple[int, int, int, int],
            word: tuple[str, ...]) -> Rollout:
    current = np.asarray(state, dtype=np.float64).copy()
    states = [current.copy()]
    rewards: list[float] = []
    failed = _failed(current)
    for event in word:
        if failed:
            reward = -1.0
            terminal = current.copy()
        else:
            terminal, reward, failed = transition(current, action, event)
        current = terminal
        states.append(current.copy())
        rewards.append(float(reward))
    return Rollout(current, float(sum(rewards)), failed, tuple(states), tuple(rewards))


def all_action_truth(state: np.ndarray, word: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    terminals = np.empty((len(ACTIONS), 9), dtype=np.float64)
    rewards = np.empty(len(ACTIONS), dtype=np.float64)
    for index, action in enumerate(ACTIONS):
        outcome = rollout(state, action, word)
        terminals[index] = outcome.terminal
        rewards[index] = outcome.reward
    return terminals, rewards


def lexargmax(values: np.ndarray) -> int:
    array = np.asarray(values)
    if array.shape != (81,):
        raise ValueError("held-action scorer must contain 81 actions")
    return int(np.argmax(array))


def oracle(rewards: np.ndarray, k: int) -> tuple[int, float, bool]:
    order = np.argsort(-np.asarray(rewards), kind="stable")
    best, second = int(order[0]), int(order[1])
    gap = float(rewards[best] - rewards[second])
    return best, gap, bool(gap > 0.02 * k)


def order_blind_oracle(forward_rewards: np.ndarray, reverse_rewards: np.ndarray) -> int:
    return lexargmax(0.5 * (np.asarray(forward_rewards) + np.asarray(reverse_rewards)))
