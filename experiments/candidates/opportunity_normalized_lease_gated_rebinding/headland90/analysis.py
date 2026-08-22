"""Pure endpoint, inference, non-harm, competence, and result-map formulas.

All functions consume already-retained scalar/count facts.  Nothing here can
run the host, select coordinates, draw randomness, or read an artifact tree.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
import math

from .controllers import Q


T_975_DF127 = 1.97882
HELD_OUT_REPLICATES = 128
OVERRIDE_DENOMINATOR_TICKS = 20 * (48 + 144)


def _mean(values: Sequence[Fraction | float]) -> Fraction | float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def service_fraction(valid_scored_ticks: int, scored_ticks: int) -> Fraction:
    if scored_ticks <= 0 or not 0 <= valid_scored_ticks <= scored_ticks:
        raise ValueError("valid and scored tick counts are inconsistent")
    return Fraction(valid_scored_ticks, scored_ticks)


def block_value(
    short_service: Fraction | float, long_service: Fraction | float
) -> Fraction | float:
    return (32 * short_service + 128 * long_service) / 160


def lower_cvar(values: Sequence[Fraction | float], mass: Fraction = Fraction(1, 10)) -> Fraction | float:
    if not values:
        raise ValueError("lower CVaR requires at least one complete value")
    if not Fraction(0) < mass <= Fraction(1):
        raise ValueError("CVaR mass must lie in (0,1]")
    ordered = sorted(values)
    exact_count = mass * len(ordered)
    whole = exact_count.numerator // exact_count.denominator
    fractional = exact_count - whole
    numerator: Fraction | float = sum(ordered[:whole])
    if fractional:
        numerator += fractional * ordered[whole]
    return numerator / exact_count


@dataclass(frozen=True)
class ReplicateEndpoints:
    mean_value: Fraction | float
    tail_value: Fraction | float


def replicate_endpoints(block_values: Sequence[Fraction | float]) -> ReplicateEndpoints:
    if len(block_values) != 20:
        raise ValueError("a conforming replicate has exactly 20 complete block values")
    return ReplicateEndpoints(_mean(block_values), lower_cvar(block_values))


@dataclass(frozen=True)
class PanelEndpoints:
    mean_value: Fraction | float
    tail_value: Fraction | float


def panel_endpoints(replicates: Sequence[ReplicateEndpoints]) -> PanelEndpoints:
    if not replicates:
        raise ValueError("panel endpoints require complete replicate summaries")
    return PanelEndpoints(
        _mean([row.mean_value for row in replicates]),
        _mean([row.tail_value for row in replicates]),
    )


@dataclass(frozen=True)
class PairedInterval:
    mean: float
    sample_sd: float
    lower: float
    upper: float
    n: int


def paired_interval(
    differences: Sequence[float], *, require_held_out_panel: bool = True
) -> PairedInterval:
    n = len(differences)
    if require_held_out_panel and n != HELD_OUT_REPLICATES:
        raise ValueError("held-out inference requires exactly 128 paired replicate differences")
    if n < 2 or any(not math.isfinite(float(value)) for value in differences):
        raise ValueError("paired inference requires at least two finite differences")
    mean = math.fsum(float(value) for value in differences) / n
    squared = math.fsum((float(value) - mean) ** 2 for value in differences)
    sd = math.sqrt(squared / (n - 1))
    radius = T_975_DF127 * sd / math.sqrt(n)
    return PairedInterval(mean, sd, mean - radius, mean + radius, n)


@dataclass(frozen=True)
class PositiveGate:
    point: float
    lower: float
    sample_sd: float
    minimum_effect: float

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value)
            for value in (self.point, self.lower, self.sample_sd, self.minimum_effect)
        ):
            raise ValueError("gate facts must be finite")
        if self.sample_sd < 0 or self.minimum_effect < 0:
            raise ValueError("gate SD and minimum effect must be nonnegative")

    @property
    def passes(self) -> bool:
        return self.point >= self.minimum_effect and self.lower > 0.0


TWO_GATE_NAMES = ("D_S", "D_L", "Delta_mean", "Delta_tail")


def _require_gate_names(gates: Mapping[str, PositiveGate], names: Iterable[str]) -> tuple[str, ...]:
    expected = tuple(names)
    if set(gates) != set(expected):
        raise ValueError(f"gate names must be exactly {expected!r}")
    return expected


def two_nonpass_power_adequate(gates: Mapping[str, PositiveGate]) -> bool:
    _require_gate_names(gates, TWO_GATE_NAMES)
    limits = {"D_S": 0.080, "D_L": 0.080, "Delta_mean": 0.080, "Delta_tail": 0.200}
    return all(gate.passes or gate.sample_sd <= limits[name] for name, gate in gates.items())


def flex_nonpass_power_adequate(gates: Mapping[str, PositiveGate]) -> bool:
    names = _require_gate_names(gates, ("Delta_FLEX_mean", "Delta_FLEX_tail"))
    limits = {"Delta_FLEX_mean": 0.080, "Delta_FLEX_tail": 0.200}
    return all(gates[name].passes or gates[name].sample_sd <= limits[name] for name in names)


@dataclass(frozen=True)
class SupportFacts:
    voluntary_keep: int
    voluntary_update: int
    replicates_with_both: int

    @property
    def adequate(self) -> bool:
        return (
            self.voluntary_keep >= 256
            and self.voluntary_update >= 256
            and self.replicates_with_both >= 96
        )


def voluntary_support_adequate(by_stratum: Mapping[str, SupportFacts]) -> bool:
    if set(by_stratum) != {"S", "L"}:
        raise ValueError("support facts require exactly S and L strata")
    return all(facts.adequate for facts in by_stratum.values())


@dataclass(frozen=True)
class HardSafetyFacts:
    terrain_penetrations: int = 0
    geofence_exits: int = 0
    separation_breaches: int = 0
    no_safe_control: int = 0
    no_planner_solution: int = 0
    battery_exhaustions: int = 0
    numerical_faults: int = 0

    @property
    def hard_safe(self) -> bool:
        values = (
            self.terrain_penetrations,
            self.geofence_exits,
            self.separation_breaches,
            self.no_safe_control,
            self.no_planner_solution,
            self.battery_exhaustions,
            self.numerical_faults,
        )
        if any(value < 0 for value in values):
            raise ValueError("hard-safety counts must be nonnegative")
        return not any(values)


def override_fraction(override_tick_intervals: int) -> Fraction:
    if not 0 <= override_tick_intervals <= OVERRIDE_DENOMINATOR_TICKS:
        raise ValueError("override ticks exceed the 20-block encounter denominator")
    return Fraction(override_tick_intervals, OVERRIDE_DENOMINATOR_TICKS)


def override_ucb95(
    controller_overrides: Sequence[int], global_overrides: Sequence[int]
) -> float:
    if len(controller_overrides) != HELD_OUT_REPLICATES or len(global_overrides) != HELD_OUT_REPLICATES:
        raise ValueError("override non-harm requires 128 paired held-out replicates")
    differences = [
        float(override_fraction(controller) - override_fraction(global_))
        for controller, global_ in zip(controller_overrides, global_overrides)
    ]
    interval = paired_interval(differences)
    return interval.mean + T_975_DF127 * interval.sample_sd / math.sqrt(HELD_OUT_REPLICATES)


def selected_controller_nonharm(
    calibration: HardSafetyFacts,
    held_out: HardSafetyFacts,
    override_ucb: float,
) -> bool:
    if not math.isfinite(override_ucb):
        raise ValueError("override UCB must be finite")
    return calibration.hard_safe and held_out.hard_safe and override_ucb <= 0.01


def reciprocal_control_nonharm(held_out: HardSafetyFacts, override_ucb: float) -> bool:
    if not math.isfinite(override_ucb):
        raise ValueError("override UCB must be finite")
    return held_out.hard_safe and override_ucb <= 0.01


def global_competent(
    *,
    selected_nonharm: bool,
    calibration_mean: Fraction | float,
    held_out_mean: Fraction | float,
    held_out_tail: Fraction | float,
    support_by_stratum: Mapping[str, SupportFacts],
) -> bool:
    return (
        selected_nonharm
        and 1 - calibration_mean >= Fraction(1, 20)
        and held_out_mean >= Fraction(1, 4)
        and held_out_tail >= Fraction(1, 10)
        and voluntary_support_adequate(support_by_stratum)
    )


def conditional_maxima(values: Mapping[Fraction, Fraction | float]) -> frozenset[Fraction]:
    if set(values) != set(Q):
        raise ValueError("conditional response curve must contain exactly Q")
    maximum = max(values.values())
    return frozenset(q for q, value in values.items() if value == maximum)


def q_distance_ticks(q: Fraction, candidates: Iterable[Fraction]) -> int:
    candidate_set = tuple(candidates)
    if not candidate_set:
        raise ValueError("rate-distance target set must be nonempty")
    distances = tuple(8 * abs(q - candidate) for candidate in candidate_set)
    if any(distance.denominator != 1 for distance in distances):
        raise ValueError("rate distances must lie on the frozen eighth grid")
    return int(min(distances))


def rate_response_identified(
    *,
    selected_short: Fraction,
    selected_long: Fraction,
    maxima_short_cal: Iterable[Fraction],
    maxima_long_cal: Iterable[Fraction],
    maxima_short_c1: Iterable[Fraction],
    maxima_short_c2: Iterable[Fraction],
    maxima_long_c1: Iterable[Fraction],
    maxima_long_c2: Iterable[Fraction],
) -> bool:
    m_s_cal, m_l_cal = frozenset(maxima_short_cal), frozenset(maxima_long_cal)
    if not m_s_cal or not m_l_cal:
        raise ValueError("complete-panel conditional maxima must be nonempty")
    return (
        m_s_cal.isdisjoint(m_l_cal)
        and q_distance_ticks(selected_short, maxima_short_c1) <= 1
        and q_distance_ticks(selected_short, maxima_short_c2) <= 1
        and q_distance_ticks(selected_long, maxima_long_c1) <= 1
        and q_distance_ticks(selected_long, maxima_long_c2) <= 1
    )


def two_answerable(
    *,
    package_valid: bool,
    global_is_competent: bool,
    response_identified: bool,
    support_adequate: bool,
    selected_nonharm: bool,
    reciprocal_controls_valid: bool,
) -> bool:
    return all(
        (
            package_valid,
            global_is_competent,
            response_identified,
            support_adequate,
            selected_nonharm,
            reciprocal_controls_valid,
        )
    )


def flex_containment_answerable(
    *,
    package_valid: bool,
    global_is_competent: bool,
    support_adequate: bool,
    selected_nonharm: bool,
    algebraically_distinct: bool,
    realized_support_distinct: bool,
) -> bool:
    return all(
        (
            package_valid,
            global_is_competent,
            support_adequate,
            selected_nonharm,
            algebraically_distinct,
            realized_support_distinct,
        )
    )


def flex_adaptive_answerable(*, containment_answerable: bool, timing_member: bool) -> bool:
    return containment_answerable and timing_member


def flex_global_qualifies(
    *, adaptive_answerable: bool, gates: Mapping[str, PositiveGate]
) -> bool:
    names = _require_gate_names(gates, ("Delta_FLEX_mean", "Delta_FLEX_tail"))
    return adaptive_answerable and all(gates[name].passes for name in names)


FLEX_TWO_COMPATIBLE = "FLEX_TWO_ABSOLUTELY_COMPATIBLE"
FLEX_STABLE_LOSS = "FLEX_STABLY_LOSES_TWO"
FLEX_RELATION_UNRESOLVED = "FLEX_RELATION_UNRESOLVED"
FLEX_RELATION_POWER_NONIDENTIFYING = "FLEX_RELATION_POWER_NONIDENTIFYING"
FLEX_RELATION_NOT_ANSWERABLE = "FLEX_RELATION_NOT_ANSWERABLE"


def flex_two_relation(
    mean: PairedInterval,
    tail: PairedInterval,
    *,
    flex_adaptive_answerable: bool,
    two_is_answerable: bool,
) -> str:
    if not flex_adaptive_answerable or not two_is_answerable:
        return FLEX_RELATION_NOT_ANSWERABLE
    intervals = (mean, tail)
    compatible = tuple(
        abs(row.mean) <= 0.01 and row.lower > -0.01 and row.upper < 0.01
        for row in intervals
    )
    stable_loss = tuple(row.mean < -0.01 and row.upper < -0.01 for row in intervals)
    if all(compatible):
        return FLEX_TWO_COMPATIBLE
    if any(stable_loss):
        return FLEX_STABLE_LOSS
    unresolved = (
        row for row, is_compatible, loses in zip(intervals, compatible, stable_loss)
        if not is_compatible and not loses
    )
    if any(row.sample_sd > 0.040 for row in unresolved):
        return FLEX_RELATION_POWER_NONIDENTIFYING
    return FLEX_RELATION_UNRESOLVED


@dataclass(frozen=True)
class ResultMapFacts:
    common_nonidentification_reason: str | None
    two_is_answerable: bool
    two_nonidentification_reason: str | None
    selected_q_short: Fraction
    selected_q_long: Fraction
    two_gates: Mapping[str, PositiveGate]
    flex_adaptive_answerable: bool
    flex_global_gates: Mapping[str, PositiveGate]
    flex_two_relation: str = FLEX_RELATION_NOT_ANSWERABLE


@dataclass(frozen=True)
class ResultMapOutcome:
    primary: str
    registered_two_rate_qualifies: bool
    opposite_sign_two_rate: bool
    flex_continuous_timing_question: bool
    flex_global_interpretation: str
    flex_two_interpretation: str
    no_current_timing_evidence: bool


def evaluate_result_map(facts: ResultMapFacts) -> ResultMapOutcome:
    """Apply the Section-15 ordered map without making a scientific decision."""

    _require_gate_names(facts.two_gates, TWO_GATE_NAMES)
    _require_gate_names(facts.flex_global_gates, ("Delta_FLEX_mean", "Delta_FLEX_tail"))
    if facts.common_nonidentification_reason:
        return ResultMapOutcome(
            facts.common_nonidentification_reason,
            False,
            False,
            False,
            "FLEX_NOT_INFERENTIAL_UNDER_COMMON_NONIDENTIFICATION",
            FLEX_RELATION_NOT_ANSWERABLE,
            False,
        )

    flex_qualifies = flex_global_qualifies(
        adaptive_answerable=facts.flex_adaptive_answerable,
        gates=facts.flex_global_gates,
    )
    flex_power_adequate = flex_nonpass_power_adequate(facts.flex_global_gates)
    if flex_qualifies:
        flex_interpretation = "FLEX_GLOBAL_QUALIFIES"
    elif facts.flex_adaptive_answerable and flex_power_adequate:
        flex_interpretation = "FLEX_VALID_POWERED_NONPASS"
    elif facts.flex_adaptive_answerable:
        flex_interpretation = "FLEX_POWER_NONIDENTIFYING"
    else:
        flex_interpretation = "FLEX_NOT_ADAPTIVELY_ANSWERABLE"

    if not facts.two_is_answerable:
        if not facts.two_nonidentification_reason:
            raise ValueError("a false TWO_ANSWERABLE fact requires its exact nonidentification reason")
        return ResultMapOutcome(
            facts.two_nonidentification_reason,
            False,
            False,
            flex_qualifies,
            flex_interpretation,
            FLEX_RELATION_NOT_ANSWERABLE,
            False,
        )

    all_two_gates_pass = all(gate.passes for gate in facts.two_gates.values())
    registered = all_two_gates_pass and facts.selected_q_short > facts.selected_q_long
    opposite = all_two_gates_pass and facts.selected_q_short < facts.selected_q_long
    if registered:
        primary = "REGISTERED_TWO_RATE_QUALIFIES"
    elif opposite:
        primary = "OPPOSITE_SIGN_TWO_RATE"
    elif two_nonpass_power_adequate(facts.two_gates):
        primary = "VALID_TWO_RATE_NONPASS"
    else:
        primary = "TWO_POWER_NONIDENTIFYING"

    powered_two_nonpass = not registered and not opposite and two_nonpass_power_adequate(
        facts.two_gates
    )
    no_current = (
        powered_two_nonpass
        and facts.flex_adaptive_answerable
        and not flex_qualifies
        and flex_power_adequate
    )
    return ResultMapOutcome(
        primary,
        registered,
        opposite,
        (not registered) and flex_qualifies,
        flex_interpretation,
        facts.flex_two_relation,
        no_current,
    )
