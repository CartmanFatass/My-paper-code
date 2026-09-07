"""Synthetic boundary checks only: no scientific initializer, training or native episode."""
from functools import partial
from io import BytesIO
import hashlib
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.sampled_execution_b06 import study
from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b05 import study as b05
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_recurrent_trainer as recurrent
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import WelfordState

KEY = "DISH/RBHR/R06/EVALUATION_COORDINATE/0/CLAIM/TARGET_VISUAL_MASK/K8/0"
TRAIN_MASTER = hashlib.sha256(b"DISH-SAMPLED-EXECUTION-B06/seed/113").digest()
POLICY_MASTER = hashlib.sha256(b"DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY/seed/113").digest()


def payload(weight=1.0, count=0):
    stream = BytesIO()
    torch.save({"model": {"weight": torch.tensor([weight])},
                "optimizer": {"param_groups": [{"lr": 3e-4}, {"lr": 3e-4}]},
                "welford": {name: SimpleNamespace(count=count) for name in ("actor", "snapshot", "critic")}}, stream)
    return stream.getvalue()


def episode_values(service, *, energy=100.0, completed=1200, transfer=None):
    return dict(service_ticks=service, complete=True, energy=energy, completed_ticks=completed,
                unstepped_zero_service_ticks=1200-completed, fixed_horizon=1200,
                legal_transfers=int(transfer is not None), first_legal_transfer_tick=transfer,
                service_before_transfer=service if transfer is None else 0,
                service_at_or_after_transfer=0 if transfer is None else service,
                hard_events=dict.fromkeys(study.b04.HARD_EVENTS, 0))


