from __future__ import annotations

from dataclasses import asdict, fields
import json
from math import exp, log

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    analysis,
    contracts,
)


ACTION_INDEX = {"COMMON": 0, "A_HR": 10, "A_RH": 12}
N = 562


def _numerators_with_sum(total: int) -> tuple[int, ...]:
    assert 0 <= total <= 363 * N
    quotient, remainder = divmod(total, N)
    return tuple(quotient + (index < remainder) for index in range(N))


def _cell(tape: int, graph: str, action: str, numerator: int) -> contracts.PanelCell:
    assert 0 <= numerator <= 363
    return contracts.PanelCell(
        tape=tape,
        graph=graph,
        action_name=action,
        action_index=ACTION_INDEX[action],
        terminal=True,
        safe_dock=True,
        dock_tick=364 - numerator,
    )


def _inventory_for_raw_sums(
    *, g_a_rh: int, g_a_hr: int, g_common: int
) -> tuple[contracts.PanelCell, ...]:
    """Build nonnegative matched numerators realizing the requested exact sums."""

    # g_A_RH uses d_1m; g_A_HR uses d_0m.  Zero mismatched utilities
    # leave COMMON's two baseline lanes to set its requested combined sum.
    common_baseline_sum = g_a_rh + g_a_hr - g_common
    assert common_baseline_sum >= 0
    hr_matched = _numerators_with_sum(g_a_rh)
    rh_matched = _numerators_with_sum(g_a_hr)
    common_values = _numerators_with_sum(common_baseline_sum)
    rows = []
    for tape in range(N):
        numerators = {
            ("RH", "COMMON"): common_values[tape],
            ("RH", "A_HR"): 0,
            ("RH", "A_RH"): rh_matched[tape],
            ("HR", "COMMON"): 0,
            ("HR", "A_HR"): hr_matched[tape],
            ("HR", "A_RH"): 0,
        }
        for graph in ("HR", "RH"):
            for action in ("COMMON", "A_HR", "A_RH"):
                rows.append(_cell(tape, graph, action, numerators[graph, action]))
    return tuple(rows)


def _passing_inventory() -> tuple[contracts.PanelCell, ...]:
    return _inventory_for_raw_sums(g_a_rh=21_046, g_a_hr=21_046, g_common=42_091)


def test_complete_panel_preserves_four_exact_tape_contrasts_and_three_gap_mapping():
    result = analysis.analyze_complete_panel(_passing_inventory())

    assert len(result.tape_contrasts) == N
    assert [row.name for row in result.gaps] == ["g_A_RH", "g_A_HR", "g_COMMON"]
    assert [row.raw_utility_numerator_sum for row in result.gaps] == [21_046, 21_046, 42_091]
    first = result.tape_contrasts[0]
    assert first.d_0m_numerator - first.d_0c_numerator == 1
    assert first.d_1m_numerator == first.d_1c_numerator
    assert first.d_0m == first.d_0m_numerator / 364
    assert first.d_1m == first.d_1m_numerator / 364
    assert [row.raw_gap_mean for row in result.gaps] == pytest.approx([
        21_046 / (2 * 364 * N),
        21_046 / (2 * 364 * N),
        42_091 / (2 * 364 * N),
    ])


def test_exact_integer_first_passing_boundaries_establish_only_the_joint_claim():
    result = analysis.analyze_complete_panel(_passing_inventory())

    assert result.joint_claim_established is True
    assert result.disposition == contracts.Disposition.ESTABLISHED.value
    assert result.p_iut == max(row.p_value_upper for row in result.gaps)
    assert result.p_iut < 0.05
    assert result.l_theta > 0.0
    assert [row.first_passing_raw_sum for row in result.gaps] == [21_046, 21_046, 42_091]
    assert all(row.component_test_passed for row in result.gaps)


