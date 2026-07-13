from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.r28_g0_target import EXPERIMENT_ID, HEAD_INPUT_WIDTH
from ha_ctse_process.r28_g1_reward import (
    FINAL_CHECKPOINT_PATH,
    FrozenR28G1Reward,
    R28G1ContractError,
    fixed_point_free_derangement,
)
from ha_ctse_process.standalone_agent import Rollout, Segment, SegmentManager
from ha_ctse_process.train import enforce_r28_g1_contract


def _head(name: str, *, full: bool) -> dict:
    weight = np.zeros((4, HEAD_INPUT_WIDTH), dtype=np.float32)
    if full:
        for label in range(4):
            weight[label, label * 3] = 4.0
    return {
        "name": name,
        "mean": np.zeros(HEAD_INPUT_WIDTH, dtype=np.float32).tolist(),
        "std": np.ones(HEAD_INPUT_WIDTH, dtype=np.float32).tolist(),
        "weight": weight.tolist(),
        "bias": np.zeros(4, dtype=np.float32).tolist(),
        "temperature": 1.0,
        "optimizer_steps": 1,
        "validation_evaluations": 1,
    }


def _write_scorer(path: Path, *, support_mean: float = 0.0, threshold: float = 1e6) -> None:
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "checkpoint_id": "arm0_final",
        "authorized_for_g1_package_review": True,
        "reward_launch_authorized": False,
        "heads": {
            "q_full": _head("q_full", full=True),
            "q_context": _head("q_context", full=False),
            "q_pre": _head("q_pre", full=False),
        },
        "support_envelope": {
            "means": np.full((4, 4, 12), support_mean, dtype=np.float32).tolist(),
            "variances": np.ones((4, 4, 12), dtype=np.float32).tolist(),
            "thresholds": np.full((4, 4), threshold, dtype=np.float32).tolist(),
            "future_ood_kill_fraction": 0.20,
        },
        "scientific_contract": {
            "duration_steps": [10, 20, 30, 40],
            "head_input_width": HEAD_INPUT_WIDTH,
            "checkpoint_slots": {
                "arm0_final": {
                    "path": FINAL_CHECKPOINT_PATH,
                    "update": 32,
                    "total_steps": 1_000_000,
                }
            },
        },
    }
    torch.save(payload, path)


def _actor_base() -> torch.nn.Module:
    torch.manual_seed(7)
    return torch.nn.Sequential(torch.nn.Linear(5, 256), torch.nn.ReLU())


def _rows_and_rollout(*, env_reward: float = 10.0) -> tuple[list[Segment], Rollout]:
    segments: list[Segment] = []
    rollout = Rollout()
    amplitudes = (0.2, 0.4, 0.6, 0.8)
    for label, amplitude in enumerate(amplitudes):
        action = np.zeros(4, dtype=np.float32)
        action[label] = amplitude
        indices = list(range(label * 10, (label + 1) * 10))
        segment = Segment(
            env_id=0,
            agent_id=0,
            skill=label,
            duration_idx=0,
            start_step=indices[0],
            high_obs=np.zeros(5, dtype=np.float32),
            high_logp=0.0,
            high_value=0.0,
            high_entropy=0.0,
            duration_target=1,
            episode_step_start=indices[0],
            episode_id=9,
            policy_update=33,
            pre_assignment_episode_id=9,
            pre_assignment_policy_update=33,
            completion_reason="renewal",
            obs=[np.zeros(5, dtype=np.float32) for _ in indices],
            actions=[action.copy() for _ in indices],
            deterministic_actions=[action.copy() for _ in indices],
            pre_assignment_deterministic_actions=[
                np.zeros(4, dtype=np.float32) for _ in range(10)
            ],
            rewards=[env_reward for _ in indices],
            rollout_indices=indices,
        )
        segments.append(segment)
        for _ in indices:
            roster = np.zeros(6, dtype=np.int64)
            roster[0] = label
            deterministic = np.zeros((6, 4), dtype=np.float32)
            deterministic[0] = action
            rollout.env_ids.append(0)
            rollout.skills.append(roster)
            rollout.deterministic_actions.append(deterministic)
            rollout.rewards.append(np.full(6, env_reward, dtype=np.float32))
    return segments, rollout


