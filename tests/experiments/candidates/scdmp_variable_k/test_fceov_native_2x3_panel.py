from __future__ import annotations

from dataclasses import fields, replace
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    contracts,
    host_bridge,
    panel,
)


def _constant_tapes(panel_slice: panel.PanelSlice) -> tuple[panel.DisturbanceTape, ...]:
    return tuple(
        panel.DisturbanceTape(
            tape=index,
            eta_v=(0.003,) * 364,
            eta_y=(0.002,) * 364,
            eta_omega=(0.004,) * 364,
        )
        for index in range(panel_slice.start_tape, panel_slice.start_tape + panel_slice.tape_count)
    )


def _output(*, active: bool, terminal: bool, tick: int, safe: bool = False):
    return SimpleNamespace(
        advanced=tick != 0,
        active=active,
        terminal=terminal,
        ticks_advanced=min(tick, 13),
        tick=tick,
        observation=contracts.fixed_claim_state().observation(),
        hold_k=0 if tick == 0 else 13,
        next_k=13,
        safe_dock=safe,
        dock_tick=tick if safe else None,
        timeout=terminal and not safe and tick == 364,
        cable_overload=terminal and not safe and tick < 364,
        gantry_contact=False,
        attitude_loss=False,
        formation_loss=False,
        cumulative_reward=0.0,
        cumulative_energy=0.0,
        energy_ticks=tick,
        last_hold_reward_count=min(tick, 13),
        last_hold_rewards=(0.0,) * 13,
    )


class TwoHoldSession:
    def __init__(self, width: int) -> None:
        self.width = width
        self.initial = tuple(_output(active=True, terminal=False, tick=0) for _ in range(width))
        self.calls = []

    @property
    def active_lanes(self):
        return tuple(range(self.width))

    def renew(self, rows):
        self.calls.append(tuple(rows))
        if len(self.calls) == 1:
            return tuple(_output(active=True, terminal=False, tick=13) for _ in range(self.width))
        return tuple(_output(active=False, terminal=True, tick=26, safe=True) for _ in range(self.width))


class TieFoundation:
    def __init__(self) -> None:
        self.queries = 0
        self.validations = 0

    def validate_immutable(self) -> None:
        self.validations += 1

    def __call__(self, observations):
        self.queries += observations.shape[0]
        return torch.zeros((observations.shape[0], 18), dtype=torch.float32)


def _terminal_cells(panel_slice: panel.PanelSlice):
    return tuple(
        contracts.PanelCell(
            lane.tape, lane.graph, lane.action_name, lane.action_index,
            True, True, 26, (),
        )
        for lane in panel_slice.lanes
    )


def test_global_inventory_and_typed_slices_are_exact_562_by_2_by_3():
    inventory = panel.build_panel_inventory()
    slices = panel.build_panel_slices()

    assert len(inventory) == 562 * 2 * 3 == 3372
    assert [row.lane for row in inventory] == list(range(3372))
    assert panel.validate_tape_pairing(inventory) is True
    assert panel.validate_panel_slices(slices) is True
    assert len(slices) == 24
    assert tuple(row.width for row in slices) == (144,) * 23 + (60,)
    assert tuple(row.tape_count for row in slices) == (24,) * 23 + (10,)
    assert slices[-1].index == 23
    assert slices[-1].start_tape == 552
    assert [lane.tape for lane in slices[-1].lanes[:6]] == [552] * 6
    assert [lane.tape for lane in slices[-1].lanes[-6:]] == [561] * 6
    for tape in (0, 23, 24, 551, 552, 561):
        rows = [row for row in inventory if row.tape == tape]
        assert [(row.graph, row.action_name) for row in rows] == [
            (graph, action)
            for graph in ("HR", "RH")
            for action in ("COMMON", "A_HR", "A_RH")
        ]


def test_slice_inventory_validator_rejects_duplicate_missing_reordered_and_mutated_lanes():
    slices = list(panel.build_panel_slices())

    for drifted in (slices[:-1], slices + [slices[-1]], [*slices[:2], slices[0], *slices[3:]]):
        with pytest.raises(panel.PanelContractError, match="slice inventory"):
            panel.validate_panel_slices(drifted)

    lanes = list(slices[0].lanes)
    lanes[0], lanes[1] = lanes[1], lanes[0]
    with pytest.raises(panel.PanelContractError, match="bounds, lanes, or order"):
        panel.validate_slice_tape_pairing(replace(slices[0], lanes=tuple(lanes)))

    first = slices[0].lanes[0]
    malformed = replace(slices[0], lanes=(replace(first, lane=False), *slices[0].lanes[1:]))
    with pytest.raises(panel.PanelContractError, match="bounds, lanes, or order|indices"):
        panel.validate_slice_tape_pairing(malformed)


