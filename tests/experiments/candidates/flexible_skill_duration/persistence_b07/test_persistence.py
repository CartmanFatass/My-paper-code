"""The persistence entry: the construction of both arms, the behaviour measures and `reduce`.

Fake learners, fake hosts and pure measure functions only (the real stack is in
`test_persistence_real_tiny.py`, because the fake-only helper forbids real construction). Two
checks read the actually recorded stage-1 D1280 configurations from
`runs/flexible_skill_duration/b01_s1_d1280_<block>_a01/summary.json`. Technical checks: nothing
here asserts the direction or the size of any measured quantity.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_persistence_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_persistence_b07 as persistence  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(persistence.BLOCKS)
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}
STATE_DIM, OBS_DIM = 119, 104  # Scenario 1's own widths, so the recorded comparison is real
N_UAVS, N_USERS, AREA, HEIGHTS = 6, 50, 1000., (50., 150.)
# Exact dyadic offsets from the block base, per arm and block; every panel of a fit carries them.
# `D_K10` carries the D1280 reference's own scores, which is the bit-identical case.
OFFSET = {"D1280": [0., 0., 0.], "D_K10": [0., 0., 0.], "D_K1": [-.0625, -.03125, -.125],
          "CF_S": [-.25, -.25, -.25]}


def lanes(count):
    return [SimpleNamespace(state_dim=STATE_DIM, obs_dim=104) for _ in range(count)]


# ---------------------------------------------------------------------------
# the construction: the D1280 one, plus the arm's three declared fields
# ---------------------------------------------------------------------------


def test_the_construction_is_the_recorded_d1280_fit_on_every_block():
    """Environment-free, both phases, all three blocks, against the published stage-1 fits."""
    persistence.bind()
    snapshot = production_shared.config_snapshot
    for seed in SEEDS:
        recorded = json.loads(persistence.RECORDED_FITS[seed].read_text(encoding="utf-8"))
        assert recorded["factorial_arm"] == "D1280" and recorded["status"] == "complete"
        for arm in persistence.PERSISTENCE_ARMS:
            learner = snapshot(b01.make_config(arm, lanes(16), seed))
            evaluation = snapshot(b01.make_config(arm, lanes(32), persistence.BLOCKS[seed]))
            expected = set(persistence.ARM_OVERRIDES[arm])
            assert set(persistence.config_differences(learner, recorded["learner_config"])) == expected
            assert set(persistence.config_differences(evaluation, recorded["evaluation_config"])) == expected
            assert learner["k"] == evaluation["k"] == 10  # the low-level chunk length, both arms
            assert learner["policy_interruption_mode"] == "d2"
            assert learner["n_Z"] == learner["n_z"] == 6
            assert learner["use_central_snapshot_in_flat_actor"] is False
            caps = persistence.ARM_CAPS[arm]
            assert (learner["skill_cap_k_max"], learner["team_cap_k_Z"]) == caps
            assert (evaluation["skill_cap_k_max"], evaluation["team_cap_k_Z"]) == caps
            assert learner["coordinator_batch_size"] == persistence.ARMS[arm][1]
            # No buffer field is derived from the caps or from the coordinator batch, so re-running
            # `calculate_and_set_buffer_sizes` after the overrides leaves them at the D1280 values.
            for field in ("high_level_buffer_size", "high_level_batch_size", "buffer_size",
                          "batch_size", "total_timesteps"):
                assert learner[field] == recorded["learner_config"][field]
        assert persistence.host_geometry() == persistence.probe.FROZEN_GEOMETRY


def test_the_overrides_are_exactly_the_three_declared_fields():
    persistence.bind()
    assert persistence.ARM_OVERRIDES["D_K10"] == {}
    assert persistence.ARM_OVERRIDES["D_K1"] == {
        "skill_cap_k_max": 1, "team_cap_k_Z": 1, "coordinator_batch_size": 12800}
    assert persistence.ARMS["D_K1"][1] == persistence.ARM_OVERRIDES["D_K1"]["coordinator_batch_size"]
    assert persistence.ARMS["D_K10"] == matched.ARMS["D1280"]  # the frozen D construction
    k1 = b01.make_config("D_K1", lanes(16), SEEDS[0])
    assert k1.validate_config() is None  # configs/config_1.py accepts caps of 1
    assert k1.k == 10 and k1.skill_cap_k_max == 1 and k1.team_cap_k_Z == 1


def test_make_config_refuses_an_override_that_moves_anything_else(monkeypatch):
    """`k` is refused because the buffer recomputation moves `high_level_buffer_size` with it."""
    persistence.bind()
    monkeypatch.setitem(persistence.ARM_OVERRIDES, "D_K1", {"k": 5})
    with pytest.raises(ValueError, match="differs from the D1280 construction"):
        b01.make_config("D_K1", lanes(16), SEEDS[0])
    monkeypatch.setitem(persistence.ARM_OVERRIDES, "D_K1", {"lambda_l": .5})
    config = b01.make_config("D_K1", lanes(16), SEEDS[0])  # a lone field is admitted, and recorded
    assert config.lambda_l == .5
    with pytest.raises(ValueError, match="unknown arm"):
        persistence.make_config("D_K7", lanes(16), SEEDS[0])


def test_the_recorded_comparison_exempts_the_host_geometry_only_on_a_shrunken_host(monkeypatch):
    persistence.bind()
    recorded = json.loads(persistence.RECORDED_FITS[SEEDS[0]].read_text(encoding="utf-8"))
    config = production_shared.config_snapshot(b01.make_config("D_K10", lanes(16), SEEDS[0]))
    assert persistence.require_recorded_construction(
        config, recorded["learner_config"], "learner_config", "D_K10") == {}
    for arm in persistence.PERSISTENCE_ARMS:
        changed = dict(config, lambda_l=.5)
        with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
            persistence.require_recorded_construction(
                changed, recorded["learner_config"], "learner_config", arm)
        # On the frozen host the lane count is not an excuse either.
        smaller = dict(config, num_envs=2)
        with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
            persistence.require_recorded_construction(
                smaller, recorded["learner_config"], "learner_config", arm)
    monkeypatch.setattr(persistence.shared, "TRAIN_LANES", 2)
    assert persistence.host_geometry() != persistence.probe.FROZEN_GEOMETRY
    assert set(persistence.require_recorded_construction(
        dict(config, num_envs=2), recorded["learner_config"], "learner_config", "D_K10")) == {"num_envs"}
    with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
        persistence.require_recorded_construction(
            dict(config, lambda_l=.5), recorded["learner_config"], "learner_config", "D_K10")
    # A D_K1 snapshot differs from the recorded D1280 fit in its three declared fields and no more.
    k1 = production_shared.config_snapshot(b01.make_config("D_K1", lanes(16), SEEDS[0]))
    assert set(persistence.require_recorded_construction(
        k1, recorded["learner_config"], "learner_config", "D_K1")) == set(
            persistence.ARM_OVERRIDES["D_K1"])
    with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
        persistence.require_recorded_construction(
            k1, recorded["learner_config"], "learner_config", "D_K10")


def test_plan_guard_admits_exactly_the_six_planned_fits():
    for arm in persistence.PERSISTENCE_ARMS:
        for seed in SEEDS:
            persistence.plan_guard(arm, seed)
    for arm, seed in (("D_K10", 773103), ("D_K1", 772603), ("D1280", SEEDS[0]),
                      ("CF", SEEDS[0]), ("D_K5", SEEDS[0])):
        with pytest.raises(SystemExit):
            persistence.plan_guard(arm, seed)


def test_the_wall_plans_are_the_d1280_plan_and_twice_it():
    assert persistence.WALL_PLANS["D_K10"] == matched.WALL_PLANS["D1280"]
    assert persistence.WALL_PLANS["D_K1"] == 2 * matched.WALL_PLANS["D1280"]


# ---------------------------------------------------------------------------
# the behaviour measures, on series with a known answer
# ---------------------------------------------------------------------------


def as_series(values):
    """One (lane, agent, dimension) series as the capture's [steps, lanes, agents, dims] block."""
    return np.asarray(values, dtype=np.float64).reshape(-1, 1, 1, 1)


