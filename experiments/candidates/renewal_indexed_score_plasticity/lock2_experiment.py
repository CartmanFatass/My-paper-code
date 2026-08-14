"""Frozen RISP-B1 revision-07 Lock-2 train/evaluate/analyse panel.

Importing this module is pre-activity: no registered generator is constructed
until :func:`run_lock2` calls ``materialize_initialization`` after validating
the retained Lock-1 certificate.
"""

from __future__ import annotations

import hashlib
import io
import itertools
import json
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
from scipy.stats import t as student_t

from lock1_certificate import (
    EXPECTED_DECISIONS,
    EXPECTED_UPDATES,
    SCIENCE_REVISION,
    T,
    clear_rational_masses,
    event_key,
    initialization_address,
    masks,
    rat32,
    rational_head,
    raw_affine_exact,
    schedule_rows,
)


LOCK2_SCHEMA = "RISP-B1-LOCK2-RESULT-20260813-07"
LOCK1_SCHEMA = "RISP-B1-LOCK1-20260813-07"
ARCHITECTURES = ("RISP", "SIGN_RNN")
FEEDBACKS = ("INTACT", "MARGINAL_TWIN")
TARGET_SCHEDULES = (2, 3, 4)
SCHEDULE_LABELS = {0: "4", 1: "8", 2: "12", 3: "4->12", 4: "12->4"}
Q_WINDOWS = {0: (0, 192), 1: (0, 192), 2: (0, 192), 3: (108, 192), 4: (100, 192)}
FORK_RENEWAL = {2: 0, 3: 24, 4: 8}
GAMMA = Fraction(99, 100)
DISCOUNT_EXACT = {k: sum((GAMMA**j for j in range(k)), Fraction(0)) for k in (4, 8, 12)}
DISCOUNT = {k: float(value) for k, value in DISCOUNT_EXACT.items()}
EXPECTED_LEDGER = {"INIT": 161_792, "ACTION": 5_664_768, "Y": 5_664_768, "ALT": 5_664_768, "TWIN": 301_056}
EXPECTED_BASE_CALLS = {"INIT": 161_792, "ACTION": 5_652_480, "Y": 5_652_480, "ALT": 5_652_480, "TWIN": 301_056}
EXPECTED_FORK_CALLS = {"FORK_ACTION": 12_288, "FORK_Y": 12_288, "FORK_ALT": 12_288}


class ResourceLimitExceeded(RuntimeError):
    """The active production process exceeded its frozen compute lease."""


@dataclass
class ResourceGuard:
    wall_limit_seconds: float = 3600.0
    rss_limit_bytes: int = 1 << 30
    started: float = field(default_factory=time.monotonic)
    frontier: dict[str, Any] = field(default_factory=lambda: {"phase": "preactivity"})

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def check(self, point: str, **frontier: Any) -> tuple[float, int]:
        if frontier:
            self.frontier = {"point": point, **frontier}
        elapsed = self.elapsed()
        peak_rss = _peak_rss_bytes()
        if elapsed >= self.wall_limit_seconds:
            raise ResourceLimitExceeded(f"wall lease exceeded at {point}: {elapsed:.6f}s >= {self.wall_limit_seconds:.6f}s")
        if peak_rss >= self.rss_limit_bytes:
            raise ResourceLimitExceeded(f"RSS lease exceeded at {point}: {peak_rss} >= {self.rss_limit_bytes}")
        return elapsed, peak_rss

    def require_finalization_headroom(self, point: str, reserve_seconds: float = 60.0) -> tuple[float, int]:
        elapsed, peak_rss = self.check(point, phase="finalization")
        if elapsed + reserve_seconds >= self.wall_limit_seconds:
            raise ResourceLimitExceeded(f"insufficient atomic-finalization wall headroom at {point}: {elapsed:.6f}s + {reserve_seconds:.6f}s >= {self.wall_limit_seconds:.6f}s")
        return elapsed, peak_rss


def _finite(values: Iterable[float], label: str) -> None:
    if not all(math.isfinite(float(value)) for value in values):
        raise RuntimeError(f"nonfinite {label}")


def _peak_rss_bytes() -> int:
    """Return Windows PeakWorkingSetSize without adding a runtime dependency."""
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
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
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.argtypes = ()
    get_current_process.restype = wintypes.HANDLE
    get_process_memory_info = psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    )
    get_process_memory_info.restype = wintypes.BOOL
    handle = get_current_process()
    ctypes.set_last_error(0)
    if not get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
        error_code = ctypes.get_last_error()
        detail = ctypes.FormatError(error_code) if error_code else "no Win32 last-error code was supplied"
        raise OSError(error_code, f"GetProcessMemoryInfo failed: {detail}")
    return int(counters.PeakWorkingSetSize)


def _peak_rss_or_none() -> int | None:
    try:
        return _peak_rss_bytes()
    except Exception:
        return None


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Create one durable artifact without exposing a partial destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError(f"refusing to overwrite artifact or stale temp: {path}")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    _atomic_write_bytes(path, encoded)


def _fraction_tuple(values: Iterable[float]) -> tuple[Fraction, ...]:
    return tuple(rat32(float(value)) for value in values)


def _score_eligibility_binary64(
    raw: tuple[Fraction, Fraction, Fraction],
    derivatives: tuple[tuple[Fraction, Fraction], ...],
    policy: tuple[Fraction, Fraction, Fraction],
    selected: int,
) -> tuple[float, float]:
    """Evaluate derivatives/Fisher in the card-authorized binary64 path."""
    raw64 = tuple(float(value) for value in raw)
    derivative64 = tuple(tuple(float(value) for value in row) for row in derivatives)
    pi64 = tuple(float(value) for value in policy)
    ratios = []
    for value in raw64:
        safe = 6.0 * value / (6.0 + abs(value))
        derivative_safe = 36.0 / (6.0 + abs(value)) ** 2
        weight = 16.0 + (safe + 6.0) ** 2
        ratios.append(2.0 * (safe + 6.0) * derivative_safe / weight)
    mean = tuple(sum(pi64[a] * ratios[a] * derivative64[a][j] for a in range(3)) for j in range(2))
    scores = tuple(tuple(ratios[a] * derivative64[a][j] - mean[j] for j in range(2)) for a in range(3))
    fisher = tuple(tuple(sum(pi64[a] * scores[a][i] * scores[a][j] for a in range(3)) for j in range(2)) for i in range(2))
    a00, a01 = fisher[0][0] + 0.05, fisher[0][1]
    a10, a11 = fisher[1][0], fisher[1][1] + 0.05
    determinant = a00 * a11 - a01 * a10
    if not math.isfinite(determinant) or determinant <= 0.0:
        raise RuntimeError("nonfinite or singular regularized Fisher")
    g = scores[selected]
    v0 = (a11 * g[0] - a01 * g[1]) / determinant
    v1 = (-a10 * g[0] + a00 * g[1]) / determinant
    norm = math.hypot(v0, v1)
    divisor = max(1.0, norm)
    result = (v0 / divisor, v1 / divisor)
    _finite(result, "eligibility")
    return result


@dataclass
class SamplerAudit:
    calls: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    attempts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    words: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    rejections: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    max_attempts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    attempt_histogram: dict[str, dict[int, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))

    def record(self, kind: str, attempts: int, words: int) -> None:
        self.calls[kind] += 1
        self.attempts[kind] += attempts
        self.words[kind] += words
        self.rejections[kind] += attempts - 1
        self.max_attempts[kind] = max(self.max_attempts[kind], attempts)
        self.attempt_histogram[kind][attempts] += 1

    def result(self) -> dict[str, Any]:
        keys = sorted(self.calls)
        return {
            "calls": {key: self.calls[key] for key in keys},
            "attempts": {key: self.attempts[key] for key in keys},
            "raw_words": {key: self.words[key] for key in keys},
            "rejections": {key: self.rejections[key] for key in keys},
            "max_attempts": {key: self.max_attempts[key] for key in keys},
            "attempt_histogram": {key: {str(attempts): count for attempts, count in sorted(self.attempt_histogram[key].items())} for key in keys},
            "total_calls": sum(self.calls.values()),
            "total_attempts": sum(self.attempts.values()),
            "total_raw_words": sum(self.words.values()),
        }


