from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
MODULE = (
    "experiments.candidates.finite_semantic_boundary_support."
    "variable_axis_uav_r01.s1"
)


def _run_cli(tmp_path: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    output = tmp_path / "fsbs-r01-s1-technical-acceptance.json"
    completed = subprocess.run(
        [sys.executable, "-m", MODULE, "--output", str(output), *extra],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed, output


def _evidence(tmp_path: Path) -> dict[str, object]:
    completed, output = _run_cli(tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert output.is_file()
    assert not list(tmp_path.glob("*.tmp"))
    evidence = json.loads(output.read_text(encoding="utf-8"))
    if "technical_measurements" in evidence:
        assert evidence["technical_measurements"]["io"]["output_bytes"] == output.stat().st_size
    return evidence


def _address(seed: int, family: str, coordinates: list[object]) -> bytes:
    return "\0".join(
        ["FSBS-VN1-R01", str(seed), family, *(str(value) for value in coordinates), "0"]
    ).encode("utf-8")


def test_cli_binds_architecture_separation_workload_and_firewall(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)

    assert evidence["schema"] == "FSBS_R01_S1_LEARNER_FREE_TECHNICAL_BINDING_V1"
    assert evidence["mode"] == "TECHNICAL_SCHEMA_ONLY_NO_LEARNER_EXECUTION"
    assert evidence["namespace"] == "FSBS-VN1-R01"
    assert evidence["effect_refs"] == []
    assert evidence["firewall"] == {
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
    }

    architecture = evidence["architecture"]
    assert architecture["selector_head"] == {
        "shape": [2, 4],
        "feature_order": ["bias", "surface_bit_signed", "interface_i_signed", "interface_r_signed"],
        "legal_actions": ["OPEN_0", "OPEN_1"],
        "parameter_values": None,
    }
    assert architecture["controller_head"] == {
        "shape": [2, 4],
        "feature_order": ["bias", "payload_bit_signed", "interface_i_signed", "interface_r_signed"],
        "legal_actions": ["LANE_0", "LANE_1"],
        "parameter_values": None,
    }
    assert architecture["shared_across_lineages_and_envelopes"] is True
    assert architecture["forbidden_feature_fields"] == [
        "identity", "token", "lineage", "partner", "roster_position", "M", "N_t",
        "arm", "donor", "block", "hidden_slot", "unopened_payload", "pair_score",
        "future_return",
    ]

    slots = architecture["structural_terminal_slots"]
    assert len(slots) == 16
    assert {(row["arm"], row["seed"]) for row in slots} == {
        (arm, seed)
        for arm in ("AUTHENTIC", "REASSOCIATED")
        for seed in (11, 23, 37, 53, 71, 89, 107, 127)
    }
    assert all(
        row["initialization_contract"] == "ZERO_ONLY_NOT_MATERIALIZED"
        and row["parameter_values"] is None
        and row["checkpoint"] is None
        for row in slots
    )
    assert evidence["separation_contract"] == {
        "parameters_cross_arm_or_seed": False,
        "transitions_cross_arm_or_seed": False,
        "updates_cross_arm_or_seed": False,
        "checkpoints_cross_arm_or_seed": False,
        "optimizer_state_cross_arm_or_seed": False,
        "paired_exogenous_addresses_across_arms": True,
        "paired_exploration_addresses_across_arms": True,
    }

    workload = evidence["workload"]
    assert workload["training_per_arm_seed"] == 64 * (13 + 18) == 1_984
    assert workload["training_all_slots"] == 16 * 1_984 == 31_744
    assert workload["evaluation_per_branch_arm_seed"] == 32 * (13 + 18 + 23) == 1_728
    assert workload["evaluation_all_branches_slots"] == 4 * 16 * 1_728 == 110_592
    assert workload["retained_gate_transactions"] == 15_360
    assert workload["registered_total_transactions"] == 31_744 + 110_592 + 15_360 == 157_696
    assert workload["registered_cap_transactions"] == 160_000

    rejected, output = _run_cli(tmp_path, "--seed", "11")
    assert rejected.returncode != 0
    assert "unrecognized arguments" in rejected.stderr
    assert output.is_file()


def test_cli_binds_schedule_addresses_evaluation_and_complete_manifest(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)

    epsilon = evidence["epsilon_contract"]
    assert epsilon["completed_decision_domain"] == [0, 1_984]
    assert epsilon["all_window_decisions_use_pre_window_count"] is True
    expected_epsilon = {0: Fraction(2, 5), 992: Fraction(9, 40), 1_984: Fraction(1, 20)}
    for fixture in epsilon["fixtures"]:
        decision = fixture["completed_decisions"]
        observed = Fraction(fixture["epsilon"][0], fixture["epsilon"][1])
        independently_recomputed = Fraction(2, 5) - Fraction(7, 20) * Fraction(decision, 1_984)
        assert observed == independently_recomputed == expected_epsilon[decision]

    update = evidence["window_update_contract"]
    assert update["same_pre_window_parameter_generation"] is True
    assert update["all_actions_sampled_before_single_apply"] is True
    assert update["applications_per_window"] == 1
    assert update["reduction"] == "COMMUTATIVE_SUM_GROUPED_BY_ACTION"
    assert update["parameter_values"] is None
    assert update["numeric_signal_values"] is None
    assert update["selector"]["feature_order"] == evidence["architecture"]["selector_head"]["feature_order"]
    assert update["controller"]["feature_order"] == evidence["architecture"]["controller_head"]["feature_order"]
    for fixture in update["coefficient_fixtures"]:
        pair_count = fixture["P_t"]
        assert pair_count in (2, 3, 4, 5)
        assert Fraction(*fixture["coefficient"]) == Fraction(1, 80 * pair_count)

    addresses = evidence["address_contract"]
    assert addresses["families"] == [
        "world", "churn", "pairing", "carrier-donor", "interface", "presentation",
        "exploration", "tie-rank", "evaluation-mask",
    ]
    assert addresses["training_choice_coordinates_separate_by_head"] is True
    assert addresses["evaluation_tie_rank_scope"] == "SEED_HEAD_FEATURE_CONTEXT_FIXED"
    assert addresses["evaluation_tie_rank_uses_world_coordinate"] is False
    for proof in addresses["paired_arm_proofs"]:
        expected = hashlib.sha256(
            _address(proof["seed"], proof["family"], proof["coordinates"])
        ).hexdigest()
        assert proof["AUTHENTIC"] == proof["REASSOCIATED"] == expected

    branches = evidence["evaluation_contract"]["branches"]
    assert evidence["evaluation_contract"]["branch_order"] == [
        "NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"
    ]
    assert set(branches) == {"NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"}
    assert all(branch["updates_parameters"] is False for branch in branches.values())
    assert all(branch["resource_receipt"] == [1, 1] for branch in branches.values())
    assert branches["MASKED"]["selector_input"] == "INDEPENDENT_BALANCED_BIT_WITHIN_EXACT_STRATUM"
    assert branches["FORCE_RELEVANT"]["open_action"] == "FORCED_RELEVANT_ONE_RECORD"
    assert branches["FORCE_DECOY"]["open_action"] == "FORCED_DECOY_ONE_RECORD"

    measurements = evidence["measurement_schema"]
    assert measurements["index_fields"] == ["seed", "arm", "M", "N_t", "window", "evaluation_branch"]
    assert measurements["independent_unit"] == "SEED"
    assert measurements["paired_seed_count"] == 8
    assert measurements["values_materialized"] is False
    assert set(measurements["required_fields"]) == {
        "relevant_record_selection_rate", "pair_safe_rate", "pair_score_distribution",
        "common_team_return", "paired_selection_effect", "paired_return_effect",
        "natural_masked_effect", "forced_relevant_decoy_effect", "heldout_M10_effect",
        "selector_action_counts", "controller_action_counts", "action_entropy",
        "action_margins", "first_passage_75pct_selection", "update_counts",
        "polarity_strata", "membership_window_strata", "lineage_role_balance",
        "peer_change_rate", "active_masks", "survivor_rejoin_state_checks",
        "identity_path_anomalies", "declared_actual_resource_totals",
        "wall_memory_storage_totals", "mediator_residual_localization",
    }

    controls = evidence["control_invariants"]
    assert controls == [
        {"branch": "REASSOCIATED", "selection_rate": [1, 2], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "MASKED", "selection_rate": [1, 2], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "FORCE_RELEVANT", "selection_rate": [1, 1], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
        {"branch": "FORCE_DECOY", "selection_rate": [0, 1], "kind": "STRUCTURAL_INVALIDATION_ONLY"},
    ]

    first_true = evidence["first_true_contract"]
    assert first_true["predicate_values"] is None
    assert first_true["ordered_enum"] == [
        "INVALID_OR_INCONCLUSIVE",
        "OPTIMIZATION_GEOMETRY_FALSIFIER",
        "CARRIER_CREDIT_UNSUPPORTED",
        "SELECTION_TO_COORDINATION_UNSUPPORTED",
        "HELDOUT_ROSTER_TRANSFER_FAILED",
        "RESERVATION_INFORMATION_EDGE_ABSENT",
        "BOUNDED_NULL",
        "POSITIVE_EDGE",
        "INCONCLUSIVE_REMAINDER",
    ]

    manifest = evidence["result_manifest_contract"]
    assert manifest["schema_only"] is True
    assert manifest["values_materialized"] is False
    assert manifest["partial_commit_allowed"] is False
    assert manifest["atomic_final_replace_required"] is True
    assert manifest["required_counts"] == {
        "retained_gate_transactions": 15_360,
        "terminal_parameter_slots": 16,
        "evaluation_branches": 4,
        "arms": 2,
        "paired_seeds": 8,
        "evaluation_envelopes": 3,
    }
    assert set(manifest["required_sections"]) == {
        "authority_refs", "source_manifest", "retained_gate", "terminal_slots",
        "evaluation_branches", "measurements", "controls", "resource_totals",
        "anomalies", "first_true_outcome", "result_firewall",
    }
    assert evidence["evidence_tree"]["terminal_status"] == "TECHNICALLY_BOUND"
    assert all(node["status"] == "PASS" for node in evidence["evidence_tree"]["nodes"])


def test_cli_binds_current_bytes_atomic_metrics_and_safe_cost_projection(tmp_path: Path) -> None:
    first = _evidence(tmp_path)
    second = _evidence(tmp_path)

    for ref_name in ("authority_ref", "accepted_s0_ref"):
        ref = first[ref_name]
        path = REPO / ref["path"]
        assert ref["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert first["accepted_s0_ref"]["schema"] == "FSBS_R01_S0_HOST_SUPPORT_FIREWALL_V1"
    assert first["accepted_s0_ref"]["terminal_status"] == "TECHNICALLY_ACCEPTED"
    assert first["accepted_s0_ref"]["effect_refs"] == []
    for source_ref in first["accepted_s0_source_refs"] + first["source_manifest"]:
        path = REPO / source_ref["path"]
        assert source_ref["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    core = {
        key: value
        for key, value in first.items()
        if key not in {"technical_measurements", "deterministic_core_sha256"}
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert first["deterministic_core_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert second["deterministic_core_sha256"] == first["deterministic_core_sha256"]

    firewall = first["runtime_input_firewall"]
    assert firewall["accepted_cli_options"] == ["--output"]
    assert firewall["fail_closed"] is True
    assert set(firewall["forbidden_cli_options"]) == {
        "--seed", "--arm", "--reward", "--loss", "--gradient", "--optimizer",
        "--checkpoint", "--model", "--policy-output", "--result",
    }
    assert firewall["numeric_question_values_accepted"] is False

    actual = first["technical_measurements"]
    assert actual["scope"] == "S1-build-validate-canonicalize-before-atomic-replace"
    assert actual["cpu_ns"] > 0
    assert actual["wall_ns"] > 0
    assert actual["peak_memory_bytes"] > 0
    assert actual["peak_memory_method"] == "tracemalloc-python-allocations"
    assert actual["io"]["atomic_replace_count"] == 1
    assert actual["io"]["authority_bytes_read"] == (REPO / first["authority_ref"]["path"]).stat().st_size
    assert actual["io"]["accepted_s0_bytes_read"] == (REPO / first["accepted_s0_ref"]["path"]).stat().st_size
    assert actual["io"]["source_bytes_read"] == sum(
        (REPO / row["path"]).stat().st_size for row in first["source_manifest"]
    )

    projection = first["cost_capacity_projection"]
    assert projection["kind"] == "STATIC_RESULT_BLIND_PLANNING_NOT_MEASUREMENT"
    assert projection["construction_engineer_hours"] == {
        "low": 16,
        "central": 32,
        "high": 56,
    }
    complete = projection["complete_conditional_transaction"]
    assert complete["transactions"] == 157_696
    assert complete["device"] == "CPU"
    assert complete["workers"] == 1
    assert complete["hard_caps"] == {
        "wall_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "durable_result_bytes": 268_435_456,
    }
    expected_scenarios = {
        "low": (10_000, 16, 134_217_728, 67_108_864, 33_554_432),
        "central": (2_000, 79, 268_435_456, 134_217_728, 67_108_864),
        "high": (263, 600, 1_073_741_824, 536_870_912, 268_435_456),
    }
    for case, expected in expected_scenarios.items():
        scenario = complete["scenarios"][case]
        assert (
            scenario["assumed_transactions_per_second"],
            scenario["wall_seconds_ceiling"],
            scenario["peak_memory_bytes"],
            scenario["scratch_bytes"],
            scenario["durable_result_bytes"],
        ) == expected
        assert scenario["wall_seconds_ceiling"] == -(-157_696 // scenario["assumed_transactions_per_second"])
    shards = complete["safe_shard_plan"]
    assert shards == {
        "execution": "SEQUENTIAL_ONE_CPU_WORKER",
        "retained_gate_transactions": 15_360,
        "arm_seed_shards": 16,
        "transactions_per_arm_seed_shard": 1_984 + 4 * 1_728,
        "partial_shard_value_exposed": False,
        "final_commit": "ONLY_AFTER_ALL_SHARDS_AND_COMPLETE_MANIFEST_VALIDATE",
    }
    assert 15_360 + 16 * shards["transactions_per_arm_seed_shard"] == 157_696
    assert first["technical_acceptance"]["terminal_status"] == "TECHNICALLY_ACCEPTED"
    assert first["technical_acceptance"]["next_boundary"] == (
        "FSBS-R01-S2-CONDITIONAL-LEARNER-CONSTRUCTION-DECISION"
    )
