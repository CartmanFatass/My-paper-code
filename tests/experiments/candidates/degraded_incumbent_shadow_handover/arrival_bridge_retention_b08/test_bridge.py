"""Synthetic fixed tensors only; no B08 master, native model or scientific learner."""
from io import BytesIO
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_training_engine as engine
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_recurrent_trainer as recurrent
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_training as training
from experiments.candidates.degraded_incumbent_shadow_handover.arrival_bridge_retention_b08 import study
from scripts.run_dish_arrival_bridge_retention_b08 import publish


def payload(mode=None):
    model = engine.ExactPolicyGraph()
    engine.deterministic_test_initialize(model)
    matrices = [p for n, p in model.named_parameters() if p.ndim >= 2 and "flex_" not in n]
    ids = {id(p) for p in matrices}
    others = [p for p in model.parameters() if id(p) not in ids]
    optimizer = torch.optim.AdamW([{"params": matrices, "weight_decay": 1e-4},
                                   {"params": others, "weight_decay": 0.0}], lr=3e-4)
    data = {"model": model.state_dict(), "optimizer": optimizer.state_dict(), "update": 0,
            "welford": {n: engine.WelfordState.empty(w) for n,w in
                        (("actor",54),("snapshot",18),("critic",58))}}
    if mode is not None:
        data["arrival_bridge_mode"] = mode
    buffer = BytesIO()
    torch.save(data, buffer)
    return buffer.getvalue()


@pytest.mark.parametrize("mode", study.ARMS)
def test_reset_owner_mask_and_gradient(mode):
    model = recurrent._load_policy(payload(mode))
    with torch.no_grad():
        model.snapshot_bridge.weight.zero_()
        model.snapshot_bridge.bias.zero_()
    hidden = torch.linspace(-.8,.7,6*4*128).reshape(6,4,128).requires_grad_()
    original = hidden.detach().clone()
    snapshot = torch.linspace(-.6,.9,6*18).reshape(6,18)
    owner = torch.tensor([0,1,0,1,0,1])
    active = torch.tensor([1,1,0,0,1,1], dtype=torch.bool)
    reset = torch.tensor([1,1,1,1,0,0], dtype=torch.float32)
    out = model.prepare_recurrent_hidden(hidden, snapshot, active, reset, owner)
    expected = original.clone()
    expected[4:] = 0
    factor = .5 if mode == "HALF_RETAIN" else 0
    expected[0,3] *= factor
    expected[1,1] *= factor
    torch.testing.assert_close(out, expected)
    torch.testing.assert_close(hidden, original)
    out.sum().backward()
    expected_grad = torch.ones_like(hidden)
    expected_grad[4:] = 0
    expected_grad[0,3] = factor
    expected_grad[1,1] = factor
    torch.testing.assert_close(hidden.grad, expected_grad)
    assert model.snapshot_bridge.weight.grad.abs().sum() > 0


