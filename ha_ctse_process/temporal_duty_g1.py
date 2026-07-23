"""Independent formal temporal-duty source for mechanism-matched EHC G1."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from numbers import Integral
from typing import Any, Literal

import numpy as np


SOURCE_FAMILY = "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
SCHEMA_VERSION = 1
HORIZON = 80
MAXIMUM_CAPACITY = 4
DURATION_SUPPORT = (6, 10, 14, 18)
ACTION_DOMAIN = frozenset((-1, 0, 1))
PROFILE_DOMAIN = frozenset(("train", "iid", "heldout"))
_LEDGER_LENGTH = HORIZON // min(DURATION_SUPPORT) + 3
_DOMAIN_TARGET = 101
_DOMAIN_DURATION = 211
_DOMAIN_OPPORTUNITY = 307
_DOMAIN_MEMBERSHIP = {"train": 401, "iid": 401, "heldout": 409}
_DOMAIN_HISTORY_FREE = 503


@dataclass(frozen=True)
class G1LifecycleLedger:
    physical_slot: int
    logical_lifecycle: int
    targets: tuple[int, ...]
    durations: tuple[int, ...]
    opportunity_gaps: tuple[int, ...]


@dataclass(frozen=True)
class G1EpisodeSpec:
    source_family: str
    schema_version: int
    profile: str
    base_id: int
    sign_mate: int
    task_seed: int
    membership_seed: int
    duty_seed: int
    opportunity_seed: int
    horizon: int
    maximum_capacity: int
    roster_size: int
    packing_mode: str
    logical_to_physical: tuple[int, ...]
    temp_target: int
    terminal_target: int
    join_target: int
    membership_events: tuple[tuple[int, str, int], ...]
    lifecycle_ledgers: tuple[G1LifecycleLedger, ...]
    active_action_denominator: int
    started_segment_denominator: int


@dataclass(frozen=True)
class G1Observation:
    actor: tuple[float, float, float, float, float, float]
    critic: tuple[float, float, float, float, float, float, float, float, float, float]
    opportunity_kind: Literal["CREATE", "EVENT"] | None


def _checked_nonnegative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"{name} must be a nonnegative integer, got {value!r}")
    normalized = int(value)
    if normalized >= 2**63:
        raise ValueError(f"{name} must be smaller than 2**63, got {value!r}")
    return normalized


def _counter_rng(seed: int, base_id: int, domain: int, coordinate: int = 0) -> np.random.Generator:
    sequence = np.random.SeedSequence([seed, base_id, domain, coordinate])
    return np.random.Generator(np.random.Philox(sequence))


def _draw_inclusive(generator: np.random.Generator, low: int, high: int) -> int:
    return int(generator.integers(low, high + 1))


def _packing(profile: str, roster_size: int, base_id: int) -> tuple[str, tuple[int, ...]]:
    if profile != "heldout":
        return "IDENTITY", tuple(range(roster_size))
    reversed_slots = tuple(reversed(range(roster_size)))
    rotation = base_id % roster_size
    return (
        "REVERSED_ROTATED",
        reversed_slots[rotation:] + reversed_slots[:rotation],
    )


def _membership_ledger(
    profile: str,
    roster_size: int,
    logical_to_physical: tuple[int, ...],
    membership_seed: int,
    base_id: int,
) -> tuple[int, int, int, tuple[tuple[int, str, int], ...]]:
    generator = _counter_rng(
        membership_seed, base_id, _DOMAIN_MEMBERSHIP[profile], roster_size
    )
    initial_order = [int(value) for value in generator.permutation(roster_size)]
    temp_target = logical_to_physical[initial_order[0]]
    terminal_target = logical_to_physical[initial_order[1]]
    join_target = roster_size
    if profile in ("train", "iid"):
        leave = _draw_inclusive(generator, 10, 18)
        rejoin = leave + _draw_inclusive(generator, 3, 7)
        join = _draw_inclusive(generator, 28, 38)
        terminal = _draw_inclusive(generator, 58, 70)
        events = (
            (leave, "TEMP_LEAVE", temp_target),
            (rejoin, "REJOIN", temp_target),
            (join, "JOIN", join_target),
            (terminal, "TERMINAL_LEAVE", terminal_target),
        )
    else:
        join = _draw_inclusive(generator, 8, 14)
        leave = _draw_inclusive(generator, 30, 38)
        rejoin = leave + _draw_inclusive(generator, 8, 12)
        terminal = _draw_inclusive(generator, 62, 74)
        events = (
            (join, "JOIN", join_target),
            (leave, "TEMP_LEAVE", temp_target),
            (rejoin, "REJOIN", temp_target),
            (terminal, "TERMINAL_LEAVE", terminal_target),
        )
    return temp_target, terminal_target, join_target, events


def _lifecycle_ledgers(
    profile: str,
    roster_size: int,
    logical_to_physical: tuple[int, ...],
    duty_seed: int,
    opportunity_seed: int,
    base_id: int,
    sign_mate: int,
) -> tuple[G1LifecycleLedger, ...]:
    ledgers: list[G1LifecycleLedger] = []
    for logical_lifecycle in range(roster_size + 1):
        physical_slot = (
            logical_to_physical[logical_lifecycle]
            if logical_lifecycle < roster_size
            else roster_size
        )
        target_rng = _counter_rng(
            duty_seed, base_id, _DOMAIN_TARGET, logical_lifecycle
        )
        targets = tuple(
            sign_mate * (2 * int(value) - 1)
            for value in target_rng.integers(0, 2, size=_LEDGER_LENGTH)
        )
        duration_rng = _counter_rng(
            duty_seed, base_id, _DOMAIN_DURATION, logical_lifecycle
        )
        if profile == "heldout":
            offset = int(duration_rng.integers(0, len(DURATION_SUPPORT)))
            cycle = DURATION_SUPPORT[offset:] + DURATION_SUPPORT[:offset]
            durations = tuple(
                cycle[index % len(cycle)] for index in range(_LEDGER_LENGTH)
            )
        else:
            durations = tuple(
                int(DURATION_SUPPORT[int(index)])
                for index in duration_rng.integers(
                    0, len(DURATION_SUPPORT), size=_LEDGER_LENGTH
                )
            )
        opportunity_rng = _counter_rng(
            opportunity_seed, base_id, _DOMAIN_OPPORTUNITY, logical_lifecycle
        )
        opportunity_gaps = tuple(
            int(value)
            for value in opportunity_rng.integers(1, 3, size=HORIZON + 1)
        )
        ledgers.append(
            G1LifecycleLedger(
                physical_slot=physical_slot,
                logical_lifecycle=logical_lifecycle,
                targets=targets,
                durations=durations,
                opportunity_gaps=opportunity_gaps,
            )
        )
    return tuple(sorted(ledgers, key=lambda ledger: ledger.physical_slot))


def _active_at(
    slot: int,
    time: int,
    roster_size: int,
    membership_events: tuple[tuple[int, str, int], ...],
) -> bool:
    active = slot < roster_size
    for event_time, event, target in membership_events:
        if event_time > time or target != slot:
            continue
        if event in ("TEMP_LEAVE", "TERMINAL_LEAVE"):
            active = False
        elif event in ("REJOIN", "JOIN"):
            active = True
    return active


def _denominators(
    roster_size: int,
    membership_events: tuple[tuple[int, str, int], ...],
    lifecycle_ledgers: tuple[G1LifecycleLedger, ...],
) -> tuple[int, int]:
    action_denominator = 0
    started_segments = 0
    for ledger in lifecycle_ledgers:
        active_times = [
            time
            for time in range(HORIZON)
            if _active_at(
                ledger.physical_slot, time, roster_size, membership_events
            )
        ]
        if not active_times:
            continue
        started_segments += 1
        segment_index = 0
        remaining = ledger.durations[segment_index]
        for time in active_times:
            action_denominator += 1
            remaining -= 1
            if remaining == 0 and time + 1 < HORIZON:
                segment_index += 1
                started_segments += 1
                remaining = ledger.durations[segment_index]
    return action_denominator, started_segments


def make_episode_spec(
    profile: str,
    *,
    task_seed: int,
    membership_seed: int,
    duty_seed: int,
    opportunity_seed: int,
    base_id: int,
    sign_mate: int,
) -> G1EpisodeSpec:
    """Build one policy-independent, counter-generated formal G1 ledger."""

    if profile not in PROFILE_DOMAIN:
        raise ValueError(
            f"profile must be one of {tuple(sorted(PROFILE_DOMAIN))}, got {profile!r}"
        )
    task_seed = _checked_nonnegative_int("task_seed", task_seed)
    membership_seed = _checked_nonnegative_int("membership_seed", membership_seed)
    duty_seed = _checked_nonnegative_int("duty_seed", duty_seed)
    opportunity_seed = _checked_nonnegative_int("opportunity_seed", opportunity_seed)
    base_id = _checked_nonnegative_int("base_id", base_id)
    if isinstance(sign_mate, bool) or not isinstance(sign_mate, Integral) or int(sign_mate) not in (-1, 1):
        raise ValueError(f"sign_mate must be -1 or +1, got {sign_mate!r}")
    sign_mate = int(sign_mate)

    # Consecutive base IDs are exactly balanced while the task seed chooses phase.
    roster_size = 2 + ((base_id + (task_seed & 1)) % 2)
    packing_mode, logical_to_physical = _packing(profile, roster_size, base_id)
    temp_target, terminal_target, join_target, membership_events = _membership_ledger(
        profile,
        roster_size,
        logical_to_physical,
        membership_seed,
        base_id,
    )
    lifecycle_ledgers = _lifecycle_ledgers(
        profile,
        roster_size,
        logical_to_physical,
        duty_seed,
        opportunity_seed,
        base_id,
        sign_mate,
    )
    action_denominator, started_segments = _denominators(
        roster_size, membership_events, lifecycle_ledgers
    )
    return G1EpisodeSpec(
        source_family=SOURCE_FAMILY,
        schema_version=SCHEMA_VERSION,
        profile=profile,
        base_id=base_id,
        sign_mate=sign_mate,
        task_seed=task_seed,
        membership_seed=membership_seed,
        duty_seed=duty_seed,
        opportunity_seed=opportunity_seed,
        horizon=HORIZON,
        maximum_capacity=MAXIMUM_CAPACITY,
        roster_size=roster_size,
        packing_mode=packing_mode,
        logical_to_physical=logical_to_physical,
        temp_target=temp_target,
        terminal_target=terminal_target,
        join_target=join_target,
        membership_events=membership_events,
        lifecycle_ledgers=lifecycle_ledgers,
        active_action_denominator=action_denominator,
        started_segment_denominator=started_segments,
    )


def _canonical_spec(spec: G1EpisodeSpec) -> G1EpisodeSpec:
    return make_episode_spec(
        spec.profile,
        task_seed=spec.task_seed,
        membership_seed=spec.membership_seed,
        duty_seed=spec.duty_seed,
        opportunity_seed=spec.opportunity_seed,
        base_id=spec.base_id,
        sign_mate=spec.sign_mate,
    )


class TemporalDutyG1Env:
    def __init__(self, spec: G1EpisodeSpec):
        if not isinstance(spec, G1EpisodeSpec):
            raise TypeError("spec must be a G1EpisodeSpec")
        if spec != _canonical_spec(spec):
            raise ValueError("spec does not match its canonical formal G1 ledger")
        self.spec = spec
        self._ledgers = {
            ledger.physical_slot: ledger for ledger in spec.lifecycle_ledgers
        }
        self._time = 0
        self._lifecycles: dict[int, dict[str, Any]] = {}
        self._segment_records: list[dict[str, Any]] = []
        self._correct_actions = 0
        self._action_opportunities = 0
        self._successful_segments = 0
        self._completed_segments = 0
        self._started_segments = 0
        self._reward_sum = 0.0
        self._step_rewards: list[float] = []
        for slot in spec.logical_to_physical:
            self._create_lifecycle(slot, start_time=0)

    def _create_lifecycle(self, slot: int, *, start_time: int) -> None:
        ledger = self._ledgers[slot]
        lifecycle: dict[str, Any] = {
            "target": ledger.targets[0],
            "duration": ledger.durations[0],
            "age": 0,
            "remaining": ledger.durations[0],
            "correct_count": 0,
            "terminal_streak": 0,
            "segment_index": 0,
            "active_steps": 0,
            "next_opportunity_active_step": 0,
            "opportunity_index": 0,
            "create_pending": True,
            "active": True,
            "terminal": False,
            "join_flag": True,
            "rejoin_flag": False,
            "segment_record_index": -1,
        }
        self._lifecycles[slot] = lifecycle
        self._start_segment(slot, start_time=start_time)

    def _start_segment(self, slot: int, *, start_time: int) -> None:
        lifecycle = self._lifecycles[slot]
        record = {
            "slot": slot,
            "segment_index": lifecycle["segment_index"],
            "start_time": start_time,
            "end_time": None,
            "target": lifecycle["target"],
            "duration": lifecycle["duration"],
            "correct_count": None,
            "success": None,
            "status": "OPEN",
        }
        lifecycle["segment_record_index"] = len(self._segment_records)
        self._segment_records.append(record)
        self._started_segments += 1

    def _utility_from_counts(self) -> float:
        return (
            0.75
            * self._correct_actions
            / self.spec.active_action_denominator
            + 0.25
            * self._successful_segments
            / self.spec.started_segment_denominator
        )

    def observe(self) -> dict[int, G1Observation]:
        if self._time >= self.spec.horizon:
            return {}
        active_count = sum(
            int(lifecycle["active"]) for lifecycle in self._lifecycles.values()
        )
        normalized_active_count = active_count / self.spec.maximum_capacity
        result: dict[int, G1Observation] = {}
        for slot in sorted(self._lifecycles):
            lifecycle = self._lifecycles[slot]
            if not lifecycle["active"]:
                continue
            cue_present = lifecycle["age"] < 2
            actor = (
                float(lifecycle["target"] if cue_present else 0),
                float(cue_present),
                float(lifecycle["age"] == 0),
                float(lifecycle["join_flag"]),
                float(lifecycle["rejoin_flag"]),
                float(normalized_active_count),
            )
            critic = actor + (
                float(lifecycle["age"] / 18),
                float(lifecycle["remaining"] / 18),
                float(
                    lifecycle["correct_count"] / max(lifecycle["age"], 1)
                ),
                float(lifecycle["terminal_streak"] / 2),
            )
            if lifecycle["create_pending"]:
                opportunity_kind: Literal["CREATE", "EVENT"] | None = "CREATE"
            elif (
                lifecycle["active_steps"]
                == lifecycle["next_opportunity_active_step"]
            ):
                opportunity_kind = "EVENT"
            else:
                opportunity_kind = None
            result[slot] = G1Observation(actor, critic, opportunity_kind)
        return result

    def oracle_actions(self) -> dict[int, int]:
        """Registered persistent oracle: act directly on the hidden current target."""

        return {
            slot: int(lifecycle["target"])
            for slot, lifecycle in sorted(self._lifecycles.items())
            if lifecycle["active"]
        }

    def history_free_actions(self, *, seed: int) -> dict[int, int]:
        """Registered stateless control: visible cue, then a fair coordinate sign."""

        seed = _checked_nonnegative_int("seed", seed)
        result: dict[int, int] = {}
        for slot, observation in self.observe().items():
            if observation.actor[1] == 1.0:
                result[slot] = int(observation.actor[0])
            else:
                generator = _counter_rng(
                    seed,
                    self.spec.base_id,
                    _DOMAIN_HISTORY_FREE + self._time,
                    slot,
                )
                result[slot] = 2 * int(generator.integers(0, 2)) - 1
        return result

    def _censor_segment(self, slot: int, *, status: str, end_time: int) -> dict[str, Any]:
        lifecycle = self._lifecycles[slot]
        record = self._segment_records[lifecycle["segment_record_index"]]
        if record["status"] != "OPEN":
            raise RuntimeError("only an open segment can be censored")
        record.update(
            end_time=end_time,
            correct_count=lifecycle["correct_count"],
            success=False,
            status=status,
        )
        return deepcopy(record)

    def _apply_membership_events(self) -> list[dict[str, Any]]:
        censored: list[dict[str, Any]] = []
        for event_time, event, target in self.spec.membership_events:
            if event_time != self._time:
                continue
            if event == "TEMP_LEAVE":
                lifecycle = self._lifecycles[target]
                if not lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("TEMP_LEAVE target is not active")
                lifecycle["active"] = False
                lifecycle["rejoin_flag"] = False
            elif event == "REJOIN":
                lifecycle = self._lifecycles[target]
                if lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("REJOIN target is not frozen")
                lifecycle["active"] = True
                lifecycle["rejoin_flag"] = True
            elif event == "JOIN":
                if target in self._lifecycles:
                    raise RuntimeError("JOIN target already exists")
                self._create_lifecycle(target, start_time=self._time)
            elif event == "TERMINAL_LEAVE":
                lifecycle = self._lifecycles[target]
                if not lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("TERMINAL_LEAVE target is not active")
                censored.append(
                    self._censor_segment(
                        target,
                        status="CENSORED_TERMINAL",
                        end_time=self._time,
                    )
                )
                lifecycle["active"] = False
                lifecycle["terminal"] = True
            else:  # pragma: no cover - canonical ledgers exclude this path
                raise RuntimeError(f"unknown membership event {event!r}")
        return censored

    def step(self, actions: dict[int, int]) -> dict[str, object]:
        if self._time >= self.spec.horizon:
            raise RuntimeError("episode is already complete")
        if not isinstance(actions, dict):
            raise TypeError("actions must be a dict keyed by active physical slot")
        observations = self.observe()
        active_slots = set(observations)
        if set(actions) != active_slots:
            raise ValueError(
                f"actions must contain exactly the active slots {sorted(active_slots)}"
            )
        normalized_actions: dict[int, int] = {}
        for slot, action in actions.items():
            if isinstance(action, bool) or not isinstance(action, Integral):
                raise ValueError(f"action for slot {slot} must be an integer in {-1, 0, 1}")
            normalized = int(action)
            if normalized not in ACTION_DOMAIN:
                raise ValueError(f"action for slot {slot} must be in {-1, 0, 1}")
            normalized_actions[slot] = normalized

        previous_utility = self._utility_from_counts()
        segment_events: list[dict[str, Any]] = []
        opportunity_events = {
            slot: observation.opportunity_kind
            for slot, observation in observations.items()
            if observation.opportunity_kind is not None
        }
        for slot in sorted(active_slots):
            lifecycle = self._lifecycles[slot]
            ledger = self._ledgers[slot]
            correct = normalized_actions[slot] == lifecycle["target"]
            self._action_opportunities += 1
            if correct:
                lifecycle["correct_count"] += 1
                lifecycle["terminal_streak"] = min(
                    2, lifecycle["terminal_streak"] + 1
                )
                self._correct_actions += 1
            else:
                lifecycle["terminal_streak"] = 0

            if observations[slot].opportunity_kind is not None:
                gap = ledger.opportunity_gaps[lifecycle["opportunity_index"]]
                lifecycle["opportunity_index"] += 1
                lifecycle["next_opportunity_active_step"] = (
                    lifecycle["active_steps"] + gap
                )
                lifecycle["create_pending"] = False
            lifecycle["active_steps"] += 1
            lifecycle["age"] += 1
            lifecycle["remaining"] -= 1
            lifecycle["join_flag"] = False
            lifecycle["rejoin_flag"] = False

            if lifecycle["remaining"] == 0:
                self._completed_segments += 1
                success = (
                    4 * lifecycle["correct_count"]
                    >= 3 * lifecycle["duration"]
                    and lifecycle["terminal_streak"] >= 2
                )
                self._successful_segments += int(success)
                record = self._segment_records[lifecycle["segment_record_index"]]
                record.update(
                    end_time=self._time + 1,
                    correct_count=lifecycle["correct_count"],
                    success=success,
                    status="COMPLETED",
                )
                segment_events.append(deepcopy(record))
                if self._time + 1 < self.spec.horizon:
                    lifecycle["segment_index"] += 1
                    segment_index = lifecycle["segment_index"]
                    lifecycle.update(
                        target=ledger.targets[segment_index],
                        duration=ledger.durations[segment_index],
                        age=0,
                        remaining=ledger.durations[segment_index],
                        correct_count=0,
                        terminal_streak=0,
                    )
                    self._start_segment(slot, start_time=self._time + 1)

        self._time += 1
        if self._time < self.spec.horizon:
            segment_events.extend(self._apply_membership_events())
        else:
            for slot, lifecycle in sorted(self._lifecycles.items()):
                if lifecycle["active"]:
                    record = self._segment_records[lifecycle["segment_record_index"]]
                    if record["status"] == "OPEN":
                        segment_events.append(
                            self._censor_segment(
                                slot,
                                status="CENSORED_HORIZON",
                                end_time=self._time,
                            )
                        )

        self._reward_sum = self._utility_from_counts()
        reward = self._reward_sum - previous_utility
        self._step_rewards.append(reward)
        return {
            "observations": self.observe(),
            "reward": reward,
            "done": self._time == self.spec.horizon,
            "time": self._time,
            "opportunities": opportunity_events,
            "segment_events": tuple(segment_events),
        }

    def snapshot_state(self) -> dict[str, object]:
        return deepcopy(
            {
                "version": 2,
                "source_family": SOURCE_FAMILY,
                "spec": asdict(self.spec),
                "time": self._time,
                "lifecycles": self._lifecycles,
                "segment_records": self._segment_records,
                "correct_actions": self._correct_actions,
                "action_opportunities": self._action_opportunities,
                "successful_segments": self._successful_segments,
                "completed_segments": self._completed_segments,
                "started_segments": self._started_segments,
                "reward_sum": self._reward_sum,
                "step_rewards": tuple(self._step_rewards),
            }
        )

    @classmethod
    def from_snapshot_state(cls, state: dict[str, object]) -> "TemporalDutyG1Env":
        if (
            not isinstance(state, dict)
            or state.get("version") != 2
            or state.get("source_family") != SOURCE_FAMILY
        ):
            raise ValueError("state is not a formal TemporalDutyG1Env snapshot")
        copied = deepcopy(state)
        spec_state = copied.get("spec")
        if not isinstance(spec_state, dict):
            raise ValueError("snapshot spec must be a dict")
        try:
            canonical = make_episode_spec(
                str(spec_state["profile"]),
                task_seed=spec_state["task_seed"],
                membership_seed=spec_state["membership_seed"],
                duty_seed=spec_state["duty_seed"],
                opportunity_seed=spec_state["opportunity_seed"],
                base_id=spec_state["base_id"],
                sign_mate=spec_state["sign_mate"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("snapshot spec is invalid") from error
        if asdict(canonical) != spec_state:
            raise ValueError("snapshot spec is not canonical")
        time = copied.get("time")
        if isinstance(time, bool) or not isinstance(time, Integral) or not 0 <= int(time) <= HORIZON:
            raise ValueError("snapshot time is outside the episode horizon")

        environment = cls(canonical)
        environment._time = int(time)
        environment._lifecycles = copied["lifecycles"]
        environment._segment_records = copied["segment_records"]
        environment._correct_actions = int(copied["correct_actions"])
        environment._action_opportunities = int(copied["action_opportunities"])
        environment._successful_segments = int(copied["successful_segments"])
        environment._completed_segments = int(copied["completed_segments"])
        environment._started_segments = int(copied["started_segments"])
        environment._reward_sum = float(copied["reward_sum"])
        environment._step_rewards = list(copied["step_rewards"])
        if set(environment._lifecycles) - set(environment._ledgers):
            raise ValueError("snapshot contains an unknown lifecycle slot")
        if environment._started_segments > canonical.started_segment_denominator:
            raise ValueError("snapshot exceeds the registered segment denominator")
        if environment._action_opportunities > canonical.active_action_denominator:
            raise ValueError("snapshot exceeds the registered action denominator")
        if environment._reward_sum != environment._utility_from_counts():
            raise ValueError("snapshot reward sum does not match its utility counts")
        return environment

    def outcome(self) -> dict[str, float]:
        action_accuracy = (
            self._correct_actions / self.spec.active_action_denominator
        )
        segment_success_rate = (
            self._successful_segments / self.spec.started_segment_denominator
        )
        utility = 0.75 * action_accuracy + 0.25 * segment_success_rate
        return {
            "correct_actions": float(self._correct_actions),
            "action_opportunities": float(self._action_opportunities),
            "action_denominator": float(self.spec.active_action_denominator),
            "successful_segments": float(self._successful_segments),
            "completed_segments": float(self._completed_segments),
            "started_segments": float(self._started_segments),
            "eligible_segments": float(self.spec.started_segment_denominator),
            "action_accuracy": float(action_accuracy),
            "segment_success_rate": float(segment_success_rate),
            "utility": float(utility),
            "reward_sum": float(self._reward_sum),
        }