def test_fixed_point_free_derangement_is_reproducible_and_marginal_preserving():
    labels = np.asarray([0, 0, 1, 1, 2, 2, 3, 3], dtype=np.int64)
    first = fixed_point_free_derangement(
        labels, policy_update=33, agent_id=2, duration_id=1
    )
    second = fixed_point_free_derangement(
        labels, policy_update=33, agent_id=2, duration_id=1
    )
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(
        np.bincount(first, minlength=4), np.bincount(labels, minlength=4)
    )
    assert np.all(first != labels)


@pytest.mark.parametrize(
    "counts",
    ((1, 1, 2, 4), (1, 2, 2, 3), (1, 3, 1, 3), (2, 3, 4, 1)),
)
def test_derangement_constructs_every_admitted_skewed_multiset(counts):
    labels = np.concatenate(
        [np.full(count, label, dtype=np.int64) for label, count in enumerate(counts)]
    )
    for update in range(12):
        sham = fixed_point_free_derangement(
            labels,
            policy_update=update,
            agent_id=update % 6,
            duration_id=update % 4,
        )
        assert np.all(sham != labels)
        np.testing.assert_array_equal(
            np.bincount(sham, minlength=4), np.asarray(counts)
        )


def test_real_reward_uses_only_final_low_steps_and_keeps_other_agents_unchanged(tmp_path):
    scorer_path = tmp_path / "scorer.pt"
    _write_scorer(scorer_path)
    reward = FrozenR28G1Reward(
        arm="real_reward",
        scorer_path=scorer_path,
        actor_base=_actor_base(),
        device="cpu",
    )
    segments, rollout = _rows_and_rollout()
    before = np.asarray(rollout.rewards, dtype=np.float32).copy()
    metrics = reward.apply(segments, rollout, policy_update=33)
    after = np.asarray(rollout.rewards, dtype=np.float32)

    assert metrics["r28_g1_rewardable_groups"] == 1.0
    assert metrics["r28_g1_rewardable_rows"] == 4.0
    assert metrics["r28_g1_support_kill_switch_event"] == 0.0
    assert metrics["r28_g1_ratio_kill_switch_event"] == 0.0
    assert metrics["r28_g1_reward_applied_steps"] > 0.0
    assert np.any(after[:, 0] != before[:, 0])
    np.testing.assert_array_equal(after[:, 1:], before[:, 1:])
    for segment in segments:
        np.testing.assert_array_equal(segment.rewards, np.full(10, 10.0))


def test_new_segment_team_boundary_marker_does_not_reject_natural_length(tmp_path):
    scorer_path = tmp_path / "scorer.pt"
    _write_scorer(scorer_path)
    reward = FrozenR28G1Reward(
        arm="probe_only",
        scorer_path=scorer_path,
        actor_base=_actor_base(),
        device="cpu",
    )
    segments, rollout = _rows_and_rollout()
    for segment in segments:
        segment.team_intent_truncated = True
    metrics = reward.apply(segments, rollout, policy_update=33)
    assert metrics["r28_g1_structural_rows"] == 4.0
    assert metrics["r28_g1_rewardable_rows"] == 4.0


def test_support_and_ratio_kill_switches_zero_the_whole_rollout(tmp_path):
    support_path = tmp_path / "support_kill.pt"
    _write_scorer(support_path, support_mean=100.0, threshold=0.01)
    support_reward = FrozenR28G1Reward(
        arm="real_reward",
        scorer_path=support_path,
        actor_base=_actor_base(),
        device="cpu",
    )
    segments, rollout = _rows_and_rollout()
    before = np.asarray(rollout.rewards).copy()
    support_metrics = support_reward.apply(segments, rollout, policy_update=33)
    assert support_metrics["r28_g1_support_kill_switch_event"] == 1.0
    np.testing.assert_array_equal(np.asarray(rollout.rewards), before)


def test_nonfinite_environment_reward_fails_before_ppo(tmp_path):
    scorer_path = tmp_path / "scorer.pt"
    _write_scorer(scorer_path)
    reward = FrozenR28G1Reward(
        arm="real_reward",
        scorer_path=scorer_path,
        actor_base=_actor_base(),
        device="cpu",
    )
    segments, rollout = _rows_and_rollout()
    rollout.rewards[0][0] = np.nan
    with pytest.raises(R28G1ContractError, match="environment reward is non-finite"):
        reward.apply(segments, rollout, policy_update=33)

    ratio_path = tmp_path / "ratio_kill.pt"
    _write_scorer(ratio_path)
    ratio_reward = FrozenR28G1Reward(
        arm="real_reward",
        scorer_path=ratio_path,
        actor_base=_actor_base(),
        device="cpu",
    )
    segments, rollout = _rows_and_rollout(env_reward=0.0)
    before = np.asarray(rollout.rewards).copy()
    ratio_metrics = ratio_reward.apply(segments, rollout, policy_update=33)
    assert ratio_metrics["r28_g1_ratio_kill_switch_event"] == 1.0
    np.testing.assert_array_equal(np.asarray(rollout.rewards), before)


