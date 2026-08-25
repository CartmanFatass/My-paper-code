"""Exact event/FIFO/channel simulator and 22-field observation firewall."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

import torch

from .authorization import ProductionPermit
from .config import (
    BASE_P0, Basin, Action, DETECTION_PROBABILITY, EVENTS_PER_BASIN,
    EVENT_TIME_SUPPORT, HORIZON, LOAD_LOGIT_SLOPE, OBSERVATION_DIM, P0,
    RELAY_FIFO_CAPACITY, REPORT_LIFETIME, Role, SURVEYOR_FIFO_CAPACITY,
    TRAINING_DTYPE, legal_action_indices, validate_roster,
)
from .rng import Coordinate, CounterRNG


def _require_local_permit(permit: ProductionPermit, seed: int | None = None) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("validated ProductionPermit is required")
    permit.assert_local_validity()
    if seed is not None and seed not in permit.payload["authorized_seeds"]:
        raise PermissionError("seed is outside the frozen registered panel")


def _loaded_probability(p0: float, sender_count: int) -> float:
    logit = math.log(p0) - math.log1p(-p0)
    return 1.0 / (1.0 + math.exp(-(logit - LOAD_LOGIT_SLOPE * (sender_count - 1))))


@dataclass(frozen=True)
class Report:
    basin: Basin
    event_ordinal: int
    event_time: int

    @property
    def event_id(self) -> tuple[int, int]:
        return (int(self.basin), self.event_ordinal)


@dataclass
class AgentState:
    role: Role
    role_local_index: int
    capacity: int
    fifo: list[Report] = field(default_factory=list)
    previous_action: int | None = None
    previous_success: bool = False

    def append(self, report: Report) -> None:
        self.fifo.append(report)
        if len(self.fifo) > self.capacity:
            self.fifo.pop(0)

    def purge_expired(self, slot: int) -> None:
        self.fifo[:] = [r for r in self.fifo if slot < r.event_time + REPORT_LIFETIME]


@dataclass(frozen=True)
class ScheduledUplink:
    arrival_slot: int
    sender_index: int
    report: Report
    listener_indices: tuple[int, ...]
    decoded_receiver_indices: tuple[int, ...]


@dataclass(frozen=True)
class ScheduledBaseForward:
    arrival_slot: int
    sender_index: int
    report: Report


@dataclass
class EpisodeMetrics:
    radio_actions: int = 0
    waste_actions: int = 0
    duplicate_arrivals: int = 0
    expired_arrivals: int = 0
    collision_losses: int = 0
    empty_actions: int = 0
    decoded_uplinks: int = 0
    decoded_base_forwards: int = 0
    new_timely_deliveries: int = 0


class RidgeGateWorld:
    """One exact, fixed-roster RIDGEGATE-2Z potential-outcome world."""

    def __init__(
        self, permit: ProductionPermit, coordinate: Coordinate,
        rng: CounterRNG | None = None,
    ) -> None:
        coordinate.validate()
        _require_local_permit(permit, coordinate.seed)
        self._permit = permit
        self.coordinate = coordinate
        self.rng = rng or CounterRNG(permit)
        self.rng.require_same_permit(permit)
        self.multiplicity = validate_roster(coordinate.roster)
        self.slot = 0
        self.metrics = EpisodeMetrics()
        self.delivered: set[tuple[int, int]] = set()
        self.delivered_by_basin = [0, 0]
        self._scheduled_uplinks: list[ScheduledUplink] = []
        self._scheduled_base: list[ScheduledBaseForward] = []
        self._predecision_prepared = False

        self.agents: list[AgentState] = []
        for role in Role:
            capacity = RELAY_FIFO_CAPACITY if role is Role.RIDGE_RELAY else SURVEYOR_FIFO_CAPACITY
            self.agents.extend(AgentState(role, index, capacity) for index in range(self.multiplicity))

        self.events: dict[Basin, tuple[Report, ...]] = {}
        for basin in Basin:
            selected = self.rng.sample_without_replacement(
                EVENT_TIME_SUPPORT, EVENTS_PER_BASIN,
                *coordinate.address(), "basin", int(basin),
                "random-variable-kind", "event-time-subset-key",
            )
            self.events[basin] = tuple(
                Report(basin, ordinal, event_time)
                for ordinal, event_time in enumerate(sorted(int(x) for x in selected))
            )

    @property
    def n_agents(self) -> int:
        return len(self.agents)

    @property
    def done(self) -> bool:
        return self.slot >= HORIZON

    def role_indices(self, role: Role) -> tuple[int, ...]:
        return tuple(i for i, state in enumerate(self.agents) if state.role is role)

    @staticmethod
    def _remove_acknowledged_head(state: AgentState, transmitted_report: Report) -> None:
        # The transmitted report identifies the arrival/scoring outcome only.
        # Step 2 literally removes the *current* head after all step-1 arrivals
        # (and their overflow drops), even if that is no longer this object.
        del transmitted_report
        if state.fifo:
            state.fifo.pop(0)

    def _process_scheduled_arrivals_and_acknowledgements(self) -> None:
        """Apply arrivals first, acknowledgements second, then let caller purge."""
        success = [False] * self.n_agents
        uplink_acknowledgements: list[ScheduledUplink] = []
        future_uplinks: list[ScheduledUplink] = []
        for scheduled in self._scheduled_uplinks:
            if scheduled.arrival_slot != self.slot:
                future_uplinks.append(scheduled)
                continue
            for receiver_index in scheduled.decoded_receiver_indices:
                self.metrics.decoded_uplinks += 1
                if self.slot < scheduled.report.event_time + REPORT_LIFETIME:
                    self.agents[receiver_index].append(scheduled.report)
                    success[receiver_index] = True
                    success[scheduled.sender_index] = True
                else:
                    self.metrics.expired_arrivals += 1
            uplink_acknowledgements.append(scheduled)
        self._scheduled_uplinks = future_uplinks

        base_acknowledgements: list[ScheduledBaseForward] = []
        future_base: list[ScheduledBaseForward] = []
        for scheduled in self._scheduled_base:
            if scheduled.arrival_slot != self.slot:
                future_base.append(scheduled)
                continue
            report = scheduled.report
            self.metrics.decoded_base_forwards += 1
            if self.slot >= report.event_time + REPORT_LIFETIME:
                self.metrics.expired_arrivals += 1
            elif report.event_id in self.delivered:
                self.metrics.duplicate_arrivals += 1
            else:
                self.delivered.add(report.event_id)
                self.delivered_by_basin[int(report.basin)] += 1
                self.metrics.new_timely_deliveries += 1
                success[scheduled.sender_index] = True
            base_acknowledgements.append(scheduled)
        self._scheduled_base = future_base

        # Step 2 begins only after every step-1 mission arrival was processed.
        for scheduled in uplink_acknowledgements:
            self._remove_acknowledged_head(
                self.agents[scheduled.sender_index], scheduled.report
            )
            if not success[scheduled.sender_index]:
                self.metrics.waste_actions += 1
            for listener_index in scheduled.listener_indices:
                if not success[listener_index]:
                    self.metrics.waste_actions += 1
        for scheduled in base_acknowledgements:
            self._remove_acknowledged_head(
                self.agents[scheduled.sender_index], scheduled.report
            )
            if not success[scheduled.sender_index]:
                self.metrics.waste_actions += 1
        for index, state in enumerate(self.agents):
            state.previous_success = success[index]

    def _prepare_predecision(self) -> None:
        _require_local_permit(self._permit)
        if self._predecision_prepared:
            return
        self._process_scheduled_arrivals_and_acknowledgements()
        for state in self.agents:
            state.purge_expired(self.slot)
        self._predecision_prepared = True

    def observations(self) -> torch.Tensor:
        _require_local_permit(self._permit)
        if self.done:
            raise RuntimeError("the episode has no post-horizon observation")
        self._prepare_predecision()
        rows: list[list[float]] = []
        for state in self.agents:
            row = [0.0] * OBSERVATION_DIM
            row[int(state.role)] = 1.0
            row[3] = self.slot / 11.0
            row[4:7] = [self.multiplicity / 7.0] * 3
            cursor = 7
            for position in range(RELAY_FIFO_CAPACITY):
                if position < len(state.fifo):
                    report = state.fifo[position]
                    row[cursor] = 1.0
                    row[cursor + 1] = min(max(0, self.slot - report.event_time), 3) / 3.0
                cursor += 2
            if state.previous_action is not None:
                row[15 + state.previous_action] = 1.0
            row[21] = float(state.previous_success)
            rows.append(row)
        return torch.tensor(rows, dtype=TRAINING_DTYPE)

    def roles_tensor(self) -> torch.Tensor:
        return torch.tensor([int(s.role) for s in self.agents], dtype=torch.long)

    def _coin_address(
        self, *, kind: str, sender: AgentState,
        receiver: AgentState | str, report: Report,
    ) -> tuple[object, ...]:
        receiver_fields: tuple[object, ...]
        if isinstance(receiver, AgentState):
            receiver_fields = (
                "receiver-role", int(receiver.role),
                "receiver-role-local-index", receiver.role_local_index,
            )
        else:
            receiver_fields = ("receiver", receiver)
        return (
            *self.coordinate.address(), "slot", self.slot,
            "basin", int(report.basin), "event-ordinal", report.event_ordinal,
            "sender-role", int(sender.role),
            "sender-role-local-index", sender.role_local_index,
            *receiver_fields, "random-variable-kind", kind,
        )

    def _resolve_uplinks(self, actions: list[Action]) -> None:
        relays = self.role_indices(Role.RIDGE_RELAY)
        for basin in Basin:
            sender_role = Role.WEST_SURVEYOR if basin is Basin.WEST else Role.EAST_SURVEYOR
            listen_action = Action.LISTEN_WEST if basin is Basin.WEST else Action.LISTEN_EAST
            uplinks = [i for i in self.role_indices(sender_role) if actions[i] is Action.UPLINK]
            nonempty = [i for i in uplinks if self.agents[i].fifo]
            listeners = [i for i in relays if actions[i] is listen_action]
            self.metrics.radio_actions += len(uplinks) + len(listeners)
            self.metrics.empty_actions += len(uplinks) - len(nonempty)
            self.metrics.waste_actions += len(uplinks) - len(nonempty)
            if len(nonempty) >= 2:
                self.metrics.collision_losses += len(nonempty)
                self.metrics.waste_actions += len(nonempty) + len(listeners)
                continue
            if not nonempty or self.slot + 1 >= HORIZON:
                self.metrics.waste_actions += len(nonempty) + len(listeners)
                continue
            sender_index = nonempty[0]
            sender = self.agents[sender_index]
            report = sender.fifo[0]
            probability = _loaded_probability(
                P0[int(Role.RIDGE_RELAY)][int(sender_role)], self.multiplicity
            )
            decoded = tuple(
                receiver_index for receiver_index in listeners
                if self.rng.bernoulli(
                    probability,
                    *self._coin_address(
                        kind="mission-uplink-packet", sender=sender,
                        receiver=self.agents[receiver_index], report=report,
                    ),
                )
            )
            if decoded:
                self._scheduled_uplinks.append(ScheduledUplink(
                    self.slot + 1, sender_index, report, tuple(listeners), decoded
                ))
            else:
                self.metrics.waste_actions += len(nonempty) + len(listeners)

    def _resolve_base(self, actions: list[Action]) -> None:
        forwards = [
            i for i in self.role_indices(Role.RIDGE_RELAY)
            if actions[i] is Action.FORWARD_BASE
        ]
        nonempty = [i for i in forwards if self.agents[i].fifo]
        self.metrics.radio_actions += len(forwards)
        self.metrics.empty_actions += len(forwards) - len(nonempty)
        self.metrics.waste_actions += len(forwards) - len(nonempty)
        if len(nonempty) >= 2:
            self.metrics.collision_losses += len(nonempty)
            self.metrics.waste_actions += len(nonempty)
            return
        if not nonempty or self.slot + 1 >= HORIZON:
            self.metrics.waste_actions += len(nonempty)
            return
        sender_index = nonempty[0]
        sender = self.agents[sender_index]
        report = sender.fifo[0]
        if self.rng.bernoulli(
            _loaded_probability(BASE_P0, self.multiplicity),
            *self._coin_address(
                kind="relay-base-packet", sender=sender, receiver="BASE", report=report
            ),
        ):
            self._scheduled_base.append(
                ScheduledBaseForward(self.slot + 1, sender_index, report)
            )
        else:
            self.metrics.waste_actions += len(nonempty)

    def _resolve_scans(self, actions: list[Action]) -> None:
        for basin in Basin:
            event = next((e for e in self.events[basin] if e.event_time == self.slot), None)
            if event is None:
                continue
            role = Role.WEST_SURVEYOR if basin is Basin.WEST else Role.EAST_SURVEYOR
            for index in self.role_indices(role):
                state = self.agents[index]
                if actions[index] is Action.SCAN and self.rng.bernoulli(
                    DETECTION_PROBABILITY,
                    *self.coordinate.address(), "slot", self.slot,
                    "basin", int(basin), "event-ordinal", event.event_ordinal,
                    "public-role", int(role),
                    "role-local-simulator-index", state.role_local_index,
                    "random-variable-kind", "event-detection",
                ):
                    state.append(event)

    def step(self, actions: Iterable[int | Action]) -> None:
        _require_local_permit(self._permit)
        if self.done:
            raise RuntimeError("cannot act after the horizon")
        if not self._predecision_prepared:
            raise RuntimeError("observations must prepare the predecision state before action")
        chosen = [Action(int(a)) for a in actions]
        if len(chosen) != self.n_agents:
            raise ValueError("one action is required for every agent")
        for state, action in zip(self.agents, chosen):
            if int(action) not in legal_action_indices(state.role):
                raise ValueError(f"illegal action {action.name} for role {state.role.name}")
        self._resolve_uplinks(chosen)
        self._resolve_base(chosen)
        self._resolve_scans(chosen)
        for index, state in enumerate(self.agents):
            state.previous_action = int(chosen[index])
            state.previous_success = False
        self.slot += 1
        self._predecision_prepared = False

    def return_value(self) -> float:
        if not self.done:
            raise RuntimeError("terminal return is defined only after slot 11")
        if self._scheduled_uplinks or self._scheduled_base:
            raise RuntimeError("post-horizon arrivals may not remain scheduled")
        west, east = self.delivered_by_basin
        waste = self.metrics.waste_actions / self.metrics.radio_actions if self.metrics.radio_actions else 0.0
        return (
            0.65 * (west + east) / 6.0
            + 0.25 * min(west, east) / 3.0
            + 0.10 * (1.0 - waste)
        )

    def basin_delivery_rates(self) -> tuple[float, float]:
        return (self.delivered_by_basin[0] / 3.0, self.delivered_by_basin[1] / 3.0)
