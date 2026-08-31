"""Exact, output-disconnected VQFP allocation and reassociation controls."""

from __future__ import annotations

import heapq
from fractions import Fraction
from typing import Iterable, Sequence

from .core import ContractError

Q = 120
FRRIE_ACTION_SEAM_ABSENT = "FRRIE_ACTION_SEAM_ABSENT"
OUTPUT_DISCONNECTED = True


class ActionSeamAbsent(ContractError):
    pass


def _fractions(values: Iterable[Fraction | int]) -> tuple[Fraction, ...]:
    result = tuple(value if isinstance(value, Fraction) else Fraction(value) for value in values)
    if not result:
        raise ContractError("VQFP vector must be nonempty")
    return result


def largest_remainder(weights: Sequence[Fraction | int], coordinates: Sequence[Fraction | int], q: int = Q) -> tuple[int, ...]:
    weights_f = _fractions(weights)
    coords_f = _fractions(coordinates)
    if len(weights_f) != len(coords_f) or any(weight <= 0 for weight in weights_f):
        raise ContractError("LR requires same-length positive weights and physical coordinates")
    if len(set(coords_f)) != len(coords_f):
        raise ContractError("physical-coordinate tie keys must be unique")
    if q != Q:
        raise ContractError("LR quantum count is frozen at Q=120")
    total = sum(weights_f, Fraction())
    quotas = [Fraction(q) * weight / total for weight in weights_f]
    command = [quota.numerator // quota.denominator for quota in quotas]
    remaining = q - sum(command)
    order = sorted(range(len(command)), key=lambda index: (-(quotas[index] - command[index]), coords_f[index]))
    for index in order[:remaining]:
        command[index] += 1
    if sum(command) != q or any(value < 0 for value in command):
        raise RuntimeError("LR legality drift")
    return tuple(command)


def marg0_weights(masses: Sequence[Fraction | int], measures: Sequence[Fraction | int]) -> tuple[Fraction, ...]:
    masses_f, measures_f = _fractions(masses), _fractions(measures)
    if len(masses_f) != len(measures_f) or any(v <= 0 for v in measures_f) or any(m < 0 for m in masses_f):
        raise ContractError("MARG0 support mismatch")
    return tuple(m / (600 * v + 1) for m, v in zip(masses_f, measures_f))


def marginal_improvement(mass: Fraction, measure: Fraction, allocated: int) -> Fraction:
    if mass < 0 or measure <= 0 or allocated < 0:
        raise ContractError("marginal-improvement support mismatch")
    before = mass * measure / (measure + Fraction(allocated, 600))
    after = mass * measure / (measure + Fraction(allocated + 1, 600))
    return before - after


def marginal_heap(
    masses: Sequence[Fraction | int], measures: Sequence[Fraction | int],
    coordinates: Sequence[Fraction | int], q: int = Q,
) -> tuple[int, ...]:
    masses_f, measures_f = _fractions(masses), _fractions(measures)
    coords_f = _fractions(coordinates)
    if q != Q:
        raise ContractError("marginal heap quantum count is frozen at Q=120")
    if len(masses_f) != len(measures_f) or len(masses_f) != len(coords_f) or len(set(coords_f)) != len(coords_f) or any(m < 0 for m in masses_f) or any(v <= 0 for v in measures_f):
        raise ContractError("marginal heap support mismatch")
    command = [0] * len(masses_f)
    heap = [(-marginal_improvement(m, v, 0), coords_f[index], index, 0) for index, (m, v) in enumerate(zip(masses_f, measures_f))]
    heapq.heapify(heap)
    for _ in range(q):
        _, _, index, allocated = heapq.heappop(heap)
        if allocated != command[index]:
            raise RuntimeError("marginal heap frontier drift")
        command[index] += 1
        heapq.heappush(heap, (-marginal_improvement(masses_f[index], measures_f[index], command[index]), coords_f[index], index, command[index]))
    return tuple(command)


def utility(command: Sequence[int], masses: Sequence[Fraction | int], measures: Sequence[Fraction | int]) -> Fraction:
    masses_f, measures_f = _fractions(masses), _fractions(measures)
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in command):
        raise ContractError("utility command entries must be nonnegative integers")
    if len(command) != len(masses_f) or len(command) != len(measures_f) or sum(command) != Q:
        raise ContractError("utility requires a legal Q=120 command")
    if any(m < 0 for m in masses_f) or any(v <= 0 for v in measures_f):
        raise ContractError("utility masses/measures are outside support")
    return sum((m * v / (v + Fraction(n, 600)) for n, m, v in zip(command, masses_f, measures_f)), Fraction())


def half_cycle_indices(n: int) -> tuple[int, ...]:
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0 or n % 2:
        raise ContractError("half-cycle requires positive even N")
    return tuple((index + n // 2) % n for index in range(n))


def half_cycle(values: Sequence[Fraction | int]) -> tuple[Fraction, ...]:
    source = _fractions(values)
    return tuple(source[index] for index in half_cycle_indices(len(source)))


def treatment_weights(measures: Sequence[Fraction | int], benefits: Sequence[Fraction | int], *, reassociated: bool = False) -> tuple[Fraction, ...]:
    v, b = _fractions(measures), _fractions(benefits)
    if len(v) != len(b):
        raise ContractError("treatment vectors differ in length")
    used = half_cycle(v) if reassociated else v
    return tuple(measure * benefit for measure, benefit in zip(used, b))


def mass_weights(measures: Sequence[Fraction | int], densities: Sequence[Fraction | int], *, reassociated: bool = False) -> tuple[Fraction, ...]:
    v, d = _fractions(measures), _fractions(densities)
    if len(v) != len(d):
        raise ContractError("MASS vectors differ in length")
    used = half_cycle(v) if reassociated else v
    # MASS-P is lambda_i*d_i, intentionally not m_{P(i)}.
    return tuple(measure * density for measure, density in zip(used, d))


def association_did(j_t: Fraction, j_t_p: Fraction, j_mass: Fraction, j_mass_p: Fraction) -> Fraction:
    """Higher-better ordering: treatment cut minus MASS control cut."""
    return (j_t - j_t_p) - (j_mass - j_mass_p)


def assert_half_cycle_laws(values: Sequence[Fraction | int]) -> None:
    original = _fractions(values)
    mapped = half_cycle(original)
    permutation = half_cycle_indices(len(original))
    if any(permutation[index] == index for index in range(len(original))) or any(permutation[permutation[index]] != index for index in range(len(original))):
        raise ContractError("half-cycle indices must be a deranging involution")
    if half_cycle(mapped) != original:
        raise ContractError("half-cycle values must be involutive")
    if sorted(mapped) != sorted(original):
        raise ContractError("half-cycle must preserve the measure multiset")


def uniform_absorption_witness(measures: Sequence[Fraction | int], density: Fraction | int) -> bool:
    v = _fractions(measures)
    d = Fraction(density)
    benefits = tuple(d for _ in v)
    coordinates = tuple(Fraction(2 * index + 1, 2 * len(v)) for index in range(len(v)))
    t = treatment_weights(v, benefits)
    mass = mass_weights(v, benefits)
    tp = treatment_weights(v, benefits, reassociated=True)
    massp = mass_weights(v, benefits, reassociated=True)
    return t == mass and tp == massp and largest_remainder(t, coordinates) == largest_remainder(mass, coordinates) and largest_remainder(tp, coordinates) == largest_remainder(massp, coordinates)


def require_action_seam() -> None:
    raise ActionSeamAbsent(FRRIE_ACTION_SEAM_ABSENT)
