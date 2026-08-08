"""The frozen validity-gate suite and the total terminal controller.

Round 6 found two structural defects in D0.4's controller, both fixed here.

``the gate set was caller-selectable``
    ``terminal_controller`` accepted an arbitrary ``validity_gates``
    iterable, so an empty tuple was legal and immediately permitted
    scientific classification.  "T5-T8 only after all validity gates" then
    meant only "after whatever the caller happened to pass".  The order and
    membership are now frozen in :data:`VALIDITY_GATE_ORDER` and owned by
    this module; the controller takes data, never gates.

``routing was not total``
    ``run_validity_gates`` caught only ``ContractError``, so a missing
    mapping key, a ``ValueError`` from an inherited constructor, or an
    unrecognized ``terminal_class`` escaped as a bare exception -- the last
    case meaning the router did not even route every ``ContractError``.
    Routing is now total: every ordinary exception, including one raised
    while advancing the gate sequence or inside classification, maps to T4,
    and ``ContractError`` constrains its class at construction time.

Non-finite scientific scalars are rejected rather than compared.  ``NaN``
compares false against every threshold, so D0.4 would have silently
classified a NaN estimand as "no registered interaction" instead of failing.
"""

from __future__ import annotations

import math

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    registry_seal_gate,
    schema_registry_digest,
)
from experiments.candidates.orbit_owner_match.records import (
    CalibrationRecord,
    EstimandRecord,
    registration_completeness_gate,
)
from experiments.candidates.orbit_owner_match import block as block_module
from experiments.candidates.orbit_owner_match import controls as controls_module
from experiments.candidates.orbit_owner_match import (
    discriminator as discriminator_module,
)
from experiments.candidates.orbit_owner_match import numerics as numerics_module
from experiments.candidates.orbit_owner_match import sealing as sealing_module
from experiments.candidates.orbit_owner_match import trust as trust_module


TERMINALS = (
    "PROVENANCE_CONTENT_CONFOUNDED_PARK",                        # T1
    "THIRTY_TWO_CELL_IDENTITY_CROSSOVER_REQUIRED",               # T2
    "AMBIENT_CHANNEL_UNCLOSEABLE_PARK",                          # T3
    "INVALID_CLOSURE_OR_GATE_FAILURE",                           # T4
    "NO_REGISTERED_INTERACTION",                                 # T5
    "LOGIT_INTERACTION_WITHOUT_REGISTERED_KERNEL_SURVIVAL",      # T6
    "KERNEL_INTERACTION_WITHOUT_REGISTERED_LOGIT_INTERACTION",   # T7
    "PASS_PREDICATE_INTERACTION_REACHES_FIRST_ACTION_KERNEL",    # T8
)

_TERMINAL_BY_CLASS = {"T1": TERMINALS[0], "T2": TERMINALS[1],
                      "T3": TERMINALS[2], "T4": TERMINALS[3]}

UNCLASSIFIED_TERMINAL = TERMINALS[3]


# ---------------------------------------------------------------------------
# The frozen gate order
# ---------------------------------------------------------------------------

# Static gates need no runtime data and run at freeze time.  Block gates need
# the constructed census.  Estimand gates need evaluated results.  The ORDER
# within and across these phases is frozen here and is not a caller choice.

STATIC_GATE_ORDER = (
    "interpreter",
    "dependency",
    "runtime_seal",
    "inherited_source",
    "registry_uniqueness",
    "calibration_fixture",
    "registration_completeness",
    "registry_seal",
    "ambient_hooks",
    "class_behavior",
    "imported_modules",
    "opaque_bindings",
    "forbidden_handles",
    "actor_path_audit",
    "actor_read_set",
    "construction_sites",
    "t2_actor_surface",
    "coefficient_oracle",
    "null_orientation",
    "logit_control",
    "kernel_control",
    "mutant_dispatch",
    "mutant_response",
    "tolerances",
    "recovery_envelope",
    "curvature_reference_stability",
    "frozen_curvature_literal",
    "curvature_margin",
    "curvature_mutant_response",
    "platform_admission",
)

BLOCK_GATE_ORDER = (
    "block_key_census",
    "exact_key_domain",
    "census_key_authenticity",
    "cross_m_closure",
    "cross_q_closure",
    "clone_independence",
    "public_write_invariance",
    "lineage_rebuild",
)

ESTIMAND_GATE_ORDER = (
    "calibration_disjointness",
    "calibration_authenticity",
    "evaluation_census",
    "estimand_authenticity",
    "finite_estimands",
    "finite_thresholds",
)

VALIDITY_GATE_ORDER = STATIC_GATE_ORDER + BLOCK_GATE_ORDER + ESTIMAND_GATE_ORDER


