"""Distinct create-only publication and validation for OMRC B1 evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence
import uuid

from .artifact import (
    canonical_json_bytes,
    create_staging_directory,
    directory_size,
    ensure_confined,
)
from .b0 import ARMS
from .b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_OBJECT_DURABLE_CAP_BYTES,
    B1_RUN_NAME,
    B1_SEEDS,
    B1_SLOT_ORDER,
    B1AttemptLedger,
    B1ContractError,
    B1LedgerBinding,
    B1Plan,
    B1ResumeCheckpointBinding,
    B1SlotLedgerEntry,
    B1SlotStatus,
    validate_b1_attempt_ledger,
)


B1_RESULT_SCHEMA = "cbsc_omrc_b01_b1_complete_result_v1"
B1_TEST_RESULT_SCHEMA = "cbsc_omrc_b01_b1_complete_result_test_only_v1"
B1_INCIDENT_SCHEMA = "cbsc_omrc_b01_b1_incident_v1"
B1_TEST_INCIDENT_SCHEMA = "cbsc_omrc_b01_b1_incident_test_only_v1"
B1_RAW_ANALYSIS_SCHEMA = "cbsc_omrc_b01_b1_raw_analysis_v1"
DECISION_PENDING = "DECISION_PENDING"
DECISION_REASONS = (
    "AUC_DEFINITION_PENDING",
    "DIAGNOSTIC_AGGREGATION_PENDING",
    "SCIENTIFIC_BRANCH_CLASSIFIER_PENDING",
)
OBJECT_ID = "CBSC-OMRC-B01"
CLARIFICATION_ID = "cbsc-online-b-innovator-20260901-02"
CLAIM_CEILING = "ENGINEERING_EVIDENCE_ONLY_DECISION_PENDING"


class B1ArtifactError(ValueError):
    """A B1 artifact is incomplete, noncanonical, or not fail-closed."""


@dataclass(frozen=True)
class B1IncidentLineageWitness:
    """Opaque validated chain; ordinary caller lists are not production authority."""

    allowed_root: Path
    canonical_references: tuple[bytes, ...]
    incident_snapshots: tuple[bytes, ...]
    binding: B1LedgerBinding | None

    def __post_init__(self) -> None:
        if len(self.canonical_references) != len(self.incident_snapshots):
            raise B1ArtifactError("incident witness reference/snapshot counts differ")


def _require_hex(name: str, value: object, length: int) -> None:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1ArtifactError(f"{name} must be {length} lowercase hexadecimal characters")


def _require_arm_seed_coverage(name: str, records: object) -> list[Mapping[str, Any]]:
    if not isinstance(records, list) or len(records) != 12:
        raise B1ArtifactError(f"{name} must contain all 12 arm-seed records")
    expected = {(arm, seed) for arm in ARMS for seed in B1_SEEDS}
    observed: set[tuple[object, object]] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise B1ArtifactError(f"{name} contains a non-record")
        key = (record.get("arm"), record.get("seed"))
        if key in observed:
            raise B1ArtifactError(f"{name} contains duplicate arm-seed identity")
        observed.add(key)
    if observed != expected:
        raise B1ArtifactError(f"{name} arm-seed coverage differs")
    return records


def _validate_analysis(value: object) -> None:
    if not isinstance(value, Mapping):
        raise B1ArtifactError("analysis is absent")
    if value.get("schema") != B1_RAW_ANALYSIS_SCHEMA:
        raise B1ArtifactError("analysis schema differs")
    if value.get("decision") != DECISION_PENDING:
        raise B1ArtifactError("analysis must remain DECISION_PENDING")
    if value.get("decision_reasons") != list(DECISION_REASONS):
        raise B1ArtifactError("analysis pending reasons differ")
    if value.get("normalized_return_auc") is not None:
        raise B1ArtifactError("AUC must remain null pending its literal definition")
    if value.get("diagnostic_aggregates") is not None:
        raise B1ArtifactError("diagnostic aggregation must remain null pending its literal law")
    if value.get("scientific_branch") is not None:
        raise B1ArtifactError("analysis cannot infer a scientific branch")
    if not isinstance(value.get("raw_checkpoint_records"), list) or len(
        value["raw_checkpoint_records"]
    ) != 48:
        raise B1ArtifactError("analysis does not preserve all 48 raw checkpoint records")
    if not isinstance(value.get("per_seed_curves"), list) or len(value["per_seed_curves"]) != 12:
        raise B1ArtifactError("analysis does not preserve all 12 seed curves")


def validate_b1_complete_manifest(
    value: Mapping[str, Any], *, allow_test_only: bool = False
) -> dict[str, Any]:
    """Validate one complete B1 manifest without forming a scientific decision."""

    if not isinstance(value, Mapping):
        raise B1ArtifactError("B1 manifest must be a mapping")
    manifest = dict(value)
    required = {
        "schema",
        "test_only",
        "object_id",
        "clarification_id",
        "run_name",
        "implementation_commit",
        "source_conformance_sha256",
        "b0_evidence",
        "pinned_evidence_ref",
        "evidence_sha256",
        "configuration_sha256",
        "law_digests",
        "arms",
        "seeds",
        "checkpoint_updates",
        "checkpoint_identities",
        "counts",
        "arm_seed_records",
        "analysis",
        "resource_caps",
        "resource_admissions",
        "telemetry",
        "parity_audits",
        "numerical_finiteness_audit",
        "incident_references",
        "durable_size_bytes",
        "scientific_branch",
        "scientific_claim",
        "decision",
        "claim_ceiling",
    }
    missing = required - set(manifest)
    if missing:
        raise B1ArtifactError(f"B1 manifest fields are missing: {sorted(missing)}")
    extra = set(manifest) - required
    if extra:
        raise B1ArtifactError(f"B1 manifest fields are not frozen: {sorted(extra)}")

    if manifest["schema"] == B1_TEST_RESULT_SCHEMA:
        if not allow_test_only or manifest["test_only"] is not True:
            raise B1ArtifactError("TEST_ONLY B1 schema requires explicit test-only validation")
    elif manifest["schema"] == B1_RESULT_SCHEMA:
        raise B1ArtifactError(
            "legacy caller-manifest formal publication is permanently disabled; "
            "use the canonical metrics production publisher"
        )
    else:
        raise B1ArtifactError("B1 result schema differs")
    if (
        manifest["object_id"] != OBJECT_ID
        or manifest["clarification_id"] != CLARIFICATION_ID
        or manifest["run_name"] != B1_RUN_NAME
    ):
        raise B1ArtifactError("B1 artifact identity differs")
    _require_hex("implementation_commit", manifest["implementation_commit"], 40)
    _require_hex("source_conformance_sha256", manifest["source_conformance_sha256"], 64)
    b0_evidence = manifest["b0_evidence"]
    if not isinstance(b0_evidence, Mapping) or set(b0_evidence) != {
        "manifest_sha256",
        "manifest_bytes",
        "reviewed_receipt_sha256",
        "inventory_sha256",
        "file_count",
        "total_bytes",
    }:
        raise B1ArtifactError("B0 evidence identity fields differ")
    _require_hex("B0 evidence manifest_sha256", b0_evidence["manifest_sha256"], 64)
    _require_hex(
        "B0 evidence reviewed_receipt_sha256",
        b0_evidence["reviewed_receipt_sha256"],
        64,
    )
    _require_hex("B0 evidence inventory_sha256", b0_evidence["inventory_sha256"], 64)
    if type(b0_evidence["manifest_bytes"]) is not int or b0_evidence["manifest_bytes"] <= 0:
        raise B1ArtifactError("B0 evidence manifest_bytes must be a positive exact integer")
    for field in ("file_count", "total_bytes"):
        if type(b0_evidence[field]) is not int or b0_evidence[field] <= 0:
            raise B1ArtifactError(
                f"B0 evidence {field} must be a positive exact integer"
            )
    _require_hex("pinned_evidence_ref", manifest["pinned_evidence_ref"], 40)
    _require_hex("evidence_sha256", manifest["evidence_sha256"], 64)
    _require_hex("configuration_sha256", manifest["configuration_sha256"], 64)
    laws = manifest["law_digests"]
    if not isinstance(laws, Mapping) or set(laws) != {
        "environment",
        "adapter",
        "token",
        "analysis",
    }:
        raise B1ArtifactError("B1 law digests differ")
    for name, digest in laws.items():
        _require_hex(f"law_digests.{name}", digest, 64)

    plan = B1Plan()
    if manifest["arms"] != list(ARMS) or manifest["seeds"] != list(B1_SEEDS):
        raise B1ArtifactError("B1 arm or seed identity differs")
    if manifest["checkpoint_updates"] != list(B1_CHECKPOINT_UPDATES):
        raise B1ArtifactError("B1 checkpoint updates differ")
    expected_checkpoint_identities = [
        f"{arm}-{seed}-update-{update}"
        for arm in ARMS
        for seed in B1_SEEDS
        for update in B1_CHECKPOINT_UPDATES
    ]
    if manifest["checkpoint_identities"] != expected_checkpoint_identities:
        raise B1ArtifactError("B1 checkpoint identities differ")
    if manifest["counts"] != {
        "arm_seed_count": 12,
        "per_arm_seed": plan.counts_per_arm_seed,
    }:
        raise B1ArtifactError("B1 exact counts differ")
    arm_seed_records = _require_arm_seed_coverage("arm_seed_records", manifest["arm_seed_records"])
    for record in arm_seed_records:
        identities = [
            f"{record['arm']}-{record['seed']}-update-{update}"
            for update in B1_CHECKPOINT_UPDATES
        ]
        if (
            record.get("counts") != plan.counts_per_arm_seed
            or record.get("checkpoint_identities") != identities
            or record.get("complete") is not True
        ):
            raise B1ArtifactError("an arm-seed record is incomplete")

    _validate_analysis(manifest["analysis"])
    recomputed_evidence_sha256 = hashlib.sha256(
        canonical_json_bytes(manifest["analysis"]["raw_checkpoint_records"])
    ).hexdigest()
    if manifest["evidence_sha256"] != recomputed_evidence_sha256:
        raise B1ArtifactError(
            "evidence_sha256 differs from canonical raw checkpoint records"
        )
    recomputed_configuration_sha256 = hashlib.sha256(
        canonical_json_bytes(plan.as_dict())
    ).hexdigest()
    if manifest["configuration_sha256"] != recomputed_configuration_sha256:
        raise B1ArtifactError(
            "configuration_sha256 differs from the immutable B1Plan"
        )
    if manifest["resource_caps"] != plan.resource_caps.as_dict():
        raise B1ArtifactError("B1 resource caps differ")
    admissions = _require_arm_seed_coverage(
        "resource admission records", manifest["resource_admissions"]
    )
    if any(record.get("admitted") is not True for record in admissions):
        raise B1ArtifactError("a B1 resource admission failed")
    telemetry = _require_arm_seed_coverage("telemetry records", manifest["telemetry"])
    required_telemetry = {
        "within_caps",
        "process_tree_peak_rss_bytes",
        "scratch_high_water_bytes",
        "durable_high_water_bytes",
        "wall_seconds",
    }
    for record in telemetry:
        if record.get("within_caps") is not True or not required_telemetry <= set(record):
            raise B1ArtifactError("a B1 telemetry record is incomplete or outside caps")
    parity = manifest["parity_audits"]
    if not isinstance(parity, Mapping) or not parity or any(value is not True for value in parity.values()):
        raise B1ArtifactError("all B1 parity audits must be present and true")
    if manifest["numerical_finiteness_audit"] is not True:
        raise B1ArtifactError("B1 numerical finiteness audit failed")
    incident_references = manifest["incident_references"]
    if not isinstance(incident_references, list):
        raise B1ArtifactError("incident reference lineage must be an ordered list")
    seen_incidents: set[tuple[str, str]] = set()
    for reference in incident_references:
        if not isinstance(reference, Mapping) or set(reference) != {
            "attempt_id",
            "incident_manifest_sha256",
            "attempt_ledger_sha256",
            "incident_relative_path",
        }:
            raise B1ArtifactError("incident reference fields differ")
        attempt_id = reference["attempt_id"]
        if type(attempt_id) is not str or not attempt_id or attempt_id.strip() != attempt_id:
            raise B1ArtifactError("incident reference attempt_id must be a nonempty exact string")
        _require_hex(
            "incident reference incident_manifest_sha256",
            reference["incident_manifest_sha256"],
            64,
        )
        relative_text = reference["incident_relative_path"]
        if type(relative_text) is not str:
            raise B1ArtifactError("incident reference path must be an exact string")
        relative = PurePosixPath(relative_text)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != relative_text
            or relative.name != "incident.json"
        ):
            raise B1ArtifactError("incident reference path must be confined and canonical")
        identity = (relative_text, reference["incident_manifest_sha256"])
        if identity in seen_incidents:
            raise B1ArtifactError("incident reference lineage contains a cycle or duplicate")
        seen_incidents.add(identity)
        _require_hex(
            "incident reference attempt_ledger_sha256",
            reference["attempt_ledger_sha256"],
            64,
        )
    durable = manifest["durable_size_bytes"]
    if type(durable) is not int or not 0 <= durable <= B1_OBJECT_DURABLE_CAP_BYTES:
        raise B1ArtifactError("B1 durable size exceeds the 512 MiB cap")
    if manifest["scientific_branch"] is not None or manifest["scientific_claim"] is not None:
        raise B1ArtifactError("B1 cannot contain a local scientific branch or claim")
    if manifest["decision"] != DECISION_PENDING or manifest["claim_ceiling"] != CLAIM_CEILING:
        raise B1ArtifactError("B1 must remain engineering evidence with decision pending")
    try:
        canonical_json_bytes(manifest)
    except Exception as exc:
        raise B1ArtifactError("B1 manifest is not finite canonical JSON") from exc
    return manifest


def create_b1_staging_directory(final_path: Path, *, allowed_root: Path) -> Path:
    """Create one private sibling staging directory for a B1 transaction."""

    return create_staging_directory(final_path, allowed_root=allowed_root)


def _decode_ledger_binding(value: object) -> B1LedgerBinding:
    if not isinstance(value, Mapping) or set(value) != {
        "attempt_id",
        "run_name",
        "implementation_commit",
        "source_conformance_sha256",
        "configuration_sha256",
        "laws_sha256",
        "b0_manifest_sha256",
        "b0_manifest_bytes",
        "b0_reviewed_receipt_sha256",
        "b0_inventory_sha256",
        "b0_file_count",
        "b0_total_bytes",
        "object_id",
        "innovator_selection_request_id",
        "innovator_selection_archive_path",
        "innovator_selection_response_sha256",
        "literal_binding_request_id",
        "literal_binding_archive_path",
        "literal_binding_response_sha256",
        "metrics_only_request_id",
        "metrics_only_archive_path",
        "metrics_only_response_sha256",
    }:
        raise B1ArtifactError("attempt ledger binding fields differ")
    return B1LedgerBinding(**dict(value))


def _decode_resume_checkpoint(value: object) -> B1ResumeCheckpointBinding | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {
        "schema",
        "binding",
        "slot_index",
        "seed",
        "arm",
        "completed_rollout_updates",
        "checkpoint_relative_path",
        "checkpoint_sha256",
        "order_chain_sha256",
    }:
        raise B1ArtifactError("attempt ledger resume-checkpoint fields differ")
    return B1ResumeCheckpointBinding(
        schema=value["schema"],
        binding=_decode_ledger_binding(value["binding"]),
        slot_index=value["slot_index"],
        seed=value["seed"],
        arm=value["arm"],
        completed_rollout_updates=value["completed_rollout_updates"],
        checkpoint_relative_path=value["checkpoint_relative_path"],
        checkpoint_sha256=value["checkpoint_sha256"],
        order_chain_sha256=value["order_chain_sha256"],
    )


def _decode_slot(value: object) -> B1SlotLedgerEntry:
    if not isinstance(value, Mapping) or set(value) != {
        "binding",
        "slot_index",
        "seed",
        "arm",
        "status",
        "raw_result_sha256",
        "admission_sha256",
        "telemetry_sha256",
        "files_sha256",
        "incident_sha256",
        "resume_checkpoint",
    }:
        raise B1ArtifactError("attempt ledger slot fields differ")
    try:
        status = B1SlotStatus(value["status"])
    except (TypeError, ValueError) as exc:
        raise B1ArtifactError("attempt ledger slot status differs") from exc
    return B1SlotLedgerEntry(
        binding=_decode_ledger_binding(value["binding"]),
        slot_index=value["slot_index"],
        seed=value["seed"],
        arm=value["arm"],
        status=status,
        raw_result_sha256=value["raw_result_sha256"],
        admission_sha256=value["admission_sha256"],
        telemetry_sha256=value["telemetry_sha256"],
        files_sha256=value["files_sha256"],
        incident_sha256=value["incident_sha256"],
        resume_checkpoint=_decode_resume_checkpoint(value["resume_checkpoint"]),
    )


def validate_b1_attempt_ledger_document(value: Mapping[str, Any]) -> B1AttemptLedger:
    """Strictly decode JSON-shaped ledger bytes into the immutable contract type."""

    if not isinstance(value, Mapping) or set(value) != {
        "schema",
        "publication_mode",
        "binding",
        "slot_order",
        "slots",
    }:
        raise B1ArtifactError("attempt ledger document fields differ")
    expected_order = [
        {"slot_index": index, "seed": seed, "arm": arm}
        for index, (seed, arm) in enumerate(B1_SLOT_ORDER)
    ]
    if value["slot_order"] != expected_order:
        raise B1ArtifactError("attempt ledger slot order differs")
    if not isinstance(value["slots"], list):
        raise B1ArtifactError("attempt ledger slots must be a JSON list")
    try:
        ledger = B1AttemptLedger(
            schema=value["schema"],
            publication_mode=value["publication_mode"],
            binding=_decode_ledger_binding(value["binding"]),
            slots=tuple(_decode_slot(slot) for slot in value["slots"]),
        )
        return validate_b1_attempt_ledger(ledger)
    except B1ContractError as exc:
        raise B1ArtifactError(f"attempt ledger binding/contract failure: {exc}") from exc


def publish_b1_attempt_ledger(
    path: Path,
    ledger: B1AttemptLedger,
    *,
    allowed_root: Path,
) -> str:
    """Create one immutable canonical ledger file and return its byte SHA-256."""

    destination = ensure_confined(path, allowed_root)
    if destination.suffix != ".json":
        raise B1ArtifactError("attempt ledger path must end in .json")
    try:
        validate_b1_attempt_ledger(ledger)
    except B1ContractError as exc:
        raise B1ArtifactError(f"attempt ledger contract failure: {exc}") from exc
    payload = canonical_json_bytes(ledger.as_dict()) + b"\n"
    _write_fsync(destination, payload)
    _fsync_directory(destination.parent)
    return hashlib.sha256(payload).hexdigest()


def load_b1_attempt_ledger(
    path: Path,
    *,
    allowed_root: Path,
    expected_sha256: str,
    expected_binding: B1LedgerBinding | None = None,
) -> B1AttemptLedger:
    """Read a ledger without mutation, binding exact bytes and source identity."""

    source = ensure_confined(path, allowed_root)
    _require_hex("expected ledger SHA", expected_sha256, 64)
    if not source.is_file():
        raise B1ArtifactError("attempt ledger file is absent")
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise B1ArtifactError("attempt ledger file SHA differs")
    try:
        decoded = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B1ArtifactError("attempt ledger bytes are not canonical JSON") from exc
    if canonical_json_bytes(decoded) + b"\n" != payload:
        raise B1ArtifactError("attempt ledger file bytes are not canonical")
    ledger = validate_b1_attempt_ledger_document(decoded)
    if expected_binding is not None:
        if type(expected_binding) is not B1LedgerBinding:
            raise B1ArtifactError("expected attempt ledger binding type differs")
        if ledger.binding != expected_binding:
            raise B1ArtifactError("attempt ledger binding refuses cross-source resume")
    return ledger


def _write_fsync(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_b1_complete(
    staging: Path,
    final_path: Path,
    manifest: Mapping[str, Any],
    *,
    allowed_root: Path,
    allow_test_only: bool = False,
) -> Path:
    """Publish only a TEST_ONLY legacy fixture; formal publication is impossible here."""

    staging = ensure_confined(staging, allowed_root)
    final = ensure_confined(final_path, allowed_root)
    if not staging.is_dir() or staging.parent != final.parent or ".partial-" not in staging.name:
        raise B1ArtifactError("B1 staging must be an existing private sibling")
    if final.exists():
        raise FileExistsError(f"create-only B1 artifact already exists: {final}")
    if manifest.get("schema") != B1_TEST_RESULT_SCHEMA or manifest.get("test_only") is not True:
        raise B1ArtifactError(
            "legacy caller-manifest publisher is permanently TEST_ONLY"
        )
    validated = validate_b1_complete_manifest(manifest, allow_test_only=allow_test_only)
    references = validated["incident_references"]
    if references:
        _, lineage_binding, _ = _validated_incident_lineage_and_binding(
            references, allowed_root=allowed_root
        )
        if lineage_binding is None:
            raise B1ArtifactError("incident lineage has no source binding")
        b0 = validated["b0_evidence"]
        if (
            lineage_binding.implementation_commit != validated["implementation_commit"]
            or lineage_binding.source_conformance_sha256
            != validated["source_conformance_sha256"]
            or lineage_binding.configuration_sha256 != validated["configuration_sha256"]
            or lineage_binding.laws_sha256
            != hashlib.sha256(canonical_json_bytes(validated["law_digests"])).hexdigest()
            or lineage_binding.b0_manifest_sha256 != b0["manifest_sha256"]
            or lineage_binding.b0_manifest_bytes != b0["manifest_bytes"]
            or lineage_binding.b0_reviewed_receipt_sha256
            != b0["reviewed_receipt_sha256"]
            or lineage_binding.b0_inventory_sha256 != b0["inventory_sha256"]
            or lineage_binding.b0_file_count != b0["file_count"]
            or lineage_binding.b0_total_bytes != b0["total_bytes"]
        ):
            raise B1ArtifactError("incident lineage source/commit/B0/law binding differs")
    manifest_path = staging / "manifest.json"
    if manifest_path.exists():
        raise B1ArtifactError("B1 staging manifest already exists")
    _write_fsync(manifest_path, canonical_json_bytes(validated) + b"\n")
    for path in staging.rglob("*"):
        if path.is_file() and path != manifest_path:
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
    if directory_size(staging) > B1_OBJECT_DURABLE_CAP_BYTES:
        raise B1ArtifactError("B1 durable bytes exceed the 512 MiB cap")
    _fsync_directory(staging)
    if final.exists():
        raise FileExistsError(f"create-only B1 artifact appeared: {final}")
    os.rename(staging, final)
    _fsync_directory(final.parent)
    return final


def publish_b1_incident(
    *,
    staging: Path | None,
    incident_root: Path,
    allowed_root: Path,
    attempt_id: str,
    category: str,
    detail: str,
    completed_arm_seeds: Sequence[tuple[str, int]],
    test_only: bool = False,
    attempt_ledger: B1AttemptLedger | None = None,
    incident_lineage_witness: B1IncidentLineageWitness | None = None,
) -> Path:
    """Preserve every available byte in one create-only B1 incident bundle."""

    if type(attempt_id) is not str or not attempt_id:
        raise B1ArtifactError("incident attempt_id must be nonempty")
    expected = {(arm, seed) for arm in ARMS for seed in B1_SEEDS}
    completed = list(completed_arm_seeds)
    if len(set(completed)) != len(completed) or any(item not in expected for item in completed):
        raise B1ArtifactError("incident completed arm-seed identities differ")
    if attempt_ledger is None and not test_only:
        raise B1ArtifactError("formal B1 incident requires a canonical attempt ledger")
    if attempt_ledger is not None:
        try:
            validate_b1_attempt_ledger(attempt_ledger)
        except B1ContractError as exc:
            raise B1ArtifactError(f"incident attempt ledger contract failure: {exc}") from exc
        if attempt_ledger.binding.attempt_id != attempt_id:
            raise B1ArtifactError("incident and attempt ledger identities differ")
        ledger_completed = [
            (slot.arm, slot.seed)
            for slot in attempt_ledger.slots
            if slot.status is B1SlotStatus.COMPLETE
        ]
        if ledger_completed != completed:
            raise B1ArtifactError("incident completed slots differ from its attempt ledger")
    if incident_lineage_witness is not None and attempt_ledger is None:
        raise B1ArtifactError("incident ancestor lineage requires a canonical attempt ledger")
    ancestors = [] if incident_lineage_witness is None else materialize_b1_incident_lineage(
        incident_lineage_witness, allowed_root=allowed_root,
        expected_binding=None if attempt_ledger is None else attempt_ledger.binding,
    )
    root = ensure_confined(incident_root, allowed_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{attempt_id}-{uuid.uuid4().hex}"
    if destination.exists():
        raise FileExistsError(f"create-only B1 incident exists: {destination}")
    if staging is None:
        destination.mkdir(mode=0o700)
    else:
        source = ensure_confined(staging, allowed_root)
        if not source.is_dir() or ".partial-" not in source.name:
            raise B1ArtifactError("B1 incident source must be a private partial directory")
        os.rename(source, destination)
    ledger_reference: dict[str, Any] | None = None
    attempt_binding: dict[str, str] | None = None
    if attempt_ledger is not None:
        relative_ledger_path = "attempt-ledger.json"
        ledger_sha256 = publish_b1_attempt_ledger(
            destination / relative_ledger_path,
            attempt_ledger,
            allowed_root=allowed_root,
        )
        attempt_binding = attempt_ledger.binding.as_dict()
        ledger_reference = {
            "relative_path": relative_ledger_path,
            "sha256": ledger_sha256,
            "binding": attempt_binding,
        }
    payload = {
        "schema": B1_TEST_INCIDENT_SCHEMA if test_only else B1_INCIDENT_SCHEMA,
        "test_only": test_only,
        "object_id": OBJECT_ID,
        "run_name": B1_RUN_NAME,
        "attempt_id": attempt_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "detail": detail,
        "completed_arm_seeds": [
            {"arm": arm, "seed": seed} for arm, seed in completed
        ],
        "attempt_binding": attempt_binding,
        "attempt_ledger": ledger_reference,
        "incident_references": ancestors,
        "preserved_evidence_relative_root": ".",
        "scientific_branch": None,
        "scientific_claim": None,
        "scientific_object_consumed": False,
        "decision": DECISION_PENDING,
        "claim_ceiling": "ENGINEERING_INCIDENT_ONLY",
    }
    _write_fsync(destination / "incident.json", canonical_json_bytes(payload) + b"\n")
    _fsync_directory(destination)
    _fsync_directory(root)
    return destination


def load_b1_attempt_ledger_from_incident(
    incident_manifest_path: Path,
    *,
    allowed_root: Path,
) -> B1AttemptLedger:
    """Load resume state only through an incident-bound path/SHA/source reference."""

    incident_path = ensure_confined(incident_manifest_path, allowed_root)
    if incident_path.name != "incident.json" or not incident_path.is_file():
        raise B1ArtifactError("canonical B1 incident manifest is absent")
    incident_bytes = incident_path.read_bytes()
    try:
        incident = json.loads(incident_bytes.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B1ArtifactError("B1 incident bytes are not canonical JSON") from exc
    if canonical_json_bytes(incident) + b"\n" != incident_bytes:
        raise B1ArtifactError("B1 incident bytes are not canonical")
    required_incident_fields = {
        "schema",
        "test_only",
        "object_id",
        "run_name",
        "attempt_id",
        "recorded_at",
        "category",
        "detail",
        "completed_arm_seeds",
        "attempt_binding",
        "attempt_ledger",
        "incident_references",
        "preserved_evidence_relative_root",
        "scientific_branch",
        "scientific_claim",
        "scientific_object_consumed",
        "decision",
        "claim_ceiling",
    }
    if not isinstance(incident, Mapping) or set(incident) != required_incident_fields:
        raise B1ArtifactError("B1 incident manifest fields differ")
    if incident.get("schema") not in {B1_INCIDENT_SCHEMA, B1_TEST_INCIDENT_SCHEMA}:
        raise B1ArtifactError("B1 incident schema differs")
    if (
        incident.get("object_id") != OBJECT_ID
        or incident.get("run_name") != B1_RUN_NAME
        or incident.get("scientific_branch") is not None
        or incident.get("scientific_claim") is not None
        or incident.get("scientific_object_consumed") is not False
        or incident.get("decision") != DECISION_PENDING
        or incident.get("claim_ceiling") != "ENGINEERING_INCIDENT_ONLY"
    ):
        raise B1ArtifactError("B1 incident identity or fail-closed disposition differs")
    reference = incident.get("attempt_ledger")
    raw_binding = incident.get("attempt_binding")
    if not isinstance(reference, Mapping) or set(reference) != {
        "relative_path",
        "sha256",
        "binding",
    }:
        raise B1ArtifactError("B1 incident has no canonical attempt-ledger reference")
    binding = _decode_ledger_binding(raw_binding)
    reference_binding = _decode_ledger_binding(reference["binding"])
    if binding != reference_binding:
        raise B1ArtifactError("B1 incident reference contains cross-source binding")
    if incident.get("attempt_id") != binding.attempt_id:
        raise B1ArtifactError("B1 incident attempt binding differs")
    relative_text = reference["relative_path"]
    if type(relative_text) is not str:
        raise B1ArtifactError("B1 incident ledger relative path differs")
    relative = PurePosixPath(relative_text)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != relative_text
        or relative.suffix != ".json"
    ):
        raise B1ArtifactError("B1 incident ledger relative path is not confined")
    ledger_path = incident_path.parent.joinpath(*relative.parts)
    return load_b1_attempt_ledger(
        ledger_path,
        allowed_root=allowed_root,
        expected_sha256=reference["sha256"],
        expected_binding=binding,
    )


def _validated_incident_lineage_and_binding(
    references: Sequence[Mapping[str, Any]],
    *,
    allowed_root: Path,
    expected_binding: B1LedgerBinding | None = None,
) -> tuple[list[dict[str, Any]], B1LedgerBinding | None, list[bytes]]:
    if not isinstance(references, Sequence) or isinstance(
        references, (str, bytes, bytearray)
    ):
        raise B1ArtifactError("incident ancestor lineage must be an ordered sequence")
    normalized: list[dict[str, Any]] = []
    snapshots: list[bytes] = []
    binding = expected_binding
    seen: set[tuple[str, str]] = set()
    for index, raw_reference in enumerate(references):
        if not isinstance(raw_reference, Mapping) or set(raw_reference) != {
            "attempt_id", "incident_manifest_sha256", "attempt_ledger_sha256",
            "incident_relative_path",
        }:
            raise B1ArtifactError("incident ancestor reference fields differ")
        reference = dict(raw_reference)
        _require_hex("incident ancestor manifest SHA", reference["incident_manifest_sha256"], 64)
        _require_hex("incident ancestor ledger SHA", reference["attempt_ledger_sha256"], 64)
        attempt_id = reference["attempt_id"]
        if type(attempt_id) is not str or not attempt_id or attempt_id.strip() != attempt_id:
            raise B1ArtifactError("incident ancestor attempt_id differs")
        relative_text = reference["incident_relative_path"]
        if type(relative_text) is not str:
            raise B1ArtifactError("incident ancestor path differs")
        relative = PurePosixPath(relative_text)
        if (
            relative.is_absolute() or ".." in relative.parts
            or relative.as_posix() != relative_text or relative.name != "incident.json"
        ):
            raise B1ArtifactError("incident ancestor path is not confined canonical JSON")
        identity = (relative_text, reference["incident_manifest_sha256"])
        if identity in seen:
            raise B1ArtifactError("incident ancestor lineage contains a cycle or duplicate")
        seen.add(identity)
        incident_path = ensure_confined(
            Path(allowed_root).joinpath(*relative.parts), allowed_root
        )
        before = incident_path.read_bytes()
        if hashlib.sha256(before).hexdigest() != reference["incident_manifest_sha256"]:
            raise B1ArtifactError("incident ancestor manifest SHA differs")
        ledger = load_b1_attempt_ledger_from_incident(
            incident_path, allowed_root=allowed_root
        )
        if incident_path.read_bytes() != before:
            raise B1ArtifactError("incident ancestor changed during validation")
        try:
            document = json.loads(before.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B1ArtifactError("incident ancestor bytes are unreadable") from exc
        ledger_sha = hashlib.sha256(
            canonical_json_bytes(ledger.as_dict()) + b"\n"
        ).hexdigest()
        if (
            reference["attempt_id"] != ledger.binding.attempt_id
            or reference["attempt_ledger_sha256"] != ledger_sha
            or document.get("incident_references") != normalized
        ):
            raise B1ArtifactError("incident ancestor order/path/ledger binding differs")
        if binding is None:
            binding = ledger.binding
        elif ledger.binding != binding:
            raise B1ArtifactError("incident ancestor cross-attempt/source binding differs")
        normalized.append(reference)
        snapshots.append(before)
    return normalized, binding, snapshots


def validate_b1_incident_lineage(
    references: Sequence[Mapping[str, Any]], *, allowed_root: Path,
    expected_binding: B1LedgerBinding | None = None,
) -> list[dict[str, Any]]:
    """Reread one ordered immutable incident chain and reject any provenance drift."""

    return _validated_incident_lineage_and_binding(
        references, allowed_root=allowed_root, expected_binding=expected_binding
    )[0]


def make_b1_incident_lineage_witness(
    references: Sequence[Mapping[str, Any]], *, allowed_root: Path,
    expected_binding: B1LedgerBinding | None = None,
) -> B1IncidentLineageWitness:
    normalized, binding, snapshots = _validated_incident_lineage_and_binding(
        references, allowed_root=allowed_root, expected_binding=expected_binding
    )
    return B1IncidentLineageWitness(
        allowed_root=Path(allowed_root).resolve(strict=False),
        canonical_references=tuple(canonical_json_bytes(item) for item in normalized),
        incident_snapshots=tuple(snapshots), binding=binding,
    )


def materialize_b1_incident_lineage(
    witness: B1IncidentLineageWitness, *, allowed_root: Path,
    expected_binding: B1LedgerBinding | None = None,
) -> list[dict[str, Any]]:
    if type(witness) is not B1IncidentLineageWitness:
        raise B1ArtifactError("production incident lineage requires an exact validated witness")
    root = Path(allowed_root).resolve(strict=False)
    if witness.allowed_root != root:
        raise B1ArtifactError("incident witness confined root differs")
    references = [json.loads(item.decode("ascii")) for item in witness.canonical_references]
    normalized, binding, snapshots = _validated_incident_lineage_and_binding(
        references, allowed_root=root,
        expected_binding=expected_binding if expected_binding is not None else witness.binding,
    )
    if tuple(snapshots) != witness.incident_snapshots or binding != witness.binding:
        raise B1ArtifactError("incident witness snapshot/binding changed")
    return normalized


__all__ = [
    "B1ArtifactError",
    "B1IncidentLineageWitness",
    "B1_INCIDENT_SCHEMA",
    "B1_TEST_INCIDENT_SCHEMA",
    "B1_TEST_RESULT_SCHEMA",
    "CLAIM_CEILING",
    "create_b1_staging_directory",
    "load_b1_attempt_ledger",
    "load_b1_attempt_ledger_from_incident",
    "make_b1_incident_lineage_witness",
    "materialize_b1_incident_lineage",
    "publish_b1_attempt_ledger",
    "publish_b1_complete",
    "publish_b1_incident",
    "validate_b1_attempt_ledger_document",
    "validate_b1_incident_lineage",
    "validate_b1_complete_manifest",
]
