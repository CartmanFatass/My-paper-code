from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from ha_ctse_process import (
    continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as g46_source,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47
    as runner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ROOT = PROJECT_ROOT / (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)
TEST_SOURCE_COMMIT = "7" * 40


@pytest.fixture(scope="module")
def readiness_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[Path, dict[str, object], dict[str, object], dict[str, object]]]:
    root = tmp_path_factory.mktemp("g47_readiness") / "proof"
    training = runner.readiness_train(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    evaluation = runner.readiness_evaluate(run_root=root)
    analysis = runner.readiness_analyze(run_root=root)
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
    assert configuration["reference_baseline_optimizer_steps"] == 2
    assert configuration["reduced_baseline_optimizer_steps"] == 0
    assert configuration["bootstrap_resamples"] == 0
    assert configuration["formal_statistical_run"] is False
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
        runner._configuration(formal=False, cpu_budget=2, process_workers=2)

    assert runner.ALIGNED_IMPLEMENTATION_COMMIT is None
    assert runner.ALIGNMENT_STAGE_COMMIT is None
    with pytest.raises(ValueError, match="independently ALIGNED"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=TEST_SOURCE_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=ANCHOR_ROOT,
            alignment_disposition="ALIGNED",
            aligned_source_commit="8" * 40,
            alignment_stage_commit="9" * 40,
            preflight_root=tmp_path / "missing",
        )


def test_readiness_lifecycle_reloads_exact_final_only_artifacts(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    root, training, evaluation, analysis = readiness_bundle
    assert training["passed"] is True
    assert training["scientific_iteration_cost"] == 0
    assert training["formal_statistical_run"] is False
    assert training["dynamic_equivalence"]["D_G47"] == 0
    assert training["dynamic_equivalence"]["real_transitions"] == 384
    assert all(
        training["static_certificate"]["static_predicates"][name] == 0
        for name in (
            "baseline_true_state_read_into_reduced_actor_gradient",
            "baseline_true_state_read_into_reduced_actor_action_or_logprob",
            "baseline_true_state_read_into_reduced_evaluation",
        )
    )
    assert tuple(training["checkpoint_inventory"]) == source.ARMS
    assert all(
        row["kind"] == "final_only"
        for row in training["checkpoint_inventory"].values()
    )
    assert evaluation["passed"] is True
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["additional_real_transitions"] == 0
    assert analysis["result_branch"] == runner.REMOVABLE_BRANCH
    assert analysis["first_match_order"] == [
        runner.INVALID_BRANCH,
        runner.COUPLING_BRANCH,
        runner.REMOVABLE_BRANCH,
        runner.UNRESOLVED_BRANCH,
    ]
    reloaded = runner.reload_artifacts(root)
    assert reloaded["training"]["source_commit"] == TEST_SOURCE_COMMIT
    assert reloaded["evaluation"]["D_G47"] == 0
    assert reloaded["analysis"]["result_branch"] == runner.REMOVABLE_BRANCH

    smoke = runner.readiness_interface_smoke(
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    assert smoke["return_schema"] == "G47_train_manifest_v1"
    assert smoke["static_certificate"]["passed"] is True


def test_artifact_tamper_and_first_match_guards_fail_closed(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = readiness_bundle
    tampered = tmp_path / "tampered"
    shutil.copytree(root, tampered)
    manifest_path = tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dynamic_equivalence"]["D_G47"] = 1
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="train manifest invariant mismatch"):
        runner.validate_training_artifacts(tampered)

    static_tampered = tmp_path / "static_tampered"
    shutil.copytree(root, static_tampered)
    static_manifest_path = static_tampered / runner.TRAIN_MANIFEST
    static_manifest = json.loads(
        static_manifest_path.read_text(encoding="utf-8")
    )
    static_manifest["static_certificate"]["static_predicates"][
        "baseline_true_state_read_into_reduced_evaluation"
    ] = 1
    static_manifest_path.write_text(
        json.dumps(static_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="train manifest invariant mismatch"):
        runner.validate_training_artifacts(static_tampered)

    base = {
        "operational_valid": True,
        "coupling_localized": False,
        "static_certificate_pass": True,
        "dynamic_equivalence_pass": True,
        "D_G47": 0,
    }
    assert runner.select_g47_result_branch(base) == runner.REMOVABLE_BRANCH
    invalid = copy.deepcopy(base)
    invalid["operational_valid"] = False
    invalid["coupling_localized"] = True
    assert runner.select_g47_result_branch(invalid) == runner.INVALID_BRANCH
    coupling = copy.deepcopy(base)
    coupling["coupling_localized"] = True
    assert runner.select_g47_result_branch(coupling) == runner.COUPLING_BRANCH
    unresolved = copy.deepcopy(base)
    unresolved["dynamic_equivalence_pass"] = False
    assert runner.select_g47_result_branch(unresolved) == runner.UNRESOLVED_BRANCH


def test_g47_import_and_orchestration_leave_g46_identity_unchanged() -> None:
    assert g46_source.ARMS == (
        "NATIVE6_G31_NO_READ_BASELINE_SHADOW_NORM",
        "NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM",
    )
    assert source.ARMS == (
        "NATIVE6_G31_RAW_NORM_SHADOW_BASELINE",
        "NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE",
    )
    assert runner.g46_runner.ALGORITHM_ID == g46_source.ALGORITHM_ID
