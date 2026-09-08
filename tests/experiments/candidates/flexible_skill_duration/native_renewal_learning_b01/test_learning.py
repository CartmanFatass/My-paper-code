"""Synthetic production-boundary tests; never instantiate a scientific model or host."""
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
SPEC = importlib.util.spec_from_file_location("fsd_b01", ROOT / "scripts/run_fsd_native_renewal_learning_b01.py")
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Corridor:
    horizon, n_roles, delta = 3, 2, 1.
    n_z = low_level_action_dim = 2

    def parameter_record(self):
        return {"H": self.horizon, "N": 2, "delta": self.delta}


class Adapter:
    n_agents, obs_dim, state_dim = 2, 1, 1

    def __init__(self, config=None, *, num_envs=2, master_seed=0, episode_ids=None, **kw):
        self.config = config or Corridor()
        self.num_envs, self.master_seed = num_envs, master_seed
        self.ids = list(range(num_envs)) if episode_ids is None else list(episode_ids)
        self.resets, self.applied, self.actions, self.events = 0, [], [], []
        self.applied_refs = []
        self.host = SimpleNamespace(change_flag=np.zeros((num_envs, 2), dtype=int), region_of_agent=np.arange(2))

    def episode_ids(self):
        return tuple(self.ids)

    def advance_episode_ids(self):
        self.events.append("advance")
        self.ids = [i + self.num_envs for i in self.ids]

    def reset(self):
        self.events.append("reset")
        self.resets += 1
        self.t = 0
        self.host.change_flag[:] = 0
        return np.full((self.num_envs, 2, 1), 10. + self.resets), {"state": np.full((self.num_envs, 1), 100. + self.resets)}

    def step(self, actions, renew_mask):
        self.events.append("host")
        self.actions.append(actions)
        self.applied.append(renew_mask.copy())
        self.applied_refs.append(renew_mask)
        # Native values differ under C and H; never use the returned reward placeholder.
        reward = np.asarray(renew_mask[:, 0] * .25 + renew_mask[:, 1] * .5 + self.t * .125, dtype=np.float64)
        self.t += 1
        self.host.change_flag[:] = [0, 1] if self.t == 1 else [1, 0]
        term = self.t == self.config.horizon
        return np.full((self.num_envs, 2, 1), 800. + self.t), -999, term, False, {
            "state": np.full((self.num_envs, 1), 900. + self.t), "shared_reward": reward,
            "renew_mask": renew_mask.copy(), "lease_fresh": np.ones((self.num_envs, 2), bool),
            "role_correct": np.broadcast_to([True, False], (self.num_envs, 2)).copy()}


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
        return {"values": [value.clone() for value in self.values]}

    def load_state_dict(self, state):
        self.values = [value.clone() for value in state["values"]]


class Optimizer:
    def __init__(self, parameters):
        self.parameters = parameters
        self.calls = 0

    def step(self):
        self.calls += 1
        for parameter in self.parameters:
            parameter.add_(.25)


