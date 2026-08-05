"""Binary64 recovery, the curvature control, and platform admission.

Three round-6 omissions are closed here:

*   ``no binary64 softmax(log K) recovery function`` and ``no executable
    propagated 8*tol_recover gate`` -- :func:`recovery_gate` runs the actual
    float pipeline over the frozen kernel control and checks both the
    per-component envelope and its propagation through the operator.
*   ``no curvature-control float pipeline`` -- :func:`curvature_gate`
    evaluates the control in binary64 and compares it to the frozen
    high-precision reference within ``tol_curv``.
*   ``D04-V02: admit the stated libm contract on the final platform`` --
    :func:`platform_admission` measures the actual relative error of
    ``math.log`` and ``math.exp`` on exactly the arguments the derivation
    uses, against an independent high-precision evaluator, and refuses to
    admit a platform that violates the contract the proof assumes.

A counter distinct from the discriminator's execution ledger records that
these numerical self-audits ran: they are properties of frozen, externally
verified tables, not evaluations of the target, so they must not be confused
with executing the discriminator.
"""

from __future__ import annotations

import math
from fractions import Fraction

from experiments.candidates.orbit_shadow_read.eight_cell_audit import _softmax

from experiments.candidates.orbit_owner_match.canon import ContractError
from experiments.candidates.orbit_owner_match.records import DecimalLiteral
from experiments.candidates.orbit_owner_match.controls import (
    ALIASES,
    KERNEL_ZERO_CONTROL,
    MARGIN,
    MUTANT_CURVATURE_MULTIPLIERS,
    MUTANT_MATRIX,
    MUTANT_TRANSFORMS,
    SIGNS,
    SWAP_COMPONENT_MUTANTS,
    TOL_CURV,
    TOL_RECOVER,
    coefficient_map,
    exact_accumulate,
)


NUMERIC_AUDIT_LEDGER = {"recovery_checks": 0, "curvature_checks": 0,
                        "curvature_mutant_checks": 0,
                        "platform_admissions": 0}

# The relative-error contract the recovery derivation assumes of the platform
# libm: log and exp correctly rounded to within one unit in the last place.
LIBM_RELATIVE_ERROR_BOUND = Fraction(1, 2**52)


def _mpmath():
    import mpmath
    return mpmath


# ---------------------------------------------------------------------------
# Binary64 recovery: softmax(log K) == K
# ---------------------------------------------------------------------------


def binary64_recovery(kernel_pair: tuple) -> tuple:
    """Recover a kernel row from its logarithms in binary64.

    The op sequence deliberately mirrors the inherited ``_softmax``: take
    logs, shift by the componentwise maximum, exponentiate, sum, divide.  The
    derivation bounds each of those five stages separately, so the code must
    perform exactly those stages for the bound to apply to it.
    """
    if type(kernel_pair) is not tuple or len(kernel_pair) != 2:
        raise ContractError("exact two-component kernel row required")
    for component in kernel_pair:
        if type(component) is not float:
            raise ContractError("exact float kernel component required")
        if not (0.0 < component < 1.0):
            raise ContractError("kernel component outside the open simplex")
    logs = tuple(math.log(component) for component in kernel_pair)
    return tuple(_softmax(logs))


def recovery_residuals() -> list:
    residuals = []
    for row in KERNEL_ZERO_CONTROL:
        exact = (row.k1.as_fraction(), row.k2.as_fraction())
        as_float = tuple(float(value) for value in exact)
        recovered = binary64_recovery(as_float)
        for index in (0, 1):
            residuals.append(abs(Fraction(recovered[index]) - exact[index]))
    return residuals


