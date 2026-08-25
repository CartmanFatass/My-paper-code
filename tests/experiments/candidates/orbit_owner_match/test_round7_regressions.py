"""One test per attack round 7 demonstrated against D0.5 (D05-V05).

Each of these passed on D0.5.  They are written to fail loudly if the
corresponding repair is ever backed out, and each docstring records what the
old behavior actually was, so a future reader can tell a real regression from
a cosmetic refactor.
"""

from __future__ import annotations

import pytest

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    build_snapshot,
    restore_clone,
    serialize_snapshot,
)

from experiments.candidates.orbit_owner_match import baseline
from experiments.candidates.orbit_owner_match import block
from experiments.candidates.orbit_owner_match import canon
from experiments.candidates.orbit_owner_match import discriminator
from experiments.candidates.orbit_owner_match import gates
from experiments.candidates.orbit_owner_match import records
from experiments.candidates.orbit_owner_match import sealing
from experiments.candidates.orbit_owner_match import trust


@pytest.fixture(scope="module")
def snapshot():
    return build_snapshot()


@pytest.fixture(scope="module")
def blk(snapshot):
    return block.build_block(snapshot)


# ---------------------------------------------------------------------------
# D05-C01 -- the runtime seal
# ---------------------------------------------------------------------------


def test_rebinding_a_module_attribute_breaks_the_seal():
    """Rejects: steering the terminal by rebinding what the controller calls.

    D0.5's controller derived the calibration and the estimand rather than
    accepting them, which closed the D0.4 attack.  But ``terminal_controller``
    resolves ``discriminator_module.calibrate`` at call time, while the audit
    fingerprinted the function objects held in its own root tuple.  Rebinding
    the live module attribute to a function returning mutually consistent
    fabricated records therefore steered the terminal with no actor call and
    a zero ledger, and no gate computed anything that changed.
    """
    gates.runtime_seal_gate()  # clean

    def fake_calibrate():
        raise AssertionError("must never be called")

    original = discriminator.calibrate
    discriminator.calibrate = fake_calibrate
    try:
        with pytest.raises(canon.ContractError):
            gates.runtime_seal_gate()
    finally:
        discriminator.calibrate = original
    gates.runtime_seal_gate()  # and clean again once restored


def test_seal_expectations_live_outside_the_sealed_set():
    """Rejects: comparing a digest with a literal stored inside that digest.

    Self-consistency was the D0.5 defect.  The expectation has to be anchored
    somewhere the digest cannot reach, or writing the value in changes it.
    """
    assert "baseline" not in "".join(sealing.OWNED_MODULE_NAMES).replace(
        "experiments.candidates.orbit_owner_match.baseline", "")
    assert (sealing._PACKAGE + "baseline") not in sealing.OWNED_MODULE_NAMES
    from experiments.candidates.orbit_owner_match import precommit
    assert "baseline.py" not in [n for n, _ in precommit.package_source_records()]
    assert "baseline.py" not in [n for n, _ in baseline.EXPECTED_BLOB_MANIFEST]
    # ... but it IS in the manifest gate's file list, so it cannot change
    # unnoticed.
    assert "baseline.py" in precommit.PACKAGE_MODULES
    assert "baseline.py" in [n for n, _ in precommit.package_blob_records()]


def test_seal_digest_is_idempotent():
    """Rejects: a seal that moves when you check it.

    D0.5 kept a per-process counter of how many times the numeric self-audit
    had run, reachable as a global binding.  Any digest covering it changed on
    every audit, so it could never equal a frozen expectation.
    """
    before = sealing.global_binding_digest()
    gates.run_static_gates()
    assert sealing.global_binding_digest() == before


# ---------------------------------------------------------------------------
# D05-C02 -- call-graph coverage
# ---------------------------------------------------------------------------


def test_fingerprint_graph_covers_the_terminal_and_the_gates():
    """Rejects: a graph that stops at the module object.

    D0.5 followed only bare ``LOAD_GLOBAL`` function references, so every
    ``discriminator_module.calibrate``-style call -- which is how the terminal
    path calls almost everything -- was invisible, and gates, numerics,
    sealing and precommit were outside ``OWNED_MODULES`` entirely.
    """
    covered = {record.qualname for record in sealing.fingerprint_set()}
    for required in (
            "experiments.candidates.orbit_owner_match.gates."
            "terminal_controller",
            "experiments.candidates.orbit_owner_match.gates.classify_science",
            "experiments.candidates.orbit_owner_match.numerics.recovery_gate",
            "experiments.candidates.orbit_owner_match.sealing.call_graph",
            "experiments.candidates.orbit_owner_match.precommit."
            "build_precommit_envelope",
            "experiments.candidates.orbit_owner_match.discriminator."
            "calibration_authenticity_gate"):
        assert required in covered, required


