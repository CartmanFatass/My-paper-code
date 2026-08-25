"""Exact frozen RISP G-initialization reachability revision-01 experiment.

Importing this module is inert.  Its coordinate root begins unbound, and every
stochastic entry point fails closed until a caller binds one fresh 64-hex root
exactly once.  This module never reads an earlier RISP coordinate, state,
checkpoint, tape, seed, or result artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
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


SCIENCE_REVISION = "RISP-G-INIT-REACH-SCIENCE-20260821-01"
COORDINATE_SCHEMA = "RISP-G-INIT-REACH-R01-LAZY-SHAKE256-PREFIX-20260821-01"
RESULT_SCHEMA = "RISP-G-INIT-REACH-R01-RESULT-20260821-01"
TRAINING_SCHEMA = "RISP-G-INIT-REACH-R01-TRAINING-UNIT-20260821-01"
EVALUATION_SCHEMA = "RISP-G-INIT-REACH-R01-EVALUATION-UNIT-20260821-01"
STRUCTURAL_SCHEMA = "RISP-G-INIT-REACH-R01-STRUCTURAL-CERTIFICATE-20260821-01"
TEST_NAMESPACE_CLASS = "TEST_ONLY"
TEST_NAMESPACE = "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1"
TEST_COORDINATE_SCHEMA = "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1"
TEST_FIXTURE_REVISION = "RISP-G-INIT-REACH-TEST-FIXTURE-20260821-01"
TEST_TRAINING_SCHEMA = "RISP-G-INIT-REACH-TEST-TRAINING-UNIT-V1"
TEST_EVALUATION_SCHEMA = "RISP-G-INIT-REACH-TEST-EVALUATION-UNIT-V1"
TEST_RESULT_SCHEMA = "RISP-G-INIT-REACH-TEST-RESULT-V1"
TEST_STRUCTURAL_SCHEMA = "RISP-G-INIT-REACH-TEST-STRUCTURAL-CERTIFICATE-V1"
FORBIDDEN_PRODUCTION_ROOTS = frozenset(
    {
        "e2b7a0e30108dd261ee7612c3f79b9f21db21d8feb7c7c1fd356eaac5316e0c5",
        "e1578340aea90b521ee8be0ea75613bf349feed4617da4a776d0801eb02cd358",
        "9468480f3c1b2c8ca3cfb2dfcb6c8b7aa9b26bbc7ba0935574bcdf1e7bbbe2e3",
    }
)
T = 192
ALGORITHM_SEEDS = tuple(range(16))
ARMS = ("G-START/ZERO-CENTER", "ZERO-START/ZERO-CENTER")
CELL_FAMILIES = (
    "G-START/ZERO-CENTER-INTACT",
    "ZERO-START/ZERO-CENTER-INTACT",
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

_PRODUCTION_COORDINATE_ROOT: str | None = None
_TEST_FIXTURE_ROOT: str | None = None
_PRODUCTION_NATIVE_PREFLIGHT: dict[str, object] | None = None


def _validate_root_shape(root: str, field: str) -> None:
    if not isinstance(root, str) or len(root) != 64 or any(ch not in "0123456789abcdef" for ch in root):
        raise ValueError(f"{field} must be exactly 64 lowercase hexadecimal characters")


def configure_production_coordinate_root(root: str, *, validated_production_binding: bool) -> str:
    """Bind the sole root only after the production transaction is validated."""
    global _PRODUCTION_COORDINATE_ROOT
    if not validated_production_binding:
        raise RuntimeError("validated production binding is required")
    _validate_root_shape(root, "coordinate_root")
    if root in FORBIDDEN_PRODUCTION_ROOTS:
        raise RuntimeError("permanently excluded TEST-provenance root")
    if _TEST_FIXTURE_ROOT is not None:
        raise RuntimeError("a TEST-only fixture binding is already active")
    if _PRODUCTION_COORDINATE_ROOT is not None:
        raise RuntimeError("production coordinate root is already configured")
    _PRODUCTION_COORDINATE_ROOT = root
    return root


def coordinate_root() -> str | None:
    """Return only the production root; TEST fixture roots never appear here."""
    return _PRODUCTION_COORDINATE_ROOT


def configure_test_fixture_root(fixture_root: str) -> str:
    """Activate the permanent TEST-only stochastic certificate namespace."""
    global _TEST_FIXTURE_ROOT
    _validate_root_shape(fixture_root, "fixture_root")
    if fixture_root in FORBIDDEN_PRODUCTION_ROOTS:
        raise RuntimeError("permanently excluded TEST-provenance root")
    if _PRODUCTION_COORDINATE_ROOT is not None:
        raise RuntimeError("a production coordinate binding is already active")
    if _TEST_FIXTURE_ROOT is not None:
        raise RuntimeError("TEST-only fixture root is already configured")
    _TEST_FIXTURE_ROOT = fixture_root
    return fixture_root


def fixture_root() -> str | None:
    return _TEST_FIXTURE_ROOT


def _binding_kind() -> str | None:
    if _PRODUCTION_COORDINATE_ROOT is not None:
        return "PRODUCTION"
    if _TEST_FIXTURE_ROOT is not None:
        return "TEST_ONLY"
    return None


def _require_coordinate_binding() -> str:
    kind = _binding_kind()
    if kind is None:
        raise RuntimeError("stochastic coordinate binding is unbound")
    return kind


def _active_revision() -> str:
    return SCIENCE_REVISION if _require_coordinate_binding() == "PRODUCTION" else TEST_FIXTURE_REVISION


def _active_training_schema() -> str:
    return TRAINING_SCHEMA if _require_coordinate_binding() == "PRODUCTION" else TEST_TRAINING_SCHEMA


def _active_evaluation_schema() -> str:
    return EVALUATION_SCHEMA if _require_coordinate_binding() == "PRODUCTION" else TEST_EVALUATION_SCHEMA


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
    kind = _require_coordinate_binding()
    if kind == "PRODUCTION":
        payload: Any = [COORDINATE_SCHEMA, _PRODUCTION_COORDINATE_ROOT, SCIENCE_REVISION, *identity]
    else:
        payload = {
            "namespace_class": TEST_NAMESPACE_CLASS,
            "namespace": TEST_NAMESPACE,
            "coordinate_schema": TEST_COORDINATE_SCHEMA,
            "test_fixture_revision": TEST_FIXTURE_REVISION,
            "fixture_root": _TEST_FIXTURE_ROOT,
            "identity": list(identity),
        }
    return json.dumps(payload, ensure_ascii=True, sort_keys=kind == "TEST_ONLY", separators=(",", ":")).encode("ascii")


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


def _initial_slow_tensor_sha256(arrays: dict[str, torch.Tensor]) -> str:
    """Canonical digest of all 75 initial binary64 slow scalars."""
    tensors = {
        "w1": arrays["w1"],
        "b1": torch.zeros(8, dtype=torch.float64),
        "w2": arrays["w2"],
        "b2": torch.zeros(4, dtype=torch.float64),
        "w3": arrays["w3"],
        "b3": torch.zeros(3, dtype=torch.float64),
    }
    digest = hashlib.sha256()
    for name in ("w1", "b1", "w2", "b2", "w3", "b3"):
        value = tensors[name].detach().cpu().numpy().astype("<f8", copy=False)
        header = json.dumps([name, list(value.shape), "binary64-le"], separators=(",", ":")).encode("ascii")
        digest.update(len(header).to_bytes(4, "big"))
        digest.update(header)
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


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

    def __init__(self, seed: int, arm: str, *, slow_arrays: dict[str, torch.Tensor] | None = None) -> None:
        super().__init__()
        if arm not in ARMS:
            raise ValueError(arm)
        arrays = slow_initialization(seed) if slow_arrays is None else slow_arrays
        self.arm = arm
        self.w1 = torch.nn.Parameter(arrays["w1"].clone())
        self.b1 = torch.nn.Parameter(torch.zeros(8, dtype=torch.float64))
        self.w2 = torch.nn.Parameter(arrays["w2"].clone())
        self.b2 = torch.nn.Parameter(torch.zeros(4, dtype=torch.float64))
        self.w3 = torch.nn.Parameter(arrays["w3"].clone())
        self.b3 = torch.nn.Parameter(torch.zeros(3, dtype=torch.float64))
        initial_e = g_matrix() if arm == "G-START/ZERO-CENTER" else torch.zeros((3, 13), dtype=torch.float64)
        self.E = torch.nn.Parameter(initial_e.clone())
        # The sole intervention is E_0.  AdamW decay is zero-centered in both
        # arms and G is never reapplied or used as a center.
        self.register_buffer("E_center", torch.zeros((3, 13), dtype=torch.float64))
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


def _event_token(identity: Sequence[Any]) -> int:
    return int.from_bytes(hashlib.sha256(_identity_bytes(identity)).digest()[:8], "big")


def _ensure_production_native_preflight() -> None:
    global _PRODUCTION_NATIVE_PREFLIGHT
    if _binding_kind() != "PRODUCTION":
        return
    if _PRODUCTION_NATIVE_PREFLIGHT is None:
        import g_init_r01_native_backend as native

        # Evaluation uses width 32; training uses two deterministic width-16
        # schedule subgroups under the same accepted max-width contract.
        _PRODUCTION_NATIVE_PREFLIGHT = native.production_preflight(batch_width=32)


def _open_native_episode(
    sectors: Sequence[int], seed: int, phase: str, update_or_schedule: int,
    episode: int, schedule_id: int,
) -> Any | None:
    if _binding_kind() != "PRODUCTION":
        return None
    raise RuntimeError("per-episode production native sessions are forbidden; use grouped adapters")


def _native_authoritative_transition(
    host: Any | None, *, seed: int, phase: str, update_or_schedule: int,
    episode: int, renewal: int, tau: int, duration: int, terminal: bool,
    sectors: Sequence[int], actions: Sequence[int], materialized: Sequence[tuple[int, int]],
) -> tuple[list[int], list[int]]:
    next_sectors = [int(row[0]) for row in materialized]
    signs = [int(row[1]) for row in materialized]
    if host is None:
        return next_sectors, signs
    import g_init_r01_native_backend as native

    rows = tuple(
        native.MaterializedStep(
            action=int(actions[agent]),
            motion_prefix=bit_prefix(event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "MOTION"), 1024),
            ack_prefix=bit_prefix(event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "ACK"), 1024),
            action_event_token=_event_token(event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "ACTION")),
            motion_event_token=_event_token(event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "MOTION")),
            ack_event_token=_event_token(event_identity(seed, phase, update_or_schedule, episode, agent, renewal, "ACK")),
        )
        for agent in range(2)
    )
    outputs = host.step(rows)
    for agent, output in enumerate(outputs):
        expected = rows[agent]
        if (
            output["renewal"] != renewal or output["tau"] != tau or output["duration"] != duration
            or output["sector_before"] != sectors[agent] or output["sector_after"] != next_sectors[agent]
            or output["action"] != actions[agent] or output["ack_sign"] != signs[agent]
            or output["utility"] != duration * signs[agent] or output["terminal"] is not terminal
            or output["action_events_consumed"] != renewal + 1
            or output["motion_events_consumed"] != renewal + 1
            or output["ack_events_consumed"] != renewal + 1
            or output["action_event_token"] != expected.action_event_token
            or output["motion_event_token"] != expected.motion_event_token
            or output["ack_event_token"] != expected.ack_event_token
        ):
            raise RuntimeError("native environment transition or event identity mismatch")
    return [int(output["sector_after"]) for output in outputs], [int(output["ack_sign"]) for output in outputs]


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
    native_host = _open_native_episode(sectors, seed, "TRAIN", update, batch_position, schedule_id)
    q, q_exact = _uniform_q(2)
    beliefs = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
    task = [[], []]
    align = [[], []]
    try:
        for renewal, (tau, duration, terminal) in enumerate(schedule_rows(schedule_id)):
            slow_numeric, slow_exact = slow_cache[tau]
            policy, policy_exact = _behavior_bundle(slow_numeric, slow_exact, q, q_exact)
            actions = [
                exact_cat(policy_exact[agent], event_identity(seed, "TRAIN", update, batch_position, agent, renewal, "ACTION"), "ACTION", audit)
                for agent in range(2)
            ]
            materialized = [
                _environment_step(seed, "TRAIN", update, batch_position, agent, renewal, actions[agent], sectors[agent], duration, audit)
                for agent in range(2)
            ]
            next_sectors, signs = _native_authoritative_transition(
                native_host, seed=seed, phase="TRAIN", update_or_schedule=update,
                episode=batch_position, renewal=renewal, tau=tau, duration=duration,
                terminal=terminal, sectors=sectors, actions=actions, materialized=materialized,
            )
            next_beliefs: list[tuple[Interval, Interval, Interval]] = []
            for agent in range(2):
                mu = _matmul_belief(beliefs[agent], p_k(duration))
                ey = tuple(iadd(interval_ratio(-3, 5), imul(interval_ratio(6, 5), mu[a])) for a in range(3))
                baseline = imul(interval_int(duration), isum(imul(policy_exact[agent][a], ey[a]) for a in range(3)))
                delta = duration * signs[agent] - rounded_float(baseline, "training-baseline")
                selected = policy[agent, actions[agent]]
                entropy = -(policy[agent] * torch.log(policy[agent])).sum()
                task[agent].append(delta * torch.log(selected) + 0.002 * duration * entropy)
                next_beliefs.append(_posterior(mu, actions[agent], signs[agent]))
            sectors = next_sectors
            if not terminal:
                q, q_exact = _recurrence_bundle(model, q, q_exact, actions, signs, duration, tau)
                for agent in range(2):
                    target = torch.tensor(_anchor_target(actions[agent], signs[agent]), dtype=torch.float64)
                    align[agent].append(-(target * torch.log(q[agent])).sum())
                beliefs = next_beliefs
    finally:
        if native_host is not None:
            native_host.close()
    return task, align


def _train_episode_group_native(
    model: TrackModel, seed: int, update: int, positions: Sequence[int], schedule_id: int,
    slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]],
    audit: SamplerAudit,
) -> dict[int, tuple[list[list[torch.Tensor]], list[list[torch.Tensor]]]]:
    """Production adapter: eight episodes / sixteen agent lanes per native host."""
    import g_init_r01_native_backend as native

    states: dict[int, dict[str, Any]] = {}
    resets = []
    for position in positions:
        q, q_exact = _uniform_q(2)
        states[position] = {
            "sectors": [0, 0], "q": q, "q_exact": q_exact,
            "beliefs": [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)],
            "task": [[], []], "align": [[], []], "trace": [],
        }
        for agent in range(2):
            identity = event_identity(seed, "TRAIN", update, position, agent, None, "INIT_SECTOR")
            resets.append(native.MaterializedReset(
                schedule_id, bit_prefix(identity, 1024), _event_token(identity),
            ))
    with native.NativeInteractiveBatch(resets) as host:
        for lane, output in enumerate(host.initial):
            position, agent = positions[lane // 2], lane % 2
            states[position]["sectors"][agent] = int(output["sector_after"]); audit.record("INIT_SECTOR", 1024)
        for renewal, (tau, duration, terminal) in enumerate(schedule_rows(schedule_id)):
            native_rows = []
            local: dict[int, tuple[torch.Tensor, Sequence[Sequence[Interval]], list[int]]] = {}
            for position in positions:
                state = states[position]
                slow_numeric, slow_exact = slow_cache[tau]
                policy, policy_exact = _behavior_bundle(slow_numeric, slow_exact, state["q"], state["q_exact"])
                actions = [exact_cat(policy_exact[a], event_identity(seed, "TRAIN", update, position, a, renewal, "ACTION"), "ACTION", audit) for a in range(2)]
                local[position] = (policy, policy_exact, actions)
                for agent in range(2):
                    native_rows.append(native.MaterializedStep(
                        actions[agent],
                        bit_prefix(event_identity(seed, "TRAIN", update, position, agent, renewal, "MOTION"), 1024),
                        bit_prefix(event_identity(seed, "TRAIN", update, position, agent, renewal, "ACK"), 1024),
                        _event_token(event_identity(seed, "TRAIN", update, position, agent, renewal, "ACTION")),
                        _event_token(event_identity(seed, "TRAIN", update, position, agent, renewal, "MOTION")),
                        _event_token(event_identity(seed, "TRAIN", update, position, agent, renewal, "ACK")),
                    ))
            outputs = host.step(native_rows)
            cursor = 0
            for position in positions:
                state = states[position]
                policy, policy_exact, actions = local[position]
                next_sectors, signs = [], []
                for agent in range(2):
                    output = outputs[cursor]; cursor += 1
                    next_sector, sign = int(output["sector_after"]), int(output["ack_sign"])
                    audit.record("MOTION", 1024); audit.record("ACK", 1024)
                    if output["sector_before"] != state["sectors"][agent] or output["terminal"] is not terminal:
                        raise RuntimeError("batched native training transition mismatch")
                    next_sectors.append(next_sector); signs.append(sign)
                next_beliefs = []
                for agent in range(2):
                    mu = _matmul_belief(state["beliefs"][agent], p_k(duration))
                    ey = tuple(iadd(interval_ratio(-3, 5), imul(interval_ratio(6, 5), mu[a])) for a in range(3))
                    baseline = imul(interval_int(duration), isum(imul(policy_exact[agent][a], ey[a]) for a in range(3)))
                    delta = duration * signs[agent] - rounded_float(baseline, "training-baseline")
                    selected = policy[agent, actions[agent]]
                    entropy = -(policy[agent] * torch.log(policy[agent])).sum()
                    state["task"][agent].append(delta * torch.log(selected) + 0.002 * duration * entropy)
                    next_beliefs.append(_posterior(mu, actions[agent], signs[agent]))
                state["sectors"] = next_sectors
                state["trace"].append((tuple(actions), tuple(signs), duration, tau, terminal))
                if not terminal:
                    state["q"], state["q_exact"] = _recurrence_bundle(model, state["q"], state["q_exact"], actions, signs, duration, tau)
                    for agent in range(2):
                        target = torch.tensor(_anchor_target(actions[agent], signs[agent]), dtype=torch.float64)
                        state["align"][agent].append(-(target * torch.log(state["q"][agent])).sum())
                    state["beliefs"] = next_beliefs
    # Rebuild the differentiable graph in the original episode-major order.
    # The native pass above owns environment state and exact draw resolution;
    # this replay preserves the frozen Python/Torch gradient accumulation order.
    return {
        position: _train_episode_from_materialized_trace(model, slow_cache, states[position]["trace"])
        for position in positions
    }


def _train_episode_from_materialized_trace(
    model: TrackModel,
    slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]],
    trace: Sequence[tuple[Sequence[int], Sequence[int], int, int, bool]],
) -> tuple[list[list[torch.Tensor]], list[list[torch.Tensor]]]:
    q, q_exact = _uniform_q(2)
    beliefs = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
    task: list[list[torch.Tensor]] = [[], []]; align: list[list[torch.Tensor]] = [[], []]
    for actions, signs, duration, tau, terminal in trace:
        slow_numeric, slow_exact = slow_cache[tau]
        policy, policy_exact = _behavior_bundle(slow_numeric, slow_exact, q, q_exact)
        next_beliefs = []
        for agent in range(2):
            mu = _matmul_belief(beliefs[agent], p_k(duration))
            ey = tuple(iadd(interval_ratio(-3, 5), imul(interval_ratio(6, 5), mu[a])) for a in range(3))
            baseline = imul(interval_int(duration), isum(imul(policy_exact[agent][a], ey[a]) for a in range(3)))
            delta = duration * signs[agent] - rounded_float(baseline, "training-baseline")
            selected = policy[agent, actions[agent]]
            entropy = -(policy[agent] * torch.log(policy[agent])).sum()
            task[agent].append(delta * torch.log(selected) + 0.002 * duration * entropy)
            next_beliefs.append(_posterior(mu, actions[agent], signs[agent]))
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


def load_model(seed: int, arm: str, state: dict[str, Any]) -> TrackModel:
    empty = {
        "w1": torch.zeros((8, 2), dtype=torch.float64),
        "w2": torch.zeros((4, 8), dtype=torch.float64),
        "w3": torch.zeros((3, 4), dtype=torch.float64),
    }
    model = TrackModel(seed, arm, slow_arrays=empty)
    tensor_state = {name: torch.tensor(value, dtype=torch.float64) for name, value in state.items()}
    model.load_state_dict(tensor_state, strict=True)
    if not torch.equal(model.E_center, torch.zeros_like(model.E_center)):
        raise RuntimeError("checkpoint recurrent decay center is not exact zero")
    if not all(bool(torch.isfinite(parameter).all()) for parameter in model.ordered_parameters()):
        raise RuntimeError("checkpoint contains a nonfinite trainable tensor")
    return model


def _checkpoint_state_from_training_packet(packet: dict[str, Any], arm: str, binding_kind: str, expected_seed: int) -> dict[str, Any]:
    expected_schema = TRAINING_SCHEMA if binding_kind == "PRODUCTION" else TEST_TRAINING_SCHEMA
    expected_revision = SCIENCE_REVISION if binding_kind == "PRODUCTION" else TEST_FIXTURE_REVISION
    if packet.get("schema") != expected_schema or packet.get("science_revision") != expected_revision:
        raise RuntimeError("checkpoint packet schema or revision does not match active binding")
    if packet.get("binding_class") != binding_kind or packet.get("arm") != arm:
        raise RuntimeError("checkpoint packet binding or arm mismatch")
    if packet.get("algorithm_seed") != expected_seed:
        raise RuntimeError("checkpoint packet algorithm seed mismatch")
    if binding_kind == "PRODUCTION":
        if packet.get("registered") is not True or packet.get("test_fixture") is not False:
            raise RuntimeError("production consumer rejects TEST or unregistered checkpoint packets")
    elif packet.get("registered") is not False or packet.get("test_fixture") is not True:
        raise RuntimeError("TEST consumer requires a TEST-only checkpoint packet")
    reduced_test_fixture = (
        binding_kind == "TEST_ONLY"
        and packet.get("test_fixture_benchmark_reduced") is True
        and isinstance(packet.get("updates"), int) and packet["updates"] > 0
        and isinstance(packet.get("episodes_per_batch"), int) and packet["episodes_per_batch"] > 0
        and packet["episodes_per_batch"] % 2 == 0
        and packet.get("conclusion_update") == REGISTERED_UPDATES
    )
    if not reduced_test_fixture and (packet.get("updates") != REGISTERED_UPDATES or packet.get("episodes_per_batch") != REGISTERED_TRAIN_EPISODES or packet.get("conclusion_update") != REGISTERED_UPDATES):
        raise RuntimeError("evaluation requires the exact update-512 training packet")
    state = packet.get("final_state")
    if not isinstance(state, dict):
        raise RuntimeError("checkpoint packet has no final state")
    return state


def run_training_unit(
    seed: int,
    arm: str,
    *,
    updates: int = REGISTERED_UPDATES,
    episodes: int = REGISTERED_TRAIN_EPISODES,
    progress_guard: Callable[[], None] | None = None,
) -> dict[str, Any]:
    binding_kind = _require_coordinate_binding()
    if arm not in ARMS or episodes <= 0 or episodes % 2:
        raise ValueError("invalid training unit")
    _ensure_production_native_preflight()
    registered = binding_kind == "PRODUCTION" and seed in ALGORITHM_SEEDS and updates == REGISTERED_UPDATES and episodes == REGISTERED_TRAIN_EPISODES
    audit = SamplerAudit()
    arrays = slow_initialization(seed, audit)
    initial_slow_digest = _initial_slow_tensor_sha256(arrays)
    model = TrackModel(seed, arm, slow_arrays=arrays)
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
        if binding_kind == "PRODUCTION":
            if episodes != REGISTERED_TRAIN_EPISODES:
                raise RuntimeError("production native batching requires the exact sixteen-episode batch")
            grouped: dict[int, tuple[list[list[torch.Tensor]], list[list[torch.Tensor]]]] = {}
            grouped.update(_train_episode_group_native(model, seed, update, tuple(range(0, episodes, 2)), 0, slow_by_k[4], audit))
            grouped.update(_train_episode_group_native(model, seed, update, tuple(range(1, episodes, 2)), 1, slow_by_k[8], audit))
        else:
            grouped = {}
        for batch_position in range(episodes):
            if binding_kind == "PRODUCTION":
                task, align = grouped[batch_position]
            else:
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
        "schema": _active_training_schema(),
        "science_revision": _active_revision(),
        "binding_class": binding_kind,
        "test_fixture": binding_kind == "TEST_ONLY",
        "algorithm_seed": seed,
        "arm": arm,
        "conclusion_update": REGISTERED_UPDATES,
        "initial_slow_tensor_sha256": initial_slow_digest,
        "treatment_fence": {
            "initial_e": "G" if arm == "G-START/ZERO-CENTER" else "ZERO",
            "e_center": "ZERO",
            "zero_optimizer_moments": True,
            "trainable_scalars": 114,
            "slow_initialization_identity": [seed, "INIT_MODEL"],
            "paired_event_identity_excludes_arm": True,
        },
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
    if cell == "G-START/ZERO-CENTER-INTACT":
        return "G-START/ZERO-CENTER", "INTACT"
    if cell == "ZERO-START/ZERO-CENTER-INTACT":
        return "ZERO-START/ZERO-CENTER", "INTACT"
    if cell in ("UNIFORM", "STATE-ORACLE"):
        return None, cell
    raise ValueError(cell)


def _evaluate_episode_group_native(
    *, seed: int, schedule_id: int, episodes: Sequence[int], arm: str | None, mode: str,
    model: TrackModel | None, slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]],
    audit: SamplerAudit, summary: EvalSummary,
) -> None:
    import g_init_r01_native_backend as native

    rows = schedule_rows(schedule_id)
    states: dict[int, dict[str, Any]] = {}
    resets = []
    for episode in episodes:
        q, q_exact = _uniform_q(2)
        states[episode] = {
            "sectors": [0, 0], "q": q, "q_exact": q_exact,
            "beta": [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)],
            "tv_values": [], "delta_values": [],
        }
        for agent in range(2):
            identity = event_identity(seed, "EVAL", schedule_id, episode, agent, None, "INIT_SECTOR")
            resets.append(native.MaterializedReset(schedule_id, bit_prefix(identity, 1024), _event_token(identity)))
    with native.NativeInteractiveBatch(resets) as host:
        for lane, output in enumerate(host.initial):
            episode, agent = episodes[lane // 2], lane % 2
            states[episode]["sectors"][agent] = int(output["sector_after"]); audit.record("INIT_SECTOR", 1024)
        for renewal, (tau, duration, terminal) in enumerate(rows):
            native_rows = []
            local: dict[int, tuple[Sequence[Sequence[Interval]], list[int]]] = {}
            for episode in episodes:
                state = states[episode]
                if mode == "UNIFORM":
                    policy_exact = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
                elif mode == "STATE-ORACLE":
                    policy_exact = [tuple(interval_ratio(29, 30) if action == state["sectors"][agent] else interval_ratio(1, 60) for action in range(3)) for agent in range(2)]
                else:
                    assert model is not None
                    _, policy_exact = _behavior_bundle(slow_cache[tau][0], slow_cache[tau][1], state["q"], state["q_exact"])
                actions = [exact_cat(policy_exact[a], event_identity(seed, "EVAL", schedule_id, episode, a, renewal, "ACTION"), "ACTION", audit) for a in range(2)]
                local[episode] = (policy_exact, actions)
                for agent in range(2):
                    native_rows.append(native.MaterializedStep(
                        actions[agent],
                        bit_prefix(event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "MOTION"), 1024),
                        bit_prefix(event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACK"), 1024),
                        _event_token(event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACTION")),
                        _event_token(event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "MOTION")),
                        _event_token(event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACK")),
                    ))
            outputs = host.step(native_rows)
            cursor = 0
            for episode in episodes:
                state = states[episode]
                policy_exact, actions = local[episode]
                next_sectors, signs = [], []
                for agent in range(2):
                    output = outputs[cursor]; cursor += 1
                    next_sector, sign = int(output["sector_after"]), int(output["ack_sign"])
                    audit.record("MOTION", 1024); audit.record("ACK", 1024)
                    if output["sector_before"] != state["sectors"][agent] or output["terminal"] is not terminal:
                        raise RuntimeError("batched native evaluation transition mismatch")
                    next_sectors.append(next_sector); signs.append(sign)
                next_beta = []
                for agent in range(2):
                    mu_beta = _matmul_belief(state["beta"][agent], p_k(duration))
                    next_beta.append(_posterior(mu_beta, actions[agent], signs[agent]))
                    overlap = _overlap(tau, tau + duration, Q_WINDOWS[schedule_id])
                    summary.weighted_reward += overlap * signs[agent]; summary.weighted_ticks += overlap
                    summary.full_reward += duration * signs[agent]; summary.full_ticks += duration
                    summary.decisions += 1; summary.action_counts[actions[agent]] += 1
                    summary.ack_successes += int(signs[agent] > 0)
                    summary.min_support = min(summary.min_support, *(rounded_float(value, "eval-support") for value in policy_exact[agent]))
                state["sectors"] = next_sectors
                if not terminal and arm is not None:
                    old_q, old_q_exact = state["q"], state["q_exact"]
                    assert model is not None
                    state["q"], state["q_exact"] = _recurrence_bundle(model, state["q"], state["q_exact"], actions, signs, duration, tau)
                    summary.updates += 2
                    next_tau, next_k, _ = rows[renewal + 1]
                    if _target_row_eligible(schedule_id, next_tau):
                        _, updated_policy = _behavior_bundle(slow_cache[next_tau][0], slow_cache[next_tau][1], state["q"], state["q_exact"])
                        _, carried_policy = _behavior_bundle(slow_cache[next_tau][0], slow_cache[next_tau][1], old_q, old_q_exact)
                        for agent in range(2):
                            updated_float = interval_vector_floats(updated_policy[agent], "updated-policy")
                            carried_float = interval_vector_floats(carried_policy[agent], "carried-policy")
                            policy_tv = _tv(updated_float, carried_float); state["tv_values"].append(policy_tv)
                            direct = 0.5 * _tv(interval_vector_floats(state["q_exact"][agent], "updated-q"), interval_vector_floats(old_q_exact[agent], "old-q"))
                            summary.direct_tv_max_residual = max(summary.direct_tv_max_residual, abs(policy_tv - direct))
                            state["delta_values"].append(rounded_float(isub(_v_k(next_beta[agent], updated_policy[agent], next_k), _v_k(next_beta[agent], carried_policy[agent], next_k)), "delta-v"))
                state["beta"] = next_beta
    # Preserve the frozen scalar episode-major binary64 reduction order even
    # though environment collection is renewal-major across native lanes.
    for episode in episodes:
        summary.tv_values.extend(states[episode]["tv_values"])
        summary.delta_values.extend(states[episode]["delta_values"])


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
    binding_kind = _require_coordinate_binding()
    arm, mode = _cell_parts(cell)
    if episodes <= 0:
        raise ValueError("episodes must be positive")
    _ensure_production_native_preflight()
    registered = binding_kind == "PRODUCTION" and seed in ALGORITHM_SEEDS and cell in CELL_FAMILIES and schedule_id in SCHEDULE_LABELS and episodes == REGISTERED_EVAL_EPISODES
    model: TrackModel | None = None
    slow_cache: dict[int, tuple[torch.Tensor, tuple[Interval, Interval, Interval]]] = {}
    if arm is not None:
        if arm not in checkpoint_states:
            raise RuntimeError(f"missing checkpoint {arm}")
        state = _checkpoint_state_from_training_packet(checkpoint_states[arm], arm, binding_kind, seed)
        model = load_model(seed, arm, state)
        slow_cache = {tau: _slow_bundle(model, _observation(tau, duration)) for tau, duration, _ in schedule_rows(schedule_id)}
    audit = SamplerAudit()
    summary = EvalSummary()
    rows = schedule_rows(schedule_id)
    started = time.monotonic()
    if binding_kind == "PRODUCTION":
        if episodes != REGISTERED_EVAL_EPISODES:
            raise RuntimeError("production native batching requires the exact sixty-four-episode evaluation unit")
        for start in range(0, episodes, 16):
            _evaluate_episode_group_native(
                seed=seed, schedule_id=schedule_id, episodes=tuple(range(start, start + 16)),
                arm=arm, mode=mode, model=model, slow_cache=slow_cache, audit=audit, summary=summary,
            )
            if progress_guard is not None:
                progress_guard()
        episode_iterator: Iterable[int] = ()
    else:
        episode_iterator = range(episodes)
    for episode in episode_iterator:
        sectors = _initial_sectors(seed, "EVAL", schedule_id, episode, audit)
        native_host = _open_native_episode(sectors, seed, "EVAL", schedule_id, episode, schedule_id)
        q, q_exact = _uniform_q(2)
        beta = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
        try:
            for renewal, (tau, duration, terminal) in enumerate(rows):
                if mode == "UNIFORM":
                    policy_exact = [tuple(interval_ratio(1, 3) for _ in range(3)) for _ in range(2)]
                elif mode == "STATE-ORACLE":
                    policy_exact = [tuple(interval_ratio(29, 30) if action == sectors[agent] else interval_ratio(1, 60) for action in range(3)) for agent in range(2)]
                else:
                    assert model is not None
                    _, policy_exact = _behavior_bundle(slow_cache[tau][0], slow_cache[tau][1], q, q_exact)
                actions = [
                    exact_cat(policy_exact[agent], event_identity(seed, "EVAL", schedule_id, episode, agent, renewal, "ACTION"), "ACTION", audit)
                    for agent in range(2)
                ]
                materialized = [
                    _environment_step(seed, "EVAL", schedule_id, episode, agent, renewal, actions[agent], sectors[agent], duration, audit)
                    for agent in range(2)
                ]
                next_sectors, signs = _native_authoritative_transition(
                    native_host, seed=seed, phase="EVAL", update_or_schedule=schedule_id,
                    episode=episode, renewal=renewal, tau=tau, duration=duration,
                    terminal=terminal, sectors=sectors, actions=actions, materialized=materialized,
                )
                next_beta: list[tuple[Interval, Interval, Interval]] = []
                for agent in range(2):
                    mu_beta = _matmul_belief(beta[agent], p_k(duration))
                    posterior = _posterior(mu_beta, actions[agent], signs[agent])
                    next_beta.append(posterior)
                    overlap = _overlap(tau, tau + duration, Q_WINDOWS[schedule_id])
                    summary.weighted_reward += overlap * signs[agent]
                    summary.weighted_ticks += overlap
                    summary.full_reward += duration * signs[agent]
                    summary.full_ticks += duration
                    summary.decisions += 1
                    summary.action_counts[actions[agent]] += 1
                    summary.ack_successes += int(signs[agent] > 0)
                    summary.min_support = min(summary.min_support, *(rounded_float(value, "eval-support") for value in policy_exact[agent]))
                sectors = next_sectors
                if not terminal and arm is not None:
                    old_q, old_q_exact = q, q_exact
                    assert model is not None
                    q, q_exact = _recurrence_bundle(model, q, q_exact, actions, signs, duration, tau)
                    summary.updates += 2
                    next_tau, next_k, _ = rows[renewal + 1]
                    if _target_row_eligible(schedule_id, next_tau):
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
        finally:
            if native_host is not None:
                native_host.close()
        if progress_guard is not None:
            progress_guard()
    result = summary.result()
    expected_decisions = len(rows) * episodes * 2
    expected_updates = (len(rows) - 1) * episodes * 2 if arm is not None else 0
    if result["decisions"] != expected_decisions or result["updates"] != expected_updates:
        raise RuntimeError("evaluation lifecycle census mismatch")
    if result["direct_tv_max_residual"] > 2.0**-40:
        raise RuntimeError("direct mixture TV identity failed")
    if mode == "INTACT":
        eligible = {0: 47, 1: 23, 2: 15, 3: 7, 4: 23}[schedule_id] * episodes * 2
        if result["diagnostic"]["rows"] != eligible:
            raise RuntimeError("diagnostic row census mismatch")
    expected_audit = {
        "INIT_SECTOR": episodes * 2,
        "ACTION": expected_decisions,
        "MOTION": expected_decisions,
        "ACK": expected_decisions,
    }
    if audit.calls != expected_audit:
        raise RuntimeError(f"evaluation ledger mismatch: {audit.calls} != {expected_audit}")
    return {
        "schema": _active_evaluation_schema(),
        "science_revision": _active_revision(),
        "binding_class": binding_kind,
        "test_fixture": binding_kind == "TEST_ONLY",
        "algorithm_seed": seed,
        "cell": cell,
        "schedule_id": schedule_id,
        "schedule": SCHEDULE_LABELS[schedule_id],
        "registered": registered,
        "episodes": episodes,
        "conclusion_update": REGISTERED_UPDATES,
        "evaluation_fence": {
            "actual_completed_recipient_ack_primary_rows": True,
            "offline_belief_does_not_enter_policy": True,
            "offline_scores_do_not_enter_loss_or_optimizer": True,
            "control": mode if mode in ("UNIFORM", "STATE-ORACLE") else None,
            "paired_event_identity_excludes_cell": True,
        },
        "result": result,
        "sampler_audit": {"calls": dict(sorted(audit.calls.items())), "max_prefix_bits": dict(sorted(audit.max_prefix_bits.items()))},
        "elapsed_seconds": time.monotonic() - started,
    }


def _mean_sem(values: np.ndarray) -> tuple[float, float]:
    return float(np.mean(values)), float(np.std(values, ddof=1) / 4.0)


def _lower(values: np.ndarray, confidence: float) -> float:
    mean, sem = _mean_sem(values)
    return mean - float(student_t.ppf(confidence, 15)) * sem


def _nested_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_nested_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_nested_finite(item) for item in value)
    return not isinstance(value, float) or math.isfinite(value)


def _analyze_complete(
    training_units: Sequence[dict[str, Any]],
    evaluation_units: Sequence[dict[str, Any]],
    *,
    test_fixture: bool,
) -> dict[str, Any]:
    training_index = {(unit["algorithm_seed"], unit["arm"]): unit for unit in training_units}
    evaluation_index = {(unit["algorithm_seed"], unit["cell"], unit["schedule_id"]): unit for unit in evaluation_units}
    expected_training = {(seed, arm) for seed in ALGORITHM_SEEDS for arm in ARMS}
    expected_evaluation = {(seed, cell, schedule) for seed in ALGORITHM_SEEDS for cell in CELL_FAMILIES for schedule in range(5)}
    if len(training_units) != 32 or len(evaluation_units) != 320:
        raise RuntimeError("complete panel requires exactly 32 training and 320 evaluation units")
    if len(training_index) != len(training_units) or len(evaluation_index) != len(evaluation_units):
        raise RuntimeError("duplicate unit coordinate")
    if set(training_index) != expected_training or set(evaluation_index) != expected_evaluation:
        raise RuntimeError("incomplete unit panel")
    expected_training_schema = TEST_TRAINING_SCHEMA if test_fixture else TRAINING_SCHEMA
    expected_evaluation_schema = TEST_EVALUATION_SCHEMA if test_fixture else EVALUATION_SCHEMA
    expected_revision = TEST_FIXTURE_REVISION if test_fixture else SCIENCE_REVISION
    expected_binding_class = "TEST_ONLY" if test_fixture else "PRODUCTION"
    if test_fixture:
        if not all(unit.get("registered") is False and unit.get("test_fixture") is True for unit in (*training_units, *evaluation_units)):
            raise RuntimeError("TEST analyzer requires permanently excluded fixture packets")
    elif not all(unit.get("registered") is True and unit.get("test_fixture") is False for unit in (*training_units, *evaluation_units)):
        raise RuntimeError("production analyzer requires registered non-TEST units")
    if not all(unit.get("binding_class") == expected_binding_class for unit in (*training_units, *evaluation_units)):
        raise RuntimeError("unit binding class mismatch")
    if not all(unit.get("schema") == expected_training_schema and unit.get("science_revision") == expected_revision for unit in training_units):
        raise RuntimeError("training schema or revision mismatch")
    if not all(unit.get("schema") == expected_evaluation_schema and unit.get("science_revision") == expected_revision for unit in evaluation_units):
        raise RuntimeError("evaluation schema or revision mismatch")

    def result(seed: int, cell: str, schedule: int) -> dict[str, Any]:
        return evaluation_index[(seed, cell, schedule)]["result"]

    def population(cell: str, metric: str, population_name: str) -> np.ndarray:
        schedules = (0,) if population_name == "k=4" else ((1,) if population_name == "k=8" else TARGET_SCHEDULES)
        return np.asarray([
            float(np.mean([result(seed, cell, schedule)["diagnostic"][metric] for schedule in schedules]))
            for seed in ALGORITHM_SEEDS
        ], dtype=np.float64)

    def q_population(cell: str, population_name: str) -> np.ndarray:
        schedules = (0,) if population_name == "k=4" else ((1,) if population_name == "k=8" else TARGET_SCHEDULES)
        return np.asarray([float(np.mean([result(seed, cell, schedule)["q"] for schedule in schedules])) for seed in ALGORITHM_SEEDS], dtype=np.float64)

    populations = ("k=4", "k=8", "TARGET")
    structural = structural_certificate()
    expected_decisions = {schedule: len(schedule_rows(schedule)) * REGISTERED_EVAL_EPISODES * 2 for schedule in range(5)}
    expected_updates = {schedule: (len(schedule_rows(schedule)) - 1) * REGISTERED_EVAL_EPISODES * 2 for schedule in range(5)}
    expected_diagnostics = {0: 47 * 128, 1: 23 * 128, 2: 15 * 128, 3: 7 * 128, 4: 23 * 128}
    registered_counts = all(
        unit.get("updates") == REGISTERED_UPDATES
        and unit.get("episodes_per_batch") == REGISTERED_TRAIN_EPISODES
        and unit.get("conclusion_update") == REGISTERED_UPDATES
        for unit in training_units
    )
    treatment_fences = all(
        unit.get("treatment_fence") == {
            "initial_e": "G" if unit["arm"] == "G-START/ZERO-CENTER" else "ZERO",
            "e_center": "ZERO",
            "zero_optimizer_moments": True,
            "trainable_scalars": 114,
            "slow_initialization_identity": [unit["algorithm_seed"], "INIT_MODEL"],
            "paired_event_identity_excludes_arm": True,
        }
        for unit in training_units
    )
    slow_digests = {(unit["algorithm_seed"], unit["arm"]): unit.get("initial_slow_tensor_sha256") for unit in training_units}
    paired_slow_digests = all(
        isinstance(slow_digests[(seed, ARMS[0])], str)
        and len(slow_digests[(seed, ARMS[0])]) == 64
        and all(ch in "0123456789abcdef" for ch in slow_digests[(seed, ARMS[0])])
        and slow_digests[(seed, ARMS[0])] == slow_digests[(seed, ARMS[1])]
        for seed in ALGORITHM_SEEDS
    )
    distinct_seed_slow_digests = len({slow_digests[(seed, ARMS[0])] for seed in ALGORITHM_SEEDS}) == len(ALGORITHM_SEEDS)
    evaluation_fences = all(
        unit.get("evaluation_fence") == {
            "actual_completed_recipient_ack_primary_rows": True,
            "offline_belief_does_not_enter_policy": True,
            "offline_scores_do_not_enter_loss_or_optimizer": True,
            "control": unit["cell"] if unit["cell"] in ("UNIFORM", "STATE-ORACLE") else None,
            "paired_event_identity_excludes_cell": True,
        }
        for unit in evaluation_units
    )
    for seed in ALGORITHM_SEEDS:
        for cell in CELL_FAMILIES:
            diagnostic_cell = cell.endswith("-INTACT")
            learned_cell = diagnostic_cell
            for schedule in range(5):
                unit = evaluation_index[(seed, cell, schedule)]
                observed = unit["result"]
                diagnostic = observed["diagnostic"]
                registered_counts &= unit.get("episodes") == REGISTERED_EVAL_EPISODES
                registered_counts &= unit.get("conclusion_update") == REGISTERED_UPDATES
                registered_counts &= observed["decisions"] == expected_decisions[schedule]
                registered_counts &= observed["updates"] == (expected_updates[schedule] if learned_cell else 0)
                registered_counts &= (diagnostic is not None and diagnostic["rows"] == expected_diagnostics[schedule]) if diagnostic_cell else diagnostic is None
    validity = {
        "complete_16_seed_32_training_320_evaluation_panel": True,
        "all_values_finite": _nested_finite(training_units) and _nested_finite(evaluation_units),
        "structural_certificate": structural["passed"],
        "common_function_domain": structural["function_class_equal"],
        "initialization_only_arm_difference": structural["initialization_only_arm_difference"],
        "zero_decay_center_both_arms": structural["zero_decay_center_both_arms"],
        "fresh_coordinate_root_bound": fixture_root() is not None if test_fixture else coordinate_root() is not None,
        "paired_event_identity_law": bool(treatment_fences and evaluation_fences),
        "paired_initial_slow_tensor_digest": bool(paired_slow_digests),
        "distinct_fresh_seed_initializations": bool(distinct_seed_slow_digests),
        "update_512_only_conclusion": True,
        "registered_counts": bool(registered_counts),
        "support_and_normalization": all(
            (result(seed, cell, schedule)["min_support"] > 1 / 21 if cell.endswith("-INTACT") else
             result(seed, cell, schedule)["min_support"] == (1 / 3 if cell == "UNIFORM" else 1 / 60))
            for seed in ALGORITHM_SEEDS for cell in CELL_FAMILIES for schedule in range(5)
        ),
        "actual_recipient_ack_primary_rows": bool(evaluation_fences),
        "offline_observable_noninterference": bool(evaluation_fences),
        "seed_first_reduction": True,
    }
    all_valid = all(validity.values())
    statistics: dict[str, Any] | None = None
    qualification: dict[str, bool] | None = None
    psi: list[int] | None = None
    branch = "NO_BRANCH_SELECTED_INVALID_PANEL"
    bound_count = 0
    if all_valid:
        arm_cells = {
            "G-START/ZERO-CENTER": "G-START/ZERO-CENTER-INTACT",
            "ZERO-START/ZERO-CENTER": "ZERO-START/ZERO-CENTER-INTACT",
        }
        thresholds = {
            "intact_minus_uniform": 0.02,
            "oracle_minus_intact": 0.02,
            "tv_ge_001_fraction": 0.25,
            "delta_positive_fraction": 0.55,
            "delta_mean": 0.005,
        }
        statistics = {}
        qualification = {}
        for arm in ARMS:
            intact = arm_cells[arm]
            arm_ok = True
            arm_rows: dict[str, Any] = {}
            for pop in populations:
                arrays = {
                    "intact_minus_uniform": q_population(intact, pop) - q_population("UNIFORM", pop),
                    "oracle_minus_intact": q_population("STATE-ORACLE", pop) - q_population(intact, pop),
                    "tv_ge_001_fraction": population(intact, "tv_ge_001_fraction", pop),
                    "delta_positive_fraction": population(intact, "delta_positive_fraction", pop),
                    "delta_mean": population(intact, "delta_mean", pop),
                }
                metric_rows: dict[str, Any] = {}
                for name, values in arrays.items():
                    lower95 = _lower(values, 0.95)
                    passed = lower95 > thresholds[name]
                    arm_ok &= passed
                    bound_count += 1
                    metric_rows[name] = {
                        "mean": float(np.mean(values)),
                        "lower95": lower95,
                        "threshold": thresholds[name],
                        "strictly_exceeds": passed,
                    }
                arm_rows[pop] = metric_rows
            statistics[arm] = arm_rows
            qualification[arm] = bool(arm_ok)
        b_g = qualification["G-START/ZERO-CENTER"]
        b_0 = qualification["ZERO-START/ZERO-CENTER"]
        psi = [int(b_g), int(b_0)]
        for candidate, name in (
            ((1, 0), "G_START_ONLY_ANSWERABILITY_QUALIFIED"),
            ((1, 1), "BOTH_STARTS_ANSWERABILITY_QUALIFIED"),
            ((0, 0), "NEITHER_START_ANSWERABILITY_QUALIFIED"),
            ((0, 1), "ZERO_START_ONLY_ANSWERABILITY_QUALIFIED"),
        ):
            if tuple(psi) == candidate:
                branch = name
                break
        if bound_count != 30:
            raise RuntimeError("registered bound census mismatch")

    return {
        "schema": TEST_RESULT_SCHEMA if test_fixture else RESULT_SCHEMA,
        "science_revision": expected_revision,
        "binding_class": expected_binding_class,
        "test_fixture": test_fixture,
        "complete_panel": True,
        "algorithm_seeds": list(ALGORITHM_SEEDS),
        "arms": list(ARMS),
        "cell_families": list(CELL_FAMILIES),
        "schedules": SCHEDULE_LABELS,
        "conclusion_update": REGISTERED_UPDATES,
        "validity": validity,
        "registered_one_sided_bound_count": bound_count,
        "arm_local_statistics": statistics,
        "basic_answerability_qualified": qualification,
        "psi": psi,
        "branch": branch,
        "continuous_arm_contrast_selects_branch": False,
        "partial_scientific_values_exposed": False,
    }


def analyze_complete(training_units: Sequence[dict[str, Any]], evaluation_units: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Analyze only production R01 packets; TEST schemas are rejected."""
    return _analyze_complete(training_units, evaluation_units, test_fixture=False)