def test_native_resets_preserve_global_lane_order_for_full_and_short_slices():
    hr, rh = host_bridge.fixed_resets()
    for panel_slice in (panel.build_panel_slices()[0], panel.build_panel_slices()[-1]):
        resets = panel.build_native_resets(panel_slice)
        assert len(resets) == panel_slice.width
        assert all(
            reset == (hr if lane.graph == "HR" else rh)
            for lane, reset in zip(panel_slice.lanes, resets)
        )
    assert hr.k_initial == rh.k_initial == 13
    assert (hr.initial_v, hr.initial_y, hr.initial_phi) == (0.015, 0.0, 0.0)
    assert (rh.initial_v, rh.initial_y, rh.initial_phi) == (0.015, 0.0, 0.0)


def test_materialization_uses_global_tape_addresses_in_last_slice():
    assert tuple(field.name for field in fields(panel.TapeAddress)) == ("tape", "tick", "component")

    class RecordingSource:
        def __init__(self) -> None:
            self.calls = []

        def uniforms(self, domain, address, count):
            self.calls.append((domain, tuple(address), count))
            return (0.75,)

    source = RecordingSource()
    last = panel.build_panel_slices()[-1]
    tapes = panel.materialize_disturbance_tapes(
        source, start_tape=last.start_tape, tape_count=last.tape_count
    )

    assert [row.tape for row in tapes] == list(range(552, 562))
    assert len(source.calls) == 10 * 364 * 3
    assert {domain for domain, _, _ in source.calls} == {"assay-disturbance"}
    assert all(len(address) == 3 and count == 1 for _, address, count in source.calls)
    assert source.calls[0][1] == (552, 0, "eta_v")
    assert source.calls[-1][1] == (561, 363, "eta_omega")
    with pytest.raises(panel.PanelContractError, match="global inventory"):
        panel.materialize_disturbance_tapes(source, start_tape=552, tape_count=11)


@pytest.mark.parametrize("slice_index,expected_width", ((0, 144), (23, 60)))
def test_production_slice_executor_constructs_one_exact_native_batch(monkeypatch, slice_index, expected_width):
    captured = []

    class BoundBatch(TwoHoldSession):
        def __init__(self, resets):
            super().__init__(len(resets))
            captured.append(tuple(resets))
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

        def close(self):
            self.closed = True

    monkeypatch.setattr(panel, "NativeBatch", BoundBatch)
    panel_slice = panel.build_panel_slices()[slice_index]
    cells = panel.execute_native_panel_slice(
        TieFoundation(), _constant_tapes(panel_slice), panel_slice
    )

    assert captured == [panel.build_native_resets(panel_slice)]
    assert len(cells) == expected_width
    assert [cell.tape for cell in cells[:6]] == [panel_slice.start_tape] * 6
    assert [cell.tape for cell in cells[-6:]] == [panel_slice.start_tape + panel_slice.tape_count - 1] * 6
    assert "_test_only_execute_panel_session" not in panel.__all__


def test_real_native_preflight_accepts_width_144_and_width_60():
    slices = panel.build_panel_slices()
    assert panel.preflight_native_panel_slice(slices[0]) == 144
    assert panel.preflight_native_panel_slice(slices[-1]) == 60


def test_preflight_all_slices_opens_23_width_144_and_one_width_60(monkeypatch):
    captured = []

    class PreflightBatch:
        def __init__(self, resets):
            self.resets = tuple(resets)
            self.initial = tuple(_output(active=True, terminal=False, tick=0) for _ in resets)
            self.closed = False
            captured.append(self)

        def __enter__(self): return self
        def __exit__(self, *_): self.closed = True

    monkeypatch.setattr(panel, "NativeBatch", PreflightBatch)
    assert panel.preflight_native_panel_widths() == (144,) * 23 + (60,)
    assert [len(item.resets) for item in captured] == [144] * 23 + [60]
    assert all(item.closed for item in captured)

    class DriftedPreflightBatch(PreflightBatch):
        def __init__(self, resets):
            super().__init__(resets)
            self.initial[0].hold_k = 13

    monkeypatch.setattr(panel, "NativeBatch", DriftedPreflightBatch)
    with pytest.raises(panel.PanelContractError, match="reset state/counters"):
        panel.preflight_native_panel_slice(panel.build_panel_slices()[-1])


@pytest.mark.parametrize("slice_index", (0, 23))
def test_forced_first_hold_precedes_query_and_query_ceiling_scales_with_slice_width(slice_index):
    panel_slice = panel.build_panel_slices()[slice_index]
    session = TwoHoldSession(panel_slice.width)
    foundation = TieFoundation()

    cells = panel._test_only_execute_panel_session(
        session, foundation, _constant_tapes(panel_slice), panel_slice
    )

    assert len(session.calls) == 2
    assert [row.action for row in session.calls[0]] == [row.action_index for row in panel_slice.lanes]
    assert all(len(row.eta_v) == len(row.eta_y) == len(row.eta_omega) == 13 for row in session.calls[0])
    assert foundation.queries == panel_slice.width
    assert {row.action for row in session.calls[1]} == {0}
    assert foundation.validations == 2
    assert len(cells) == panel_slice.width and all(row.terminal for row in cells)


