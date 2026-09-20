"""The label-content entry: the construction, the execution rules, the measures and `reduce`.

Fake learners, fake hosts, a stub D2 agent and pure measure functions only (the real stack is in
`test_label_content_real_tiny.py`, because the fake-only helper forbids real construction). Two
checks read the actually recorded stage-1 D1280 configurations from
`runs/flexible_skill_duration/b01_s1_d1280_<block>_a01/summary.json`. Technical checks: nothing here
asserts the direction or the size of any measured quantity.
"""
import copy
import importlib.util
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_label_content_helpers",
    Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_label_content_b08 as label  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402  (class constants only; never constructed here)
from hmasd.r_mappo_utils import DiagGaussian  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(label.BLOCKS)
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}
STATE_DIM, OBS_DIM = 119, 104  # Scenario 1's own widths, so the recorded comparison is real
N_UAVS, N_USERS, AREA, HEIGHTS = 6, 50, 1000., (50., 150.)
# Exact dyadic offsets from the block base, per arm and block; every panel of a fit carries them.
# `D_SAVE` carries the D1280 reference's own scores, which is the bit-identical case.
OFFSET = {"D1280": [0., 0., 0.], "D_SAVE": [0., 0., 0.]}


def lanes(count):
    return [SimpleNamespace(state_dim=STATE_DIM, obs_dim=OBS_DIM) for _ in range(count)]


# ---------------------------------------------------------------------------
# the construction: the recorded D1280 one, with nothing moved
# ---------------------------------------------------------------------------


def test_the_construction_is_the_recorded_d1280_fit_on_every_block():
    """Environment-free, both phases, all three blocks, against the published stage-1 fits."""
    label.bind()
    snapshot = production_shared.config_snapshot
    for seed in SEEDS:
        recorded = json.loads(label.RECORDED_FITS[seed].read_text(encoding="utf-8"))
        assert recorded["factorial_arm"] == "D1280" and recorded["status"] == "complete"
        learner = snapshot(b01.make_config(label.SAVE_ARM, lanes(16), seed))
        evaluation = snapshot(b01.make_config(label.SAVE_ARM, lanes(32), label.BLOCKS[seed]))
        assert label.config_differences(learner, recorded["learner_config"]) == {}
        assert label.config_differences(evaluation, recorded["evaluation_config"]) == {}
        assert learner["k"] == evaluation["k"] == label.SKILL_PERIOD
        assert learner["policy_interruption_mode"] == "d2"
        assert learner["n_Z"] == learner["n_z"] == 6
        assert learner["use_central_snapshot_in_flat_actor"] is False
        assert (learner["skill_cap_k_max"], learner["team_cap_k_Z"]) == label.ARM_CAPS
        assert (evaluation["skill_cap_k_max"], evaluation["team_cap_k_Z"]) == label.ARM_CAPS
        assert learner["coordinator_batch_size"] == label.ARMS[label.SAVE_ARM][1]
        assert learner["interruption_cost_c"] == learner["interruption_cost_c_Z"] == "Infinity"
    assert label.host_geometry() == label.probe.FROZEN_GEOMETRY
    assert label.ARM_OVERRIDES == {"D_SAVE": {}}
    assert label.ARMS[label.SAVE_ARM] == matched.ARMS["D1280"]  # the frozen D construction
    assert label.WALL_PLANS[label.SAVE_ARM] == matched.WALL_PLANS["D1280"]


def test_make_config_refuses_any_difference_from_the_d1280_construction(monkeypatch):
    label.bind()
    monkeypatch.setitem(label.ARM_OVERRIDES, label.SAVE_ARM, {"k": 5})
    with pytest.raises(ValueError, match="differs from the D1280 construction"):
        b01.make_config(label.SAVE_ARM, lanes(16), SEEDS[0])
    with pytest.raises(ValueError, match="unknown arm"):
        label.make_config("D_OTHER", lanes(16), SEEDS[0])


def test_the_recorded_comparison_exempts_the_host_geometry_only_on_a_shrunken_host(monkeypatch):
    label.bind()
    recorded = json.loads(label.RECORDED_FITS[SEEDS[0]].read_text(encoding="utf-8"))
    config = production_shared.config_snapshot(b01.make_config(label.SAVE_ARM, lanes(16), SEEDS[0]))
    assert label.require_recorded_construction(
        config, recorded["learner_config"], "learner_config") == {}
    for changed in (dict(config, lambda_l=.5), dict(config, num_envs=2),
                    dict(config, skill_cap_k_max=1)):
        with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
            label.require_recorded_construction(changed, recorded["learner_config"], "learner_config")
    monkeypatch.setattr(label.shared, "TRAIN_LANES", 2)
    assert label.host_geometry() != label.probe.FROZEN_GEOMETRY
    assert set(label.require_recorded_construction(
        dict(config, num_envs=2), recorded["learner_config"], "learner_config")) == {"num_envs"}
    with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
        label.require_recorded_construction(
            dict(config, lambda_l=.5), recorded["learner_config"], "learner_config")