def test_autocorrelation_of_an_ar1_series_is_its_known_coefficient():
    phi, steps = .8, 40000
    noise = np.random.default_rng(11).standard_normal(steps)
    values = np.empty(steps)
    values[0] = noise[0]
    for t in range(1, steps):
        values[t] = phi * values[t - 1] + noise[t]
    reading = persistence.autocorrelation(as_series(values), lags=(1, 2, 5, 9, 10, 20))
    assert reading["action_series"] == reading["action_series_used"] == 1
    assert reading["action_series_skipped"] == 0
    for lag in (1, 2, 5, 9, 10, 20):
        assert reading["action_autocorrelation"][str(lag)] == pytest.approx(phi ** lag, abs=.03)


def test_autocorrelation_of_a_held_mode_series_falls_off_with_the_holding_length():
    """A value redrawn every ten steps and held: r(h) = 1 - h/10 for h < 10, and zero beyond."""
    period, blocks = 10, 4000
    draws = np.random.default_rng(3).standard_normal(blocks)
    values = np.repeat(draws, period)
    reading = persistence.autocorrelation(as_series(values), lags=(1, 2, 5, 9, 10, 20))
    for lag in (1, 2, 5, 9):
        assert reading["action_autocorrelation"][str(lag)] == pytest.approx(1 - lag / period, abs=.05)
    for lag in (10, 20):
        assert reading["action_autocorrelation"][str(lag)] == pytest.approx(0., abs=.05)
    # The same draws with no holding at all: the mode is redrawn every step.
    single = persistence.autocorrelation(as_series(draws), lags=(1, 5))
    for lag in (1, 5):
        assert single["action_autocorrelation"][str(lag)] == pytest.approx(0., abs=.05)


