"""CF central-input pathway of the FSD matched-information baseline B01 (card section 8).

Real agents on the real Scenario 1 host at a tiny size (two lanes, twenty-step episodes): the
snapshot's fields, its refresh steps and lane reset, the identity of the actor input across
collection, stored replay and the evaluator, and the flag-off bit identity of every other arm.
These are technical checks of the changed contract, never a scientific result.
"""
import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_flexible_skill_duration_e0 as e0  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

shared = b01.shared
LANES, HORIZON, N_UAVS, K = 2, 20, 6, 10
SEED = 772603


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(shared, "HORIZON", HORIZON)
    monkeypatch.setattr(shared, "TRAIN_LANES", LANES)
    monkeypatch.setattr(shared, "EVAL_LANES", LANES)
    matched.bind()


def build(tmp_path, arm="CF", seed=SEED, lanes=LANES, name="learner", **config_overrides):
    """One real learner of this object's arm, built through the runner's own make_config."""
    shared.seed_rng(seed)
    envs = e0._make_envs(lanes, seed, N_UAVS, shared.N_USERS, HORIZON)
    config = matched.make_config(arm, envs, seed)
    for key, value in config_overrides.items():
        setattr(config, key, value)
    agent = HMASDAgent(config, log_dir=str(tmp_path / name), device=torch.device("cpu"))
    return envs, config, agent


def capture_actor_inputs(agent, sink):
    return agent.skill_discoverer.actor.register_forward_pre_hook(
        lambda module, args: sink.append(np.array(args[0].detach().cpu().numpy(), copy=True)))


def collect(agent, envs, steps, *, store=True, record=None, reset_at=None):
    """The frozen collector loop of the B01 runner at a tiny size."""
    states, observations = e0._reset_all(envs)
    lanes = len(envs)
    env_steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
    for t in range(steps):
        actions, _, data = agent.step(states, observations, env_steps, dones,
                                      deterministic=not agent.training, return_step_data=True,
                                      build_infos=False)
        if record is not None:
            record.append({
                "t": t,
                "skill_timer": np.asarray(data["skill_timer"], dtype=np.int64).copy(),
                "snapshot_states": agent._central_snapshot_states[:lanes].copy(),
                "snapshot_obs": agent._central_snapshot_obs[:lanes].copy(),
                "states": states.copy(), "observations": observations.copy(),
                "env_steps": env_steps.copy(), "dones": dones.copy(), "reset_lanes": []})
        next_states, next_observations = [], []
        rewards, next_dones = np.zeros(lanes), np.zeros(lanes, dtype=bool)
        for lane, env in enumerate(envs):
            observation, reward, terminated, truncated, info = env.step(actions[lane])
            next_dones[lane] = bool(terminated or truncated)
            rewards[lane] = reward
            next_states.append(np.asarray(info["next_state"], dtype=np.float64))
            next_observations.append(np.asarray(observation, dtype=np.float32))
        next_states, next_observations = np.stack(next_states), np.stack(next_observations)
        if store:
            agent.store_transition_batch(
                states=states, next_states=next_states.copy(), observations=observations,
                next_observations=next_observations.copy(), actions=actions, rewards=rewards,
                dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data)
        forced = () if reset_at is None else reset_at.get(t, ())
        for lane, env in enumerate(envs):
            if next_dones[lane] or lane in forced:
                reset_observation, reset_info = env.reset()
                next_observations[lane] = np.asarray(reset_observation, dtype=np.float32)
                next_states[lane] = np.asarray(reset_info["state"], dtype=np.float64)
                agent.reset_env_state(lane)
                env_steps[lane] = 0
                if record is not None:
                    record[-1]["reset_lanes"].append(lane)
            else:
                env_steps[lane] += 1
        states, observations, dones = next_states, next_observations, next_dones
    return states, observations, dones


