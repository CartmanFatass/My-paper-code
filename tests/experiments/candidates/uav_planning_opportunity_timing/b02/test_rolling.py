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
from experiments.candidates.uav_planning_opportunity_timing.b02 import controller, option, segment


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


def bank(t, plans):
    stay = dict(start_t=t, initiated=False, selected=None, commands=[], member=None, site=None,
                duration=0, arrival_t=None, predicted_destination=StubHistory(t).positions.tolist(),
                predicted_mask=None, stay_total_J=1., stay_total_served=1, predicted_total_J=1.,
                predicted_total_served=1, counts=dict.fromkeys(COUNT_KEYS, 0), candidate_count=0,
                candidate_digest=hashlib.sha256(b"").hexdigest(), digest_layout=[])
    return dict(original_R=stay, champions=deepcopy(plans), candidate_rows=np.zeros((0, 40), dtype="<f8"))



@pytest.fixture
def stubbed(monkeypatch):
    monkeypatch.setattr(controller, "OptionProgram", StubProgram)
    StubProgram.calls = []
    def new(arm="A_E4", t=40, **kwargs):
        actor = controller.RollingProgram(arm, **kwargs)
        actor.base.controller = StubHistory(t)
        def simulate(identifier, history, state, mask, commitment, **kwargs):
            result = segment.simulate_segment(history, state, mask, commitment, dependencies=DEPS,
                                               reuse=actor.reuse, **kwargs)
            actor._emit_segment(identifier, result)
            return result
        monkeypatch.setattr(actor, "_simulate", simulate)
        return actor
    return new


def test_next_clock_every_start_duration_and_invalid():
    for t in range(40, 191, 10):
        assert option.next_clock(None, t) == t + 10
        assert option.next_clock(bank(t, [])["original_R"], t) == t + 10
        for duration in (10, 20, 30, 40):
            assert option.next_clock(plan(t, duration), t) == t + duration + 10
    for t in (39, 41, 200, True):
        with pytest.raises(ValueError):
            option.next_clock(None, t)
    for bad in (plan(40, 11), plan(50), dict(plan(), arrival_t=51), {"initiated": 1}):
        with pytest.raises(ValueError):
            option.next_clock(bad, 40)


@pytest.mark.parametrize("arm", ["G_E4", "A_E4"])
@pytest.mark.parametrize("duration, expected", [(0, [40, 50, 60, 70]), (10, [40, 60, 80, 100]),
                                              (20, [40, 70, 100, 130]), (30, [40, 80, 120, 160]),
                                              (40, [40, 90, 140, 190])])
def test_four_consumed_opportunities_expiry_history_no_fifth(stubbed, monkeypatch, arm, duration, expected):
    actor = stubbed(arm)
    original = actor.controller
    calls = []
    def selection(history, state, mask, t, kind):
        ordinal = len(actor.opportunity_times) + 1
        assert history is original and history.next_t == t
        if ordinal > 1 and duration:
            assert mask & (1 << (ordinal - 1))  # previous mover active before E.
        selected = plan(t, duration, member=ordinal) if duration else bank(t, [])["original_R"]
        calls.append((t, kind, state[-1], history.commands.copy()))
        return selected, {"selected_branch": option.branch_id(selected)}
    monkeypatch.setattr(actor, "_ordinary_selection", lambda h, r, m, t, scope, first: selection(h, r, m, t, "ordinary"))
    monkeypatch.setattr(actor, "_rolling_anticipated_selection", lambda r, m, t, k: selection(actor.controller, r, m, t, "anticipated"))
    mask = 1
    for t in range(40, 500):
        _, mask, decision = actor.select(t, report(t) if t % 10 == 0 else None, mask)
        if t in expected:
            assert "temporal" in decision and actor.plan["start_t"] == t
    assert actor.opportunity_times == expected and list(actor.plans) == expected
    assert actor.next_opportunity_t is None and actor.controller is original and original.next_t == 500
    assert [c[0] for c in calls] == expected
    assert [c[1] for c in calls] == (["anticipated"] * 3 + ["ordinary"] if arm == "A_E4" else ["ordinary"] * 4)
    assert all(c[2] == np.float32(c[0] / 500) for c in calls)
    if duration:
        assert actor.plan["arrival_t"] == expected[-1] + duration
        assert sum(c[2] == "arrival" for c in StubProgram.calls) == 4
    else:
        assert not actor.plan["initiated"]
    actor.opportunity_times.clear()
    actor.plans.clear()
    actor.selections.clear()
    assert len(actor.opportunity_times) == len(actor.plans) == len(actor.selections) == 4
    with pytest.raises(ValueError):
        actor.select(499, None, mask)