def exact_cat(masses: tuple[Fraction, ...], key: int, kind: str, audit: SamplerAudit) -> int:
    """Materialize one science-level R[e,q] tape using event-local PCG64."""
    integer_masses = clear_rational_masses(masses)
    total = sum(integer_masses)
    k_words = max(1, ((total - 1).bit_length() + 63) // 64)
    space = 1 << (64 * k_words)
    limit = (space // total) * total
    bit_generator = np.random.PCG64(key)
    attempts = 0
    while True:
        attempts += 1
        raw = bit_generator.random_raw(k_words)
        words = [int(value) for value in np.asarray(raw, dtype=np.uint64).reshape(-1)]
        assembled = sum(value << (64 * index) for index, value in enumerate(words))
        if assembled < limit:
            residue = assembled % total
            cumulative = 0
            for category, mass in enumerate(integer_masses):
                cumulative += mass
                if residue < cumulative:
                    audit.record(kind, attempts, attempts * k_words)
                    return category


def materialize_initialization(seed: int) -> dict[str, np.ndarray]:
    """Consume exactly I[s,0:100] and construct the paired float32 arrays."""
    bit_generator = np.random.PCG64(initialization_address(seed, 0))
    words = np.asarray(bit_generator.random_raw(100), dtype=np.uint64)
    uniforms = (words >> np.uint64(11)).astype(np.float64) * (2.0**-53)
    shapes = (("w1", 8, 2), ("w2", 4, 8), ("base", 3, 4), ("U", 3, 2), ("V", 4, 2), ("W", 2, 13))
    arrays: dict[str, np.ndarray] = {}
    offset = 0
    for name, fan_out, fan_in in shapes:
        size = fan_out * fan_in
        bound = math.sqrt(6.0 / (fan_in + fan_out))
        array = bound * (2.0 * uniforms[offset : offset + size] - 1.0)
        arrays[name] = np.asarray(array.reshape(fan_out, fan_in), dtype=np.float32)
        offset += size
    if offset != 100:
        raise RuntimeError("initialization traversal did not consume exactly 100 words")
    return arrays


class RISPModel(torch.nn.Module):
    """The 117-scalar common policy and architecture-specific transition."""

    def __init__(self, arrays: dict[str, np.ndarray], architecture: str) -> None:
        super().__init__()
        if architecture not in ARCHITECTURES:
            raise ValueError(architecture)
        self.architecture = architecture
        for name in ("w1", "w2", "base", "U", "V", "W"):
            self.register_parameter(name, torch.nn.Parameter(torch.from_numpy(arrays[name].copy())))
        self.register_parameter("b1", torch.nn.Parameter(torch.zeros(8, dtype=torch.float32)))
        self.register_parameter("b2", torch.nn.Parameter(torch.zeros(4, dtype=torch.float32)))
        self.register_parameter("base_b", torch.nn.Parameter(torch.zeros(3, dtype=torch.float32)))
        self.register_parameter("transition_b", torch.nn.Parameter(torch.zeros(2, dtype=torch.float32)))
        mask_r, mask_g = masks()
        chosen = mask_r if architecture == "RISP" else mask_g
        self.register_buffer("fixed_mask", torch.tensor(chosen, dtype=torch.float32))
        if sum(parameter.numel() for parameter in self.parameters()) != 117:
            raise RuntimeError("architecture does not have exactly 117 learned scalars")

    def policy_features(self, observation: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden8 = torch.tanh(observation @ self.w1.T + self.b1)
        hidden4 = torch.tanh(hidden8 @ self.w2.T + self.b2)
        base = hidden4 @ self.base.T + self.base_b
        return hidden4, base

    def policy_binary64_derivative_path(self, hidden4: torch.Tensor, base: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
        """Authorized binary64 derivative evaluation of the exact rational head."""
        # Each operand first exists as the registered binary32 tensor output;
        # conversion to binary64 is exact, and no alternate softmax/rounded CDF
        # law is introduced on the backward path.
        hidden64 = hidden4.to(torch.float64)
        base64 = base.to(torch.float64)
        state64 = state.to(torch.float64)
        vh = hidden64 @ self.V.to(torch.float64)
        raw = base64 + (vh * state64) @ self.U.to(torch.float64).T
        safe = 6.0 * raw / (6.0 + torch.abs(raw))
        weight = 16.0 + (safe + 6.0).square()
        return weight / weight.sum(dim=-1, keepdim=True)

    def transition(self, state: torch.Tensor, packet: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        preprojection = state + 0.1 * (packet @ (self.W + self.fixed_mask).T + self.transition_b)
        norm = torch.linalg.vector_norm(preprojection, dim=-1, keepdim=True)
        scale = torch.clamp(3.0 / torch.clamp(norm, min=torch.finfo(torch.float32).tiny), max=1.0)
        projected = preprojection * scale
        return projected, preprojection, norm.squeeze(-1)


def _exact_policy_rows(
    model: RISPModel, hidden: torch.Tensor, base: torch.Tensor, state: torch.Tensor
) -> tuple[list[tuple[Fraction, Fraction, Fraction]], list[tuple[tuple[Fraction, Fraction], ...]], list[tuple[Fraction, Fraction, Fraction]]]:
    u = tuple(tuple(rat32(float(value)) for value in row) for row in model.U.detach().cpu().tolist())
    v = tuple(tuple(rat32(float(value)) for value in row) for row in model.V.detach().cpu().tolist())
    policies: list[tuple[Fraction, Fraction, Fraction]] = []
    derivatives: list[tuple[tuple[Fraction, Fraction], ...]] = []
    raw_rows: list[tuple[Fraction, Fraction, Fraction]] = []
    for h_values, b_values, x_values in zip(hidden.detach().cpu().tolist(), base.detach().cpu().tolist(), state.detach().cpu().tolist()):
        h = _fraction_tuple(h_values)
        b = _fraction_tuple(b_values)
        x = _fraction_tuple(x_values)
        raw = raw_affine_exact(b, u, v, h, x)
        raw_rows.append(raw)
        policies.append(rational_head(raw)["pi"])
        vh = tuple(sum((v[row][column] * h[row] for row in range(4)), Fraction(0)) for column in range(2))
        derivatives.append(tuple(tuple(u[action][j] * vh[j] for j in range(2)) for action in range(3)))
    return policies, derivatives, raw_rows


def _policy_bundle(model: RISPModel, observation: torch.Tensor, state: torch.Tensor) -> tuple[torch.Tensor, list[tuple[Fraction, Fraction, Fraction]], list[tuple[tuple[Fraction, Fraction], ...]], list[tuple[Fraction, Fraction, Fraction]], torch.Tensor, torch.Tensor]:
    hidden, base = model.policy_features(observation)
    numeric = model.policy_binary64_derivative_path(hidden, base, state)
    exact, derivatives, raw_rows = _exact_policy_rows(model, hidden, base, state)
    exact_float = torch.tensor([[float(value) for value in row] for row in exact], dtype=torch.float64)
    policy = numeric + (exact_float - numeric).detach()
    _finite(policy.detach().cpu().flatten().tolist(), "policy")
    return policy, exact, derivatives, raw_rows, hidden, base


def _observation(count: int, tau: int, k: int) -> torch.Tensor:
    return torch.tensor([[tau / T, k / 12.0]] * count, dtype=torch.float32)


def _controller_belief_update(actions: list[int], signs: list[int]) -> torch.Tensor:
    result = torch.zeros((len(actions), 3), dtype=torch.float32)
    for row, (action, sign) in enumerate(zip(actions, signs)):
        if sign > 0:
            result[row, action] = 1.0
        elif sign < 0:
            result[row, :] = 0.5
            result[row, action] = 0.0
        else:
            result[row, :] = 1.0 / 3.0
    return result


def _packet(state: torch.Tensor, actions: list[int], signs: list[int], eligibility: list[tuple[float, float]], k: int, tau: int) -> torch.Tensor:
    rows = []
    for row, (action, sign, e) in enumerate(zip(actions, signs, eligibility)):
        one_hot = [0.0, 0.0, 0.0]
        one_hot[action] = 1.0
        norm = math.hypot(*e)
        rows.append([state[row, 0], state[row, 1], *one_hot, float(sign), e[0], e[1], sign * e[0], sign * e[1], sign * norm, k / 12.0, tau / T])
    return torch.stack([torch.stack([value if isinstance(value, torch.Tensor) else torch.tensor(value, dtype=torch.float32) for value in row]) for row in rows])


def _draw_environment(kind_prefix: str, fields: tuple[int, ...], action: int, target: int, audit: SamplerAudit) -> tuple[int, int]:
    match = action == target
    outcome_index = exact_cat((Fraction(3), Fraction(1)) if match else (Fraction(1), Fraction(3)), event_key(f"{kind_prefix}_Y", *fields), "Y", audit)
    sign = 1 if outcome_index == 0 else -1
    alternatives = tuple(candidate for candidate in range(3) if candidate != action)
    alt_index = exact_cat((Fraction(1), Fraction(1)), event_key(f"{kind_prefix}_alt", *fields), "ALT", audit)
    next_target = action if sign > 0 else alternatives[alt_index]
    return sign, next_target


def _training_group(model: RISPModel, seed: int, update: int, episode_indices: list[int], k: int, audit: SamplerAudit) -> torch.Tensor:
    count = len(episode_indices) * 2
    targets: list[int] = []
    for episode in episode_indices:
        for agent in range(2):
            fields = (seed, update, episode, agent)
            targets.append(exact_cat((Fraction(1),) * 3, event_key("train_init", *fields), "INIT", audit))
    state = torch.zeros((count, 2), dtype=torch.float32)
    belief = torch.full((count, 3), 1.0 / 3.0, dtype=torch.float32)
    terms: list[torch.Tensor] = []
    for renewal, (tau, duration, terminal) in enumerate(schedule_rows(0 if k == 4 else 1)):
        policy, exact_policy, derivatives, raw_rows, _, _ = _policy_bundle(model, _observation(count, tau, duration), state)
        actions: list[int] = []
        outcomes: list[int] = []
        next_targets: list[int] = []
        eligibility: list[tuple[float, float]] = []
        for row, (episode, agent) in enumerate((pair for episode in episode_indices for pair in ((episode, 0), (episode, 1)))):
            fields = (seed, update, episode, agent, renewal)
            action = exact_cat(exact_policy[row], event_key("train_action", *fields), "ACTION", audit)
            outcome, next_target = _draw_environment("train", fields, action, targets[row], audit)
            eligibility.append(_score_eligibility_binary64(raw_rows[row], derivatives[row], exact_policy[row], action))
            actions.append(action)
            outcomes.append(outcome)
            next_targets.append(next_target)
        selected = policy[torch.arange(count), torch.tensor(actions)]
        centered = belief - 0.5
        baseline_factor = (policy * centered).sum(dim=1).detach()
        delta = DISCOUNT[duration] * (torch.tensor(outcomes, dtype=torch.float32) - baseline_factor)
        if any((1 if value > 0 else -1 if value < 0 else 0) != outcome for value, outcome in zip(delta.tolist(), outcomes)):
            raise RuntimeError("analytic residual sign identity failed in training")
        entropy = -(policy * torch.log(policy)).sum(dim=1)
        terms.append((delta.detach() * torch.log(selected) + 0.002 * DISCOUNT[duration] * entropy).sum())
        targets = next_targets
        if not terminal:
            state, _, _ = model.transition(state, _packet(state, actions, outcomes, eligibility, duration, tau))
            belief = _controller_belief_update(actions, outcomes)
    return torch.stack(terms).sum()


def train_model(model: RISPModel, seed: int, audit: SamplerAudit, guard: ResourceGuard) -> dict[str, Any]:
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)
    losses: list[float] = []
    for update in range(256):
        optimizer.zero_grad(set_to_none=True)
        sum_terms = _training_group(model, seed, update, list(range(0, 16, 2)), 4, audit)
        sum_terms = sum_terms + _training_group(model, seed, update, list(range(1, 16, 2)), 8, audit)
        loss = -sum_terms / (16 * 2 * T)
        if not torch.isfinite(loss):
            raise RuntimeError("nonfinite training loss")
        loss.backward()
        gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
        if not math.isfinite(gradient_norm):
            raise RuntimeError("nonfinite global gradient norm")
        optimizer.step()
        losses.append(float(loss.detach()))
        guard.check("training_update_complete", phase="training", seed=seed, architecture=model.architecture, completed_update=update)
    return {"updates": 256, "loss_first": losses[0], "loss_final": losses[-1], "loss_min": min(losses), "loss_max": max(losses)}


@dataclass
class EvalAccumulator:
    reward_by_tick: np.ndarray = field(default_factory=lambda: np.zeros(T, dtype=np.float64))
    reward_by_renewal: np.ndarray = field(default_factory=lambda: np.zeros(48, dtype=np.float64))
    renewal_observations: np.ndarray = field(default_factory=lambda: np.zeros(48, dtype=np.int64))
    action_counts: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.int64))
    entropy_sum: float = 0.0
    decisions: int = 0
    updates: int = 0
    projection_active: int = 0
    nonzero_sign_packets: int = 0
    eligibility_gt_005: int = 0
    tv_rows: int = 0
    tv_ge_0005: int = 0
    support_min: float = 1.0
    residual_sign_errors: int = 0
    terminal_residual_diagnostics: int = 0
    zero_signs: int = 0
    mechanism_read: bool = False
    pbar_min: float = 1.0
    pbar_max: float = 0.0
    twin_rows: int = 0
    recipient_sign_counts: dict[str, list[int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0]))
    twin_sign_counts: dict[str, list[int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0]))
    discordance_counts: dict[str, list[int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0]))
    fork_tv_sum: float = 0.0
    fork_return_realized_sum: float = 0.0
    fork_return_twin_sum: float = 0.0
    fork_agent_rows: int = 0


