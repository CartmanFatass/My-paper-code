"""The phase-2 precommit envelope and the freeze evidence report.

Round 6 could not authenticate D0.4's module digest or its bytecode
fingerprints, because the module reached the reviewer as rendered
conversation text rather than as a file, and the exact interpreter was not
available.  Two changes answer that (D04-V03, D04-V04):

*   The contract now lives in a tracked package, so its bytes are reachable
    by git blob id and by raw URL.  :func:`package_source_records` digests
    every module of the package, and :func:`package_blob_records` gives the
    git object ids an external reviewer can compare against the tree without
    trusting this machine.
*   Envelope assembly is a function rather than a description, so nobody has
    to infer the concatenation order from prose.

All source digests are taken over LF-normalized bytes.  This checkout has
``core.autocrlf=true``: the working files hold CRLF while the git objects and
the raw files a reviewer fetches hold LF, so a digest over raw on-disk bytes
would be an artifact of this machine's configuration rather than a statement
about the content.
"""

from __future__ import annotations

import pathlib
import sys

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    SERIALIZER_VERSION,
    _enc_str,
    schema_registry_digest,
    serialize_struct,
    sha256_hex,
)
from experiments.candidates.orbit_owner_match.records import (
    PrecommitEnvelope,
    SCHEMA_PRECOMMIT,
    _SCHEMA_TABLE,
    D2,
)
from experiments.candidates.orbit_owner_match import controls as controls_module
from experiments.candidates.orbit_owner_match import (
    discriminator as discriminator_module,
)
from experiments.candidates.orbit_owner_match import gates as gates_module
from experiments.candidates.orbit_owner_match import numerics as numerics_module
from experiments.candidates.orbit_owner_match import records as records_module
from experiments.candidates.orbit_owner_match import sealing as sealing_module
from experiments.candidates.orbit_owner_match import trust as trust_module


PACKAGE_DIR = pathlib.Path(__file__).resolve().parent

# Modules that constitute the contract.  Listed rather than globbed so that a
# new file appearing in the directory changes the manifest gate instead of
# silently joining the digest.
PACKAGE_MODULES = (
    "canon.py",
    "records.py",
    "trust.py",
    "block.py",
    "controls.py",
    "discriminator.py",
    "numerics.py",
    "sealing.py",
    "gates.py",
    "precommit.py",
    "baseline.py",
)

# ``baseline.py`` stores the frozen expectation that ``package_source`` is
# compared against, so it cannot be inside the digest it records.  It is
# authenticated externally, by git blob id -- see the module docstring there.
# It still appears in PACKAGE_MODULES, so a change to it is visible in the
# manifest and in the blob records; it is only excluded from the one digest it
# would make self-referential.
UNSEALED_MODULES = ("baseline.py",)

SEALED_MODULES = tuple(name for name in PACKAGE_MODULES
                       if name not in UNSEALED_MODULES)


def package_source_records() -> tuple:
    records = []
    for name in SEALED_MODULES:
        data = trust_module.normalized_source_bytes(PACKAGE_DIR / name)
        records.append((name, sha256_hex(data)))
    return tuple(records)


def package_blob_records() -> tuple:
    """Blob ids for EVERY module, baseline included.

    The blob manifest is the external anchor, so it must cover the file that
    the internal digest cannot.
    """
    records = []
    for name in PACKAGE_MODULES:
        data = trust_module.normalized_source_bytes(PACKAGE_DIR / name)
        records.append((name, trust_module.git_blob_sha1(data)))
    return tuple(records)


def package_manifest_gate() -> None:
    """The listed modules are EXACTLY the package's Python files.

    No name filtering: an earlier version skipped files starting with an
    underscore, which meant a module named ``_anything.py`` could join the
    package -- there is no ``__init__.py``, so this is a namespace package
    and every ``.py`` beside it is importable -- without appearing in the
    manifest or in the source digest.
    """
    present = tuple(sorted(path.name for path in PACKAGE_DIR.glob("*.py")))
    if present != tuple(sorted(PACKAGE_MODULES)):
        raise ContractError(
            "package manifest drift: present=%r listed=%r"
            % (present, tuple(sorted(PACKAGE_MODULES))))


def package_source_digest() -> str:
    parts = []
    for name, digest in package_source_records():
        parts.append(_enc_str(name))
        parts.append(_enc_str(digest))
    return sha256_hex(b"".join(parts))


def build_precommit_envelope() -> PrecommitEnvelope:
    return PrecommitEnvelope(
        SERIALIZER_VERSION,
        package_source_digest(),
        schema_registry_digest(),
        trust_module.SOURCE_SNAPSHOT_DIGEST,
        trust_module.INHERITED_SOURCE,
        sha256_hex(serialize_struct("WriterRegistry_D2" + D2,
                                    trust_module.WRITER_REGISTRY)),
        trust_module.binding_digest_hex(),
        controls_module.logit_control_digest(),
        controls_module.kernel_control_digest(),
        controls_module.coefficient_oracle_digest(),
        controls_module.mutant_matrix_digest(),
        sealing_module.fingerprint_set_digest(),
        controls_module.CURVATURE_REFERENCE_FIRST_COMPONENT,
        controls_module.TOL_RECOVER,
        controls_module.TOL_CURV,
        controls_module.MARGIN,
        _mpmath_version(),
        sealing_module.fingerprint_function(
            numerics_module.hp_curvature_reference),
        sealing_module.global_binding_digest(),
        sealing_module.class_behavior_digest(),
        gates_module.gate_order_digest(),
        blob_manifest_digest(),
        "%s %d.%d.%d" % ((sys.implementation.name,) + sys.version_info[:3]),
        execution_ledger_digest(),
    )


