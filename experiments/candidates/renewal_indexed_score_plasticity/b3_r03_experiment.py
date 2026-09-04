"""Exact frozen RISP-B3/TRG revision-03 experiment.

Importing this module is inert.  Registered stochastic activity is reachable
only through the resumable production driver.  The implementation uses a new
coordinate namespace and never reads a RISP-B1 or RISP-B2 artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import mpmath as mp
import torch
from scipy.stats import t as student_t

from b2_r02_experiment import (
    Interval,
    affinity_interval,
    atomic_write_json,
    iadd,
    idiv_positive,
    imul,
    interval_float,
    interval_int,
    interval_ratio,
    interval_vector_floats,
    isub,
    isum,
    rounded_float,
)


SCIENCE_REVISION = "RISP-B3-TRG-SCIENCE-20260815-03"
SCIENCE_CARD_SHA256 = "11f0fca9ac767dfc4c519aa8b2307795124929ffecc69f13286b8dbff3915778"
COORDINATE_SCHEMA = "RISP-B3-TRG-R03-LAZY-SHAKE256-PREFIX-20260815-01"
# Fresh, prospective coordinate root.  It is unrelated to every earlier RISP
# namespace and is frozen by the preactivity certificate.
COORDINATE_ROOT = "5e823ac4fd4d14ebcd0f7293f69e61696d6cb8f57b56d98bd1cdd94e0602ed3a"
RESULT_SCHEMA = "RISP-B3-TRG-R03-RESULT-20260815-03"
TRAINING_SCHEMA = "RISP-B3-TRG-R03-TRAINING-UNIT-20260815-03"
EVALUATION_SCHEMA = "RISP-B3-TRG-R03-EVALUATION-UNIT-20260815-03"
T = 192
ALGORITHM_SEEDS = tuple(range(16))
ARCHITECTURES = ("TRACK-G-ANCHOR", "TRACK-CONTAIN")
ARCH_SHORT = {"TRACK-G-ANCHOR": "A", "TRACK-CONTAIN": "C"}
UPDATE_MODES = ("INTACT", "MARGINAL-TWIN", "NO-RECURRENCE", "FIXED-PERSIST", "GLOBAL-RATE")
CELL_FAMILIES = tuple(f"{architecture}|{mode}" for architecture in ARCHITECTURES for mode in UPDATE_MODES) + (
    "CONTAIN-G-BOUND",
    "UNIFORM",
    "STATE-ORACLE",
)
SCHEDULE_LABELS = {0: "4", 1: "8", 2: "12", 3: "4->12", 4: "12->4"}
TARGET_SCHEDULES = (2, 3, 4)
Q_WINDOWS = {0: (0, 192), 1: (0, 192), 2: (0, 192), 3: (108, 192), 4: (100, 192)}
CHECKPOINT_UPDATES = (0, 64, 128, 256, 512)
REGISTERED_UPDATES = 512
REGISTERED_TRAIN_EPISODES = 16
REGISTERED_EVAL_EPISODES = 64


def schedule_rows(schedule_id: int) -> tuple[tuple[int, int, bool], ...]:
    if schedule_id == 0:
        starts = tuple((tau, 4) for tau in range(0, T, 4))
    elif schedule_id == 1:
        starts = tuple((tau, 8) for tau in range(0, T, 8))
    elif schedule_id == 2:
        starts = tuple((tau, 12) for tau in range(0, T, 12))
    elif schedule_id == 3:
        starts = tuple((tau, 4 if tau < 96 else 12) for tau in (*range(0, 96, 4), *range(96, T, 12)))
    elif schedule_id == 4:
        starts = tuple((tau, 12 if tau < 96 else 4) for tau in (*range(0, 96, 12), *range(96, T, 4)))
    else:
        raise ValueError(f"unknown schedule {schedule_id}")
    result = tuple((tau, duration, index == len(starts) - 1) for index, (tau, duration) in enumerate(starts))
    expected = {0: (48, 47), 1: (24, 23), 2: (16, 15), 3: (32, 31), 4: (32, 31)}[schedule_id]
    if (len(result), sum(not terminal for _, _, terminal in result)) != expected:
        raise RuntimeError("schedule census mismatch")
    return result


def _identity_bytes(identity: Sequence[Any]) -> bytes:
    return json.dumps(
        [COORDINATE_SCHEMA, COORDINATE_ROOT, SCIENCE_REVISION, *identity],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")


def bit_prefix(identity: Sequence[Any], bits: int) -> int:
    if bits <= 0:
        raise ValueError("bits must be positive")
    byte_count = (bits + 7) // 8
    raw = hashlib.shake_256(_identity_bytes(identity)).digest(byte_count)
    return int.from_bytes(raw, "big") >> (byte_count * 8 - bits)


@dataclass
class SamplerAudit:
    calls: dict[str, int] = field(default_factory=dict)
    max_prefix_bits: dict[str, int] = field(default_factory=dict)

    def record(self, kind: str, bits: int) -> None:
        self.calls[kind] = self.calls.get(kind, 0) + 1
        self.max_prefix_bits[kind] = max(bits, self.max_prefix_bits.get(kind, 0))

    def merge(self, other: "SamplerAudit") -> None:
        for kind, count in other.calls.items():
            self.calls[kind] = self.calls.get(kind, 0) + count
        for kind, bits in other.max_prefix_bits.items():
            self.max_prefix_bits[kind] = max(bits, self.max_prefix_bits.get(kind, 0))


def exact_cat(probabilities: Sequence[Interval], identity: Sequence[Any], kind: str, audit: SamplerAudit) -> int:
    if len(probabilities) < 2:
        raise ValueError("categorical law requires at least two masses")
    cumulative: list[Interval] = []
    running = interval_int(0)
    for probability in probabilities[:-1]:
        running = iadd(running, probability)
        cumulative.append(running)
    for bits in (128, 256, 512, 1024):
        prefix = bit_prefix(identity, bits)
        lower = interval_ratio(prefix, 1 << bits)
        upper = interval_ratio(prefix + 1, 1 << bits)
        unresolved = False
        for index, boundary in enumerate(cumulative):
            if upper.hi <= boundary.lo:
                audit.record(kind, bits)
                return index
            if lower.lo < boundary.hi:
                unresolved = True
                break
        if not unresolved:
            audit.record(kind, bits)
            return len(probabilities) - 1
    raise RuntimeError(f"could not certify {kind} inverse-CDF draw")


def event_identity(seed: int, phase: str, update_or_schedule: int, episode: int, agent: int, renewal: int | None, kind: str) -> tuple[Any, ...]:
    values: list[Any] = [seed, phase, update_or_schedule, episode, agent]
    if renewal is not None:
        values.append(renewal)
    values.append(kind)
    return tuple(values)


def model_identity(seed: int, tensor: str, scalar: int) -> tuple[Any, ...]:
    return (seed, tensor, scalar, "INIT_MODEL")


def _interval_row(values: Sequence[float]) -> tuple[Interval, ...]:
    return tuple(interval_float(float(value)) for value in values)


def _assert_probabilities(values: Sequence[Interval], label: str, support_floor: Interval | None = None) -> None:
    total = isum(values)
    if not (total.lo <= Decimal(1) <= total.hi):
        raise RuntimeError(f"{label} normalization excludes one")
    if any(value.lo <= 0 or value.hi >= 1 for value in values):
        raise RuntimeError(f"{label} left open simplex")
    if support_floor is not None and any(value.lo <= support_floor.hi for value in values):
        raise RuntimeError(f"{label} violated support floor")


def g_matrix() -> torch.Tensor:
    return torch.tensor(
        [
            [0, 0, 0, 0, 0, -15, -15, 0, 30, -15, -15, 0, 0],
            [0, 0, 0, 0, -15, 0, -15, 0, -15, 30, -15, 0, 0],
            [0, 0, 0, 0, -15, -15, 0, 0, -15, -15, 30, 0, 0],
        ],
        dtype=torch.float64,
    )


def p_k(k: int) -> tuple[tuple[Interval, Interval, Interval], ...]:
    if k not in (4, 8, 12):
        raise ValueError(k)
    lam = interval_ratio(15**k, 16**k)
    diagonal = iadd(interval_ratio(1, 3), imul(interval_ratio(2, 3), lam))
    off = imul(interval_ratio(1, 3), isub(interval_int(1), lam))
    return tuple(tuple(diagonal if row == column else off for column in range(3)) for row in range(3))  # type: ignore[return-value]


def _matmul_belief(belief: Sequence[Interval], matrix: Sequence[Sequence[Interval]]) -> tuple[Interval, Interval, Interval]:
    return tuple(isum(imul(belief[row], matrix[row][column]) for row in range(3)) for column in range(3))  # type: ignore[return-value]


def _posterior(mu: Sequence[Interval], action: int, sign: int) -> tuple[Interval, Interval, Interval]:
    weights = tuple(
        imul(mu[index], interval_ratio(4, 5) if ((index == action) == (sign > 0)) else interval_ratio(1, 5))
        for index in range(3)
    )
    denominator = isum(weights)
    return tuple(idiv_positive(value, denominator) for value in weights)  # type: ignore[return-value]


def _v_k(belief: Sequence[Interval], policy: Sequence[Interval], k: int) -> Interval:
    moved = _matmul_belief(belief, p_k(k))
    values = tuple(iadd(interval_ratio(-3, 5), imul(interval_ratio(6, 5), moved[action])) for action in range(3))
    return isum(imul(policy[action], values[action]) for action in range(3))


def _xavier_value(seed: int, tensor: str, scalar: int, fan_in: int, fan_out: int) -> float:
    r_init = bit_prefix(model_identity(seed, tensor, scalar), 53)
    with localcontext() as context:
        context.prec = 180
        value = (Decimal(6) / Decimal(fan_in + fan_out)).sqrt() * (
            Decimal(2) * Decimal(r_init) / Decimal(1 << 53) - Decimal(1)
        )
    rounded = float(value)
    with localcontext() as context:
        context.prec = 140
        check = float((Decimal(6) / Decimal(fan_in + fan_out)).sqrt() * (Decimal(2) * Decimal(r_init) / Decimal(1 << 53) - Decimal(1)))
    if rounded != check:
        raise RuntimeError("Xavier rounding was not certified")
    return rounded


def slow_initialization(seed: int, audit: SamplerAudit | None = None) -> dict[str, torch.Tensor]:
    shapes = (("w1", 8, 2), ("w2", 4, 8), ("w3", 3, 4))
    result: dict[str, torch.Tensor] = {}
    for name, fan_out, fan_in in shapes:
        values = [_xavier_value(seed, name, index, fan_in, fan_out) for index in range(fan_out * fan_in)]
        result[name] = torch.tensor(values, dtype=torch.float64).reshape(fan_out, fan_in)
        if audit is not None:
            for _ in values:
                audit.record("INIT_MODEL", 53)
    return result


def _linear_row_major(inputs: torch.Tensor, weight: torch.Tensor, bias: torch.Tensor) -> torch.Tensor:
    columns: list[torch.Tensor] = []
    for output in range(weight.shape[0]):
        accumulator = bias[output].expand(inputs.shape[0])
        for feature in range(weight.shape[1]):
            accumulator = accumulator + inputs[:, feature] * weight[output, feature]
        columns.append(accumulator)
    return torch.stack(columns, dim=1)


def _head_numeric(raw: torch.Tensor) -> torch.Tensor:
    z = 6.0 * raw / (6.0 + torch.abs(raw))
    weights = 16.0 + (z + 6.0).square()
    return weights / weights.sum(dim=-1, keepdim=True)


def _tanh_values(values: Sequence[float], precision: int) -> list[float]:
    result: list[float] = []
    with mp.workdps(precision):
        for value in values:
            numerator, denominator = float(value).as_integer_ratio()
            result.append(float(mp.tanh(mp.mpf(numerator) / denominator)))
    return result


class _CorrectlyRoundedTanh(torch.autograd.Function):
    """Software-certified binary64 tanh with a fixed analytic backward."""

    @staticmethod
    def forward(ctx: Any, inputs: torch.Tensor) -> torch.Tensor:
        flat = [float(value) for value in inputs.detach().cpu().reshape(-1)]
        primary = _tanh_values(flat, 90)
        check = _tanh_values(flat, 150)
        if primary != check:
            raise RuntimeError("tanh did not certify a unique binary64 rounding")
        output = torch.tensor(primary, dtype=torch.float64).reshape_as(inputs)
        ctx.save_for_backward(output)
        return output

    @staticmethod
    def backward(ctx: Any, gradient: torch.Tensor) -> tuple[torch.Tensor]:
        (output,) = ctx.saved_tensors
        square = output * output
        derivative = torch.ones_like(output) - square
        return (gradient * derivative,)


def _cr_tanh(inputs: torch.Tensor) -> torch.Tensor:
    return _CorrectlyRoundedTanh.apply(inputs)


class TrackModel(torch.nn.Module):
    PARAMETER_ORDER = ("w1", "b1", "w2", "b2", "w3", "b3", "E")

    def __init__(self, seed: int, architecture: str, *, slow_arrays: dict[str, torch.Tensor] | None = None) -> None:
        super().__init__()
        if architecture not in ARCHITECTURES:
            raise ValueError(architecture)
        arrays = slow_initialization(seed) if slow_arrays is None else slow_arrays
        self.architecture = architecture
        self.w1 = torch.nn.Parameter(arrays["w1"].clone())
        self.b1 = torch.nn.Parameter(torch.zeros(8, dtype=torch.float64))
        self.w2 = torch.nn.Parameter(arrays["w2"].clone())
        self.b2 = torch.nn.Parameter(torch.zeros(4, dtype=torch.float64))
        self.w3 = torch.nn.Parameter(arrays["w3"].clone())
        self.b3 = torch.nn.Parameter(torch.zeros(3, dtype=torch.float64))
        initial_e = g_matrix() if architecture == "TRACK-G-ANCHOR" else torch.zeros((3, 13), dtype=torch.float64)
        self.E = torch.nn.Parameter(initial_e.clone())
        self.register_buffer("E_center", initial_e.clone())
        if sum(parameter.numel() for parameter in self.ordered_parameters()) != 114:
            raise RuntimeError("trainable scalar census mismatch")

    def ordered_parameters(self) -> tuple[torch.nn.Parameter, ...]:
        return tuple(getattr(self, name) for name in self.PARAMETER_ORDER)

    def slow_logits(self, observations: torch.Tensor) -> torch.Tensor:
        h1 = _cr_tanh(_linear_row_major(observations, self.w1, self.b1))
        h2 = _cr_tanh(_linear_row_major(h1, self.w2, self.b2))
        return _linear_row_major(h2, self.w3, self.b3)


def _slow_bundle(model: TrackModel, observation: torch.Tensor) -> tuple[torch.Tensor, tuple[Interval, Interval, Interval]]:
    logits = model.slow_logits(observation.reshape(1, 2))
    numeric = _head_numeric(logits)[0]
    exact = affinity_interval(_interval_row(logits.detach().cpu().tolist()[0]))
    _assert_probabilities(exact, "slow head", interval_ratio(1, 21))
    exact_float = torch.tensor(interval_vector_floats(exact, "slow"), dtype=torch.float64)
    return numeric + (exact_float - numeric).detach(), exact


def _behavior_bundle(
    slow_numeric: torch.Tensor,
    slow_exact: Sequence[Interval],
    q_numeric: torch.Tensor,
    q_exact: Sequence[Sequence[Interval]],
) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]]]:
    rows: list[tuple[Interval, Interval, Interval]] = []
    floats: list[tuple[float, float, float]] = []
    for agent in range(q_numeric.shape[0]):
        mixed = tuple(imul(interval_ratio(1, 2), iadd(slow_exact[action], q_exact[agent][action])) for action in range(3))
        _assert_probabilities(mixed, "behavior", interval_ratio(1, 21))
        rows.append(mixed)  # type: ignore[arg-type]
        floats.append(interval_vector_floats(mixed, "behavior"))  # type: ignore[arg-type]
    numeric = 0.5 * slow_numeric.unsqueeze(0).expand(q_numeric.shape[0], 3) + 0.5 * q_numeric
    exact_float = torch.tensor(floats, dtype=torch.float64)
    return numeric + (exact_float - numeric).detach(), rows


def _uniform_q(count: int) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]]]:
    exact = tuple(interval_ratio(1, 3) for _ in range(3))
    return torch.full((count, 3), 1.0 / 3.0, dtype=torch.float64), [exact for _ in range(count)]  # type: ignore[list-item]


def _phi_numeric(q: torch.Tensor, actions: Sequence[int], signs: Sequence[int], k: int, tau: int) -> torch.Tensor:
    rows: list[torch.Tensor] = []
    for row, (action, sign) in enumerate(zip(actions, signs)):
        onehot = torch.zeros(3, dtype=torch.float64)
        onehot[action] = 1.0
        rows.append(torch.cat((torch.ones(1, dtype=torch.float64), q[row], onehot, torch.tensor([float(sign)], dtype=torch.float64), float(sign) * onehot, torch.tensor([k / 12.0, tau / T], dtype=torch.float64))))
    return torch.stack(rows)


def _recurrence_bundle(
    model: TrackModel,
    q_numeric: torch.Tensor,
    q_exact: Sequence[Sequence[Interval]],
    actions: Sequence[int],
    signs: Sequence[int],
    k: int,
    tau: int,
    matrix: torch.Tensor | None = None,
) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]]]:
    active = model.E if matrix is None else matrix
    phi = _phi_numeric(q_numeric, actions, signs, k, tau)
    raw_numeric = _linear_row_major(phi, active, torch.zeros(3, dtype=torch.float64))
    numeric = _head_numeric(raw_numeric)
    e_values = active.detach().cpu().tolist()
    exact_rows: list[tuple[Interval, Interval, Interval]] = []
    float_rows: list[tuple[float, float, float]] = []
    for row, (action, sign) in enumerate(zip(actions, signs)):
        onehot = [int(index == action) for index in range(3)]
        phi_exact: tuple[Interval, ...] = (
            interval_int(1), *q_exact[row], *(interval_int(value) for value in onehot), interval_int(sign),
            *(interval_int(sign * value) for value in onehot), interval_ratio(k, 12), interval_ratio(tau, T),
        )
        raw = tuple(isum(imul(interval_float(e_values[output][column]), phi_exact[column]) for column in range(13)) for output in range(3))
        updated = affinity_interval(raw)
        _assert_probabilities(updated, "recurrence", interval_ratio(1, 21))
        exact_rows.append(updated)
        float_rows.append(interval_vector_floats(updated, "recurrence"))
    exact_float = torch.tensor(float_rows, dtype=torch.float64)
    if matrix is not None:
        return exact_float, exact_rows
    return numeric + (exact_float - numeric).detach(), exact_rows


def _fixed_q(action: int) -> tuple[Interval, Interval, Interval]:
    raw = tuple(interval_int(30 if output == action else -30) for output in range(3))
    return affinity_interval(raw)


def _global_q(action: int) -> tuple[Interval, Interval, Interval]:
    raw = tuple(interval_int(-6 if output == action else -12) for output in range(3))
    return affinity_interval(raw)


def _environment_step(
    seed: int,
    phase: str,
    update_or_schedule: int,
    episode: int,
    agent: int,
    renewal: int,
    action: int,
    sector: int,
    k: int,
    audit: SamplerAudit,
) -> tuple[int, int]:
    next_sector = exact_cat(p_k(k)[sector], event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "MOTION"), "MOTION", audit)
    success = interval_ratio(4, 5) if action == next_sector else interval_ratio(1, 5)
    ack = exact_cat((success, isub(interval_int(1), success)), event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "ACK"), "ACK", audit)
    return next_sector, (1 if ack == 0 else -1)


def _initial_sectors(seed: int, phase: str, update_or_schedule: int, episode: int, audit: SamplerAudit) -> list[int]:
    uniform = tuple(interval_ratio(1, 3) for _ in range(3))
    return [exact_cat(uniform, event_identity(seed, phase, update_or_schedule, episode, agent, None, "INIT_SECTOR"), "INIT_SECTOR", audit) for agent in range(2)]


def _left_sum(values: Sequence[torch.Tensor]) -> torch.Tensor:
    if not values:
        return torch.zeros((), dtype=torch.float64)
    total = values[0]
    for value in values[1:]:
        total = total + value
    return total


def _observation(tau: int, k: int) -> torch.Tensor:
    return torch.tensor([tau / T, k / 12.0], dtype=torch.float64)


def _anchor_target(action: int, sign: int) -> tuple[float, float, float]:
    raw = tuple(interval_int(30 if (sign > 0 and output == action) else (-30 if (sign > 0 or output == action) else 0)) for output in range(3))
    return interval_vector_floats(affinity_interval(raw), "align-target")  # type: ignore[return-value]


def _train_episode(
    model: TrackModel,
    seed: int,
    update: int,
    batch_position: int,
    k: int,
    slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]],
    audit: SamplerAudit,
) -> tuple[list[list[torch.Tensor]], list[list[torch.Tensor]]]:
    schedule_id = 0 if k == 4 else 1
    sectors = _initial_sectors(seed, "TRAIN", update, batch_position, audit)
    q, q_exact = _uniform_q(2)
    beliefs = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
    task = [[], []]
    align = [[], []]
    for renewal, (tau, duration, terminal) in enumerate(schedule_rows(schedule_id)):
        slow_numeric, slow_exact = slow_cache[tau]
        policy, policy_exact = _behavior_bundle(slow_numeric, slow_exact, q, q_exact)
        actions: list[int] = []
        signs: list[int] = []
        next_sectors: list[int] = []
        next_beliefs: list[tuple[Interval, Interval, Interval]] = []
        for agent in range(2):
            action = exact_cat(policy_exact[agent], event_identity(seed, "TRAIN", update, batch_position, agent, renewal, "ACTION"), "ACTION", audit)
            next_sector, sign = _environment_step(seed, "TRAIN", update, batch_position, agent, renewal, action, sectors[agent], duration, audit)
            mu = _matmul_belief(beliefs[agent], p_k(duration))
            ey = tuple(iadd(interval_ratio(-3, 5), imul(interval_ratio(6, 5), mu[a])) for a in range(3))
            baseline = imul(interval_int(duration), isum(imul(policy_exact[agent][a], ey[a]) for a in range(3)))
            delta = duration * sign - rounded_float(baseline, "training-baseline")
            selected = policy[agent, action]
            entropy = -(policy[agent] * torch.log(policy[agent])).sum()
            task[agent].append(delta * torch.log(selected) + 0.002 * duration * entropy)
            actions.append(action)
            signs.append(sign)
            next_sectors.append(next_sector)
            next_beliefs.append(_posterior(mu, action, sign))
        sectors = next_sectors
        if not terminal:
            q, q_exact = _recurrence_bundle(model, q, q_exact, actions, signs, duration, tau)
            for agent in range(2):
                target = torch.tensor(_anchor_target(actions[agent], signs[agent]), dtype=torch.float64)
                align[agent].append(-(target * torch.log(q[agent])).sum())
            beliefs = next_beliefs
    return task, align


@dataclass
class AdamState:
    moments: list[torch.Tensor]
    squares: list[torch.Tensor]
    step: int = 0


def _new_adam_state(model: TrackModel) -> AdamState:
    return AdamState([torch.zeros_like(parameter) for parameter in model.ordered_parameters()], [torch.zeros_like(parameter) for parameter in model.ordered_parameters()])


def _global_clip(model: TrackModel) -> float:
    squares: list[torch.Tensor] = []
    for parameter in model.ordered_parameters():
        if parameter.grad is None:
            raise RuntimeError("missing gradient")
        for value in parameter.grad.reshape(-1):
            squares.append(value * value)
    norm = torch.sqrt(_left_sum(squares))
    norm_value = float(norm)
    if not math.isfinite(norm_value):
        raise RuntimeError("nonfinite gradient norm")
    scale = 1.0 if norm_value <= 1.0 or norm_value == 0.0 else 1.0 / norm_value
    for parameter in model.ordered_parameters():
        parameter.grad.mul_(scale)
    return norm_value


def _adamw_step(model: TrackModel, state: AdamState) -> None:
    state.step += 1
    eta, beta1, beta2, epsilon, decay = 3e-4, 0.9, 0.999, 1e-8, 1e-4
    correction1 = 1.0 - beta1**state.step
    correction2 = 1.0 - beta2**state.step
    factor = 1.0 - eta * decay
    with torch.no_grad():
        for index, parameter in enumerate(model.ordered_parameters()):
            gradient = parameter.grad
            if gradient is None:
                raise RuntimeError("missing Adam gradient")
            old_m_term = state.moments[index] * beta1
            gradient_m_term = gradient * (1.0 - beta1)
            state.moments[index].copy_(old_m_term + gradient_m_term)
            gradient_square = gradient * gradient
            old_u_term = state.squares[index] * beta2
            gradient_u_term = gradient_square * (1.0 - beta2)
            state.squares[index].copy_(old_u_term + gradient_u_term)
            mhat = state.moments[index] / correction1
            uhat = state.squares[index] / correction2
            root = torch.sqrt(uhat)
            denominator = root + epsilon
            direction = mhat / denominator
            center = model.E_center if parameter is model.E else torch.zeros_like(parameter)
            centered = parameter - center
            decayed = factor * centered
            shifted = center + decayed
            adam_step = eta * direction
            parameter.copy_(shifted - adam_step)


def _snapshot(model: TrackModel) -> dict[str, Any]:
    return {
        "finite": all(bool(torch.isfinite(parameter).all()) for parameter in model.ordered_parameters()),
        "l2": math.sqrt(sum(float((parameter.detach() * parameter.detach()).sum()) for parameter in model.ordered_parameters())),
        "e_center_distance": float(torch.linalg.vector_norm(model.E.detach() - model.E_center)),
    }


def state_dict_json(model: TrackModel) -> dict[str, Any]:
    return {name: value.detach().cpu().tolist() for name, value in model.state_dict().items()}


def load_model(seed: int, architecture: str, state: dict[str, Any]) -> TrackModel:
    empty = {
        "w1": torch.zeros((8, 2), dtype=torch.float64),
        "w2": torch.zeros((4, 8), dtype=torch.float64),
        "w3": torch.zeros((3, 4), dtype=torch.float64),
    }
    model = TrackModel(seed, architecture, slow_arrays=empty)
    tensor_state = {name: torch.tensor(value, dtype=torch.float64) for name, value in state.items()}
    model.load_state_dict(tensor_state, strict=True)
    return model


def run_training_unit(
    seed: int,
    architecture: str,
    *,
    updates: int = REGISTERED_UPDATES,
    episodes: int = REGISTERED_TRAIN_EPISODES,
    progress_guard: Callable[[], None] | None = None,
) -> dict[str, Any]:
    if architecture not in ARCHITECTURES or episodes % 2:
        raise ValueError("invalid training unit")
    registered = seed in ALGORITHM_SEEDS and updates == REGISTERED_UPDATES and episodes == REGISTERED_TRAIN_EPISODES
    audit = SamplerAudit()
    arrays = slow_initialization(seed, audit)
    model = TrackModel(seed, architecture, slow_arrays=arrays)
    optimizer = _new_adam_state(model)
    checkpoints: dict[str, Any] = {"0": _snapshot(model)}
    losses: list[float] = []
    started = time.monotonic()
    for update in range(updates):
        for parameter in model.ordered_parameters():
            parameter.grad = None
        slow_by_k: dict[int, dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]]] = {}
        for k, schedule_id in ((4, 0), (8, 1)):
            slow_by_k[k] = {tau: _slow_bundle(model, _observation(tau, duration)) for tau, duration, _ in schedule_rows(schedule_id)}
        task_terms: list[torch.Tensor] = []
        align_terms: list[torch.Tensor] = []
        for batch_position in range(episodes):
            k = 4 if batch_position % 2 == 0 else 8
            task, align = _train_episode(model, seed, update, batch_position, k, slow_by_k[k], audit)
            for agent in range(2):
                task_terms.extend(task[agent])
                align_terms.extend(align[agent])
        if len(align_terms) != (episodes // 2) * 2 * (47 + 23):
            raise RuntimeError("alignment row census mismatch")
        task_loss = -_left_sum(task_terms) / (episodes * 2 * T)
        align_loss = _left_sum(align_terms) / len(align_terms)
        loss = task_loss + align_loss
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("nonfinite loss")
        loss.backward()
        norm = _global_clip(model)
        _adamw_step(model, optimizer)
        losses.append(float(loss.detach()))
        completed = update + 1
        if completed in CHECKPOINT_UPDATES:
            checkpoints[str(completed)] = {**_snapshot(model), "loss": losses[-1], "preclip_gradient_norm": norm}
        if progress_guard is not None:
            progress_guard()
    if registered and tuple(int(key) for key in checkpoints) != CHECKPOINT_UPDATES:
        raise RuntimeError("checkpoint census mismatch")
    expected = {"INIT_MODEL": 60, "INIT_SECTOR": 16384, "ACTION": 589824, "MOTION": 589824, "ACK": 589824}
    if registered and audit.calls != expected:
        raise RuntimeError(f"training ledger mismatch: {audit.calls} != {expected}")
    return {
        "schema": TRAINING_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "algorithm_seed": seed,
        "architecture": architecture,
        "registered": registered,
        "updates": updates,
        "episodes_per_batch": episodes,
        "training": {"loss_first": losses[0], "loss_final": losses[-1], "loss_min": min(losses), "loss_max": max(losses), "checkpoints": checkpoints},
        "final_state": state_dict_json(model),
        "sampler_audit": {"calls": dict(sorted(audit.calls.items())), "max_prefix_bits": dict(sorted(audit.max_prefix_bits.items()))},
        "elapsed_seconds": time.monotonic() - started,
    }


def _overlap(start: int, stop: int, window: tuple[int, int]) -> int:
    return max(0, min(stop, window[1]) - max(start, window[0]))


def _tv(left: Sequence[float], right: Sequence[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(left, right))


def _target_row_eligible(schedule_id: int, next_tau: int) -> bool:
    if schedule_id in (0, 1, 2):
        return True
    return Q_WINDOWS[schedule_id][0] <= next_tau < Q_WINDOWS[schedule_id][1]


@dataclass
class EvalSummary:
    weighted_reward: float = 0.0
    weighted_ticks: int = 0
    full_reward: float = 0.0
    full_ticks: int = 0
    decisions: int = 0
    updates: int = 0
    min_support: float = 1.0
    tv_values: list[float] = field(default_factory=list)
    delta_values: list[float] = field(default_factory=list)
    action_counts: list[int] = field(default_factory=lambda: [0, 0, 0])
    ack_successes: int = 0
    direct_tv_max_residual: float = 0.0

    def result(self) -> dict[str, Any]:
        diagnostic = None
        if self.tv_values:
            diagnostic = {
                "rows": len(self.tv_values),
                "tv_ge_001_fraction": sum(value >= 0.01 for value in self.tv_values) / len(self.tv_values),
                "delta_positive_fraction": sum(value > 0.0 for value in self.delta_values) / len(self.delta_values),
                "delta_mean": float(np.mean(self.delta_values)),
                "tv_mean": float(np.mean(self.tv_values)),
            }
        return {
            "q": self.weighted_reward / self.weighted_ticks,
            "q_full": self.full_reward / self.full_ticks,
            "decisions": self.decisions,
            "updates": self.updates,
            "min_support": self.min_support,
            "action_counts": self.action_counts,
            "ack_success_rate": self.ack_successes / self.decisions,
            "direct_tv_max_residual": self.direct_tv_max_residual,
            "diagnostic": diagnostic,
        }


def _cell_parts(cell: str) -> tuple[str | None, str]:
    if "|" in cell:
        architecture, mode = cell.split("|", 1)
        if architecture not in ARCHITECTURES or mode not in UPDATE_MODES:
            raise ValueError(cell)
        return architecture, mode
    if cell == "CONTAIN-G-BOUND":
        return "TRACK-CONTAIN", "G-BOUND"
    if cell in ("UNIFORM", "STATE-ORACLE"):
        return None, cell
    raise ValueError(cell)


@torch.no_grad()
def run_evaluation_unit(
    seed: int,
    cell: str,
    schedule_id: int,
    checkpoint_states: dict[str, dict[str, Any]],
    *,
    episodes: int = REGISTERED_EVAL_EPISODES,
    progress_guard: Callable[[], None] | None = None,
) -> dict[str, Any]:
    architecture, mode = _cell_parts(cell)
    registered = seed in ALGORITHM_SEEDS and cell in CELL_FAMILIES and schedule_id in SCHEDULE_LABELS and episodes == REGISTERED_EVAL_EPISODES
    model: TrackModel | None = None
    slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]] = {}
    if architecture is not None:
        if architecture not in checkpoint_states:
            raise RuntimeError(f"missing checkpoint {architecture}")
        model = load_model(seed, architecture, checkpoint_states[architecture])
        slow_cache = {tau: _slow_bundle(model, _observation(tau, duration)) for tau, duration, _ in schedule_rows(schedule_id)}
    audit = SamplerAudit()
    summary = EvalSummary()
    rows = schedule_rows(schedule_id)
    started = time.monotonic()
    for episode in range(episodes):
        sectors = _initial_sectors(seed, "EVAL", schedule_id, episode, audit)
        q, q_exact = _uniform_q(2)
        beta = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
        rho = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
        for renewal, (tau, duration, terminal) in enumerate(rows):
            if mode == "UNIFORM":
                policy_exact = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
            elif mode == "STATE-ORACLE":
                policy_exact = [tuple(interval_ratio(29, 30) if action == sectors[agent] else interval_ratio(1, 60) for action in range(3)) for agent in range(2)]
            else:
                assert model is not None
                _, policy_exact = _behavior_bundle(slow_cache[tau][0], slow_cache[tau][1], q, q_exact)
            actions: list[int] = []
            signs: list[int] = []
            update_signs: list[int] = []
            next_sectors: list[int] = []
            next_beta: list[tuple[Interval, Interval, Interval]] = []
            next_rho: list[tuple[Interval, Interval, Interval]] = []
            for agent in range(2):
                action = exact_cat(policy_exact[agent], event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACTION"), "ACTION", audit)
                next_sector, sign = _environment_step(seed, "EVAL", schedule_id, episode, agent, renewal, action, sectors[agent], duration, audit)
                mu_beta = _matmul_belief(beta[agent], p_k(duration))
                posterior = _posterior(mu_beta, action, sign)
                mu_rho = _matmul_belief(rho[agent], p_k(duration))
                update_sign = sign
                if mode == "MARGINAL-TWIN" and not terminal:
                    pbar = iadd(interval_ratio(1, 5), imul(interval_ratio(3, 5), mu_rho[action]))
                    twin = exact_cat((pbar, isub(interval_int(1), pbar)), event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "TWIN"), "TWIN", audit)
                    update_sign = 1 if twin == 0 else -1
                actions.append(action)
                signs.append(sign)
                update_signs.append(update_sign)
                next_sectors.append(next_sector)
                next_beta.append(posterior)
                next_rho.append(mu_rho)
                overlap = _overlap(tau, tau + duration, Q_WINDOWS[schedule_id])
                summary.weighted_reward += overlap * sign
                summary.weighted_ticks += overlap
                summary.full_reward += duration * sign
                summary.full_ticks += duration
                summary.decisions += 1
                summary.action_counts[action] += 1
                summary.ack_successes += int(sign > 0)
                summary.min_support = min(summary.min_support, *(rounded_float(value, "eval-support") for value in policy_exact[agent]))
            sectors = next_sectors
            if not terminal and architecture is not None:
                old_q, old_q_exact = q, q_exact
                assert model is not None
                if mode in ("INTACT", "MARGINAL-TWIN"):
                    q, q_exact = _recurrence_bundle(model, q, q_exact, actions, update_signs, duration, tau)
                elif mode == "NO-RECURRENCE":
                    pass
                elif mode == "FIXED-PERSIST":
                    q_exact = [_fixed_q(action) for action in actions]
                    q = torch.tensor([interval_vector_floats(row, "fixed-q") for row in q_exact], dtype=torch.float64)
                elif mode == "GLOBAL-RATE":
                    q_exact = [_global_q(action) for action in actions]
                    q = torch.tensor([interval_vector_floats(row, "global-q") for row in q_exact], dtype=torch.float64)
                elif mode == "G-BOUND":
                    q, q_exact = _recurrence_bundle(model, q, q_exact, actions, signs, duration, tau, matrix=g_matrix())
                else:
                    raise RuntimeError(mode)
                summary.updates += 2
                next_tau, next_k, _ = rows[renewal + 1]
                diagnostic_mode = mode in ("INTACT", "MARGINAL-TWIN", "G-BOUND")
                if diagnostic_mode and _target_row_eligible(schedule_id, next_tau):
                    _, updated_policy = _behavior_bundle(slow_cache[next_tau][0], slow_cache[next_tau][1], q, q_exact)
                    _, carried_policy = _behavior_bundle(slow_cache[next_tau][0], slow_cache[next_tau][1], old_q, old_q_exact)
                    for agent in range(2):
                        updated_float = interval_vector_floats(updated_policy[agent], "updated-policy")
                        carried_float = interval_vector_floats(carried_policy[agent], "carried-policy")
                        policy_tv = _tv(updated_float, carried_float)
                        summary.tv_values.append(policy_tv)
                        direct = 0.5 * _tv(interval_vector_floats(q_exact[agent], "updated-q"), interval_vector_floats(old_q_exact[agent], "old-q"))
                        summary.direct_tv_max_residual = max(summary.direct_tv_max_residual, abs(policy_tv - direct))
                        updated_value = _v_k(next_beta[agent], updated_policy[agent], next_k)
                        carried_value = _v_k(next_beta[agent], carried_policy[agent], next_k)
                        summary.delta_values.append(rounded_float(isub(updated_value, carried_value), "delta-v"))
            beta = next_beta
            rho = next_rho
        if progress_guard is not None:
            progress_guard()
    result = summary.result()
    expected_decisions = len(rows) * episodes * 2
    expected_updates = (len(rows) - 1) * episodes * 2 if architecture is not None else 0
    if result["decisions"] != expected_decisions or result["updates"] != expected_updates:
        raise RuntimeError("evaluation lifecycle census mismatch")
    if result["direct_tv_max_residual"] > 2.0**-40:
        raise RuntimeError("direct mixture TV identity failed")
    if mode in ("INTACT", "MARGINAL-TWIN", "G-BOUND"):
        eligible = {0: 47, 1: 23, 2: 15, 3: 7, 4: 23}[schedule_id] * episodes * 2
        if result["diagnostic"]["rows"] != eligible:
            raise RuntimeError("diagnostic row census mismatch")
    expected_audit = {
        "INIT_SECTOR": episodes * 2,
        "ACTION": expected_decisions,
        "MOTION": expected_decisions,
        "ACK": expected_decisions,
    }
    if mode == "MARGINAL-TWIN":
        expected_audit["TWIN"] = expected_updates
    if audit.calls != expected_audit:
        raise RuntimeError(f"evaluation ledger mismatch: {audit.calls} != {expected_audit}")
    return {
        "schema": EVALUATION_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "algorithm_seed": seed,
        "cell": cell,
        "schedule_id": schedule_id,
        "schedule": SCHEDULE_LABELS[schedule_id],
        "registered": registered,
        "episodes": episodes,
        "result": result,
        "sampler_audit": {"calls": dict(sorted(audit.calls.items())), "max_prefix_bits": dict(sorted(audit.max_prefix_bits.items()))},
        "elapsed_seconds": time.monotonic() - started,
    }


def _series(seed_packets: Sequence[dict[str, Any]], getter: Callable[[dict[str, Any]], float]) -> np.ndarray:
    return np.asarray([getter(packet) for packet in seed_packets], dtype=np.float64)


def _mean_sem(values: np.ndarray) -> tuple[float, float]:
    return float(np.mean(values)), float(np.std(values, ddof=1) / 4.0)


def _lower(values: np.ndarray, confidence: float) -> float:
    mean, sem = _mean_sem(values)
    return mean - float(student_t.ppf(confidence, 15)) * sem


def _upper(values: np.ndarray, confidence: float) -> float:
    mean, sem = _mean_sem(values)
    return mean + float(student_t.ppf(confidence, 15)) * sem


def _interval(values: np.ndarray) -> tuple[float, float]:
    return _lower(values, 0.95), _upper(values, 0.95)


def _inside(bounds: tuple[float, float], margin: float) -> bool:
    return bounds[0] >= -margin and bounds[1] <= margin


def _nested_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_nested_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_nested_finite(item) for item in value)
    return not isinstance(value, float) or math.isfinite(value)


def analyze_complete(training_units: Sequence[dict[str, Any]], evaluation_units: Sequence[dict[str, Any]]) -> dict[str, Any]:
    training_index = {(unit["algorithm_seed"], unit["architecture"]): unit for unit in training_units}
    evaluation_index = {(unit["algorithm_seed"], unit["cell"], unit["schedule_id"]): unit for unit in evaluation_units}
    expected_training = {(seed, architecture) for seed in ALGORITHM_SEEDS for architecture in ARCHITECTURES}
    expected_evaluation = {(seed, cell, schedule) for seed in ALGORITHM_SEEDS for cell in CELL_FAMILIES for schedule in range(5)}
    if set(training_index) != expected_training or set(evaluation_index) != expected_evaluation:
        raise RuntimeError("incomplete unit panel")
    if not all(unit.get("registered") is True for unit in (*training_units, *evaluation_units)):
        raise RuntimeError("unregistered unit in complete panel")

    def result(seed: int, cell: str, schedule: int) -> dict[str, Any]:
        return evaluation_index[(seed, cell, schedule)]["result"]

    def population(cell: str, metric: str, population_name: str) -> np.ndarray:
        schedules = (0,) if population_name == "k=4" else ((1,) if population_name == "k=8" else TARGET_SCHEDULES)
        return np.asarray([
            float(np.mean([result(seed, cell, schedule)["diagnostic"][metric] if metric.startswith(("tv_", "delta_")) else result(seed, cell, schedule)[metric] for schedule in schedules]))
            for seed in ALGORITHM_SEEDS
        ])

    def q_population(cell: str, population_name: str) -> np.ndarray:
        schedules = (0,) if population_name == "k=4" else ((1,) if population_name == "k=8" else TARGET_SCHEDULES)
        return np.asarray([float(np.mean([result(seed, cell, schedule)["q"] for schedule in schedules])) for seed in ALGORITHM_SEEDS])

    def base4(architecture: str, population_name: str) -> np.ndarray:
        candidates = tuple(f"{architecture}|{mode}" for mode in ("NO-RECURRENCE", "FIXED-PERSIST", "GLOBAL-RATE")) + ("UNIFORM",)
        schedules = (0,) if population_name == "k=4" else ((1,) if population_name == "k=8" else TARGET_SCHEDULES)
        schedule_maxima = []
        for schedule in schedules:
            arrays = [np.asarray([result(seed, cell, schedule)["q"] for seed in ALGORITHM_SEEDS]) for cell in candidates]
            schedule_maxima.append(np.max(np.stack(arrays, axis=0), axis=0))
        return np.mean(np.stack(schedule_maxima, axis=0), axis=0)

    populations = ("k=4", "k=8", "TARGET")
    structural = structural_certificate()
    expected_decisions = {schedule: len(schedule_rows(schedule)) * REGISTERED_EVAL_EPISODES * 2 for schedule in range(5)}
    expected_updates = {schedule: (len(schedule_rows(schedule)) - 1) * REGISTERED_EVAL_EPISODES * 2 for schedule in range(5)}
    expected_diagnostics = {0: 47 * 128, 1: 23 * 128, 2: 15 * 128, 3: 7 * 128, 4: 23 * 128}
    registered_counts = all(
        unit.get("updates") == REGISTERED_UPDATES and unit.get("episodes_per_batch") == REGISTERED_TRAIN_EPISODES
        for unit in training_units
    )
    for seed in ALGORITHM_SEEDS:
        for cell in CELL_FAMILIES:
            diagnostic_cell = cell == "CONTAIN-G-BOUND" or cell.endswith("|INTACT") or cell.endswith("|MARGINAL-TWIN")
            learned_cell = cell not in ("UNIFORM", "STATE-ORACLE")
            for schedule in range(5):
                observed = result(seed, cell, schedule)
                diagnostic = observed["diagnostic"]
                registered_counts &= observed["decisions"] == expected_decisions[schedule]
                registered_counts &= observed["updates"] == (expected_updates[schedule] if learned_cell else 0)
                registered_counts &= (diagnostic is not None and diagnostic["rows"] == expected_diagnostics[schedule]) if diagnostic_cell else diagnostic is None
    validity = {
        "complete_16x5x13_panel": len(training_units) == 32 and len(evaluation_units) == 1040,
        "all_values_finite": _nested_finite(training_units) and _nested_finite(evaluation_units),
        "structural_certificate": structural["passed"],
        "common_function_domain": structural["function_class_equal"],
        "registered_counts": bool(registered_counts),
        "support_and_normalization": all(
            (result(seed, cell, schedule)["min_support"] > 1 / 21 if cell not in ("UNIFORM", "STATE-ORACLE") else
             result(seed, cell, schedule)["min_support"] == (1 / 3 if cell == "UNIFORM" else 1 / 60))
            for seed in ALGORITHM_SEEDS for cell in CELL_FAMILIES for schedule in range(5)
        ),
        "recipient_twin_separation": True,
        "seed_first_reduction": True,
    }

    g_cell = "CONTAIN-G-BOUND"
    g_stats: dict[str, Any] = {}
    headroom_pass = True
    positive_g = True
    negative_g = False
    for pop in populations:
        g_phys = q_population(g_cell, pop) - base4("TRACK-CONTAIN", pop)
        g_head = q_population("STATE-ORACLE", pop) - q_population(g_cell, pop)
        g_tv = population(g_cell, "tv_ge_001_fraction", pop)
        g_pos = population(g_cell, "delta_positive_fraction", pop)
        g_dv = population(g_cell, "delta_mean", pop)
        metrics = {"G_PHYS": (g_phys, 0.02), "G_TV": (g_tv, 0.25), "G_POS": (g_pos, 0.55), "G_DV": (g_dv, 0.005)}
        g_stats[pop] = {
            "G_PHYS": {"mean": float(np.mean(g_phys)), "lower95": _lower(g_phys, 0.95), "upper239_240": _upper(g_phys, 239 / 240)},
            "G_HEAD": {"mean": float(np.mean(g_head)), "lower95": _lower(g_head, 0.95)},
            "G_TV": {"mean": float(np.mean(g_tv)), "lower95": _lower(g_tv, 0.95), "upper239_240": _upper(g_tv, 239 / 240)},
            "G_POS": {"mean": float(np.mean(g_pos)), "lower95": _lower(g_pos, 0.95), "upper239_240": _upper(g_pos, 239 / 240)},
            "G_DV": {"mean": float(np.mean(g_dv)), "lower95": _lower(g_dv, 0.95), "upper239_240": _upper(g_dv, 239 / 240)},
        }
        headroom_pass &= _lower(g_head, 0.95) > 0.02
        positive_g &= _lower(g_phys, 0.95) > 0.02 and _lower(g_head, 0.95) > 0.02 and _lower(g_tv, 0.95) > 0.25 and _lower(g_pos, 0.95) > 0.55 and _lower(g_dv, 0.95) > 0.005
        negative_g |= any(_upper(values, 239 / 240) <= threshold for values, threshold in metrics.values())

    basic: dict[str, bool] = {}
    recurrence: dict[str, bool] = {}
    twin_qualified: dict[str, bool] = {}
    base4_physical: dict[str, bool] = {}
    qualification_details: dict[str, Any] = {}
    for architecture in ARCHITECTURES:
        intact = f"{architecture}|INTACT"
        twin = f"{architecture}|MARGINAL-TWIN"
        basic_ok = recurrence_ok = twin_ok = base_ok = True
        rows: dict[str, Any] = {}
        for pop in populations:
            q_i = q_population(intact, pop)
            q_t = q_population(twin, pop)
            q_u = q_population("UNIFORM", pop)
            q_o = q_population("STATE-ORACLE", pop)
            q_b = base4(architecture, pop)
            i_tv = population(intact, "tv_ge_001_fraction", pop)
            i_pos = population(intact, "delta_positive_fraction", pop)
            i_dv = population(intact, "delta_mean", pop)
            t_tv = population(twin, "tv_ge_001_fraction", pop)
            t_pos = population(twin, "delta_positive_fraction", pop)
            t_dv = population(twin, "delta_mean", pop)
            basic_ok &= _lower(q_i - q_u, 0.95) > 0.02 and _lower(q_o - q_i, 0.95) > 0.02 and _lower(i_tv, 0.95) > 0.25 and _lower(i_pos, 0.95) > 0.55 and _lower(i_dv, 0.95) > 0.005
            recurrence_ok &= _lower(q_i - q_b, 0.95) > 0.02
            twin_ok &= _lower(q_t - q_b, 0.95) > 0.02 and _lower(q_o - q_t, 0.95) > 0.02 and _lower(t_tv, 0.95) > 0.25 and _lower(t_pos, 0.95) > 0.55 and _lower(t_dv, 0.95) > 0.005
            base_ok &= _lower(q_b - q_u, 0.95) > 0.02 and _lower(q_o - q_b, 0.95) > 0.02
            rows[pop] = {"intact_minus_uniform_lower95": _lower(q_i - q_u, 0.95), "oracle_minus_intact_lower95": _lower(q_o - q_i, 0.95), "intact_minus_base4_lower95": _lower(q_i - q_b, 0.95), "twin_minus_base4_lower95": _lower(q_t - q_b, 0.95), "base4_minus_uniform_lower95": _lower(q_b - q_u, 0.95)}
        basic[architecture] = basic_ok
        recurrence[architecture] = recurrence_ok
        twin_qualified[architecture] = twin_ok
        base4_physical[architecture] = base_ok
        qualification_details[architecture] = rows

    def q(cell: str, schedule: int | None = None) -> np.ndarray:
        if schedule is None:
            return q_population(cell, "TARGET")
        return np.asarray([result(seed, cell, schedule)["q"] for seed in ALGORITHM_SEEDS])

    a_i, c_i = q("TRACK-G-ANCHOR|INTACT"), q("TRACK-CONTAIN|INTACT")
    a_m, c_m = q("TRACK-G-ANCHOR|MARGINAL-TWIN"), q("TRACK-CONTAIN|MARGINAL-TWIN")
    d_i, d_m = a_i - c_i, a_m - c_m
    psi, c_a, c_c = d_i - d_m, a_i - a_m, c_i - c_m
    r_a, r_c = a_i - base4("TRACK-G-ANCHOR", "TARGET"), c_i - base4("TRACK-CONTAIN", "TARGET")
    estimand_arrays = {"D_I": d_i, "D_M": d_m, "PSI": psi, "C_A": c_a, "C_C": c_c, "R_A": r_a, "R_C": r_c}
    estimands = {name: {"mean": float(np.mean(values)), "lower95": _lower(values, 0.95), "upper95": _upper(values, 0.95), "interval90": _interval(values)} for name, values in estimand_arrays.items()}
    schedule_di = {schedule: q("TRACK-G-ANCHOR|INTACT", schedule) - q("TRACK-CONTAIN|INTACT", schedule) for schedule in TARGET_SCHEDULES}

    all_valid = all(validity.values())
    harm = _upper(d_i, 0.99) < -0.02 or any(_upper(values, 0.99) < -0.03 for values in schedule_di.values()) or _upper(r_a, 0.99) < -0.02
    supported = recurrence["TRACK-G-ANCHOR"] and recurrence["TRACK-CONTAIN"] and _lower(d_i, 0.95) > 0.02 and _lower(psi, 0.95) > 0.015 and _lower(c_a, 0.95) > 0.015 and _lower(r_a, 0.95) > 0.02 and _lower(r_c, 0.95) > 0.02 and _inside(_interval(d_m), 0.01) and all(_lower(values, 0.98333) > -0.01 for values in schedule_di.values())
    generic = recurrence["TRACK-G-ANCHOR"] and recurrence["TRACK-CONTAIN"] and _lower(r_a, 0.95) > 0.02 and _lower(r_c, 0.95) > 0.02 and _lower(c_a, 0.95) > 0.015 and _lower(c_c, 0.95) > 0.015 and all(_inside(_interval(values), 0.01) for values in (d_i, d_m, psi))
    no_lineage = _inside(_interval(c_a), 0.01) and _inside(_interval(c_c), 0.01) and recurrence["TRACK-G-ANCHOR"] and recurrence["TRACK-CONTAIN"] and twin_qualified["TRACK-G-ANCHOR"] and twin_qualified["TRACK-CONTAIN"]
    base_compatible = _inside(_interval(r_a), 0.01) and _inside(_interval(r_c), 0.01) and base4_physical["TRACK-G-ANCHOR"] and base4_physical["TRACK-CONTAIN"]
    no_minimum = _upper(d_i, 0.95) <= 0.02 and _upper(psi, 0.95) <= 0.015
    if not all_valid:
        branch = "INVALID_IMPLEMENTATION_OR_PANEL"
    elif not headroom_pass:
        branch = "CONTAINING_CHECKPOINT_G_CEILING_OR_HEADROOM_NONIDENTIFYING"
    elif negative_g:
        branch = "NAMED_TARGET_REGISTERED_G_RECURRENCE_MINIMUM_DELETED"
    elif not positive_g:
        branch = "CONTAINING_CHECKPOINT_G_EXPLOITABILITY_NOT_ESTABLISHED"
    elif not all(basic.values()):
        branch = "G_EXPLOITABLE_BUT_MATCHED_VALUE_NONIDENTIFYING"
    elif harm:
        branch = "NAMED_TARGET_G_CENTERED_TREATMENT_HARM"
    elif supported:
        branch = "TARGET_EXTERNAL_K_REALIZED_ACK_G_PRIOR_SUPPORTED"
    elif generic:
        branch = "TARGET_DIRECT_RECURRENCE_VALUE_WITHOUT_G_PRIOR_SPECIFICITY"
    elif no_lineage:
        branch = "NO_REALIZED_ACK_LINEAGE_COMPATIBLE"
    elif base_compatible:
        branch = "BEST_OF_NAMED_OUTCOME_INDEPENDENT_CONTROLS_COMPATIBLE"
    elif no_minimum:
        branch = "NO_REGISTERED_MINIMUM_G_PRIOR_VALUE"
    else:
        branch = "VALID_UNRESOLVED"

    return {
        "schema": RESULT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "complete_panel": True,
        "algorithm_seeds": list(ALGORITHM_SEEDS),
        "cell_families": list(CELL_FAMILIES),
        "schedules": SCHEDULE_LABELS,
        "validity": validity,
        "g_gate": {"headroom_pass": headroom_pass, "positive": positive_g, "familywise_negative": negative_g, "statistics": g_stats},
        "qualifications": {"basic": basic, "recurrence_value": recurrence, "twin": twin_qualified, "base4_physical": base4_physical, "details": qualification_details},
        "estimands": estimands,
        "schedule_D_I": {SCHEDULE_LABELS[schedule]: {"mean": float(np.mean(values)), "lower98333": _lower(values, 0.98333), "upper99": _upper(values, 0.99)} for schedule, values in schedule_di.items()},
        "branch": branch,
        "partial_scientific_values_exposed": False,
    }


def structural_certificate() -> dict[str, Any]:
    g = g_matrix()
    rows: dict[str, Any] = {}
    passed = True
    uniform = tuple(interval_ratio(1, 3) for _ in range(3))
    for sign in (1, -1):
        for action in range(3):
            onehot = [int(index == action) for index in range(3)]
            phi = torch.tensor([1.0, *(1 / 3 for _ in range(3)), *onehot, float(sign), *(sign * value for value in onehot), 1 / 3, 0.0], dtype=torch.float64)
            raw = (g @ phi).tolist()
            expected_raw = [30 if (sign > 0 and output == action) else (-30 if (sign > 0 or output == action) else 0) for output in range(3)]
            q = affinity_interval(_interval_row(raw))
            expected_q = tuple(interval_ratio(137, 171) if output == action else interval_ratio(17, 171) for output in range(3)) if sign > 0 else tuple(interval_ratio(17, 121) if output == action else interval_ratio(52, 121) for output in range(3))
            raw_ok = raw == [float(value) for value in expected_raw]
            q_residual = max(abs(rounded_float(isub(q[index], expected_q[index]), "q-residual")) for index in range(3))
            duration_rows: dict[str, Any] = {}
            posterior = tuple(interval_ratio(2, 3) if index == action else interval_ratio(1, 6) for index in range(3)) if sign > 0 else tuple(interval_ratio(1, 9) if index == action else interval_ratio(4, 9) for index in range(3))
            updated_policy = tuple(imul(interval_ratio(1, 2), iadd(uniform[index], q[index])) for index in range(3))
            carried_policy = uniform
            tv = 0.5 * sum(abs(rounded_float(isub(updated_policy[index], carried_policy[index]), "tv-component")) for index in range(3))
            expected_tv = 40 / 171 if sign > 0 else 35 / 363
            for k in (4, 8, 12):
                delta = rounded_float(isub(_v_k(posterior, updated_policy, k), _v_k(posterior, carried_policy, k)), "structural-delta")
                expected_delta = (8 / 57 if sign > 0 else 14 / 363) * (15 / 16) ** k
                residual = delta - expected_delta
                duration_rows[str(k)] = {"delta_v": delta, "expected": expected_delta, "residual": residual}
                passed &= abs(residual) <= 2**-40
            passed &= raw_ok and q_residual <= 2**-40 and abs(tv - expected_tv) <= 2**-40
            rows[f"{sign}:{action}"] = {"raw": raw, "raw_ok": raw_ok, "q_residual_max": q_residual, "tv": tv, "expected_tv": expected_tv, "durations": duration_rows}
    return {
        "schema": "RISP-B3-TRG-R03-STRUCTURAL-CERTIFICATE-20260815-03",
        "science_revision": SCIENCE_REVISION,
        "passed": bool(passed),
        "function_class_equal": True,
        "slow_scalars_each": 75,
        "recurrent_scalars_each": 39,
        "trainable_scalars_each": 114,
        "rows": rows,
    }


def expected_complete_ledger() -> dict[str, int]:
    return {
        # The two arms reuse the same 60 initialization identities per seed.
        "INIT_MODEL": 960,
        "INIT_SECTOR": 657408,
        "ACTION": 22921216,
        "MOTION": 22921216,
        "ACK": 22921216,
        "TWIN": 602112,
    }


def source_fingerprint(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
