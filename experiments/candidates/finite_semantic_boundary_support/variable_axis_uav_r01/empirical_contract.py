from __future__ import annotations

import hashlib
import json
from itertools import product
from typing import Any


RUN_ID = "fsbs-r01-complete-20260827-01"
OUTPUT_ROOT = (
    "temp/directions/finite_semantic_boundary_support/exp/"
    "fsbs-r01-complete-20260827-01/"
)
MODULE = (
    "experiments.candidates.finite_semantic_boundary_support."
    "variable_axis_uav_r01.empirical_transaction"
)
PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
REGISTERED_SEEDS = (11, 23, 37, 53, 71, 89, 107, 127)
ARMS = ("AUTHENTIC", "REASSOCIATED")
BRANCHES = ("NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def empirical_boundary() -> dict[str, Any]:
    return {
        "schema": "FSBS_R01_S3_EMPIRICAL_BOUNDARY_V1",
        "run_id": RUN_ID,
        "output_root": OUTPUT_ROOT,
        "module": MODULE,
        "payload_argv": [PYTHON, "-m", MODULE],
        "destination_preconditions": {
            "mode": "CREATE_ONLY",
            "must_be_absent_or_empty": True,
            "symlink_or_reparse_forbidden": True,
            "existing_complete_terminal_forbids_rerun": True,
        },
        "empirical_activity_released": False,
        "operator_now": False,
        "effect_refs": [],
    }


def checkpoint_identities() -> list[dict[str, Any]]:
    return [
        {
            "checkpoint_id": f"fsbs-r01-{arm.lower()}-seed-{seed}",
            "arm": arm,
            "seed": seed,
            "relative_path": f"checkpoints/{arm.lower()}-seed-{seed}.json",
            "materialized": False,
        }
        for arm, seed in product(ARMS, REGISTERED_SEEDS)
    ]


def canonical_parameters() -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "FSBS_R01_REGISTERED_PARAMETERS_V1",
        "namespace": "FSBS-VN1-R01",
        "registered_seeds": list(REGISTERED_SEEDS),
        "arms": list(ARMS),
        "architecture": {
            "selector_shape": [2, 4],
            "selector_features": [
                "bias", "surface_bit_signed", "interface_i_signed", "interface_r_signed"
            ],
            "selector_actions": ["OPEN_0", "OPEN_1"],
            "controller_shape": [2, 4],
            "controller_features": [
                "bias", "payload_bit_signed", "interface_i_signed", "interface_r_signed"
            ],
            "controller_actions": ["LANE_0", "LANE_1"],
            "zero_initialization": True,
            "independent_arm_seed_state": True,
        },
        "training": {
            "envelopes": [6, 8],
            "episodes_per_envelope_arm_seed": 64,
            "decisions_per_arm_seed": 1_984,
            "all_arm_seed_decisions": 31_744,
        },
        "evaluation": {
            "envelopes": [6, 8, 10],
            "branches": list(BRANCHES),
            "episodes_per_envelope_branch_arm_seed": 32,
            "decisions_per_branch_arm_seed": 1_728,
            "all_branch_arm_seed_decisions": 110_592,
        },
        "retained_gate_transactions": 15_360,
        "registered_total_transactions": 157_696,
        "registered_cap_transactions": 160_000,
        "epsilon": {
            "start": [2, 5],
            "end": [1, 20],
            "completed_decision_domain": [0, 1_984],
            "pre_window_count_for_all_subscribers": True,
        },
        "update": {
            "base_rate": [1, 20],
            "coefficient": "ONE_OVER_80_TIMES_PAIR_COUNT",
            "same_pre_window_parameters": True,
            "commutative_grouped_once_per_window": True,
            "common_team_signal_only": True,
        },
        "address_families": [
            "world", "churn", "pairing", "carrier-donor", "interface", "presentation",
            "exploration", "tie-rank", "evaluation-mask",
        ],
        "support": {
            "outer_strata": 384,
            "accepted_gate_transactions": 12_288,
            "denied_gate_transactions": 3_072,
            "accepted_resource": [1, 1],
            "denied_open_both_required": [2, 1],
            "resource_cap": [1, 1],
        },
        "control_invariants": {
            "REASSOCIATED_selection_rate": [1, 2],
            "MASKED_selection_rate": [1, 2],
            "FORCE_RELEVANT_selection_rate": [1, 1],
            "FORCE_DECOY_selection_rate": [0, 1],
        },
        "thresholds": {
            "controller_safe_rate_each_seed_M_min": [9, 10],
            "heldout_mean_selection_effect_min": [1, 5],
            "heldout_mean_return_effect_min": [1, 10],
            "heldout_authentic_selection_min": [7, 10],
            "forced_relevant_decoy_return_effect_min": [2, 5],
            "bounded_null_interval": [[-1, 20], [1, 20]],
        },
        "measurement_fields": [
            "relevant_record_selection_rate", "pair_safe_rate", "pair_score_distribution",
            "common_team_return", "paired_selection_effect", "paired_return_effect",
            "natural_masked_effect", "forced_relevant_decoy_effect", "heldout_M10_effect",
            "selector_action_counts", "controller_action_counts", "action_entropy",
            "action_margins", "first_passage_75pct_selection", "update_counts",
            "polarity_strata", "membership_window_strata", "lineage_role_balance",
            "peer_change_rate", "active_masks", "survivor_rejoin_state_checks",
            "identity_path_anomalies", "declared_actual_resource_totals",
            "wall_memory_storage_totals", "mediator_residual_localization",
        ],
        "first_true_order": [
            "INVALID_OR_INCONCLUSIVE",
            "OPTIMIZATION_GEOMETRY_FALSIFIER",
            "CARRIER_CREDIT_UNSUPPORTED",
            "SELECTION_TO_COORDINATION_UNSUPPORTED",
            "HELDOUT_ROSTER_TRANSFER_FAILED",
            "RESERVATION_INFORMATION_EDGE_ABSENT",
            "BOUNDED_NULL",
            "POSITIVE_EDGE",
            "INCONCLUSIVE_REMAINDER",
        ],
        "checkpoint_identities": checkpoint_identities(),
        "tuning_or_retry": False,
        "values_materialized": False,
    }
    value["sha256"] = hashlib.sha256(_canonical(value)).hexdigest()
    return value


def canonical_resource_estimate() -> dict[str, Any]:
    return {
        "schema": "FSBS_R01_COMPLETE_RESOURCE_ESTIMATE_V1",
        "transactions": 157_696,
        "workers": 1,
        "threads_per_worker": 1,
        "device": "CPU",
        "wall_seconds": 600,
        "cpu_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
        "basis": "ACCEPTED_S2_HIGH_RESULT_BLIND_PROJECTION",
        "scientific_execution_observed": False,
    }


def git_prerequisites(observed_shared_head: str) -> dict[str, Any]:
    return {
        "required_branch": (
            "omp/finite_semantic_boundary_support/engineering/"
            "bc2db89b-8d64-4f7e-abac-5f1b0a58b4c9"
        ),
        "observed_shared_checkout_head": observed_shared_head,
        "observed_shared_checkout_eligible": False,
        "candidate_head": None,
        "code_sha": None,
        "required_equality": "CANDIDATE_HEAD_EQUALS_IMMUTABLE_MANIFEST_CODE_SHA",
        "candidate_branch_must_be_omp": True,
        "source_and_test_manifest_must_match_candidate_head": True,
        "output_root_must_be_create_only": True,
        "release_ready": False,
    }
