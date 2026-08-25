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

LEDGER_COUNTERS = ("actor_calls", "block_evaluations", "calibration_runs")


class ExecutionLedger:
    """Increment-only counters for every scientific evaluation.

    Round 7 broke D0.5's ledger in one line.  It was a module-level ``dict``,
    so ``EXECUTION_LEDGER["actor_calls"] = 0`` restored an all-zero reading
    after a full run and :func:`execution_ledger_gate` passed.  Removing the
    ``reset`` HELPER, which is what D0.5 did, does not remove the ability to
    reset a mutable mapping that is exported by name.

    This class removes the ordinary spellings ON THE INSTANCE: there is no
    ``__setitem__``, attribute assignment and deletion raise, and the
    counters live in ``__slots__`` so no instance ``__dict__`` shadows them.

    It does NOT defend the NAME.  An earlier version of this docstring said
    it "removes the ordinary spellings" without that qualifier, which was
    wrong: rebinding the module global IS the ordinary spelling, one scope
    up, and

        discriminator.EXECUTION_LEDGER = ExecutionLedger()

    resets the reading with :func:`execution_ledger_gate` and both runtime
    seals still passing.  ``PROCESS_STATE_GLOBALS`` pins this slot by type,
    not by value, because the value is supposed to change.  A same-typed
    replacement is therefore invisible to the seal by construction.  So is
    neutering :meth:`increment`, whose code is outside every digest.

    It is NOT tamper-proof and the contract does not claim it is; the
    evidence that carries weight is an externally launched clean process,
    not this counter.  See :func:`execution_ledger_gate`.
    """

    __slots__ = LEDGER_COUNTERS

    def __init__(self) -> None:
        for name in LEDGER_COUNTERS:
            object.__setattr__(self, name, 0)

    def __setattr__(self, name, value):
        raise ContractError("execution ledger is increment-only", "T4")

    def __delattr__(self, name):
        raise ContractError("execution ledger is increment-only", "T4")

    def increment(self, name: str) -> None:
        if name not in LEDGER_COUNTERS:
            raise ContractError("unknown ledger counter %r" % (name,), "T4")
        object.__setattr__(self, name, object.__getattribute__(self, name) + 1)

    def snapshot(self) -> dict:
        return {name: object.__getattribute__(self, name)
                for name in LEDGER_COUNTERS}


EXECUTION_LEDGER = ExecutionLedger()


