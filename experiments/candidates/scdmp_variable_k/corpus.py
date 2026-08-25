from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import (
    BANK_ORDER, BATCH_ROWS_PER_STRATUM, FIT_EPISODES_PER_DURATION, N_AGENTS,
    SCALE_FLOOR, SCALER_ATOMS_PER_OUTPUT, SCALER_DDOF, STRATUM_ORDER,
    TRAIN_DURATIONS, TRAIN_EPISODES_PER_DURATION,
    TRAIN_HORIZON,
)
from .dgp import (
    IntervalOutcome, PhysicalState, class_for_episode, joint_action_from_index,
    reset_from_raw, rollout_interval, scheduled_word,
)
from .rng import fisher_yates


@dataclass(frozen=True)
class BankRow:
    duration: int
    dynamics_class: str
    word_row: int
    episode_index: int
    boundary_index: int
    initial: PhysicalState
    action: tuple[int, int, int, int]
    word: tuple[str, ...]
    terminal: PhysicalState
    node_rewards: np.ndarray
    edge_rewards: np.ndarray
    split: int | None = None
    intermediate: PhysicalState | None = None
    prefix_node_rewards: np.ndarray | None = None
    prefix_edge_rewards: np.ndarray | None = None
    suffix_node_rewards: np.ndarray | None = None
    suffix_edge_rewards: np.ndarray | None = None

    @property
    def key(self) -> tuple[int, int]:
        return self.episode_index, self.boundary_index


@dataclass(frozen=True)
class Scales:
    e: np.float32
    v: np.float32
    node_reward: np.float32
    edge_reward: np.float32
    atoms_per_output: int = SCALER_ATOMS_PER_OUTPUT
    ddof: int = SCALER_DDOF

    def as_dict(self) -> dict[str, object]:
        return {
            "e": float(self.e), "v": float(self.v),
            "node_reward": float(self.node_reward), "edge_reward": float(self.edge_reward),
            "atoms_per_output": self.atoms_per_output, "ddof": self.ddof,
            "stored_dtype": "numpy.float32",
            "float64_floor": SCALE_FLOOR,
            "mean_subtracted": False,
        }


@dataclass
class Corpus:
    endpoint_banks: dict[int, list[BankRow]]
    composition_banks: dict[str, list[BankRow]]
    probe_rows: dict[int, list[BankRow]]
    scales: Scales
    microsteps: int

    @property
    def banks(self) -> dict[str, list[BankRow]]:
        return {
            "E_2": self.endpoint_banks[2],
            "E_4": self.endpoint_banks[4],
            "E_8": self.endpoint_banks[8],
            "C_22": self.composition_banks["C_22"],
            "C_44": self.composition_banks["C_44"],
        }


@dataclass(frozen=True)
class LockedBatch:
    rows: dict[str, tuple[BankRow, ...]]
    update_index: int


def _endpoint_row(
    *, duration: int, episode_index: int, boundary_index: int,
    dynamics_class: str, initial: PhysicalState, outcome: IntervalOutcome,
) -> BankRow:
    midpoint = duration // 2 if duration in (4, 8) else None
    if midpoint is not None:
        if outcome.state_trace is None or outcome.node_reward_trace is None or outcome.edge_reward_trace is None:
            raise RuntimeError("composition endpoint is missing its charged rollout trace")
        intermediate = outcome.state_trace[midpoint - 1].clone()
        node_trace = np.stack(outcome.node_reward_trace)
        edge_trace = np.stack(outcome.edge_reward_trace)
        def ordered_sum(values: np.ndarray) -> np.ndarray:
            total = np.zeros(N_AGENTS, dtype=np.float64)
            for value in values:
                total += value
            return total
        prefix_node = ordered_sum(node_trace[:midpoint])
        suffix_node = ordered_sum(node_trace[midpoint:])
        prefix_edge = ordered_sum(edge_trace[:midpoint])
        suffix_edge = ordered_sum(edge_trace[midpoint:])
    else:
        intermediate = prefix_node = suffix_node = prefix_edge = suffix_edge = None
    return BankRow(
        duration=duration, dynamics_class=dynamics_class,
        word_row=(episode_index % 4 + boundary_index) % 4,
        episode_index=episode_index, boundary_index=boundary_index,
        initial=initial.clone(), action=outcome.action, word=outcome.word,
        terminal=outcome.terminal.clone(), node_rewards=outcome.node_rewards.copy(),
        edge_rewards=outcome.edge_rewards.copy(),
        intermediate=intermediate,
        prefix_node_rewards=prefix_node,
        suffix_node_rewards=suffix_node,
        prefix_edge_rewards=prefix_edge,
        suffix_edge_rewards=suffix_edge,
    )


