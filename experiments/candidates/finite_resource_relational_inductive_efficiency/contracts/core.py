"""Frozen, value-blind FRRIE manifest contract.

Validation here inspects identities and structure only.  It never opens a
seed packet, evaluates a return, or infers a threshold from an observed value.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

FRRIE_MANIFEST_V1 = "FRRIE_MANIFEST_V1"
FRRIE_CHECKPOINT_V1 = "FRRIE_CHECKPOINT_V1"
FRRIE_SEALED_SEED_PACKET_V1 = "FRRIE_SEALED_SEED_PACKET_V1"
FRRIE_COMPLETE_PANEL_RESULT_V1 = "FRRIE_COMPLETE_PANEL_RESULT_V1"
FRRIE_TERMINAL_V1 = "FRRIE_TERMINAL_V1"
FRRIE_MANIFEST_V2 = "FRRIE_MANIFEST_V2"
FRRIE_CHECKPOINT_V2 = "FRRIE_CHECKPOINT_V2"
FRRIE_SEALED_SEED_PACKET_V2 = "FRRIE_SEALED_SEED_PACKET_V2"
FRRIE_COMPLETE_PANEL_RESULT_V2 = "FRRIE_COMPLETE_PANEL_RESULT_V2"
FRRIE_COMPLETE_PANEL_ANALYSIS_V2 = "FRRIE_COMPLETE_PANEL_ANALYSIS_V2"
FRRIE_TERMINAL_V2 = "FRRIE_TERMINAL_V2"

EXPERIMENT_ID = "FRRIE-RIDGEGATE-2Z-RSCF-R01"
DIRECTION_ID = "finite_resource_relational_inductive_efficiency"
HOST_ID = "FRRIE-RIDGEGATE-2Z/RSCF"
SOURCE_ID_V1 = "FRRIE-RIDGEGATE-2Z-RSCF-FRESH-SOURCE-V1"
NATIVE_COMPONENT_V1 = "FRRIE_RIDGEGATE2Z_RSCF_FULL_HOST"
SOURCE_ID = "FRRIE-RIDGEGATE-2Z-RSCF-FRESH-SOURCE-V2"
NATIVE_COMPONENT = "FRRIE_RIDGEGATE2Z_RSCF_EXTERNAL_ACTION_HOST_V2"
NATIVE_ABI_V1 = "FRRIE_RIDGEGATE2Z_RSCF_NATIVE_ABI_V1_FP32"
NATIVE_ABI = "FRRIE_NATIVE_STEP_ABI_V2_FP32"
NATIVE_BINDING_KIND = "FRRIE_NATIVE_CTYPES_EXTERNAL_STEP_V2"
LEARNED_ARMS = ("PHY_TRUST", "EDGE_FLEX")
EVALUATION_ONLY_ARM = "UNIFORM_LEGAL"
TRAIN_ROSTERS = (9, 15)
HELDOUT_ROSTERS = (6, 21)
INTERVENTIONS = ("INTACT", "SEMANTIC_COLUMN_ROTATE")
MODEL_PARAMETER_COUNT = 35_513
UPDATES = 512
EPISODES_PER_UPDATE = 64
EVALUATIONS_PER_CELL = 256
FP32_PROBABILITY_TOLERANCE = 2.0e-6
REQUIRED_SEED_BLOCKS = tuple(f"FRRIE-FRESH-BLOCK-{index:03d}" for index in range(1, 25))

QUANTITY_ORDER = (
    "d_N9", "d_N15", "d_N6", "d_N21",
    "e_N9", "e_N15", "c_N6", "c_N21", "z_N6", "z_N21",
    "C_PHY_N6", "V_N6", "I_N6", "C_PHY_N21", "V_N21", "I_N21",
    "A_cut_N6", "A_atten_N6", "A_TV_N6",
    "A_cut_N21", "A_atten_N21", "A_TV_N21",
    "A_dir_N6", "A_interaction_N6", "A_zone_N6",
    "A_dir_N21", "A_interaction_N21", "A_zone_N21",
)
THRESHOLDS = {
    "delta_R": 0.04,
    "delta_C": 0.03,
    "delta_Z": 0.02,
    "delta_cutR": 0.05,
    "delta_TV": 0.08,
    "delta_I": 0.03,
    "delta_E": 0.08,
    "delta_seen_eq": 0.04,
}
THRESHOLD_FIELDS = tuple(THRESHOLDS)
INFERENCE_CONTRACT = {
    "status": "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS",
    "active_method": None,
    "alpha": None,
    "critical": None,
    "polarity_enabled": False,
    "ready": False,
    "block_unit": "WHOLE_SEED_BLOCK",
    "block_count": 24,
    "quantity_order": list(QUANTITY_ORDER),
    "descriptive_only": True,
    "reduction": "MANIFEST_ORDER_BINARY64_MATH_FSUM",
    "missing_or_nonfinite": "INVALID_NO_SCIENTIFIC_VALUES",
}
IMPLEMENTATION_CONTRACT = {
    "schema": "FRRIE_IMPLEMENTATION_CONTRACT_V2",
    "dgp_native": {
        "component": NATIVE_COMPONENT,
        "abi": NATIVE_ABI,
        "binding_kind": NATIVE_BINDING_KIND,
        "ownership": "NATIVE_ENVIRONMENT_TRANSITIONS_EXTERNAL_POLICY_ACTIONS",
        "horizon": 12,
        "basins": 2,
        "events": {
            "per_basin": 3,
            "event_time_support": list(range(8)),
            "sampling": "UNIFORM_WITHOUT_REPLACEMENT_WITHIN_BASIN",
            "detection_probability": 0.75,
            "detection_condition": "SCAN_AT_MATCHING_EVENT_SLOT",
            "report_identity": ["basin", "event_ordinal", "event_time"],
            "report_identity_persistent_through_fifo_and_delivery": True,
        },
        "fifo": {
            "WEST_SURVEYOR_capacity": 2, "EAST_SURVEYOR_capacity": 2,
            "RIDGE_RELAY_capacity": 4, "overflow": "DROP_HEAD_APPEND_TAIL",
            "expired_when": "slot >= event_time + 4",
        },
        "within_slot_order": [
            "ARRIVAL_ACK_DEQUEUE", "PURGE", "OBSERVE", "EXTERNAL_ACTION",
            "RADIO", "SCAN",
        ],
        "actions": ["SCAN", "UPLINK", "LISTEN_WEST", "LISTEN_EAST", "FORWARD_BASE", "HOLD"],
        "legal_masks": [[True, True, False, False, False, True], [True, True, False, False, False, True], [False, False, True, True, True, True]],
        "radio": {
            "half_duplex": True,
            "decode_condition": "EXACTLY_ONE_NONEMPTY_SENDER",
            "collision_capture": False,
            "uplink_P0_by_basin": [0.86, 0.78],
            "uplink_probability": "logistic(logit(P0[basin]) - 0.22*(N/3-1))",
            "base_P0": 0.90,
            "base_probability": "logistic(logit(0.90) - 0.22*(N/3-1))",
            "latency_slots": 1,
            "slot_11_reception": False,
        },
        "arrival_and_success": {
            "decoded_uplink": "APPEND_IF_NONEXPIRED_THEN_DEQUEUE_SENDER_HEAD",
            "decoded_base": "CLASSIFY_EXPIRED_AND_DUPLICATE_THEN_DEQUEUE_SENDER_HEAD",
            "duplicate_delivery": "NO_NEW_DELIVERY_BUT_ACK_DEQUEUE",
            "expired_delivery": "NO_NEW_DELIVERY_BUT_ACK_DEQUEUE",
            "surveyor_success": "ANY_DECODED_NONEXPIRED_RECEIVER_APPEND",
            "relay_success": "NEW_NONEXPIRED_NONDUPLICATE_BASE_DELIVERY_ONLY",
        },
        "waste": {
            "denominator": "ALL_UPLINK_LISTEN_AND_FORWARD_BASE_ACTIONS",
            "empty_sender": True,
            "listener_without_nonexpired_enqueue": True,
            "uplink_sender_not_sole_useful_or_at_slot11": True,
            "base_sender_not_sole_new_timely_or_at_slot11": True,
            "zero_radio_actions_value": 0.0,
            "formula": "waste_actions/radio_actions",
        },
    },
    "observation_and_rosters": {
        "observation_width": 22,
        "rosters": [6, 9, 15, 21],
        "roles": ["WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY"],
        "role_layout": "CONTIGUOUS_EQUAL_THIRDS_WEST_EAST_RELAY",
        "roster_churn": False,
        "fields": [
            {"indices": [0, 1, 2], "value": "ROLE_ONE_HOT_WEST_EAST_RELAY"},
            {"index": 3, "value": "slot/11"},
            {"indices": [4, 5, 6], "value": "(N/3)/7_REPEATED"},
            {"indices": [7, 9, 11, 13], "value": "FIFO_POSITION_OCCUPIED"},
            {"indices": [8, 10, 12, 14], "value": "min(max(slot-event_time,0),3)/3_IF_OCCUPIED_ELSE_0"},
            {"indices": [15, 16, 17, 18, 19, 20], "value": "PREVIOUS_ACTION_ONE_HOT_OR_ALL_ZERO_IF_UNSET"},
            {"index": 21, "value": "PREVIOUS_SUCCESS_BOOLEAN"},
        ],
        "zero_conventions": ["EMPTY_FIFO_POSITION_ZERO_PAIR", "UNSET_PREVIOUS_ACTION_ALL_ZERO", "INACTIVE_AGENT_ALL_ZERO"],
    },
    "actor": {
        "message_encoder": [[22, 64], [64, 32]],
        "gru_input_width": 55,
        "gru_hidden_width": 64,
        "action_head": [64, 6],
        "legal_probability_floor": "0.04/m",
        "fp32_probability_tolerance": FP32_PROBABILITY_TOLERANCE,
        "rotation": "SENDER_COLUMNS_ONLY_ONE_GRU_STEP_NO_PROPAGATION",
        "layer_shapes_in_order": [
            ["message_encoder.weight_ih", [64, 22]], ["message_encoder.bias_ih", [64]],
            ["message_encoder.weight_ho", [32, 64]], ["message_encoder.bias_ho", [32]],
            ["gru.weight_input_zrn", [192, 55]], ["gru.weight_hidden_zrn", [192, 64]],
            ["gru.bias_zrn", [192]], ["action_head.weight", [6, 64]],
            ["action_head.bias", [6]], ["beta", [3, 3, 2]],
            ["critic.input.weight", [64, 66]], ["critic.input.bias", [64]],
            ["critic.hidden.weight", [64, 64]], ["critic.hidden.bias", [64]],
            ["critic.output.weight", [1, 64]], ["critic.output.bias", [1]],
        ],
        "parameter_count": 35_513,
        "initialization": {
            "address": ["seed_block", "INITIALIZE", 0, 0, 0, 0, 0, "draw", "INITIALIZATION"],
            "uint32_to_unit": "(uint32 + 0.5)/2**32",
            "scale": "(2*unit-1)*0.05",
            "dtype_layout": "LITTLE_ENDIAN_FP32_C_ORDER_LAYER_SHAPES",
            "paired_arms": "SEPARATE_COPIES_BIT_IDENTICAL",
        },
        "projection_boxes": {"PHY_TRUST": [-0.15, 0.15], "EDGE_FLEX": [-1.5, 1.5]},
        "P0": [[0.92, 0.48, 0.88], [0.48, 0.92, 0.82], [0.86, 0.78, 0.90]],
        "latency": [[1.0, 2.0, 1.0], [2.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
        "loaded_probability": "sigmoid(logit(P0[r,s]) - 0.22*(n_s-1))",
        "v": "(2*log(n_s)-log(14))/log(3.5)",
        "K0": "loaded_probability/latency[r,s]",
        "omega": "K0*exp(beta[r,s,0]+beta[r,s,1]*v_s)",
        "denominator": "sum_s(omega[r,s]*n_s)",
        "role_summary": "sum_s(omega[r,s]*role_sum_s)/(denominator_r+1e-12)",
        "encoder": "tanh(linear_64x22);tanh(linear_32x64)",
        "gru": {
            "input_order": ["observation22", "role_summary32", "denominator1"],
            "z": "sigmoid(Wz*x + Uz*h)", "r": "sigmoid(Wr*x + Ur*h)",
            "candidate": "tanh(Wn*x + Un*(r*h))",
            "hidden": "(1-z)*candidate + z*h",
            "reset_before_candidate": True,
        },
        "probabilities": "0.96*softmax(masked_logits)+legal_mask*(0.04/m)",
        "critic": "role_mean_observations_concat66 -> tanh64 -> tanh64 -> scalar1",
        "semantic_column_rotation": [2, 0, 1],
        "rotation_invariants": ["observations", "incoming_hidden", "beta_indices", "messages", "counts", "simulator_physics", "rng"],
    },
    "rscf": {
        "factual": "CACHED_DIFFERENTIABLE_FULL_EPISODE",
        "origin_schedule": {
            "pairs_per_roster_update": 16,
            "episodes_per_roster_update": 32,
            "roles_in_order": ["WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY"],
            "one_origin_per_episode_role": True,
            "base_slot_support": list(range(12)),
            "antithetic_pair_law": "slot_side0 + slot_side1 = 11",
            "base_slot_address_includes_side": False,
            "base_slot_shared_across_pair_sides": True,
            "side0_slot": "BASE_SLOT",
            "side1_slot": "11_MINUS_BASE_SLOT",
            "role_local_index_address_includes_side": True,
            "role_local_entity_shared_across_pair_sides": False,
            "role_local_entity_draws_independent_across_pair_sides": True,
            "role_local_index_support": "0..N/3-1",
            "matching_episode_coordinate_shared_across_arms": True,
        },
        "legal_q_entries_per_episode": 10,
        "factual_q_entries_cached_per_episode": 3,
        "nonfactual_suffixes_per_episode": 7,
        "physical_factual_label_restore_closed_loop_suffix_audits_per_episode": 3,
        "factual_identity_audit": {
            "origin_clock": "POST_GRU_DISTRIBUTION_ACTION_PRETRANSITION",
            "origin_current_step": "RETAINED_JOINT_ACTION_AND_POSTDECISION_HIDDEN",
            "actor_recomputation_begins": "ORIGIN_SLOT_PLUS_1",
            "per_slot_direct_equal": [
                "state", "observation", "roles", "legal_masks", "incoming_hidden",
                "probabilities", "actions", "terminal_return",
            ],
            "new_rng_addresses": 0,
            "cache_J_only_after_equality": True,
        },
        "suffix": {
            "restore": ["environment_snapshot", "incoming_hidden", "postdecision_hidden"],
            "factual_focal_action": "RETAIN_AND_REPLAY_CLOSED_LOOP",
            "nonfactual_focal_action": "REPLACE_ONLY_FOCAL_ACTION_AT_ORIGIN",
            "teammate_origin_actions": "UNCHANGED_FACTUAL_JOINT_ACTION",
            "future_actions": "CLOSED_LOOP_CURRENT_POLICY_FROM_T_PLUS_1",
            "future_tape": "COMMON_FACTUAL_POTENTIAL_OUTCOME_TAPE",
            "model_mutation": False,
            "new_rng_addresses": 0,
        },
        "targets_and_loss": {
            "q_targets": "ALL_10_LEGAL_ENTRIES_STOPPED",
            "baseline": "sum_legal(stop(p_a)*stop(Q_a))_PER_ROLE",
            "advantage": "stop(terminal_return-baseline)",
            "score": "-sum_3_roles(log(p_factual)*advantage)/3",
            "entropy": "MEAN_OVER_ALL_12xN_FACTUAL_POLICY_ROWS",
            "entropy_coefficient": 0.01,
            "critic": "mean((V_slot-stop(terminal_return))**2)",
            "critic_coefficient": 0.5,
            "gamma": 1.0,
            "update_batch": {"episodes": 64, "roster_order": [9, 15] * 32, "equal_episode_weight": "1/64"},
        },
    },
    "optimizer": {
        "kind": "TORCH_ADAM_PROJECT_AFTER_STEP_MOMENTS_UNTOUCHED",
        "lr": 3.0e-4, "betas": [0.9, 0.999], "eps": 1.0e-8,
        "weight_decay": 0.0, "amsgrad": False, "maximize": False,
        "foreach": False, "capturable": False, "differentiable": False,
        "fused": None, "gradient_clip_l2": 0.5,
        "parameter_order": "LAYER_SHAPES",
        "zero_grad_set_to_none": True,
        "backward_calls_per_update": 1,
        "global_norm_clip": {"norm_type": 2.0, "max_norm": 0.5, "error_if_nonfinite": True, "foreach": False},
        "order": ["ZERO_GRAD", "ONE_FULL_BATCH_BACKWARD", "FINITE_GRADIENT_AUDIT", "GLOBAL_NORM_CLIP", "ADAM_STEP", "BETA_PROJECTION"],
        "projection_updates_optimizer_moments": False,
    },
    "state_codec": {
        "optimizer_magic_ascii": "FRRIEOPT",
        "optimizer_state_version": 1,
        "encoding": "DIRECT_LITTLE_ENDIAN_FP32_NO_PICKLE",
        "parameter_state": "16_LAYER_SHAPES_LITTLE_ENDIAN_FP32_C_ORDER",
        "adam_state": "FIRST_MOMENT_FP32_THEN_SECOND_MOMENT_FP32_THEN_UINT64_STEP",
        "checkpoint_schema": FRRIE_CHECKPOINT_V2,
        "checkpoint_boundary": "POST_UPDATE_512_PRE_EVALUATION",
        "evaluation_checkpoint_cursor": 0,
        "checkpoint_io": 1,
    },
    "rng": {
        "addressing": "SEMANTIC_ARM_CUT_BRANCH_INDEPENDENT",
        "fp32_uniform_mapping": {
            "schema": "FRRIE_ADDRESSED_FP32_UNIFORM_V1",
            "prf": "SHA-256", "prf_word_bits": 256,
            "selected_bits": 24, "selection": "MOST_SIGNIFICANT_BITS",
            "numerator_min": 0, "numerator_max": 16_777_215,
            "denominator": 16_777_216, "formula": "TOP24 / 2**24",
            "support": "K_OVER_2_POW_24", "upper_endpoint_excluded": True,
        },
        "semantic_coordinate_fields": [
            "seed_block", "purpose", "roster", "update", "episode", "basin",
            "event_ordinal", "slot", "public_role", "role_local_index",
            "sender", "receiver", "kind", "draw",
        ],
        "semantic_kinds": [
            "event_time", "detection_uniform", "uplink_uniform", "base_uniform",
            "action_uniform", "origin_base_slot", "origin_role_local_index",
        ],
        "forbidden_address_coordinates": ["arm", "arm_id", "cut", "cut_id", "intervention", "intervention_id", "branch", "branch_id"],
        "event_time_generation": "ADDRESS_UINT32_REJECTION_SAMPLE_UNIFORM_WITHOUT_REPLACEMENT_3_OF_8_PER_BASIN",
    },
    "endpoint": {
        "formula": "0.65*(dw+de)/6 + 0.25*min(dw,de)/3 + 0.10*(1-waste)",
        "support": {"dw": [0, 3], "de": [0, 3], "waste": [0.0, 1.0]},
        "reduction": "BINARY64_DIRECT_EPISODE_PRIMITIVES",
    },
    "work_estimator": {
        "version": "FRRIE_STATIC_FLOP_ESTIMATOR_V2",
        "formula": "MODEL_AND_NATIVE_OPERATION_COUNT_NO_WALL_CLOCK_PROXY",
        "per_learned_arm_per_seed_block": {
            "factual_train_environment_slots": 393_216,
            "factual_audits_per_episode": 3,
            "counterfactual_alternatives_per_episode": 7,
            "counterfactual_alternative_environment_slots": 1_490_944,
            "factual_audit_environment_slots": 638_976,
            "alternative_suffix_environment_slots": 2_129_920,
            "learned_eval_environment_slots": 24_576,
            "environment_slots": 2_547_712,
            "base_policy_decisions": 4_718_592,
            "counterfactual_alternative_future_actor_steps": 1_261_568,
            "counterfactual_alternative_future_policy_decisions": 15_138_816,
            "factual_audit_future_actor_steps": 540_672,
            "factual_audit_future_policy_decisions": 6_488_064,
            "suffix_future_actor_steps": 1_802_240,
            "suffix_future_policy_decisions": 21_626_880,
            "learned_eval_policy_decisions": 313_344,
            "shadow_audit_policy_decisions": 82_944,
            "learned_decisions": 26_741_760,
            "backward_calls": 512, "adam_steps": 512,
            "parameter_bytes": 142_052, "checkpoint_io": 1,
            "evaluation_opportunities": 2_048,
            "checkpoint_conventional_flops": 1_958_344_320_512,
            "final_conventional_flops": 1_979_786_229_248,
        },
    },
    "package_relative_sources": [
        "__init__.py", "__main__.py", "analysis.py", "arms.py", "checkpoint.py",
        "cli.py", "contracts/__init__.py", "contracts/ccic_control.py",
        "contracts/core.py", "contracts/egrcr_control.py", "contracts/vqfp_controls.py",
        "controls/__init__.py", "controls/raw_value.py", "evaluator.py",
        "fixtures/ccic_control_v1.json", "fixtures/egrcr_control_v1.json",
        "fixtures/raw_value_v1.json", "fixtures/vqfp_controls_v1.json", "host.py",
        "lifecycle.py", "native/frrie_ridgegate2z_external.cpp",
        "native/native_abi.py", "native_adapter.py", "orchestration.py", "policy.py",
        "preflight.py", "rng.py", "runner.py", "state_codec.py", "tapes.py",
        "training.py", "work.py",
    ],
}
FIXTURE_CONTRACTS = {
    "ccic": {"schema": "FRRIE_CCIC_CONTROL_V1", "complete": True},
    "egrcr": {"schema": "FRRIE_EGRCR_CONTROL_V1", "complete": True},
    "raw_value": {"schema": "FRRIE_RAW_VALUE_CONTROL_V1", "complete": True},
    "vqfp": {
        "schema": "FRRIE_VQFP_CONTROLS_V1",
        "complete": True,
        "output_disconnected": True,
        "action_seam": "FRRIE_ACTION_SEAM_ABSENT",
    },
}
class ContractError(ValueError):
    """A frozen structural invariant is absent or false."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def manifest_packet_contract(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Direct packet binding projection, excluding its circular locator."""
    projection = deepcopy(dict(manifest))
    projection.pop("sealed_seed_packet", None)
    return projection