def test_plan_guard_admits_exactly_the_three_planned_fits():
    for seed in SEEDS:
        label.plan_guard(label.SAVE_ARM, seed)
    for arm, seed in ((label.SAVE_ARM, 773103), ("D1280", SEEDS[0]), ("D_K10", SEEDS[0])):
        with pytest.raises(SystemExit):
            label.plan_guard(arm, seed)


# ---------------------------------------------------------------------------
# the execution rules, on a stub D2 agent whose cadence is the caps'
# ---------------------------------------------------------------------------


class StubD2Agent:
    """The decision cadence and the D2 masks of the real route, with no network at all.

    The coordinator's "choice" is a fixed pseudo-random label per decision, drawn from this stub's
    own generator, so a rule that replaces nothing reproduces it exactly and a rule that replaces
    everything is visible.
    """

    D2_CAUSE_NONE = HMASDAgent.D2_CAUSE_NONE
    D2_CAUSE_RESET = HMASDAgent.D2_CAUSE_RESET
    D2_CAUSE_TEAM_CAP = HMASDAgent.D2_CAUSE_TEAM_CAP

    def __init__(self, lanes=2, n_agents=3, n_Z=4, n_z=6, period=10, seed=11):
        self.config = SimpleNamespace(n_Z=n_Z, n_z=n_z, n_agents=n_agents)
        self.lanes, self.n_agents = lanes, n_agents
        self.d2_enabled = True
        self.d2_cost_c = self.d2_cost_c_Z = float("inf")
        self.d2_k_max = self.d2_k_Z = period
        self.env_team_skills, self.env_agent_skills = {}, {}
        self._d2_last_step = None
        self.choices = np.random.default_rng(seed)
        self.step_index = 0
        self.decisions = 0

    def _batched_assign_skills(self, *args, **kwargs):
        step = self.step_index
        self.step_index += 1
        reset = step == 0
        decision = reset or (step % int(self.d2_k_Z) == 0)
        self.decisions += int(decision)
        held_team = np.array([self.env_team_skills.get(i, 0) for i in range(self.lanes)],
                             dtype=np.int64)
        held_agents = np.stack([
            np.asarray(self.env_agent_skills.get(i, np.zeros(self.n_agents, dtype=np.int64)),
                       dtype=np.int64) for i in range(self.lanes)])
        if decision:
            team = self.choices.integers(0, self.config.n_Z, size=self.lanes)
            agents = self.choices.integers(0, self.config.n_z, size=(self.lanes, self.n_agents))
        else:
            team, agents = held_team.copy(), held_agents.copy()
        mask = np.full((self.lanes, self.n_agents), decision, dtype=bool)
        cause = self.D2_CAUSE_RESET if reset else (
            self.D2_CAUSE_TEAM_CAP if decision else self.D2_CAUSE_NONE)
        self._d2_last_step = {
            "decision": np.full(self.lanes, decision, dtype=bool),
            "team_decision": np.full(self.lanes, decision, dtype=bool),
            "sampled_mask": mask, "sample_Z": np.full(self.lanes, decision, dtype=bool),
            "team_cause": np.full(self.lanes, cause, dtype=np.int64),
            "agent_cause": np.full((self.lanes, self.n_agents), cause, dtype=np.int64)}
        for lane in range(self.lanes):
            self.env_team_skills[lane] = int(team[lane])
            self.env_agent_skills[lane] = agents[lane].copy()
        return team, agents, [{} for _ in range(self.lanes)]


def run_stub_panel(rule, agent, steps):
    executed = []
    with rule.attached():
        for _ in range(steps):
            team, agents, _ = agent._batched_assign_skills()
            executed.append((team.copy(), agents.copy()))
    return executed


def rule_for(name, agent, evaluation_seed=782803):
    generator = (label.label_generator(evaluation_seed, name)
                 if name in ("uniform_every_step", "uniform_every_10") else None)
    return label.ExecutionRule(name, agent, generator=generator, horizon=100)


def test_as_trained_replaces_nothing_and_only_records():
    agent = StubD2Agent(period=10)
    plain = StubD2Agent(period=10)  # the same generator seed, so the same coordinator choices
    rule = rule_for("as_trained", agent)
    executed = run_stub_panel(rule, agent, 30)
    reference = [plain._batched_assign_skills()[:2] for _ in range(30)]
    for (team, agents), (other_team, other_agents) in zip(executed, reference):
        assert team.tolist() == other_team.tolist()
        assert agents.tolist() == other_agents.tolist()
    measures = rule.measures()
    assert measures["caps_applied"] == {} and measures["steps_recorded"] == 30
    assert measures["reset_rows"] == agent.lanes
    assert sum(measures["agent_label_histogram"]) == 30 * agent.lanes * agent.n_agents
    assert sum(measures["team_label_histogram"]) == 30 * agent.lanes
    assert measures["agent_label_comparisons"] == 29 * agent.lanes * agent.n_agents
    assert "run_fsd_label_content_b08.py:" in measures["attached_at"]
    # the wrapper is an instance attribute and it is gone
    assert "_batched_assign_skills" not in agent.__dict__
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)


