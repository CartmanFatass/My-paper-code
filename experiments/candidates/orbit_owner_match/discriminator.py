"""The target actor, the estimand, and the execution ledger that gates them.

This is the only module that evaluates anything scientific.  Everything it
exposes is inert until called, and every actor evaluation increments
:data:`EXECUTION_LEDGER`.  The freeze evidence asserts that counter is zero,
which turns "the discriminator was not executed" from a promise into a
checkable fact -- and one that a reviewer can re-check by running the audit
themselves.

The separation is structural, not stylistic: :mod:`block` constructs cells
and proves closure over their INPUTS without importing this module at all, so
the claim "cells constructed, discriminator not executed" is visible in the
import graph.

Target algebra (hand-proved in D0.3, independently verified in round 5):
``logit = 0.5 * m_c * b_c * r_c`` with centered codes, so the pure
three-factor contrast is ``Z^L = (m*b*r/8) * (4, -4)``, giving
``Theta_L = 4*sqrt(2)`` and ``Theta_K = 4*tanh(1/2) ~= 1.8485``.
"""

from __future__ import annotations

import math

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    _softmax,
    restore_clone,
    serialize_snapshot,
    Snapshot,
)

from experiments.candidates.orbit_owner_match.canon import ContractError
from experiments.candidates.orbit_owner_match.records import (
    ActorInput_D2,
    CalibrationRecord,
    DiameterRecord,
    EstimandRecord,
    ReplicaRecord,
)
from experiments.candidates.orbit_owner_match.controls import (
    ALIASES,
    SIGNS,
    check_value_domain,
    coefficient_map,
    exact_accumulate,
)
from experiments.candidates.orbit_owner_match.canon import sha256_hex
from experiments.candidates.orbit_owner_match.trust import (
    CALIBRATION_SNAPSHOT_DIGEST,
    SOURCE_SNAPSHOT_DIGEST,
    build_d1_actor_input,
    build_write_d2_with_b,
    declassify,
    extend_d1_actor_input,
    verify_write_d2,
)


# ---------------------------------------------------------------------------
# Execution ledger
# ---------------------------------------------------------------------------

EXECUTION_LEDGER = {"actor_calls": 0, "block_evaluations": 0,
                    "calibration_runs": 0}


def execution_ledger_gate() -> None:
    """No scientific evaluation has happened in this process.

    This is the freeze-evidence gate.  It is expected to FAIL once the
    discriminator is authorized and actually run; at freeze time it must pass.

    The ledger is MONOTONE: there is deliberately no reset.  An earlier
    version exposed one, which meant the gate certified "not executed" only
    relative to the last reset -- a full run followed by a reset produced
    an all-zero ledger and a clean freeze.  Because the counters can only
    rise, the evidence must be generated in a process that has never run the
    discriminator, which is the property the freeze actually needs.
    """
    for name in sorted(EXECUTION_LEDGER):
        if EXECUTION_LEDGER[name] != 0:
            raise ContractError(
                "execution ledger is nonzero: %s=%d"
                % (name, EXECUTION_LEDGER[name]), "T4")


# ---------------------------------------------------------------------------
# Target actor
# ---------------------------------------------------------------------------


def owner_predicate_actor(actor_input: ActorInput_D2) -> tuple:
    """Read set: exactly ``{verified_owner_match, actor_tensor[-2:]}``.

    Round 4 found that D0.2's registered read set excluded
    ``verified_owner_match``, which made the target M-blind under its own
    closure rules and therefore unable to realize the estimand at all.
    """
    if type(actor_input) is not ActorInput_D2:
        raise ContractError("exact ActorInput_D2 required")
    EXECUTION_LEDGER["actor_calls"] += 1
    b, role = (int(value) for value in actor_input.actor_tensor[-2:])
    sign = 1.0 if actor_input.verified_owner_match else -1.0
    interaction = 0.5 if b == role else -0.5
    logit = sign * interaction
    return logit, -logit


def centered(vector: tuple) -> tuple:
    mean = sum(vector) / len(vector)
    return tuple(value - mean for value in vector)


# ---------------------------------------------------------------------------
# Block evaluation and estimands
# ---------------------------------------------------------------------------


def evaluate_block(cells: dict) -> dict:
    """Evaluate the target actor on every constructed cell.

    THIS EXECUTES THE DISCRIMINATOR.  It is not called by any gate, freeze
    routine or digest computation.
    """
    EXECUTION_LEDGER["block_evaluations"] += 1
    logits = {}
    kernels = {}
    for key in sorted(cells):
        logit_pair = owner_predicate_actor(cells[key].actor_input)
        logits[key] = logit_pair
        kernels[key] = tuple(_softmax(logit_pair))
    check_value_domain(logits, exact=False)
    check_value_domain(kernels, exact=False)
    return {"logits": logits, "kernels": kernels}


def float_accumulate(values_by_key: dict) -> tuple:
    """Binary64 accumulation in the frozen oracle order.

    Coefficients are exactly representable (``+/-1/2``), so the only rounding
    is in the additions.
    """
    check_value_domain(values_by_key, exact=False)
    coefficients = coefficient_map()
    total = (0.0, 0.0)
    for key in sorted(values_by_key):
        weight = float(coefficients[key])
        value = values_by_key[key]
        total = tuple(total[i] + weight * value[i] for i in (0, 1))
    return total


