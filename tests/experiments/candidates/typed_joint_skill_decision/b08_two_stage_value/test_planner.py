"""Synthetic menus/segments only: no radio, motion, native or world queries."""
from copy import deepcopy
import hashlib
from types import FunctionType, MethodType, SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import planner as p
from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, empty_counts


def report_at(t=40):
    report = np.zeros(133, np.float32)
    report[:24] = np.tile([.1, .2, .3], 8)
    report[24:32] = 1
    report[132] = np.float32(t / 500)
    return report


def plan(member, *, t=40, value=-1., path=3., site=None):
    site = member if site is None else site
    selected = dict(predicted_total_J=value, predicted_total_served=10,
        path=path, duration=10, member=member, site=site)
    return dict(initiated=True, member=member, site=site, selected=selected,
        duration=10, arrival_t=t+10, start_t=t, offsets=[0, 0],
        # Zero-displacement commitment remains initiated, with explicit commands.
        commands=np.zeros((10, 8, 3), np.float32).tolist(),
        predicted_destination=np.zeros((8, 3), np.float64).tolist(),
        predicted_mask=1 | (1 << member), predicted_total_J=value,
        predicted_total_served=10, stay_score=dict(J=0., served=0),
        stay_total_J=0., stay_total_served=0,
        candidate_count=0, candidate_digest="", digest_layout=[], counts={})


def bank(champions, t):
    champions = deepcopy(champions)
    for candidate in champions:
        candidate.update(start_t=t, arrival_t=t+candidate["duration"])
    # Include duplicate rows to verify that aliases are not removed.
    rows = np.asarray([[1., 2.], [1., 2.], [3., 4.]], dtype="<f8")
    original = deepcopy(max(champions, key=lambda c: p.stationary_rank(c["selected"]))) if champions else dict(
        initiated=False, member=None, site=None, selected=None, commands=[], duration=0,
        arrival_t=None, offsets=None, predicted_destination=np.zeros((8, 3)).tolist(),
        predicted_mask=None, stay_total_J=0., stay_total_served=0.,
        predicted_total_J=0., predicted_total_served=0., stay_score=dict(J=0., served=0))
    if original["predicted_total_J"] <= 0:
        original.update(initiated=False, member=None, site=None, duration=0,
            commands=[], arrival_t=None, predicted_mask=None)
    original.update(candidate_count=len(rows), candidate_digest=hashlib.sha256(rows.tobytes()).hexdigest(),
        digest_layout=["x", "y"], counts={"requested_candidates": 99}, start_t=t)
    return dict(champions=champions, original_R=original, candidate_rows=rows)


class MockExecution:
    def __init__(self, controller, plan=None):
        self.controller, self.plan, self.option_old_mask = controller, deepcopy(plan), None
        self.calls = []

    def select(self, t, report, mask):
        assert t == self.controller.next_t
        self.calls.append(t)
        self.controller.next_t += 1
        return self.controller.commands.copy(), mask, {"t": t}