def test_frozen_episode_holds_the_reset_labels_for_the_whole_episode():
    agent = StubD2Agent(period=10)
    rule = rule_for("frozen_episode", agent)
    executed = run_stub_panel(rule, agent, 30)
    first_team, first_agents = executed[0]
    for team, agents in executed:
        assert team.tolist() == first_team.tolist()
        assert agents.tolist() == first_agents.tolist()
    measures = rule.measures()
    assert measures["agent_label_change_fraction"] == 0.
    assert measures["team_label_change_fraction"] == 0.
    assert measures["caps_applied"] == {}
    # the executed label is also the label the agent now holds
    assert agent.env_team_skills[0] == int(first_team[0])
    assert agent.env_agent_skills[0].tolist() == first_agents[0].tolist()
    assert "_batched_assign_skills" not in agent.__dict__


def test_uniform_every_step_sets_the_caps_for_the_panel_only_and_redraws_every_step():
    agent = StubD2Agent(period=10)
    rule = rule_for("uniform_every_step", agent)
    steps = 400
    with rule.attached():
        assert (agent.d2_k_max, agent.d2_k_Z) == (1, 1)  # only for this panel
        for _ in range(steps):
            agent._batched_assign_skills()
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)  # restored
    assert "_batched_assign_skills" not in agent.__dict__
    assert agent.decisions == steps  # the stub's cadence follows the caps, as the real route does
    measures = rule.measures()
    assert measures["caps_applied"] == {"d2_k_max": 1, "d2_k_Z": 1}
    assert measures["uniform_label_change_reference"] == pytest.approx(1. - 1. / 6)
    assert measures["agent_label_change_fraction"] == pytest.approx(1. - 1. / 6, abs=.06)
    assert measures["team_label_change_fraction"] == pytest.approx(1. - 1. / 4, abs=.08)
    assert min(measures["agent_label_histogram"]) > 0  # every label is executed somewhere


def test_uniform_every_10_redraws_only_at_the_caps_ten_decisions():
    agent = StubD2Agent(period=10)
    rule = rule_for("uniform_every_10", agent)
    executed = run_stub_panel(rule, agent, 100)
    for step, (team, agents) in enumerate(executed):
        if step % 10:  # between decisions the drawn labels are held
            assert team.tolist() == executed[step - 1][0].tolist()
            assert agents.tolist() == executed[step - 1][1].tolist()
    measures = rule.measures()
    assert measures["caps_applied"] == {}
    assert agent.decisions == 10
    # At most one change per ten steps, and the drawn labels do move at least once.
    assert 0. < measures["agent_label_change_fraction"] <= 9 / 99 + 1e-12


def test_a_uniform_rule_uses_its_own_generator_and_no_global_stream():
    before = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    agent = StubD2Agent(period=10)
    rule = rule_for("uniform_every_step", agent)
    run_stub_panel(rule, agent, 50)
    generator = label.label_generator(782803, "uniform_every_step")
    values = generator.integers(0, 6, 100).tolist()
    after = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    assert before[0] == after[0]
    assert before[1][0] == after[1][0] and before[1][2:] == after[1][2:]
    np.testing.assert_array_equal(before[1][1], after[1][1])
    assert torch.equal(before[2], after[2])
    # the same (block, rule) is the same stream, and a different rule is a different one
    assert label.label_generator(782803, "uniform_every_step").integers(0, 6, 100).tolist() == values
    assert label.label_generator(782803, "uniform_every_10").integers(0, 6, 100).tolist() != values
    assert label.label_generator(782903, "uniform_every_step").integers(0, 6, 100).tolist() != values


def test_the_rules_refuse_a_construction_they_are_not_defined_on():
    agent = StubD2Agent()
    agent.d2_cost_c = .25
    with pytest.raises(ValueError, match="infinite interruption costs"):
        with rule_for("frozen_episode", agent).attached():
            pass
    agent.d2_cost_c = float("inf")
    agent.d2_enabled = False
    with pytest.raises(ValueError, match="D2 route"):
        with rule_for("frozen_episode", agent).attached():
            pass
    with pytest.raises(ValueError, match="unknown execution rule"):
        label.ExecutionRule("uniform_every_2", agent)
    with pytest.raises(ValueError, match="needs its own label generator"):
        label.ExecutionRule("uniform_every_step", agent)


