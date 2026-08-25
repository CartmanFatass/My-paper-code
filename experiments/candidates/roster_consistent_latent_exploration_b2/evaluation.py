from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch

from .authorization import ProductionPermit
from .config import ARMS, COMMON_ARMS, EVAL_SIZES, REGISTERED
from .host import make_roster
from .models import Actor, Posterior
from .rng import generator, permutation4
from .training import TrainingResult

_BATCH_CAMPAIGNS = 64


def _inputs(
    x: np.ndarray,
    mu: np.ndarray,
    latents: np.ndarray,
    phase: int,
    previous: torch.Tensor | None = None,
) -> torch.Tensor:
    # x [B,N], mu [B], latents [B,P,N]
    batch, probes, n = latents.shape
    expanded_x = np.broadcast_to(x[:, None, :], (batch, probes, n))
    expanded_mu = np.broadcast_to(mu[:, None, None], (batch, probes, n))
    one_hot = np.eye(4, dtype=np.float64)[latents]
    fields = np.zeros((batch, probes, n, 4), dtype=np.float64)
    if phase == 1:
        fields[..., 0] = 1.0
    elif phase == 2 and previous is not None:
        fields[..., 1:3] = 1.0
        fields[..., 3] = 2.0 * previous.detach().cpu().numpy().astype(np.float64) - 1.0
    else:
        raise ValueError("phase-two inputs require previous actions")
    return torch.from_numpy(np.concatenate((
        expanded_x[..., None], expanded_mu[..., None],
        (expanded_x - expanded_mu)[..., None], fields, one_hot,
    ), axis=-1))


def _phase2_inputs(x: np.ndarray, mu: np.ndarray, latents: np.ndarray, action: int) -> torch.Tensor:
    shape = latents.shape
    return _inputs(x, mu, latents, 2, torch.full(shape, action, dtype=torch.int64))


def _panel(
    actor: Actor,
    x: np.ndarray,
    mu: np.ndarray,
    bins: np.ndarray,
    locks: np.ndarray,
    phase1_latents: np.ndarray,
    phase2_latents: np.ndarray,
    uniforms: np.ndarray,
) -> dict[str, np.ndarray]:
    with torch.no_grad():
        first_probabilities = torch.softmax(actor(_inputs(x, mu, phase1_latents, 1)), dim=-1)
        first_actions = (
            torch.from_numpy(uniforms[:, :, 0, :]) >= first_probabilities[..., 0]
        ).to(torch.int64)
        second_zero = torch.softmax(actor(_phase2_inputs(x, mu, phase2_latents, 0)), dim=-1)
        second_one = torch.softmax(actor(_phase2_inputs(x, mu, phase2_latents, 1)), dim=-1)
        second_probabilities = torch.where(
            first_actions[..., None] == 0, second_zero, second_one,
        )
        second_actions = (
            torch.from_numpy(uniforms[:, :, 1, :]) >= second_probabilities[..., 0]
        ).to(torch.int64)
        routes = 2 * first_actions + second_actions
        rotations = (routes - torch.from_numpy(bins)[:, None, :]) % 4
        counts = torch.nn.functional.one_hot(rotations, num_classes=4).sum(dim=2)
        maximum, winners = counts.max(dim=2)
        valid = maximum.to(torch.float64) / float(bins.shape[1]) >= 0.75
        rewards = valid & (winners == torch.from_numpy(locks)[:, None])
        ties = (counts == maximum[..., None]).sum(dim=2) > 1
    return {
        "routes": routes.cpu().numpy(),
        "rotations": rotations.cpu().numpy(),
        "valid": valid.cpu().numpy(),
        "winners": winners.cpu().numpy(),
        "agreement": (maximum.to(torch.float64) / float(bins.shape[1])).cpu().numpy(),
        "rewards": rewards.cpu().numpy(),
        "ties": ties.cpu().numpy(),
        "p_one_first": first_probabilities[..., 1].cpu().numpy(),
        "p_one_second": second_probabilities[..., 1].cpu().numpy(),
    }


