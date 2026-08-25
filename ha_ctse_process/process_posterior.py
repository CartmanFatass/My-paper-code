"""Segment-level process posterior for standalone HA-CTSE.

This is not the legacy HMASD single-step discriminator.  It estimates a
process-level posterior q(z | S, g) and a coordination-conditioned prior
p(z | g), where S is a completed skill-lifetime segment.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


def mlp(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(input_dim),
        nn.Linear(input_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, output_dim),
    )


class SegmentSkillPosterior(nn.Module):
    """Variational estimator for process MI: log q(z|S,g) - log p(z|g).

    It also owns lightweight shortcut heads for residual semantic pressure.
    Those heads estimate how well skill labels can be recovered from duration,
    segment length, reward sum, or start context alone.  A residual process
    reward can then use only the information in the segment embedding that
    exceeds those shortcuts.
    """

    def __init__(
        self,
        embedding_dim: int,
        n_skills: int,
        num_team_codes: int,
        hidden_dim: int,
        team_embed_dim: int | None = None,
        condition_on_team: bool = True,
        num_duration_bins: int = 1,
        obs_dim: int = 0,
        num_agents: int = 1,
        num_phase_bins: int = 8,
        use_context_shortcut: bool = True,
    ):
        super().__init__()
        self.embedding_dim = int(embedding_dim)
        self.n_skills = int(n_skills)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.condition_on_team = bool(condition_on_team)
        self.team_embed_dim = int(team_embed_dim or min(hidden_dim, max(8, self.num_team_codes * 4)))
        self.num_duration_bins = int(max(num_duration_bins, 1))
        self.obs_dim = int(max(obs_dim, 0))
        self.num_agents = int(max(num_agents, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.use_context_shortcut = bool(use_context_shortcut and self.obs_dim > 0)

        if self.condition_on_team:
            self.team_embedding = nn.Embedding(self.num_team_codes, self.team_embed_dim)
            posterior_input_dim = self.embedding_dim + self.team_embed_dim
            self.prior_head = mlp(self.team_embed_dim, hidden_dim, self.n_skills)
        else:
            self.team_embedding = None
            posterior_input_dim = self.embedding_dim
            self.global_prior_logits = nn.Parameter(torch.zeros(self.n_skills))

        self.posterior_head = mlp(posterior_input_dim, hidden_dim, self.n_skills)
        self.duration_embedding = nn.Embedding(self.num_duration_bins, self.team_embed_dim)
        self.duration_shortcut_head = mlp(self.team_embed_dim, hidden_dim, self.n_skills)
        self.length_shortcut_head = mlp(1, hidden_dim, self.n_skills)
        self.reward_sum_shortcut_head = mlp(1, hidden_dim, self.n_skills)
        if self.use_context_shortcut:
            self.context_team_embedding = None if self.condition_on_team else nn.Embedding(
                self.num_team_codes,
                self.team_embed_dim,
            )
            self.agent_embedding = nn.Embedding(self.num_agents, self.team_embed_dim)
            self.phase_embedding = nn.Embedding(self.num_phase_bins, self.team_embed_dim)
            context_input_dim = self.obs_dim + 3 * self.team_embed_dim
            self.context_shortcut_head = mlp(context_input_dim, hidden_dim, self.n_skills)
        else:
            self.context_team_embedding = None
            self.agent_embedding = None
            self.phase_embedding = None
            self.context_shortcut_head = None

    def forward(self, segment_embedding: torch.Tensor, team_codes: torch.Tensor):
        team_codes = team_codes.long().clamp(0, self.num_team_codes - 1)
        if self.condition_on_team:
            team_emb = self.team_embedding(team_codes)
            posterior_input = torch.cat([segment_embedding.float(), team_emb.float()], dim=-1)
            prior_logits = self.prior_head(team_emb)
        else:
            posterior_input = segment_embedding.float()
            prior_logits = self.global_prior_logits.unsqueeze(0).expand(segment_embedding.shape[0], -1)
        posterior_logits = self.posterior_head(posterior_input)
        return posterior_logits, prior_logits

    @staticmethod
    def log_prob_for_labels(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        labels = labels.long()
        return F.log_softmax(logits, dim=-1)[torch.arange(labels.shape[0], device=labels.device), labels]

    def losses(self, posterior_logits: torch.Tensor, prior_logits: torch.Tensor, labels: torch.Tensor):
        labels = labels.long()
        posterior_loss = F.cross_entropy(posterior_logits, labels)
        prior_loss = F.cross_entropy(prior_logits, labels)
        with torch.no_grad():
            log_q = self.log_prob_for_labels(posterior_logits, labels)
            log_p = self.log_prob_for_labels(prior_logits, labels)
            mi_estimate = log_q - log_p
            posterior_acc = (posterior_logits.argmax(dim=-1) == labels).float().mean()
        return {
            "posterior_loss": posterior_loss,
            "prior_loss": prior_loss,
            "log_q": log_q,
            "log_p": log_p,
            "mi_estimate": mi_estimate,
            "posterior_acc": posterior_acc,
        }

    @staticmethod
    def scalar_feature(values: torch.Tensor) -> torch.Tensor:
        values = values.float().reshape(-1, 1)
        if values.numel() <= 1:
            return torch.zeros_like(values)
        mean = values.mean()
        std = values.std(unbiased=False).clamp_min(1e-6)
        return ((values - mean) / std).clamp(-5.0, 5.0)

    def shortcut_logits(
        self,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
        start_obs: torch.Tensor | None = None,
        team_codes: torch.Tensor | None = None,
        agent_ids: torch.Tensor | None = None,
        phase_bins: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        durations = durations.long().clamp(0, self.num_duration_bins - 1)
        duration_logits = self.duration_shortcut_head(self.duration_embedding(durations))
        length_logits = self.length_shortcut_head(self.scalar_feature(lengths))
        reward_sum_logits = self.reward_sum_shortcut_head(self.scalar_feature(reward_sums))
        result = {
            "duration": duration_logits,
            "length": length_logits,
            "reward_sum": reward_sum_logits,
        }
        if (
            self.use_context_shortcut
            and start_obs is not None
            and team_codes is not None
            and agent_ids is not None
            and phase_bins is not None
        ):
            result["context"] = self.context_shortcut_logits(start_obs, team_codes, agent_ids, phase_bins)
        return result

    def context_shortcut_logits(
        self,
        start_obs: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
    ) -> torch.Tensor:
        if not self.use_context_shortcut or self.context_shortcut_head is None:
            raise RuntimeError("Context shortcut is disabled for this SegmentSkillPosterior")
        team_codes = team_codes.long().clamp(0, self.num_team_codes - 1)
        agent_ids = agent_ids.long().clamp(0, self.num_agents - 1)
        phase_bins = phase_bins.long().clamp(0, self.num_phase_bins - 1)
        if self.condition_on_team:
            team_emb = self.team_embedding(team_codes)
        else:
            team_emb = self.context_team_embedding(team_codes)
        context_input = torch.cat(
            [
                start_obs.float(),
                team_emb.float(),
                self.agent_embedding(agent_ids).float(),
                self.phase_embedding(phase_bins).float(),
            ],
            dim=-1,
        )
        return self.context_shortcut_head(context_input)

    def shortcut_losses(
        self,
        labels: torch.Tensor,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
        start_obs: torch.Tensor | None = None,
        team_codes: torch.Tensor | None = None,
        agent_ids: torch.Tensor | None = None,
        phase_bins: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        labels = labels.long()
        logits = self.shortcut_logits(
            durations,
            lengths,
            reward_sums,
            start_obs=start_obs,
            team_codes=team_codes,
            agent_ids=agent_ids,
            phase_bins=phase_bins,
        )
        losses = {name: F.cross_entropy(head_logits, labels) for name, head_logits in logits.items()}
        with torch.no_grad():
            log_qs = {
                name: self.log_prob_for_labels(head_logits, labels)
                for name, head_logits in logits.items()
            }
            accs = {
                name: (head_logits.argmax(dim=-1) == labels).float().mean()
                for name, head_logits in logits.items()
            }
            shortcut_names = list(log_qs)
            stacked = torch.stack([log_qs[name] for name in shortcut_names], dim=0)
            max_log_q, max_indices = torch.max(stacked, dim=0)
            acc_stack = torch.stack(
                [
                    (logits[name].argmax(dim=-1) == labels).float()
                    for name in shortcut_names
                ],
                dim=0,
            )
            max_shortcut_acc = (
                torch.gather(
                    acc_stack,
                    0,
                    max_indices.unsqueeze(0),
                )
                .squeeze(0)
                .mean()
            )
            zeros = torch.zeros((), device=labels.device)
            zero_vec = torch.zeros_like(max_log_q)
        return {
            "shortcut_loss": (losses["duration"] + losses["length"] + losses["reward_sum"]) / 3.0,
            "duration_loss": losses["duration"],
            "length_loss": losses["length"],
            "reward_sum_loss": losses["reward_sum"],
            "context_loss": losses.get("context", zeros),
            "log_q_duration": log_qs["duration"],
            "log_q_length": log_qs["length"],
            "log_q_reward_sum": log_qs["reward_sum"],
            "log_q_context": log_qs.get("context", zero_vec),
            "max_log_q": max_log_q,
            "duration_acc": accs["duration"],
            "length_acc": accs["length"],
            "reward_sum_acc": accs["reward_sum"],
            "context_acc": accs.get("context", zeros),
            "max_shortcut_acc": max_shortcut_acc,
        }


class FixedWindowEffectPosterior(nn.Module):
    """R31 posterior pair for task-agnostic fixed-window effects.

    The full head estimates ``q(z_i | E_i, C_i)`` and the context head estimates
    the natural-usage null ``q(z_i | C_i)``.  Its interface accepts only the
    prebuilt effect and context vectors; actions, rewards, agent identity, age,
    duration, phase, and OPT features are intentionally absent.  Inputs are
    detached here as a second boundary against posterior gradients entering the
    policy or representation paths.
    """

    def __init__(
        self,
        effect_dim: int,
        context_dim: int,
        n_skills: int,
        hidden_dim: int,
    ):
        super().__init__()
        self.effect_dim = int(effect_dim)
        self.context_dim = int(context_dim)
        self.n_skills = int(n_skills)
        if self.effect_dim <= 0 or self.context_dim <= 0 or self.n_skills <= 1:
            raise ValueError(
                "FixedWindowEffectPosterior requires positive effect/context "
                "dimensions and at least two skills"
            )
        self.full_head = mlp(
            self.effect_dim + self.context_dim,
            int(hidden_dim),
            self.n_skills,
        )
        self.context_head = mlp(
            self.context_dim,
            int(hidden_dim),
            self.n_skills,
        )

    def full_logits(
        self,
        effect: torch.Tensor,
        context: torch.Tensor,
    ) -> torch.Tensor:
        features = torch.cat(
            [effect.detach().float(), context.detach().float()],
            dim=-1,
        )
        return self.full_head(features)

    def context_logits(self, context: torch.Tensor) -> torch.Tensor:
        return self.context_head(context.detach().float())

    def forward(
        self,
        effect: torch.Tensor,
        context: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        return self.full_logits(effect, context), self.context_logits(context)

    @staticmethod
    def log_prob_for_labels(
        logits: torch.Tensor,
        labels: torch.Tensor,
    ) -> torch.Tensor:
        labels = labels.long()
        row_indices = torch.arange(labels.shape[0], device=labels.device)
        return F.log_softmax(logits, dim=-1)[row_indices, labels]

    def losses(
        self,
        full_logits: torch.Tensor,
        context_logits: torch.Tensor,
        labels: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        labels = labels.long()
        full_loss = F.cross_entropy(full_logits, labels)
        context_loss = F.cross_entropy(context_logits, labels)
        with torch.no_grad():
            log_q_full = self.log_prob_for_labels(full_logits, labels)
            log_q_context = self.log_prob_for_labels(context_logits, labels)
            effect_information = log_q_full - log_q_context
            full_acc = (full_logits.argmax(dim=-1) == labels).float().mean()
            context_acc = (context_logits.argmax(dim=-1) == labels).float().mean()
        return {
            "loss": full_loss + context_loss,
            "full_loss": full_loss,
            "context_loss": context_loss,
            "log_q_full": log_q_full,
            "log_q_context": log_q_context,
            "effect_information": effect_information,
            "full_acc": full_acc,
            "context_acc": context_acc,
        }


class TransitionSkillDiscriminator(nn.Module):
    """Dense semantic pressure q(z | o_t, a_t, delta_o_t, r_t, g).

    The segment posterior receives one sample per completed skill lifetime.  In
    long-horizon UAV service tasks that can be too sparse to reliably shape
    skill semantics.  This discriminator deliberately uses every primitive
    transition inside completed segments, mirroring the sample-density advantage
    of HMASD's discriminator while staying in the standalone process algorithm.
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        n_skills: int,
        num_team_codes: int,
        hidden_dim: int,
        team_embed_dim: int | None = None,
        condition_on_team: bool = True,
        num_agents: int = 1,
        num_phase_bins: int = 8,
        use_context_shortcut: bool = True,
    ):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.action_dim = int(action_dim)
        self.n_skills = int(n_skills)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.condition_on_team = bool(condition_on_team)
        self.team_embed_dim = int(team_embed_dim or min(hidden_dim, max(8, self.num_team_codes * 4)))
        self.num_agents = int(max(num_agents, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.use_context_shortcut = bool(use_context_shortcut)

        transition_dim = self.obs_dim + self.action_dim + self.obs_dim + 1
        if self.condition_on_team:
            self.team_embedding = nn.Embedding(self.num_team_codes, self.team_embed_dim)
            posterior_input_dim = transition_dim + self.team_embed_dim
            self.prior_head = mlp(self.team_embed_dim, hidden_dim, self.n_skills)
        else:
            self.team_embedding = None
            posterior_input_dim = transition_dim
            self.global_prior_logits = nn.Parameter(torch.zeros(self.n_skills))

        self.posterior_head = mlp(posterior_input_dim, hidden_dim, self.n_skills)
        if self.use_context_shortcut:
            self.context_team_embedding = None if self.condition_on_team else nn.Embedding(
                self.num_team_codes,
                self.team_embed_dim,
            )
            self.agent_embedding = nn.Embedding(self.num_agents, self.team_embed_dim)
            self.phase_embedding = nn.Embedding(self.num_phase_bins, self.team_embed_dim)
            context_input_dim = self.obs_dim + 3 * self.team_embed_dim
            self.context_shortcut_head = mlp(context_input_dim, hidden_dim, self.n_skills)
        else:
            self.context_team_embedding = None
            self.agent_embedding = None
            self.phase_embedding = None
            self.context_shortcut_head = None

    @staticmethod
    def _scalar_feature(values: torch.Tensor) -> torch.Tensor:
        values = values.float().reshape(-1, 1)
        if values.numel() <= 1:
            return torch.zeros_like(values)
        mean = values.mean()
        std = values.std(unbiased=False).clamp_min(1e-6)
        return ((values - mean) / std).clamp(-5.0, 5.0)

    @staticmethod
    def log_prob_for_labels(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        labels = labels.long()
        return F.log_softmax(logits, dim=-1)[torch.arange(labels.shape[0], device=labels.device), labels]

    def forward(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        delta_obs: torch.Tensor,
        rewards: torch.Tensor,
        team_codes: torch.Tensor,
    ):
        team_codes = team_codes.long().clamp(0, self.num_team_codes - 1)
        reward_feat = self._scalar_feature(rewards).to(device=obs.device, dtype=obs.dtype)
        transition_feat = torch.cat(
            [
                obs.float(),
                actions.float(),
                delta_obs.float(),
                reward_feat.float(),
            ],
            dim=-1,
        )
        if self.condition_on_team:
            team_emb = self.team_embedding(team_codes)
            posterior_input = torch.cat([transition_feat, team_emb.float()], dim=-1)
            prior_logits = self.prior_head(team_emb)
        else:
            posterior_input = transition_feat
            prior_logits = self.global_prior_logits.unsqueeze(0).expand(obs.shape[0], -1)
        posterior_logits = self.posterior_head(posterior_input)
        return posterior_logits, prior_logits

    def context_shortcut_logits(
        self,
        start_obs: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
    ) -> torch.Tensor:
        if not self.use_context_shortcut or self.context_shortcut_head is None:
            raise RuntimeError("Context shortcut is disabled for this TransitionSkillDiscriminator")
        team_codes = team_codes.long().clamp(0, self.num_team_codes - 1)
        agent_ids = agent_ids.long().clamp(0, self.num_agents - 1)
        phase_bins = phase_bins.long().clamp(0, self.num_phase_bins - 1)
        if self.condition_on_team:
            team_emb = self.team_embedding(team_codes)
        else:
            team_emb = self.context_team_embedding(team_codes)
        context_input = torch.cat(
            [
                start_obs.float(),
                team_emb.float(),
                self.agent_embedding(agent_ids).float(),
                self.phase_embedding(phase_bins).float(),
            ],
            dim=-1,
        )
        return self.context_shortcut_head(context_input)

    def losses(self, posterior_logits: torch.Tensor, prior_logits: torch.Tensor, labels: torch.Tensor):
        labels = labels.long()
        posterior_loss = F.cross_entropy(posterior_logits, labels)
        prior_loss = F.cross_entropy(prior_logits, labels)
        with torch.no_grad():
            log_q = self.log_prob_for_labels(posterior_logits, labels)
            log_p = self.log_prob_for_labels(prior_logits, labels)
            mi_estimate = log_q - log_p
            posterior_acc = (posterior_logits.argmax(dim=-1) == labels).float().mean()
        return {
            "posterior_loss": posterior_loss,
            "prior_loss": prior_loss,
            "log_q": log_q,
            "log_p": log_p,
            "mi_estimate": mi_estimate,
            "posterior_acc": posterior_acc,
        }