def expected_block_checkpoint_path(manifest: Mapping[str, Any], seed_block: str) -> Path:
    """Dependency-light direct path binding for the sole V2 block checkpoint."""
    if seed_block not in manifest.get("seed_blocks", ()):
        raise ContractError("checkpoint seed block is outside the manifest inventory")
    root = Path(manifest["roots"]["checkpoint"]).resolve(strict=False)
    target = (root / seed_block / "update-512.json").resolve(strict=False)
    if target == root or not target.is_relative_to(root):
        raise ContractError("block checkpoint path escapes the manifest checkpoint root")
    return target


def expected_native_contract_record(compute: Mapping[str, Any]) -> dict[str, Any]:
    """Dependency-light manifest-side native V2 record; loads no artifact."""
    return {
        "host_id": HOST_ID, "source_id": SOURCE_ID, "component": NATIVE_COMPONENT,
        "abi": NATIVE_ABI, "binding_kind": NATIVE_BINDING_KIND,
        "native_width": compute["native_width"], "workers": compute["workers"],
        "threads": compute["threads"], "dtype": "float32",
        "reduction_dtype": "float64", "device": "cpu",
        "python_fallback": False, "test_only": False,
    }


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{field} must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], required: Sequence[str], field: str) -> None:
    missing = set(required) - set(value)
    if missing:
        raise ContractError(f"{field} missing fields: {sorted(missing)}")
    extra = set(value) - set(required)
    if extra:
        raise ContractError(f"{field} has undeclared fields: {sorted(extra)}")


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractError(f"{field} must be a positive integer")
    return value


