from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import numpy as np

from ha_ctse_process import uav_episode_serialization as episode_serialization
from ha_ctse_process import uav_episode_schema as episode_schema
from ha_ctse_process import uav_g0_geometry as geometry
from ha_ctse_process import uav_g0_environment as g0_environment
from ha_ctse_process import uav_g0_oracle_evidence as oracle_evidence
from ha_ctse_process import uav_g0_statistics as statistics
from ha_ctse_process import uav_source_identifiability_g0 as source
from scripts import run_uav_source_identifiability_g0 as runner


SOURCE_COMMIT = "fdc76381176a40c306a327c6edd1357a828cf466"
DESIGN_ROUND = "20260730_uav_g0_executable_contract_addendum_v2"
DESIGN_STAGE_COMMIT = "8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc"
DESIGN_ARCHIVE_COMMIT = "9c1566e1c6adefcd500facb1bb50d5a7428eae9c"
DESIGN_DISPOSITION = (
    "G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT"
)


def test_episode_serialization_import_is_source_independent() -> None:
    assert episode_serialization.schema is episode_schema
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            "from ha_ctse_process import uav_episode_serialization as codec; "
            "assert codec.schema.__name__ == 'ha_ctse_process.uav_episode_schema'; "
            "assert 'ha_ctse_process.uav_source_identifiability_g0' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_runner_imports_environment_true_owner() -> None:
    assert runner.g0_environment is g0_environment
    assert not hasattr(source, "UAVSourceIdentifiabilityEnv")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _store(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _complete_readiness(root: Path) -> None:
    runner.readiness_train(run_root=root, source_commit=SOURCE_COMMIT)
    runner.readiness_validate(run_root=root)
    runner.readiness_reload(run_root=root)
    runner.readiness_evaluate(run_root=root)
    runner.readiness_analyze(run_root=root)


def test_readiness_train_uses_phase_local_context_and_one_disk_validator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "phase-local-validation"
    context = object()
    ledger = SimpleNamespace(to_primitive=lambda: {"sealed": "ledger"})
    qualification = SimpleNamespace(
        passed=True,
        to_primitive=lambda: {"passed": True, "sealed": "qualification"},
    )
    replay = {
        "schema_version": 1,
        "ledger_sha256": "ledger",
        "selected_candidate_id": "stage:-1",
        "prebehavior_self_replay": {},
        "behavioral_execution": {},
        "behavioral_self_replay": {},
        "certificate": {},
    }
    final_validation_calls: list[Path] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("readiness train re-entered a public full validator")

    monkeypatch.setattr(
        source,
        "_build_oracle_safety_ledger_with_context",
        lambda _episode: (ledger, context),
    )
    monkeypatch.setattr(
        source,
        "_oracle_qualification_from_validated_context",
        lambda supplied: qualification if supplied is context else forbidden(),
    )
    monkeypatch.setattr(
        source,
        "_build_oracle_branch_aware_replay_evidence_from_validated_context",
        lambda supplied: replay if supplied is context else forbidden(),
    )
    monkeypatch.setattr(
        runner,
        "_build_tracker_proof",
        lambda _episode: {"passed": True, "sealed": "tracker"},
    )
    for name in (
        "build_oracle_safety_ledger",
        "validate_oracle_safety_primitive",
        "oracle_qualification_from_safety_ledger",
        "build_oracle_branch_aware_replay_evidence",
    ):
        monkeypatch.setattr(source, name, forbidden)

    def final_validate(path: Path) -> dict:
        final_validation_calls.append(Path(path).resolve())
        return {"status": "COMPLETE"}

    monkeypatch.setattr(runner, "validate_source_artifacts", final_validate)
    manifest = runner.readiness_train(
        run_root=root,
        source_commit=SOURCE_COMMIT,
    )
    assert manifest["artifact_inventory"] == [
        runner.SOURCE_PROOF,
        runner.ORACLE_PROOF,
        runner.TRACKER_PROOF,
        runner.ORACLE_SAFETY_LEDGER_PROOF,
        runner.ORACLE_BEHAVIORAL_REPLAY_PROOF,
    ]
    assert final_validation_calls == [root.resolve()]
    assert {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    } == {
        runner.SOURCE_MANIFEST,
        runner.SOURCE_PROOF,
        runner.ORACLE_PROOF,
        runner.TRACKER_PROOF,
        runner.ORACLE_SAFETY_LEDGER_PROOF,
        runner.ORACLE_BEHAVIORAL_REPLAY_PROOF,
    }


def test_v2_contract_metadata_and_manifest_schema_are_exact() -> None:
    assert source.DESIGN_ROUND == DESIGN_ROUND
    assert source.DESIGN_PACKAGE_STAGE_COMMIT == DESIGN_STAGE_COMMIT
    assert source.DESIGN_ARCHIVE_COMMIT == DESIGN_ARCHIVE_COMMIT
    assert source.DESIGN_DISPOSITION == DESIGN_DISPOSITION
    assert runner.DESIGN_DISPOSITION == DESIGN_DISPOSITION
    assert runner.BOOTSTRAP_GENERATOR == "numpy.Generator(PCG64(2026072901))"
    assert runner.ORACLE_RANKING_ARITHMETIC["lexicographic_keys"] == [
        "violation_count",
        "gate_arrival_step",
        "event_tracking_error",
        "path_length",
        "original_stage_x",
        "original_stage_y",
    ]
    assert {
        "design_archive_commit",
        "geometry_support_certificate",
        "oracle_ranking_arithmetic",
        "return_ready_ownership_rule",
        "pre_action_context_service_mask_rule",
        "first_match_evaluation_rule",
    } <= runner._SOURCE_MANIFEST_KEYS
    frozen = runner._load_frozen_records()
    assert frozen["reconstruction_clarification_stage_commit"] == (
        "d77710ec87e06d345cc1cdfc94d77645d8673de8"
    )
    assert {
        key: frozen[key]
        for key in runner.RECONSTRUCTION_CLARIFICATION_RECORDS
    } == runner.RECONSTRUCTION_CLARIFICATION_RECORDS
    assert frozen["scientific_source_module_git_blob_sha"] == (
        runner.FROZEN_V2_SCIENTIFIC_SOURCE_BLOB_SHA
    )


def test_six_readiness_entries_and_terminal_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "uav-g0-readiness"
    smoke = runner.readiness_interface_smoke(source_commit=SOURCE_COMMIT)
    assert smoke["passed"] is True
    assert smoke["formal_execution_authorized"] is False
    assert smoke["design_round"] == DESIGN_ROUND
    assert smoke["design_package_stage_commit"] == DESIGN_STAGE_COMMIT
    assert smoke["design_archive_commit"] == DESIGN_ARCHIVE_COMMIT
    assert smoke["design_disposition"] == DESIGN_DISPOSITION
    assert smoke["claim_scope"] == "SOURCE_IDENTIFIABILITY_G0_ONLY"
    assert smoke["bootstrap_generator"] == "numpy.Generator(PCG64(2026072901))"
    assert smoke["bootstrap_seed"] == 2026072901
    assert smoke["geometry_support_certificate"]["passed"] is True
    assert smoke["oracle_ranking_arithmetic"] == runner.ORACLE_RANKING_ARITHMETIC
    assert smoke["return_ready_ownership_rule"] == runner.RETURN_READY_OWNERSHIP_RULE
    assert smoke["pre_action_context_service_mask_rule"] == (
        "complete_bool8_target_owned_internal_order"
    )
    assert smoke["first_match_evaluation_rule"] == (
        "strict_lazy_stop_at_first_match_lower_priority_statuses_null"
    )
    assert smoke["production_shapes"] == {
        "uav_positions": [8, 3],
        "service_mask": [8],
        "action": [8, 4],
    }
    _complete_readiness(root)
    assert {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    } == {
        runner.SOURCE_MANIFEST,
        runner.EVALUATION_MANIFEST,
        runner.ANALYSIS_RESULT,
        runner.SOURCE_PROOF,
        runner.ORACLE_PROOF,
        runner.TRACKER_PROOF,
        runner.ORACLE_SAFETY_LEDGER_PROOF,
        runner.ORACLE_BEHAVIORAL_REPLAY_PROOF,
    }
    source_manifest = runner.validate_source_artifacts(root)
    evaluation = runner.validate_evaluation_artifacts(root)
    analysis = runner.validate_analysis_artifacts(root)
    assert source_manifest["episode_id_inventory"] == list(range(128))
    assert source_manifest["design_round"] == DESIGN_ROUND
    assert source_manifest["design_package_stage_commit"] == DESIGN_STAGE_COMMIT
    assert source_manifest["design_archive_commit"] == DESIGN_ARCHIVE_COMMIT
    assert source_manifest["design_disposition"] == DESIGN_DISPOSITION
    assert source_manifest["bootstrap_generator"] == (
        "numpy.Generator(PCG64(2026072901))"
    )
    assert source_manifest["bootstrap_seed"] == 2026072901
    assert source_manifest["geometry_support_rule"] == (
        "analytic_complete_support_for_every_phi_in_[0,2*pi)"
    )
    assert source_manifest["geometry_support_certificate"] == (
        smoke["geometry_support_certificate"]
    )
    assert source_manifest["accepted_g1_source_commit"] == source.ACCEPTED_G1_SOURCE_COMMIT
    assert source_manifest["nested_rollout"] is False
    assert source_manifest["replanning"] is False
    assert source_manifest["real_environment_transitions"] == 0
    assert source_manifest["hypothetical_candidate_transitions"] == 2 * 500
    assert source_manifest["oracle_safety_disposition"] == source.ORACLE_SAFETY_DISPOSITION
    assert source_manifest["return_ready_step_disposition"] == (
        "G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273"
    )
    replay = _load(root / runner.ORACLE_BEHAVIORAL_REPLAY_PROOF)
    assert replay["certificate"]["return_ready_step"] == 273
    execution_steps = replay["behavioral_execution"]["steps"]
    assert sum(execution_steps[190]["pre_action_context"]["service_active_mask"]) == 8
    assert sum(execution_steps[191]["pre_action_context"]["service_active_mask"]) == 7
    assert sum(execution_steps[271]["pre_action_context"]["service_active_mask"]) == 7
    assert sum(execution_steps[272]["pre_action_context"]["service_active_mask"]) == 8
    assert sum(execution_steps[273]["pre_action_context"]["service_active_mask"]) == 8
    assert evaluation["evaluation_optimizer_steps"] == 0
    assert evaluation["production_episode_validity_witness"]["operational_valid"] is True
    assert analysis["result_branch"] is None
    assert analysis["scientific_conclusion"] is None
    assert analysis["primitive_analysis_witness"] == {
        "proof_only": True,
        "operational_valid": True,
        "operational_errors": [],
        "result_branch": None,
    }
    assert not list(root.rglob("*.pt"))
    assert not (root / "checkpoints").exists()


def test_reference_paths_cp_and_tracker_are_independently_reconstructed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "uav-g0-tamper"
    _complete_readiness(root)

    manifest_path = root / runner.SOURCE_MANIFEST
    manifest_bytes = manifest_path.read_bytes()
    manifest = _load(manifest_path)
    manifest["source_proof"]["path"] = "../episode_0_source.json"
    _store(manifest_path, manifest)
    with pytest.raises(ValueError, match="root-local"):
        runner.validate_source_artifacts(root)
    manifest_path.write_bytes(manifest_bytes)

    for field, forged in (
        ("design_round", "20260729_stale"),
        ("design_package_stage_commit", "0" * 40),
        ("design_archive_commit", "1" * 40),
        ("design_disposition", "STALE"),
        ("claim_scope", "UAV_GENERALIZATION"),
        ("bootstrap_generator", "numpy.Generator(MT19937(2026072901))"),
        ("geometry_support_rule", "sampled_phi_only"),
        ("oracle_ranking_arithmetic", {"forged": True}),
        ("return_ready_ownership_rule", "position_tolerance"),
        ("pre_action_context_service_mask_rule", "storage_order"),
        ("first_match_evaluation_rule", "eager"),
    ):
        manifest = _load(manifest_path)
        manifest[field] = forged
        _store(manifest_path, manifest)
        with pytest.raises(ValueError, match="source manifest invariant"):
            runner.validate_source_artifacts(root)
        manifest_path.write_bytes(manifest_bytes)

    manifest = _load(manifest_path)
    manifest.pop("design_archive_commit")
    _store(manifest_path, manifest)
    with pytest.raises(ValueError, match="source manifest exact schema"):
        runner.validate_source_artifacts(root)
    manifest_path.write_bytes(manifest_bytes)

    source_path = root / runner.SOURCE_PROOF
    source_bytes = source_path.read_bytes()
    source_proof = _load(source_path)
    source_proof["geometry"]["geometry_support_certificate"]["passed"] = False
    _store(source_path, source_proof)
    manifest = _load(manifest_path)
    manifest["source_proof"]["sha256"] = runner._digest(source_path)
    _store(manifest_path, manifest)
    with pytest.raises(ValueError, match="source proof does not reconstruct"):
        runner.validate_source_artifacts(root)
    source_path.write_bytes(source_bytes)
    manifest_path.write_bytes(manifest_bytes)

    tracker_path = root / runner.TRACKER_PROOF
    tracker_bytes = tracker_path.read_bytes()
    tracker = _load(tracker_path)
    tracker["permutation_equivariant"] = False
    _store(tracker_path, tracker)
    manifest = _load(manifest_path)
    manifest["tracker_proof"]["sha256"] = runner._digest(tracker_path)
    _store(manifest_path, manifest)
    with pytest.raises(ValueError, match="tracker proof reconstruction"):
        runner.validate_source_artifacts(root)
    tracker_path.write_bytes(tracker_bytes)
    manifest_path.write_bytes(manifest_bytes)

    evaluation_path = root / runner.EVALUATION_MANIFEST
    evaluation_bytes = evaluation_path.read_bytes()
    evaluation = _load(evaluation_path)
    evaluation["clopper_pearson_witness"]["tail_probability"] = 0.049
    _store(evaluation_path, evaluation)
    with pytest.raises(ValueError, match="evaluation artifact invariant"):
        runner.validate_evaluation_artifacts(root)
    evaluation_path.write_bytes(evaluation_bytes)

    extra = root / "proof" / "compatibility-placeholder.json"
    extra.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory mismatch"):
        runner.validate_source_artifacts(root)


def test_registered_ledger_and_behavioral_replay_tampering_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "uav-g0-ledger-tamper"
    _complete_readiness(root)
    manifest_path = root / runner.SOURCE_MANIFEST
    ledger_path = root / runner.ORACLE_SAFETY_LEDGER_PROOF
    replay_path = root / runner.ORACLE_BEHAVIORAL_REPLAY_PROOF
    original_manifest = manifest_path.read_bytes()
    original_ledger = ledger_path.read_bytes()
    original_replay = replay_path.read_bytes()

    ledger = _load(ledger_path)
    ledger["candidates"][0]["service_score"] = 1.0
    ledger_without_digest = dict(ledger)
    ledger_without_digest.pop("content_sha256")
    ledger["content_sha256"] = geometry.sha256_json(ledger_without_digest)
    _store(ledger_path, ledger)
    manifest = _load(manifest_path)
    manifest["oracle_safety_ledger_proof"]["sha256"] = runner._digest(ledger_path)
    _store(manifest_path, manifest)
    with pytest.raises(source.G0RealizationError, match="candidate trace schema"):
        runner.validate_source_artifacts(root)

    ledger_path.write_bytes(original_ledger)
    manifest_path.write_bytes(original_manifest)
    replay = _load(replay_path)
    replay["behavioral_execution"]["steps"][0]["candidate_id"] = "stage:forged"
    _store(replay_path, replay)
    manifest = _load(manifest_path)
    manifest["oracle_behavioral_replay_proof"]["sha256"] = runner._digest(
        replay_path
    )
    _store(manifest_path, manifest)
    with pytest.raises(
        source.G0RealizationError,
        match="digest|self-replay|identity",
    ):
        runner.validate_source_artifacts(root)

    replay_path.write_bytes(original_replay)
    manifest_path.write_bytes(original_manifest)
    replay = _load(replay_path)
    for name in ("behavioral_execution", "behavioral_self_replay"):
        replay[name]["steps"][273]["pre_action_context"].pop(
            "channel_tape_cursor"
        )
        replay[name]["trace_sha256"] = geometry.sha256_json(
            {
                key: value
                for key, value in replay[name].items()
                if key != "trace_sha256"
            }
        )
    _store(replay_path, replay)
    manifest = _load(manifest_path)
    manifest["oracle_behavioral_replay_proof"]["sha256"] = runner._digest(
        replay_path
    )
    _store(manifest_path, manifest)
    with pytest.raises(source.G0RealizationError, match="branchpoint"):
        runner.validate_source_artifacts(root)

    replay_path.write_bytes(original_replay)
    manifest_path.write_bytes(original_manifest)
    replay = _load(replay_path)
    for name in ("behavioral_execution", "behavioral_self_replay"):
        replay[name]["steps"][191]["pre_action_context"].pop(
            "service_active_mask"
        )
        replay[name]["trace_sha256"] = geometry.sha256_json(
            {
                key: value
                for key, value in replay[name].items()
                if key != "trace_sha256"
            }
        )
    _store(replay_path, replay)
    manifest = _load(manifest_path)
    manifest["oracle_behavioral_replay_proof"]["sha256"] = runner._digest(
        replay_path
    )
    _store(manifest_path, manifest)
    with pytest.raises(source.G0RealizationError, match="branchpoint"):
        runner.validate_source_artifacts(root)

    replay_path.write_bytes(original_replay)
    manifest_path.write_bytes(original_manifest)
    evaluation_path = root / runner.EVALUATION_MANIFEST
    evaluation = _load(evaluation_path)
    evaluation["production_episode_validity_witness"] = {
        "operational_valid": True,
        "errors": [],
        "result_branch": statistics.IDENTIFIED_BRANCH,
    }
    _store(evaluation_path, evaluation)
    with pytest.raises(ValueError, match="evaluation artifact invariant"):
        runner.validate_evaluation_artifacts(root)


def test_stale_readiness_root_fails_before_mutation(
    tmp_path: Path,
) -> None:
    stale = tmp_path / "stale"
    stale.mkdir()
    (stale / "existing.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError, match="absent or empty"):
        runner.readiness_train(run_root=stale, source_commit=SOURCE_COMMIT)
    assert (stale / "existing.txt").read_text(encoding="utf-8") == "preserve"



def _binding(tmp_path: Path, *, mode: str = "nonformal-preflight") -> runner.FormalRuntimeBinding:
    preflight = tmp_path / "preflight"
    formal = tmp_path / "formal"
    return runner.FormalRuntimeBinding(
        execution_mode=mode,
        run_root=preflight if mode == "nonformal-preflight" else formal,
        nonformal_preflight_root=None if mode == "nonformal-preflight" else preflight,
        bound_formal_root=formal,
        source_commit=runner.FORMAL_INTERFACE_SOURCE_COMMIT,
        accepted_g0_source_commit=runner.ACCEPTED_G0_SOURCE_COMMIT,
        formal_execution_commit="a" * 40,
        formal_authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
        external_user_authorization_reference="direct-user-grant:test",
        failed_root_identity="b" * 64,
        failed_root_schema_id=runner.FAILED_ROOT_SCHEMA_ID,
        failed_root_schema_version=runner.FAILED_ROOT_SCHEMA_VERSION,
        workers=16,
        start_method="spawn",
    )


def test_result_bearing_alignment_binding_is_exact_and_removal_fails_pre_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(tmp_path)
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == (
        "c88f43de6451c40defefd7c679ba8d353c45735c"
    )
    assert runner.ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA == (
        "b0baab9c47c2537217b689699d0520f158355e3d"
    )
    assert runner.ALIGNMENT_STAGE_COMMIT == (
        "499fcaac7acea4faf58268b71773459ef73bedec"
    )
    assert runner.ALIGNMENT_DISPOSITION == "ALIGNED"
    monkeypatch.setattr(runner, "_verify_git_identity", lambda _commit: None)
    monkeypatch.setattr(
        runner,
        "_runtime_environment_manifest",
        lambda commit: {"formal_execution_commit": commit},
    )
    environment = runner._validate_binding(binding, stage="train")
    assert environment["formal_execution_commit"] == binding.formal_execution_commit
    assert not binding.run_root.exists()
    assert not binding.bound_formal_root.exists()

    monkeypatch.setattr(runner, "ALIGNMENT_DISPOSITION", None)
    with pytest.raises(ValueError, match="implementation/alignment"):
        runner.scientific_train(binding=binding)
    assert not binding.run_root.exists()
    assert not binding.bound_formal_root.exists()


def test_bound_alignment_tuple_matches_git_objects() -> None:
    source_path = "ha_ctse_process/uav_source_identifiability_g0.py"
    aligned_blob = runner._command_output(
        (
            "git",
            "rev-parse",
            f"{runner.ALIGNED_IMPLEMENTATION_COMMIT}:{source_path}",
        )
    )
    head_blob = runner._command_output(("git", "rev-parse", f"HEAD:{source_path}"))
    assert aligned_blob == runner.ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA
    assert head_blob == aligned_blob
    assert runner._command_output(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            runner.ALIGNED_IMPLEMENTATION_COMMIT,
            "HEAD",
        )
    ) == ""
    assert runner._command_output(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            runner.ALIGNMENT_STAGE_COMMIT,
            "HEAD",
        )
    ) == ""