# ---------------------------------------------------------------------------
# the label-effect measures, on a synthetic actor and critic with a known offset
# ---------------------------------------------------------------------------


class SyntheticActor:
    """`SkillDiscoverer.forward`'s interface, with the label's effect an exact per-label offset."""

    def __init__(self, offsets):
        self.offsets = torch.as_tensor(offsets, dtype=torch.float64)  # [labels, dims]
        self.calls = 0

    def __call__(self, observation, agent_skill, hidden_state, deterministic=False,
                 compact_context=None, central_input=None):
        assert deterministic is True and compact_context is None and central_input is None
        self.calls += 1
        base = observation[:, :self.offsets.shape[1]].double()
        actions = base + self.offsets[agent_skill.long()]
        return actions, None, None, hidden_state


class SyntheticCritic:
    """`R_Critic.forward`'s interface, with the team label's effect an exact per-label offset."""

    def __init__(self, offsets):
        self.offsets = torch.as_tensor(offsets, dtype=torch.float64)

    def __call__(self, cent_obs, rnn_states, masks, team_skill):
        values = cent_obs[:, :1].double() + self.offsets[team_skill.long()].reshape(-1, 1)
        return values, rnn_states


def synthetic_capture(rows, dims, labels, actor, held=0):
    observation = torch.arange(rows * dims, dtype=torch.float32).reshape(rows, dims) * .01
    skills = torch.full((rows,), int(held), dtype=torch.long)
    hidden = torch.zeros(rows, 4)
    action = actor(observation, skills, hidden, True)[0]
    return [{"observation": observation, "agent_skill": skills, "hidden": hidden,
             "deterministic": True, "compact_context": None, "central_input": None,
             "action": action}]


def test_the_label_effect_recovers_a_known_film_offset():
    labels, dims, rows = 6, 3, 8
    delta = np.array([.1, .2, .4])
    offsets = np.arange(labels)[:, None] * delta[None, :]  # label l shifts dimension d by l * delta
    actor = SyntheticActor(offsets)
    captured = synthetic_capture(rows, dims, labels, actor, held=0)
    std = np.array([1., 2., 4.])
    result = label.label_action_effect(actor, captured, std, n_z=labels)

    spread = float(np.sqrt(np.mean((np.arange(labels) - np.mean(np.arange(labels))) ** 2)))
    assert result["rows"] == rows and result["labels"] == labels
    assert result["action_dimensions"] == dims
    assert result["rms_label_deviation_per_dimension"] == pytest.approx((delta * spread).tolist())
    assert result["rms_label_deviation_over_std_per_dimension"] == pytest.approx(
        (delta * spread / std).tolist())
    assert result["rms_label_deviation_over_std_mean"] == pytest.approx(
        float(np.mean(delta * spread / std)))
    assert result["max_pairwise_label_distance_per_dimension"] == pytest.approx(
        ((labels - 1) * delta).tolist())
    assert result["max_pairwise_label_distance_in_std_units"] == pytest.approx(
        float(np.sqrt((((labels - 1) * delta / std) ** 2).sum())))
    # held label 0: the mean distance to the other five labels is the mean of 1..5 times delta
    assert result["held_label_to_others_distance_per_dimension"] == pytest.approx(
        (delta * np.mean(np.arange(1, labels))).tolist())
    assert result["held_label_to_others_in_std_units"] == pytest.approx(
        float(np.mean([np.sqrt(((l * delta / std) ** 2).sum()) for l in range(1, labels)])))
    assert result["recomputed_action_at_held_label_reproduces_the_panel"] is True
    assert result["max_absolute_difference_from_the_panel_action"] == 0.
    assert actor.calls == labels + 1  # one sweep over the labels, plus the capture's own call


def test_an_inert_label_measures_as_zero_and_a_changed_panel_action_is_reported():
    labels, dims, rows = 6, 3, 4
    actor = SyntheticActor(np.zeros((labels, dims)))
    captured = synthetic_capture(rows, dims, labels, actor, held=2)
    result = label.label_action_effect(actor, captured, np.ones(dims), n_z=labels)
    assert result["rms_label_deviation_over_std_mean"] == 0.
    assert result["max_pairwise_label_distance_in_std_units"] == 0.
    assert result["held_label_to_others_over_std_mean"] == 0.
    captured[0]["action"] = captured[0]["action"] + .5
    changed = label.label_action_effect(actor, captured, np.ones(dims), n_z=labels)
    assert changed["recomputed_action_at_held_label_reproduces_the_panel"] is False
    assert changed["max_absolute_difference_from_the_panel_action"] == pytest.approx(.5)


