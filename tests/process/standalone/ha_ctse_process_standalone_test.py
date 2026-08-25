from copy import deepcopy
import random
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process import checkpoint_io
from ha_ctse_process import standalone_evaluation as process_evaluation
from ha_ctse_process import standalone_train_runner
from ha_ctse_process.assignment_actionability import (
    AssignmentActionabilityDiscriminator,
)
from ha_ctse_process.metrics_io import read_csv_records
from ha_ctse_process.standalone_agent import StandaloneProcessAgent
from ha_ctse_process.standalone_ar_selection import StandaloneARSelectionMixin
from ha_ctse_process.standalone_lifecycle import StandaloneLifecycleMixin
from ha_ctse_process.standalone_low_inference import StandaloneLowInferenceMixin
from ha_ctse_process.standalone_low_update import StandaloneLowUpdateMixin
from ha_ctse_process.standalone_segments import Rollout, Segment


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
        rollout_length=4,
        total_timesteps=100,
        log_dir="",
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


def test_retired_p3_module_is_not_part_of_agent_state():
    agent = make_agent()

    assert not hasattr(agent, "skill_" + "effect_discovery")


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


def test_low_update_mixin_owns_only_low_update_methods():
    method_names = (
        "_empty_low_metrics",
        "_grad_norm",
        "_low_rollout_diagnostics",
        "_low_returns",
        "_low_sequence_chunks",
        "_low_batch_from_chunk_ids",
        "_update_low_recurrent",
        "update_low",
    )
    assert StandaloneLowUpdateMixin in StandaloneProcessAgent.__bases__
    for name in method_names:
        assert name not in StandaloneProcessAgent.__dict__
        assert getattr(StandaloneProcessAgent, name) is getattr(
            StandaloneLowUpdateMixin, name
        )

    for name in (
        "_label_entropy_np",
        "_group_mean_summary",
        "_info_scalar",
        "_lifetime_diagnostics",
        "_joint_mi_norm",
        "_state_array",
        "_joint_obs_array",
        "process_update",
    ):
        assert name in StandaloneProcessAgent.__dict__
        assert name not in StandaloneLowUpdateMixin.__dict__


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


class _StrictSnapshotCollector:
    def __init__(self):
        self.frontier = np.asarray([3.0, 5.0], dtype=np.float32)
        self.restored = None

    def snapshot_training_state(self):
        return {
            "snapshot_capability_name": "standalone_collector_training_state",
            "snapshot_capability_version": 1,
            "frontier": self.frontier.copy(),
        }

    def restore_training_state(self, snapshot):
        # Strict restore installs global RNG last, so collector internals may use
        # randomness while rebuilding without advancing the resumed stream.
        random.random()
        np.random.random()
        torch.rand(())
        self.restored = deepcopy(snapshot)
        self.frontier = np.asarray(snapshot["frontier"], dtype=np.float32).copy()