def estimands(evaluation: dict) -> EstimandRecord:
    """Theta_logit is the L2 norm of the centered logit contrast; Theta_kernel
    is the half-L1 norm of the uncentered kernel contrast, matching the
    inherited D1 operator convention."""
    centered_logits = {key: centered(value)
                       for key, value in evaluation["logits"].items()}
    d_logit = float_accumulate(centered_logits)
    d_kernel = float_accumulate(evaluation["kernels"])
    theta_logit = math.sqrt(sum(value * value for value in d_logit))
    theta_kernel = 0.5 * sum(abs(value) for value in d_kernel)
    return EstimandRecord(d_logit, d_kernel, theta_logit, theta_kernel)


def exact_target_contrast() -> tuple:
    """The closed-form three-factor contrast, in exact rational arithmetic.

    Available without executing the float pipeline because the target logits
    are exactly ``+/-1/2``: this is the algebra round 5 verified.
    """
    from fractions import Fraction

    values = {}
    for q in ALIASES:
        for m in SIGNS:
            for b in SIGNS:
                for r in SIGNS:
                    logit = Fraction(m * b * r, 2)
                    values[(q, m, b, r)] = (logit, -logit)
    return exact_accumulate(values, coefficient_map())


# ---------------------------------------------------------------------------
# Four-replica diameter and calibration
# ---------------------------------------------------------------------------

CALIBRATION_SNAPSHOT = Snapshot(
    snapshot_id="disjoint-calibration-owner-s0",
    owner_epoch=3,
    current_state=(0.125, -0.125),
    legal_actions=("hold", "advance"),
    recurrent_state=(0.125, -0.125),
)

REPLICA_IDS = ("A-cold", "A-warm", "B-cold", "B-warm")


def _calibration_actor_input(replica_id: str) -> ActorInput_D2:
    """Build one calibration replica's input on a disjoint fixture.

    'cold' and 'warm' differ only in whether the clone is restored freshly
    for this replica or reused from a prior restore in the same process;
    'A'/'B' are two independent clone identities.  All four are the same
    mathematical input, so any spread between them is pure evaluation noise,
    which is exactly what the diameter measures.
    """
    source = serialize_snapshot(CALIBRATION_SNAPSHOT)
    clone = restore_clone(source, "calibration-clone-" + replica_id[0])
    write = build_write_d2_with_b(CALIBRATION_SNAPSHOT, "W1", 0)
    verification = verify_write_d2(clone, write)
    predicate = declassify(verification)
    base = build_d1_actor_input(clone, write, 0, 0)
    return extend_d1_actor_input(base, predicate)


def four_replica_diameter() -> DiameterRecord:
    """Componentwise diameter over the four replicas.

    Round 6 found this machinery entirely absent from D0.4 even though the
    four-replica structure had been accepted in round 4.
    """
    EXECUTION_LEDGER["calibration_runs"] += 1
    replicas = []
    for replica_id in REPLICA_IDS:
        actor_input = _calibration_actor_input(replica_id)
        logits = owner_predicate_actor(actor_input)
        kernel = tuple(_softmax(logits))
        replicas.append(ReplicaRecord(replica_id, logits, kernel))
    eta_logit = max(
        abs(a.logits[i] - b.logits[i])
        for a in replicas for b in replicas for i in (0, 1))
    eta_kernel = max(
        abs(a.kernel[i] - b.kernel[i])
        for a in replicas for b in replicas for i in (0, 1))
    return DiameterRecord(tuple(replicas), eta_logit, eta_kernel)


def calibrate() -> CalibrationRecord:
    """Derive the frozen tolerance ladder from the measured diameter.

    ``u_L = 16*eps_L`` (sixteen Hadamard terms, each carrying at most one
    ``eps``, doubled by centering across two components); ``u_K = 8*eps_K``
    (sixteen terms at coefficient ``1/2``, then the ``0.5 * L1`` operator);
    ``tau_L = sqrt(2)*u_L`` (L2 over two components), ``tau_K = u_K``;
    ``delta = 4*tau`` on both, with a STRICT ``>`` decision.  These constants
    were locked ALREADY_ADEQUATE in round 3 and are reproduced, not chosen,
    here.
    """
    diameter = four_replica_diameter()
    logits = diameter.replicas[0].logits
    kernel = diameter.replicas[0].kernel
    one_ulp_logit = math.ulp(max(1.0, *(abs(v) for v in logits)))
    one_ulp_kernel = math.ulp(max(1.0, *(abs(v) for v in kernel)))
    eps_logit = max(diameter.eta_logit, one_ulp_logit)
    eps_kernel = max(diameter.eta_kernel, one_ulp_kernel)
    u_logit = 16.0 * eps_logit
    u_kernel = 8.0 * eps_kernel
    tau_logit = math.sqrt(2.0) * u_logit
    tau_kernel = u_kernel
    return CalibrationRecord(
        sha256_hex(serialize_snapshot(CALIBRATION_SNAPSHOT)),
        diameter,
        one_ulp_logit, one_ulp_kernel,
        u_logit, u_kernel,
        tau_logit, tau_kernel,
        4.0 * tau_logit, 4.0 * tau_kernel,
    )