def _overlap(start: int, stop: int, window: tuple[int, int]) -> int:
    return max(0, min(stop, window[1]) - max(start, window[0]))


def _single_policy_exact(model: RISPModel, observation: torch.Tensor, state: torch.Tensor) -> tuple[Fraction, Fraction, Fraction]:
    with torch.no_grad():
        _, exact, _, _, _, _ = _policy_bundle(model, observation, state)
    return exact[0]


def _run_fork(
    model: RISPModel,
    seed: int,
    schedule_id: int,
    episode: int,
    states_before: torch.Tensor,
    packets_realized: torch.Tensor,
    packets_twin: torch.Tensor,
    targets_after: list[int],
    next_tau: int,
    next_k: int,
    audit: SamplerAudit,
    accumulator: EvalAccumulator,
) -> None:
    with torch.no_grad():
        state_r, _, _ = model.transition(states_before, packets_realized)
        state_m, _, _ = model.transition(states_before, packets_twin)
        observation = _observation(2, next_tau, next_k)
        _, policy_r, _, _, _, _ = _policy_bundle(model, observation, state_r)
        _, policy_m, _, _, _, _ = _policy_bundle(model, observation, state_m)
    for agent in range(2):
        accumulator.fork_tv_sum += 0.5 * sum(abs(float(policy_r[agent][a] - policy_m[agent][a])) for a in range(3))
        branch_returns = []
        for policy in (policy_r[agent], policy_m[agent]):
            fields = (seed, schedule_id, episode, agent)
            action = exact_cat(policy, event_key("fork_action", *fields), "FORK_ACTION", audit)
            match = action == targets_after[agent]
            y_index = exact_cat((Fraction(3), Fraction(1)) if match else (Fraction(1), Fraction(3)), event_key("fork_Y", *fields), "FORK_Y", audit)
            sign = 1 if y_index == 0 else -1
            exact_cat((Fraction(1), Fraction(1)), event_key("fork_alt", *fields), "FORK_ALT", audit)
            branch_returns.append(sign * next_k)
        accumulator.fork_return_realized_sum += branch_returns[0]
        accumulator.fork_return_twin_sum += branch_returns[1]
        accumulator.fork_agent_rows += 1