def test_frozen_actor_base_survives_policy_mutation_and_checkpoint_resume(tmp_path):
    scorer_path = tmp_path / "scorer.pt"
    _write_scorer(scorer_path)
    actor = _actor_base()
    reward = FrozenR28G1Reward(
        arm="probe_only",
        scorer_path=scorer_path,
        actor_base=actor,
        device="cpu",
    )
    observation = torch.zeros(1, 5)
    with torch.no_grad():
        expected = reward.phi0(observation).clone()
        for parameter in actor.parameters():
            parameter.add_(10.0)
    np.testing.assert_allclose(reward.phi0(observation).detach().numpy(), expected.numpy())

    state = reward.checkpoint_state()
    resumed = FrozenR28G1Reward(
        arm="probe_only",
        scorer_path=scorer_path,
        actor_base=actor,
        device="cpu",
        frozen_actor_base_state=state["frozen_actor_base"],
    )
    np.testing.assert_allclose(resumed.phi0(observation).detach().numpy(), expected.numpy())
    assert all(not parameter.requires_grad for parameter in resumed.phi0.parameters())

    corrupted = {
        name: value.clone() for name, value in state["frozen_actor_base"].items()
    }
    first_name = next(iter(corrupted))
    corrupted[first_name].reshape(-1)[0] = torch.nan
    with pytest.raises(R28G1ContractError, match="actor-base tensor.*non-finite"):
        FrozenR28G1Reward(
            arm="probe_only",
            scorer_path=scorer_path,
            actor_base=actor,
            device="cpu",
            frozen_actor_base_state=corrupted,
        )


