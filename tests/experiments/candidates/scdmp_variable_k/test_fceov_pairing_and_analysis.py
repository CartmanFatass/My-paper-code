from __future__ import annotations

import inspect
from math import fsum, sqrt

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    analysis,
    contracts,
)


ACTION_INDEX = {"COMMON": 0, "A_HR": 10, "A_RH": 12}


def _cell(tape: int, graph: str, action: str, dock_tick: int) -> contracts.PanelCell:
    return contracts.PanelCell(
        tape=tape,
        graph=graph,
        action_name=action,
        action_index=ACTION_INDEX[action],
        terminal=True,
        safe_dock=True,
        dock_tick=dock_tick,
    )


def _nonlinear_inventory() -> tuple[contracts.PanelCell, ...]:
    rows = []
    for tape in range(24):
        # Each half has one zero matched/mismatched contrast.  Aggregate d_0m
        # and d_1m are both positive, distinguishing min(aggregate means) from
        # the incorrect mean(per-tape minima).
        ticks = {
            ("RH", "COMMON"): 282,
            ("RH", "A_RH"): 82 if tape < 12 else 182,
            ("RH", "A_HR"): 182,
            ("HR", "COMMON"): 282,
            ("HR", "A_HR"): 182 if tape < 12 else 82,
            ("HR", "A_RH"): 182,
        }
        for graph in ("HR", "RH"):
            for action in ("COMMON", "A_HR", "A_RH"):
                rows.append(_cell(tape, graph, action, ticks[graph, action]))
    return tuple(rows)


def test_complete_panel_freezes_exact_four_paired_contrasts_and_aggregate_i_va():
    result = analysis.analyze_complete_panel(_nonlinear_inventory())

    assert [row.name for row in result.bounds] == ["d_0m", "d_1m", "d_0c", "d_1c"]
    first, last = result.tape_contrasts[0], result.tape_contrasts[-1]
    assert (first.d_0m, first.d_1m, first.d_0c, first.d_1c) == pytest.approx(
        (100 / 364, 0.0, 200 / 364, 100 / 364)
    )
    assert (last.d_0m, last.d_1m, last.d_0c, last.d_1c) == pytest.approx(
        (0.0, 100 / 364, 100 / 364, 200 / 364)
    )
    mean_d0m = fsum(row.d_0m for row in result.tape_contrasts) / 24
    mean_d1m = fsum(row.d_1m for row in result.tape_contrasts) / 24
    mean_d0c = fsum(row.d_0c for row in result.tape_contrasts) / 24
    mean_d1c = fsum(row.d_1c for row in result.tape_contrasts) / 24
    assert result.interaction == pytest.approx(0.5 * (mean_d0m + mean_d1m))
    assert result.candidate_order_value == pytest.approx(
        min(0.5 * mean_d0m, 0.5 * mean_d1m, 0.5 * (mean_d0c + mean_d1c))
    )
    assert result.candidate_order_value == pytest.approx(25 / 364)
    assert result.disposition == contracts.Disposition.ESTABLISHED.value


def test_paired_student_t_uses_df23_bonferroni_quantile_and_float64_fsum():
    assert "alpha" not in inspect.signature(analysis.paired_t_lower_bound).parameters
    values = tuple(index / 100.0 for index in range(24))
    bound = analysis.paired_t_lower_bound(values, name="d_0m")

    mean = fsum(values) / 24
    variance = fsum((value - mean) ** 2 for value in values) / 23
    standard_error = sqrt(variance / 24)
    critical_df23_at_09875 = 2.397875064657109
    assert bound.mean == mean
    assert bound.standard_error == pytest.approx(standard_error, abs=1e-15)
    assert bound.lower == pytest.approx(
        mean - critical_df23_at_09875 * standard_error,
        abs=2e-13,
    )
    assert bound.zero_variance is False


def test_zero_variance_is_explicit_and_every_lower_bound_must_be_strictly_positive():
    positive = analysis.paired_t_lower_bound((0.125,) * 24, name="positive")
    boundary = analysis.paired_t_lower_bound((0.0,) * 24, name="boundary")
    assert (positive.mean, positive.standard_error, positive.lower, positive.zero_variance) == (
        0.125,
        0.0,
        0.125,
        True,
    )
    assert (boundary.lower, boundary.zero_variance) == (0.0, True)

    equal_cells = tuple(
        _cell(tape, graph, action, 182)
        for tape in range(24)
        for graph in ("HR", "RH")
        for action in ("COMMON", "A_HR", "A_RH")
    )
    result = analysis.analyze_complete_panel(equal_cells)
    assert all(row.lower == 0.0 and row.zero_variance for row in result.bounds)
    assert result.disposition == contracts.Disposition.CLOSED.value


def test_scientific_hold_counterexample_for_current_24_block_t_rule_is_exact():
    cells = tuple(
        _cell(
            tape,
            graph,
            action,
            1 if (graph, action) in (("HR", "A_HR"), ("RH", "A_RH")) else 2,
        )
        for tape in range(24)
        for graph in ("HR", "RH")
        for action in ("COMMON", "A_HR", "A_RH")
    )
    observed = analysis.analyze_complete_panel(cells)
    direct_float_contrast = (1.0 - 1.0 / 364.0) - (1.0 - 2.0 / 364.0)
    assert all(bound.zero_variance for bound in observed.bounds)
    assert all(bound.lower == direct_float_contrast for bound in observed.bounds)
    assert direct_float_contrast == pytest.approx(1.0 / 364.0, abs=1e-17)
    assert observed.disposition == contracts.Disposition.ESTABLISHED.value

    parent_mean = (127.0 / 128.0) * (1.0 / 364.0) + (1.0 / 128.0) * (-363.0 / 364.0)
    all_positive_probability = (127.0 / 128.0) ** 24
    assert parent_mean == pytest.approx(-59.0 / 11648.0, abs=1e-18)
    assert all_positive_probability == pytest.approx(0.8284, abs=5e-5)


def test_analysis_rejects_partial_nonterminal_duplicate_and_action_index_mismatch():
    rows = list(_nonlinear_inventory())
    with pytest.raises(analysis.AnalysisContractError, match="144 terminal"):
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
    with pytest.raises(analysis.AnalysisContractError, match="144 terminal"):
        analysis.analyze_complete_panel(rows)

    rows = list(_nonlinear_inventory())
    rows[1] = rows[0]
    with pytest.raises(analysis.AnalysisContractError, match="duplicate"):
        analysis.analyze_complete_panel(rows)

    rows = list(_nonlinear_inventory())
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

    rows = list(_nonlinear_inventory())
    row = rows[0]
    rows[0] = contracts.PanelCell(
        row.tape, row.graph, row.action_name, False, True, row.safe_dock, row.dock_tick
    )
    with pytest.raises(analysis.AnalysisContractError, match="action.*index|index.*action"):
        analysis.analyze_complete_panel(rows)
