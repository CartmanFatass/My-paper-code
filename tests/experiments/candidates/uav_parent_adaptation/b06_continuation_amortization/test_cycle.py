"""Synthetic checks; three paid replays require explicit, separately costed opt-in."""

from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import time

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import cycle


def _history():
    state = np.zeros(133, dtype=np.float32)
    state[:24].reshape(8, 3)[:, :2] = .5
    state[24:32] = 1
    state[32:132] = np.linspace(.1, .9, 100, dtype=np.float32)
    state[-1] = np.float32(40 / 500)
    controller = OrdinaryController(8)
    controller.positions, controller.users = decode_public_state(state, 8)
    controller.next_t = 40
    return controller, state


def _synthetic(monkeypatch, *, drift=False, clipping=False):
    calls, score_calls = [], []

    class Program:
        def __init__(self, arm, horizon=500):
            self.controller = None
            self.plan = None

        def select(self, t, state, old_mask):
            assert t == self.controller.next_t
            assert (state is not None) == (t % 10 == 0)
            calls.append(t)
            command = np.zeros((8, 3), dtype=np.float32)
            if clipping:
                command[:, 0] = -1
            self.controller.commands = command.copy()
            self.controller.next_t += 1
            if drift:
                self.controller.positions[0, 1] += 1e-10
            elif clipping:
                self.controller.positions = cycle.predict_next(self.controller.positions, command)
            phase = "ordinary"
            if self.plan is not None and self.plan["initiated"]:
                if t < self.plan["arrival_t"]:
                    phase = "transit"
                elif t == self.plan["arrival_t"]:
                    phase = "arrival"
            counts = dict(requested_candidates=2, scored_candidates=2, cached_candidates=0,
                          geometry_rows_computed=8, geometry_rows_reused=8)
            decision = dict(t=t, old_mask=old_mask, issued_mask=old_mask, phase=phase,
                            motion=dict(counts, member_order=[(t + i) % 8 for i in range(8)],
                                        nested={"mutable": [t % 40]}))
            if t % 10 == 0:
                decision["mask"] = dict(counts)
            return command, old_mask, decision

    class Scores:
        def __init__(self, users):
            self.counts = {key: 0 for key in cycle.COUNT_KEYS}

        def score(self, positions, masks):
            score_calls.append(calls[-1])
            self.counts.update(requested_candidates=1, scored_candidates=1, geometry_rows_computed=8)
            j = [1e16, 1., -1e16, .1][calls[-1] % 4]
            return [dict(J=j, served=1, quality=.1, energy_penalty=.00375)]

    monkeypatch.setattr(cycle, "Program", Program)
    monkeypatch.setattr(cycle, "_Scores", Scores)
    return calls, score_calls


def _assert_counts(result):
    reuse, summary = result["reuse"], result["summary"]
    assert reuse["computed_ticks"] + reuse["reused_ticks"] == summary["model_transitions"]
    assert reuse["logical_controller_counts"] == summary["controller_counts"]
    assert reuse["logical_reward_counts"] == summary["reward_counts"]
    assert reuse["actual_controller_calls"] == reuse["actual_reward_calls"] == reuse["computed_ticks"]
    assert reuse["logical_controller_calls"] == reuse["logical_reward_calls"] == summary["model_transitions"]
    assert reuse["actual_requested_candidates"] <= reuse["logical_requested_candidates"]
    assert len(reuse["source_times"]) == summary["model_transitions"]
    for index, source in enumerate(reuse["source_times"]):
        t = 40 + index
        assert source <= t
        if source != t:
            assert source > reuse["eligibility_after_t"] and source % 40 == t % 40
            assert reuse["source_times"][source - 40] == source


def test_key_all_bits_phase_mask_and_static_user_fields():
    controller, state = _history()
    positions = controller.positions.copy()
    key = cycle.recurrence_key(41, positions, controller, 1, state)
    assert key == cycle.recurrence_key(81, positions, controller, 1, state)
    assert key != cycle.recurrence_key(42, positions, controller, 1, state)
    assert key != cycle.recurrence_key(41, positions, controller, 2, state)
    changed = positions.copy()
    changed[0, 0] = np.nextafter(changed[0, 0], np.inf)
    assert key != cycle.recurrence_key(41, changed, controller, 1, state)
    changed_controller = deepcopy(controller)
    changed_controller.positions[0, 0] = np.nextafter(changed_controller.positions[0, 0], np.inf)
    assert key != cycle.recurrence_key(41, positions, changed_controller, 1, state)
    changed_controller = deepcopy(controller)
    changed_controller.commands[0, 0] = np.float32(-0.)
    assert key != cycle.recurrence_key(41, positions, changed_controller, 1, state)
    changed_state = state.copy()
    changed_state[32] = np.nextafter(changed_state[32], np.float32(np.inf))
    assert key != cycle.recurrence_key(41, positions, controller, 1, changed_state)
    changed_state = state.copy()
    changed_state[-1] = .9
    assert key == cycle.recurrence_key(41, positions, controller, 1, changed_state)


