from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_run_manifest import (
    HMAC_DOMAINS,
    build_prospective_activity_manifest,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_gate import (
    ActivityGateError,
    FoundationActivityGate,
    command_contract,
    technical_authorization_fixture,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_evidence import (
    EXACT_TEST_COMMAND,
    ActivityEvidenceError,
    build_complete_activity_evidence,
    build_s3_acceptance,
    build_source_manifest,
    canonical_json_bytes,
    manifest_digest,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.barriers import StageBarrier


ROOT = Path(__file__).resolve().parents[4]


def test_prospective_manifest_binds_exact_domain_roster_counts_and_no_identity() -> None:
    manifest = build_prospective_activity_manifest(code_sha256="a" * 64)

    assert HMAC_DOMAINS == (
        "foundation/initialization",
        "foundation/training",
        "foundation/competence",
        "opportunity/states",
        "opportunity/actions",
        "opportunity/tapes",
        "adapter/initialization",
        "adapter/training",
        "final/evaluation",
        "event/order",
        "switch/time",
        "disturbances",
        "action/uniforms",
        "minibatch/permutations",
    )
    assert manifest["status"] == "PROSPECTIVE_CREATE_ONLY_UNISSUED"
    assert manifest["create_only"] is True
    assert manifest["master_present"] is False
    assert manifest["registered_identity_present"] is False
    assert manifest["activity_authorized"] is False
    assert manifest["operator_now"] is False
    assert manifest["effect_refs"] == []
    assert len(manifest["replicate_roster"]) == 24
    assert manifest["replicate_roster"][0]["prospective_namespace"].endswith("/00000000")
    assert manifest["replicate_roster"][-1]["prospective_namespace"].endswith("/00000017")
    assert len(manifest["terminal_slots"]) == 24
    assert all(slot["update_index"] == 192 for slot in manifest["terminal_slots"])
    assert all(slot["materialized"] is False for slot in manifest["terminal_slots"])
    assert all(slot["eligible"] is False for slot in manifest["terminal_slots"])
    assert manifest["counts"] == {
        "replicates": 24,
        "updates_per_foundation": 192,
        "episodes_per_update": 16,
        "structural_steps_per_update": 16,
        "episodes_per_foundation": 3_072,
        "steps_per_foundation": 3_072,
        "total_foundation_episodes": 73_728,
        "total_foundation_steps": 73_728,
        "terminal_slots": 24,
    }


def test_command_contract_and_activity_gate_fail_closed_before_contact() -> None:
    contract = command_contract()
    gate = FoundationActivityGate()
    fixture = technical_authorization_fixture(
        manifest_sha256="b" * 64,
        code_sha256="a" * 64,
    )
    exact_options = {
        "--run-manifest": "future.json",
        "--code-sha256": "a" * 64,
        "--output-root": fixture["output_root"],
    }

    assert contract.required_options == (
        "--run-manifest",
        "--code-sha256",
        "--output-root",
    )
    assert contract.forbidden_options == (
        "--replicate",
        "--seed",
        "--threshold",
        "--stopping",
        "--retry",
        "--tuning",
        "--reward-inspection",
        "--partial-result",
    )
    with pytest.raises(ActivityGateError, match="command options"):
        gate.preflight(
            manifest=None,
            observed_manifest_sha256="b" * 64,
            expected_manifest_sha256="b" * 64,
            observed_code_sha256="a" * 64,
            expected_code_sha256="a" * 64,
            output_root=fixture["output_root"],
            output_root_exists=False,
            options={"--seed": "1"},
        )
    with pytest.raises(ActivityGateError, match="later immutable run manifest"):
        gate.preflight(
            manifest=None,
            observed_manifest_sha256="b" * 64,
            expected_manifest_sha256="b" * 64,
            observed_code_sha256="a" * 64,
            expected_code_sha256="a" * 64,
            output_root=fixture["output_root"],
            output_root_exists=False,
            options=exact_options,
        )
    with pytest.raises(ActivityGateError, match="code SHA"):
        gate.preflight(
            manifest=fixture,
            observed_manifest_sha256="b" * 64,
            expected_manifest_sha256="b" * 64,
            observed_code_sha256="c" * 64,
            expected_code_sha256="a" * 64,
            output_root=fixture["output_root"],
            output_root_exists=False,
            options=exact_options,
        )
    with pytest.raises(ActivityGateError, match="create-only output root"):
        gate.preflight(
            manifest=fixture,
            observed_manifest_sha256="b" * 64,
            expected_manifest_sha256="b" * 64,
            observed_code_sha256="a" * 64,
            expected_code_sha256="a" * 64,
            output_root=fixture["output_root"],
            output_root_exists=True,
            options=exact_options,
        )
    with pytest.raises(ActivityGateError, match="cannot self-release"):
        gate.preflight(
            manifest=fixture,
            observed_manifest_sha256="b" * 64,
            expected_manifest_sha256="b" * 64,
            observed_code_sha256="a" * 64,
            expected_code_sha256="a" * 64,
            output_root=fixture["output_root"],
            output_root_exists=False,
            options=exact_options,
        )


def test_complete_only_evidence_binds_chain_and_rejects_every_artifact() -> None:
    source = build_source_manifest(ROOT)
    prospective = build_prospective_activity_manifest(
        code_sha256=manifest_digest(source)
    )
    evidence = build_complete_activity_evidence(
        repository_root=ROOT,
        source_manifest=source,
        prospective_manifest=prospective,
        observed_artifact_paths=(),
    )

    assert len(source["files"]) == 4
    assert len(evidence["accepted_chain_refs"]) == 7
    assert evidence["complete"] is True
    assert evidence["prospective_manifest_status"] == "PROSPECTIVE_CREATE_ONLY_UNISSUED"
    assert evidence["observed_artifact_paths"] == []
    assert evidence["hard_downstream_absence"] is True
    assert evidence["registered_identity_present"] is False
    assert evidence["eligible_artifact_present"] is False
    assert evidence["question_relevant_value_visible"] is False
    assert evidence["activity_authorized"] is False
    assert evidence["operator_now"] is False
    assert evidence["effect_refs"] == []

    incomplete = deepcopy(prospective)
    incomplete["terminal_slots"] = incomplete["terminal_slots"][:-1]
    with pytest.raises(ActivityEvidenceError, match="24 terminal slots"):
        build_complete_activity_evidence(
            repository_root=ROOT,
            source_manifest=source,
            prospective_manifest=incomplete,
            observed_artifact_paths=(),
        )
    with pytest.raises(ActivityEvidenceError, match="artifact path"):
        build_complete_activity_evidence(
            repository_root=ROOT,
            source_manifest=source,
            prospective_manifest=prospective,
            observed_artifact_paths=("checkpoint.bin",),
        )


def test_s3_acceptance_binds_exact_estimate_and_portfolio_boundary() -> None:
    source = build_source_manifest(ROOT)
    prospective = build_prospective_activity_manifest(code_sha256=manifest_digest(source))
    evidence = build_complete_activity_evidence(
        repository_root=ROOT,
        source_manifest=source,
        prospective_manifest=prospective,
        observed_artifact_paths=(),
    )
    acceptance = build_s3_acceptance(
        repository_root=ROOT,
        source_manifest=source,
        prospective_manifest=prospective,
        evidence_manifest=evidence,
        measurements={
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "peak_tracemalloc_bytes": 4,
            "read_bytes": 5,
            "write_bytes": 6,
            "storage_bytes": 7,
        },
        verification_sha256="c" * 64,
    )

    StageBarrier.s0().validate_payload(acceptance)
    assert acceptance["schema"] == "SCDMP_NATIVE_FUSION_R01_S3_TECHNICAL_ACCEPTANCE"
    assert acceptance["verification_command"] == EXACT_TEST_COMMAND
    assert acceptance["accepted_construction_estimate"] == {
        "low": {
            "engineering_hours": 16,
            "cpu_core_hours": 1,
            "wall_seconds": 120,
            "peak_memory_mib": 1024,
            "storage_mib": 50,
        },
        "central": {
            "engineering_hours": 28,
            "cpu_core_hours": 2,
            "wall_seconds": 300,
            "peak_memory_mib": 2048,
            "storage_mib": 100,
        },
        "high": {
            "engineering_hours": 48,
            "cpu_core_hours": 4,
            "wall_seconds": 600,
            "peak_memory_mib": 4096,
            "storage_mib": 200,
        },
    }
    assert acceptance["next_conditional_boundary"]["kind"] == (
        "PORTFOLIO_RECONCILE_FOUNDATION_ACTIVITY"
    )
    assert acceptance["firewall"] == {
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }
    assert canonical_json_bytes(acceptance).endswith(b"\n")
