from __future__ import annotations

import copy
import inspect
import json
import shutil
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from scripts import (
    run_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51
    as runner_module,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / (
    "scripts/run_continuous_roster_native_six_g31_phase_a_shadow_baseline_"
    "module_reduction_g51.py"
)
TEST_SOURCE_COMMIT = "5" * 40


@pytest.fixture(scope="module")
def runner():
    return runner_module


@pytest.fixture(scope="module")
def readiness_bundle(
    runner, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[
    tuple[Path, dict[str, object], dict[str, object], dict[str, object]]
]:
    root = tmp_path_factory.mktemp("g51_readiness") / "proof"
    training = runner.readiness_train(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
    )
    evaluation = runner.readiness_evaluate(run_root=root)
    analysis = runner.readiness_analyze(run_root=root)
    yield root, training, evaluation, analysis


def _contains_baseline_identity(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            "baseline" in str(key).lower()
            or _contains_baseline_identity(row)
            for key, row in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_baseline_identity(row) for row in value)
    return isinstance(value, str) and "baseline" in value.lower()


def _synthetic_adverse_failure(
    runner, *, branch: str, static: Mapping[str, object]
) -> object:
    if branch == runner.INVALID_BRANCH:
        invalid_static = copy.deepcopy(static)
        predicate = next(iter(invalid_static["static_predicates"]))
        invalid_static["static_predicates"][predicate] = 1
        invalid_static["passed"] = False
        return runner.source.G51InvariantError(
            "static_certificate_failed_before_optimizer", invalid_static
        )
    if branch == runner.COUPLING_BRANCH:
        return runner.source.G51InvariantError(
            "phase_A_pre_step_semantic_coupling",
            {
                "pass_index": 0,
                "optimizer_ledger": runner.source._optimizer_ledger(
                    paired_passes=0,
                    failure_detected_before_current_pair=True,
                ),
                "static_certificate": static,
                "comparison": {
                    "actor_assigned_gradient_bytes_equal": True,
                    "policy_loss_bytes_equal": True,
                    "teacher_logprob_bytes_equal": True,
                    "teacher_pre_tanh_bytes_equal": True,
                    "teacher_action_bytes_equal": True,
                    "baseline_loss_gradient_into_actor_count": 1,
                    "actor_loss_gradient_into_baseline_count": 0,
                    "plan_RNG_unchanged": True,
                },
            },
        )
    if branch == runner.UNRESOLVED_BRANCH:
        return runner.source.G51InvariantError(
            "phase_A_actual_Adam_kernel_difference",
            {
                "pass_index": 0,
                "optimizer_ledger": runner.source._optimizer_ledger(
                    paired_passes=1,
                    failure_detected_before_current_pair=False,
                ),
                "static_certificate": static,
                "comparison": {"synthetic_zero_work_test": True},
            },
        )
    raise AssertionError(f"unsupported synthetic adverse branch: {branch}")


def test_configuration_provenance_and_formal_admission_are_fail_closed(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    configuration = runner._configuration(formal=False)
    assert configuration["proof_kind"] == (
        "structural_certificate_plus_mandatory_actual_Adam_kernel_witness"
    )
    assert configuration["accepted_G50_fresh_initializations"] == 1
    assert configuration["shared_stored_phase_A_batches"] == 1
    assert configuration["episodes"] == 8
    assert configuration["horizon"] == 48
    assert configuration["real_transitions"] == 384
    assert configuration["PPO_passes_per_arm"] == 2
    assert configuration["actor_optimizer_steps_per_arm"] == 2
    assert configuration["reference_baseline_parameter_Adam_exposures"] == 2
    assert configuration["reduced_baseline_parameter_Adam_exposures"] == 0
    assert configuration["total_optimizer_steps"] == 4
    assert configuration["phase_B_optimizer_steps"] == 0
    assert configuration["bootstrap_resamples"] == 0
    assert configuration["formal_statistical_run"] is False
    assert configuration["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert configuration["environment_python_fallback"] is False
    assert configuration["K_search"] == 0
    assert configuration["hypothetical_transitions"] == 0
    assert configuration["process_workers"] == 1
    assert configuration["same_stored_trajectory_for_both_paths"] is True
    controls = runner.source_controls()
    assert controls["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert controls["environment_python_fallback"] is False
    native_backend = runner._native_backend_identity()
    assert native_backend == runner.g50_runner._backend._native_backend_identity()
    assert native_backend["kind"] == "ContinuousRosterToyBatch_CPU_CPP"
    assert native_backend["required"] is True
    assert native_backend["python_fallback"] is False
    with pytest.raises(ValueError, match="process_workers=1"):
        runner._configuration(formal=False, cpu_budget=2, process_workers=2)

    assert runner.DESIGN_STAGE_COMMIT == (
        "fb16a412841ad69912d927262dae8f694ea5471a"
    )
    assert runner.ACCEPTED_PREDECESSOR_SOURCE_COMMIT == (
        "044d9690fa19aa07b8e68bf5cbb2a159c19be8c1"
    )
    assert runner.source.ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT == (
        "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
    )
    assert runner.FORMAL_SOURCE_COMMIT == (
        "ce6ed8659c480ca2779155b2871dc82b89fa0e95"
    )
    assert runner.AUTHORIZATION_TOKEN == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_"
        "REDUCTION_G51_FORMAL_AUTHORIZATION_V1"
    )
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == (
        "188b210975a0f243ae34318d658fbf943d1d63ab"
    )
    assert runner.ALIGNMENT_STAGE_COMMIT == (
        "aa756dcd06a2ea622c155f2983a89bb5d76e9d80"
    )
    assert "formal_authorization_token" not in controls
    assert "aligned_implementation_commit" not in controls
    monkeypatch_preflight = tmp_path / "preflight"
    monkeypatch.setattr(runner, "PREFLIGHT_ROOT", monkeypatch_preflight)
    assert runner._formal_admission_errors(
        source_commit=runner.FORMAL_SOURCE_COMMIT,
        authorization_token=runner.AUTHORIZATION_TOKEN,
        preflight_root=monkeypatch_preflight,
        alignment_disposition="ALIGNED",
        aligned_implementation_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
        alignment_stage_commit=runner.ALIGNMENT_STAGE_COMMIT,
    ) == []
    wrong_binding_errors = runner._formal_admission_errors(
        source_commit=TEST_SOURCE_COMMIT,
        authorization_token="invented",
        preflight_root=tmp_path,
        alignment_disposition="MISMATCH",
        aligned_implementation_commit="3" * 40,
        alignment_stage_commit="4" * 40,
    )
    assert wrong_binding_errors == [
        "G51 formal authorization token mismatch",
        "G51 formal execution source identity mismatch",
        "G51 formal alignment disposition is not ALIGNED",
        "G51 formal aligned implementation identity mismatch",
        "G51 formal alignment stage identity mismatch",
        "G51 formal preflight root identity mismatch",
    ]
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=TEST_SOURCE_COMMIT,
            formal=True,
            authorization_token="invented",
            preflight_root=tmp_path,
            alignment_disposition="ALIGNED",
            aligned_implementation_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
            alignment_stage_commit=runner.ALIGNMENT_STAGE_COMMIT,
        )
    assert not (tmp_path / "formal").exists()
    implementation = inspect.getsource(runner._materialize_source_bundle)
    assert 'ledger_seed=seeds["phase_A_ledger"]' in implementation
    assert 'action_seed=seeds["phase_A_action"]' in implementation


def test_cli_separates_formal_train_from_nonformal_and_inferred_stages(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatched = False

    def forbidden_dispatch(**_arguments: object) -> object:
        nonlocal dispatched
        dispatched = True
        raise AssertionError("G51 CLI dispatched a formal-bearing request")

    for name in (
        "train",
        "evaluate",
        "analyze",
        "exercise",
        "readiness_interface_smoke",
        "readiness_train",
        "readiness_validate",
        "readiness_reload",
        "readiness_evaluate",
        "readiness_analyze",
    ):
        monkeypatch.setattr(runner, name, forbidden_dispatch)

    stages = (
        "evaluate",
        "analyze",
        "exercise",
        "readiness-smoke",
        "readiness-train",
        "readiness-validate",
        "readiness-reload",
        "readiness-evaluate",
        "readiness-analyze",
    )
    formal_arguments = (
        ("--formal",),
        ("--authorization-token", "invented"),
        ("--preflight-root", str(tmp_path)),
        ("--alignment-disposition", "ALIGNED"),
        ("--aligned-implementation-commit", TEST_SOURCE_COMMIT),
        ("--alignment-stage-commit", "4" * 40),
    )
    for stage in stages:
        for index, extra in enumerate(formal_arguments):
            root = tmp_path / f"{stage}_{index}"
            monkeypatch.setattr(
                sys,
                "argv",
                [str(RUNNER_PATH), stage, "--run-root", str(root), *extra],
            )
            with pytest.raises(
                ValueError, match="only for train"
            ):
                runner.main()
            assert not root.exists()
    for index, extra in enumerate(formal_arguments[1:]):
        root = tmp_path / f"nonformal_train_{index}"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                str(RUNNER_PATH),
                "train",
                "--run-root",
                str(root),
                "--source-commit",
                TEST_SOURCE_COMMIT,
                *extra,
            ],
        )
        with pytest.raises(ValueError, match="nonformal train forbids"):
            runner.main()
        assert not root.exists()
    assert dispatched is False

    captured: dict[str, object] = {}

    def capture_formal_train(**arguments: object) -> dict[str, object]:
        captured.update(arguments)
        return {}

    monkeypatch.setattr(runner, "train", capture_formal_train)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER_PATH),
            "train",
            "--run-root",
            str(tmp_path / "formal_train"),
            "--source-commit",
            runner.FORMAL_SOURCE_COMMIT,
            "--formal",
            "--authorization-token",
            runner.AUTHORIZATION_TOKEN,
            "--preflight-root",
            str(tmp_path / "preflight"),
            "--alignment-disposition",
            runner.ALIGNMENT_DISPOSITION,
            "--aligned-implementation-commit",
            runner.ALIGNED_IMPLEMENTATION_COMMIT,
            "--alignment-stage-commit",
            runner.ALIGNMENT_STAGE_COMMIT,
        ],
    )
    runner.main()
    assert captured["formal"] is True
    assert captured["authorization_token"] == runner.AUTHORIZATION_TOKEN
    assert captured["aligned_implementation_commit"] == (
        runner.ALIGNED_IMPLEMENTATION_COMMIT
    )


