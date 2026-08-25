from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

import numpy as np
import torch

from .authorization import ProductionPermit
from .config import ARMS, COMMON_ARMS, LOCKS, REGISTERED, TRAIN_SIZES
from .host import Roster, make_roster
from .models import Actor, Posterior, paired_models
from .rng import generator, permutation4


@dataclass(frozen=True)
class BlockData:
    n: int
    roster: Roster
    locks: np.ndarray
    probe_latents: np.ndarray
    private_latents: np.ndarray
    shuffled_labels: np.ndarray
    action_uniforms: np.ndarray


@dataclass(frozen=True)
class TrainingResult:
    seed: int
    actors: dict[str, Actor]
    posteriors: dict[str, Posterior]
    common_baselines: dict[str, np.ndarray]
    independent_baseline: np.ndarray
    metadata: dict[str, object]


def _block(permit: ProductionPermit, seed: int, update: int, n: int) -> BlockData:
    roster = make_roster(permit, "training", seed, n, "update", update)
    lock_order = permutation4(permit, "training", seed, n, update, "hidden_lock_order")
    locks: list[int] = []
    latents: list[int] = []
    for lock in lock_order.tolist():
        probe_order = permutation4(
            permit, "training", seed, n, update, "lock", lock, "probe_order",
        )
        locks.extend([int(lock)] * 4)
        latents.extend(int(value) for value in probe_order)
    private = generator(
        permit, "training", seed, n, update, "private_latents",
    ).integers(0, 4, size=(16, n), dtype=np.int64)
    shuffled = generator(
        permit, "training", seed, n, update, "shuffled_labels",
    ).integers(0, 4, size=16, dtype=np.int64)
    uniforms = generator(
        permit, "training", seed, n, update, "actor_uniforms",
    ).random((2, 16, n), dtype=np.float64)
    return BlockData(
        n=n,
        roster=roster,
        locks=np.asarray(locks, dtype=np.int64),
        probe_latents=np.asarray(latents, dtype=np.int64),
        private_latents=private,
        shuffled_labels=shuffled,
        action_uniforms=uniforms,
    )


def _inputs(
    roster: Roster,
    latents: np.ndarray,
    phase: int,
    previous: torch.Tensor | None = None,
) -> torch.Tensor:
    if latents.ndim != 2 or latents.shape[1] != len(roster.x):
        raise ValueError("batched latent shape mismatch")
    batch, n = latents.shape
    x = np.broadcast_to(roster.x, (batch, n))
    mu = np.full((batch, n), roster.mu, dtype=np.float64)
    one_hot = np.eye(4, dtype=np.float64)[latents]
    if phase == 1:
        phase_fields = np.zeros((batch, n, 4), dtype=np.float64)
        phase_fields[..., 0] = 1.0
    elif phase == 2 and previous is not None:
        previous_np = previous.detach().cpu().numpy().astype(np.float64, copy=False)
        phase_fields = np.zeros((batch, n, 4), dtype=np.float64)
        phase_fields[..., 1:3] = 1.0
        phase_fields[..., 3] = 2.0 * previous_np - 1.0
    else:
        raise ValueError("phase-two inputs require previous action")
    values = np.concatenate(
        (x[..., None], mu[..., None], (x - mu)[..., None], phase_fields, one_hot), axis=-1,
    )
    return torch.from_numpy(values)


def _phase2_counterfactual_inputs(roster: Roster, latents: np.ndarray, action: int) -> torch.Tensor:
    batch, n = latents.shape
    previous = torch.full((batch, n), action, dtype=torch.int64)
    return _inputs(roster, latents, 2, previous)


def _sample(probabilities: torch.Tensor, uniforms: np.ndarray) -> torch.Tensor:
    u = torch.from_numpy(uniforms)
    return (u >= probabilities[..., 0]).to(torch.int64)


def _entropy(probabilities: torch.Tensor) -> torch.Tensor:
    return -(probabilities * torch.log(probabilities)).sum(dim=-1)