def test_the_low_level_value_spread_recovers_a_known_team_label_offset():
    labels, rows = 4, 5
    offsets = np.array([0., 1., 2., 3.])
    critic = SyntheticCritic(offsets)
    state = torch.full((rows, 2), 10., dtype=torch.float32)
    held = torch.zeros(rows, dtype=torch.long)
    captured = [{"cent_obs": state, "hidden": torch.zeros(rows, 4),
                 "masks": torch.ones(rows, 1), "team_skill": held,
                 "value": critic(state, None, None, held)[0]}]
    result = label.label_value_effect(critic, captured, n_Z=labels, use_valuenorm=True)
    expected_spread = float(np.sqrt(np.mean((offsets - offsets.mean()) ** 2)))
    assert result["rows"] == rows and result["labels"] == labels
    assert result["rms_label_spread"] == pytest.approx(expected_spread)
    assert result["mean_absolute_value"] == pytest.approx(float(np.mean(10. + offsets)))
    assert result["rms_label_spread_over_mean_absolute_value"] == pytest.approx(
        expected_spread / float(np.mean(10. + offsets)))
    assert result["max_pairwise_label_spread"] == pytest.approx(3.)
    assert result["held_label_to_others_mean_distance"] == pytest.approx(2.)
    assert result["recomputed_value_at_held_label_reproduces_the_panel"] is True
    assert result["value_norm"]["use_valuenorm"] is True


def test_the_action_standard_deviation_is_the_heads_own_log_std():
    head = DiagGaussian(4, 3, use_orthogonal=True, gain=.01, args=None)
    with torch.no_grad():
        head.logstd._bias.copy_(torch.tensor([[-1.], [0.], [.5]]))
    actor = SimpleNamespace(act=SimpleNamespace(action_out=head))
    values, note = label.action_standard_deviation(actor)
    assert values.tolist() == pytest.approx(np.exp([-1., 0., .5]).tolist())
    assert note["head"] == "DiagGaussian"
    assert note["log_std_clamped"] is False
    assert note["deterministic_action_is_squashed"] is False
    assert note["mean_and_std_share_a_space"] is True
    with pytest.raises(ValueError, match="diagonal Gaussian"):
        label.action_standard_deviation(SimpleNamespace(act=SimpleNamespace(
            action_out=SimpleNamespace())))


def test_every_recorded_measure_carries_a_definition():
    for name, text in label.RULE_DEFINITIONS.items():
        assert name in label.RULES and isinstance(text, str) and len(text) > 40
    for name, text in label.SOURCE_NOTES.items():
        assert isinstance(text, str) and len(text) > 40
    actor = SyntheticActor(np.zeros((6, 3)))
    result = label.label_action_effect(actor, synthetic_capture(2, 3, 6, actor), np.ones(3), n_z=6)
    for key in ("rms_label_deviation", "over_std", "max_pairwise_label_distance",
                "held_label_to_others", "scope", "label_path"):
        assert isinstance(result["definitions"][key], str)
    agent = StubD2Agent()
    measures = rule_for("as_trained", agent).measures()
    for key in ("label_change_fraction", "label_histogram", "uniform_label_change_reference"):
        assert isinstance(measures["definitions"][key], str)


# ---------------------------------------------------------------------------
# fake fits, the weights sidecar, and `reduce`
# ---------------------------------------------------------------------------


class HostEnv(helpers.Env):
    """The fake host carries Scenario 1's own widths and bounds."""

    state_dim, obs_dim = STATE_DIM, OBS_DIM
    area_size, height_range, n_uavs, n_users = AREA, HEIGHTS, N_UAVS, N_USERS

    def reset(self):
        _observations, info = super().reset()
        info["state"] = np.full(STATE_DIM, 100. * self.resets + self.lane)
        return np.full((r.N_UAVS, OBS_DIM), 10 * self.resets + self.lane), info

    def step(self, actions):
        _observations, reward, term, trunc, info = super().step(actions)
        info["next_state"] = np.full(STATE_DIM, 900. + self.t + self.lane)
        return np.full((r.N_UAVS, OBS_DIM), 800 + self.t + self.lane), reward, term, trunc, info


class PanelAgent(helpers.Agent):
    """The fake learner takes one coordinator step per PPO epoch and can write a checkpoint.

    `save_model` writes the same top-level shape the real `HMASDAgent.save_model` does, so the
    sidecar's inventory is exercised without a real model.
    """

    def update(self, **kwargs):
        losses = super().update(**kwargs)
        for _ in range(int(self.config.ppo_epochs)):
            self.coordinator_optimizer.step()
        return losses

    def save_model(self, path):
        torch.save({
            "skill_coordinator": {"encoder.weight": torch.zeros(2, 2)},
            "skill_discoverer": {"actor.base.weight": torch.zeros(2, 2),
                                 "actor.act.action_out.logstd._bias": torch.zeros(3, 1)},
            "team_discriminator": None, "individual_discriminator": None,
            "coordinator_optimizer": {"state": {}},
            "config": None,
            "valuenorm_state": {"coordinator": {"mean": 0.}, "discoverer": {"mean": 1.}},
        }, path)