def test_result_bearing_alignment_rejects_historical_identity_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(tmp_path)
    monkeypatch.setattr(
        runner, "ALIGNED_IMPLEMENTATION_COMMIT", runner.ACCEPTED_G0_SOURCE_COMMIT
    )
    monkeypatch.setattr(
        runner,
        "ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA",
        runner.FROZEN_V2_SCIENTIFIC_SOURCE_BLOB_SHA,
    )
    monkeypatch.setattr(runner, "ALIGNMENT_STAGE_COMMIT", "c" * 40)
    monkeypatch.setattr(runner, "ALIGNMENT_DISPOSITION", "ALIGNED")
    with pytest.raises(ValueError, match="implementation/alignment"):
        runner.scientific_train(binding=binding)
    assert not binding.run_root.exists()
    assert not binding.bound_formal_root.exists()


def test_result_cli_requires_explicit_wrapper_carriers(tmp_path: Path) -> None:
    parser = runner._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "train", "--execution-mode", "nonformal-preflight",
                "--run-root", str((tmp_path / "preflight").resolve()),
                "--source-commit", runner.FORMAL_INTERFACE_SOURCE_COMMIT,
            ]
        )
    args = parser.parse_args(
        [
            "train", "--execution-mode", "nonformal-preflight",
            "--run-root", str((tmp_path / "preflight").resolve()),
            "--source-commit", runner.FORMAL_INTERFACE_SOURCE_COMMIT,
            "--accepted-g0-source-commit", runner.ACCEPTED_G0_SOURCE_COMMIT,
            "--formal-execution-commit", "a" * 40,
            "--formal-authorization-token", runner.FORMAL_AUTHORIZATION_TOKEN,
            "--external-user-authorization-reference", "direct-user-grant:test",
            "--bound-formal-root", str((tmp_path / "formal").resolve()),
            "--failed-root-identity", "b" * 64,
            "--failed-root-schema-id", runner.FAILED_ROOT_SCHEMA_ID,
            "--failed-root-schema-version", "1", "--workers", "16",
            "--start-method", "spawn",
        ]
    )
    assert args.external_user_authorization_reference == "direct-user-grant:test"
    assert args.bound_formal_root == (tmp_path / "formal").resolve()
    exact_binding = _binding(tmp_path).to_primitive()
    runner._require_runtime_binding_schema(exact_binding)
    with pytest.raises(ValueError, match="runtime binding exact schema"):
        runner._require_runtime_binding_schema({**exact_binding, "authority": True})
    with pytest.raises(ValueError, match="carrier exact schema"):
        runner._require_runtime_binding_schema(
            {
                **exact_binding,
                "carrier": {**exact_binding["carrier"], "result_branch": "IDENTIFIED"},
            }
        )


