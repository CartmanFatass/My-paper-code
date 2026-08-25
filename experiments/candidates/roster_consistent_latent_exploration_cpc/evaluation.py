from __future__ import annotations

from typing import Any

import numpy as np
import torch

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, EVAL_SIZES, REGISTERED
from .host import EpisodeBatch, evaluate_outcomes, make_episode_batch
from .models import ArmModel, actor_inputs, inverse_cdf
from .rng import generator
from .training import CellData, TrainingResult, rollout


def _finalize(result: dict[str, object], batch: EpisodeBatch) -> dict[str, Any]:
    outcomes = result["outcomes"]
    macro = np.asarray(result["macro"], dtype=np.int64)
    refinement = result["refinement"]
    macro_p = np.asarray(result["macro_probabilities"], dtype=np.float64)
    clue_sum = batch.initial_clues.sum(axis=1)
    majority_index = np.where(clue_sum < 0, 0, np.where(clue_sum > 0, 2, 1))
    by_majority = []
    for index, label in enumerate(("LEFT", "TIE", "RIGHT")):
        selected = majority_index == index
        by_majority.append({
            "majority": label,
            "episodes": int(selected.sum()),
            "mean_p_macro_1": float(macro_p[selected, 1].mean()) if selected.any() else 0.0,
        })
    out: dict[str, Any] = {
        "mean_value": float(outcomes.value.mean()),
        "mission_success": float(outcomes.mission.mean()),
        "fragmentation": float(outcomes.fragmentation.mean()),
        "pre_target_accuracy": float(outcomes.pre_accuracy.mean()),
        "post_target_accuracy": float(outcomes.post_accuracy.mean()),
        "pre_validity": float(outcomes.pre_validity.mean()),
        "post_validity": float(outcomes.post_validity.mean()),
        "episodes": len(outcomes.value),
        "macro_occupancy": np.bincount(macro, minlength=2).tolist(),
        "manager_by_clue_majority": by_majority,
        "source_map_fixed_points": int(
            (np.asarray(result["source_indices"], dtype=np.int64) == np.arange(len(macro))).sum()
        ),
        "role_corridor_histograms": {
            "PRE": [
                np.bincount(
                    np.asarray(result["pre_actions"], dtype=np.int64)[batch.initial_roles == role],
                    minlength=3,
                ).tolist()
                for role in (0, 1)
            ],
            "POST": [
                np.bincount(
                    np.asarray(result["post_actions"], dtype=np.int64)[batch.post_roles == role],
                    minlength=3,
                ).tolist()
                for role in (0, 1)
            ],
        },
    }
    if refinement is not None:
        joint = 4 * macro + np.asarray(refinement, dtype=np.int64)
        occupancy = np.bincount(joint, minlength=8)
        out["refinement_occupancy"] = occupancy.tolist()
        out["effective_cardinality"] = int((occupancy > 0).sum())
    else:
        out["refinement_occupancy"] = [0] * 8
        out["effective_cardinality"] = int((np.bincount(macro, minlength=2) > 0).sum())
    return out


def _cut_rollout(
    permit: ProductionPermit,
    model: ArmModel,
    batch: EpisodeBatch,
    macro_p: torch.Tensor,
    pre_macro: torch.Tensor,
    post_macro: torch.Tensor,
    action_uniforms: np.ndarray,
) -> dict[str, float | int]:
    require_active_permit(permit)
    n = batch.n
    pre_latent = model.macro_base[pre_macro]
    post_latent = model.macro_base[post_macro]
    pre_probabilities = torch.softmax(
        model.actor(actor_inputs(batch.initial_roles, batch.initial_clues, 0, n, pre_latent)), dim=-1,
    )
    pre_actions = inverse_cdf(permit, pre_probabilities, action_uniforms[0])
    post_probabilities = torch.softmax(
        model.actor(actor_inputs(batch.post_roles, batch.post_clues, 1, n, post_latent)), dim=-1,
    )
    post_actions = inverse_cdf(permit, post_probabilities, action_uniforms[1])
    outcomes = evaluate_outcomes(
        batch, pre_actions.cpu().numpy(), post_actions.cpu().numpy(),
    )
    return {
        "mean_value": float(outcomes.value.mean()),
        "mission_success": float(outcomes.mission.mean()),
        "fragmentation": float(outcomes.fragmentation.mean()),
        "episodes": len(outcomes.value),
    }