@pytest.mark.parametrize("mode", study.ARMS)
def test_live_replay_likelihood_reset_and_promotion(mode, monkeypatch):
    torch.set_num_threads(1)
    state = recurrent.RecurrentRolloutState.fresh("STRUCTURED", width=2)
    state.hidden = torch.linspace(-.7,.6,2*4*128).reshape(2,4,128)
    initial = state.hidden.clone()
    policy = recurrent.BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=payload(mode), state=state)
    original = policy.model.prepare_recurrent_hidden
    calls = []
    def prepare(*args):
        calls.append(1)
        return original(*args)
    monkeypatch.setattr(policy.model, "prepare_recurrent_hidden", prepare)
    stored = {k: [] for k in ("obs","snapshot","mask","reset","owner","promote","states","action","prep","commit","renew","lp")}
    owner = np.array([0,1])
    sampler = SimpleNamespace(normal=lambda **kw: .2 if kw["lane"] else -.3,
                              bernoulli=lambda **kw: int(kw["probability"] > .45))
    for tick in range(64):
        raw = np.sin(np.arange(2*4*54).reshape(2,4,54)*.07+tick*.13).astype(np.float32)
        snapshot = np.cos(np.arange(36).reshape(2,18)*.11+tick*.09).astype(np.float32)
        mask = np.array([tick%7==0,tick%5==0])
        resets = np.array([tick==0,tick==35])
        renew = np.array([tick%3==0,tick%4==0])
        observation = dict(actor=raw, snapshot_payload=snapshot, snapshot_delivery_mask=mask,
                           owner=owner.copy(), renew=renew)
        if tick%2:
            policy.prepare_recurrent(observation, reset_lanes=resets)
        rows = policy.step_rows(observation, sampler=sampler, global_tick=tick, deterministic=False,
                                reset_lanes=resets, recurrent_prepared=bool(tick%2))
        promotion = np.array([tick==19,tick==38])
        values = dict(obs=policy.normalized_actor(observation),snapshot=torch.from_numpy(snapshot),
                      mask=torch.from_numpy(mask),reset=torch.from_numpy((~resets).astype(np.float32)),
                      owner=torch.from_numpy(owner.copy()),promote=torch.from_numpy(promotion),
                      states=policy.state.hidden.clone(), action=torch.tensor(rows["raw_action"].copy()).float(),
                      prep=torch.tensor(rows["prepare"][np.arange(2),owner].copy()).float(),
                      commit=torch.tensor(rows["commit"][np.arange(2),owner].copy()).float(),
                      renew=torch.from_numpy(renew),lp=policy.last_behavior_log_prob.clone())
        for key,value in values.items(): stored[key].append(value)
        policy.state.hidden = recurrent._promotion(policy.state.hidden, promotion, owner, np.ones(2))
        owner = np.where(promotion,1-owner,owner)
    assert len(calls) == 64
    data = {k:torch.stack(v,dim=1) for k,v in stored.items()}
    replay = recurrent._load_policy(payload(mode))
    states,heads = replay.replay(data["obs"],initial,data["snapshot"],data["mask"],data["reset"],
                                 data["owner"],data["promote"])
    torch.testing.assert_close(states,data["states"],rtol=2e-5,atol=2e-6)
    motion,prep,commit = engine._role_policy_heads(heads,data["owner"])
    _,lp = engine._policy_log_prob("STRUCTURED",motion,replay.log_std,data["action"],prep,commit,
                                  data["prep"],data["commit"],data["renew"])
    torch.testing.assert_close(lp,data["lp"],rtol=2e-5,atol=3e-6)
    assert torch.all(lp[~data["renew"]] == 0)
    (-lp.mean()+states.square().mean()).backward()
    assert replay.snapshot_encoder.weight.grad.abs().sum() > 0
    assert replay.snapshot_bridge.weight.grad.abs().sum() > 0


@pytest.mark.parametrize("mode", study.ARMS)
def test_real_synthetic_update_checkpoint_reconstruction(mode):
    torch.set_num_threads(1)
    source = payload()
    initial = study.b04.set_learning_rate(source,3e-5,arrival_bridge_mode=mode)
    left = torch.load(BytesIO(source),weights_only=False)
    right = torch.load(BytesIO(initial),weights_only=False)
    for key in left["model"]:
        torch.testing.assert_close(left["model"][key],right["model"][key],rtol=0,atol=0)
    assert recurrent._load_policy(source).arrival_bridge_mode == "REPLACE"
    assert recurrent._load_policy(initial).arrival_bridge_mode == mode
    trainer = training.PersistentTrainer(arm="STRUCTURED",checkpoint_bytes=initial)
    receipt = trainer.run_update(engine._synthetic_complete_update(),source_label="B08_TEST_SYNTHETIC_NO_NATIVE")
    updated = torch.load(BytesIO(trainer.checkpoint_bytes),weights_only=False)
    assert receipt["optimizer_steps"] == 32 and receipt["losses_finite"]
    assert updated["arrival_bridge_mode"] == mode and updated["update"] == 1
    assert study.b04.learning_rates(trainer.checkpoint_bytes) == [3e-5,3e-5]
    reloaded = recurrent.BatchedRecurrentPolicy(arm="STRUCTURED",checkpoint_bytes=trainer.checkpoint_bytes,
                                               state=recurrent.RecurrentRolloutState.fresh("STRUCTURED",width=1))
    assert reloaded.model.arrival_bridge_mode == mode


