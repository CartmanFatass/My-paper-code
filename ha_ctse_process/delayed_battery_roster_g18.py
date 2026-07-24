"""Minimal delayed-service information gate for the G18 toy boundary.

The source has no UAV radio, motion, station geometry, queueing or shaped
energy reward.  Utility is only the externally served demand fraction.  A
low-demand allocation changes battery state before an announced charging
rotation and a temporary demand spike, so equal current service can have
different later service consequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


CAPACITY = 6
ACTION_DIM = 1
OBSERVATION_DIM = 8
CRITIC_STATE_DIM = 6
HORIZON = 12
TEMPORARY_LEAVE_TIME = 6
RETURN_TIME = 10
ENERGY_PER_EFFORT = 0.25
INACTIVE_CHARGE_PER_STEP = 0.25
LOW_DEMAND = 1.0
SPIKE_DEMAND = 2.0

PASS_BRANCH = "PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18"
FAIL_BRANCH = "FAIL_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18"

GATE_SLOT_ORDERS = (
    (0, 1, 2, 3, 4, 5),
    (3, 5, 0, 4, 1, 2),
    (5, 2, 4, 1, 3, 0),
)


@dataclass(frozen=True)
class MembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class BatteryRosterLedger:
    slot_order: tuple[int, ...]
    persistent_keys: tuple[int, int]
    rotating_keys: tuple[int, int]
    fresh_key: int
    padding_key: int
    terminal_leave_key: int

    @property
    def initial_keys(self) -> tuple[int, ...]:
        return self.persistent_keys + self.rotating_keys

    def validate(self) -> None:
        if len(self.slot_order) != CAPACITY or set(self.slot_order) != set(
            range(CAPACITY)
        ):
            raise ValueError("G18 slot order must be a capacity-wide permutation")
        inventory = (
            self.persistent_keys
            + self.rotating_keys
            + (self.fresh_key, self.padding_key)
        )
        if len(set(inventory)) != CAPACITY:
            raise ValueError("G18 lifecycle inventory collides")
        if self.terminal_leave_key not in self.persistent_keys:
            raise ValueError("G18 terminal leave must reference a persistent lifecycle")


def make_ledger(slot_order: Sequence[int] = GATE_SLOT_ORDERS[0]) -> BatteryRosterLedger:
    order = tuple(int(value) for value in slot_order)
    if len(order) != CAPACITY:
        raise ValueError("G18 slot order length mismatch")
    ledger = BatteryRosterLedger(
        slot_order=order,
        persistent_keys=(order[0], order[1]),
        rotating_keys=(order[2], order[3]),
        fresh_key=order[4],
        padding_key=order[5],
        terminal_leave_key=order[0],
    )
    ledger.validate()
    return ledger


@dataclass(frozen=True)
class BatteryRosterView:
    time: int
    observations: np.ndarray
    active_mask: np.ndarray
    critic_state: np.ndarray
    membership_change: MembershipChange
    demand: float
    battery: np.ndarray
    rotating_mask: np.ndarray


@dataclass(frozen=True)
class BatteryRosterOutcome:
    utility: float
    minimum_step_utility: float
    future_service_deficit: float
    reward_trace: tuple[float, ...]
    served_trace: tuple[float, ...]
    roster_sizes: tuple[int, ...]


class BatteryRosterEnv:
    """Twelve-step dynamic-roster carrier with policy-dependent battery state."""

    def __init__(self, ledger: BatteryRosterLedger):
        ledger.validate()
        self.ledger = ledger
        self.time = 0
        self.active = np.zeros(CAPACITY, dtype=np.bool_)
        self.active[np.asarray(ledger.initial_keys, dtype=np.int64)] = True
        self.charging = np.zeros(CAPACITY, dtype=np.bool_)
        self.battery = np.zeros(CAPACITY, dtype=np.float64)
        self.battery[np.asarray(ledger.initial_keys, dtype=np.int64)] = 1.0
        self.previous_effort = np.zeros(CAPACITY, dtype=np.float32)
        self.age = np.zeros(CAPACITY, dtype=np.int64)
        self.reward_trace: list[float] = []
        self.served_trace: list[float] = []
        self.roster_sizes: list[int] = []
        self._prepared_time: int | None = None
        self._membership_change = MembershipChange(joined=ledger.initial_keys)
        self._terminated = False

    @staticmethod
    def demand_at(time: int) -> float:
        return (
            SPIKE_DEMAND
            if TEMPORARY_LEAVE_TIME <= int(time) < RETURN_TIME
            else LOW_DEMAND
        )

    def _prepare_membership(self) -> None:
        if self._prepared_time == self.time:
            return
        change = MembershipChange()
        if self.time == TEMPORARY_LEAVE_TIME:
            keys = self.ledger.rotating_keys
            index = np.asarray(keys, dtype=np.int64)
            self.active[index] = False
            self.charging[index] = True
            change = MembershipChange(temporarily_left=keys)
        elif self.time == RETURN_TIME:
            rotating = self.ledger.rotating_keys
            rotating_index = np.asarray(rotating, dtype=np.int64)
            self.charging[rotating_index] = False
            self.active[rotating_index] = True
            self.active[self.ledger.terminal_leave_key] = False
            self.active[self.ledger.fresh_key] = True
            self.battery[self.ledger.fresh_key] = 1.0
            self.previous_effort[self.ledger.fresh_key] = 0.0
            self.age[self.ledger.fresh_key] = 0
            change = MembershipChange(
                joined=(self.ledger.fresh_key,),
                rejoined=rotating,
                terminally_left=(self.ledger.terminal_leave_key,),
            )
        self._membership_change = change
        self._prepared_time = self.time

    def observe(self) -> BatteryRosterView:
        if self._terminated or self.time >= HORIZON:
            raise RuntimeError("G18 cannot observe a terminal environment")
        self._prepare_membership()
        active_keys = np.flatnonzero(self.active)
        if active_keys.size == 0:
            raise RuntimeError("G18 source produced an empty active roster")
        demand = self.demand_at(self.time)
        rotating_mask = np.zeros(CAPACITY, dtype=np.bool_)
        rotating_mask[np.asarray(self.ledger.rotating_keys, dtype=np.int64)] = True
        observations = np.zeros(
            (CAPACITY, OBSERVATION_DIM), dtype=np.float32
        )
        observations[active_keys, 0] = self.battery[active_keys]
        observations[active_keys, 1] = demand / SPIKE_DEMAND
        observations[active_keys, 2] = active_keys.size / CAPACITY
        observations[active_keys, 3] = self.age[active_keys] / HORIZON
        observations[active_keys, 4] = self.previous_effort[active_keys]
        observations[active_keys, 5] = rotating_mask[active_keys]
        observations[active_keys, 6] = self.time / (HORIZON - 1)
        observations[active_keys, 7] = float(
            TEMPORARY_LEAVE_TIME <= self.time < RETURN_TIME
        )
        persistent_battery = self.battery[
            np.asarray(self.ledger.persistent_keys, dtype=np.int64)
        ].mean()
        rotating_battery = self.battery[
            np.asarray(self.ledger.rotating_keys, dtype=np.int64)
        ].mean()
        critic_state = np.asarray(
            (
                demand / SPIKE_DEMAND,
                active_keys.size / CAPACITY,
                persistent_battery,
                rotating_battery,
                self.time / (HORIZON - 1),
                float(TEMPORARY_LEAVE_TIME <= self.time < RETURN_TIME),
            ),
            dtype=np.float32,
        )
        return BatteryRosterView(
            time=self.time,
            observations=observations,
            active_mask=self.active.copy(),
            critic_state=critic_state,
            membership_change=self._membership_change,
            demand=demand,
            battery=self.battery.copy(),
            rotating_mask=rotating_mask,
        )

    def step(self, actions: np.ndarray) -> tuple[float, bool, dict[str, float]]:
        if self._terminated:
            raise RuntimeError("G18 cannot step a terminal environment")
        view = self.observe()
        values = np.asarray(actions, dtype=np.float32)
        if values.shape != (CAPACITY, ACTION_DIM) or not np.isfinite(values).all():
            raise ValueError("G18 action shape/finite contract mismatch")
        if np.any(values < -1.0) or np.any(values > 1.0):
            raise ValueError("G18 action left tanh support")
        if np.count_nonzero(values[~view.active_mask]) != 0:
            raise ValueError("G18 inactive lifecycle received a physical action")

        active_keys = np.flatnonzero(view.active_mask)
        requested = (values[active_keys, 0].astype(np.float64) + 1.0) / 2.0
        available = self.battery[active_keys] / ENERGY_PER_EFFORT
        executed = np.minimum(requested, available)
        served = float(min(view.demand, executed.sum(dtype=np.float64)))
        utility = served / view.demand
        self.battery[active_keys] -= ENERGY_PER_EFFORT * executed
        self.battery[active_keys] = np.maximum(self.battery[active_keys], 0.0)
        charging_keys = np.flatnonzero(self.charging)
        self.battery[charging_keys] = np.minimum(
            1.0, self.battery[charging_keys] + INACTIVE_CHARGE_PER_STEP
        )
        self.previous_effort[active_keys] = executed.astype(np.float32)
        self.age[active_keys] += 1
        self.reward_trace.append(float(utility))
        self.served_trace.append(served)
        self.roster_sizes.append(int(active_keys.size))
        self.time += 1
        self._prepared_time = None
        self._membership_change = MembershipChange()
        self._terminated = self.time == HORIZON
        return float(utility), self._terminated, {
            "served": served,
            "demand": view.demand,
            "service_utility": float(utility),
        }

    def outcome(self) -> BatteryRosterOutcome:
        if not self._terminated or len(self.reward_trace) != HORIZON:
            raise RuntimeError("G18 outcome requires a complete episode")
        rewards = np.asarray(self.reward_trace, dtype=np.float64)
        spike_rewards = rewards[TEMPORARY_LEAVE_TIME:RETURN_TIME]
        return BatteryRosterOutcome(
            utility=float(rewards.mean()),
            minimum_step_utility=float(rewards.min()),
            future_service_deficit=float(np.sum(1.0 - spike_rewards)),
            reward_trace=tuple(float(value) for value in rewards),
            served_trace=tuple(self.served_trace),
            roster_sizes=tuple(self.roster_sizes),
        )


def _actions_from_effort(view: BatteryRosterView, effort: np.ndarray) -> np.ndarray:
    values = np.zeros((CAPACITY, ACTION_DIM), dtype=np.float32)
    values[view.active_mask, 0] = np.float32(-1.0)
    active_effort = np.asarray(effort, dtype=np.float32)
    values[view.active_mask, 0] = 2.0 * active_effort[view.active_mask] - 1.0
    return values


def _greedy_effort(
    view: BatteryRosterView, priority: Sequence[int]
) -> np.ndarray:
    effort = np.zeros(CAPACITY, dtype=np.float32)
    remaining = float(view.demand)
    for key in priority:
        if remaining <= 0.0 or not view.active_mask[key]:
            continue
        available = min(1.0, float(view.battery[key] / ENERGY_PER_EFFORT))
        assigned = min(remaining, available)
        effort[key] = np.float32(assigned)
        remaining -= assigned
    return effort


def constructive_actions(view: BatteryRosterView) -> np.ndarray:
    ledger_order = tuple(range(CAPACITY))
    rotating = tuple(int(key) for key in np.flatnonzero(view.rotating_mask))
    if view.time < TEMPORARY_LEAVE_TIME:
        priority = rotating + tuple(key for key in ledger_order if key not in rotating)
    elif view.time < RETURN_TIME:
        priority = tuple(key for key in ledger_order if key not in rotating) + rotating
    else:
        priority = rotating + tuple(key for key in ledger_order if key not in rotating)
    return _actions_from_effort(view, _greedy_effort(view, priority))


def counterfactual_first_action(view: BatteryRosterView) -> np.ndarray:
    if view.time != 0:
        raise ValueError("G18 counterfactual is defined only for the first action")
    non_rotating = tuple(
        int(key)
        for key in np.flatnonzero(view.active_mask & ~view.rotating_mask)
    )
    rotating = tuple(int(key) for key in np.flatnonzero(view.rotating_mask))
    priority = non_rotating + rotating
    return _actions_from_effort(view, _greedy_effort(view, priority))


def myopic_equal_actions(view: BatteryRosterView) -> np.ndarray:
    active_count = int(view.active_mask.sum())
    effort = np.zeros(CAPACITY, dtype=np.float32)
    effort[view.active_mask] = np.float32(
        min(1.0, view.demand / max(active_count, 1))
    )
    return _actions_from_effort(view, effort)


def run_controller(
    ledger: BatteryRosterLedger,
    controller: Callable[[BatteryRosterView], np.ndarray],
) -> BatteryRosterOutcome:
    environment = BatteryRosterEnv(ledger)
    for _ in range(HORIZON):
        view = environment.observe()
        environment.step(controller(view))
    return environment.outcome()


def run_information_gate() -> dict[str, object]:
    constructive_outcomes = []
    myopic_outcomes = []
    for slot_order in GATE_SLOT_ORDERS:
        ledger = make_ledger(slot_order)
        constructive_outcomes.append(run_controller(ledger, constructive_actions))
        myopic_outcomes.append(run_controller(ledger, myopic_equal_actions))

    ledger = make_ledger(GATE_SLOT_ORDERS[0])
    natural = BatteryRosterEnv(ledger)
    intervened = BatteryRosterEnv(ledger)
    natural_reward, _, natural_info = natural.step(
        constructive_actions(natural.observe())
    )
    intervention_reward, _, intervention_info = intervened.step(
        counterfactual_first_action(intervened.observe())
    )
    next_persistent_delta = float(
        natural.battery[ledger.persistent_keys[0]]
        - intervened.battery[ledger.persistent_keys[0]]
    )
    for _ in range(1, HORIZON):
        natural.step(constructive_actions(natural.observe()))
        intervened.step(constructive_actions(intervened.observe()))
    natural_outcome = natural.outcome()
    intervention_outcome = intervened.outcome()

    constructive_utilities = [row.utility for row in constructive_outcomes]
    myopic_utilities = [row.utility for row in myopic_outcomes]
    gaps = [
        constructive.utility - myopic.utility
        for constructive, myopic in zip(constructive_outcomes, myopic_outcomes)
    ]
    slot_invariant = (
        len(set(constructive_utilities)) == 1
        and len(set(myopic_utilities)) == 1
    )
    immediate_equal = (
        natural_reward == intervention_reward
        and natural_info["served"] == intervention_info["served"]
    )
    sequence_bearing = (
        next_persistent_delta > 0.0
        and natural_outcome.utility > intervention_outcome.utility
    )
    passed = (
        min(constructive_utilities) == 1.0
        and max(myopic_utilities) < 0.90
        and min(gaps) > 0.10
        and slot_invariant
        and immediate_equal
        and sequence_bearing
    )
    return {
        "branch": PASS_BRANCH if passed else FAIL_BRANCH,
        "constructive_utilities": constructive_utilities,
        "myopic_utilities": myopic_utilities,
        "constructive_minimum_utility": min(constructive_utilities),
        "myopic_maximum_utility": max(myopic_utilities),
        "minimum_constructive_minus_myopic": min(gaps),
        "slot_permutation_invariant": slot_invariant,
        "roster_sizes": list(constructive_outcomes[0].roster_sizes),
        "immediate_service_equal": immediate_equal,
        "next_persistent_battery_delta": next_persistent_delta,
        "natural_utility": natural_outcome.utility,
        "intervened_utility": intervention_outcome.utility,
        "intervened_future_service_deficit": (
            intervention_outcome.future_service_deficit
        ),
        "formal": False,
        "iteration_consumed": False,
    }
