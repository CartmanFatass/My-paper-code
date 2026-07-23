"""Frozen controllers and natural collection for the bounded EHC G1 prototype."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
from random import Random
from typing import Any, Final

from ha_ctse_process.temporal_duty_g1 import (
    G1EpisodeSpec,
    TemporalDutyG1Env,
    make_episode_spec,
)


CONTROLLERS: Final[tuple[str, ...]] = (
    "MECHANISM_CONTROL",
    "RANDOM_USE",
    "EXOGENOUS_LIFETIME",
    "LOGIT_WITHOUT_BEHAVIOR",
    "RECURRENT_CONTROL",
    "DUM_CONTROL",
)

_ACTION_ORDER: Final[tuple[int, int, int]] = (-1, 0, 1)
_SEED_NAMESPACES: Final[tuple[str, str, str]] = ("event", "mark", "action")
_ZERO_LOGITS: Final[tuple[float, float, float]] = (0.0, 0.0, 0.0)
_MAX_BRANCH_SNAPSHOTS: Final[int] = 2
_MAX_DOWNSTREAM_WINDOW: Final[int] = 6
_MEASUREMENT_FAMILIES: Final[tuple[str, ...]] = (
    "policy_dependence",
    "instantaneous_tv",
    "sequence_hamming",
    "terminal_utility_delta",
    "natural_mediation",
    "heldout_robustness",
)


def primitive_logits(
    base_logits: tuple[float, float, float], treatment: int, mark: int
) -> tuple[float, float, float]:
    """Apply the frozen ``base_logits + W_z(m*z)`` primitive-logit path."""

    if not isinstance(base_logits, tuple) or len(base_logits) != 3:
        raise ValueError("base_logits must be a length-three tuple")
    normalized_base = tuple(float(value) for value in base_logits)
    if not all(math.isfinite(value) for value in normalized_base):
        raise ValueError("base_logits must be finite")
    if type(treatment) is not int or treatment not in (0, 1):
        raise ValueError("treatment must be 0 or 1")
    if type(mark) is not int or mark not in (-1, 0, 1):
        raise ValueError("mark must be -1, 0, or +1")

    signal = treatment * mark
    return (
        normalized_base[0] - 4.0 * signal,
        normalized_base[1],
        normalized_base[2] + 4.0 * signal,
    )


class _OwnedRng:
    """A source-owned RNG with explicit draw accounting."""

    def __init__(self, seed: int):
        self._random = Random(seed)
        self.draws = 0

    def bernoulli_half(self) -> bool:
        self.draws += 1
        return self._random.random() < 0.5

    def sign(self) -> int:
        self.draws += 1
        return -1 if self._random.random() < 0.5 else 1

    def snapshot_state(self) -> dict[str, object]:
        return {"state": deepcopy(self._random.getstate()), "draws": self.draws}

    @classmethod
    def from_snapshot_state(cls, state: dict[str, object]) -> "_OwnedRng":
        if not isinstance(state, dict) or set(state) != {"state", "draws"}:
            raise ValueError("RNG snapshot has an invalid schema")
        draws = state["draws"]
        if type(draws) is not int or draws < 0:
            raise ValueError("RNG draw count must be a nonnegative integer")
        rng = cls.__new__(cls)
        rng._random = Random()
        rng._random.setstate(_tuple_tree(state["state"]))
        rng.draws = draws
        return rng


@dataclass
class _LifecycleControllerState:
    mark: int = 0
    recurrent_sign: int = 0
    opportunities: int = 0


def _probabilities(logits: tuple[float, float, float]) -> tuple[float, float, float]:
    maximum = max(logits)
    exponentials = tuple(math.exp(value - maximum) for value in logits)
    denominator = sum(exponentials)
    return tuple(value / denominator for value in exponentials)


def _greedy_action(logits: tuple[float, float, float]) -> int:
    index = max(range(len(_ACTION_ORDER)), key=logits.__getitem__)
    return _ACTION_ORDER[index]


class _NaturalController:
    def __init__(self, controller: str, seeds: dict[str, int]):
        self.controller = controller
        self.event_rng = _OwnedRng(seeds["event"])
        self.mark_rng = _OwnedRng(seeds["mark"])
        self.action_rng = _OwnedRng(seeds["action"])
        self.states: dict[int, _LifecycleControllerState] = {}

    def act(
        self, slot: int, observation: tuple[float, float, float, float, float, float]
    ) -> dict[str, object]:
        state = self.states.get(slot)
        if state is None:
            state = _LifecycleControllerState()
            if self.controller == "RANDOM_USE":
                state.mark = self.mark_rng.sign()
            self.states[slot] = state
        opportunity = state.opportunities
        cue = int(observation[0])
        cue_present = observation[1] == 1.0
        new_segment = observation[2] == 1.0
        base_logits = _ZERO_LOGITS
        event = "KEEP"
        treatment = 0

        if self.controller in ("MECHANISM_CONTROL", "DUM_CONTROL"):
            if new_segment:
                event = "RENEW"
                state.mark = cue
            treatment = int(self.controller == "MECHANISM_CONTROL")
        elif self.controller == "RANDOM_USE":
            if self.event_rng.bernoulli_half():
                event = "RENEW"
                state.mark = self.mark_rng.sign()
            treatment = 1
        elif self.controller == "EXOGENOUS_LIFETIME":
            if opportunity % 4 == 0:
                event = "RENEW"
                state.mark = cue if cue_present else self.mark_rng.sign()
            treatment = 1
        elif self.controller == "LOGIT_WITHOUT_BEHAVIOR":
            if new_segment:
                event = "RENEW"
                state.mark = cue
                treatment = 1
        elif self.controller == "RECURRENT_CONTROL":
            event = "NONE"
            state.mark = 0
            if cue_present:
                state.recurrent_sign = cue
            recurrent_signal = state.recurrent_sign
            base_logits = (
                -4.0 * recurrent_signal,
                0.0,
                4.0 * recurrent_signal,
            )
        else:  # pragma: no cover - public validation prevents this path
            raise RuntimeError(f"unknown controller {self.controller!r}")

        logits = primitive_logits(base_logits, treatment, state.mark)
        action = _greedy_action(logits)
        state.opportunities += 1
        return {
            "controller_opportunity": opportunity,
            "event": event,
            "mark": state.mark,
            "treatment": treatment,
            "base_logits": base_logits,
            "primitive_logits": logits,
            "probabilities": _probabilities(logits),
            "action": action,
            "action_rng_draws": self.action_rng.draws,
        }

    def draw_counts(self) -> dict[str, int]:
        return {
            "event": self.event_rng.draws,
            "mark": self.mark_rng.draws,
            "action": self.action_rng.draws,
        }

    def snapshot_state(self) -> dict[str, object]:
        return deepcopy(
            {
                "version": 1,
                "controller": self.controller,
                "states": self.serializable_state(),
                "rng": {
                    "event": self.event_rng.snapshot_state(),
                    "mark": self.mark_rng.snapshot_state(),
                    "action": self.action_rng.snapshot_state(),
                },
            }
        )

    @classmethod
    def from_snapshot_state(cls, state: dict[str, object]) -> "_NaturalController":
        if not isinstance(state, dict) or state.get("version") != 1:
            raise ValueError("controller state is not a version-1 snapshot")
        controller = state.get("controller")
        if controller not in CONTROLLERS:
            raise ValueError("controller snapshot has an unknown controller")
        serialized_states = state.get("states")
        rng_states = state.get("rng")
        if not isinstance(serialized_states, dict) or not isinstance(rng_states, dict):
            raise ValueError("controller snapshot state or RNG payload is invalid")
        if set(rng_states) != set(_SEED_NAMESPACES):
            raise ValueError("controller snapshot RNG namespaces are invalid")

        restored = cls.__new__(cls)
        restored.controller = str(controller)
        restored.event_rng = _OwnedRng.from_snapshot_state(rng_states["event"])
        restored.mark_rng = _OwnedRng.from_snapshot_state(rng_states["mark"])
        restored.action_rng = _OwnedRng.from_snapshot_state(rng_states["action"])
        restored.states = {}
        for raw_slot, raw_lifecycle in serialized_states.items():
            slot = int(raw_slot)
            if not isinstance(raw_lifecycle, dict):
                raise ValueError("controller lifecycle snapshot must be a dict")
            values = {
                name: raw_lifecycle.get(name)
                for name in ("mark", "recurrent_sign", "opportunities")
            }
            if any(type(value) is not int for value in values.values()):
                raise ValueError("controller lifecycle fields must be integers")
            restored.states[slot] = _LifecycleControllerState(**values)
        return restored

    def forced_decision(
        self,
        slot: int,
        observation: tuple[float, float, float, float, float, float],
        *,
        event: str,
        candidate_mark: int,
    ) -> dict[str, object]:
        """Apply one deterministic intervention without consuming owned RNG."""

        if event not in ("KEEP", "RENEW") or candidate_mark not in (-1, 1):
            raise ValueError("forced event and candidate mark are outside support")
        state = self.states.get(slot)
        if state is None:
            raise ValueError("forced target has no controller lifecycle state")
        opportunity = state.opportunities
        cue = int(observation[0])
        cue_present = observation[1] == 1.0
        base_logits = _ZERO_LOGITS

        if self.controller == "RECURRENT_CONTROL":
            if cue_present:
                state.recurrent_sign = cue
            recurrent_signal = state.recurrent_sign
            base_logits = (
                -4.0 * recurrent_signal,
                0.0,
                4.0 * recurrent_signal,
            )
            state.mark = 0
            controller_event = "NONE"
            treatment = 0
        else:
            state.mark = candidate_mark
            controller_event = event
            if self.controller == "DUM_CONTROL":
                treatment = 0
            elif self.controller == "LOGIT_WITHOUT_BEHAVIOR":
                treatment = int(event == "RENEW")
            else:
                treatment = 1

        logits = primitive_logits(base_logits, treatment, state.mark)
        action = _greedy_action(logits)
        state.opportunities += 1
        return {
            "controller_opportunity": opportunity,
            "event": controller_event,
            "mark": state.mark,
            "treatment": treatment,
            "base_logits": base_logits,
            "primitive_logits": logits,
            "probabilities": _probabilities(logits),
            "action": action,
            "action_rng_draws": self.action_rng.draws,
        }

    def serializable_state(self) -> dict[int, dict[str, int]]:
        return {
            slot: {
                "mark": state.mark,
                "recurrent_sign": state.recurrent_sign,
                "opportunities": state.opportunities,
            }
            for slot, state in sorted(self.states.items())
        }


def _validate_seeds(seeds: dict[str, int]) -> dict[str, int]:
    if not isinstance(seeds, dict):
        raise TypeError("seeds must be a dict")
    missing = [namespace for namespace in _SEED_NAMESPACES if namespace not in seeds]
    if missing:
        raise ValueError(f"seeds is missing namespaces {missing}")
    copied = dict(seeds)
    for namespace, seed in copied.items():
        if type(namespace) is not str or type(seed) is not int:
            raise ValueError("seed namespaces must be strings with integer values")
    return copied


def _tuple_tree(value: object) -> object:
    """Restore tuple structure after an optional JSON list round-trip."""

    if isinstance(value, (tuple, list)):
        return tuple(_tuple_tree(item) for item in value)
    return value


def _normalized_environment_state(state: object) -> dict[str, object]:
    """Normalize only JSON's tuple/key conversions, then recheck canonical state."""

    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValueError("environment state is not a version-1 snapshot")
    copied = deepcopy(state)
    raw_spec = copied.get("spec")
    if not isinstance(raw_spec, dict):
        raise ValueError("environment snapshot spec must be a dict")
    canonical_spec = asdict(
        make_episode_spec(
            str(raw_spec.get("split")),
            int(raw_spec.get("roster_size")),
            int(raw_spec.get("duration")),
            int(raw_spec.get("sign_start")),
            int(raw_spec.get("rotation")),
        )
    )
    normalized_spec = deepcopy(raw_spec)
    if isinstance(normalized_spec.get("logical_to_physical"), list):
        normalized_spec["logical_to_physical"] = tuple(
            normalized_spec["logical_to_physical"]
        )
    if isinstance(normalized_spec.get("membership_events"), list):
        normalized_spec["membership_events"] = tuple(
            tuple(event) for event in normalized_spec["membership_events"]
        )
    if normalized_spec != canonical_spec:
        raise ValueError("environment snapshot spec is not canonical")
    copied["spec"] = canonical_spec

    raw_lifecycles = copied.get("lifecycles")
    if not isinstance(raw_lifecycles, dict):
        raise ValueError("environment snapshot lifecycles must be a dict")
    copied["lifecycles"] = {
        int(slot): lifecycle for slot, lifecycle in raw_lifecycles.items()
    }
    if isinstance(copied.get("step_rewards"), list):
        copied["step_rewards"] = tuple(copied["step_rewards"])
    return copied


