"""Frozen control tables, the coefficient oracle, accumulators and mutants.

Everything here is exact rational arithmetic over frozen literals.  No float
pipeline runs in this module and the actor is never called, so importing it
and running its gates verifies table algebra without executing the
discriminator.

Round-6 corrections realized here:

*   ``MutantRow.transform`` used to hold English prose, so M1-M6 were
    digest-bearing descriptions rather than controls.  Each row now names a
    ``transform_id`` that resolves to a real function, and
    ``mutant_dispatch_gate`` proves the id set and the function set are
    equal in both directions.
*   The accumulators exact-gate their input domain: the exact sixteen-key
    set, no extra keys, exact two-component tuples, exact finite floats or
    Fractions.  Round 6 noted that ``zip`` silently truncates a short vector,
    which would have degraded a malformed cell into a plausible number
    instead of a failure.

The mutant expected responses were recomputed by hand before being frozen:
M1 drops ``r`` from the coefficient, leaving ``sum m*b*(m*b) = 8`` as the only
surviving term, giving ``(1/2)(1/128)(8)(2 q aliases) = +1/16`` on the first
component and its negation on the second; M2 flips one ``+1/2`` coefficient
to ``-1/2`` for both aliases, giving ``-2*K(1,1,1) = (-71/64, -57/64)``.
M3-M6 are global sign/scale/orientation mutations, which zero-contrast
controls provably cannot detect (``0 == -0 == 2*0``), so they are routed to
the curvature control instead, where their responses are exact multiples of
the frozen reference.
"""

from __future__ import annotations

import struct as _structmod
from fractions import Fraction

_POSITIVE_ZERO_BITS = _structmod.pack(">d", 0.0)

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    serialize_struct,
    sha256_hex,
)
from experiments.candidates.orbit_owner_match.records import (
    CoefficientRow,
    DecimalLiteral,
    KernelRow,
    LogitRow,
    MutantRow,
    RationalValue,
    rational,
    D2,
)


SIGNS = (-1, 1)
ALIASES = (0, 1)

EXPECTED_KEYS = frozenset(
    (q, m, b, r) for q in ALIASES for m in SIGNS for b in SIGNS for r in SIGNS
)


# ---------------------------------------------------------------------------
# Coefficient oracle
# ---------------------------------------------------------------------------

COEFFICIENT_ORACLE = tuple(
    CoefficientRow(q, m, b, r, RationalValue(m * b * r, 2))
    for q in ALIASES for m in SIGNS for b in SIGNS for r in SIGNS
)


def generate_coefficients_direct() -> tuple:
    """Direct route: form the three-factor product, then halve."""
    rows = []
    for q in ALIASES:
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    rows.append(CoefficientRow(
                        q, m, b, r, RationalValue(m * b * r, 2)))
    return tuple(rows)


def interaction_functional(m: int, q: int) -> dict:
    """``I_BR(m, q) = 0.5 * sum_{b,r} b*r*Z[q,m,b,r]`` as a weight map.

    Built as an object in its own right so the staged route can actually form
    the difference of two functionals rather than assert its result.
    """
    return {(q, m, b, r): Fraction(b * r, 2) for b in SIGNS for r in SIGNS}


def generate_coefficients_staged() -> tuple:
    """Staged route: literally difference the B x role interactions across M.

    ``sum_q [I_BR(+1,q) - I_BR(-1,q)]``.  An earlier version computed
    ``Fraction(b*r,2)`` and branched on ``m`` to attach the sign, which is
    the direct algebra with one factor moved into an ``if`` -- agreement with
    the oracle was close to a tautology.  Here the two functionals are built
    separately and subtracted, so the ``m`` dependence emerges from the
    subtraction rather than from a hardcoded sign.
    """
    weights = {}
    for q in ALIASES:
        positive = interaction_functional(1, q)
        negative = interaction_functional(-1, q)
        for key, weight in positive.items():
            weights[key] = weights.get(key, Fraction(0)) + weight
        for key, weight in negative.items():
            weights[key] = weights.get(key, Fraction(0)) - weight
    rows = []
    for q in ALIASES:
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    rows.append(CoefficientRow(
                        q, m, b, r, rational(weights[(q, m, b, r)])))
    return tuple(rows)