def test_autocorrelation_skips_a_constant_series_and_counts_it():
    steps = 50
    actions = np.zeros((steps, 1, 2, 1))
    actions[:, 0, 0, 0] = .1  # exactly constant: skipped
    actions[:, 0, 1, 0] = np.arange(steps) % 2  # alternating: r(1) = -1, r(2) = +1
    reading = persistence.autocorrelation(actions, lags=(1, 2, 60))
    assert reading["action_series"] == 2 and reading["action_series_used"] == 1
    assert reading["action_series_skipped"] == 1
    assert reading["action_autocorrelation"]["1"] == pytest.approx(-1., abs=.05)
    assert reading["action_autocorrelation"]["2"] == pytest.approx(1., abs=.05)
    assert reading["action_autocorrelation"]["60"] is None  # a lag longer than the rollout
    every = np.zeros((steps, 1, 1, 1))
    empty = persistence.autocorrelation(every, lags=(1,))
    assert empty["action_autocorrelation"]["1"] is None and empty["action_series_used"] == 0


def synthetic_positions(tracks):
    """[steps, lanes, agents, 3] from one (x, y, z) track per agent of a single lane."""
    steps = len(tracks[0])
    positions = np.zeros((steps, 1, len(tracks), 3))
    for agent, track in enumerate(tracks):
        positions[:, 0, agent, :] = np.asarray(track, dtype=np.float64)
    return positions


def test_cells_visited_and_path_length_on_a_synthetic_path():
    moving = [(0., 0., 0.), (60., 0., 0.), (120., 0., 0.), (120., 0., 0.), (130., 0., 0.)]
    still = [(10., 10., 0.)] * 5
    positions = synthetic_positions([moving, still])
    env_steps = np.arange(5, dtype=np.int64).reshape(5, 1)
    reading = persistence.displacement_measures(positions, env_steps, cell_metres=50.)
    assert reading["episode_series"] == 2  # one episode, two UAVs
    assert reading["cells_visited_mean"] == pytest.approx((3 + 1) / 2)
    assert reading["cells_visited_max"] == 3
    assert reading["path_length_metres_mean"] == pytest.approx((60. + 60. + 0. + 10.) / 2)
    assert reading["net_displacement_metres_mean"] == pytest.approx(130. / 2)
    assert reading["path_over_net_displacement_mean"] == pytest.approx(1.)  # the still UAV is excluded
    assert reading["net_displacement_zero_series"] == 1
    # A second episode inside the same rollout is segmented by the collector's own step counter.
    two = np.concatenate([positions, positions])
    counters = np.concatenate([env_steps, env_steps])
    split = persistence.displacement_measures(two, counters, cell_metres=50.)
    assert split["episode_series"] == 4 and split["cells_visited_mean"] == pytest.approx(2.)
    assert split["path_length_metres_mean"] == pytest.approx(65.)


def test_cells_are_fifty_metre_squares_in_x_and_y():
    track = [(0., 0., 0.), (49.9, 49.9, 999.), (50., 0., 0.), (0., 50., 0.)]
    positions = synthetic_positions([track])
    env_steps = np.arange(4, dtype=np.int64).reshape(4, 1)
    reading = persistence.displacement_measures(positions, env_steps, cell_metres=50.)
    assert reading["cells_visited_mean"] == 3.  # (0,0) twice, then (1,0) and (0,1)


