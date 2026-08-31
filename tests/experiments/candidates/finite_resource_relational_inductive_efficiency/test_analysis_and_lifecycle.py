import json
import struct
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest
import experiments.candidates.finite_resource_relational_inductive_efficiency.lifecycle as lifecycle_module

from experiments.candidates.finite_resource_relational_inductive_efficiency.analysis import (
    analyze_complete_panel,
    expected_checkpoint_inventory,
    expected_result_binding,
    validate_complete_panel,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.checkpoint import (
    learned_arm_state_bytes, serialize_checkpoint, write_checkpoint_atomic,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    FRRIE_COMPLETE_PANEL_RESULT_V1,
    FRRIE_COMPLETE_PANEL_RESULT_V2,
    FRRIE_TERMINAL_V2,
    LEARNED_ARMS, QUANTITY_ORDER, expected_block_checkpoint_path,
    manifest_packet_contract,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import HORIZON
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import expected_native_contract
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.lifecycle import (
    LifecycleError,
    ROOT_MARKER_NAME,
    claim_fresh_roots,
    publish_terminal,
)


def _materialize_checkpoint_files(manifest):
    packet = {
        "schema": "FRRIE_SEALED_SEED_PACKET_V2", "version": 2,
        "manifest_contract": manifest_packet_contract(manifest),
        "blocks": list(manifest["seed_blocks"]),
        "addressed_rng_roots": [f"{index:064x}" for index in range(1, 25)],
        "generation_provenance": "TEST_GENERATION_PROVENANCE_V2",
        "no_prior_use": True, "sealed": True, "complete": True,
    }
    packet_path = Path(manifest["sealed_seed_packet"]["path"])
    if not packet_path.exists():
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        with packet_path.open("x", encoding="utf-8") as handle:
            json.dump(packet, handle)
    paths = [expected_block_checkpoint_path(manifest, block) for block in manifest["seed_blocks"]]
    if all(path.is_file() for path in paths):
        return
    phy, edge = initialize_paired_arms(
        AddressedRNG(b"A" * 32), "FRRIE-TEST-ONLY-ANALYSIS-CHECKPOINTS"
    )
    arm_state = learned_arm_state_bytes({"PHY_TRUST": phy, "EDGE_FLEX": edge})
    optimizer_payload = b"\0" * (OPTIMIZER_PAYLOAD_BYTE_COUNT - 8) + struct.pack("<Q", 512)
    optimizer_blob = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        len(optimizer_payload),
    ) + optimizer_payload
    native = asdict(expected_native_contract(manifest["compute"]))
    for block, path in zip(manifest["seed_blocks"], paths):
        if path.exists():
            continue
        data = serialize_checkpoint(
            manifest_contract=manifest, native_contract=native,
            seed_packet_contract=packet,
            seed_packet_path=manifest["sealed_seed_packet"]["path"],
            seed_block=block, update=512,
            frontiers={
                "training_update": 512, "minibatch_cursor": 0,
                "factual_episode_cursor": 512 * 64,
                "factual_environment_slot_cursor": 393_216,
                "alternative_suffix_environment_slot_cursor": 1_490_944,
                "evaluation_checkpoint_cursor": 0,
            },
            arm_state_bytes=arm_state,
            optimizer_state_bytes={arm: optimizer_blob for arm in LEARNED_ARMS},
            work_receipts=checkpoint_cumulative_work(manifest["compute"]),
            rng_frontier={
                "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1", "stateless": True,
                "tape_contract": {"schema": "TEST_ANALYSIS_TAPE", "block": block},
            },
        )
        write_checkpoint_atomic(path, data)
from experiments.candidates.finite_resource_relational_inductive_efficiency.work import (
    checkpoint_cumulative_work,
    final_cumulative_work,
)


def _vector(role, *, shadow=False):
    if role == "RIDGE_RELAY":
        return [0.0, 0.0, 0.7 if not shadow else 0.1, 0.1, 0.1, 0.1 if not shadow else 0.7]
    return [0.8 if not shadow else 0.1, 0.1, 0.0, 0.0, 0.0, 0.1 if not shadow else 0.8]


def _probability_history(roster):
    roles = ("WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY")
    return [
        {
            "slot": slot,
            "entity": entity,
            "role": roles[min(entity // (roster // 3), 2)],
            "intact": _vector(roles[min(entity // (roster // 3), 2)]),
            "shadow": _vector(roles[min(entity // (roster // 3), 2)], shadow=True),
        }
        for slot in range(HORIZON)
        for entity in range(roster)
    ]


def _panel(manifest, *, support=True, checkpoint_bytes_revalidated=True):
    if checkpoint_bytes_revalidated:
        _materialize_checkpoint_files(manifest)
    rows = []
    record_cache = {}
    inventory = expected_checkpoint_inventory(
        manifest,
        generation_provenance="TEST_GENERATION_PROVENANCE_V2",
        checkpoint_bytes_revalidated=checkpoint_bytes_revalidated,
    )
    for block in manifest["seed_blocks"]:
        for arm in ("PHY_TRUST", "EDGE_FLEX", "UNIFORM_LEGAL"):
            for roster in (9, 15, 6, 21):
                for intervention in ("INTACT", "SEMANTIC_COLUMN_ROTATE"):
                    if arm == "PHY_TRUST" and intervention == "INTACT":
                        dw = de = 2
                    elif arm == "UNIFORM_LEGAL":
                        dw = de = 0
                    else:
                        dw = de = 1
                    cache_key = (arm, roster, intervention, dw, de)
                    if cache_key not in record_cache:
                        record_cache[cache_key] = (
                            _probability_history(roster)
                            if arm == "PHY_TRUST" and intervention == "INTACT"
                            else None
                        )
                    probabilities = record_cache[cache_key]
                    tapes = [
                        {
                            "schema": "FRRIE_ADDRESSED_TAPE_V1",
                            "seed_block": block,
                            "purpose": "EVALUATE",
                            "roster": roster,
                            "update": 512,
                            "episode": episode,
                        }
                        for episode in range(256)
                    ]
                    records = [
                        {
                            "episode": episode,
                            "tape_contract": tapes[episode],
                            "dw": dw,
                            "de": de,
                            "waste": 0.0,
                            "decision_probability_pairs": probabilities,
                        }
                        for episode in range(256)
                    ]
                    rows.append({
                        "seed_block": block,
                        "arm": arm,
                        "checkpoint": 512,
                        "roster": roster,
                        "intervention": intervention,
                        "episodes": 256,
                        "tape_contracts": tapes,
                        "episode_records": records if support and checkpoint_bytes_revalidated else None,
                        "support_valid": support,
                        "support_reason": None if support else "ENDPOINT_SUPPORT_UNAVAILABLE",
                        "result_binding": expected_result_binding(
                            manifest, inventory, block=block, arm=arm, roster=roster,
                            intervention=intervention,
                        ),
                    })
    return {
        "schema": FRRIE_COMPLETE_PANEL_RESULT_V2,
        "manifest_contract": manifest,
        "complete": True,
        "receipts": {
            "checkpoint": checkpoint_cumulative_work(manifest["compute"]),
            "work": final_cumulative_work(manifest["compute"]),
            "support": {
                "endpoint_support_complete": support,
                "complete": True,
                "reason": None if support else "ENDPOINT_SUPPORT_UNAVAILABLE",
            },
        },
        "checkpoint_inventory": inventory,
        "cells": rows,
    }


def test_v2_extracts_exact_order_but_emits_no_inference(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    result = analyze_complete_panel(panel, manifest)
    assert result["status"] == "UNRESOLVED_ANALYSIS_METHOD_UNFROZEN"
    assert result["scientific_polarity"] is None
    assert result["intervals"] is None
    assert result["predicates"] == []
    assert result["quantity_order"] == list(QUANTITY_ORDER)
    assert list(result["block_quantities"]) == manifest["seed_blocks"]
    assert all(tuple(values) == QUANTITY_ORDER for values in result["block_quantities"].values())


def test_probability_tv_is_block_level_and_v1_or_partial_is_invalid(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    result = analyze_complete_panel(panel, manifest)
    assert result["block_quantities"][manifest["seed_blocks"][0]]["V_N6"] == pytest.approx(2.0 / 3.0)

    legacy = dict(panel)
    legacy["schema"] = FRRIE_COMPLETE_PANEL_RESULT_V1
    assert analyze_complete_panel(legacy, manifest)["status"] == "INVALID"
    partial = dict(panel)
    partial["cells"] = list(panel["cells"][:-1])
    assert analyze_complete_panel(partial, manifest)["status"] == "INVALID"
    with pytest.raises(ValueError, match="partial"):
        validate_complete_panel(partial, manifest)


def test_support_and_receipts_fail_closed(manifest_factory):
    manifest = manifest_factory()
    unsupported = analyze_complete_panel(_panel(manifest, support=False), manifest)
    assert unsupported["status"] == "NONIDENTIFICATION_ENDPOINT_SUPPORT"
    broken = _panel(manifest)
    broken["cells"][0]["result_binding"]["rng_tape_binding"]["branch_independent"] = False
    invalid = analyze_complete_panel(broken, manifest)
    assert invalid["status"] == "INVALID"
    assert invalid["scientific_values_emitted"] is False
    assert "block_quantities" not in invalid

    exposed = _panel(manifest, support=False)
    exposed["cells"][0]["episode_records"] = []
    assert analyze_complete_panel(exposed, manifest)["status"] == "INVALID"


def test_probability_floor_and_fixed_slot_roles_fail_closed(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    decision = panel["cells"][0]["episode_records"][0]["decision_probability_pairs"][0]
    decision["intact"] = [0.999, 0.001, 0.0, 0.0, 0.0, 0.0]
    assert analyze_complete_panel(panel, manifest)["status"] == "INVALID"

    panel = _panel(manifest)
    history = panel["cells"][0]["episode_records"][0]["decision_probability_pairs"]
    assert [row["role"] for row in history[:9]] == ["WEST_SURVEYOR"] * 3 + ["EAST_SURVEYOR"] * 3 + ["RIDGE_RELAY"] * 3
    history[0]["role"] = "EAST_SURVEYOR"
    assert analyze_complete_panel(panel, manifest)["status"] == "INVALID"


def test_episode_tape_and_cell_result_bindings_fail_closed(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    panel["cells"][0]["episode_records"][1]["episode"] = 0
    invalid = analyze_complete_panel(panel, manifest)
    assert invalid["status"] == "INVALID"
    assert invalid["scientific_values_emitted"] is False

    panel = _panel(manifest)
    panel["cells"][0]["episode_records"][1]["tape_contract"] = panel["cells"][0]["tape_contracts"][0]
    assert analyze_complete_panel(panel, manifest)["status"] == "INVALID"

    panel = _panel(manifest)
    panel["cells"][0]["result_binding"]["source"]["path"] = "fabricated-checkpoint.json"
    assert analyze_complete_panel(panel, manifest)["status"] == "INVALID"


def test_checkpoint_inventory_without_byte_revalidation_is_engineering_blocker(manifest_factory):
    manifest = manifest_factory()
    result = analyze_complete_panel(
        _panel(manifest, checkpoint_bytes_revalidated=False), manifest,
    )
    assert result["status"] == "TECHNICAL_FAILURE"
    assert result["engineering_blockers"] == ["CHECKPOINT_BYTES_NOT_REVALIDATED"]
    assert result["scientific_values_emitted"] is False
    assert "block_quantities" not in result

    panel = _panel(manifest)
    panel["checkpoint_inventory"]["blocks"][0]["checkpoint_path"] = "wrong"
    assert analyze_complete_panel(panel, manifest)["status"] == "INVALID"


def test_episode_endpoint_is_averaged_before_block_estimands(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    first = panel["cells"][0]
    first["episode_records"][0]["dw"], first["episode_records"][0]["de"] = 3, 0
    first["episode_records"][1]["dw"], first["episode_records"][1]["de"] = 0, 3
    rows = validate_complete_panel(panel, manifest)
    assert rows[0]["native_return"] < 0.7


def test_paired_fresh_roots_and_v2_create_only_terminal(manifest_factory):
    manifest = manifest_factory()
    root, checkpoint = claim_fresh_roots(manifest)
    analysis = analyze_complete_panel(_panel(manifest), manifest)
    assert (root / ROOT_MARKER_NAME).is_file()
    assert (checkpoint / ROOT_MARKER_NAME).is_file()
    target = publish_terminal(
        root,
        status="UNRESOLVED_ANALYSIS_METHOD_UNFROZEN",
        manifest_contract=manifest,
        analysis=analysis,
    )
    assert FRRIE_TERMINAL_V2 in target.read_text(encoding="ascii")
    with pytest.raises(LifecycleError):
        publish_terminal(root, status="INVALID", manifest_contract=manifest)


def test_paired_root_stale_and_direct_marker_mismatch_fail(manifest_factory, tmp_path):
    stale = manifest_factory()
    stale["roots"] = {"output": str(tmp_path / "stale-run" / "output"), "checkpoint": str(tmp_path / "stale-run" / "checkpoint")}
    (tmp_path / "stale-run.FRRIE_CLAIM_V2.tmp").mkdir()
    with pytest.raises(LifecycleError, match="stale"):
        claim_fresh_roots(stale)

    partial = manifest_factory()
    partial["roots"] = {"output": str(tmp_path / "partial-run" / "output"), "checkpoint": str(tmp_path / "partial-run" / "checkpoint")}
    (tmp_path / "partial-run").mkdir()
    (tmp_path / "partial-run" / "foreign.txt").write_text("do not remove", encoding="ascii")
    with pytest.raises(LifecycleError, match="common run parent"):
        claim_fresh_roots(partial)
    assert (tmp_path / "partial-run" / "foreign.txt").is_file()

    manifest = manifest_factory()
    manifest["roots"] = {"output": str(tmp_path / "paired-run" / "output"), "checkpoint": str(tmp_path / "paired-run" / "checkpoint")}
    output, checkpoint = claim_fresh_roots(manifest)
    (checkpoint / ROOT_MARKER_NAME).write_text("{}", encoding="ascii")
    with pytest.raises(LifecycleError, match="checkpoint.*marker"):
        publish_terminal(output, status="INVALID", manifest_contract=manifest)


def test_paired_root_parent_rename_crash_rolls_back_staging(manifest_factory, tmp_path, monkeypatch):
    manifest = manifest_factory()
    manifest["roots"] = {"output": str(tmp_path / "crash-run" / "output"), "checkpoint": str(tmp_path / "crash-run" / "checkpoint")}

    def fail_rename(_source, _target):
        raise OSError("simulated parent rename crash")

    monkeypatch.setattr(lifecycle_module.os, "rename", fail_rename)
    with pytest.raises(LifecycleError, match="simulated parent rename crash"):
        claim_fresh_roots(manifest)
    assert not (tmp_path / "crash-run").exists()
    assert not (tmp_path / "crash-run.FRRIE_CLAIM_V2.tmp").exists()
