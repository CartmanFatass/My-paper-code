"""Registered stopped score-function learning and learned rollouts."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Mapping

import torch

from . import rng
from .config import CLAIM_PERIOD, EVENT_TICK, HORIZON, TRAIN_CELLS
from .host import (
    construct_public_state, endpoints, fragmentation, initial_entities,
    move_once, mutate_entities, unserved,
)
from .models import PCPVPolicy, inverse_cdf_action


def normal_log_density(value: torch.Tensor, mean: torch.Tensor,
                       log_scale: torch.Tensor) -> torch.Tensor:
    stopped = value.detach()
    standardized = (stopped - mean) / torch.exp(log_scale)
    return (-0.5 * standardized.square() - log_scale
            - 0.5 * math.log(2.0 * math.pi)).sum()


def draw_plan(policy: PCPVPolicy, summary: torch.Tensor, root: int,
              phase: str, cell: tuple[int, int], scenario: int,
              update: int | None) -> tuple[torch.Tensor, torch.Tensor]:
    mean, log_scale = policy.manager(summary)
    label = rng.root_label(root)
    fields = (label, "common", phase, "cell", *cell,
              "update", update if update is not None else "evaluation",
              "scenario", scenario, "manager-plan")
    noise = torch.tensor([rng.normal(*fields, "coordinate", coordinate)
                          for coordinate in range(4)], dtype=torch.float64)
    plan = (mean + torch.exp(log_scale) * noise).detach()
    return plan, normal_log_density(plan, mean, log_scale)


def rollout(
    policy: PCPVPolicy,
    arm: str,
    root: int,
    cell: tuple[int, int],
    scenario: int,
    phase: str,
    update: int | None = None,
    clamp: bool = False,
) -> tuple[dict[str, float], torch.Tensor]:
    """Run one complete retained episode and return endpoints and score mean."""
    churn = cell[0] != cell[1]
    global_scenario = scenario if update is None else update * 8 + scenario
    entities = initial_entities(root, cell, global_scenario, phase)
    initial = construct_public_state(entities, 0, churn, root, cell,
                                     global_scenario, phase)
    initial_summary = policy.public_summary(initial)
    common_plan, plan_score = draw_plan(policy, initial_summary, root, phase,
                                        cell, global_scenario, update)
    plans: dict[int, torch.Tensor] = {key: common_plan for key in entities}
    action_scores: list[torch.Tensor] = []
    u_values: list[float] = []
    f_values: list[float] = []
    claims: dict[int, int] = {}
    label = rng.root_label(root)

    for tick in range(HORIZON):
        if tick % CLAIM_PERIOD == 0:
            if tick == EVENT_TICK and churn:
                survivors = set(entities)
                mutate_entities(entities, cell[1], root, cell, global_scenario,
                                phase)
                for key in list(plans):
                    if key not in entities:
                        del plans[key]
                for key in entities:
                    if key not in plans:
                        plans[key] = common_plan
            state = construct_public_state(entities, tick, churn, root, cell,
                                           global_scenario, phase)
            summary = policy.public_summary(state)
            if arm == "FLEX" and churn and tick == EVENT_TICK:
                updated = {}
                for key in state.angular_order:
                    noise = torch.tensor([
                        rng.normal(label, "arm-only", "FLEX", phase, "cell",
                                   *cell, "update",
                                   update if update is not None else "evaluation",
                                   "scenario", global_scenario, "tick", tick,
                                   "entity", key, "event-noise", "coordinate", c)
                        for c in range(4)
                    ], dtype=torch.float64)
                    own = torch.as_tensor(state.own_features(key),
                                          dtype=torch.float64)
                    updated[key] = policy.event_plan(summary, own, plans[key],
                                                     noise, clamp=clamp)
                plans = updated
            claims = {}
            for key in state.angular_order:
                logits = policy.action_logits(state, key, summary, plans[key])
                log_probs = torch.log_softmax(logits, dim=-1)
                probs = torch.softmax(logits, dim=-1)
                action_u = rng.uniform(
                    label, "common", phase, "cell", *cell, "update",
                    update if update is not None else "evaluation",
                    "scenario", global_scenario, "tick", tick, "entity", key,
                    "action-draw")
                action = inverse_cdf_action(probs, action_u)
                claims[key] = action
                action_scores.append(log_probs[action])
            if tick >= EVENT_TICK:
                f_values.append(fragmentation(claims, len(entities), tick))
            for key, entity in entities.items():
                entity.previous_claim = claims[key]
                entity.newcomer = False
        move_once(entities, claims, tick)
        u_values.append(unserved(entities, tick))

    action_score = torch.stack(action_scores).mean()
    return endpoints(u_values, f_values), plan_score + action_score


def normalized_sgd_step(policy: PCPVPolicy, loss: torch.Tensor) -> float:
    """Apply the literal whole-tensor normalized SGD update."""
    for parameter in policy.parameters():
        parameter.grad = None
    loss.backward()
    square_norm = torch.zeros((), dtype=torch.float64)
    for parameter in policy.parameters():
        if parameter.grad is not None:
            square_norm += parameter.grad.detach().square().sum()
    raw_norm = float(torch.sqrt(square_norm))
    if not math.isfinite(raw_norm):
        raise FloatingPointError("nonfinite whole-tensor raw gradient norm")
    if raw_norm == 0.0:
        return 0.0
    scale = 0.01 * 0.05 / raw_norm
    with torch.no_grad():
        for parameter in policy.parameters():
            if parameter.grad is not None:
                parameter.add_(parameter.grad, alpha=-scale)
    return 0.0005


def train_arm(policy: PCPVPolicy, arm: str, root: int, deadline=None, *,
              rollout_fn=None, step_fn=None,
              baseline_update_fn=None, update_blocks: int = 256) -> dict[str, object]:
    """Train an arm; injectable functions/count are non-result fixture seams."""
    if rollout_fn is None:
        rollout_fn = rollout
    if step_fn is None:
        step_fn = normalized_sgd_step
    if baseline_update_fn is None:
        baseline_update_fn = lambda old, mean: 0.95 * old + 0.05 * mean
    if update_blocks < 1 or update_blocks > 256:
        raise ValueError("fixture update_blocks must be in [1,256]")
    baselines = {cell: 0.0 for cell in TRAIN_CELLS}
    nonzero_updates = 0
    max_update_error = 0.0
    cell_returns: dict[tuple[int, int], list[float]] = defaultdict(list)
    for update in range(update_blocks):
        if deadline is not None:
            deadline.check()
        scores = []
        advantages = []
        batch_returns: dict[tuple[int, int], list[float]] = defaultdict(list)
        for cell in TRAIN_CELLS:
            for scenario in range(8):
                result, score = rollout_fn(policy, arm, root, cell, scenario,
                                           "stage-b-train", update=update)
                scores.append(score)
                advantages.append(result["Y"] - baselines[cell])
                batch_returns[cell].append(result["Y"])
                cell_returns[cell].append(result["Y"])
        loss = -torch.stack([
            score * torch.tensor(advantage, dtype=torch.float64)
            for score, advantage in zip(scores, advantages)
        ]).mean()
        update_norm = step_fn(policy, loss)
        nonzero_updates += int(update_norm != 0.0)
        if update_norm:
            max_update_error = max(max_update_error, abs(update_norm - 0.0005))
        # Registered order: baselines change only after the joint update.
        for cell in TRAIN_CELLS:
            mean_return = sum(batch_returns[cell]) / 8.0
            baselines[cell] = baseline_update_fn(baselines[cell], mean_return)
    return {
        "updates": update_blocks,
        "episodes": update_blocks * 32,
        "nonzero_updates": nonzero_updates,
        "maximum_nonzero_update_norm_error": max_update_error,
        "final_baselines": {f"{a}->{b}": baselines[(a, b)]
                            for a, b in TRAIN_CELLS},
        "mean_returns": {f"{a}->{b}": sum(cell_returns[(a, b)]) /
                         len(cell_returns[(a, b)]) for a, b in TRAIN_CELLS},
    }
