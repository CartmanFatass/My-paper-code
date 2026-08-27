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
RESERVED_ROOT = REPO / "temp/directions/finite_semantic_boundary_support/exp/fsbs-r01-complete-20260827-02"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_candidate_local_release_contract_v2_is_self_contained() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_manifest import (
        build_runtime_contract,
        validate_candidate_source_binding,
        validate_operator_runtime_files,
        validate_release_manifest,
    )

    candidate = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert len(candidate) == 40
    branch = subprocess.run(
        ["git", "-C", str(REPO), "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert branch == (
        "omp/finite_semantic_boundary_support/engineering/a394938d-runtime-v2"
    )
    contract = build_runtime_contract(REPO, candidate_branch=branch)
    assert contract["schema"] == "FSBS_R01_CANDIDATE_RUNTIME_CONTRACT_V2"
    assert contract["run_id"] == "fsbs-r01-complete-20260827-02"
    assert contract["authority_refs"][0] == {
        "path": "docs/research/candidates/finite_semantic_boundary_support/FSBS_VARIABLE_AXIS_COOPERATIVE_UAV_SCIENCE_AUTHORITY_R01_20260827.md",
        "sha256": "9e302f2ff32316c7e992a531fe49b112f4dc07397209055b320d4e4d98ed42fb",
    }
    assert len(contract["authority_refs"]) == 4
    assert "accepted_s0_ref" not in contract
    assert contract["effect"] == {
        "kind": "LOCAL_RESULT_ROOT",
        "resource_id": (
            "temp/directions/finite_semantic_boundary_support/exp/"
            "fsbs-r01-complete-20260827-02/"
        ),
        "operation": "CREATE_ONLY",
    }
    assert contract["parameters"]["registered_total_transactions"] == 157_696
    assert contract["resource_estimate"]["workers"] == 1
    assert contract["resource_estimate"]["threads_per_worker"] == 1
    assert all(
        ref["sha256"] == hashlib.sha256((REPO / ref["path"]).read_bytes()).hexdigest()
        for ref in contract["source_test_manifest"]["refs"]
    )
    blob_hashes = {
        ref["path"]: ref["sha256"] for ref in contract["source_test_manifest"]["refs"]
    }
    assert validate_candidate_source_binding(contract, blob_hashes) == {
        "source_test_bytes_equal_candidate": True,
        "ref_count": len(blob_hashes),
    }
    changed_path = next(iter(blob_hashes))
    with pytest.raises(PermissionError, match="candidate blob"):
        validate_candidate_source_binding(
            contract, {**blob_hashes, changed_path: "0" * 64}
        )

    command = contract["payload_argv"]
    command_sha = hashlib.sha256(b"\0".join(os.fsencode(part) for part in command)).hexdigest()
    claim_sha = hashlib.sha256(
        _canonical(
            {
                "code_sha": candidate,
                "command_sha256": command_sha,
                "direction_id": "finite_semantic_boundary_support",
            }
        )
    ).hexdigest()
    parameters = contract["parameters"]
    manifest = {
        "schema_version": 1,
        "revision": 2,
        "writer": "Operator-fsbs-r01-complete-20260827-02",
        "operator_identity": "Operator-fsbs-r01-complete-20260827-02",
        "run_id": "fsbs-r01-complete-20260827-02",
        "direction_id": "finite_semantic_boundary_support",
        "assignment_id": "fsbs-r01-complete-20260827-02",
        "status": "RUNNING",
        "command": command,
        "command_sha256": command_sha,
        "claim_sha256": claim_sha,
        "cwd": str(REPO.resolve()),
        "parameters": parameters,
        "parameters_sha256": hashlib.sha256(_canonical(parameters)).hexdigest(),
        "code_sha": candidate,
        "estimate": {
            "wall_seconds": 600.0,
            "basis": "ACCEPTED_S2_HIGH_RESULT_BLIND_PROJECTION",
            "peak_memory_gib": 1.0,
        },
        "environment": {
            "python": "3.10.0",
            "platform": "windows",
            "hostname": "result-blind-host",
            "captured_variables": {},
        },
        "outputs": {
            "stdout": "stdout.log",
            "stderr": "stderr.log",
            "checkpoints": "checkpoints",
            "metrics": "metrics",
            "artifacts": "artifacts",
        },
        "process": {
            "execution_token": "result-blind-token",
            "pid": os.getpid(),
            "process_group_id": 101,
            "linux_boot_id": "result-blind-boot",
            "proc_start_ticks": 202,
            "identity_persisted_at": "2026-08-27T00:00:01Z",
            "group_quiescent": None,
            "started_at": "2026-08-27T00:00:00Z",
            "ended_at": None,
            "exit_code": None,
            "terminal_reason": None,
        },
        "resources": {
            "preflight_ref": "preflight.json",
            "preflight_sha256": "1" * 64,
            "runner_spec_sha256": "2" * 64,
            "workers": 1,
            "threads_per_worker": 1,
            "memory_safe": True,
        },
        "observed_metrics": {},
        "created_at": "2026-08-27T00:00:00Z",
        "updated_at": "2026-08-27T00:00:01Z",
    }
    runtime_file_evidence = {
        "operator_runtime_files_valid": True,
        "preflight_sha256": manifest["resources"]["preflight_sha256"],
        "runner_spec_sha256": manifest["resources"]["runner_spec_sha256"],
    }
    manifest_path = RESERVED_ROOT / "manifest.json"
    released = validate_release_manifest(
        manifest,
        contract,
        manifest_path=manifest_path,
        observed_cwd=REPO.resolve(),
        observed_branch=branch,
        observed_candidate_head=candidate,
        observed_payload_pid=os.getpid(),
        operator_runtime_files=runtime_file_evidence,
    )
    assert released == {
        "released": True,
        "run_id": "fsbs-r01-complete-20260827-02",
        "code_sha": candidate,
        "authority_refs": contract["authority_refs"],
        "source_test_manifest": contract["source_test_manifest"],
    }
    with pytest.raises(PermissionError, match="process RUNNING identity"):
        validate_release_manifest(
            {**manifest, "process": {**manifest["process"], "pid": os.getpid() - 1}},
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    with pytest.raises(PermissionError, match="runtime file provenance"):
        validate_release_manifest(
            manifest,
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
        )
    operator_root = TEST_ROOT / "operator-runtime-files"
    operator_root.mkdir(parents=True, exist_ok=True)
    preflight_path = operator_root / "preflight.json"
    runner_path = operator_root / "runner-spec.json"
    preflight_path.write_text('{"memory_safe":true}\n', encoding="utf-8")
    preflight_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
    runner = {
        "schema_version": 1,
        "command": command,
        "command_sha256": command_sha,
        "cwd": str(REPO.resolve()),
        "git_branch": branch,
        "output_root": str(operator_root.resolve()),
        "outputs": manifest["outputs"],
        "preflight_sha256": preflight_sha,
    }
    runner_path.write_text(json.dumps(runner), encoding="utf-8")
    runtime_manifest = {
        **manifest,
        "resources": {
            **manifest["resources"],
            "preflight_sha256": preflight_sha,
            "runner_spec_sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
        },
    }
    assert validate_operator_runtime_files(
        runtime_manifest,
        operator_root / "manifest.json",
        observed_branch=branch,
    )["operator_runtime_files_valid"] is True
    runner_path.write_text('{"schema_version":1}', encoding="utf-8")
    with pytest.raises(PermissionError, match="runner hash"):
        validate_operator_runtime_files(
            runtime_manifest,
            operator_root / "manifest.json",
            observed_branch=branch,
        )
    with pytest.raises(PermissionError, match="command"):
        validate_release_manifest(
            {**manifest, "command": [sys.executable, "-c", "pass"]},
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    with pytest.raises(PermissionError, match="legacy terminal"):
        validate_release_manifest(
            {**manifest, "run_id": "fsbs-r01-complete-20260827-01"},
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    with pytest.raises(PermissionError, match="estimate"):
        validate_release_manifest(
            {**manifest, "estimate": {**manifest["estimate"], "wall_seconds": 601.0}},
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    for missing_field in ("process", "environment", "outputs", "resources"):
        incomplete = {key: value for key, value in manifest.items() if key != missing_field}
        with pytest.raises(PermissionError, match=missing_field):
            validate_release_manifest(
                incomplete,
                contract,
                manifest_path=manifest_path,
                observed_cwd=REPO.resolve(),
                observed_branch=branch,
                observed_candidate_head=candidate,
                observed_payload_pid=os.getpid(),
                operator_runtime_files=runtime_file_evidence,
            )
    tampered_effect_parameters = {
        **parameters,
        "effect_refs": [
            {
                **parameters["effect_refs"][0],
                "resource_id": "temp/directions/finite_semantic_boundary_support/exp/wrong/",
            }
        ],
    }
    tampered_effect_parameters["sha256"] = hashlib.sha256(
        _canonical(
            {
                key: value
                for key, value in tampered_effect_parameters.items()
                if key != "sha256"
            }
        )
    ).hexdigest()
    with pytest.raises(PermissionError, match="Effect"):
        validate_release_manifest(
            {
                **manifest,
                "parameters": tampered_effect_parameters,
                "parameters_sha256": hashlib.sha256(
                    _canonical(tampered_effect_parameters)
                ).hexdigest(),
            },
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    tampered_cap_parameters = {
        **parameters,
        "resource_caps": {**parameters["resource_caps"], "scratch_bytes": 1},
    }
    tampered_cap_parameters["sha256"] = hashlib.sha256(
        _canonical(
            {
                key: value
                for key, value in tampered_cap_parameters.items()
                if key != "sha256"
            }
        )
    ).hexdigest()
    with pytest.raises(PermissionError, match="caps"):
        validate_release_manifest(
            {
                **manifest,
                "parameters": tampered_cap_parameters,
                "parameters_sha256": hashlib.sha256(
                    _canonical(tampered_cap_parameters)
                ).hexdigest(),
            },
            contract,
            manifest_path=manifest_path,
            observed_cwd=REPO.resolve(),
            observed_branch=branch,
            observed_candidate_head=candidate,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=runtime_file_evidence,
        )
    assert not RESERVED_ROOT.exists()


def test_result_blind_production_learner_mirror_preserves_update_and_isolation() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.learner import (
        ProductionDecision,
        RegisteredLinearLearner,
        ResultBlindLinearMirror,
    )

    with pytest.raises(PermissionError, match="validated release"):
        RegisteredLinearLearner("AUTHENTIC", 11, release=None)

    mirror = ResultBlindLinearMirror("MIRROR_A", 1_000_003)
    selector = (
        ProductionDecision(0, (1.0, -1.0, -1.0, 1.0), 0.0),
        ProductionDecision(1, (1.0, 1.0, 1.0, -1.0), 0.0),
    )
    controller = (
        ProductionDecision(0, (1.0, 1.0, -1.0, -1.0), 0.0),
        ProductionDecision(1, (1.0, -1.0, 1.0, 1.0), 0.0),
    )
    receipt = mirror.apply_window(
        selector,
        controller,
        pair_count=2,
        window_id="MIRROR-W0",
        common_team_return=0.5,
    )
    assert receipt == {
        "window_id": "MIRROR-W0",
        "coefficient": 0.00625,
        "same_pre_window_generation": True,
        "applications": 1,
        "completed_decisions": 2,
    }
    assert mirror.selector_weights == (
        (0.003125, -0.003125, -0.003125, 0.003125),
        (0.003125, 0.003125, 0.003125, -0.003125),
    )
    snapshot = mirror.snapshot()
    restored = ResultBlindLinearMirror.from_snapshot(snapshot)
    assert restored.snapshot_digest() == mirror.snapshot_digest()
    with pytest.raises(ValueError, match="already applied"):
        restored.apply_window(
            selector,
            controller,
            pair_count=2,
            window_id="MIRROR-W0",
            common_team_return=0.5,
        )
    assert not RESERVED_ROOT.exists()


def test_result_blind_content_addressed_checkpoint_cold_resume(tmp_path: Path) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.checkpoint import (
        load_result_blind_checkpoint,
        write_result_blind_checkpoint,
    )
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.learner import (
        ProductionDecision,
        ResultBlindLinearMirror,
    )

    mirror = ResultBlindLinearMirror("MIRROR_A", 1_000_003)
    rows = (
        ProductionDecision(0, (1.0, -1.0, 1.0, -1.0), 0.0),
        ProductionDecision(1, (1.0, 1.0, -1.0, 1.0), 0.0),
    )
    mirror.apply_window(
        rows,
        rows,
        pair_count=2,
        window_id="MIRROR-W0",
        common_team_return=-0.5,
    )
    checkpoint_root = TEST_ROOT / "checkpoint-slice"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    path = checkpoint_root / "mirror.json"
    ref = write_result_blind_checkpoint(path, mirror, cursor={"window": 1})
    assert ref["content_addressed"] is True
    assert ref["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    restored, cursor = load_result_blind_checkpoint(path)
    assert cursor == {"window": 1}
    assert restored.snapshot_digest() == mirror.snapshot_digest()
    with pytest.raises(ValueError, match="already applied"):
        restored.apply_window(
            rows,
            rows,
            pair_count=2,
            window_id="MIRROR-W0",
            common_team_return=-0.5,
        )
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["cursor"] = {"window": 0}
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="content digest"):
        load_result_blind_checkpoint(path)
    assert not RESERVED_ROOT.exists()


def test_registered_transaction_plan_is_complete_and_result_blind() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        registered_transaction_plan,
    )

    plan = registered_transaction_plan()
    assert plan["schema"] == "FSBS_R01_REGISTERED_TRANSACTION_PLAN_V2"
    assert plan["fixture_kind"] == "RESULT_BLIND_PLAN_ONLY"
    assert plan["workers"] == 1
    assert plan["threads_per_worker"] == 1
    assert plan["gate_transactions"] == 15_360
    assert len(plan["shards"]) == 16
    assert {(row["arm"], row["seed"]) for row in plan["shards"]} == {
        (arm, seed)
        for arm in ("AUTHENTIC", "REASSOCIATED")
        for seed in (11, 23, 37, 53, 71, 89, 107, 127)
    }
    assert all(row["training_decisions"] == 1_984 for row in plan["shards"])
    assert all(row["evaluation_decisions"] == 6_912 for row in plan["shards"])
    assert plan["training_decisions"] == 31_744
    assert plan["evaluation_decisions"] == 110_592
    assert plan["registered_total_transactions"] == 157_696
    assert plan["checkpoint_count"] == 16
    assert plan["question_relevant_values"] is None
    assert plan["effect_refs"] == []
    assert not RESERVED_ROOT.exists()


def test_nonregistered_paired_progress_and_terminal_checkpoint_mirror() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        result_blind_orchestration_mirror,
    )

    mirror = result_blind_orchestration_mirror()
    assert mirror["paired_progress"] == {
        "paused_cursor": {"AUTHENTIC": 3, "REASSOCIATED": 3},
        "resumed_cursor": {"AUTHENTIC": 10, "REASSOCIATED": 10},
        "cold_resume_equal": True,
    }
    assert mirror["checkpoint_count"] == 16
    assert len(mirror["terminal_identities"]) == 16
    assert len({row["content_sha256"] for row in mirror["terminal_identities"]}) == 16
    assert all(
        row["content_addressed"] is True and row["terminal"] is True
        for row in mirror["terminal_identities"]
    )
    assert mirror["repeated_update"] is False
    assert mirror["cross_arm_or_seed_state"] is False
    assert mirror["question_relevant_values"] is None
    assert mirror["effect_refs"] == []


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"valid": False}, "INVALID_OR_INCONCLUSIVE"),
        ({"polarity_geometry_pass": False}, "OPTIMIZATION_GEOMETRY_FALSIFIER"),
        (
            {"primary_selection_all_positive": False, "positive_thresholds_pass": False},
            "CARRIER_CREDIT_UNSUPPORTED",
        ),
        (
            {"primary_return_all_positive": False, "positive_thresholds_pass": False},
            "SELECTION_TO_COORDINATION_UNSUPPORTED",
        ),
        (
            {"heldout_both_positive": False, "positive_thresholds_pass": False},
            "HELDOUT_ROSTER_TRANSFER_FAILED",
        ),
        ({"forced_contrast_pass": False, "positive_thresholds_pass": False}, "RESERVATION_INFORMATION_EDGE_ABSENT"),
        ({"bounded_null": True, "positive_thresholds_pass": False}, "BOUNDED_NULL"),
        ({}, "POSITIVE_EDGE"),
        ({"positive_thresholds_pass": False}, "INCONCLUSIVE_REMAINDER"),
    ],
)
def test_first_true_interpretation_worked_fixtures(
    changes: dict[str, bool], expected: str
) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        interpret_first_true,
    )

    passing = {
        "valid": True,
        "controller_competent": True,
        "primary_selection_all_positive": True,
        "primary_return_all_positive": True,
        "in_support_both_positive": True,
        "heldout_both_positive": True,
        "forced_contrast_pass": True,
        "bounded_null": False,
        "positive_thresholds_pass": True,
        "natural_masked_pass": True,
        "polarity_geometry_pass": True,
        "membership_geometry_pass": True,
    }
    assert interpret_first_true({**passing, **changes}) == expected