def _remaining_active_opportunities(
    environment_state: dict[str, object], slot: int
) -> int:
    spec = environment_state["spec"]
    lifecycles = environment_state["lifecycles"]
    if not isinstance(spec, dict) or not isinstance(lifecycles, dict):
        raise ValueError("environment snapshot is malformed")
    lifecycle = lifecycles[slot]
    active = bool(lifecycle["active"])
    terminal = bool(lifecycle["terminal"])
    current_time = int(environment_state["time"])
    events_by_time: dict[int, list[str]] = {}
    for raw_time, event, target in spec["membership_events"]:
        if int(target) == slot:
            events_by_time.setdefault(int(raw_time), []).append(str(event))

    remaining = 0
    for time in range(current_time + 1, int(spec["horizon"])):
        for event in events_by_time.get(time, ()):
            if event in ("TEMP_LEAVE", "TERMINAL_LEAVE"):
                active = False
                terminal = terminal or event == "TERMINAL_LEAVE"
            elif event == "REJOIN":
                active = not terminal
            elif event == "JOIN":
                active = True
                terminal = False
        if active:
            remaining += 1
    return remaining


def _eligible_snapshots(
    environment: TemporalDutyG1Env,
    controller: _NaturalController,
    already_selected: set[int],
) -> list[dict[str, object]]:
    environment_state = environment.snapshot_state()
    time = int(environment_state["time"])
    spec = environment_state["spec"]
    lifecycles = environment_state["lifecycles"]
    terminal_event_same_step = any(
        int(event_time) == time and event == "TERMINAL_LEAVE"
        for event_time, event, _target in spec["membership_events"]
    )
    if terminal_event_same_step:
        return []

    candidates: list[dict[str, object]] = []
    for slot in sorted(lifecycles):
        lifecycle = lifecycles[slot]
        if slot in already_selected or not lifecycle["active"] or lifecycle["terminal"]:
            continue
        if int(lifecycle["age"]) != 3:
            continue
        remaining = _remaining_active_opportunities(environment_state, int(slot))
        if remaining < 2:
            continue
        controller_lifecycle = controller.states.get(int(slot))
        if controller_lifecycle is None:
            continue
        current_mark = controller_lifecycle.mark
        if current_mark == 0:
            current_mark = controller_lifecycle.recurrent_sign
        if current_mark not in (-1, 1):
            continue
        candidates.append(
            deepcopy(
                {
                    "version": 1,
                    "controller": controller.controller,
                    "target_slot": int(slot),
                    "selection": {
                        "time": time,
                        "age": 3,
                        "cue_present": False,
                        "remaining_active_opportunities": remaining,
                        "terminal_event_same_step": False,
                        "current_mark": current_mark,
                    },
                    "environment_state": environment_state,
                    "controller_state": controller.snapshot_state(),
                }
            )
        )
    return candidates