def _strict_test_runner_state():
    return standalone_train_runner._strict_runner_state(
        num_envs=1,
        observations=[np.asarray([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)],
        states=[np.arange(8, dtype=np.float32)],
        prev_state_info=[{"step": 7}],
        prev_reward_info=[{"reward": 0.25}],
        last_eval_step=9,
        proto_ratio_over05_count=1,
        proto_ratio_consecutive_over05_count=2,
        proto_ratio_kill_triggered_count=3,
        team_disc_ratio_over05_count=4,
        team_disc_ratio_consecutive_over05_count=5,
        team_disc_ratio_kill_triggered_count=6,
        combined_intrinsic_ratio_over05_count=7,
        combined_intrinsic_ratio_consecutive_over05_count=8,
        combined_intrinsic_ratio_kill_triggered_count=9,
    )


def test_schema4_strict_resume_restores_complete_frontier_and_rng(tmp_path):
    cfg = make_process_config(seed=41)
    args = make_args(seed=41, total_timesteps=200)
    agent = make_agent(cfg)
    agent.initialize_standalone_rngs(args.seed)
    agent.active_skills[:] = np.asarray([[2, 1]], dtype=np.int64)
    agent.has_active_skill[:] = True
    agent.episode_steps[:] = 17
    collector = _StrictSnapshotCollector()
    checkpoint_path = tmp_path / "strict-schema4.pt"

    random.seed(101)
    np.random.seed(103)
    torch.manual_seed(107)
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        agent,
        args,
        cfg,
        total_steps=123,
        update_idx=11,
        collector=collector,
        runner_state=_strict_test_runner_state(),
    )
    next_obs = np.arange(8, dtype=np.float32).reshape(2, 4) / 10.0
    next_state = np.arange(8, dtype=np.float32) / 20.0
    expected_action = agent.act_low(next_obs, env_id=0, state=next_state)
    expected_shuffle = agent._low_update_shuffle_rng.permutation(13)
    expected_global = (random.random(), np.random.random(), torch.rand(()).item())

    restored = make_agent(cfg)
    restored.initialize_standalone_rngs(999)
    restored.active_skills[:] = 0
    random.seed(1)
    np.random.seed(2)
    torch.manual_seed(3)
    restore_collector = _StrictSnapshotCollector()
    restore_collector.frontier[:] = -1.0

    total_steps, update_idx, runner_state = checkpoint_io.load_training_checkpoint(
        checkpoint_path,
        restored,
        collector=restore_collector,
        args=args,
        config=cfg,
    )

    assert (total_steps, update_idx) == (123, 11)
    np.testing.assert_array_equal(restored.active_skills, np.asarray([[2, 1]]))
    np.testing.assert_array_equal(restored.episode_steps, np.asarray([17]))
    actual_action = restored.act_low(next_obs, env_id=0, state=next_state)
    for actual, expected in zip(actual_action, expected_action):
        np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(
        restored._low_update_shuffle_rng.permutation(13), expected_shuffle
    )
    actual_global = (random.random(), np.random.random(), torch.rand(()).item())
    assert actual_global == expected_global
    np.testing.assert_array_equal(restore_collector.frontier, collector.frontier)
    assert runner_state["combined_intrinsic_ratio_kill_triggered_count"] == 9
    torch.testing.assert_close(
        next(restored.high.parameters()), next(agent.high.parameters())
    )


def test_schema4_restores_nonzero_actionability_gate_for_next_update(tmp_path):
    cfg = make_process_config(
        enable_team_intent=True,
        enable_team_disc_probe=True,
        enable_team_disc_reward=True,
        team_disc_coef=0.05,
        team_disc_warmup_steps=0,
        team_disc_actionability_floor=0.25,
    )
    args = make_args()
    agent = make_agent(cfg)
    agent.initialize_standalone_rngs(args.seed)
    agent._last_forced_z_assignment_kl = 0.375
    checkpoint_path = tmp_path / "strict-actionability-gate.pt"
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        agent,
        args,
        cfg,
        total_steps=32,
        update_idx=4,
        collector=_StrictSnapshotCollector(),
        runner_state=_strict_test_runner_state(),
    )

    restored = make_agent(cfg)
    restored.initialize_standalone_rngs(999)
    checkpoint_io.load_training_checkpoint(
        checkpoint_path,
        restored,
        collector=_StrictSnapshotCollector(),
        args=args,
        config=cfg,
    )

    assert agent._team_disc_actionability_gate_open()
    assert restored._team_disc_actionability_gate_open()
    assert restored._last_forced_z_assignment_kl == 0.375
    rollout_source = Rollout(
        next_states=[
            np.linspace(0.0, 0.7, 8, dtype=np.float32),
            np.linspace(0.2, 0.9, 8, dtype=np.float32),
        ],
        team_codes=[0, 1],
        rewards=[
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
        ],
    )
    uninterrupted_rollout = deepcopy(rollout_source)
    resumed_rollout = deepcopy(rollout_source)
    uninterrupted_metrics = agent._team_intent_rollout_update(
        uninterrupted_rollout, total_steps=32
    )
    resumed_metrics = restored._team_intent_rollout_update(
        resumed_rollout, total_steps=32
    )

    assert uninterrupted_metrics == pytest.approx(resumed_metrics, abs=0.0)
    assert resumed_metrics["team_disc_reward_gated_off"] == 0.0
    assert resumed_metrics["team_disc_forced_z_kl"] == 0.375
    for uninterrupted_reward, resumed_reward in zip(
        uninterrupted_rollout.rewards, resumed_rollout.rewards
    ):
        np.testing.assert_array_equal(uninterrupted_reward, resumed_reward)
    torch.testing.assert_close(
        next(agent.team_discriminator.parameters()),
        next(restored.team_discriminator.parameters()),
        rtol=0.0,
        atol=0.0,
    )


