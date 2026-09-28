"""B05 collector: coordinate-contract consumers (c, e), identity parity, routing and c00 (d)."""

from __future__ import annotations

import copy
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b02 import training as b02_tr
from experiments.candidates.energy_relay_benchmark.b05 import training as tr
from experiments.candidates.uav_geometric_generalization.b01.symmetry import (
    D4, inverse_actions, transform_observations, transform_state,
)
from experiments.candidates.uav_service_auxiliary.b01.native import (
    make_env, optimizer_steps,
)

REPO = Path(__file__).resolve().parents[5]
C00 = REPO / "runs/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c00"
C00_FINGERPRINT = "58a6a8a13217c8126a4eca73d02cbfa610433005a21e8e68756559318c9bf333"
MODULES = ("skill_coordinator", "skill_discoverer", "team_discriminator",
           "individual_discriminator")
# Seed with non-identity frames in both lanes (lane 0 MIRROR_X, lane 1 ROT180 at the first reset).
TINY_SEED = 317763


def _tiny(canonical="sw", **changes):
    spec = tr.B05Spec(seed=TINY_SEED, rollouts=2, rollout_length=25, episode_length=40,
                      hidden_size=32, gru_hidden_size=32, ppo_epochs=1,
                      checkpoint_every_transitions=50, canonical=canonical)
    spec = replace(spec, **changes)
    config = cfg.make_b02_config(spec)
    config.initial_battery_ratio_range = (0.03, 0.03)   # forces shield entries
    return spec, config


def _canon(obs, state, frame):
    if frame == D4.IDENTITY:
        return obs, state
    return transform_observations(obs, frame), transform_state(state, frame)


def _assert_same_modules(left, right):
    for name in MODULES:
        a, b = getattr(left, name), getattr(right, name)
        assert (a is None) == (b is None), name
        if a is None:
            continue
        sa, sb = a.state_dict(), b.state_dict()
        assert sa.keys() == sb.keys()
        for key in sa:
            torch.testing.assert_close(sa[key], sb[key], rtol=0, atol=0)


class RecordingEnv:
    """Physical env outputs as the collector receives them; the test's own frame bookkeeping."""

    def __init__(self, env):
        self.env = env
        self.obs = self.state = None
        self.frame = None
        self.actions = []
        self.frames = []
        self.last_step_obs = self.last_step_state = None

    def reset(self, *args, **kwargs):
        obs, info = self.env.reset(*args, **kwargs)
        self.obs = np.asarray(obs, dtype=np.float32)
        self.state = np.asarray(info["state"], dtype=np.float32)
        mean = self.obs[:, :2].mean(axis=0)   # independent SW rule
        self.frame = {(True, True): D4.IDENTITY, (True, False): D4.MIRROR_Y,
                      (False, True): D4.MIRROR_X, (False, False): D4.ROT180}[
            (bool(mean[0] < .5), bool(mean[1] < .5))]
        self.frames.append(self.frame)
        return obs, info

    def step(self, action):
        self.actions.append(np.array(action, copy=True))
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.obs = np.asarray(obs, dtype=np.float32)
        self.state = np.asarray(info["next_state"], dtype=np.float32)
        self.last_step_obs, self.last_step_state = self.obs, self.state
        return obs, reward, terminated, truncated, info

    def close(self):
        self.env.close()


