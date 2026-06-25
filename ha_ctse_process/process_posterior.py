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
    """Variational estimator for process MI: log q(z|S,g) - log p(z|g)."""

    def __init__(
        self,
        embedding_dim: int,
        n_skills: int,
        num_team_codes: int,
        hidden_dim: int,
        team_embed_dim: int | None = None,
        condition_on_team: bool = True,
    ):
        super().__init__()
        self.embedding_dim = int(embedding_dim)
        self.n_skills = int(n_skills)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.condition_on_team = bool(condition_on_team)
        self.team_embed_dim = int(team_embed_dim or min(hidden_dim, max(8, self.num_team_codes * 4)))

        if self.condition_on_team:
            self.team_embedding = nn.Embedding(self.num_team_codes, self.team_embed_dim)
            posterior_input_dim = self.embedding_dim + self.team_embed_dim
            self.prior_head = mlp(self.team_embed_dim, hidden_dim, self.n_skills)
        else:
            self.team_embedding = None
            posterior_input_dim = self.embedding_dim
            self.global_prior_logits = nn.Parameter(torch.zeros(self.n_skills))

        self.posterior_head = mlp(posterior_input_dim, hidden_dim, self.n_skills)

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