def evaluate_cell(model: RISPModel, seed: int, schedule_id: int, feedback: str, audit: SamplerAudit, guard: ResourceGuard) -> tuple[dict[str, Any], EvalAccumulator]:
    rows = schedule_rows(schedule_id)
    count = 64 * 2
    targets: list[int] = []
    for episode in range(64):
        for agent in range(2):
            fields = (seed, schedule_id, episode, agent)
            targets.append(exact_cat((Fraction(1),) * 3, event_key("eval_init", *fields), "INIT", audit))
    state = torch.zeros((count, 2), dtype=torch.float32)
    belief = torch.full((count, 3), 1.0 / 3.0, dtype=torch.float32)
    rho = [[Fraction(1, 3)] * 3 for _ in range(count)]
    acc = EvalAccumulator()
    episode_reward = np.zeros(64, dtype=np.float64)
    episode_q = np.zeros(64, dtype=np.float64)
    q_window = Q_WINDOWS[schedule_id]
    updated_pending_read = np.zeros(count, dtype=bool)
    for renewal, (tau, duration, terminal) in enumerate(rows):
        if renewal > 0 and bool(updated_pending_read.any()):
            acc.mechanism_read = True
            updated_pending_read[:] = False
        with torch.no_grad():
            policy, exact_policy, derivatives, raw_rows, _, _ = _policy_bundle(model, _observation(count, tau, duration), state)
        # H_n is frozen here, including policy, b_n, baseline inputs and score inputs.
        baseline_factor = (policy * (belief - 0.5)).sum(dim=1).detach().cpu().tolist()
        actions: list[int] = []
        outcomes: list[int] = []
        next_targets: list[int] = []
        eligibility: list[tuple[float, float]] = []
        twin_signs: list[int] = []
        for row in range(count):
            episode, agent = divmod(row, 2)
            fields = (seed, schedule_id, episode, agent, renewal)
            action = exact_cat(exact_policy[row], event_key("eval_action", *fields), "ACTION", audit)
            e = _score_eligibility_binary64(raw_rows[row], derivatives[row], exact_policy[row], action)
            twin_sign: int | None = None
            if feedback == "MARGINAL_TWIN" and not terminal:
                # The replicate coordinate is consumed before any recipient Y/ALT/next-target
                # coordinate, so no recipient outcome lineage can enter the draw.
                pbar = Fraction(1, 4) + Fraction(1, 2) * rho[row][action]
                twin_index = exact_cat((pbar, 1 - pbar), event_key("twin", *fields), "TWIN", audit)
                twin_sign = 1 if twin_index == 0 else -1
                twin_signs.append(twin_sign)
                acc.pbar_min = min(acc.pbar_min, float(pbar))
                acc.pbar_max = max(acc.pbar_max, float(pbar))
                acc.twin_rows += 1
                rho[row] = [(1 - pbar) / 2] * 3
                rho[row][action] = pbar
            outcome, next_target = _draw_environment("eval", fields, action, targets[row], audit)
            actions.append(action)
            outcomes.append(outcome)
            next_targets.append(next_target)
            eligibility.append(e)
            acc.action_counts[action] += 1
            acc.support_min = min(acc.support_min, *(float(value) for value in exact_policy[row]))
            acc.entropy_sum += -sum(float(value) * math.log(float(value)) for value in exact_policy[row])
            start, stop = tau, tau + duration
            acc.reward_by_tick[start:stop] += outcome
            acc.reward_by_renewal[renewal] += outcome
            acc.renewal_observations[renewal] += 1
            episode_reward[episode] += outcome * duration / (2 * T)
            episode_q[episode] += outcome * _overlap(start, stop, q_window) / (2 * (q_window[1] - q_window[0]))
            if twin_sign is not None:
                key_action = f"{duration}:{action}"
                acc.recipient_sign_counts[key_action][0 if outcome < 0 else 1] += 1
                acc.twin_sign_counts[key_action][0 if twin_sign < 0 else 1] += 1
                match_key = f"{duration}:{int(action == targets[row])}"
                acc.discordance_counts[match_key][0] += int(twin_sign != outcome)
                acc.discordance_counts[match_key][1] += 1
            elif not terminal:
                twin_signs.append(outcome)
        acc.decisions += count
        targets = next_targets
        if terminal:
            for value, recipient_sign in zip(baseline_factor, outcomes):
                delta = DISCOUNT[duration] * (recipient_sign - value)
                _finite((value, delta), "terminal recipient baseline/delta diagnostic")
                acc.residual_sign_errors += int((1 if delta > 0 else -1 if delta < 0 else 0) != recipient_sign)
                acc.terminal_residual_diagnostics += 1
            guard.check("evaluation_terminal_renewal_complete", phase="evaluation", seed=seed, architecture=model.architecture, feedback=feedback, schedule_id=schedule_id, completed_renewal=renewal)
            continue
        supplied = outcomes if feedback == "INTACT" else twin_signs
        acc.zero_signs += sum(sign == 0 for sign in supplied)
        for value, supplied_sign in zip(baseline_factor, supplied):
            delta = DISCOUNT[duration] * (supplied_sign - value)
            acc.residual_sign_errors += int((1 if delta > 0 else -1 if delta < 0 else 0) != supplied_sign)
        packet_supplied = _packet(state, actions, supplied, eligibility, duration, tau)
        with torch.no_grad():
            next_state, preprojection, pre_norm = model.transition(state, packet_supplied)
        acc.updates += count
        acc.projection_active += int((pre_norm > 3.0).sum())
        for e in eligibility:
            norm = math.hypot(*e)
            acc.nonzero_sign_packets += 1
            acc.eligibility_gt_005 += int(norm > 0.05)
        if feedback == "INTACT" and schedule_id in TARGET_SCHEDULES:
            next_tau, next_duration, _ = rows[renewal + 1]
            with torch.no_grad():
                _, p_updated, _, _, _, _ = _policy_bundle(model, _observation(count, next_tau, next_duration), next_state)
                _, p_clone, _, _, _, _ = _policy_bundle(model, _observation(count, next_tau, next_duration), state)
            for row in range(count):
                tv = 0.5 * sum(abs(float(p_updated[row][a] - p_clone[row][a])) for a in range(3))
                acc.tv_rows += 1
                acc.tv_ge_0005 += int(tv >= 0.005)
        if feedback == "MARGINAL_TWIN" and schedule_id in TARGET_SCHEDULES and renewal == FORK_RENEWAL[schedule_id]:
            realized_packet = _packet(state, actions, outcomes, eligibility, duration, tau)
            for episode in range(64):
                sl = slice(2 * episode, 2 * episode + 2)
                next_tau, next_duration, _ = rows[renewal + 1]
                _run_fork(model, seed, schedule_id, episode, state[sl], realized_packet[sl], packet_supplied[sl], targets[sl], next_tau, next_duration, audit, acc)
        state = next_state
        belief = _controller_belief_update(actions, supplied)
        updated_pending_read[:] = True
        guard.check("evaluation_renewal_complete", phase="evaluation", seed=seed, architecture=model.architecture, feedback=feedback, schedule_id=schedule_id, completed_renewal=renewal)
    denom_rows = 64 * 2
    result = {
        "J": float(episode_reward.mean()),
        "Q": float(episode_q.mean()),
        "episode_J": episode_reward.tolist(),
        "episode_Q": episode_q.tolist(),
        "action_counts": acc.action_counts.tolist(),
        "mean_action_entropy": acc.entropy_sum / acc.decisions,
        "renewal_count": len(rows),
        "decisions": acc.decisions,
        "updates": acc.updates,
        "physical_tick_reward_curve": (acc.reward_by_tick / denom_rows).tolist(),
        "renewal_reward_curve": [float(acc.reward_by_renewal[n] / acc.renewal_observations[n]) for n in range(len(rows))],
        "support_min": acc.support_min,
        "nonzero_sign_packet_count": acc.nonzero_sign_packets,
        "eligibility_gt_005_count": acc.eligibility_gt_005,
        "eligibility_gt_005_fraction": acc.eligibility_gt_005 / max(1, acc.nonzero_sign_packets),
        "projection_active_fraction": acc.projection_active / max(1, acc.updates),
        "tv_ge_0005_fraction": acc.tv_ge_0005 / max(1, acc.tv_rows) if acc.tv_rows else None,
        "mechanism_update_read": acc.mechanism_read,
        "zero_sign_count": acc.zero_signs,
        "terminal_recipient_residual_diagnostic_count": acc.terminal_residual_diagnostics,
    }
    if schedule_id in (3, 4):
        result["first_48_post_switch_mean_reward"] = float(np.mean(result["physical_tick_reward_curve"][96:144]))
    if feedback == "MARGINAL_TWIN":
        result["twin_audit"] = {
            "eligible_rows": acc.twin_rows,
            "pbar_min": acc.pbar_min,
            "pbar_max": acc.pbar_max,
            "recipient_sign_counts": dict(acc.recipient_sign_counts),
            "replicate_sign_counts": dict(acc.twin_sign_counts),
            "discordance_counts": dict(acc.discordance_counts),
        }
    if acc.fork_agent_rows:
        result["immediate_fork"] = {
            "agent_rows": acc.fork_agent_rows,
            "mean_next_action_tv": acc.fork_tv_sum / acc.fork_agent_rows,
            "mean_next_hold_return_realized_branch": acc.fork_return_realized_sum / acc.fork_agent_rows,
            "mean_next_hold_return_twin_branch": acc.fork_return_twin_sum / acc.fork_agent_rows,
            "first_possible_difference_after_completed_update": True,
        }
    return result, acc


