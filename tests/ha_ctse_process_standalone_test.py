from types import SimpleNamespace

import numpy as np
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process import checkpoint_io
from ha_ctse_process import standalone_evaluation as process_evaluation
from ha_ctse_process.standalone_agent import StandaloneProcessAgent
from ha_ctse_process.standalone_ar_selection import StandaloneARSelectionMixin
from ha_ctse_process.standalone_lifecycle import StandaloneLifecycleMixin
from ha_ctse_process.standalone_low_inference import StandaloneLowInferenceMixin
from ha_ctse_process.standalone_segments import Rollout, Segment
from ha_ctse_process.topology_potential import TopologyPotentialShaper


def make_process_config(**overrides):
    cfg = SimpleNamespace(
        n_z=3,
        state_dim=8,
        skill_lifetime_candidates=(1, 2),
        hidden_size=16,
        gamma=0.99,
        clip_epsilon=0.2,
        low_clip_epsilon=0.1,
        process_reward_coef=1.0,
        process_reward_warmup_steps=0,
        process_shortcut_margin=0.1,
        process_shortcut_margin_coef=0.5,
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


def make_agent(config=None, num_envs=1, action_space_type="discrete"):
    return StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=config or make_process_config(),
        device="cpu",
        action_space_type=action_space_type,
        num_envs=num_envs,
    )


def test_lifecycle_reset_mixin_owns_methods_and_preserves_reset_state():
    agent = make_agent(num_envs=2)
    method_names = (
        "reset_env_state",
        "reset_all_policy_state",
        "_team_transition_xi",
        "_team_transition_record_check",
        "_team_transition_clear_rollout_buffers",
    )
    assert StandaloneProcessAgent.__mro__[:4] == (
        StandaloneProcessAgent,
        StandaloneARSelectionMixin,
        StandaloneLifecycleMixin,
        StandaloneLowInferenceMixin,
    )
    for name in method_names:
        assert getattr(StandaloneProcessAgent, name) is getattr(StandaloneLifecycleMixin, name)

    env_id = 1
    agent.episode_steps[env_id] = 9
    agent.episode_ids[env_id] = 4
    agent.steps_to_check[env_id] = 3
    agent.duration_remaining[env_id, :] = 2
    agent.active_skills[env_id, :] = 1
    agent.active_duration_indices[env_id, :] = 1
    agent.skill_age[env_id, :] = 5
    agent.has_active_skill[env_id, :] = True
    agent.active_team_codes[env_id] = 1
    agent.team_intent_remaining[env_id] = 2
    agent.team_intent_age[env_id] = 3
    agent.low_actor_hxs[env_id, :, :] = 1.0
    agent.low_critic_hxs[env_id, :, :] = 1.0
    agent._last_low_context[env_id] = {"retained": 1}
    agent._team_transition_open[env_id] = object()
    agent._team_transition_env_steps[env_id] = 6

    agent.reset_env_state(env_id)

    assert agent.episode_steps[env_id] == 0
    assert agent.episode_ids[env_id] == 5
    assert agent.steps_to_check[env_id] == 0
    for state in (
        agent.duration_remaining[env_id],
        agent.active_skills[env_id],
        agent.active_duration_indices[env_id],
        agent.skill_age[env_id],
        agent.low_actor_hxs[env_id],
        agent.low_critic_hxs[env_id],
    ):
        assert np.count_nonzero(state) == 0
    assert not np.any(agent.has_active_skill[env_id])
    assert agent.active_team_codes[env_id] == 0
    assert agent.team_intent_remaining[env_id] == 0
    assert agent.team_intent_age[env_id] == 0
    assert agent._last_low_context[env_id] is None
    assert agent._team_transition_open[env_id] is None
    assert agent._team_transition_env_steps[env_id] == 0

    segments_before = agent.segments
    episode_ids_before = agent.episode_ids.copy()
    agent._team_transition_closed.append(object())
    agent._team_transition_env_steps[:] = 5
    agent.reset_all_policy_state()

    assert agent.segments is not segments_before
    np.testing.assert_array_equal(agent.episode_ids, episode_ids_before)
    assert agent._team_transition_open == [None, None]
    assert agent._team_transition_closed == []
    np.testing.assert_array_equal(
        agent._team_transition_env_steps, np.zeros(2, dtype=np.int64)
    )

    agent.r30_enabled = True
    try:
        agent.reset_all_policy_state()
    except RuntimeError as error:
        assert str(error) == "R30 policy state cannot be reset at a PPO update boundary"
    else:
        raise AssertionError("R30 reset guard did not raise")


