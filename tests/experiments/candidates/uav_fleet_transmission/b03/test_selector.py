"""Constructed shortlist/selection rules; no new result-world queries."""
from copy import deepcopy
import hashlib

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b02 import option as original
from experiments.candidates.uav_fleet_transmission.b02.controller import Program
from experiments.candidates.uav_fleet_transmission.b03 import controller, option
from experiments.candidates.uav_fleet_transmission.b03.host import WORLD_IDS, bound_worlds, seed
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_fleet_transmission.reader import _public_state


def fixture():
    rng = np.random.RandomState(71)
    positions = rng.uniform(0, 1000, (8, 3))
    positions[:, 2] = rng.uniform(50, 150, 8)
    return positions, rng.uniform(0, 1000, (50, 2))


def test_bound_fresh_inputs_only():
    scenes = bound_worlds()
    assert tuple(scenes) == WORLD_IDS
    assert len({s.user_positions.tobytes() for s in scenes.values()}) == 16
    assert len({seed(w, 3, 8) for w in WORLD_IDS}) == 16
    assert all(not s.user_positions.flags.writeable for s in scenes.values())


@pytest.mark.parametrize("mask", [63, 127, 255])
def test_exact_original_enumeration_global_R_and_per_member_champions(mask):
    positions, users = fixture()
    before = positions.copy(), users.copy()
    expected = original.plan_option(positions, users, mask)
    result = option.enumerate_champions(positions, users, mask)
    assert result["original_R"] == expected
    rows = result["candidate_rows"]
    assert rows.dtype == np.dtype("<f8")
    assert hashlib.sha256(rows.tobytes()).hexdigest() == expected["candidate_digest"]
    assert len(rows) == 100 * (8 - mask.bit_count())
    for plan in result["champions"]:
        member_rows = rows[rows[:, 0] == plan["member"]]
        best = max(member_rows, key=lambda r: (r[7], r[8], -r[9], -r[5], -r[0], -r[1]))
        assert plan["initiated"] is True
        assert plan["site"] == int(best[1])
        assert plan["predicted_total_J"] == best[7]
        assert plan["predicted_total_served"] == best[8]
        np.testing.assert_array_equal(plan["predicted_destination"], best[16:].reshape(8, 3))
    if expected["selected"] is not None:
        assert (expected["selected"]["member"], expected["selected"]["site"]) in {
            (p["member"], p["site"]) for p in result["champions"]}
    np.testing.assert_array_equal(positions, before[0])
    np.testing.assert_array_equal(users, before[1])


class ZeroScores:
    def __init__(self, users):
        self.counts = dict(requested_candidates=0, scored_candidates=0, cached_candidates=0,
                           geometry_rows_computed=0, geometry_rows_reused=0)

    def score(self, positions, masks):
        self.counts["requested_candidates"] += len(masks)
        self.counts["scored_candidates"] += len(masks)
        return [dict(J=0., served=0, quality=0., energy_penalty=0.) for _ in masks]


def test_nonpositive_champions_retained_and_stationary_ties(monkeypatch):
    monkeypatch.setattr(option, "_Scores", ZeroScores)
    positions = np.tile([0., 0., 50.], (8, 1))
    result = option.enumerate_champions(positions, np.zeros((50, 2)), 63)
    assert not result["original_R"]["initiated"]
    assert [(p["member"], p["site"]) for p in result["champions"]] == [(6, 0), (7, 0)]
    assert all(p["initiated"] and p["predicted_total_J"] == p["stay_total_J"] == 0.
               for p in result["champions"])
    assert result["original_R"]["selected"]["member"] == 6


def selected_fixture(monkeypatch, values):
    positions = np.tile([0., 0., 50.], (8, 1))
    users = np.zeros((50, 2))
    monkeypatch.setattr(option, "_Scores", ZeroScores)
    shortlist = option.enumerate_champions(positions, users, 63)
    monkeypatch.setattr(controller, "enumerate_champions", lambda *a: deepcopy(shortlist))
    seen = []
    def simulate(history, state, old_mask, plan, horizon):
        identifier = option.branch_id(plan)
        assert history.next_t == 40 and horizon == 500 and old_mask == 63
        seen.append(identifier)
        return {"arrays": {"positions": positions[None], "actions": np.zeros((0, 8, 3), dtype=np.float32),
                           "masks": np.zeros(0, dtype=np.int64)},
                "decisions": [], "summary": dict(total_J=values[identifier][0],
            total_served=values[identifier][1])}
    monkeypatch.setattr(controller, "simulate_continuation", simulate)
    policy = controller.ContinuationProgram()
    policy.controller.next_t = 40
    policy.controller.positions, policy.controller.users = positions.copy(), users.copy()
    policy.controller.commands[:] = [1, -1, 0]
    state = _public_state(positions, users, 40, 500)
    return policy, state, seen


def test_complete_branch_order_strict_tie_decline_and_original_history(monkeypatch):
    policy, state, seen = selected_fixture(monkeypatch, {"stay": (1., 0), "m6_s0": (1., 5), "m7_s0": (1., 6)})
    ordinary = deepcopy(policy.base)
    expected, expected_mask, expected_decision = ordinary.select(40, state, 63)
    action, mask, decision = policy.select(40, state, 63)
    assert seen == ["stay", "m6_s0", "m7_s0"]
    assert not policy.plan["initiated"]
    assert policy.continuation["selected_branch"] == "stay"
    np.testing.assert_array_equal(action, expected)
    assert mask == expected_mask and decision["motion"] == expected_decision["motion"]
    assert decision["mask"] == expected_decision["mask"]
    assert policy.controller.next_t == 41


def test_complete_branch_selection_and_original_forced_execution(monkeypatch):
    policy, state, seen = selected_fixture(monkeypatch, {"stay": (0., 0), "m6_s0": (1., 1), "m7_s0": (2., 1)})
    action, mask, decision = policy.select(40, state, 63)
    assert policy.plan["initiated"] and policy.plan["member"] == 7
    assert policy.continuation["selected_branch"] == "m7_s0"
    assert policy.continuation["original_R_branch"] == "stay"
    assert policy.continuation["best_stationary_physical_branch"] == "m6_s0"
    assert mask == 63 and decision["phase"] == "transit"
    np.testing.assert_array_equal(action, np.asarray(policy.plan["commands"], dtype=np.float32)[0])
    assert "motion" not in decision and "mask" not in decision
    assert len(seen) == 3


def test_full_continuation_rank_all_tie_dimensions():
    base = {"member": 3, "site": 8, "duration": 20, "selected": {"path": 300.}}
    score = dict(total_J=5., total_served=10)
    baseline = controller.continuation_rank(score, base)
    assert controller.continuation_rank(dict(score, total_J=6.), base) > baseline
    assert controller.continuation_rank(dict(score, total_served=11), base) > baseline
    for altered in (dict(base, selected={"path": 299.}), dict(base, duration=10),
                    dict(base, member=2), dict(base, site=7)):
        assert controller.continuation_rank(score, altered) > baseline


def test_physical_alias_ignores_site_but_preserves_arrival_member_and_duration():
    plan = {"initiated": True, "member": 6, "site": 0, "duration": 10,
            "commands": np.zeros((10, 8, 3), dtype=np.float32).tolist()}
    alias = dict(plan, site=99)
    assert option.branch_id(plan) != option.branch_id(alias)
    assert option.physical_identity(plan) == option.physical_identity(alias)
    assert option.physical_identity(plan) != option.physical_identity(dict(plan, member=7))
    assert option.physical_identity(None) == option.physical_identity({"initiated": False})