def test_schema4_lazy_actionability_roundtrip_from_fresh_agent(tmp_path):
    cfg = make_process_config(
        enable_assignment_actionability_probe=True,
        assignment_actionability_hidden_dim=12,
    )
    args = make_args(total_timesteps=200)
    agent = make_agent(cfg)
    agent.assignment_actionability = AssignmentActionabilityDiscriminator(
        xi_dim=5,
        context_dim=3,
        num_team_codes=agent.num_team_codes,
        hidden_dim=agent.assignment_actionability_cfg.hidden_dim,
    ).to(agent.device)
    agent.q_a_opt = torch.optim.Adam(
        agent.assignment_actionability.parameters(), lr=1e-3
    )
    xi = torch.arange(20, dtype=torch.float32).reshape(4, 5) / 10.0
    context = torch.arange(12, dtype=torch.float32).reshape(4, 3) / 10.0
    labels = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    prior = torch.full((agent.num_team_codes,), 1.0 / agent.num_team_codes)
    terms = agent.assignment_actionability.losses(xi, context, labels, prior)
    agent.q_a_opt.zero_grad()
    (terms["loss_full"] + terms["loss_prior"]).backward()
    agent.q_a_opt.step()
    expected_parameters = [
        parameter.detach().clone()
        for parameter in agent.assignment_actionability.parameters()
    ]
    expected_optimizer = deepcopy(agent.q_a_opt.state_dict())
    checkpoint_path = tmp_path / "strict-lazy-actionability.pt"
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        agent,
        args,
        cfg,
        total_steps=40,
        update_idx=5,
        collector=_StrictSnapshotCollector(),
        runner_state=_strict_test_runner_state(),
    )

    corrupt_path = tmp_path / "strict-lazy-bad-runner.pt"
    corrupt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    del corrupt["strict_trajectory"]["runner_state"]["last_eval_step"]
    torch.save(corrupt, corrupt_path)
    unmaterialized = make_agent(cfg)
    assert unmaterialized.assignment_actionability is None
    assert unmaterialized.q_a_opt is None
    with pytest.raises(ValueError, match="runner state schema mismatch"):
        checkpoint_io.load_training_checkpoint(
            corrupt_path,
            unmaterialized,
            collector=_StrictSnapshotCollector(),
            args=args,
            config=cfg,
        )
    assert unmaterialized.assignment_actionability is None
    assert unmaterialized.q_a_opt is None

    restored = make_agent(cfg)
    assert restored.assignment_actionability is None
    assert restored.q_a_opt is None
    checkpoint_io.load_training_checkpoint(
        checkpoint_path,
        restored,
        collector=_StrictSnapshotCollector(),
        args=args,
        config=cfg,
    )

    assert restored.assignment_actionability is not None
    assert restored.q_a_opt is not None
    for expected, actual in zip(
        expected_parameters, restored.assignment_actionability.parameters()
    ):
        torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)
    actual_optimizer = restored.q_a_opt.state_dict()
    assert actual_optimizer["param_groups"] == expected_optimizer["param_groups"]
    assert actual_optimizer["state"].keys() == expected_optimizer["state"].keys()
    for parameter_id, expected_state in expected_optimizer["state"].items():
        for name, expected in expected_state.items():
            actual = actual_optimizer["state"][parameter_id][name]
            if isinstance(expected, torch.Tensor):
                torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)
            else:
                assert actual == expected


def test_schema4_contract_mismatch_fails_before_any_restore(tmp_path):
    cfg = make_process_config(seed=29)
    args = make_args(seed=29)
    checkpoint_path = tmp_path / "strict-contract.pt"
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        make_agent(cfg),
        args,
        cfg,
        total_steps=16,
        update_idx=2,
        collector=_StrictSnapshotCollector(),
        runner_state=_strict_test_runner_state(),
    )

    changed_cfg = make_process_config(seed=29, gamma=0.91)
    restored = make_agent(changed_cfg)
    with torch.no_grad():
        next(restored.high.parameters()).fill_(7.0)
    restored.active_skills[:] = 2
    parameter_before = next(restored.high.parameters()).detach().clone()
    active_skills_before = restored.active_skills.copy()
    restore_collector = _StrictSnapshotCollector()

    with pytest.raises(ValueError, match="effective training contract mismatch"):
        checkpoint_io.load_training_checkpoint(
            checkpoint_path,
            restored,
            collector=restore_collector,
            args=args,
            config=changed_cfg,
        )

    torch.testing.assert_close(
        next(restored.high.parameters()), parameter_before, rtol=0.0, atol=0.0
    )
    assert restore_collector.restored is None
    np.testing.assert_array_equal(restored.active_skills, active_skills_before)


