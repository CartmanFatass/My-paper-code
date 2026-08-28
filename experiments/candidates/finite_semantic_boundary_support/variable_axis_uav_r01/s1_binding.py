from __future__ import annotations

from itertools import product
import hashlib
from typing import Any

from .counter import address
from .s1_validation import validate_binding


ARMS = ("AUTHENTIC", "REASSOCIATED")
SEEDS = (11, 23, 37, 53, 71, 89, 107, 127)


def architecture_contract() -> dict[str, Any]:
    slots = [
        {
            "arm": arm,
            "seed": seed,
            "initialization_contract": "ZERO_ONLY_NOT_MATERIALIZED",
            "parameter_values": None,
            "checkpoint": None,
        }
        for arm, seed in product(ARMS, SEEDS)
    ]
    return {
        "selector_head": {
            "shape": [2, 4],
            "feature_order": [
                "bias",
                "surface_bit_signed",
                "interface_i_signed",
                "interface_r_signed",
            ],
            "legal_actions": ["OPEN_0", "OPEN_1"],
            "parameter_values": None,
        },
        "controller_head": {
            "shape": [2, 4],
            "feature_order": [
                "bias",
                "payload_bit_signed",
                "interface_i_signed",
                "interface_r_signed",
            ],
            "legal_actions": ["LANE_0", "LANE_1"],
            "parameter_values": None,
        },
        "shared_across_lineages_and_envelopes": True,
        "forbidden_feature_fields": [
            "identity",
            "token",
            "lineage",
            "partner",
            "roster_position",
            "M",
            "N_t",
            "arm",
            "donor",
            "block",
            "hidden_slot",
            "unopened_payload",
            "pair_score",
            "future_return",
        ],
        "structural_terminal_slots": slots,
    }


def workload_contract() -> dict[str, int]:
    training_per_slot = 64 * (13 + 18)
    evaluation_per_branch_slot = 32 * (13 + 18 + 23)
    training = len(ARMS) * len(SEEDS) * training_per_slot
    evaluation = 4 * len(ARMS) * len(SEEDS) * evaluation_per_branch_slot
    gate = 15_360
    return {
        "training_per_arm_seed": training_per_slot,
        "training_all_slots": training,
        "evaluation_per_branch_arm_seed": evaluation_per_branch_slot,
        "evaluation_all_branches_slots": evaluation,
        "retained_gate_transactions": gate,
        "registered_total_transactions": training + evaluation + gate,
        "registered_cap_transactions": 160_000,
    }


def epsilon_contract() -> dict[str, Any]:
    fixtures = (
        (0, (2, 5)),
        (992, (9, 40)),
        (1_984, (1, 20)),
    )
    return {
        "completed_decision_domain": [0, 1_984],
        "linear_start": [2, 5],
        "linear_end": [1, 20],
        "all_window_decisions_use_pre_window_count": True,
        "fixtures": [
            {"completed_decisions": decision, "epsilon": list(value)}
            for decision, value in fixtures
        ],
    }


def window_update_contract() -> dict[str, Any]:
    return {
        "same_pre_window_parameter_generation": True,
        "all_actions_sampled_before_single_apply": True,
        "applications_per_window": 1,
        "reduction": "COMMUTATIVE_SUM_GROUPED_BY_ACTION",
        "base_rate": [1, 20],
        "normalization": "ONE_OVER_FOUR_TIMES_PAIR_COUNT",
        "coefficient_fixtures": [
            {"P_t": pair_count, "coefficient": [1, 80 * pair_count]}
            for pair_count in (2, 3, 4, 5)
        ],
        "selector": {
            "action_indicator": "SELECTOR_ACTION_EQUALS_GROUP_ACTION",
            "symbolic_residual": "COMMON_TEAM_SIGNAL_MINUS_SELECTOR_HEAD_SCORE",
            "feature_order": [
                "bias", "surface_bit_signed", "interface_i_signed", "interface_r_signed"
            ],
        },
        "controller": {
            "action_indicator": "CONTROLLER_ACTION_EQUALS_GROUP_ACTION",
            "symbolic_residual": "COMMON_TEAM_SIGNAL_MINUS_CONTROLLER_HEAD_SCORE",
            "feature_order": [
                "bias", "payload_bit_signed", "interface_i_signed", "interface_r_signed"
            ],
        },
        "parameter_values": None,
        "numeric_signal_values": None,
    }


def address_contract() -> dict[str, Any]:
    proof_specs = (
        (11, "exploration", ["TRAIN", 6, 0, "selector", 0]),
        (11, "tie-rank", ["EVALUATION", "selector", "b+1_i-1_r+1"]),
        (127, "paired-exogenous-world", [10, "REDUCED", 1, 0, 1, 1, 0]),
    )
    proofs: list[dict[str, Any]] = []
    for seed, family, coordinates in proof_specs:
        digest = hashlib.sha256(address(seed, family, coordinates, 0)).hexdigest()
        proofs.append(
            {
                "seed": seed,
                "family": family,
                "coordinates": coordinates,
                "AUTHENTIC": digest,
                "REASSOCIATED": digest,
            }
        )
    return {
        "families": [
            "world", "churn", "pairing", "carrier-donor", "interface", "presentation",
            "exploration", "tie-rank", "evaluation-mask",
        ],
        "training_choice_coordinates_separate_by_head": True,
        "evaluation_tie_rank_scope": "SEED_HEAD_FEATURE_CONTEXT_FIXED",
        "evaluation_tie_rank_uses_world_coordinate": False,
        "paired_arm_proofs": proofs,
    }