def _composition_row(endpoint: BankRow, split: int) -> BankRow:
    if split != endpoint.duration // 2:
        raise RuntimeError("composition split does not match captured endpoint midpoint")
    if any(value is None for value in (
        endpoint.intermediate, endpoint.prefix_node_rewards, endpoint.prefix_edge_rewards,
        endpoint.suffix_node_rewards, endpoint.suffix_edge_rewards,
    )):
        raise RuntimeError("composition row cannot be built without captured endpoint trace")
    return BankRow(
        **{name: getattr(endpoint, name) for name in (
            "duration", "dynamics_class", "word_row", "episode_index",
            "boundary_index", "initial", "action", "word", "terminal",
            "node_rewards", "edge_rewards",
        )},
        split=split, intermediate=endpoint.intermediate.clone(),
        prefix_node_rewards=endpoint.prefix_node_rewards.copy(),
        prefix_edge_rewards=endpoint.prefix_edge_rewards.copy(),
        suffix_node_rewards=endpoint.suffix_node_rewards.copy(),
        suffix_edge_rewards=endpoint.suffix_edge_rewards.copy(),
    )


def _fit_scales(rows: list[BankRow]) -> Scales:
    # ``rows`` is supplied in the frozen duration/episode/boundary traversal;
    # each row array is already in slot order.  Concatenation therefore makes
    # the registered one-dimensional target populations without duplicating
    # composition-bank views.
    populations = (
        np.asarray([value for row in rows for value in row.terminal.e], dtype=np.float64, order="C"),
        np.asarray([value for row in rows for value in row.terminal.v], dtype=np.float64, order="C"),
        np.asarray([value for row in rows for value in row.node_rewards], dtype=np.float64, order="C"),
        np.asarray([value for row in rows for value in row.edge_rewards], dtype=np.float64, order="C"),
    )
    if any(array.shape != (SCALER_ATOMS_PER_OUTPUT,) or not array.flags.c_contiguous
           for array in populations):
        raise RuntimeError("fit scaler population is not the exact 10,752-atom C-order population")

    def scale32(x64: np.ndarray) -> np.float32:
        sigma64 = np.std(x64, axis=None, dtype=np.float64, ddof=0)
        scale64 = np.maximum(sigma64, np.float64(SCALE_FLOOR))
        return np.float32(scale64)

    return Scales(
        e=scale32(populations[0]), v=scale32(populations[1]),
        node_reward=scale32(populations[2]), edge_reward=scale32(populations[3]),
    )