class SyntheticProgram(p.BudgetedProgram):
    """Replaces all scoring and physical transitions with prescribed arrays."""
    def __init__(self, arm, champions=None, second=None, **kwargs):
        super().__init__(arm, **kwargs)
        self.champions = deepcopy(champions if champions is not None else [plan(1), plan(2), plan(3)])
        self.second = deepcopy(second if second is not None else [plan(4), plan(5)])
        self.events, self.c_calls, self.segment_calls = [], [], []
        self.one_values, self.outer_values, self.inner_values = {}, {}, {}
        history = SimpleNamespace(next_t=40, n_uavs=8,
            positions=np.full((8, 3), 111.123456789, np.float64),
            users=np.zeros((50, 2), np.float64), commands=np.ones((8, 3), np.float32))
        self.base = MockExecution(history)
        if self._first is not None:
            self._first.base = self.base

    def _bank(self, controller, report, mask, start_t, identifier):
        self.events.append(("bank", identifier))
        result = bank(self.champions if start_t == 40 else self.second, start_t)
        self._banks[identifier] = deepcopy({k: result["original_R"][k] for k in (
            "candidate_count", "candidate_digest", "counts", "digest_layout")})
        self._banks[identifier]["start_t"] = start_t
        if self.candidate_sink is not None:
            self.candidate_sink(identifier, result["candidate_rows"].copy())
        return result

    def _payload(self, controller, report, mask, plan, start_t, end_t, physical=None, identifier=""):
        h = end_t-start_t
        decoded = p.decode_public_state(report, 8)[0]
        positions = np.repeat((decoded if physical is None else physical)[None], h+1, axis=0)
        # A deliberately unrepresentable FP32 endpoint, not simulated movement.
        if start_t == 40 and end_t == 120:
            positions[-1] = 123.123456789 + (0 if plan is None else plan["member"])
        local = p.branch_id(plan)
        value, served = self.inner_values.get(local, (0., 0))
        if identifier.endswith("/suffix"):
            first = identifier.split("/")[2]
            value, served = self.outer_values.get(first, (0., 0))
        if start_t == 40:
            value, served = (0., 0) if end_t == 120 else self.one_values.get(local, (0., 0))
        rewards = np.zeros((h, 4), np.float64)
        rewards[0, :2] = [value, served]
        arrays = dict(positions=positions, controller_estimates=positions.copy(),
            actions=np.zeros((h, 8, 3), np.float32), masks=np.full(h, mask, np.int64),
            reward_components=rewards, report_times=np.arange(start_t, end_t, 10, dtype=np.int64),
            reports=np.repeat(report[None], len(range(start_t, end_t, 10)), axis=0))
        terminal = deepcopy(controller)
        terminal.next_t, terminal.positions = end_t, positions[-1].copy()
        cc, rc = empty_counts(), {k: 0 for k in COUNT_KEYS}
        summary = dict(start_t=start_t, end_t=end_t, horizon=500, total_J=value, total_served=served,
            controller_counts=cc, reward_counts=rc, model_transitions=h)
        return dict(arrays=arrays, summary=summary, decisions=[dict(t=t) for t in range(start_t, end_t)],
            terminal_controller=terminal, terminal_mask=mask,
            certificate=dict(start_t=start_t, end_t=end_t, entry_report=report.copy(),
                reuse=dict(logical_reward_calls=h, actual_reward_calls=h)))

    def _simulate(self, identifier, controller, report, mask, plan, **kwargs):
        self.events.append(("segment", identifier))
        self.segment_calls.append(dict(id=identifier, report=report.copy(), history=deepcopy(controller),
            mask=mask, plan=deepcopy(plan), **deepcopy(kwargs)))
        result = self._payload(controller, report, mask, plan, kwargs["start_t"],
            kwargs.get("end_t", 500), kwargs.get("physical_positions"), identifier)
        p._finite_summary(result)
        self._emit_segment(identifier, result)
        return result

    def _c_only(self, identifier, report, mask, plan):
        self.events.append(("c_only", identifier))
        self.c_calls.append((identifier, p.branch_id(plan)))
        result = self._payload(self.controller, report, mask, plan, 40, 500)
        p._finite_summary(result)
        self._emit_segment(identifier, result)
        return result

    def _install(self, selected, old_mask):
        self.base = MockExecution(self.controller, selected)
        self.base.option_old_mask = old_mask


def first_record(program):
    return program.prepare_first(report_at(), 1)[1]


