from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    TestNativeBatch, artifact_identity, empty_step_rows, open_production_batch,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_contract import (
    R06ContractError, TestAuthority as R06TestAuthority, complete_inventory,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_inference import (
    aggregate_schedule_regime_intersections, classify_atomic,
    common_anchor_classify, inference_manifest, reduce_speed_cell,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_full_panel import (
    STAGE_TOTALS, production_surface_manifest,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_population import (
    address, complete_evaluation_coordinates, population_manifest,
)


def test_complete_population_is_exact_arm_independent_factorial() -> None:
    manifest = population_manifest()
    assert manifest["coordinate_count"] == 11_520
    assert manifest["geometry_factorial_complete"]
    assert manifest["identity_combinations_twice_per_speed_cell"]
    assert manifest["clock_support_nonempty_per_speed_cell"]
    assert manifest["turn_magnitude_exact_across_blocks"]
    assert not manifest["candidate_attempt_coordinate"]
    assert not manifest["rejection_or_search"]
    assert complete_inventory()["scientific_admission_failure_probability"] == 0.0


def test_r06_address_deletes_accepted_and_candidate_coordinates() -> None:
    value = address(
        purpose="WIND", block=0, split="CLAIM", regime="TARGET_VISUAL_MASK",
        schedule="K8", evaluation_slot=0, tick=0, field="WIND_X", draw_index=0,
    )
    assert value.startswith("DISH/RBHR/R06/")
    assert "accepted_slot" not in value and "candidate_attempt" not in value
    assert len(value.split("/")) == 22


def test_native_abi_binds_exact_r06_population_row() -> None:
    identity = artifact_identity()
    assert identity["abi_version"] == 1
    assert identity["component"] == "dish.rbhr.r06.full_host"
    assert identity["full_reset_step_cpp"]
    batch = TestNativeBatch(16, R06TestAuthority())
    output = batch.step(empty_step_rows(16))
    assert output["actor"].shape == (16, 4, 54)
    assert np.isfinite(output["actor"]).all()


def test_r06_production_entry_refuses_without_later_decision_and_lease() -> None:
    with pytest.raises(R06ContractError, match="later Portfolio decision"):
        open_production_batch(authority=None, width=1)


def test_speed_reducer_uses_exact_sixteen_tapes() -> None:
    rows = np.ones((16, 1_200), dtype=np.int8)
    value = reduce_speed_cell(rows, [420] * 16)
    assert value == {"MEAN": 1.0, "TAIL": 1.0, "DEFICIT": 0.0, "DELAY": 0.0}
    with pytest.raises(Exception):
        reduce_speed_cell(rows[:15], [420] * 15)


def test_common_anchor_and_schedule_regime_intersections_are_enforced() -> None:
    common = {"protocol_ok": True, "comp": True, "witness": True, "headroom": True, "precision": True, "support": True}
    row = common_anchor_classify(common, {
        "SPEED_4": {"core": True}, "SPEED_6": {}, "SPEED_8": {"core": True},
    })
    assert row["label"] == "STRUCTURED_ATOMIC_VALUE"
    assert row["qualifying_anchor_speeds"] == ["SPEED_4", "SPEED_8"]
    atomic = {
        (regime, schedule): dict(row)
        for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
        for schedule in ("K8", "K4_TO_K12", "K12_TO_K4")
    }
    aggregate = aggregate_schedule_regime_intersections(atomic)
    assert aggregate["cross_regime"]["label"] == "STRUCTURED_ATOMIC_VALUE"
    assert aggregate["cross_regime"]["common_anchor_speeds"] == ["SPEED_4", "SPEED_8"]


def test_all_fifteen_first_match_branches_remain_reachable() -> None:
    observed = []
    for branch in range(1, 16):
        vector = {"protocol_ok": True, "comp": True, "witness": True, "headroom": True, "precision": True, "support": True}
        if branch == 1: vector["protocol_ok"] = False
        elif branch == 2: vector["comp"] = False
        elif branch == 3: vector["witness"] = False
        elif branch == 4: vector["headroom"] = False
        elif branch == 5: vector["support"] = False
        elif branch == 6: vector["harm"] = True
        elif branch == 7: vector["package_effect"] = True
        elif branch == 8: vector["fork_excluded"] = True
        elif branch == 9: vector["rulequal_i"] = True
        elif branch == 10: vector["rulequal_h"] = True
        elif branch == 11: vector["flexqual"] = True
        elif branch == 12: vector["flex_rel"] = True
        elif branch == 13: vector["core"] = True
        elif branch == 14: vector["nm_all"] = True
        observed.append(classify_atomic(vector)[0])
    assert observed == list(range(1, 16))
    assert inference_manifest()["estimand_count"] == 6_990


def test_full_panel_surface_is_indivisible_and_resource_guarded() -> None:
    value = production_surface_manifest()
    assert value["stages"] == {
        "POPULATION": 11_520, "TRAINING": 122_880,
        "EVALUATION": 115_200, "FORK": 6_912, "INFERENCE": 1,
    }
    assert value["workers_max"] == 8 and value["gpu"] == 0
    assert value["same_identity_successor_slice"]
    assert value["complete_result_firewall"]
    assert not value["partial_values_exposed"]
