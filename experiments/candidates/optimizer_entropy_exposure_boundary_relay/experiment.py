"""Deterministic NumPy host for the OEER-B1 boundary-relay experiment.

The implementation deliberately keeps the four boundary mutations separate
from every stochastic continuation.  DELTA_MATCH and GENERIC states are made
by direct parameter assignment and therefore have fresh, empty Adam state.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np


MASTER_SEEDS = (31013, 31033, 31051, 31069, 31091, 31121, 31139, 31159)
ROOTS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
START_ROOTS = ROOTS
MEMORIES = ("CARRY", "RESET")
ENTROPIES = ("PULSE", "ZERO")
EXPOSURES = ("YOKED", "SELF")
GENERIC_KICKS = ("+J1", "-J1", "+J2", "-J2")
THETA0 = np.asarray((-0.24, -0.12, 0.12, 0.24), dtype=np.float64)
M0 = np.asarray((0.06, 0.02, -0.02, -0.06), dtype=np.float64)
V0 = np.asarray((0.0100, 0.0025, 0.0025, 0.0100), dtype=np.float64)
B0 = tuple((q, n, int(q > 0), 0.25) for q, n in ROOTS)
PANEL = tuple(
    (q, n, int(q > 0))
    for q in (-0.8, -0.4, 0.4, 0.8)
    for n in (-0.8, -0.4, 0.0, 0.4, 0.8)
)
HORIZON = 64
LEARNING_RATE = 0.02
BETA1 = 0.9
BETA2 = 0.999
EPSILON = 1e-8
MATERIALITY = 0.02
EXPECTED_CONTINUATIONS_PER_START = 32
EXPECTED_FUTURE_ROWS = 65_536
T_CRITICAL_95_DF7 = 2.3646242510103
T_CRITICAL_90_DF7 = 1.8945786050613


class ExperimentContractError(ValueError):
    """Raised when retained data cannot support the frozen contrasts."""


@dataclass(frozen=True)
class AdamState:
    m: np.ndarray
    v: np.ndarray
    t: int

    def as_dict(self) -> dict[str, Any]:
        return {"m": self.m.tolist(), "v": self.v.tolist(), "t": int(self.t)}


def fresh_adam() -> AdamState:
    return AdamState(np.zeros(4, dtype=np.float64), np.zeros(4, dtype=np.float64), 0)


def carried_adam() -> AdamState:
    return AdamState(M0.copy(), V0.copy(), 12)


def _sigmoid(value: np.ndarray | float) -> np.ndarray | float:
    array = np.asarray(value, dtype=np.float64)
    out = np.empty_like(array)
    positive = array >= 0.0
    out[positive] = 1.0 / (1.0 + np.exp(-array[positive]))
    exp_value = np.exp(array[~positive])
    out[~positive] = exp_value / (1.0 + exp_value)
    return float(out) if out.ndim == 0 else out


def adam_step(theta: np.ndarray, gradient: np.ndarray, state: AdamState) -> tuple[np.ndarray, AdamState]:
    """Apply the card's ordinary bias-corrected Adam equation."""
    theta = np.asarray(theta, dtype=np.float64)
    gradient = np.asarray(gradient, dtype=np.float64)
    if theta.shape != (4,) or gradient.shape != (4,):
        raise ExperimentContractError("Adam theta and gradient must each have four coordinates")
    step = int(state.t) + 1
    moment = BETA1 * state.m + (1.0 - BETA1) * gradient
    variance = BETA2 * state.v + (1.0 - BETA2) * gradient * gradient
    corrected_moment = moment / (1.0 - BETA1**step)
    corrected_variance = variance / (1.0 - BETA2**step)
    updated = theta - LEARNING_RATE * corrected_moment / (np.sqrt(corrected_variance) + EPSILON)
    if not np.all(np.isfinite(updated)):
        raise ExperimentContractError("nonfinite Adam update")
    return updated, AdamState(moment, variance, step)


def _root_batch_gradient(theta: np.ndarray, entropy_coefficient: float) -> np.ndarray:
    probabilities = np.asarray(_sigmoid(theta), dtype=np.float64)
    targets = np.asarray((0.0, 0.0, 1.0, 1.0), dtype=np.float64)
    # dH/dz = -z*p*(1-p); the entropy tensor is evaluated even at beta=0.
    entropy_gradient = -theta * probabilities * (1.0 - probabilities)
    return (probabilities - targets - entropy_coefficient * entropy_gradient) / 4.0


def _single_root_gradient(theta: np.ndarray, root: tuple[int, int]) -> np.ndarray:
    index = ROOTS.index(root)
    gradient = np.zeros(4, dtype=np.float64)
    gradient[index] = float(_sigmoid(theta[index])) - float(root[0] > 0)
    # This is the same graph's entropy term multiplied by numeric 0.0.
    entropy_gradient = -theta[index] * float(_sigmoid(theta[index])) * (1.0 - float(_sigmoid(theta[index])))
    gradient[index] -= 0.0 * entropy_gradient
    return gradient


def _weights(q: float, n: float) -> np.ndarray:
    return np.asarray([(1.0 + a * q) * (1.0 + b * n) / 4.0 for a, b in ROOTS], dtype=np.float64)


PANEL_WEIGHTS = np.stack([_weights(q, n) for q, n, _target in PANEL])
PANEL_TARGETS = np.asarray([target for _q, _n, target in PANEL], dtype=np.float64)


