from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import product

import numpy as np
import torch

from .config import (
    ACTIONS, CHECKPOINT_FIT_ROWS, FIT_SUPPORT_ROWS, K_FIT, K_TARGET,
    STATE_BOUNDS, TARGET_BASE_ROWS,
)
from .dgp import event_indices, rollout, words
from .rng import HMACStream, balanced_roster, identity_digests, seed_key


@dataclass(frozen=True)
class Row:
    index: int
    state: np.ndarray
    k: int
    sigma: int
    gamma: int
    orientation: str
    action_index: int | None

    @property
    def word(self) -> tuple[str, ...]:
        forward, reverse = words(self.k, self.sigma, self.gamma)
        return forward if self.orientation == "F" else reverse

    @property
    def action(self) -> tuple[int, int, int, int]:
        if self.action_index is None:
            raise ValueError("target base rows enumerate actions and have no assigned action")
        return ACTIONS[self.action_index]


@dataclass(frozen=True)
class SegmentExamples:
    states: np.ndarray
    actions: np.ndarray
    words: np.ndarray
    lengths: np.ndarray
    terminal: np.ndarray
    reward: np.ndarray
    weights: np.ndarray

    def tensors(self, device: str = "cpu") -> tuple[torch.Tensor, ...]:
        return tuple(torch.as_tensor(value, device=device) for value in (
            self.states.astype(np.float32, copy=False),
            self.actions.astype(np.float32, copy=False),
            self.words.astype(np.int64, copy=False),
            self.lengths.astype(np.int64, copy=False),
            self.terminal.astype(np.float32, copy=False),
            self.reward.astype(np.float32, copy=False),
            self.weights.astype(np.float32, copy=False),
        ))


@dataclass(frozen=True)
class SeedCorpus:
    seed_index: int
    fit: tuple[Row, ...]
    fit_support: tuple[Row, ...]
    targets: dict[int, tuple[Row, ...]]
    draw_counts: dict[str, int]
    block_hashes: dict[str, str]


def _cell_order(k_values: tuple[int, ...]) -> tuple[tuple[int, int, int, str], ...]:
    return tuple(product(k_values, (-1, 1), (-1, 1), ("F", "R")))


def _states(master: bytes, seed_index: int, label: str, count: int) \
        -> tuple[np.ndarray, HMACStream]:
    stream = HMACStream.for_domain(master, seed_index, label)
    values = np.empty((count, 9), dtype=np.float64)
    for row in range(count):
        for coordinate, (low, high) in enumerate(STATE_BOUNDS):
            values[row, coordinate] = stream.uniform(low, high)
    return values, stream


def _rows(master: bytes, seed_index: int, prefix: str, count: int,
          k_values: tuple[int, ...], assigned_actions: bool) \
        -> tuple[tuple[Row, ...], dict[str, int], dict[str, str]]:
    states, state_stream = _states(master, seed_index, f"{prefix}/state", count)
    cell_stream = HMACStream.for_domain(master, seed_index, f"{prefix}/cells")
    cells = balanced_roster(_cell_order(k_values), count, cell_stream)
    if assigned_actions:
        action_stream = HMACStream.for_domain(master, seed_index, f"{prefix}/action")
        action_indices = balanced_roster(tuple(range(len(ACTIONS))), count, action_stream)
    else:
        action_stream = None
        action_indices = [None] * count
    rows = tuple(
        Row(index, states[index].copy(), int(cell[0]), int(cell[1]), int(cell[2]),
            str(cell[3]), action_indices[index])
        for index, cell in enumerate(cells)
    )
    cell_bytes = json.dumps(cells, separators=(",", ":")).encode("utf-8")
    action_bytes = json.dumps(action_indices, separators=(",", ":")).encode("utf-8")
    counts = {
        f"{prefix}/state": state_stream.draw_count,
        f"{prefix}/cells": cell_stream.draw_count,
    }
    if action_stream is not None:
        counts[f"{prefix}/action"] = action_stream.draw_count
    hashes = {
        f"{prefix}/state": hashlib.sha256(states.tobytes(order="C")).hexdigest(),
        f"{prefix}/cells": hashlib.sha256(cell_bytes).hexdigest(),
    }
    if action_stream is not None:
        hashes[f"{prefix}/action"] = hashlib.sha256(action_bytes).hexdigest()
    return rows, counts, hashes


def materialize_seed(master: bytes, seed_index: int) -> SeedCorpus:
    fit, counts, hashes = _rows(
        master, seed_index, "checkpoint_fit", CHECKPOINT_FIT_ROWS, K_FIT, True,
    )
    support, support_counts, support_hashes = _rows(
        master, seed_index, "fit_support", FIT_SUPPORT_ROWS, K_FIT, True,
    )
    counts.update(support_counts)
    hashes.update(support_hashes)
    targets: dict[int, tuple[Row, ...]] = {}
    for k in K_TARGET:
        rows, target_counts, target_hashes = _rows(
            master, seed_index, f"target_k{k}", TARGET_BASE_ROWS, (k,), False,
        )
        targets[k] = rows
        counts.update(target_counts)
        hashes.update(target_hashes)
    return SeedCorpus(seed_index, fit, support, targets, counts, hashes)