def test_schema4_contract_names_core_update_semantics():
    cfg = make_process_config(
        gamma=0.97,
        low_gae_lambda=0.91,
        r30_high_gae_lambda=0.87,
        clip_epsilon=0.19,
        low_clip_epsilon=0.08,
        low_ppo_epochs=4,
        r30_high_ppo_epochs=1,
        process_reward_coef=0.07,
        transition_skill_reward_coef=0.03,
        intrinsic_reward_normalize=True,
    )
    args = make_args(rollout_length=23, total_timesteps=1000)
    contract = checkpoint_io.effective_training_contract(
        make_agent(cfg), args, cfg
    )

    for field, expected in {
        "gamma": 0.97,
        "low_gae_lambda": 0.91,
        "r30_high_gae_lambda": 0.87,
        "clip_epsilon": 0.19,
        "low_clip_epsilon": 0.08,
        "low_ppo_epochs": 4,
        "r30_high_ppo_epochs": 1,
        "process_reward_coef": 0.07,
        "transition_skill_reward_coef": 0.03,
        "intrinsic_reward_normalize": True,
    }.items():
        assert contract["config"][field] == expected
    assert contract["args"]["rollout_length"] == 23
    assert contract["resume_constraints"]["minimum_total_timesteps"] == 1000


def test_schema4_contract_rejects_rollout_change_but_allows_operational_changes(
    tmp_path,
):
    cfg = make_process_config(seed=31)
    args = make_args(seed=31, rollout_length=4, total_timesteps=100, log_dir="old")
    checkpoint_path = tmp_path / "strict-contract-args.pt"
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        make_agent(cfg),
        args,
        cfg,
        total_steps=16,
        update_idx=2,
        collector=_StrictSnapshotCollector(),
        runner_state=_strict_test_runner_state(),
    )

    changed_rollout_args = make_args(
        seed=31, rollout_length=5, total_timesteps=500, log_dir="new"
    )
    with pytest.raises(ValueError, match="effective training contract mismatch"):
        checkpoint_io.load_training_checkpoint(
            checkpoint_path,
            make_agent(cfg),
            collector=_StrictSnapshotCollector(),
            args=changed_rollout_args,
            config=cfg,
        )

    shortened_args = make_args(
        seed=31, rollout_length=4, total_timesteps=50, log_dir="new"
    )
    with pytest.raises(ValueError, match="effective training contract mismatch"):
        checkpoint_io.load_training_checkpoint(
            checkpoint_path,
            make_agent(cfg),
            collector=_StrictSnapshotCollector(),
            args=shortened_args,
            config=cfg,
        )

    operational_args = make_args(
        seed=31,
        rollout_length=4,
        total_timesteps=500,
        log_dir="new",
        resume_from=str(checkpoint_path),
        checkpoint_keep_last=9,
    )
    total_steps, update_idx, _ = checkpoint_io.load_training_checkpoint(
        checkpoint_path,
        make_agent(cfg),
        collector=_StrictSnapshotCollector(),
        args=operational_args,
        config=cfg,
    )
    assert (total_steps, update_idx) == (16, 2)


def test_schema2_is_rejected_for_strict_training_resume(tmp_path):
    cfg = make_process_config()
    args = make_args()
    agent = make_agent(cfg)
    checkpoint_path = tmp_path / "warm-start-schema2.pt"
    checkpoint_io.save_checkpoint(
        checkpoint_path, agent, args, cfg, total_steps=4, update_idx=2
    )

    with pytest.raises(ValueError, match="requires standalone schema-4"):
        checkpoint_io.load_training_checkpoint(
            checkpoint_path,
            make_agent(cfg),
            collector=_StrictSnapshotCollector(),
            args=args,
            config=cfg,
        )