def panel_observables(
    theta: np.ndarray,
    actions_probe: int,
    probe_exposures: int,
    elapsed_steps: int,
) -> dict[str, Any]:
    logits = PANEL_WEIGHTS @ theta
    probabilities = np.asarray(_sigmoid(logits), dtype=np.float64)
    correct = np.where(PANEL_TARGETS > 0.5, probabilities, 1.0 - probabilities)
    clipped = np.clip(probabilities, 1e-15, 1.0 - 1e-15)
    entropy = -clipped * np.log(clipped) - (1.0 - clipped) * np.log(1.0 - clipped)
    signed_margin = np.where(PANEL_TARGETS > 0.5, logits, -logits)
    displacement = theta - THETA0
    denominator = float(elapsed_steps) if elapsed_steps else 1.0
    return {
        "correct_probability": float(np.mean(correct)),
        "panel_bce": float(np.mean(-np.log(np.clip(correct, 1e-15, 1.0)))),
        "panel_entropy": float(np.mean(entropy)),
        "signed_logit_margin": float(np.mean(signed_margin)),
        "root_probe_probabilities": np.asarray(_sigmoid(theta), dtype=np.float64).tolist(),
        "parameter_displacement": displacement.tolist(),
        "parameter_displacement_l2": float(np.linalg.norm(displacement)),
        "probe_action_rate": float(actions_probe / denominator) if elapsed_steps else 0.0,
        "probe_target_exposure_occupancy": float(probe_exposures / denominator) if elapsed_steps else 0.0,
    }


def _root_label(root: tuple[int, int]) -> str:
    return f"q{root[0]:+d}_n{root[1]:+d}"


def _root_list(root: tuple[int, int]) -> list[int]:
    return [int(root[0]), int(root[1])]


