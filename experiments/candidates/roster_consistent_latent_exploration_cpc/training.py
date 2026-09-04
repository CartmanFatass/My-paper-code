from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

import numpy as np
import torch

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, REGISTERED, TRAIN_SIZES
from .host import EpisodeBatch, evaluate_outcomes, make_episode_batch
from .models import ArmModel, actor_inputs, inverse_cdf, paired_models
from .rng import generator


@dataclass(frozen=True)
class CellData:
    batch: EpisodeBatch
    macro_uniforms: np.ndarray
    refinement_uniforms: np.ndarray
    action_uniforms: np.ndarray
    cyclic_shift: int


@dataclass(frozen=True)
class TrainingResult:
    seed: int
    models: dict[str, ArmModel]
    baselines: dict[str, np.ndarray]
    metadata: dict[str, object]


def _cell_index(n: int, handoff: bool) -> int:
    return (0 if n == 5 else 2) + int(handoff)


def _block_cell(
    permit: ProductionPermit, seed: int, update: int, n: int, handoff: bool,
) -> CellData:
    size = REGISTERED.train_episodes_per_cell
    batch = make_episode_batch(permit, "training", seed, n, handoff, update * size, size)
    return CellData(
        batch=batch,
        macro_uniforms=generator(permit, "training", seed, update, n, handoff, "macro_uniforms").random(size),
        refinement_uniforms=generator(permit, "training", seed, update, n, handoff, "refinement_uniforms").random(size),
        action_uniforms=generator(permit, "training", seed, update, n, handoff, "action_uniforms").random((2, size, n)),
        cyclic_shift=int(generator(permit, "training", seed, update, n, handoff, "cyclic_shift").integers(1, size)),
    )


def _sample_actions(
    permit: ProductionPermit,
    probabilities: torch.Tensor,
    uniforms: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor]:
    actions = inverse_cdf(permit, probabilities, uniforms)
    selected = torch.log(probabilities.gather(-1, actions[..., None]).squeeze(-1))
    return actions, selected


def rollout(permit: ProductionPermit, model: ArmModel, arm: str, data: CellData) -> dict[str, object]:
    require_active_permit(permit)
    if arm not in ARMS:
        raise ValueError("arm outside CPC registry")
    batch, n = data.batch, data.batch.n
    roles = torch.from_numpy(batch.initial_roles)
    clues = torch.from_numpy(batch.initial_clues)
    macro_p, refinement_q = model.manager(roles, clues, n)
    source_macro = inverse_cdf(permit, macro_p, data.macro_uniforms)
    source_log_macro = torch.log(macro_p.gather(1, source_macro[:, None]).squeeze(1))

    if arm == "CONTEXT-SHUFFLED-COARSE":
        macro = torch.roll(source_macro, shifts=data.cyclic_shift, dims=0)
        log_macro = torch.roll(source_log_macro, shifts=data.cyclic_shift, dims=0)
        source_indices = torch.roll(torch.arange(len(source_macro)), shifts=data.cyclic_shift)
        refinement = None
    else:
        macro, log_macro = source_macro, source_log_macro
        source_indices = torch.arange(len(source_macro))
        if arm == "FLEXIBLE-PERSISTENT":
            selected_q = refinement_q[torch.arange(len(macro)), macro]
            refinement = inverse_cdf(permit, selected_q, data.refinement_uniforms)
            log_macro = log_macro + torch.log(
                selected_q.gather(1, refinement[:, None]).squeeze(1),
            )
        else:
            refinement = None

    latent = model.latent(macro, refinement, arm == "FLEXIBLE-PERSISTENT")
    pre_logits = model.actor(actor_inputs(batch.initial_roles, batch.initial_clues, 0, n, latent))
    pre_p = torch.softmax(pre_logits, dim=-1)
    pre_actions, pre_log = _sample_actions(permit, pre_p, data.action_uniforms[0])
    post_logits = model.actor(actor_inputs(batch.post_roles, batch.post_clues, 1, n, latent))
    post_p = torch.softmax(post_logits, dim=-1)
    post_actions, post_log = _sample_actions(permit, post_p, data.action_uniforms[1])
    outcomes = evaluate_outcomes(
        batch,
        pre_actions.detach().cpu().numpy(),
        post_actions.detach().cpu().numpy(),
    )
    score = log_macro + pre_log.sum(dim=1) + post_log.sum(dim=1)
    return {
        "score": score,
        "outcomes": outcomes,
        "macro": macro.detach().cpu().numpy(),
        "refinement": None if refinement is None else refinement.detach().cpu().numpy(),
        "source_indices": source_indices.detach().cpu().numpy(),
        "macro_probabilities": macro_p.detach().cpu().numpy(),
        "refinement_probabilities": refinement_q.detach().cpu().numpy(),
        "pre_actions": pre_actions.detach().cpu().numpy(),
        "post_actions": post_actions.detach().cpu().numpy(),
    }


def complete_gradient(model: ArmModel) -> tuple[list[torch.Tensor], torch.Tensor, float]:
    gradients: list[torch.Tensor] = []
    flattened: list[torch.Tensor] = []
    for parameter in model.parameters():
        gradient = torch.zeros_like(parameter) if parameter.grad is None else parameter.grad.detach().clone()
        gradients.append(gradient)
        flattened.append(gradient.reshape(-1))
    vector = torch.cat(flattened)
    if not bool(torch.isfinite(vector).all()):
        raise FloatingPointError("nonfinite raw gradient in complete registered tensor")
    norm = float(torch.linalg.vector_norm(vector).item())
    return gradients, vector, norm


