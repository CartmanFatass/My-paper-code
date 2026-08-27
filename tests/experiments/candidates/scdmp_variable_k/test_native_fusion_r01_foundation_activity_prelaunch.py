from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_production import (
    FoundationActivityProduction,
    PrelaunchRefusal,
    parse_production_inputs,
    technical_run_manifest_fixture,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_resource_estimate import (
    ActivityPrimitiveMeasurements,
    MeasuredPrimitive,
    project_activity_estimate,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_validation import (
    EXACT_TEST_COMMAND,
    ESTIMATOR_HELP_COMMAND,
    ESTIMATOR_OUTPUT_COMMAND,
    ActivityValidationError,
    build_complete_prelaunch_evidence,
    build_s4_acceptance,
    build_source_manifest,
    manifest_digest,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_run_manifest import (
    HMAC_DOMAINS,
    PROSPECTIVE_OUTPUT_ROOT,
    S4_RUN_MANIFEST_PATH,
    build_prelaunch_manifest,
    build_production_argv,
)


ROOT = Path(__file__).resolve().parents[4]


def test_prelaunch_contract_binds_exact_full_foundation_payload_without_release() -> None:
    code_sha256 = "a" * 64
    estimate_sha256 = "b" * 64
    argv = build_production_argv(code_sha256=code_sha256)
    manifest = build_prelaunch_manifest(
        code_sha256=code_sha256,
        activity_estimate_sha256=estimate_sha256,
    )

    assert argv == (
        "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
        "-m",
        (
            "experiments.candidates.scdmp_variable_k.native_fusion_r01."
            "foundation_activity_production"
        ),
        "--run-manifest",
        S4_RUN_MANIFEST_PATH,
        "--code-sha256",
        code_sha256,
        "--output-root",
        PROSPECTIVE_OUTPUT_ROOT,
    )
    assert manifest["schema"] == (
        "SCDMP_NATIVE_FUSION_R01_S4_FOUNDATION_ACTIVITY_PRELAUNCH_V1"
    )
    assert manifest["canonical_parameters"] == {
        "replicates": 24,
        "updates_per_foundation": 192,
        "episodes_per_update": 16,
        "adamw_steps_per_update": 16,
        "episodes_per_foundation": 3_072,
        "adamw_steps_per_foundation": 3_072,
        "total_episodes": 73_728,
        "total_allocated_primitive_slots": 30_965_760,
        "total_maximum_policy_queries": 5_419_008,
        "total_adamw_steps": 73_728,
        "final_checkpoint_slots": 24,
        "k_balance_per_update": {"4": 8, "10": 8},
        "order_balance_per_k_update": {"GR": 4, "RG": 4},
    }
    assert manifest["hmac_sha256_domains"] == list(HMAC_DOMAINS)
    assert manifest["payload_argv"] == list(argv)
    assert manifest["output_effect_template"] == {
        "kind": "LOCAL_RESULT_ROOT",
        "resource_id": PROSPECTIVE_OUTPUT_ROOT,
        "operation": "CREATE_ONLY",
    }
    assert manifest["run_manifest_contract"]["required_status"] == (
        "AUTHORIZED_IMMUTABLE"
    )
    assert manifest["run_manifest_contract"]["required_effect_count"] == 1
    assert manifest["result_responsive_options"] == []
    assert manifest["registered_identity_present"] is False
    assert manifest["eligible_artifact_present"] is False
    assert manifest["question_relevant_value_visible"] is False
    assert manifest["activity_authorized"] is False
    assert manifest["operator_now"] is False
    assert manifest["effect_refs"] == []


def test_production_surface_has_only_three_inputs_and_fails_before_contact() -> None:
    code_sha256 = "a" * 64
    manifest_sha256 = "b" * 64
    argv = (
        "--run-manifest",
        S4_RUN_MANIFEST_PATH,
        "--code-sha256",
        code_sha256,
        "--output-root",
        PROSPECTIVE_OUTPUT_ROOT,
    )
    inputs = parse_production_inputs(argv)
    assert inputs.run_manifest == S4_RUN_MANIFEST_PATH
    assert inputs.code_sha256 == code_sha256
    assert inputs.output_root == PROSPECTIVE_OUTPUT_ROOT

    for forbidden in (
        "--replicate",
        "--seed",
        "--threshold",
        "--stopping",
        "--retry",
        "--tuning",
        "--reward-inspection",
        "--partial-result",
    ):
        with pytest.raises(PrelaunchRefusal, match="exact production argv"):
            parse_production_inputs((*argv, forbidden, "1"))

    fixture = technical_run_manifest_fixture(
        manifest_sha256=manifest_sha256,
        code_sha256=code_sha256,
    )
    contacted: list[object] = []
    runner = FoundationActivityProduction()
    with pytest.raises(PrelaunchRefusal, match="nonregistered fixture"):
        runner.launch(
            inputs=inputs,
            manifest=fixture,
            observed_manifest_sha256=manifest_sha256,
            expected_manifest_sha256=manifest_sha256,
            output_root_exists=False,
            activity_executor=contacted.append,
        )
    assert contacted == []

    externally_bound_fixture = deepcopy(fixture)
    externally_bound_fixture.pop("manifest_sha256")
    with pytest.raises(PrelaunchRefusal, match="nonregistered fixture"):
        runner.launch(
            inputs=inputs,
            manifest=externally_bound_fixture,
            observed_manifest_sha256=manifest_sha256,
            expected_manifest_sha256=manifest_sha256,
            output_root_exists=False,
            activity_executor=contacted.append,
        )
    assert contacted == []

    with pytest.raises(PrelaunchRefusal, match="create-only output root"):
        runner.launch(
            inputs=inputs,
            manifest=fixture,
            observed_manifest_sha256=manifest_sha256,
            expected_manifest_sha256=manifest_sha256,
            output_root_exists=True,
            activity_executor=contacted.append,
        )
    assert contacted == []


def test_resource_projection_scales_all_measured_primitives_and_classifies_runtime() -> None:
    measured = ActivityPrimitiveMeasurements(
        allocated_slot=MeasuredPrimitive(
            repetitions=7,
            units_per_repetition=1_024,
            wall_seconds_per_unit=0.000_020,
            cpu_seconds_per_unit=0.000_019,
        ),
        policy_query=MeasuredPrimitive(
            repetitions=7,
            units_per_repetition=512,
            wall_seconds_per_unit=0.000_040,
            cpu_seconds_per_unit=0.000_038,
        ),
        adamw_step=MeasuredPrimitive(
            repetitions=7,
            units_per_repetition=1,
            wall_seconds_per_unit=0.001,
            cpu_seconds_per_unit=0.0009,
        ),
        baseline_peak_rss_bytes=100_000_000,
        one_update_scratch_bytes=500_000,
        one_checkpoint_retained_bytes=250_000,
        one_checkpoint_io_bytes=500_000,
    )
    estimate = project_activity_estimate(measured)

    measured_wall = (
        30_965_760 * 0.000_020
        + 5_419_008 * 0.000_040
        + 73_728 * 0.001
    )
    measured_cpu = (
        30_965_760 * 0.000_019
        + 5_419_008 * 0.000_038
        + 73_728 * 0.0009
    )
    assert estimate["workload"]["total_allocated_primitive_slots"] == 30_965_760
    assert estimate["workload"]["total_maximum_policy_queries"] == 5_419_008
    assert estimate["workload"]["total_adamw_steps"] == 73_728
    assert estimate["estimates"]["low"]["wall_seconds"] == pytest.approx(
        measured_wall
    )
    assert estimate["estimates"]["central"]["wall_seconds"] == pytest.approx(
        2 * measured_wall
    )
    assert estimate["estimates"]["high"]["wall_seconds"] == pytest.approx(
        4 * measured_wall
    )
    assert estimate["estimates"]["low"]["cpu_core_seconds"] == pytest.approx(
        measured_cpu
    )
    assert estimate["runtime_classification"] == "<=7200"
    assert estimate["performance_reasonableness_review_required"] is False
    assert estimate["explicit_user_approval_required_before_activity"] is False
    assert estimate["device_limits"] == {
        "workers": 1,
        "cpu_threads": 1,
        "accelerators": 0,
        "foundations_concurrent": 1,
    }
    assert estimate["unsafe_memory_plan"] is False
    assert estimate["registered_identity_present"] is False
    assert estimate["question_relevant_value_visible"] is False
    assert estimate["activity_authorized"] is False
    assert estimate["operator_now"] is False
    assert estimate["effect_refs"] == []


def test_complete_s4_acceptance_binds_chain_estimate_commands_and_no_activity() -> None:
    source = build_source_manifest(ROOT)
    measured = ActivityPrimitiveMeasurements(
        allocated_slot=MeasuredPrimitive(7, 1_024, 0.000_020, 0.000_019),
        policy_query=MeasuredPrimitive(7, 512, 0.000_040, 0.000_038),
        adamw_step=MeasuredPrimitive(7, 1, 0.001, 0.0009),
        baseline_peak_rss_bytes=100_000_000,
        one_update_scratch_bytes=500_000,
        one_checkpoint_retained_bytes=250_000,
        one_checkpoint_io_bytes=500_000,
    )
    estimate = project_activity_estimate(measured)
    estimate["implementation_refs"] = deepcopy(source["files"])
    estimate["runtime"] = {
        "workers": 1,
        "torch_threads": 1,
        "accelerators": 0,
    }
    prelaunch = build_prelaunch_manifest(
        code_sha256=manifest_digest(source),
        activity_estimate_sha256=manifest_digest(estimate),
    )
    evidence = build_complete_prelaunch_evidence(
        repository_root=ROOT,
        source_manifest=source,
        estimate=estimate,
        prelaunch_manifest=prelaunch,
        observed_activity_paths=(),
    )
    command_measurements = {
        "focused_pytest": {
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "read_bytes": 4,
            "write_bytes": 5,
        },
        "estimator_help": {
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "read_bytes": 4,
            "write_bytes": 5,
        },
        "estimator_output": {
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "read_bytes": 4,
            "write_bytes": 5,
        },
        "storage_bytes": 6,
    }
    command_refs = {
        "focused_pytest": "c" * 64,
        "estimator_help": "d" * 64,
        "estimator_output": "e" * 64,
    }
    acceptance = build_s4_acceptance(
        repository_root=ROOT,
        source_manifest=source,
        estimate=estimate,
        prelaunch_manifest=prelaunch,
        evidence=evidence,
        command_measurements=command_measurements,
        command_ref_sha256=command_refs,
    )

    assert evidence["complete"] is True
    assert len(evidence["accepted_chain_refs"]) == 8
    assert evidence["observed_activity_paths"] == []
    assert acceptance["schema"] == (
        "SCDMP_NATIVE_FUSION_R01_S4_TECHNICAL_ACCEPTANCE_V1"
    )
    assert acceptance["accepted"] is True
    assert acceptance["technical_commands"] == {
        "focused_pytest": EXACT_TEST_COMMAND,
        "estimator_help": ESTIMATOR_HELP_COMMAND,
        "estimator_output": ESTIMATOR_OUTPUT_COMMAND,
    }
    assert acceptance["runtime_classification"] == "<=7200"
    assert acceptance["next_portfolio_boundary"][
        "performance_reasonableness_review_required"
    ] is False
    assert acceptance["next_portfolio_boundary"][
        "explicit_user_approval_required_before_activity"
    ] is False
    assert acceptance["firewall"] == {
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }

    with pytest.raises(ActivityValidationError, match="activity path"):
        build_complete_prelaunch_evidence(
            repository_root=ROOT,
            source_manifest=source,
            estimate=estimate,
            prelaunch_manifest=prelaunch,
            observed_activity_paths=("checkpoint.pt",),
        )
