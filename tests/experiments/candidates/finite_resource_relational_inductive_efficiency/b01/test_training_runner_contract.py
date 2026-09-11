from __future__ import annotations

import inspect
from copy import deepcopy
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.training_runner import (
    PILOT_PEAK_RSS_BYTES, PILOT_SCRATCH_DURABLE_BYTES, PILOT_WALL_SECONDS,
    assemble_slice_b_component_gate, exact512_induction_contract,
    plan_b1_exact512_component, validate_b4_induction_receipt,
    validate_exact512_transition_closure,
)


def _component(tmp_path: Path) -> dict:
    return {
        "schema": "FRRIE_B01_B1_EXACT512_COMPONENT_INPUT_V1",
        "component_root": str((tmp_path / "B1 component & exact512").resolve()),
        "axes": {
            "updates": {"start": 1, "stop_inclusive": 512, "count": 512},
            "checkpoints": [0, 32, 64, 128, 256, 512],
            "arms": ["PHY_TRUST", "EDGE_FLEX"],
            "roster_order": list((9, 15) * 32),
            "coordinate_order": ["update_1_512", "arm_PHY_THEN_EDGE"],
        },
        "work_contract": {
            "per_update_per_arm": {
                "factual": 768, "seven_nonfactual_alternatives": 2_912,
                "three_audits": 1_248, "total": 4_928,
            },
            "per_seed_per_arm": {
                "factual": 393_216, "seven_nonfactual_alternatives": 1_490_944,
                "three_audits": 638_976, "total": 2_523_136,
            },
        },
    }


def test_public_b1_component_seam_is_one_arg_pure_and_claim_limited(tmp_path):
    assert list(inspect.signature(plan_b1_exact512_component).parameters) == ["component"]
    component = _component(tmp_path)
    before_component = deepcopy(component)
    before_fs = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    plan = plan_b1_exact512_component(component)
    after_fs = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert component == before_component and before_fs == after_fs
    assert plan["schema"] == "FRRIE_B01_B1_EXACT512_COMPONENT_PLAN_V1"
    assert plan["component_contract"] == component
    assert plan["training_validation_replay_complete"] is False
    assert plan["parameter_distance_complete"] is False
    assert plan["launch_capable"] is False
    assert plan["result_bearing"] is False
    assert plan["production_token_minted"] is False
    assert plan["effect_count"] == 0
    assert plan["artifact_content_read"] is False
    gate = plan["static_full512_validation_gate"]
    assert gate["schema"] == "FRRIE_B01_B1_STATIC_FULL512_VALIDATION_GATE_V1"
    assert gate["transition_induction_contract"] == exact512_induction_contract()
    assert gate["b4_induction_receipt_complete"] is False
    assert gate["authoritative_full512_paired_shard_validation_executed"] is False
    assert gate["result_root_created"] is False
    assert gate["rng_model_optimizer_created"] is False
    assert gate["launch_capable"] is False
    assert gate["performance_disposition"] == "REPAIR_REQUIRED"
    assert gate["next_effect_requires_explicit_authorization"] is True