def test_schema4_optimizer_mismatch_is_not_swallowed(tmp_path):
    cfg = make_process_config(seed=17)
    args = make_args(seed=17)
    checkpoint_path = tmp_path / "strict-bad-opt.pt"
    checkpoint_io.save_training_checkpoint(
        checkpoint_path,
        make_agent(cfg),
        args,
        cfg,
        total_steps=8,
        update_idx=3,
        collector=_StrictSnapshotCollector(),
        runner_state=_strict_test_runner_state(),
    )
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    payload["strict_trajectory"]["optimizers"]["high_opt"]["param_groups"] = []
    torch.save(payload, checkpoint_path)

    with pytest.raises(ValueError):
        checkpoint_io.load_training_checkpoint(
            checkpoint_path,
            make_agent(cfg),
            collector=_StrictSnapshotCollector(),
            args=args,
            config=cfg,
        )


def test_evaluation_restores_global_rng_even_when_evaluation_raises(monkeypatch):
    random.seed(211)
    np.random.seed(223)
    torch.manual_seed(227)
    before = checkpoint_io.capture_global_rng_state()

    def fail_after_consuming_rng(*_args, **_kwargs):
        random.random()
        np.random.random()
        torch.rand(())
        raise RuntimeError("synthetic evaluation failure")

    monkeypatch.setattr(process_evaluation, "_evaluate_impl", fail_after_consuming_rng)
    with pytest.raises(RuntimeError, match="synthetic evaluation failure"):
        process_evaluation.evaluate(None, None, None, episodes=1, total_steps=0)
    after = checkpoint_io.capture_global_rng_state()

    assert before["python"] == after["python"]
    assert before["numpy"][0] == after["numpy"][0]
    np.testing.assert_array_equal(before["numpy"][1], after["numpy"][1])
    assert before["numpy"][2:] == after["numpy"][2:]
    torch.testing.assert_close(before["torch_cpu"], after["torch_cpu"])


def test_process_update_injects_reward_into_matching_rollout_agent():
    np.random.seed(2)
    torch.manual_seed(2)
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


class DummyMixedBackhaulEvalEnv(DummyEvalEnv):
    def __init__(self):
        super().__init__()
        self.episode_index = -1

    def reset(self, seed=None):
        self.episode_index += 1
        return super().reset(seed=seed)

    def step(self, actions):
        obs, reward, terminated, truncated, info = super().step(actions)
        if self.episode_index == 0:
            info["reward_info"]["backhaul_connected_flag"] = 0.0
        return obs, reward, terminated, truncated, info


class _OneStepTrainCollector:
    def __init__(self):
        self.spec = {
            "obs_dim": 4,
            "action_dim": 3,
            "n_uavs": 2,
            "state_dim": 8,
            "action_space": SimpleNamespace(
                dtype=np.dtype(np.int64),
                low=np.asarray([0], dtype=np.int64),
                high=np.asarray([2], dtype=np.int64),
            ),
        }
        self.closed = False

    def reset_all(self, seed):
        return (
            [np.zeros((2, 4), dtype=np.float32)],
            [np.zeros(8, dtype=np.float32)],
            [{}],
        )

    def step(self, actions):
        return [
            SimpleNamespace(
                obs=np.ones((2, 4), dtype=np.float32),
                reward=1.0,
                terminated=False,
                truncated=False,
                info={
                    "next_state": np.ones(8, dtype=np.float32),
                    "state_info": {},
                    "reward_info": {},
                    "reward_components": {
                        "individual_rewards": np.ones(2, dtype=np.float32)
                    },
                },
            )
        ]

    def snapshot_training_state(self):
        return {
            "snapshot_capability_name": "standalone_collector_training_state",
            "snapshot_capability_version": 1,
            "frontier": np.asarray([1], dtype=np.int64),
        }

    def close(self):
        self.closed = True


def test_standalone_eval_does_not_average_over_partial_metric_episodes(monkeypatch):
    cfg = make_process_config(scenario="base")
    args = make_args(eval_max_steps=3)
    agent = make_agent(cfg)
    monkeypatch.setattr(
        process_evaluation,
        "create_env",
        lambda *args, **kwargs: DummyMixedBackhaulEvalEnv(),
    )

    metrics = process_evaluation.evaluate(
        agent, cfg, args, episodes=2, total_steps=10
    )

    assert "backhaul_connected_flag" not in metrics
    assert "backhaul_connected_step_fraction" not in metrics


