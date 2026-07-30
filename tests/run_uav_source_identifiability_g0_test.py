from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from ha_ctse_process import uav_source_identifiability_g0 as source
from scripts import run_uav_source_identifiability_g0 as runner


SOURCE_COMMIT = "fdc76381176a40c306a327c6edd1357a828cf466"
DESIGN_ROUND = "20260730_uav_g0_executable_contract_addendum_v2"
DESIGN_STAGE_COMMIT = "8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc"
DESIGN_ARCHIVE_COMMIT = "9c1566e1c6adefcd500facb1bb50d5a7428eae9c"
DESIGN_DISPOSITION = (
    "G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT"
)


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
    ledger["content_sha256"] = source.sha256_json(ledger_without_digest)
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
        replay[name]["trace_sha256"] = source.sha256_json(
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
        replay[name]["trace_sha256"] = source.sha256_json(
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
        "result_branch": source.IDENTIFIED_BRANCH,
    }
    _store(evaluation_path, evaluation)
    with pytest.raises(ValueError, match="evaluation artifact invariant"):
        runner.validate_evaluation_artifacts(root)


def test_stale_root_and_scientific_or_formal_entries_fail_before_mutation(
    tmp_path: Path,
) -> None:
    stale = tmp_path / "stale"
    stale.mkdir()
    (stale / "existing.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError, match="absent or empty"):
        runner.readiness_train(run_root=stale, source_commit=SOURCE_COMMIT)
    assert (stale / "existing.txt").read_text(encoding="utf-8") == "preserve"

    for scientific in (
        runner.scientific_source,
        runner.scientific_evaluate,
        runner.scientific_analyze,
    ):
        root = tmp_path / scientific.__name__
        with pytest.raises(RuntimeError, match="not authorized"):
            scientific(run_root=root, source_commit=SOURCE_COMMIT)
        assert not root.exists()

    cli_root = tmp_path / "formal-cli"
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(runner.__file__).resolve()),
            "source",
            "--run-root",
            str(cli_root),
            "--source-commit",
            SOURCE_COMMIT,
            "--formal",
        ],
        cwd=Path(runner.__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "not authorized" in completed.stderr
    assert not cli_root.exists()


def test_branch_witnesses_cover_exact_first_match_inventory() -> None:
    witnesses = runner._branch_witnesses()
    assert {item["result_branch"] for item in witnesses.values()} == set(
        source.FIRST_MATCH_ORDER
    )
    assert witnesses["invalid"] == {
        "valid": False,
        "ORACLE_STATUS": None,
        "SAMEINFO_STATUS": None,
        "CAUSAL_STATUS": None,
        "result_branch": source.INVALID_BRANCH,
    }
    assert witnesses["infeasible"]["SAMEINFO_STATUS"] is None
    assert witnesses["infeasible"]["CAUSAL_STATUS"] is None
    assert witnesses["oracle_only"]["CAUSAL_STATUS"] is None
    assert witnesses["underpowered_oracle"]["SAMEINFO_STATUS"] is None
    assert witnesses["underpowered_oracle"]["CAUSAL_STATUS"] is None
    assert witnesses["underpowered_sameinfo"]["CAUSAL_STATUS"] is None
    assert witnesses["identified"]["result_branch"] == source.IDENTIFIED_BRANCH
    assert runner.SCHEMA_VERSION == source.SCHEMA_VERSION
    assert runner.FORMAL_EXECUTION_AUTHORIZED is False