def test_small_positive_effects_are_inside_bounded_null_interval() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        within_bounded_null,
    )

    assert within_bounded_null([(0.01, 0.02), (0.03, 0.04), (0.05, 0.01)]) is True
    assert within_bounded_null([(0.051, 0.02), (0.03, 0.04), (0.05, 0.01)]) is False


def test_result_blind_world_mirror_preserves_authentic_and_reassociated_laws() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        result_blind_world_mirror,
    )

    mirror = result_blind_world_mirror()
    assert mirror["fixture_kind"] == "NONREGISTERED_RESULT_BLIND_MIRROR"
    assert mirror["question_relevant_values"] is None
    assert mirror["effect_refs"] == []
    authentic = mirror["modes"]["MIRROR_AUTHENTIC"]
    reassociated = mirror["modes"]["MIRROR_REASSOCIATED"]
    expected_cells = {
        (slot, relevant, decoy)
        for slot in (0, 1)
        for relevant in (0, 1)
        for decoy in (0, 1)
    }
    assert {
        (row["relevant_slot"], row["relevant_reservation"], row["decoy_reservation"])
        for row in authentic
    } == expected_cells
    assert all(row["semantic_bit"] == row["relevant_slot"] for row in authentic)
    for block_start in (0, 4):
        assert {
            (row["relevant_slot"], row["semantic_bit"])
            for row in reassociated[block_start : block_start + 4]
        } == {(0, 0), (0, 1), (1, 0), (1, 1)}
    for batch in mirror["paired_window_batches"].values():
        for window_rows in batch:
            for index, row in enumerate(window_rows):
                assert row["decoy_reservation"] == window_rows[
                    (index + 1) % len(window_rows)
                ]["relevant_reservation"]
            for carrier_block in (0, 1):
                matching = [
                    row
                    for row in window_rows
                    if row["relevant_reservation"] == carrier_block
                ]
                assert len({row["donor_permutation_index"] for row in matching}) <= 1
                assert len({row["donor_address_sha256"] for row in matching}) <= 1
        for pair_index in range(len(batch[0])):
            assert {
                (
                    window_rows[pair_index]["relevant_slot"],
                    window_rows[pair_index]["relevant_reservation"],
                    window_rows[pair_index]["decoy_reservation"],
                )
                for window_rows in batch
            } == expected_cells
            masked_pairs = [
                (
                    window_rows[pair_index]["relevant_slot"],
                    window_rows[pair_index]["evaluation_mask_bit"],
                )
                for window_rows in batch
            ]
            assert {pair: masked_pairs.count(pair) for pair in set(masked_pairs)} == {
                (0, 0): 2,
                (0, 1): 2,
                (1, 0): 2,
                (1, 1): 2,
            }
            assert all(
                window_rows[pair_index]["evaluation_mask_family"]
                == "evaluation-mask"
                and
                len(window_rows[pair_index]["evaluation_mask_address_sha256"]) == 64
                for window_rows in batch
            )
    assert not RESERVED_ROOT.exists()


