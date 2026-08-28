"""Complete S2 source/slot/evidence manifests with hard downstream absence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .barriers import StageBarrier
from .foundation_activity_contract import (
    REPLICATES,
    S2_SLICE,
    UPDATES_PER_FOUNDATION,
    prospective_counts,
)
from .foundation_lifecycle import TechnicalFoundationSlot


SOURCE_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_contract.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_evidence.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_lifecycle.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_runner.py",
    "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation_preactivity.py",
)
EXACT_TEST_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
    "tests/experiments/candidates/scdmp_variable_k/"
    "test_native_fusion_r01_foundation_preactivity.py -q"
)
OUTPUT_ROOT: Final[str] = (
    "temp/directions/semigroup_consistent_duration_model_policy/test/"
    "native_fusion_r01/s2/g1"
)
ACCEPTED_INPUT_REFS: Final[tuple[dict[str, str], ...]] = (
    {
        "path": (
            "docs/research/candidates/semigroup_consistent_duration_model_policy/"
            "SCDMP_NATIVE_FUSION_SCIENCE_AUTHORITY_R01_20260827.md"
        ),
        "sha256": "c8091b15293f2cdeae4fc00a42bdfc1a0ae165d930fc152bca86610979e0c47c",
    },
    {
        "path": "experiments/candidates/scdmp_variable_k/native_fusion_r01/source_manifest.json",
        "sha256": "0e6b6f02d2f893e2687c6abaf70fa99a03bf8c4324e4a9458efa9f450ba363a0",
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
)
_MEASUREMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "cpu_seconds",
        "wall_seconds",
        "peak_working_set_bytes",
        "peak_tracemalloc_bytes",
        "read_bytes",
        "write_bytes",
    }
)


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class DownstreamBarrier:
    all_24_technically_accepted: bool
    competence_open: bool
    opportunity_open: bool
    activity_authorized: bool
    effect_refs: tuple[object, ...]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_sha(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_source_manifest(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    files = []
    for relative in SOURCE_PATHS:
        target = root / relative
        if not target.is_file():
            raise EvidenceError(f"S2 source is absent: {relative}")
        files.append({"path": relative, "sha256": _sha(target)})
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S2_SOURCE_MANIFEST_V1",
        "complete": True,
        "files": files,
        "legacy_imported": False,
        "activity_authorized": False,
        "effect_refs": [],
    }


def accepted_technical_slot_fixture(
    replicate_index: int, *, technical_state_sha256: str
) -> TechnicalFoundationSlot:
    if (
        isinstance(replicate_index, bool)
        or not isinstance(replicate_index, int)
        or not 0 <= replicate_index < REPLICATES
    ):
        raise EvidenceError("replicate_index must be in [0,24)")
    if not _valid_sha(technical_state_sha256):
        raise EvidenceError("technical_state_sha256 is invalid")
    return TechnicalFoundationSlot(
        replicate_index=replicate_index,
        completed_updates=UPDATES_PER_FOUNDATION,
        persistent_step_index=3_072,
        technical_state_sha256=technical_state_sha256,
        materialized=False,
        eligible=False,
        technically_accepted=True,
    )


def build_checkpoint_manifest(
    slots: tuple[TechnicalFoundationSlot, ...],
) -> dict[str, object]:
    if len(slots) != REPLICATES or tuple(slot.replicate_index for slot in slots) != tuple(
        range(REPLICATES)
    ):
        raise EvidenceError("checkpoint manifest requires all 24 ordered technical slots")
    for slot in slots:
        if (
            slot.completed_updates != UPDATES_PER_FOUNDATION
            or slot.persistent_step_index != 3_072
            or slot.materialized
            or slot.eligible
            or not slot.technically_accepted
            or not _valid_sha(slot.technical_state_sha256)
        ):
            raise EvidenceError("checkpoint manifest slot is not technically accepted and closed")
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S2_CHECKPOINT_MANIFEST_V1",
        "complete": True,
        "slots": [asdict(slot) for slot in slots],
        "eligible_artifact_present": False,
        "activity_authorized": False,
        "effect_refs": [],
    }


def require_all_technical_acceptance(
    checkpoint_manifest: Mapping[str, object],
) -> DownstreamBarrier:
    slots = checkpoint_manifest.get("slots")
    if (
        checkpoint_manifest.get("complete") is not True
        or not isinstance(slots, list)
        or len(slots) != REPLICATES
        or checkpoint_manifest.get("eligible_artifact_present") is not False
    ):
        raise EvidenceError("all 24 checkpoint slots must be technically accepted")
    return DownstreamBarrier(True, False, False, False, ())


def build_evidence_manifest(
    *,
    source_manifest: Mapping[str, object],
    checkpoint_manifest: Mapping[str, object],
    observed_artifact_paths: tuple[str, ...],
) -> dict[str, object]:
    if observed_artifact_paths:
        raise EvidenceError("downstream artifact path is forbidden in S2")
    barrier = require_all_technical_acceptance(checkpoint_manifest)
    files = source_manifest.get("files")
    if source_manifest.get("complete") is not True or not isinstance(files, list) or len(files) != 5:
        raise EvidenceError("source manifest is incomplete")
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S2_EVIDENCE_MANIFEST_V1",
        "complete": True,
        "source_manifest_sha256": manifest_digest(source_manifest),
        "checkpoint_manifest_sha256": manifest_digest(checkpoint_manifest),
        "all_24_technically_accepted": barrier.all_24_technically_accepted,
        "observed_artifact_paths": [],
        "hard_downstream_absence": True,
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "effect_refs": [],
    }


def _require_ref_fresh(root: Path, ref: Mapping[str, str]) -> None:
    target = root / ref["path"]
    if not target.is_file() or _sha(target) != ref["sha256"]:
        raise EvidenceError(f"accepted input bytes changed: {ref['path']}")


def build_s2_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    checkpoint_manifest: Mapping[str, object],
    evidence_manifest: Mapping[str, object],
    measurements: Mapping[str, int | float],
    verification_sha256: str,
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if source_manifest != build_source_manifest(root):
        raise EvidenceError("S2 source manifest does not bind current bytes")
    require_all_technical_acceptance(checkpoint_manifest)
    if evidence_manifest != build_evidence_manifest(
        source_manifest=source_manifest,
        checkpoint_manifest=checkpoint_manifest,
        observed_artifact_paths=(),
    ):
        raise EvidenceError("S2 evidence manifest differs")
    if set(measurements) != _MEASUREMENT_KEYS or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        for value in measurements.values()
    ):
        raise EvidenceError("S2 measurements are incomplete, extended, or negative")
    if not _valid_sha(verification_sha256):
        raise EvidenceError("verification evidence SHA-256 is invalid")
    for ref in ACCEPTED_INPUT_REFS:
        _require_ref_fresh(root, ref)
    counts = prospective_counts()
    acceptance: dict[str, object] = {
        "schema": "SCDMP_NATIVE_FUSION_R01_S2_TECHNICAL_ACCEPTANCE_V1",
        "accepted": True,
        "stage": "S2_FOUNDATION_PREACTIVITY",
        "slice": S2_SLICE,
        "accepted_input_refs": [dict(ref) for ref in ACCEPTED_INPUT_REFS],
        "source_refs": list(source_manifest["files"]),
        "manifest_refs": [
            {
                "path": f"{OUTPUT_ROOT}/S2_SOURCE_MANIFEST.json",
                "sha256": manifest_digest(source_manifest),
            },
            {
                "path": f"{OUTPUT_ROOT}/S2_CHECKPOINT_MANIFEST.json",
                "sha256": manifest_digest(checkpoint_manifest),
            },
            {
                "path": f"{OUTPUT_ROOT}/S2_EVIDENCE_MANIFEST.json",
                "sha256": manifest_digest(evidence_manifest),
            },
        ],
        "verification_command": EXACT_TEST_COMMAND,
        "verification_evidence_ref": {
            "path": f"{OUTPUT_ROOT}/pytest-verification.json",
            "sha256": verification_sha256.lower(),
        },
        "measurements": dict(measurements),
        "prospective_counts": asdict(counts),
        "technical_assertions": [
            "exact_24_replicate_roster_without_identity_creation",
            "exact_update_episode_order_duration_and_step_counts",
            "immutable_old_state_and_atomic_update_transitions",
            "cold_resume_without_persistent_index_reuse",
            "all_24_technical_slots_required_before_any_downstream_gate",
            "complete_source_checkpoint_and_evidence_manifests",
            "runner_blocks_registered_flags_activity_flags_and_unmanifested_commands",
            "hard_downstream_absence",
        ],
        "static_next_slice_cost": {
            "basis": "direction-local result-blind immutable activity-gate construction only",
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
        "next_conditional_slice": {
            "name": "SCDMP-NATIVE-FUSION-R01-S3-FOUNDATION-ACTIVITY-GATE-CONSTRUCTION-V1",
            "exact_paths": [
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_run_manifest.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_gate.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_evidence.py",
                "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation_activity_gate.py",
                "temp/directions/semigroup_consistent_duration_model_policy/test/native_fusion_r01/s3/g1/",
            ],
            "technical_command": (
                "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
                "tests/experiments/candidates/scdmp_variable_k/"
                "test_native_fusion_r01_foundation_activity_gate.py -q"
            ),
            "effect_refs": [],
            "activity_authorized": False,
        },
        "firewall": {
            "registered_identity_present": False,
            "eligible_artifact_present": False,
            "question_relevant_value_visible": False,
            "activity_authorized": False,
            "effect_refs": [],
        },
        "effect_refs": [],
        "activity_authorized": False,
    }
    StageBarrier.s0().validate_payload(acceptance)
    return acceptance


def emit_create_only(path: Path, value: Mapping[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
