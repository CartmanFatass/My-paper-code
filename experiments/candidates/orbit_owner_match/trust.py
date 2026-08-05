"""Trust roots, authentication, verification and the declassifier boundary.

The owner-match predicate is the only channel by which owner identity may
reach the actor.  Everything in this module exists to make that claim
*executable* rather than disciplinary.

Round-6 validation rejected D0.4 here on one point: exact-class gates prove
type, not origin.  ``VerifiedOwnerPredicate(True)`` could be constructed
directly, so nothing forced a predicate to have come from a verified write.
Two mechanisms replace that gap, and neither relies on secrecy (the registry
keys are literals in this file, so a secret cannot be an origin proof):

1.  A frozen construction-site map (:data:`GUARDED_CONSTRUCTORS`).  The
    bytecode scan in :mod:`sealing` proves that inside the accepted call
    graph the NAME of each guarded class is loaded only where construction is
    permitted.  That is a claim about names, so it is paired with
    ``forbidden_handle_gate``, which removes the name-free spellings --
    ``registered_class(schema_id)(...)``, ``getattr(records, ...)``,
    ``type(existing)(...)`` -- that would otherwise walk around it.
2.  A lineage gate (:mod:`block`) that rebuilds every cell from its own
    recorded inputs and requires byte equality of the serialized
    ``TargetCell``.  A fabricated predicate cannot survive it: rebuilding
    from the cell's own ``writer_id`` recomputes ``owner_match`` from the
    binding, so a cell claiming a match it did not earn differs in bytes.

Neither alone is sufficient; together they make provenance an extensional
property of the accepted execution graph, which is what the closure contract
requires.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import pathlib
import sys

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    ActorInput,
    Clone,
    SiblingWrite,
    Snapshot,
    q_adapter,
    verify_sibling,
    write_sibling,
)

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    serialize_struct,
    sha256_hex,
)
from experiments.candidates.orbit_owner_match.records import (
    ActorInput_D2,
    AuthSidecar_D2,
    ExpectedOwnerBinding,
    InheritedSourceRecord,
    MacEnvelope,
    SCHEMA_ACTOR_INPUT_D1,
    SCHEMA_ACTOR_INPUT_D2,
    SCHEMA_MAC_ENVELOPE,
    SCHEMA_SIBLING_WRITE_D1,
    SCHEMA_TRANSCRIPT_ENVELOPE,
    SiblingWrite_D2,
    TranscriptEnvelope,
    VerificationResult,
    VerifiedOwnerPredicate,
    WriterRegistry_D2,
    WriterRegistryEntry_D2,
    D2,
)


# ---------------------------------------------------------------------------
# Trust-root literals
# ---------------------------------------------------------------------------

KEY_1 = b"orbit-owner-registry-key-1-of-2-v1"
KEY_2 = b"orbit-owner-registry-key-2-of-2-v1"

WRITER_REGISTRY = WriterRegistry_D2(
    WriterRegistryEntry_D2("W1", "K1", KEY_1),
    WriterRegistryEntry_D2("W2", "K2", KEY_2),
)

# Digest of the canonical serialization of the synthetic prior-epoch snapshot
# fixture.  Independently reproduced by the round-5 reviewer.
SOURCE_SNAPSHOT_DIGEST = (
    "27190b4a137b0e00acab2359ddd90107c759081466825121d9e370770e790610"
)

EXPECTED_OWNER_BINDING = ExpectedOwnerBinding(
    "orbit-owner-binding-v1", "W1", SOURCE_SNAPSHOT_DIGEST, 7)

# Calibration runs on a fixture disjoint from the discriminator's, so it needs
# its own binding: a single binding pinned to the discriminator snapshot would
# make verification on the calibration fixture impossible, and the alternative
# -- letting calibration skip verification -- would put a predicate into
# existence outside the closed construction path.
CALIBRATION_SNAPSHOT_DIGEST = (
    "fdcda2684bfd7e542ce8efdcaedf3d895a39cde5082dccaa2c68f5075b767571"
)

CALIBRATION_OWNER_BINDING = ExpectedOwnerBinding(
    "orbit-owner-binding-calibration-v1", "W1", CALIBRATION_SNAPSHOT_DIGEST, 3)

# Bindings are selected by source digest, never supplied by a caller: that is
# what keeps ``owner_match`` a derived fact rather than an argument.
ADMISSIBLE_BINDINGS = (EXPECTED_OWNER_BINDING, CALIBRATION_OWNER_BINDING)

# Identity of the inherited D1 module.  ``blob_sha1`` is the git object id,
# which is what an external reviewer can check against the pushed tree
# without depending on this machine's checkout; ``source_digest`` is the
# sha256 of the SAME (line-ending normalized) bytes.  Round 6 noted that no
# executable source/blob gate existed at all -- ``inherited_source_gate`` is
# that gate.
#
# Both digests are taken over LF-normalized bytes.  This checkout has
# ``core.autocrlf=true``, so the working file holds CRLF while the git object
# and the raw file an external reviewer fetches hold LF; a digest over raw
# on-disk bytes would therefore be checkout-dependent and unreproducible off
# this machine.  Normalization is what makes the frozen literal mean the same
# thing to the reviewer as it does here.
INHERITED_SOURCE = InheritedSourceRecord(
    "experiments.candidates.orbit_shadow_read.eight_cell_audit",
    "bd62eea3d56cde3f76b7a97b2daad5b3c45b03e305e7df6a3d9f2ac68a476ed6",
    "e027822166bf247dd0733831fe717998f14398ca",
    "d82a462aeab6609902711a14e1d8a6c6a2ec134a",
)

# guarded class name -> the sole function permitted to construct it inside
# the accepted call graph.
GUARDED_CONSTRUCTORS = {
    "AuthSidecar_D2": "build_write_d2_with_b",
    "SiblingWrite_D2": "build_write_d2_with_b",
    "VerificationResult": "verify_write_d2",
    "VerifiedOwnerPredicate": "declassify",
    "ActorInput_D2": "extend_d1_actor_input",
    "TargetCell": "build_target_cell",
}

SANCTIONED_PREDICATE_FIELD = "verified_owner_match"

FORBIDDEN_IDENTITY_CARRIERS = frozenset({
    "writer_id", "key_id", "key", "mac", "transcript_digest",
    "binding_version", "expected_owner_id", "sidecar", "auth_ok",
    "owner_match", "owner_match_raw", "registry_entry", "raw_m",
})


# ---------------------------------------------------------------------------
# Trust-root gates
# ---------------------------------------------------------------------------


def binding_for_source(source_snapshot_digest: str) -> ExpectedOwnerBinding:
    """Select the admissible binding for a source snapshot; fail closed."""
    for binding in ADMISSIBLE_BINDINGS:
        if binding.source_snapshot_digest == source_snapshot_digest:
            return binding
    raise ContractError("no admissible binding for this source snapshot")


def registry_uniqueness_gate() -> None:
    e1, e2 = WRITER_REGISTRY.entry_1, WRITER_REGISTRY.entry_2
    if e1.writer_id == e2.writer_id or e1.key_id == e2.key_id or e1.key == e2.key:
        raise ContractError("registry uniqueness violated")
    registered = (e1.writer_id, e2.writer_id)
    digests = set()
    for binding in ADMISSIBLE_BINDINGS:
        if binding.expected_owner_id not in registered:
            raise ContractError("expected owner is not a registered writer")
        digests.add(binding.source_snapshot_digest)
    if len(digests) != len(ADMISSIBLE_BINDINGS):
        raise ContractError("admissible bindings share a source snapshot")
    if CALIBRATION_SNAPSHOT_DIGEST == SOURCE_SNAPSHOT_DIGEST:
        raise ContractError("calibration fixture is not disjoint")


def normalized_source_bytes(path) -> bytes:
    """Read a source file as LF-normalized bytes.

    See the note on :data:`INHERITED_SOURCE`: without this, every source
    digest in the contract would depend on the checkout's line-ending
    configuration rather than on the content an external reviewer sees.
    """
    return pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")


def git_blob_sha1(data: bytes) -> str:
    """The git object id of ``data`` as a blob, computed without git."""
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def inherited_source_gate() -> None:
    """The imported inherited module is the exact pinned source.

    Checks the blob id, not only the sha256, because the blob id is what an
    external reviewer can compare against the repository tree.
    """
    module = sys.modules[INHERITED_SOURCE.module_name]
    data = normalized_source_bytes(module.__file__)
    if sha256_hex(data) != INHERITED_SOURCE.source_digest:
        raise ContractError("inherited source digest mismatch", "T3")
    if git_blob_sha1(data) != INHERITED_SOURCE.blob_sha1:
        raise ContractError("inherited source blob mismatch", "T3")


def registry_lookup(writer_id: str, key_id: str) -> bytes:
    for entry in (WRITER_REGISTRY.entry_1, WRITER_REGISTRY.entry_2):
        if entry.writer_id == writer_id and entry.key_id == key_id:
            return entry.key
    raise ContractError("unknown registry pair")


def key_id_for_writer(writer_id: str) -> str:
    for entry in (WRITER_REGISTRY.entry_1, WRITER_REGISTRY.entry_2):
        if entry.writer_id == writer_id:
            return entry.key_id
    raise ContractError("unknown writer id")


# ---------------------------------------------------------------------------
# MAC and transcript
# ---------------------------------------------------------------------------


def binding_digest_hex() -> str:
    return sha256_hex(serialize_struct(
        "ExpectedOwnerBinding" + D2, EXPECTED_OWNER_BINDING))


def compute_mac(key: bytes, writer_id: str, key_id: str,
                public: SiblingWrite) -> bytes:
    """MAC over the COMPLETE canonical bytes of the public write.

    Including ``writer_schema`` (round-4 correction): the inherited
    ``verify_sibling`` never checks it, so a schema swap would otherwise pass
    unauthenticated.
    """
    public_bytes = serialize_struct(SCHEMA_SIBLING_WRITE_D1, public)
    envelope = serialize_struct(
        SCHEMA_MAC_ENVELOPE, MacEnvelope(writer_id, key_id, public_bytes))
    return _hmac.new(key, envelope, hashlib.sha256).digest()


def compute_transcript(sidecar: AuthSidecar_D2, auth_ok: bool,
                       owner_match: bool) -> str:
    envelope = serialize_struct(SCHEMA_TRANSCRIPT_ENVELOPE, TranscriptEnvelope(
        binding_digest_hex(), sidecar.writer_id, sidecar.key_id, sidecar.mac,
        auth_ok, owner_match))
    return sha256_hex(envelope)


# ---------------------------------------------------------------------------
# Write construction (the only place writer identity is admitted)
# ---------------------------------------------------------------------------


def build_write_d2_with_b(snapshot: Snapshot, writer_id: str,
                          b: int) -> SiblingWrite_D2:
    """Build a D2 write.

    The public component is the unmodified inherited constructor output and
    is therefore byte-identical across writers for a fixed ``(snapshot, b)``.
    Writer identity exists only in the private sidecar.
    """
    if type(writer_id) is not str:
        raise ContractError("exact str writer_id required")
    if type(b) is not int or b not in (0, 1):
        raise ContractError("exact binary int b required")
    public = write_sibling(snapshot, b)
    key_id = key_id_for_writer(writer_id)
    key = registry_lookup(writer_id, key_id)
    mac = compute_mac(key, writer_id, key_id, public)
    return SiblingWrite_D2(public, AuthSidecar_D2(writer_id, key_id, mac))


# ---------------------------------------------------------------------------
# Verification (abort on failure; no failed result object is ever built)
# ---------------------------------------------------------------------------


def verify_write_d2(clone: Clone, w: SiblingWrite_D2) -> VerificationResult:
    if type(w) is not SiblingWrite_D2:
        raise ContractError("exact SiblingWrite_D2 required")
    if type(clone) is not Clone:
        raise ContractError("exact inherited Clone required")
    public = w.public
    if type(public) is not SiblingWrite:
        raise ContractError("exact inherited SiblingWrite required")
    if not verify_sibling(public):
        raise ContractError("inherited integrity failed")
    if public.writer_input.source_snapshot_digest != clone.source_bytes_digest:
        raise ContractError("write/clone source mismatch")
    reference = write_sibling(clone.snapshot, public.writer_input.b)
    if (serialize_struct(SCHEMA_SIBLING_WRITE_D1, public)
            != serialize_struct(SCHEMA_SIBLING_WRITE_D1, reference)):
        raise ContractError("public write is not the exact constructor output")
    sidecar = w.sidecar
    if type(sidecar) is not AuthSidecar_D2:
        raise ContractError("exact AuthSidecar_D2 required")
    key = registry_lookup(sidecar.writer_id, sidecar.key_id)
    expected_mac = compute_mac(key, sidecar.writer_id, sidecar.key_id, public)
    if not _hmac.compare_digest(expected_mac, sidecar.mac):
        raise ContractError("MAC verification failed")
    binding = binding_for_source(clone.source_bytes_digest)
    if binding.owner_epoch != clone.snapshot.owner_epoch:
        raise ContractError("binding/clone epoch mismatch")
    owner_match = sidecar.writer_id == binding.expected_owner_id
    transcript = compute_transcript(sidecar, True, owner_match)
    return VerificationResult(True, owner_match, sidecar.writer_id, transcript)


# ---------------------------------------------------------------------------
# Declassifier boundary: the sole V -> P flow
# ---------------------------------------------------------------------------


def declassify(vr: VerificationResult) -> VerifiedOwnerPredicate:
    if type(vr) is not VerificationResult:
        raise ContractError("exact VerificationResult required")
    if vr.auth_ok is not True:
        raise ContractError("declassify requires auth_ok True")
    if type(vr.owner_match) is not bool:
        raise ContractError("exact bool owner_match required")
    return VerifiedOwnerPredicate(vr.owner_match)


def extend_d1_actor_input(base: ActorInput,
                          predicate: VerifiedOwnerPredicate) -> ActorInput_D2:
    if type(base) is not ActorInput:
        raise ContractError("exact inherited ActorInput required")
    if type(predicate) is not VerifiedOwnerPredicate:
        raise ContractError("exact VerifiedOwnerPredicate required")
    if type(predicate.value) is not bool:
        raise ContractError("exact bool predicate value required")
    return ActorInput_D2(base.payload, base.valid, base.age, base.actor_tensor,
                         base.recurrent_state, base.legal_actions,
                         base.evaluation_order, predicate.value)


def project_write_D1(w: SiblingWrite_D2) -> SiblingWrite:
    if type(w) is not SiblingWrite_D2:
        raise ContractError("exact SiblingWrite_D2 required")
    if type(w.public) is not SiblingWrite:
        raise ContractError("exact inherited SiblingWrite required")
    return w.public


def strip_predicate(d2: ActorInput_D2) -> ActorInput:
    if type(d2) is not ActorInput_D2:
        raise ContractError("exact ActorInput_D2 required")
    return ActorInput(d2.payload, d2.valid, d2.age, d2.actor_tensor,
                      d2.recurrent_state, d2.legal_actions,
                      d2.evaluation_order)


def build_d1_actor_input(clone: Clone, w: SiblingWrite_D2, role: int,
                         q: int) -> ActorInput:
    """The inherited adapter, reached only through the D1 projection."""
    if type(role) is not int or role not in (0, 1):
        raise ContractError("exact binary int role required")
    if type(q) is not int or q not in (0, 1):
        raise ContractError("exact binary int q required")
    return q_adapter(clone, project_write_D1(w), role, q)


# ---------------------------------------------------------------------------
# Actor-surface gate (T2), exact rather than subset
# ---------------------------------------------------------------------------


def t2_surface_descriptor_gate(d1_fields: tuple, actor_attrs: frozenset,
                               d2_descriptor: tuple) -> None:
    """The D2 actor surface adds exactly the sanctioned predicate field.

    Round 6 found the D0.4 version used a subset test, so an empty or partial
    attribute allowlist passed, and it compared field names without the
    normalized type.  Both comparisons here are exact equalities.
    """
    expected = d1_fields + ((SANCTIONED_PREDICATE_FIELD, "bool"),)
    if d2_descriptor != expected:
        raise ContractError("D2 actor descriptor is not the sanctioned "
                            "extension of the D1 surface", "T2")
    if actor_attrs != frozenset({"actor_tensor", SANCTIONED_PREDICATE_FIELD}):
        raise ContractError("target actor read set is not exactly "
                            "{actor_tensor, verified_owner_match}", "T2")
    # The forbidden-carrier check is applied to the DESCRIPTOR rather than to
    # ``actor_attrs``: the exact-equality test above already fixes the read
    # set, so re-testing it against the forbidden set could never fail.  The
    # descriptor is where a carrier could actually appear.
    descriptor_names = frozenset(name for name, _ in d2_descriptor)
    if descriptor_names & FORBIDDEN_IDENTITY_CARRIERS:
        raise ContractError("identity carrier on the D2 actor surface", "T2")


def actor_input_schema_binding_gate(registry_view) -> None:
    """The D2 actor-input schema id still maps to the D2 record class."""
    if SCHEMA_ACTOR_INPUT_D2 not in registry_view:
        raise ContractError("D2 actor-input schema missing", "T2")
    if registry_view[SCHEMA_ACTOR_INPUT_D2][0] is not ActorInput_D2:
        raise ContractError("D2 actor-input schema rebound", "T2")
    if SCHEMA_ACTOR_INPUT_D1 not in registry_view:
        raise ContractError("D1 actor-input schema missing", "T2")
    if registry_view[SCHEMA_ACTOR_INPUT_D1][0] is not ActorInput:
        raise ContractError("D1 actor-input schema rebound", "T2")
