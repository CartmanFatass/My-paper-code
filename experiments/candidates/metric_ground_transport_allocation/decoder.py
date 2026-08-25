"""Batched fixed-length legal autoregressive decoder."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .config import LOGIT_CLIP, UNIFORM_MIXTURE


@dataclass
class DecodeResult:
    actions: torch.Tensor
    residual: torch.Tensor
    log_probability: torch.Tensor
    mean_entropy: torch.Tensor
    probabilities: torch.Tensor
    masks: torch.Tensor
    expanded_logits: torch.Tensor
    idle_logits: torch.Tensor


def decode(
    mapped_scores: torch.Tensor,
    idle_scores: torch.Tensor,
    roles: torch.Tensor,
    demand_values: torch.Tensor,
    priority_ranks: torch.Tensor,
    action_uniforms: torch.Tensor,
) -> DecodeResult:
    """Decode B decisions; ranks are attached to rows and uniforms to ranks."""
    batch, n = roles.shape
    device = mapped_scores.device
    roles = roles.to(dtype=torch.long)
    demand_values = demand_values.to(dtype=torch.long)
    priority_ranks = priority_ranks.to(dtype=torch.long)
    row_index = torch.arange(batch, device=device)
    expanded = mapped_scores.reshape(batch, 2, 4)[row_index[:, None], roles]
    idle = idle_scores[row_index[:, None], roles]
    expanded = expanded.clamp(-LOGIT_CLIP, LOGIT_CLIP)
    idle = idle.clamp(-LOGIT_CLIP, LOGIT_CLIP)
    residual = demand_values.clone()
    actions = torch.full((batch, n), 4, dtype=torch.long, device=device)
    probs_out = torch.zeros((batch, n, 5), dtype=torch.float64, device=device)
    masks_out = torch.zeros((batch, n, 5), dtype=torch.bool, device=device)
    logp = torch.zeros(batch, dtype=torch.float64, device=device)
    entropy = torch.zeros(batch, dtype=torch.float64, device=device)
    row_for_rank = torch.argsort(priority_ranks, dim=1)
    for rank in range(n):
        row = row_for_rank[:, rank]
        logits = torch.cat((expanded[row_index, row], idle[row_index, row, None]), dim=1)
        legal = torch.cat((residual > 0, torch.ones((batch, 1), dtype=torch.bool, device=device)), dim=1)
        masked = logits.masked_fill(~legal, -torch.inf)
        soft = torch.softmax(masked, dim=1)
        count = legal.sum(dim=1, keepdim=True)
        probs = 0.95 * soft + UNIFORM_MIXTURE * legal.to(torch.float64) / count
        u = action_uniforms[:, rank]
        chosen = torch.searchsorted(torch.cumsum(probs, dim=1).contiguous(), u[:, None], right=False).squeeze(1)
        chosen = torch.minimum(chosen, torch.full_like(chosen, 4))
        actions[row_index, row] = chosen
        probs_out[:, rank] = probs
        masks_out[:, rank] = legal
        picked = probs[row_index, chosen]
        logp = logp + torch.log(picked)
        safe_probs = torch.where(legal, probs, torch.ones_like(probs))
        entropy = entropy - torch.sum(torch.where(legal, probs * torch.log(safe_probs), torch.zeros_like(probs)), dim=1)
        real = chosen < 4
        if torch.any(real):
            residual[real, chosen[real]] -= 1
    return DecodeResult(actions, residual, logp, entropy / n, probs_out, masks_out, expanded, idle)