def recovery_gate() -> None:
    """Per-component recovery and the propagated OPERATOR error are bounded.

    The second check used to be ``8*worst > 8*tolerance``, which is
    algebraically the first check and could never add information.  It now
    accumulates the RECOVERED rows through the real operator and bounds the
    distance from the exact contrast -- the quantity the derivation's
    ``8 * tol_recover`` propagation is actually about.  The factor 8 is the
    total absolute coefficient mass: sixteen terms at ``1/2``.
    """
    NUMERIC_AUDIT_LEDGER["recovery_checks"] += 1
    tolerance = TOL_RECOVER.as_fraction()
    worst = max(recovery_residuals())
    if worst > tolerance:
        raise ContractError(
            "recovery residual %s exceeds tol_recover" % (float(worst),))
    coefficients = coefficient_map()
    coefficient_mass = sum(abs(value) for value in coefficients.values())
    if coefficient_mass != 8:
        raise ContractError("coefficient mass is not 8; propagation invalid")

    exact_values = {}
    recovered_values = {}
    for row in KERNEL_ZERO_CONTROL:
        exact = (row.k1.as_fraction(), row.k2.as_fraction())
        recovered = binary64_recovery(tuple(float(v) for v in exact))
        for q in ALIASES:
            key = (q, row.m, row.b, row.r)
            exact_values[key] = exact
            recovered_values[key] = (Fraction(recovered[0]),
                                     Fraction(recovered[1]))
    exact_contrast = exact_accumulate(exact_values, coefficients)
    recovered_contrast = exact_accumulate(recovered_values, coefficients)
    envelope = coefficient_mass * tolerance
    for index in (0, 1):
        deviation = abs(recovered_contrast[index] - exact_contrast[index])
        if deviation > envelope:
            raise ContractError(
                "propagated recovery envelope violated on component %d"
                % (index,))


def recovery_worst_residual() -> Fraction:
    return max(recovery_residuals())


# ---------------------------------------------------------------------------
# Curvature control
# ---------------------------------------------------------------------------


def curvature_logit_row(m: int, b: int, r: int) -> tuple:
    """The frozen curvature control logit row ``(1/4 + b/4 + m*r/4, 0)``.

    Unlike the zero controls this row is deliberately curved, which is what
    lets it detect the global sign and scale mutants that a zero-contrast
    control provably cannot (``0 == -0 == 2*0``).
    """
    return (0.25 + b * 0.25 + (m * r) * 0.25, 0.0)


def curvature_values() -> dict:
    """Binary64 kernel values of the curvature control, keyed as usual."""
    values = {}
    for q in ALIASES:
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    kernel = _softmax(curvature_logit_row(m, b, r))
                    values[(q, m, b, r)] = (kernel[0], kernel[1])
    return values


def curvature_accumulate(values: dict, coefficients: dict) -> float:
    """First-component accumulation in the frozen oracle order."""
    total = 0.0
    for key in sorted(values):
        total += float(coefficients[key]) * values[key][0]
    return total


def curvature_reference_float() -> float:
    """Binary64 evaluation of the curvature control's first component."""
    return curvature_accumulate(curvature_values(), coefficient_map())


def curvature_mutant_response_gate() -> None:
    """Each curvature-detected mutant is RUN, and lands where the table says.

    The multipliers used to be unchecked literals: ``mutant_dispatch_gate``
    only asserted the transforms were callable and ``curvature_gate``
    consumed the multipliers as numbers, so nothing ever applied M3-M6.  Six
    mutants advertised as executable were executable in two cases.  A typo in
    the multiplier table would have frozen a wrong margin argument with no
    test able to notice.

    This also gives :data:`MARGIN` its only real consumer: each mutant's
    deviation from the reference must exceed it.
    """
    NUMERIC_AUDIT_LEDGER["curvature_mutant_checks"] += 1
    baseline = curvature_reference_float()
    if baseline == 0.0:
        raise ContractError("curvature reference is zero; cannot detect scale")
    margin = float(MARGIN.as_fraction())
    tolerance = float(TOL_CURV.as_fraction())
    checked = set()
    for row in MUTANT_MATRIX:
        if row.detector != "curvature_control":
            continue
        multiplier = MUTANT_CURVATURE_MULTIPLIERS[row.mutant_id]
        values = curvature_values()
        if row.transform_id in SWAP_COMPONENT_MUTANTS:
            values = {key: (value[1], value[0])
                      for key, value in values.items()}
        mutated = MUTANT_TRANSFORMS[row.transform_id](coefficient_map())
        observed = curvature_accumulate(values, mutated)
        expected = float(multiplier) * baseline
        if abs(observed - expected) > tolerance:
            raise ContractError(
                "mutant %s response %r is not %s * reference"
                % (row.mutant_id, observed, multiplier))
        if abs(observed - baseline) <= margin:
            raise ContractError(
                "mutant %s deviation does not clear the margin"
                % (row.mutant_id,))
        checked.add(row.mutant_id)
    if checked != frozenset(MUTANT_CURVATURE_MULTIPLIERS):
        raise ContractError("curvature mutant coverage incomplete")