def build_tapes(master_seed: int) -> dict[str, dict[str, Any]]:
    """Build all four counter-keyed, sign-mirrored tapes for one master seed."""
    tapes: dict[str, dict[str, Any]] = {}
    canonical = (((1, 1), (-1, -1), 0), ((1, -1), (-1, 1), 1))
    for positive_start, negative_start, pair_index in canonical:
        streams: dict[int, np.ndarray] = {}
        for stream in (1, 2, 3):
            generator = np.random.Generator(np.random.Philox(np.random.SeedSequence([master_seed, pair_index, stream])))
            streams[stream] = generator.random(HORIZON)
        action_uniforms = streams[1]
        nuisance = np.where(streams[2] >= 0.5, 1, -1).astype(np.int8)
        yoked: list[tuple[int, int]] = []
        for block_index in range(HORIZON // 4):
            keys = streams[3][4 * block_index : 4 * block_index + 4]
            order = np.argsort(keys, kind="stable")
            yoked.extend(ROOTS[int(index)] for index in order)
        first_position = yoked.index(positive_start, 0, 4)
        yoked[0], yoked[first_position] = yoked[first_position], yoked[0]
        positive = {
            "master_seed": int(master_seed),
            "start_root": _root_list(positive_start),
            "pair_index": pair_index,
            "mirrored": False,
            "action_uniforms": action_uniforms.tolist(),
            "nuisance_bits": nuisance.astype(int).tolist(),
            "yoked_roots": [_root_list(root) for root in yoked],
        }
        negative_yoked = [(-q, -n) for q, n in yoked]
        negative = {
            "master_seed": int(master_seed),
            "start_root": _root_list(negative_start),
            "pair_index": pair_index,
            "mirrored": True,
            "action_uniforms": (1.0 - action_uniforms).tolist(),
            "nuisance_bits": (-nuisance).astype(int).tolist(),
            "yoked_roots": [_root_list(root) for root in negative_yoked],
        }
        tapes[_root_label(positive_start)] = positive
        tapes[_root_label(negative_start)] = negative
    _validate_tapes(tapes)
    return tapes


def _validate_tapes(tapes: Mapping[str, Mapping[str, Any]]) -> None:
    if set(tapes) != {_root_label(root) for root in START_ROOTS}:
        raise ExperimentContractError("tape start-root panel is incomplete")
    for root in START_ROOTS:
        tape = tapes[_root_label(root)]
        if tuple(tape["start_root"]) != root or tuple(tape["yoked_roots"][0]) != root:
            raise ExperimentContractError("yoked tape does not start at its assigned root")
        if any(len(tape[key]) != HORIZON for key in ("action_uniforms", "nuisance_bits", "yoked_roots")):
            raise ExperimentContractError("tape length mismatch")
        for offset in range(0, HORIZON, 4):
            if {tuple(value) for value in tape["yoked_roots"][offset : offset + 4]} != set(ROOTS):
                raise ExperimentContractError("yoked block is not a four-root permutation")
    for positive, negative in (((1, 1), (-1, -1)), ((1, -1), (-1, 1))):
        left, right = tapes[_root_label(positive)], tapes[_root_label(negative)]
        if not np.allclose(np.asarray(left["action_uniforms"]) + np.asarray(right["action_uniforms"]), 1.0):
            raise ExperimentContractError("mirror action uniforms are not antithetic")
        if not np.array_equal(-np.asarray(left["nuisance_bits"]), np.asarray(right["nuisance_bits"])):
            raise ExperimentContractError("mirror nuisance tape mismatch")
        if any(tuple(-x for x in a) != tuple(b) for a, b in zip(left["yoked_roots"], right["yoked_roots"])):
            raise ExperimentContractError("mirror yoked-root tape mismatch")


def _generic_kicks(delta_difference: np.ndarray) -> dict[str, np.ndarray]:
    d1, d2, d3, d4 = delta_difference
    j1 = np.asarray((d2, -d1, d4, -d3), dtype=np.float64)
    j2 = np.asarray((d3, d4, -d1, -d2), dtype=np.float64)
    kicks = {"+J1": j1, "-J1": -j1, "+J2": j2, "-J2": -j2}
    for kick in kicks.values():
        if not math.isclose(float(np.linalg.norm(kick)), float(np.linalg.norm(delta_difference)), rel_tol=1e-6, abs_tol=1e-8):
            raise ExperimentContractError("generic kick norm mismatch")
        if not math.isclose(float(np.dot(kick, delta_difference)), 0.0, rel_tol=1e-6, abs_tol=1e-8):
            raise ExperimentContractError("generic kick is not orthogonal")
    if not np.allclose(sum(kicks.values()), np.zeros(4), rtol=1e-6, atol=1e-8):
        raise ExperimentContractError("generic kicks do not sum to zero")
    return kicks


def build_boundary() -> dict[str, Any]:
    """Perform the four common B0 updates, then direct-assign every shadow."""
    if B0 != tuple((q, n, int(q > 0), 0.25) for q, n in ROOTS):
        raise ExperimentContractError("B0 changed")
    cells: dict[str, Any] = {}
    numeric: dict[tuple[str, str], tuple[np.ndarray, AdamState, np.ndarray]] = {}
    for memory, entropy in product(MEMORIES, ENTROPIES):
        initial_state = carried_adam() if memory == "CARRY" else fresh_adam()
        coefficient = 0.01 if entropy == "PULSE" else 0.0
        gradient = _root_batch_gradient(THETA0.copy(), coefficient)
        theta1, post_state = adam_step(THETA0.copy(), gradient, initial_state)
        delta = theta1 - THETA0
        key = f"{memory}|{entropy}"
        numeric[(memory, entropy)] = (theta1, post_state, delta)
        cells[key] = {
            "memory": memory,
            "entropy": entropy,
            "entropy_coefficient": coefficient,
            "gradient": gradient.tolist(),
            "theta1_main": theta1.tolist(),
            "delta": delta.tolist(),
            "post_adam_state": post_state.as_dict(),
            "delta_match": {
                "construction": "direct_parameter_assignment",
                "theta1": (THETA0 + delta).tolist(),
                "adam_state": fresh_adam().as_dict(),
            },
        }
        target = THETA0 + delta
        tolerance = 1e-8 + 1e-6 * np.maximum(1.0, np.abs(delta))
        if np.any(np.abs(theta1 - target) > tolerance):
            raise ExperimentContractError("DELTA_MATCH coordinate mismatch")
        main_panel = np.asarray(panel_observables(theta1, 0, 0, 0)["root_probe_probabilities"])
        match_panel = np.asarray(panel_observables(target, 0, 0, 0)["root_probe_probabilities"])
        if not np.allclose(main_panel, match_panel, rtol=1e-6, atol=1e-8):
            raise ExperimentContractError("DELTA_MATCH policy mismatch")
    generic: dict[str, Any] = {}
    for memory in MEMORIES:
        zero_delta = numeric[(memory, "ZERO")][2]
        difference = numeric[(memory, "PULSE")][2] - zero_delta
        kicks = _generic_kicks(difference)
        generic[memory] = {
            "entropy_displacement_difference": difference.tolist(),
            "difference_norm": float(np.linalg.norm(difference)),
            "states": {
                name: {
                    "kick": kick.tolist(),
                    "theta1": (THETA0 + zero_delta + kick).tolist(),
                    "adam_state": fresh_adam().as_dict(),
                }
                for name, kick in kicks.items()
            },
        }
    return {
        "theta0": THETA0.tolist(),
        "common_adam_state": carried_adam().as_dict(),
        "B0": [[q, n, target, weight] for q, n, target, weight in B0],
        "held_out_panel": [[q, n, target] for q, n, target in PANEL],
        "main_cells": cells,
        "generic": generic,
        "mutation_barrier": {
            "four_main_updates_completed_before_continuation": True,
            "future_tapes_materialized_before_main_updates": True,
            "arm_specific_future_data_read_during_boundary": False,
            "delta_match_direct_assignment": True,
            "delta_match_creates_optimizer_moments": False,
        },
    }


def _state_from_dict(value: Mapping[str, Any]) -> AdamState:
    return AdamState(np.asarray(value["m"], dtype=np.float64), np.asarray(value["v"], dtype=np.float64), int(value["t"]))


def _initial_conditions(boundary: Mapping[str, Any]) -> list[tuple[str, str, str | None, str | None, np.ndarray, AdamState]]:
    conditions: list[tuple[str, str, str | None, str | None, np.ndarray, AdamState]] = []
    for memory, entropy, exposure in product(MEMORIES, ENTROPIES, EXPOSURES):
        cell = boundary["main_cells"][f"{memory}|{entropy}"]
        conditions.append((f"MAIN|{memory}|{entropy}|{exposure}", "MAIN", memory, entropy, np.asarray(cell["theta1_main"]), _state_from_dict(cell["post_adam_state"])))
        conditions.append((f"DELTA_MATCH|{memory}|{entropy}|{exposure}", "DELTA_MATCH", memory, entropy, np.asarray(cell["delta_match"]["theta1"]), fresh_adam()))
    for memory, kick_name, exposure in product(MEMORIES, GENERIC_KICKS, EXPOSURES):
        state = boundary["generic"][memory]["states"][kick_name]
        conditions.append((f"GENERIC|{memory}|{kick_name}|{exposure}", "GENERIC", memory, kick_name, np.asarray(state["theta1"]), fresh_adam()))
    if len(conditions) != EXPECTED_CONTINUATIONS_PER_START or len({row[0] for row in conditions}) != len(conditions):
        raise ExperimentContractError("continuation arm construction is incomplete")
    return conditions


TRAJECTORY_FIELDS = (
    "correct_probability",
    "panel_bce",
    "panel_entropy",
    "signed_logit_margin",
    "root_probe_probabilities",
    "parameter_displacement",
    "parameter_displacement_l2",
    "probe_action_rate",
    "probe_target_exposure_occupancy",
)


def run_continuation(
    arm_id: str,
    family: str,
    memory: str,
    variant: str,
    exposure: str,
    theta1: np.ndarray,
    adam_state: AdamState,
    tape: Mapping[str, Any],
) -> dict[str, Any]:
    theta = np.asarray(theta1, dtype=np.float64).copy()
    state = AdamState(adam_state.m.copy(), adam_state.v.copy(), adam_state.t)
    current_root = tuple(int(x) for x in tape["start_root"])
    trajectories = {field: [] for field in TRAJECTORY_FIELDS}
    initial = panel_observables(theta, 0, 0, 0)
    for field in TRAJECTORY_FIELDS:
        trajectories[field].append(initial[field])
    future_rows: list[dict[str, Any]] = []
    action_count = 0
    exposure_count = 0
    for index in range(HORIZON):
        if exposure == "YOKED":
            current_root = tuple(int(x) for x in tape["yoked_roots"][index])
        action_uniform = float(tape["action_uniforms"][index])
        root_index = ROOTS.index(current_root)
        action_probe = bool(action_uniform < float(_sigmoid(theta[root_index])))
        correct_probe = current_root[0] > 0
        reward = 1 if action_probe == correct_probe else -1
        action_count += int(action_probe)
        exposure_count += int(current_root[0] > 0)
        gradient = _single_root_gradient(theta, current_root)
        theta, state = adam_step(theta, gradient, state)
        nuisance = int(tape["nuisance_bits"][index])
        if exposure == "SELF":
            next_root = (1 if action_probe else -1, nuisance)
        elif index + 1 < HORIZON:
            next_root = tuple(int(x) for x in tape["yoked_roots"][index + 1])
        else:
            next_root = current_root
        future_rows.append({
            "j": index + 1,
            "current_root": _root_list(current_root),
            "action_uniform": action_uniform,
            "action_probe": action_probe,
            "reward": reward,
            "nuisance_bit": nuisance,
            "next_root": _root_list(next_root),
        })
        current_root = next_root
        observed = panel_observables(theta, action_count, exposure_count, index + 1)
        for field in TRAJECTORY_FIELDS:
            trajectories[field].append(observed[field])
    correct_curve = np.asarray(trajectories["correct_probability"], dtype=np.float64)
    if any(len(values) != HORIZON + 1 for values in trajectories.values()) or not np.all(np.isfinite(correct_curve)):
        raise ExperimentContractError("incomplete or nonfinite continuation trajectory")
    return {
        "arm_id": arm_id,
        "family": family,
        "memory": memory,
        "variant": variant,
        "exposure": exposure,
        "start_root": list(tape["start_root"]),
        "initial_theta": np.asarray(theta1, dtype=np.float64).tolist(),
        "initial_adam_state": adam_state.as_dict(),
        "final_theta": theta.tolist(),
        "final_adam_state": state.as_dict(),
        "future_rows": future_rows,
        "trajectories": trajectories,
        "U": float(np.mean(correct_curve)),
        "endpoint_correct_probability": float(correct_curve[-1]),
        "exposure_occupancy": float(exposure_count / HORIZON),
    }


def _run_seed(master_seed: int, tapes: Mapping[str, Mapping[str, Any]], boundary: Mapping[str, Any]) -> dict[str, Any]:
    starts: dict[str, Any] = {}
    conditions = _initial_conditions(boundary)
    for root in START_ROOTS:
        label = _root_label(root)
        tape = tapes[label]
        continuations: dict[str, Any] = {}
        for arm_id, family, memory, variant, theta, state in conditions:
            exposure = arm_id.rsplit("|", 1)[-1]
            continuations[arm_id] = run_continuation(arm_id, family, str(memory), str(variant), exposure, theta, state, tape)
        starts[label] = {"start_root": list(root), "tape": dict(tape), "continuations": continuations}
    seed = {"master_seed": int(master_seed), "starts": starts}
    seed["analysis"] = analyze_seed(seed, boundary)
    return seed


def _average_starts(seed: Mapping[str, Any], field: str) -> dict[str, np.ndarray | float]:
    values: dict[str, list[Any]] = {}
    for start in seed["starts"].values():
        for arm_id, arm in start["continuations"].items():
            if field in arm:
                value = arm[field]
            else:
                value = arm["trajectories"][field]
            values.setdefault(arm_id, []).append(value)
    return {key: np.mean(np.asarray(rows, dtype=np.float64), axis=0) for key, rows in values.items()}


def _values_by_start(seed: Mapping[str, Any], field: str) -> dict[str, dict[str, np.ndarray | float]]:
    result: dict[str, dict[str, np.ndarray | float]] = {}
    for label, start in seed["starts"].items():
        values: dict[str, np.ndarray | float] = {}
        for arm_id, arm in start["continuations"].items():
            value = arm[field] if field in arm else arm["trajectories"][field]
            values[arm_id] = np.asarray(value, dtype=np.float64)
        result[label] = values
    return result


def _effect_equations(values: Mapping[str, Any]) -> dict[str, Any]:
    def arm(family: str, memory: str, variant: str, exposure: str) -> np.ndarray:
        return np.asarray(values[f"{family}|{memory}|{variant}|{exposure}"], dtype=np.float64)

    p: dict[tuple[str, str], np.ndarray] = {}
    r: dict[tuple[str, str, str], np.ndarray] = {}
    h: dict[str, np.ndarray] = {}
    for memory, exposure in product(MEMORIES, EXPOSURES):
        p[(memory, exposure)] = arm("DELTA_MATCH", memory, "PULSE", exposure) - arm("DELTA_MATCH", memory, "ZERO", exposure)
        for entropy in ENTROPIES:
            r[(memory, entropy, exposure)] = arm("MAIN", memory, entropy, exposure) - arm("DELTA_MATCH", memory, entropy, exposure)
    for exposure in EXPOSURES:
        h[exposure] = 0.5 * sum(
            (r[("CARRY", entropy, exposure)] - r[("RESET", entropy, exposure)] for entropy in ENTROPIES),
            start=np.zeros_like(r[("CARRY", "PULSE", exposure)]),
        )
    effects = {
        "D_M": 0.5 * sum((p[(memory, "YOKED")] for memory in MEMORIES), start=np.zeros_like(p[("CARRY", "YOKED")])),
        "D_H": h["YOKED"],
        "A_M": 0.5 * sum((p[(memory, "SELF")] - p[(memory, "YOKED")] for memory in MEMORIES), start=np.zeros_like(p[("CARRY", "YOKED")])),
        "A_H": h["SELF"] - h["YOKED"],
    }
    pulse_history = {
        exposure: (r[("CARRY", "PULSE", exposure)] - r[("RESET", "PULSE", exposure)])
        - (r[("CARRY", "ZERO", exposure)] - r[("RESET", "ZERO", exposure)])
        for exposure in EXPOSURES
    }
    return {"effects": effects, "P": p, "R": r, "H": h, "pulse_specific_history": pulse_history}


def _factorial(values: Mapping[str, Any], exposure: str) -> dict[str, Any]:
    def a(memory: str, entropy: str) -> np.ndarray:
        return np.asarray(values[f"MAIN|{memory}|{entropy}|{exposure}"], dtype=np.float64)
    memory = 0.5 * sum((a("CARRY", e) - a("RESET", e) for e in ENTROPIES), start=np.zeros_like(a("CARRY", "PULSE")))
    entropy = 0.5 * sum((a(m, "PULSE") - a(m, "ZERO") for m in MEMORIES), start=np.zeros_like(a("CARRY", "PULSE")))
    interaction = (a("CARRY", "PULSE") - a("CARRY", "ZERO")) - (a("RESET", "PULSE") - a("RESET", "ZERO"))
    return {"M": memory, "E": entropy, "M_x_E": interaction}


def _contributing_components(values: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """Return the unaveraged cell terms entering each scalar primary effect."""
    equations = _effect_equations(values)
    p, r = equations["P"], equations["R"]
    return {
        "D_M": {memory: float(p[(memory, "YOKED")]) for memory in MEMORIES},
        "D_H": {
            entropy: float(r[("CARRY", entropy, "YOKED")] - r[("RESET", entropy, "YOKED")])
            for entropy in ENTROPIES
        },
        "A_M": {
            memory: float(p[(memory, "SELF")] - p[(memory, "YOKED")])
            for memory in MEMORIES
        },
        "A_H": {
            entropy: float(
                (r[("CARRY", entropy, "SELF")] - r[("RESET", entropy, "SELF")])
                - (r[("CARRY", entropy, "YOKED")] - r[("RESET", entropy, "YOKED")])
            )
            for entropy in ENTROPIES
        },
    }


def _opposite_nonzero_signs(values: Iterable[float]) -> bool:
    """Detect genuine sign opposition without treating exact zero as opposition."""
    signs = {int(np.sign(value)) for value in values if math.isfinite(float(value)) and float(value) != 0.0}
    return -1 in signs and 1 in signs


def _mirror_pairs_for_effect(start_effects: Mapping[str, Mapping[str, float]], effect: str) -> list[dict[str, Any]]:
    pairs = (((1, 1), (-1, -1)), ((1, -1), (-1, 1)))
    result: list[dict[str, Any]] = []
    for positive, negative in pairs:
        positive_label, negative_label = _root_label(positive), _root_label(negative)
        left = float(start_effects[positive_label][effect])
        right = float(start_effects[negative_label][effect])
        result.append({
            "positive_start": positive_label,
            "negative_start": negative_label,
            "positive_effect": left,
            "negative_effect": right,
            "opposite_nonzero_signs": _opposite_nonzero_signs((left, right)),
        })
    return result


def _root_mirror_components(start_effects: Mapping[str, Mapping[str, float]]) -> dict[str, list[dict[str, Any]]]:
    return {
        effect: _mirror_pairs_for_effect(start_effects, effect)
        for effect in ("D_M", "D_H", "A_M", "A_H")
    }


def _jsonable_effects(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: np.asarray(value).tolist() for key, value in values.items()}


def analyze_seed(seed: Mapping[str, Any], boundary: Mapping[str, Any]) -> dict[str, Any]:
    u = _average_starts(seed, "U")
    u_by_start = _values_by_start(seed, "U")
    curves = _average_starts(seed, "correct_probability")
    occupancies = _average_starts(seed, "exposure_occupancy")
    scalar_equations = _effect_equations(u)
    curve_equations = _effect_equations(curves)
    x_m = 0.25 * sum(
        abs(float(occupancies[f"DELTA_MATCH|{memory}|{entropy}|SELF"]) - float(occupancies[f"DELTA_MATCH|{memory}|{entropy}|YOKED"]))
        for memory, entropy in product(MEMORIES, ENTROPIES)
    )
    x_h = 0.125 * sum(
        abs(float(occupancies[f"{family}|{memory}|{entropy}|SELF"]) - float(occupancies[f"{family}|{memory}|{entropy}|YOKED"]))
        for family, memory, entropy in product(("MAIN", "DELTA_MATCH"), MEMORIES, ENTROPIES)
    )
    generic_direct = 0.5 * sum(
        max(abs(float(u[f"GENERIC|{memory}|{kick}|YOKED"]) - float(u[f"DELTA_MATCH|{memory}|ZERO|YOKED"])) for kick in GENERIC_KICKS)
        for memory in MEMORIES
    )
    generic_amplification = 0.5 * sum(
        max(abs(
            (float(u[f"GENERIC|{memory}|{kick}|SELF"]) - float(u[f"DELTA_MATCH|{memory}|ZERO|SELF"]))
            - (float(u[f"GENERIC|{memory}|{kick}|YOKED"]) - float(u[f"DELTA_MATCH|{memory}|ZERO|YOKED"]))
        ) for kick in GENERIC_KICKS)
        for memory in MEMORIES
    )
    scalar_effects = {key: float(value) for key, value in scalar_equations["effects"].items()}
    start_effects = {
        label: {key: float(value) for key, value in _effect_equations(values)["effects"].items()}
        for label, values in u_by_start.items()
    }
    contributing_components = _contributing_components(u)
    root_mirrors = _root_mirror_components(start_effects)
    seed_heterogeneity = {
        effect: {
            "opposite_sign_across_contributing_cells": _opposite_nonzero_signs(contributing_components[effect].values()),
            "opposite_sign_across_root_mirrors": any(pair["opposite_nonzero_signs"] for pair in root_mirrors[effect]),
        }
        for effect in scalar_effects
    }
    delta_values = {
        f"MAIN|{memory}|{entropy}|YOKED": boundary["main_cells"][f"{memory}|{entropy}"]["delta"]
        for memory, entropy in product(MEMORIES, ENTROPIES)
    }
    return {
        "four_start_averaged_U": {key: float(value) for key, value in u.items()},
        "four_start_averaged_exposure_occupancy": {key: float(value) for key, value in occupancies.items()},
        "effects": scalar_effects,
        "effect_trajectories": _jsonable_effects(curve_equations["effects"]),
        "endpoint_effects": {key: float(np.asarray(value)[-1]) for key, value in curve_equations["effects"].items()},
        "start_root_effects": start_effects,
        "contributing_cell_effects": contributing_components,
        "root_mirror_components": root_mirrors,
        "heterogeneity": seed_heterogeneity,
        "exposure_checks": {"X_M": x_m, "X_H": x_h, "A_M_exposed": x_m >= 0.10, "A_H_exposed": x_h >= 0.10},
        "generic_envelopes": {"G_D": generic_direct, "G_A": generic_amplification},
        "generic_margins": {"D_M": abs(scalar_effects["D_M"]) - generic_direct, "A_M": abs(scalar_effects["A_M"]) - generic_amplification},
        "factorial_contrasts": {
            "delta": _jsonable_effects(_factorial(delta_values, "YOKED")),
            "U": {exposure: _jsonable_effects(_factorial(u, exposure)) for exposure in EXPOSURES},
            "correct_probability_trajectory": {exposure: _jsonable_effects(_factorial(curves, exposure)) for exposure in EXPOSURES},
        },
        "pulse_specific_history": {
            "U": _jsonable_effects(scalar_equations["pulse_specific_history"]),
            "correct_probability_trajectory": _jsonable_effects(curve_equations["pulse_specific_history"]),
        },
    }


def _sign_flip_p(values: np.ndarray) -> float:
    observed = abs(float(np.mean(values)))
    exceed = 0
    for signs in product((-1.0, 1.0), repeat=len(values)):
        permuted = abs(float(np.mean(values * np.asarray(signs))))
        exceed += int(permuted >= observed - 1e-15)
    return float(exceed / (2 ** len(values)))


def _summary(values: Iterable[float]) -> dict[str, Any]:
    array = np.asarray(tuple(values), dtype=np.float64)
    if len(array) != len(MASTER_SEEDS) or not np.all(np.isfinite(array)):
        raise ExperimentContractError("inference requires eight finite master-seed units")
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=1))
    standard_error = sd / math.sqrt(len(array))
    return {
        "unit_values": array.tolist(),
        "mean": mean,
        "standard_deviation": sd,
        "t_interval_95": [mean - T_CRITICAL_95_DF7 * standard_error, mean + T_CRITICAL_95_DF7 * standard_error],
        "t_interval_90": [mean - T_CRITICAL_90_DF7 * standard_error, mean + T_CRITICAL_90_DF7 * standard_error],
        "exact_two_sided_sign_flip_p": _sign_flip_p(array),
    }


