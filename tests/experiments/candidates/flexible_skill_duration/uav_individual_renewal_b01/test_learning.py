"""Fake-only tests at the UAV B01 production boundaries; no real model or host."""
import copy
import importlib.util
import json
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location("fsd_uav_b01", ROOT / "scripts/run_fsd_uav_individual_renewal_b01.py")
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Module:
    def __init__(self, value):
        self.values = [torch.tensor(float(value)), torch.tensor(float(value + 1))]

    def parameters(self):
        return self.values

    def actor_update_parameters(self):
        return self.values[:1]

    def critic_update_parameters(self):
        return self.values[1:]

    def state_dict(self):
        return {"values": [v.clone() for v in self.values]}

    def load_state_dict(self, state):
        self.values = [v.clone() for v in state["values"]]


class Optimizer:
    def __init__(self, parameters):
        self.parameters, self.calls = parameters, 0

    def step(self):
        self.calls += 1
        for parameter in self.parameters:
            parameter.add_(.01)


class Agent:
    constructed = []

    def __init__(self, config, **kwargs):
        self.constructor_rng = (random.random(), np.random.rand(), float(torch.rand(())))
        self.config, self.device = config, kwargs["device"]
        self.threads = torch.get_num_threads()
        self.skill_coordinator, self.skill_discoverer = Module(1), Module(3)
        self.team_discriminator, self.individual_discriminator = Module(5), Module(7)
        self.obs_norm = SimpleNamespace(mean=np.array([10.]), var=np.array([2.]), count=3)
        self.state_norm = SimpleNamespace(mean=np.array([11.]), var=np.array([3.]), count=4)
        self.value_norm_coordinator = SimpleNamespace(mean=np.array([12.]), var=np.array([4.]), count=5)
        self.value_norm_discoverer = SimpleNamespace(mean=np.array([13.]), var=np.array([5.]), count=6)
        for name, parameters in r.e0._parameter_groups(self).items():
            setattr(self, name + "_optimizer", Optimizer(parameters))
        self.inputs, self.data, self.actions, self.stored, self.events, self.reset_calls = [], [], [], [], [], []
        self.updates, self.training = 0, True
        self._reset_metrics()
        self.constructed.append(self)

    def _reset_metrics(self):
        self.d2_metrics = {"segment_lengths_agent": [], "segment_lengths_team": []}
        self.metrics = {"steps": 0, "decision_steps": 0, "team_decisions": 0, "sampled_total": 0,
                        "switch_count_by_agent": [0] * r.N_UAVS,
                        "cause_counts": {"reset": 0, "team_gap": 0, "team_cap": 0, "gap": 0, "cap": 0}}

    def train(self, mode):
        self.training = mode

    def clear_buffers(self):
        self.events.append("clear")
        self._reset_metrics()

    def reset_env_state(self, lane):
        self.events.append("reset_lane")
        self.reset_calls.append(lane)

    def step(self, states, observations, steps, dones, **kwargs):
        self.events.append("step")
        assert kwargs["deterministic"] is (not self.training)
        if not self.training:
            assert not torch.is_grad_enabled()
        random.random(), np.random.rand(), torch.rand(1)
        self.inputs.append((states.copy(), observations.copy(), steps.copy(), dones.copy(), self.updates))
        lanes = len(states)
        sampled = np.broadcast_to((steps % 10 == 0)[:, None], (lanes, r.N_UAVS)).copy()
        # Both arms may have no extra gaps and may resample the same token.
        data = {"d2_sampled_mask": sampled, "d2_team_decision": sampled.any(1),
                "team_skills": np.full(lanes, 4), "agent_skills": np.full((lanes, r.N_UAVS), 3),
                "credit_marker": np.arange(lanes) + 71., "same_token": True}
        actions = np.broadcast_to((self.updates + steps * .01 + states[:, 0] * .0001)[:, None, None],
                                  (lanes, r.N_UAVS, 3)).copy().astype(np.float32)
        self.data.append(data)
        self.actions.append(actions)
        self.metrics["steps"] += lanes
        self.metrics["decision_steps"] += int(sampled.any(1).sum())
        self.metrics["team_decisions"] += int(sampled.any(1).sum())
        self.metrics["sampled_total"] += int(sampled.sum())
        return actions, None, data

    def store_transition_batch(self, **kwargs):
        self.events.append("store")
        assert kwargs["step_data"] is self.data[-1]
        assert kwargs["actions"] is self.actions[-1]
        self.stored.append(copy.deepcopy(kwargs))
        if kwargs["dones"].all():
            self.d2_metrics["segment_lengths_agent"] = [r.HORIZON] * (self.config.num_envs * r.N_UAVS)
            self.d2_metrics["segment_lengths_team"] = [r.HORIZON] * self.config.num_envs

    def update(self, **kwargs):
        self.events.append("update")
        assert kwargs["steps_in_buffer"] == r.HORIZON
        assert kwargs["dones"].all() and not kwargs["last_values"].any()
        for lane in range(self.config.num_envs):
            assert (kwargs["last_state"][lane] == 100 * (self.updates + 2) + lane).all()
            assert (kwargs["last_observations"][lane] == 10 * (self.updates + 2) + lane).all()
        self.updates += 1
        for i, name in enumerate(r.NETWORKS):
            for _ in range(i):
                getattr(self, name + "_optimizer").step()
        self.value_norm_coordinator.mean += .1
        self.value_norm_discoverer.var += .2
        return {"coordinator_loss": .5, "discoverer_loss": float(self.updates), "unused_group": None}

    def get_d2_metrics(self):
        self.events.append("metrics")
        return copy.deepcopy(self.metrics)


