from __future__ import annotations

import copy
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from ha_ctse_process import (
    continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45
    as g45_runner,
)
from scripts import (
    run_continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as runner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ROOT = PROJECT_ROOT / (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)
TEST_SOURCE_COMMIT = "6" * 40


@pytest.fixture(scope="module")
def readiness_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[Path, dict[str, object], dict[str, object], dict[str, object]]]:
    root = tmp_path_factory.mktemp("g46_readiness") / "exercise"
    training = runner.readiness_train(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    evaluation = runner.readiness_evaluate(run_root=root)
    analysis = runner.readiness_analyze(run_root=root)
    yield root, training, evaluation, analysis


def test_configuration_seed_backend_and_formal_admission_are_exact(
    tmp_path: Path,
) -> None:
    nonformal = runner._configuration(formal=False)
    formal = runner._configuration(formal=True, cpu_budget=6, process_workers=6)
    assert nonformal["arms"] == list(source.ARMS)
    assert nonformal["branch_updates_per_arm"] == 10
    assert nonformal["training_transitions"] == 7_680
    assert nonformal["evaluation_transitions"] == 6_912
    assert nonformal["total_real_transitions"] == 14_592
    assert nonformal["optimizer_steps"] == 40
    assert formal["replicates"] == 3
    assert formal["branch_updates_per_arm"] == 100
    assert formal["training_transitions"] == 230_400
    assert formal["evaluation_transitions"] == 165_888
    assert formal["total_real_transitions"] == 396_288
    assert formal["optimizer_steps"] == 1_200
    assert formal["cpu_budget"] == 6
    assert formal["process_workers"] == 6
    assert formal["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert formal["environment_python_fallback"] is False
    assert formal["worker_thread_controls"] == {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "torch_intraop_threads": 1,
    }
    assert runner.SEED_BASES == g45_runner.SEED_BASES
    assert runner.seed_block(0, formal=True) == runner.SEED_BASES
    assert runner.seed_block(2, formal=True) == {
        name: value + 2 for name, value in runner.SEED_BASES.items()
    }
    assert runner.seed_block(0, formal=False) == {
        name: value + runner.NONFORMAL_SEED_OFFSET
        for name, value in runner.SEED_BASES.items()
    }
    assert runner.bootstrap_seed(formal=True) == 10_457_045
    assert runner.bootstrap_seed(formal=False) == 11_357_045
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT is None
    assert runner.ALIGNMENT_STAGE_COMMIT is None
    with pytest.raises(ValueError, match="ALIGNED source"):
        runner._backend._validate_formal_preflight(
            tmp_path / "unbound_alignment_never_read",
            source_commit=TEST_SOURCE_COMMIT,
            alignment_disposition="ALIGNED",
            aligned_source_commit=TEST_SOURCE_COMMIT,
            alignment_stage_commit="7" * 40,
            accepted_anchor_root=ANCHOR_ROOT.resolve(),
        )
    never_root = tmp_path / "formal_must_not_start"
    with pytest.raises(ValueError, match="ALIGNED source"):
        runner.train(
            run_root=never_root,
            source_commit=TEST_SOURCE_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=ANCHOR_ROOT,
            preflight_root=tmp_path / "unread_preflight",
            alignment_disposition="ALIGNED",
            aligned_source_commit=TEST_SOURCE_COMMIT,
            alignment_stage_commit="7" * 40,
        )
    assert not never_root.exists()
    for value in (0, 7):
        with pytest.raises(ValueError):
            runner._configuration(
                formal=False, cpu_budget=value, process_workers=value
            )


def test_g46_isolated_orchestration_does_not_mutate_g45() -> None:
    assert g45_runner.ALGORITHM_ID == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_"
        "ATTRIBUTION_G45"
    )
    assert g45_runner.source.ARMS == (
        "NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ",
        "NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ",
    )
    assert runner._backend.source is source
    assert runner._backend._training_replicate_worker.__module__ == runner.__name__
    assert runner._backend._evaluation_cell_worker.__module__ == runner.__name__
    assert runner.source_controls()["parent_source_id"] == g45_runner.source.SOURCE_ID


def test_result_branch_order_and_equality_boundary() -> None:
    base = {
        "operational_valid": True,
        "source_valid": True,
        "read_access_pass": True,
        "no_read_access_pass": True,
        "read_access_confident_fail": False,
        "no_read_access_confident_fail": False,
        "no_read_noninferior": True,
        "material_baseline_conditioning_advantage": False,
    }
    assert runner.select_g46_result_branch(base) == runner.RAW_SUFFICIENT_BRANCH
    assert (
        runner.select_g46_result_branch(dict(base, operational_valid=False))
        == runner.INVALID_BRANCH
    )
    assert (
        runner.select_g46_result_branch(dict(base, source_valid=False))
        == runner.SOURCE_FAILURE_BRANCH
    )
    advantage = dict(
        base,
        no_read_access_pass=False,
        no_read_noninferior=False,
        no_read_access_confident_fail=True,
    )
    assert runner.select_g46_result_branch(advantage) == (
        runner.SHADOW_ADVANTAGE_BRANCH
    )
    underpowered = dict(
        base,
        no_read_noninferior=False,
        material_baseline_conditioning_advantage=False,
    )
    assert runner.select_g46_result_branch(underpowered) == (
        runner.UNDERPOWERED_BRANCH
    )


def test_readiness_lifecycle_real_two_process_and_artifact_reload(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    root, training, evaluation, analysis = readiness_bundle
    assert training["algorithm"] == source.ALGORITHM_ID
    assert training["source_id"] == source.SOURCE_ID
    assert training["formal"] is False
    assert training["scientific_iteration_cost"] == 0
    assert training["conclusion_bearing"] is False
    assert training["production_configuration"]["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    proof = training["two_process_update_equivalence"]
    assert proof["proof_kind"] == "two_process_single_g46_update_equivalence"
    assert proof["worker_count"] == 2
    assert proof["distinct_processes"] is True
    assert proof["single_thread_workers"] is True
    assert proof["deterministic_preassigned_index_merge"] is True
    assert proof["parameters_adam_evidence_bitwise_equivalent"] is True
    assert proof["passed"] is True
    assert source._update_evidence_valid(training["update_evidence"])
    assert source.validate_conclusion_evidence(
        training["proof_activation_evidence"]
    )
    assert set(training["checkpoints"]) == set(source.ARMS)
    assert evaluation["status"] == "COMPLETE"
    assert len(evaluation["cells"]) == 2
    assert all(cell["optimizer_steps"] == 0 for cell in evaluation["cells"])
    assert analysis["status"] == "COMPLETE"
    assert analysis["science_disposition"] is None
    assert analysis["scientific_iteration_cost"] == 0
    assert runner.reload_readiness_artifacts(root)["passed"] is True
    assert runner.validate_readiness_artifacts(root) == []
    assert (root / "train_manifest.json").is_file()
    assert (root / "evaluation_manifest.json").is_file()
    assert (root / "analysis_result.json").is_file()
    assert (root / "parallel_proof/two_process_update_equivalence.json").is_file()


def test_readiness_and_checkpoint_reload_reject_schedule_tampering(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, training, _, _ = readiness_bundle
    leaked = copy.deepcopy(training)
    leaked["update_evidence"]["pass_records"][0]["composition"][
        source.RAW_NORM_ARM
    ]["baseline_counterfactual_calls"] = 1
    assert runner.readiness_training_errors(root, leaked)

    forged_q = copy.deepcopy(training)
    activation = forged_q["proof_activation_evidence"]["replicate_rows"][0][
        "reconstructed_passes"
    ][0]["activation"]
    activation["q_norm"] = 1.0
    assert runner.readiness_training_errors(root, forged_q)

    final_update = training["update_evidence"]
    conclusion = training["proof_activation_evidence"]
    certificate = {
        "residual_evidence_arms": list(source.ARMS),
        "final_update_evidence": final_update,
        "conclusion_evidence": conclusion,
        "baseline_gradient_groups_by_arm": (
            source._baseline_gradient_groups_from_pass(
                final_update["pass_records"][-1]
            )
        ),
        "no_read_certificate": final_update["pass_records"][-1]["composition"][
            source.RAW_NORM_ARM
        ],
        "baseline_checkpoint_selection_read_count": 0,
        "baseline_evaluation_metric_read_count": 0,
    }
    production_training = {
        "replicate_results": [{"update_records": [final_update]}],
        "conclusion_evidence": conclusion,
    }
    payload = {"source_final_checkpoint_certificate": certificate}
    monkeypatch.setattr(
        runner._base._base,
        "_original_load_checkpoint_payload",
        lambda *args, **kwargs: payload,
    )
    assert runner._load_checkpoint_payload(
        Path("unused.pt"),
        training=production_training,
        replicate=0,
        arm=source.RAW_NORM_ARM,
    ) is payload

    tampered = copy.deepcopy(payload)
    tampered["source_final_checkpoint_certificate"]["no_read_certificate"][
        "baseline_counterfactual_calls"
    ] = 1
    monkeypatch.setattr(
        runner._base._base,
        "_original_load_checkpoint_payload",
        lambda *args, **kwargs: tampered,
    )
    with pytest.raises(ValueError, match="checkpoint evidence mismatch"):
        runner._load_checkpoint_payload(
            Path("unused.pt"),
            training=production_training,
            replicate=0,
            arm=source.RAW_NORM_ARM,
        )


def test_thread_environment_is_hard_bound_before_compute() -> None:
    for name in runner.WORKER_THREAD_ENV:
        assert os.environ[name] == "1"
    smoke = runner.readiness_interface_smoke(
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    assert smoke["return_schema"] == "G46_execution_readiness_train_manifest_v1"
    assert smoke["formal"] is False
    assert smoke["scientific_iteration_cost"] == 0
    assert smoke["production_configuration"]["process_workers"] == 2
