"""UAV G0 proof-readiness and fail-closed result-bearing runner.

The six readiness entries remain proof-only.  The result-bearing entries
implement the frozen V2 train/evaluate/analyze artifact contract, but cannot
admit a root until a post-acceptance implementation identity and independent
alignment-stage identity are explicitly bound below.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, fields
import hashlib
import importlib.metadata
import json
import math
import multiprocessing
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence

_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_env_name in _THREAD_ENV_NAMES:
    os.environ[_thread_env_name] = "1"
os.environ["OMP_DYNAMIC"] = "FALSE"
os.environ["MKL_DYNAMIC"] = "FALSE"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from ha_ctse_process import uav_g0_geometry as geometry
from ha_ctse_process import uav_g0_statistics as statistics
from ha_ctse_process import uav_source_identifiability_g0 as source
from ha_ctse_process import uav_episode_serialization as episode_serialization


SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = geometry.ALGORITHM_ID
SOURCE_ID = geometry.SOURCE_ID
FORMAL_EXECUTION_AUTHORIZED = source.FORMAL_EXECUTION_AUTHORIZED
DESIGN_DISPOSITION = source.DESIGN_DISPOSITION
ORACLE_SAFETY_DISPOSITION = source.ORACLE_SAFETY_DISPOSITION
REPLAY_DISPOSITION = source.REPLAY_DISPOSITION
RETURN_READY_STEP_DISPOSITION = source.RETURN_READY_STEP_DISPOSITION
CLAIM_SCOPE = "SOURCE_IDENTIFIABILITY_G0_ONLY"
FORMAL_INTERFACE_CONTRACT_ID = "UAV_SOURCE_IDENTIFIABILITY_G0_FORMAL_INTERFACE_V2"
FORMAL_INTERFACE_CONTRACT_VERSION = 2
FORMAL_INTERFACE_SOURCE_COMMIT = "83bad9ebf489d24cb67ad30e10905cb0eb84f04a"
ACCEPTED_G0_SOURCE_COMMIT = "9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43"
FROZEN_V2_SCIENTIFIC_SOURCE_BLOB_SHA = "0bfaca5c0e2be428c6c9a15cd41c83f4bf7d1f5a"
FORMAL_AUTHORIZATION_TOKEN = "G0_FORMAL_ADMISSION=PROCEED"
FAILED_ROOT_SCHEMA_ID = "UAV_G0_FAILED_ROOT"
FAILED_ROOT_SCHEMA_VERSION = 1

# Bound only after CODE_ACCEPTED and the independent c88f43d correction-only
# code-science audit.
# The historical accepted provenance above remains distinct from this active
# aligned implementation identity.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = (
    "c88f43de6451c40defefd7c679ba8d353c45735c"
)
ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA: str | None = (
    "b0baab9c47c2537217b689699d0520f158355e3d"
)
ALIGNMENT_STAGE_COMMIT: str | None = (
    "499fcaac7acea4faf58268b71773459ef73bedec"
)
ALIGNMENT_DISPOSITION: str | None = "ALIGNED"

FROZEN_CONTRACT_PATH = PROJECT_ROOT / (
    "docs/external-review/rounds/"
    "20260730_uav_source_identifiability_g0_formal_interface_contract_"
    "clarification_v2/21_PRO_OPEN_RAW.md"
)
FROZEN_CONTRACT_GIT_BLOB_SHA = "c5280bb3ea8d67681ae8068d861155e940eed698"
RECONSTRUCTION_CLARIFICATION_PATH = PROJECT_ROOT / (
    "docs/external-review/rounds/"
    "20260731_uav_source_identifiability_g0_formal_interface_reconstruction_"
    "carrier_clarification/21_PRO_OPEN_RAW.md"
)
RECONSTRUCTION_CLARIFICATION_GIT_BLOB_SHA = (
    "e38596847018b6a2a13aad437c5b96f090ae41c0"
)
RECONSTRUCTION_CLARIFICATION_STAGE_COMMIT = (
    "d77710ec87e06d345cc1cdfc94d77645d8673de8"
)
RECONSTRUCTION_CLARIFICATION_RECORDS = {
    "G0_FORMAL_INTERFACE_CLARIFICATION": "SOURCE_RECONSTRUCTION_ALLOWED",
    "G0_ORACLE_REPLAY_CERTIFICATE_RULE": "SEPARATE_CERTIFICATE_COMPARISON_ALLOWED",
    "G0_RUNTIME_CARRIER_RULE": "EXPLICIT_WRAPPER_FIELDS_REQUIRED",
    "G0_FORMAL_INTERFACE_NEXT_ACTION": "NEW_SOURCE_CANDIDATE_AND_ALIGNMENT",
}
BOOTSTRAP_GENERATOR = "numpy.Generator(PCG64(2026072901))"
GEOMETRY_SUPPORT_RULE = "analytic_complete_support_for_every_phi_in_[0,2*pi)"
ORACLE_RANKING_ARITHMETIC = {
    "violation_count": (
        "candidate_steps_with_hard_physical_or_safety_violation_or_"
        "real_guard_safety_deviation"
    ),
    "gate_arrival_step": (
        "min_pre_action_t_latest_departure_le_t_le_O_bitwise_equal_gate_"
        "else_H_plus_1"
    ),
    "event_tracking_error": (
        "sum_t_O_to_O_plus_D_minus_1_squared_xy_post_to_primary"
    ),
    "path_length": "sum_t_0_to_H_minus_1_euclidean_xy_post_minus_pre",
    "lexicographic_keys": [
        "violation_count",
        "gate_arrival_step",
        "event_tracking_error",
        "path_length",
        "original_stage_x",
        "original_stage_y",
    ],
}
RETURN_READY_OWNERSHIP_RULE = (
    "lifecycle_owner_to_target_owned_internal_row|service_active_and_owns_"
    "vacant_primary|no_position_tolerance_or_storage_row"
)
PRE_ACTION_CONTEXT_SERVICE_MASK_RULE = "complete_bool8_target_owned_internal_order"
FIRST_MATCH_EVALUATION_RULE = (
    "strict_lazy_stop_at_first_match_lower_priority_statuses_null"
)
ENVIRONMENT_BACKEND = (
    "envs.pettingzoo.relay.energy_aware.UAVEnergyAwareRelayEnv|S7-S1"
)

SOURCE_MANIFEST = "source_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
SOURCE_PROOF = "proof/episode_0_source.json"
ORACLE_PROOF = "proof/oracle_qualification.json"
TRACKER_PROOF = "proof/common_tracker_qualification.json"
ORACLE_SAFETY_LEDGER_PROOF = "proof/oracle_safety_ledger.json"
ORACLE_BEHAVIORAL_REPLAY_PROOF = "proof/oracle_behavioral_replay.json"


@dataclass(frozen=True)
class _ValidatedSourceArtifacts:
    manifest: Mapping[str, Any]
    episode: geometry.G0EpisodeSource
    ledger: source.OracleSafetyLedger
    ledger_context: source._ValidatedOracleSafetyContext
    replay_primitive: Mapping[str, Any]
    replay_certificate: source.OracleSafetyCertificate

_SHA1 = re.compile(r"^[0-9a-f]{40}$")

_SOURCE_MANIFEST_KEYS = frozenset(
    {
        "status",
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "design_round",
        "design_disposition",
        "design_package_stage_commit",
        "design_archive_commit",
        "claim_scope",
        "evidence_source_commit",
        "oracle_safety_clarification_round",
        "oracle_safety_package_stage_commit",
        "oracle_safety_archive_commit",
        "oracle_safety_disposition",
        "replay_clarification_round",
        "replay_package_stage_commit",
        "replay_archive_commit",
        "replay_disposition",
        "return_ready_step_clarification_round",
        "return_ready_step_package_stage_commit",
        "return_ready_step_archive_commit",
        "return_ready_step_disposition",
        "accepted_g1_source_commit",
        "accepted_g1_tracker_source_sha256",
        "environment_backend",
        "formal",
        "formal_execution_authorized",
        "proof_only",
        "scientific_iteration_cost",
        "learning_enabled",
        "optimizer_enabled",
        "checkpoint_enabled",
        "physical_horizon_steps",
        "physical_fleet_size",
        "ground_users",
        "ground_base_stations",
        "paired_episode_ids",
        "episode_id_inventory",
        "bootstrap_resamples",
        "bootstrap_generator",
        "bootstrap_seed",
        "K_search",
        "K_search_ceiling",
        "nested_rollout",
        "replanning",
        "tree_or_beam_or_mcts",
        "real_environment_transitions",
        "hypothetical_candidate_transitions",
        "geometry_support_rule",
        "geometry_support_certificate",
        "oracle_ranking_arithmetic",
        "return_ready_ownership_rule",
        "pre_action_context_service_mask_rule",
        "first_match_evaluation_rule",
        "source_proof",
        "oracle_proof",
        "tracker_proof",
        "oracle_safety_ledger_proof",
        "oracle_behavioral_replay_proof",
        "artifact_inventory",
    }
)
_EVALUATION_KEYS = frozenset(
    {
        "status",
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "formal",
        "proof_only",
        "scientific_iteration_cost",
        "source_manifest_sha256",
        "metric_witness",
        "bootstrap_plan",
        "clopper_pearson_witness",
        "evaluation_optimizer_steps",
        "real_environment_transitions",
        "production_episode_validity_witness",
    }
)
_ANALYSIS_KEYS = frozenset(
    {
        "status",
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "formal",
        "proof_only",
        "scientific_iteration_cost",
        "source_manifest_sha256",
        "evaluation_manifest_sha256",
        "first_match_order",
        "branch_witnesses",
        "primitive_analysis_witness",
        "operational_valid",
        "result_branch",
        "scientific_conclusion",
        "claim_scope",
        "additional_environment_transitions",
        "additional_optimizer_steps",
    }
)
_BEHAVIORAL_REPLAY_KEYS = frozenset(
    {
        "schema_version",
        "ledger_sha256",
        "selected_candidate_id",
        "prebehavior_self_replay",
        "behavioral_execution",
        "behavioral_self_replay",
        "certificate",
    }
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    payload = _canonical_bytes(dict(value)) + b"\n"
    if temporary.exists():
        raise ValueError(f"G0 stale temporary artifact exists: {temporary.name}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary.read_bytes() != payload or json.loads(payload) != dict(value):
            raise ValueError("G0 temporary artifact validation failed")
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G0 artifact {path.name} is not a mapping")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_exact_keys(value: Any, keys: frozenset[str], *, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ValueError(f"G0 {label} exact schema mismatch")


def _validate_source_commit(value: str) -> str:
    candidate = str(value)
    if _SHA1.fullmatch(candidate) is None:
        raise ValueError("G0 source commit must be a lowercase 40-character SHA-1")
    return candidate


def _require_fresh_root(path: Path) -> Path:
    root = Path(path).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("G0 run root must be absent or empty")
    return root


def _reference(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _digest(path),
    }


def _assert_exact_files(root: Path, expected: set[str]) -> None:
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise ValueError(
            f"G0 terminal proof inventory mismatch: expected {sorted(expected)}, got {sorted(actual)}"
        )


def readiness_interface_smoke(*, source_commit: str) -> dict[str, Any]:
    commit = _validate_source_commit(source_commit)
    if source.FORMAL_EXECUTION_AUTHORIZED or FORMAL_EXECUTION_AUTHORIZED:
        raise RuntimeError("G0 readiness requires formal execution to remain closed")
    if any((source.LEARNING_ENABLED, source.OPTIMIZER_ENABLED, source.CHECKPOINT_ENABLED)):
        raise RuntimeError("G0 readiness found a prohibited learning artifact class")
    episode = geometry.make_episode_source(0)
    source_primitive = episode.to_primitive()
    geometry_primitive = source_primitive.get("geometry")
    geometry_support_certificate = (
        geometry_primitive.get("geometry_support_certificate")
        if isinstance(geometry_primitive, Mapping)
        else None
    )
    if not isinstance(geometry_support_certificate, Mapping):
        raise RuntimeError("G0 universal geometry-support certificate is absent")
    environment = source.UAVSourceIdentifiabilityEnv(episode, source.Cell.EVENT)
    try:
        production_shapes = {
            "uav_positions": list(np.asarray(environment.uav_positions).shape),
            "service_mask": list(np.asarray(environment._service_active_mask).shape),
            "action": [source.PHYSICAL_UAVS, source.ACTION_DIM],
        }
    finally:
        environment.close()
    required_source_interfaces = (
        source.build_oracle_safety_ledger,
        source.oracle_safety_ledger_from_primitive,
        source.validate_oracle_safety_primitive,
        source.build_oracle_branch_aware_replay_evidence,
        source.validate_oracle_branch_aware_replay_primitive,
        source.build_proof_episode_validity,
        source.analyze_proof_fixture,
    )
    if not all(callable(item) for item in required_source_interfaces):
        raise RuntimeError("G0 registered-ledger production interface is incomplete")
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": commit,
        "design_round": source.DESIGN_ROUND,
        "design_package_stage_commit": source.DESIGN_PACKAGE_STAGE_COMMIT,
        "design_archive_commit": source.DESIGN_ARCHIVE_COMMIT,
        "design_disposition": DESIGN_DISPOSITION,
        "claim_scope": CLAIM_SCOPE,
        "interfaces": [
            "train",
            "evaluate",
            "analyze",
            "readiness-smoke",
            "readiness-train",
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ],
        "formal_execution_authorized": False,
        "production_shapes": production_shapes,
        "oracle_safety_disposition": ORACLE_SAFETY_DISPOSITION,
        "replay_disposition": REPLAY_DISPOSITION,
        "return_ready_step_disposition": RETURN_READY_STEP_DISPOSITION,
        "bootstrap_generator": BOOTSTRAP_GENERATOR,
        "bootstrap_seed": statistics.BOOTSTRAP_SEED,
        "geometry_support_rule": GEOMETRY_SUPPORT_RULE,
        "geometry_support_certificate": geometry_support_certificate,
        "oracle_ranking_arithmetic": ORACLE_RANKING_ARITHMETIC,
        "return_ready_ownership_rule": RETURN_READY_OWNERSHIP_RULE,
        "pre_action_context_service_mask_rule": (
            PRE_ACTION_CONTEXT_SERVICE_MASK_RULE
        ),
        "first_match_evaluation_rule": FIRST_MATCH_EVALUATION_RULE,
        "scientific_iteration_cost": 0,
        "passed": True,
    }


def _build_tracker_proof(episode: geometry.G0EpisodeSource) -> dict[str, Any]:
    physical = np.concatenate(
        (
            episode.geometry.physical_xy,
            np.full((source.PHYSICAL_UAVS, 1), geometry.FIXED_ALTITUDE_M),
        ),
        axis=1,
    )
    targets = np.stack(
        [
            np.concatenate(
                (
                    episode.geometry.coordinate(geometry.TargetLabel.parse(label)),
                    [geometry.FIXED_ALTITUDE_M],
                )
            )
            for label in episode.assignment.row_to_target
        ]
    )
    return source.qualify_common_tracker(
        episode_source=episode,
        physical_positions=physical,
        target_positions=targets,
        active_mask=np.ones(source.PHYSICAL_UAVS, dtype=np.bool_),
        max_speed=30.0,
        max_vertical_speed=5.0,
        time_step=1.0,
        permutation=(3, 1, 7, 0, 6, 2, 5, 4),
    )


def readiness_train(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    commit = _validate_source_commit(source_commit)
    root = _require_fresh_root(run_root)
    root.mkdir(parents=True, exist_ok=True)
    episode = geometry.make_episode_source(0)
    source_value = episode.to_primitive()
    geometry_primitive = source_value.get("geometry")
    geometry_support_certificate = (
        geometry_primitive.get("geometry_support_certificate")
        if isinstance(geometry_primitive, Mapping)
        else None
    )
    if not isinstance(geometry_support_certificate, Mapping):
        raise RuntimeError("G0 universal geometry-support certificate is absent")
    source_path = root / SOURCE_PROOF
    _write_json(source_path, source_value)

    ledger, ledger_context = source._build_oracle_safety_ledger_with_context(
        episode
    )
    ledger_value = ledger.to_primitive()
    ledger_path = root / ORACLE_SAFETY_LEDGER_PROOF
    _write_json(ledger_path, ledger_value)

    oracle = source._oracle_qualification_from_validated_context(ledger_context)
    oracle_value = oracle.to_primitive()
    if not oracle.passed:
        raise RuntimeError("G0 proof oracle qualification failed")
    oracle_path = root / ORACLE_PROOF
    _write_json(oracle_path, oracle_value)

    replay_value = (
        source._build_oracle_branch_aware_replay_evidence_from_validated_context(
            ledger_context
        )
    )
    _require_exact_keys(
        replay_value, _BEHAVIORAL_REPLAY_KEYS, label="behavioral replay proof"
    )
    replay_path = root / ORACLE_BEHAVIORAL_REPLAY_PROOF
    _write_json(replay_path, replay_value)

    tracker = _build_tracker_proof(episode)
    if not tracker["passed"]:
        raise RuntimeError("G0 proof common tracker qualification failed")
    tracker_path = root / TRACKER_PROOF
    _write_json(tracker_path, tracker)

    manifest = {
        "status": "COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": commit,
        "design_round": source.DESIGN_ROUND,
        "design_disposition": DESIGN_DISPOSITION,
        "design_package_stage_commit": source.DESIGN_PACKAGE_STAGE_COMMIT,
        "design_archive_commit": source.DESIGN_ARCHIVE_COMMIT,
        "claim_scope": CLAIM_SCOPE,
        "evidence_source_commit": source.EVIDENCE_SOURCE_COMMIT,
        "oracle_safety_clarification_round": source.ORACLE_SAFETY_CLARIFICATION_ROUND,
        "oracle_safety_package_stage_commit": source.ORACLE_SAFETY_PACKAGE_STAGE_COMMIT,
        "oracle_safety_archive_commit": source.ORACLE_SAFETY_ARCHIVE_COMMIT,
        "oracle_safety_disposition": ORACLE_SAFETY_DISPOSITION,
        "replay_clarification_round": source.REPLAY_CLARIFICATION_ROUND,
        "replay_package_stage_commit": source.REPLAY_PACKAGE_STAGE_COMMIT,
        "replay_archive_commit": source.REPLAY_ARCHIVE_COMMIT,
        "replay_disposition": REPLAY_DISPOSITION,
        "return_ready_step_clarification_round": source.RETURN_READY_STEP_CLARIFICATION_ROUND,
        "return_ready_step_package_stage_commit": source.RETURN_READY_STEP_PACKAGE_STAGE_COMMIT,
        "return_ready_step_archive_commit": source.RETURN_READY_STEP_ARCHIVE_COMMIT,
        "return_ready_step_disposition": RETURN_READY_STEP_DISPOSITION,
        "accepted_g1_source_commit": source.ACCEPTED_G1_SOURCE_COMMIT,
        "accepted_g1_tracker_source_sha256": source.ACCEPTED_G1_TRACKER_SOURCE_SHA256,
        "environment_backend": ENVIRONMENT_BACKEND,
        "formal": False,
        "formal_execution_authorized": False,
        "proof_only": True,
        "scientific_iteration_cost": 0,
        "learning_enabled": False,
        "optimizer_enabled": False,
        "checkpoint_enabled": False,
        "physical_horizon_steps": source.PHYSICAL_HORIZON,
        "physical_fleet_size": source.PHYSICAL_UAVS,
        "ground_users": source.GROUND_USERS,
        "ground_base_stations": geometry.GROUND_BASE_STATIONS,
        "paired_episode_ids": len(statistics.EPISODE_IDS),
        "episode_id_inventory": list(statistics.EPISODE_IDS),
        "bootstrap_resamples": statistics.BOOTSTRAP_RESAMPLES,
        "bootstrap_generator": BOOTSTRAP_GENERATOR,
        "bootstrap_seed": statistics.BOOTSTRAP_SEED,
        "K_search": source.K_SEARCH,
        "K_search_ceiling": source.K_SEARCH_CEILING,
        "nested_rollout": False,
        "replanning": False,
        "tree_or_beam_or_mcts": False,
        "real_environment_transitions": 0,
        "hypothetical_candidate_transitions": source.PHYSICAL_HORIZON * source.K_SEARCH,
        "geometry_support_rule": GEOMETRY_SUPPORT_RULE,
        "geometry_support_certificate": geometry_support_certificate,
        "oracle_ranking_arithmetic": ORACLE_RANKING_ARITHMETIC,
        "return_ready_ownership_rule": RETURN_READY_OWNERSHIP_RULE,
        "pre_action_context_service_mask_rule": (
            PRE_ACTION_CONTEXT_SERVICE_MASK_RULE
        ),
        "first_match_evaluation_rule": FIRST_MATCH_EVALUATION_RULE,
        "source_proof": _reference(source_path, root),
        "oracle_proof": _reference(oracle_path, root),
        "tracker_proof": _reference(tracker_path, root),
        "oracle_safety_ledger_proof": _reference(ledger_path, root),
        "oracle_behavioral_replay_proof": _reference(replay_path, root),
        "artifact_inventory": [
            SOURCE_PROOF,
            ORACLE_PROOF,
            TRACKER_PROOF,
            ORACLE_SAFETY_LEDGER_PROOF,
            ORACLE_BEHAVIORAL_REPLAY_PROOF,
        ],
    }
    _require_exact_keys(manifest, _SOURCE_MANIFEST_KEYS, label="source manifest")
    _write_json(root / SOURCE_MANIFEST, manifest)
    validate_source_artifacts(root)
    return manifest


def _load_reference(
    root: Path,
    reference: Any,
    *,
    label: str,
    expected_relative_path: str,
) -> dict[str, Any]:
    if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
        raise ValueError(f"G0 {label} reference schema mismatch")
    relative = Path(str(reference["path"]))
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != expected_relative_path
    ):
        raise ValueError(f"G0 {label} path is not the registered root-local path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"G0 {label} path escapes the run root") from error
    if not path.is_file() or _digest(path) != reference["sha256"]:
        raise ValueError(f"G0 {label} digest mismatch")
    return _read_json(path)


def _validate_source_artifacts_bundle(
    run_root: Path,
) -> _ValidatedSourceArtifacts:
    root = Path(run_root).resolve()
    value = _read_json(root / SOURCE_MANIFEST)
    _require_exact_keys(value, _SOURCE_MANIFEST_KEYS, label="source manifest")
    commit = _validate_source_commit(value.get("source_commit", ""))
    episode = geometry.make_episode_source(0)
    episode_primitive = episode.to_primitive()
    expected_scalars = {
        "status": "COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "design_round": source.DESIGN_ROUND,
        "design_disposition": DESIGN_DISPOSITION,
        "design_package_stage_commit": source.DESIGN_PACKAGE_STAGE_COMMIT,
        "design_archive_commit": source.DESIGN_ARCHIVE_COMMIT,
        "claim_scope": CLAIM_SCOPE,
        "evidence_source_commit": source.EVIDENCE_SOURCE_COMMIT,
        "oracle_safety_clarification_round": source.ORACLE_SAFETY_CLARIFICATION_ROUND,
        "oracle_safety_package_stage_commit": source.ORACLE_SAFETY_PACKAGE_STAGE_COMMIT,
        "oracle_safety_archive_commit": source.ORACLE_SAFETY_ARCHIVE_COMMIT,
        "oracle_safety_disposition": ORACLE_SAFETY_DISPOSITION,
        "replay_clarification_round": source.REPLAY_CLARIFICATION_ROUND,
        "replay_package_stage_commit": source.REPLAY_PACKAGE_STAGE_COMMIT,
        "replay_archive_commit": source.REPLAY_ARCHIVE_COMMIT,
        "replay_disposition": REPLAY_DISPOSITION,
        "return_ready_step_clarification_round": source.RETURN_READY_STEP_CLARIFICATION_ROUND,
        "return_ready_step_package_stage_commit": source.RETURN_READY_STEP_PACKAGE_STAGE_COMMIT,
        "return_ready_step_archive_commit": source.RETURN_READY_STEP_ARCHIVE_COMMIT,
        "return_ready_step_disposition": RETURN_READY_STEP_DISPOSITION,
        "accepted_g1_source_commit": source.ACCEPTED_G1_SOURCE_COMMIT,
        "accepted_g1_tracker_source_sha256": source.ACCEPTED_G1_TRACKER_SOURCE_SHA256,
        "environment_backend": ENVIRONMENT_BACKEND,
        "formal": False,
        "formal_execution_authorized": False,
        "proof_only": True,
        "scientific_iteration_cost": 0,
        "learning_enabled": False,
        "optimizer_enabled": False,
        "checkpoint_enabled": False,
        "physical_horizon_steps": source.PHYSICAL_HORIZON,
        "physical_fleet_size": source.PHYSICAL_UAVS,
        "ground_users": source.GROUND_USERS,
        "ground_base_stations": geometry.GROUND_BASE_STATIONS,
        "paired_episode_ids": len(statistics.EPISODE_IDS),
        "episode_id_inventory": list(statistics.EPISODE_IDS),
        "bootstrap_resamples": statistics.BOOTSTRAP_RESAMPLES,
        "bootstrap_generator": BOOTSTRAP_GENERATOR,
        "bootstrap_seed": statistics.BOOTSTRAP_SEED,
        "K_search": source.K_SEARCH,
        "K_search_ceiling": source.K_SEARCH_CEILING,
        "nested_rollout": False,
        "replanning": False,
        "tree_or_beam_or_mcts": False,
        "real_environment_transitions": 0,
        "hypothetical_candidate_transitions": source.PHYSICAL_HORIZON * source.K_SEARCH,
        "geometry_support_rule": GEOMETRY_SUPPORT_RULE,
        "geometry_support_certificate": episode_primitive["geometry"][
            "geometry_support_certificate"
        ],
        "oracle_ranking_arithmetic": ORACLE_RANKING_ARITHMETIC,
        "return_ready_ownership_rule": RETURN_READY_OWNERSHIP_RULE,
        "pre_action_context_service_mask_rule": (
            PRE_ACTION_CONTEXT_SERVICE_MASK_RULE
        ),
        "first_match_evaluation_rule": FIRST_MATCH_EVALUATION_RULE,
        "artifact_inventory": [
            SOURCE_PROOF,
            ORACLE_PROOF,
            TRACKER_PROOF,
            ORACLE_SAFETY_LEDGER_PROOF,
            ORACLE_BEHAVIORAL_REPLAY_PROOF,
        ],
    }
    if any(value.get(key) != expected for key, expected in expected_scalars.items()):
        raise ValueError("G0 source manifest invariant mismatch")
    source_value = _load_reference(
        root,
        value["source_proof"],
        label="source proof",
        expected_relative_path=SOURCE_PROOF,
    )
    if source_value != episode_primitive:
        raise ValueError("G0 source proof does not reconstruct episode zero")
    ledger_value = _load_reference(
        root,
        value["oracle_safety_ledger_proof"],
        label="oracle safety ledger proof",
        expected_relative_path=ORACLE_SAFETY_LEDGER_PROOF,
    )
    ledger = source.oracle_safety_ledger_from_primitive(ledger_value)
    ledger_context = source._validated_oracle_safety_context(
        episode, ledger
    )
    safety_certificate = ledger_context.certificate
    replay_value = _load_reference(
        root,
        value["oracle_behavioral_replay_proof"],
        label="oracle behavioral replay proof",
        expected_relative_path=ORACLE_BEHAVIORAL_REPLAY_PROOF,
    )
    _require_exact_keys(
        replay_value, _BEHAVIORAL_REPLAY_KEYS, label="behavioral replay proof"
    )
    if (
        replay_value.get("ledger_sha256") != ledger.content_sha256
        or replay_value.get("selected_candidate_id") != ledger.selected_candidate_id
    ):
        raise ValueError("G0 behavioral replay identity mismatch")
    replay_certificate = (
        source._validate_oracle_branch_aware_replay_primitive_from_validated_context(
            ledger_context, replay_value
        )
    )
    if replay_value.get("certificate") != replay_certificate.to_primitive():
        raise ValueError("G0 behavioral replay certificate reconstruction mismatch")
    if safety_certificate.ledger_sha256 != replay_certificate.ledger_sha256:
        raise ValueError("G0 ledger/replay certificate digest mismatch")

    oracle_value = _load_reference(
        root,
        value["oracle_proof"],
        label="oracle proof",
        expected_relative_path=ORACLE_PROOF,
    )
    expected_oracle = source._oracle_qualification_from_validated_context(
        ledger_context
    ).to_primitive()
    if oracle_value != expected_oracle or oracle_value.get("passed") is not True:
        raise ValueError("G0 oracle proof reconstruction mismatch")
    tracker_value = _load_reference(
        root,
        value["tracker_proof"],
        label="tracker proof",
        expected_relative_path=TRACKER_PROOF,
    )
    expected_tracker = _build_tracker_proof(episode)
    if tracker_value != expected_tracker or tracker_value.get("passed") is not True:
        raise ValueError("G0 tracker proof reconstruction mismatch")
    if value["source_commit"] != commit:
        raise ValueError("G0 source commit normalization mismatch")
    prohibited = list(root.rglob("*.pt")) + list(root.rglob("*.pth"))
    if prohibited or (root / "checkpoints").exists():
        raise ValueError("G0 proof artifact contains a prohibited checkpoint")
    allowed = {
        SOURCE_MANIFEST,
        SOURCE_PROOF,
        ORACLE_PROOF,
        TRACKER_PROOF,
        ORACLE_SAFETY_LEDGER_PROOF,
        ORACLE_BEHAVIORAL_REPLAY_PROOF,
    }
    if (root / EVALUATION_MANIFEST).is_file():
        allowed.add(EVALUATION_MANIFEST)
    if (root / ANALYSIS_RESULT).is_file():
        allowed.add(ANALYSIS_RESULT)
    _assert_exact_files(root, allowed)
    return _ValidatedSourceArtifacts(
        manifest=value,
        episode=episode,
        ledger=ledger,
        ledger_context=ledger_context,
        replay_primitive=replay_value,
        replay_certificate=replay_certificate,
    )


def validate_source_artifacts(run_root: Path) -> dict[str, Any]:
    return dict(_validate_source_artifacts_bundle(run_root).manifest)


def readiness_validate(*, run_root: Path) -> dict[str, Any]:
    value = validate_source_artifacts(run_root)
    return {
        "artifact_validation": True,
        "source_commit": value["source_commit"],
        "additional_environment_transitions": 0,
        "additional_optimizer_steps": 0,
        "passed": True,
    }


def readiness_reload(*, run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    before = _digest(root / SOURCE_MANIFEST)
    value = validate_source_artifacts(root)
    after = _digest(root / SOURCE_MANIFEST)
    if before != after:
        raise RuntimeError("G0 reload mutated source evidence")
    return {
        "artifact_reload": True,
        "source_commit": value["source_commit"],
        "source_manifest_sha256": before,
        "additional_environment_transitions": 0,
        "additional_optimizer_steps": 0,
        "passed": True,
    }


def _metric_witness() -> dict[str, Any]:
    service = np.full(source.PHYSICAL_HORIZON, 0.90, dtype=np.float64)
    event = statistics.compute_episode_metrics(
        service,
        episode_id=0,
        control=source.Control.SAME_INFORMATION,
        cell=source.Cell.EVENT,
        onset=180,
        duration=80,
    )
    no_event = statistics.compute_episode_metrics(
        service,
        episode_id=0,
        control=source.Control.SAME_INFORMATION,
        cell=source.Cell.NO_EVENT,
        onset=180,
        duration=80,
    )
    catastrophe = service.copy()
    catastrophe[180:190] = np.nextafter(0.60, 0.0)
    catastrophe_row = statistics.compute_episode_metrics(
        catastrophe,
        episode_id=0,
        control=source.Control.SAME_INFORMATION,
        cell=source.Cell.EVENT,
        onset=180,
        duration=80,
    )
    return {
        "event_at_access_equality": event.to_primitive(),
        "no_event_at_access_equality": no_event.to_primitive(),
        "ten_step_catastrophe": catastrophe_row.to_primitive(),
    }


def _clopper_pearson_witness() -> dict[str, Any]:
    lower_zero, upper_zero = statistics.clopper_pearson_one_sided(0)
    lower_all, upper_all = statistics.clopper_pearson_one_sided(len(statistics.EPISODE_IDS))
    return {
        "k0": [lower_zero, upper_zero],
        "k128": [lower_all, upper_all],
        "tail_probability": 0.05,
    }


def _proof_episode_validity_from_bundle(
    bundle: _ValidatedSourceArtifacts,
) -> dict[str, Any]:
    return source._build_proof_episode_validity_from_validated_evidence(
        bundle.ledger_context,
        replay_primitive=bundle.replay_primitive,
        replay_certificate=bundle.replay_certificate,
    )


def readiness_evaluate(*, run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    bundle = _validate_source_artifacts_bundle(root)
    training = bundle.manifest
    production_witness = _proof_episode_validity_from_bundle(bundle)
    if (
        production_witness.get("operational_valid") is not True
        or production_witness.get("result_branch") is not None
    ):
        raise RuntimeError("G0 production proof episode validity failed")
    plan = statistics.make_bootstrap_index_plan()
    value = {
        "status": "COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": training["source_commit"],
        "formal": False,
        "proof_only": True,
        "scientific_iteration_cost": 0,
        "source_manifest_sha256": _digest(root / SOURCE_MANIFEST),
        "metric_witness": _metric_witness(),
        "bootstrap_plan": {
            "shape": list(plan.shape),
            "seed": statistics.BOOTSTRAP_SEED,
            "sha256": hashlib.sha256(plan.tobytes(order="C")).hexdigest(),
            "lower_order_statistic": 500,
            "upper_order_statistic": 9500,
            "interpolation": False,
        },
        "clopper_pearson_witness": _clopper_pearson_witness(),
        "evaluation_optimizer_steps": 0,
        "real_environment_transitions": 0,
        "production_episode_validity_witness": production_witness,
    }
    _require_exact_keys(value, _EVALUATION_KEYS, label="evaluation manifest")
    _write_json(root / EVALUATION_MANIFEST, value)
    _validate_evaluation_artifacts_from_bundle(root, bundle)
    return value


def _validate_evaluation_artifacts_from_bundle(
    run_root: Path,
    bundle: _ValidatedSourceArtifacts,
) -> dict[str, Any]:
    root = Path(run_root).resolve()
    training = bundle.manifest
    value = _read_json(root / EVALUATION_MANIFEST)
    _require_exact_keys(value, _EVALUATION_KEYS, label="evaluation manifest")
    plan = statistics.make_bootstrap_index_plan()
    expected_plan = {
        "shape": list(plan.shape),
        "seed": statistics.BOOTSTRAP_SEED,
        "sha256": hashlib.sha256(plan.tobytes(order="C")).hexdigest(),
        "lower_order_statistic": 500,
        "upper_order_statistic": 9500,
        "interpolation": False,
    }
    expected_production_witness = _proof_episode_validity_from_bundle(bundle)
    if (
        value.get("status") != "COMPLETE"
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("source_commit") != training["source_commit"]
        or value.get("formal") is not False
        or value.get("proof_only") is not True
        or value.get("scientific_iteration_cost") != 0
        or value.get("source_manifest_sha256") != _digest(root / SOURCE_MANIFEST)
        or value.get("metric_witness") != _metric_witness()
        or value.get("bootstrap_plan") != expected_plan
        or value.get("clopper_pearson_witness") != _clopper_pearson_witness()
        or value.get("evaluation_optimizer_steps") != 0
        or value.get("real_environment_transitions") != 0
        or value.get("production_episode_validity_witness")
        != expected_production_witness
    ):
        raise ValueError("G0 evaluation artifact invariant mismatch")
    allowed = {
        SOURCE_MANIFEST,
        EVALUATION_MANIFEST,
        SOURCE_PROOF,
        ORACLE_PROOF,
        TRACKER_PROOF,
        ORACLE_SAFETY_LEDGER_PROOF,
        ORACLE_BEHAVIORAL_REPLAY_PROOF,
    }
    if (root / ANALYSIS_RESULT).is_file():
        allowed.add(ANALYSIS_RESULT)
    _assert_exact_files(root, allowed)
    return value


def validate_evaluation_artifacts(run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    return _validate_evaluation_artifacts_from_bundle(
        root, _validate_source_artifacts_bundle(root)
    )


def _branch_witnesses() -> dict[str, dict[str, Any]]:
    cases = {
        "invalid": (False, None, None, None),
        "infeasible": (True, statistics.GateStatus.FAIL, None, None),
        "oracle_only": (True, statistics.GateStatus.PASS, statistics.GateStatus.FAIL, None),
        "non_causal": (True, statistics.GateStatus.PASS, statistics.GateStatus.PASS, statistics.GateStatus.FAIL),
        "underpowered_oracle": (True, statistics.GateStatus.OPEN, None, None),
        "underpowered_sameinfo": (True, statistics.GateStatus.PASS, statistics.GateStatus.OPEN, None),
        "underpowered_causal": (True, statistics.GateStatus.PASS, statistics.GateStatus.PASS, statistics.GateStatus.OPEN),
        "identified": (True, statistics.GateStatus.PASS, statistics.GateStatus.PASS, statistics.GateStatus.PASS),
    }
    return {
        name: {
            "valid": valid,
            "ORACLE_STATUS": oracle.value if oracle is not None else None,
            "SAMEINFO_STATUS": sameinfo.value if sameinfo is not None else None,
            "CAUSAL_STATUS": causal.value if causal is not None else None,
            "result_branch": statistics.select_result_branch(
                valid=valid,
                oracle_status=oracle,
                sameinfo_status=sameinfo,
                causal_status=causal,
            ),
        }
        for name, (valid, oracle, sameinfo, causal) in cases.items()
    }


def _primitive_analysis_witness(
    bundle: _ValidatedSourceArtifacts,
) -> dict[str, Any]:
    reconstructed = source._analyze_proof_fixture_from_validated_evidence(
        bundle.ledger_context,
        replay_primitive=bundle.replay_primitive,
        replay_certificate=bundle.replay_certificate,
    )
    if (
        reconstructed.get("proof_only") is not True
        or reconstructed.get("operational_valid") is not True
        or reconstructed.get("operational_errors") != []
        or reconstructed.get("result_branch") is not None
    ):
        raise RuntimeError("G0 public primitive proof analyzer failed")
    return reconstructed


def readiness_analyze(*, run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    bundle = _validate_source_artifacts_bundle(root)
    training = bundle.manifest
    evaluation = _validate_evaluation_artifacts_from_bundle(root, bundle)
    primitive_witness = _primitive_analysis_witness(bundle)
    value = {
        "status": "COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": training["source_commit"],
        "formal": False,
        "proof_only": True,
        "scientific_iteration_cost": 0,
        "source_manifest_sha256": _digest(root / SOURCE_MANIFEST),
        "evaluation_manifest_sha256": _digest(root / EVALUATION_MANIFEST),
        "first_match_order": list(statistics.FIRST_MATCH_ORDER),
        "branch_witnesses": _branch_witnesses(),
        "primitive_analysis_witness": primitive_witness,
        "operational_valid": False,
        "result_branch": None,
        "scientific_conclusion": None,
        "claim_scope": CLAIM_SCOPE,
        "additional_environment_transitions": 0,
        "additional_optimizer_steps": 0,
    }
    del evaluation
    _require_exact_keys(value, _ANALYSIS_KEYS, label="analysis result")
    _write_json(root / ANALYSIS_RESULT, value)
    _validate_analysis_artifacts_from_bundle(root, bundle)
    return value


def _validate_analysis_artifacts_from_bundle(
    run_root: Path,
    bundle: _ValidatedSourceArtifacts,
) -> dict[str, Any]:
    root = Path(run_root).resolve()
    training = bundle.manifest
    _validate_evaluation_artifacts_from_bundle(root, bundle)
    value = _read_json(root / ANALYSIS_RESULT)
    _require_exact_keys(value, _ANALYSIS_KEYS, label="analysis result")
    if (
        value.get("status") != "COMPLETE"
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("source_commit") != training["source_commit"]
        or value.get("formal") is not False
        or value.get("proof_only") is not True
        or value.get("scientific_iteration_cost") != 0
        or value.get("source_manifest_sha256") != _digest(root / SOURCE_MANIFEST)
        or value.get("evaluation_manifest_sha256") != _digest(root / EVALUATION_MANIFEST)
        or value.get("first_match_order") != list(statistics.FIRST_MATCH_ORDER)
        or value.get("branch_witnesses") != _branch_witnesses()
        or value.get("primitive_analysis_witness")
        != _primitive_analysis_witness(bundle)
        or value.get("operational_valid") is not False
        or value.get("result_branch") is not None
        or value.get("scientific_conclusion") is not None
        or value.get("claim_scope") != CLAIM_SCOPE
        or value.get("additional_environment_transitions") != 0
        or value.get("additional_optimizer_steps") != 0
    ):
        raise ValueError("G0 analysis artifact invariant mismatch")
    _assert_exact_files(
        root,
        {
            SOURCE_MANIFEST,
            EVALUATION_MANIFEST,
            ANALYSIS_RESULT,
            SOURCE_PROOF,
            ORACLE_PROOF,
            TRACKER_PROOF,
            ORACLE_SAFETY_LEDGER_PROOF,
            ORACLE_BEHAVIORAL_REPLAY_PROOF,
        },
    )
    return value


def validate_analysis_artifacts(run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    return _validate_analysis_artifacts_from_bundle(
        root, _validate_source_artifacts_bundle(root)
    )


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RUN_KEYS = (
    "O|E",
    "O|Z",
    "S|E",
    "S|Z",
    "N|E",
    "N|Z",
)
_RUN_IDENTITIES = (
    (source.Control.ORACLE, source.Cell.EVENT),
    (source.Control.ORACLE, source.Cell.NO_EVENT),
    (source.Control.SAME_INFORMATION, source.Cell.EVENT),
    (source.Control.SAME_INFORMATION, source.Cell.NO_EVENT),
    (source.Control.NO_REALLOCATION, source.Cell.EVENT),
    (source.Control.NO_REALLOCATION, source.Cell.NO_EVENT),
)
_BUNDLE_KEYS = frozenset(
    {
        "schema_id", "schema_version", "formal", "contract_sha256",
        "episode_id", "source_primitive", "source_sha256", "runs",
        "bundle_sha256",
    }
)
_PREFLIGHT_CONTRACT_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "frozen_records",
        "runtime_binding", "environment_manifest", "content_sha256",
    }
)
_PREFLIGHT_RESULT_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "episode_bundle_sha256", "episode_id", "run_count",
        "primary_real_simulator_steps", "validation_replay_steps",
        "required_certificates", "zero_counters", "oracle_event_return_ready_step",
        "oracle_no_event_return_ready_step", "ORACLE_STATUS", "SAMEINFO_STATUS",
        "CAUSAL_STATUS", "result_branch", "scientific_conclusion",
        "scientific_iteration_cost", "content_sha256",
    }
)
_REQUIRED_CERTIFICATE_KEYS = frozenset(
    {
        "source", "geometry", "assignment", "tracker", "oracle_safety",
        "oracle_EVENT_replay", "oracle_NO_EVENT_replay", "ownership",
        "permutation", "pairing", "NO_EVENT_identity", "metric_arithmetic",
    }
)
_ZERO_COUNTER_KEYS = frozenset(
    {
        "tracker_failures", "action_support_violations",
        "ownership_violations", "oracle_qualification_failures",
    }
)
_FORMAL_CONTRACT_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "frozen_records",
        "runtime_binding", "environment_manifest",
        "preflight_terminal_manifest_sha256", "content_sha256",
    }
)
_SOURCE_MANIFEST_FORMAL_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "source_identities", "execution_identity", "environment_identity",
        "episode_ids", "control_order", "cell_order", "run_count",
        "simulator_step_count", "episode_bundle_references_and_sha256_values",
        "content_sha256",
    }
)
_EVALUATION_FORMAL_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "source_manifest_sha256", "episode_bundle_sha256_by_id", "metric_rows",
        "validity_records", "bootstrap_generator", "bootstrap_seed",
        "bootstrap_shape", "bootstrap_index_sha256", "real_simulator_steps",
        "optimizer_steps", "result_branch", "evaluation_sha256",
    }
)
_ANALYSIS_FORMAL_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "source_manifest_sha256", "evaluation_manifest_sha256", "continuous",
        "binary", "bootstrap_seed", "bootstrap_resamples", "bootstrap_index_sha256",
        "quantile_rule", "valid", "validity_errors", "ORACLE_STATUS",
        "SAMEINFO_STATUS", "CAUSAL_STATUS", "first_match_order", "result_branch",
        "claim_scope", "scientific_iteration_cost", "analysis_sha256",
    }
)


@dataclass(frozen=True)
class FormalRuntimeBinding:
    execution_mode: str
    run_root: Path
    nonformal_preflight_root: Path | None
    bound_formal_root: Path
    source_commit: str
    accepted_g0_source_commit: str
    formal_execution_commit: str
    formal_authorization_token: str
    external_user_authorization_reference: str
    failed_root_identity: str
    failed_root_schema_id: str
    failed_root_schema_version: int
    workers: int
    start_method: str

    def carrier_primitive(self) -> dict[str, Any]:
        return {
            "external_user_authorization_reference": self.external_user_authorization_reference,
            "bound_formal_root": str(self.bound_formal_root),
            "failed_root_identity": self.failed_root_identity,
            "failed_root_schema_id": self.failed_root_schema_id,
            "failed_root_schema_version": self.failed_root_schema_version,
        }

    def to_primitive(self) -> dict[str, Any]:
        return {
            "execution_mode": self.execution_mode,
            "run_root": str(self.run_root),
            "nonformal_preflight_root": (
                None if self.nonformal_preflight_root is None
                else str(self.nonformal_preflight_root)
            ),
            "source_commit": self.source_commit,
            "accepted_g0_source_commit": self.accepted_g0_source_commit,
            "formal_execution_commit": self.formal_execution_commit,
            "formal_authorization_token": self.formal_authorization_token,
            "workers": self.workers,
            "start_method": self.start_method,
            "python_executable": str(Path(sys.executable).resolve()),
            "aligned_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
            "aligned_scientific_source_blob_sha": ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA,
            "alignment_stage_commit": ALIGNMENT_STAGE_COMMIT,
            "alignment_disposition": ALIGNMENT_DISPOSITION,
            "carrier": self.carrier_primitive(),
        }


_RUNTIME_BINDING_KEYS = frozenset(
    {
        "execution_mode",
        "run_root",
        "nonformal_preflight_root",
        "source_commit",
        "accepted_g0_source_commit",
        "formal_execution_commit",
        "formal_authorization_token",
        "workers",
        "start_method",
        "python_executable",
        "aligned_implementation_commit",
        "aligned_scientific_source_blob_sha",
        "alignment_stage_commit",
        "alignment_disposition",
        "carrier",
    }
)
_RUNTIME_CARRIER_KEYS = frozenset(
    {
        "external_user_authorization_reference",
        "bound_formal_root",
        "failed_root_identity",
        "failed_root_schema_id",
        "failed_root_schema_version",
    }
)


def _require_runtime_binding_schema(value: Any) -> None:
    _require_exact_keys(value, _RUNTIME_BINDING_KEYS, label="runtime binding")
    _require_exact_keys(
        value["carrier"],
        _RUNTIME_CARRIER_KEYS,
        label="runtime binding carrier",
    )


def _require_preflight_runtime_path_binding(value: Mapping[str, Any], root: Path) -> None:
    if (
        value["execution_mode"] != "nonformal-preflight"
        or value["run_root"] != str(root.resolve())
        or value["nonformal_preflight_root"] is not None
        or value["python_executable"] != str(Path(sys.executable).resolve())
    ):
        raise ValueError("G0 gate_06 preflight runtime path binding mismatch")


def _content_digest(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def _validate_content_digest(value: Mapping[str, Any], field: str) -> None:
    candidate = dict(value)
    stored = candidate.pop(field, None)
    if stored != hashlib.sha256(_canonical_bytes(candidate)).hexdigest():
        raise ValueError(f"G0 {field} content digest mismatch")


def _load_frozen_records() -> dict[str, str]:
    records: dict[str, str] = {}
    for raw_line in FROZEN_CONTRACT_PATH.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        if not key or key in records:
            raise ValueError("G0 frozen contract record inventory is ambiguous")
        records[key] = value
    if records.get("formal_interface_contract_id") != FORMAL_INTERFACE_CONTRACT_ID:
        raise ValueError("G0 frozen formal-interface contract identity mismatch")
    if records.get("scientific_source_module_git_blob_sha") != (
        FROZEN_V2_SCIENTIFIC_SOURCE_BLOB_SHA
    ):
        raise ValueError("G0 frozen v2 scientific source blob identity mismatch")
    clarification: dict[str, str] = {}
    for raw_line in RECONSTRUCTION_CLARIFICATION_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        if not key or key in clarification:
            raise ValueError("G0 reconstruction clarification is ambiguous")
        clarification[key] = value
    if clarification != RECONSTRUCTION_CLARIFICATION_RECORDS:
        raise ValueError("G0 reconstruction clarification disposition mismatch")
    if set(records).intersection(clarification):
        raise ValueError("G0 frozen contract/clarification keys collide")
    records.update(clarification)
    records["reconstruction_clarification_stage_commit"] = (
        RECONSTRUCTION_CLARIFICATION_STAGE_COMMIT
    )
    return records


def _absolute_path(value: Path, *, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"G0 {label} must be absolute")
    return path.resolve()


def _paths_nested(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        return False


def _command_output(argv: Sequence[str]) -> str:
    completed = subprocess.run(
        list(argv), cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise ValueError(f"G0 identity command failed: {' '.join(argv)}")
    return completed.stdout.strip()


def _verify_git_identity(commit: str) -> None:
    if _command_output(("git", "rev-parse", "HEAD")) != commit:
        raise ValueError("G0 formal execution commit is not current HEAD")
    if _command_output(("git", "status", "--porcelain=v1", "--untracked-files=all")):
        raise ValueError("G0 formal execution worktree is not clean")
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", FORMAL_INTERFACE_SOURCE_COMMIT, commit),
        cwd=PROJECT_ROOT, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise ValueError("G0 formal execution commit lacks the frozen interface ancestor")
    if ALIGNED_IMPLEMENTATION_COMMIT is None:
        raise ValueError("G0 aligned implementation identity is absent")
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ALIGNED_IMPLEMENTATION_COMMIT, commit),
        cwd=PROJECT_ROOT, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise ValueError("G0 formal execution commit lacks the aligned source ancestor")
    if ALIGNMENT_STAGE_COMMIT is None:
        raise ValueError("G0 alignment-stage identity is absent")
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ALIGNMENT_STAGE_COMMIT, commit),
        cwd=PROJECT_ROOT, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise ValueError("G0 formal execution commit lacks the alignment-stage ancestor")
    frozen_contract_blob = _command_output(
        (
            "git", "rev-parse",
            f"{commit}:{FROZEN_CONTRACT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        )
    )
    clarification_blob = _command_output(
        (
            "git", "rev-parse",
            f"{commit}:{RECONSTRUCTION_CLARIFICATION_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        )
    )
    if frozen_contract_blob != FROZEN_CONTRACT_GIT_BLOB_SHA or (
        clarification_blob != RECONSTRUCTION_CLARIFICATION_GIT_BLOB_SHA
    ):
        raise ValueError("G0 frozen contract Git blob identity mismatch")
    blob = _command_output(
        ("git", "rev-parse", f"{commit}:ha_ctse_process/uav_source_identifiability_g0.py")
    )
    aligned_blob = _command_output(
        (
            "git", "rev-parse",
            f"{ALIGNED_IMPLEMENTATION_COMMIT}:ha_ctse_process/uav_source_identifiability_g0.py",
        )
    )
    if (
        ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA is None
        or blob != aligned_blob
        or blob != ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA
    ):
        raise ValueError("G0 scientific source module Git blob identity mismatch")
    if source.common_tracker_source_digest() != source.ACCEPTED_G1_TRACKER_SOURCE_SHA256:
        raise ValueError("G0 accepted G1 tracker source digest mismatch")
    if source.shared_action_method_digests() != source.ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256:
        raise ValueError("G0 accepted G1 shared action source digests mismatch")


def _runtime_environment_manifest(commit: str) -> dict[str, Any]:
    if platform.python_implementation() != "CPython":
        raise ValueError("G0 formal runner requires CPython")
    if not Path(sys.executable).is_absolute():
        raise ValueError("G0 Python executable identity is not absolute")
    required_environment = {
        "PYTHONHASHSEED": "0",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "OMP_DYNAMIC": "FALSE",
        "MKL_DYNAMIC": "FALSE",
        "CUDA_VISIBLE_DEVICES": "",
    }
    if any(os.environ.get(key) != expected for key, expected in required_environment.items()):
        raise ValueError("G0 frozen process/thread environment mismatch")
    if torch.cuda.is_available():
        raise ValueError("G0 formal runner forbids a CUDA execution backend")
    return {
        "absolute_python_executable": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "scipy_version": importlib.metadata.version("scipy"),
        "torch_version": torch.__version__,
        "cpu_model": platform.processor() or platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "thread_environment": required_environment,
        "formal_execution_commit": commit,
        "scientific_source_module_git_blob_sha": ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA,
    }


def _validate_binding(binding: FormalRuntimeBinding, *, stage: str) -> dict[str, Any]:
    # gate 01: the admission token is identity-only; the explicit wrapper
    # authorization reference is the separate carrier for the direct grant.
    if (
        not binding.external_user_authorization_reference.strip()
        or binding.formal_authorization_token != FORMAL_AUTHORIZATION_TOKEN
    ):
        raise ValueError("G0 gate_01 external authorization carrier/token mismatch")
    if binding.failed_root_schema_id != FAILED_ROOT_SCHEMA_ID or (
        binding.failed_root_schema_version != FAILED_ROOT_SCHEMA_VERSION
    ) or _SHA256.fullmatch(binding.failed_root_identity) is None:
        raise ValueError("G0 gate_01 failed-root carrier schema/identity mismatch")

    # Reconstruction clarification: a new accepted implementation and its
    # independent alignment must be bound; the old source identity alone is
    # never sufficient admission.
    if (
        ALIGNED_IMPLEMENTATION_COMMIT is None
        or ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA is None
        or ALIGNMENT_STAGE_COMMIT is None
        or _SHA1.fullmatch(ALIGNED_IMPLEMENTATION_COMMIT) is None
        or _SHA1.fullmatch(ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA) is None
        or _SHA1.fullmatch(ALIGNMENT_STAGE_COMMIT) is None
        or ALIGNED_IMPLEMENTATION_COMMIT == ACCEPTED_G0_SOURCE_COMMIT
        or (
            ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA
            == FROZEN_V2_SCIENTIFIC_SOURCE_BLOB_SHA
        )
        or ALIGNMENT_DISPOSITION != "ALIGNED"
    ):
        raise ValueError("G0 gate_02 new implementation/alignment binding is absent")
    if (
        binding.source_commit != FORMAL_INTERFACE_SOURCE_COMMIT
        or binding.accepted_g0_source_commit != ACCEPTED_G0_SOURCE_COMMIT
        or _SHA1.fullmatch(binding.formal_execution_commit) is None
    ):
        raise ValueError("G0 gate_02 frozen source identity mismatch")

    _verify_git_identity(binding.formal_execution_commit)  # gate 03
    if binding.workers != 16 or binding.start_method != "spawn":
        raise ValueError("G0 gate_04 worker process contract mismatch")
    environment = _runtime_environment_manifest(binding.formal_execution_commit)

    if binding.execution_mode not in {"nonformal-preflight", "formal"}:
        raise ValueError("G0 execution mode is not registered")
    if stage == "train" and binding.execution_mode == "nonformal-preflight":
        preflight = binding.run_root
        formal = binding.bound_formal_root
        if binding.nonformal_preflight_root is not None:
            raise ValueError("G0 preflight command must not bind itself as prior preflight")
        if preflight.exists() or formal.exists() or preflight == formal or (
            _paths_nested(preflight, formal) or _paths_nested(formal, preflight)
        ):
            raise ValueError("G0 gate_05 preflight/formal root freshness or separation failed")
    elif binding.execution_mode == "formal":
        if binding.run_root != binding.bound_formal_root:
            raise ValueError("G0 bound formal root differs from --run-root")
        if binding.nonformal_preflight_root is None:
            raise ValueError("G0 formal entry requires the nonformal preflight root")
        if binding.nonformal_preflight_root == binding.run_root or (
            _paths_nested(binding.run_root, binding.nonformal_preflight_root)
            or _paths_nested(binding.nonformal_preflight_root, binding.run_root)
        ):
            raise ValueError("G0 formal/preflight roots are equal or nested")
    else:
        raise ValueError("G0 evaluate/analyze entries require --execution-mode formal")
    return environment


def _run_episode_worker(episode_id: int) -> dict[str, Any]:
    episode = geometry.make_episode_source(int(episode_id))
    runs = {
        key: episode_serialization.episode_run_to_primitive(
            source.run_g0_episode(episode, control=control, cell=cell)
        )
        for key, (control, cell) in zip(_RUN_KEYS, _RUN_IDENTITIES)
    }
    return {
        "episode_id": int(episode_id),
        "source_primitive": episode.to_primitive(),
        "runs": runs,
    }


def _execute_episode_ids(episode_ids: Sequence[int], *, workers: int) -> list[dict[str, Any]]:
    ids = [int(item) for item in episode_ids]
    results: list[dict[str, Any]] = []
    for start in range(0, len(ids), 16):
        wave = ids[start : start + 16]
        context = multiprocessing.get_context("spawn")
        with context.Pool(processes=workers, maxtasksperchild=1) as pool:
            results.extend(pool.map(_run_episode_worker, wave))
    if [item["episode_id"] for item in results] != ids:
        raise RuntimeError("G0 deterministic episode merge order drifted")
    return results


def _episode_bundle(payload: Mapping[str, Any], *, formal: bool, contract_sha256: str) -> dict[str, Any]:
    if set(payload) != {"episode_id", "source_primitive", "runs"}:
        raise ValueError("G0 worker payload schema mismatch")
    episode_id = int(payload["episode_id"])
    source_primitive = payload["source_primitive"]
    if not isinstance(source_primitive, Mapping) or source_primitive.get("sha256") is None:
        raise ValueError("G0 episode source primitive is incomplete")
    if not isinstance(payload["runs"], Mapping) or tuple(payload["runs"]) != _RUN_KEYS:
        raise ValueError("G0 episode run merge order/schema mismatch")
    value = {
        "schema_id": "UAV_G0_EPISODE_BUNDLE",
        "schema_version": 1,
        "formal": formal,
        "contract_sha256": contract_sha256,
        "episode_id": episode_id,
        "source_primitive": dict(source_primitive),
        "source_sha256": source_primitive["sha256"],
        "runs": dict(payload["runs"]),
    }
    return _content_digest(value, "bundle_sha256")


def _load_episode_bundle(path: Path, *, formal: bool, contract_sha256: str) -> tuple[geometry.G0EpisodeSource, dict[tuple[source.Control, source.Cell], source.EpisodeRunEvidence], dict[str, Any]]:
    value = _read_json(path)
    _require_exact_keys(value, _BUNDLE_KEYS, label="episode bundle")
    _validate_content_digest(value, "bundle_sha256")
    episode_id = int(value["episode_id"])
    if (
        value["schema_id"] != "UAV_G0_EPISODE_BUNDLE"
        or value["schema_version"] != 1
        or value["formal"] is not formal
        or value["contract_sha256"] != contract_sha256
        or path.name != f"episode_{episode_id:03d}.json"
        or not isinstance(value["runs"], Mapping)
        or set(value["runs"]) != set(_RUN_KEYS)
    ):
        raise ValueError("G0 episode bundle identity mismatch")
    episode = geometry.make_episode_source(episode_id)
    if episode.to_primitive() != value["source_primitive"] or (
        value["source_sha256"] != value["source_primitive"].get("sha256")
    ):
        raise ValueError("G0 episode source reconstruction mismatch")
    runs = {
        identity: episode_serialization.episode_run_from_primitive(
            value["runs"][key]
        )
        for key, identity in zip(_RUN_KEYS, _RUN_IDENTITIES)
    }
    if any(run.episode_id != episode_id for run in runs.values()):
        raise ValueError("G0 episode run identity mismatch")
    return episode, runs, value


def _validity_to_primitive(record: statistics.EpisodeValidityRecord) -> dict[str, Any]:
    return {item.name: getattr(record, item.name) for item in fields(record)}


def _reconstruct_inventory(root: Path, *, contract_sha256: str, episode_ids: Sequence[int]) -> tuple[list[geometry.G0EpisodeSource], dict[tuple[source.Control, source.Cell], list[source.EpisodeRunEvidence]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, str]]:
    sources: list[geometry.G0EpisodeSource] = []
    rows = {identity: [] for identity in _RUN_IDENTITIES}
    metrics = {key: [] for key in _RUN_KEYS}
    validity: list[dict[str, Any]] = []
    bundle_digests: dict[str, str] = {}
    for episode_id in episode_ids:
        path = root / "episodes" / f"episode_{episode_id:03d}.json"
        episode, episode_runs, bundle = _load_episode_bundle(
            path, formal=True, contract_sha256=contract_sha256
        )
        record, reconstructed_metrics = source.build_episode_validity_record(
            episode, episode_runs
        )
        sources.append(episode)
        validity.append(_validity_to_primitive(record))
        bundle_digests[str(episode_id)] = bundle["bundle_sha256"]
        for key, identity in zip(_RUN_KEYS, _RUN_IDENTITIES):
            rows[identity].append(episode_runs[identity])
            metrics[key].append(reconstructed_metrics[identity].to_primitive())
    return sources, rows, metrics, validity, bundle_digests


def _load_inventory_without_replay(root: Path, *, contract_sha256: str, episode_ids: Sequence[int]) -> tuple[list[geometry.G0EpisodeSource], dict[tuple[source.Control, source.Cell], list[source.EpisodeRunEvidence]], dict[str, list[dict[str, Any]]], dict[str, str]]:
    sources: list[geometry.G0EpisodeSource] = []
    rows = {identity: [] for identity in _RUN_IDENTITIES}
    stored_metrics = {key: [] for key in _RUN_KEYS}
    bundle_digests: dict[str, str] = {}
    for episode_id in episode_ids:
        episode, episode_runs, bundle = _load_episode_bundle(
            root / "episodes" / f"episode_{episode_id:03d}.json",
            formal=True, contract_sha256=contract_sha256,
        )
        sources.append(episode)
        bundle_digests[str(episode_id)] = bundle["bundle_sha256"]
        for key, identity in zip(_RUN_KEYS, _RUN_IDENTITIES):
            run = episode_runs[identity]
            rows[identity].append(run)
            stored_metrics[key].append(run.metrics.to_primitive())
    return sources, rows, stored_metrics, bundle_digests


@contextmanager
def _authoritative_replay_guard(expected_calls: int):
    original = source.run_g0_episode
    calls = 0

    def counted(*args: Any, **kwargs: Any) -> source.EpisodeRunEvidence:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    source.run_g0_episode = counted
    completed = False
    try:
        yield
        completed = True
    finally:
        source.run_g0_episode = original
    if completed and calls != expected_calls:
        raise RuntimeError(
            f"G0 authoritative replay count mismatch: expected {expected_calls}, got {calls}"
        )


@contextmanager
def _capture_authoritative_replay_errors():
    original = source._authoritative_replay_errors
    captured: list[tuple[str, str, tuple[str, ...]]] = []

    def checked(
        episode: geometry.G0EpisodeSource,
        run: source.EpisodeRunEvidence,
    ) -> tuple[str, ...]:
        errors = tuple(original(episode, run))
        captured.append((run.control.value, run.cell.value, errors))
        return errors

    source._authoritative_replay_errors = checked
    try:
        yield captured
    finally:
        source._authoritative_replay_errors = original


def _preflight_semantic_evidence(
    episode: geometry.G0EpisodeSource,
    runs: Mapping[tuple[source.Control, source.Cell], source.EpisodeRunEvidence],
    *,
    source_matches_bundle: bool,
) -> tuple[dict[str, bool], dict[str, int], int, int | None]:
    with _authoritative_replay_guard(6):
        with _capture_authoritative_replay_errors() as replay_rows:
            validity, _metrics = source.build_episode_validity_record(episode, runs)
    if len(replay_rows) != 6 or any(errors for _control, _cell, errors in replay_rows):
        raise ValueError("G0 preflight authoritative replay mismatch")

    oracle_event = runs[(source.Control.ORACLE, source.Cell.EVENT)]
    oracle_no_event = runs[(source.Control.ORACLE, source.Cell.NO_EVENT)]
    event_ready = int(
        oracle_event.controller_evidence["behavioral_replay_certificate"][
            "return_ready_step"
        ]
    )
    no_event_ready = oracle_no_event.controller_evidence[
        "behavioral_replay_certificate"
    ]["return_ready_step"]
    if no_event_ready is not None:
        no_event_ready = int(no_event_ready)
    required_certificates = {
        "source": bool(source_matches_bundle),
        "geometry": bool(
            episode.to_primitive()["geometry"]["geometry_support_certificate"][
                "passed"
            ]
        ),
        "assignment": bool(episode.assignment.passed),
        "tracker": validity.tracker_failures == 0,
        "oracle_safety": validity.oracle_qualification_failures == 0,
        "oracle_EVENT_replay": event_ready == 273,
        "oracle_NO_EVENT_replay": no_event_ready is None,
        "ownership": validity.ownership_violations == 0,
        "permutation": validity.permutation_mismatches == 0,
        "pairing": validity.pairing_mismatches == 0,
        "NO_EVENT_identity": (
            validity.sameinfo_no_event_digest
            == validity.no_reallocation_no_event_digest
        ),
        "metric_arithmetic": validity.metric_reconstruction_mismatches == 0,
    }
    zero_counters = {
        "tracker_failures": validity.tracker_failures,
        "action_support_violations": validity.action_support_violations,
        "ownership_violations": validity.ownership_violations,
        "oracle_qualification_failures": validity.oracle_qualification_failures,
    }
    if not all(required_certificates.values()) or any(zero_counters.values()):
        raise ValueError("G0 preflight certificate/counter failure")
    return required_certificates, zero_counters, event_ready, no_event_ready


@contextmanager
def _capture_analysis_reconstruction():
    original = source.build_episode_validity_record
    captured_metrics = {key: [] for key in _RUN_KEYS}
    captured_validity: list[dict[str, Any]] = []

    def captured(*args: Any, **kwargs: Any):
        record, metrics = original(*args, **kwargs)
        captured_validity.append(_validity_to_primitive(record))
        for key, identity in zip(_RUN_KEYS, _RUN_IDENTITIES):
            captured_metrics[key].append(metrics[identity].to_primitive())
        return record, metrics

    source.build_episode_validity_record = captured
    try:
        yield captured_metrics, captured_validity
    finally:
        source.build_episode_validity_record = original


@contextmanager
def _reuse_bootstrap_index_plan(index_plan: np.ndarray):
    """Make source-side plan validation reuse the one coordinator matrix."""

    original = statistics.make_bootstrap_index_plan
    plan = np.asarray(index_plan, dtype=np.int64)
    calls = 0

    def reused() -> np.ndarray:
        nonlocal calls
        calls += 1
        return plan

    statistics.make_bootstrap_index_plan = reused
    completed = False
    try:
        yield
        completed = True
    finally:
        statistics.make_bootstrap_index_plan = original
    if completed and calls != 1:
        raise RuntimeError(
            f"G0 source bootstrap-plan validation count mismatch: expected 1, got {calls}"
        )


def _require_evaluation_reconstruction(
    evaluation: Mapping[str, Any],
    metric_rows: Mapping[str, Any],
    validity_records: Sequence[Mapping[str, Any]],
    bundle_digests: Mapping[str, str],
) -> None:
    if (
        dict(metric_rows) != evaluation["metric_rows"]
        or list(validity_records) != evaluation["validity_records"]
        or dict(bundle_digests) != evaluation["episode_bundle_sha256_by_id"]
    ):
        raise ValueError("G0 gate_10 independent reconstruction differs from evaluation")


def _assert_no_forbidden_artifacts(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("G0 artifact root contains a forbidden symlink")
        if path.is_file() and (
            path.suffix in {".pt", ".pth", ".ckpt"} or path.name.endswith(".tmp")
        ):
            raise ValueError("G0 artifact root contains checkpoint/temporary evidence")
    if (root / "checkpoints").exists():
        raise ValueError("G0 artifact root contains a checkpoint directory")


def _file_inventory(root: Path) -> set[str]:
    _assert_no_forbidden_artifacts(root)
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file()
    }


def _write_failed_root(
    root: Path,
    binding: FormalRuntimeBinding,
    *,
    gate: str,
    error: BaseException,
    current_attempt_terminal: bool = False,
) -> None:
    if not root.exists():
        return
    # Previously COMPLETE and already-failed roots are immutable. A terminal
    # written by this attempt but rejected by its final self-check is not valid
    # terminal evidence and must not survive as an apparently COMPLETE root.
    terminal_path = root / "terminal_manifest.json"
    if (root / "failed_root.json").exists():
        return
    if terminal_path.exists():
        if not current_attempt_terminal:
            return
        terminal_path.unlink()
    value = {
        "schema_id": binding.failed_root_schema_id,
        "schema_version": binding.failed_root_schema_version,
        "failed_root_identity": binding.failed_root_identity,
        "status": "TERMINAL_FAILED",
        "formal": binding.execution_mode == "formal",
        "failed_gate": gate,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "result_branch": None,
        "scientific_update": False,
        "runtime_binding": binding.to_primitive(),
    }
    _write_json(root / "failed_root.json", _content_digest(value, "content_sha256"))


def _preflight_identity(binding: FormalRuntimeBinding) -> dict[str, Any]:
    return {
        "source_commit": binding.source_commit,
        "accepted_g0_source_commit": binding.accepted_g0_source_commit,
        "formal_execution_commit": binding.formal_execution_commit,
        "formal_authorization_token": binding.formal_authorization_token,
        "external_user_authorization_reference": binding.external_user_authorization_reference,
        "bound_formal_root": str(binding.bound_formal_root),
        "failed_root_identity": binding.failed_root_identity,
        "failed_root_schema_id": binding.failed_root_schema_id,
        "failed_root_schema_version": binding.failed_root_schema_version,
        "workers": binding.workers,
        "start_method": binding.start_method,
        "aligned_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "aligned_scientific_source_blob_sha": ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA,
        "alignment_stage_commit": ALIGNMENT_STAGE_COMMIT,
        "alignment_disposition": ALIGNMENT_DISPOSITION,
    }


_PREFLIGHT_TERMINAL_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "episode_bundle_sha256", "preflight_result_sha256", "exact_file_inventory",
        "result_branch", "scientific_conclusion", "content_sha256",
    }
)
_FORMAL_TERMINAL_KEYS = frozenset(
    {
        "schema_id", "schema_version", "status", "formal", "contract_sha256",
        "source_manifest_sha256", "evaluation_manifest_sha256",
        "analysis_result_sha256", "episode_bundle_sha256_by_id",
        "exact_file_inventory", "result_branch", "content_sha256",
    }
)


def _validate_preflight(
    root: Path,
    binding: FormalRuntimeBinding,
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError("G0 gate_05 nonformal preflight root is absent")
    expected = {
        "preflight_contract.json", "episodes/episode_000.json",
        "preflight_result.json", "terminal_manifest.json",
    }
    if _file_inventory(root) != expected:
        raise ValueError("G0 gate_06 preflight terminal inventory mismatch")
    contract = _read_json(root / "preflight_contract.json")
    _require_exact_keys(contract, _PREFLIGHT_CONTRACT_KEYS, label="preflight contract")
    _validate_content_digest(contract, "content_sha256")
    if (
        contract["schema_id"] != "UAV_G0_NONFORMAL_PREFLIGHT_CONTRACT"
        or contract["schema_version"] != 1
        or contract["status"] != "COMPLETE"
        or contract["formal"] is not False
        or contract["frozen_records"] != _load_frozen_records()
        or contract["environment_manifest"] != environment
    ):
        raise ValueError("G0 gate_06 preflight contract identity mismatch")
    preflight_binding = contract["runtime_binding"]
    _require_runtime_binding_schema(preflight_binding)
    _require_preflight_runtime_path_binding(preflight_binding, root)
    for key, expected_value in _preflight_identity(binding).items():
        actual = preflight_binding.get("carrier", {}).get(key, object()) if key in {
            "external_user_authorization_reference", "bound_formal_root",
            "failed_root_identity", "failed_root_schema_id", "failed_root_schema_version",
        } else preflight_binding.get(key, object())
        if actual != expected_value:
            raise ValueError("G0 gate_06 preflight runtime identity mismatch")
    bundle_path = root / "episodes" / "episode_000.json"
    episode, runs, bundle = _load_episode_bundle(
        bundle_path, formal=False, contract_sha256=contract["content_sha256"]
    )
    result = _read_json(root / "preflight_result.json")
    _require_exact_keys(result, _PREFLIGHT_RESULT_KEYS, label="preflight result")
    _validate_content_digest(result, "content_sha256")
    if (
        result["status"] != "COMPLETE" or result["formal"] is not False
        or result["schema_id"] != "UAV_G0_NONFORMAL_PREFLIGHT_RESULT"
        or result["schema_version"] != 1
        or result["contract_sha256"] != contract["content_sha256"]
        or result["episode_bundle_sha256"] != bundle["bundle_sha256"]
        or result["episode_id"] != 0 or result["run_count"] != 6
        or result["primary_real_simulator_steps"] != 3000
        or result["validation_replay_steps"] != 3000
        or result["scientific_iteration_cost"] != 0
        or result["result_branch"] is not None
        or result["scientific_conclusion"] is not None
        or result["ORACLE_STATUS"] is not None
        or result["SAMEINFO_STATUS"] is not None
        or result["CAUSAL_STATUS"] is not None
        or result["oracle_event_return_ready_step"] != 273
        or result["oracle_no_event_return_ready_step"] is not None
        or set(result["required_certificates"]) != set(_REQUIRED_CERTIFICATE_KEYS)
        or set(result["zero_counters"]) != set(_ZERO_COUNTER_KEYS)
        or not all(result["required_certificates"].values())
        or any(int(item) != 0 for item in result["zero_counters"].values())
    ):
        raise ValueError("G0 gate_06 preflight operational result mismatch")
    terminal = _read_json(root / "terminal_manifest.json")
    _require_exact_keys(terminal, _PREFLIGHT_TERMINAL_KEYS, label="preflight terminal manifest")
    _validate_content_digest(terminal, "content_sha256")
    expected_refs = {
        name: _digest(root / name)
        for name in expected if name != "terminal_manifest.json"
    }
    if (
        terminal["schema_id"] != "UAV_G0_NONFORMAL_PREFLIGHT_TERMINAL_MANIFEST"
        or terminal["schema_version"] != 1 or terminal["status"] != "COMPLETE"
        or terminal["formal"] is not False or terminal["result_branch"] is not None
        or terminal["scientific_conclusion"] is not None
        or terminal["contract_sha256"] != contract["content_sha256"]
        or terminal["episode_bundle_sha256"] != bundle["bundle_sha256"]
        or terminal["preflight_result_sha256"] != result["content_sha256"]
        or terminal["exact_file_inventory"] != expected_refs
    ):
        raise ValueError("G0 gate_06 preflight terminal manifest mismatch")
    return terminal


def _validate_preflight_admission(
    root: Path,
    binding: FormalRuntimeBinding,
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the gate-06 carrier without importing preflight science rows.

    The preflight command already spent its registered six primary runs and six
    authoritative validation replays.  Formal admission may see only the
    identity/operational-pass projection, so it hashes the episode bundle but
    neither deserializes EpisodeRunEvidence nor invokes the environment.
    """

    if not root.is_dir():
        raise ValueError("G0 gate_05 nonformal preflight root is absent")
    expected = {
        "preflight_contract.json",
        "episodes/episode_000.json",
        "preflight_result.json",
        "terminal_manifest.json",
    }
    if _file_inventory(root) != expected:
        raise ValueError("G0 gate_06 preflight terminal inventory mismatch")

    contract = _read_json(root / "preflight_contract.json")
    _require_exact_keys(contract, _PREFLIGHT_CONTRACT_KEYS, label="preflight contract")
    _validate_content_digest(contract, "content_sha256")
    if (
        contract["schema_id"] != "UAV_G0_NONFORMAL_PREFLIGHT_CONTRACT"
        or contract["schema_version"] != 1
        or contract["status"] != "COMPLETE"
        or contract["formal"] is not False
        or contract["frozen_records"] != _load_frozen_records()
        or contract["environment_manifest"] != environment
    ):
        raise ValueError("G0 gate_06 preflight contract identity mismatch")
    preflight_binding = contract["runtime_binding"]
    _require_runtime_binding_schema(preflight_binding)
    _require_preflight_runtime_path_binding(preflight_binding, root)
    for key, expected_value in _preflight_identity(binding).items():
        actual = (
            preflight_binding.get("carrier", {}).get(key, object())
            if key
            in {
                "external_user_authorization_reference",
                "bound_formal_root",
                "failed_root_identity",
                "failed_root_schema_id",
                "failed_root_schema_version",
            }
            else preflight_binding.get(key, object())
        )
        if actual != expected_value:
            raise ValueError("G0 gate_06 preflight runtime identity mismatch")

    result = _read_json(root / "preflight_result.json")
    _require_exact_keys(result, _PREFLIGHT_RESULT_KEYS, label="preflight result")
    _validate_content_digest(result, "content_sha256")
    if (
        result["schema_id"] != "UAV_G0_NONFORMAL_PREFLIGHT_RESULT"
        or result["schema_version"] != 1
        or result["status"] != "COMPLETE"
        or result["formal"] is not False
        or result["contract_sha256"] != contract["content_sha256"]
        or not isinstance(result["episode_bundle_sha256"], str)
        or _SHA256.fullmatch(result["episode_bundle_sha256"]) is None
        or result["episode_id"] != 0
        or result["run_count"] != 6
        or result["primary_real_simulator_steps"] != 3000
        or result["validation_replay_steps"] != 3000
        or result["scientific_iteration_cost"] != 0
        or result["result_branch"] is not None
        or result["scientific_conclusion"] is not None
        or result["ORACLE_STATUS"] is not None
        or result["SAMEINFO_STATUS"] is not None
        or result["CAUSAL_STATUS"] is not None
        or result["oracle_event_return_ready_step"] != 273
        or result["oracle_no_event_return_ready_step"] is not None
        or set(result["required_certificates"]) != set(_REQUIRED_CERTIFICATE_KEYS)
        or set(result["zero_counters"]) != set(_ZERO_COUNTER_KEYS)
        or not all(result["required_certificates"].values())
        or any(int(item) != 0 for item in result["zero_counters"].values())
    ):
        raise ValueError("G0 gate_06 preflight operational result mismatch")

    terminal = _read_json(root / "terminal_manifest.json")
    _require_exact_keys(
        terminal,
        _PREFLIGHT_TERMINAL_KEYS,
        label="preflight terminal manifest",
    )
    _validate_content_digest(terminal, "content_sha256")
    expected_refs = {
        name: _digest(root / name)
        for name in expected
        if name != "terminal_manifest.json"
    }
    if (
        terminal["schema_id"]
        != "UAV_G0_NONFORMAL_PREFLIGHT_TERMINAL_MANIFEST"
        or terminal["schema_version"] != 1
        or terminal["status"] != "COMPLETE"
        or terminal["formal"] is not False
        or terminal["result_branch"] is not None
        or terminal["scientific_conclusion"] is not None
        or terminal["contract_sha256"] != contract["content_sha256"]
        or terminal["episode_bundle_sha256"] != result["episode_bundle_sha256"]
        or terminal["preflight_result_sha256"] != result["content_sha256"]
        or terminal["exact_file_inventory"] != expected_refs
    ):
        raise ValueError("G0 gate_06 preflight terminal manifest mismatch")
    return terminal


