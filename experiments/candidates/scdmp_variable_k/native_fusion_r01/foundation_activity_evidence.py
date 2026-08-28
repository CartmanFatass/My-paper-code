"""Complete-only S3 source/chain/gate evidence; no activity artifacts."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .barriers import StageBarrier
from .foundation_activity_gate import command_contract
from .foundation_run_manifest import HMAC_DOMAINS, canonical_json_bytes


SOURCE_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_evidence.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_gate.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_run_manifest.py",
    "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation_activity_gate.py",
)
EXACT_TEST_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
    "tests/experiments/candidates/scdmp_variable_k/"
    "test_native_fusion_r01_foundation_activity_gate.py -q"
)
S3_OUTPUT_ROOT: Final[str] = (
    "temp/directions/semigroup_consistent_duration_model_policy/test/"
    "native_fusion_r01/s3/g1"
)
_MEASUREMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "cpu_seconds",
        "wall_seconds",
        "peak_working_set_bytes",
        "peak_tracemalloc_bytes",
        "read_bytes",
        "write_bytes",
        "storage_bytes",
    }
)
ACCEPTED_CHAIN_REFS: Final[tuple[dict[str, str], ...]] = (
    {
        "path": (
            "docs/research/candidates/semigroup_consistent_duration_model_policy/"
            "SCDMP_NATIVE_FUSION_SCIENCE_AUTHORITY_R01_20260827.md"
        ),
        "sha256": "c8091b15293f2cdeae4fc00a42bdfc1a0ae165d930fc152bca86610979e0c47c",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s0/g1/S0_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "52bd81aed310a81791c441dd9253d1704f3e28efa295fe42a635d78776645cce",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s1/g1/S1_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "8dfcb06ca4b37d297a624323ef7f178009f1a84724f7797d6de7268a00dc3195",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s2/g1/S2_SOURCE_MANIFEST.json"
        ),
        "sha256": "794f888c6ec0dbfe50b086884c0e602da7f1278d68ceef33e2ac4358496808a3",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s2/g1/S2_CHECKPOINT_MANIFEST.json"
        ),
        "sha256": "6dd1968db5a95455dead048a036202bab73437eb0dbda7b1b19f3d967d115ea3",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s2/g1/S2_EVIDENCE_MANIFEST.json"
        ),
        "sha256": "0464459b1fe639efd9847e95bd5b103871c8950b1abeea48b3a4d694aae6eb36",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s2/g1/S2_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "bacfbfe0da703b1bef4bb93a93fff92c4f5ce0c39c6f800617d255a6e7fdb825",
    },
)


class ActivityEvidenceError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_source_manifest(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    files = []
    for relative in SOURCE_PATHS:
        target = root / relative
        if not target.is_file():
            raise ActivityEvidenceError(f"S3 source is absent: {relative}")
        files.append({"path": relative, "sha256": _sha(target)})
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S3_SOURCE_MANIFEST_V1",
        "complete": True,
        "files": files,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def _require_chain_fresh(root: Path) -> None:
    for ref in ACCEPTED_CHAIN_REFS:
        target = root / ref["path"]
        if not target.is_file() or _sha(target) != ref["sha256"]:
            raise ActivityEvidenceError(f"accepted chain bytes changed: {ref['path']}")


def build_complete_activity_evidence(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    prospective_manifest: Mapping[str, object],
    observed_artifact_paths: tuple[str, ...],
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if source_manifest != build_source_manifest(root):
        raise ActivityEvidenceError("S3 source manifest does not bind current bytes")
    _require_chain_fresh(root)
    if observed_artifact_paths:
        raise ActivityEvidenceError("activity artifact path is forbidden in S3")
    roster = prospective_manifest.get("replicate_roster")
    terminal = prospective_manifest.get("terminal_slots")
    if not isinstance(roster, list) or len(roster) != 24:
        raise ActivityEvidenceError("prospective manifest requires 24 roster entries")
    if not isinstance(terminal, list) or len(terminal) != 24:
        raise ActivityEvidenceError("prospective manifest requires 24 terminal slots")
    if any(
        row.get("update_index") != 192
        or row.get("materialized") is not False
        or row.get("eligible") is not False
        for row in terminal
        if isinstance(row, Mapping)
    ) or any(not isinstance(row, Mapping) for row in terminal):
        raise ActivityEvidenceError("prospective terminal slot differs")
    if prospective_manifest.get("status") != "PROSPECTIVE_CREATE_ONLY_UNISSUED":
        raise ActivityEvidenceError("prospective manifest status differs")
    if prospective_manifest.get("code_sha256") != manifest_digest(source_manifest):
        raise ActivityEvidenceError("prospective manifest code SHA differs")
    if tuple(prospective_manifest.get("hmac_sha256_domains", ())) != HMAC_DOMAINS:
        raise ActivityEvidenceError("HMAC domain roster differs")
    for field in (
        "master_present",
        "registered_identity_present",
        "registered_address_present",
        "model_present",
        "optimizer_present",
        "checkpoint_present",
        "question_relevant_value_visible",
        "activity_authorized",
        "operator_now",
    ):
        if prospective_manifest.get(field) is not False:
            raise ActivityEvidenceError(f"prospective firewall field differs: {field}")
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S3_COMPLETE_ACTIVITY_EVIDENCE_V1",
        "complete": True,
        "accepted_chain_refs": [dict(ref) for ref in ACCEPTED_CHAIN_REFS],
        "source_manifest_sha256": manifest_digest(source_manifest),
        "prospective_manifest_sha256": manifest_digest(prospective_manifest),
        "prospective_manifest_status": prospective_manifest["status"],
        "command_contract": asdict(command_contract()),
        "observed_artifact_paths": [],
        "hard_downstream_absence": True,
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def build_s3_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    prospective_manifest: Mapping[str, object],
    evidence_manifest: Mapping[str, object],
    measurements: Mapping[str, object],
    verification_sha256: str,
) -> dict[str, object]:
    """Bind complete S3 construction evidence without authorizing activity."""

    root = Path(repository_root).resolve()
    if source_manifest != build_source_manifest(root):
        raise ActivityEvidenceError("S3 source manifest does not bind current bytes")
    expected_evidence = build_complete_activity_evidence(
        repository_root=root,
        source_manifest=source_manifest,
        prospective_manifest=prospective_manifest,
        observed_artifact_paths=(),
    )
    if evidence_manifest != expected_evidence:
        raise ActivityEvidenceError("S3 evidence manifest differs")
    if set(measurements) != _MEASUREMENT_KEYS or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value < 0
        for value in measurements.values()
    ):
        raise ActivityEvidenceError("S3 measurements are incomplete or invalid")
    if (
        len(verification_sha256) != 64
        or any(character not in "0123456789abcdef" for character in verification_sha256)
    ):
        raise ActivityEvidenceError("verification SHA256 is invalid")

    source_digest = manifest_digest(source_manifest)
    prospective_digest = manifest_digest(prospective_manifest)
    evidence_digest = manifest_digest(evidence_manifest)
    acceptance: dict[str, object] = {
        "schema": "SCDMP_NATIVE_FUSION_R01_S3_TECHNICAL_ACCEPTANCE",
        "accepted": True,
        "stage": "S3_FOUNDATION_ACTIVITY_GATE_CONSTRUCTION",
        "accepted_chain_refs": [dict(ref) for ref in ACCEPTED_CHAIN_REFS],
        "source_refs": [dict(ref) for ref in source_manifest["files"]],
        "manifest_refs": [
            {
                "path": f"{S3_OUTPUT_ROOT}/S3_SOURCE_MANIFEST.json",
                "sha256": source_digest,
            },
            {
                "path": (
                    f"{S3_OUTPUT_ROOT}/"
                    "S3_PROSPECTIVE_FOUNDATION_ACTIVITY_MANIFEST.json"
                ),
                "sha256": prospective_digest,
            },
            {
                "path": f"{S3_OUTPUT_ROOT}/S3_COMPLETE_ACTIVITY_EVIDENCE.json",
                "sha256": evidence_digest,
            },
        ],
        "verification_command": EXACT_TEST_COMMAND,
        "verification_ref": {
            "path": f"{S3_OUTPUT_ROOT}/pytest-verification.json",
            "sha256": verification_sha256,
        },
        "measurements": dict(measurements),
        "accepted_construction_estimate": {
            "low": {
                "engineering_hours": 16,
                "cpu_core_hours": 1,
                "wall_seconds": 120,
                "peak_memory_mib": 1024,
                "storage_mib": 50,
            },
            "central": {
                "engineering_hours": 28,
                "cpu_core_hours": 2,
                "wall_seconds": 300,
                "peak_memory_mib": 2048,
                "storage_mib": 100,
            },
            "high": {
                "engineering_hours": 48,
                "cpu_core_hours": 4,
                "wall_seconds": 600,
                "peak_memory_mib": 4096,
                "storage_mib": 200,
            },
        },
        "technical_assertions": {
            "prospective_manifest_create_only": True,
            "exact_code_sha_bound": True,
            "output_root_must_be_absent": True,
            "ordered_native_gates": ["I_native", "C_native", "O_native"],
            "foundation_activity_observed": False,
            "downstream_stages_observed": False,
        },
        "next_conditional_boundary": {
            "kind": "PORTFOLIO_RECONCILE_FOUNDATION_ACTIVITY",
            "requirements": [
                "fresh R01 and S0-S3 path-plus-SHA references",
                "separate empirical activity authorization",
                "issued immutable run manifest",
                "exact code SHA byte match",
                "create-only output root absent",
                "exactly one Experiment Operator for the frozen activity command",
                (
                    "runtime estimate over 7200 seconds requires one performance "
                    "reasonableness review and exact user approval"
                ),
            ],
            "activity_authorized": False,
            "operator_now": False,
            "effect_refs": [],
        },
        "firewall": {
            "registered_identity_present": False,
            "eligible_artifact_present": False,
            "question_relevant_value_visible": False,
            "activity_authorized": False,
            "operator_now": False,
            "effect_refs": [],
        },
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }
    StageBarrier.s0().validate_payload(acceptance)
    return acceptance


def emit_create_only(path: Path, value: Mapping[str, object]) -> None:
    """Atomically create one canonical JSON artifact and never replace bytes."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as temporary:
            temporary.write(canonical_json_bytes(value))
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.link(temporary_name, target)
    except FileExistsError as exc:
        raise ActivityEvidenceError(f"create-only artifact exists: {target}") from exc
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
