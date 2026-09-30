"""Integration and saved-data checks on old/synthetic correctness fixtures only."""
import copy
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.load_critical_member_generalization.load_probe import probe as frozen
from experiments.candidates.load_critical_member_generalization.load_probe.scenes import matched_world, MatchedWorldS1
from experiments.candidates.uav_fleet_transmission import host, study, reader, run_b01


@pytest.fixture
def old_fixture(monkeypatch):
    fixture = matched_world(0)
    monkeypatch.setattr(host, "world", lambda _: fixture)
    monkeypatch.setattr(reader, "world", lambda _: fixture)
    monkeypatch.setattr(study, "runtime_seed", lambda w,n: 1234+n)
    return fixture


class Actor:
    def __init__(self):
        self.calls = []

    def reset_env_state(self, lane):
        self.calls.clear()

    def step(self, states, observations, steps, dones, **kwargs):
        self.calls.append((int(steps[0]),states.copy(),observations.copy()))
        n = observations.shape[1]
        # Nontrivial clipping and changing every tick, including off E boundaries.
        actions = np.full((1,n,3), .13+int(steps[0])*.007, dtype=np.float32)
        actions[:,:,0] = 1.25
        return actions, None, {"action_logprobs":np.zeros((1,n,1),np.float32)}


@pytest.mark.parametrize("arm,n", [("H6_all",4),("H6_E",8),("C_E",4)])
def test_complete_episode_and_pure_reader(old_fixture, tmp_path, monkeypatch, arm, n):
    spec = study.Spec(world_ids=(0,), ns=(n,), horizon=20)
    actor = None if arm == "C_E" else Actor()
    # Mock only actor-runtime fingerprint, not dynamics, masking or reading.
    monkeypatch.setattr(frozen, "runtime_state_digest", lambda agent: str(len(agent.calls)))
    row = study.evaluate_episode(arm,n,0,spec,actor,tmp_path)
    derived, counts = reader.verify_episode(row,tmp_path,spec)
    assert derived == row["metrics"]
    assert counts["mask"]["requested_candidates"] == (2*((1<<n)-1) if arm.endswith("_E") else 0)
    assert counts["motion"]["requested_candidates"] == (20*n*27 if arm == "C_E" else 0)
    if actor:
        assert [x[0] for x in actor.calls] == list(range(20))
        with np.load(tmp_path/row["raw"]["path"]) as raw:
            for t, state, observation in actor.calls:
                np.testing.assert_array_equal(state[0],raw["states"][t])
                np.testing.assert_array_equal(observation[0],raw["observations"][t])
            assert not np.array_equal(raw["actions"][1], raw["actions"][2])
            assert np.all(raw["actions"][:,:,0] == 1.)


def test_reader_rejects_changed_choice_and_artifact(old_fixture,tmp_path,monkeypatch):
    monkeypatch.setattr(frozen,"runtime_state_digest",lambda agent: "test")
    spec = study.Spec(world_ids=(0,),ns=(4,),horizon=20)
    row = study.evaluate_episode("H6_E",4,0,spec,Actor(),tmp_path)
    wrong = copy.deepcopy(row)
    wrong["raw"]["sha256"] = "0"*64
    with pytest.raises(ValueError,match="artifact identity"):
        reader.verify_episode(wrong,tmp_path,spec)
    path = tmp_path/row["decisions"]["path"]
    with gzip.open(path,"rt") as stream:
        data = [json.loads(line) for line in stream]
    data[10]["old_mask"] = 0
    with gzip.open(path,"wt") as stream:
        for item in data:
            stream.write(json.dumps(item)+"\n")
    row["decisions"] = study.artifact(path,tmp_path)
    with pytest.raises(ValueError,match="old-mask decision order"):
        reader.verify_episode(row,tmp_path,spec)


def test_entry_admission_precedes_scientific_imports_and_output(tmp_path,monkeypatch):
    import scripts.hmasd_admission as admission
    def reject(*args,**kwargs):
        raise RuntimeError("test admission refusal")
    monkeypatch.setattr(admission,"require_admission",reject)
    target = tmp_path/"not_created"
    with pytest.raises(RuntimeError,match="admission refusal"):
        run_b01.main(["--out",str(target),"--checkpoint-root",str(tmp_path),"--launch-sha","x"])
    assert not target.exists()