def scientific_train(*, binding: FormalRuntimeBinding) -> dict[str, Any]:
    environment = _validate_binding(binding, stage="train")
    root = binding.run_root
    frozen = _load_frozen_records()
    if binding.execution_mode == "nonformal-preflight":
        root.mkdir(parents=True, exist_ok=False)
        terminal_written = False
        try:
            contract = _content_digest(
                {
                    "schema_id": "UAV_G0_NONFORMAL_PREFLIGHT_CONTRACT",
                    "schema_version": 1, "status": "COMPLETE", "formal": False,
                    "frozen_records": frozen, "runtime_binding": binding.to_primitive(),
                    "environment_manifest": environment,
                },
                "content_sha256",
            )
            _require_exact_keys(contract, _PREFLIGHT_CONTRACT_KEYS, label="preflight contract")
            _write_json(root / "preflight_contract.json", contract)
            payload = _execute_episode_ids((0,), workers=binding.workers)[0]
            bundle = _episode_bundle(
                payload, formal=False, contract_sha256=contract["content_sha256"]
            )
            bundle_path = root / "episodes" / "episode_000.json"
            _write_json(bundle_path, bundle)
            episode, runs, _ = _load_episode_bundle(
                bundle_path, formal=False, contract_sha256=contract["content_sha256"]
            )
            (
                required_certificates,
                zero_counters,
                event_ready,
                no_event_ready,
            ) = _preflight_semantic_evidence(
                episode,
                runs,
                source_matches_bundle=(
                    bundle["source_sha256"] == episode.to_primitive()["sha256"]
                ),
            )
            result = _content_digest(
                {
                    "schema_id": "UAV_G0_NONFORMAL_PREFLIGHT_RESULT",
                    "schema_version": 1, "status": "COMPLETE", "formal": False,
                    "contract_sha256": contract["content_sha256"],
                    "episode_bundle_sha256": bundle["bundle_sha256"],
                    "episode_id": 0, "run_count": 6,
                    "primary_real_simulator_steps": 3000,
                    "validation_replay_steps": 3000,
                    "required_certificates": required_certificates,
                    "zero_counters": zero_counters,
                    "oracle_event_return_ready_step": event_ready,
                    "oracle_no_event_return_ready_step": no_event_ready,
                    "ORACLE_STATUS": None, "SAMEINFO_STATUS": None,
                    "CAUSAL_STATUS": None, "result_branch": None,
                    "scientific_conclusion": None, "scientific_iteration_cost": 0,
                },
                "content_sha256",
            )
            _require_exact_keys(result, _PREFLIGHT_RESULT_KEYS, label="preflight result")
            _write_json(root / "preflight_result.json", result)
            refs = {
                name: _digest(root / name)
                for name in (
                    "preflight_contract.json", "episodes/episode_000.json",
                    "preflight_result.json",
                )
            }
            terminal = _content_digest(
                {
                    "schema_id": "UAV_G0_NONFORMAL_PREFLIGHT_TERMINAL_MANIFEST",
                    "schema_version": 1, "status": "COMPLETE", "formal": False,
                    "contract_sha256": contract["content_sha256"],
                    "episode_bundle_sha256": bundle["bundle_sha256"],
                    "preflight_result_sha256": result["content_sha256"],
                    "exact_file_inventory": refs, "result_branch": None,
                    "scientific_conclusion": None,
                },
                "content_sha256",
            )
            _write_json(root / "terminal_manifest.json", terminal)
            terminal_written = True
            _validate_preflight(root, binding, environment)
            return terminal
        except BaseException as error:
            _write_failed_root(
                root,
                binding,
                gate="gate_05",
                error=error,
                current_attempt_terminal=terminal_written,
            )
            raise

    assert binding.nonformal_preflight_root is not None
    preflight_terminal = _validate_preflight_admission(
        binding.nonformal_preflight_root,
        binding,
        environment,
    )
    if root.exists():
        raise ValueError("G0 gate_07 formal root must be fresh and absent")
    root.mkdir(parents=True, exist_ok=False)
    try:
        contract = _content_digest(
            {
                "schema_id": "UAV_G0_FORMAL_CONTRACT", "schema_version": 1,
                "status": "COMPLETE", "formal": True, "frozen_records": frozen,
                "runtime_binding": binding.to_primitive(),
                "environment_manifest": environment,
                "preflight_terminal_manifest_sha256": _digest(
                    binding.nonformal_preflight_root / "terminal_manifest.json"
                ),
            },
            "content_sha256",
        )
        _require_exact_keys(contract, _FORMAL_CONTRACT_KEYS, label="formal contract")
        _write_json(root / "formal_contract.json", contract)
        payloads = _execute_episode_ids(tuple(range(128)), workers=binding.workers)
        references: dict[str, str] = {}
        for payload in payloads:
            bundle = _episode_bundle(
                payload, formal=True, contract_sha256=contract["content_sha256"]
            )
            episode_id = int(bundle["episode_id"])
            path = root / "episodes" / f"episode_{episode_id:03d}.json"
            _write_json(path, bundle)
            references[str(episode_id)] = bundle["bundle_sha256"]
        manifest = _content_digest(
            {
                "schema_id": "UAV_G0_FORMAL_SOURCE_MANIFEST", "schema_version": 1,
                "status": "COMPLETE", "formal": True,
                "contract_sha256": contract["content_sha256"],
                "source_identities": {
                    "algorithm_id": ALGORITHM_ID, "source_id": SOURCE_ID,
                    "source_schema_version": SCHEMA_VERSION,
                    "scientific_source_blob_sha": ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA,
                },
                "execution_identity": _preflight_identity(binding),
                "environment_identity": hashlib.sha256(_canonical_bytes(environment)).hexdigest(),
                "episode_ids": list(range(128)),
                "control_order": [item.value for item in (
                    source.Control.ORACLE, source.Control.SAME_INFORMATION,
                    source.Control.NO_REALLOCATION,
                )],
                "cell_order": [source.Cell.EVENT.value, source.Cell.NO_EVENT.value],
                "run_count": 768, "simulator_step_count": 384000,
                "episode_bundle_references_and_sha256_values": references,
            },
            "content_sha256",
        )
        _require_exact_keys(manifest, _SOURCE_MANIFEST_FORMAL_KEYS, label="formal source manifest")
        _write_json(root / "source_manifest.json", manifest)
        expected = {"formal_contract.json", "source_manifest.json"} | {
            f"episodes/episode_{episode_id:03d}.json" for episode_id in range(128)
        }
        if _file_inventory(root) != expected:
            raise RuntimeError("G0 gate_08 formal train artifact inventory mismatch")
        return manifest
    except BaseException as error:
        _write_failed_root(root, binding, gate="gate_08", error=error)
        raise


