"""Zero-science doubles protect completed evidence across an arrival failure."""

from copy import deepcopy
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_radio_uncertainty.b01 import collect


class FakeController:
    def __init__(self,history):
        assert history is False
        self._nav_index=0
        self.counters={"calls":0}

    def act(self,observation,tick):
        self.counters["calls"]+=1
        return np.zeros(3,np.float32),{"test_double":True}


class FakeManager:
    def __init__(self,*args,**kwargs):
        self.last_record=None

    def decide(self,*args,**kwargs):
        self.last_record={"counts":{},"wall_seconds":.001,"cpu_seconds":.001}
        return dict(commands=np.zeros((5,3),np.float32),mask=1,record=self.last_record)


class FakeEnv:
    sigma=4.14

    def __init__(self):
        self.env=self
        self.tick=0
        self.counts={"fake_step_calls":0}

    @property
    def physical_counters(self):
        return self.counts.copy()

    def obs(self):
        result=np.zeros((5,104),np.float32)
        result[:,:3]=(.5,.5,.5)
        result[:,-1]=self.tick/8
        return result

    def reset(self,seed):
        self.tick=0
        return self.obs(),{}

    def physical_snapshot(self):
        return deepcopy(dict(world=29641900,tick=self.tick,positions=np.tile((500.,500.,100.),(5,1)),
            users=np.zeros((50,2)),residual=np.zeros((5,50)),user_loss=np.full((5,50),80.),
            sinr=np.full((5,50),-np.inf),peer_sinr=np.full((5,5),-np.inf),connections=np.zeros((5,50),bool),
            transmitter_mask=np.ones(5,bool),counters=self.counts))

    def step(self,commands):
        self.tick+=1
        self.counts["fake_step_calls"]+=1
        return self.obs(),0.,False,False,{"rewards_dict":{"fake":0.}}

    def set_transmitter_mask(self,mask):
        raise RuntimeError("injected arrival failure")


def test_completed_postmove_state_survives_failed_arrival(monkeypatch):
    monkeypatch.setattr(collect,"LocalController",FakeController)
    monkeypatch.setattr(collect,"Scheduler",FakeManager)
    monkeypatch.setattr(collect,"service_metrics",lambda *args:dict(J=0.,served=0,quality=0.))
    raw,row,failure=collect.collect_episode(FakeEnv(),29641900,"P",horizon=8)
    assert isinstance(failure,RuntimeError) and str(failure)=="injected arrival failure"
    assert row["steps"]==int(raw["completed_steps"])==3
    assert np.isfinite(raw["positions"][3]).all() and np.isfinite(raw["loss"][3]).all()
    np.testing.assert_array_equal(raw["observations"][3],raw["postmove_observations"][2])
    assert raw["refresh_attempted"][3] and not raw["refresh_completed"][3]
    evidence=unpack_records(raw)
    assert evidence["failure_snapshot"]["tick"]==3
    assert evidence["failure_snapshot"]["counters"]["fake_step_calls"]==3
    assert str(raw["failure_type"])=="RuntimeError"


def test_paid_episode_and_renamed_file_survive_identity_failure(tmp_path,monkeypatch):
    from experiments.candidates.uav_radio_uncertainty.b01 import study,io

    class EmptyEnv:
        def __init__(self):
            self.env=self
            self.physical_counters={"test_double_only":1}

        def close(self):
            pass

    monkeypatch.setattr(study.torch,"set_num_threads",lambda *args:None)
    monkeypatch.setattr(study.torch,"set_num_interop_threads",lambda *args:None)
    monkeypatch.setattr(study,"make_env",lambda *args:EmptyEnv())
    monkeypatch.setattr(study,"constructor_witness",lambda *args:dict(test_double=np.array(True)))

    def episode(env,world,arm):
        # These integers are a synthetic ledger, not executed native/model work.
        return ({"test_double":np.array(True)},dict(world=world,arm=arm,steps=256,
            model_counts={"candidate_plans":7},controller_counts={"decisions":320},
            physical_counts={"fake":1},failure=None),None)

    monkeypatch.setattr(study,"collect_episode",episode)
    original_identity=io.identity

    def failed_identity(path):
        if Path(path).name.startswith("P_"):
            raise OSError("injected post-rename identity failure")
        return original_identity(path)

    monkeypatch.setattr(io,"identity",failed_identity)
    result=study.run_batch(tmp_path,"test_double_source",{},time.perf_counter())
    assert result["status"]=="INCOMPLETE_TECHNICAL_FAILURE"
    assert result["counts"]["native_steps"]==256 and result["counts"]["complete_episodes"]==1
    assert result["model_counts"]=={"candidate_plans":7}
    assert result["controller_counts"]=={"decisions":320}
    binding=result["rows"][0]["raw"]
    assert binding in result["artifacts"] and binding["write_status"]=="failed"
    assert binding["final_exists"] and not binding["partial_exists"] and binding["final_bytes"]>0
    assert Path(binding["path"]).is_file() and "final_identity_error" in binding
