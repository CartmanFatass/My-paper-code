
"""Source-bound exact-feasibility selector for the VSP06-B2R1 treatment.

This module is import-safe without OR-Tools.  The canonical selector entry
point fails closed unless the exact pinned CPython/OR-Tools identity is
available.  It has no alternative solver and never interprets infeasibility as
a scientific conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from itertools import product
from typing import Any, Iterable, Mapping, Sequence


SELECTOR_ID = "VSP06-B2R1-SB-EF-CP-SAT-V1"
VERIFIER_ID = "VSP06-B2R1-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
TREATMENT_ID = (
    "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-EXACT-FEASIBILITY"
)
CATALOG_ID = "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CATALOG-V1"
LEDGER_ID = "VSP06-B2R1-CONSTRAINT-TARGET-LEDGER-V1"
SALT = "8100799/"
DECISION_PREFIX = b"VSP06-B2R1-SB-EF-CP-SAT-V1/decision-order/v1\0"
REQUIRED_ORTOOLS = "9.12.4544"
REQUIRED_PYTHON = (3, 11)
REQUIRED_TORCH = "2.7.0"
WALL_SECONDS = 1800
MEMORY_BYTES = 4096 * 1024 * 1024
INVALID = "B2R1_SELECTOR_INVALID_NO_RUN"
VALID = "B2R1_SELECTOR_VERIFIED_MANIFEST_FIXED"

TUPLE_FIELDS = (
    "consumer",
    "seed_row",
    "panel",
    "branch",
    "retention_length",
    "y",
    "reset_y",
    "target_identity",
    "target_version",
    "event_type",
    "decoy_sequence",
    "current_bytes",
    "roster",
    "legal_mask",
    "clock",
    "rng_binding",
    "quartet_base",
    "nonce",
)

PARAMETER_ASSIGNMENTS = {
    "num_search_workers": 1,
    "search_branching": "FIXED_SEARCH",
    "randomize_search": False,
    "random_seed": 8100699,
    "stop_after_first_solution": True,
    "enumerate_all_solutions": False,
    "cp_model_presolve": True,
    "symmetry_level": 0,
    "use_lns": False,
    "log_search_progress": True,
    "max_time_in_seconds": 1800.0,
    "max_deterministic_time": 1000.0,
}

DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v8"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
ACTIVITY_NAMES = (
    "canonical_generator_calls", "canonical_rows_observed", "canonical_ortools_processes",
    "replicas", "canonical_verifier_admissions", "witnesses", "manifests", "model_fits",
    "trainer_calls", "environment_episodes", "environment_transitions", "policy_forwards",
    "learner_updates", "optimizer_steps", "evaluator_calls", "evaluation_episodes",
    "environment_rng_calls", "action_rng_calls",
)

SOURCE_CONFIG_RELATIVE_PATHS = (
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_source_bound_exact_feasibility.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_independent_exact_manifest_verifier.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "scripts/run_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "docs/research/legacy/directions/vsp_06_mssr/VSP06_B2R1_CONSTRAINT_TARGET_LEDGER_V1.json",
    "docs/research/legacy/directions/vsp_06_mssr/VSP06_B2R1_CODE_SCIENCE_INDEX.md",
)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STAGE2_SESSION_ROOT = (
    PROJECT_ROOT
    / "temp/sessions/code_project_manager/"
    "vsp06_b2r1_source_bound_exact_feasibility_credit_efficiency"
)
SELECTOR_RECEIPT_KEYS = frozenset({
    "branch", "final_commit", "stage2_authorization_sha256",
    "source_config_digest_map", "source_config_digest_map_sha256",
    "python_executable", "python_executable_sha256", "solver_artifacts",
    "solver_artifact_set_sha256", "sealed_objects", "sealed_path_schema",
    "sealed_path_schema_sha256", "receipt_path", "receipt_self_digest_is_external",
    "replica_count", "replica_2_role", "activity_accounting", "catalog_path",
    "catalog_sha256", "universe_spec_path", "universe_spec_sha256", "ledger_path",
    "ledger_sha256", "bindings_path", "bindings_sha256", "witness_path",
    "witness_sha256", "manifest_path", "manifest_file_sha256",
    "manifest_content_sha256", "verifier_report_path", "verifier_report_sha256",
    "replica_resource_telemetry",
    "activity_counts", "full_environment_receipt_path",
    "full_environment_receipt_sha256",
})
FULL_ENVIRONMENT_RECEIPT_KEYS = frozenset({
    "schema_version", "python_implementation", "python_version",
    "python_executable", "python_executable_sha256", "ortools_version",
    "ortools_source_tag", "solver_artifacts", "solver_artifact_set_sha256",
    "sat_parameters_sha256", "sat_parameters_hex", "sat_parameter_assignments",
    "sat_parameter_assignments_sha256", "os", "os_release", "architecture",
    "torch_distribution_version", "torch_build_version", "torch_cpu_only",
    "torch_cuda_version", "torch_cuda_available",
    "torch_deterministic_algorithms", "torch_deterministic_warn_only",
    "torch_num_threads", "torch_num_interop_threads", "torch_native_artifacts",
    "torch_native_artifact_set_sha256", "torch_distribution_inventory_sha256",
    "torch_build_config_sha256", "thread_environment",
})
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
}


def stage2_paths() -> dict[str, Path]:
    selector_root = STAGE2_SESSION_ROOT / "selector"
    result = {
        "session_root": STAGE2_SESSION_ROOT,
        "claim": STAGE2_SESSION_ROOT / "stage2_namespace_claim.json",
        "catalog": STAGE2_SESSION_ROOT / "canonical_catalog.json",
        "universe_spec": STAGE2_SESSION_ROOT / "declarative_universe_spec.json",
        "ledger": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[5],
        "selector": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[0],
        "verifier": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[1],
        "toy": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[2],
        "runner": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[3],
        "test": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[4],
        "index": PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[6],
        "selector_root": selector_root,
        "bindings": selector_root / "frozen_bindings.json",
        "replica_1": selector_root / "cold_replica_1.json",
        "replica_2": selector_root / "cold_replica_2.json",
        "witness": selector_root / "membership_witness.json",
        "proposed_manifest": selector_root / "proposed_manifest.json",
        "verifier_report": selector_root / "independent_verifier_report.json",
        "receipt": selector_root / "selector_success_receipt.json",
        "manifest": STAGE2_SESSION_ROOT / "frozen_manifest.json",
        "stage2_failure": STAGE2_SESSION_ROOT / "stage2_terminal_failure.json",
        "registered_full": STAGE2_SESSION_ROOT / "registered_full",
        "full_claim": STAGE2_SESSION_ROOT / "registered_full/registered_full_claim.json",
        "full_failure": STAGE2_SESSION_ROOT / "registered_full/registered_full_failure.json",
        "result": PROJECT_ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json",
        "operator_receipt": PROJECT_ROOT / "temp/sessions/code_project_manager/vsp06_b2r1_operator_receipt.json",
    }
    for phase in (
        "claim", "catalog", "replica_1", "replica_2", "verifier", "witness",
        "manifest", "full_claim", "full_calibration", "full_primary_1",
        "full_primary_2", "full_primary_3", "full_primary_4", "full_complete",
    ):
        result[f"activity_{phase}"] = STAGE2_SESSION_ROOT / "activity" / f"{phase}.json"
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for arm in ("MSSR_P_FIXED_VALIDITY_CARRIER", "GENERIC_PROVENANCE_CONDITIONED_CARRIER"):
            for checkpoint in (0, 512, 1024, 1536, 2048, 2560, 3072, 4096):
                result[f"checkpoint_{seed}_{arm}_{checkpoint}"] = (
                    result["registered_full"] / "checkpoints" / seed / arm
                    / f"episodes_{checkpoint}.pt"
                )
    return result


def validate_stage2_authorization(value: Mapping[str, Any]) -> Mapping[str, Any]:
    required = {
        "direction", "candidate", "treatment_id", "selector_id", "verifier_id",
        "scientific_parent", "final_commit", "source_build_read_allowlist",
        "source_config_digest_map", "source_config_digest_map_sha256",
        "formal", "synthetic_only", "zero_start_activity",
        "full_environment_receipt_path", "full_environment_receipt_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise SelectorInvalid("missing or malformed Stage-2 authorization")
    fixed = {
        "direction": DIRECTION_ID, "candidate": CANDIDATE_ID, "treatment_id": TREATMENT_ID,
        "selector_id": SELECTOR_ID, "verifier_id": VERIFIER_ID,
        "scientific_parent": SCIENTIFIC_PARENT, "formal": False, "synthetic_only": False,
    }
    if any(
        type(value[key]) is not type(expected) or value[key] != expected
        for key, expected in fixed.items()
    ):
        raise SelectorInvalid("Stage-2 authorization binding mismatch")
    commit = value["final_commit"]
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SelectorInvalid("Stage-2 final commit must be one exact lowercase 40-hex binding")
    environment_path = value["full_environment_receipt_path"]
    environment_digest = value["full_environment_receipt_sha256"]
    if (
        not isinstance(environment_path, str) or not environment_path
        or not Path(environment_path).is_absolute() or ".." in Path(environment_path).parts
        or any(char in environment_path for char in "*?[")
        or not isinstance(environment_digest, str) or len(environment_digest) != 64
        or any(char not in "0123456789abcdef" for char in environment_digest)
    ):
        raise SelectorInvalid("Stage-2 full-environment receipt anchor is invalid")
    allowlist = value["source_build_read_allowlist"]
    if not isinstance(allowlist, list) or not allowlist or any(
        not isinstance(item, str) or not item or not Path(item).is_absolute()
        or ".." in Path(item).parts or any(char in item for char in "*?[")
        for item in allowlist
    ) or len(set(allowlist)) != len(allowlist):
        raise SelectorInvalid("Stage-2 source/build/read allowlist is absent")
    activity = value["zero_start_activity"]
    if not isinstance(activity, Mapping) or set(activity) != set(ACTIVITY_NAMES) or any(
        type(v) is not int or v != 0 for v in activity.values()
    ):
        raise SelectorInvalid("Stage-2 zero-start activity binding failed")
    digest_map = value["source_config_digest_map"]
    digest_map_digest = value["source_config_digest_map_sha256"]
    if (
        not isinstance(digest_map, Mapping)
        or set(digest_map) != set(SOURCE_CONFIG_RELATIVE_PATHS)
        or any(
            not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            for digest in digest_map.values()
        )
        or not isinstance(digest_map_digest, str) or len(digest_map_digest) != 64
        or any(char not in "0123456789abcdef" for char in digest_map_digest)
        or digest_map_digest != sha256_bytes(_canonical_json_bytes(dict(digest_map)))
    ):
        raise SelectorInvalid("Stage-2 audited source/config digest map is invalid")
    return value


def validate_activity_counts(value: Mapping[str, Any]) -> dict[str, int]:
    if (
        not isinstance(value, Mapping) or set(value) != set(ACTIVITY_NAMES)
        or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in value.values())
    ):
        raise SelectorInvalid("Stage-2 activity counter schema is invalid")
    return dict(value)


def exact_claim(
    authorization: Mapping[str, Any], *, phase: str,
) -> dict[str, Any]:
    validate_stage2_authorization(authorization)
    if phase not in {"stage2_selector_continuation", "registered_full"}:
        raise SelectorInvalid("Stage-2 claim phase is invalid")
    return {
        "treatment": TREATMENT_ID,
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": sha256_bytes(_canonical_json_bytes(authorization)),
        "ordinal": 1,
        "phase": phase,
        "zero_start_activity": dict(authorization["zero_start_activity"]),
        "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
    }


def validate_exact_claim(
    value: Mapping[str, Any], authorization: Mapping[str, Any], *, phase: str,
) -> dict[str, Any]:
    expected = exact_claim(authorization, phase=phase)
    if not isinstance(value, Mapping) or not _exact_json_equal(dict(value), expected):
        raise SelectorInvalid("missing, partial, preconstructed, mutated, or mismatched Stage-2 claim")
    validate_activity_counts(value["zero_start_activity"])
    return dict(value)


class _Stage2ReadinessCapability:
    __slots__ = ("authorization_sha256", "authorization_path", "consumed")

    def __init__(self, authorization_sha256: str, authorization_path: str) -> None:
        self.authorization_sha256 = authorization_sha256
        self.authorization_path = authorization_path
        self.consumed = False


class _Stage2ClaimContinuation:
    __slots__ = (
        "claim_sha256", "authorization_sha256", "catalog_issued",
        "selector_consumed",
    )

    def __init__(self, claim_sha256: str, authorization_sha256: str) -> None:
        self.claim_sha256 = claim_sha256
        self.authorization_sha256 = authorization_sha256
        self.catalog_issued = False
        self.selector_consumed = False


class _CatalogGenerationCapability:
    __slots__ = ("authorization_sha256", "claim_sha256", "consumed", "in_progress")

    def __init__(self, authorization_sha256: str, claim_sha256: str) -> None:
        self.authorization_sha256 = authorization_sha256
        self.claim_sha256 = claim_sha256
        self.consumed = False
        self.in_progress = False


class _ReplicaStartCapability:
    __slots__ = ("authorization_sha256", "claim_sha256", "consumed")

    def __init__(self, authorization_sha256: str, claim_sha256: str) -> None:
        self.authorization_sha256 = authorization_sha256
        self.claim_sha256 = claim_sha256
        self.consumed = False


_ACTIVE_READINESS_CAPABILITY: _Stage2ReadinessCapability | None = None
_ACTIVE_CLAIM_CONTINUATION: _Stage2ClaimContinuation | None = None
_ACTIVE_CATALOG_GENERATION_CAPABILITY: _CatalogGenerationCapability | None = None
_ACTIVE_REPLICA_START_CAPABILITY: _ReplicaStartCapability | None = None


def _issue_stage2_readiness_capability(
    authorization: Mapping[str, Any], authorization_path: Path,
) -> _Stage2ReadinessCapability:
    """Issue only after the runner completes every write-free readiness check."""

    global _ACTIVE_READINESS_CAPABILITY
    if _ACTIVE_READINESS_CAPABILITY is not None:
        raise SelectorInvalid("Stage-2 readiness capability was already issued")
    capability = _Stage2ReadinessCapability(
        sha256_bytes(_canonical_json_bytes(authorization)),
        str(authorization_path.resolve()),
    )
    _ACTIVE_READINESS_CAPABILITY = capability
    return capability


def _discard_stage2_readiness_capability(
    capability: _Stage2ReadinessCapability,
) -> None:
    global _ACTIVE_READINESS_CAPABILITY
    if capability is _ACTIVE_READINESS_CAPABILITY:
        capability.consumed = True
        _ACTIVE_READINESS_CAPABILITY = None


def _issue_stage2_claim_continuation(
    authorization: Mapping[str, Any], claim_path: Path,
) -> _Stage2ClaimContinuation:
    """Issue the in-process exact-once capability only after a secure claim read."""

    global _ACTIVE_CLAIM_CONTINUATION
    if _ACTIVE_CLAIM_CONTINUATION is not None:
        raise SelectorInvalid("Stage-2 claim continuation was already issued")
    claim = authorized_json(authorization, claim_path)
    validate_exact_claim(claim, authorization, phase="stage2_selector_continuation")
    capability = _Stage2ClaimContinuation(
        sha256_authorized_file(authorization, claim_path),
        sha256_bytes(_canonical_json_bytes(authorization)),
    )
    _ACTIVE_CLAIM_CONTINUATION = capability
    return capability


def claim_stage2_namespace(
    authorization: Mapping[str, Any], *,
    readiness_capability: _Stage2ReadinessCapability,
    on_claim_created: Any | None = None,
) -> _Stage2ClaimContinuation:
    """Exclusively create the fixed namespace and issue its one continuation."""

    global _ACTIVE_READINESS_CAPABILITY
    validate_stage2_authorization(authorization)
    authorization_digest = sha256_bytes(_canonical_json_bytes(authorization))
    if (
        not isinstance(readiness_capability, _Stage2ReadinessCapability)
        or readiness_capability is not _ACTIVE_READINESS_CAPABILITY
        or readiness_capability.consumed
        or readiness_capability.authorization_sha256 != authorization_digest
    ):
        raise SelectorInvalid("direct claim API lacks complete write-free readiness")
    readiness_capability.consumed = True
    _ACTIVE_READINESS_CAPABILITY = None
    paths = stage2_paths()
    root = paths["session_root"]
    try:
        validate_absent_destination(root)
    except SelectorInvalid as exc:
        raise SelectorInvalid("preconstructed or replayed Stage-2 namespace is forbidden") from exc
    try:
        os.mkdir(root)
    except FileExistsError as exc:
        raise SelectorInvalid("fixed Stage-2 namespace claim was not exclusive") from exc
    claim = exact_claim(authorization, phase="stage2_selector_continuation")
    write_exclusive(paths["claim"], _canonical_json_bytes(claim) + b"\n")
    if on_claim_created is not None:
        on_claim_created()
    return _issue_stage2_claim_continuation(authorization, paths["claim"])


def validate_claim_continuation(
    authorization: Mapping[str, Any], continuation: _Stage2ClaimContinuation,
) -> None:
    if (
        not isinstance(continuation, _Stage2ClaimContinuation)
        or continuation is not _ACTIVE_CLAIM_CONTINUATION
        or continuation.selector_consumed
        or continuation.authorization_sha256
        != sha256_bytes(_canonical_json_bytes(authorization))
    ):
        raise SelectorInvalid("direct canonical API lacks the exact claim continuation")


def begin_catalog_generation(
    authorization: Mapping[str, Any], continuation: _Stage2ClaimContinuation,
) -> _CatalogGenerationCapability:
    global _ACTIVE_CATALOG_GENERATION_CAPABILITY
    validate_claim_continuation(authorization, continuation)
    if continuation.catalog_issued or _ACTIVE_CATALOG_GENERATION_CAPABILITY is not None:
        raise SelectorInvalid("canonical catalog capability was already issued")
    continuation.catalog_issued = True
    capability = _CatalogGenerationCapability(
        continuation.authorization_sha256, continuation.claim_sha256
    )
    _ACTIVE_CATALOG_GENERATION_CAPABILITY = capability
    return capability


def validate_catalog_generation_capability(
    authorization: Mapping[str, Any], capability: _CatalogGenerationCapability,
) -> None:
    if (
        not isinstance(capability, _CatalogGenerationCapability)
        or capability is not _ACTIVE_CATALOG_GENERATION_CAPABILITY
        or capability.consumed
        or capability.authorization_sha256
        != sha256_bytes(_canonical_json_bytes(authorization))
    ):
        raise SelectorInvalid("direct catalog API lacks the scoped claim capability")


def consume_catalog_generation_capability(
    authorization: Mapping[str, Any], capability: _CatalogGenerationCapability,
) -> None:
    """Consume the one catalog capability before the generator can yield."""

    validate_catalog_generation_capability(authorization, capability)
    capability.consumed = True
    capability.in_progress = True


def validate_catalog_generation_in_progress(
    authorization: Mapping[str, Any], capability: _CatalogGenerationCapability,
) -> None:
    if (
        not isinstance(capability, _CatalogGenerationCapability)
        or capability is not _ACTIVE_CATALOG_GENERATION_CAPABILITY
        or not capability.consumed
        or not capability.in_progress
        or capability.authorization_sha256
        != sha256_bytes(_canonical_json_bytes(authorization))
    ):
        raise SelectorInvalid("final-KEEP generation lacks the active scoped claim catalog iteration")


def finish_catalog_generation(capability: _CatalogGenerationCapability) -> None:
    if capability is _ACTIVE_CATALOG_GENERATION_CAPABILITY:
        capability.in_progress = False


def _issue_replica_start_capability(
    authorization: Mapping[str, Any], claim_path: Path,
) -> _ReplicaStartCapability:
    global _ACTIVE_REPLICA_START_CAPABILITY
    claim = authorized_json(authorization, claim_path)
    validate_exact_claim(claim, authorization, phase="stage2_selector_continuation")
    capability = _ReplicaStartCapability(
        sha256_bytes(_canonical_json_bytes(authorization)),
        sha256_authorized_file(authorization, claim_path),
    )
    _ACTIVE_REPLICA_START_CAPABILITY = capability
    return capability


def _is_reparse(path: Path) -> bool:
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def path_lexists(path: Path) -> bool:
    """Existence check that also observes dangling links and reparse entries."""

    return os.path.lexists(os.fspath(path))


def _validate_path_components(path: Path, *, require_directory: bool) -> Path:
    absolute = Path(os.path.abspath(path))
    component = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        component = component / part
        if not path_lexists(component):
            if require_directory:
                raise SelectorInvalid(f"fixed destination parent is absent: {path}")
            continue
        if component.is_symlink() or _is_reparse(component):
            raise SelectorInvalid("link/junction/reparse destination locator is forbidden")
    if require_directory:
        resolved = path.resolve(strict=True)
        if resolved != absolute or not resolved.is_dir():
            raise SelectorInvalid("fixed destination parent is not an exact directory")
    return absolute


def _validate_existing_directory(path: Path) -> Path:
    return _validate_path_components(path, require_directory=True)


def validate_absent_destination(path: Path) -> None:
    """Validate one fixed write destination without following a dangling alias."""

    if path != Path(os.path.abspath(path)) or ".." in path.parts:
        raise SelectorInvalid("write destination is not the exact fixed locator")
    _validate_existing_directory(path.parent)
    if path_lexists(path):
        if path.is_symlink() or _is_reparse(path):
            raise SelectorInvalid("dangling/link/junction/reparse destination is forbidden")
        raise SelectorInvalid(f"write-once destination already exists: {path}")


def safe_existing_path(path: Path) -> Path:
    text = str(path)
    if not text or any(char in text for char in "*?[") or ".." in path.parts:
        raise SelectorInvalid("glob, empty, and parent-traversal locators are forbidden")
    absolute = Path(os.path.abspath(path))
    component = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        component = component / part
        if path_lexists(component) and (component.is_symlink() or _is_reparse(component)):
            raise SelectorInvalid("link/junction/reparse read locator is forbidden")
    resolved = path.resolve(strict=True)
    if resolved != absolute or not resolved.is_file():
        raise SelectorInvalid("read locator alias or non-regular file is forbidden")
    predecessor = "vsp06_" + "b2_"
    if predecessor in resolved.as_posix().casefold():
        raise SelectorInvalid("predecessor read locator is forbidden")
    return resolved


def authorize_read_path(authorization: Mapping[str, Any], path: Path) -> Path:
    validate_stage2_authorization(authorization)
    resolved = safe_existing_path(path)
    if str(path) != str(resolved) or str(resolved) not in authorization["source_build_read_allowlist"]:
        raise SelectorInvalid("read locator is not the exact authorized canonical path")
    return resolved


def authorized_read_bytes(authorization: Mapping[str, Any], path: Path) -> bytes:
    """Read one exact allowlisted regular file with pre/post-open validation."""

    resolved = authorize_read_path(authorization, path)
    before = os.stat(resolved, follow_symlinks=False)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(resolved, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
        ) != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
            raise SelectorInvalid("authorized file changed between validation and open")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.stat(authorize_read_path(authorization, path), follow_symlinks=False)
    opened_identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    if opened_identity != (
        after_open.st_dev, after_open.st_ino, after_open.st_size, after_open.st_mtime_ns
    ) or opened_identity != (
        after_path.st_dev, after_path.st_ino, after_path.st_size, after_path.st_mtime_ns
    ):
        raise SelectorInvalid("authorized file changed during or after read")
    return b"".join(chunks)


def authorized_json(authorization: Mapping[str, Any], path: Path) -> Mapping[str, Any]:
    try:
        value = _strict_json_loads(
            authorized_read_bytes(authorization, path).decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectorInvalid(f"authorized JSON is invalid: {path}") from exc
    if not isinstance(value, Mapping):
        raise SelectorInvalid(f"JSON root must be an object: {path}")
    return value


def sha256_authorized_file(authorization: Mapping[str, Any], path: Path) -> str:
    return sha256_bytes(authorized_read_bytes(authorization, path))


def load_full_environment_receipt(
    authorization: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Securely load the one externally digested full-environment receipt."""

    validate_stage2_authorization(authorization)
    path = Path(str(authorization["full_environment_receipt_path"]))
    payload = authorized_read_bytes(authorization, path)
    if sha256_bytes(payload) != authorization["full_environment_receipt_sha256"]:
        raise SelectorInvalid("external full-environment receipt digest mismatch")
    try:
        value = _strict_json_loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectorInvalid("external full-environment receipt is invalid JSON") from exc
    if not isinstance(value, Mapping) or set(value) != FULL_ENVIRONMENT_RECEIPT_KEYS:
        raise SelectorInvalid("external full-environment receipt schema is not exact")
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1:
        raise SelectorInvalid("external full-environment receipt schema version is invalid")
    if (
        value.get("torch_distribution_version") != REQUIRED_TORCH
        or value.get("torch_cpu_only") is not True
        or value.get("torch_cuda_version") is not None
        or value.get("torch_cuda_available") is not False
        or value.get("torch_deterministic_algorithms") is not True
        or value.get("torch_deterministic_warn_only") is not False
        or type(value.get("torch_num_threads")) is not int
        or value.get("torch_num_threads") != 1
        or type(value.get("torch_num_interop_threads")) is not int
        or value.get("torch_num_interop_threads") != 1
        or value.get("thread_environment") != THREAD_ENVIRONMENT
    ):
        raise SelectorInvalid("external full-environment Torch/determinism/thread binding is invalid")
    for artifacts, digest_name in (
        (value.get("solver_artifacts"), "solver_artifact_set_sha256"),
        (value.get("torch_native_artifacts"), "torch_native_artifact_set_sha256"),
    ):
        if (
            not isinstance(artifacts, list) or not artifacts
            or any(
                not isinstance(row, list) or len(row) != 2
                or not isinstance(row[0], str) or not Path(row[0]).is_absolute()
                or not isinstance(row[1], str) or len(row[1]) != 64
                or any(char not in "0123456789abcdef" for char in row[1])
                for row in artifacts
            )
            or value.get(digest_name) != sha256_bytes(_canonical_json_bytes(artifacts))
        ):
            raise SelectorInvalid("external full-environment native-artifact binding is invalid")
    for name in ("torch_distribution_inventory_sha256", "torch_build_config_sha256"):
        digest = value.get(name)
        if (
            not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise SelectorInvalid("external full-environment Torch build digest is invalid")
    return authorize_read_path(authorization, path), dict(value)


def source_config_digest_map(
    authorization: Mapping[str, Any], project_root: Path,
) -> dict[str, str]:
    """Seal the exact seven-path final-commit source/configuration surface."""

    result: dict[str, str] = {}
    for relative in SOURCE_CONFIG_RELATIVE_PATHS:
        path = project_root / relative
        result[relative] = sha256_authorized_file(authorization, path)
    if tuple(result) != SOURCE_CONFIG_RELATIVE_PATHS:
        raise SelectorInvalid("seven-path source/config digest map is incomplete")
    return result


def verify_authorized_source_config(
    authorization: Mapping[str, Any], project_root: Path = PROJECT_ROOT,
) -> dict[str, str]:
    """Securely rehash and match the Explorer-audited seven-path map."""

    validate_stage2_authorization(authorization)
    live = source_config_digest_map(authorization, project_root)
    audited = dict(authorization["source_config_digest_map"])
    if live != audited:
        raise SelectorInvalid("live seven-path source/config differs from audited final-commit map")
    digest = sha256_bytes(_canonical_json_bytes(live))
    if digest != authorization["source_config_digest_map_sha256"]:
        raise SelectorInvalid("live seven-path source/config map digest mismatch")
    return live


class SelectorInvalid(RuntimeError):
    """Fail-closed selector/config/lifecycle error."""


def _reject_duplicate_object_pairs(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SelectorInvalid(f"duplicate JSON object key is forbidden: {key}")
        result[key] = value
    return result


def _strict_json_loads(payload: str) -> Any:
    return json.loads(payload, object_pairs_hook=_reject_duplicate_object_pairs)


def validate_selector_receipt_schema(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping) or set(value) != SELECTOR_RECEIPT_KEYS:
        raise SelectorInvalid("selector receipt key schema is not exact")
    if type(value.get("replica_count")) is not int or value.get("replica_count") != 2:
        raise SelectorInvalid("selector receipt replica count is not an exact integer")
    if not _exact_json_equal(
        value.get("activity_accounting"),
        {"sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0},
    ):
        raise SelectorInvalid("selector receipt activity accounting is not type-exact")
    validate_activity_counts(value.get("activity_counts"))


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _exact_json_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, Mapping):
        return set(left) == set(right) and all(
            _exact_json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _exact_json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
        raise SelectorInvalid(f"{field} must be an NFC string")
    return value


def canonical_tuple_bytes(row: Mapping[str, Any]) -> bytes:
    """Serialize one catalog tuple as a fixed-schema canonical JSON array."""

    if not isinstance(row, Mapping) or tuple(row) != TUPLE_FIELDS:
        raise SelectorInvalid("catalog tuple fields do not match declared order")
    integers = {"retention_length", "y", "reset_y", "target_identity", "target_version", "nonce"}
    strings = set(TUPLE_FIELDS) - integers - {"decoy_sequence"}
    for field in integers:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SelectorInvalid(f"{field} must be a nonnegative integer")
    for field in strings:
        _strict_text(row[field], field)
    decoys = row["decoy_sequence"]
    if not isinstance(decoys, list) or not decoys:
        raise SelectorInvalid("decoy_sequence must be a nonempty list")
    normalized_decoys: list[list[Any]] = []
    for index, decoy in enumerate(decoys):
        if (
            not isinstance(decoy, list)
            or len(decoy) != 4
            or any(isinstance(decoy[i], bool) or not isinstance(decoy[i], int) for i in (0, 1, 2))
            or not isinstance(decoy[3], bool)
        ):
            raise SelectorInvalid(f"decoy_sequence[{index}] has invalid schema")
        normalized_decoys.append([int(decoy[0]), int(decoy[1]), int(decoy[2]), decoy[3]])
    positional = [normalized_decoys if field == "decoy_sequence" else row[field] for field in TUPLE_FIELDS]
    return _canonical_json_bytes(positional)


def bucket_for_tuple(payload: bytes) -> int:
    return hashlib.sha256(SALT.encode("utf-8") + payload).digest()[0] % 8


def split_for_bucket(bucket: int) -> str:
    if isinstance(bucket, bool) or not isinstance(bucket, int) or not 0 <= bucket <= 7:
        raise SelectorInvalid("bucket must be an integer in 0..7")
    return "train" if bucket <= 5 else "calibration" if bucket == 6 else "evaluation"


def decision_key(payload: bytes) -> bytes:
    return hashlib.sha256(DECISION_PREFIX + payload).digest()


@dataclass(frozen=True)
class CatalogRow:
    source_index: int
    tuple_value: Mapping[str, Any]
    tuple_bytes: bytes
    tuple_sha256: str
    bucket: int
    split: str
    decision_key: bytes


def parse_catalog(raw: Mapping[str, Any]) -> tuple[CatalogRow, ...]:
    if (
        not isinstance(raw, Mapping)
        or raw.get("catalog_id") != CATALOG_ID
        or raw.get("salt") != SALT
        or set(raw) != {"catalog_id", "salt", "rows"}
        or not isinstance(raw.get("rows"), list)
        or not raw["rows"]
    ):
        raise SelectorInvalid("raw catalog envelope is invalid")

    parsed: list[CatalogRow] = []
    seen: set[bytes] = set()
    for index, row in enumerate(raw["rows"]):
        payload = canonical_tuple_bytes(row)
        if payload in seen:
            raise SelectorInvalid("catalog tuples are not unique")
        seen.add(payload)
        bucket = bucket_for_tuple(payload)
        parsed.append(
            CatalogRow(
                source_index=index,
                tuple_value=dict(row),
                tuple_bytes=payload,
                tuple_sha256=sha256_bytes(payload),
                bucket=bucket,
                split=split_for_bucket(bucket),
                decision_key=decision_key(payload),
            )
        )
    canonical = tuple(sorted(parsed, key=lambda item: item.tuple_bytes))
    if tuple(item.tuple_bytes for item in canonical) != tuple(
        sorted(item.tuple_bytes for item in parsed)
    ):
        raise SelectorInvalid("catalog canonical ordering failed")
    return canonical


def _validate_predicate(predicate: Mapping[str, Any]) -> None:
    if not isinstance(predicate, Mapping) or set(predicate) - {"eq", "in"}:
        raise SelectorInvalid("ledger predicate has unsupported operators")
    if not predicate:
        raise SelectorInvalid("ledger predicate may not be empty")
    for operator, clauses in predicate.items():
        if not isinstance(clauses, Mapping) or not clauses:
            raise SelectorInvalid("ledger predicate clauses are invalid")
        for field, value in clauses.items():
            if field not in TUPLE_FIELDS and field not in {"split", "bucket"}:
                raise SelectorInvalid(f"ledger predicate field is unknown: {field}")
            if operator == "in" and (not isinstance(value, list) or not value):
                raise SelectorInvalid("ledger 'in' values must be a nonempty list")


def parse_ledger(raw: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    required = {"ledger_id", "equation_semantics", "equation_templates", "family_counts", "ledger_digest"}
    if not isinstance(raw, Mapping) or set(raw) != required or raw.get("ledger_id") != LEDGER_ID:
        raise SelectorInvalid("raw target ledger envelope is invalid")
    digest_body = {key: value for key, value in raw.items() if key != "ledger_digest"}
    if raw["ledger_digest"] != sha256_bytes(_canonical_json_bytes(digest_body)):
        raise SelectorInvalid("target ledger digest mismatch")
    if raw.get("equation_semantics") != "sum(integer_coefficient * selected_row_indicator) == integer_rhs":
        raise SelectorInvalid("target ledger semantics changed")
    templates = raw.get("equation_templates")
    if not isinstance(templates, list) or not templates:
        raise SelectorInvalid("target ledger has no equation templates")
    equations: list[Mapping[str, Any]] = []
    def substitute(value: Any, bindings: Mapping[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            if value[1:] not in bindings:
                raise SelectorInvalid("ledger template references an unknown axis")
            return bindings[value[1:]]
        if isinstance(value, list):
            return [substitute(item, bindings) for item in value]
        if isinstance(value, Mapping):
            return {key: substitute(item, bindings) for key, item in value.items()}
        return value
    for template in templates:
        if not isinstance(template, Mapping) or set(template) != {"name_template", "family", "axes", "terms", "rhs"}:
            raise SelectorInvalid("ledger equation-template schema is invalid")
        axes = template["axes"]
        if not isinstance(axes, Mapping) or any(not isinstance(values, list) or not values for values in axes.values()):
            raise SelectorInvalid("ledger equation-template axes are invalid")
        axis_names = tuple(axes)
        for values in product(*(axes[name] for name in axis_names)):
            bindings = dict(zip(axis_names, values))
            equations.append({
                "name": str(template["name_template"]).format(**bindings),
                "family": template["family"],
                "terms": substitute(template["terms"], bindings),
                "rhs": substitute(template["rhs"], bindings),
            })
    names: set[str] = set()
    observed_families: dict[str, int] = {}
    for equation in equations:
        if not isinstance(equation, Mapping) or set(equation) != {"name", "family", "terms", "rhs"}:
            raise SelectorInvalid("ledger equation schema is invalid")
        name = _strict_text(equation["name"], "equation.name")
        family = _strict_text(equation["family"], "equation.family")
        if name in names:
            raise SelectorInvalid("ledger equation names are not unique")
        names.add(name)
        rhs = equation["rhs"]
        if isinstance(rhs, bool) or not isinstance(rhs, int):
            raise SelectorInvalid("ledger RHS must be integer")
        terms = equation["terms"]
        if not isinstance(terms, list) or not terms:
            raise SelectorInvalid("ledger equation must have terms")
        for term in terms:
            if not isinstance(term, Mapping) or set(term) != {"coefficient", "predicate"}:
                raise SelectorInvalid("ledger term schema is invalid")
            coefficient = term["coefficient"]
            if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient == 0:
                raise SelectorInvalid("ledger coefficients must be nonzero integers")
            _validate_predicate(term["predicate"])
        observed_families[family] = observed_families.get(family, 0) + 1
    if raw["family_counts"] != observed_families:
        raise SelectorInvalid("ledger family counts mismatch")
    return tuple(equations)


def _field(row: CatalogRow, name: str) -> Any:
    if name == "split":
        return row.split
    if name == "bucket":
        return row.bucket
    return row.tuple_value[name]


def predicate_matches(row: CatalogRow, predicate: Mapping[str, Any]) -> bool:
    for field, expected in predicate.get("eq", {}).items():
        if _field(row, field) != expected:
            return False
    for field, allowed in predicate.get("in", {}).items():
        if _field(row, field) not in allowed:
            return False
    return True


def compile_equations(
    rows: Sequence[CatalogRow], equations: Sequence[Mapping[str, Any]]
) -> tuple[tuple[str, str, tuple[tuple[int, int], ...], int], ...]:
    referenced = {
        field
        for equation in equations
        for term in equation["terms"]
        for clauses in term["predicate"].values()
        for field in clauses
    }
    inverted: dict[str, dict[bytes, set[int]]] = {field: {} for field in referenced}
    for index, row in enumerate(rows):
        for field in referenced:
            key = _canonical_json_bytes(_field(row, field))
            inverted[field].setdefault(key, set()).add(index)

    def matching(predicate: Mapping[str, Any]) -> set[int]:
        candidates: list[set[int]] = []
        for field, expected in predicate.get("eq", {}).items():
            candidates.append(inverted[field].get(_canonical_json_bytes(expected), set()))
        for field, allowed in predicate.get("in", {}).items():
            union: set[int] = set()
            for value in allowed:
                union.update(inverted[field].get(_canonical_json_bytes(value), set()))
            candidates.append(union)
        if not candidates:
            raise SelectorInvalid("ledger predicate has no indexed clauses")
        result = set(candidates[0])
        for candidate in candidates[1:]:
            result.intersection_update(candidate)
        return result

    compiled = []
    for equation in equations:
        coefficients: dict[int, int] = {}
        for term in equation["terms"]:
            coefficient = int(term["coefficient"])
            for index in matching(term["predicate"]):
                coefficients[index] = coefficients.get(index, 0) + coefficient
        sparse = tuple((index, value) for index, value in sorted(coefficients.items()) if value)
        if not sparse:
            raise SelectorInvalid(f"ledger equation has empty support: {equation['name']}")
        compiled.append((equation["name"], equation["family"], sparse, int(equation["rhs"])))
    return tuple(compiled)


def canonical_order(rows: Sequence[CatalogRow]) -> tuple[int, ...]:
    return tuple(
        sorted(
            range(len(rows)),
            key=lambda index: (rows[index].decision_key, rows[index].tuple_bytes),
        )
    )



def validate_final_keep_support(rows: Sequence[CatalogRow]) -> dict[str, Any]:
    """Reject structurally impossible final-KEEP support before CP-SAT."""

    final_rows = [row for row in rows if row.tuple_value["consumer"] == "final_keep"]
    expected_seeds = {"primary_1", "primary_2", "primary_3", "primary_4"}
    groups: dict[tuple[str, str], list[CatalogRow]] = {}
    for row in final_rows:
        value = row.tuple_value
        if row.split != "evaluation" or value["branch"] != "KEEP" or value["retention_length"] != 6:
            raise SelectorInvalid("final-KEEP row is structurally ineligible")
        groups.setdefault((value["seed_row"], value["quartet_base"]), []).append(row)
    if {seed for seed, _base in groups} != expected_seeds:
        raise SelectorInvalid("final-KEEP seed support is incomplete")
    structural_fields = tuple(field for field in TUPLE_FIELDS if field not in {"y", "nonce"})
    for key, group in groups.items():
        if len(group) != 4 or {row.tuple_value["y"] for row in group} != {0, 1, 2, 3}:
            raise SelectorInvalid(f"final-KEEP quartet is incomplete: {key}")
        reference = tuple(group[0].tuple_value[field] for field in structural_fields)
        if any(tuple(row.tuple_value[field] for field in structural_fields) != reference for row in group[1:]):
            raise SelectorInvalid(f"final-KEEP quartet is not structurally identical: {key}")
    event_domain = {"target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster"}
    for seed in sorted(expected_seeds):
        seed_rows = [row for row in final_rows if row.tuple_value["seed_row"] == seed]
        seed_groups = {row.tuple_value["quartet_base"] for row in seed_rows}
        if len(seed_rows) != 256 or len(seed_groups) != 64:
            raise SelectorInvalid("final-KEEP requires exactly 64 complete quartets per seed")
        for field, domain in (
            ("target_identity", set(range(4))),
            ("target_version", set(range(4))),
            ("event_type", event_domain),
        ):
            counts = {value: sum(row.tuple_value[field] == value for row in seed_rows) for value in domain}
            if set(counts.values()) != {64}:
                raise SelectorInvalid(f"final-KEEP {field} support is not exactly balanced")
        decoy_counts: dict[bytes, int] = {}
        for row in seed_rows:
            key = _canonical_json_bytes(row.tuple_value["decoy_sequence"])
            decoy_counts[key] = decoy_counts.get(key, 0) + 1
        if len(decoy_counts) != 4 or set(decoy_counts.values()) != {64}:
            raise SelectorInvalid("final-KEEP ordered-decoy support is not exactly balanced")
    return {
        "selected_count_required": 1024,
        "quartet_count": len(groups),
        "per_seed_quartets": 64,
        "balanced_fields": ["target_identity", "target_version", "event_type", "decoy_sequence"],
        "digest": sha256_bytes(_canonical_json_bytes(sorted((key[0], key[1]) for key in groups))),
    }


def validate_catalog_structural_support(rows: Sequence[CatalogRow]) -> dict[str, Any]:
    """Necessary frozen count/marginal support check before model construction."""

    final_report = validate_final_keep_support(rows)
    minima: list[tuple[str, Mapping[str, Any], int]] = []
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for branch, target in (("KEEP", 384), ("RESET", 64), ("CURRENT", 64)):
            for length in (4, 8):
                for y in range(4):
                    minima.append((
                        f"primary/{seed}/{branch}/{length}/{y}",
                        {"consumer": "primary_fit", "seed_row": seed, "branch": branch,
                         "retention_length": length, "y": y}, target,
                    ))
    for consumer, target in (("calibration_fit", 128), ("calibration_check", 32)):
        for y in range(4):
            minima.append((f"{consumer}/{y}", {"consumer": consumer, "y": y}, target))
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for panel in ("0", "512", "1024", "1536", "2048", "2560", "3072", "4096"):
            for branch, target in (("KEEP", 16), ("RESET", 8), ("CURRENT", 8)):
                for y in range(4):
                    minima.append((
                        f"checkpoint/{seed}/{panel}/{branch}/{y}",
                        {"consumer": "checkpoint", "seed_row": seed, "panel": panel,
                         "branch": branch, "y": y}, target,
                    ))
    for name, clauses, target in minima:
        support = [row for row in rows if all(row.tuple_value[field] == value for field, value in clauses.items())]
        if len(support) < target:
            raise SelectorInvalid(f"canonical structural support below target: {name}")
        for field in ("target_identity", "target_version", "event_type", "decoy_sequence"):
            values = {_canonical_json_bytes(row.tuple_value[field]) for row in support}
            if len(values) != 4:
                raise SelectorInvalid(f"canonical marginal support incomplete: {name}/{field}")
        if clauses.get("branch") == "RESET":
            for reset_y in range(4):
                if sum(row.tuple_value["reset_y"] == reset_y for row in support) < target // 4:
                    raise SelectorInvalid(f"fresh reset-Y support incomplete: {name}/{reset_y}")
    reset_strata = []
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for length in (4, 8):
            reset_strata.append((
                f"primary/{seed}/{length}",
                {"consumer": "primary_fit", "seed_row": seed, "branch": "RESET", "retention_length": length},
                16,
            ))
        for panel in ("0", "512", "1024", "1536", "2048", "2560", "3072", "4096"):
            reset_strata.append((
                f"checkpoint/{seed}/{panel}",
                {"consumer": "checkpoint", "seed_row": seed, "panel": panel, "branch": "RESET"},
                2,
            ))
    for name, clauses, minimum in reset_strata:
        support = [row for row in rows if all(row.tuple_value[field] == value for field, value in clauses.items())]
        for reset_y in range(4):
            for field in ("target_identity", "target_version", "event_type", "decoy_sequence"):
                values = {_canonical_json_bytes(row.tuple_value[field]) for row in support}
                for value in values:
                    count = sum(
                        row.tuple_value["reset_y"] == reset_y
                        and _canonical_json_bytes(row.tuple_value[field]) == value
                        for row in support
                    )
                    if count < minimum:
                        raise SelectorInvalid(f"fresh reset-Y pairwise support incomplete: {name}/{reset_y}/{field}")
    return {
        "final_keep": final_report,
        "minimum_strata_checked": len(minima),
        "reset_pairwise_strata_checked": len(reset_strata),
        "catalog_row_count": len(rows),
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = _strict_json_loads(stream.read())
    if not isinstance(value, Mapping):
        raise SelectorInvalid(f"JSON root must be an object: {path}")
    return value


def _ortools_bindings() -> tuple[Any, Any, Any]:
    if sys.version_info[:2] != REQUIRED_PYTHON:
        raise SelectorInvalid("CPython 3.11 ABI is required")
    try:
        version = importlib.metadata.version("ortools")
    except importlib.metadata.PackageNotFoundError as exc:
        raise SelectorInvalid(f"ortools=={REQUIRED_ORTOOLS} is not installed") from exc
    if version != REQUIRED_ORTOOLS:
        raise SelectorInvalid(f"ortools build mismatch: {version!r}")
    try:
        from ortools.sat.python import cp_model
        from ortools.sat import sat_parameters_pb2
        import ortools
    except Exception as exc:
        raise SelectorInvalid("pinned OR-Tools CP-SAT import failed") from exc
    return cp_model, sat_parameters_pb2, ortools


def _parameters(sat_parameters_pb2: Any) -> Any:
    parameters = sat_parameters_pb2.SatParameters()
    for name, value in PARAMETER_ASSIGNMENTS.items():
        if name == "search_branching":
            value = sat_parameters_pb2.SatParameters.FIXED_SEARCH
        setattr(parameters, name, value)
    return parameters


def selector_environment(stage2_authorization: Mapping[str, Any]) -> dict[str, Any]:
    validate_stage2_authorization(stage2_authorization)
    executable = authorize_read_path(stage2_authorization, Path(sys.executable))
    executable_digest = sha256_authorized_file(stage2_authorization, executable)
    cp_model, sat_parameters_pb2, ortools = _ortools_bindings()
    del cp_model
    parameters = _parameters(sat_parameters_pb2)
    distribution = importlib.metadata.distribution("ortools")
    inventory = distribution.files
    if inventory is None:
        raise SelectorInvalid("OR-Tools distribution metadata inventory is absent")
    artifacts = []
    for item in sorted(inventory, key=lambda entry: str(entry)):
        if Path(str(item)).suffix.lower() not in {".pyd", ".so", ".dll"}:
            continue
        artifact = authorize_read_path(
            stage2_authorization, Path(distribution.locate_file(item)).resolve()
        )
        artifacts.append(artifact)
    if not artifacts:
        raise SelectorInvalid("OR-Tools native solver artifact is absent")
    artifact_rows = [
        [str(path), sha256_authorized_file(stage2_authorization, path)]
        for path in artifacts
    ]
    parameter_bytes = parameters.SerializeToString(deterministic=True)
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": str(executable),
        "python_executable_sha256": executable_digest,
        "ortools_version": REQUIRED_ORTOOLS,
        "ortools_source_tag": "v9.12",
        "solver_artifacts": artifact_rows,

        "solver_artifact_set_sha256": sha256_bytes(_canonical_json_bytes(artifact_rows)),
        "sat_parameters_sha256": sha256_bytes(parameter_bytes),
        "sat_parameters_hex": parameter_bytes.hex(),
        "sat_parameter_assignments": dict(PARAMETER_ASSIGNMENTS),
        "sat_parameter_assignments_sha256": sha256_bytes(
            _canonical_json_bytes(PARAMETER_ASSIGNMENTS)
        ),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
    }


def validate_selector_environment_receipt(
    stage2_authorization: Mapping[str, Any], receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate live CPython/OR-Tools/parameters against the external receipt."""

    live = selector_environment(stage2_authorization)
    if any(
        not _exact_json_equal(receipt.get(name), value)
        for name, value in live.items()
    ):
        raise SelectorInvalid("live CPython/OR-Tools environment differs from external receipt")
    return live


def source_bindings(stage2_authorization: Mapping[str, Any]) -> dict[str, Any]:
    digest_map = verify_authorized_source_config(stage2_authorization, PROJECT_ROOT)
    return {
        "source_config_digest_map": dict(stage2_authorization["source_config_digest_map"]),
        "source_config_digest_map_sha256": stage2_authorization["source_config_digest_map_sha256"],
        "selector_source_sha256": digest_map[SOURCE_CONFIG_RELATIVE_PATHS[0]],
        "verifier_source_sha256": digest_map[SOURCE_CONFIG_RELATIVE_PATHS[1]],
    }


def _manifest_body(
    rows: Sequence[CatalogRow], vector: Sequence[int], bindings: Mapping[str, Any]
) -> dict[str, Any]:
    selected = [row for row, value in zip(rows, vector) if value == 1]
    selected_rows = [
        {
            "tuple": dict(row.tuple_value),
            "tuple_sha256": row.tuple_sha256,
            "bucket": row.bucket,
            "split": row.split,
        }
        for row in selected
    ]
    order_digest = sha256_bytes(
        _canonical_json_bytes([item["tuple_sha256"] for item in selected_rows])
    )
    return {
        "manifest_id": "vsp06_b2r1_authenticated_partner_recall_manifest_v1",
        "treatment": TREATMENT_ID,
        "selector_identity": SELECTOR_ID,
        "bindings": dict(bindings),
        "selected_count": len(selected_rows),
        "selected_rows": selected_rows,
        "common_two_arm_order_digest": order_digest,
        "rank_claim": False,
    }


def solve_replica(
    catalog_path: Path, ledger_path: Path, bindings_path: Path,
    stage2_authorization: Mapping[str, Any], *, claim_path: Path,
    start_capability: _ReplicaStartCapability,
) -> dict[str, Any]:
    global _ACTIVE_REPLICA_START_CAPABILITY
    validate_stage2_authorization(stage2_authorization)
    claim = authorized_json(stage2_authorization, claim_path)
    validate_exact_claim(
        claim, stage2_authorization, phase="stage2_selector_continuation"
    )
    if (
        not isinstance(start_capability, _ReplicaStartCapability)
        or start_capability is not _ACTIVE_REPLICA_START_CAPABILITY
        or start_capability.consumed
        or start_capability.authorization_sha256
        != sha256_bytes(_canonical_json_bytes(stage2_authorization))
        or start_capability.claim_sha256
        != sha256_authorized_file(stage2_authorization, claim_path)
    ):
        raise SelectorInvalid("replica solve lacks validated claim and mandatory start token")
    start_capability.consumed = True
    _ACTIVE_REPLICA_START_CAPABILITY = None
    catalog_path = authorize_read_path(stage2_authorization, catalog_path)
    ledger_path = authorize_read_path(stage2_authorization, ledger_path)
    bindings_path = authorize_read_path(stage2_authorization, bindings_path)
    raw_catalog = authorized_json(stage2_authorization, catalog_path)
    raw_ledger = authorized_json(stage2_authorization, ledger_path)
    expected_bindings = authorized_json(stage2_authorization, bindings_path)
    rows = parse_catalog(raw_catalog)
    equations = parse_ledger(raw_ledger)
    validate_catalog_structural_support(rows)
    compiled = compile_equations(rows, equations)
    declared_expected = expected_bindings.get("expected")
    if (
        not isinstance(declared_expected, Mapping)
        or not isinstance(declared_expected.get("universe_spec_sha256"), str)
        or not isinstance(declared_expected.get("sealed_path_schema"), Mapping)
        or not isinstance(declared_expected["sealed_path_schema"].get("stage2_authorization"), str)
    ):
        raise SelectorInvalid("independent universe binding absent")
    environment_path, full_environment = load_full_environment_receipt(stage2_authorization)
    validate_selector_environment_receipt(stage2_authorization, full_environment)
    sealed_schema = _sealed_path_schema(
        stage2_paths(),
        authorization_path=Path(declared_expected["sealed_path_schema"]["stage2_authorization"]),
        authorization=stage2_authorization,
    )
    actual = {
        **source_bindings(stage2_authorization),
        "catalog_sha256": sha256_authorized_file(stage2_authorization, catalog_path),
        "ledger_sha256": sha256_authorized_file(stage2_authorization, ledger_path),
        "final_commit": stage2_authorization["final_commit"],
        "stage2_authorization_sha256": sha256_bytes(_canonical_json_bytes(stage2_authorization)),
        "universe_spec_sha256": declared_expected["universe_spec_sha256"],
        "sealed_path_schema": sealed_schema,
        "sealed_path_schema_sha256": sha256_bytes(
            _canonical_json_bytes(sealed_schema)
        ),
        "full_environment_receipt_path": str(environment_path),
        "full_environment_receipt_sha256": stage2_authorization["full_environment_receipt_sha256"],
        **full_environment,
    }
    expected = declared_expected
    if not isinstance(expected, Mapping) or dict(expected) != actual:
        raise SelectorInvalid("source/build/input/parameter binding mismatch")

    cp_model, sat_parameters_pb2, _ortools = _ortools_bindings()
    model = cp_model.CpModel()
    variables = [model.NewBoolVar(f"x_{index}") for index in range(len(rows))]
    for _name, _family, sparse, rhs in compiled:
        model.Add(sum(coefficient * variables[index] for index, coefficient in sparse) == rhs)
    order = canonical_order(rows)
    model.AddDecisionStrategy(
        [variables[index] for index in order],
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MAX_VALUE,
    )
    solver = cp_model.CpSolver()
    solver.parameters.CopyFrom(_parameters(sat_parameters_pb2))
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    if status_name not in {"FEASIBLE", "OPTIMAL"}:
        raise SelectorInvalid(f"non-admissible CP-SAT terminal status: {status_name}")
    vector = [int(solver.Value(variable)) for variable in variables]
    if len(vector) != len(rows) or any(value not in (0, 1) for value in vector):
        raise SelectorInvalid("CP-SAT returned a partial/nonbinary witness")
    manifest = _manifest_body(rows, vector, actual)
    return {
        "selector_identity": SELECTOR_ID,
        "terminal_status": status_name,
        "membership_vector": vector,
        "membership_vector_sha256": sha256_bytes(_canonical_json_bytes(vector)),
        "selected_tuple_sha256": [row.tuple_sha256 for row, value in zip(rows, vector) if value],
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(_canonical_json_bytes(manifest)),
        "solver_response_stats": solver.ResponseStats(),
    }


def compare_replicas(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "selector_identity",
        "terminal_status",
        "membership_vector",
        "membership_vector_sha256",
        "selected_tuple_sha256",
        "manifest",
        "manifest_sha256",
    )
    if left.get("terminal_status") not in {"FEASIBLE", "OPTIMAL"} or any(left.get(key) != right.get(key) for key in keys):
        raise SelectorInvalid("two mandatory cold replicas disagree")
    vector = left.get("membership_vector")
    if not isinstance(vector, list) or not vector or any(
        type(value) is not int or value not in (0, 1) for value in vector
    ):
        raise SelectorInvalid("replica witness is incomplete or nonbinary")
    return dict(left)


def write_exclusive(path: Path, payload: bytes) -> None:
    if path_lexists(path):
        raise SelectorInvalid(f"write-once destination already exists: {path}")
    _validate_path_components(path.parent, require_directory=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    _validate_existing_directory(path.parent)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as exc:
        raise SelectorInvalid(f"write-once destination already exists: {path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    write_exclusive(path, _canonical_json_bytes(value) + b"\n")


def write_json_exclusive_verified(
    authorization: Mapping[str, Any], path: Path, value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Write canonical JSON once and prove its exact bytes through the secure reader."""

    payload = _canonical_json_bytes(value) + b"\n"
    write_exclusive(path, payload)
    reloaded = authorized_read_bytes(authorization, path)
    if reloaded != payload or sha256_bytes(reloaded) != sha256_bytes(payload):
        raise SelectorInvalid("durable JSON raw-byte reload mismatch")
    try:
        parsed = _strict_json_loads(reloaded.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectorInvalid("durable JSON reload is invalid") from exc
    if not isinstance(parsed, Mapping) or not _exact_json_equal(dict(parsed), dict(value)):
        raise SelectorInvalid("durable JSON type-exact reload mismatch")
    return parsed


def _apply_resource_cap(process: subprocess.Popen[bytes]) -> Any:
    """Bind one logical CPU and 4096 MiB; child waits for a start token."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        kernel32.SetProcessAffinityMask.restype = wintypes.BOOL
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process_handle = wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
        if not kernel32.SetProcessAffinityMask(process_handle, 1):
            raise SelectorInvalid("failed to enforce one-logical-CPU affinity")

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]


        class EXTENDED(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BASIC),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            raise SelectorInvalid("failed to create Windows selector job")
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x100 | 0x2000  # kill-on-close + process-memory
        info.ProcessMemoryLimit = MEMORY_BYTES
        if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            kernel32.CloseHandle(job)
            raise SelectorInvalid("failed to enforce selector memory cap")
        if not kernel32.AssignProcessToJobObject(job, process_handle):
            kernel32.CloseHandle(job)
            raise SelectorInvalid("failed to assign selector resource job")
        return (kernel32, job)
    try:
        os.sched_setaffinity(process.pid, {min(os.sched_getaffinity(0))})
    except (AttributeError, OSError) as exc:
        raise SelectorInvalid("failed to enforce one-logical-CPU affinity") from exc
    return None


def _release_resource_cap(token: Any) -> None:
    if token is not None:
        kernel32, job = token
        kernel32.CloseHandle(job)


def _self_memory_cap() -> None:
    if os.name == "nt":
        return
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    except (ImportError, OSError, ValueError) as exc:
        raise SelectorInvalid("failed to enforce selector 4096-MiB memory cap") from exc
    if soft != MEMORY_BYTES or hard != MEMORY_BYTES:
        raise SelectorInvalid("selector memory cap did not bind exactly")


def _run_cold_replica(
    *, selector_path: Path, catalog_path: Path, ledger_path: Path,
    bindings_path: Path, output_path: Path, authorization_path: Path,
    authorization: Mapping[str, Any],
    on_process_started: Any,
) -> Mapping[str, Any]:
    command = [
        sys.executable, "-I", "-B", str(selector_path), "replica",
        "--catalog", str(catalog_path), "--ledger", str(ledger_path),
        "--bindings", str(bindings_path), "--output", str(output_path),
        "--stage2-authorization", str(authorization_path),
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    on_process_started()
    cap = None
    try:
        cap = _apply_resource_cap(process)
        assert process.stdin is not None
        process.stdin.write(b"START\n")
        process.stdin.flush()
        process.stdin.close()
        process.stdin = None
        stdout, stderr = process.communicate(timeout=WALL_SECONDS)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise SelectorInvalid("cold replica exceeded 1800 wall seconds") from exc
    except Exception:
        process.kill()
        process.communicate()
        raise
    finally:
        _release_resource_cap(cap)
    elapsed = time.monotonic() - started
    write_exclusive(output_path.with_name(output_path.stem + ".stdout.log"), stdout)
    write_exclusive(output_path.with_name(output_path.stem + ".stderr.log"), stderr)
    if process.returncode != 0:
        raise SelectorInvalid(
            "cold replica failed closed: "
            + stderr.decode("utf-8", errors="replace")[:500]
        )
    telemetry = {
        "wall_seconds": elapsed,
        "wall_cap_seconds": WALL_SECONDS,
        "logical_cpu_cap": 1,
        "process_memory_cap_bytes": MEMORY_BYTES,
        "return_code": process.returncode,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
    }
    _write_json_exclusive(
        output_path.with_name(output_path.stem + ".resource.json"), telemetry
    )
    result = dict(authorized_json(authorization, output_path))
    result["resource_telemetry"] = telemetry
    return result


def _sealed_path_schema(
    paths: Mapping[str, Path], *, authorization_path: Path | None = None,
    authorization: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    names = (
        "claim", "catalog", "universe_spec", "ledger", "bindings", "replica_1",
        "replica_2", "witness", "proposed_manifest", "verifier_report", "receipt",
        "manifest", "stage2_failure", "full_claim", "full_failure", "result",
        "operator_receipt",
        "activity_claim", "activity_catalog", "activity_replica_1",
        "activity_replica_2", "activity_verifier", "activity_witness",
        "activity_manifest", "activity_full_claim", "activity_full_calibration",
        "activity_full_primary_1", "activity_full_primary_2",
        "activity_full_primary_3", "activity_full_primary_4",
        "activity_full_complete",
    )
    result = {name: str(paths[name].resolve()) for name in names}
    for name in sorted(paths):
        if name.startswith("checkpoint_"):
            result[name] = str(paths[name].resolve())
    for replica in (1, 2):
        base = paths[f"replica_{replica}"]
        result[f"replica_{replica}_stdout"] = str(
            base.with_name(base.stem + ".stdout.log").resolve()
        )
        result[f"replica_{replica}_stderr"] = str(
            base.with_name(base.stem + ".stderr.log").resolve()
        )
        result[f"replica_{replica}_resource"] = str(
            base.with_name(base.stem + ".resource.json").resolve()
        )
    if authorization_path is not None:
        result["stage2_authorization"] = str(authorization_path.resolve())
    if authorization is not None:
        result["full_environment_receipt"] = str(
            Path(str(authorization["full_environment_receipt_path"])).resolve()
        )
    return result


SELECTOR_SEALED_OBJECT_NAMES = frozenset({
    "stage2_authorization", "full_environment_receipt", "claim", "catalog",
    "universe_spec", "ledger", "bindings", "replica_1", "replica_2",
    "replica_1_stdout", "replica_1_stderr", "replica_1_resource",
    "replica_2_stdout", "replica_2_stderr", "replica_2_resource", "witness",
    "proposed_manifest", "verifier_report", "manifest", "activity_claim",
    "activity_catalog", "activity_replica_1", "activity_replica_2",
    "activity_verifier", "activity_witness", "activity_manifest",
})


def output_paths_must_be_absent(paths: Mapping[str, Path]) -> None:
    for name in ("session_root", "result", "operator_receipt"):
        validate_absent_destination(paths[name])


def persist_activity_snapshot(
    authorization: Mapping[str, Any], paths: Mapping[str, Path], phase: str,
    activity: Mapping[str, Any],
) -> dict[str, Any]:
    key = f"activity_{phase}"
    if key not in paths:
        raise SelectorInvalid("unknown Stage-2 activity phase")
    counts = validate_activity_counts(activity)
    envelope = {"phase": phase, "activity_counts": counts}
    loaded = write_json_exclusive_verified(authorization, paths[key], envelope)
    return dict(loaded)


def validate_pre_replica_catalog_snapshot(
    authorization: Mapping[str, Any], paths: Mapping[str, Path],
    expected_catalog: Mapping[str, Any], expected_activity: Mapping[str, Any],
) -> tuple[tuple[CatalogRow, ...], dict[str, int]]:
    """Securely prove one complete catalog attempt before any replica starts."""

    catalog = authorized_json(authorization, paths["catalog"])
    snapshot = authorized_json(authorization, paths["activity_catalog"])
    if not _exact_json_equal(dict(catalog), dict(expected_catalog)):
        raise SelectorInvalid("durable catalog differs from the generated catalog")
    if (
        not isinstance(snapshot, Mapping)
        or set(snapshot) != {"phase", "activity_counts"}
        or snapshot.get("phase") != "catalog"
    ):
        raise SelectorInvalid("durable catalog activity snapshot is malformed")
    counts = validate_activity_counts(snapshot["activity_counts"])
    expected_counts = validate_activity_counts(expected_activity)
    rows = parse_catalog(catalog)
    if (
        not _exact_json_equal(counts, expected_counts)
        or counts["canonical_generator_calls"] != 1
        or counts["canonical_rows_observed"] != len(rows)
        or len(rows) != len(expected_catalog.get("rows", ()))
    ):
        raise SelectorInvalid("catalog call/observed-row/cardinality proof failed")
    return rows, counts


def _require_exhaustive_allowlist(
    authorization: Mapping[str, Any], authorization_path: Path,
    paths: Mapping[str, Path], environment: Mapping[str, Any],
) -> None:
    required = {
        str((PROJECT_ROOT / relative).resolve())
        for relative in SOURCE_CONFIG_RELATIVE_PATHS
    }
    required.add(str(authorization_path.resolve()))
    required.add(str(Path(str(environment["python_executable"])).resolve()))
    required.update(str(path) for path in _sealed_path_schema(
        paths, authorization_path=authorization_path, authorization=authorization,
    ).values())
    required.update(str(Path(row[0]).resolve()) for row in environment["solver_artifacts"])
    required.update(str(Path(row[0]).resolve()) for row in environment["torch_native_artifacts"])
    actual = set(authorization["source_build_read_allowlist"])
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise SelectorInvalid(
            f"Stage-2 exhaustive exact allowlist mismatch: missing={missing!r} extra={extra!r}"
        )


def run_two_replica_sequence(
    *, stage2_authorization_path: Path,
    claim_continuation: _Stage2ClaimContinuation,
    activity_counts: dict[str, int],
) -> dict[str, Any]:
    """Fixed-root continuation: two cold replicas, verifier, and one seal."""

    global _ACTIVE_CLAIM_CONTINUATION, _ACTIVE_CATALOG_GENERATION_CAPABILITY
    paths = stage2_paths()
    stage2_authorization_path = safe_existing_path(stage2_authorization_path)
    bootstrap_authorization = _load_json(stage2_authorization_path)
    validate_stage2_authorization(bootstrap_authorization)
    authorize_read_path(bootstrap_authorization, stage2_authorization_path)
    authorization = authorized_json(bootstrap_authorization, stage2_authorization_path)
    validate_stage2_authorization(authorization)
    if not _exact_json_equal(dict(authorization), dict(bootstrap_authorization)):
        raise SelectorInvalid("Stage-2 authorization changed during secure load")
    verify_authorized_source_config(authorization)
    if (
        not isinstance(claim_continuation, _Stage2ClaimContinuation)
        or claim_continuation is not _ACTIVE_CLAIM_CONTINUATION
        or claim_continuation.selector_consumed
        or not claim_continuation.catalog_issued
        or claim_continuation.authorization_sha256
        != sha256_bytes(_canonical_json_bytes(authorization))
    ):
        raise SelectorInvalid("direct API lacks the exact fixed-root claim continuation")
    claim_continuation.selector_consumed = True
    _ACTIVE_CLAIM_CONTINUATION = None
    if (
        _ACTIVE_CATALOG_GENERATION_CAPABILITY is None
        or not _ACTIVE_CATALOG_GENERATION_CAPABILITY.consumed
        or _ACTIVE_CATALOG_GENERATION_CAPABILITY.in_progress
        or _ACTIVE_CATALOG_GENERATION_CAPABILITY.authorization_sha256
        != claim_continuation.authorization_sha256
        or _ACTIVE_CATALOG_GENERATION_CAPABILITY.claim_sha256
        != claim_continuation.claim_sha256
    ):
        raise SelectorInvalid("fixed-root continuation lost its issued catalog capability")
    _ACTIVE_CATALOG_GENERATION_CAPABILITY = None
    _validate_existing_directory(paths["session_root"])
    if not paths["claim"].is_file():
        raise SelectorInvalid("fixed Stage-2 namespace was not exclusively claimed")
    claim = authorized_json(authorization, paths["claim"])
    validate_exact_claim(
        claim, authorization, phase="stage2_selector_continuation",
    )
    if sha256_authorized_file(authorization, paths["claim"]) != claim_continuation.claim_sha256:
        raise SelectorInvalid("Stage-2 claim changed after continuation issuance")
    validate_activity_counts(activity_counts)
    for name in ("verifier", "selector"):
        authorize_read_path(authorization, paths[name])
    for name in (
        "bindings", "replica_1", "replica_2", "witness", "proposed_manifest",
        "verifier_report", "receipt", "manifest",
    ):
        if path_lexists(paths[name]):
            raise SelectorInvalid("pre-existing fixed-root output invalidates exact-once Stage 2")
    validate_absent_destination(paths["selector_root"])
    paths["selector_root"].mkdir()
    environment_path, full_environment = load_full_environment_receipt(authorization)
    validate_selector_environment_receipt(authorization, full_environment)
    _require_exhaustive_allowlist(
        authorization, stage2_authorization_path, paths, full_environment
    )
    for name in ("catalog", "universe_spec", "ledger"):
        authorize_read_path(authorization, paths[name])
    sealed_schema = _sealed_path_schema(
        paths, authorization_path=stage2_authorization_path,
        authorization=authorization,
    )
    expected = {
        **source_bindings(authorization),
        "catalog_sha256": sha256_authorized_file(authorization, paths["catalog"]),
        "ledger_sha256": sha256_authorized_file(authorization, paths["ledger"]),
        "universe_spec_sha256": sha256_authorized_file(
            authorization, paths["universe_spec"]
        ),
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": sha256_bytes(_canonical_json_bytes(authorization)),
        "sealed_path_schema": sealed_schema,
        "sealed_path_schema_sha256": sha256_bytes(
            _canonical_json_bytes(sealed_schema)
        ),
        "full_environment_receipt_path": str(environment_path),
        "full_environment_receipt_sha256": authorization["full_environment_receipt_sha256"],
        **full_environment,
    }
    bindings = {
        "selector_path": str(paths["selector"].resolve()),
        "verifier_path": str(paths["verifier"].resolve()),
        "synthetic_only": False,
        "expected": expected,
    }
    _write_json_exclusive(paths["bindings"], bindings)
    replicas = []
    for replica_index in (1, 2):
        def process_started(index: int = replica_index) -> None:
            activity_counts["canonical_ortools_processes"] += 1
            activity_counts["replicas"] += 1
            persist_activity_snapshot(
                authorization, paths, f"replica_{index}", activity_counts,
            )
        output = paths[f"replica_{replica_index}"]
        replicas.append(
            _run_cold_replica(
                selector_path=paths["selector"], catalog_path=paths["catalog"],
                ledger_path=paths["ledger"], bindings_path=paths["bindings"],
                output_path=output,
                authorization_path=stage2_authorization_path,
                authorization=authorization,
                on_process_started=process_started,
            )
        )
    agreed = compare_replicas(replicas[0], replicas[1])
    witness = {
        "selector_identity": SELECTOR_ID,
        "membership_vector": agreed["membership_vector"],
        "membership_vector_sha256": agreed["membership_vector_sha256"],
    }
    _write_json_exclusive(paths["witness"], witness)
    activity_counts["witnesses"] += 1
    persist_activity_snapshot(authorization, paths, "witness", activity_counts)
    _write_json_exclusive(paths["proposed_manifest"], agreed["manifest"])
    verifier_command = [
        sys.executable, "-I", "-B", str(paths["verifier"]),
        "--catalog", str(paths["catalog"]), "--ledger", str(paths["ledger"]),
        "--universe", str(paths["universe_spec"]),
        "--witness", str(paths["witness"]), "--manifest", str(paths["proposed_manifest"]),
        "--bindings", str(paths["bindings"]), "--report", str(paths["verifier_report"]),
        "--replica", str(paths["replica_1"]), "--replica", str(paths["replica_2"]),
        "--stage2-authorization", str(stage2_authorization_path),
    ]
    try:
        verifier_process = subprocess.Popen(
            verifier_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError as exc:
        raise SelectorInvalid("independent verifier failed to start") from exc
    activity_counts["canonical_verifier_admissions"] += 1
    persist_activity_snapshot(authorization, paths, "verifier", activity_counts)
    try:
        verifier_stdout, verifier_stderr = verifier_process.communicate(
            timeout=WALL_SECONDS
        )
    except subprocess.TimeoutExpired as exc:
        verifier_process.kill()
        verifier_process.communicate()
        raise SelectorInvalid("independent verifier exceeded 1800 wall seconds") from exc
    if verifier_process.returncode != 0 or verifier_stdout or verifier_stderr:
        raise SelectorInvalid("independent verifier failed closed")
    report = authorized_json(authorization, paths["verifier_report"])
    if report.get("verdict") != "VERIFIED" or report.get("manifest_sha256") != agreed["manifest_sha256"]:

        raise SelectorInvalid("independent verifier report mismatch")
    manifest_bytes = _canonical_json_bytes(agreed["manifest"]) + b"\n"
    write_exclusive(paths["manifest"], manifest_bytes)
    if sha256_authorized_file(authorization, paths["manifest"]) != sha256_bytes(manifest_bytes):
        raise SelectorInvalid("published manifest reload digest mismatch")
    try:
        paths["manifest"].chmod(0o444)
    except OSError as exc:
        raise SelectorInvalid("published manifest could not be made read-only") from exc
    activity_counts["manifests"] += 1
    persist_activity_snapshot(authorization, paths, "manifest", activity_counts)
    sealed_objects = {
        name: {
            "path": locator,
            "sha256": sha256_authorized_file(authorization, Path(locator)),
        }
        for name, locator in sealed_schema.items()
        if name in SELECTOR_SEALED_OBJECT_NAMES
    }
    success = {
        "branch": VALID,
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": expected["stage2_authorization_sha256"],
        "source_config_digest_map": expected["source_config_digest_map"],
        "source_config_digest_map_sha256": expected["source_config_digest_map_sha256"],
        "python_executable": expected["python_executable"],
        "python_executable_sha256": expected["python_executable_sha256"],
        "solver_artifacts": expected["solver_artifacts"],
        "solver_artifact_set_sha256": expected["solver_artifact_set_sha256"],
        "sealed_objects": sealed_objects,
        "sealed_path_schema": expected["sealed_path_schema"],
        "sealed_path_schema_sha256": expected["sealed_path_schema_sha256"],
        "receipt_path": str(paths["receipt"].resolve()),
        "receipt_self_digest_is_external": True,
        "replica_count": 2,
        "replica_2_role": "prospective_determinism_gate_not_retry",
        "activity_accounting": {"sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0},
        "catalog_path": str(paths["catalog"].resolve()),
        "catalog_sha256": sealed_objects["catalog"]["sha256"],
        "universe_spec_path": str(paths["universe_spec"].resolve()),
        "universe_spec_sha256": sealed_objects["universe_spec"]["sha256"],
        "ledger_path": str(paths["ledger"].resolve()),
        "ledger_sha256": sealed_objects["ledger"]["sha256"],
        "bindings_path": str(paths["bindings"].resolve()),
        "bindings_sha256": sealed_objects["bindings"]["sha256"],
        "witness_path": str(paths["witness"].resolve()),
        "witness_sha256": sealed_objects["witness"]["sha256"],
        "manifest_path": str(paths["manifest"].resolve()),
        "manifest_file_sha256": sealed_objects["manifest"]["sha256"],
        "manifest_content_sha256": agreed["manifest_sha256"],
        "verifier_report_path": str(paths["verifier_report"].resolve()),
        "verifier_report_sha256": sealed_objects["verifier_report"]["sha256"],
        "replica_resource_telemetry": [
            replicas[0]["resource_telemetry"], replicas[1]["resource_telemetry"]
        ],
        "activity_counts": dict(activity_counts),
        "full_environment_receipt_path": str(environment_path),
        "full_environment_receipt_sha256": authorization["full_environment_receipt_sha256"],
    }
    validate_selector_receipt_schema(success)
    _write_json_exclusive(paths["receipt"], success)
    success["selector_success_receipt_path"] = str(paths["receipt"].resolve())
    success["selector_success_receipt_sha256"] = sha256_authorized_file(
        authorization, paths["receipt"]
    )
    return success


def _replica_cli(args: argparse.Namespace) -> int:
    authorization_path = safe_existing_path(Path(args.stage2_authorization))
    bootstrap_authorization = _load_json(authorization_path)
    validate_stage2_authorization(bootstrap_authorization)
    authorize_read_path(bootstrap_authorization, authorization_path)
    authorization = authorized_json(bootstrap_authorization, authorization_path)
    validate_stage2_authorization(authorization)
    if authorization != bootstrap_authorization:
        raise SelectorInvalid("Stage-2 authorization changed during replica secure load")
    output_path = Path(args.output)
    allowed_outputs = {
        str(stage2_paths()["replica_1"].resolve()),
        str(stage2_paths()["replica_2"].resolve()),
    }
    if (
        str(output_path) != str(output_path.resolve())
        or str(output_path) not in allowed_outputs
        or str(output_path) not in authorization["source_build_read_allowlist"]
    ):
        raise SelectorInvalid("cold replica output is not an exact fixed-root locator")
    claim_path = stage2_paths()["claim"]
    authorize_read_path(authorization, claim_path)
    _self_memory_cap()
    if sys.stdin.buffer.readline() != b"START\n":
        raise SelectorInvalid("cold replica mandatory start-token gate failed")
    start_capability = _issue_replica_start_capability(
        authorization, claim_path
    )
    result = solve_replica(
        Path(args.catalog), Path(args.ledger), Path(args.bindings), authorization,
        claim_path=claim_path, start_capability=start_capability,
    )
    _write_json_exclusive(output_path, result)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    replica = sub.add_parser("replica")
    replica.add_argument("--catalog", required=True)
    replica.add_argument("--ledger", required=True)
    replica.add_argument("--stage2-authorization", required=True)
    replica.add_argument("--bindings", required=True)
    replica.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        return _replica_cli(args)
    except Exception as exc:
        sys.stderr.write(f"{INVALID}: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CatalogRow", "SelectorInvalid", "canonical_tuple_bytes", "bucket_for_tuple",
    "split_for_bucket", "decision_key", "parse_catalog", "parse_ledger",
    "compile_equations", "canonical_order", "compare_replicas", "write_exclusive",
    "validate_final_keep_support", "validate_catalog_structural_support",
    "selector_environment", "run_two_replica_sequence", "INVALID", "VALID",
    "authorized_read_bytes", "authorized_json", "sha256_authorized_file",
    "source_config_digest_map", "verify_authorized_source_config", "stage2_paths",
    "validate_selector_receipt_schema", "SELECTOR_RECEIPT_KEYS",
]