def test_b1_declares_distinct_contained_b2_b5_evidence_fields_and_locators(tmp_path):
    component = _component(tmp_path)
    plan = plan_b1_exact512_component(component)
    root = Path(component["component_root"])
    downstream = plan["required_downstream_evidence"]
    assert list(downstream) == ["B2", "B3", "B4", "B5"]
    expected = {
        "B2": (
            "B2-checkpoint-codec-inventory.json",
            [
                "schema", "seed_label", "checkpoint_schedule",
                "direct_checkpoint_inventory", "literal_codec_receipts", "complete",
            ],
        ),
        "B3": (
            "B3-exact512-paired-training-shards.json",
            [
                "schema", "seed_label", "arms", "updates_1_512",
                "typed_paired_training_shards", "loss_reduction_provenance",
                "scientific_work_ledger", "complete",
            ],
        ),
        "B4": (
            "B4-uninterrupted-resume-replay.json",
            [
                "schema", "seed_label", "checkpoint_schedule",
                "resume_suffix_contract", "literal_checkpoint_restore_inventory",
                "uninterrupted_suffix_receipts", "resumed_suffix_receipts",
                "direct_state_work_equality", "validation_replay_work", "complete",
            ],
        ),
        "B5": (
            "B5-kappa-parameter-panel-handoff.json",
            [
                "schema", "seed_label", "paired_training_validation_binding",
                "kappa_from_validated_training_ledger", "parameter_inventory_contract",
                "formal_parameter_distance_inventory", "complete_panel_handoff", "complete",
            ],
        ),
    }
    locators = []
    for slice_id, row in downstream.items():
        assert row["slice"] == slice_id
        assert row["required_fields"] == expected[slice_id][1]
        locator = Path(row["locator"])
        assert locator.name == expected[slice_id][0]
        assert locator.is_absolute() and locator.is_relative_to(root)
        assert not locator.exists()
        locators.append(locator)
    assert len(locators) == len(set(locators))
    assert plan["b1_direct_training_index_locator"] == str(
        root / "B1-direct-training-index.json"
    )
    assert not Path(plan["b1_direct_training_index_locator"]).exists()
    assert plan["residual_blockers"] == [
        "B2_CHECKPOINT_CODEC_AND_DIRECT_INVENTORY_NOT_PRODUCED",
        "B3_EXACT512_TYPED_PAIRED_TRAINING_SHARDS_NOT_PRODUCED",
        "B4_UNINTERRUPTED_RESUME_DIRECT_REPLAY_NOT_PRODUCED",
        "B5_KAPPA_PARAMETER_INVENTORY_AND_PANEL_HANDOFF_NOT_PRODUCED",
    ]