def test_skill_change_and_decision_fractions():
    team = np.array([[0], [0], [1], [1], [2]], dtype=np.int64)
    agents = np.array([[[0, 1]], [[0, 2]], [[3, 2]], [[3, 2]], [[3, 2]]], dtype=np.int64)
    env_steps = np.array([[0], [1], [2], [3], [4]], dtype=np.int64)
    reading = persistence.skill_change_measures(team, agents, env_steps)
    assert reading["skill_change_comparisons"] == 4
    assert reading["team_skill_change_fraction"] == pytest.approx(2 / 4)
    assert reading["agent_skill_change_fraction"] == pytest.approx(2 / 8)
    # A step whose predecessor belongs to the previous episode is never compared: the counter is
    # back at zero on the third step, so that step's comparison with the second is dropped.
    fresh = np.array([[0], [1], [0], [1], [2]], dtype=np.int64)
    reading = persistence.skill_change_measures(team, agents, fresh)
    assert reading["skill_change_comparisons"] == 3
    assert reading["team_skill_change_fraction"] == pytest.approx(1 / 3)  # 1->1 dropped, 1->2 kept
    buffer = [{"team_decision": np.array([True, False]),
               "sampled": np.array([[True, True], [False, False]])},
              {"team_decision": np.array([False, False]),
               "sampled": np.array([[False, True], [False, False]])}]
    decisions = persistence.decision_measures(buffer)
    assert decisions["team_decision_fraction"] == pytest.approx(.25)
    assert decisions["agent_sampled_fraction"] == pytest.approx(3 / 8)
    assert decisions["decision_steps_recorded"] == 2
    assert persistence.decision_measures([{"team_decision": None, "sampled": None}]) == {
        "team_decision_fraction": None, "agent_sampled_fraction": None, "decision_steps_recorded": 0}


class StubAgent:
    """A learner-shaped stub: `step` on the class, as `HMASDAgent` has it, and this host's widths."""

    def __init__(self, n_users=N_USERS):
        self.config = SimpleNamespace(n_agents=N_UAVS, n_users=n_users, state_dim=STATE_DIM)
        self.calls, self.handed = [], []

    def step(self, states, observations, env_steps, dones, **kwargs):
        self.calls.append((states, env_steps, kwargs))
        actions = np.arange(2 * N_UAVS * 3, dtype=np.float32).reshape(2, N_UAVS, 3)
        self.handed.append(actions)
        return actions, None, {"team_skills": np.zeros(2, dtype=np.int64),
                               "agent_skills": np.zeros((2, N_UAVS), dtype=np.int64),
                               "d2_team_decision": np.ones(2, dtype=bool),
                               "d2_sampled_mask": np.ones((2, N_UAVS), dtype=bool)}


def test_the_capture_wraps_one_instance_and_leaves_no_trace_behind():
    """No learner at all: a stub with the frozen call signature and this host's widths."""
    agent, summary = StubAgent(), {}
    capture = persistence.BehaviourCapture(summary, horizon=2)
    capture.attach(agent)
    assert "step" in vars(agent)  # an instance attribute; the class is untouched
    assert vars(StubAgent)["step"] is StubAgent.step
    assert summary["behaviour_capture"]["steps_per_rollout"] == 2
    states = np.zeros((2, STATE_DIM))
    for t in range(2):
        states = states + 10.
        returned = agent.step(states, None, np.array([t, t]), np.zeros(2, dtype=bool),
                              deterministic=False, return_step_data=True, build_infos=False)
        assert returned[0] is agent.handed[-1]  # the very array the collector hands the environments
    assert len(agent.calls) == 2 and capture.calls == 2
    assert [row["rollout"] for row in summary["behaviour"]] == [1]
    assert summary["behaviour_capture"]["agent_step_calls"] == 2
    assert summary["behaviour"][0]["team_decision_fraction"] == 1.
    capture.detach()
    assert "step" not in vars(agent) and agent.step.__func__ is StubAgent.step
    agent.step(states, None, np.array([0, 0]), np.zeros(2, dtype=bool))
    assert capture.calls == 2 and len(agent.calls) == 3  # nothing is recorded once it is off
    capture.detach()  # idempotent

    with pytest.raises(ValueError, match="not the configured state_dim"):
        persistence.BehaviourCapture({}, horizon=2).attach(StubAgent(n_users=1))