def test_menu_all_original_sites_nonpositive_aliases_and_repricing():
    visits = []
    def sites(users):
        return np.zeros((100, 2))
    def transit(positions, member, site, stay):
        i = len(visits) % 100
        visits.append((member, i))
        duration = 40 if i == 1 else 10
        destination = positions.copy()
        destination[0, 0] = i
        return dict(offsets=[0, 0], descent_ticks=0, duration=duration,
                    commands=np.zeros((duration, 8, 3), np.float32), destination=destination,
                    transit_J=-62. if i == 1 else -49., transit_served=duration, path=0.)
    def mask_choice(scorer, destination, member):
        tail = dict(J=.25 if int(destination[0, 0]) == 1 else .2, served=1, quality=0., energy_penalty=0.)
        return [1 << member], [tail], 0
    deps = option.MenuDependencies(StubScore, sites, transit, mask_choice)
    positions, users = decode_public_state(report(), 8)
    early = option.enumerate_champions(positions, users, 253, 40, dependencies=deps)
    late = option.enumerate_champions(positions, users, 253, 190, dependencies=deps)
    assert visits == [(1, i) for i in range(100)] * 2
    assert early["champions"][0]["site"] == 1 and late["champions"][0]["site"] == 0
    assert not late["original_R"]["initiated"] and late["champions"][0]["initiated"]
    assert late["champions"][0]["start_t"] == 190 and late["champions"][0]["arrival_t"] == 200
    assert option.physical_identity(early["champions"][0]) != option.physical_identity(late["champions"][0])
    assert late["original_R"]["candidate_digest"] == hashlib.sha256(late["candidate_rows"].tobytes()).hexdigest()
    assert early["original_R"]["candidate_digest"] != late["original_R"]["candidate_digest"]
    empty = option.enumerate_champions(positions, users, 255, 190, dependencies=deps)
    assert not empty["champions"] and empty["candidate_rows"].shape[0] == 0


@pytest.mark.parametrize("start", [100, 140, 190])
@pytest.mark.parametrize("duration", [0, 10, 20, 30, 40])
def test_segment_new_clocks_barriers_bits_private_cache_and_certificate(start, duration):
    h = StubHistory(start)
    commitment = plan(start, duration) if duration else None
    physical = h.positions.copy()
    physical[0, 0] += .0000001
    arguments = dict(start_t=start, end_t=start + (duration + 90), physical_positions=physical, dependencies=DEPS)
    full = segment.simulate_segment(h, report(start), 1, commitment, reuse=False, **arguments)
    reused = segment.simulate_segment(h, report(start), 1, commitment, reuse=True, **arguments)
    repeated = segment.simulate_segment(h, report(start), 1, commitment, reuse=True, **arguments)
    for key in full["arrays"]:
        assert full["arrays"][key].tobytes() == reused["arrays"][key].tobytes()
    assert full["summary"] == reused["summary"] and full["decisions"] == reused["decisions"]
    assert reused["certificate"] == repeated["certificate"]
    work = reused["certificate"]["reuse"]
    assert work["eligibility_after_t"] == start + duration and work["reused_ticks"] > 0
    assert work["first_repeat"]["source_t"] > start + duration
    assert work["first_repeat"]["period"] == 40 and h.next_t == start
    assert np.array_equal(full["arrays"]["positions"][0], physical)
    reference = SimpleNamespace(payload={k: full[k] for k in ("arrays", "summary", "decisions")},
        start=start, end=arguments["end_t"], kind="inner", entry_mask=1, entry_commands=h.commands.copy(),
        entry_users=h.users.copy(), expected_plan=commitment, plan_bound=True)
    identifier = "ae/op3/stay/t140/t190/inner/" + option.branch_id(commitment)
    record = dict(id=identifier, certificate=reused["certificate"], scientific=certificate_reader.payload_binding(reference.payload))
    certificate_reader.verify_certificate(identifier, record, reference, True)
    corrupt = deepcopy(record)
    corrupt["certificate"]["reuse"]["source_times"][-1] = start - 1
    with pytest.raises(ValueError):
        certificate_reader.verify_certificate(identifier, corrupt, reference, True)


