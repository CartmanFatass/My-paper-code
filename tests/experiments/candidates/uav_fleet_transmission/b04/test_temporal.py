"""Synthetic arithmetic/clock checks; no native or complete real-policy runs."""
from copy import deepcopy
import json

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b02.controller import Program, COUNT_KEYS, empty_counts
from experiments.candidates.uav_fleet_transmission.b03 import controller as original
from experiments.candidates.uav_fleet_transmission.b04 import controller as temporal, option, surrogate
from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state, predict_next, _Scores


def report(t):
    state = np.zeros(133, dtype=np.float32)
    state[:24].reshape(8, 3)[:, :2] = [.123456789, .87654321]
    state[24:32] = 1
    state[32:132] = np.linspace(0, 1, 100, dtype=np.float32)
    state[-1] = t/500
    return state


def history(t):
    c = OrdinaryController(8)
    c.positions, c.users = decode_public_state(report(t), 8)
    c.next_t = t
    return c


def plan(t=40, site=0):
    commands = np.zeros((10, 8, 3), np.float32)
    commands[0, 7, 0] = 1
    positions, _ = decode_public_state(report(t), 8)
    destination = predict_next(positions, commands[0])
    return dict(start_t=t, initiated=True, member=7, site=site, duration=10, arrival_t=t+10,
        commands=commands.tolist(), predicted_destination=destination.tolist(), predicted_mask=128,
        selected=dict(path=30., member=7, site=site, duration=10), predicted_total_J=-1.,
        predicted_total_served=0, stay_total_J=0., stay_total_served=0,
        counts=dict.fromkeys(COUNT_KEYS, 0) | dict(model_ticks=1000), candidate_count=100,
        candidate_digest="fixture", digest_layout=[])


def bank(t=40, empty=False):
    champion = plan(t)
    declined = deepcopy(champion)
    declined.update(initiated=False, commands=[], duration=0, member=None, site=None, arrival_t=None)
    return dict(original_R=declined, champions=[] if empty else [champion], candidate_rows=np.zeros((100, 40), dtype="<f8"))


def fake_ordinary(self, t, state, mask):
    c = self.controller
    assert c.next_t == t
    if state is not None:
        c.positions, c.users = decode_public_state(state, 8)
    c.commands = np.zeros((8, 3), np.float32)
    c.next_t += 1
    return c.commands.copy(), mask, dict(t=t, old_mask=mask, issued_mask=mask, phase="ordinary")


def fake_result(controller, state, mask, p=None, *, start_t=40, end_t=500,
                report_horizon=500, physical_positions=None, tie=False):
    physical, _ = decode_public_state(state, 8)
    if physical_positions is not None:
        physical = np.asarray(physical_positions).copy()
    count = end_t-start_t
    positions = np.repeat(physical[None], count+1, axis=0)
    actions = np.zeros((count, 8, 3), np.float32)
    if start_t == 40 and p is not None:
        actions[0] = p["commands"][0]
        positions[1:] = predict_next(physical, actions[0])
    reward = np.zeros((count, 4))
    reward[:, 0] = (0 if tie else 1) if start_t == 40 and p else 0 if start_t == 40 else 2 if p and p["initiated"] else 1
    reward[:, 1] = 1 if p and p["initiated"] else 0
    times = np.arange(start_t, end_t, 10, dtype=np.int64)
    reports = np.asarray([surrogate.encode_model_report(positions[t-start_t], state, int(t)) for t in times])
    arrays = dict(positions=positions, actions=actions, masks=np.full(count, mask, np.int64),
        reward_components=reward, controller_estimates=positions.copy(), report_times=times, reports=reports)
    cc, rc = empty_counts(), dict.fromkeys(COUNT_KEYS, 0)
    rc.update(requested_candidates=count, scored_candidates=count)
    terminal = deepcopy(controller)
    terminal.positions = positions[-1].copy()
    terminal.next_t = end_t
    return dict(arrays=arrays, decisions=[dict(t=t) for t in range(start_t, end_t)],
        summary=surrogate.summarize(arrays, start_t, end_t, cc, rc), terminal_controller=terminal, terminal_mask=mask)


