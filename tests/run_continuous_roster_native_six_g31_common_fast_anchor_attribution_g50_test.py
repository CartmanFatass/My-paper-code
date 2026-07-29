from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / (
    "scripts/run_continuous_roster_native_six_g31_common_fast_anchor_"
    "attribution_g50.py"
)


@pytest.fixture(scope="module")
def runner():
    name = "tests._g50_runner_focused"
    spec = importlib.util.spec_from_file_location(name, RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_result_contract_configuration_counts_and_source_authority(runner) -> None:
    nonformal = runner._configuration(
        formal=False, cpu_budget=2, process_workers=2
    )
    assert nonformal["replicates"] == 1
    assert nonformal["phase_A_updates_per_arm"] == 10
    assert nonformal["phase_B_updates_per_arm"] == 10
    assert nonformal["evaluation_cells"] == 24
    assert nonformal["episodes_per_cell"] == 6
    assert nonformal["total_real_transitions"] == 22_272
    assert nonformal["optimizer_steps"] == 80
    assert nonformal["bootstrap_resamples"] == 250

    formal = runner._configuration(formal=True, cpu_budget=2, process_workers=2)
    assert formal["replicates"] == 3
    assert formal["phase_A_updates_per_arm"] == 100
    assert formal["phase_B_updates_per_arm"] == 100
    assert formal["evaluation_cells"] == 72
    assert formal["episodes_per_cell"] == 48
    assert formal["total_real_transitions"] == 626_688
    assert formal["optimizer_steps"] == 2_400
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["environment_backend"] == "ContinuousRosterToyBatch_CPU_CPP_required"
    assert formal["python_fallback"] is False

    controls = runner.source_controls()
    assert controls["historical_anchor_used_as_objective_authority_only"] is True
    assert controls["historical_anchor_checkpoint_loaded_as_G50_initial_state"] is False
    assert controls["phase_A_source_commit"] == (
        "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
    )
    assert controls["phase_B_source_commit"] == (
        "8ecb01fd3ac0debf1b792e4e51293e07974d633b"
    )


def test_accepted_anchor_replicate_interface_survives_private_backend_binding(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert runner.source.ACCEPTED_G40_ANCHOR_REPLICATES == (0, 1, 2)
    assert runner._backend.source is runner.source

    rows = []
    for replicate in runner.source.ACCEPTED_G40_ANCHOR_REPLICATES:
        authority = runner._backend.g41.accepted_g40_anchor_authority(replicate)
        rows.append(
            {
                "replicate": replicate,
                "common_anchor": {
                    "checkpoint": authority.checkpoint_reference,
                    "state_digest": authority.complete_state_digest,
                    "optimizer_steps": (
                        runner._backend.g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS
                    ),
                },
            }
        )
    manifest = {
        "schema_version": runner._backend.g41.ACCEPTED_G40_SCHEMA_VERSION,
        "algorithm": runner._backend.g40.ALGORITHM_ID,
        "source_id": runner._backend.g40.SOURCE_ID,
        "source_commit": runner._backend.g41.ACCEPTED_G40_SOURCE_COMMIT,
        "formal": True,
        "authorization_token": (
            runner._backend.g41.ACCEPTED_G40_AUTHORIZATION_TOKEN
        ),
        "status": "COMPLETE",
        "configuration": dict(
            runner._backend.g41.ACCEPTED_G40_CONFIGURATION_FIELDS
        ),
        "replicate_results": rows,
    }
    monkeypatch.setattr(runner._backend, "_read_json", lambda _path: manifest)
    monkeypatch.setattr(
        runner._backend, "_artifact_digest", lambda path: f"digest:{path.name}"
    )

    assert runner._backend._validate_anchor_manifest(tmp_path) == {
        "manifest": "digest:train_manifest.json",
        "checkpoint_0": "digest:replicate_0_common_native6_fast_anchor.pt",
        "checkpoint_1": "digest:replicate_1_common_native6_fast_anchor.pt",
        "checkpoint_2": "digest:replicate_2_common_native6_fast_anchor.pt",
    }


def test_five_branch_first_match_order_and_tokens(runner) -> None:
    assert runner._synthetic_branch_witnesses() == {
        "invalid": runner.INVALID_BRANCH,
        "source_failure": runner.SOURCE_FAILURE_BRANCH,
        "sufficient": runner.NULL_SUFFICIENT_BRANCH,
        "advantage": runner.REFERENCE_ADVANTAGE_BRANCH,
        "underpowered": runner.UNDERPOWERED_BRANCH,
    }
    assert runner.select_g50_result_branch(
        {
            "operational_valid": False,
            "source_valid": True,
            "reference_access_confident_fail": False,
            "reference_access_pass": True,
            "null_access_pass": True,
            "null_access_confident_fail": False,
            "fresh_single_immediate_noninferior": True,
            "material_common_fast_anchor_advantage": True,
        }
    ) == runner.INVALID_BRANCH
    assert runner.select_g50_result_branch(
        {
            "operational_valid": True,
            "source_valid": True,
            "reference_access_confident_fail": True,
            "reference_access_pass": False,
            "null_access_pass": True,
            "null_access_confident_fail": False,
            "fresh_single_immediate_noninferior": True,
            "material_common_fast_anchor_advantage": False,
        }
    ) == runner.SOURCE_FAILURE_BRANCH


def test_reference_access_failure_precedes_favorable_comparison_without_confidence(
    runner,
) -> None:
    assert runner.select_g50_result_branch(
        {
            "operational_valid": True,
            "source_valid": True,
            "reference_access_pass": False,
            "reference_access_confident_fail": False,
            "null_access_pass": True,
            "null_access_confident_fail": False,
            "fresh_single_immediate_noninferior": True,
            "material_common_fast_anchor_advantage": True,
        }
    ) == runner.SOURCE_FAILURE_BRANCH


def test_formal_admission_is_bound_and_fails_before_runtime_without_preflight(
    runner, tmp_path
) -> None:
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == (
        "b8290699f5c10c593bbc21a6666c17950fae84d3"
    )
    assert runner.ALIGNMENT_STAGE_COMMIT == (
        "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
    )
    result = runner.validate_formal_admission(
        source_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
        authorization_token=runner.AUTHORIZATION_TOKEN,
        accepted_anchor_root=runner.PROJECT_ROOT / runner.ACCEPTED_ANCHOR_ROOT_RELATIVE,
        preflight_root=tmp_path / "missing_preflight",
        alignment_disposition="ALIGNED",
        aligned_source_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
        alignment_stage_commit=runner.ALIGNMENT_STAGE_COMMIT,
        cpu_budget=2,
        process_workers=2,
    )
    assert result["admitted"] is False
    assert result["errors"] == ["same_source_preflight"]
    implementation = inspect.getsource(runner.train)
    assert implementation.index("_formal_admission_errors") < implementation.index(
        "_configure_cpu_execution"
    )
    assert implementation.index("_formal_admission_errors") < implementation.index(
        "root.mkdir"
    )


def test_checkpoint_inventory_and_terminal_artifact_names_are_exact(runner) -> None:
    formal = runner._configuration(formal=True, cpu_budget=2, process_workers=2)
    assert runner._expected_checkpoint_files(formal) == {
        f"checkpoints/replicate_{replicate}_{arm.lower()}_final.pt"
        for replicate in range(3)
        for arm in runner.source.ARMS
    }
    assert len(runner._expected_checkpoint_files(formal)) == 6
    assert runner.TRAIN_MANIFEST == "train_manifest.json"
    assert runner.EVALUATION_MANIFEST == "evaluation_manifest.json"
    assert runner.ANALYSIS_RESULT == "analysis_result.json"
    assert all("intermediate" not in row for row in runner._expected_checkpoint_files(formal))


def test_paired_bootstrap_plan_uses_whole_episode_indices(runner) -> None:
    replicate_indices, episode_indices = runner._backend._bootstrap_plan(
        formal=False, replicates=1, episodes=6, repetitions=3
    )
    assert tuple(replicate_indices.shape) == (3, 1)
    assert tuple(episode_indices.shape) == (3, 1, 3, 6)
    assert replicate_indices.min() == 0 and replicate_indices.max() == 0
    assert episode_indices.min() >= 0 and episode_indices.max() < 6
    comparison_source = inspect.getsource(runner._comparison)
    assert comparison_source.count("plan") >= 2


def test_cpu_spawn_and_single_thread_contract_is_exact(runner) -> None:
    cpu = runner._resolve_cpu_execution(2, 2)
    assert cpu == {
        "cpu_budget": 2,
        "process_workers": 2,
        "supported_process_worker_ceiling": 6,
        "worker_thread_controls": {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        },
        "torch_intraop_threads": 1,
        "worker_start_method": "spawn",
        "deterministic_merge": "preassigned_index_not_completion_order",
    }
    with pytest.raises(ValueError):
        runner._resolve_cpu_execution(1, 2)
    with pytest.raises(ValueError):
        runner._resolve_cpu_execution(2, 7)


def test_readiness_interfaces_are_zero_science_and_cover_six_phases(runner) -> None:
    source_text = RUNNER_PATH.read_text(encoding="utf-8")
    for stage in (
        "readiness-smoke",
        "readiness-train",
        "readiness-validate",
        "readiness-reload",
        "readiness-evaluate",
        "readiness-analyze",
    ):
        assert stage in source_text
    for function in (
        runner.readiness_train,
        runner.readiness_validate,
        runner.readiness_reload,
        runner.readiness_evaluate,
        runner.readiness_analyze,
    ):
        implementation = inspect.getsource(function)
        assert "formal=True" not in implementation
    readiness_train_source = inspect.getsource(runner.readiness_train)
    assert "_run_distinct_readiness_workers(tasks)" in readiness_train_source
    assert "_backend._run_indexed_worker_tasks" not in readiness_train_source
    assert '"scientific_real_transitions": 0' in readiness_train_source
    assert '"optimizer_steps": 0' in readiness_train_source


def test_readiness_two_process_proof_cannot_reuse_one_pool_worker(runner) -> None:
    implementation = inspect.getsource(runner._run_distinct_readiness_workers)
    assert 'multiprocessing.get_context("spawn")' in implementation
    assert "context.Process(" in implementation
    assert "ready_event.wait(timeout=60.0)" in implementation
    assert "release_event.set()" in implementation
    assert "len(set(pids)) != 2" in implementation
    assert 'row.get("pid") != process.pid' in implementation


def test_formal_token_and_predecessor_bindings_are_frozen(runner) -> None:
    assert runner.AUTHORIZATION_TOKEN == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_"
        "FORMAL_AUTHORIZATION_V1"
    )
    assert runner.ALIGNMENT_AUDIT_ID.endswith("G50_CODE_SCIENCE_ALIGNMENT_AUDIT")
    assert str(runner.ACCEPTED_ANCHOR_ROOT_RELATIVE).replace("\\", "/") == (
        "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
        "20260727_97a8b23_r1"
    )
    assert runner.source.PHASE_B_ALIGNED_IMPLEMENTATION_COMMIT == (
        "9edddc845d88191bbfbd6c2ec779551edbbcb78a"
    )
    assert runner.source.PHASE_B_ALIGNMENT_STAGE_COMMIT == (
        "b56288597c6c91f784fb5f0fcc36ec5ef92de452"
    )