def _static_gates() -> tuple:
    return (
        ("interpreter", sealing_module.interpreter_gate),
        ("dependency", sealing_module.dependency_gate),
        ("runtime_seal", runtime_seal_gate),
        ("inherited_source", trust_module.inherited_source_gate),
        ("registry_uniqueness", trust_module.registry_uniqueness_gate),
        ("calibration_fixture",
         discriminator_module.calibration_fixture_gate),
        ("registration_completeness", registration_completeness_gate),
        ("registry_seal", registry_seal_gate),
        ("ambient_hooks", sealing_module.ambient_hook_gate),
        ("class_behavior", sealing_module.class_behavior_gate),
        ("imported_modules", sealing_module.imported_module_gate),
        ("opaque_bindings", sealing_module.opaque_binding_gate),
        ("forbidden_handles", sealing_module.forbidden_handle_gate),
        ("actor_path_audit", sealing_module.actor_path_audit_gate),
        ("actor_read_set", sealing_module.actor_read_set_gate),
        ("construction_sites", sealing_module.construction_site_gate),
        ("t2_actor_surface", sealing_module.t2_gate),
        ("coefficient_oracle", controls_module.coefficient_oracle_gate),
        ("null_orientation", controls_module.null_orientation_gate),
        ("logit_control", controls_module.logit_control_gates),
        ("kernel_control", controls_module.kernel_control_gates),
        ("mutant_dispatch", controls_module.mutant_dispatch_gate),
        ("mutant_response", controls_module.mutant_response_gate),
        ("tolerances", controls_module.tolerance_gate),
        ("recovery_envelope", numerics_module.recovery_gate),
        ("curvature_reference_stability",
         numerics_module.curvature_reference_stability_gate),
        ("frozen_curvature_literal", _frozen_curvature_literal_gate),
        ("curvature_margin", numerics_module.curvature_gate),
        ("curvature_mutant_response",
         numerics_module.curvature_mutant_response_gate),
        ("platform_admission", numerics_module.platform_admission_gate),
    )


def _frozen_curvature_literal_gate() -> None:
    numerics_module.frozen_curvature_literal_gate(
        controls_module.CURVATURE_REFERENCE_FIRST_COMPONENT.text)


def runtime_seal_gate() -> None:
    """Live digests equal the EXTERNALLY frozen expected digests.

    This is the gate D0.5 did not have (round-7 correction D05-C01).  D0.5
    computed ``fingerprint_set_digest()``, ``global_binding_digest()`` and the
    rest, reported them in the freeze evidence, and placed the freshly
    computed value into a freshly computed envelope.  Nothing ever compared a
    live digest with a frozen one, so the package INVENTORIED its runtime
    trust surface rather than sealing it: rebinding an audited global from one
    supported object to another changed the computed digest and failed no
    gate.

    The expected values live in :mod:`baseline`, which is outside the sealed
    set and is authenticated by its git blob id -- the same external anchor
    the reviewer used to authenticate the rest of the package.  Comparing a
    digest against a literal stored inside the digested set would be
    self-consistency again, which is the defect, not the fix.

    THE STRENGTH OF THIS SEAL, STATED HONESTLY AND KNOWN TO BE INCOMPLETE.
    It detects accidental drift and DIRECT rebinding of an audited global
    (verified: rebinding is caught at both the pre-phase and post-phase
    check).  It does NOT withstand an adversary running inside this process,
    and two concrete defeats are known and unfixed:

    1. MODULE SUBSTITUTION.  ``sealing.accepted_roots`` resolves roots
       through ``sys.modules`` while :mod:`sealing` holds its own
       import-time module bindings.  Where those disagree the audit measures
       a different object from the one that executes.  Installing a pristine
       :mod:`gates` into ``sys.modules`` and tampering the live module
       yields terminal T8 with an all-zero ledger and BOTH seals passing.
       ``LIVE_PROCESS_ATTRS`` pins only one live attribute of this module.
       ``sealing.owned_modules()`` is named in the source as the
       compensating control and has no call site.

    2. SAME-TYPED SUBSTITUTION of a ``PROCESS_STATE_GLOBALS`` slot -- see
       :class:`discriminator.ExecutionLedger`.

    Both are recorded rather than repaired: closing them requires sealing a
    Python process against an in-process adversary, which is not achievable,
    and the freeze is being stated at the strength it has rather than
    iterated toward a strength it cannot reach.  Anything relying on this
    package must treat the interpreter as trusted and the external clean
    process, not the seal, as the load-bearing evidence.
    """
    from experiments.candidates.orbit_owner_match import baseline
    observed = (
        ("fingerprint_set", sealing_module.fingerprint_set_digest()),
        ("global_binding", sealing_module.global_binding_digest()),
        ("class_behavior", sealing_module.class_behavior_digest()),
        ("schema_registry", schema_registry_digest()),
        ("gate_order", gate_order_digest()),
        ("package_source", precommit_source_digest()),
    )
    for name, value in observed:
        expected = baseline.EXPECTED_DIGESTS.get(name)
        if expected is None:
            raise ContractError("no frozen expectation for %r" % (name,), "T3")
        if value != expected:
            raise ContractError(
                "runtime seal broken: %s digest is %s, frozen expectation is %s"
                % (name, value, expected), "T3")


