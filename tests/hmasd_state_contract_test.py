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


@pytest.mark.parametrize(
    "kind,factory,schema_name",
    [
        ("research", research_state, "hmasd_research_state.schema.json"),
        ("engineering", engineering_state, "hmasd_engineering_state.schema.json"),
    ],
)
def test_waiting_reentry_contract_matches_json_schema(
    kind: str, factory, schema_name: str
) -> None:
    schema = json.loads(
        (Path("scripts/schemas") / schema_name).read_text(encoding="utf-8")
    )
    waiting = factory()
    waiting["snapshot_state"] = "WAITING_REENTRY"
    waiting["blockers"] = ["External condition is not ready."]
    with pytest.raises(hmasd_state.StateError, match="reentry_condition"):
        hmasd_state.validate_document(kind, waiting)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(waiting, schema)

    waiting["reentry_condition"] = "The exact external condition becomes observable."
    assert hmasd_state.validate_document(kind, waiting) == waiting
    jsonschema.validate(waiting, schema)

    working = factory()
    working["reentry_condition"] = "A condition that must not exist for WORKING."
    with pytest.raises(hmasd_state.StateError, match="null reentry_condition"):
        hmasd_state.validate_document(kind, working)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(working, schema)


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


def test_terminal_engineering_snapshot_cannot_reopen_without_fresh_scope(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/engineering/state.json"
    completed = engineering_state()
    completed["milestone"] = "RUN_OR_HANDOFF_READY"
    completed["snapshot_state"] = "COMPLETE"
    hmasd_state.update_state("engineering", path, "CM", completed, root=tmp_path)

    reopened = engineering_state()
    reopened["milestone"] = "RUN_OR_HANDOFF_READY"
    with pytest.raises(hmasd_state.StateError, match="terminal snapshot"):
        hmasd_state.update_state("engineering", path, "CM", reopened, root=tmp_path)

    replacement = engineering_state()
    replacement["milestone"] = "SCOPE_FROZEN"
    updated = hmasd_state.update_state(
        "engineering", path, "CM", replacement, root=tmp_path
    )
    assert updated["snapshot_state"] == "WORKING"


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


@pytest.mark.parametrize("snapshot_state", ["TERMINAL_GAP", "COMPLETE"])
@pytest.mark.parametrize(
    "transport_state", ["COMMITMENT_UNKNOWN", "SENT_WAITING", "SENT_UNREADABLE"]
)
def test_research_terminal_snapshot_rejects_unresolved_transport(
    snapshot_state: str, transport_state: str
) -> None:
    document = research_state()
    document["snapshot_state"] = snapshot_state
    if snapshot_state == "COMPLETE":
        document["milestone"] = "HANDOFF_READY"
    document["research_cycle"]["pro_innovator"] = {
        "status": transport_state,
        "response": None,
    }
    with pytest.raises(hmasd_state.StateError, match="unresolved Pro"):
        hmasd_state.validate_document("research", document)
    schema = json.loads(
        Path("scripts/schemas/hmasd_research_state.schema.json").read_text(
            encoding="utf-8"
        )
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)


@pytest.mark.parametrize("snapshot_state", ["TERMINAL_GAP", "COMPLETE"])
@pytest.mark.parametrize("run_status", ["RUNNING", "UNKNOWN"])
def test_engineering_terminal_snapshot_rejects_run_without_terminal_witness(
    snapshot_state: str, run_status: str
) -> None:
    document = engineering_state()
    document["snapshot_state"] = snapshot_state
    if snapshot_state == "COMPLETE":
        document["milestone"] = "RUN_OR_HANDOFF_READY"
    document["run"] = {
        "run_id": "run-01",
        "status": run_status,
        "manifest": "temp/directions/example_direction/test/run-01/manifest.json",
        "result": None,
    }
    with pytest.raises(hmasd_state.StateError, match="terminal run witness"):
        hmasd_state.validate_document("engineering", document)
    schema = json.loads(
        Path("scripts/schemas/hmasd_engineering_state.schema.json").read_text(
            encoding="utf-8"
        )
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)


@pytest.mark.parametrize(
    "kind,factory,final_milestone,schema_name",
    [
        (
            "research",
            research_state,
            "HANDOFF_READY",
            "hmasd_research_state.schema.json",
        ),
        (
            "engineering",
            engineering_state,
            "RUN_OR_HANDOFF_READY",
            "hmasd_engineering_state.schema.json",
        ),
    ],
)
def test_complete_snapshot_requires_final_milestone(
    kind: str, factory, final_milestone: str, schema_name: str
) -> None:
    document = factory()
    document["snapshot_state"] = "COMPLETE"
    with pytest.raises(hmasd_state.StateError, match="final milestone"):
        hmasd_state.validate_document(kind, document)
    schema = json.loads(
        (Path("scripts/schemas") / schema_name).read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)

    document["milestone"] = final_milestone
    if kind == "research":
        for field in ("pro_innovator", "pro_convergence"):
            document["research_cycle"][field] = {
                "status": "WAIVED",
                "response": None,
            }
    assert hmasd_state.validate_document(kind, document) == document
    jsonschema.validate(document, schema)


@pytest.mark.parametrize(
    "milestone", ["SCOPE_FROZEN", "SYNTHESIS_READY", "REVIEW_RESOLVED", "HANDOFF_READY"]
)
def test_research_snapshot_requires_a_material_cycle(milestone: str) -> None:
    document = research_state()
    document["milestone"] = milestone
    document["research_cycle"] = None
    with pytest.raises(hmasd_state.StateError, match="research_cycle fields are invalid"):
        hmasd_state.validate_document("research", document)
    schema = json.loads(
        Path("scripts/schemas/hmasd_research_state.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)


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


def test_terminal_research_snapshot_can_only_reopen_as_fresh_cycle(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    completed = research_state()
    completed["milestone"] = "HANDOFF_READY"
    completed["snapshot_state"] = "COMPLETE"
    for field in ("pro_innovator", "pro_convergence"):
        completed["research_cycle"][field] = {"status": "WAIVED", "response": None}
    hmasd_state.update_state("research", path, "EM", completed, root=tmp_path)

    reopened = dict(completed)
    reopened["snapshot_state"] = "WORKING"
    with pytest.raises(hmasd_state.StateError, match="terminal snapshot"):
        hmasd_state.update_state("research", path, "EM", reopened, root=tmp_path)

    replacement = research_state()
    replacement["research_cycle"] = {
        "label": "mechanism-r02",
        "opened_at": "2026-08-28T01:00:00Z",
        "reason": "A successor WORK opened a fresh material cycle.",
        "pro_innovator": {"status": "PENDING", "response": None},
        "pro_convergence": {"status": "PENDING", "response": None},
    }
    updated = hmasd_state.update_state(
        "research", path, "EM", replacement, root=tmp_path
    )
    assert updated["snapshot_state"] == "WORKING"
    assert updated["research_cycle"]["label"] == "mechanism-r02"


@pytest.mark.parametrize(
    "kind,factory", [("research", research_state), ("engineering", engineering_state)]
)
def test_waiting_reentry_resumes_same_work(kind: str, factory, tmp_path: Path) -> None:
    path = (
        tmp_path
        / f"docs/research/candidates/example_direction/workflow/{kind}/state.json"
    )
    waiting = factory()
    waiting["snapshot_state"] = "WAITING_REENTRY"
    waiting["blockers"] = ["The exact reentry condition is not yet true."]
    waiting["reentry_condition"] = "The exact reentry condition becomes true."
    hmasd_state.update_state(kind, path, waiting["role"], waiting, root=tmp_path)

    resumed = factory()
    updated = hmasd_state.update_state(
        kind, path, resumed["role"], resumed, root=tmp_path
    )
    assert updated["snapshot_state"] == "WORKING"


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
        "COMPLETE", "SENT_INPUT_MISMATCH", "SENT_UNREADABLE", "WAIVED",
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


@pytest.mark.parametrize(
    "initial", ["PENDING", "COMMITMENT_UNKNOWN", "SENT_WAITING", "SENT_UNREADABLE"]
)
def test_confirmed_send_can_resolve_to_terminal_input_mismatch(
    tmp_path: Path, initial: str
) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {"status": initial, "response": None}
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    mismatch = research_state()
    mismatch["research_cycle"]["pro_innovator"] = {
        "status": "SENT_INPUT_MISMATCH", "response": None,
    }
    updated = hmasd_state.update_state("research", path, "EM", mismatch, root=tmp_path)
    assert updated["research_cycle"]["pro_innovator"]["status"] == "SENT_INPUT_MISMATCH"


def test_terminal_input_mismatch_cannot_change_within_operation(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {
        "status": "SENT_INPUT_MISMATCH", "response": None,
    }
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    completed = research_state()
    completed["research_cycle"]["pro_innovator"] = {
        "status": "COMPLETE", "response": "external/pro-innovator.md",
    }
    with pytest.raises(hmasd_state.StateError, match="cannot regress"):
        hmasd_state.update_state("research", path, "EM", completed, root=tmp_path)


def test_new_cycle_can_replace_terminal_input_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "docs/research/candidates/example_direction/workflow/research/state.json"
    current = research_state()
    current["research_cycle"]["pro_innovator"] = {
        "status": "SENT_INPUT_MISMATCH", "response": None,
    }
    hmasd_state.update_state("research", path, "EM", current, root=tmp_path)
    replacement = research_state()
    replacement["research_cycle"] = {
        "label": "mechanism-r02",
        "opened_at": "2026-08-28T01:00:00Z",
        "reason": "Fresh work after terminal transport repair",
        "pro_innovator": {"status": "PENDING", "response": None},
        "pro_convergence": {"status": "PENDING", "response": None},
    }
    updated = hmasd_state.update_state("research", path, "EM", replacement, root=tmp_path)
    assert updated["research_cycle"]["label"] == "mechanism-r02"


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