def _completed_worker_evidence():
    value = {"status":"collected", "worker_status":"complete", "schema":1,
             "direction":study.DIRECTION,"object_id":study.OBJECT_ID,
             "new_fits":0,"updates":0,"launch_sha":"a"*40,
             "config":{"launch_sha":"a"*40,"source_training_sha":frozen.PRODUCER_SHA,
                "object_id":study.OBJECT_ID,"direction":study.DIRECTION,"arms":study.ARMS,
                "expected_episodes":160,"expected_native_steps":80000,
                "expected_mask_requests":648000,"expected_motion_requests":2592000},
             "assets":{},"frozen_checks":{"4":{},"8":{}}}
    for arm,seed,tag in frozen.SOURCE_POLICIES:
        digest = {"H6":"98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343",
                  "SET":"03f4f070e30b34fb61cd45820f1579ebde185c9417468689bd0c2e7ef60c0a3b"}[arm]
        value["assets"][arm] = {"source":{"arm":arm,"seed":seed,"tag":tag},
            "checkpoint_sha256_before":digest,"checkpoint_sha256_after":digest,
            "checkpoint_record":{"sha256":digest},"source_final_digest":"f"*64}
        for n in ("4","8"):
            value["frozen_checks"][n][arm] = {"initial_digest":"f"*64,"final_digest":"f"*64,
                "normalizers_unchanged":True,"optimizer_calls":{"actor":0}}
    return value


def test_reader_never_certifies_full_panel_after_worker_freeze_failure():
    value = _completed_worker_evidence()
    reader.validate_worker(value)
    # Only reader failure can be repaired over a fully validated worker panel.
    value.update(status="failed",failure_stage="reader")
    reader.validate_worker(value)
    for mutation in ("postcollection_failure","parameter","normalizer","optimizer","checkpoint"):
        bad = copy.deepcopy(value)
        if mutation == "postcollection_failure":
            bad.update(status="failed",failure_stage="running")
            bad.pop("worker_status")
        elif mutation == "parameter":
            bad["frozen_checks"]["8"]["SET"]["final_digest"] = "0"*64
        elif mutation == "normalizer":
            bad["frozen_checks"]["8"]["SET"]["normalizers_unchanged"] = False
        elif mutation == "optimizer":
            bad["frozen_checks"]["8"]["SET"]["optimizer_calls"]["actor"] = 1
        else:
            bad["assets"]["H6"]["checkpoint_sha256_after"] = "0"*64
        with pytest.raises(ValueError):
            reader.validate_worker(bad)


@pytest.mark.parametrize("n,arm",[(4,"H6"),(8,"H6"),(4,"SET"),(8,"SET")])
def test_final45_all_on_actor_equivalence(old_fixture,tmp_path,n,arm):
    """External frozen inputs are optional to unit CI, required before this study launches."""
    external = os.environ.get("HMASD_FLEET_CHECKPOINT_ROOT")
    if not external:
        pytest.skip("requires declared final45 checkpoint inputs")
    source = next(frozen.SourcePolicy(*p) for p in frozen.SOURCE_POLICIES if p[0] == arm)
    record = frozen.load_source_policy(Path(external),source)
    old = CountAdapter(ParallelToArrayAdapter(MatchedWorldS1(n_uavs=n,capacity=10,world_id=0,horizon=500)))
    new = CountAdapter(ParallelToArrayAdapter(host.FleetS1(n,0,horizon=500)))
    torch.set_num_threads(4)
    old_agents, old_binding, old_hooks = study.load_agents({arm:record},n,old,tmp_path/"old")
    new_agents, new_binding, new_hooks = study.load_agents({arm:record},n,new,tmp_path/"new")
    try:
        for reset in range(2):
            old_agent,new_agent = old_agents[arm],new_agents[arm]
            old_agent.reset_env_state(0)
            new_agent.reset_env_state(0)
            old_obs,old_info = old.reset(seed=734)
            new_obs,new_info = new.reset(seed=734)
            states = [old_info["state"],new_info["state"]]
            observations = [old_obs,new_obs]
            for t in range(22):
                np.testing.assert_array_equal(states[0],states[1])
                np.testing.assert_array_equal(observations[0],observations[1])
                results = []
                with torch.no_grad():
                    for agent,state,obs in zip((old_agent,new_agent),states,observations):
                        frozen.seed_rng(90000+t)
                        results.append(agent.step(state[None],obs[None],np.asarray([t]),np.asarray([False]),
                            deterministic=True,return_step_data=True,build_infos=False))
                np.testing.assert_array_equal(results[0][0],results[1][0])
                assert frozen.runtime_state_digest(old_agent) == frozen.runtime_state_digest(new_agent)
                transitions = [env.step(np.clip(result[0][0],-1,1)) for env,result in zip((old,new),results)]
                assert transitions[0][1] == transitions[1][1]
                states = [x[4]["next_state"] for x in transitions]
                observations = [x[0] for x in transitions]
            np.testing.assert_array_equal(states[0],states[1])
        study.check_agents(old_agents,old_binding)
        study.check_agents(new_agents,new_binding)
    finally:
        for handle in old_hooks+new_hooks:
            handle.remove()
        for agent in list(old_agents.values())+list(new_agents.values()):
            if getattr(agent,"writer",None):
                agent.writer.close()
        old.close()
        new.close()
