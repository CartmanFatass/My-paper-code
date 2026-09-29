"""R3 (coupled_host_replan_timing): the shared_wide arm (routing edges UNION mutually visible UAV
pairs), per-step re-reading of the edges, reduction to shared, truth guard, KEEP identity,
runner --arms / --regression-run handling and the two-world probe.

Reuses the R2 test fixtures (shortened host 9103, event cluster 3 at step 150, budget 60).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.coupled_host_replan_timing import r2_info as R2
from experiments.candidates.coupled_host_replan_timing import rules as R
from experiments.candidates.coupled_host_replan_timing import run_r2

from test_r2_info import (  # noqa: F401  (fixtures; rootdir-basename import, no package)
    BUDGET, REFERENCE, ROOT, STEPS, T_E, WORLD, StubEnv, scripted, setup, truth_guard,
)

REGRESSION = ROOT / "runs" / "coupled_host_replan_timing" / "r2_dev_a01"


def vis_env(n, visible, routing_paths=None):
    return SimpleNamespace(n_uavs=n, routing_paths=routing_paths or {},
                           _get_local_uavs=lambda i: [(j, 5.0) for j in visible.get(i, [])])


# ------------------------------------------------------------------------------ edge rule


def test_mutual_visibility_rule():
    # 0 <-> 1 mutual; 2 -> 3 one-way (3 does not hear 2); routing edge 1 - 2 kept; 4 sees itself only
    env = vis_env(5, {0: [1], 1: [0], 2: [3], 4: [4]},
                  {1: [("uav", 1), ("uav", 2), ("ground_bs", 0)]})
    assert R2.visible_uavs(env, 2) == [3]
    assert R2.wide_links(env) == [{1}, {0, 2}, {1}, set(), set()]
    # one-way in the other direction: still no edge
    assert R2.wide_links(vis_env(2, {1: [0]})) == [set(), set()]
    assert R2.wide_links(vis_env(2, {0: [1], 1: [0]})) == [{1}, {0}]
    # routing edges are kept even when neither end hears the other
    only_route = vis_env(3, {}, {0: [("uav", 0), ("uav", 2), ("ground_bs", 0)]})
    assert R2.wide_links(only_route) == R2.routing_links(only_route) == [{2}, set(), {0}]


class VisStub(StubEnv):
    """StubEnv (route 0 - 1 - 2) plus a scripted, step-varying UAV-UAV visibility."""

    def __init__(self, schedule):
        super().__init__(n_uavs=4)
        self.schedule, self.calls = schedule, 0
        self.routing_paths = {1: [("uav", 1), ("ground_bs", 0)]}     # no routing edges at all

    def _get_local_uavs(self, i):
        return [(j, 5.0) for j in self.schedule(self.step).get(i, [])]


def test_wide_edges_reread_every_step(scripted):
    script, _calls = scripted
    # UAV 3 sees 3 moved users at step 2; 3 <-> 0 mutual only on steps 4 and 5 (state after call s)
    script[2] = {3: {u: (900.0, 900.0) for u in range(3)}}
    env = VisStub(lambda s: {0: [3], 3: [0]} if s in (4, 5) else {0: [3]})
    ctrl = R2.InfoArm("shared_wide", env, np.zeros((4, 3)), np.zeros((6, 2)), 0, world=1, budget=5)
    for t in range(1, 10):
        env.step = t - 1                                             # the state the facts come from
        ctrl.targets(t)
    rec = ctrl.record()
    assert rec["wide_link_counts_per_step"] == [0, 0, 0, 0, 1, 1, 0, 0, 0]
    assert rec["routing_link_counts_per_step"] == [0] * 9
    assert rec["wide_links"]["min"] == 0 and rec["wide_links"]["steps_with_zero_links"] == 7
    assert rec["wide_edges_added_mean"] == pytest.approx(2 / 9)
    # the fact held by UAV 3 since step 2 crosses the first time the edge exists (step 4)
    assert rec["changed_fact_arrivals_at_decision_end"]["0"] == {"obs_step": 2, "arrival_step": 4,
                                                                "observer": 3}
    assert rec["trigger_steps"] == [{"fact_step": 4, "first_call_with_new_targets": 5}]
    assert "wide_links" not in R2.InfoArm("shared", env, np.zeros((4, 3)), np.zeros((6, 2)), 0,
                                          world=1, budget=5).record()


# ------------------------------------------------------------------------------ host


def test_shared_wide_without_visible_pairs_is_shared_bit_for_bit(setup, monkeypatch):
    monkeypatch.setattr(R2, "visible_uavs", lambda env, i: [])
    res_n, rec_n, _ = R2.run_arm(setup.snapshot, "shared", setup.keep, setup.old_map, setup.de,
                                 WORLD, BUDGET, STEPS)
    res_w, rec_w, _ = R2.run_arm(setup.snapshot, "shared_wide", setup.keep, setup.old_map, setup.de,
                                 WORLD, BUDGET, STEPS)
    assert rec_n["replans"] >= 1
    assert res_w["coverage_backhauled"] == res_n["coverage_backhauled"]
    wide_only = {"arm", "wide_links", "wide_edges_added_mean", "wide_link_counts_per_step",
                 "routing_link_counts_per_step"}
    assert {k: v for k, v in rec_w.items() if k not in wide_only} == \
           {k: v for k, v in rec_n.items() if k != "arm"}
    assert rec_w["wide_edges_added_mean"] == 0.0


def test_shared_wide_on_host_adds_edges_and_never_reads_the_truth(setup, truth_guard):
    before = truth_guard["grants"]
    _res, rec, _env = R2.run_arm(setup.snapshot, "shared_wide", setup.keep, setup.old_map, setup.de,
                                 WORLD, BUDGET, STEPS)
    assert truth_guard["grants"] == before and rec["truth_grant_steps"] == []
    assert rec["replans"] >= 1 and rec["trigger_steps"][0]["fact_step"] >= T_E
    assert all(w >= r for w, r in zip(rec["wide_link_counts_per_step"],
                                      rec["routing_link_counts_per_step"]))


def test_shared_wide_keep_identity_and_no_side_effects(setup, monkeypatch):
    snap = setup.snapshot
    fingerprint = R.state_fingerprint(snap)
    monkeypatch.setattr(R2, "TRIGGER_K", 10 ** 6)
    result, rec, _env = R2.run_arm(snap, "shared_wide", setup.keep, setup.old_map, setup.de, WORLD,
                                   BUDGET, STEPS)
    keep = R.branch(snap, lambda t: setup.keep, setup.keep, STEPS)
    assert rec["replans"] == 0 and result["coverage_backhauled"] == keep["coverage_backhauled"]
    R.assert_unchanged(snap, fingerprint, "shared_wide")


# ------------------------------------------------------------------------------ runner


def test_regression_diffs():
    shared = {"post_event_mean": 0.5, "replans": 1,
              "trigger_steps": [{"fact_step": 3, "first_call_with_new_targets": 4}]}
    row = {"arms": {"shared": json.loads(json.dumps(shared))}}
    assert run_r2.regression_diffs(row, shared) == {}
    assert set(run_r2.regression_diffs(row, {**shared, "post_event_mean": 0.5 + 1e-15})) == {"post_event_mean"}
    assert set(run_r2.regression_diffs(row, {**shared, "replans": 2, "trigger_steps": []})) == \
           {"replans", "trigger_steps"}
    assert run_r2.regression_diffs(None, shared) == {"world": "absent from the regression run"}


def test_bad_arms_rejected(tmp_path):
    for arms in ("shared,bogus", "shared,shared", ""):
        with pytest.raises(SystemExit):
            run_r2.main(["--worlds", "1002", "--out", str(tmp_path), "--reference-run", str(REFERENCE),
                         "--arms", arms])
    with pytest.raises(SystemExit):
        run_r2.main(["--worlds", "1002", "--out", str(tmp_path), "--reference-run", str(REFERENCE),
                     "--arms", "shared_wide", "--regression-run", str(REGRESSION)])


needs_runs = pytest.mark.skipif(not ((REFERENCE / "summary.json").exists()
                                     and (REGRESSION / "summary.json").exists()),
                                reason="R1-lite / R2 dev runs absent")


@needs_runs
def test_two_world_probe_r3_and_regression_mismatch(tmp_path, monkeypatch):
    monkeypatch.delenv(run_r2.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    args = ["--worlds", "1002", "1011", "--budget", "3000", "--reference-run", str(REFERENCE),
            "--arms", "shared,shared_wide", "--launch-sha", "test"]
    assert run_r2.main(args + ["--out", str(out), "--regression-run", str(REGRESSION)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["arms"] == ["shared", "shared_wide"] and summary["regression_ok"] is True
    reg = summary["regression_run"]
    assert reg["regression_ok"] is True and reg["mismatch_worlds"] == [] and len(reg["sha256"]) == 64
    assert summary["information_contract"]["wide_forwarding_links"] == R2.WIDE_FORWARDING_LINKS
    for row in summary["per_world"]:
        assert set(row["arms"]) == {"shared", "shared_wide"} and row["regression"]["ok"]
        wide = row["arms"]["shared_wide"]
        assert set(run_r2.ARM_KEYS) | set(run_r2.WIDE_KEYS) <= set(wide)
        assert wide["wide_links"]["mean"] >= row["arms"]["shared"]["routing_links"]["mean"]
        assert row["stakes"]["delta_adj"] == wide["post_event_mean"] - row["arms"]["shared"]["post_event_mean"]
        assert row["stakes"]["delta_share"] is None and "delta_adj_flag" not in row
        copied = row["copied_from_regression_run"]
        assert set(copied) == {"note", "unshared", "D"}
    stats = summary["means"]["stakes"]["delta_adj"]
    assert set(stats) >= {"mean", "sd", "min", "max", "n", "n_positive"} and stats["n"] == 2
    assert all("delta_adj" in c for c in summary["means"]["by_routing_class"].values())
    assert summary["means"]["arms"]["shared_wide"]["wide_edges_added_mean"]["n"] == 2
    assert set(summary["timing_totals"]["cpu_s_by_arm"]) == {"shared", "shared_wide"}

    # a regression run whose shared arm differs on world 1011: flagged, means withheld
    bad = tmp_path / "bad_regression"
    bad.mkdir()
    data = json.loads((REGRESSION / "summary.json").read_text())
    for row in data["per_world"]:
        if row["world"] == 1011:
            row["arms"]["shared"]["post_event_mean"] += 0.01
    (bad / "summary.json").write_text(json.dumps(data))
    out2 = tmp_path / "probe_bad"
    assert run_r2.main(args + ["--out", str(out2), "--regression-run", str(bad)]) == 0
    summary2 = json.loads((out2 / "summary.json").read_text())
    assert summary2["regression_ok"] is False
    assert summary2["regression_run"]["mismatch_worlds"] == [1011]
    assert summary2["means"]["stakes"]["delta_adj"] is None
    assert summary2["means"]["delta_adj_withheld"] == "regression mismatch"
    assert all("delta_adj" not in c for c in summary2["means"]["by_routing_class"].values())
    flagged = {r["world"]: r for r in summary2["per_world"]}
    assert flagged[1011]["delta_adj_flag"] == "regression mismatch" and not flagged[1011]["regression"]["ok"]
    assert flagged[1011]["stakes"]["delta_adj"] is not None               # per-world value kept
    shutil.rmtree(out2)