def test_k2_c_only_nonstay_rank_and_complete_charged_tree():
    branches, segments, candidates, menus = [], [], [], []
    program = SyntheticProgram("K2-C", branch_sink=lambda i, x: branches.append((i, x)),
        segment_sink=lambda i, x: segments.append((i, x)),
        candidate_sink=lambda i, x: candidates.append((i, x)),
        menu_sink=lambda **x: menus.append(x))
    program.one_values = {"m1_s1": (-5., 0), "m2_s2": (-3., 3), "m3_s3": (-3., 4)}
    record = first_record(program)
    assert [local for _, local in program.c_calls] == ["m1_s1", "m2_s2", "m3_s3"]
    assert all(i.startswith("k2-c/rank/t40/branch/") for i, _ in program.c_calls)
    assert record["allocation"]["retained_first_ids"] == ["stay", "m2_s2", "m3_s3"]
    assert record["allocation"]["ranked_nonstay_ids"] == ["m3_s3", "m2_s2", "m1_s1"]
    assert len(branches) == 3 + 3*(3+1)  # rank, every inner, every outer
    assert len(segments) == 3 + 3*(1+3+1)  # rank, prefix, every inner, suffix
    assert len(candidates) == 4 and len(menus) == 1
    assert len(record["branches"]) == 3
    assert all("certificate" in payload for _, payload in segments)
    assert sum(x["certificate"]["reuse"]["logical_reward_calls"] for _, x in segments) == 3*460 + 3*(80+3*380+380)


def test_k2_c_complete_value_ties_use_path_not_stationary_j():
    program = SyntheticProgram("K2-C", [plan(1, value=-10., path=1.),
        plan(2, value=-2., path=100.), plan(3, value=-3., path=2.)])
    program.one_values = {"m1_s1": (1., 10), "m2_s2": (1., 10), "m3_s3": (1., 10)}
    allocation = first_record(program)["allocation"]
    assert allocation["ranked_nonstay_ids"] == ["m1_s1", "m3_s3", "m2_s2"]
    assert allocation["retained_first_ids"] == ["stay", "m1_s1", "m3_s3"]
    assert [row["stationary_key"][0] for row in allocation["candidates"]] == [-10., -2., -3.]
    assert allocation["candidates"][0]["allocation_key"] == [1., 10, -1., -10, -1, -1]


def test_k2_s_no_c_queries_and_l2_equal_score_stationary_ties():
    champions = [plan(1, value=-10.), plan(2, value=-2.), plan(3, value=-3.)]
    ordinary = SyntheticProgram("K2-S", champions)
    learned = SyntheticProgram("L2", champions,
        scorer=lambda *args: np.full(len(args[-1]), -100., np.float32))
    for program in (ordinary, learned):
        record = first_record(program)
        assert record["allocation"]["retained_first_ids"] == ["stay", "m2_s2", "m3_s3"]
        assert record["allocation"]["excluded_first_ids"] == ["m1_s1"]
        assert program.c_calls == []
    assert learned.selections[40]["allocation"]["scores"] == [-100.]*4


@pytest.mark.parametrize("arm", ["A2", "K2-C", "K2-S", "L2"])
def test_declines_equal_j_regardless_service(arm):
    program = SyntheticProgram(arm, scorer=lambda *args: np.zeros(len(args[-1]), np.float32))
    program.outer_values = {"stay": (2., 1), "m1_s1": (2., 100), "m2_s2": (1., 100)}
    record = first_record(program)
    assert record["selected_branch"] == "stay" and not record["selected_plan"]["initiated"]
    assert not record["strict_model_improvement_over_stay"]
    assert all(len(b["choice_key"]) == 6 for b in record["branches"])


def test_g2_exact_one_stage_rule_ids_and_native_installation():
    program = SyntheticProgram("G2")
    program.one_values = {"stay": (1., 1), "m1_s1": (1., 100)}
    _, _, decision = program.select(40, report_at(), 1)
    record = program.selections[40]
    assert record["selected_branch"] == "stay"
    assert record["bank_id"] == "actual/t40/bank"
    assert len(program.c_calls) == 4 and not program.segment_calls
    assert all(i.startswith("actual/t40/branch/") for i, _ in program.c_calls)
    assert decision["continuation"]["selected_branch"] == "stay"
    assert decision["option"] == program.plan
    assert program.controller.next_t == 41


