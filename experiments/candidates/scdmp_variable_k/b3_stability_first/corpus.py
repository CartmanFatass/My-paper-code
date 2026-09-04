from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..corpus import BankRow, _composition_row, _endpoint_row
from ..dgp import class_for_episode, joint_action_from_index, reset_from_raw, rollout_interval, scheduled_word
from ..rng import fisher_yates
from .config import (
    BANK_ORDER, BATCH_NAMESPACE_BASE, BATCH_ROWS_PER_STRATUM, CORPUS_NAMESPACE_BASE,
    FIT_EPISODES_PER_DURATION, SCALE_FLOOR, SCALER_ATOMS_PER_OUTPUT, STRATUM_ORDER,
    TRAIN_DURATIONS, TRAIN_EPISODES_PER_DURATION, TRAIN_HORIZON,
)


@dataclass(frozen=True)
class Scales:
    e: np.float32
    v: np.float32
    node_reward: np.float32
    edge_reward: np.float32

    def as_dict(self) -> dict[str, object]:
        return {"e": float(self.e), "v": float(self.v), "node_reward": float(self.node_reward),
                "edge_reward": float(self.edge_reward), "atoms_per_output": SCALER_ATOMS_PER_OUTPUT,
                "ddof": 0, "stored_dtype": "numpy.float32", "float64_floor": SCALE_FLOOR}


@dataclass
class Corpus:
    endpoint_banks: dict[int, list[BankRow]]
    composition_banks: dict[str, list[BankRow]]
    probe_rows: dict[int, list[BankRow]]
    homogeneous_probe: dict[int, list[BankRow]]
    scales: Scales
    means: dict[str, np.float64]
    microsteps: int

    @property
    def banks(self) -> dict[str, list[BankRow]]:
        return {"E_2": self.endpoint_banks[2], "E_4": self.endpoint_banks[4],
                "E_8": self.endpoint_banks[8], "C_22": self.composition_banks["C_22"],
                "C_44": self.composition_banks["C_44"]}


@dataclass(frozen=True)
class LockedBatch:
    rows: dict[str, tuple[BankRow, ...]]
    update_index: int


def _populations(rows: list[BankRow]) -> tuple[np.ndarray, ...]:
    arrays = (
        np.asarray([x for row in rows for x in row.terminal.e], dtype=np.float64, order="C"),
        np.asarray([x for row in rows for x in row.terminal.v], dtype=np.float64, order="C"),
        np.asarray([x for row in rows for x in row.node_rewards], dtype=np.float64, order="C"),
        np.asarray([x for row in rows for x in row.edge_rewards], dtype=np.float64, order="C"),
    )
    if any(x.shape != (SCALER_ATOMS_PER_OUTPUT,) or not x.flags.c_contiguous for x in arrays):
        raise RuntimeError("B3 scaler population is not the exact 10,752-atom C-order population")
    return arrays


def _scales_and_means(rows: list[BankRow]) -> tuple[Scales, dict[str, np.float64]]:
    arrays = _populations(rows)
    def scale(x: np.ndarray) -> np.float32:
        return np.float32(np.maximum(np.std(x, axis=None, dtype=np.float64, ddof=0),
                                     np.float64(SCALE_FLOOR)))
    scales = Scales(*(scale(x) for x in arrays))
    names = ("e", "v", "node_reward", "edge_reward")
    return scales, {name: np.mean(x, axis=None, dtype=np.float64)
                    for name, x in zip(names, arrays)}


