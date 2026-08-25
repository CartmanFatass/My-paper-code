"""Stopped-target RSCF loss and one-step projected-Adam integration.

Only factual-policy probabilities, all factual entropy terms and the terminal
critic retain gradients.  Native full-suffix targets are required to arrive as
detached tensors and are never exposed to actor or critic inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import torch
from torch import Tensor, nn

from .policy import RSCFActor, TerminalCritic


ENTROPY_COEFFICIENT = 0.01
CRITIC_COEFFICIENT = 0.5
GLOBAL_GRADIENT_NORM_CLIP = 0.5
ADAM_LEARNING_RATE = 3.0e-4
ADAM_BETAS = (0.9, 0.999)
ADAM_EPSILON = 1.0e-8
PHY_TRUST_BOUND = 0.15
EDGE_FLEX_BOUND = 1.50


@dataclass(frozen=True)
class EpisodeLossInputs:
    """One complete factual episode after all three Q vectors are available.

    ``selected_probabilities`` and ``selected_legal_mask`` have shape ``[3,6]``
    in public role order W, E, R.  ``q_targets`` has the same dense shape; only
    legal entries are read. ``all_slot_agent_entropy`` is ``[12,N]`` and
    ``critic_values`` is ``[12]``.  Episode tensors may have different ``N``
    across the 64-episode batch.
    """

    selected_probabilities: Tensor
    selected_factual_actions: Tensor
    selected_legal_mask: Tensor
    q_targets: Tensor
    factual_return: Tensor
    all_slot_agent_entropy: Tensor
    critic_values: Tensor
    selected_role_indices: Tensor


@dataclass(frozen=True)
class EpisodeLossAudit:
    baseline: Tensor
    stopped_advantage: Tensor
    score_loss: Tensor
    entropy_mean: Tensor
    critic_mse: Tensor
    complete_roles: bool
    q_target_requires_grad: bool
    factual_return_requires_grad: bool


@dataclass(frozen=True)
class BatchLossAudit:
    episode_count: int
    score_loss: Tensor
    entropy_mean: Tensor
    critic_mse: Tensor
    complete_episode_q_vectors: bool
    equal_episode_weighting: bool


@dataclass(frozen=True)
class StepAudit:
    preclip_global_gradient_norm: float
    clip_limit: float
    projection_bound: float
    beta_min: float
    beta_max: float
    optimizer_parameter_count: int
    backward_calls: int
    optimizer_steps: int
    projection_after_step: bool


def stopped_policy_weighted_baseline(
    factual_probabilities: Tensor, q_targets: Tensor, legal_mask: Tensor
) -> Tensor:
    """Return ``sum_a sg[pi(a)] sg[Q(a)]`` for all three roles."""

    if factual_probabilities.shape != (3, 6):
        raise ValueError("factual_probabilities must have shape [3,6]")
    if q_targets.shape != (3, 6) or legal_mask.shape != (3, 6):
        raise ValueError("q_targets and legal_mask must have shape [3,6]")
    if factual_probabilities.dtype is not torch.float32:
        raise TypeError("factual_probabilities must be float32")
    if q_targets.dtype is not torch.float32:
        raise TypeError("native q_targets must be float32")
    if legal_mask.dtype is not torch.bool:
        raise TypeError("legal_mask must be bool")
    if q_targets.requires_grad or q_targets.grad_fn is not None:
        raise ValueError("native q_targets must be detached before loss construction")
    if not bool(torch.isfinite(factual_probabilities).all().item()):
        raise ValueError("factual probabilities contain a nonfinite value")
    if not bool(torch.isfinite(q_targets[legal_mask]).all().item()):
        raise ValueError("a legal native Q target is nonfinite")
    illegal_probability = factual_probabilities.masked_select(~legal_mask)
    if illegal_probability.numel() and not bool((illegal_probability == 0).all().item()):
        raise ValueError("illegal action probability must be exactly zero")
    probability_mass = factual_probabilities.masked_fill(~legal_mask, 0.0).sum(dim=-1)
    if not bool(torch.allclose(
        probability_mass,
        torch.ones_like(probability_mass),
        rtol=0.0,
        atol=2.0e-6,
    )):
        raise ValueError("legal probabilities must sum to one")
    stopped_q = q_targets.detach().masked_fill(~legal_mask, 0.0)
    return (factual_probabilities.detach() * stopped_q).sum(dim=-1)


def rscf_episode_loss(
    inputs: EpisodeLossInputs,
) -> tuple[Tensor, EpisodeLossAudit]:
    """Construct the exact equal-role score plus entropy and critic nuisance loss."""

    _validate_episode_inputs(inputs)
    baseline = stopped_policy_weighted_baseline(
        inputs.selected_probabilities, inputs.q_targets, inputs.selected_legal_mask
    )
    advantage = (inputs.factual_return.detach() - baseline).detach()
    factual_actions = inputs.selected_factual_actions.to(torch.int64)
    chosen_legal = inputs.selected_legal_mask.gather(
        -1, factual_actions[:, None]
    ).squeeze(-1)
    if not bool(chosen_legal.all().item()):
        raise ValueError("selected factual action is not legal at an origin")
    selected_probability = inputs.selected_probabilities.gather(
        -1, factual_actions[:, None]
    ).squeeze(-1)
    score_loss = -(torch.log(selected_probability) * advantage).sum() / 3.0
    entropy_mean = inputs.all_slot_agent_entropy.mean()
    critic_target = inputs.factual_return.detach().expand_as(inputs.critic_values)
    critic_mse = torch.mean((inputs.critic_values - critic_target) ** 2)
    loss = score_loss - ENTROPY_COEFFICIENT * entropy_mean + CRITIC_COEFFICIENT * critic_mse
    audit = EpisodeLossAudit(
        baseline=baseline.detach(),
        stopped_advantage=advantage,
        score_loss=score_loss.detach(),
        entropy_mean=entropy_mean.detach(),
        critic_mse=critic_mse.detach(),
        complete_roles=True,
        q_target_requires_grad=inputs.q_targets.requires_grad,
        factual_return_requires_grad=inputs.factual_return.requires_grad,
    )
    return loss, audit


def rscf_full_batch_loss(
    episodes: Sequence[EpisodeLossInputs], *, required_episode_count: int = 64
) -> tuple[Tensor, BatchLossAudit, tuple[EpisodeLossAudit, ...]]:
    """Average complete episode losses equally, independent of roster size."""

    if len(episodes) != required_episode_count:
        raise ValueError(
            f"one update requires {required_episode_count} complete episodes, got {len(episodes)}"
        )
    losses: list[Tensor] = []
    audits: list[EpisodeLossAudit] = []
    for episode in episodes:
        loss, audit = rscf_episode_loss(episode)
        losses.append(loss)
        audits.append(audit)
    total = torch.stack(losses).mean()
    batch_audit = BatchLossAudit(
        episode_count=len(episodes),
        score_loss=torch.stack([audit.score_loss for audit in audits]).mean(),
        entropy_mean=torch.stack([audit.entropy_mean for audit in audits]).mean(),
        critic_mse=torch.stack([audit.critic_mse for audit in audits]).mean(),
        complete_episode_q_vectors=True,
        equal_episode_weighting=True,
    )
    return total, batch_audit, tuple(audits)


def make_projected_adam(actor: RSCFActor, critic: TerminalCritic) -> torch.optim.Adam:
    """Create the one joint optimizer with the frozen hyperparameters."""

    parameters = list(actor.parameters()) + list(critic.parameters())
    return torch.optim.Adam(
        parameters,
        lr=ADAM_LEARNING_RATE,
        betas=ADAM_BETAS,
        eps=ADAM_EPSILON,
        weight_decay=0.0,
    )


def project_residual_coefficients_(actor: RSCFActor, bound: float) -> None:
    """Project only the live 18 beta coefficients, preserving Adam moments."""

    if bound not in (PHY_TRUST_BOUND, EDGE_FLEX_BOUND):
        raise ValueError("projection bound must be exactly 0.15 or 1.50")
    with torch.no_grad():
        actor.beta.clamp_(min=-bound, max=bound)


def projected_adam_step(
    loss: Tensor,
    *,
    actor: RSCFActor,
    critic: TerminalCritic,
    optimizer: torch.optim.Adam,
    projection_bound: float,
) -> StepAudit:
    """Perform exactly one backward, one concatenated clip, one Adam step and projection."""

    if loss.ndim != 0 or loss.dtype is not torch.float32:
        raise ValueError("loss must be one float32 scalar")
    if not bool(torch.isfinite(loss.detach()).item()):
        raise ValueError("loss is nonfinite")
    parameters = list(actor.parameters()) + list(critic.parameters())
    parameter_ids = {id(parameter) for parameter in parameters}
    optimizer_parameters = [
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    if len({id(parameter) for parameter in optimizer_parameters}) != len(
        optimizer_parameters
    ):
        raise ValueError("optimizer contains duplicate parameters")
    if {id(parameter) for parameter in optimizer_parameters} != parameter_ids:
        raise ValueError("optimizer must contain exactly actor, critic and beta parameters")
    _validate_adam_hyperparameters(optimizer)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    for parameter in parameters:
        if parameter.grad is None:
            raise ValueError("every actor, critic and beta parameter must receive a gradient")
        if not bool(torch.isfinite(parameter.grad).all().item()):
            raise ValueError("a gradient is nonfinite")
    preclip_norm = nn.utils.clip_grad_norm_(
        parameters,
        max_norm=GLOBAL_GRADIENT_NORM_CLIP,
        norm_type=2.0,
        error_if_nonfinite=True,
    )
    optimizer.step()
    project_residual_coefficients_(actor, projection_bound)
    return StepAudit(
        preclip_global_gradient_norm=float(preclip_norm.detach().cpu().item()),
        clip_limit=GLOBAL_GRADIENT_NORM_CLIP,
        projection_bound=projection_bound,
        beta_min=float(actor.beta.detach().min().cpu().item()),
        beta_max=float(actor.beta.detach().max().cpu().item()),
        optimizer_parameter_count=sum(parameter.numel() for parameter in parameters),
        backward_calls=1,
        optimizer_steps=1,
        projection_after_step=True,
    )


def training_contract_audit() -> dict[str, object]:
    """Return deterministic, value-free loss and optimizer facts."""

    return {
        "selected_origins_per_episode": 3,
        "selected_role_order": (0, 1, 2),
        "role_score_weights": (1.0 / 3.0,) * 3,
        "baseline": "sum_a sg[pi(a)]*sg[Q(a)]",
        "advantage": "sg[J_base-baseline]",
        "branch_target_gradient": False,
        "branch_policy_log_probability": False,
        "entropy_scope": "all factual agents and all 12 slots",
        "entropy_coefficient": ENTROPY_COEFFICIENT,
        "critic_target": "terminal J_base",
        "critic_coefficient": CRITIC_COEFFICIENT,
        "episodes_per_update": 64,
        "episode_weighting": "equal",
        "backward_calls_per_arm_update": 1,
        "adam_learning_rate": ADAM_LEARNING_RATE,
        "adam_betas": ADAM_BETAS,
        "adam_epsilon": ADAM_EPSILON,
        "adam_weight_decay": 0.0,
        "global_gradient_norm_clip": GLOBAL_GRADIENT_NORM_CLIP,
        "projection_order": "after Adam step, moments unprojected",
    }


def _validate_episode_inputs(inputs: EpisodeLossInputs) -> None:
    if inputs.selected_probabilities.shape != (3, 6):
        raise ValueError("selected_probabilities must have shape [3,6]")
    if inputs.selected_probabilities.dtype is not torch.float32:
        raise TypeError("selected_probabilities must be float32")
    if inputs.selected_factual_actions.shape != (3,):
        raise ValueError("selected_factual_actions must have shape [3]")
    if inputs.selected_factual_actions.dtype not in (torch.int32, torch.int64):
        raise TypeError("selected_factual_actions must use an integer dtype")
    if inputs.selected_legal_mask.shape != (3, 6) or inputs.selected_legal_mask.dtype is not torch.bool:
        raise ValueError("selected_legal_mask must be bool [3,6]")
    if inputs.q_targets.shape != (3, 6):
        raise ValueError("q_targets must have shape [3,6]")
    if inputs.factual_return.ndim != 0 or inputs.factual_return.dtype is not torch.float32:
        raise ValueError("factual_return must be one float32 scalar")
    if inputs.factual_return.requires_grad or inputs.factual_return.grad_fn is not None:
        raise ValueError("factual_return must be detached")
    if not bool(torch.isfinite(inputs.factual_return).item()):
        raise ValueError("factual_return is nonfinite")
    if inputs.all_slot_agent_entropy.ndim != 2 or inputs.all_slot_agent_entropy.shape[0] != 12:
        raise ValueError("all_slot_agent_entropy must have shape [12,N]")
    if inputs.all_slot_agent_entropy.dtype is not torch.float32:
        raise TypeError("all_slot_agent_entropy must be float32")
    if inputs.critic_values.shape != (12,) or inputs.critic_values.dtype is not torch.float32:
        raise ValueError("critic_values must be float32 [12]")
    if inputs.selected_role_indices.shape != (3,):
        raise ValueError("selected_role_indices must have shape [3]")
    expected_roles = torch.tensor(
        (0, 1, 2), dtype=inputs.selected_role_indices.dtype, device=inputs.selected_role_indices.device
    )
    if not bool(torch.equal(inputs.selected_role_indices, expected_roles)):
        raise ValueError("selected origins must be ordered WEST, EAST, RELAY")
    for name, value in (
        ("selected_probabilities", inputs.selected_probabilities),
        ("all_slot_agent_entropy", inputs.all_slot_agent_entropy),
        ("critic_values", inputs.critic_values),
    ):
        if not bool(torch.isfinite(value).all().item()):
            raise ValueError(f"{name} contains a nonfinite value")


def _validate_adam_hyperparameters(optimizer: torch.optim.Adam) -> None:
    if len(optimizer.param_groups) != 1:
        raise ValueError("the joint optimizer must have exactly one parameter group")
    group = optimizer.param_groups[0]
    observed = (
        float(group["lr"]),
        tuple(float(value) for value in group["betas"]),
        float(group["eps"]),
        float(group["weight_decay"]),
    )
    expected = (ADAM_LEARNING_RATE, ADAM_BETAS, ADAM_EPSILON, 0.0)
    if observed != expected:
        raise ValueError(f"optimizer hyperparameters {observed} != frozen {expected}")
