"""Artifact-bound CM acceptance gate between A/RECON review and RUN-01."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import fields
from pathlib import Path
from typing import Mapping

from .assessment import ASSESS_ID, ASSESS_SCHEMA
from .contracts import RESOURCE_CAPS
from .orchestration import atomic_create_bytes
from .resources import ResourceTelemetry
from .source_identity import compute_source_identity_bytes, validate_source_identity_bytes


READINESS_SCHEMA = "SCDMP_MF_RS_MK_B01_A_R2_PERFORMANCE_READINESS_V1"
REVIEW_SCHEMA = "SCDMP_MF_RS_MK_B01_A_R2_CM_PERFORMANCE_REVIEW_V1"
_RECEIPT_KEYS = {
    "schema", "status", "assessment_id", "assessment_root", "source_identity_sha256",
    "source_identity", "assessment_binding", "telemetry_binding", "inventory_binding",
    "review_binding", "resource_caps", "projection",
}
_REVIEW_KEYS = {
    "schema", "review_disposition", "review_evidence_id", "reviewer_identity",
    "assessment_id", "assessment_root", "scientific_polarity",
}


class PerformanceReadinessError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _read_canonical(path: Path, *, label: str) -> tuple[bytes, dict[str, object]]:
    try:
        direct = path.read_bytes()
        value = json.loads(direct)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PerformanceReadinessError(f"{label} is unavailable or unreadable") from error
    if not isinstance(value, dict) or direct != _canonical(value):
        raise PerformanceReadinessError(f"{label} is not canonical JSON")
    return direct, value


def _binding(path: Path, direct: bytes) -> dict[str, object]:
    return {
        "resolved_path": str(path.resolve(strict=True)),
        "byte_size": len(direct),
        "sha256": hashlib.sha256(direct).hexdigest(),
    }


def _finite_projection(projection: object, *, caps: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(projection, dict):
        raise PerformanceReadinessError("A/RECON projection is missing")
    for key in (
        "conservative_projected_total_seconds", "margin_to_1800_seconds",
        "projected_work_seconds", "fixed_overhead_seconds",
    ):
        value = projection.get(key)
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise PerformanceReadinessError("A/RECON projection contains a nonfinite domain")
    wall = caps.get("wall_seconds")
    if (
        isinstance(wall, bool) or not isinstance(wall, (int, float))
        or not math.isfinite(float(wall)) or float(wall) <= 0
        or float(projection["conservative_projected_total_seconds"]) > float(wall)
        or not math.isclose(
            float(projection["margin_to_1800_seconds"]),
            float(wall) - float(projection["conservative_projected_total_seconds"]),
            rel_tol=0.0, abs_tol=1e-9,
        )
        or not math.isclose(
            float(projection["conservative_projected_total_seconds"]),
            float(projection["projected_work_seconds"])
            + float(projection["fixed_overhead_seconds"]),
            rel_tol=0.0, abs_tol=1e-9,
        )
    ):
        raise PerformanceReadinessError("A/RECON projection does not fit the frozen wall cap")
    return projection


def _validate_caps(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "peak_rss_bytes", "scratch_bytes", "durable_bytes", "wall_seconds",
    }:
        raise PerformanceReadinessError("A/RECON resource caps differ")
    for key, row in value.items():
        if (
            isinstance(row, bool) or not isinstance(row, (int, float))
            or not math.isfinite(float(row)) or float(row) <= 0
            or (key != "wall_seconds" and not isinstance(row, int))
        ):
            raise PerformanceReadinessError("A/RECON resource cap domain differs")
    if value != RESOURCE_CAPS:
        raise PerformanceReadinessError("A/RECON resource caps are not the exact frozen caps")
    return value


def _inventory_binding(root: Path, preview_direct: bytes, preview: dict[str, object]) -> dict[str, object]:
    inventory = preview.get("inventory")
    if (
        preview.get("schema") != ASSESS_SCHEMA
        or preview.get("source_identity_file") != "source-identity.json"
        or preview.get("checkpoint_files") != 322
        or preview.get("scientific_polarity") is not None
        or preview.get("ordered_branch") is not None
        or not isinstance(inventory, list) or len(inventory) != 322
    ):
        raise PerformanceReadinessError("A/RECON inventory preview differs")
    checkpoint_root = root / "technical-checkpoints"
    measured = []
    total = 0
    for index, row in enumerate(inventory):
        seed = 1709 if index < 161 else 2903
        coordinate = index % 161
        relative = f"{seed}/coordinate-{coordinate:03d}.json"
        if (
            not isinstance(row, dict) or set(row) != {"relative_path", "direct_size_bytes"}
            or row.get("relative_path") != relative
            or isinstance(row.get("direct_size_bytes"), bool)
            or not isinstance(row.get("direct_size_bytes"), int)
            or row["direct_size_bytes"] < 1
        ):
            raise PerformanceReadinessError("A/RECON inventory coordinate differs")
        path = checkpoint_root / relative
        try:
            direct = path.read_bytes()
        except OSError as error:
            raise PerformanceReadinessError("A/RECON inventory artifact is unavailable") from error
        if len(direct) != row["direct_size_bytes"]:
            raise PerformanceReadinessError("A/RECON inventory artifact size differs")
        total += len(direct)
        measured.append({
            "relative_path": relative, "direct_size_bytes": len(direct),
            "sha256": hashlib.sha256(direct).hexdigest(),
        })
    if preview.get("checkpoint_direct_bytes") != total:
        raise PerformanceReadinessError("A/RECON inventory byte summary differs")
    return {
        **_binding(root / "technical-publication-preview.json", preview_direct),
        "checkpoint_files": 322,
        "checkpoint_direct_bytes": total,
        "inventory_sha256": hashlib.sha256(_canonical(measured)).hexdigest(),
    }


def _validate_telemetry(
    *, telemetry_direct: bytes, telemetry: dict[str, object],
    assessment_direct: bytes, assessment: dict[str, object], caps: Mapping[str, object],
) -> None:
    measured = telemetry.get("telemetry")
    accounting = telemetry.get("final_tail_accounting")
    expected_telemetry_keys = {field.name for field in fields(ResourceTelemetry)}
    if (
        set(telemetry) != {"schema", "telemetry", "final_tail_accounting"}
        or telemetry.get("schema") != "SCDMP_MF_RS_MK_B01_A_RESOURCE_V1"
        or not isinstance(measured, dict) or set(measured) != expected_telemetry_keys
        or measured.get("passed") is not True
        or measured.get("failure_reasons") != [] or measured.get("exit_status") != 0
    ):
        raise PerformanceReadinessError("A/RECON telemetry did not pass its canonical schema")
    for key in ("sample_count", "process_tree_peak_rss_bytes", "scratch_high_water_bytes",
                "durable_high_water_bytes"):
        value = measured.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PerformanceReadinessError("A/RECON telemetry count/resource domain differs")
    for key in ("wall_seconds", "cpu_seconds"):
        value = measured.get(key)
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value)) or float(value) <= 0
        ):
            raise PerformanceReadinessError("A/RECON telemetry work duration is zero or nonfinite")
    if (
        measured["sample_count"] <= 0
        or measured["process_tree_peak_rss_bytes"] > caps["peak_rss_bytes"]
        or measured["scratch_high_water_bytes"] > caps["scratch_bytes"]
        or measured["durable_high_water_bytes"] > caps["durable_bytes"]
        or float(measured["wall_seconds"]) > float(caps["wall_seconds"])
    ):
        raise PerformanceReadinessError("A/RECON telemetry exceeds a frozen cap or lacks samples")
    incidents = measured.get("measurement_incidents")
    incident_keys = {
        "severity", "disposition", "exception_class", "phase", "path_summary",
        "errno", "winerror",
    }
    if not isinstance(incidents, list):
        raise PerformanceReadinessError("A/RECON measurement incident inventory differs")
    for incident in incidents:
        if (
            not isinstance(incident, dict) or set(incident) != incident_keys
            or incident.get("severity") != "TOLERATED"
            or not all(isinstance(incident.get(key), str) and incident[key]
                       for key in ("disposition", "exception_class", "phase", "path_summary"))
            or any(value is not None and (isinstance(value, bool) or not isinstance(value, int))
                   for value in (incident.get("errno"), incident.get("winerror")))
        ):
            raise PerformanceReadinessError("A/RECON contains a fatal or malformed measurement incident")
    accounting_keys = {
        "prepublication_durable_bytes", "telemetry_exact_bytes", "assessment_exact_bytes",
        "exact_tail_bytes", "predicted_final_durable_bytes", "durable_cap_bytes",
    }
    if (
        not isinstance(accounting, dict) or set(accounting) != accounting_keys
        or assessment.get("final_tail_accounting") != accounting
        or accounting.get("telemetry_exact_bytes") != len(telemetry_direct)
        or accounting.get("assessment_exact_bytes") != len(assessment_direct)
        or accounting.get("exact_tail_bytes") != len(telemetry_direct) + len(assessment_direct)
        or accounting.get("predicted_final_durable_bytes") != (
            accounting.get("prepublication_durable_bytes", -1)
            + len(telemetry_direct) + len(assessment_direct)
        )
        or accounting.get("durable_cap_bytes") != caps["durable_bytes"]
        or accounting.get("predicted_final_durable_bytes", caps["durable_bytes"] + 1)
        > caps["durable_bytes"]
    ):
        raise PerformanceReadinessError("A/RECON final-tail accounting differs from direct artifacts")


def _evidence_value(root: Path, review_path: Path) -> dict[str, object]:
    try:
        root = root.resolve(strict=True)
    except Exception as error:
        raise PerformanceReadinessError("A/RECON assessment root is unavailable") from error
    manifest_direct, manifest = _read_canonical(root / "manifest.json", label="A/RECON manifest")
    if (
        manifest.get("schema") != ASSESS_SCHEMA
        or manifest.get("assessment_id") != ASSESS_ID
        or manifest.get("resolved_assess_root") != str(root)
    ):
        raise PerformanceReadinessError("A/RECON manifest binding differs")
    caps = _validate_caps(manifest.get("resource_caps"))

    try:
        current_source = compute_source_identity_bytes()
        persisted_source = (root / "source-identity.json").read_bytes()
        source_value = validate_source_identity_bytes(persisted_source, current_source)
    except Exception as error:
        raise PerformanceReadinessError("A/RECON source identity differs from current source") from error

    assessment_direct, assessment = _read_canonical(
        root / "assessment.json", label="A/RECON assessment",
    )
    if (
        assessment.get("schema") != ASSESS_SCHEMA
        or assessment.get("assessment_id") != ASSESS_ID
        or assessment.get("status") != "PERFORMANCE_OBSERVATION_COMPLETE"
        or assessment.get("performance_readiness") != "REVIEW_REQUIRED"
        or assessment.get("telemetry_file") != "telemetry.json"
        or assessment.get("scientific_polarity") is not None
        or assessment.get("ordered_branch") is not None
    ):
        raise PerformanceReadinessError("A/RECON assessment is not a review-required artifact")
    projection = _finite_projection(assessment.get("projection"), caps=caps)

    telemetry_direct, telemetry = _read_canonical(
        root / "telemetry.json", label="A/RECON telemetry",
    )
    _validate_telemetry(
        telemetry_direct=telemetry_direct, telemetry=telemetry,
        assessment_direct=assessment_direct, assessment=assessment, caps=caps,
    )

    preview_direct, preview = _read_canonical(
        root / "technical-publication-preview.json", label="A/RECON inventory preview",
    )
    inventory_binding = _inventory_binding(root, preview_direct, preview)

    review_direct, review = _read_canonical(review_path, label="CM performance review evidence")
    if (
        set(review) != _REVIEW_KEYS or review.get("schema") != REVIEW_SCHEMA
        or review.get("review_disposition") != "CLEAN"
        or not isinstance(review.get("review_evidence_id"), str) or not review["review_evidence_id"]
        or not isinstance(review.get("reviewer_identity"), str) or not review["reviewer_identity"]
        or review.get("assessment_id") != ASSESS_ID
        or review.get("assessment_root") != str(root)
        or review.get("scientific_polarity") is not None
    ):
        raise PerformanceReadinessError("CM performance review must be canonical CLEAN evidence")

    return {
        "schema": READINESS_SCHEMA,
        "status": "PERFORMANCE_READY",
        "assessment_id": ASSESS_ID,
        "assessment_root": str(root),
        "source_identity_sha256": hashlib.sha256(current_source).hexdigest(),
        "source_identity": source_value,
        "assessment_binding": {
            **_binding(root / "assessment.json", assessment_direct),
            "manifest_sha256": hashlib.sha256(manifest_direct).hexdigest(),
        },
        "telemetry_binding": _binding(root / "telemetry.json", telemetry_direct),
        "inventory_binding": inventory_binding,
        "review_binding": {
            **_binding(review_path, review_direct),
            "review_disposition": "CLEAN",
            "review_evidence_id": review["review_evidence_id"],
            "reviewer_identity": review["reviewer_identity"],
            "review_evidence": review,
        },
        "resource_caps": caps,
        "projection": projection,
    }


def create_performance_readiness_receipt(
    *, assessment_root: str | Path, review_evidence: str | Path, output: str | Path,
) -> Path:
    destination = Path(output).resolve(strict=False)
    if destination.exists():
        raise PerformanceReadinessError("performance readiness receipt is create-once")
    try:
        root = Path(assessment_root).resolve(strict=True)
        review = Path(review_evidence).resolve(strict=True)
    except Exception as error:
        raise PerformanceReadinessError("performance readiness input path is unavailable") from error
    value = _evidence_value(root, review)
    try:
        atomic_create_bytes(destination, _canonical(value))
    except FileExistsError as error:
        raise PerformanceReadinessError("performance readiness receipt is create-once") from error
    return destination


def validate_performance_readiness_receipt(path: str | Path) -> dict[str, object]:
    try:
        receipt_path = Path(path).resolve(strict=True)
    except Exception as error:
        raise PerformanceReadinessError("performance readiness receipt is unavailable") from error
    _direct, observed = _read_canonical(receipt_path, label="performance readiness receipt")
    if set(observed) != _RECEIPT_KEYS or observed.get("schema") != READINESS_SCHEMA:
        raise PerformanceReadinessError("performance readiness receipt schema or fields differ")
    if observed.get("status") != "PERFORMANCE_READY":
        raise PerformanceReadinessError("performance readiness receipt is not PERFORMANCE_READY")
    try:
        root = Path(str(observed.get("assessment_root"))).resolve(strict=True)
    except OSError as error:
        raise PerformanceReadinessError("performance readiness assessment root differs") from error
    review_binding = observed.get("review_binding")
    if not isinstance(review_binding, dict) or not isinstance(review_binding.get("resolved_path"), str):
        raise PerformanceReadinessError("performance readiness review binding differs")
    try:
        review_path = Path(review_binding["resolved_path"]).resolve(strict=True)
    except OSError as error:
        raise PerformanceReadinessError("performance readiness review path differs") from error
    expected = _evidence_value(root, review_path)
    if observed != expected:
        raise PerformanceReadinessError("performance readiness receipt or bound evidence differs")
    return observed


__all__ = [
    "PerformanceReadinessError", "READINESS_SCHEMA", "REVIEW_SCHEMA",
    "create_performance_readiness_receipt", "validate_performance_readiness_receipt",
]