def _rollout(
    actor: Actor,
    posterior: Posterior,
    arm: str,
    block: BlockData,
) -> dict[str, torch.Tensor | np.ndarray | int]:
    episode_latents = (
        block.private_latents
        if arm == "INDEPENDENT-ENTROPY"
        else np.broadcast_to(block.probe_latents[:, None], (16, block.n))
    )
    first_logits = actor(_inputs(block.roster, episode_latents, 1))
    first_probabilities = torch.softmax(first_logits, dim=-1)
    first_actions = _sample(first_probabilities, block.action_uniforms[0])

    # Every arm computes the same exact autoregressive entropy work. Only the
    # independent arm connects it to the actor loss.
    phase2_zero = torch.softmax(
        actor(_phase2_counterfactual_inputs(block.roster, episode_latents, 0)), dim=-1,
    )
    phase2_one = torch.softmax(
        actor(_phase2_counterfactual_inputs(block.roster, episode_latents, 1)), dim=-1,
    )
    phase2_probabilities = torch.where(
        first_actions[..., None] == 0, phase2_zero, phase2_one,
    )
    second_actions = _sample(phase2_probabilities, block.action_uniforms[1])

    first_selected = torch.log(
        first_probabilities.gather(-1, first_actions[..., None]).squeeze(-1),
    )
    second_selected = torch.log(
        phase2_probabilities.gather(-1, second_actions[..., None]).squeeze(-1),
    )
    log_probability = (first_selected + second_selected).sum(dim=1)
    route_entropy = (
        _entropy(first_probabilities)
        + first_probabilities[..., 0] * _entropy(phase2_zero)
        + first_probabilities[..., 1] * _entropy(phase2_one)
    ).mean(dim=1) / math.log(4.0)

    bins = torch.from_numpy(block.roster.bins).view(1, block.n)
    routes = 2 * first_actions + second_actions
    rotations = (routes - bins) % 4
    counts = torch.nn.functional.one_hot(rotations, num_classes=4).sum(dim=1)
    maximum, winners = counts.max(dim=1)
    valid = maximum.to(torch.float64) / float(block.n) >= 0.75
    rewards = valid & (winners == torch.from_numpy(block.locks))

    log_q = posterior.log_probabilities()
    information = torch.zeros(16, dtype=torch.float64)
    valid_indices = torch.nonzero(valid, as_tuple=False).flatten()
    valid_rows = winners.detach()[valid_indices]
    if arm == "SHUFFLED-MI" and valid_indices.numel():
        shuffled = torch.from_numpy(block.shuffled_labels)[valid_indices]
        selected_score = 1.0 + log_q[valid_rows, shuffled] / math.log(4.0)
        centered = selected_score - (
            1.0 + log_q[valid_rows].mean(dim=1) / math.log(4.0)
        )
        information[valid_indices] = centered.detach()
    elif arm == "RCLE" and valid_indices.numel():
        z = torch.from_numpy(block.probe_latents)[valid_indices]
        score = 1.0 + log_q[valid_rows, z] / math.log(4.0)
        information[valid_indices] = score.detach()

    labels = (
        block.probe_latents
        if arm in COMMON_ARMS
        else block.probe_latents  # uniform dummy probe label, excluded from actor/environment
    )
    label_tensor = torch.from_numpy(labels)
    posterior_terms = log_q.sum() * torch.zeros(16, dtype=torch.float64)
    if valid_indices.numel():
        posterior_terms[valid_indices] = log_q[
            valid_rows, label_tensor[valid_indices]
        ]
    return {
        "log_probability": log_probability,
        "route_entropy": route_entropy,
        "valid": valid,
        "winners": winners,
        "rewards": rewards.to(torch.float64),
        "information": information,
        "posterior_terms": posterior_terms,
        "invalid_posterior_symbols": 0,
    }


def _adam(parameters, learning_rate: float) -> torch.optim.Adam:
    return torch.optim.Adam(
        parameters,
        lr=learning_rate,
        betas=(REGISTERED.adam_beta1, REGISTERED.adam_beta2),
        eps=REGISTERED.adam_epsilon,
        weight_decay=0.0,
        foreach=False,
    )