@pytest.mark.parametrize(
    ("g_a_rh", "g_a_hr", "g_common"),
    (
        (21_045, 21_046, 42_091),
        (21_046, 21_045, 42_091),
        (21_046, 21_046, 42_090),
    ),
)
def test_preceding_integer_in_each_component_fails_whole_bundle(
    g_a_rh: int, g_a_hr: int, g_common: int
):
    result = analysis.analyze_complete_panel(
        _inventory_for_raw_sums(g_a_rh=g_a_rh, g_a_hr=g_a_hr, g_common=g_common)
    )

    assert result.joint_claim_established is False
    assert result.disposition == contracts.Disposition.CLOSED.value
    assert result.p_iut >= 0.05
    assert result.l_theta <= 0.0


def test_heterogeneous_support_joint_lower_is_normalized_before_taking_minimum():
    result = analysis.analyze_complete_panel(
        _inventory_for_raw_sums(g_a_rh=25_000, g_a_hr=30_000, g_common=46_500)
    )
    normalized_lowers = tuple(
        analysis.invert_marginal_lower(row.normalized_mean, sample_size=N) - 0.5
        for row in result.gaps
    )
    assert normalized_lowers.index(min(normalized_lowers)) == 2  # g_COMMON
    assert result.l_theta == pytest.approx(normalized_lowers[2], abs=1e-15)

    raw_scale_lowers = (
        normalized_lowers[0] * 363 / 364,
        normalized_lowers[1] * 363 / 364,
        normalized_lowers[2] * 2 * 363 / 364,
    )
    assert raw_scale_lowers.index(min(raw_scale_lowers)) == 0  # g_A_RH

    payload = json.loads(json.dumps(asdict(result)))
    assert set(payload) == {
        "disposition", "joint_claim_established", "p_iut", "l_theta",
        "gaps", "tape_contrasts", "cell_means",
    }
    assert all("marginal" not in key and "lower" not in key for gap in payload["gaps"] for key in gap)
    assert "minimum_raw_gap_mean" not in payload
    assert "joint_value_raw_lower" not in payload


def test_iut_is_max_component_p_and_components_have_no_independent_claim_field():
    result = analysis.analyze_complete_panel(
        _inventory_for_raw_sums(g_a_rh=21_046, g_a_hr=0, g_common=21_046)
    )

    assert result.p_iut == max(row.p_value_upper for row in result.gaps)
    assert result.joint_claim_established is False
    assert result.disposition == contracts.Disposition.CLOSED.value
    component_fields = {field.name for field in fields(analysis.GapEvidence)}
    assert "component_test_passed" in component_fields
    assert component_fields.isdisjoint({"claim_established", "standalone_claim", "disposition"})
    assert {field.name for field in fields(analysis.PanelAnalysis)} & {
        "joint_claim_established",
        "disposition",
    } == {"joint_claim_established", "disposition"}


def test_kl_constants_planning_guarantee_and_audit_lower_inversion_are_frozen():
    assert analysis.INFERENCE_SAMPLE_SIZE == 562
    assert analysis.EXPECTED_CELL_COUNT == 3372
    assert analysis.CRITICAL_NORMALIZED_MEAN == 0.551580065745296
    assert analysis.LARGEST_FAILING_NORMALIZED_MEAN == 0.551579365312785
    assert analysis.PLANNING_JOINT_POWER_LOWER_BOUND == 0.801021247429385
    assert analysis.N561_PLANNING_JOINT_POWER_LOWER_BOUND == 0.799048262648854
    assert 562 * analysis.binary_kl_from_half(analysis.CRITICAL_NORMALIZED_MEAN) == pytest.approx(
        log(20), abs=1e-13
    )
    log_stat, p_value = analysis.bounded_chernoff_p_value(
        analysis.CRITICAL_NORMALIZED_MEAN, sample_size=562
    )
    assert p_value == pytest.approx(exp(-log_stat), abs=1e-16)
    observed = 0.6
    marginal = analysis.invert_marginal_lower(observed, sample_size=562)
    assert marginal < observed
    assert 562 * analysis.binary_kl(observed, marginal) == pytest.approx(log(20), abs=1e-10)