def normalized_joint_update(model: ArmModel) -> tuple[torch.Tensor, float, float]:
    gradients, vector, raw_norm = complete_gradient(model)
    if raw_norm == 0.0:
        scale = 0.0
    else:
        scale = REGISTERED.learning_rate * REGISTERED.gradient_direction_scale / raw_norm
    with torch.no_grad():
        for parameter, gradient in zip(model.parameters(), gradients, strict=True):
            parameter.add_(gradient, alpha=-scale)
    update_norm = 0.0 if raw_norm == 0.0 else REGISTERED.nonzero_update_norm
    return vector, raw_norm, update_norm


def _cosine(left: torch.Tensor, right: torch.Tensor) -> float | None:
    denominator = float(torch.linalg.vector_norm(left) * torch.linalg.vector_norm(right))
    return None if denominator == 0.0 else float(torch.dot(left, right).item() / denominator)


def train_seed(
    permit: ProductionPermit,
    seed: int,
    progress_guard: Callable[[], None] | None = None,
) -> TrainingResult:
    require_active_permit(permit)
    permit.require_seed(seed)
    models = paired_models(permit, seed)
    # This check occurs only after a lease has authorized inspection of the
    # fresh initialization.  It enforces the registered live-extension fact
    # before the first optimizer update.
    initial_residual_jacobian_nonzero: dict[str, bool] = {}
    fixture_roles = np.asarray([[0, 0, 0, 1, 1]], dtype=np.int64)
    fixture_clues = np.ones((1, 5), dtype=np.int64)
    for arm, model in models.items():
        residual_probe = torch.zeros((1, 8), dtype=torch.float64, requires_grad=True)
        latent = model.macro_base[torch.zeros(1, dtype=torch.int64)] + residual_probe
        probabilities = torch.softmax(
            model.actor(actor_inputs(fixture_roles, fixture_clues, 0, 5, latent)), dim=-1,
        )
        gradient = torch.autograd.grad(probabilities[0, 0, 0], residual_probe)[0]
        initial_residual_jacobian_nonzero[arm] = bool(torch.count_nonzero(gradient).item() > 0)
    if not all(initial_residual_jacobian_nonzero.values()):
        raise RuntimeError("fresh initialized actor lacks the registered residual output Jacobian")
    baselines = {arm: np.zeros(4, dtype=np.float64) for arm in ARMS}
    zero_steps = {arm: 0 for arm in ARMS}
    raw_norm_sum = {arm: 0.0 for arm in ARMS}
    update_norm_sum = {arm: 0.0 for arm in ARMS}
    cosine_sum: dict[str, float] = {"COARSE|FLEXIBLE": 0.0, "COARSE|SHUFFLED": 0.0, "FLEXIBLE|SHUFFLED": 0.0}
    cosine_count = {key: 0 for key in cosine_sum}

    for update in range(REGISTERED.train_updates):
        if progress_guard is not None:
            progress_guard()
        cells = [
            _block_cell(permit, seed, update, n, handoff)
            for n in TRAIN_SIZES for handoff in (False, True)
        ]
        vectors: dict[str, torch.Tensor] = {}
        for arm in ARMS:
            model = models[arm]
            model.zero_grad(set_to_none=True)
            losses: list[torch.Tensor] = []
            cell_values: list[np.ndarray] = []
            for cell in cells:
                result = rollout(permit, model, arm, cell)
                values = result["outcomes"].value
                index = _cell_index(cell.batch.n, cell.batch.handoff)
                advantage = torch.from_numpy(values - baselines[arm][index])
                losses.append(-(advantage.detach() * result["score"]).sum() / 64.0)
                cell_values.append(values)
            sum(losses).backward()
            vector, raw_norm, update_norm = normalized_joint_update(model)
            vectors[arm] = vector
            zero_steps[arm] += int(raw_norm == 0.0)
            raw_norm_sum[arm] += raw_norm
            update_norm_sum[arm] += update_norm
            for cell, values in zip(cells, cell_values, strict=True):
                index = _cell_index(cell.batch.n, cell.batch.handoff)
                baselines[arm][index] = (
                    REGISTERED.baseline_decay * baselines[arm][index]
                    + (1.0 - REGISTERED.baseline_decay) * float(values.mean())
                )
        for label, left, right in (
            ("COARSE|FLEXIBLE", ARMS[0], ARMS[1]),
            ("COARSE|SHUFFLED", ARMS[0], ARMS[2]),
            ("FLEXIBLE|SHUFFLED", ARMS[1], ARMS[2]),
        ):
            value = _cosine(vectors[left], vectors[right])
            if value is not None:
                cosine_sum[label] += value
                cosine_count[label] += 1

    return TrainingResult(
        seed=seed,
        models=models,
        baselines=baselines,
        metadata={
            "updates_completed": REGISTERED.train_updates,
            "training_episodes": len(ARMS) * REGISTERED.train_updates * 4 * REGISTERED.train_episodes_per_cell,
            "optimizer_steps": len(ARMS) * REGISTERED.train_updates,
            "zero_gradient_steps": zero_steps,
            "mean_raw_gradient_norm": {arm: raw_norm_sum[arm] / REGISTERED.train_updates for arm in ARMS},
            "cumulative_update_norm": update_norm_sum,
            "mean_gradient_cosine": {
                key: (cosine_sum[key] / cosine_count[key] if cosine_count[key] else None)
                for key in cosine_sum
            },
            "complete_registered_parameter_count_per_arm": REGISTERED.parameters_per_arm,
            "initial_coarse_flexible_action_distributions_bit_identical": True,
            "initial_residual_output_jacobian_nonzero": initial_residual_jacobian_nonzero,
            "baselines_updated_after_parameter_step": True,
            "only_evaluable_checkpoint": "immediately_after_update_1000",
            "validation_selection": False,
            "early_stopping": False,
            "checkpoint_selection": False,
        },
    )