def test_120_menu_remaining_time_nonpositive_and_aliases(monkeypatch):
    class NegativeScores:
        def __init__(self, users):
            self.counts = dict.fromkeys(COUNT_KEYS, 0)
        def score(self, positions, masks):
            self.counts["requested_candidates"] += len(masks)
            self.counts["scored_candidates"] += len(masks)
            return [dict(J=0. if m == 127 else -1., served=0, quality=0., energy_penalty=0.) for m in masks]
    monkeypatch.setattr(option, "_Scores", NegativeScores)
    positions = np.tile([0., 0., 50.], (8, 1))
    users = np.zeros((50, 2))
    menu = option.enumerate_champions(positions, users, 127, start_t=120)
    assert not menu["original_R"]["initiated"]
    champion = menu["champions"][0]
    assert champion["initiated"] and champion["predicted_total_J"] == -370
    assert champion["arrival_t"] == 130 and champion["selected"]["site"] == 0
    assert menu["candidate_rows"].shape == (100, 40)
    assert champion["counts"]["requested_candidates"] == 12801
    assert champion["counts"]["model_ticks"] == 1000
    alias = deepcopy(champion)
    alias["site"] = 99
    assert option.branch_id(alias) != option.branch_id(champion)
    assert option.physical_identity(alias) == option.physical_identity(champion)
    empty = option.enumerate_champions(positions, users, 255, start_t=120)
    assert empty["champions"] == [] and empty["candidate_rows"].shape == (0, 40)
    assert empty["original_R"]["counts"]["requested_candidates"] == 1


def test_real_short_segment_separates_unrounded_physics_and_report():
    c, state = history(120), report(120)
    physical = c.positions.copy()
    physical[:, 0] += .000003
    before = deepcopy(c.__dict__)
    result = surrogate.simulate_segment(c, state, 127, start_t=120, end_t=123,
                                        physical_positions=physical)
    np.testing.assert_array_equal(result["arrays"]["positions"][0], physical)
    np.testing.assert_array_equal(result["arrays"]["reports"][0], state)
    users = decode_public_state(state, 8)[1]
    for i in range(3):
        score = _Scores(users).score(result["arrays"]["positions"][i+1], [result["arrays"]["masks"][i]])[0]
        np.testing.assert_array_equal(result["arrays"]["reward_components"][i], [score[k] for k in surrogate.REWARD_COMPONENTS])
    assert result["summary"]["model_transitions"] == result["summary"]["reward_counts"]["requested_candidates"] == 3
    assert result["summary"]["reward_counts"]["cached_candidates"] == 0
    assert result["arrays"]["reports"][0, -1] == np.float32(120/500)
    for key, value in before.items():
        if isinstance(value, np.ndarray):
            np.testing.assert_array_equal(getattr(c, key), value)
        else:
            assert getattr(c, key) == value


def test_parameterized_forced_index_arrival_zero_and_expired_plan(monkeypatch):
    p = plan(120)
    base = surrogate.OptionProgram("C")
    base.controller, base.plan, base.option_old_mask = history(120), p, 127
    command, mask, decision = base.select(120, report(120), 127)
    np.testing.assert_array_equal(command, p["commands"][0])
    assert decision["phase"] == "transit" and mask == 127
    base.controller.next_t = 130
    monkeypatch.setattr(surrogate, "arrival_mask", lambda *args: (128, dict(counts=dict.fromkeys(COUNT_KEYS, 0))))
    command, mask, decision = base.select(130, report(130), 127)
    assert not command.any() and mask == 128 and decision["phase"] == "arrival"
    assert not base.controller.commands.any()
    monkeypatch.setattr(Program, "select", fake_ordinary)
    _, _, decision = base.select(131, None, 128)
    assert decision["phase"] == "ordinary"
    with pytest.raises(ValueError):
        base.select(131, None, 128)


def test_original_T_G2_prefix_bridge_and_fresh_120(monkeypatch):
    monkeypatch.setattr(Program, "select", fake_ordinary)
    monkeypatch.setattr(original, "enumerate_champions", lambda *args: bank())
    monkeypatch.setattr(original, "simulate_continuation", lambda c, s, m, p, h: fake_result(c, s, m, p))
    monkeypatch.setattr(temporal, "enumerate_champions", lambda p, u, m, start, h: bank(start, empty=True))
    monkeypatch.setattr(temporal, "simulate_segment", fake_result)
    tprog, gprog, reference = temporal.TemporalProgram("T"), temporal.TemporalProgram("G2"), original.ContinuationProgram()
    for tick in range(120):
        state = report(tick) if tick % 10 == 0 else None
        actual = tprog.select(tick, state, 127)
        repeated = gprog.select(tick, state, 127)
        expected = reference.select(tick, state, 127)
        np.testing.assert_array_equal(actual[0], expected[0])
        np.testing.assert_array_equal(repeated[0], expected[0])
        assert actual[1:] == repeated[1:] == expected[1:]
    first = gprog.plans[40]
    assert first["arrival_t"] == 50
    _, _, second = gprog.select(120, report(120), 127)
    assert not gprog.plan["initiated"] and gprog.plan["arrival_t"] is None
    assert gprog.plans[40] == first
    assert sorted(gprog.selections) == [40, 120] and sorted(tprog.selections) == [40]
    assert second["temporal"]["selected_model_branch"] == "actual/t120/branch/stay"
    assert set(gprog.banks) == {"actual/t40/bank", "actual/t120/bank"}