def train_seed(
    permit: ProductionPermit,
    seed: int,
    progress_guard: Callable[[], None] | None = None,
) -> TrainingResult:
    permit.require_seed(seed)
    actors, posteriors = paired_models(permit, seed)
    actor_optimizers = {arm: _adam(actors[arm].parameters(), REGISTERED.actor_learning_rate) for arm in ARMS}
    posterior_optimizers = {
        arm: _adam(posteriors[arm].parameters(), REGISTERED.posterior_learning_rate) for arm in ARMS
    }
    common_baselines = {arm: np.zeros((2, 4), dtype=np.float64) for arm in COMMON_ARMS}
    independent_baseline = np.zeros(2, dtype=np.float64)
    total_proposals = 0
    max_proposals = 0
    valid_posterior_updates = {arm: 0 for arm in ARMS}
    invalid_posterior_symbols = 0

    for update in range(REGISTERED.train_updates):
        if progress_guard is not None:
            progress_guard()
        blocks = [_block(permit, seed, update, n) for n in TRAIN_SIZES]
        total_proposals += sum(block.roster.proposal_count for block in blocks)
        max_proposals = max(max_proposals, *(block.roster.proposal_count for block in blocks))
        for arm in ARMS:
            if progress_guard is not None:
                progress_guard()
            rollouts = [_rollout(actors[arm], posteriors[arm], arm, block) for block in blocks]
            actor_optimizer = actor_optimizers[arm]
            actor_optimizer.zero_grad(set_to_none=True)
            per_size_losses: list[torch.Tensor] = []
            targets: list[np.ndarray] = []
            for n_index, rollout in enumerate(rollouts):
                rewards = rollout["rewards"]
                log_probability = rollout["log_probability"]
                if arm in COMMON_ARMS:
                    target = rewards + REGISTERED.beta * rollout["information"]
                    z = blocks[n_index].probe_latents
                    baseline = torch.from_numpy(common_baselines[arm][n_index, z])
                    loss = -((target - baseline).detach() * log_probability).mean()
                    targets.append(target.detach().cpu().numpy())
                else:
                    baseline = float(independent_baseline[n_index])
                    loss = -(
                        ((rewards - baseline).detach() * log_probability)
                        + REGISTERED.alpha * rollout["route_entropy"]
                    ).mean()
                    targets.append(rewards.detach().cpu().numpy())
                per_size_losses.append(loss)
            actor_loss = 0.5 * (per_size_losses[0] + per_size_losses[1])
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                tuple(actors[arm].parameters()),
                REGISTERED.gradient_clip_norm,
                norm_type=2.0,
                error_if_nonfinite=True,
                foreach=False,
            )
            actor_optimizer.step()

            # The baselines are action-independent stopped state and update
            # after the actor step from this block's frozen target values.
            if arm in COMMON_ARMS:
                for n_index, block in enumerate(blocks):
                    for z in range(4):
                        mean_target = float(targets[n_index][block.probe_latents == z].mean())
                        common_baselines[arm][n_index, z] = (
                            REGISTERED.baseline_decay * common_baselines[arm][n_index, z]
                            + (1.0 - REGISTERED.baseline_decay) * mean_target
                        )
            else:
                for n_index in range(2):
                    independent_baseline[n_index] = (
                        REGISTERED.baseline_decay * independent_baseline[n_index]
                        + (1.0 - REGISTERED.baseline_decay) * float(targets[n_index].mean())
                    )

            posterior_optimizer = posterior_optimizers[arm]
            posterior_optimizer.zero_grad(set_to_none=True)
            posterior_loss = -0.5 * (
                rollouts[0]["posterior_terms"].mean() + rollouts[1]["posterior_terms"].mean()
            )
            posterior_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                tuple(posteriors[arm].parameters()),
                REGISTERED.gradient_clip_norm,
                norm_type=2.0,
                error_if_nonfinite=True,
                foreach=False,
            )
            posterior_optimizer.step()
            valid_posterior_updates[arm] += int(
                rollouts[0]["valid"].sum().item() + rollouts[1]["valid"].sum().item()
            )
            invalid_posterior_symbols += int(rollouts[0]["invalid_posterior_symbols"])
            invalid_posterior_symbols += int(rollouts[1]["invalid_posterior_symbols"])

    return TrainingResult(
        seed=seed,
        actors=actors,
        posteriors=posteriors,
        common_baselines=common_baselines,
        independent_baseline=independent_baseline,
        metadata={
            "updates_completed": REGISTERED.train_updates,
            "training_episodes": len(ARMS) * len(TRAIN_SIZES)
            * REGISTERED.train_updates * REGISTERED.train_episodes_per_size_update,
            "actor_optimizer_steps": len(ARMS) * REGISTERED.train_updates,
            "posterior_optimizer_steps": len(ARMS) * REGISTERED.train_updates,
            "accepted_roster_proposals": total_proposals,
            "max_proposals_for_one_roster": max_proposals,
            "valid_posterior_training_episodes": valid_posterior_updates,
            "invalid_posterior_symbols": invalid_posterior_symbols,
            "posterior_invalid_fixed_uniform": True,
            "only_evaluable_checkpoint": "immediately_after_update_2000",
            "validation_selection": False,
            "early_stopping": False,
            "heldout_tuning": False,
        },
    )