@pytest.mark.parametrize("start,duration", [(90, 0), (140, 10), (140, 40)])
def test_prefix_nine_eligible_ticks_cannot_recur(start, duration):
    result = segment.simulate_segment(StubHistory(start), report(start), 1, plan(start, duration) if duration else None,
                                     start_t=start, end_t=start + duration + 10, dependencies=DEPS)
    assert result["certificate"]["reuse"]["reused_ticks"] == 0
    assert result["certificate"]["reuse"]["first_repeat"] is None
    h = StubHistory(start)
    commitment = plan(start, duration) if duration else None
    full = segment.simulate_segment(h, report(start), 1, commitment, start_t=start,
                                    end_t=start + duration + 10, dependencies=DEPS, reuse=False)
    reference = SimpleNamespace(payload={k: full[k] for k in ("arrays", "summary", "decisions")},
        start=start, end=start + duration + 10, kind="prefix", entry_mask=1,
        entry_commands=h.commands.copy(), entry_users=h.users.copy(), expected_plan=commitment, plan_bound=True)
    identifier = f"ae/op3/{option.branch_id(commitment)}/t{start}/t{start + duration + 10}/prefix"
    record = dict(id=identifier, certificate=result["certificate"], scientific=certificate_reader.payload_binding(reference.payload))
    certificate_reader.verify_certificate(identifier, record, reference, True)


def test_strict_j_stay_and_complete_aliases(stubbed, monkeypatch):
    actor = stubbed("G_E4", 190)
    plans = [plan(190, member=1, site=i) for i in (0, 1)]
    monkeypatch.setattr(actor, "_bank", lambda *a: bank(190, plans))
    simulate = actor._simulate
    seen = []
    def tied(identifier, *args, **kwargs):
        result = simulate(identifier, *args, **kwargs)
        result["summary"].update(total_J=1., total_served=10 if args[3] else 0)
        seen.append(identifier)
        return result
    monkeypatch.setattr(actor, "_simulate", tied)
    selected, record = actor._ordinary_selection(actor.controller, report(190), 1, 190, "actual/op4/t190/first/stay", "stay")
    assert not selected["initiated"] and len(seen) == 3
    assert record["branches"][1]["physical_identity"] == record["branches"][2]["physical_identity"]
    assert record["branches"][1]["model_branch"] != record["branches"][2]["model_branch"]


def test_first_search_retains_b01_payload_and_ids_without_real_constructor(stubbed, monkeypatch):
    from experiments.candidates.uav_planning_opportunity_timing.b01.controller import TimingProgram
    from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.inputs import record_bytes
    emitted = [{}, {}]
    actors = [stubbed(), TimingProgram.__new__(TimingProgram)]
    old = actors[1]
    old.arm, old.horizon, old.reuse = "A_E", 500, True
    old.base, old._banks = StubProgram(), {}
    old.base.controller = StubHistory(40)
    old.candidate_sink = old.segment_sink = None
    first_plans = [plan(duration=d, site=i) for i, d in enumerate((10, 20, 30, 40))]
    for i, actor in enumerate(actors):
        actor.branch_sink = lambda identifier, payload, i=i: emitted[i].update({identifier: deepcopy(payload)})
        monkeypatch.setattr(actor, "_bank", lambda h, r, m, t, identifier: bank(t, first_plans if t == 40 else []))
        def simulate(identifier, h, r, m, p, actor=actor, **kw):
            return segment.simulate_segment(h, r, m, p, dependencies=DEPS, reuse=actor.reuse, **kw)
        monkeypatch.setattr(actor, "_simulate", simulate)
    new_selected, new_record = actors[0]._rolling_anticipated_selection(report(), 1, 40, 1)
    old_selected, old_record = old._anticipated_selection(report(), 1)
    assert record_bytes(new_selected) == record_bytes(old_selected)
    assert record_bytes(new_record) == record_bytes(old_record)
    assert list(emitted[0]) == list(emitted[1])
    for identifier in emitted[0]:
        assert record_bytes(certificate_reader.payload_binding(emitted[0][identifier])) == record_bytes(certificate_reader.payload_binding(emitted[1][identifier]))
    assert all(i.startswith("ae/first/") for i in emitted[0])


