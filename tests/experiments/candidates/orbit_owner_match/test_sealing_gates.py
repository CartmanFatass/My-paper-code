"""Fingerprints, call-graph closure, live-object sealing, terminal routing."""

import math
import sys

import pytest

from experiments.candidates.orbit_shadow_read import eight_cell_audit

from experiments.candidates.orbit_owner_match import canon
from experiments.candidates.orbit_owner_match import discriminator
from experiments.candidates.orbit_owner_match import gates
from experiments.candidates.orbit_owner_match import precommit
from experiments.candidates.orbit_owner_match import records
from experiments.candidates.orbit_owner_match import sealing


def test_fingerprint_distinguishes_signed_zero_constants():
    """Rejects: the round-6 fingerprint that erased the sign of zero.

    Two functions differing only in ``(0.0, 0.0)`` versus ``(-0.0, -0.0)``
    must fingerprint differently, or the freeze cannot pin the very
    orientation the null argument depends on.
    """
    namespace = {}
    exec("def positive():\n    return (0.0, 0.0)\n", namespace)
    exec("def negative():\n    return (-0.0, -0.0)\n", namespace)
    positive = sealing.fingerprint_function(namespace["positive"])
    negative = sealing.fingerprint_function(namespace["negative"])
    assert positive != negative


def test_fingerprint_covers_stack_size():
    """Rejects: a fingerprint blind to operationally relevant metadata."""
    namespace = {}
    exec("def shallow():\n    return 1\n", namespace)
    exec("def deep():\n    return (1, (2, (3, (4, 5))))\n", namespace)
    assert (sealing.fingerprint_function(namespace["shallow"])
            != sealing.fingerprint_function(namespace["deep"]))


def test_call_graph_reaches_the_inherited_callees():
    """Rejects: fingerprinting entry points but not what they call.

    Round 6 found the inherited writer, verifier and adapter outside the
    advertised freeze entirely.
    """
    graph = sealing.call_graph(sealing.accepted_roots())
    reached = set(graph)
    for name in ("write_sibling", "verify_sibling", "q_adapter", "_softmax",
                 "actor", "restore_clone", "_digest"):
        qualname = eight_cell_audit.__name__ + "." + name
        assert qualname in reached, name


def test_actor_path_satisfies_its_allowlists():
    sealing.actor_path_audit_gate()


def test_construction_sites_are_closed():
    sealing.construction_site_gate()


def test_construction_site_gate_catches_a_new_construction_site():
    """Rejects: a closure proof that only inspects the permitted function."""

    def rogue():
        return records.VerifiedOwnerPredicate(True)

    original = sealing.accepted_roots
    sealing.accepted_roots = lambda: original() + (rogue,)
    try:
        with pytest.raises(canon.ContractError):
            sealing.construction_site_gate()
    finally:
        sealing.accepted_roots = original
    sealing.construction_site_gate()


def test_forbidden_handle_gate_blocks_name_free_construction():
    """Rejects: a name scan carrying a claim it cannot bear.

    ``registered_class(schema_id)(...)``, ``getattr(records, ...)`` and
    ``type(existing)(...)`` all construct a guarded record without naming it,
    so the construction-site scan cannot see them.
    """
    sealing.forbidden_handle_gate()

    def via_registry():
        return canon.registered_class(
            "VerifiedOwnerPredicate@orbit-owner-match-d2")(True)

    def via_type(existing):
        return type(existing)(True)

    original = sealing.provenance_roots
    for rogue in (via_registry, via_type):
        sealing.provenance_roots = lambda r=rogue: original() + (r,)
        try:
            with pytest.raises(canon.ContractError):
                sealing.forbidden_handle_gate()
        finally:
            sealing.provenance_roots = original
    sealing.forbidden_handle_gate()


def test_interpreter_is_pinned():
    """Rejects: digests that silently mean different things per interpreter."""
    sealing.interpreter_gate()
    assert sealing.INTERPRETER_CONTRACT[0] == "cpython"
    assert (sys.implementation.name, ) + sys.version_info[:3] == (
        sealing.INTERPRETER_CONTRACT)
    assert len(sealing.INTERPRETER_CONTRACT) == 4, (
        "the patch level must be pinned; 3.11.x is not 3.11.9")


def test_type_tests_against_guarded_classes_stay_legal():
    """Rejects: an over-strict gate that forbids reading a guarded type."""
    code = compile("type(x) is not records.VerifiedOwnerPredicate",
                   "<t>", "eval")
    assert not sealing._references_for_construction(
        code, "VerifiedOwnerPredicate")


def test_every_reachable_global_is_content_pinned():
    """Rejects: name-only allowlisting that ignores object identity."""
    sealing.opaque_binding_gate()
    bindings = sealing.global_binding_records()
    assert bindings
    assert all(record.binding_kind != "opaque" for record in bindings)