@pytest.fixture
def fakes(monkeypatch, fake_only):
    # The thin entries install their own `base_summary` wrapper on the shared module and only some
    # of them take it off again; this restores the plain one after every test.
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, label):
        monkeypatch.setattr(module, "shared", r)
        monkeypatch.setattr(module, "_orig_base_summary", r.base_summary)

    def make_envs(count, seed, n_uavs, n_users, horizon):
        return [HostEnv(lane, seed + lane) for lane in range(count)]

    monkeypatch.setattr(r.e0, "_make_envs", make_envs)


def world_scores(arm, block_index):
    values = np.arange(r.EVAL_LANES, dtype=np.float64)
    return .25 + .015625 * block_index + .00390625 * (values % 4) + OFFSET[arm][block_index]


_TEMPLATES = {}


def template(tmp_path, name):
    if name not in _TEMPLATES:
        out = tmp_path / f"template_{name}"
        if name == label.SAVE_ARM:
            assert label.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        else:
            assert matched.run_fit(name, SEEDS[0], 1, None, out, admission=ADMISSION) == 0
        _TEMPLATES[name] = (json.loads((out / "summary.json").read_text()), out)
    summary, out = _TEMPLATES[name]
    return copy.deepcopy(summary), out


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = label.BLOCKS[seed]
    summary = copy.deepcopy(summary)
    summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                   training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                   evaluation_lane_seeds=list(range(evaluation_seed,
                                                    evaluation_seed + r.EVAL_LANES)))
    summary["learner_config"]["seed"] = seed
    summary["evaluation_config"]["seed"] = evaluation_seed
    for panel in summary["panels"]:
        values = world_scores(arm, index)
        panel["lane_seeds"] = summary["evaluation_lane_seeds"]
        panel["native_scores_J"] = [float(v) for v in values]
        panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
    summary["evaluation"] = summary["panels"][-1]
    if summary.get("final_weights"):
        summary["final_weights"] = dict(summary["final_weights"], block_seed=seed,
                                        sha256=f"sha-{seed}")
    return summary


def probe_summary(seed, sha, **overrides):
    """A published probe summary of this object, in the shape `reduce` reads."""
    measured = {}
    for index, name in enumerate(label.RULES):
        measured[name] = {
            "rule": name, "J_mean": .3 + .01 * index,
            "J_world_scores": [.3 + .01 * index] * 4,
            "agent_label_change_fraction": .1 * (index + 1),
            "decision_fraction": 1. if name == "uniform_every_step" else .1,
            "agent_label_histogram": [4] * 6}
    summary = {
        "object_id": label.OBJECT_ID, "command": "probe", "status": "complete",
        "block_seed": seed, "evaluation_seed": label.BLOCKS[seed],
        "launch_sha": "synthetic-source", "optimizer_steps": 0,
        "weights_record": {"sha256": sha},
        "faithful_load": {"faithful_load": True, "first_differing_world": None},
        "reference": {"panel_rollouts": label.ROLLOUTS},
        "rules_measured": measured,
        "label_effect": {
            "action": {
                "rows": 100, "rms_label_deviation_over_std_mean": .02,
                "rms_label_deviation_over_std_per_dimension": [.01, .02, .03],
                "max_pairwise_label_distance_over_std_mean": .05,
                "max_pairwise_label_distance_in_std_units": .09,
                "held_label_to_others_over_std_mean": .03,
                "held_label_to_others_in_std_units": .06,
                "action_standard_deviation_per_dimension": [1., 1., 1.]},
            "low_level_value": {"rows": 100, "rms_label_spread_over_mean_absolute_value": .12}}}
    summary.update(overrides)
    return summary


def supplied(tmp_path):
    fits = [placed(template(tmp_path, label.SAVE_ARM)[0], label.SAVE_ARM, index)
            for index in range(3)]
    references = [placed(template(tmp_path, "D1280")[0], "D1280", index) for index in range(3)]
    probes = [probe_summary(SEEDS[index], f"sha-{SEEDS[index]}") for index in range(3)]
    return fits, probes, references