def test_coordinate_contract_consumers(tmp_path, monkeypatch):
    """(c) frame persistence across the k = 10 held snapshot, a lane reset and a live rollout
    boundary in both lanes; (e) the shield and env.step receive physical actions/observations;
    every agent-side consumer (step inputs, held snapshot, stored next inputs, buffer rows,
    bootstrap, update's last inputs) receives the canonical copy."""
    torch.set_num_threads(1)
    spec, config = _tiny()
    agent, _ = tr.b02_training.new_agent(config, device=torch.device("cpu"),
                                         log_dir=tmp_path / "logs", seed=spec.seed)
    envs: list[RecordingEnv] = []

    def env_factory(config, seed):
        envs.append(RecordingEnv(make_env(config, seed)))
        return envs[-1]

    feedback_calls, bootstrap_calls, update_calls, stores = [], [], [], []
    real_feedback, real_bootstrap = tr.apply_feedback, tr._bootstrap_values

    def feedback_spy(obs, proposal, modes, **kwargs):
        decision = real_feedback(obs, proposal, modes, **kwargs)
        feedback_calls.append((np.array(obs, copy=True), np.array(proposal, copy=True),
                               np.array(decision.submitted_actions, copy=True)))
        return decision

    def bootstrap_spy(agent, states, dones):
        bootstrap_calls.append(np.array(states, copy=True))
        return real_bootstrap(agent, states, dones)

    monkeypatch.setattr(tr, "make_env", env_factory)
    monkeypatch.setattr(tr, "apply_feedback", feedback_spy)
    monkeypatch.setattr(tr, "_bootstrap_values", bootstrap_spy)
    fed, expected_inputs, frames_now, returned, physical_now = [], [], [], [], []
    original_step, original_store, original_update = (agent.step, agent.store_transition_batch,
                                                      agent.update)

    def step(states, obs, *args, **kwargs):
        fed.append((np.array(states, copy=True), np.array(obs, copy=True)))
        frames_now.append([env.frame for env in envs])
        physical_now.append([env.obs.copy() for env in envs])
        expected_inputs.append([_canon(env.obs, env.state, env.frame) for env in envs])
        result = original_step(states, obs, *args, **kwargs)
        returned.append(np.array(result[0], dtype=np.float32, copy=True))
        return result

    def store(states, next_states, obs, next_obs, actions, rewards, dones, **kwargs):
        stores.append({"next_states": np.array(next_states, copy=True),
                       "next_obs": np.array(next_obs, copy=True), "dones": np.array(dones),
                       "frames": [env.frame for env in envs],
                       "expected": [_canon(env.last_step_obs, env.last_step_state, env.frame)
                                    for env in envs]})
        return original_store(states, next_states, obs, next_obs, actions, rewards, dones, **kwargs)

    def update(**kwargs):
        data = agent.rollout_buffer._get_full_rollout_data()
        update_calls.append({"last_state": np.array(kwargs["last_state"], copy=True),
                             "last_observations": np.array(kwargs["last_observations"], copy=True),
                             "expected": [_canon(env.obs, env.state, env.frame) for env in envs],
                             "obs": data["obs"].copy(), "states": data["states"].copy(),
                             "snapshot_obs": data["central_snapshot_obs"].copy(),
                             "snapshot_states": data["central_snapshot_states"].copy()})
        return original_update(**kwargs)

    agent.step, agent.store_transition_batch, agent.update = step, store, update
    snapshots = []

    def observe(agent, step_data, index):
        snapshots.append((agent._central_snapshot_obs[:spec.lanes].copy(),
                          agent._central_snapshot_states[:spec.lanes].copy(),
                          np.asarray([agent.env_timers.get(lane) for lane in range(spec.lanes)])))

    started = time.perf_counter()
    result = tr.collect_and_train_canonical(agent, agent.config, spec, feedback=True,
                                            observe_step=observe)
    wall = time.perf_counter() - started
    print(f"short collection (2 lanes x 2 rollouts x 25 steps, update included): {wall:.2f} s")
    n = spec.rollouts * spec.rollout_length
    assert len(fed) == len(snapshots) == len(returned) == len(stores) == n
    # Both lanes non-identity at the start, a lane reset at step 40, a live boundary at step 25.
    assert frames_now[0] == [D4.MIRROR_X, D4.ROT180]
    assert [len(env.frames) for env in envs] == [2, 2]
    assert result["rollouts"][0]["live_lanes_at_boundary"] == 2
    assert any(env.frames[0] != env.frames[1] for env in envs)
    # Frames persist across the live rollout boundary (interactions 24 -> 25, same episodes).
    assert frames_now[24] == frames_now[25] == frames_now[0]
    chosen = [c for r in result["rollouts"] for c in r["frames_chosen"]]
    assert [(c["lane"], c["episode"], c["frame"]) for c in chosen] == \
        [(lane, index, env.frames[index].name) for index in range(2)
         for lane, env in enumerate(envs)]
    assert [row["frame"] for row in result["rollouts"][1]["episodes_completed"]] == \
        [envs[0].frames[0].name, envs[1].frames[0].name]
    refresh = [None, None]
    for i in range(n):
        states_in, obs_in = fed[i]
        for lane in range(spec.lanes):
            # Current own and joint observation and the state: canonical, the episode's frame.
            exp_obs, exp_state = expected_inputs[i][lane]
            assert obs_in[lane].tobytes() == np.asarray(exp_obs, np.float32).tobytes(), (i, lane)
            assert states_in[lane].tobytes() == np.asarray(exp_state, np.float32).tobytes(), (i, lane)
            # Held snapshot (refreshed at timer 0 from what the agent was fed; held for k = 10).
            snap_obs, snap_states, timers = snapshots[i]
            if timers[lane] == 0:
                refresh[lane] = (obs_in[lane].copy(), states_in[lane].copy(), frames_now[i][lane])
            assert refresh[lane][2] == frames_now[i][lane], "snapshot from another frame"
            np.testing.assert_array_equal(snap_obs[lane], refresh[lane][0])
            np.testing.assert_array_equal(snap_states[lane], refresh[lane][1].astype(np.float64))
            # (e) the shield: physical observation, inverse-transformed proposal.
            obs_arg, proposal_arg, submitted = feedback_calls[i * spec.lanes + lane]
            env = envs[lane]
            physical_proposal = (returned[i][lane] if frames_now[i][lane] == D4.IDENTITY
                                 else inverse_actions(returned[i][lane], frames_now[i][lane]))
            assert proposal_arg.tobytes() == physical_proposal.tobytes()
            assert obs_arg.tobytes() == physical_now[i][lane].tobytes()
            if frames_now[i][lane] != D4.IDENTITY:
                assert not np.array_equal(proposal_arg[:, :2], returned[i][lane][:, :2])
            # env.step got the shield's physical output.
            assert env.actions[i].tobytes() == submitted.tobytes()
            # Stored next observation/state: canonical in the frame of the episode that produced it
            # (a terminal transition keeps the ending episode's frame; the reset comes after).
            exp_next_obs, exp_next_state = stores[i]["expected"][lane]
            assert stores[i]["frames"][lane] == frames_now[i][lane]
            assert stores[i]["next_obs"][lane].tobytes() == np.asarray(exp_next_obs, np.float32).tobytes()
            assert stores[i]["next_states"][lane].tobytes() == \
                np.asarray(exp_next_state, np.float32).tobytes()
    # At least one terminal transition was followed by a reset into a different frame.
    switched = [(i, lane) for i in range(n - 1) for lane in range(spec.lanes)
                if stores[i]["dones"][lane] and frames_now[i + 1][lane] != frames_now[i][lane]]
    assert switched
    assert len(feedback_calls) == n * spec.lanes
    assert sum(r["f_mapped_commands"] for r in result["rollouts"]) > 0
    # Buffer rows, snapshot rows, bootstrap and update inputs: canonical.
    assert len(update_calls) == len(bootstrap_calls) == spec.rollouts
    for r, call in enumerate(update_calls):
        for t in range(spec.rollout_length):
            i = r * spec.rollout_length + t
            np.testing.assert_array_equal(call["obs"][t], fed[i][1])
            np.testing.assert_array_equal(call["states"][t], fed[i][0])
            np.testing.assert_array_equal(call["snapshot_obs"][t], snapshots[i][0])
            np.testing.assert_array_equal(call["snapshot_states"][t], snapshots[i][1])
        for lane in range(spec.lanes):
            exp_obs, exp_state = call["expected"][lane]
            assert call["last_observations"][lane].tobytes() == np.asarray(exp_obs, np.float32).tobytes()
            assert call["last_state"][lane].tobytes() == np.asarray(exp_state, np.float32).tobytes()
        np.testing.assert_array_equal(bootstrap_calls[r], call["last_state"])