def test_diagnostics_read_the_coordinator_records_of_a_published_d1280_fit():
    """The reported per-rollout records exist under those names in an actually published fit."""
    recorded = json.loads(persistence.RECORDED_FITS[SEEDS[0]].read_text(encoding="utf-8"))
    reading = persistence.diagnostics(recorded)
    for rollout in persistence.DIAGNOSTIC_ROLLOUTS:
        entry = reading[str(rollout)]
        for name in ("coordinator_policy_loss", "coordinator_value_loss", "team_skill_entropy",
                     "agent_skill_entropy", "coordinator_displacement", "discoverer_policy_loss",
                     "actor_displacement", "action_entropy", "training_return_U"):
            assert isinstance(entry[name], float)
        assert entry["segment_length_agent_mean"] == 10.  # the D1280 cadence, from the runner
        assert entry["segment_length_team_mean"] == 10.
    assert isinstance(reading["mean_coordinator_policy_loss"], float)
    assert isinstance(reading["mean_team_skill_entropy"], float)
    assert isinstance(reading["training_return_U_rollouts_35_45"], float)
    parts = scale.displacement_parts(recorded, persistence.ROLLOUTS)
    assert parts["network_part"] is not None and "failure" not in parts


def test_the_published_references_are_read_by_their_own_objects_validators():
    """The actual stage-1 D1280 and B05 CF_S summaries, on the real host geometry."""
    for seed in SEEDS:
        recorded = json.loads(persistence.RECORDED_FITS[seed].read_text(encoding="utf-8"))
        arm, scores = persistence.reference_endpoint(recorded)
        assert arm == "D1280" and set(scores) == set(persistence.PANEL_ROLLOUTS)
        persistence.bind()
        flat = json.loads(
            (ROOT / f"runs/flexible_skill_duration/b05_s_{seed}_a01/summary.json").read_text(
                encoding="utf-8"))
        arm, scores = persistence.reference_endpoint(flat)
        assert arm == "CF_S" and set(scores) == set(persistence.PANEL_ROLLOUTS)
        persistence.bind()
    with pytest.raises(ValueError, match="the references are the stage-1 D1280"):
        persistence.reference_endpoint({"block_seed": SEEDS[0], "factorial_arm": "CF"})
    with pytest.raises(ValueError, match="fits of the three blocks"):
        persistence.reference_endpoint({"block_seed": 773103})


def test_every_recorded_measure_carries_a_definition():
    for name in ("action_autocorrelation", "executed_actions", "cells_visited", "path_length",
                 "net_displacement", "path_over_net_displacement", "skill_change_fraction",
                 "decision_fraction", "state_layout"):
        assert isinstance(persistence.DEFINITIONS[name], str) and persistence.DEFINITIONS[name]
    assert "uav_env.py" in persistence.DEFINITIONS["state_layout"]
    assert "run_fsd_baseline_interruption_b01.py:121" in persistence.DEFINITIONS["executed_actions"]
    site = persistence.attachment_site()
    file, line = site.split(" ", 1)[0].split(":")
    assert file == "scripts/run_fsd_persistence_b07.py"
    source = (ROOT / file).read_text(encoding="utf-8").splitlines()
    assert source[int(line) - 1].strip().startswith("agent.step = step")


# ---------------------------------------------------------------------------
# fake fits and `reduce`
# ---------------------------------------------------------------------------


class HostEnv(helpers.Env):
    """The fake host carries Scenario 1's own widths and bounds, so the UAV block can be read.

    The state and observation arrays keep the fake host's constant-per-step values (the fake
    learner asserts them), at Scenario 1's widths: the UAV positions the capture reads are then
    the leading 3 x 6 entries of a 119-entry state, as `MultiUAVEnv._get_state` lays them out.
    """

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
    """The fake learner moves the coordinator optimizer only where the arm has skills.

    Both persistence arms take one coordinator step per PPO epoch, which is what one full-pool
    minibatch per epoch means; the flat CF_S reference trains no coordinator or discriminator.
    """

    def update(self, **kwargs):
        if self.config.n_z == 1:
            saved = {name: getattr(self, name + "_optimizer").step for name in b01.FLAT_ONLY_ZERO}
            for name in saved:
                getattr(self, name + "_optimizer").step = lambda: None
            try:
                return super().update(**kwargs)
            finally:
                for name, step in saved.items():
                    getattr(self, name + "_optimizer").step = step
        losses = super().update(**kwargs)
        for _ in range(int(self.config.ppo_epochs)):
            self.coordinator_optimizer.step()
        return losses


