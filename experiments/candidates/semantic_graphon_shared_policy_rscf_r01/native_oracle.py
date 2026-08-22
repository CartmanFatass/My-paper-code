"""Independent deterministic Python oracle for the TEST-only native ABI.

The production boundary never calls this module.  Its sole purpose is exact
Gate-A conformance and paired warm timing against the C++17 implementation.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
import struct
import time
from typing import Iterable

import numpy as np

from .native_contract import (
    ABI_VERSION,
    ACTION_FORWARD_BASE,
    ACTION_HOLD,
    ACTION_LISTEN_EAST,
    ACTION_LISTEN_WEST,
    ACTION_SCAN,
    ACTION_UPLINK,
    FIFO_CAPACITY,
    HIDDEN_DIM,
    HORIZON,
    LEGAL_ACTIONS,
    MAX_AGENTS,
    METRIC_COLLISION_LOSS,
    METRIC_DECODED_ARRIVALS,
    METRIC_DUPLICATE_ARRIVALS,
    METRIC_EMPTY_ACTIONS,
    METRIC_EXPIRED_ARRIVALS,
    METRIC_NEW_TIMELY,
    METRIC_RADIO_ACTIONS,
    METRIC_WASTE_ACTIONS,
    MODE_FULL_ROTATED,
    MODE_INTACT,
    NATIVE_THREADS,
    ROTATED_PHYSICAL_SOURCE_COLUMN,
    FactualEpisodeBatch,
    FactualTrajectory,
    NativeSuffixResult,
    ROLE_EAST,
    ROLE_RELAY,
    ROLE_WEST,
    SCHEDULE_BASE,
    SCHEDULE_UPLINK,
    ActorParameters,
    SuffixBatch,
    ShadowTrajectory,
    make_test_actor_parameters,
    make_test_factual_episode_batch,
    make_test_suffix_batch,
    validate_actor_parameters,
    validate_factual_episode_batch,
    validate_suffix_batch,
    with_factual_actions,
    with_factual_terminal,
)


_P0 = np.asarray(
    ((0.92, 0.48, 0.88), (0.48, 0.92, 0.82), (0.86, 0.78, 0.90)),
    dtype=np.float64,
)
_LATENCY = np.asarray(((1.0, 2.0, 1.0), (2.0, 1.0, 1.0), (1.0, 1.0, 1.0)))
_FNV_OFFSET = 1469598103934665603
_FNV_PRIME = 1099511628211
_MASK64 = (1 << 64) - 1


def _fnv_bytes(value: int, data: bytes) -> int:
    for byte in data:
        value ^= byte
        value = (value * _FNV_PRIME) & _MASK64
    return value


def _fnv_i64(value: int, item: int) -> int:
    return _fnv_bytes(value, struct.pack("<q", int(item)))


def _fnv_u64(value: int, item: int) -> int:
    return _fnv_bytes(value, struct.pack("<Q", int(item)))


def _fnv_f64(value: int, item: float) -> int:
    return _fnv_bytes(value, struct.pack("<d", float(item)))


def _fnv_canonical_f64(value: int, item: float) -> int:
    scaled = float(item) * 1.0e8
    quantized = math.floor(scaled + 0.5) if scaled >= 0.0 else math.ceil(scaled - 0.5)
    return _fnv_i64(value, quantized)


def _sigmoid(value: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-value))


def _link_probability(base: float, multiplicity: int) -> float:
    logit = math.log(base / (1.0 - base))
    shifted = logit - 0.22 * (multiplicity - 1)
    return 1.0 / (1.0 + math.exp(-shifted))


@dataclass
class _Scheduled:
    kind: int
    due: int
    sender: int
    receiver: int
    basin: int
    ordinal: int
    birth: int


def _fifo_head(
    basin: np.ndarray, ordinal: np.ndarray, birth: np.ndarray, agent: int
) -> tuple[int, int, int] | None:
    if birth[agent, 0] < 0:
        return None
    return int(basin[agent, 0]), int(ordinal[agent, 0]), int(birth[agent, 0])


def _fifo_remove_head(
    basin: np.ndarray,
    ordinal: np.ndarray,
    birth: np.ndarray,
    agent: int,
    expected: tuple[int, int, int],
) -> None:
    head = _fifo_head(basin, ordinal, birth, agent)
    if head != expected:
        raise ValueError(
            f"scheduled acknowledgement packet {expected} does not match sender {agent} head {head}"
        )
    basin[agent, :-1] = basin[agent, 1:]
    ordinal[agent, :-1] = ordinal[agent, 1:]
    birth[agent, :-1] = birth[agent, 1:]
    basin[agent, -1] = -1
    ordinal[agent, -1] = -1
    birth[agent, -1] = -1


def _fifo_append(
    basin: np.ndarray,
    ordinal: np.ndarray,
    birth: np.ndarray,
    agent: int,
    capacity: int,
    packet: tuple[int, int, int],
) -> None:
    empty = next((position for position in range(capacity) if birth[agent, position] < 0), None)
    if empty is None:
        basin[agent, : capacity - 1] = basin[agent, 1:capacity]
        ordinal[agent, : capacity - 1] = ordinal[agent, 1:capacity]
        birth[agent, : capacity - 1] = birth[agent, 1:capacity]
        empty = capacity - 1
    basin[agent, empty], ordinal[agent, empty], birth[agent, empty] = packet


def _purge_expired(
    basin: np.ndarray,
    ordinal: np.ndarray,
    birth: np.ndarray,
    roles: np.ndarray,
    n_agents: int,
    slot: int,
) -> None:
    for agent in range(n_agents):
        capacity = 2 if roles[agent] != ROLE_RELAY else 4
        keep = [
            position
            for position in range(capacity)
            if birth[agent, position] >= 0 and slot < birth[agent, position] + 4
        ]
        packets = [
            (int(basin[agent, position]), int(ordinal[agent, position]), int(birth[agent, position]))
            for position in keep
        ]
        basin[agent, :] = -1
        ordinal[agent, :] = -1
        birth[agent, :] = -1
        for position, packet in enumerate(packets):
            basin[agent, position], ordinal[agent, position], birth[agent, position] = packet


def _process_arrivals(
    scheduled: list[_Scheduled],
    slot: int,
    basin: np.ndarray,
    ordinal: np.ndarray,
    birth: np.ndarray,
    roles: np.ndarray,
    delivered: np.ndarray,
    metrics: np.ndarray,
    previous_success: np.ndarray,
) -> None:
    due = [entry for entry in scheduled if entry.due == slot]
    scheduled[:] = [entry for entry in scheduled if entry.due != slot]
    removed: set[tuple[int, int, int, int, int]] = set()
    for entry in due:
        packet = (entry.basin, entry.ordinal, entry.birth)
        removal_key = (entry.kind, entry.sender, *packet)
        if removal_key not in removed:
            _fifo_remove_head(basin, ordinal, birth, entry.sender, packet)
            removed.add(removal_key)
        metrics[METRIC_DECODED_ARRIVALS] += 1
        if slot >= entry.birth + 4:
            metrics[METRIC_EXPIRED_ARRIVALS] += 1
            continue
        if entry.kind == SCHEDULE_UPLINK:
            _fifo_append(basin, ordinal, birth, entry.receiver, 4, packet)
            previous_success[entry.sender] = 1
            previous_success[entry.receiver] = 1
        elif entry.kind == SCHEDULE_BASE:
            if delivered[entry.basin, entry.ordinal]:
                metrics[METRIC_DUPLICATE_ARRIVALS] += 1
            else:
                delivered[entry.basin, entry.ordinal] = 1
                metrics[METRIC_NEW_TIMELY] += 1
                previous_success[entry.sender] = 1
        else:
            raise ValueError(f"unsupported scheduled kind {entry.kind}")


def _observations(
    slot: int,
    n_agents: int,
    roles: np.ndarray,
    fifo_birth: np.ndarray,
    previous_action: np.ndarray,
    previous_success: np.ndarray,
) -> np.ndarray:
    result = np.zeros((n_agents, 22), dtype=np.float64)
    per_role = n_agents / 3.0
    for agent in range(n_agents):
        role = int(roles[agent])
        obs = result[agent]
        obs[role] = 1.0
        obs[3] = slot / 11.0
        obs[4:7] = per_role / 7.0
        for position in range(FIFO_CAPACITY):
            packet_birth = int(fifo_birth[agent, position])
            if packet_birth >= 0:
                obs[7 + 2 * position] = 1.0
                obs[8 + 2 * position] = min(max(slot - packet_birth, 0), 3) / 3.0
        action = int(previous_action[agent])
        if action >= 0:
            obs[15 + action] = 1.0
        obs[21] = float(previous_success[agent])
    return result


def _policy_step(
    observations: np.ndarray,
    hidden: np.ndarray,
    roles: np.ndarray,
    parameters: ActorParameters,
    action_uniform: np.ndarray,
    mode: str = MODE_INTACT,
    messages_override: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_agents = observations.shape[0]
    if mode not in (MODE_INTACT, MODE_FULL_ROTATED):
        raise ValueError(f"unsupported policy mode {mode}")
    if messages_override is None:
        messages = np.tanh(observations @ parameters.encoder_w1.T + parameters.encoder_b1)
        messages = np.tanh(messages @ parameters.encoder_w2.T + parameters.encoder_b2)
    else:
        messages = np.asarray(messages_override, dtype=np.float64)
        if messages.shape != (n_agents, 32):
            raise ValueError("message override has wrong shape")
    counts = np.asarray([np.count_nonzero(roles == role) for role in range(3)], dtype=np.int64)
    role_sums = np.vstack([messages[roles == role].sum(axis=0) for role in range(3)])
    omega = np.empty((3, 3), dtype=np.float64)
    for receiver_role in range(3):
        for sender_role in range(3):
            multiplicity = int(counts[sender_role])
            physical_sender = (
                sender_role
                if mode == MODE_INTACT
                else ROTATED_PHYSICAL_SOURCE_COLUMN[sender_role]
            )
            probability = _link_probability(
                float(_P0[receiver_role, physical_sender]), multiplicity
            )
            k0 = probability / float(_LATENCY[receiver_role, physical_sender])
            v = (2.0 * math.log(multiplicity) - math.log(14.0)) / math.log(7.0 / 2.0)
            residual = (
                parameters.beta[receiver_role, sender_role, 0]
                + parameters.beta[receiver_role, sender_role, 1] * v
            )
            omega[receiver_role, sender_role] = k0 * math.exp(float(residual))

    summaries = np.empty((n_agents, 32), dtype=np.float64)
    denominators = np.empty(n_agents, dtype=np.float64)
    for agent in range(n_agents):
        receiver_role = int(roles[agent])
        weights = omega[receiver_role]
        denominator = float(np.dot(counts, weights))
        summaries[agent] = (weights[:, None] * role_sums).sum(axis=0) / (denominator + 1e-12)
        denominators[agent] = denominator

    actor_input = np.concatenate((observations, summaries, denominators[:, None]), axis=1)
    z = _sigmoid(actor_input @ parameters.gru_w[0].T + hidden @ parameters.gru_u[0].T + parameters.gru_b[0])
    r = _sigmoid(actor_input @ parameters.gru_w[1].T + hidden @ parameters.gru_u[1].T + parameters.gru_b[1])
    candidate = np.tanh(
        actor_input @ parameters.gru_w[2].T
        + (r * hidden) @ parameters.gru_u[2].T
        + parameters.gru_b[2]
    )
    new_hidden = (1.0 - z) * candidate + z * hidden
    logits = new_hidden @ parameters.actor_w.T + parameters.actor_b
    probabilities = np.zeros((n_agents, 6), dtype=np.float64)
    actions = np.empty(n_agents, dtype=np.int64)
    for agent in range(n_agents):
        legal = LEGAL_ACTIONS[int(roles[agent])]
        legal_logits = logits[agent, list(legal)]
        shifted = legal_logits - float(np.max(legal_logits))
        softmax = np.exp(shifted)
        softmax /= float(softmax.sum())
        executed = 0.96 * softmax + 0.04 / len(legal)
        probabilities[agent, list(legal)] = executed
        uniform = float(action_uniform[agent])
        cumulative = 0.0
        action = legal[-1]
        for candidate_action, probability in zip(legal, executed):
            cumulative += float(probability)
            if uniform < cumulative:
                action = candidate_action
                break
        actions[agent] = action
    return actions, new_hidden, messages, probabilities, summaries, denominators


def _schedule_radio(
    slot: int,
    actions: np.ndarray,
    n_agents: int,
    roles: np.ndarray,
    fifo_basin: np.ndarray,
    fifo_ordinal: np.ndarray,
    fifo_birth: np.ndarray,
    delivered: np.ndarray,
    metrics: np.ndarray,
    scheduled: list[_Scheduled],
    uplink_uniform: np.ndarray,
    base_uniform: np.ndarray,
) -> None:
    per_role = n_agents // 3
    for action in actions:
        if int(action) in (
            ACTION_UPLINK,
            ACTION_LISTEN_WEST,
            ACTION_LISTEN_EAST,
            ACTION_FORWARD_BASE,
        ):
            metrics[METRIC_RADIO_ACTIONS] += 1

    for basin_id, surveyor_role, listen_action in (
        (0, ROLE_WEST, ACTION_LISTEN_WEST),
        (1, ROLE_EAST, ACTION_LISTEN_EAST),
    ):
        uplink_agents = [
            agent
            for agent in range(n_agents)
            if roles[agent] == surveyor_role and actions[agent] == ACTION_UPLINK
        ]
        nonempty = [agent for agent in uplink_agents if _fifo_head(fifo_basin, fifo_ordinal, fifo_birth, agent)]
        for agent in uplink_agents:
            if agent not in nonempty:
                metrics[METRIC_EMPTY_ACTIONS] += 1
                metrics[METRIC_WASTE_ACTIONS] += 1
        listeners = [
            agent
            for agent in range(n_agents)
            if roles[agent] == ROLE_RELAY and actions[agent] == listen_action
        ]
        if len(nonempty) != 1:
            if len(nonempty) >= 2:
                metrics[METRIC_COLLISION_LOSS] += len(nonempty)
                metrics[METRIC_WASTE_ACTIONS] += len(nonempty)
            metrics[METRIC_WASTE_ACTIONS] += len(listeners)
            continue

        sender = nonempty[0]
        packet = _fifo_head(fifo_basin, fifo_ordinal, fifo_birth, sender)
        assert packet is not None and packet[0] == basin_id
        due = slot + 1
        decoded_nonexpired: set[int] = set()
        if slot < HORIZON - 1:
            probability = _link_probability(float(_P0[ROLE_RELAY, surveyor_role]), per_role)
            for receiver in listeners:
                if float(uplink_uniform[sender, receiver]) < probability:
                    scheduled.append(
                        _Scheduled(SCHEDULE_UPLINK, due, sender, receiver, *packet)
                    )
                    if due < packet[2] + 4:
                        decoded_nonexpired.add(receiver)
        if not decoded_nonexpired:
            metrics[METRIC_WASTE_ACTIONS] += 1
        metrics[METRIC_WASTE_ACTIONS] += sum(receiver not in decoded_nonexpired for receiver in listeners)

    forward_agents = [agent for agent in range(n_agents) if actions[agent] == ACTION_FORWARD_BASE]
    nonempty_forward = [
        agent for agent in forward_agents if _fifo_head(fifo_basin, fifo_ordinal, fifo_birth, agent)
    ]
    for agent in forward_agents:
        if agent not in nonempty_forward:
            metrics[METRIC_EMPTY_ACTIONS] += 1
            metrics[METRIC_WASTE_ACTIONS] += 1
    if len(nonempty_forward) >= 2:
        metrics[METRIC_COLLISION_LOSS] += len(nonempty_forward)
        metrics[METRIC_WASTE_ACTIONS] += len(nonempty_forward)
    elif len(nonempty_forward) == 1:
        sender = nonempty_forward[0]
        packet = _fifo_head(fifo_basin, fifo_ordinal, fifo_birth, sender)
        assert packet is not None
        due = slot + 1
        probability = _link_probability(0.90, per_role)
        decoded = slot < HORIZON - 1 and float(base_uniform[sender]) < probability
        new_timely = decoded and due < packet[2] + 4 and not delivered[packet[0], packet[1]]
        if decoded:
            scheduled.append(_Scheduled(SCHEDULE_BASE, due, sender, -1, *packet))
        if not new_timely:
            metrics[METRIC_WASTE_ACTIONS] += 1


def _scan(
    slot: int,
    actions: np.ndarray,
    n_agents: int,
    roles: np.ndarray,
    fifo_basin: np.ndarray,
    fifo_ordinal: np.ndarray,
    fifo_birth: np.ndarray,
    event_schedule: np.ndarray,
    detection_uniform: np.ndarray,
) -> None:
    for agent in range(n_agents):
        role = int(roles[agent])
        if role not in (ROLE_WEST, ROLE_EAST) or actions[agent] != ACTION_SCAN:
            continue
        basin_id = role
        matching = np.flatnonzero(event_schedule[basin_id] == slot)
        if matching.size == 1 and float(detection_uniform[agent]) < 0.75:
            ordinal = int(matching[0])
            _fifo_append(
                fifo_basin,
                fifo_ordinal,
                fifo_birth,
                agent,
                2,
                (basin_id, ordinal, slot),
            )


def _terminal(delivered: np.ndarray, metrics: np.ndarray) -> float:
    west = int(delivered[0].sum())
    east = int(delivered[1].sum())
    radio = int(metrics[METRIC_RADIO_ACTIONS])
    waste = 0.0 if radio == 0 else float(metrics[METRIC_WASTE_ACTIONS]) / radio
    return 0.65 * (west + east) / 6.0 + 0.25 * min(west, east) / 3.0 + 0.10 * (1.0 - waste)


def _common_tape_digest(batch: SuffixBatch, lane: int, n_agents: int, origin: int) -> int:
    digest = _fnv_i64(_FNV_OFFSET, n_agents)
    digest = _fnv_i64(digest, origin)
    for slot in range(origin, HORIZON):
        for agent in range(n_agents):
            digest = _fnv_f64(digest, batch.detection_uniform[lane, slot, agent])
            digest = _fnv_f64(digest, batch.base_uniform[lane, slot, agent])
            digest = _fnv_f64(digest, batch.action_uniform[lane, slot, agent])
            for receiver in range(n_agents):
                digest = _fnv_f64(digest, batch.uplink_uniform[lane, slot, agent, receiver])
    return digest


def _audit_prefix(batch: SuffixBatch, lane: int, n_agents: int, common_digest: int) -> int:
    digest = _fnv_u64(_FNV_OFFSET, common_digest)
    digest = _fnv_i64(digest, int(batch.origin_slot[lane]))
    digest = _fnv_i64(digest, int(batch.focal_agent[lane]))
    for agent in range(n_agents):
        digest = _fnv_i64(digest, int(batch.roles[lane, agent]))
        for position in range(4):
            digest = _fnv_i64(digest, int(batch.fifo_basin[lane, agent, position]))
            digest = _fnv_i64(digest, int(batch.fifo_ordinal[lane, agent, position]))
            digest = _fnv_i64(digest, int(batch.fifo_birth[lane, agent, position]))
    digest = _fnv_i64(digest, int(batch.scheduled_count[lane]))
    for value in batch.delivered[lane].ravel():
        digest = _fnv_i64(digest, int(value))
    for value in batch.metrics[lane]:
        digest = _fnv_i64(digest, int(value))
    for agent in range(n_agents):
        digest = _fnv_i64(digest, int(batch.previous_action[lane, agent]))
        digest = _fnv_i64(digest, int(batch.previous_success[lane, agent]))
    for value in batch.event_schedule[lane].ravel():
        digest = _fnv_i64(digest, int(value))
    for array in (
        batch.post_gru_hidden[lane, :n_agents],
        batch.current_observations[lane, :n_agents],
        batch.current_messages[lane, :n_agents],
        batch.current_legal_probabilities[lane, :n_agents],
    ):
        for value in array.ravel():
            digest = _fnv_f64(digest, float(value))
    for value in batch.factual_joint_action[lane, :n_agents]:
        digest = _fnv_i64(digest, int(value))
    digest = _fnv_i64(digest, int(batch.focal_intervention[lane]))
    return digest


def _run_lane(batch: SuffixBatch, parameters: ActorParameters, lane: int) -> tuple:
    n_agents = int(batch.n_agents[lane])
    origin = int(batch.origin_slot[lane])
    focal = int(batch.focal_agent[lane])
    roles = batch.roles[lane, :n_agents].copy()
    fifo_basin = batch.fifo_basin[lane, :n_agents].copy()
    fifo_ordinal = batch.fifo_ordinal[lane, :n_agents].copy()
    fifo_birth = batch.fifo_birth[lane, :n_agents].copy()
    delivered = batch.delivered[lane].copy()
    metrics = batch.metrics[lane].copy()
    previous_action = batch.previous_action[lane, :n_agents].copy()
    previous_success = batch.previous_success[lane, :n_agents].copy()
    hidden = batch.post_gru_hidden[lane, :n_agents].copy()
    event_schedule = batch.event_schedule[lane]
    scheduled = [
        _Scheduled(
            int(batch.scheduled_kind[lane, index]),
            int(batch.scheduled_due[lane, index]),
            int(batch.scheduled_sender[lane, index]),
            int(batch.scheduled_receiver[lane, index]),
            int(batch.scheduled_basin[lane, index]),
            int(batch.scheduled_ordinal[lane, index]),
            int(batch.scheduled_birth[lane, index]),
        )
        for index in range(int(batch.scheduled_count[lane]))
    ]

    actions = batch.factual_joint_action[lane, :n_agents].copy()
    actions[focal] = batch.focal_intervention[lane]
    transitions = 0
    future_policy_rounds = 0
    future_policy_decisions = 0
    for slot in range(origin, HORIZON):
        if slot > origin:
            _process_arrivals(
                scheduled,
                slot,
                fifo_basin,
                fifo_ordinal,
                fifo_birth,
                roles,
                delivered,
                metrics,
                previous_success,
            )
            _purge_expired(fifo_basin, fifo_ordinal, fifo_birth, roles, n_agents, slot)
            obs = _observations(
                slot, n_agents, roles, fifo_birth, previous_action, previous_success
            )
            actions, hidden, _, _, _, _ = _policy_step(
                obs,
                hidden,
                roles,
                parameters,
                batch.action_uniform[lane, slot, :n_agents],
            )
            future_policy_rounds += 1
            future_policy_decisions += n_agents

        previous_action[:] = actions
        previous_success[:] = 0
        _schedule_radio(
            slot,
            actions,
            n_agents,
            roles,
            fifo_basin,
            fifo_ordinal,
            fifo_birth,
            delivered,
            metrics,
            scheduled,
            batch.uplink_uniform[lane, slot],
            batch.base_uniform[lane, slot],
        )
        _scan(
            slot,
            actions,
            n_agents,
            roles,
            fifo_basin,
            fifo_ordinal,
            fifo_birth,
            event_schedule,
            batch.detection_uniform[lane, slot],
        )
        transitions += 1

    terminal = _terminal(delivered, metrics)
    common_digest = _common_tape_digest(batch, lane, n_agents, origin)
    audit = _audit_prefix(batch, lane, n_agents, common_digest)
    audit = _fnv_i64(audit, int(batch.factual_joint_action[lane, focal]))
    for value in delivered.ravel():
        audit = _fnv_i64(audit, int(value))
    for value in metrics:
        audit = _fnv_i64(audit, int(value))
    audit = _fnv_f64(audit, terminal)
    counters = np.asarray(
        (transitions, future_policy_rounds, future_policy_decisions, metrics[METRIC_DECODED_ARRIVALS]),
        dtype=np.int64,
    )
    factual_candidate = int(batch.focal_intervention[lane]) == int(
        batch.factual_joint_action[lane, focal]
    )
    factual_identity = factual_candidate and struct.pack("<d", terminal) == struct.pack(
        "<d", float(batch.factual_terminal[lane])
    )
    return (
        terminal,
        delivered.sum(axis=1).astype(np.int64),
        metrics.astype(np.int64),
        counters,
        np.uint64(common_digest),
        np.uint64(audit),
        factual_candidate,
        factual_identity,
    )


def _trace_snapshot_digest(
    slot: int,
    state_roles: np.ndarray,
    fifo_basin: np.ndarray,
    fifo_ordinal: np.ndarray,
    fifo_birth: np.ndarray,
    delivered: np.ndarray,
    metrics: np.ndarray,
    previous_action: np.ndarray,
    previous_success: np.ndarray,
    event_schedule: np.ndarray,
    observations: np.ndarray,
    messages: np.ndarray,
    summaries: np.ndarray,
    denominators: np.ndarray,
    incoming_hidden: np.ndarray,
    post_hidden: np.ndarray,
    probabilities: np.ndarray,
    actions: np.ndarray,
) -> int:
    digest = _fnv_i64(_FNV_OFFSET, slot)
    for array in (
        state_roles,
        fifo_basin,
        fifo_ordinal,
        fifo_birth,
        delivered,
        metrics,
        previous_action,
        previous_success,
        event_schedule,
        actions,
    ):
        for value in array.ravel():
            digest = _fnv_i64(digest, int(value))
    for array in (
        observations,
        messages,
        summaries,
        denominators,
        incoming_hidden,
        post_hidden,
        probabilities,
    ):
        for value in array.ravel():
            digest = _fnv_canonical_f64(digest, float(value))
    return digest


def _episode_common_tape_digest(
    episode: FactualEpisodeBatch, lane: int, n_agents: int
) -> int:
    digest = _fnv_i64(_FNV_OFFSET, n_agents)
    digest = _fnv_i64(digest, 0)
    for slot in range(HORIZON):
        for agent in range(n_agents):
            digest = _fnv_f64(digest, episode.detection_uniform[lane, slot, agent])
            digest = _fnv_f64(digest, episode.base_uniform[lane, slot, agent])
            digest = _fnv_f64(digest, episode.action_uniform[lane, slot, agent])
            for receiver in range(n_agents):
                digest = _fnv_f64(
                    digest, episode.uplink_uniform[lane, slot, agent, receiver]
                )
    return digest


def python_factual_trajectory(
    episode: FactualEpisodeBatch,
    parameters: ActorParameters,
    *,
    mode: str = MODE_INTACT,
) -> FactualTrajectory:
    """Independent reset-to-terminal TEST oracle for factual trajectories."""

    validate_factual_episode_batch(episode)
    validate_actor_parameters(parameters)
    if mode not in (MODE_INTACT, MODE_FULL_ROTATED):
        raise ValueError(f"unsupported factual trajectory mode {mode}")
    width = episode.width
    observations = np.zeros((width, HORIZON, MAX_AGENTS, 22), dtype=np.float64)
    messages = np.zeros((width, HORIZON, MAX_AGENTS, 32), dtype=np.float64)
    role_summaries = np.zeros_like(messages)
    denominators = np.zeros((width, HORIZON, MAX_AGENTS), dtype=np.float64)
    incoming_hidden = np.zeros(
        (width, HORIZON, MAX_AGENTS, HIDDEN_DIM), dtype=np.float64
    )
    post_gru_hidden = np.zeros_like(incoming_hidden)
    legal_probabilities = np.zeros(
        (width, HORIZON, MAX_AGENTS, 6), dtype=np.float64
    )
    factual_actions = np.full((width, HORIZON, MAX_AGENTS), -1, dtype=np.int64)
    fifo_basin_trace = np.full(
        (width, HORIZON, MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int64
    )
    fifo_ordinal_trace = np.full_like(fifo_basin_trace, -1)
    fifo_birth_trace = np.full_like(fifo_basin_trace, -1)
    scheduled_count = np.zeros((width, HORIZON), dtype=np.int64)
    delivered_trace = np.zeros((width, HORIZON, 2, 3), dtype=np.int64)
    metrics_trace = np.zeros((width, HORIZON, 8), dtype=np.int64)
    previous_action_trace = np.full(
        (width, HORIZON, MAX_AGENTS), -1, dtype=np.int64
    )
    previous_success_trace = np.zeros_like(previous_action_trace)
    snapshot_digest = np.zeros((width, HORIZON), dtype=np.uint64)
    origin_slot = episode.selector_slot.copy()
    origin_agent = np.zeros((width, 3), dtype=np.int64)
    origin_snapshot_digest = np.zeros((width, 3), dtype=np.uint64)
    terminal_return = np.zeros(width, dtype=np.float64)
    final_delivered = np.zeros((width, 2), dtype=np.int64)
    final_metrics = np.zeros((width, 8), dtype=np.int64)
    common_tape_digest = np.zeros(width, dtype=np.uint64)
    trajectory_digest = np.zeros(width, dtype=np.uint64)
    active = episode.n_agents != 0

    for lane in np.flatnonzero(active):
        lane = int(lane)
        n_agents = int(episode.n_agents[lane])
        roles = episode.roles[lane, :n_agents].copy()
        fifo_basin = np.full((n_agents, FIFO_CAPACITY), -1, dtype=np.int64)
        fifo_ordinal = np.full_like(fifo_basin, -1)
        fifo_birth = np.full_like(fifo_basin, -1)
        delivered = np.zeros((2, 3), dtype=np.int64)
        metrics = np.zeros(8, dtype=np.int64)
        previous_action = np.full(n_agents, -1, dtype=np.int64)
        previous_success = np.zeros(n_agents, dtype=np.int64)
        hidden = np.zeros((n_agents, HIDDEN_DIM), dtype=np.float64)
        scheduled: list[_Scheduled] = []
        for slot in range(HORIZON):
            if slot > 0:
                _process_arrivals(
                    scheduled,
                    slot,
                    fifo_basin,
                    fifo_ordinal,
                    fifo_birth,
                    roles,
                    delivered,
                    metrics,
                    previous_success,
                )
                _purge_expired(
                    fifo_basin, fifo_ordinal, fifo_birth, roles, n_agents, slot
                )
            if scheduled:
                raise AssertionError("latency-one reset trajectory retained a pending predecision arrival")
            obs = _observations(
                slot, n_agents, roles, fifo_birth, previous_action, previous_success
            )
            incoming = hidden.copy()
            (
                actions,
                hidden,
                slot_messages,
                probabilities,
                summaries,
                slot_denominators,
            ) = _policy_step(
                obs,
                hidden,
                roles,
                parameters,
                episode.action_uniform[lane, slot, :n_agents],
                mode=mode,
            )
            observations[lane, slot, :n_agents] = obs
            messages[lane, slot, :n_agents] = slot_messages
            role_summaries[lane, slot, :n_agents] = summaries
            denominators[lane, slot, :n_agents] = slot_denominators
            incoming_hidden[lane, slot, :n_agents] = incoming
            post_gru_hidden[lane, slot, :n_agents] = hidden
            legal_probabilities[lane, slot, :n_agents] = probabilities
            factual_actions[lane, slot, :n_agents] = actions
            fifo_basin_trace[lane, slot, :n_agents] = fifo_basin
            fifo_ordinal_trace[lane, slot, :n_agents] = fifo_ordinal
            fifo_birth_trace[lane, slot, :n_agents] = fifo_birth
            delivered_trace[lane, slot] = delivered
            metrics_trace[lane, slot] = metrics
            previous_action_trace[lane, slot, :n_agents] = previous_action
            previous_success_trace[lane, slot, :n_agents] = previous_success
            snapshot_digest[lane, slot] = np.uint64(
                _trace_snapshot_digest(
                    slot,
                    roles,
                    fifo_basin,
                    fifo_ordinal,
                    fifo_birth,
                    delivered,
                    metrics,
                    previous_action,
                    previous_success,
                    episode.event_schedule[lane],
                    obs,
                    slot_messages,
                    summaries,
                    slot_denominators,
                    incoming,
                    hidden,
                    probabilities,
                    actions,
                )
            )
            previous_action[:] = actions
            previous_success[:] = 0
            _schedule_radio(
                slot,
                actions,
                n_agents,
                roles,
                fifo_basin,
                fifo_ordinal,
                fifo_birth,
                delivered,
                metrics,
                scheduled,
                episode.uplink_uniform[lane, slot],
                episode.base_uniform[lane, slot],
            )
            _scan(
                slot,
                actions,
                n_agents,
                roles,
                fifo_basin,
                fifo_ordinal,
                fifo_birth,
                episode.event_schedule[lane],
                episode.detection_uniform[lane, slot],
            )
        terminal_return[lane] = _terminal(delivered, metrics)
        final_delivered[lane] = delivered.sum(axis=1)
        final_metrics[lane] = metrics
        common_tape_digest[lane] = np.uint64(
            _episode_common_tape_digest(episode, lane, n_agents)
        )
        digest = _fnv_u64(_FNV_OFFSET, int(common_tape_digest[lane]))
        digest = _fnv_i64(digest, 0 if mode == MODE_INTACT else 1)
        for value in snapshot_digest[lane]:
            digest = _fnv_u64(digest, int(value))
        digest = _fnv_f64(digest, float(terminal_return[lane]))
        trajectory_digest[lane] = np.uint64(digest)
        per_role = n_agents // 3
        for role in range(3):
            origin_agent[lane, role] = role * per_role + int(
                episode.selector_local_index[lane, role]
            )
            origin_snapshot_digest[lane, role] = snapshot_digest[
                lane, origin_slot[lane, role]
            ]
    return FactualTrajectory(
        observations=observations,
        messages=messages,
        role_summaries=role_summaries,
        denominators=denominators,
        incoming_hidden=incoming_hidden,
        post_gru_hidden=post_gru_hidden,
        legal_probabilities=legal_probabilities,
        factual_actions=factual_actions,
        fifo_basin=fifo_basin_trace,
        fifo_ordinal=fifo_ordinal_trace,
        fifo_birth=fifo_birth_trace,
        scheduled_count=scheduled_count,
        delivered=delivered_trace,
        metrics=metrics_trace,
        previous_action=previous_action_trace,
        previous_success=previous_success_trace,
        snapshot_digest=snapshot_digest,
        origin_slot=origin_slot,
        origin_agent=origin_agent,
        origin_snapshot_digest=origin_snapshot_digest,
        terminal_return=terminal_return,
        final_delivered=final_delivered,
        final_metrics=final_metrics,
        common_tape_digest=common_tape_digest,
        trajectory_digest=trajectory_digest,
        active=active,
        parameter_digest=parameters.digest,
        mode=mode,
    )


def python_shadow_trajectory(
    episode: FactualEpisodeBatch,
    intact: FactualTrajectory,
    parameters: ActorParameters,
) -> ShadowTrajectory:
    """One-step rotated-summary update on fixed intact observations/hidden."""

    validate_factual_episode_batch(episode)
    if intact.mode != MODE_INTACT:
        raise ValueError("shadow input must be the intact factual trajectory")
    width = episode.width
    summaries = np.zeros_like(intact.role_summaries)
    denominators = np.zeros_like(intact.denominators)
    post_hidden = np.zeros_like(intact.post_gru_hidden)
    probabilities = np.zeros_like(intact.legal_probabilities)
    digest = np.zeros((width, HORIZON), dtype=np.uint64)
    for lane in np.flatnonzero(intact.active):
        lane = int(lane)
        n = int(episode.n_agents[lane])
        roles = episode.roles[lane, :n]
        for slot in range(HORIZON):
            _, hidden, _, probs, slot_summaries, slot_denominators = _policy_step(
                intact.observations[lane, slot, :n],
                intact.incoming_hidden[lane, slot, :n],
                roles,
                parameters,
                episode.action_uniform[lane, slot, :n],
                mode=MODE_FULL_ROTATED,
                messages_override=intact.messages[lane, slot, :n],
            )
            summaries[lane, slot, :n] = slot_summaries
            denominators[lane, slot, :n] = slot_denominators
            post_hidden[lane, slot, :n] = hidden
            probabilities[lane, slot, :n] = probs
            value = _fnv_u64(_FNV_OFFSET, int(intact.snapshot_digest[lane, slot]))
            for array in (slot_summaries, slot_denominators, hidden, probs):
                for item in array.ravel():
                    value = _fnv_canonical_f64(value, float(item))
            digest[lane, slot] = np.uint64(value)
    return ShadowTrajectory(
        role_summaries=summaries,
        denominators=denominators,
        post_gru_hidden=post_hidden,
        legal_probabilities=probabilities,
        snapshot_digest=digest,
        active=intact.active.copy(),
        parameter_digest=parameters.digest,
    )


def python_full_suffix(batch: SuffixBatch, parameters: ActorParameters) -> NativeSuffixResult:
    """Run the independent TEST oracle; never use this as a production fallback."""

    validate_suffix_batch(batch)
    validate_actor_parameters(parameters)
    width = batch.width
    terminal = np.zeros(width, dtype=np.float64)
    final_delivered = np.zeros((width, 2), dtype=np.int64)
    final_metrics = np.zeros((width, 8), dtype=np.int64)
    counters = np.zeros((width, 4), dtype=np.int64)
    common_digest = np.zeros(width, dtype=np.uint64)
    audit_digest = np.zeros(width, dtype=np.uint64)
    factual_candidate = np.zeros(width, dtype=np.bool_)
    factual_identity = np.zeros(width, dtype=np.bool_)
    active = batch.n_agents != 0
    for lane in np.flatnonzero(active):
        (
            terminal[lane],
            final_delivered[lane],
            final_metrics[lane],
            counters[lane],
            common_digest[lane],
            audit_digest[lane],
            factual_candidate[lane],
            factual_identity[lane],
        ) = _run_lane(batch, parameters, int(lane))
    return NativeSuffixResult(
        terminal_target=terminal,
        final_delivered=final_delivered,
        final_metrics=final_metrics,
        counters=counters,
        common_tape_digest=common_digest,
        audit_digest=audit_digest,
        factual_suffix_candidate=factual_candidate,
        factual_suffix_identity=factual_identity,
        active=active,
        parameter_digest=parameters.digest,
    )


def _assert_equal(reference: NativeSuffixResult, candidate: NativeSuffixResult) -> None:
    for name in (
        "terminal_target",
        "final_delivered",
        "final_metrics",
        "counters",
        "common_tape_digest",
        "audit_digest",
        "factual_suffix_candidate",
        "factual_suffix_identity",
        "active",
    ):
        left = getattr(reference, name)
        right = getattr(candidate, name)
        if not np.array_equal(left, right):
            mismatch = np.argwhere(left != right)
            raise AssertionError(f"native/oracle mismatch in {name} at {mismatch[:8].tolist()}")
    if reference.parameter_digest != candidate.parameter_digest:
        raise AssertionError("native/oracle parameter digest mismatch")


def _assert_factual_trace_equivalent(
    reference: FactualTrajectory,
    candidate: FactualTrajectory,
    *,
    reorder: np.ndarray | None = None,
) -> float:
    exact_fields = (
        "factual_actions",
        "fifo_basin",
        "fifo_ordinal",
        "fifo_birth",
        "scheduled_count",
        "delivered",
        "metrics",
        "previous_action",
        "previous_success",
        "snapshot_digest",
        "origin_slot",
        "origin_agent",
        "origin_snapshot_digest",
        "terminal_return",
        "final_delivered",
        "final_metrics",
        "common_tape_digest",
        "trajectory_digest",
        "active",
    )
    float_fields = (
        "observations",
        "messages",
        "role_summaries",
        "denominators",
        "incoming_hidden",
        "post_gru_hidden",
        "legal_probabilities",
    )
    maximum = 0.0
    for name in exact_fields:
        right = getattr(candidate, name)
        if reorder is not None:
            right = right[reorder]
        if not np.array_equal(getattr(reference, name), right):
            raise AssertionError(f"factual trace mismatch in {name}")
    for name in float_fields:
        right = getattr(candidate, name)
        if reorder is not None:
            right = right[reorder]
        left = getattr(reference, name)
        difference = float(np.max(np.abs(left - right)))
        maximum = max(maximum, difference)
        if not np.allclose(left, right, rtol=0.0, atol=5e-14):
            raise AssertionError(f"factual trace numerical mismatch in {name}: {difference}")
    if reference.parameter_digest != candidate.parameter_digest or reference.mode != candidate.mode:
        raise AssertionError("factual trace identity mismatch")
    return maximum


def _assert_shadow_equivalent(
    reference: ShadowTrajectory, candidate: ShadowTrajectory
) -> float:
    if not np.array_equal(reference.snapshot_digest, candidate.snapshot_digest):
        raise AssertionError("shadow snapshot digest mismatch")
    if not np.array_equal(reference.active, candidate.active):
        raise AssertionError("shadow active mask mismatch")
    maximum = 0.0
    for name in (
        "role_summaries",
        "denominators",
        "post_gru_hidden",
        "legal_probabilities",
    ):
        difference = float(np.max(np.abs(getattr(reference, name) - getattr(candidate, name))))
        maximum = max(maximum, difference)
        if not np.allclose(getattr(reference, name), getattr(candidate, name), rtol=0.0, atol=5e-14):
            raise AssertionError(f"shadow numerical mismatch in {name}: {difference}")
    return maximum


def run_gate_a_self_check(
    widths: Iterable[int] = (32, 64, 128, 256),
    repetitions: int = 3,
) -> dict[str, object]:
    """Reaccept V3 factual trace, evaluation surfaces and suffix host."""

    from dataclasses import fields as dataclass_fields
    from .native_contract import suffix_batch_from_factual_trajectory
    from .native_loader import (
        load_native_host,
        native_factual_trajectory,
        native_full_suffix,
        native_shadow_trajectory,
    )

    if repetitions < 2:
        raise ValueError("repetitions must be at least two")
    parameters = make_test_actor_parameters()
    identity = load_native_host()
    records: dict[str, object] = {}
    concurrency_batch: SuffixBatch | None = None
    concurrency_reference: NativeSuffixResult | None = None
    for width_value in widths:
        width = int(width_value)
        episode = make_test_factual_episode_batch(width)
        intact_oracle = python_factual_trajectory(episode, parameters, mode=MODE_INTACT)
        intact_native = native_factual_trajectory(
            episode, parameters, mode=MODE_INTACT, identity=identity
        )
        intact_error = _assert_factual_trace_equivalent(intact_oracle, intact_native)
        if np.any(intact_native.scheduled_count[intact_native.active] != 0):
            raise AssertionError("pretransition factual snapshot retained scheduled arrivals")
        for lane in np.flatnonzero(intact_native.active):
            for role in range(3):
                slot = int(intact_native.origin_slot[lane, role])
                if (
                    intact_native.origin_snapshot_digest[lane, role]
                    != intact_native.snapshot_digest[lane, slot]
                ):
                    raise AssertionError("selector origin detached from factual slot snapshot")

        rotated_oracle = python_factual_trajectory(
            episode, parameters, mode=MODE_FULL_ROTATED
        )
        rotated_native = native_factual_trajectory(
            episode, parameters, mode=MODE_FULL_ROTATED, identity=identity
        )
        rotated_error = _assert_factual_trace_equivalent(
            rotated_oracle, rotated_native
        )
        if not np.array_equal(
            intact_native.common_tape_digest, rotated_native.common_tape_digest
        ):
            raise AssertionError("FULL_ROTATED changed common potential tapes")
        if not np.array_equal(intact_native.observations[:, 0], rotated_native.observations[:, 0]):
            raise AssertionError("FULL_ROTATED changed reset observations")

        shadow_oracle = python_shadow_trajectory(episode, intact_native, parameters)
        shadow_native = native_shadow_trajectory(
            episode, intact_native, parameters, identity=identity
        )
        shadow_error = _assert_shadow_equivalent(shadow_oracle, shadow_native)

        order = np.arange(width - 1, -1, -1)
        reversed_arrays: dict[str, np.ndarray] = {}
        for field in dataclass_fields(episode):
            value = np.ascontiguousarray(getattr(episode, field.name)[order])
            value.setflags(write=False)
            reversed_arrays[field.name] = value
        reversed_episode = FactualEpisodeBatch(**reversed_arrays)
        reversed_native = native_factual_trajectory(
            reversed_episode, parameters, mode=MODE_INTACT, identity=identity
        )
        _assert_factual_trace_equivalent(
            intact_native, reversed_native, reorder=order
        )

        batch = suffix_batch_from_factual_trajectory(
            episode, intact_native, np.arange(width, dtype=np.int64) % 3
        )
        factual_batch = with_factual_actions(batch)
        factual_reference = python_full_suffix(factual_batch, parameters)
        factual_native = native_full_suffix(
            factual_batch, parameters, identity=identity
        )
        _assert_equal(factual_reference, factual_native)
        if not np.array_equal(
            factual_native.terminal_target, intact_native.terminal_return
        ) or not bool(factual_native.factual_suffix_identity[factual_native.active].all()):
            raise AssertionError("trace-derived factual suffix identity failed")

        reference = python_full_suffix(batch, parameters)
        native = native_full_suffix(batch, parameters, identity=identity)
        _assert_equal(reference, native)
        observed_nonfactual: list[set[int]] = [set() for _ in range(width)]
        for alternative_offset in (1, 2, 3):
            alternative_batch = suffix_batch_from_factual_trajectory(
                episode,
                intact_native,
                np.arange(width, dtype=np.int64) % 3,
                alternative_offset=alternative_offset,
            )
            alternative_reference = python_full_suffix(alternative_batch, parameters)
            alternative_native = native_full_suffix(
                alternative_batch, parameters, identity=identity
            )
            _assert_equal(alternative_reference, alternative_native)
            if not np.array_equal(
                native.common_tape_digest, alternative_native.common_tape_digest
            ):
                raise AssertionError("nonfactual action changed common tape identity")
            for lane in np.flatnonzero(batch.n_agents):
                focal = int(alternative_batch.focal_agent[lane])
                action = int(alternative_batch.focal_intervention[lane])
                factual = int(alternative_batch.factual_joint_action[lane, focal])
                if action != factual:
                    observed_nonfactual[int(lane)].add(action)
        for lane in np.flatnonzero(batch.n_agents):
            focal = int(batch.focal_agent[lane])
            role = int(batch.roles[lane, focal])
            factual = int(batch.factual_joint_action[lane, focal])
            if observed_nonfactual[int(lane)] != set(LEGAL_ACTIONS[role]) - {factual}:
                raise AssertionError("incomplete legal nonfactual coverage")

        if concurrency_batch is None:
            concurrency_batch = batch
            concurrency_reference = reference

        python_suffix_times: list[float] = []
        native_suffix_times: list[float] = []
        python_trace_times: list[float] = []
        native_trace_times: list[float] = []
        python_full_suffix(batch, parameters)
        native_full_suffix(batch, parameters, identity=identity)
        python_factual_trajectory(episode, parameters, mode=MODE_INTACT)
        native_factual_trajectory(
            episode, parameters, mode=MODE_INTACT, identity=identity
        )
        for repetition in range(repetitions):
            order_labels = ("python", "native") if repetition % 2 == 0 else ("native", "python")
            for label in order_labels:
                started = time.perf_counter()
                if label == "python":
                    python_full_suffix(batch, parameters)
                    python_suffix_times.append(time.perf_counter() - started)
                else:
                    native_full_suffix(batch, parameters, identity=identity)
                    native_suffix_times.append(time.perf_counter() - started)
            for label in order_labels:
                started = time.perf_counter()
                if label == "python":
                    python_factual_trajectory(episode, parameters, mode=MODE_INTACT)
                    python_trace_times.append(time.perf_counter() - started)
                else:
                    native_factual_trajectory(
                        episode, parameters, mode=MODE_INTACT, identity=identity
                    )
                    native_trace_times.append(time.perf_counter() - started)
        suffix_speedup = float(np.median(python_suffix_times) / np.median(native_suffix_times))
        trace_speedup = float(np.median(python_trace_times) / np.median(native_trace_times))
        if suffix_speedup < 2.0 or trace_speedup < 2.0:
            raise AssertionError(
                f"width {width}: suffix={suffix_speedup:.6f}x trace={trace_speedup:.6f}x"
            )
        records[str(width)] = {
            "suffix_paired_warm_speedup": suffix_speedup,
            "factual_trace_paired_warm_speedup": trace_speedup,
            "intact_float_max_abs_error": intact_error,
            "full_rotated_float_max_abs_error": rotated_error,
            "shadow_float_max_abs_error": shadow_error,
            "categorical_terminal_digest_exact": True,
            "three_origins_same_factual_episode": True,
            "factual_suffix_identity": True,
            "all_nonfactual_legal_actions": True,
            "common_tape_across_actions_and_modes": True,
            "reverse_order_independence": True,
        }

    assert concurrency_batch is not None and concurrency_reference is not None
    concurrency: dict[str, object] = {}
    for workers in (1, 2, 4):
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(
                executor.map(
                    lambda _: native_full_suffix(
                        concurrency_batch, parameters, identity=identity
                    ),
                    range(workers),
                )
            )
        for result in results:
            _assert_equal(concurrency_reference, result)
        concurrency[str(workers)] = {
            "elapsed_seconds": time.perf_counter() - started,
            "exact": True,
        }
    return {
        "abi_version": ABI_VERSION,
        "native_threads": NATIVE_THREADS,
        "identity": identity.as_dict(),
        "widths": records,
        "concurrency": concurrency,
    }