def test_shield_receives_the_physical_observation(tmp_path, monkeypatch):
    """(e) spy on apply_feedback: its observation argument is bitwise the env's physical output."""
    torch.set_num_threads(1)
    spec, config = _tiny(rollouts=1, rollout_length=12, episode_length=12,
                         checkpoint_every_transitions=24)
    agent, _ = tr.b02_training.new_agent(config, device=torch.device("cpu"),
                                         log_dir=tmp_path / "logs", seed=spec.seed)
    envs, calls = [], []

    def env_factory(config, seed):
        envs.append(RecordingEnv(make_env(config, seed)))
        return envs[-1]

    real = tr.apply_feedback

    def spy(obs, proposal, modes, **kwargs):
        lane = len(calls) % 2
        calls.append((np.array(obs, copy=True), envs[lane].obs.copy(), envs[lane].frame))
        return real(obs, proposal, modes, **kwargs)

    monkeypatch.setattr(tr, "make_env", env_factory)
    monkeypatch.setattr(tr, "apply_feedback", spy)
    tr.collect_and_train_canonical(agent, agent.config, spec, feedback=True)
    assert len(calls) == 24 and {frame for _, _, frame in calls} == {D4.MIRROR_X, D4.ROT180}
    for obs, physical, frame in calls:
        assert obs.tobytes() == physical.tobytes()
        assert not np.array_equal(obs[:, :2], transform_observations(physical, frame)[:, :2])


