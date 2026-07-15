from types import SimpleNamespace

import numpy as np

from envs.pettingzoo.cooperative_two_timescale_sparse import (
    CooperativeTwoTimescaleSparseEnv,
)
from ha_ctse_process.config_r38_two_timescale_sparse import Config
from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario


def config():
    return SimpleNamespace(
        r38_world_size=6.0,
        r38_action_scale=0.5,
        r38_zone_radius=0.75,
        r38_anchor_required_steps=40,
        r38_shuttle_stages=4,
        max_steps=200,
    )


def zeros():
    return {
        "agent_0": np.zeros(2, dtype=np.float32),
        "agent_1": np.zeros(2, dtype=np.float32),
    }


def test_reset_is_exchangeable_and_hides_attempt_state_from_actor():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=7)
    anchor_agent_ids = set()
    for seed in range(32):
        obs, _ = env.reset(seed=seed)
        distances = np.linalg.norm(env.positions - env.anchor, axis=1)
        anchor_agent_ids.add(int(np.argmin(distances)))
    assert anchor_agent_ids == {0, 1}
    assert env.get_obs_dim() == 10
    assert env.get_state_dim() == 10
    assert obs["agent_0"].shape == (10,)
    assert obs["agent_1"].shape == (10,)
    assert env.action_space("agent_0").shape == (2,)
    assert np.all(np.isfinite(np.stack(list(obs.values()))))


def test_simultaneous_anchor_and_four_stage_shuttle_pays_once():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=1)
    env.reset(seed=1)
    env.positions[:] = np.asarray([[3.0, 3.0], [1.0, 3.0]], dtype=np.float32)
    _, rewards, terms, truncs, infos = env.step(zeros())
    assert infos["agent_0"]["reward_info"]["r38_shuttle_stage_max"] == 1.0
    for direction in (1.0, -1.0, 1.0):
        for _ in range(8):
            actions = zeros()
            actions["agent_1"][0] = direction
            _, rewards, terms, truncs, infos = env.step(actions)
    while not any(terms.values()):
        _, rewards, terms, truncs, infos = env.step(zeros())
    metrics = infos["agent_0"]["reward_info"]
    assert metrics["r38_short_duty_complete"] == 1.0
    assert metrics["r38_long_duty_complete"] == 1.0
    assert metrics["r38_full_cycle_success"] == 1.0
    assert rewards == {"agent_0": 1.0, "agent_1": 1.0}
    assert all(terms.values()) and not any(truncs.values())


def test_holder_break_resets_before_visitor_contact_and_cannot_rearm_same_step():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=2)
    env.reset(seed=2)
    env.positions[:] = np.asarray([[3.0, 3.0], [1.0, 3.0]], dtype=np.float32)
    env.step(zeros())
    env.positions[0] = np.asarray([3.7, 3.0], dtype=np.float32)
    actions = zeros()
    actions["agent_0"][:] = (1.0, 0.0)
    _, rewards, terms, _, infos = env.step(actions)
    metrics = infos["agent_0"]["reward_info"]
    assert env.active_holder == -1
    assert metrics["r38_short_duty_complete"] == 0.0
    assert metrics["r38_long_duty_complete"] == 0.0
    assert metrics["r38_full_cycle_success"] == 0.0
    assert rewards == {"agent_0": 0.0, "agent_1": 0.0}
    assert not any(terms.values())


def test_locked_holder_cannot_advance_the_shuttle_duty():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=4)
    env.reset(seed=4)
    env.positions[:] = np.asarray([[3.0, 3.0], [2.0, 3.0]], dtype=np.float32)
    env.step(zeros())
    assert env.active_holder == 0
    env.positions[:] = np.asarray([[1.0, 3.0], [3.0, 3.0]], dtype=np.float32)
    _, rewards, terms, _, infos = env.step(zeros())
    metrics = infos["agent_0"]["reward_info"]
    assert env.active_holder == -1
    assert env.shuttle_stage == 0
    assert metrics["r38_full_cycle_success"] == 0.0
    assert rewards == {"agent_0": 0.0, "agent_1": 0.0}
    assert not any(terms.values())


def test_agent_swap_is_transition_and_reward_equivariant():
    env_a = CooperativeTwoTimescaleSparseEnv(config=config(), seed=3)
    env_b = CooperativeTwoTimescaleSparseEnv(config=config(), seed=3)
    env_a.reset(seed=3)
    env_b.reset(seed=3)
    env_a.positions[:] = np.asarray([[3.0, 3.0], [2.0, 3.0]], dtype=np.float32)
    env_b.positions[:] = env_a.positions[::-1]
    actions_a = {
        "agent_0": np.zeros(2, np.float32),
        "agent_1": np.asarray([-1.0, 0.0], np.float32),
    }
    actions_b = {
        "agent_0": actions_a["agent_1"],
        "agent_1": actions_a["agent_0"],
    }
    out_a = env_a.step(actions_a)
    out_b = env_b.step(actions_b)
    assert np.allclose(out_a[0]["agent_0"], out_b[0]["agent_1"])
    assert np.allclose(out_a[0]["agent_1"], out_b[0]["agent_0"])
    assert out_a[1]["agent_0"] == out_b[1]["agent_1"]
    assert (
        out_a[4]["agent_0"]["reward_info"]["r38_shuttle_stage_max"]
        == out_b[4]["agent_1"]["reward_info"]["r38_shuttle_stage_max"]
    )


def test_factory_adapter_preserves_sparse_shared_reward_and_shapes():
    assert normalize_scenario("cts") == "cooperative_two_timescale_sparse"
    env = make_env(
        Config,
        EnvSpec(scenario="cooperative_two_timescale_sparse", seed=11),
    )()
    obs, info = env.reset(seed=11)
    assert obs.shape == (2, 10)
    assert info["state"].shape == (10,)
    next_obs, reward, terminated, truncated, step_info = env.step(
        np.zeros((2, 2), dtype=np.float32)
    )
    assert next_obs.shape == (2, 10)
    assert reward == 0.0
    assert not terminated and not truncated
    reward_info = step_info["reward_info"]
    assert reward_info["r38_sparse_reward"] == 0.0
    assert reward_info["intrinsic_reward"] == 0.0
