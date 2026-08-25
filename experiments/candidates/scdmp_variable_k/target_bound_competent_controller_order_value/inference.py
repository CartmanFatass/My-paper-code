"""Exact simultaneous inference and first-true map for TBCC revision 02.

All functions consume complete in-memory replicate summaries.  The accepted
Stage-1b opportunity analyzer remains the sole owner of Q/D/S; this module only
accepts its complete ``OpportunityGateAnalysis`` disposition.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Final, Iterable, Mapping, Sequence

from scipy.stats import t as student_t

from .evaluation import (
    COMPETENCE_REGIMES,
    CONTROLLERS,
    EvaluationContractError,
    FAILURE_FIELDS,
    GRAPH_ORDERS,
    FoundationReplicateSummary,
    FinalReplicateSummary,
    REPLICATE_COUNT,
)
from .lifecycle import (
    GateOutcome,
    InferenceBranch,
    InferenceFixture,
    PredicateState,
    RouteState,
    exhaustive_first_true_branch,
)
from .opportunity import OpportunityGateAnalysis


class InferenceContractError(RuntimeError):
    pass


DF: Final[int] = 23
FAMILY_ERROR: Final[float] = 0.05
FOUNDATION_FAMILY_MEMBERS: Final[int] = 17
FINAL_COMPETENCE_FAMILY_MEMBERS: Final[int] = 15
DIRECT_FAMILY_MEMBERS: Final[int] = 26
QUALIFICATION_CONTROLLERS: Final[tuple[str, ...]] = ("TREAT", "FREE", "SET")
CONTROL_CONTROLLERS: Final[tuple[str, ...]] = (
    "FOUNDATION", "FREE", "REVERSED", "SET"
)
COMPETENCE_KEYS: Final[tuple[str, ...]] = tuple(
    f"{regime}/{order}" for regime in COMPETENCE_REGIMES for order in GRAPH_ORDERS
) + ("pooled",)
FOUNDATION_SAFE_KEYS: Final[tuple[str, ...]] = tuple(
    f"{regime}/{order}"
    for regime in ("fixed-5", "fixed-11", "fixed-7", "fixed-13", "7-to-13", "13-to-7")
    for order in GRAPH_ORDERS
)
VALIDITY_FLAGS: Final[tuple[str, ...]] = (
    "registered_source_conformance",
    "identity_conformance",
    "pairing_conformance",
    "event_map_conformance",
    "public_aliasing_conformance",
    "support_graph_conformance",
    "set_invariance_conformance",
    "strict_containment_conformance",
    "foundation_immutability_conformance",
    "external_k_conformance",
    "direct_endpoint_conformance",
    "workload_conformance",
    "atomicity_conformance",
    "inference_conformance",
    "no_partial_inspection",
    "no_per_k_parameter_or_update",
    "no_post_absorption_policy_query",
)

V_MARGINS: Final[Mapping[str, float]] = {
    "FOUNDATION": 0.025,
    "FREE": 0.015,
    "REVERSED": 0.020,
    "SET": 0.020,
}
W_MARGINS: Final[Mapping[str, float]] = {
    "FOUNDATION": 0.020,
    "FREE": 0.0125,
    "REVERSED": 0.0175,
    "SET": 0.0175,
}


def _vector(values: Sequence[float]) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != REPLICATE_COUNT or any(not math.isfinite(value) for value in result):
        raise InferenceContractError("inference vector must contain exactly 24 finite values")
    return result


def _mean_variance(values: tuple[float, ...]) -> tuple[float, float]:
    if all(value == values[0] for value in values):
        return values[0], 0.0
    mean = math.fsum(values) / REPLICATE_COUNT
    variance = math.fsum((value - mean) ** 2 for value in values) / DF
    return mean, variance


@dataclass(frozen=True, slots=True)
class OneSidedBound:
    mean: float
    bound: float
    direction: str
    standard_error: float
    critical: float
    sample_count: int = REPLICATE_COUNT
    family_members: int = FOUNDATION_FAMILY_MEMBERS


def one_sided_bound(values: Sequence[float], *, direction: str) -> OneSidedBound:
    vector = _vector(values)
    if direction not in ("lower", "upper"):
        raise InferenceContractError("one-sided direction must be lower or upper")
    mean, variance = _mean_variance(vector)
    standard_error = math.sqrt(variance / REPLICATE_COUNT)
    critical = float(student_t.ppf(1.0 - FAMILY_ERROR / FOUNDATION_FAMILY_MEMBERS, df=DF))
    signed = -1.0 if direction == "lower" else 1.0
    return OneSidedBound(
        mean=mean,
        bound=mean + signed * critical * standard_error,
        direction=direction,
        standard_error=standard_error,
        critical=critical,
    )


@dataclass(frozen=True, slots=True)
class TwoSidedInterval:
    mean: float
    lower: float
    upper: float
    standard_error: float
    critical: float
    sample_count: int = REPLICATE_COUNT
    family_members: int = 0


def two_sided_interval(values: Sequence[float], *, family_members: int) -> TwoSidedInterval:
    vector = _vector(values)
    if family_members <= 0:
        raise InferenceContractError("interval family size must be positive")
    mean, variance = _mean_variance(vector)
    standard_error = math.sqrt(variance / REPLICATE_COUNT)
    critical = float(student_t.ppf(1.0 - FAMILY_ERROR / (2.0 * family_members), df=DF))
    half_width = critical * standard_error
    return TwoSidedInterval(
        mean=mean,
        lower=mean - half_width,
        upper=mean + half_width,
        standard_error=standard_error,
        critical=critical,
        family_members=family_members,
    )


def higher_better_state(interval: TwoSidedInterval, margin: float) -> PredicateState:
    if interval.lower > margin:
        return PredicateState.PASS
    if interval.upper <= margin:
        return PredicateState.FAIL
    return PredicateState.UNRESOLVED


def upper_margin_state(interval: TwoSidedInterval, margin: float) -> PredicateState:
    if interval.upper < margin:
        return PredicateState.PASS
    if interval.lower >= margin:
        return PredicateState.FAIL
    return PredicateState.UNRESOLVED


@dataclass(frozen=True, slots=True)
class FoundationCompetenceAnalysis:
    safe_lower_bounds: tuple[tuple[str, OneSidedBound], ...]
    pooled_lower_bound: OneSidedBound
    failure_upper_bounds: tuple[tuple[str, OneSidedBound], ...]
    gate: GateOutcome
    family_members: int = FOUNDATION_FAMILY_MEMBERS


def _ordered_foundation(
    summaries: Iterable[FoundationReplicateSummary],
) -> tuple[FoundationReplicateSummary, ...]:
    values = tuple(summaries)
    for value in values:
        value.validate()
    if len(values) != REPLICATE_COUNT or {value.replicate for value in values} != set(range(REPLICATE_COUNT)):
        raise InferenceContractError("foundation analyzer requires exact replicates 0 through 23")
    return tuple(sorted(values, key=lambda value: value.replicate))


def analyze_foundation_competence(
    summaries: Iterable[FoundationReplicateSummary],
) -> FoundationCompetenceAnalysis:
    ordered = _ordered_foundation(summaries)
    safe_maps = [dict(value.safe_cells) for value in ordered]
    failure_maps = [dict(value.worst_failures) for value in ordered]
    safe = tuple(
        (key, one_sided_bound(tuple(value[key] for value in safe_maps), direction="lower"))
        for key in FOUNDATION_SAFE_KEYS
    )
    pooled = one_sided_bound(tuple(value.pooled_safe for value in ordered), direction="lower")
    failures = tuple(
        (key, one_sided_bound(tuple(value[key] for value in failure_maps), direction="upper"))
        for key in FAILURE_FIELDS
    )
    passes = (
        all(bound.bound > 0.72 for _, bound in safe)
        and pooled.bound > 0.84
        and all(bound.bound < 0.10 for _, bound in failures)
    )
    return FoundationCompetenceAnalysis(
        safe_lower_bounds=safe,
        pooled_lower_bound=pooled,
        failure_upper_bounds=failures,
        gate=GateOutcome.PASS if passes else GateOutcome.NONPASS,
    )


@dataclass(frozen=True, slots=True)
class CompetenceItem:
    controller: str
    key: str
    threshold: float
    interval: TwoSidedInterval
    state: PredicateState


@dataclass(frozen=True, slots=True)
class DirectItem:
    name: str
    interval: TwoSidedInterval


@dataclass(frozen=True, slots=True)
class RouteAnalysis:
    endpoint: str
    state: RouteState
    item_states: tuple[tuple[str, PredicateState], ...]


@dataclass(frozen=True, slots=True)
class FinalInferenceAnalysis:
    competence_items: tuple[CompetenceItem, ...]
    competence_states: tuple[tuple[str, PredicateState], ...]
    direct_items: tuple[DirectItem, ...]
    v_route: RouteAnalysis
    w_route: RouteAnalysis
    branch: InferenceBranch
    competence_family_members: int = FINAL_COMPETENCE_FAMILY_MEMBERS
    direct_family_members: int = DIRECT_FAMILY_MEMBERS

    def direct(self, name: str) -> TwoSidedInterval:
        return next(item.interval for item in self.direct_items if item.name == name)


def _ordered_final(summaries: Iterable[FinalReplicateSummary]) -> tuple[FinalReplicateSummary, ...]:
    values = tuple(summaries)
    for value in values:
        value.validate()
    if len(values) != REPLICATE_COUNT or {value.replicate for value in values} != set(range(REPLICATE_COUNT)):
        raise InferenceContractError("final analyzer requires exact replicates 0 through 23")
    return tuple(sorted(values, key=lambda value: value.replicate))


def _controller_state(states: Sequence[PredicateState]) -> PredicateState:
    if all(state is PredicateState.PASS for state in states):
        return PredicateState.PASS
    if any(state is PredicateState.FAIL for state in states):
        return PredicateState.FAIL
    return PredicateState.UNRESOLVED


def _route(endpoint: str, items: Mapping[str, PredicateState]) -> RouteAnalysis:
    if any(state is PredicateState.FAIL for state in items.values()):
        state = RouteState.EXCLUDED
    elif items and all(value is PredicateState.PASS for value in items.values()):
        state = RouteState.PASS
    else:
        state = RouteState.UNRESOLVED
    return RouteAnalysis(endpoint=endpoint, state=state, item_states=tuple(items.items()))


def analyze_final_inference(
    summaries: Iterable[FinalReplicateSummary],
) -> FinalInferenceAnalysis:
    ordered = _ordered_final(summaries)
    controllers = {
        name: tuple(value.controller(name) for value in ordered) for name in CONTROLLERS
    }

    competence_items: list[CompetenceItem] = []
    competence_states: dict[str, PredicateState] = {}
    for controller in QUALIFICATION_CONTROLLERS:
        row_maps = [dict(value.competence) for value in controllers[controller]]
        states: list[PredicateState] = []
        for key in COMPETENCE_KEYS:
            interval = two_sided_interval(
                tuple(value[key] for value in row_maps),
                family_members=FINAL_COMPETENCE_FAMILY_MEMBERS,
            )
            threshold = 0.82 if key == "pooled" else 0.70
            state = higher_better_state(interval, threshold)
            competence_items.append(CompetenceItem(controller, key, threshold, interval, state))
            states.append(state)
        competence_states[controller] = _controller_state(states)
    if len(competence_items) != FINAL_COMPETENCE_FAMILY_MEMBERS:
        raise AssertionError("final competence family must contain exactly 15 intervals")

    direct_specs: list[tuple[str, str, str]] = []
    for endpoint in ("V", "W"):
        for control in CONTROL_CONTROLLERS:
            direct_specs.append((f"{endpoint}_TREAT_minus_{control}", endpoint, control))
    direct_specs.extend(
        (
            ("P_TREAT_minus_FOUNDATION", "P", "FOUNDATION"),
            ("E_TREAT_minus_FOUNDATION", "E", "FOUNDATION"),
        )
    )
    for endpoint in ("O", "G", "L", "F"):
        for control in CONTROL_CONTROLLERS:
            direct_specs.append((f"{endpoint}_TREAT_minus_{control}", endpoint, control))
    if len(direct_specs) != DIRECT_FAMILY_MEMBERS:
        raise AssertionError("direct family must contain exactly 26 intervals")
    direct_items: list[DirectItem] = []
    direct_map: dict[str, TwoSidedInterval] = {}
    for name, endpoint, control in direct_specs:
        differences = tuple(
            float(getattr(treatment, endpoint)) - float(getattr(comparator, endpoint))
            for treatment, comparator in zip(controllers["TREAT"], controllers[control])
        )
        interval = two_sided_interval(differences, family_members=DIRECT_FAMILY_MEMBERS)
        direct_items.append(DirectItem(name, interval))
        direct_map[name] = interval

    common: dict[str, PredicateState] = {
        f"competence/{controller}": competence_states[controller]
        for controller in QUALIFICATION_CONTROLLERS
    }
    common["P_noninferior_to_FOUNDATION"] = higher_better_state(
        direct_map["P_TREAT_minus_FOUNDATION"], -0.03
    )
    common["E_nonharm_to_FOUNDATION"] = upper_margin_state(
        direct_map["E_TREAT_minus_FOUNDATION"], 0.06
    )
    for endpoint in ("O", "G", "L", "F"):
        for control in CONTROL_CONTROLLERS:
            name = f"{endpoint}_TREAT_minus_{control}"
            common[f"{name}/nonharm"] = upper_margin_state(direct_map[name], 0.025)

    route_analyses: dict[str, RouteAnalysis] = {}
    for endpoint, other, margins in (("V", "W", V_MARGINS), ("W", "V", W_MARGINS)):
        items = dict(common)
        for control in CONTROL_CONTROLLERS:
            name = f"{endpoint}_TREAT_minus_{control}"
            items[f"{name}/superiority"] = higher_better_state(direct_map[name], margins[control])
        items[f"{other}_noninferior_to_FOUNDATION"] = higher_better_state(
            direct_map[f"{other}_TREAT_minus_FOUNDATION"], -0.015
        )
        route_analyses[endpoint] = _route(endpoint, items)

    branch = exhaustive_first_true_branch(
        InferenceFixture(
            conformance_valid=True,
            foundation_stage_complete=True,
            foundation_gate=GateOutcome.PASS,
            opportunity_stage_complete=True,
            opportunity_gate=GateOutcome.PASS,
            final_stage_complete=True,
            free_competence=competence_states["FREE"],
            set_competence=competence_states["SET"],
            v_route=route_analyses["V"].state,
            w_route=route_analyses["W"].state,
        )
    )
    return FinalInferenceAnalysis(
        competence_items=tuple(competence_items),
        competence_states=tuple(competence_states.items()),
        direct_items=tuple(direct_items),
        v_route=route_analyses["V"],
        w_route=route_analyses["W"],
        branch=branch,
    )


@dataclass(frozen=True, slots=True)
class CompletePathInference:
    branch: InferenceBranch
    evidence_valid: bool
    invalid_reasons: tuple[str, ...]
    foundation: FoundationCompetenceAnalysis | None = None
    opportunity_passed: bool | None = None
    final: FinalInferenceAnalysis | None = None
    partial_inspection_permitted: bool = False


def complete_realized_path_inference(
    *,
    foundation_summaries: Iterable[FoundationReplicateSummary] | None,
    opportunity_analysis: OpportunityGateAnalysis | None,
    final_summaries: Iterable[FinalReplicateSummary] | None,
    validity: Mapping[str, bool],
) -> CompletePathInference:
    """Return exactly one complete first-true disposition for the realized path."""

    invalid = [flag for flag in VALIDITY_FLAGS if validity.get(flag) is not True]
    if set(validity) != set(VALIDITY_FLAGS):
        invalid.append("validity_flag_inventory_mismatch")
    if invalid:
        return CompletePathInference(InferenceBranch.INVALID_EVIDENCE, False, tuple(invalid))
    if foundation_summaries is None:
        return CompletePathInference(
            InferenceBranch.INVALID_EVIDENCE, False, ("foundation_stage_incomplete",)
        )
    try:
        foundation = analyze_foundation_competence(foundation_summaries)
    except (InferenceContractError, EvaluationContractError, ValueError, TypeError, KeyError) as error:
        return CompletePathInference(InferenceBranch.INVALID_EVIDENCE, False, (str(error),))
    if foundation.gate is GateOutcome.NONPASS:
        return CompletePathInference(
            InferenceBranch.FOUNDATION_NOT_ESTABLISHED,
            True,
            (),
            foundation=foundation,
        )
    if opportunity_analysis is None or not isinstance(opportunity_analysis, OpportunityGateAnalysis):
        return CompletePathInference(
            InferenceBranch.INVALID_EVIDENCE, False, ("opportunity_stage_incomplete",)
        )
    if opportunity_analysis.passes is not True:
        return CompletePathInference(
            InferenceBranch.OPPORTUNITY_NOT_ESTABLISHED,
            True,
            (),
            foundation=foundation,
            opportunity_passed=False,
        )
    if final_summaries is None:
        return CompletePathInference(
            InferenceBranch.INVALID_EVIDENCE, False, ("final_stage_incomplete",)
        )
    try:
        final = analyze_final_inference(final_summaries)
    except (InferenceContractError, EvaluationContractError, ValueError, TypeError, KeyError) as error:
        return CompletePathInference(InferenceBranch.INVALID_EVIDENCE, False, (str(error),))
    return CompletePathInference(
        branch=final.branch,
        evidence_valid=True,
        invalid_reasons=(),
        foundation=foundation,
        opportunity_passed=True,
        final=final,
    )