def test_ar_selection_mixin_owns_roster_prefix_and_kl_helpers():
    method_names = (
        "_ar_prefix_dim",
        "_empty_ar_prefix",
        "_updated_ar_prefix",
        "_roster_age_scale",
        "_build_roster_ar_prefix",
        "_build_shuffled_roster_ar_prefix",
        "_segment_ar_prefix_tensor",
        "_roster_selection_metrics",
        "_categorical_kl",
    )
    for name in method_names:
        assert getattr(StandaloneProcessAgent, name) is getattr(
            StandaloneARSelectionMixin, name
        )

    agent = make_agent()
    agent.n_agents = 3
    agent.high.ar_prefix_dim = 21
    agent.ar_prefix_mode = "roster"
    skills = np.array([0, 1, 2], dtype=np.int64)
    ages = np.array([0.0, 1.0, 4.0], dtype=np.float32)
    mask = np.array([True, True, True], dtype=np.bool_)

    empty = agent._empty_ar_prefix()
    assert empty.shape == (1, 21)
    assert empty.dtype == torch.float32
    assert empty.device == agent.device

    prefix = agent._build_roster_ar_prefix(0, skills, ages, mask, [1])
    assert prefix.dtype == torch.float32
    torch.testing.assert_close(prefix[0, :3], torch.tensor([0.0, 2.0 / 3.0, 1.0 / 3.0]))
    torch.testing.assert_close(prefix[0, 7], torch.tensor(1.0 / 3.0))
    torch.testing.assert_close(prefix[0, 11], torch.tensor(1.0 / 3.0))
    torch.testing.assert_close(prefix[0, 16], torch.tensor(1.0 / 6.0))
    torch.testing.assert_close(prefix[0, 20], torch.tensor(1.0 / 3.0))
    updated = agent._updated_ar_prefix(prefix, 0)
    torch.testing.assert_close(prefix[0, 0], torch.tensor(0.0))
    torch.testing.assert_close(updated[0, 0], torch.tensor(1.0 / 3.0))
    assert not torch.equal(prefix, agent._build_shuffled_roster_ar_prefix(0, skills, ages, mask, [1]))

    segment = Segment(
        env_id=0,
        agent_id=0,
        skill=1,
        duration_idx=0,
        start_step=0,
        high_obs=np.zeros(4, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        roster_active_skills_start=skills,
        roster_active_ages_start=ages,
        roster_active_mask_start=mask,
    )
    rebuilt = agent._segment_ar_prefix_tensor([segment])
    torch.testing.assert_close(rebuilt[0], agent._build_roster_ar_prefix(0, skills, ages, mask)[0])
    metrics = agent._roster_selection_metrics([segment])
    assert metrics == {
        "selection_independence_available": 1.0,
        "selection_same_skill_rate": 1.0,
        "selection_independence_null_rate": 0.75,
        "selection_independence_deficit": 0.25,
    }

    logits_p = torch.tensor([[0.0, 1.0], [2.0, -1.0]], dtype=torch.float64)
    logits_q = torch.tensor([[1.0, 0.0], [2.0, -1.0]], dtype=torch.float64)
    kl = agent._categorical_kl(logits_p, logits_q)
    assert kl.shape == (2,)
    assert kl.dtype == torch.float32
    assert kl[0] > 0.0
    torch.testing.assert_close(kl[1], torch.tensor(0.0))


def test_batched_low_deterministic_inference_matches_scalar_path():
    rng = np.random.default_rng(17)
    scalar_agent = make_agent(num_envs=2)
    batched_agent = make_agent(num_envs=2)
    batched_agent.low.load_state_dict(scalar_agent.low.state_dict())

    skills = np.array([[0, 2], [1, 0]], dtype=np.int64)
    team_codes = np.array([0, 1], dtype=np.int64)
    actor_hxs = rng.normal(
        size=(2, 2, scalar_agent.low_rnn_hidden_size)
    ).astype(np.float32)
    critic_hxs = rng.normal(
        size=(2, 2, scalar_agent.low_rnn_hidden_size)
    ).astype(np.float32)
    observations = [
        rng.normal(size=(2, 4)).astype(np.float32),
        rng.normal(size=(2, 4)).astype(np.float32),
    ]
    states = [
        rng.normal(size=8).astype(np.float32),
        rng.normal(size=8).astype(np.float32),
    ]
    for agent in (scalar_agent, batched_agent):
        agent.active_skills[:] = skills
        agent.active_team_codes[:] = team_codes
        agent.has_active_skill[:] = True
        agent.low_actor_hxs[:] = actor_hxs
        agent.low_critic_hxs[:] = critic_hxs

    scalar_rows = [
        scalar_agent.act_low(
            observations[env_id],
            env_id=env_id,
            state=states[env_id],
            deterministic=True,
            return_context=True,
        )
        for env_id in range(2)
    ]
    batch_actions, batch_logp, batch_values, batch_contexts = (
        batched_agent.act_low_batch(
            observations,
            states=states,
            deterministic=True,
            return_context=True,
        )
    )

    np.testing.assert_array_equal(
        batch_actions, np.stack([row[0] for row in scalar_rows])
    )
    np.testing.assert_allclose(
        batch_logp, np.stack([row[1] for row in scalar_rows]), rtol=0.0, atol=1e-6
    )
    np.testing.assert_allclose(
        batch_values,
        np.stack([row[2] for row in scalar_rows]),
        rtol=0.0,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        batched_agent.low_actor_hxs,
        scalar_agent.low_actor_hxs,
        rtol=0.0,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        batched_agent.low_critic_hxs,
        scalar_agent.low_critic_hxs,
        rtol=0.0,
        atol=1e-6,
    )
    for batch_context, scalar_row in zip(batch_contexts, scalar_rows):
        scalar_context = scalar_row[3]
        assert batch_context["team_code"] == scalar_context["team_code"]
        for field in ("state", "actor_hxs", "critic_hxs"):
            np.testing.assert_allclose(
                batch_context[field], scalar_context[field], rtol=0.0, atol=1e-6
            )


def test_batched_stochastic_actions_replay_with_exact_log_probability():
    rng = np.random.default_rng(23)
    agent = make_agent(num_envs=2, action_space_type="continuous")
    agent.active_skills[:] = np.array([[0, 1], [2, 0]], dtype=np.int64)
    agent.active_team_codes[:] = np.array([1, 0], dtype=np.int64)
    agent.has_active_skill[:] = True
    agent.low_actor_hxs[:] = rng.normal(
        size=agent.low_actor_hxs.shape
    ).astype(np.float32)
    agent.low_critic_hxs[:] = rng.normal(
        size=agent.low_critic_hxs.shape
    ).astype(np.float32)
    observations = [
        rng.normal(size=(2, 4)).astype(np.float32),
        rng.normal(size=(2, 4)).astype(np.float32),
    ]
    states = [
        rng.normal(size=8).astype(np.float32),
        rng.normal(size=8).astype(np.float32),
    ]

    torch.manual_seed(2301)
    actions, stored_logp, _values, contexts = agent.act_low_batch(
        observations,
        states=states,
        return_context=True,
    )
    obs_t = torch.as_tensor(np.stack(observations)[None], dtype=torch.float32)
    skills_t = torch.as_tensor(agent.active_skills[None], dtype=torch.long)
    actions_t = torch.as_tensor(actions[None], dtype=torch.float32)
    states_t = torch.as_tensor(np.stack(states)[None], dtype=torch.float32)
    team_codes_t = torch.as_tensor(agent.active_team_codes[None], dtype=torch.long)
    agent_ids_t = torch.arange(agent.n_agents, dtype=torch.long).reshape(1, 1, -1)
    actor_hxs_t = torch.as_tensor(
        np.stack([context["actor_hxs"] for context in contexts]),
        dtype=torch.float32,
    )
    critic_hxs_t = torch.as_tensor(
        np.stack([context["critic_hxs"] for context in contexts]),
        dtype=torch.float32,
    )
    masks_t = torch.ones((1, 2, agent.n_agents), dtype=torch.float32)

    with torch.no_grad():
        replay_logp, _entropy, _replay_values = agent.low.evaluate_sequence(
            obs_t,
            skills_t,
            actions_t,
            states_t,
            team_codes_t,
            agent_ids_t,
            actor_hxs_t,
            critic_hxs_t,
            masks_t,
            masks_t,
        )

    max_error = np.max(
        np.abs(replay_logp.cpu().numpy()[0] - stored_logp)
    )
    assert max_error <= 1e-6


def test_packed_recurrent_batches_match_reference_construction():
    agent = make_agent(num_envs=2)
    agent.low_sequence_length = 2
    row_count = 5
    hidden = agent.low_rnn_hidden_size
    env_ids = np.array([0, 1, 0, 1, 0], dtype=np.int64)
    rollout = Rollout(
        env_ids=env_ids.tolist(),
        obs=[np.full((2, 4), row + 0.1, dtype=np.float32) for row in range(row_count)],
        states=[np.full(8, row + 10.0, dtype=np.float32) for row in range(row_count)],
        skills=[
            np.array([row % 3, (row + 1) % 3], dtype=np.int64)
            for row in range(row_count)
        ],
        team_codes=[row % 2 for row in range(row_count)],
        actions=[
            np.array([(row + 1) % 3, (row + 2) % 3], dtype=np.int64)
            for row in range(row_count)
        ],
        logp=[np.array([row + 0.2, row + 0.3], dtype=np.float32) for row in range(row_count)],
        values=[np.array([row + 0.4, row + 0.5], dtype=np.float32) for row in range(row_count)],
        low_actor_hxs=[
            np.full((2, hidden), row + 0.6, dtype=np.float32)
            for row in range(row_count)
        ],
        low_critic_hxs=[
            np.full((2, hidden), row + 0.7, dtype=np.float32)
            for row in range(row_count)
        ],
        dones=[False, False, True, False, False],
    )
    returns = np.arange(row_count * 2, dtype=np.float32).reshape(row_count, 2)
    advantages = returns + 20.0
    packed = agent._low_sequence_chunks(rollout, returns, advantages, env_ids)

    chunk_indices = (
        np.array([0, 2], dtype=np.int64),
        np.array([4], dtype=np.int64),
        np.array([1, 3], dtype=np.int64),
    )
    reference = {
        "obs": np.zeros((2, 3, 2, 4), dtype=np.float32),
        "states": np.zeros((2, 3, 8), dtype=np.float32),
        "skills": np.zeros((2, 3, 2), dtype=np.int64),
        "team_codes": np.zeros((2, 3), dtype=np.int64),
        "actions": np.zeros((2, 3, 2), dtype=np.int64),
        "old_logp": np.zeros((2, 3, 2), dtype=np.float32),
        "old_values": np.zeros((2, 3, 2), dtype=np.float32),
        "returns": np.zeros((2, 3, 2), dtype=np.float32),
        "advantages": np.zeros((2, 3, 2), dtype=np.float32),
        "masks": np.zeros((2, 3, 2), dtype=np.float32),
        "reset_masks": np.ones((2, 3, 2), dtype=np.float32),
    }
    raw = {
        "obs": np.asarray(rollout.obs),
        "states": np.asarray(rollout.states),
        "skills": np.asarray(rollout.skills),
        "team_codes": np.asarray(rollout.team_codes),
        "actions": np.asarray(rollout.actions),
        "old_logp": np.asarray(rollout.logp),
        "old_values": np.asarray(rollout.values),
        "returns": returns,
        "advantages": advantages,
    }
    dones = np.asarray(rollout.dones, dtype=np.bool_)
    for chunk_id, indices in enumerate(chunk_indices):
        length = len(indices)
        for field in raw:
            reference[field][:length, chunk_id] = raw[field][indices]
        reference["masks"][:length, chunk_id] = 1.0
        reference["reset_masks"][:length, chunk_id] = (~dones[indices])[:, None]

    assert packed["num_chunks"] == 3
    np.testing.assert_array_equal(packed["lengths"], np.array([2, 1, 2]))
    for field, expected in reference.items():
        np.testing.assert_array_equal(packed[field].cpu().numpy(), expected)
    np.testing.assert_array_equal(
        packed["initial_actor_hxs"].cpu().numpy(),
        np.stack([rollout.low_actor_hxs[int(indices[0])] for indices in chunk_indices]),
    )
    np.testing.assert_array_equal(
        packed["initial_critic_hxs"].cpu().numpy(),
        np.stack([rollout.low_critic_hxs[int(indices[0])] for indices in chunk_indices]),
    )

    selected = agent._low_batch_from_chunk_ids(packed, [2, 1])
    for field, expected in reference.items():
        np.testing.assert_array_equal(
            selected[field].cpu().numpy(), expected[:, [2, 1]]
        )


def test_standalone_checkpoint_roundtrip_restores_networks(tmp_path):
    cfg = make_process_config()
    args = make_args()
    agent = make_agent(cfg)
    expected = next(agent.high.parameters()).detach().clone()
    agent.high_value_norm.load_state_dict({"mean": 3.0, "var": 5.0, "count": 7.0})
    if agent.low_value_norm is not None:
        agent.low_value_norm.load_state_dict(
            {"mean": 11.0, "var": 13.0, "count": 17.0}
        )

    ckpt_path = tmp_path / "standalone.pt"
    checkpoint_io.save_checkpoint(ckpt_path, agent, args, cfg, total_steps=12, update_idx=3)

    restored = make_agent(cfg)
    with torch.no_grad():
        next(restored.high.parameters()).add_(1.0)
    total_steps, update_idx = checkpoint_io.load_checkpoint(
        ckpt_path, restored, load_optimizers=False
    )

    assert total_steps == 12
    assert update_idx == 3
    torch.testing.assert_close(next(restored.high.parameters()).detach(), expected)
    assert restored.high_value_norm.state_dict() == agent.high_value_norm.state_dict()
    if agent.low_value_norm is not None:
        assert restored.low_value_norm.state_dict() == agent.low_value_norm.state_dict()


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


def test_topology_potential_rewards_disconnect_recovery():
    cfg = SimpleNamespace(
        use_topology_potential_shaping=True,
        topology_potential_coef=1.0,
        topology_potential_clip=10.0,
        topology_potential_warmup_steps=0,
        topology_potential_discount_mode="delta",
        topology_potential_positive_only=False,
    )
    segment = Segment(
        env_id=0,
        agent_id=0,
        skill=0,
        duration_idx=0,
        start_step=0,
        high_obs=np.zeros(4, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
    )
    segment.append(
        obs=np.zeros(4, dtype=np.float32),
        action=np.array([1], dtype=np.float32),
        reward=0.0,
        next_obs=np.ones(4, dtype=np.float32),
        rollout_idx=0,
        reward_info={
            "coverage_ratio": 0.0,
            "qos_satisfaction_ratio": 0.0,
            "uavs_with_backhaul": 0,
            "full_network_disconnect": 1.0,
            "backhaul_outage_ratio": 1.0,
            "system_throughput_mbps": 0.0,
        },
    )
    segment.append(
        obs=np.ones(4, dtype=np.float32),
        action=np.array([1], dtype=np.float32),
        reward=0.0,
        next_obs=np.ones(4, dtype=np.float32) * 2.0,
        rollout_idx=1,
        reward_info={
            "coverage_ratio": 0.5,
            "qos_satisfaction_ratio": 0.3,
            "uavs_with_backhaul": 3,
            "current_backhaul_served_users": 4,
            "full_network_disconnect": 0.0,
            "backhaul_outage_ratio": 0.0,
            "system_throughput_mbps": 12.0,
            "min_serving_backhaul_bottleneck_mbps": 8.0,
        },
    )

    rewards, metrics = TopologyPotentialShaper(cfg, n_agents=6, gamma=0.99).rewards(
        [segment],
        total_steps=0,
    )

    assert metrics["topology_potential_active"] == 1.0
    assert metrics["topology_potential_available_frac"] == 1.0
    assert metrics["topology_potential_phi_end_mean"] > metrics["topology_potential_phi_start_mean"]
    assert rewards.shape == (1,)
    assert rewards[0] > 0.0


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

    monkeypatch.setattr(process_evaluation, "create_env", lambda *args, **kwargs: DummyEvalEnv())
    metrics = process_evaluation.evaluate(agent, cfg, args, episodes=1, total_steps=10)

    assert metrics["reward_mean"] == 2.0
    assert metrics["coverage"] == 0.5
    np.testing.assert_array_equal(agent.active_skills, active_before)
    np.testing.assert_array_equal(agent.duration_remaining, duration_before)
    np.testing.assert_array_equal(agent.skill_age, age_before)
    np.testing.assert_array_equal(agent.has_active_skill, has_active_before)
    assert agent.segments is segments_before
