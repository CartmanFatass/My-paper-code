from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_useful_effect_roster_g3 import (
    EXERCISE_CONFIG,
    run_exercise,
    select_result_branch,
    validate_formal_result,
    validate_run_artifacts,
)


def _predicates(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "operational_valid": True,
        "source_identifiable": True,
        "max_arm_lcb": 0.95,
        "max_arm_ucb": 0.97,
        "g_team_lcb": 0.12,
        "g_team_ucb": 0.16,
        "g_null_lcb": 0.20,
        "g_null_ucb": 0.24,
        "battery_pass": True,
        "battery_confident_fail": False,
    }
    values.update(overrides)
    return values


def test_first_match_selector_precedence_and_boundaries() -> None:
    assert (
        select_result_branch(_predicates(operational_valid=False))
        == "INVALID_OPERATIONAL_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(_predicates(source_identifiable=False))
        == "SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(_predicates(max_arm_lcb=0.2, max_arm_ucb=0.89))
        == "NO_ACCESS_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(_predicates(max_arm_lcb=0.89, max_arm_ucb=0.90))
        == "UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(_predicates())
        == "ROSTER_GENERALIZATION_SUPPORTED_G3"
    )
    assert (
        select_result_branch(_predicates(g_team_lcb=-0.1, g_team_ucb=0.10))
        == "TEAM_REC_SUFFICIENT_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(
            _predicates(
                g_team_lcb=0.11,
                g_team_ucb=0.14,
                g_null_lcb=-0.1,
                g_null_ucb=0.10,
                battery_pass=False,
            )
        )
        == "NO_ROSTER_SUFFICIENT_USEFUL_ROSTER_G3"
    )
    assert (
        select_result_branch(
            _predicates(battery_pass=False, battery_confident_fail=True)
        )
        == "ROSTER_REPRESENTATION_ONLY_G3"
    )


def test_bounded_exercise_closes_shared_path_and_is_nonformal(tmp_path: Path) -> None:
    root = tmp_path / "exercise"
    source_commit = "5" * 40
    analysis_path = run_exercise(root, source_commit=source_commit)
    assert analysis_path == root / "analysis_result.json"

    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    evaluation = json.loads(
        (root / "evaluation_manifest.json").read_text(encoding="utf-8")
    )
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert manifest["formal"] is False
    assert manifest["status"] == "TRAIN_COMPLETE"
    assert len(manifest["checkpoint_references"]) == 3
    assert evaluation["status"] == "EVALUATION_COMPLETE"
    assert len(evaluation["evaluation_references"]) == 24
    assert analysis["status"] == "COMPLETE"
    assert analysis["operational_errors"] == []
    assert analysis["training_exposure"] == {
        arm: {
            "updates": EXERCISE_CONFIG.updates,
            "optimizer_steps": EXERCISE_CONFIG.updates * EXERCISE_CONFIG.ppo_passes,
            "episodes_completed": EXERCISE_CONFIG.updates
            * EXERCISE_CONFIG.episodes_per_update,
        }
        for arm in ("NO_ROSTER", "TEAM_REC", "ROSTER_ATTN")
    }
    validate_run_artifacts(root, require_formal=False)
    with pytest.raises(ValueError, match="formal=true"):
        validate_formal_result(root)


def test_reference_tamper_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "tamper"
    run_exercise(root, source_commit="6" * 40)
    evaluation = json.loads(
        (root / "evaluation_manifest.json").read_text(encoding="utf-8")
    )
    first = root / evaluation["evaluation_references"][0]
    rows = first.read_text(encoding="utf-8").splitlines()
    original_row = rows[0]
    payload = json.loads(rows[0])
    payload["source_commit"] = "7" * 40
    rows[0] = json.dumps(payload, sort_keys=True)
    first.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source commit"):
        validate_run_artifacts(root, require_formal=False)

    rows[0] = original_row
    first.write_text("\n".join(rows) + "\n", encoding="utf-8")
    audit_path = root / evaluation["audit_reference"]
    audit_rows = audit_path.read_text(encoding="utf-8").splitlines()
    audit_payload = json.loads(audit_rows[0])
    audit_payload["adapted_utility"] = 0.123
    audit_rows[0] = json.dumps(audit_payload, sort_keys=True)
    audit_path.write_text("\n".join(audit_rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="audit utility mismatch"):
        validate_run_artifacts(root, require_formal=False)
