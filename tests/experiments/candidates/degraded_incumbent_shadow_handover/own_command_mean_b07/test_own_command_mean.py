"""Small synthetic inputs only: no scientific initializer, native episode or learner."""
from io import BytesIO
import inspect
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_training_engine as engine
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_recurrent_trainer as recurrent
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_training as training
from experiments.candidates.degraded_incumbent_shadow_handover.own_command_mean_b07 import study
from scripts.run_dish_own_command_mean_b07 import publish

OWN, DIRECT = "OWN_COMMAND_MEAN", "DIRECT_MEAN"


@pytest.mark.parametrize("replay", [False, True])
def test_physical_raw_mapping_and_gradient(replay):
    owner = torch.tensor([0, 1, 1, 0])
    raw = torch.arange(4 * 4 * 54, dtype=torch.float32).reshape(4, 4, 54) / 300
    motion_layer = torch.nn.Linear(3, 4)
    x = torch.tensor([[.2, -.4, .1]]).expand(4, 3)
    motion = motion_layer(x)
    expected_own = torch.stack([torch.cat((raw[i, int(o), 8:10], raw[i, 3-int(o), 8:10]))
                                for i, o in enumerate(owner)])
    if replay:
        owner, raw, motion, expected_own = (a[:, None] for a in (owner, raw, motion, expected_own))
    mean = engine._motion_mean(motion, mean_mode=OWN, actor_raw=raw, owner=owner)
    torch.testing.assert_close(mean, 3 * torch.tanh(motion + expected_own / 3), rtol=1e-6, atol=2e-6)
    direct = engine._motion_mean(motion)
    torch.testing.assert_close(direct, 3 * torch.tanh(motion), rtol=0, atol=0)
    zero = engine._motion_mean(motion, mean_mode=OWN, actor_raw=torch.zeros_like(raw), owner=owner)
    torch.testing.assert_close(zero, direct, rtol=0, atol=0)
    assert not torch.allclose(mean, engine._motion_mean(motion, mean_mode=OWN, actor_raw=raw*0, owner=owner))
    (-.5 * (mean - .7).square().sum()).backward()
    assert motion_layer.weight.grad.abs().sum() > 0


def test_live_behavior_replay_and_masks(monkeypatch):
    state = recurrent.RecurrentRolloutState.fresh("STRUCTURED", width=3)
    motion = torch.tensor([[[.1, -.2], [.3, -.4], [.5, -.6], [.7, -.8]]]).expand(3, 4, 2)
    heads = {"motion": motion, "prepare": torch.ones(3, 4, 1)*.3,
             "commit": torch.ones(3, 4, 1)*-.2, "prediction_mean": torch.zeros(3, 4, 4),
             "prediction_cholesky": torch.zeros(3, 4, 10), "service_q": torch.zeros(3, 4, 20)}
    fake = SimpleNamespace(log_std=torch.zeros(4), heads=lambda h: heads,
                           advance_recurrent_hidden=lambda obs, h: h + 1)
    monkeypatch.setattr(recurrent, "_load_policy", lambda checkpoint: fake)
    raw = np.arange(3*4*54, dtype=np.float32).reshape(3,4,54) / 400
    owner = torch.tensor([0, 1, 0])
    observation = {"actor": raw, "owner": owner.numpy(), "renew": np.array([True, True, False])}
    for mode in (DIRECT, OWN):
        policy = recurrent.BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=None,
                                                 state=state, mean_mode=mode)
        monkeypatch.setattr(policy, "normalized_actor", lambda obs: torch.zeros_like(torch.from_numpy(raw)))
        rows = policy.step_rows(observation, sampler=None, global_tick=0, deterministic=True,
                                recurrent_prepared=True)
        selected, pl, cl = engine._role_policy_heads(heads, owner)
        mean = engine._motion_mean(selected, mean_mode=mode, actor_raw=torch.from_numpy(raw), owner=owner)
        torch.testing.assert_close(torch.tensor(rows["raw_action"][:2].copy()).float(), mean[:2], rtol=1e-6, atol=2e-6)
        np.testing.assert_array_equal(rows["raw_action"][2], np.concatenate([raw[2,0,8:10], raw[2,3,8:10]]))
        assert not rows["prepare"][2].any() and not rows["commit"][2].any()
        action = torch.tensor(rows["raw_action"].copy()).float()
        prep = torch.tensor(rows["prepare"][np.arange(3),owner.numpy()].copy()).float()
        commit = torch.tensor(rows["commit"][np.arange(3),owner.numpy()].copy()).float()
        replay_mean, lp = engine._policy_log_prob("STRUCTURED", selected[:,None], fake.log_std,
            action[:,None], pl[:,None], cl[:,None], prep[:,None], commit[:,None],
            torch.tensor(observation["renew"])[:,None], mean_mode=mode,
            actor_raw=torch.from_numpy(raw)[:,None], owner=owner[:,None])
        torch.testing.assert_close(replay_mean[:,0], mean, rtol=1e-6, atol=2e-6)
        torch.testing.assert_close(lp[:,0], policy.last_behavior_log_prob, rtol=1e-6, atol=2e-6)
        motion_lp = -.5 * ((action - mean).square() + math.log(2*math.pi)).sum(-1)
        expected = (motion_lp - torch.nn.functional.binary_cross_entropy_with_logits(pl, prep, reduction="none")
                    - torch.nn.functional.binary_cross_entropy_with_logits(cl, commit, reduction="none"))
        expected *= torch.tensor(observation["renew"])
        torch.testing.assert_close(lp[:,0], expected, rtol=1e-6, atol=2e-6)
        assert lp[2] == 0
    # The changed repeated engine term consumes the returned mean, without a new detached law.
    source = inspect.getsource(engine.run_full_4096_dry_update)
    assert 'mean, log_prob = _policy_log_prob(' in source
    assert 'actor_raw=data["actor_raw"][selected]' in source
    assert 'mean = 3.0 * torch.tanh(motion)' not in source
    assert 'data["action"][selected] - mean' in source