def collect_natural_episode(
    spec: G1EpisodeSpec, controller: str, seeds: dict[str, int]
) -> dict[str, object]:
    """Collect one complete, unforced natural episode for a frozen controller."""

    if controller not in CONTROLLERS:
        raise ValueError(f"controller must be one of {CONTROLLERS}, got {controller!r}")
    copied_seeds = _validate_seeds(seeds)
    environment = TemporalDutyG1Env(spec)
    natural_controller = _NaturalController(controller, copied_seeds)
    rows: list[dict[str, object]] = []
    branch_snapshots: list[dict[str, object]] = []
    selected_slots: set[int] = set()

    observations = environment.observe()
    for time in range(spec.horizon):
        if len(branch_snapshots) < _MAX_BRANCH_SNAPSHOTS:
            for snapshot in _eligible_snapshots(
                environment, natural_controller, selected_slots
            ):
                branch_snapshots.append(snapshot)
                selected_slots.add(int(snapshot["target_slot"]))
                if len(branch_snapshots) == _MAX_BRANCH_SNAPSHOTS:
                    break
        actions: dict[int, int] = {}
        step_rows: list[dict[str, object]] = []
        environment_state = environment.snapshot_state()
        for slot in sorted(observations):
            actor_observation = observations[slot].actor
            decision = natural_controller.act(slot, actor_observation)
            actions[slot] = int(decision["action"])
            step_rows.append(
                {
                    "provenance": "natural",
                    "forced": False,
                    "controller": controller,
                    "time": time,
                    "slot": slot,
                    "observation": actor_observation,
                    "evaluation_correct": (
                        int(decision["action"])
                        == int(environment_state["lifecycles"][slot]["g"])
                    ),
                    **decision,
                }
            )
        transition = environment.step(actions)
        rows.extend(step_rows)
        observations = transition["observations"]

    return {
        "controller": controller,
        "spec": asdict(spec),
        "seeds": copied_seeds,
        "rows": rows,
        "branch_snapshots": branch_snapshots,
        "outcome": environment.outcome(),
        "controller_state": natural_controller.serializable_state(),
        "rng_draws": natural_controller.draw_counts(),
        "final_environment_state": environment.snapshot_state(),
    }