def _ordinary_accumulator(common: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "campaigns": 0,
        "campaign_value_sum": 0,
        "probe_reward_sum": 0,
        "valid_sum": 0,
        "agreement_valid_sum": 0.0,
        "distinct_valid_rotations_sum": 0,
        "route_histogram": np.zeros(4, dtype=np.int64),
        "relative_rotation_histogram": np.zeros(4, dtype=np.int64),
        "invalid_count": 0,
        "tie_count": 0,
        "probability_sum": 0.0,
        "probability_square_sum": 0.0,
        "probability_count": 0,
    }
    if common:
        out.update(
            semantic_matrix=np.zeros((4, 4), dtype=np.int64),
            semantic_denominator=np.zeros(4, dtype=np.int64),
            posterior_correct=0,
            posterior_valid=0,
            normalized_information_sum=0.0,
            anchor_matrix=np.zeros((4, 4), dtype=np.int64),
            anchor_denominator=np.zeros(4, dtype=np.int64),
            scoring_matrix=np.zeros((4, 4), dtype=np.int64),
            scoring_denominator=np.zeros(4, dtype=np.int64),
        )
    return out


def _accumulate(
    accumulator: dict[str, Any],
    panel: dict[str, np.ndarray],
    latents: np.ndarray,
    within_lock_indices: np.ndarray,
    posterior: Posterior | None,
    n: int,
) -> None:
    valid = panel["valid"]
    winners = panel["winners"]
    rewards = panel["rewards"]
    accumulator["campaigns"] += int(valid.shape[0])
    accumulator["campaign_value_sum"] += int(rewards.any(axis=1).sum())
    accumulator["probe_reward_sum"] += int(rewards.sum())
    accumulator["valid_sum"] += int(valid.sum())
    accumulator["agreement_valid_sum"] += float(panel["agreement"][valid].sum())
    accumulator["invalid_count"] += int((~valid).sum())
    accumulator["tie_count"] += int(panel["ties"].sum())
    for row_valid, row_winners in zip(valid, winners, strict=True):
        accumulator["distinct_valid_rotations_sum"] += len(set(row_winners[row_valid].tolist()))
    accumulator["route_histogram"] += np.bincount(panel["routes"].ravel(), minlength=4)
    accumulator["relative_rotation_histogram"] += np.bincount(panel["rotations"].ravel(), minlength=4)
    for key in ("p_one_first", "p_one_second"):
        values = panel[key]
        accumulator["probability_sum"] += float(values.sum(dtype=np.float64))
        accumulator["probability_square_sum"] += float(np.square(values).sum(dtype=np.float64))
        accumulator["probability_count"] += int(values.size)

    if posterior is None:
        return
    common_z = latents[:, :, 0]
    log_q = posterior.log_probabilities().detach().cpu().numpy()
    prediction = log_q.argmax(axis=1)
    for batch_index in range(valid.shape[0]):
        split_anchor = n == 4 and int(within_lock_indices[batch_index]) < REGISTERED.anchor_campaigns_per_lock
        split_scoring = n == 4 and not split_anchor
        for probe in range(4):
            z = int(common_z[batch_index, probe])
            accumulator["semantic_denominator"][z] += 1
            if split_anchor:
                accumulator["anchor_denominator"][z] += 1
            if split_scoring:
                accumulator["scoring_denominator"][z] += 1
            if bool(valid[batch_index, probe]):
                k = int(winners[batch_index, probe])
                accumulator["semantic_matrix"][z, k] += 1
                if split_anchor:
                    accumulator["anchor_matrix"][z, k] += 1
                if split_scoring:
                    accumulator["scoring_matrix"][z, k] += 1
                accumulator["posterior_valid"] += 1
                accumulator["posterior_correct"] += int(prediction[k] == z)
                accumulator["normalized_information_sum"] += 1.0 + log_q[k, z] / math.log(4.0)
            # Invalid episodes contribute q(.|bot)=1/4 and normalized score zero.


