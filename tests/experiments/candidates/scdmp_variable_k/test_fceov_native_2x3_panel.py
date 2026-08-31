from __future__ import annotations

from dataclasses import fields
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    contracts,
    host_bridge,
    panel,
)


def _constant_tape(index: int) -> panel.DisturbanceTape:
    return panel.DisturbanceTape(
        tape=index,
        eta_v=(0.003,) * 364,
        eta_y=(0.002,) * 364,
        eta_omega=(0.004,) * 364,
    )


def _output(*, active: bool, terminal: bool, tick: int, safe: bool = False):
    return SimpleNamespace(
        active=active,
        terminal=terminal,
        tick=tick,
        observation=contracts.fixed_claim_state().observation(),
        hold_k=13,
        safe_dock=safe,
        dock_tick=tick if safe else None,
        cable_overload=False,
        gantry_contact=False,
        attitude_loss=False,
        formation_loss=False,
    )


class TwoHoldSession:
    def __init__(self) -> None:
        self.initial = tuple(_output(active=True, terminal=False, tick=0) for _ in range(144))
        self.calls = []

    @property
    def active_lanes(self):
        return tuple(range(144))

    def renew(self, rows):
        self.calls.append(tuple(rows))
        if len(self.calls) == 1:
            return tuple(_output(active=True, terminal=False, tick=13) for _ in range(144))
        return tuple(_output(active=False, terminal=True, tick=26, safe=True) for _ in range(144))


class TieFoundation:
    def __init__(self) -> None:
        self.queries = 0
        self.validations = 0

    def validate_immutable(self) -> None:
        self.validations += 1

    def __call__(self, observations):
        self.queries += observations.shape[0]
        return torch.zeros((observations.shape[0], 18), dtype=torch.float32)


def test_panel_inventory_is_one_width_144_session_with_each_tape_in_all_six_cells():
    inventory = panel.build_panel_inventory()

    assert len(inventory) == 24 * 2 * 3 == 144
    assert [row.lane for row in inventory] == list(range(144))
    assert panel.validate_tape_pairing(inventory) is True
    for tape in range(24):
        rows = [row for row in inventory if row.tape == tape]
        assert {(row.graph, row.action_name) for row in rows} == {
            (graph, action)
            for graph in ("HR", "RH")
            for action in ("COMMON", "A_HR", "A_RH")
        }

    drifted = list(inventory)
    first = drifted[0]
    drifted[0] = panel.PanelLane(False, first.tape, first.graph, first.action_name, first.action_index)
    with pytest.raises(panel.PanelContractError, match="indices"):
        panel.validate_tape_pairing(drifted)

    resets = panel.build_native_resets(inventory)
    hr, rh = host_bridge.fixed_resets()
    assert len(resets) == 144
    assert all(reset == (hr if lane.graph == "HR" else rh) for lane, reset in zip(inventory, resets))
    assert hr.k_initial == rh.k_initial == 13
    assert (hr.initial_v, hr.initial_y, hr.initial_phi) == (0.015, 0.0, 0.0)
    assert (rh.initial_v, rh.initial_y, rh.initial_phi) == (0.015, 0.0, 0.0)


def test_production_executor_constructs_and_owns_exact_native_reset_order(monkeypatch):
    captured = []

    class BoundBatch(TwoHoldSession):
        def __init__(self, resets):
            super().__init__()
            captured.append(tuple(resets))
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

        def close(self):
            self.closed = True

    monkeypatch.setattr(panel, "NativeBatch", BoundBatch)
    foundation = TieFoundation()
    cells = panel.execute_native_panel(
        foundation,
        tuple(_constant_tape(index) for index in range(24)),
    )

    assert captured == [panel.build_native_resets()]
    assert len(cells) == 144
    assert "_test_only_execute_panel_session" not in panel.__all__

def test_disturbance_addresses_contain_only_tape_tick_component_and_are_shared():
    assert tuple(field.name for field in fields(panel.TapeAddress)) == ("tape", "tick", "component")

    class RecordingSource:
        def __init__(self) -> None:
            self.calls = []

        def uniforms(self, domain, address, count):
            self.calls.append((domain, tuple(address), count))
            return (0.75,)

    source = RecordingSource()
    tapes = panel.materialize_disturbance_tapes(source)

    assert len(tapes) == 24
    assert len(source.calls) == 24 * 364 * 3
    assert {domain for domain, _, _ in source.calls} == {"assay-disturbance"}
    assert all(len(address) == 3 and count == 1 for _, address, count in source.calls)
    assert source.calls[0][1] == (0, 0, "eta_v")
    assert source.calls[-1][1] == (23, 363, "eta_omega")