def _validate_branch_snapshot(
    snapshot: dict[str, object], controller: str, window: int
) -> tuple[TemporalDutyG1Env, _NaturalController, int, int]:
    if controller not in CONTROLLERS:
        raise ValueError(f"controller must be one of {CONTROLLERS}, got {controller!r}")
    if type(window) is not int or not 1 <= window <= _MAX_DOWNSTREAM_WINDOW:
        raise ValueError(f"window must be an integer from 1 to {_MAX_DOWNSTREAM_WINDOW}")
    if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
        raise ValueError("snapshot is not a version-1 intervention snapshot")
    if snapshot.get("controller") != controller:
        raise ValueError("snapshot controller does not match requested controller")
    selection = snapshot.get("selection")
    if not isinstance(selection, dict):
        raise ValueError("snapshot selection provenance is missing")
    required_selection = {
        "time",
        "age",
        "cue_present",
        "remaining_active_opportunities",
        "terminal_event_same_step",
        "current_mark",
    }
    if not required_selection.issubset(selection):
        raise ValueError("snapshot selection provenance is incomplete")
    if (
        selection["age"] != 3
        or selection["cue_present"] is not False
        or selection["terminal_event_same_step"] is not False
        or int(selection["remaining_active_opportunities"]) < 2
    ):
        raise ValueError("snapshot is not an eligible age-three branch point")
    current_mark = selection["current_mark"]
    if type(current_mark) is not int or current_mark not in (-1, 1):
        raise ValueError("snapshot current mark must be -1 or +1")
    target_slot = snapshot.get("target_slot")
    if type(target_slot) is not int:
        raise ValueError("snapshot target slot must be an integer")

    environment_state = _normalized_environment_state(
        snapshot.get("environment_state")
    )
    controller_state = snapshot.get("controller_state")
    environment = TemporalDutyG1Env.from_snapshot_state(environment_state)
    natural_controller = _NaturalController.from_snapshot_state(controller_state)
    if int(environment.snapshot_state()["time"]) != int(selection["time"]):
        raise ValueError("snapshot time and selection provenance differ")
    observations = environment.observe()
    if target_slot not in observations:
        raise ValueError("snapshot target is not active")
    lifecycle = environment.snapshot_state()["lifecycles"][target_slot]
    if int(lifecycle["age"]) != 3 or observations[target_slot].actor[1] != 0.0:
        raise ValueError("snapshot target is not at the registered state")
    return environment, natural_controller, target_slot, int(current_mark)