def build_corpus(algorithm_seed: int) -> Corpus:
    bit_generator = np.random.PCG64(CORPUS_NAMESPACE_BASE + algorithm_seed)
    endpoint = {d: [] for d in TRAIN_DURATIONS}
    probe = {d: [] for d in TRAIN_DURATIONS}
    microsteps = 0
    for duration in TRAIN_DURATIONS:
        global_boundary = 0
        for episode_index in range(TRAIN_EPISODES_PER_DURATION):
            state = reset_from_raw(bit_generator)
            dynamics_class = class_for_episode(episode_index)
            for boundary_index in range(TRAIN_HORIZON // duration):
                context_word = scheduled_word(duration, dynamics_class, episode_index, boundary_index)
                action = joint_action_from_index((global_boundary + 17 * algorithm_seed) % 81)
                outcome = rollout_interval(state, action, context_word, capture_trace=True)
                row = _endpoint_row(duration=duration, episode_index=episode_index,
                    boundary_index=boundary_index, dynamics_class=dynamics_class,
                    initial=state, outcome=outcome)
                (endpoint[duration] if episode_index < FIT_EPISODES_PER_DURATION else probe[duration]).append(row)
                state = outcome.terminal
                global_boundary += 1
                microsteps += duration
    composition = {"C_22": [_composition_row(r, 2) for r in endpoint[4]],
                   "C_44": [_composition_row(r, 4) for r in endpoint[8]]}
    fit_rows = [r for d in TRAIN_DURATIONS for r in endpoint[d]]
    scales, means = _scales_and_means(fit_rows)
    homogeneous = {d: [r for r in probe[d] if len(set(r.word)) == 1] for d in (4, 8)}
    return Corpus(endpoint, composition, probe, homogeneous, scales, means, microsteps)


class LockedBatchPlan:
    """Pure random-access locked batches; obtaining update zero never advances a cursor."""

    def __init__(self, corpus: Corpus, algorithm_seed: int) -> None:
        bg = np.random.PCG64(BATCH_NAMESPACE_BASE + algorithm_seed)
        self.rows: dict[tuple[str, str, int], tuple[BankRow, ...]] = {}
        self.perms: dict[tuple[str, str, int], tuple[int, ...]] = {}
        for bank in BANK_ORDER:
            for dynamics_class, word_row in STRATUM_ORDER:
                key = bank, dynamics_class, word_row
                rows = tuple(sorted((r for r in corpus.banks[bank]
                    if r.dynamics_class == dynamics_class and r.word_row == word_row), key=lambda r: r.key))
                if len(rows) < BATCH_ROWS_PER_STRATUM:
                    raise RuntimeError(f"insufficient B3 stratum {key}")
                self.rows[key] = rows
                self.perms[key] = tuple(fisher_yates(bg, range(len(rows))))

    def batch_for_update(self, update_index: int) -> LockedBatch:
        if not 0 <= update_index < 1_000:
            raise ValueError("B3 update index must be in [0,999]")
        selected: dict[str, tuple[BankRow, ...]] = {}
        for bank in BANK_ORDER:
            out: list[BankRow] = []
            for dynamics_class, word_row in STRATUM_ORDER:
                key = bank, dynamics_class, word_row
                rows, permutation = self.rows[key], self.perms[key]
                start = (update_index * BATCH_ROWS_PER_STRATUM) % len(permutation)
                out.extend(rows[permutation[(start + slot) % len(permutation)]]
                           for slot in range(BATCH_ROWS_PER_STRATUM))
            selected[bank] = tuple(out)
        return LockedBatch(selected, update_index)


def support_certificate(corpus: Corpus, batch: LockedBatch) -> dict[str, object]:
    endpoint = tuple(r for b in ("E_2", "E_4", "E_8") for r in batch.rows[b])
    composition = tuple(r for b in ("C_22", "C_44") for r in batch.rows[b])
    all_rows = endpoint + composition
    conditions = {
        "three_endpoint_durations": sorted({r.duration for r in endpoint}) == [2, 4, 8],
        "two_composition_pairs": sorted({f"{r.split}+{r.duration-r.split}" for r in composition}) == ["2+2", "4+4"],
        "both_classes": sorted({r.dynamics_class for r in all_rows}) == ["REAL", "SHAM"],
        "all_word_rows": sorted({r.word_row for r in all_rows}) == [0, 1, 2, 3],
        "two_joint_actions": len({r.action for r in all_rows}) >= 2,
        "all_scalar_actions": sorted({a for r in all_rows for a in r.action}) == [-1, 0, 1],
        "denominators": len(endpoint) == 192 and len(composition) == 128,
    }
    return {"conditions": conditions, "conforming": all(conditions.values()),
            "endpoint_complete_rows": len(endpoint), "composition_complete_rows": len(composition)}


def structural_certificate(corpus: Corpus) -> dict[str, object]:
    fit_hom = [r for b in ("C_22", "C_44") for r in corpus.banks[b] if len(set(r.word)) == 1]
    identity = all(r.word[:int(r.split or 0)] == r.word[int(r.split or 0):] for r in fit_hom)
    probe_counts = {str(d): len(corpus.homogeneous_probe[d]) for d in (4, 8)}
    actions: dict[str, dict[str, int | bool]] = {}
    for duration in TRAIN_DURATIONS:
        counts = {i: 0 for i in range(81)}
        for row in corpus.endpoint_banks[duration]:
            index = sum((a + 1) * place for a, place in zip(row.action, (27, 9, 3, 1)))
            counts[index] += 1
        actions[str(duration)] = {"minimum": min(counts.values()),
                                  "all_at_least_four": min(counts.values()) >= 4}
    checks = {"homogeneous_fit_identity": identity,
              "homogeneous_probe_counts": probe_counts == {"4": 128, "8": 64},
              "action_support": all(bool(x["all_at_least_four"]) for x in actions.values()),
              "corpus_microsteps": corpus.microsteps == 12_288}
    return {"checks": checks, "conforming": all(checks.values()),
            "fit_homogeneous_rows": len(fit_hom), "homogeneous_probe_rows": probe_counts,
            "action_support": actions}