def _load_formal_train(root: Path, binding: FormalRuntimeBinding, environment: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = _read_json(root / "formal_contract.json")
    _require_exact_keys(contract, _FORMAL_CONTRACT_KEYS, label="formal contract")
    _validate_content_digest(contract, "content_sha256")
    if (
        contract["schema_id"] != "UAV_G0_FORMAL_CONTRACT"
        or contract["schema_version"] != 1 or contract["status"] != "COMPLETE"
        or contract["formal"] is not True
        or contract["frozen_records"] != _load_frozen_records()
        or contract["runtime_binding"] != binding.to_primitive()
        or contract["environment_manifest"] != environment
    ):
        raise ValueError("G0 formal contract reconstruction mismatch")
    assert binding.nonformal_preflight_root is not None
    preflight = _validate_preflight_admission(
        binding.nonformal_preflight_root,
        binding,
        environment,
    )
    if contract["preflight_terminal_manifest_sha256"] != _digest(
        binding.nonformal_preflight_root / "terminal_manifest.json"
    ):
        raise ValueError("G0 formal/preflight terminal binding mismatch")
    manifest = _read_json(root / "source_manifest.json")
    _require_exact_keys(manifest, _SOURCE_MANIFEST_FORMAL_KEYS, label="formal source manifest")
    _validate_content_digest(manifest, "content_sha256")
    expected_refs = {str(item): None for item in range(128)}
    expected_source_identities = {
        "algorithm_id": ALGORITHM_ID, "source_id": SOURCE_ID,
        "source_schema_version": SCHEMA_VERSION,
        "scientific_source_blob_sha": ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA,
    }
    expected_controls = [
        source.Control.ORACLE.value, source.Control.SAME_INFORMATION.value,
        source.Control.NO_REALLOCATION.value,
    ]
    expected_cells = [source.Cell.EVENT.value, source.Cell.NO_EVENT.value]
    if (
        manifest["status"] != "COMPLETE" or manifest["formal"] is not True
        or manifest["contract_sha256"] != contract["content_sha256"]
        or manifest["episode_ids"] != list(range(128))
        or manifest["source_identities"] != expected_source_identities
        or manifest["execution_identity"] != _preflight_identity(binding)
        or manifest["environment_identity"] != hashlib.sha256(
            _canonical_bytes(environment)
        ).hexdigest()
        or manifest["control_order"] != expected_controls
        or manifest["cell_order"] != expected_cells
        or manifest["run_count"] != 768 or manifest["simulator_step_count"] != 384000
        or set(manifest["episode_bundle_references_and_sha256_values"]) != set(expected_refs)
    ):
        raise ValueError("G0 formal source manifest identity mismatch")
    for episode_id in range(128):
        _, _, bundle = _load_episode_bundle(
            root / "episodes" / f"episode_{episode_id:03d}.json",
            formal=True, contract_sha256=contract["content_sha256"],
        )
        if manifest["episode_bundle_references_and_sha256_values"][str(episode_id)] != bundle["bundle_sha256"]:
            raise ValueError("G0 source manifest episode digest mismatch")
    return contract, manifest


def scientific_evaluate(*, binding: FormalRuntimeBinding) -> dict[str, Any]:
    environment = _validate_binding(binding, stage="evaluate")
    root = binding.run_root
    if not root.is_dir():
        raise ValueError("G0 formal root is absent at evaluate")
    try:
        contract, manifest = _load_formal_train(root, binding, environment)
        expected = {"formal_contract.json", "source_manifest.json"} | {
            f"episodes/episode_{episode_id:03d}.json" for episode_id in range(128)
        }
        if _file_inventory(root) != expected:
            raise ValueError("G0 gate_09 pre-evaluate inventory mismatch")
        with _authoritative_replay_guard(768):
            with _capture_authoritative_replay_errors() as replay_rows:
                (
                    _sources,
                    _rows,
                    metric_rows,
                    validity,
                    bundle_digests,
                ) = _reconstruct_inventory(
                    root,
                    contract_sha256=contract["content_sha256"],
                    episode_ids=range(128),
                )
        if len(replay_rows) != 768 or any(
            errors for _control, _cell, errors in replay_rows
        ):
            raise ValueError("G0 gate_09 authoritative replay mismatch")
        plan = statistics.make_bootstrap_index_plan()
        value = _content_digest(
            {
                "schema_id": "UAV_G0_FORMAL_EVALUATION_MANIFEST",
                "schema_version": 1, "status": "COMPLETE", "formal": True,
                "contract_sha256": contract["content_sha256"],
                "source_manifest_sha256": manifest["content_sha256"],
                "episode_bundle_sha256_by_id": bundle_digests,
                "metric_rows": metric_rows, "validity_records": validity,
                "bootstrap_generator": BOOTSTRAP_GENERATOR,
                "bootstrap_seed": statistics.BOOTSTRAP_SEED,
                "bootstrap_shape": [statistics.BOOTSTRAP_RESAMPLES, len(statistics.EPISODE_IDS)],
                "bootstrap_index_sha256": hashlib.sha256(
                    np.asarray(plan, dtype=np.int64).tobytes(order="C")
                ).hexdigest(),
                "real_simulator_steps": 384000, "optimizer_steps": 0,
                "result_branch": None,
            },
            "evaluation_sha256",
        )
        _require_exact_keys(value, _EVALUATION_FORMAL_KEYS, label="formal evaluation manifest")
        _write_json(root / "evaluation_manifest.json", value)
        if _file_inventory(root) != expected | {"evaluation_manifest.json"}:
            raise ValueError("G0 gate_09 post-evaluate artifact inventory mismatch")
        return value
    except BaseException as error:
        _write_failed_root(root, binding, gate="gate_09", error=error)
        raise


def _load_formal_evaluation(
    root: Path,
    contract: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    index_plan: np.ndarray,
) -> dict[str, Any]:
    value = _read_json(root / "evaluation_manifest.json")
    _require_exact_keys(value, _EVALUATION_FORMAL_KEYS, label="formal evaluation manifest")
    _validate_content_digest(value, "evaluation_sha256")
    expected_bootstrap_sha = hashlib.sha256(
        np.asarray(index_plan, dtype=np.int64).tobytes(order="C")
    ).hexdigest()
    if (
        value["schema_id"] != "UAV_G0_FORMAL_EVALUATION_MANIFEST"
        or value["schema_version"] != 1 or value["status"] != "COMPLETE"
        or value["formal"] is not True
        or value["contract_sha256"] != contract["content_sha256"]
        or value["source_manifest_sha256"] != manifest["content_sha256"]
        or value["result_branch"] is not None or value["optimizer_steps"] != 0
        or value["real_simulator_steps"] != 384000
        or value["bootstrap_generator"] != BOOTSTRAP_GENERATOR
        or value["bootstrap_seed"] != statistics.BOOTSTRAP_SEED
        or value["bootstrap_shape"] != [statistics.BOOTSTRAP_RESAMPLES, 128]
        or value["bootstrap_index_sha256"] != expected_bootstrap_sha
    ):
        raise ValueError("G0 formal evaluation manifest identity mismatch")
    return value


def scientific_analyze(*, binding: FormalRuntimeBinding) -> dict[str, Any]:
    environment = _validate_binding(binding, stage="analyze")
    root = binding.run_root
    if not root.is_dir():
        raise ValueError("G0 formal root is absent at analyze")
    failed_gate = "gate_10"
    terminal_written = False
    try:
        contract, manifest = _load_formal_train(root, binding, environment)
        analysis_plan = statistics.make_bootstrap_index_plan()
        evaluation = _load_formal_evaluation(
            root,
            contract,
            manifest,
            index_plan=analysis_plan,
        )
        expected = {"formal_contract.json", "source_manifest.json", "evaluation_manifest.json"} | {
            f"episodes/episode_{episode_id:03d}.json" for episode_id in range(128)
        }
        if _file_inventory(root) != expected:
            raise ValueError("G0 gate_10 pre-analyze inventory mismatch")
        sources, rows, stored_metric_rows, bundle_digests = _load_inventory_without_replay(
            root, contract_sha256=contract["content_sha256"], episode_ids=range(128)
        )
        if (
            stored_metric_rows != evaluation["metric_rows"]
            or bundle_digests != evaluation["episode_bundle_sha256_by_id"]
        ):
            raise ValueError("G0 gate_10 independent reconstruction differs from evaluation")
        with _authoritative_replay_guard(768):
            with _capture_authoritative_replay_errors() as replay_rows:
                with _capture_analysis_reconstruction() as (
                    reconstructed_metrics,
                    reconstructed_validity,
                ):
                    with _reuse_bootstrap_index_plan(analysis_plan):
                        analysis = source.build_analysis_evidence(
                            sources,
                            rows,
                            index_plan=analysis_plan,
                        )
        if len(replay_rows) != 768 or any(
            errors for _control, _cell, errors in replay_rows
        ):
            raise ValueError("G0 gate_10 authoritative replay mismatch")
        _require_evaluation_reconstruction(
            evaluation,
            reconstructed_metrics,
            reconstructed_validity,
            bundle_digests,
        )
        value = _content_digest(
            {
                "schema_id": "UAV_G0_FORMAL_ANALYSIS_RESULT", "schema_version": 1,
                "status": "COMPLETE", "formal": True,
                "contract_sha256": contract["content_sha256"],
                "source_manifest_sha256": manifest["content_sha256"],
                "evaluation_manifest_sha256": evaluation["evaluation_sha256"],
                "continuous": analysis["continuous"], "binary": analysis["binary"],
                "bootstrap_seed": analysis["bootstrap_seed"],
                "bootstrap_resamples": analysis["bootstrap_resamples"],
                "bootstrap_index_sha256": analysis["bootstrap_index_sha256"],
                "quantile_rule": analysis["quantile_rule"], "valid": analysis["valid"],
                "validity_errors": analysis["validity_errors"],
                "ORACLE_STATUS": analysis["ORACLE_STATUS"],
                "SAMEINFO_STATUS": analysis["SAMEINFO_STATUS"],
                "CAUSAL_STATUS": analysis["CAUSAL_STATUS"],
                "first_match_order": analysis["first_match_order"],
                "result_branch": analysis["result_branch"], "claim_scope": CLAIM_SCOPE,
                "scientific_iteration_cost": 1,
            },
            "analysis_sha256",
        )
        _require_exact_keys(value, _ANALYSIS_FORMAL_KEYS, label="formal analysis result")
        _write_json(root / "analysis_result.json", value)
        failed_gate = "gate_11"
        expected_terminal_refs = {
            "formal_contract.json",
            "source_manifest.json",
            "evaluation_manifest.json",
            "analysis_result.json",
        } | {
            f"episodes/episode_{episode_id:03d}.json"
            for episode_id in range(128)
        }
        refs = {
            path.relative_to(root).as_posix(): _digest(path)
            for path in root.rglob("*") if path.is_file()
        }
        if set(refs) != expected_terminal_refs:
            raise ValueError("G0 gate_11 terminal inventory excluding self is not exact")
        terminal = _content_digest(
            {
                "schema_id": "UAV_G0_FORMAL_TERMINAL_MANIFEST", "schema_version": 1,
                "status": "COMPLETE", "formal": True,
                "contract_sha256": contract["content_sha256"],
                "source_manifest_sha256": manifest["content_sha256"],
                "evaluation_manifest_sha256": evaluation["evaluation_sha256"],
                "analysis_result_sha256": value["analysis_sha256"],
                "episode_bundle_sha256_by_id": bundle_digests,
                "exact_file_inventory": refs, "result_branch": value["result_branch"],
            },
            "content_sha256",
        )
        _require_exact_keys(terminal, _FORMAL_TERMINAL_KEYS, label="formal terminal manifest")
        _write_json(root / "terminal_manifest.json", terminal)
        terminal_written = True
        if _file_inventory(root) != expected_terminal_refs | {"terminal_manifest.json"}:
            raise ValueError("G0 gate_11 formal terminal inventory is not exact")
        return terminal
    except BaseException as error:
        _write_failed_root(
            root,
            binding,
            gate=failed_gate,
            error=error,
            current_attempt_terminal=terminal_written,
        )
        raise


def _result_binding_from_args(args: argparse.Namespace) -> FormalRuntimeBinding:
    run_root = _absolute_path(args.run_root, label="run root")
    bound_formal_root = _absolute_path(args.bound_formal_root, label="bound formal root")
    preflight_root = (
        None if args.nonformal_preflight_root is None
        else _absolute_path(args.nonformal_preflight_root, label="nonformal preflight root")
    )
    return FormalRuntimeBinding(
        execution_mode=args.execution_mode,
        run_root=run_root,
        nonformal_preflight_root=preflight_root,
        bound_formal_root=bound_formal_root,
        source_commit=args.source_commit,
        accepted_g0_source_commit=args.accepted_g0_source_commit,
        formal_execution_commit=args.formal_execution_commit,
        formal_authorization_token=args.formal_authorization_token,
        external_user_authorization_reference=args.external_user_authorization_reference,
        failed_root_identity=args.failed_root_identity,
        failed_root_schema_id=args.failed_root_schema_id,
        failed_root_schema_version=args.failed_root_schema_version,
        workers=args.workers,
        start_method=args.start_method,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="stage", required=True)
    for stage in ("train", "evaluate", "analyze"):
        entry = subparsers.add_parser(stage)
        entry.add_argument("--execution-mode", choices=("nonformal-preflight", "formal"), required=True)
        entry.add_argument("--run-root", type=Path, required=True)
        entry.add_argument("--nonformal-preflight-root", type=Path)
        entry.add_argument("--source-commit", required=True)
        entry.add_argument("--accepted-g0-source-commit", required=True)
        entry.add_argument("--formal-execution-commit", required=True)
        entry.add_argument("--formal-authorization-token", required=True)
        entry.add_argument("--external-user-authorization-reference", required=True)
        entry.add_argument("--bound-formal-root", type=Path, required=True)
        entry.add_argument("--failed-root-identity", required=True)
        entry.add_argument("--failed-root-schema-id", required=True)
        entry.add_argument("--failed-root-schema-version", type=int, required=True)
        entry.add_argument("--workers", type=int, required=True)
        entry.add_argument("--start-method", required=True)
    for stage in (
        "readiness-smoke", "readiness-train", "readiness-validate",
        "readiness-reload", "readiness-evaluate", "readiness-analyze",
    ):
        entry = subparsers.add_parser(stage)
        entry.add_argument("--run-root", type=Path, required=True)
        if stage in {"readiness-smoke", "readiness-train"}:
            entry.add_argument("--source-commit", required=True)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.stage == "readiness-smoke":
        readiness_interface_smoke(source_commit=args.source_commit)
    elif args.stage == "readiness-train":
        readiness_train(run_root=args.run_root, source_commit=args.source_commit)
    elif args.stage == "readiness-validate":
        readiness_validate(run_root=args.run_root)
    elif args.stage == "readiness-reload":
        readiness_reload(run_root=args.run_root)
    elif args.stage == "readiness-evaluate":
        readiness_evaluate(run_root=args.run_root)
    elif args.stage == "readiness-analyze":
        readiness_analyze(run_root=args.run_root)
    elif args.stage == "train":
        scientific_train(binding=_result_binding_from_args(args))
    elif args.stage == "evaluate":
        scientific_evaluate(binding=_result_binding_from_args(args))
    else:
        scientific_analyze(binding=_result_binding_from_args(args))


if __name__ == "__main__":
    main()
