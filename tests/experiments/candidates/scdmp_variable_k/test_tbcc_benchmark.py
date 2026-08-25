from __future__ import annotations

import copy

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import benchmark


def test_registered_workload_and_stage_unit_arithmetic() -> None:
    assert benchmark.WIDTHS == (1, 8, 12, 32, 120, 144)
    assert benchmark.FULL_WORKLOAD == {
        "episodes_rollouts": 343_296,
        "allocated_primitive_slots": 124_959_744,
        "maximum_policy_queries": 15_829_632,
        "forced_first_action_interventions": 110_592,
        "adamw_steps": 129_024,
        "final_learned_checkpoints": 96,
    }
    assert 12 * benchmark.STAGE_UNIT_MULTIPLIERS["foundation_update"] == 46_080
    assert 120 * benchmark.STAGE_UNIT_MULTIPLIERS["competence_cell"] == 17_280
    assert 144 * benchmark.STAGE_UNIT_MULTIPLIERS["opportunity_state"] == 110_592
    assert 12 * benchmark.STAGE_UNIT_MULTIPLIERS["order_update"] == 82_944
    assert 120 * benchmark.STAGE_UNIT_MULTIPLIERS["final_evaluation_cell"] == 86_400


def test_width_eight_oracle_native_full_chain_and_mask_positions() -> None:
    row = benchmark._width_measurement(8, 1)
    assert row["oracle_native_equal"] is True
    assert row["full_reset_to_terminal"] is True
    assert row["maximum_absolute_float_difference"] <= 2e-14
    assert row["masked_reset_positions"] == [7]
    assert row["lane_positions_preserved"] is True
    assert row["native_transitions_per_second"] > 0


def test_fixture_controller_batch_and_optimizer_paths_are_deterministic() -> None:
    forward = benchmark._forward_measurement(12, 2)
    assert set(forward["controllers"]) == set(benchmark.CONTROLLERS)
    assert all(row["rowwise_semantic_equal"] for row in forward["controllers"].values())
    assert max(row["rowwise_maximum_absolute_difference"] for row in forward["controllers"].values()) <= 2e-6
    first = benchmark._training_kernel("FOUNDATION", 12, 2)
    second = benchmark._training_kernel("FOUNDATION", 12, 2)
    assert first["fixture_digest"] == second["fixture_digest"]
    assert first["adamw_steps"] == 2


def test_synthetic_atomic_io_has_exact_shapes_and_frontier(tmp_path) -> None:
    row = benchmark._io_measurement(tmp_path)
    assert row["foundation_artifact_shapes"] == 24
    assert row["adapter_artifact_shapes"] == 72
    assert row["total_artifact_shapes"] == 96
    assert row["projected_checkpoint_shaped_io"] == {
        "foundation": 24,
        "adapter": 72,
        "total": 96,
        "actual_scientific_checkpoints_created": 0,
    }
    assert row["atomic_publication"] is True
    assert row["exact_frontier_recovery"] is True
    assert row["interrupted_fragment_ignored"] is True
    assert row["durable_bytes"] > 0


def test_worker_speedup_is_measured_and_bounded_without_ideal_division() -> None:
    rows = benchmark._annotate_worker_scaling(
        [
            {"outer_workers": 1, "aggregate_work_units_per_second": 10.0},
            {"outer_workers": 2, "aggregate_work_units_per_second": 18.0},
            {"outer_workers": 4, "aggregate_work_units_per_second": 50.0},
        ]
    )
    assert rows[0]["effective_speedup_vs_one_worker"] == 1.0
    assert rows[1]["effective_speedup_vs_one_worker"] == 1.8
    assert rows[1]["parallel_efficiency"] == 0.9
    assert rows[2]["raw_speedup_vs_one_worker"] == 5.0
    assert rows[2]["effective_speedup_vs_one_worker"] == 4.0
    assert rows[2]["effective_speedup_bounded_by_worker_count"] is True

    retained = benchmark._select_acceptance_worker_speedup(rows[2])
    assert retained["current_effective_speedup"] == 4.0
    assert retained["retained_effective_speedup"] == pytest.approx(3.034772909220757)
    assert retained["acceptance_effective_speedup"] == pytest.approx(3.034772909220757)
    assert retained["acceptance_speedup_source"] == "retained_prior"
    current = benchmark._select_acceptance_worker_speedup(
        {"effective_speedup_vs_one_worker": 2.5}
    )
    assert current["acceptance_effective_speedup"] == 2.5
    assert current["acceptance_speedup_source"] == "current_measurement"