@pytest.mark.parametrize("tie", [False, True])
def test_nested_state_flow_stay_first_sinks_bank_counts_and_actual_replan(monkeypatch, tie):
    monkeypatch.setattr(Program, "select", fake_ordinary)
    menu_calls, model_calls, emitted, bank_ids = [], [], [], []
    def menu(positions, users, mask, start, horizon):
        menu_calls.append((start, positions.copy()))
        return bank(start)
    def model(c, s, m, p=None, **kwargs):
        model_calls.append(dict(start=kwargs["start_t"], report=s.copy(), physical=deepcopy(kwargs.get("physical_positions")), plan=deepcopy(p)))
        return fake_result(c, s, m, p, tie=tie, **kwargs)
    monkeypatch.setattr(temporal, "enumerate_champions", menu)
    monkeypatch.setattr(temporal, "simulate_segment", model)
    def sink(identifier, result):
        emitted.append((identifier, deepcopy(result)))
        result["summary"]["total_J"] = 1e99  # Must not alter selection.
        result["arrays"]["positions"][:] = -99
    def candidates(identifier, rows):
        bank_ids.append(identifier)
        rows[:] = -99
    program = temporal.TemporalProgram("A2", branch_sink=sink, candidate_sink=candidates)
    program.base.controller = history(40)
    command, mask, decision = program.select(40, report(40), 127)
    assert len(menu_calls) == 3 and [t for t, _ in menu_calls] == [40, 120, 120]
    assert len(emitted) == 6
    assert bank_ids == ["a2/first/bank", "a2/first/stay/t120/bank", "a2/first/m7_s0/t120/bank"]
    expected = "stay" if tie else "m7_s0"
    assert program.selections[40]["selected_branch"] == expected
    assert program.selections[40]["selected_model_branch"] == f"a2/first/{expected}/outer"
    assert program.selections[40]["branches"][0]["summary"]["total_J"] == 760
    assert program.plan["initiated"] != tie
    outer = [r for key, r in emitted if key.endswith("/outer")]
    assert sum(r["summary"]["model_transitions"] for _, r in emitted) == 2440
    assert all(r["summary"]["model_transitions"] == 460 for r in outer)
    for call in model_calls:
        if call["physical"] is not None:
            assert call["start"] == 120
            # The inner report is independently rounded. The outer suffix uses
            # the old physical state rather than any selected inner trajectory.
            decoded = decode_public_state(call["report"], 8)[0]
            if np.any(call["physical"][:, 0] != history(40).positions[:, 0]):
                assert np.any(call["physical"] != decoded)
    assert all("terminal_controller" not in r for _, r in emitted)
    assert outer[0]["summary"]["inner_selection"]["selected_model_branch"] == "a2/first/stay/inner/m7_s0"
    saved = program.selections
    saved[40]["selected_branch"] = "corrupted"
    assert program.selections[40]["selected_branch"] == expected
    program.base.controller.next_t = 120
    actual = report(120)
    actual[:24].reshape(8, 3)[:, 0] = .4
    program.select(120, actual, mask)
    assert menu_calls[-1][0] == 120
    np.testing.assert_array_equal(menu_calls[-1][1], decode_public_state(actual, 8)[0])
    assert program.selections[120]["selected_model_branch"].startswith("actual/t120/branch/")
    assert "actual/t120/bank" in program.banks
    json.dumps(program.selections, allow_nan=False)


