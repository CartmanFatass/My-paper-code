"""Synthetic storage/control/reader checks; zero real native or radio queries."""
from copy import deepcopy
from types import SimpleNamespace
import json

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import controller as c
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import cycle, fit, learning, reader, run, study
from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, empty_counts
from experiments.candidates.uav_fleet_transmission.b03.option import branch_id
from test_learning import STAY, artifact, candidate, report, synthetic_rows


def test_scalar_features_and_solution_auditor(monkeypatch):
    candidates = [candidate(), candidate(member=2, predicted_mask=0)]
    np.testing.assert_allclose(fit.scalar_features(report(), 1, candidates, STAY),
                               learning.feature_matrix(report(), 1, candidates, STAY), rtol=1e-13, atol=1e-13)
    data = synthetic_rows()
    data["manifest"]["references"] = []
    fitted = learning.fit_rows(data)
    result = fit.audit_solution(data, fitted)
    assert result["rank"] == 13 and result["maximum_normal_equation_residual"] < 1e-12
    with monkeypatch.context() as m:
        m.setattr(np.linalg,"lstsq",lambda *a,**k: pytest.fail("evaluation may not solve again"))
        m.setattr(np.linalg,"solve",lambda *a,**k: pytest.fail("evaluation may not refit"))
        assert fit.audit_solution(data,fitted,resolve=False)["verification_lstsq_solves"] == 0
    for field in ("beta", "means", "weights"):
        corrupted = deepcopy(fitted)
        corrupted[field][0] += .01
        with pytest.raises(ValueError):
            fit.audit_solution(data, corrupted)
    corrupted = deepcopy(fitted)
    corrupted["diagnostics"]["weighted_mse"] += .01
    with pytest.raises(ValueError):
        fit.audit_solution(data, corrupted)


def test_recurring_and_nonrecurring_certificate_and_corruption(monkeypatch):
    from test_cycle import _history, _synthetic
    for drift in (False, True):
        with monkeypatch.context() as m:
            _synthetic(m, drift=drift)
            history, state = _history()
            # The mock scorer counts eight unique geometry rows. Supply exactly
            # that geometry so the independent reader can reconstruct counts.
            state[:24].reshape(8,3)[:,0] = np.linspace(.1,.8,8,dtype=np.float32)
            history.positions, history.users = cycle.decode_public_state(state,8)
            result = cycle.simulate_continuation(history,state,1,horizon=200)
            audit = reader.verify_reuse(result["reuse"],result,history.commands,None)
            assert audit["reused_ticks"] == (0 if drift else 119)
            bad = deepcopy(result["reuse"])
            bad["computed_ticks"] += 1
            with pytest.raises(ValueError):
                reader.verify_reuse(bad,result,history.commands,None)
            if not drift:
                bad = deepcopy(result["reuse"])
                bad["first_repeat"]["key_sha256"] = "0"*64
                with pytest.raises(ValueError):
                    reader.verify_reuse(bad,result,history.commands,None)


def _bank():
    counts = dict(requested_candidates=0, scored_candidates=0, cached_candidates=0,
                  geometry_rows_computed=0, geometry_rows_reused=0, model_ticks=0)
    plans = []
    for i,value in enumerate((930.,960.,945.)):
        selected = candidate(member=i+1,site=i,predicted_total_J=value)
        plans.append(dict(initiated=True,selected=selected,stay_score=STAY.copy(),
            member=i+1,site=i,duration=20,arrival_t=60,commands=np.zeros((20,8,3)).tolist(),
            predicted_destination=selected["predicted_destination"],predicted_mask=3,
            stay_total_J=920.,predicted_total_J=value,stay_total_served=9200,
            predicted_total_served=9300,counts=counts.copy(),candidate_count=300,candidate_digest="synthetic"))
    return dict(champions=plans,original_R=deepcopy(plans[1]),candidate_rows=np.zeros((300,12)))


@pytest.mark.parametrize("arm, expected", [("R", "m2_s1"), ("T_E", "m1_s0"), ("K2_E", "m3_s2"), ("L", "m2_s1")])
def test_t40_control_branch_subset_and_zero_fallback(monkeypatch, arm, expected):
    bank = _bank()
    queried = []
    def simulator(controller,state,old_mask,plan,horizon):
        identifier = branch_id(plan)
        queried.append(identifier)
        values = {"stay":0.,"m1_s0":3.,"m2_s1":1.,"m3_s2":2.}
        return {"arrays":{},"decisions":[],"summary":dict(total_J=values[identifier],total_served=0,total_path=0)}
    monkeypatch.setattr(c,"enumerate_champions",lambda *a: deepcopy(bank))
    monkeypatch.setattr(c,"simulate_reference",simulator)
    policy = c.AmortizedProgram(arm,artifact() if arm == "L" else None,reference=True)
    policy._decide(report(),1)
    assert policy.selection["selected_branch"] == expected
    assert queried == ({"T_E":["stay","m1_s0","m2_s1","m3_s2"],
                        "K2_E":["stay","m2_s1","m3_s2"]}.get(arm,[]))
    pending = policy.take_artifacts()
    assert pending["candidate_rows"].shape == (300,12) and policy.take_artifacts() is None
    assert policy.selection_timing["cpu_seconds"] >= 0