class Env:
    state_dim, obs_dim = 7, 3

    def __init__(self, lane, seed):
        self.lane, self.seed, self.resets, self.t = lane, seed, 0, 0
        self.actions, self.rewards = [], []

    def reset(self):
        random.random(), np.random.rand(), torch.rand(1)
        self.resets += 1
        self.t = 0
        return np.full((r.N_UAVS, 3), 10 * self.resets + self.lane), {
            "state": np.full(7, 100 * self.resets + self.lane)}

    def step(self, actions):
        self.actions.append(actions)
        self.t += 1
        # Deliberately non-unit raw reward, with exact native info components.
        coverage, quality, altitude = .5 + self.lane * .01, .4, .03
        native = .7 * coverage + .3 * quality - altitude
        reward = native / r.N_UAVS
        self.rewards.append(reward)
        return np.full((r.N_UAVS, 3), 800 + self.t + self.lane), reward, self.t == r.HORIZON, False, {
            "next_state": np.full(7, 900 + self.t + self.lane),
            "reward_components": {"reward_info": {"coverage_reward": coverage, "quality_reward": quality,
                                                 "energy_penalty": altitude, "total_reward": native}}}


@pytest.fixture(autouse=True)
def fake_only(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("real scientific construction forbidden")
    import hmasd.agent
    import envs.pettingzoo.scenario1
    monkeypatch.setattr(hmasd.agent, "HMASDAgent", forbidden)
    monkeypatch.setattr(envs.pettingzoo.scenario1, "UAVBaseStationEnv", forbidden)
    monkeypatch.setattr(r.e0, "UAVBaseStationEnv", forbidden)
    monkeypatch.setattr(r.e0, "HMASDAgent", forbidden)
    monkeypatch.setattr(r, "HMASDAgent", Agent)
    monkeypatch.setattr(r, "TRAIN_LANES", 2)
    monkeypatch.setattr(r, "EVAL_LANES", 3)
    monkeypatch.setattr(r, "HORIZON", 10)
    monkeypatch.setattr(r, "PROCESS_START", r.time.perf_counter())
    monkeypatch.setattr(r.e0, "_git", lambda *args: "synthetic-source")
    Agent.constructed = []
    batches = []
    def make_envs(count, seed, n_uavs, n_users, horizon):
        assert n_uavs == 6 and n_users == 50 and horizon == r.HORIZON
        envs = [Env(lane, seed + lane) for lane in range(count)]
        batches.append(envs)
        return envs
    monkeypatch.setattr(r.e0, "_make_envs", make_envs)
    return batches


def argv(arm, out, *extra):
    return ["--arm", arm, "--output-root", str(out), *map(str, extra)]


def rng_state():
    return random.getstate(), copy.deepcopy(np.random.get_state()), torch.get_rng_state().clone()


def assert_rng_equal(a, b):
    assert a[0] == b[0] and a[1][0] == b[1][0] and a[1][2:] == b[1][2:]
    np.testing.assert_array_equal(a[1][1], b[1][1])
    assert torch.equal(a[2], b[2])


@pytest.mark.parametrize("arm,cost", [("D0", float("inf")), ("I", .25)])
def test_real_config_reaches_learner_and_evaluator(monkeypatch, tmp_path, fake_only, arm, cost):
    monkeypatch.setattr(r, "TRAIN_LANES", 16)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    monkeypatch.setattr(r, "HORIZON", 500)
    s = r.base_summary(arm)
    calls = []
    original = r.seed_rng
    def seed(seed):
        calls.append(seed)
        original(seed)
    monkeypatch.setattr(r, "seed_rng", seed)
    envs, learner, _, _ = r.build_learner(s, tmp_path)
    assert calls == [770503]
    assert [env.seed for env in envs] == list(range(770503, 770519))
    # Build evaluator in the same required scope without a 500-step fake loop.
    with r.e0._preserve_rng():
        r.seed_rng(r.EVAL_SEED)
        evaluator = r.Evaluator(arm, tmp_path)
    assert calls == [770503, 780503]
    assert [env.seed for env in evaluator.envs] == list(range(780503, 780535))
    for agent, count, seed in ((learner, 16, 770503), (evaluator.agent, 32, 780503)):
        cfg = agent.config
        assert cfg.policy_interruption_mode == "d2" and cfg.interruption_cost_c == cost
        assert cfg.interruption_cost_c_Z == float("inf") and cfg.age_feature == "off"
        assert cfg.k == cfg.skill_cap_k_max == cfg.team_cap_k_Z == 10
        assert cfg.interruption_delta == 1 and cfg.n_Z == cfg.n_z == cfg.n_agents == 6
        assert cfg.n_users == 50 and cfg.num_envs == count and cfg.seed == seed
        assert cfg.state_dim == 7 and cfg.obs_dim == 3 and cfg.action_dim == 3
        assert cfg.gamma == .99 and cfg.gae_lambda == .95 and cfg.ppo_epochs == 15
        assert cfg.use_valuenorm and not cfg.use_obsnorm and not cfg.use_statenorm
        assert cfg.high_level_buffer_size == count * 50 and cfg.high_level_batch_size == 128
        assert cfg.total_timesteps == count * 500 * 5
        assert agent.threads == 4 and agent.device == torch.device("cpu")
    assert learner.training and not evaluator.agent.training
    r.write_json(tmp_path / "config.json", r.config_snapshot(learner.config))
    stored = json.loads((tmp_path / "config.json").read_text())
    assert stored["interruption_cost_c_Z"] == "Infinity"
    assert stored["interruption_cost_c"] == ("Infinity" if arm == "D0" else .25)


@pytest.mark.parametrize("arm", ["D0", "I"])
def test_actual_actions_storage_terminal_reset_and_updates(tmp_path, fake_only, arm):
    s = r.base_summary(arm)
    envs, agent, theta0, counters = r.build_learner(s, tmp_path)
    r.collect_training(envs, agent, theta0, counters, s, tmp_path)
    assert agent.updates == s["counts"]["update_stages"] == 5
    assert len(agent.inputs) == 50 and len(agent.stored) == 50  # No bootstrap action.
    assert agent.reset_calls == [0, 1] * 5
    assert [env.resets for env in envs] == [6, 6]
    assert [event for event in agent.events if event in ("update", "metrics", "clear")] == ["update", "metrics", "clear"] * 5
    for rollout in range(5):
        for t in range(10):
            index = rollout * 10 + t
            stored = agent.stored[index]
            assert stored["rollout_step_idx"] == t
            np.testing.assert_array_equal(stored["step_data"]["agent_skills"], 3)
            assert stored["step_data"]["same_token"] is True
            np.testing.assert_array_equal(stored["step_data"]["d2_sampled_mask"], t == 0)
            for lane in range(2):
                assert np.shares_memory(envs[lane].actions[index], agent.actions[index])
                np.testing.assert_array_equal(stored["actions"][lane], envs[lane].actions[index])
                assert stored["rewards"][lane] == envs[lane].rewards[index]  # Raw, not scaled.
                assert (stored["next_states"][lane] == 901 + t + lane).all()
                assert (stored["next_observations"][lane] == 801 + t + lane).all()
            assert stored["rewards"].dtype == np.float64
            assert bool(stored["dones"].all()) == (t == 9)
        states, observations, steps, dones, update = agent.inputs[rollout * 10]
        for lane in range(2):
            assert (states[lane] == 100 * (rollout + 1) + lane).all()
            assert (observations[lane] == 10 * (rollout + 1) + lane).all()
        assert not steps.any() and bool(dones.all()) == (rollout > 0) and update == rollout
        row = s["training_rows"][rollout]
        assert row["optimizer_calls_delta"] == dict(zip(r.NETWORKS, range(5)))
        assert row["d2_metrics"]["cause_counts"]["gap"] == 0
        assert row["d2_metrics"]["sampled_total"] == 12
        assert row["d2_metrics"]["switch_count_by_agent"] == [0] * 6
        assert row["segments"]["agent"]["min"] == row["segments"]["agent"]["max"] == 10
        assert row["relative_initialization_displacement"]["coordinator"] == 0
        assert row["relative_initialization_displacement"]["discoverer_actor"] > 0
    assert s["counts"]["training_transitions"] == s["counts"]["stored_training_transitions"] == 100
    assert s["counts"]["training_episodes"] == 10
    assert len((tmp_path / "training.jsonl").read_text().splitlines()) == 5


@pytest.mark.parametrize("arm", ["D0", "I"])
def test_final_only_sync_rng_and_native_components(tmp_path, fake_only, arm):
    s = r.base_summary(arm)
    envs, learner, theta0, counters = r.build_learner(s, tmp_path)
    r.collect_training(envs, learner, theta0, counters, s, tmp_path)
    original = copy.deepcopy(learner.__dict__)
    before = rng_state()
    r.final_evaluation(learner, s, tmp_path)
    assert_rng_equal(before, rng_state())
    evaluator = Agent.constructed[-1]
    assert evaluator is not learner and not evaluator.training and evaluator.updates == 0
    assert len(Agent.constructed) == 2 and s["evaluation"]["after_update"] == 5
    assert evaluator.reset_calls == [0, 1, 2] and evaluator.events[0] == "clear"
    assert learner.events == original["events"] and learner.reset_calls == original["reset_calls"]
    assert learner.updates == 5 and len(evaluator.inputs) == 10 and not evaluator.stored
    assert not any(s["evaluation_optimizer_calls"].values())
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
        for source, target, old in zip(getattr(learner, name).parameters(), getattr(evaluator, name).parameters(), original[name].parameters()):
            assert torch.equal(source, target) and torch.equal(source, old)
            assert source.data_ptr() != target.data_ptr()
    for name in ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer"):
        source, target, old = getattr(learner, name), getattr(evaluator, name), original[name]
        for key in ("mean", "var"):
            np.testing.assert_array_equal(getattr(source, key), getattr(target, key))
            np.testing.assert_array_equal(getattr(source, key), getattr(old, key))
            assert not np.shares_memory(getattr(source, key), getattr(target, key))
        assert source.count == target.count == old.count
    e = s["evaluation"]
    assert e["episode_ids"] == [0, 1, 2] and e["lane_seeds"] == [780503, 780504, 780505]
    for lane, env in enumerate(fake_only[-1]):
        assert env.resets == 1
        assert e["returns_U"][lane] == pytest.approx(sum(env.rewards))
        assert e["native_scores_J"][lane] == pytest.approx(6 * sum(env.rewards) / 10)
        assert e["component_means"]["coverage_reward"][lane] == pytest.approx(.5 + lane * .01)
        assert e["component_means"]["quality_reward"][lane] == pytest.approx(.4)
        assert e["component_means"]["energy_penalty"][lane] == pytest.approx(.03)
        assert e["component_means"]["total_reward"][lane] == pytest.approx(e["native_scores_J"][lane])
    assert e["d2_metrics"]["team_decisions"] == 3 and e["d2_metrics"]["sampled_total"] == 18
    assert e["segments"]["agent"]["count"] == 0  # Evaluation does not store learner segments.


def completed(arm, returns):
    s = r.base_summary(arm)
    s["status"] = "complete"
    s["counts"].update(model_constructions=2, training_starts=1, training_transitions=r.TRAIN_LANES*r.HORIZON*5,
                       stored_training_transitions=r.TRAIN_LANES*r.HORIZON*5, training_episodes=r.TRAIN_LANES*5,
                       update_stages=5, training_agent_step_batches=r.HORIZON*5,
                       evaluation_steps=r.EVAL_LANES*r.HORIZON, evaluation_episodes=r.EVAL_LANES,
                       evaluation_agent_step_batches=r.HORIZON)
    s["training_rows"] = [{"updated": True}] * 5
    s["evaluation_optimizer_calls"] = dict.fromkeys(r.NETWORKS, 0)
    s["evaluation"] = {"status": "complete", "after_update": 5, "episode_ids": list(range(r.EVAL_LANES)),
                       "lane_seeds": s["evaluation_lane_seeds"], "steps_per_lane": [r.HORIZON]*r.EVAL_LANES,
                       "completed_episodes": r.EVAL_LANES, "returns_U": list(returns),
                       "native_scores_J": (np.asarray(returns)*6/r.HORIZON).tolist()}
    for name, count, seed in (("learner_config", r.TRAIN_LANES, r.TRAIN_SEED), ("evaluation_config", r.EVAL_LANES, r.EVAL_SEED)):
        s[name] = r.config_snapshot(r.make_config(arm, [Env(i, seed+i) for i in range(count)], seed))
    return s


def test_full_size_primary_scaling_pair_order_sd_and_se(monkeypatch):
    monkeypatch.setattr(r, "HORIZON", 500)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    u0 = np.arange(32, dtype=np.float64) + 2
    ui = u0 + np.linspace(-2., 4., 32)
    treatment, control = completed("I", ui), completed("D0", u0)
    result = r.assemble_pair(treatment, control)
    expected = 6 * (ui-u0) / 500
    primary = result["i_minus_d0"]
    np.testing.assert_allclose(primary["differences"], expected)
    assert primary["mean"] == pytest.approx(expected.mean())
    assert primary["sample_sd"] == pytest.approx(expected.std(ddof=1))
    assert primary["conditional_se"] == pytest.approx(expected.std(ddof=1)/np.sqrt(32))
    assert result["episode_ids"] == list(range(32)) and result["independent_training_pairs"] == 1
    control["launch_sha"] = "different-document-descendant"
    assert r.assemble_pair(treatment, control) == result  # Reported SHA is not a pair gate.


@pytest.mark.parametrize("delta,reading", [(.02,"above_mei"), (.01,"small_or_resolution_limited"),
    (0.,"small_or_resolution_limited"), (-.01,"small_or_resolution_limited"), (-.02,"opposite_sign")])
def test_inclusive_native_mei(monkeypatch, delta, reading):
    monkeypatch.setattr(r, "HORIZON", 500)
    treatment = completed("I", [delta * 500 / 6] * r.EVAL_LANES)
    control = completed("D0", [0.] * r.EVAL_LANES)
    assert r.assemble_pair(treatment, control)["card_reading"] == reading


@pytest.mark.parametrize("damage", ["arm", "object", "seed", "config", "evaluation_config", "endpoint_ids", "endpoint_seed",
    "short_learning", "checkpoint", "nonfinite", "wrong_scaling", "short_endpoint"])
def test_damaged_companion_never_supplies_polarity(damage):
    i, d0 = completed("I", [1.] * 3), completed("D0", [.5] * 3)
    if damage == "arm": d0["arm"] = "off"
    elif damage == "object": d0["object_id"] = "old"
    elif damage == "seed": d0["training_seed"] = 1
    elif damage == "config": d0["learner_config"]["interruption_cost_c"] = .25
    elif damage == "evaluation_config": d0["evaluation_config"]["interruption_cost_c_Z"] = .25
    elif damage == "endpoint_ids": d0["evaluation"]["episode_ids"] = [2, 1, 0]
    elif damage == "endpoint_seed": d0["evaluation"]["lane_seeds"] = [1, 2, 3]
    elif damage == "short_learning": d0["counts"]["update_stages"] = 4
    elif damage == "checkpoint": d0["counts"]["checkpoint_loads"] = 1
    elif damage == "nonfinite": d0["evaluation"]["native_scores_J"][0] = float("nan")
    elif damage == "wrong_scaling": d0["evaluation"]["native_scores_J"][0] = 1.
    else: d0["evaluation"]["steps_per_lane"][0] = 9
    with pytest.raises(ValueError):
        r.assemble_pair(i, d0)


def test_main_complete_pair_and_missing_d0_preserves_i(tmp_path):
    assert r.main(argv("D0", tmp_path / "D0")) == 0
    assert r.main(argv("I", tmp_path / "I", "--d0-summary", tmp_path / "D0/summary.json")) == 0
    result = json.loads((tmp_path / "I/summary.json").read_text())
    assert result["status"] == result["pair"]["status"] == "complete"
    assert result["pair"]["card_reading"] == "small_or_resolution_limited"
    assert result["counts"]["model_constructions"] == 2
    assert (tmp_path / "I/manifest.json").exists() and len((tmp_path / "I/training.jsonl").read_text().splitlines()) == 5
    assert len(Agent.constructed) == 4
    assert r.main(argv("I", tmp_path / "missing", "--d0-summary", tmp_path / "absent.json")) == 1
    missing = json.loads((tmp_path / "missing/summary.json").read_text())
    assert missing["status"] == missing["evaluation"]["status"] == "complete"
    assert missing["pair"]["status"] == "incomplete" and "card_reading" not in missing["pair"]


@pytest.mark.parametrize("stage", ["action", "loss", "primary", "parameters"])
def test_nonfinite_failure_is_readable_with_true_counts(monkeypatch, tmp_path, stage):
    if stage == "action":
        original = Agent.step
        def step(self, *args, **kwargs):
            actions, infos, data = original(self, *args, **kwargs)
            actions[0, 0, 0] = np.nan
            return actions, infos, data
        monkeypatch.setattr(Agent, "step", step)
    elif stage == "loss":
        original = Agent.update
        def update(self, **kwargs):
            original(self, **kwargs)
            return {"loss": float("inf")}
        monkeypatch.setattr(Agent, "update", update)
    elif stage == "primary":
        original = Env.step
        def step(self, actions):
            obs, reward, term, trunc, info = original(self, actions)
            return obs, float("inf") if self.seed >= 780503 else reward, term, trunc, info
        monkeypatch.setattr(Env, "step", step)
    else:
        original = r.e0._exposure_line
        def exposure(*args):
            result = original(*args)
            result["coordinator"] = float("nan")
            return result
        monkeypatch.setattr(r.e0, "_exposure_line", exposure)
    assert r.main(argv("I", tmp_path)) == 1
    result = json.loads((tmp_path / "summary.json").read_text())
    assert result["status"] == "incomplete" and "nonfinite" in result["failure"]
    assert "pair" not in result and result["learner_config"]["interruption_cost_c_Z"] == "Infinity"
    if stage == "action":
        assert result["counts"]["training_agent_step_batches"] == 1 and result["counts"]["training_transitions"] == 0
        assert result["counts"]["model_constructions"] == 1
    elif stage == "primary":
        assert result["counts"]["update_stages"] == 5 and result["counts"]["evaluation_steps"] == 1
        assert result["evaluation"]["returns_U"] is None and result["evaluation"]["native_scores_J"] is None
    else:
        assert result["counts"]["update_stages"] == 1 and result["counts"]["stored_training_transitions"] == 20
        assert result["optimizer_calls"] == dict(zip(r.NETWORKS, range(5)))
        assert result["counts"]["model_constructions"] == 1  # No rescue endpoint.


@pytest.mark.parametrize("arm,cap", [("D0", 3600), ("I", 18000)])
def test_cap_covers_closed_file_publication(monkeypatch, tmp_path, arm, cap):
    clock = SimpleNamespace(now=cap-.1)
    monkeypatch.setattr(r, "PROCESS_START", 0)
    monkeypatch.setattr(r.time, "perf_counter", lambda: clock.now)
    summary = r.base_summary(arm)
    assert summary["cap_seconds"] == cap and summary["summed_pair_cap_seconds"] == 21600
    original = r.write_json
    def write(*args):
        original(*args)
        clock.now = cap
    monkeypatch.setattr(r, "write_json", write)
    with pytest.raises(TimeoutError, match="published"):
        r.publish(tmp_path, summary, "final")
    assert (tmp_path / "summary.json").exists()


def test_fixed_cli_rejects_extra_scientific_parameters_before_creation(tmp_path):
    for args in (argv("off", tmp_path / "off"), argv("I", tmp_path / "seed", "--seed", "770503"),
                 argv("D0", tmp_path / "d0", "--d0-summary", "anything")):
        with pytest.raises(SystemExit) as exc:
            r.main(args)
        assert exc.value.code == 2
    assert not list(tmp_path.iterdir()) and not Agent.constructed


def test_runner_size_and_clock_boundary():
    source = Path(r.__file__).read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 600
    assert source.index("PROCESS_START =") < source.index("import numpy")
    assert "complete-command timeouts" in r.__doc__