def _trajectory_summary(seed_values: list[list[float]]) -> list[dict[str, Any]]:
    matrix = np.asarray(seed_values, dtype=np.float64)
    if matrix.shape != (len(MASTER_SEEDS), HORIZON + 1):
        raise ExperimentContractError("pointwise effect matrix is incomplete")
    rows: list[dict[str, Any]] = []
    for j in range(HORIZON + 1):
        summary = _summary(matrix[:, j])
        rows.append({"j": j, "unit_values": summary["unit_values"], "mean": summary["mean"], "t_interval_95": summary["t_interval_95"]})
    return rows


def _holm(primary: dict[str, dict[str, Any]]) -> None:
    ordered = sorted(primary, key=lambda key: float(primary[key]["exact_two_sided_sign_flip_p"]))
    running = 0.0
    count = len(ordered)
    for rank, key in enumerate(ordered):
        raw = float(primary[key]["exact_two_sided_sign_flip_p"])
        running = max(running, min(1.0, (count - rank) * raw))
        primary[key]["holm_adjusted_p"] = running
        primary[key]["holm_significant_familywise_alpha_0_10"] = running <= 0.10
    for key, report in primary.items():
        values = np.asarray(report["unit_values"])
        direction = np.sign(float(report["mean"]))
        concordant = int(np.sum(np.sign(values) == direction)) if direction else 0
        report["concordant_nonzero_sign_units"] = concordant
        report["directional_material_effect"] = bool(
            abs(float(report["mean"])) >= MATERIALITY
            and report["holm_significant_familywise_alpha_0_10"]
            and concordant >= 7
        )
        low90, high90 = report["t_interval_90"]
        report["practical_absence_supported"] = bool(low90 >= -MATERIALITY and high90 <= MATERIALITY)
        report["classification"] = (
            "directional_material_effect" if report["directional_material_effect"]
            else "practical_absence" if report["practical_absence_supported"]
            else "unresolved"
        )


