from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import product

import numpy as np
import torch

from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.dgp import (
    event_indices,
    rollout,
    words,
)

from .config import (
    ACTIONS,
    FIT_SUPPORT_ROWS,
    K_FIT,
    K_TARGET,
    S1_ACTION_BASE_REPEATS,
    S1_ACTION_EXTRAS,
    S1_WORD_CELL_ROWS,
    STATE_BOUNDS,
    STATE_COORDINATES,
    TARGET_BASE_ROWS,
    TRAIN_ROWS,
)
from .rng import HMACStream, balanced_roster, identity_digests


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
    train: dict[str, tuple[Row, ...]]
    fit_support: tuple[Row, ...]
    targets: dict[int, tuple[Row, ...]]
    draw_counts: dict[str, int]
    block_hashes: dict[str, str]

    @property
    def evaluation_identity(self) -> str:
        digest = hashlib.sha256()
        for label in sorted(
            key for key in self.block_hashes if key.startswith("eval/")
        ):
            digest.update(label.encode("utf-8"))
            digest.update(self.block_hashes[label].encode("ascii"))
        return digest.hexdigest()


def word_cell_order(k_values: tuple[int, ...]) -> tuple[tuple[int, int, int, str], ...]:
    return tuple(product(k_values, (-1, 1), (-1, 1), ("F", "R")))


def _independent_states(
    master: bytes, seed_index: int, label: str, count: int,
) -> tuple[np.ndarray, HMACStream]:
    stream = HMACStream.for_domain(master, seed_index, label)
    states = np.empty((count, len(STATE_COORDINATES)), dtype=np.float64)
    for row_index in range(count):
        for coordinate, (low, high) in enumerate(STATE_BOUNDS):
            states[row_index, coordinate] = stream.uniform(low, high)
    return states, stream


def _rows_from_rosters(
    states: np.ndarray,
    cells: list[tuple[int, int, int, str]],
    action_indices: list[int | None],
) -> tuple[Row, ...]:
    if not (len(states) == len(cells) == len(action_indices)):
        raise ValueError("state, word-cell and action rosters must have the same length")
    return tuple(
        Row(
            index=index,
            state=states[index].copy(),
            k=int(cell[0]),
            sigma=int(cell[1]),
            gamma=int(cell[2]),
            orientation=str(cell[3]),
            action_index=action_indices[index],
        )
        for index, cell in enumerate(cells)
    )


def _hash_array(value: np.ndarray) -> str:
    return hashlib.sha256(value.tobytes(order="C")).hexdigest()


def _hash_json(value: object) -> str:
    payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _balanced_rows(
    master: bytes,
    seed_index: int,
    prefix: str,
    count: int,
    k_values: tuple[int, ...],
    assigned_actions: bool,
) -> tuple[tuple[Row, ...], dict[str, int], dict[str, str]]:
    states, state_stream = _independent_states(
        master, seed_index, f"{prefix}/state", count,
    )
    cell_stream = HMACStream.for_domain(master, seed_index, f"{prefix}/word_cells")
    cells = balanced_roster(word_cell_order(k_values), count, cell_stream)
    action_stream: HMACStream | None = None
    if assigned_actions:
        action_stream = HMACStream.for_domain(master, seed_index, f"{prefix}/action")
        action_indices: list[int | None] = balanced_roster(
            tuple(range(len(ACTIONS))), count, action_stream,
        )
    else:
        action_indices = [None] * count
    counts = {
        f"{prefix}/state": state_stream.draw_count,
        f"{prefix}/word_cells": cell_stream.draw_count,
    }
    hashes = {
        f"{prefix}/state": _hash_array(states),
        f"{prefix}/word_cells": _hash_json(cells),
    }
    if action_stream is not None:
        counts[f"{prefix}/action"] = action_stream.draw_count
        hashes[f"{prefix}/action"] = _hash_json(action_indices)
    return _rows_from_rosters(states, cells, action_indices), counts, hashes


