"""Independent temporal-duty source for the bounded G1 mediation prototype."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from numbers import Integral
from typing import Any


HORIZON = 80
MAXIMUM_CAPACITY = 4
ACTION_DOMAIN = frozenset((-1, 0, 1))
_SPLIT_DURATIONS = {"fitting": frozenset((6, 14)), "heldout": frozenset((10, 18))}
_SPLIT_EVENT_STEPS = {
    "fitting": (12, 16, 28, 68),
    "heldout": (13, 17, 29, 69),
}
_EVENT_NAMES = ("TEMP_LEAVE", "REJOIN", "JOIN", "TERMINAL_LEAVE")


@dataclass(frozen=True)
class G1EpisodeSpec:
    split: str
    roster_size: int
    duration: int
    sign_start: int
    rotation: int
    horizon: int
    logical_to_physical: tuple[int, ...]
    temp_target: int
    terminal_target: int
    join_target: int
    membership_events: tuple[tuple[int, str, int], ...]
    action_denominator: int
    eligible_segment_denominator: int


@dataclass(frozen=True)
class G1Observation:
    actor: tuple[float, float, float, float, float, float]


def _active_action_counts(
    roster_size: int,
    membership_events: tuple[tuple[int, str, int], ...],
) -> dict[int, int]:
    active = set(range(roster_size))
    counts = {slot: 0 for slot in range(roster_size + 1)}
    events_by_step: dict[int, list[tuple[str, int]]] = {}
    for step, event, target in membership_events:
        events_by_step.setdefault(step, []).append((event, target))

    for step in range(HORIZON):
        for event, target in events_by_step.get(step, ()):
            if event in ("TEMP_LEAVE", "TERMINAL_LEAVE"):
                active.remove(target)
            elif event in ("REJOIN", "JOIN"):
                active.add(target)
        for target in active:
            counts[target] += 1
    return counts


def make_episode_spec(
    split: str,
    roster_size: int,
    duration: int,
    sign_start: int,
    rotation: int,
) -> G1EpisodeSpec:
    if split not in _SPLIT_DURATIONS:
        raise ValueError(f"split must be one of {tuple(_SPLIT_DURATIONS)}, got {split!r}")
    if type(roster_size) is not int or roster_size not in (2, 3):
        raise ValueError(f"roster_size must be 2 or 3, got {roster_size!r}")
    if type(duration) is not int or duration not in _SPLIT_DURATIONS[split]:
        raise ValueError(
            f"duration for {split!r} must be one of "
            f"{tuple(sorted(_SPLIT_DURATIONS[split]))}, got {duration!r}"
        )
    if type(sign_start) is not int or sign_start not in (-1, 1):
        raise ValueError(f"sign_start must be -1 or +1, got {sign_start!r}")
    if type(rotation) is not int or rotation not in (0, 1):
        raise ValueError(f"rotation must be 0 or 1, got {rotation!r}")

    split_shift = 0 if split == "fitting" else 1
    logical_to_physical = tuple(
        (logical_slot + rotation + split_shift) % roster_size
        for logical_slot in range(roster_size)
    )
    temp_target = logical_to_physical[1]
    terminal_target = logical_to_physical[0]
    join_target = roster_size
    targets = (temp_target, temp_target, join_target, terminal_target)
    membership_events = tuple(
        (step, event, target)
        for step, event, target in zip(
            _SPLIT_EVENT_STEPS[split], _EVENT_NAMES, targets, strict=True
        )
    )
    active_counts = _active_action_counts(roster_size, membership_events)
    action_denominator = sum(active_counts.values())
    eligible_segment_denominator = sum(
        (count + duration - 1) // duration for count in active_counts.values() if count
    )
    return G1EpisodeSpec(
        split=split,
        roster_size=roster_size,
        duration=duration,
        sign_start=sign_start,
        rotation=rotation,
        horizon=HORIZON,
        logical_to_physical=logical_to_physical,
        temp_target=temp_target,
        terminal_target=terminal_target,
        join_target=join_target,
        membership_events=membership_events,
        action_denominator=action_denominator,
        eligible_segment_denominator=eligible_segment_denominator,
    )


def _new_lifecycle(sign: int, duration: int, *, join_flag: bool) -> dict[str, Any]:
    return {
        "g": sign,
        "age": 0,
        "remaining": duration,
        "correct_count": 0,
        "terminal_streak": 0,
        "active": True,
        "terminal": False,
        "join_flag": join_flag,
        "rejoin_flag": False,
        "opportunities": 0,
    }


class TemporalDutyG1Env:
    def __init__(self, spec: G1EpisodeSpec):
        if not isinstance(spec, G1EpisodeSpec):
            raise TypeError("spec must be a G1EpisodeSpec")
        canonical = make_episode_spec(
            spec.split, spec.roster_size, spec.duration, spec.sign_start, spec.rotation
        )
        if spec != canonical:
            raise ValueError("spec does not match the canonical G1 episode manifest")
        self._spec = spec
        self._time = 0
        self._lifecycles = {
            slot: _new_lifecycle(spec.sign_start, spec.duration, join_flag=False)
            for slot in range(spec.roster_size)
        }
        self._correct_actions = 0
        self._action_opportunities = 0
        self._successful_segments = 0
        self._started_segments = spec.roster_size
        self._reward_sum = 0.0
        self._step_rewards: list[float] = []

    def observe(self) -> dict[int, G1Observation]:
        if self._time >= self._spec.horizon:
            return {}
        active_count = sum(
            1 for lifecycle in self._lifecycles.values() if lifecycle["active"]
        )
        normalized_active_count = active_count / MAXIMUM_CAPACITY
        observations: dict[int, G1Observation] = {}
        for slot in sorted(self._lifecycles):
            lifecycle = self._lifecycles[slot]
            if not lifecycle["active"]:
                continue
            cue_present = lifecycle["age"] < 2
            observations[slot] = G1Observation(
                actor=(
                    float(lifecycle["g"] if cue_present else 0),
                    float(cue_present),
                    float(lifecycle["age"] == 0),
                    float(lifecycle["join_flag"]),
                    float(lifecycle["rejoin_flag"]),
                    float(normalized_active_count),
                )
            )
        return observations

    def _utility_from_counts(self) -> float:
        action_term = self._correct_actions / self._spec.action_denominator
        segment_term = (
            self._successful_segments / self._spec.eligible_segment_denominator
        )
        return 0.75 * action_term + 0.25 * segment_term

    def _apply_membership_events(self) -> None:
        for step, event, target in self._spec.membership_events:
            if step != self._time:
                continue
            if event == "TEMP_LEAVE":
                lifecycle = self._lifecycles[target]
                if not lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("TEMP_LEAVE target is not an active lifecycle")
                lifecycle["active"] = False
            elif event == "REJOIN":
                lifecycle = self._lifecycles[target]
                if lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("REJOIN target is not a frozen lifecycle")
                lifecycle["active"] = True
                lifecycle["rejoin_flag"] = True
            elif event == "JOIN":
                if target in self._lifecycles:
                    raise RuntimeError("JOIN target already has a lifecycle")
                self._lifecycles[target] = _new_lifecycle(
                    self._spec.sign_start, self._spec.duration, join_flag=True
                )
                self._started_segments += 1
            elif event == "TERMINAL_LEAVE":
                lifecycle = self._lifecycles[target]
                if not lifecycle["active"] or lifecycle["terminal"]:
                    raise RuntimeError("TERMINAL_LEAVE target is not active")
                lifecycle["active"] = False
                lifecycle["terminal"] = True
            else:  # pragma: no cover - canonical manifests prevent this path
                raise RuntimeError(f"unknown membership event {event!r}")

    def step(self, actions: dict[int, int]) -> dict[str, object]:
        if self._time >= self._spec.horizon:
            raise RuntimeError("episode is already complete")
        if not isinstance(actions, dict):
            raise TypeError("actions must be a dict keyed by active physical slot")
        active_slots = {
            slot for slot, lifecycle in self._lifecycles.items() if lifecycle["active"]
        }
        if set(actions) != active_slots:
            raise ValueError(
                f"actions must contain exactly the active slots {sorted(active_slots)}"
            )
        normalized_actions: dict[int, int] = {}
        for slot, action in actions.items():
            if isinstance(action, bool) or not isinstance(action, Integral):
                raise ValueError(f"action for slot {slot} must be an integer in {-1, 0, 1}")
            normalized_action = int(action)
            if normalized_action not in ACTION_DOMAIN:
                raise ValueError(f"action for slot {slot} must be in {-1, 0, 1}")
            normalized_actions[slot] = normalized_action

        previous_utility = self._reward_sum
        for slot in sorted(active_slots):
            lifecycle = self._lifecycles[slot]
            correct = normalized_actions[slot] == lifecycle["g"]
            lifecycle["opportunities"] += 1
            self._action_opportunities += 1
            if correct:
                lifecycle["correct_count"] += 1
                lifecycle["terminal_streak"] += 1
                self._correct_actions += 1
            else:
                lifecycle["terminal_streak"] = 0
            lifecycle["age"] += 1
            lifecycle["remaining"] -= 1
            lifecycle["join_flag"] = False
            lifecycle["rejoin_flag"] = False

            if lifecycle["remaining"] == 0:
                if lifecycle["terminal_streak"] >= 2:
                    self._successful_segments += 1
                if self._time + 1 < self._spec.horizon:
                    lifecycle["g"] = -lifecycle["g"]
                    lifecycle["age"] = 0
                    lifecycle["remaining"] = self._spec.duration
                    lifecycle["correct_count"] = 0
                    lifecycle["terminal_streak"] = 0
                    self._started_segments += 1

        self._time += 1
        if self._time < self._spec.horizon:
            self._apply_membership_events()
        self._reward_sum = self._utility_from_counts()
        reward = self._reward_sum - previous_utility
        self._step_rewards.append(reward)
        return {
            "observations": self.observe(),
            "reward": reward,
            "done": self._time == self._spec.horizon,
            "time": self._time,
        }

    def snapshot_state(self) -> dict[str, object]:
        return deepcopy(
            {
                "version": 1,
                "spec": asdict(self._spec),
                "time": self._time,
                "lifecycles": self._lifecycles,
                "correct_actions": self._correct_actions,
                "action_opportunities": self._action_opportunities,
                "successful_segments": self._successful_segments,
                "started_segments": self._started_segments,
                "reward_sum": self._reward_sum,
                "step_rewards": tuple(self._step_rewards),
            }
        )

    @classmethod
    def from_snapshot_state(cls, state: dict[str, object]) -> "TemporalDutyG1Env":
        if not isinstance(state, dict) or state.get("version") != 1:
            raise ValueError("state is not a version-1 TemporalDutyG1Env snapshot")
        copied = deepcopy(state)
        spec_state = copied["spec"]
        if not isinstance(spec_state, dict):
            raise ValueError("snapshot spec must be a dict")
        canonical = make_episode_spec(
            str(spec_state["split"]),
            int(spec_state["roster_size"]),
            int(spec_state["duration"]),
            int(spec_state["sign_start"]),
            int(spec_state["rotation"]),
        )
        if asdict(canonical) != spec_state:
            raise ValueError("snapshot spec is not canonical")

        environment = cls.__new__(cls)
        environment._spec = canonical
        environment._time = int(copied["time"])
        environment._lifecycles = copied["lifecycles"]
        environment._correct_actions = int(copied["correct_actions"])
        environment._action_opportunities = int(copied["action_opportunities"])
        environment._successful_segments = int(copied["successful_segments"])
        environment._started_segments = int(copied["started_segments"])
        environment._reward_sum = float(copied["reward_sum"])
        environment._step_rewards = list(copied["step_rewards"])
        return environment

    def outcome(self) -> dict[str, float]:
        action_accuracy = self._correct_actions / self._spec.action_denominator
        segment_success_rate = (
            self._successful_segments / self._spec.eligible_segment_denominator
        )
        utility = 0.75 * action_accuracy + 0.25 * segment_success_rate
        return {
            "correct_actions": float(self._correct_actions),
            "action_opportunities": float(self._action_opportunities),
            "action_denominator": float(self._spec.action_denominator),
            "successful_segments": float(self._successful_segments),
            "eligible_segments": float(self._spec.eligible_segment_denominator),
            "action_accuracy": float(action_accuracy),
            "segment_success_rate": float(segment_success_rate),
            "utility": float(utility),
            "reward_sum": float(self._reward_sum),
        }
