"""PPO training and registered evaluation for VNFC-B1."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import copy
import gzip
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Iterable, Mapping, Sequence

import numpy as np
import torch

from .host import (
    CAPACITY_NORMALIZED, CHURN_SCHEDULES, REGIMES, TRUE_EXPANSION, World,
    allocation_metrics, changed_set_stratum, churn_world, counter_seed, row_order,
    static_pair, training_world, validation_world,
)
from .models import (
    A_JOINT, A_MASS, B_REBIND, G_MEAN, GREEDY_ORACLE, JOINT_ARMS,
    LEARNED_ARMS, Observation, SetActorCritic, action_logprob_entropy,
    assignments_for_n, assignment_tensor, coverage_scores, exact_best_response,
    greedy_action, joint_scores, keep_scores, make_observation, sample_action,
)


TRAIN_UPDATES = 32
EPISODES_PER_UPDATE = 128
PPO_EPOCHS = 4
MINIBATCH_ROWS = 192
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_COEFFICIENT = 0.5
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.5
LEARNING_RATE = 3e-4
BASE_SEEDS = (1103, 1129, 1151, 1171, 1193, 1213, 1237, 1277)


@dataclass
class Transition:
    observation: Observation
    action: torch.Tensor
    old_logprob: float
    old_value: float
    reward: float
    episode: int
    segment: int
    decoder_base: torch.Tensor | None
    advantage: float = 0.0
    target_return: float = 0.0


def _torch_generator(*parts: object) -> torch.Generator:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(counter_seed(*parts))
    return generator


def _initialize_model(arm: str, base_seed: int) -> SetActorCritic:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(counter_seed(base_seed, arm, "model_initialization"))
        return SetActorCritic(arm)


def _training_order(world: World, segment: int, arm: str) -> tuple[int, ...]:
    roster = list(world.rosters[segment])
    generator = np.random.default_rng(counter_seed(
        world.base_seed, world.split, world.world_index, world.regime,
        segment, "training_row_permutation",
    ))
    generator.shuffle(roster)
    return tuple(roster)


def _decoder_base(arm: str, observation: Observation) -> torch.Tensor | None:
    if arm not in JOINT_ARMS:
        return None
    assignments = assignments_for_n(observation.n)
    base = coverage_scores(observation, assignments)
    if arm == B_REBIND and observation.segment > 0:
        base = base + 0.04 * keep_scores(observation, assignments)
    return base.detach()


def _collect_rollout(
    model: SetActorCritic, arm: str, base_seed: int, update: int,
) -> tuple[list[Transition], dict[str, float]]:
    transitions: list[Transition] = []
    episode_returns: list[float] = []
    action_generator = _torch_generator(base_seed, arm, update, "action_sampling")
    first_episode = update * EPISODES_PER_UPDATE
    model.eval()
    for local_episode in range(EPISODES_PER_UPDATE):
        episode_index = first_episode + local_episode
        world = training_world(base_seed, episode_index)
        previous: dict[int, int] | None = None
        episode_rewards: list[float] = []
        for segment in range(3):
            order = _training_order(world, segment, arm)
            observation = make_observation(world, segment, order, previous)
            with torch.no_grad():
                logits, value = model(observation)
                action, logprob, _ = sample_action(arm, observation, logits, action_generator)
            allocation = {
                handle: int(action[index]) for index, handle in enumerate(observation.handles)
            }
            metrics = allocation_metrics(
                world.rosters[segment], world.capacities(segment), world.demands,
                allocation, previous,
            )
            reward = float(metrics["reward"])
            transitions.append(Transition(
                observation=observation,
                action=action.detach().clone(),
                old_logprob=float(logprob),
                old_value=float(value),
                reward=reward,
                episode=episode_index,
                segment=segment,
                decoder_base=_decoder_base(arm, observation),
            ))
            episode_rewards.append(reward)
            previous = allocation
        episode_returns.append(statistics.fmean(episode_rewards))

    if len(transitions) != EPISODES_PER_UPDATE * 3:
        raise RuntimeError("rollout row count mismatch")
    for offset in range(0, len(transitions), 3):
        gae = 0.0
        next_value = 0.0
        for segment in reversed(range(3)):
            transition = transitions[offset + segment]
            nonterminal = 0.0 if segment == 2 else 1.0
            delta = transition.reward + GAMMA * next_value * nonterminal - transition.old_value
            gae = delta + GAMMA * GAE_LAMBDA * nonterminal * gae
            transition.advantage = gae
            transition.target_return = gae + transition.old_value
            next_value = transition.old_value
    return transitions, {
        "mean_episode_return": statistics.fmean(episode_returns),
        "mean_segment_reward": statistics.fmean(t.reward for t in transitions),
    }


def _joint_group_statistics(
    arm: str,
    rows: Sequence[Transition],
    logits_rows: Sequence[torch.Tensor],
) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    logprob_by_position: list[torch.Tensor | None] = [None] * len(rows)
    entropy_by_position: list[torch.Tensor | None] = [None] * len(rows)
    groups: dict[int, list[int]] = defaultdict(list)
    for position, row in enumerate(rows):
        groups[row.observation.n].append(position)
    for n, positions in groups.items():
        assignments = assignments_for_n(n)
        assignment_count = assignments.shape[0]
        logits = torch.stack([logits_rows[position] for position in positions])
        expanded_logits = logits[:, None, :, :].expand(-1, assignment_count, -1, -1)
        gather_index = assignments[None, :, :, None].expand(len(positions), -1, -1, 1)
        bid = torch.gather(expanded_logits, 3, gather_index).squeeze(-1).sum(dim=-1) / n
        bases = torch.stack([
            rows[position].decoder_base for position in positions  # type: ignore[arg-type]
        ])
        scores = bid + bases
        log_probabilities = torch.log_softmax(scores, dim=-1)
        probabilities = torch.exp(log_probabilities)
        entropies = -(probabilities * log_probabilities).sum(dim=-1)
        powers = torch.tensor([4 ** power for power in reversed(range(n))], dtype=torch.long)
        selected = torch.stack([rows[position].action for position in positions]).matmul(powers)
        selected_logprob = log_probabilities.gather(1, selected[:, None]).squeeze(1)
        for local, position in enumerate(positions):
            logprob_by_position[position] = selected_logprob[local]
            entropy_by_position[position] = entropies[local]
    if any(value is None for value in logprob_by_position + entropy_by_position):
        raise RuntimeError("joint batch statistics incomplete")
    return (
        [value for value in logprob_by_position if value is not None],
        [value for value in entropy_by_position if value is not None],
    )


def _ppo_minibatch(
    model: SetActorCritic,
    optimizer: torch.optim.Optimizer,
    arm: str,
    rows: Sequence[Transition],
    normalized_advantages: torch.Tensor,
    positions: Sequence[int],
) -> dict[str, float]:
    selected_rows = [rows[position] for position in positions]
    logits_rows: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    for row in selected_rows:
        logits, value = model(row.observation)
        logits_rows.append(logits)
        values.append(value)
    if arm in JOINT_ARMS:
        logprobs, entropies = _joint_group_statistics(arm, selected_rows, logits_rows)
    else:
        logprobs, entropies = [], []
        for row, logits in zip(selected_rows, logits_rows):
            logprob, entropy = action_logprob_entropy(arm, row.observation, logits, row.action)
            logprobs.append(logprob)
            entropies.append(entropy)
    new_logprob = torch.stack(logprobs)
    value_tensor = torch.stack(values)
    entropy_tensor = torch.stack(entropies)
    old_logprob = torch.tensor([row.old_logprob for row in selected_rows], dtype=torch.float32)
    target_return = torch.tensor([row.target_return for row in selected_rows], dtype=torch.float32)
    advantage = normalized_advantages[torch.tensor(positions, dtype=torch.long)]
    ratio = torch.exp(new_logprob - old_logprob)
    policy_loss = -torch.minimum(
        ratio * advantage,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * advantage,
    ).mean()
    value_loss = torch.nn.functional.mse_loss(value_tensor, target_return)
    entropy = entropy_tensor.mean()
    loss = policy_loss + VALUE_COEFFICIENT * value_loss - ENTROPY_COEFFICIENT * entropy
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
    optimizer.step()
    return {
        "loss": float(loss.detach()),
        "policy_loss": float(policy_loss.detach()),
        "value_loss": float(value_loss.detach()),
        "entropy": float(entropy.detach()),
    }


def train_arm(
    arm: str, base_seed: int,
) -> tuple[SetActorCritic, torch.optim.Optimizer, list[dict[str, object]], list[dict[str, torch.Tensor]]]:
    torch.set_num_threads(1)
    model = _initialize_model(arm, base_seed)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LEARNING_RATE, betas=(0.9, 0.999), eps=1e-8,
        weight_decay=0.0,
    )
    curves: list[dict[str, object]] = []
    snapshots: list[dict[str, torch.Tensor]] = []
    started = time.perf_counter()
    optimizer_steps = 0
    for update in range(TRAIN_UPDATES):
        rollout, rollout_summary = _collect_rollout(model, arm, base_seed, update)
        advantages = torch.tensor([row.advantage for row in rollout], dtype=torch.float32)
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
        epoch_losses: list[dict[str, float]] = []
        model.train()
        for epoch in range(PPO_EPOCHS):
            permutation = torch.randperm(
                len(rollout), generator=_torch_generator(
                    base_seed, arm, update, epoch, "minibatch_order"
                ),
            )
            for start in range(0, len(rollout), MINIBATCH_ROWS):
                positions = permutation[start:start + MINIBATCH_ROWS].tolist()
                if len(positions) != MINIBATCH_ROWS:
                    raise RuntimeError("non-full PPO minibatch")
                epoch_losses.append(_ppo_minibatch(
                    model, optimizer, arm, rollout, advantages, positions,
                ))
                optimizer_steps += 1
        elapsed = time.perf_counter() - started
        curves.append({
            "update": update + 1,
            "episodes_completed": (update + 1) * EPISODES_PER_UPDATE,
            "segment_rows_completed": (update + 1) * EPISODES_PER_UPDATE * 3,
            "cumulative_wall_seconds": elapsed,
            **rollout_summary,
            "ppo": {
                key: statistics.fmean(float(row[key]) for row in epoch_losses)
                for key in ("loss", "policy_loss", "value_loss", "entropy")
            },
        })
        snapshots.append({key: value.detach().cpu().clone() for key, value in model.state_dict().items()})
    if optimizer_steps != 256:
        raise RuntimeError(f"optimizer step mismatch: {optimizer_steps}")
    return model, optimizer, curves, snapshots


def save_checkpoint(
    path: Path, model: SetActorCritic, optimizer: torch.optim.Optimizer,
    arm: str, base_seed: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save({
        "schema": "VNFC-B1-PPO-CHECKPOINT-v1",
        "arm": arm,
        "base_seed": base_seed,
        "update": TRAIN_UPDATES,
        "episodes": TRAIN_UPDATES * EPISODES_PER_UPDATE,
        "segment_rows": TRAIN_UPDATES * EPISODES_PER_UPDATE * 3,
        "optimizer_steps": TRAIN_UPDATES * PPO_EPOCHS * 2,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
    }, temporary)
    temporary.replace(path)


def _evaluate_learned_episode(
    model: SetActorCritic, arm: str, world: World, replica: int,
    latency: dict[tuple[str, int], list[float]] | None = None,
    *, compute_access_regret: bool = True,
) -> dict[str, object]:
    previous: dict[int, int] | None = None
    held_allocation: dict[int, int] | None = None
    segments: list[dict[str, object]] = []
    model.eval()
    for segment in range(3):
        query = not world.static or segment == 0
        if query:
            order = row_order(
                world.rosters[segment], world.base_seed, world.split,
                world.world_index, world.regime, segment, replica,
            )
            observation = make_observation(world, segment, order, previous)
            started = time.perf_counter_ns()
            with torch.no_grad():
                logits, _ = model(observation)
                allocation, selected_probability, role_probabilities = greedy_action(
                    arm, observation, logits
                )
            elapsed_us = (time.perf_counter_ns() - started) / 1000.0
            if latency is not None:
                latency[(arm, observation.n)].append(elapsed_us)
            with torch.no_grad():
                selected_tensor = assignment_tensor(observation, allocation)
                joint_logprob, _ = action_logprob_entropy(
                    arm, observation, logits, selected_tensor
                )
            held_allocation = allocation
        else:
            if held_allocation is None:
                raise RuntimeError("static allocation missing")
            allocation = held_allocation
            selected_probability = float(segments[0]["selected_probability"])
            role_probabilities = segments[0]["role_probabilities"]
            joint_logprob = torch.tensor(float(segments[0]["joint_log_probability"]))
        metrics = allocation_metrics(
            world.rosters[segment], world.capacities(segment), world.demands,
            allocation, previous,
        )
        if compute_access_regret:
            _, best_metrics = exact_best_response(world, segment, previous)
        else:
            best_metrics = metrics
        stable_handles = tuple(sorted(world.rosters[segment]))
        segments.append({
            "segment": segment,
            "fleet_size": len(stable_handles),
            "event_kind": world.event_kind(segment),
            "assignment": [allocation[handle] for handle in stable_handles],
            "stable_handles": list(stable_handles),
            "selected_probability": selected_probability,
            "role_probabilities": role_probabilities,
            "joint_log_probability": float(joint_logprob),
            "service": metrics["service"],
            "waste": metrics["waste"],
            "switch": metrics["switch"],
            "reward": metrics["reward"],
            "best_response_reward": best_metrics["reward"],
            "access_regret": float(best_metrics["reward"]) - float(metrics["reward"]),
            "change_stratum": changed_set_stratum(world, segment),
        })
        previous = dict(allocation)
    return {
        "J": statistics.fmean(float(row["reward"]) for row in segments),
        "post_churn_reward": statistics.fmean(float(row["reward"]) for row in segments[1:]),
        "post_churn_access_regret": statistics.fmean(float(row["access_regret"]) for row in segments[1:]),
        "segments": segments,
    }


def _evaluate_oracle_episode(world: World) -> dict[str, object]:
    previous: dict[int, int] | None = None
    held_allocation: dict[int, int] | None = None
    segments: list[dict[str, object]] = []
    for segment in range(3):
        if not world.static or segment == 0:
            allocation, metrics = exact_best_response(world, segment, previous)
            held_allocation = allocation
        else:
            if held_allocation is None:
                raise RuntimeError("static oracle allocation missing")
            allocation = held_allocation
            metrics = allocation_metrics(
                world.rosters[segment], world.capacities(segment), world.demands,
                allocation, previous,
            )
        stable_handles = tuple(sorted(world.rosters[segment]))
        segments.append({
            "segment": segment,
            "fleet_size": len(stable_handles),
            "event_kind": world.event_kind(segment),
            "assignment": [allocation[handle] for handle in stable_handles],
            "stable_handles": list(stable_handles),
            "selected_probability": 1.0,
            "role_probabilities": [],
            "joint_log_probability": 0.0,
            "service": metrics["service"],
            "waste": metrics["waste"],
            "switch": metrics["switch"],
            "reward": metrics["reward"],
            "best_response_reward": metrics["reward"],
            "access_regret": 0.0,
            "change_stratum": changed_set_stratum(world, segment),
        })
        previous = allocation
    return {
        "J": statistics.fmean(float(row["reward"]) for row in segments),
        "post_churn_reward": statistics.fmean(float(row["reward"]) for row in segments[1:]),
        "post_churn_access_regret": 0.0,
        "segments": segments,
    }


def _replica_deviations(replicas: Sequence[Mapping[str, object]]) -> dict[str, float | int]:
    probability = 0.0
    reward = 0.0
    assignment_disagreements = 0
    probability_tolerance_violations = 0
    reward_tolerance_violations = 0
    reference = replicas[0]["segments"]
    for replica in replicas[1:]:
        for left, right in zip(reference, replica["segments"]):  # type: ignore[arg-type]
            probability = max(
                probability,
                abs(float(left["selected_probability"]) - float(right["selected_probability"])),
            )
            probability_tolerance_violations += int(not math.isclose(
                float(left["selected_probability"]), float(right["selected_probability"]),
                rel_tol=1e-5, abs_tol=1e-6,
            ))
            left_probs = np.asarray(left["role_probabilities"], dtype=float)
            right_probs = np.asarray(right["role_probabilities"], dtype=float)
            if left_probs.size and right_probs.size:
                probability = max(probability, float(np.max(np.abs(left_probs - right_probs))))
                probability_tolerance_violations += int(np.count_nonzero(
                    ~np.isclose(left_probs, right_probs, rtol=1e-5, atol=1e-6)
                ))
            reward = max(reward, abs(float(left["reward"]) - float(right["reward"])))
            reward_tolerance_violations += int(not math.isclose(
                float(left["reward"]), float(right["reward"]),
                rel_tol=1e-5, abs_tol=1e-6,
            ))
            assignment_disagreements += int(left["assignment"] != right["assignment"])
    return {
        "max_probability_difference": probability,
        "max_reward_difference": reward,
        "assignment_disagreements": assignment_disagreements,
        "probability_tolerance_violations": probability_tolerance_violations,
        "reward_tolerance_violations": reward_tolerance_violations,
    }


def _world_descriptors(base_seed: int) -> Iterable[tuple[str, str, World, int | None]]:
    for regime in REGIMES:
        for pair_index in range(48):
            world4, world6 = static_pair(base_seed, regime, pair_index)
            yield "static", f"static:{regime}:{pair_index}:N4", world4, pair_index
            yield "static", f"static:{regime}:{pair_index}:N6", world6, pair_index
        for sequence_index in range(len(CHURN_SCHEDULES)):
            for world_index in range(24):
                world = churn_world(base_seed, regime, sequence_index, world_index)
                yield "churn", f"churn:{regime}:{sequence_index}:{world_index}", world, None


def evaluate_models(
    models: Mapping[str, SetActorCritic], base_seed: int,
    raw_rows_path: Path | None,
    *, include_oracle: bool = True,
) -> dict[str, object]:
    arms = (*LEARNED_ARMS, *((GREEDY_ORACLE,) if include_oracle else ()))
    values: dict[str, dict[str, list[float]]] = {
        arm: defaultdict(list) for arm in arms
    }
    cell_values: dict[str, dict[str, list[float]]] = {
        arm: defaultdict(list) for arm in arms
    }
    strata: dict[str, dict[str, list[float]]] = {
        arm: defaultdict(list) for arm in arms
    }
    nested: dict[str, dict[tuple[str, int], dict[int, float]]] = {
        arm: defaultdict(dict) for arm in arms
    }
    latency: dict[tuple[str, int], list[float]] = defaultdict(list)
    permutation_max = {
        arm: {"max_probability_difference": 0.0, "max_reward_difference": 0.0,
              "assignment_disagreements": 0, "probability_tolerance_violations": 0,
              "reward_tolerance_violations": 0}
        for arm in arms
    }
    raw_stream = None
    if raw_rows_path is not None:
        raw_rows_path.parent.mkdir(parents=True, exist_ok=True)
        raw_stream = gzip.open(raw_rows_path, "wt", encoding="utf-8", newline="\n")
    try:
        for panel, world_key, world, pair_index in _world_descriptors(base_seed):
            for arm in arms:
                if arm == GREEDY_ORACLE:
                    replicas = [_evaluate_oracle_episode(world) for _ in range(4)]
                else:
                    replicas = [
                        _evaluate_learned_episode(models[arm], arm, world, replica, latency)
                        for replica in range(4)
                    ]
                deviation = _replica_deviations(replicas)
                for key in permutation_max[arm]:
                    if key in {
                        "assignment_disagreements", "probability_tolerance_violations",
                        "reward_tolerance_violations",
                    }:
                        permutation_max[arm][key] += int(deviation[key])
                    else:
                        permutation_max[arm][key] = max(
                            float(permutation_max[arm][key]), float(deviation[key])
                        )
                mean_j = statistics.fmean(float(replica["J"]) for replica in replicas)
                mean_h = statistics.fmean(float(replica["post_churn_reward"]) for replica in replicas)
                mean_gap = statistics.fmean(float(replica["post_churn_access_regret"]) for replica in replicas)
                values[arm]["all_J"].append(mean_j)
                if panel == "static":
                    cell_values[arm][f"static:{world.regime}:N{world.sequence[0]}"] .append(mean_j)
                    if world.regime == TRUE_EXPANSION:
                        values[arm]["P"].append(mean_j)
                    if pair_index is not None:
                        nested[arm][(world.regime, pair_index)][world.sequence[0]] = mean_j
                else:
                    values[arm]["H"].append(mean_h)
                    values[arm]["Ogap"].append(mean_gap)
                    sequence_text = "->".join(str(value) for value in world.sequence)
                    cell_values[arm][f"churn:{world.regime}:{sequence_text}"].append(mean_h)
                    for segment in (1, 2):
                        stratum = str(replicas[0]["segments"][segment]["change_stratum"])
                        strata[arm][stratum].append(statistics.fmean(
                            float(replica["segments"][segment]["reward"]) for replica in replicas
                        ))
                if raw_stream is not None:
                    raw_stream.write(json.dumps({
                        "base_seed": base_seed,
                        "world_key": world_key,
                        "panel": panel,
                        "regime": world.regime,
                        "sequence": list(world.sequence),
                        "demands": list(world.demands),
                        "arm": arm,
                        "replicas": replicas,
                        "replica_deviations": deviation,
                    }, separators=(",", ":")) + "\n")
    finally:
        if raw_stream is not None:
            raw_stream.close()

    arm_summaries: dict[str, object] = {}
    for arm in arms:
        expansion = [
            by_n[6] - by_n[4]
            for (regime, _), by_n in nested[arm].items()
            if regime == TRUE_EXPANSION
        ]
        normalized = [
            by_n[6] - by_n[4]
            for (regime, _), by_n in nested[arm].items()
            if regime == CAPACITY_NORMALIZED
        ]
        arm_summaries[arm] = {
            "P": statistics.fmean(values[arm]["P"]),
            "H": statistics.fmean(values[arm]["H"]),
            "Ogap": statistics.fmean(values[arm]["Ogap"]),
            "X": statistics.fmean(expansion),
            "capacity_normalized_N6_minus_N4": statistics.fmean(normalized),
            "cells": {
                key: statistics.fmean(rows) for key, rows in sorted(cell_values[arm].items())
            },
            "change_strata": {
                key: statistics.fmean(rows) for key, rows in sorted(strata[arm].items())
            },
            "permutation": permutation_max[arm],
        }
    latency_summary = {
        arm: {
            str(n): {
                "events": len(rows),
                "p50_microseconds": float(np.percentile(rows, 50)),
                "p95_microseconds": float(np.percentile(rows, 95)),
            }
            for (key_arm, n), rows in sorted(latency.items()) if key_arm == arm
        }
        for arm in LEARNED_ARMS
    }
    return {
        "base_seed": base_seed,
        "arms": arm_summaries,
        "inference_latency": latency_summary,
        "base_episode_count": 480,
        "replicated_episode_count_per_arm": 1920,
        "raw_rows": str(raw_rows_path) if raw_rows_path is not None else None,
    }


def evaluate_validation(model: SetActorCritic, arm: str, base_seed: int) -> dict[str, float | int]:
    returns: list[float] = []
    for index in range(192):
        episode = _evaluate_learned_episode(
            model, arm, validation_world(base_seed, index), replica=2,
            compute_access_regret=False,
        )
        returns.append(float(episode["J"]))
    return {"episodes": 192, "mean_J": statistics.fmean(returns)}


def peak_process_rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def clone_model(arm: str, base_seed: int, state: Mapping[str, torch.Tensor]) -> SetActorCritic:
    model = _initialize_model(arm, base_seed)
    model.load_state_dict(state)
    model.eval()
    return model