@pytest.mark.parametrize("count", [0, 1, 2, 7])
@pytest.mark.parametrize("arm", ["A2", "K2-C", "K2-S", "L2"])
def test_fewer_than_two_or_zero_champions_and_full_menu_limit(count, arm):
    seen = []
    program = SyntheticProgram(arm, [plan(i+1) for i in range(count)],
        scorer=lambda *args: np.arange(len(args[-1]), dtype=np.float32),
        menu_sink=lambda **x: seen.append(x))
    record = first_record(program)
    assert len(seen[0]["plans"]) == count+1
    assert record["allocation"]["retained_first_ids"][0] == "stay"
    assert len(record["branches"]) == 1+(count if arm == "A2" else min(count, 2))
    assert len(program.c_calls) == (count if arm == "K2-C" else 0)


def test_nonpositive_and_zero_displacement_champions_and_site_alias_rows_retained():
    menu, rows = [], []
    program = SyntheticProgram("A2", [plan(1, site=0), plan(2, site=0)],
        menu_sink=lambda **x: menu.append(x), candidate_sink=lambda i, x: rows.append(x))
    record = first_record(program)
    assert record["allocation"]["all_first_ids"] == ["stay", "m1_s0", "m2_s0"]
    assert all(option["initiated"] and np.count_nonzero(option["commands"]) == 0 for option in menu[0]["plans"][1:])
    assert np.array_equal(rows[0][0], rows[0][1]) and len(rows[0]) == 3
    assert set(record["Q2"]) == {"stay", "m1_s0", "m2_s0"}


def test_inner_report_decodes_fp32_but_outer_suffix_uses_unrounded_fp64():
    program = SyntheticProgram("A2", [plan(1)])
    first_record(program)
    for first in ("stay", "m1_s1"):
        suffix = next(c for c in program.segment_calls if c["id"] == f"a2/first/{first}/suffix")
        inner = next(c for c in program.segment_calls if c["id"] == f"a2/first/{first}/inner/stay")
        rounded = p.decode_public_state(inner["report"], 8)[0]
        assert inner["report"].dtype == np.float32
        assert suffix["physical_positions"].dtype == np.float64
        assert not np.array_equal(rounded, suffix["physical_positions"])
        assert "physical_positions" not in inner


def test_prepare_once_no_install_action_or_history_mutation_and_all_a2_labels():
    program = SyntheticProgram("A2")
    history, base = deepcopy(program.controller), program.base
    selected, record = program.prepare_first(report_at(), 1)
    assert program.base is base and program.plan is None and base.calls == []
    assert program.controller.next_t == 40
    assert np.array_equal(history.positions, program.controller.positions)
    assert np.array_equal(history.commands, program.controller.commands)
    assert len(record["Q2"]) == 4
    selected["initiated"] = True
    record["Q2"].clear()
    assert len(program.selections[40]["Q2"]) == 4
    with pytest.raises(ValueError, match="unused lawful"):
        program.prepare_first(report_at(), 1)
    with pytest.raises(ValueError, match="repeated"):
        program.select(40, report_at(), 1)


@pytest.mark.parametrize("arm", ["G2", "A2", "K2-C", "K2-S", "L2"])
def test_actual120_always_replans_full_menu_from_actual_report_and_history(arm):
    program = SyntheticProgram(arm, scorer=lambda *args: np.zeros(len(args[-1]), np.float32))
    program.select(40, report_at(), 1)
    # Explicit mock boundary advancement; no hidden native/physical transitions.
    program.controller.next_t = 120
    program.controller.positions.fill(777.)
    program.inner_values = {"m4_s4": (4., 10)}
    actual_report = report_at(120)
    actual_report[0] = np.float32(.87654321)
    _, _, decision = program.select(120, actual_report, 1)
    record = program.selections[120]
    assert record["bank_id"] == "actual/t120/bank"
    assert record["selected_branch"] == "m4_s4" and len(record["branches"]) == 3
    actual_calls = [c for c in program.segment_calls if c["id"].startswith("actual/t120/branch/")]
    assert len(actual_calls) == 3 and all(np.array_equal(c["report"], actual_report) for c in actual_calls)
    assert all(np.array_equal(c["history"].positions, np.full((8, 3), 777.)) for c in actual_calls)
    assert program.controller.next_t == 121 and decision["temporal"]["selected_branch"] == "m4_s4"
    with pytest.raises(ValueError):
        program.select(120, actual_report, 1)