def test_fit_runs_the_frozen_d_route_and_writes_the_weights_after_it(tmp_path, fakes):
    summary, out = template(tmp_path, label.SAVE_ARM)
    assert summary["status"] == "complete" and summary["object_id"] == label.OBJECT_ID
    assert summary["label_content_object"] == label.OBJECT_ID
    assert summary["label_content_arm"] == label.SAVE_ARM
    assert summary["factorial_arm"] == label.SAVE_ARM and summary["arm"] == "D0"
    assert summary["admission"] == ADMISSION and summary["primary"] == "J_45"
    assert summary["arm_overrides"] == {}
    assert summary["ordinary_wall_plan_seconds"] == label.WALL_PLANS[label.SAVE_ARM]
    assert summary["coordinator_batch_size"] == label.ARMS[label.SAVE_ARM][1]
    assert summary["last_completed_boundary"] == "final weights written"
    for phase in ("learner_config", "evaluation_config"):
        assert (summary[phase]["skill_cap_k_max"], summary[phase]["team_cap_k_Z"]) == label.ARM_CAPS
        assert summary[phase]["k"] == label.SKILL_PERIOD
        differences = summary[f"{phase}_differences_from_recorded_d1280"]
        assert differences["available"] is True
        assert set(differences["differences"]) <= set(label.GEOMETRY_FIELDS)

    weights = summary["final_weights"]
    path = out / label.WEIGHTS_NAME
    assert path.exists() and weights["file"] == label.WEIGHTS_NAME
    assert weights["sha256"] == label.file_sha256(path)
    assert weights["bytes"] == path.stat().st_size
    assert weights["block_seed"] == SEEDS[0] and weights["launch_sha"] == summary["launch_sha"]
    inventory = weights["inventory"]
    assert "skill_coordinator" in inventory["keys"] and "skill_discoverer" in inventory["keys"]
    assert inventory["empty_keys"] == ["config", "individual_discriminator", "team_discriminator"]
    assert inventory["low_level_actor_logstd_key"] == "actor.act.action_out.logstd._bias"
    assert inventory["valuenorm_state"] == ["coordinator", "discoverer"]
    assert inventory["normalization_state"] == []
    sidecar = json.loads((out / label.SIDECAR_NAME).read_text())
    assert sidecar == weights
    record, reason = label.weights_record(out / "summary.json")
    assert reason is None and record["sha256"] == weights["sha256"]

    assert set(label.fit_endpoint(summary)) == set(range(5, 50, 5))
    assert label.CURRENT == {"label_content_arm": None, "admission": None, "summary": None,
                             "agent": None}
    assert production_shared.base_summary is not label.base_summary  # the wrapper came off
    assert b01.build_learner is label._orig_build_learner  # and so did this one


def test_a_fit_that_is_not_complete_saves_nothing(tmp_path, fakes, monkeypatch):
    out = tmp_path / "broken"

    def broken(*args, **kwargs):
        raise ValueError("synthetic collector failure")

    monkeypatch.setattr(b01, "collect_training", broken)
    assert label.run_fit(label.SAVE_ARM, SEEDS[0], out, admission=ADMISSION) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete" and "synthetic collector failure" in summary["failure"]
    assert summary["final_weights"] is None
    assert not (out / label.WEIGHTS_NAME).exists()
    assert not (out / label.SIDECAR_NAME).exists()
    assert label.CURRENT["agent"] is None
    with pytest.raises(ValueError, match="not complete saves no weights"):
        label.save_final_weights(None, summary, out)


def test_fit_endpoint_refuses_a_fit_that_is_not_the_declared_one(tmp_path, fakes):
    summary = placed(template(tmp_path, label.SAVE_ARM)[0], label.SAVE_ARM, 0)
    for mutate, message in (
            (lambda s: s.update(label_content_object="OTHER"), "not a label-content fit"),
            (lambda s: s.update(label_content_arm="D_K10"), "three planned fits"),
            (lambda s: s.update(block_seed=773103), "three planned fits"),
            (lambda s: s.update(arm_overrides={"k": 5}), "empty override set"),
            (lambda s: s.update(status="incomplete"), "incomplete or wrong arm")):
        damaged = copy.deepcopy(summary)
        mutate(damaged)
        with pytest.raises(ValueError, match=message):
            label.fit_endpoint(damaged)
    assert set(label.fit_endpoint(summary)) == set(range(5, 50, 5))
    with pytest.raises(ValueError):  # a reference fit is not one of this object's
        label.fit_endpoint(placed(template(tmp_path, "D1280")[0], "D1280", 0))