def hp_curvature_reference(dps: int):
    """Independent high-precision evaluator; shares no code with the float
    pipeline (round-4 requirement: a same-pipeline reference is circular)."""
    mpmath = _mpmath()
    with mpmath.workdps(dps):
        total = mpmath.mpf(0)
        for q in ALIASES:
            for m in SIGNS:
                for b in SIGNS:
                    for r in SIGNS:
                        l1 = (mpmath.mpf(1) / 4 + mpmath.mpf(b) / 4
                              + mpmath.mpf(m * r) / 4)
                        e1 = mpmath.exp(l1)
                        total += mpmath.mpf(m * b * r) / 2 * (e1 / (e1 + 1))
        return total


def hp_recovery_identity_check(dps: int):
    """``softmax(log K) == K`` at high precision for every control row."""
    mpmath = _mpmath()
    with mpmath.workdps(dps):
        worst = mpmath.mpf(0)
        for row in KERNEL_ZERO_CONTROL:
            k = (mpmath.mpf(row.k1.numerator) / row.k1.denominator,
                 mpmath.mpf(row.k2.numerator) / row.k2.denominator)
            logs = tuple(mpmath.log(value) for value in k)
            shift = max(logs)
            exps = tuple(mpmath.exp(value - shift) for value in logs)
            denominator = exps[0] + exps[1]
            recovered = (exps[0] / denominator, exps[1] / denominator)
            for got, want in zip(recovered, k):
                worst = max(worst, abs(got - want))
        return worst


CURVATURE_STABILITY_TOLERANCE_EXPONENT = 50


def curvature_reference_stability_gate() -> None:
    """The high-precision reference is precision-stable.

    Comparing the two evaluations for exact equality would compare mpf
    objects carried at different working precisions, which is a statement
    about representation rather than about the value.  The check is therefore
    an explicit agreement bound, far tighter than any tolerance the contract
    relies on.
    """
    mpmath = _mpmath()
    at_60 = hp_curvature_reference(60)
    at_120 = hp_curvature_reference(120)
    with mpmath.workdps(120):
        tolerance = mpmath.mpf(10) ** (-CURVATURE_STABILITY_TOLERANCE_EXPONENT)
        if abs(mpmath.mpf(at_60) - mpmath.mpf(at_120)) > tolerance:
            raise ContractError("curvature reference is not precision-stable")


def curvature_gate() -> None:
    """The binary64 curvature value matches the frozen reference within
    ``tol_curv``, and the mutant margin dominates that tolerance."""
    NUMERIC_AUDIT_LEDGER["curvature_checks"] += 1
    mpmath = _mpmath()
    with mpmath.workdps(60):
        reference = hp_curvature_reference(60)
        observed = mpmath.mpf(curvature_reference_float())
        residual = abs(observed - reference)
        tolerance = mpmath.mpf(TOL_CURV.numerator) / TOL_CURV.denominator
        if residual > tolerance:
            raise ContractError("curvature residual exceeds tol_curv")
        margin = mpmath.mpf(MARGIN.numerator) / MARGIN.denominator
        if margin <= 4 * tolerance:
            raise ContractError("margin does not dominate 4*tol_curv")
        # Derive the smallest detectable response from the mutant table
        # rather than hardcoding it, so adding a subtler mutant later forces
        # the margin to be revisited instead of silently going undetected.
        smallest_multiplier = min(
            abs(multiplier - 1)
            for multiplier in MUTANT_CURVATURE_MULTIPLIERS.values())
        smallest_gap = (abs(reference)
                        * mpmath.mpf(smallest_multiplier.numerator)
                        / smallest_multiplier.denominator)
        if smallest_gap <= margin:
            raise ContractError(
                "smallest mutant response does not clear the margin")