@pytest.fixture
def fakes(monkeypatch, fake_only):
    # The thin entries install their own `base_summary` wrapper on the shared module and only some
    # of them take it off again; this restores the plain one after every test.
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, scale, persistence):
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
        if name in persistence.PERSISTENCE_ARMS:
            assert persistence.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        elif name in matched.ARMS:
            assert matched.run_fit(name, SEEDS[0], 1, None, out, admission=ADMISSION) == 0
        else:
            assert scale.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        _TEMPLATES[name] = json.loads((out / "summary.json").read_text())
    return copy.deepcopy(_TEMPLATES[name])


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = persistence.BLOCKS[seed]
    summary = copy.deepcopy(summary)
    summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                   training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                   evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
    summary["learner_config"]["seed"] = seed
    summary["evaluation_config"]["seed"] = evaluation_seed
    for panel in summary["panels"]:
        values = world_scores(arm, index)
        panel["lane_seeds"] = summary["evaluation_lane_seeds"]
        panel["native_scores_J"] = [float(v) for v in values]
        panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
    summary["evaluation"] = summary["panels"][-1]
    return summary


def supplied(tmp_path):
    new = [placed(template(tmp_path, arm), arm, index)
           for arm in persistence.PERSISTENCE_ARMS for index in range(3)]
    references = [placed(template(tmp_path, "D1280"), "D1280", index) for index in range(3)]
    references += [placed(template(tmp_path, "CF_S"), "CF_S", index) for index in range(3)]
    return new, references


def test_fit_runs_the_frozen_d_route_under_this_identity(tmp_path, fakes):
    for arm in persistence.PERSISTENCE_ARMS:
        summary = template(tmp_path, arm)
        assert summary["status"] == "complete" and summary["object_id"] == persistence.OBJECT_ID
        assert summary["persistence_object"] == persistence.OBJECT_ID
        assert summary["persistence_arm"] == arm and summary["factorial_arm"] == arm
        assert summary["arm"] == "D0"  # the frozen runner's renewal route
        assert summary["admission"] == ADMISSION and summary["primary"] == "J_45"
        assert summary["arm_overrides"] == persistence.ARM_OVERRIDES[arm]
        assert summary["ordinary_wall_plan_seconds"] == persistence.WALL_PLANS[arm]
        assert summary["coordinator_batch_size"] == persistence.ARMS[arm][1]
        caps = persistence.ARM_CAPS[arm]
        for phase in ("learner_config", "evaluation_config"):
            assert (summary[phase]["skill_cap_k_max"], summary[phase]["team_cap_k_Z"]) == caps
            assert summary[phase]["k"] == 10
            differences = summary[f"{phase}_differences_from_recorded_d1280"]
            assert differences["available"] is True
            assert set(differences["differences"]) <= set(persistence.ARM_OVERRIDES[arm]) | set(
                persistence.GEOMETRY_FIELDS)
        assert len(summary["behaviour"]) == persistence.ROLLOUTS
        assert [row["rollout"] for row in summary["behaviour"]] == list(
            range(1, persistence.ROLLOUTS + 1))
        capture = summary["behaviour_capture"]
        assert capture["agent_step_calls"] == persistence.ROLLOUTS * r.HORIZON
        assert capture["finalized_rollouts"] == persistence.ROLLOUTS
        assert capture["lags"] == list(persistence.AUTOCORRELATION_LAGS)
        assert "run_fsd_persistence_b07.py:" in capture["attached_at"]
        row = summary["behaviour"][-1]
        assert row["lanes"] == r.TRAIN_LANES and row["agents"] == r.N_UAVS
        assert row["steps"] == r.HORIZON and row["action_dimensions"] == 3
        assert row["cells_visited_mean"] > 0. and row["path_length_metres_mean"] > 0.
        assert set(persistence.fit_endpoint(summary)) == set(range(5, 50, 5))
    assert persistence.CURRENT == {"persistence_arm": None, "admission": None, "summary": None,
                                   "capture": None}
    assert production_shared.base_summary is not persistence.base_summary  # the wrapper came off
    assert b01.build_learner is persistence._orig_build_learner  # and so did this one
    with pytest.raises(ValueError):  # a reference fit is not one of this object's
        persistence.fit_endpoint(template(tmp_path, "D1280"))