def _plain_vs_canonical(tmp_path, frame_rule):
    spec, config = _tiny()
    outputs = []
    for label in ("plain", "canonical"):
        agent, _ = tr.b02_training.new_agent(copy.deepcopy(config), device=torch.device("cpu"),
                                             log_dir=tmp_path / label / "logs", seed=spec.seed)
        if label == "plain":
            result = b02_tr.collect_and_train(agent, agent.config, spec, feedback=True)
        else:
            result = tr.collect_and_train_canonical(agent, agent.config, spec, feedback=True,
                                                    frame_rule=frame_rule)
        outputs.append((agent, result))
    return outputs


def test_identity_frame_collector_is_bitwise_b02(tmp_path):
    """With every frame forced to IDENTITY the B05 loop is B02's loop: same learner, same records."""
    torch.set_num_threads(1)
    (plain_agent, plain), (canon_agent, canon) = _plain_vs_canonical(
        tmp_path, lambda obs: D4.IDENTITY)
    _assert_same_modules(plain_agent, canon_agent)
    assert optimizer_steps(plain_agent) == optimizer_steps(canon_agent)
    assert plain["counts"] == canon["counts"]
    added = {"frames_chosen", "lane_frames_at_boundary", "collection_seconds", "update_seconds"}
    for left, right in zip(plain["rollouts"], canon["rollouts"], strict=True):
        assert {k: v for k, v in left.items() if k not in added} == \
            {k: v for k, v in right.items() if k not in added
             and k != "episodes_completed"} | {"episodes_completed": left["episodes_completed"]}
        assert [{k: v for k, v in row.items() if k != "frame"} for row in right["episodes_completed"]] \
            == left["episodes_completed"]


def test_sw_frame_changes_the_learning_target(tmp_path):
    """The same seed under the SW rule (non-identity lanes) is a different fit (the wrapper acts)."""
    torch.set_num_threads(1)
    (plain_agent, _), (canon_agent, _) = _plain_vs_canonical(tmp_path, None)
    differs = any(not torch.equal(a, b) for a, b in zip(
        plain_agent.skill_discoverer.state_dict().values(),
        canon_agent.skill_discoverer.state_dict().values()))
    assert differs