def test_selected_master_reaches_every_shared_consumer_and_fixed_final_bytes(monkeypatch, tmp_path):
    b04 = study.b04
    assert study.master() == TRAIN_MASTER and study.evaluation_policy_master() == POLICY_MASTER
    assert b04.master() == hashlib.sha256(b"DISH-CONTROL-LOW-LR-B04/seed/89").digest()
    assert b05.master() == hashlib.sha256(b"DISH-CONTROL-LOW-LR-B04/seed/101").digest()
    assert b04.configuration("LOW_LR")["seed"] == 89
    assert b05.configuration("LOW_LR")["object"] == "DISH-CONTROL-LOW-LR-B05"
    seen = {"initial": [], "resets": [], "factories": [], "flows": [], "native": [],
            "states": [], "policies": [], "evaluations": []}
    initial = payload()
    final = b04.set_learning_rate(payload(2.0, count=40), 3e-5)

    def initializer(**kwargs):
        seen["initial"].append(kwargs)
        return initial

    def reset_row(master_digest, coordinate):
        seen["resets"].append(master_digest)
        return {"master": master_digest.hex(), "key": coordinate.canonical_key()}

    class ResetFactory:
        def __init__(self, **kwargs):
            seen["factories"].append(kwargs)
            self.master = kwargs["master"]
        def rows(self, wave):
            assert wave.tolist() == [0] * 32
            return tuple({"master": self.master.hex(), "lane": lane} for lane in range(32))

    def native(rows, **kwargs):
        value = SimpleNamespace(rows=rows, observe=lambda: None)
        seen["native"].append(value)
        return value

    def fresh(*args, **kwargs):
        value = object()
        seen["states"].append(value)
        return value

    class Policy:
        def __init__(self, **kwargs):
            seen["policies"].append(kwargs)
            loaded = torch.load(BytesIO(kwargs["checkpoint_bytes"]), weights_only=False)
            self.model = SimpleNamespace(state_dict=lambda: loaded["model"])

    class Flow:
        def __init__(self, **kwargs):
            seen["flows"].append(kwargs)
            self.progress = kwargs["progress"]
            self.trainer = SimpleNamespace(checkpoint_bytes=kwargs["checkpoint_bytes"])
        def collect_update(self, observation):
            return None
        def apply_update(self, fragments):
            self.progress["ordinary_training_transitions"] += 4096
            self.progress["next_label_steps"] += 4096
            self.progress["optimizer_steps"] += 32
            self.trainer.checkpoint_bytes = final
            return dict(optimizer_steps=32, mean_loss=0.1, mean_gradient_norm=0.2,
                        losses_finite=True, gradient_norms_finite=True)

    def evaluate(native, policy, deadline, progress, record, *, sampler=None,
                 deterministic=True, record_first_transfer=False):
        assert record_first_transfer
        assert deterministic == (sampler is None)
        if sampler is not None:
            assert sampler.master_digest == POLICY_MASTER
            assert sampler.canonical_key == record["coordinate"] and sampler.sample == record["sample"]
        seen["evaluations"].append((native, sampler, deterministic))
        record.update(episode_values(100))
        progress["evaluation_ticks"] += 1200

    monkeypatch.setattr(b04, "load_host", lambda host: None)
    monkeypatch.setattr(b04, "build_master_addressed_initial_state", initializer)
    monkeypatch.setattr(b04, "_reset_row", reset_row)
    monkeypatch.setattr(b04, "MasterAddressedTrainResetFactory", ResetFactory)
    monkeypatch.setattr(b04.backend, "native_batch_from_rows", native)
    monkeypatch.setattr(b04, "RecurrentRolloutState", SimpleNamespace(fresh=fresh))
    monkeypatch.setattr(b04, "BatchedRecurrentPolicy", Policy)
    monkeypatch.setattr(study, "SampledEvaluationPolicy", Policy)
    monkeypatch.setattr(b04, "TrainingMeasurements", lambda native, *args: native)
    monkeypatch.setattr(b04, "NativePersistentTrainingFlow", Flow)
    monkeypatch.setattr(study, "evaluate_modal", partial(evaluate, record_first_transfer=True))
    monkeypatch.setattr(study.b02, "evaluate_episode", evaluate)
    result = {}
    study.run_study(tmp_path, math.inf, result)
    assert result["status"] == "COMPLETE"
    assert seen["initial"] == [dict(master=TRAIN_MASTER, block=0, arm="STRUCTURED")]
    assert seen["factories"] == [dict(master=TRAIN_MASTER, block=0, arm="STRUCTURED")]
    assert seen["resets"] == [TRAIN_MASTER] * 8
    assert len(seen["flows"]) == 1 and seen["flows"][0]["master"] == TRAIN_MASTER
    assert seen["flows"][0]["forecast_package"] is False
    loaded = torch.load(BytesIO(seen["flows"][0]["checkpoint_bytes"]), weights_only=False)
    assert loaded["model"]["weight"].tolist() == [1.0]
    assert all(s.count == 0 for s in loaded["welford"].values())
    assert b04.learning_rates(seen["flows"][0]["checkpoint_bytes"]) == [3e-5, 3e-5]
    assert [p["checkpoint_bytes"] for p in seen["policies"]] == [initial] * 4 + [final] * 12
    assert len({id(s) for s in seen["states"]}) == 16
    assert len({id(n) for n,_,_ in seen["evaluations"]}) == 16
    assert [d for _,_,d in seen["evaluations"]] == [True] * 8 + [False] * 8
    assert [p["forecast_package"] for p in seen["policies"]] == [False] * 16
    reset_rows = json.loads((tmp_path / "shared/resets.json").read_text())
    assert all(n.rows == (reset_rows[s.canonical_key],) for n,s,d in seen["evaluations"] if s is not None)
    for panel in (result["reference"], result["learner"]):
        assert (panel["seed"], panel["object"], panel["master_hex"]) == (113, study.OBJECT, TRAIN_MASTER.hex())
    assert result["learner"]["configuration"]["master_hex"] == TRAIN_MASTER.hex()
    exposure = study.actual_exposure(result)
    assert exposure["evaluation_rows_complete"] == 16 and exposure["executed_evaluation_ticks"] == 19200
    assert exposure["learner"]["ordinary_training_transitions"] == 65536
    assert exposure["learner"]["optimizer_steps"] == 512
    assert (tmp_path / "learner/checkpoint_update16.pt").read_bytes() == final
    assert list(tmp_path.rglob("checkpoint_*.pt")) == [tmp_path / "learner/checkpoint_update16.pt"]