def test_snapshot_fields_refresh_steps_and_lane_reset(tmp_path, tiny):
    envs, config, agent = build(tmp_path)
    agent.train(True)
    assert getattr(config, matched.CF_FLAG) is True and config.k == K
    central = agent.skill_discoverer.central_input_dim
    assert central == config.state_dim + N_UAVS * config.obs_dim + N_UAVS
    assert agent.skill_discoverer.actor.base.mlp[0].in_features == config.obs_dim + central
    # Nothing else widened: the critic still reads the global state alone.
    assert agent.skill_discoverer.critic.base.mlp[0].in_features == config.state_dim
    assert agent.skill_discoverer.actor.rnn.rnn.input_size == config.hidden_size

    inputs, record = [], []
    capture_actor_inputs(agent, inputs)
    # A forced lane-0 reset at step 3 leaves the k-cadence of lane 1 untouched. One step short
    # of the horizon, so the episode's own terminal reset does not hide the lane-reset check.
    collect(agent, envs, HORIZON - 1, store=False, record=record, reset_at={3: (0,)})

    for step, row in enumerate(record):
        actor_input = inputs[step].reshape(LANES, N_UAVS, -1)
        for lane in range(LANES):
            for agent_index in range(N_UAVS):
                row_input = actor_input[lane, agent_index]
                np.testing.assert_array_equal(
                    row_input[:config.obs_dim], row["observations"][lane, agent_index])
                offset = config.obs_dim
                np.testing.assert_array_equal(
                    row_input[offset:offset + config.state_dim],
                    row["snapshot_states"][lane].astype(np.float32))
                offset += config.state_dim
                np.testing.assert_array_equal(
                    row_input[offset:offset + N_UAVS * config.obs_dim],
                    row["snapshot_obs"][lane].reshape(-1))
                ego = row_input[-N_UAVS:]
                np.testing.assert_array_equal(ego, np.eye(N_UAVS, dtype=np.float32)[agent_index])

    for lane in range(LANES):
        refreshed = [row["t"] for row in record
                     if row["t"] == 0 or not np.array_equal(row["snapshot_states"][lane],
                                                            record[row["t"] - 1]["snapshot_states"][lane])]
        decisions = [row["t"] for row in record if row["skill_timer"][lane] == 0]
        assert refreshed == decisions, (lane, refreshed, decisions)
    # Lane 1 keeps the plain k cadence; lane 0 restarts it at its reset (step 3 resets, so the
    # step-4 input is the first of the new episode).
    assert [row["t"] for row in record if row["skill_timer"][1] == 0] == [0, 10]
    assert [row["t"] for row in record if row["skill_timer"][0] == 0] == [0, 4, 14]
    for row in record:
        if row["t"] in (4, 14):
            np.testing.assert_array_equal(row["snapshot_states"][0], row["states"][0])
            np.testing.assert_array_equal(row["snapshot_obs"][0], row["observations"][0])

    agent.reset_env_state(0)
    assert not agent._central_snapshot_valid[0] and agent._central_snapshot_valid[1]
    assert not agent._central_snapshot_states[0].any()