def test_segment_manager_records_natural_pre_window_and_flush_reason():
    manager = SegmentManager(n_envs=1, n_agents=1)
    common = dict(
        env_id=0,
        agent_id=0,
        duration_idx=0,
        step=0,
        high_obs=np.zeros(5, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        duration_target=1,
        episode_step_start=0,
        episode_id=4,
        policy_update=33,
    )
    manager.renew(skill=0, **common)
    for step in range(10):
        manager.append(
            0,
            obs=np.zeros((1, 5), dtype=np.float32),
            actions=np.zeros((1, 4), dtype=np.float32),
            rewards=np.zeros(1, dtype=np.float32),
            next_obs=np.zeros((1, 5), dtype=np.float32),
            rollout_idx=step,
            deterministic_actions=np.full((1, 4), step, dtype=np.float32),
        )
    manager.renew(skill=1, **{**common, "step": 10, "episode_step_start": 10})
    completed = manager.pop_completed()
    assert completed[0].completion_reason == "renewal"
    active = manager.active[0][0]
    assert active is not None
    assert len(active.pre_assignment_deterministic_actions) == 10
    assert active.pre_assignment_episode_id == 4
    assert active.pre_assignment_policy_update == 33
    manager.append(
        0,
        obs=np.zeros((1, 5), dtype=np.float32),
        actions=np.zeros((1, 4), dtype=np.float32),
        rewards=np.zeros(1, dtype=np.float32),
        next_obs=np.zeros((1, 5), dtype=np.float32),
        rollout_idx=10,
        deterministic_actions=np.zeros((1, 4), dtype=np.float32),
        done=True,
    )
    manager.flush(0, reason="episode")
    assert manager.pop_completed()[0].completion_reason == "episode"


def test_contract_is_applied_after_checkpoint_metadata(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    args = SimpleNamespace(
        r28_g1_arm="real_reward",
        r28_g1_scorer_path="scorer.pt",
        resume_from=FINAL_CHECKPOINT_PATH,
        device="cuda",
        num_envs=16,
        skill_interval=10,
        rollout_length=500,
        preset="S7-S1",
        scenario="energy",
        collector_backend="subproc",
        low_ppo_epochs=15,
        total_timesteps=1_160_000,
        seed=28031,
        eval_interval=80_000,
        eval_episodes=20,
    )
    config = SimpleNamespace(enable_prototype_disc_reward=True)
    metadata = {
        "n_agents": 6,
        "n_skills": 4,
        "action_space_type": "continuous",
        "use_recurrent_low_level": True,
        "low_level_architecture": "strict_hmasd_mappo",
        "duration_candidates": (1, 2, 3, 4),
        "skill_interval": 10,
        "low_actor_condition_on_team_code": False,
        "total_steps": 1_000_000,
        "update_idx": 32,
        "r28_g1": None,
    }
    enforce_r28_g1_contract(config, args, metadata)
    assert config.r28_g1_arm == "real_reward"
    assert config.enable_prototype_disc_reward is False
    assert config.enable_team_disc_reward is False
    assert config.enable_assignment_actionability_reward is False
    assert config.skill_forcing_reward_on is False
    assert config.p2_recovery_credit_reward_on is False
    assert config.assignment_actionability_coef == 0.0
    assert config.p2_recovery_reward_coef == 0.0
    assert config.process_reward_injection == "none"
    assert config.skill_force_reward_injection == "none"
    assert config.duration_entropy_floor_enabled is False


def test_contract_rejects_metadata_compatible_nonregistered_source(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    args = SimpleNamespace(
        r28_g1_arm="real_reward",
        r28_g1_scorer_path="scorer.pt",
        resume_from=(
            "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/"
            "standalone_process_core_final.pt"
        ),
        device="cuda",
        num_envs=16,
        skill_interval=10,
        rollout_length=500,
        preset="S7-S1",
        scenario="energy",
        collector_backend="subproc",
        low_ppo_epochs=15,
        total_timesteps=1_160_000,
        seed=28031,
        eval_interval=80_000,
        eval_episodes=20,
    )
    metadata = {
        "n_agents": 6,
        "n_skills": 4,
        "action_space_type": "continuous",
        "use_recurrent_low_level": True,
        "low_level_architecture": "strict_hmasd_mappo",
        "duration_candidates": (1, 2, 3, 4),
        "skill_interval": 10,
        "low_actor_condition_on_team_code": False,
        "total_steps": 1_000_000,
        "update_idx": 32,
        "r28_g1": None,
    }
    with pytest.raises(ValueError, match="registered R25 arm0 final path"):
        enforce_r28_g1_contract(SimpleNamespace(), args, metadata)


def test_contract_rejects_stochastic_evaluation(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    args = SimpleNamespace(
        r28_g1_arm="real_reward",
        r28_g1_scorer_path="scorer.pt",
        resume_from=FINAL_CHECKPOINT_PATH,
        device="cuda",
        eval_action_mode="stochastic",
    )
    with pytest.raises(ValueError, match="deterministic evaluation actions"):
        enforce_r28_g1_contract(SimpleNamespace(), args, {})


def test_continuation_rejects_scorer_path_swap(monkeypatch, tmp_path):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    args = SimpleNamespace(
        r28_g1_arm="real_reward",
        r28_g1_scorer_path=str(tmp_path / "replacement.pt"),
        resume_from=str(tmp_path / "continuation.pt"),
        device="cuda",
        num_envs=16,
        skill_interval=10,
        rollout_length=500,
        preset="S7-S1",
        scenario="energy",
        collector_backend="subproc",
        low_ppo_epochs=15,
        total_timesteps=1_160_000,
        seed=28031,
        eval_interval=80_000,
        eval_episodes=20,
    )
    metadata = {
        "n_agents": 6,
        "n_skills": 4,
        "action_space_type": "continuous",
        "use_recurrent_low_level": True,
        "low_level_architecture": "strict_hmasd_mappo",
        "duration_candidates": (1, 2, 3, 4),
        "skill_interval": 10,
        "low_actor_condition_on_team_code": False,
        "total_steps": 1_080_000,
        "update_idx": 42,
        "r28_g1": {
            "arm": "real_reward",
            "scorer_path": str(tmp_path / "frozen.pt"),
            "source_total_steps": 1_000_000,
            "source_update_idx": 32,
            "source_checkpoint_id": "arm0_final",
            "has_frozen_actor_base": True,
        },
    }
    with pytest.raises(ValueError, match="scorer path"):
        enforce_r28_g1_contract(SimpleNamespace(), args, metadata)