def _target_rows(
    master: bytes, seed_index: int, k: int,
) -> tuple[tuple[Row, ...], dict[str, int], dict[str, str]]:
    prefix = f"eval/target_k{k}"
    states, state_stream = _independent_states(
        master, seed_index, f"{prefix}/state", TARGET_BASE_ROWS,
    )
    cell_stream = HMACStream.for_domain(master, seed_index, f"{prefix}/cells")
    cells = balanced_roster(word_cell_order((k,)), TARGET_BASE_ROWS, cell_stream)
    actions: list[int | None] = [None] * TARGET_BASE_ROWS
    return (
        _rows_from_rosters(states, cells, actions),
        {
            f"{prefix}/state": state_stream.draw_count,
            f"{prefix}/cells": cell_stream.draw_count,
        },
        {
            f"{prefix}/state": _hash_array(states),
            f"{prefix}/cells": _hash_json(cells),
        },
    )


def _s1_rows(
    master: bytes, seed_index: int,
) -> tuple[tuple[Row, ...], dict[str, int], dict[str, str]]:
    states = np.empty((TRAIN_ROWS, len(STATE_COORDINATES)), dtype=np.float64)
    counts: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for coordinate, (name, (low, high)) in enumerate(zip(STATE_COORDINATES, STATE_BOUNDS)):
        lhs_label = f"train/S1/state_lhs/{name}"
        jitter_label = f"train/S1/jitter/{name}"
        lhs_stream = HMACStream.for_domain(master, seed_index, lhs_label)
        jitter_stream = HMACStream.for_domain(master, seed_index, jitter_label)
        strata = list(range(TRAIN_ROWS))
        lhs_stream.shuffle(strata)
        for row_index, stratum in enumerate(strata):
            unit = (stratum + jitter_stream.uniform53()) / TRAIN_ROWS
            states[row_index, coordinate] = low + (high - low) * unit
        counts[lhs_label] = lhs_stream.draw_count
        counts[jitter_label] = jitter_stream.draw_count
        hashes[lhs_label] = _hash_json(strata)
        hashes[jitter_label] = _hash_array(states[:, coordinate])

    roster_stream = HMACStream.for_domain(master, seed_index, "train/S1/word_action")
    word_action: list[tuple[tuple[int, int, int, str], int]] = []
    for cell in word_cell_order(K_FIT):
        extras = list(range(len(ACTIONS)))
        roster_stream.shuffle(extras)
        action_indices = list(range(len(ACTIONS))) * S1_ACTION_BASE_REPEATS
        action_indices.extend(extras[:S1_ACTION_EXTRAS])
        if len(action_indices) != S1_WORD_CELL_ROWS:
            raise RuntimeError("S1 word-action cell does not contain exactly 256 rows")
        word_action.extend((cell, action_index) for action_index in action_indices)
    if len(word_action) != TRAIN_ROWS:
        raise RuntimeError("S1 complete word-action roster does not contain 4,096 rows")
    roster_stream.shuffle(word_action)
    cells = [item[0] for item in word_action]
    action_indices = [item[1] for item in word_action]
    counts["train/S1/word_action"] = roster_stream.draw_count
    hashes["train/S1/word_action"] = _hash_json(word_action)
    return _rows_from_rosters(states, cells, action_indices), counts, hashes


def materialize_seed(master: bytes, seed_index: int) -> SeedCorpus:
    s0, counts, hashes = _balanced_rows(
        master, seed_index, "train/S0", TRAIN_ROWS, K_FIT, True,
    )
    s1, s1_counts, s1_hashes = _s1_rows(master, seed_index)
    counts.update(s1_counts)
    hashes.update(s1_hashes)
    fit_support, eval_counts, eval_hashes = _balanced_rows(
        master, seed_index, "eval/fit_support", FIT_SUPPORT_ROWS, K_FIT, True,
    )
    counts.update(eval_counts)
    hashes.update(eval_hashes)
    targets: dict[int, tuple[Row, ...]] = {}
    for k in K_TARGET:
        target_rows, target_counts, target_hashes = _target_rows(master, seed_index, k)
        targets[k] = target_rows
        counts.update(target_counts)
        hashes.update(target_hashes)
    return SeedCorpus(
        seed_index=seed_index,
        train={"S0": s0, "S1": s1},
        fit_support=fit_support,
        targets=targets,
        draw_counts=counts,
        block_hashes=hashes,
    )