def test_mocked_preflight_writes_exact_four_file_terminal_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(tmp_path)
    episode = geometry.make_episode_source(0)
    fake_runs = {
        identity: SimpleNamespace(
            control=identity[0],
            cell=identity[1],
            controller_evidence={
                "behavioral_replay_certificate": {
                    "return_ready_step": 273 if identity[1] is source.Cell.EVENT else None
                }
            }
        )
        for identity in runner._RUN_IDENTITIES
    }
    validity = statistics.EpisodeValidityRecord(
        episode_id=0,
        source_event_digest="s", source_no_event_digest="s",
        sameinfo_no_event_digest="n", no_reallocation_no_event_digest="n",
        geometry_support_violations=0, rng_namespace_violations=0,
        pairing_mismatches=0, assignment_failures=0, tracker_failures=0,
        oracle_qualification_failures=0, action_support_violations=0,
        information_visibility_violations=0, ownership_violations=0,
        survivor_continuity_violations=0, permutation_mismatches=0,
        metric_reconstruction_mismatches=0, missing_rows=0, nonfinite_rows=0,
    )
    payload = {
        "episode_id": 0,
        "source_primitive": episode.to_primitive(),
        "runs": {key: {"mocked": key} for key in runner._RUN_KEYS},
    }
    monkeypatch.setattr(
        runner, "ALIGNED_IMPLEMENTATION_COMMIT", "d" * 40
    )
    monkeypatch.setattr(runner, "ALIGNED_SCIENTIFIC_SOURCE_BLOB_SHA", "e" * 40)
    monkeypatch.setattr(runner, "ALIGNMENT_STAGE_COMMIT", "c" * 40)
    monkeypatch.setattr(runner, "ALIGNMENT_DISPOSITION", "ALIGNED")
    monkeypatch.setattr(runner, "_verify_git_identity", lambda _commit: None)
    monkeypatch.setattr(
        runner, "_runtime_environment_manifest",
        lambda commit: {"formal_execution_commit": commit, "mocked": True},
    )
    monkeypatch.setattr(
        runner, "_execute_episode_ids",
        lambda episode_ids, *, workers: [payload],
    )
    monkeypatch.setattr(
        runner, "_load_episode_bundle",
        lambda *_args, **_kwargs: (episode, fake_runs, {
            "bundle_sha256": _load(binding.run_root / "episodes" / "episode_000.json")["bundle_sha256"]
        }),
    )
    def mocked_replay(_episode: object, run: object) -> tuple[str, ...]:
        source.run_g0_episode(None)
        assert getattr(run, "control") in source.Control
        return ()

    def mocked_validity(
        replay_episode: object,
        replay_runs: dict,
    ) -> tuple[object, dict]:
        for run in replay_runs.values():
            source._authoritative_replay_errors(replay_episode, run)
        return validity, {}

    monkeypatch.setattr(source, "run_g0_episode", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(source, "_authoritative_replay_errors", mocked_replay)
    monkeypatch.setattr(source, "build_episode_validity_record", mocked_validity)

    terminal = runner.scientific_train(binding=binding)
    assert terminal["status"] == "COMPLETE"
    assert terminal["formal"] is False
    assert terminal["result_branch"] is None
    assert {
        path.relative_to(binding.run_root).as_posix()
        for path in binding.run_root.rglob("*") if path.is_file()
    } == {
        "preflight_contract.json", "episodes/episode_000.json",
        "preflight_result.json", "terminal_manifest.json",
    }
    contract = _load(binding.run_root / "preflight_contract.json")
    assert contract["runtime_binding"]["carrier"] == binding.carrier_primitive()
    assert contract["runtime_binding"]["accepted_g0_source_commit"] == (
        runner.ACCEPTED_G0_SOURCE_COMMIT
    )
    assert contract["runtime_binding"]["aligned_implementation_commit"] == "d" * 40
    assert contract["runtime_binding"]["aligned_scientific_source_blob_sha"] == (
        "e" * 40
    )
    assert contract["frozen_records"]["G0_FORMAL_INTERFACE_NEXT_ACTION"] == (
        "NEW_SOURCE_CANDIDATE_AND_ALIGNMENT"
    )
    assert contract["content_sha256"] == runner._content_digest(
        {key: value for key, value in contract.items() if key != "content_sha256"},
        "content_sha256",
    )["content_sha256"]

    monkeypatch.setattr(
        source,
        "run_g0_episode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("formal admission executed a preflight simulator run")
        ),
    )
    monkeypatch.setattr(
        runner,
        "_load_episode_bundle",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("formal admission imported preflight episode rows")
        ),
    )
    admission = runner._validate_preflight_admission(
        binding.run_root,
        binding,
        {"formal_execution_commit": "a" * 40, "mocked": True},
    )
    assert admission["content_sha256"] == terminal["content_sha256"]
    copied_root = tmp_path / "copied-preflight"
    shutil.copytree(binding.run_root, copied_root)
    with pytest.raises(ValueError, match="runtime path binding"):
        runner._validate_preflight_admission(
            copied_root,
            binding,
            {"formal_execution_commit": "a" * 40, "mocked": True},
        )

    result_path = binding.run_root / "preflight_result.json"
    result = _load(result_path)
    result["run_count"] = 7
    result = runner._content_digest(
        {key: value for key, value in result.items() if key != "content_sha256"},
        "content_sha256",
    )
    _store(result_path, result)
    terminal_path = binding.run_root / "terminal_manifest.json"
    tampered_terminal = _load(terminal_path)
    tampered_terminal["preflight_result_sha256"] = result["content_sha256"]
    tampered_terminal["exact_file_inventory"]["preflight_result.json"] = runner._digest(result_path)
    tampered_terminal = runner._content_digest(
        {
            key: value
            for key, value in tampered_terminal.items()
            if key != "content_sha256"
        },
        "content_sha256",
    )
    _store(terminal_path, tampered_terminal)
    with pytest.raises(ValueError, match="preflight operational result"):
        runner._validate_preflight_admission(
            binding.run_root,
            binding,
            {"formal_execution_commit": "a" * 40, "mocked": True},
        )


