"""Frozen calibration and conclusion training loops."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path

import numpy as np
import torch

from .actor import Actor
from .config import (
    CALIBRATION_UPDATES, CHECKPOINTS, ENTROPY_COEFFICIENT, FINAL_UPDATES,
    GRAD_CLIP, LOADS, ORDERED_PAIRS, TRAIN_SIZES, VALIDATION_TAPES,
    REVISION, STOCHASTIC_NAMESPACE, HyperParameters, demand,
)
from .decoder import decode
from .environment import canonical_roles, canonicalize_task_values, reward
from .rng import generator, tapes_for_decisions


@dataclass
class FitResult:
    parameters: np.ndarray
    validation: dict[int, float]
    gradient_norm_max: float


_ACTIVITY_MARKED = False


def _mark_registered_activity() -> None:
    global _ACTIVITY_MARKED
    if _ACTIVITY_MARKED:
        return
    marker = os.environ.get("MGTAP_ACTIVITY_MARKER")
    if marker:
        path = Path(marker)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps({
            "revision": REVISION,
            "stochastic_namespace": STOCHASTIC_NAMESPACE,
            "scientific_activity_started": True,
            "criterion_observation": "registered stochastic episode order materialized",
        }, separators=(",", ":")) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    _ACTIVITY_MARKED = True


def _features(n: int, demands: np.ndarray, epochs: np.ndarray) -> np.ndarray:
    return np.column_stack((np.ones(len(demands)), demands / float(n), epochs - 1.0))


def _training_group(phase: str, seed: int, update: int, n: int) -> dict[str, np.ndarray]:
    episodes = [(pair, load) for pair in ORDERED_PAIRS for load in LOADS]
    _mark_registered_activity()
    order_rng = generator(f"{phase}_episode_order", seed, update)
    full_order = order_rng.permutation(len(TRAIN_SIZES) * len(episodes))
    indexed = [(nn, pair, load) for nn in TRAIN_SIZES for pair, load in episodes]
    selected = [indexed[i] for i in full_order if indexed[i][0] == n]
    pairs: list[tuple[int, int]] = []
    loads: list[str] = []
    epochs: list[int] = []
    demand_rows: list[tuple[int, int, int, int]] = []
    for _, pair, load in selected:
        for epoch in (1, 2):
            pairs.append(pair)
            loads.append(load)
            epochs.append(epoch)
            demand_rows.append(demand(n, pair, load, epoch))
    batch = len(demand_rows)
    tapes = tapes_for_decisions(phase, seed, (update, n), batch, n, include_training_presentations=True)
    canonical_demands = np.asarray(demand_rows, dtype=np.int16)
    presented_demands = np.take_along_axis(canonical_demands, tapes["task_permutations"], axis=1)
    canonical_demands = canonicalize_task_values(presented_demands, tapes["task_permutations"])
    base_roles = np.broadcast_to(canonical_roles(n), (batch, n)).copy()
    roles = np.take_along_axis(base_roles, tapes["row_permutations"], axis=1)
    priorities = np.take_along_axis(tapes["priority_ranks"], tapes["row_permutations"], axis=1)
    return {
        "features": _features(n, canonical_demands, np.asarray(epochs)),
        "demands": canonical_demands,
        "roles": roles,
        "priorities": priorities,
        "uniforms": tapes["action_uniforms"],
        "pairs": np.asarray(pairs, dtype=np.int8),
        "loads": np.asarray([0 if x == "SLACK" else 1 for x in loads], dtype=np.int8),
        "epochs": np.asarray(epochs, dtype=np.int8),
    }


def _decode_group(actor: Actor, group: dict[str, np.ndarray]):
    features = torch.as_tensor(group["features"], dtype=torch.float64)
    roles = torch.as_tensor(group["roles"], dtype=torch.long)
    demands = torch.as_tensor(group["demands"], dtype=torch.long)
    priorities = torch.as_tensor(group["priorities"], dtype=torch.long)
    uniforms = torch.as_tensor(group["uniforms"], dtype=torch.float64)
    raw, mapped, idle = actor.scores(features)
    decoded = decode(mapped, idle, roles, demands, priorities, uniforms)
    rewards = reward(group["roles"], decoded.actions.detach().cpu().numpy(), decoded.residual.detach().cpu().numpy())
    return raw, mapped, idle, decoded, torch.as_tensor(rewards, dtype=torch.float64)


def validation_value(actor: Actor, calibration_seed: int) -> float:
    episode_rewards: list[np.ndarray] = []
    with torch.no_grad():
        for n in TRAIN_SIZES:
            epoch_rewards: list[np.ndarray] = []
            for pair_index, pair in enumerate(ORDERED_PAIRS):
                for load_index, load in enumerate(LOADS):
                    pair_rewards = []
                    for epoch in (1, 2):
                        demands = np.broadcast_to(np.asarray(demand(n, pair, load, epoch), dtype=np.int16), (VALIDATION_TAPES, 4)).copy()
                        tapes = tapes_for_decisions("validation", calibration_seed, (n, pair_index, load_index, epoch), VALIDATION_TAPES, n)
                        roles = np.broadcast_to(canonical_roles(n), (VALIDATION_TAPES, n)).copy()
                        group = {
                            "features": _features(n, demands, np.full(VALIDATION_TAPES, epoch)),
                            "demands": demands,
                            "roles": roles,
                            "priorities": tapes["priority_ranks"],
                            "uniforms": tapes["action_uniforms"],
                        }
                        _, _, _, _, rewards = _decode_group(actor, group)
                        pair_rewards.append(rewards.numpy())
                    epoch_rewards.append((pair_rewards[0] + pair_rewards[1]) / (2.0 * n))
            episode_rewards.extend(epoch_rewards)
    return float(np.mean(np.concatenate(episode_rewards)))


def fit(
    arm: str,
    binding: str,
    seed: int,
    hyper: HyperParameters,
    *,
    updates: int,
    validate: bool,
    phase: str,
) -> FitResult:
    actor = Actor(arm, binding)
    optimizer = torch.optim.SGD(actor.parameters(), lr=hyper.learning_rate, momentum=0.0)
    validation: dict[int, float] = {}
    max_grad = 0.0
    for update in range(1, updates + 1):
        optimizer.zero_grad(set_to_none=True)
        stochastic = torch.zeros((), dtype=torch.float64)
        for n in TRAIN_SIZES:
            group = _training_group(phase, seed, update, n)
            _, _, _, decoded, rewards = _decode_group(actor, group)
            stochastic = stochastic + torch.sum(-0.5 * (rewards / n) * decoded.log_probability - 0.5 * ENTROPY_COEFFICIENT * decoded.mean_entropy)
        regularizer = hyper.weight_decay * (actor.W.square().sum() + actor.V.square().sum())
        loss = stochastic / 48.0 + regularizer
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(actor.parameters(), GRAD_CLIP))
        max_grad = max(max_grad, grad_norm)
        optimizer.step()
        if validate and update in CHECKPOINTS:
            validation[update] = validation_value(actor, seed)
    return FitResult(actor.parameter_vector(), validation, max_grad)


def calibration_fit(arm: str, binding: str, seed: int, hyper: HyperParameters) -> FitResult:
    return fit(arm, binding, seed, hyper, updates=CALIBRATION_UPDATES, validate=True, phase="calibration_training")


def conclusion_fit(arm: str, binding: str, seed: int, hyper: HyperParameters) -> FitResult:
    return fit(arm, binding, seed, hyper, updates=FINAL_UPDATES, validate=False, phase="conclusion_training")