def test_module_qualified_calls_are_resolved():
    """The resolver follows ``LOAD_GLOBAL m; LOAD_ATTR f``, not just bare f."""
    reached = {fn.__qualname__
               for fn in sealing._referenced_functions(gates.terminal_controller)}
    assert "build_block" in reached
    assert "calibrate" in reached
    assert "evaluate_block" in reached


# ---------------------------------------------------------------------------
# D05-C03 / C08 -- census ownership and key types
# ---------------------------------------------------------------------------


def test_terminal_controller_owns_the_census():
    """Rejects: a caller-owned mutable census crossing into evaluation."""
    import inspect
    assert list(inspect.signature(gates.terminal_controller).parameters) == [
        "snapshot"]


def test_post_gate_mutation_changes_the_census_image(blk):
    """The image is what the controller re-checks before evaluating.

    ``frozen=True`` stops assignment syntax; it does not stop
    ``object.__setattr__``.  The defense is that the controller compares the
    canonical image before and after validation, so a mutation between the
    two is visible even though the dataclass could not prevent it.
    """
    image = block.block_image(blk)
    victim = blk.entries[0].cell
    original = victim.key
    object.__setattr__(victim, "key", records.AnalysisKey(1, 1, 1, 1))
    try:
        assert block.block_image(blk) != image
    finally:
        object.__setattr__(victim, "key", original)
    assert block.block_image(blk) == image


def test_equality_bearing_census_key_is_rejected(blk):
    """Rejects: an object that merely COMPARES equal to a label tuple."""

    class Chameleon(tuple):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash((0, 1, 1, 1))

    cells = block.block_cells(blk)
    forged = dict(cells)
    forged[Chameleon((0, 1, 1, 1))] = forged.pop((0, 1, 1, 1))
    with pytest.raises(canon.ContractError):
        block.exact_key_domain_gate(forged)


# ---------------------------------------------------------------------------
# D05-C05 -- the cold/warm protocol
# ---------------------------------------------------------------------------


def test_cold_and_warm_share_one_clone_object():
    """Rejects: four labels over four freshly restored clones.

    D0.5 called ``restore_clone`` on every replica, so 'A-warm' was as cold
    as 'A-cold' and the diameter measured four repetitions of one condition
    instead of the accepted cold/warm structure.
    """
    diameter = discriminator.four_replica_diameter()
    replicas = diameter.replicas
    assert [r.replica_id for r in replicas] == list(
        discriminator.REPLICA_IDS)
    assert [r.prior_uses for r in replicas] == [0, 1, 0, 1]
    assert replicas[0].clone_label == replicas[1].clone_label
    assert replicas[2].clone_label == replicas[3].clone_label
    assert replicas[0].clone_label != replicas[2].clone_label


def test_calibration_authenticity_requires_the_protocol():
    """A ladder whose replicas do not carry the cold/warm structure fails."""
    calibration = discriminator.calibrate()
    discriminator.calibration_authenticity_gate(calibration)
    all_cold = records.CalibrationRecord(
        calibration.calibration_snapshot_digest,
        records.DiameterRecord(
            tuple(records.ReplicaRecord(r.replica_id, r.logits, r.kernel,
                                        r.clone_label, 0)
                  for r in calibration.diameter.replicas),
            calibration.diameter.eta_logit, calibration.diameter.eta_kernel),
        calibration.one_ulp_logit, calibration.one_ulp_kernel,
        calibration.u_logit, calibration.u_kernel,
        calibration.tau_logit, calibration.tau_kernel,
        calibration.delta_logit, calibration.delta_kernel)
    with pytest.raises(canon.ContractError):
        discriminator.calibration_authenticity_gate(all_cold)


# ---------------------------------------------------------------------------
# D05-C06 -- evaluation is of the validated census
# ---------------------------------------------------------------------------


def test_estimand_cannot_be_bound_to_a_foreign_evaluation(blk):
    """Rejects: an internally consistent (estimand, evaluation) pair that has
    nothing to do with the census the block gates validated."""
    cells = block.block_cells(blk)
    evaluation = discriminator.evaluate_block(cells)
    discriminator.evaluation_census_gate(evaluation, cells)

    foreign = dict(cells)
    foreign.pop(sorted(foreign)[0])
    with pytest.raises(canon.ContractError):
        discriminator.evaluation_census_gate(evaluation, foreign)

    stripped = {k: v for k, v in evaluation.items() if k != "census_digest"}
    with pytest.raises(canon.ContractError):
        discriminator.evaluation_census_gate(stripped, cells)


