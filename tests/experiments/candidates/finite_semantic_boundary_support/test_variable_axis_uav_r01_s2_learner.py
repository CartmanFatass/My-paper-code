from __future__ import annotations

import os
import json
import hashlib
from fractions import Fraction
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[4]
TEST_ROOT = (
    REPO
    / "temp/directions/finite_semantic_boundary_support/test/variable_axis_uav_r01/s2/g1/pytest-root"
)
TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["PYTEST_DEBUG_TEMPROOT"] = str(TEST_ROOT)


def test_nonregistered_learner_exact_schema_schedule_and_grouped_update() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.learner import (
        REGISTERED_SEEDS,
        TechnicalDecision,
        TechnicalLinearLearner,
    )

    assert REGISTERED_SEEDS == {11, 23, 37, 53, 71, 89, 107, 127}
    first = TechnicalLinearLearner("TECHNICAL_A", 1_000_003)
    second = TechnicalLinearLearner("TECHNICAL_B", 1_000_003)
    expected_zero = {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "seed": 1_000_003,
        "selector": [[[0, 1]] * 4, [[0, 1]] * 4],
        "controller": [[[0, 1]] * 4, [[0, 1]] * 4],
        "completed_windows": [],
    }
    first_snapshot = first.snapshot()
    second_snapshot = second.snapshot()
    assert first_snapshot.pop("arm") == "TECHNICAL_A"
    assert second_snapshot.pop("arm") == "TECHNICAL_B"
    assert first_snapshot == second_snapshot == expected_zero
    assert first.selector_features({"surface_bit": 1, "i": 0, "r": 1}) == (
        Fraction(1), Fraction(1), Fraction(-1), Fraction(1)
    )
    assert first.controller_features({"payload_bit": 0, "i": 1, "r": 0}) == (
        Fraction(1), Fraction(-1), Fraction(1), Fraction(-1)
    )
    with pytest.raises(ValueError, match="exactly"):
        first.selector_features({"surface_bit": 1, "i": 0, "r": 1, "M": 6})
    with pytest.raises(PermissionError, match="registered"):
        TechnicalLinearLearner("TECHNICAL_A", 11)
    with pytest.raises(PermissionError, match="nonregistered"):
        TechnicalLinearLearner("AUTHENTIC", 1_000_003)

    assert first.action_names("selector") == ("OPEN_0", "OPEN_1")
    assert first.action_names("controller") == ("LANE_0", "LANE_1")
    assert [first.epsilon(value) for value in (0, 992, 1_984)] == [
        Fraction(2, 5), Fraction(9, 40), Fraction(1, 20)
    ]
    coordinates = ("NONREGISTERED_FIXTURE", 0, "selector")
    assert first.paired_address("exploration", coordinates) == second.paired_address(
        "exploration", coordinates
    )
    assert first.paired_address("tie-rank", coordinates) == second.paired_address(
        "tie-rank", coordinates
    )

    decisions = (
        TechnicalDecision(
            action=0,
            features=(Fraction(1), Fraction(1), Fraction(-1), Fraction(1)),
            pre_window_score=Fraction(0),
            canned_common_signal=Fraction(1, 2),
        ),
        TechnicalDecision(
            action=1,
            features=(Fraction(1), Fraction(-1), Fraction(1), Fraction(-1)),
            pre_window_score=Fraction(0),
            canned_common_signal=Fraction(-1, 2),
        ),
    )
    forward = TechnicalLinearLearner("TECHNICAL_A", 1_000_033)
    reverse = TechnicalLinearLearner("TECHNICAL_A", 1_000_033)
    forward_receipt = forward.apply_grouped_window_update(
        "selector", decisions, pair_count=2, window_id="TECH-W0"
    )
    reverse_receipt = reverse.apply_grouped_window_update(
        "selector", tuple(reversed(decisions)), pair_count=2, window_id="TECH-W0"
    )
    assert forward.snapshot() == reverse.snapshot()
    assert forward.selector_weights == (
        (Fraction(1, 320), Fraction(1, 320), Fraction(-1, 320), Fraction(1, 320)),
        (Fraction(-1, 320), Fraction(1, 320), Fraction(-1, 320), Fraction(1, 320)),
    )
    assert forward_receipt["coefficient"] == reverse_receipt["coefficient"] == [1, 160]
    assert forward_receipt["same_pre_window_generation"] is True
    assert forward_receipt["applications"] == 1
    with pytest.raises(ValueError, match="already applied"):
        forward.apply_grouped_window_update(
            "selector", decisions, pair_count=2, window_id="TECH-W0"
        )


