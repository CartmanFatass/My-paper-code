"""Pure B1 exact-512 component planning; no training or artifact effects."""

from __future__ import annotations

from copy import deepcopy
from math import prod
from pathlib import Path
from typing import Any, Mapping

from ..arms import LAYER_SHAPES, PARAMETER_BYTE_COUNT
from .constants import (
    CHECKPOINTS, LEARNED_ARMS, TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED,
    TRAIN_AUDIT_WORK_PER_ARM_SEED, TRAIN_FACTUAL_WORK_PER_ARM_SEED,
    TRAIN_ROSTER_ORDER, TRAIN_TOTAL_WORK_PER_ARM_SEED, UPDATES,
)
from .contract import B01ContractError


PILOT_WALL_SECONDS = 600
PILOT_SCRATCH_DURABLE_BYTES = 128 * 1024 * 1024
PILOT_PEAK_RSS_BYTES = 1536 * 1024 * 1024
PILOT_BOUNDARY_SUFFIXES = {
    0: (1, 2), 32: (33, 34), 64: (65, 66),
    128: (129, 130), 256: (257, 258), 512: (),
}


def exact512_induction_contract() -> dict[str, Any]:
    """Pure closure contract; this does not claim any transition executed."""

    return {
        "schema": "FRRIE_B01_EXACT512_TRANSITION_INDUCTION_CONTRACT_V1",
        "base": {
            "checkpoint": 0,
            "required": [
                "LITERAL_WRITE_REOPEN_DECODE_TEMPORARY_RESTORE",
                "PAIRED_MODEL_OPTIMIZER_BYTES_EQUAL",
                "ZERO_WORK_AND_UNTOUCHED_AUDIT",
            ],
        },
        "step": {
            "updates": {"start": 1, "stop_inclusive": 512, "count": 512},
            "single_unbypassable_path": [
                "ACTUAL_NATIVE_COLLECTOR", "PAIRED_TRANSACTIONAL_TRAINER",
                "ACTUAL_TYPED_DIRECT_ROW", "STREAMING_ROW_VALIDATION",
            ],
            "state_fields": [
                "UPDATE", "PAIRED_MODEL_BYTES", "PAIRED_OPTIMIZER_BYTES_AND_STEP",
                "FIRST_TIGHT_CONTACT", "EXACT_CHANGED_COORDINATE_SET",
                "PRECONTACT_EQUALITY", "WIDE_CONTACT", "MAXIMUM_OVERSHOOT",
                "CUMULATIVE_DISPLACEMENT", "CUMULATIVE_WORK_FRONTIER",
            ],
            "input_fields": [
                "TAPE_BYTES", "TAPE_COORDINATES", "LAW_REVISIONS", "ROLES_MASKS",
                "ORIGIN_COORDINATES", "ORIGIN_ADDRESSES", "ROSTER_ORDER",
            ],
            "rollback": [
                "FAILED_SECOND_ARM_RESTORES_BOTH_ARMS_AUDIT_AND_UNCOMMITTED_WORK",
                "PAIRED_SHARD_APPEND_TRUNCATES_BOTH_TO_PRIOR_OFFSETS",
                "CHECKPOINT_WRITE_READBACK_LEAVES_NO_VISIBLE_CHECKPOINT",
                "CREATE_ONCE_PUBLICATION_FAILURE_QUARANTINES_TRANSACTION",
            ],
            "branch_matrix": [
                "NO_CONTACT_PRESTATE_EQUAL",
                "FIRST_FP32_CHANGING_PHY_PROJECTION_SETS_KAPPA",
                "POSTCONTACT_COMMON_EXOGENOUS_ONLY",
            ],
        },
        "closure": {
            "literal_python_range": [1, 513],
            "update_order": list(range(1, 513)),
            "checkpoint_schedule": list(CHECKPOINTS),
            "row_count": 512,
            "scientific_early_stop": False,
            "future_actual_rows_require_direct_streaming_revalidation": True,
        },
        "b4_boundary_suffixes": {
            str(checkpoint): list(updates)
            for checkpoint, updates in PILOT_BOUNDARY_SUFFIXES.items()
        },
        "pilot_ceiling": {
            "wall_seconds": PILOT_WALL_SECONDS,
            "scratch_durable_bytes": PILOT_SCRATCH_DURABLE_BYTES,
            "peak_rss_bytes": PILOT_PEAK_RSS_BYTES,
            "memory_admission_minimum_bytes": 4 * 1024 * 1024 * 1024,
            "active_parent_process_tree_termination": True,
        },
        "test_component_only": True, "result_bearing": False,
        "scientific_values": None, "launch_capable": False,
        "performance_disposition": "PILOT_ONLY",
    }


