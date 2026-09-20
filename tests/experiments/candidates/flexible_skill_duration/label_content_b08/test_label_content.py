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
PAIR_RULE_KEYS = tuple(f"pair_rule_{name}" for name in label.PAIR_RULES)


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


# ---------------------------------------------------------------------------
# (d): the pure measures of the accessible-END reading
# ---------------------------------------------------------------------------


def test_the_law_weighted_action_change_is_the_laws_own_squared_distance_from_keep():
    """A synthetic label sweep with a known offset, a known law and a known variance."""
    labels, dims = 6, 3
    delta = np.array([.1, .2, .4])
    means = np.arange(labels)[:, None] * delta[None, :]  # label l shifts dimension d by l * delta
    variance = np.array([1., 4., 16.])
    law = np.array([.5, .2, .1, .1, .05, .05])
    held = 2
    expected = float(sum(
        law[l] * np.mean(((means[l] - means[held]) ** 2) / variance) for l in range(labels)))
    assert label.law_weighted_action_change(means, held, law, variance) == pytest.approx(expected)

    # KEEP contributes zero, so a law that keeps with probability one reaches nothing
    certain = np.zeros(labels)
    certain[held] = 1.
    assert label.law_weighted_action_change(means, held, certain, variance) == 0.
    # an inert label sweep is zero under every law
    assert label.law_weighted_action_change(
        np.zeros((labels, dims)), held, law, variance) == 0.
    # the per-dimension normaliser is the variance, not the standard deviation
    assert label.law_weighted_action_change(means, held, law, variance * 4.) == pytest.approx(
        expected / 4.)


def test_the_capture_rule_at_the_production_geometry_covers_every_phase():
    """What the fixed rule selects on the real panel: 32 worlds, 500 ticks, caps of 10.

    Arithmetic only, no model: the rule is an even stride over ticks crossed with a world rotation,
    and a candidate tick that falls on the forced team boundary yields nothing.
    """
    horizon, limit, lanes, period = 500, label.HISTORY_LIMIT, 32, 10
    capture = label.HistoryCapture(
        SimpleNamespace(config=SimpleNamespace(n_agents=6, n_z=6, n_Z=6, state_dim=STATE_DIM,
                                               obs_dim=OBS_DIM)),
        limit=limit, horizon=horizon)
    assert capture.stride == 7  # 500 // 64
    candidates = list(range(0, horizon, capture.stride))
    assert len(candidates) == 72
    # a_Z is the predecision team age: tick 0 resets, and the cap fires at every multiple of 10
    kept = [tick for tick in candidates if tick % period]
    assert len(kept) == limit == 64  # the eight excluded candidates are the multiples of 70
    assert [tick for tick in candidates if tick not in kept] == list(range(0, horizon, 70))
    # every world is taken exactly twice, in the fixed rotation
    worlds = [index % lanes for index in range(len(kept))]
    assert sorted(set(worlds)) == list(range(lanes))
    assert all(worlds.count(world) == 2 for world in range(lanes))
    # and every time-to-forced-cap from 1 to 9 is present, so the three strata are all populated
    strata = {}
    for tick in kept:
        strata[label.stratum_name(period - tick % period)] = strata.get(
            label.stratum_name(period - tick % period), 0) + 1
    assert strata == {"1": 7, "2-4": 22, "5-9": 35}
    assert sum(strata.values()) == limit
    assert len({tick % period for tick in kept}) == 9  # phases 1..9, never 0


def test_the_strata_are_the_entrys_own_three():
    assert [name for name, _low, _high in label.PHASE_STRATA] == ["1", "2-4", "5-9"]
    assert [label.stratum_name(value) for value in range(1, 10)] == [
        "1", "2-4", "2-4", "2-4", "5-9", "5-9", "5-9", "5-9", "5-9"]
    assert label.stratum_name(0) is None and label.stratum_name(10) is None


