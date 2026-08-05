"""Record types and the closed schema registry for the D2 owner-match contract.

Every record that carries lineage, evidence, or a frozen literal is a frozen
dataclass registered in :mod:`canon`.  Round-6 validation found that D0.4
declared 23 registered schemas while the module performed 22 registrations --
``TargetCell``, the record that joins the private write, the verification
result, the analysis key and the public actor input, was defined but never
registered.  That made the claimed "complete lineage freeze" false and left
the central lineage object outside the digest-bearing contract.  Here every
record class defined in this module is registered, and
``registration_completeness_gate`` proves it mechanically rather than by
counting in prose.

The inherited D1 classes (``Snapshot``, ``Clone``, ``WriterInput``,
``SiblingWrite``, ``ActorInput``) are registered here too, unmodified and
imported from the pinned inherited module, so that D1 objects can be
serialized and compared under the same canonical rules as D2 objects.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from fractions import Fraction

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    ActorInput,
    Clone,
    SiblingWrite,
    Snapshot,
    WriterInput,
)

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    register_schema,
    schema_ids,
    seal_registry,
)


# ---------------------------------------------------------------------------
# Value records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RationalValue:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if type(self.numerator) is not int or type(self.denominator) is not int:
            raise ContractError("exact int rational parts required")
        if self.denominator <= 0:
            raise ContractError("positive denominator required")
        frac = Fraction(self.numerator, self.denominator)
        if (frac.numerator, frac.denominator) != (self.numerator,
                                                  self.denominator):
            raise ContractError("rational not in lowest terms")

    def as_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


def rational(value: Fraction) -> RationalValue:
    if type(value) is not Fraction:
        raise ContractError("exact Fraction required")
    return RationalValue(value.numerator, value.denominator)


@dataclass(frozen=True)
class DecimalLiteral:
    text: str


@dataclass(frozen=True)
class AnalysisKey:
    """Audit-only lineage key.

    ``m``, ``b`` and ``r`` are centered codes in {-1,+1}; ``q`` is the raw
    alias label in {0,1}.  The ``type(x) is int`` gates reject ``bool``:
    round 6 found that plain membership tests admitted ``True`` as ``m=1``,
    ``b=1``, ``r=1`` or ``q=1``, which would have let a boolean-typed label
    enter the analysis keyspace and collide with a genuine code.
    """

    m: int
    b: int
    r: int
    q: int

    def __post_init__(self) -> None:
        for name in ("m", "b", "r", "q"):
            if type(object.__getattribute__(self, name)) is not int:
                raise ContractError("exact int label required for %s" % name)
        if self.m not in (-1, 1) or self.b not in (-1, 1) or self.r not in (-1, 1):
            raise ContractError("centered code required")
        if self.q not in (0, 1):
            raise ContractError("raw q alias required")

    def as_tuple(self) -> tuple:
        return (self.q, self.m, self.b, self.r)


# ---------------------------------------------------------------------------
# D2 write / authentication records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActorInput_D2:
    payload: bytes
    valid: bool
    age: int
    actor_tensor: tuple
    recurrent_state: tuple
    legal_actions: tuple
    evaluation_order: tuple
    verified_owner_match: bool


@dataclass(frozen=True)
class WriterRegistryEntry_D2:
    writer_id: str
    key_id: str
    key: bytes


@dataclass(frozen=True)
class WriterRegistry_D2:
    entry_1: WriterRegistryEntry_D2
    entry_2: WriterRegistryEntry_D2


@dataclass(frozen=True)
class AuthSidecar_D2:
    writer_id: str
    key_id: str
    mac: bytes


@dataclass(frozen=True)
class SiblingWrite_D2:
    public: SiblingWrite
    sidecar: AuthSidecar_D2


@dataclass(frozen=True)
class ExpectedOwnerBinding:
    binding_version: str
    expected_owner_id: str
    source_snapshot_digest: str
    owner_epoch: int


@dataclass(frozen=True)
class VerificationResult:
    auth_ok: bool
    owner_match: bool
    writer_id: str
    transcript_digest: str


@dataclass(frozen=True)
class VerifiedOwnerPredicate:
    value: bool


@dataclass(frozen=True)
class MacEnvelope:
    writer_id: str
    key_id: str
    public_write_bytes: bytes


@dataclass(frozen=True)
class TranscriptEnvelope:
    binding_digest: str
    writer_id: str
    key_id: str
    mac: bytes
    auth_ok: bool
    owner_match: bool


# ---------------------------------------------------------------------------
# Lineage / block records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TargetCell:
    """The central lineage object.  Registered (round-6 correction D04-C01)."""

    key: AnalysisKey
    write: SiblingWrite_D2
    verification: VerificationResult
    actor_input: ActorInput_D2


@dataclass(frozen=True)
class CellEvidence:
    """Digest-bearing summary of one constructed cell."""

    key: AnalysisKey
    clone_id: str
    writer_id: str
    target_cell_digest: str
    actor_input_d1_digest: str
    actor_input_d2_digest: str


@dataclass(frozen=True)
class BlockCensus:
    """The complete matched census over the sixteen (m,b,r,q) cells."""

    block_id: str
    cells: tuple


@dataclass(frozen=True)
class ReplicaRecord:
    replica_id: str
    logits: tuple
    kernel: tuple


@dataclass(frozen=True)
class DiameterRecord:
    replicas: tuple
    eta_logit: float
    eta_kernel: float


@dataclass(frozen=True)
class CalibrationRecord:
    calibration_snapshot_digest: str
    diameter: DiameterRecord
    one_ulp_logit: float
    one_ulp_kernel: float
    u_logit: float
    u_kernel: float
    tau_logit: float
    tau_kernel: float
    delta_logit: float
    delta_kernel: float


@dataclass(frozen=True)
class EstimandRecord:
    d_logit: tuple
    d_kernel: tuple
    theta_logit: float
    theta_kernel: float


@dataclass(frozen=True)
class PlatformAdmission:
    python_version: str
    implementation: str
    worst_log_residual: DecimalLiteral
    worst_exp_residual: DecimalLiteral
    worst_recovery_residual: DecimalLiteral
    admitted: bool


# ---------------------------------------------------------------------------
# Frozen-table rows
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoefficientRow:
    q: int
    m: int
    b: int
    r: int
    coefficient: RationalValue


@dataclass(frozen=True)
class KernelRow:
    m: int
    b: int
    r: int
    k1: RationalValue
    k2: RationalValue


@dataclass(frozen=True)
class LogitRow:
    m: int
    b: int
    r: int
    c1: RationalValue
    c2: RationalValue


@dataclass(frozen=True)
class MutantRow:
    """One executable mutation control.

    ``transform_id`` keys an actual transformation function in
    :mod:`controls`; ``description`` is prose for the reader only.  Round 6
    found D0.4 shipped only prose in a field named ``transform``, so the
    mutants were digest-bearing descriptions rather than controls.  The
    ``mutant_dispatch_gate`` in :mod:`controls` proves every id here resolves
    to a real function and vice versa.
    """

    mutant_id: str
    transform_id: str
    description: str
    detector: str
    expected_response: str


@dataclass(frozen=True)
class CodeFingerprintRecord:
    qualname: str
    fingerprint_hex: str


@dataclass(frozen=True)
class GlobalBindingRecord:
    function_qualname: str
    global_name: str
    binding_kind: str
    binding_digest: str


@dataclass(frozen=True)
class InheritedSourceRecord:
    module_name: str
    source_digest: str
    blob_sha1: str
    commit: str


@dataclass(frozen=True)
class PrecommitEnvelope:
    serializer_version: str
    module_source_digest: str
    schema_registry_digest: str
    source_snapshot_digest: str
    inherited_source: InheritedSourceRecord
    registry_digest: str
    binding_digest: str
    logit_control_digest: str
    kernel_control_digest: str
    coefficient_oracle_digest: str
    mutant_matrix_digest: str
    fingerprint_set_digest: str
    curvature_reference_first_component: DecimalLiteral
    tol_recover: RationalValue
    tol_curv: RationalValue
    margin: RationalValue
    mpmath_version: str
    evaluator_fingerprint: str


# ---------------------------------------------------------------------------
# Schema identifiers and registration
# ---------------------------------------------------------------------------

D1 = "@orbit-shadow-read-d1"
D2 = "@orbit-owner-match-d2"

SCHEMA_SNAPSHOT_D1 = "Snapshot_D1" + D1
SCHEMA_CLONE_D1 = "Clone_D1" + D1
SCHEMA_WRITER_INPUT_D1 = "WriterInput_D1" + D1
SCHEMA_SIBLING_WRITE_D1 = "SiblingWrite_D1" + D1
SCHEMA_ACTOR_INPUT_D1 = "ActorInput_D1" + D1
SCHEMA_ACTOR_INPUT_D2 = "ActorInput_D2" + D2
SCHEMA_TARGET_CELL = "TargetCell" + D2
SCHEMA_MAC_ENVELOPE = "orbit-owner-mac-v3"
SCHEMA_TRANSCRIPT_ENVELOPE = "orbit-owner-transcript-v1"
SCHEMA_PRECOMMIT = "orbit-owner-precommit-v1"

_D1_ACTOR_FIELDS = (
    ("payload", "bytes"), ("valid", "bool"), ("age", "int"),
    ("actor_tensor", "tuple[float;4]"), ("recurrent_state", "tuple[float;2]"),
    ("legal_actions", "tuple[str;2]"), ("evaluation_order", "tuple[int;2]"),
)

_RATIONAL = "struct:RationalValue" + D2
_DECIMAL = "struct:DecimalLiteral" + D2
_ANALYSIS_KEY = "struct:AnalysisKey" + D2

# (schema_id, class, descriptor) -- the single source of truth.  Nothing is
# registered anywhere else, which is what makes the completeness gate total.
_SCHEMA_TABLE = (
    (SCHEMA_SNAPSHOT_D1, Snapshot, (
        ("snapshot_id", "str"), ("owner_epoch", "int"),
        ("current_state", "tuple[float;2]"),
        ("legal_actions", "tuple[str;2]"),
        ("recurrent_state", "tuple[float;2]"),
    )),
    (SCHEMA_CLONE_D1, Clone, (
        ("clone_id", "str"), ("snapshot", "struct:" + SCHEMA_SNAPSHOT_D1),
        ("source_bytes_digest", "str"),
    )),
    (SCHEMA_WRITER_INPUT_D1, WriterInput, (
        ("source_snapshot_digest", "str"), ("writer_schema", "str"),
        ("b", "int"),
    )),
    (SCHEMA_SIBLING_WRITE_D1, SiblingWrite, (
        ("writer_input", "struct:" + SCHEMA_WRITER_INPUT_D1),
        ("payload", "bytes"), ("valid", "bool"), ("age", "int"),
        ("writer_input_digest", "str"), ("ancestry_digest", "str"),
        ("auth_digest", "str"),
    )),
    (SCHEMA_ACTOR_INPUT_D1, ActorInput, _D1_ACTOR_FIELDS),
    (SCHEMA_ACTOR_INPUT_D2, ActorInput_D2,
     _D1_ACTOR_FIELDS + (("verified_owner_match", "bool"),)),
    ("WriterRegistryEntry_D2" + D2, WriterRegistryEntry_D2, (
        ("writer_id", "str"), ("key_id", "str"), ("key", "bytes"),
    )),
    ("WriterRegistry_D2" + D2, WriterRegistry_D2, (
        ("entry_1", "struct:WriterRegistryEntry_D2" + D2),
        ("entry_2", "struct:WriterRegistryEntry_D2" + D2),
    )),
    ("AuthSidecar_D2" + D2, AuthSidecar_D2, (
        ("writer_id", "str"), ("key_id", "str"), ("mac", "bytes"),
    )),
    ("SiblingWrite_D2" + D2, SiblingWrite_D2, (
        ("public", "struct:" + SCHEMA_SIBLING_WRITE_D1),
        ("sidecar", "struct:AuthSidecar_D2" + D2),
    )),
    ("ExpectedOwnerBinding" + D2, ExpectedOwnerBinding, (
        ("binding_version", "str"), ("expected_owner_id", "str"),
        ("source_snapshot_digest", "str"), ("owner_epoch", "int"),
    )),
    ("VerificationResult" + D2, VerificationResult, (
        ("auth_ok", "bool"), ("owner_match", "bool"), ("writer_id", "str"),
        ("transcript_digest", "str"),
    )),
    ("VerifiedOwnerPredicate" + D2, VerifiedOwnerPredicate, (
        ("value", "bool"),
    )),
    (SCHEMA_MAC_ENVELOPE, MacEnvelope, (
        ("writer_id", "str"), ("key_id", "str"),
        ("public_write_bytes", "bytes"),
    )),
    (SCHEMA_TRANSCRIPT_ENVELOPE, TranscriptEnvelope, (
        ("binding_digest", "str"), ("writer_id", "str"), ("key_id", "str"),
        ("mac", "bytes"), ("auth_ok", "bool"), ("owner_match", "bool"),
    )),
    (SCHEMA_TARGET_CELL, TargetCell, (
        ("key", _ANALYSIS_KEY),
        ("write", "struct:SiblingWrite_D2" + D2),
        ("verification", "struct:VerificationResult" + D2),
        ("actor_input", "struct:" + SCHEMA_ACTOR_INPUT_D2),
    )),
    ("CellEvidence" + D2, CellEvidence, (
        ("key", _ANALYSIS_KEY), ("clone_id", "str"), ("writer_id", "str"),
        ("target_cell_digest", "str"), ("actor_input_d1_digest", "str"),
        ("actor_input_d2_digest", "str"),
    )),
    ("BlockCensus" + D2, BlockCensus, (
        ("block_id", "str"),
        ("cells", "tuple[struct:CellEvidence" + D2 + ";16]"),
    )),
    ("ReplicaRecord" + D2, ReplicaRecord, (
        ("replica_id", "str"), ("logits", "tuple[float;2]"),
        ("kernel", "tuple[float;2]"),
    )),
    ("DiameterRecord" + D2, DiameterRecord, (
        ("replicas", "tuple[struct:ReplicaRecord" + D2 + ";4]"),
        ("eta_logit", "float"), ("eta_kernel", "float"),
    )),
    ("CalibrationRecord" + D2, CalibrationRecord, (
        ("calibration_snapshot_digest", "str"),
        ("diameter", "struct:DiameterRecord" + D2),
        ("one_ulp_logit", "float"), ("one_ulp_kernel", "float"),
        ("u_logit", "float"), ("u_kernel", "float"),
        ("tau_logit", "float"), ("tau_kernel", "float"),
        ("delta_logit", "float"), ("delta_kernel", "float"),
    )),
    ("EstimandRecord" + D2, EstimandRecord, (
        ("d_logit", "tuple[float;2]"), ("d_kernel", "tuple[float;2]"),
        ("theta_logit", "float"), ("theta_kernel", "float"),
    )),
    ("PlatformAdmission" + D2, PlatformAdmission, (
        ("python_version", "str"), ("implementation", "str"),
        ("worst_log_residual", _DECIMAL),
        ("worst_exp_residual", _DECIMAL),
        ("worst_recovery_residual", _DECIMAL),
        ("admitted", "bool"),
    )),
    ("RationalValue" + D2, RationalValue, (
        ("numerator", "int"), ("denominator", "int"),
    )),
    ("DecimalLiteral" + D2, DecimalLiteral, (("text", "str"),)),
    ("AnalysisKey" + D2, AnalysisKey, (
        ("m", "int"), ("b", "int"), ("r", "int"), ("q", "int"),
    )),
    ("CoefficientRow" + D2, CoefficientRow, (
        ("q", "int"), ("m", "int"), ("b", "int"), ("r", "int"),
        ("coefficient", _RATIONAL),
    )),
    ("KernelRow" + D2, KernelRow, (
        ("m", "int"), ("b", "int"), ("r", "int"),
        ("k1", _RATIONAL), ("k2", _RATIONAL),
    )),
    ("LogitRow" + D2, LogitRow, (
        ("m", "int"), ("b", "int"), ("r", "int"),
        ("c1", _RATIONAL), ("c2", _RATIONAL),
    )),
    ("MutantRow" + D2, MutantRow, (
        ("mutant_id", "str"), ("transform_id", "str"), ("description", "str"),
        ("detector", "str"), ("expected_response", "str"),
    )),
    ("CodeFingerprintRecord" + D2, CodeFingerprintRecord, (
        ("qualname", "str"), ("fingerprint_hex", "str"),
    )),
    ("GlobalBindingRecord" + D2, GlobalBindingRecord, (
        ("function_qualname", "str"), ("global_name", "str"),
        ("binding_kind", "str"), ("binding_digest", "str"),
    )),
    ("InheritedSourceRecord" + D2, InheritedSourceRecord, (
        ("module_name", "str"), ("source_digest", "str"),
        ("blob_sha1", "str"), ("commit", "str"),
    )),
    (SCHEMA_PRECOMMIT, PrecommitEnvelope, (
        ("serializer_version", "str"), ("module_source_digest", "str"),
        ("schema_registry_digest", "str"), ("source_snapshot_digest", "str"),
        ("inherited_source", "struct:InheritedSourceRecord" + D2),
        ("registry_digest", "str"), ("binding_digest", "str"),
        ("logit_control_digest", "str"), ("kernel_control_digest", "str"),
        ("coefficient_oracle_digest", "str"), ("mutant_matrix_digest", "str"),
        ("fingerprint_set_digest", "str"),
        ("curvature_reference_first_component", _DECIMAL),
        ("tol_recover", _RATIONAL), ("tol_curv", _RATIONAL),
        ("margin", _RATIONAL),
        ("mpmath_version", "str"), ("evaluator_fingerprint", "str"),
    )),
)

for _schema_id, _cls, _descriptor in _SCHEMA_TABLE:
    register_schema(_schema_id, _cls, _descriptor)

SCHEMA_OF_CLASS = {cls: schema_id for schema_id, cls, _ in _SCHEMA_TABLE}


def registration_completeness_gate() -> None:
    """Every frozen record class defined in this module is registered.

    This replaces the prose schema count that round 6 falsified.  It walks the
    module's own namespace rather than trusting a hand-maintained list, so a
    newly added record class that nobody registered fails the gate instead of
    silently sitting outside the digest-bearing contract.
    """
    module = sys.modules[__name__]
    registered_classes = {cls for _, cls, _ in _SCHEMA_TABLE}
    declared = []
    pending = [getattr(module, name) for name in dir(module)]
    seen = set()
    while pending:
        value = pending.pop()
        # ``isinstance`` rather than ``type(value) is type``: a dataclass
        # declared with any custom metaclass would otherwise be skipped and
        # sit outside the digest-bearing contract while this gate passed --
        # which is precisely the defect the gate exists to close.
        if not isinstance(value, type):
            continue
        if id(value) in seen:
            continue
        seen.add(id(value))
        if getattr(value, "__module__", None) != __name__:
            continue
        if hasattr(value, "__dataclass_fields__"):
            declared.append(value)
        # Nested classes are invisible to ``dir(module)``, so walk into them.
        pending.extend(vars(value).values())
    missing = [cls.__name__ for cls in declared
               if cls not in registered_classes]
    if missing:
        raise ContractError(
            "record classes defined but not registered: %s" % (sorted(missing),))
    if len(registered_classes) != len(_SCHEMA_TABLE):
        raise ContractError("a class is registered under two schema ids")
    if schema_ids() != tuple(sorted(sid for sid, _, _ in _SCHEMA_TABLE)):
        raise ContractError("registry contents differ from the schema table")


registration_completeness_gate()

# Seal immediately after the completeness proof: from here on
# ``register_schema`` refuses new entries and ``canon.registry_seal_gate``
# can detect any post-seal mutation of the mapping.
SEALED_REGISTRY_DIGEST = seal_registry()
