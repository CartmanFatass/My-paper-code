from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.run_cross_lifecycle_handoff_g2 as runner


def _passing_predicates() -> dict[str, object]:
    return {
        "operational_valid": True,
        "source_identifiable": True,
        "max_arm_lcb": 0.90,
        "max_arm_ucb": 0.94,
        "g_team_lcb": 0.14,
        "g_team_ucb": 0.18,
        "g_link_lcb": 0.15,
        "g_link_ucb": 0.19,
        "mark_accuracy_lcb": 0.80,
        "mark_accuracy_ucb": 0.90,
        "action_tv_lcb": 0.20,
        "action_tv_ucb": 0.30,
        "utility_drop_lcb": 0.20,
        "utility_drop_ucb": 0.30,
        "ehc_utility_lcb": 0.90,
        "ehc_utility_ucb": 0.94,
    }


def test_frozen_budget_and_first_match_selector_are_exact() -> None:
    assert runner.ARM_NAMES == ("TEAM_REC", "DUM", "EHC")
    assert runner.FORMAL_BUDGET == {
        "replicates": 5,
        "environments": 16,
        "horizon": 64,
        "updates": 160,
        "ppo_passes": 4,
        "evaluation_episodes_per_cell": 256,
        "audit_episodes_per_replicate": 128,
        "bootstrap_repetitions": 10_000,
    }
    predicates = _passing_predicates()
    assert runner.select_result_branch(predicates) == "EHC_HANDOFF_SUPPORTED_G2"

    changed = predicates | {"operational_valid": False, "max_arm_ucb": 0.0}
    assert runner.select_result_branch(changed) == "INVALID_OPERATIONAL_HANDOFF_G2"
    changed = predicates | {"source_identifiable": False, "max_arm_ucb": 0.0}
    assert runner.select_result_branch(changed) == "SOURCE_NON_IDENTIFIABLE_HANDOFF_G2"
    changed = predicates | {"max_arm_lcb": 0.70, "max_arm_ucb": 0.79}
    assert runner.select_result_branch(changed) == "NO_ACCESS_HANDOFF_G2"
    changed = predicates | {"max_arm_lcb": 0.79, "max_arm_ucb": 0.81}
    assert runner.select_result_branch(changed) == "UNDERPOWERED_ACCESS_HANDOFF_G2"
    changed = predicates | {"g_team_lcb": -0.02, "g_team_ucb": 0.08}
    assert runner.select_result_branch(changed) == "TEAM_REC_SUFFICIENT_HANDOFF_G2"
    changed = predicates | {"g_link_lcb": -0.02, "g_link_ucb": 0.08}
    assert runner.select_result_branch(changed) == "LINK_NULL_HANDOFF_G2"
    changed = predicates | {"mark_accuracy_lcb": 0.60, "mark_accuracy_ucb": 0.70}
    assert runner.select_result_branch(changed) == "REPRESENTATION_ONLY_HANDOFF_G2"
    changed = predicates | {
        "g_team_lcb": 0.05,
        "g_team_ucb": 0.15,
        "g_link_lcb": 0.05,
        "g_link_ucb": 0.15,
    }
    assert runner.select_result_branch(changed) == "MIXED_UNDERPOWERED_HANDOFF_G2"


def test_reduced_exercise_closes_paths_and_is_not_formal(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    analysis = runner.exercise_run(run_root, source_commit="d" * 40)
    assert analysis["formal"] is False
    assert analysis["status"] == "COMPLETE"
    assert analysis["operational_errors"] == []
    assert analysis["result"] == "SOURCE_NON_IDENTIFIABLE_HANDOFF_G2"
    assert len(analysis["checkpoint_references"]) == 3
    assert len(analysis["evaluation_references"]) == 12
    assert len((run_root / "causal_audit.jsonl").read_text().splitlines()) == 8
    assert not list(run_root.rglob("latest.pt"))
    resumed = runner.train_run(
        run_root,
        source_commit="d" * 40,
        formal=False,
        authorization_token=None,
    )
    assert resumed["status"] == "TRAIN_COMPLETE"
    with pytest.raises(ValueError, match="formal=true"):
        runner.validate_formal_result(run_root)
    with pytest.raises(FileExistsError, match="already exists"):
        runner.exercise_run(run_root, source_commit="d" * 40)


def test_analyzer_turns_evidence_tamper_into_operational_invalid(tmp_path: Path) -> None:
    run_root = tmp_path / "tamper"
    runner.exercise_run(run_root, source_commit="e" * 40)
    path = run_root / "evaluation" / "EHC" / "replicate_0" / "heldout_deterministic.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["utility"] = 2.0
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    analysis = runner.analyze_run(run_root, formal=False)
    assert analysis["result"] == "INVALID_OPERATIONAL_HANDOFF_G2"
    assert analysis["predicate_inputs"]["operational_valid"] is False
    assert "outside [0,1]" in analysis["operational_errors"][0]


def test_progress_replace_retries_transient_onedrive_permission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "progress.json"
    real_replace = runner.os.replace
    calls = 0

    def flaky_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise PermissionError("transient lock")
        return real_replace(source, destination)

    monkeypatch.setattr(runner.os, "replace", flaky_replace)
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)
    runner._atomic_json(path, {"status": "OK"})
    assert calls == 3
    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "OK"}
    assert not list(tmp_path.glob("*.tmp"))


def test_formal_token_fails_before_run_creation(tmp_path: Path) -> None:
    run_root = tmp_path / "formal"
    with pytest.raises(ValueError, match="authorization token"):
        runner.train_run(
            run_root,
            source_commit="f" * 40,
            formal=True,
            authorization_token="wrong",
        )
    assert not run_root.exists()