def _finalize(accumulator: dict[str, Any], n: int) -> dict[str, Any]:
    campaigns = int(accumulator["campaigns"])
    probes = campaigns * 4
    valid = int(accumulator["valid_sum"])
    p_count = int(accumulator["probability_count"])
    p_mean = float(accumulator["probability_sum"]) / p_count
    p_var = max(0.0, float(accumulator["probability_square_sum"]) / p_count - p_mean * p_mean)
    out: dict[str, Any] = {
        "campaign_task_value": int(accumulator["campaign_value_sum"]) / campaigns,
        "per_probe_return": int(accumulator["probe_reward_sum"]) / probes,
        "validity": valid / probes,
        "mean_winning_agreement": (
            float(accumulator["agreement_valid_sum"]) / valid if valid else 0.0
        ),
        "mean_distinct_valid_rotations": int(accumulator["distinct_valid_rotations_sum"]) / campaigns,
        "hidden_lock_discovery": int(accumulator["campaign_value_sum"]) / campaigns,
        "permitted_input_action_probability_std": math.sqrt(p_var),
        "route_histogram": accumulator["route_histogram"].tolist(),
        "relative_rotation_histogram": accumulator["relative_rotation_histogram"].tolist(),
        "invalid_count": int(accumulator["invalid_count"]),
        "tie_count": int(accumulator["tie_count"]),
        "campaigns": campaigns,
        "episodes": probes,
        "agent_decisions": probes * n * 2,
    }
    if "semantic_matrix" in accumulator:
        denominator = accumulator["semantic_denominator"]
        matrix = accumulator["semantic_matrix"]
        out["common_semantics"] = {
            "per_z_valid_rate": [
                int(matrix[z].sum()) / int(denominator[z]) for z in range(4)
            ],
            "normalized_variational_lower_bound": float(
                accumulator["normalized_information_sum"]
            ) / probes,
            "posterior_accuracy_on_valid": (
                int(accumulator["posterior_correct"]) / int(accumulator["posterior_valid"])
                if accumulator["posterior_valid"] else 0.0
            ),
            "p_k_valid_given_z": [
                (matrix[z].astype(np.float64) / int(denominator[z])).tolist() for z in range(4)
            ],
            "semantic_counts": matrix.tolist(),
            "semantic_denominator": denominator.tolist(),
            "anchor_counts": accumulator["anchor_matrix"].tolist(),
            "anchor_denominator": accumulator["anchor_denominator"].tolist(),
            "scoring_counts": accumulator["scoring_matrix"].tolist(),
            "scoring_denominator": accumulator["scoring_denominator"].tolist(),
        }
    return out


