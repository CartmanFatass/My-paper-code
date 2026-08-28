from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import hmasd_state


def research_state() -> dict[str, object]:
    return {
        "direction": "example_direction", "role": "EM", "revision": 1,
        "updated_at": "2026-08-28T00:00:00Z", "milestone": "SCOPE_FROZEN",
        "status": "ACTIVE", "completed_summary": "Question and comparator frozen.",
        "refs": ["docs/research/candidates/example_direction/DIRECTION.md"],
        "blockers": [], "reentry_condition": None, "next_action": "Acquire primary evidence.",
        "claim_ceiling": "Mechanism hypothesis only.", "next_discriminator": "Matched comparator.",
        "research_cycle": {
            "label": "mechanism-r01", "opened_at": "2026-08-28T00:00:00Z",
            "reason": "New mechanism", "pro_innovator": {"status": "PENDING", "response": None},
            "pro_convergence": {"status": "PENDING", "response": None},
        },
    }


def engineering_state() -> dict[str, object]:
    return {
        "direction": "example_direction", "role": "CM", "revision": 1,
        "updated_at": "2026-08-28T00:00:00Z", "milestone": "CANDIDATE_READY",
        "status": "ACTIVE", "completed_summary": "Candidate and focused tests are ready.",
        "refs": ["experiments/candidates/example_direction/model.py"], "blockers": [],
        "reentry_condition": None, "next_action": "Run independent review.",
        "worktree": None, "branch": "main",
        "changed_paths": ["experiments/candidates/example_direction/model.py"],
        "verification_summary": "Focused tests passed.", "run": None,
    }


@pytest.mark.parametrize("kind,factory", [("research", research_state), ("engineering", engineering_state)])
def test_minimal_state_validation_rejects_unknown_fields(kind: str, factory) -> None:
    document = factory()
    assert hmasd_state.validate_document(kind, document) == document
    document["message_id"] = "legacy"
    with pytest.raises(hmasd_state.StateError):
        hmasd_state.validate_document(kind, document)


def test_waiting_requires_reentry_condition() -> None:
    document = research_state()
    document["status"] = "WAITING"
    document["blockers"] = ["Paper unavailable"]
    with pytest.raises(hmasd_state.StateError, match="reentry_condition"):
        hmasd_state.validate_document("research", document)


@pytest.mark.parametrize("kind,factory", [("research", research_state), ("engineering", engineering_state)])
def test_cancelled_is_terminal_without_reentry(kind: str, factory) -> None:
    document = factory()
    document["status"] = "CANCELLED"
    document["completed_summary"] = "Cancelled by direct CONTROL after Effects became terminal."
    assert hmasd_state.validate_document(kind, document) == document
    document["reentry_condition"] = "A replacement arrives"
    with pytest.raises(hmasd_state.StateError, match="null reentry_condition"):
        hmasd_state.validate_document(kind, document)


def test_update_creates_then_increments_one_current_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    first = hmasd_state.update_state(
        "research", path, "EM", research_state(), root=tmp_path
    )
    assert first["revision"] == 1
    second = hmasd_state.update_state(
        "research", path, "EM", research_state(), root=tmp_path
    )
    assert second["revision"] == 2


def test_cancelled_engineering_slice_can_start_fresh_scope(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/engineering/state.json"
    cancelled = engineering_state()
    cancelled["status"] = "CANCELLED"
    cancelled["completed_summary"] = "Cancelled after Effects became terminal."
    hmasd_state.update_state("engineering", path, "CM", cancelled, root=tmp_path)
    restarted = engineering_state()
    restarted["milestone"] = "SCOPE_FROZEN"
    restarted["completed_summary"] = "A distinct replacement WORK was frozen."
    updated = hmasd_state.update_state("engineering", path, "CM", restarted, root=tmp_path)
    assert updated["revision"] == 2
    assert updated["milestone"] == "SCOPE_FROZEN"


def test_cli_refuses_shadow_state_outside_repository_root(tmp_path: Path) -> None:
    outside = tmp_path / "shadow/docs/research/candidates/example_direction/workflow/research/state.json"
    incoming = tmp_path / "incoming.json"
    incoming.write_text(json.dumps(research_state()), encoding="utf-8")
    refused = subprocess.run(
        [
            sys.executable, "scripts/hmasd_state.py", "update", "--kind", "research",
            "--path", str(outside), "--writer", "EM", "--input", str(incoming),
        ],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
    )
    assert refused.returncode == 2
    assert not outside.exists()


def test_material_cycle_requires_pro_reviews_before_later_milestones() -> None:
    document = research_state()
    document["milestone"] = "HANDOFF_READY"
    document["status"] = "COMPLETE"
    with pytest.raises(hmasd_state.StateError, match="Pro Innovator"):
        hmasd_state.validate_document("research", document)


def test_same_cycle_cannot_regress_pro_status_or_milestone(tmp_path: Path) -> None:
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": "docs/research/candidates/example_direction/external/pro.md"
    }
    current["milestone"] = "SYNTHESIS_READY"
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(current), encoding="utf-8")
    regressed = research_state()
    with pytest.raises(hmasd_state.StateError, match="cannot regress"):
        hmasd_state.update_state("research", path, "EM", regressed, root=tmp_path)


def test_convergence_cannot_start_before_synthesis_ready() -> None:
    document = research_state()
    document["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": "external/pro-innovator.md"
    }
    document["research_cycle"]["pro_convergence"] = {
        "status": "COMPLETE", "response": "external/pro-convergence.md"
    }
    with pytest.raises(hmasd_state.StateError, match="before SYNTHESIS_READY"):
        hmasd_state.validate_document("research", document)