def test_width1_exact_addresses_word_transform_and_one_batch_per_renewal(monkeypatch):
    calls = []
    def words(master, addresses):
        calls.append((master, addresses))
        return tuple(0x8000000000000000 if a.endswith("/draw/1") else 0x4000000000000000
                     for a in addresses)
    monkeypatch.setattr(study.b04.backend, "rng_words_native", words)
    sampler = study.EvaluationPolicySampler(master_digest=POLICY_MASTER, canonical_key=KEY, sample=0)
    sampler.begin_tick(owner=0, tick=17, renew=True)
    normals = [sampler.normal(lane=0, tick=17, field=f) for f in study.MOTION_FIELDS]
    assert normals == pytest.approx([-1.6651092223153954] * 4, abs=2e-15)
    assert sampler.bernoulli(lane=0, tick=17, field="PREPARE_BERNOULLI", probability=0.25) == 0
    assert sampler.bernoulli(lane=0, tick=17, field="COMMIT_BERNOULLI", probability=0.5) == 1
    fields = [(f,d) for f in study.MOTION_FIELDS for d in (0,1)] + [("PREPARE_BERNOULLI",0),("COMMIT_BERNOULLI",0)]
    expected = tuple("DISH/RBHR/R06/DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY/" + KEY
                     + f"/sample/0/tick/17/field/{f}/draw/{d}" for f,d in fields)
    assert calls == [(POLICY_MASTER, expected)]
    assert sampler.counts == dict(renewals=1, normal_draws=4, bernoulli_draws=2, uniform_draws=10)
    sampler.begin_tick(owner=1, tick=18, renew=False)
    assert len(calls) == 1 and sampler.words == {}
    other = study.EvaluationPolicySampler(master_digest=POLICY_MASTER, canonical_key=KEY, sample=1)
    other.begin_tick(owner=1, tick=19, renew=True)
    expected_swapped = tuple(a.replace("/sample/0/tick/17/", "/sample/1/tick/19/") for a in expected)
    assert calls[1][1] == expected_swapped[4:8] + expected_swapped[:4] + expected_swapped[8:]
    assert len(set(calls[0][1]) | set(calls[1][1])) == 20


class SyntheticModel:
    """Deterministic heads replacing model construction, not a scientific checkpoint."""
    def __init__(self):
        self.log_std = torch.tensor([-8.0, -0.5, 0.3, 3.0])
        self.motion = torch.arange(8, dtype=torch.float32).reshape(1,4,2) / 10
    def prepare_recurrent_hidden(self, hidden, *args):
        return hidden
    def advance_recurrent_hidden(self, normalized, hidden):
        return hidden + 0.1
    def heads(self, hidden):
        return {"motion": self.motion, "prepare": torch.zeros(1,4,1), "commit": torch.zeros(1,4,1),
                "prediction_mean": torch.zeros(1,4,4), "prediction_cholesky": torch.zeros(1,4,10),
                "service_q": torch.full((1,4,20), -2.0)}


def synthetic_policy(monkeypatch, sampled):
    monkeypatch.setattr(recurrent, "_load_policy", lambda checkpoint: SyntheticModel())
    stream = BytesIO()
    states = {name: WelfordState.empty(width) for name,width in (("actor",54),("snapshot",18),("critic",58))}
    for state in states.values():
        state.count = 3
        state.mean.fill_(0.25)
        state.m2.fill_(2.0)
    torch.save({"welford": states}, stream)
    state = recurrent.RecurrentRolloutState.fresh("STRUCTURED", width=1)
    # Distinct role-copy state makes the inherited promotion's state ownership observable.
    state.hidden[0,:,0] = torch.tensor([0.1,0.2,0.3,0.4])
    cls = study.SampledEvaluationPolicy if sampled else recurrent.BatchedRecurrentPolicy
    return cls(arm="STRUCTURED", checkpoint_bytes=stream.getvalue(), state=state, forecast_package=False)


