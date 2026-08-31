"""Complete-only bounded FCEOV analysis with one all-or-none IUT claim."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log
from typing import Sequence

from .contracts import (
    CANDIDATE_ACTIONS,
    Disposition,
    FAILURE_LABELS,
    GRAPHS,
    INFERENCE_ALPHA,
    INFERENCE_COMMON_GAP_RAW_SUM_PASS,
    INFERENCE_CONTINUOUS_Q_STAR,
    INFERENCE_DISCRETE_Q_FAIL,
    INFERENCE_FIRST_GAP_RAW_SUM_PASS,
    INFERENCE_JOINT_POWER_LOWER_BOUND,
    INFERENCE_N561_JOINT_POWER_LOWER_BOUND,
    PANEL_WIDTH,
    PanelCell,
    TAPE_COUNT,
)


class AnalysisContractError(ValueError):
    pass


INFERENCE_SAMPLE_SIZE = TAPE_COUNT
EXPECTED_CELL_COUNT = PANEL_WIDTH
UTILITY_DENOMINATOR = 364
MAXIMUM_UTILITY_NUMERATOR = 363
GAP_NAMES = ("g_A_RH", "g_A_HR", "g_COMMON")
COMPONENT_ALPHA = INFERENCE_ALPHA
FIRST_ACTION_FIRST_PASSING_RAW_SUM = INFERENCE_FIRST_GAP_RAW_SUM_PASS
COMMON_FIRST_PASSING_RAW_SUM = INFERENCE_COMMON_GAP_RAW_SUM_PASS
CRITICAL_NORMALIZED_MEAN = INFERENCE_CONTINUOUS_Q_STAR
LARGEST_FAILING_NORMALIZED_MEAN = INFERENCE_DISCRETE_Q_FAIL
PLANNING_JOINT_POWER_LOWER_BOUND = INFERENCE_JOINT_POWER_LOWER_BOUND
N561_PLANNING_JOINT_POWER_LOWER_BOUND = INFERENCE_N561_JOINT_POWER_LOWER_BOUND
_LOG_ALPHA_INVERSE = log(1.0 / COMPONENT_ALPHA)


@dataclass(frozen=True, slots=True)
class TapeContrasts:
    """The four original paired contrasts, stored first on the exact /364 grid."""

    tape: int
    d_0m_numerator: int
    d_1m_numerator: int
    d_0c_numerator: int
    d_1c_numerator: int

    @property
    def d_0m(self) -> float:
        return self.d_0m_numerator / UTILITY_DENOMINATOR

    @property
    def d_1m(self) -> float:
        return self.d_1m_numerator / UTILITY_DENOMINATOR

    @property
    def d_0c(self) -> float:
        return self.d_0c_numerator / UTILITY_DENOMINATOR

    @property
    def d_1c(self) -> float:
        return self.d_1c_numerator / UTILITY_DENOMINATOR


@dataclass(frozen=True, slots=True)
class GapEvidence:
    """Audit statistics for one member of the inseparable three-gap conjunction."""

    name: str
    raw_utility_numerator_sum: int
    raw_gap_mean: float
    normalized_mean: float
    log_statistic: float
    p_value_upper: float
    first_passing_raw_sum: int
    component_test_passed: bool


@dataclass(frozen=True, slots=True)
class PanelAnalysis:
    disposition: str
    joint_claim_established: bool
    p_iut: float
    l_theta: float
    gaps: tuple[GapEvidence, GapEvidence, GapEvidence]
    tape_contrasts: tuple[TapeContrasts, ...]
    cell_means: tuple[tuple[str, str, float], ...]


def _validate_probability(value: float, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnalysisContractError(f"{name} must be a finite real in [0,1]")
    result = float(value)
    if not isfinite(result) or not 0.0 <= result <= 1.0:
        raise AnalysisContractError(f"{name} must be a finite real in [0,1]")
    return result


def binary_kl(observed: float, reference: float) -> float:
    """Return binary kl(observed || reference) with endpoint conventions."""

    x = _validate_probability(observed, name="observed mean")
    q = _validate_probability(reference, name="reference mean")
    if x == 0.0:
        return -log(1.0 - q) if q < 1.0 else float("inf")
    if x == 1.0:
        return -log(q) if q > 0.0 else float("inf")
    if q == 0.0 or q == 1.0:
        return float("inf")
    return x * log(x / q) + (1.0 - x) * log((1.0 - x) / (1.0 - q))


def binary_kl_from_half(normalized_mean: float) -> float:
    """Return kl(normalized_mean || 0.5) with continuous endpoint conventions."""

    return binary_kl(normalized_mean, 0.5)


def invert_marginal_lower(normalized_mean: float, *, sample_size: int) -> float:
    """Invert n*kl(x||ell)=log(20) on the shared unit-range support."""

    x = _validate_probability(normalized_mean, name="normalized mean")
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size <= 0:
        raise AnalysisContractError("sample size must be a positive integer")
    if x == 0.0:
        return 0.0
    lower = 0.0
    upper = x
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        statistic = sample_size * binary_kl(x, midpoint)
        if not isfinite(statistic):
            lower = midpoint
        elif statistic > _LOG_ALPHA_INVERSE:
            lower = midpoint
        else:
            upper = midpoint
    result = (lower + upper) / 2.0
    residual = sample_size * binary_kl(x, result)
    if not isfinite(result) or not isfinite(residual) or abs(residual - _LOG_ALPHA_INVERSE) > 1e-10:
        raise AnalysisContractError("marginal lower inversion failed")
    return result


def bounded_chernoff_p_value(normalized_mean: float, *, sample_size: int) -> tuple[float, float]:
    """Return the log statistic and conservative one-sided bounded-mean p-value."""

    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size <= 0:
        raise AnalysisContractError("sample size must be a positive integer")
    value = _validate_probability(normalized_mean, name="normalized mean")
    divergence = binary_kl_from_half(value)
    if value <= 0.5:
        return 0.0, 1.0
    log_statistic = sample_size * divergence
    p_value = exp(-log_statistic)
    if not isfinite(log_statistic) or not isfinite(p_value):
        raise AnalysisContractError("nonfinite bounded-mean statistic")
    return log_statistic, p_value


def _utility_numerator(row: PanelCell) -> int:
    if row.safe_dock:
        if (
            isinstance(row.dock_tick, bool)
            or not isinstance(row.dock_tick, int)
            or not 1 <= row.dock_tick <= UTILITY_DENOMINATOR
        ):
            raise AnalysisContractError("safe terminal cell has an invalid dock tick")
        return UTILITY_DENOMINATOR - row.dock_tick
    if row.dock_tick is not None:
        raise AnalysisContractError("unsafe terminal cell cannot have a dock tick")
    return 0


def _cell_numerators(cells: Sequence[PanelCell]) -> dict[tuple[int, str, str], int]:
    rows = tuple(cells)
    if len(rows) != EXPECTED_CELL_COUNT:
        raise AnalysisContractError("analysis requires 3372 terminal cells")
    result: dict[tuple[int, str, str], int] = {}
    for row in rows:
        if not isinstance(row, PanelCell):
            raise AnalysisContractError("analysis inputs must be PanelCell values")
        if not isinstance(row.terminal, bool) or not row.terminal:
            raise AnalysisContractError("analysis requires 3372 terminal cells")
        if not isinstance(row.safe_dock, bool):
            raise AnalysisContractError("panel endpoint flags must be bool")
        if (
            isinstance(row.tape, bool)
            or not isinstance(row.tape, int)
            or not 0 <= row.tape < INFERENCE_SAMPLE_SIZE
        ):
            raise AnalysisContractError("panel tape index differs")
        if row.graph not in GRAPHS:
            raise AnalysisContractError("panel graph label differs")
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
        result[key] = _utility_numerator(row)
    expected = {
        (tape, graph, action)
        for tape in range(INFERENCE_SAMPLE_SIZE)
        for graph in GRAPHS
        for action in ("COMMON", "A_HR", "A_RH")
    }
    if set(result) != expected:
        raise AnalysisContractError("panel cell inventory differs")
    return result


def _gap_evidence(name: str, raw_sum: int) -> GapEvidence:
    if name in ("g_A_RH", "g_A_HR"):
        normalization_denominator = 2 * MAXIMUM_UTILITY_NUMERATOR * INFERENCE_SAMPLE_SIZE
        threshold = FIRST_ACTION_FIRST_PASSING_RAW_SUM
    elif name == "g_COMMON":
        normalization_denominator = 4 * MAXIMUM_UTILITY_NUMERATOR * INFERENCE_SAMPLE_SIZE
        threshold = COMMON_FIRST_PASSING_RAW_SUM
    else:  # pragma: no cover - only fixed internal names call this helper
        raise AnalysisContractError("unknown gap name")
    normalized_mean = 0.5 + raw_sum / normalization_denominator
    log_statistic, p_value = bounded_chernoff_p_value(
        normalized_mean, sample_size=INFERENCE_SAMPLE_SIZE
    )
    integer_pass = raw_sum >= threshold
    if abs(log_statistic - _LOG_ALPHA_INVERSE) <= 1e-12:
        raise AnalysisContractError("ambiguous bounded-mean decision boundary")
    log_space_pass = log_statistic > _LOG_ALPHA_INVERSE
    p_value_pass = p_value < COMPONENT_ALPHA
    if integer_pass != log_space_pass or integer_pass != p_value_pass:
        raise AnalysisContractError("integer-grid, log-space, and p-value decisions disagree")
    return GapEvidence(
        name=name,
        raw_utility_numerator_sum=raw_sum,
        raw_gap_mean=raw_sum / (2 * UTILITY_DENOMINATOR * INFERENCE_SAMPLE_SIZE),
        normalized_mean=normalized_mean,
        log_statistic=log_statistic,
        p_value_upper=p_value,
        first_passing_raw_sum=threshold,
        component_test_passed=integer_pass,
    )


def analyze_complete_panel(cells: Sequence[PanelCell]) -> PanelAnalysis:
    """Analyze exactly 562 complete tapes; no partial panel has a scientific branch."""

    values = _cell_numerators(cells)
    contrasts = tuple(
        TapeContrasts(
            tape=tape,
            d_0m_numerator=values[tape, "RH", "A_RH"] - values[tape, "RH", "A_HR"],
            d_1m_numerator=values[tape, "HR", "A_HR"] - values[tape, "HR", "A_RH"],
            d_0c_numerator=values[tape, "RH", "A_RH"] - values[tape, "RH", "COMMON"],
            d_1c_numerator=values[tape, "HR", "A_HR"] - values[tape, "HR", "COMMON"],
        )
        for tape in range(INFERENCE_SAMPLE_SIZE)
    )
    raw_sums = (
        sum(row.d_1m_numerator for row in contrasts),
        sum(row.d_0m_numerator for row in contrasts),
        sum(row.d_0c_numerator + row.d_1c_numerator for row in contrasts),
    )
    gaps_untyped = tuple(
        _gap_evidence(name, raw_sum) for name, raw_sum in zip(GAP_NAMES, raw_sums, strict=True)
    )
    gaps = (gaps_untyped[0], gaps_untyped[1], gaps_untyped[2])
    # This is the production branch.  It is intentionally evaluated only on
    # exact integer endpoint numerators, never on reconstructed utility floats.
    joint_established = (
        raw_sums[0] >= FIRST_ACTION_FIRST_PASSING_RAW_SUM
        and raw_sums[1] >= FIRST_ACTION_FIRST_PASSING_RAW_SUM
        and raw_sums[2] >= COMMON_FIRST_PASSING_RAW_SUM
    )
    p_iut = max(row.p_value_upper for row in gaps)
    if (p_iut < COMPONENT_ALPHA) != joint_established:
        raise AnalysisContractError("IUT p-value and integer-grid decisions disagree")
    l_theta = min(
        invert_marginal_lower(row.normalized_mean, sample_size=INFERENCE_SAMPLE_SIZE) - 0.5
        for row in gaps
    )
    if (l_theta > 0.0) != joint_established:
        raise AnalysisContractError("joint lower and integer-grid decisions disagree")
    cell_means = tuple(
        (
            graph,
            action,
            sum(values[tape, graph, action] for tape in range(INFERENCE_SAMPLE_SIZE))
            / (UTILITY_DENOMINATOR * INFERENCE_SAMPLE_SIZE),
        )
        for graph in GRAPHS
        for action in CANDIDATE_ACTIONS
    )
    return PanelAnalysis(
        disposition=Disposition.ESTABLISHED.value if joint_established else Disposition.CLOSED.value,
        joint_claim_established=joint_established,
        p_iut=p_iut,
        l_theta=l_theta,
        gaps=gaps,
        tape_contrasts=contrasts,
        cell_means=cell_means,
    )


__all__ = [
    "AnalysisContractError",
    "COMMON_FIRST_PASSING_RAW_SUM",
    "COMPONENT_ALPHA",
    "CRITICAL_NORMALIZED_MEAN",
    "EXPECTED_CELL_COUNT",
    "FIRST_ACTION_FIRST_PASSING_RAW_SUM",
    "GAP_NAMES",
    "GapEvidence",
    "INFERENCE_SAMPLE_SIZE",
    "LARGEST_FAILING_NORMALIZED_MEAN",
    "N561_PLANNING_JOINT_POWER_LOWER_BOUND",
    "PLANNING_JOINT_POWER_LOWER_BOUND",
    "PanelAnalysis",
    "TapeContrasts",
    "analyze_complete_panel",
    "binary_kl",
    "binary_kl_from_half",
    "bounded_chernoff_p_value",
    "invert_marginal_lower",
]