def coefficient_oracle_gate() -> None:
    if generate_coefficients_direct() != COEFFICIENT_ORACLE:
        raise ContractError("direct coefficient generator disagrees with oracle")
    if generate_coefficients_staged() != COEFFICIENT_ORACLE:
        raise ContractError("staged coefficient generator disagrees with oracle")
    if len(COEFFICIENT_ORACLE) != 16:
        raise ContractError("coefficient oracle cardinality mismatch")
    if frozenset((row.q, row.m, row.b, row.r)
                 for row in COEFFICIENT_ORACLE) != EXPECTED_KEYS:
        raise ContractError("coefficient oracle key census mismatch")


def coefficient_map() -> dict:
    return {(row.q, row.m, row.b, row.r): row.coefficient.as_fraction()
            for row in COEFFICIENT_ORACLE}


# ---------------------------------------------------------------------------
# Accumulator domain gates
# ---------------------------------------------------------------------------


def check_value_domain(values_by_key: dict, *, exact: bool) -> None:
    """Exact-gate the accumulator input.

    ``exact=True`` requires ``Fraction`` components (rational control tables);
    ``exact=False`` requires finite ``float`` components (the binary64
    pipeline).  Either way the key census, tuple shape and component types
    are exact -- there is no path where a short or malformed vector is
    silently truncated.
    """
    if type(values_by_key) is not dict:
        raise ContractError("exact dict of values required")
    keys = frozenset(values_by_key)
    if keys != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - keys)
        extra = sorted(keys - EXPECTED_KEYS)
        raise ContractError(
            "value key census mismatch (missing=%r extra=%r)" % (missing, extra))
    for key in sorted(values_by_key):
        value = values_by_key[key]
        if type(value) is not tuple:
            raise ContractError("exact tuple value required at %r" % (key,))
        if len(value) != 2:
            raise ContractError("exact two-component value required at %r"
                                % (key,))
        for component in value:
            if exact:
                if type(component) is not Fraction:
                    raise ContractError("exact Fraction component required")
            else:
                if type(component) is not float:
                    raise ContractError("exact float component required")
                if component != component or component in (
                        float("inf"), float("-inf")):
                    raise ContractError("nonfinite component rejected")


def exact_accumulate(values_by_key: dict, coefficients: dict) -> tuple:
    """Exact rational accumulation in the frozen oracle order."""
    check_value_domain(values_by_key, exact=True)
    if frozenset(coefficients) != EXPECTED_KEYS:
        raise ContractError("coefficient key census mismatch")
    total = [Fraction(0), Fraction(0)]
    for row in COEFFICIENT_ORACLE:
        key = (row.q, row.m, row.b, row.r)
        weight = coefficients[key]
        value = values_by_key[key]
        for index in (0, 1):
            total[index] += weight * value[index]
    return (total[0], total[1])


def oriented_pair_first_m_blind(values_by_key: dict) -> tuple:
    """M-blind null: ``D = 0.5 * sum_{q,b,r} (Z[m=b*r] - Z[m=-b*r])``.

    Positively oriented: every coefficient applied to a difference is
    ``+0.5``.  Round 5 found the earlier formulation multiplied a zero
    difference by a negative weight, and ``(+0.0) * (-0.5)`` is ``-0.0``,
    which broke the exact-zero claim on bit-identical pairs.
    """
    check_value_domain(values_by_key, exact=False)
    total = (0.0, 0.0)
    for q in ALIASES:
        for b in SIGNS:
            for r in SIGNS:
                lead = values_by_key[(q, b * r, b, r)]
                lag = values_by_key[(q, -b * r, b, r)]
                total = tuple(
                    total[i] + 0.5 * (lead[i] - lag[i]) for i in (0, 1))
    return total


def oriented_pair_first_b_blind(values_by_key: dict) -> tuple:
    """B-blind null, same positive orientation."""
    check_value_domain(values_by_key, exact=False)
    total = (0.0, 0.0)
    for q in ALIASES:
        for m in SIGNS:
            for r in SIGNS:
                lead = values_by_key[(q, m, m * r, r)]
                lag = values_by_key[(q, m, -m * r, r)]
                total = tuple(
                    total[i] + 0.5 * (lead[i] - lag[i]) for i in (0, 1))
    return total