def segment_examples(
    rows: tuple[Row, ...] | list[Row], *, row_equal: bool = True,
) -> SegmentExamples:
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
        atoms = tuple(
            (start, length)
            for start in range(row.k)
            for length in range(1, row.k - start + 1)
        )
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
        np.asarray(states, dtype=np.float64),
        np.asarray(actions, dtype=np.int8),
        padded,
        np.asarray(lengths, dtype=np.int64),
        np.asarray(terminals, dtype=np.float64),
        np.asarray(rewards, dtype=np.float64),
        np.asarray(weights, dtype=np.float64),
    )


def complete_word_examples(rows: tuple[Row, ...]) -> SegmentExamples:
    states: list[np.ndarray] = []
    actions: list[tuple[int, int, int, int]] = []
    token_words: list[np.ndarray] = []
    lengths: list[int] = []
    terminals: list[np.ndarray] = []
    rewards: list[float] = []
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
        np.asarray(states, dtype=np.float64),
        np.asarray(actions, dtype=np.int8),
        padded,
        np.asarray(lengths, dtype=np.int64),
        np.asarray(terminals, dtype=np.float64),
        np.asarray(rewards, dtype=np.float64),
        weights,
    )


def output_scales(rows: tuple[Row, ...]) -> tuple[np.ndarray, np.float32]:
    examples = segment_examples(rows)
    mean_f = np.zeros(9, dtype=np.float64)
    mean_g = np.float64(0.0)
    for index in range(len(examples.weights)):
        weight = np.float64(examples.weights[index])
        for coordinate in range(9):
            mean_f[coordinate] = np.float64(
                mean_f[coordinate]
                + weight * np.float64(examples.terminal[index, coordinate])
            )
        mean_g = np.float64(mean_g + weight * np.float64(examples.reward[index]))
    var_f = np.zeros(9, dtype=np.float64)
    var_g = np.float64(0.0)
    for index in range(len(examples.weights)):
        weight = np.float64(examples.weights[index])
        for coordinate in range(9):
            residual = np.float64(examples.terminal[index, coordinate]) - mean_f[coordinate]
            var_f[coordinate] = np.float64(
                var_f[coordinate] + weight * residual * residual
            )
        residual_g = np.float64(examples.reward[index]) - mean_g
        var_g = np.float64(var_g + weight * residual_g * residual_g)
    scale_f = np.maximum(np.sqrt(var_f, dtype=np.float64), 1.0e-6).astype(np.float32)
    scale_g = np.float32(max(float(np.sqrt(var_g)), 1.0e-6))
    return scale_f, scale_g


def complete_word_truth_mean(rows: tuple[Row, ...]) -> tuple[np.ndarray, float]:
    examples = complete_word_examples(rows)
    return (
        np.mean(examples.terminal, axis=0, dtype=np.float64),
        float(np.mean(examples.reward, dtype=np.float64)),
    )


def seed_manifest(
    master: bytes,
    corpus: SeedCorpus,
    initialization: dict[str, object],
    minibatch_draws: dict[str, int],
) -> dict[str, object]:
    panel_digest, seed_digests = identity_digests(master)
    counts = dict(corpus.draw_counts)
    counts.update(initialization["draw_counts"])
    counts.update(minibatch_draws)
    return {
        "panel_digest": panel_digest,
        "seed_index": corpus.seed_index,
        "seed_digest": seed_digests[corpus.seed_index],
        "domain_draw_counts": counts,
        "block_hashes": dict(corpus.block_hashes),
        "evaluation_identity": corpus.evaluation_identity,
        "initialization_digests": initialization["digests"],
        "support_clone_identity": initialization["support_clone_identity"],
    }