def blob_manifest_digest() -> str:
    parts = []
    for name, blob in package_blob_records():
        parts.append(_enc_str(name))
        parts.append(_enc_str(blob))
    return sha256_hex(b"".join(parts))


def execution_ledger_digest() -> str:
    """Digest of the ledger reading, so the envelope carries the claim.

    D0.5 printed the ledger next to the envelope digest, which meant the
    committed digest was compatible with any ledger at all.
    """
    counts = discriminator_module.EXECUTION_LEDGER.snapshot()
    parts = []
    for name in sorted(counts):
        parts.append(_enc_str(name))
        parts.append(_enc_str(str(counts[name])))
    return sha256_hex(b"".join(parts))


def _mpmath_version() -> str:
    import mpmath
    return mpmath.__version__


def precommit_bytes(envelope=None) -> bytes:
    if envelope is None:
        envelope = build_precommit_envelope()
    return serialize_struct(SCHEMA_PRECOMMIT, envelope)


def precommit_digest(envelope=None) -> str:
    return sha256_hex(precommit_bytes(envelope))


# ---------------------------------------------------------------------------
# Freeze evidence
# ---------------------------------------------------------------------------


def freeze_evidence() -> dict:
    """Everything a reviewer needs to re-derive the freeze, in one call.

    Includes the discriminator execution ledger, which must be all zeros.

    WHAT THAT DOES AND DOES NOT SHOW.  An all-zero ledger read from a
    freshly launched interpreter is evidence that THIS process never ran
    the discriminator.  It is NOT evidence that no process ever did, and it
    is NOT tamper-proof within its own process.  An earlier version of this
    docstring claimed the ledger was monotone with no reset; that claim was
    false and is withdrawn.  ExecutionLedger blocks __setattr__ and
    __delattr__ on the instance, but the module global holding it is an
    ordinary name, and

        discriminator.EXECUTION_LEDGER = ExecutionLedger()

    restores an all-zero ledger after a full run with every gate and both
    runtime seals still passing, because PROCESS_STATE_GLOBALS pins that
    slot by type and not by value.  Neutering ExecutionLedger.increment has
    the same effect, because its methods are outside every digest.

    The load-bearing control is therefore EXTERNAL, not this counter:
    scripts/orbit_owner_freeze_evidence.py launches a clean interpreter and
    the ledger is read from a process whose entire lifetime is visible in
    the command that started it.  Read this field as a cheap consistency
    check on an externally launched process, not as a tamper seal.

    The envelope is built ONCE and reused for both the reported fields and
    the reported digest; building it separately for each meant the digest
    described a different object from the one whose fields were printed.

    The numeric-audit counters are deliberately NOT reported: they count how
    many times the self-audit ran in this process, so they rise on every
    call and made two consecutive evidence dumps differ for no contractual
    reason.  The evidence is now idempotent.
    """
    package_manifest_gate()
    verdict = gates_module.run_static_gates()
    if verdict:
        raise ContractError("static gate suite failed: %s" % (verdict,))
    gates_module.gate_order_gate()
    discriminator_module.execution_ledger_gate()
    envelope = build_precommit_envelope()
    admission = numerics_module.platform_admission_literals()
    platform = records_module.PlatformAdmission(
        "%d.%d.%d" % sys.version_info[:3],
        sys.implementation.name,
        admission[0], admission[1], admission[2], True)
    return {
        "serializer_version": SERIALIZER_VERSION,
        "package_source_records": package_source_records(),
        "package_blob_records": package_blob_records(),
        "package_source_digest": envelope.module_source_digest,
        "schema_registry_digest": envelope.schema_registry_digest,
        "schema_count": len(_SCHEMA_TABLE),
        "inherited_source_digest": trust_module.INHERITED_SOURCE.source_digest,
        "inherited_blob_sha1": trust_module.INHERITED_SOURCE.blob_sha1,
        "source_snapshot_digest": trust_module.SOURCE_SNAPSHOT_DIGEST,
        "registry_digest": envelope.registry_digest,
        "binding_digest": envelope.binding_digest,
        "logit_control_digest": envelope.logit_control_digest,
        "kernel_control_digest": envelope.kernel_control_digest,
        "coefficient_oracle_digest": envelope.coefficient_oracle_digest,
        "mutant_matrix_digest": envelope.mutant_matrix_digest,
        "fingerprint_set_digest": envelope.fingerprint_set_digest,
        "fingerprint_count": len(sealing_module.fingerprint_set()),
        "global_binding_digest": sealing_module.global_binding_digest(),
        "global_binding_count": len(sealing_module.global_binding_records()),
        "precommit_digest": precommit_digest(envelope),
        "precommit_envelope_bytes": len(precommit_bytes(envelope)),
        "validity_gate_order": gates_module.VALIDITY_GATE_ORDER,
        "gate_counts": {
            "static": len(gates_module.STATIC_GATE_ORDER),
            "block": len(gates_module.BLOCK_GATE_ORDER),
            "estimand": len(gates_module.ESTIMAND_GATE_ORDER),
            "total": len(gates_module.VALIDITY_GATE_ORDER),
        },
        "gate_order_digest": envelope.gate_order_digest,
        "blob_manifest_digest": envelope.blob_manifest_digest,
        "class_behavior_digest": envelope.class_behavior_digest,
        "interpreter": "%s %s" % (platform.implementation,
                                  platform.python_version),
        "platform_worst_log_relative_error": platform.worst_log_residual.text,
        "platform_worst_exp_relative_error": platform.worst_exp_residual.text,
        "platform_worst_recovery_residual":
            platform.worst_recovery_residual.text,
        "execution_ledger": discriminator_module.EXECUTION_LEDGER.snapshot(),
    }