def test_forced_first_hold_precedes_any_foundation_query_then_uses_lexicographic_argmax():
    inventory = panel.build_panel_inventory()
    session = TwoHoldSession()
    foundation = TieFoundation()

    cells = panel._test_only_execute_panel_session(
        session,
        foundation,
        tuple(_constant_tape(index) for index in range(24)),
    )

    assert len(session.calls) == 2
    assert [row.action for row in session.calls[0]] == [row.action_index for row in inventory]
    assert all(len(row.eta_v) == len(row.eta_y) == len(row.eta_omega) == 13 for row in session.calls[0])
    assert foundation.queries == 144  # only after the forced 13-tick hold
    assert {row.action for row in session.calls[1]} == {0}  # all-logit tie -> catalogue index 0
    assert foundation.validations == 2
    assert len(cells) == 144 and all(row.terminal for row in cells)


def test_absorption_during_first_hold_performs_no_foundation_query():
    class OneHoldSession(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            return tuple(_output(active=False, terminal=True, tick=7) for _ in range(144))

    session = OneHoldSession()
    foundation = TieFoundation()
    cells = panel._test_only_execute_panel_session(
        session,
        foundation,
        tuple(_constant_tape(index) for index in range(24)),
    )

    assert len(session.calls) == 1
    assert foundation.queries == 0
    assert all(row.terminal and not row.safe_dock for row in cells)


def test_panel_rejects_wrong_but_aliased_state_short_native_output_and_wrong_policy_batch():
    class WrongAlias(TwoHoldSession):
        def __init__(self):
            super().__init__()
            wrong = _output(active=True, terminal=False, tick=0)
            wrong.observation = (0.0,) * 18
            self.initial = (wrong,) * 144

    with pytest.raises(panel.PanelContractError, match="fixed state"):
        panel._test_only_execute_panel_session(
            WrongAlias(), TieFoundation(), tuple(_constant_tape(index) for index in range(24))
        )

    class ShortOutput(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            return tuple(_output(active=False, terminal=True, tick=13) for _ in range(143))

    with pytest.raises(panel.PanelContractError, match="144|width"):
        panel._test_only_execute_panel_session(
            ShortOutput(), TieFoundation(), tuple(_constant_tape(index) for index in range(24))
        )

    class WrongBatchFoundation(TieFoundation):
        def __init__(self, rows):
            super().__init__()
            self.rows = rows

        def __call__(self, observations):
            self.queries += observations.shape[0]
            return torch.zeros((self.rows, 18), dtype=torch.float32)

    for rows in (1, 145):
        with pytest.raises(panel.PanelContractError, match="batch|policy"):
            panel._test_only_execute_panel_session(
                TwoHoldSession(),
                WrongBatchFoundation(rows),
                tuple(_constant_tape(index) for index in range(24)),
            )


def test_panel_rejects_query_ceiling_and_terminal_lane_reactivation():
    class TooManyQueries(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            if len(self.calls) <= 28:
                return tuple(
                    _output(active=True, terminal=False, tick=min(13 * len(self.calls), 363))
                    for _ in range(144)
                )
            return tuple(_output(active=False, terminal=True, tick=364) for _ in range(144))

    # A 28th post-intervention query is already impossible under the exact
    # 364-tick/fixed-13 clock, so either the clock guard or the explicit work
    # ceiling must stop this malformed session before another query.
    with pytest.raises(panel.PanelContractError, match="query ceiling|fixed-13"):
        panel._test_only_execute_panel_session(
            TooManyQueries(), TieFoundation(), tuple(_constant_tape(index) for index in range(24))
        )

    class Reactivating(TwoHoldSession):
        def renew(self, rows):
            self.calls.append(tuple(rows))
            if len(self.calls) == 1:
                return tuple(
                    _output(active=index >= 72, terminal=index < 72, tick=13)
                    for index in range(144)
                )
            return tuple(_output(active=True, terminal=False, tick=26) for _ in range(144))

    with pytest.raises(panel.PanelContractError, match="reactivat|terminal"):
        panel._test_only_execute_panel_session(
            Reactivating(), TieFoundation(), tuple(_constant_tape(index) for index in range(24))
        )


def test_full_mission_utility_ignores_rewards_loads_and_rate_diagnostics():
    assert panel.mission_utility(safe_dock=True, dock_tick=91) == 0.75
    assert panel.mission_utility(safe_dock=False, dock_tick=None) == 0.0