def test_activity_marker_requires_complete_paired_window_after_failure_injection() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        commit_paired_activity_marker,
    )

    root = TEST_ROOT / "activity-boundary-mirror"
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "activity.json"
    marker.unlink(missing_ok=True)
    release = {
        "released": False,
        "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
        "run_id": "mirror-run",
        "code_sha": "0" * 40,
    }
    authentic = {
        "arm": "AUTHENTIC",
        "window_id": "MIRROR-W0",
        "complete": True,
        "common_team_return_observed": True,
        "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
    }
    reassociated = {**authentic, "arm": "REASSOCIATED"}
    with pytest.raises(ValueError, match="paired window"):
        commit_paired_activity_marker(root, [authentic], release=release)
    assert not marker.exists()
    value = commit_paired_activity_marker(
        root, [authentic, reassociated], release=release
    )
    assert value["schema"] == "FSBS_R01_ACTIVITY_BOUNDARY_MIRROR_V2"
    assert value["paired_arms"] == ["AUTHENTIC", "REASSOCIATED"]
    assert value["question_relevant_values"] is None
    assert marker.is_file()
    assert not RESERVED_ROOT.exists()


def test_result_blind_host_activity_log_is_observed_not_hardcoded() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        result_blind_host_observability_mirror,
        validate_host_activity_log_mirror,
    )

    rows = result_blind_host_observability_mirror()
    proof = validate_host_activity_log_mirror(rows)
    assert proof["complete"] is True
    assert proof["row_count"] == 104
    assert all(proof["predicates"].values())
    tampered = [dict(row) for row in rows]
    tampered[0]["registry_serial_match"] = False
    with pytest.raises(ValueError, match="activity log"):
        validate_host_activity_log_mirror(tampered)
    assert not RESERVED_ROOT.exists()