def test_fit_endpoint_refuses_a_fit_that_is_not_the_declared_one(tmp_path, fakes):
    summary = placed(template(tmp_path, "D_K1"), "D_K1", 0)
    for mutate, message in (
            (lambda s: s.update(persistence_object="OTHER"), "not a persistence fit"),
            (lambda s: s.update(persistence_arm="D_K5"), "six planned fits"),
            (lambda s: s.update(block_seed=773103), "six planned fits"),
            (lambda s: s.update(factorial_arm="D_K10"), "arm name"),
            (lambda s: s.update(arm_overrides={}), "declared overrides"),
            (lambda s: s["learner_config"].update(team_cap_k_Z=10), "construction mismatch"),
            (lambda s: s["evaluation_config"].update(skill_cap_k_max=10), "construction mismatch"),
            (lambda s: s["learner_config"].update(k=1), "construction mismatch"),
            (lambda s: s["optimizer_calls"].update(coordinator=3), "coordinator steps"),
            (lambda s: s.update(status="incomplete"), "incomplete or wrong"),
            (lambda s: s["behaviour"].pop(), "one behaviour row per rollout"),
            (lambda s: s.update(behaviour=None), "one behaviour row per rollout")):
        broken = copy.deepcopy(summary)
        mutate(broken)
        with pytest.raises(ValueError, match=message):
            persistence.fit_endpoint(broken)
    recorded = json.loads(persistence.RECORDED_FITS[SEEDS[0]].read_text(encoding="utf-8"))
    extra = copy.deepcopy(summary)
    extra["learner_config"]["lambda_l"] = .5
    with pytest.raises(ValueError, match="not the recorded D1280 fit's construction"):
        persistence.fit_endpoint(extra, recorded=recorded)


def test_this_readers_panel_law_is_the_frozen_readers_where_the_caps_are_the_frozen_ones(tmp_path, fakes):
    summary = placed(template(tmp_path, "D_K10"), "D_K10", 0)
    persistence.bind()
    mine = persistence.persistence_panels(summary)
    frozen = b01.arm_panels(summary)
    assert set(mine) == set(frozen)
    for rollout, values in mine.items():
        assert np.array_equal(values, frozen[rollout])
    # The frozen reader cannot read caps of 1; this object's reader is why it has its own.
    ones = placed(template(tmp_path, "D_K1"), "D_K1", 0)
    persistence.bind()
    with pytest.raises(ValueError, match="arm construction mismatch"):
        b01.arm_panels(ones)
    assert set(persistence.persistence_panels(ones)) == set(range(5, 50, 5))