def observation(owner, renew, terminal=False, cas=0, service=1):
    actor = np.zeros((1,4,54),dtype=np.float32)
    actor[0,:,8] = [0.1,0.2,0.3,0.4]
    actor[0,:,9] = [0.5,0.6,0.7,0.8]
    return {"actor":actor,"owner":np.array([owner]),"renew":np.array([renew]),
            "terminal":np.array([terminal]),"cas_applied":np.array([cas]),"service":np.array([service]),
            "snapshot_payload":np.zeros((1,4,18)),"snapshot_delivery_mask":np.zeros((1,4))}


class SyntheticNative:
    def __init__(self, transfer=True):
        self.transfer = transfer
        self.tick = 0
        self.owner = 0
        self.records = []
        self.state = np.zeros(1,dtype=np.dtype(study.b04.backend._State))
        self.state["battery"] = 100
        self.state["p"][0,2] = 100
        self.current = observation(0,True)
    def observe(self):
        return self.current
    def step(self, rows):
        self.records.append(rows.copy())
        self.tick += 1
        cas = int(self.transfer and self.tick == 2)
        self.owner = 1 if cas else self.owner
        self.current = observation(self.owner, self.tick != 1, terminal=self.tick == 3, cas=cas)
        self.state["tick"] = self.tick
        self.state["owner"] = self.state["actuator_owner"] = self.owner
        self.state["terminal"] = self.tick == 3
        self.state["total_energy"] = 10 * self.tick
        return self.current


def test_actual_policy_nonrenewal_role_remap_modal_promotion_and_fixed_welford(monkeypatch):
    calls = []
    def words(master, addresses):
        calls.append(addresses)
        return tuple(0x4000000000000000 if "/draw/0" in a else 0x8000000000000000 for a in addresses)
    monkeypatch.setattr(study.b04.backend, "rng_words_native", words)
    monkeypatch.setattr(study.b02, "native_state", lambda native: native.state)
    policy = synthetic_policy(monkeypatch, sampled=True)
    native = SyntheticNative()
    sampler = study.EvaluationPolicySampler(master_digest=POLICY_MASTER, canonical_key=KEY, sample=0)
    record = {}
    progress = study.b04.new_progress()
    study.b02.evaluate_episode(native,policy,math.inf,progress,record,sampler=sampler,
                               deterministic=False,record_first_transfer=True)
    assert len(calls) == 2 and all("/tick/1/" not in a for batch in calls for a in batch)
    assert "/tick/0/field/MOTION_OWNER_X/draw/0" in calls[0][0]
    assert "/tick/2/field/MOTION_STANDBY_X/draw/0" in calls[1][0]
    assert "/tick/2/field/MOTION_OWNER_X/draw/0" in calls[1][4]
    assert sampler.counts == dict(renewals=2, normal_draws=8, bernoulli_draws=4, uniform_draws=20)
    assert native.records[1]["raw_action"][0] == pytest.approx([0.1,0.5,0.4,0.8])
    assert not native.records[1]["prepare"].any() and not native.records[1]["commit"].any()
    means = (3*torch.tanh(policy.model.motion[0,[0,3]].reshape(4))).numpy()
    expected = means + np.exp(np.array([-5.0,-0.5,float(torch.tensor(0.3)),1.0])) * -1.6651092223153954
    assert native.records[0]["raw_action"][0] == pytest.approx(expected,abs=2e-7)
    assert np.all(native.records[0]["service_q"] == -2.0)  # raw service-Q, not sigmoid
    assert record["first_legal_transfer_tick"] == 2 and record["legal_transfers"] == 1
    assert record["completed_ticks"] == 3 and record["unstepped_zero_service_ticks"] == 1197
    assert record["complete"] and record["service_before_transfer"] == 1
    assert record["service_at_or_after_transfer"] == 2
    # STRUCTURED alpha=1 promotes new-owner shadow=.6 and copies old active=.3 to old shadow.
    # Third forward adds .1 to each, including the promoted active and old-owner shadow.
    assert policy.state.hidden[0,:,0].tolist() == pytest.approx([0.4,0.4,0.7,0.7])
    for state in (policy.state.actor_welford,policy.state.snapshot_welford,policy.state.critic_welford):
        assert state.count == 3 and torch.all(state.mean == 0.25) and torch.all(state.m2 == 2.0)
    modal = synthetic_policy(monkeypatch, sampled=False)
    modal_native = SyntheticNative()
    default_record = {}
    study.b02.evaluate_episode(modal_native,modal,math.inf,study.b04.new_progress(),default_record)
    assert len(calls) == 2  # unchanged default modal never calls the sampler
    assert "first_legal_transfer_tick" not in default_record
    assert modal_native.records[0]["raw_action"][0] == pytest.approx(means)
    assert modal_native.records[0]["prepare"][0,0] == modal_native.records[0]["commit"][0,0] == 1
    assert np.all(modal_native.records[0]["service_q"] == -2.0)
    for name,value in default_record.items():
        assert record[name] == value  # same synthetic consequences; added first-tick field only
    absent = {}
    study.evaluate_modal(SyntheticNative(transfer=False),synthetic_policy(monkeypatch,False),
                         math.inf,study.b04.new_progress(),absent)
    assert absent["first_legal_transfer_tick"] is None and absent["legal_transfers"] == 0


