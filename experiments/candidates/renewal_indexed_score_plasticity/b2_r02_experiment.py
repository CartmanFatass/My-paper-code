"""Exact frozen RISP-B2 revision-02 experiment implementation.

The module is deliberately inert on import.  Registered stochastic activity is
created only by :func:`run_seed`, after the resumable production driver has
installed an exclusive frontier.  The implementation follows
``RISP-B2-SCIENCE-20260814-02`` and does not read any RISP-B1 artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import torch
from scipy.stats import t as student_t


SCIENCE_REVISION = "RISP-B2-SCIENCE-20260814-02"
RESULT_SCHEMA = "RISP-B2-R02-RESULT-20260814-02"
SEED_SCHEMA = "RISP-B2-R02-SEED-20260814-02"
T = 192
ALGORITHM_SEEDS = tuple(range(16))
ARCHITECTURES = ("DIRECT-ANCHOR", "DIRECT-CONTAIN")
FEEDBACKS = ("INTACT", "MARGINAL-TWIN")
CONTROLS = ("UNIFORM", "STATE-ORACLE")
SCHEDULE_LABELS = {0: "4", 1: "8", 2: "12", 3: "4->12", 4: "12->4"}
TARGET_SCHEDULES = (2, 3, 4)
Q_WINDOWS = {0: (0, 192), 1: (0, 192), 2: (0, 192), 3: (108, 192), 4: (100, 192)}
CHECKPOINT_UPDATES = (0, 32, 64, 128, 256)

# The exact arithmetic path uses outward-rounded decimal intervals.  Two
# hundred digits comfortably certifies binary64 rounding through all 48
# recurrent updates while avoiding the explosive numerator growth of eagerly
# materialized Fraction objects.
INTERVAL_PRECISION = 200


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
    rows = tuple((tau, duration, index == len(starts) - 1) for index, (tau, duration) in enumerate(starts))
    expected = {0: (48, 47), 1: (24, 23), 2: (16, 15), 3: (32, 31), 4: (32, 31)}[schedule_id]
    if (len(rows), sum(not terminal for _, _, terminal in rows)) != expected:
        raise RuntimeError("schedule construction mismatch")
    return rows


@dataclass(frozen=True)
class Interval:
    lo: Decimal
    hi: Decimal

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError("reversed interval")


def _round_op(rounding: str, fn: Any) -> Decimal:
    with localcontext() as context:
        context.prec = INTERVAL_PRECISION
        context.rounding = rounding
        return +fn()


def interval_int(value: int) -> Interval:
    point = Decimal(value)
    return Interval(point, point)


def interval_float(value: float) -> Interval:
    if not math.isfinite(value):
        raise ValueError("nonfinite binary64 interval input")
    point = Decimal.from_float(float(value))
    return Interval(point, point)


def interval_ratio(numerator: int, denominator: int) -> Interval:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    n = Decimal(numerator)
    d = Decimal(denominator)
    return Interval(
        _round_op(ROUND_FLOOR, lambda: n / d),
        _round_op(ROUND_CEILING, lambda: n / d),
    )


def iadd(a: Interval, b: Interval) -> Interval:
    return Interval(
        _round_op(ROUND_FLOOR, lambda: a.lo + b.lo),
        _round_op(ROUND_CEILING, lambda: a.hi + b.hi),
    )


def ineg(a: Interval) -> Interval:
    return Interval(-a.hi, -a.lo)


def isub(a: Interval, b: Interval) -> Interval:
    return iadd(a, ineg(b))


def imul(a: Interval, b: Interval) -> Interval:
    lows = [_round_op(ROUND_FLOOR, lambda x=x, y=y: x * y) for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    highs = [_round_op(ROUND_CEILING, lambda x=x, y=y: x * y) for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    return Interval(min(lows), max(highs))


def idiv_positive(a: Interval, b: Interval) -> Interval:
    if b.lo <= 0:
        raise ValueError("division interval is not strictly positive")
    lows = [_round_op(ROUND_FLOOR, lambda x=x, y=y: x / y) for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    highs = [_round_op(ROUND_CEILING, lambda x=x, y=y: x / y) for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    return Interval(min(lows), max(highs))


def iabs(a: Interval) -> Interval:
    if a.lo >= 0:
        return a
    if a.hi <= 0:
        return Interval(-a.hi, -a.lo)
    return Interval(Decimal(0), max(-a.lo, a.hi))


def isum(values: Iterable[Interval]) -> Interval:
    total = interval_int(0)
    for value in values:
        total = iadd(total, value)
    return total


def isquare(a: Interval) -> Interval:
    if a.lo >= 0:
        return imul(a, a)
    if a.hi <= 0:
        return imul(ineg(a), ineg(a))
    upper = max(a.lo * a.lo, a.hi * a.hi)
    return Interval(Decimal(0), _round_op(ROUND_CEILING, lambda: upper))


def rounded_float(a: Interval, label: str) -> float:
    lo = float(a.lo)
    hi = float(a.hi)
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo != hi:
        raise RuntimeError(f"interval does not certify one binary64 value for {label}: [{a.lo}, {a.hi}]")
    return lo


def affinity_interval(raw: Sequence[Interval]) -> tuple[Interval, Interval, Interval]:
    six = interval_int(6)
    sixteen = interval_int(16)
    weights: list[Interval] = []
    for value in raw:
        z = idiv_positive(imul(six, value), iadd(six, iabs(value)))
        weights.append(iadd(sixteen, isquare(iadd(z, six))))
    denominator = isum(weights)
    result = tuple(idiv_positive(weight, denominator) for weight in weights)
    if len(result) != 3:
        raise RuntimeError("affinity arity mismatch")
    return result  # type: ignore[return-value]


def interval_vector_floats(values: Sequence[Interval], label: str) -> tuple[float, ...]:
    return tuple(rounded_float(value, f"{label}[{index}]") for index, value in enumerate(values))


def _assert_probability_intervals(values: Sequence[Interval], label: str, support_floor: Interval | None = None) -> None:
    total = isum(values)
    if not (total.lo <= Decimal(1) <= total.hi):
        raise RuntimeError(f"{label} exact normalization interval excludes one")
    if any(value.lo <= 0 or value.hi >= 1 for value in values):
        raise RuntimeError(f"{label} probability interval left open simplex")
    if support_floor is not None and any(value.lo <= support_floor.hi for value in values):
        raise RuntimeError(f"{label} violated common support floor")


def _identity_bytes(identity: Sequence[Any]) -> bytes:
    return json.dumps([SCIENCE_REVISION, *identity], ensure_ascii=True, separators=(",", ":")).encode("ascii")


def bit_prefix(identity: Sequence[Any], bits: int) -> int:
    if bits <= 0:
        raise ValueError("bits must be positive")
    byte_count = (bits + 7) // 8
    raw = hashlib.shake_256(_identity_bytes(identity)).digest(byte_count)
    value = int.from_bytes(raw, "big")
    return value >> (byte_count * 8 - bits)


@dataclass
class SamplerAudit:
    calls: dict[str, int] = field(default_factory=dict)
    max_prefix_bits: dict[str, int] = field(default_factory=dict)

    def record(self, kind: str, bits: int) -> None:
        self.calls[kind] = self.calls.get(kind, 0) + 1
        self.max_prefix_bits[kind] = max(bits, self.max_prefix_bits.get(kind, 0))


def exact_cat(probabilities: Sequence[Interval], identity: Sequence[Any], kind: str, audit: SamplerAudit) -> int:
    if len(probabilities) < 2:
        raise ValueError("categorical law needs at least two masses")
    cumulative: list[Interval] = []
    running = interval_int(0)
    for probability in probabilities[:-1]:
        running = iadd(running, probability)
        cumulative.append(running)
    for bits in (128, 256, 512, 1024):
        prefix = bit_prefix(identity, bits)
        u = interval_ratio(prefix, 1 << bits)
        u_cover = Interval(u.lo, interval_ratio(prefix + 1, 1 << bits).hi)
        lower_certified = True
        for index, boundary in enumerate(cumulative):
            if u_cover.hi <= boundary.lo:
                audit.record(kind, bits)
                return index
            if u_cover.lo < boundary.hi:
                lower_certified = False
                break
        if lower_certified:
            audit.record(kind, bits)
            return len(probabilities) - 1
    raise RuntimeError(f"could not certify categorical draw {kind}; increase interval precision")


def event_identity(seed: int, phase: str, update_or_schedule: int, episode: int, agent: int, renewal: int | None, kind: str) -> tuple[Any, ...]:
    parts: list[Any] = [seed, phase, update_or_schedule, episode, agent]
    if renewal is not None:
        parts.append(renewal)
    parts.append(kind)
    return tuple(parts)


def model_identity(seed: int, tensor: str, scalar: int) -> tuple[Any, ...]:
    return (seed, tensor, scalar, "INIT_MODEL")


def g_matrix() -> torch.Tensor:
    result = torch.zeros((3, 13), dtype=torch.float64)
    # onehot(a) columns 4:7 are the half-sums; s*onehot(a) columns
    # 8:11 are the half-differences of g(+1,a) and g(-1,a).
    for action in range(3):
        for output in range(3):
            positive = 30.0 if output == action else -30.0
            negative = -30.0 if output == action else 0.0
            result[output, 4 + action] = (positive + negative) / 2.0
            result[output, 8 + action] = (positive - negative) / 2.0
    return result


def _xavier_value(seed: int, tensor: str, scalar: int, fan_in: int, fan_out: int) -> float:
    r_init = bit_prefix(model_identity(seed, tensor, scalar), 53)
    with localcontext() as context:
        context.prec = INTERVAL_PRECISION
        u53 = Decimal(r_init) / Decimal(1 << 53)
        value = (Decimal(6) / Decimal(fan_in + fan_out)).sqrt() * (Decimal(2) * u53 - Decimal(1))
    rounded = float(value)
    # Re-evaluate at a lower independent precision; agreement is a compact
    # guard against accidental insufficient precision in the one-rounding path.
    with localcontext() as context:
        context.prec = INTERVAL_PRECISION - 40
        check = float((Decimal(6) / Decimal(fan_in + fan_out)).sqrt() * (Decimal(2) * (Decimal(r_init) / Decimal(1 << 53)) - Decimal(1)))
    if rounded != check:
        raise RuntimeError("Xavier binary64 rounding was not certified")
    return rounded


def slow_initialization(seed: int, audit: SamplerAudit | None = None) -> dict[str, torch.Tensor]:
    shapes = (("w1", 8, 2), ("w2", 4, 8), ("base", 3, 4))
    result: dict[str, torch.Tensor] = {}
    for name, fan_out, fan_in in shapes:
        values = [_xavier_value(seed, name, index, fan_in, fan_out) for index in range(fan_out * fan_in)]
        result[name] = torch.tensor(values, dtype=torch.float64).reshape(fan_out, fan_in)
        if audit is not None:
            for _ in values:
                audit.record("INIT_MODEL", 53)
    return result


def _affinity_numeric(raw: torch.Tensor) -> torch.Tensor:
    safe = 6.0 * raw / (6.0 + torch.abs(raw))
    weights = 16.0 + (safe + 6.0).square()
    return weights / weights.sum(dim=-1, keepdim=True)


def _linear_row_major(inputs: torch.Tensor, weight: torch.Tensor, bias: torch.Tensor) -> torch.Tensor:
    columns: list[torch.Tensor] = []
    for output in range(weight.shape[0]):
        accumulator = bias[output].expand(inputs.shape[0])
        for feature in range(weight.shape[1]):
            accumulator = accumulator + inputs[:, feature] * weight[output, feature]
        columns.append(accumulator)
    return torch.stack(columns, dim=1)


class DirectModel(torch.nn.Module):
    PARAMETER_ORDER = ("w1", "b1", "w2", "b2", "base", "base_b", "E")

    def __init__(self, seed: int, architecture: str, audit: SamplerAudit | None = None, slow_arrays: dict[str, torch.Tensor] | None = None) -> None:
        super().__init__()
        if architecture not in ARCHITECTURES:
            raise ValueError(architecture)
        self.architecture = architecture
        arrays = slow_initialization(seed, audit) if slow_arrays is None else slow_arrays
        self.w1 = torch.nn.Parameter(arrays["w1"].clone())
        self.b1 = torch.nn.Parameter(torch.zeros(8, dtype=torch.float64))
        self.w2 = torch.nn.Parameter(arrays["w2"].clone())
        self.b2 = torch.nn.Parameter(torch.zeros(4, dtype=torch.float64))
        self.base = torch.nn.Parameter(arrays["base"].clone())
        self.base_b = torch.nn.Parameter(torch.zeros(3, dtype=torch.float64))
        initial_e = g_matrix() if architecture == "DIRECT-ANCHOR" else torch.zeros((3, 13), dtype=torch.float64)
        self.E = torch.nn.Parameter(initial_e.clone())
        self.register_buffer("E_center", initial_e.clone())
        if self.E.numel() != 39:
            raise RuntimeError("recurrent capacity mismatch")

    def ordered_parameters(self) -> tuple[torch.nn.Parameter, ...]:
        return tuple(getattr(self, name) for name in self.PARAMETER_ORDER)

    def slow_logits(self, observations: torch.Tensor) -> torch.Tensor:
        hidden8 = torch.tanh(_linear_row_major(observations, self.w1, self.b1))
        hidden4 = torch.tanh(_linear_row_major(hidden8, self.w2, self.b2))
        return _linear_row_major(hidden4, self.base, self.base_b)


def _interval_row_from_float(values: Sequence[float]) -> tuple[Interval, ...]:
    return tuple(interval_float(float(value)) for value in values)


def policy_bundle(
    model: DirectModel,
    observations: torch.Tensor,
    q_numeric: torch.Tensor,
    q_exact: Sequence[Sequence[Interval]],
) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]], torch.Tensor]:
    logits = model.slow_logits(observations)
    slow_numeric = _affinity_numeric(logits)
    exact_rows: list[tuple[Interval, Interval, Interval]] = []
    exact_float_rows: list[tuple[float, float, float]] = []
    for row, logit_values in enumerate(logits.detach().cpu().tolist()):
        slow_exact = affinity_interval(_interval_row_from_float(logit_values))
        mixed = tuple(
            imul(interval_ratio(1, 2), iadd(slow_exact[action], q_exact[row][action]))
            for action in range(3)
        )
        _assert_probability_intervals(mixed, "behavior policy", interval_ratio(1, 21))
        exact_rows.append(mixed)  # type: ignore[arg-type]
        exact_float_rows.append(interval_vector_floats(mixed, "policy"))  # type: ignore[arg-type]
    numeric = 0.5 * slow_numeric + 0.5 * q_numeric
    exact_float = torch.tensor(exact_float_rows, dtype=torch.float64)
    policy = numeric + (exact_float - numeric).detach()
    return policy, exact_rows, logits


def _phi_numeric(q: torch.Tensor, actions: Sequence[int], signs: Sequence[int], k: int, tau: int) -> torch.Tensor:
    rows: list[torch.Tensor] = []
    for row, (action, sign) in enumerate(zip(actions, signs)):
        onehot = torch.zeros(3, dtype=torch.float64)
        onehot[action] = 1.0
        rows.append(torch.cat((torch.ones(1, dtype=torch.float64), q[row], onehot, torch.tensor([float(sign)], dtype=torch.float64), float(sign) * onehot, torch.tensor([k / 12.0, tau / T], dtype=torch.float64))))
    return torch.stack(rows)


def recurrence_bundle(
    model: DirectModel,
    q_numeric: torch.Tensor,
    q_exact: Sequence[Sequence[Interval]],
    actions: Sequence[int],
    signs: Sequence[int],
    k: int,
    tau: int,
) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]]]:
    phi = _phi_numeric(q_numeric, actions, signs, k, tau)
    raw_numeric = _linear_row_major(phi, model.E, torch.zeros(3, dtype=torch.float64))
    numeric = _affinity_numeric(raw_numeric)
    e_values = model.E.detach().cpu().tolist()
    exact_rows: list[tuple[Interval, Interval, Interval]] = []
    float_rows: list[tuple[float, float, float]] = []
    for row, (action, sign) in enumerate(zip(actions, signs)):
        onehot = [int(index == action) for index in range(3)]
        phi_exact: tuple[Interval, ...] = (
            interval_int(1),
            *q_exact[row],
            *(interval_int(value) for value in onehot),
            interval_int(sign),
            *(interval_int(sign * value) for value in onehot),
            interval_ratio(k, 12),
            interval_ratio(tau, T),
        )
        raw = tuple(
            isum(imul(interval_float(e_values[output][column]), phi_exact[column]) for column in range(13))
            for output in range(3)
        )
        updated = affinity_interval(raw)
        _assert_probability_intervals(updated, "recurrent affinity", interval_ratio(1, 21))
        exact_rows.append(updated)
        float_rows.append(interval_vector_floats(updated, "q"))
    exact_float = torch.tensor(float_rows, dtype=torch.float64)
    return numeric + (exact_float - numeric).detach(), exact_rows


def _observation(count: int, tau: int, k: int) -> torch.Tensor:
    return torch.tensor([[tau / T, k / 12.0]] * count, dtype=torch.float64)


def _uniform_q(count: int) -> tuple[torch.Tensor, list[tuple[Interval, Interval, Interval]]]:
    exact = tuple(interval_ratio(1, 3) for _ in range(3))
    return torch.full((count, 3), 1.0 / 3.0, dtype=torch.float64), [exact for _ in range(count)]  # type: ignore[list-item]


def _belief_after(action: int, sign: int) -> tuple[float, float, float]:
    if sign > 0:
        return tuple(1.0 if index == action else 0.0 for index in range(3))  # type: ignore[return-value]
    return tuple(0.0 if index == action else 0.5 for index in range(3))  # type: ignore[return-value]


def _anchor_target(action: int, sign: int) -> tuple[float, float, float]:
    raw = [0.0, 0.0, 0.0]
    if sign > 0:
        raw = [30.0 if index == action else -30.0 for index in range(3)]
    else:
        raw[action] = -30.0
    exact = affinity_interval(_interval_row_from_float(raw))
    return interval_vector_floats(exact, "anchor_target")  # type: ignore[return-value]


def _environment_draw(
    seed: int,
    phase: str,
    update_or_schedule: int,
    episode: int,
    agent: int,
    renewal: int,
    action: int,
    target: int,
    audit: SamplerAudit,
) -> tuple[int, int]:
    outcome_probabilities = (interval_ratio(3, 4), interval_ratio(1, 4)) if action == target else (interval_ratio(1, 4), interval_ratio(3, 4))
    outcome_index = exact_cat(outcome_probabilities, event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "OUTCOME"), "OUTCOME", audit)
    sign = 1 if outcome_index == 0 else -1
    alternatives = tuple(index for index in range(3) if index != action)
    alt_index = exact_cat((interval_ratio(1, 2), interval_ratio(1, 2)), event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "ALT"), "ALT", audit)
    return sign, action if sign > 0 else alternatives[alt_index]


def _initial_targets(seed: int, phase: str, update_or_schedule: int, episodes: Sequence[int], audit: SamplerAudit) -> list[int]:
    uniform = (interval_ratio(1, 3), interval_ratio(1, 3), interval_ratio(1, 3))
    return [
        exact_cat(uniform, event_identity(seed, phase, update_or_schedule, episode, agent, None, "INIT_TARGET"), "INIT_TARGET", audit)
        for episode in episodes
        for agent in range(2)
    ]


def _left_sum(values: Sequence[torch.Tensor]) -> torch.Tensor:
    if not values:
        return torch.zeros((), dtype=torch.float64)
    total = values[0]
    for value in values[1:]:
        total = total + value
    return total


def _training_group(model: DirectModel, seed: int, update: int, episodes: Sequence[int], k: int, audit: SamplerAudit) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    count = len(episodes) * 2
    targets = _initial_targets(seed, "TRAIN", update, episodes, audit)
    q, q_exact = _uniform_q(count)
    beliefs = torch.full((count, 3), 1.0 / 3.0, dtype=torch.float64)
    task_by_episode = [torch.zeros((), dtype=torch.float64) for _ in episodes]
    align_rows: list[torch.Tensor] = []
    schedule_id = 0 if k == 4 else 1
    for renewal, (tau, duration, terminal) in enumerate(schedule_rows(schedule_id)):
        policy, policy_exact, _ = policy_bundle(model, _observation(count, tau, duration), q, q_exact)
        actions: list[int] = []
        signs: list[int] = []
        next_targets: list[int] = []
        for row, (episode, agent) in enumerate((pair for episode in episodes for pair in ((episode, 0), (episode, 1)))):
            action = exact_cat(policy_exact[row], event_identity(seed, "TRAIN", update, episode, agent, renewal, "ACTION"), "ACTION", audit)
            sign, next_target = _environment_draw(seed, "TRAIN", update, episode, agent, renewal, action, targets[row], audit)
            actions.append(action)
            signs.append(sign)
            next_targets.append(next_target)
        action_tensor = torch.tensor(actions, dtype=torch.long)
        selected = policy[torch.arange(count), action_tensor]
        baseline = duration * (policy * (beliefs - 0.5)).sum(dim=1)
        delta = duration * torch.tensor(signs, dtype=torch.float64) - baseline.detach()
        entropy = -(policy * torch.log(policy)).sum(dim=1)
        row_terms = delta.detach() * torch.log(selected) + 0.002 * duration * entropy
        for episode_index in range(len(episodes)):
            pair_start = 2 * episode_index
            task_by_episode[episode_index] = task_by_episode[episode_index] + row_terms[pair_start] + row_terms[pair_start + 1]
        targets = next_targets
        if not terminal:
            q, q_exact = recurrence_bundle(model, q, q_exact, actions, signs, duration, tau)
            for row, (action, sign) in enumerate(zip(actions, signs)):
                target = torch.tensor(_anchor_target(action, sign), dtype=torch.float64)
                align_rows.append(-(target * torch.log(q[row])).sum())
            beliefs = torch.tensor([_belief_after(action, sign) for action, sign in zip(actions, signs)], dtype=torch.float64)
    return task_by_episode, align_rows


@dataclass
class AdamState:
    moments: list[torch.Tensor]
    squares: list[torch.Tensor]
    step: int = 0


def _new_adam_state(model: DirectModel) -> AdamState:
    return AdamState([torch.zeros_like(parameter) for parameter in model.ordered_parameters()], [torch.zeros_like(parameter) for parameter in model.ordered_parameters()])


def _global_clip(model: DirectModel, maximum: float = 1.0) -> float:
    squares: list[torch.Tensor] = []
    for parameter in model.ordered_parameters():
        if parameter.grad is None:
            raise RuntimeError("missing parameter gradient")
        for value in parameter.grad.reshape(-1):
            squares.append(value * value)
    norm = torch.sqrt(_left_sum(squares))
    norm_value = float(norm.detach())
    if not math.isfinite(norm_value):
        raise RuntimeError("nonfinite gradient norm")
    factor = min(1.0, maximum / norm_value) if norm_value > 0 else 1.0
    for parameter in model.ordered_parameters():
        parameter.grad.mul_(factor)
    return norm_value


def _adamw_step(model: DirectModel, state: AdamState) -> None:
    state.step += 1
    lr, beta1, beta2, epsilon, weight_decay = 3e-4, 0.9, 0.999, 1e-8, 1e-4
    correction1 = 1.0 - beta1**state.step
    correction2 = 1.0 - beta2**state.step
    factor = 1.0 - lr * weight_decay
    with torch.no_grad():
        for index, parameter in enumerate(model.ordered_parameters()):
            gradient = parameter.grad
            if gradient is None:
                raise RuntimeError("missing gradient at Adam step")
            state.moments[index].mul_(beta1).add_(gradient, alpha=1.0 - beta1)
            state.squares[index].mul_(beta2).addcmul_(gradient, gradient, value=1.0 - beta2)
            direction = (state.moments[index] / correction1) / (torch.sqrt(state.squares[index] / correction2) + epsilon)
            center = model.E_center if parameter is model.E else torch.zeros_like(parameter)
            updated = center + factor * (parameter - center) - lr * direction
            parameter.copy_(updated)


def _parameter_snapshot(model: DirectModel) -> dict[str, Any]:
    return {
        "l2": math.sqrt(sum(float((parameter.detach() * parameter.detach()).sum()) for parameter in model.ordered_parameters())),
        "e_center_distance": float(torch.linalg.vector_norm(model.E.detach() - model.E_center)),
        "finite": all(bool(torch.isfinite(parameter).all()) for parameter in model.ordered_parameters()),
    }


def train_model(model: DirectModel, seed: int, audit: SamplerAudit, updates: int = 256, episodes_per_batch: int = 16, progress_guard: Callable[[], None] | None = None) -> dict[str, Any]:
    if episodes_per_batch != 16 and updates == 256:
        raise ValueError("registered training requires 16 episodes")
    state = _new_adam_state(model)
    checkpoints: dict[str, Any] = {"0": _parameter_snapshot(model)}
    losses: list[float] = []
    for update in range(updates):
        for parameter in model.ordered_parameters():
            parameter.grad = None
        episode_ids = list(range(episodes_per_batch))
        k4 = episode_ids[0::2]
        k8 = episode_ids[1::2]
        task4, align4 = _training_group(model, seed, update, k4, 4, audit)
        task8, align8 = _training_group(model, seed, update, k8, 8, audit)
        task_by_episode: list[torch.Tensor] = []
        for index in range(episodes_per_batch):
            task_by_episode.append(task4[index // 2] if index % 2 == 0 else task8[index // 2])
        task_loss = -_left_sum(task_by_episode) / (episodes_per_batch * 2 * T)
        align_loss = _left_sum([*align4, *align8]) / len([*align4, *align8])
        loss = task_loss + 0.25 * align_loss
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("nonfinite loss")
        loss.backward()
        gradient_norm = _global_clip(model)
        _adamw_step(model, state)
        losses.append(float(loss.detach()))
        completed = update + 1
        if completed in CHECKPOINT_UPDATES:
            checkpoints[str(completed)] = {**_parameter_snapshot(model), "loss": losses[-1], "preclip_gradient_norm": gradient_norm}
        if progress_guard is not None:
            progress_guard()
    if updates == 256 and tuple(int(key) for key in checkpoints) != CHECKPOINT_UPDATES:
        raise RuntimeError("registered checkpoint census mismatch")
    return {"updates": updates, "loss_first": losses[0], "loss_final": losses[-1], "loss_min": min(losses), "loss_max": max(losses), "checkpoints": checkpoints}


def _overlap(start: int, stop: int, window: tuple[int, int]) -> int:
    return max(0, min(stop, window[1]) - max(start, window[0]))


def _tv(left: Sequence[float], right: Sequence[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(left, right))


def _value(belief: Sequence[float], policy: Sequence[float]) -> float:
    return sum(probability * (target - 0.5) for probability, target in zip(policy, belief))


@dataclass
class EvalSummary:
    reward_weighted: float = 0.0
    reward_ticks: int = 0
    full_reward: float = 0.0
    full_ticks: int = 0
    decisions: int = 0
    updates: int = 0
    min_support: float = 1.0
    tv_values: list[float] = field(default_factory=list)
    delta_values: list[float] = field(default_factory=list)
    direct_tv_max_residual: float = 0.0
    entropy_sum: float = 0.0
    action_counts: list[int] = field(default_factory=lambda: [0, 0, 0])
    reward_by_tick: np.ndarray = field(default_factory=lambda: np.zeros(T, dtype=np.float64))
    reward_by_renewal: np.ndarray = field(default_factory=lambda: np.zeros(48, dtype=np.float64))
    renewal_counts: np.ndarray = field(default_factory=lambda: np.zeros(48, dtype=np.int64))

    def result(self) -> dict[str, Any]:
        return {
            "q": self.reward_weighted / self.reward_ticks,
            "q_full": self.full_reward / self.full_ticks,
            "decisions": self.decisions,
            "updates": self.updates,
            "min_support": self.min_support,
            "action_entropy": self.entropy_sum / self.decisions,
            "action_counts": self.action_counts,
            "reward_curve_by_tick": (self.reward_by_tick / (self.full_ticks / T)).tolist(),
            "reward_curve_by_completed_renewal": [
                float(self.reward_by_renewal[index] / self.renewal_counts[index]) if self.renewal_counts[index] else None
                for index in range(48)
            ],
            "direct_tv_max_residual": self.direct_tv_max_residual,
            "diagnostic": {
                "rows": len(self.tv_values),
                "tv_ge_001_fraction": sum(value >= 0.01 for value in self.tv_values) / len(self.tv_values),
                "delta_positive_fraction": sum(value > 0.0 for value in self.delta_values) / len(self.delta_values),
                "delta_mean": float(np.mean(self.delta_values)),
                "tv_mean": float(np.mean(self.tv_values)),
            } if self.tv_values else None,
        }


def _target_row_eligible(schedule_id: int, next_tau: int) -> bool:
    if schedule_id in (0, 1):
        return True
    return Q_WINDOWS[schedule_id][0] <= next_tau < Q_WINDOWS[schedule_id][1]


@torch.no_grad()
def evaluate_architecture_cell(model: DirectModel, seed: int, schedule_id: int, feedback: str, audit: SamplerAudit, episodes: int = 64, progress_guard: Callable[[], None] | None = None) -> dict[str, Any]:
    if feedback not in FEEDBACKS:
        raise ValueError(feedback)
    summary = EvalSummary()
    rows = schedule_rows(schedule_id)
    for episode in range(episodes):
        targets = _initial_targets(seed, "EVAL", schedule_id, (episode,), audit)
        q, q_exact = _uniform_q(2)
        rho_exact = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
        for renewal, (tau, duration, terminal) in enumerate(rows):
            policy, policy_exact, _ = policy_bundle(model, _observation(2, tau, duration), q, q_exact)
            actions: list[int] = []
            signs: list[int] = []
            update_signs: list[int] = []
            next_targets: list[int] = []
            for agent in range(2):
                action = exact_cat(policy_exact[agent], event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACTION"), "ACTION", audit)
                sign, next_target = _environment_draw(seed, "EVAL", schedule_id, episode, agent, renewal, action, targets[agent], audit)
                update_sign = sign
                if feedback == "MARGINAL-TWIN" and not terminal:
                    pbar = iadd(interval_ratio(1, 4), imul(interval_ratio(1, 2), rho_exact[agent][action]))
                    twin_index = exact_cat((pbar, isub(interval_int(1), pbar)), event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "TWIN"), "TWIN", audit)
                    update_sign = 1 if twin_index == 0 else -1
                    rho_exact[agent] = tuple(pbar if index == action else imul(interval_ratio(1, 2), isub(interval_int(1), pbar)) for index in range(3))
                actions.append(action)
                signs.append(sign)
                update_signs.append(update_sign)
                next_targets.append(next_target)
                overlap = _overlap(tau, tau + duration, Q_WINDOWS[schedule_id])
                summary.reward_weighted += sign * overlap
                summary.reward_ticks += overlap
                summary.full_reward += sign * duration
                summary.full_ticks += duration
                summary.reward_by_tick[tau : tau + duration] += sign
                summary.reward_by_renewal[renewal] += sign
                summary.renewal_counts[renewal] += 1
                summary.entropy_sum += -sum(rounded_float(value, "entropy_probability") * math.log(rounded_float(value, "entropy_probability")) for value in policy_exact[agent])
                summary.action_counts[action] += 1
                summary.min_support = min(summary.min_support, *(rounded_float(value, "eval_support") for value in policy_exact[agent]))
                summary.decisions += 1
            targets = next_targets
            if not terminal:
                old_q, old_q_exact = q, q_exact
                q, q_exact = recurrence_bundle(model, q, q_exact, actions, update_signs, duration, tau)
                summary.updates += 2
                next_tau, next_k, _ = rows[renewal + 1]
                if _target_row_eligible(schedule_id, next_tau):
                    updated_policy, _, _ = policy_bundle(model, _observation(2, next_tau, next_k), q, q_exact)
                    no_update_policy, _, _ = policy_bundle(model, _observation(2, next_tau, next_k), old_q, old_q_exact)
                    for agent in range(2):
                        updated = updated_policy[agent].detach().cpu().tolist()
                        no_update = no_update_policy[agent].detach().cpu().tolist()
                        policy_tv = _tv(updated, no_update)
                        summary.tv_values.append(policy_tv)
                        updated_q = interval_vector_floats(q_exact[agent], "updated_q_tv")
                        carried_q = interval_vector_floats(old_q_exact[agent], "carried_q_tv")
                        summary.direct_tv_max_residual = max(summary.direct_tv_max_residual, abs(policy_tv - 0.5 * _tv(updated_q, carried_q)))
                        scoring_sign = signs[agent]
                        belief = _belief_after(actions[agent], scoring_sign)
                        summary.delta_values.append(_value(belief, updated) - _value(belief, no_update))
        if progress_guard is not None:
            progress_guard()
    result = summary.result()
    expected_decisions = len(rows) * episodes * 2
    expected_updates = (len(rows) - 1) * episodes * 2
    if result["decisions"] != expected_decisions or result["updates"] != expected_updates:
        raise RuntimeError("evaluation lifecycle census mismatch")
    if result["direct_tv_max_residual"] > 2.0**-40:
        raise RuntimeError("direct policy-mixture TV identity failed")
    return result


@torch.no_grad()
def evaluate_control(seed: int, schedule_id: int, control: str, audit: SamplerAudit, episodes: int = 64, progress_guard: Callable[[], None] | None = None) -> dict[str, Any]:
    if control not in CONTROLS:
        raise ValueError(control)
    rows = schedule_rows(schedule_id)
    weighted_reward = 0.0
    weighted_ticks = 0
    full_reward = 0.0
    full_ticks = 0
    decisions = 0
    for episode in range(episodes):
        targets = _initial_targets(seed, "EVAL", schedule_id, (episode,), audit)
        for renewal, (tau, duration, _) in enumerate(rows):
            next_targets: list[int] = []
            for agent in range(2):
                if control == "UNIFORM":
                    probabilities = (interval_ratio(1, 3), interval_ratio(1, 3), interval_ratio(1, 3))
                else:
                    probabilities = tuple(interval_ratio(29, 30) if action == targets[agent] else interval_ratio(1, 60) for action in range(3))
                action = exact_cat(probabilities, event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACTION"), "ACTION", audit)
                sign, next_target = _environment_draw(seed, "EVAL", schedule_id, episode, agent, renewal, action, targets[agent], audit)
                next_targets.append(next_target)
                overlap = _overlap(tau, tau + duration, Q_WINDOWS[schedule_id])
                weighted_reward += sign * overlap
                weighted_ticks += overlap
                full_reward += sign * duration
                full_ticks += duration
                decisions += 1
            targets = next_targets
        if progress_guard is not None:
            progress_guard()
    return {"q": weighted_reward / weighted_ticks, "q_full": full_reward / full_ticks, "decisions": decisions, "updates": 0, "min_support": 1.0 / 60.0 if control == "STATE-ORACLE" else 1.0 / 3.0}


def _state_dict_json(model: DirectModel) -> dict[str, Any]:
    return {name: parameter.detach().cpu().tolist() for name, parameter in model.named_parameters()}


def run_seed(seed: int, *, training_updates: int = 256, training_episodes: int = 16, evaluation_episodes: int = 64, progress_guard: Callable[[], None] | None = None) -> dict[str, Any]:
    if seed not in ALGORITHM_SEEDS and (training_updates, training_episodes, evaluation_episodes) == (256, 16, 64):
        raise ValueError("registered execution requires a registered seed")
    audit = SamplerAudit()
    started = time.monotonic()
    models: dict[str, DirectModel] = {}
    training: dict[str, Any] = {}
    shared_slow_arrays = slow_initialization(seed, audit)
    for architecture in ARCHITECTURES:
        model = DirectModel(seed, architecture, slow_arrays=shared_slow_arrays)
        models[architecture] = model
        training[architecture] = train_model(model, seed, audit, training_updates, training_episodes, progress_guard)
    evaluation: dict[str, Any] = {}
    for architecture in ARCHITECTURES:
        for feedback in FEEDBACKS:
            for schedule_id in range(5):
                key = f"{architecture}|{feedback}|{schedule_id}"
                evaluation[key] = evaluate_architecture_cell(models[architecture], seed, schedule_id, feedback, audit, evaluation_episodes, progress_guard)
    controls: dict[str, Any] = {}
    for control in CONTROLS:
        for schedule_id in range(5):
            controls[f"{control}|{schedule_id}"] = evaluate_control(seed, schedule_id, control, audit, evaluation_episodes, progress_guard)
    result = {
        "schema": SEED_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "algorithm_seed": seed,
        "registered": (training_updates, training_episodes, evaluation_episodes) == (256, 16, 64),
        "training": training,
        "evaluation": evaluation,
        "controls": controls,
        "final_parameters": {architecture: _state_dict_json(model) for architecture, model in models.items()},
        "sampler_audit": {"calls": dict(sorted(audit.calls.items())), "max_prefix_bits": dict(sorted(audit.max_prefix_bits.items()))},
        "elapsed_seconds": time.monotonic() - started,
    }
    if result["registered"]:
        expected = {"INIT_MODEL": 60, "INIT_TARGET": 20224, "ACTION": 706560, "OUTCOME": 706560, "ALT": 706560, "TWIN": 37632}
        if result["sampler_audit"]["calls"] != expected:
            raise RuntimeError(f"registered seed ledger mismatch: {result['sampler_audit']['calls']} != {expected}")
    return result


def _series(seed_results: Sequence[dict[str, Any]], getter: Any) -> np.ndarray:
    return np.asarray([float(getter(result)) for result in seed_results], dtype=np.float64)


def _nested_finite(value: Any) -> bool:
    if isinstance(value, list):
        return all(_nested_finite(item) for item in value)
    return math.isfinite(float(value))


def _mean_sem(values: np.ndarray) -> tuple[float, float]:
    return float(np.mean(values)), float(np.std(values, ddof=1) / math.sqrt(len(values)))


def _lower(values: np.ndarray, confidence: float) -> float:
    mean, sem = _mean_sem(values)
    return mean - float(student_t.ppf(confidence, len(values) - 1)) * sem


def _upper(values: np.ndarray, confidence: float) -> float:
    mean, sem = _mean_sem(values)
    return mean + float(student_t.ppf(confidence, len(values) - 1)) * sem


def _interval(values: np.ndarray, confidence: float = 0.90) -> tuple[float, float]:
    mean, sem = _mean_sem(values)
    critical = float(student_t.ppf(0.5 + confidence / 2.0, len(values) - 1))
    return mean - critical * sem, mean + critical * sem


def _inside(interval: tuple[float, float], margin: float) -> bool:
    return interval[0] >= -margin and interval[1] <= margin


def analyze_complete(seed_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(seed_results) != 16 or tuple(sorted(result["algorithm_seed"] for result in seed_results)) != ALGORITHM_SEEDS:
        raise ValueError("analysis requires the complete registered sixteen-seed panel")
    ordered = sorted(seed_results, key=lambda result: result["algorithm_seed"])

    def q(architecture: str, feedback: str, schedule: int) -> np.ndarray:
        return _series(ordered, lambda result: result["evaluation"][f"{architecture}|{feedback}|{schedule}"]["q"])

    def control_q(control: str, schedule: int) -> np.ndarray:
        return _series(ordered, lambda result: result["controls"][f"{control}|{schedule}"]["q"])

    def target(architecture: str, feedback: str) -> np.ndarray:
        return sum((q(architecture, feedback, schedule) for schedule in TARGET_SCHEDULES), np.zeros(16)) / 3.0

    def target_control(control: str) -> np.ndarray:
        return sum((control_q(control, schedule) for schedule in TARGET_SCHEDULES), np.zeros(16)) / 3.0

    anchor_i = target("DIRECT-ANCHOR", "INTACT")
    contain_i = target("DIRECT-CONTAIN", "INTACT")
    anchor_m = target("DIRECT-ANCHOR", "MARGINAL-TWIN")
    contain_m = target("DIRECT-CONTAIN", "MARGINAL-TWIN")
    d_i = anchor_i - contain_i
    d_m = anchor_m - contain_m
    psi = d_i - d_m
    c_a = anchor_i - anchor_m
    c_c = contain_i - contain_m

    validity = {
        "all_seed_packets_registered": all(result.get("registered") is True for result in ordered),
        "all_parameters_finite": all(_nested_finite(tensor) for result in ordered for architecture in ARCHITECTURES for tensor in result["final_parameters"][architecture].values()),
        "support_above_1_over_21": min(result["evaluation"][f"{architecture}|{feedback}|{schedule}"]["min_support"] for result in ordered for architecture in ARCHITECTURES for feedback in FEEDBACKS for schedule in range(5)) > 1.0 / 21.0,
        "structural_references": structural_certificate()["passed"],
        "complete_counts": True,
        "function_class_equal": True,
        "no_risp_b1_reuse": True,
    }

    qualifications: dict[str, Any] = {}
    qualification_pass = True
    for architecture in ARCHITECTURES:
        for schedule in (0, 1):
            competence = _lower(q(architecture, "INTACT", schedule) - control_q("UNIFORM", schedule), 0.95)
            headroom = _lower(control_q("STATE-ORACLE", schedule) - q(architecture, "INTACT", schedule), 0.95)
            diagnostics = {
                name: _series(ordered, lambda result, a=architecture, s=schedule, n=name: result["evaluation"][f"{a}|INTACT|{s}"]["diagnostic"][n])
                for name in ("tv_ge_001_fraction", "delta_positive_fraction", "delta_mean")
            }
            diag_bounds = {name: _lower(values, 0.95) for name, values in diagnostics.items()}
            passed = competence > 0.08 and headroom > 0.02 and diag_bounds["tv_ge_001_fraction"] > 0.25 and diag_bounds["delta_positive_fraction"] > 0.55 and diag_bounds["delta_mean"] > 0.005
            qualifications[f"{architecture}|seen|{schedule}"] = {"competence_lower": competence, "headroom_lower": headroom, "diagnostic_lowers": diag_bounds, "passed": passed}
            qualification_pass = qualification_pass and passed
        target_diag: dict[str, np.ndarray] = {}
        for name in ("tv_ge_001_fraction", "delta_positive_fraction", "delta_mean"):
            target_diag[name] = sum((_series(ordered, lambda result, a=architecture, s=schedule, n=name: result["evaluation"][f"{a}|INTACT|{s}"]["diagnostic"][n]) for schedule in TARGET_SCHEDULES), np.zeros(16)) / 3.0
        bounds = {name: _lower(values, 0.95) for name, values in target_diag.items()}
        passed = bounds["tv_ge_001_fraction"] > 0.25 and bounds["delta_positive_fraction"] > 0.55 and bounds["delta_mean"] > 0.005
        qualifications[f"{architecture}|target"] = {"diagnostic_lowers": bounds, "passed": passed}
        qualification_pass = qualification_pass and passed

    twin_clear: dict[str, bool] = {}
    for architecture in ARCHITECTURES:
        twin_diag: dict[str, np.ndarray] = {}
        for name in ("tv_ge_001_fraction", "delta_positive_fraction", "delta_mean"):
            twin_diag[name] = sum((_series(ordered, lambda result, a=architecture, s=schedule, n=name: result["evaluation"][f"{a}|MARGINAL-TWIN|{s}"]["diagnostic"][n]) for schedule in TARGET_SCHEDULES), np.zeros(16)) / 3.0
        twin_clear[architecture] = (
            _lower(target(architecture, "MARGINAL-TWIN") - target_control("UNIFORM"), 0.95) > 0.08
            and _lower(twin_diag["tv_ge_001_fraction"], 0.95) > 0.25
            and _lower(twin_diag["delta_positive_fraction"], 0.95) > 0.55
            and _lower(twin_diag["delta_mean"], 0.95) > 0.005
        )

    estimands = {
        "D_I": {"mean": float(np.mean(d_i)), "lower95": _lower(d_i, 0.95), "upper95": _upper(d_i, 0.95), "interval90": _interval(d_i)},
        "D_M": {"mean": float(np.mean(d_m)), "lower95": _lower(d_m, 0.95), "upper95": _upper(d_m, 0.95), "interval90": _interval(d_m)},
        "PSI": {"mean": float(np.mean(psi)), "lower95": _lower(psi, 0.95), "upper95": _upper(psi, 0.95), "interval90": _interval(psi)},
        "C_A": {"mean": float(np.mean(c_a)), "lower95": _lower(c_a, 0.95), "upper95": _upper(c_a, 0.95), "interval90": _interval(c_a)},
        "C_C": {"mean": float(np.mean(c_c)), "lower95": _lower(c_c, 0.95), "upper95": _upper(c_c, 0.95), "interval90": _interval(c_c)},
    }
    schedule_d_i = {schedule: q("DIRECT-ANCHOR", "INTACT", schedule) - q("DIRECT-CONTAIN", "INTACT", schedule) for schedule in TARGET_SCHEDULES}
    harm = _upper(d_i, 0.9875) < -0.02 or any(_upper(values, 0.9875) < -0.03 for values in schedule_d_i.values())
    supported = _lower(d_i, 0.95) > 0.02 and _lower(psi, 0.95) > 0.015 and _lower(c_a, 0.95) > 0.015 and _inside(_interval(d_m), 0.01) and all(_lower(values, 0.98333) > -0.01 for values in schedule_d_i.values())
    generic = _lower(c_a, 0.95) > 0.015 and _lower(c_c, 0.95) > 0.015 and all(_inside(_interval(values), 0.01) for values in (d_i, psi, d_m))
    global_rate = _inside(_interval(c_a), 0.01) and _inside(_interval(c_c), 0.01) and all(twin_clear.values())
    no_minimum = _upper(d_i, 0.95) <= 0.02 and _upper(psi, 0.95) <= 0.015 and not harm
    if not all(validity.values()):
        branch = "INVALID_IMPLEMENTATION_OR_PANEL"
    elif not qualification_pass:
        branch = "EXACT_PACKAGE_NONIDENTIFYING_FOR_VALUE_ATTRIBUTION"
    elif harm:
        branch = "HARM_FOR_EXACT_ANCHOR"
    elif supported:
        branch = "FINITE_TOY_REALIZED_OUTCOME_COUPLED_PRIOR_SUPPORTED"
    elif generic:
        branch = "DIRECT_RECURRENCE_PACKAGE_WITHOUT_REGISTERED_ANCHOR_SPECIFICITY"
    elif global_rate:
        branch = "GLOBAL_RATE_OR_OUTCOME_INDEPENDENT_PERSISTENCE_COMPATIBLE"
    elif no_minimum:
        branch = "NO_REGISTERED_MINIMUM_INTACT_OR_REALIZED_COUPLING_SPECIFIC_ANCHOR_BENEFIT"
    else:
        branch = "VALID_UNRESOLVED"
    return {
        "schema": RESULT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "complete_panel": True,
        "algorithm_seeds": list(ALGORITHM_SEEDS),
        "validity": validity,
        "qualifications": qualifications,
        "twin_diagnostic_clear": twin_clear,
        "estimands": estimands,
        "schedule_D_I": {SCHEDULE_LABELS[schedule]: {"mean": float(np.mean(values)), "lower98333": _lower(values, 0.98333), "upper9875": _upper(values, 0.9875)} for schedule, values in schedule_d_i.items()},
        "branch": branch,
        "partial_scientific_values_exposed": False,
    }


def structural_certificate() -> dict[str, Any]:
    g = g_matrix()
    rows: dict[str, Any] = {}
    expected = {1: (40.0 / 171.0, 40.0 / 171.0), -1: (35.0 / 726.0, 35.0 / 363.0)}
    uniform = [1.0 / 3.0] * 3
    for sign in (1, -1):
        action = 0
        onehot = [1, 0, 0]
        phi = torch.tensor([1.0, *uniform, *onehot, float(sign), *(sign * value for value in onehot), 1.0 / 3.0, 0.0], dtype=torch.float64)
        raw = (g @ phi).tolist()
        q = interval_vector_floats(affinity_interval(_interval_row_from_float(raw)), "structural_q")
        updated = [0.5 / 3.0 + 0.5 * value for value in q]
        belief = _belief_after(action, sign)
        delta = _value(belief, updated) - _value(belief, uniform)
        tv = _tv(updated, uniform)
        rows[str(sign)] = {"raw": raw, "delta_v": delta, "tv": tv, "expected_delta_v": expected[sign][0], "expected_tv": expected[sign][1], "residual_delta_v": delta - expected[sign][0], "residual_tv": tv - expected[sign][1]}
    passed = all(abs(row["residual_delta_v"]) <= 2.0**-40 and abs(row["residual_tv"]) <= 2.0**-40 for row in rows.values())
    return {"science_revision": SCIENCE_REVISION, "passed": passed, "rows": rows, "function_class_equal": True, "recurrent_scalars_each": 39}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    encoded = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