def test_authoritative_replay_counts_are_single_pass_and_guarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source, "run_g0_episode", lambda *_args, **_kwargs: None)
    with runner._authoritative_replay_guard(6):
        for _ in range(6):
            source.run_g0_episode(None)
    with pytest.raises(RuntimeError, match="expected 6, got 5"):
        with runner._authoritative_replay_guard(6):
            for _ in range(5):
                source.run_g0_episode(None)


def test_analysis_reconstruction_rejects_per_episode_validity_tamper() -> None:
    metrics = {key: [{"episode_id": 0}] for key in runner._RUN_KEYS}
    validity = [{"episode_id": 0, "tracker_failures": 0}]
    bundles = {"0": "d" * 64}
    evaluation = {
        "metric_rows": metrics,
        "validity_records": validity,
        "episode_bundle_sha256_by_id": bundles,
    }
    runner._require_evaluation_reconstruction(
        evaluation, metrics, validity, bundles
    )
    tampered = [{"episode_id": 0, "tracker_failures": 1}]
    with pytest.raises(ValueError, match="independent reconstruction"):
        runner._require_evaluation_reconstruction(
            evaluation, metrics, tampered, bundles
        )


def _empty_episode_run() -> source.EpisodeRunEvidence:
    arrays = {
        name: np.zeros(shape, dtype=dtype)
        for name, (shape, dtype) in source.EPISODE_RUN_ARRAY_SPECS.items()
    }
    return source.EpisodeRunEvidence(
        episode_id=0, control=source.Control.SAME_INFORMATION,
        cell=source.Cell.NO_EVENT,
        metrics=source.EpisodeMetrics(
            episode_id=0, control=source.Control.SAME_INFORMATION,
            cell=source.Cell.NO_EVENT, onset=200, duration=80,
            j_event=1.0, q_ordinary=0.90, m_event=0.0,
            a_control=1.0, b_access=1, c_cat=0,
        ),
        source_sha256="s" * 64, controller_evidence={}, lifecycle_events=(),
        target_trace_sha256="t" * 64, raw_action_trace_sha256="a" * 64,
        executed_velocity_trace_sha256="v" * 64,
        executed_position_trace_sha256="p" * 64,
        service_trace_sha256="r" * 64, controller_state_sha256="c" * 64,
        tracker_failures=0, action_support_violations=0, ownership_violations=0,
        backhaul_guard_blocked_actions=0, oracle_qualification_failures=0,
        **arrays,
    )


