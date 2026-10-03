"""Source/mock checks only: no real controller/option/scorer/world is executed."""

from copy import deepcopy
import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state
from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS
from experiments.candidates.uav_fleet_transmission.b04.surrogate import encode_model_report
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import reader as certificate_reader
from experiments.candidates.uav_planning_opportunity_timing.b01 import controller, option, segment


def report(t=40):
    value = np.zeros(133, dtype=np.float32)
    value[:24].reshape(8, 3)[:, :2] = .1
    value[24:32] = 1
    value[-1] = np.float32(t / 500)
    return value


class StubHistory(OrdinaryController):
    # Deliberately never call OrdinaryController.__init__ or its select method.
    def __init__(self, t=40):
        self.n_uavs, self.next_t = 8, t
        self.positions, self.users = decode_public_state(report(t), 8)
        self.commands = np.zeros((8, 3), dtype=np.float32)


def stub_predict(positions, commands):
    assert commands.dtype == np.float32
    return np.clip(positions + (commands * 30) * 1.0, [0, 0, 50], [1000, 1000, 150])


class StubProgram:
    calls = []

    def __init__(self, arm="C", horizon=500):
        self.controller, self.plan, self.option_old_mask = StubHistory(0), None, None

    def select(self, t, state, mask):
        c = self.controller
        assert c.next_t == t and (state is not None) == (t % 10 == 0)
        if state is not None:
            c.positions, c.users = decode_public_state(state, 8)
        command = np.zeros((8, 3), dtype=np.float32)
        phase = "ordinary"
        if self.plan and self.plan["initiated"] and t <= self.plan["arrival_t"]:
            assert mask == self.option_old_mask
            if t < self.plan["arrival_t"]:
                command = np.asarray(self.plan["commands"][t - self.plan.get("start_t", 40)], dtype=np.float32)
                phase = "transit"
            else:
                mask |= 1 << self.plan["member"]
                phase = "arrival"
        c.positions = stub_predict(c.positions, command)
        c.commands, c.next_t = command.copy(), t + 1
        decision = dict(t=t, old_mask=self.option_old_mask if phase != "ordinary" else mask,
                        issued_mask=mask, phase=phase)
        if phase == "ordinary":
            decision["motion"] = dict.fromkeys(COUNT_KEYS, 0)
            decision["motion"]["requested_candidates"] = 1
        type(self).calls.append((t, state is not None, phase, mask))
        return command, mask, decision


class StubScore:
    calls = 0

    def __init__(self, users):
        self.counts = dict.fromkeys(COUNT_KEYS, 0)

    def score(self, positions, masks):
        type(self).calls += 1
        self.counts["requested_candidates"] += len(masks)
        self.counts["scored_candidates"] += len(masks)
        unique_rows = len({row.tobytes() for row in positions})
        self.counts["geometry_rows_computed"] += unique_rows
        self.counts["geometry_rows_reused"] += 8 - unique_rows
        return [dict(J=.1, served=1, quality=.2, energy_penalty=.0) for _ in masks]


DEPS = segment.SegmentDependencies(program=StubProgram, predict=stub_predict, scorer=StubScore)


def plan(t=40, duration=10, member=1, site=0):
    return dict(start_t=t, initiated=True, member=member, site=site, duration=duration,
                arrival_t=t + duration, commands=np.zeros((duration, 8, 3), dtype=np.float32).tolist(),
                predicted_destination=StubHistory(t).positions.tolist(), selected=dict(path=0.))


def test_candidate_clocks_minimum_zero_path_and_malformed():
    assert option.second_clock(None) == 50
    assert option.second_clock({"initiated": False}) == 50
    for duration, expected in zip((10, 20, 30, 40), (60, 70, 80, 90)):
        assert option.second_clock(plan(duration=duration)) == expected
    with pytest.raises(ValueError):
        option.second_clock(plan(t=50))
    with pytest.raises(ValueError):
        option.second_clock(plan(duration=11))


