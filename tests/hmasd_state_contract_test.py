from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import jsonschema

from scripts import hmasd_state


def research_state() -> dict[str, object]:
    return {
        "direction": "example_direction", "role": "EM", "revision": 1,
        "updated_at": "2026-08-28T00:00:00Z", "milestone": "SCOPE_FROZEN",
        "snapshot_state": "WORKING", "completed_summary": "Question and comparator frozen.",
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
        "snapshot_state": "WORKING", "completed_summary": "Candidate and focused tests are ready.",
        "refs": ["experiments/candidates/example_direction/model.py"], "blockers": [],
        "reentry_condition": None, "next_action": "Run independent review.",
        "worktree": None, "branch": "main",
        "changed_paths": ["experiments/candidates/example_direction/model.py"],
        "verification_summary": "Focused tests passed.", "run": None,
    }


def test_research_schema_binds_response_to_complete_status() -> None:
    schema = json.loads(
        Path("scripts/schemas/hmasd_research_state.schema.json").read_text(encoding="utf-8")
    )
    complete = research_state()
    complete["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": "docs/research/pro.md",
    }
    jsonschema.validate(complete, schema)

    missing_response = research_state()
    missing_response["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": None,
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing_response, schema)

    premature_response = research_state()
    premature_response["research_cycle"]["pro_innovator"] = {
        "status": "PENDING", "response": "docs/research/pro.md",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(premature_response, schema)


@pytest.mark.parametrize("kind,factory", [("research", research_state), ("engineering", engineering_state)])
def test_minimal_state_validation_rejects_unknown_fields(kind: str, factory) -> None:
    document = factory()
    assert hmasd_state.validate_document(kind, document) == document
    document["message_id"] = "legacy"
    with pytest.raises(hmasd_state.StateError):
        hmasd_state.validate_document(kind, document)


def test_waiting_requires_reentry_condition() -> None:
    document = research_state()
    document["snapshot_state"] = "WAITING_REENTRY"
    document["blockers"] = ["Paper unavailable"]
    with pytest.raises(hmasd_state.StateError, match="reentry_condition"):
        hmasd_state.validate_document("research", document)


@pytest.mark.parametrize("kind,factory", [("research", research_state), ("engineering", engineering_state)])
def test_terminal_gap_is_not_assignment_cancellation(kind: str, factory) -> None:
    document = factory()
    document["snapshot_state"] = "TERMINAL_GAP"
    document["completed_summary"] = "Current slice stopped before the next milestone."
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


def test_terminal_engineering_gap_can_start_fresh_scope(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/engineering/state.json"
    stopped = engineering_state()
    stopped["snapshot_state"] = "TERMINAL_GAP"
    stopped["completed_summary"] = "Current slice stopped before the next milestone."
    hmasd_state.update_state("engineering", path, "CM", stopped, root=tmp_path)
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
    document["snapshot_state"] = "COMPLETE"
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


@pytest.mark.parametrize(
    "status",
    [
        "PENDING", "ZERO_SEND_FAILED", "COMMITMENT_UNKNOWN", "SENT_WAITING",
        "COMPLETE", "SENT_UNREADABLE", "WAIVED",
    ],
)
def test_research_state_accepts_every_pro_operation_fact(status: str) -> None:
    document = research_state()
    document["research_cycle"]["pro_innovator"] = {
        "status": status,
        "response": "external/pro-innovator.md" if status == "COMPLETE" else None,
    }
    assert hmasd_state.validate_document("research", document) == document


def test_unknown_or_sent_pro_operation_never_regresses_to_zero_send(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {
        "status": "COMMITMENT_UNKNOWN", "response": None,
    }
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    regressed = research_state()
    regressed["research_cycle"]["pro_innovator"] = {
        "status": "ZERO_SEND_FAILED", "response": None,
    }
    with pytest.raises(hmasd_state.StateError, match="cannot regress"):
        hmasd_state.update_state("research", path, "EM", regressed, root=tmp_path)


def test_sent_unreadable_can_only_remain_or_become_complete(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {
        "status": "SENT_UNREADABLE", "response": None,
    }
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    completed = research_state()
    completed["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": "external/pro-innovator.md",
    }
    updated = hmasd_state.update_state("research", path, "EM", completed, root=tmp_path)
    assert updated["research_cycle"]["pro_innovator"]["status"] == "COMPLETE"


@pytest.mark.parametrize("initial", ["PENDING", "ZERO_SEND_FAILED"])
def test_send_can_be_observed_directly_as_unreadable_without_fake_intermediate_snapshot(
    tmp_path: Path, initial: str
) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {"status": initial, "response": None}
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    unreadable = research_state()
    unreadable["research_cycle"]["pro_innovator"] = {
        "status": "SENT_UNREADABLE", "response": None,
    }
    updated = hmasd_state.update_state("research", path, "EM", unreadable, root=tmp_path)
    assert updated["research_cycle"]["pro_innovator"]["status"] == "SENT_UNREADABLE"


@pytest.mark.parametrize("unresolved", ["COMMITMENT_UNKNOWN", "SENT_WAITING", "SENT_UNREADABLE"])
def test_new_cycle_cannot_discard_an_unresolved_sent_operation(
    tmp_path: Path, unresolved: str
) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {"status": unresolved, "response": None}
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    replacement = research_state()
    replacement["research_cycle"] = {
        "label": "mechanism-r02",
        "opened_at": "2026-08-28T01:00:00Z",
        "reason": "Replacement mechanism",
        "pro_innovator": {"status": "PENDING", "response": None},
        "pro_convergence": {"status": "PENDING", "response": None},
    }
    with pytest.raises(hmasd_state.StateError, match="unresolved external operation"):
        hmasd_state.update_state("research", path, "EM", replacement, root=tmp_path)