def test_off_flag_calls_b02_function(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(tr, "plain_collect_and_train",
                        lambda *args, **kwargs: calls.append((args, kwargs)) or "b02")
    spec, config = _tiny(canonical="off")
    assert tr.collect_and_train_canonical(None, config, spec, feedback=True) == "b02"
    assert len(calls) == 1
    with pytest.raises(ValueError, match="unknown canonical flag"):
        tr.frame_rule_of(replace(spec, canonical="ne"))


def test_run_training_routes_the_canonical_collector_and_c00(tmp_path):
    """``run_training`` goes through the B05 collector (records carry frames), writes B05 records and
    a manifest, and its c00 is bitwise the plain B02 recipe's c00 for the same seed (d)."""
    torch.set_num_threads(1)
    spec, _ = _tiny()
    # The tiny spec cannot carry the battery override through run_training; the recipe builds
    # its own config from the spec (same as production).
    summary = tr.run_training(out=tmp_path / "b05", launch_sha="test", spec=spec,
                              device_name="cpu", threads=1, argv=["test"])
    assert summary["status"] == "COMPLETE" and summary["object_id"] == tr.OBJECT_ID
    config_json = json.loads((tmp_path / "b05" / "config.json").read_text())
    assert config_json["canonical_frame"]["rule"] == "sw" and config_json["spec"]["canonical"] == "sw"
    progress = [json.loads(line) for line in (tmp_path / "b05" / "progress.jsonl").read_text().splitlines()]
    rollouts = [row["event"] for row in progress if row["event"].get("event") == "rollout"]
    assert rollouts and all("frames_chosen" in event for event in rollouts)
    assert rollouts[0]["frames_chosen"][0]["frame"] == "MIRROR_X"
    records = sorted((tmp_path / "b05" / "checkpoints").glob("c*/record.json"))
    assert [p.parent.name for p in records] == ["c00", "c01", "c02"]
    for path in records:
        record = json.loads(path.read_text())
        assert record["object_id"] == tr.OBJECT_ID and record["canonical_frame"]["rule"] == "sw"
    manifest = json.loads((tmp_path / "b05" / "manifest.json").read_text())
    assert set(manifest["checkpoints"]) == {"c00", "c01", "c02"}
    assert manifest["canonical_frame"]["adapter_sha256"]
    plain = b02_tr.run_training(out=tmp_path / "b02", launch_sha="test",
                                spec=replace(cfg.B02Spec(), **{k: getattr(spec, k) for k in (
                                    "seed", "rollouts", "rollout_length", "episode_length",
                                    "hidden_size", "gru_hidden_size", "ppo_epochs",
                                    "checkpoint_every_transitions")}),
                                device_name="cpu", threads=1, argv=["test"])
    b05_c00 = json.loads((tmp_path / "b05/checkpoints/c00/record.json").read_text())
    b02_c00 = json.loads((tmp_path / "b02/checkpoints/c00/record.json").read_text())
    assert b05_c00["policy_fingerprint"] == b02_c00["policy_fingerprint"]
    assert b05_c00["config"] == b02_c00["config"]
    left = torch.load(tmp_path / "b05/checkpoints/c00/agent.pt", map_location="cpu", weights_only=False)
    right = torch.load(tmp_path / "b02/checkpoints/c00/agent.pt", map_location="cpu", weights_only=False)
    for key, value in left["skill_discoverer"].items():
        assert torch.equal(value, right["skill_discoverer"][key]), key
    # The two fits then differ (frames act on the learning inputs).
    assert summary["checkpoints"]["c02"]["policy_fingerprint"] != \
        plain["checkpoints"]["c02"]["policy_fingerprint"]
    with pytest.raises(FileExistsError):
        tr.run_training(out=tmp_path / "b05", launch_sha="test", spec=spec, device_name="cpu")


def test_production_recipe_and_c00_initialisation(tmp_path):
    """(d) Production B is B02's recipe: same config record as the saved c00 and, on this device,
    bitwise the plain recipe's initialisation; the saved c00 (CUDA) is compared where CUDA exists."""
    torch.set_num_threads(2)
    spec = tr.production_spec(925031)
    cfg.assert_production(spec)
    config = tr.b05_recipe().make_config(spec)
    if C00.exists():
        record = json.loads((C00 / "record.json").read_text())
        assert tr.b05_recipe().config_dict(config) == record["config"]
        assert record["training_seed"] == spec.seed
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    b05_agent, b05_identity = b02_tr.new_agent(config, device=device, log_dir=tmp_path / "a",
                                               seed=spec.seed, construct=tr.b05_recipe().construct_agent)
    plain_agent, plain_identity = b02_tr.new_agent(cfg.make_b02_config(cfg.production_spec(925031)),
                                                   device=device, log_dir=tmp_path / "b", seed=spec.seed)
    assert b05_identity == plain_identity
    _assert_same_modules(b05_agent, plain_agent)
    if device.type != "cuda":
        pytest.skip("the recorded c00 fingerprint is a CUDA initialisation; compare on the node "
                    f"(CPU gives {b05_identity['policy_fingerprint'][:8]}...)")
    assert b05_identity["policy_fingerprint"] == C00_FINGERPRINT   # the recorded c06 lineage's c00


def test_production_spec_guards():
    spec = tr.production_spec(925031)
    assert spec.canonical == "sw" and spec.transitions == 1_200_000
    assert cfg.checkpoint_rollouts(spec) == (34, 67, 100, 134, 167, 200)
    with pytest.raises(ValueError):
        tr.production_spec(1)
    with pytest.raises(TypeError):
        tr.run_training(out=Path("never"), launch_sha="x", spec=cfg.B02Spec())


def test_resume_from_a_b05_checkpoint(tmp_path):
    """``--resume-from`` finishes a B05 fit from its own checkpoint through the canonical collector;
    a B02 checkpoint is refused (object id)."""
    torch.set_num_threads(1)
    spec, _ = _tiny()
    tr.run_training(out=tmp_path / "fit", launch_sha="src", spec=spec, device_name="cpu", threads=1)
    resumed = tr.run_training(out=tmp_path / "resumed", launch_sha="test", spec=spec,
                              device_name="cpu", threads=1,
                              resume_from=tmp_path / "fit" / "checkpoints" / "c01",
                              resume_source_sha="src")
    assert resumed["status"] == "COMPLETE" and resumed["resume"]["checkpoint"] == "c01"
    assert resumed["rollouts"][0]["frames_chosen"][0]["step"] is None
    assert sorted(p.name for p in (tmp_path / "resumed" / "checkpoints").iterdir()) == ["c02"]
    plain_spec = replace(cfg.B02Spec(), **{k: getattr(spec, k) for k in (
        "seed", "rollouts", "rollout_length", "episode_length", "hidden_size", "gru_hidden_size",
        "ppo_epochs", "checkpoint_every_transitions")})
    b02_tr.run_training(out=tmp_path / "b02", launch_sha="src", spec=plain_spec, device_name="cpu",
                        threads=1)
    with pytest.raises(ValueError, match="is not ENERGY-RELAY-BENCHMARK-B05"):
        tr.run_training(out=tmp_path / "refused", launch_sha="test", spec=spec, device_name="cpu",
                        threads=1, resume_from=tmp_path / "b02" / "checkpoints" / "c01")