def evaluate_seed(
    permit: ProductionPermit,
    training: TrainingResult,
    progress_guard=None,
) -> dict[str, Any]:
    require_active_permit(permit)
    permit.require_seed(training.seed)
    cells: dict[str, Any] = {}
    heldout_batch: EpisodeBatch | None = None
    heldout_action_uniforms: np.ndarray | None = None
    heldout_macro_p: torch.Tensor | None = None
    heldout_intact_macro: torch.Tensor | None = None
    with torch.no_grad():
        for n in EVAL_SIZES:
            cells[str(n)] = {}
            for handoff in (False, True):
                if progress_guard is not None:
                    progress_guard()
                size = REGISTERED.eval_episodes_per_cell
                batch = make_episode_batch(permit, "evaluation", training.seed, n, handoff, 0, size)
                macro_uniforms = generator(
                    permit, "evaluation", training.seed, n, handoff, "macro_uniforms",
                ).random(size)
                refinement_uniforms = generator(
                    permit, "evaluation", training.seed, n, handoff, "refinement_uniforms",
                ).random(size)
                action_uniforms = generator(
                    permit, "evaluation", training.seed, n, handoff, "action_uniforms",
                ).random((2, size, n))
                shift = int(generator(
                    permit, "evaluation", training.seed, n, handoff, "cyclic_shift",
                ).integers(1, size))
                data = CellData(batch, macro_uniforms, refinement_uniforms, action_uniforms, shift)
                label = "handoff" if handoff else "no_handoff"
                cells[str(n)][label] = {}
                for arm in ARMS:
                    result = rollout(permit, training.models[arm], arm, data)
                    cells[str(n)][label][arm] = _finalize(result, batch)
                if n == 9 and handoff:
                    heldout_batch = batch
                    heldout_action_uniforms = action_uniforms
                    model = training.models["COARSE-PERSISTENT"]
                    heldout_macro_p, _ = model.manager(
                        torch.from_numpy(batch.initial_roles), torch.from_numpy(batch.initial_clues), n,
                    )
                    heldout_intact_macro = inverse_cdf(permit, heldout_macro_p, macro_uniforms)

        if any(value is None for value in (
            heldout_batch, heldout_action_uniforms, heldout_macro_p, heldout_intact_macro,
        )):
            raise RuntimeError("held-out N=9 handoff cell was not established")
        model = training.models["COARSE-PERSISTENT"]
        batch = heldout_batch
        size, n = REGISTERED.eval_episodes_per_cell, 9
        private_pre_u = generator(
            permit, "evaluation", training.seed, n, True, "private_cut_pre_macro",
        ).random((size, n))
        private_post_u = generator(
            permit, "evaluation", training.seed, n, True, "private_cut_newcomer_macro",
        ).random((size, n))
        expanded_p = heldout_macro_p[:, None, :].expand(-1, n, -1)
        private_pre = inverse_cdf(permit, expanded_p, private_pre_u)
        fresh_post = inverse_cdf(permit, expanded_p, private_post_u)
        private_post = torch.where(torch.from_numpy(batch.replaced), fresh_post, private_pre)
        temporal_u = generator(
            permit, "evaluation", training.seed, n, True, "temporal_reset_macro",
        ).random(size)
        temporal_post = inverse_cdf(permit, heldout_macro_p, temporal_u)
        cuts = {
            "PRIVATE-LATENT-CUT": _cut_rollout(
                permit, model, batch, heldout_macro_p, private_pre, private_post, heldout_action_uniforms,
            ),
            "TEMPORAL-RESET-CUT": _cut_rollout(
                permit, model, batch, heldout_macro_p, heldout_intact_macro, temporal_post, heldout_action_uniforms,
            ),
        }
    return {
        "seed": training.seed,
        "cells": cells,
        "cuts": cuts,
        "ordinary_episodes": len(ARMS) * len(EVAL_SIZES) * 2 * REGISTERED.eval_episodes_per_cell,
        "cut_episodes": 2 * REGISTERED.eval_episodes_per_cell,
        "frozen_checkpoint": "immediately_after_update_1000",
        "evaluation_updates": 0,
        "heldout_training_or_adaptation": False,
        "selected_checkpoint": False,
        "mechanism_index": {"N": 9, "handoff": True},
    }