class Agent:
    constructed = []

    def __init__(self, config=None, **kw):
        random.random(), np.random.rand(), torch.rand(1)  # Construction must be inside preserved RNG.
        self.config = config or SimpleNamespace(num_envs=2)
        self.threads = torch.get_num_threads()
        self.skill_coordinator, self.skill_discoverer = Module(1), Module(3)
        self.team_discriminator, self.individual_discriminator = Module(5), Module(7)
        self.obs_norm, self.state_norm = SimpleNamespace(mean=np.array([9.])), SimpleNamespace(mean=np.array([10.]))
        self.value_norm_coordinator = SimpleNamespace(mean=np.array([11.]), var=np.array([12.]), count=13.)
        self.value_norm_discoverer = SimpleNamespace(mean=np.array([14.]), var=np.array([15.]), count=16.)
        for name, params in r.e0._parameter_groups(self).items():
            setattr(self, name + "_optimizer", Optimizer(params))
        self.inputs, self.stored, self.data, self.actions, self.events = [], [], [], [], []
        self.updates, self.reset_calls, self.training = 0, [], True
        self.d2_metrics = {"segment_lengths_agent": [], "segment_lengths_team": []}
        self.constructed.append(self)

    def train(self, mode):
        self.training = mode

    def clear_buffers(self):
        self.events.append("clear")
        self.d2_metrics = {"segment_lengths_agent": [], "segment_lengths_team": []}

    def reset_env_state(self, lane):
        self.events.append("reset_lane")
        self.reset_calls.append(lane)

    def step(self, states, observations, env_steps, dones, **kw):
        self.events.append("step")
        if not self.training:
            assert not torch.is_grad_enabled()
            assert kw["deterministic"] is True
            random.random(), np.random.rand(), torch.rand(1)
        else:
            assert kw["deterministic"] is False
        self.inputs.append((states.copy(), observations.copy(), env_steps.copy(), dones.copy(), self.updates))
        lanes = len(states)
        internal = np.broadcast_to([True, False], (lanes, 2)).copy()
        internal[np.asarray(env_steps) == 0] = True
        data = {"d2_sampled_mask": internal, "credit_metadata": np.array([31.])}
        actions = np.full((lanes, 2, 2), float(self.updates), dtype=np.float32)
        self.data.append(data)
        self.actions.append(actions)
        return actions, None, data

    def store_transition_batch(self, **kw):
        self.events.append("store")
        assert kw["step_data"] is self.data[-1]
        assert kw["actions"] is self.actions[-1]
        self.stored.append(copy.deepcopy(kw))
        if np.any(kw["dones"]):
            self.d2_metrics = {"segment_lengths_agent": [1, 2, 3, 3], "segment_lengths_team": [3, 3]}

    def update(self, **kw):
        self.events.append("update")
        assert kw["steps_in_buffer"] == 3
        assert kw["dones"].all() and not kw["last_values"].any()
        np.testing.assert_array_equal(kw["last_state"], self.stored[-1]["next_states"] * 0 + 102 + self.updates)
        np.testing.assert_array_equal(kw["last_observations"], self.stored[-1]["next_observations"] * 0 + 12 + self.updates)
        self.updates += 1
        # Deliberately unequal actual calls, including an observed zero network.
        for index, name in enumerate(r.NETWORKS):
            for _ in range(index):
                getattr(self, name + "_optimizer").step()
        return {"loss": .5}

    def get_d2_metrics(self):
        self.events.append("metrics")
        assert self.d2_metrics["segment_lengths_agent"]
        return {"rows_M_agent": 4, "rows_M_team": 2, "rows_M": 6, "coordinator_inference_calls": 3}