def validate_exact512_transition_closure(rows: Any) -> dict[str, Any]:
    """Single-pass closure over 512 direct-row receipts; no artifact contents inferred."""

    count = 0
    fields = {
        "schema", "update", "typed_tape_address_equal", "native_work_equal",
        "outcome_equality_required", "test_component_only", "production_token",
    }
    for expected, row in enumerate(rows, start=1):
        if expected > UPDATES:
            raise B01ContractError("exact512 closure contains more than 512 updates")
        if (
            not isinstance(row, Mapping) or set(row) != fields
            or row.get("schema") != "FRRIE_B01_ACTUAL_PAIRED_DIRECT_ROW_V1"
            or row.get("update") != expected
            or row.get("typed_tape_address_equal") is not True
            or row.get("native_work_equal") is not True
            or row.get("outcome_equality_required") is not False
            or row.get("test_component_only") is not True
            or row.get("production_token") is not False
        ):
            raise B01ContractError("exact512 closure direct row differs")
        count += 1
    if count != UPDATES:
        raise B01ContractError("exact512 closure requires exactly 512 ordered rows")
    return {
        "schema": "FRRIE_B01_EXACT512_TRANSITION_CLOSURE_COMPONENT_V1",
        "updates": UPDATES, "update_order": [1, 512],
        "all_typed_tape_address_equal": True, "all_native_work_equal": True,
        "scientific_early_stop_observed": False,
        "actual_future_artifact_content_claimed": False,
        "test_component_only": True, "production_token": False,
    }


