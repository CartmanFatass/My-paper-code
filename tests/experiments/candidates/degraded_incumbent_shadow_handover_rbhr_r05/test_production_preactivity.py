from __future__ import annotations

from pathlib import Path
import hashlib

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_analysis import (
    aggregate_atomic_labels,
    complete_estimand_manifest,
    complete_estimand_source_manifest,
    complete_hypothesis_inventory,
    endpoint_vector,
    estimand_manifest_identity,
    reduce_fork_rows,
    reduce_full_cell_rows,
    run_result_blind_analyzer_seam,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_backend import (
    TestNativeBatch as NativeBatch,
    TEST_MASTER,
    artifact_identity,
    empty_step_rows,
    native_protocol_audit,
    native_natural_protocol_trace,
    native_protocol_transition_probe,
    open_production_batch,
    rng_words_test_native,
    scan_test_candidate_attempts,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_contract import (
    PreactivityAuthority,
    ProductionContractError,
    complete_inventory,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_lifecycle import (
    BlindedFrontierPlan,
    CompletePanelLifecycleState,
    ProductionLifecycleError,
    run_result_blind_lifecycle_seam,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_preactivity import (
    BASELINE_PLANNING_PROJECTION,
    HIGH_GATES,
    benchmark_native_rollout,
    run_native_connected_training_seam,
    run_native_connected_analyzer_acceptance,
    verify_science_composite,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_protocol import (
    test_wire_fixture_inventory as wire_fixture_inventory,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_training import (
    ExactPolicyGraph,
    arm_mask_inventory,
    run_full_4096_dry_update,
    run_result_blind_training_seam,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_tapes import (
    candidate_accounting_identity,
    complete_accepted_tape_coordinates,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def test_complete_inventory_is_exact_and_has_only_update_1024_checkpoint() -> None:
    value = complete_inventory()
    assert value["training_jobs"] == 120
    assert value["training_transitions"] == 503_316_480
    assert value["accepted_tapes"] == 11_520
    assert value["candidate_attempts_max"] == 1_152_000_000
    assert value["candidate_rejected_attempt_count"] == "UNKNOWN_BEFORE_VALUE_BLIND_MASTER"
    assert value["recovery_witness_ticks"] == 33_177_600
    assert value["evaluation_episodes"] == 115_200
    assert value["evaluation_ticks"] == 138_240_000
    assert value["atomic_supercells"] == 6
    assert value["bootstrap_resamples"] == 99_999
    assert value["branch_count"] == 15
    assert value["checkpoint_updates"] == [1_024]
    assert value["partial_interpretation_permitted"] is False


def test_complete_accepted_tape_coordinate_accounting_is_unique_and_unopened() -> None:
    rows = complete_accepted_tape_coordinates()
    identity = candidate_accounting_identity()
    assert len(rows) == len({row.canonical_key() for row in rows}) == 11_520
    assert identity["calibration_coordinate_count"] == 4_608
    assert identity["claim_coordinate_count"] == 6_912
    assert identity["candidate_attempts_global_cap"] == 1_152_000_000
    assert identity["qualification_evaluated"] is False


def test_science_composite_hashes_are_bound() -> None:
    observed = verify_science_composite(REPOSITORY_ROOT)
    assert len(observed) == 7
    assert all(len(value) == 64 for value in observed.values())


def test_production_entry_refuses_without_later_root_lease() -> None:
    with pytest.raises(ProductionContractError, match="Root lease"):
        open_production_batch(authority=None, width=32)


def test_native_interactive_and_fused_rollout_have_exact_shapes() -> None:
    batch = NativeBatch(32, PreactivityAuthority())
    one = batch.step(empty_step_rows(32))
    assert one["actor"].shape == (32, 4, 54)
    assert one["critic"].shape == (32, 58)
    assert np.all(one["tick"] == 1)
    rows = np.repeat(empty_step_rows(32)[None, :], 64, axis=0)
    output = batch.rollout(rows)
    assert output["actor"].shape == (64, 32, 4, 54)
    assert output["critic"].shape == (64, 32, 58)
    assert np.isfinite(output["actor"]).all()
    assert np.isfinite(output["critic"]).all()
    assert np.all(output["tick"][-1] == 65)
    assert np.all(output["protocol_wire_messages"][-1] >= 3 * 64)
    assert np.all(output["protocol_wire_hash"][-1] != 0)
    step_fields = set(empty_step_rows(1).dtype.names or ())
    assert not {"camera_z", "camera_present", "radio_margin", "source_noise", "wind_eta", "origin_certificate_pass"} & step_fields


def test_native_fused_rollout_reaches_exact_1200_tick_terminal() -> None:
    batch = NativeBatch(1, PreactivityAuthority())
    rows = np.repeat(empty_step_rows(1)[None, :], 1_200, axis=0)
    output = batch.rollout(rows)
    assert int(output["tick"][-1, 0]) == 1_200
    assert int(output["terminal"][-1, 0]) == 1


def test_native_real_sham_clone_differs_only_at_authority_seam() -> None:
    batch = NativeBatch(8, PreactivityAuthority())
    fork = batch.clone_real_sham()
    real = fork["real_state"]
    sham = fork["sham_state"]
    assert np.all(real["owner"] == 1 - sham["owner"])
    assert np.all(real["service_epoch"] == sham["service_epoch"])
    assert np.all(real["handover_used"] == 1)
    assert np.all(sham["handover_used"] == 1)
    for field in ("next_payload_sequence", "source_sequence", "base_source_sequence", "p", "v", "battery"):
        assert np.array_equal(real[field], sham[field])
    assert np.all(fork["byte_identical_telemetry"] == 1)
    assert np.array_equal(fork["real_telemetry_sha256"], fork["sham_telemetry_sha256"])


def test_native_script_and_identity_are_fail_closed_and_native_only() -> None:
    batch = NativeBatch(48, PreactivityAuthority())
    script = batch.scripted_actions()
    assert script.shape == (48,)
    assert np.isfinite(script["raw_action"]).all()
    assert np.isin(script["transfer"], (0, 1)).all()
    identity = artifact_identity()
    assert identity["component"] == "dish.rbhr.r05.full_host"
    assert identity["full_reset_step_cpp"] is True
    assert identity["python_environment_fallback"] is False
    assert identity["accepted_native_rng_generator_service"]["sha256"] == "7c1ab7f76d343ae27a2830f9928d8a909c42838aec4aea3ace8d422090a3d020"
    protocol = native_protocol_audit()
    assert protocol["wire_sizes"] == [40, 64, 64, 96, 48, 32, 32, 24]
    assert protocol["all_integrity_verified"] is True
    assert protocol["all_tamper_rejected"] is True
    transition = native_protocol_transition_probe()
    assert transition["source_lineage_preserved"] is True
    assert transition["locks_released"] is True
    assert transition["cas_applied"] is True
    assert transition["application_reason"] == 0
    assert transition["owner_before"] == 0 and transition["owner_after"] == 1
    assert transition["service_epoch_after"] == 1
    assert transition["actuator_owner_after"] == 1
    assert transition["recurrent_promotion_verified"] is True
    natural = native_natural_protocol_trace()
    assert natural["snapshot_accepted"] is True
    assert natural["readiness_accepted"] is True
    assert natural["cas_applied_count"] == 8
    assert natural["owner_epoch_actuator_consistent"] is True
    scanner = scan_test_candidate_attempts(4, PreactivityAuthority())
    assert scanner.shape == (4,)
    assert set(scanner.dtype.names or ()) == {
        "eligible", "origin_tick", "stratum", "real_service_ticks",
        "retain_service_ticks", "opportunities_checked", "rejection_mask", "advantage",
    }
    controlled = scan_test_candidate_attempts(12, PreactivityAuthority(), clear_channel_fixture=True)
    assert np.count_nonzero(controlled["eligible"]) > 0
    assert np.count_nonzero(controlled["stratum"] == 0) > 0


def test_native_full_master_address_words_match_sha256() -> None:
    addresses = (
        "DISH/RBHR/R05/INIT/0/TRAIN/TARGET_VISUAL_MASK/K4/NONE/NONE/0/0/COMMON/DEGRADED_ONLY/NONE/0/0/NONE/NONE/NONE/NONE/PARAMETER_UNIFORM/0",
        "DISH/RBHR/R05/INFERENCE/NONE/BOOTSTRAP/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/1/BOOTSTRAP_BLOCK/0",
    )
    observed = rng_words_test_native(addresses, PreactivityAuthority())
    expected = tuple(
        int.from_bytes(hashlib.sha256(TEST_MASTER + b"\x00" + address.encode("utf-8")).digest()[:8], "big")
        for address in addresses
    )
    assert observed == expected


def test_exact_policy_graph_and_batched_training_seam() -> None:
    graph = ExactPolicyGraph()
    assert graph.encoder1.in_features == 54 and graph.encoder2.out_features == 128
    assert graph.critic1.in_features == 58
    assert graph.service_q.out_features == 20
    value = run_result_blind_training_seam()
    assert value["test_only"] is True
    assert value["scientific_model"] is False
    assert value["checkpoint_created"] is False
    assert value["loss_finite"] is True
    assert value["gradient_norm_finite"] is True
    assert value["flex_zero_exact"] is True
    assert value["checkpoint_resume_projected_bytes_per_job"] > 0


def test_full_4096_update_and_all_arm_authority_masks() -> None:
    masks = arm_mask_inventory()
    assert masks["STRUCTURED"]["prepare_bernoulli"] > 0
    assert masks["NEVER"]["noop_bernoulli"] == masks["NEVER"]["commit_bernoulli"]
    assert masks["NEVER"]["transfer_authority"] == 0
    assert masks["IMMEDIATE"]["prepare_bernoulli"] == 0
    assert masks["HYSTERESIS"]["commit_bernoulli"] == 0
    value = run_full_4096_dry_update()
    assert value["transitions"] == 4_096
    assert value["epochs"] == 4
    assert value["minibatches_per_epoch"] == 8
    assert value["optimizer_steps"] == 32
    assert value["losses_finite"] is True
    assert value["checkpoint_resume_equal"] is True
    assert value["welford_counts"] == {"actor": 16_384, "snapshot": 256, "critic": 4_096}
    connected = run_native_connected_training_seam()
    assert connected["fragment_source"] == "CPP20_NATIVE_PROTOCOL_TEST_ROLLOUT"
    assert connected["native_fragment_binding"]["native_ticks"] == 4_096
    assert connected["optimizer_steps"] == 32
    assert connected["losses_finite"] is True
    analyzer = run_native_connected_analyzer_acceptance()
    assert analyzer["native_tapes"] == 16
    assert analyzer["estimand_source_count"] == 6_990
    assert analyzer["joint_resamples"] == 99_999
    assert analyzer["wire_hash_nonzero"] is True


def test_reducers_max_t_and_all_fifteen_branches() -> None:
    bits = np.ones((16, 200), dtype=np.int8)
    bits[:, 0] = 0
    endpoint = endpoint_vector(bits)
    assert tuple(endpoint) == ("MEAN", "TAIL", "DEFICIT", "DELAY")
    value = run_result_blind_analyzer_seam()
    assert value["resamples"] == 99_999
    assert value["branch_count"] == 15
    assert value["all_intervals_finite"] is True
    assert complete_hypothesis_inventory()["total"] == 6_990
    full = reduce_full_cell_rows(
        np.ones((16, 1_200), dtype=np.int8), [420] * 16,
        np.arange(16, dtype=np.float64) + 1.0, np.zeros((16, 7), dtype=np.int8),
    )
    assert full["row_count"] == 16 and full["endpoints"]["MEAN"] == 1.0
    fork = reduce_fork_rows(np.ones((3, 100), dtype=np.int8), [1.0, 2.0, 3.0], np.zeros((3, 7), dtype=np.int8))
    assert fork["row_count"] == 3 and fork["endpoints"]["TAIL"] == 1.0
    labels = {
        (regime, schedule): "STRUCTURED_ATOMIC_VALUE"
        for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
        for schedule in ("K8", "K4_TO_K12", "K12_TO_K4")
    }
    assert aggregate_atomic_labels(labels)["cross_regime"] == "STRUCTURED_CROSS_REGIME_VALUE"


def test_complete_6990_estimand_identity_mapper_is_unique_and_value_blind() -> None:
    rows = complete_estimand_manifest()
    identity = estimand_manifest_identity()
    assert len(rows) == len(set(rows)) == 6_990
    assert identity["count"] == identity["unique"] == 6_990
    assert identity["value_bearing"] is False
    assert identity["first"] == rows[0] and identity["last"] == rows[-1]
    sources = complete_estimand_source_manifest()
    assert sources["count"] == sources["unique"] == 6_990
    assert sources["block_rows_required_per_estimand"] == 24
    assert sources["joint_resamples"] == 99_999


def test_all_exact_wire_schemas_round_trip_and_reject_tamper() -> None:
    identity = wire_fixture_inventory()
    assert identity["message_count"] == 8
    assert identity["wire_sizes"] == {
        "SOURCE": 40, "SERVICE_RELAY": 64, "STATE": 64, "SNAPSHOT": 96,
        "READINESS": 48, "COMMIT_INTENT": 32, "NOOP_INTENT": 32,
        "COMMIT_RESULT": 24,
    }
    assert identity["all_integrity_verified"] is True
    assert identity["all_tamper_rejected"] is True


def test_atomic_resume_plan_is_non_evaluable(tmp_path: Path) -> None:
    plan = BlindedFrontierPlan()
    assert plan.resume_generations_per_job == 64
    assert plan.payload()["evaluation_checkpoint"] == 1_024
    value = run_result_blind_lifecycle_seam(tmp_path, 2_000_000)
    assert value["duplicate_rejected"] is True
    assert value["stale_parent_rejected"] is True
    assert value["atomic_job_component_count"] == 13
    assert value["question_relevant_output"] is False
    state = CompletePanelLifecycleState.preactivity()
    assert state.payload()["phase"] == "PREACTIVITY"
    invalid = CompletePanelLifecycleState("EVALUATION", (0,) * 120, 0, 0, 0, 0)
    with pytest.raises(ProductionLifecycleError, match="checkpoint barrier"):
        invalid.validate()


def test_native_rollout_measurement_and_high_projection_are_within_exact_gates() -> None:
    value = benchmark_native_rollout(32, steps=64)
    assert value["lane_ticks"] == 2_048
    assert value["lane_ticks_per_second"] > 0
    assert value["all_finite"] is True
    for name, gate in HIGH_GATES.items():
        assert BASELINE_PLANNING_PROJECTION[name]["high"] <= gate