def evaluate_control(seed: int, schedule_id: int, controller: str, audit: SamplerAudit, guard: ResourceGuard) -> dict[str, Any]:
    rows = schedule_rows(schedule_id)
    episode_j = np.zeros(64, dtype=np.float64)
    episode_q = np.zeros(64, dtype=np.float64)
    window = Q_WINDOWS[schedule_id]
    for episode in range(64):
        targets = [exact_cat((Fraction(1),) * 3, event_key("eval_init", seed, schedule_id, episode, agent), "INIT", audit) for agent in range(2)]
        for renewal, (tau, duration, _) in enumerate(rows):
            for agent in range(2):
                if controller == "UNIFORM":
                    masses = (Fraction(1),) * 3
                elif controller == "STATE_ORACLE":
                    masses_list = [Fraction(1, 60)] * 3
                    masses_list[targets[agent]] = Fraction(29, 30)
                    masses = tuple(masses_list)
                else:
                    raise ValueError(controller)
                fields = (seed, schedule_id, episode, agent, renewal)
                action = exact_cat(masses, event_key("eval_action", *fields), "ACTION", audit)
                outcome, next_target = _draw_environment("eval", fields, action, targets[agent], audit)
                targets[agent] = next_target
                episode_j[episode] += outcome * duration / (2 * T)
                episode_q[episode] += outcome * _overlap(tau, tau + duration, window) / (2 * (window[1] - window[0]))
        guard.check("control_episode_complete", phase="control", seed=seed, controller=controller, schedule_id=schedule_id, completed_episode=episode)
    return {"J": float(episode_j.mean()), "Q": float(episode_q.mean()), "episode_J": episode_j.tolist(), "episode_Q": episode_q.tolist(), "decisions": 64 * 2 * len(rows)}


def _save_checkpoint(model: RISPModel, path: Path) -> dict[str, Any]:
    actually_frozen = (not model.training) and all(not parameter.requires_grad for parameter in model.parameters())
    if not actually_frozen:
        raise RuntimeError("checkpoint save refused because model/evaluation state is not actually frozen")
    arrays = {name: parameter.detach().cpu().numpy() for name, parameter in model.named_parameters()}
    buffer = io.BytesIO()
    np.savez(buffer, **arrays)
    payload = buffer.getvalue()
    _atomic_write_bytes(path, payload)
    digest = hashlib.sha256(payload).hexdigest()
    return {"path": str(path.resolve()), "sha256": digest, "learned_scalars": sum(array.size for array in arrays.values()), "slow_parameters_frozen_before_evaluation": actually_frozen}


def _load_frozen_checkpoint(path: Path, architecture: str, expected_sha256: str) -> RISPModel:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise RuntimeError(f"checkpoint digest mismatch before evaluation: {path}")
    with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
        archived = {name: np.asarray(archive[name], dtype=np.float32).copy() for name in archive.files}
    weight_names = ("w1", "w2", "base", "U", "V", "W")
    if any(name not in archived for name in weight_names):
        raise RuntimeError(f"checkpoint lacks a registered learned weight: {path}")
    model = RISPModel({name: archived[name] for name in weight_names}, architecture)
    parameters = dict(model.named_parameters())
    if set(archived) != set(parameters):
        raise RuntimeError(f"checkpoint parameter-name set mismatch: {path}")
    with torch.no_grad():
        for name, parameter in parameters.items():
            value = torch.from_numpy(archived[name])
            if value.shape != parameter.shape or value.dtype != parameter.dtype:
                raise RuntimeError(f"checkpoint tensor shape/dtype mismatch for {name}: {path}")
            parameter.copy_(value)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if model.training or any(parameter.requires_grad for parameter in model.parameters()):
        raise RuntimeError(f"deterministically loaded checkpoint is not frozen: {path}")
    return model


def _interval(values: list[float], confidence: float, side: str = "two-sided") -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    sem = float(array.std(ddof=1) / math.sqrt(len(array)))
    if side == "two-sided":
        critical = float(student_t.ppf((1 + confidence) / 2, len(array) - 1))
        lower, upper = mean - critical * sem, mean + critical * sem
    elif side == "lower":
        critical = float(student_t.ppf(confidence, len(array) - 1))
        lower, upper = mean - critical * sem, None
    elif side == "upper":
        critical = float(student_t.ppf(confidence, len(array) - 1))
        lower, upper = None, mean + critical * sem
    else:
        raise ValueError(side)
    return {"seed_effects": array.tolist(), "mean": mean, "sem": sem, "df": len(array) - 1, "confidence": confidence, "side": side, "lower": lower, "upper": upper}


def _sign_flip_p(values: list[float]) -> float:
    observed = abs(float(np.mean(values)))
    exceed = 0
    for signs in itertools.product((-1.0, 1.0), repeat=8):
        exceed += abs(float(np.mean(np.asarray(values) * np.asarray(signs)))) >= observed - 1e-15
    return exceed / 256.0


def _aggregate_counter(accumulators: list[EvalAccumulator], field_name: str) -> int:
    return sum(int(getattr(item, field_name)) for item in accumulators)