def test_prior_record_provenance_is_immutable_and_not_current_path_bytes() -> None:
    prior = benchmark.PRIOR_RETAINED_EFFICIENCY_EVIDENCE
    assert prior["historical_whole_file_sha256"] == "91d3a16009f68891b0402464783954e35ca03dea1aa7d85c85b3165135d0a2cf"
    assert prior["measured_effective_speedup"] == pytest.approx(3.034772909220757)
    assert prior["projected_cpu_core_hours"] == pytest.approx(2.0266105726403127)
    assert prior["projected_measured_wall_hours"] == pytest.approx(0.6677964491124604)
    assert prior["historical_path_bytes_still_present"] is False
    record = benchmark._attach_evidence_provenance({"schema": "TEST_ONLY", "efficiency_review": "COMPLETE"})
    provenance = record["evidence_provenance"]
    assert provenance["prior_retained_record"]["historical_whole_file_sha256"] == prior["historical_whole_file_sha256"]
    assert provenance["current_record"]["digest_kind"] == "canonical_current_evidence_payload_sha256"
    assert provenance["current_record"]["whole_file_sha256_is_external_after_atomic_write"] is True
    assert provenance["current_record"]["historical_whole_file_sha256_is_not_current_whole_file_sha256"] is True


def test_worker_semantic_proof_derives_every_claim_and_rejects_mismatch() -> None:
    frontier = []
    for ordinal in range(benchmark.SUSTAINED_TOTAL_WORK_UNITS):
        unit = {
            "unit": (
                "TEST_ONLY_FOUNDATION_SUSTAINED_UNIT"
                if ordinal % 2 == 0
                else "TEST_ONLY_FINAL_CONTROLLER_SUSTAINED_UNIT"
            ),
            "controller_path": "FOUNDATION" if ordinal % 2 == 0 else "FREE",
            "allocated_episodes": 120,
            "allocated_primitive_slots": 120 * 364,
            "policy_queries": 120,
            "forced_interventions": 0,
            "primitive_transitions": 120,
            "renewal_batches": 1,
            "endpoint_digest": f"{ordinal:064x}",
            "endpoint_inventory": {"lanes": 120, "terminal": 120},
        }
        frontier.append(benchmark._worker_ordinal_proof(ordinal, unit)["row"])
    digest = benchmark.hashlib.sha256(benchmark._canonical(frontier)).hexdigest()
    rows = [
        {
            "outer_workers": count,
            "exact_disjoint_partition_complete": True,
            "merged_ordinal_inventory": list(range(benchmark.SUSTAINED_TOTAL_WORK_UNITS)),
            "merged_ordered_frontier": copy.deepcopy(frontier),
            "merged_ordered_frontier_sha256": digest,
        }
        for count in (1, 2, 4)
    ]
    derived = benchmark._validate_worker_semantic_proofs(rows)
    assert derived["outer_worker_partitions_complete"] is True
    assert derived["all_merged_frontiers_equal"] is True
    assert derived["rng_address_order_preserved"] is True
    assert derived["controller_tensor_outputs_preserved"] is True
    assert derived["optimizer_state_arithmetic_preserved"] is True
    assert derived["endpoint_counts_preserved"] is True
    assert derived["stage_counts_preserved"] is True
    assert derived["opportunity_assay_absent"] is True

    tampered = copy.deepcopy(rows)
    tampered[2]["merged_ordered_frontier"][7]["optimizer_state_arithmetic"]["final_state_sha256"] = "f" * 64
    tampered[2]["merged_ordered_frontier_sha256"] = benchmark.hashlib.sha256(
        benchmark._canonical(tampered[2]["merged_ordered_frontier"])
    ).hexdigest()
    with pytest.raises(RuntimeError, match="merged frontier differs"):
        benchmark._validate_worker_semantic_proofs(tampered)


def test_real_native_test_only_opportunity_service_is_complete_and_blinded(tmp_path) -> None:
    row = benchmark._opportunity_service_measurement(tmp_path)
    assert row["real_native_batch_service"] is True
    assert row["pair_count"] == 32
    assert row["rollouts_per_pair"] == 144
    assert row["measured_replicate_rollouts"] == 4_608
    assert row["full_stage_rollouts"] == 110_592
    assert row["full_stage_allocated_slots"] == 40_255_488
    assert row["full_stage_registered_query_ceiling"] == 4_313_088
    assert row["address_inventory_complete"] is True
    assert row["common_tape_binding_equal"] is True
    assert row["masking_and_lane_positions_equal"] is True
    assert row["exact_tie_rule_exercised"] is True
    assert row["replicate_aggregate_completed"] is True
    assert row["replicate_count_analyzed"] == 24
    assert row["full_24_replicate_stage_publication"] is True
    assert row["publication_prerequisite_permit_bound"] is True
    assert row["complete_only_publication"] is True
    assert row["load_equal"] is row["resume_equal"] is True
    assert row["question_relevant_output"] is False
    assert row["analyzer_values_exposed"] is False
    assert row["scientific_values_retained_or_exposed"] is False