def test_sequential_checkpoint_resume_branches_and_complete_only_result(
    tmp_path: Path,
) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        dispatch_technical_branches,
        fixed_technical_shards,
        run_sequential_shards,
    )
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.result import (
        build_complete_technical_result,
        write_complete_technical_result,
    )

    shards = fixed_technical_shards()
    assert [(row.arm, row.seed) for row in shards] == [
        ("TECHNICAL_A", 1_000_003),
        ("TECHNICAL_B", 1_000_033),
    ]
    assert all(row.fixture_kind == "NONREGISTERED_TECHNICAL_ONLY" for row in shards)

    uninterrupted_checkpoint = tmp_path / "uninterrupted-checkpoint.json"
    uninterrupted = run_sequential_shards(
        shards, checkpoint_path=uninterrupted_checkpoint
    )
    resume_checkpoint = tmp_path / "resume-checkpoint.json"
    paused = run_sequential_shards(
        shards, checkpoint_path=resume_checkpoint, stop_after_windows=1
    )
    assert paused["terminal_status"] == "TECHNICAL_PAUSED"
    resumed = run_sequential_shards(
        shards, checkpoint_path=resume_checkpoint, resume=True
    )
    assert uninterrupted["terminal_status"] == resumed["terminal_status"] == "TECHNICAL_COMPLETE"
    assert uninterrupted["fixture_state_digests"] == resumed["fixture_state_digests"]
    assert uninterrupted["update_ledger"] == resumed["update_ledger"]
    assert len(uninterrupted["update_ledger"]) == len(set(uninterrupted["update_ledger"])) == 8
    assert set(uninterrupted["fixture_state_digests"]) == {row.shard_id for row in shards}
    assert len(set(uninterrupted["fixture_state_digests"].values())) == 2
    assert uninterrupted["workers"] == 1
    assert uninterrupted["execution"] == "SEQUENTIAL"
    assert uninterrupted["registered_seed_or_arm_used"] is False
    assert uninterrupted["cross_arm_or_seed_state"] is False
    assert not list(tmp_path.glob("*.tmp"))

    checkpoint = json.loads(resume_checkpoint.read_text(encoding="utf-8"))
    assert checkpoint["schema"] == "FSBS_R01_S2_TECHNICAL_CHECKPOINT_V1"
    assert checkpoint["fixture_kind"] == "NONREGISTERED_TECHNICAL_ONLY"
    assert checkpoint["registered_manifest"] is False
    assert checkpoint["effect_refs"] == []
    assert checkpoint["cursor"] == {"shard_index": 2, "window_index": 0}

    branches = dispatch_technical_branches(resumed)
    assert len(branches) == 8
    assert {
        row["branch"] for row in branches
    } == {"NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"}
    assert all(row["fixture_kind"] == "NONREGISTERED_TECHNICAL_ONLY" for row in branches)
    assert all(row["resource_receipt"] == [1, 1] for row in branches)
    assert all(row["updates_parameters"] is False for row in branches)
    assert all(row["question_relevant_values"] is None for row in branches)

    with pytest.raises(ValueError, match="complete"):
        build_complete_technical_result(paused, branches[:4])
    package = build_complete_technical_result(resumed, branches)
    assert package["schema"] == "FSBS_R01_S2_COMPLETE_TECHNICAL_RESULT_V1"
    assert package["fixture_kind"] == "NONREGISTERED_TECHNICAL_ONLY"
    assert package["complete"] is True
    assert package["registered_manifest"] is False
    assert package["scientific_first_true_outcome"] is None
    assert package["question_relevant_values"] is None
    assert package["effect_refs"] == []
    result_path = tmp_path / "complete-technical-result.json"
    write_complete_technical_result(result_path, package)
    assert json.loads(result_path.read_text(encoding="utf-8")) == package
    assert not list(tmp_path.glob("*.tmp"))