def validate_b4_induction_receipt(value: Any) -> dict[str, Any]:
    """Validate B4 independently; B5 fields or replay booleans are never accepted."""

    fields = {
        "schema", "seed_label", "checkpoint_schedule", "base_checkpoint0",
        "nonterminal_probes", "terminal_checkpoint512", "rollback_fault",
        "tamper_matrix", "transition_induction_contract", "resource_observation",
        "b4_complete", "test_component_only", "production_token",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("B4 induction receipt fields differ")
    receipt = dict(value)
    if (
        receipt["schema"] != "FRRIE_B01_B4_INDUCTION_RECEIPT_V1"
        or receipt["checkpoint_schedule"] != list(CHECKPOINTS)
        or receipt["transition_induction_contract"] != exact512_induction_contract()
        or receipt["test_component_only"] is not True
        or receipt["production_token"] is not False
        or receipt["b4_complete"] is not True
    ):
        raise B01ContractError("B4 induction receipt identity/claim ceiling differs")
    base = receipt["base_checkpoint0"]
    if not isinstance(base, Mapping) or set(base) != {
        "literal_restore_complete", "model_optimizer_bytes_equal",
        "zero_work_untouched_audit",
    } or any(base[field] is not True for field in base):
        raise B01ContractError("B4 checkpoint0 base differs")
    probes = receipt["nonterminal_probes"]
    expected_checkpoints = list(CHECKPOINTS[:-1])
    if (
        not isinstance(probes, list)
        or any(not isinstance(row, Mapping) for row in probes)
        or [row.get("checkpoint") for row in probes] != expected_checkpoints
    ):
        raise B01ContractError("B4 nonterminal checkpoint probe inventory differs")
    for row in probes:
        checkpoint = row["checkpoint"]
        if set(row) != {
            "checkpoint", "updates", "literal_restore_complete",
            "uninterrupted_resumed_direct_equal", "typed_tape_address_equal",
            "native_work_equal", "frontier_equal", "loss_projection_equal",
            "checkpoint_prefix_role", "audit_branch_fixture",
            "fresh_spawned_resume_process", "fresh_native_adapter",
            "global_rng_states_perturbed", "audit_state_equal",
            "persistence_frontier_equal", "contact_audit_set_union_validated",
        } or row["updates"] != list(PILOT_BOUNDARY_SUFFIXES[checkpoint]) or any(
            row[field] is not True for field in set(row) - {
                "checkpoint", "updates", "checkpoint_prefix_role",
                "audit_branch_fixture", "contact_audit_set_union_validated",
            }
        ) or row["checkpoint_prefix_role"] != (
            "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK"
        ) or row["audit_branch_fixture"] not in (
            "NO_CONTACT", "POSTCONTACT_RESTORE",
        ) or row["contact_audit_set_union_validated"] is not (
            True if checkpoint == 64 else None
        ):
            raise B01ContractError("B4 nonterminal suffix probe differs")
    if {row["audit_branch_fixture"] for row in probes} != {
        "NO_CONTACT", "POSTCONTACT_RESTORE",
    }:
        raise B01ContractError("B4 contact/no-contact branch fixture coverage differs")
    if receipt["terminal_checkpoint512"] != {
        "checkpoint": 512, "literal_restore_complete": True,
        "restore_only": True, "suffix_updates": [],
        "checkpoint_prefix_role": "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK",
    }:
        raise B01ContractError("B4 terminal restore-only probe differs")
    if receipt["rollback_fault"] != {
        "second_arm_failure_injected": True,
        "both_arm_model_optimizer_rollback_equal": True,
        "audit_and_uncommitted_work_rollback_equal": True,
        "direct_row_validation_failure_rolled_back": True,
        "paired_shard_append_faults_rolled_back": True,
        "checkpoint_write_readback_faults_rolled_back": True,
        "create_once_publication_faults_quarantined": True,
    }:
        raise B01ContractError("B4 paired rollback fault receipt differs")
    expected_tampers = [
        "MODEL", "OPTIMIZER", "ADAM_STEP", "FRONTIER", "WORK",
        "AUDIT", "SEED_PHASE", "TAPE", "COMMON_MODE_TAPE", "ORIGIN_ADDRESS", "LAW_REVISION",
        "ROLE_MASK", "LOSS_BITS", "PROJECTION_MASK", "ROW_ORDER",
    ]
    if receipt["tamper_matrix"] != {
        "injections": expected_tampers, "all_rejected": True,
    }:
        raise B01ContractError("B4 tamper matrix differs")
    resource = receipt["resource_observation"]
    if (
        not isinstance(resource, Mapping)
        or set(resource) != {
            "wall_seconds", "scratch_durable_bytes", "peak_rss_bytes",
            "admission_minimum_bytes", "active_supervisor_enforced",
        }
        or isinstance(resource.get("wall_seconds"), bool)
        or not isinstance(resource.get("wall_seconds"), (int, float))
        or not 0 <= resource["wall_seconds"] <= PILOT_WALL_SECONDS
        or any(
            type(resource.get(field)) is not int or resource[field] < 0
            for field in (
                "scratch_durable_bytes", "peak_rss_bytes", "admission_minimum_bytes",
            )
        )
        or resource["scratch_durable_bytes"] > PILOT_SCRATCH_DURABLE_BYTES
        or resource["peak_rss_bytes"] > PILOT_PEAK_RSS_BYTES
        or resource["admission_minimum_bytes"] < 4 * 1024 * 1024 * 1024
        or resource["active_supervisor_enforced"] is not True
    ):
        raise B01ContractError("B4 pilot resource observation exceeds its ceiling")
    return receipt


def assemble_slice_b_component_gate(
    *, b3_receipt: Mapping[str, Any] | None,
    b4_receipt: Mapping[str, Any] | None,
    b5_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Consume exact validated B3/B4/B5 receipts; no caller booleans suffice."""

    b3_complete = False
    if b3_receipt is not None:
        fields = {
            "schema", "seed_label", "kappa", "phy_contacted_coordinate_indices",
            "phy_contacted_coordinate_count", "edge_wide_contact",
            "parameter_distance_contract_status", "parameter_distance_state_stage",
            "parameter_distance_required_updates", "parameter_distance_raw_records",
            "raw_native_call_ledger_by_arm", "precontact_and_contact_prestate_equal",
            "training_validation_replay_complete", "production_token_minted",
        }
        if not isinstance(b3_receipt, Mapping) or set(b3_receipt) != fields or (
            b3_receipt.get("schema")
            != "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1"
            or not isinstance(b3_receipt.get("seed_label"), str)
            or b3_receipt.get("precontact_and_contact_prestate_equal") is not True
            or b3_receipt.get("training_validation_replay_complete") is not False
            or b3_receipt.get("production_token_minted") is not False
            or b3_receipt.get("parameter_distance_state_stage") != "POSTPROJECTION"
        ):
            raise B01ContractError("Slice-B B3 validated paired receipt differs")
        kappa = b3_receipt["kappa"]
        if kappa is not None and (type(kappa) is not int or not 1 <= kappa <= UPDATES):
            raise B01ContractError("Slice-B B3 kappa differs")
        wanted = [] if kappa is None else list(range(kappa, UPDATES + 1))
        ledgers = b3_receipt["raw_native_call_ledger_by_arm"]
        indices = b3_receipt["phy_contacted_coordinate_indices"]
        if (
            not isinstance(indices, list) or indices != sorted(set(indices))
            or any(type(index) is not int or not 0 <= index < 18 for index in indices)
            or b3_receipt["phy_contacted_coordinate_count"] != len(indices)
            or (kappa is None and indices != []) or (kappa is not None and not indices)
            or type(b3_receipt["edge_wide_contact"]) is not bool
            or b3_receipt["parameter_distance_contract_status"]
            != "PRO_FINAL_RAW_RECORDS_REQUIRED"
            or b3_receipt["parameter_distance_required_updates"] != wanted
            or b3_receipt["parameter_distance_raw_records"] is not None
            or not isinstance(ledgers, Mapping) or set(ledgers) != set(LEARNED_ARMS)
            or any(
                not isinstance(ledgers[arm], Mapping)
                or set(ledgers[arm]) != {"reset_calls", "observe_calls", "step_calls"}
                or not all(type(value) is int and value > 0 for value in ledgers[arm].values())
                for arm in LEARNED_ARMS
            )
        ):
            raise B01ContractError("Slice-B B3 coverage/native receipt differs")
        b3_complete = True
    b4_complete = False
    if b4_receipt is not None:
        validate_b4_induction_receipt(b4_receipt)
        b4_complete = True
    b5_complete = False
    if b5_receipt is not None:
        fields = {
            "schema", "seed_block", "first_tight_contact_update", "records",
            "record_count", "available_count", "measurement_role", "temporal_reducer",
            "included_in_ordered_28", "production_gate", "kappa_source",
            "paired_training_schema", "paired_training_state_chain_revalidated",
            "required_postcontact_updates", "caller_supplied_kappa_accepted",
        }
        if not isinstance(b5_receipt, Mapping) or set(b5_receipt) != fields:
            raise B01ContractError("Slice-B B5 formal receipt fields differ")
        kappa = b5_receipt["first_tight_contact_update"]
        if kappa is not None and (type(kappa) is not int or not 1 <= kappa <= UPDATES):
            raise B01ContractError("Slice-B B5 kappa differs")
        wanted = [] if kappa is None else list(range(kappa, UPDATES + 1))
        records = b5_receipt["records"]
        if (
            b5_receipt["schema"] != "FRRIE_B01_FORMAL_PARAMETER_DISTANCE_INVENTORY_V1"
            or b5_receipt["record_count"] != UPDATES
            or not isinstance(records, list) or len(records) != UPDATES
            or any(not isinstance(row, Mapping) for row in records)
            or [row.get("training_update") for row in records] != list(range(1, UPDATES + 1))
            or any(row.get("seed_block") != b5_receipt["seed_block"] for row in records)
            or b5_receipt["available_count"] != sum(
                row.get("available") is True for row in records
            )
            or b5_receipt["kappa_source"]
            != "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS"
            or b5_receipt["paired_training_schema"]
            != "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1"
            or b5_receipt["paired_training_state_chain_revalidated"] is not True
            or b5_receipt["required_postcontact_updates"] != wanted
            or b5_receipt["caller_supplied_kappa_accepted"] is not False
            or b5_receipt["measurement_role"] != "MANDATORY_DESCRIPTIVE_NON_GATE"
            or b5_receipt["temporal_reducer"] is not None
            or b5_receipt["included_in_ordered_28"] is not False
            or b5_receipt["production_gate"] is not False
        ):
            raise B01ContractError("Slice-B B5 formal receipt content differs")
        b5_complete = True
    if b3_complete and b5_complete and (
        b3_receipt["seed_label"] != b5_receipt["seed_block"]
        or b3_receipt["kappa"] != b5_receipt["first_tight_contact_update"]
    ):
        raise B01ContractError("Slice-B B3/B5 source binding differs")
    return {
        "schema": "FRRIE_B01_SLICE_B_COMPONENT_GATE_V1",
        "b3_complete": b3_complete, "b4_complete": b4_complete,
        "b5_complete": b5_complete,
        "b5_can_imply_b4": False,
        "slice_b_component_complete": b3_complete and b4_complete and b5_complete,
        "launch_capable": False, "result_bearing": False,
        "performance_disposition": "REPAIR_REQUIRED",
        "production_token": False,
    }


def _resume_suffix_contract() -> dict[str, Any]:
    suffixes = []
    for checkpoint in CHECKPOINTS:
        first = checkpoint + 1 if checkpoint < UPDATES else None
        suffixes.append({
            "checkpoint": checkpoint,
            "first_update": first,
            "last_update": UPDATES if first is not None else None,
            "update_count": UPDATES - checkpoint,
            "terminal_restore_only": checkpoint == UPDATES,
        })
    return {
        "schema": "FRRIE_B01_B4_RESUME_SUFFIX_CONTRACT_V1",
        "checkpoint_schedule": list(CHECKPOINTS),
        "suffixes": suffixes,
        "arms": list(LEARNED_ARMS),
        "literal_checkpoint_reopen_decode_temporary_restore_required": True,
        "direct_row_validation_required": True,
        "uninterrupted_resumed_exact_byte_equality_required": True,
        "nonterminal_state_chain_from_checkpoint_required": True,
        "terminal_checkpoint_512_requires_literal_restore_not_suffix": True,
        "work_and_loss_receipt_equality_required": True,
        "rng_tape_address_equality_required": True,
        "digest_or_summary_substitute_allowed": False,
        "scientific_early_stop_allowed": False,
    }


def _parameter_inventory_contract() -> dict[str, Any]:
    tensor_order = [
        {"name": name, "shape": list(shape)} for name, shape in LAYER_SHAPES
    ]
    if (
        sum(prod(row["shape"]) for row in tensor_order) != 35_513
        or PARAMETER_BYTE_COUNT != 142_052
        or tensor_order[9] != {"name": "beta", "shape": [3, 3, 2]}
    ):
        raise B01ContractError("B5 actual parameter layout differs from the frozen inventory")
    return {
        "schema": "FRRIE_B01_B5_KAPPA_PARAMETER_INVENTORY_CONTRACT_V1",
        "training_update_axis": {
            "start": 1, "stop_inclusive": UPDATES, "count": UPDATES,
        },
        "display_checkpoints": list(CHECKPOINTS),
        "kappa_source": "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS",
        "kappa_law": (
            "FIRST_PHY_POST_ADAM_TO_POSTPROJECTION_STORED_FP32_BYTE_CHANGE"
        ),
        "caller_supplied_kappa_allowed": False,
        "no_contact_kappa": None,
        "state_stage": "POSTPROJECTION",
        "parameter_layout": {
            "schema": "FRRIE_LAYER_SHAPES_V1",
            "parameter_count": 35_513,
            "parameter_byte_count": 142_052,
            "dtype": "IEEE754_BINARY32",
            "byte_order": "LITTLE_ENDIAN",
            "tensor_flattening": "C_ORDER",
            "tensor_order": tensor_order,
            "beta_flat_start": 26_982,
            "beta_flat_end_exclusive": 27_000,
            "beta_byte_start": 107_928,
            "beta_byte_end_exclusive": 108_000,
        },
        "postcontact_update_coverage": "KAPPA_THROUGH_512_INCLUSIVE",
        "no_contact_coverage": "ALL_512_ROWS_UNAVAILABLE_NO_TIGHT_CONTACT_BY_512",
        "checkpoint_state_source": "LITERAL_ARM_CHECKPOINT_STATE_BYTES",
        "noncheckpoint_state_source": "WRITE_ONCE_NONRESUMABLE_PAIRED_PARAMETER_STATE",
        "distance_components": ["LINF_FULL", "LINF_BETA", "LINF_NONBETA"],
        "full_parameter_bytes_equal_field_required": True,
        "temporal_reducer": None,
        "scientific_gate": False,
        "zero_imputation_allowed": False,
    }


def _static_validation_gate() -> dict[str, Any]:
    return {
        "schema": "FRRIE_B01_B1_STATIC_FULL512_VALIDATION_GATE_V1",
        "transition_induction_contract": exact512_induction_contract(),
        "b4_resume_suffix_contract": _resume_suffix_contract(),
        "b5_kappa_parameter_inventory_contract": _parameter_inventory_contract(),
        "b4_induction_receipt_complete": False,
        "authoritative_full512_paired_shard_validation_executed": False,
        "result_root_created": False,
        "rng_model_optimizer_created": False,
        "launch_capable": False,
        "performance_disposition": "REPAIR_REQUIRED",
        "next_effect_requires_explicit_authorization": True,
    }


def _exact_axes() -> dict[str, Any]:
    return {
        "updates": {"start": 1, "stop_inclusive": UPDATES, "count": UPDATES},
        "checkpoints": list(CHECKPOINTS),
        "arms": list(LEARNED_ARMS),
        "roster_order": list(TRAIN_ROSTER_ORDER),
        "coordinate_order": ["update_1_512", "arm_PHY_THEN_EDGE"],
    }


def _exact_work() -> dict[str, Any]:
    return {
        "per_update_per_arm": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED // UPDATES,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED // UPDATES,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED // UPDATES,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED // UPDATES,
        },
        "per_seed_per_arm": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED,
        },
    }


def _component_root(value: Any) -> Path:
    if type(value) is not str or not value.strip():
        raise B01ContractError("B1 component root is absent")
    literal = Path(value)
    if not literal.is_absolute() or ".." in literal.parts:
        raise B01ContractError("B1 component root must be one literal absolute path")
    root = literal.resolve(strict=False)
    if root == Path(root.anchor).resolve(strict=False) or not root.name:
        raise B01ContractError("B1 component root cannot be a filesystem anchor")
    if root.exists():
        raise B01ContractError("B1 component root is not fresh")
    return root


def _downstream(root: Path) -> dict[str, dict[str, Any]]:
    specifications = (
        (
            "B2", "B2-checkpoint-codec-inventory.json",
            [
                "schema", "seed_label", "checkpoint_schedule",
                "direct_checkpoint_inventory", "literal_codec_receipts", "complete",
            ],
        ),
        (
            "B3", "B3-exact512-paired-training-shards.json",
            [
                "schema", "seed_label", "arms", "updates_1_512",
                "typed_paired_training_shards", "loss_reduction_provenance",
                "scientific_work_ledger", "complete",
            ],
        ),
        (
            "B4", "B4-uninterrupted-resume-replay.json",
            [
                "schema", "seed_label", "checkpoint_schedule",
                "resume_suffix_contract",
                "literal_checkpoint_restore_inventory",
                "uninterrupted_suffix_receipts", "resumed_suffix_receipts",
                "direct_state_work_equality", "validation_replay_work", "complete",
            ],
        ),
        (
            "B5", "B5-kappa-parameter-panel-handoff.json",
            [
                "schema", "seed_label", "paired_training_validation_binding",
                "kappa_from_validated_training_ledger", "parameter_inventory_contract",
                "formal_parameter_distance_inventory", "complete_panel_handoff", "complete",
            ],
        ),
    )
    return {
        slice_id: {
            "slice": slice_id,
            "required_fields": list(fields),
            "locator": str((root / filename).resolve(strict=False)),
            "content_read": False,
            "complete": False,
        }
        for slice_id, filename, fields in specifications
    }


def _validate_plan(plan: Any, component: Mapping[str, Any], root: Path) -> dict[str, Any]:
    fields = {
        "schema", "component_contract", "b1_direct_training_index_locator",
        "required_downstream_evidence", "training_validation_replay_complete",
        "parameter_distance_complete", "launch_capable", "result_bearing",
        "production_token_minted", "effect_count", "artifact_content_read",
        "public_launch_seam", "static_full512_validation_gate", "residual_blockers",
    }
    if not isinstance(plan, Mapping) or set(plan) != fields:
        raise B01ContractError("B1 component plan fields differ")
    value = dict(plan)
    expected_downstream = _downstream(root)
    own_locator = (root / "B1-direct-training-index.json").resolve(strict=False)
    if (
        value["schema"] != "FRRIE_B01_B1_EXACT512_COMPONENT_PLAN_V1"
        or value["component_contract"] != component
        or value["b1_direct_training_index_locator"] != str(own_locator)
        or value["required_downstream_evidence"] != expected_downstream
        or value["training_validation_replay_complete"] is not False
        or value["parameter_distance_complete"] is not False
        or value["launch_capable"] is not False
        or value["result_bearing"] is not False
        or value["production_token_minted"] is not False
        or value["effect_count"] != 0
        or value["artifact_content_read"] is not False
        or value["public_launch_seam"] is not False
        or value["static_full512_validation_gate"] != _static_validation_gate()
        or value["residual_blockers"] != [
            "B2_CHECKPOINT_CODEC_AND_DIRECT_INVENTORY_NOT_PRODUCED",
            "B3_EXACT512_TYPED_PAIRED_TRAINING_SHARDS_NOT_PRODUCED",
            "B4_UNINTERRUPTED_RESUME_DIRECT_REPLAY_NOT_PRODUCED",
            "B5_KAPPA_PARAMETER_INVENTORY_AND_PANEL_HANDOFF_NOT_PRODUCED",
        ]
    ):
        raise B01ContractError("B1 component claim ceiling/derivation differs")
    locators = [own_locator] + [
        Path(row["locator"]) for row in expected_downstream.values()
    ]
    if (
        len(locators) != len(set(locators))
        or any(not path.is_relative_to(root) or path.exists() for path in locators)
    ):
        raise B01ContractError("B1 component locators are not distinct/fresh/contained")
    return value


def plan_b1_exact512_component(component: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one exact B1 index and return a zero-effect downstream plan."""

    fields = {"schema", "component_root", "axes", "work_contract"}
    if not isinstance(component, Mapping) or set(component) != fields:
        raise B01ContractError("B1 component input fields differ")
    if (
        component["schema"] != "FRRIE_B01_B1_EXACT512_COMPONENT_INPUT_V1"
        or component["axes"] != _exact_axes()
        or component["work_contract"] != _exact_work()
    ):
        raise B01ContractError("B1 exact512 axes/work contract differs")
    root = _component_root(component["component_root"])
    downstream = _downstream(root)
    plan = {
        "schema": "FRRIE_B01_B1_EXACT512_COMPONENT_PLAN_V1",
        "component_contract": deepcopy(dict(component)),
        "b1_direct_training_index_locator": str(
            (root / "B1-direct-training-index.json").resolve(strict=False)
        ),
        "required_downstream_evidence": downstream,
        "training_validation_replay_complete": False,
        "parameter_distance_complete": False,
        "launch_capable": False,
        "result_bearing": False,
        "production_token_minted": False,
        "effect_count": 0,
        "artifact_content_read": False,
        "public_launch_seam": False,
        "static_full512_validation_gate": _static_validation_gate(),
        "residual_blockers": [
            "B2_CHECKPOINT_CODEC_AND_DIRECT_INVENTORY_NOT_PRODUCED",
            "B3_EXACT512_TYPED_PAIRED_TRAINING_SHARDS_NOT_PRODUCED",
            "B4_UNINTERRUPTED_RESUME_DIRECT_REPLAY_NOT_PRODUCED",
            "B5_KAPPA_PARAMETER_INVENTORY_AND_PANEL_HANDOFF_NOT_PRODUCED",
        ],
    }
    return _validate_plan(plan, component, root)
