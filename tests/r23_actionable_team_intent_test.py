"""R23 Stage-0/architecture: sampled team intent Z must be able to move the
high-level assignment (skill/duration) distributions. R21 autopsy showed the
current architecture routes Z with ~noise gain (forced-Z skill KL ~0.002 at
random-init AND final). The default-off `z_action_gain` residual path gives Z a
direct, controllable pathway into the assignment logits.
"""

import numpy as np
import torch

from ha_ctse_process.config import Config
from ha_ctse_process.standalone_agent import SkillDurationPolicy, StandaloneProcessAgent


def _policy(gain: float) -> SkillDurationPolicy:
    torch.manual_seed(0)
    return SkillDurationPolicy(
        obs_dim=5,
        n_skills=6,
        n_durations=4,
        hidden_dim=16,
        compact_dim=8,
        team_code_dim=8,
        z_action_gain=gain,
    )


def _skill_kl_between_team_vectors(policy: SkillDurationPolicy, tv_a, tv_b) -> float:
    B = 64
    torch.manual_seed(1)
    obs = torch.randn(B, 5)
    prev = torch.zeros(B, dtype=torch.long)
    ages = torch.zeros(B)
    compact = torch.randn(B, 8)
    with torch.no_grad():
        la, _, _ = policy.logits(obs, prev, ages, compact, tv_a)
        lb, _, _ = policy.logits(obs, prev, ages, compact, tv_b)
    pa = torch.softmax(la, -1)
    pb = torch.softmax(lb, -1)
    return float((pa * (torch.log(pa + 1e-12) - torch.log(pb + 1e-12))).sum(-1).mean())


def test_z_action_gain_makes_team_intent_move_skill_assignment():
    # Two distinct team-code vectors (stand-ins for bridge.code_embedding(z)).
    tv_a = torch.zeros(64, 8)
    tv_b = torch.full((64, 8), 2.0)

    kl_on = _skill_kl_between_team_vectors(_policy(1.0), tv_a, tv_b)
    kl_off = _skill_kl_between_team_vectors(_policy(0.0), tv_a, tv_b)

    # With the residual path on, Z clearly moves the skill assignment (well above
    # the R21 decorative band ~0.002) and far more than the default trunk-only path.
    assert kl_on > 0.05
    assert kl_on > 10.0 * max(kl_off, 1e-9)


def test_default_gain_is_off_and_preserves_sbase():
    # Default (gain 0.0): no residual modules created -> S-base architecture unchanged.
    p = _policy(0.0)
    assert float(p.z_action_gain) == 0.0
    assert getattr(p, "z_skill_residual", None) is None
    assert getattr(p, "z_duration_residual", None) is None


def _build_agent(gain: float) -> StandaloneProcessAgent:
    cfg = Config()
    cfg.n_Z = 4
    cfg.n_z = 4
    cfg.legacy_n_skills_override = 4
    cfg.skill_lifetime_candidates = (2, 4)
    cfg.hidden_size = 16
    cfg.embedding_dim = 16
    cfg.opt_compact_dim = 8
    cfg.opt_num_prototypes = 3
    cfg.team_code_dim = 8
    cfg.num_team_codes = 4
    cfg.low_rnn_hidden_size = 16
    cfg.use_prototype_response_skills = False
    cfg.team_bridge_type = "stochastic"
    cfg.z_assignment_residual_gain = gain
    return StandaloneProcessAgent(
        obs_dim=5,
        action_dim=2,
        n_agents=3,
        config=cfg,
        device="cpu",
        action_space_type="continuous",
        num_envs=1,
        state_dim=12,
    )


def test_agent_wires_config_z_assignment_residual_gain_into_high_policy():
    agent = _build_agent(1.0)
    assert float(agent.high.z_action_gain) == 1.0
    assert agent.high.z_skill_residual is not None


def _g_info_actionability(agent):
    """R23-1 Option A: the existing GInfoObjective enumerates team codes Z and
    measures I(Z; skill decision | c,omega). Returns (skill_mi, loss)."""
    from ha_ctse_process.g_info_objective import GInfoObjective, GInfoConfig

    torch.manual_seed(2)
    obj = GInfoObjective(
        GInfoConfig(diagnostic_on=True, objective_on=True, coef_skill=1.0, warmup_steps=0)
    )
    B = 64
    high_obs = torch.randn(B, agent.obs_dim)
    prev = torch.zeros(B, dtype=torch.long)
    ages = torch.zeros(B)
    compact = torch.randn(B, agent.bridge.compact_dim)
    loss, metrics = obj(
        high_policy=agent.high,
        bridge=agent.bridge,
        high_obs=high_obs,
        prev_skills=prev,
        ages=ages,
        compact=compact,
        total_steps=0,
    )
    return float(metrics["g_info_skill_mi"]), float(loss.detach())


def test_r23_1_actionability_objective_is_live_when_residual_path_on():
    # With the R23-0 residual path, enumerating Z produces real skill-decision MI
    # and the actionability objective loss is negative (it MAXimizes that MI).
    skill_mi, loss = _g_info_actionability(_build_agent(1.0))
    assert skill_mi > 0.02
    assert loss < 0.0


def test_r23_1_actionability_is_decorative_without_residual_path():
    # Without the residual path (the R21/Round-10 architecture), the SAME objective
    # sees ~zero MI: Z cannot move the assignment, so actionability pressure is inert.
    # This is why the Round-10 g-info objective failed and why R23-0 is a precondition.
    skill_mi, _loss = _g_info_actionability(_build_agent(0.0))
    assert skill_mi < 0.005


def test_r23_3_team_disc_reward_actionability_gate():
    # R23-3 hard rule: the q_D(Z|future) reward is forbidden until the measured
    # forced-Z assignment KL clears an actionability floor.
    agent = _build_agent(0.5)

    # Floor 0.0 (default) disables the gate -> always open (backward-compatible with R21).
    agent.team_disc_actionability_floor = 0.0
    assert agent._team_disc_actionability_gate_open() is True

    # Floor set, last measured forced-Z KL below it -> reward gated OFF.
    agent.team_disc_actionability_floor = 0.05
    agent._last_forced_z_assignment_kl = 0.02
    assert agent._team_disc_actionability_gate_open() is False

    # Last measured forced-Z KL above the floor -> reward allowed.
    agent._last_forced_z_assignment_kl = 0.10
    assert agent._team_disc_actionability_gate_open() is True