def payload(update=0):
    out = BytesIO()
    torch.save({"model": {"test_weight": torch.tensor([1.])}, "update": update,
                "optimizer": {"param_groups": [{"lr": 3e-4}, {"lr": 3e-4}]},
                "welford": {n: SimpleNamespace(count=0) for n in ("actor", "snapshot", "critic")}}, out)
    return out.getvalue()


def test_persistent_mode_reconstruction_and_default(monkeypatch):
    calls = []
    def update(**kw):
        calls.append(kw)
        return {"private_checkpoint_bytes": payload(1), "update": 1}
    monkeypatch.setattr(training, "_retained_full_update", update)
    for mode in (DIRECT, OWN):
        trainer = training.PersistentTrainer(arm="STRUCTURED", checkpoint_bytes=payload(), mean_mode=mode)
        trainer.run_update({"synthetic": True}, source_label="INTERCEPTED")
        assert calls[-1]["mean_mode"] == mode
    assert training.PersistentTrainer(arm="STRUCTURED").mean_mode == DIRECT
    constructed = []
    class Policy:
        def __init__(self, **kw):
            constructed.append(kw)
    monkeypatch.setattr(recurrent, "BatchedRecurrentPolicy", Policy)
    stream_calls = []
    monkeypatch.setattr(recurrent, "MasterAddressedPolicySampler", lambda **kw: stream_calls.append(kw))
    monkeypatch.setattr(recurrent, "MasterAddressedTrainResetFactory", lambda **kw: stream_calls.append(kw))
    for mode in (DIRECT, OWN):
        flow = recurrent.NativePersistentTrainingFlow(native=SimpleNamespace(width=32), arm="STRUCTURED",
                 master=b"synthetic-nonexperimental", block=0, checkpoint_bytes=payload(), mean_mode=mode)
        assert flow.trainer.mean_mode == mode and constructed[-1]["mean_mode"] == mode
        flow.apply_update({"synthetic": True})
        assert constructed[-1]["mean_mode"] == mode
        assert calls[-1]["mean_mode"] == mode
    assert all(c["master"] == b"synthetic-nonexperimental" and c["arm"] == "STRUCTURED" for c in stream_calls)