def test_historical_all_positive_dyadic_counterexample_does_not_pass_v3():
    # On this event every original contrast is +1/364.  The historical
    # zero-variance t rule passed it; the frozen finite-sample IUT must not.
    result = analysis.analyze_complete_panel(
        _inventory_for_raw_sums(g_a_rh=N, g_a_hr=N, g_common=2 * N)
    )

    assert all(row.d_0m_numerator == 1 for row in result.tape_contrasts)
    assert all(row.d_1m_numerator == 1 for row in result.tape_contrasts)
    assert result.joint_claim_established is False
    assert result.disposition == contracts.Disposition.CLOSED.value
    assert result.p_iut > 0.05


def test_analysis_rejects_partial_nonterminal_duplicate_and_action_index_mismatch():
    rows = list(_passing_inventory())
    with pytest.raises(analysis.AnalysisContractError, match="3372 terminal"):
        analysis.analyze_complete_panel(rows[:-1])

    first = rows[0]
    rows[0] = contracts.PanelCell(
        first.tape,
        first.graph,
        first.action_name,
        first.action_index,
        False,
        False,
        None,
    )
    with pytest.raises(analysis.AnalysisContractError, match="3372 terminal"):
        analysis.analyze_complete_panel(rows)

    rows = list(_passing_inventory())
    rows[1] = rows[0]
    with pytest.raises(analysis.AnalysisContractError, match="duplicate"):
        analysis.analyze_complete_panel(rows)

    rows = list(_passing_inventory())
    row = rows[0]
    rows[0] = contracts.PanelCell(
        row.tape,
        row.graph,
        row.action_name,
        17,
        row.terminal,
        row.safe_dock,
        row.dock_tick,
    )
    with pytest.raises(analysis.AnalysisContractError, match="action.*index|index.*action"):
        analysis.analyze_complete_panel(rows)


def test_joint_branch_source_uses_integer_sums_not_utility_floats():
    result = analysis.analyze_complete_panel(_passing_inventory())

    assert all(isinstance(row.raw_utility_numerator_sum, int) for row in result.gaps)
    # The exact first-passing raw grid is above the continuous critical point;
    # the previous integer is below it for both range lengths.
    assert 0.5 + 21_045 / (2 * 363 * N) == analysis.LARGEST_FAILING_NORMALIZED_MEAN
    assert 0.5 + 42_090 / (4 * 363 * N) == analysis.LARGEST_FAILING_NORMALIZED_MEAN
    assert result.joint_claim_established


def test_support_violation_and_integer_log_disagreement_are_invalid(monkeypatch):
    rows = list(_passing_inventory())
    row = rows[0]
    rows[0] = contracts.PanelCell(
        row.tape,
        row.graph,
        row.action_name,
        row.action_index,
        True,
        True,
        0,
    )
    with pytest.raises(analysis.AnalysisContractError, match="invalid dock tick"):
        analysis.analyze_complete_panel(rows)

    monkeypatch.setattr(
        analysis,
        "bounded_chernoff_p_value",
        lambda normalized_mean, *, sample_size: (0.0, 1.0),
    )
    with pytest.raises(analysis.AnalysisContractError, match="integer-grid, log-space"):
        analysis.analyze_complete_panel(_passing_inventory())


def test_ambiguous_direct_log_boundary_is_invalid(monkeypatch):
    monkeypatch.setattr(
        analysis,
        "bounded_chernoff_p_value",
        lambda normalized_mean, *, sample_size: (log(20), 0.05),
    )
    with pytest.raises(analysis.AnalysisContractError, match="ambiguous"):
        analysis.analyze_complete_panel(_passing_inventory())


def test_joint_iut_p_value_disagreement_fails_closed(monkeypatch):
    def inconsistent_gap(name: str, raw_sum: int) -> analysis.GapEvidence:
        return analysis.GapEvidence(
            name=name,
            raw_utility_numerator_sum=raw_sum,
            raw_gap_mean=1.0,
            normalized_mean=0.6,
            log_statistic=4.0,
            p_value_upper=1.0,
            first_passing_raw_sum=1,
            component_test_passed=True,
        )

    monkeypatch.setattr(analysis, "_gap_evidence", inconsistent_gap)
    with pytest.raises(analysis.AnalysisContractError, match="IUT p-value"):
        analysis.analyze_complete_panel(_passing_inventory())