def test_stale_root_rejects_before_witness_materialization(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "stale"
    root.mkdir()
    (root / "owned.txt").write_text("preserve\n", encoding="utf-8")
    called = False

    def forbidden_materialization(**_arguments: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("G51 materialized before fresh-root admission")

    monkeypatch.setattr(
        runner, "_materialize_source_bundle", forbidden_materialization
    )
    with pytest.raises(ValueError, match="absent or empty"):
        runner.train(
            run_root=root,
            source_commit=TEST_SOURCE_COMMIT,
            formal=False,
            authorization_token=None,
        )
    assert called is False
    assert (root / "owned.txt").read_text(encoding="utf-8") == "preserve\n"


def test_formal_gate_binds_preflight_before_root_and_model_materialization(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    preflight_root = tmp_path / "preflight"
    formal_root = tmp_path / "formal"
    monkeypatch.setattr(runner, "PREFLIGHT_ROOT", preflight_root)
    monkeypatch.setattr(runner, "FORMAL_RUN_ROOT", formal_root)
    calls: list[str] = []
    preflight_digests = {
        "preflight_source_commit": runner.FORMAL_SOURCE_COMMIT,
        "preflight_train_manifest_sha256": "1" * 64,
        "preflight_evaluation_manifest_sha256": "2" * 64,
        "preflight_analysis_result_sha256": "3" * 64,
    }

    def validate_preflight(root: Path) -> dict[str, str]:
        calls.append("preflight")
        assert root == preflight_root
        assert not formal_root.exists()
        return dict(preflight_digests)

    def fresh_root(root: Path) -> Path:
        calls.append("root")
        root.mkdir()
        return root

    def materialize(**arguments: object) -> tuple[object, object, object]:
        calls.append("model")
        assert arguments["formal"] is True
        return object(), object(), object()

    captured: dict[str, object] = {}

    def write_training(**arguments: object) -> dict[str, object]:
        calls.append("write")
        captured.update(arguments)
        return {"result_branch": runner.INVALID_BRANCH}

    monkeypatch.setattr(runner, "_validate_preflight", validate_preflight)
    monkeypatch.setattr(runner, "_fresh_root", fresh_root)
    monkeypatch.setattr(runner, "_native_backend_identity", lambda: {})
    monkeypatch.setattr(runner, "_materialize_source_bundle", materialize)
    monkeypatch.setattr(runner, "_write_training_assessment", write_training)
    monkeypatch.setattr(
        runner, "validate_training_artifacts", lambda *_args, **_kwargs: {}
    )
    result = runner.train(
        run_root=formal_root,
        source_commit=runner.FORMAL_SOURCE_COMMIT,
        formal=True,
        authorization_token=runner.AUTHORIZATION_TOKEN,
        preflight_root=preflight_root,
        alignment_disposition=runner.ALIGNMENT_DISPOSITION,
        aligned_implementation_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
        alignment_stage_commit=runner.ALIGNMENT_STAGE_COMMIT,
    )
    assert result["result_branch"] == runner.INVALID_BRANCH
    assert calls == ["preflight", "root", "model", "write"]
    assert captured["formal"] is True
    assert captured["formal_authority"] == {
        "authorization_token_id": runner.AUTHORIZATION_TOKEN,
        "aligned_implementation_commit": runner.ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": runner.ALIGNMENT_STAGE_COMMIT,
        "alignment_disposition": runner.ALIGNMENT_DISPOSITION,
        **preflight_digests,
    }


def test_frozen_first_match_order_and_tokens_are_exact(runner) -> None:
    assert runner.FIRST_MATCH_ORDER == (
        "INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51",
        "UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51",
        "PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51",
        "NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51",
    )
    assert tuple(runner.source.RESULT_BRANCHES) == runner.FIRST_MATCH_ORDER
    base = {
        "operational_valid": True,
        "coupling_localized": False,
        "static_dependency_certificate": True,
        "per_parameter_Adam_factorization": True,
        "D_G51": 0,
        "numerical_witness_invoked": True,
        "numerical_witness_all_zero": True,
    }
    assert runner.select_g51_result_branch(base) == runner.REMOVABLE_BRANCH
    invalid = copy.deepcopy(base)
    invalid["operational_valid"] = False
    invalid["coupling_localized"] = True
    assert runner.select_g51_result_branch(invalid) == runner.INVALID_BRANCH
    coupling = copy.deepcopy(base)
    coupling["coupling_localized"] = True
    coupling["D_G51"] = 1
    assert runner.select_g51_result_branch(coupling) == runner.COUPLING_BRANCH
    unresolved = copy.deepcopy(base)
    unresolved["numerical_witness_all_zero"] = False
    assert runner.select_g51_result_branch(unresolved) == runner.UNRESOLVED_BRANCH
    static_only = copy.deepcopy(base)
    static_only["numerical_witness_invoked"] = False
    static_only["numerical_witness_all_zero"] = False
    assert runner.select_g51_result_branch(static_only) == runner.UNRESOLVED_BRANCH


@pytest.mark.parametrize("branch", runner_module.FIRST_MATCH_ORDER)
def test_preflight_admission_accepts_every_registered_branch_without_a_favorable_gate(
    runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    branch: str,
) -> None:
    root = tmp_path / branch
    root.mkdir()
    for name in (
        runner.TRAIN_MANIFEST,
        runner.EVALUATION_MANIFEST,
        runner.ANALYSIS_RESULT,
    ):
        (root / name).write_text(
            json.dumps({"formal": False, "branch": branch}) + "\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(
        runner,
        "validate_training_artifacts",
        lambda *_args, **_kwargs: {
            "formal": False,
            "source_commit": runner.FORMAL_SOURCE_COMMIT,
            "result_branch": branch,
        },
    )
    monkeypatch.setattr(
        runner,
        "validate_evaluation_artifacts",
        lambda *_args, **_kwargs: {
            "formal": False,
            "source_commit": runner.FORMAL_SOURCE_COMMIT,
        },
    )
    monkeypatch.setattr(
        runner,
        "validate_analysis_artifacts",
        lambda *_args, **_kwargs: {
            "formal": False,
            "source_commit": runner.FORMAL_SOURCE_COMMIT,
        },
    )
    inventory_call: dict[str, object] = {}

    def capture_inventory(
        checked_root: Path, *, result_branch: str, terminal: bool
    ) -> None:
        inventory_call.update(
            root=checked_root, result_branch=result_branch, terminal=terminal
        )

    monkeypatch.setattr(runner, "_validate_branch_inventory", capture_inventory)
    digests = runner._validate_preflight(root)
    assert inventory_call == {
        "root": root.resolve(),
        "result_branch": branch,
        "terminal": True,
    }
    assert digests["preflight_source_commit"] == runner.FORMAL_SOURCE_COMMIT
    assert all(
        len(value) == 64
        for key, value in digests.items()
        if key.endswith("sha256")
    )


def test_formal_evaluate_and_analyze_infer_and_propagate_manifest_scope(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "formal_adverse"
    root.mkdir()
    (root / runner.TRAIN_MANIFEST).write_text("{}\n", encoding="utf-8")
    training = {
        "source_commit": runner.FORMAL_SOURCE_COMMIT,
        "formal": True,
        "result_branch": runner.INVALID_BRANCH,
        "result_assessment": {
            "path": runner.ASSESSMENT_REFERENCE,
            "sha256": "a" * 64,
            "result": runner.INVALID_BRANCH,
        },
        "checkpoint_inventory": {},
        "configuration": {"numerical_witness_invoked": True},
        "static_certificate": None,
        "structural_witness": None,
    }
    assessment = {
        "result_envelope": {
            "result": runner.INVALID_BRANCH,
            "D_G51": None,
            "evidence": {},
        }
    }
    monkeypatch.setattr(
        runner,
        "validate_training_artifacts",
        lambda *_args, **_kwargs: training,
    )
    monkeypatch.setattr(runner, "_load_checkpoint", lambda _path: assessment)
    monkeypatch.setattr(
        runner,
        "_result_assessment",
        lambda _root, _training: assessment,
    )
    monkeypatch.setattr(
        runner.source,
        "classify_result",
        lambda _evidence: runner.INVALID_BRANCH,
    )
    monkeypatch.setattr(
        runner, "_validate_branch_inventory", lambda *_args, **_kwargs: None
    )
    evaluation = runner.evaluate(run_root=root)
    analysis = runner.analyze(run_root=root)
    assert evaluation["formal"] is True
    assert evaluation["checkpoint_sha256"] == {}
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["environment_transitions"] == 0
    assert analysis["formal"] is True
    assert analysis["train_manifest_sha256"] == runner._artifact_digest(
        root / runner.TRAIN_MANIFEST
    )
    assert analysis["evaluation_manifest_sha256"] == runner._artifact_digest(
        root / runner.EVALUATION_MANIFEST
    )
    assert analysis["result_branch"] == runner.INVALID_BRANCH
    (root / runner.TRAIN_MANIFEST).write_text(
        '{"tampered":true}\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="evaluation artifact invariant mismatch"):
        runner.validate_evaluation_artifacts(root)


def test_readiness_lifecycle_is_exact_reloadable_and_zero_additional_science(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    root, training, evaluation, analysis = readiness_bundle
    assert training["passed"] is True
    assert training["formal"] is False
    assert training["formal_statistical_run"] is False
    assert training["scientific_iteration_cost"] == 0
    assert training["configuration"]["real_transitions"] == 384
    assert training["configuration"]["total_optimizer_steps"] == 4
    assert training["native_backend"] == runner._native_backend_identity()
    assert training["seed_block"] == runner.source.seed_block(0, formal=False)
    assert training["execution_readiness_proof_only"] is True
    assert training["two_process_proof"]["worker_count"] == 2
    assert training["two_process_proof"]["distinct_processes"] is True
    assert training["two_process_proof"]["single_thread_workers"] is True
    assert training["two_process_proof"]["semantic_payload_equal"] is True
    assert training["two_process_proof"]["scientific_real_transitions"] == 0
    assert training["two_process_proof"]["optimizer_steps"] == 0
    assert training["two_process_proof_sha256"] == runner._artifact_digest(
        root / runner.TWO_PROCESS_REPORT_REFERENCE
    )
    assert tuple(training["checkpoint_inventory"]) == runner.source.ARMS
    assert all(
        row["kind"] == "final_only_proof_witness"
        for row in training["checkpoint_inventory"].values()
    )
    assert evaluation["passed"] is True
    assert evaluation["D_G51"] == 0
    assert evaluation["canonical_final_checkpoint_projection_equal"] is True
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["environment_transitions"] == 0
    assert evaluation["checkpoint_sha256"] == {
        arm: training["checkpoint_inventory"][arm]["sha256"]
        for arm in runner.source.ARMS
    }
    assert analysis["result_branch"] == runner.REMOVABLE_BRANCH
    assert analysis["first_match_order"] == list(runner.FIRST_MATCH_ORDER)
    assert runner.readiness_validate(run_root=root)["passed"] is True
    assert runner.readiness_reload(run_root=root)["passed"] is True
    reloaded = runner.reload_artifacts(root)
    assert reloaded["training"]["source_commit"] == TEST_SOURCE_COMMIT
    assert reloaded["evaluation"]["D_G51"] == 0
    assert reloaded["analysis"]["result_branch"] == runner.REMOVABLE_BRANCH

    checkpoints = {
        arm: runner._load_checkpoint(runner._checkpoint_path(root, arm))
        for arm in runner.source.ARMS
    }
    assert runner.source.validate_checkpoint_pair(checkpoints)
    assert all(
        checkpoints[arm]["source"]["implementation_commit"]
        == training["source_commit"]
        for arm in runner.source.ARMS
    )
    assert runner._canonical_values_equal(
        runner.source.canonical_actor_projection(
            checkpoints[runner.source.REFERENCE_ARM]
        ),
        runner.source.canonical_actor_projection(
            checkpoints[runner.source.REDUCED_ARM]
        ),
    )
    reduced = checkpoints[runner.source.REDUCED_ARM]
    assert all(
        identity not in reduced for identity in ("algorithm_id", "source_id", "arm")
    )
    assert not _contains_baseline_identity(reduced)
    phase_B = training["structural_witness"]["phase_B_zero_step_certificate"]
    assert runner._strict_phase_B_zero_step_certificate(phase_B)
    assert phase_B["phase_B_optimizer_steps"] == 0
    assert all(phase_B["predicates"].values())
    assessment = runner._load_checkpoint(root / runner.ASSESSMENT_REFERENCE)
    assert assessment["result_envelope"]["result"] == runner.REMOVABLE_BRANCH
    assert assessment["passed"] is True
    assert assessment["static_certificate"]["path_identities"]["Adam_step"] == (
        runner._stable_Adam_step_identity()
    )


def test_interface_smoke_calls_real_static_boundary_without_trajectory(runner) -> None:
    smoke = runner.readiness_interface_smoke(source_commit=TEST_SOURCE_COMMIT)
    assert smoke["passed"] is True
    assert smoke["scientific_real_transitions"] == 0
    assert smoke["optimizer_steps"] == 0
    assert smoke["phase_A_boundary"]["passed"] is True
    assert smoke["native_backend"] == runner._native_backend_identity()
    assert runner.source.validate_static_certificate(
        runner._source_validation_view(smoke["static_certificate"])
    )
    assert smoke["static_certificate"]["path_identities"]["Adam_step"] == (
        runner._stable_Adam_step_identity()
    )
    assert smoke["interfaces"] == [
        "train",
        "evaluate",
        "analyze",
        "exercise",
        "readiness-smoke",
        "readiness-train",
        "readiness-validate",
        "readiness-reload",
        "readiness-evaluate",
        "readiness-analyze",
    ]


@pytest.mark.parametrize(
    ("branch", "completed_paired_passes"),
    (
        (runner_module.INVALID_BRANCH, 0),
        (runner_module.COUPLING_BRANCH, 0),
        (runner_module.UNRESOLVED_BRANCH, 1),
    ),
)
def test_source_assessed_adverse_lifecycles_are_terminal_and_zero_extra_work(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    branch: str,
    completed_paired_passes: int,
) -> None:
    exact_root, exact_training, _, _ = readiness_bundle
    static = exact_training["static_certificate"]
    assert isinstance(static, Mapping)
    trajectory = runner._load_shared_phase_A_trajectory(
        exact_root / runner.SHARED_TRAJECTORY_REFERENCE
    )
    failure = _synthetic_adverse_failure(
        runner, branch=branch, static=static
    )
    assessment = runner._adverse_assessment(
        source_commit=TEST_SOURCE_COMMIT,
        failure=failure,
    )
    assert runner._strict_structural_assessment(
        assessment, source_commit=TEST_SOURCE_COMMIT
    )
    assert assessment["result_envelope"]["result"] == branch

    def forbidden_materialization(**_arguments: object) -> object:
        raise AssertionError("terminal recording attempted new scientific work")

    monkeypatch.setattr(
        runner, "_materialize_source_bundle", forbidden_materialization
    )
    root = tmp_path / branch
    training = runner.record_terminal_assessment(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        assessment=assessment,
        trajectory=trajectory,
    )
    evaluation = runner.evaluate(run_root=root)
    analysis = runner.analyze(run_root=root)
    reloaded = runner.reload_artifacts(root)

    assert training["result_branch"] == branch
    assert training["passed"] is False
    assert training["operational_valid"] is True
    assert training["structural_witness"] is None
    assert training["checkpoint_inventory"] == {}
    assert training["checkpoint_selection"] is None
    assert training["execution_readiness_proof_only"] is False
    assert training["work_accounting"]["completed_paired_passes"] == (
        completed_paired_passes
    )
    assert training["configuration"]["total_optimizer_steps"] == (
        2 * completed_paired_passes
    )
    assert not (root / runner.CHECKPOINT_DIRECTORY).exists()
    assert evaluation["result_branch"] == branch
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["environment_transitions"] == 0
    assert evaluation["operational_valid"] is True
    assert evaluation["passed"] is False
    assert analysis["result_branch"] == branch
    assert analysis["operational_valid"] is True
    assert analysis["passed"] is False
    assert reloaded["training"]["result_branch"] == branch
    assert reloaded["evaluation"]["result_branch"] == branch
    assert reloaded["analysis"]["result_branch"] == branch
    assert runner._relative_file_inventory(root) == {
        runner.TRAIN_MANIFEST,
        runner.EVALUATION_MANIFEST,
        runner.ANALYSIS_RESULT,
        runner.SHARED_TRAJECTORY_REFERENCE,
        runner.ASSESSMENT_REFERENCE,
    }

    forbidden = root / runner.TWO_PROCESS_REPORT_REFERENCE
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact inventory mismatch"):
        runner.validate_training_artifacts(root)


def test_unknown_and_partial_step_failures_are_reraised_without_assessment(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    _, training, _, _ = readiness_bundle
    static = training["static_certificate"]
    assert isinstance(static, Mapping)
    unknown = runner.source.G51InvariantError(
        "unregistered_failure", {"static_certificate": static}
    )
    with pytest.raises(runner.source.G51InvariantError) as unknown_error:
        runner._adverse_assessment(
            source_commit=TEST_SOURCE_COMMIT, failure=unknown
        )
    assert unknown_error.value is unknown

    partial = runner.source.G51InvariantError(
        "phase_A_pre_step_semantic_coupling",
        {
            "pass_index": 0,
            "optimizer_ledger": runner.source._optimizer_ledger(
                paired_passes=1,
                failure_detected_before_current_pair=True,
            ),
            "static_certificate": static,
        },
    )
    with pytest.raises(runner.source.G51InvariantError) as partial_error:
        runner._adverse_assessment(
            source_commit=TEST_SOURCE_COMMIT, failure=partial
        )
    assert partial_error.value is partial


def test_zero_coupling_pre_step_numeric_difference_is_unresolved_with_zero_steps(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    exact_root, training, _, _ = readiness_bundle
    static = training["static_certificate"]
    assert isinstance(static, Mapping)
    failure = runner.source.G51InvariantError(
        "phase_A_pre_step_numeric_difference",
        {
            "pass_index": 0,
            "optimizer_ledger": runner.source._optimizer_ledger(
                paired_passes=0,
                failure_detected_before_current_pair=True,
            ),
            "static_certificate": static,
            "comparison": {
                "actor_assigned_gradient_bytes_equal": False,
                "policy_loss_bytes_equal": True,
                "teacher_logprob_bytes_equal": True,
                "teacher_pre_tanh_bytes_equal": True,
                "teacher_action_bytes_equal": True,
                "baseline_loss_gradient_into_actor_count": 0,
                "actor_loss_gradient_into_baseline_count": 0,
                "plan_RNG_unchanged": True,
            },
        },
    )
    assessment = runner._adverse_assessment(
        source_commit=TEST_SOURCE_COMMIT,
        failure=failure,
    )
    assert runner._strict_structural_assessment(
        assessment, source_commit=TEST_SOURCE_COMMIT
    )
    assert assessment["result_envelope"]["result"] == runner.UNRESOLVED_BRANCH
    assert assessment["result_envelope"]["evidence"].get(
        "semantic_coupling_detected"
    ) is not True
    assert assessment["optimizer_ledger"]["reference_actor_steps"] == 0
    assert assessment["optimizer_ledger"]["reduced_actor_steps"] == 0
    assert assessment["optimizer_ledger"]["completed_paired_passes"] == 0
    assert assessment["optimizer_ledger"][
        "failure_detected_before_current_pair"
    ] is True

    trajectory = runner._load_shared_phase_A_trajectory(
        exact_root / runner.SHARED_TRAJECTORY_REFERENCE
    )
    root = tmp_path / "pre_step_numeric_unresolved"
    terminal = runner.record_terminal_assessment(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        assessment=assessment,
        trajectory=trajectory,
    )
    evaluation = runner.evaluate(run_root=root)
    analysis = runner.analyze(run_root=root)
    assert terminal["work_accounting"]["completed_paired_passes"] == 0
    assert terminal["checkpoint_inventory"] == {}
    assert evaluation["result_branch"] == runner.UNRESOLVED_BRANCH
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["environment_transitions"] == 0
    assert analysis["result_branch"] == runner.UNRESOLVED_BRANCH
    assert analysis["passed"] is False


def test_recursive_artifact_and_checkpoint_tamper_guards_fail_closed(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = readiness_bundle
    outer_tampered = tmp_path / "outer_tampered"
    shutil.copytree(root, outer_tampered)
    manifest_path = outer_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["compatibility"] = None
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="train manifest schema mismatch"):
        runner.validate_training_artifacts(outer_tampered)

    nested_tampered = tmp_path / "nested_tampered"
    shutil.copytree(root, nested_tampered)
    manifest_path = nested_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["static_certificate"]["compatibility"] = False
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="source evidence/checkpoint validation failed"
    ):
        runner.validate_training_artifacts(nested_tampered)

    reduced_tampered = tmp_path / "reduced_tampered"
    shutil.copytree(root, reduced_tampered)
    checkpoint_path = runner._checkpoint_path(
        reduced_tampered, runner.source.REDUCED_ARM
    )
    checkpoint = runner._load_checkpoint(checkpoint_path)
    checkpoint["legacy"] = {
        "route": "phase_A_shadow_baseline_removed",
        "dummy": 0,
    }
    runner._save_checkpoint(checkpoint_path, checkpoint)
    manifest_path = reduced_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checkpoint_inventory"][runner.source.REDUCED_ARM]["sha256"] = (
        runner._artifact_digest(checkpoint_path)
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="source evidence/checkpoint validation failed"
    ):
        runner.validate_training_artifacts(reduced_tampered)

    source_nested_tampered = tmp_path / "source_nested_tampered"
    shutil.copytree(root, source_nested_tampered)
    checkpoint_path = runner._checkpoint_path(
        source_nested_tampered, runner.source.REDUCED_ARM
    )
    checkpoint = runner._load_checkpoint(checkpoint_path)
    checkpoint["source"]["innocuous_extra"] = None
    runner._save_checkpoint(checkpoint_path, checkpoint)
    manifest_path = source_nested_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checkpoint_inventory"][runner.source.REDUCED_ARM]["sha256"] = (
        runner._artifact_digest(checkpoint_path)
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="source evidence/checkpoint validation failed"
    ):
        runner.validate_training_artifacts(source_nested_tampered)

    boundary_nested_tampered = tmp_path / "boundary_nested_tampered"
    shutil.copytree(root, boundary_nested_tampered)
    checkpoint_path = runner._checkpoint_path(
        boundary_nested_tampered, runner.source.REDUCED_ARM
    )
    checkpoint = runner._load_checkpoint(checkpoint_path)
    checkpoint["phase_A_projection_evidence"]["innocuous_extra"] = None
    runner._save_checkpoint(checkpoint_path, checkpoint)
    manifest_path = boundary_nested_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checkpoint_inventory"][runner.source.REDUCED_ARM]["sha256"] = (
        runner._artifact_digest(checkpoint_path)
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="source evidence/checkpoint validation failed"
    ):
        runner.validate_training_artifacts(boundary_nested_tampered)

    commit_tampered = tmp_path / "checkpoint_commit_tampered"
    shutil.copytree(root, commit_tampered)
    manifest_path = commit_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for arm in runner.source.ARMS:
        checkpoint_path = runner._checkpoint_path(commit_tampered, arm)
        checkpoint = runner._load_checkpoint(checkpoint_path)
        checkpoint["source"]["implementation_commit"] = "6" * 40
        runner._save_checkpoint(checkpoint_path, checkpoint)
        manifest["checkpoint_inventory"][arm]["sha256"] = (
            runner._artifact_digest(checkpoint_path)
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="source evidence/checkpoint validation failed"
    ):
        runner.validate_training_artifacts(commit_tampered)

    backend_tampered = tmp_path / "backend_tampered"
    shutil.copytree(root, backend_tampered)
    manifest_path = backend_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["native_backend"]["build_identity"] = "0" * 20
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="train manifest invariant mismatch"):
        runner.validate_training_artifacts(backend_tampered)

    evaluation_tampered = tmp_path / "evaluation_tampered"
    shutil.copytree(root, evaluation_tampered)
    evaluation_path = evaluation_tampered / runner.EVALUATION_MANIFEST
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    evaluation["legacy"] = True
    evaluation_path.write_text(
        json.dumps(evaluation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="evaluation manifest schema mismatch"):
        runner.validate_evaluation_artifacts(evaluation_tampered)


def test_saved_shared_trajectory_type_shape_and_trace_are_reconstructed(
    runner,
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = readiness_bundle

    type_tampered = tmp_path / "trajectory_type_tampered"
    shutil.copytree(root, type_tampered)
    trajectory_path = type_tampered / runner.SHARED_TRAJECTORY_REFERENCE
    runner.torch.save({"not": "AnchoredRosterTrajectory"}, trajectory_path)
    manifest_path = type_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shared_phase_A_trajectory"]["sha256"] = runner._artifact_digest(
        trajectory_path
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="exact 8x48 type"):
        runner.validate_training_artifacts(type_tampered)

    shape_tampered = tmp_path / "trajectory_shape_tampered"
    shutil.copytree(root, shape_tampered)
    trajectory_path = shape_tampered / runner.SHARED_TRAJECTORY_REFERENCE
    trajectory = runner._load_shared_phase_A_trajectory(trajectory_path)
    trajectory.rewards = trajectory.rewards[:-1].clone()
    runner.torch.save(trajectory, trajectory_path)
    manifest_path = shape_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shared_phase_A_trajectory"]["sha256"] = runner._artifact_digest(
        trajectory_path
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="exact 8x48 type"):
        runner.validate_training_artifacts(shape_tampered)

    trace_tampered = tmp_path / "trajectory_trace_tampered"
    shutil.copytree(root, trace_tampered)
    trajectory_path = trace_tampered / runner.SHARED_TRAJECTORY_REFERENCE
    trajectory = runner._load_shared_phase_A_trajectory(trajectory_path)
    trajectory.rewards = trajectory.rewards.clone()
    trajectory.rewards[0, 0] += 1.0
    runner.torch.save(trajectory, trajectory_path)
    manifest_path = trace_tampered / runner.TRAIN_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shared_phase_A_trajectory"]["sha256"] = runner._artifact_digest(
        trajectory_path
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="source trace mismatch"):
        runner.validate_training_artifacts(trace_tampered)


def test_two_process_attestation_is_dedicated_spawn_and_not_a_second_witness(
    runner,
) -> None:
    implementation = inspect.getsource(runner._run_distinct_proof_workers)
    assert 'multiprocessing.get_context("spawn")' in implementation
    assert "context.Process(" in implementation
    assert "ready_event.wait(timeout=60.0)" in implementation
    assert "release_event.set()" in implementation
    assert "len(set(pids)) != 2" in implementation
    worker = inspect.getsource(runner._proof_reload_worker)
    assert "optimize_phase_A_update" not in worker
    assert "collect_g40_trajectory" not in worker
    assert "validate_training_artifacts" in worker


def test_g51_import_leaves_g50_identity_unchanged(runner) -> None:
    assert runner.source.g50.ALGORITHM_ID == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
    )
    assert runner.source.g50.ARMS == (
        "FAST_ANCHOR_THEN_SINGLE_IMMEDIATE",
        "SINGLE_IMMEDIATE_FROM_INITIALIZATION",
    )
    assert runner.g50_runner.ALGORITHM_ID == runner.source.g50.ALGORITHM_ID
