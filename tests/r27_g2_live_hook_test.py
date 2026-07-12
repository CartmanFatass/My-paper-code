from __future__ import annotations

import copy

import numpy as np
import pytest
import torch

from ha_ctse_process.low_actor_capacity_audit import forward_actor_snapshot
from ha_ctse_process.standalone_agent import (
    StandaloneProcessAgent,
    StrictHMASDMAPPOLowLevelPolicy,
)


def make_policy(*, actor_team_code: bool = False):
    torch.manual_seed(27120)
    return StrictHMASDMAPPOLowLevelPolicy(
        obs_dim=7,
        state_dim=11,
        n_skills=4,
        num_team_codes=3,
        action_dim=4,
        hidden_dim=8,
        action_space_type="continuous",
        continuous_action_distribution="tanh_gaussian",
        actor_condition_on_team_code=actor_team_code,
        device="cpu",
    ).eval()


def make_agent() -> StandaloneProcessAgent:
    agent = object.__new__(StandaloneProcessAgent)
    agent.device = torch.device("cpu")
    agent.num_envs = 1
    agent.n_agents = 6
    agent.obs_dim = 7
    agent.state_dim = 11
    agent.action_space_type = "continuous"
    agent.use_recurrent_low_level = True
    agent.low = make_policy()
    agent.low_value_norm = None
    agent.active_skills = np.array([[0, 1, 2, 3, 0, 1]], dtype=np.int64)
    agent.active_team_codes = np.array([2], dtype=np.int64)
    agent.low_actor_hxs = np.arange(48, dtype=np.float32).reshape(1, 6, 8) / 100.0
    agent.low_critic_hxs = np.arange(48, dtype=np.float32).reshape(1, 6, 8) / 80.0
    agent._last_low_context = [None]
    agent.duration_remaining = np.array([[7, 8, 9, 10, 11, 12]], dtype=np.int64)
    agent.skill_age = np.array([[1, 2, 3, 4, 5, 6]], dtype=np.int64)
    return agent


def test_reference_audit_step_matches_live_act_low_on_duplicate_runtime():
    agent = make_agent()
    obs = np.arange(42, dtype=np.float32).reshape(6, 7) / 50.0
    state = np.arange(11, dtype=np.float32) / 20.0
    duplicate = copy.deepcopy(agent)

    audit = agent.r27_g2_audit_step(
        obs,
        env_id=0,
        state=state,
        focal_agent=3,
        focal_skill=None,
    )
    live_action, live_logp, live_value = duplicate.act_low(
        obs, env_id=0, deterministic=True, state=state
    )

    np.testing.assert_allclose(audit["deterministic_action"], live_action, atol=1e-6)
    np.testing.assert_allclose(audit["log_probability"], live_logp, atol=1e-6)
    np.testing.assert_allclose(audit["value"], live_value, atol=1e-6)
    np.testing.assert_allclose(agent.low_actor_hxs, duplicate.low_actor_hxs, atol=1e-6)
    np.testing.assert_allclose(agent.low_critic_hxs, duplicate.low_critic_hxs, atol=1e-6)


def test_focal_override_does_not_mutate_roster_or_clocks_and_matches_preview():
    agent = make_agent()
    obs = np.arange(42, dtype=np.float32).reshape(6, 7) / 40.0
    state = np.arange(11, dtype=np.float32) / 30.0
    roster_before = agent.active_skills.copy()
    duration_before = agent.duration_remaining.copy()
    age_before = agent.skill_age.copy()
    hidden_before = agent.low_actor_hxs[0].copy()

    result = agent.r27_g2_audit_step(
        obs,
        env_id=0,
        state=state,
        focal_agent=2,
        focal_skill=1,
    )
    preview = forward_actor_snapshot(
        agent.low,
        torch.as_tensor(obs[2:3]),
        torch.tensor([1]),
        torch.as_tensor(hidden_before[2:3]),
        inactive_film=False,
    )

    np.testing.assert_array_equal(agent.active_skills, roster_before)
    np.testing.assert_array_equal(agent.duration_remaining, duration_before)
    np.testing.assert_array_equal(agent.skill_age, age_before)
    assert result["visible_skills"].tolist() == [0, 1, 1, 3, 0, 1]
    np.testing.assert_allclose(
        result["pre_tanh_mean"][2], preview.action_mean[0].numpy(), atol=1e-6
    )
    np.testing.assert_allclose(
        result["new_actor_hxs"][2], preview.new_hidden[0].numpy(), atol=1e-6
    )


def test_focal_inactive_film_is_label_invariant_only_for_focal_row():
    obs = np.arange(42, dtype=np.float32).reshape(6, 7) / 35.0
    state = np.arange(11, dtype=np.float32) / 25.0
    first = make_agent()
    second = copy.deepcopy(first)

    out_a = first.r27_g2_audit_step(
        obs,
        env_id=0,
        state=state,
        focal_agent=4,
        focal_skill=1,
        focal_inactive_film=True,
    )
    out_b = second.r27_g2_audit_step(
        obs,
        env_id=0,
        state=state,
        focal_agent=4,
        focal_skill=2,
        focal_inactive_film=True,
    )

    np.testing.assert_array_equal(out_a["deterministic_action"], out_b["deterministic_action"])
    np.testing.assert_array_equal(out_a["new_actor_hxs"], out_b["new_actor_hxs"])
    np.testing.assert_array_equal(out_a["new_critic_hxs"], out_b["new_critic_hxs"])


def test_audit_step_fails_closed_for_unregistered_actor_contract():
    agent = make_agent()
    agent.low = make_policy(actor_team_code=True)
    obs = np.zeros((6, 7), dtype=np.float32)
    state = np.zeros(11, dtype=np.float32)

    with pytest.raises(TypeError, match="team-code conditioning"):
        agent.r27_g2_audit_step(
            obs,
            env_id=0,
            state=state,
            focal_agent=0,
            focal_skill=1,
        )
