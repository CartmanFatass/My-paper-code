"""Proof-only runner and future fail-closed interface for UAV G0.

The accepted G0 contract explicitly leaves formal execution unauthorized.
Accordingly, only the six candidate-bound readiness stages are executable in
this source revision.  They materialize synthetic/structural technical proof
artifacts with zero scientific environment transitions and no scientific
result.  ``source``, ``evaluate`` and ``analyze`` are present as compatibility
surfaces but fail before creating or mutating a run root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_env_name in _THREAD_ENV_NAMES:
    os.environ[_thread_env_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from ha_ctse_process import uav_source_identifiability_g0 as source


SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = source.ALGORITHM_ID
SOURCE_ID = source.SOURCE_ID
FORMAL_EXECUTION_AUTHORIZED = source.FORMAL_EXECUTION_AUTHORIZED
DESIGN_DISPOSITION = source.DESIGN_DISPOSITION
ORACLE_SAFETY_DISPOSITION = source.ORACLE_SAFETY_DISPOSITION
REPLAY_DISPOSITION = source.REPLAY_DISPOSITION
RETURN_READY_STEP_DISPOSITION = source.RETURN_READY_STEP_DISPOSITION
CLAIM_SCOPE = "SOURCE_IDENTIFIABILITY_G0_ONLY"
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
    "envs.pettingzoo.scenario7_energy_aware.UAVEnergyAwareRelayEnv|S7-S1"
)

SOURCE_MANIFEST = "source_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
SOURCE_PROOF = "proof/episode_0_source.json"
ORACLE_PROOF = "proof/oracle_qualification.json"
TRACKER_PROOF = "proof/common_tracker_qualification.json"
ORACLE_SAFETY_LEDGER_PROOF = "proof/oracle_safety_ledger.json"
ORACLE_BEHAVIORAL_REPLAY_PROOF = "proof/oracle_behavioral_replay.json"

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
    temporary.write_bytes(_canonical_bytes(dict(value)) + b"\n")
    temporary.replace(path)


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
    episode = source.make_episode_source(0)
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
            "source",
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
        "bootstrap_seed": source.BOOTSTRAP_SEED,
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


def _build_tracker_proof(episode: source.G0EpisodeSource) -> dict[str, Any]:
    physical = np.concatenate(
        (
            episode.geometry.physical_xy,
            np.full((source.PHYSICAL_UAVS, 1), source.FIXED_ALTITUDE_M),
        ),
        axis=1,
    )
    targets = np.stack(
        [
            np.concatenate(
                (
                    episode.geometry.coordinate(source.TargetLabel.parse(label)),
                    [source.FIXED_ALTITUDE_M],
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
    episode = source.make_episode_source(0)
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

    ledger = source.build_oracle_safety_ledger(episode)
    ledger_value = ledger.to_primitive()
    ledger_certificate = source.validate_oracle_safety_primitive(
        episode, ledger_value
    )
    ledger_path = root / ORACLE_SAFETY_LEDGER_PROOF
    _write_json(ledger_path, ledger_value)

    oracle = source.oracle_qualification_from_safety_ledger(episode, ledger)
    oracle_value = oracle.to_primitive()
    if not oracle.passed:
        raise RuntimeError("G0 proof oracle qualification failed")
    oracle_path = root / ORACLE_PROOF
    _write_json(oracle_path, oracle_value)

    replay_value = source.build_oracle_branch_aware_replay_evidence(
        episode, ledger
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
        "ground_base_stations": source.GROUND_BASE_STATIONS,
        "paired_episode_ids": len(source.EPISODE_IDS),
        "episode_id_inventory": list(source.EPISODE_IDS),
        "bootstrap_resamples": source.BOOTSTRAP_RESAMPLES,
        "bootstrap_generator": BOOTSTRAP_GENERATOR,
        "bootstrap_seed": source.BOOTSTRAP_SEED,
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


def validate_source_artifacts(run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    value = _read_json(root / SOURCE_MANIFEST)
    _require_exact_keys(value, _SOURCE_MANIFEST_KEYS, label="source manifest")
    commit = _validate_source_commit(value.get("source_commit", ""))
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
        "ground_base_stations": source.GROUND_BASE_STATIONS,
        "paired_episode_ids": len(source.EPISODE_IDS),
        "episode_id_inventory": list(source.EPISODE_IDS),
        "bootstrap_resamples": source.BOOTSTRAP_RESAMPLES,
        "bootstrap_generator": BOOTSTRAP_GENERATOR,
        "bootstrap_seed": source.BOOTSTRAP_SEED,
        "K_search": source.K_SEARCH,
        "K_search_ceiling": source.K_SEARCH_CEILING,
        "nested_rollout": False,
        "replanning": False,
        "tree_or_beam_or_mcts": False,
        "real_environment_transitions": 0,
        "hypothetical_candidate_transitions": source.PHYSICAL_HORIZON * source.K_SEARCH,
        "geometry_support_rule": GEOMETRY_SUPPORT_RULE,
        "geometry_support_certificate": source.make_episode_source(0)
        .to_primitive()["geometry"]["geometry_support_certificate"],
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
    expected_source = source.make_episode_source(0).to_primitive()
    if source_value != expected_source:
        raise ValueError("G0 source proof does not reconstruct episode zero")
    ledger_value = _load_reference(
        root,
        value["oracle_safety_ledger_proof"],
        label="oracle safety ledger proof",
        expected_relative_path=ORACLE_SAFETY_LEDGER_PROOF,
    )
    ledger = source.oracle_safety_ledger_from_primitive(ledger_value)
    safety_certificate = source.validate_oracle_safety_ledger(
        source.make_episode_source(0), ledger
    )
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
    replay_certificate = source.validate_oracle_branch_aware_replay_primitive(
        source.make_episode_source(0), ledger, replay_value
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
    expected_oracle = source.oracle_qualification_from_safety_ledger(
        source.make_episode_source(0), ledger
    ).to_primitive()
    if oracle_value != expected_oracle or oracle_value.get("passed") is not True:
        raise ValueError("G0 oracle proof reconstruction mismatch")
    tracker_value = _load_reference(
        root,
        value["tracker_proof"],
        label="tracker proof",
        expected_relative_path=TRACKER_PROOF,
    )
    expected_tracker = _build_tracker_proof(source.make_episode_source(0))
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
    return value


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
    event = source.compute_episode_metrics(
        service,
        episode_id=0,
        control=source.Control.SAME_INFORMATION,
        cell=source.Cell.EVENT,
        onset=180,
        duration=80,
    )
    no_event = source.compute_episode_metrics(
        service,
        episode_id=0,
        control=source.Control.SAME_INFORMATION,
        cell=source.Cell.NO_EVENT,
        onset=180,
        duration=80,
    )
    catastrophe = service.copy()
    catastrophe[180:190] = np.nextafter(0.60, 0.0)
    catastrophe_row = source.compute_episode_metrics(
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
    lower_zero, upper_zero = source.clopper_pearson_one_sided(0)
    lower_all, upper_all = source.clopper_pearson_one_sided(len(source.EPISODE_IDS))
    return {
        "k0": [lower_zero, upper_zero],
        "k128": [lower_all, upper_all],
        "tail_probability": 0.05,
    }


def readiness_evaluate(*, run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    training = validate_source_artifacts(root)
    ledger_value = _load_reference(
        root,
        training["oracle_safety_ledger_proof"],
        label="oracle safety ledger proof",
        expected_relative_path=ORACLE_SAFETY_LEDGER_PROOF,
    )
    replay_value = _load_reference(
        root,
        training["oracle_behavioral_replay_proof"],
        label="oracle behavioral replay proof",
        expected_relative_path=ORACLE_BEHAVIORAL_REPLAY_PROOF,
    )
    production_witness = source.build_proof_episode_validity(
        source.make_episode_source(0), ledger_value, replay_value
    )
    if (
        production_witness.get("operational_valid") is not True
        or production_witness.get("result_branch") is not None
    ):
        raise RuntimeError("G0 production proof episode validity failed")
    plan = source.make_bootstrap_index_plan()
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
            "seed": source.BOOTSTRAP_SEED,
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
    validate_evaluation_artifacts(root)
    return value


def validate_evaluation_artifacts(run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    training = validate_source_artifacts(root)
    value = _read_json(root / EVALUATION_MANIFEST)
    _require_exact_keys(value, _EVALUATION_KEYS, label="evaluation manifest")
    plan = source.make_bootstrap_index_plan()
    expected_plan = {
        "shape": list(plan.shape),
        "seed": source.BOOTSTRAP_SEED,
        "sha256": hashlib.sha256(plan.tobytes(order="C")).hexdigest(),
        "lower_order_statistic": 500,
        "upper_order_statistic": 9500,
        "interpolation": False,
    }
    ledger_value = _load_reference(
        root,
        training["oracle_safety_ledger_proof"],
        label="oracle safety ledger proof",
        expected_relative_path=ORACLE_SAFETY_LEDGER_PROOF,
    )
    replay_value = _load_reference(
        root,
        training["oracle_behavioral_replay_proof"],
        label="oracle behavioral replay proof",
        expected_relative_path=ORACLE_BEHAVIORAL_REPLAY_PROOF,
    )
    expected_production_witness = source.build_proof_episode_validity(
        source.make_episode_source(0), ledger_value, replay_value
    )
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
    return value


def _branch_witnesses() -> dict[str, dict[str, Any]]:
    cases = {
        "invalid": (False, None, None, None),
        "infeasible": (True, source.GateStatus.FAIL, None, None),
        "oracle_only": (True, source.GateStatus.PASS, source.GateStatus.FAIL, None),
        "non_causal": (True, source.GateStatus.PASS, source.GateStatus.PASS, source.GateStatus.FAIL),
        "underpowered_oracle": (True, source.GateStatus.OPEN, None, None),
        "underpowered_sameinfo": (True, source.GateStatus.PASS, source.GateStatus.OPEN, None),
        "underpowered_causal": (True, source.GateStatus.PASS, source.GateStatus.PASS, source.GateStatus.OPEN),
        "identified": (True, source.GateStatus.PASS, source.GateStatus.PASS, source.GateStatus.PASS),
    }
    return {
        name: {
            "valid": valid,
            "ORACLE_STATUS": oracle.value if oracle is not None else None,
            "SAMEINFO_STATUS": sameinfo.value if sameinfo is not None else None,
            "CAUSAL_STATUS": causal.value if causal is not None else None,
            "result_branch": source.select_result_branch(
                valid=valid,
                oracle_status=oracle,
                sameinfo_status=sameinfo,
                causal_status=causal,
            ),
        }
        for name, (valid, oracle, sameinfo, causal) in cases.items()
    }


def _primitive_analysis_witness(
    *, root: Path, training: Mapping[str, Any]
) -> dict[str, Any]:
    ledger_value = _load_reference(
        root,
        training["oracle_safety_ledger_proof"],
        label="oracle safety ledger proof",
        expected_relative_path=ORACLE_SAFETY_LEDGER_PROOF,
    )
    replay_value = _load_reference(
        root,
        training["oracle_behavioral_replay_proof"],
        label="oracle behavioral replay proof",
        expected_relative_path=ORACLE_BEHAVIORAL_REPLAY_PROOF,
    )
    reconstructed = source.analyze_proof_fixture(
        source.make_episode_source(0), ledger_value, replay_value
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
    training = validate_source_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    primitive_witness = _primitive_analysis_witness(root=root, training=training)
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
        "first_match_order": list(source.FIRST_MATCH_ORDER),
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
    validate_analysis_artifacts(root)
    return value


def validate_analysis_artifacts(run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    training = validate_source_artifacts(root)
    validate_evaluation_artifacts(root)
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
        or value.get("first_match_order") != list(source.FIRST_MATCH_ORDER)
        or value.get("branch_witnesses") != _branch_witnesses()
        or value.get("primitive_analysis_witness")
        != _primitive_analysis_witness(root=root, training=training)
        or value.get("operational_valid") is not False
        or value.get("result_branch") is not None
        or value.get("scientific_conclusion") is not None
        or value.get("claim_scope") != CLAIM_SCOPE
        or value.get("additional_environment_transitions") != 0
        or value.get("additional_optimizer_steps") != 0
    ):
        raise ValueError("G0 analysis artifact invariant mismatch")
    return value


def _formal_execution_unbound(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError(
        "UAV G0 formal/nonformal scientific execution is not authorized in this source"
    )


def scientific_source(*args: Any, **kwargs: Any) -> None:
    _formal_execution_unbound(*args, **kwargs)


def scientific_evaluate(*args: Any, **kwargs: Any) -> None:
    _formal_execution_unbound(*args, **kwargs)


def scientific_analyze(*args: Any, **kwargs: Any) -> None:
    _formal_execution_unbound(*args, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=(
            "source",
            "evaluate",
            "analyze",
            "readiness-smoke",
            "readiness-train",
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ),
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    args = parser.parse_args()
    if args.formal:
        _formal_execution_unbound()
    if args.stage in {"readiness-smoke", "readiness-train"} and args.source_commit is None:
        raise ValueError("G0 readiness entry requires --source-commit")
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
    elif args.stage == "source":
        scientific_source(run_root=args.run_root, source_commit=args.source_commit)
    elif args.stage == "evaluate":
        scientific_evaluate(run_root=args.run_root)
    else:
        scientific_analyze(run_root=args.run_root)


if __name__ == "__main__":
    main()