def _validate_complete(result: Mapping[str, Any]) -> int:
    seeds = result.get("seeds", [])
    if [int(seed["master_seed"]) for seed in seeds] != list(MASTER_SEEDS):
        raise ExperimentContractError("master-seed panel is incomplete or reordered")
    rows = 0
    expected_starts = {_root_label(root) for root in START_ROOTS}
    expected_arms = {row[0] for row in _initial_conditions(result["boundary"])}
    for seed in seeds:
        if set(seed["starts"]) != expected_starts:
            raise ExperimentContractError("start-root quartet is incomplete")
        _validate_tapes({label: start["tape"] for label, start in seed["starts"].items()})
        for start in seed["starts"].values():
            arms = start["continuations"]
            if set(arms) != expected_arms:
                raise ExperimentContractError("continuation arm identity/count mismatch")
            tape = start["tape"]
            for arm in arms.values():
                rows += len(arm["future_rows"])
                if len(arm["future_rows"]) != HORIZON:
                    raise ExperimentContractError("future-row count mismatch")
                if any(len(arm["trajectories"][field]) != HORIZON + 1 for field in TRAJECTORY_FIELDS):
                    raise ExperimentContractError("continuous trajectory is incomplete")
                for index, row in enumerate(arm["future_rows"]):
                    if not math.isclose(float(row["action_uniform"]), float(tape["action_uniforms"][index]), rel_tol=0.0, abs_tol=0.0):
                        raise ExperimentContractError("arm-dependent action tape detected")
                    if arm["exposure"] == "YOKED" and tuple(row["current_root"]) != tuple(tape["yoked_roots"][index]):
                        raise ExperimentContractError("arm-dependent yoked-root tape detected")
    if rows != EXPECTED_FUTURE_ROWS:
        raise ExperimentContractError(f"expected {EXPECTED_FUTURE_ROWS} future rows, observed {rows}")
    return rows


