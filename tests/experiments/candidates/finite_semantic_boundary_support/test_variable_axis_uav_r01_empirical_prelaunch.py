from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[4]
TEST_ROOT = (
    REPO
    / "temp/directions/finite_semantic_boundary_support/test/variable_axis_uav_r01/s3/g1/pytest-root"
)
TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["PYTEST_DEBUG_TEMPROOT"] = str(TEST_ROOT)
RESERVED_ROOT = REPO / "temp/directions/finite_semantic_boundary_support/exp/fsbs-r01-complete-20260827-01"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_canonical_empirical_contract_payload_checkpoints_and_git_prerequisites() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_contract import (
        canonical_parameters,
        canonical_resource_estimate,
        checkpoint_identities,
        empirical_boundary,
        git_prerequisites,
    )

    assert not RESERVED_ROOT.exists()
    boundary = empirical_boundary()
    assert boundary == {
        "schema": "FSBS_R01_S3_EMPIRICAL_BOUNDARY_V1",
        "run_id": "fsbs-r01-complete-20260827-01",
        "output_root": "temp/directions/finite_semantic_boundary_support/exp/fsbs-r01-complete-20260827-01/",
        "module": "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
        "payload_argv": [
            "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
            "-m",
            "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
        ],
        "destination_preconditions": {
            "mode": "CREATE_ONLY",
            "must_be_absent_or_empty": True,
            "symlink_or_reparse_forbidden": True,
            "existing_complete_terminal_forbids_rerun": True,
        },
        "empirical_activity_released": False,
        "operator_now": False,
        "effect_refs": [],
    }

    parameters = canonical_parameters()
    assert parameters["schema"] == "FSBS_R01_REGISTERED_PARAMETERS_V1"
    assert parameters["registered_seeds"] == [11, 23, 37, 53, 71, 89, 107, 127]
    assert parameters["arms"] == ["AUTHENTIC", "REASSOCIATED"]
    assert parameters["training"] == {
        "envelopes": [6, 8],
        "episodes_per_envelope_arm_seed": 64,
        "decisions_per_arm_seed": 1_984,
        "all_arm_seed_decisions": 31_744,
    }
    assert parameters["evaluation"] == {
        "envelopes": [6, 8, 10],
        "branches": ["NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"],
        "episodes_per_envelope_branch_arm_seed": 32,
        "decisions_per_branch_arm_seed": 1_728,
        "all_branch_arm_seed_decisions": 110_592,
    }
    assert parameters["retained_gate_transactions"] == 15_360
    assert parameters["registered_total_transactions"] == 157_696
    assert parameters["registered_cap_transactions"] == 160_000
    assert parameters["namespace"] == "FSBS-VN1-R01"
    assert parameters["tuning_or_retry"] is False
    assert parameters["values_materialized"] is False
    assert parameters["sha256"] == hashlib.sha256(
        _canonical({key: value for key, value in parameters.items() if key != "sha256"})
    ).hexdigest()

    checkpoints = checkpoint_identities()
    assert len(checkpoints) == 16
    assert {(row["arm"], row["seed"]) for row in checkpoints} == {
        (arm, seed)
        for arm in ("AUTHENTIC", "REASSOCIATED")
        for seed in (11, 23, 37, 53, 71, 89, 107, 127)
    }
    assert len({row["checkpoint_id"] for row in checkpoints}) == 16
    assert all(row["materialized"] is False for row in checkpoints)

    estimate = canonical_resource_estimate()
    assert estimate == {
        "schema": "FSBS_R01_COMPLETE_RESOURCE_ESTIMATE_V1",
        "transactions": 157_696,
        "workers": 1,
        "threads_per_worker": 1,
        "device": "CPU",
        "wall_seconds": 600,
        "cpu_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
        "basis": "ACCEPTED_S2_HIGH_RESULT_BLIND_PROJECTION",
        "scientific_execution_observed": False,
    }

    git = git_prerequisites("a5fb767b7be3ef4c5bc0e92cc22ed13fe77fe3c5")
    assert git["required_branch"] == (
        "omp/finite_semantic_boundary_support/engineering/"
        "bc2db89b-8d64-4f7e-abac-5f1b0a58b4c9"
    )
    assert git["observed_shared_checkout_head"] == "a5fb767b7be3ef4c5bc0e92cc22ed13fe77fe3c5"
    assert git["observed_shared_checkout_eligible"] is False
    assert git["candidate_head"] is None
    assert git["code_sha"] is None
    assert git["required_equality"] == "CANDIDATE_HEAD_EQUALS_IMMUTABLE_MANIFEST_CODE_SHA"
    assert git["release_ready"] is False
    assert not RESERVED_ROOT.exists()