def test_exact_reuse_absolute_clock_reports_deepcopy_and_fp_order(monkeypatch):
    calls, score_calls = _synthetic(monkeypatch)
    controller, state = _history()
    original = deepcopy(controller)
    result = cycle.simulate_continuation(controller, state, 1, horizon=200)
    _assert_counts(result)
    reuse = result["reuse"]
    assert reuse["computed_ticks"] == 41 and reuse["reused_ticks"] == 119
    assert calls == score_calls == list(range(40, 81))
    assert reuse["first_repeat"]["source_t"] == 41 and reuse["first_repeat"]["repeat_t"] == 81
    assert reuse["first_repeat"]["period"] == 40
    positions = result["arrays"]["positions"]
    witness = cycle.recurrence_key(41, positions[1], original, 1, state)
    assert reuse["first_repeat"]["key_sha256"] == hashlib.sha256(witness).hexdigest()
    assert [decision["t"] for decision in result["decisions"]] == list(range(40, 200))
    for index, report_t in enumerate(result["arrays"]["report_times"]):
        report = result["arrays"]["reports"][index]
        assert report[-1] == (state[-1] if report_t == 40 else np.float32(report_t / 200))
        assert report[32:132].tobytes() == state[32:132].tobytes()
    expected_j, expected_q, expected_h = 0., 0., 0.
    for t in range(40, 200):
        expected_j += [1e16, 1., -1e16, .1][t % 4]
        expected_q += .1
        expected_h += .00375
    assert result["summary"]["total_J"] == expected_j
    assert result["summary"]["total_quality"] == expected_q
    assert result["summary"]["total_energy_penalty"] == expected_h
    assert result["summary"]["total_J"] != sum([1e16, 1., -1e16, .1]) * 40
    assert result["summary"]["total_path"] == 0
    result["decisions"][41]["motion"]["nested"]["mutable"][0] = -1
    assert result["decisions"][1]["motion"]["nested"]["mutable"] == [1]
    assert result["decisions"][81]["motion"]["nested"]["mutable"] == [1]
    assert controller.next_t == 40
    assert controller.commands.tobytes() == original.commands.tobytes()
    assert controller.positions.tobytes() == original.positions.tobytes()


def test_no_recurrence_executes_entire_suffix(monkeypatch):
    calls, score_calls = _synthetic(monkeypatch, drift=True)
    controller, state = _history()
    result = cycle.simulate_continuation(controller, state, 1, horizon=150)
    _assert_counts(result)
    assert calls == score_calls == list(range(40, 150))
    assert result["reuse"]["computed_ticks"] == 110
    assert result["reuse"]["first_repeat"] is None and result["reuse"]["reused_ticks"] == 0


def test_arrival_barrier_and_input_plan_immutability(monkeypatch):
    calls, _ = _synthetic(monkeypatch)
    controller, state = _history()
    plan = dict(initiated=True, duration=40, arrival_t=80, member=1,
                commands=np.zeros((40, 8, 3), dtype=np.float32),
                predicted_destination=controller.positions.copy())
    original = deepcopy(plan)
    result = cycle.simulate_continuation(controller, state, 1, plan, horizon=200)
    _assert_counts(result)
    assert calls == list(range(40, 121))
    assert result["reuse"]["first_repeat"]["source_t"] == 81
    assert result["reuse"]["first_repeat"]["repeat_t"] == 121
    assert result["decisions"][40]["phase"] == "arrival"
    assert all(d["phase"] == "ordinary" for d in result["decisions"][41:])
    assert np.array_equal(plan["commands"], original["commands"])
    assert np.array_equal(plan["predicted_destination"], original["predicted_destination"])


def test_clipping_retains_nonzero_issued_commands_and_path_accumulation(monkeypatch):
    _synthetic(monkeypatch, clipping=True)
    controller, state = _history()
    state[:24].reshape(8, 3)[:, 0] = 0
    controller.positions, controller.users = decode_public_state(state, 8)
    result = cycle.simulate_continuation(controller, state, 1, horizon=200)
    _assert_counts(result)
    assert result["reuse"]["first_repeat"]["repeat_t"] == 81
    assert np.all(result["arrays"]["actions"][:, :, 0] == -1)
    assert np.all(result["arrays"]["positions"][:, :, 0] == 0)
    assert result["summary"]["total_path"] == 0


