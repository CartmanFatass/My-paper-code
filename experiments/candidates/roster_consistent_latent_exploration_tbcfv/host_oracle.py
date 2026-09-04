"""Deterministic TEST-only oracle for the TBCFV rotating-perimeter host.

This module accepts only fully materialized, hand-written fixture data.  It
contains no RNG, coordinate materializer, training/evaluation adapter, or
production fallback.  The candidate native host is authoritative outside
conformance tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
from typing import Iterable


SECTORS = 120
BEACONS = 6
MAX_AGENTS = 12
MIN_AGENTS = 6
HORIZON = 64
EVENT_TICK = 24
CLAIM_PERIOD = 4
MOVE_LIMIT = 3
ACTIVE_CONTINUATION = 0
NEW_EPOCH = 1
EVENT_POSITION = -2


def _exact_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact int")
    return value


@dataclass(frozen=True)
class FixtureSpec:
    """One non-scientific, fixed host fixture.

    ``after_positions`` is aligned with ``after_keys``.  A survivor uses ``-1``
    (its physical position is retained); a newcomer uses ``EVENT_POSITION``.
    Its actual sector is supplied only at the event-time native lifecycle call,
    after the pre-boundary physical state exists.  Keys are internal runtime
    linkage and never appear in :class:`PublicObservation`.
    """

    initial_keys: tuple[int, ...]
    initial_positions: tuple[int, ...]
    after_keys: tuple[int, ...]
    after_positions: tuple[int, ...]
    event_condition: int = ACTIVE_CONTINUATION
    omega_plus: int = 0
    kappa_plus: int = 0

    def validate(self) -> None:
        initial_n = len(self.initial_keys)
        after_n = len(self.after_keys)
        if not MIN_AGENTS <= initial_n <= MAX_AGENTS:
            raise ValueError("fixture initial roster must contain 6..12 agents")
        if not MIN_AGENTS <= after_n <= MAX_AGENTS:
            raise ValueError("fixture post-boundary roster must contain 6..12 agents")
        if len(self.initial_positions) != initial_n:
            raise ValueError("initial key/position lengths differ")
        if len(self.after_positions) != after_n:
            raise ValueError("post-boundary key/position lengths differ")
        for name, values in (
            ("initial_keys", self.initial_keys),
            ("initial_positions", self.initial_positions),
            ("after_keys", self.after_keys),
            ("after_positions", self.after_positions),
        ):
            for value in values:
                _exact_int(value, name)
        if len(set(self.initial_keys)) != initial_n or len(set(self.after_keys)) != after_n:
            raise ValueError("physical-agent fixture keys must be unique within each roster")
        if any(not 0 <= position < SECTORS for position in self.initial_positions):
            raise ValueError("initial positions must be perimeter sectors")
        if len(set(self.initial_positions)) != initial_n:
            raise ValueError("initial positions must be sampled without replacement")
        initial = set(self.initial_keys)
        after = set(self.after_keys)
        if after_n > initial_n and not initial.issubset(after):
            raise ValueError("expansion must retain every survivor")
        if after_n < initial_n and not after.issubset(initial):
            raise ValueError("contraction cannot introduce newcomers")
        if after_n == initial_n and tuple(self.after_keys) != tuple(self.initial_keys):
            raise ValueError("a static fixture cannot replace or reorder the roster")
        for key, position in zip(self.after_keys, self.after_positions):
            if key in initial:
                if position != -1:
                    raise ValueError("a survivor must retain its position using the -1 sentinel")
            else:
                if position != EVENT_POSITION:
                    raise ValueError("a newcomer must use the event-position sentinel")
        condition = _exact_int(self.event_condition, "event_condition")
        if condition == ACTIVE_CONTINUATION:
            if self.omega_plus != 0 or self.kappa_plus != 0:
                raise ValueError("active continuation has zero epoch offsets")
        elif condition == NEW_EPOCH:
            if self.omega_plus not in (5, 10, 15):
                raise ValueError("new-epoch omega_plus must be 5, 10, or 15")
            if self.kappa_plus not in (1, 2, 3, 4, 5):
                raise ValueError("new-epoch kappa_plus must be in 1..5")
        else:
            raise ValueError("unknown event condition")


@dataclass(frozen=True)
class StepInput:
    """Claims aligned with the public angular order in the current snapshot."""

    claims: tuple[int, ...] = ()

    @classmethod
    def no_claims(cls) -> "StepInput":
        return cls(())

    def validate(self, *, claim_required: bool, agent_count: int) -> None:
        for claim in self.claims:
            _exact_int(claim, "claim")
        expected = agent_count if claim_required else 0
        if len(self.claims) != expected:
            raise ValueError(f"expected {expected} simultaneous claims, got {len(self.claims)}")
        if any(not 0 <= claim < BEACONS for claim in self.claims):
            raise ValueError("every claim must be in the fully legal six-way support")


@dataclass(frozen=True)
class EventInput:
    """Event-time newcomer sectors, in ``after_keys`` newcomer order."""

    newcomer_positions: tuple[int, ...] = ()

    def validate_shape(self, expected_newcomers: int) -> None:
        if len(self.newcomer_positions) != expected_newcomers:
            raise ValueError(
                f"expected {expected_newcomers} event-time newcomer positions, "
                f"got {len(self.newcomer_positions)}"
            )
        for position in self.newcomer_positions:
            _exact_int(position, "newcomer_position")
            if not 0 <= position < SECTORS:
                raise ValueError("newcomer positions must be perimeter sectors")
        if len(set(self.newcomer_positions)) != len(self.newcomer_positions):
            raise ValueError("newcomer positions must be without replacement")


@dataclass(frozen=True)
class PublicObservation:
    """The complete actor/model-visible host payload.

    Physical-agent transport keys are intentionally absent.  They are runtime
    linkage metadata, not a public scientific observation or model feature.
    """

    tick: int
    claim_required: bool
    roster_event: bool
    new_epoch: bool
    positions: tuple[int, ...]
    angular_ranks: tuple[int, ...]
    previous_displacements: tuple[int, ...]
    newcomers: tuple[bool, ...]
    beacon_positions: tuple[int, ...]
    demands: tuple[int, ...]


@dataclass(frozen=True)
class Snapshot:
    """Full runtime snapshot.

    ``transport_keys`` is aligned row-for-row with the agent arrays and is
    stable for a physical agent through sorting, crossing, and roster churn.
    It is internal transport metadata only.  Actor/model consumers must use
    :meth:`public_observation`, which deliberately excludes it.
    """

    tick: int
    terminal: bool
    event_input_required: bool
    claim_required: bool
    roster_event: bool
    new_epoch: bool
    positions: tuple[int, ...]
    transport_keys: tuple[int, ...]
    angular_ranks: tuple[int, ...]
    previous_displacements: tuple[int, ...]
    newcomers: tuple[bool, ...]
    current_claims: tuple[int, ...]
    beacon_positions: tuple[int, ...]
    demands: tuple[int, ...]
    last_coverage: tuple[int, ...]
    last_u: float | None
    last_fragmentation: float | None
    accumulated_u: float
    accumulated_post_u: float
    accumulated_fragmentation: float
    tau: int | None
    U: float | None
    F: float | None
    Y: float | None

    def public_observation(self) -> PublicObservation:
        if self.event_input_required:
            raise RuntimeError("pre-event tick-24 state is lifecycle metadata, not actor input")
        return PublicObservation(
            tick=self.tick,
            claim_required=self.claim_required,
            roster_event=self.roster_event,
            new_epoch=self.new_epoch,
            positions=self.positions,
            angular_ranks=self.angular_ranks,
            previous_displacements=self.previous_displacements,
            newcomers=self.newcomers,
            beacon_positions=self.beacon_positions,
            demands=self.demands,
        )


@dataclass
class _Agent:
    key: int
    position: int
    previous_displacement: int
    newcomer: bool
    claim: int
    entry_order: int


class OracleHost:
    """Transactional scalar reference used only by deterministic tests."""

    def __init__(self, fixture: FixtureSpec):
        fixture.validate()
        self.fixture = fixture
        self.tick = 0
        self.terminal = False
        self._omega = 0
        self._kappa = 0
        self._roster_event = False
        self._new_epoch = False
        self._event_input_required = False
        self._agents = [
            _Agent(key, position, 0, False, -1, index)
            for index, (key, position) in enumerate(
                zip(fixture.initial_keys, fixture.initial_positions)
            )
        ]
        self._sum_u = 0.0
        self._sum_post_u = 0.0
        self._sum_fragmentation = 0.0
        self._post_claim_count = 0
        self._zero_run = 0
        self._tau: int | None = None
        self._last_u: float | None = None
        self._last_fragmentation: float | None = None
        self._last_coverage = (0,) * BEACONS

    def _ordered_agents(self) -> list[_Agent]:
        return sorted(self._agents, key=lambda agent: (agent.position, agent.entry_order))

    def _beacons(self, tick: int | None = None) -> tuple[int, ...]:
        at = min(self.tick, HORIZON - 1) if tick is None else tick
        return tuple((20 * index + at // 4 + self._omega) % SECTORS for index in range(BEACONS))

    def _demands(self, tick: int | None = None) -> tuple[int, ...]:
        at = min(self.tick, HORIZON - 1) if tick is None else tick
        n = len(self._agents)
        base, remainder = divmod(n, BEACONS)
        phase = (at // 8 + self._kappa) % BEACONS
        extra = {(phase + offset) % BEACONS for offset in range(remainder)}
        return tuple(base + int(index in extra) for index in range(BEACONS))

    def snapshot(self) -> Snapshot:
        ordered = self._ordered_agents()
        positions = tuple(agent.position for agent in ordered)
        terminal = self.terminal
        tick = self.tick
        return Snapshot(
            tick=tick,
            terminal=terminal,
            event_input_required=(not terminal and self._event_input_required),
            claim_required=(
                not terminal
                and not self._event_input_required
                and tick % CLAIM_PERIOD == 0
            ),
            roster_event=(not terminal and self._roster_event),
            new_epoch=(not terminal and self._new_epoch),
            positions=positions,
            transport_keys=tuple(agent.key for agent in ordered),
            angular_ranks=tuple(range(len(ordered))),
            previous_displacements=tuple(agent.previous_displacement for agent in ordered),
            newcomers=tuple(agent.newcomer for agent in ordered),
            current_claims=tuple(agent.claim for agent in ordered),
            beacon_positions=self._beacons(),
            demands=self._demands(),
            last_coverage=self._last_coverage,
            last_u=self._last_u,
            last_fragmentation=self._last_fragmentation,
            accumulated_u=self._sum_u,
            accumulated_post_u=self._sum_post_u,
            accumulated_fragmentation=self._sum_fragmentation,
            tau=self._tau if terminal else None,
            U=(self._sum_post_u / 40.0) if terminal else None,
            F=(self._sum_fragmentation / 10.0) if terminal else None,
            Y=(1.0 - self._sum_u / 64.0) if terminal else None,
        )

    def _install_boundary(self, event: EventInput) -> None:
        fixture = self.fixture
        by_key = {agent.key: agent for agent in self._agents}
        expected_newcomers = sum(key not in by_key for key in fixture.after_keys)
        event.validate_shape(expected_newcomers)
        new_agents: list[_Agent] = []
        occupied: set[int] = set()
        next_entry = max((agent.entry_order for agent in self._agents), default=-1) + 1
        newcomer_index = 0
        for key in fixture.after_keys:
            survivor = by_key.get(key)
            if survivor is not None:
                survivor.newcomer = False
                new_agents.append(survivor)
                occupied.add(survivor.position)
            else:
                supplied_position = event.newcomer_positions[newcomer_index]
                newcomer_index += 1
                if supplied_position in occupied:
                    raise ValueError("newcomer entry sector is occupied at the boundary")
                new_agents.append(_Agent(key, supplied_position, 0, True, -1, next_entry))
                next_entry += 1
                occupied.add(supplied_position)
        # Newcomers may precede survivors in after_keys, so check all current
        # survivor sectors after constructing the proposed roster.
        survivor_positions = {agent.position for agent in new_agents if agent.key in by_key}
        newcomer_positions = {agent.position for agent in new_agents if agent.key not in by_key}
        if survivor_positions & newcomer_positions:
            raise ValueError("newcomer entry sector is occupied by a survivor")
        self._agents = new_agents
        self._roster_event = len(fixture.initial_keys) != len(fixture.after_keys)
        self._new_epoch = fixture.event_condition == NEW_EPOCH
        if self._new_epoch:
            self._omega = fixture.omega_plus
            self._kappa = fixture.kappa_plus
        self._event_input_required = False

    def _prepare_tick(self) -> None:
        self._roster_event = False
        self._new_epoch = False
        for agent in self._agents:
            agent.newcomer = False
        if self.tick == EVENT_TICK:
            self._event_input_required = True

    def _apply_event_in_place(self, event: EventInput) -> Snapshot:
        if self.terminal or self.tick != EVENT_TICK or not self._event_input_required:
            raise RuntimeError("event input is not valid in the current lifecycle state")
        self._install_boundary(event)
        return self.snapshot()

    def apply_event(self, event: EventInput) -> Snapshot:
        """Install the t=24 mutation transactionally before public observation."""
        trial = copy.deepcopy(self)
        result = trial._apply_event_in_place(event)
        self.__dict__.clear()
        self.__dict__.update(trial.__dict__)
        return result

    @staticmethod
    def _movement(position: int, target: int) -> int:
        clockwise = (target - position) % SECTORS
        if clockwise <= SECTORS // 2:
            return min(MOVE_LIMIT, clockwise)
        return -min(MOVE_LIMIT, SECTORS - clockwise)

    def _step_in_place(self, action: StepInput) -> Snapshot:
        if self.terminal:
            raise RuntimeError("cannot step a terminal host")
        if self._event_input_required:
            raise RuntimeError("event input must be applied before the t=24 claim")
        claim_required = self.tick % CLAIM_PERIOD == 0
        ordered = self._ordered_agents()
        action.validate(claim_required=claim_required, agent_count=len(ordered))
        if claim_required:
            for agent, claim in zip(ordered, action.claims):
                agent.claim = claim
        beacons = self._beacons(self.tick)
        demands = self._demands(self.tick)
        for agent in self._agents:
            if agent.claim < 0:
                raise RuntimeError("an agent has no current claim")
            displacement = self._movement(agent.position, beacons[agent.claim])
            agent.position = (agent.position + displacement) % SECTORS
            agent.previous_displacement = displacement
        coverage = [0] * BEACONS
        for beacon_index, beacon_position in enumerate(beacons):
            for agent in self._agents:
                delta = abs(agent.position - beacon_position)
                if min(delta, SECTORS - delta) <= 2:
                    coverage[beacon_index] += 1
        unserved_units = sum(max(demand - count, 0) for demand, count in zip(demands, coverage))
        u = unserved_units / len(self._agents)
        self._sum_u += u
        self._last_u = u
        self._last_coverage = tuple(coverage)
        self._last_fragmentation = None
        if self.tick >= EVENT_TICK:
            self._sum_post_u += u
            if u == 0.0:
                self._zero_run += 1
                if self._zero_run == 4 and self._tau is None:
                    start = self.tick - 3 - EVENT_TICK
                    if 0 <= start <= 36:
                        self._tau = start
            else:
                self._zero_run = 0
            if claim_required:
                claim_counts = [0] * BEACONS
                for agent in self._agents:
                    claim_counts[agent.claim] += 1
                shortfall = sum(
                    max(demand - count, 0)
                    for demand, count in zip(demands, claim_counts)
                )
                fragmentation = shortfall / len(self._agents)
                self._sum_fragmentation += fragmentation
                self._post_claim_count += 1
                self._last_fragmentation = fragmentation
        self.tick += 1
        if self.tick == HORIZON:
            self.terminal = True
            if self._tau is None:
                self._tau = 40
        else:
            self._prepare_tick()
        return self.snapshot()

    def step(self, action: StepInput) -> Snapshot:
        """Advance transactionally; malformed calls leave this host unchanged."""
        trial = copy.deepcopy(self)
        result = trial._step_in_place(action)
        self.__dict__.clear()
        self.__dict__.update(trial.__dict__)
        return result


@dataclass(frozen=True)
class EpisodeTape:
    fixture: FixtureSpec
    claims_by_clock: tuple[tuple[int, ...], ...]
    event_newcomer_positions: tuple[int, ...] = ()

    def validate(self) -> None:
        self.fixture.validate()
        expected_newcomers = sum(
            key not in set(self.fixture.initial_keys) for key in self.fixture.after_keys
        )
        EventInput(self.event_newcomer_positions).validate_shape(expected_newcomers)
        if len(self.claims_by_clock) != HORIZON // CLAIM_PERIOD:
            raise ValueError("an episode tape must contain exactly sixteen claim rows")
        pre_n = len(self.fixture.initial_keys)
        post_n = len(self.fixture.after_keys)
        for index, claims in enumerate(self.claims_by_clock):
            expected = pre_n if index < EVENT_TICK // CLAIM_PERIOD else post_n
            StepInput(tuple(claims)).validate(claim_required=True, agent_count=expected)


def run_oracle_trace(case: EpisodeTape) -> tuple[Snapshot, ...]:
    """Return reset plus all 64 snapshots for one hand-written fixture tape."""
    case.validate()
    host = OracleHost(case.fixture)
    trace = [host.snapshot()]
    clock_index = 0
    for tick in range(HORIZON):
        if tick % CLAIM_PERIOD == 0:
            action = StepInput(tuple(case.claims_by_clock[clock_index]))
            clock_index += 1
        else:
            action = StepInput.no_claims()
        snapshot = host.step(action)
        if snapshot.event_input_required:
            snapshot = host.apply_event(EventInput(case.event_newcomer_positions))
        trace.append(snapshot)
    return tuple(trace)


def run_oracle_batch(cases: Iterable[EpisodeTape]) -> tuple[tuple[Snapshot, ...], ...]:
    """Test helper only; deliberately scalar and never used by native loading."""
    return tuple(run_oracle_trace(case) for case in cases)