def _fresh_literal(value: Any, expected: str, field: str) -> None:
    if value != expected:
        raise ContractError(f"{field} must equal {expected!r}")


def expected_cells() -> tuple[tuple[str, int, str], ...]:
    return tuple(
        [("TRAIN", n, "INTACT") for n in TRAIN_ROSTERS]
        + [("EVALUATE", n, cut) for n in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS) for cut in INTERVENTIONS]
    )


def _validate_cells(rows: Any) -> None:
    if not isinstance(rows, list):
        raise ContractError("cells must be a list")
    observed: list[tuple[str, int, str]] = []
    for index, row0 in enumerate(rows):
        row = _mapping(row0, f"cells[{index}]")
        _exact_keys(row, ("purpose", "roster", "intervention", "episodes"), f"cells[{index}]")
        triple = (row["purpose"], row["roster"], row["intervention"])
        observed.append(triple)  # type: ignore[arg-type]
        expected_episodes = EPISODES_PER_UPDATE // 2 if row["purpose"] == "TRAIN" else EVALUATIONS_PER_CELL
        if row["episodes"] != expected_episodes:
            raise ContractError(f"cells[{index}].episodes must equal {expected_episodes}")
    if tuple(observed) != expected_cells():
        raise ContractError("cells must exactly equal the frozen ordered train/evaluation cells")