def test_source_run_manifest_release_refusal_cold_resume_and_no_rerun(
    tmp_path: Path,
) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_manifest import (
        build_prelaunch_dossier,
        validate_release_manifest,
    )
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_validation import (
        assert_no_terminal_rerun,
        validate_cold_resume_fixture,
        validate_prelaunch_dossier,
    )

    assert not RESERVED_ROOT.exists()
    dossier = build_prelaunch_dossier(
        REPO, observed_shared_head="a5fb767b7be3ef4c5bc0e92cc22ed13fe77fe3c5"
    )
    validate_prelaunch_dossier(dossier, REPO)
    assert dossier["schema"] == "FSBS_R01_S3_PRELAUNCH_DOSSIER_V1"
    assert dossier["accepted_s0_ref"]["sha256"] == "778cbe7c8c90279b0787e6a651ca537cb72e94b0b786a453a2e62b297dd571de"
    assert dossier["accepted_s1_ref"]["sha256"] == "dec17c340970bb5aa3c46cf1a15cf40c814cda708ec9950f721a3f134df990b0"
    assert dossier["accepted_s2_ref"]["sha256"] == "dafa687110a6e9af331f3328b0eb4943536bdfc4af6c458d0c214d67266d7cfd"
    source_paths = {row["path"] for row in dossier["source_test_manifest"]["refs"]}
    assert {
        "experiments/candidates/finite_semantic_boundary_support/variable_axis_uav_r01/empirical_transaction.py",
        "experiments/candidates/finite_semantic_boundary_support/variable_axis_uav_r01/empirical_contract.py",
        "experiments/candidates/finite_semantic_boundary_support/variable_axis_uav_r01/empirical_manifest.py",
        "experiments/candidates/finite_semantic_boundary_support/variable_axis_uav_r01/empirical_validation.py",
        "tests/experiments/candidates/finite_semantic_boundary_support/test_variable_axis_uav_r01_s0.py",
        "tests/experiments/candidates/finite_semantic_boundary_support/test_variable_axis_uav_r01_s1_binding.py",
        "tests/experiments/candidates/finite_semantic_boundary_support/test_variable_axis_uav_r01_s2_learner.py",
        "tests/experiments/candidates/finite_semantic_boundary_support/test_variable_axis_uav_r01_empirical_prelaunch.py",
    } <= source_paths
    for ref in dossier["source_test_manifest"]["refs"]:
        assert ref["sha256"] == hashlib.sha256((REPO / ref["path"]).read_bytes()).hexdigest()
    assert dossier["run_manifest_template"]["code_sha"] is None
    assert dossier["run_manifest_template"]["candidate_head"] is None
    assert dossier["run_manifest_template"]["release_ready"] is False
    assert dossier["evidence_tree"]["terminal_status"] == "PRELAUNCH_TECHNICALLY_BOUND"
    assert all(node["status"] == "PASS" for node in dossier["evidence_tree"]["nodes"])

    candidate = "4" * 40
    released = {
        "schema_version": 1,
        "writer": "Operator-fsbs-r01-complete-20260827-01",
        "operator_identity": "Operator-fsbs-r01-complete-20260827-01",
        "run_id": "fsbs-r01-complete-20260827-01",
        "direction_id": "finite_semantic_boundary_support",
        "assignment_id": "fsbs-r01-complete-20260827-01",
        "status": "RUNNING",
        "command": dossier["boundary"]["payload_argv"],
        "parameters_sha256": dossier["parameters"]["sha256"],
        "code_sha": candidate,
    }
    assert validate_release_manifest(
        released,
        dossier,
        observed_branch=dossier["git_prerequisites"]["required_branch"],
        observed_candidate_head=candidate,
    )["released"] is True
    with pytest.raises(PermissionError, match="command"):
        validate_release_manifest(
            {**released, "command": [sys.executable, "-c", "pass"]},
            dossier,
            observed_branch=dossier["git_prerequisites"]["required_branch"],
            observed_candidate_head=candidate,
        )
    with pytest.raises(PermissionError, match="code_sha"):
        validate_release_manifest(
            {**released, "code_sha": "5" * 40},
            dossier,
            observed_branch=dossier["git_prerequisites"]["required_branch"],
            observed_candidate_head=candidate,
        )

    technical = validate_cold_resume_fixture(tmp_path)
    assert technical == {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "cold_resume_equal": True,
        "repeated_update": False,
        "cross_arm_or_seed_state": False,
        "registered_seed_or_arm_used": False,
        "effect_refs": [],
    }
    terminal_root = tmp_path / "terminal-root"
    terminal_root.mkdir()
    (terminal_root / "terminal.json").write_text(
        '{"status":"SUCCEEDED","complete":true}\n', encoding="utf-8"
    )
    with pytest.raises(PermissionError, match="rerun"):
        assert_no_terminal_rerun(terminal_root)

    refused = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
        ],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert refused.returncode != 0
    assert "not released" in refused.stderr
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
            "--seed",
            "11",
        ],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert forbidden.returncode != 0
    assert "unrecognized arguments" in forbidden.stderr
    assert not RESERVED_ROOT.exists()