def _heterogeneity_summary(seeds: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    effects = ("D_M", "D_H", "A_M", "A_H")
    result: dict[str, dict[str, Any]] = {}
    for effect in effects:
        unit_values = [float(seed["analysis"]["effects"][effect]) for seed in seeds]
        component_rows = [seed["analysis"]["contributing_cell_effects"][effect] for seed in seeds]
        component_names = tuple(component_rows[0])
        component_means = {
            name: float(np.mean([float(row[name]) for row in component_rows]))
            for name in component_names
        }
        start_labels = tuple(seeds[0]["analysis"]["start_root_effects"])
        start_means = {
            label: float(np.mean([float(seed["analysis"]["start_root_effects"][label][effect]) for seed in seeds]))
            for label in start_labels
        }
        aggregate_mirrors = _mirror_pairs_for_effect(
            {label: {effect: value} for label, value in start_means.items()}, effect
        )
        contributing_opposition = any(
            bool(seed["analysis"]["heterogeneity"][effect]["opposite_sign_across_contributing_cells"])
            for seed in seeds
        ) or _opposite_nonzero_signs(component_means.values())
        mirror_opposition = any(
            bool(seed["analysis"]["heterogeneity"][effect]["opposite_sign_across_root_mirrors"])
            for seed in seeds
        ) or any(pair["opposite_nonzero_signs"] for pair in aggregate_mirrors)
        seed_opposition = _opposite_nonzero_signs(unit_values)
        cancellation = bool(contributing_opposition or mirror_opposition or seed_opposition)
        result[effect] = {
            "contributing_cell_effects_by_seed": component_rows,
            "contributing_cell_means": component_means,
            "start_root_effect_means": start_means,
            "aggregate_root_mirror_components": aggregate_mirrors,
            "opposite_sign_across_contributing_cells": contributing_opposition,
            "opposite_sign_across_root_mirrors": mirror_opposition,
            "opposite_sign_across_seeds": seed_opposition,
            "heterogeneity_present": cancellation,
            "mean_obtained_by_cancellation": cancellation,
        }
    return result


def _claim_qualification(
    primary: Mapping[str, Mapping[str, Any]],
    exposure: Mapping[str, Mapping[str, Any]],
    generic: Mapping[str, Any],
    heterogeneity: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, bool]]:
    """Apply the card's claim gates without altering raw classifications."""
    result: dict[str, dict[str, bool]] = {}
    for effect in ("D_M", "D_H", "A_M", "A_H"):
        raw = bool(primary[effect]["directional_material_effect"])
        exposure_required = effect in ("A_M", "A_H")
        exposure_realized = (
            float(exposure["X_M" if effect == "A_M" else "X_H"]["mean"]) >= 0.10
            if exposure_required else True
        )
        generic_required = effect in ("D_M", "A_M")
        generic_separated = (
            bool(generic[f"{effect}_entropy_direction_separated"])
            if generic_required else True
        )
        no_cancellation = not bool(heterogeneity[effect]["mean_obtained_by_cancellation"])
        qualified = bool(raw and exposure_realized and generic_separated and no_cancellation)
        result[effect] = {
            "raw_directional_material_effect": raw,
            "exposure_gate_required": exposure_required,
            "exposure_gate_realized": exposure_realized,
            "generic_margin_gate_required": generic_required,
            "generic_margin_separated": generic_separated,
            "no_component_mirror_or_seed_cancellation": no_cancellation,
            "claim_qualified_directional_effect": qualified,
            "claim_qualified_entropy_specific_directional_effect": bool(qualified and generic_required),
        }
    return result


