"""Batched native production work for the SCDMP B01 orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Iterable, Sequence

import torch

from .contracts import GRAPHS, K_VALUES
from .foundation import (
    CompetenceRecord,
    FoundationActorCritic,
    ImmutableBatchedFoundationPolicy,
    freeze_foundation_actor,
)
from .native_backend import NativeSession
from .native_state import DisturbanceHold, HostOutput
from .rng import CounterRNG
from .training import (
    EpisodeSlot,
    ExactAdamW,
    RolloutBatch,
    UpdateReceipt,
    build_training_plan,
    train_one_update,
)


class WorkloadError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MissionEndpoint:
    seed: int
    stage: str
    update: int
    graph: str
    k: int
    mission: int
    terminal: bool
    safe_dock: bool
    dock_tick: int | None
    timeout: bool
    failures: tuple[str, ...]
    utility: float
    external_reward: float
    energy: float
    allocated_slots: int
    transitions: int
    policy_queries: int


@dataclass(frozen=True, slots=True)
class TrainingExecution:
    receipt: UpdateReceipt
    missions: int
    allocated_slots: int
    transitions: int
    policy_queries: int


@dataclass(frozen=True, slots=True)
class RepresentativeTwinWork:
    source_missions: int
    development_missions: int
    heldout_missions: int
    allocated_slots: int
    transitions: int
    policy_queries: int
    source_wall_seconds: float
    development_wall_seconds: float
    heldout_wall_seconds: float


def _uniform_reset(source: CounterRNG, domain: str, address: tuple[object, ...]):
    return (
        0.03 * source.uniform53(domain + "-reset-v", address),
        -0.01 + 0.02 * source.uniform53(domain + "-reset-y", address),
        -0.01 + 0.02 * source.uniform53(domain + "-reset-phi", address),
    )


def _disturbance(
    source: CounterRNG,
    *,
    domain: str,
    address: tuple[object, ...],
    renewal: int,
) -> DisturbanceHold:
    channels = []
    for channel, magnitude in enumerate((0.003, 0.002, 0.004)):
        channels.append(tuple(
            magnitude if source.bernoulli(
                0.5,
                domain=domain + "-disturbance-sign",
                address=address + (renewal, tick, channel),
            ) else -magnitude
            for tick in range(13)
        ))
    return DisturbanceHold(*channels)


def _reset_lanes(
    source: CounterRNG,
    rows: Sequence[tuple[str, int, tuple[object, ...]]],
    *,
    domain: str,
) -> NativeSession:
    states = []
    orders = []
    for graph, k, address in rows:
        initial_v, initial_y, initial_phi = _uniform_reset(source, domain, address)
        lane = NativeSession.reset(
            width=1,
            k=k,
            pre_event_q=0,
            initial_v=initial_v,
            initial_y=initial_y,
            initial_phi=initial_phi,
        )
        states.append(lane.states()[0])
        orders.append(graph)
    session = NativeSession.from_states(states)
    session.apply_orders(orders)
    return session


def _sample_action(probabilities: torch.Tensor, uniform: float) -> int:
    if probabilities.dtype != torch.float32 or probabilities.shape != (18,):
        raise WorkloadError("training categorical probabilities differ")
    cumulative = 0.0
    for index, probability in enumerate(probabilities.tolist()):
        cumulative += float(probability)
        if uniform < cumulative or index == 17:
            return index
    raise AssertionError("categorical sampler did not select an action")


def execute_training_update(
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    source: CounterRNG,
    *,
    update: int,
) -> TrainingExecution:
    """Run twelve real native episodes as one lane-stable PPO update."""

    slots = tuple(row for row in build_training_plan() if row.update == update)
    if len(slots) != 12 or model.foundation_seed != source.seed:
        raise WorkloadError("training update seed or twelve-slot frontier differs")
    rows = tuple(
        (slot.graph, slot.k, (update, slot.episode, slot.graph, slot.k)) for slot in slots
    )
    session = _reset_lanes(source, rows, domain="foundation-training")
    per_episode: list[list[tuple[tuple[float, ...], int, float, float, tuple[float, ...], bool]]] = [
        [] for _ in slots
    ]
    transitions = 0
    policy_queries = 0
    renewal = 0
    while any(not output.terminal for output in session.outputs):
        active_indices = tuple(index for index, output in enumerate(session.outputs) if not output.terminal)
        observations = torch.tensor(
            tuple(session.outputs[index].observation for index in active_indices),
            dtype=torch.float32,
        )
        with torch.no_grad():
            result = model(observations)
            probabilities = torch.softmax(result.logits, dim=1)
            log_probabilities = torch.log_softmax(result.logits, dim=1)
        actions = [0] * len(slots)
        staged: dict[int, tuple[tuple[float, ...], int, float, float]] = {}
        for batch_index, lane_index in enumerate(active_indices):
            slot = slots[lane_index]
            action = _sample_action(
                probabilities[batch_index],
                source.uniform53(
                    "foundation-action-sampling", slot.action_address(renewal),
                ),
            )
            actions[lane_index] = action
            staged[lane_index] = (
                tuple(float(value) for value in observations[batch_index].tolist()),
                action,
                float(log_probabilities[batch_index, action]),
                float(result.value[batch_index]),
            )
        disturbances = tuple(
            _disturbance(
                source,
                domain="foundation-training",
                address=(update, slot.episode, slot.graph, slot.k),
                renewal=renewal,
            )
            for slot in slots
        )
        outputs = session.step(
            tuple(actions), disturbances,
            active=tuple(index in active_indices for index in range(len(slots))),
        )
        for lane_index in active_indices:
            observation, action, log_probability, value = staged[lane_index]
            output = outputs[lane_index]
            per_episode[lane_index].append((
                observation, action, log_probability, value,
                output.last_hold_rewards, not output.terminal,
            ))
            transitions += output.ticks_advanced
            policy_queries += 1
        renewal += 1
        if renewal > 64:
            raise WorkloadError("training mission exceeded the 64-hold tape allocation")
    if any(not records for records in per_episode):
        raise WorkloadError("training mission produced no renewal records")

    flat = tuple(record for episode in per_episode for record in episode)
    offsets = [0]
    for episode in per_episode:
        offsets.append(offsets[-1] + len(episode))
    batch = RolloutBatch(
        observations=torch.tensor(tuple(row[0] for row in flat), dtype=torch.float32),
        actions=torch.tensor(tuple(row[1] for row in flat), dtype=torch.int64),
        old_log_probabilities=torch.tensor(tuple(row[2] for row in flat), dtype=torch.float32),
        old_values=torch.tensor(tuple(row[3] for row in flat), dtype=torch.float32),
        primitive_rewards=tuple(row[4] for row in flat),
        nonterminal=torch.tensor(tuple(row[5] for row in flat), dtype=torch.bool),
        episode_offsets=tuple(offsets),
        episode_slots=slots,
    )
    receipt = train_one_update(model, optimizer, source, batch, update=update)
    if receipt.transitions != transitions or receipt.records != policy_queries:
        raise WorkloadError("training kernel and native rollout counts differ")
    return TrainingExecution(receipt, 12, 12 * 364, transitions, policy_queries)


def _failure_labels(output: HostOutput) -> tuple[str, ...]:
    return tuple(
        label
        for label, present in (
            ("cable_overload", output.cable_overload),
            ("gantry_contact", output.gantry_contact),
            ("attitude_loss", output.attitude_loss),
            ("formation_loss", output.formation_loss),
        )
        if present
    )


def evaluate_foundation_missions(
    model: FoundationActorCritic,
    source: CounterRNG,
    *,
    stage: str,
    update: int,
    missions_per_cell: int,
) -> tuple[MissionEndpoint, ...]:
    """Run one real native evaluator batch over every graph-by-k cell."""

    if (
        model.foundation_seed != source.seed
        or stage not in {"CURVE", "COMPETENCE"}
        or isinstance(missions_per_cell, bool)
        or not isinstance(missions_per_cell, int)
        or missions_per_cell not in (8, 32)
    ):
        raise WorkloadError("foundation evaluator address differs")
    addresses = tuple(
        (graph, k, mission)
        for graph in GRAPHS for k in K_VALUES for mission in range(missions_per_cell)
    )
    lanes = tuple(
        (graph, k, (stage, update, graph, k, mission))
        for graph, k, mission in addresses
    )
    session = _reset_lanes(source, lanes, domain="foundation-" + stage.lower())
    policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(model))
    transitions = [0] * len(lanes)
    queries = [0] * len(lanes)
    renewal = 0
    while any(not output.terminal for output in session.outputs):
        active_indices = tuple(index for index, output in enumerate(session.outputs) if not output.terminal)
        visible = tuple(session.outputs[index].observation for index in active_indices)
        selected = policy(visible)
        actions = [0] * len(lanes)
        for lane_index, action in zip(active_indices, selected, strict=True):
            actions[lane_index] = action
            queries[lane_index] += 1
        disturbances = tuple(
            _disturbance(
                source,
                domain="foundation-" + stage.lower(),
                address=(stage, update, graph, k, mission),
                renewal=renewal,
            )
            for graph, k, mission in addresses
        )
        outputs = session.step(
            tuple(actions), disturbances,
            active=tuple(index in active_indices for index in range(len(lanes))),
        )
        for lane_index in active_indices:
            transitions[lane_index] += outputs[lane_index].ticks_advanced
        renewal += 1
        if renewal > 64:
            raise WorkloadError("foundation evaluator exceeded the 64-hold tape allocation")
    endpoints = []
    for index, ((graph, k, mission), output) in enumerate(zip(addresses, session.outputs, strict=True)):
        endpoints.append(MissionEndpoint(
            seed=source.seed, stage=stage, update=update, graph=graph, k=k, mission=mission,
            terminal=output.terminal, safe_dock=output.safe_dock, dock_tick=output.dock_tick,
            timeout=output.timeout, failures=_failure_labels(output), utility=output.completion_value,
            external_reward=output.cumulative_reward, energy=output.cumulative_energy,
            allocated_slots=364, transitions=transitions[index], policy_queries=queries[index],
        ))
    if len(endpoints) != 4 * missions_per_cell or not all(row.terminal for row in endpoints):
        raise WorkloadError("foundation evaluator did not produce the complete terminal inventory")
    return tuple(endpoints)


def competence_records(endpoints: Iterable[MissionEndpoint]) -> tuple[CompetenceRecord, ...]:
    rows = tuple(endpoints)
    failure_map = {
        "gantry_contact": "boundary_contact",
        "attitude_loss": "swing_envelope_loss",
        "cable_overload": "cable_overload",
        "formation_loss": "formation_loss",
    }
    return tuple(CompetenceRecord(
        seed=row.seed,
        graph=row.graph,
        k=row.k,
        mission=row.mission,
        terminal=row.terminal,
        finite=all(math.isfinite(value) for value in (
            row.utility, row.external_reward, row.energy,
        )),
        evaluator_valid=(row.stage == "COMPETENCE" and row.update == 160),
        safe_dock=row.safe_dock,
        failures=tuple(failure_map[label] for label in row.failures),
    ) for row in rows)


def _continue_technical_twins(
    state_bytes: tuple[bytes, bytes],
    *,
    forced_actions: tuple[int, int],
    policy: ImmutableBatchedFoundationPolicy,
    source: CounterRNG,
    address: tuple[object, ...],
) -> tuple[int, int]:
    session = NativeSession.from_state_bytes(state_bytes)
    first_row = _disturbance(
        source, domain="a-recon-twin", address=address, renewal=0,
    )
    outputs = session.step(
        forced_actions,
        (first_row, first_row),
    )
    transitions = sum(row.ticks_advanced for row in outputs)
    queries = 0
    renewal = 1
    while any(not row.terminal for row in outputs):
        active = tuple(index for index, row in enumerate(outputs) if not row.terminal)
        selected = policy(tuple(outputs[index].observation for index in active))
        actions = [0, 0]
        for index, action in zip(active, selected, strict=True):
            actions[index] = action
            queries += 1
        common_row = _disturbance(
            source, domain="a-recon-twin", address=address, renewal=renewal,
        )
        rows = (common_row, common_row)
        outputs = session.step(tuple(actions), rows, active=tuple(index in active for index in range(2)))
        transitions += sum(outputs[index].ticks_advanced for index in active)
        renewal += 1
        if renewal > 64:
            raise WorkloadError("A/RECON twin continuation exceeded 64 holds")
    return transitions, queries


def execute_representative_twin_work(
    model: FoundationActorCritic,
    source: CounterRNG,
) -> RepresentativeTwinWork:
    """Exercise source clone, full action sweep, and three-arm seams without RUN-01 identity."""

    if model.foundation_seed != source.seed:
        raise WorkloadError("A/RECON twin work seed differs")
    policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(model))
    # Build the technical source lane directly and use no RUN-01 q/master.
    source_started = time.perf_counter()
    initial_v, initial_y, initial_phi = _uniform_reset(
        source, "a-recon-source", ("A/RECON", "source", 0),
    )
    source_session = NativeSession.reset(
        width=1, k=7, pre_event_q=0, initial_v=initial_v,
        initial_y=initial_y, initial_phi=initial_phi,
    )
    source_transitions = 0
    source_queries = 0
    renewal = 0
    while source_session.outputs[0].tick < 64 and not source_session.outputs[0].terminal:
        action = policy((source_session.outputs[0].observation,))[0]
        output = source_session.step((action,), (
            _disturbance(
                source, domain="a-recon-source", address=("A/RECON", "source", 0),
                renewal=renewal,
            ),
        ))[0]
        source_transitions += output.ticks_advanced
        source_queries += 1
        renewal += 1
    if source_session.outputs[0].terminal or source_session.outputs[0].tick < 64:
        raise WorkloadError("A/RECON technical source did not reach its representative boundary")
    source_bytes = source_session.state_bytes()[0]
    twins = NativeSession.from_state_bytes((source_bytes, source_bytes))
    twins.apply_orders(("HR", "RH"))
    twin_bytes = twins.state_bytes()
    source_wall = time.perf_counter() - source_started
    transitions = source_transitions
    queries = source_queries
    development_started = time.perf_counter()
    for action in range(18):
        observed_transitions, observed_queries = _continue_technical_twins(
            twin_bytes, forced_actions=(action, action), policy=policy, source=source,
            address=("A/RECON", "development", action),
        )
        transitions += observed_transitions
        queries += observed_queries
    development_wall = time.perf_counter() - development_started
    heldout_started = time.perf_counter()
    for arm, actions in enumerate(((0, 1), (1, 0), (0, 0))):
        observed_transitions, observed_queries = _continue_technical_twins(
            twin_bytes, forced_actions=actions, policy=policy, source=source,
            address=("A/RECON", "heldout", arm),
        )
        transitions += observed_transitions
        queries += observed_queries
    heldout_wall = time.perf_counter() - heldout_started
    return RepresentativeTwinWork(
        source_missions=1,
        development_missions=36,
        heldout_missions=6,
        allocated_slots=(1 + 36 + 6) * 364,
        transitions=transitions,
        policy_queries=queries,
        source_wall_seconds=source_wall,
        development_wall_seconds=development_wall,
        heldout_wall_seconds=heldout_wall,
    )


__all__ = [
    "MissionEndpoint", "RepresentativeTwinWork", "TrainingExecution", "WorkloadError",
    "competence_records", "evaluate_foundation_missions", "execute_representative_twin_work",
    "execute_training_update",
]