def analyse(seed_results: list[dict[str, Any]], accumulators: dict[tuple[str, str, int], list[EvalAccumulator]], sampler: SamplerAudit, lock1: dict[str, Any]) -> dict[str, Any]:
    def q(seed: int, arch: str, feedback: str, schedule: int) -> float:
        return seed_results[seed]["cells"][arch][feedback][str(schedule)]["Q"]

    def j(seed: int, arch: str, feedback: str, schedule: int) -> float:
        return seed_results[seed]["cells"][arch][feedback][str(schedule)]["J"]

    effects: dict[str, dict[int, list[float]]] = {name: {} for name in ("D_I", "D_M", "Psi", "C_R", "C_G")}
    for schedule in TARGET_SCHEDULES:
        effects["D_I"][schedule] = [q(s, "RISP", "INTACT", schedule) - q(s, "SIGN_RNN", "INTACT", schedule) for s in range(8)]
        effects["D_M"][schedule] = [q(s, "RISP", "MARGINAL_TWIN", schedule) - q(s, "SIGN_RNN", "MARGINAL_TWIN", schedule) for s in range(8)]
        effects["Psi"][schedule] = [effects["D_I"][schedule][s] - effects["D_M"][schedule][s] for s in range(8)]
        effects["C_R"][schedule] = [q(s, "RISP", "INTACT", schedule) - q(s, "RISP", "MARGINAL_TWIN", schedule) for s in range(8)]
        effects["C_G"][schedule] = [q(s, "SIGN_RNN", "INTACT", schedule) - q(s, "SIGN_RNN", "MARGINAL_TWIN", schedule) for s in range(8)]
    pooled = {name: [sum(by_schedule[schedule][seed] for schedule in TARGET_SCHEDULES) / 3 for seed in range(8)] for name, by_schedule in effects.items()}
    inference: dict[str, Any] = {"schedule": {}, "pooled": {}}
    for name, by_schedule in effects.items():
        inference["schedule"][name] = {}
        for schedule, values in by_schedule.items():
            inference["schedule"][name][SCHEDULE_LABELS[schedule]] = {
                "two_sided_90": _interval(values, 0.90),
                "one_sided_95": _interval(values, 0.95, "lower"),
                "one_sided_98_333_lower": _interval(values, 1 - 0.05 / 3, "lower"),
                "one_sided_97_5_lower": _interval(values, 0.975, "lower"),
                "one_sided_98_75_upper": _interval(values, 0.9875, "upper"),
                "exact_two_sided_sign_flip_p": _sign_flip_p(values),
            }
        values = pooled[name]
        inference["pooled"][name] = {
            "two_sided_90": _interval(values, 0.90),
            "one_sided_95": _interval(values, 0.95, "lower"),
            "one_sided_98_75_upper": _interval(values, 0.9875, "upper"),
            "exact_two_sided_sign_flip_p": _sign_flip_p(values),
        }

    competence: dict[str, Any] = {}
    competence_ok = True
    seen_equivalence = True
    for schedule in (0, 1):
        uniform = [seed_results[s]["controls"]["UNIFORM"][str(schedule)]["J"] for s in range(8)]
        oracle = [seed_results[s]["controls"]["STATE_ORACLE"][str(schedule)]["J"] for s in range(8)]
        gap = float(np.mean(np.asarray(oracle) - np.asarray(uniform)))
        captures = {}
        for arch in ARCHITECTURES:
            learned = [j(s, arch, "INTACT", schedule) for s in range(8)]
            captures[arch] = float(np.mean(np.asarray(learned) - np.asarray(uniform)) / gap) if gap != 0 else None
        equivalence = _interval([j(s, "RISP", "INTACT", schedule) - j(s, "SIGN_RNN", "INTACT", schedule) for s in range(8)], 0.90)
        ok = gap >= 0.10 and captures["SIGN_RNN"] is not None and captures["RISP"] is not None and captures["SIGN_RNN"] >= 0.20 and captures["RISP"] <= 0.95 and captures["SIGN_RNN"] <= 0.95
        competence_ok &= ok
        seen_equivalence &= equivalence["lower"] >= -0.02 and equivalence["upper"] <= 0.02
        competence[SCHEDULE_LABELS[schedule]] = {"Gap": gap, "Capture": captures, "SIGN_RNN_competence_and_headroom": ok, "RISP_minus_SIGN_RNN_two_sided_90": equivalence}

    validity_conditions: dict[str, Any] = {
        "lock1_passed_before_activity": lock1.get("certificate_result") == "PASS" and lock1.get("scientific_activity_started") is False,
        "complete_eight_seed_panel": len(seed_results) == 8,
        "parameter_parity_117": all(all(seed_results[s]["checkpoints"][a]["learned_scalars"] == 117 for a in ARCHITECTURES) for s in range(8)),
        "lock1_containment_identity_passed": lock1.get("checks", {}).get("containment_and_action_reachability") is not None,
        "lock1_no_leakage_dependency_sentinel_passed": lock1.get("checks", {}).get("marginal_twin_no_leakage", {}).get("controller_visible_fields_identical") is True,
        "residual_sign_identity": all(_aggregate_counter(items, "residual_sign_errors") == 0 for items in accumulators.values()),
        "terminal_recipient_residual_diagnostics_complete": all(all(item.terminal_residual_diagnostics == 64 * 2 for item in items) for items in accumulators.values()),
        "zero_sign_rate_exactly_zero": all(_aggregate_counter(items, "zero_signs") == 0 for items in accumulators.values()),
        "common_support_floor": all(min(item.support_min for item in items) > 1 / 21 for items in accumulators.values()),
        "mechanism_exercised_every_target_cell": all(all(item.mechanism_read for item in accumulators[(arch, feedback, schedule)]) for arch in ARCHITECTURES for feedback in FEEDBACKS for schedule in TARGET_SCHEDULES),
        "sign_rnn_seen_competence": competence_ok,
        "final_checkpoints_frozen": all(all(seed_results[s]["checkpoints"][a]["slow_parameters_frozen_before_evaluation"] for a in ARCHITECTURES) for s in range(8)),
        "all_16_checkpoints_frozen_before_any_evaluation": all(seed_results[s].get("all_16_checkpoints_frozen_before_any_evaluation") is True for s in range(8)),
    }
    eligibility: dict[str, float] = {}
    projection: dict[str, float] = {}
    tv: dict[str, float] = {}
    for arch in ARCHITECTURES:
        for feedback in FEEDBACKS:
            items = [item for schedule in TARGET_SCHEDULES for item in accumulators[(arch, feedback, schedule)]]
            frac_e = _aggregate_counter(items, "eligibility_gt_005") / max(1, _aggregate_counter(items, "nonzero_sign_packets"))
            frac_p = _aggregate_counter(items, "projection_active") / max(1, _aggregate_counter(items, "updates"))
            eligibility[f"{arch}:{feedback}"] = frac_e
            projection[f"{arch}:{feedback}"] = frac_p
            validity_conditions[f"eligibility_{arch}_{feedback}"] = frac_e >= 0.95
            validity_conditions[f"projection_{arch}_{feedback}"] = frac_p < 0.10
        intact_items = [item for schedule in TARGET_SCHEDULES for item in accumulators[(arch, "INTACT", schedule)]]
        frac_tv = _aggregate_counter(intact_items, "tv_ge_0005") / max(1, _aggregate_counter(intact_items, "tv_rows"))
        tv[arch] = frac_tv
        validity_conditions[f"tv_update_{arch}"] = frac_tv >= 0.25

    yoke: dict[str, Any] = {}
    yoke_ok = True
    for arch in ARCHITECTURES:
        yoke[arch] = {}
        for schedule in TARGET_SCHEDULES:
            items = accumulators[(arch, "MARGINAL_TWIN", schedule)]
            pbar_ok = min(item.pbar_min for item in items) >= 0.25 and max(item.pbar_max for item in items) <= 0.75
            sign_ok = True
            discord_ok = True
            recipient_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            twin_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            discord_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            for item in items:
                for key, counts in item.recipient_sign_counts.items():
                    recipient_counts[key][0] += counts[0]; recipient_counts[key][1] += counts[1]
                for key, counts in item.twin_sign_counts.items():
                    twin_counts[key][0] += counts[0]; twin_counts[key][1] += counts[1]
                for key, counts in item.discordance_counts.items():
                    discord_counts[key][0] += counts[0]; discord_counts[key][1] += counts[1]
            relevant_k = {row[1] for row in schedule_rows(schedule)}
            expected_action_strata = {f"{duration}:{action}" for duration in relevant_k for action in range(3)}
            expected_match_strata = {f"{duration}:{match}" for duration in relevant_k for match in (0, 1)}
            strata_complete = set(recipient_counts) == expected_action_strata and set(twin_counts) == expected_action_strata and set(discord_counts) == expected_match_strata
            for collection in (recipient_counts, twin_counts):
                for key in expected_action_strata:
                    counts = collection.get(key, [0, 0])
                    total = sum(counts)
                    sign_ok &= total > 0 and min(counts) / total >= 0.10
            for key in expected_match_strata:
                discordant, total = discord_counts.get(key, [0, 0])
                rate = discordant / total if total else math.nan
                discord_ok &= total > 0 and 0.20 <= rate <= 0.80
            expected_rows = 8 * 64 * 2 * EXPECTED_UPDATES[schedule]
            counts_ok = sum(item.twin_rows for item in items) == expected_rows
            zero_sign_ok = sum(item.zero_signs for item in items) == 0
            cell_ok = pbar_ok and strata_complete and sign_ok and discord_ok and counts_ok and zero_sign_ok
            yoke_ok &= cell_ok
            yoke[arch][SCHEDULE_LABELS[schedule]] = {"pbar_bounds": pbar_ok, "expected_action_strata": sorted(expected_action_strata), "expected_match_strata": sorted(expected_match_strata), "all_expected_strata_present": strata_complete, "both_sign_probabilities_ge_0_10": sign_ok, "discordance_in_0_20_0_80": discord_ok, "zero_sign_rate_exactly_zero": zero_sign_ok, "eligible_count_exact": counts_ok, "passed": cell_ok}
    validity_conditions["feedback_integrity"] = yoke_ok

    call_counts = sampler.calls
    aggregate_calls = {
        "INIT": call_counts["INIT"],
        "ACTION": call_counts["ACTION"] + call_counts["FORK_ACTION"],
        "Y": call_counts["Y"] + call_counts["FORK_Y"],
        "ALT": call_counts["ALT"] + call_counts["FORK_ALT"],
        "TWIN": call_counts["TWIN"],
    }
    ledger_ok = (
        all(call_counts[name] == expected for name, expected in EXPECTED_BASE_CALLS.items())
        and all(call_counts[name] == expected for name, expected in EXPECTED_FORK_CALLS.items())
        and aggregate_calls == EXPECTED_LEDGER
    )
    evaluation_decisions = sum(item.decisions for items in accumulators.values() for item in items)
    evaluation_updates = sum(item.updates for items in accumulators.values() for item in items)
    control_decisions = sum(seed_result["controls"][controller][str(schedule)]["decisions"] for seed_result in seed_results for controller in ("UNIFORM", "STATE_ORACLE") for schedule in range(5))
    training_decisions = call_counts["ACTION"] - evaluation_decisions - control_decisions
    training_updates = 8 * 2 * 256 * 2 * (8 * 47 + 8 * 23)
    count_summary = {
        "training_decisions": training_decisions,
        "training_updates": training_updates,
        "evaluation_decisions": evaluation_decisions,
        "evaluation_updates": evaluation_updates,
        "control_decisions": control_decisions,
        "twin_calls": call_counts["TWIN"],
        "fork_action_calls": call_counts["FORK_ACTION"],
        "base_agent_ticks": 31_064_064,
        "fork_agent_ticks": 114_688,
        "total_agent_ticks_with_forks": 31_178_752,
    }
    published_counts_ok = count_summary == {
        "training_decisions": 4_718_592,
        "training_updates": 4_587_520,
        "evaluation_decisions": 622_592,
        "evaluation_updates": 602_112,
        "control_decisions": 311_296,
        "twin_calls": 301_056,
        "fork_action_calls": 12_288,
        "base_agent_ticks": 31_064_064,
        "fork_agent_ticks": 114_688,
        "total_agent_ticks_with_forks": 31_178_752,
    }
    validity_conditions["exact_categorical_call_ledger"] = ledger_ok
    validity_conditions["complete_episode_decision_update_counts"] = published_counts_ok
    all_valid = all(bool(value) for value in validity_conditions.values())

    pooled_di = inference["pooled"]["D_I"]
    pooled_dm = inference["pooled"]["D_M"]
    pooled_psi = inference["pooled"]["Psi"]
    pooled_cr = inference["pooled"]["C_R"]
    harm = pooled_di["one_sided_98_75_upper"]["upper"] < -0.020 or any(inference["schedule"]["D_I"][SCHEDULE_LABELS[r]]["one_sided_98_75_upper"]["upper"] < -0.030 for r in TARGET_SCHEDULES)
    simultaneous_noninferior = all(inference["schedule"]["D_I"][SCHEDULE_LABELS[r]]["one_sided_98_333_lower"]["lower"] > -0.010 for r in TARGET_SCHEDULES)
    dm_equiv = pooled_dm["two_sided_90"]["lower"] >= -0.010 and pooled_dm["two_sided_90"]["upper"] <= 0.010
    advantage = all_valid and pooled_di["one_sided_95"]["lower"] > 0.020 and pooled_psi["one_sided_95"]["lower"] > 0.015 and pooled_cr["one_sided_95"]["lower"] > 0.015 and simultaneous_noninferior and dm_equiv
    interaction_failure = pooled_psi["one_sided_95"]["lower"] <= 0.015 or pooled_cr["one_sided_95"]["lower"] <= 0.015 or not dm_equiv
    intact_value = all_valid and pooled_di["one_sided_95"]["lower"] > 0.020 and interaction_failure
    no_minimum = all_valid and competence_ok and pooled_di["two_sided_90"]["lower"] >= -0.010 and pooled_di["two_sided_90"]["upper"] <= 0.010 and pooled_psi["two_sided_90"]["lower"] >= -0.010 and pooled_psi["two_sided_90"]["upper"] <= 0.010
    if not all_valid:
        primary = "INVALID_OR_NONIDENTIFYING"
    elif harm:
        primary = "MATERIAL_HARM"
    elif advantage:
        primary = "REALIZED_SIGN_COUPLED_EXPLICIT_ANCHOR_ADVANTAGE"
    elif intact_value:
        primary = "INTACT_PACKAGE_VALUE_WITHOUT_REGISTERED_COUPLING_INTERACTION"
    elif no_minimum:
        primary = "NO_REGISTERED_MINIMUM_BENEFIT_OF_EXPLICIT_SCORE_ANCHOR"
    else:
        primary = "STATISTICALLY_UNRESOLVED"

    pooled_cg = inference["pooled"]["C_G"]
    both_feedback = all_valid and pooled_cr["one_sided_95"]["lower"] > 0.015 and pooled_cg["one_sided_95"]["lower"] > 0.015 and pooled_psi["two_sided_90"]["lower"] >= -0.010 and pooled_psi["two_sided_90"]["upper"] <= 0.010
    bidirectional = all_valid and all(inference["schedule"]["D_I"][label]["one_sided_97_5_lower"]["lower"] > 0 for label in ("4->12", "12->4"))
    return {
        "validity": {"all_conditions_pass": all_valid, "conditions": validity_conditions, "eligibility_fractions": eligibility, "projection_fractions": projection, "tv_update_fractions": tv, "yoke": yoke, "competence": competence, "seen_schedule_equivalence_for_narrow_ood_reading": seen_equivalence},
        "observed_counts": count_summary,
        "inference": inference,
        "disposition": {"primary": primary, "secondary_labels": [label for label, passed in (("BOTH_ARCHITECTURES_FAVOR_REALIZED_SIGN_REGIME", both_feedback), ("BIDIRECTIONAL_POSTFEEDBACK_POSITIVE", bidirectional)) if passed], "narrow_ood_finite_budget_prior_reading": primary == "REALIZED_SIGN_COUPLED_EXPLICIT_ANCHOR_ADVANTAGE" and seen_equivalence},
    }


