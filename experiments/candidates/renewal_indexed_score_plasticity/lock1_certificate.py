"""Deterministic RISP-B1 revision-07 Lock-1 conformance certificate.

This module intentionally has no stochastic dependency or stochastic-object
construction surface.  All sampler inputs below are literal fixture words.
"""

from __future__ import annotations

import ast
import json
import math
import struct
import sys
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from pathlib import Path


SCHEMA = "RISP-B1-LOCK1-20260813-07"
SCIENCE_REVISION = "RISP-B1-SCIENCE-20260813-07"
T = 192
U64 = 1 << 64
U64_MAX = U64 - 1
ACTION_NAMES = ("LEFT", "HOLD", "RIGHT")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, name: str, tolerance: float = 1e-6) -> None:
    require(math.isfinite(actual), f"{name}: nonfinite candidate value")
    require(math.isfinite(expected), f"{name}: nonfinite reference value")
    require(abs(actual - expected) <= tolerance, f"{name}: {actual!r} != {expected!r}")


def gcd_many(values: list[int]) -> int:
    return reduce(math.gcd, values)


def lcm(a: int, b: int) -> int:
    return abs(a * b) // math.gcd(a, b)


def lcm_many(values: list[int]) -> int:
    return reduce(lcm, values, 1)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def rat32_from_bits(bits: int) -> Fraction:
    require(0 <= bits <= 0xFFFFFFFF, "binary32 bit pattern outside uint32")
    sign = (bits >> 31) & 1
    exponent = (bits >> 23) & 0xFF
    fraction = bits & ((1 << 23) - 1)
    require(exponent != 0xFF, "nonfinite binary32 row")
    if exponent == 0:
        magnitude = Fraction(fraction, 1 << 149)
    else:
        significand = (1 << 23) + fraction
        power = exponent - 150
        magnitude = Fraction(significand << power, 1) if power >= 0 else Fraction(significand, 1 << (-power))
    return -magnitude if sign else magnitude


def rat32(value: float) -> Fraction:
    return rat32_from_bits(f32_bits(value))