def build_corpus(algorithm_seed: int) -> Corpus:
    bit_generator = np.random.PCG64(730_000 + algorithm_seed)
    endpoint_banks = {duration: [] for duration in TRAIN_DURATIONS}
    probe_rows = {duration: [] for duration in TRAIN_DURATIONS}
    microsteps = 0
    for duration in TRAIN_DURATIONS:
        global_boundary_index = 0
        for episode_index in range(TRAIN_EPISODES_PER_DURATION):
            state = reset_from_raw(bit_generator)
            dynamics_class = class_for_episode(episode_index)
            for boundary_index in range(TRAIN_HORIZON // duration):
                context_word = scheduled_word(
                    duration, dynamics_class, episode_index, boundary_index,
                )
                action_index = (global_boundary_index + 17 * algorithm_seed) % 81
                action = joint_action_from_index(action_index)
                outcome = rollout_interval(state, action, context_word, capture_trace=True)
                row = _endpoint_row(
                    duration=duration, episode_index=episode_index,
                    boundary_index=boundary_index, dynamics_class=dynamics_class,
                    initial=state, outcome=outcome,
                )
                destination = (
                    endpoint_banks[duration]
                    if episode_index < FIT_EPISODES_PER_DURATION
                    else probe_rows[duration]
                )
                destination.append(row)
                state = outcome.terminal
                global_boundary_index += 1
                microsteps += duration
    composition_banks = {
        "C_22": [_composition_row(row, 2) for row in endpoint_banks[4]],
        "C_44": [_composition_row(row, 4) for row in endpoint_banks[8]],
    }
    fit_rows = [row for duration in TRAIN_DURATIONS for row in endpoint_banks[duration]]
    return Corpus(
        endpoint_banks=endpoint_banks, composition_banks=composition_banks,
        probe_rows=probe_rows, scales=_fit_scales(fit_rows), microsteps=microsteps,
    )


class LockedBatchStream:
    def __init__(self, corpus: Corpus, algorithm_seed: int) -> None:
        bit_generator = np.random.PCG64(720_000 + algorithm_seed)
        self._rows: dict[tuple[str, str, int], tuple[BankRow, ...]] = {}
        self._permutations: dict[tuple[str, str, int], list[int]] = {}
        self._cursors: dict[tuple[str, str, int], int] = {}
        for bank_name in BANK_ORDER:
            bank = corpus.banks[bank_name]
            for dynamics_class, word_row in STRATUM_ORDER:
                key = bank_name, dynamics_class, word_row
                rows = tuple(sorted(
                    (row for row in bank
                     if row.dynamics_class == dynamics_class and row.word_row == word_row),
                    key=lambda row: row.key,
                ))
                if len(rows) < BATCH_ROWS_PER_STRATUM:
                    raise RuntimeError(f"bank stratum {key} has only {len(rows)} rows")
                self._rows[key] = rows
                self._permutations[key] = fisher_yates(bit_generator, range(len(rows)))
                self._cursors[key] = 0
        self._update_index = 0

    def next_batch(self) -> LockedBatch:
        selected: dict[str, tuple[BankRow, ...]] = {}
        for bank_name in BANK_ORDER:
            bank_rows: list[BankRow] = []
            for dynamics_class, word_row in STRATUM_ORDER:
                key = bank_name, dynamics_class, word_row
                rows = self._rows[key]
                permutation = self._permutations[key]
                cursor = self._cursors[key]
                for _ in range(BATCH_ROWS_PER_STRATUM):
                    bank_rows.append(rows[permutation[cursor]])
                    cursor = (cursor + 1) % len(permutation)
                self._cursors[key] = cursor
            selected[bank_name] = tuple(bank_rows)
        batch = LockedBatch(rows=selected, update_index=self._update_index)
        self._update_index += 1
        return batch


def support_certificate(corpus: Corpus, batch: LockedBatch) -> dict[str, object]:
    endpoint_rows = tuple(row for bank in ("E_2", "E_4", "E_8") for row in batch.rows[bank])
    composition_rows = tuple(row for bank in ("C_22", "C_44") for row in batch.rows[bank])
    joint_actions = {row.action for row in (*endpoint_rows, *composition_rows)}
    scalar_actions = {action for row in (*endpoint_rows, *composition_rows) for action in row.action}
    facts = {
        "endpoint_complete_rows": len(endpoint_rows),
        "composition_complete_rows": len(composition_rows),
        "endpoint_durations": sorted({row.duration for row in endpoint_rows}),
        "composition_pair_types": sorted({f"{row.split}+{row.duration-row.split}" for row in composition_rows}),
        "dynamics_classes": sorted({row.dynamics_class for row in (*endpoint_rows, *composition_rows)}),
        "word_rows": sorted({row.word_row for row in (*endpoint_rows, *composition_rows)}),
        "distinct_joint_actions": len(joint_actions),
        "scalar_actions": sorted(scalar_actions),
        "corpus_microsteps": corpus.microsteps,
    }
    conditions = {
        "three_endpoint_durations": facts["endpoint_durations"] == [2, 4, 8],
        "two_composition_pairs": facts["composition_pair_types"] == ["2+2", "4+4"],
        "both_classes": facts["dynamics_classes"] == ["REAL", "SHAM"],
        "all_word_rows": facts["word_rows"] == [0, 1, 2, 3],
        "at_least_two_joint_actions": int(facts["distinct_joint_actions"]) >= 2,
        "every_scalar_skill": facts["scalar_actions"] == [-1, 0, 1],
        "exact_batch_denominators": len(endpoint_rows) == 192 and len(composition_rows) == 128,
    }
    return {"facts": facts, "conditions": conditions, "conforming": all(conditions.values())}


def action_support_report(corpus: Corpus) -> dict[str, object]:
    by_duration: dict[str, dict[str, int]] = {}
    for duration in TRAIN_DURATIONS:
        counts = {index: 0 for index in range(81)}
        for row in corpus.endpoint_banks[duration]:
            action_index = sum((value + 1) * place for value, place in zip(row.action, (27, 9, 3, 1)))
            counts[action_index] += 1
        by_duration[str(duration)] = {
            "minimum_joint_action_count": min(counts.values()),
            "maximum_joint_action_count": max(counts.values()),
            "all_at_least_four": int(min(counts.values()) >= 4),
        }
    return by_duration


def corpus_conformance_certificate(corpus: Corpus, algorithm_seed: int) -> dict[str, object]:
    endpoint_counts = {str(duration): len(corpus.endpoint_banks[duration]) for duration in TRAIN_DURATIONS}
    probe_counts = {str(duration): len(corpus.probe_rows[duration]) for duration in TRAIN_DURATIONS}
    all_training_rows = [row for bank in corpus.banks.values() for row in bank]
    scaler_endpoint_rows = [
        row for duration in TRAIN_DURATIONS for row in corpus.endpoint_banks[duration]
    ]
    checks = {
        "endpoint_bank_counts_exact": endpoint_counts == {"2": 1_536, "4": 768, "8": 384},
        "probe_bank_counts_exact": probe_counts == {"2": 512, "4": 256, "8": 128},
        "composition_bank_counts_exact": {
            name: len(rows) for name, rows in corpus.composition_banks.items()
        } == {"C_22": 768, "C_44": 384},
        "fit_endpoint_rows_exact": len(scaler_endpoint_rows) == 2_688,
        "only_training_durations_in_training_banks": sorted(
            {row.duration for row in all_training_rows}
        ) == [2, 4, 8],
        "no_target_duration_in_training_banks": not any(
            row.duration in (6, 12) for row in all_training_rows
        ),
        "scaler_atoms_exact": corpus.scales.atoms_per_output == 10_752,
        "scaler_ddof_zero": corpus.scales.ddof == 0,
        "scaler_values_float32": all(
            isinstance(value, np.float32) for value in (
                corpus.scales.e, corpus.scales.v,
                corpus.scales.node_reward, corpus.scales.edge_reward,
            )
        ),
        "composition_rows_reuse_charged_endpoint_trace": all(
            row.intermediate is not None
            and row.prefix_node_rewards is not None and row.prefix_edge_rewards is not None
            and row.suffix_node_rewards is not None and row.suffix_edge_rewards is not None
            for rows in corpus.composition_banks.values() for row in rows
        ),
    }
    return {
        "checks": checks,
        "conforming": all(checks.values()),
        "corpus_rng": {
            "api": "numpy.random.PCG64(seed).random_raw()",
            "seed": 730_000 + algorithm_seed,
            "reset_order": "duration 2,4,8; episode 0..63; q,e1..e4,v1..v4",
        },
        "scaler_traversal": "duration 2,4,8; episode 0..47; boundary ascending; slot 1..4",
        "scaler_sources": "terminal e/v and complete node/edge targets from E_2,E_4,E_8 only",
        "scaler_exclusions": [
            "input_states", "composition_duplicate_views", "support_probe", "audit",
            "scored_evaluation", "model_predictions", "arm_outputs", "other_seeds",
        ],
        "batch_rng": {
            "api": "numpy.random.PCG64(seed).random_raw() rejection-sampled Fisher-Yates",
            "seed": 720_000 + algorithm_seed,
            "bank_order": list(BANK_ORDER),
            "stratum_order": [list(item) for item in STRATUM_ORDER],
        },
    }