def test_intercepted_full_pair_publication_master_counts_and_cost(monkeypatch, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("pair")
    b04 = study.b04
    calls = []
    sentinel = b"synthetic-master-not-experimental"
    monkeypatch.setattr(b04, "master", lambda seed, family: calls.append(("master", seed, family)) or sentinel)
    monkeypatch.setattr(b04, "load_host", lambda host: None)
    monkeypatch.setattr(b04, "build_master_addressed_initial_state", lambda **kw: calls.append(("init",kw)) or payload())
    monkeypatch.setattr(b04, "_reset_row", lambda master, coordinate: {"master": master.hex(), "key": coordinate.canonical_key()})
    monkeypatch.setattr(b04.backend, "native_batch_from_rows", lambda rows, library: SimpleNamespace(observe=lambda: {}, width=len(rows)))
    class Reset:
        def __init__(self, **kw): calls.append(("reset", kw))
        def rows(self, waves): return [None]*32
    monkeypatch.setattr(b04, "MasterAddressedTrainResetFactory", Reset)
    class Policy:
        def __init__(self, **kw):
            calls.append(("policy",kw))
            self.mean_mode = kw["mean_mode"]
    monkeypatch.setattr(b04, "BatchedRecurrentPolicy", Policy)
    class Flow:
        def __init__(self, **kw):
            calls.append(("flow",kw))
            self.trainer = SimpleNamespace(checkpoint_bytes=kw["checkpoint_bytes"])
            self.progress = kw["progress"]
        def collect_update(self, observation): return {}
        def apply_update(self, fragments):
            self.progress["ordinary_training_transitions"] += 4096
            self.progress["optimizer_steps"] += 32
            return dict(optimizer_steps=32, mean_loss=1., mean_gradient_norm=1., losses_finite=True, gradient_norms_finite=True)
    monkeypatch.setattr(b04, "NativePersistentTrainingFlow", Flow)
    monkeypatch.setattr(b04, "parameter_movement", lambda initial, final: {"l2_displacement": 0})
    def evaluate(native, policy, deadline, progress, record, **kw):
        assert kw["record_first_transfer"]
        progress["evaluation_ticks"] += 10
        record.update(complete=True, service_ticks=100 + (30 if policy.mean_mode == OWN else 0),
                      legal_transfers=0, first_legal_transfer_tick=None, completed_ticks=10,
                      unstepped_zero_service_ticks=1190, terminal={"native_terminal":True},
                      hard_events={"invalid_commit": 3})
    monkeypatch.setattr(b04, "evaluate_episode", evaluate)
    result = {"status":"INCOMPLETE"}
    study.run_study(tmp_path, study.time.perf_counter(), 10, result)
    assert result["status"] == "COMPLETE"
    assert result["primary"]["Delta_mean"] == 30 and result["primary"]["D_OWN"] == 0
    assert len([c for c in calls if c[0] == "init"]) == 1
    flows = [c[1] for c in calls if c[0] == "flow"]
    assert [f["mean_mode"] for f in flows] == [DIRECT, OWN]
    assert all(f["master"] == sentinel and f["arm"] == "STRUCTURED" for f in flows)
    assert all(c[1:] == (127,study.OBJECT) for c in calls if c[0] == "master")
    assert all(c[1]["master"] == sentinel for c in calls if c[0] in ("init","reset"))
    for mode in (DIRECT, OWN):
        arm = result["arms"][mode]
        assert arm["evaluation_ticks"] == 80 and arm["ordinary_training_transitions"] == 65536
        assert arm["optimizer_steps"] == 512 and len(arm["initial_rows"]) == len(arm["evaluation_rows"]) == 4
        assert all(r["mean_mode"] == mode for r in arm["initial_rows"] + arm["evaluation_rows"])
        arm["exclusive_wall_seconds"] = 100 if mode == DIRECT else 200
    cost = study.allocate_cost(result, 0, 20, now=340)
    assert cost["shared_seconds"] == 60 and cost["charged_pair_seconds"] == 360
    assert cost["charged_arm_seconds"] == {DIRECT:130, OWN:230}
    publish(tmp_path,result)
    readback = json.loads((tmp_path/"summary.json").read_text())
    assert readback["cost"] == cost
    result["arms"][OWN]["initial_rows"].pop()
    result["primary"] = study.reduce_pair(result["arms"])
    assert result["primary"]["Delta_mean"] == 30 and result["primary"]["D_OWN"] is None
    assert result["primary"]["status"] == "FINAL_PRIMARY_COMPLETE"
    publish(tmp_path,result)
    assert json.loads((tmp_path/"summary.json").read_text())["primary"]["D_OWN"] is None


@pytest.mark.parametrize("delta,plus,band,minus", [(24,True,False,False),(-24,False,False,True),(0,False,True,False)])
def test_primary_thresholds_and_adverse_rows(delta,plus,band,minus):
    arms = {}
    for mode in (DIRECT, OWN):
        arms[mode] = dict(completed_updates=16,ordinary_training_transitions=65536,optimizer_steps=512)
        for phase,field in (("initial","initial_rows"),("final","evaluation_rows")):
            values = [100]*4 if mode == DIRECT else ([200]*4 if phase == "initial" else [100+delta-30,100+delta+10,100+delta+10,100+delta+10])
            arms[mode][field] = [dict(coordinate=c.canonical_key(),service_ticks=v,complete=True,legal_transfers=0)
                                  for c,v in zip(study.b04.coordinates(),values)]
    r=study.reduce_pair(arms)
    assert r["Delta_mean"] == delta and len(r["final_differences"]) == 4
    assert r["branch_facts"]["at_least_plus24"] == plus
    assert r["branch_facts"]["open_band"] == band
    assert r["branch_facts"]["at_most_minus24"] == minus
    assert r["branch_facts"]["increment_with_own_initial_loss"] == (delta>0)
    arms[OWN]["evaluation_rows"][0]["complete"] = False
    assert study.reduce_pair(arms)["Delta_mean"] is None


@pytest.mark.parametrize("transfer_tick", [None, 2])
def test_native_terminal_and_first_post_step_tick_with_intercepted_native(monkeypatch, transfer_tick):
    from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import study as b02
    class Native:
        tick = 0
        def observe(self):
            return {"terminal": np.array([self.tick == 3]), "owner": np.array([0]),
                    "cas_applied": np.array([int(self.tick == transfer_tick)]), "service": np.array([1])}
        def step(self, rows):
            self.tick += 1
            return self.observe()
    native = Native()
    def state(n):
        return [{"tick": n.tick, "total_energy": float(n.tick), **dict.fromkeys(b02.HARD_EVENTS,0)}]
    monkeypatch.setattr(b02, "native_state", state)
    monkeypatch.setattr(b02, "terminal_facts", lambda n, ticks: {"native_tick": n.tick, "actual_completed_ticks":ticks})
    policy = SimpleNamespace(step_rows=lambda *a, **kw: None, apply_native_promotion=lambda **kw: None)
    progress, record = b02.new_progress(), {}
    b02.evaluate_episode(native, policy, float("inf"), progress, record, record_first_transfer=True)
    assert record["complete"] and record["service_ticks"] == 3
    assert record["unstepped_zero_service_ticks"] == 1197 and record["completed_ticks"] == 3
    assert record["first_legal_transfer_tick"] == transfer_tick
    assert record["service_at_or_after_transfer"] == (0 if transfer_tick is None else 2)
    assert progress["ordinary_training_transitions"] == 0 and progress["evaluation_ticks"] == 3


def test_cost_cap_preserves_incomplete_and_exposure(tmp_path_factory):
    output = tmp_path_factory.mktemp("cap")
    result = {"status":"COMPLETE", "arms":{DIRECT:study.b04.new_progress(), OWN:study.b04.new_progress()}}
    result["arms"][DIRECT]["exclusive_wall_seconds"] = 1780
    study.allocate_cost(result, 0, 20, now=1810)
    assert result["status"] == "INCOMPLETE" and result["budget_exhausted"]
    result["actual_exposure"] = study.exposure(result["arms"])
    assert result["actual_exposure"][OWN]["H_measured"] is False
    assert result["actual_exposure"][OWN]["consequence_steps_upper"] == 0
    assert study.planned_cost()["per_arm"]["evaluation_ticks_upper"] == 9600
    publish(output,result)
    assert json.loads((output/"summary.json").read_text())["budget_exhausted"]


def test_publication_deadline_uses_tightest_arm_and_stays_armed():
    from scripts import run_dish_own_command_mean_b07 as runner
    result = {"status":"COMPLETE", "arms": {DIRECT:{"exclusive_wall_seconds":1780},
                                            OWN:{"exclusive_wall_seconds":100}}}
    # At wall1890 and prior10, shared20: DIRECT1790, OWN110. Publication may
    # consume18 shared seconds (20 remaining minus2 closure), not pair slack.
    assert runner.publication_deadline(study, result, 0, 10, 1890) == 1908
    assert runner.publication_deadline(None, {}, 0, 10, 20) == 3588
    source = inspect.getsource(runner.main)
    assert 'signal.signal(signal.SIGALRM, signal.SIG_DFL)' in source
    assert 'signal.setitimer(signal.ITIMER_REAL, 0)' not in source