def segment_examples(rows: tuple[Row, ...] | list[Row], *, row_equal: bool = True) \
        -> SegmentExamples:
    states: list[np.ndarray] = []
    actions: list[tuple[int, int, int, int]] = []
    token_words: list[np.ndarray] = []
    lengths: list[int] = []
    terminals: list[np.ndarray] = []
    rewards: list[float] = []
    weights: list[float] = []
    row_count = len(rows)
    for row in rows:
        full = rollout(row.state, row.action, row.word)
        atoms = tuple((start, length) for start in range(row.k)
                      for length in range(1, row.k - start + 1))
        atom_weight = (1.0 / row_count / len(atoms)) if row_equal else 1.0
        for start, length in atoms:
            segment_word = row.word[start:start + length]
            start_state = full.states[start]
            truth = rollout(start_state, row.action, segment_word)
            states.append(start_state)
            actions.append(row.action)
            token_words.append(event_indices(segment_word))
            lengths.append(length)
            terminals.append(truth.terminal)
            rewards.append(truth.reward)
            weights.append(atom_weight)
    max_length = max(lengths, default=0)
    padded = np.full((len(lengths), max_length), -1, dtype=np.int64)
    for index, value in enumerate(token_words):
        padded[index, :len(value)] = value
    return SegmentExamples(
        np.asarray(states, dtype=np.float64), np.asarray(actions, dtype=np.int8),
        padded, np.asarray(lengths, dtype=np.int64),
        np.asarray(terminals, dtype=np.float64), np.asarray(rewards, dtype=np.float64),
        np.asarray(weights, dtype=np.float64),
    )


def complete_word_examples(rows: tuple[Row, ...]) -> SegmentExamples:
    states, actions, token_words, lengths, terminals, rewards = [], [], [], [], [], []
    for row in rows:
        truth = rollout(row.state, row.action, row.word)
        states.append(row.state)
        actions.append(row.action)
        token_words.append(event_indices(row.word))
        lengths.append(row.k)
        terminals.append(truth.terminal)
        rewards.append(truth.reward)
    max_length = max(lengths, default=0)
    padded = np.full((len(rows), max_length), -1, dtype=np.int64)
    for index, value in enumerate(token_words):
        padded[index, :len(value)] = value
    weights = np.full(len(rows), 1.0 / len(rows), dtype=np.float64)
    return SegmentExamples(
        np.asarray(states, dtype=np.float64), np.asarray(actions, dtype=np.int8), padded,
        np.asarray(lengths), np.asarray(terminals), np.asarray(rewards), weights,
    )


def output_scales(fit: tuple[Row, ...]) -> tuple[np.ndarray, np.float32]:
    examples = segment_examples(fit)
    # The card requires literal two-pass float64 accumulation in ascending row,
    # then (start,length) atom order. segment_examples preserves exactly that order.
    mean_f = np.zeros(9, dtype=np.float64)
    mean_g = np.float64(0.0)
    for index in range(len(examples.weights)):
        weight = np.float64(examples.weights[index])
        for coordinate in range(9):
            mean_f[coordinate] = np.float64(
                mean_f[coordinate] + weight * np.float64(examples.terminal[index, coordinate])
            )
        mean_g = np.float64(mean_g + weight * np.float64(examples.reward[index]))
    var_f = np.zeros(9, dtype=np.float64)
    var_g = np.float64(0.0)
    for index in range(len(examples.weights)):
        weight = np.float64(examples.weights[index])
        for coordinate in range(9):
            residual = np.float64(examples.terminal[index, coordinate]) - mean_f[coordinate]
            var_f[coordinate] = np.float64(var_f[coordinate] + weight * residual * residual)
        reward_residual = np.float64(examples.reward[index]) - mean_g
        var_g = np.float64(var_g + weight * reward_residual * reward_residual)
    scale_f = np.maximum(np.sqrt(var_f, dtype=np.float64), 1.0e-6).astype(np.float32)
    scale_g = np.float32(max(float(np.sqrt(var_g)), 1.0e-6))
    return scale_f, scale_g


def complete_word_truth_mean(fit: tuple[Row, ...]) -> tuple[np.ndarray, float]:
    examples = complete_word_examples(fit)
    return (np.mean(examples.terminal, axis=0, dtype=np.float64),
            float(np.mean(examples.reward, dtype=np.float64)))


def seed_manifest(master: bytes, corpus: SeedCorpus,
                  initializer_draws: int, minibatch_draws: int) -> dict[str, object]:
    panel_digest, seed_digests = identity_digests(master)
    counts = dict(corpus.draw_counts)
    counts["checkpoint_init"] = initializer_draws
    counts["checkpoint_minibatch"] = minibatch_draws
    return {
        "panel_digest": panel_digest,
        "seed_index": corpus.seed_index,
        "seed_digest": seed_digests[corpus.seed_index],
        "domain_draw_counts": counts,
        "block_hashes": dict(corpus.block_hashes),
    }
