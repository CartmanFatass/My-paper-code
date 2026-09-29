"""R2 (coupled_host_replan_timing): lawful-information arms -- facts, forwarding, map, trigger,
cap, D's detection, truth-access guard, no side effects, and the two-world probe run.

Hand-built dict/stub checks need no host; host checks use shortened hosts outside the declared
panels (world 9103, event overridden to cluster 3 at step 150, 200 steps, budget 60), where the
decision end sees the event and every arm re-plans at least once.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS
from experiments.candidates.coupled_host_replan_timing import event_host as EH
from experiments.candidates.coupled_host_replan_timing import r2_info as R2
from experiments.candidates.coupled_host_replan_timing import rules as R
from experiments.candidates.coupled_host_replan_timing import run_r2

ROOT = Path(__file__).resolve().parents[4]
BUDGET = 60
WORLD, CLUSTER, T_E, STEPS = 9103, 3, 150, 200


def small_host(world=WORLD, max_steps=STEPS, t_e=T_E, cluster=CLUSTER):
    kwargs = dict(HOST_CONTRACT_KWARGS)
    kwargs["max_steps"] = max_steps
    return EH.EventCoupledRelayHost(area_size=5000, seed=world,
                                    event_override={"t_e": t_e, "cluster": cluster}, **kwargs)


@pytest.fixture(scope="module")
def setup():
    """Pre-event plan, prefix and snapshot exactly as ``run_world_r2`` builds them."""
    env = small_host()
    env.reset(seed=WORLD)
    initial = np.array(env.uav_positions, copy=True)
    old_map = np.array(env.user_positions, copy=True)
    relay, _flat = R.d2_planner(env, old_map, WORLD, BUDGET)
    sites = np.asarray(relay.positions_xyz)
    keep = sites[R2.assign_targets(initial, sites)]
    prefix, snapshot = R.prefix_and_snapshot(env, keep, WORLD, STEPS)
    de = R2.gateway_uav(snapshot)                           # held pre-event deployment
    return SimpleNamespace(snapshot=snapshot, keep=keep, old_map=old_map, de=de, prefix=prefix)


# ------------------------------------------------------------------------------ facts


def test_facts_only_for_visible_users(setup):
    env = setup.snapshot
    positions = np.array(env.user_positions, copy=True)
    seen_any = False
    for uav in range(env.n_uavs):
        visible = {int(u) for u, _ in env._get_local_users(uav)}
        facts = R2.facts_for_uav(env, uav, 7)
        assert set(facts) == visible
        for user, (step, x, y, observer) in facts.items():
            assert (step, observer) == (7, uav) and (x, y) == tuple(positions[user])
        seen_any |= bool(visible) and len(visible) < env.n_users
    assert seen_any  # some UAV sees some but not all users: the restriction is exercised
    # a hand-edited visibility list is all the facts can contain
    stub = SimpleNamespace(_get_local_users=lambda i: [(3, 9.0), (41, 4.0)], user_positions=positions)
    assert set(R2.facts_for_uav(stub, 0, 0)) == {3, 41}


def test_routing_links_are_the_actual_route_edges():
    env = SimpleNamespace(n_uavs=6, routing_paths={
        0: [("uav", 0), ("uav", 1), ("uav", 2), ("ground_bs", 0)],
        2: [("uav", 2), ("ground_bs", 0)],
        4: [("uav", 4), ("uav", 2), ("ground_bs", 0)]})
    links = R2.routing_links(env)
    assert links == [{1}, {0, 2}, {1, 4}, set(), {2}, set()]


# ------------------------------------------------------------------------------ forwarding


def test_forwarding_one_hop_per_step_both_directions_lossless():
    line = [{1}, {0, 2}, {1}, set()]                       # 0 - 1 - 2, UAV 3 unlinked
    empty = [{} for _ in range(4)]
    holdings = [dict(h) for h in empty]
    own0 = [{}, {}, {7: (0, 10.0, 20.0, 2)}, {}]           # UAV 2 sees user 7 at step 0
    holdings = R2.forward(holdings, own0, line)
    assert [7 in h for h in holdings] == [False, False, True, False]
    holdings = R2.forward(holdings, empty, line)           # step 1: one hop
    assert [7 in h for h in holdings] == [False, True, True, False]
    holdings = R2.forward(holdings, empty, line)           # step 2: two hops
    assert [7 in h for h in holdings] == [True, True, True, False]
    assert holdings[0][7] == (0, 10.0, 20.0, 2)            # content unchanged
    # reverse direction, and a newer fact replaces an older one, an older one never replaces
    holdings = R2.forward(holdings, [{7: (5, 99.0, 1.0, 0)}, {}, {}, {}], line)
    holdings = R2.forward(holdings, empty, line)
    assert holdings[1][7] == (5, 99.0, 1.0, 0) and holdings[2][7] == (0, 10.0, 20.0, 2)
    holdings = R2.forward(holdings, empty, line)
    assert holdings[2][7] == (5, 99.0, 1.0, 0)
    assert R2.merge(holdings[2], {7: (5, 99.0, 1.0, 1)}) == []   # already held: not duplicated
    assert holdings[3] == {}


def test_latest_per_user_equals_holding_every_fact():
    """The storage form is exact: the map from latest-per-user holdings equals the map from full
    fact sets forwarded by the same recurrence (random links, random observations)."""
    rng = np.random.default_rng(0)
    n, users = 5, 8
    old = rng.uniform(0, 5000, (users, 2))
    latest = [{} for _ in range(n)]
    full: list[set] = [set() for _ in range(n)]
    for step in range(30):
        truth = old + (step >= 10) * 500.0
        own = [{int(u): (step, *map(float, truth[u]), a) for u in rng.choice(users, 2, replace=False)}
               if rng.random() < 0.5 else {} for a in range(n)]
        links = [set() for _ in range(n)]
        for a, b in rng.choice(n, (2, 2)):
            if a != b:
                links[a].add(int(b))
                links[b].add(int(a))
        latest = R2.forward(latest, own, links)
        full = [full[a] | {(u, *f) for u, f in own[a].items()} | set().union(*(full[b] for b in links[a]))
                for a in range(n)]
        for a in range(n):
            best: dict[int, tuple] = {}
            for u, s, x, y, o in full[a]:
                if u not in best or s > best[u][0]:
                    best[u] = (s, x, y, o)
            assert np.array_equal(R2.map_from(old, latest[a]), R2.map_from(old, best))


# ------------------------------------------------------------------------------ map and trigger


def test_map_retention_absence_moves_nobody():
    old = np.array([[0.0, 0.0], [100.0, 0.0], [200.0, 0.0]])
    held = {1: (4, 900.0, 900.0, 0)}
    mapped = R2.map_from(old, held)
    assert np.array_equal(mapped[[0, 2]], old[[0, 2]]) and tuple(mapped[1]) == (900.0, 900.0)
    # user 1 leaves every view: the held fact (and so the map row) is kept
    held_next = dict(held)
    R2.merge(held_next, {})
    assert np.array_equal(R2.map_from(old, held_next), mapped)
    assert R2.moved_users(mapped, old) == [1]
    assert R2.moved_users(old + [[100.0, 0.0], [0.0, 0.0], [0.0, 0.0]], old) == []   # 100 m is not > 100


class StubEnv:
    """Minimal host for the controller: scripted facts per step, one route 0 - 1 - 2."""

    def __init__(self, n_uavs=3):
        self.n_uavs = n_uavs
        self.uav_positions = np.zeros((n_uavs, 3))
        self.routing_paths = {0: [("uav", 0), ("uav", 1), ("uav", 2), ("ground_bs", 0)]}


@pytest.fixture
def scripted(monkeypatch):
    """Scripted facts {step: {uav: {user: xy}}}; the planner stub returns a marker layout."""
    script: dict[int, dict[int, dict[int, tuple]]] = {}
    calls: list[np.ndarray] = []

    def fake_facts(env, uav, step):
        return {u: (step, float(x), float(y), uav) for u, (x, y) in script.get(step, {}).get(uav, {}).items()}

    def fake_planner(env, users_xy, world, budget):
        calls.append(np.array(users_xy, copy=True))
        layout = np.full((env.n_uavs, 3), float(len(calls)))
        result = SimpleNamespace(positions_xyz=layout, evaluations=10)
        return result, result

    monkeypatch.setattr(R2, "facts_for_uav", fake_facts)
    monkeypatch.setattr(R2, "d2_planner", fake_planner)
    monkeypatch.setattr(R2, "assign_targets", lambda initial, layout: np.arange(len(layout)))
    monkeypatch.setattr(R2, "grant_truth", lambda env: np.full((6, 2), -1.0))
    return script, calls


def drive(arm, steps, de=0, old=None):
    env = StubEnv()
    old = np.zeros((6, 2)) if old is None else old
    ctrl = R2.InfoArm(arm, env, np.zeros((3, 3)), old, de, world=1, budget=5)
    for t in range(1, steps + 1):
        ctrl.targets(t)
    return ctrl


def test_trigger_fires_at_exactly_three_users_moved(scripted):
    script, calls = scripted
    script[3] = {0: {0: (150.0, 0.0), 1: (150.0, 0.0)}}                     # 2 users moved
    script[5] = {0: {2: (100.0, 0.0)}}                                       # exactly 100 m: not moved
    script[7] = {0: {3: (0.0, 101.0)}}                                       # third user > 100 m
    ctrl = drive("unshared", 12)
    rec = ctrl.record()
    assert rec["trigger_steps"] == [{"fact_step": 7, "first_call_with_new_targets": 8}]
    assert rec["replans"] == 1 and rec["evaluations_used"] == 20 and not rec["cap_hit"]
    assert np.array_equal(calls[0][[0, 1, 3]], [[150.0, 0.0], [150.0, 0.0], [0.0, 101.0]])
    assert np.array_equal(calls[0][[2, 4, 5]], [[100.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
    # after the re-plan the planned map is the map: nothing re-triggers without new moves
    assert rec["first_change_step_at_decision_end"] == 3


def test_replan_cap_three(scripted):
    script, calls = scripted
    for k, step in enumerate((2, 4, 6, 8, 10)):
        script[step] = {0: {u: (1000.0 * (k + 1), 0.0) for u in range(3)}}
    rec = drive("unshared", 14).record()
    assert rec["replans"] == R2.MAX_REPLANS == 3 == len(calls)
    assert [tr["fact_step"] for tr in rec["trigger_steps"]] == [2, 4, 6]
    assert rec["cap_hit"] and rec["first_cap_hit_step"] == 8


def test_shared_reaches_decision_end_by_hops_unshared_never(scripted):
    script, _calls = scripted
    script[4] = {2: {u: (500.0, 500.0) for u in range(3)}}                  # seen by UAV 2 (two hops)
    shared = drive("shared", 10).record()
    unshared = drive("unshared", 10).record()
    assert shared["first_change_step_per_uav"] == [None, None, 4]
    assert shared["changed_fact_arrivals_at_decision_end"]["0"] == {"obs_step": 4, "arrival_step": 6,
                                                                   "observer": 2}
    assert shared["trigger_steps"] == [{"fact_step": 6, "first_call_with_new_targets": 7}]
    assert unshared["replans"] == 0 and unshared["first_change_step_at_decision_end"] is None


def test_d_detection_step_any_uav_grants_truth_once(scripted):
    script, calls = scripted
    script[5] = {2: {5: (0.0, 150.0)}}                                       # one user, not the DE
    script[8] = {1: {u: (400.0, 0.0) for u in range(4)}}
    rec = drive("D", 12).record()
    assert rec["detection_step_any_uav"] == 5 and rec["truth_grant_steps"] == [5]
    assert rec["trigger_steps"] == [{"fact_step": 5, "first_call_with_new_targets": 6}]
    assert rec["replans"] == 1 and np.all(calls[0] == -1.0)                 # planned on the truth
    assert drive("unshared", 12).record()["truth_grant_steps"] == []


# ------------------------------------------------------------------------------ host: guard, side effects


FORBIDDEN = {"event", "_post_event_users", "post_event_user_positions", "event_info"}


class TruthAccess(AssertionError):
    pass


@pytest.fixture
def truth_guard(monkeypatch):
    """Raise on event/truth attributes except inside host dynamics (step) and grant_truth."""
    state = {"allowed": 0, "grants": 0}
    plain = object.__getattribute__

    def guarded(self, name):
        if name in FORBIDDEN and not state["allowed"]:
            raise TruthAccess(f"arm code read env.{name}")
        return plain(self, name)

    def allow(function, count=None):
        def wrapper(*args, **kwargs):
            state["allowed"] += 1
            if count:
                state[count] += 1
            try:
                return function(*args, **kwargs)
            finally:
                state["allowed"] -= 1
        return wrapper

    def no_draw(*args, **kwargs):
        raise TruthAccess("arm code re-drew the event")

    monkeypatch.setattr(EH.EventCoupledRelayHost, "step", allow(EH.EventCoupledRelayHost.step))
    monkeypatch.setattr(R2, "grant_truth", allow(R2.grant_truth, "grants"))
    monkeypatch.setattr(EH, "draw_event", no_draw)
    monkeypatch.setattr(EH.EventCoupledRelayHost, "__getattribute__", guarded)
    return state


def test_arms_never_read_the_truth(setup, truth_guard):
    snap = setup.snapshot
    with pytest.raises(TruthAccess):                                        # negative controls
        snap.post_event_user_positions()
    with pytest.raises(TruthAccess):
        _ = snap.event["t_e"]
    records = {}
    for arm in R2.ARMS:
        before = truth_guard["grants"]
        _result, rec, _env = R2.run_arm(snap, arm, setup.keep, setup.old_map, setup.de, WORLD,
                                        BUDGET, STEPS)
        records[arm] = rec
        assert truth_guard["grants"] - before == (1 if arm == "D" else 0)
        assert rec["replans"] >= 1                                           # the arms did act
    assert records["D"]["truth_grant_steps"] == [records["D"]["detection_step_any_uav"]] == [T_E]
    for arm in ("unshared", "shared"):
        assert records[arm]["trigger_steps"][0]["fact_step"] >= T_E        # earliest: after call t_e


def test_guard_catches_a_leaking_arm(setup, truth_guard, monkeypatch):
    original = R2.facts_for_uav

    def leaking(env, uav, step):
        _ = env.event["new_user_positions"]
        return original(env, uav, step)
    monkeypatch.setattr(R2, "facts_for_uav", leaking)
    with pytest.raises(TruthAccess):
        R2.run_arm(setup.snapshot, "unshared", setup.keep, setup.old_map, setup.de, WORLD, BUDGET, STEPS)


def test_no_side_effects_and_keep_identity(setup, monkeypatch):
    snap = setup.snapshot
    fingerprint = R.state_fingerprint(snap)
    live_checks = []
    original = R.d2_planner

    def checked(env, users_xy, world, budget):
        before = R.state_fingerprint(env)
        out = original(env, users_xy, world, budget)
        live_checks.append(before == R.state_fingerprint(env))
        return out
    monkeypatch.setattr(R2, "d2_planner", checked)
    for arm in R2.ARMS:
        R2.run_arm(snap, arm, setup.keep, setup.old_map, setup.de, WORLD, BUDGET, STEPS)
    assert live_checks and all(live_checks)
    R.assert_unchanged(snap, fingerprint, "R2 arms")
    # an arm that never re-plans is KEEP bit for bit: reading facts does not perturb the host
    monkeypatch.setattr(R2, "TRIGGER_K", 10 ** 6)
    result, rec, _env = R2.run_arm(snap, "shared", setup.keep, setup.old_map, setup.de, WORLD,
                                   BUDGET, STEPS)
    keep = R.branch(snap, lambda t: setup.keep, setup.keep, STEPS)
    assert rec["replans"] == 0 and result["coverage_backhauled"] == keep["coverage_backhauled"]


def test_decision_end_rule():
    env = SimpleNamespace(n_uavs=4, routing_paths={2: [("uav", 2), ("uav", 3), ("ground_bs", 0)],
                                                   3: [("uav", 3), ("ground_bs", 0)],
                                                   1: [("uav", 1), ("ground_bs", 0)]})
    assert R2.gateway_uav(env) == 1
    assert R2.gateway_uav(SimpleNamespace(n_uavs=4, routing_paths={})) == 0


def test_decision_end_is_the_snapshot_gateway():
    """run_world_r2 takes the decision end from the branch-point snapshot, not the reset state."""
    rec = R2.run_world_r2(small_host(), BUDGET, arms=("unshared",))
    env = small_host()
    env.reset(seed=WORLD)
    keep = np.asarray(rec["keep_targets_xyz"])
    _prefix, snapshot = R.prefix_and_snapshot(env, keep, WORLD, STEPS)
    assert rec["decision_end"] == R2.gateway_uav(snapshot) == rec["arms"]["unshared"]["decision_end"]
    assert rec["routed_uavs_at_snapshot"] == sorted(snapshot.routing_paths)
    assert rec["decision_end_reason"] == ("no routed uav" if not snapshot.routing_paths
                                          else "shortest routing path at the branch-point snapshot")
    env.reset(seed=WORLD)
    assert rec["reset_gateway"] == R2.gateway_uav(env)


# ------------------------------------------------------------------------------ runner


REFERENCE = ROOT / "runs" / "coupled_host_replan_timing" / "r1lite_dev_a01"


@pytest.mark.skipif(not (REFERENCE / "summary.json").exists(), reason="R1-lite dev reference absent")
def test_two_world_probe_end_to_end(tmp_path, monkeypatch):
    monkeypatch.delenv(run_r2.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    cpu0 = time.process_time()
    assert run_r2.main(["--worlds", "1002", "1011", "--probe", "2", "--out", str(out),
                        "--budget", "3000", "--reference-run", str(REFERENCE),
                        "--launch-sha", "test"]) == 0
    assert time.process_time() - cpu0 < 120
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1002, 1011] and summary["training_fits_performed"] == 0
    for key in ("timing_totals", "cpu_seconds", "wall_clock_s", "git_head", "launch_sha",
                "arguments", "interpreter", "reference_run", "means", "information_contract"):
        assert key in summary
    assert len(summary["reference_run"]["sha256"]) == 64
    for row in summary["per_world"]:
        for key in ("world", "t_e", "routing_class", "decision_end", "decision_end_reason",
                    "reset_gateway", "reference_cold_post_event_mean",
                    "stakes"):
            assert key in row
        assert set(row["arms"]) == set(R2.ARMS)
        for rec in row["arms"].values():
            assert set(run_r2.ARM_KEYS) <= set(rec)
            assert rec["evaluations_used"] <= 2 * 3000 * max(rec["replans"], 1)
        post = {a: r["post_event_mean"] for a, r in row["arms"].items()}
        cold = row["reference_cold_post_event_mean"]
        assert row["stakes"] == {"delta_share": post["shared"] - post["unshared"],
                                 "s_info_unshared": cold - post["unshared"],
                                 "s_info_shared": cold - post["shared"],
                                 "d_minus_shared": post["D"] - post["shared"],
                                 "d_minus_unshared": post["D"] - post["unshared"]}
    for stake in run_r2.STAKES:
        assert set(summary["means"]["stakes"][stake]) >= {"mean", "sd", "min", "max", "n", "n_positive"}
    assert summary["means"]["by_routing_class"]
    # refuses to overwrite; refuses a reference at another budget
    assert run_r2.main(["--worlds", "1002", "--out", str(out), "--reference-run", str(REFERENCE)]) == 2
    assert run_r2.main(["--worlds", "1002", "--out", str(tmp_path / "b"), "--budget", "60",
                        "--reference-run", str(REFERENCE)]) == 2
