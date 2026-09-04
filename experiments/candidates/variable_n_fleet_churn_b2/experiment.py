"""Recurrent PPO and paired evaluation for VNFC-B2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import copy
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Mapping, Sequence

import numpy as np
import torch

from .config import (
    BASE_SEEDS, C0, C1, C2, C3, EVENT_CELLS, LEARNED_ARMS, ORACLE,
    PRODUCTION_CONFIG, RAW, RESET, SEEN_SCHEDULES, TYPED, Config,
)
from .host import (
    IDLE, PROBE_ENTITY, PROBE_ROLE, SERVE_0, SERVE_1, World,
    counter_seed, make_world, oracle_actions, row_order, shared_reward,
)
from .lifecycle import Authority, LifecycleRegistry
from .models import ACTION_COUNT, ROW_WIDTH, RecurrentSetActorCritic, initialize_model


@dataclass
class EventTransition:
    rows: torch.Tensor
    actor_hidden: torch.Tensor
    critic_hidden: torch.Tensor
    actions: torch.Tensor
    old_logprobs: torch.Tensor
    old_value: float
    reward: float
    episode: int
    tick: int
    advantage: float = 0.0
    target_return: float = 0.0


def _key(authority: Authority) -> tuple[str, int]:
    return authority.entity, authority.owner_generation


def _initial_registry(world: World) -> LifecycleRegistry:
    registry = LifecycleRegistry()
    for authority in world.initial:
        registry.bind(authority)
    return registry


def _relation(world: World, tick: int, authority: Authority) -> tuple[float, ...]:
    return world.event(tick, authority).numerical()


def _row_features(
    world: World, tick: int, authority: Authority, n: int,
    registry: LifecycleRegistry, arm: str,
    cue: tuple[float, float, float, float],
) -> list[float]:
    capsule = registry.exposed(authority) if arm != RAW else (0.0, 0.0, 0.0, 0.0)
    phase = world.public_phase(authority.role, tick)
    row = [
        float(authority.role == 0), float(authority.role == 1), n / 5.0,
        float(phase == 0), float(phase == 1),
        world.energy_cost(authority, tick) / .03, tick / 11.0,
        *cue, *capsule, *_relation(world, tick, authority),
    ]
    if len(row) != ROW_WIDTH:
        raise RuntimeError(f"feature width {len(row)} != {ROW_WIDTH}")
    return row


def _apply_return_transition(
    world: World, arm: str, registry: LifecycleRegistry,
    hidden: dict[tuple[str, int], torch.Tensor], tick: int,
) -> None:
    if world.cell == C0 or tick != world.return_tick:
        return
    before = world.focal
    after = world.returned_authority()
    if arm == TYPED:
        registry.transition(before, after, world.cell)
        hidden[_key(after)] = torch.zeros(64)
    elif arm == RESET:
        registry.clear_both(before)
        registry.bind(after)
        hidden[_key(after)] = torch.zeros(64)
    else:
        if world.cell == C3:
            hidden.pop(_key(before), None)
            hidden[_key(after)] = torch.zeros(64)


def _cue_for(
    world: World, tick: int, authority: Authority,
    pending: Mapping[tuple[str, int], tuple[int | None, int | None]],
) -> tuple[float, float, float, float]:
    entity: int | None = None
    role: int | None = None
    probe_entity, probe_role = pending.get(_key(authority), (None, None))
    if probe_entity is not None:
        entity = probe_entity
    if probe_role is not None:
        role = probe_role
    return (
        float(entity is not None), float(entity or 0),
        float(role is not None), float(role or 0),
    )


def _store_valid_cues(
    registry: LifecycleRegistry, authority: Authority,
    cue: tuple[float, float, float, float], arm: str,
) -> None:
    if arm == RAW:
        return
    if cue[0]:
        registry.observe_entity(authority, int(cue[1]))
    if cue[2]:
        registry.observe_role(authority, int(cue[3]))


def run_episode(
    model: RecurrentSetActorCritic | None, arm: str, world: World, replica: int,
    generator: torch.Generator | None, *, greedy: bool,
    collect_transitions: bool,
    latency: dict[tuple[str, int], list[float]] | None = None,
) -> tuple[dict[str, object], list[EventTransition]]:
    registry = _initial_registry(world)
    hidden: dict[tuple[str, int], torch.Tensor] = {
        _key(authority): torch.zeros(64) for authority in world.initial
    }
    critic_hidden = torch.zeros(64)
    pending: dict[tuple[str, int], tuple[int | None, int | None]] = {}
    transitions: list[EventTransition] = []
    tick_rows: list[dict[str, object]] = []
    hard_errors = defaultdict(int)
    stale_eligible = stale_selected = 0
    old_entity = world.entity_fact(world.focal)
    old_role = world.lease_fact(world.focal)
    focal_key_after = _key(world.returned_authority())
    role_cue_emitted: set[tuple[str, int, int, int]] = set()
    entity_cue_emitted: set[tuple[str, int]] = set()
    previous_active_keys = {_key(authority) for authority in world.initial}

    for tick in range(12):
        departing_event = None
        if world.cell != C0 and tick == world.leave_tick:
            departing_event = world.departing_event().numerical()
        if arm == RESET and world.cell != C0 and tick == world.leave_tick:
            registry.clear_both(world.focal)
        _apply_return_transition(world, arm, registry, hidden, tick)
        active = world.active(tick)
        active_keys = {_key(authority) for authority in active}
        if tick > 0 and active_keys != previous_active_keys:
            critic_hidden = torch.zeros(64)
        previous_active_keys = active_keys
        order = row_order(active, world, tick, replica)
        cues = {}
        for authority in order:
            cue = list(_cue_for(world, tick, authority, pending))
            entity_key = _key(authority)
            if entity_key not in entity_cue_emitted and (
                tick == 0 or (world.cell == C3 and tick == world.return_tick
                              and authority == world.returned_authority())
            ):
                cue[0] = 1.0
                cue[1] = float(world.entity_fact(authority))
                entity_cue_emitted.add(entity_key)
            lease_key = (
                authority.entity, authority.owner_generation,
                authority.role, authority.lease_generation,
            )
            if lease_key not in role_cue_emitted and (
                tick == 1 or (tick == world.return_tick and authority == world.returned_authority())
            ):
                cue[2] = 1.0
                cue[3] = float(world.lease_fact(authority))
                role_cue_emitted.add(lease_key)
            cues[authority] = tuple(cue)
        for authority in order:
            _store_valid_cues(registry, authority, cues[authority], arm)
        pending = {}
        rows = torch.tensor([
            _row_features(world, tick, authority, len(order), registry, arm, cues[authority])
            for authority in order
        ], dtype=torch.float32)
        before_hidden = torch.stack([
            hidden.setdefault(_key(authority), torch.zeros(64)) for authority in order
        ])
        before_critic = critic_hidden.clone()
        if arm == ORACLE:
            action_map = oracle_actions(world, tick, order) if tick >= 2 else {a: IDLE for a in order}
            actions = torch.tensor([action_map[authority] for authority in order], dtype=torch.long)
            logprobs = torch.zeros(len(order))
            value = torch.tensor(0.0)
            probabilities = torch.nn.functional.one_hot(actions, ACTION_COUNT).to(torch.float32)
        else:
            if model is None:
                raise RuntimeError("learned arm requires model")
            inference_started = time.perf_counter_ns()
            output = model.step(rows, before_hidden, before_critic)
            distribution = torch.distributions.Categorical(logits=output.logits)
            if greedy:
                actions = torch.argmax(output.logits, dim=-1)
            else:
                if generator is None:
                    raise RuntimeError("sampling generator missing")
                probabilities = torch.softmax(output.logits, dim=-1)
                actions = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
            inference_us = (time.perf_counter_ns() - inference_started) / 1000.0
            if latency is not None:
                latency[(arm, len(order))].append(inference_us)
            logprobs = distribution.log_prob(actions)
            probabilities = torch.softmax(output.logits, dim=-1)
            value = output.value
            for index, authority in enumerate(order):
                hidden[_key(authority)] = output.actor_hidden[index].detach()
            critic_hidden = output.critic_hidden.detach()
            action_map = {authority: int(actions[index]) for index, authority in enumerate(order)}

        for authority, action in action_map.items():
            if action == PROBE_ENTITY:
                pending[_key(authority)] = (world.entity_fact(authority), None)
            elif action == PROBE_ROLE:
                pending[_key(authority)] = (None, world.lease_fact(authority))
        observed = shared_reward(world, tick, order, action_map) if tick >= 2 else {
            "reward": 0.0, "correct": [0, 0], "wrong": 0,
            "duplicate": 0, "probe": 0, "correct_command": {},
        }
        oracle_map = oracle_actions(world, tick, order) if tick >= 2 else {a: IDLE for a in order}
        oracle_observed = shared_reward(world, tick, order, oracle_map) if tick >= 2 else {"reward": 0.0}
        stale_here_eligible = stale_here_selected = 0
        focal_correct_service = 0
        focal_active = next((authority for authority in order if _key(authority) == focal_key_after), None)
        if tick >= 2 and focal_active is not None:
            command = world.entity_fact(focal_active) ^ world.lease_fact(focal_active) ^ world.public_phase(focal_active.role, tick)
            focal_correct_service = int(action_map[focal_active] == SERVE_0 + command)
        if world.cell in (C2, C3) and tick >= world.return_tick:
            returned = next((authority for authority in order if _key(authority) == focal_key_after), None)
            if returned is not None:
                old_command = old_entity ^ old_role ^ world.public_phase(returned.role, tick)
                current_command = world.entity_fact(returned) ^ world.lease_fact(returned) ^ world.public_phase(returned.role, tick)
                if (
                    old_command != current_command
                    and action_map[returned] in (SERVE_0, SERVE_1)
                ):
                    stale_here_eligible = 1
                    stale_here_selected = int(action_map[returned] == SERVE_0 + old_command)
                    stale_eligible += 1
                    stale_selected += stale_here_selected
        for name, count in registry.hard_stale_errors(list(active)).items():
            hard_errors[name] += count
        tick_rows.append({
            "tick": tick, "active_n": len(order), "reward": float(observed["reward"]),
            "oracle_reward": float(oracle_observed["reward"]),
            "wrong": observed["wrong"], "duplicate": observed["duplicate"],
            "probe": observed["probe"], "correct": observed["correct"],
            "physical_rows_stable_registry_order": [
                {
                    "role": authority.role,
                    "action": int(action_map[authority]),
                    "probabilities": probabilities[index].detach().cpu().tolist(),
                }
                for index, authority in sorted(
                    enumerate(order), key=lambda item: _key(item[1])
                )
            ],
            "stale_command_eligible": stale_here_eligible,
            "stale_command_selected": stale_here_selected,
            "focal_correct_service": focal_correct_service,
            "departing_focal_lifecycle_event": departing_event,
        })
        if collect_transitions:
            transitions.append(EventTransition(
                rows=rows, actor_hidden=before_hidden, critic_hidden=before_critic,
                actions=actions.detach().clone(), old_logprobs=logprobs.detach().clone(),
                old_value=float(value.detach()), reward=float(observed["reward"]),
                episode=world.world_index, tick=tick,
            ))

    service = tick_rows[2:]
    checkpoint = world.leave_tick if world.cell == C0 else world.return_tick
    recovery = [row for row in tick_rows if checkpoint <= int(row["tick"]) < checkpoint + 3 and int(row["tick"]) >= 2]
    correct_delays = [
        int(row["tick"]) - checkpoint for row in tick_rows
        if int(row["tick"]) >= checkpoint and int(row["focal_correct_service"]) == 1
    ]
    result = {
        "J": statistics.fmean(float(row["reward"]) for row in service),
        "RR3": sum(float(row["oracle_reward"]) - float(row["reward"]) for row in recovery),
        "hard_stale_errors": dict(hard_errors),
        "stale_command_eligible": stale_eligible,
        "stale_command_selected": stale_selected,
        "probe_count": sum(int(row["probe"]) for row in service),
        "wrong_count": sum(int(row["wrong"]) for row in service),
        "duplicate_count": sum(int(row["duplicate"]) for row in service),
        "coverage_by_role": [sum(int(row["correct"][role]) > 0 for row in service) for role in (0, 1)],
        "time_to_first_correct_post_return": min(correct_delays) if correct_delays else 12 - checkpoint,
        "ticks": tick_rows,
    }
    return result, transitions


def _training_spec(base_seed: int, episode: int) -> tuple[int, str, str]:
    block, offset = divmod(episode, 16)
    cells = [(n, cell, schedule) for n in (3, 4) for cell in EVENT_CELLS for schedule in SEEN_SCHEDULES]
    order = np.random.default_rng(counter_seed(base_seed, block, "training_cell_order")).permutation(16)
    return cells[int(order[offset])]


def _assign_gae(events: list[EventTransition], config: Config) -> None:
    if len(events) != 12:
        raise RuntimeError("VNFC-B2 episode must contain twelve event transitions")
    gae = 0.0
    next_value = 0.0
    for event in reversed(events):
        nonterminal = float(event.tick != 11)
        delta = event.reward + config.gamma * next_value * nonterminal - event.old_value
        gae = delta + config.gamma * config.gae_lambda * nonterminal * gae
        event.advantage = gae
        event.target_return = gae + event.old_value
        next_value = event.old_value


def collect_rollout(
    model: RecurrentSetActorCritic, arm: str, base_seed: int, update: int,
    config: Config,
) -> tuple[list[EventTransition], dict[str, float]]:
    model.eval()
    transitions: list[EventTransition] = []
    returns: list[float] = []
    first_episode = update * config.episodes_per_update
    with torch.no_grad():
        for local in range(config.episodes_per_update):
            episode = first_episode + local
            n, cell, schedule = _training_spec(base_seed, episode)
            world = make_world(base_seed, "train", episode, n, cell, schedule)
            generator = torch.Generator(device="cpu")
            generator.manual_seed(counter_seed(base_seed, arm, episode, "training_action"))
            result, rows = run_episode(
                model, arm, world, replica=2, generator=generator,
                greedy=False, collect_transitions=True,
            )
            _assign_gae(rows, config)
            transitions.extend(rows)
            returns.append(float(result["J"]))
    return transitions, {
        "mean_service_return": statistics.fmean(returns),
        "agent_event_rows": float(sum(event.rows.shape[0] for event in transitions)),
    }


def _row_references(events: Sequence[EventTransition]) -> list[tuple[int, int]]:
    return [
        (event_index, row_index)
        for event_index, event in enumerate(events)
        for row_index in range(event.rows.shape[0])
    ]


def ppo_epoch(
    model: RecurrentSetActorCritic, optimizer: torch.optim.Optimizer,
    events: Sequence[EventTransition], base_seed: int, arm: str,
    update: int, epoch: int, config: Config,
) -> tuple[dict[str, float], int, int]:
    references = _row_references(events)
    advantages = torch.tensor([
        events[event_index].advantage for event_index, _ in references
    ], dtype=torch.float32)
    advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(counter_seed(base_seed, arm, update, epoch, "ppo_order"))
    permutation = torch.randperm(len(references), generator=generator).tolist()
    # Preserve exactly four passes over the collected agent-event rows.  The
    # final minibatch contains the remaining rows; duplicating rows to fill it
    # would silently change exposure.
    padded = 0
    losses: list[dict[str, float]] = []
    model.train()
    for start in range(0, len(permutation), config.minibatch_agent_rows):
        selected_positions = permutation[start:start + config.minibatch_agent_rows]
        grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for batch_position, global_position in enumerate(selected_positions):
            event_index, row_index = references[global_position]
            grouped[event_index].append((batch_position, row_index))
        new_logprob: list[torch.Tensor | None] = [None] * len(selected_positions)
        entropy: list[torch.Tensor | None] = [None] * len(selected_positions)
        values: list[torch.Tensor | None] = [None] * len(selected_positions)
        old_logprob: list[float] = [0.0] * len(selected_positions)
        targets: list[float] = [0.0] * len(selected_positions)
        batch_advantages: list[float] = [0.0] * len(selected_positions)
        for event_index, positions in grouped.items():
            event = events[event_index]
            output = model.step(event.rows, event.actor_hidden, event.critic_hidden)
            distribution = torch.distributions.Categorical(logits=output.logits)
            event_logprob = distribution.log_prob(event.actions)
            event_entropy = distribution.entropy()
            for batch_position, row_index in positions:
                new_logprob[batch_position] = event_logprob[row_index]
                entropy[batch_position] = event_entropy[row_index]
                values[batch_position] = output.value
                old_logprob[batch_position] = float(event.old_logprobs[row_index])
                targets[batch_position] = event.target_return
                global_position = selected_positions[batch_position]
                batch_advantages[batch_position] = float(advantages[global_position])
        if any(item is None for item in (*new_logprob, *entropy, *values)):
            raise RuntimeError("incomplete PPO minibatch")
        new_lp = torch.stack([item for item in new_logprob if item is not None])
        entropy_tensor = torch.stack([item for item in entropy if item is not None])
        value_tensor = torch.stack([item for item in values if item is not None])
        old_lp = torch.tensor(old_logprob, dtype=torch.float32)
        target_tensor = torch.tensor(targets, dtype=torch.float32)
        advantage_tensor = torch.tensor(batch_advantages, dtype=torch.float32)
        ratio = torch.exp(new_lp - old_lp)
        policy_loss = -torch.minimum(
            ratio * advantage_tensor,
            torch.clamp(ratio, 1.0 - config.ppo_clip, 1.0 + config.ppo_clip) * advantage_tensor,
        ).mean()
        value_loss = torch.nn.functional.mse_loss(value_tensor, target_tensor)
        mean_entropy = entropy_tensor.mean()
        loss = policy_loss + config.value_coefficient * value_loss - config.entropy_coefficient * mean_entropy
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)
        optimizer.step()
        losses.append({
            "loss": float(loss.detach()), "policy_loss": float(policy_loss.detach()),
            "value_loss": float(value_loss.detach()), "entropy": float(mean_entropy.detach()),
        })
    return ({
        key: statistics.fmean(row[key] for row in losses)
        for key in ("loss", "policy_loss", "value_loss", "entropy")
    }, len(losses), padded)


def train_arm(
    arm: str, base_seed: int, config: Config = PRODUCTION_CONFIG,
) -> tuple[RecurrentSetActorCritic, torch.optim.Optimizer, list[dict[str, object]]]:
    torch.set_num_threads(1)
    model = initialize_model(base_seed, arm, counter_seed)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, betas=(.9, .999),
        eps=1e-8, weight_decay=0.0,
    )
    curves: list[dict[str, object]] = []
    started = time.perf_counter()
    optimizer_steps = 0
    for update in range(config.updates):
        rollout, rollout_summary = collect_rollout(model, arm, base_seed, update, config)
        epoch_summaries = []
        padded_rows = 0
        for epoch in range(config.ppo_epochs):
            summary, steps, padded = ppo_epoch(
                model, optimizer, rollout, base_seed, arm, update, epoch, config,
            )
            optimizer_steps += steps
            padded_rows += padded
            epoch_summaries.append(summary)
        curves.append({
            "update": update + 1,
            "episodes_completed": (update + 1) * config.episodes_per_update,
            "cumulative_wall_seconds": time.perf_counter() - started,
            "optimizer_steps_completed": optimizer_steps,
            "padded_minibatch_rows_this_update": padded_rows,
            **rollout_summary,
            "ppo": {
                key: statistics.fmean(row[key] for row in epoch_summaries)
                for key in ("loss", "policy_loss", "value_loss", "entropy")
            },
        })
    return model, optimizer, curves


def save_checkpoint(
    path: Path, model: RecurrentSetActorCritic,
    optimizer: torch.optim.Optimizer, arm: str, base_seed: int,
    curves: Sequence[Mapping[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save({
        "schema": "VNFC-B2-PPO-CHECKPOINT-v1", "arm": arm,
        "base_seed": base_seed, "update": PRODUCTION_CONFIG.updates,
        "episodes": PRODUCTION_CONFIG.updates * PRODUCTION_CONFIG.episodes_per_update,
        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
        "optimizer_steps": int(curves[-1]["optimizer_steps_completed"]),
        "parameter_count": model.parameter_count,
    }, temporary)
    temporary.replace(path)


def _panel_specs(config: Config) -> list[tuple[str, int, str, int]]:
    specs: list[tuple[str, int, str, int]] = []
    for n in (3, 4):
        for schedule in SEEN_SCHEDULES:
            specs.append(("seen_size_seen_schedule", n, schedule, 32))
    for schedule in SEEN_SCHEDULES:
        specs.append(("held_out_size_only", config.held_out_size, schedule, 32))
    for n in (3, 4):
        specs.append(("held_out_schedule_only", n, "S*", 32))
    specs.append(("joint_holdout", config.held_out_size, "S*", 64))
    return specs


def _replica_deviation(
    replicas: Sequence[Mapping[str, object]], config: Config,
) -> dict[str, float | int]:
    base = replicas[0]
    max_probability = max_reward = 0.0
    assignment_disagreements = probability_violations = reward_violations = 0
    for replica in replicas[1:]:
        for left, right in zip(base["ticks"], replica["ticks"]):  # type: ignore[arg-type]
            left_rows = left["physical_rows_stable_registry_order"]
            right_rows = right["physical_rows_stable_registry_order"]
            left_actions = [row["action"] for row in left_rows]
            right_actions = [row["action"] for row in right_rows]
            assignment_disagreements += int(left_actions != right_actions)
            reward_delta = abs(float(left["reward"]) - float(right["reward"]))
            max_reward = max(max_reward, reward_delta)
            reward_violations += int(not math.isclose(
                float(left["reward"]), float(right["reward"]),
                rel_tol=config.ordinary_rtol, abs_tol=config.ordinary_atol,
            ))
            for left_row, right_row in zip(left_rows, right_rows):
                a = np.asarray(left_row["probabilities"], dtype=np.float64)
                b = np.asarray(right_row["probabilities"], dtype=np.float64)
                if a.size:
                    max_probability = max(max_probability, float(np.max(np.abs(a - b))))
                    probability_violations += int(np.count_nonzero(~np.isclose(
                        a, b, rtol=config.ordinary_rtol, atol=config.ordinary_atol,
                    )))
    return {
        "max_probability_difference": max_probability,
        "max_reward_difference": max_reward,
        "assignment_disagreements": assignment_disagreements,
        "probability_tolerance_violations": probability_violations,
        "reward_tolerance_violations": reward_violations,
    }


def evaluate_models(
    models: Mapping[str, RecurrentSetActorCritic], base_seed: int,
    raw_rows_path: Path | None, config: Config = PRODUCTION_CONFIG,
) -> dict[str, object]:
    import gzip
    import json

    arms = (*LEARNED_ARMS, ORACLE)
    accumulators: dict[str, dict[tuple[str, str], dict[str, object]]] = {
        arm: defaultdict(lambda: {
            "J": [], "RR3": [], "probe": [], "wrong": [], "duplicate": [],
            "coverage_0": [], "coverage_1": [], "first_correct": [],
            "stale_selected": 0, "stale_eligible": 0,
            "hard": defaultdict(int),
        }) for arm in arms
    }
    stratified_accumulators: dict[
        str, dict[tuple[str, int, str, str], dict[str, object]]
    ] = {
        arm: defaultdict(lambda: {
            "J": [], "RR3": [], "probe": [], "wrong": [], "duplicate": [],
            "coverage_0": [], "coverage_1": [], "first_correct": [],
            "stale_selected": 0, "stale_eligible": 0,
            "hard": defaultdict(int),
        }) for arm in arms
    }
    permutation = {
        arm: {"max_probability_difference": 0.0, "max_reward_difference": 0.0,
              "assignment_disagreements": 0, "probability_tolerance_violations": 0,
              "reward_tolerance_violations": 0}
        for arm in arms
    }
    latency: dict[tuple[str, int], list[float]] = defaultdict(list)
    raw_stream = None
    if raw_rows_path is not None:
        raw_rows_path.parent.mkdir(parents=True, exist_ok=True)
        raw_stream = gzip.open(raw_rows_path, "wt", encoding="utf-8", newline="\n")
    world_counter = 0
    try:
        for panel, n, schedule, worlds in _panel_specs(config):
            for cell in EVENT_CELLS:
                for local_world in range(worlds):
                    cell_world_index = local_world
                    world = make_world(
                        base_seed, f"evaluation:{panel}:{n}:{schedule}:{cell}", cell_world_index,
                        n, cell, schedule,
                    )
                    world_counter += 1
                    for arm in arms:
                        with torch.no_grad():
                            replicas = [
                                run_episode(
                                    models.get(arm), arm, world, replica,
                                    generator=None, greedy=True,
                                    collect_transitions=False,
                                    latency=latency if arm != ORACLE else None,
                                )[0]
                                for replica in range(config.row_order_replicas)
                            ]
                        deviation = _replica_deviation(replicas, config)
                        for key, value in deviation.items():
                            if key.startswith("max_"):
                                permutation[arm][key] = max(float(permutation[arm][key]), float(value))
                            else:
                                permutation[arm][key] += int(value)
                        buckets = (
                            accumulators[arm][(panel, cell)],
                            stratified_accumulators[arm][(panel, n, schedule, cell)],
                        )
                        for bucket in buckets:
                            for metric in ("J", "RR3"):
                                bucket[metric].append(statistics.fmean(float(row[metric]) for row in replicas))
                            for target, source in (
                                ("probe", "probe_count"), ("wrong", "wrong_count"),
                                ("duplicate", "duplicate_count"),
                                ("first_correct", "time_to_first_correct_post_return"),
                            ):
                                bucket[target].append(statistics.fmean(float(row[source]) for row in replicas))
                            for role in (0, 1):
                                bucket[f"coverage_{role}"].append(statistics.fmean(
                                    float(row["coverage_by_role"][role]) for row in replicas
                                ))
                            bucket["stale_selected"] += sum(int(row["stale_command_selected"]) for row in replicas)
                            bucket["stale_eligible"] += sum(int(row["stale_command_eligible"]) for row in replicas)
                            for row in replicas:
                                for name, count in row["hard_stale_errors"].items():
                                    bucket["hard"][name] += int(count)
                        if raw_stream is not None:
                            raw_stream.write(json.dumps({
                                "base_seed": base_seed, "panel": panel, "n": n,
                                "schedule": schedule, "cell": cell,
                                "world_index": world.world_index, "arm": arm,
                                "replicas": replicas, "permutation": deviation,
                            }, separators=(",", ":")) + "\n")
    finally:
        if raw_stream is not None:
            raw_stream.close()

    arm_summaries: dict[str, object] = {}
    def summarize_bucket(bucket: Mapping[str, object]) -> dict[str, object]:
        return {
            metric: statistics.fmean(bucket[metric])  # type: ignore[arg-type]
            for metric in (
                "J", "RR3", "probe", "wrong", "duplicate",
                "coverage_0", "coverage_1", "first_correct",
            )
        } | {
            "SCR": (
                int(bucket["stale_selected"]) / int(bucket["stale_eligible"])
                if int(bucket["stale_eligible"]) else None
            ),
            "stale_command_selected": int(bucket["stale_selected"]),
            "stale_command_eligible": int(bucket["stale_eligible"]),
            "hard_stale_errors": dict(bucket["hard"]),  # type: ignore[arg-type]
            "base_worlds": len(bucket["J"]),  # type: ignore[arg-type]
        }
    for arm in arms:
        cells: dict[str, object] = {}
        for (panel, cell), bucket in sorted(accumulators[arm].items()):
            cells[f"{panel}:{cell}"] = summarize_bucket(bucket)
        stratified_cells = {
            f"{panel}:N{n}:{schedule}:{cell}": summarize_bucket(bucket)
            for (panel, n, schedule, cell), bucket
            in sorted(stratified_accumulators[arm].items())
        }
        arm_summaries[arm] = {
            "cells": cells, "stratified_cells": stratified_cells,
            "permutation": permutation[arm],
        }
    latency_summary = {
        arm: {
            str(n): {
                "events": len(rows), "p50_microseconds": float(np.percentile(rows, 50)),
                "p95_microseconds": float(np.percentile(rows, 95)),
            }
            for (key_arm, n), rows in sorted(latency.items()) if key_arm == arm
        }
        for arm in LEARNED_ARMS
    }
    return {
        "base_seed": base_seed, "arms": arm_summaries,
        "inference_latency": latency_summary,
        "base_worlds": world_counter,
        "replicated_episodes_per_arm": world_counter * config.row_order_replicas,
        "raw_rows": str(raw_rows_path) if raw_rows_path is not None else None,
    }


def evaluate_validation(
    model: RecurrentSetActorCritic, arm: str, base_seed: int,
    episodes: int = 128,
) -> dict[str, float | int]:
    values = []
    model.eval()
    with torch.no_grad():
        for episode in range(episodes):
            n, cell, schedule = _training_spec(base_seed, episode)
            world = make_world(base_seed, "validation", episode, n, cell, schedule)
            result, _ = run_episode(
                model, arm, world, replica=3, generator=None,
                greedy=True, collect_transitions=False,
            )
            values.append(float(result["J"]))
    return {"episodes": episodes, "mean_J": statistics.fmean(values)}


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
