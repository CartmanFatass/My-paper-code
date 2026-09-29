"""R1-lite (coupled_host_replan_timing): event host, rules, small grid and runner schema.

Worlds are outside the declared panels; hosts are shortened (max_steps < 500) and the event step
is overridden so every check is a technical check, not a result.
"""
from __future__ import annotations

import copy
import json

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    HOST_CONTRACT_KWARGS,
    CoupledRelayHost,
    static_evaluate,
)
from experiments.candidates.coupled_host_joint_skills_stage1.menus import compute_menu
from experiments.candidates.coupled_host_joint_skills_stage1.planner import closed_loop_execute
from experiments.candidates.coupled_host_replan_timing import event_host as EH
from experiments.candidates.coupled_host_replan_timing import rules as R
from experiments.candidates.coupled_host_replan_timing import run_r1lite

BUDGET = 60


def small_host(world, max_steps=160, t_e=130, cluster=None, cls=EH.EventCoupledRelayHost):
    kwargs = dict(HOST_CONTRACT_KWARGS)
    kwargs["max_steps"] = max_steps
    if cls is CoupledRelayHost:
        return CoupledRelayHost(area_size=5000, seed=world, **kwargs)
    override = {"t_e": t_e} | ({} if cluster is None else {"cluster": cluster})
    return cls(area_size=5000, seed=world, event_override=override, **kwargs)


@pytest.fixture(scope="module")
def record_9101():
    return R.run_world(small_host(9101), BUDGET)


@pytest.fixture(scope="module")
def record_9104():
    return R.run_world(small_host(9104), BUDGET)


# ------------------------------------------------------------------------------ event host


def test_event_draw_reproducible_and_in_range():
    for world in range(1000, 1032):
        first = EH.draw_event(world, 5000, 50)
        second = EH.draw_event(world, 5000, 50)
        assert first["t_e"] == second["t_e"] and first["cluster"] == second["cluster"]
        assert np.array_equal(first["new_user_positions"], second["new_user_positions"])
        assert 150 <= first["t_e"] <= 350 and 0 <= first["cluster"] <= 4
        assert np.all(first["new_user_positions"] >= 0) and np.all(first["new_user_positions"] <= 5000)
        assert list(first["members"]) == list(range(10 * first["cluster"], 10 * first["cluster"] + 10))
    rng = np.random.default_rng([1000, 3])
    t_e, cluster = int(rng.integers(150, 351)), int(rng.integers(0, 5))
    centre = rng.uniform(0, 5000, 2)
    event = EH.draw_event(1000, 5000, 50)
    assert (event["t_e"], event["cluster"]) == (t_e, cluster)
    assert np.array_equal(event["new_centre_xy"], centre)
    # an override replaces t_e / cluster only; the centre and member draws are unchanged
    override = EH.draw_event(1000, 5000, 50, {"t_e": 7})
    assert override["t_e"] == 7 and np.array_equal(override["new_centre_xy"], centre)


def test_event_host_equals_parent_before_te_and_moves_one_cluster():
    parent = small_host(9101, max_steps=40, cls=CoupledRelayHost)
    child = small_host(9101, max_steps=40, t_e=15, cluster=2)
    parent.reset(seed=9101)
    child.reset(seed=9101)
    rng = np.random.default_rng(0)
    for t in range(15):
        actions = rng.uniform(-1, 1, (6, 3))
        parent.step({a: actions[i] for i, a in enumerate(parent.agents)})
        child.step({a: actions[i] for i, a in enumerate(child.agents)})
        assert np.array_equal(parent.uav_positions, child.uav_positions)
        assert np.array_equal(parent.user_positions, child.user_positions)
        assert parent.reward_info == child.reward_info
        assert np.array_equal(parent.connections, child.connections)
        assert parent.routing_paths == child.routing_paths
    assert not child.event_applied
    before = np.array(child.user_positions, copy=True)
    actions = rng.uniform(-1, 1, (6, 3))
    parent.step({a: actions[i] for i, a in enumerate(parent.agents)})
    child.step({a: actions[i] for i, a in enumerate(child.agents)})
    assert child.event_applied and child.event["applied_in_step_call"] == 15
    changed = np.flatnonzero(np.any(child.user_positions != before, axis=1))
    assert set(changed) <= set(range(20, 30)) and len(changed) > 0
    assert np.array_equal(child.user_positions[20:30], child.event["new_user_positions"])
    others = np.r_[0:20, 30:50]
    assert np.array_equal(child.user_positions[others], parent.user_positions[others])
    assert np.array_equal(child.uav_positions, parent.uav_positions)
    # the reset restores the pre-event users and re-draws the same event
    child.reset(seed=9101)
    assert not child.event_applied and np.array_equal(child.user_positions, before)
    info = child.event_info
    assert info["cluster"] == 2 and info["t_e"] == 15 and info["applied"] is False
    assert info["old_centre_source"] == "generator_replay"