def test_b4_resume_suffix_and_b5_parameter_inventory_are_complete_and_literal(tmp_path):
    gate = plan_b1_exact512_component(_component(tmp_path))["static_full512_validation_gate"]
    b4 = gate["b4_resume_suffix_contract"]
    assert b4 == {
        "schema": "FRRIE_B01_B4_RESUME_SUFFIX_CONTRACT_V1",
        "checkpoint_schedule": [0, 32, 64, 128, 256, 512],
        "suffixes": [
            {"checkpoint": 0, "first_update": 1, "last_update": 512,
             "update_count": 512, "terminal_restore_only": False},
            {"checkpoint": 32, "first_update": 33, "last_update": 512,
             "update_count": 480, "terminal_restore_only": False},
            {"checkpoint": 64, "first_update": 65, "last_update": 512,
             "update_count": 448, "terminal_restore_only": False},
            {"checkpoint": 128, "first_update": 129, "last_update": 512,
             "update_count": 384, "terminal_restore_only": False},
            {"checkpoint": 256, "first_update": 257, "last_update": 512,
             "update_count": 256, "terminal_restore_only": False},
            {"checkpoint": 512, "first_update": None, "last_update": None,
             "update_count": 0, "terminal_restore_only": True},
        ],
        "arms": ["PHY_TRUST", "EDGE_FLEX"],
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
    b5 = gate["b5_kappa_parameter_inventory_contract"]
    assert b5["training_update_axis"] == {
        "start": 1, "stop_inclusive": 512, "count": 512,
    }
    assert b5["display_checkpoints"] == [0, 32, 64, 128, 256, 512]
    assert b5["kappa_source"] == (
        "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS"
    )
    assert b5["caller_supplied_kappa_allowed"] is False
    assert b5["parameter_layout"] == {
        "schema": "FRRIE_LAYER_SHAPES_V1",
        "parameter_count": 35_513,
        "parameter_byte_count": 142_052,
        "dtype": "IEEE754_BINARY32",
        "byte_order": "LITTLE_ENDIAN",
        "tensor_flattening": "C_ORDER",
        "tensor_order": [
            {"name": "message_encoder.weight_ih", "shape": [64, 22]},
            {"name": "message_encoder.bias_ih", "shape": [64]},
            {"name": "message_encoder.weight_ho", "shape": [32, 64]},
            {"name": "message_encoder.bias_ho", "shape": [32]},
            {"name": "gru.weight_input_zrn", "shape": [192, 55]},
            {"name": "gru.weight_hidden_zrn", "shape": [192, 64]},
            {"name": "gru.bias_zrn", "shape": [192]},
            {"name": "action_head.weight", "shape": [6, 64]},
            {"name": "action_head.bias", "shape": [6]},
            {"name": "beta", "shape": [3, 3, 2]},
            {"name": "critic.input.weight", "shape": [64, 66]},
            {"name": "critic.input.bias", "shape": [64]},
            {"name": "critic.hidden.weight", "shape": [64, 64]},
            {"name": "critic.hidden.bias", "shape": [64]},
            {"name": "critic.output.weight", "shape": [1, 64]},
            {"name": "critic.output.bias", "shape": [1]},
        ],
        "beta_flat_start": 26_982,
        "beta_flat_end_exclusive": 27_000,
        "beta_byte_start": 107_928,
        "beta_byte_end_exclusive": 108_000,
    }
    assert b5["postcontact_update_coverage"] == "KAPPA_THROUGH_512_INCLUSIVE"
    assert b5["no_contact_coverage"] == (
        "ALL_512_ROWS_UNAVAILABLE_NO_TIGHT_CONTACT_BY_512"
    )
    assert b5["distance_components"] == ["LINF_FULL", "LINF_BETA", "LINF_NONBETA"]
    assert b5["full_parameter_bytes_equal_field_required"] is True
    assert b5["temporal_reducer"] is None
    assert b5["scientific_gate"] is False
    assert b5["zero_imputation_allowed"] is False


@pytest.mark.parametrize("field", ["axes", "work_contract"])
def test_exact512_axes_and_work_are_literal(field, tmp_path):
    component = _component(tmp_path)
    if field == "axes":
        component[field]["checkpoints"] = [0, 32, 64, 128, 512]
    else:
        component[field]["per_update_per_arm"]["total"] = 4_927
    with pytest.raises(B01ContractError):
        plan_b1_exact512_component(component)


@pytest.mark.parametrize(
    "substitute",
    [
        {"training_validation_replay_complete": True},
        {"parameter_distance_complete": True},
        {"kappa": 17},
        {"training_hash": "not-direct-evidence"},
        {"summary": {"updates": 512}},
    ],
)
def test_summary_bool_hash_and_caller_kappa_substitutes_reject(tmp_path, substitute):
    component = {**_component(tmp_path), **substitute}
    with pytest.raises(B01ContractError, match="fields"):
        plan_b1_exact512_component(component)


def test_component_root_must_be_absolute_and_not_filesystem_anchor(tmp_path):
    relative = _component(tmp_path)
    relative["component_root"] = "relative/B1"
    with pytest.raises(B01ContractError, match="component root"):
        plan_b1_exact512_component(relative)
    anchored = _component(tmp_path)
    anchored["component_root"] = anchored["component_root"][:3]
    with pytest.raises(B01ContractError, match="component root"):
        plan_b1_exact512_component(anchored)


def _b4_receipt():
    return {
        "schema": "FRRIE_B01_B4_INDUCTION_RECEIPT_V1",
        "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001",
        "checkpoint_schedule": [0, 32, 64, 128, 256, 512],
        "base_checkpoint0": {
            "literal_restore_complete": True,
            "model_optimizer_bytes_equal": True,
            "zero_work_untouched_audit": True,
        },
        "nonterminal_probes": [
            {
                "checkpoint": checkpoint, "updates": [checkpoint + 1, checkpoint + 2],
                "literal_restore_complete": True,
                "uninterrupted_resumed_direct_equal": True,
                "typed_tape_address_equal": True, "native_work_equal": True,
                "frontier_equal": True, "loss_projection_equal": True,
                "fresh_spawned_resume_process": True,
                "fresh_native_adapter": True,
                "global_rng_states_perturbed": True,
                "audit_state_equal": True,
                "persistence_frontier_equal": True,
                "contact_audit_set_union_validated": (
                    True if checkpoint == 64 else None
                ),
                "checkpoint_prefix_role": (
                    "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK"
                ),
                "audit_branch_fixture": (
                    "POSTCONTACT_RESTORE" if checkpoint == 64 else "NO_CONTACT"
                ),
            }
            for checkpoint in (0, 32, 64, 128, 256)
        ],
        "terminal_checkpoint512": {
            "checkpoint": 512, "literal_restore_complete": True,
            "restore_only": True, "suffix_updates": [],
            "checkpoint_prefix_role": (
                "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK"
            ),
        },
        "rollback_fault": {
            "second_arm_failure_injected": True,
            "both_arm_model_optimizer_rollback_equal": True,
            "audit_and_uncommitted_work_rollback_equal": True,
            "direct_row_validation_failure_rolled_back": True,
            "paired_shard_append_faults_rolled_back": True,
            "checkpoint_write_readback_faults_rolled_back": True,
            "create_once_publication_faults_quarantined": True,
        },
        "tamper_matrix": {
            "injections": [
                "MODEL", "OPTIMIZER", "ADAM_STEP", "FRONTIER", "WORK",
                "AUDIT", "SEED_PHASE", "TAPE", "COMMON_MODE_TAPE", "ORIGIN_ADDRESS", "LAW_REVISION",
                "ROLE_MASK", "LOSS_BITS", "PROJECTION_MASK", "ROW_ORDER",
            ],
            "all_rejected": True,
        },
        "transition_induction_contract": exact512_induction_contract(),
        "resource_observation": {
            "wall_seconds": 240.0, "scratch_durable_bytes": 64 * 1024 * 1024,
            "peak_rss_bytes": 512 * 1024 * 1024,
            "admission_minimum_bytes": 4 * 1024 * 1024 * 1024,
            "active_supervisor_enforced": True,
        },
        "b4_complete": True, "test_component_only": True, "production_token": False,
    }


def test_induction_contract_closure_and_b4_b5_independence():
    contract = exact512_induction_contract()
    assert contract["closure"]["literal_python_range"] == [1, 513]
    assert contract["closure"]["update_order"] == list(range(1, 513))
    assert contract["b4_boundary_suffixes"] == {
        "0": [1, 2], "32": [33, 34], "64": [65, 66],
        "128": [129, 130], "256": [257, 258], "512": [],
    }
    assert contract["step"]["branch_matrix"] == [
        "NO_CONTACT_PRESTATE_EQUAL",
        "FIRST_FP32_CHANGING_PHY_PROJECTION_SETS_KAPPA",
        "POSTCONTACT_COMMON_EXOGENOUS_ONLY",
    ]
    assert contract["pilot_ceiling"] == {
        "wall_seconds": PILOT_WALL_SECONDS,
        "scratch_durable_bytes": PILOT_SCRATCH_DURABLE_BYTES,
        "peak_rss_bytes": PILOT_PEAK_RSS_BYTES,
        "memory_admission_minimum_bytes": 4 * 1024 * 1024 * 1024,
        "active_parent_process_tree_termination": True,
    }
    rows = (
        {
            "schema": "FRRIE_B01_ACTUAL_PAIRED_DIRECT_ROW_V1", "update": update,
            "typed_tape_address_equal": True, "native_work_equal": True,
            "outcome_equality_required": False, "test_component_only": True,
            "production_token": False,
        }
        for update in range(1, 513)
    )
    closure = validate_exact512_transition_closure(rows)
    assert closure["updates"] == 512 and closure["scientific_early_stop_observed"] is False
    seed = "FRRIE-B01-TEST-ONLY-BLOCK-001"
    b3 = {
        "schema": "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1",
        "seed_label": seed, "kappa": None,
        "phy_contacted_coordinate_indices": [],
        "phy_contacted_coordinate_count": 0, "edge_wide_contact": False,
        "parameter_distance_contract_status": "PRO_FINAL_RAW_RECORDS_REQUIRED",
        "parameter_distance_state_stage": "POSTPROJECTION",
        "parameter_distance_required_updates": [],
        "parameter_distance_raw_records": None,
        "raw_native_call_ledger_by_arm": {
            arm: {"reset_calls": 1, "observe_calls": 1, "step_calls": 1}
            for arm in ("PHY_TRUST", "EDGE_FLEX")
        },
        "precontact_and_contact_prestate_equal": True,
        "training_validation_replay_complete": False,
        "production_token_minted": False,
    }
    b5 = {
        "schema": "FRRIE_B01_FORMAL_PARAMETER_DISTANCE_INVENTORY_V1",
        "seed_block": seed, "first_tight_contact_update": None,
        "records": [
            {"seed_block": seed, "training_update": update, "available": False,
             "availability_reason": "NO_TIGHT_CONTACT_BY_512"}
            for update in range(1, 513)
        ],
        "record_count": 512, "available_count": 0,
        "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        "temporal_reducer": None, "included_in_ordered_28": False,
        "kappa_source": "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS",
        "paired_training_schema": "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1",
        "paired_training_state_chain_revalidated": True,
        "required_postcontact_updates": [],
        "caller_supplied_kappa_accepted": False, "production_gate": False,
    }
    without_b4 = assemble_slice_b_component_gate(
        b3_receipt=b3, b4_receipt=None, b5_receipt=b5,
    )
    assert without_b4["b3_complete"] is True
    assert without_b4["b5_complete"] is True
    assert without_b4["b4_complete"] is False
    assert without_b4["slice_b_component_complete"] is False
    assert without_b4["launch_capable"] is False
    complete = assemble_slice_b_component_gate(
        b3_receipt=b3,
        b4_receipt=validate_b4_induction_receipt(_b4_receipt()), b5_receipt=b5,
    )
    assert complete["slice_b_component_complete"] is True
    assert complete["b5_can_imply_b4"] is False
    assert complete["launch_capable"] is False


@pytest.mark.parametrize("tamper", ["suffix", "terminal", "rollback", "resource", "b5"])
def test_b4_induction_tamper_matrix_is_fail_closed(tamper):
    receipt = _b4_receipt()
    if tamper == "suffix":
        receipt["nonterminal_probes"][2]["updates"] = [65]
    elif tamper == "terminal":
        receipt["terminal_checkpoint512"]["suffix_updates"] = [513]
    elif tamper == "rollback":
        receipt["rollback_fault"]["audit_and_uncommitted_work_rollback_equal"] = False
    elif tamper == "resource":
        receipt["resource_observation"]["wall_seconds"] = PILOT_WALL_SECONDS + 0.001
    else:
        receipt["formal_parameter_distance_inventory"] = {"complete": True}
    with pytest.raises(B01ContractError):
        validate_b4_induction_receipt(receipt)


def test_slice_b_gate_rejects_selected_field_b5_forgery_without_b3():
    forged = {
        "schema": "FRRIE_B01_FORMAL_PARAMETER_DISTANCE_INVENTORY_V1",
        "record_count": 512,
        "kappa_source": "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS",
        "caller_supplied_kappa_accepted": False, "production_gate": False,
    }
    with pytest.raises(B01ContractError, match="B5 formal receipt fields"):
        assemble_slice_b_component_gate(
            b3_receipt=None, b4_receipt=None, b5_receipt=forged,
        )