def test_collection_replay_and_evaluator_read_the_identical_actor_input(tmp_path, tiny):
    envs, config, agent = build(tmp_path)
    agent.train(True)
    assert config.use_obsnorm is False and config.use_statenorm is False
    collected, record = [], []
    capture_actor_inputs(agent, collected)
    states, observations, dones = collect(agent, envs, HORIZON, record=record)
    collected = np.stack(collected)

    # Replay: one PPO epoch, one batch, no shuffle, so sequence i is (chunk, env, agent).
    class _NoShuffle:
        def shuffle(self, array):
            return None

    agent.rollout_buffer._sampler_rng = _NoShuffle()
    agent.config.ppo_epochs = 1
    agent.config.sequence_batch_size = 10 ** 6
    replayed = []
    original = agent.skill_discoverer.actor.evaluate_actions

    def spy(observations_seq, *args, **kwargs):
        replayed.append(np.array(observations_seq.detach().cpu().numpy(), copy=True))
        return original(observations_seq, *args, **kwargs)

    agent.skill_discoverer.actor.evaluate_actions = spy
    agent.update(last_values=np.zeros((LANES, N_UAVS), dtype=np.float32), dones=dones.copy(),
                 steps_in_buffer=HORIZON, last_state=states.copy(), last_observations=observations.copy())
    assert len(replayed) == 1
    sequence = replayed[0]
    assert sequence.shape == (K, (HORIZON // K) * LANES * N_UAVS,
                              config.obs_dim + agent.skill_discoverer.central_input_dim)
    for index in range(sequence.shape[1]):
        chunk, remainder = divmod(index, LANES * N_UAVS)
        lane, agent_index = divmod(remainder, N_UAVS)
        for local in range(K):
            np.testing.assert_array_equal(
                sequence[local, index], collected[chunk * K + local, lane * N_UAVS + agent_index])

    # The evaluator assembles the same tensor from its own snapshot, timer and RNN state.
    # It is driven over the collected input sequence, because a deterministic evaluator's own
    # actions would move its worlds away from the learner's after the first step; what must be
    # identical is the actor input the same information produces.
    _envs, _config, evaluator = build(tmp_path, lanes=LANES, name="evaluator", seed=SEED)
    evaluator.skill_discoverer.load_state_dict(agent.skill_discoverer.state_dict())
    evaluator.skill_coordinator.load_state_dict(agent.skill_coordinator.state_dict())
    evaluator.obs_norm = e0.copy.deepcopy(agent.obs_norm)
    evaluator.state_norm = e0.copy.deepcopy(agent.state_norm)
    evaluator.train(False)
    for lane in range(LANES):
        evaluator.reset_env_state(lane)
    learner_snapshot = agent._central_snapshot_states.copy()
    learner_buffer = agent.rollout_buffer.central_snapshot_states.copy()
    learner_rng = _rng_state()
    evaluation_inputs = []
    capture_actor_inputs(evaluator, evaluation_inputs)
    # The runner runs every panel inside this wrapper; the evaluator's own construction and
    # steps draw RNG, and the learner's stream must not see them.
    with e0._preserve_rng(), torch.no_grad():
        for row in record:
            evaluator.step(row["states"], row["observations"], row["env_steps"], row["dones"],
                           deterministic=True, return_step_data=True, build_infos=False)
            for lane in row["reset_lanes"]:
                evaluator.reset_env_state(lane)
    evaluation_inputs = np.stack(evaluation_inputs)
    np.testing.assert_array_equal(
        evaluation_inputs[:, :, config.obs_dim:], collected[:, :, config.obs_dim:])
    np.testing.assert_array_equal(evaluation_inputs, collected)
    # Evaluation touched no learner snapshot, buffer or RNG stream.
    np.testing.assert_array_equal(learner_snapshot, agent._central_snapshot_states)
    np.testing.assert_array_equal(learner_buffer, agent.rollout_buffer.central_snapshot_states)
    _assert_rng_equal(learner_rng, _rng_state())


def test_running_normalisation_replay_matches_the_private_observation_path(tmp_path, tiny):
    """With running normalisers on, the snapshot inherits the existing replay semantics.

    The stored snapshot is raw and re-normalised at replay with the end-of-rollout statistics,
    exactly as the private observation and the critic state already are; the ego one-hot has no
    statistics and is exact. The B01 arms run with both normalisers off, where the whole actor
    input replays bit-identically (previous test).
    """
    envs, config, agent = build(tmp_path, use_obsnorm=True, use_statenorm=True)
    agent.train(True)
    collected, record = [], []
    capture_actor_inputs(agent, collected)
    states, observations, dones = collect(agent, envs, HORIZON, record=record)
    collected = np.stack(collected)

    class _NoShuffle:
        def shuffle(self, array):
            return None

    agent.rollout_buffer._sampler_rng = _NoShuffle()
    agent.config.ppo_epochs = 1
    agent.config.sequence_batch_size = 10 ** 6
    replayed = []
    original = agent.skill_discoverer.actor.evaluate_actions

    def spy(observations_seq, *args, **kwargs):
        replayed.append(np.array(observations_seq.detach().cpu().numpy(), copy=True))
        return original(observations_seq, *args, **kwargs)

    agent.skill_discoverer.actor.evaluate_actions = spy
    agent.update(last_values=np.zeros((LANES, N_UAVS), dtype=np.float32), dones=dones.copy(),
                 steps_in_buffer=HORIZON, last_state=states.copy(), last_observations=observations.copy())
    sequence = replayed[0]
    private, snapshot, ego = [], [], []
    for index in range(sequence.shape[1]):
        chunk, remainder = divmod(index, LANES * N_UAVS)
        lane, agent_index = divmod(remainder, N_UAVS)
        for local in range(K):
            difference = np.abs(sequence[local, index]
                                - collected[chunk * K + local, lane * N_UAVS + agent_index])
            private.append(difference[:config.obs_dim].max())
            snapshot.append(difference[config.obs_dim:-N_UAVS].max())
            ego.append(difference[-N_UAVS:].max())
    assert max(ego) == 0.0
    assert max(private) > 0.0  # the pre-existing normaliser drift, not a CF effect
    assert max(snapshot) == pytest.approx(max(private), rel=1e-6)

    # The stored raw snapshot is byte-identical to the raw values the collector held, at every
    # step and not only at the refresh steps.
    buffer = agent.rollout_buffer
    assert buffer.central_snapshot_mask[:HORIZON].all()
    for row in record:
        np.testing.assert_array_equal(
            buffer.central_snapshot_states[row["t"]],
            row["snapshot_states"].astype(np.float32))
        np.testing.assert_array_equal(buffer.central_snapshot_obs[row["t"]], row["snapshot_obs"])


def _rng_state():
    return (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())


def _assert_rng_equal(first, second):
    assert first[0] == second[0]
    assert first[1][0] == second[1][0] and first[1][2:] == second[1][2:]
    np.testing.assert_array_equal(first[1][1], second[1][1])
    assert torch.equal(first[2], second[2])


def _owner_of(config, name):
    return next(klass for klass in type(config).__mro__ if name in klass.__dict__)


def test_flag_off_is_bit_identical_to_the_flag_being_absent(tmp_path, tiny, monkeypatch):
    """Every other arm: no module, parameter, buffer field, RNG draw or tensor shape changes."""
    results = {}
    for label in ("absent", "false"):
        shared.seed_rng(SEED)
        envs = e0._make_envs(LANES, SEED, N_UAVS, shared.N_USERS, HORIZON)
        config = matched.make_config("D1280", envs, SEED)
        with monkeypatch.context() as patch:
            if label == "absent":
                # An older config object carries no such attribute at all; the agent, the
                # discoverer and the buffer must reach the same state through getattr defaults.
                patch.delattr(_owner_of(config, matched.CF_FLAG), matched.CF_FLAG)
                assert not hasattr(config, matched.CF_FLAG)
            else:
                setattr(config, matched.CF_FLAG, False)
            agent = HMASDAgent(config, log_dir=str(tmp_path / label), device=torch.device("cpu"))
        state_after_construction = _rng_state()
        agent.train(True)
        actions = []
        states, observations = e0._reset_all(envs)
        env_steps, dones = np.zeros(LANES, dtype=int), np.zeros(LANES, dtype=bool)
        for t in range(4):
            step_actions, _, data = agent.step(states, observations, env_steps, dones,
                                               deterministic=False, return_step_data=True,
                                               build_infos=False)
            actions.append((step_actions.copy(), np.asarray(data["values"]).copy(),
                            np.asarray(data["action_logprobs"]).copy()))
            next_states, next_observations = [], []
            for lane, env in enumerate(envs):
                observation, _reward, terminated, truncated, info = env.step(step_actions[lane])
                next_states.append(np.asarray(info["next_state"], dtype=np.float64))
                next_observations.append(np.asarray(observation, dtype=np.float32))
            states, observations = np.stack(next_states), np.stack(next_observations)
            env_steps += 1
        results[label] = {
            "parameters": {name: [p.detach().clone() for p in parameters]
                           for name, parameters in e0._parameter_groups(agent).items()},
            "rng": state_after_construction,
            "actions": actions,
            "agent": agent,
        }
    absent, false = results["absent"], results["false"]
    assert set(absent["parameters"]) == set(false["parameters"])
    for name, left_parameters in absent["parameters"].items():
        right_parameters = false["parameters"][name]
        assert len(left_parameters) == len(right_parameters) and left_parameters
        for left, right in zip(left_parameters, right_parameters):
            assert left.shape == right.shape and torch.equal(left, right)
    _assert_rng_equal(absent["rng"], false["rng"])
    for (left_actions, left_values, left_logprobs), (right_actions, right_values, right_logprobs) in zip(
            absent["actions"], false["actions"]):
        np.testing.assert_array_equal(left_actions, right_actions)
        np.testing.assert_array_equal(left_values, right_values)
        np.testing.assert_array_equal(left_logprobs, right_logprobs)
    for label in ("absent", "false"):
        agent = results[label]["agent"]
        assert agent.use_central_snapshot is False
        assert agent._central_snapshot_states is None and agent._central_snapshot_valid is None
        assert agent.rollout_buffer.central_snapshot is False
        for field in ("central_snapshot_states", "central_snapshot_obs", "central_snapshot_mask"):
            assert not hasattr(agent.rollout_buffer, field), f"flag-off allocated {field}"
        assert agent.skill_discoverer.central_input_dim == 0
        assert (agent.skill_discoverer.actor.base.mlp[0].in_features
                == agent.config.obs_dim)


def test_central_snapshot_is_refused_outside_the_off_route(tmp_path, tiny):
    envs = e0._make_envs(1, SEED, N_UAVS, shared.N_USERS, HORIZON)
    config = matched.make_config("D1280", envs, SEED)
    setattr(config, matched.CF_FLAG, True)
    with pytest.raises(ValueError, match="`off` route only"):
        HMASDAgent(config, log_dir=str(tmp_path / "refused"), device=torch.device("cpu"))