# ---------------------------------------------------------------------------
# D05-C07 -- the derived actor read set
# ---------------------------------------------------------------------------


def test_actor_read_set_is_equality_not_subset():
    """Rejects: an allowlist that only catches EXTRA reads.

    Round 4 rejected D0.2 because the actor did not read
    ``verified_owner_match`` -- a MISSING read, which a subset test cannot
    see.  D0.5's audit was exactly such a subset test.
    """
    assert sealing.actor_field_reads() == sealing.REGISTERED_ACTOR_READ_SET
    sealing.actor_read_set_gate()

    def m_blind(actor_input):
        if type(actor_input) is not records.ActorInput_D2:
            raise canon.ContractError("exact ActorInput_D2 required")
        b, role = (int(value) for value in actor_input.actor_tensor[-2:])
        logit = 0.5 if b == role else -0.5
        return logit, -logit

    original = discriminator.owner_predicate_actor
    discriminator.owner_predicate_actor = m_blind
    try:
        with pytest.raises(canon.ContractError):
            sealing.actor_read_set_gate()
    finally:
        discriminator.owner_predicate_actor = original
    sealing.actor_read_set_gate()


# ---------------------------------------------------------------------------
# D05-C10 -- the transcript binding
# ---------------------------------------------------------------------------


def test_transcript_records_the_binding_that_decided_owner_match():
    """Rejects: a lineage record naming a binding that was not consulted.

    D0.5 selected the binding correctly with ``binding_for_source`` and then
    always serialized ``EXPECTED_OWNER_BINDING`` into the transcript, so every
    calibration verification registered the discriminator's binding while
    deciding under the calibration one.
    """
    source = serialize_snapshot(discriminator.CALIBRATION_SNAPSHOT)
    clone = restore_clone(source, "calibration-clone-A")
    write = trust.build_write_d2_with_b(
        discriminator.CALIBRATION_SNAPSHOT, "W1", 0)
    result = trust.verify_write_d2(clone, write)

    calibration_binding = trust.binding_for_source(clone.source_bytes_digest)
    assert calibration_binding is not trust.EXPECTED_OWNER_BINDING

    expected = trust.compute_transcript(
        write.sidecar, True, result.owner_match, calibration_binding)
    assert result.transcript_digest == expected

    wrong = trust.compute_transcript(
        write.sidecar, True, result.owner_match, trust.EXPECTED_OWNER_BINDING)
    assert result.transcript_digest != wrong


# ---------------------------------------------------------------------------
# D05-C11 -- the environment contract
# ---------------------------------------------------------------------------


def test_environment_is_pinned_exactly():
    """Rejects: a contract that admits any 3.11.x or any mpmath."""
    assert len(sealing.INTERPRETER_CONTRACT) == 4
    assert sealing.INTERPRETER_CONTRACT == baseline.FROZEN_INTERPRETER
    assert sealing.MPMATH_CONTRACT == baseline.FROZEN_MPMATH
    sealing.interpreter_gate()
    sealing.dependency_gate()


def test_envelope_binds_what_the_freeze_claims():
    """Rejects: reporting a value beside the digest instead of inside it."""
    import dataclasses
    from experiments.candidates.orbit_owner_match import precommit
    fields = {f.name for f in dataclasses.fields(records.PrecommitEnvelope)}
    for required in ("global_binding_digest", "class_behavior_digest",
                     "gate_order_digest", "blob_manifest_digest",
                     "interpreter", "execution_ledger_digest"):
        assert required in fields, required
    envelope = precommit.build_precommit_envelope()
    assert envelope.gate_order_digest == gates.gate_order_digest()
    assert envelope.interpreter.startswith("cpython 3.11.9")


# ---------------------------------------------------------------------------
# D05-V01 -- the gate count the freeze document reports
# ---------------------------------------------------------------------------


def test_reported_gate_counts_match_the_source():
    """Rejects: a freeze document whose gate count is not the source's.

    D0.5's document said 23 static / 35 total; the source had 27 / 39.  The
    counts are computed here so the document can quote a test rather than a
    hand tally.
    """
    assert len(gates.VALIDITY_GATE_ORDER) == (
        len(gates.STATIC_GATE_ORDER) + len(gates.BLOCK_GATE_ORDER)
        + len(gates.ESTIMAND_GATE_ORDER))
    assert len(frozenset(gates.VALIDITY_GATE_ORDER)) == len(
        gates.VALIDITY_GATE_ORDER)
    assert tuple(name for name, _ in gates._static_gates()) == (
        gates.STATIC_GATE_ORDER)
