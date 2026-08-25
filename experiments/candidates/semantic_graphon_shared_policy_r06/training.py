from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np
import torch

from .authorization import ProductionPermit
from .config import ARMS, REGISTERED, TRAIN_CELLS_LEXICOGRAPHIC
from .policies import (
    SharedSGSPPolicy,
    actions_from_uniforms,
    common_tensors_bitwise_equal,
    paired_policy_set,
    parameter_count,
)
from .world import World, generate_world


@dataclass(frozen=True)
class TrainingResult:
    seed: int
    models: dict[str, SharedSGSPPolicy]
    metadata: dict[str, object]


def _tensor_world(
    permit: ProductionPermit, world: World,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    return (
        torch.from_numpy(world.x.copy()).to(torch.float64),
        torch.from_numpy(world.roles.copy()).to(torch.int64),
        torch.from_numpy(world.targets.copy()).to(torch.int64),
        torch.from_numpy(world.action_uniforms(permit)).to(torch.float64),
    )


def _per_world_loss(
    permit: ProductionPermit, model: SharedSGSPPolicy, world: World,
) -> torch.Tensor:
    messages, roles, targets, uniforms = _tensor_world(permit, world)
    output = model(messages, roles)
    actions = actions_from_uniforms(output.probabilities, uniforms)
    correctness = (actions == targets).to(torch.float64)
    realized_return = correctness.mean()
    correct_action_probability = output.probabilities.gather(1, targets[:, None]).squeeze(1)
    baseline = (
        correctness.sum() - correctness + correct_action_probability
    ) / float(world.n)
    advantage = realized_return - baseline
    selected_log_probability = torch.log(
        output.probabilities.gather(1, actions[:, None]).squeeze(1)
    )
    entropy = -(output.probabilities * torch.log(output.probabilities)).sum(dim=1)
    return -(advantage.detach() * selected_log_probability).mean() - (
        REGISTERED.entropy_coefficient * entropy.mean()
    )


def _optimizer(model: SharedSGSPPolicy) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.parameters(),
        lr=REGISTERED.learning_rate,
        betas=(REGISTERED.adam_beta1, REGISTERED.adam_beta2),
        eps=REGISTERED.adam_epsilon,
        weight_decay=REGISTERED.weight_decay,
        amsgrad=REGISTERED.adam_amsgrad,
        foreach=False,
    )


def train_seed(
    permit: ProductionPermit, seed: int, progress_guard: Callable[[], None] | None = None,
) -> TrainingResult:
    permit.require_seed(seed)
    models = paired_policy_set(permit, seed)
    initial_pairing = common_tensors_bitwise_equal(models)
    if not initial_pairing:
        raise RuntimeError("common tensors are not bitwise paired before update 1")
    expected_counts = {
        "SGSP-W": 1318, "ALT-CENTER": 1318, "EDGE-PE": 1318, "ANON-MEAN": 1314,
    }
    counts = {arm: parameter_count(model) for arm, model in models.items()}
    if counts != expected_counts:
        raise RuntimeError(f"registered parameter count mismatch: {counts}")
    optimizers = {arm: _optimizer(model) for arm, model in models.items()}

    final_losses: dict[str, float] = {}
    for update in range(1, REGISTERED.train_updates + 1):
        if progress_guard is not None:
            progress_guard()
        worlds: list[World] = []
        for n, regime in TRAIN_CELLS_LEXICOGRAPHIC:
            for within_cell in range(REGISTERED.worlds_per_train_cell_update):
                episode = 16 * (update - 1) + within_cell
                worlds.append(generate_world(permit, "training", seed, n, regime, episode))
        if len(worlds) != REGISTERED.train_batch_worlds:
            raise RuntimeError("registered batch must contain exactly 64 worlds")

        for arm in ARMS:
            if progress_guard is not None:
                progress_guard()
            optimizer = optimizers[arm]
            optimizer.zero_grad(set_to_none=True)
            accumulated: torch.Tensor | None = None
            for world in worlds:  # Already literal lexicographic cell/episode order.
                loss = _per_world_loss(permit, models[arm], world)
                accumulated = loss if accumulated is None else accumulated + loss
            if accumulated is None:
                raise RuntimeError("empty registered batch")
            mean_loss = accumulated / float(REGISTERED.train_batch_worlds)
            mean_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                tuple(models[arm].parameters()), REGISTERED.gradient_clip_norm,
                norm_type=2.0, error_if_nonfinite=True, foreach=False,
            )
            optimizer.step()
            final_losses[arm] = float(mean_loss.detach().cpu())

    return TrainingResult(
        seed=seed,
        models=models,
        metadata={
            "updates_completed": REGISTERED.train_updates,
            "only_evaluable_checkpoint": "immediately_after_optimizer_update_240",
            "initial_common_tensors_bitwise_equal": initial_pairing,
            "parameter_counts": counts,
            "final_training_loss_descriptive_only": final_losses,
            "validation_selection": False,
            "early_stopping": False,
            "heldout_calibration": False,
            "posthoc_seed_replacement": False,
        },
    )