def precommit_source_digest() -> str:
    from experiments.candidates.orbit_owner_match import precommit
    return precommit.package_source_digest()


def gate_order_digest() -> str:
    """Digest over the frozen gate names, so the ORDER is sealed too."""
    from experiments.candidates.orbit_owner_match.canon import (
        _enc_str, sha256_hex,
    )
    return sha256_hex(b"".join(_enc_str(name) for name in VALIDITY_GATE_ORDER))


def _block_gates(snapshot, block) -> tuple:
    cells = block_module.block_cells(block)
    return (
        ("block_key_census", lambda: _block_key_census_gate(cells)),
        ("exact_key_domain",
         lambda: block_module.exact_key_domain_gate(cells)),
        ("census_key_authenticity",
         lambda: block_module.census_key_authenticity_gate(cells)),
        ("cross_m_closure", lambda: block_module.cross_m_closure_gate(cells)),
        ("cross_q_closure", lambda: block_module.cross_q_closure_gate(cells)),
        ("clone_independence",
         lambda: block_module.clone_independence_gate(block)),
        ("public_write_invariance",
         lambda: block_module.public_write_invariance_gate(cells)),
        ("lineage_rebuild",
         lambda: block_module.lineage_rebuild_gate(snapshot, cells)),
    )


def _block_key_census_gate(cells) -> None:
    if type(cells) is not dict:
        raise ContractError("exact dict census required")
    if frozenset(cells) != controls_module.EXPECTED_KEYS:
        raise ContractError("block key census mismatch")


def _estimand_gates(estimand, calibration, evaluation, cells) -> tuple:
    return (
        ("calibration_disjointness",
         lambda: discriminator_module.calibration_disjointness_gate(
             calibration, trust_module.SOURCE_SNAPSHOT_DIGEST)),
        ("calibration_authenticity",
         lambda: discriminator_module.calibration_authenticity_gate(
             calibration)),
        ("evaluation_census",
         lambda: discriminator_module.evaluation_census_gate(
             evaluation, cells)),
        ("estimand_authenticity",
         lambda: discriminator_module.estimand_authenticity_gate(
             estimand, evaluation)),
        ("finite_estimands", lambda: _finite_estimand_gate(estimand)),
        ("finite_thresholds", lambda: _finite_threshold_gate(calibration)),
    )


def _require_finite(value, label: str) -> None:
    """Exact binary64 admission.

    ``type(value) is not float`` rejects ``bool`` and ``int``; the finiteness
    test rejects NaN and the infinities, which would otherwise compare false
    against every threshold and be classified as a null result.
    """
    if type(value) is not float:
        raise ContractError("exact float required for %s" % label)
    if not math.isfinite(value):
        raise ContractError("nonfinite %s rejected" % label)


def _finite_estimand_gate(estimand) -> None:
    if type(estimand) is not EstimandRecord:
        raise ContractError("exact EstimandRecord required")
    _require_finite(estimand.theta_logit, "theta_logit")
    _require_finite(estimand.theta_kernel, "theta_kernel")
    if estimand.theta_logit < 0.0 or estimand.theta_kernel < 0.0:
        raise ContractError("negative norm is impossible; estimand corrupt")
    for name in ("d_logit", "d_kernel"):
        vector = getattr(estimand, name)
        if type(vector) is not tuple or len(vector) != 2:
            raise ContractError("exact two-component %s required" % name)
        for component in vector:
            _require_finite(component, name)


def _finite_threshold_gate(calibration) -> None:
    if type(calibration) is not CalibrationRecord:
        raise ContractError("exact CalibrationRecord required")
    for name in ("delta_logit", "delta_kernel", "tau_logit", "tau_kernel",
                 "u_logit", "u_kernel"):
        value = getattr(calibration, name)
        _require_finite(value, name)
        if value <= 0.0:
            raise ContractError("%s must be strictly positive" % name)
    if calibration.delta_logit != 4.0 * calibration.tau_logit:
        raise ContractError("delta_logit is not 4*tau_logit")
    if calibration.delta_kernel != 4.0 * calibration.tau_kernel:
        raise ContractError("delta_kernel is not 4*tau_kernel")


# ---------------------------------------------------------------------------
# Total routing
# ---------------------------------------------------------------------------