def test_atomic_s3_prelaunch_acceptance_records_actual_technical_costs(
    tmp_path: Path,
) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_manifest import (
        write_prelaunch_acceptance,
    )

    output = tmp_path / "FSBS_R01_S3_EMPIRICAL_PRELAUNCH_ACCEPTANCE.json"
    write_prelaunch_acceptance(
        output,
        REPO,
        observed_shared_head="a5fb767b7be3ef4c5bc0e92cc22ed13fe77fe3c5",
        scratch_root=tmp_path / "technical-fixture",
    )
    acceptance = json.loads(output.read_text(encoding="utf-8"))
    assert acceptance["schema"] == "FSBS_R01_S3_EMPIRICAL_PRELAUNCH_ACCEPTANCE_V1"
    assert acceptance["terminal_status"] == "PRELAUNCH_TECHNICALLY_ACCEPTED"
    assert acceptance["canonical_parameters"]["registered_total_transactions"] == 157_696
    assert acceptance["canonical_resource_estimate"]["wall_seconds"] == 600
    assert acceptance["payload_argv"] == [
        "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
        "-m",
        "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
    ]
    assert acceptance["reserved_output_effect"] == {
        "kind": "LOCAL_RESULT_ROOT",
        "resource_id": (
            "temp/directions/finite_semantic_boundary_support/exp/"
            "fsbs-r01-complete-20260827-01/"
        ),
        "operation": "CREATE_ONLY",
        "reserved_not_created": True,
    }
    assert acceptance["technical_fixture_validation"]["cold_resume_equal"] is True
    measurements = acceptance["actual_technical_measurements"]
    assert measurements["cpu_ns"] > 0
    assert measurements["wall_ns"] > 0
    assert measurements["peak_memory_bytes"] > 0
    assert measurements["peak_memory_method"] == "tracemalloc-python-allocations"
    assert measurements["scratch_peak_bytes"] > 0
    assert measurements["storage_bytes"] == output.stat().st_size
    assert measurements["io"]["output_bytes"] == output.stat().st_size
    assert measurements["io"]["technical_checkpoint_bytes"] > 0
    assert measurements["io"]["atomic_acceptance_replace_count"] == 1
    assert acceptance["git_prerequisites"]["candidate_head"] is None
    assert acceptance["git_prerequisites"]["code_sha"] is None
    assert acceptance["git_prerequisites"]["release_ready"] is False
    assert acceptance["empirical_activity_released"] is False
    assert acceptance["operator_now"] is False
    assert acceptance["effect_refs"] == []
    assert all(
        ref["sha256"] == hashlib.sha256((REPO / ref["path"]).read_bytes()).hexdigest()
        for ref in acceptance["source_test_manifest"]["refs"]
    )
    assert acceptance["deterministic_core_sha256"] == hashlib.sha256(
        _canonical(
            {
                key: value
                for key, value in acceptance.items()
                if key not in {"actual_technical_measurements", "deterministic_core_sha256"}
            }
        )
    ).hexdigest()
    assert not list(tmp_path.glob("*.tmp"))
    assert not RESERVED_ROOT.exists()
