"""Create-only technical acceptance for S1 foundation construction."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .barriers import StageBarrier
from .foundation_contract import S1_SLICE


ACCEPTANCE_SCHEMA: Final[str] = "SCDMP_NATIVE_FUSION_R01_S1_TECHNICAL_ACCEPTANCE_V1"
EXACT_TEST_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
    "tests/experiments/candidates/scdmp_variable_k/"
    "test_native_fusion_r01_foundation.py -q"
)
S1_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_acceptance.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_contract.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_identity.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_network.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_optimizer.py",
    "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation.py",
)
R01_REF: Final[dict[str, str]] = {
    "path": (
        "docs/research/candidates/semigroup_consistent_duration_model_policy/"
        "SCDMP_NATIVE_FUSION_SCIENCE_AUTHORITY_R01_20260827.md"
    ),
    "sha256": "c8091b15293f2cdeae4fc00a42bdfc1a0ae165d930fc152bca86610979e0c47c",
}
S0_MANIFEST_REF: Final[dict[str, str]] = {
    "path": "experiments/candidates/scdmp_variable_k/native_fusion_r01/source_manifest.json",
    "sha256": "0e6b6f02d2f893e2687c6abaf70fa99a03bf8c4324e4a9458efa9f450ba363a0",
}
S0_ACCEPTANCE_REF: Final[dict[str, str]] = {
    "path": (
        "temp/directions/semigroup_consistent_duration_model_policy/test/"
        "native_fusion_r01/s0/g1/S0_TECHNICAL_ACCEPTANCE.json"
    ),
    "sha256": "52bd81aed310a81791c441dd9253d1704f3e28efa295fe42a635d78776645cce",
}
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


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_sha(value: str) -> bool:
    if len(value) != 64:
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


def _require_ref_fresh(root: Path, ref: Mapping[str, str]) -> None:
    target = root / ref["path"]
    if not target.is_file() or _sha(target) != ref["sha256"]:
        raise ValueError(f"accepted input bytes changed: {ref['path']}")


def build_s1_acceptance(
    *,
    repository_root: Path,
    measurements: Mapping[str, int | float],
    verification_sha256: str,
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if set(measurements) != _MEASUREMENT_KEYS or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        for value in measurements.values()
    ):
        raise ValueError("S1 measurements are incomplete, extended, or negative")
    if not _valid_sha(verification_sha256):
        raise ValueError("verification evidence SHA-256 is invalid")
    for ref in (R01_REF, S0_MANIFEST_REF, S0_ACCEPTANCE_REF):
        _require_ref_fresh(root, ref)
    source_refs = []
    for relative in S1_SOURCE_PATHS:
        target = root / relative
        if not target.is_file():
            raise ValueError(f"S1 source is absent: {relative}")
        source_refs.append({"path": relative, "sha256": _sha(target)})
    acceptance: dict[str, object] = {
        "schema": ACCEPTANCE_SCHEMA,
        "accepted": True,
        "stage": "S1_FOUNDATION_CONSTRUCTION",
        "slice": S1_SLICE,
        "accepted_input_refs": [dict(R01_REF), dict(S0_MANIFEST_REF), dict(S0_ACCEPTANCE_REF)],
        "source_refs": source_refs,
        "verification_command": EXACT_TEST_COMMAND,
        "verification_evidence_sha256": verification_sha256.lower(),
        "measurements": dict(measurements),
        "technical_assertions": [
            "exact_actor_critic_architecture_and_parameter_counts",
            "float32_row_major_xavier_gain_one_and_zero_biases",
            "strict_order_erasure",
            "nonregistered_replicate_identity_and_byte_immutability",
            "duration_correct_targets_advantages_and_ppo_losses",
            "combined_global_gradient_clip",
            "persistent_adamw_index_and_exact_hyperparameters",
            "four_epoch_four_minibatch_partition_and_structural_step_counts",
        ],
        "static_next_slice_cost": {
            "basis": "direction-local result-blind foundation preactivity services only",
            "low": {
                "engineering_hours": 20,
                "cpu_core_hours": 1,
                "wall_seconds": 120,
                "peak_memory_mib": 1024,
                "storage_mib": 50,
            },
            "central": {
                "engineering_hours": 36,
                "cpu_core_hours": 2,
                "wall_seconds": 300,
                "peak_memory_mib": 2048,
                "storage_mib": 100,
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
            "name": "SCDMP-NATIVE-FUSION-R01-S2-FOUNDATION-PREACTIVITY-V1",
            "exact_paths": [
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_contract.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_lifecycle.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_runner.py",
                "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_evidence.py",
                "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation_preactivity.py",
                "temp/directions/semigroup_consistent_duration_model_policy/test/native_fusion_r01/s2/g1/",
            ],
            "technical_command": (
                "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
                "tests/experiments/candidates/scdmp_variable_k/"
                "test_native_fusion_r01_foundation_preactivity.py -q"
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
