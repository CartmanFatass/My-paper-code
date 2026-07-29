from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from ha_ctse_process import (
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as runner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ROOT = PROJECT_ROOT / (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)
TEST_SOURCE_COMMIT = "9" * 40


@pytest.fixture(scope="module")
def proof_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[Path, dict[str, object], dict[str, object], dict[str, object]]]:
    root = tmp_path_factory.mktemp("g49_proof") / "proof"
    training = runner.train(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    evaluation = runner.evaluate(run_root=root)
    analysis = runner.analyze(run_root=root)
    yield root, training, evaluation, analysis


def test_configuration_backend_and_formal_admission_are_fail_closed(
    tmp_path: Path,
) -> None:
    configuration = runner._configuration(formal=False)
    assert configuration["accepted_branch_starts"] == 1
    assert configuration["shared_real_trajectory_batches"] == 1
    assert configuration["episodes"] == 8
    assert configuration["horizon"] == 48
    assert configuration["real_transitions"] == 384
    assert configuration["ppo_passes_per_arm"] == 2
    assert configuration["actor_optimizer_steps_per_arm"] == 2
    assert configuration["bootstrap_resamples"] == 0
    assert configuration["formal_statistical_run"] is False
    assert configuration["reference_channel_count"] == 2
    assert configuration["reduced_channel_count"] == 1
    assert configuration["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert configuration["environment_python_fallback"] is False
    assert configuration["process_workers"] == 1
    assert configuration["worker_thread_controls"] == {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "torch_intraop_threads": 1,
    }
    with pytest.raises(ValueError, match="process_workers=1"):
        runner._configuration(formal=False, cpu_budget=4, process_workers=3)

    assert runner.ALIGNED_IMPLEMENTATION_COMMIT is None
    assert runner.ALIGNMENT_STAGE_COMMIT is None
    errors = runner._formal_admission_errors(
        source_commit=TEST_SOURCE_COMMIT,
        authorization_token=runner.AUTHORIZATION_TOKEN,
        preflight_root=None,
        alignment_disposition="ALIGNED",
        aligned_source_commit=TEST_SOURCE_COMMIT,
        alignment_stage_commit="8" * 40,
    )
    assert errors == [
        "G49 formal execution requires an independently ALIGNED source"
    ]
    with pytest.raises(ValueError, match="independently ALIGNED"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=TEST_SOURCE_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=ANCHOR_ROOT,
            alignment_disposition="ALIGNED",
            aligned_source_commit=TEST_SOURCE_COMMIT,
            alignment_stage_commit="8" * 40,
            preflight_root=tmp_path / "preflight",
        )


def test_full_proof_artifact_lifecycle_is_final_only_and_reloadable(
    proof_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    root, training, evaluation, analysis = proof_bundle
    assert training["passed"] is True
    assert training["formal"] is False
    assert training["formal_statistical_run"] is False
    assert training["scientific_iteration_cost"] == 0
    assert training["execution_readiness_proof_only"] is False
    assert training["two_process_equivalence"] is None
    assert training["dynamic_equivalence"]["D_SC"] == 0.0
    assert training["dynamic_equivalence"]["real_transitions"] == 384
    assert training["shared_trajectory"]["used_by_both_paths"] is True
    assert tuple(training["checkpoint_inventory"]) == source.ARMS
    assert all(
        row["kind"] == "final_only"
        for row in training["checkpoint_inventory"].values()
    )
    assert evaluation["passed"] is True
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["environment_transitions"] == 0
    assert evaluation["D_SC"] == 0.0
    assert analysis["result_branch"] == runner.REMOVABLE_BRANCH
    assert analysis["first_match_priority"] == [
        runner.INVALID_BRANCH,
        runner.COUPLING_BRANCH,
        runner.REMOVABLE_BRANCH,
        runner.UNRESOLVED_BRANCH,
    ]
    reloaded = runner.reload_artifacts(root)
    assert reloaded["training"]["source_commit"] == TEST_SOURCE_COMMIT
    assert reloaded["evaluation"]["D_SC"] == 0.0
    assert reloaded["analysis"]["result_branch"] == runner.REMOVABLE_BRANCH

    smoke = runner.readiness_interface_smoke(
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    assert smoke["return_schema"] == "G49_train_manifest_v1"
    assert smoke["static_certificate"]["passed"] is True


def test_two_real_processes_reconstruct_identical_model_adam_and_evidence(
    proof_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = proof_bundle
    report = runner.prove_two_process_equivalence(
        proof_root=tmp_path / "parallel",
        accepted_anchor_root=ANCHOR_ROOT,
        trajectory_path=root / runner.SHARED_TRAJECTORY_REFERENCE,
    )
    assert report["passed"] is True
    assert report["worker_count"] == 2
    assert report["distinct_processes"] is True
    assert report["single_thread_workers"] is True
    assert report["deterministic_preassigned_index_merge"] is True
    assert report["duplicated_environment_interaction"] is False
    assert report["real_transitions"] == 384
    assert report[
        "parameters_Adam_evidence_checkpoint_bitwise_equivalent"
    ] is True

    ordinary = {
        "execution_readiness_proof_only": False,
        "two_process_equivalence": None,
        "two_process_equivalence_artifact": None,
    }
    attached = runner._attach_readiness_process_proof(ordinary, report)
    assert attached["execution_readiness_proof_only"] is True
    assert attached["two_process_equivalence"] == report
    assert attached["two_process_equivalence_artifact"] == (
        runner.TWO_PROCESS_REPORT_REFERENCE
    )
    premature = copy.deepcopy(ordinary)
    premature["execution_readiness_proof_only"] = True
    with pytest.raises(ValueError, match="marked complete before process proof"):
        runner._attach_readiness_process_proof(premature, report)


def test_artifact_and_first_match_tamper_guards_fail_closed(
    proof_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = proof_bundle
    tampered = tmp_path / "manifest_tampered"
    shutil.copytree(root, tampered)
    manifest_path = tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dynamic_equivalence"]["D_SC"] = 1.0
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="train manifest invariant mismatch"):
        runner.validate_training_artifacts(tampered)

    reduced_tampered = tmp_path / "checkpoint_tampered"
    shutil.copytree(root, reduced_tampered)
    path = runner._checkpoint_path(reduced_tampered, source.REDUCED_ARM)
    checkpoint = runner._load_checkpoint(path)
    checkpoint["route_schema"]["channel_2_placeholder"] = 0
    runner._save_checkpoint(path, checkpoint)
    manifest_path = reduced_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checkpoint_inventory"][source.REDUCED_ARM]["sha256"] = (
        runner._artifact_digest(path)
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="checkpoint reload validation failed"):
        runner.validate_training_artifacts(reduced_tampered)

    base = {
        "valid": True,
        "static_factorization": True,
        "D_SC": 0.0,
        "canonical_projection_equal": True,
    }
    assert runner.select_g49_result_branch(base) == runner.REMOVABLE_BRANCH
    invalid = copy.deepcopy(base)
    invalid["valid"] = False
    assert runner.select_g49_result_branch(invalid) == runner.INVALID_BRANCH
    coupling = copy.deepcopy(base)
    coupling["static_factorization"] = False
    assert runner.select_g49_result_branch(coupling) == runner.COUPLING_BRANCH
    unresolved = copy.deepcopy(base)
    unresolved["D_SC"] = 1.0
    assert runner.select_g49_result_branch(unresolved) == runner.UNRESOLVED_BRANCH


def test_g49_import_leaves_accepted_g48_identity_unchanged() -> None:
    assert source.g48.ALGORITHM_ID == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_"
        "ATTRIBUTION_G48"
    )
    assert source.g48.ARMS == (
        "NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR",
        "NATIVE6_G31_DUPLICATED_IMMEDIATE",
    )
    assert runner.g48_runner.ALGORITHM_ID == source.g48.ALGORITHM_ID
