"""Exact four-agent service-relay host for CRTO-B1 v4.

This module owns physical dynamics, deployable telemetry, the external-K review
clock, option charging/re-anchoring, immutable exogenous tapes, and clonable
predecision state.  It intentionally owns no learned model or predictor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from math import isfinite
from typing import Callable, Mapping, Sequence

import numpy as np

from .config import AGENT_COUNT, COST_REGIMES, EVENT_CLASSES, HORIZON, OPTIONS, REGIMES
from .rng import StreamNamespace, categorical_from_logits, namespaced_pcg64, score_mapping


LANES = ("L", "R")
EVENT_DURATION = 32
SWITCH_TIME = 128
REVIEW_PERIOD = 4
QUEUE_CAPACITY = 64
BUFFER_CAPACITY = 64
ENERGY_CAPACITY = 32.0
FIXED_ONSETS = (50, 66, 82, 98, 146, 162, 178, 194)
LATE_ONSETS = (146, 162, 178, 194)
EARLY_ONSETS = (50, 66, 82, 98)


class Lane(IntEnum):
    L = 0
    R = 1


class Location(IntEnum):
    L = 0
    BASE = 1
    R = 2


class Option(IntEnum):
    TRACK_L = 0
    TRACK_R = 1
    RELAY_L = 2
    RELAY_R = 3
    TRANSIT_L = 4
    TRANSIT_R = 5
    RETURN = 6

    @property
    def label(self) -> str:
        return OPTIONS[int(self)]


class EventClass(str, Enum):
    NONE = "NONE"
    UNANNOUNCED_DIFFERENTIAL = "UNANNOUNCED-DIFFERENTIAL"
    CUED_DIFFERENTIAL = "CUED-DIFFERENTIAL"
    COMMON_SENSOR = "COMMON-SENSOR"


class Regime(str, Enum):
    K4 = "K4"
    K8 = "K8"
    K16 = "K16"
    K4_TO_16 = "K4_TO_16"
    K16_TO_4 = "K16_TO_4"


class DecisionKind(str, Enum):
    NONE = "NONE"
    INITIAL = "INITIAL"
    DISCRETIONARY = "DISCRETIONARY"
    FORCED_RENEWAL = "FORCED_RENEWAL"


class CueState(str, Enum):
    NONE = "none"
    L = "L"
    R = "R"


def _readonly(array: np.ndarray, dtype: np.dtype | type) -> np.ndarray:
    result = np.asarray(array, dtype=dtype).copy()
    result.setflags(write=False)
    return result


def _require_shape(name: str, value: np.ndarray, shape: tuple[int, ...]) -> None:
    if value.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {value.shape}")


@dataclass(frozen=True)
class ScenarioSpec:
    """One prospectively assigned event-by-cost-onset cell."""

    episode_index: int
    episode_seed: int
    regime: Regime
    event: EventClass
    event_onset: int
    replanning_cost: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "regime", Regime(self.regime))
        object.__setattr__(self, "event", EventClass(self.event))
        object.__setattr__(self, "replanning_cost", float(self.replanning_cost))
        if self.episode_index < 0 or self.episode_seed < 0:
            raise ValueError("episode index and seed must be nonnegative")
        if self.replanning_cost not in COST_REGIMES:
            raise ValueError("replanning cost is outside the frozen crossed cells")
        allowed = onset_schedule(self.regime)
        if self.event_onset not in allowed:
            raise ValueError(f"onset {self.event_onset} is invalid for {self.regime.value}")


@dataclass(frozen=True)
class ScenarioTape:
    """Complete provider-independent exogenous episode tape."""

    spec: ScenarioSpec
    initial_locations: np.ndarray
    initial_hot_lane: Lane
    arrival_hot_coin: np.ndarray
    arrival_cold_coin: np.ndarray
    relay_capacity_coin: np.ndarray
    option_uniform: np.ndarray
    rate_control_uniform: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_hot_lane", Lane(self.initial_hot_lane))
        object.__setattr__(self, "initial_locations", _readonly(self.initial_locations, np.int8))
        object.__setattr__(self, "arrival_hot_coin", _readonly(self.arrival_hot_coin, np.int8))
        object.__setattr__(self, "arrival_cold_coin", _readonly(self.arrival_cold_coin, np.int8))
        object.__setattr__(self, "relay_capacity_coin", _readonly(self.relay_capacity_coin, np.int8))
        object.__setattr__(self, "option_uniform", _readonly(self.option_uniform, np.float64))
        object.__setattr__(self, "rate_control_uniform", _readonly(self.rate_control_uniform, np.float64))
        _require_shape("initial_locations", self.initial_locations, (AGENT_COUNT,))
        _require_shape("arrival_hot_coin", self.arrival_hot_coin, (HORIZON,))
        _require_shape("arrival_cold_coin", self.arrival_cold_coin, (HORIZON,))
        _require_shape("relay_capacity_coin", self.relay_capacity_coin, (HORIZON, 2))
        _require_shape("option_uniform", self.option_uniform, (HORIZON, AGENT_COUNT))
        _require_shape("rate_control_uniform", self.rate_control_uniform, (HORIZON, AGENT_COUNT))
        if sorted(int(value) for value in self.initial_locations) != [0, 1, 1, 2]:
            raise ValueError("initial locations must be a permutation of (L,R,BASE,BASE)")
        for name, array in (
            ("arrival_hot_coin", self.arrival_hot_coin),
            ("arrival_cold_coin", self.arrival_cold_coin),
            ("relay_capacity_coin", self.relay_capacity_coin),
        ):
            if np.any((array != 0) & (array != 1)):
                raise ValueError(f"{name} must contain Bernoulli outcomes")
        for name, array in (("option_uniform", self.option_uniform),
                            ("rate_control_uniform", self.rate_control_uniform)):
            if not np.all(np.isfinite(array)) or np.any(array < 0.0) or np.any(array >= 1.0):
                raise ValueError(f"{name} must contain values in [0,1)")

    def k_at(self, primitive_time: int) -> int:
        if not 0 <= primitive_time < HORIZON:
            raise IndexError("primitive time outside episode tape")
        if self.spec.regime is Regime.K4:
            return 4
        if self.spec.regime is Regime.K8:
            return 8
        if self.spec.regime is Regime.K16:
            return 16
        before = primitive_time < SWITCH_TIME
        if self.spec.regime is Regime.K4_TO_16:
            return 4 if before else 16
        if self.spec.regime is Regime.K16_TO_4:
            return 16 if before else 4
        raise AssertionError("unhandled regime")

    def total_physical_arrivals(self) -> int:
        """Return the action-invariant complete-episode physical denominator."""

        total = 0
        initial_hot = self.initial_hot_lane
        for time in range(HORIZON):
            hot = initial_hot
            active = (
                self.spec.event is not EventClass.NONE
                and self.spec.event_onset <= time < self.spec.event_onset + EVENT_DURATION
            )
            if active and self.spec.event in (
                EventClass.UNANNOUNCED_DIFFERENTIAL, EventClass.CUED_DIFFERENTIAL,
            ):
                hot = Lane.R if hot is Lane.L else Lane.L
            # Lane assignment changes allocation but not total demand.
            _ = hot
            total += 1 + int(self.arrival_hot_coin[time]) + int(self.arrival_cold_coin[time])
        return total


def onset_schedule(regime: Regime) -> tuple[int, ...]:
    regime = Regime(regime)
    if regime is Regime.K4_TO_16:
        return LATE_ONSETS
    if regime is Regime.K16_TO_4:
        return EARLY_ONSETS
    return FIXED_ONSETS


def balanced_scenario_specs(
    *, count: int, regime: Regime, root_seed: int, first_episode_index: int = 0,
) -> tuple[ScenarioSpec, ...]:
    """Create a shuffled, exactly balanced event/cost/onset manifest.

    ``count`` must contain an integer number of complete crossed-cell blocks;
    this fail-closed rule prevents silent cell imbalance.
    """

    regime = Regime(regime)
    onsets = onset_schedule(regime)
    cells = tuple(
        (EventClass(event), float(cost), onset)
        for event in EVENT_CLASSES for cost in COST_REGIMES for onset in onsets
    )
    if count <= 0 or count % len(cells):
        raise ValueError(f"count must be a positive multiple of {len(cells)} for {regime.value}")
    rows = list(cells) * (count // len(cells))
    order_rng = namespaced_pcg64(root_seed, StreamNamespace.MANIFEST_ORDER, int(regime_index(regime)))
    order = order_rng.permutation(len(rows))
    return tuple(
        ScenarioSpec(
            episode_index=first_episode_index + offset,
            episode_seed=int(root_seed) + first_episode_index + offset,
            regime=regime,
            event=rows[int(source)][0],
            replanning_cost=rows[int(source)][1],
            event_onset=rows[int(source)][2],
        )
        for offset, source in enumerate(order)
    )


def regime_index(regime: Regime) -> int:
    return (Regime.K4, Regime.K8, Regime.K16, Regime.K4_TO_16, Regime.K16_TO_4).index(
        Regime(regime)
    )


def build_scenario_tape(spec: ScenarioSpec) -> ScenarioTape:
    """Materialize all random episode quantities before any action is seen."""

    physical = namespaced_pcg64(spec.episode_seed, StreamNamespace.PHYSICAL_TAPE)
    locations = physical.permutation(
        np.asarray((Location.L, Location.R, Location.BASE, Location.BASE), dtype=np.int8)
    )
    hot_lane = Lane(int(physical.integers(0, 2)))
    arrivals_hot = physical.integers(0, 2, size=HORIZON, dtype=np.int8)
    arrivals_cold = physical.integers(0, 2, size=HORIZON, dtype=np.int8)
    capacity = physical.integers(0, 2, size=(HORIZON, 2), dtype=np.int8)
    option_rng = namespaced_pcg64(spec.episode_seed, StreamNamespace.OPTION_SELECTION)
    rate_rng = namespaced_pcg64(spec.episode_seed, StreamNamespace.RATE_CONTROL)
    return ScenarioTape(
        spec=spec,
        initial_locations=locations,
        initial_hot_lane=hot_lane,
        arrival_hot_coin=arrivals_hot,
        arrival_cold_coin=arrivals_cold,
        relay_capacity_coin=capacity,
        option_uniform=option_rng.random((HORIZON, AGENT_COUNT)),
        rate_control_uniform=rate_rng.random((HORIZON, AGENT_COUNT)),
    )


@dataclass(frozen=True)
class AnchorRecord:
    agent: int
    primitive_time: int
    option: Option
    commitment_id: int
    reason: str


@dataclass(frozen=True)
class DecisionRecord:
    agent: int
    kind: DecisionKind
    previous_option: Option | None
    selected_option: Option
    changed: bool
    charge: float
    age_before: int
    age_after_decision: int
    switch_time: bool
    reanchored: bool


@dataclass(frozen=True)
class DeployableTelemetry:
    queue_tilde: tuple[float, float]
    buffer: tuple[float, float]
    deliveries_previous_four: tuple[float, float]
    option_count: tuple[float, ...]
    location_count: tuple[float, float, float]
    time_fraction: float


@dataclass(frozen=True)
class DeployableObservation:
    agent: int
    location: Location
    energy: float
    current_option: Option | None
    absolute_age: int
    age_over_k: float
    k_over_16: float
    cost_over_4: float
    legal_mask: tuple[bool, ...]
    visible_cue: CueState
    broadcast: DeployableTelemetry

    def vector(self) -> np.ndarray:
        """Return the normalized 42-coordinate deployed primitive input."""

        location = np.eye(3, dtype=np.float32)[int(self.location)]
        option = (
            np.zeros(7, dtype=np.float32) if self.current_option is None
            else np.eye(7, dtype=np.float32)[int(self.current_option)]
        )
        cue_index = (CueState.NONE, CueState.L, CueState.R).index(self.visible_cue)
        cue = np.eye(3, dtype=np.float32)[cue_index]
        vector = np.concatenate((
            location,
            np.asarray((self.energy / ENERGY_CAPACITY,), dtype=np.float32),
            option,
            np.asarray((self.absolute_age / 16.0, self.age_over_k, self.k_over_16,
                        self.cost_over_4), dtype=np.float32),
            np.asarray(self.legal_mask, dtype=np.float32),
            cue,
            np.asarray(self.broadcast.queue_tilde, dtype=np.float32),
            np.asarray(self.broadcast.buffer, dtype=np.float32),
            np.asarray(self.broadcast.deliveries_previous_four, dtype=np.float32),
            np.asarray(self.broadcast.option_count, dtype=np.float32),
            np.asarray(self.broadcast.location_count, dtype=np.float32),
            np.asarray((self.broadcast.time_fraction,), dtype=np.float32),
        ))
        if vector.shape != (42,) or not np.all(np.isfinite(vector)):
            raise RuntimeError("deployable observation construction violated its fixed width")
        return vector


@dataclass(frozen=True)
class PhysicalAuditState:
    primitive_time: int
    queues: tuple[int, int]
    buffers: tuple[int, int]
    locations: tuple[Location, ...]
    energies: tuple[float, ...]
    options: tuple[Option, ...]
    option_ages: tuple[int, ...]
    current_k: int

    def terminal_potential(self) -> float:
        return -0.02 * (sum(self.queues) + sum(self.buffers)) - 0.01 * sum(
            ENERGY_CAPACITY - energy for energy in self.energies
        )


@dataclass
class HostState:
    primitive_time: int
    queues: np.ndarray
    buffers: np.ndarray
    locations: np.ndarray
    energies: np.ndarray
    options: np.ndarray
    option_ages: np.ndarray
    commitment_ids: np.ndarray
    anchor_times: np.ndarray
    anchor_commitment_ids: np.ndarray
    current_k: int
    total_arrivals: int = 0
    total_delivered: int = 0
    total_overflow: int = 0
    total_energy_spent: float = 0.0
    total_renewal_replan_cost: float = 0.0
    renewal_count: int = 0
    replan_count: int = 0
    simultaneous_trigger_count: int = 0
    option_collisions: int = 0
    delivery_history: list[tuple[int, int]] = field(default_factory=list)

    def clone(self) -> "HostState":
        return HostState(
            primitive_time=self.primitive_time,
            queues=self.queues.copy(), buffers=self.buffers.copy(),
            locations=self.locations.copy(), energies=self.energies.copy(),
            options=self.options.copy(), option_ages=self.option_ages.copy(),
            commitment_ids=self.commitment_ids.copy(), anchor_times=self.anchor_times.copy(),
            anchor_commitment_ids=self.anchor_commitment_ids.copy(), current_k=self.current_k,
            total_arrivals=self.total_arrivals, total_delivered=self.total_delivered,
            total_overflow=self.total_overflow, total_energy_spent=self.total_energy_spent,
            total_renewal_replan_cost=self.total_renewal_replan_cost,
            renewal_count=self.renewal_count, replan_count=self.replan_count,
            simultaneous_trigger_count=self.simultaneous_trigger_count,
            option_collisions=self.option_collisions,
            delivery_history=list(self.delivery_history),
        )


@dataclass(frozen=True)
class StepRecord:
    primitive_time: int
    k: int
    event_active: bool
    physical_queues_before: tuple[int, int]
    deployable_queues_before: tuple[int, int]
    buffers_before: tuple[int, int]
    arrivals: tuple[int, int]
    relay_capacity: tuple[int, int]
    tracked: tuple[int, int]
    delivered: tuple[int, int]
    overflow: int
    energy_spent: float
    decision_charge: float
    reward: float
    physical_queues_after: tuple[int, int]
    buffers_after: tuple[int, int]
    decisions: tuple[DecisionRecord, ...]


@dataclass(frozen=True)
class EpisodeRecord:
    scenario: ScenarioSpec
    steps: tuple[StepRecord, ...]
    anchors: tuple[AnchorRecord, ...]
    normalized_score: float
    failure: bool
    delivery_fraction: float
    total_arrivals: int
    total_delivered: int
    total_overflow: int
    total_energy_spent: float
    renewal_count: int
    replan_count: int
    simultaneous_trigger_count: int
    option_collisions: int


ScoreRows = Sequence[Mapping[Option, float]]


class ServiceRelayHost:
    """Clonable exact simulator whose only stochasticity is its immutable tape."""

    def __init__(self, tape: ScenarioTape) -> None:
        self.tape = tape
        self.state = HostState(
            primitive_time=0,
            queues=np.asarray((8, 8), dtype=np.int16),
            buffers=np.asarray((4, 4), dtype=np.int16),
            locations=tape.initial_locations.astype(np.int8, copy=True),
            energies=np.full(AGENT_COUNT, 24.0, dtype=np.float64),
            options=np.full(AGENT_COUNT, -1, dtype=np.int8),
            option_ages=np.zeros(AGENT_COUNT, dtype=np.int16),
            commitment_ids=np.zeros(AGENT_COUNT, dtype=np.int64),
            anchor_times=np.full(AGENT_COUNT, -1, dtype=np.int16),
            anchor_commitment_ids=np.full(AGENT_COUNT, -1, dtype=np.int64),
            current_k=tape.k_at(0),
        )
        self.steps: list[StepRecord] = []
        self.anchors: list[AnchorRecord] = []
        self._reward_sum = 0.0

    def clone(self, *, retain_records: bool = True) -> "ServiceRelayHost":
        """Clone complete predecision state while sharing the immutable future tape."""

        clone = object.__new__(ServiceRelayHost)
        clone.tape = self.tape
        clone.state = self.state.clone()
        clone.steps = list(self.steps) if retain_records else []
        clone.anchors = list(self.anchors) if retain_records else []
        clone._reward_sum = self._reward_sum
        return clone

    @property
    def done(self) -> bool:
        return self.state.primitive_time >= HORIZON

    @property
    def initialized(self) -> bool:
        return bool(np.all(self.state.options >= 0))

    def _require_live(self) -> None:
        if self.done:
            raise RuntimeError("episode is complete")

    def event_active(self, primitive_time: int | None = None) -> bool:
        time = self.state.primitive_time if primitive_time is None else primitive_time
        event = self.tape.spec.event
        return event is not EventClass.NONE and self.tape.spec.event_onset <= time < (
            self.tape.spec.event_onset + EVENT_DURATION
        )

    def visible_cue(self, primitive_time: int | None = None) -> CueState:
        time = self.state.primitive_time if primitive_time is None else primitive_time
        if self.tape.spec.event is not EventClass.CUED_DIFFERENTIAL:
            return CueState.NONE
        onset = self.tape.spec.event_onset
        if not onset - 8 <= time < onset:
            return CueState.NONE
        future_hot = Lane.R if self.tape.initial_hot_lane is Lane.L else Lane.L
        return CueState.L if future_hot is Lane.L else CueState.R

    def physical_arrivals(self, primitive_time: int | None = None) -> tuple[int, int]:
        time = self.state.primitive_time if primitive_time is None else primitive_time
        hot = self.tape.initial_hot_lane
        if self.event_active(time) and self.tape.spec.event in (
            EventClass.UNANNOUNCED_DIFFERENTIAL, EventClass.CUED_DIFFERENTIAL,
        ):
            hot = Lane.R if hot is Lane.L else Lane.L
        cold = Lane.R if hot is Lane.L else Lane.L
        arrivals = [0, 0]
        arrivals[int(hot)] = 1 + int(self.tape.arrival_hot_coin[time])
        arrivals[int(cold)] = int(self.tape.arrival_cold_coin[time])
        return int(arrivals[0]), int(arrivals[1])

    def deployable_queue(self) -> tuple[int, int]:
        offset = 4 if (
            self.tape.spec.event is EventClass.COMMON_SENSOR and self.event_active()
        ) else 0
        values = np.clip(self.state.queues.astype(np.int32) + offset, 0, QUEUE_CAPACITY)
        return int(values[0]), int(values[1])

    def legal_mask(self, agent: int) -> tuple[bool, ...]:
        if not 0 <= agent < AGENT_COUNT:
            raise IndexError("agent outside fixed four-agent team")
        location = Location(int(self.state.locations[agent]))
        energy = float(self.state.energies[agent])
        return (
            location is Location.L and energy >= 1.0,
            location is Location.R and energy >= 1.0,
            location is Location.L and energy >= 1.0,
            location is Location.R and energy >= 1.0,
            location is not Location.L and energy >= 0.25,
            location is not Location.R and energy >= 0.25,
            True,
        )

    def broadcast(self) -> DeployableTelemetry:
        queue = self.deployable_queue()
        previous = self.state.delivery_history[-4:]
        delivery = tuple(sum(row[lane] for row in previous) / 8.0 for lane in range(2))
        option_count = tuple(
            float(np.count_nonzero(self.state.options == option)) / AGENT_COUNT
            for option in range(len(OPTIONS))
        )
        location_count = tuple(
            float(np.count_nonzero(self.state.locations == location)) / AGENT_COUNT
            for location in range(3)
        )
        return DeployableTelemetry(
            queue_tilde=(queue[0] / 64.0, queue[1] / 64.0),
            buffer=(float(self.state.buffers[0]) / 64.0, float(self.state.buffers[1]) / 64.0),
            deliveries_previous_four=(float(delivery[0]), float(delivery[1])),
            option_count=option_count,
            location_count=location_count,
            time_fraction=self.state.primitive_time / HORIZON,
        )

    def observations(self) -> tuple[DeployableObservation, ...]:
        common = self.broadcast()
        k = self.tape.k_at(self.state.primitive_time)
        return tuple(
            DeployableObservation(
                agent=agent,
                location=Location(int(self.state.locations[agent])),
                energy=float(self.state.energies[agent]),
                current_option=(
                    Option(int(self.state.options[agent])) if self.state.options[agent] >= 0 else None
                ),
                absolute_age=int(self.state.option_ages[agent]),
                age_over_k=float(self.state.option_ages[agent]) / k,
                k_over_16=k / 16.0,
                cost_over_4=self.tape.spec.replanning_cost / 4.0,
                legal_mask=self.legal_mask(agent),
                visible_cue=self.visible_cue(),
                broadcast=common,
            )
            for agent in range(AGENT_COUNT)
        )

    def physical_audit_state(self) -> PhysicalAuditState:
        if not self.initialized:
            raise RuntimeError("initial options have not been selected")
        return PhysicalAuditState(
            primitive_time=self.state.primitive_time,
            queues=tuple(int(value) for value in self.state.queues),
            buffers=tuple(int(value) for value in self.state.buffers),
            locations=tuple(Location(int(value)) for value in self.state.locations),
            energies=tuple(float(value) for value in self.state.energies),
            options=tuple(Option(int(value)) for value in self.state.options),
            option_ages=tuple(int(value) for value in self.state.option_ages),
            current_k=self.tape.k_at(self.state.primitive_time),
        )

    def centralized_state_vector(self) -> np.ndarray:
        """Evaluation/training-only physical state; never a deployed input."""

        audit = self.physical_audit_state()
        vector = np.concatenate((
            np.asarray(audit.queues, dtype=np.float32) / 64.0,
            np.asarray(audit.buffers, dtype=np.float32) / 64.0,
            np.eye(3, dtype=np.float32)[self.state.locations].reshape(-1),
            self.state.energies.astype(np.float32) / 32.0,
            np.eye(7, dtype=np.float32)[self.state.options].reshape(-1),
            self.state.option_ages.astype(np.float32) / 16.0,
            np.asarray((audit.current_k / 16.0, self.state.primitive_time / HORIZON), dtype=np.float32),
        ))
        if not np.all(np.isfinite(vector)):
            raise RuntimeError("nonfinite centralized state")
        return vector

    def predictor_target(self, agent: int) -> np.ndarray:
        if not self.initialized:
            raise RuntimeError("initial options have not been selected")
        option = Option(int(self.state.options[agent]))
        target_location = option_target(option)
        distance = abs(int(self.state.locations[agent]) - int(target_location))
        common = self.broadcast()
        return np.asarray((
            common.queue_tilde[0], common.queue_tilde[1], common.buffer[0], common.buffer[1],
            common.deliveries_previous_four[0], common.deliveries_previous_four[1],
            float(self.state.energies[agent]) / 32.0, distance / 2.0,
        ), dtype=np.float32)

    def forecast_target_eligible(self, agent: int, horizon: int) -> bool:
        """Check the exact continuous-anchor eligibility at this predecision state."""

        if horizon not in (4, 8, 12, 16):
            raise ValueError("forecast horizon must be one of 4,8,12,16")
        return bool(
            self.initialized
            and self.state.primitive_time - int(self.state.anchor_times[agent]) == horizon
            and self.state.commitment_ids[agent] == self.state.anchor_commitment_ids[agent]
        )

    def _anchor(self, agent: int, reason: str) -> None:
        option = Option(int(self.state.options[agent]))
        self.state.anchor_times[agent] = self.state.primitive_time
        self.state.anchor_commitment_ids[agent] = self.state.commitment_ids[agent]
        self.anchors.append(AnchorRecord(
            agent=agent, primitive_time=self.state.primitive_time, option=option,
            commitment_id=int(self.state.commitment_ids[agent]), reason=reason,
        ))

    def select_initial(self, q_scores: ScoreRows, *, training: bool) -> tuple[DecisionRecord, ...]:
        self._require_live()
        if self.initialized or self.state.primitive_time != 0 or len(q_scores) != AGENT_COUNT:
            raise RuntimeError("initial selection is legal exactly once at reset")
        decisions: list[DecisionRecord] = []
        for agent in range(AGENT_COUNT):
            legal = tuple(Option(index) for index, allowed in enumerate(self.legal_mask(agent)) if allowed)
            logits = score_mapping(legal, q_scores[agent], label="initial q")
            selected = (
                categorical_from_logits(legal, logits, float(self.tape.option_uniform[0, agent]))
                if training else legal[int(np.argmax(logits))]
            )
            self.state.options[agent] = int(selected)
            self.state.option_ages[agent] = 0
            self.state.commitment_ids[agent] += 1
            self._anchor(agent, "initial")
            decisions.append(DecisionRecord(
                agent, DecisionKind.INITIAL, None, selected, False, 0.0, 0, 0, False, True,
            ))
        selected_options = [record.selected_option for record in decisions]
        self.state.option_collisions += len(selected_options) - len(set(selected_options))
        return tuple(decisions)

    def review_kinds(self) -> tuple[DecisionKind, ...]:
        if not self.initialized:
            raise RuntimeError("initial options have not been selected")
        new_k = self.tape.k_at(self.state.primitive_time)
        kinds: list[DecisionKind] = []
        for age in self.state.option_ages:
            value = int(age)
            if value >= new_k:
                kinds.append(DecisionKind.FORCED_RENEWAL)
            elif value > 0 and value % REVIEW_PERIOD == 0:
                kinds.append(DecisionKind.DISCRETIONARY)
            else:
                kinds.append(DecisionKind.NONE)
        return tuple(kinds)

    def resolve_reviews(
        self,
        q_scores: ScoreRows,
        residual_scores: ScoreRows,
        *,
        training: bool,
        disable_residual: bool = False,
        forced_renewal_only: bool = False,
    ) -> tuple[DecisionRecord, ...]:
        """Resolve simultaneous ordinary or switch-time decisions exactly once."""

        self._require_live()
        if not self.initialized or len(q_scores) != AGENT_COUNT or len(residual_scores) != AGENT_COUNT:
            raise ValueError("review scores require four initialized agent rows")
        time = self.state.primitive_time
        new_k = self.tape.k_at(time)
        switch = new_k != self.state.current_k
        kinds = self.review_kinds()
        records: list[DecisionRecord] = []
        trigger_count = sum(kind is not DecisionKind.NONE for kind in kinds)
        if trigger_count > 1:
            self.state.simultaneous_trigger_count += 1
        for agent, kind in enumerate(kinds):
            previous = Option(int(self.state.options[agent]))
            age_before = int(self.state.option_ages[agent])
            selected = previous
            charge = 0.0
            if kind is DecisionKind.DISCRETIONARY and not forced_renewal_only:
                replacements = tuple(
                    Option(index) for index, allowed in enumerate(self.legal_mask(agent))
                    if allowed and index != int(previous)
                )
                if replacements:
                    q = score_mapping((previous,) + replacements, q_scores[agent], label="review q")
                    b = score_mapping(replacements, residual_scores[agent], label="review residual")
                    residual = (0.0,) * len(replacements) if (switch or disable_residual) else b
                    relative = tuple(
                        q[index + 1] - q[0] - (0.05 + self.tape.spec.replanning_cost) + residual[index]
                        for index in range(len(replacements))
                    )
                    choices = (None,) + replacements
                    logits = (0.0,) + relative
                    if training:
                        choice = categorical_from_logits(
                            choices, logits, float(self.tape.option_uniform[time, agent])
                        )
                        selected = previous if choice is None else choice
                    else:
                        maximum = max(relative)
                        selected = previous if maximum <= 0.0 else replacements[relative.index(maximum)]
                if selected != previous:
                    charge = 0.05 + self.tape.spec.replanning_cost
            elif kind is DecisionKind.FORCED_RENEWAL:
                legal = tuple(Option(index) for index, allowed in enumerate(self.legal_mask(agent)) if allowed)
                q = score_mapping(legal, q_scores[agent], label="renewal q")
                b = score_mapping(legal, residual_scores[agent], label="renewal residual")
                residual = (0.0,) * len(legal) if (switch or disable_residual) else b
                logits = tuple(
                    q[index] - 0.05 - (
                        self.tape.spec.replanning_cost if option != previous else 0.0
                    ) + residual[index]
                    for index, option in enumerate(legal)
                )
                selected = (
                    categorical_from_logits(legal, logits, float(self.tape.option_uniform[time, agent]))
                    if training else legal[int(np.argmax(logits))]
                )
                charge = 0.05 + (self.tape.spec.replanning_cost if selected != previous else 0.0)
            changed = selected != previous
            reanchored = False
            if kind is DecisionKind.FORCED_RENEWAL or (
                kind is DecisionKind.DISCRETIONARY and changed
            ):
                self.state.options[agent] = int(selected)
                self.state.option_ages[agent] = 0
                self.state.commitment_ids[agent] += 1
                self.state.renewal_count += int(kind is DecisionKind.FORCED_RENEWAL)
                self.state.replan_count += int(changed)
                self._anchor(agent, "forced-renewal" if kind is DecisionKind.FORCED_RENEWAL else "termination")
                reanchored = True
            if switch:
                if not reanchored:
                    self._anchor(agent, "k-switch")
                else:
                    # The new commitment's existing same-time anchor is exactly
                    # the post-switch anchor; do not create a duplicate.
                    self.anchors[-1] = AnchorRecord(
                        agent=agent, primitive_time=time, option=selected,
                        commitment_id=int(self.state.commitment_ids[agent]), reason="k-switch",
                    )
                reanchored = True
            self.state.total_renewal_replan_cost += charge
            records.append(DecisionRecord(
                agent=agent, kind=kind, previous_option=previous, selected_option=selected,
                changed=changed, charge=charge, age_before=age_before,
                age_after_decision=int(self.state.option_ages[agent]), switch_time=switch,
                reanchored=reanchored,
            ))
        self.state.current_k = new_k
        triggered_options = [
            records[agent].selected_option for agent, kind in enumerate(kinds)
            if kind is not DecisionKind.NONE
        ]
        self.state.option_collisions += len(triggered_options) - len(set(triggered_options))
        return tuple(records)

    def apply_audit_actions(
        self,
        *,
        target_agent: int,
        target_option: Option | None,
        aligned_decisions: Sequence[DecisionRecord],
    ) -> tuple[DecisionRecord, ...]:
        """Apply KEEP/replacement at one legal audit boundary to a cloned host.

        Other agents' decisions are held to their aligned simultaneous choices.
        ``target_option=None`` means KEEP.  This method performs only the
        predecision action/cost/reset operation; :meth:`advance` then consumes
        the common future physical tape.
        """

        if len(aligned_decisions) != AGENT_COUNT or not 0 <= target_agent < AGENT_COUNT:
            raise ValueError("audit requires four aligned decisions and one target agent")
        if self.review_kinds()[target_agent] is not DecisionKind.DISCRETIONARY:
            raise ValueError("audit target must be at a legal discretionary review")
        if any(record.agent != agent for agent, record in enumerate(aligned_decisions)):
            raise ValueError("aligned decisions must be in fixed environment-slot order")
        if any(record.switch_time for record in aligned_decisions):
            raise ValueError("registered audit boundary cannot be a K-switch decision")
        records: list[DecisionRecord] = []
        trigger_count = sum(record.kind is not DecisionKind.NONE for record in aligned_decisions)
        if trigger_count > 1:
            self.state.simultaneous_trigger_count += 1
        for agent, aligned in enumerate(aligned_decisions):
            previous = Option(int(self.state.options[agent]))
            if aligned.previous_option != previous or aligned.age_before != int(self.state.option_ages[agent]):
                raise ValueError("audit clone does not match aligned predecision state")
            selected = aligned.selected_option
            if agent == target_agent:
                selected = previous if target_option is None else Option(target_option)
            if aligned.kind is DecisionKind.NONE:
                if selected != previous:
                    raise ValueError("a no-review agent cannot change option")
                charge = 0.0
            elif aligned.kind is DecisionKind.DISCRETIONARY:
                if selected != previous and not self.legal_mask(agent)[int(selected)]:
                    raise ValueError("audit replacement is illegal")
                charge = 0.0 if selected == previous else 0.05 + self.tape.spec.replanning_cost
            elif aligned.kind is DecisionKind.FORCED_RENEWAL:
                if not self.legal_mask(agent)[int(selected)]:
                    raise ValueError("aligned forced-renewal option is illegal")
                charge = 0.05 + (self.tape.spec.replanning_cost if selected != previous else 0.0)
            else:
                raise ValueError("initial decisions cannot occur at an audit boundary")
            changed = selected != previous
            reanchored = aligned.kind is DecisionKind.FORCED_RENEWAL or (
                aligned.kind is DecisionKind.DISCRETIONARY and changed
            )
            if reanchored:
                self.state.options[agent] = int(selected)
                self.state.option_ages[agent] = 0
                self.state.commitment_ids[agent] += 1
                self.state.renewal_count += int(aligned.kind is DecisionKind.FORCED_RENEWAL)
                self.state.replan_count += int(changed)
                self._anchor(
                    agent,
                    "audit-enumeration" if agent == target_agent else
                    ("forced-renewal" if aligned.kind is DecisionKind.FORCED_RENEWAL else "termination"),
                )
            self.state.total_renewal_replan_cost += charge
            records.append(DecisionRecord(
                agent=agent, kind=aligned.kind, previous_option=previous,
                selected_option=selected, changed=changed, charge=charge,
                age_before=aligned.age_before,
                age_after_decision=int(self.state.option_ages[agent]),
                switch_time=False, reanchored=reanchored,
            ))
        self.state.current_k = self.tape.k_at(self.state.primitive_time)
        triggered_options = [
            record.selected_option for record in records if record.kind is not DecisionKind.NONE
        ]
        self.state.option_collisions += len(triggered_options) - len(set(triggered_options))
        return tuple(records)

    def apply_external_decisions(
        self,
        decisions: Sequence[DecisionRecord],
    ) -> tuple[DecisionRecord, ...]:
        """Apply one externally selected simultaneous decision tuple.

        This is the non-audit bridge for controls such as the frozen
        rate-matched hazard.  The caller supplies exactly one decision record
        per fixed environment slot.  The host validates the tuple against the
        current ordinary or switch-time review state, including redundant
        action, charge, reset, and re-anchor fields, before mutating anything.
        It applies decision effects only; :meth:`advance` must subsequently
        execute the primitive transition with the returned canonical tuple.

        At a K switch, the review kind is determined using ``K_new``.  Every
        accepted record must declare ``switch_time=True`` and every resulting
        active option is re-anchored after the selected action.  Absolute age is
        reset only by a forced renewal or changed discretionary option.
        Multiple simultaneous discretionary hazard fires are supported.
        """

        self._require_live()
        if not self.initialized or len(decisions) != AGENT_COUNT:
            raise ValueError("external decisions require four initialized agent rows")
        if any(record.agent != agent for agent, record in enumerate(decisions)):
            raise ValueError("external decisions must be in fixed environment-slot order")

        time = self.state.primitive_time
        new_k = self.tape.k_at(time)
        switch = new_k != self.state.current_k
        expected_kinds = self.review_kinds()
        canonical: list[DecisionRecord] = []

        # Validate the complete simultaneous tuple against one untouched
        # predecision snapshot.  No state mutation is permitted in this pass.
        for agent, supplied in enumerate(decisions):
            expected_kind = expected_kinds[agent]
            previous = Option(int(self.state.options[agent]))
            age_before = int(self.state.option_ages[agent])
            try:
                selected = Option(supplied.selected_option)
            except ValueError as error:
                raise ValueError(f"agent {agent} selected option outside the frozen order") from error
            if supplied.kind is not expected_kind:
                raise ValueError(
                    f"agent {agent} decision kind {supplied.kind.value} does not match "
                    f"current {expected_kind.value} review law"
                )
            if supplied.previous_option != previous or supplied.age_before != age_before:
                raise ValueError(f"agent {agent} external decision does not match predecision state")
            if supplied.switch_time is not switch:
                raise ValueError(f"agent {agent} switch-time marker is incorrect")

            legal = self.legal_mask(agent)
            if expected_kind is DecisionKind.NONE:
                if selected != previous:
                    raise ValueError(f"agent {agent} cannot change option without a legal review")
                charge = 0.0
                resets_commitment = False
            elif expected_kind is DecisionKind.DISCRETIONARY:
                if selected != previous and not legal[int(selected)]:
                    raise ValueError(f"agent {agent} selected an illegal discretionary replacement")
                charge = 0.0 if selected == previous else 0.05 + self.tape.spec.replanning_cost
                resets_commitment = selected != previous
            elif expected_kind is DecisionKind.FORCED_RENEWAL:
                if not legal[int(selected)]:
                    raise ValueError(f"agent {agent} selected an illegal forced-renewal option")
                charge = 0.05 + (
                    self.tape.spec.replanning_cost if selected != previous else 0.0
                )
                resets_commitment = True
            else:
                raise ValueError("initial selection cannot be externally applied after reset")

            changed = selected != previous
            age_after = 0 if resets_commitment else age_before
            reanchored = switch or resets_commitment
            expected = DecisionRecord(
                agent=agent,
                kind=expected_kind,
                previous_option=previous,
                selected_option=selected,
                changed=changed,
                charge=charge,
                age_before=age_before,
                age_after_decision=age_after,
                switch_time=switch,
                reanchored=reanchored,
            )
            if supplied != expected:
                raise ValueError(
                    f"agent {agent} external decision metadata disagrees with exact host law; "
                    f"expected {expected!r}"
                )
            canonical.append(expected)

        trigger_count = sum(kind is not DecisionKind.NONE for kind in expected_kinds)
        if trigger_count > 1:
            self.state.simultaneous_trigger_count += 1

        # Apply the already validated tuple.  Sequential writes here cannot
        # affect legality or selection because both were frozen above.
        for record in canonical:
            agent = record.agent
            resets_commitment = (
                record.kind is DecisionKind.FORCED_RENEWAL
                or (record.kind is DecisionKind.DISCRETIONARY and record.changed)
            )
            if resets_commitment:
                self.state.options[agent] = int(record.selected_option)
                self.state.option_ages[agent] = 0
                self.state.commitment_ids[agent] += 1
                self.state.renewal_count += int(record.kind is DecisionKind.FORCED_RENEWAL)
                self.state.replan_count += int(record.changed)

            if switch:
                # This is the indivisible post-action switch anchor.  A renewal
                # or termination above created the new commitment but did not
                # separately anchor it, avoiding duplicate same-time anchors.
                self._anchor(agent, "k-switch")
            elif resets_commitment:
                self._anchor(
                    agent,
                    "forced-renewal" if record.kind is DecisionKind.FORCED_RENEWAL
                    else "termination",
                )
            self.state.total_renewal_replan_cost += record.charge

        self.state.current_k = new_k
        triggered_options = [
            record.selected_option for record in canonical
            if record.kind is not DecisionKind.NONE
        ]
        self.state.option_collisions += len(triggered_options) - len(set(triggered_options))
        return tuple(canonical)

    def audit_action_set(self, target_agent: int) -> tuple[Option | None, ...]:
        previous = Option(int(self.state.options[target_agent]))
        replacements = tuple(
            Option(index) for index, allowed in enumerate(self.legal_mask(target_agent))
            if allowed and index != int(previous)
        )
        return (None,) + replacements

    def advance(self, decisions: Sequence[DecisionRecord]) -> StepRecord:
        """Execute one simultaneous low-level step from the predecision snapshot."""

        self._require_live()
        if not self.initialized or len(decisions) != AGENT_COUNT:
            raise ValueError("advance requires four initialized decision records")
        time = self.state.primitive_time
        queues_before = self.state.queues.copy()
        buffers_before = self.state.buffers.copy()
        deployable_before = self.deployable_queue()
        locations_before = self.state.locations.copy()
        energies_before = self.state.energies.copy()
        active_options = self.state.options.copy()
        tracked = np.zeros(2, dtype=np.int16)
        delivered = np.zeros(2, dtype=np.int16)
        energy_spent = np.zeros(AGENT_COUNT, dtype=np.float64)
        track_agents: list[list[int]] = [[], []]
        relay_agents: list[list[int]] = [[], []]
        for agent in range(AGENT_COUNT):
            option = Option(int(active_options[agent]))
            location = Location(int(locations_before[agent]))
            energy = float(energies_before[agent])
            if option in (Option.TRACK_L, Option.TRACK_R):
                lane = Lane.L if option is Option.TRACK_L else Lane.R
                wanted = Location.L if lane is Lane.L else Location.R
                if location is wanted and energy >= 1.0:
                    track_agents[int(lane)].append(agent)
            elif option in (Option.RELAY_L, Option.RELAY_R):
                lane = Lane.L if option is Option.RELAY_L else Lane.R
                wanted = Location.L if lane is Lane.L else Location.R
                if location is wanted and energy >= 1.0:
                    relay_agents[int(lane)].append(agent)
        capacities = 1 + self.tape.relay_capacity_coin[time].astype(np.int16)
        for lane in range(2):
            trackers = track_agents[lane]
            relayers = relay_agents[lane]
            tracked[lane] = min(int(queues_before[lane]), len(trackers))
            delivered[lane] = min(int(buffers_before[lane]), int(capacities[lane]), len(relayers))
            if trackers:
                share = float(tracked[lane]) / len(trackers)
                energy_spent[trackers] += share
            if relayers:
                share = float(delivered[lane]) / len(relayers)
                energy_spent[relayers] += share
        for agent in range(AGENT_COUNT):
            option = Option(int(active_options[agent]))
            location = Location(int(locations_before[agent]))
            energy = float(energies_before[agent])
            if option in (Option.TRANSIT_L, Option.TRANSIT_R) and energy >= 0.25:
                target = Location.L if option is Option.TRANSIT_L else Location.R
                if location is not target:
                    self.state.locations[agent] += np.int8(1 if target > location else -1)
                    energy_spent[agent] += 0.25
            elif option is Option.RETURN:
                if location is Location.BASE:
                    self.state.energies[agent] = min(ENERGY_CAPACITY, energy + 2.0)
                elif energy >= 0.25:
                    self.state.locations[agent] = int(Location.BASE)
                    energy_spent[agent] += 0.25
        if np.any(energy_spent - energies_before > 1e-12):
            raise RuntimeError("low-level action attempted to create negative energy")
        self.state.energies -= energy_spent
        self.state.energies = np.clip(self.state.energies, 0.0, ENERGY_CAPACITY)
        arrivals = np.asarray(self.physical_arrivals(time), dtype=np.int16)
        raw_queues = queues_before - tracked + arrivals
        raw_buffers = buffers_before - delivered + tracked
        queue_overflow = np.maximum(raw_queues - QUEUE_CAPACITY, 0)
        buffer_overflow = np.maximum(raw_buffers - BUFFER_CAPACITY, 0)
        overflow = int(queue_overflow.sum() + buffer_overflow.sum())
        self.state.queues = np.minimum(raw_queues, QUEUE_CAPACITY).astype(np.int16)
        self.state.buffers = np.minimum(raw_buffers, BUFFER_CAPACITY).astype(np.int16)
        decision_charge = float(sum(record.charge for record in decisions))
        reward = (
            float(delivered.sum())
            - 0.02 * float(self.state.queues.sum() + self.state.buffers.sum())
            - 2.0 * overflow
            - 0.01 * float(energy_spent.sum())
            - decision_charge
        )
        self.state.total_arrivals += int(arrivals.sum())
        self.state.total_delivered += int(delivered.sum())
        self.state.total_overflow += overflow
        self.state.total_energy_spent += float(energy_spent.sum())
        self.state.delivery_history.append((int(delivered[0]), int(delivered[1])))
        self.state.option_ages += 1
        record = StepRecord(
            primitive_time=time, k=self.state.current_k, event_active=self.event_active(time),
            physical_queues_before=(int(queues_before[0]), int(queues_before[1])),
            deployable_queues_before=deployable_before,
            buffers_before=(int(buffers_before[0]), int(buffers_before[1])),
            arrivals=(int(arrivals[0]), int(arrivals[1])),
            relay_capacity=(int(capacities[0]), int(capacities[1])),
            tracked=(int(tracked[0]), int(tracked[1])),
            delivered=(int(delivered[0]), int(delivered[1])), overflow=overflow,
            energy_spent=float(energy_spent.sum()), decision_charge=decision_charge,
            reward=reward,
            physical_queues_after=(int(self.state.queues[0]), int(self.state.queues[1])),
            buffers_after=(int(self.state.buffers[0]), int(self.state.buffers[1])),
            decisions=tuple(decisions),
        )
        self.steps.append(record)
        self._reward_sum += reward
        self.state.primitive_time += 1
        return record

    def finish(self) -> EpisodeRecord:
        if not self.done or len(self.steps) != HORIZON:
            raise RuntimeError("episode record requires exactly 256 completed primitive steps")
        if self.state.total_arrivals != self.tape.total_physical_arrivals():
            raise RuntimeError("executed arrival denominator diverged from the exogenous tape")
        denominator = max(1, self.state.total_arrivals)
        delivery_fraction = self.state.total_delivered / denominator
        failure = delivery_fraction < 0.80 or self.state.total_overflow > 0
        return EpisodeRecord(
            scenario=self.tape.spec, steps=tuple(self.steps), anchors=tuple(self.anchors),
            normalized_score=self._reward_sum / denominator, failure=failure,
            delivery_fraction=delivery_fraction, total_arrivals=self.state.total_arrivals,
            total_delivered=self.state.total_delivered, total_overflow=self.state.total_overflow,
            total_energy_spent=self.state.total_energy_spent,
            renewal_count=self.state.renewal_count, replan_count=self.state.replan_count,
            simultaneous_trigger_count=self.state.simultaneous_trigger_count,
            option_collisions=self.state.option_collisions,
        )


def option_target(option: Option) -> Location:
    option = Option(option)
    if option in (Option.TRACK_L, Option.RELAY_L, Option.TRANSIT_L):
        return Location.L
    if option in (Option.TRACK_R, Option.RELAY_R, Option.TRANSIT_R):
        return Location.R
    return Location.BASE


def discounted_audit_return(
    rewards: Sequence[float], terminal_state: PhysicalAuditState, denominator: int,
) -> float:
    """Exact normalized 16-step audit return with discounted physical potential."""

    if len(rewards) != 16 or denominator < 1:
        raise ValueError("audit return requires 16 rewards and a positive episode denominator")
    values = tuple(float(value) for value in rewards)
    if not all(isfinite(value) for value in values):
        raise ValueError("audit rewards must be finite")
    gamma = 0.99
    return (
        sum((gamma ** offset) * reward for offset, reward in enumerate(values))
        + gamma ** 16 * terminal_state.terminal_potential()
    ) / denominator


Continuation = Callable[[ServiceRelayHost], tuple[DecisionRecord, ...]]


def common_future_audit_rollout(
    predecision_host: ServiceRelayHost,
    *,
    target_agent: int,
    audit_action: Option | None,
    aligned_decisions: Sequence[DecisionRecord],
    continuation: Continuation,
) -> tuple[float, ServiceRelayHost]:
    """Run one legal 16-step action branch on the identical future tape.

    The first step holds other simultaneous actions fixed.  Starting at the
    next primitive step, ``continuation`` must supply the frozen CRTO decisions.
    The function performs no nested search and consumes at most 16 transitions.
    """

    branch = predecision_host.clone(retain_records=False)
    first = branch.apply_audit_actions(
        target_agent=target_agent, target_option=audit_action,
        aligned_decisions=aligned_decisions,
    )
    rewards = [branch.advance(first).reward]
    for _ in range(15):
        if branch.done:
            raise RuntimeError("registered audit boundary lacks 16 future primitive steps")
        decisions = continuation(branch)
        rewards.append(branch.advance(decisions).reward)
    value = discounted_audit_return(
        rewards, branch.physical_audit_state(), max(1, branch.tape.total_physical_arrivals())
    )
    return value, branch


def validate_registration() -> None:
    if tuple(option.label for option in Option) != tuple(OPTIONS):
        raise RuntimeError("host option order drifted from frozen config")
    if tuple(event.value for event in EventClass) != tuple(EVENT_CLASSES):
        raise RuntimeError("host event order drifted from frozen config")
    if tuple(regime.value for regime in (Regime.K8, Regime.K16, Regime.K4_TO_16, Regime.K16_TO_4)) != tuple(REGIMES):
        raise RuntimeError("host evaluation regime order drifted from frozen config")


validate_registration()


__all__ = [
    "AnchorRecord", "CueState", "DecisionKind", "DecisionRecord", "DeployableObservation",
    "DeployableTelemetry", "EpisodeRecord", "EventClass", "HostState", "Lane", "Location",
    "Option", "PhysicalAuditState", "Regime", "ScenarioSpec", "ScenarioTape",
    "ServiceRelayHost", "StepRecord", "balanced_scenario_specs", "build_scenario_tape",
    "common_future_audit_rollout", "discounted_audit_return", "onset_schedule",
    "option_target", "regime_index", "validate_registration",
]