def test_complete_menu_reprices_all_sites_not_old_champion_and_keeps_nonpositive():
    visited = []
    def sites(users):
        return np.zeros((100, 2))
    def transit(positions, member, site, stay):
        index = len(visited) % 100
        visited.append((member, index))
        # Short site0 wins at50; longer site1 with a larger tail wins at40.
        duration = 40 if index == 1 else 10
        transit_J = -47.14 if index == 1 else -49.
        destination = positions.copy()
        destination[0, 0] = index
        return dict(offsets=[0, 0], descent_ticks=0, duration=duration, commands=np.zeros((duration, 8, 3), np.float32),
                    destination=destination, transit_J=transit_J, transit_served=duration, path=0.)
    def mask_choice(scorer, destination, member):
        index = int(destination[0, 0])
        tail = dict(J=.21 if index == 1 else .2, served=1, quality=0., energy_penalty=0.)
        return [1 << member], [tail], 0
    dependencies = option.MenuDependencies(StubScore, sites, transit, mask_choice)
    positions, users = StubHistory().positions, StubHistory().users
    # Silence only member1. All original100 aliases are visited every time.
    old = 255 ^ 2
    first = option.enumerate_champions(positions, users, old, 40, dependencies=dependencies)
    second = option.enumerate_champions(positions, users, old, 90, dependencies=dependencies)
    assert len(visited) == 200 and len(first["candidate_rows"]) == len(second["candidate_rows"]) == 100
    assert first["champions"][0]["site"] != second["champions"][0]["site"]
    assert all(p["initiated"] for p in first["champions"] + second["champions"])
    assert not first["original_R"]["initiated"] and not second["original_R"]["initiated"]
    assert first["champions"][0]["duration"] in (10, 40)
    for bank in (first, second):
        assert bank["original_R"]["candidate_digest"] == hashlib.sha256(bank["candidate_rows"].tobytes()).hexdigest()
    empty = option.enumerate_champions(positions, users, 255, 50, dependencies=dependencies)
    assert not empty["champions"] and empty["candidate_rows"].shape == (0, 40)


@pytest.mark.parametrize("duration", [10, 20, 30, 40])
def test_early_prefix_nine_eligible_ticks_no_recurrence_and_source_isolation(duration):
    history = StubHistory()
    before = deepcopy(history.__dict__)
    commitment = plan(duration=duration)
    t2 = option.second_clock(commitment)
    full = segment.simulate_segment(history, report(), 1, commitment, end_t=t2, reuse=False, dependencies=DEPS)
    reused = segment.simulate_segment(history, report(), 1, commitment, end_t=t2, reuse=True, dependencies=DEPS)
    for key in full["arrays"]:
        assert full["arrays"][key].tobytes() == reused["arrays"][key].tobytes()
    assert full["summary"] == reused["summary"] and full["decisions"] == reused["decisions"]
    work = reused["certificate"]["reuse"]
    assert work["reused_ticks"] == 0 and work["first_repeat"] is None
    assert work["eligibility_after_t"] == 40 + duration
    assert sum(t > work["eligibility_after_t"] for t in work["source_times"]) == 9
    assert [d["phase"] for d in reused["decisions"]] == ["transit"] * duration + ["arrival"] + ["ordinary"] * 9
    for key, value in before.items():
        assert np.array_equal(getattr(history, key), value)
    assert reused["terminal_mask"] & 2


def test_suffix_reuse_full_bits_fresh_cache_phase_and_outer_precision():
    h = StubHistory(60)
    physical = h.positions.copy()
    physical[0, 0] += .0000001
    full = segment.simulate_segment(h, report(60), 3, start_t=60, end_t=150, physical_positions=physical,
                                    reuse=False, dependencies=DEPS)
    reused = segment.simulate_segment(h, report(60), 3, start_t=60, end_t=150, physical_positions=physical,
                                      reuse=True, dependencies=DEPS)
    for key in full["arrays"]:
        assert full["arrays"][key].tobytes() == reused["arrays"][key].tobytes()
    assert full["summary"] == reused["summary"] and full["decisions"] == reused["decisions"]
    work = reused["certificate"]["reuse"]
    assert work["reused_ticks"] > 0 and work["first_repeat"]["period"] == 40
    assert all(source <= t for t, source in zip(range(60, 150), work["source_times"]))
    assert np.array_equal(reused["arrays"]["positions"][0], physical)
    assert not np.array_equal(decode_public_state(report(60), 8)[0], physical)
    assert reused["arrays"]["report_times"].tolist() == list(range(60, 150, 10))
    repeated = segment.simulate_segment(h, report(60), 3, start_t=60, end_t=150, physical_positions=physical,
                                        reuse=True, dependencies=DEPS)
    assert repeated["certificate"]["reuse"] == work  # no cross-call cache.

    # Frozen independent checker receives a freshly generated uncompressed reference.
    reference = SimpleNamespace(payload={k: full[k] for k in ("arrays", "summary", "decisions")},
        start=60, end=150, kind="inner", entry_mask=3, entry_commands=h.commands.copy(), entry_users=h.users.copy(),
        expected_plan=None, plan_bound=True)
    identifier = "ae/first/stay/t60/inner/stay"
    record = dict(id=identifier, certificate=reused["certificate"],
                  scientific=certificate_reader.payload_binding(reference.payload))
    certificate_reader.verify_certificate(identifier, record, reference, True)