# ------------------------------------------------------------------------------ rules


def test_keep_equals_d2_closed_loop_on_parent_up_to_te(record_9101):
    rec = record_9101
    t_e = rec["t_e"]
    parent = small_host(9101, cls=CoupledRelayHost)
    reference = closed_loop_execute(parent, rec["pre_event"]["P_relay_sites_xyz"])
    assert reference["series"]["coverage_backhauled"][:t_e] == rec["pre_event"]["coverage_backhauled"]
    assert reference["series"]["contract_reward"][:t_e] == rec["pre_event"]["contract_reward"]
    assert reference["target_permutation"] == rec["pre_event"]["permutation"]
    # the pre-event plan is D2's menu (P_relay) for this world at the same budget
    menu = compute_menu(9101, 5000, BUDGET)
    assert menu["positions_xyz"] == rec["pre_event"]["P_relay_sites_xyz"]
    assert rec["rules"]["keep"]["unbranched_check"] == "equal bit for bit"


def test_prefix_identity_across_rules_and_branch_equals_unbranched(record_9104):
    rec = record_9104
    pre = rec["pre_event"]
    for name in R.RULES:
        assert rec["rules"][name]["pre_event_mean"] == pre["pre_event_mean"]
    # branched cold == an un-branched episode with the same target schedule, bit for bit
    env = small_host(9104)
    env.reset(seed=9104)
    keep = np.asarray(pre["keep_targets_xyz"])
    cold = np.asarray(rec["rules"]["cold"]["targets_xyz"])
    t_e = rec["t_e"]
    full = R.rollout(env, lambda t: keep if t < t_e else cold, 0, rec["horizon"], record_actions=True)
    assert full["coverage_backhauled"][:t_e] == pre["coverage_backhauled"]
    assert full["coverage_backhauled"][t_e:] == rec["rules"]["cold"]["post_event_coverage_backhauled"]
    # the shared prefix is the same actions as a KEEP-only prefix run
    env2 = small_host(9104)
    prefix, _snap = R.prefix_and_snapshot(env2, keep, 9104, rec["horizon"])
    assert all(np.array_equal(a, b) for a, b in zip(prefix["actions"], full["actions"][:t_e]))


def test_planning_never_mutates_live_state(record_9104):
    rec = record_9104
    env = small_host(9104)
    keep = np.asarray(rec["pre_event"]["keep_targets_xyz"])
    _prefix, snapshot = R.prefix_and_snapshot(env, keep, 9104, rec["horizon"])
    fingerprint = R.state_fingerprint(snapshot)
    users = snapshot.post_event_user_positions()
    R.d2_planner(snapshot, users, 9104, BUDGET)
    R.held_site_replacement(snapshot, users, keep, [0, 1], users[20:30].mean(axis=0), 30)
    R.static_value(snapshot, users, keep)
    R.assert_unchanged(snapshot, fingerprint, "test")
    # negative control: evaluating on the live host is detected
    static_evaluate(snapshot, keep + np.array([100.0, 0.0, 0.0]), allow_a2a=True)
    with pytest.raises(AssertionError, match="mutated"):
        R.assert_unchanged(snapshot, fingerprint, "direct static_evaluate")


def test_warm_holds_unaffected_uav_targets(record_9101, record_9104):
    for rec in (record_9101, record_9104):
        keep = np.asarray(rec["pre_event"]["keep_targets_xyz"])
        warm = rec["rules"]["warm"]
        facts = rec["event_info"]["pre_event_routing"]
        if facts["movable_uavs"]:
            assert warm["movable_source"] == "pre_event_routing"
            assert warm["movable_uavs"] == facts["movable_uavs"]
        targets = np.asarray(warm["targets_xyz"])
        for u in range(6):
            if u not in warm["movable_uavs"]:
                assert np.array_equal(targets[u], keep[u])
        assert set(warm["moved_uavs"]) <= set(warm["movable_uavs"])
        assert warm["evaluations"] <= BUDGET
        # cold SET-now is a whole new layout: nothing holds it to the pre-event targets
        assert rec["rules"]["cold"]["moved_uavs"]
        seeded = rec["rules"]["seeded"]
        assert seeded["evaluations"] <= seeded["budget"] == BUDGET
        assert rec["stakes"]["S_seeded"] == seeded["post_event_mean"] - rec["rules"]["keep"]["post_event_mean"]