def test_reduce_reads_both_arms_against_the_published_d1280_fits(tmp_path, fakes):
    new, references = supplied(tmp_path)
    paths = []
    for index, summary in enumerate(new + references):
        path = tmp_path / f"input_{index}.json"
        path.write_text(json.dumps(summary), encoding="utf-8")
        paths.append(str(path))
    out = tmp_path / "reduce"
    assert persistence.main(["reduce", "--summaries", *paths[:6], "--references", *paths[6:],
                             "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete"
    assert not result["invalid_inputs"] and not result["invalid_references"]
    assert result["capture_bit_identical_blocks"] == 3
    assert result["blocks_with_behaviour_read"] == 3
    for index, block in enumerate(result["blocks"]):
        assert block["status"] == "complete"
        assert set(block["arms"]) == set(persistence.PERSISTENCE_ARMS)
        assert block["capture_bit_identical"]["bit_identical"] is True
        assert block["references"]["D1280"]["object_id"] == matched.OBJECT_ID
        assert block["references"]["CF_S"]["object_id"] == scale.OBJECT_ID
        expected = OFFSET["D_K10"][index] - OFFSET["D_K1"][index]
        for name in ("late", "late_35_45", "J45"):  # every panel carries the same offset
            assert block[f"D_K10_minus_D_K1_{name}"] == pytest.approx(expected)
        assert block["behaviour"]["status"] == "read"
        assert set(block["behaviour"]["D_K10"]) == {"early", "late"}
        assert set(block["behaviour"]["lag_autocorrelation_difference_late"]) == {
            str(lag) for lag in persistence.AUTOCORRELATION_LAGS}
        # The fake learner reports no coordinator policy loss, so the structure is what is read
        # here; the real records are read from a published fit in the test below.
        assert set(block["coordinator"]["D_K1"]) == {
            "mean_policy_loss", "mean_team_skill_entropy", "displacement_by_rollout",
            "team_skill_entropy_by_rollout", "actor_displacement_parts"}
        assert set(block["coordinator"]["D_K10"]["actor_displacement_parts"]) == {"1", "45"}
        assert block["training_return_U_rollouts_35_45"]["D_K10"] is not None
    counts = result["blocks_at_or_above_threshold"]
    assert counts["threshold"] == .05
    assert counts["D_K10_minus_D_K1_late"] == int(
        sum(-v >= .05 for v in OFFSET["D_K1"]))  # two of the three blocks
    assert result["D_K10_minus_D_K1_late"]["mean"] == pytest.approx(
        float(np.mean([-v for v in OFFSET["D_K1"]])))
    assert result["batch_launch_sha"] == "synthetic-source"
    assert "no MEI verdict" in result["interpretation_limit"]
    assert result["lag5_autocorrelation_difference_late"]["available_blocks"] == 3


def test_reduce_marks_a_block_whose_capture_is_not_established(tmp_path, fakes):
    new, references = supplied(tmp_path)
    new[1]["panels"][0]["native_scores_J"][0] += 1e-12  # D_K10 on the second block
    result = persistence.reduce_fits(new, references)
    block = result["blocks"][1]
    assert block["status"] == "complete"  # the fit itself is read
    assert block["capture_bit_identical"] == {"bit_identical": False, "failure": None,
                                              "first_differing_panel": 5}
    assert block["behaviour"]["status"] == "not_read" and "bit-identical" in block["behaviour"]["reason"]
    assert result["capture_bit_identical_blocks"] == 2
    assert result["blocks_with_behaviour_read"] == 2
    assert result["lag5_autocorrelation_difference_late"]["available_blocks"] == 2
    assert result["D_K10_minus_D_K1_late"]["available_blocks"] == 3  # J is still read


def test_reduce_refuses_a_batch_it_cannot_read(tmp_path, fakes):
    new, references = supplied(tmp_path)
    mixed = copy.deepcopy(new)
    mixed[0]["launch_sha"] = "another-source"
    with pytest.raises(ValueError, match="mixed launch shas"):
        persistence.reduce_fits(mixed, references)
    with pytest.raises(ValueError, match="duplicate arm/block"):
        persistence.reduce_fits(new + [copy.deepcopy(new[0])], references)

    foreign = copy.deepcopy(new)
    foreign[0]["persistence_object"] = "FSD_OTHER"
    result = persistence.reduce_fits(foreign, references)
    assert result["status"] == "incomplete"
    assert result["invalid_inputs"][f"{SEEDS[0]}:D_K10"] == "not a fit of this object"
    assert result["blocks"][0]["capture_bit_identical"]["bit_identical"] is False
    assert "missing" in result["blocks"][0]["capture_bit_identical"]["failure"]

    incomplete = copy.deepcopy(new)
    incomplete[3]["status"] = "incomplete"  # a D_K1 fit
    result = persistence.reduce_fits(incomplete, references)
    assert "incomplete or wrong" in result["invalid_inputs"][f"{SEEDS[0]}:D_K1"]
    assert result["blocks"][0]["status"] == "incomplete"

    outside = copy.deepcopy(new)
    outside[3]["learner_config"]["lambda_l"] = .5
    result = persistence.reduce_fits(outside, references)
    assert "not the recorded D1280 fit's construction" in result["invalid_inputs"][f"{SEEDS[0]}:D_K1"]

    without = [s for s in references if s.get("factorial_arm") != "D1280"]
    result = persistence.reduce_fits(new, without)
    assert result["status"] == "incomplete"
    assert all("was not supplied" in text for text in result["invalid_inputs"].values())

    other = copy.deepcopy(references)
    other[0]["factorial_arm"] = "CF"
    result = persistence.reduce_fits(new, other)
    assert result["invalid_references"]
    assert result["blocks"][0]["status"] == "incomplete"


def test_reduce_refuses_two_arms_that_differ_outside_the_declared_overrides(tmp_path, fakes):
    new, references = supplied(tmp_path)
    for summary in new:
        summary["learner_config"]["lambda_l"] = .5  # both arms, so the recorded guard is relaxed
    result = persistence.reduce_fits(new, references)
    assert all("not the recorded D1280" in text for text in result["invalid_inputs"].values())

    new, references = supplied(tmp_path)
    new[0]["host"] = dict(new[0]["host"], n_users=49)  # D_K10 on the first block
    result = persistence.reduce_fits(new, references)
    assert result["blocks"][0]["failure"] == "the two arms differ outside the declared overrides"
    assert result["blocks"][0]["status"] == "incomplete"
    assert result["status"] == "incomplete"