def _validate_arms(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) != 3:
        raise ContractError("arms must contain exactly three ordered records")
    expected = (
        ("PHY_TRUST", True, False, [-0.15, 0.15]),
        ("EDGE_FLEX", True, False, [-1.5, 1.5]),
        ("UNIFORM_LEGAL", False, True, None),
    )
    for index, (row0, wanted) in enumerate(zip(rows, expected)):
        row = _mapping(row0, f"arms[{index}]")
        _exact_keys(row, ("id", "learned", "evaluation_only", "beta_projection", "parameter_count"), f"arms[{index}]")
        got = (row.get("id"), row.get("learned"), row.get("evaluation_only"), row.get("beta_projection"))
        if got != wanted:
            raise ContractError(f"arms[{index}] violates the frozen learned/evaluation/projection contract")
        if row.get("parameter_count") != (MODEL_PARAMETER_COUNT if wanted[1] else 0):
            raise ContractError(f"arms[{index}].parameter_count is invalid")


def _validate_work(work0: Any, compute: Mapping[str, Any]) -> None:
    from ..work import planned_work

    work = _mapping(work0, "planned_work")
    try:
        exact = planned_work(compute)
    except ValueError as exc:
        raise ContractError(f"cannot bind planned_work: {exc}") from exc
    if dict(work) != exact:
        raise ContractError("planned_work must equal the exact per-arm/per-block v2 work vector")