def test_absorption_during_first_hold_performs_no_foundation_query_on_short_slice():
    panel_slice = panel.build_panel_slices()[-1]

    class OneHoldSession(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            return tuple(_output(active=False, terminal=True, tick=7) for _ in range(self.width))

    session = OneHoldSession(panel_slice.width)
    foundation = TieFoundation()
    cells = panel._test_only_execute_panel_session(
        session, foundation, _constant_tapes(panel_slice), panel_slice
    )
    assert len(session.calls) == 1
    assert foundation.queries == 0
    assert all(row.terminal and not row.safe_dock for row in cells)


def test_slice_execution_rejects_wrong_tape_address_short_output_and_wrong_policy_batch():
    panel_slice = panel.build_panel_slices()[-1]
    tapes = list(_constant_tapes(panel_slice))
    tapes[0] = replace(tapes[0], tape=0)
    with pytest.raises(panel.PanelContractError, match="slice disturbance tape inventory"):
        panel._test_only_execute_panel_session(
            TwoHoldSession(60), TieFoundation(), tapes, panel_slice
        )

    class ShortOutput(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            return tuple(_output(active=False, terminal=True, tick=13) for _ in range(self.width - 1))

    with pytest.raises(panel.PanelContractError, match="width"):
        panel._test_only_execute_panel_session(
            ShortOutput(60), TieFoundation(), _constant_tapes(panel_slice), panel_slice
        )

    class WrongBatchFoundation(TieFoundation):
        def __call__(self, observations):
            self.queries += observations.shape[0]
            return torch.zeros((1, 18), dtype=torch.float32)

    with pytest.raises(panel.PanelContractError, match="batch"):
        panel._test_only_execute_panel_session(
            TwoHoldSession(60), WrongBatchFoundation(), _constant_tapes(panel_slice), panel_slice
        )


def test_global_aggregation_accepts_only_complete_ordered_terminal_3372_cells():
    slices = panel.build_panel_slices()
    completed = tuple(_terminal_cells(panel_slice) for panel_slice in slices)
    cells = panel.aggregate_panel_slices(completed)

    assert len(cells) == 3372
    assert panel.validate_complete_panel_cells(cells) is True

    with pytest.raises(panel.PanelContractError, match="slice count"):
        panel.aggregate_panel_slices(completed[:-1])
    with pytest.raises(panel.PanelContractError, match="order|identity|completeness"):
        panel.aggregate_panel_slices((*completed[:-1], completed[-1][:-1]))

    for drifted in (
        cells[:-1],
        (*cells[:-1], cells[-2]),
        (cells[1], cells[0], *cells[2:]),
        (replace(cells[0], terminal=False), *cells[1:]),
    ):
        with pytest.raises(panel.PanelContractError, match="order|identity|completeness|terminal"):
            panel.validate_complete_panel_cells(drifted)


def test_slice_artifact_validator_rejects_identity_endpoint_and_failure_tampering():
    panel_slice = panel.build_panel_slices()[-1]
    cells = _terminal_cells(panel_slice)
    assert panel.validate_panel_slice_cells(cells, panel_slice) is True

    identity_tampers = (
        cells[:-1],
        (*cells[:-1], cells[-2]),
        (cells[1], cells[0], *cells[2:]),
        (replace(cells[0], tape=0), *cells[1:]),
    )
    for drifted in identity_tampers:
        with pytest.raises(panel.PanelContractError, match="order|identity|completeness"):
            panel.validate_panel_slice_cells(drifted, panel_slice)

    endpoint_tampers = (
        replace(cells[0], terminal=False),
        replace(cells[0], safe_dock=1),
        replace(cells[0], dock_tick=None),
        replace(cells[0], dock_tick=365),
        replace(cells[0], failures=("cable_overload",)),
        replace(cells[0], safe_dock=False, dock_tick=26),
        replace(cells[0], safe_dock=False, dock_tick=None, failures=["cable_overload"]),
        replace(cells[0], safe_dock=False, dock_tick=None, failures=("cable_overload", "cable_overload")),
        replace(cells[0], safe_dock=False, dock_tick=None, failures=("unregistered",)),
    )
    for drifted_cell in endpoint_tampers:
        with pytest.raises(panel.PanelContractError, match="terminal|endpoint|failure"):
            panel.validate_panel_slice_cells((drifted_cell, *cells[1:]), panel_slice)


def test_full_mission_utility_ignores_rewards_loads_and_rate_diagnostics():
    assert panel.mission_utility(safe_dock=True, dock_tick=91) == 0.75
    assert panel.mission_utility(safe_dock=False, dock_tick=None) == 0.0
