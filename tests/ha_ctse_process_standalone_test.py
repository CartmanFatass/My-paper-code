from types import SimpleNamespace

import numpy as np
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.standalone_agent import Segment, StandaloneProcessAgent


def make_process_config(**overrides):
    cfg = SimpleNamespace(
        n_z=3,
        state_dim=8,
        skill_lifetime_candidates=(1, 2),
        hidden_size=16,
        gamma=0.99,
        clip_epsilon=0.2,
        process_reward_coef=1.0,
        normalize_process_outcomes=False,
        lr_discoverer_actor=1e-3,
        lr_coordinator=1e-3,
        lr_process_encoder=1e-3,
        process_encoder_embedding_dim=8,
        opt_compact_dim=8,
        opt_num_prototypes=2,
        opt_use_sparsemax=True,
        team_code_dim=8,
        num_team_codes=2,
        team_bridge_type="stochastic",
        high_entropy_coef=0.01,
        low_entropy_coef=0.01,
        edit_penalty_alpha=0.0,
        switch_penalty_beta=0.0,
        opt_cd_coef=0.0,
        opt_cmi_coef=0.0,
        scenario="base",
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def make_args(**overrides):
    args = SimpleNamespace(
        config="config_test",
        preset="",
        scenario="base",
        seed=1,
        skill_interval=2,
        eval_max_steps=3,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def make_agent(config=None, num_envs=1):
    return StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=config or make_process_config(),
        device="cpu",
        action_space_type="discrete",
        num_envs=num_envs,
    )


def test_standalone_checkpoint_roundtrip_restores_networks(tmp_path):
    cfg = make_process_config()
    args = make_args()
    agent = make_agent(cfg)
    expected = next(agent.high.parameters()).detach().clone()

    ckpt_path = tmp_path / "standalone.pt"
    process_train.save_checkpoint(ckpt_path, agent, args, cfg, total_steps=12, update_idx=3)

    restored = make_agent(cfg)
    with torch.no_grad():
        next(restored.high.parameters()).add_(1.0)
    total_steps, update_idx = process_train.load_checkpoint(ckpt_path, restored)

    assert total_steps == 12
    assert update_idx == 3
    torch.testing.assert_close(next(restored.high.parameters()).detach(), expected)


def test_process_update_injects_reward_into_matching_rollout_agent():
    cfg = make_process_config(process_reward_coef=1.0)
    agent = make_agent(cfg)
    segment = Segment(
        env_id=0,
        agent_id=1,
        skill=0,
        duration_idx=0,
        start_step=0,
        high_obs=np.zeros(4, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        high_state=np.zeros(8, dtype=np.float32),
        high_joint_obs=np.zeros((2, 4), dtype=np.float32),
    )
    segment.append(
        obs=np.zeros(4, dtype=np.float32),
        action=np.array([1], dtype=np.float32),
        reward=0.25,
        next_obs=np.ones(4, dtype=np.float32),
        rollout_idx=0,
        reward_info={"coverage_ratio": 0.2, "qos_satisfaction": 0.1},
    )
    segment.append(
        obs=np.ones(4, dtype=np.float32),
        action=np.array([2], dtype=np.float32),
        reward=0.5,
        next_obs=np.ones(4, dtype=np.float32) * 2.0,
        rollout_idx=1,
        reward_info={"coverage_ratio": 0.3, "qos_satisfaction": 0.2},
    )
    agent.segments.completed = [segment]
    rollout = SimpleNamespace(
        rewards=[
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
        ]
    )

    metrics = agent.process_update(rollout)

    assert metrics["process_segments"] == 1.0
    assert rollout.rewards[0][0] == 0.0
    assert rollout.rewards[1][0] == 0.0
    assert rollout.rewards[0][1] != 0.0
    assert rollout.rewards[1][1] != 0.0


class DummyEvalEnv:
    obs_dim = 4
    action_dim = 3
    n_uavs = 2
    state_dim = 8

    def __init__(self):
        self.step_count = 0

    def reset(self, seed=None):
        self.step_count = 0
        obs = np.zeros((self.n_uavs, self.obs_dim), dtype=np.float32)
        return obs, {"state": np.zeros(self.state_dim, dtype=np.float32)}

    def step(self, actions):
        self.step_count += 1
        obs = np.full((self.n_uavs, self.obs_dim), self.step_count, dtype=np.float32)
        info = {
            "next_state": np.full(self.state_dim, self.step_count, dtype=np.float32),
            "reward_info": {
                "coverage_ratio": 0.5,
                "qos_satisfaction": 0.25,
                "system_throughput_mbps": 7.0,
                "battery_min_ratio": 0.8,
            }
        }
        return obs, 1.0, self.step_count >= 2, False, info

    def close(self):
        return None


def test_standalone_eval_restores_runtime_state(monkeypatch):
    cfg = make_process_config(scenario="base")
    args = make_args(eval_max_steps=3)
    agent = make_agent(cfg)
    agent.active_skills[:] = np.array([[2, 1]])
    agent.duration_remaining[:] = np.array([[4, 5]])
    agent.skill_age[:] = np.array([[3, 2]])
    agent.has_active_skill[:] = True
    active_before = agent.active_skills.copy()
    duration_before = agent.duration_remaining.copy()
    age_before = agent.skill_age.copy()
    has_active_before = agent.has_active_skill.copy()
    segments_before = agent.segments

    monkeypatch.setattr(process_train, "create_env", lambda *args, **kwargs: DummyEvalEnv())
    metrics = process_train.evaluate(agent, cfg, args, episodes=1, total_steps=10)

    assert metrics["reward_mean"] == 2.0
    assert metrics["coverage"] == 0.5
    np.testing.assert_array_equal(agent.active_skills, active_before)
    np.testing.assert_array_equal(agent.duration_remaining, duration_before)
    np.testing.assert_array_equal(agent.skill_age, age_before)
    np.testing.assert_array_equal(agent.has_active_skill, has_active_before)
    assert agent.segments is segments_before
