"""Fixture-only controller/compositor conformance for SCDMP TBCC r02."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import torch

from .contracts import ACTION_COUNT, ContractError


LEXICOGRAPHIC_ACTIONS: Final[tuple[tuple[int, int, int, int, int], ...]] = tuple(
    (a, *r)
    for a in (1, 2)
    for r in (
        (0, 0, 0, 0),
        (1, -1, 0, 0),
        (-1, 1, 0, 0),
        (0, 0, 1, -1),
        (0, 0, -1, 1),
        (1, 0, -1, 0),
        (-1, 0, 1, 0),
        (0, 1, 0, -1),
        (0, -1, 0, 1),
    )
)


def _action_tensor(*, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
    return torch.tensor(LEXICOGRAPHIC_ACTIONS, dtype=dtype, device=device)


def graph_slack_scores(observation: torch.Tensor, q: torch.Tensor, k: torch.Tensor) -> torch.Tensor:
    """Compute all 18 exact J_q scores from scaled public TEST observations."""

    if observation.dtype != torch.float32 or observation.ndim != 2 or observation.shape[1] != 18:
        raise ContractError("observation must be float32 [batch,18]")
    batch = observation.shape[0]
    if q.dtype != torch.float32 or q.shape != (batch,) or torch.any((q != 0.0) & (q != 1.0)):
        raise ContractError("physical graph compositor q must be exactly 0 or 1")
    if k.shape != (batch,) or torch.any(k <= 0):
        raise ContractError("one positive announced hold is required per row")
    if not torch.isfinite(observation).all():
        raise ContractError("observation must be finite")

    actions = _action_tensor(dtype=torch.float32, device=observation.device)
    a = actions[:, 0].view(1, ACTION_COUNT)
    r = actions[:, 1:].view(1, ACTION_COUNT, 4)
    x = observation[:, 0] * 24.5
    y = observation[:, 2] * 0.40
    phi = observation[:, 4] * 0.35
    z = observation[:, 6:10] * 0.25
    n = observation[:, 17] * 364.0
    y_ref = torch.where(
        x < 8.0,
        torch.zeros_like(x),
        torch.where(
            x < 16.0,
            0.18 * torch.sin(torch.pi * (x - 8.0) / 8.0),
            torch.zeros_like(x),
        ),
    )
    error = y - y_ref
    b0 = torch.tensor((0.0, 0.0, 1.0, -1.0), device=observation.device)
    b1 = torch.tensor((1.0, -1.0, 0.0, 0.0), device=observation.device)
    b = torch.where(q[:, None] == 1.0, b1, b0)
    tau = (
        0.38
        + 0.12 * a[:, :, None]
        + 0.16 * a[:, :, None] * torch.clamp_min(b[:, None, :], 0.0)
        - 0.10 * r
        + 0.04 * torch.abs(phi)[:, None, None]
        + 0.03 * torch.abs(error)[:, None, None]
    )
    tau_bar = tau.mean(dim=2, keepdim=True)
    mu = 0.5 * torch.sum(b[:, None, :] * (tau - tau_bar), dim=2)
    h_plan = torch.minimum(k.to(torch.float32), 364.0 - n).clamp_min(0.0)
    decay = torch.pow(torch.tensor(0.84, dtype=torch.float32), h_plan)[:, None, None]
    exposure = (
        decay * z[:, None, :]
        + ((1.0 - decay) / (1.0 - 0.84)) * torch.clamp_min(tau - 0.88, 0.0)
    )
    clearance = 0.25 - exposure.max(dim=2).values
    u_req = torch.clamp((24.5 - x) / (0.075 * torch.maximum(torch.ones_like(n), 364.0 - n)), 0.0, 2.0)
    return (
        0.30 * u_req[:, None] * (a - 1.0)
        + 0.10 * torch.clamp(clearance / 0.25, 0.0, 1.0)
        + torch.minimum(clearance / 0.10, torch.zeros_like(clearance))
        - 0.20 * torch.abs(mu)
    )


def treat_logits(foundation_logits: torch.Tensor, alpha: torch.Tensor, scores: torch.Tensor) -> torch.Tensor:
    if foundation_logits.shape != scores.shape or foundation_logits.ndim != 2 or foundation_logits.shape[1] != ACTION_COUNT:
        raise ContractError("foundation and J tensors must both have shape [batch,18]")
    if alpha.shape != foundation_logits.shape[:1] or torch.any(alpha < 0):
        raise ContractError("alpha must be one nonnegative value per row")
    return foundation_logits + alpha[:, None] * scores


def free_logits(treat: torch.Tensor, residual: torch.Tensor) -> torch.Tensor:
    if treat.shape != residual.shape:
        raise ContractError("FREE residual must match TREAT logits")
    return treat + residual


def strict_containment_witness(scores: torch.Tensor) -> torch.Tensor:
    """Return a deterministic vector outside span{1,J}, or fail if J is constant."""

    if scores.dtype != torch.float32 or scores.shape != (ACTION_COUNT,) or not torch.isfinite(scores).all():
        raise ContractError("strict-containment fixture requires one finite float32 J vector")
    ones = torch.ones_like(scores)
    centered = scores - scores.mean()
    if torch.linalg.vector_norm(centered) == 0:
        raise ContractError("strict containment requires nonconstant J")
    for index in range(ACTION_COUNT):
        basis = torch.zeros_like(scores)
        basis[index] = 1.0
        residual = basis - basis.mean() * ones
        residual = residual - torch.dot(residual, centered) / torch.dot(centered, centered) * centered
        if torch.linalg.vector_norm(residual) > 1e-5:
            return residual
    raise ContractError("could not construct strict-containment witness")


@dataclass(frozen=True)
class ReversedCompositor:
    physical_q: torch.Tensor
    compositor_q: torch.Tensor


def reversed_compositor(physical_q: torch.Tensor) -> ReversedCompositor:
    if physical_q.dtype != torch.float32 or torch.any((physical_q != 0.0) & (physical_q != 1.0)):
        raise ContractError("REVERSED requires binary physical q")
    return ReversedCompositor(physical_q=physical_q.clone(), compositor_q=1.0 - physical_q)


def set_scores(observation: torch.Tensor, k: torch.Tensor) -> torch.Tensor:
    batch = observation.shape[0]
    zero = torch.zeros(batch, dtype=torch.float32, device=observation.device)
    one = torch.ones(batch, dtype=torch.float32, device=observation.device)
    return 0.5 * (graph_slack_scores(observation, zero, k) + graph_slack_scores(observation, one, k))


def set_compositor(raw_middle_events: tuple[str, str]) -> float:
    if sorted(raw_middle_events) != ["FORMATION-ROTATE", "HOOK-HANDOFF"]:
        raise ContractError("SET fixture requires the registered unordered middle-event multiset")
    return 0.5