def analyze_test_fixture_complete(training_units: Sequence[dict[str, Any]], evaluation_units: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Pure TEST-only branch seam with no production schema or revision."""
    return _analyze_complete(training_units, evaluation_units, test_fixture=True)


def structural_certificate() -> dict[str, Any]:
    g = g_matrix()
    zeros = {"w1": torch.zeros((8, 2), dtype=torch.float64), "w2": torch.zeros((4, 8), dtype=torch.float64), "w3": torch.zeros((3, 4), dtype=torch.float64)}
    g_arm = TrackModel(0, "G-START/ZERO-CENTER", slow_arrays=zeros)
    zero_arm = TrackModel(0, "ZERO-START/ZERO-CENTER", slow_arrays=zeros)
    g_initial_ok = torch.equal(g_arm.E.detach(), g)
    zero_initial_ok = torch.equal(zero_arm.E.detach(), torch.zeros_like(g))
    centers_zero = torch.equal(g_arm.E_center, torch.zeros_like(g)) and torch.equal(zero_arm.E_center, torch.zeros_like(g))
    slow_equal = all(
        torch.equal(getattr(g_arm, name).detach(), getattr(zero_arm, name).detach())
        for name in ("w1", "b1", "w2", "b2", "w3", "b3")
    )
    parameter_domains_equal = tuple(parameter.shape for parameter in g_arm.ordered_parameters()) == tuple(parameter.shape for parameter in zero_arm.ordered_parameters())
    rows: dict[str, Any] = {}
    passed = g_initial_ok and zero_initial_ok and centers_zero and slow_equal and parameter_domains_equal
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
        "schema": TEST_STRUCTURAL_SCHEMA if _binding_kind() == "TEST_ONLY" else STRUCTURAL_SCHEMA,
        "science_revision": TEST_FIXTURE_REVISION if _binding_kind() == "TEST_ONLY" else SCIENCE_REVISION,
        "binding_class": _binding_kind(),
        "test_fixture": _binding_kind() == "TEST_ONLY",
        "passed": bool(passed),
        "function_class_equal": bool(parameter_domains_equal),
        "initialization_only_arm_difference": bool(g_initial_ok and zero_initial_ok and slow_equal and parameter_domains_equal),
        "zero_decay_center_both_arms": bool(centers_zero),
        "g_start_exact": bool(g_initial_ok),
        "zero_start_exact": bool(zero_initial_ok),
        "slow_scalars_each": 75,
        "recurrent_scalars_each": 39,
        "trainable_scalars_each": 114,
        "rows": rows,
    }


def expected_complete_ledger() -> dict[str, int]:
    return {
        # The two arms reuse the same 60 initialization identities per seed.
        "INIT_MODEL": 960,
        "INIT_SECTOR": 565248,
        "ACTION": 20119552,
        "MOTION": 20119552,
        "ACK": 20119552,
    }


def source_fingerprint(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