# ---------------------------------------------------------------------------
# Literal control tables
# ---------------------------------------------------------------------------

LOGIT_SEPARABLE_CONTROL = tuple(
    LogitRow(m, b, r,
             rational(Fraction(b, 8) + Fraction(r, 4) + Fraction(m, 8)),
             rational(Fraction(-b, 8) + Fraction(m * r, 8)))
    for m in SIGNS for b in SIGNS for r in SIGNS
)

KERNEL_ZERO_CONTROL = tuple(
    KernelRow(m, b, r,
              RationalValue(64 + 4 * b + 2 * r + m * b, 128),
              RationalValue(64 - 4 * b - 2 * r - m * b, 128))
    for m in SIGNS for b in SIGNS for r in SIGNS
)


def _table_values(rows, first: str, second: str) -> dict:
    """Broadcast an (m,b,r) table across both q aliases."""
    values = {}
    for row in rows:
        pair = (getattr(row, first).as_fraction(),
                getattr(row, second).as_fraction())
        for q in ALIASES:
            values[(q, row.m, row.b, row.r)] = pair
    return values


def logit_control_values() -> dict:
    return _table_values(LOGIT_SEPARABLE_CONTROL, "c1", "c2")


def kernel_control_values() -> dict:
    return _table_values(KERNEL_ZERO_CONTROL, "k1", "k2")


def null_orientation_gate() -> None:
    """The blind nulls collapse to a POSITIVELY signed exact zero.

    The nulls were fingerprinted and reachable but no gate ever ran them, so
    the orientation property the round-5 correction established had no
    executable check at all.  An M-independent value table must give the
    M-blind null exactly ``+0.0`` -- not ``-0.0``, which is what an
    incorrectly oriented accumulator produces from bit-identical pairs.
    """
    m_blind_values = {}
    b_blind_values = {}
    for q in ALIASES:
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    # Independent of m: the M-blind null must see nothing.
                    m_blind_values[(q, m, b, r)] = (0.25 * b * r, -0.25 * b * r)
                    # Independent of b: the B-blind null must see nothing.
                    b_blind_values[(q, m, b, r)] = (0.25 * m * r, -0.25 * m * r)
    for name, values, accumulator in (
            ("m-blind", m_blind_values, oriented_pair_first_m_blind),
            ("b-blind", b_blind_values, oriented_pair_first_b_blind)):
        total = accumulator(values)
        for component in total:
            if component != 0.0:
                raise ContractError(
                    "%s null does not collapse to zero" % (name,))
            if _structmod.pack(">d", component) != _POSITIVE_ZERO_BITS:
                raise ContractError(
                    "%s null produced a negatively signed zero" % (name,))


def logit_control_gates() -> None:
    """The separable logit control has no three-factor component."""
    total = exact_accumulate(logit_control_values(), coefficient_map())
    if total != (Fraction(0), Fraction(0)):
        raise ContractError("separable logit control is not three-factor zero")


def kernel_control_gates() -> None:
    """The kernel control sits on the simplex, stays bounded away from the
    boundary, and carries no three-factor component."""
    for row in KERNEL_ZERO_CONTROL:
        k1, k2 = row.k1.as_fraction(), row.k2.as_fraction()
        if k1 + k2 != 1:
            raise ContractError("kernel control row off simplex")
        if k1 < Fraction(1, 4) or k2 < Fraction(1, 4):
            raise ContractError("kernel control positivity bound violated")
    total = exact_accumulate(kernel_control_values(), coefficient_map())
    if total != (Fraction(0), Fraction(0)):
        raise ContractError("kernel control is not three-factor zero")


# ---------------------------------------------------------------------------
# Executable mutants
# ---------------------------------------------------------------------------


def mutate_m1_drop_r(coefficients: dict) -> dict:
    """Drop ``r`` from the three-factor coefficient."""
    return {(q, m, b, r): Fraction(m * b, 2)
            for (q, m, b, r) in coefficients}


def mutate_m2_flip_one_cell(coefficients: dict) -> dict:
    """Flip the ``(m,b,r) = (+1,+1,+1)`` coefficient for both q aliases."""
    mutated = dict(coefficients)
    for q in ALIASES:
        mutated[(q, 1, 1, 1)] = -coefficients[(q, 1, 1, 1)]
    return mutated


