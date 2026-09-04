"""Canonical-only production transaction for CBSC-OMRC-B01 metrics evidence.

The public seam accepts an existing attempt staging tree and grouped engine raw
slices.  It accepts no caller tables, models, factories, audit booleans, or
scientific reductions.  Every publication row is rebuilt by the three frozen
producer assemblers before a prospective byte census permits any table write.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .artifact import canonical_json_bytes, ensure_confined
from .b1_artifact import (
    B1IncidentLineageWitness,
    materialize_b1_incident_lineage,
)
from .b0 import ARMS
from .b1_contract import (
    B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
    B1_INNOVATOR_SELECTION_REQUEST_ID,
    B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
    B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
    B1_LITERAL_BINDING_REQUEST_ID,
    B1_LITERAL_BINDING_RESPONSE_SHA256,
    B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
    B1_METRICS_ONLY_REQUEST_ID,
    B1_METRICS_ONLY_RESPONSE_SHA256,
    B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
    B1_OBJECT_DURABLE_CAP_BYTES,
    B1_RESOURCE_CAPS,
    B1_RUN_NAME,
    B1_SLOT_ORDER,
    B1Plan,
)
from .b1_descriptive import (
    B1DescriptiveError,
    compute_b1_descriptive_curves,
    unavailable_descriptive_curves,
    validate_descriptive_curves,
)
from .b1_metrics_artifact import (
    FORMAL_ANALYSIS_BOUND,
    LITERAL_BINDING_SPEC_RELATIVE_PATH,
    MetricsArtifactError,
    TABLE_KEY_FIELDS,
    _build_metrics_only_manifest,
    build_b0_nonpolarity_leaf_index,
    _bind_transaction_reread,
    _materialize_prepared_metrics_subset,
    _publish_metrics_only_complete,
    _start_canonical_transaction,
    build_prospective_artifact_inventory,
    build_complete_artifact_inventory,
    canonicalize_metrics_table_order,
    prepare_metrics_only_tables,
    validate_prospective_output_cap,
)
from .b1_metrics_policy_assembly import (
    aggregate_b1_policy_replay_results,
    assemble_b1_metrics_policy_tables,
    validate_one_slot_policy_packet,
)
from .b1_metrics_rehydrate import rehydrate_b1_metrics
from .b1_metrics_training_assembly import assemble_b1_metrics_training
from .b1_metrics_training_assembly import (
    finalize_audit_table_bindings,
    finalize_audit_pointer_bindings,
    finalize_materialized_raw_facts,
)
from .b1_mechanical import (
    build_mechanical_input_descriptor,
    compute_b1_mechanical,
)
from .b1_policy_records import (
    build_literal_null_manifest_fields,
)
from .b1_policy_replay_worker import (
    POLICY_REPLAY_RESULT_SCHEMA,
    POLICY_REPLAY_TEST_RESULT_SCHEMA,
)
from .b1_mechanical import b0_nonpolarity_record
from .telemetry import validate_telemetry


PRODUCTION_SCHEMA = "cbsc_omrc_b01_b1_metrics_production_v1"
REPO_ROOT = Path(__file__).resolve().parents[4]


class B1MetricsProductionError(RuntimeError):
    """Canonical production inputs, upstream instrumentation, or transaction differ."""


@dataclass(frozen=True)
class B1CanonicalAuthorityWitness:
    allowed_root: Path
    staging_root: Path
    attempt_id: str
    implementation_commit: str
    source_conformance_sha256: str
    source_receipt_bytes: bytes
    b0_root: Path
    b0_evidence_bytes: bytes
    law_digests_bytes: bytes
    staging_inventory: tuple[tuple[str, str, int], ...]
    staging_snapshots: tuple[bytes, ...]


def _canonical_staging_authority_snapshot(
    staging: Path,
) -> tuple[tuple[tuple[str, str, int], ...], tuple[bytes, ...]]:
    paths = sorted(
        {
            *staging.glob("workers/*/slice-*/result.json"),
            *staging.glob("workers/*/slice-*/telemetry.json"),
            *staging.glob("admissions/*.json"),
            *staging.glob("policy-replay/*/admission.json"),
            *staging.glob("policy-replay/*/telemetry.json"),
            *staging.glob("policy-replay/*/result.json"),
            *staging.glob("policy-replay/*/.admission.json.raw-*"),
        },
        key=lambda path: path.relative_to(staging).as_posix(),
    )
    if not paths:
        raise B1MetricsProductionError("canonical staging authority inventory is empty")
    snapshots = tuple(path.read_bytes() for path in paths)
    inventory = tuple(
        (path.relative_to(staging).as_posix(), _digest(payload), len(payload))
        for path, payload in zip(paths, snapshots, strict=True)
    )
    return inventory, snapshots


def make_b1_canonical_authority_witness(
    *, staging_root: Path, allowed_root: Path, attempt_id: str,
    implementation_commit: str, b0_root: Path,
) -> B1CanonicalAuthorityWitness:
    """Create formal authority only by rerunning canonical source/B0/law locators."""

    from .b1 import _law_digests, locate_b0_evidence, verify_source_conformance

    root = Path(allowed_root).resolve(strict=False)
    staging = ensure_confined(Path(staging_root), root).resolve(strict=True)
    # Publication time: HEAD may have advanced under concurrent sessions.
    source = verify_source_conformance(
        implementation_commit, require_head_match=False
    )
    b0 = locate_b0_evidence(Path(b0_root))
    laws = _law_digests(source)
    inventory, snapshots = _canonical_staging_authority_snapshot(staging)
    return B1CanonicalAuthorityWitness(
        allowed_root=root, staging_root=staging, attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source["source_conformance_sha256"],
        source_receipt_bytes=canonical_json_bytes(source),
        b0_root=Path(b0["root"]).resolve(strict=True),
        b0_evidence_bytes=canonical_json_bytes({
            key: b0[key] for key in (
                "manifest_sha256", "manifest_bytes", "reviewed_receipt_sha256",
                "inventory_sha256", "file_count", "total_bytes",
            )
        }),
        law_digests_bytes=canonical_json_bytes(laws),
        staging_inventory=inventory, staging_snapshots=snapshots,
    )


def materialize_b1_canonical_authority_witness(
    witness: B1CanonicalAuthorityWitness, *, staging_root: Path,
    allowed_root: Path, attempt_id: str,
) -> dict[str, Any]:
    if type(witness) is not B1CanonicalAuthorityWitness:
        raise B1MetricsProductionError("formal production requires exact authority witness")
    root = Path(allowed_root).resolve(strict=False)
    staging = ensure_confined(Path(staging_root), root).resolve(strict=True)
    if (
        witness.allowed_root != root or witness.staging_root != staging
        or witness.attempt_id != attempt_id
    ):
        raise B1MetricsProductionError("canonical authority witness root/attempt differs")
    from .b1 import _law_digests, locate_b0_evidence, verify_source_conformance

    source = verify_source_conformance(
        witness.implementation_commit, require_head_match=False
    )
    b0 = locate_b0_evidence(witness.b0_root)
    laws = _law_digests(source)
    inventory, snapshots = _canonical_staging_authority_snapshot(staging)
    b0_six = {key: b0[key] for key in (
        "manifest_sha256", "manifest_bytes", "reviewed_receipt_sha256",
        "inventory_sha256", "file_count", "total_bytes",
    )}
    if (
        source["source_conformance_sha256"] != witness.source_conformance_sha256
        or canonical_json_bytes(source) != witness.source_receipt_bytes
        or canonical_json_bytes(b0_six) != witness.b0_evidence_bytes
        or canonical_json_bytes(laws) != witness.law_digests_bytes
        or inventory != witness.staging_inventory or snapshots != witness.staging_snapshots
    ):
        raise B1MetricsProductionError("canonical source/B0/law/staging authority changed")
    return {
        "implementation_commit": witness.implementation_commit,
        "source_conformance_sha256": witness.source_conformance_sha256,
        "b0_root": witness.b0_root,
        "b0_evidence": b0_six,
        "law_digests": laws,
    }


@dataclass(frozen=True)
class B1PolicyReplaySlotSnapshot:
    original_slot_index: int
    seed: int
    arm: str
    result_relative_path: str
    result_sha256: str
    result_bytes: bytes
    admission_relative_path: str
    admission_sha256: str
    admission_bytes: bytes
    telemetry_relative_path: str
    telemetry_sha256: str
    telemetry_bytes: bytes
    raw_receipt_relative_path: str
    raw_receipt_sha256: str
    raw_receipt_bytes: bytes


@dataclass(frozen=True)
class B1PolicyReplayBatchWitness:
    """Immutable 12-child replay result/admission/telemetry snapshot."""

    allowed_root: Path
    attempt_id: str
    implementation_commit: str
    source_conformance_sha256: str
    literal_binding_spec_sha256: str
    test_only: bool
    slot_order: tuple[tuple[int, str], ...]
    slots: tuple[B1PolicyReplaySlotSnapshot, ...]


def _validate_policy_replay_wrapper(
    value: Mapping[str, Any], *, index: int, attempt_id: str, test_only: bool,
) -> dict[str, Any]:
    seed, arm = B1_SLOT_ORDER[index]
    required = {
        "schema", "test_only", "run_name", "attempt_id", "seed", "arm",
        "original_slot_index", "admission_receipt_sha256", "admission_binding",
        "implementation_commit",
        "source_conformance_sha256", "literal_binding_spec_sha256",
        "checkpoint_inventory", "source_evaluations_sha256", "slot_packet_schema",
        "policy_decisions", "policy_curves", "execution_mode_records",
        "evaluation_join_records", "literal_nulls", "counts", "scientific_branch",
        "scientific_polarity", "promotion_eligible", "b2_extension_trigger",
        "result_body_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise B1MetricsProductionError("policy replay result wrapper fields differ")
    body = {key: value[key] for key in value if key != "result_body_sha256"}
    if _digest(canonical_json_bytes(body)) != value["result_body_sha256"]:
        raise B1MetricsProductionError("policy replay result body digest differs")
    expected_schema = POLICY_REPLAY_TEST_RESULT_SCHEMA if test_only else POLICY_REPLAY_RESULT_SCHEMA
    if (
        value["schema"] != expected_schema or value["test_only"] is not test_only
        or value["run_name"] != B1_RUN_NAME or value["attempt_id"] != attempt_id
        or value["seed"] != seed or value["arm"] != arm
        or value["original_slot_index"] != index
    ):
        raise B1MetricsProductionError("policy replay result identity/order differs")
    admission = value["admission_binding"]
    if (
        not isinstance(admission, Mapping) or set(admission) != {
            "schema", "attempt_id", "run_name", "seed", "arm",
            "implementation_commit", "source_conformance_sha256", "receipt_sha256",
            "available_physical_bytes", "effective_available_bytes",
        }
        or admission["schema"] != "cbsc_omrc_b01_b1_bound_admission_v1"
        or admission["attempt_id"] != attempt_id or admission["run_name"] != B1_RUN_NAME
        or admission["seed"] != seed or admission["arm"] != arm
        or admission["implementation_commit"] != value["implementation_commit"]
        or admission["source_conformance_sha256"] != value["source_conformance_sha256"]
        or admission["receipt_sha256"] != value["admission_receipt_sha256"]
        or type(admission["available_physical_bytes"]) is not int
        or type(admission["effective_available_bytes"]) is not int
        or admission["available_physical_bytes"] < 4 * 1024**3
        or admission["effective_available_bytes"] < 4 * 1024**3
    ):
        raise B1MetricsProductionError("policy replay admission binding differs")
    packet = {
        key: value[key] for key in (
            "test_only", "run_name", "attempt_id", "seed", "arm",
            "original_slot_index", "policy_decisions", "policy_curves",
            "execution_mode_records", "evaluation_join_records", "literal_nulls",
            "scientific_branch", "scientific_polarity", "promotion_eligible",
            "b2_extension_trigger", "counts",
        )
    }
    packet["schema"] = value["slot_packet_schema"]
    try:
        validate_one_slot_policy_packet(
            packet, expected_attempt_id=attempt_id, expected_seed=seed,
            expected_arm=arm, expected_slot_index=index, test_only=test_only,
        )
    except ValueError as exc:
        raise B1MetricsProductionError("policy replay slot packet differs") from exc
    return dict(value)


def make_b1_policy_replay_batch_witness(
    *, staging_root: Path, allowed_root: Path, attempt_id: str,
    implementation_commit: str, source_conformance_sha256: str,
    literal_binding_spec_sha256: str, test_only: bool = False,
) -> B1PolicyReplayBatchWitness:
    indices = (1, 5, 9) if test_only else tuple(range(len(B1_SLOT_ORDER)))
    root = Path(allowed_root).resolve(strict=False)
    staging = ensure_confined(Path(staging_root), root).resolve(strict=True)
    slots: list[B1PolicyReplaySlotSnapshot] = []
    admission_fields = {
        "schema", "attempt_id", "run_name", "arm", "seed",
        "implementation_commit", "source_conformance_sha256", "bound_receipt_path",
        "raw_output_path", "python_executable", "python_sha256", "preflight_script",
        "preflight_script_sha256", "exact_command", "raw_receipt_sha256", "receipt",
    }
    telemetry_fields = {
        "schema", "attempt_id", "run_name", "original_slot_index", "seed", "arm",
        "measurement", "scientific_branch",
    }
    for index in indices:
        seed, arm = B1_SLOT_ORDER[index]
        slot_root = staging / "policy-replay" / f"{index:02d}"
        paths = {
            name: ensure_confined(slot_root / f"{name}.json", root).resolve(strict=True)
            for name in ("result", "admission", "telemetry")
        }
        payload = paths["result"].read_bytes()
        try:
            value = json.loads(payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B1MetricsProductionError("policy replay result is unreadable") from exc
        if canonical_json_bytes(value) + b"\n" != payload:
            raise B1MetricsProductionError("policy replay result is not canonical JSON")
        _validate_policy_replay_wrapper(
            value, index=index, attempt_id=attempt_id, test_only=test_only
        )
        admission_bytes = paths["admission"].read_bytes()
        telemetry_bytes = paths["telemetry"].read_bytes()
        try:
            admission = json.loads(admission_bytes.decode("ascii"))
            telemetry = json.loads(telemetry_bytes.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B1MetricsProductionError("policy replay admission/telemetry is unreadable") from exc
        if (
            canonical_json_bytes(admission) + b"\n" != admission_bytes
            or canonical_json_bytes(telemetry) + b"\n" != telemetry_bytes
            or not isinstance(admission, Mapping) or set(admission) != admission_fields
            or not isinstance(telemetry, Mapping) or set(telemetry) != telemetry_fields
            or admission["schema"] != "cbsc_omrc_b01_b1_bound_admission_v1"
            or admission["attempt_id"] != attempt_id or admission["run_name"] != B1_RUN_NAME
            or admission["seed"] != seed or admission["arm"] != arm
            or admission["implementation_commit"] != implementation_commit
            or admission["source_conformance_sha256"] != source_conformance_sha256
            or telemetry["schema"] != "cbsc_omrc_b01_policy_replay_telemetry_v1"
            or telemetry["attempt_id"] != attempt_id or telemetry["run_name"] != B1_RUN_NAME
            or telemetry["original_slot_index"] != index
            or telemetry["seed"] != seed or telemetry["arm"] != arm
            or telemetry["scientific_branch"] is not None
            or value["admission_receipt_sha256"] != _digest(admission_bytes)
            or value["implementation_commit"] != implementation_commit
            or value["source_conformance_sha256"] != source_conformance_sha256
            or value["literal_binding_spec_sha256"] != literal_binding_spec_sha256
        ):
            raise B1MetricsProductionError("policy replay admission/telemetry/source binding differs")
        try:
            validate_telemetry(telemetry["measurement"], caps=B1_RESOURCE_CAPS)
        except ValueError as exc:
            raise B1MetricsProductionError("policy replay telemetry measurement differs") from exc
        raw_receipt_path = ensure_confined(
            Path(admission["raw_output_path"]), root
        ).resolve(strict=True)
        raw_receipt_bytes = raw_receipt_path.read_bytes()
        if _digest(raw_receipt_bytes) != admission["raw_receipt_sha256"]:
            raise B1MetricsProductionError("policy replay raw receipt binding differs")
        slots.append(B1PolicyReplaySlotSnapshot(
            original_slot_index=index, seed=seed, arm=arm,
            result_relative_path=paths["result"].relative_to(root).as_posix(),
            result_sha256=_digest(payload), result_bytes=payload,
            admission_relative_path=paths["admission"].relative_to(root).as_posix(),
            admission_sha256=_digest(admission_bytes), admission_bytes=admission_bytes,
            telemetry_relative_path=paths["telemetry"].relative_to(root).as_posix(),
            telemetry_sha256=_digest(telemetry_bytes), telemetry_bytes=telemetry_bytes,
            raw_receipt_relative_path=raw_receipt_path.relative_to(root).as_posix(),
            raw_receipt_sha256=_digest(raw_receipt_bytes),
            raw_receipt_bytes=raw_receipt_bytes,
        ))
    return B1PolicyReplayBatchWitness(
        allowed_root=root, attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
        test_only=test_only,
        slot_order=tuple(B1_SLOT_ORDER[index] for index in indices),
        slots=tuple(slots),
    )


def materialize_b1_policy_replay_batch_witness(
    witness: B1PolicyReplayBatchWitness, *, allowed_root: Path, attempt_id: str,
    test_only: bool,
) -> list[dict[str, Any]]:
    if type(witness) is not B1PolicyReplayBatchWitness:
        raise B1MetricsProductionError("formal policy replay requires exact witness type")
    root = Path(allowed_root).resolve(strict=False)
    if (
        witness.allowed_root != root or witness.attempt_id != attempt_id
        or witness.test_only is not test_only
    ):
        raise B1MetricsProductionError("policy replay witness identity differs")
    output: list[dict[str, Any]] = []
    indices = (1, 5, 9) if test_only else tuple(range(len(B1_SLOT_ORDER)))
    if witness.slot_order != tuple(B1_SLOT_ORDER[index] for index in indices):
        raise B1MetricsProductionError("policy replay witness slot order differs")
    for slot, index in zip(witness.slots, indices, strict=True):
        payload = (root / slot.result_relative_path).read_bytes()
        admission = (root / slot.admission_relative_path).read_bytes()
        telemetry = (root / slot.telemetry_relative_path).read_bytes()
        raw_receipt = (root / slot.raw_receipt_relative_path).read_bytes()
        if (
            payload != slot.result_bytes or _digest(payload) != slot.result_sha256
            or admission != slot.admission_bytes or _digest(admission) != slot.admission_sha256
            or telemetry != slot.telemetry_bytes or _digest(telemetry) != slot.telemetry_sha256
            or raw_receipt != slot.raw_receipt_bytes
            or _digest(raw_receipt) != slot.raw_receipt_sha256
        ):
            raise B1MetricsProductionError("policy replay batch changed after validation")
        value = json.loads(payload.decode("ascii"))
        output.append(_validate_policy_replay_wrapper(
            value, index=index, attempt_id=attempt_id, test_only=test_only
        ))
    return output


def _policy_replay_resource_authority(
    witness: B1PolicyReplayBatchWitness, *, allowed_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(allowed_root).resolve(strict=False)
    admissions: list[dict[str, Any]] = []
    telemetry_rows: list[dict[str, Any]] = []
    mechanical: list[dict[str, Any]] = []
    for slot in witness.slots:
        admission = json.loads(slot.admission_bytes.decode("ascii"))
        telemetry = json.loads(slot.telemetry_bytes.decode("ascii"))
        measurement = validate_telemetry(telemetry["measurement"], caps=B1_RESOURCE_CAPS)
        raw_receipt = ensure_confined(Path(admission["raw_output_path"]), root)
        raw_receipt_relative = raw_receipt.relative_to(root).as_posix()
        if (
            not raw_receipt.is_file()
            or raw_receipt_relative != slot.raw_receipt_relative_path
            or _digest(raw_receipt.read_bytes()) != slot.raw_receipt_sha256
            or slot.raw_receipt_sha256 != admission["raw_receipt_sha256"]
        ):
            raise B1MetricsProductionError("policy replay raw admission receipt differs")
        base = {
            "run_order": 0, "invocation_kind": "POLICY_REPLAY",
            "original_slot_index": slot.original_slot_index, "attempt_order": 0,
            "seed": slot.seed, "arm_order": ARMS.index(slot.arm),
            "run_name": B1_RUN_NAME, "arm": slot.arm,
            "attempt_id": witness.attempt_id,
            "slice_start_update": None, "slice_stop_update": None,
        }
        admissions.append({
            **base, "receipt_sha256": slot.admission_sha256,
            "bound_admission_relative_path": slot.admission_relative_path,
            "raw_receipt_relative_path": raw_receipt_relative,
            "raw_receipt_sha256": admission["raw_receipt_sha256"],
            "available_physical_bytes": admission["receipt"]["available_physical_bytes"],
            "effective_available_bytes": admission["receipt"]["effective_available_bytes"],
        })
        telemetry_rows.append({
            **base, "measurement": measurement,
            "telemetry_relative_path": slot.telemetry_relative_path,
            "telemetry_sha256": slot.telemetry_sha256,
        })
        mechanical.append({
            "invocation_id": f"POLICY_REPLAY:{slot.original_slot_index:02d}",
            "physical_available_bytes": admission["receipt"]["available_physical_bytes"],
            "effective_available_bytes": admission["receipt"]["effective_available_bytes"],
            "wall_seconds": measurement["end_to_end_wall_seconds"],
            "peak_rss_bytes": measurement["process_tree_peak_rss_bytes"],
            "scratch_peak_bytes": measurement["scratch_high_water_bytes"],
            "durable_peak_bytes": measurement["durable_high_water_bytes"],
        })
    return admissions, telemetry_rows, mechanical


def stage_pro_decision_evidence(
    *, staging_root: Path, allowed_root: Path,
) -> list[dict[str, Any]]:
    """Snapshot the three fixed Pro decisions and transport companions once."""

    root = ensure_confined(Path(staging_root), Path(allowed_root))
    bindings = (
        (B1_INNOVATOR_SELECTION_REQUEST_ID,
         B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
         B1_INNOVATOR_SELECTION_RESPONSE_SHA256),
        (B1_LITERAL_BINDING_REQUEST_ID, B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
         B1_LITERAL_BINDING_RESPONSE_SHA256),
        (B1_METRICS_ONLY_REQUEST_ID, B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
         B1_METRICS_ONLY_RESPONSE_SHA256),
    )
    inventory: list[dict[str, Any]] = []
    for request_id, response_origin, response_sha in bindings:
        origin_root = REPO_ROOT / Path(response_origin).parent
        destination = root / "evidence" / "pro-decisions" / request_id
        if destination.exists():
            raise FileExistsError("create-only Pro decision evidence root exists")
        destination.mkdir(parents=True)
        for kind, filename in (
            ("RESPONSE", "RESPONSE.md"),
            ("TRANSPORT_FACTS", "TRANSPORT_FACTS.json"),
            ("PACKET_MANIFEST", "PACKET_MANIFEST.json"),
        ):
            source = origin_root / filename
            try:
                payload = source.read_bytes()
            except OSError as exc:
                raise B1MetricsProductionError(
                    f"fixed Pro decision attachment is absent: {request_id}/{filename}"
                ) from exc
            sha = _digest(payload)
            if kind == "RESPONSE" and sha != response_sha:
                raise B1MetricsProductionError("fixed Pro response bytes differ")
            target = destination / filename
            with target.open("xb") as stream:
                stream.write(payload)
            copied = target.read_bytes()
            if copied != payload:
                raise B1MetricsProductionError("copied Pro decision bytes differ")
            inventory.append({
                "request_id": request_id, "kind": kind,
                "origin_relative_path": source.relative_to(REPO_ROOT).as_posix(),
                "artifact_relative_path": target.relative_to(root).as_posix(),
                "sha256": sha, "byte_count": len(payload),
            })
    return inventory


def _b0_record_is_indexed(relative: str) -> bool:
    """The only reviewed-B0 files whose CONTENT the nonpolarity index reads.

    ``_b0_leaf_rows`` indexes exactly ``manifest.json`` and
    ``workers/**/result.json``; every other file yields no leaf rows, so parsing
    it here never affected the published index.  The reviewed B0 root also
    legitimately contains the preflight's raw receipt siblings
    (``.<name>.raw-<hex>.json``), which ``scripts/hmasd_resource_preflight.py``
    writes pretty-printed with ``indent=2`` and which are therefore never
    canonical JSON.  Requiring canonical bytes of every ``.json`` file refused
    every formal B1 publication against that root, with "B0 worker result bytes
    are not canonical JSON", although the offending files carry no indexed
    content.  Their bytes remain fully covered by the byte_count / sha256 /
    copied_inventory_sha256 checks above, which are unchanged.
    """

    return relative == "manifest.json" or (
        relative.startswith("workers/") and relative.endswith("/result.json")
    )


def stage_reviewed_b0_evidence(
    *, source_root: Path, staging_root: Path,
    expected: Mapping[str, Any], allowed_root: Path, test_only: bool,
) -> dict[str, Any]:
    """Copy and index the exact reviewed B0 root without interpreting outcomes."""

    source = Path(source_root).resolve(strict=True)
    staging = ensure_confined(Path(staging_root), Path(allowed_root))
    destination = staging / "b0-reviewed-evidence"
    index_root = staging / "b0-reviewed-index"
    if destination.exists() or index_root.exists():
        raise FileExistsError("create-only B0 reviewed evidence/index exists")
    files = sorted(
        (path for path in source.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source).as_posix(),
    )
    snapshots = [
        (path, path.relative_to(source), path.read_bytes()) for path in files
    ]
    inventory = [
        {
            "path": relative.as_posix(),
            "byte_count": len(payload),
            "sha256": _digest(payload),
        }
        for _, relative, payload in snapshots
    ]
    inventory_sha = _digest(canonical_json_bytes(inventory))
    total_bytes = sum(row["byte_count"] for row in inventory)
    manifest = source / "manifest.json"
    manifest_payload = next(
        (payload for path, _, payload in snapshots if path == manifest), None
    )
    if (
        manifest_payload is None
        or _digest(manifest_payload) != expected.get("manifest_sha256")
        or len(manifest_payload) != expected.get("manifest_bytes")
        or inventory_sha != expected.get("inventory_sha256")
        or len(files) != expected.get("file_count")
        or total_bytes != expected.get("total_bytes")
    ):
        raise B1MetricsProductionError("reviewed B0 manifest/inventory authority differs")
    if not test_only and (len(files), total_bytes) != (33, 12_807_274):
        raise B1MetricsProductionError("formal reviewed B0 root differs from r02 authority")
    destination.mkdir(parents=True)
    for path, relative, payload in snapshots:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(payload)
    copied_inventory = [{
        "path": path.relative_to(destination).as_posix(),
        "byte_count": len(path.read_bytes()),
        "sha256": _digest(path.read_bytes()),
    } for path in sorted(
        (path for path in destination.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(destination).as_posix(),
    )]
    if copied_inventory != inventory or _digest(
        canonical_json_bytes(copied_inventory)
    ) != inventory_sha:
        raise B1MetricsProductionError("copied reviewed B0 inventory differs")
    json_records: dict[str, Mapping[str, Any]] = {}
    for _, relative_path, payload in snapshots:
        relative = relative_path.as_posix()
        if not _b0_record_is_indexed(relative):
            continue
        try:
            value = json.loads(payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B1MetricsProductionError("B0 worker result is unreadable") from exc
        if not isinstance(value, Mapping) or canonical_json_bytes(value) + b"\n" != payload:
            raise B1MetricsProductionError("B0 worker result bytes are not canonical JSON")
        json_records[relative] = value
    try:
        evaluator_leaves = build_b0_nonpolarity_leaf_index(json_records)
    except MetricsArtifactError as exc:
        raise B1MetricsProductionError(str(exc)) from exc
    index_root.mkdir(parents=True)
    index = {
        "schema": "cbsc_omrc_b01_b0_nonpolarity_index_v1",
        "nonpolarity": b0_nonpolarity_record(),
        "evaluator_leaves": evaluator_leaves,
    }
    index_path = index_root / "nonpolarity-index.json"
    _write_payload = canonical_json_bytes(index) + b"\n"
    with index_path.open("xb") as stream:
        stream.write(_write_payload)
    return {
        **dict(expected),
        "relative_root": "b0-reviewed-evidence",
        "copied_inventory_sha256": inventory_sha,
        "nonpolarity_index": {
            "relative_path": "b0-reviewed-index/nonpolarity-index.json",
            "sha256": _digest(_write_payload),
            "byte_count": len(_write_payload),
            "leaf_count": len(evaluator_leaves),
        },
    }


def _digest_record(
    *, name: str, expected_sha256: str, expected_byte_count: int, path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise B1MetricsProductionError(f"materialized evidence is absent: {name}")
    payload = path.read_bytes()
    return {
        "name": name,
        "expected_sha256": expected_sha256,
        "actual_sha256": _digest(payload),
        "expected_byte_count": expected_byte_count,
        "actual_byte_count": len(payload),
    }


def reread_materialized_digest_records(
    root: Path,
    *,
    table_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Reread table, whole-artifact and checkpoint bytes after materialization."""

    base = Path(root).resolve(strict=True)
    tables = [
        _digest_record(
            name=row["table"], expected_sha256=row["sha256"],
            expected_byte_count=row["byte_count"],
            path=base / row["relative_path"],
        )
        for row in table_inventory
    ]
    artifacts = [
        _digest_record(
            name=row["relative_path"], expected_sha256=row["sha256"],
            expected_byte_count=row["byte_count"],
            path=base / row["relative_path"],
        )
        for row in artifact_inventory
    ]
    checkpoints = [
        row for row in artifacts if row["name"].endswith(".pt")
    ]
    if not tables or not artifacts or not checkpoints:
        raise B1MetricsProductionError(
            "materialized table/artifact/checkpoint reread inventory is incomplete"
        )
    return {"tables": tables, "artifacts": artifacts, "checkpoints": checkpoints}