def execution_ledger_gate() -> None:
    """The counters read zero at the moment this gate runs.

    That is the whole claim, and D0.5 overstated it.  Its docstring said the
    ledger was monotone and therefore that an all-zero reading PROVED the
    process had never run the discriminator; the exported dict made that
    false.  The counters are now increment-only against ordinary mutation,
    but an in-process adversary with ``object.__setattr__`` is outside what
    any in-process counter can exclude.

    The freeze therefore does not rest on this gate alone.  It rests on this
    gate plus ``scripts/orbit_owner_freeze_evidence.py``, which runs the
    audit in a separately launched interpreter that imports the package and
    does nothing else, and on :mod:`block` not importing this module at all --
    a structural fact anyone can check by reading the import graph rather
    than by trusting a counter.
    """
    counts = EXECUTION_LEDGER.snapshot()
    for name in sorted(counts):
        if counts[name] != 0:
            raise ContractError(
                "execution ledger is nonzero: %s=%d" % (name, counts[name]),
                "T4")


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
    EXECUTION_LEDGER.increment("actor_calls")
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

    The result records a digest of the cells it actually read, so the
    downstream estimand can be tied back to a specific census rather than to
    "some evaluation dict" (round-7 correction D05-C06).
    """
    EXECUTION_LEDGER.increment("block_evaluations")
    logits = {}
    kernels = {}
    for key in sorted(cells):
        logit_pair = owner_predicate_actor(cells[key].actor_input)
        logits[key] = logit_pair
        kernels[key] = tuple(_softmax(logit_pair))
    check_value_domain(logits, exact=False)
    check_value_domain(kernels, exact=False)
    return {"logits": logits, "kernels": kernels,
            "census_digest": evaluated_census_digest(cells)}


def evaluated_census_digest(cells: dict) -> str:
    """Digest of the cells an evaluation read, in frozen key order."""
    from experiments.candidates.orbit_owner_match.canon import (
        _enc_str, serialize_struct,
    )
    from experiments.candidates.orbit_owner_match.records import (
        SCHEMA_TARGET_CELL,
    )
    parts = []
    for key in sorted(cells):
        parts.append(_enc_str(repr(key)))
        parts.append(serialize_struct(SCHEMA_TARGET_CELL, cells[key]))
    return sha256_hex(b"".join(parts))


def evaluation_census_gate(evaluation: dict, cells: dict) -> None:
    """The evaluation is of THIS census.

    Without it, ``estimand_authenticity_gate`` proves only that the estimand
    matches the evaluation it was handed -- an internally consistent pair that
    need not have anything to do with the census the block gates validated.
    """
    if type(evaluation) is not dict:
        raise ContractError("exact dict evaluation required")
    recorded = evaluation.get("census_digest")
    if type(recorded) is not str:
        raise ContractError("evaluation carries no census digest", "T1")
    if recorded != evaluated_census_digest(cells):
        raise ContractError(
            "evaluation is not of the validated census", "T1")


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

# (clone label, prior uses of that clone object) in execution order.  Cold is
# the first evaluation on a freshly restored clone; warm is the second
# evaluation on THAT SAME object.
REPLICA_PROTOCOL = (("A", 0), ("A", 1), ("B", 0), ("B", 1))


def _calibration_actor_input(clone) -> ActorInput_D2:
    """Build one calibration replica's input on a disjoint fixture.

    Takes the clone rather than a replica name.  D0.5 took the name and
    called ``restore_clone`` on every invocation, so all four replicas ran on
    freshly restored objects: 'A-warm' and 'B-warm' were labels for
    evaluations that were as cold as the other two, and the four-replica
    diameter measured four repetitions of one condition instead of the
    cold/warm structure accepted in round 4.
    """
    write = build_write_d2_with_b(CALIBRATION_SNAPSHOT, "W1", 0)
    verification = verify_write_d2(clone, write)
    predicate = declassify(verification)
    base = build_d1_actor_input(clone, write, 0, 0)
    return extend_d1_actor_input(base, predicate)


def four_replica_diameter() -> DiameterRecord:
    """Componentwise diameter over the four replicas.

    Two clone objects, each evaluated twice: cold then warm, in that order,
    on the same object.  The reuse is asserted by identity (``is``), not
    inferred from the labels.
    """
    EXECUTION_LEDGER.increment("calibration_runs")
    source = serialize_snapshot(CALIBRATION_SNAPSHOT)
    clones = {label: restore_clone(source, "calibration-clone-" + label)
              for label in ("A", "B")}
    if clones["A"] is clones["B"]:
        raise ContractError("calibration clones A and B are the same object")
    uses = {"A": 0, "B": 0}
    used_objects = {}
    replicas = []
    for label, expected_prior in REPLICA_PROTOCOL:
        clone = clones[label]
        if uses[label] != expected_prior:
            raise ContractError(
                "calibration replica order violated at %s: %d prior uses, "
                "protocol expects %d" % (label, uses[label], expected_prior))
        if expected_prior == 0:
            used_objects[label] = clone
        elif used_objects[label] is not clone:
            raise ContractError(
                "warm replica %s did not reuse the cold replica's clone"
                % (label,))
        actor_input = _calibration_actor_input(clone)
        uses[label] = expected_prior + 1
        logits = owner_predicate_actor(actor_input)
        kernel = tuple(_softmax(logits))
        replicas.append(ReplicaRecord(
            "%s-%s" % (label, "cold" if expected_prior == 0 else "warm"),
            logits, kernel, clone.clone_id, expected_prior))
    if tuple(r.replica_id for r in replicas) != REPLICA_IDS:
        raise ContractError("replica ids are not the frozen protocol order")
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
    # The cold/warm protocol is part of what "four replicas" means: two clone
    # labels, each appearing once cold and once warm, in the frozen order.
    if tuple(r.replica_id for r in replicas) != REPLICA_IDS:
        raise ContractError("replica ids are not the frozen protocol order")
    for replica, (label, prior) in zip(replicas, REPLICA_PROTOCOL):
        if type(replica) is not ReplicaRecord:
            raise ContractError("exact ReplicaRecord required")
        if replica.clone_label != "calibration-clone-" + label:
            raise ContractError(
                "replica %r is not on clone %s" % (replica.replica_id, label))
        if replica.prior_uses != prior:
            raise ContractError(
                "replica %r records %d prior uses, protocol expects %d"
                % (replica.replica_id, replica.prior_uses, prior))
    if len({r.clone_label for r in replicas}) != 2:
        raise ContractError("calibration does not use exactly two clones")
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