def test_result_blind_complete_only_publication_mirror(tmp_path: Path) -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.engine import (
        registered_transaction_plan,
    )
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.result import (
        build_result_blind_complete_mirror,
        write_result_blind_complete_mirror,
    )

    value = build_result_blind_complete_mirror(registered_transaction_plan())
    assert value["schema"] == "FSBS_R01_REGISTERED_COMPLETE_RESULT_V2_MIRROR"
    assert value["fixture_kind"] == "NONREGISTERED_RESULT_BLIND_MIRROR"
    assert value["complete"] is True
    assert value["registered_total_transactions"] == 157_696
    assert value["checkpoint_count"] == 16
    assert value["question_relevant_values"] is None
    assert value["scientific_first_true_outcome"] is None
    assert value["effect_refs"] == []
    assert value["evidence_tree"]["terminal_status"] == "COMPLETE_ONLY_MIRROR"
    assert all(node["status"] == "PASS" for node in value["evidence_tree"]["nodes"])
    result_root = TEST_ROOT / "result-slice"
    result_root.mkdir(parents=True, exist_ok=True)
    output = result_root / "mirror.json"
    output.unlink(missing_ok=True)
    with pytest.raises(ValueError, match="complete-only"):
        write_result_blind_complete_mirror(output, {**value, "complete": False})
    assert not output.exists()
    write_result_blind_complete_mirror(output, value)
    assert json.loads(output.read_text(encoding="utf-8")) == value
    assert not list(result_root.glob("*.tmp"))
    assert not RESERVED_ROOT.exists()


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
        "schema": "FSBS_R01_REGISTERED_RUNTIME_BOUNDARY_V2",
        "run_id": "fsbs-r01-complete-20260827-02",
        "output_root": "temp/directions/finite_semantic_boundary_support/exp/fsbs-r01-complete-20260827-02/",
        "legacy_terminal_run_id": "fsbs-r01-complete-20260827-01",
        "legacy_terminal_replay_permitted": False,
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
    assert parameters["effect_refs"] == [
        {
            "kind": "LOCAL_RESULT_ROOT",
            "resource_id": (
                "temp/directions/finite_semantic_boundary_support/exp/"
                "fsbs-r01-complete-20260827-02/"
            ),
            "operation": "CREATE_ONLY",
        }
    ]
    assert parameters["resource_caps"] == {
        "wall_seconds": 600,
        "cpu_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
        "workers": 1,
        "threads_per_worker": 1,
    }
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
    assert all(row["content_addressed"] is True for row in checkpoints)

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
        "a394938d-runtime-v2"
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
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_validation import (
        assert_no_terminal_rerun,
        validate_cold_resume_fixture,
    )

    assert not RESERVED_ROOT.exists()
    technical_root = TEST_ROOT / "legacy-technical-guards"
    technical_root.mkdir(parents=True, exist_ok=True)
    technical = validate_cold_resume_fixture(technical_root)
    assert technical == {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "cold_resume_equal": True,
        "repeated_update": False,
        "cross_arm_or_seed_state": False,
        "registered_seed_or_arm_used": False,
        "effect_refs": [],
    }
    terminal_root = TEST_ROOT / "terminal-no-rerun"
    terminal_root.mkdir(parents=True, exist_ok=True)
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
        write_runtime_prelaunch_acceptance,
    )
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_validation import (
        validate_runtime_prelaunch_acceptance,
    )

    acceptance_root = TEST_ROOT / "runtime-v2-acceptance"
    acceptance_root.mkdir(parents=True, exist_ok=True)
    output = acceptance_root / "acceptance.json"
    write_runtime_prelaunch_acceptance(
        output,
        REPO,
        candidate_branch=(
            "omp/finite_semantic_boundary_support/engineering/"
            "a394938d-runtime-v2"
        ),
        scratch_root=acceptance_root / "technical-fixture",
    )
    acceptance = json.loads(output.read_text(encoding="utf-8"))
    assert validate_runtime_prelaunch_acceptance(acceptance, REPO)["accepted"] is True
    assert acceptance["schema"] == "FSBS_R01_RUNTIME_V2_PRELAUNCH_ACCEPTANCE"
    assert acceptance["terminal_status"] == "RUNTIME_V2_TECHNICALLY_ACCEPTED"
    assert acceptance["runtime_contract"]["parameters"]["registered_total_transactions"] == 157_696
    assert acceptance["runtime_contract"]["resource_estimate"]["wall_seconds"] == 600
    assert acceptance["payload_argv"] == [
        "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
        "-m",
        "experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_transaction",
    ]
    assert acceptance["reserved_output_effect"] == {
        "kind": "LOCAL_RESULT_ROOT",
        "resource_id": (
            "temp/directions/finite_semantic_boundary_support/exp/"
            "fsbs-r01-complete-20260827-02/"
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
    assert acceptance["runtime_contract"]["candidate_branch"].endswith(
        "a394938d-runtime-v2"
    )
    assert acceptance["empirical_activity_released"] is False
    assert acceptance["operator_now"] is False
    assert acceptance["effect_refs"] == []
    tampered = json.loads(json.dumps(acceptance))
    tampered["runtime_contract"]["parameters"]["resource_caps"]["scratch_bytes"] = 1
    with pytest.raises(PermissionError, match="caps"):
        validate_runtime_prelaunch_acceptance(tampered, REPO)
    assert all(
        ref["sha256"] == hashlib.sha256((REPO / ref["path"]).read_bytes()).hexdigest()
        for ref in acceptance["runtime_contract"]["source_test_manifest"]["refs"]
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
    assert not list(acceptance_root.glob("*.tmp"))
    assert not RESERVED_ROOT.exists()


def test_process_cpu_measurement_observes_a_real_positive_clock_delta() -> None:
    from experiments.candidates.finite_semantic_boundary_support.variable_axis_uav_r01.empirical_manifest import (
        observe_positive_process_cpu_ns,
    )

    observed = [observe_positive_process_cpu_ns() for _ in range(4)]
    assert all(value > 0 for value in observed)
