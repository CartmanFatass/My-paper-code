"""Exact Q52 categorical and physical CDF law for VNFC R02."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import struct
from typing import Sequence, TypeAlias

from .contract import (
    ContractViolation,
    LOGIT_FLOOR,
    MASS_TOTAL,
    MAX_CANDIDATES,
    ScalarTranscendentals,
    UINT64_LIMIT,
)
from .scalar import rn64


Candidate: TypeAlias = int | None


def _validate_candidates(candidates: Sequence[Candidate]) -> tuple[Candidate, ...]:
    result = tuple(candidates)
    if not 1 <= len(result) <= MAX_CANDIDATES:
        raise ContractViolation("candidate count must be in [1,8]")
    ranks = tuple(candidate for candidate in result if candidate is not None)
    if any(isinstance(rank, bool) or not isinstance(rank, int) or rank <= 0 for rank in ranks):
        raise ContractViolation("physical candidates must be positive opaque ranks")
    if ranks != tuple(sorted(set(ranks))):
        raise ContractViolation("physical candidates must be unique and ascending")
    if None in result and result[-1] is not None:
        raise ContractViolation("null must be last")
    if result.count(None) > 1:
        raise ContractViolation("null may occur at most once")
    return result


def _strict_max(values: Sequence[float]) -> tuple[float, int]:
    if not values:
        raise ContractViolation("strict maximum requires a nonempty sequence")
    best = rn64(values[0])
    winner = 0
    for index, raw in enumerate(values[1:], start=1):
        value = rn64(raw)
        if value > best:
            best = value
            winner = index
    return best, winner


@dataclass(frozen=True)
class ProbabilityObject:
    candidates: tuple[Candidate, ...]
    logits: tuple[float, ...]
    max_index: int
    centered: tuple[float, ...]
    q: tuple[float, ...]
    weights: tuple[float, ...]
    masses: tuple[int, ...]
    probabilities: tuple[float, ...]
    cumulative: tuple[int, ...]
    stored_log_p: tuple[float, ...]
    stored_H: float
    fixed: bool = False

    def __post_init__(self) -> None:
        length = len(self.candidates)
        if any(len(values) != length for values in (self.logits, self.centered, self.q, self.weights, self.masses, self.probabilities, self.cumulative, self.stored_log_p)):
            raise ContractViolation("probability object shape drift")
        rn64(self.stored_H)
        tuple(rn64(value) for value in self.stored_log_p)
        _validate_candidates(self.candidates)
        if not 0 <= self.max_index < length:
            raise ContractViolation("probability maximum index drift")
        if any(mass <= 0 for mass in self.masses) or sum(self.masses) != MASS_TOTAL:
            raise ContractViolation("Q52 mass invariant failed")
        expected = []
        total = 0
        for mass in self.masses:
            total += mass
            expected.append(total)
        if self.cumulative != tuple(expected) or total != MASS_TOTAL:
            raise ContractViolation("cumulative Q52 mass invariant failed")
        if any(Fraction.from_float(p) != Fraction(n, MASS_TOTAL) for p, n in zip(self.probabilities, self.masses)):
            raise ContractViolation("probability bits do not represent their Q52 masses")
        entropy_accumulator = 0.0
        for p, log_p in zip(self.probabilities, self.stored_log_p):
            entropy_accumulator = rn64(entropy_accumulator + rn64(p * log_p))
        if self.stored_H != rn64(-entropy_accumulator):
            raise ContractViolation("stored categorical entropy differs from stored p/log_p bits")
        if self.fixed and (length != 1 or self.candidates[0] is None):
            raise ContractViolation("fixed support must contain one physical occupant")
        if self.fixed and not (
            self.masses == (MASS_TOTAL,)
            and self.probabilities == (1.0,)
            and self.stored_log_p == (0.0,)
            and self.stored_H == 0.0
        ):
            raise ContractViolation("fixed probability object differs from exact unit law")


def _apportion(weights: Sequence[float]) -> tuple[int, ...]:
    exact = tuple(Fraction.from_float(rn64(weight)) for weight in weights)
    if any(weight <= 0 for weight in exact):
        raise ContractViolation("all categorical weights must be positive")
    total = sum(exact, Fraction(0))
    quotas = tuple(weight * MASS_TOTAL / total for weight in exact)
    floors = [quota.numerator // quota.denominator for quota in quotas]
    remainder_count = MASS_TOTAL - sum(floors)
    if not 0 <= remainder_count < len(floors):
        raise ContractViolation("largest-remainder count is invalid")
    order = sorted(
        range(len(floors)),
        key=lambda index: (-(quotas[index] - floors[index]), index),
    )
    for index in order[:remainder_count]:
        floors[index] += 1
    if any(mass <= 0 for mass in floors) or sum(floors) != MASS_TOTAL:
        raise ContractViolation("Q52 positivity or exact-sum invariant failed")
    return tuple(floors)


def construct_probability(
    logits: Sequence[float], candidates: Sequence[Candidate], kernel: ScalarTranscendentals
) -> ProbabilityObject:
    ordered = _validate_candidates(candidates)
    finite_logits = tuple(rn64(value) for value in logits)
    if len(finite_logits) != len(ordered):
        raise ContractViolation("logit/support shape drift")
    maximum, winner = _strict_max(finite_logits)
    centered = tuple(rn64(value - maximum) for value in finite_logits)
    q = tuple(rn64(max(LOGIT_FLOOR, value)) for value in centered)
    weights = tuple(rn64(kernel.exp_R02(value)) for value in q)
    masses = _apportion(weights)
    probabilities = tuple(rn64(mass / MASS_TOTAL) for mass in masses)
    stored_log_p = tuple(rn64(kernel.log_R02(value)) for value in probabilities)
    entropy_accumulator = 0.0
    for p, log_p in zip(probabilities, stored_log_p):
        entropy_term = rn64(p * log_p)
        entropy_accumulator = rn64(entropy_accumulator + entropy_term)
    stored_h = rn64(-entropy_accumulator)
    cumulative: list[int] = []
    total = 0
    for mass in masses:
        total += mass
        cumulative.append(total)
    return ProbabilityObject(
        candidates=ordered,
        logits=finite_logits,
        max_index=winner,
        centered=centered,
        q=q,
        weights=weights,
        masses=masses,
        probabilities=probabilities,
        cumulative=tuple(cumulative),
        stored_log_p=stored_log_p,
        stored_H=stored_h,
    )


def construct_fixed_probability(occupant: int) -> ProbabilityObject:
    ordered = _validate_candidates((occupant,))
    return ProbabilityObject(
        candidates=ordered,
        logits=(0.0,),
        max_index=0,
        centered=(0.0,),
        q=(0.0,),
        weights=(1.0,),
        masses=(MASS_TOTAL,),
        probabilities=(1.0,),
        cumulative=(MASS_TOTAL,),
        stored_log_p=(0.0,),
        stored_H=0.0,
        fixed=True,
    )


def construct_probability_from_centered(
    centered: Sequence[float], candidates: Sequence[Candidate], kernel: ScalarTranscendentals
) -> ProbabilityObject:
    values = tuple(rn64(value) for value in centered)
    maximum, winner = _strict_max(values)
    if maximum != 0.0:
        raise ContractViolation("injected centered scores must have strict-fold maximum +0.0")
    return construct_probability(values, candidates, kernel)


def deterministic_choice(probability: ProbabilityObject) -> Candidate:
    _, winner = _strict_max(probability.q)
    return probability.candidates[winner]


def choose_production_word(probability: ProbabilityObject, word: int) -> Candidate:
    if probability.fixed:
        raise ContractViolation("fixed tokens consume no action RNG coordinate")
    if isinstance(word, bool) or not isinstance(word, int) or not 0 <= word < UINT64_LIMIT:
        raise ContractViolation("production word must be uint64")
    midpoint_numerator = 2 * word + 1
    for candidate, cumulative in zip(probability.candidates, probability.cumulative):
        if midpoint_numerator * MASS_TOTAL < (1 << 65) * cumulative:
            return candidate
    raise ContractViolation("Q52 cumulative mass failed to select a production action")


def _u_fraction(value: Fraction | float | int) -> Fraction:
    if isinstance(value, bool):
        raise ContractViolation("diagnostic u cannot be boolean")
    if isinstance(value, Fraction):
        result = value
    elif isinstance(value, int):
        result = Fraction(value)
    elif isinstance(value, float):
        result = Fraction.from_float(rn64(value))
    else:
        raise ContractViolation("diagnostic u must be an exact ratio or binary64")
    if not Fraction(0) <= result < Fraction(1):
        raise ContractViolation("diagnostic u must satisfy 0<=u<1")
    return result


def choose_diagnostic_u(probability: ProbabilityObject, value: Fraction | float | int) -> Candidate:
    if probability.fixed:
        raise ContractViolation("fixed tokens have no CDF records")
    u = _u_fraction(value)
    for candidate, cumulative in zip(probability.candidates, probability.cumulative):
        if u * MASS_TOTAL < cumulative:
            return candidate
    raise ContractViolation("diagnostic CDF failed to select an action")


def _next_binary64(value: float, upward: bool) -> float:
    """Adjacent binary64 toward the selected infinity without a math kernel."""

    value = rn64(value)
    bits = int.from_bytes(struct.pack(">d", value), "big")
    if value == 0.0:
        next_bits = 1 if upward else (1 << 63) | 1
    elif (value > 0.0) == upward:
        next_bits = bits + 1
    else:
        next_bits = bits - 1
    return struct.unpack(">d", next_bits.to_bytes(8, "big"))[0]


@dataclass(frozen=True)
class CDFProbe:
    edge_index: int
    name: str
    kind: str
    value: Fraction | int
    action: Candidate | None
    rejected: bool


def diagnostic_cdf_probes(probability: ProbabilityObject) -> tuple[CDFProbe, ...]:
    if probability.fixed:
        raise ContractViolation("fixed tokens have no CDF records")
    boundaries = (0,) + probability.cumulative
    probes: list[CDFProbe] = []
    for edge, boundary in enumerate(boundaries):
        exact = Fraction(boundary, MASS_TOTAL)
        rounded = float(exact)
        for name, value in (
            ("EXACT", exact),
            ("NEXTAFTER_LOWER", Fraction.from_float(_next_binary64(rounded, False))),
            ("NEXTAFTER_UPPER", Fraction.from_float(_next_binary64(rounded, True))),
        ):
            try:
                action = choose_diagnostic_u(probability, value)
            except ContractViolation:
                probes.append(CDFProbe(edge, name, "diagnostic_u", value, None, True))
            else:
                probes.append(CDFProbe(edge, name, "diagnostic_u", value, action, False))
        if boundary > 0:
            word = 4096 * boundary - 1
            probes.append(CDFProbe(edge, "PRODUCTION_WORD_BELOW", "production_word", word, choose_production_word(probability, word), False))
        if boundary < MASS_TOTAL:
            word = 4096 * boundary
            probes.append(CDFProbe(edge, "PRODUCTION_WORD_ABOVE", "production_word", word, choose_production_word(probability, word), False))
    expected = 5 * len(probability.candidates) + 3
    if len(probes) != expected:
        raise ContractViolation("diagnostic CDF address cardinality drift")
    return tuple(probes)


def forced_log_probability(
    probability: ProbabilityObject, chosen: Candidate, kernel: ScalarTranscendentals
) -> float:
    try:
        index = probability.candidates.index(chosen)
    except ValueError as exc:
        raise ContractViolation("forced physical command is absent from canonical support") from exc
    if probability.fixed:
        return 0.0
    return probability.stored_log_p[index]


def entropy(probability: ProbabilityObject, kernel: ScalarTranscendentals) -> float:
    return probability.stored_H


def categorical_logprob_adjoint(probability: ProbabilityObject, chosen: Candidate) -> tuple[float, ...]:
    if chosen not in probability.candidates:
        raise ContractViolation("chosen candidate is absent from support")
    if probability.fixed:
        return (0.0,)
    return tuple(rn64((1.0 if candidate == chosen else 0.0) - p) for candidate, p in zip(probability.candidates, probability.probabilities))


def entropy_adjoint(probability: ProbabilityObject, kernel: ScalarTranscendentals) -> tuple[float, ...]:
    if probability.fixed:
        return (0.0,)
    token_entropy = probability.stored_H
    result: list[float] = []
    for p, log_p in zip(probability.probabilities, probability.stored_log_p):
        inside = rn64(log_p + token_entropy)
        result.append(rn64(rn64(-p) * inside))
    return tuple(result)


def combined_categorical_entropy_adjoint(
    probability: ProbabilityObject,
    chosen: Candidate,
    kernel: ScalarTranscendentals,
    *,
    logprob_incoming: float,
    entropy_incoming: float,
) -> tuple[float, ...]:
    log_scale = rn64(logprob_incoming)
    entropy_scale = rn64(entropy_incoming)
    log_gradient = categorical_logprob_adjoint(probability, chosen)
    entropy_gradient = entropy_adjoint(probability, kernel)
    return tuple(
        rn64(rn64(log_scale * a) + rn64(entropy_scale * b))
        for a, b in zip(log_gradient, entropy_gradient)
    )


def clamp_centered_max_adjoint(
    probability: ProbabilityObject, g_q: Sequence[float]
) -> tuple[float, ...]:
    if probability.fixed:
        return (0.0,)
    incoming = tuple(rn64(value) for value in g_q)
    if len(incoming) != len(probability.candidates):
        raise ContractViolation("q adjoint/support shape drift")
    g_d = tuple(
        rn64(value * (1.0 if centered > LOGIT_FLOOR else 0.0))
        for value, centered in zip(incoming, probability.centered)
    )
    total = 0.0
    for value in g_d:
        total = rn64(total + value)
    output = list(g_d)
    output[probability.max_index] = rn64(g_d[probability.max_index] - total)
    return tuple(output)
