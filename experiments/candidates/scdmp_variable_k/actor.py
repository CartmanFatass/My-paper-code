from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import torch

from .config import ACTIONS, N_AGENTS, V_STAR
from .dgp import PhysicalState, factorized_true_panel
from .model import SCDMPModel, encode_words, one_hot_actions


@dataclass(frozen=True)
class LearnedActionPanel:
    terminal: np.ndarray       # [4,3,2]
    node_reward: np.ndarray    # [4,3]
    edge_reward: np.ndarray    # [4,3,3]
    node_factors: np.ndarray   # [4,3]
    edge_factors: np.ndarray   # [4,3,3]
    selected_action: tuple[int, int, int, int]
    selected_score: float
    minimum_score: float
    score_range: float


def _candidate_factors(
    model: SCDMPModel, state: PhysicalState, context_word: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return batched node/edge predictions and exact-cycle factors."""
    state_e = np.repeat(state.e[:, None], 3, axis=1)
    state_v = np.repeat(state.v[:, None], 3, axis=1)
    return candidate_factors_from_action_states(
        model, state_e, state_v, state.q, context_word,
    )


def candidate_factors_from_action_states(
    model: SCDMPModel,
    state_e: np.ndarray,
    state_v: np.ndarray,
    state_q: np.ndarray,
    context_word: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate the 12 node/action and 36 edge/action-pair factors once."""
    duration_value = np.float32(len(context_word) / 12.0)
    if state_e.shape != (N_AGENTS, 3) or state_v.shape != (N_AGENTS, 3):
        raise ValueError("action-conditioned states must have shape [4,3]")
    q = np.repeat(np.asarray(state_q, dtype=np.float64)[:, None], 3, axis=1)
    normalized = np.stack((state_e / 1.5, state_v / 0.6, q), axis=-1).reshape(
        N_AGENTS * 3, 3,
    ).astype(np.float32, copy=False)
    action_values = np.tile(np.asarray(ACTIONS, dtype=np.int64), N_AGENTS).reshape(-1, 1)
    action_one_hot = one_hot_actions(action_values).reshape(N_AGENTS * 3, 3)
    word_sequence = encode_words([context_word] * (N_AGENTS * 3))
    duration = torch.full((N_AGENTS * 3, 1), duration_value, dtype=torch.float32)
    with torch.no_grad():
        normalized_tensor = torch.as_tensor(normalized, dtype=torch.float32)
        node_encoding = model.node_encoding(normalized_tensor)
        action_encoding = model.action_encoding(action_one_hot)
        word_encoding = model.word_encoding(word_sequence)
        terminal_tensor = model.transition_from_encoded(
            node_encoding, action_encoding, word_encoding, duration,
        )
        node_reward_tensor = model.node_reward_from_encoded(
            node_encoding, action_encoding, word_encoding, duration,
        )
        left_indices: list[int] = []
        right_indices: list[int] = []
        for slot in range(N_AGENTS):
            neighbor = (slot + 1) % N_AGENTS
            for left_action in range(3):
                for right_action in range(3):
                    left_indices.append(3 * slot + left_action)
                    right_indices.append(3 * neighbor + right_action)
        left = torch.as_tensor(left_indices, dtype=torch.long)
        right = torch.as_tensor(right_indices, dtype=torch.long)
        edge_reward_tensor = model.edge_reward_from_encoded(
            node_encoding[left], node_encoding[right],
            action_encoding[left], action_encoding[right],
            word_encoding[left], duration[left],
        )
    terminal = terminal_tensor.to(dtype=torch.float64).cpu().numpy().reshape(N_AGENTS, 3, 2)
    node_reward = node_reward_tensor.to(dtype=torch.float64).cpu().numpy().reshape(N_AGENTS, 3)
    edge_reward = edge_reward_tensor.to(dtype=torch.float64).cpu().numpy().reshape(N_AGENTS, 3, 3)
    node_scores = node_reward.copy()
    node_scores += -0.25 * np.square(terminal[:, :, 0]) / 4.0
    node_scores += -0.125 * np.square(terminal[:, :, 1] - V_STAR) / 4.0
    edge_scores = edge_reward.copy()
    for slot in range(N_AGENTS):
        neighbor = (slot + 1) % N_AGENTS
        for left_action in range(3):
            for right_action in range(3):
                predicted_gap = (
                    1.0 + terminal[neighbor, right_action, 0] - terminal[slot, left_action, 0]
                )
                edge_scores[slot, left_action, right_action] += (
                    -0.375 * (predicted_gap - 1.0) ** 2 / 4.0
                    - 1.0 * float(predicted_gap < 0.25) / 4.0
                )
    return node_scores, edge_scores, terminal, node_reward, edge_reward


def cycle_extreme(
    node: np.ndarray, edge: np.ndarray, *, maximize: bool = True,
) -> tuple[tuple[int, int, int, int], float]:
    if not maximize:
        action, negated = cycle_extreme(-node, -edge, maximize=True)
        return action, -negated
    best_action: tuple[int, int, int, int] | None = None
    best_score = -float("inf")
    for first in range(3):
        paths: dict[int, tuple[float, tuple[int, ...]]] = {
            first: (float(node[0, first]), (first,))
        }
        for slot in range(1, N_AGENTS):
            next_paths: dict[int, tuple[float, tuple[int, ...]]] = {}
            for current in range(3):
                candidates = [
                    (score + float(edge[slot - 1, previous, current])
                     + float(node[slot, current]), path + (current,))
                    for previous, (score, path) in paths.items()
                ]
                winner = candidates[0]
                for candidate in candidates[1:]:
                    if candidate[0] > winner[0] or (
                        candidate[0] == winner[0] and candidate[1] < winner[1]
                    ):
                        winner = candidate
                next_paths[current] = winner
            paths = next_paths
        for last, (open_score, path) in paths.items():
            score = open_score + float(edge[N_AGENTS - 1, last, first])
            action = tuple(ACTIONS[index] for index in path)
            if best_action is None or score > best_score or (
                score == best_score and action < best_action
            ):
                best_score, best_action = score, action  # type: ignore[assignment]
    if best_action is None:
        raise RuntimeError("exact actor produced no action")
    return best_action, best_score


def factor_score(
    node: np.ndarray, edge: np.ndarray, action: tuple[int, int, int, int],
) -> float:
    digits = tuple(value + 1 for value in action)
    score = float(node[0, digits[0]])
    for slot in range(1, N_AGENTS):
        score += float(edge[slot - 1, digits[slot - 1], digits[slot]])
        score += float(node[slot, digits[slot]])
    score += float(edge[N_AGENTS - 1, digits[-1], digits[0]])
    return score


def learned_action_panel(
    model: SCDMPModel, state: PhysicalState, context_word: tuple[str, ...],
) -> LearnedActionPanel:
    node, edge, terminal, node_reward, edge_reward = _candidate_factors(
        model, state, context_word,
    )
    action, score = cycle_extreme(node, edge)
    _minimum_action, minimum_score = cycle_extreme(node, edge, maximize=False)
    if score != factor_score(node, edge, action):
        raise RuntimeError("cycle DP and selected factor score disagree")
    return LearnedActionPanel(
        terminal=terminal, node_reward=node_reward, edge_reward=edge_reward,
        node_factors=node, edge_factors=edge,
        selected_action=action, selected_score=score,
        minimum_score=minimum_score, score_range=score - minimum_score,
    )


def exact_cycle_actor(
    model: SCDMPModel, state: PhysicalState, context_word: tuple[str, ...],
) -> tuple[tuple[int, int, int, int], float, float]:
    started = time.perf_counter()
    panel = learned_action_panel(model, state, context_word)
    return panel.selected_action, panel.selected_score, time.perf_counter() - started


def constrained_oracle(
    state: PhysicalState, context_word: tuple[str, ...],
) -> tuple[tuple[int, int, int, int], float]:
    """First exact float64 maximum in slotwise lexicographic joint-action order."""
    _terminal, _node_reward, _edge_reward, node, edge, _steps = factorized_true_panel(
        state, context_word,
    )
    return cycle_extreme(node, edge)