@pytest.fixture(autouse=True)
def no_scientific_construction(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("real scientific construction forbidden in this suite")
    import hmasd.agent
    import envs.relay_corridor.host
    monkeypatch.setattr(hmasd.agent, "HMASDAgent", forbidden)
    monkeypatch.setattr(envs.relay_corridor.host, "RelayCorridorHost", forbidden)
    monkeypatch.setattr(r, "HMASDAgent", forbidden)
    monkeypatch.setattr(r, "RelayCorridorAdapter", forbidden)
    monkeypatch.setattr(r, "TRAIN_LANES", 2)
    monkeypatch.setattr(r, "EVAL_LANES", 2)
    Agent.constructed = []


def setup_training(tmp_path, policy="H"):
    adapter, agent = Adapter(), Agent()
    summary = r.base_summary(policy, adapter.config, "source")
    counters = {name: r.e0._StepCounter(getattr(agent, name + "_optimizer")) for name in r.NETWORKS}
    return adapter, agent, summary, r.e0._capture_theta0(agent), counters


@pytest.mark.parametrize("policy", ["C", "H"])
def test_real_collector_native_storage_reset_update_and_exposure(tmp_path, policy):
    adapter, agent, summary, theta0, counters = setup_training(tmp_path, policy)
    r.collect_training(policy, adapter, agent, summary, theta0, counters, tmp_path, r.time.perf_counter())
    assert adapter.resets == 6
    assert agent.reset_calls == [0, 1] * 5  # No extra internal reset at public renewal.
    for rollout in range(5):
        offset = 3 * rollout
        np.testing.assert_array_equal(adapter.applied[offset], [[True, True]] * 2)
        np.testing.assert_array_equal(adapter.applied[offset + 1], [[False, True] if policy == "H" else [True, False]] * 2)
        for t in range(3):
            stored = agent.stored[offset + t]
            mask = adapter.applied[offset + t]
            np.testing.assert_array_equal(stored["rewards"], mask[:, 0] * .25 + mask[:, 1] * .5 + t * .125)
            assert not np.shares_memory(adapter.applied_refs[offset + t], agent.data[offset + t]["d2_sampled_mask"])
            assert stored["rewards"].dtype == np.float64
            assert stored["rollout_step_idx"] == t
            np.testing.assert_array_equal(stored["step_data"]["d2_sampled_mask"], [[True, True] if t == 0 else [True, False]] * 2)
        terminal = agent.stored[offset + 2]
        assert (terminal["next_states"] == 903).all() and (terminal["next_observations"] == 803).all()
        state, obs, steps, dones, updated = agent.inputs[offset]
        assert (state == 101 + rollout).all() and (obs == 11 + rollout).all()
        assert not steps.any() and updated == rollout
        assert bool(dones.all()) == (rollout > 0)
        row = summary["training_rows"][rollout]
        assert row["episode_ids"] == [2 * rollout, 2 * rollout + 1]
        assert row["segments"]["agent"] == {"count": 4, "total_length": 9, "min": 1, "max": 3, "mean": 2.25}
        assert row["d2_metrics"]["rows_M"] == 6
        assert row["optimizer_calls_delta"] == dict(zip(r.NETWORKS, range(5)))
        assert row["optimizer_calls_total"] == {name: index * (rollout + 1) for index, name in enumerate(r.NETWORKS)}
        assert row["relative_initialization_displacement"]["coordinator"] == 0.
        assert row["relative_initialization_displacement"]["discoverer_actor"] > 0.
    assert [x for x in agent.events if x in ("update", "metrics", "clear")] == ["update", "metrics", "clear"] * 5
    assert summary["counts"]["training_transitions"] == 30
    assert summary["counts"]["training_episodes"] == 10
    assert summary["counts"]["update_stages"] == 5
    assert json.loads((tmp_path / "summary.json").read_text())["training_rows"][-1]["updated"]


def test_build_uses_real_config_builder_and_four_threads_before_fake_model(monkeypatch, tmp_path):
    monkeypatch.setattr(r, "RelayCorridorAdapter", Adapter)
    monkeypatch.setattr(r, "HMASDAgent", Agent)
    corridor = r.proposal_config("large")  # Config only, no scientific host.
    summary = r.base_summary("H", corridor, "source")
    adapter, agent, overrides, theta0, counters = r.build_learner(corridor, tmp_path, summary, r.time.perf_counter())
    cfg = agent.config
    assert agent.threads == 4
    assert (cfg.n_Z, cfg.n_z, cfg.action_dim, cfg.gamma, cfg.gae_lambda) == (6, 2, 2, .99, .95)
    assert cfg.ppo_epochs == 15 and cfg.num_mini_batch == 4
    assert cfg.use_valuenorm and not cfg.use_obsnorm and not cfg.use_statenorm
    assert cfg.policy_interruption_mode == "d2" and cfg.skill_cap_k_max == 40 and cfg.team_cap_k_Z == 400
    assert cfg.interruption_cost_c == cfg.interruption_cost_c_Z == .25
    assert cfg.age_feature == "off" and adapter.master_seed == r.SEED
    assert summary["counts"]["model_constructions"] == 1
    assert summary["initial_parameter_norms"]["coordinator"] == pytest.approx(np.sqrt(5))
    assert all(counter.count == 0 for counter in counters.values())


def rng_state():
    return random.getstate(), copy.deepcopy(np.random.get_state()), torch.get_rng_state().clone()


def assert_rng_equal(a, b):
    assert a[0] == b[0]
    assert a[1][0] == b[1][0] and a[1][2:] == b[1][2:]
    np.testing.assert_array_equal(a[1][1], b[1][1])
    assert torch.equal(a[2], b[2])


def test_actual_e2_constructor_sync_reset_and_rng_isolation(monkeypatch, tmp_path):
    import run_flexible_skill_duration_e2 as e2
    monkeypatch.setattr(e2, "RelayCorridorAdapter", Adapter)
    monkeypatch.setattr(e2, "HMASDAgent", Agent)
    learner = Agent()
    learner.skill_coordinator.values[0].add_(20)
    learner.value_norm_coordinator.mean[:] = 44.
    learner.value_norm_discoverer.var[:] = 55.
    original = copy.deepcopy(learner.__dict__)
    summary = r.base_summary("H", Corridor(), "source")
    before = rng_state()
    r.final_evaluation("H", Corridor(), learner, r.arm_parameters("large", "d2", horizon=3), summary, tmp_path, r.time.perf_counter())
    assert_rng_equal(before, rng_state())
    evaluator = Agent.constructed[-1]
    assert evaluator is not learner and not evaluator.training
    assert evaluator.reset_calls == [0, 1] and evaluator.events[0] == "clear"
    assert evaluator.updates == 0 and learner.updates == 0
    assert learner.events == [] and learner.inputs == [] and learner.reset_calls == []
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
        for left, right in zip(getattr(learner, name).parameters(), getattr(evaluator, name).parameters()):
            assert torch.equal(left, right) and left.data_ptr() != right.data_ptr()
    for name in ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer"):
        left, right = getattr(learner, name), getattr(evaluator, name)
        assert left is not right
        np.testing.assert_array_equal(left.mean, right.mean)
        assert not np.shares_memory(left.mean, right.mean)
        np.testing.assert_array_equal(left.mean, original[name].mean)
    assert evaluator.value_norm_coordinator.mean[0] == 44
    assert evaluator.value_norm_discoverer.var[0] == 55
    assert summary["counts"]["model_constructions"] == 1
    assert summary["counts"]["evaluation_episodes"] == 2
    assert summary["evaluation"]["status"] == "complete"
    assert all(getattr(evaluator, name + "_optimizer").calls == 0 for name in r.NETWORKS)


def test_evaluation_measures_native_arrays_and_conditional_counts(tmp_path):
    adapter, agent = Adapter(), Agent()
    summary = r.base_summary("H", adapter.config, "source")
    def reset():
        agent.clear_buffers()
        for lane in range(2):
            agent.reset_env_state(lane)
    r.evaluate("H", adapter, agent, summary, tmp_path, r.time.perf_counter(), reset)
    result = summary["evaluation"]
    # Rewards [.75, .625, .5], full 5/8, post 9/16. H applied [TT,FT,TF].
    np.testing.assert_allclose(result["return_full"], [5 / 8] * 2)
    np.testing.assert_allclose(result["return_post"], [9 / 16] * 2)
    assert result["eligible_full"] == [2, 2] and result["wrong_full"] == [1, 1]
    assert result["pooled_post"] == {"wrong": 2, "eligible": 4, "wrong_rate": .5}
    assert result["wrong_rate_post"] == [.5, .5]
    assert result["role_loss_full"] == [1 / 6] * 2 and result["role_loss_post"] == [.25] * 2
    assert result["internal_renew_full"] == [4, 4] and result["applied_renew_post"] == [2, 2]
    assert not agent.stored and not agent.updates


def arm(policy, values=(.2, .4), post=(.3, .5)):
    result = r.base_summary(policy, Corridor(), "source")
    result["status"] = "complete"
    result["counts"].update(update_stages=5, training_transitions=30)
    result["training_rows"] = [{"updated": True}] * 5
    result["evaluation"] = {"status": "complete", "episode_ids": [0, 1],
                            "valid_reward_steps_per_lane": 3, "completed_episodes": 2,
                            "return_full": list(values), "return_post": list(post),
                            "role_loss_full": [.1, .2], "role_loss_post": [.2, .3]}
    return result


def test_pair_sign_se_reference_gaps_and_missing_dependencies():
    h, c, g = arm("H", (.5, .9)), arm("C"), arm("G", (.8, 1.))
    result = r.summarize_panel(h, c, g)
    pair = result["paired"]["h_minus_c_full"]
    np.testing.assert_allclose(pair["differences"], [.3, .5])
    assert pair["mean"] == pytest.approx(.4) and pair["stderr"] == pytest.approx(.1)
    assert result["paired"]["g_minus_h_full"]["mean"] == pytest.approx(.2)
    assert result["paired"]["g_minus_c_full"]["mean"] == pytest.approx(.6)
    assert result["g_minus_h_less_h_role_loss_full"]["mean"] == pytest.approx(.05)
    assert result["card_reading"] == "above_mei"
    assert r.summarize_panel(h, c)["reference_status"] == "incomplete"
    g["evaluation"]["return_full"][0] = float("nan")
    assert r.summarize_panel(h, c, g)["status"] == "complete"
    c["counts"]["update_stages"] = 4
    with pytest.raises(ValueError, match="learning"):
        r.summarize_panel(h, c)
    c = arm("C")
    c["evaluation"]["return_full"][0] = float("nan")
    with pytest.raises(ValueError, match="primary"):
        r.summarize_panel(h, c)
    assert r.summarize_panel(arm("H", (-.2, -.4)), arm("C"))["card_reading"] == "opposite_sign"
    assert r.summarize_panel(arm("H"), arm("C"))["card_reading"] == "small_or_resolution_limited"


def test_zero_opportunities_are_null_and_g_constructs_no_learner(tmp_path):
    class Greedy:
        def reset(self, host):
            pass
        def act(self, host, t):
            return np.zeros((2, 2), dtype=int), np.ones((2, 2), dtype=bool)
    summary = r.base_summary("G", Corridor(), "source")
    r.evaluate("G", Adapter(), Greedy(), summary, tmp_path, r.time.perf_counter())
    assert summary["counts"]["model_constructions"] == 0
    result = summary["evaluation"]
    assert result["wrong_rate_full"] == [None, None]
    assert result["pooled_post"] == {"wrong": 0, "eligible": 0, "wrong_rate": None}
    assert result["internal_renew_full"] is None


@pytest.mark.parametrize("where", ["collection", "update", "evaluation", "publication", "setup"])
def test_deadline_at_actual_boundaries(monkeypatch, tmp_path, where):
    clock = SimpleNamespace(now=0.)
    monkeypatch.setattr(r.time, "perf_counter", lambda: clock.now)
    adapter, agent, summary, theta0, counters = setup_training(tmp_path)
    if where == "collection":
        original = agent.store_transition_batch
        def store(**kw):
            original(**kw)
            if len(agent.stored) == 2:
                clock.now = 901
        monkeypatch.setattr(agent, "store_transition_batch", store)
        with pytest.raises(TimeoutError):
            r.collect_training("H", adapter, agent, summary, theta0, counters, tmp_path, 0)
        row = summary["training_rows"][0]
        assert row["transitions"] == 4 and row["native_return"] is None and not row["updated"]
        assert summary["counts"]["update_stages"] == 0
    elif where == "update":
        original = agent.update
        def update(**kw):
            result = original(**kw)
            clock.now = 901
            return result
        monkeypatch.setattr(agent, "update", update)
        with pytest.raises(TimeoutError):
            r.collect_training("H", adapter, agent, summary, theta0, counters, tmp_path, 0)
        assert summary["counts"]["update_stages"] == 1
        assert summary["optimizer_calls"]["individual_discriminator"] == 4
        assert "clear" not in agent.events
    elif where == "evaluation":
        original = adapter.step
        def step(*args, **kw):
            result = original(*args, **kw)
            clock.now = 901
            return result
        monkeypatch.setattr(adapter, "step", step)
        with pytest.raises(TimeoutError):
            r.evaluate("H", adapter, agent, summary, tmp_path, 0, lambda: None)
        assert summary["evaluation"]["steps_per_lane"] == 1
        assert summary["evaluation"]["return_full"] is None
        assert summary["evaluation"]["completed_episodes"] == 0
    elif where == "publication":
        monkeypatch.setattr(r, "write_summary", lambda *a: setattr(clock, "now", 901))
        with pytest.raises(TimeoutError, match="published"):
            r.publish(tmp_path, summary, 0, "final")
    else:
        clock.now = 901
        with pytest.raises(TimeoutError, match="setup"):
            r.build_learner(Corridor(), tmp_path, summary, 0)
        assert summary["counts"]["model_constructions"] == 0


def test_nonfinite_primary_stops_and_retains_true_denominator(monkeypatch, tmp_path):
    adapter, agent = Adapter(), Agent()
    original = adapter.step
    def step(*args, **kw):
        result = original(*args, **kw)
        if adapter.t == 2:
            result[-1]["shared_reward"][0] = np.nan
        return result
    monkeypatch.setattr(adapter, "step", step)
    summary = r.base_summary("H", Corridor(), "source")
    with pytest.raises(ValueError, match="nonfinite evaluation native reward"):
        r.evaluate("H", adapter, agent, summary, tmp_path, r.time.perf_counter(), lambda: None)
    result = summary["evaluation"]
    assert result["steps_per_lane"] == 2 and result["valid_reward_steps_per_lane"] == 1
    assert result["return_full"] is None and result["status"] == "incomplete"
    assert result["partial_sums"]["return"] == [[.75, .75], [0., 0.]]
    json.dumps(summary, allow_nan=False)


def test_clock_precedes_heavy_imports_and_complete_timeout_is_documented():
    source = Path(r.__file__).read_text(encoding="utf-8")
    assert source.index("PROCESS_START =") < source.index("import numpy") < source.index("import torch")
    assert "complete-command OS timeout" in r.__doc__
    assert "900 s C/H, 60 s G" in r.__doc__
    assert len(source.splitlines()) <= 600


def patch_main(monkeypatch):
    import run_flexible_skill_duration_e2 as e2
    monkeypatch.setattr(r, "HMASDAgent", Agent)
    monkeypatch.setattr(r, "RelayCorridorAdapter", Adapter)
    monkeypatch.setattr(e2, "HMASDAgent", Agent)
    monkeypatch.setattr(e2, "RelayCorridorAdapter", Adapter)
    monkeypatch.setattr(r, "proposal_config", lambda row: Corridor())
    original_parameters = r.arm_parameters
    monkeypatch.setattr(r, "arm_parameters", lambda row, arm: original_parameters(row, arm, horizon=3))
    class Greedy:
        def reset(self, host):
            pass
        def act(self, host, t):
            return np.zeros((2, 2), dtype=int), np.ones((2, 2), dtype=bool)
    monkeypatch.setattr(r, "GreedyOnPublicState", Greedy)


def invocation(policy, out, *extra):
    return ["--policy", policy, "--seed", str(r.SEED), "--launch-sha", "synthetic-source",
            "--out", str(out), *map(str, extra)]


def test_main_synthetic_panel_and_missing_companion_preserve_arm(monkeypatch, tmp_path):
    patch_main(monkeypatch)
    for policy in ("G", "C", "H"):
        extra = [] if policy != "H" else ["--c-summary", tmp_path / "C/summary.json", "--g-summary", tmp_path / "G/summary.json"]
        assert r.main(invocation(policy, tmp_path / policy, *extra)) == 0
    summary = json.loads((tmp_path / "H/summary.json").read_text())
    assert summary["status"] == "complete" and summary["panel"]["status"] == "complete"
    assert summary["panel"]["reference_status"] == "complete"
    assert summary["counts"]["model_constructions"] == 2
    assert summary["counts"]["training_starts"] == 1
    assert not any(summary["evaluation_optimizer_calls"].values())
    assert summary["training_rows"][4]["episode_ids"] == [8, 9]
    # Missing C affects the pair, not the independently collected H endpoint.
    assert r.main(invocation("H", tmp_path / "missing", "--c-summary", tmp_path / "absent.json")) == 1
    missing = json.loads((tmp_path / "missing/summary.json").read_text())
    assert missing["status"] == "complete" and missing["panel"]["status"] == "incomplete"
    assert "card_reading" not in missing["panel"]
    assert missing["evaluation"]["status"] == "complete"


@pytest.mark.parametrize("stage", ["initial_norms", "d2_metrics"])
def test_main_nonfinite_diagnostics_leave_readable_failure_and_counts(monkeypatch, tmp_path, stage):
    patch_main(monkeypatch)
    if stage == "initial_norms":
        original = r.e0._capture_theta0
        def capture(agent):
            data = original(agent)
            data["coordinator"]["norm"] = float("nan")
            return data
        monkeypatch.setattr(r.e0, "_capture_theta0", capture)
    else:
        original = Agent.get_d2_metrics
        def metrics(self):
            data = original(self)
            data["bad_metric"] = float("inf")
            return data
        monkeypatch.setattr(Agent, "get_d2_metrics", metrics)
    assert r.main(invocation("C", tmp_path)) == 1
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["status"] == "incomplete" and "nonfinite" in summary["failure"]
    assert summary["counts"]["model_constructions"] == 1
    if stage == "initial_norms":
        assert summary["initial_parameter_norms"] == {} and summary["counts"]["training_transitions"] == 0
    else:
        assert summary["counts"]["training_transitions"] == 6
        assert summary["counts"]["update_stages"] == 1
        assert summary["optimizer_calls"]["individual_discriminator"] == 4
        assert "d2_metrics" not in summary["training_rows"][0]


def test_interrupted_or_nonfinite_write_keeps_previous_completed_summary(monkeypatch, tmp_path):
    r.write_summary(tmp_path, {"transitions": 6})
    with pytest.raises(ValueError):
        r.write_summary(tmp_path, {"transitions": 8, "bad": float("nan")})
    assert json.loads((tmp_path / "summary.json").read_text()) == {"transitions": 6}
    def interrupted(data, stream, **kw):
        stream.write('{"transitions":')
        raise OSError("publication interrupted")
    monkeypatch.setattr(r.json, "dump", interrupted)
    with pytest.raises(OSError):
        r.write_summary(tmp_path, {"transitions": 10})
    assert json.loads((tmp_path / "summary.json").read_text()) == {"transitions": 6}