def test_key_preserves_signed_zero_all_state_bits_and_absolute_phase():
    history = StubHistory(60)
    state = report(60)
    key = segment.recurrence_key(60, history.positions, history, 3, state)
    assert segment.recurrence_key(100, history.positions, history, 3, state) == key
    assert segment.recurrence_key(61, history.positions, history, 3, state) != key
    altered = deepcopy(history)
    altered.commands[0, 0] = np.float32(-0.)
    assert segment.recurrence_key(60, altered.positions, altered, 3, state) != key
    altered = deepcopy(history)
    altered.positions[0, 0] = np.nextafter(altered.positions[0, 0], np.inf)
    assert segment.recurrence_key(60, history.positions, altered, 3, state) != key
    with pytest.raises(ValueError):
        segment.simulate_segment(history, state, 3, start_t=100, dependencies=DEPS)


def test_nonpositive_and_alias_ties_keep_complete_hypothetical_branches(stubbed_controller, monkeypatch):
    program = controller.TimingProgram("A_E")
    program.base.controller = StubHistory(60)
    aliases = [plan(t=60, site=1), plan(t=60, site=0)]
    seen = []
    monkeypatch.setattr(program, "_bank", lambda *a: bank(60, aliases))
    def simulate(identifier, history, state, mask, commitment, **kwargs):
        seen.append(identifier)
        result = stubbed_controller(identifier, history, state, mask, commitment, **kwargs)
        result["summary"].update(total_J=2. if commitment else 1., total_served=1)
        return result
    monkeypatch.setattr(program, "_simulate", simulate)
    selected, record = program._ordinary_selection(program.controller, report(60), 1, 60, "actual/t60/first/stay", "stay")
    assert len(seen) == 3 and selected["site"] == 0 and record["selected_branch"] == "m1_s0"
    assert record["branches"][1]["physical_identity"] == record["branches"][2]["physical_identity"]
    assert record["branches"][1]["id"] != record["branches"][2]["id"]


def bank(t, plans):
    stay = dict(start_t=t, initiated=False, selected=None, commands=[], member=None, site=None,
                duration=0, arrival_t=None, predicted_destination=StubHistory(t).positions.tolist(),
                predicted_mask=None, stay_total_J=1., stay_total_served=1, predicted_total_J=1.,
                predicted_total_served=1, counts=dict.fromkeys(COUNT_KEYS, 0), candidate_count=0,
                candidate_digest=hashlib.sha256(b"").hexdigest(), digest_layout=[])
    return dict(original_R=stay, champions=deepcopy(plans), candidate_rows=np.zeros((0, 40), dtype="<f8"))


@pytest.fixture
def stubbed_controller(monkeypatch):
    monkeypatch.setattr(controller, "OptionProgram", StubProgram)
    StubProgram.calls = []
    def simulate(identifier, history, state, mask, commitment, **kwargs):
        return segment.simulate_segment(history, state, mask, commitment, dependencies=DEPS, **kwargs)
    return simulate


def test_ordinary_strict_stay_tie_even_with_service_advantage(stubbed_controller, monkeypatch):
    program = controller.TimingProgram("A_E")
    program.base.controller = StubHistory(60)
    monkeypatch.setattr(program, "_bank", lambda *a: bank(60, [plan(t=60)]))
    def simulate(identifier, history, state, mask, commitment, **kwargs):
        result = stubbed_controller(identifier, history, state, mask, commitment, **kwargs)
        result["summary"].update(total_J=1., total_served=100 if commitment else 0)
        return result
    monkeypatch.setattr(program, "_simulate", simulate)
    selected, record = program._ordinary_selection(program.controller, report(60), 1, 60, "actual/t60/first/stay", "stay")
    assert not selected["initiated"] and record["selected_branch"] == "stay"