def test_read_run_rejects_incomplete_worker_before_replay(tmp_path,monkeypatch):
    (tmp_path/"summary.json").write_text(json.dumps({"worker_status":"incomplete"}))
    monkeypatch.setattr(reader,"verify_episode",lambda *a: pytest.fail("incomplete worker must not replay"))
    with pytest.raises(ValueError):
        reader.read_run(tmp_path)


def test_entry_requires_admission_before_result_effects(tmp_path,monkeypatch):
    import scripts.hmasd_admission as admission
    out = tmp_path/"b06_paid_ranker_fit_a01"
    def refuse(*a,**k):
        raise RuntimeError("synthetic admission refusal")
    monkeypatch.setattr(admission,"require_admission",refuse)
    monkeypatch.setattr(run.sys,"argv",["run.py","--phase","fit","--out",str(out),"--launch-sha","0"*40,"--seed","29366991"])
    with pytest.raises(RuntimeError,match="admission refusal"):
        run.main()
    assert not out.exists()


def test_synthetic_collector_to_reader_and_corrupted_trace(tmp_path,monkeypatch):
    users = np.zeros((50,2),dtype=np.float64)
    positions = np.asarray([[100.+i*20,200.,100.] for i in range(8)])
    scene = SimpleNamespace(world_id=-1,user_positions=users,uav_positions=positions)
    sinr = np.full((8,50),-np.inf)
    sinr[0,:10] = 3.
    connections = sinr >= 0
    peer = np.zeros((8,8))
    obs = np.zeros((8,104),dtype=np.float32)
    components = dict(zip(study.COMPONENTS,[.2,.1,.05,.12]))

    def native():
        return SimpleNamespace(uav_positions=positions.copy(),sinr_matrix=sinr.copy(),connections=connections.copy(),
            uav_sinr_matrix=peer.copy(),_local_user_entries=lambda i: (list(range(10)) if i==0 else [],None),
            _local_uav_entries=lambda i: ([],None),set_transmitter_mask=lambda mask: None)

    class Environment:
        def __init__(self):
            self.env = SimpleNamespace(env=native())
            self.t = 0
        def reset(self,seed):
            return obs.copy(),{"state":reader._public_state(positions,users,0,500)}
        def step(self,actions):
            self.t += 1
            return obs.copy(),components["total_reward"]/8,self.t==500,False,{
                "next_state":reader._public_state(positions,users,self.t,500),
                "reward_components":{"reward_info":components.copy()}}
        def close(self):
            pass

    class Policy:
        def __init__(self,arm,fitted=None,reference=False):
            self.plan = {"initiated":False,"stay_total_J":55.2,"predicted_total_J":55.2,"selected":None}
            self.selection = {"arm":arm,"branches":[]}
            self.selection_timing = {"cpu_seconds":0.,"wall_seconds":0.}
            self.pending = None
        def select(self,t,state,old_mask):
            assert (state is not None) == (t%10==0)
            if t==40:
                self.pending = {"candidate_rows":np.zeros((0,12)),"branches":[]}
            return np.zeros((8,3),dtype=np.float32),old_mask,{"t":t,"old_mask":old_mask,"issued_mask":old_mask,"phase":"ordinary"}
        def take_artifacts(self):
            result,self.pending = self.pending,None
            return result

    monkeypatch.setattr(study,"make_env",lambda *a: Environment())
    monkeypatch.setattr(study,"AmortizedProgram",Policy)
    monkeypatch.setattr(reader,"AmortizedProgram",Policy)
    monkeypatch.setattr(reader,"_native_view",lambda *a: native())
    monkeypatch.setattr(reader.uav_radio,"free_space_user_path_loss",lambda *a: None)
    monkeypatch.setattr(reader.uav_radio,"user_sinr_from_path_loss",lambda *a,**k: sinr.copy())
    monkeypatch.setattr(reader.uav_radio,"greedy_connection_assignment",lambda *a: connections.copy())
    monkeypatch.setattr(reader.MultiUAVEnv,"_compute_uav_path_loss_matrix",lambda *a: None)
    monkeypatch.setattr(reader.MultiUAVEnv,"_compute_uav_uav_sinr_matrix",lambda *a: peer.copy())
    monkeypatch.setattr(reader.MultiUAVEnv,"_get_observation_vectorized",lambda *a: {"obs":obs[0].copy()})
    monkeypatch.setattr(reader.UAVBaseStationEnv,"_compute_reward",lambda view: setattr(view,"reward_info",components.copy()))
    row = study.evaluate_episode("R",scene,123,tmp_path,None)
    audit = reader.verify_episode(row,tmp_path,scene,None)
    assert row["steps"] == 500 and row["metrics"]["served"] == 10
    assert audit["counts"] == empty_counts() and not audit["reuse"]
    bad = deepcopy(row)
    bad["metrics"]["J"] += 1
    with pytest.raises(ValueError,match="native reduction"):
        reader.verify_episode(bad,tmp_path,scene,None)
    trace = tmp_path/row["decisions"]["path"]
    trace.write_bytes(b"corrupted")
    with pytest.raises(ValueError,match="saved artifact bytes"):
        reader.verify_episode(row,tmp_path,scene,None)
