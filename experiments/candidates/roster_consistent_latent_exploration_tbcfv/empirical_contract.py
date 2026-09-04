"""Fail-closed prospective empirical contract for RCLE-TBCFV revision 04.

The module freezes the complete future panel and the bindings that a later
Operational-Root lease must carry.  It does not issue a lease or create a
production identity.  The only materialization admitted without a validated
Root lease and CM acceptance is one of the fixed, unmistakably synthetic TEST
fixtures below.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Final, Mapping

from .config import (
    DIRECTION_ID,
    LEARNED_PACKAGES,
    REGISTERED,
    SCIENCE_REVISION,
    SCRIPTED_PACKAGES,
)
from .inference import (
    ANALYZER_SCHEMA_VERSION,
    BLOCK_COUNT,
    BRANCHES,
    DEGREES_OF_FREEDOM,
    DIRECT_VALUE_VARIABLES,
    GAMMA_GLOBAL,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TAIL_COUNT,
    TRAINING_CELLS,
)
from .native_backend import NATIVE_ABI_VERSION, SUPPORTED_BATCH_WIDTHS
from .process_workers import (
    CANONICAL_DURABLE_CEILING,
    CHECKPOINT_READ_CEILING,
    CHECKPOINT_WRITE_CEILING,
    CPU_HOURS_CEILING,
    FOUR_PROCESS_WALL_HOURS_CEILING,
    PRIVATE_SCRATCH_COMBINED_CEILING,
    PROCESS_GROUP_RSS_CEILING,
    make_process_resource_object,
    validate_process_resource_object,
)


EMPIRICAL_OBJECT: Final[str] = "RCLE-TBCFV-R04-FULL-EMPIRICAL-PANEL"
SHARED_COMPONENT: Final[str] = "rcle.tbcfv.r04.full_host"
SELECTED_BATCH_WIDTH: Final[int] = 8
CM_OWNER: Final[str] = "/root/cm_rcle_cpc_r04"
ACCEPTED_NATIVE_SOURCE_SHA256: Final[str] = (
    "18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819"
)
LEGACY_ACCEPTED_NATIVE_SOURCE_SHA256: Final[str] = (
    "ddb14c33d822924b21b872713745f242fee92f16b4329efed439a1e2b816a910"
)
ACCEPTED_NATIVE_BUILD_KEY: Final[str] = (
    "d2501eb514977026c645a3c23a53d86626a5817a51ee859dbdfa9f07f3523e81"
)
ACCEPTED_NATIVE_ARTIFACT_SHA256: Final[str] = (
    "c4db07f1d5ffaf7bd61354edd74a2bf861e9c1a20a2eec96faa85dd1d9f56cfd"
)

PREACTIVITY_SCHEMA: Final[str] = "RCLE_TBCFV_R04_PREACTIVITY_CERTIFICATE_V1"
TEST_PREACTIVITY_SCHEMA: Final[str] = (
    "RCLE_TBCFV_R04_SYNTHETIC_TEST_PREACTIVITY_CERTIFICATE_V1"
)
COORDINATE_PROPOSAL_SCHEMA: Final[str] = "RCLE_TBCFV_R04_COORDINATE_PROPOSAL_V1"
CM_ACCEPTED_BINDING_SCHEMA: Final[str] = "RCLE_TBCFV_R04_CM_ACCEPTED_PREACTIVITY_BINDING_V1"
RESOURCE_REQUEST_SCHEMA: Final[str] = "RCLE_TBCFV_R04_ROOT_RESOURCE_REQUEST_V1"
ROOT_LEASE_SCHEMA: Final[str] = "RCLE_TBCFV_R04_ROOT_DIRECTION_LEASE_V1"
MATERIALIZED_BINDING_SCHEMA: Final[str] = "RCLE_TBCFV_R04_MATERIALIZED_COORDINATE_BINDING_V1"
SOURCE_REPAIR_TRANSITION_SCHEMA: Final[str] = (
    "RCLE_TBCFV_R04_POST_ACTIVITY_SOURCE_REPAIR_TRANSITION_V1"
)
SOURCE_REPAIR_LEASE_SCHEMA: Final[str] = (
    "RCLE_TBCFV_R04_ROOT_SOURCE_REPAIR_REPLACEMENT_LEASE_V1"
)
SOURCE_REPAIR_FAILED_TERMINAL_SCHEMA: Final[str] = (
    "RCLE_TBCFV_R04_SOURCE_REPAIR_FAILED_TERMINAL_V1"
)
SOURCE_REPAIR_BOOTSTRAP_SCHEMA: Final[str] = (
    "RCLE_TBCFV_R04_SOURCE_REPAIR_BOOTSTRAP_V1"
)
MAX_SOURCE_REPAIR_REPLACEMENT_INDEX: Final[int] = 3
SOURCE_REPAIR_REASON: Final[str] = "WINDOWS_ATOMIC_TEMP_BASENAME_PATH_LENGTH"
SOURCE_REPAIR_SHARED_POLICY_REASON: Final[str] = (
    "SHARED_POLICY_ABI2_RECEIPT_ALIGNMENT"
)
SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH: Final[str] = (
    "docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md"
)
SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256: Final[str] = (
    "aed308f6b667dd33d33d39956b17f06f78f3a3f9cb5ce6e94f3374ad38432204"
)
SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256: Final[str] = (
    "088fee8c6b2f1521df755a1255642de77fb6a1c104d3440e02cc3c0fcfcd8ef9"
)
SOURCE_REPAIR_SHARED_POLICY_NEW_BYTES: Final[int] = 23_618
SOURCE_REPAIR_SHARED_POLICY_CURRENT_SHA256: Final[str] = (
    "e71099351f40aa891f38ad57ba4d178d1ab42771d78cc4933d78c70fe72d3221"
)
SOURCE_REPAIR_SHARED_POLICY_CURRENT_BYTES: Final[int] = 25_935
SOURCE_REPAIR_OPERATOR_TERMINAL_LOGICAL_PATH: Final[str] = (
    "temp/leases/RCLE_TBCFV_R04_OPERATOR_TERMINAL_20260821_01.json"
)
SOURCE_REPAIR_OPERATOR_ACTIVITY_PREDICATE: Final[str] = (
    "Question-relevant scientific activity begins only when the exact bound "
    "coordinate identity is consumed by the production panel run."
)
SOURCE_REPAIR_OPERATOR_COMMAND: Final[tuple[str, ...]] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
    "-m",
    "experiments.candidates.roster_consistent_latent_exploration_tbcfv",
    "run",
    "--certificate",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/RCLE_TBCFV_R04_PREACTIVITY_CERTIFICATE_20260821.json",
    "--accepted-binding",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/RCLE_TBCFV_R04_CM_PREACTIVITY_ACCEPTANCE_20260821.json",
    "--resource-request",
    "temp/leases/RCLE_TBCFV_R04_ROOT_RESOURCE_REQUEST_20260821.json",
    "--lease",
    "temp/leases/RCLE_TBCFV_R04_ROOT_DIRECTION_LEASE_20260821_01.json",
    "--coordinate-binding",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/RCLE_TBCFV_R04_RESULTS_20260821_01/RUN_IDENTITY.json",
    "--result-root",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/RCLE_TBCFV_R04_RESULTS_20260821_01",
)
SOURCE_REPAIR_OPERATOR_OUTPUT_PATH: Final[str] = (
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/"
    "RCLE_TBCFV_R04_RESULTS_20260821_01/RUN_IDENTITY.json"
)
SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/__main__.py",
    "envs/native/production_backend.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_artifacts.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_contract.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/native/tbcfv_backend.cpp",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/native_backend.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/process_workers.py",
    "runtime/benchmarks/rcle_tbcfv_r04_production_protocol_efficiency_20260822.json",
    "tools/benchmarks/benchmark_rcle_tbcfv_r04_runner_chain.py",
)
PROCESS_WORKERS_LOGICAL_PATH: Final[str] = (
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/process_workers.py"
)
SOURCE_ABSENT_SHA256: Final[str] = "0" * 64

PANEL_COUNTS: Final[dict[str, int]] = {
    "run_blocks": 20,
    "learned_arms": 5,
    "scripted_packages": 3,
    "updates_per_learned_arm_block": 800,
    "episodes_per_update": 64,
    "learned_arm_block_updates": 80_000,
    "training_episodes": 5_120_000,
    "learned_heldout_episodes_per_cell": 2_048,
    "learned_heldout_episodes": 1_638_400,
    "scripted_heldout_episodes_per_cell": 2_048,
    "scripted_heldout_episodes": 983_040,
    "total_episodes": 7_741_440,
    "environment_ticks": 495_452_160,
    "agent_ticks": 4_299_161_600,
    "agent_claim_decisions": 1_074_790_400,
    "candidate_pointer_scores": 6_448_742_400,
    "registered_tails": 72,
    "result_branches": 12,
}

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_PERMIT_SEAL: Final[object] = object()
_SOURCE_REPAIR_BOOTSTRAP_SEAL: Final[object] = object()

LEGACY_PRODUCTION_SOURCE_LOGICAL_PATHS: Final[tuple[str, ...]] = (
    "docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md",
    "docs/research/candidates/roster_consistent_latent_exploration/RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md",
    "docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_R04_FULL_EMPIRICAL_PANEL_EM_HANDOFF_20260821.md",
    "envs/native/production_backend.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/__init__.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/__main__.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/artifacts.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/config.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_artifacts.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_contract.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_inference.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/host_oracle.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/inference.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/models.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/native/tbcfv_backend.cpp",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/native_backend.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/packages.py",
    "experiments/candidates/roster_consistent_latent_exploration_tbcfv/scripted.py",
    "runtime/benchmarks/rcle_tbcfv_r04_efficiency_20260821.json",
    "tools/benchmarks/benchmark_rcle_tbcfv_r04_native.py",
)
PROCESS_PRODUCTION_SOURCE_LOGICAL_PATHS: Final[tuple[str, ...]] = tuple(
    sorted((*LEGACY_PRODUCTION_SOURCE_LOGICAL_PATHS, PROCESS_WORKERS_LOGICAL_PATH))
)
PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH: Final[str] = (
    "runtime/benchmarks/rcle_tbcfv_r04_production_protocol_efficiency_20260822.json"
)
PRODUCTION_PROTOCOL_BENCHMARK_SCRIPT_LOGICAL_PATH: Final[str] = (
    "tools/benchmarks/benchmark_rcle_tbcfv_r04_runner_chain.py"
)
PRODUCTION_SOURCE_LOGICAL_PATHS: Final[tuple[str, ...]] = tuple(
    sorted(
        (
            *PROCESS_PRODUCTION_SOURCE_LOGICAL_PATHS,
            PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH,
            PRODUCTION_PROTOCOL_BENCHMARK_SCRIPT_LOGICAL_PATH,
        )
    )
)
BENCHMARK_EVIDENCE_LOGICAL_PATH: Final[str] = (
    "runtime/benchmarks/rcle_tbcfv_r04_efficiency_20260821.json"
)

SYNTHETIC_TEST_IDENTITIES: Final[tuple[str, ...]] = (
    "SYNTHETIC-TEST-RCLE-TBCFV-R04-A",
    "SYNTHETIC-TEST-RCLE-TBCFV-R04-B",
    "SYNTHETIC-TEST-RCLE-TBCFV-R04-C",
    "SYNTHETIC-TEST-RCLE-TBCFV-R04-D",
)
_SYNTHETIC_TEST_KEYS: Final[dict[str, bytes]] = {
    SYNTHETIC_TEST_IDENTITIES[0]: b"RCLE-TBCFV-R04-SYNTHETIC-TEST-KEY-A-v1",
    SYNTHETIC_TEST_IDENTITIES[1]: b"RCLE-TBCFV-R04-SYNTHETIC-TEST-KEY-B-v1",
    SYNTHETIC_TEST_IDENTITIES[2]: b"RCLE-TBCFV-R04-SYNTHETIC-TEST-KEY-C-v1",
    SYNTHETIC_TEST_IDENTITIES[3]: b"RCLE-TBCFV-R04-SYNTHETIC-TEST-KEY-D-v1",
}


class EmpiricalContractError(ValueError):
    """A proposed object differs from the frozen prospective contract."""


class LeaseError(PermissionError):
    """An object is not an active exact Operational-Root lease."""


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise EmpiricalContractError("value is not finite canonical ASCII JSON") from exc


def document_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise EmpiricalContractError(f"{label} must be lowercase SHA-256")
    return value


def _safe_identity(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_LABEL.fullmatch(value) is None:
        raise EmpiricalContractError(f"{label} is absent or malformed")
    return value


def _exact_mapping(value: object, keys: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise EmpiricalContractError(f"{label} field inventory differs")
    return value


def canonical_source_identity(paths: Mapping[str, str | Path]) -> dict[str, object]:
    """Bind named source bytes without admitting escaping logical labels."""

    if not paths:
        raise EmpiricalContractError("source identity requires at least one file")
    files: dict[str, object] = {}
    for label, source in sorted(paths.items()):
        if not isinstance(label, str) or not label:
            raise EmpiricalContractError("source labels must be nonempty strings")
        logical = PurePosixPath(label.replace("\\", "/"))
        if logical.is_absolute() or "." in logical.parts or ".." in logical.parts:
            raise EmpiricalContractError("source label escapes its logical scope")
        resolved = Path(source).resolve(strict=True)
        payload = resolved.read_bytes()
        files[logical.as_posix()] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    body = {"files": files, "ordering": "logical-path byte order"}
    return {**body, "source_set_sha256": document_sha256(body)}


def validate_source_identity(value: Mapping[str, object]) -> dict[str, object]:
    mapping = _exact_mapping(
        value, {"files", "ordering", "source_set_sha256"}, "source identity"
    )
    if mapping["ordering"] != "logical-path byte order":
        raise EmpiricalContractError("source ordering differs")
    files = mapping["files"]
    if not isinstance(files, Mapping) or not files:
        raise EmpiricalContractError("source identity is empty")
    for label, item in files.items():
        logical = PurePosixPath(str(label))
        if logical.is_absolute() or "." in logical.parts or ".." in logical.parts:
            raise EmpiricalContractError("source identity contains an escaping label")
        row = _exact_mapping(item, {"bytes", "sha256"}, f"source file {label}")
        size = row["bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise EmpiricalContractError("source byte count is invalid")
        _require_sha256(row["sha256"], "source file")
    body = {"files": dict(files), "ordering": mapping["ordering"]}
    if mapping["source_set_sha256"] != document_sha256(body):
        raise EmpiricalContractError("source-set digest differs")
    return dict(mapping)


def production_source_paths(
    repository_root: str | Path | None = None,
) -> dict[str, Path]:
    """Return the one exact repository-relative production source inventory."""

    repository = (
        Path(repository_root).resolve(strict=True)
        if repository_root is not None
        else Path(__file__).resolve().parents[3]
    )
    return {label: repository / Path(label) for label in PRODUCTION_SOURCE_LOGICAL_PATHS}


def _validate_production_source_paths(
    source_paths: Mapping[str, str | Path],
) -> dict[str, Path]:
    expected = production_source_paths()
    if set(source_paths) != set(PRODUCTION_SOURCE_LOGICAL_PATHS):
        raise EmpiricalContractError("production source logical-path inventory differs")
    result: dict[str, Path] = {}
    for label in PRODUCTION_SOURCE_LOGICAL_PATHS:
        supplied = Path(source_paths[label]).resolve(strict=True)
        required = expected[label].resolve(strict=True)
        if supplied != required or supplied.is_symlink() or not supplied.is_file():
            raise EmpiricalContractError(f"production source path is misbound: {label}")
        result[label] = supplied
    return result


def _validate_live_production_source_identity(
    value: Mapping[str, object],
) -> dict[str, object]:
    source = validate_source_identity(value)
    files = source["files"]
    assert isinstance(files, Mapping)
    if set(files) != set(PRODUCTION_SOURCE_LOGICAL_PATHS):
        raise EmpiricalContractError("production source logical-path inventory differs")
    repository = Path(__file__).resolve().parents[3]
    for label in PRODUCTION_SOURCE_LOGICAL_PATHS:
        target = (repository / Path(label)).resolve(strict=True)
        try:
            target.relative_to(repository)
        except ValueError as exc:
            raise EmpiricalContractError("production source escapes repository") from exc
        if not target.is_file() or target.is_symlink():
            raise EmpiricalContractError(f"production source is absent or symlinked: {label}")
        payload = target.read_bytes()
        row = files[label]
        assert isinstance(row, Mapping)
        if row.get("bytes") != len(payload) or row.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise EmpiricalContractError(f"live production source bytes drifted: {label}")
    return source


def frozen_config_identity() -> dict[str, object]:
    body: dict[str, object] = {
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "host": {
            "sectors": 120,
            "beacons": 6,
            "max_agents": 12,
            "horizon": 64,
            "event_tick": 24,
            "claim_period": 4,
        },
        "learned_packages": list(LEARNED_PACKAGES),
        "scripted_packages": list(SCRIPTED_PACKAGES),
        "training_cells": list(TRAINING_CELLS),
        "heldout_cells": list(HELDOUT_CELLS),
        "counts": dict(PANEL_COUNTS),
        "model": REGISTERED.manifest(),
        "checkpoint": {"sole_scientific_update": 800, "selection": False},
        "native": {
            "component": SHARED_COMPONENT,
            "abi_version": NATIVE_ABI_VERSION,
            "supported_widths": list(SUPPORTED_BATCH_WIDTHS),
            "selected_width": SELECTED_BATCH_WIDTH,
            "event_time_newcomer_position_input": True,
            "event_input_size": 64,
            "atomic_t24_event_input_before_claim": True,
            "stable_physical_agent_transport_keys": True,
            "transport_keys_actor_model_visible": False,
            "public_observation_excludes_transport_keys": True,
            "python_fallback": False,
        },
    }
    return {**body, "config_sha256": document_sha256(body)}


def analyzer_identity() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": ANALYZER_SCHEMA_VERSION,
        "science_revision": SCIENCE_REVISION,
        "run_blocks": BLOCK_COUNT,
        "degrees_of_freedom": DEGREES_OF_FREEDOM,
        "registered_tails": TAIL_COUNT,
        "gamma_global_hex": float(GAMMA_GLOBAL).hex(),
        "prerequisite_variables": list(PREREQUISITE_VARIABLES),
        "direct_value_variables": list(DIRECT_VALUE_VARIABLES),
        "mechanism_variables": list(MECHANISM_VARIABLES),
        "branches": list(BRANCHES),
        "first_match_precedence": True,
    }
    return {**body, "analyzer_sha256": document_sha256(body)}


def native_identity_from_observation(observation: Mapping[str, object]) -> dict[str, object]:
    """Normalize an already observed candidate-native artifact identity."""

    required = {
        "path",
        "sha256",
        "size",
        "mtime_ns",
        "source_sha256",
        "build_key",
        "resolved_build_root",
        "runtime_abi",
        "toolchain",
        "abi",
        "load_seconds",
    }
    raw = _exact_mapping(observation, required, "native observation")
    abi = _exact_mapping(
        raw["abi"],
        {
            "abi_version",
            "fixture_magic",
            "fixture_input_size",
            "step_input_size",
            "event_input_size",
            "snapshot_size",
        },
        "native ABI",
    )
    expected_abi = {
        "abi_version": 2,
        "fixture_magic": 0x52434C4554424347,
        "fixture_input_size": 224,
        "step_input_size": 64,
        "event_input_size": 64,
        "snapshot_size": 464,
    }
    if dict(abi) != expected_abi:
        raise EmpiricalContractError("native ABI differs from accepted construction")
    runtime_abi = raw["runtime_abi"]
    toolchain = raw["toolchain"]
    if not isinstance(runtime_abi, Mapping) or not runtime_abi:
        raise EmpiricalContractError("native runtime ABI identity is absent")
    if not isinstance(toolchain, Mapping) or not toolchain:
        raise EmpiricalContractError("native toolchain identity is absent")
    value: dict[str, object] = {
        "component": SHARED_COMPONENT,
        "backend": "cpp",
        "full_reset_step_terminal_cpp": True,
        "python_fallback": False,
        "abi": expected_abi,
        "supported_batch_widths": list(SUPPORTED_BATCH_WIDTHS),
        "selected_batch_width": SELECTED_BATCH_WIDTH,
        "event_time_newcomer_position_input": True,
        "atomic_t24_event_input_before_claim": True,
        "event_batch_prevalidated_before_mutation": True,
        "stable_physical_agent_transport_keys": True,
        "transport_keys_actor_model_visible": False,
        "public_observation_excludes_transport_keys": True,
        "source_sha256": _require_sha256(raw["source_sha256"], "native source"),
        "artifact_sha256": _require_sha256(raw["sha256"], "native artifact"),
        "build_key": _require_sha256(raw["build_key"], "native build key"),
        "runtime_abi": dict(runtime_abi),
        "toolchain": dict(toolchain),
    }
    canonical_json_bytes(value)
    sealed = {**value, "native_identity_sha256": document_sha256(value)}
    return validate_native_identity(sealed)


def validate_native_identity(
    value: Mapping[str, object], *, require_current_acceptance: bool = True
) -> dict[str, object]:
    required = {
        "component",
        "backend",
        "full_reset_step_terminal_cpp",
        "python_fallback",
        "abi",
        "supported_batch_widths",
        "selected_batch_width",
        "event_time_newcomer_position_input",
        "atomic_t24_event_input_before_claim",
        "event_batch_prevalidated_before_mutation",
        "stable_physical_agent_transport_keys",
        "transport_keys_actor_model_visible",
        "public_observation_excludes_transport_keys",
        "source_sha256",
        "artifact_sha256",
        "build_key",
        "runtime_abi",
        "toolchain",
        "native_identity_sha256",
    }
    mapping = _exact_mapping(value, required, "native identity")
    body = {key: mapping[key] for key in required - {"native_identity_sha256"}}
    if mapping["native_identity_sha256"] != document_sha256(body):
        raise EmpiricalContractError("native identity digest differs")
    if (
        mapping["component"] != SHARED_COMPONENT
        or mapping["backend"] != "cpp"
        or mapping["full_reset_step_terminal_cpp"] is not True
        or mapping["python_fallback"] is not False
        or mapping["supported_batch_widths"] != list(SUPPORTED_BATCH_WIDTHS)
        or mapping["selected_batch_width"] != SELECTED_BATCH_WIDTH
        or mapping["event_time_newcomer_position_input"] is not True
        or mapping["atomic_t24_event_input_before_claim"] is not True
        or mapping["event_batch_prevalidated_before_mutation"] is not True
        or mapping["stable_physical_agent_transport_keys"] is not True
        or mapping["transport_keys_actor_model_visible"] is not False
        or mapping["public_observation_excludes_transport_keys"] is not True
    ):
        raise EmpiricalContractError("native host/component/width binding differs")
    if mapping["abi"] != {
        "abi_version": 2,
        "fixture_magic": 0x52434C4554424347,
        "fixture_input_size": 224,
        "step_input_size": 64,
        "event_input_size": 64,
        "snapshot_size": 464,
    }:
        raise EmpiricalContractError("native ABI binding differs")
    for key in ("source_sha256", "artifact_sha256", "build_key"):
        _require_sha256(mapping[key], f"native {key}")
    if require_current_acceptance and (
        mapping["source_sha256"] != ACCEPTED_NATIVE_SOURCE_SHA256
        or mapping["build_key"] != ACCEPTED_NATIVE_BUILD_KEY
        or mapping["artifact_sha256"] != ACCEPTED_NATIVE_ARTIFACT_SHA256
    ):
        raise EmpiricalContractError("native ABI2 source/build/artifact identity differs")
    if not isinstance(mapping["runtime_abi"], Mapping) or not mapping["runtime_abi"]:
        raise EmpiricalContractError("native runtime ABI binding is absent")
    if not isinstance(mapping["toolchain"], Mapping) or not mapping["toolchain"]:
        raise EmpiricalContractError("native toolchain binding is absent")
    return dict(mapping)


def coordinate_proposal() -> dict[str, object]:
    """Return the exact unmaterialized product-family proposal."""

    body: dict[str, object] = {
        "schema": COORDINATE_PROPOSAL_SCHEMA,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "materialized": False,
        "namespace": None,
        "run_block_identities": None,
        "numeric_seeds": None,
        "master": None,
        "master_digest": None,
        "coordinate_rows": None,
        "random_scientific_state": None,
        "run_block_count": BLOCK_COUNT,
        "derivation": "HMAC-SHA256 over canonical semantic addresses",
        "semantic_address_fields": [
            "run_block",
            "parameter_entry",
            "arm_only_variable",
            "cell",
            "update_or_scenario",
            "physical_tick",
            "roster_event",
            "physical_agent",
            "draw_kind",
            "draw_index",
        ],
        "pairing": {
            "world_and_evaluation_scenarios_shared_across_arms": True,
            "common_initial_tensor_shared_across_arms": True,
            "common_plan_draws_shared_when_semantically_common": True,
            "actor_draws_shared_when_agent_semantics_and_distribution_coincide": True,
            "coherent_fragmented_scenarios_shared_through_intervention": True,
            "unused_draws_have_no_forward_or_score_path": True,
        },
    }
    return {**body, "proposal_sha256": document_sha256(body)}


def validate_coordinate_proposal(value: Mapping[str, object]) -> dict[str, object]:
    expected = coordinate_proposal()
    if dict(value) != expected:
        raise EmpiricalContractError("coordinate proposal differs or contains material")
    return expected


def build_preactivity_certificate(
    *,
    source_paths: Mapping[str, str | Path],
    native_identity: Mapping[str, object],
    fixture_only: bool = False,
) -> dict[str, object]:
    """Seal result-blind construction facts without creating activity objects."""

    if fixture_only:
        if not source_paths or any(
            not isinstance(label, str) or not label.startswith("TEST/")
            for label in source_paths
        ):
            raise EmpiricalContractError("TEST certificate requires explicit TEST/ labels")
        source = canonical_source_identity(source_paths)
        schema = TEST_PREACTIVITY_SCHEMA
        empirical_object = "SYNTHETIC-TEST-ONLY"
        inventory_kind = "SYNTHETIC_TEST_EXPLICIT_NONPRODUCTION"
    else:
        source = canonical_source_identity(_validate_production_source_paths(source_paths))
        schema = PREACTIVITY_SCHEMA
        empirical_object = EMPIRICAL_OBJECT
        inventory_kind = "EXACT_REPOSITORY_PRODUCTION_LOGICAL_PATHS"
    native = validate_native_identity(native_identity)
    config = frozen_config_identity()
    analyzer = analyzer_identity()
    proposal = coordinate_proposal()
    certificate: dict[str, object] = {
        "schema": schema,
        "fixture_only": fixture_only,
        "non_scientific": fixture_only,
        "source_inventory_kind": inventory_kind,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": empirical_object,
        "source": source,
        "config": config,
        "native": native,
        "analyzer": analyzer,
        "coordinate_proposal": proposal,
        "frozen_inventories": {
            "learned_packages": list(LEARNED_PACKAGES),
            "scripted_packages": list(SCRIPTED_PACKAGES),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
        },
        "counts": dict(PANEL_COUNTS),
        "result_blind": True,
        "activity_boundary": {
            "scientific_activity_started": False,
            "identity_present": False,
            "numeric_seed_present": False,
            "coordinate_present": False,
            "random_scientific_state_present": False,
            "model_or_checkpoint_present": False,
            "training_or_evaluation_present": False,
            "result_or_endpoint_present": False,
            "lease_present": False,
            "production_launch": False,
        },
    }
    return {**certificate, "certificate_sha256": document_sha256(certificate)}


def build_test_preactivity_certificate(
    *, source_paths: Mapping[str, str | Path], native_identity: Mapping[str, object]
) -> dict[str, object]:
    """Build an explicit non-scientific TEST certificate with no admission use."""

    return build_preactivity_certificate(
        source_paths=source_paths,
        native_identity=native_identity,
        fixture_only=True,
    )


def validate_preactivity_certificate(
    value: Mapping[str, object],
    *,
    allow_test_fixture: bool = False,
    validate_live_sources: bool = True,
) -> dict[str, object]:
    required = {
        "schema",
        "fixture_only",
        "non_scientific",
        "source_inventory_kind",
        "direction_id",
        "science_revision",
        "empirical_object",
        "source",
        "config",
        "native",
        "analyzer",
        "coordinate_proposal",
        "frozen_inventories",
        "counts",
        "result_blind",
        "activity_boundary",
        "certificate_sha256",
    }
    mapping = _exact_mapping(value, required, "preactivity certificate")
    body = {key: mapping[key] for key in required - {"certificate_sha256"}}
    if mapping["certificate_sha256"] != document_sha256(body):
        raise EmpiricalContractError("preactivity certificate digest differs")
    fixture_only = mapping["fixture_only"]
    if fixture_only is True:
        if not allow_test_fixture:
            raise EmpiricalContractError("TEST preactivity certificate is not production-admissible")
        if (
            mapping["schema"] != TEST_PREACTIVITY_SCHEMA
            or mapping["non_scientific"] is not True
            or mapping["source_inventory_kind"]
            != "SYNTHETIC_TEST_EXPLICIT_NONPRODUCTION"
            or mapping["empirical_object"] != "SYNTHETIC-TEST-ONLY"
        ):
            raise EmpiricalContractError("TEST preactivity certificate boundary differs")
    elif fixture_only is False:
        if (
            mapping["schema"] != PREACTIVITY_SCHEMA
            or mapping["non_scientific"] is not False
            or mapping["source_inventory_kind"]
            != "EXACT_REPOSITORY_PRODUCTION_LOGICAL_PATHS"
            or mapping["empirical_object"] != EMPIRICAL_OBJECT
        ):
            raise EmpiricalContractError("production preactivity certificate boundary differs")
    else:
        raise EmpiricalContractError("preactivity fixture_only marker is not boolean")
    if (
        mapping["direction_id"] != DIRECTION_ID
        or mapping["science_revision"] != SCIENCE_REVISION
        or mapping["config"] != frozen_config_identity()
        or mapping["analyzer"] != analyzer_identity()
        or mapping["counts"] != PANEL_COUNTS
        or mapping["result_blind"] is not True
    ):
        raise EmpiricalContractError("preactivity frozen object differs")
    source = mapping["source"]
    native = mapping["native"]
    proposal = mapping["coordinate_proposal"]
    if not isinstance(source, Mapping) or not isinstance(native, Mapping) or not isinstance(proposal, Mapping):
        raise EmpiricalContractError("preactivity identity object is malformed")
    if fixture_only:
        validated_source = validate_source_identity(source)
        files = validated_source["files"]
        assert isinstance(files, Mapping)
        if not files or any(not str(label).startswith("TEST/") for label in files):
            raise EmpiricalContractError("TEST source inventory contains a non-TEST label")
    else:
        if validate_live_sources:
            _validate_live_production_source_identity(source)
        else:
            archived_source = validate_source_identity(source)
            archived_files = archived_source["files"]
            assert isinstance(archived_files, Mapping)
            if set(archived_files) not in (
                set(LEGACY_PRODUCTION_SOURCE_LOGICAL_PATHS),
                set(PROCESS_PRODUCTION_SOURCE_LOGICAL_PATHS),
                set(PRODUCTION_SOURCE_LOGICAL_PATHS),
            ):
                raise EmpiricalContractError(
                    "production source logical-path inventory differs"
                )
    validate_native_identity(native, require_current_acceptance=validate_live_sources)
    validate_coordinate_proposal(proposal)
    if mapping["frozen_inventories"] != {
        "learned_packages": list(LEARNED_PACKAGES),
        "scripted_packages": list(SCRIPTED_PACKAGES),
        "training_cells": list(TRAINING_CELLS),
        "heldout_cells": list(HELDOUT_CELLS),
    }:
        raise EmpiricalContractError("preactivity inventories differ")
    if mapping["activity_boundary"] != {
        "scientific_activity_started": False,
        "identity_present": False,
        "numeric_seed_present": False,
        "coordinate_present": False,
        "random_scientific_state_present": False,
        "model_or_checkpoint_present": False,
        "training_or_evaluation_present": False,
        "result_or_endpoint_present": False,
        "lease_present": False,
        "production_launch": False,
    }:
        raise EmpiricalContractError("preactivity boundary differs")
    return dict(mapping)


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EmpiricalContractError(f"benchmark {label} must be numeric")
    converted = float(value)
    if not math.isfinite(converted) or converted < 0.0:
        raise EmpiricalContractError(f"benchmark {label} must be finite and nonnegative")
    return converted


def validate_archived_preactivity_certificate(
    value: Mapping[str, object]
) -> dict[str, object]:
    """Validate an immutable historical production certificate by its own bytes."""

    return validate_preactivity_certificate(value, validate_live_sources=False)


def validate_benchmark_evidence_payload(
    payload: bytes, *, expected_sha256: str
) -> dict[str, object]:
    """Validate exact result-blind ABI2 benchmark bytes and derive resource facts."""

    _require_sha256(expected_sha256, "benchmark evidence")
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise EmpiricalContractError("benchmark evidence SHA-256 differs from source binding")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalContractError("benchmark evidence is not canonical ASCII JSON") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise EmpiricalContractError("benchmark evidence is not canonical ASCII JSON")
    required_top = {
        "abi2_event_lifecycle",
        "atomic_write_resume",
        "baseline_optimized_summary",
        "batched_reset_to_terminal",
        "chain_coverage",
        "command",
        "compile_load",
        "component_identity",
        "dominant_projected_component",
        "efficiency_review",
        "empirical_runner_measured",
        "fixture_only",
        "formal_activity",
        "learned_heldout_forward",
        "lease_readiness",
        "model_forward_backward",
        "projected_full_panel_cost",
        "python_fallback",
        "python_oracle_only",
        "rollback_nodes",
        "schema",
        "scientific_output_exposed",
        "scripted_consumers",
        "semantic_equivalence",
        "synthetic_72_tail_analyzer",
    }
    benchmark = _exact_mapping(value, required_top, "benchmark evidence")
    if (
        benchmark["schema"] != "RCLE_TBCFV_R04_FIXTURE_EFFICIENCY_REVIEW_V1"
        or benchmark["efficiency_review"] != "COMPLETE"
        or benchmark["lease_readiness"] != "WITHHOLD"
        or benchmark["fixture_only"] is not True
        or benchmark["empirical_runner_measured"] is not False
        or benchmark["formal_activity"] is not False
        or benchmark["scientific_output_exposed"] is not False
        or benchmark["python_fallback"] is not False
        or benchmark["python_oracle_only"] is not True
    ):
        raise EmpiricalContractError("benchmark activity/result-blind boundary differs")
    if benchmark["chain_coverage"] != {
        "abi2_event_lifecycle": True,
        "analyzer": True,
        "batch": True,
        "environment": True,
        "evaluation": True,
        "fixed_norm_update": True,
        "forward_backward": True,
        "io": True,
        "learned_heldout_forward": True,
        "loader": True,
        "resume": True,
        "rollout": True,
        "telemetry_complete": True,
    }:
        raise EmpiricalContractError("benchmark chain coverage is incomplete")
    if benchmark["semantic_equivalence"] != {
        "abi2_event_lifecycle_exact": True,
        "all_widths_exact": True,
        "all_widths_terminal": True,
        "chunk_order_exact": True,
        "scalar_order_exact": True,
    }:
        raise EmpiricalContractError("benchmark semantic equivalence differs")
    if benchmark["abi2_event_lifecycle"] != {
        "apply_event_batch_observed": True,
        "model_public_inputs_exclude_transport_keys": True,
        "pre_event_observed": True,
        "stable_transport_alignment": True,
    }:
        raise EmpiricalContractError("benchmark ABI2 event lifecycle differs")
    component = _exact_mapping(
        benchmark["component_identity"], {"abi", "contract", "source_sha256"}, "benchmark component"
    )
    if component["source_sha256"] != LEGACY_ACCEPTED_NATIVE_SOURCE_SHA256:
        raise EmpiricalContractError("benchmark native source identity is stale")
    if component["abi"] != {
        "abi_version": 2,
        "event_input_size": 64,
        "fixture_input_size": 224,
        "fixture_magic": 0x52434C4554424347,
        "snapshot_size": 464,
        "step_input_size": 64,
    }:
        raise EmpiricalContractError("benchmark native ABI2 identity differs")
    if component["contract"] != {
        "abi_version": 2,
        "backend": "cpp",
        "candidate_local_boundary": "RCLE-TBCFV-R04 full native host",
        "event_time_newcomer_position_input": True,
        "fixture_magic": 0x52434C4554424347,
        "interactive_reset_step_terminal": True,
        "process_local_warm_cache": True,
        "public_observation_excludes_transport_keys": True,
        "python_fallback": False,
        "python_oracle": "TEST-only",
        "rng": False,
        "shared_component_alias": None,
        "source_toolchain_runtime_abi_build_root_keyed": True,
        "stable_physical_agent_transport_keys": True,
        "supported_batch_widths": [1, 8, 32],
        "transport_keys_actor_model_visible": False,
    }:
        raise EmpiricalContractError("benchmark native component contract differs")
    command = _exact_mapping(
        benchmark["command"], {"batch_widths", "bounded_fixture_only", "repetitions"}, "benchmark command"
    )
    if (
        command["batch_widths"] != [1, 8, 32]
        or command["bounded_fixture_only"] is not True
        or isinstance(command["repetitions"], bool)
        or not isinstance(command["repetitions"], int)
        or command["repetitions"] <= 0
    ):
        raise EmpiricalContractError("benchmark command coverage differs")
    selection = _exact_mapping(
        benchmark["baseline_optimized_summary"],
        {
            "baseline_batch_width",
            "baseline_ticks_per_second",
            "selected_batch_width",
            "selected_ticks_per_second",
            "selection_rule",
        },
        "benchmark batch selection",
    )
    if (
        selection["baseline_batch_width"] != 1
        or selection["selected_batch_width"] != SELECTED_BATCH_WIDTH
        or selection["selection_rule"]
        != "maximum measured ticks_per_second; exact ties choose lower batch width"
        or _finite_nonnegative(selection["baseline_ticks_per_second"], "baseline throughput") <= 0.0
        or _finite_nonnegative(selection["selected_ticks_per_second"], "selected throughput") <= 0.0
    ):
        raise EmpiricalContractError("benchmark selected width/throughput differs")
    atomic = _exact_mapping(
        benchmark["atomic_write_resume"],
        {
            "atomic_write",
            "durable_bytes",
            "empirical_runner_measured",
            "resume_exact",
            "resume_scan_restore",
            "run_blocks",
            "scratch_bytes_peak",
        },
        "benchmark atomic resume",
    )
    if (
        atomic["empirical_runner_measured"] is not False
        or atomic["resume_exact"] is not True
        or atomic["run_blocks"] != 20
    ):
        raise EmpiricalContractError("benchmark atomic/resume evidence differs")
    model = benchmark["model_forward_backward"]
    learned = benchmark["learned_heldout_forward"]
    scripted = benchmark["scripted_consumers"]
    analyzer = benchmark["synthetic_72_tail_analyzer"]
    if not isinstance(model, Mapping) or any(
        model.get(key) is not True
        for key in (
            "actor_path",
            "backward_completed",
            "deterministic_fixture",
            "fixed_norm_update_completed",
            "flex_path",
            "stopped_normal_score_path",
        )
    ):
        raise EmpiricalContractError("benchmark model/update evidence is incomplete")
    if not isinstance(learned, Mapping) or learned.get("deterministic_fixture") is not True or learned.get("forward_completed") is not True:
        raise EmpiricalContractError("benchmark learned evaluation evidence is incomplete")
    if not isinstance(scripted, Mapping) or scripted.get("completed") is not True or scripted.get("outcome_values_exposed") is not False:
        raise EmpiricalContractError("benchmark scripted evidence is incomplete or exposed")
    if not isinstance(analyzer, Mapping) or any(
        analyzer.get(key) is not expected
        for key, expected in {
            "completed": True,
            "construction_guards_verified": True,
            "fixture_only": True,
            "interpretation_value_exposed": False,
            "non_scientific": True,
            "schema_identity_verified": True,
        }.items()
    ) or analyzer.get("synthetic_tail_count") != 72:
        raise EmpiricalContractError("benchmark analyzer evidence differs")
    projection = _exact_mapping(
        benchmark["projected_full_panel_cost"],
        {
            "basis",
            "components",
            "cpu_seconds",
            "frozen_component_counts",
            "material_delta",
            "measured_resource_basis",
            "prior_envelope_comparison",
            "uncertainty",
            "wall_seconds",
        },
        "benchmark full-panel projection",
    )
    if projection["basis"] != "sum of named deterministic fixture components scaled only by frozen workload counts":
        raise EmpiricalContractError("benchmark projection basis differs")
    if projection["frozen_component_counts"] != {
        "analyzer_invocations": 1,
        "atomic_run_blocks": 20,
        "cold_loads_per_worker": 1,
        "learned_arm_run_block_updates": 80_000,
        "learned_heldout_agent_decisions": 262_144_000,
        "native_host_ticks": 495_452_160,
        "scripted_claim_clock_consumer_calls": 15_728_640,
    }:
        raise EmpiricalContractError("benchmark frozen component counts differ")
    components = projection["components"]
    expected_component_names = (
        "cold_load_per_worker",
        "native_host_width_8",
        "learned_update_forward_backward",
        "learned_heldout_forward",
        "scripted_claim_clock_consumers",
        "synthetic_72_tail_analyzer",
        "atomic_publish_resume",
    )
    if not isinstance(components, list) or tuple(
        row.get("name") if isinstance(row, Mapping) else None for row in components
    ) != expected_component_names:
        raise EmpiricalContractError("benchmark projected component inventory differs")
    for row in components:
        assert isinstance(row, Mapping)
        if row.get("cpu_basis_kind") != "measured" or not isinstance(
            row.get("measurement"), Mapping
        ):
            raise EmpiricalContractError("benchmark component lacks measured basis")
        measurement = row["measurement"]
        assert isinstance(measurement, Mapping)
        if measurement.get("telemetry_available") is not True or measurement.get("telemetry_error") is not None:
            raise EmpiricalContractError("benchmark component telemetry is incomplete")
        for key in ("projected_cpu_seconds", "projected_wall_seconds", "total_units"):
            _finite_nonnegative(row.get(key), f"component {row['name']} {key}")
    cpu = _exact_mapping(
        projection["cpu_seconds"], {"one_worker", "up_to_four_workers"}, "benchmark CPU projection"
    )
    wall = _exact_mapping(
        projection["wall_seconds"],
        {"one_worker", "up_to_four_equivalence_supported"},
        "benchmark wall projection",
    )
    four_wall = _exact_mapping(
        wall["up_to_four_equivalence_supported"], {"lower", "upper"}, "benchmark four-worker wall"
    )
    resources = _exact_mapping(
        projection["measured_resource_basis"],
        {
            "durable_fixture_bytes_for_20_blocks",
            "measured_read_bytes",
            "measured_write_bytes",
            "rss_per_worker_bytes",
            "scratch_fixture_bytes_peak",
        },
        "benchmark resource basis",
    )
    cpu_seconds = _finite_nonnegative(cpu["one_worker"], "one-worker CPU")
    one_wall_seconds = _finite_nonnegative(wall["one_worker"], "one-worker wall")
    four_lower_seconds = _finite_nonnegative(four_wall["lower"], "four-worker lower wall")
    four_upper_seconds = _finite_nonnegative(four_wall["upper"], "four-worker upper wall")
    if cpu_seconds <= 0.0 or one_wall_seconds <= 0.0 or four_lower_seconds <= 0.0 or four_upper_seconds != one_wall_seconds:
        raise EmpiricalContractError("benchmark projected CPU/wall values differ")
    measured = {
        key: int(_finite_nonnegative(resources[key], key))
        for key in (
            "rss_per_worker_bytes",
            "measured_read_bytes",
            "measured_write_bytes",
            "durable_fixture_bytes_for_20_blocks",
            "scratch_fixture_bytes_peak",
        )
    }
    if any(measured[key] != resources[key] for key in measured):
        raise EmpiricalContractError("benchmark measured resource bytes must be integers")
    return {
        "logical_path": BENCHMARK_EVIDENCE_LOGICAL_PATH,
        "sha256": actual_sha256,
        "schema": benchmark["schema"],
        "native_source_sha256": component["source_sha256"],
        "projected_cpu_core_hours": cpu_seconds / 3600.0,
        "projected_wall_hours_one_worker": one_wall_seconds / 3600.0,
        "projected_wall_hours_four_workers_lower": four_lower_seconds / 3600.0,
        "measured_basis": measured,
    }


def _load_bound_benchmark_evidence(
    certificate: Mapping[str, object],
) -> dict[str, object]:
    source = certificate["source"]
    assert isinstance(source, Mapping)
    files = source["files"]
    assert isinstance(files, Mapping)
    row = files.get(PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH)
    if not isinstance(row, Mapping):
        raise EmpiricalContractError("production protocol evidence is absent from source binding")
    expected_sha256 = _require_sha256(row.get("sha256"), "benchmark source row")
    path = production_source_paths()[PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH].resolve(strict=True)
    payload = path.read_bytes()
    evidence = validate_production_protocol_evidence_payload(
        payload, expected_sha256=expected_sha256
    )
    if row.get("bytes") != len(payload):
        raise EmpiricalContractError("benchmark evidence byte count differs from source binding")
    bound = evidence["source_binding"]
    assert isinstance(bound, Mapping)
    expected_bound_rows = {
        "native_source_sha256": "experiments/candidates/roster_consistent_latent_exploration_tbcfv/native/tbcfv_backend.cpp",
        "empirical_runner_sha256": "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py",
        "process_workers_sha256": PROCESS_WORKERS_LOGICAL_PATH,
        "benchmark_sha256": PRODUCTION_PROTOCOL_BENCHMARK_SCRIPT_LOGICAL_PATH,
    }
    for evidence_key, logical_path in expected_bound_rows.items():
        source_row = files.get(logical_path)
        if not isinstance(source_row, Mapping) or bound[evidence_key] != source_row.get("sha256"):
            raise EmpiricalContractError("production protocol evidence source bytes differ")
    return {
        **evidence,
        "source_set_sha256": source["source_set_sha256"],
    }


def validate_production_protocol_evidence_payload(
    payload: bytes, *, expected_sha256: str
) -> dict[str, object]:
    """Validate the non-circular current-byte production-protocol evidence."""

    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != _require_sha256(expected_sha256, "protocol evidence"):
        raise EmpiricalContractError("production protocol evidence SHA-256 differs")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalContractError("production protocol evidence is not ASCII JSON") from exc
    required = {
        "schema", "mode", "source_binding", "projection", "resources",
        "equivalence", "failure_resume", "ceiling_checks",
        "scientific_identity_materialized", "production_authority_used",
        "result_value_exposed",
    }
    evidence = _exact_mapping(value, required, "production protocol evidence")
    if canonical_json_bytes(evidence) != payload:
        raise EmpiricalContractError("production protocol evidence is not canonical")
    if (
        evidence["schema"] != "RCLE_TBCFV_R04_PRODUCTION_PROTOCOL_EFFICIENCY_EVIDENCE_V1"
        or evidence["mode"] != "FIXED_SYNTHETIC_RESULT_BLIND_PRODUCTION_PROTOCOL"
        or evidence["scientific_identity_materialized"] is not False
        or evidence["production_authority_used"] is not False
        or evidence["result_value_exposed"] is not False
    ):
        raise EmpiricalContractError("production protocol evidence boundary differs")
    source = _exact_mapping(
        evidence["source_binding"],
        {
            "native_source_sha256", "native_build_key", "native_artifact_sha256",
            "empirical_runner_sha256", "process_workers_sha256", "benchmark_sha256",
        },
        "production protocol source binding",
    )
    for key, item in source.items():
        _require_sha256(item, f"protocol {key}")
    if (
        source["native_source_sha256"] != ACCEPTED_NATIVE_SOURCE_SHA256
        or source["native_build_key"] != ACCEPTED_NATIVE_BUILD_KEY
        or source["native_artifact_sha256"] != ACCEPTED_NATIVE_ARTIFACT_SHA256
    ):
        raise EmpiricalContractError("production protocol native identity differs")
    projection = _exact_mapping(
        evidence["projection"],
        {
            "complete_cpu_core_hours", "one_process_wall_hours",
            "four_process_wall_hours", "checkpoint_read_bytes",
            "checkpoint_write_bytes",
        },
        "production protocol projection",
    )
    cpu = _finite_nonnegative(projection["complete_cpu_core_hours"], "protocol CPU")
    wall_one = _finite_nonnegative(projection["one_process_wall_hours"], "protocol one-process wall")
    wall_four = _finite_nonnegative(projection["four_process_wall_hours"], "protocol four-process wall")
    checkpoint_read = int(_finite_nonnegative(projection["checkpoint_read_bytes"], "protocol checkpoint read"))
    checkpoint_write = int(_finite_nonnegative(projection["checkpoint_write_bytes"], "protocol checkpoint write"))
    resources = _exact_mapping(
        evidence["resources"],
        {
            "process_group_rss_bytes", "private_scratch_projected_bytes",
            "canonical_durable_projected_bytes", "measured_io_read_bytes",
            "measured_io_write_bytes",
        },
        "production protocol resources",
    )
    normalized_resources = {
        key: int(_finite_nonnegative(item, f"protocol {key}"))
        for key, item in resources.items()
    }
    if any(normalized_resources[key] != resources[key] for key in resources):
        raise EmpiricalContractError("production protocol resource bytes are not integers")
    equivalence = _exact_mapping(
        evidence["equivalence"],
        {
            "widths_1_8_32_exact", "spawn_1_2_4_exact",
            "normalized_block_tree_sha256", "parent_prevalidation_install_exact",
            "closed_one_block_authorization_exact",
        },
        "production protocol equivalence",
    )
    if any(equivalence[key] is not True for key in equivalence if key != "normalized_block_tree_sha256"):
        raise EmpiricalContractError("production protocol equivalence differs")
    _require_sha256(equivalence["normalized_block_tree_sha256"], "protocol equivalence")
    failure = _exact_mapping(
        evidence["failure_resume"],
        {
            "injected_failure_observed", "packet_absent_after_failure",
            "canonical_absent_after_failure", "same_payload_resumed",
            "private_generation_preserved", "final_packet_exact",
        },
        "production protocol failure/resume",
    )
    if any(item is not True for item in failure.values()):
        raise EmpiricalContractError("production protocol failure/resume differs")
    checks = evidence["ceiling_checks"]
    if not isinstance(checks, Mapping) or not checks or any(item is not True for item in checks.values()):
        raise EmpiricalContractError("production protocol ceiling check failed")
    if (
        cpu > CPU_HOURS_CEILING
        or wall_four > FOUR_PROCESS_WALL_HOURS_CEILING
        or normalized_resources["process_group_rss_bytes"] > PROCESS_GROUP_RSS_CEILING
        or normalized_resources["private_scratch_projected_bytes"] > PRIVATE_SCRATCH_COMBINED_CEILING
        or normalized_resources["canonical_durable_projected_bytes"] > CANONICAL_DURABLE_CEILING
        or checkpoint_read > CHECKPOINT_READ_CEILING
        or checkpoint_write > CHECKPOINT_WRITE_CEILING
    ):
        raise EmpiricalContractError("production protocol evidence exceeds fixed ceiling")
    return {
        "logical_path": PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH,
        "sha256": actual_sha256,
        "schema": evidence["schema"],
        "native_source_sha256": source["native_source_sha256"],
        "projected_cpu_core_hours": cpu,
        "projected_wall_hours_one_worker": wall_one,
        "projected_wall_hours_four_workers": wall_four,
        "measured_basis": normalized_resources,
        "checkpoint_read_bytes": checkpoint_read,
        "checkpoint_write_bytes": checkpoint_write,
        "equivalence": dict(equivalence),
        "failure_resume": dict(failure),
        "source_binding": dict(source),
    }


def resource_request_proposal(
    certificate: Mapping[str, object], *, repository_root: Path, result_root: Path
) -> dict[str, object]:
    """Create a request-only resource packet; it is never a lease."""

    validated = validate_preactivity_certificate(certificate)
    repository = Path(repository_root).resolve(strict=True)
    result = Path(result_root).resolve()
    try:
        result.relative_to(repository)
    except ValueError as exc:
        raise EmpiricalContractError("proposed result root escapes repository") from exc
    proposal = validated["coordinate_proposal"]
    assert isinstance(proposal, Mapping)
    native = validated["native"]
    assert isinstance(native, Mapping)
    benchmark = _load_bound_benchmark_evidence(validated)
    measured = benchmark["measured_basis"]
    assert isinstance(measured, Mapping)
    projected_cpu_core_hours = float(benchmark["projected_cpu_core_hours"])
    projected_wall_hours_one_worker = float(
        benchmark["projected_wall_hours_one_worker"]
    )
    projected_wall_hours_four_workers = float(
        benchmark["projected_wall_hours_four_workers"]
    )
    if projected_cpu_core_hours > CPU_HOURS_CEILING:
        raise EmpiricalContractError("benchmark CPU projection exceeds stage ceiling")
    if int(measured["process_group_rss_bytes"]) > PROCESS_GROUP_RSS_CEILING:
        raise EmpiricalContractError("benchmark process-group RSS exceeds stage ceiling")
    if int(measured["canonical_durable_projected_bytes"]) > CANONICAL_DURABLE_CEILING:
        raise EmpiricalContractError("benchmark durable bytes exceed stage ceiling")
    if int(measured["private_scratch_projected_bytes"]) > PRIVATE_SCRATCH_COMBINED_CEILING:
        raise EmpiricalContractError("benchmark scratch bytes exceed stage ceiling")
    private_scope = str(proposal["proposal_sha256"])[:12]
    private_parent = result.parent / ".r04p" / private_scope
    process_resource = validate_process_resource_object(
        make_process_resource_object(
            canonical_result_root=result,
            private_scratch_roots=[
                private_parent / f"worker_{index:02d}" for index in range(4)
            ],
            source_set_sha256=str(validated["source"]["source_set_sha256"]),  # type: ignore[index]
            native_binding_sha256=str(native["native_identity_sha256"]),
        )
    )
    process_paths = process_resource["paths"]
    assert isinstance(process_paths, Mapping)
    paths = {
        "result_root": str(result),
        "frontier_root": str(result / "frontiers"),
        "run_identity_path": str(result / "RUN_IDENTITY.json"),
        "complete_manifest_path": str(result / "COMPLETE_MANIFEST.json"),
        "technical_acceptance_path": str(result / "CM_TECHNICAL_ACCEPTANCE.json"),
        **{str(key): str(item) for key, item in process_paths.items()},
    }
    return {
        "schema": RESOURCE_REQUEST_SCHEMA,
        "authority": "REQUEST_ONLY",
        "lease_issued": False,
        "activity_authorized": False,
        "production_launch": False,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": validated["certificate_sha256"],
        "coordinate_proposal_sha256": proposal["proposal_sha256"],
        "source_set_sha256": validated["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": validated["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": native["native_identity_sha256"],
        "analyzer_sha256": validated["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "benchmark_evidence": benchmark,
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "paths": paths,
        "resources": {
            "cpu_only": True,
            "gpu_count": 0,
            "one_thread_per_worker": True,
            "max_independent_workers": 4,
            "projected_cpu_core_hours": projected_cpu_core_hours,
            "cpu_core_hours_upper": CPU_HOURS_CEILING,
            "projected_wall_hours_one_worker": projected_wall_hours_one_worker,
            "projected_wall_hours_four_workers_lower": projected_wall_hours_four_workers,
            "projected_wall_hours_four_workers": projected_wall_hours_four_workers,
            "measured_process_group_rss_bytes": int(measured["process_group_rss_bytes"]),
            "measured_io_read_bytes": int(measured["measured_io_read_bytes"]),
            "measured_io_write_bytes": int(measured["measured_io_write_bytes"]),
            "projected_canonical_durable_bytes": int(
                measured["canonical_durable_projected_bytes"]
            ),
            "projected_private_scratch_bytes": int(
                measured["private_scratch_projected_bytes"]
            ),
            "projected_checkpoint_read_bytes": int(benchmark["checkpoint_read_bytes"]),
            "projected_checkpoint_write_bytes": int(benchmark["checkpoint_write_bytes"]),
            "process_group_rss_bytes_upper": PROCESS_GROUP_RSS_CEILING,
            "scratch_gib_upper": 12.0,
            "durable_artifacts_gib_upper": 1.0,
            "checkpoint_read_bytes_upper": CHECKPOINT_READ_CEILING,
            "checkpoint_write_bytes_upper": CHECKPOINT_WRITE_CEILING,
            "process_resource": process_resource,
            "validity_hours": 24,
        },
        "counts": dict(PANEL_COUNTS),
        "complete_panel_only": True,
        "result_blind": True,
        "python_fallback": False,
        "coordinate_materialization": "ONLY_AFTER_ROOT_LEASE_AND_CM_ACCEPTED_BINDING",
        "renewal": {
            "same_coordinate_resume_only": True,
            "immutable_origin_lease_id": True,
            "immutable_stage_binding_sha256": True,
            "immediate_predecessor_required": True,
            "replacement_index_increments_by_one": True,
            "windows_are_contiguous_and_nonoverlapping": True,
            "accepted_preactivity_and_coordinate_proposal_preserved": True,
            "source_config_native_analyzer_preserved": True,
            "result_root_preserved": True,
            "worker_and_resource_stage_ceiling_preserved": True,
            "replacement_coordinate_materialization": False,
        },
    }


def validate_accepted_binding(
    value: Mapping[str, object],
    certificate: Mapping[str, object],
    *,
    validate_live_sources: bool = True,
) -> dict[str, object]:
    """Validate, but never create, a future CM-owned preactivity acceptance."""

    cert = validate_preactivity_certificate(
        certificate, validate_live_sources=validate_live_sources
    )
    required = {
        "schema",
        "issuer",
        "technically_accepted",
        "direction_id",
        "science_revision",
        "empirical_object",
        "preactivity_certificate_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "coordinate_proposal_sha256",
        "result_blind",
        "scientific_activity_started",
        "binding_sha256",
    }
    mapping = _exact_mapping(value, required, "CM accepted binding")
    body = {key: mapping[key] for key in required - {"binding_sha256"}}
    if mapping["binding_sha256"] != document_sha256(body):
        raise EmpiricalContractError("CM accepted binding digest differs")
    proposal = cert["coordinate_proposal"]
    assert isinstance(proposal, Mapping)
    expected = {
        "schema": CM_ACCEPTED_BINDING_SCHEMA,
        "issuer": CM_OWNER,
        "technically_accepted": True,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "coordinate_proposal_sha256": proposal["proposal_sha256"],
        "result_blind": True,
        "scientific_activity_started": False,
    }
    if body != expected:
        raise EmpiricalContractError("CM accepted binding differs from certificate")
    return dict(mapping)


def validate_archived_accepted_binding(
    value: Mapping[str, object], certificate: Mapping[str, object]
) -> dict[str, object]:
    """Validate an immutable historical CM binding against archived source bytes."""

    return validate_accepted_binding(value, certificate, validate_live_sources=False)


def _validated_resource_request(
    certificate: Mapping[str, object], resource_request: Mapping[str, object]
) -> dict[str, object]:
    cert = validate_preactivity_certificate(certificate)
    request = dict(resource_request)
    request_paths = request.get("paths")
    if not isinstance(request_paths, Mapping) or not isinstance(
        request_paths.get("result_root"), str
    ):
        raise LeaseError("resource request paths are malformed")
    try:
        expected = resource_request_proposal(
            cert,
            repository_root=Path(__file__).resolve().parents[3],
            result_root=Path(str(request_paths["result_root"])),
        )
    except EmpiricalContractError as exc:
        raise LeaseError("resource request is not an exact in-repository proposal") from exc
    if request != expected:
        raise LeaseError("resource request differs from the exact request-only proposal")
    return request


def validate_archived_resource_request(
    value: Mapping[str, object], certificate: Mapping[str, object]
) -> dict[str, object]:
    """Validate an immutable pre-repair request without consulting live sources."""

    cert = validate_preactivity_certificate(
        certificate, validate_live_sources=False
    )
    required = {
        "schema",
        "authority",
        "lease_issued",
        "activity_authorized",
        "production_launch",
        "direction_id",
        "science_revision",
        "empirical_object",
        "preactivity_certificate_sha256",
        "coordinate_proposal_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "benchmark_evidence",
        "component",
        "abi_version",
        "batch_width",
        "paths",
        "resources",
        "counts",
        "complete_panel_only",
        "result_blind",
        "python_fallback",
        "coordinate_materialization",
        "renewal",
    }
    request = _exact_mapping(value, required, "archived resource request")
    fixed = {
        "schema": RESOURCE_REQUEST_SCHEMA,
        "authority": "REQUEST_ONLY",
        "lease_issued": False,
        "activity_authorized": False,
        "production_launch": False,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "coordinate_proposal_sha256": cert["coordinate_proposal"]["proposal_sha256"],  # type: ignore[index]
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind": True,
        "python_fallback": False,
        "coordinate_materialization": "ONLY_AFTER_ROOT_LEASE_AND_CM_ACCEPTED_BINDING",
    }
    for key, expected in fixed.items():
        if request.get(key) != expected:
            raise EmpiricalContractError(f"archived resource request differs: {key}")
    benchmark = request["benchmark_evidence"]
    if (
        isinstance(benchmark, Mapping)
        and benchmark.get("logical_path") == PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH
    ):
        expected_benchmark_keys = {
            "logical_path", "sha256", "schema", "native_source_sha256",
            "projected_cpu_core_hours", "projected_wall_hours_one_worker",
            "projected_wall_hours_four_workers", "measured_basis",
            "checkpoint_read_bytes", "checkpoint_write_bytes", "equivalence",
            "failure_resume", "source_binding", "source_set_sha256",
        }
        if set(benchmark) != expected_benchmark_keys:
            raise EmpiricalContractError("archived protocol evidence inventory differs")
        if (
            benchmark["source_set_sha256"] != cert["source"]["source_set_sha256"]  # type: ignore[index]
            or benchmark["native_source_sha256"] != cert["native"]["source_sha256"]  # type: ignore[index]
        ):
            raise EmpiricalContractError("archived protocol/source binding differs")
        resources = request["resources"]
        measured = benchmark["measured_basis"]
        if not isinstance(resources, Mapping) or not isinstance(measured, Mapping):
            raise EmpiricalContractError("archived protocol resources are malformed")
        process_resource_value = resources.get("process_resource")
        if not isinstance(process_resource_value, Mapping):
            raise EmpiricalContractError(
                "archived protocol resource measurements differ: process resource is absent"
            )
        process_resource = validate_process_resource_object(process_resource_value)
        expected_links = {
            "projected_cpu_core_hours": benchmark["projected_cpu_core_hours"],
            "projected_wall_hours_one_worker": benchmark["projected_wall_hours_one_worker"],
            "projected_wall_hours_four_workers": benchmark["projected_wall_hours_four_workers"],
            "projected_wall_hours_four_workers_lower": benchmark["projected_wall_hours_four_workers"],
            "measured_process_group_rss_bytes": measured.get("process_group_rss_bytes"),
            "measured_io_read_bytes": measured.get("measured_io_read_bytes"),
            "measured_io_write_bytes": measured.get("measured_io_write_bytes"),
            "projected_canonical_durable_bytes": measured.get("canonical_durable_projected_bytes"),
            "projected_private_scratch_bytes": measured.get("private_scratch_projected_bytes"),
            "projected_checkpoint_read_bytes": benchmark["checkpoint_read_bytes"],
            "projected_checkpoint_write_bytes": benchmark["checkpoint_write_bytes"],
        }
        if any(resources.get(key) != item for key, item in expected_links.items()):
            raise EmpiricalContractError("archived protocol resource measurements differ")
        if (
            process_resource["source_set_sha256"] != cert["source"]["source_set_sha256"]  # type: ignore[index]
            or process_resource["native_binding_sha256"] != cert["native"]["native_identity_sha256"]  # type: ignore[index]
        ):
            raise EmpiricalContractError("archived process resource identity differs")
        paths = request["paths"]
        process_paths = process_resource["paths"]
        if not isinstance(paths, Mapping) or not isinstance(process_paths, Mapping):
            raise EmpiricalContractError("archived protocol path inventory differs")
        standard_keys = {
            "result_root", "frontier_root", "run_identity_path",
            "complete_manifest_path", "technical_acceptance_path",
        }
        if set(paths) != standard_keys | set(process_paths) or any(
            paths.get(key) != item for key, item in process_paths.items()
        ):
            raise EmpiricalContractError("archived protocol path inventory differs")
        result_root = Path(str(paths["result_root"])).resolve()
        try:
            result_root.relative_to(Path(__file__).resolve().parents[3])
        except ValueError as exc:
            raise EmpiricalContractError("archived result root escapes repository") from exc
        return dict(request)
    if not isinstance(benchmark, Mapping) or set(benchmark) != {
        "logical_path",
        "sha256",
        "schema",
        "native_source_sha256",
        "projected_cpu_core_hours",
        "projected_wall_hours_one_worker",
        "projected_wall_hours_four_workers_lower",
        "measured_basis",
        "source_set_sha256",
    }:
        raise EmpiricalContractError("archived benchmark evidence inventory differs")
    source_files = cert["source"]["files"]  # type: ignore[index]
    assert isinstance(source_files, Mapping)
    benchmark_row = source_files[BENCHMARK_EVIDENCE_LOGICAL_PATH]
    assert isinstance(benchmark_row, Mapping)
    if (
        benchmark["logical_path"] != BENCHMARK_EVIDENCE_LOGICAL_PATH
        or benchmark["sha256"] != benchmark_row["sha256"]
        or benchmark["source_set_sha256"] != cert["source"]["source_set_sha256"]  # type: ignore[index]
        or benchmark["native_source_sha256"] != cert["native"]["source_sha256"]  # type: ignore[index]
    ):
        raise EmpiricalContractError("archived benchmark/source binding differs")
    resources = request["resources"]
    measured = benchmark["measured_basis"]
    if not isinstance(resources, Mapping) or not isinstance(measured, Mapping):
        raise EmpiricalContractError("archived resource measurements are malformed")
    expected_resource_links = {
        "projected_cpu_core_hours": benchmark["projected_cpu_core_hours"],
        "projected_wall_hours_one_worker": benchmark["projected_wall_hours_one_worker"],
        "projected_wall_hours_four_workers_lower": benchmark[
            "projected_wall_hours_four_workers_lower"
        ],
        "measured_rss_bytes_per_worker": measured.get("rss_per_worker_bytes"),
        "measured_io_read_bytes": measured.get("measured_read_bytes"),
        "measured_io_write_bytes": measured.get("measured_write_bytes"),
        "measured_durable_fixture_bytes": measured.get(
            "durable_fixture_bytes_for_20_blocks"
        ),
        "measured_scratch_fixture_bytes_peak": measured.get(
            "scratch_fixture_bytes_peak"
        ),
    }
    if any(resources.get(key) != item for key, item in expected_resource_links.items()):
        raise EmpiricalContractError("archived resource/benchmark measurements differ")
    for key, expected in {
        "cpu_only": True,
        "gpu_count": 0,
        "one_thread_per_worker": True,
        "max_independent_workers": 4,
        "cpu_core_hours_upper": 30.0,
        "rss_gib_per_worker_upper": 4.0,
        "scratch_gib_upper": 12.0,
        "durable_artifacts_gib_upper": 1.0,
        "validity_hours": 24,
    }.items():
        if resources.get(key) != expected:
            raise EmpiricalContractError(f"archived resource ceiling differs: {key}")
    paths = request["paths"]
    if not isinstance(paths, Mapping) or set(paths) != {
        "result_root",
        "frontier_root",
        "run_identity_path",
        "complete_manifest_path",
        "technical_acceptance_path",
    }:
        raise EmpiricalContractError("archived resource path inventory differs")
    result_root = Path(str(paths["result_root"])).resolve()
    repository = Path(__file__).resolve().parents[3]
    try:
        result_root.relative_to(repository)
    except ValueError as exc:
        raise EmpiricalContractError("archived result root escapes repository") from exc
    if any(
        Path(str(path)).resolve() != result_root / Path(str(path)).name
        for key, path in paths.items()
        if key not in {"result_root", "frontier_root"}
    ) or Path(str(paths["frontier_root"])).resolve() != result_root / "frontiers":
        raise EmpiricalContractError("archived resource paths drift from result root")
    return dict(request)


def stage_binding_identity(
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
) -> dict[str, object]:
    """Build the immutable frontier/stage binding shared by every lease window."""

    cert = validate_preactivity_certificate(certificate)
    binding = validate_accepted_binding(accepted_binding, cert)
    request = _validated_resource_request(cert, resource_request)
    return _stage_binding_from_validated(cert, binding, request)


def _stage_binding_from_validated(
    cert: Mapping[str, object],
    binding: Mapping[str, object],
    request: Mapping[str, object],
) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": "RCLE_TBCFV_R04_IMMUTABLE_STAGE_BINDING_V1",
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "accepted_binding_sha256": binding["binding_sha256"],
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "coordinate_proposal_sha256": cert["coordinate_proposal"]["proposal_sha256"],  # type: ignore[index]
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "benchmark_evidence": request["benchmark_evidence"],
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "paths": request["paths"],
        "result_root": request["paths"]["result_root"],  # type: ignore[index]
        "worker_and_resource_stage_ceiling": request["resources"],
        "counts": dict(PANEL_COUNTS),
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "same_coordinate_resume_only": True,
    }
    return {**body, "stage_binding_sha256": document_sha256(body)}


@dataclass(frozen=True, repr=False)
class RootLeasePermit:
    lease_id: str
    origin_lease_id: str
    predecessor_lease_id: str | None
    replacement_index: int
    lease_lineage: tuple[str, ...]
    stage_binding_sha256: str
    accepted_binding_sha256: str
    preactivity_certificate_sha256: str
    coordinate_proposal_sha256: str
    issued_at: str
    expires_at: str
    paths: Mapping[str, str]
    resources: Mapping[str, object]
    fixture_only: bool
    repair_transition_sha256: str | None = None
    archived_only: bool = False
    _seal: object | None = None

    def require_active(self, *, now: datetime) -> None:
        if self._seal is not _PERMIT_SEAL:
            raise LeaseError("unvalidated Root lease permit")
        if self.archived_only:
            raise LeaseError("archived initial lease cannot authorize activity")
        start = _parse_aware_datetime(self.issued_at, "issued_at")
        end = _parse_aware_datetime(self.expires_at, "expires_at")
        if now.tzinfo is None or not start <= now < end:
            raise LeaseError("Root lease is inactive")

    def runtime_authority(self) -> dict[str, object]:
        """Expose the renewable current window; never use this as frontier identity."""

        if self._seal is not _PERMIT_SEAL or self.fixture_only or self.archived_only:
            raise LeaseError("runtime authority requires a production validated permit")
        return {
            "lease_id": self.lease_id,
            "origin_lease_id": self.origin_lease_id,
            "predecessor_lease_id": self.predecessor_lease_id,
            "replacement_index": self.replacement_index,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }

    def immutable_frontier_lease_binding(self) -> dict[str, str]:
        """Map onto the visible empirical-artifact binding without renewal drift."""

        if self._seal is not _PERMIT_SEAL or self.archived_only:
            raise LeaseError("frontier binding requires a validated permit")
        return {
            "origin_lease_id": self.origin_lease_id,
            # EmpiricalBindings currently names this field ``lease_id``.  It is
            # deliberately the immutable origin, not the renewable runtime id.
            "lease_id": self.origin_lease_id,
            "lease_binding_sha256": self.stage_binding_sha256,
        }


def _read_canonical_artifact(path: str | Path, label: str) -> tuple[dict[str, object], str]:
    target = Path(path)
    if not target.is_file() or target.is_symlink():
        raise EmpiricalContractError(f"{label} is absent or not a regular file")
    payload = target.read_bytes()
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalContractError(f"{label} is not canonical ASCII JSON") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise EmpiricalContractError(f"{label} is not canonical ASCII JSON")
    return dict(value), hashlib.sha256(payload).hexdigest()


def validate_frozen_run_identity(
    path: str | Path,
    permit: RootLeasePermit,
    *,
    synthetic_fixture: bool = False,
) -> dict[str, object]:
    """Validate the already materialized identity without deriving any coordinate."""

    if permit._seal is not _PERMIT_SEAL or permit.fixture_only is not synthetic_fixture:
        raise EmpiricalContractError("run identity permit is not the exact validated mode")
    target = Path(path).resolve()
    if target != Path(permit.paths["run_identity_path"]).resolve():
        raise EmpiricalContractError("RUN_IDENTITY path differs from original request")
    value, file_sha256 = _read_canonical_artifact(target, "RUN_IDENTITY")
    keys = {
        "schema",
        "identity",
        "science_revision",
        "empirical_object",
        "fixture_only",
        "non_scientific",
        "authority",
        "stage_binding_sha256",
        "numeric_seed_present",
        "master_material_exposed",
        "master_digest",
        "run_block_count",
        "run_block_roots",
        "binding_sha256",
    }
    identity = _exact_mapping(value, keys, "RUN_IDENTITY")
    body = {key: identity[key] for key in keys - {"binding_sha256"}}
    if identity["binding_sha256"] != document_sha256(body):
        raise EmpiricalContractError("RUN_IDENTITY binding digest differs")
    expected_object = "SYNTHETIC-TEST-ONLY" if synthetic_fixture else EMPIRICAL_OBJECT
    if (
        identity["schema"] != MATERIALIZED_BINDING_SCHEMA
        or identity["science_revision"] != SCIENCE_REVISION
        or identity["empirical_object"] != expected_object
        or identity["fixture_only"] is not synthetic_fixture
        or identity["non_scientific"] is not synthetic_fixture
        or identity["authority"] != permit.origin_lease_id
        or identity["stage_binding_sha256"] != permit.stage_binding_sha256
        or identity["numeric_seed_present"] is not False
        or identity["master_material_exposed"] is not False
        or identity["run_block_count"] != 20
    ):
        raise EmpiricalContractError("RUN_IDENTITY frozen binding differs")
    run_identity = _safe_identity(identity["identity"], "RUN_IDENTITY identity")
    if synthetic_fixture:
        if not run_identity.upper().startswith("SYNTHETIC"):
            raise EmpiricalContractError("synthetic RUN_IDENTITY label is not explicit")
    elif run_identity.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")):
        raise EmpiricalContractError("synthetic RUN_IDENTITY is forbidden in production")
    master_digest = _require_sha256(identity["master_digest"], "RUN_IDENTITY master")
    binding_sha256 = _require_sha256(identity["binding_sha256"], "RUN_IDENTITY binding")
    roots = identity["run_block_roots"]
    if not isinstance(roots, list) or len(roots) != 20:
        raise EmpiricalContractError("RUN_IDENTITY must contain twenty roots")
    root_digests: list[str] = []
    for index, row in enumerate(roots):
        if not isinstance(row, Mapping) or set(row) != {"block_index", "root_digest"}:
            raise EmpiricalContractError("RUN_IDENTITY root inventory differs")
        if row["block_index"] != index:
            raise EmpiricalContractError("RUN_IDENTITY roots are not ordered 0..19")
        root_digests.append(_require_sha256(row["root_digest"], "RUN_IDENTITY root"))
    if len(set(root_digests)) != 20:
        raise EmpiricalContractError("RUN_IDENTITY roots are not pairwise distinct")
    return {
        "path": str(target),
        "file_sha256": file_sha256,
        "binding_sha256": binding_sha256,
        "master_digest": master_digest,
        "run_block_roots": [dict(row) for row in roots],
        "identity": run_identity,
        "stage_binding_sha256": permit.stage_binding_sha256,
        "origin_lease_id": permit.origin_lease_id,
    }


def validate_source_repair_operator_terminal(
    path: str | Path, *, synthetic_fixture: bool = False
) -> dict[str, object]:
    """Validate the exact observed Operator terminal without adding claims."""

    target = Path(path).resolve()
    if synthetic_fixture:
        if target.name != "SYNTHETIC_TEST_OPERATOR_TERMINAL.json":
            raise EmpiricalContractError("synthetic Operator terminal path differs")
        expected = {
            "command": ["SYNTHETIC-TEST-OPERATOR", "run"],
            "cwd": "SYNTHETIC-TEST-CWD",
            "started_at": "2026-08-21T10:05:54.011589+00:00",
            "ended_at": "2026-08-21T10:05:58.128668+00:00",
            "exit_code": 2,
            "direct_error": "command exited with code 2",
            "output_paths": ["SYNTHETIC-TEST-RUN_IDENTITY.json"],
            "scientific_activity_predicate": "SYNTHETIC TEST activity predicate",
            "scientific_activity_started": True,
        }
    else:
        repository = Path(__file__).resolve().parents[3]
        expected_path = (repository / SOURCE_REPAIR_OPERATOR_TERMINAL_LOGICAL_PATH).resolve()
        if target != expected_path:
            raise EmpiricalContractError("production Operator terminal path differs")
        expected = {
            "command": list(SOURCE_REPAIR_OPERATOR_COMMAND),
            "cwd": str(repository),
            "started_at": "2026-08-21T07:05:54.011589-07:00",
            "ended_at": "2026-08-21T07:05:58.128668-07:00",
            "exit_code": 2,
            "direct_error": "command exited with code 2",
            "output_paths": [SOURCE_REPAIR_OPERATOR_OUTPUT_PATH],
            "scientific_activity_predicate": SOURCE_REPAIR_OPERATOR_ACTIVITY_PREDICATE,
            "scientific_activity_started": True,
        }
    if not target.is_file() or target.is_symlink():
        raise EmpiricalContractError("Operator terminal is absent or not a regular file")
    payload = target.read_bytes()
    duplicate_key = False

    def _operator_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        nonlocal duplicate_key
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                duplicate_key = True
            result[key] = item
        return result

    try:
        observed = json.loads(payload.decode("utf-8"), object_pairs_hook=_operator_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalContractError("Operator terminal is not canonical JSON") from exc
    rendered = (
        json.dumps(observed, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if (
        duplicate_key
        or not isinstance(observed, Mapping)
        or set(observed) != set(expected)
        or payload != rendered
        or dict(observed) != expected
    ):
        raise EmpiricalContractError("Operator terminal observed fields differ")
    started = _parse_aware_datetime(observed["started_at"], "Operator started_at")
    ended = _parse_aware_datetime(observed["ended_at"], "Operator ended_at")
    if ended <= started:
        raise EmpiricalContractError("Operator terminal timestamps are not increasing")
    return {
        **expected,
        "path": str(target),
        "file_sha256": hashlib.sha256(payload).hexdigest(),
        "command_sha256": document_sha256(expected["command"]),
    }


def build_source_repair_failed_terminal(
    run_identity_facts: Mapping[str, object],
    permit: RootLeasePermit,
    operator_terminal_facts: Mapping[str, object],
    *,
    synthetic_fixture: bool = False,
) -> dict[str, object]:
    """Build the immutable observed-failure terminal bound to RUN_IDENTITY."""

    if permit._seal is not _PERMIT_SEAL or permit.fixture_only is not synthetic_fixture:
        raise EmpiricalContractError("failed terminal permit is not the validated mode")
    body: dict[str, object] = {
        "schema": SOURCE_REPAIR_FAILED_TERMINAL_SCHEMA,
        "fixture_only": synthetic_fixture,
        "non_scientific": synthetic_fixture,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": "SYNTHETIC-TEST-ONLY" if synthetic_fixture else EMPIRICAL_OBJECT,
        "reason": SOURCE_REPAIR_REASON,
        "terminal": True,
        "failed_operation": "ATOMIC_TEMP_PUBLICATION",
        "scientific_values_exposed": False,
        "partial_interpretation_permitted": False,
        "resume_same_coordinates_required": True,
        "operator_terminal": dict(operator_terminal_facts),
        "run_identity_file_sha256": run_identity_facts["file_sha256"],
        "coordinate_binding_sha256": run_identity_facts["binding_sha256"],
        "master_digest": run_identity_facts["master_digest"],
        "origin_lease_id": permit.origin_lease_id,
        "stage_binding_sha256": permit.stage_binding_sha256,
    }
    return {**body, "terminal_sha256": document_sha256(body)}


def validate_source_repair_failed_terminal(
    path: str | Path,
    run_identity_facts: Mapping[str, object],
    permit: RootLeasePermit,
    *,
    synthetic_fixture: bool = False,
) -> dict[str, object]:
    result_root = Path(permit.paths["result_root"]).resolve()
    target = Path(path).resolve()
    if target != result_root / "FAILED_TERMINAL.json":
        raise EmpiricalContractError("failed terminal path differs")
    value, file_sha256 = _read_canonical_artifact(target, "failed terminal")
    operator_record = value.get("operator_terminal")
    if not isinstance(operator_record, Mapping) or not isinstance(
        operator_record.get("path"), str
    ):
        raise EmpiricalContractError("failed terminal Operator binding is malformed")
    operator_terminal = validate_source_repair_operator_terminal(
        str(operator_record["path"]), synthetic_fixture=synthetic_fixture
    )
    expected = build_source_repair_failed_terminal(
        run_identity_facts,
        permit,
        operator_terminal,
        synthetic_fixture=synthetic_fixture,
    )
    if value != expected:
        raise EmpiricalContractError("failed terminal binding differs")
    return {**value, "file_sha256": file_sha256, "path": str(target)}


def _expected_source_repair_delta(
    label: str,
    old_row: Mapping[str, object] | None,
    new_row: Mapping[str, object] | None,
) -> dict[str, object]:
    if label in SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS and old_row is None and new_row is not None:
        reason = SOURCE_REPAIR_REASON
        old_sha256 = SOURCE_ABSENT_SHA256
        new_sha256 = new_row["sha256"]
    elif label in SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS and old_row is not None and new_row is not None:
        reason = SOURCE_REPAIR_REASON
        old_sha256 = old_row["sha256"]
        new_sha256 = new_row["sha256"]
    elif label == SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH:
        if old_row is None or new_row is None:
            raise EmpiricalContractError("shared-policy repair row is absent")
        first_repair = (
            old_row.get("sha256") == SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256
            and new_row.get("sha256") == SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256
            and new_row.get("bytes") == SOURCE_REPAIR_SHARED_POLICY_NEW_BYTES
        )
        current_successor = (
            old_row.get("sha256") == SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256
            and new_row.get("sha256") == SOURCE_REPAIR_SHARED_POLICY_CURRENT_SHA256
            and new_row.get("bytes") == SOURCE_REPAIR_SHARED_POLICY_CURRENT_BYTES
        )
        if not (first_repair or current_successor):
            raise EmpiricalContractError("shared-policy repair identity differs")
        reason = (
            SOURCE_REPAIR_SHARED_POLICY_REASON if first_repair else SOURCE_REPAIR_REASON
        )
        old_sha256 = old_row["sha256"]
        new_sha256 = new_row["sha256"]
    else:
        raise EmpiricalContractError("source repair changes a protected science/runtime source")
    return {
        "logical_path": label,
        "old_sha256": old_sha256,
        "new_sha256": new_sha256,
        "reason": reason,
    }


def _validate_index1_predecessor_transition(
    value: Mapping[str, object],
    *,
    original_permit: RootLeasePermit,
    old_certificate: Mapping[str, object],
    old_binding: Mapping[str, object],
    old_request: Mapping[str, object],
    old_stage: Mapping[str, object],
    synthetic_fixture: bool,
    predecessor_original_certificate: Mapping[str, object] | None = None,
    predecessor_original_binding: Mapping[str, object] | None = None,
    predecessor_original_request: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate the exact immediately preceding index-1 or index-2 transition."""

    required = {
        "schema",
        "fixture_only",
        "non_scientific",
        "reason",
        "direction_id",
        "science_revision",
        "empirical_object",
        "origin_lease_id",
        "original",
        "repaired",
        "run_identity",
        "failed_terminal",
        "source_deltas",
        "preserved",
        "science_change",
        "coordinate_materialization_authorized",
        "partial_interpretation_permitted",
        "repair_transition_sha256",
    }
    predecessor = _exact_mapping(value, required, "index-1 predecessor transition")
    predecessor_body = {
        key: item
        for key, item in predecessor.items()
        if key != "repair_transition_sha256"
    }
    predecessor_digest = predecessor["repair_transition_sha256"]
    if (
        predecessor_digest != document_sha256(predecessor_body)
        or predecessor_digest != original_permit.repair_transition_sha256
    ):
        raise EmpiricalContractError("index-1 predecessor transition digest differs")
    if (
        predecessor["schema"] != SOURCE_REPAIR_TRANSITION_SCHEMA
        or predecessor["fixture_only"] is not synthetic_fixture
        or predecessor["non_scientific"] is not synthetic_fixture
        or predecessor["reason"] != SOURCE_REPAIR_REASON
        or predecessor["direction_id"] != DIRECTION_ID
        or predecessor["science_revision"] != SCIENCE_REVISION
        or predecessor["empirical_object"] != EMPIRICAL_OBJECT
        or predecessor["origin_lease_id"] != original_permit.origin_lease_id
        or predecessor["science_change"] is not False
        or predecessor["coordinate_materialization_authorized"] is not False
        or predecessor["partial_interpretation_permitted"] is not False
    ):
        raise EmpiricalContractError("index-1 predecessor transition authority differs")

    original = _exact_mapping(
        predecessor["original"],
        {
            "certificate_sha256",
            "binding_sha256",
            "request_sha256",
            "source_set_sha256",
            "stage_binding_sha256",
            "lease_id",
        },
        "index-1 predecessor original locator",
    )
    expected_origin_lease = original_permit.predecessor_lease_id
    lineage_original_cert: Mapping[str, object] | None = None
    lineage_original_binding: Mapping[str, object] | None = None
    lineage_original_request: Mapping[str, object] | None = None
    lineage_original_stage: Mapping[str, object] | None = None
    predecessor_original_values = (
        predecessor_original_certificate,
        predecessor_original_binding,
        predecessor_original_request,
    )
    if any(value is not None for value in predecessor_original_values):
        if any(value is None for value in predecessor_original_values):
            raise EmpiricalContractError(
                "predecessor original stage inventory is incomplete"
            )
        assert predecessor_original_certificate is not None
        assert predecessor_original_binding is not None
        assert predecessor_original_request is not None
        lineage_original_cert = validate_archived_preactivity_certificate(
            predecessor_original_certificate
        )
        lineage_original_binding = validate_archived_accepted_binding(
            predecessor_original_binding, lineage_original_cert
        )
        lineage_original_request = validate_archived_resource_request(
            predecessor_original_request, lineage_original_cert
        )
        lineage_original_stage = _stage_binding_from_validated(
            lineage_original_cert,
            lineage_original_binding,
            lineage_original_request,
        )
    elif original_permit.replacement_index == 2:
        raise EmpiricalContractError(
            "index-2 predecessor requires its exact archived original stage"
        )
    if (
        expected_origin_lease is None
        or len(original_permit.lease_lineage) < 2
        or expected_origin_lease != original_permit.lease_lineage[-2]
        or original["lease_id"] != expected_origin_lease
    ):
        raise EmpiricalContractError("index-1 predecessor original lease locator differs")
    for label in (
        "certificate_sha256",
        "binding_sha256",
        "request_sha256",
        "source_set_sha256",
        "stage_binding_sha256",
    ):
        _require_sha256(original[label], f"index-1 predecessor original {label}")
    if lineage_original_cert is not None:
        assert lineage_original_binding is not None
        assert lineage_original_request is not None
        assert lineage_original_stage is not None
        expected_original = {
            "certificate_sha256": lineage_original_cert["certificate_sha256"],
            "binding_sha256": lineage_original_binding["binding_sha256"],
            "request_sha256": document_sha256(lineage_original_request),
            "source_set_sha256": lineage_original_cert["source"]["source_set_sha256"],  # type: ignore[index]
            "stage_binding_sha256": lineage_original_stage["stage_binding_sha256"],
            "lease_id": expected_origin_lease,
        }
        if original != expected_original:
            raise EmpiricalContractError("index-2 predecessor original stage differs")

    repaired = _exact_mapping(
        predecessor["repaired"],
        {
            "certificate_sha256",
            "binding_sha256",
            "request_sha256",
            "source_set_sha256",
            "stage_binding_sha256",
        },
        "index-1 predecessor repaired locator",
    )
    expected_repaired = {
        "certificate_sha256": old_certificate["certificate_sha256"],
        "binding_sha256": old_binding["binding_sha256"],
        "request_sha256": document_sha256(old_request),
        "source_set_sha256": old_certificate["source"]["source_set_sha256"],  # type: ignore[index]
        "stage_binding_sha256": old_stage["stage_binding_sha256"],
    }
    if repaired != expected_repaired:
        raise EmpiricalContractError("index-1 predecessor repaired locator differs")

    run_record = predecessor["run_identity"]
    failed_record = predecessor["failed_terminal"]
    if not isinstance(run_record, Mapping) or not isinstance(failed_record, Mapping):
        raise EmpiricalContractError("index-1 predecessor durable records are malformed")
    for key in ("binding_sha256", "master_digest", "run_block_roots"):
        if key not in run_record:
            raise EmpiricalContractError("index-1 predecessor RUN_IDENTITY binding is incomplete")
    _require_sha256(run_record["binding_sha256"], "index-1 predecessor coordinate")
    _require_sha256(run_record["master_digest"], "index-1 predecessor master")
    run_roots = run_record["run_block_roots"]
    if not isinstance(run_roots, list):
        raise EmpiricalContractError("index-1 predecessor root inventory is malformed")

    preserved = _exact_mapping(
        predecessor["preserved"],
        {
            "coordinate_binding_sha256",
            "master_digest",
            "run_block_roots",
            "result_root",
            "resource_ceiling",
            "config_sha256",
            "native_identity_sha256",
            "analyzer_sha256",
            "counts",
        },
        "index-1 predecessor preserved bindings",
    )
    preserved_certificate = lineage_original_cert or old_certificate
    preserved_request = lineage_original_request or old_request
    expected_preserved = {
        "coordinate_binding_sha256": run_record["binding_sha256"],
        "master_digest": run_record["master_digest"],
        "run_block_roots": run_roots,
        "result_root": preserved_request["paths"]["result_root"],  # type: ignore[index]
        "resource_ceiling": preserved_request["resources"],
        "config_sha256": preserved_certificate["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": preserved_certificate["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": preserved_certificate["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "counts": preserved_certificate["counts"],
    }
    if preserved != expected_preserved:
        raise EmpiricalContractError("index-1 predecessor preserved binding differs")

    deltas = predecessor["source_deltas"]
    if not isinstance(deltas, list) or not deltas:
        raise EmpiricalContractError("index-1 predecessor source delta inventory is empty")
    labels: list[str] = []
    for row in deltas:
        delta = _exact_mapping(
            row,
            {"logical_path", "old_sha256", "new_sha256", "reason"},
            "index-1 predecessor source delta",
        )
        label = delta["logical_path"]
        if (
            not isinstance(label, str)
            or label not in PRODUCTION_SOURCE_LOGICAL_PATHS
            or label in labels
            or delta["old_sha256"] == delta["new_sha256"]
            or delta["reason"]
            not in {SOURCE_REPAIR_REASON, SOURCE_REPAIR_SHARED_POLICY_REASON}
        ):
            raise EmpiricalContractError("index-1 predecessor source delta differs")
        _require_sha256(delta["old_sha256"], "index-1 predecessor old source")
        _require_sha256(delta["new_sha256"], "index-1 predecessor new source")
        labels.append(label)
    if labels != [
        label for label in PRODUCTION_SOURCE_LOGICAL_PATHS if label in labels
    ]:
        raise EmpiricalContractError("index-1 predecessor source delta ordering differs")
    if lineage_original_cert is not None:
        prior_files = lineage_original_cert["source"]["files"]  # type: ignore[index]
        repaired_files = old_certificate["source"]["files"]  # type: ignore[index]
        expected_deltas = [
            _expected_source_repair_delta(
                label, prior_files.get(label), repaired_files.get(label)
            )
            for label in PRODUCTION_SOURCE_LOGICAL_PATHS
            if prior_files.get(label) != repaired_files.get(label)
        ]
        if list(deltas) != expected_deltas:
            raise EmpiricalContractError("predecessor source delta binding differs")
    return dict(run_record), dict(failed_record)


def build_source_repair_transition(
    *,
    original_certificate: Mapping[str, object],
    original_binding: Mapping[str, object],
    original_request: Mapping[str, object],
    original_permit: RootLeasePermit,
    repaired_certificate: Mapping[str, object],
    repaired_binding: Mapping[str, object],
    repaired_request: Mapping[str, object],
    run_identity_path: str | Path,
    failed_terminal_path: str | Path,
    source_deltas: list[Mapping[str, object]],
    synthetic_fixture: bool = False,
    predecessor_transition: Mapping[str, object] | None = None,
    predecessor_original_certificate: Mapping[str, object] | None = None,
    predecessor_original_binding: Mapping[str, object] | None = None,
    predecessor_original_request: Mapping[str, object] | None = None,
    _bootstrap_failed_terminal: Mapping[str, object] | None = None,
    _bootstrap_seal: object | None = None,
) -> dict[str, object]:
    """Build one bounded post-activity unchanged-science source transition."""

    if (
        original_permit._seal is not _PERMIT_SEAL
        or original_permit.fixture_only is not synthetic_fixture
        or original_permit.replacement_index not in (0, 1, 2)
        or len(original_permit.lease_lineage) != original_permit.replacement_index + 1
        or original_permit.lease_lineage[0] != original_permit.origin_lease_id
        or original_permit.lease_lineage[-1] != original_permit.lease_id
        or (
            original_permit.replacement_index == 0
            and (
                original_permit.origin_lease_id != original_permit.lease_id
                or original_permit.predecessor_lease_id is not None
                or original_permit.repair_transition_sha256 is not None
                or predecessor_transition is not None
            )
        )
        or (
            original_permit.replacement_index in (1, 2)
            and (
                original_permit.predecessor_lease_id
                != original_permit.lease_lineage[-2]
                or original_permit.repair_transition_sha256 is None
                or predecessor_transition is None
            )
        )
    ):
        raise EmpiricalContractError(
            "source repair requires an exact contiguous index-0, index-1, or index-2 predecessor"
        )
    old_cert = validate_archived_preactivity_certificate(original_certificate)
    old_binding = validate_archived_accepted_binding(original_binding, old_cert)
    old_request = validate_archived_resource_request(original_request, old_cert)
    old_stage = _stage_binding_from_validated(old_cert, old_binding, old_request)
    if old_stage["stage_binding_sha256"] != original_permit.stage_binding_sha256:
        raise EmpiricalContractError("original permit/stage binding differs")

    new_cert = validate_preactivity_certificate(
        repaired_certificate, validate_live_sources=not synthetic_fixture
    )
    new_binding = validate_accepted_binding(
        repaired_binding,
        new_cert,
        validate_live_sources=not synthetic_fixture,
    )
    new_request = (
        validate_archived_resource_request(repaired_request, new_cert)
        if synthetic_fixture
        else _validated_resource_request(new_cert, repaired_request)
    )
    new_stage = _stage_binding_from_validated(new_cert, new_binding, new_request)

    for key in (
        "direction_id",
        "science_revision",
        "coordinate_proposal",
        "config",
        "analyzer",
        "counts",
        "frozen_inventories",
        "activity_boundary",
    ):
        if old_cert[key] != new_cert[key]:
            raise EmpiricalContractError(f"source repair changes frozen certificate field: {key}")
    if old_cert["empirical_object"] != new_cert["empirical_object"]:
        raise EmpiricalContractError("source repair changes empirical object")
    old_native = dict(old_cert["native"])  # type: ignore[arg-type]
    new_native = dict(new_cert["native"])  # type: ignore[arg-type]
    for key in (
        "source_sha256", "artifact_sha256", "build_key", "runtime_abi",
        "toolchain", "native_identity_sha256",
    ):
        old_native.pop(key, None)
        new_native.pop(key, None)
    if old_native != new_native:
        raise EmpiricalContractError("source repair changes native ABI semantics")
    for key in (
        "counts",
        "component",
        "abi_version",
        "batch_width",
        "complete_panel_only",
        "result_blind",
        "python_fallback",
        "coordinate_materialization",
        "renewal",
    ):
        if old_request[key] != new_request[key]:
            raise EmpiricalContractError(f"source repair changes request field: {key}")
    standard_paths = {
        "result_root", "frontier_root", "run_identity_path",
        "complete_manifest_path", "technical_acceptance_path",
    }
    old_paths = old_request["paths"]
    new_paths = new_request["paths"]
    if not isinstance(old_paths, Mapping) or not isinstance(new_paths, Mapping) or any(
        old_paths.get(key) != new_paths.get(key) for key in standard_paths
    ):
        raise EmpiricalContractError("source repair changes request field: paths")
    old_resources = dict(old_request["resources"])
    new_resources = dict(new_request["resources"])
    old_process_value = old_resources.pop("process_resource", None)
    new_process_value = new_resources.pop("process_resource", None)
    resource_invariants = {
        "cpu_only": True,
        "gpu_count": 0,
        "one_thread_per_worker": True,
        "max_independent_workers": 4,
        "scratch_gib_upper": 12.0,
        "durable_artifacts_gib_upper": 1.0,
        "validity_hours": 24,
    }
    if any(
        old_resources.get(key) != expected or new_resources.get(key) != expected
        for key, expected in resource_invariants.items()
    ):
        raise EmpiricalContractError("source repair changes fixed resource ceiling")
    if new_process_value is None:
        if old_process_value is not None or old_resources != new_resources:
            raise EmpiricalContractError("source repair removes or changes process resources")
        if set(old_paths) != standard_paths or set(new_paths) != standard_paths:
            raise EmpiricalContractError("source repair legacy path inventory differs")
        new_process = None
    else:
        new_process = validate_process_resource_object(new_process_value)
        if (
            float(old_resources.get("cpu_core_hours_upper", CPU_HOURS_CEILING))
            > CPU_HOURS_CEILING
            or new_resources.get("cpu_core_hours_upper") != CPU_HOURS_CEILING
            or new_resources.get("process_group_rss_bytes_upper")
            != PROCESS_GROUP_RSS_CEILING
            or new_resources.get("checkpoint_read_bytes_upper") != CHECKPOINT_READ_CEILING
            or new_resources.get("checkpoint_write_bytes_upper") != CHECKPOINT_WRITE_CEILING
        ):
            raise EmpiricalContractError("source repair current resource ceiling differs")
        new_process_paths = new_process["paths"]
        assert isinstance(new_process_paths, Mapping)
        if set(new_paths) != standard_paths | set(new_process_paths) or any(
            new_paths.get(key) != item for key, item in new_process_paths.items()
        ):
            raise EmpiricalContractError("source repair current private-root paths differ")
    if old_process_value is not None and new_process is not None:
        if old_resources != new_resources:
            raise EmpiricalContractError("source repair changes request field: resources")
        old_process = validate_process_resource_object(old_process_value)
        for key in set(old_process) - {
            "source_set_sha256", "native_binding_sha256", "resource_sha256"
        }:
            if old_process[key] != new_process[key]:
                raise EmpiricalContractError("source repair changes process resource topology")
    elif old_process_value is None and set(old_paths) != standard_paths:
        raise EmpiricalContractError("source repair predecessor path inventory differs")
    if new_process is not None and (
        new_process["source_set_sha256"] != new_cert["source"]["source_set_sha256"]  # type: ignore[index]
        or new_process["native_binding_sha256"] != new_cert["native"]["native_identity_sha256"]  # type: ignore[index]
    ):
        raise EmpiricalContractError("source repair process resource identity differs")
    if old_process_value is not None and (
        old_process["source_set_sha256"] != old_cert["source"]["source_set_sha256"]  # type: ignore[index]
        or old_process["native_binding_sha256"] != old_cert["native"]["native_identity_sha256"]  # type: ignore[index]
    ):
        raise EmpiricalContractError("source repair predecessor process resource differs")
    old_benchmark = dict(old_request["benchmark_evidence"])  # type: ignore[arg-type]
    new_benchmark = dict(new_request["benchmark_evidence"])  # type: ignore[arg-type]
    old_benchmark.pop("source_set_sha256", None)
    new_benchmark.pop("source_set_sha256", None)
    if old_benchmark.get("logical_path") == new_benchmark.get("logical_path"):
        if old_benchmark != new_benchmark:
            raise EmpiricalContractError("source repair changes same-revision benchmark evidence")
    elif (
        old_benchmark.get("logical_path") != BENCHMARK_EVIDENCE_LOGICAL_PATH
        or new_benchmark.get("logical_path") != PRODUCTION_PROTOCOL_BENCHMARK_LOGICAL_PATH
    ):
        raise EmpiricalContractError("source repair benchmark successor is not exact")

    old_files = old_cert["source"]["files"]  # type: ignore[index]
    new_files = new_cert["source"]["files"]  # type: ignore[index]
    assert isinstance(old_files, Mapping) and isinstance(new_files, Mapping)
    actual_changed = tuple(
        label
        for label in PRODUCTION_SOURCE_LOGICAL_PATHS
        if old_files.get(label) != new_files.get(label)
    )
    if not actual_changed:
        raise EmpiricalContractError("source repair contains no source delta")
    normalized_deltas: list[dict[str, object]] = []
    for row in source_deltas:
        mapping = _exact_mapping(
            row, {"logical_path", "old_sha256", "new_sha256", "reason"}, "source delta"
        )
        label = mapping["logical_path"]
        if not isinstance(label, str) or label not in new_files:
            raise EmpiricalContractError("source delta logical path is not repair-authorized")
        old_row = old_files.get(label)
        new_row = new_files[label]
        if old_row is not None and not isinstance(old_row, Mapping):
            raise EmpiricalContractError("old source delta row is malformed")
        assert isinstance(new_row, Mapping)
        expected = _expected_source_repair_delta(label, old_row, new_row)
        if dict(mapping) != expected or expected["old_sha256"] == expected["new_sha256"]:
            raise EmpiricalContractError("source delta hash/reason differs")
        normalized_deltas.append(expected)
    if tuple(row["logical_path"] for row in normalized_deltas) != actual_changed:
        raise EmpiricalContractError("enumerated source delta is incomplete or out of order")

    if original_permit.replacement_index in (1, 2):
        assert predecessor_transition is not None
        run_record, failed_record = _validate_index1_predecessor_transition(
            predecessor_transition,
            original_permit=original_permit,
            old_certificate=old_cert,
            old_binding=old_binding,
            old_request=old_request,
            old_stage=old_stage,
            synthetic_fixture=synthetic_fixture,
            predecessor_original_certificate=predecessor_original_certificate,
            predecessor_original_binding=predecessor_original_binding,
            predecessor_original_request=predecessor_original_request,
        )
        predecessor_original = predecessor_transition["original"]
        assert isinstance(predecessor_original, Mapping)
        origin_identity_permit = RootLeasePermit(
            lease_id=original_permit.origin_lease_id,
            origin_lease_id=original_permit.origin_lease_id,
            predecessor_lease_id=None,
            replacement_index=0,
            lease_lineage=(original_permit.origin_lease_id,),
            stage_binding_sha256=str(run_record["stage_binding_sha256"]),
            accepted_binding_sha256=str(predecessor_original["binding_sha256"]),
            preactivity_certificate_sha256=str(predecessor_original["certificate_sha256"]),
            coordinate_proposal_sha256=original_permit.coordinate_proposal_sha256,
            issued_at=original_permit.issued_at,
            expires_at=original_permit.expires_at,
            paths=original_permit.paths,
            resources=original_permit.resources,
            fixture_only=synthetic_fixture,
            repair_transition_sha256=None,
            archived_only=True,
            _seal=_PERMIT_SEAL,
        )
        run_identity = validate_frozen_run_identity(
            run_identity_path,
            origin_identity_permit,
            synthetic_fixture=synthetic_fixture,
        )
        failed_value, failed_file_sha256 = _read_canonical_artifact(
            failed_terminal_path, "index-1 frozen FAILED_TERMINAL"
        )
        failed_terminal = {
            **failed_value,
            "file_sha256": failed_file_sha256,
            "path": str(Path(failed_terminal_path).resolve()),
        }
        if run_identity != run_record or failed_terminal != failed_record:
            raise EmpiricalContractError("index-1 predecessor durable artifact differs")
    else:
        run_identity = validate_frozen_run_identity(
            run_identity_path, original_permit, synthetic_fixture=synthetic_fixture
        )
    if original_permit.replacement_index == 0 and _bootstrap_failed_terminal is None:
        failed_terminal = validate_source_repair_failed_terminal(
            failed_terminal_path,
            run_identity,
            original_permit,
            synthetic_fixture=synthetic_fixture,
        )
    elif original_permit.replacement_index == 0:
        if _bootstrap_seal is not _SOURCE_REPAIR_BOOTSTRAP_SEAL:
            raise EmpiricalContractError("source repair bootstrap record is unsealed")
        target = Path(failed_terminal_path).resolve()
        if target != Path(original_permit.paths["result_root"]).resolve() / "FAILED_TERMINAL.json":
            raise EmpiricalContractError("source repair bootstrap failed terminal path differs")
        operator_record = _bootstrap_failed_terminal.get("operator_terminal")
        if not isinstance(operator_record, Mapping) or not isinstance(
            operator_record.get("path"), str
        ):
            raise EmpiricalContractError("source repair bootstrap Operator binding differs")
        operator_terminal = validate_source_repair_operator_terminal(
            str(operator_record["path"]), synthetic_fixture=synthetic_fixture
        )
        expected_document = build_source_repair_failed_terminal(
            run_identity,
            original_permit,
            operator_terminal,
            synthetic_fixture=synthetic_fixture,
        )
        expected_record = {
            **expected_document,
            "file_sha256": hashlib.sha256(canonical_json_bytes(expected_document)).hexdigest(),
            "path": str(target),
        }
        if dict(_bootstrap_failed_terminal) != expected_record:
            raise EmpiricalContractError("source repair bootstrap failed terminal differs")
        failed_terminal = expected_record
    body: dict[str, object] = {
        "schema": SOURCE_REPAIR_TRANSITION_SCHEMA,
        "fixture_only": synthetic_fixture,
        "non_scientific": synthetic_fixture,
        "reason": SOURCE_REPAIR_REASON,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "origin_lease_id": original_permit.origin_lease_id,
        "original": {
            "certificate_sha256": old_cert["certificate_sha256"],
            "binding_sha256": old_binding["binding_sha256"],
            "request_sha256": document_sha256(old_request),
            "source_set_sha256": old_cert["source"]["source_set_sha256"],  # type: ignore[index]
            "stage_binding_sha256": old_stage["stage_binding_sha256"],
            "lease_id": original_permit.lease_id,
        },
        "repaired": {
            "certificate_sha256": new_cert["certificate_sha256"],
            "binding_sha256": new_binding["binding_sha256"],
            "request_sha256": document_sha256(new_request),
            "source_set_sha256": new_cert["source"]["source_set_sha256"],  # type: ignore[index]
            "stage_binding_sha256": new_stage["stage_binding_sha256"],
        },
        "run_identity": run_identity,
        "failed_terminal": failed_terminal,
        "source_deltas": normalized_deltas,
        "preserved": {
            "coordinate_binding_sha256": run_identity["binding_sha256"],
            "master_digest": run_identity["master_digest"],
            "run_block_roots": run_identity["run_block_roots"],
            "result_root": old_request["paths"]["result_root"],  # type: ignore[index]
            "resource_ceiling": old_request["resources"],
            "config_sha256": old_cert["config"]["config_sha256"],  # type: ignore[index]
            "native_identity_sha256": old_cert["native"]["native_identity_sha256"],  # type: ignore[index]
            "analyzer_sha256": old_cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
            "counts": old_cert["counts"],
        },
        "science_change": False,
        "coordinate_materialization_authorized": False,
        "partial_interpretation_permitted": False,
    }
    return {**body, "repair_transition_sha256": document_sha256(body)}


def validate_source_repair_transition(
    value: Mapping[str, object], **build_kwargs: object
) -> dict[str, object]:
    expected = build_source_repair_transition(**build_kwargs)  # type: ignore[arg-type]
    if dict(value) != expected:
        raise EmpiricalContractError("source repair transition artifact differs")
    return expected


def _parse_aware_datetime(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise LeaseError(f"Root lease {label} is malformed")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LeaseError(f"Root lease {label} is malformed") from exc
    if parsed.tzinfo is None:
        raise LeaseError(f"Root lease {label} must be timezone-aware")
    return parsed


def _validate_archived_repair_bridge(
    transition_value: Mapping[str, object],
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    lease: Mapping[str, object],
    stage_binding_sha256: str,
    synthetic_fixture: bool,
) -> dict[str, object]:
    """Validate the self-bound bridge needed to reconstruct an expired permit.

    This is deliberately only the archived side of the bridge.  The caller must
    still pass the resulting ``archived_only`` permit through the full transition
    validator before a repaired replacement permit can be admitted.
    """

    required = {
        "schema",
        "fixture_only",
        "non_scientific",
        "reason",
        "direction_id",
        "science_revision",
        "empirical_object",
        "origin_lease_id",
        "original",
        "repaired",
        "run_identity",
        "failed_terminal",
        "source_deltas",
        "preserved",
        "science_change",
        "coordinate_materialization_authorized",
        "partial_interpretation_permitted",
        "repair_transition_sha256",
    }
    transition = _exact_mapping(
        transition_value, required, "archived source repair transition"
    )
    body = {key: transition[key] for key in required - {"repair_transition_sha256"}}
    if transition["repair_transition_sha256"] != document_sha256(body):
        raise LeaseError("archived source repair transition digest differs")
    if (
        transition["schema"] != SOURCE_REPAIR_TRANSITION_SCHEMA
        or transition["fixture_only"] is not synthetic_fixture
        or transition["non_scientific"] is not synthetic_fixture
        or transition["reason"] != SOURCE_REPAIR_REASON
        or transition["direction_id"] != DIRECTION_ID
        or transition["science_revision"] != SCIENCE_REVISION
        or transition["empirical_object"] != EMPIRICAL_OBJECT
        or transition["origin_lease_id"] != lease["origin_lease_id"]
        or transition["science_change"] is not False
        or transition["coordinate_materialization_authorized"] is not False
        or transition["partial_interpretation_permitted"] is not False
    ):
        raise LeaseError("archived source repair transition authority differs")

    original = _exact_mapping(
        transition["original"],
        {
            "certificate_sha256",
            "binding_sha256",
            "request_sha256",
            "source_set_sha256",
            "stage_binding_sha256",
            "lease_id",
        },
        "archived source repair original locator",
    )
    expected_original = {
        "certificate_sha256": certificate["certificate_sha256"],
        "binding_sha256": accepted_binding["binding_sha256"],
        "request_sha256": document_sha256(resource_request),
        "source_set_sha256": certificate["source"]["source_set_sha256"],  # type: ignore[index]
        "stage_binding_sha256": stage_binding_sha256,
        "lease_id": lease["lease_id"],
    }
    if original != expected_original:
        raise LeaseError("archived source repair original locator differs")

    repaired = _exact_mapping(
        transition["repaired"],
        {
            "certificate_sha256",
            "binding_sha256",
            "request_sha256",
            "source_set_sha256",
            "stage_binding_sha256",
        },
        "archived source repair repaired locator",
    )
    for label, value in repaired.items():
        _require_sha256(value, f"archived repaired {label}")
    if repaired["source_set_sha256"] == original["source_set_sha256"]:
        raise LeaseError("archived source repair does not change the source set")

    source = certificate["source"]
    assert isinstance(source, Mapping)
    old_files = source["files"]
    assert isinstance(old_files, Mapping)
    deltas = transition["source_deltas"]
    if not isinstance(deltas, list) or not deltas:
        raise LeaseError("archived source repair delta inventory is empty")
    normalized_labels: list[str] = []
    for row in deltas:
        delta = _exact_mapping(
            row,
            {"logical_path", "old_sha256", "new_sha256", "reason"},
            "archived source repair delta",
        )
        label = delta["logical_path"]
        if (
            not isinstance(label, str)
            or (
                label not in SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS
                and label != SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH
            )
        ):
            raise LeaseError("archived source repair delta path differs")
        old_row = old_files.get(label)
        added_source = label in SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS and old_row is None
        if old_row is not None and not isinstance(old_row, Mapping):
            raise LeaseError("archived source repair old row is malformed")
        expected_reason = (
            SOURCE_REPAIR_SHARED_POLICY_REASON
            if label == SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH
            else SOURCE_REPAIR_REASON
        )
        if (
            delta["old_sha256"]
            != (SOURCE_ABSENT_SHA256 if added_source else old_row["sha256"])
            or delta["new_sha256"] == delta["old_sha256"]
            or delta["reason"] != expected_reason
            or (
                label == SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH
                and (
                    delta["old_sha256"] != SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256
                    or delta["new_sha256"]
                    != SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256
                )
            )
        ):
            raise LeaseError("archived source repair old-source row differs")
        _require_sha256(delta["new_sha256"], "archived repaired source")
        normalized_labels.append(label)
    expected_order = [
        label for label in PRODUCTION_SOURCE_LOGICAL_PATHS if label in normalized_labels
    ]
    if normalized_labels != expected_order or len(set(normalized_labels)) != len(
        normalized_labels
    ):
        raise LeaseError("archived source repair delta ordering differs")
    return dict(transition)


def _validate_archived_repair_artifacts(
    transition: Mapping[str, object],
    *,
    permit: RootLeasePermit,
    certificate: Mapping[str, object],
    resource_request: Mapping[str, object],
    synthetic_fixture: bool,
) -> None:
    """Close the archived half of the bridge against its immutable files."""

    run_record = transition["run_identity"]
    terminal_record = transition["failed_terminal"]
    preserved = transition["preserved"]
    if not isinstance(run_record, Mapping) or not isinstance(terminal_record, Mapping):
        raise LeaseError("archived source repair artifact locators are malformed")
    run_path = run_record.get("path")
    terminal_path = terminal_record.get("path")
    if not isinstance(run_path, str) or not isinstance(terminal_path, str):
        raise LeaseError("archived source repair artifact paths are malformed")
    try:
        observed_run = validate_frozen_run_identity(
            run_path, permit, synthetic_fixture=synthetic_fixture
        )
        if observed_run != dict(run_record):
            raise LeaseError("archived source repair RUN_IDENTITY record differs")
        observed_terminal = validate_source_repair_failed_terminal(
            terminal_path,
            observed_run,
            permit,
            synthetic_fixture=synthetic_fixture,
        )
        if observed_terminal != dict(terminal_record):
            raise LeaseError("archived source repair failed-terminal record differs")
    except EmpiricalContractError as exc:
        raise LeaseError("archived source repair immutable artifact differs") from exc
    preserved_mapping = _exact_mapping(
        preserved,
        {
            "coordinate_binding_sha256",
            "master_digest",
            "run_block_roots",
            "result_root",
            "resource_ceiling",
            "config_sha256",
            "native_identity_sha256",
            "analyzer_sha256",
            "counts",
        },
        "archived source repair preserved bindings",
    )
    expected_preserved = {
        "coordinate_binding_sha256": observed_run["binding_sha256"],
        "master_digest": observed_run["master_digest"],
        "run_block_roots": observed_run["run_block_roots"],
        "result_root": resource_request["paths"]["result_root"],  # type: ignore[index]
        "resource_ceiling": resource_request["resources"],
        "config_sha256": certificate["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": certificate["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": certificate["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "counts": certificate["counts"],
    }
    if preserved_mapping != expected_preserved:
        raise LeaseError("archived source repair preserved binding differs")


def _validate_archived_initial_lease_documents(
    value: Mapping[str, object],
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    synthetic_fixture: bool = False,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    RootLeasePermit,
]:
    """Validate archived initial documents without granting live authority.

    Historical source rows are checked against their archived certificate, not
    against the repaired checkout.  This private bootstrap primitive never
    validates or grants a replacement transition.
    """

    cert = validate_archived_preactivity_certificate(certificate)
    binding = validate_archived_accepted_binding(accepted_binding, cert)
    request = validate_archived_resource_request(resource_request, cert)
    stage = _stage_binding_from_validated(cert, binding, request)
    required = {
        "schema",
        "issuer",
        "lease_id",
        "origin_lease_id",
        "predecessor_lease_id",
        "replacement_index",
        "stage_binding_sha256",
        "fixture_only",
        "activity_authorized",
        "coordinate_materialization_authorized",
        "direction_id",
        "science_revision",
        "empirical_object",
        "issued_at",
        "expires_at",
        "preactivity_certificate_sha256",
        "accepted_binding_sha256",
        "coordinate_proposal_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "component",
        "abi_version",
        "batch_width",
        "paths",
        "resources",
        "counts",
        "complete_panel_only",
        "result_blind_until_complete",
        "python_fallback",
    }
    try:
        lease = _exact_mapping(value, required, "archived initial Root lease")
    except EmpiricalContractError as exc:
        raise LeaseError("archived initial Root lease field inventory differs") from exc
    lease_id = _safe_identity(lease["lease_id"], "archived Root lease id")
    origin = _safe_identity(lease["origin_lease_id"], "archived Root origin lease id")
    if synthetic_fixture:
        if lease_id not in SYNTHETIC_TEST_IDENTITIES or origin not in SYNTHETIC_TEST_IDENTITIES:
            raise LeaseError("archived synthetic lease identity is not fixed")
    elif lease_id.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")) or origin.upper().startswith(
        ("SYNTHETIC", "TEST", "FIXTURE")
    ):
        raise LeaseError("synthetic labels cannot impersonate an archived Root lease")
    expected = {
        "schema": ROOT_LEASE_SCHEMA,
        "issuer": "SYNTHETIC-TEST-ONLY" if synthetic_fixture else "Operational Root",
        "fixture_only": synthetic_fixture,
        "activity_authorized": not synthetic_fixture,
        "coordinate_materialization_authorized": not synthetic_fixture,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "origin_lease_id": lease_id,
        "predecessor_lease_id": None,
        "replacement_index": 0,
        "stage_binding_sha256": stage["stage_binding_sha256"],
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "accepted_binding_sha256": binding["binding_sha256"],
        "coordinate_proposal_sha256": cert["coordinate_proposal"]["proposal_sha256"],  # type: ignore[index]
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "paths": request["paths"],
        "resources": request["resources"],
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "python_fallback": False,
    }
    for key, expected_value in expected.items():
        if lease.get(key) != expected_value:
            raise LeaseError(f"archived initial Root lease binding differs: {key}")
    start = _parse_aware_datetime(lease["issued_at"], "issued_at")
    end = _parse_aware_datetime(lease["expires_at"], "expires_at")
    validity_hours = request["resources"]["validity_hours"]  # type: ignore[index]
    if (
        (end - start).total_seconds() <= 0
        or (end - start).total_seconds() > float(validity_hours) * 3600
    ):
        raise LeaseError("archived initial Root lease exceeds requested validity")
    paths = lease["paths"]
    if not isinstance(paths, Mapping) or not all(
        isinstance(item, str) for item in paths.values()
    ):
        raise LeaseError("archived initial Root lease paths are malformed")
    permit = RootLeasePermit(
        lease_id=lease_id,
        origin_lease_id=origin,
        predecessor_lease_id=None,
        replacement_index=0,
        lease_lineage=(lease_id,),
        stage_binding_sha256=str(stage["stage_binding_sha256"]),
        accepted_binding_sha256=str(binding["binding_sha256"]),
        preactivity_certificate_sha256=str(cert["certificate_sha256"]),
        coordinate_proposal_sha256=str(cert["coordinate_proposal"]["proposal_sha256"]),  # type: ignore[index]
        issued_at=str(lease["issued_at"]),
        expires_at=str(lease["expires_at"]),
        paths={str(key): str(item) for key, item in paths.items()},
        resources=dict(request["resources"]),  # type: ignore[arg-type]
        fixture_only=synthetic_fixture,
        repair_transition_sha256=None,
        archived_only=True,
        _seal=_PERMIT_SEAL,
    )
    return cert, binding, request, lease, permit


def validate_archived_initial_lease_for_source_repair(
    value: Mapping[str, object],
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    repair_transition: Mapping[str, object],
    synthetic_fixture: bool = False,
) -> RootLeasePermit:
    """Reconstruct an immutable initial permit solely for repair validation.

    The returned permit is sealed but ``archived_only`` and therefore cannot
    authorize materialization, runtime, or frontier mutation.  Both immutable
    repair artifacts must already exist and match the transition.
    """

    cert, binding, request, lease, permit = _validate_archived_initial_lease_documents(
        value,
        certificate=certificate,
        accepted_binding=accepted_binding,
        resource_request=resource_request,
        synthetic_fixture=synthetic_fixture,
    )
    stage = _stage_binding_from_validated(cert, binding, request)
    try:
        transition = _validate_archived_repair_bridge(
            repair_transition,
            certificate=cert,
            accepted_binding=binding,
            resource_request=request,
            lease=lease,
            stage_binding_sha256=str(stage["stage_binding_sha256"]),
            synthetic_fixture=synthetic_fixture,
        )
    except EmpiricalContractError as exc:
        raise LeaseError("archived source repair bridge is malformed") from exc
    try:
        _validate_archived_repair_artifacts(
            transition,
            permit=permit,
            certificate=cert,
            resource_request=request,
            synthetic_fixture=synthetic_fixture,
        )
    except EmpiricalContractError as exc:
        raise LeaseError("archived source repair artifact binding is malformed") from exc
    return permit


def build_source_repair_bootstrap(
    *,
    original_certificate: Mapping[str, object],
    original_binding: Mapping[str, object],
    original_request: Mapping[str, object],
    original_lease: Mapping[str, object],
    repaired_certificate: Mapping[str, object],
    repaired_binding: Mapping[str, object],
    repaired_request: Mapping[str, object],
    run_identity_path: str | Path,
    operator_terminal_path: str | Path,
    source_deltas: list[Mapping[str, object]],
    synthetic_fixture: bool = False,
) -> dict[str, object]:
    """Prepare the two canonical repair artifacts without a circular permit.

    The function does not write either artifact.  It returns canonical document
    values and exact target/hash bindings for CM-controlled installation.  Once
    installed, ``validate_archived_initial_lease_for_source_repair`` must
    independently re-read and validate both immutable inputs.
    """

    cert, binding, request, lease, archived_permit = (
        _validate_archived_initial_lease_documents(
            original_lease,
            certificate=original_certificate,
            accepted_binding=original_binding,
            resource_request=original_request,
            synthetic_fixture=synthetic_fixture,
        )
    )
    run_identity = validate_frozen_run_identity(
        run_identity_path, archived_permit, synthetic_fixture=synthetic_fixture
    )
    operator_terminal = validate_source_repair_operator_terminal(
        operator_terminal_path, synthetic_fixture=synthetic_fixture
    )
    lease_start = _parse_aware_datetime(lease["issued_at"], "issued_at")
    lease_end = _parse_aware_datetime(lease["expires_at"], "expires_at")
    operator_start = _parse_aware_datetime(
        operator_terminal["started_at"], "Operator started_at"
    )
    operator_end = _parse_aware_datetime(
        operator_terminal["ended_at"], "Operator ended_at"
    )
    if not lease_start <= operator_start < operator_end <= lease_end:
        raise EmpiricalContractError("Operator terminal falls outside the original lease")
    failed_terminal_document = build_source_repair_failed_terminal(
        run_identity,
        archived_permit,
        operator_terminal,
        synthetic_fixture=synthetic_fixture,
    )
    failed_terminal_path = (
        Path(str(request["paths"]["result_root"])).resolve() / "FAILED_TERMINAL.json"  # type: ignore[index]
    )
    if failed_terminal_path.exists():
        raise EmpiricalContractError(
            "source repair bootstrap refuses an existing FAILED_TERMINAL artifact"
        )
    failed_terminal_bytes = canonical_json_bytes(failed_terminal_document)
    failed_terminal_record = {
        **failed_terminal_document,
        "file_sha256": hashlib.sha256(failed_terminal_bytes).hexdigest(),
        "path": str(failed_terminal_path),
    }
    transition = build_source_repair_transition(
        original_certificate=cert,
        original_binding=binding,
        original_request=request,
        original_permit=archived_permit,
        repaired_certificate=repaired_certificate,
        repaired_binding=repaired_binding,
        repaired_request=repaired_request,
        run_identity_path=run_identity_path,
        failed_terminal_path=failed_terminal_path,
        source_deltas=source_deltas,
        synthetic_fixture=synthetic_fixture,
        _bootstrap_failed_terminal=failed_terminal_record,
        _bootstrap_seal=_SOURCE_REPAIR_BOOTSTRAP_SEAL,
    )
    body: dict[str, object] = {
        "schema": SOURCE_REPAIR_BOOTSTRAP_SCHEMA,
        "fixture_only": synthetic_fixture,
        "non_scientific": synthetic_fixture,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "reason": SOURCE_REPAIR_REASON,
        "original_lease_id": archived_permit.lease_id,
        "archived_permit_authoritative": False,
        "activity_authorized": False,
        "coordinate_materialization_authorized": False,
        "failed_terminal_path": str(failed_terminal_path),
        "failed_terminal_file_sha256": failed_terminal_record["file_sha256"],
        "failed_terminal_document": failed_terminal_document,
        "repair_transition_document": transition,
        "operator_terminal_file_sha256": operator_terminal["file_sha256"],
    }
    return {**body, "bootstrap_sha256": document_sha256(body)}


def validate_root_lease(
    value: Mapping[str, object],
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    now: datetime,
    predecessor_permit: RootLeasePermit | None = None,
    synthetic_fixture: bool = False,
) -> RootLeasePermit:
    """Admit only the exact future Root-issued, certificate-bound lease."""

    cert = validate_preactivity_certificate(certificate)
    binding = validate_accepted_binding(accepted_binding, cert)
    request = _validated_resource_request(cert, resource_request)
    stage_binding = stage_binding_identity(
        certificate=cert,
        accepted_binding=binding,
        resource_request=request,
    )
    required = {
        "schema",
        "issuer",
        "lease_id",
        "origin_lease_id",
        "predecessor_lease_id",
        "replacement_index",
        "stage_binding_sha256",
        "fixture_only",
        "activity_authorized",
        "coordinate_materialization_authorized",
        "direction_id",
        "science_revision",
        "empirical_object",
        "issued_at",
        "expires_at",
        "preactivity_certificate_sha256",
        "accepted_binding_sha256",
        "coordinate_proposal_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "component",
        "abi_version",
        "batch_width",
        "paths",
        "resources",
        "counts",
        "complete_panel_only",
        "result_blind_until_complete",
        "python_fallback",
    }
    try:
        lease = _exact_mapping(value, required, "Root lease")
    except EmpiricalContractError as exc:
        raise LeaseError("Root lease field inventory differs") from exc
    lease_id = _safe_identity(lease["lease_id"], "Root lease id")
    if synthetic_fixture:
        if lease_id not in SYNTHETIC_TEST_IDENTITIES:
            raise LeaseError("synthetic lease fixture identity is not fixed")
    elif lease_id.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")):
        raise LeaseError("synthetic/test labels cannot impersonate a Root lease")
    origin_lease_id = _safe_identity(lease["origin_lease_id"], "Root origin lease id")
    if synthetic_fixture:
        if origin_lease_id not in SYNTHETIC_TEST_IDENTITIES:
            raise LeaseError("synthetic origin fixture identity is not fixed")
    elif origin_lease_id.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")):
        raise LeaseError("synthetic/test labels cannot impersonate a Root lease origin")
    predecessor_lease_id = lease["predecessor_lease_id"]
    if predecessor_lease_id is not None:
        predecessor_lease_id = _safe_identity(
            predecessor_lease_id, "Root predecessor lease id"
        )
        if synthetic_fixture:
            if predecessor_lease_id not in SYNTHETIC_TEST_IDENTITIES:
                raise LeaseError("synthetic predecessor fixture identity is not fixed")
        elif predecessor_lease_id.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")):
            raise LeaseError("synthetic/test labels cannot impersonate a predecessor lease")
    replacement_index = lease["replacement_index"]
    if (
        isinstance(replacement_index, bool)
        or not isinstance(replacement_index, int)
        or replacement_index < 0
    ):
        raise LeaseError("Root lease replacement index is malformed")
    if replacement_index > MAX_SOURCE_REPAIR_REPLACEMENT_INDEX:
        if (
            predecessor_permit is not None
            and predecessor_permit.repair_transition_sha256 is not None
        ):
            raise LeaseError("repair lineage cannot bypass the exact index-3 cap")
        raise LeaseError("Root lease replacement index exceeds the exact index-3 cap")
    stage_binding_sha256 = _require_sha256(
        lease["stage_binding_sha256"], "Root stage binding"
    )
    expected = {
        "schema": ROOT_LEASE_SCHEMA,
        "issuer": "SYNTHETIC-TEST-ONLY" if synthetic_fixture else "Operational Root",
        "fixture_only": synthetic_fixture,
        "activity_authorized": not synthetic_fixture,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "accepted_binding_sha256": binding["binding_sha256"],
        "coordinate_proposal_sha256": cert["coordinate_proposal"]["proposal_sha256"],  # type: ignore[index]
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "paths": request["paths"],
        "resources": request["resources"],
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "python_fallback": False,
        "stage_binding_sha256": stage_binding["stage_binding_sha256"],
    }
    for key, expected_value in expected.items():
        if lease.get(key) != expected_value:
            raise LeaseError(f"Root lease binding differs: {key}")
    start = _parse_aware_datetime(lease["issued_at"], "issued_at")
    end = _parse_aware_datetime(lease["expires_at"], "expires_at")
    if now.tzinfo is None or not start <= now < end:
        raise LeaseError("Root lease is inactive")
    validity_hours = request["resources"]["validity_hours"]  # type: ignore[index]
    if (end - start).total_seconds() <= 0 or (end - start).total_seconds() > float(validity_hours) * 3600:
        raise LeaseError("Root lease exceeds requested validity")
    if predecessor_permit is None:
        if (
            replacement_index != 0
            or origin_lease_id != lease_id
            or predecessor_lease_id is not None
        ):
            raise LeaseError("initial lease lineage differs")
        if lease["coordinate_materialization_authorized"] is not (not synthetic_fixture):
            raise LeaseError("initial lease must authorize one coordinate materialization")
        lease_lineage = (lease_id,)
    else:
        if predecessor_permit._seal is not _PERMIT_SEAL:
            raise LeaseError("replacement predecessor permit is unvalidated")
        if predecessor_permit.fixture_only is not synthetic_fixture:
            raise LeaseError("replacement predecessor fixture/production mode differs")
        if (
            replacement_index != predecessor_permit.replacement_index + 1
            or predecessor_lease_id != predecessor_permit.lease_id
            or origin_lease_id != predecessor_permit.origin_lease_id
        ):
            raise LeaseError("replacement lease has a lineage gap")
        if (
            len(predecessor_permit.lease_lineage)
            != predecessor_permit.replacement_index + 1
            or predecessor_permit.lease_lineage[0]
            != predecessor_permit.origin_lease_id
            or predecessor_permit.lease_lineage[-1]
            != predecessor_permit.lease_id
        ):
            raise LeaseError("replacement predecessor lineage is internally inconsistent")
        if lease_id in predecessor_permit.lease_lineage:
            raise LeaseError("replacement lease id is not fresh")
        if (
            stage_binding_sha256 != predecessor_permit.stage_binding_sha256
            or str(binding["binding_sha256"])
            != predecessor_permit.accepted_binding_sha256
            or str(cert["certificate_sha256"])
            != predecessor_permit.preactivity_certificate_sha256
            or str(cert["coordinate_proposal"]["proposal_sha256"])  # type: ignore[index]
            != predecessor_permit.coordinate_proposal_sha256
            or dict(request["paths"]) != dict(predecessor_permit.paths)  # type: ignore[arg-type]
            or dict(request["resources"]) != dict(predecessor_permit.resources)  # type: ignore[arg-type]
        ):
            raise LeaseError("replacement lease drifts from immutable stage binding")
        predecessor_end = _parse_aware_datetime(
            predecessor_permit.expires_at, "predecessor expires_at"
        )
        if start != predecessor_end:
            raise LeaseError("replacement window has a gap or overlap")
        if lease["coordinate_materialization_authorized"] is not False:
            raise LeaseError("replacement lease cannot rematerialize coordinates")
        lease_lineage = (*predecessor_permit.lease_lineage, lease_id)
    paths = lease["paths"]
    if not isinstance(paths, Mapping) or not all(isinstance(item, str) for item in paths.values()):
        raise LeaseError("Root lease paths are malformed")
    return RootLeasePermit(
        lease_id=lease_id,
        origin_lease_id=origin_lease_id,
        predecessor_lease_id=predecessor_lease_id,
        replacement_index=replacement_index,
        lease_lineage=lease_lineage,
        stage_binding_sha256=stage_binding_sha256,
        accepted_binding_sha256=str(binding["binding_sha256"]),
        preactivity_certificate_sha256=str(cert["certificate_sha256"]),
        coordinate_proposal_sha256=str(cert["coordinate_proposal"]["proposal_sha256"]),  # type: ignore[index]
        issued_at=str(lease["issued_at"]),
        expires_at=str(lease["expires_at"]),
        paths={str(key): str(item) for key, item in paths.items()},
        resources=dict(request["resources"]),  # type: ignore[arg-type]
        fixture_only=synthetic_fixture,
        repair_transition_sha256=None,
        _seal=_PERMIT_SEAL,
    )


def _validate_source_repair_replacement_lease(
    value: Mapping[str, object],
    *,
    repair_transition: Mapping[str, object],
    original_permit: RootLeasePermit,
    repaired_certificate: Mapping[str, object],
    repaired_binding: Mapping[str, object],
    repaired_request: Mapping[str, object],
    now: datetime,
    synthetic_fixture: bool = False,
    archived_stage: bool = False,
) -> RootLeasePermit:
    """Validate one exact contiguous source-repair lease, capped at index 3."""

    if (
        original_permit._seal is not _PERMIT_SEAL
        or original_permit.fixture_only is not synthetic_fixture
        or original_permit.replacement_index not in (0, 1, 2)
        or len(original_permit.lease_lineage) != original_permit.replacement_index + 1
        or original_permit.lease_lineage[0] != original_permit.origin_lease_id
        or original_permit.lease_lineage[-1] != original_permit.lease_id
        or (
            original_permit.replacement_index == 0
            and (
                original_permit.origin_lease_id != original_permit.lease_id
                or original_permit.repair_transition_sha256 is not None
            )
        )
        or (
            original_permit.replacement_index in (1, 2)
            and original_permit.repair_transition_sha256 is None
        )
    ):
        raise LeaseError("source repair predecessor lineage is not exact")
    if original_permit.replacement_index + 1 > MAX_SOURCE_REPAIR_REPLACEMENT_INDEX:
        raise LeaseError("source repair replacement index exceeds the exact index-3 cap")
    transition = dict(repair_transition)
    if set(transition) != {
        "schema",
        "fixture_only",
        "non_scientific",
        "reason",
        "direction_id",
        "science_revision",
        "empirical_object",
        "origin_lease_id",
        "original",
        "repaired",
        "run_identity",
        "failed_terminal",
        "source_deltas",
        "preserved",
        "science_change",
        "coordinate_materialization_authorized",
        "partial_interpretation_permitted",
        "repair_transition_sha256",
    }:
        raise LeaseError("source repair transition inventory differs")
    transition_body = {
        key: item for key, item in transition.items() if key != "repair_transition_sha256"
    }
    if transition["repair_transition_sha256"] != document_sha256(transition_body):
        raise LeaseError("source repair transition digest differs")
    if (
        transition["schema"] != SOURCE_REPAIR_TRANSITION_SCHEMA
        or transition["fixture_only"] is not synthetic_fixture
        or transition["non_scientific"] is not synthetic_fixture
        or transition["reason"] != SOURCE_REPAIR_REASON
        or transition["direction_id"] != DIRECTION_ID
        or transition["science_revision"] != SCIENCE_REVISION
        or transition["empirical_object"] != EMPIRICAL_OBJECT
        or transition["origin_lease_id"] != original_permit.origin_lease_id
        or transition["science_change"] is not False
        or transition["coordinate_materialization_authorized"] is not False
        or transition["partial_interpretation_permitted"] is not False
    ):
        raise LeaseError("source repair transition authority boundary differs")
    original = transition["original"]
    repaired = transition["repaired"]
    if not isinstance(original, Mapping) or not isinstance(repaired, Mapping):
        raise LeaseError("source repair stage locators are malformed")
    if (
        original.get("lease_id") != original_permit.lease_id
        or original.get("stage_binding_sha256") != original_permit.stage_binding_sha256
    ):
        raise LeaseError("source repair transition predecessor binding differs")

    if archived_stage:
        cert = validate_archived_preactivity_certificate(repaired_certificate)
        binding = validate_archived_accepted_binding(repaired_binding, cert)
        request = validate_archived_resource_request(repaired_request, cert)
    else:
        cert = validate_preactivity_certificate(
            repaired_certificate, validate_live_sources=not synthetic_fixture
        )
        binding = validate_accepted_binding(
            repaired_binding,
            cert,
            validate_live_sources=not synthetic_fixture,
        )
        request = (
            validate_archived_resource_request(repaired_request, cert)
            if synthetic_fixture
            else _validated_resource_request(cert, repaired_request)
        )
    stage = _stage_binding_from_validated(cert, binding, request)
    if (
        repaired.get("certificate_sha256") != cert["certificate_sha256"]
        or repaired.get("binding_sha256") != binding["binding_sha256"]
        or repaired.get("request_sha256") != document_sha256(request)
        or repaired.get("source_set_sha256") != cert["source"]["source_set_sha256"]  # type: ignore[index]
        or repaired.get("stage_binding_sha256") != stage["stage_binding_sha256"]
    ):
        raise LeaseError("source repair transition repaired-stage binding differs")

    required = {
        "schema",
        "issuer",
        "fixture_only",
        "lease_id",
        "origin_lease_id",
        "predecessor_lease_id",
        "replacement_index",
        "stage_binding_sha256",
        "repair_transition_sha256",
        "activity_authorized",
        "coordinate_materialization_authorized",
        "direction_id",
        "science_revision",
        "empirical_object",
        "issued_at",
        "expires_at",
        "preactivity_certificate_sha256",
        "accepted_binding_sha256",
        "coordinate_proposal_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "component",
        "abi_version",
        "batch_width",
        "paths",
        "resources",
        "counts",
        "complete_panel_only",
        "result_blind_until_complete",
        "python_fallback",
    }
    lease = _exact_mapping(value, required, "source repair replacement lease")
    lease_id = _safe_identity(lease["lease_id"], "source repair lease id")
    if synthetic_fixture:
        if lease_id not in SYNTHETIC_TEST_IDENTITIES:
            raise LeaseError("source repair synthetic lease identity is not fixed")
    elif lease_id.upper().startswith(("SYNTHETIC", "TEST", "FIXTURE")):
        raise LeaseError("synthetic/test source repair lease cannot impersonate production")
    expected = {
        "schema": SOURCE_REPAIR_LEASE_SCHEMA,
        "issuer": "SYNTHETIC-TEST-ONLY" if synthetic_fixture else "Operational Root",
        "fixture_only": synthetic_fixture,
        "origin_lease_id": original_permit.origin_lease_id,
        "predecessor_lease_id": original_permit.lease_id,
        "replacement_index": original_permit.replacement_index + 1,
        "stage_binding_sha256": stage["stage_binding_sha256"],
        "repair_transition_sha256": transition["repair_transition_sha256"],
        "activity_authorized": not synthetic_fixture,
        "coordinate_materialization_authorized": False,
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "accepted_binding_sha256": binding["binding_sha256"],
        "coordinate_proposal_sha256": cert["coordinate_proposal"]["proposal_sha256"],  # type: ignore[index]
        "source_set_sha256": cert["source"]["source_set_sha256"],  # type: ignore[index]
        "config_sha256": cert["config"]["config_sha256"],  # type: ignore[index]
        "native_identity_sha256": cert["native"]["native_identity_sha256"],  # type: ignore[index]
        "analyzer_sha256": cert["analyzer"]["analyzer_sha256"],  # type: ignore[index]
        "component": SHARED_COMPONENT,
        "abi_version": NATIVE_ABI_VERSION,
        "batch_width": SELECTED_BATCH_WIDTH,
        "paths": request["paths"],
        "resources": request["resources"],
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "python_fallback": False,
    }
    for key, expected_value in expected.items():
        if lease.get(key) != expected_value:
            raise LeaseError(f"source repair replacement lease differs: {key}")
    start = _parse_aware_datetime(lease["issued_at"], "issued_at")
    end = _parse_aware_datetime(lease["expires_at"], "expires_at")
    predecessor_end = _parse_aware_datetime(
        original_permit.expires_at, "predecessor expires_at"
    )
    if start != predecessor_end:
        raise LeaseError("source repair replacement window has a gap or overlap")
    if now.tzinfo is None or not start <= now < end:
        raise LeaseError("source repair replacement lease is inactive")
    if (
        (end - start).total_seconds() <= 0
        or (end - start).total_seconds()
        > float(request["resources"]["validity_hours"]) * 3600  # type: ignore[index]
    ):
        raise LeaseError("source repair replacement validity differs")
    return RootLeasePermit(
        lease_id=lease_id,
        origin_lease_id=original_permit.origin_lease_id,
        predecessor_lease_id=original_permit.lease_id,
        replacement_index=original_permit.replacement_index + 1,
        lease_lineage=(*original_permit.lease_lineage, lease_id),
        stage_binding_sha256=str(stage["stage_binding_sha256"]),
        accepted_binding_sha256=str(binding["binding_sha256"]),
        preactivity_certificate_sha256=str(cert["certificate_sha256"]),
        coordinate_proposal_sha256=str(cert["coordinate_proposal"]["proposal_sha256"]),  # type: ignore[index]
        issued_at=str(lease["issued_at"]),
        expires_at=str(lease["expires_at"]),
        paths={str(key): str(item) for key, item in request["paths"].items()},  # type: ignore[union-attr]
        resources=dict(request["resources"]),  # type: ignore[arg-type]
        fixture_only=synthetic_fixture,
        repair_transition_sha256=str(transition["repair_transition_sha256"]),
        archived_only=archived_stage,
        _seal=_PERMIT_SEAL,
    )


def validate_source_repair_replacement_lease(
    value: Mapping[str, object],
    *,
    repair_transition: Mapping[str, object],
    original_permit: RootLeasePermit,
    repaired_certificate: Mapping[str, object],
    repaired_binding: Mapping[str, object],
    repaired_request: Mapping[str, object],
    now: datetime,
    synthetic_fixture: bool = False,
) -> RootLeasePermit:
    """Validate one active exact contiguous source-repair lease."""

    return _validate_source_repair_replacement_lease(
        value,
        repair_transition=repair_transition,
        original_permit=original_permit,
        repaired_certificate=repaired_certificate,
        repaired_binding=repaired_binding,
        repaired_request=repaired_request,
        now=now,
        synthetic_fixture=synthetic_fixture,
        archived_stage=False,
    )


def validate_archived_source_repair_replacement_lease(
    value: Mapping[str, object],
    *,
    repair_transition: Mapping[str, object],
    original_permit: RootLeasePermit,
    repaired_certificate: Mapping[str, object],
    repaired_binding: Mapping[str, object],
    repaired_request: Mapping[str, object],
    synthetic_fixture: bool = False,
) -> RootLeasePermit:
    """Reconstruct a validated replacement lease without runtime authority."""

    try:
        issued_at = value["issued_at"]
    except (KeyError, TypeError) as exc:
        raise LeaseError("archived source repair lease issued_at is absent") from exc
    permit = _validate_source_repair_replacement_lease(
        value,
        repair_transition=repair_transition,
        original_permit=original_permit,
        repaired_certificate=repaired_certificate,
        repaired_binding=repaired_binding,
        repaired_request=repaired_request,
        now=_parse_aware_datetime(issued_at, "issued_at"),
        synthetic_fixture=synthetic_fixture,
        archived_stage=True,
    )
    return permit


def _derive_block_digest(key: bytes, identity: str, block_index: int) -> str:
    message = canonical_json_bytes(
        {
            "domain": "RCLE-TBCFV-R04/run-block-root/v1",
            "identity": identity,
            "block_index": block_index,
        }
    )
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def materialize_coordinates(
    identity: str,
    *,
    master_material: bytes | None = None,
    permit: RootLeasePermit | None = None,
    accepted_binding: Mapping[str, object] | None = None,
    certificate: Mapping[str, object] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Materialize synthetic TEST roots or a future fully authorized binding.

    Production materialization requires all four external authority objects:
    a sealed active permit, the exact CM accepted binding, its certificate, and
    caller-supplied 256-bit master material.  This function never generates a
    master and never emits numeric seeds.
    """

    _safe_identity(identity, "coordinate identity")
    if identity in SYNTHETIC_TEST_IDENTITIES:
        if any(value is not None for value in (master_material, permit, accepted_binding, certificate, now)):
            raise EmpiricalContractError("synthetic TEST materialization accepts no authority or master inputs")
        key = _SYNTHETIC_TEST_KEYS[identity]
        block_count = 2
        fixture_only = True
        non_scientific = True
        authority = "FIXED_SYNTHETIC_TEST_IDENTITY"
        master_digest = hashlib.sha256(key).hexdigest()
    else:
        if permit is None or accepted_binding is None or certificate is None or now is None:
            raise LeaseError("production materialization requires Root lease and CM accepted binding")
        if permit.fixture_only:
            raise LeaseError("synthetic lease fixture cannot authorize production materialization")
        permit.require_active(now=now)
        if permit.replacement_index != 0:
            raise LeaseError("replacement lease cannot rematerialize coordinates")
        binding = validate_accepted_binding(accepted_binding, certificate)
        if permit.accepted_binding_sha256 != binding["binding_sha256"]:
            raise LeaseError("permit and CM accepted binding differ")
        if not isinstance(master_material, bytes) or len(master_material) != 32:
            raise LeaseError("production master material must be caller-supplied 256 bits")
        key = master_material
        block_count = BLOCK_COUNT
        fixture_only = False
        non_scientific = False
        authority = permit.origin_lease_id
        master_digest = hashlib.sha256(key).hexdigest()
    body: dict[str, object] = {
        "schema": MATERIALIZED_BINDING_SCHEMA,
        "identity": identity,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT if not fixture_only else "SYNTHETIC-TEST-ONLY",
        "fixture_only": fixture_only,
        "non_scientific": non_scientific,
        "authority": authority,
        "stage_binding_sha256": (
            permit.stage_binding_sha256
            if not fixture_only and permit is not None
            else document_sha256(
                {
                    "fixture_only": True,
                    "identity": identity,
                    "stage": "SYNTHETIC-TEST-ONLY",
                }
            )
        ),
        "numeric_seed_present": False,
        "master_material_exposed": False,
        "master_digest": master_digest,
        "run_block_count": block_count,
        "run_block_roots": [
            {"block_index": index, "root_digest": _derive_block_digest(key, identity, index)}
            for index in range(block_count)
        ],
    }
    return {**body, "binding_sha256": document_sha256(body)}


def _verify_frozen_arithmetic() -> None:
    if BLOCK_COUNT != 20 or len(LEARNED_PACKAGES) != 5 or len(SCRIPTED_PACKAGES) != 3:
        raise RuntimeError("RCLE-TBCFV frozen inventory drift")
    if len(TRAINING_CELLS) != 8 or len(HELDOUT_CELLS) != 8:
        raise RuntimeError("RCLE-TBCFV frozen cell inventory drift")
    if len(PREREQUISITE_VARIABLES) != 44 or len(DIRECT_VALUE_VARIABLES) != 4 or len(MECHANISM_VARIABLES) != 10:
        raise RuntimeError("RCLE-TBCFV analyzer variable inventory drift")
    if TAIL_COUNT != 72 or len(BRANCHES) != 12 or not math.isclose(GAMMA_GLOBAL, 1.0 - 0.05 / 72):
        raise RuntimeError("RCLE-TBCFV analyzer family drift")
    if PANEL_COUNTS["training_episodes"] != 5 * 20 * 800 * 64:
        raise RuntimeError("RCLE-TBCFV training count drift")
    if PANEL_COUNTS["learned_heldout_episodes"] != 5 * 20 * 8 * 2_048:
        raise RuntimeError("RCLE-TBCFV learned evaluation count drift")
    if PANEL_COUNTS["scripted_heldout_episodes"] != 3 * 20 * 8 * 2_048:
        raise RuntimeError("RCLE-TBCFV scripted evaluation count drift")


_verify_frozen_arithmetic()


__all__ = [
    "ACCEPTED_NATIVE_ARTIFACT_SHA256",
    "ACCEPTED_NATIVE_BUILD_KEY",
    "ACCEPTED_NATIVE_SOURCE_SHA256",
    "BENCHMARK_EVIDENCE_LOGICAL_PATH",
    "CM_OWNER",
    "CM_ACCEPTED_BINDING_SCHEMA",
    "COORDINATE_PROPOSAL_SCHEMA",
    "EMPIRICAL_OBJECT",
    "EmpiricalContractError",
    "LeaseError",
    "MATERIALIZED_BINDING_SCHEMA",
    "MAX_SOURCE_REPAIR_REPLACEMENT_INDEX",
    "PANEL_COUNTS",
    "PREACTIVITY_SCHEMA",
    "PRODUCTION_SOURCE_LOGICAL_PATHS",
    "RESOURCE_REQUEST_SCHEMA",
    "ROOT_LEASE_SCHEMA",
    "SOURCE_REPAIR_ALLOWED_LOGICAL_PATHS",
    "SOURCE_REPAIR_BOOTSTRAP_SCHEMA",
    "SOURCE_REPAIR_FAILED_TERMINAL_SCHEMA",
    "SOURCE_REPAIR_LEASE_SCHEMA",
    "SOURCE_REPAIR_REASON",
    "SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH",
    "SOURCE_REPAIR_SHARED_POLICY_NEW_BYTES",
    "SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256",
    "SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256",
    "SOURCE_REPAIR_SHARED_POLICY_REASON",
    "SOURCE_REPAIR_OPERATOR_ACTIVITY_PREDICATE",
    "SOURCE_REPAIR_OPERATOR_COMMAND",
    "SOURCE_REPAIR_OPERATOR_OUTPUT_PATH",
    "SOURCE_REPAIR_OPERATOR_TERMINAL_LOGICAL_PATH",
    "SOURCE_REPAIR_TRANSITION_SCHEMA",
    "RootLeasePermit",
    "SELECTED_BATCH_WIDTH",
    "SHARED_COMPONENT",
    "SYNTHETIC_TEST_IDENTITIES",
    "TEST_PREACTIVITY_SCHEMA",
    "analyzer_identity",
    "build_preactivity_certificate",
    "build_source_repair_bootstrap",
    "build_source_repair_failed_terminal",
    "build_source_repair_transition",
    "build_test_preactivity_certificate",
    "canonical_json_bytes",
    "canonical_source_identity",
    "coordinate_proposal",
    "document_sha256",
    "frozen_config_identity",
    "materialize_coordinates",
    "native_identity_from_observation",
    "production_source_paths",
    "resource_request_proposal",
    "stage_binding_identity",
    "validate_accepted_binding",
    "validate_archived_accepted_binding",
    "validate_archived_initial_lease_for_source_repair",
    "validate_archived_preactivity_certificate",
    "validate_archived_resource_request",
    "validate_archived_source_repair_replacement_lease",
    "validate_benchmark_evidence_payload",
    "validate_coordinate_proposal",
    "validate_native_identity",
    "validate_preactivity_certificate",
    "validate_frozen_run_identity",
    "validate_root_lease",
    "validate_source_repair_failed_terminal",
    "validate_source_repair_operator_terminal",
    "validate_source_repair_replacement_lease",
    "validate_source_repair_transition",
    "validate_source_identity",
]
