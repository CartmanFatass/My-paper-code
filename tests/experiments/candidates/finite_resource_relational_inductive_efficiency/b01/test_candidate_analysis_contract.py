from __future__ import annotations

from copy import deepcopy
from itertools import islice
from pathlib import Path
from types import SimpleNamespace

import pytest
import numpy as np
from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
    exact_loss_reduction_contract,
)

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.analysis import (
    candidate_test_quantity_values, quantity_values_from_validated_cells,
    summarize_candidate_quantities, summarize_between_arm_tv,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    CHECKPOINTS, QUANTITY_ORDER, ROOT_LABELS,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, exact_descriptive_contract, exact_formal_runner_contract,
    validate_manifest,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.panel import (
    exact_inventory_cardinalities, iter_arm_update_coordinates,
    iter_checkpoint_restore_coordinates, iter_primitive_coordinates,
    iter_quantity_coordinates, iter_shadow_action_pair_coordinates,
    validate_candidate_primitive_shard, validate_direct_primitive_trace_shard,
    validate_direct_shadow_trace_shard, replay_direct_primitive_trace_shard,
    validate_complete_panel, validate_between_arm_tv_shard,
    validate_candidate_panel_index_contract,
    validate_checkpoint_restore_inventory,
    formal_validate_complete_panel,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.raw_control import (
    raw_control_receipt, validate_raw_control_receipt,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    PairedB01Trainer, direct_training_loss_reduction_array_contract,
    manifest_bound_paired_update_component,
    validate_direct_training_shard, _validate_paired_stage_equality,
)


def _last(iterator):
    item = None
    for item in iterator:
        pass
    return item


def test_manifest_machine_binds_canonical_28_margins_and_pending_anchor(b01_manifest):
    descriptive = exact_descriptive_contract()
    assert b01_manifest["scientific_contract"]["descriptive_contract"] == descriptive
    assert descriptive["quantity_order"] == list(QUANTITY_ORDER)
    assert descriptive["inventory_per_seed"] == {
        "primitive_rows": 25_088,
        "arm_update_receipts": 1_024,
        "paired_checkpoint_restores": 6,
        "quantity_values": 168,
        "shadow_action_pairs": 497_664,
    }
    anchor = descriptive["postcontact_cross_arm_action_tv_anchor"]
    assert anchor["role"] == "MANDATORY_DESCRIPTIVE_NON_GATE"
    assert anchor["selected_anchor"] == "SYMMETRIC"
    assert anchor["included_in_ordered_28"] is False
    assert anchor["raw_schema"] == "FRRIE_B01_BETWEEN_ARM_TV_RAW_V1"
    assert anchor["maximum_rows_per_seed_contact_by_32"] == 3_133_440
    altered = deepcopy(b01_manifest)
    altered["scientific_contract"]["descriptive_contract"][
        "postcontact_cross_arm_action_tv_anchor"
    ] = {
        "status": "PENDING_PRO_CLARIFICATION_NO_LOCAL_CLASSIFICATION",
        "included_in_ordered_28": False,
    }
    with pytest.raises(B01ContractError, match="scientific_contract"):
        validate_manifest(altered)


def test_raw_control_is_direct_fixture_readback_not_analysis_literal():
    receipt = raw_control_receipt()
    assert validate_raw_control_receipt(receipt)["balanced_accuracy"] == 0.5
    altered = deepcopy(receipt)
    altered["balanced_accuracy"] = 0.5000001
    with pytest.raises(B01ContractError, match="direct fixture"):
        validate_raw_control_receipt(altered)


def test_exact_coordinate_orders_boundaries_and_cardinalities():
    seed = "S001"
    assert exact_inventory_cardinalities([seed]) == {
        "primitive_rows": 25_088,
        "arm_update_receipts": 1_024,
        "paired_checkpoint_restores": 6,
        "quantity_values": 168,
        "shadow_action_pairs": 497_664,
    }
    primitive = iter_primitive_coordinates([seed])
    assert list(islice(primitive, 3)) == [
        (seed, "PHY_TRUST", 0, 6, "INTACT", 0),
        (seed, "PHY_TRUST", 0, 6, "INTACT", 1),
        (seed, "PHY_TRUST", 0, 6, "INTACT", 2),
    ]
    assert _last(iter_primitive_coordinates([seed])) == (
        seed, "UNIFORM_LEGAL", None, 15, "INTACT", 255,
    )
    assert sum(1 for _ in iter_primitive_coordinates([seed])) == 25_088
    assert list(islice(iter_arm_update_coordinates([seed]), 4)) == [
        (seed, "PHY_TRUST", 1), (seed, "EDGE_FLEX", 1),
        (seed, "PHY_TRUST", 2), (seed, "EDGE_FLEX", 2),
    ]
    assert _last(iter_arm_update_coordinates([seed])) == (seed, "EDGE_FLEX", 512)
    assert list(iter_checkpoint_restore_coordinates([seed])) == [
        (seed, checkpoint) for checkpoint in CHECKPOINTS
    ]
    quantities = iter_quantity_coordinates([seed])
    assert list(islice(quantities, 2)) == [
        (seed, 0, "d_N9"), (seed, 0, "d_N15"),
    ]
    assert _last(iter_quantity_coordinates([seed])) == (seed, 512, "A_zone_N21")
    shadow = iter_shadow_action_pair_coordinates([seed])
    assert list(islice(shadow, 3)) == [
        (seed, 0, 6, 0, 0, 0),
        (seed, 0, 6, 0, 0, 1),
        (seed, 0, 6, 0, 0, 2),
    ]
    assert _last(iter_shadow_action_pair_coordinates([seed])) == (
        seed, 512, 21, 255, 11, 20,
    )
    assert sum(1 for _ in iter_shadow_action_pair_coordinates([seed])) == 497_664


def test_formal_panel_signature_has_no_public_adapter_injection():
    import inspect
    assert list(inspect.signature(validate_complete_panel).parameters) == ["panel", "manifest"]
    assert list(inspect.signature(formal_validate_complete_panel).parameters) == [
        "panel", "manifest",
    ]


def test_formal_runner_static_contract_orders_gates_and_cannot_claim_readiness():
    contract = exact_formal_runner_contract()
    stages = contract["stage_order"]
    assert stages.index("ACTUAL_SOURCE_GATE") < stages.index(
        "FRESH_INVOCATION_MEMORY_ADMISSION"
    ) < stages.index("CANONICAL_PACKAGE_NATIVE_LOAD")
    assert stages.index("MANIFEST_BOUND_BATCH_COLLECTION") < stages.index(
        "ATOMIC_PAIRED_UPDATE"
    ) < stages.index("LITERAL_CHECKPOINT_WRITE_REOPEN_DECODE_RESTORE")
    assert stages[-2:] == [
        "PROCESS_TREE_MONITOR_FINALIZE", "CREATE_ONCE_PANEL_PUBLICATION",
    ]
    assert contract["seed_labels"] == "EXACT_VALIDATED_MANIFEST_EXECUTION_LABELS"
    assert contract["validation_replay_work"] == "SEPARATE_FROM_SCIENTIFIC_WORK"
    assert contract["readiness_from_static_contract"] is False


def test_candidate_top_index_refuses_partial_locator_inventory(
    b01_manifest, b01_production_binding,
):
    panel = {
        "schema": "FRRIE_B01_EXACT_PANEL_CANDIDATE_INDEX_V1",
        "manifest_contract": b01_manifest,
        "invocation_inventory": {
            "schema": "FRRIE_B01_INVOCATION_INVENTORY_V1", "entries": [],
        },
        "analysis_invocation_binding": {
            **b01_production_binding, "operation": "ANALYZE",
        },
        "primitive_index": [], "training_index": [], "checkpoint_index": [],
        "ordered_shadow_index": [], "between_arm_index": [],
        "quantity_coordinates": [], "work_ledger": [],
        "raw_control_receipt": raw_control_receipt(),
        "inventory_cardinalities": exact_inventory_cardinalities(
            b01_manifest["execution_labels"]
        ),
        "complete": True,
    }
    with pytest.raises(B01ContractError, match="primitive_index cardinality"):
        validate_candidate_panel_index_contract(panel, b01_manifest)


def test_candidate_top_invocations_require_unique_ids_and_fresh_receipt_files(
    b01_manifest, b01_production_binding,
):
    seed = b01_manifest["execution_labels"][0]
    repeated_receipt = {
        **b01_production_binding,
        "invocation_id": "FRRIE-B01-PRODUCTION-SCHEMA-TEST-SECOND",
    }
    analysis = {
        **b01_production_binding,
        "invocation_id": "FRRIE-B01-ANALYSIS-SCHEMA-TEST",
        "operation": "ANALYZE",
    }
    panel = {
        "schema": "FRRIE_B01_EXACT_PANEL_CANDIDATE_INDEX_V1",
        "manifest_contract": b01_manifest,
        "invocation_inventory": {
            "schema": "FRRIE_B01_INVOCATION_INVENTORY_V1",
            "entries": [
                {"seed_label": seed, "phase": b01_manifest["phase"],
                 "binding": b01_production_binding},
                {"seed_label": seed, "phase": b01_manifest["phase"],
                 "binding": repeated_receipt},
            ],
        },
        "analysis_invocation_binding": analysis,
        "primitive_index": [], "training_index": [], "checkpoint_index": [],
        "ordered_shadow_index": [], "between_arm_index": [],
        "quantity_coordinates": [], "work_ledger": [],
        "raw_control_receipt": raw_control_receipt(),
        "inventory_cardinalities": exact_inventory_cardinalities(
            b01_manifest["execution_labels"]
        ),
        "complete": True,
    }
    with pytest.raises(B01ContractError, match="own fresh receipt"):
        validate_candidate_panel_index_contract(panel, b01_manifest)


def test_training_shard_contract_rejects_summary_or_wrong_work_before_state_replay():
    assert direct_training_loss_reduction_array_contract() == {
        "loss_episode_component_bits": ("<u4", (512, 64, 4)),
        "loss_aggregate_bits": ("<u4", (512, 4)),
    }
    shard = {
        "schema": "FRRIE_B01_DIRECT_TRAINING_SHARD_V1", "seed_label": "S001",
        "arm": "PHY_TRUST", "coordinate_order": ["update_1_512"],
        "array_shards": {}, "state_blobs": {},
        "loss_reduction_contract": exact_loss_reduction_contract(),
        "work_contract": {"summary": 2_523_136}, "complete": True,
    }
    with pytest.raises(B01ContractError, match="work contract"):
        validate_direct_training_shard(shard)


def _synthetic_training_stages():
    model = {
        name: {
            "PHY_TRUST": [b"ABCD", b"EFGH"],
            "EDGE_FLEX": [b"ABCD", b"EFGH"],
        }
        for name in ("model_pre", "model_post_adam", "model_post_projection")
    }
    optimizer = {
        name: {
            "PHY_TRUST": [b"adam0", b"adam1"],
            "EDGE_FLEX": [b"adam0", b"adam1"],
        }
        for name in ("optimizer_pre", "optimizer_post_adam", "optimizer_post_projection")
    }
    return model, optimizer


def test_paired_training_kappa_and_no_contact_byte_drift_laws_are_direct():
    model, optimizer = _synthetic_training_stages()
    model["model_post_projection"]["EDGE_FLEX"][0] = b"AXYD"
    _validate_paired_stage_equality(
        model_stages=model, optimizer_stages=optimizer, kappa=1,
        beta_offset=1, beta_stop=3, updates=2,
    )
    model, optimizer = _synthetic_training_stages()
    model["model_post_adam"]["EDGE_FLEX"][0] = b"AXYD"
    with pytest.raises(B01ContractError, match="postAdam bytes differ at κ"):
        _validate_paired_stage_equality(
            model_stages=model, optimizer_stages=optimizer, kappa=1,
            beta_offset=1, beta_stop=3, updates=2,
        )
    model, optimizer = _synthetic_training_stages()
    model["model_post_projection"]["EDGE_FLEX"][1] = b"EFGX"
    with pytest.raises(B01ContractError, match="before κ"):
        _validate_paired_stage_equality(
            model_stages=model, optimizer_stages=optimizer, kappa=None,
            beta_offset=1, beta_stop=3, updates=2,
        )
    assert all("parameter" not in name.lower() for name in QUANTITY_ORDER)


def test_formal_paired_component_calls_manifest_bound_collector_for_both_arms(
    monkeypatch, b01_manifest,
):
    import experiments.candidates.finite_resource_relational_inductive_efficiency.b01.batch_collector as collector

    calls = []
    batch = object()
    audit = SimpleNamespace(
        total_environment_slots=4_928, factual_slots=768,
        factual_suffix_audit_slots=1_248, nonfactual_suffix_slots=2_912,
    )

    def fake_collect(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(batch=batch, audit=audit)

    monkeypatch.setattr(collector, "collect_b01_arm_update", fake_collect)
    paired = PairedB01Trainer.__new__(PairedB01Trainer)
    paired.models = {"PHY_TRUST": object(), "EDGE_FLEX": object()}
    paired.update = lambda batches, update: {
        arm: f"receipt-{arm}-{update}" for arm in batches
    }
    tape = SimpleNamespace(seed_block=b01_manifest["execution_labels"][0])
    result = manifest_bound_paired_update_component(
        paired_trainer=paired, adapter=object(), tapes=(tape,), origins=((),),
        update=1, manifest=b01_manifest,
    )
    assert [call["model"] for call in calls] == [
        paired.models["PHY_TRUST"], paired.models["EDGE_FLEX"],
    ]
    assert all(call["manifest"] == b01_manifest for call in calls)
    assert all("allowed_seed_labels" not in call for call in calls)
    assert result["scientific_training_work_per_arm"] == 4_928
    assert result["production_token_minted"] is False


def test_checkpoint_restore_inventory_reopens_all_six_in_literal_order(
    tmp_path, b01_manifest, b01_production_binding,
):
    import json
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import encode_checkpoint
    from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
    phy, edge = initialize_paired_arms(AddressedRNG(b"I" * 32), "FRRIE-B01-CHECKPOINT-INVENTORY")
    rows = []
    for checkpoint in CHECKPOINTS:
        checkpoint_path = (tmp_path / f"checkpoint-{checkpoint}.json").resolve()
        checkpoint_path.write_bytes(encode_checkpoint(
            manifest=b01_manifest, seed_label=ROOT_LABELS[0], update=checkpoint,
            arm_state_bytes={
                "PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes(),
            },
            optimizer_state_bytes={
                "PHY_TRUST": _optimizer_bytes_at(checkpoint),
                "EDGE_FLEX": _optimizer_bytes_at(checkpoint),
            },
            work=_checkpoint_work_at(checkpoint),
            invocation_binding=b01_production_binding,
            projection_audit=_checkpoint_zero_audit(),
        ))
        descriptor_path = (tmp_path / f"checkpoint-{checkpoint}-locator.json").resolve()
        descriptor_path.write_text(json.dumps({
            "schema": "FRRIE_B01_CHECKPOINT_LOCATOR_V1",
            "seed_label": ROOT_LABELS[0], "checkpoint": checkpoint,
            "checkpoint_path": str(checkpoint_path), "complete": True,
        }), encoding="utf-8")
        rows.append({
            "seed_label": ROOT_LABELS[0], "checkpoint": checkpoint,
            "descriptor_path": str(descriptor_path),
        })
    result = validate_checkpoint_restore_inventory(
        rows, manifest=b01_manifest, seed_labels=[ROOT_LABELS[0]],
    )
    assert result["receipt_count"] == 6
    assert [row["checkpoint"] for row in result["receipts"]] == list(CHECKPOINTS)


def _candidate_cells(seed: str, checkpoint: int):
    learned_returns = {
        "PHY_TRUST": {6: 0.70, 9: 0.65, 15: 0.60, 21: 0.55},
        "EDGE_FLEX": {6: 0.50, 9: 0.45, 15: 0.40, 21: 0.35},
    }
    rows = []
    for arm in ("PHY_TRUST", "EDGE_FLEX"):
        for roster in (6, 9, 15, 21):
            for intervention in ("INTACT", "SEMANTIC_COLUMN_ROTATE"):
                value = learned_returns[arm][roster]
                if intervention != "INTACT":
                    value -= 0.10 if arm == "PHY_TRUST" else 0.05
                needs_tv = arm == "PHY_TRUST" and roster in (6, 21) and intervention == "INTACT"
                rows.append({
                    "seed_label": seed, "checkpoint": checkpoint, "arm": arm,
                    "roster": roster, "intervention": intervention,
                    "native_return": value, "basin_west": value - 0.10,
                    "basin_east": value - 0.05,
                    "legal_tv": ({6: 0.12, 21: 0.14}[roster] if needs_tv else None),
                    "tv_sup": ({6: 0.30, 21: 0.40}[roster] if needs_tv else None),
                })
    for roster, value in ((9, 0.25), (15, 0.20)):
        rows.append({
            "seed_label": seed, "checkpoint": None, "arm": "UNIFORM_LEGAL",
            "roster": roster, "intervention": "INTACT", "native_return": value,
            "basin_west": value, "basin_east": value,
            "legal_tv": None, "tv_sup": None,
        })
    return rows


def test_candidate_formula_reducer_emits_exact_order_without_interpretation():
    values = candidate_test_quantity_values(_candidate_cells("S001", 512), seed_label="S001", checkpoint=512)
    assert list(values) == list(QUANTITY_ORDER)
    assert values["d_N6"] == pytest.approx(0.20)
    assert values["e_N9"] == pytest.approx(0.20)
    assert values["c_N6"] == pytest.approx(0.0)
    assert values["C_PHY_N6"] == pytest.approx(0.10)
    assert values["V_N6"] == pytest.approx(0.12)
    assert values["I_N6"] == pytest.approx(0.05)
    assert values["A_TV_N6"] == pytest.approx(0.22)
    broken = _candidate_cells("S001", 512)
    broken[1], broken[2] = broken[2], broken[1]
    with pytest.raises(B01ContractError, match="order"):
        candidate_test_quantity_values(broken, seed_label="S001", checkpoint=512)
    with pytest.raises(B01ContractError, match="streamed direct-shard"):
        quantity_values_from_validated_cells({"cells": _candidate_cells("S001", 512)})


def test_manifest_seed_order_summary_is_individual_mean_median_min_max_only():
    seeds = ["S001", "S002"]
    rows = []
    for seed_index, seed in enumerate(seeds):
        for checkpoint in CHECKPOINTS:
            for quantity_index, quantity in enumerate(QUANTITY_ORDER):
                rows.append({
                    "seed_label": seed, "checkpoint": checkpoint, "quantity": quantity,
                    "value": float(seed_index * 10 + checkpoint + quantity_index),
                })
    result = summarize_candidate_quantities(rows, seed_labels=seeds)
    first = result["summaries"][0]
    assert first == {
        "checkpoint": 0, "quantity": "d_N9",
        "individual": [
            {"seed_label": "S001", "value": 0.0},
            {"seed_label": "S002", "value": 10.0},
        ],
        "mean": 5.0, "median": 5.0, "min": 0.0, "max": 10.0,
    }
    assert result["branch_interpretation"] is None
    assert result["confidence_intervals"] is None
    assert result["polarity"] is None


def _primitive_shard(tmp_path):
    shapes = {
        "dw": (256,), "de": (256,), "radio_actions": (256,),
        "waste_actions": (256,), "successful_scan": (256,),
        "successful_uplink": (256,), "successful_receive": (256,),
        "successful_delivery": (256,), "expired": (256,), "duplicate": (256,),
        "collision": (256,), "empty_radio": (256,),
        "role_action_counts": (256, 3, 6), "terminal_delivered": (256, 2, 3),
    }
    dtypes = {
        "dw": "|u1", "de": "|u1", "terminal_delivered": "|u1",
        **{
            name: "<u2" for name in shapes
            if name not in {"dw", "de", "terminal_delivered"}
        },
    }
    arrays = {}
    for name, shape in shapes.items():
        array = np.zeros(shape, dtype=np.dtype(dtypes[name]))
        if name == "role_action_counts":
            array[:, :, 5] = 24
        path = (tmp_path / f"{name}.bin").resolve()
        array.tofile(path)
        arrays[name] = {
            "path": str(path), "dtype": dtypes[name], "shape": list(shape),
            "order": "C", "byte_count": int(array.nbytes),
        }
    return {
        "schema": "FRRIE_B01_PRIMITIVE_RAW_SHARD_V1", "seed_label": "S001",
        "arm": "PHY_TRUST", "checkpoint": 0, "roster": 6,
        "intervention": "INTACT", "coordinate_order": ["episode"],
        "tape_surface": {
            "schema": "FRRIE_B01_EVALUATION_TAPE_SURFACE_V1",
            "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
            "checkpoint_role": "METADATA_ONLY", "arm_independent": True,
            "intervention_independent": True, "checkpoint_independent": True,
        },
        "arrays": arrays, "complete": True,
    }


def test_primitive_raw_shard_mmap_recomputes_endpoint_ledgers_and_cell_census(tmp_path):
    shard = _primitive_shard(tmp_path)
    cell = validate_candidate_primitive_shard(shard)
    assert cell["candidate_only"] is True
    assert cell["support_classification"] is None
    assert cell["native_return"] == pytest.approx(0.1)
    assert cell["support_census"] == [{
        "D_W": 0, "D_E": 0, "waste_actions": 0,
        "radio_actions": 0, "episodes": 256,
    }]
    waste = np.memmap(
        shard["arrays"]["waste_actions"]["path"], dtype="<u2", mode="r+", shape=(256,),
    )
    waste[0] = 1
    waste.flush()
    with pytest.raises(B01ContractError, match="waste/radio"):
        validate_candidate_primitive_shard(shard)


def _direct_primitive_trace_shard(tmp_path):
    roster = 6
    shapes = {
        "observation": (256, 12, roster, 22),
        "actions": (256, 12, roster),
        "predecision_previous_action": (256, 12, roster),
        "predecision_previous_success": (256, 12, roster),
        "poststep_previous_success": (256, 12, roster),
        "terminal_delivered": (256, 2, 3),
        **{
            f"metric_{name}": (256, 12) for name in (
                "dw", "de", "radio_actions", "waste_actions",
                "new_timely_deliveries", "expired_arrivals", "duplicate_arrivals",
                "collision_loss", "empty_actions",
            )
        },
    }
    arrays = {}
    values = {}
    for name, shape in shapes.items():
        dtype = "<f4" if name == "observation" else "|u1" if name in {
            "actions", "predecision_previous_action",
            "predecision_previous_success", "poststep_previous_success",
            "terminal_delivered",
        } else "<u4"
        array = np.zeros(shape, dtype=np.dtype(dtype))
        if name == "observation":
            array[:, 1:, :, 20] = 1.0
            array[0, 1, 0, 20] = 0.0
            array[0, 1, 0, 16] = 1.0
            array[0, 1, 0, 21] = 1.0
        elif name == "actions":
            array.fill(5)
            array[0, 0, 0] = 1
        elif name == "predecision_previous_action":
            array[:, 0, :] = 255
            array[:, 1:, :] = 5
            array[0, 1, 0] = 1
        elif name == "predecision_previous_success":
            # Success for the slot-0 uplink appears only at the next predecision.
            array[0, 1, 0] = 1
        elif name == "poststep_previous_success":
            array[0, 0, 0] = 1
        elif name == "metric_radio_actions":
            array[0, :] = 1
        path = (tmp_path / f"direct-{name}.bin").resolve()
        array.tofile(path)
        values[name] = array
        arrays[name] = {
            "path": str(path), "dtype": dtype, "shape": list(shape),
            "order": "C", "byte_count": int(array.nbytes),
        }
    return {
        "schema": "FRRIE_B01_PRIMITIVE_TRACE_SHARD_V1",
        "seed_label": ROOT_LABELS[0], "arm": "PHY_TRUST", "checkpoint": 0,
        "roster": roster, "intervention": "INTACT",
        "coordinate_order": ["episode", "slot", "entity"],
        "arrays": arrays, "complete": True,
    }


def test_direct_trace_uses_next_predecision_success_not_poststep_aggregate(tmp_path):
    shard = _direct_primitive_trace_shard(tmp_path)
    cell = validate_direct_primitive_trace_shard(shard, root=b"R" * 32)
    assert cell["direct_success_counts"] == {
        "successful_scan": 0, "successful_uplink": 1,
        "successful_receive": 0, "successful_delivery": 0,
    }
    assert cell["production_token_minted"] is False
    previous = np.memmap(
        shard["arrays"]["predecision_previous_action"]["path"],
        dtype="|u1", mode="r+", shape=(256, 12, 6),
    )
    previous[0, 0, 0] = 0
    previous.flush()
    with pytest.raises(B01ContractError, match="unset sentinel"):
        validate_direct_primitive_trace_shard(shard, root=b"R" * 32)
    previous[0, 0, 0] = 255
    previous.flush()
    poststep = np.memmap(
        shard["arrays"]["poststep_previous_success"]["path"],
        dtype="|u1", mode="r+", shape=(256, 12, 6),
    )
    poststep[0, 0, 0] = 0
    poststep.flush()
    with pytest.raises(B01ContractError, match="next predecision"):
        validate_direct_primitive_trace_shard(shard, root=b"R" * 32)
    poststep[0, 0, 0] = 1
    poststep[0, 11, 0] = 1
    poststep.flush()
    with pytest.raises(B01ContractError, match="terminal slot"):
        validate_direct_primitive_trace_shard(shard, root=b"R" * 32)


def _zero_optimizer_bytes():
    import struct
    from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
        OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
    )
    return struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        OPTIMIZER_PAYLOAD_BYTE_COUNT,
    ) + bytes(OPTIMIZER_PAYLOAD_BYTE_COUNT)


def _checkpoint_zero_work():
    row = {
        "training_update": 0, "episodes": 0, "environment_slots": 0,
        "backward_calls": 0, "adam_steps": 0, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 0,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {"PHY_TRUST": dict(row), "EDGE_FLEX": dict(row)}


def _checkpoint_zero_audit():
    return {
        "first_tight_contact_update": None, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0, "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
    }


def _optimizer_bytes_at(update):
    import struct
    value = bytearray(_zero_optimizer_bytes())
    value[-8:] = struct.pack("<Q", update)
    return bytes(value)


def _checkpoint_work_at(update):
    row = {
        "training_update": update, "episodes": update * 64,
        "environment_slots": update * 4_928, "backward_calls": update,
        "adam_steps": update, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": update * 4_928,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {"PHY_TRUST": dict(row), "EDGE_FLEX": dict(row)}


def _write_final_checkpoint(
    path, *, b01_manifest, b01_production_binding, phy, edge, contact,
):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import encode_checkpoint
    audit = _checkpoint_zero_audit() if contact is None else {
        "first_tight_contact_update": contact, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 1, "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.01, "cumulative_tight_displacement": 0.01,
    }
    path.write_bytes(encode_checkpoint(
        manifest=b01_manifest, seed_label=ROOT_LABELS[0], update=512,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={
            "PHY_TRUST": _optimizer_bytes_at(512), "EDGE_FLEX": _optimizer_bytes_at(512),
        },
        work=_checkpoint_work_at(512), invocation_binding=b01_production_binding,
        projection_audit=audit,
    ))
    return path


def _shadow_trace_shard(tmp_path, b01_manifest, b01_production_binding):
    import torch
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import encode_checkpoint
    from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
        FRRIEActorCritic, LEGAL_ACTION_INDICES,
    )
    from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG

    phy, edge = initialize_paired_arms(AddressedRNG(b"S" * 32), "FRRIE-B01-SHADOW-TEST")
    checkpoint_path = (tmp_path / "checkpoint-0.json").resolve()
    checkpoint_path.write_bytes(encode_checkpoint(
        manifest=b01_manifest, seed_label=ROOT_LABELS[0], update=0,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={
            "PHY_TRUST": _zero_optimizer_bytes(), "EDGE_FLEX": _zero_optimizer_bytes(),
        },
        work=_checkpoint_zero_work(), invocation_binding=b01_production_binding,
        projection_audit=_checkpoint_zero_audit(),
    ))
    model = FRRIEActorCritic(phy)
    roster = 6
    roles = np.repeat(np.arange(3, dtype=np.uint8), roster // 3)
    mask = np.zeros((roster, 6), dtype=np.uint8)
    for entity, role in enumerate(roles):
        mask[entity, list(LEGAL_ACTION_INDICES[int(role)])] = 1
    observation_episode = np.zeros((12, roster, 22), dtype=np.float32)
    hidden_episode = np.zeros((12, roster, 64), dtype=np.float32)
    intact_episode = np.zeros((12, roster, 6), dtype=np.float32)
    shadow_episode = np.zeros((12, roster, 6), dtype=np.float32)
    hidden = np.zeros((roster, 64), dtype=np.float32)
    roles_tensor = torch.from_numpy(roles.astype(np.int64))
    with torch.no_grad():
        for slot in range(12):
            hidden_episode[slot] = hidden
            obs = torch.from_numpy(observation_episode[slot])
            incoming = torch.from_numpy(hidden.copy())
            actual = model.actor_step(obs, roles_tensor, incoming)
            shadow = model.shadow_step(obs, roles_tensor, incoming)
            intact_episode[slot] = actual.probabilities.numpy()
            shadow_episode[slot] = shadow.probabilities.numpy()
            hidden = actual.hidden.numpy().copy()
    values = {
        "observation": np.broadcast_to(observation_episode, (256, *observation_episode.shape)).copy(),
        "incoming_hidden": np.broadcast_to(hidden_episode, (256, *hidden_episode.shape)).copy(),
        "intact_probability": np.broadcast_to(intact_episode, (256, *intact_episode.shape)).copy(),
        "role": np.broadcast_to(roles, (256, 12, roster)).copy(),
        "legal_mask": np.broadcast_to(mask, (256, 12, roster, 6)).copy(),
        "shadow_probability": np.broadcast_to(shadow_episode, (256, *shadow_episode.shape)).copy(),
    }
    trace_arrays = {}
    shadow_arrays = {}
    for name, array in values.items():
        dtype = "<f4" if array.dtype == np.float32 else "|u1"
        path = (tmp_path / f"shadow-{name}.bin").resolve()
        array.tofile(path)
        descriptor = {
            "path": str(path), "dtype": dtype, "shape": list(array.shape),
            "order": "C", "byte_count": int(array.nbytes),
        }
        (shadow_arrays if name == "shadow_probability" else trace_arrays)[name] = descriptor
    return {
        "schema": "FRRIE_B01_PHY_INTACT_SHADOW_TRACE_SHARD_V1",
        "seed_label": ROOT_LABELS[0], "checkpoint": 0, "roster": roster,
        "checkpoint_path": str(checkpoint_path),
        "coordinate_order": ["episode", "slot", "entity"],
        "trace_arrays": trace_arrays, "shadow_arrays": shadow_arrays,
        "shadow_semantics": {
            "operation": "SEMANTIC_COLUMN_ROTATE_ONE_STEP_ONLY",
            "incoming_hidden_source": "SAME_ACTUAL_TRACE_INCOMING_HIDDEN",
            "shadow_hidden": "DISCARDED", "native_action_effect": False,
            "actual_rotate_trajectory": "SEPARATE_12_SLOT_SEQUENTIAL_PRIMITIVE_CELL",
        },
        "complete": True,
    }


def test_shadow_trace_reopens_checkpoint_and_recomputes_actual_shadow_fp32_bytes(
    tmp_path, b01_manifest, b01_production_binding,
):
    pytest.importorskip("torch")
    shard = _shadow_trace_shard(tmp_path, b01_manifest, b01_production_binding)
    component = validate_direct_shadow_trace_shard(shard, manifest=b01_manifest)
    assert component["direct_pair_count"] == 256 * 12 * 6
    assert component["checkpoint_literal_reopened"] is True
    assert component["shadow_hidden_discarded"] is True
    assert component["native_action_effect"] is False
    shadow = np.memmap(
        shard["shadow_arrays"]["shadow_probability"]["path"],
        dtype="<f4", mode="r+", shape=(256, 12, 6, 6),
    )
    shadow[0, 0, 0, 0] += np.float32(0.01)
    shadow.flush()
    with pytest.raises(B01ContractError, match="shadow actor probability bytes"):
        validate_direct_shadow_trace_shard(shard, manifest=b01_manifest)


def test_between_arm_precontact_availability_has_no_raw_rows(
    tmp_path, b01_manifest, b01_production_binding,
):
    pytest.importorskip("torch")
    checkpoint = _shadow_trace_shard(tmp_path, b01_manifest, b01_production_binding)[
        "checkpoint_path"
    ]
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
    from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
    phy, edge = initialize_paired_arms(AddressedRNG(b"F" * 32), "FRRIE-B01-FINAL-NOCONTACT")
    final_path = _write_final_checkpoint(
        (tmp_path / "checkpoint-512-no-contact.json").resolve(),
        b01_manifest=b01_manifest, b01_production_binding=b01_production_binding,
        phy=phy, edge=edge, contact=None,
    )
    value = {
        "schema": "FRRIE_B01_BETWEEN_ARM_TV_SHARD_V1",
        "seed_label": ROOT_LABELS[0], "checkpoint": 0, "roster": 6,
        "intervention": "INTACT", "checkpoint_path": checkpoint,
        "seed_contact_ledger": {
            "schema": "FRRIE_B01_SEED_CONTACT_LEDGER_V1",
            "final_checkpoint_path": str(final_path), "complete_projection_ledger": True,
            "first_tight_contact_update": None,
        },
        "availability": {
            "status": "NO_TIGHT_CONTACT_BY_512", "available": False,
            "first_tight_contact_update": None, "checkpoint": 0,
        },
        "coordinate_order": ["episode", "slot", "entity", "anchor_PHY_EDGE"],
        "tape_surface": {
            "schema": "FRRIE_B01_EVALUATION_TAPE_SURFACE_V1",
            "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
            "checkpoint_role": "METADATA_ONLY", "arm_independent": True,
            "intervention_independent": True, "checkpoint_independent": True,
        },
        "raw_row_schema": "FRRIE_B01_BETWEEN_ARM_TV_RAW_V1",
        "trace_arrays": None, "raw_arrays": None, "complete": True,
    }
    result = validate_between_arm_tv_shard(value, manifest=b01_manifest)
    assert result["status"] == "NO_TIGHT_CONTACT_BY_512"
    assert result["raw_row_count"] == 0
    assert result["individual_cell_mean"] is None
    altered = deepcopy(value)
    altered["raw_arrays"] = {}
    with pytest.raises(B01ContractError, match="no raw rows"):
        validate_between_arm_tv_shard(altered, manifest=b01_manifest)


def _between_arm_available_shard(tmp_path, b01_manifest, b01_production_binding):
    import struct
    import torch
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import encode_checkpoint
    from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
        FRRIEActorCritic, LEGAL_ACTION_INDICES,
    )
    from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG

    phy, edge = initialize_paired_arms(AddressedRNG(b"B" * 32), "FRRIE-B01-BETWEEN-ARM-TEST")
    optimizer = _optimizer_bytes_at(32)
    work_row = {
        "training_update": 32, "episodes": 32 * 64,
        "environment_slots": 32 * 4_928, "backward_calls": 32,
        "adam_steps": 32, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 32 * 4_928,
        },
        "worker_count": 4, "thread_count": 1,
    }
    audit = {
        "first_tight_contact_update": 1, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 1, "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.01, "cumulative_tight_displacement": 0.01,
    }
    checkpoint_path = (tmp_path / "checkpoint-32.json").resolve()
    checkpoint_path.write_bytes(encode_checkpoint(
        manifest=b01_manifest, seed_label=ROOT_LABELS[0], update=32,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={"PHY_TRUST": optimizer, "EDGE_FLEX": optimizer},
        work={"PHY_TRUST": dict(work_row), "EDGE_FLEX": dict(work_row)},
        invocation_binding=b01_production_binding, projection_audit=audit,
    ))
    final_path = _write_final_checkpoint(
        (tmp_path / "checkpoint-512-contact.json").resolve(),
        b01_manifest=b01_manifest, b01_production_binding=b01_production_binding,
        phy=phy, edge=edge, contact=1,
    )
    roster = 6
    roles = np.repeat(np.arange(3, dtype=np.uint8), roster // 3)
    mask = np.zeros((roster, 6), dtype=np.uint8)
    for entity, role in enumerate(roles):
        mask[entity, list(LEGAL_ACTION_INDICES[int(role)])] = 1
    models = {"PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge)}
    observation_episode = np.zeros((12, roster, 2, 22), dtype=np.float32)
    hidden_episode = np.zeros((12, roster, 2, 64), dtype=np.float32)
    probability_bits_episode = np.zeros((12, roster, 2, 2, 6), dtype=np.uint32)
    tv_episode = np.zeros((12, roster, 2), dtype=np.float64)
    hidden_by_anchor = {
        "PHY_TRUST": np.zeros((roster, 64), dtype=np.float32),
        "EDGE_FLEX": np.zeros((roster, 64), dtype=np.float32),
    }
    role_tensor = torch.from_numpy(roles.astype(np.int64))
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.tapes import evaluation_tape
    from experiments.candidates.finite_resource_relational_inductive_efficiency.tapes import inverse_cdf_action
    root = bytes.fromhex(b01_manifest["seed_packet"]["contract"]["roots_hex"][0])
    with torch.no_grad():
        for slot in range(12):
            for anchor_index, anchor in enumerate(("PHY_TRUST", "EDGE_FLEX")):
                hidden_episode[slot, :, anchor_index] = hidden_by_anchor[anchor]
                obs = torch.from_numpy(observation_episode[slot, :, anchor_index])
                incoming = torch.from_numpy(hidden_by_anchor[anchor].copy())
                steps = [
                    models[arm].actor_step(obs, role_tensor, incoming)
                    for arm in ("PHY_TRUST", "EDGE_FLEX")
                ]
                outputs = [step.probabilities.numpy() for step in steps]
                probability_bits_episode[slot, :, anchor_index] = np.stack(
                    outputs, axis=1,
                ).astype("<f4", copy=False).view("<u4")
                hidden_by_anchor[anchor] = steps[anchor_index].hidden.numpy().copy()
    selected_actions = np.zeros((256, 12, roster, 2), dtype=np.uint8)
    probability_float_episode = probability_bits_episode.view("<f4")
    for episode in range(256):
        tape = evaluation_tape(root, seed_label=ROOT_LABELS[0], roster=roster, episode=episode)
        for slot in range(12):
            for anchor_index in range(2):
                own = probability_float_episode[slot, :, anchor_index, anchor_index]
                for entity in range(roster):
                    selected_actions[episode, slot, entity, anchor_index] = inverse_cdf_action(
                        own[entity], float(tape.action_uniform[slot, entity]),
                    )
    values = {
        "observation": np.broadcast_to(
            observation_episode, (256, *observation_episode.shape),
        ).copy(),
        "incoming_hidden": np.broadcast_to(
            hidden_episode, (256, *hidden_episode.shape),
        ).copy(),
        "role": np.broadcast_to(roles, (256, 12, roster)).copy(),
        "legal_mask": np.broadcast_to(mask, (256, 12, roster, 6)).copy(),
        "selected_action": selected_actions,
        "probability_bits": np.broadcast_to(
            probability_bits_episode, (256, *probability_bits_episode.shape),
        ).copy(),
        "tv64": np.broadcast_to(tv_episode, (256, *tv_episode.shape)).copy(),
    }
    trace_arrays = {}
    raw_arrays = {}
    for name, array in values.items():
        path = (tmp_path / f"between-{name}.bin").resolve()
        array.tofile(path)
        descriptor = {
            "path": str(path), "dtype": np.dtype(array.dtype).str,
            "shape": list(array.shape), "order": "C", "byte_count": int(array.nbytes),
        }
        (raw_arrays if name in {"probability_bits", "tv64"} else trace_arrays)[name] = descriptor
    return {
        "schema": "FRRIE_B01_BETWEEN_ARM_TV_SHARD_V1",
        "seed_label": ROOT_LABELS[0], "checkpoint": 32, "roster": roster,
        "intervention": "INTACT", "checkpoint_path": str(checkpoint_path),
        "seed_contact_ledger": {
            "schema": "FRRIE_B01_SEED_CONTACT_LEDGER_V1",
            "final_checkpoint_path": str(final_path), "complete_projection_ledger": True,
            "first_tight_contact_update": 1,
        },
        "availability": {
            "status": "AVAILABLE", "available": True,
            "first_tight_contact_update": 1, "checkpoint": 32,
        },
        "coordinate_order": ["episode", "slot", "entity", "anchor_PHY_EDGE"],
        "tape_surface": {
            "schema": "FRRIE_B01_EVALUATION_TAPE_SURFACE_V1",
            "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
            "checkpoint_role": "METADATA_ONLY", "arm_independent": True,
            "intervention_independent": True, "checkpoint_independent": True,
        },
        "raw_row_schema": "FRRIE_B01_BETWEEN_ARM_TV_RAW_V1",
        "trace_arrays": trace_arrays, "raw_arrays": raw_arrays, "complete": True,
    }


def test_between_arm_available_shard_recomputes_exact_u32_bits_and_exact_zero(
    tmp_path, b01_manifest, b01_production_binding,
):
    pytest.importorskip("torch")
    shard = _between_arm_available_shard(tmp_path, b01_manifest, b01_production_binding)
    result = validate_between_arm_tv_shard(shard, manifest=b01_manifest)
    assert result["status"] == "AVAILABLE"
    assert result["raw_row_count"] == 256 * 12 * 6 * 2
    assert result["individual_cell_mean"] == 0.0
    assert result["anchor_reduction"] == "SYMMETRIC_HALF_PHY_HALF_EDGE"
    assert result["actor_forward_calls"] == 256 * 12 * 2 * 2
    assert result["actor_forward_topology"] == (
        "TWO_POLICIES_PER_ANCHOR_NO_THIRD_ANCHOR_FORWARD"
    )
    bits = np.memmap(
        shard["raw_arrays"]["probability_bits"]["path"], dtype="<u4", mode="r+",
        shape=(256, 12, 6, 2, 2, 6),
    )
    bits[0, 0, 0, 0, 0, 0] ^= np.uint32(1)
    bits.flush()
    with pytest.raises(B01ContractError, match="FP32 probability bits"):
        validate_between_arm_tv_shard(shard, manifest=b01_manifest)


def test_between_arm_cross_seed_summary_uses_available_ids_without_pooling():
    base = {
        "checkpoint": 32, "roster": 6, "intervention": "INTACT",
    }
    components = [
        {**base, "seed_label": "S1", "status": "AVAILABLE", "individual_cell_mean": 0.0},
        {**base, "seed_label": "S2", "status": "PRE_TIGHT_CONTACT",
         "individual_cell_mean": None},
        {**base, "seed_label": "S3", "status": "AVAILABLE", "individual_cell_mean": 0.2},
        {**base, "seed_label": "S4", "status": "UNAVAILABLE_MEASUREMENT_DEFECT",
         "individual_cell_mean": None},
    ]
    result = summarize_between_arm_tv(
        components, seed_labels=["S1", "S2", "S3", "S4"],
        checkpoint=32, roster=6, intervention="INTACT",
    )
    assert result["contact_seed_ids"] == ["S1", "S3", "S4"]
    assert result["contact_count"] == 3
    assert result["valid_value_seed_ids"] == ["S1", "S3"]
    assert result["valid_value_count"] == 2
    assert result["individual"] == [
        {"seed_label": "S1", "value": 0.0},
        {"seed_label": "S3", "value": 0.2},
    ]
    assert result["mean"] == pytest.approx(0.1)
    assert result["measurement_defects"] == [
        {"seed_label": "S4", "status": "UNAVAILABLE_MEASUREMENT_DEFECT"}
    ]
    none = summarize_between_arm_tv(
        [
            {**base, "seed_label": seed, "status": "NO_TIGHT_CONTACT_BY_512",
             "individual_cell_mean": None}
            for seed in ("S1", "S2")
        ],
        seed_labels=["S1", "S2"], checkpoint=32, roster=6, intervention="INTACT",
    )
    assert none["status"] == "NO_POST_CONTACT_SEEDS"
    assert none["mean"] is None
    all_defect = summarize_between_arm_tv(
        [
            {**base, "seed_label": seed, "status": "UNAVAILABLE_MEASUREMENT_DEFECT",
             "individual_cell_mean": None}
            for seed in ("S1", "S2")
        ],
        seed_labels=["S1", "S2"], checkpoint=32, roster=6, intervention="INTACT",
    )
    assert all_defect["status"] == "UNAVAILABLE_MEASUREMENT_DEFECT"
    assert all_defect["unavailable_reason"] == "NO_VALID_DIAGNOSTIC_VALUES"
    assert all_defect["contact_seed_ids"] == ["S1", "S2"]
    assert all_defect["valid_value_count"] == 0


def test_actual_native_width32_replay_revalidates_direct_trace(
    tmp_path, b01_manifest,
):
    import json
    import os
    import subprocess
    import sys
    from dataclasses import asdict
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
        bind_invocation_resource, named_compute_profile,
    )
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
        B01NativeBatchEnvironment,
    )
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.tapes import evaluation_tape
    from experiments.candidates.finite_resource_relational_inductive_efficiency.native.native_abi import (
        NativeStateV1, STATE_SIZE,
    )
    from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import (
        build_package_native_artifact, load_package_native_adapter,
        package_native_artifact_path,
    )

    artifact = package_native_artifact_path().resolve(strict=False)
    if artifact.exists():
        pytest.skip("unknown pre-existing package native artifact")
    if os.environ.get("FRRIE_B01_NATIVE_REPLAY_CHILD") != "1":
        bytes_path = (tmp_path / "child-native-artifact-bytes.bin").resolve()
        environment = dict(os.environ)
        environment["FRRIE_B01_NATIVE_REPLAY_CHILD"] = "1"
        environment["FRRIE_B01_NATIVE_REPLAY_BYTES_PATH"] = str(bytes_path)
        try:
            completed = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    str(Path(__file__).resolve())
                    + "::test_actual_native_width32_replay_revalidates_direct_trace",
                    "-q", "--basetemp", str((tmp_path / "child-pytest").resolve()),
                    "-p", "no:cacheprovider",
                ],
                env=environment, check=False, capture_output=True, text=True, timeout=120,
            )
            assert completed.returncode == 0, completed.stderr or completed.stdout
            assert artifact.is_file() and bytes_path.is_file()
            assert artifact.read_bytes() == bytes_path.read_bytes()
        finally:
            if artifact.exists():
                artifact.unlink()
        return
    artifact_bytes = None
    try:
        artifact = build_package_native_artifact()
        artifact_bytes = artifact.read_bytes()
        adapter = load_package_native_adapter(named_compute_profile())
        receipt_path = (tmp_path / "native-replay-admit-memory.json").resolve()
        completed = subprocess.run(
            [
                sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
                "admit-memory", "--out", str(receipt_path),
            ],
            check=False, capture_output=True, text=True, timeout=30,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        binding = bind_invocation_resource(
            invocation_id="FRRIE-B01-TEST-NATIVE-REPLAY", operation="EVALUATE",
            receipt_path=receipt_path, receipt=receipt, test_only=False,
        )
        roster = 6
        root = bytes.fromhex(b01_manifest["seed_packet"]["contract"]["roots_hex"][0])
        arrays_np = {
            "observation": np.zeros((256, 12, roster, 22), dtype=np.float32),
            "actions": np.full((256, 12, roster), 5, dtype=np.uint8),
            "predecision_previous_action": np.full((256, 12, roster), 255, dtype=np.uint8),
            "predecision_previous_success": np.zeros((256, 12, roster), dtype=np.uint8),
            "poststep_previous_success": np.zeros((256, 12, roster), dtype=np.uint8),
            "terminal_delivered": np.zeros((256, 2, 3), dtype=np.uint8),
            **{
                f"metric_{name}": np.zeros((256, 12), dtype="<u4")
                for name in (
                    "dw", "de", "radio_actions", "waste_actions",
                    "new_timely_deliveries", "expired_arrivals", "duplicate_arrivals",
                    "collision_loss", "empty_actions",
                )
            },
        }
        for start in range(0, 256, 32):
            episodes = list(range(start, start + 32))
            environment = B01NativeBatchEnvironment(adapter, roster=roster, lanes=32)
            environment.reset([
                evaluation_tape(
                    root, seed_label=ROOT_LABELS[0], roster=roster, episode=episode,
                )
                for episode in episodes
            ])
            for slot in range(12):
                observation = environment.observe()
                arrays_np["observation"][start:start + 32, slot] = observation.observations
                if slot > 0:
                    arrays_np["predecision_previous_action"][start:start + 32, slot] = (
                        observation.observations[:, :, 15:21].argmax(axis=-1).astype(np.uint8)
                    )
                arrays_np["predecision_previous_success"][start:start + 32, slot] = (
                    observation.observations[:, :, 21].astype(np.uint8)
                )
                step = environment.step(arrays_np["actions"][start:start + 32, slot])
                arrays_np["poststep_previous_success"][start:start + 32, slot] = (
                    step.previous_success.astype(np.uint8)
                )
                for lane, primitive in enumerate(step.primitives):
                    direct = asdict(primitive)
                    row = start + lane
                    for name, source in {
                        "dw": "dw", "de": "de", "radio_actions": "radio_actions",
                        "waste_actions": "waste_actions",
                        "new_timely_deliveries": "successful_deliveries",
                        "expired_arrivals": "expired", "duplicate_arrivals": "duplicate",
                        "collision_loss": "collision", "empty_actions": "empty_radio",
                    }.items():
                        arrays_np[f"metric_{name}"][row, slot] = direct[source]
            snapshots = environment.snapshot()
            for lane, episode in enumerate(episodes):
                state = NativeStateV1.from_buffer_copy(
                    snapshots[lane * STATE_SIZE:(lane + 1) * STATE_SIZE]
                )
                arrays_np["terminal_delivered"][episode] = np.ctypeslib.as_array(
                    state.delivered
                ).reshape(2, 3)
        arrays = {}
        for name, array in arrays_np.items():
            path = (tmp_path / f"native-replay-{name}.bin").resolve()
            array.tofile(path)
            arrays[name] = {
                "path": str(path), "dtype": np.dtype(array.dtype).str,
                "shape": list(array.shape), "order": "C", "byte_count": int(array.nbytes),
            }
        shard = {
            "schema": "FRRIE_B01_PRIMITIVE_TRACE_SHARD_V1",
            "seed_label": ROOT_LABELS[0], "arm": "PHY_TRUST", "checkpoint": 0,
            "roster": roster, "intervention": "INTACT",
            "coordinate_order": ["episode", "slot", "entity"],
            "arrays": arrays, "complete": True,
        }
        replay = replay_direct_primitive_trace_shard(
            shard, manifest=b01_manifest, invocation_binding=binding, adapter=adapter,
        )
        assert replay["native_replay"] is True
        assert replay["validation_replay_work"] == {
            "native_reset_calls": 8, "native_observe_calls": 96,
            "native_step_calls": 96, "environment_slots": 3072, "native_width": 32,
        }
        assert replay["scientific_work_accounting"] == (
            "EXCLUDED_POSTHOC_DETERMINISTIC_VALIDATION"
        )
        assert replay["stepoutput_to_next_observe_revalidated"] is True
        assert replay["terminal_no_pending_revalidated"] is True
    finally:
        if artifact_bytes is not None and artifact.exists():
            assert artifact.read_bytes() == artifact_bytes
            bytes_path = Path(os.environ["FRRIE_B01_NATIVE_REPLAY_BYTES_PATH"])
            bytes_path.write_bytes(artifact_bytes)