def test_concatenation_reduces_in_tick_order_not_grouped_returns():
    c, state = history(40), report(40)
    prefix = fake_result(c, state, 127, start_t=40, end_t=120)
    report120 = surrogate.encode_model_report(prefix["arrays"]["positions"][-1], state, 120)
    suffix = fake_result(prefix["terminal_controller"], report120, 127,
                         start_t=120, end_t=500, physical_positions=prefix["arrays"]["positions"][-1])
    prefix["arrays"]["reward_components"][:, 0] = 0
    prefix["arrays"]["reward_components"][0, 0] = 1e16
    suffix["arrays"]["reward_components"][:, 0] = 0
    suffix["arrays"]["reward_components"][:2, 0] = [-1e16, 1]
    combined = surrogate.concatenate(prefix, suffix)
    assert combined["summary"]["total_J"] == 1
    assert len(combined["arrays"]["positions"]) == 461
    assert combined["arrays"]["report_times"].tolist() == list(range(40, 500, 10))
    combined["decisions"][0]["t"] = -1
    assert prefix["decisions"][0]["t"] == 40
    suffix["arrays"]["positions"][0, 0, 0] += 1e-9
    with pytest.raises(ValueError, match="physical state"):
        surrogate.concatenate(prefix, suffix)


def test_nested_reversal_values_stay_first_with_later_T(monkeypatch):
    monkeypatch.setattr(Program, "select", fake_ordinary)
    monkeypatch.setattr(temporal, "enumerate_champions", lambda p, u, m, t, h: bank(t))
    def model(c, s, m, p=None, **kwargs):
        result = fake_result(c, s, m, p, **kwargs)
        if kwargs["start_t"] == 120:
            first_moved = decode_public_state(s, 8)[0][7, 0] > 140
            result["arrays"]["reward_components"][:, 0] = 1 if first_moved else 3 if p and p["initiated"] else 1
            result["summary"] = surrogate.summarize(result["arrays"], 120, 500,
                result["summary"]["controller_counts"], result["summary"]["reward_counts"])
        return result
    monkeypatch.setattr(temporal, "simulate_segment", model)
    a2 = temporal.TemporalProgram("A2")
    a2.base.controller = history(40)
    a2.select(40, report(40), 127)
    selection = a2.selections[40]
    assert selection["branches"][0]["summary"]["total_J"] == 1140
    assert selection["branches"][1]["summary"]["total_J"] == 460
    assert selection["selected_branch"] == "stay" and not a2.plan["initiated"]
    # The unchanged first T values the option above C-only stay in this fixture.
    monkeypatch.setattr(original, "enumerate_champions", lambda *args: bank())
    monkeypatch.setattr(original, "simulate_continuation", lambda c, s, m, p, h: fake_result(c, s, m, p))
    first_t = temporal.TemporalProgram("T")
    first_t.base.controller = history(40)
    first_t.select(40, report(40), 127)
    assert first_t.plan["initiated"]


def test_all_active_stay_menu_and_clock_validation(monkeypatch):
    monkeypatch.setattr(Program, "select", fake_ordinary)
    monkeypatch.setattr(temporal, "enumerate_champions", lambda p, u, m, t, h: bank(t, empty=True))
    monkeypatch.setattr(temporal, "simulate_segment", fake_result)
    program = temporal.TemporalProgram("A2")
    program.base.controller = history(40)
    program.select(40, report(40), 255)
    assert len(program.selections[40]["branches"]) == 1
    assert not program.plan["initiated"]
    assert set(program.banks) == {"a2/first/bank", "a2/first/stay/t120/bank"}
    with pytest.raises(ValueError):
        program.select(40, report(40), 255)
    with pytest.raises(ValueError):
        program.select(41, report(41), 255)


def test_refuses_altered_plan_history_and_expired_commitment():
    c, state = history(120), report(120)
    with pytest.raises(ValueError, match="expired"):
        surrogate.simulate_segment(c, state, 127, plan(40), start_t=120, end_t=121)
    for key, value in (("arrival_t", 131), ("duration", 11), ("member", 6)):
        modified = plan(120)
        modified[key] = value
        with pytest.raises(ValueError):
            surrogate.simulate_segment(c, state, 127, modified, start_t=120, end_t=121)
    modified = plan(120)
    modified["commands"][0][0][0] = 1
    with pytest.raises(ValueError, match="malformed"):
        surrogate.simulate_segment(c, state, 127, modified, start_t=120, end_t=121)
    c.commands = c.commands.astype(np.float64)
    with pytest.raises(ValueError, match="float32"):
        surrogate.simulate_segment(c, state, 127, start_t=120, end_t=121)