def evaluation_contract() -> dict[str, Any]:
    common = {"updates_parameters": False, "resource_receipt": [1, 1]}
    return {
        "branch_order": ["NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"],
        "episodes_per_envelope_branch_arm_seed": 32,
        "envelopes": [6, 8, 10],
        "branches": {
            "NATURAL": {
                **common,
                "selector_input": "BOUND_AUTHENTIC_OR_REASSOCIATED_SURFACE_BIT",
                "open_action": "SCHEMA_BOUND_GREEDY_SELECTOR",
            },
            "MASKED": {
                **common,
                "selector_input": "INDEPENDENT_BALANCED_BIT_WITHIN_EXACT_STRATUM",
                "open_action": "SCHEMA_BOUND_GREEDY_SELECTOR",
            },
            "FORCE_RELEVANT": {
                **common,
                "selector_input": "NOT_CONSUMED_BY_FORCED_OPEN",
                "open_action": "FORCED_RELEVANT_ONE_RECORD",
            },
            "FORCE_DECOY": {
                **common,
                "selector_input": "NOT_CONSUMED_BY_FORCED_OPEN",
                "open_action": "FORCED_DECOY_ONE_RECORD",
            },
        },
    }


def measurement_schema() -> dict[str, Any]:
    return {
        "index_fields": ["seed", "arm", "M", "N_t", "window", "evaluation_branch"],
        "independent_unit": "SEED",
        "paired_seed_count": 8,
        "values_materialized": False,
        "required_fields": [
            "relevant_record_selection_rate",
            "pair_safe_rate",
            "pair_score_distribution",
            "common_team_return",
            "paired_selection_effect",
            "paired_return_effect",
            "natural_masked_effect",
            "forced_relevant_decoy_effect",
            "heldout_M10_effect",
            "selector_action_counts",
            "controller_action_counts",
            "action_entropy",
            "action_margins",
            "first_passage_75pct_selection",
            "update_counts",
            "polarity_strata",
            "membership_window_strata",
            "lineage_role_balance",
            "peer_change_rate",
            "active_masks",
            "survivor_rejoin_state_checks",
            "identity_path_anomalies",
            "declared_actual_resource_totals",
            "wall_memory_storage_totals",
            "mediator_residual_localization",
        ],
    }


def control_invariants() -> list[dict[str, Any]]:
    return [
        {"branch": "REASSOCIATED", "selection_rate": [1, 2], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "MASKED", "selection_rate": [1, 2], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "FORCE_RELEVANT", "selection_rate": [1, 1], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "FORCE_DECOY", "selection_rate": [0, 1], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
    ]


def first_true_contract() -> dict[str, Any]:
    return {
        "predicate_values": None,
        "ordered_enum": [
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
    }


def result_manifest_contract() -> dict[str, Any]:
    return {
        "schema_only": True,
        "values_materialized": False,
        "partial_commit_allowed": False,
        "atomic_final_replace_required": True,
        "required_counts": {
            "retained_gate_transactions": 15_360,
            "terminal_parameter_slots": 16,
            "evaluation_branches": 4,
            "arms": 2,
            "paired_seeds": 8,
            "evaluation_envelopes": 3,
        },
        "required_sections": [
            "authority_refs",
            "source_manifest",
            "retained_gate",
            "terminal_slots",
            "evaluation_branches",
            "measurements",
            "controls",
            "resource_totals",
            "anomalies",
            "first_true_outcome",
            "result_firewall",
        ],
    }


def build_binding() -> dict[str, Any]:
    binding: dict[str, Any] = {
        "schema": "FSBS_R01_S1_LEARNER_FREE_TECHNICAL_BINDING_V1",
        "mode": "TECHNICAL_SCHEMA_ONLY_NO_LEARNER_EXECUTION",
        "namespace": "FSBS-VN1-R01",
        "effect_refs": [],
        "firewall": {
            "registered_seed_execution_enabled": False,
            "parameter_values_materialized": False,
            "learner_or_model_instantiated": False,
            "checkpoint_materialized": False,
            "optimizer_called": False,
            "policy_executed": False,
            "training_or_evaluation_executed": False,
            "question_relevant_values_emitted": False,
            "partial_manifest_allowed": False,
            "external_effect_executed": False,
        },
        "architecture": architecture_contract(),
        "separation_contract": {
            "parameters_cross_arm_or_seed": False,
            "transitions_cross_arm_or_seed": False,
            "updates_cross_arm_or_seed": False,
            "checkpoints_cross_arm_or_seed": False,
            "optimizer_state_cross_arm_or_seed": False,
            "paired_exogenous_addresses_across_arms": True,
            "paired_exploration_addresses_across_arms": True,
        },
        "workload": workload_contract(),
        "epsilon_contract": epsilon_contract(),
        "window_update_contract": window_update_contract(),
        "address_contract": address_contract(),
        "evaluation_contract": evaluation_contract(),
        "measurement_schema": measurement_schema(),
        "control_invariants": control_invariants(),
        "first_true_contract": first_true_contract(),
        "result_manifest_contract": result_manifest_contract(),
    }
    binding["evidence_tree"] = validate_binding(binding)
    return binding