def test_atomic_s2_acceptance_current_bytes_resources_projection_and_firewall(
    tmp_path: Path,
) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.s2 import (
        write_acceptance,
    )

    output = tmp_path / "FSBS_R01_S2_TECHNICAL_ACCEPTANCE.json"
    write_acceptance(output)
    first = json.loads(output.read_text(encoding="utf-8"))
    write_acceptance(output)
    second = json.loads(output.read_text(encoding="utf-8"))

    assert first["schema"] == "FSBS_R01_S2_TECHNICAL_ACCEPTANCE_V1"
    assert first["fixture_kind"] == "NONREGISTERED_TECHNICAL_ONLY"
    assert first["terminal_status"] == "TECHNICALLY_ACCEPTED"
    assert first["effect_refs"] == []
    assert first["deterministic_core_sha256"] == second["deterministic_core_sha256"]
    core = {
        key: value
        for key, value in first.items()
        if key not in {"technical_measurements", "deterministic_core_sha256"}
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert first["deterministic_core_sha256"] == hashlib.sha256(canonical).hexdigest()

    for ref_name in ("authority_ref", "accepted_s0_ref", "accepted_s1_ref"):
        ref = first[ref_name]
        path = REPO / ref["path"]
        assert ref["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    for source_ref in first["source_manifest"]:
        path = REPO / source_ref["path"]
        assert source_ref["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    fixture = first["technical_fixture_acceptance"]
    assert fixture == {
        "shards": 2,
        "windows": 4,
        "grouped_updates": 8,
        "branch_dispatches": 8,
        "workers": 1,
        "registered_seed_or_arm_used": False,
        "cross_arm_or_seed_state": False,
        "repeated_update": False,
        "question_relevant_values": None,
        "complete_only_result": True,
    }
    checkpoint_path = output.with_name("FSBS_R01_S2_TECHNICAL_CHECKPOINT.json")
    result_path = output.with_name("FSBS_R01_S2_COMPLETE_TECHNICAL_RESULT.json")
    assert checkpoint_path.is_file() and result_path.is_file()
    assert first["technical_artifact_refs"] == [
        {
            "path": checkpoint_path.name,
            "sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        },
        {
            "path": result_path.name,
            "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        },
    ]

    firewall = first["firewall"]
    assert firewall == {
        "registered_seed_execution": False,
        "registered_arm_execution": False,
        "complete_scientific_transaction": False,
        "scientific_training_or_evaluation": False,
        "effect_or_estimand_values": False,
        "interval_values": False,
        "scientific_first_true_outcome": False,
        "partial_package_access": False,
        "question_relevant_output": False,
        "result_query_enabled": False,
        "experiment_operator_requested": False,
        "provider_or_external_effect": False,
    }
    assert first["runtime_input_firewall"] == {
        "accepted_cli_options": ["--output"],
        "forbidden_cli_options": [
            "--seed", "--arm", "--partial", "--result", "--query", "--registered"
        ],
        "fail_closed": True,
    }

    measurements = first["technical_measurements"]
    assert measurements["scope"] == "S2-fixed-nonregistered-build-validate-atomic-write"
    assert measurements["cpu_ns"] > 0
    assert measurements["wall_ns"] > 0
    assert measurements["peak_memory_bytes"] > 0
    assert measurements["peak_memory_method"] == "tracemalloc-python-allocations"
    assert measurements["scratch_peak_bytes"] == checkpoint_path.stat().st_size + result_path.stat().st_size
    assert measurements["storage_bytes"] == (
        output.stat().st_size + checkpoint_path.stat().st_size + result_path.stat().st_size
    )
    assert measurements["io"]["output_bytes"] == output.stat().st_size
    assert measurements["io"]["atomic_replace_count"] == 6

    projection = first["complete_transaction_projection"]
    assert projection["kind"] == "FRESH_RESULT_BLIND_PROJECTION_NOT_EXECUTION"
    assert projection["transactions"] == 157_696
    assert projection["device"] == "CPU"
    assert projection["workers"] == 1
    assert projection["sequential_arm_seed_shards"] == 16
    assert projection["transactions_per_shard"] == 8_896
    assert projection["wall_seconds"] == {"low": 16, "central": 79, "high": 600}
    assert projection["hard_caps"] == {
        "cpu_seconds": 1_200,
        "wall_seconds": 2_400,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
    }
    assert first["next_boundary"] == "FSBS-R01-S3-COMPLETE-SCIENTIFIC-ACTIVITY-DECISION"
    assert not list(tmp_path.glob("*.tmp"))