def _apply_generic_classifications(
    primary: Mapping[str, Mapping[str, Any]], generic: dict[str, Any]
) -> None:
    """Classify paired generic margins; effect/envelope marginal means are not paired."""
    for effect in ("D_M", "A_M"):
        margin = generic[f"{effect}_margin"]
        generic[f"{effect}_entropy_direction_separated"] = bool(
            float(margin["mean"]) >= MATERIALITY and float(margin["t_interval_95"][0]) > 0.0
        )
        generic[f"{effect}_within_0_02_of_generic_envelope"] = bool(
            float(margin["mean"]) < MATERIALITY
        )


def analyze_result(result: Mapping[str, Any]) -> dict[str, Any]:
    observed_rows = _validate_complete(result)
    seeds = result["seeds"]
    primary = {
        effect: _summary(seed["analysis"]["effects"][effect] for seed in seeds)
        for effect in ("D_M", "D_H", "A_M", "A_H")
    }
    _holm(primary)
    pointwise = {
        effect: _trajectory_summary([seed["analysis"]["effect_trajectories"][effect] for seed in seeds])
        for effect in ("D_M", "D_H", "A_M", "A_H")
    }
    exposure = {
        key: _summary(seed["analysis"]["exposure_checks"][key] for seed in seeds)
        for key in ("X_M", "X_H")
    }
    generic = {
        "G_D": _summary(seed["analysis"]["generic_envelopes"]["G_D"] for seed in seeds),
        "G_A": _summary(seed["analysis"]["generic_envelopes"]["G_A"] for seed in seeds),
        "D_M_margin": _summary(seed["analysis"]["generic_margins"]["D_M"] for seed in seeds),
        "A_M_margin": _summary(seed["analysis"]["generic_margins"]["A_M"] for seed in seeds),
    }
    _apply_generic_classifications(primary, generic)
    heterogeneity = _heterogeneity_summary(seeds)
    claims = _claim_qualification(primary, exposure, generic, heterogeneity)
    return {
        "raw_future_action_update_rows": observed_rows,
        "primary_effects": primary,
        "pointwise_primary_effects": pointwise,
        "endpoint_primary_effects": {effect: rows[-1] for effect, rows in pointwise.items()},
        "exposure_checks": exposure,
        "generic_envelopes_and_margins": generic,
        "heterogeneity_and_cancellation": heterogeneity,
        "claim_qualification": claims,
        "amplification_interpretability": {
            "A_M_exposure_realized_mean": float(exposure["X_M"]["mean"]) >= 0.10,
            "A_H_exposure_realized_mean": float(exposure["X_H"]["mean"]) >= 0.10,
        },
    }