def evaluate_seed(
    permit: ProductionPermit,
    training: TrainingResult,
    progress_guard=None,
) -> dict[str, Any]:
    permit.require_seed(training.seed)
    cells: dict[str, Any] = {}
    cut_cells: dict[str, Any] = {}
    roster_stats: dict[str, Any] = {}
    for n in EVAL_SIZES:
        accumulators = {arm: _ordinary_accumulator(True) for arm in ARMS}
        cut_accumulators = {
            "PRIVATE-LATENT-CUT": _ordinary_accumulator(False),
            "TEMPORAL-LATENT-CUT": _ordinary_accumulator(False),
        }
        xi_values: list[float] = []
        proposals: list[int] = []
        for start in range(0, REGISTERED.eval_campaigns_per_size, _BATCH_CAMPAIGNS):
            if progress_guard is not None:
                progress_guard()
            size = min(_BATCH_CAMPAIGNS, REGISTERED.eval_campaigns_per_size - start)
            x = np.empty((size, n), dtype=np.float64)
            mu = np.empty(size, dtype=np.float64)
            bins = np.empty((size, n), dtype=np.int64)
            locks = np.empty(size, dtype=np.int64)
            within = np.empty(size, dtype=np.int64)
            common_latents = np.empty((size, 4, n), dtype=np.int64)
            cut_private_latents = np.empty((size, 4, n), dtype=np.int64)
            temporal_second = np.empty((size, 4, n), dtype=np.int64)
            uniforms = np.empty((size, 4, 2, n), dtype=np.float64)
            for local, campaign in enumerate(range(start, start + size)):
                lock = campaign // REGISTERED.eval_campaigns_per_lock
                within_lock = campaign % REGISTERED.eval_campaigns_per_lock
                roster = make_roster(
                    permit, "evaluation", training.seed, n, "lock", lock, "campaign", within_lock,
                )
                order = permutation4(
                    permit, "evaluation", training.seed, n, lock, within_lock, "probe_order",
                )
                x[local], mu[local], bins[local] = roster.x, roster.mu, roster.bins
                locks[local], within[local] = lock, within_lock
                common_latents[local] = np.broadcast_to(order[:, None], (4, n))
                cut_private_latents[local] = generator(
                    permit, "evaluation", training.seed, n, lock, within_lock, "private_latent_cut",
                ).integers(0, 4, size=(4, n), dtype=np.int64)
                temporal_values = generator(
                    permit, "evaluation", training.seed, n, lock, within_lock, "temporal_latent_cut",
                ).integers(0, 4, size=4, dtype=np.int64)
                temporal_second[local] = np.broadcast_to(temporal_values[:, None], (4, n))
                uniforms[local] = generator(
                    permit, "evaluation", training.seed, n, lock, within_lock, "actor_uniforms",
                ).random((4, 2, n), dtype=np.float64)
                xi_values.append(roster.xi)
                proposals.append(roster.proposal_count)

            for arm in ARMS:
                panel = _panel(
                    training.actors[arm], x, mu, bins, locks,
                    common_latents, common_latents, uniforms,
                )
                _accumulate(
                    accumulators[arm], panel, common_latents, within,
                    training.posteriors[arm], n,
                )
            private_cut = _panel(
                training.actors["RCLE"], x, mu, bins, locks,
                cut_private_latents, cut_private_latents, uniforms,
            )
            temporal_cut = _panel(
                training.actors["RCLE"], x, mu, bins, locks,
                common_latents, temporal_second, uniforms,
            )
            _accumulate(cut_accumulators["PRIVATE-LATENT-CUT"], private_cut, cut_private_latents, within, None, n)
            _accumulate(cut_accumulators["TEMPORAL-LATENT-CUT"], temporal_cut, common_latents, within, None, n)

        cells[str(n)] = {arm: _finalize(accumulators[arm], n) for arm in ARMS}
        cut_cells[str(n)] = {name: _finalize(value, n) for name, value in cut_accumulators.items()}
        xi_array = np.asarray(xi_values, dtype=np.float64)
        roster_stats[str(n)] = {
            "retained_xi_mean": float(xi_array.mean()),
            "retained_xi_std": float(xi_array.std(ddof=0)),
            "retained_xi_min": float(xi_array.min()),
            "retained_xi_max": float(xi_array.max()),
            "accepted_rosters": len(xi_values),
            "proposal_draws": int(sum(proposals)),
            "maximum_proposals_for_one_roster": int(max(proposals)),
        }

    posterior_probabilities = {
        arm: torch.softmax(training.posteriors[arm].logits.detach(), dim=1).cpu().numpy().tolist()
        for arm in ARMS
    }
    return {
        "seed": training.seed,
        "cells": cells,
        "cuts": cut_cells,
        "roster_statistics": roster_stats,
        "posterior_probabilities": posterior_probabilities,
        "ordinary_episodes": len(ARMS) * len(EVAL_SIZES)
        * REGISTERED.eval_campaigns_per_size * 4,
        "cut_episodes": 2 * len(EVAL_SIZES) * REGISTERED.eval_campaigns_per_size * 4,
        "frozen_checkpoint": "immediately_after_update_2000",
        "evaluation_updates": 0,
        "selected_latents": False,
        "greedy_decoding": False,
        "semantic_diagnostics_arm_scoped": True,
    }
