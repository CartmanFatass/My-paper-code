"""One real tiny-host execution of the flat-input-scale probe, and the affine's reach.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real agent, through the
frozen runner's own learner construction, evaluator construction and evaluation panel. Technical
checks, no result: nothing here asserts the direction or the size of any measured quantity. Kept
apart from the fake-learner tests, whose helper forbids real construction.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

SEEDS = sorted(scale.BLOCKS)
ARM = scale.INPUT_SCALE_ARMS[0]
LANES, HORIZON = 2, 20


@pytest.fixture
def tiny(monkeypatch):
    shared = b01.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", LANES)
    monkeypatch.setattr(shared, "EVAL_LANES", LANES)
    monkeypatch.setattr(shared, "HORIZON", HORIZON)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    return shared


def build_agent(arm, seed, log_dir):
    """One real learner of this object's construction, through the runner's own make_config."""
    shared = b01.shared
    scale.bind()
    scale.CURRENT.update(input_scale_arm=arm)
    try:
        shared.seed_rng(seed)
        envs = shared.e0._make_envs(LANES, seed, shared.N_UAVS, shared.N_USERS, HORIZON)
        config = b01.make_config("CF", envs, seed)
        shared.seed_rng(seed)  # the two constructions draw the same parameters
        agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))
    finally:
        scale.CURRENT.update(input_scale_arm=None)
    return envs, config, agent


def test_real_tiny_probe_takes_no_optimizer_step_and_measures_both_constructions(tmp_path, tiny):
    out = tmp_path / "probe"
    head = scale.shared.e0._git("rev-parse", "HEAD")
    assert scale.main(["probe", "--seed", str(SEEDS[0]), "--launch-sha", head,
                       "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == scale.OBJECT_ID and summary["command"] == "probe"
    assert summary["block_seed"] == SEEDS[0] and summary["evaluation_seed"] == scale.BLOCKS[SEEDS[0]]
    assert summary["optimizer_steps"] == 0
    assert summary["evaluation_episodes"] == 2 * LANES
    assert summary["wall_seconds"] > 0.
    assert summary[scale.BOUNDS_FIELD] == {"area_size": 1000., "height_range": [50., 150.],
                                           "n_uavs": 6, "n_users": 50}
    assert len(summary[scale.AFFINE_FIELD]["offset"]) == 119

    for label in ("unscaled", "scaled"):
        entry = summary["constructions"][label]
        assert entry["optimizer_steps"] == 0
        assert not any(entry["optimizer_calls"].values())
        assert not any(entry["evaluator_optimizer_calls"].values())
        assert entry["evaluation_episodes"] == LANES and entry["evaluation_steps"] == LANES * HORIZON
        assert len(entry["J_init_world_scores"]) == LANES
        assert entry["J_init_mean"] == pytest.approx(float(np.mean(entry["J_init_world_scores"])))
        assert entry["learner_config"]["use_central_snapshot_in_flat_actor"] is True
        assert entry["wall_seconds"] > 0.

        measurements = entry["measurements"]
        obs_dim, state_dim = entry["learner_config"]["obs_dim"], entry["learner_config"]["state_dim"]
        assert measurements["actor_input_dim"] == obs_dim + state_dim + 6 * obs_dim + 6
        assert measurements["actor_calls"] == HORIZON
        assert measurements["actor_rows"] == HORIZON * LANES * 6
        for key in ("first_layer_preactivation_squared_norm_share", "input_squared_norm_share"):
            shares = measurements[key]
            assert set(shares) == {"own_observation", "state", "joint_observations", "ego_one_hot"}
            assert sum(shares.values()) == pytest.approx(1.)
            assert all(0. <= value <= 1. for value in shares.values())
        for gate in ("update", "reset"):
            saturation = measurements["gru_gate_saturation"][gate]
            assert 0. <= saturation["fraction_saturated"] <= 1.
            assert saturation["total_units"] == HORIZON * LANES * 6 * entry["learner_config"]["gru_hidden_size"]
        sensitivity = measurements["mean_action_sensitivity"]
        assert sensitivity["baseline_reproduces_panel_action"] is True
        assert sensitivity["captured_steps"] == HORIZON  # stride 1 at this tiny horizon
        assert set(sensitivity["mean_absolute_change_in_mean_action"]) == {
            "own_observation_relative", "own_observation_additive", "ego_one_hot"}
        assert all(value >= 0. for value in sensitivity["mean_absolute_change_in_mean_action"].values())

    assert summary["constructions"]["unscaled"]["central_snapshot_state_affine"] is None
    assert summary["constructions"]["unscaled"]["input_scale_arm"] is None
    assert summary["constructions"]["scaled"]["input_scale_arm"] == ARM
    # Both constructions start from the same seed, so any difference at all is the affine reaching
    # the frozen evaluation route through `_apply_central_input`. Direction and size are not asserted.
    measured = [summary["constructions"][label]["measurements"][
        "first_layer_preactivation_squared_norm_share"]["state"] for label in ("unscaled", "scaled")]
    assert measured[0] != measured[1]
    assert (summary["constructions"]["unscaled"]["J_init_mean"]
            != summary["constructions"]["scaled"]["J_init_mean"])
    assert scale.probe_endpoint(summary) == {
        label: summary["constructions"][label]["J_init_mean"] for label in ("unscaled", "scaled")}
    assert scale.CURRENT == {"input_scale_arm": None, "admission": None, "summary": None}


def test_scaled_and_unscaled_differ_only_through_the_affine(tmp_path, tiny):
    """A pre-transformed central input in the unconfigured learner reproduces the scaled one."""
    _envs, plain_config, plain = build_agent(None, SEEDS[0], tmp_path / "plain")
    _envs, scaled_config, scaled = build_agent(ARM, SEEDS[0], tmp_path / "scaled")
    assert not hasattr(plain_config, scale.AFFINE_FIELD)
    offset, values = getattr(scaled_config, scale.AFFINE_FIELD)
    assert plain.skill_discoverer.use_central_state_affine is False
    assert scaled.skill_discoverer.use_central_state_affine is True
    for left, right in zip(plain.skill_discoverer.parameters(), scaled.skill_discoverer.parameters()):
        assert torch.equal(left, right)
    assert list(plain.skill_discoverer.state_dict()) == list(scaled.skill_discoverer.state_dict())

    state_dim, obs_dim = int(plain_config.state_dim), int(plain_config.obs_dim)
    generator = torch.Generator().manual_seed(SEEDS[0])
    batch = LANES * 6
    observation = torch.randn(batch, obs_dim, generator=generator)
    central = torch.rand(batch, state_dim + 6 * obs_dim + 6, generator=generator)
    central[:, :state_dim] *= 1000.  # raw metres, as the collector's snapshot delivers them
    hidden = torch.zeros(batch, int(plain_config.gru_hidden_size))
    skill = torch.zeros(batch, dtype=torch.long)
    pre = central.clone()
    pre[:, :state_dim] = ((pre[:, :state_dim] - torch.tensor(offset)) / torch.tensor(values))

    with torch.no_grad():
        scaled_actions = scaled.skill_discoverer.forward(
            observation, skill, hidden, deterministic=True, central_input=central)
        manual_actions = plain.skill_discoverer.forward(
            observation, skill, hidden, deterministic=True, central_input=pre)
        raw_actions = plain.skill_discoverer.forward(
            observation, skill, hidden, deterministic=True, central_input=central)
    assert torch.equal(scaled_actions[0], manual_actions[0])
    assert torch.equal(scaled_actions[3], manual_actions[3])
    assert not torch.equal(scaled_actions[0], raw_actions[0])


def test_the_probe_makes_every_optimizer_step_raise(tmp_path, tiny):
    _envs, _config, agent = build_agent(ARM, SEEDS[0], tmp_path / "forbidden")
    restore = scale._forbid_optimizer_steps(agent)
    assert restore, "the flat route still trains an actor and a critic"
    try:
        for optimizer, _original in restore:
            with pytest.raises(RuntimeError, match="optimizer step"):
                optimizer.step()
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    assert all(optimizer.step is original for optimizer, original in restore)


def test_the_probe_refuses_a_block_outside_the_plan(tmp_path, tiny):
    with pytest.raises(SystemExit):
        scale.run_probe(772603, tmp_path / "refused")
    assert not (tmp_path / "refused").exists()
