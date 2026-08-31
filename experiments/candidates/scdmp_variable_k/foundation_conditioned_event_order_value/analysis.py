"""Complete-only paired FCEOV analysis with no action selection."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isfinite, sqrt
from typing import Mapping, Sequence

from scipy.stats import t as student_t

from .contracts import (
    CANDIDATE_ACTIONS, Disposition, FAILURE_LABELS, GRAPHS, PANEL_WIDTH, PanelCell, TAPE_COUNT,
)
from .panel import mission_utility


class AnalysisContractError(ValueError):
    pass


CONTRAST_NAMES = ("d_0m", "d_1m", "d_0c", "d_1c")
FAMILY_ALPHA = 0.05
FAMILY_SIZE = 4


@dataclass(frozen=True, slots=True)
class TapeContrasts:
    tape: int
    d_0m: float
    d_1m: float
    d_0c: float
    d_1c: float

    @property
    def interaction(self) -> float:
        return 0.5 * (self.d_0m + self.d_1m)

@dataclass(frozen=True, slots=True)
class PairedBound:
    name: str
    mean: float
    standard_error: float
    lower: float
    zero_variance: bool


@dataclass(frozen=True, slots=True)
class PanelAnalysis:
    disposition: str
    bounds: tuple[PairedBound, ...]
    tape_contrasts: tuple[TapeContrasts, ...]
    cell_means: tuple[tuple[str, str, float], ...]
    interaction: float
    candidate_order_value: float


def paired_t_lower_bound(
    values: Sequence[float], *, name: str = "contrast"
) -> PairedBound:
    raw = tuple(values)
    if len(raw) != TAPE_COUNT or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) for value in raw
    ):
        raise AnalysisContractError("paired Student-t input must contain 24 finite tape blocks")
    rows = tuple(float(value) for value in raw)
    if any(not isfinite(value) for value in rows):
        raise AnalysisContractError("paired Student-t input must contain 24 finite tape blocks")
    mean = fsum(rows) / len(rows)
    centered_squares = fsum((value - mean) * (value - mean) for value in rows)
    if centered_squares == 0.0:
        return PairedBound(name, mean, 0.0, mean, True)
    variance = centered_squares / (len(rows) - 1)
    standard_error = sqrt(variance / len(rows))
    critical = float(student_t.ppf(1.0 - FAMILY_ALPHA / FAMILY_SIZE, df=23))
    return PairedBound(name, mean, standard_error, mean - critical * standard_error, False)


def _cell_values(cells: Sequence[PanelCell]) -> dict[tuple[int, str, str], float]:
    rows = tuple(cells)
    if len(rows) != PANEL_WIDTH or any(not row.terminal for row in rows):
        raise AnalysisContractError("analysis requires 144 terminal cells")
    result: dict[tuple[int, str, str], float] = {}
    for row in rows:
        if not isinstance(row, PanelCell):
            raise AnalysisContractError("analysis inputs must be PanelCell values")
        if not isinstance(row.terminal, bool) or not isinstance(row.safe_dock, bool):
            raise AnalysisContractError("panel endpoint flags must be bool")
        if isinstance(row.tape, bool) or not isinstance(row.tape, int) or not 0 <= row.tape < TAPE_COUNT:
            raise AnalysisContractError("panel tape index differs")
        if (
            isinstance(row.action_index, bool)
            or not isinstance(row.action_index, int)
            or CANDIDATE_ACTIONS.get(row.action_name) != row.action_index
        ):
            raise AnalysisContractError("panel action label and catalogue index differ")
        if (
            not isinstance(row.failures, tuple)
            or len(set(row.failures)) != len(row.failures)
            or any(label not in FAILURE_LABELS for label in row.failures)
            or (row.safe_dock and row.failures)
        ):
            raise AnalysisContractError("panel endpoint/failure semantics differ")
        key = (row.tape, row.graph, row.action_name)
        if key in result:
            raise AnalysisContractError("duplicate panel lane")
        result[key] = mission_utility(safe_dock=row.safe_dock, dock_tick=row.dock_tick)
    expected = {
        (tape, graph, action)
        for tape in range(TAPE_COUNT)
        for graph in GRAPHS
        for action in ("COMMON", "A_HR", "A_RH")
    }
    if set(result) != expected:
        raise AnalysisContractError("panel cell inventory differs")
    return result


def analyze_complete_panel(cells: Sequence[PanelCell]) -> PanelAnalysis:
    values = _cell_values(cells)
    contrasts = tuple(
        TapeContrasts(
            tape,
            values[tape, "RH", "A_RH"] - values[tape, "RH", "A_HR"],
            values[tape, "HR", "A_HR"] - values[tape, "HR", "A_RH"],
            values[tape, "RH", "A_RH"] - values[tape, "RH", "COMMON"],
            values[tape, "HR", "A_HR"] - values[tape, "HR", "COMMON"],
        )
        for tape in range(TAPE_COUNT)
    )
    bounds = tuple(
        paired_t_lower_bound(tuple(getattr(row, name) for row in contrasts), name=name)
        for name in CONTRAST_NAMES
    )
    established = all(row.lower > 0.0 for row in bounds)
    means = {
        (graph, action): fsum(values[tape, graph, action] for tape in range(TAPE_COUNT)) / TAPE_COUNT
        for graph in GRAPHS
        for action in CANDIDATE_ACTIONS
    }
    d_means = {
        name: fsum(getattr(row, name) for row in contrasts) / TAPE_COUNT
        for name in CONTRAST_NAMES
    }
    interaction = 0.5 * (d_means["d_0m"] + d_means["d_1m"])
    candidate_value = min(
        0.5 * d_means["d_0m"],
        0.5 * d_means["d_1m"],
        0.5 * (d_means["d_0c"] + d_means["d_1c"]),
    )
    return PanelAnalysis(
        Disposition.ESTABLISHED.value if established else Disposition.CLOSED.value,
        bounds,
        contrasts,
        tuple((graph, action, means[graph, action]) for graph in GRAPHS for action in CANDIDATE_ACTIONS),
        interaction,
        candidate_value,
    )


__all__ = [
    "AnalysisContractError", "CONTRAST_NAMES", "FAMILY_ALPHA", "PairedBound", "PanelAnalysis",
    "TapeContrasts", "analyze_complete_panel", "paired_t_lower_bound",
]