def test_standalone_eval_restores_runtime_state(monkeypatch, capsys):
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
    assert "backhaul_connected_flag" not in metrics
    assert "backhaul_connected_step_fraction" not in metrics
    assert "throughput_when_backhaul_connected_mbps" not in metrics
    output = capsys.readouterr().out
    assert "backhaul_connected_frac=NA" in output
    assert "throughput_when_backhaul_connected=NA" in output
    np.testing.assert_array_equal(agent.active_skills, active_before)
    np.testing.assert_array_equal(agent.duration_remaining, duration_before)
    np.testing.assert_array_equal(agent.skill_age, age_before)
    np.testing.assert_array_equal(agent.has_active_skill, has_active_before)
    assert agent.segments is segments_before


def test_periodic_evaluation_records_grouping_identity_and_renders_plots(
    tmp_path, monkeypatch
):
    cfg = make_process_config(scenario="base")
    args = make_args(
        seed=13,
        log_dir=str(tmp_path),
        eval_episodes=2,
        eval_max_steps=3,
    )
    agent = make_agent(cfg)
    monkeypatch.setattr(
        process_evaluation, "create_env", lambda *args, **kwargs: DummyEvalEnv()
    )

    process_evaluation.evaluate(agent, cfg, args, episodes=2, total_steps=80)

    rows = read_csv_records(tmp_path / "metrics" / "eval_episodes.csv")
    assert len(rows) == 2
    assert [row["checkpoint"] for row in rows] == [
        "in_training_step_80",
        "in_training_step_80",
    ]
    assert [row["eval_step"] for row in rows] == [80.0, 80.0]
    assert [row["run_seed"] for row in rows] == [13.0, 13.0]
    assert [row["seed"] for row in rows] == [100013.0, 100013.0]
    assert [row["reset_seed"] for row in rows] == [100013.0, 100014.0]
    assert (tmp_path / "eval_reward.png").is_file()


def test_train_runner_periodic_evaluation_renders_and_saves_completed_frontier(
    tmp_path, monkeypatch
):
    cfg = make_process_config(scenario="base")
    args = make_args(
        num_envs=1,
        collector_backend="sync",
        preset="",
        resume_from="",
        rollout_length=1,
        total_timesteps=1,
        save_interval=1,
        checkpoint_keep_last=2,
        eval_interval=1,
        eval_episodes=2,
        infrastructure_profile_interval=0,
        log_dir=str(tmp_path),
    )
    collector = _OneStepTrainCollector()
    agent = make_agent(cfg)
    zero_process_metrics = {
        "process_segments": 0.0,
        "process_loss": 0.0,
        "process_reward_mean": 0.0,
        "outcome_available_mean": 0.0,
        "outcome_abs_mean": 0.0,
        "high_loss": 0.0,
        "high_entropy": 0.0,
        "high_return_mean": 0.0,
    }
    zero_low_metrics = {
        "low_loss": 0.0,
        "low_entropy": 0.0,
        "return_mean": 0.0,
    }
    agent.process_update = lambda *_args, **_kwargs: dict(zero_process_metrics)
    agent.update_low = lambda *_args, **_kwargs: dict(zero_low_metrics)
    monkeypatch.setattr(
        standalone_train_runner, "create_collector", lambda *_args, **_kwargs: collector
    )
    monkeypatch.setattr(
        standalone_train_runner, "create_agent", lambda *_args, **_kwargs: agent
    )
    monkeypatch.setattr(
        standalone_train_runner.standalone_manifest,
        "export_run_manifest",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        standalone_train_runner, "export_update_metrics", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(standalone_train_runner, "emit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        process_evaluation, "create_env", lambda *_args, **_kwargs: DummyEvalEnv()
    )

    returned_agent, total_steps, update_idx = standalone_train_runner.train_loop(
        cfg, args, writer=None
    )

    assert returned_agent is agent
    assert (total_steps, update_idx) == (1, 1)
    assert collector.closed
    rows = read_csv_records(tmp_path / "metrics" / "eval_episodes.csv")
    assert len(rows) == 2
    assert {row["checkpoint"] for row in rows} == {"in_training_step_1"}
    assert {row["eval_step"] for row in rows} == {1.0}
    assert {row["run_seed"] for row in rows} == {1.0}
    assert {row["seed"] for row in rows} == {100001.0}
    assert (tmp_path / "eval_reward.png").is_file()
    periodic = torch.load(
        tmp_path / "standalone_process_core_update_1.pt",
        map_location="cpu",
        weights_only=False,
    )
    assert periodic["strict_trajectory"]["runner_state"]["last_eval_step"] == 1