@pytest.mark.parametrize("ordinal,start", [(2, 90), (3, 140)])
def test_later_two_layer_context_precision_annotations_ids_and_mutating_sinks(stubbed, monkeypatch, ordinal, start):
    branches, segments, contexts, rows = {}, {}, [], {}
    def branch_sink(identifier, payload):
        branches[identifier] = deepcopy(payload)
        payload["arrays"]["positions"][:] = -1
        payload["summary"]["total_J"] = -999
    def segment_sink(identifier, payload):
        segments[identifier] = deepcopy(payload)
        payload["arrays"]["positions"][:] = -2
        payload["certificate"].clear()
    def candidate_sink(identifier, payload):
        rows[identifier] = payload.copy()
        payload[:] = -3
    actor = stubbed(t=start, branch_sink=branch_sink, segment_sink=segment_sink, candidate_sink=candidate_sink)
    candidates = [plan(start, d, site=i) for i, d in enumerate((10, 20, 30, 40))]
    monkeypatch.setattr(controller, "enumerate_champions", lambda p, u, m, t, h: bank(t, candidates if t == start else []))
    original = deepcopy(actor.controller.__dict__)
    simulate = actor._simulate
    def inspect(identifier, h, r, m, p, **kw):
        result = simulate(identifier, h, r, m, p, **kw)
        if identifier.endswith("/prefix"):
            result["arrays"]["positions"][-1, 0, 0] += .0000001
        contexts.append((identifier, deepcopy(h.__dict__), r.copy(), kw.get("physical_positions")))
        return result
    monkeypatch.setattr(actor, "_simulate", inspect)
    selected, record = actor._rolling_anticipated_selection(report(start), 1, start, ordinal)
    assert not selected["initiated"]
    assert [b["second_t"] for b in record["branches"]] == [start + d for d in (10, 20, 30, 40, 50)]
    for b in record["branches"]:
        scope = f"ae/op{ordinal}/{b['id']}/t{start}/t{b['second_t']}"
        outer = branches[scope + "/outer"]
        assert outer["summary"]["identity"]["ordinal"] == ordinal
        assert len(outer["decisions"]) == 500 - start
        assert sum("predicted_temporal_selection" in d for d in outer["decisions"]) == 1
        assert "predicted_temporal_selection" in outer["decisions"][b["second_t"] - start]
        suffix = next(c for c in contexts if c[0] == scope + "/suffix")
        assert suffix[1]["next_t"] == b["second_t"]
        assert suffix[2][-1] == np.float32(b["second_t"] / 500)
        assert not np.array_equal(suffix[3], decode_public_state(suffix[2], 8)[0])
        assert scope + "/bank" in rows and scope + "/prefix" in segments and scope + "/suffix" in segments
    assert all(np.array_equal(getattr(actor.controller, k), v) for k, v in original.items())
    assert all(i.startswith(f"ae/op{ordinal}/") and f"/t{start}/" in i for i in branches)


def test_stay_consumes_expired_plan_and_can_remute_allowing_earlier_member_again(stubbed, monkeypatch):
    actor = stubbed("G_E4")
    original = actor.controller
    class RemutingProgram(StubProgram):
        def select(self, t, state, mask):
            command, mask, decision = super().select(t, state, mask)
            if t == 60 and decision["phase"] == "ordinary":
                mask = 1  # synthetic E remutes the previous mover only AFTER t60 selection.
                decision["issued_mask"] = mask
            return command, mask, decision
    monkeypatch.setattr(controller, "OptionProgram", RemutingProgram)
    contexts = []
    def choose(history, state, mask, t, scope, first):
        contexts.append((t, mask, actor.plan, history is original))
        if t in (40, 70):
            selected = plan(t, member=1)
            assert not mask & 2
        else:
            selected = bank(t, [])["original_R"]
            assert mask & 2  # immediate previous initiated mover still active at t60/t90.
        return selected, {"selected_branch": option.branch_id(selected)}
    monkeypatch.setattr(actor, "_ordinary_selection", choose)
    mask = 1
    for t in range(40, 131):
        _, mask, _ = actor.select(t, report(t) if t % 10 == 0 else None, mask)
    assert actor.opportunity_times == [40, 60, 70, 90]
    assert [(t, mask) for t, mask, _, _ in contexts] == [(40, 1), (60, 3), (70, 1), (90, 3)]
    assert contexts[1][2]["initiated"] and not contexts[2][2]["initiated"]
    assert all(same for _, _, _, same in contexts)
    assert actor.plans[40]["member"] == actor.plans[70]["member"] == 1
    assert not actor.plan["initiated"] and actor.plan["start_t"] == 90
    assert actor.next_opportunity_t is None