def activity_witness(seed: Mapping[str, Any], boundary: Mapping[str, Any]) -> dict[str, Any]:
    delta_finite = all(np.all(np.isfinite(cell["delta"])) for cell in boundary["main_cells"].values())
    delta_match = all(
        np.allclose(cell["theta1_main"], cell["delta_match"]["theta1"], rtol=1e-6, atol=1e-8)
        for cell in boundary["main_cells"].values()
    )
    required = [
        f"{family}|{memory}|{entropy}|{exposure}"
        for family, memory, entropy, exposure in product(("MAIN", "DELTA_MATCH"), MEMORIES, ENTROPIES, EXPOSURES)
    ]
    complete = True
    for start in seed["starts"].values():
        for arm_id in required:
            arm = start["continuations"].get(arm_id)
            complete = complete and arm is not None and len(arm["future_rows"]) >= 1
            complete = complete and len(arm["trajectories"]["correct_probability"]) == HORIZON + 1
            complete = complete and math.isfinite(float(arm["trajectories"]["correct_probability"][0]))
    reached = bool(delta_finite and delta_match and complete and len(seed["starts"]) == 4)
    return {
        "schema": "OEER-B1-activity-witness-v1",
        "master_seed": int(seed["master_seed"]),
        "complete_master_seed_quartet": len(seed["starts"]) == 4,
        "all_four_main_deltas_finite": delta_finite,
        "delta_match_policies_adequate": delta_match,
        "j0_and_first_yoked_self_rows_complete_for_main_and_matched": complete,
        "activity_started": reached,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")


def run_experiment(
    *,
    activity_witness_path: Path | None = None,
    witness_writer: Callable[[Path, Mapping[str, Any]], None] = _write_json,
) -> dict[str, Any]:
    """Run exactly the registered eight-seed experiment; no reduced mode exists."""
    # Materialize every exogenous tape before the boundary mutation barrier.
    tapes = {str(seed): build_tapes(seed) for seed in MASTER_SEEDS}
    boundary = build_boundary()
    seeds: list[dict[str, Any]] = []
    for index, master_seed in enumerate(MASTER_SEEDS):
        seed = _run_seed(master_seed, tapes[str(master_seed)], boundary)
        seeds.append(seed)
        if index == 0 and activity_witness_path is not None:
            witness = activity_witness(seed, boundary)
            if not witness["activity_started"]:
                raise ExperimentContractError("activity-start criterion was not reached by first seed quartet")
            witness_writer(activity_witness_path, witness)
    result: dict[str, Any] = {
        "schema": "OEER-B1-BOUNDARY-RELAY-v1",
        "candidate": "CAND-OPTIMIZER-ENTROPY-EXPOSURE-BOUNDARY-RELAY",
        "treatment": "OEER-B1-BOUNDARY-RELAY-v1",
        "registered_budget": {
            "master_seeds": list(MASTER_SEEDS),
            "starts_per_seed": 4,
            "continuations_per_start": EXPECTED_CONTINUATIONS_PER_START,
            "future_updates_per_continuation": HORIZON,
            "expected_raw_future_action_update_rows": EXPECTED_FUTURE_ROWS,
            "panel_cues": len(PANEL),
            "trajectory_points_per_continuation": HORIZON + 1,
        },
        "boundary": boundary,
        "seeds": seeds,
        "activity_start": activity_witness(seeds[0], boundary),
    }
    result["analysis"] = analyze_result(result)
    return result
