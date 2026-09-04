from __future__ import annotations

import math

import numpy as np
import pytest
import torch

# Match the process-isolated B3 CLI for proof-sized runtime checks.  Restoring
# a large Windows thread pool is far slower than the registered smoke itself.
torch.set_num_threads(1)

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import reward_credit_learnability as b3


def test_registered_full_and_smoke_budgets_are_exact() -> None:
    assert b3.FULL_PLAN.training_episodes == 576
    assert b3.FULL_PLAN.training_transitions == 27_648
    assert b3.FULL_PLAN.evaluation_episodes == 648
    assert b3.FULL_PLAN.evaluation_transitions == 31_104
    assert b3.FULL_PLAN.maximum_transitions == 58_752
    assert b3.SMOKE_PLAN.training_episodes == 12
    assert b3.SMOKE_PLAN.training_updates_per_actor == 6
    assert b3.SMOKE_PLAN.mid_update == 3
    assert b3.SMOKE_PLAN.evaluation_episodes == 54


def test_episode_identity_matches_learners_and_separates_checkpoints() -> None:
    identities = {
        stage: b3.episode_id(stage, 2, 1, 3)
        for stage in ("train", *b3.CHECKPOINTS)
    }
    assert len(set(identities.values())) == 4
    assert identities["train"] == 6_210_003
    with pytest.raises(ValueError, match="unregistered B3"):
        b3.episode_id("unknown", 0, 0, 0)


def test_terminal_gae_norm_matches_direct_episode_arithmetic() -> None:
    actor = b1.RecurrentActorCritic(8, 91, encoder_kind="content_separating")
    log_probs = torch.linspace(-0.7, -0.2, roster_env.HORIZON, requires_grad=True)
    values = torch.linspace(-0.3, 0.4, roster_env.HORIZON, requires_grad=True)
    rewards = np.linspace(-0.2, 0.5, roster_env.HORIZON, dtype=np.float32)
    actor._log_probs = list(log_probs.unbind())
    actor._values = list(values.unbind())

    loss, parts = actor.episode_loss_gae_norm(rewards)

    value_np = values.detach().numpy()
    next_values = np.concatenate((value_np[1:], np.zeros(1, dtype=np.float32)))
    deltas = rewards + b1.GAMMA * next_values - value_np
    raw = np.empty_like(deltas)
    carry = np.float32(0.0)
    for index in range(roster_env.HORIZON - 1, -1, -1):
        carry = deltas[index] + b1.GAMMA * b3.GAE_LAMBDA * carry
        raw[index] = carry
    normalized = (raw - raw.mean()) / max(raw.std(ddof=0), b3.NORMALIZATION_EPSILON)
    target = raw + value_np
    expected_actor = -float(np.mean(log_probs.detach().numpy() * normalized))
    expected_critic = float(np.mean(np.square(target - value_np)))
    expected = expected_actor + 0.5 * expected_critic

    assert float(loss.detach()) == pytest.approx(expected, rel=2e-6, abs=2e-6)
    assert parts["actor_loss"] == pytest.approx(expected_actor, rel=2e-6)
    assert parts["critic_loss"] == pytest.approx(expected_critic, rel=2e-6)
    assert parts["value_target_error"] == pytest.approx(float(np.mean(np.abs(raw))))
    assert parts["normalized_advantage_mean"] == pytest.approx(0.0, abs=2e-6)
    assert parts["normalized_advantage_population_std"] == pytest.approx(1.0, abs=2e-6)
    loss.backward()
    assert log_probs.grad is not None
    assert values.grad is not None


def test_gae_fails_closed_on_incomplete_episode_and_invalid_hyperparameters() -> None:
    actor = b1.RecurrentActorCritic(8, 92, encoder_kind="content_separating")
    actor._log_probs = [torch.tensor(0.0)]
    actor._values = [torch.tensor(0.0)]
    with pytest.raises(RuntimeError, match="complete episode"):
        actor.episode_loss_gae_norm([0.0])

    actor._log_probs = [torch.tensor(0.0)] * roster_env.HORIZON
    actor._values = [torch.tensor(0.0)] * roster_env.HORIZON
    rewards = [0.0] * roster_env.HORIZON
    with pytest.raises(ValueError, match="gae_lambda"):
        actor.episode_loss_gae_norm(rewards, gae_lambda=1.1)
    with pytest.raises(ValueError, match="normalization_epsilon"):
        actor.episode_loss_gae_norm(rewards, normalization_epsilon=0.0)


def test_real_smoke_runs_matched_learners_checkpoints_and_three_arm_evaluator() -> None:
    result = b3.run_experiment("smoke")

    assert result["mechanical_status"] == "MECHANICAL_B3_COMPLETE"
    assert result["scientific_disposition"] is None
    assert result["registered_c_outcome_experiment_licensed"] is False
    assert result["real_environment_calls"] is True
    assert result["real_policy_calls"] is True
    assert result["real_actor_learner_updates"] is True
    assert result["real_evaluation_runner_calls"] is True
    assert result["counts"] == {
        "environment_transitions": 3_168,
        "policy_calls": 3_168,
        "actor_critic_optimizer_steps": 12,
        "training_episodes": 12,
        "evaluation_episodes": 54,
    }
    assert all(result["matching_proof"].values())
    assert {row["learner"] for row in result["actors"]} == set(b3.LEARNERS)
    for actor in result["actors"]:
        assert len(actor["training"]) == 6
        assert actor["training_summary"]["all_finite"] is True
        assert set(actor["checkpoint_state_digests"]) == set(b3.CHECKPOINTS)
        assert [row["update"] for row in actor["training"]] == list(range(1, 7))
    # One row retains the three matched arm episodes for each
    # learner/checkpoint/profile/root coordinate.
    assert len(result["evaluation_rows"]) == 18
    for row in result["evaluation_rows"]:
        assert set(row["arms"]) == set(b3.EVALUATION_ARMS)
        assert all(row["matching"].values())
        assert len(row["ab_diagnostics"]) == len(
            row["delivered_registered_body_labels"]
        )
    root_summaries = [
        row for row in result["condition_summaries"] if "checkpoint" in row
    ]
    delta_summaries = [
        row for row in result["condition_summaries"] if "checkpoint_change" in row
    ]
    assert len(root_summaries) == 18
    assert len(delta_summaries) == 12
    assert all(row["correct_minus_swapped"]["count"] == 1 for row in root_summaries)
    assert all(
        math.isfinite(float(actor["training_summary"]["grad_clip_exceed_fraction"]))
        for actor in result["actors"]
    )