def mutate_m3_global_sign(coefficients: dict) -> dict:
    return {key: -value for key, value in coefficients.items()}


def mutate_m4_drop_half_scale(coefficients: dict) -> dict:
    return {key: value * 2 for key, value in coefficients.items()}


def mutate_m5_swap_components(coefficients: dict) -> dict:
    """Orientation mutation; the swap happens in the accumulator wrapper."""
    return dict(coefficients)


def mutate_m6_average_aliases(coefficients: dict) -> dict:
    return {key: value / 2 for key, value in coefficients.items()}


MUTANT_TRANSFORMS = {
    "m1_drop_r": mutate_m1_drop_r,
    "m2_flip_one_cell": mutate_m2_flip_one_cell,
    "m3_global_sign": mutate_m3_global_sign,
    "m4_drop_half_scale": mutate_m4_drop_half_scale,
    "m5_swap_components": mutate_m5_swap_components,
    "m6_average_aliases": mutate_m6_average_aliases,
}

SWAP_COMPONENT_MUTANTS = frozenset({"m5_swap_components"})

MUTANT_MATRIX = (
    MutantRow("M1", "m1_drop_r",
              "replace coefficient m*b*r/2 with m*b/2 (drops r)",
              "kernel_zero_control",
              "D == (+1/16, -1/16) exactly"),
    MutantRow("M2", "m2_flip_one_cell",
              "replace the +1/2 coefficient at (m,b,r)=(+1,+1,+1) with -1/2 "
              "for BOTH q aliases",
              "kernel_zero_control",
              "D == (-71/64, -57/64) exactly"),
    MutantRow("M3", "m3_global_sign",
              "negate every coefficient (global sign reversal)",
              "curvature_control",
              "D_obs == -D_ref; |D_obs - D_ref| == 2*|D_ref|"),
    MutantRow("M4", "m4_drop_half_scale",
              "drop the global 1/2 scale (coefficients +/-1)",
              "curvature_control",
              "D_obs == 2*D_ref; |D_obs - D_ref| == |D_ref|"),
    MutantRow("M5", "m5_swap_components",
              "swap the two action components before accumulation",
              "curvature_control",
              "D_obs == -D_ref on the first component (K1+K2==1)"),
    MutantRow("M6", "m6_average_aliases",
              "average over q aliases instead of summing",
              "curvature_control",
              "D_obs == D_ref/2; |D_obs - D_ref| == |D_ref|/2"),
)

MUTANT_EXACT_RESPONSES = {
    "M1": (Fraction(1, 16), Fraction(-1, 16)),
    "M2": (Fraction(-71, 64), Fraction(-57, 64)),
}

# Exact multipliers relating a curvature-detected mutant's first component to
# the frozen reference.  These are algebraic consequences of the mutation, so
# they are checkable without running the float pipeline.
MUTANT_CURVATURE_MULTIPLIERS = {
    "M3": Fraction(-1),
    "M4": Fraction(2),
    "M5": Fraction(-1),
    "M6": Fraction(1, 2),
}


def mutant_dispatch_gate() -> None:
    """Every mutant row resolves to a real function, and vice versa."""
    row_ids = tuple(row.transform_id for row in MUTANT_MATRIX)
    if len(frozenset(row_ids)) != len(row_ids):
        raise ContractError("duplicate mutant transform id")
    if frozenset(row_ids) != frozenset(MUTANT_TRANSFORMS):
        raise ContractError("mutant rows and transforms are not in bijection")
    for row in MUTANT_MATRIX:
        transform = MUTANT_TRANSFORMS[row.transform_id]
        if not callable(transform):
            raise ContractError("mutant transform is not callable")
    detectors = frozenset(row.detector for row in MUTANT_MATRIX)
    if not detectors <= frozenset({"kernel_zero_control", "curvature_control"}):
        raise ContractError("unknown mutant detector")
    covered = frozenset(MUTANT_EXACT_RESPONSES) | frozenset(
        MUTANT_CURVATURE_MULTIPLIERS)
    if covered != frozenset(row.mutant_id for row in MUTANT_MATRIX):
        raise ContractError("mutant response coverage incomplete")


