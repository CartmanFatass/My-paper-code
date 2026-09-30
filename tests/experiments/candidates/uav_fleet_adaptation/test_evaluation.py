"""Endpoint behavior checks on synthetic/old worlds, never the declared fresh panel."""
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation import evaluation as ev
from experiments.candidates.uav_fleet_adaptation import reader
from experiments.candidates.uav_fleet_transmission import study as original
from experiments.candidates.uav_fleet_transmission.host import world as old_world


def old_fixture(monkeypatch):
    monkeypatch.setattr(ev, "make_env", lambda world_id, horizon: original.make_env(8, world_id, horizon))
    monkeypatch.setattr(ev, "runtime_seed", lambda world_id: original.runtime_seed(world_id,8))
    monkeypatch.setattr(reader, "runtime_seed", lambda world_id: original.runtime_seed(world_id,8))
    monkeypatch.setattr(reader, "world", old_world)


def test_ordinary_evaluation_matches_frozen_controller_and_reader(tmp_path, monkeypatch):
    old_fixture(monkeypatch)
    spec = ev.EvalSpec(world_ids=(29310000,), horizon=20)
    row = ev.evaluate_episode("C_E",29310000,None,tmp_path,spec)
    result, counts = reader.verify_evaluation(row,tmp_path,spec)
    assert result == row["metrics"]
    assert counts["mask"]["requested_candidates"] == 2*255
    assert counts["motion"]["requested_candidates"] == 20*8*27
    assert row["counts"] == {"actor_calls":0,"motion_calls":20,"mask_calls":2}
    row["runtime_seed"] += 1
    with pytest.raises(ValueError, match="runtime seed"):
        reader.verify_evaluation(row,tmp_path,spec)


class FakeActor:
    def __init__(self):
        self.inputs = []
        self.resets = []

    def reset_env_state(self, lane):
        self.resets.append(lane)

    def step(self, states, observations, steps, dones, **kwargs):
        assert kwargs == {"deterministic":True,"return_step_data":True,"build_infos":False}
        self.inputs.append((states.copy(),observations.copy(),steps.copy(),dones.copy()))
        return np.full((1,8,3),2.,np.float32), None, {"action_logprobs":np.zeros((1,8,1),np.float32)}


def test_actor_steps_once_on_previous_mask_feedback_before_boundary_E(tmp_path, monkeypatch):
    old_fixture(monkeypatch)
    monkeypatch.setattr(ev.frozen,"runtime_state_digest",lambda agent: str(len(agent.inputs)))
    agent = FakeActor()
    spec = ev.EvalSpec(world_ids=(29310000,),horizon=20)
    row = ev.evaluate_episode("F_E",29310000,agent,tmp_path,spec)
    assert agent.resets == [0] and len(agent.inputs) == 20
    with np.load(tmp_path / row["raw"]["path"]) as raw:
        for t,(state,obs,steps,dones) in enumerate(agent.inputs):
            np.testing.assert_array_equal(state[0],raw["states"][t])
            np.testing.assert_array_equal(obs[0],raw["observations"][t])
            assert steps.item() == t and not dones.item()
        np.testing.assert_array_equal(raw["raw_actions"],2.)
        np.testing.assert_array_equal(raw["actions"],1.)
    reader.verify_evaluation(row,tmp_path,spec)


def test_parent_endpoint_matches_original_full_policy_path(tmp_path, monkeypatch):
    """Exact supplied final45 bytes; bounded old-world correctness, not a fresh study endpoint."""
    from experiments.candidates.uav_fleet_adaptation.training import load_parent, build_warmstart
    checkpoint_root = Path(__file__).resolve().parents[4] / "temp/directions/uav_fleet_adaptation/inputs"
    checkpoint = checkpoint_root / "s1_action_law_b03_h6_clip_s942201/checkpoint_45.pt"
    if not checkpoint.exists():
        pytest.skip("exact retained parent checkpoint not staged")
    old_fixture(monkeypatch)
    record = load_parent(checkpoint_root)
    torch.set_num_threads(1)
    agent,_,initial = build_warmstart(record,tmp_path / "new_logs")
    agent.train(False)
    old_env = original.make_env(8,29310000,500)
    agents,bindings,hooks = original.load_agents({"H6":record},8,old_env,tmp_path / "old_logs")
    # The warm-start explicitly resets all16 slots. Match unused slot bookkeeping
    # before comparing the digest, which includes every slot rather than only lane0.
    for lane in range(16):
        agents["H6"].reset_env_state(lane)
    try:
        row = ev.evaluate_episode("I_E",29310000,agent,tmp_path / "new",ev.EvalSpec(horizon=22))
        old = original.evaluate_episode("H6_E",8,29310000,original.Spec(horizon=22),agents["H6"],tmp_path / "old")
        with np.load(tmp_path / "new" / row["raw"]["path"]) as lhs, np.load(tmp_path / "old" / old["raw"]["path"]) as rhs:
            assert set(lhs.files) == set(rhs.files)
            for key in lhs.files:
                np.testing.assert_array_equal(lhs[key],rhs[key],err_msg=key)
        original.check_agents(agents,bindings)
        assert original.frozen.digest_agent(agent) == record["summary"]["final_parameter_normalizer_digest"]
    finally:
        for handle in hooks:
            handle.remove()
        for model in (agent,agents["H6"]):
            if getattr(model,"writer",None):
                model.writer.close()
        old_env.close()