def frozen_curvature_literal_gate(frozen_text: str) -> None:
    """The frozen decimal literal agrees with the reference to its last digit.

    Interpreting the literal as an exact decimal and bounding the difference
    by one unit in its last decimal place is a statement about the number;
    string-prefix matching would instead be a statement about mpmath's
    rendering, which is not what the contract needs to freeze.
    """
    mpmath = _mpmath()
    if type(frozen_text) is not str or "." not in frozen_text:
        raise ContractError("frozen curvature literal must be decimal text")
    decimals = len(frozen_text.split(".", 1)[1])
    with mpmath.workdps(120):
        reference = mpmath.mpf(hp_curvature_reference(120))
        literal = mpmath.mpf(frozen_text)
        if abs(reference - literal) > mpmath.mpf(10) ** (-decimals):
            raise ContractError(
                "frozen curvature literal disagrees with the reference")


# ---------------------------------------------------------------------------
# Platform admission (D04-V02)
# ---------------------------------------------------------------------------


def _relative_error(observed, exact) -> object:
    if exact == 0:
        return abs(observed - exact)
    return abs(observed - exact) / abs(exact)


def platform_admission() -> tuple:
    """Measure this platform's ``log``/``exp`` against the assumed contract.

    Returns ``(worst_log, worst_exp, worst_recovery)`` as high-precision
    values.  The derivation's ``< 2^-47`` per-component conclusion is
    conditional on these staying within one ulp of relative error; without
    this check the conclusion is an assumption about an unexamined machine.
    """
    NUMERIC_AUDIT_LEDGER["platform_admissions"] += 1
    mpmath = _mpmath()
    bound = None
    with mpmath.workdps(60):
        bound = (mpmath.mpf(LIBM_RELATIVE_ERROR_BOUND.numerator)
                 / LIBM_RELATIVE_ERROR_BOUND.denominator)
        worst_log = mpmath.mpf(0)
        worst_exp = mpmath.mpf(0)
        log_arguments = []
        for row in KERNEL_ZERO_CONTROL:
            log_arguments.append(row.k1.as_fraction())
            log_arguments.append(row.k2.as_fraction())
        # The measurement compares math.log(float(x)) against the exact log of
        # the RATIONAL x, so it folds the Fraction->float rounding into the
        # reported "libm error".  That is only harmless while every control
        # value is exactly representable; assert it rather than rely on it,
        # or a future non-dyadic table would fail the platform for the wrong
        # reason.
        for argument in log_arguments:
            if Fraction(float(argument)) != argument:
                raise ContractError(
                    "control value %s is not exactly representable; the "
                    "platform measurement would conflate conversion error "
                    "with libm error" % (argument,), "T3")
        for argument in log_arguments:
            exact = mpmath.log(mpmath.mpf(argument.numerator)
                               / argument.denominator)
            observed = mpmath.mpf(math.log(float(argument)))
            worst_log = max(worst_log,
                            _relative_error(observed, exact))
        exp_arguments = []
        for row in KERNEL_ZERO_CONTROL:
            k1 = float(row.k1.as_fraction())
            k2 = float(row.k2.as_fraction())
            logs = (math.log(k1), math.log(k2))
            shift = max(logs)
            exp_arguments.extend([logs[0] - shift, logs[1] - shift])
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    row = curvature_logit_row(m, b, r)
                    shift = max(row)
                    exp_arguments.extend([row[0] - shift, row[1] - shift])
        for argument in exp_arguments:
            exact = mpmath.exp(mpmath.mpf(argument))
            observed = mpmath.mpf(math.exp(argument))
            worst_exp = max(worst_exp,
                            _relative_error(observed, exact))
        worst_recovery = hp_recovery_identity_check(60)
        if worst_log > bound:
            raise ContractError(
                "platform log exceeds the assumed relative-error contract",
                "T3")
        if worst_exp > bound:
            raise ContractError(
                "platform exp exceeds the assumed relative-error contract",
                "T3")
        return (worst_log, worst_exp, worst_recovery)


def platform_admission_literals() -> tuple:
    mpmath = _mpmath()
    worst_log, worst_exp, worst_recovery = platform_admission()
    with mpmath.workdps(60):
        return (DecimalLiteral(mpmath.nstr(worst_log, 20)),
                DecimalLiteral(mpmath.nstr(worst_exp, 20)),
                DecimalLiteral(mpmath.nstr(worst_recovery, 20)))


def platform_admission_gate() -> None:
    platform_admission()
