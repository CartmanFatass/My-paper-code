import numpy as np
import pytest
from dataclasses import replace

from experiments.candidates.commitment_residual_triggered_options.host import (
    EventClass, Regime, ScenarioSpec, build_scenario_tape,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    Panel, RowKey, Split, assert_disjoint_panels,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    _protected_switch_boundary, _valid_event_window, canonical_tape,
    materialize_common_history_row,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    CalibrationTable, construct_packet_views,
)


def _forecast(_history: np.ndarray, _option: int, _k: int, _elapsed: int):
    return np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32)


def _host_at(time: int):
    from experiments.candidates.commitment_residual_triggered_options.host import ServiceRelayHost
    from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import scripted_decisions
    spec = ScenarioSpec(0, 321, Regime.K8, EventClass.NONE, 50, 0.25)
    host = ServiceRelayHost(build_scenario_tape(spec))
    while host.state.primitive_time < time:
        host.advance(scripted_decisions(host))
    return host


def test_exact_inherited_window_and_switch_protection_endpoints() -> None:
    assert not _valid_event_window(_host_at(53))
    assert _valid_event_window(_host_at(54))
    assert _valid_event_window(_host_at(70))
    assert not _valid_event_window(_host_at(71))
    assert _protected_switch_boundary(_host_at(119))
    assert not _protected_switch_boundary(_host_at(120))
    assert not _protected_switch_boundary(_host_at(136))
    assert _protected_switch_boundary(_host_at(137))


def test_materialized_row_is_complete_predecision_history_and_records_stable() -> None:
    spec = ScenarioSpec(7, 654, Regime.K8, EventClass.NONE, 50, 0.25)
    row = materialize_common_history_row(
        build_scenario_tape(spec), replicate=0, split=Split.TRAIN, forecast=_forecast,
    )
    assert row is not None
    assert row.history.shape == (row.key.primitive_time + 1, 42)
    assert row.elapsed_horizon in (4, 8, 12, 16)
    assert row.legal_mask[0] and np.isnan(row.g16[~row.legal_mask]).all()
    assert row.history_record[1] == row.history.shape
    assert row.label_record[1] == row.g16.shape
    assert row.tape_record == canonical_tape(build_scenario_tape(spec))
    views = construct_packet_views((row,), CalibrationTable(np.zeros((8, 1), dtype=np.float32)))
    assert views.raw_dataset.row_keys == views.true_residual_dataset.row_keys == (row.key.text,)
    assert row.history_record == row.history_record and row.label_record == row.label_record

    eval_row = replace(row, key=RowKey(0, Split.EVALUATION, "K8", 7, 60, 0))
    with pytest.raises(ValueError, match="leaked"):
        assert_disjoint_panels({
            Split.TRAIN: Panel(Split.TRAIN, (row,)),
            Split.EVALUATION: Panel(Split.EVALUATION, (eval_row,)),
        })


def test_canonical_tape_includes_initial_hot_lane() -> None:
    from experiments.candidates.commitment_residual_triggered_options.host import Lane
    tape = build_scenario_tape(ScenarioSpec(9, 777, Regime.K8, EventClass.NONE, 50, 0.25))
    flipped = replace(tape, initial_hot_lane=Lane.R if tape.initial_hot_lane is Lane.L else Lane.L)
    assert canonical_tape(tape) != canonical_tape(flipped)


def test_panel_row_fails_closed_on_invalid_action_factor_cell_and_illegal_label() -> None:
    row = materialize_common_history_row(
        build_scenario_tape(ScenarioSpec(11, 812, Regime.K8, EventClass.NONE, 50, 0.25)),
        replicate=0, split=Split.TRAIN, forecast=_forecast,
    )
    assert row is not None
    with pytest.raises(ValueError, match="logged scripted action"):
        replace(row, logged_action=-1)
    upper = np.array(row.cholesky, copy=True)
    upper[0, 1] = np.float32(1e-7)
    with pytest.raises(ValueError, match="lower triangular"):
        replace(row, cholesky=upper)
    with pytest.raises(ValueError, match="cost"):
        replace(row, cost=float("inf"))
    with pytest.raises(ValueError, match="replicate"):
        replace(row, key=replace(row.key, replicate=8))
    illegal = np.flatnonzero(~row.legal_mask)
    if illegal.size:
        malformed = np.array(row.g16, copy=True)
        malformed[int(illegal[0])] = np.inf
        with pytest.raises(ValueError, match="must be NaN"):
            replace(row, g16=malformed)