@pytest.mark.parametrize("arm", ["G2", "A2", "K2-C", "K2-S", "L2"])
def test_callbacks_and_scorer_cannot_mutate_retained_policy_state_or_each_other(arm):
    seen = []
    def menu_sink(**data):
        assert not program.c_calls and not program.segment_calls
        seen.append(tuple(data))
        data["report"].fill(999.)
        data["history"].positions.fill(999.)
        data["commands"].fill(-1.)
        data["plans"].clear()
        data["bank"]["champions"].clear()
    def scorer(report, history, mask, bank, plans):
        assert report[0] != 999. and history.positions[0, 0] != 999.
        assert len(bank["champions"]) == 3 and len(plans) == 4
        scores = np.zeros(len(plans), np.float32)
        report.fill(999.)
        history.positions.fill(999.)
        bank["champions"].clear()
        plans.clear()
        return scores
    def branch_sink(identifier, data):
        data["summary"]["total_J"] = 1e100
        data["arrays"]["positions"].fill(999.)
        data["decisions"].clear()
    def segment_sink(identifier, data):
        data["certificate"].clear()
        branch_sink(identifier, data)
    def candidate_sink(identifier, rows):
        rows.fill(999.)
    program = SyntheticProgram(arm, scorer=scorer, menu_sink=menu_sink,
        branch_sink=branch_sink, segment_sink=segment_sink, candidate_sink=candidate_sink)
    original_report, original_history = report_at(), deepcopy(program.controller)
    record = program.prepare_first(original_report, 1)[1]
    assert set(seen[0]) == {"start_t", "report", "commands", "history", "mask", "bank", "plans"}
    assert original_report[0] == np.float32(.1)
    assert np.array_equal(program.controller.positions, original_history.positions)
    assert all(b["summary"]["total_J"] == 0. for b in record["branches"])
    assert record["selected_branch"] == "stay"
    properties = [program.selections, program.plans, program.banks, program.plan]
    properties[0].clear(); properties[1].clear(); properties[2].clear()
    assert program.selections and program.plans and program.banks and properties[3] is None


@pytest.mark.parametrize("scores", [np.array([0., 1., 2., 3.], np.float64),
    np.array([0., 1.], np.float32), np.array([0., np.nan, 2., 3.], np.float32),
    np.array([0., np.inf, 2., 3.], np.float32)])
def test_invalid_scorer_output_stops_first_choice(scores):
    program = SyntheticProgram("L2", scorer=lambda *args: scores)
    with pytest.raises(ValueError, match="finite FP32"):
        first_record(program)
    assert not program.segment_calls
    with pytest.raises(ValueError, match="twice"):
        first_record(program)


@pytest.mark.parametrize("reuse", [False, True])
def test_kernel_bindings_route_reuse_and_full_paths_locally(monkeypatch, reuse):
    program = p.BudgetedProgram("A2", reuse=reuse)
    calls, certs, outputs = [], [], []
    def mock_segment(*args, **kwargs):
        calls.append(("segment", kwargs))
        return dict(summary=dict(total_J=1., total_served=2), arrays={}, decisions=[], certificate={})
    def mock_c(name):
        def kernel(*args):
            calls.append((name, args))
            return dict(summary=dict(total_J=1., total_served=2), arrays={}, decisions=[],
                reuse={"schema": "exact_ordinary_recurrence.v1"} if name == "cycle" else None)
        return kernel
    def mock_certify(result, *args, **kwargs):
        certs.append(kwargs)
        result["certificate"] = {"reuse": kwargs["reuse"]}
    monkeypatch.setattr(p, "simulate_segment", mock_segment)
    monkeypatch.setattr(p, "simulate_c_only", mock_c("cycle"))
    monkeypatch.setattr(p, "simulate_c_only_full", mock_c("full"))
    monkeypatch.setattr(p, "certify", mock_certify)
    program.segment_sink = lambda i, data: outputs.append((i, data))
    program._simulate("prefix", program.controller, report_at(), 1, None, start_t=40, end_t=120)
    program._c_only("k2-c/rank/t40/branch/m1_s1", report_at(), 1, plan(1))
    assert calls[0][1]["reuse"] is reuse
    assert calls[1][0] == ("cycle" if reuse else "full")
    assert certs[0]["reuse"] == ({"schema": "exact_ordinary_recurrence.v1"} if reuse else None)
    assert outputs[1][0] == "k2-c/rank/t40/branch/m1_s1"