def _materialized_audit_authority_records(
    root: Path, *, audit_rows: Sequence[Mapping[str, Any]],
    table_inventory: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    descriptors = {row["table"]: row for row in table_inventory}
    output: list[dict[str, Any]] = []
    for audit in audit_rows:
        if audit.get("authority_type") != "CANONICAL_TABLE_AUTHORITY":
            continue
        table = audit["source_table"]
        descriptor = descriptors.get(table)
        if descriptor is None or table == "audits":
            raise B1MetricsProductionError("audit authority source table descriptor is absent")
        path = Path(root) / descriptor["relative_path"]
        if not path.is_file():
            raise B1MetricsProductionError("audit authority source table is absent after stage one")
        payload = path.read_bytes()
        try:
            rows = [json.loads(line.decode("ascii")) for line in payload.splitlines()]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B1MetricsProductionError("audit authority table reread is unreadable") from exc
        key_fields = audit["source_key_range"]["key_fields"]
        if not rows or any(
            not isinstance(row, Mapping) or any(field not in row for field in key_fields)
            for row in rows
        ):
            raise B1MetricsProductionError("audit authority table reread is empty")
        output.append({
            "source_table": table,
            "actual_sha256": _digest(payload),
            "actual_row_count": len(rows),
            "actual_first_key": [rows[0][field] for field in key_fields],
            "actual_last_key": [rows[-1][field] for field in key_fields],
        })
    return output


def _reload_materialized_table(root: Path, descriptor: Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = (Path(root) / descriptor["relative_path"]).read_bytes()
    try:
        rows = [json.loads(line.decode("ascii")) for line in payload.splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B1MetricsProductionError("materialized metrics table is unreadable") from exc
    if any(canonical_json_bytes(row) + b"\n" not in payload for row in rows):
        raise B1MetricsProductionError("materialized metrics table row is noncanonical")
    return rows


def _reload_raw_source_groups(
    root: Path, raw_source_groups: Sequence[Sequence[Mapping[str, Any]]],
) -> list[list[dict[str, Any]]]:
    output: list[list[dict[str, Any]]] = []
    for source_group in raw_source_groups:
        group: list[dict[str, Any]] = []
        for source in source_group:
            wrapper = _load_json(
                Path(root) / source["source_relative_path"], "materialized worker result"
            )
            raw = wrapper.get("raw_evidence")
            if not isinstance(raw, Mapping):
                raise B1MetricsProductionError("materialized worker raw_evidence is absent")
            group.append(dict(raw))
        output.append(group)
    return output


def _json_pointer_value(value: object, pointer: str) -> object:
    if type(pointer) is not str or not pointer.startswith("/"):
        raise B1MetricsProductionError("mechanical evidence JSON pointer differs")
    current = value
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if part not in current:
                raise B1MetricsProductionError("mechanical evidence JSON pointer is absent")
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError) as exc:
                raise B1MetricsProductionError(
                    "mechanical evidence JSON pointer index differs"
                ) from exc
        else:
            raise B1MetricsProductionError("mechanical evidence JSON pointer crosses a scalar")
    return current


def _resolve_descriptor_source(root: Path, source: Mapping[str, Any]) -> object:
    if not isinstance(source, Mapping) or set(source) != {
        "source_relative_path", "source_file_sha256", "json_pointer"
    }:
        raise B1MetricsProductionError("mechanical evidence source fields differ")
    relative = source["source_relative_path"]
    if type(relative) is not str:
        raise B1MetricsProductionError("mechanical evidence source path differs")
    base = Path(root).resolve(strict=True)
    path = (base / relative).resolve(strict=True)
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise B1MetricsProductionError("mechanical evidence source escapes artifact") from exc
    payload = path.read_bytes()
    if _digest(payload) != source["source_file_sha256"]:
        raise B1MetricsProductionError("mechanical evidence source SHA differs")
    try:
        document = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B1MetricsProductionError("mechanical evidence source is unreadable") from exc
    if canonical_json_bytes(document) + b"\n" != payload:
        raise B1MetricsProductionError("mechanical evidence source is noncanonical")
    return _json_pointer_value(document, source["json_pointer"])


def _table_bindings(inventory: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "table": row["table"],
            "sha256": row["sha256"],
            "row_count": row["row_count"],
            "byte_count": row["byte_count"],
        }
        for row in inventory
    ]


def _descriptor_worker_sources(
    raw_source_groups: Sequence[Sequence[Mapping[str, Any]]],
) -> list[list[dict[str, str]]]:
    return [
        [
            {
                "source_relative_path": source["source_relative_path"],
                "source_file_sha256": source["source_file_sha256"],
                "json_pointer": source["raw_json_pointer"],
            }
            for source in group
        ]
        for group in raw_source_groups
    ]


def _policy_mode_sources(
    staging: Path,
    *,
    policy_replay_witness: B1PolicyReplayBatchWitness | None,
    execution_mode_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Bind non-table execution-mode facts to canonical in-artifact JSON pointers."""

    if policy_replay_witness is not None:
        sources: list[dict[str, str]] = []
        staging_root = Path(staging).resolve(strict=True)
        for slot in policy_replay_witness.slots:
            source = (
                policy_replay_witness.allowed_root / slot.result_relative_path
            ).resolve(strict=True)
            try:
                relative = source.relative_to(staging_root).as_posix()
            except ValueError as exc:
                raise B1MetricsProductionError(
                    "policy execution-mode source lies outside artifact staging"
                ) from exc
            sources.append({
                "source_relative_path": relative,
                "source_file_sha256": slot.result_sha256,
                "json_pointer": "/execution_mode_records",
            })
        return sources
    relative = "mechanical-inputs/test-only-policy-execution-modes.json"
    path = Path(staging) / relative
    payload = canonical_json_bytes(
        {
            "schema": "cbsc_omrc_b01_test_only_policy_execution_modes_v1",
            "execution_mode_records": list(execution_mode_records),
        }
    ) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
    return [{
        "source_relative_path": relative,
        "source_file_sha256": _digest(payload),
        "json_pointer": "/execution_mode_records",
    }]


def _group_table_invocations(
    raw_groups: Sequence[Sequence[Mapping[str, Any]]],
    *,
    resource_rows: Sequence[Mapping[str, Any]],
    telemetry_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    admissions: list[list[dict[str, Any]]] = []
    telemetry: list[list[dict[str, Any]]] = []
    for group in raw_groups:
        slot_admissions: list[dict[str, Any]] = []
        slot_telemetry: list[dict[str, Any]] = []
        for attempt_order, raw in enumerate(group):
            seed, arm = raw["seed"], raw["arm"]
            arm_order = ARMS.index(arm)
            admission_matches = [
                row for row in resource_rows
                if row.get("invocation_kind") == "TRAINING_SLICE"
                and row.get("seed") == seed and row.get("arm_order") == arm_order
                and row.get("attempt_order") == attempt_order
            ]
            telemetry_matches = [
                row for row in telemetry_rows
                if row.get("invocation_kind") == "TRAINING_SLICE"
                and row.get("seed") == seed and row.get("arm_order") == arm_order
                and row.get("attempt_order") == attempt_order
            ]
            if len(admission_matches) != 1 or len(telemetry_matches) != 1:
                raise B1MetricsProductionError(
                    "mechanical training invocation table identity differs"
                )
            admission = admission_matches[0]
            measured = telemetry_matches[0]
            slot_admissions.append({
                "attempt_order": attempt_order,
                "attempt_id": raw["attempt_id"],
                "run_name": raw["run_name"],
                "seed": seed,
                "arm": arm,
                "receipt_sha256": admission["receipt_sha256"],
                "available_physical_bytes": admission["available_physical_bytes"],
                "effective_available_bytes": admission["effective_available_bytes"],
            })
            slot_telemetry.append({
                "attempt_order": attempt_order,
                "attempt_id": raw["attempt_id"],
                "run_name": raw["run_name"],
                "seed": seed,
                "arm": arm,
                "measurement": measured["measurement"],
            })
        admissions.append(slot_admissions)
        telemetry.append(slot_telemetry)
    return admissions, telemetry


def _policy_replay_tables_as_resources(
    resource_rows: Sequence[Mapping[str, Any]],
    telemetry_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, object] | None:
    admissions = [dict(row) for row in resource_rows if row.get("invocation_kind") == "POLICY_REPLAY"]
    telemetry = [dict(row) for row in telemetry_rows if row.get("invocation_kind") == "POLICY_REPLAY"]
    if not admissions and not telemetry:
        return None
    if len(admissions) != len(telemetry):
        raise B1MetricsProductionError("policy replay resource table coverage differs")
    return {"resource_admissions": admissions, "telemetry": telemetry}


def _require_reconstructed_rows(
    name: str,
    reconstructed: Sequence[Mapping[str, Any]],
    published: Sequence[Mapping[str, Any]],
) -> None:
    """Reject semantic drift even when both file/inventory hashes were refreshed."""

    if canonical_json_bytes(list(reconstructed)) != canonical_json_bytes(list(published)):
        raise B1MetricsProductionError(
            f"{name} differs from independently reopened evidence"
        )


def _require_raw_manifest_identity(
    raw: Mapping[str, Any], source_identity: Mapping[str, Any]
) -> None:
    bindings = raw.get("full_bindings")
    if (
        raw.get("attempt_id") != source_identity.get("attempt_id")
        or not isinstance(bindings, Mapping)
        or bindings.get("implementation_commit")
        != source_identity.get("implementation_commit")
        or bindings.get("source_conformance_sha256")
        != source_identity.get("source_conformance_sha256")
    ):
        raise B1MetricsProductionError(
            "mechanical raw worker differs from manifest source identity"
        )


def _require_checkpoint_manifest_identity(
    binding: Mapping[str, Any],
    raw: Mapping[str, Any],
    record: Mapping[str, Any],
    source_identity: Mapping[str, Any],
) -> None:
    if (
        binding != record.get("binding")
        or binding.get("attempt_id") != source_identity.get("attempt_id")
        or binding.get("implementation_commit")
        != source_identity.get("implementation_commit")
        or binding.get("source_conformance_sha256")
        != source_identity.get("source_conformance_sha256")
        or binding.get("seed") != raw.get("seed")
        or binding.get("arm") != raw.get("arm")
        or binding.get("completed_rollout_updates") != record.get("update")
    ):
        raise B1MetricsProductionError(
            "checkpoint envelope differs from raw/manifest identity"
        )


def _validate_relocated_training_admission(
    admission_path: Path,
    bound: Mapping[str, Any],
    *,
    attempt_id: str,
    arm: str,
    seed: int,
    implementation_commit: str,
    source_conformance_sha256: str,
) -> dict[str, Any]:
    """Validate a bound admission after staging-root atomic rename.

    Historical absolute paths remain provenance, while their basenames and
    internal command relationship identify the relocated in-artifact files.
    """

    from .b0 import validate_memory_receipt
    from .b1 import validate_bound_admission

    try:
        validated = validate_bound_admission(
            bound,
            expected_attempt_id=attempt_id,
            expected_arm=arm,
            expected_seed=seed,
            expected_commit=implementation_commit,
            expected_receipt_path=None,
        )
    except ValueError as exc:
        raise B1MetricsProductionError(
            "training admission reconstruction failed"
        ) from exc
    if (
        Path(validated["bound_receipt_path"]).name != admission_path.name
        or validated["source_conformance_sha256"] != source_conformance_sha256
    ):
        raise B1MetricsProductionError(
            "training admission differs from relocated/manifest identity"
        )
    relocated_raw = admission_path.parent / Path(validated["raw_output_path"]).name
    if (
        not relocated_raw.is_file()
        or _digest(relocated_raw.read_bytes()) != validated["raw_receipt_sha256"]
    ):
        raise B1MetricsProductionError("relocated training raw admission bytes differ")
    try:
        raw = json.loads(relocated_raw.read_text(encoding="utf-8"))
        parsed = validate_memory_receipt(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise B1MetricsProductionError(
            "relocated training raw admission is unreadable"
        ) from exc
    if parsed != validated["receipt"]:
        raise B1MetricsProductionError("relocated training parsed admission differs")
    return validated


def reconstruct_b1_mechanical_from_artifact(
    *,
    root: Path,
    descriptor: Mapping[str, Any],
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    table_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]],
    source_identity: Mapping[str, Any],
    test_only: bool,
) -> dict[str, Any]:
    """Consumer-side rebuild from bound bytes, checkpoints, replay facts and audits."""

    if descriptor.get("authority") != "BOUND_ARTIFACT_EVIDENCE":
        raise B1MetricsProductionError("published mechanical descriptor lacks artifact authority")
    if descriptor.get("test_only") is not test_only:
        raise B1MetricsProductionError("mechanical descriptor TEST/formal identity differs")
    attempt_id = source_identity.get("attempt_id")
    implementation_commit = source_identity.get("implementation_commit")
    source_conformance_sha256 = source_identity.get("source_conformance_sha256")
    if (
        type(attempt_id) is not str or not attempt_id
        or type(implementation_commit) is not str or len(implementation_commit) != 40
        or type(source_conformance_sha256) is not str
        or len(source_conformance_sha256) != 64
    ):
        raise B1MetricsProductionError("mechanical consumer source identity differs")
    expected_bindings = _table_bindings(table_inventory)
    if descriptor.get("table_bindings") != expected_bindings:
        raise B1MetricsProductionError("mechanical descriptor table bindings differ")
    if descriptor.get("artifact_inventory_sha256") != _digest(
        canonical_json_bytes(list(artifact_inventory))
    ):
        raise B1MetricsProductionError("mechanical descriptor artifact inventory differs")

    raw_groups: list[list[dict[str, Any]]] = []
    raw_source_groups: list[list[dict[str, str]]] = []
    source_groups = descriptor.get("raw_worker_sources")
    indices = descriptor.get("training_slot_indices")
    if not isinstance(source_groups, list) or not isinstance(indices, list):
        raise B1MetricsProductionError("mechanical worker descriptor inventory differs")
    for sources in source_groups:
        group: list[dict[str, Any]] = []
        provenance: list[dict[str, str]] = []
        for source in sources:
            raw = _resolve_descriptor_source(root, source)
            if not isinstance(raw, Mapping):
                raise B1MetricsProductionError("mechanical raw worker pointer is not a record")
            _require_raw_manifest_identity(raw, source_identity)
            group.append(dict(raw))
            provenance.append({
                "source_relative_path": source["source_relative_path"],
                "source_file_sha256": source["source_file_sha256"],
                "raw_json_pointer": source["json_pointer"],
            })
        raw_groups.append(group)
        raw_source_groups.append(provenance)
    expected_identities = [B1_SLOT_ORDER[index] for index in indices]
    observed_identities = [(group[0].get("seed"), group[0].get("arm")) for group in raw_groups]
    if observed_identities != expected_identities:
        raise B1MetricsProductionError("mechanical raw worker slot identity differs")

    # Reopen the canonical training admission/telemetry/result paths rather
    # than trusting their table copies.  This also rebinds source file SHA and
    # attempt/seed/arm identity to the descriptor.
    admissions, telemetry, reopened_sources = _direct_invocation_groups(
        Path(root), raw_groups, indices
    )
    if _descriptor_worker_sources(reopened_sources) != source_groups:
        raise B1MetricsProductionError(
            "mechanical raw worker descriptor differs from reopened invocation sources"
        )
    if not test_only:
        for index, group in zip(indices, raw_groups, strict=True):
            seed, arm = B1_SLOT_ORDER[index]
            tag = f"{index:02d}-seed-{seed}-{arm}"
            for raw in group:
                interval = raw["slice"]
                invocation = (
                    f"slice-{interval['start_update']:02d}-{interval['stop_update']:02d}"
                )
                admission_path = (
                    Path(root) / "admissions" / f"{tag}-{invocation}-admission.json"
                ).resolve(strict=True)
                bound = _load_json(admission_path, "consumer training bound admission")
                _validate_relocated_training_admission(
                    admission_path,
                    bound,
                    attempt_id=attempt_id,
                    arm=arm,
                    seed=seed,
                    implementation_commit=implementation_commit,
                    source_conformance_sha256=source_conformance_sha256,
                )

    # Bind every actual checkpoint envelope and byte digest to the raw worker
    # record and the validated manifest identity.
    from .b1_engine import load_b1_checkpoint

    for group, sources in zip(raw_groups, source_groups, strict=True):
        for raw, source in zip(group, sources, strict=True):
            records = raw.get("checkpoints_created")
            if not isinstance(records, list):
                raise B1MetricsProductionError("raw checkpoint inventory is absent")
            for record in records:
                if not isinstance(record, Mapping):
                    raise B1MetricsProductionError("raw checkpoint record differs")
                matches = [
                    item for item in artifact_inventory
                    if Path(item["relative_path"]).name == record.get("relative_path")
                    and item.get("sha256") == record.get("sha256")
                    and item.get("byte_count") == record.get("byte_count")
                ]
                if len(matches) != 1:
                    raise B1MetricsProductionError(
                        "checkpoint artifact identity is absent or ambiguous"
                    )
                path = (Path(root) / matches[0]["relative_path"]).resolve(strict=True)
                payload = path.read_bytes()
                if (
                    _digest(payload) != record.get("sha256")
                    or len(payload) != record.get("byte_count")
                ):
                    raise B1MetricsProductionError(
                        "checkpoint bytes differ from raw worker record"
                    )
                envelope = load_b1_checkpoint(path)
                binding = envelope["binding"]
                _require_checkpoint_manifest_identity(
                    binding, raw, record, source_identity
                )

    modes: list[Mapping[str, Any]] = []
    reopened_replay_admissions: list[dict[str, Any]] = []
    reopened_replay_telemetry: list[dict[str, Any]] = []
    mode_sources = descriptor.get("policy_execution_mode_sources")
    if not isinstance(mode_sources, list) or not mode_sources:
        raise B1MetricsProductionError("mechanical policy mode sources are absent")
    for source in mode_sources:
        value = _resolve_descriptor_source(root, source)
        if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
            raise B1MetricsProductionError("mechanical policy mode pointer differs")
        modes.extend(value)

        relative = source["source_relative_path"]
        if relative.startswith("policy-replay/"):
            result_path = Path(root) / relative
            wrapper = _load_json(result_path, "consumer policy replay result")
            index = wrapper.get("original_slot_index")
            if type(index) is not int:
                raise B1MetricsProductionError("policy replay source slot differs")
            _validate_policy_replay_wrapper(
                wrapper, index=index, attempt_id=attempt_id, test_only=test_only
            )
            if (
                wrapper.get("implementation_commit") != implementation_commit
                or wrapper.get("source_conformance_sha256")
                != source_conformance_sha256
            ):
                raise B1MetricsProductionError(
                    "policy replay wrapper differs from manifest source identity"
                )
            slot_root = result_path.parent
            admission_doc = _load_json(
                slot_root / "admission.json", "consumer policy replay admission"
            )
            telemetry_doc = _load_json(
                slot_root / "telemetry.json", "consumer policy replay telemetry"
            )
            validated_policy_admission = _validate_relocated_training_admission(
                slot_root / "admission.json",
                admission_doc,
                attempt_id=attempt_id,
                arm=wrapper["arm"],
                seed=wrapper["seed"],
                implementation_commit=implementation_commit,
                source_conformance_sha256=source_conformance_sha256,
            )
            telemetry_fields = {
                "schema", "attempt_id", "run_name", "original_slot_index",
                "seed", "arm", "measurement", "scientific_branch",
            }
            if set(telemetry_doc) != telemetry_fields:
                raise B1MetricsProductionError(
                    "policy replay telemetry companion fields differ"
                )
            resource_matches = [
                row for row in tables["resource_admissions"]
                if row.get("invocation_kind") == "POLICY_REPLAY"
                and row.get("original_slot_index") == index
            ]
            telemetry_matches = [
                row for row in tables["telemetry"]
                if row.get("invocation_kind") == "POLICY_REPLAY"
                and row.get("original_slot_index") == index
            ]
            if len(resource_matches) != 1 or len(telemetry_matches) != 1:
                raise B1MetricsProductionError("policy replay resource table identity differs")
            resource_row, telemetry_row = resource_matches[0], telemetry_matches[0]
            raw_receipt = Path(root) / resource_row["raw_receipt_relative_path"]
            try:
                from .b0 import validate_memory_receipt

                parsed_raw_receipt = json.loads(raw_receipt.read_text(encoding="utf-8"))
                parsed_receipt = validate_memory_receipt(parsed_raw_receipt)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise B1MetricsProductionError(
                    "policy replay raw admission receipt is unreadable"
                ) from exc
            if (
                telemetry_doc.get("schema")
                != "cbsc_omrc_b01_policy_replay_telemetry_v1"
                or telemetry_doc.get("attempt_id") != attempt_id
                or telemetry_doc.get("run_name") != B1_RUN_NAME
                or telemetry_doc.get("original_slot_index") != index
                or telemetry_doc.get("seed") != wrapper.get("seed")
                or telemetry_doc.get("arm") != wrapper.get("arm")
                or telemetry_doc.get("scientific_branch") is not None
                or resource_row.get("attempt_id") != attempt_id
                or telemetry_row.get("attempt_id") != attempt_id
                or resource_row.get("bound_admission_relative_path")
                != (slot_root / "admission.json").relative_to(Path(root)).as_posix()
                or resource_row.get("receipt_sha256") != _digest(
                    (slot_root / "admission.json").read_bytes()
                )
                or wrapper.get("admission_receipt_sha256")
                != _digest((slot_root / "admission.json").read_bytes())
                or telemetry_row.get("telemetry_relative_path")
                != (slot_root / "telemetry.json").relative_to(Path(root)).as_posix()
                or telemetry_row.get("telemetry_sha256") != _digest(
                    (slot_root / "telemetry.json").read_bytes()
                )
                or telemetry_row.get("measurement") != telemetry_doc.get("measurement")
                or not raw_receipt.is_file()
                or _digest(raw_receipt.read_bytes()) != resource_row.get("raw_receipt_sha256")
                or resource_row.get("raw_receipt_sha256")
                != admission_doc.get("raw_receipt_sha256")
                or parsed_receipt != validated_policy_admission.get("receipt")
                or resource_row.get("available_physical_bytes")
                != parsed_receipt["available_physical_bytes"]
                or resource_row.get("effective_available_bytes")
                != parsed_receipt["effective_available_bytes"]
            ):
                raise B1MetricsProductionError(
                    "policy replay admission/telemetry/raw receipt binding differs"
                )
            base = {
                "run_order": 0,
                "invocation_kind": "POLICY_REPLAY",
                "original_slot_index": index,
                "attempt_order": 0,
                "seed": wrapper["seed"],
                "arm_order": ARMS.index(wrapper["arm"]),
                "run_name": B1_RUN_NAME,
                "arm": wrapper["arm"],
                "attempt_id": attempt_id,
                "slice_start_update": None,
                "slice_stop_update": None,
            }
            reopened_replay_admissions.append({
                **base,
                "receipt_sha256": _digest((slot_root / "admission.json").read_bytes()),
                "bound_admission_relative_path": (
                    slot_root / "admission.json"
                ).relative_to(Path(root)).as_posix(),
                "raw_receipt_relative_path": raw_receipt.relative_to(Path(root)).as_posix(),
                "raw_receipt_sha256": _digest(raw_receipt.read_bytes()),
                "available_physical_bytes": parsed_receipt["available_physical_bytes"],
                "effective_available_bytes": parsed_receipt["effective_available_bytes"],
            })
            reopened_replay_telemetry.append({
                **base,
                "measurement": telemetry_doc["measurement"],
                "telemetry_relative_path": (
                    slot_root / "telemetry.json"
                ).relative_to(Path(root)).as_posix(),
                "telemetry_sha256": _digest((slot_root / "telemetry.json").read_bytes()),
            })
    policy_resources = (
        {
            "resource_admissions": reopened_replay_admissions,
            "telemetry": reopened_replay_telemetry,
        }
        if reopened_replay_admissions
        else _policy_replay_tables_as_resources(
            tables["resource_admissions"], tables["telemetry"]
        )
    )
    truth_rows = list(tables["evaluator_decision_truth"])
    if test_only:
        truth_rows = [
            row for row in truth_rows
            if row["split_order"] in (1, 2) and row["tape_id"] == 0
        ]
    training = assemble_b1_metrics_training(
        raw_slice_groups=raw_groups,
        admission_groups=admissions,
        telemetry_groups=telemetry,
        shared_tables={
            "evaluator_decision_truth": truth_rows,
            "motif_twin_index": list(tables["motif_twin_index"]),
        },
        policy_tables={
            "policy_decisions": list(tables["policy_decisions"]),
            "per_tape_curves": list(tables["per_tape_curves"]),
            "policy_support_signature_counts": list(
                tables["policy_support_signature_counts"]
            ),
            "execution_mode_records": list(modes),
        },
        raw_source_groups=raw_source_groups,
        policy_replay_resources=policy_resources,
        test_only=test_only,
    )
    _require_reconstructed_rows(
        "resource_admissions",
        training["tables"]["resource_admissions"],
        tables["resource_admissions"],
    )
    _require_reconstructed_rows(
        "telemetry", training["tables"]["telemetry"], tables["telemetry"]
    )
    if canonical_json_bytes(training["tables"]["raw_competence"]) != canonical_json_bytes(
        tables["raw_competence"]
    ):
        raise B1MetricsProductionError(
            "raw_competence JSONL differs from consumer reconstruction"
        )
    recomputed_audits = finalize_audit_pointer_bindings(
        training["tables"]["audits"], Path(root)
    )
    authorities = _materialized_audit_authority_records(
        Path(root), audit_rows=recomputed_audits, table_inventory=table_inventory
    )
    audit_tables = {
        name: (
            finalize_audit_table_bindings(recomputed_audits, authorities)
            if name == "audits" else list(tables[name])
        )
        for name in TABLE_KEY_FIELDS
    }
    recomputed_audits = canonicalize_metrics_table_order(audit_tables)["audits"]
    if canonical_json_bytes(recomputed_audits) != canonical_json_bytes(tables["audits"]):
        raise B1MetricsProductionError("typed audit table differs from consumer reconstruction")

    reread = reread_materialized_digest_records(
        Path(root), table_inventory=table_inventory,
        artifact_inventory=artifact_inventory,
    )
    facts = finalize_materialized_raw_facts(
        training["prepublication_raw_facts"],
        table_digest_records=reread["tables"],
        artifact_digest_records=reread["artifacts"],
        checkpoint_digest_records=reread["checkpoints"],
    )
    return compute_b1_mechanical(
        facts, training["raw_competence_inputs"], input_descriptor=descriptor
    )


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_hex(name: str, value: object, length: int) -> str:
    if (
        type(value) is not str or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1MetricsProductionError(f"{name} must be lowercase hexadecimal")
    return value


def _attempt_id(groups: Sequence[Sequence[Mapping[str, Any]]]) -> str:
    values = {
        raw.get("attempt_id")
        for group in groups
        for raw in group
        if isinstance(raw, Mapping)
    }
    if len(values) != 1:
        raise B1MetricsProductionError("canonical raw groups do not bind one attempt_id")
    value = next(iter(values))
    if type(value) is not str or not value:
        raise B1MetricsProductionError("canonical attempt_id is absent")
    return value


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload.decode("ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B1MetricsProductionError(f"{label} is unreadable") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) + b"\n" != payload:
        raise B1MetricsProductionError(f"{label} bytes are not canonical JSON")
    return value


def _direct_invocation_groups(
    staging: Path,
    groups: Sequence[Sequence[Mapping[str, Any]]],
    slot_indices: Sequence[int],
) -> tuple[
    list[list[dict[str, Any]]], list[list[dict[str, Any]]],
    list[list[dict[str, str]]],
]:
    """Read exact admission and telemetry bytes for the same raw slice intervals."""

    admissions: list[list[dict[str, Any]]] = []
    telemetry: list[list[dict[str, Any]]] = []
    sources: list[list[dict[str, str]]] = []
    attempt = _attempt_id(groups)
    if len(groups) != len(slot_indices):
        raise B1MetricsProductionError("direct invocation group/index inventory differs")
    for index, group in zip(slot_indices, groups, strict=True):
        seed, arm = B1_SLOT_ORDER[index]
        tag = f"{index:02d}-seed-{seed}-{arm}"
        slot_admissions: list[dict[str, Any]] = []
        slot_telemetry: list[dict[str, Any]] = []
        slot_sources: list[dict[str, str]] = []
        for attempt_order, raw in enumerate(group):
            interval = raw.get("slice")
            if not isinstance(interval, Mapping):
                raise B1MetricsProductionError("raw slice interval is absent")
            invocation = f"slice-{interval.get('start_update'):02d}-{interval.get('stop_update'):02d}"
            admission_path = staging / "admissions" / f"{tag}-{invocation}-admission.json"
            telemetry_path = staging / "workers" / tag / invocation / "telemetry.json"
            result_path = staging / "workers" / tag / invocation / "result.json"
            bound = _load_json(admission_path, "bound admission")
            measurement = _load_json(telemetry_path, "direct telemetry")
            result_wrapper = _load_json(result_path, "direct worker result")
            receipt = bound.get("receipt")
            if (
                bound.get("attempt_id") != attempt
                or bound.get("run_name") != B1_RUN_NAME
                or bound.get("seed") != seed
                or bound.get("arm") != arm
                or not isinstance(receipt, Mapping)
            ):
                raise B1MetricsProductionError("bound admission identity differs")
            if result_wrapper.get("raw_evidence") != raw:
                raise B1MetricsProductionError("direct worker result/raw evidence differs")
            slot_admissions.append({
                "attempt_order": attempt_order,
                "attempt_id": attempt, "run_name": B1_RUN_NAME,
                "seed": seed, "arm": arm,
                "receipt_sha256": _digest(admission_path.read_bytes()),
                "available_physical_bytes": receipt.get("available_physical_bytes"),
                "effective_available_bytes": receipt.get("effective_available_bytes"),
            })
            slot_telemetry.append({
                "attempt_order": attempt_order,
                "attempt_id": attempt, "run_name": B1_RUN_NAME,
                "seed": seed, "arm": arm, "measurement": dict(measurement),
            })
            slot_sources.append({
                "source_relative_path": result_path.relative_to(staging).as_posix(),
                "source_file_sha256": _digest(result_path.read_bytes()),
                "raw_json_pointer": "/raw_evidence",
            })
        admissions.append(slot_admissions)
        telemetry.append(slot_telemetry)
        sources.append(slot_sources)
    return admissions, telemetry, sources


def _source_identity(
    *, attempt_id: str, implementation_commit: str,
    source_conformance_sha256: str,
    decision_evidence_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    literal = REPO_ROOT / LITERAL_BINDING_SPEC_RELATIVE_PATH
    metrics = REPO_ROOT / B1_METRICS_ONLY_SPEC_RELATIVE_PATH
    if not literal.is_file() or not metrics.is_file():
        raise B1MetricsProductionError("bound .02/.03 specification file is absent")
    return {
        "attempt_id": attempt_id,
        "implementation_commit": _require_hex(
            "implementation_commit", implementation_commit, 40
        ),
        "source_conformance_sha256": _require_hex(
            "source_conformance_sha256", source_conformance_sha256, 64
        ),
        "configuration_sha256": _digest(canonical_json_bytes(B1Plan().as_dict())),
        "literal_binding_spec_path": LITERAL_BINDING_SPEC_RELATIVE_PATH,
        "literal_binding_spec_sha256": _digest(literal.read_bytes()),
        "literal_binding_response_sha256": B1_LITERAL_BINDING_RESPONSE_SHA256,
        "innovator_selection_request_id": B1_INNOVATOR_SELECTION_REQUEST_ID,
        "innovator_selection_archive_path": B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
        "innovator_selection_response_sha256": B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
        "literal_binding_request_id": B1_LITERAL_BINDING_REQUEST_ID,
        "literal_binding_archive_path": B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
        "metrics_only_request_id": B1_METRICS_ONLY_REQUEST_ID,
        "metrics_only_archive_path": B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
        "decision_evidence_inventory": [
            dict(row) for row in decision_evidence_inventory
        ],
        "metrics_only_spec_path": B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
        "metrics_only_spec_sha256": _digest(metrics.read_bytes()),
        "metrics_only_response_sha256": B1_METRICS_ONLY_RESPONSE_SHA256,
    }


def _assemble_and_publish_b1_metrics(
    *,
    staging_root: Path,
    final_path: Path,
    grouped_raw_slices: Sequence[Sequence[Mapping[str, Any]]],
    implementation_commit: str,
    source_conformance_sha256: str,
    b0_root: Path,
    b0_evidence: Mapping[str, Any],
    law_digests: Mapping[str, str],
    incident_lineage_witness: B1IncidentLineageWitness,
    policy_replay_witness: B1PolicyReplayBatchWitness | None = None,
    allowed_root: Path,
    test_only: bool = False,
) -> Path:
    """Rebuild all 15 tables and publish one create-only transaction."""

    if type(test_only) is not bool:
        raise B1MetricsProductionError("test_only must be literal bool")
    # Section-11 recast (owner decision 3, 2026-09-02): the former
    # `if not FORMAL_ANALYSIS_BOUND: raise B1MetricsProductionError(
    #     "REPAIR_REQUIRED: formal metrics publication awaits whole-pipeline
    #      CLEAN review")`
    # is removed here.  The flag is published in the manifest's
    # `formal_analysis_record` with `gating: false` instead.
    try:
        incident_references = materialize_b1_incident_lineage(
            incident_lineage_witness, allowed_root=allowed_root
        )
    except (TypeError, ValueError) as exc:
        raise B1MetricsProductionError(
            "production incident lineage requires a validated immutable witness"
        ) from exc
    root = ensure_confined(Path(staging_root), Path(allowed_root))
    final = ensure_confined(Path(final_path), Path(allowed_root))
    if not root.is_dir() or final.exists():
        raise B1MetricsProductionError("canonical staging/final create-only boundary differs")
    groups = tuple(tuple(group) for group in grouped_raw_slices)
    attempt = _attempt_id(groups)
    decision_evidence = stage_pro_decision_evidence(
        staging_root=root, allowed_root=allowed_root
    )
    identity = _source_identity(
        attempt_id=attempt,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        decision_evidence_inventory=decision_evidence,
    )
    transaction = _start_canonical_transaction(identity)
    materialized_b0 = stage_reviewed_b0_evidence(
        source_root=b0_root, staging_root=root, expected=b0_evidence,
        allowed_root=allowed_root, test_only=test_only,
    )
    rehydrated = rehydrate_b1_metrics(
        groups,
        attempt_id=attempt,
        literal_binding_spec_sha256=identity["literal_binding_spec_sha256"],
    )
    policy_indices = (1, 5, 9) if test_only else tuple(range(len(groups)))
    policy_tapes = tuple(
        tape for tape in rehydrated.unique_tapes
        if tape.identity.seed in {B1_SLOT_ORDER[index][0] for index in policy_indices}
        and tape.identity.split in ("EVAL_STOCHASTIC", "EVAL_MOTIF")
        and (not test_only or tape.identity.episode_id == 0)
    )
    replay_admissions: list[dict[str, Any]] = []
    replay_telemetry: list[dict[str, Any]] = []
    if policy_replay_witness is None:
        if not test_only:
            raise B1MetricsProductionError(
                "formal policy tables require 12 admitted child replay outputs"
            )
        policy_groups = tuple(groups[index] for index in policy_indices)
        policy_packet = assemble_b1_metrics_policy_tables(
            staging_root=root,
            grouped_raw_slices=policy_groups,
            heldout_tapes=policy_tapes,
            expected_attempt_id=attempt,
            expected_implementation_commit=implementation_commit,
            expected_source_conformance_sha256=source_conformance_sha256,
            literal_binding_spec_sha256=identity["literal_binding_spec_sha256"],
            test_only=True,
        )
    else:
        replay = materialize_b1_policy_replay_batch_witness(
            policy_replay_witness, allowed_root=allowed_root,
            attempt_id=attempt, test_only=test_only,
        )
        (
            replay_admissions, replay_telemetry, _,
        ) = _policy_replay_resource_authority(
            policy_replay_witness, allowed_root=allowed_root
        )
        try:
            policy_packet = aggregate_b1_policy_replay_results(
                replay, heldout_tapes=policy_tapes,
                expected_attempt_id=attempt,
                expected_implementation_commit=implementation_commit,
                expected_source_conformance_sha256=source_conformance_sha256,
                literal_binding_spec_sha256=identity["literal_binding_spec_sha256"],
                test_only=test_only,
            )
        except ValueError as exc:
            raise B1MetricsProductionError(
                "policy replay batch aggregation differs"
            ) from exc
    policy_tables = {
        "policy_decisions": policy_packet["policy_decisions"],
        "per_tape_curves": policy_packet["policy_curves"],
        "policy_support_signature_counts": policy_packet[
            "policy_support_signature_counts"
        ],
        "execution_mode_records": policy_packet["execution_mode_records"],
    }
    policy_mode_sources = _policy_mode_sources(
        root,
        policy_replay_witness=policy_replay_witness,
        execution_mode_records=policy_tables["execution_mode_records"],
    )
    training_indices = (0,) if test_only else tuple(range(len(groups)))
    training_groups = tuple(groups[index] for index in training_indices)
    admission_groups, telemetry_groups, raw_source_groups = _direct_invocation_groups(
        root, training_groups, training_indices
    )
    training_shared = rehydrated.canonical_shared_tables
    if test_only:
        training_shared = dict(training_shared)
        training_shared["evaluator_decision_truth"] = [
            row for row in training_shared["evaluator_decision_truth"]
            if row["split_order"] in (1, 2) and row["tape_id"] == 0
        ]
    training_packet = assemble_b1_metrics_training(
        raw_slice_groups=training_groups,
        admission_groups=admission_groups,
        telemetry_groups=telemetry_groups,
        shared_tables=training_shared,
        policy_tables=policy_tables,
        raw_source_groups=raw_source_groups,
        policy_replay_resources={
            "resource_admissions": replay_admissions,
            "telemetry": replay_telemetry,
        } if replay_admissions else None,
        test_only=test_only,
    )
    shared = rehydrated.canonical_shared_tables
    training = training_packet["tables"]
    training["audits"] = finalize_audit_pointer_bindings(
        training["audits"], root
    )
    tables = {
        "tape_transitions": shared["tape_transitions"],
        # The audit authority for this table is built from ``training_shared``,
        # which the test-only profile narrows to two splits of tape 0.
        # Publishing the unnarrowed table while auditing the narrowed one made
        # the two disagree, so finalize_audit_table_bindings refused with
        # "materialized table reread binding differs: evaluator_decision_truth".
        # In the formal profile training_shared IS shared, so this is a no-op.
        "evaluator_decision_truth": training_shared["evaluator_decision_truth"],
        "policy_decisions": policy_tables["policy_decisions"],
        "per_tape_curves": policy_tables["per_tape_curves"],
        "motif_twin_index": shared["motif_twin_index"],
        "support_signature_counts": shared["support_signature_counts"],
        "policy_support_signature_counts": policy_tables[
            "policy_support_signature_counts"
        ],
        "motif_pair_support_counts": shared["motif_pair_support_counts"],
        **training,
    }
    if list(tables) != list(TABLE_KEY_FIELDS):
        raise B1MetricsProductionError("canonical 15-table order differs")
    tables = canonicalize_metrics_table_order(tables)
    invocation_keys = [
        (
            "TRAINING_SLICE", B1_SLOT_ORDER.index((raw["seed"], raw["arm"])),
            raw["seed"], ARMS.index(raw["arm"]), attempt_order,
            raw["slice"]["start_update"], raw["slice"]["stop_update"],
        )
        for group in groups
        for attempt_order, raw in enumerate(group)
    ] + [
        ("POLICY_REPLAY", row["original_slot_index"], row["seed"], row["arm_order"],
         0, None, None)
        for row in replay_admissions
    ]
    preliminary = prepare_metrics_only_tables(
        tables, allow_test_only=test_only,
        formal_invocation_keys=None if test_only else invocation_keys,
        # The audits table is not materialized from this pass, and its rows
        # cannot be bound until the authority tables below have been reread.
        allow_pending_audits=True,
        _transaction_witness=None if test_only else transaction,
    )
    authority_table_names = tuple(name for name in TABLE_KEY_FIELDS if name != "audits")
    _materialize_prepared_metrics_subset(
        root, preliminary, table_names=authority_table_names,
        allowed_root=allowed_root,
        _transaction_witness=None if test_only else transaction,
    )
    materialized_authorities = _materialized_audit_authority_records(
        root, audit_rows=tables["audits"], table_inventory=preliminary.inventory,
    )
    try:
        tables["audits"] = finalize_audit_table_bindings(
            tables["audits"], materialized_authorities
        )
    except ValueError as exc:
        raise B1MetricsProductionError(
            "typed audit materialized-table binding failed"
        ) from exc
    tables = canonicalize_metrics_table_order(tables)
    prepared = prepare_metrics_only_tables(
        tables, allow_test_only=test_only,
        formal_invocation_keys=None if test_only else invocation_keys,
        _transaction_witness=None if test_only else transaction,
    )
    preliminary_payloads = dict(preliminary.payloads)
    final_payloads = dict(prepared.payloads)
    if any(
        preliminary_payloads[f"metrics/raw/{name}.jsonl"]
        != final_payloads[f"metrics/raw/{name}.jsonl"]
        for name in authority_table_names
    ):
        raise B1MetricsProductionError("authority table bytes changed during audit finalization")
    prospective_inventory = build_prospective_artifact_inventory(
        root, prepared, allow_existing_equal=True
    )
    prospective_bytes = sum(row["byte_count"] for row in prospective_inventory)
    if prospective_bytes + 4 * 1024**2 > B1_OBJECT_DURABLE_CAP_BYTES:
        raise B1MetricsProductionError(
            "prospective artifact plus fixed manifest upper exceeds 512 MiB"
        )
    _materialize_prepared_metrics_subset(
        root, prepared, table_names=("audits",), allowed_root=allowed_root,
        _transaction_witness=None if test_only else transaction,
    )
    reread = reread_materialized_digest_records(
        root,
        table_inventory=prepared.inventory,
        artifact_inventory=prospective_inventory,
    )
    if not test_only:
        _bind_transaction_reread(
            transaction, prepared_inventory=prepared.inventory,
            artifact_inventory=prospective_inventory, reread=reread,
        )
    finalized_facts = finalize_materialized_raw_facts(
        training_packet["prepublication_raw_facts"],
        table_digest_records=reread["tables"],
        artifact_digest_records=reread["artifacts"],
        checkpoint_digest_records=reread["checkpoints"],
    )
    input_descriptor = build_mechanical_input_descriptor(
        finalized_facts,
        training_packet["raw_competence_inputs"],
        authority="BOUND_ARTIFACT_EVIDENCE",
        test_only=test_only,
        training_slot_indices=training_indices,
        raw_worker_sources=_descriptor_worker_sources(raw_source_groups),
        policy_execution_mode_sources=policy_mode_sources,
        table_bindings=_table_bindings(prepared.inventory),
        artifact_inventory_sha256=_digest(
            canonical_json_bytes(prospective_inventory)
        ),
    )
    candidate_mechanical = compute_b1_mechanical(
        finalized_facts,
        training_packet["raw_competence_inputs"],
        input_descriptor=input_descriptor,
    )
    materialized = {
        row["table"]: _reload_materialized_table(root, row)
        for row in prepared.inventory
    }
    reloaded_groups = _reload_raw_source_groups(root, raw_source_groups)
    reread_admissions, reread_telemetry, reread_sources = _direct_invocation_groups(
        root, reloaded_groups, training_indices
    )
    reread_shared = {
        "evaluator_decision_truth": materialized["evaluator_decision_truth"],
        "motif_twin_index": materialized["motif_twin_index"],
    }
    if test_only:
        reread_shared["evaluator_decision_truth"] = [
            row for row in reread_shared["evaluator_decision_truth"]
            if row["split_order"] in (1, 2) and row["tape_id"] == 0
        ]
    recomputed_training = assemble_b1_metrics_training(
        raw_slice_groups=reloaded_groups,
        admission_groups=reread_admissions, telemetry_groups=reread_telemetry,
        shared_tables=reread_shared,
        policy_tables={
            "policy_decisions": materialized["policy_decisions"],
            "per_tape_curves": materialized["per_tape_curves"],
            "policy_support_signature_counts": materialized[
                "policy_support_signature_counts"
            ],
            "execution_mode_records": policy_tables["execution_mode_records"],
        },
        raw_source_groups=reread_sources, test_only=test_only,
        policy_replay_resources={
            "resource_admissions": replay_admissions,
            "telemetry": replay_telemetry,
        } if replay_admissions else None,
    )
    recomputed_facts = finalize_materialized_raw_facts(
        recomputed_training["prepublication_raw_facts"],
        table_digest_records=reread["tables"],
        artifact_digest_records=reread["artifacts"],
        checkpoint_digest_records=reread["checkpoints"],
    )
    final_mechanical = compute_b1_mechanical(
        recomputed_facts,
        recomputed_training["raw_competence_inputs"],
        input_descriptor=input_descriptor,
    )
    if canonical_json_bytes(final_mechanical) != canonical_json_bytes(candidate_mechanical):
        raise B1MetricsProductionError(
            "materialized raw/table mechanical recomputation differs"
        )
    if final_mechanical["mechanical_components"]["publication_digests"] is not True:
        raise B1MetricsProductionError(
            "materialized publication digest reread failed; final rename refused"
        )
    if not test_only and (
        final_mechanical["mechanical_conformance_pass"] is not True
        or final_mechanical["scientific_packet_readable"] is not True
    ):
        raise B1MetricsProductionError(
            "formal final mechanical conformance/readability failed"
        )
    actual_inventory = build_complete_artifact_inventory(root)
    try:
        descriptive = validate_descriptive_curves(compute_b1_descriptive_curves(
            per_tape_curves=materialized["per_tape_curves"],
            policy_decisions=materialized["policy_decisions"],
            training_episodes=materialized["training_episodes"],
            optimizer_steps=materialized["optimizer_steps"],
            raw_competence=materialized["raw_competence"],
        ))
    except (B1DescriptiveError, KeyError, TypeError, ValueError) as exc:
        # Decision 7 (2026-09-02): a summary that cannot be produced is recorded
        # with its reason; it never annuls or quarantines the attempt.
        descriptive = unavailable_descriptive_curves(str(exc))
    manifest = _build_metrics_only_manifest(
        identity=identity,
        b0_evidence=materialized_b0,
        law_digests=law_digests,
        table_inventory=prepared.inventory,
        artifact_inventory=actual_inventory,
        literal_nulls=build_literal_null_manifest_fields(),
        mechanical=final_mechanical,
        incident_references=incident_references,
        descriptive_curves=descriptive,
        test_only=test_only,
        _transaction_witness=None if test_only else transaction,
    )
    validate_prospective_output_cap(
        artifact_inventory=actual_inventory, manifest=manifest
    )
    return _publish_metrics_only_complete(
        staging=root, final_path=final, manifest=manifest,
        allowed_root=allowed_root, allow_test_only=test_only,
        _transaction_witness=None if test_only else transaction,
    )


def assemble_and_publish_b1_metrics(
    *, staging_root: Path, final_path: Path,
    grouped_raw_slices: Sequence[Sequence[Mapping[str, Any]]],
    authority_witness: B1CanonicalAuthorityWitness,
    incident_lineage_witness: B1IncidentLineageWitness,
    policy_replay_witness: B1PolicyReplayBatchWitness,
    allowed_root: Path,
) -> Path:
    """The sole public formal entry; ordinary source/B0/law values are not accepted.

    Section-11 recast (owner decision 3, 2026-09-02): the former
    ``FORMAL_ANALYSIS_BOUND`` refusal that stood here is removed; the flag is a
    recorded manifest field.
    """

    groups = tuple(tuple(group) for group in grouped_raw_slices)
    attempt = _attempt_id(groups)
    authority = materialize_b1_canonical_authority_witness(
        authority_witness, staging_root=staging_root,
        allowed_root=allowed_root, attempt_id=attempt,
    )
    return _assemble_and_publish_b1_metrics(
        staging_root=staging_root, final_path=final_path,
        grouped_raw_slices=groups,
        implementation_commit=authority["implementation_commit"],
        source_conformance_sha256=authority["source_conformance_sha256"],
        b0_root=authority["b0_root"], b0_evidence=authority["b0_evidence"],
        law_digests=authority["law_digests"],
        incident_lineage_witness=incident_lineage_witness,
        policy_replay_witness=policy_replay_witness,
        allowed_root=allowed_root, test_only=False,
    )


def assemble_and_publish_b1_metrics_test_only(
    *, staging_root: Path, final_path: Path,
    grouped_raw_slices: Sequence[Sequence[Mapping[str, Any]]],
    implementation_commit: str, source_conformance_sha256: str,
    b0_root: Path, b0_evidence: Mapping[str, Any], law_digests: Mapping[str, str],
    incident_lineage_witness: B1IncidentLineageWitness,
    allowed_root: Path,
    policy_replay_witness: B1PolicyReplayBatchWitness | None = None,
) -> Path:
    """Explicit TEST_ONLY integration profile; physically cannot publish formal schema."""

    return _assemble_and_publish_b1_metrics(
        staging_root=staging_root, final_path=final_path,
        grouped_raw_slices=grouped_raw_slices,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        b0_root=b0_root, b0_evidence=b0_evidence, law_digests=law_digests,
        incident_lineage_witness=incident_lineage_witness,
        policy_replay_witness=policy_replay_witness,
        allowed_root=allowed_root, test_only=True,
    )


__all__ = [
    "B1CanonicalAuthorityWitness", "B1MetricsProductionError",
    "B1PolicyReplayBatchWitness", "B1PolicyReplaySlotSnapshot", "PRODUCTION_SCHEMA",
    "assemble_and_publish_b1_metrics", "assemble_and_publish_b1_metrics_test_only",
    "make_b1_canonical_authority_witness", "make_b1_policy_replay_batch_witness",
]