def _lock1_artifact(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    required = artifact.get("schema") == LOCK1_SCHEMA and artifact.get("science_revision") == SCIENCE_REVISION and artifact.get("certificate_result") == "PASS" and artifact.get("all_required_structural_fixtures_passed") is True and artifact.get("scientific_activity_started") is False and artifact.get("registered_stochastic_object_created") is False
    if not required:
        raise RuntimeError("retained exact revision-07 Lock-1 artifact is not a preactivity PASS")
    return artifact


def _refuse_stale_artifacts(output: Path, checkpoint_dir: Path, activity_marker: Path, incomplete_receipt: Path) -> None:
    targets = (output, checkpoint_dir, activity_marker, incomplete_receipt)
    stale = [str(path) for path in targets if path.exists()]
    for path in (output, activity_marker, incomplete_receipt):
        temporary = path.with_name(path.name + ".tmp")
        if temporary.exists():
            stale.append(str(temporary))
    if checkpoint_dir.parent.exists():
        stale.extend(str(path) for path in checkpoint_dir.parent.glob(checkpoint_dir.name + "*.tmp"))
    if stale:
        raise FileExistsError("one-attempt Lock-2 refuses stale result/checkpoint/activity/incomplete artifacts: " + ", ".join(sorted(set(stale))))


def run_lock2(output: Path, checkpoint_dir: Path, lock1_path: Path, activity_marker: Path, incomplete_receipt: Path, launch_started: float) -> dict[str, Any]:
    guard = ResourceGuard(started=launch_started)
    activity_started = False
    lock1: dict[str, Any] | None = None
    audit = SamplerAudit()
    seed_results: list[dict[str, Any]] = []
    accumulators: dict[tuple[str, str, int], list[EvalAccumulator]] = defaultdict(list)
    try:
        # Preactivity gate order is fixed: validate retained Lock-1, then refuse
        # every artifact that could indicate an earlier attempt.
        lock1 = _lock1_artifact(lock1_path)
        _refuse_stale_artifacts(output, checkpoint_dir, activity_marker, incomplete_receipt)
        for parent in {output.parent, checkpoint_dir.parent, activity_marker.parent, incomplete_receipt.parent}:
            parent.mkdir(parents=True, exist_ok=True)
        guard.check("preactivity_resource_gate", phase="preactivity_gate")
        checkpoint_dir.mkdir(parents=False, exist_ok=False)
        marker_payload = {
            "schema": "RISP-B1-LOCK2-ACTIVITY-MARKER-20260813-07",
            "science_revision": SCIENCE_REVISION,
            "scientific_activity_started": True,
            "one_attempt_only": True,
            "boundary": "immediately before first PCG64 initialization-family object for seed zero",
            "lock1_path": str(lock1_path.resolve()),
            "lock1_sha256": hashlib.sha256(lock1_path.read_bytes()).hexdigest(),
            "created_unix_seconds": time.time(),
        }
        _atomic_write_json(activity_marker, marker_payload)
        activity_started = True
        guard.frontier = {"phase": "activity_boundary_committed", "next": "seed_0_initialization"}

        # Phase 1: this is the first registered stochastic object and immediately
        # follows the durable marker. Train/freeze/save all 16 checkpoints before
        # any evaluation, while retaining a serial one-seed live lifecycle.
        for seed in range(8):
            initialization = materialize_initialization(seed)
            guard.check("initialization_materialized", phase="training", seed=seed, initialization_words=100)
            seed_result: dict[str, Any] = {"seed": seed, "training": {}, "checkpoints": {}, "cells": {}, "controls": {}}
            for architecture in ARCHITECTURES:
                model = RISPModel(initialization, architecture)
                seed_result["training"][architecture] = train_model(model, seed, audit, guard)
                model.eval()
                for parameter in model.parameters():
                    parameter.requires_grad_(False)
                checkpoint_path = checkpoint_dir / f"seed_{seed}_{architecture}.npz"
                seed_result["checkpoints"][architecture] = _save_checkpoint(model, checkpoint_path)
                guard.check("checkpoint_retained", phase="checkpoint", seed=seed, architecture=architecture, checkpoint=str(checkpoint_path.resolve()))
                del model
            seed_results.append(seed_result)
            guard.check("training_seed_checkpoints_complete", phase="checkpoint", completed_training_seed=seed, retained_checkpoint_count=2 * (seed + 1))
            del initialization

        expected_checkpoint_names = {f"seed_{seed}_{architecture}.npz" for seed in range(8) for architecture in ARCHITECTURES}
        retained_checkpoint_names = {path.name for path in checkpoint_dir.glob("*.npz")}
        if retained_checkpoint_names != expected_checkpoint_names:
            raise RuntimeError("all 16 frozen seed-by-architecture checkpoints were not retained before evaluation")
        for seed_result in seed_results:
            seed_result["all_16_checkpoints_frozen_before_any_evaluation"] = True
        guard.check("all_checkpoints_before_any_evaluation", phase="checkpoint_barrier", retained_checkpoint_count=16)

        # Phase 2: load one seed's frozen pair deterministically, evaluate it,
        # then discard it before loading the next seed. No RNG is used to load.
        for seed in range(8):
            seed_result = seed_results[seed]
            models: dict[str, RISPModel] = {}
            for architecture in ARCHITECTURES:
                checkpoint_info = seed_result["checkpoints"][architecture]
                model = _load_frozen_checkpoint(Path(checkpoint_info["path"]), architecture, checkpoint_info["sha256"])
                models[architecture] = model
                guard.check("frozen_checkpoint_loaded_for_evaluation", phase="evaluation_load", seed=seed, architecture=architecture, all_16_checkpoints_preexisted=True)
            for architecture, model in models.items():
                seed_result["cells"][architecture] = {}
                for feedback in FEEDBACKS:
                    seed_result["cells"][architecture][feedback] = {}
                    for schedule in range(5):
                        result, accumulator = evaluate_cell(model, seed, schedule, feedback, audit, guard)
                        seed_result["cells"][architecture][feedback][str(schedule)] = result
                        accumulators[(architecture, feedback, schedule)].append(accumulator)
                        guard.check("evaluation_cell_retained", phase="evaluation", seed=seed, architecture=architecture, feedback=feedback, completed_schedule_id=schedule)
            for controller in ("UNIFORM", "STATE_ORACLE"):
                seed_result["controls"][controller] = {}
                for schedule in range(5):
                    seed_result["controls"][controller][str(schedule)] = evaluate_control(seed, schedule, controller, audit, guard)
                    guard.check("control_schedule_retained", phase="control", seed=seed, controller=controller, completed_schedule_id=schedule)
            for architecture in ARCHITECTURES:
                for feedback in FEEDBACKS:
                    for schedule in range(5):
                        cell = seed_result["cells"][architecture][feedback][str(schedule)]
                        oracle_j = seed_result["controls"]["STATE_ORACLE"][str(schedule)]["J"]
                        cell["physical_time_regret_to_state_oracle_J"] = oracle_j - cell["J"]
            guard.check("evaluation_seed_complete", phase="evaluation_seed_complete", completed_evaluation_seed=seed)
            del models

        guard.check("complete_panel_before_analysis", phase="analysis", completed_seeds=8)
        analysis = analyse(seed_results, accumulators, audit, lock1)
        elapsed, peak_rss = guard.require_finalization_headroom("analysis_complete")
        sampler_audit = audit.result()
        result = {
            "schema": LOCK2_SCHEMA,
            "science_revision": SCIENCE_REVISION,
            "activity": {"scientific_activity_started": True, "boundary": "first PCG64 initialization-family object for seed zero", "activity_marker": str(activity_marker.resolve()), "complete_panel_retained": True, "one_attempt_only": True},
            "lock1": {"path": str(lock1_path.resolve()), "sha256": hashlib.sha256(lock1_path.read_bytes()).hexdigest(), "passed_before_activity": True},
            "execution_order": {"phase_1": "train_freeze_atomic_save_all_8x2_checkpoints_serially_by_seed", "checkpoint_barrier_count": 16, "phase_2": "deterministically_load_one_frozen_seed_pair_then_evaluate_and_discard", "any_evaluation_before_checkpoint_barrier": False},
            "frozen_panel": {"algorithm_seeds": list(range(8)), "architectures": list(ARCHITECTURES), "feedbacks": list(FEEDBACKS), "schedules": SCHEDULE_LABELS, "training_updates": 256, "batch_size": 16, "training_k": [4, 8], "evaluation_episodes_per_cell": 64, "optimizer": {"name": "AdamW", "learning_rate": 3e-4, "betas": [0.9, 0.999], "epsilon": 1e-8, "decoupled_weight_decay": 1e-4, "global_gradient_clip": 1.0}, "processes": 1, "cpu_threads": 1, "gpu_visible": False},
            "sampler_audit": {**sampler_audit, "initialization_family_raw_words": 800, "all_registered_raw_words_including_initialization": sampler_audit["total_raw_words"] + 800},
            "seed_results": seed_results,
            "analysis": analysis,
            "runtime": {"wall_seconds": elapsed, "wall_below_60_minutes": True, "wall_limit_seconds": guard.wall_limit_seconds, "peak_rss_bytes": peak_rss, "peak_rss_below_1_gib": True, "rss_limit_bytes": guard.rss_limit_bytes, "active_in_process_guard": True},
            "anomalies": [],
        }
        # Serialize before the last resource decision; no final result path exists
        # unless active limits and conservative durable-write headroom still pass.
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
        elapsed, peak_rss = guard.require_finalization_headroom("result_payload_validated")
        result["runtime"]["wall_seconds"] = elapsed
        result["runtime"]["peak_rss_bytes"] = peak_rss
        encoded_result = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
        guard.require_finalization_headroom("result_payload_serialized")
        _atomic_write_bytes(output, encoded_result)
        return result
    except BaseException as exc:
        if activity_started:
            receipt = {
                "schema": "RISP-B1-LOCK2-INCOMPLETE-20260813-07",
                "science_revision": SCIENCE_REVISION,
                "scientific_activity_started": True,
                "complete_panel_retained": False,
                "activity_marker": str(activity_marker.resolve()),
                "reason_kind": "RESOURCE_LIMIT" if isinstance(exc, ResourceLimitExceeded) else "POSTACTIVITY_EXCEPTION",
                "exception_type": type(exc).__name__,
                "reason": str(exc),
                "elapsed_seconds": guard.elapsed(),
                "peak_rss_bytes": _peak_rss_or_none(),
                "completed_frontier": guard.frontier,
                "partial_atomic_checkpoints": sorted(str(path.resolve()) for path in checkpoint_dir.glob("*.npz")) if checkpoint_dir.exists() else [],
                "result_written": output.exists(),
            }
            _atomic_write_json(incomplete_receipt, receipt)
        raise
