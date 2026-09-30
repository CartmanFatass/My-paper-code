"""Cell b01 piece 3 (coupled_host_planner_distillation): student, layout loss, trainer, runner.

(a) loss: permutation invariance, min over K, equality with the declared B x K x 720 x 6 x 3
expansion, gradient flow, box mapping; (b) JSON / .pt checkpoints agree bit for bit; (c) StudentArm
trigger / hold / re-assignment with stubbed sightings and a planner that raises; (d) no planner
call on a real short host; (e) truth guard; (f) ``fit`` determinism; (g) ``dagger_round`` smoke on
the short host (labels at the decision state, roll-in unchanged); (h) segment loader refusals;
(i) ``run_b01 --phase evaluate`` smoke on one dev world with untrained nets.

Stub and host checks use the shortened static host of the teacher tests (world 9103, 60 steps).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS
from experiments.candidates.coupled_host_planner_distillation import run_b01
from experiments.candidates.coupled_host_planner_distillation import student as S
from experiments.candidates.coupled_host_planner_distillation import teacher_markov as TM
from experiments.candidates.coupled_host_planner_distillation import train as TR
from experiments.candidates.coupled_host_replan_timing import event_host as EH
from experiments.candidates.coupled_host_replan_timing import rules as R

ROOT = Path(__file__).resolve().parents[4]
TM_RUN = ROOT / "runs" / "coupled_host_planner_distillation" / "b01_tm_dev_a01"
B04_RUN = ROOT / "runs" / "coupled_host_joint_skills_stage1" / "b04_b0_dev_a01"
WORLD, STEPS, BUDGET = 9103, 60, 60


def small_host(world=WORLD, max_steps=STEPS):
    kwargs = dict(HOST_CONTRACT_KWARGS)
    kwargs["max_steps"] = max_steps
    env = EH.EventCoupledRelayHost(area_size=5000, seed=world,
                                   event_override={"t_e": B4.NO_EVENT_T_E}, **kwargs)
    env.reset(seed=world)
    return env


def forbid_planner(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("planner called by the student arm")
    monkeypatch.setattr(B4, "plan_on_known", boom)
    monkeypatch.setattr(B4, "d2_planner", boom)
    monkeypatch.setattr(R, "d2_planner", boom)


# ------------------------------------------------------------------------------ loss


def brute_force_loss(pred, targets):
    """The declared formula, literally: B x K x 720 x 6 x 3, min over K and permutations."""
    perms = torch.tensor(list(itertools.permutations(range(6))))
    permuted = pred[:, perms]                                         # [B, 720, 6, 3]
    d = ((permuted[:, None] - targets[:, :, None]) ** 2).sum(-1).mean(-1)   # [B, K, 720]
    return d.reshape(pred.shape[0], -1).min(1).values.mean()


def test_loss_permutation_invariance_min_over_k_and_expansion():
    g = torch.Generator().manual_seed(1)
    pred = torch.rand(5, 6, 3, generator=g, dtype=torch.float64)
    perm = torch.tensor([3, 0, 5, 1, 4, 2])
    assert S.layout_loss(pred, pred[:, perm][:, None]).item() == 0.0     # a permuted copy -> 0
    far = torch.rand(5, 1, 6, 3, generator=g, dtype=torch.float64)
    assert S.layout_loss(pred, far).item() > 0.0
    both = torch.cat([far, pred[:, perm][:, None]], dim=1)               # min over K picks the copy
    assert S.layout_loss(pred, both).item() == 0.0
    y = torch.rand(5, 3, 6, 3, generator=g, dtype=torch.float64)
    per_k = torch.stack([S.per_item_loss(pred, y[:, k:k + 1]) for k in range(3)], 1)
    assert torch.allclose(S.per_item_loss(pred, y), per_k.min(1).values, rtol=0, atol=1e-15)
    assert torch.allclose(S.layout_loss(pred, y), brute_force_loss(pred, y), rtol=0, atol=1e-15)
    assert S.PERMUTATIONS.shape == (720, 6)
    with pytest.raises(ValueError):
        S.layout_loss(pred, y[:, 0])


def test_gradient_flows_and_box_mapping():
    net = S.make_net()
    assert all(p.dtype == torch.float32 for p in net.parameters())
    x = torch.rand(4, 168, generator=torch.Generator().manual_seed(2)).to(S.DTYPE)
    y = torch.rand(4, 3, 6, 3, generator=torch.Generator().manual_seed(3)).to(S.DTYPE)
    loss = S.layout_loss(net(x), y)
    loss.backward()
    grads = [p.grad for p in net.parameters()]
    assert all(g is not None and torch.all(torch.isfinite(g)) for g in grads)
    assert sum(float(g.abs().sum()) for g in grads) > 0
    with torch.no_grad():                                                # mapping formula
        raw = net.body(x).reshape(-1, 6, 3).double()
        metres = S.to_metres(net(x).double().numpy())
    t = torch.tanh(raw).numpy()
    assert np.allclose(metres[..., 0], 2500 * (1 + t[..., 0]), atol=1e-3)
    assert np.allclose(metres[..., 1], 2500 * (1 + t[..., 1]), atol=1e-3)
    assert np.allclose(metres[..., 2], 100 + 50 * t[..., 2], atol=1e-4)
    with torch.no_grad():                                                # ranges at extreme inputs
        big = net(torch.cat([x * 1e4, -x * 1e4]))
    m = S.to_metres(big.double().numpy())
    assert m[..., :2].min() >= 0 and m[..., :2].max() <= 5000
    assert m[..., 2].min() >= 50 and m[..., 2].max() <= 150
    assert np.allclose(S.normalise(S.to_metres(np.full((6, 3), 0.25))), 0.25)


def test_init_determinism_and_checkpoint_json_pt(tmp_path):
    a, b = S.make_net(), S.make_net()
    assert all(torch.equal(p, q) for p, q in zip(a.state_dict().values(), b.state_dict().values()))
    S.save_checkpoint(a, tmp_path / "s0.pt", {"name": "S0"})
    net_j, meta = S.load_checkpoint(tmp_path / "s0.json")
    assert meta == {"name": "S0"}
    assert all(torch.equal(p, q) for p, q in zip(a.state_dict().values(), net_j.state_dict().values()))
    json.loads((tmp_path / "s0.json").read_text())                       # plain JSON
    (tmp_path / "s0.pt").unlink()
    only_json, _ = S.load_checkpoint(tmp_path / "s0.pt")                 # json alone suffices
    assert torch.equal(only_json.body[0].weight, a.body[0].weight)
    S.save_checkpoint(a, tmp_path / "s0.pt", {"name": "S0"})
    payload = json.loads((tmp_path / "s0.json").read_text())
    payload["state_dict"]["body.4.bias"]["values"][0] += 0.5             # tampered copy
    (tmp_path / "s0.json").write_text(json.dumps(payload))
    with pytest.raises(AssertionError, match="disagree"):
        S.load_checkpoint(tmp_path / "s0.json")


# ------------------------------------------------------------------------------ stubbed arm


@pytest.fixture
def scripted(monkeypatch):
    """Scripted sightings {step: {user: xy}}; the planner raises."""
    script: dict[int, dict[int, tuple]] = {}

    def fake_sightings(env):
        step = int(env.current_step)
        seen = {}
        for s in sorted(script):
            if s <= step:
                seen.update(script[s])
        return seen, [len(seen)] * env.n_uavs

    monkeypatch.setattr(B4, "team_sightings", fake_sightings)
    forbid_planner(monkeypatch)
    return script


def test_student_trigger_hold_reassign(scripted, monkeypatch):
    script = scripted
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    script[0] = {u: (100.0 * u, 1000.0) for u in range(3)}              # hold at 0, 10
    script[12] = {u: (100.0 * u, 2000.0) for u in range(3, 6)}          # 6 known: forward at 20
    script[25] = {6: (700.0, 700.0)}                                     # set changed: forward at 30
    script[33] = {6: (750.0, 750.0)}                                     # same set: reuse at 40, 50
    perms = iter([np.arange(6), np.arange(6), np.arange(6)[::-1], np.arange(6)[::-1]])
    monkeypatch.setattr(B4, "assign_targets", lambda initial, layout: next(perms))
    net = S.make_net()
    arm = S.StudentArm(env, WORLD, net)
    seen_inputs = []
    original = net.forward

    def spy(x):
        seen_inputs.append(x.clone())
        return original(x)
    net.forward = spy
    issued = []

    def targets_fn(t):
        out = arm.targets(t)
        issued.append(np.array(out, copy=True))
        return out
    R.rollout(env, targets_fn, 0, STEPS)
    arm.finish(STEPS)
    d = arm.decisions
    assert [x["hold"] for x in d] == [True, True, False, False, False, False]
    assert [x["replanned"] for x in d] == [False, False, True, True, False, False]
    assert [x["cache_hit"] for x in d] == [False, False, False, False, True, True]
    assert arm.forward_passes == 2 == len(seen_inputs) and len(arm.forward_cpu) == 2
    for t in range(20):
        assert np.array_equal(issued[t], spawn)
    layout = arm.cache[frozenset(range(7))]
    assert np.array_equal(d[3]["targets"], layout) and np.array_equal(d[4]["targets"], layout[::-1])
    assert np.array_equal(d[5]["targets"], layout[::-1])
    assert layout[:, :2].min() >= 0 and layout[:, :2].max() <= 5000
    assert layout[:, 2].min() >= 50 and layout[:, 2].max() <= 150
    # the forward pass saw the shared features of the map at the decision (7 known users)
    feat = seen_inputs[1][0].double().numpy()
    assert feat.shape == (168,) and feat[0:150:3].sum() == 7
    rec = arm.record()
    assert rec["forward_passes"] == 2 and rec["forward_steps"] == [20, 30]
    assert rec["hold_steps"] == 20 and rec["cache_hits"] == 2 and rec["planner_evaluations"] == 0
    assert [l["step"] for l in arm.labelled] == [20, 30]


def test_student_holds_below_six_known_all_episode(scripted):
    scripted[0] = {u: (float(u), 1.0) for u in range(5)}
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    result, arm = S.run_student(env, WORLD, S.make_net(), horizon=STEPS)
    assert arm.forward_passes == 0 and arm.record()["hold_steps"] == STEPS
    assert all(np.array_equal(d["targets"], spawn) for d in arm.decisions)


def test_permuted_user_indices_move_feature_blocks_only():
    feat = np.arange(168, dtype=float)
    perm = S.world_user_perm(1000)
    assert np.array_equal(perm, np.random.default_rng([1000, 7]).permutation(50))
    out = S.permute_user_blocks(feat, perm)
    for u in range(50):
        assert np.array_equal(out[3 * perm[u]: 3 * perm[u] + 3], feat[3 * u: 3 * u + 3])
    assert np.array_equal(out[150:], feat[150:])


# ------------------------------------------------------------------------------ real short host


def test_no_planner_call_real_short_host(monkeypatch):
    forbid_planner(monkeypatch)
    env = small_host()
    result, arm = S.run_student(env, WORLD, S.make_net(), horizon=STEPS)
    assert result["t_end"] == STEPS and arm.forward_passes >= 1
    assert arm.record()["planner_evaluations"] == 0
    env2 = small_host()                                                  # determinism
    result2, arm2 = S.run_student(env2, WORLD, S.make_net(), horizon=STEPS)
    assert result["coverage_backhauled"] == result2["coverage_backhauled"]
    assert all(np.array_equal(a["targets"], b["targets"]) for a, b in zip(arm.decisions, arm2.decisions))


# ------------------------------------------------------------------------------ truth guard
# Copied from test_teacher_markov.py (itself from test_b04_lawful_sensing.py), arm = the student.

FORBIDDEN = {"event", "_post_event_users", "post_event_user_positions", "event_info"}


class TruthAccess(AssertionError):
    pass


@pytest.fixture
def truth_guard(monkeypatch):
    state = {"allowed": 0, "accessor": 0, "live": None, "accessor_calls": 0, "rows_read": 0}
    plain = object.__getattribute__
    original_local_users = EH.EventCoupledRelayHost._get_local_users

    class VisibleRows:
        def __init__(self, env):
            self._array = plain(env, "user_positions")
            state["allowed"] += 1
            try:
                self._visible = {int(u) for i in range(plain(env, "n_uavs"))
                                 for u, _ in original_local_users(env, i)}
            finally:
                state["allowed"] -= 1

        def __getitem__(self, key):
            if isinstance(key, (int, np.integer)) and int(key) in self._visible:
                state["rows_read"] += 1
                return np.array(self._array[int(key)], copy=True)
            raise TruthAccess(f"read user_positions[{key!r}] (not a visible row)")

        def __array__(self, *args, **kwargs):
            raise TruthAccess("read the whole user_positions array")

        def __len__(self):
            raise TruthAccess("read the user count through user_positions")

    def guarded(self, name):
        if self is state["live"] and not state["allowed"]:
            if name == "user_positions":
                if state["accessor"]:
                    return VisibleRows(self)
                raise TruthAccess("read env.user_positions outside the sighting accessor")
            if name in FORBIDDEN:
                raise TruthAccess(f"read env.{name}")
        return plain(self, name)

    def allow(function):
        def wrapper(*args, **kwargs):
            state["allowed"] += 1
            try:
                return function(*args, **kwargs)
            finally:
                state["allowed"] -= 1
        return wrapper

    def as_accessor(function):
        def wrapper(*args, **kwargs):
            state["accessor"] += 1
            state["accessor_calls"] += 1
            try:
                return function(*args, **kwargs)
            finally:
                state["accessor"] -= 1
        return wrapper

    monkeypatch.setattr(EH.EventCoupledRelayHost, "step", allow(EH.EventCoupledRelayHost.step))
    monkeypatch.setattr(EH.EventCoupledRelayHost, "_get_local_users", allow(original_local_users))
    monkeypatch.setattr(B4, "team_sightings", as_accessor(B4.team_sightings))
    monkeypatch.setattr(EH.EventCoupledRelayHost, "__getattribute__", guarded)
    return state


def test_student_never_reads_unseen_users(truth_guard):
    env = small_host()
    truth_guard["live"] = env
    with pytest.raises(TruthAccess):                                     # negative control
        _ = env.user_positions
    result, arm = S.run_student(env, WORLD, S.make_net(), horizon=STEPS)
    assert result["t_end"] == STEPS and arm.forward_passes >= 1
    assert truth_guard["accessor_calls"] == STEPS + 1 and truth_guard["rows_read"] > 0
    truth_guard["live"] = None
    assert arm.decisions[0]["n_known"] < env.n_users


# ------------------------------------------------------------------------------ trainer


def test_fit_determinism_tiny_synthetic():
    rng = np.random.default_rng(5)
    X = rng.uniform(0, 1, (20, 168))
    Y = np.stack([rng.uniform(0, 5000, (20, 2, 6)), rng.uniform(0, 5000, (20, 2, 6)),
                  rng.uniform(50, 150, (20, 2, 6))], -1)
    runs = []
    for _ in range(2):
        net = S.make_net()
        runs.append((TR.fit(net, X, Y, epochs=3, batch=8), net))
    (a, na), (b, nb) = runs
    assert a["epoch_loss"] == b["epoch_loss"] and a["steps"] == b["steps"] == 9
    assert a["initial_loss"] == b["initial_loss"] and a["final_loss"] == b["final_loss"]
    assert all(torch.equal(p, q) for p, q in zip(na.state_dict().values(), nb.state_dict().values()))
    assert a["final_loss"] < a["initial_loss"]
    c = TR.fit(S.make_net(), X, Y, epochs=3, batch=8, seed=1)
    assert c["epoch_loss"] != a["epoch_loss"]                            # the shuffling seed matters
    k1 = TR.dataset_loss(na, X, Y, k_first=1)
    assert k1["K"] == 1 and k1["mean"] >= TR.dataset_loss(na, X, Y)["mean"]


def test_dagger_round_smoke_short_host(monkeypatch, tmp_path):
    calls = []
    original = B4.plan_on_known

    def spy(env, users_xy, world, budget):
        calls.append({"step": int(env.current_step), "seed": world, "budget": budget,
                      "positions": np.array(env.uav_positions, copy=True)})
        return original(env, users_xy, world, budget)
    monkeypatch.setattr(B4, "plan_on_known", spy)
    net = S.make_net()
    X, Y, readings = TR.dagger_round(net, [WORLD], budget=BUDGET, horizon=STEPS, out_dir=tmp_path)
    row = readings["per_world"][0]
    assert X.shape == (row["forward_passes"], 168) and Y.shape == (row["forward_passes"], 3, 6, 3)
    assert row["forward_passes"] >= 1 and row["rollin_unchanged_without_labels"] is True
    assert [c["seed"] for c in calls] == [0, 1, 2] * row["forward_passes"]
    assert all(c["budget"] == BUDGET for c in calls)
    saved = json.loads((tmp_path / f"{WORLD}.json").read_text())
    for lab, trio in zip(saved["labelled"], zip(*[iter(calls)] * 3)):
        assert {c["step"] for c in trio} == {lab["step"]} and lab["step"] % 10 == 0
        assert all(np.array_equal(c["positions"], np.asarray(lab["positions"])) for c in trio)
    with pytest.raises(ValueError):
        TR.dagger_round(net, [1000], budget=BUDGET, horizon=STEPS)


def write_world(dirpath, world, seeds, n=1):
    lab = {"step": 0, "known": list(range(6)), "features": [0.0] * 168, "positions": [[0, 0, 50]] * 6,
           "seeds": seeds, "layouts": [[[1.0, 2.0, 50.0]] * 6] * len(seeds)}
    (dirpath / "worlds").mkdir(parents=True, exist_ok=True)
    (dirpath / "worlds" / f"{world}.json").write_text(json.dumps({"world": world, "labelled": [lab] * n}))


def test_load_segment_refusals(tmp_path):
    ok = tmp_path / "ok"
    write_world(ok, 3000, [0, 1, 2], 2)
    write_world(ok, 3001, [0, 1, 2], 1)
    X, Y, meta = TR.load_segment(ok)
    assert X.shape == (3, 168) and Y.shape == (3, 3, 6, 3) and meta["K"] == 3
    assert meta["per_world"] == {3000: 2, 3001: 1}
    mixed = tmp_path / "mixed"
    write_world(mixed, 3000, [0, 1, 2])
    write_world(mixed, 3001, [0])
    with pytest.raises(ValueError, match="K / seeds"):
        TR.load_segment(mixed)
    for world in (1005, 2031):
        panel = tmp_path / f"panel{world}"
        write_world(panel, world, [0, 1, 2])
        with pytest.raises(ValueError, match="panel"):
            TR.load_segment(panel)
        assert TR.load_labelled(panel, allow_panels=True)[2]["n"] == 1


# ------------------------------------------------------------------------------ runner


def test_runner_refuses_direct_out_outside_temp(monkeypatch, tmp_path):
    monkeypatch.delenv(run_b01.ADMISSION_ENV, raising=False)
    outside = ROOT / "runs" / "coupled_host_planner_distillation" / "never_written"
    assert run_b01.main(["--phase", "evaluate", "--out", str(outside), "--checkpoints", "x"]) == 2
    assert not outside.exists()


@pytest.mark.skipif(not ((TM_RUN / "summary.json").exists() and (B04_RUN / "summary.json").exists()),
                    reason="committed dev references absent")
def test_evaluate_smoke_one_world_untrained(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv(run_b01.ADMISSION_ENV, raising=False)
    ck = tmp_path / "ck"
    net = S.make_net()
    for stem in ("s0", "s_bc", "s"):
        S.save_checkpoint(net, ck / f"{stem}.pt", {"name": stem})
    (ck / "s_bc.pt").unlink()                                            # json-only load path
    out = tmp_path / "eval"
    assert run_b01.main(["--phase", "evaluate", "--out", str(out), "--checkpoints", str(ck),
                         "--worlds", "1000"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1000] and summary["panel_complete"] is False
    assert summary["decision_bearing"] is False
    row = summary["per_world"][0]
    assert row["S"] == row["S_bc"] == row["S0"]                           # same untrained net
    assert row["T_M"] is not None and row["B0"] is not None and row["F"] is not None
    for arm in ("S", "S_bc", "S0", "S_perm"):
        assert row["arms"][arm]["replay"] == {"series_identical": True, "contract_reward_identical": True}
        assert row["arms"][arm]["far_cluster_backhauled_share_mean"] is not None
    for pair in ("S-T_M", "S-B0", "S-S_bc", "S_bc-S0", "S_perm-S", "T_M200-T_M", "F-S"):
        assert pair in summary["paired_all_500"]
    flags = summary["purchase_line"]
    assert set(flags["flags"]) == {"S_ge_0.71", "S_minus_TM_ge_-0.03", "TM_ge_0.70"}
    assert flags["band"] in {"purchase", "partial", "stop"} and flags["valid_panel"] is False
    world = json.loads((out / "worlds" / "1000.json").read_text())
    assert len(world["episodes"]["S"]["coverage_backhauled"]) == 500
    assert np.asarray([d["targets"] for d in world["episodes"]["S0"]["decision_record"]]).shape == (50, 6, 3)
    with capsys.disabled():
        print(f"\nreading world=1000 S0={row['S0']:.4f} S_perm={row['S_perm']:.4f} TM={row['T_M']:.4f} "
              f"fwd={row['arms']['S0']['forward_passes']} "
              f"fwd_cpu/pass={row['arms']['S0']['forward_cpu_per_pass_s']:.5f}s")