def _run_branch(
    snapshot: dict[str, object],
    controller_name: str,
    *,
    event: str,
    mark: int,
    window: int,
) -> tuple[dict[str, object], dict[str, object]]:
    environment, controller, target_slot, _current_mark = _validate_branch_snapshot(
        snapshot, controller_name, window
    )
    origin = {
        "environment_state": environment.snapshot_state(),
        "controller_state": controller.snapshot_state(),
    }
    intervention_time = int(origin["environment_state"]["time"])
    downstream_actions: list[int] = []
    downstream_correct: list[bool] = []
    downstream_times: list[int] = []
    intervention_decision: dict[str, object] | None = None
    first_step = True

    loop_state = environment.snapshot_state()
    while int(loop_state["time"]) < int(loop_state["spec"]["horizon"]):
        observations = environment.observe()
        time = int(loop_state["time"])
        lifecycle_state = loop_state["lifecycles"]
        actions: dict[int, int] = {}
        target_decision: dict[str, object] | None = None
        target_correct: bool | None = None
        for slot in sorted(observations):
            actor_observation = observations[slot].actor
            if first_step and slot == target_slot:
                decision = controller.forced_decision(
                    slot, actor_observation, event=event, candidate_mark=mark
                )
                intervention_decision = decision
            else:
                decision = controller.act(slot, actor_observation)
            actions[slot] = int(decision["action"])
            if slot == target_slot:
                target_decision = decision
                target_correct = int(decision["action"]) == int(
                    lifecycle_state[slot]["g"]
                )
        environment.step(actions)
        if (
            not first_step
            and target_decision is not None
            and len(downstream_actions) < window
        ):
            downstream_actions.append(int(target_decision["action"]))
            downstream_correct.append(bool(target_correct))
            downstream_times.append(time)
        first_step = False
        loop_state = environment.snapshot_state()

    if intervention_decision is None:
        raise RuntimeError("intervention target was not acted at the branch point")
    terminal_state = loop_state
    branch = {
        "intervention_event": event,
        "intervention_mark": mark,
        "intervention_time": intervention_time,
        "intervention_action": int(intervention_decision["action"]),
        "intervention_probabilities": intervention_decision["probabilities"],
        "downstream_actions": tuple(downstream_actions),
        "downstream_correct": tuple(downstream_correct),
        "downstream_times": tuple(downstream_times),
        "terminal_time": int(terminal_state["time"]),
        "terminal_outcome": environment.outcome(),
        "final_rng_draws": controller.draw_counts(),
    }
    final_rng_state = controller.snapshot_state()["rng"]
    return branch, {"origin": origin, "final_rng_state": final_rng_state}


