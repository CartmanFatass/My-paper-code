from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from ha_ctse_process import uav_source_identifiability_g0 as source
from scripts import run_uav_source_identifiability_g0 as runner


SOURCE_COMMIT = "a9580155b294a52f1e57be08c4ea3a8dfdd7630b"


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


def test_six_readiness_entries_and_terminal_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "uav-g0-readiness"
    smoke = runner.readiness_interface_smoke(source_commit=SOURCE_COMMIT)
    assert smoke["passed"] is True
    assert smoke["formal_execution_authorized"] is False
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
    assert set(witnesses.values()) == set(source.FIRST_MATCH_ORDER)
    assert witnesses["invalid"] == source.INVALID_BRANCH
    assert witnesses["identified"] == source.IDENTIFIED_BRANCH
    assert runner.SCHEMA_VERSION == source.SCHEMA_VERSION
    assert runner.FORMAL_EXECUTION_AUTHORIZED is False
