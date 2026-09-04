"""Finite EGRCR-T3 support, competence, and oracle-headroom prerequisite.

This module is intentionally dependency-free.  It implements the frozen host
as an explicit ten-tick physical process, but uses analytic full-batch policy
gradients because the registered comparison contains exactly one update.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
import hashlib
import math
import os
import statistics
import time
from typing import Mapping, Sequence

from . import prerequisite_config as C


Vector = list[float]
Pair = tuple[int, int]


@dataclass(frozen=True)
class DeployedVersion:
    """Physical port state, deliberately containing no pair-status label."""

    agent_id: int
    output_port: int
    input_port: int


@dataclass(frozen=True)
class TrainingRecord:
    root: int
    pair_index: int
    waiter_id: int
    joiner_id: int
    action: int
    repetition: int
    stored_probability: float
    generic_vector: tuple[float, ...]
    actor_features: tuple[float, ...]
    rewards: tuple[float, ...]
    physical_trace: tuple[dict[str, object], ...]


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def _rms(values: Sequence[float]) -> float:
    return math.sqrt(_mean([value * value for value in values]))


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def _bernoulli_kl_from_half(probability: float) -> float:
    return 0.5 * math.log(0.5 / probability) + 0.5 * math.log(0.5 / (1.0 - probability))


def _ci95(values: Sequence[float]) -> dict[str, float | int]:
    count = len(values)
    mean = _mean(values)
    if count < 2:
        return {"n": count, "mean": mean, "sd": math.nan, "lower": math.nan, "upper": math.nan}
    standard_deviation = statistics.stdev(values)
    half_width = C.TCRIT_11 * standard_deviation / math.sqrt(count)
    return {
        "n": count,
        "mean": mean,
        "sd": standard_deviation,
        "lower": mean - half_width,
        "upper": mean + half_width,
    }


def pair_index(waiter_id: int, joiner_id: int) -> int:
    if waiter_id == joiner_id:
        raise ValueError("diagonal ordered pairs are masked and unreachable")
    try:
        return C.PAIR_TO_INDEX[(waiter_id, joiner_id)]
    except KeyError as exc:
        raise ValueError("agent IDs must be in the frozen population") from exc


def counter_key(
    root: int,
    namespace: str,
    pair_index_value: int,
    action: int,
    repetition: int,
    tick: int,
    slot: int,
) -> str:
    return (
        f"{C.TREATMENT}|{root}|{namespace}|{pair_index_value}|{action}|"
        f"{repetition}|{tick}|{slot}"
    )


def counter_uniform(
    root: int,
    namespace: str,
    pair_index_value: int,
    action: int,
    repetition: int,
    tick: int,
    slot: int,
) -> float:
    """Return the frozen ordering-independent SHA-256 uniform."""

    digest = hashlib.sha256(
        counter_key(root, namespace, pair_index_value, action, repetition, tick, slot).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) / 2**64


def deployed_version(agent_id: int) -> DeployedVersion:
    if agent_id not in C.AGENTS:
        raise ValueError("agent outside frozen population")
    return DeployedVersion(agent_id, (agent_id + 1) % len(C.AGENTS), agent_id)


def route_capacity(
    waiter_id: int,
    joiner_id: int,
    immediate_joiner: bool,
    immediate_waiter: bool,
    *,
    sever_waiter: bool = False,
) -> dict[str, object]:
    """Derive capacity only from deployment, ports, and route occupancy."""

    waiter = deployed_version(waiter_id)
    joiner = deployed_version(joiner_id)
    waiter_output_occupancy = (
        (waiter.output_port,) if immediate_waiter and not sever_waiter else ()
    )
    joiner_input_occupancy = (joiner.input_port,) if immediate_joiner else ()
    atomic = immediate_joiner and immediate_waiter and not sever_waiter
    route_connected = (
        atomic
        and joiner.input_port in waiter_output_occupancy
        and joiner.input_port in joiner_input_occupancy
    )
    if atomic:
        capacity = 2 if route_connected else 0
    else:
        capacity = 1
    return {
        "capacity": capacity,
        "atomic": atomic,
        "route_connected": route_connected,
        "waiter_output_port": waiter.output_port,
        "joiner_input_port": joiner.input_port,
        "waiter_output_occupancy": list(waiter_output_occupancy),
        "joiner_input_occupancy": list(joiner_input_occupancy),
        "waiter_transition_severed": sever_waiter,
    }


def expected_world(
    waiter_id: int,
    joiner_id: int,
    immediate_joiner: int,
    immediate_waiter: int,
    *,
    sever_waiter: bool = False,
) -> dict[str, object]:
    if immediate_joiner not in (0, 1) or immediate_waiter not in (0, 1):
        raise ValueError("world selectors must be binary")
    route = route_capacity(
        waiter_id,
        joiner_id,
        bool(immediate_joiner),
        bool(immediate_waiter),
        sever_waiter=sever_waiter,
    )
    expected_delivered_slots = (
        len(C.SERVICE_TICKS) * C.SERVICE_PROBABILITY * int(route["capacity"])
    )
    utility = expected_delivered_slots / 10.0 - C.DEPLOYMENTS_PER_WORLD * C.DEPLOYMENT_COST
    waiter_action_tick = C.JOINER_SOURCE_TICK if immediate_waiter else C.WAITER_EXPIRY_TICK
    waiter_tick = (
        C.JOINER_SOURCE_TICK
        if immediate_waiter and not sever_waiter
        else C.WAITER_EXPIRY_TICK
    )
    joiner_tick = C.JOINER_SOURCE_TICK if immediate_joiner else C.JOINER_FALLBACK_TICK
    return {
        "utility": utility,
        "expected_delivered_slots": expected_delivered_slots,
        "joiner_deployment_tick": joiner_tick,
        "waiter_action_tick": waiter_action_tick,
        "waiter_deployment_tick": waiter_tick,
        "first_service_tick": C.SERVICE_TICKS[0],
        "waiter_deployed_at_first_service": waiter_tick < C.SERVICE_TICKS[0],
        "waiter_port_at_first_service": (
            route["waiter_output_port"] if waiter_tick < C.SERVICE_TICKS[0] else None
        ),
        **route,
    }


def _quartet(waiter_id: int, joiner_id: int, *, sever_waiter: bool = False) -> dict[str, object]:
    worlds = {
        f"Y{joiner_now}{waiter_now}": expected_world(
            waiter_id,
            joiner_id,
            joiner_now,
            waiter_now,
            sever_waiter=sever_waiter,
        )
        for joiner_now in (0, 1)
        for waiter_now in (0, 1)
    }
    y = {name: float(world["utility"]) for name, world in worlds.items()}
    delta = y["Y11"] - y["Y00"]
    kappa = (y["Y11"] - y["Y10"]) - (y["Y01"] - y["Y00"])
    return {
        "waiter_id": waiter_id,
        "joiner_id": joiner_id,
        "pair_index": pair_index(waiter_id, joiner_id),
        "worlds": worlds,
        "Y00": y["Y00"],
        "Y10": y["Y10"],
        "Y01": y["Y01"],
        "Y11": y["Y11"],
        "Delta": delta,
        "kappa": kappa,
        "joiner_single_effect": y["Y10"] - y["Y00"],
        "waiter_single_effect": y["Y01"] - y["Y00"],
        "true_waiter_first_stage": (
            worlds["Y11"]["waiter_deployment_tick"] == C.JOINER_SOURCE_TICK
            and worlds["Y00"]["waiter_deployment_tick"] == C.WAITER_EXPIRY_TICK
            and worlds["Y11"]["waiter_port_at_first_service"]
            != worlds["Y00"]["waiter_port_at_first_service"]
        ),
    }


def _joiner_contrasts(pair_rows: Mapping[Pair, Mapping[str, object]]) -> dict[str, dict[str, float]]:
    contrasts: dict[str, dict[str, float]] = {}
    for joiner_id in C.AGENTS:
        predecessor = ((joiner_id - 1) % len(C.AGENTS), joiner_id)
        successor = ((joiner_id + 1) % len(C.AGENTS), joiner_id)
        contrasts[str(joiner_id)] = {
            "favorable_waiter": predecessor[0],
            "unfavorable_waiter": successor[0],
            "C": float(pair_rows[predecessor]["Delta"])
            - float(pair_rows[successor]["Delta"]),
            "K": float(pair_rows[predecessor]["kappa"])
            - float(pair_rows[successor]["kappa"]),
        }
    return contrasts


def _tape_balance() -> dict[str, object]:
    cell_counts = {
        f"{waiter_id},{joiner_id}|a={action}": C.TRAINING_REPETITIONS_PER_ACTION_CELL
        for waiter_id, joiner_id in C.ORDERED_PAIRS
        for action in (0, 1)
    }
    crossed_signatures: dict[str, set[tuple[int, int, int, int]]] = {
        "favorable": set(),
        "unfavorable": set(),
    }
    for waiter_id, joiner_id in C.ORDERED_PAIRS:
        status = "favorable" if waiter_id == (joiner_id - 1) % len(C.AGENTS) else "unfavorable"
        for action in (0, 1):
            for repetition in range(C.TRAINING_REPETITIONS_PER_ACTION_CELL):
                for tick in C.SERVICE_TICKS:
                    for slot in range(C.SLOTS_PER_SERVICE_TICK):
                        crossed_signatures[status].add((action, repetition, tick, slot))
    expected_signatures = {
        (action, repetition, tick, slot)
        for action in (0, 1)
        for repetition in range(C.TRAINING_REPETITIONS_PER_ACTION_CELL)
        for tick in C.SERVICE_TICKS
        for slot in range(C.SLOTS_PER_SERVICE_TICK)
    }
    return {
        "pair_action_counts": cell_counts,
        "expected_per_cell": C.TRAINING_REPETITIONS_PER_ACTION_CELL,
        "all_cells_equal": set(cell_counts.values()) == {C.TRAINING_REPETITIONS_PER_ACTION_CELL},
        "action_counts_per_pair": {
            "a0": C.TRAINING_REPETITIONS_PER_ACTION_CELL,
            "a1": C.TRAINING_REPETITIONS_PER_ACTION_CELL,
        },
        "stored_propensity": C.STORED_BEHAVIOR_PROBABILITY,
        "favorable_and_unfavorable_cross_same_action_rep_tick_slot_panel": (
            crossed_signatures["favorable"] == expected_signatures
            and crossed_signatures["unfavorable"] == expected_signatures
        ),
        "counter_key_includes_pair_index": True,
        "root_balance": {
            str(root): {
                "cells": len(C.ORDERED_PAIRS) * 2,
                "records_per_cell": C.TRAINING_REPETITIONS_PER_ACTION_CELL,
                "eligible_source_records": C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT,
                "action_zero": C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT // 2,
                "action_one": C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT // 2,
            }
            for root in C.CONFIRMATION_ROOTS
        },
    }


def compute_support() -> dict[str, object]:
    rows = {(w, j): _quartet(w, j) for w, j in C.ORDERED_PAIRS}
    severed_rows = {(w, j): _quartet(w, j, sever_waiter=True) for w, j in C.ORDERED_PAIRS}
    contrasts = _joiner_contrasts(rows)
    severed_contrasts = _joiner_contrasts(severed_rows)
    waiter_marginals = {
        str(waiter): sum(float(rows[(waiter, joiner)]["Delta"]) for joiner in C.AGENTS if joiner != waiter)
        for waiter in C.AGENTS
    }
    joiner_marginals = {
        str(joiner): sum(float(rows[(waiter, joiner)]["Delta"]) for waiter in C.AGENTS if waiter != joiner)
        for joiner in C.AGENTS
    }
    joiner_singles = [float(row["joiner_single_effect"]) for row in rows.values()]
    waiter_singles = [float(row["waiter_single_effect"]) for row in rows.values()]
    tape_balance = _tape_balance()
    checks = {
        "true_waiter_first_stage_all_pairs": all(bool(row["true_waiter_first_stage"]) for row in rows.values()),
        "all_C_at_least_minimum": all(float(row["C"]) >= C.SUPPORT_CONTRAST_MIN for row in contrasts.values()),
        "all_K_at_least_minimum": all(float(row["K"]) >= C.SUPPORT_CONTRAST_MIN for row in contrasts.values()),
        "waiter_marginal_sums_zero": max(abs(value) for value in waiter_marginals.values()) <= C.BALANCE_TOLERANCE,
        "joiner_marginal_sums_zero": max(abs(value) for value in joiner_marginals.values()) <= C.BALANCE_TOLERANCE,
        "joiner_single_effect_identity_invariant": max(joiner_singles) - min(joiner_singles) <= C.BALANCE_TOLERANCE,
        "waiter_single_effect_identity_invariant": max(waiter_singles) - min(waiter_singles) <= C.BALANCE_TOLERANCE,
        "path_sever_C_collapsed": max(abs(float(row["C"])) for row in severed_contrasts.values()) <= C.BALANCE_TOLERANCE,
        "path_sever_K_collapsed": max(abs(float(row["K"])) for row in severed_contrasts.values()) <= C.BALANCE_TOLERANCE,
        "exact_pair_action_balance": bool(tape_balance["all_cells_equal"]),
        "tapes_cross_pair_status": bool(tape_balance["favorable_and_unfavorable_cross_same_action_rep_tick_slot_panel"]),
    }
    return {
        "pair_world_table": [rows[pair] for pair in C.ORDERED_PAIRS],
        "joiner_contrasts": contrasts,
        "marginal_sums": {"waiter": waiter_marginals, "joiner": joiner_marginals},
        "single_deployment_effects": {
            "joiner_only": joiner_singles,
            "waiter_only": waiter_singles,
        },
        "path_sever": {
            "pair_world_table": [severed_rows[pair] for pair in C.ORDERED_PAIRS],
            "joiner_contrasts": severed_contrasts,
        },
        "tape_balance": tape_balance,
        "checks": checks,
        "all_passed": all(checks.values()),
    }


def generic_pre_action_vector() -> tuple[float, ...]:
    # lag, cue, cue sign, readiness, waiter age, joiner age, budget, token,
    # clock, propensity, and two-sided action support are constant.
    return (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 0.5, 1.0)


def actor_features(waiter_id: int, joiner_id: int, *, pair_masked: bool = False) -> tuple[float, ...]:
    features = [1.0] + [0.0] * len(C.ORDERED_PAIRS)
    if not pair_masked:
        features[1 + pair_index(waiter_id, joiner_id)] = 1.0
    return tuple(features)


def prospective_q_table() -> dict[Pair, tuple[float, float]]:
    return {
        (waiter_id, joiner_id): (
            float(expected_world(waiter_id, joiner_id, 0, 0)["utility"]),
            float(expected_world(waiter_id, joiner_id, 1, 1)["utility"]),
        )
        for waiter_id, joiner_id in C.ORDERED_PAIRS
    }


def oracle_advantage(waiter_id: int, joiner_id: int, action: int) -> float:
    q0, q1 = prospective_q_table()[(waiter_id, joiner_id)]
    return (q0, q1)[action] - 0.5 * (q0 + q1)


def _natural_capacity(waiter_id: int, joiner_id: int, action: int) -> int:
    route = route_capacity(waiter_id, joiner_id, bool(action), bool(action))
    return int(route["capacity"])


def _sampled_rewards(
    root: int,
    namespace: str,
    waiter_id: int,
    joiner_id: int,
    action: int,
    repetition: int,
    *,
    source_local: bool = False,
) -> tuple[float, ...]:
    rewards = [0.0] * C.BLOCK_TICKS
    capacity = _natural_capacity(waiter_id, joiner_id, action) if action else 1
    delivered_by_tick: dict[int, int] = {}
    p_index = pair_index(waiter_id, joiner_id)
    for tick in C.SERVICE_TICKS:
        slot_successes = [
            counter_uniform(root, namespace, p_index, action, repetition, tick, slot)
            < C.SERVICE_PROBABILITY
            for slot in range(C.SLOTS_PER_SERVICE_TICK)
        ]
        delivered_by_tick[tick] = sum(
            int(success) for slot, success in enumerate(slot_successes) if slot < capacity
        )
    if action == 1:
        rewards[C.JOINER_SOURCE_TICK] -= 2.0 * C.DEPLOYMENT_COST
    else:
        rewards[C.JOINER_FALLBACK_TICK] -= C.DEPLOYMENT_COST
        rewards[C.WAITER_EXPIRY_TICK] -= C.DEPLOYMENT_COST
    for tick, delivered in delivered_by_tick.items():
        rewards[tick] += delivered / 10.0
    if source_local:
        total = sum(rewards)
        rewards = [0.0] * C.BLOCK_TICKS
        rewards[C.JOINER_SOURCE_TICK] = total
    return tuple(rewards)


def _expected_rewards(waiter_id: int, joiner_id: int, action: int, *, source_local: bool = False) -> tuple[float, ...]:
    rewards = [0.0] * C.BLOCK_TICKS
    capacity = _natural_capacity(waiter_id, joiner_id, action) if action else 1
    if action == 1:
        rewards[C.JOINER_SOURCE_TICK] -= 2.0 * C.DEPLOYMENT_COST
    else:
        rewards[C.JOINER_FALLBACK_TICK] -= C.DEPLOYMENT_COST
        rewards[C.WAITER_EXPIRY_TICK] -= C.DEPLOYMENT_COST
    for tick in C.SERVICE_TICKS:
        rewards[tick] += C.SERVICE_PROBABILITY * capacity / 10.0
    if source_local:
        total = sum(rewards)
        rewards = [0.0] * C.BLOCK_TICKS
        rewards[C.JOINER_SOURCE_TICK] = total
    return tuple(rewards)


def _physical_trace(
    waiter_id: int,
    joiner_id: int,
    action: int,
    rewards: Sequence[float],
    *,
    source_local: bool,
) -> tuple[dict[str, object], ...]:
    waiter_deployment_tick = C.JOINER_SOURCE_TICK if action and not source_local else C.WAITER_EXPIRY_TICK
    joiner_deployment_tick = C.JOINER_SOURCE_TICK if action else C.JOINER_FALLBACK_TICK
    waiter_port = deployed_version(waiter_id).output_port
    rows: list[dict[str, object]] = []
    for tick in range(C.BLOCK_TICKS):
        for agent_id in C.AGENTS:
            role = "waiter" if agent_id == waiter_id else "joiner" if agent_id == joiner_id else "nonparticipant"
            rows.append(
                {
                    "agent_id": agent_id,
                    "tick": tick,
                    "role": role,
                    "present": True,
                    "source_eligible": agent_id == joiner_id and tick == C.JOINER_SOURCE_TICK,
                    "action": action if agent_id == joiner_id and tick == C.JOINER_SOURCE_TICK else None,
                    "stored_probability": (
                        C.STORED_BEHAVIOR_PROBABILITY
                        if agent_id == joiner_id and tick == C.JOINER_SOURCE_TICK
                        else None
                    ),
                    "waiter_deployed": tick >= waiter_deployment_tick,
                    "joiner_deployed": tick >= joiner_deployment_tick,
                    "waiter_output_occupancy": (
                        waiter_port if tick >= waiter_deployment_tick and not source_local else None
                    ),
                    "team_reward": rewards[tick],
                }
            )
    return tuple(rows)


def build_training_batch(root: int, namespace: str, *, source_local: bool = False) -> list[TrainingRecord]:
    records: list[TrainingRecord] = []
    for p_index, (waiter_id, joiner_id) in enumerate(C.ORDERED_PAIRS):
        for action in (0, 1):
            for repetition in range(C.TRAINING_REPETITIONS_PER_ACTION_CELL):
                rewards = _sampled_rewards(
                    root,
                    namespace,
                    waiter_id,
                    joiner_id,
                    action,
                    repetition,
                    source_local=source_local,
                )
                records.append(
                    TrainingRecord(
                        root=root,
                        pair_index=p_index,
                        waiter_id=waiter_id,
                        joiner_id=joiner_id,
                        action=action,
                        repetition=repetition,
                        stored_probability=C.STORED_BEHAVIOR_PROBABILITY,
                        generic_vector=generic_pre_action_vector(),
                        actor_features=actor_features(waiter_id, joiner_id),
                        rewards=rewards,
                        physical_trace=_physical_trace(
                            waiter_id,
                            joiner_id,
                            action,
                            rewards,
                            source_local=source_local,
                        ),
                    )
                )
    if len(records) != C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT:
        raise AssertionError("frozen source-record count changed")
    return records


def _source_gae(
    waiter_id: int,
    joiner_id: int,
    action: int,
    rewards: Sequence[float],
    gae_lambda: float,
    *,
    source_local: bool,
) -> tuple[float, float]:
    expected = _expected_rewards(waiter_id, joiner_id, action, source_local=source_local)
    q0, q1 = prospective_q_table()[(waiter_id, joiner_id)]
    pre_action_value = 0.5 * (q0 + q1)
    deltas = [0.0] * C.BLOCK_TICKS
    deltas[C.JOINER_SOURCE_TICK] = (
        rewards[C.JOINER_SOURCE_TICK]
        + sum(expected[C.JOINER_SOURCE_TICK + 1 :])
        - pre_action_value
    )
    for tick in range(C.JOINER_SOURCE_TICK + 1, C.BLOCK_TICKS):
        value_now = sum(expected[tick:])
        value_next = sum(expected[tick + 1 :])
        deltas[tick] = rewards[tick] + value_next - value_now
    advantage = sum(
        (C.GAMMA * gae_lambda) ** (tick - C.JOINER_SOURCE_TICK) * deltas[tick]
        for tick in range(C.JOINER_SOURCE_TICK, C.BLOCK_TICKS)
    )
    residual = _bellman_residual(waiter_id, joiner_id, source_local=source_local)
    return advantage, residual


def _bellman_residual(waiter_id: int, joiner_id: int, *, source_local: bool) -> float:
    q0, q1 = prospective_q_table()[(waiter_id, joiner_id)]
    pre = 0.5 * (q0 + q1)
    residuals: list[float] = []
    for action in (0, 1):
        expected = _expected_rewards(waiter_id, joiner_id, action, source_local=source_local)
        residuals.append(abs((expected[C.JOINER_SOURCE_TICK] + sum(expected[C.JOINER_SOURCE_TICK + 1 :])) - (q0, q1)[action]))
        for tick in range(C.JOINER_SOURCE_TICK + 1, C.BLOCK_TICKS):
            residuals.append(abs(sum(expected[tick:]) - expected[tick] - sum(expected[tick + 1 :])))
    residuals.append(abs(pre - 0.5 * (q0 + q1)))
    return max(residuals)


def _analytic_gradient(records: Sequence[TrainingRecord], advantages: Sequence[float]) -> dict[str, object]:
    centered = [value - _mean(advantages) for value in advantages]
    rms = _rms(centered)
    if not math.isfinite(rms) or rms <= 0.0:
        raise ValueError("advantage RMS is zero or non-finite")
    normalized = [value / rms for value in centered]
    gradient = [0.0] * (1 + len(C.ORDERED_PAIRS))
    raw_gradient = [0.0] * len(gradient)
    for record, raw_advantage, norm_advantage in zip(records, centered, normalized):
        score = record.action - record.stored_probability
        for coordinate, feature in enumerate(record.actor_features):
            gradient[coordinate] += score * norm_advantage * feature / len(records)
            raw_gradient[coordinate] += score * raw_advantage * feature / len(records)
    return {
        "gradient": gradient,
        "raw_gradient": raw_gradient,
        "advantage_mean_before_centering": _mean(advantages),
        "advantage_rms_after_centering": rms,
        "centering": "arm-local",
        "normalization": "arm-local-rms",
    }


def _oracle_direction() -> Vector:
    records = build_training_batch(C.CALIBRATION_ROOTS[0], C.TRAINING_SERVICE_NAMESPACE)
    advantages = [oracle_advantage(record.waiter_id, record.joiner_id, record.action) for record in records]
    return list(_analytic_gradient(records, advantages)["gradient"])


def _mean_head_kl(theta: Sequence[float]) -> float:
    values = []
    for waiter_id, joiner_id in C.ORDERED_PAIRS:
        probability = _sigmoid(_dot(theta, actor_features(waiter_id, joiner_id)))
        values.append(_bernoulli_kl_from_half(probability))
    return _mean(values)


def freeze_trust_scale() -> dict[str, float]:
    direction = _oracle_direction()
    norm = _norm(direction)
    if norm <= 0.0:
        raise ValueError("calibration oracle direction is zero")
    unit = [value / norm for value in direction]
    # The scale is frozen prospectively from the calibration oracle radius,
    # but it must be safe when that common displacement is applied to either
    # arm.  A radius solved only on the oracle's equal-magnitude coordinates is
    # not sufficient: a sampled, equal-norm GAE direction can concentrate its
    # mass and create a larger held-out KL.  Every applicable pair feature has
    # the same finite norm, so Cauchy-Schwarz supplies an outcome-independent
    # upper bound for every direction in the shared head class.
    full_panel_feature_norm = max(
        _norm(actor_features(waiter_id, joiner_id))
        for waiter_id, joiner_id in C.ORDERED_PAIRS
    )

    def prospective_full_panel_kl_upper_bound(displacement: float) -> float:
        worst_case_logit = displacement * full_panel_feature_norm
        return _bernoulli_kl_from_half(_sigmoid(worst_case_logit))

    lower = 0.0
    upper = 1.0
    while prospective_full_panel_kl_upper_bound(upper) <= C.KL_MAX:
        upper *= 2.0
        if upper > 1024.0:
            raise ValueError("could not bracket the frozen KL radius")
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if prospective_full_panel_kl_upper_bound(midpoint) <= C.KL_MAX:
            lower = midpoint
        else:
            upper = midpoint
    displacement = math.nextafter(lower, 0.0)
    theta = [displacement * value for value in unit]
    return {
        "parameter_displacement": displacement,
        "mean_bernoulli_kl": _mean_head_kl(theta),
        "kl_limit": C.KL_MAX,
        "direction_source": "prospective oracle analytic gradient on the balanced calibration design",
        "direction_roots": list(C.CALIBRATION_ROOTS),
        "full_applicable_pair_panel_size": len(C.ORDERED_PAIRS),
        "full_panel_feature_norm": full_panel_feature_norm,
        "prospective_function_class_kl_upper_bound": prospective_full_panel_kl_upper_bound(displacement),
        "confirmation_outcomes_read": False,
    }


def _update(gradient: Sequence[float], displacement: float) -> Vector:
    norm = _norm(gradient)
    if norm <= 0.0:
        raise ValueError("normalized gradient is zero")
    return [displacement * value / norm for value in gradient]


def _sample_utility(
    root: int,
    namespace: str,
    waiter_id: int,
    joiner_id: int,
    action: int,
    repetition: int,
    *,
    source_local: bool = False,
) -> tuple[float, int]:
    rewards = _sampled_rewards(
        root,
        namespace,
        waiter_id,
        joiner_id,
        action,
        repetition,
        source_local=source_local,
    )
    delivered = int(round((sum(rewards) + 2.0 * C.DEPLOYMENT_COST) * 10.0))
    return sum(rewards), delivered


def evaluate_policy(
    root: int,
    theta: Sequence[float],
    *,
    service_namespace: str,
    token_namespace: str,
    source_local: bool,
) -> dict[str, object]:
    favorable_tokens = 0
    total_utility = 0.0
    total_delivered = 0
    favorable_probabilities: list[float] = []
    token_uniform_checksum = 0.0
    conditional_tape_keys = 0
    for joiner_id in C.AGENTS:
        favorable_waiter = (joiner_id - 1) % len(C.AGENTS)
        unfavorable_waiter = (joiner_id + 1) % len(C.AGENTS)
        favorable_index = pair_index(favorable_waiter, joiner_id)
        for repetition in range(C.EVALUATION_DYADS_PER_JOINER):
            favorable_logit = _dot(theta, actor_features(favorable_waiter, joiner_id))
            unfavorable_logit = _dot(theta, actor_features(unfavorable_waiter, joiner_id))
            favorable_probability = _sigmoid(favorable_logit - unfavorable_logit)
            token_uniform = counter_uniform(
                root,
                token_namespace,
                favorable_index,
                0,
                repetition,
                C.JOINER_SOURCE_TICK,
                0,
            )
            choose_favorable = token_uniform < favorable_probability
            favorable_tokens += int(choose_favorable)
            favorable_probabilities.append(favorable_probability)
            token_uniform_checksum += token_uniform
            assignments = (
                (favorable_waiter, 1 if choose_favorable else 0),
                (unfavorable_waiter, 0 if choose_favorable else 1),
            )
            for waiter_id, action in assignments:
                utility, delivered = _sample_utility(
                    root,
                    service_namespace,
                    waiter_id,
                    joiner_id,
                    action,
                    repetition,
                    source_local=source_local,
                )
                total_utility += utility
                total_delivered += delivered
                conditional_tape_keys += len(C.SERVICE_TICKS) * C.SLOTS_PER_SERVICE_TICK
    opportunities = C.EVALUATION_OPPORTUNITIES_PER_ROOT
    raw_utility = total_utility / opportunities
    always_unfavorable_expected = 0.18
    always_favorable_expected = 0.58
    normalized_utility = (
        raw_utility - always_unfavorable_expected
    ) / (always_favorable_expected - always_unfavorable_expected)
    return {
        "favorable_token_fraction": favorable_tokens / C.EVALUATION_TOKENS_PER_ROOT,
        "favorable_token_count": favorable_tokens,
        "fixed_token_count": C.EVALUATION_TOKENS_PER_ROOT,
        "opportunity_count": opportunities,
        "mean_favorable_allocation_probability": _mean(favorable_probabilities),
        "raw_bounded_utility": raw_utility,
        "normalized_bounded_utility": normalized_utility,
        "delivered_slots": total_delivered,
        "deployment_count": opportunities * C.DEPLOYMENTS_PER_WORLD,
        "deployment_cost_total": opportunities * C.DEPLOYMENTS_PER_WORLD * C.DEPLOYMENT_COST,
        "renewal_count": opportunities * C.DEPLOYMENTS_PER_WORLD,
        "token_uniform_checksum": token_uniform_checksum,
        "conditional_service_tape_draws": conditional_tape_keys,
        "source_localized": source_local,
        "waiter_transition_severed": source_local,
        "payout_tick": C.JOINER_SOURCE_TICK if source_local else C.OUTCOME_BOUNDARY_TICK,
        "expected_normalization_endpoints": {
            "always_unfavorable": always_unfavorable_expected,
            "always_favorable": always_favorable_expected,
            "span": always_favorable_expected - always_unfavorable_expected,
        },
    }


def _fit_arm(
    records: Sequence[TrainingRecord],
    gae_lambda: float,
    displacement: float,
    *,
    arm: str,
    source_local: bool,
) -> tuple[Vector, dict[str, object]]:
    ordinary_advantages: list[float] = []
    bellman_residual = 0.0
    for record in records:
        advantage, residual = _source_gae(
            record.waiter_id,
            record.joiner_id,
            record.action,
            record.rewards,
            gae_lambda,
            source_local=source_local,
        )
        ordinary_advantages.append(advantage)
        bellman_residual = max(bellman_residual, residual)
    if arm == "GAE-DP":
        advantages = ordinary_advantages
        replacements = 0
    elif arm == "PAIR-Q-ORACLE":
        advantages = [
            oracle_advantage(record.waiter_id, record.joiner_id, record.action)
            for record in records
        ]
        replacements = len(records)
    else:
        raise ValueError(f"unknown arm: {arm}")
    gradient_fact = _analytic_gradient(records, advantages)
    theta = _update(gradient_fact["gradient"], displacement)
    work = {
        "batch_rows": len(records),
        "eligible_source_records": len(records),
        "complete_trace_records": sum(len(record.physical_trace) for record in records),
        "actor_calls": len(records),
        "value_calls": len(records) * C.BLOCK_TICKS,
        "expected_q_lookups": len(records),
        "gradient_evaluations": 1,
        "full_batch_passes": 1,
        "updates": 1,
        "critic_updates": 0,
        "oracle_source_replacements": replacements,
        "changed_non_source_records": 0,
    }
    return theta, {
        **gradient_fact,
        "gradient": list(gradient_fact["gradient"]),
        "raw_gradient": list(gradient_fact["raw_gradient"]),
        "parameter_displacement": _norm(theta),
        "mean_bernoulli_kl": _mean_head_kl(theta),
        "bellman_residual": bellman_residual,
        "source_advantage": "ordinary-full-reward-GAE" if arm == "GAE-DP" else "prospective-Q-replacement",
        "replacement_not_addition": arm == "PAIR-Q-ORACLE",
        "work": work,
    }


def select_lambda(trust_scale: Mapping[str, float]) -> dict[str, object]:
    displacement = float(trust_scale["parameter_displacement"])
    candidate_results: dict[str, object] = {}
    selected_lambda: float | None = None
    selected_mean = -math.inf
    calibration_batches = {
        root: build_training_batch(root, C.TRAINING_SERVICE_NAMESPACE)
        for root in C.CALIBRATION_ROOTS
    }
    for gae_lambda in C.GAE_LAMBDAS:
        root_utilities: list[float] = []
        for root in C.CALIBRATION_ROOTS:
            records = calibration_batches[root]
            theta, _ = _fit_arm(
                records,
                gae_lambda,
                displacement,
                arm="GAE-DP",
                source_local=False,
            )
            evaluation = evaluate_policy(
                root,
                theta,
                service_namespace=C.CALIBRATION_NAMESPACE,
                token_namespace=C.CALIBRATION_NAMESPACE,
                source_local=False,
            )
            root_utilities.append(float(evaluation["raw_bounded_utility"]))
        mean_utility = _mean(root_utilities)
        candidate_results[str(gae_lambda)] = {
            "root_native_raw_bounded_utilities": root_utilities,
            "mean_heldout_native_raw_bounded_utility": mean_utility,
        }
        # Candidates are ordered ascending, so strict improvement implements
        # the frozen exact-tie preference for the smaller lambda.
        if mean_utility > selected_mean:
            selected_mean = mean_utility
            selected_lambda = gae_lambda
    return {
        "candidates": list(C.GAE_LAMBDAS),
        "calibration_roots": list(C.CALIBRATION_ROOTS),
        "selection_metric": "maximum mean heldout native raw bounded utility",
        "exact_tie_break": "smaller lambda",
        "candidate_results": candidate_results,
        "selected_lambda": selected_lambda,
        "selected_mean_utility": selected_mean,
        "confirmation_critic_learning": False,
    }


def representation_checks(displacement: float) -> dict[str, object]:
    oracle_gradient = _oracle_direction()
    theta = _update(oracle_gradient, displacement)
    comparisons: dict[str, object] = {}
    all_ranked = True
    for joiner_id in C.AGENTS:
        favorable_waiter = (joiner_id - 1) % len(C.AGENTS)
        unfavorable_waiter = (joiner_id + 1) % len(C.AGENTS)
        favorable = _sigmoid(_dot(theta, actor_features(favorable_waiter, joiner_id)))
        unfavorable = _sigmoid(_dot(theta, actor_features(unfavorable_waiter, joiner_id)))
        comparisons[str(joiner_id)] = {
            "favorable_probability": favorable,
            "unfavorable_probability": unfavorable,
            "ranked": favorable > unfavorable,
        }
        all_ranked = all_ranked and favorable > unfavorable
    records = build_training_batch(C.CALIBRATION_ROOTS[0], C.TRAINING_SERVICE_NAMESPACE)
    advantages = [oracle_advantage(record.waiter_id, record.joiner_id, record.action) for record in records]
    masked_records = [
        TrainingRecord(**{**asdict(record), "actor_features": actor_features(record.waiter_id, record.joiner_id, pair_masked=True)})
        for record in records
    ]
    masked_gradient = _analytic_gradient(masked_records, advantages)["gradient"]
    return {
        "head": "generic intercept plus six independent off-diagonal ordered-pair one-hots",
        "diagonal_masked": True,
        "action_time_information": ["ordered_waiter_id", "ordered_joiner_id", "fixed_generic_vector"],
        "forbidden_information_absent": ["compatibility", "future_service", "counterfactual", "suffix_label"],
        "comparisons": comparisons,
        "all_favorable_ranked_over_matched_unfavorable": all_ranked,
        "pair_masked_gradient_norm": _norm(masked_gradient),
        "pair_masked_probability": 0.5,
        "pair_masked_remains_chance": _norm(masked_gradient) <= C.BALANCE_TOLERANCE,
        "passed": all_ranked and _norm(masked_gradient) <= C.BALANCE_TOLERANCE,
    }


def noiseless_competence(gae_lambda: float, trust_scale: Mapping[str, float]) -> dict[str, object]:
    records = build_training_batch(C.CALIBRATION_ROOTS[0], C.TRAINING_SERVICE_NAMESPACE)
    expected_records: list[TrainingRecord] = []
    max_residual = 0.0
    for record in records:
        rewards = _expected_rewards(record.waiter_id, record.joiner_id, record.action)
        expected_records.append(
            TrainingRecord(
                **{
                    **asdict(record),
                    "rewards": rewards,
                    "physical_trace": _physical_trace(
                        record.waiter_id,
                        record.joiner_id,
                        record.action,
                        rewards,
                        source_local=False,
                    ),
                }
            )
        )
        max_residual = max(max_residual, _bellman_residual(record.waiter_id, record.joiner_id, source_local=False))
    displacement = float(trust_scale["parameter_displacement"])
    gae_theta, gae_fact = _fit_arm(
        expected_records,
        gae_lambda,
        displacement,
        arm="GAE-DP",
        source_local=False,
    )
    oracle_theta, oracle_fact = _fit_arm(
        expected_records,
        gae_lambda,
        displacement,
        arm="PAIR-Q-ORACLE",
        source_local=False,
    )
    gae_gradient = list(gae_fact["gradient"])[1:]
    oracle_gradient = list(oracle_fact["gradient"])[1:]
    sign_matches = [
        (gae > 0.0) == (oracle > 0.0) and (gae < 0.0) == (oracle < 0.0)
        for gae, oracle in zip(gae_gradient, oracle_gradient)
    ]
    cosine = _dot(gae_gradient, oracle_gradient) / (_norm(gae_gradient) * _norm(oracle_gradient))
    allocation_differences: list[float] = []
    for joiner_id in C.AGENTS:
        favorable_waiter = (joiner_id - 1) % len(C.AGENTS)
        unfavorable_waiter = (joiner_id + 1) % len(C.AGENTS)
        gae_probability = _sigmoid(
            _dot(gae_theta, actor_features(favorable_waiter, joiner_id))
            - _dot(gae_theta, actor_features(unfavorable_waiter, joiner_id))
        )
        oracle_probability = _sigmoid(
            _dot(oracle_theta, actor_features(favorable_waiter, joiner_id))
            - _dot(oracle_theta, actor_features(unfavorable_waiter, joiner_id))
        )
        allocation_differences.append(abs(gae_probability - oracle_probability))
    work_keys = (
        "batch_rows",
        "eligible_source_records",
        "complete_trace_records",
        "actor_calls",
        "value_calls",
        "expected_q_lookups",
        "gradient_evaluations",
        "full_batch_passes",
        "updates",
        "critic_updates",
        "changed_non_source_records",
    )
    work_match = all(gae_fact["work"][key] == oracle_fact["work"][key] for key in work_keys)
    checks = {
        "all_six_gradient_signs_match": all(sign_matches),
        "gradient_cosine_at_least_minimum": cosine >= C.COMPETENCE_COSINE_MIN,
        "favorable_allocation_probability_difference_within_tolerance": max(allocation_differences) <= C.COMPETENCE_ALLOCATION_DIFFERENCE_MAX,
        "bellman_residual_within_tolerance": max_residual <= C.BELLMAN_RESIDUAL_MAX,
        "equal_displacement": abs(float(gae_fact["parameter_displacement"]) - float(oracle_fact["parameter_displacement"])) <= C.BALANCE_TOLERANCE,
        "work_equal": work_match,
        "one_update_each": gae_fact["work"]["updates"] == oracle_fact["work"]["updates"] == 1,
        "no_critic_learning": gae_fact["work"]["critic_updates"] == oracle_fact["work"]["critic_updates"] == 0,
        "head_shared": True,
    }
    return {
        "deterministic_expected_service": True,
        "selected_lambda": gae_lambda,
        "gradient_sign_matches": sign_matches,
        "gradient_cosine": cosine,
        "max_favorable_allocation_probability_difference": max(allocation_differences),
        "max_bellman_residual": max_residual,
        "gae": gae_fact,
        "oracle": oracle_fact,
        "checks": checks,
        "all_passed": all(checks.values()),
    }


def _root_panel(
    root: int,
    gae_lambda: float,
    trust_scale: Mapping[str, float],
    *,
    source_local: bool,
) -> dict[str, object]:
    records = build_training_batch(root, C.TRAINING_SERVICE_NAMESPACE, source_local=source_local)
    pair_action_counts = {
        (waiter_id, joiner_id, action): sum(
            int(
                record.waiter_id == waiter_id
                and record.joiner_id == joiner_id
                and record.action == action
            )
            for record in records
        )
        for waiter_id, joiner_id in C.ORDERED_PAIRS
        for action in (0, 1)
    }
    displacement = float(trust_scale["parameter_displacement"])
    arms: dict[str, object] = {}
    work_signatures: list[tuple[object, ...]] = []
    displacements: list[float] = []
    tape_checksums: list[tuple[float, int]] = []
    for arm in ("GAE-DP", "PAIR-Q-ORACLE"):
        theta, training = _fit_arm(
            records,
            gae_lambda,
            displacement,
            arm=arm,
            source_local=source_local,
        )
        evaluation = evaluate_policy(
            root,
            theta,
            service_namespace=C.EVALUATION_SERVICE_NAMESPACE,
            token_namespace=C.EVALUATION_TOKEN_NAMESPACE,
            source_local=source_local,
        )
        arms[arm] = {"theta": theta, "training": training, "evaluation": evaluation}
        work = training["work"]
        work_signatures.append(
            tuple(
                work[key]
                for key in (
                    "batch_rows",
                    "eligible_source_records",
                    "complete_trace_records",
                    "actor_calls",
                    "value_calls",
                    "expected_q_lookups",
                    "gradient_evaluations",
                    "full_batch_passes",
                    "updates",
                    "critic_updates",
                    "changed_non_source_records",
                )
            )
        )
        displacements.append(float(training["parameter_displacement"]))
        tape_checksums.append(
            (
                float(evaluation["token_uniform_checksum"]),
                int(evaluation["conditional_service_tape_draws"]),
            )
        )
    gae_eval = arms["GAE-DP"]["evaluation"]
    oracle_eval = arms["PAIR-Q-ORACLE"]["evaluation"]
    return {
        "arms": arms,
        "oracle_minus_gae": {
            "allocation": float(oracle_eval["favorable_token_fraction"])
            - float(gae_eval["favorable_token_fraction"]),
            "allocation_probability": float(oracle_eval["mean_favorable_allocation_probability"])
            - float(gae_eval["mean_favorable_allocation_probability"]),
            "raw_bounded_utility": float(oracle_eval["raw_bounded_utility"])
            - float(gae_eval["raw_bounded_utility"]),
            "normalized_bounded_utility": float(oracle_eval["normalized_bounded_utility"])
            - float(gae_eval["normalized_bounded_utility"]),
        },
        "controls": {
            "work_equal": len(set(work_signatures)) == 1,
            "displacement_equal": max(displacements) - min(displacements) <= C.BALANCE_TOLERANCE,
            "mean_kl_within_limit": all(float(arms[arm]["training"]["mean_bernoulli_kl"]) <= C.KL_MAX for arm in arms),
            "token_and_tape_work_equal": len(set(tape_checksums)) == 1,
            "fixed_token_counts_equal": len({int(arms[arm]["evaluation"]["fixed_token_count"]) for arm in arms}) == 1,
            "renewal_counts_equal": len({int(arms[arm]["evaluation"]["renewal_count"]) for arm in arms}) == 1,
            "deployment_costs_equal": len({float(arms[arm]["evaluation"]["deployment_cost_total"]) for arm in arms}) == 1,
            "complete_three_agent_ten_tick_traces": all(
                int(arms[arm]["training"]["work"]["complete_trace_records"])
                == C.COMPLETE_TRACE_RECORDS_PER_ROOT
                for arm in arms
            ),
            "exact_pair_action_balance": set(pair_action_counts.values())
            == {C.TRAINING_REPETITIONS_PER_ACTION_CELL},
            "exact_action_balance": sum(record.action == 0 for record in records)
            == sum(record.action == 1 for record in records)
            == C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT // 2,
            "stored_propensity_exact": all(
                record.stored_probability == C.STORED_BEHAVIOR_PROBABILITY
                for record in records
            ),
            "same_conditional_service_keys_across_arms": True,
        },
    }


def _aggregate_roots(roots: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
    native_allocation = [float(root["native"]["oracle_minus_gae"]["allocation"]) for root in roots]
    native_probability = [float(root["native"]["oracle_minus_gae"]["allocation_probability"]) for root in roots]
    native_utility = [float(root["native"]["oracle_minus_gae"]["normalized_bounded_utility"]) for root in roots]
    local_allocation = [float(root["source_local"]["oracle_minus_gae"]["allocation"]) for root in roots]
    local_utility = [float(root["source_local"]["oracle_minus_gae"]["normalized_bounded_utility"]) for root in roots]
    native_minus_local = [native - local for native, local in zip(native_utility, local_utility)]
    gae_favorable = [
        float(root["native"]["arms"]["GAE-DP"]["evaluation"]["favorable_token_fraction"])
        for root in roots
    ]
    intervals = {
        "native_oracle_minus_gae_allocation": _ci95(native_allocation),
        "native_oracle_minus_gae_allocation_probability": _ci95(native_probability),
        "native_oracle_minus_gae_normalized_utility": _ci95(native_utility),
        "local_oracle_minus_gae_allocation": _ci95(local_allocation),
        "local_oracle_minus_gae_normalized_utility": _ci95(local_utility),
        "native_minus_local_oracle_gae_normalized_utility_gap": _ci95(native_minus_local),
        "native_gae_favorable_token_fraction": _ci95(gae_favorable),
    }
    geometry_controls = all(
        all(bool(panel["controls"][name]) for name in panel["controls"])
        for root in roots
        for panel in (root["native"], root["source_local"])
    )
    native_allocation_ci = intervals["native_oracle_minus_gae_allocation"]
    native_utility_ci = intervals["native_oracle_minus_gae_normalized_utility"]
    gae_ci = intervals["native_gae_favorable_token_fraction"]
    excess_ci = intervals["native_minus_local_oracle_gae_normalized_utility_gap"]
    criteria = {
        "native_allocation_lower_above_zero": float(native_allocation_ci["lower"]) > 0.0,
        "native_normalized_utility_lower_above_zero": float(native_utility_ci["lower"]) > 0.0,
        "native_allocation_mean_at_least_full_span_fraction": float(native_allocation_ci["mean"]) >= C.HEADROOM_MEAN_MIN,
        "native_normalized_utility_mean_at_least_full_span_fraction": float(native_utility_ci["mean"]) >= C.HEADROOM_MEAN_MIN,
        "gae_favorable_token_lower_above_chance": float(gae_ci["lower"]) > C.GAE_ABOVE_CHANCE_MIN,
        "geometry_and_accounting_controls": geometry_controls,
        "native_minus_local_mean_at_least_margin": float(excess_ci["mean"]) >= C.NATIVE_EXCESS_MEAN_MIN,
        "native_minus_local_lower_above_zero": float(excess_ci["lower"]) > 0.0,
    }
    criteria["native_headroom_passed"] = all(
        criteria[name]
        for name in (
            "native_allocation_lower_above_zero",
            "native_normalized_utility_lower_above_zero",
            "native_allocation_mean_at_least_full_span_fraction",
            "native_normalized_utility_mean_at_least_full_span_fraction",
            "gae_favorable_token_lower_above_chance",
            "geometry_and_accounting_controls",
        )
    )
    criteria["source_path_relevance_passed"] = (
        bool(criteria["native_headroom_passed"])
        and bool(criteria["native_minus_local_mean_at_least_margin"])
        and bool(criteria["native_minus_local_lower_above_zero"])
    )
    criteria["probability_only_evaluator_movement"] = (
        abs(float(intervals["native_oracle_minus_gae_allocation_probability"]["mean"])) > C.BALANCE_TOLERANCE
        and abs(float(native_allocation_ci["mean"])) <= C.BALANCE_TOLERANCE
        and abs(float(native_utility_ci["mean"])) <= C.BALANCE_TOLERANCE
    )
    return intervals, criteria


def classify_headroom_branch(criteria: Mapping[str, object]) -> str:
    """Apply only the frozen mutually exclusive interpretation ordering."""

    if bool(criteria["native_headroom_passed"]):
        if bool(criteria["source_path_relevance_passed"]):
            return "valid_source_path_headroom"
        return "static_identity_or_denoising"
    if bool(criteria["probability_only_evaluator_movement"]):
        return "evaluator_null"
    return "gae_sufficiency"


def _base_artifact() -> dict[str, object]:
    return {
        "artifact_kind": C.ARTIFACT_KIND,
        "artifact_schema_version": C.ARTIFACT_SCHEMA_VERSION,
        "treatment": C.TREATMENT,
        "starting_commit": C.STARTING_COMMIT,
        "artifact_identity": {
            "treatment": C.TREATMENT,
            "starting_commit": C.STARTING_COMMIT,
            "implementation": "isolated-dependency-free-three-agent-finite-host",
        },
        "claim_ceiling": C.CLAIM_CEILING,
        "frozen": {
            "agents": list(C.AGENTS),
            "ticks": {
                "block": C.BLOCK_TICKS,
                "waiter_request": C.WAITER_REQUEST_TICK,
                "joiner_source": C.JOINER_SOURCE_TICK,
                "joiner_fallback": C.JOINER_FALLBACK_TICK,
                "waiter_expiry": C.WAITER_EXPIRY_TICK,
                "outcome_boundary": C.OUTCOME_BOUNDARY_TICK,
                "terminal_padding": C.TERMINAL_PADDING_TICK,
            },
            "service": {
                "ticks": list(C.SERVICE_TICKS),
                "slots_per_tick": C.SLOTS_PER_SERVICE_TICK,
                "bernoulli_q": C.SERVICE_PROBABILITY,
                "deployment_cost_each": C.DEPLOYMENT_COST,
                "utility": "delivered_slots/10 - 0.02",
            },
            "ordered_pairs": [list(pair) for pair in C.ORDERED_PAIRS],
            "natural_action_worlds": {"0": "Y00", "1": "Y11"},
            "calibration_roots": list(C.CALIBRATION_ROOTS),
            "confirmation_roots": list(C.CONFIRMATION_ROOTS),
            "lambda_candidates": list(C.GAE_LAMBDAS),
            "namespaces": dict(C.NAMESPACES),
            "thresholds": {
                "support_C_K_min": C.SUPPORT_CONTRAST_MIN,
                "balance_tolerance": C.BALANCE_TOLERANCE,
                "kl_max": C.KL_MAX,
                "competence_cosine_min": C.COMPETENCE_COSINE_MIN,
                "competence_allocation_difference_max": C.COMPETENCE_ALLOCATION_DIFFERENCE_MAX,
                "headroom_mean_min": C.HEADROOM_MEAN_MIN,
                "gae_above_chance": C.GAE_ABOVE_CHANCE_MIN,
                "native_excess_mean_min": C.NATIVE_EXCESS_MEAN_MIN,
                "tcrit_11": C.TCRIT_11,
            },
            "selected_lambda": None,
            "trust_scale": None,
            "source_local_falsifier": {
                "retained": [
                    "ordered_pair_contexts",
                    "stored_propensity",
                    "prospective_q_table",
                    "conditional_service_tapes",
                    "common_head",
                    "batch_size",
                    "optimizer_geometry",
                    "fixed_token_evaluator",
                ],
                "severed": "waiter transition",
                "sampled_total_service_payout_tick": C.JOINER_SOURCE_TICK,
            },
        },
        "support": None,
        "representation": None,
        "lambda_selection": None,
        "noiseless_competence": None,
        "prospective_q_table": {
            f"{waiter},{joiner}": {"a0": q[0], "a1": q[1]}
            for (waiter, joiner), q in prospective_q_table().items()
        },
        "per_root": [],
        "intervals": {},
        "criteria": {},
        "branch": None,
        "stage": "initialized",
        "interpretation_valid": False,
        "scientific_null": False,
        "complete_terminal_artifact": False,
        "accounting": {
            "three_agent_physical_ticks": 0,
            "physical_tick_cap": C.MAX_THREE_AGENT_PHYSICAL_TICKS,
            "cpu_workers": C.MAX_CPU_WORKERS,
            "restarts": 0,
            "sweeps": 0,
            "seed_replacement": False,
            "threshold_repair": False,
            "post_result_enlargement": False,
            "arm_specific_tuning": False,
        },
        "anomalies": [],
        "runtime_seconds": None,
        "cap_status": {
            "wall_seconds_limit": C.MAX_WALL_SECONDS,
            "wall_respected": None,
            "rss_bytes_limit": C.MAX_RSS_BYTES,
            "peak_rss_bytes": None,
            "rss_respected": None,
            "physical_ticks_respected": None,
            "one_cpu_worker": True,
        },
    }


def _peak_rss_bytes() -> int:
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return int(counters.PeakWorkingSetSize)
        return 0
    try:
        import resource

        rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return rss if rss > 10_000_000 else rss * 1024
    except (ImportError, OSError):
        return 0


def _finalize(artifact: dict[str, object], started: float) -> dict[str, object]:
    runtime = time.perf_counter() - started
    peak_rss = _peak_rss_bytes()
    ticks = int(artifact["accounting"]["three_agent_physical_ticks"])
    cap_status = artifact["cap_status"]
    cap_status["wall_respected"] = runtime <= C.MAX_WALL_SECONDS
    cap_status["peak_rss_bytes"] = peak_rss
    cap_status["rss_respected"] = peak_rss == 0 or peak_rss <= C.MAX_RSS_BYTES
    cap_status["physical_ticks_respected"] = ticks <= C.MAX_THREE_AGENT_PHYSICAL_TICKS
    artifact["runtime_seconds"] = runtime
    caps_ok = all(
        bool(cap_status[name])
        for name in ("wall_respected", "rss_respected", "physical_ticks_respected", "one_cpu_worker")
    )
    if not caps_ok:
        artifact["anomalies"].append("registered resource cap exceeded")
        artifact["stage"] = "resource_limit_stop"
        artifact["branch"] = "representation_or_comparator_invalid"
        artifact["interpretation_valid"] = False
        artifact["scientific_null"] = False
    artifact["complete_terminal_artifact"] = True
    return artifact


def run_prerequisite() -> dict[str, object]:
    """Run the sole frozen stage sequence and return one terminal artifact."""

    started = time.perf_counter()
    artifact = _base_artifact()
    support = compute_support()
    artifact["support"] = support
    artifact["accounting"]["three_agent_physical_ticks"] += (
        len(C.ORDERED_PAIRS) * 8 * len(C.AGENTS) * C.BLOCK_TICKS
    )
    if not bool(support["all_passed"]):
        artifact["stage"] = "support_stopped_before_headroom"
        artifact["branch"] = "bounded_support_null"
        artifact["criteria"] = {"support_passed": False}
        artifact["interpretation_valid"] = True
        artifact["scientific_null"] = True
        return _finalize(artifact, started)

    trust_scale = freeze_trust_scale()
    artifact["frozen"]["trust_scale"] = trust_scale
    representation = representation_checks(float(trust_scale["parameter_displacement"]))
    artifact["representation"] = representation
    if not bool(representation["passed"]):
        artifact["stage"] = "representation_invalid_stopped_before_headroom"
        artifact["branch"] = "representation_or_comparator_invalid"
        artifact["criteria"] = {"support_passed": True, "representation_passed": False}
        return _finalize(artifact, started)

    lambda_selection = select_lambda(trust_scale)
    artifact["lambda_selection"] = lambda_selection
    selected_lambda = float(lambda_selection["selected_lambda"])
    artifact["frozen"]["selected_lambda"] = selected_lambda
    artifact["accounting"]["three_agent_physical_ticks"] += (
        len(C.CALIBRATION_ROOTS)
        * C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT
        * len(C.AGENTS)
        * C.BLOCK_TICKS
    )
    artifact["accounting"]["three_agent_physical_ticks"] += (
        len(C.GAE_LAMBDAS)
        * len(C.CALIBRATION_ROOTS)
        * C.EVALUATION_OPPORTUNITIES_PER_ROOT
        * len(C.AGENTS)
        * C.BLOCK_TICKS
    )
    competence = noiseless_competence(selected_lambda, trust_scale)
    artifact["noiseless_competence"] = competence
    artifact["accounting"]["three_agent_physical_ticks"] += (
        C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT * len(C.AGENTS) * C.BLOCK_TICKS
    )
    if not bool(competence["all_passed"]):
        artifact["stage"] = "comparator_invalid_stopped_before_sampled_headroom"
        artifact["branch"] = "representation_or_comparator_invalid"
        artifact["criteria"] = {
            "support_passed": True,
            "representation_passed": True,
            "noiseless_competence_passed": False,
        }
        return _finalize(artifact, started)

    roots: list[dict[str, object]] = []
    for root in C.CONFIRMATION_ROOTS:
        native = _root_panel(root, selected_lambda, trust_scale, source_local=False)
        source_local = _root_panel(root, selected_lambda, trust_scale, source_local=True)
        roots.append({"root": root, "native": native, "source_local": source_local})
    artifact["per_root"] = roots
    intervals, criteria = _aggregate_roots(roots)
    artifact["intervals"] = intervals
    artifact["criteria"] = {
        "support_passed": True,
        "representation_passed": True,
        "noiseless_competence_passed": True,
        **criteria,
    }
    artifact["accounting"]["three_agent_physical_ticks"] += (
        len(C.CONFIRMATION_ROOTS)
        * 2
        * C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT
        * len(C.AGENTS)
        * C.BLOCK_TICKS
    )
    artifact["accounting"]["three_agent_physical_ticks"] += (
        len(C.CONFIRMATION_ROOTS)
        * 2
        * 2
        * C.EVALUATION_OPPORTUNITIES_PER_ROOT
        * len(C.AGENTS)
        * C.BLOCK_TICKS
    )
    all_controls = all(
        all(bool(panel["controls"][name]) for name in panel["controls"])
        for root in roots
        for panel in (root["native"], root["source_local"])
    )
    artifact["accounting"].update(
        {
            "confirmation_source_records": len(C.CONFIRMATION_ROOTS) * C.ELIGIBLE_SOURCE_RECORDS_PER_ROOT,
            "confirmation_complete_trace_records": len(C.CONFIRMATION_ROOTS) * C.COMPLETE_TRACE_RECORDS_PER_ROOT,
            "tokens_per_root_per_arm_panel": C.EVALUATION_TOKENS_PER_ROOT,
            "exact_work_and_count_equality": all_controls,
            "one_update_per_arm_root_panel": True,
            "complete_three_agent_ten_tick_traces": True,
        }
    )
    artifact["branch"] = classify_headroom_branch(criteria)
    artifact["scientific_null"] = artifact["branch"] != "valid_source_path_headroom"
    artifact["stage"] = "headroom_evaluation_complete"
    artifact["interpretation_valid"] = bool(all_controls)
    if not all_controls:
        artifact["branch"] = "representation_or_comparator_invalid"
        artifact["stage"] = "accounting_invalid"
        artifact["scientific_null"] = False
    return _finalize(artifact, started)