def test_reduce_reads_three_fits_three_probes_and_the_published_d1280_fits(tmp_path, fakes):
    fits, probes, references = supplied(tmp_path)
    result = label.reduce_inputs(fits, probes, references)
    assert result["status"] == "complete" and result["object_id"] == label.OBJECT_ID
    assert result["capture_bit_identical_blocks"] == 3
    assert result["faithful_load_blocks"] == 3
    assert result["invalid_fits"] == result["invalid_probes"] == result["invalid_references"] == {}
    for block in result["blocks"]:
        assert block["status"] == "complete"
        assert block["capture_bit_identical"]["bit_identical"] is True
        assert block["weights_match"] is True and block["faithful_load"] is True
        assert sorted(block["J_by_rule"]) == sorted(label.RULES)
        assert block["J_minus_as_trained"]["as_trained"] == 0.
        assert block["label_effect"]["rms_label_deviation_over_std_mean"] == .02
        assert block["decision_fraction_by_rule"]["uniform_every_step"] == 1.
    assert result["J_by_rule"]["as_trained"]["available_blocks"] == 3
    counts = result["J_difference_counts"]
    assert counts["threshold"] == .05 and counts["small_difference"] == .02
    assert counts["as_trained"]["blocks_below_small_difference"] == 3
    assert counts["uniform_every_step"]["blocks_at_or_above_threshold"] == 0
    assert result["label_effect"]["rms_label_deviation_over_std_mean"]["mean"] == .02
    # no verdict strings: the summary reports numbers, definitions and limits only
    text = json.dumps(result).lower()
    for word in ("inert", "content present", "verdict", "confirmed", "supported"):
        assert word not in text


def test_reduce_refuses_inputs_it_cannot_read(tmp_path, fakes):
    fits, probes, references = supplied(tmp_path)
    with pytest.raises(ValueError, match="mixed launch shas"):
        damaged = copy.deepcopy(fits)
        damaged[1]["launch_sha"] = "another-source"
        label.reduce_inputs(damaged, probes, references)
    with pytest.raises(ValueError, match="duplicate block"):
        label.reduce_inputs(fits + [copy.deepcopy(fits[0])], probes, references)
    with pytest.raises(ValueError, match="duplicate probe block"):
        label.reduce_inputs(fits, probes + [copy.deepcopy(probes[0])], references)
    with pytest.raises(ValueError, match="duplicate reference block"):
        label.reduce_inputs(fits, probes, references + [copy.deepcopy(references[0])])

    # a fit of another object, and a block whose published D1280 fit was not supplied
    damaged = copy.deepcopy(fits)
    damaged[0]["label_content_object"] = "OTHER"
    result = label.reduce_inputs(damaged, probes, references)
    assert result["status"] == "incomplete"
    assert "not a fit of this object" in result["invalid_fits"][str(SEEDS[0])]
    assert result["blocks"][0]["capture_bit_identical"]["bit_identical"] is False
    result = label.reduce_inputs(fits, probes, references[1:])
    assert "was not supplied" in result["invalid_fits"][str(SEEDS[0])]

    # an incomplete probe, a probe without the four rules, and a probe that is not faithful
    for mutate, message in (
            (lambda s: s.update(status="incomplete"), "incomplete probe"),
            (lambda s: s.update(command="fit"), "not a probe of this object"),
            (lambda s: s.update(optimizer_steps=1), "took an optimizer step"),
            (lambda s: s["rules_measured"].pop("uniform_every_10"), "all four execution rules"),
            (lambda s: s.update(faithful_load={"faithful_load": False,
                                               "first_differing_world": 3}), "faithful load"),
            (lambda s: s.update(label_effect={}), "no label-effect reading")):
        damaged = copy.deepcopy(probes)
        mutate(damaged[2])
        result = label.reduce_inputs(fits, damaged, references)
        assert result["status"] == "incomplete"
        assert message in result["invalid_probes"][str(SEEDS[2])]
        assert result["blocks"][2]["status"] == "incomplete"


def test_reduce_refuses_a_probe_whose_weights_are_not_its_blocks(tmp_path, fakes):
    fits, probes, references = supplied(tmp_path)
    probes[1]["weights_record"] = {"sha256": "sha-of-another-fit"}
    result = label.reduce_inputs(fits, probes, references)
    assert result["status"] == "incomplete"
    block = result["blocks"][1]
    assert block["weights_match"] is False and block["status"] == "incomplete"
    assert "sha256" in block["missing_or_invalid"]["weights"]
    assert "J_by_rule" not in block


def test_reduce_does_not_read_a_probe_whose_fit_is_not_bit_identical(tmp_path, fakes):
    fits, probes, references = supplied(tmp_path)
    panel = fits[2]["panels"][0]  # the rollout-5 panel, with its returns kept consistent
    panel["native_scores_J"] = [v + .5 for v in panel["native_scores_J"]]
    panel["returns_U"] = [v * r.HORIZON / r.N_UAVS for v in panel["native_scores_J"]]
    result = label.reduce_inputs(fits, probes, references)
    assert result["status"] == "incomplete"
    block = result["blocks"][2]
    assert block["capture_bit_identical"]["bit_identical"] is False
    assert block["capture_bit_identical"]["first_differing_panel"] == 5
    assert block["weights_match"] is True and block["status"] == "incomplete"
    assert "not bit-identical" in block["missing_or_invalid"]["capture"]
    assert "J_by_rule" not in block
    assert result["capture_bit_identical_blocks"] == 2