def run_gate_sequence(named_gates: tuple, expected_order: tuple) -> str:
    """Run gates in the frozen order; return "" if all pass, else a terminal.

    Routing is total by construction: ``ContractError`` maps through its
    constrained class, and every other ordinary exception -- including one
    raised while building or advancing the sequence -- becomes T4.  Nothing
    reaches scientific classification by escaping this function.
    """
    try:
        names = tuple(name for name, _ in named_gates)
    except Exception:
        return UNCLASSIFIED_TERMINAL
    if names != expected_order:
        return UNCLASSIFIED_TERMINAL
    for _, gate in named_gates:
        try:
            gate()
        except ContractError as failure:
            return _TERMINAL_BY_CLASS.get(failure.terminal_class,
                                          UNCLASSIFIED_TERMINAL)
        except Exception:
            return UNCLASSIFIED_TERMINAL
    return ""


def run_static_gates() -> str:
    """Freeze-time evidence: every data-independent gate passes."""
    try:
        gates = _static_gates()
    except Exception:
        return UNCLASSIFIED_TERMINAL
    return run_gate_sequence(gates, STATIC_GATE_ORDER)


def classify_science(estimand, calibration) -> str:
    """Strict-``>`` classification against calibration-derived thresholds.

    Thresholds come from the calibration record, never from a caller
    argument: round 6 observed that a caller could otherwise supply arbitrary
    ``theta_*``/``delta_*`` values and obtain any terminal it liked.
    """
    _finite_estimand_gate(estimand)
    _finite_threshold_gate(calibration)
    logit_pass = estimand.theta_logit > calibration.delta_logit
    kernel_pass = estimand.theta_kernel > calibration.delta_kernel
    if logit_pass and kernel_pass:
        return TERMINALS[7]
    if logit_pass:
        return TERMINALS[5]
    if kernel_pass:
        return TERMINALS[6]
    return TERMINALS[4]


def terminal_controller(snapshot) -> str:
    """The single entry point from a snapshot to a terminal.

    It takes ONLY the snapshot.  It builds the census itself and derives the
    calibration and the estimand itself.  Two earlier forms were broken:

    *   D0.4 took the estimand and the calibration as arguments, so a
        fabricated pair -- finite, positive, ``delta == 4*tau`` -- returned T8
        with the discriminator never run.
    *   D0.5 fixed that but still took ``cells``: a caller-owned mutable dict
        that crossed from the validation phase into the evaluation phase, so
        everything the block gates established was established about a state
        the caller could replace afterwards.

    The census is now built here, carried as an immutable :class:`Block`, and
    its canonical image is re-verified immediately before evaluation.  What
    that does NOT close is a concurrent mutator inside this process, which no
    in-process check can close; the contract claims the caller boundary, not
    thread safety.

    This EXECUTES the discriminator, and is meant to: it is the run-time
    entry point, not a freeze-time one.  At freeze time only
    :func:`run_static_gates` runs, and the execution ledger stays zero.
    """
    try:
        verdict = run_gate_sequence(_static_gates(), STATIC_GATE_ORDER)
        if verdict:
            return verdict
        block = block_module.build_block(snapshot)
        image = block_module.block_image(block)
        verdict = run_gate_sequence(_block_gates(snapshot, block),
                                    BLOCK_GATE_ORDER)
        if verdict:
            return verdict
        if block_module.block_image(block) != image:
            raise ContractError("census changed during validation", "T1")
        calibration = discriminator_module.calibrate()
        evaluated_cells = block_module.block_cells(block)
        evaluation = discriminator_module.evaluate_block(evaluated_cells)
        estimand = discriminator_module.estimands(evaluation)
        verdict = run_gate_sequence(
            _estimand_gates(estimand, calibration, evaluation,
                            evaluated_cells),
            ESTIMAND_GATE_ORDER)
        if verdict:
            return verdict
        # Re-seal after the audited phase, so a rebinding performed between
        # the static gates and the evaluation is caught before a scientific
        # terminal is issued rather than after.
        runtime_seal_gate()
        return classify_science(estimand, calibration)
    except Exception:
        return UNCLASSIFIED_TERMINAL


def gate_order_gate() -> None:
    """The declared order matches what the builders actually produce."""
    if tuple(name for name, _ in _static_gates()) != STATIC_GATE_ORDER:
        raise ContractError("static gate order drift")
    if len(frozenset(VALIDITY_GATE_ORDER)) != len(VALIDITY_GATE_ORDER):
        raise ContractError("duplicate gate name")
    if frozenset(_TERMINAL_BY_CLASS) != ContractError.VALID_CLASSES:
        raise ContractError("terminal class map does not cover every class")
    if len(frozenset(TERMINALS)) != 8:
        raise ContractError("terminal set is not eight distinct outcomes")