def test_class_behavior_gate_catches_a_data_descriptor():
    """Rejects: trusting object.__getattribute__ to close class behavior.

    Bypassing an instance-level override still runs descriptor protocol, so a
    property installed on the exact registered class can change what a field
    read returns while ``type(value) is cls`` remains true.
    """
    sealing.class_behavior_gate()
    victim = records.DecimalLiteral
    original = victim.__dict__.get("text")
    setattr(victim, "text", property(lambda self: "hijacked"))
    try:
        with pytest.raises(canon.ContractError):
            sealing.class_behavior_gate()
    finally:
        if original is None:
            delattr(victim, "text")
        else:  # pragma: no cover - defensive
            setattr(victim, "text", original)
    sealing.class_behavior_gate()


def test_ambient_hook_gate_refuses_a_trace_hook():
    """Rejects: closure claims made while a tracer can rewrite locals."""
    sealing.ambient_hook_gate()
    sys.settrace(lambda *args: None)
    try:
        with pytest.raises(canon.ContractError):
            sealing.ambient_hook_gate()
    finally:
        sys.settrace(None)
    sealing.ambient_hook_gate()


def test_contract_error_constrains_its_terminal_class():
    """Rejects: a router that KeyErrors on an unrecognized class."""
    with pytest.raises(ValueError):
        canon.ContractError("x", "T9")
    assert set(gates._TERMINAL_BY_CLASS) == canon.ContractError.VALID_CLASSES


def test_routing_is_total_for_ordinary_exceptions():
    """Rejects: catching only ContractError.

    A missing mapping key, a ValueError from an inherited constructor, or a
    TypeError from a malformed boundary value must all terminalize.
    """
    def raises_key_error():
        raise KeyError("missing pair key")

    def raises_value_error():
        raise ValueError("inherited constructor rejected input")

    for gate in (raises_key_error, raises_value_error):
        verdict = gates.run_gate_sequence((("only", gate),), ("only",))
        assert verdict == gates.UNCLASSIFIED_TERMINAL


def test_gate_sequence_rejects_a_reordered_or_short_suite():
    """Rejects: a caller-selectable gate set.

    An empty tuple used to be legal and permitted immediate classification.
    """
    assert gates.run_gate_sequence((), ("expected",)) == (
        gates.UNCLASSIFIED_TERMINAL)
    reordered = (("b", lambda: None), ("a", lambda: None))
    assert gates.run_gate_sequence(reordered, ("a", "b")) == (
        gates.UNCLASSIFIED_TERMINAL)


def test_static_gate_suite_passes_in_the_frozen_order():
    gates.gate_order_gate()
    assert gates.run_static_gates() == ""
    assert (gates.VALIDITY_GATE_ORDER[:len(gates.STATIC_GATE_ORDER)]
            == gates.STATIC_GATE_ORDER)


def test_nonfinite_estimand_is_rejected_not_classified():
    """Rejects: comparing NaN against a threshold and calling it a null.

    Every comparison with NaN is false, so D0.4 would have returned
    "no registered interaction" for a corrupt estimand.
    """
    estimand = records.EstimandRecord((float("nan"), 0.0), (0.0, 0.0),
                                      float("nan"), 0.0)
    with pytest.raises(canon.ContractError):
        gates._finite_estimand_gate(estimand)


def _fabricated_calibration(delta=1e-300):
    diameter = records.DiameterRecord(
        tuple(records.ReplicaRecord("R%d" % i, (0.5, -0.5), (0.6, 0.4),
                                    "calibration-clone-A", i % 2)
              for i in range(4)), 0.0, 0.0)
    tau = delta / 4.0
    return records.CalibrationRecord(
        "de" * 32, diameter, tau, tau, tau, tau, tau, tau,
        4.0 * tau, 4.0 * tau)


def test_terminal_controller_does_not_accept_an_estimand_or_calibration():
    """Rejects: a controller whose terminal is a caller argument.

    Moving the thresholds one struct deeper into a CalibrationRecord did not
    take them out of the caller's hands -- the record was still an argument,
    and a fabricated pair yielded T8 with the discriminator never run.  The
    controller must take only the block and derive the rest.
    """
    import inspect

    parameters = list(
        inspect.signature(gates.terminal_controller).parameters)
    assert parameters == ["snapshot"], parameters


def test_calibration_authenticity_rejects_a_fabricated_ladder():
    """Rejects: threshold checks that only test finiteness and delta==4*tau.

    Every literal ladder satisfies those.  The ladder must be recomputable
    from the replicas the record itself carries.
    """
    forged = _fabricated_calibration()
    gates._finite_threshold_gate(forged)  # passes the weak checks ...
    with pytest.raises(canon.ContractError):  # ... and fails the real one
        discriminator.calibration_authenticity_gate(forged)


def test_classification_still_separates_pass_from_null():
    """The classifier itself is correct, given an authentic calibration."""
    calibration = _fabricated_calibration(delta=1e-300)
    strong = records.EstimandRecord((4.0, -4.0), (1.8, -1.8),
                                    4.0 * math.sqrt(2.0), 1.8)
    assert gates.classify_science(strong, calibration) == gates.TERMINALS[7]
    null = records.EstimandRecord((0.0, 0.0), (0.0, 0.0), 0.0, 0.0)
    assert gates.classify_science(null, calibration) == gates.TERMINALS[4]


