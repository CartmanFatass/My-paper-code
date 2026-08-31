import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.analysis import (
    analyze_complete_panel,
    validate_complete_panel,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    FRRIE_COMPLETE_PANEL_RESULT_V1,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import HORIZON
from experiments.candidates.finite_resource_relational_inductive_efficiency.lifecycle import (
    LifecycleError,
    claim_fresh_root,
    publish_terminal,
)


def _actions(roster, arm):
    count = HORIZON * (roster // 3)
    if arm == "PHY_TRUST":
        return {
            "WEST_SURVEYOR": [count, 0, 0, 0, 0, 0],
            "EAST_SURVEYOR": [count, 0, 0, 0, 0, 0],
            "RIDGE_RELAY": [0, 0, 0, 0, count, 0],
        }
    if arm == "EDGE_FLEX":
        return {
            "WEST_SURVEYOR": [0, count, 0, 0, 0, 0],
            "EAST_SURVEYOR": [0, count, 0, 0, 0, 0],
            "RIDGE_RELAY": [0, 0, 0, 0, 0, count],
        }
    return {
        "WEST_SURVEYOR": [count, 0, 0, 0, 0, 0],
        "EAST_SURVEYOR": [count, 0, 0, 0, 0, 0],
        "RIDGE_RELAY": [0, 0, count, 0, 0, 0],
    }


def _panel(manifest, *, support=True):
    rows = []
    for block in manifest["seed_blocks"]:
        for arm in ("PHY_TRUST", "EDGE_FLEX", "UNIFORM_LEGAL"):
            for checkpoint in manifest["training"]["checkpoints"]:
                for roster in (9, 15, 6, 21):
                    for intervention in ("INTACT", "SEMANTIC_COLUMN_ROTATE"):
                        if arm == "PHY_TRUST" and intervention == "INTACT":
                            dw = de = 2
                        elif arm == "UNIFORM_LEGAL":
                            dw = de = 0
                        else:
                            dw = de = 1
                        tapes = [
                            {
                                "schema": "FRRIE_ADDRESSED_TAPE_V1",
                                "seed_block": block,
                                "purpose": "EVALUATE",
                                "roster": roster,
                                "update": checkpoint,
                                "episode": episode,
                            }
                            for episode in range(256)
                        ]
                        records = [
                            {
                                "dw": dw,
                                "de": de,
                                "waste": 0.0,
                                "action_counts_by_role": _actions(roster, arm),
                            }
                            for _ in range(256)
                        ]
                        rows.append({
                            "seed_block": block,
                            "arm": arm,
                            "checkpoint": checkpoint,
                            "roster": roster,
                            "intervention": intervention,
                            "episodes": 256,
                            "tape_contracts": tapes,
                            "episode_records": records if support else None,
                            "support_valid": support,
                        })
    return {
        "schema": FRRIE_COMPLETE_PANEL_RESULT_V1,
        "manifest_contract": manifest,
        "complete": True,
        "cells": rows,
    }


def test_complete_only_analysis_is_unresolved_without_inference_method(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    result = analyze_complete_panel(panel, manifest)
    assert result["status"] == "UNRESOLVED_ANALYSIS_METHOD_UNFROZEN"
    assert result["scientific_polarity"] is None
    assert set(result["deterministic_gate_inputs"]) >= {
        "heldout_direct_return", "worst_basin_delivery", "treatment_cut_loss",
        "legal_action_tv", "differential_cut_attenuation",
    }
    panel["cells"].pop()
    with pytest.raises(ValueError, match="cell contract set"):
        validate_complete_panel(panel, manifest)


def test_endpoint_support_failure_is_nonidentification(manifest_factory):
    manifest = manifest_factory()
    result = analyze_complete_panel(_panel(manifest, support=False), manifest)
    assert result["status"] == "NONIDENTIFICATION_ENDPOINT_SUPPORT"
    assert result["treatment_contrasts_computed"] is False


def test_episode_level_endpoint_is_not_endpoint_of_cell_means(manifest_factory):
    manifest = manifest_factory()
    panel = _panel(manifest)
    cell = panel["cells"][0]
    cell["episode_records"][0]["dw"], cell["episode_records"][0]["de"] = 3, 0
    cell["episode_records"][1]["dw"], cell["episode_records"][1]["de"] = 0, 3
    rows = validate_complete_panel(panel, manifest)
    assert rows[0]["native_return"] < 0.7


def test_fresh_root_and_create_only_terminal(tmp_path):
    root = claim_fresh_root(tmp_path / "fresh")
    assert (root / ".FRRIE_FRESH_ROOT_V1").is_file()
    with pytest.raises(LifecycleError):
        claim_fresh_root(root)
    contract = {"schema": "TEST_MANIFEST_V1"}
    publish_terminal(root, status="INVALID", manifest_contract=contract)
    with pytest.raises(LifecycleError):
        publish_terminal(root, status="INVALID", manifest_contract=contract)