def _constructed(uav4_xy, e_post_xy):
    """Hand-built world on BS (2500, 2500): A east chain (UAV 0 server, 1 relay), C west direct
    (UAV 2), D south chain (UAV 3 server, 5 relay), B far west, UAV 4 at ``uav4_xy``; the
    relocated cluster 4 is unserved before the event and moves to ``e_post_xy``."""
    env = small_host(9101)
    env.reset(seed=9101)
    offsets = np.array([[dx, dy] for dx in (-20.0, 0.0, 20.0) for dy in (-20.0, 20.0)] * 2)[:10]
    spots = {0: (4500, 2500), 1: (500, 2500), 2: (1600, 2500), 3: (2500, 500), 4: (200, 200)}
    pre = np.concatenate([np.asarray(spots[c], dtype=float) + offsets for c in range(5)])
    post = pre.copy()
    post[40:50] = np.asarray(e_post_xy, dtype=float) + offsets
    layout = np.array([[4500, 2500, 100], [3500, 2500, 100], [1600, 2500, 100],
                       [2500, 500, 100], [uav4_xy[0], uav4_xy[1], 100], [2500, 1500, 100]], dtype=float)
    shadow = R.shadow_host(env, pre)
    info = static_evaluate(shadow, layout, allow_a2a=True)
    facts = EH.cluster_routing_facts(shadow, 4, np.minimum(np.arange(50) // 10, 4))
    return env, pre, post, layout, info, facts


def test_warm_fallback_moves_the_redundant_uav():
    env, _pre, post, layout, info, facts = _constructed((0, 5000), (2500, 3400))
    assert info["backhauled_users"] == 30 and facts["class"] == "unserved" and facts["movable_uavs"] == []
    warm = R.warm_rule(env, post, layout, layout, facts, post[40:50].mean(axis=0), BUDGET,
                       fallback_budget=5)
    assert warm["movable_source"] == "fallback_single_uav" and warm["movable_uavs"] == [4]
    assert not warm["warm_equals_keep"]
    assert np.array_equal(warm["targets"][[0, 1, 2, 3, 5]], layout[[0, 1, 2, 3, 5]])
    assert warm["fallback"]["chosen_uav"] == 4 and len(warm["fallback"]["candidates"]) == 6
    assert warm["static_coverage_backhauled"] == pytest.approx(0.8)


def test_warm_fallback_keeps_when_no_candidate_beats_held():
    env, _pre, post, layout, info, facts = _constructed((500, 2500), (150, 150))
    assert info["backhauled_users"] == 40 and facts["class"] == "unserved"
    warm = R.warm_rule(env, post, layout, layout, facts, post[40:50].mean(axis=0), BUDGET,
                       fallback_budget=5)
    assert warm["movable_source"] == "empty" and warm["movable_uavs"] == []
    assert warm["warm_equals_keep"] and "no single-UAV candidate" in warm["warm_equals_keep_reason"]
    assert np.array_equal(warm["targets"], layout)
    assert all(c["contract_reward"] < warm["fallback"]["held_contract_reward"]
               for c in warm["fallback"]["candidates"])


def test_routing_facts_rule_on_a_constructed_state():
    env = small_host(9104)
    env.reset(seed=9104)
    membership = np.minimum(np.arange(50) // 10, 4)
    # empty connections -> unserved, empty movable set
    env.connections = np.zeros_like(env.connections)
    facts = EH.cluster_routing_facts(env, 2, membership)
    assert facts["class"] == "unserved" and facts["movable_uavs"] == []


def test_held_replacement_moves_only_movable_rows(record_9104):
    rec = record_9104
    env = small_host(9104)
    keep = np.asarray(rec["pre_event"]["keep_targets_xyz"])
    _prefix, snapshot = R.prefix_and_snapshot(env, keep, 9104, rec["horizon"])
    users = snapshot.post_event_user_positions()
    result = R.held_site_replacement(snapshot, users, keep, [3], users[20:30].mean(axis=0), 40)
    rows = [0, 1, 2, 4, 5]
    assert np.array_equal(result["positions_xyz"][rows], keep[rows])
    assert result["evaluations"] <= 40
    empty = R.held_site_replacement(snapshot, users, keep, [], users[20:30].mean(axis=0), 40)
    assert np.array_equal(empty["positions_xyz"], keep) and empty["evaluations"] == 1


# ------------------------------------------------------------------------------ grid


@pytest.mark.parametrize("world", [9101, 9104])
def test_grid_192_entries_identities_and_dedupe(world):
    env = small_host(world, max_steps=150, t_e=130)
    rec = json.loads(json.dumps(R.run_world(env, BUDGET)))  # JSON round trip as in the runner
    grid = R.run_grid(small_host(world, max_steps=150, t_e=130), rec)
    assert grid["entries"] == 192 and len(grid["table"]) == 192
    warm_post = rec["rules"]["warm"]["post_event_mean"]
    assert grid["best"]["post_event_mean"] >= warm_post
    all_zero = [e for e in grid["table"] if e["mask"] == 63 and e["delay"] == 0][0]
    assert all_zero["post_event_mean"] == warm_post
    for entry in grid["table"]:
        if entry["mask"] == 0:
            assert entry["post_event_mean"] == rec["rules"]["keep"]["post_event_mean"]
    best_ordinary = max(rec["rules"][r]["post_event_mean"] for r in R.RULES)
    assert grid["room"] == pytest.approx(grid["best"]["post_event_mean"] - best_ordinary, abs=0)
    if world == 9104:  # warm moves several UAVs here: dedupe must not change any value
        assert grid["unique_rollouts"] > 3
        plain = R.run_grid(small_host(world, max_steps=150, t_e=130), rec, delays=(0, 20, 50),
                           dedupe=False)
        assert plain["unique_rollouts"] == 192
        assert plain["table"] == grid["table"]


# ------------------------------------------------------------------------------ runner


def test_runner_summary_schema_and_stakes(tmp_path, monkeypatch):
    def fake_make(world, area_size=5000, event_override=None):
        return small_host(int(world), max_steps=150, t_e=130)
    monkeypatch.setattr(EH, "make_event_host", fake_make)
    monkeypatch.delenv(run_r1lite.ADMISSION_ENV, raising=False)
    out = tmp_path / "run"
    assert run_r1lite.main(["--worlds", "9101-9102", "--out", str(out), "--budget", str(BUDGET),
                            "--launch-sha", "deadbeef"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["schema"] == 1 and summary["direction"] == "coupled_host_replan_timing"
    assert summary["worlds"] == [9101, 9102] and summary["rules"] == ["keep", "cold", "warm", "seeded"]
    assert summary["training_fits_performed"] == 0 and summary["launch_sha"] == "deadbeef"
    rows = summary["per_world"]
    for row in rows:
        world = json.loads((out / "worlds" / f"{row['world']}.json").read_text())
        post = {r: world["rules"][r]["post_event_mean"] for r in R.RULES}
        assert row["stakes"]["S_switch"] == post["warm"] - post["keep"]
        assert row["stakes"]["S_cold"] == post["warm"] - post["cold"]
        assert row["stakes"]["S_seeded"] == post["seeded"] - post["keep"]
        for part in ("pre_event_plan", "pre_event_prefix", "keep", "keep_unbranched_check",
                     "cold", "warm", "seeded", "world_total"):
            assert part in world["timing"]
    diffs = np.array([row["stakes"]["S_switch"] for row in rows])
    stake = summary["means"]["stakes"]["S_switch"]
    assert stake["n"] == 2 and stake["mean"] == pytest.approx(diffs.mean())
    assert stake["sd"] == pytest.approx(diffs.std(ddof=1))
    assert summary["means"]["by_routing_class"]
    assert set(summary["means"]["stakes"]) == {"S_switch", "S_cold", "S_seeded"}
    # refuses to overwrite; the grid pass reads the warm result from the out dir
    assert run_r1lite.main(["--worlds", "9101", "--out", str(out), "--budget", str(BUDGET)]) == 2
    assert run_r1lite.main(["--worlds", "9101-9102", "--probe", "1", "--out", str(out),
                            "--budget", str(BUDGET), "--rules", "grid"]) == 0
    grid_summary = json.loads((out / "grid_summary.json").read_text())
    assert grid_summary["worlds"] == [9101]
    assert grid_summary["inputs"]["9101"]["sha256"]
    grid = json.loads((out / "grid" / "9101.json").read_text())
    assert grid["entries"] == 192 and grid_summary["means"]["room"]["n"] == 1


def test_parse_rules():
    assert run_r1lite.parse_rules("seeded,warm,keep") == ("keep", "warm", "seeded")
    assert run_r1lite.parse_rules("grid") == ("grid",)
    for bad in ("grid,warm", "keep,keep", "oracle", ""):
        with pytest.raises(ValueError):
            run_r1lite.parse_rules(bad)


def test_canonical_data_root(tmp_path):
    snap = tmp_path / "checkout" / ".git" / "hmasd-launch-sources" / "abc"
    assert run_r1lite.canonical_data_root(snap) == tmp_path / "checkout"
    assert run_r1lite.canonical_data_root(tmp_path) == tmp_path