def test_invalid_arm_horizon_missing_scorer_and_wrong_clock():
    for arm, kwargs in [("X", {}), ("A2", {"horizon": 499}), ("L2", {})]:
        with pytest.raises(ValueError):
            p.BudgetedProgram(arm, **kwargs)
    program = SyntheticProgram("A2")
    program.controller.next_t = 39
    with pytest.raises(ValueError, match="unused lawful"):
        program.prepare_first(report_at(), 1)
    with pytest.raises(ValueError):
        program.select(40, report_at(), 1)
    assert not program.events


def assert_payload_bits_equal(left, right):
    assert left.keys() == right.keys()
    for key in left["arrays"]:
        a, b = left["arrays"][key], right["arrays"][key]
        assert a.shape == b.shape and a.dtype == b.dtype and a.tobytes() == b.tobytes()
    assert left["summary"] == right["summary"]
    assert left["decisions"] == right["decisions"]


@pytest.mark.parametrize("arm", ["G2", "A2"])
@pytest.mark.parametrize("tie", [False, True])
def test_g2_a2_match_inherited_selectors_over_identical_synthetic_kernels(arm, tie):
    """Execute the original selector bodies without patching frozen globals.

    The G2 body has no injected enumeration seam, so bind a copy of that same
    function's code to a detached globals dict with a synthetic enumerator.
    This invokes no physical/model/native queries and changes no frozen module.
    """
    saved, reference = [], []
    candidate = SyntheticProgram(arm, branch_sink=lambda i, x: saved.append((i, x)))
    original = SyntheticProgram(arm, branch_sink=lambda i, x: reference.append((i, x)))
    for program in (candidate, original):
        values = {"stay": (2., 1), "m1_s1": (2. if tie else 3., 20), "m2_s2": (1., 100)}
        program.one_values = deepcopy(values)
        program.outer_values = deepcopy(values)
        program.inner_values = {"m4_s4": (1., 3), "m5_s5": (1., 100)}
    original._anticipated_selection = MethodType(p.inherited.TemporalProgram._anticipated_selection, original)
    original._ordinary_selection = MethodType(p.inherited.TemporalProgram._ordinary_selection, original)
    if arm == "G2":
        method = p.inherited._BoundFirst.select
        detached_globals = dict(method.__globals__)
        detached_globals["first"] = SimpleNamespace(
            enumerate_champions=lambda *args: bank(original.champions, 40),
            branch_id=p.branch_id, physical_identity=p.physical_identity)
        copied_method = FunctionType(method.__code__, detached_globals, method.__name__,
            method.__defaults__, method.__closure__)
        original._first.select = MethodType(copied_method, original._first)
        original._first._simulate = lambda controller, report, mask, plan, horizon: original._c_only(
            "actual/t40/branch/"+p.branch_id(plan), report, mask, plan)
    result = candidate.select(40, report_at(), 1)
    expected = p.frozen.TemporalProgram.select(original, 40, report_at(), 1)
    assert np.array_equal(result[0], expected[0]) and result[1] == expected[1]
    assert candidate.plan == original.plan and candidate.plans == original.plans
    actual_record, expected_record = candidate.selections[40], original.selections[40]
    for key in expected_record:
        if key == "branches":
            for actual_branch, expected_branch in zip(actual_record[key], expected_record[key]):
                assert {k: actual_branch[k] for k in expected_branch} == expected_branch
        else:
            assert actual_record[key] == expected_record[key]
    assert candidate.banks == original.banks
    assert [i for i, _ in saved] == [i for i, _ in reference]
    for (_, actual), (_, expected_payload) in zip(saved, reference):
        assert_payload_bits_equal(actual, expected_payload)