def test_episode_run_codec_is_exact_byte_stable_and_fail_closed() -> None:
    run = _empty_episode_run()
    primitive = episode_serialization.episode_run_to_primitive(run)
    assert list(primitive) == [
        "episode_id", "control", "cell", "metrics", "source_sha256",
        "user_demand_input_mbps", "user_delivered_input_mbps",
        "channel_association_input", "delivered_user_rates_mbps",
        "target_trace", "raw_action_trace", "executed_velocity_trace",
        "position_trace", "active_mask_trace", "weakest_service",
        "controller_evidence", "target_trace_sha256", "raw_action_trace_sha256",
        "executed_velocity_trace_sha256", "executed_position_trace_sha256",
        "service_trace_sha256", "controller_state_sha256", "lifecycle_events",
        "tracker_failures", "action_support_violations", "ownership_violations",
        "backhaul_guard_blocked_actions", "oracle_qualification_failures",
    ]
    raw_action = primitive["raw_action_trace"]
    assert raw_action == {
        "dtype": "float32", "shape": [500, 8, 4],
        "data_hex": run.raw_action_trace.tobytes(order="C").hex(),
    }
    restored = episode_serialization.episode_run_from_primitive(primitive)
    assert episode_serialization.episode_run_to_primitive(restored) == primitive
    assert all(
        not getattr(restored, name).flags.writeable
        for name in source.EPISODE_RUN_ARRAY_SPECS
    )

    with pytest.raises(ValueError, match="schema mismatch"):
        episode_serialization.episode_run_from_primitive(
            {key: value for key, value in primitive.items() if key != "source_sha256"}
        )
    wrong_dtype = np.zeros((500, 8, 4), dtype=np.float64)
    tampered = dict(primitive)
    tampered["raw_action_trace"] = {
        "dtype": "float64", "shape": [500, 8, 4],
        "data_hex": wrong_dtype.tobytes(order="C").hex(),
    }
    with pytest.raises(ValueError, match="dtype/shape mismatch"):
        episode_serialization.episode_run_from_primitive(tampered)


