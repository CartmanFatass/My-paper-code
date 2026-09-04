"""Result-blind development action construction for SCDMP B01."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable

from .contracts import HELDOUT_NAMESPACE_TOKEN, NAMED_RUN_ID, STUDY_ID


TRAINING_SEEDS = (1709, 2903)
STATE_ROWS = (
    ("k7-early", 7, "early"),
    ("k7-middle", 7, "middle"),
    ("k7-late", 7, "late"),
    ("k13-early", 13, "early"),
    ("k13-middle", 13, "middle"),
    ("k13-late", 13, "late"),
)
GRAPHS = ("HR", "RH")
ACTIONS = tuple(range(18))
DEVELOPMENT_TAPES = tuple(range(8))
FAILURE_LABELS = (
    "cable_overload", "gantry_contact", "attitude_loss", "formation_loss",
)


class DevelopmentMappingError(ValueError):
    """The development panel cannot freeze the exact B01 mapping."""


@dataclass(frozen=True, slots=True)
class DevelopmentCell:
    seed: int
    state_id: str
    k: int
    stratum: str
    tape: int
    graph: str
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
class MappingUnit:
    seed: int
    state_id: str
    k: int
    stratum: str
    hr_action: int
    rh_action: int
    common_action: int
    graph_means: tuple[tuple[str, tuple[float, ...]], ...]
    graph_ranks: tuple[tuple[str, tuple[int, ...]], ...]
    top_two_margins: tuple[tuple[str, float], ...]
    half_winner_agreement: tuple[tuple[str, bool], ...]

    def action_for(self, graph: str) -> int:
        if graph == "HR":
            return self.hr_action
        if graph == "RH":
            return self.rh_action
        raise KeyError(graph)


@dataclass(frozen=True, slots=True)
class DevelopmentMapping:
    units: tuple[MappingUnit, ...]
    raw_cells: tuple[DevelopmentCell, ...]
    serialized_bytes: bytes
    heldout_namespace_token: str

    def _unit(self, seed: int, state_id: str) -> MappingUnit:
        rows = tuple(row for row in self.units if (row.seed, row.state_id) == (seed, state_id))
        if len(rows) != 1:
            raise KeyError((seed, state_id))
        return rows[0]

    def action_for(self, seed: int, state_id: str, graph: str) -> int:
        return self._unit(seed, state_id).action_for(graph)

    def common_for(self, seed: int, state_id: str) -> int:
        return self._unit(seed, state_id).common_action

    def fceov_rank_diagnostics(self, seed: int, state_id: str) -> dict[str, dict[int, int]]:
        unit = self._unit(seed, state_id)
        return {
            graph: {action: ranks[action] for action in (0, 10, 12)}
            for graph, ranks in unit.graph_ranks
        }

    @property
    def entirely_nondiscriminating(self) -> bool:
        return all(row.hr_action == row.rh_action for row in self.units)


def _argmax_smallest(values: tuple[float, ...]) -> int:
    maximum = max(values)
    return next(index for index, value in enumerate(values) if value == maximum)


def _ranks(values: tuple[float, ...]) -> tuple[int, ...]:
    ordered = sorted(range(len(values)), key=lambda action: (-values[action], action))
    result = [0] * len(values)
    for rank, action in enumerate(ordered, start=1):
        result[action] = rank
    return tuple(result)


def _validate_cell(cell: DevelopmentCell) -> None:
    expected = {state_id: (k, stratum) for state_id, k, stratum in STATE_ROWS}
    if cell.seed not in TRAINING_SEEDS or expected.get(cell.state_id) != (cell.k, cell.stratum):
        raise DevelopmentMappingError("development cell seed/state contract differs")
    if cell.graph not in GRAPHS or cell.action not in ACTIONS or cell.tape not in DEVELOPMENT_TAPES:
        raise DevelopmentMappingError("development cell address differs")
    if not isinstance(cell.utility, (int, float)) or isinstance(cell.utility, bool) or not math.isfinite(cell.utility):
        raise DevelopmentMappingError("development utility must be finite")
    if not 0.0 <= float(cell.utility) <= 1.0:
        raise DevelopmentMappingError("development utility lies outside [0,1]")
    if (
        cell.terminal is not True
        or not isinstance(cell.safe_dock, bool)
        or not isinstance(cell.timeout, bool)
        or not isinstance(cell.failures, tuple)
        or cell.failures != tuple(label for label in FAILURE_LABELS if label in cell.failures)
        or len(set(cell.failures)) != len(cell.failures)
        or not math.isfinite(cell.external_reward)
        or not math.isfinite(cell.energy)
        or cell.allocated_slots != 364
        or cell.transitions < 0 or cell.transitions > cell.allocated_slots
        or cell.policy_queries < 0
    ):
        raise DevelopmentMappingError("development endpoint or work fields differ")
    if cell.safe_dock:
        if (
            isinstance(cell.dock_tick, bool) or not isinstance(cell.dock_tick, int)
            or not 1 <= cell.dock_tick <= 364 or cell.timeout or cell.failures
        ):
            raise DevelopmentMappingError("development safe-dock endpoint differs")
        expected_utility = 1.0 - cell.dock_tick / 364.0
    else:
        if cell.dock_tick is not None or not (cell.timeout or cell.failures):
            raise DevelopmentMappingError("development terminal cause differs")
        expected_utility = 0.0
    if cell.utility != expected_utility:
        raise DevelopmentMappingError("development utility differs from the native endpoint")


def freeze_development_mapping(cells: Iterable[DevelopmentCell]) -> DevelopmentMapping:
    """Freeze the complete 3456-cell development mapping before held-out RNG exists."""

    rows = tuple(cells)
    for row in rows:
        if not isinstance(row, DevelopmentCell):
            raise DevelopmentMappingError("development panel contains an untyped cell")
        _validate_cell(row)
    addresses = tuple(
        (row.seed, row.state_id, row.tape, row.graph, row.action) for row in rows
    )
    if len(set(addresses)) != len(addresses):
        raise DevelopmentMappingError("development panel contains a duplicate address")
    expected = {
        (seed, state_id, tape, graph, action)
        for seed in TRAINING_SEEDS
        for state_id, _k, _stratum in STATE_ROWS
        for tape in DEVELOPMENT_TAPES
        for graph in GRAPHS
        for action in ACTIONS
    }
    if set(addresses) != expected or len(rows) != 3_456:
        raise DevelopmentMappingError("development panel is not complete")
    indexed = {
        (row.seed, row.state_id, row.tape, row.graph, row.action): float(row.utility)
        for row in rows
    }
    units = []
    for seed in TRAINING_SEEDS:
        for state_id, k, stratum in STATE_ROWS:
            means_by_graph = {}
            ranks_by_graph = {}
            margins = []
            agreements = []
            for graph in GRAPHS:
                values = tuple(
                    math.fsum(indexed[seed, state_id, tape, graph, action] for tape in DEVELOPMENT_TAPES)
                    / len(DEVELOPMENT_TAPES)
                    for action in ACTIONS
                )
                means_by_graph[graph] = values
                ranks_by_graph[graph] = _ranks(values)
                ordered = sorted(values, reverse=True)
                margins.append((graph, ordered[0] - ordered[1]))
                halves = tuple(
                    _argmax_smallest(tuple(
                        math.fsum(indexed[seed, state_id, tape, graph, action] for tape in tape_half)
                        / len(tape_half)
                        for action in ACTIONS
                    ))
                    for tape_half in (DEVELOPMENT_TAPES[:4], DEVELOPMENT_TAPES[4:])
                )
                agreements.append((graph, halves[0] == halves[1]))
            hr_action = _argmax_smallest(means_by_graph["HR"])
            rh_action = _argmax_smallest(means_by_graph["RH"])
            common_values = tuple(
                0.5 * (means_by_graph["HR"][action] + means_by_graph["RH"][action])
                for action in ACTIONS
            )
            units.append(MappingUnit(
                seed, state_id, k, stratum, hr_action, rh_action,
                _argmax_smallest(common_values),
                tuple((graph, means_by_graph[graph]) for graph in GRAPHS),
                tuple((graph, ranks_by_graph[graph]) for graph in GRAPHS),
                tuple(margins), tuple(agreements),
            ))
    payload = {
        "schema": "SCDMP_MF_RS_MK_B01_DEVELOPMENT_MAPPING_V1",
        "object_id": STUDY_ID,
        "run_id": NAMED_RUN_ID,
        "tie_rule": "maximum_mean_then_smallest_native_action_index",
        "units": [
            {
                "seed": row.seed,
                "state_id": row.state_id,
                "k": row.k,
                "stratum": row.stratum,
                "hr_action": row.hr_action,
                "rh_action": row.rh_action,
                "common_action": row.common_action,
                "graph_means": {graph: list(values) for graph, values in row.graph_means},
                "graph_ranks": {graph: list(values) for graph, values in row.graph_ranks},
                "top_two_margins": dict(row.top_two_margins),
                "half_winner_agreement": dict(row.half_winner_agreement),
            }
            for row in units
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    # The namespace is prospectively fixed and therefore cannot depend on any
    # development outcome. The artifact fence, not address derivation, proves
    # that the complete mapping persisted before this namespace was opened.
    token = HELDOUT_NAMESPACE_TOKEN
    return DevelopmentMapping(tuple(units), rows, encoded, token)


__all__ = [
    "DevelopmentCell", "DevelopmentMapping", "DevelopmentMappingError", "MappingUnit",
    "freeze_development_mapping",
]
