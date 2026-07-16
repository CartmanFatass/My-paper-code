"""Reset-censored native HMASD renewal overlay for the R43-NRC gate.

The official HMASD source tree remains unchanged.  The treatment decomposes
each native individual categorical factor into an explicit KEEP/RENEW factor
and, only on RENEW, a categorical distribution over non-incumbent skills.
At zero residual this is exactly the source categorical distribution.  The
global k0=50 controller clock, source team token, low policy, and both source
discriminators are retained.
"""

from __future__ import annotations

import math
from types import MethodType
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


R43_FIXED = "fixed_refresh"
R43_TREATMENT = "r43_nrc"
R43_MODES = (R43_FIXED, R43_TREATMENT)
KEEP = 0
RENEW = 1


class ContextHead(nn.Module):
    """Small task-agnostic head over source representation and controller state."""

    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 32) -> None:
        super().__init__()
        self.hidden = nn.Linear(input_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim, output_dim)
        nn.init.orthogonal_(self.hidden.weight, gain=nn.init.calculate_gain("relu"))
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.output(F.gelu(self.hidden(features)))


def _capture_torch_rng() -> dict[str, Any]:
    return {
        "cpu": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def _restore_torch_rng(state: dict[str, Any]) -> None:
    torch.set_rng_state(state["cpu"])
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["cuda"])


def _available_actions(policy: Any, batch_size: int) -> torch.Tensor | None:
    if policy.available_actions is None:
        return None
    return torch.as_tensor(
        np.expand_dims(policy.available_actions, 0).repeat(batch_size, 0),
        dtype=torch.float32,
        device=policy.device,
    )


def _mask_logits(logits: torch.Tensor, available: torch.Tensor | None) -> torch.Tensor:
    if available is None:
        return logits
    return logits.masked_fill(available == 0, -1e10)


def _context_features(
    transformer: nn.Module,
    obs_rep: torch.Tensor,
    team_skill: torch.Tensor,
    working_roster: torch.Tensor,
    working_age: torch.Tensor,
    focal_index: int,
    active_mask: torch.Tensor,
) -> torch.Tensor:
    """Build the environment-agnostic R43 controller context."""

    skill_dim = int(transformer.action_dim)
    num_agents = int(transformer.n_agent)
    safe_roster = working_roster.clamp(min=0, max=skill_dim - 1)
    roster = F.one_hot(safe_roster, num_classes=skill_dim).to(obs_rep.dtype)
    roster = roster * active_mask.unsqueeze(-1).to(obs_rep.dtype)
    roster_valid = (working_roster >= 0).to(obs_rep.dtype)
    team = F.one_hot(
        team_skill.long().clamp(min=0, max=skill_dim - 1),
        num_classes=skill_dim,
    ).to(obs_rep.dtype)
    age = working_age.to(obs_rep.dtype)
    age = age / (age + 50.0)
    focal = torch.zeros(
        (obs_rep.shape[0], num_agents),
        dtype=obs_rep.dtype,
        device=obs_rep.device,
    )
    focal[:, focal_index] = 1.0
    return torch.cat(
        (
            obs_rep[:, 0].detach(),
            obs_rep[:, focal_index + 1].detach(),
            team,
            roster.reshape(obs_rep.shape[0], -1),
            roster_valid,
            age,
            focal,
            active_mask.to(obs_rep.dtype),
        ),
        dim=-1,
    )


def _binary_and_conditional(
    transformer: nn.Module,
    source_logits: torch.Tensor,
    incumbent: torch.Tensor,
    features: torch.Tensor,
) -> tuple[Categorical, Categorical]:
    skill_dim = int(source_logits.shape[-1])
    safe_incumbent = incumbent.long().clamp(min=0, max=skill_dim - 1)
    incumbent_column = safe_incumbent.unsqueeze(-1)
    keep_base = source_logits.gather(-1, incumbent_column).squeeze(-1)
    non_incumbent_mask = F.one_hot(
        safe_incumbent, num_classes=skill_dim
    ).bool()
    conditional_logits = source_logits.masked_fill(non_incumbent_mask, -1e10)
    renew_base = torch.logsumexp(conditional_logits, dim=-1)
    base_binary = torch.stack((keep_base, renew_base), dim=-1)
    residual = transformer.r43_renewal_actor(features)
    return Categorical(logits=base_binary + residual), Categorical(
        logits=conditional_logits
    )