def test_canonical_sorted_episode_bundle_round_trip_preserves_run_identities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_primitive = {"episode_id": 0, "sha256": "d" * 64}
    dummy_episode = SimpleNamespace(to_primitive=lambda: source_primitive)
    contract_sha = "c" * 64
    bundle = runner._content_digest(
        {
            "schema_id": "UAV_G0_EPISODE_BUNDLE",
            "schema_version": 1,
            "formal": False,
            "contract_sha256": contract_sha,
            "episode_id": 0,
            "source_primitive": source_primitive,
            "source_sha256": source_primitive["sha256"],
            "runs": {
                key: {"episode_id": 0, "identity": key}
                for key in runner._RUN_KEYS
            },
        },
        "bundle_sha256",
    )
    path = tmp_path / "episode_000.json"
    _store(path, bundle)
    monkeypatch.setattr(geometry, "make_episode_source", lambda _episode_id: dummy_episode)
    monkeypatch.setattr(
        episode_serialization,
        "episode_run_from_primitive",
        lambda value: SimpleNamespace(
            episode_id=value["episode_id"], identity=value["identity"]
        ),
    )

    _episode, runs, loaded = runner._load_episode_bundle(
        path,
        formal=False,
        contract_sha256=contract_sha,
    )
    assert loaded == bundle
    assert [runs[identity].identity for identity in runner._RUN_IDENTITIES] == list(
        runner._RUN_KEYS
    )