def test_complete_primary_averages_samples_then_conditions_and_preserves_bad_rows(tmp_path):
    keys = [c.canonical_key() for c in study.b04.coordinates()]
    reference = {"status":"COMPLETE", "reference_rows":[]}
    modal = {"status":"COMPLETE", "evaluation_rows":[]}
    sampled = {"status":"COMPLETE", "evaluation_rows":[]}
    for index,key in enumerate(keys):
        reference["reference_rows"].append(dict(coordinate=key,**episode_values(700)))
        modal["evaluation_rows"].append(dict(coordinate=key,**episode_values(500)))
        for j,value in enumerate((1200,0) if index != 1 else (100,200)):
            row = dict(coordinate=key,sample=j,**episode_values(value,energy=100+200*j,
                        completed=1200 if value else 7,transfer=2 if j==0 else None))
            row["hard_events"]["invalid_commit"] = 2+2*j
            sampled["evaluation_rows"].append(row)
    primary = study.paired_result(reference,modal,sampled)
    assert primary["reference_mean"] == 700 and primary["modal_mean"] == 500
    assert primary["sampled_mean"] == 487.5 and primary["delta_exec"] == -12.5
    assert primary["d_modal"] == -200 and primary["g_sampled_vs_init"] == -212.5
    assert primary["g_sampled_vs_init"] == primary["d_modal"]+primary["delta_exec"]
    assert [r["sampled_minus_modal"] for r in primary["rows"]] == [100,-350,100,100]
    assert primary["rows"][0]["sampled_native_mean"]["energy"] == 200
    assert primary["rows"][0]["sampled_native_mean"]["hard_events"]["invalid_commit"] == 3
    assert primary["rows"][0]["first_legal_transfer_ticks"]["final_sampled"] == [2,None]
    with pytest.raises(ValueError,match="eight sampled"):
        study.paired_result(reference,modal,{"status":"COMPLETE","evaluation_rows":sampled["evaluation_rows"][:-1]})
    sampled["evaluation_rows"][0]["complete"] = False
    with pytest.raises(ValueError,match="incomplete episode"):
        study.paired_result(reference,modal,sampled)
    from scripts.run_dish_sampled_execution_b06 import publish
    publish(tmp_path,{"status":"COMPLETE","primary":primary})
    assert json.loads((tmp_path/"paired.json").read_text()) == primary
    publish(tmp_path,{"status":"INCOMPLETE","exception":{"type":"FloatingPointError"},"loss":float("nan")})
    assert json.loads((tmp_path/"summary.json").read_text())["loss"] == "nan"