def _paired_metrics(
    left: dict[str, object], right: dict[str, object]
) -> dict[str, float]:
    left_actions = tuple(left["downstream_actions"])
    right_actions = tuple(right["downstream_actions"])
    left_correct = tuple(left["downstream_correct"])
    right_correct = tuple(right["downstream_correct"])
    if len(left_actions) != len(right_actions) or len(left_correct) != len(right_correct):
        raise RuntimeError("paired downstream windows do not have equal support")
    support = len(left_actions)
    hamming = (
        sum(a != b for a, b in zip(left_actions, right_actions, strict=True)) / support
        if support
        else 0.0
    )
    correctness_difference = (
        (
            sum(left_correct) / len(left_correct)
            - sum(right_correct) / len(right_correct)
        )
        if left_correct
        else 0.0
    )
    terminal_delta = float(left["terminal_outcome"]["utility"]) - float(
        right["terminal_outcome"]["utility"]
    )
    left_probabilities = left["intervention_probabilities"]
    right_probabilities = right["intervention_probabilities"]
    instantaneous_tv = 0.5 * sum(
        abs(float(a) - float(b))
        for a, b in zip(left_probabilities, right_probabilities, strict=True)
    )
    return {
        "instantaneous_tv": float(instantaneous_tv),
        "sequence_hamming": float(hamming),
        "sequence_correctness_difference": float(correctness_difference),
        "terminal_utility_delta": float(terminal_delta),
    }