def validate_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a detached manifest without inspecting result values."""
    manifest = _mapping(value, "manifest")
    required = (
        "schema", "direction_id", "experiment_id", "host", "arms", "cells", "compute",
        "training", "evaluation", "seed_blocks", "sealed_seed_packet",
        "preflight_receipt", "thresholds", "inference", "implementation_contract",
        "roots", "fixture_contracts", "planned_work", "resource_ceiling",
    )
    _exact_keys(manifest, required, "manifest")
    if manifest["schema"] != FRRIE_MANIFEST_V2:
        raise ContractError(f"production schema must equal {FRRIE_MANIFEST_V2}; V1 is legacy scaffold only")
    if manifest["direction_id"] != DIRECTION_ID:
        raise ContractError("direction_id mismatch")
    _fresh_literal(manifest["experiment_id"], EXPERIMENT_ID, "experiment_id")

    host = _mapping(manifest["host"], "host")
    _exact_keys(host, (
        "id", "source_id", "component", "abi", "binding_kind",
        "native_required", "python_fallback",
    ), "host")
    _fresh_literal(host["id"], HOST_ID, "host.id")
    _fresh_literal(host["source_id"], SOURCE_ID, "host.source_id")
    if host["component"] != NATIVE_COMPONENT or host["abi"] != NATIVE_ABI:
        raise ContractError("host component/ABI differs from the fresh FRRIE native contract")
    if host["binding_kind"] != NATIVE_BINDING_KIND:
        raise ContractError("host must use the external-step FRRIE V2 ctypes seam")
    if host["native_required"] is not True or host["python_fallback"] is not False:
        raise ContractError("production host must require native execution and forbid Python fallback")

    _validate_arms(manifest["arms"])
    _validate_cells(manifest["cells"])
    compute = _mapping(manifest["compute"], "compute")
    _exact_keys(compute, ("device", "gpu", "model_dtype", "reduction_dtype", "native_width", "workers", "threads", "network"), "compute")
    if (compute["device"], compute["gpu"], compute["model_dtype"], compute["reduction_dtype"], compute["network"]) != ("cpu", False, "float32", "float64", False):
        raise ContractError("compute must be CPU/FP32 with float64 reductions and no network")
    for field in ("native_width", "workers", "threads"):
        _positive_int(compute[field], f"compute.{field}")

    training = _mapping(manifest["training"], "training")
    _exact_keys(
        training,
        (
            "updates", "episodes_per_update", "rosters", "episodes_by_roster",
            "episode_roster_order", "checkpoints",
        ),
        "training",
    )
    if training["updates"] != UPDATES or training["episodes_per_update"] != EPISODES_PER_UPDATE:
        raise ContractError("training must use exactly 512 updates and 64 episodes/update")
    if training["rosters"] != list(TRAIN_ROSTERS) or training["episodes_by_roster"] != {"9": 32, "15": 32}:
        raise ContractError("each update must split episodes equally over N=9 and N=15")
    episode_roster_order = training["episode_roster_order"]
    if episode_roster_order != [9, 15] * 32:
        raise ContractError(
            "training.episode_roster_order must equal the exact alternating 64-position [9,15]*32 order"
        )
    checkpoints = training["checkpoints"]
    if checkpoints != [UPDATES]:
        raise ContractError("training checkpoint must be exactly [512], with no earlier evaluable checkpoint")

    evaluation = _mapping(manifest["evaluation"], "evaluation")
    _exact_keys(evaluation, ("episodes_per_cell", "adaptation", "seen_rosters", "heldout_rosters", "interventions"), "evaluation")
    if evaluation != {"episodes_per_cell": 256, "adaptation": False, "seen_rosters": [9, 15], "heldout_rosters": [6, 21], "interventions": list(INTERVENTIONS)}:
        raise ContractError("evaluation must be adaptation-free with 256 episodes per frozen cell")
    blocks = manifest["seed_blocks"]
    if blocks != list(REQUIRED_SEED_BLOCKS):
        raise ContractError("seed_blocks must be the exact ordered 24 FRRIE fresh-block labels")
    for binding_name in ("sealed_seed_packet", "preflight_receipt"):
        binding = _mapping(manifest[binding_name], binding_name)
        _exact_keys(binding, ("path",), binding_name)
        if not isinstance(binding["path"], str) or not binding["path"]:
            raise ContractError(f"{binding_name}.path must be discoverable")

    thresholds = _mapping(manifest["thresholds"], "thresholds")
    if dict(thresholds) != THRESHOLDS:
        raise ContractError("thresholds must equal the exact frozen eight-margin contract")
    inference = _mapping(manifest["inference"], "inference")
    if dict(inference) != INFERENCE_CONTRACT:
        raise ContractError("inference must preserve the exact 28-family order and explicit pending-method state")
    implementation = _mapping(manifest["implementation_contract"], "implementation_contract")
    if dict(implementation) != IMPLEMENTATION_CONTRACT:
        raise ContractError("implementation_contract differs from the exact dependency-light V2 implementation identity")

    roots = _mapping(manifest["roots"], "roots")
    if set(roots) != {"output", "checkpoint"} or not all(isinstance(v, str) and v for v in roots.values()):
        raise ContractError("fresh output and checkpoint roots are required")
    output_root = Path(roots["output"])
    checkpoint_root = Path(roots["checkpoint"])
    if not output_root.is_absolute() or not checkpoint_root.is_absolute():
        raise ContractError("fresh output and checkpoint roots must be absolute")
    output_resolved = output_root.resolve(strict=False)
    checkpoint_resolved = checkpoint_root.resolve(strict=False)
    if output_resolved == checkpoint_resolved:
        raise ContractError("output and checkpoint roots must be distinct")
    if output_resolved in checkpoint_resolved.parents or checkpoint_resolved in output_resolved.parents:
        raise ContractError("output and checkpoint roots must be non-nested and must not contain one another")
    if output_resolved.parent != checkpoint_resolved.parent:
        raise ContractError("output and checkpoint roots must be sibling children of one common run parent")
    fixtures = _mapping(manifest["fixture_contracts"], "fixture_contracts")
    _exact_keys(fixtures, tuple(FIXTURE_CONTRACTS), "fixture_contracts")
    if dict(fixtures) != FIXTURE_CONTRACTS:
        raise ContractError("FRRIE-owned fixture contracts do not match the frozen controls")

    resources = _mapping(manifest["resource_ceiling"], "resource_ceiling")
    if set(resources) != {"wall_seconds", "cpu_core_hours", "rss_bytes", "scratch_bytes", "durable_bytes"}:
        raise ContractError("all resource ceilings must be prospectively supplied")
    for field, number in resources.items():
        _positive_int(number, f"resource_ceiling.{field}")
    _validate_work(manifest["planned_work"], compute)
    canonical_json_bytes(manifest)
    return deepcopy(dict(manifest))


def load_manifest(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read manifest: {exc}") from exc
    return validate_manifest(value)


def structural_description() -> dict[str, Any]:
    """Public facts only; contains no threshold, seed, or scientific value."""
    return {
        "schema": FRRIE_MANIFEST_V2,
        "direction_id": DIRECTION_ID,
        "experiment_id": EXPERIMENT_ID,
        "host_id": HOST_ID,
        "learned_arms": list(LEARNED_ARMS),
        "evaluation_only_arm": EVALUATION_ONLY_ARM,
        "parameter_count": MODEL_PARAMETER_COUNT,
        "updates": UPDATES,
        "episodes_per_update": EPISODES_PER_UPDATE,
        "heldout_rosters": list(HELDOUT_ROSTERS),
        "seen_evaluation_rosters": list(TRAIN_ROSTERS),
        "evaluation_episodes_per_cell": EVALUATIONS_PER_CELL,
        "production_native_source_bundled": True,
        "production_native_prebuilt_artifact_bundled": False,
        "inference_ready": False,
        "READY": False,
        "vqfp_action_seam": "FRRIE_ACTION_SEAM_ABSENT",
    }
