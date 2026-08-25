"""Deterministic scalar full-suffix reference for the TEST-only Gate A host.

This is intentionally not the r03 runner and imports neither Torch nor any
production authorization surface.  It preserves the engineering shape needed
for Gate A: N=9/15 balanced public roles, r03 legal masks, an origin-time
focal intervention, teammate factual action identity at that time, a mutable
FIFO/radio/delivery world, and closed-loop future action selection driven by
materialized tapes and recurrent-shaped fixture state.
"""

from __future__ import annotations

from typing import Final

import numpy as np

from .contract import FIFO_CAPACITY, HIDDEN_DIM, HORIZON, MAX_AGENTS, TAPE_MODULUS, legal_actions, validate_fixture_batch


_MASK64: Final = (1 << 64) - 1
_DIGEST_MULTIPLIER: Final = 1_000_003
_REPORT_LIFETIME: Final = 4


def _fixture_word(case: int, *parts: int) -> int:
    """A literal fixture formula, deliberately unrelated to a seed namespace."""
    value = (case * 131 + 17) & 0xFFFFFFFF
    for part in parts:
        value = (value * 65537 + int(part) * 257 + 97) & 0xFFFFFFFF
    return value


def _fixture_tape(case: int, shape: tuple[int, ...], salt: int) -> np.ndarray:
    values = np.empty(shape, dtype=np.uint32)
    for flat_index in range(values.size):
        values.flat[flat_index] = _fixture_word(case, salt, flat_index) % TAPE_MODULUS
    return values