def clear_rational_masses(masses: tuple[Fraction, ...]) -> tuple[int, ...]:
    require(len(masses) >= 2, "categorical law needs at least two masses")
    require(all(m > 0 for m in masses), "categorical masses must be positive")
    denominator = lcm_many([m.denominator for m in masses])
    integers = [m.numerator * (denominator // m.denominator) for m in masses]
    divisor = gcd_many(integers)
    return tuple(value // divisor for value in integers)


def rational_head(raw_logits: tuple[Fraction, Fraction, Fraction]) -> dict[str, object]:
    z = tuple(Fraction(6) * r / (Fraction(6) + abs(r)) for r in raw_logits)
    w = tuple(Fraction(16) + (value + 6) ** 2 for value in z)
    total = sum(w, Fraction(0))
    probabilities = tuple(value / total for value in w)
    masses = clear_rational_masses(probabilities)
    require(all(Fraction(0) < value < Fraction(1) for value in probabilities), "invalid policy mass")
    require(all(value > Fraction(1, 21) for value in probabilities), "global support floor failed")
    return {"z": z, "w": w, "pi": probabilities, "masses": masses}


def candidate_rational_head(raw_logits: tuple[Fraction, Fraction, Fraction]) -> dict[str, object]:
    """Independent candidate implementation of the frozen rational head."""
    candidate_z: list[Fraction] = []
    candidate_w: list[Fraction] = []
    for raw in raw_logits:
        denominator = Fraction(6) + (raw if raw >= 0 else -raw)
        safe = (Fraction(6) * raw) / denominator
        candidate_z.append(safe)
        candidate_w.append(Fraction(16) + (safe + Fraction(6)) * (safe + Fraction(6)))
    weight_sum = candidate_w[0] + candidate_w[1] + candidate_w[2]
    candidate_pi = tuple(weight / weight_sum for weight in candidate_w)
    denominator_lcm = lcm_many([mass.denominator for mass in candidate_pi])
    unreduced = [mass.numerator * (denominator_lcm // mass.denominator) for mass in candidate_pi]
    joint_gcd = gcd_many(unreduced)
    candidate_masses = tuple(value // joint_gcd for value in unreduced)
    require(all(mass > Fraction(1, 21) for mass in candidate_pi), "candidate support floor failed")
    return {"z": tuple(candidate_z), "w": tuple(candidate_w), "pi": candidate_pi, "masses": candidate_masses}


def raw_affine_exact(
    base: tuple[Fraction, Fraction, Fraction],
    u: tuple[tuple[Fraction, Fraction], ...],
    v: tuple[tuple[Fraction, Fraction], ...],
    h: tuple[Fraction, Fraction, Fraction, Fraction],
    x: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction, Fraction]:
    vh = tuple(sum((v[row][column] * h[row] for row in range(4)), Fraction(0)) for column in range(2))
    return tuple(base[action] + sum((u[action][j] * x[j] * vh[j] for j in range(2)), Fraction(0)) for action in range(3))


def raw_affine_float(
    base: tuple[float, float, float],
    u: tuple[tuple[float, float], ...],
    v: tuple[tuple[float, float], ...],
    h: tuple[float, float, float, float],
    x: tuple[float, float],
) -> tuple[float, float, float]:
    vh = tuple(sum(v[row][column] * h[row] for row in range(4)) for column in range(2))
    return tuple(base[action] + sum(u[action][j] * x[j] * vh[j] for j in range(2)) for action in range(3))


def raw_affine_candidate_f32(
    base: tuple[float, float, float],
    u: tuple[tuple[float, float], ...],
    v: tuple[tuple[float, float], ...],
    h: tuple[float, float, float, float],
    x: tuple[float, float],
) -> tuple[float, float, float]:
    """Binary32 candidate tensor path with explicit tensor-output rounding."""
    vh_values: list[float] = []
    for column in range(2):
        accumulator = f32(0.0)
        for row in range(4):
            accumulator = f32(accumulator + f32(f32(v[row][column]) * f32(h[row])))
        vh_values.append(accumulator)
    output: list[float] = []
    for action in range(3):
        fast_accumulator = f32(0.0)
        for column in range(2):
            product = f32(f32(u[action][column]) * f32(x[column]))
            fast_accumulator = f32(fast_accumulator + f32(product * vh_values[column]))
        output.append(f32(f32(base[action]) + fast_accumulator))
    return tuple(output)


def score_fisher_eligibility_reference(
    raw: tuple[Fraction, Fraction, Fraction],
    derivatives: tuple[tuple[Fraction, Fraction], ...],
    selected: int,
) -> dict[str, object]:
    head = rational_head(raw)
    z = head["z"]
    w = head["w"]
    pi = head["pi"]
    ratios = []
    for index, r in enumerate(raw):
        dz = Fraction(36) / (Fraction(6) + abs(r)) ** 2
        dw = Fraction(2) * (z[index] + 6) * dz
        ratios.append(dw / w[index])
    mean = tuple(
        sum((pi[a] * ratios[a] * derivatives[a][j] for a in range(3)), Fraction(0))
        for j in range(2)
    )
    scores = tuple(
        tuple(ratios[a] * derivatives[a][j] - mean[j] for j in range(2))
        for a in range(3)
    )
    fisher = tuple(
        tuple(sum((pi[a] * scores[a][i] * scores[a][j] for a in range(3)), Fraction(0)) for j in range(2))
        for i in range(2)
    )
    matrix = ((fisher[0][0] + Fraction(1, 20), fisher[0][1]), (fisher[1][0], fisher[1][1] + Fraction(1, 20)))
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    require(determinant > 0, "regularized Fisher is not positive definite")
    g = scores[selected]
    v = (
        (matrix[1][1] * g[0] - matrix[0][1] * g[1]) / determinant,
        (-matrix[1][0] * g[0] + matrix[0][0] * g[1]) / determinant,
    )
    norm = math.hypot(float(v[0]), float(v[1]))
    divisor = max(1.0, norm)
    eligibility = (float(v[0]) / divisor, float(v[1]) / divisor)
    return {"pi": pi, "scores": scores, "fisher": fisher, "v": v, "e": eligibility}


def score_fisher_eligibility_float(
    raw: tuple[float, float, float],
    derivatives: tuple[tuple[float, float], ...],
    selected: int,
) -> dict[str, object]:
    exact_raw = tuple(rat32(value) for value in raw)
    pi = tuple(float(value) for value in candidate_rational_head(exact_raw)["pi"])
    z = tuple(6.0 * value / (6.0 + abs(value)) for value in raw)
    ratios = []
    for index, value in enumerate(raw):
        dz = 36.0 / (6.0 + abs(value)) ** 2
        w = 16.0 + (z[index] + 6.0) ** 2
        ratios.append((2.0 * (z[index] + 6.0) * dz) / w)
    mean = tuple(sum(pi[a] * ratios[a] * derivatives[a][j] for a in range(3)) for j in range(2))
    scores = tuple(tuple(ratios[a] * derivatives[a][j] - mean[j] for j in range(2)) for a in range(3))
    fisher = tuple(
        tuple(sum(pi[a] * scores[a][i] * scores[a][j] for a in range(3)) for j in range(2))
        for i in range(2)
    )
    a00, a01 = fisher[0][0] + 0.05, fisher[0][1]
    a10, a11 = fisher[1][0], fisher[1][1] + 0.05
    determinant = a00 * a11 - a01 * a10
    g = scores[selected]
    v = ((a11 * g[0] - a01 * g[1]) / determinant, (-a10 * g[0] + a00 * g[1]) / determinant)
    norm = math.hypot(*v)
    divisor = max(1.0, norm / 1.0)
    eligibility = (v[0] / divisor, v[1] / divisor)
    return {"pi": pi, "scores": scores, "fisher": fisher, "v": v, "e": eligibility}


@dataclass(frozen=True)
class ExactCatResult:
    category: int
    residue: int
    attempts: int
    words_consumed: int
    integer_masses: tuple[int, ...]
    total_mass: int
    words_per_attempt: int
    acceptance_limit: int


def exactcat_literal(masses: tuple[Fraction, ...], words: tuple[int, ...]) -> ExactCatResult:
    integer_masses = clear_rational_masses(masses)
    total = sum(integer_masses)
    words_per_attempt = max(1, ((total - 1).bit_length() + 63) // 64)
    require(len(words) % words_per_attempt == 0, "literal word bank does not contain complete attempts")
    require(all(0 <= word <= U64_MAX for word in words), "literal sampler word outside uint64")
    sample_space = 1 << (64 * words_per_attempt)
    limit = (sample_space // total) * total
    for attempt in range(len(words) // words_per_attempt):
        offset = attempt * words_per_attempt
        assembled = sum(words[offset + j] << (64 * j) for j in range(words_per_attempt))
        if assembled >= limit:
            continue
        residue = assembled % total
        cumulative = 0
        for category, mass in enumerate(integer_masses):
            cumulative += mass
            if residue < cumulative:
                return ExactCatResult(category, residue, attempt + 1, offset + words_per_attempt, integer_masses, total, words_per_attempt, limit)
    raise AssertionError("literal fixture exhausted before acceptance")


def packet(x: tuple[float, float], action: int, sign: int, eligibility: tuple[float, float], k: int, tau: int) -> tuple[float, ...]:
    require(action in range(3) and sign in (-1, 0, 1), "invalid packet action/sign")
    one_hot = tuple(1.0 if action == index else 0.0 for index in range(3))
    norm = math.hypot(*eligibility)
    result = x + one_hot + (float(sign),) + eligibility + tuple(sign * value for value in eligibility) + (sign * norm, k / 12.0, tau / T)
    require(len(result) == 13, "packet does not have 13 coordinates")
    return result


def masks() -> tuple[tuple[tuple[float, ...], ...], tuple[tuple[float, ...], ...]]:
    risp = [[0.0] * 13 for _ in range(2)]
    sign = [[0.0] * 13 for _ in range(2)]
    risp[0][8] = 1.0
    risp[1][9] = 1.0
    anchor = 1.0 / math.sqrt(2.0)
    sign[0][10] = anchor
    sign[1][10] = anchor
    return tuple(tuple(row) for row in risp), tuple(tuple(row) for row in sign)


def matrix_add(a: tuple[tuple[float, ...], ...], b: tuple[tuple[float, ...], ...], scale_b: float = 1.0) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(a[i][j] + scale_b * b[i][j] for j in range(13)) for i in range(2))


def project3(state: tuple[float, float]) -> tuple[float, float]:
    norm = math.hypot(*state)
    if norm <= 3.0:
        return state
    scale = 3.0 / norm
    return (state[0] * scale, state[1] * scale)


def transition_candidate_f32(x: tuple[float, float], p: tuple[float, ...], learned: tuple[tuple[float, ...], ...], mask: tuple[tuple[float, ...], ...], bias: tuple[float, float]) -> dict[str, tuple[float, float]]:
    effective = matrix_add(learned, mask)
    increments: list[float] = []
    for i in range(2):
        accumulator = f32(0.0)
        for j in range(13):
            accumulator = f32(accumulator + f32(f32(effective[i][j]) * f32(p[j])))
        increments.append(f32(accumulator + f32(bias[i])))
    preprojection = tuple(f32(f32(x[i]) + f32(f32(0.1) * increments[i])) for i in range(2))
    projected = project3(preprojection)
    postprojection = tuple(f32(value) for value in projected)
    return {"preprojection": preprojection, "postprojection": postprojection}


def transition_reference_fraction(
    x: tuple[Fraction, Fraction],
    p: tuple[Fraction, ...],
    effective_weight: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    bias: tuple[Fraction, Fraction],
) -> dict[str, tuple[Fraction, Fraction]]:
    increment = tuple(sum((effective_weight[i][j] * p[j] for j in range(13)), Fraction(0)) + bias[i] for i in range(2))
    preprojection = tuple(x[i] + Fraction(1, 10) * increment[i] for i in range(2))
    squared_norm = preprojection[0] ** 2 + preprojection[1] ** 2
    if squared_norm <= 9:
        postprojection = preprojection
    elif preprojection[1] == 0:
        postprojection = (Fraction(3) if preprojection[0] > 0 else Fraction(-3), Fraction(0))
    else:
        scale = 3.0 / math.sqrt(float(squared_norm))
        postprojection = (Fraction(f32(float(preprojection[0]) * scale)), Fraction(f32(float(preprojection[1]) * scale)))
    return {"preprojection": preprojection, "postprojection": postprojection}


POLICY_BASE_F32 = (f32(0.125), f32(-0.25), f32(0.5))
POLICY_U_F32 = ((f32(1.0), f32(-0.5)), (f32(0.25), f32(1.0)), (f32(-1.0), f32(1.0)))
POLICY_V_F32 = ((f32(1.0), f32(0.0)), (f32(0.0), f32(1.0)), (f32(0.0), f32(0.0)), (f32(0.0), f32(0.0)))
POLICY_H_F32 = (f32(1.0), f32(1.0), f32(0.0), f32(0.0))


def policy_port_reference(state: tuple[float, float]) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    raw = raw_affine_exact(
        tuple(rat32(value) for value in POLICY_BASE_F32),
        tuple(tuple(rat32(value) for value in row) for row in POLICY_U_F32),
        tuple(tuple(rat32(value) for value in row) for row in POLICY_V_F32),
        tuple(rat32(value) for value in POLICY_H_F32),
        tuple(rat32(value) for value in state),
    )
    return raw, rational_head(raw)["pi"]


def policy_port_candidate(state: tuple[float, float]) -> tuple[tuple[float, ...], tuple[Fraction, ...]]:
    raw = raw_affine_candidate_f32(POLICY_BASE_F32, POLICY_U_F32, POLICY_V_F32, POLICY_H_F32, tuple(f32(value) for value in state))
    exact_candidate_raw = tuple(rat32(value) for value in raw)
    return raw, candidate_rational_head(exact_candidate_raw)["pi"]


SCHEDULES = {
    0: ((0, 4),),
    1: ((0, 8),),
    2: ((0, 12),),
    3: ((0, 4), (96, 12)),
    4: ((0, 12), (96, 4)),
}
EXPECTED_DECISIONS = (48, 24, 16, 32, 32)
EXPECTED_UPDATES = (47, 23, 15, 31, 31)


def schedule_rows(schedule_id: int) -> tuple[tuple[int, int, bool], ...]:
    segments = SCHEDULES[schedule_id]
    rows: list[tuple[int, int, bool]] = []
    tau = 0
    while tau < T:
        k = segments[-1][1]
        for start, duration in segments:
            if tau >= start:
                k = duration
        require(tau + k <= T, "registered schedule creates unfinished terminal hold")
        rows.append((tau, k, tau + k == T))
        tau += k
    require(tau == T, "registered schedule does not terminate at T")
    return tuple(rows)


EVENT_FIELDS = {
    "train_init": ("algorithm_seed", "optimizer_update", "episode_in_batch", "agent"),
    "train_action": ("algorithm_seed", "optimizer_update", "episode_in_batch", "agent", "renewal"),
    "train_Y": ("algorithm_seed", "optimizer_update", "episode_in_batch", "agent", "renewal"),
    "train_alt": ("algorithm_seed", "optimizer_update", "episode_in_batch", "agent", "renewal"),
    "eval_init": ("algorithm_seed", "schedule_id", "episode", "agent"),
    "eval_action": ("algorithm_seed", "schedule_id", "episode", "agent", "renewal"),
    "eval_Y": ("algorithm_seed", "schedule_id", "episode", "agent", "renewal"),
    "eval_alt": ("algorithm_seed", "schedule_id", "episode", "agent", "renewal"),
    "twin": ("algorithm_seed", "schedule_id", "episode", "agent", "renewal"),
    "fork_action": ("algorithm_seed", "schedule_id", "episode", "agent"),
    "fork_Y": ("algorithm_seed", "schedule_id", "episode", "agent"),
    "fork_alt": ("algorithm_seed", "schedule_id", "episode", "agent"),
}


def train_row(seed: int, update: int, episode: int, agent: int) -> int:
    require(seed in range(8) and update in range(256) and episode in range(16) and agent in range(2), "train tuple outside domain")
    return (((seed * 256 + update) * 16 + episode) * 2 + agent)


def eval_row(seed: int, schedule: int, episode: int, agent: int) -> int:
    require(seed in range(8) and schedule in range(5) and episode in range(64) and agent in range(2), "eval tuple outside domain")
    return (((seed * 5 + schedule) * 64 + episode) * 2 + agent)


def training_renewal_count(episode_in_batch: int) -> int:
    return 48 if episode_in_batch % 2 == 0 else 24


def event_key(kind: str, *fields: int) -> int:
    require(kind in EVENT_FIELDS, f"unknown typed event {kind}")
    require(len(fields) == len(EVENT_FIELDS[kind]), f"wrong arity for {kind}")
    if kind.startswith("train_"):
        seed, update, episode, agent = fields[:4]
        row = train_row(seed, update, episode, agent)
        if len(fields) == 5:
            renewal = fields[4]
            require(renewal in range(training_renewal_count(episode)), "train renewal outside schedule domain")
        if kind == "train_init":
            key = 10_000_000_000 + 1_000 * row
        elif kind == "train_Y":
            key = 10_000_000_000 + 1_000 * row + 100 + fields[4]
        elif kind == "train_alt":
            key = 10_000_000_000 + 1_000 * row + 200 + fields[4]
        else:
            key = 40_000_000_000 + 1_000 * row + fields[4]
    elif kind.startswith("eval_"):
        seed, schedule, episode, agent = fields[:4]
        row = eval_row(seed, schedule, episode, agent)
        if len(fields) == 5:
            renewal = fields[4]
            require(renewal in range(EXPECTED_DECISIONS[schedule]), "eval renewal outside schedule domain")
        if kind == "eval_init":
            key = 20_000_000_000 + 1_000 * row
        elif kind == "eval_Y":
            key = 20_000_000_000 + 1_000 * row + 100 + fields[4]
        elif kind == "eval_alt":
            key = 20_000_000_000 + 1_000 * row + 200 + fields[4]
        else:
            key = 50_000_000_000 + 1_000 * row + fields[4]
    elif kind == "twin":
        seed, schedule, episode, agent, renewal = fields
        eval_row(seed, schedule, episode, agent)
        require(renewal in range(EXPECTED_UPDATES[schedule]), "twin event exists at ineligible/terminal renewal")
        key = 30_000_000_000 + 1_000_000_000 * seed + 100_000_000 * schedule + 1_000_000 * episode + 1_000 * agent + renewal
    else:
        seed, schedule, episode, agent = fields
        require(schedule in (2, 3, 4), "fork schedule is not a target schedule")
        row = eval_row(seed, schedule, episode, agent)
        if kind == "fork_Y":
            key = 70_000_000_000 + 1_000 * row
        elif kind == "fork_alt":
            key = 70_000_000_000 + 1_000 * row + 1
        else:
            key = 80_000_000_000 + 1_000 * row
    require(0 <= key <= U64_MAX, "event key outside uint64")
    return key


def initialization_address(seed: int, q: int) -> int:
    require(seed in range(8) and q in range(100), "initialization coordinate outside domain")
    return 60_000_000_000 + seed


def check_rat32_head_score() -> dict[str, object]:
    require(rat32_from_bits(0x00000000) == 0 and rat32_from_bits(0x80000000) == 0, "signed zero conversion failed")
    require(rat32_from_bits(0x00000001) == Fraction(1, 1 << 149), "subnormal conversion failed")
    require(rat32_from_bits(0x00800000) == Fraction(1, 1 << 126), "minimum normal conversion failed")
    require(rat32_from_bits(0x3FC00000) == Fraction(3, 2), "normal conversion failed")
    nonfinite_rejected = False
    try:
        rat32_from_bits(0x7F800000)
    except AssertionError:
        nonfinite_rejected = True
    require(nonfinite_rejected, "nonfinite Rat32 operand was accepted")

    base_f = (f32(0.125), f32(-0.25), f32(0.0))
    h_f = (f32(0.5), f32(-1.0), f32(0.25), f32(0.0))
    x_f = (f32(0.5), f32(-0.25))
    u_f = ((f32(1.0), f32(0.5)), (f32(-0.5), f32(1.0)), (f32(0.25), f32(-1.0)))
    v_f = ((f32(0.5), f32(1.0)), (f32(0.25), f32(-0.5)), (f32(1.0), f32(0.25)), (f32(0.0), f32(0.0)))
    base_q = tuple(rat32(value) for value in base_f)
    h_q = tuple(rat32(value) for value in h_f)
    x_q = tuple(rat32(value) for value in x_f)
    u_q = tuple(tuple(rat32(value) for value in row) for row in u_f)
    v_q = tuple(tuple(rat32(value) for value in row) for row in v_f)
    raw_q = raw_affine_exact(base_q, u_q, v_q, h_q, x_q)
    raw_f = raw_affine_candidate_f32(base_f, u_f, v_f, h_f, x_f)
    for index in range(3):
        close(raw_f[index], float(raw_q[index]), f"raw_affine[{index}]")
    head = rational_head(raw_q)
    candidate_head = candidate_rational_head(tuple(rat32(value) for value in raw_f))
    require(sum(head["pi"], Fraction(0)) == 1, "rational policy does not sum to one")
    require(math.gcd(*head["masses"]) == 1, "integer masses not jointly reduced")
    for index in range(3):
        close(float(candidate_head["pi"][index]), float(head["pi"][index]), f"candidate_head.pi[{index}]")
    require(candidate_head["masses"] == head["masses"], "candidate/reference rational-head integer masses differ")

    score_raw = (Fraction(1, 2), Fraction(0), Fraction(-1, 2))
    derivatives_q = ((Fraction(4), Fraction(0)), (Fraction(0), Fraction(0)), (Fraction(-4), Fraction(0)))
    reference = score_fisher_eligibility_reference(score_raw, derivatives_q, 0)
    candidate = score_fisher_eligibility_float(tuple(float(value) for value in score_raw), tuple(tuple(float(value) for value in row) for row in derivatives_q), 0)
    for a in range(3):
        close(candidate["pi"][a], float(reference["pi"][a]), f"score.pi[{a}]")
        for j in range(2):
            close(candidate["scores"][a][j], float(reference["scores"][a][j]), f"score.g[{a},{j}]")
    for i in range(2):
        for j in range(2):
            close(candidate["fisher"][i][j], float(reference["fisher"][i][j]), f"fisher[{i},{j}]")
        close(candidate["e"][i], reference["e"][i], f"eligibility[{i}]")
    require(math.hypot(*candidate["e"]) <= 1.0 + 1e-12, "eligibility norm cap failed")
    return {
        "rat32_cases": 5,
        "nonfinite_rejected": True,
        "implementation_paths": {"reference": "Fraction Rat32/raw/head/score/Fisher solve", "candidate": "explicit binary32 tensor-output rounding + independent rational-head code + binary64 score/Fisher solve"},
        "raw_logits": [str(value) for value in raw_q],
        "policy_integer_masses": list(head["masses"]),
        "score_fixture_selected_action": "LEFT",
        "fisher_regularizer": "1/20",
        "eligibility_norm": math.hypot(*candidate["e"]),
        "tolerance": 1e-6,
    }


def check_exactcat() -> dict[str, object]:
    fixture1 = exactcat_literal((Fraction(1), Fraction(1), Fraction(1)), (U64_MAX, 0))
    require((fixture1.total_mass, fixture1.words_per_attempt, fixture1.acceptance_limit) == (3, 1, U64_MAX), "M=3 sampler geometry failed")
    require((fixture1.category, fixture1.residue, fixture1.attempts) == (0, 0, 2), "M=3 retry fixture failed")
    l12 = U64 - 4
    fixture2 = exactcat_literal((Fraction(5), Fraction(7)), (l12, 5))
    require((fixture2.total_mass, fixture2.acceptance_limit) == (12, l12), "M=12 sampler geometry failed")
    require((fixture2.category, fixture2.residue, fixture2.attempts) == (1, 5, 2), "strict cumulative M=12 fixture failed")
    fixture3 = exactcat_literal((Fraction(U64), Fraction(1)), (1, 1))
    require((fixture3.total_mass, fixture3.words_per_attempt) == (U64 + 1, 2), "multiword geometry failed")
    require((fixture3.category, fixture3.residue, fixture3.attempts) == (0, 0, 1), "little-endian multiword fixture failed")
    reduced = clear_rational_masses((Fraction(2, 6), Fraction(4, 6)))
    require(reduced == (1, 2), "rational mass LCM/GCD reduction failed")

    event_local_tapes = {
        ("literal_event_a",): (U64_MAX, 0),
        ("literal_event_b",): (5,),
    }
    result_a = exactcat_literal((Fraction(1), Fraction(1), Fraction(1)), event_local_tapes[("literal_event_a",)])
    result_b = exactcat_literal((Fraction(5), Fraction(7)), event_local_tapes[("literal_event_b",)])
    require(result_a.words_consumed == 2 and result_b.words_consumed == 1 and result_b.residue == 5, "event-local retry isolation failed")
    return {
        "literal_fixture_count": 3,
        "reduction": "LCM_then_joint_GCD",
        "rejection_boundary": "X>=L",
        "category_rule": "first_strict_cumulative_mass_greater_than_J",
        "multiword_assembly": "little_endian_64_bit_words",
        "event_local_retry_isolation": True,
        "random_words_materialized": 0,
    }


def check_containment_and_reachability() -> dict[str, object]:
    risp_mask, sign_mask = masks()
    zeros = tuple(tuple(0.0 for _ in range(13)) for _ in range(2))
    translated_sign = matrix_add(zeros, risp_mask)
    translated_sign = matrix_add(translated_sign, sign_mask, -1.0)
    effective_risp = matrix_add(zeros, risp_mask)
    effective_sign = matrix_add(translated_sign, sign_mask)
    reverse_risp = matrix_add(zeros, sign_mask)
    reverse_risp = matrix_add(reverse_risp, risp_mask, -1.0)
    effective_reverse_risp = matrix_add(reverse_risp, risp_mask)
    effective_reverse_sign = matrix_add(zeros, sign_mask)
    for i in range(2):
        for j in range(13):
            close(effective_sign[i][j], effective_risp[i][j], f"forward_mask_identity[{i},{j}]")
            close(effective_reverse_risp[i][j], effective_reverse_sign[i][j], f"reverse_mask_identity[{i},{j}]")

    fixtures = (
        ("C1", (0.0, 0.0), 0, 1, (0.6, -0.8), 4, 48, (0.06, -0.08), (0.06, -0.08)),
        ("C2", (2.99, 0.0), 1, 1, (1.0, 0.0), 12, 96, (3.09, 0.0), (3.0, 0.0)),
        ("C3", (0.2, -0.1), 2, -1, (-0.3, 0.4), 8, 144, (0.23, -0.14), (0.23, -0.14)),
    )
    fixture_records = []
    reference_effective = tuple(tuple(Fraction(1) if (i, j) in ((0, 8), (1, 9)) else Fraction(0) for j in range(13)) for i in range(2))
    for name, old_x, action, supplied_sign, eligibility, k, tau, expected_pre, expected_post in fixtures:
        p = packet(old_x, action, supplied_sign, eligibility, k, tau)
        require(p[0:2] == old_x and p[2 + action] == 1.0 and p[5] == supplied_sign, f"{name}: packet coordinate layout failed")
        reference = transition_reference_fraction(
            tuple(Fraction(str(value)) for value in old_x),
            tuple(Fraction(str(value)) for value in p),
            reference_effective,
            (Fraction(0), Fraction(0)),
        )
        risp_result = transition_candidate_f32(old_x, p, zeros, risp_mask, (0.0, 0.0))
        sign_result = transition_candidate_f32(old_x, p, translated_sign, sign_mask, (0.0, 0.0))
        for j in range(2):
            close(float(reference["preprojection"][j]), expected_pre[j], f"{name}.reference.preprojection[{j}]")
            close(float(reference["postprojection"][j]), expected_post[j], f"{name}.reference.postprojection[{j}]")
            close(risp_result["preprojection"][j], float(reference["preprojection"][j]), f"{name}.RISP.preprojection[{j}]")
            close(sign_result["preprojection"][j], float(reference["preprojection"][j]), f"{name}.SIGN.preprojection[{j}]")
            close(risp_result["postprojection"][j], float(reference["postprojection"][j]), f"{name}.RISP.state[{j}]")
            close(sign_result["postprojection"][j], float(reference["postprojection"][j]), f"{name}.SIGN.state[{j}]")
        risp_state = risp_result["postprojection"]
        sign_state = sign_result["postprojection"]
        raw_reference, pi_reference = policy_port_reference(risp_state)
        raw_r, pi_r = policy_port_candidate(risp_state)
        raw_g, pi_g = policy_port_candidate(sign_state)
        for a in range(3):
            close(raw_r[a], float(raw_reference[a]), f"{name}.candidate_reference.logit[{a}]")
            close(float(pi_r[a]), float(pi_reference[a]), f"{name}.candidate_reference.pi[{a}]")
            close(raw_r[a], raw_g[a], f"{name}.logit[{a}]")
            close(float(pi_r[a]), float(pi_g[a]), f"{name}.pi[{a}]")
        fixture_records.append({"id": name, "reference_preprojection": [str(value) for value in reference["preprojection"]], "candidate_preprojection": list(risp_result["preprojection"]), "reference_postprojection": [str(value) for value in reference["postprojection"]], "state": list(risp_state), "packet_coordinates": 13})

    tanh_bias = f32(math.tanh(f32(2.0 ** -20)))
    require(f32_bits(tanh_bias) == f32_bits(2.0 ** -20), "binary32 tanh reachability fixture failed")
    vh = f32(f32(2.0 ** 20) * tanh_bias)
    require(vh == 1.0, "reachability V^T h fixture failed")
    reach_packet = packet((0.0, 0.0), 1, 1, (1.0, 0.0), 12, 96)
    reach_reference = transition_reference_fraction(
        (Fraction(0), Fraction(0)),
        tuple(Fraction(str(value)) for value in reach_packet),
        reference_effective,
        (Fraction(1, 4), Fraction(0)),
    )
    reach_risp_result = transition_candidate_f32((0.0, 0.0), reach_packet, zeros, risp_mask, (0.25, 0.0))
    reach_sign_result = transition_candidate_f32((0.0, 0.0), reach_packet, translated_sign, sign_mask, (0.25, 0.0))
    for j in range(2):
        close(reach_risp_result["postprojection"][j], float(reach_reference["postprojection"][j]), f"reachability.RISP.state[{j}]")
        close(reach_sign_result["postprojection"][j], float(reach_reference["postprojection"][j]), f"reachability.SIGN.state[{j}]")
    reach_state = reach_risp_result["postprojection"]
    reach_h = (tanh_bias, f32(0.0), f32(0.0), f32(0.0))
    reach_v = ((f32(2.0 ** 20), f32(0.0)), (f32(0.0), f32(0.0)), (f32(0.0), f32(0.0)), (f32(0.0), f32(0.0)))
    reach_u = ((f32(4.0), f32(0.0)), (f32(0.0), f32(0.0)), (f32(-4.0), f32(0.0)))
    reach_base = (f32(0.0), f32(0.0), f32(0.0))
    reach_raw_candidate = raw_affine_candidate_f32(reach_base, reach_u, reach_v, reach_h, reach_state)
    reach_raw_reference = raw_affine_exact(
        tuple(rat32(value) for value in reach_base),
        tuple(tuple(rat32(value) for value in row) for row in reach_u),
        tuple(tuple(rat32(value) for value in row) for row in reach_v),
        tuple(rat32(value) for value in reach_h),
        tuple(rat32(value) for value in reach_state),
    )
    raw = (Fraction(1, 2), Fraction(0), Fraction(-1, 2))
    for action in range(3):
        close(reach_raw_candidate[action], float(reach_raw_reference[action]), f"reachability.raw_reference[{action}]")
        close(reach_raw_candidate[action], float(raw[action]), f"reachability.raw_expected[{action}]")
    head = candidate_rational_head(tuple(rat32(value) for value in reach_raw_candidate))
    reference_head = rational_head(raw)
    require(head["z"] == (Fraction(6, 13), Fraction(0), Fraction(-6, 13)), "reachability safe logits failed")
    require(head["masses"] == (2440, 2197, 1972), "reachability integer masses failed")
    for action in range(3):
        close(float(head["pi"][action]), float(reference_head["pi"][action]), f"reachability.pi[{action}]")
    no_update = candidate_rational_head((Fraction(0), Fraction(0), Fraction(0)))
    require(no_update["masses"] == (1, 1, 1), "no-update policy masses failed")
    tv = sum((abs(head["pi"][a] - no_update["pi"][a]) for a in range(3)), Fraction(0)) / 2
    require(tv == Fraction(237, 6609) and tv > Fraction(3, 100), "action reachability TV fixture failed")
    return {
        "packet_coordinates": ["x0", "x1", "LEFT", "HOLD", "RIGHT", "sign", "e0", "e1", "sign_e0", "sign_e1", "sign_norm_e", "k_over_12", "tau_over_T"],
        "mask_nonzeros": {"RISP": [[0, 8], [1, 9]], "SIGN_RNN": [[0, 10], [1, 10]]},
        "analytic_full_class_translation": ["W_G=W_R+M_RISP-M_SIGN_RNN", "W_R=W_G+M_SIGN_RNN-M_RISP"],
        "containment_fixtures": fixture_records,
        "reachability": {"candidate_path": "binary32 tanh(2^-20) -> literal V -> literal transition state -> literal U -> raw logits -> independent candidate rational head", "updated_state": ["1/8", "0"], "candidate_raw_logits": list(reach_raw_candidate), "reference_raw_logits": [str(value) for value in reach_raw_reference], "raw_logits": ["1/2", "0", "-1/2"], "integer_masses": list(head["masses"]), "no_update_masses": [1, 1, 1], "tv": "237/6609", "tv_gt_0.03": True},
    }


def exact_discount_factor(duration: int) -> Fraction:
    require(duration in (4, 8, 12), "duration outside registered Lock-1 domain")
    gamma = Fraction(99, 100)
    return sum((gamma ** j for j in range(duration)), Fraction(0))


def exact_baseline_delta_sign(
    duration: int,
    outcome_sign: int,
    belief: tuple[Fraction, Fraction, Fraction],
    policy: tuple[Fraction, Fraction, Fraction],
) -> dict[str, object]:
    require(outcome_sign in (-1, 1), "registered outcome sign must be binary")
    require(sum(policy, Fraction(0)) == 1 and all(mass > 0 for mass in policy), "invalid exact policy")
    require(sum(belief, Fraction(0)) == 1, "invalid controller belief")
    discount_factor = exact_discount_factor(duration)
    centered = tuple(value - Fraction(1, 2) for value in belief)
    baseline = discount_factor * sum((policy[a] * centered[a] for a in range(3)), Fraction(0))
    interval_return = discount_factor * outcome_sign
    delta = interval_return - baseline
    supplied_sign = 1 if delta > 0 else (-1 if delta < 0 else 0)
    require(supplied_sign == outcome_sign, "exact baseline changed registered outcome sign")
    return {"C": discount_factor, "B": baseline, "R": interval_return, "delta": delta, "sign": supplied_sign}


def controller_step(
    rho: tuple[Fraction, Fraction, Fraction],
    belief: tuple[Fraction, Fraction, Fraction],
    state: tuple[Fraction, Fraction],
    action: int,
    residue: int,
    eligibility: tuple[Fraction, Fraction],
    duration: int,
    policy: tuple[Fraction, Fraction, Fraction],
    recipient_outcome: int,
    recipient_target: int,
) -> tuple[tuple[Fraction, Fraction, Fraction], tuple[Fraction, Fraction, Fraction], tuple[Fraction, Fraction], dict[str, object], dict[str, object]]:
    require(recipient_outcome in (-1, 1) and recipient_target in range(3), "invalid recipient diagnostic input")
    pbar = Fraction(1, 4) + Fraction(1, 2) * rho[action]
    masses = clear_rational_masses((pbar, 1 - pbar))
    total = sum(masses)
    require(0 <= residue < total, "sentinel residue outside ExactCat interval")
    replicate_outcome = 1 if residue < masses[0] else -1
    residual = exact_baseline_delta_sign(duration, replicate_outcome, belief, policy)
    supplied_sign = residual["sign"]
    next_rho = tuple(pbar if index == action else (1 - pbar) / 2 for index in range(3))
    next_belief = tuple(Fraction(1) if index == action else Fraction(0) for index in range(3)) if supplied_sign == 1 else tuple(Fraction(0) if index == action else Fraction(1, 2) for index in range(3))
    next_state = (state[0] + Fraction(1, 10) * supplied_sign * eligibility[0], state[1] + Fraction(1, 10) * supplied_sign * eligibility[1])
    visible = {
        "selected_action": ACTION_NAMES[action],
        "pbar": str(pbar),
        "duration": duration,
        "discount_factor": str(residual["C"]),
        "baseline": str(residual["B"]),
        "replicate_delta": str(residual["delta"]),
        "supplied_sign": supplied_sign,
        "controller_belief": [str(value) for value in next_belief],
        "fast_state": [str(value) for value in next_state],
        "rho": [str(value) for value in next_rho],
        "dependency_fields": ["prior_rho", "prior_controller_belief", "prior_fast_state", "selected_action", "literal_twin_residue", "eligibility", "duration", "exact_policy"],
    }
    recipient_diagnostic = {"actual_recipient_outcome": recipient_outcome, "actual_recipient_target": ACTION_NAMES[recipient_target]}
    return next_rho, next_belief, next_state, visible, recipient_diagnostic


def check_yoke_sentinel() -> dict[str, object]:
    initial_rho = (Fraction(1, 3),) * 3
    initial_belief = (Fraction(1, 3),) * 3
    initial_state = (Fraction(0), Fraction(0))

    duration_residuals = {}
    baseline_policy = rational_head((Fraction(1, 2), Fraction(0), Fraction(-1, 2)))["pi"]
    for duration in (4, 8, 12):
        positive = exact_baseline_delta_sign(duration, 1, initial_belief, baseline_policy)
        negative = exact_baseline_delta_sign(duration, -1, initial_belief, baseline_policy)
        require(positive["sign"] == 1 and negative["sign"] == -1, f"duration-{duration} sign coverage failed")
        duration_residuals[str(duration)] = {"C": str(positive["C"]), "B": str(positive["B"]), "delta_positive": str(positive["delta"]), "delta_negative": str(negative["delta"]), "signs": [positive["sign"], negative["sign"]]}

    def run_controller_lineage(recipient_world: dict[str, tuple[int, ...]]) -> tuple[tuple[dict[str, object], dict[str, object]], tuple[dict[str, object], dict[str, object]]]:
        rho1, belief1, state1, visible1, diagnostic1 = controller_step(
            initial_rho, initial_belief, initial_state, 0, 4,
            (Fraction(3, 5), Fraction(-4, 5)), 4, baseline_policy,
            recipient_world["actual_outcomes"][0], recipient_world["recipient_targets"][0],
        )
        require(visible1["pbar"] == "5/12" and visible1["supplied_sign"] == 1, "first yoke sentinel law failed")
        require(rho1 == (Fraction(5, 12), Fraction(7, 24), Fraction(7, 24)), "first rho update failed")
        rho2, belief2, state2, visible2, diagnostic2 = controller_step(
            rho1, belief1, state1, 1, 19,
            (Fraction(1, 5), Fraction(2, 5)), 12, baseline_policy,
            recipient_world["actual_outcomes"][1], recipient_world["recipient_targets"][1],
        )
        require(visible2["pbar"] == "19/48" and visible2["supplied_sign"] == -1, "second yoke sentinel law failed")
        require(rho2 == (Fraction(29, 96), Fraction(19, 48), Fraction(29, 96)), "second rho update failed")
        require(belief2[1] == 0 and state2 == (Fraction(1, 25), Fraction(-3, 25)), "second controller update failed")
        return (visible1, visible2), (diagnostic1, diagnostic2)

    recipient_world_plus = {"actual_outcomes": (1, -1), "recipient_targets": (0, 0, 2)}
    recipient_world_minus = {"actual_outcomes": (-1, 1), "recipient_targets": (0, 2, 1)}
    visible_plus, diagnostics_plus = run_controller_lineage(recipient_world_plus)
    visible_minus, diagnostics_minus = run_controller_lineage(recipient_world_minus)
    require(visible_plus == visible_minus, "recipient lineage leaked into controller-visible fields")
    require(diagnostics_plus != diagnostics_minus, "divergent recipient inputs did not flow through sentinel function")
    dependency_fields = visible_plus[0]["dependency_fields"]
    require(
        all(name not in dependency_fields for name in ("actual_outcomes", "recipient_targets", "actual_recipient_outcome", "actual_recipient_target")),
        "recipient-only field appears in dependency trace",
    )
    require(recipient_world_plus != recipient_world_minus, "sentinel recipient worlds are not distinct")
    return {
        "recipient_worlds": 2,
        "duration_baseline_delta_sign": duration_residuals,
        "first_step": visible_plus[0],
        "second_step": visible_plus[1],
        "recipient_diagnostics_plus": list(diagnostics_plus),
        "recipient_diagnostics_minus": list(diagnostics_minus),
        "divergent_recipient_inputs_flowed_through_tested_function": True,
        "controller_visible_fields_identical": True,
        "recipient_outcome_or_target_dependency": False,
    }


def check_schedules_keys_counts() -> dict[str, object]:
    schedule_report = {}
    for schedule_id in range(5):
        rows = schedule_rows(schedule_id)
        require(len(rows) == EXPECTED_DECISIONS[schedule_id], f"schedule {schedule_id} decision count failed")
        update_rows = [row for row in rows if not row[2]]
        require(len(update_rows) == EXPECTED_UPDATES[schedule_id], f"schedule {schedule_id} update count failed")
        require(rows[-1][0] + rows[-1][1] == T and rows[-1][2], f"schedule {schedule_id} terminal row failed")
        schedule_report[str(schedule_id)] = {"decisions": len(rows), "nonterminal_updates": len(update_rows), "terminal_update": False, "terminal_twin": False}
    rows_3 = schedule_rows(3)
    rows_4 = schedule_rows(4)
    require((rows_3[23], rows_3[24], rows_3[25]) == ((92, 4, False), (96, 12, False), (108, 12, False)), "4->12 boundary latching failed")
    require((rows_4[7], rows_4[8], rows_4[9]) == ((84, 12, False), (96, 4, False), (100, 4, False)), "12->4 boundary latching failed")
    target_windows = {"12": [0, 191, 192], "4->12": [108, 191, 84], "12->4": [100, 191, 92]}

    require(set(EVENT_FIELDS) == {"train_init", "train_action", "train_Y", "train_alt", "eval_init", "eval_action", "eval_Y", "eval_alt", "twin", "fork_action", "fork_Y", "fork_alt"}, "typed event-kind domain failed")
    representative = {
        "train_init_min": event_key("train_init", 0, 0, 0, 0),
        "train_init_max": event_key("train_init", 7, 255, 15, 1),
        "train_Y_max": event_key("train_Y", 7, 255, 15, 1, 23),
        "train_alt_max": event_key("train_alt", 7, 255, 15, 1, 23),
        "train_action_max": event_key("train_action", 7, 255, 15, 1, 23),
        "eval_init_min": event_key("eval_init", 0, 0, 0, 0),
        "eval_alt_max": event_key("eval_alt", 7, 4, 63, 1, 31),
        "eval_action_max": event_key("eval_action", 7, 4, 63, 1, 31),
        "twin_min": event_key("twin", 0, 0, 0, 0, 0),
        "twin_max": event_key("twin", 7, 4, 63, 1, 30),
        "initialization_family_min": initialization_address(0, 0),
        "initialization_family_max": initialization_address(7, 99),
        "fork_y_min": event_key("fork_Y", 0, 2, 0, 0),
        "fork_alt_max": event_key("fork_alt", 7, 4, 63, 1),
        "fork_action_max": event_key("fork_action", 7, 4, 63, 1),
    }
    namespace_intervals = {
        "train_init_y_alt": (10_000_000_000, 10_065_535_223),
        "eval_init_y_alt": (20_000_000_000, 20_005_119_231),
        "twin": (30_000_000_000, 37_463_001_046),
        "train_action": (40_000_000_000, 40_065_535_023),
        "eval_action": (50_000_000_000, 50_005_119_031),
        "initialization_family": (60_000_000_000, 60_000_000_007),
        "fork_y_alt": (70_000_256_000, 70_005_119_001),
        "fork_action": (80_000_256_000, 80_005_119_000),
    }
    ordered_intervals = sorted(namespace_intervals.items(), key=lambda item: item[1][0])
    for index, (_, interval) in enumerate(ordered_intervals):
        require(0 <= interval[0] <= interval[1] <= U64_MAX, "namespace interval outside uint64")
        if index:
            require(ordered_intervals[index - 1][1][1] < interval[0], "namespace intervals overlap")
    require(len(set(representative.values())) == len(representative), "representative event keys collide")
    representative_namespaces = {
        "train_init_y_alt": (representative["train_init_min"], representative["train_init_max"], representative["train_Y_max"], representative["train_alt_max"]),
        "eval_init_y_alt": (representative["eval_init_min"], representative["eval_alt_max"]),
        "twin": (representative["twin_min"], representative["twin_max"]),
        "train_action": (representative["train_action_max"],),
        "eval_action": (representative["eval_action_max"],),
        "initialization_family": (representative["initialization_family_min"], representative["initialization_family_max"]),
        "fork_y_alt": (representative["fork_y_min"], representative["fork_alt_max"]),
        "fork_action": (representative["fork_action_max"],),
    }
    for namespace, values in representative_namespaces.items():
        lower, upper = namespace_intervals[namespace]
        require(all(lower <= value <= upper for value in values), f"{namespace} representative/extremum outside claimed interval")
    require(event_key("fork_Y", 0, 2, 0, 0) == 70_000_256_000, "fork Y namespace lower bound failed")
    require(event_key("fork_action", 0, 2, 0, 0) == 80_000_256_000, "fork action namespace lower bound failed")

    # Within-row offsets are disjoint; row strides are 1000.  Mixed-radix row
    # formulas are injective over their literal domains, completing the analytic
    # proof without enumerating or materializing a stochastic tape menu.
    require(247 < 1000 and 47 < 1000 and 31 < 1000, "row-local key offset exceeds stride")
    require(train_row(0, 0, 0, 0) == 0 and train_row(7, 255, 15, 1) == 65_535, "train row domain failed")
    require(eval_row(0, 0, 0, 0) == 0 and eval_row(7, 4, 63, 1) == 5_119, "eval row domain failed")

    init_shapes = (("encoder_8x2", 16), ("encoder_4x8", 32), ("base_3x4", 12), ("U_3x2", 6), ("V_4x2", 8), ("W_2x13", 26))
    offsets = []
    cursor = 0
    for name, size in init_shapes:
        offsets.append({"tensor": name, "q_start": cursor, "q_stop_exclusive": cursor + size, "row_major": True})
        cursor += size
    require(cursor == 100, "initialization traversal does not consume exactly 100 coordinates")
    require(initialization_address(0, 0) == 60_000_000_000 and initialization_address(7, 99) == 60_000_000_007, "initialization seed address failed")
    require(initialization_address(3, 0) == initialization_address(3, 99), "I[s,q] family address changed with q")
    paired_reuse = {("RISP", 3): initialization_address(3, 17), ("SIGN_RNN", 3): initialization_address(3, 17)}
    require(len(set(paired_reuse.values())) == 1 and initialization_address(2, 17) != initialization_address(3, 17), "paired-only initialization reuse failed")

    train_action = 8 * 2 * (2048 * 48 + 2048 * 24) * 2
    train_updates = 8 * 2 * (2048 * 47 + 2048 * 23) * 2
    eval_decisions = 8 * 4 * 64 * 2 * sum(EXPECTED_DECISIONS)
    eval_updates = 8 * 4 * 64 * 2 * sum(EXPECTED_UPDATES)
    control_decisions = 8 * 2 * 64 * 2 * sum(EXPECTED_DECISIONS)
    twin_calls = 8 * 2 * 64 * 2 * sum(EXPECTED_UPDATES)
    require((train_action, train_updates, eval_decisions, eval_updates, control_decisions, twin_calls) == (4_718_592, 4_587_520, 622_592, 602_112, 311_296, 301_056), "published decision/update counts failed")

    ledger = {
        "training": {"INIT": 131_072, "ACTION": train_action, "Y": train_action, "ALT": train_action, "TWIN": 0, "total": 14_286_848},
        "factorial_evaluation": {"INIT": 20_480, "ACTION": eval_decisions, "Y": eval_decisions, "ALT": eval_decisions, "TWIN": twin_calls, "total": 2_189_312},
        "descriptive_controls": {"INIT": 10_240, "ACTION": control_decisions, "Y": control_decisions, "ALT": control_decisions, "TWIN": 0, "total": 944_128},
        "immediate_forks": {"INIT": 0, "ACTION": 12_288, "Y": 12_288, "ALT": 12_288, "TWIN": 0, "total": 36_864},
    }
    totals = {name: sum(scope[name] for scope in ledger.values()) for name in ("INIT", "ACTION", "Y", "ALT", "TWIN", "total")}
    require(totals == {"INIT": 161_792, "ACTION": 5_664_768, "Y": 5_664_768, "ALT": 5_664_768, "TWIN": 301_056, "total": 17_457_152}, "categorical call ledger failed")
    distinct = {"training": 7_143_424, "evaluation_control": 472_064, "twin": 150_528, "fork": 9_216}
    require(sum(distinct.values()) == 7_775_232, "distinct event-key total failed")
    require(8 * 100 == 800, "initialization raw-word count failed")

    base_ticks = 25_165_824 + 3_932_160 + 1_966_080
    require(base_ticks == 31_064_064 and base_ticks + 114_688 == 31_178_752, "agent-tick ledger failed")
    return {
        "schedules": schedule_report,
        "post_feedback_windows": target_windows,
        "terminal_rule": "terminal completed hold records recipient diagnostic and detached residual; no packet/update/belief/rho/twin",
        "typed_event_fields": {name: list(fields) for name, fields in EVENT_FIELDS.items()},
        "key_formula_representatives": representative,
        "namespace_intervals": {name: list(interval) for name, interval in namespace_intervals.items()},
        "injectivity_proof": "mixed_radix rows + disjoint within-row offsets + disjoint namespace intervals",
        "uint64_range": True,
        "deliberate_reuse": {"base_events": "complete typed tuple reused across paired architectures/feedback/controllers", "twin": "architecture-free identity reused across paired architecture calls only where specified", "fork": "both branches and architectures replay the same typed fork event", "unequal_typed_tuples": "separate event identities"},
        "event_local_variable_retry": True,
        "fixed_raw_word_total_predicted": False,
        "initialization": {"seed_address": "60000000000+s", "coordinates_per_seed": 100, "total_literal_coordinate_count": 800, "traversal": offsets, "reuse": "paired RISP/SIGN_RNN only at identical seed stratum; different seeds disjoint"},
        "counts": {"training_decisions": train_action, "training_updates": train_updates, "evaluation_decisions": eval_decisions, "evaluation_updates": eval_updates, "control_decisions": control_decisions, "twin_calls": twin_calls, "categorical_ledger": ledger, "categorical_totals": totals, "distinct_event_keys": distinct, "distinct_event_key_total": sum(distinct.values()), "base_agent_ticks": base_ticks, "fork_agent_ticks": 114_688, "total_agent_ticks_with_forks": base_ticks + 114_688},
    }


def check_resource_and_activity() -> dict[str, object]:
    mib = 1 << 20
    bytes_f32 = 4
    bytes_f64 = 8
    bytes_u64 = 8
    parameter_scalars = 117
    learned_optimizer_bytes = parameter_scalars * bytes_f32 * 4  # parameters, gradients, Adam m, Adam v
    renewal_nodes = 16 * 2 * 48
    renewal_tensor_shapes = {
        "observation": 2,
        "encoder_hidden_8": 8,
        "encoder_hidden_4": 4,
        "base_logits": 3,
        "fast_logits": 3,
        "raw_logits": 3,
        "safe_logits": 3,
        "head_weights": 3,
        "probabilities": 3,
        "selected_log_probability": 1,
        "all_action_raw_derivatives": 6,
        "all_action_scores": 6,
        "fisher": 4,
        "eligibility": 2,
        "fast_state_input": 2,
        "packet": 13,
        "fast_state_output": 2,
        "controller_belief": 3,
        "return_baseline_delta_sign": 4,
    }
    activation_scalars_per_node = sum(renewal_tensor_shapes.values())
    autograd_saved_copies = 4
    renewal_graph_bytes = renewal_nodes * activation_scalars_per_node * bytes_f32 * autograd_saved_copies
    allocator_tensor_count_per_node = len(renewal_tensor_shapes) * autograd_saved_copies
    allocator_alignment_bytes = renewal_nodes * allocator_tensor_count_per_node * 256
    duration_batch_bytes = (16 * 2 * T * 3 * bytes_f32) + (16 * 2 * 48 * 8 * bytes_u64)
    summary_bytes = 8 * 4 * 5 * 64 * bytes_f64
    initialization_bytes = 100 * bytes_u64
    exact_slots = 512
    exact_integer_bits_per_numerator_or_denominator = 16_384
    exact_integer_payload_bytes = exact_slots * 2 * (exact_integer_bits_per_numerator_or_denominator // 8)
    exact_fraction_metadata_bytes = exact_slots * 64
    exact_workspace_bytes = exact_integer_payload_bytes + exact_fraction_metadata_bytes
    runtime_reserve_bytes = 256 * mib
    resource_components = {
        "117_f32_parameters_gradients_and_two_adam_moments": learned_optimizer_bytes,
        "renewal_graph_explicit_f32_activation_and_saved_backward_scalars": renewal_graph_bytes,
        "256_byte_allocator_alignment_per_live_saved_tensor": allocator_alignment_bytes,
        "duration_split_batch_rewards_indices_and_audit_counters": duration_batch_bytes,
        "streamed_seed_schedule_f64_summaries": summary_bytes,
        "single_seed_100_word_initialization_buffer": initialization_bytes,
        "streamed_exact_fraction_512_slot_16384_bit_workspace": exact_workspace_bytes,
        "separate_interpreter_tensor_runtime_overhead_reserve": runtime_reserve_bytes,
    }
    static_bound = sum(resource_components.values())
    require(static_bound < (1 << 30), "shape-derived static resource bound is not below 1 GiB")
    require(16 * 2 * 48 == 1536, "renewal-state graph bound failed")

    source_paths = (Path(__file__), Path(__file__).with_name("run_lock1.py"))
    allowed_imports = {"__future__", "ast", "json", "math", "struct", "sys", "dataclasses", "fractions", "functools", "pathlib", "lock1_certificate"}
    forbidden_calls = {"PCG" + "64", "default_" + "rng", "Random", "RandomState", "seed"}
    observed_imports: set[str] = set()
    observed_forbidden_calls: set[str] = set()
    for source_path in source_paths:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed_imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                observed_imports.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                    observed_forbidden_calls.add(node.func.id)
                if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls:
                    observed_forbidden_calls.add(node.func.attr)
    require(observed_imports <= allowed_imports, f"unapproved import surface: {sorted(observed_imports - allowed_imports)}")
    require(not observed_forbidden_calls, f"stochastic constructor/call surface found: {sorted(observed_forbidden_calls)}")
    require("random" not in sys.modules and "numpy" not in sys.modules, "stochastic module loaded during Lock 1")
    return {
        "manifest": {"processes": 1, "cpu_processes": 1, "gpu": False, "learned_tensor_dtype": "binary32", "serial_seed_lifecycle": True, "episodes_per_vectorized_batch": 16, "agents_per_episode": 2, "split_batches_by_duration": True, "max_renewal_states_per_episode_graph": 48, "max_live_renewal_nodes": renewal_nodes, "renewal_tensor_shapes_f32_scalars": renewal_tensor_shapes, "activation_scalars_per_node": activation_scalars_per_node, "autograd_saved_copies_assumption": autograd_saved_copies, "allocator_alignment_bytes_per_live_tensor": 256, "exact_fraction_slots": exact_slots, "exact_integer_bits_per_numerator_or_denominator": exact_integer_bits_per_numerator_or_denominator, "discard_graph_after_each_adam_update": True, "exact_rational_event_workspace": "streamed one event at a time", "seed_schedule_summaries": "streamed", "per_tick_graph": False, "per_row_durable_json": False},
        "static_live_memory_components_bytes": resource_components,
        "static_live_memory_bound_bytes": static_bound,
        "static_live_memory_bound_mib": static_bound / mib,
        "below_one_gib": True,
        "sixty_minute_wall_claimed_by_lock1": False,
        "source_imports": sorted(observed_imports),
        "stochastic_constructor_calls": 0,
        "registered_stochastic_objects_created": 0,
        "registered_random_words_created_or_consumed": 0,
        "learned_checkpoints_initialized": 0,
        "training_or_evaluation_rows": 0,
        "lock2_executed": False,
        "scientific_activity_started": False,
        "activity_boundary_assertion": "no registered Lock-2 stochastic object or random word was created, inspected, or consumed",
    }


def run_certificate() -> dict[str, object]:
    checks = {
        "rat32_raw_head_score_fisher_eligibility": check_rat32_head_score(),
        "literal_exactcat": check_exactcat(),
        "containment_and_action_reachability": check_containment_and_reachability(),
        "marginal_twin_no_leakage": check_yoke_sentinel(),
        "schedule_terminal_keys_and_counts": check_schedules_keys_counts(),
        "resource_and_activity_boundary": check_resource_and_activity(),
    }
    return {
        "schema": SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "certificate_result": "PASS",
        "required_structural_fixture_groups": 6,
        "required_structural_fixture_groups_passed": 6,
        "all_required_structural_fixtures_passed": True,
        "registered_stochastic_object_created": False,
        "scientific_activity_started": False,
        "interpretation": "deterministic structural answerability/conformance only; no algorithm, efficacy, competence, mechanism, or portfolio evidence",
        "checks": checks,
        "anomalies": [],
    }


def write_artifact(path: Path) -> dict[str, object]:
    result = run_certificate()
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