def test_the_serving_competitor_pair_is_codexs_rule_on_a_known_serving_state():
    """Five UAVs, four users, a hand-built serving assignment: the rule has one answer."""
    sinr = np.array([
        [10., 10., -5., -5.],   # UAV 0 serves users 0 and 1
        [3., 2., 9., -8.],      # UAV 1 serves user 2, and is the best other link for user 0
        [1., 4., 1., 7.],       # UAV 2 serves user 3, and is the best other link for user 1
        [9., 9., 9., 9.],       # UAV 3 serves nobody: it is never a competitor
        [-20., -20., -20., -20.]])
    connections = np.zeros((5, 4), dtype=bool)
    connections[0, 0] = connections[0, 1] = connections[1, 2] = connections[2, 3] = True
    snapshot = {"sinr": sinr, "connections": connections, "positions": np.zeros((5, 3)),
                "min_sinr": 0., "max_connections": 10, "users": 4}
    pair = label.serving_competitor_pair(snapshot)
    # user 0: server 0, best other serving link 1 (3 dB > 1 dB) -> (0, 1)
    # user 1: server 0, best other serving link 2 (4 dB > 2 dB) -> (0, 2)
    # user 2: server 1, best other serving link 2 (1 dB > -5 dB) -> (1, 2)
    # user 3: server 2, best other serving link 0 (-5 dB > -8 dB) -> (0, 2)
    # so (0, 2) is counted twice and wins; UAV 3 serves nobody and is never a competitor
    assert pair["agents"] == [0, 2] and pair["count"] == 2
    assert pair["rule"] == "serving_competitor" and pair["candidate_pairs"] == 3
    assert pair["service_loads"] == [2, 1]
    assert pair["serving_sinr_mean_dB"] == pytest.approx(np.mean([10., 7.]))
    assert pair["competitor_sinr_mean_dB"] == pytest.approx(np.mean([4., -5.]))
    assert pair["served_users"] == 4 and pair["serving_uavs"] == 3

    # nobody is served: no pair
    empty = dict(snapshot, connections=np.zeros((5, 4), dtype=bool))
    assert label.serving_competitor_pair(empty) is None
    # a single serving UAV has no other serving UAV to pair with
    single = np.zeros((5, 4), dtype=bool)
    single[0, 0] = True
    assert label.serving_competitor_pair(dict(snapshot, connections=single)) is None


def test_the_nearest_horizontal_pair_ignores_height_and_breaks_ties_by_id():
    positions = np.array([[0., 0., 100.], [10., 0., 50.], [0., 10., 150.], [500., 500., 100.]])
    pair = label.nearest_horizontal_pair(positions)
    assert pair["agents"] == [0, 1] and pair["rule"] == "nearest_horizontal"
    assert pair["horizontal_distance_metres"] == pytest.approx(10.)
    # the height differs by 50 m and does not enter; an exact tie takes the lowest ids
    tied = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.], [3., 0., 0.]])
    assert label.nearest_horizontal_pair(tied)["agents"] == [0, 1]


def test_the_pair_rule_falls_back_when_the_snapshots_are_not_the_histories_own():
    """A snapshot from another environment or tick does not establish a predecision serving state."""
    good = [{"serving": {"connections": np.zeros((6, 4), dtype=bool)}, "position_gap": 1e-5}
            for _ in range(4)]
    rule, reason, worst = label.resolve_pair_rule("serving_competitor", good)
    assert rule == "serving_competitor" and reason is None and worst == 1e-5

    stale = copy.deepcopy(good)
    stale[2]["position_gap"] = 993.4  # the whole-area difference a never-stepped lane gives
    rule, reason, worst = label.resolve_pair_rule("serving_competitor", stale)
    assert rule == "nearest_horizontal" and worst == 993.4
    assert "not the captured states' own" in reason

    missing = copy.deepcopy(good)
    missing[0] = {"serving": None, "position_gap": None}
    rule, reason, _worst = label.resolve_pair_rule("serving_competitor", missing)
    assert rule == "nearest_horizontal" and "carry no predecision serving state" in reason

    # the fallback is never overridden, and it carries the reason it was requested with
    assert label.resolve_pair_rule("nearest_horizontal", good, "no serving state here") == (
        "nearest_horizontal", "no serving state here", None)


def test_a_host_without_the_serving_state_selects_the_fallback_pair_rule():
    available, reason = label.serving_available([SimpleNamespace(env=None)], 6)
    assert available is False and "does not expose" in reason
    available, reason = label.serving_available([], 6)
    assert available is False and "no evaluation environments" in reason
    assert label.serving_snapshot(SimpleNamespace(env=SimpleNamespace()), 6) is None
    assert label.action_scale([SimpleNamespace(env=None)]) is None
    assert label.action_scale([SimpleNamespace(env=SimpleNamespace(max_speed=30., time_step=1.))]) \
        == 30.