def test_delta_must_be_four_tau():
    diameter = records.DiameterRecord(
        tuple(records.ReplicaRecord("R%d" % i, (0.5, -0.5), (0.6, 0.4),
                                    "calibration-clone-A", i % 2)
              for i in range(4)), 0.0, 0.0)
    broken = records.CalibrationRecord(
        "0" * 64, diameter, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0, 4.0)
    with pytest.raises(canon.ContractError):
        gates._finite_threshold_gate(broken)


def _clean_process(source):
    """Run a snippet in a fresh interpreter and return its stdout.

    Freeze evidence has to come from a process that never ran the
    discriminator; asserting it inside the test session would only prove
    something about this session's history.
    """
    import subprocess

    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True, text=True,
        cwd=str(precommit.PACKAGE_DIR.parents[2]))
    assert result.returncode == 0, result.stderr[-2000:]
    return result.stdout.strip()


def test_freeze_evidence_comes_from_a_process_that_never_ran_anything():
    """The freeze claim, in checkable form, from a clean interpreter."""
    output = _clean_process(
        "from experiments.candidates.orbit_owner_match import precommit\n"
        "e = precommit.freeze_evidence()\n"
        "print(e['execution_ledger'], e['schema_count'],"
        " e['fingerprint_count'], len(e['precommit_digest']))\n")
    assert output.startswith(
        "{'actor_calls': 0, 'block_evaluations': 0, 'calibration_runs': 0}")
    assert output.endswith(" 64")


def test_freeze_evidence_is_idempotent():
    """Rejects: evidence whose fields drift between two consecutive dumps."""
    output = _clean_process(
        "from experiments.candidates.orbit_owner_match import precommit\n"
        "a = precommit.freeze_evidence()\n"
        "b = precommit.freeze_evidence()\n"
        "print(a == b)\n")
    assert output == "True"


def test_schema_count_matches_the_table_not_a_hand_count():
    evidence_count = len(records._SCHEMA_TABLE)
    assert evidence_count == len(canon.schema_ids())


def test_fingerprint_set_covers_the_whole_accepted_graph():
    """Rejects: comparing a function's output to itself."""
    fingerprints = sealing.fingerprint_set()
    covered = {record.qualname for record in fingerprints}
    assert covered == set(sealing.call_graph(sealing.accepted_roots()))
    assert any(name.startswith(eight_cell_audit.__name__)
               for name in covered)
    assert len({record.fingerprint_hex for record in fingerprints}) == len(
        fingerprints)


def test_package_manifest_has_not_drifted():
    precommit.package_manifest_gate()


def test_execution_ledger_notices_an_actor_call_in_a_clean_process():
    """Rejects: a ledger that does not move when the actor runs."""
    assert not hasattr(discriminator, "reset_execution_ledger")
    output = _clean_process(
        "from experiments.candidates.orbit_owner_match import discriminator\n"
        "from experiments.candidates.orbit_owner_match import canon\n"
        "from experiments.candidates.orbit_shadow_read.eight_cell_audit "
        "import restore_clone, serialize_snapshot\n"
        "discriminator.execution_ledger_gate()\n"
        "src = serialize_snapshot(discriminator.CALIBRATION_SNAPSHOT)\n"
        "ai = discriminator._calibration_actor_input("
        "restore_clone(src, 'calibration-clone-A'))\n"
        "discriminator.owner_predicate_actor(ai)\n"
        "try:\n"
        "    discriminator.execution_ledger_gate(); print('LEAKED')\n"
        "except canon.ContractError:\n"
        "    print('CAUGHT')\n")
    assert output == "CAUGHT"


def test_execution_ledger_refuses_the_ordinary_reset_spellings():
    """Rejects: the one-line reset that defeated D0.5's ledger.

    D0.5 exported a plain dict and claimed monotonicity because it had
    removed the reset HELPER.  ``EXECUTION_LEDGER["actor_calls"] = 0``
    restored an all-zero reading after a full run and the gate passed.
    """
    ledger = discriminator.EXECUTION_LEDGER
    assert not hasattr(ledger, "__setitem__")
    with pytest.raises(canon.ContractError):
        ledger.actor_calls = 0
    with pytest.raises(canon.ContractError):
        del ledger.actor_calls
    with pytest.raises(canon.ContractError):
        ledger.increment("not_a_counter")
    assert not hasattr(ledger, "__dict__"), (
        "__slots__ must be real; an instance dict would shadow the counters")


def test_execution_ledger_claim_is_not_overstated():
    """The contract must not claim tamper-proofness it cannot deliver.

    ``object.__setattr__`` still reaches the counters.  That is a fact about
    CPython, not a defect to be papered over, and the docstring says so --
    this test fails if someone re-asserts the stronger claim.
    """
    source = discriminator.execution_ledger_gate.__doc__
    assert "object.__setattr__" in source
    assert "orbit_owner_freeze_evidence" in source
    probe = discriminator.ExecutionLedger()
    object.__setattr__(probe, "actor_calls", 7)
    assert probe.snapshot()["actor_calls"] == 7