@pytest.mark.parametrize("horizon", [40, 501, True, 41.5])
def test_invalid_horizons_rejected(horizon):
    controller, state = _history()
    with pytest.raises(ValueError):
        cycle.simulate_continuation(controller, state, 1, horizon=horizon)


def _bound_content(root, binding):
    content = (root / binding["path"]).read_bytes()
    assert len(content) == binding["bytes"]
    assert hashlib.sha256(content).hexdigest() == binding["sha256"]
    return content


@pytest.mark.skipif(os.environ.get("HMASD_B06_PAID_CYCLE_CHECKS") != "1",
                    reason="three paid replays require explicit correctness-budget opt-in")
@pytest.mark.parametrize("world,branch_id", [(29326000, "stay"), (29326000, "m2_s23"), (29326002, "m4_s33")])
def test_paid_saved_branch_exact_identity(world, branch_id):
    # Never call the frozen full reference or a native environment here. Expected
    # arrays, decisions and totals are the already-paid original archived bytes.
    root = Path(__file__).resolve().parents[5] / "runs/uav_fleet_transmission/b03_complete_continuation_a02"
    summary_content = (root / "summary.json").read_bytes()
    assert hashlib.sha256(summary_content).hexdigest() == "df0d60b900d816bc93fed1855feca1afc9050dc2b719b017a7beb5d159a5cd7d"
    summary = json.loads(summary_content)
    episode = next(e for e in summary["episodes"] if e["arm"] == "T" and e["world_id"] == world)
    branch = next(b for b in episode["model_branches"] if b["id"] == branch_id)
    if world == 29326002:
        assert episode["continuation"]["original_R_branch"] == branch_id
    _bound_content(root, branch["raw"])
    _bound_content(root, episode["raw"])
    with np.load(root / branch["raw"]["path"]) as archive:
        expected_arrays = {key: archive[key].copy() for key in archive.files}
    stay = next(b for b in episode["model_branches"] if b["id"] == "stay")
    _bound_content(root, stay["raw"])
    with np.load(root / stay["raw"]["path"]) as archive:
        report = archive["reports"][0].copy()
        estimates = archive["controller_estimates"][0].copy()
    controller = OrdinaryController(8)
    controller.positions = estimates
    _, controller.users = decode_public_state(report, 8)
    controller.next_t = 40
    with np.load(root / episode["raw"]["path"]) as archive:
        controller.commands = archive["actions"][39].copy()
    _bound_content(root, episode["decisions"])
    with gzip.open(root / episode["decisions"]["path"], "rt") as stream:
        decision40 = next(json.loads(line) for line in stream if json.loads(line)["t"] == 40)
    branch_record = next(b for b in decision40["continuation"]["branches"] if b["id"] == branch_id)
    plan = branch_record["plan"]
    _bound_content(root, branch["decisions"])
    with gzip.open(root / branch["decisions"]["path"], "rt") as stream:
        expected_decisions = [json.loads(line) for line in stream]
    wall_start, usage_start = time.monotonic(), resource.getrusage(resource.RUSAGE_SELF)
    result = cycle.simulate_continuation(controller, report, branch["summary"]["initial_old_mask"], plan)
    usage_end = resource.getrusage(resource.RUSAGE_SELF)
    costs = dict(world=world, branch=branch_id, wall_seconds=time.monotonic() - wall_start,
                 user_seconds=usage_end.ru_utime - usage_start.ru_utime,
                 system_seconds=usage_end.ru_stime - usage_start.ru_stime,
                 logical_ticks=result["reuse"]["logical_controller_calls"],
                 actual_ticks=result["reuse"]["computed_ticks"],
                 logical_requests=result["reuse"]["logical_requested_candidates"],
                 actual_requests=result["reuse"]["actual_requested_candidates"],
                 first_repeat=result["reuse"]["first_repeat"])
    print("PAID_CYCLE_CORRECTNESS " + json.dumps(costs, sort_keys=True))
    assert set(result["arrays"]) == set(expected_arrays)
    for key, expected in expected_arrays.items():
        actual = result["arrays"][key]
        assert actual.shape == expected.shape and actual.dtype == expected.dtype, key
        assert actual.tobytes() == expected.tobytes(), key
    assert result["decisions"] == expected_decisions
    assert result["summary"] == branch["summary"]
    _assert_counts(result)
    assert result["reuse"]["first_repeat"] is not None
    assert result["reuse"]["logical_controller_calls"] == 460
    assert result["reuse"]["logical_requested_candidates"] <= 111550