def test_final_only_pair_counts_mode_and_publication(monkeypatch,tmp_path_factory):
    out = tmp_path_factory.mktemp("pair")
    b04 = study.b04
    calls = []
    sentinel = b"synthetic-master-not-experimental"
    monkeypatch.setattr(b04,"master",lambda seed,family: calls.append((seed,family)) or sentinel)
    monkeypatch.setattr(b04,"load_host",lambda host: None)
    initial = payload()
    monkeypatch.setattr(b04,"build_master_addressed_initial_state",lambda **kw: initial)
    monkeypatch.setattr(b04,"_reset_row",lambda master,coordinate: {"key":coordinate.canonical_key()})
    monkeypatch.setattr(b04.backend,"native_batch_from_rows",lambda rows,library: SimpleNamespace(observe=lambda: {},width=len(rows)))
    class Reset:
        def __init__(self,**kw): assert kw["master"]==sentinel and kw["arm"]=="STRUCTURED"
        def rows(self,waves): return [None]*32
    monkeypatch.setattr(b04,"MasterAddressedTrainResetFactory",Reset)
    class Policy:
        def __init__(self,**kw): self.model=recurrent._load_policy(kw["checkpoint_bytes"])
    monkeypatch.setattr(b04,"BatchedRecurrentPolicy",Policy)
    class Flow:
        def __init__(self,**kw):
            assert kw["mean_mode"]=="DIRECT_MEAN" and kw["arm"]=="STRUCTURED"
            self.trainer=SimpleNamespace(checkpoint_bytes=kw["checkpoint_bytes"])
            self.progress=kw["progress"]
        def collect_update(self,obs): return {}
        def apply_update(self,fragments):
            self.progress["ordinary_training_transitions"]+=4096
            self.progress["optimizer_steps"]+=32
            return dict(optimizer_steps=32,mean_loss=1.,mean_gradient_norm=1.,losses_finite=True,gradient_norms_finite=True)
    monkeypatch.setattr(b04,"NativePersistentTrainingFlow",Flow)
    monkeypatch.setattr(b04,"parameter_movement",lambda initial,final: {})
    counts = dict.fromkeys(study.ARMS,0)
    def evaluate(native,policy,deadline,progress,record,**kw):
        assert kw["record_first_transfer"] and record["phase"]=="final"
        mode=policy.model.arrival_bridge_mode
        ordinal=counts[mode]; counts[mode]+=1
        score=100 if mode=="REPLACE" else [60,170,160,130][ordinal]
        ticks=1200 if ordinal else 600
        progress["evaluation_ticks"]+=ticks
        record.update(complete=True,service_ticks=score,completed_ticks=ticks,
                      unstepped_zero_service_ticks=1200-ticks,terminal={"native_terminal":ticks<1200},
                      legal_transfers=int(ordinal==2),first_legal_transfer_tick=8 if ordinal==2 else None,
                      hard_events=dict.fromkeys(b04.HARD_EVENTS,3),energy=2000)
    monkeypatch.setattr(b04,"evaluate_episode",evaluate)
    result={"status":"INCOMPLETE"}
    study.run_study(out,study.time.perf_counter(),20,result)
    assert counts=={"REPLACE":4,"HALF_RETAIN":4} and result["status"]=="COMPLETE"
    assert all(c==(137,study.OBJECT) for c in calls)
    assert result["shared"]["reference_rows"]==[]
    assert result["primary"]["Delta_bridge"]==30
    assert [r["difference"] for r in result["primary"]["paired_rows"]]==[-40,70,60,30]
    assert result["primary"]["paired_rows"][0]["HALF_RETAIN"]["first_legal_transfer_tick"] is None
    for arm in result["arms"].values():
        assert arm["optimizer_steps"]==512 and arm["ordinary_training_transitions"]==65536
        assert len(arm["evaluation_rows"])==4 and arm["configuration"]["learning_rate"]==3e-5
    result["actual_exposure"]=study.exposure(result["arms"])
    publish(out,result)
    assert json.loads((out/"summary.json").read_text())["primary"]==result["primary"]
    result["arms"]["HALF_RETAIN"]["evaluation_rows"][0]["complete"]=False
    assert study.reduce_pair(result["arms"])["Delta_bridge"] is None


@pytest.mark.parametrize("delta,positive,band,negative",[(24,True,False,False),(-24,False,False,True),(0,False,True,False)])
def test_primary_branches_and_separate_caps(delta,positive,band,negative):
    arms={m:dict(completed_updates=16,ordinary_training_transitions=65536,optimizer_steps=512,
                evaluation_rows=[dict(coordinate=c.canonical_key(),complete=True,service_ticks=100+(delta if m=="HALF_RETAIN" else 0))
                                 for c in study.b04.coordinates()]) for m in study.ARMS}
    facts=study.reduce_pair(arms)["branch_facts"]
    assert (facts["at_least_plus24"],facts["open_band"],facts["at_most_minus24"])==(positive,band,negative)
    arms["REPLACE"]["exclusive_wall_seconds"]=901
    result={"status":"COMPLETE","arms":arms}
    cost=study.allocate_cost(result,0,20,now=911)
    assert result["budget_exhausted"] and cost["shared_seconds"]==30
    arms["REPLACE"]["exclusive_wall_seconds"]=100
    result={"status":"COMPLETE","arms":arms}
    study.allocate_cost(result,0,20,now=390)
    assert result["budget_exhausted"]  # Shared310 cannot borrow unused arm allowance.
    assert study.shared_deadline({"arms":{}},0,20,now=30)==190
    assert study.planned_cost()["per_arm"]["whole_arm_cap_seconds"]==1050
