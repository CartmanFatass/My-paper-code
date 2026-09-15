"""Focused acceptance of ACVC_M_DEPLOYMENT_TRANSFER_B01: identity binding, no-op identity with the
unchanged M evaluator, real substitution semantics on a synthetic fixture, private state and RNG
isolation, and the reduce readout. Synthetic only; no native environment, fit or profiling."""
import importlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from experiments.candidates.acvc.m_deployment_transfer_b01.wrapped_eval import PANELS, evaluate_wrapped
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from scripts import run_acvc_fresh_dense_reuse_b01 as shared

ON_POLICY = os.environ.get("HMASD_ON_POLICY_ROOT")


@pytest.fixture
def fresh_modules():
    names = [n for n in list(sys.modules) if "cluster_mappo_comparison_b0" in n or "m_deployment_transfer_b01" in n]
    saved = {n: sys.modules.pop(n) for n in names}
    yield
    for n in [n for n in list(sys.modules) if "cluster_mappo_comparison_b0" in n or "m_deployment_transfer_b01" in n]:
        sys.modules.pop(n)
    sys.modules.update(saved)


# ---------------------------------------------------------------- identity binding

def test_bind_object_rebinds_identities_panels_and_keeps_the_recipe(fresh_modules):
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    p = runner.p
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28331, 38331)
    frozen = {name: getattr(p, name) for name in runner.FROZEN}
    original_execute_m = runner.b01.execute_m
    runner.bind_object()
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28531, 38531)
    assert p.OBJECT == "ACVC_M_DEPLOYMENT_TRANSFER_B01"
    assert p.ARMS == {"M": ("M", "F(M)", "dwell(M)")}
    for name, value in frozen.items():
        assert getattr(p, name) is value
    assert frozen["TRAIN_EPISODES"] == 4096 and frozen["EVAL_EPISODES"] == 64 and frozen["HORIZON"] == 256
    assert frozen["UPSTREAM_SHA"] == "de66d7a4b23fac2513f56f96f73b3f5cb96695ac"
    assert runner.b01.execute_m is runner.execute_m_with_panels
    assert runner._B01_EXECUTE_M is original_execute_m
    # Derived seeds never collide with blocks 1 and 2 or the C-side namespaces.
    span = range(0, 50000)
    new = {100000 * 28531 + k for k in span} | {100000 * 38531 + k for k in span}
    for master, namespace in ((28331, 38331), (28431, 38431), (8961, 8962)):
        old = {100000 * master + k for k in span} | {100000 * namespace + k for k in span}
        assert not (old & new)
    assert set(runner.CONSTRUCTOR_OFFSETS.values()) == {65, 66, 67}


def test_early_recipe_import_is_refused(fresh_modules):
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    sys.modules["experiments.candidates.acvc.cluster_mappo_comparison_b01.mappo"] = object()
    with pytest.raises(RuntimeError):
        runner.bind_object()


def test_wrong_seed_and_missing_inputs_are_refused(fresh_modules):
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    with pytest.raises(SystemExit):
        runner.main(["--seed", "28431", "--output", "x", "--launch-sha", "abc", "--on-policy-root", "y"])
    with pytest.raises(SystemExit):
        runner.main(["--output", "x", "--launch-sha", "abc"])  # no on-policy root


# ---------------------------------------------------------------- synthetic fixtures

class FakePolicy:
    """Deterministic actor-only stand-in: raw = (-3, 0, 0) for every agent (proposal ~ (-.995, 0, 0));
    hidden advances by one per call so recurrent-state handling is observable."""
    def __init__(self):
        self.actor = type("Actor", (), {})()
        self.actor.act = type("Head", (), {"generator": None})()
        self.actor.eval = lambda: None
        self.calls = []

    def act(self, own, hidden, masks):
        self.calls.append((np.array(own, copy=True), np.array(hidden, copy=True), np.array(masks, copy=True)))
        raw = torch.tensor([[-3., 0., 0.]] * 5)
        return raw, torch.from_numpy(np.asarray(hidden, dtype=np.float32)) + 1.