def _critic_values(
    transformer: nn.Module,
    source_values: torch.Tensor,
    features: torch.Tensor,
    focal_index: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    base = source_values[:, focal_index + 1, 0].detach()
    renewal = base + transformer.r43_renewal_critic(features).squeeze(-1)
    skill = base + transformer.r43_skill_event_critic(features).squeeze(-1)
    return renewal, skill


def sample_r43_actions(
    policy: Any,
    cent_obs: Any,
    obs: Any,
    incumbent_roster: Any,
    pre_age: Any,
    active_mask: Any,
    *,
    structural: bool,
    deterministic: bool = False,
) -> dict[str, torch.Tensor]:
    """Sample one complete source-team/R43-individual autoregressive action."""

    from hmasd.algorithms.utils.util import check

    cent = check(cent_obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.share_obs_dim
    )
    local = check(obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.obs_dim
    )
    transformer = policy.transformer
    batch_size = int(local.shape[0])
    num_agents = int(policy.num_agents)
    skill_dim = int(policy.act_dim)
    available = _available_actions(policy, batch_size)
    source_values, obs_rep = transformer.encoder(cent, local)
    actions = torch.zeros(
        (batch_size, num_agents + 1, 1),
        dtype=torch.long,
        device=policy.device,
    )
    combined_logp = torch.zeros(
        (batch_size, num_agents + 1, 1), **transformer.tpdv
    )
    shifted = torch.zeros(
        (batch_size, num_agents + 1, skill_dim + 1), **transformer.tpdv
    )
    shifted[:, 0, 0] = 1.0
    working = torch.as_tensor(
        incumbent_roster, dtype=torch.long, device=policy.device
    ).reshape(batch_size, num_agents).clone()
    working_age = torch.as_tensor(
        pre_age, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents).clone()
    active = torch.as_tensor(
        active_mask, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents)

    renew_token = torch.full(
        (batch_size, num_agents), -1, dtype=torch.long, device=policy.device
    )
    renew_valid = torch.zeros((batch_size, num_agents), **transformer.tpdv)
    renew_logp = torch.zeros_like(renew_valid)
    renew_value = torch.zeros_like(renew_valid)
    skill_valid = torch.zeros_like(renew_valid)
    skill_logp = torch.zeros_like(renew_valid)
    skill_entropy = torch.zeros_like(renew_valid)
    skill_value = torch.zeros_like(renew_valid)
    source_selected_logp = torch.zeros_like(renew_valid)
    prefixes = torch.zeros(
        (batch_size, num_agents, num_agents),
        dtype=torch.long,
        device=policy.device,
    )

    team_logits = _mask_logits(
        transformer.decoder(shifted, obs_rep)[:, 0, :],
        None if available is None else available[:, 0, :],
    )
    team_distribution = Categorical(logits=team_logits)
    team_action = (
        team_distribution.probs.argmax(dim=-1)
        if deterministic
        else team_distribution.sample()
    )
    actions[:, 0, 0] = team_action
    combined_logp[:, 0, 0] = team_distribution.log_prob(team_action)
    shifted = shifted.clone()
    shifted[:, 1, 1:] = F.one_hot(team_action, num_classes=skill_dim).to(
        shifted.dtype
    )

    for focal_index in range(num_agents):
        prefixes[:, focal_index] = working
        source_logits = _mask_logits(
            transformer.decoder(shifted, obs_rep)[:, focal_index + 1, :],
            None if available is None else available[:, focal_index + 1, :],
        )
        source_distribution = Categorical(logits=source_logits)
        features = _context_features(
            transformer,
            obs_rep,
            team_action,
            working,
            working_age,
            focal_index,
            active,
        )
        renewal_v, _ = _critic_values(
            transformer, source_values, features, focal_index
        )
        renew_value[:, focal_index] = renewal_v

        if structural:
            skill_distribution = source_distribution
            selected_skill = (
                skill_distribution.probs.argmax(dim=-1)
                if deterministic
                else skill_distribution.sample()
            )
            selected_renew = torch.full_like(selected_skill, RENEW)
            current_skill_valid = active[:, focal_index].clone()
            skill_valid[:, focal_index] = current_skill_valid
        else:
            incumbent = working[:, focal_index]
            if bool((incumbent < 0).any()):
                raise RuntimeError("normal R43 check has no incumbent skill")
            renewal_distribution, skill_distribution = _binary_and_conditional(
                transformer, source_logits, incumbent, features
            )
            renew_valid[:, focal_index] = active[:, focal_index]
            if deterministic:
                effective = renewal_distribution.probs[:, RENEW].unsqueeze(-1)
                effective = effective * skill_distribution.probs
                effective.scatter_(
                    1,
                    incumbent.unsqueeze(-1),
                    renewal_distribution.probs[:, KEEP].unsqueeze(-1),
                )
                selected_skill = effective.argmax(dim=-1)
                selected_renew = (selected_skill != incumbent).long()
            else:
                selected_renew = renewal_distribution.sample()
                sampled_skill = skill_distribution.sample()
                selected_skill = torch.where(
                    selected_renew == RENEW, sampled_skill, incumbent
                )
            renew_token[:, focal_index] = selected_renew
            current_renew_logp = renewal_distribution.log_prob(selected_renew)
            renew_logp[:, focal_index] = current_renew_logp
            current_skill_valid = (
                (selected_renew == RENEW).to(source_values.dtype)
                * active[:, focal_index]
            )
            skill_valid[:, focal_index] = current_skill_valid

        selected_skill_logp = skill_distribution.log_prob(selected_skill)
        if structural:
            current_renew_logp = torch.zeros_like(selected_skill_logp)
        current_skill_logp = selected_skill_logp * current_skill_valid
        skill_logp[:, focal_index] = current_skill_logp
        skill_entropy[:, focal_index] = (
            skill_distribution.entropy() * current_skill_valid
        )
        source_selected_logp[:, focal_index] = source_distribution.log_prob(
            selected_skill
        )
        factor_logp = current_skill_logp
        if not structural:
            factor_logp = current_renew_logp + factor_logp
        combined_logp[:, focal_index + 1, 0] = factor_logp
        actions[:, focal_index + 1, 0] = selected_skill
        working = working.clone()
        working_age = working_age.clone()
        working[:, focal_index] = selected_skill
        working_age[:, focal_index] = torch.where(
            selected_renew == RENEW,
            torch.zeros_like(working_age[:, focal_index]),
            working_age[:, focal_index],
        )
        post_features = _context_features(
            transformer,
            obs_rep,
            team_action,
            working,
            working_age,
            focal_index,
            active,
        )
        _, skill_v = _critic_values(
            transformer, source_values, post_features, focal_index
        )
        skill_value[:, focal_index] = skill_v
        if focal_index + 2 < num_agents + 1:
            shifted = shifted.clone()
            shifted[:, focal_index + 2, 1:] = F.one_hot(
                selected_skill, num_classes=skill_dim
            ).to(shifted.dtype)

    source_error = (
        combined_logp[:, 1:, 0] - source_selected_logp
    ).abs()
    return {
        "values": source_values,
        "actions": actions,
        "combined_logp": combined_logp,
        "team_logp": combined_logp[:, 0, 0],
        "team_entropy": team_distribution.entropy(),
        "renew_token": renew_token,
        "renew_valid": renew_valid,
        "renew_logp": renew_logp,
        "renew_value": renew_value,
        "skill_valid": skill_valid,
        "skill_logp": skill_logp,
        "skill_entropy": skill_entropy,
        "skill_value": skill_value,
        "prefixes": prefixes,
        "post_roster": working,
        "post_age": working_age,
        "source_equivalence_error": source_error,
    }


def evaluate_r43_factors(
    policy: Any,
    cent_obs: Any,
    obs: Any,
    actions: Any,
    pre_roster: Any,
    pre_age: Any,
    active_mask: Any,
    renew_token: Any,
    renew_valid: Any,
    skill_valid: Any,
    prefix_truth: Any | None = None,
) -> dict[str, torch.Tensor]:
    """Teacher-force the exact factors stored at collection."""

    from hmasd.algorithms.utils.util import check

    cent = check(cent_obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.share_obs_dim
    )
    local = check(obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.obs_dim
    )
    action = check(actions).to(**policy.tpdv).long().reshape(
        -1, policy.num_agents + 1, 1
    )
    batch_size = int(local.shape[0])
    num_agents = int(policy.num_agents)
    skill_dim = int(policy.act_dim)
    transformer = policy.transformer
    available = _available_actions(policy, batch_size)
    source_values, obs_rep = transformer.encoder(cent, local)
    working = torch.as_tensor(
        pre_roster, dtype=torch.long, device=policy.device
    ).reshape(batch_size, num_agents).clone()
    working_age = torch.as_tensor(
        pre_age, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents).clone()
    active = torch.as_tensor(
        active_mask, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents)
    renew = torch.as_tensor(
        renew_token, dtype=torch.long, device=policy.device
    ).reshape(batch_size, num_agents)
    renew_mask = torch.as_tensor(
        renew_valid, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents)
    skill_mask = torch.as_tensor(
        skill_valid, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, num_agents)
    truth = None
    if prefix_truth is not None:
        truth = torch.as_tensor(
            prefix_truth, dtype=torch.long, device=policy.device
        ).reshape(batch_size, num_agents, num_agents)

    shifted = torch.zeros(
        (batch_size, num_agents + 1, skill_dim + 1), **transformer.tpdv
    )
    shifted[:, 0, 0] = 1.0
    team_action = action[:, 0, 0]
    team_logits = _mask_logits(
        transformer.decoder(shifted, obs_rep)[:, 0, :],
        None if available is None else available[:, 0, :],
    )
    team_distribution = Categorical(logits=team_logits)
    team_logp = team_distribution.log_prob(team_action)
    shifted = shifted.clone()
    shifted[:, 1, 1:] = F.one_hot(team_action, num_classes=skill_dim).to(
        shifted.dtype
    )

    combined = torch.zeros(
        (batch_size, num_agents + 1), **transformer.tpdv
    )
    combined[:, 0] = team_logp
    renewal_logp = torch.zeros((batch_size, num_agents), **transformer.tpdv)
    renewal_entropy = torch.zeros_like(renewal_logp)
    renewal_values = torch.zeros_like(renewal_logp)
    conditional_logp = torch.zeros_like(renewal_logp)
    conditional_entropy = torch.zeros_like(renewal_logp)
    skill_values = torch.zeros_like(renewal_logp)
    source_selected = torch.zeros_like(renewal_logp)
    prefix_mismatch = torch.zeros((), dtype=torch.long, device=policy.device)

    for focal_index in range(num_agents):
        if truth is not None:
            prefix_mismatch = prefix_mismatch + (
                working != truth[:, focal_index]
            ).sum()
        source_logits = _mask_logits(
            transformer.decoder(shifted, obs_rep)[:, focal_index + 1, :],
            None if available is None else available[:, focal_index + 1, :],
        )
        source_distribution = Categorical(logits=source_logits)
        selected_skill = action[:, focal_index + 1, 0]
        source_selected[:, focal_index] = source_distribution.log_prob(
            selected_skill
        )
        features = _context_features(
            transformer,
            obs_rep,
            team_action,
            working,
            working_age,
            focal_index,
            active,
        )
        renewal_v, _ = _critic_values(
            transformer, source_values, features, focal_index
        )
        renewal_values[:, focal_index] = renewal_v
        structural_rows = renew_mask[:, focal_index] == 0
        normal_rows = ~structural_rows
        factor_logp = torch.zeros(batch_size, **transformer.tpdv)

        if bool(structural_rows.any()):
            structural_skill_valid = skill_mask[:, focal_index] > 0
            if bool((structural_rows & ~structural_skill_valid).any()):
                raise RuntimeError("structural R43 row has no skill factor")
            conditional_logp[structural_rows, focal_index] = (
                source_distribution.log_prob(selected_skill)[structural_rows]
            )
            conditional_entropy[structural_rows, focal_index] = (
                source_distribution.entropy()[structural_rows]
            )
            factor_logp[structural_rows] = conditional_logp[
                structural_rows, focal_index
            ]

        if bool(normal_rows.any()):
            incumbent = working[:, focal_index]
            invalid_incumbent = (incumbent < 0) | (incumbent >= skill_dim)
            if bool(invalid_incumbent[normal_rows].any()):
                raise RuntimeError(
                    "normal replay row has invalid incumbent: "
                    f"focal={focal_index}, incumbent={incumbent.detach().cpu().tolist()}, "
                    f"normal={normal_rows.detach().cpu().tolist()}"
                )
            if bool(((selected_skill < 0) | (selected_skill >= skill_dim)).any()):
                raise RuntimeError(
                    "replay row has invalid selected skill: "
                    f"focal={focal_index}, skill={selected_skill.detach().cpu().tolist()}"
                )
            renewal_distribution, skill_distribution = _binary_and_conditional(
                transformer, source_logits, incumbent, features
            )
            selected_renew = renew[:, focal_index]
            safe_selected_renew = selected_renew.clamp(min=KEEP, max=RENEW)
            expected_renew = (selected_skill != incumbent).long()
            if bool((selected_renew[normal_rows] != expected_renew[normal_rows]).any()):
                raise RuntimeError("stored renewal token contradicts the post skill")
            expected_skill_valid = (selected_renew == RENEW).to(skill_mask.dtype)
            if bool(
                (
                    skill_mask[normal_rows, focal_index]
                    != expected_skill_valid[normal_rows]
                ).any()
            ):
                raise RuntimeError("stored conditional-skill mask is invalid")
            renewal_logp[normal_rows, focal_index] = renewal_distribution.log_prob(
                safe_selected_renew
            )[normal_rows]
            renewal_entropy[normal_rows, focal_index] = renewal_distribution.entropy()[
                normal_rows
            ]
            conditional_logp[normal_rows, focal_index] = (
                skill_distribution.log_prob(selected_skill)[normal_rows]
                * skill_mask[normal_rows, focal_index]
            )
            conditional_entropy[normal_rows, focal_index] = (
                skill_distribution.entropy()[normal_rows]
                * skill_mask[normal_rows, focal_index]
            )
            factor_logp[normal_rows] = (
                renewal_logp[normal_rows, focal_index]
                + conditional_logp[normal_rows, focal_index]
            )

        combined[:, focal_index + 1] = factor_logp
        selected_renew_for_age = torch.where(
            structural_rows,
            torch.full_like(renew[:, focal_index], RENEW),
            renew[:, focal_index],
        )
        working = working.clone()
        working_age = working_age.clone()
        working[:, focal_index] = selected_skill
        working_age[:, focal_index] = torch.where(
            selected_renew_for_age == RENEW,
            torch.zeros_like(working_age[:, focal_index]),
            working_age[:, focal_index],
        )
        post_features = _context_features(
            transformer,
            obs_rep,
            team_action,
            working,
            working_age,
            focal_index,
            active,
        )
        _, skill_v = _critic_values(
            transformer, source_values, post_features, focal_index
        )
        skill_values[:, focal_index] = skill_v
        if focal_index + 2 < num_agents + 1:
            shifted = shifted.clone()
            shifted[:, focal_index + 2, 1:] = F.one_hot(
                selected_skill, num_classes=skill_dim
            ).to(shifted.dtype)

    return {
        "source_values": source_values,
        "team_logp": team_logp,
        "team_entropy": team_distribution.entropy(),
        "renew_logp": renewal_logp,
        "renew_entropy": renewal_entropy,
        "renew_value": renewal_values,
        "skill_logp": conditional_logp,
        "skill_entropy": conditional_entropy,
        "skill_value": skill_values,
        "combined_logp": combined,
        "source_selected_logp": source_selected,
        "prefix_mismatch": prefix_mismatch,
    }


def boundary_critic_values(
    policy: Any,
    cent_obs: Any,
    obs: Any,
    team_skill: Any,
    roster: Any,
    age: Any,
    active_mask: Any,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Evaluate critic-only continuation state without sampling an action."""

    from hmasd.algorithms.utils.util import check

    cent = check(cent_obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.share_obs_dim
    )
    local = check(obs).to(**policy.tpdv).reshape(
        -1, policy.num_agents, policy.obs_dim
    )
    transformer = policy.transformer
    source_values, obs_rep = transformer.encoder(cent, local)
    batch_size = int(local.shape[0])
    current_team = torch.as_tensor(
        team_skill, dtype=torch.long, device=policy.device
    ).reshape(batch_size)
    working = torch.as_tensor(
        roster, dtype=torch.long, device=policy.device
    ).reshape(batch_size, policy.num_agents)
    working_age = torch.as_tensor(
        age, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, policy.num_agents)
    active = torch.as_tensor(
        active_mask, dtype=torch.float32, device=policy.device
    ).reshape(batch_size, policy.num_agents)
    renewal_values = []
    skill_values = []
    for focal_index in range(policy.num_agents):
        features = _context_features(
            transformer,
            obs_rep,
            current_team,
            working,
            working_age,
            focal_index,
            active,
        )
        renewal, skill = _critic_values(
            transformer, source_values, features, focal_index
        )
        renewal_values.append(renewal)
        skill_values.append(skill)
    return torch.stack(renewal_values, dim=1), torch.stack(skill_values, dim=1)


def _patch_buffer(buffer: Any, num_agents: int) -> None:
    shape = (buffer.episode_length, buffer.n_rollout_threads)
    buffer.r43_pre_roster = np.full((*shape, num_agents), -1, dtype=np.int64)
    buffer.r43_pre_age = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_active_mask = np.ones((*shape, num_agents), dtype=np.float32)
    buffer.r43_agent_order = np.broadcast_to(
        np.arange(num_agents, dtype=np.int64), (*shape, num_agents)
    ).copy()
    buffer.r43_renew_token = np.full((*shape, num_agents), -1, dtype=np.int64)
    buffer.r43_renew_valid = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_renew_old_logp = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_skill_valid = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_new_skill = np.zeros((*shape, num_agents), dtype=np.int64)
    buffer.r43_skill_old_logp = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_working_prefix = np.full(
        (*shape, num_agents, num_agents), -1, dtype=np.int64
    )
    buffer.r43_renew_value = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_skill_value = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_renew_returns = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_skill_returns = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_renew_advantages = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_skill_advantages = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_structural = np.zeros(shape, dtype=np.float32)
    buffer.r43_policy_truncated = np.zeros((*shape, num_agents), dtype=np.float32)
    buffer.r43_continuation_actor_valid = np.zeros(
        (*shape, num_agents), dtype=np.float32
    )
    buffer.r43_source_equivalence_error = np.zeros(
        (*shape, num_agents), dtype=np.float32
    )


def _empty_clock_ledger(num_agents: int, skill_dim: int) -> dict[str, Any]:
    return {
        "global_check_calls": 0,
        "env_check_rows": 0,
        "structural_env_assignments": 0,
        "normal_env_checks": 0,
        "auto_resets": 0,
        "auto_reset_high_actions": 0,
        "auto_reset_roster_violations": 0,
        "auto_reset_team_violations": 0,
        "auto_reset_age_violations": 0,
        "low_actor_hidden_reset_violations": 0,
        "low_critic_hidden_reset_violations": 0,
        "execution_fragments_env_reset_censored": 0,
        "assignment_spell_reset_closures": 0,
        "update_policy_truncations": 0,
        "continuation_critic_only_states": 0,
        "continuation_actor_valid_count": 0,
        "events": 0,
        "agent_keep": [0 for _ in range(num_agents)],
        "agent_renew": [0 for _ in range(num_agents)],
        "discordant": 0,
        "full_sync_renew": 0,
        "renew_skill_counts": [0 for _ in range(skill_dim)],
        "same_label_renew": 0,
        "early_reset_blocks": 0,
        "early_reset_reward_blocks": 0,
        "post_reset_steps_in_same_block": 0,
        "zero_init_source_equivalence_max": 0.0,
    }


def _wrap_runtime_clock(runner: Any, mode: str, skill_dim: int) -> None:
    runner.r43_clock_ledger = _empty_clock_ledger(runner.num_agents, skill_dim)
    runner._r43_primitive_rewards = []
    runner._r43_primitive_dones = []
    runner._r43_in_env_step = False
    original_env_step = runner.envs.step

    def env_step(actions: Any):
        pre_high_calls = runner.r43_clock_ledger["global_check_calls"]
        pre_roster = (
            None
            if getattr(runner, "_r43_current_roster", None) is None
            else runner._r43_current_roster.copy()
        )
        pre_team = (
            None
            if getattr(runner, "_r43_current_team", None) is None
            else runner._r43_current_team.copy()
        )
        pre_age = (
            None
            if getattr(runner, "_r43_age", None) is None
            else runner._r43_age.copy()
        )
        runner._r43_in_env_step = True
        try:
            result = original_env_step(actions)
        finally:
            runner._r43_in_env_step = False
        _, _, rewards, dones, _, _ = result
        dones_env = np.all(dones, axis=1)
        runner._r43_primitive_rewards.append(
            np.mean(rewards, axis=1).reshape(runner.n_rollout_threads).copy()
        )
        runner._r43_primitive_dones.append(dones_env.copy())
        if mode == R43_TREATMENT and runner._r43_age is not None:
            runner._r43_age += 1.0
        resets = int(dones_env.sum())
        if resets:
            ledger = runner.r43_clock_ledger
            ledger["auto_resets"] += resets
            ledger["execution_fragments_env_reset_censored"] += resets
            if ledger["global_check_calls"] != pre_high_calls:
                ledger["auto_reset_high_actions"] += resets
            if pre_roster is not None and not np.array_equal(
                runner._r43_current_roster, pre_roster
            ):
                ledger["auto_reset_roster_violations"] += resets
            if pre_team is not None and not np.array_equal(
                runner._r43_current_team, pre_team
            ):
                ledger["auto_reset_team_violations"] += resets
            if mode == R43_TREATMENT and pre_age is not None:
                expected = pre_age + 1.0
                if not np.array_equal(runner._r43_age, expected):
                    ledger["auto_reset_age_violations"] += resets
        return result

    runner.envs.step = env_step
    original_l_insert = runner.l_insert

    def l_insert(self: Any, data: Any) -> None:
        dones_env = np.all(data[3], axis=1)
        original_l_insert(data)
        if bool(dones_env.any()):
            actor_states = data[-2]
            critic_states = data[-1]
            if np.any(actor_states[dones_env] != 0):
                self.r43_clock_ledger["low_actor_hidden_reset_violations"] += int(
                    dones_env.sum()
                )
            if np.any(critic_states[dones_env] != 0):
                self.r43_clock_ledger["low_critic_hidden_reset_violations"] += int(
                    dones_env.sum()
                )

    runner.l_insert = MethodType(l_insert, runner)


def _patch_fixed_runner(runner: Any) -> None:
    original_h_collect = runner.h_collect
    runner._r43_current_roster = None
    runner._r43_current_team = None
    runner._r43_fixed_initialized = False

    @torch.no_grad()
    def h_collect(self: Any, step: int):
        if self._r43_in_env_step:
            raise RuntimeError("high action requested from inside env auto-reset")
        result = original_h_collect(step)
        values, actions, log_probs = result
        ledger = self.r43_clock_ledger
        ledger["global_check_calls"] += 1
        ledger["env_check_rows"] += self.n_rollout_threads
        if not self._r43_fixed_initialized:
            ledger["structural_env_assignments"] += self.n_rollout_threads
            self._r43_fixed_initialized = True
        else:
            ledger["normal_env_checks"] += self.n_rollout_threads
        self._r43_current_team = actions[:, 0, 0].astype(np.int64, copy=True)
        self._r43_current_roster = actions[:, 1:, 0].astype(np.int64, copy=True)
        return values, actions, log_probs

    runner.h_collect = MethodType(h_collect, runner)


def _patch_treatment_runner(runner: Any, skill_dim: int) -> None:
    envs = runner.n_rollout_threads
    agents = runner.num_agents
    runner._r43_current_roster = np.full((envs, agents), -1, dtype=np.int64)
    runner._r43_current_team = np.full(envs, -1, dtype=np.int64)
    runner._r43_age = np.zeros((envs, agents), dtype=np.float32)
    runner._r43_initialized = np.zeros(envs, dtype=bool)

    @torch.no_grad()
    def h_collect(self: Any, step: int):
        if self._r43_in_env_step:
            raise RuntimeError("high action requested from inside env auto-reset")
        self.h_trainer.prep_rollout()
        structural = not bool(self._r43_initialized.all())
        if structural and bool(self._r43_initialized.any()):
            raise RuntimeError("R43 batched structural initialization diverged")
        active = np.ones((envs, agents), dtype=np.float32)
        pre_roster = self._r43_current_roster.copy()
        pre_age = self._r43_age.copy()
        sampled = sample_r43_actions(
            self.h_policy,
            np.concatenate(self.h_buffer.share_obs[step]),
            np.concatenate(self.h_buffer.obs[step]),
            pre_roster,
            pre_age,
            active,
            structural=structural,
            deterministic=False,
        )
        values = sampled["values"].detach().cpu().numpy()
        actions = sampled["actions"].detach().cpu().numpy()
        combined = sampled["combined_logp"].detach().cpu().numpy()
        buffer = self.h_buffer
        buffer.r43_pre_roster[step] = pre_roster
        buffer.r43_pre_age[step] = pre_age
        buffer.r43_active_mask[step] = active
        buffer.r43_renew_token[step] = sampled["renew_token"].cpu().numpy()
        buffer.r43_renew_valid[step] = sampled["renew_valid"].cpu().numpy()
        buffer.r43_renew_old_logp[step] = sampled["renew_logp"].cpu().numpy()
        buffer.r43_skill_valid[step] = sampled["skill_valid"].cpu().numpy()
        buffer.r43_new_skill[step] = sampled["post_roster"].cpu().numpy()
        buffer.r43_skill_old_logp[step] = sampled["skill_logp"].cpu().numpy()
        buffer.r43_working_prefix[step] = sampled["prefixes"].cpu().numpy()
        buffer.r43_renew_value[step] = sampled["renew_value"].cpu().numpy()
        buffer.r43_skill_value[step] = sampled["skill_value"].cpu().numpy()
        buffer.r43_structural[step] = float(structural)
        buffer.r43_source_equivalence_error[step] = sampled[
            "source_equivalence_error"
        ].cpu().numpy()
        if self.r43_clock_ledger["global_check_calls"] < 2:
            self.r43_clock_ledger["zero_init_source_equivalence_max"] = max(
                float(
                    self.r43_clock_ledger["zero_init_source_equivalence_max"]
                ),
                float(sampled["source_equivalence_error"].max().item()),
            )
        if step == 0 and bool(self._r43_initialized.all()):
            buffer.r43_continuation_actor_valid[step] = 0.0
        self._r43_current_team = actions[:, 0, 0].astype(np.int64, copy=True)
        self._r43_current_roster = actions[:, 1:, 0].astype(np.int64, copy=True)
        self._r43_age = sampled["post_age"].cpu().numpy().astype(np.float32)
        self._r43_initialized[:] = True

        ledger = self.r43_clock_ledger
        ledger["global_check_calls"] += 1
        ledger["env_check_rows"] += envs
        if structural:
            ledger["structural_env_assignments"] += envs
        else:
            ledger["normal_env_checks"] += envs
            tokens = sampled["renew_token"].cpu().numpy()
            post = self._r43_current_roster
            ledger["events"] += envs
            for agent_index in range(agents):
                renew = tokens[:, agent_index] == RENEW
                ledger["agent_renew"][agent_index] += int(renew.sum())
                ledger["agent_keep"][agent_index] += int((~renew).sum())
                for label in range(skill_dim):
                    ledger["renew_skill_counts"][label] += int(
                        (renew & (post[:, agent_index] == label)).sum()
                    )
                ledger["same_label_renew"] += int(
                    (renew & (post[:, agent_index] == pre_roster[:, agent_index])).sum()
                )
            if agents == 2:
                ledger["discordant"] += int(
                    np.logical_xor(tokens[:, 0] == RENEW, tokens[:, 1] == RENEW).sum()
                )
            ledger["full_sync_renew"] += int((tokens == RENEW).all(axis=1).sum())
        return values, actions, combined

    runner.h_collect = MethodType(h_collect, runner)

    original_compute = runner.compute

    @torch.no_grad()
    def compute(self: Any) -> None:
        _compute_custom_credit(self)
        original_compute()

    runner.compute = MethodType(compute, runner)


def _denormalize_values(trainer: Any, values: np.ndarray) -> np.ndarray:
    if trainer._use_valuenorm:
        return trainer.value_normalizer.denormalize(values)
    return np.asarray(values, dtype=np.float32)


def _compute_custom_credit(runner: Any) -> None:
    rewards = np.asarray(runner._r43_primitive_rewards, dtype=np.float32)
    dones = np.asarray(runner._r43_primitive_dones, dtype=bool)
    expected = runner.episode_length
    if rewards.shape != (expected, runner.n_rollout_threads):
        raise RuntimeError(
            f"R43 primitive reward trace {rewards.shape}, expected "
            f"({expected}, {runner.n_rollout_threads})"
        )
    if dones.shape != rewards.shape:
        raise RuntimeError("R43 primitive done trace shape mismatch")
    interval = runner.skill_interval
    gamma = float(runner.h_buffer.gamma)
    gae_lambda = float(runner.h_buffer.gae_lambda)
    discount = np.power(gamma, np.arange(interval, dtype=np.float32))
    block_returns = np.stack(
        [
            (rewards[start : start + interval] * discount[:, None]).sum(axis=0)
            for start in range(0, expected, interval)
        ],
        axis=0,
    )
    if block_returns.shape[0] != 2:
        raise RuntimeError("R43 first gate requires exactly two controller blocks")

    runner.h_trainer.prep_rollout()
    boundary_renew, boundary_skill = boundary_critic_values(
        runner.h_policy,
        np.concatenate(runner.h_buffer.share_obs[-1]),
        np.concatenate(runner.h_buffer.obs[-1]),
        runner._r43_current_team,
        runner._r43_current_roster,
        runner._r43_age,
        np.ones_like(runner._r43_age, dtype=np.float32),
    )
    boundary_renew_np = boundary_renew.cpu().numpy()
    boundary_skill_np = boundary_skill.cpu().numpy()
    buffer = runner.h_buffer
    renewal_value = _denormalize_values(
        runner.h_trainer, buffer.r43_renew_value
    )
    skill_value = _denormalize_values(runner.h_trainer, buffer.r43_skill_value)
    boundary_renew_raw = _denormalize_values(
        runner.h_trainer, boundary_renew_np
    )
    boundary_skill_raw = _denormalize_values(
        runner.h_trainer, boundary_skill_np
    )
    repeated_rewards = np.repeat(block_returns[:, :, None], runner.num_agents, axis=2)
    controller_gamma = gamma ** interval

    renewal_delta_1 = (
        repeated_rewards[1]
        + controller_gamma * boundary_renew_raw
        - renewal_value[1]
    )
    renewal_adv_1 = renewal_delta_1
    renewal_delta_0 = (
        repeated_rewards[0]
        + controller_gamma * renewal_value[1]
        - renewal_value[0]
    )
    renewal_adv_0 = (
        renewal_delta_0
        + controller_gamma * gae_lambda * renewal_adv_1
    )
    buffer.r43_renew_advantages[0] = renewal_adv_0
    buffer.r43_renew_advantages[1] = renewal_adv_1
    buffer.r43_renew_returns[:] = buffer.r43_renew_advantages + renewal_value

    skill_delta_1 = (
        repeated_rewards[1]
        + controller_gamma * boundary_skill_raw
        - skill_value[1]
    )
    skill_adv_1 = skill_delta_1
    skill_delta_0 = (
        repeated_rewards[0]
        + controller_gamma * skill_value[1]
        - skill_value[0]
    )
    same_event = (buffer.r43_renew_token[1] == KEEP).astype(np.float32)
    skill_adv_0 = (
        skill_delta_0
        + controller_gamma * gae_lambda * same_event * skill_adv_1
    )
    buffer.r43_skill_advantages[0] = skill_adv_0
    buffer.r43_skill_advantages[1] = skill_adv_1
    buffer.r43_skill_returns[:] = buffer.r43_skill_advantages + skill_value
    buffer.r43_policy_truncated[1] = 1.0
    runner.r43_clock_ledger["update_policy_truncations"] += (
        runner.n_rollout_threads * runner.num_agents
    )
    runner.r43_clock_ledger["continuation_critic_only_states"] += (
        runner.n_rollout_threads * runner.num_agents
    )

    for block_index, start in enumerate((0, interval)):
        block_done = dones[start : start + interval]
        for env_index in range(runner.n_rollout_threads):
            offsets = np.flatnonzero(block_done[:, env_index])
            if offsets.size and int(offsets[0]) < interval - 1:
                runner.r43_clock_ledger["early_reset_blocks"] += 1
                first = int(offsets[0])
                if rewards[start + first, env_index] != 0.0:
                    runner.r43_clock_ledger["early_reset_reward_blocks"] += 1
                runner.r43_clock_ledger["post_reset_steps_in_same_block"] += (
                    interval - first - 1
                )
    runner._r43_primitive_rewards.clear()
    runner._r43_primitive_dones.clear()


def _masked_normalize(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    selected = values[mask > 0]
    if selected.size == 0:
        raise RuntimeError("R43 actor factor has no valid samples")
    normalized = (values - float(selected.mean())) / (float(selected.std()) + 1e-5)
    return normalized.astype(np.float32)


def _custom_value_loss(
    trainer: Any,
    values: torch.Tensor,
    old_values: torch.Tensor,
    returns: torch.Tensor,
) -> torch.Tensor:
    clipped = old_values + (values - old_values).clamp(
        -trainer.clip_param, trainer.clip_param
    )
    target = (
        trainer.value_normalizer.normalize(returns)
        if trainer._use_valuenorm
        else returns
    )
    error = target - values
    clipped_error = target - clipped
    if trainer._use_huber_loss:
        delta = float(trainer.huber_delta)
        loss = torch.where(
            error.abs() <= delta,
            0.5 * error.pow(2),
            delta * (error.abs() - 0.5 * delta),
        )
        clipped_loss = torch.where(
            clipped_error.abs() <= delta,
            0.5 * clipped_error.pow(2),
            delta * (clipped_error.abs() - 0.5 * delta),
        )
    else:
        loss = 0.5 * error.pow(2)
        clipped_loss = 0.5 * clipped_error.pow(2)
    if trainer._use_clipped_value_loss:
        loss = torch.maximum(loss, clipped_loss)
    return loss.mean()


def _patch_treatment_trainer(trainer: Any, buffer: Any) -> None:
    trainer.r43_gradient_stats = {
        "renewal_actor_nonzero_steps": 0,
        "renewal_critic_nonzero_steps": 0,
        "skill_event_critic_nonzero_steps": 0,
        "maximum_prefix_mismatch": 0,
    }

    def train(self: Any, replay_buffer: Any) -> dict[str, Any]:
        if replay_buffer is not buffer:
            raise RuntimeError("R43 trainer received an unexpected buffer")
        source_adv = replay_buffer.advantages.copy()
        source_adv = (
            source_adv - float(np.nanmean(source_adv))
        ) / (float(np.nanstd(source_adv)) + 1e-5)
        renewal_adv = _masked_normalize(
            replay_buffer.r43_renew_advantages,
            replay_buffer.r43_renew_valid,
        )
        skill_adv = _masked_normalize(
            replay_buffer.r43_skill_advantages,
            replay_buffer.r43_skill_valid,
        )
        total_rows = replay_buffer.episode_length * replay_buffer.n_rollout_threads
        arrays = {
            "share_obs": replay_buffer.share_obs[:-1].reshape(
                total_rows, *replay_buffer.share_obs.shape[2:]
            ),
            "obs": replay_buffer.obs[:-1].reshape(
                total_rows, *replay_buffer.obs.shape[2:]
            ),
            "actions": replay_buffer.actions.reshape(
                total_rows, *replay_buffer.actions.shape[2:]
            ),
            "source_old_logp": replay_buffer.action_log_probs.reshape(
                total_rows, *replay_buffer.action_log_probs.shape[2:]
            ),
            "source_value_preds": replay_buffer.value_preds[:-1].reshape(
                total_rows, *replay_buffer.value_preds.shape[2:]
            ),
            "source_returns": replay_buffer.returns[:-1].reshape(
                total_rows, *replay_buffer.returns.shape[2:]
            ),
            "source_adv": source_adv.reshape(total_rows, *source_adv.shape[2:]),
            "pre_roster": replay_buffer.r43_pre_roster.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "pre_age": replay_buffer.r43_pre_age.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "active": replay_buffer.r43_active_mask.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew": replay_buffer.r43_renew_token.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew_valid": replay_buffer.r43_renew_valid.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew_old_logp": replay_buffer.r43_renew_old_logp.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew_value": replay_buffer.r43_renew_value.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew_returns": replay_buffer.r43_renew_returns.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "renew_adv": renewal_adv.reshape(total_rows, replay_buffer.num_agents),
            "skill_valid": replay_buffer.r43_skill_valid.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "skill_old_logp": replay_buffer.r43_skill_old_logp.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "skill_value": replay_buffer.r43_skill_value.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "skill_returns": replay_buffer.r43_skill_returns.reshape(
                total_rows, replay_buffer.num_agents
            ),
            "skill_adv": skill_adv.reshape(total_rows, replay_buffer.num_agents),
            "prefix": replay_buffer.r43_working_prefix.reshape(
                total_rows, replay_buffer.num_agents, replay_buffer.num_agents
            ),
        }
        train_info = {
            "h_value_loss": 0.0,
            "h_policy_loss": 0.0,
            "h_dist_entropy": 0.0,
            "h_actor_grad_norm": 0.0,
            "h_critic_grad_norm": 0.0,
            "h_ratio": 0.0,
            "r43_renew_value_loss": 0.0,
            "r43_skill_value_loss": 0.0,
            "r43_renew_entropy": 0.0,
        }
        for _ in range(self.ppo_epoch):
            indices = torch.randperm(total_rows).cpu().numpy()
            evaluated = evaluate_r43_factors(
                self.policy,
                arrays["share_obs"][indices].reshape(
                    -1, *arrays["share_obs"].shape[2:]
                ),
                arrays["obs"][indices].reshape(-1, *arrays["obs"].shape[2:]),
                arrays["actions"][indices],
                arrays["pre_roster"][indices],
                arrays["pre_age"][indices],
                arrays["active"][indices],
                arrays["renew"][indices],
                arrays["renew_valid"][indices],
                arrays["skill_valid"][indices],
                arrays["prefix"][indices],
            )
            prefix_mismatch = int(evaluated["prefix_mismatch"].item())
            self.r43_gradient_stats["maximum_prefix_mismatch"] = max(
                self.r43_gradient_stats["maximum_prefix_mismatch"], prefix_mismatch
            )
            if prefix_mismatch:
                raise RuntimeError("R43 teacher-forced working prefix mismatch")
            device = self.device
            def tensor(name: str) -> torch.Tensor:
                return torch.as_tensor(
                    arrays[name][indices], dtype=torch.float32, device=device
                )

            source_old = tensor("source_old_logp").squeeze(-1)
            team_old = source_old[:, 0]
            team_adv = tensor("source_adv")[:, 0, 0]
            team_ratio = torch.exp(evaluated["team_logp"] - team_old)
            team_objective = torch.minimum(
                team_ratio * team_adv,
                team_ratio.clamp(1.0 - self.clip_param, 1.0 + self.clip_param)
                * team_adv,
            )
            renew_mask = tensor("renew_valid")
            renew_ratio = torch.exp(
                evaluated["renew_logp"] - tensor("renew_old_logp")
            )
            renew_target = tensor("renew_adv")
            renew_objective = torch.minimum(
                renew_ratio * renew_target,
                renew_ratio.clamp(1.0 - self.clip_param, 1.0 + self.clip_param)
                * renew_target,
            ) * renew_mask
            skill_mask = tensor("skill_valid")
            skill_ratio = torch.exp(
                evaluated["skill_logp"] - tensor("skill_old_logp")
            )
            skill_target = tensor("skill_adv")
            skill_objective = torch.minimum(
                skill_ratio * skill_target,
                skill_ratio.clamp(1.0 - self.clip_param, 1.0 + self.clip_param)
                * skill_target,
            ) * skill_mask
            policy_loss = -(
                team_objective
                + renew_objective.sum(dim=1)
                + skill_objective.sum(dim=1)
            ).div(float(replay_buffer.num_agents + 1)).mean()
            entropy = (
                evaluated["team_entropy"]
                + (evaluated["skill_entropy"] * skill_mask).sum(dim=1)
            ).div(float(replay_buffer.num_agents + 1)).mean()

            source_value_loss = self.cal_value_loss(
                evaluated["source_values"].reshape(-1, 1),
                tensor("source_value_preds").reshape(-1, 1),
                tensor("source_returns").reshape(-1, 1),
            )
            renewal_value_loss = _custom_value_loss(
                self,
                evaluated["renew_value"],
                tensor("renew_value"),
                tensor("renew_returns"),
            )
            skill_value_loss = _custom_value_loss(
                self,
                evaluated["skill_value"],
                tensor("skill_value"),
                tensor("skill_returns"),
            )
            value_loss = source_value_loss + 0.5 * (
                renewal_value_loss + skill_value_loss
            )
            loss = (
                policy_loss
                - entropy * self.entropy_coef
                + value_loss * self.value_loss_coef
            )
            self.policy.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            for module_name, field in (
                ("r43_renewal_actor", "renewal_actor_nonzero_steps"),
                ("r43_renewal_critic", "renewal_critic_nonzero_steps"),
                ("r43_skill_event_critic", "skill_event_critic_nonzero_steps"),
            ):
                module = getattr(self.policy.transformer, module_name)
                norm_sq = sum(
                    float(parameter.grad.detach().float().pow(2).sum().item())
                    for parameter in module.parameters()
                    if parameter.grad is not None
                )
                if math.isfinite(norm_sq) and norm_sq > 0.0:
                    self.r43_gradient_stats[field] += 1
            if self._use_max_grad_norm:
                grad_norm = nn.utils.clip_grad_norm_(
                    self.policy.transformer.parameters(), self.max_grad_norm
                )
            else:
                norm_sq = sum(
                    float(parameter.grad.detach().float().pow(2).sum().item())
                    for parameter in self.policy.transformer.parameters()
                    if parameter.grad is not None
                )
                grad_norm = math.sqrt(norm_sq)
            self.policy.optimizer.step()
            valid_ratios = torch.cat(
                (
                    team_ratio.reshape(-1),
                    renew_ratio[renew_mask > 0],
                    skill_ratio[skill_mask > 0],
                )
            )
            train_info["h_value_loss"] += float(value_loss.detach().item())
            train_info["h_policy_loss"] += float(policy_loss.detach().item())
            train_info["h_dist_entropy"] += float(entropy.detach().item())
            train_info["h_actor_grad_norm"] += float(
                grad_norm.detach().item() if torch.is_tensor(grad_norm) else grad_norm
            )
            train_info["h_critic_grad_norm"] += float(
                grad_norm.detach().item() if torch.is_tensor(grad_norm) else grad_norm
            )
            train_info["h_ratio"] += float(valid_ratios.mean().detach().item())
            train_info["r43_renew_value_loss"] += float(
                renewal_value_loss.detach().item()
            )
            train_info["r43_skill_value_loss"] += float(
                skill_value_loss.detach().item()
            )
        for name in train_info:
            train_info[name] /= float(self.ppo_epoch)
        return train_info

    trainer.train = MethodType(train, trainer)


def _enumeration_parity(runner: Any) -> dict[str, Any]:
    policy = runner.h_policy
    transformer = policy.transformer
    batch_size = 2
    cent = np.linspace(
        -1.0,
        1.0,
        batch_size * runner.num_agents * policy.share_obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.share_obs_dim)
    obs = np.linspace(
        1.0,
        -1.0,
        batch_size * runner.num_agents * policy.obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.obs_dim)
    incumbents = np.asarray([[0, 1], [2, 3]], dtype=np.int64)
    ages = np.asarray([[50, 100], [150, 25]], dtype=np.float32)
    active = np.ones_like(ages, dtype=np.float32)
    rng = _capture_torch_rng()
    was_training = transformer.training
    transformer.eval()
    maximum_logp_error = 0.0
    maximum_probability_error = 0.0
    maximum_sum_error = 0.0
    with torch.no_grad():
        for row in range(batch_size):
            source_probabilities = []
            factor_probabilities = []
            for team in range(2):
                for first in range(policy.act_dim):
                    for second in range(policy.act_dim):
                        actions = np.asarray([[[team], [first], [second]]], dtype=np.int64)
                        renew = np.asarray(
                            [[first != incumbents[row, 0], second != incumbents[row, 1]]],
                            dtype=np.int64,
                        )
                        evaluated = evaluate_r43_factors(
                            policy,
                            cent[row * runner.num_agents : (row + 1) * runner.num_agents],
                            obs[row * runner.num_agents : (row + 1) * runner.num_agents],
                            actions,
                            incumbents[row : row + 1],
                            ages[row : row + 1],
                            active[row : row + 1],
                            renew,
                            np.ones((1, runner.num_agents), dtype=np.float32),
                            renew.astype(np.float32),
                        )
                        source_logp = (
                            evaluated["team_logp"]
                            + evaluated["source_selected_logp"].sum(dim=1)
                        )
                        factor_logp = evaluated["combined_logp"].sum(dim=1)
                        maximum_logp_error = max(
                            maximum_logp_error,
                            float((source_logp - factor_logp).abs().item()),
                        )
                        source_probabilities.append(float(source_logp.exp().item()))
                        factor_probabilities.append(float(factor_logp.exp().item()))
            source_array = np.asarray(source_probabilities)
            factor_array = np.asarray(factor_probabilities)
            maximum_probability_error = max(
                maximum_probability_error,
                float(np.max(np.abs(source_array - factor_array))),
            )
            maximum_sum_error = max(
                maximum_sum_error,
                abs(float(factor_array.sum()) - 1.0),
            )
    _restore_torch_rng(rng)
    if was_training:
        transformer.train()
    return {
        "enumerated_joint_actions_per_context": 32,
        "contexts": batch_size,
        "maximum_logp_error": maximum_logp_error,
        "maximum_probability_error": maximum_probability_error,
        "maximum_probability_sum_error": maximum_sum_error,
        "rng_restored": True,
    }


def _direct_gradient_preflight(runner: Any) -> dict[str, float]:
    policy = runner.h_policy
    transformer = policy.transformer
    batch_size = 4
    cent = np.linspace(
        -0.7,
        0.9,
        batch_size * runner.num_agents * policy.share_obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.share_obs_dim)
    obs = np.linspace(
        0.8,
        -0.6,
        batch_size * runner.num_agents * policy.obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.obs_dim)
    incumbents = np.asarray([[0, 1], [1, 2], [2, 3], [3, 0]], dtype=np.int64)
    ages = np.asarray([[50, 100], [100, 50], [150, 75], [25, 200]], dtype=np.float32)
    active = np.ones_like(ages, dtype=np.float32)
    rng = _capture_torch_rng()
    sampled = sample_r43_actions(
        policy,
        cent,
        obs,
        incumbents,
        ages,
        active,
        structural=False,
        deterministic=False,
    )
    policy.optimizer.zero_grad(set_to_none=True)
    loss = (
        -sampled["renew_logp"].mean()
        -sampled["skill_logp"].sum() / sampled["skill_valid"].sum().clamp_min(1.0)
        + sampled["renew_value"].pow(2).mean()
        + sampled["skill_value"].pow(2).mean()
    )
    loss.backward()

    def grad_norm(module: nn.Module) -> float:
        return math.sqrt(
            sum(
                float(parameter.grad.detach().float().pow(2).sum().item())
                for parameter in module.parameters()
                if parameter.grad is not None
            )
        )

    result = {
        "renewal_actor_gradient_norm": grad_norm(transformer.r43_renewal_actor),
        "renewal_critic_gradient_norm": grad_norm(transformer.r43_renewal_critic),
        "skill_event_critic_gradient_norm": grad_norm(
            transformer.r43_skill_event_critic
        ),
        "source_decoder_gradient_norm": grad_norm(transformer.decoder),
    }
    policy.optimizer.zero_grad(set_to_none=True)
    _restore_torch_rng(rng)
    return result


def install_native_renewal(runner: Any, mode: str) -> dict[str, Any]:
    """Install R43 modules/runtime and return focused zero-init evidence."""

    if mode not in R43_MODES:
        raise ValueError(f"unsupported R43 mode: {mode}")
    policy = runner.h_policy
    transformer = policy.transformer
    if policy.action_type != "Discrete" or runner.num_agents != 2:
        raise RuntimeError("R43 first gate requires N=2 discrete source HMASD")
    if hasattr(transformer, "r43_renewal_actor"):
        raise RuntimeError("R43 is already installed")
    n_embd = int(transformer.encoder.n_embd)
    input_dim = (
        2 * n_embd
        + policy.act_dim
        + runner.num_agents * policy.act_dim
        + 4 * runner.num_agents
    )
    construction_rng = _capture_torch_rng()
    renewal_actor = ContextHead(input_dim, 2).to(policy.device)
    renewal_critic = ContextHead(input_dim, 1).to(policy.device)
    skill_event_critic = ContextHead(input_dim, 1).to(policy.device)
    _restore_torch_rng(construction_rng)
    transformer.add_module("r43_renewal_actor", renewal_actor)
    transformer.add_module("r43_renewal_critic", renewal_critic)
    transformer.add_module("r43_skill_event_critic", skill_event_critic)
    parity = _enumeration_parity(runner)
    gradients = _direct_gradient_preflight(runner)
    for field in (
        "maximum_logp_error",
        "maximum_probability_error",
        "maximum_probability_sum_error",
    ):
        if not math.isfinite(float(parity[field])) or float(parity[field]) > 1e-6:
            raise RuntimeError(f"R43 zero-init probability parity failed: {parity}")
    if any(not math.isfinite(value) or value <= 0.0 for value in gradients.values()):
        raise RuntimeError(f"R43 direct-gradient preflight failed: {gradients}")
    new_parameters = (
        list(renewal_actor.parameters())
        + list(renewal_critic.parameters())
        + list(skill_event_critic.parameters())
    )
    policy.optimizer.add_param_group({"params": new_parameters})
    if mode == R43_FIXED:
        for module in (renewal_actor, renewal_critic, skill_event_critic):
            module.requires_grad_(False)
    _wrap_runtime_clock(runner, mode, policy.act_dim)
    if mode == R43_FIXED:
        _patch_fixed_runner(runner)
    else:
        _patch_buffer(runner.h_buffer, runner.num_agents)
        _patch_treatment_runner(runner, policy.act_dim)
        _patch_treatment_trainer(runner.h_trainer, runner.h_buffer)
    return {
        "mode": mode,
        "controller_clock": "source_global_k50_reset_censored",
        "context_input_dim": input_dim,
        "module_parameter_counts": {
            "renewal_actor": sum(p.numel() for p in renewal_actor.parameters()),
            "renewal_critic": sum(p.numel() for p in renewal_critic.parameters()),
            "skill_event_critic": sum(
                p.numel() for p in skill_event_critic.parameters()
            ),
        },
        "zero_init_probability": parity,
        "direct_gradients": gradients,
        "new_modules_frozen": mode == R43_FIXED,
        "task_specific_inputs": False,
        "intrinsic_reward_changed": False,
    }


def module_state_snapshot(runner: Any) -> dict[str, dict[str, torch.Tensor]]:
    transformer = runner.h_policy.transformer
    return {
        name: {
            key: value.detach().cpu().clone()
            for key, value in getattr(transformer, name).state_dict().items()
        }
        for name in (
            "r43_renewal_actor",
            "r43_renewal_critic",
            "r43_skill_event_critic",
        )
    }


def module_parameter_drift(
    runner: Any, initial: dict[str, dict[str, torch.Tensor]]
) -> dict[str, dict[str, float]]:
    transformer = runner.h_policy.transformer
    result: dict[str, dict[str, float]] = {}
    for module_name, before_state in initial.items():
        after_state = getattr(transformer, module_name).state_dict()
        delta_sq = 0.0
        initial_sq = 0.0
        maximum = 0.0
        for name, before in before_state.items():
            after = after_state[name].detach().cpu()
            delta = after - before
            delta_sq += float(delta.float().pow(2).sum().item())
            initial_sq += float(before.float().pow(2).sum().item())
            maximum = max(maximum, float(delta.abs().max().item()))
        absolute = math.sqrt(delta_sq)
        result[module_name] = {
            "absolute_l2": absolute,
            "relative_l2": absolute / (math.sqrt(initial_sq) + 1e-12),
            "max_abs": maximum,
        }
    return result


def summarize_renewal_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    events = int(ledger["events"])
    counts = np.asarray(ledger["renew_skill_counts"], dtype=np.float64)
    total = float(counts.sum())
    if total:
        probabilities = counts[counts > 0] / total
        entropy = float(-(probabilities * np.log(probabilities)).sum()) / math.log(
            len(counts)
        )
    else:
        entropy = 0.0
    return {
        **ledger,
        "agent_keep_rate": [
            count / events if events else 0.0 for count in ledger["agent_keep"]
        ],
        "agent_renew_rate": [
            count / events if events else 0.0 for count in ledger["agent_renew"]
        ],
        "discordant_rate": ledger["discordant"] / events if events else 0.0,
        "full_sync_renew_rate": (
            ledger["full_sync_renew"] / events if events else 0.0
        ),
        "renew_skill_entropy_normalized": entropy,
    }