def run_mutant_exact(mutant_id: str) -> tuple:
    """Run a zero-control-detected mutant over the exact kernel table."""
    row = next(r for r in MUTANT_MATRIX if r.mutant_id == mutant_id)
    if row.detector != "kernel_zero_control":
        raise ContractError("mutant %s is not zero-control detected"
                            % (mutant_id,))
    # No component-swap branch here: the only swap mutant is curvature
    # detected, so the branch was unreachable behind the check above.  The
    # swap is applied in :func:`numerics.curvature_mutant_response_gate`,
    # where it can actually run.
    mutated = MUTANT_TRANSFORMS[row.transform_id](coefficient_map())
    return exact_accumulate(kernel_control_values(), mutated)


def mutant_response_gate() -> None:
    """Each zero-control mutant produces exactly its frozen response.

    The unmutated accumulation is exactly zero, so any nonzero response also
    proves the control can separate the mutant from the true coefficients --
    which is the property that makes these controls evidence rather than
    decoration.
    """
    baseline = exact_accumulate(kernel_control_values(), coefficient_map())
    if baseline != (Fraction(0), Fraction(0)):
        raise ContractError("kernel control baseline is not zero")
    for mutant_id, expected in MUTANT_EXACT_RESPONSES.items():
        observed = run_mutant_exact(mutant_id)
        if observed != expected:
            raise ContractError(
                "mutant %s response %r != frozen %r"
                % (mutant_id, observed, expected))
        if observed == baseline:
            raise ContractError("mutant %s is undetected" % (mutant_id,))


# ---------------------------------------------------------------------------
# Frozen numeric constants
# ---------------------------------------------------------------------------

CURVATURE_REFERENCE_FIRST_COMPONENT = DecimalLiteral(
    "-0.014701606964002677844581595864520080")
TOL_RECOVER = RationalValue(1, 2**40)
TOL_CURV = RationalValue(8 * 2**12 + 1, 2**52)  # 8*2^-40 + 2^-52 exactly

# Detection margin for the curvature control.  It must sit strictly between
# the numerical tolerance and the SMALLEST mutant response.
#
# D0.3/D0.4 froze 1/128 and rounds 5-6 verified it against the tolerance
# only -- (1/128)/(4*tol_curv) ~= 2^28, which is true.  Nobody checked it
# against the mutants until the executable gate did: the smallest response is
# M6 at |D_ref|/2 ~= 0.0073508, and 1/128 = 0.0078125 exceeds it, so under
# the frozen margin M6 would have been undetectable.  1/256 = 0.00390625
# clears M6 by ~1.88x and still dominates 4*tol_curv by ~2^27.
MARGIN = RationalValue(1, 256)


def tolerance_gate() -> None:
    """The frozen tolerances are the exact values the proof needs."""
    if TOL_RECOVER.as_fraction() != Fraction(1, 2**40):
        raise ContractError("tol_recover is not 2^-40")
    if TOL_CURV.as_fraction() != 8 * Fraction(1, 2**40) + Fraction(1, 2**52):
        raise ContractError("tol_curv is not 8*tol_recover + 2^-52")
    if TOL_CURV.numerator % 2 == 0:
        raise ContractError("tol_curv is not in lowest terms")
    if MARGIN.as_fraction() <= 4 * TOL_CURV.as_fraction():
        raise ContractError("margin does not dominate 4*tol_curv")


# ---------------------------------------------------------------------------
# Table digests
# ---------------------------------------------------------------------------


def _rows_digest(schema_id: str, rows: tuple) -> str:
    return sha256_hex(b"".join(serialize_struct(schema_id, row)
                               for row in rows))


def logit_control_digest() -> str:
    return _rows_digest("LogitRow" + D2, LOGIT_SEPARABLE_CONTROL)


def kernel_control_digest() -> str:
    return _rows_digest("KernelRow" + D2, KERNEL_ZERO_CONTROL)


def coefficient_oracle_digest() -> str:
    return _rows_digest("CoefficientRow" + D2, COEFFICIENT_ORACLE)


def mutant_matrix_digest() -> str:
    return _rows_digest("MutantRow" + D2, MUTANT_MATRIX)