class LinkLossEnv(SyntheticAdapter):
    """Two visible entries at tick 0 (entry 0 nearest, an anchor 50 m in +x); from tick 1 only entry 1
    stays visible at a fixed world position, so every agent's anchor is lost exactly once while the
    (-x) proposal moves away from it: one Binding opportunity per agent at tick 1, none afterwards."""
    ENTRY1 = np.array([.30, .30])

    def __init__(self, seed, horizon=4):
        super().__init__(seed, horizon)

    def _obs(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        own = self.positions[:, :2] / 1000
        obs[:, :2] = own
        obs[:, 2] = (self.positions[:, 2] - 50) / 100
        rows = np.zeros((5, 20, 3), dtype=np.float32)
        if self.t == 0:
            rows[:, 0, :2] = [.05, 0.]
            rows[:, 0, 2] = .1
        rows[:, 1, :2] = self.ENTRY1[None] - own
        rows[:, 1, 2] = .5
        obs[:, 3:63] = rows.reshape(5, 60)
        obs[:, -1] = self.t / self.horizon
        return obs


def run_panel(arm, horizon=4, policy=None, env=None, namespace=38531):
    policy = policy or FakePolicy()
    env = env or LinkLossEnv(3, horizon)
    rows, counts = [], shared._counts()
    sent_log = []
    original_step = env.step

    def logged_step(actions):
        sent_log.append(np.array(actions, copy=True))
        return original_step(actions)
    env.step = logged_step
    evaluate_wrapped(policy, env, 0, counts, rows.append, arm, namespace, horizon)
    return rows, counts, policy, sent_log


# ---------------------------------------------------------------- substitution semantics

def test_substitution_fires_only_on_the_binding_mask_and_feeds_back_the_sent_command():
    for arm in ("F(M)", "dwell(M)"):
        rows, counts, policy, sent = run_panel(arm)
        proposal = np.tanh(np.array([[-3., 0., 0.]] * 5, dtype=np.float32))
        assert len(sent) == 4 and len(policy.calls) == 4          # one actor call per tick, one step per tick
        assert np.array_equal(sent[0], proposal)                      # tick 0: no valid anchor yet -> proposal
        replacement = sent[1]
        if arm == "F(M)":
            # retrace = clip(-displacement, -1, 1) with displacement = (position - previous) / 30 = proposal
            assert np.allclose(replacement, -proposal, atol=1e-4)
        else:
            assert np.array_equal(replacement, np.zeros((5, 3), np.float32))
        assert np.array_equal(sent[2], proposal) and np.array_equal(sent[3], proposal)
        row = rows[0]
        assert row["arm"] == arm and row["opportunities"] == 5 and row["distinguishable"] == 5
        assert row["retrace" if arm == "F(M)" else "dwell"] == 5 and row["apply"] == 0
        assert row["dwell" if arm == "F(M)" else "retrace"] == 0
        # The actually sent command (not the proposal) feeds back; remaining hold stays 0.
        for t in range(1, 4):
            own = policy.calls[t][0]
            assert np.array_equal(own[:, 104:107], sent[t - 1]) and not own[:, 107].any()
        assert not policy.calls[0][0][:, 104:108].any()
        assert counts["eval_episodes"] == 1 and counts["eval_team_steps"] == 4 and counts["eval_actor_agent_forwards"] == 20
        assert row["steps"] == 4 and row["J"] == row["S"] / 4 and row["reset_seed"] == 100000 * 38531 + 2000


def test_unwrapped_panel_sends_the_proposal_and_carries_no_counters():
    rows, counts, policy, sent = run_panel("M")
    proposal = np.tanh(np.array([[-3., 0., 0.]] * 5, dtype=np.float32))
    assert all(np.array_equal(s, proposal) for s in sent)
    assert "opportunities" not in rows[0] and rows[0]["arm"] == "M"


def test_private_state_resets_per_episode_and_masks_start_at_zero():
    policy = FakePolicy()
    env = LinkLossEnv(3, 4)
    rows, counts = [], shared._counts()
    evaluate_wrapped(policy, env, 0, counts, rows.append, "F(M)", 38531, 4)
    evaluate_wrapped(policy, env, 1, counts, rows.append, "F(M)", 38531, 4)
    first_call_ep0, first_call_ep1 = policy.calls[0], policy.calls[4]
    for own, hidden, masks in (first_call_ep0, first_call_ep1):
        assert not hidden.any() and not masks.any() and not own[:, 104:108].any()
    assert policy.calls[1][2].all() and float(policy.calls[1][1].max()) == 1.  # masks 1, hidden carried
    assert float(policy.calls[3][1].max()) == 3.
    assert rows[0]["reset_seed"] + 1 == rows[1]["reset_seed"]
    # A fresh Binding per episode: the second episode again sees exactly one opportunity per agent.
    assert rows[1]["opportunities"] == 5 and counts["explicit_resets"] == 2


def test_panel_order_does_not_change_a_panel():
    alone = run_panel("dwell(M)")[0]
    run_panel("F(M)")
    after = run_panel("dwell(M)")[0]
    assert alone == after


# ---------------------------------------------------------------- no-op identity with the unchanged evaluator

@pytest.mark.skipif(not ON_POLICY, reason="HMASD_ON_POLICY_ROOT (pinned on-policy checkout) not set")
def test_wrapped_no_substitution_is_identical_to_the_unchanged_m_evaluator(fresh_modules):
    sys.path.insert(0, ON_POLICY)
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    runner.bind_object()
    m = importlib.import_module("experiments.candidates.acvc.cluster_mappo_comparison_b01.mappo")
    assert (m.MASTER, m.EVALUATION_NAMESPACE) == (28531, 38531)
    args, _ = m.configuration()
    args.episode_length = 16
    policy, _ = m.make_policy(args)
    traces = {}
    for label, function in (("unchanged", None), ("wrapped", "M")):
        env = SyntheticAdapter(21, horizon=16)
        rows, counts, trace = [], shared._counts(), []
        original_act, original_step = policy.act, env.step

        def act(own, hidden, masks, _o=original_act, _t=trace):
            raw, h = _o(own, hidden, masks)
            _t.append(("act", np.array(own, copy=True), np.array(hidden, copy=True), np.array(masks, copy=True),
                       raw.detach().clone(), h.detach().clone()))
            return raw, h

        def step(actions, _o=original_step, _t=trace):
            _t.append(("step", np.array(actions, copy=True)))
            return _o(actions)
        policy.act, env.step = act, step
        try:
            if function is None:
                m.evaluate(policy, env, 3, counts, rows.append, horizon=16)
            else:
                evaluate_wrapped(policy, env, 3, counts, rows.append, "M", runner.p.EVALUATION_NAMESPACE, 16)
        finally:
            policy.act, env.step = original_act, original_step
        traces[label] = (rows, counts, trace)
    (rows_a, counts_a, trace_a), (rows_b, counts_b, trace_b) = traces["unchanged"], traces["wrapped"]
    assert rows_a == rows_b and counts_a == counts_b
    assert len(trace_a) == len(trace_b) == 32
    for a, b in zip(trace_a, trace_b):
        assert a[0] == b[0]
        for x, y in zip(a[1:], b[1:]):
            assert (torch.equal(x, y) if torch.is_tensor(x) else np.array_equal(x, y))


# ---------------------------------------------------------------- reduce readout

def make_summary(scores, master=28531, namespace=38531, drop=None):
    panels = {arm: dict(complete=True, available_episodes=64, scores_J=list(s), mean_J=float(np.mean(s)))
              for arm, s in scores.items() if arm != drop}
    if drop:
        panels[drop] = dict(complete=False, available_episodes=0, scores_J=None, mean_J=None)
    counts = dict(train_episodes=4096, train_team_steps=4096 * 256, rollouts=2048, final_checkpoints=1,
                  actor_optimizer_steps=8192, critic_optimizer_steps=8192)
    return dict(object="ACVC_M_DEPLOYMENT_TRANSFER_B01", arm="M", master=master, evaluation_namespace=namespace,
                fit_complete=True, counts=counts, panels=panels, interventions={"F(M)": {"opportunities": 7}})


def test_reduce_reads_t_f_at_the_mei_and_u_from_matched_rows(fresh_modules):
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    runner.bind_object()
    rng = np.random.default_rng(5)
    base = rng.uniform(.2, .5, 64)
    for shift, label in ((.03, "TRANSFERS"), (.004, "WITHIN_MEI"), (-.02, "ADVERSE")):
        out = runner.reduce_transfer(make_summary({"M": base, "F(M)": base + shift, "dwell(M)": base + .002}))
        assert out["complete"] and out["eligible_fit"] and out["primary"] == "T_F"
        assert out["contrasts"]["T_F"]["reading"] == label
        assert out["contrasts"]["T_F"]["mean_J"] == pytest.approx(shift)
        assert out["contrasts"]["T_D"]["reading"] == "WITHIN_MEI"
        u = out["contrasts"]["U"]
        assert u["mean_J"] == pytest.approx(shift - .002)
        assert u["paired_world_differences_J"] == pytest.approx(list((base + shift) - (base + .002)))
        assert out["interventions"] == {"F(M)": {"opportunities": 7}}


def test_reduce_keeps_unaffected_contrasts_when_one_panel_is_incomplete(fresh_modules):
    runner = importlib.import_module("run_acvc_m_deployment_transfer_b01")
    runner.bind_object()
    base = np.linspace(.2, .5, 64)
    out = runner.reduce_transfer(make_summary({"M": base, "F(M)": base + .05, "dwell(M)": base}, drop="dwell(M)"))
    assert not out["complete"]
    assert out["contrasts"]["T_F"]["reading"] == "TRANSFERS"
    assert out["contrasts"]["T_D"]["reading"] == "INCOMPLETE" and out["contrasts"]["U"]["reading"] == "INCOMPLETE"
    wrong = runner.reduce_transfer(make_summary({"M": base, "F(M)": base, "dwell(M)": base}, master=28431))
    assert not wrong["eligible_fit"] and all(v["reading"] == "INCOMPLETE" for v in wrong["contrasts"].values())
