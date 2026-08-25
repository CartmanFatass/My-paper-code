"""Deterministic TEST_ONLY contract fixtures; no empirical activity exists here."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.evaluation import (
    COMPETENCE_REGIMES,
    CONTROLLERS,
    FAILURE_FIELDS,
    GRAPH_ORDERS,
    REGIMES,
    ControllerReplicateSummary,
    EpisodeEndpoint,
    EvaluationContractError,
    EvaluationScenario,
    FinalReplicateSummary,
    FoundationReplicateSummary,
    aggregate_final_replicate,
    aggregate_foundation_replicate,
    deterministic_lexicographic_argmax,
    validate_complete_scenarios,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.inference import (
    COMPETENCE_KEYS,
    DIRECT_FAMILY_MEMBERS,
    FINAL_COMPETENCE_FAMILY_MEMBERS,
    FOUNDATION_SAFE_KEYS,
    VALIDITY_FLAGS,
    analyze_final_inference,
    analyze_foundation_competence,
    complete_realized_path_inference,
    higher_better_state,
    two_sided_interval,
    upper_margin_state,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.lifecycle import (
    GateOutcome,
    InferenceBranch,
    PredicateState,
    RouteState,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.opportunity import (
    OneSidedLowerBound,
    OpportunityGateAnalysis,
)


def _scenarios() -> tuple[EvaluationScenario, ...]:
    rows: list[EvaluationScenario] = []
    for regime in REGIMES:
        for index in range(120):
            if regime in ("7-to-13", "13-to-7"):
                graph_order, switch_tick = (
                    (("HR", 91), ("HR", 273), ("RH", 91), ("RH", 273))[index // 30]
                )
            else:
                graph_order, switch_tick = ("HR" if index < 60 else "RH"), 0
            digest = hashlib.sha256(f"TEST_ONLY:{regime}:{index}".encode("ascii")).hexdigest()
            rows.append(EvaluationScenario(regime, index, graph_order, switch_tick, digest))
    return tuple(rows)


def _endpoint(controller: str, scenario: EvaluationScenario) -> EpisodeEndpoint:
    return EpisodeEndpoint(
        replicate=0,
        controller=controller,
        scenario=scenario,
        safe_dock=True,
        timeout=False,
        cable_overload=False,
        gantry_contact=False,
        attitude_loss=False,
        formation_loss=False,
        dock_tick=100,
        active_energy_sum=10.0,
        active_ticks=50,
    )


def _foundation_summary(replicate: int, *, safe: float = 0.90, failure: float = 0.01) -> FoundationReplicateSummary:
    return FoundationReplicateSummary(
        replicate=replicate,
        safe_cells=tuple((key, safe) for key in FOUNDATION_SAFE_KEYS),
        pooled_safe=safe,
        worst_failures=tuple((key, failure) for key in FAILURE_FIELDS),
    )


def _controller_summary(
    controller: str,
    *,
    competence: float = 0.90,
    pooled: float | None = None,
    V: float,
    W: float,
    P: float = 0.90,
    E: float = 0.30,
    failure: float = 0.01,
) -> ControllerReplicateSummary:
    pooled = competence if pooled is None else pooled
    competence_rows = tuple(
        (key, pooled if key == "pooled" else competence) for key in COMPETENCE_KEYS
    )
    return ControllerReplicateSummary(
        controller=controller,
        competence=competence_rows,
        V=V,
        W=W,
        P=P,
        T=20.0,
        E=E,
        O=failure,
        G=failure,
        L=failure,
        F=failure,
    )


def _final_summary(replicate: int, *, treatment_low: bool = False, free_boundary: bool = False) -> FinalReplicateSummary:
    controls = {
        "FOUNDATION": (0.80, 0.75),
        "FREE": (0.82, 0.76),
        "REVERSED": (0.81, 0.75),
        "SET": (0.81, 0.75),
    }
    treatment = (0.50, 0.45) if treatment_low else (0.90, 0.85)
    rows = [
        _controller_summary("FOUNDATION", V=controls["FOUNDATION"][0], W=controls["FOUNDATION"][1])
    ]
    rows.append(_controller_summary("TREAT", V=treatment[0], W=treatment[1]))
    rows.append(
        _controller_summary(
            "FREE",
            competence=0.70 if free_boundary else 0.90,
            pooled=0.82 if free_boundary else 0.90,
            V=controls["FREE"][0],
            W=controls["FREE"][1],
        )
    )
    rows.append(_controller_summary("REVERSED", V=controls["REVERSED"][0], W=controls["REVERSED"][1]))
    rows.append(_controller_summary("SET", V=controls["SET"][0], W=controls["SET"][1]))
    return FinalReplicateSummary(replicate=replicate, controllers=tuple(rows))


def _opportunity(passes: bool) -> OpportunityGateAnalysis:
    def bound(value: float) -> OneSidedLowerBound:
        return OneSidedLowerBound(value, value, 0.0, 0.0)

    return OpportunityGateAnalysis(bound(0.30), bound(0.04), bound(0.08), passes)


def _validity() -> dict[str, bool]:
    return {key: True for key in VALIDITY_FLAGS}


def test_scenario_and_endpoint_inventories_are_exact_and_complete_only() -> None:
    scenarios = validate_complete_scenarios(_scenarios())
    assert len(scenarios) == 720
    foundation_rows = tuple(_endpoint("FOUNDATION", scenario) for scenario in scenarios)
    foundation = aggregate_foundation_replicate(foundation_rows, replicate=0)
    assert foundation.episode_count == 720
    assert len(foundation.safe_cells) == 12
    assert foundation.pooled_safe == 1.0
    assert dict(foundation.worst_failures) == {field: 0.0 for field in FAILURE_FIELDS}

    final_rows = tuple(
        _endpoint(controller, scenario)
        for controller in CONTROLLERS
        for scenario in scenarios
    )
    final = aggregate_final_replicate(final_rows, replicate=0)
    assert final.episode_count == 3_600
    assert {row.controller for row in final.controllers} == set(CONTROLLERS)
    for row in final.controllers:
        assert (row.V, row.W, row.P, row.T, row.E) == pytest.approx(
            (1.0 - 100 / 364.0, 1.0 - 100 / 364.0, 1.0, 10.0, 0.2)
        )

    with pytest.raises(EvaluationContractError, match="exactly 3600"):
        aggregate_final_replicate(final_rows[:-1], replicate=0)
    mismatched = replace(final_rows[-1], scenario=replace(final_rows[-1].scenario, scenario_digest="f" * 64))
    with pytest.raises(EvaluationContractError, match="not exactly paired"):
        aggregate_final_replicate(final_rows[:-1] + (mismatched,), replicate=0)


def test_argmax_and_terminal_contracts_fail_closed() -> None:
    assert deterministic_lexicographic_argmax((1.0, 2.0, 2.0) + (0.0,) * 15) == 1
    with pytest.raises(EvaluationContractError, match="18 finite"):
        deterministic_lexicographic_argmax((0.0,) * 17 + (float("nan"),))
    scenario = _scenarios()[0]
    with pytest.raises(EvaluationContractError, match="exactly one"):
        replace(_endpoint("FOUNDATION", scenario), timeout=True).validate()
    with pytest.raises(EvaluationContractError, match="post-absorption"):
        replace(_endpoint("FOUNDATION", scenario), post_absorption_policy_queries=1).validate()


def test_foundation_family_has_17_one_sided_members_and_strict_gate() -> None:
    passed = analyze_foundation_competence(_foundation_summary(i) for i in range(24))
    assert passed.family_members == 17
    assert len(passed.safe_lower_bounds) == 12
    assert len(passed.failure_upper_bounds) == 4
    assert passed.gate is GateOutcome.PASS

    cell_contact = analyze_foundation_competence(
        _foundation_summary(i, safe=0.72) for i in range(24)
    )
    failure_contact = analyze_foundation_competence(
        _foundation_summary(i, safe=0.90, failure=0.10) for i in range(24)
    )
    pooled_contact = analyze_foundation_competence(
        replace(_foundation_summary(i), pooled_safe=0.84) for i in range(24)
    )
    assert cell_contact.gate is GateOutcome.NONPASS
    assert failure_contact.gate is GateOutcome.NONPASS
    assert pooled_contact.gate is GateOutcome.NONPASS


def test_final_families_routes_and_boundaries_are_exact() -> None:
    retained = analyze_final_inference(_final_summary(i) for i in range(24))
    assert retained.competence_family_members == FINAL_COMPETENCE_FAMILY_MEMBERS == 15
    assert retained.direct_family_members == DIRECT_FAMILY_MEMBERS == 26
    assert len(retained.competence_items) == 15
    assert len(retained.direct_items) == 26
    assert retained.v_route.state is RouteState.PASS
    assert retained.w_route.state is RouteState.PASS
    assert retained.branch is InferenceBranch.RETAIN

    declined = analyze_final_inference(_final_summary(i, treatment_low=True) for i in range(24))
    assert declined.v_route.state is RouteState.EXCLUDED
    assert declined.w_route.state is RouteState.EXCLUDED
    assert declined.branch is InferenceBranch.DECLINE

    nonidentified = analyze_final_inference(
        _final_summary(i, treatment_low=True, free_boundary=True) for i in range(24)
    )
    assert dict(nonidentified.competence_states)["FREE"] is PredicateState.FAIL
    assert nonidentified.branch is InferenceBranch.NONIDENTIFIED

    contact = two_sided_interval((0.025,) * 24, family_members=26)
    assert higher_better_state(contact, 0.025) is PredicateState.FAIL
    assert upper_margin_state(contact, 0.025) is PredicateState.FAIL


def test_complete_realized_path_map_requires_only_stages_on_realized_path() -> None:
    foundation_nonpass = complete_realized_path_inference(
        foundation_summaries=(_foundation_summary(i, safe=0.72) for i in range(24)),
        opportunity_analysis=None,
        final_summaries=None,
        validity=_validity(),
    )
    assert foundation_nonpass.branch is InferenceBranch.FOUNDATION_NOT_ESTABLISHED
    assert foundation_nonpass.evidence_valid
    assert foundation_nonpass.opportunity_passed is None

    opportunity_nonpass = complete_realized_path_inference(
        foundation_summaries=(_foundation_summary(i) for i in range(24)),
        opportunity_analysis=_opportunity(False),
        final_summaries=None,
        validity=_validity(),
    )
    assert opportunity_nonpass.branch is InferenceBranch.OPPORTUNITY_NOT_ESTABLISHED
    assert opportunity_nonpass.final is None

    complete = complete_realized_path_inference(
        foundation_summaries=(_foundation_summary(i) for i in range(24)),
        opportunity_analysis=_opportunity(True),
        final_summaries=(_final_summary(i) for i in range(24)),
        validity=_validity(),
    )
    assert complete.branch is InferenceBranch.RETAIN
    assert complete.evidence_valid and complete.final is not None
    assert not complete.partial_inspection_permitted

    invalid_validity = _validity()
    invalid_validity["pairing_conformance"] = False
    invalid = complete_realized_path_inference(
        foundation_summaries=None,
        opportunity_analysis=None,
        final_summaries=None,
        validity=invalid_validity,
    )
    assert invalid.branch is InferenceBranch.INVALID_EVIDENCE
    assert not invalid.evidence_valid
    assert invalid.foundation is None and invalid.final is None
