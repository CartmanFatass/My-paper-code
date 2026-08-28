"""Atomic, create-only technical acceptance for the result-blind S0 slice."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .barriers import StageBarrier
from .contract import REVISION, S0_SLICE
from .manifest import canonical_json_bytes, manifest_digest


ACCEPTANCE_SCHEMA: Final[str] = "SCDMP_NATIVE_FUSION_R01_S0_TECHNICAL_ACCEPTANCE_V1"
_MEASUREMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "cpu_seconds",
        "wall_seconds",
        "peak_tracemalloc_bytes",
        "peak_rss_bytes",
        "read_bytes",
        "write_bytes",
    }
)


def _valid_sha(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def build_s0_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    measurements: Mapping[str, int | float],
    verification_command: str,
    verification_sha256: str,
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if set(measurements) != _MEASUREMENT_KEYS or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        for value in measurements.values()
    ):
        raise ValueError("S0 measurements are incomplete, extended, or negative")
    if not verification_command or not _valid_sha(verification_sha256):
        raise ValueError("verification command or evidence SHA-256 is invalid")
    rows = source_manifest.get("files")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("source manifest inventory is malformed")
    for row in rows:
        relative = str(row.get("path", ""))
        if not (root / relative).is_file():
            raise ValueError(f"manifest source is absent: {relative}")
    acceptance: dict[str, object] = {
        "schema": ACCEPTANCE_SCHEMA,
        "accepted": True,
        "stage": "S0_SOURCE_CONFORMANCE",
        "revision": REVISION,
        "slice": S0_SLICE,
        "source_manifest_sha256": manifest_digest(source_manifest),
        "verification_evidence_sha256": verification_sha256.lower(),
        "verification_command": verification_command,
        "verification": {
            "independent_oracle_native_equality": True,
            "terminal_precedence": True,
            "public_hold_switch_clocks": True,
            "endpoint_recomputation": True,
            "ordered_token_taint": True,
            "foundation_set_invariance": True,
            "zero_downstream_identity_leakage": True,
            "current_byte_source_manifest": True,
            "atomic_create_only": True,
        },
        "measurements": dict(measurements),
        "static_next_slice_cost": {
            "basis": "direction-local foundation construction and result-blind technical tests only",
            "low": {
                "engineering_hours": 16,
                "cpu_core_hours": 1,
                "wall_seconds": 60,
                "peak_memory_mib": 1024,
                "storage_mib": 25,
            },
            "central": {
                "engineering_hours": 32,
                "cpu_core_hours": 2,
                "wall_seconds": 180,
                "peak_memory_mib": 2048,
                "storage_mib": 75,
            },
            "high": {
                "engineering_hours": 56,
                "cpu_core_hours": 4,
                "wall_seconds": 600,
                "peak_memory_mib": 4096,
                "storage_mib": 200,
            },
        },
        "next_conditional_slice": {
            "name": "SCDMP-NATIVE-FUSION-R01-S1-FOUNDATION-CONSTRUCTION-V1",
            "exact_paths": [
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_contract.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_identity.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_network.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_optimizer.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_acceptance.py",
                "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation.py",
                "temp/directions/semigroup_consistent_duration_model_policy/test/native_fusion_r01/s1/g1/",
            ],
            "technical_command": (
                "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
                "tests/experiments/candidates/scdmp_variable_k/"
                "test_native_fusion_r01_foundation.py -q"
            ),
            "effect_refs": [],
            "activity_authorized": False,
        },
        "firewall": {
            "materialized": ["source_manifest", "technical_acceptance"],
            "question_relevant_value_visible": False,
            "activity_authorized": False,
            "effect_refs": [],
        },
        "effect_refs": [],
        "activity_authorized": False,
    }
    StageBarrier.s0().validate_payload(acceptance)
    return acceptance


def acceptance_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def emit_create_only(path: Path, value: Mapping[str, object]) -> None:
    """Install complete canonical bytes atomically without overwrite semantics."""

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