def calibration_fixture_gate() -> None:
    """The calibration fixture is exactly the one its binding is pinned to.

    Without this, editing the fixture would silently orphan the calibration
    binding and every calibration verification would fail closed at run time
    instead of at freeze time.
    """
    digest = sha256_hex(serialize_snapshot(CALIBRATION_SNAPSHOT))
    if digest != CALIBRATION_SNAPSHOT_DIGEST:
        raise ContractError("calibration fixture digest drift")
    if digest == SOURCE_SNAPSHOT_DIGEST:
        raise ContractError("calibration fixture is not disjoint")


def calibration_disjointness_gate(calibration: CalibrationRecord,
                                  source_snapshot_digest: str) -> None:
    """Calibration must not run on the discriminator's own fixture."""
    if type(calibration) is not CalibrationRecord:
        raise ContractError("exact CalibrationRecord required")
    if calibration.calibration_snapshot_digest == source_snapshot_digest:
        raise ContractError("calibration fixture is not disjoint")
    if len(calibration.diameter.replicas) != 4:
        raise ContractError("four replicas required")
    if len({r.replica_id for r in calibration.diameter.replicas}) != 4:
        raise ContractError("replica ids are not distinct")


def calibration_authenticity_gate(calibration: CalibrationRecord) -> None:
    """The calibration record is internally consistent with its own replicas.

    Checking only that the numbers are finite, positive and satisfy
    ``delta == 4*tau`` leaves every threshold trivially forgeable: any
    literal ladder passes.  This recomputes the whole ladder -- diameter,
    ulp, u, tau, delta -- from the replicas the record itself carries, and
    pins the fixture digest to the frozen literal rather than to "anything
    that differs from the discriminator's".
    """
    if type(calibration) is not CalibrationRecord:
        raise ContractError("exact CalibrationRecord required")
    if calibration.calibration_snapshot_digest != CALIBRATION_SNAPSHOT_DIGEST:
        raise ContractError("calibration fixture digest is not the frozen one")
    replicas = calibration.diameter.replicas
    if type(replicas) is not tuple or len(replicas) != 4:
        raise ContractError("four replicas required")
    eta_logit = max(abs(a.logits[i] - b.logits[i])
                    for a in replicas for b in replicas for i in (0, 1))
    eta_kernel = max(abs(a.kernel[i] - b.kernel[i])
                     for a in replicas for b in replicas for i in (0, 1))
    if eta_logit != calibration.diameter.eta_logit:
        raise ContractError("recorded eta_logit is not the replica diameter")
    if eta_kernel != calibration.diameter.eta_kernel:
        raise ContractError("recorded eta_kernel is not the replica diameter")
    one_ulp_logit = math.ulp(max(1.0, *(abs(v) for v in replicas[0].logits)))
    one_ulp_kernel = math.ulp(max(1.0, *(abs(v) for v in replicas[0].kernel)))
    if (one_ulp_logit != calibration.one_ulp_logit
            or one_ulp_kernel != calibration.one_ulp_kernel):
        raise ContractError("recorded ulp does not match the replica values")
    u_logit = 16.0 * max(eta_logit, one_ulp_logit)
    u_kernel = 8.0 * max(eta_kernel, one_ulp_kernel)
    if u_logit != calibration.u_logit or u_kernel != calibration.u_kernel:
        raise ContractError("recorded u is not the frozen multiple of eps")
    if calibration.tau_logit != math.sqrt(2.0) * u_logit:
        raise ContractError("recorded tau_logit is not sqrt(2)*u_logit")
    if calibration.tau_kernel != u_kernel:
        raise ContractError("recorded tau_kernel is not u_kernel")
    if calibration.delta_logit != 4.0 * calibration.tau_logit:
        raise ContractError("recorded delta_logit is not 4*tau_logit")
    if calibration.delta_kernel != 4.0 * calibration.tau_kernel:
        raise ContractError("recorded delta_kernel is not 4*tau_kernel")


def estimand_authenticity_gate(estimand: EstimandRecord,
                               evaluation: dict) -> None:
    """The estimand is the one this evaluation produces.

    Without it, ``theta`` is just a number a caller supplied next to a set of
    cells it need not have come from.
    """
    if type(estimand) is not EstimandRecord:
        raise ContractError("exact EstimandRecord required")
    recomputed = estimands(evaluation)
    if recomputed.d_logit != estimand.d_logit:
        raise ContractError("d_logit does not match the evaluation")
    if recomputed.d_kernel != estimand.d_kernel:
        raise ContractError("d_kernel does not match the evaluation")
    if recomputed.theta_logit != estimand.theta_logit:
        raise ContractError("theta_logit does not match the evaluation")
    if recomputed.theta_kernel != estimand.theta_kernel:
        raise ContractError("theta_kernel does not match the evaluation")