def _run_intervention(
    snapshot: dict[str, object], controller: str, *, kind: str, window: int
) -> dict[str, object]:
    _environment, _controller, target_slot, current_mark = _validate_branch_snapshot(
        snapshot, controller, window
    )
    if kind == "event":
        left_event, right_event = "KEEP", "RENEW"
        contrast = {
            "left": {"event": "KEEP", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
    elif kind == "mark":
        left_event = right_event = "RENEW"
        contrast = {
            "left": {"event": "RENEW", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
    else:  # pragma: no cover - private caller freezes the two kinds
        raise RuntimeError("unknown intervention kind")

    left, left_audit = _run_branch(
        snapshot,
        controller,
        event=left_event,
        mark=current_mark,
        window=window,
    )
    right, right_audit = _run_branch(
        snapshot,
        controller,
        event=right_event,
        mark=-current_mark,
        window=window,
    )
    origin_equal = left_audit["origin"] == right_audit["origin"]
    rng_equal = left_audit["final_rng_state"] == right_audit["final_rng_state"]
    if not origin_equal or not rng_equal:
        raise RuntimeError("paired branch origin or common future RNG diverged")
    return {
        "kind": kind,
        "controller": controller,
        "snapshot_provenance": deepcopy(snapshot["selection"]),
        "target_slot": target_slot,
        "contrast": contrast,
        "branch_origin_equal": True,
        "common_random_numbers": {
            "equal": True,
            "left_draws": deepcopy(left["final_rng_draws"]),
            "right_draws": deepcopy(right["final_rng_draws"]),
        },
        "branches": {"left": left, "right": right},
        "metrics": _paired_metrics(left, right),
    }


def run_event_intervention(
    snapshot: dict[str, object], controller: str, window: int = 6
) -> dict[str, object]:
    """Run KEEP/current versus RENEW/opposite from independent restores."""

    return _run_intervention(snapshot, controller, kind="event", window=window)


def run_mark_intervention(
    snapshot: dict[str, object], controller: str, window: int = 6
) -> dict[str, object]:
    """Run current versus opposite mark while holding RENEW fixed."""

    return _run_intervention(snapshot, controller, kind="mark", window=window)


def _mean(values: list[float], label: str) -> float:
    if not values:
        raise ValueError(f"{label} has no observations")
    result = sum(values) / len(values)
    if not math.isfinite(result):
        raise ValueError(f"{label} is not finite")
    return float(result)


def _commitment_lifetimes(rows: list[dict[str, object]]) -> list[int]:
    support: list[int] = []
    by_slot: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        by_slot.setdefault(int(row["slot"]), []).append(row)
    for slot_rows in by_slot.values():
        run_length = 0
        for row in sorted(slot_rows, key=lambda item: int(item["time"])):
            if row["event"] == "RENEW" and run_length:
                support.append(run_length)
                run_length = 0
            run_length += 1
        if run_length:
            support.append(run_length)
    return support


def _expected_cells() -> set[tuple[str, str, int, int, int, int]]:
    cells: set[tuple[str, str, int, int, int, int]] = set()
    for controller in CONTROLLERS:
        for split, durations in (("fitting", (6, 14)), ("heldout", (10, 18))):
            for roster_size in (2, 3):
                for duration in durations:
                    for sign_start in (-1, 1):
                        for rotation in (0, 1):
                            cells.add(
                                (
                                    controller,
                                    split,
                                    roster_size,
                                    duration,
                                    sign_start,
                                    rotation,
                                )
                            )
    return cells


def analyze_prototype(records: list[dict[str, object]]) -> dict[str, object]:
    """Return only the complete registered G1 measurement tuple and provenance."""

    if not isinstance(records, list):
        raise TypeError("records must be a list")
    observed_cells: set[tuple[str, str, int, int, int, int]] = set()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("every prototype record must be a dict")
        controller = record.get("controller")
        spec = record.get("spec")
        if controller not in CONTROLLERS or not isinstance(spec, dict):
            raise ValueError("record controller or cell manifest is invalid")
        cell = (
            str(controller),
            str(spec.get("split")),
            int(spec.get("roster_size")),
            int(spec.get("duration")),
            int(spec.get("sign_start")),
            int(spec.get("rotation")),
        )
        if cell in observed_cells:
            raise ValueError(f"duplicate registered cell {cell}")
        observed_cells.add(cell)
        rows = record.get("rows")
        event_results = record.get("event_interventions")
        mark_results = record.get("mark_interventions")
        if (
            not isinstance(rows, list)
            or not rows
            or not isinstance(event_results, list)
            or not event_results
            or not isinstance(mark_results, list)
            or len(event_results) != len(mark_results)
        ):
            raise ValueError("record natural or paired branch evidence is incomplete")
        if any(row.get("provenance") != "natural" or row.get("forced") is not False for row in rows):
            raise ValueError("natural rows have invalid provenance")
        if any(result.get("kind") != "event" for result in event_results) or any(
            result.get("kind") != "mark" for result in mark_results
        ):
            raise ValueError("event and mark contrasts must remain separate")
        if any(
            result.get("controller") != controller
            or result.get("branch_origin_equal") is not True
            or result.get("common_random_numbers", {}).get("equal") is not True
            for result in (*event_results, *mark_results)
        ):
            raise ValueError("paired branch provenance is invalid")
        grouped.setdefault((str(controller), str(spec["split"])), []).append(record)

    if observed_cells != _expected_cells():
        missing = sorted(_expected_cells() - observed_cells)
        extra = sorted(observed_cells - _expected_cells())
        raise ValueError(
            f"registered controller/cell inventory is incomplete: missing={missing}, extra={extra}"
        )

    policy_dependence: dict[str, dict[str, object]] = {}
    instantaneous_tv: dict[str, dict[str, float]] = {}
    sequence_hamming: dict[str, dict[str, object]] = {}
    terminal_utility_delta: dict[str, dict[str, object]] = {}
    natural_mediation: dict[str, dict[str, object]] = {}
    heldout_robustness: dict[str, object] = {}
    controller_provenance: dict[str, object] = {}

    for controller in CONTROLLERS:
        policy_dependence[controller] = {}
        instantaneous_tv[controller] = {}
        sequence_hamming[controller] = {}
        terminal_utility_delta[controller] = {}
        natural_mediation[controller] = {}
        for split in ("fitting", "heldout"):
            cell_records = grouped[(controller, split)]
            rows = [row for record in cell_records for row in record["rows"]]
            boundary = [row for row in rows if float(row["observation"][2]) == 1.0]
            mid = [row for row in rows if float(row["observation"][2]) == 0.0]
            hidden = [row for row in rows if float(row["observation"][1]) == 0.0]
            boundary_renew = _mean(
                [float(row["event"] == "RENEW") for row in boundary],
                f"{controller}/{split} boundary renew",
            )
            mid_renew = _mean(
                [float(row["event"] == "RENEW") for row in mid],
                f"{controller}/{split} mid renew",
            )
            mid_keep = _mean(
                [float(row["event"] == "KEEP") for row in mid],
                f"{controller}/{split} mid keep",
            )
            lifetime_support = sorted(
                {
                    lifetime
                    for record in cell_records
                    for lifetime in _commitment_lifetimes(record["rows"])
                }
            )
            policy_value = {
                "renew_given_new_segment": boundary_renew,
                "renew_given_mid_segment": mid_renew,
                "difference": float(boundary_renew - mid_renew),
                "commitment_lifetime_support": lifetime_support,
            }
            policy_dependence[controller][split] = policy_value

            event_results = [
                result
                for record in cell_records
                for result in record["event_interventions"]
            ]
            mark_results = [
                result
                for record in cell_records
                for result in record["mark_interventions"]
            ]
            tv_value = _mean(
                [float(result["metrics"]["instantaneous_tv"]) for result in mark_results],
                f"{controller}/{split} instantaneous TV",
            )
            instantaneous_tv[controller][split] = tv_value
            sequence_value = {
                "event_keep_vs_renew": {
                    "hamming": _mean(
                        [float(result["metrics"]["sequence_hamming"]) for result in event_results],
                        f"{controller}/{split} event hamming",
                    ),
                    "correctness_difference": _mean(
                        [float(result["metrics"]["sequence_correctness_difference"]) for result in event_results],
                        f"{controller}/{split} event correctness",
                    ),
                },
                "mark_current_vs_opposite": {
                    "hamming": _mean(
                        [float(result["metrics"]["sequence_hamming"]) for result in mark_results],
                        f"{controller}/{split} mark hamming",
                    ),
                    "correctness_difference": _mean(
                        [float(result["metrics"]["sequence_correctness_difference"]) for result in mark_results],
                        f"{controller}/{split} mark correctness",
                    ),
                },
            }
            sequence_hamming[controller][split] = sequence_value
            terminal_value = {
                "event_keep_vs_renew": _mean(
                    [float(result["metrics"]["terminal_utility_delta"]) for result in event_results],
                    f"{controller}/{split} event utility",
                ),
                "mark_current_vs_opposite": _mean(
                    [float(result["metrics"]["terminal_utility_delta"]) for result in mark_results],
                    f"{controller}/{split} mark utility",
                ),
            }
            terminal_utility_delta[controller][split] = terminal_value
            natural_value = {
                "boundary_renew_rate": boundary_renew,
                "mid_segment_keep_rate": mid_keep,
                "hidden_post_cue_correctness": _mean(
                    [float(bool(row["evaluation_correct"])) for row in hidden],
                    f"{controller}/{split} hidden correctness",
                ),
                "natural_utility": _mean(
                    [float(record["outcome"]["utility"]) for record in cell_records],
                    f"{controller}/{split} natural utility",
                ),
            }
            natural_mediation[controller][split] = natural_value
            if split == "heldout":
                heldout_robustness[controller] = {
                    "policy_dependence": policy_value,
                    "instantaneous_tv": tv_value,
                    "sequence_hamming": sequence_value,
                    "terminal_utility_delta": terminal_value,
                    "natural_mediation": natural_value,
                }

        controller_provenance[controller] = {
            "natural_provenance": "natural",
            "fitting_cells": len(grouped[(controller, "fitting")]),
            "heldout_cells": len(grouped[(controller, "heldout")]),
            "event_contrast": "KEEP/current_vs_RENEW/opposite",
            "mark_contrast": "RENEW/current_vs_RENEW/opposite",
        }

    measurement_tuple: dict[str, Any] = {
        "policy_dependence": policy_dependence,
        "instantaneous_tv": instantaneous_tv,
        "sequence_hamming": sequence_hamming,
        "terminal_utility_delta": terminal_utility_delta,
        "natural_mediation": natural_mediation,
        "heldout_robustness": heldout_robustness,
    }
    if tuple(measurement_tuple) != _MEASUREMENT_FAMILIES:
        raise RuntimeError("measurement tuple family order changed")
    return {
        "status": "COMPLETE",
        "measurement_tuple": measurement_tuple,
        "controller_provenance": controller_provenance,
    }