def make_fixture_batch(width: int, case_offset: int = 0) -> dict[str, np.ndarray]:
    """Materialize canonical Gate A fixture lanes without any scientific ID.

    ``case_offset`` only selects deterministic test cases.  It is not a seed,
    coordinate, panel row, initialization, or rollout identifier.
    """
    if width not in (32, 64, 128, 256):
        raise ValueError(f"unsupported Gate A fixture width: {width}")
    if not isinstance(case_offset, int):
        raise TypeError("case_offset must be an int")

    batch = {
        "n_agents": np.empty((width,), dtype=np.int32),
        "roles": np.full((width, MAX_AGENTS), -1, dtype=np.int32),
        "origin_slot": np.empty((width,), dtype=np.int32),
        "focal_index": np.empty((width,), dtype=np.int32),
        "forced_action": np.empty((width,), dtype=np.int32),
        "factual_actions": np.full((width, MAX_AGENTS), -1, dtype=np.int32),
        "initial_fifo_basin": np.full((width, MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int32),
        "initial_fifo_time": np.full((width, MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int32),
        "initial_previous_action": np.full((width, MAX_AGENTS), -1, dtype=np.int32),
        "initial_previous_success": np.zeros((width, MAX_AGENTS), dtype=np.int32),
        "initial_hidden": np.zeros((width, MAX_AGENTS, HIDDEN_DIM), dtype=np.float64),
        "event_times": np.empty((width, 2, 3), dtype=np.int32),
        "action_tape": np.empty((width, HORIZON, MAX_AGENTS), dtype=np.uint32),
        "detection_tape": np.empty((width, HORIZON, 2, 5), dtype=np.uint32),
        "uplink_tape": np.empty((width, HORIZON, MAX_AGENTS), dtype=np.uint32),
        "base_tape": np.empty((width, HORIZON, MAX_AGENTS), dtype=np.uint32),
    }
    for lane in range(width):
        case = case_offset + lane
        n = 9 if case % 2 == 0 else 15
        multiplicity = n // 3
        batch["n_agents"][lane] = n
        batch["roles"][lane, :n] = np.repeat(np.arange(3, dtype=np.int32), multiplicity)
        batch["origin_slot"][lane] = case % HORIZON
        focal = _fixture_word(case, 1) % n
        role = int(batch["roles"][lane, focal])
        batch["focal_index"][lane] = focal
        legal = legal_actions(role)
        batch["forced_action"][lane] = legal[_fixture_word(case, 2) % len(legal)]
        for agent in range(n):
            agent_role = int(batch["roles"][lane, agent])
            agent_legal = legal_actions(agent_role)
            batch["factual_actions"][lane, agent] = agent_legal[_fixture_word(case, 3, agent) % len(agent_legal)]
            batch["initial_previous_action"][lane, agent] = -1 if (case + agent) % 5 == 0 else agent_legal[_fixture_word(case, 4, agent) % len(agent_legal)]
            batch["initial_previous_success"][lane, agent] = _fixture_word(case, 5, agent) & 1
            for component in range(HIDDEN_DIM):
                # Binary fractions preserve exact code recovery across Python/C++.
                batch["initial_hidden"][lane, agent, component] = ((_fixture_word(case, 6, agent, component) % 65) - 32) / 64.0
            capacity = 4 if agent_role == 2 else 2
            payload_count = _fixture_word(case, 7, agent) % (capacity + 1)
            for position in range(payload_count):
                batch["initial_fifo_basin"][lane, agent, position] = _fixture_word(case, 8, agent, position) % 2
                batch["initial_fifo_time"][lane, agent, position] = _fixture_word(case, 9, agent, position) % (int(batch["origin_slot"][lane]) + 1)
        for basin in range(2):
            # The three fixture events remain in the actual r03 [0, 7] support.
            selected: list[int] = []
            for candidate in range(32):
                value = _fixture_word(case, 10, basin, candidate) % 8
                if value not in selected:
                    selected.append(value)
                if len(selected) == 3:
                    break
            if len(selected) != 3:
                raise AssertionError("fixture event formula must supply three support points")
            batch["event_times"][lane, basin] = np.asarray(sorted(selected), dtype=np.int32)
        batch["action_tape"][lane] = _fixture_tape(case, (HORIZON, MAX_AGENTS), 11)
        batch["detection_tape"][lane] = _fixture_tape(case, (HORIZON, 2, 5), 12)
        batch["uplink_tape"][lane] = _fixture_tape(case, (HORIZON, MAX_AGENTS), 13)
        batch["base_tape"][lane] = _fixture_tape(case, (HORIZON, MAX_AGENTS), 14)
    validate_fixture_batch(batch, width)
    return batch


def _digest_step(digest: int, value: int) -> int:
    return (digest * _DIGEST_MULTIPLIER + (int(value) & _MASK64) + 97) & _MASK64


def _append_fifo(fifo: list[tuple[int, int, int]], report: tuple[int, int, int], capacity: int) -> None:
    fifo.append(report)
    if len(fifo) > capacity:
        fifo.pop(0)


def _policy_action(
    *, role: int, slot: int, fifo_count: int, previous_action: int, previous_success: int,
    hidden: np.ndarray, action_word: int,
) -> int:
    """Fixture closed-loop policy: legal-mask support plus recurrent-shaped state.

    The numerical rule is intentionally integer/binary-fraction based so the
    two hosts can establish bit-exact categorical outputs without relying on a
    BLAS, Torch, or a learned parameter object.
    """
    legal = legal_actions(role)
    hidden_code = int(round(float(hidden[role * 7 % HIDDEN_DIM]) * 64.0))
    total = 0
    weights: list[int] = []
    for action in legal:
        weight = 1 + ((role * 17 + action * 23 + slot * 7 + fifo_count * 11 + (previous_action + 1) * 3 + previous_success * 5 + hidden_code) % 31)
        weights.append(weight)
        total += weight
    needle = int(action_word) % total
    for action, weight in zip(legal, weights):
        if needle < weight:
            return action
        needle -= weight
    raise AssertionError("nonempty legal policy support must select an action")


def _advance_hidden(hidden: np.ndarray, *, slot: int, role: int, action: int, fifo_count: int, success: int) -> None:
    for component in range(HIDDEN_DIM):
        prior_code = int(round(float(hidden[component]) * 64.0))
        injection = ((slot + 1) * 3 + role * 5 + action * 7 + fifo_count * 11 + success * 13 + component) % 65 - 32
        # Both operands are multiples of 1/64; result is a binary fraction.
        hidden[component] = (prior_code + injection) / 128.0


def _run_lane(batch: dict[str, np.ndarray], lane: int) -> tuple[float, int, int, int, int, int, int, int]:
    n = int(batch["n_agents"][lane])
    roles = [int(value) for value in batch["roles"][lane, :n]]
    slot = int(batch["origin_slot"][lane])
    focal = int(batch["focal_index"][lane])
    forced = int(batch["forced_action"][lane])
    hidden = np.array(batch["initial_hidden"][lane, :n], dtype=np.float64, copy=True)
    previous_action = [int(value) for value in batch["initial_previous_action"][lane, :n]]
    previous_success = [int(value) for value in batch["initial_previous_success"][lane, :n]]
    fifo: list[list[tuple[int, int, int]]] = [[] for _ in range(n)]
    for agent in range(n):
        for position in range(FIFO_CAPACITY):
            basin = int(batch["initial_fifo_basin"][lane, agent, position])
            if basin >= 0:
                fifo[agent].append((basin, position, int(batch["initial_fifo_time"][lane, agent, position])))
    events = [[int(value) for value in row] for row in batch["event_times"][lane]]
    scheduled_uplinks: list[tuple[int, int, tuple[int, int, int], tuple[int, ...], tuple[int, ...]]] = []
    scheduled_base: list[tuple[int, int, tuple[int, int, int]]] = []
    delivered: set[tuple[int, int]] = set()
    delivered_by_basin = [0, 0]
    radio = waste = deliveries = scans = 0
    digest = 1469598103934665603
    transitions = decisions = 0

    def prepare(current_slot: int) -> None:
        nonlocal scheduled_uplinks, scheduled_base, waste, deliveries
        success = [0] * n
        uplink_acks: list[tuple[int, int, tuple[int, int, int], tuple[int, ...], tuple[int, ...]]] = []
        future_uplinks: list[tuple[int, int, tuple[int, int, int], tuple[int, ...], tuple[int, ...]]] = []
        for scheduled in scheduled_uplinks:
            if scheduled[0] != current_slot:
                future_uplinks.append(scheduled)
                continue
            _, sender, report, listeners, decoded = scheduled
            for receiver in decoded:
                if current_slot < report[2] + _REPORT_LIFETIME:
                    _append_fifo(fifo[receiver], report, 4)
                    success[receiver] = 1
                    success[sender] = 1
            uplink_acks.append(scheduled)
        scheduled_uplinks = future_uplinks
        base_acks: list[tuple[int, int, tuple[int, int, int]]] = []
        future_base: list[tuple[int, int, tuple[int, int, int]]] = []
        for scheduled in scheduled_base:
            if scheduled[0] != current_slot:
                future_base.append(scheduled)
                continue
            _, sender, report = scheduled
            key = (report[0], report[1])
            if current_slot < report[2] + _REPORT_LIFETIME and key not in delivered:
                delivered.add(key)
                delivered_by_basin[report[0]] += 1
                deliveries += 1
                success[sender] = 1
            base_acks.append(scheduled)
        scheduled_base = future_base
        for _, sender, _, listeners, _ in uplink_acks:
            if fifo[sender]:
                fifo[sender].pop(0)
            if not success[sender]:
                waste += 1
            for listener in listeners:
                if not success[listener]:
                    waste += 1
        for _, sender, _ in base_acks:
            if fifo[sender]:
                fifo[sender].pop(0)
            if not success[sender]:
                waste += 1
        for agent in range(n):
            fifo[agent][:] = [report for report in fifo[agent] if current_slot < report[2] + _REPORT_LIFETIME]
            previous_success[agent] = success[agent]

    for current_slot in range(slot, HORIZON):
        prepare(current_slot)
        if current_slot == slot:
            actions = [int(value) for value in batch["factual_actions"][lane, :n]]
            actions[focal] = forced
        else:
            actions = []
            for agent in range(n):
                action = _policy_action(
                    role=roles[agent], slot=current_slot, fifo_count=len(fifo[agent]),
                    previous_action=previous_action[agent], previous_success=previous_success[agent],
                    hidden=hidden[agent], action_word=int(batch["action_tape"][lane, current_slot, agent]),
                )
                actions.append(action)
        decisions += n
        for action in actions:
            digest = _digest_step(digest, (current_slot << 8) | action)

        # Radio resolution preserves r03 public role/action masks and one-slot arrival.
        for basin in (0, 1):
            sender_role, listen_action = basin, 2 + basin
            uplinks = [agent for agent in range(n) if roles[agent] == sender_role and actions[agent] == 1]
            nonempty = [agent for agent in uplinks if fifo[agent]]
            listeners = [agent for agent in range(n) if roles[agent] == 2 and actions[agent] == listen_action]
            radio += len(uplinks) + len(listeners)
            waste += len(uplinks) - len(nonempty)
            if len(nonempty) >= 2:
                waste += len(nonempty) + len(listeners)
            elif nonempty and current_slot + 1 < HORIZON:
                sender = nonempty[0]
                report = fifo[sender][0]
                threshold = 4_800 + 400 * basin
                decoded = tuple(receiver for receiver in listeners if int(batch["uplink_tape"][lane, current_slot, receiver]) < threshold)
                if decoded:
                    scheduled_uplinks.append((current_slot + 1, sender, report, tuple(listeners), decoded))
                else:
                    waste += len(nonempty) + len(listeners)
            else:
                waste += len(nonempty) + len(listeners)

        forwards = [agent for agent in range(n) if roles[agent] == 2 and actions[agent] == 4]
        nonempty_forwards = [agent for agent in forwards if fifo[agent]]
        radio += len(forwards)
        waste += len(forwards) - len(nonempty_forwards)
        if len(nonempty_forwards) >= 2:
            waste += len(nonempty_forwards)
        elif nonempty_forwards and current_slot + 1 < HORIZON:
            sender = nonempty_forwards[0]
            if int(batch["base_tape"][lane, current_slot, sender]) < 9_000:
                scheduled_base.append((current_slot + 1, sender, fifo[sender][0]))
            else:
                waste += 1
        else:
            waste += len(nonempty_forwards)

        for basin in (0, 1):
            if current_slot not in events[basin]:
                continue
            ordinal = events[basin].index(current_slot)
            for agent in range(n):
                if roles[agent] == basin and actions[agent] == 0:
                    scans += 1
                    local_index = agent % (n // 3)
                    if int(batch["detection_tape"][lane, current_slot, basin, local_index]) < 7_500:
                        _append_fifo(fifo[agent], (basin, ordinal, current_slot), 2)

        for agent in range(n):
            _advance_hidden(
                hidden[agent], slot=current_slot, role=roles[agent], action=actions[agent],
                fifo_count=len(fifo[agent]), success=previous_success[agent],
            )
            previous_action[agent] = actions[agent]
            previous_success[agent] = 0
        transitions += 1

    if scheduled_uplinks or scheduled_base:
        raise RuntimeError("fixture suffix left a post-horizon scheduled arrival")
    for metric in (radio, waste, deliveries, scans, transitions, decisions):
        digest = _digest_step(digest, metric)
    hidden_code_sum = sum(int(round(float(value) * 128.0)) for value in hidden.ravel())
    digest = _digest_step(digest, hidden_code_sum)
    return_micros = (650_000 * sum(delivered_by_basin)) // 6 + (250_000 * min(delivered_by_basin)) // 3
    return_micros += 100_000 if radio == 0 else (100_000 * max(0, radio - waste)) // radio
    return (
        float(return_micros) / 1_000_000.0, digest, transitions, decisions,
        deliveries, waste, scans, hidden_code_sum,
    )


def python_suffix_batch(batch: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Run every materialized fixture lane through the scalar suffix oracle."""
    validate_fixture_batch(batch)
    width = int(batch["n_agents"].shape[0])
    output = {
        "terminal_return": np.empty((width,), dtype=np.float64),
        "audit_digest": np.empty((width,), dtype=np.uint64),
        "transition_count": np.empty((width,), dtype=np.int32),
        "decision_count": np.empty((width,), dtype=np.int32),
        "delivery_count": np.empty((width,), dtype=np.int32),
        "waste_count": np.empty((width,), dtype=np.int32),
        "scan_count": np.empty((width,), dtype=np.int32),
        "hidden_code_sum": np.empty((width,), dtype=np.int64),
        "forced_action_count": np.ones((width,), dtype=np.int32),
        "factual_teammate_count": batch["n_agents"].astype(np.int32, copy=True) - 1,
    }
    for lane in range(width):
        value, digest, transitions, decisions, deliveries, waste, scans, hidden_code_sum = _run_lane(batch, lane)
        output["terminal_return"][lane] = value
        output["audit_digest"][lane] = np.uint64(digest)
        output["transition_count"][lane] = transitions
        output["decision_count"][lane] = decisions
        output["delivery_count"][lane] = deliveries
        output["waste_count"][lane] = waste
        output["scan_count"][lane] = scans
        output["hidden_code_sum"][lane] = hidden_code_sum
    return output