def test_sink_failure_propagates_without_consuming_or_retrying_selection(stubbed, monkeypatch):
    calls = []
    def broken(identifier, payload):
        calls.append(identifier)
        raise RuntimeError("synthetic sink failure")
    actor = stubbed(segment_sink=broken)
    monkeypatch.setattr(actor, "_bank", lambda h, r, m, t, identifier: bank(t, []))
    with pytest.raises(RuntimeError, match="synthetic sink failure"):
        actor.select(40, report(), 1)
    assert calls == ["ae/first/stay/t50/prefix"]
    assert actor.opportunity_times == [] and actor.selections == {} and actor.plans == {}
    assert actor.controller.next_t == 40 and actor.next_opportunity_t == 40


def test_adapter_clock_validation_preserves_frozen_allowlist():
    from experiments.candidates.uav_planning_opportunity_timing.b01 import option as first_option
    assert first_option.STARTS == (40, 50, 60, 70, 80, 90)
    for start, end in ((39, 50), (195, 210), (200, 210), (190, 190), (190, 501)):
        with pytest.raises(ValueError):
            segment.simulate_segment(StubHistory(start), report(start), 1, start_t=start, end_t=end, dependencies=DEPS)
    with pytest.raises(ValueError):
        segment.simulate_segment(StubHistory(190), report(190), 1, start_t=190, end_t=200,
                                 report_horizon=200, dependencies=DEPS)


@pytest.mark.parametrize("initiated", [False, True])
def test_later_selected_suffix_certificate_full_reference_clock_and_plan_binding(initiated):
    start = 190
    h = StubHistory(start)
    commitment = plan(start, 40) if initiated else bank(start, [])["original_R"]
    outer = h.positions.copy()
    outer[0, 0] += .0000001
    kw = dict(start_t=start, end_t=500, physical_positions=outer, dependencies=DEPS)
    full = segment.simulate_segment(h, report(start), 1, commitment, reuse=False, **kw)
    reused = segment.simulate_segment(h, report(start), 1, commitment, reuse=True, **kw)
    reference = SimpleNamespace(payload={k: full[k] for k in ("arrays", "summary", "decisions")},
        start=start, end=500, kind="suffix", entry_mask=1, entry_commands=h.commands.copy(),
        entry_users=h.users.copy(), expected_plan=commitment, plan_bound=True)
    identifier = "ae/op3/m1_s0/t140/t190/suffix"
    record = dict(id=identifier, certificate=reused["certificate"], scientific=certificate_reader.payload_binding(reference.payload))
    certificate_reader.verify_certificate(identifier, record, reference, True)
    for key in full["arrays"]:
        assert reused["arrays"][key].tobytes() == full["arrays"][key].tobytes()
    changed = deepcopy(record)
    changed["certificate"]["start_t"] = 180
    with pytest.raises(ValueError):
        certificate_reader.verify_certificate(identifier, changed, reference, True)
    changed = deepcopy(record)
    changed["certificate"]["plan"]["start_t"] = 180
    with pytest.raises(ValueError):
        certificate_reader.verify_certificate(identifier, changed, reference, True)
    changed = deepcopy(record)
    wrong_report = report(180)
    changed["certificate"]["entry_report"]["hex"] = wrong_report.tobytes().hex()
    with pytest.raises(ValueError):
        certificate_reader.verify_certificate(identifier, changed, reference, True)