def test_anticipation_candidate_clocks_inner_copy_outer_unrounded_annotations_and_sink_isolation(stubbed_controller, monkeypatch):
    emitted, certificates, banks, contexts = {}, {}, {}, []
    def branch_sink(identifier, payload):
        emitted[identifier] = deepcopy(payload)
        payload["arrays"]["positions"][:] = -100  # malicious callbacks cannot change science.
        payload["summary"]["total_J"] = -999
    def segment_sink(identifier, payload):
        certificates[identifier] = deepcopy(payload)
        payload["arrays"]["positions"][:] = -200
        payload["certificate"].clear()
    def candidate_sink(identifier, rows):
        banks[identifier] = rows.copy()
        rows[:] = -300
    program = controller.TimingProgram("A_E", branch_sink=branch_sink, candidate_sink=candidate_sink, segment_sink=segment_sink)
    program.base.controller = StubHistory(40)
    first_plans = [plan(duration=d, site=i) for i, d in enumerate((10, 20, 30, 40))]
    def enumerate_mock(positions, users, mask, start_t, horizon):
        return bank(start_t, first_plans if start_t == 40 else [])
    monkeypatch.setattr(controller, "enumerate_champions", enumerate_mock)
    def simulate(identifier, history, state, mask, commitment, **kwargs):
        result = stubbed_controller(identifier, history, state, mask, commitment, **kwargs)
        if identifier.endswith("/prefix"):
            result["arrays"]["positions"][-1, 0, 0] += .0000001
        contexts.append((identifier, deepcopy(history.__dict__), state.copy(), kwargs.get("physical_positions")))
        program._emit_segment(identifier, result)
        return result
    monkeypatch.setattr(program, "_simulate", simulate)
    original_history = deepcopy(program.controller.__dict__)
    selected, record = program._anticipated_selection(report(), 1)
    assert not selected["initiated"]  # all modeled J totals tie; full stay-first program wins.
    assert [b["second_t"] for b in record["branches"]] == [50, 60, 70, 80, 90]
    for first, t2 in [("stay", 50)] + [(f"m1_s{i}", t) for i, t in enumerate((60, 70, 80, 90))]:
        scope = f"ae/first/{first}/t{t2}"
        outer = emitted[scope + "/outer"]
        assert outer["summary"]["identity"]["second_t"] == t2
        assert len(outer["decisions"]) == 460
        assert "predicted_temporal_selection" in outer["decisions"][t2 - 40]
        assert sum("predicted_temporal_selection" in d for d in outer["decisions"]) == 1
        suffix_context = next(c for c in contexts if c[0] == scope + "/suffix")
        assert suffix_context[1]["next_t"] == t2
        assert suffix_context[2].dtype == np.float32 and suffix_context[2][-1] == np.float32(t2 / 500)
        assert not np.array_equal(suffix_context[3], decode_public_state(suffix_context[2], 8)[0])
        assert scope + "/bank" in banks
    for key, value in original_history.items():
        assert np.array_equal(getattr(program.controller, key), value)
    assert all("certificate" in value for value in certificates.values())


def test_pre_e_dispatch_actual_history_expiry_decline_and_no_third(stubbed_controller, monkeypatch):
    program = controller.TimingProgram("A_E")
    program.base.controller = StubHistory(40)
    first = plan(duration=10)
    monkeypatch.setattr(program, "_anticipated_selection", lambda state, mask: (deepcopy(first), {"selected_branch": "m1_s0"}))
    calls = []
    def actual(history, state, mask, start_t, scope, first_context):
        calls.append((history, history.commands.copy(), mask, start_t, scope, first_context))
        assert mask & 2 and history.next_t == 60  # arrival installed member, no prior remuting E.
        return bank(60, [])["original_R"], {"selected_branch": "stay"}
    monkeypatch.setattr(program, "_ordinary_selection", actual)
    mask = 1
    original = program.controller
    for t in range(40, 131):
        command, mask, decision = program.select(t, report(t) if t % 10 == 0 else None, mask)
    assert program.controller is original and program.second_t == 60
    assert len(calls) == 1 and calls[0][0] is original
    assert set(program.plans) == {40, 60} and not program.plan["initiated"]
    assert [row[2] for row in StubProgram.calls[:21]] == ["transit"] * 10 + ["arrival"] + ["ordinary"] * 10
    assert all(row[2] == "ordinary" for row in StubProgram.calls[21:])
    with pytest.raises(ValueError):
        program.select(130, report(130), mask)


def test_ge_uses_retained_first_selector_callbacks_and_stay_clock(monkeypatch, stubbed_controller):
    class StubFirst:
        def __init__(self, owner):
            self.owner, self.base, self.continuation = owner, StubProgram(), None
        def select(self, t, state, mask):
            if t == 40:
                self.base.plan = bank(40, [])["original_R"]
                self.owner._original_bank(np.zeros((0, 40), dtype="<f8"))
                self.continuation = dict(original_R=deepcopy(self.base.plan), selected_branch="stay", branches=[])
            return self.base.select(t, state, mask)
    monkeypatch.setattr(controller, "_BoundFirst", StubFirst)
    program = controller.TimingProgram("G_E")
    program.base.controller = StubHistory(40)
    calls = []
    def second(history, state, mask, start_t, scope, first):
        calls.append((start_t, scope, first))
        return bank(50, [])["original_R"], {"selected_branch": "stay"}
    monkeypatch.setattr(program, "_ordinary_selection", second)
    mask = 255
    for t in range(40, 61):
        _, mask, _ = program.select(t, report(t) if t % 10 == 0 else None, mask)
    assert program.second_t == 50 and calls == [(50, "actual/t50/first/stay", "stay")]
    assert "actual/t40/bank" in program.banks and set(program.selections) == {40, 50}