def test_failed_root_preserves_prior_terminal_but_replaces_current_invalid_terminal(
    tmp_path: Path,
) -> None:
    binding = _binding(tmp_path)
    prior_root = tmp_path / "prior"
    prior_root.mkdir()
    prior_terminal = prior_root / "terminal_manifest.json"
    prior_terminal.write_text("prior-terminal\n", encoding="utf-8")
    runner._write_failed_root(
        prior_root,
        binding,
        gate="gate_11",
        error=ValueError("repeat"),
    )
    assert prior_terminal.read_text(encoding="utf-8") == "prior-terminal\n"
    assert not (prior_root / "failed_root.json").exists()

    current_root = tmp_path / "current"
    current_root.mkdir()
    (current_root / "terminal_manifest.json").write_text(
        "current-invalid-terminal\n",
        encoding="utf-8",
    )
    runner._write_failed_root(
        current_root,
        binding,
        gate="gate_11",
        error=ValueError("self-check"),
        current_attempt_terminal=True,
    )
    assert not (current_root / "terminal_manifest.json").exists()
    failed_path = current_root / "failed_root.json"
    first = failed_path.read_bytes()
    assert _load(failed_path)["failed_gate"] == "gate_11"
    runner._write_failed_root(
        current_root,
        binding,
        gate="gate_09",
        error=ValueError("repeat"),
    )
    assert failed_path.read_bytes() == first