def test_the_end_aggregates_count_every_query_and_every_stratum():
    records = [
        {"label_changes": True, "one_minus_q_held": .8, "law_weighted_action_change": .2,
         "greedy_action_change_in_std_units": .4, "greedy_action_change_native_max_abs": .1,
         "next_hidden_relative_difference": .3, "min_remaining": 1, "stratum": "1"},
        {"label_changes": False, "one_minus_q_held": .2, "law_weighted_action_change": .0,
         "greedy_action_change_in_std_units": .0, "greedy_action_change_native_max_abs": .0,
         "next_hidden_relative_difference": None, "min_remaining": 3, "stratum": "2-4"},
        {"label_changes": False, "one_minus_q_held": .5, "law_weighted_action_change": .1,
         "greedy_action_change_in_std_units": .2, "greedy_action_change_native_max_abs": .05,
         "next_hidden_relative_difference": .1, "min_remaining": 7, "stratum": "5-9"}]
    overall = label.aggregate_end_records(records)
    assert overall["agent_queries"] == 3
    assert overall["same_label_reselection"] == {"count": 2, "of": 3, "fraction": 2 / 3}
    assert overall["label_changes"] == {"count": 1, "of": 3, "fraction": 1 / 3}
    assert overall["mean_one_minus_q_held"] == pytest.approx(.5)
    assert overall["mean_next_hidden_relative_difference"] == pytest.approx(.2)  # None is skipped
    strata = label.by_stratum(records, label.aggregate_end_records)
    assert [strata[name]["agent_queries"] for name in ("1", "2-4", "5-9")] == [1, 1, 1]
    assert strata["outside_1_to_9"]["agent_queries"] == 0
    assert sum(strata[name]["agent_queries"] for name in strata) == overall["agent_queries"]
    assert label.aggregate_end_records([])["same_label_reselection"]["fraction"] is None

    pairs = [
        {"pair": {"agents": [0, 1]}, "stratum": "1", "label_changes": [True, True],
         "singleton_label_changes": [True, False], "action_change_in_std_units": [.4, .2]},
        {"pair": {"agents": [0, 2]}, "stratum": "5-9", "label_changes": [True, False],
         "singleton_label_changes": [False, False], "action_change_in_std_units": [.1, .0]},
        {"pair": None, "stratum": "2-4", "label_changes": (),
         "singleton_label_changes": (), "action_change_in_std_units": ()}]
    outcomes = label.aggregate_pair_records(pairs)
    assert outcomes["histories"] == 3 and outcomes["histories_with_a_pair"] == 2
    assert outcomes["histories_without_a_pair"] == 1
    assert outcomes["outcome_counts"] == {"neither": 0, "one": 1, "both": 1}
    assert outcomes["both_singletons_also_change"] == {"count": 0, "of": 2, "fraction": 0.}
    assert outcomes["mean_action_change_in_std_units"] == pytest.approx(np.mean([.4, .2, .1, .0]))


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
    for name, text in label.END_DEFINITIONS.items():
        assert isinstance(text, str) and len(text) > 40
    for name in PAIR_RULE_KEYS:
        assert name in label.END_DEFINITIONS
    # the strata definition says what these strata cannot identify on this construction
    assert "collinear" in label.END_DEFINITIONS["strata"]
    assert "synchronised" in label.END_DEFINITIONS["strata"]
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


def accessible_end_summary(index):
    """The shape of (d) that `reduce` reads, with per-stratum counts that add up."""
    stratum = lambda queries, reselection: {
        "agent_queries": queries,
        "same_label_reselection": {"count": int(queries * reselection), "of": queries,
                                   "fraction": reselection},
        "label_changes": {"count": queries - int(queries * reselection), "of": queries,
                          "fraction": 1. - reselection},
        "mean_one_minus_q_held": .3 + .01 * index,
        "mean_law_weighted_action_change": .02,
        "mean_greedy_action_change_in_std_units": .1,
        "mean_greedy_action_change_native_max_abs": .05,
        "mean_next_hidden_relative_difference": .2,
        "mean_min_remaining": 5.}
    return {
        "pair_rule": "serving_competitor", "pair_rule_reason": None,
        "histories": 57, "agent_queries": 342,
        "caps": {"skill_cap_k_max": 10, "team_cap_k_Z": 10, "labels": 6},
        "metres_per_action_unit": 30.,
        "overall": stratum(342, .8),
        "by_stratum": {"1": stratum(36, .75), "2-4": stratum(114, .8),
                       "5-9": stratum(192, .82), "outside_1_to_9": stratum(0, 0.)},
        "stratum_counts": {"1": 36, "2-4": 114, "5-9": 192},
        "by_serving": {"serving": stratum(200, .8), "not_serving": stratum(142, .8)},
        "pairs": {"histories": 57, "histories_with_a_pair": 50, "histories_without_a_pair": 7,
                  "outcome_counts": {"neither": 40, "one": 8, "both": 2},
                  "outcome_fractions": {"neither": .8, "one": .16, "both": .04}},
        "pairs_by_stratum": {},
        "checks": {"q_sums_to_one_max_deviation": 1e-7,
                   "actor_label_is_the_held_label": True,
                   "label_means_reproduce_the_panel_action": True},
        "capture": {"histories": 57, "capture_stride": 7, "candidate_ticks": 64},
        "normalisers": {"use_obsnorm": False, "use_statenorm": False},
        "decision_replay": {"checked": 4, "reproduced": 4},
        "wall_seconds": 2.}


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
            "low_level_value": {"rows": 100, "rms_label_spread_over_mean_absolute_value": .12}},
        "accessible_end": accessible_end_summary(SEEDS.index(seed))}
    summary.update(overrides)
    return summary


