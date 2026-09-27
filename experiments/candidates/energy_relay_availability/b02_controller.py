"""B02 legal-observation H1 clock and availability response rules."""

from __future__ import annotations

import time

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy

from .configuration import AvailableH1Controller, AvailableLayoutHeuristic


ARMS = ("clock30", "availability_event")


class TimedAvailableHeuristic(AvailableLayoutHeuristic):
    def __init__(self, params):
        super().__init__(params)
        self.extra_replan = False
        self.last_plan_wall_seconds = 0.0
        self.last_plan_cpu_seconds = 0.0

    def replans_next(self) -> bool:
        return self.extra_replan or super().replans_next()

    def plan(self, observations, modes, plan_inputs=None):
        wall = time.perf_counter()
        cpu = time.process_time()
        try:
            return super().plan(observations, modes, plan_inputs)
        finally:
            self.last_plan_wall_seconds = time.perf_counter() - wall
            self.last_plan_cpu_seconds = time.process_time() - cpu


class B02Controller(AvailableH1Controller):
    """Observe availability at each decision; leave the 30-step clock untouched."""

    def __init__(self, arm: str):
        if arm not in ARMS:
            raise ValueError(f"B02 arm must be one of {ARMS}")
        super().__init__("local")
        self.arm = arm
        self.heuristic = TimedAvailableHeuristic(self.heuristic.params)
        self.reset()

    def reset(self) -> None:
        super().reset()
        self._previous_available = None
        self._plan_count = 0
        self.decision_rows: list[dict] = []

    def propose(self, observations, state, step, previous_done, modes):
        available = own_energy(observations)["available"].copy()
        if available.shape != (8,):
            raise ValueError("B02 legal availability shape changed")
        if step != len(self.decision_rows):
            raise ValueError("B02 decision clock skipped or repeated")
        changed = (self._previous_available is not None
                   and not np.array_equal(available, self._previous_available))
        regular = self.heuristic.calls % self.heuristic.params.replan_period == 0
        event_trigger = self.arm == "availability_event" and changed
        extra = bool(event_trigger and not regular)
        before = self.heuristic.calls
        self.heuristic.extra_replan = extra
        try:
            actions = super().propose(observations, state, step, previous_done, modes)
        finally:
            self.heuristic.extra_replan = False
        executed = regular or extra
        if self.heuristic.calls != before + 1:
            raise RuntimeError("H1 call count changed unexpectedly")
        if executed != (self.heuristic.last_plan["call"] == before if
                        self.heuristic.last_plan is not None else False):
            raise RuntimeError("H1 planning cadence changed unexpectedly")
        self._plan_count += int(executed)
        self.decision_rows.append({
            "step": int(step), "available": available,
            "availability_changed": bool(changed),
            "regular_replan": bool(regular), "event_trigger": bool(event_trigger),
            "extra_replan": bool(extra), "executed_replan": bool(executed),
            "coincident_trigger": bool(event_trigger and regular),
            "plan_call_count": self._plan_count,
            "plan_wall_seconds": self.heuristic.last_plan_wall_seconds if executed else 0.0,
            "plan_cpu_seconds": self.heuristic.last_plan_cpu_seconds if executed else 0.0,
        })
        self._previous_available = available
        return actions

    def as_arrays(self) -> dict[str, np.ndarray]:
        return {key: np.asarray([row[key] for row in self.decision_rows])
                for key in self.decision_rows[0]} if self.decision_rows else {}


def response_lags(decisions: dict[str, np.ndarray], terminal_available: np.ndarray) -> dict:
    """Lag in decision indices to first executed plan; terminal changes are censored."""
    available = np.asarray(decisions["available"], dtype=bool)
    executed = np.asarray(decisions["executed_replan"], dtype=bool)
    changed = np.asarray(decisions["availability_changed"], dtype=bool)
    length = len(available)
    if available.shape != (length, 8) or executed.shape != (length,) or changed.shape != (length,):
        raise ValueError("B02 decision trace shape disagreement")
    if changed[0] or not executed[0]:
        raise ValueError("reset must have one regular plan and no change trigger")
    if not np.array_equal(changed[1:], np.any(available[1:] != available[:-1], axis=1)):
        raise ValueError("availability change flags disagree with legal trace")
    events = []
    for step in np.flatnonzero(changed):
        later = np.flatnonzero(executed[step:])
        events.append({"decision": int(step), "lag": int(later[0]) if later.size else None,
                       "right_censored": not bool(later.size),
                       "observed_decisions": int(length - step),
                       "terminal_observation_only": False})
    terminal_available = np.asarray(terminal_available, dtype=bool)
    if terminal_available.shape != (8,):
        raise ValueError("terminal availability shape changed")
    if np.any(terminal_available != available[-1]):
        events.append({"decision": length, "lag": None, "right_censored": True,
                       "observed_decisions": 0, "terminal_observation_only": True})
    complete = [item["lag"] for item in events if item["lag"] is not None]
    return {"changes": len(events), "complete_lags": len(complete),
            "censored_lags": len(events) - len(complete),
            "terminal_changes": sum(item["terminal_observation_only"] for item in events),
            "world_mean_lag": float(np.mean(complete)) if complete else None,
            "rows": events}