def test_bootstrap_plan_is_generated_once_and_reused_for_source_validation() -> None:
    original = statistics.make_bootstrap_index_plan
    plan = np.arange(12, dtype=np.int64).reshape(3, 4)
    with runner._reuse_bootstrap_index_plan(plan):
        assert statistics.make_bootstrap_index_plan() is plan
    assert statistics.make_bootstrap_index_plan is original


def test_branch_witnesses_cover_exact_first_match_inventory() -> None:
    witnesses = runner._branch_witnesses()
    assert {item["result_branch"] for item in witnesses.values()} == set(
        statistics.FIRST_MATCH_ORDER
    )
    assert witnesses["invalid"] == {
        "valid": False,
        "ORACLE_STATUS": None,
        "SAMEINFO_STATUS": None,
        "CAUSAL_STATUS": None,
        "result_branch": statistics.INVALID_BRANCH,
    }
    assert witnesses["infeasible"]["SAMEINFO_STATUS"] is None
    assert witnesses["infeasible"]["CAUSAL_STATUS"] is None
    assert witnesses["oracle_only"]["CAUSAL_STATUS"] is None
    assert witnesses["underpowered_oracle"]["SAMEINFO_STATUS"] is None
    assert witnesses["underpowered_oracle"]["CAUSAL_STATUS"] is None
    assert witnesses["underpowered_sameinfo"]["CAUSAL_STATUS"] is None
    assert witnesses["identified"]["result_branch"] == statistics.IDENTIFIED_BRANCH
    assert runner.SCHEMA_VERSION == source.SCHEMA_VERSION
    assert runner.FORMAL_EXECUTION_AUTHORIZED is False