def supplied(tmp_path, probe_sha="synthetic-source"):
    fits = [placed(template(tmp_path, label.SAVE_ARM)[0], label.SAVE_ARM, index)
            for index in range(3)]
    references = [placed(template(tmp_path, "D1280")[0], "D1280", index) for index in range(3)]
    probes = [probe_summary(SEEDS[index], f"sha-{SEEDS[index]}", launch_sha=probe_sha)
              for index in range(3)]
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
    # (d) is carried through per block and described across them, with no verdict
    end = result["accessible_end"]
    assert end["one_pair_rule_across_blocks"] == "serving_competitor"
    assert set(end["pair_rule_by_block"]) == {str(seed) for seed in SEEDS}
    assert end["histories_by_block"] == {str(seed): 57 for seed in SEEDS}
    assert end["same_label_reselection_fraction"]["available_blocks"] == 3
    assert end["same_label_reselection_fraction"]["mean"] == pytest.approx(.8)
    assert end["same_label_reselection_fraction_by_stratum"]["1"]["mean"] == pytest.approx(.75)
    assert end["mean_one_minus_q_held"]["available_blocks"] == 3
    assert end["pair_outcome_fractions"]["both"]["mean"] == pytest.approx(.04)
    assert end["agent_queries_by_stratum"]["2-4"] == {str(seed): 114 for seed in SEEDS}
    for block in result["blocks"]:
        carried = block["accessible_end"]
        assert carried["pair_rule"] == "serving_competitor" and carried["histories"] == 57
        assert sum(carried["stratum_counts"].values()) == carried["agent_queries"]
        assert carried["decision_replay"] == {"checked": 4, "reproduced": 4}
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
            (lambda s: s.update(label_effect={}), "no label-effect reading"),
            (lambda s: s.update(accessible_end={}), "no accessible-END reading")):
        damaged = copy.deepcopy(probes)
        mutate(damaged[2])
        result = label.reduce_inputs(fits, damaged, references)
        assert result["status"] == "incomplete"
        assert message in result["invalid_probes"][str(SEEDS[2])]
        assert result["blocks"][2]["status"] == "incomplete"


def test_reduce_accepts_probes_published_later_than_their_fits(tmp_path, fakes):
    """The probe is a later command from a later source; only the checkpoint ties it to its fit."""
    fits, probes, references = supplied(tmp_path, probe_sha="a-later-source")
    assert {fit["launch_sha"] for fit in fits} == {"synthetic-source"}
    result = label.reduce_inputs(fits, probes, references)
    assert result["status"] == "complete"
    assert result["batch_launch_sha"] == "synthetic-source"
    assert result["probe_launch_sha"] == "a-later-source"
    assert result["invalid_probes"] == {}
    for index, block in enumerate(result["blocks"]):
        assert block["status"] == "complete"
        assert block["probe"]["launch_sha"] == "a-later-source"
        assert block["fit"]["launch_sha"] == "synthetic-source"
        # what ties the probe to the fit is the checkpoint, which is still compared
        assert block["weights_match"] is True
        assert block["probe"]["weights_sha256"] == block["fit"]["weights"]["sha256"] == (
            f"sha-{SEEDS[index]}")
    assert "one launch sha is required within the fits and one within the probes" in result[
        "fit_and_probe_launch_shas"]

    # a probe whose weights are not its fit's is still refused, whatever its sha
    damaged = copy.deepcopy(probes)
    damaged[0]["weights_record"] = {"sha256": "sha-of-another-fit"}
    assert label.reduce_inputs(fits, damaged, references)["blocks"][0]["weights_match"] is False

    # mixed shas *within* the probes are refused, exactly as mixed shas within the fits are
    mixed = copy.deepcopy(probes)
    mixed[2]["launch_sha"] = "a-third-source"
    with pytest.raises(ValueError, match="mixed launch shas among the probes"):
        label.reduce_inputs(fits, mixed, references)


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
