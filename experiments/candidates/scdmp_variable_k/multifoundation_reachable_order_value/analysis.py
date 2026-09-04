"""Raw held-out panel validation and ordered exploratory B branch selection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .selection import DevelopmentMapping, FAILURE_LABELS, GRAPHS, STATE_ROWS, TRAINING_SEEDS


ARMS = ("MATCHED", "SWAPPED", "COMMON")


@dataclass(frozen=True, slots=True)
class HeldoutCell:
    seed: int
    state_id: str
    k: int
    stratum: str
    tape: int
    graph: str
    arm: str
    action: int
    utility: float
    terminal: bool
    safe_dock: bool
    dock_tick: int | None
    timeout: bool
    failures: tuple[str, ...]
    external_reward: float
    energy: float
    allocated_slots: int
    transitions: int
    policy_queries: int


@dataclass(frozen=True, slots=True)
class TapeUnit:
    seed: int
    state_id: str
    k: int
    stratum: str
    tape: int
    matched: float
    swapped: float
    common: float
    delta_swap: float
    delta_common: float
    graphwise: tuple[tuple[str, float, float], ...]


@dataclass(frozen=True, slots=True)
class HeldoutAnalysis:
    branch: str
    raw_cells: tuple[HeldoutCell, ...]
    tape_units: tuple[TapeUnit, ...]
    foundation_means: tuple[tuple[int, float, float], ...]
    k_means: tuple[tuple[int, int, float, float], ...]
    state_means: tuple[tuple[int, str, float, float], ...]
    tape_covariance: float
    within_state_tape_variance: tuple[tuple[str, float], ...]
    between_state_variance: tuple[tuple[str, float], ...]
    between_foundation_dispersion: tuple[tuple[str, float], ...]
    counts: dict[str, int]


def _expected_action(mapping: DevelopmentMapping, cell: HeldoutCell) -> int:
    hr = mapping.action_for(cell.seed, cell.state_id, "HR")
    rh = mapping.action_for(cell.seed, cell.state_id, "RH")
    if cell.arm == "MATCHED":
        return hr if cell.graph == "HR" else rh
    if cell.arm == "SWAPPED":
        return rh if cell.graph == "HR" else hr
    if cell.arm == "COMMON":
        return mapping.common_for(cell.seed, cell.state_id)
    raise ValueError("held-out arm differs")


def _mean(values: Iterable[float]) -> float:
    rows = tuple(values)
    return math.fsum(rows) / len(rows)


def _sample_variance(values: Iterable[float]) -> float:
    rows = tuple(values)
    if len(rows) < 2:
        return 0.0
    center = _mean(rows)
    return math.fsum((value - center) ** 2 for value in rows) / (len(rows) - 1)


def _branch(
    foundation: dict[int, tuple[float, float]],
    by_k: dict[tuple[int, int], tuple[float, float]],
    by_state: dict[tuple[int, str], tuple[float, float]],
    mapping: DevelopmentMapping,
) -> str:
    def positive(seed: int) -> bool:
        overall = foundation[seed]
        k_ok = all(by_k[seed, k][0] > 0.0 and by_k[seed, k][1] > 0.0 for k in (7, 13))
        states = tuple(by_state[seed, state_id] for state_id, _k, _s in STATE_ROWS)
        return overall[0] > 0.0 and overall[1] > 0.0 and k_ok and (
            sum(item[0] > 0.0 for item in states) >= 4
            and sum(item[1] > 0.0 for item in states) >= 4
        )
    if all(positive(seed) for seed in TRAINING_SEEDS):
        return "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"
    swapped_favorable = all(foundation[seed][0] > 0.0 for seed in TRAINING_SEEDS)
    common_bad = all(foundation[seed][1] <= 0.0 for seed in TRAINING_SEEDS) or any(
        all(by_k[seed, k][1] <= 0.0 for seed in TRAINING_SEEDS) for k in (7, 13)
    )
    if swapped_favorable and common_bad:
        return "GENERIC_ACTION_OR_RECOVERY_EXPLANATION"
    distinct_each_k = all(any(
        row.k == k and row.hr_action != row.rh_action for row in mapping.units
    ) for k in (7, 13))
    if distinct_each_k and all(
        by_k[seed, k][0] <= 0.0 for seed in TRAINING_SEEDS for k in (7, 13)
    ):
        return "ORDER_ASSOCIATION_NOT_OBSERVED_IN_RUN_01"
    return "FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY"


def analyze_heldout_panel(
    mapping: DevelopmentMapping, cells: Iterable[HeldoutCell]
) -> HeldoutAnalysis:
    """Validate all 1152 raw cells, preserve them, and apply branches 5--8."""

    if not isinstance(mapping, DevelopmentMapping):
        raise TypeError("a frozen development mapping is required")
    rows = tuple(cells)
    expected_states = {state_id: (k, stratum) for state_id, k, stratum in STATE_ROWS}
    addresses = []
    for row in rows:
        if not isinstance(row, HeldoutCell):
            raise ValueError("held-out panel contains an untyped cell")
        if (
            row.seed not in TRAINING_SEEDS
            or expected_states.get(row.state_id) != (row.k, row.stratum)
            or row.tape not in range(16)
            or row.graph not in GRAPHS
            or row.arm not in ARMS
        ):
            raise ValueError("held-out address differs")
        if row.action != _expected_action(mapping, row):
            raise ValueError("held-out action differs from frozen development mapping")
        if (
            not math.isfinite(row.utility) or not 0.0 <= row.utility <= 1.0
            or not math.isfinite(row.external_reward) or not math.isfinite(row.energy)
            or row.terminal is not True or not isinstance(row.safe_dock, bool)
            or not isinstance(row.timeout, bool)
            or not isinstance(row.failures, tuple)
            or row.failures != tuple(label for label in FAILURE_LABELS if label in row.failures)
            or len(set(row.failures)) != len(row.failures)
            or row.allocated_slots != 364
            or row.transitions < 0 or row.transitions > row.allocated_slots
            or row.policy_queries < 0
        ):
            raise ValueError("held-out endpoint or work parity fields differ")
        if row.safe_dock:
            if (
                isinstance(row.dock_tick, bool) or not isinstance(row.dock_tick, int)
                or not 1 <= row.dock_tick <= 364 or row.timeout or row.failures
            ):
                raise ValueError("held-out safe-dock endpoint differs")
            expected_utility = 1.0 - row.dock_tick / 364.0
        else:
            if row.dock_tick is not None or not (row.timeout or row.failures):
                raise ValueError("held-out terminal cause differs")
            expected_utility = 0.0
        if row.utility != expected_utility:
            raise ValueError("held-out utility differs from the native endpoint")
        addresses.append((row.seed, row.state_id, row.tape, row.graph, row.arm))
    expected = {
        (seed, state_id, tape, graph, arm)
        for seed in TRAINING_SEEDS
        for state_id, _k, _stratum in STATE_ROWS
        for tape in range(16)
        for graph in GRAPHS
        for arm in ARMS
    }
    if len(rows) != 1_152 or len(set(addresses)) != len(addresses) or set(addresses) != expected:
        raise ValueError("held-out panel is not complete")
    indexed = {
        (row.seed, row.state_id, row.tape, row.graph, row.arm): row for row in rows
    }
    # Allocated work is the causal parity field. Actual transitions and queries
    # may differ only because an evaluated trajectory absorbs earlier.
    for seed in TRAINING_SEEDS:
        for state_id, _k, _stratum in STATE_ROWS:
            for tape in range(16):
                if {indexed[seed, state_id, tape, graph, arm].allocated_slots
                    for graph in GRAPHS for arm in ARMS} != {364}:
                    raise ValueError("held-out work parity differs")
    units = []
    for seed in TRAINING_SEEDS:
        for state_id, k, stratum in STATE_ROWS:
            for tape in range(16):
                values = {
                    arm: 0.5 * math.fsum(
                        indexed[seed, state_id, tape, graph, arm].utility for graph in GRAPHS
                    )
                    for arm in ARMS
                }
                graphwise = tuple(
                    (
                        graph,
                        indexed[seed, state_id, tape, graph, "MATCHED"].utility
                        - indexed[seed, state_id, tape, graph, "SWAPPED"].utility,
                        indexed[seed, state_id, tape, graph, "MATCHED"].utility
                        - indexed[seed, state_id, tape, graph, "COMMON"].utility,
                    )
                    for graph in GRAPHS
                )
                units.append(TapeUnit(
                    seed, state_id, k, stratum, tape,
                    values["MATCHED"], values["SWAPPED"], values["COMMON"],
                    values["MATCHED"] - values["SWAPPED"],
                    values["MATCHED"] - values["COMMON"], graphwise,
                ))
    by_foundation = {
        seed: (
            _mean(row.delta_swap for row in units if row.seed == seed),
            _mean(row.delta_common for row in units if row.seed == seed),
        )
        for seed in TRAINING_SEEDS
    }
    by_k = {
        (seed, k): (
            _mean(row.delta_swap for row in units if row.seed == seed and row.k == k),
            _mean(row.delta_common for row in units if row.seed == seed and row.k == k),
        )
        for seed in TRAINING_SEEDS for k in (7, 13)
    }
    by_state = {
        (seed, state_id): (
            _mean(row.delta_swap for row in units if row.seed == seed and row.state_id == state_id),
            _mean(row.delta_common for row in units if row.seed == seed and row.state_id == state_id),
        )
        for seed in TRAINING_SEEDS for state_id, _k, _stratum in STATE_ROWS
    }
    swap_values = tuple(row.delta_swap for row in units)
    common_values = tuple(row.delta_common for row in units)
    swap_mean = _mean(swap_values)
    common_mean = _mean(common_values)
    covariance = math.fsum(
        (left - swap_mean) * (right - common_mean)
        for left, right in zip(swap_values, common_values)
    ) / (len(units) - 1)
    within = tuple(
        (name, _mean(
            _sample_variance(
                getattr(row, field)
                for row in units if row.seed == seed and row.state_id == state_id
            )
            for seed in TRAINING_SEEDS for state_id, _k, _stratum in STATE_ROWS
        ))
        for name, field in (("swap", "delta_swap"), ("common", "delta_common"))
    )
    state_swap_means = tuple(value[0] for value in by_state.values())
    state_common_means = tuple(value[1] for value in by_state.values())
    foundation_swap_means = tuple(value[0] for value in by_foundation.values())
    foundation_common_means = tuple(value[1] for value in by_foundation.values())
    return HeldoutAnalysis(
        _branch(by_foundation, by_k, by_state, mapping), rows, tuple(units),
        tuple((seed, *by_foundation[seed]) for seed in TRAINING_SEEDS),
        tuple((seed, k, *by_k[seed, k]) for seed in TRAINING_SEEDS for k in (7, 13)),
        tuple((seed, state_id, *by_state[seed, state_id]) for seed in TRAINING_SEEDS
              for state_id, _k, _stratum in STATE_ROWS),
        covariance, within,
        (("swap", _sample_variance(state_swap_means)),
         ("common", _sample_variance(state_common_means))),
        (("swap", _sample_variance(foundation_swap_means)),
         ("common", _sample_variance(foundation_common_means))),
        {
            "raw_cells": len(rows),
            "tape_units": len(units),
            "allocated_slots": sum(row.allocated_slots for row in rows),
            "transitions": sum(row.transitions for row in rows),
            "policy_queries": sum(row.policy_queries for row in rows),
        },
    )


__all__ = ["HeldoutAnalysis", "HeldoutCell", "TapeUnit", "analyze_heldout_panel"]
