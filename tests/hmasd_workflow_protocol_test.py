"""Typed agent-result binding tests for the event-local workflow planner."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import hmasd_work_packet as packets


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _packet_input(repo: Path, direction: str = "alpha") -> dict[str, Any]:
    root = repo / "docs" / "research" / "candidates" / direction
    _write_json(root / "STATE.json", {"revision": 7, "direction": direction})
    _write_json(root / "DIRECTION.json", {"revision": 3, "direction": direction})
    return {
        "schema_version": 1,
        "scope_ref": {
            "path": f"docs/research/candidates/{direction}/STATE.json",
            "revision": 7,
        },
        "sender_identity": "Portfolio",
        "target_identity": f"EM-{direction}",
        "authority_refs": [
            {
                "path": f"docs/research/candidates/{direction}/DIRECTION.json",
                "revision": 3,
            }
        ],
        "objective": "advance one bounded discriminator",
        "non_goals": ["do not change shared core"],
        "owned_paths": [f"experiments/candidates/{direction}"],
        "done_criteria": ["return one typed result"],
        "effect_refs": [],
    }


def _setup(repo: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    packet = packets.build_packet(_packet_input(repo), repo=repo)
    packets.publish_packet(packet, repo=repo)
    observed = [
        {
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-alpha",
        }
    ]
    return packet, observed


def _result(packet: dict[str, Any], kind: str = "NONE") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": "EM-alpha",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Completed the bounded scientific slice.",
        "changed_paths": ["experiments/candidates/alpha/result.json"],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": kind, "input_refs": []},
        "payload": {
            "kind": "em",
            "direction_id": "alpha",
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [],
            "engineering_request_ref": None,
        },
    }


def _draft(repo: Path, target: str) -> dict[str, Any]:
    scope_path = "docs/research/candidates/alpha/NEXT.json"
    _write_json(repo / scope_path, {"revision": 1, "direction": "alpha"})
    return {
        "schema_version": 1,
        "scope_ref": {"path": scope_path, "revision": 1},
        "sender_identity": "EM-alpha",
        "target_identity": target,
        "authority_refs": [],
        "objective": "continue through one typed responsibility request",
        "non_goals": ["do not execute transport in the planner"],
        "owned_paths": ["docs/research/candidates/alpha/NEXT.json"],
        "done_criteria": ["return one typed result"],
        "effect_refs": [],
    }


def _bind(
    repo: Path,
    packet: dict[str, Any],
    observed: list[dict[str, Any]],
    result: dict[str, Any],
    draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = copy.deepcopy(result)
    if (
        draft is not None
        and result.get("next_action", {}).get("kind", "").startswith("REQUEST_")
        and result["next_action"].get("input_refs") == []
    ):
        try:
            result["next_action"]["input_refs"] = [packets.packet_id(draft)]
        except packets.WorkPacketError:
            pass
    return packets.reconcile_once(
        repo=repo,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=result,
        next_packet_draft=draft,
    )["plan"]


def _assert_defect(
    plan: dict[str, Any], code: str, field_path: str, *, expected_ref: Any = None
) -> None:
    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == code
    assert plan["defect"]["field_path"] == field_path
    assert set(plan["defect"]) == {
        "code",
        "field_path",
        "expected",
        "actual",
        "ref",
        "failure_scope",
        "producing_command",
        "responsible_owner",
    }
    assert plan["defect"]["ref"] == expected_ref
    assert plan["defect"]["producing_command"] == "hmasd_work_packet.reconcile_once"
    assert plan["defect"]["responsible_owner"] == "Root"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("assignment_id", "wrong-assignment", "ASSIGNMENT_ID_MISMATCH"),
        ("logical_identity", "EM-beta", "RESULT_IDENTITY_MISMATCH"),
        ("generation", 2, "RESULT_GENERATION_MISMATCH"),
    ],
)
def test_result_binding_rejects_assignment_identity_and_generation_mismatch(
    tmp_path: Path, field: str, value: Any, code: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)
    result[field] = value
    if field == "logical_identity":
        result["payload"]["direction_id"] = "beta"
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, code, field)


@pytest.mark.parametrize(
    ("changed_paths", "code"),
    [
        (["experiments/candidates/beta/result.json"], "CHANGED_PATH_OUTSIDE_OWNERSHIP"),
        (
            [
                "experiments/candidates/alpha/result.json",
                "experiments/candidates/alpha/result.json",
            ],
            "DUPLICATE_CHANGED_PATH",
        ),
    ],
)
def test_result_binding_rejects_path_escape_and_duplicates(
    tmp_path: Path, changed_paths: list[str], code: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)
    result["changed_paths"] = changed_paths
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, code, "changed_paths")


def test_result_binding_rejects_windows_case_alias_duplicates(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)
    result["changed_paths"] = [
        "experiments/candidates/alpha/Result.py",
        "experiments/candidates/alpha/result.py",
    ]

    plan = _bind(tmp_path, packet, observed, result)

    _assert_defect(plan, "DUPLICATE_CHANGED_PATH", "changed_paths")


def test_bare_blocked_result_is_a_precise_schema_defect(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "WAIT_FOR_REF")
    result["status"] = "BLOCKED"
    result["next_action"]["input_refs"] = ["missing-ref"]
    plan = _bind(tmp_path, packet, observed, result)
    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == "INVALID_AGENT_RESULT"
    assert plan["defect"]["field_path"] in {"failure_scope", "failure_ref"}


def test_scoped_blocked_wait_result_is_accepted(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "WAIT_FOR_REF")
    result.update(
        {
            "status": "BLOCKED",
            "failure_scope": "direction",
            "failure_ref": "docs/research/candidates/alpha/DIRECTION.md",
        }
    )
    result["next_action"]["input_refs"] = ["missing-ref"]
    plan = _bind(tmp_path, packet, observed, result)
    assert plan["verb"] == "WAIT_FOR_REF"
    assert plan["input_refs"] == ["missing-ref"]


def test_protocol_closes_next_action_kind_without_closing_global_schema(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "MODEL_INVENTED_GATE")
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, "UNSUPPORTED_NEXT_ACTION", "next_action.kind")


def test_next_packet_draft_without_agent_result_is_a_precise_defect(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        next_packet_draft=_draft(tmp_path, "CM-alpha"),
    )["plan"]
    _assert_defect(plan, "AGENT_RESULT_REQUIRED", "agent_result")


@pytest.mark.parametrize(
    ("kind", "with_draft", "code"),
    [
        ("REQUEST_CM_ENGINEERING", False, "NEXT_PACKET_DRAFT_REQUIRED"),
        ("NONE", True, "NEXT_PACKET_DRAFT_FORBIDDEN"),
        ("RESUME_SAME_SLICE", True, "NEXT_PACKET_DRAFT_FORBIDDEN"),
        ("WAIT_FOR_REF", True, "NEXT_PACKET_DRAFT_FORBIDDEN"),
    ],
)
def test_next_packet_draft_presence_is_exact(
    tmp_path: Path, kind: str, with_draft: bool, code: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, kind)
    if kind == "WAIT_FOR_REF":
        result["status"] = "PARTIAL"
        result["next_action"]["input_refs"] = ["missing-ref"]
    elif kind == "RESUME_SAME_SLICE":
        result["status"] = "PARTIAL"
    draft = _draft(tmp_path, "CM-alpha") if with_draft else None
    plan = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(plan, code, "next_packet_draft")


@pytest.mark.parametrize(
    "missing",
    [
        "schema_version",
        "scope_ref",
        "sender_identity",
        "target_identity",
        "authority_refs",
        "objective",
        "non_goals",
        "owned_paths",
        "done_criteria",
        "effect_refs",
    ],
)
def test_request_draft_reports_every_missing_packet_field(
    tmp_path: Path, missing: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    draft = _draft(tmp_path, "CM-alpha")
    draft.pop(missing)
    plan = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(plan, "INVALID_NEXT_PACKET_DRAFT", f"next_packet_draft.{missing}")


@pytest.mark.parametrize(
    ("kind", "target"),
    [
        ("REQUEST_PORTFOLIO_DECISION", "Portfolio"),
        ("REQUEST_EM_DECISION", "EM-alpha"),
        ("REQUEST_CM_ENGINEERING", "CM-alpha"),
        ("REQUEST_ROOT_ACTION", "Root"),
    ],
)
def test_request_actions_emit_canonical_publish_packet_intent_without_mutation(
    tmp_path: Path, kind: str, target: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, kind)
    draft = _draft(tmp_path, target)
    ready = tmp_path / ".codex" / "runtime" / "work" / "ready"
    before = sorted(path.relative_to(tmp_path).as_posix() for path in ready.rglob("*"))

    plan = _bind(tmp_path, packet, observed, result, draft)

    assert plan["verb"] == "PUBLISH_PACKET_INTENT"
    assert plan["packet"] == packets.build_packet(draft, repo=tmp_path)
    assert plan["next_work_id"] == plan["packet"]["work_id"]
    assert plan["next_target_identity"] == target
    assert "target_identity" not in plan
    assert "task_resolution" not in plan
    after = sorted(path.relative_to(tmp_path).as_posix() for path in ready.rglob("*"))
    assert after == before


@pytest.mark.parametrize(
    ("kind", "target", "field_path"),
    [
        ("REQUEST_EM_DECISION", "EM-beta", "next_packet_draft.target_identity"),
        ("REQUEST_CM_ENGINEERING", "CM-beta", "next_packet_draft.target_identity"),
        ("REQUEST_ROOT_ACTION", "Portfolio", "next_packet_draft.target_identity"),
    ],
)
def test_request_draft_rejects_wrong_or_cross_direction_target(
    tmp_path: Path, kind: str, target: str, field_path: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, kind)
    draft = _draft(tmp_path, target)
    plan = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(plan, "NEXT_PACKET_TARGET_MISMATCH", field_path)


def test_request_draft_cannot_route_an_ordinary_packet_to_workflow_clerk(
    tmp_path: Path,
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "REQUEST_ROOT_ACTION")
    draft = _draft(tmp_path, "Workflow-Clerk")

    plan = _bind(tmp_path, packet, observed, result, draft)

    _assert_defect(
        plan,
        "ORDINARY_PACKET_CLERK_TARGET",
        "next_packet_draft.target_identity",
    )
    assert plan["verb"] == "CONFLICT"


def test_request_draft_rejects_stale_authority_and_wrong_sender(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    draft = _draft(tmp_path, "CM-alpha")
    draft["sender_identity"] = "Root"
    wrong_sender = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(wrong_sender, "NEXT_PACKET_SENDER_MISMATCH", "next_packet_draft.sender_identity")

    draft["sender_identity"] = "EM-alpha"
    _write_json(tmp_path / draft["scope_ref"]["path"], {"revision": 2})
    stale = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(stale, "STALE_NEXT_PACKET_AUTHORITY", "next_packet_draft.scope_ref")


def test_request_draft_effects_are_validated_without_execution(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    draft = _draft(tmp_path, "CM-alpha")
    effect_path = "temp/directions/example-direction/exp/example-run/manifest.json"
    draft["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": effect_path,
            "resource_id": "example-direction/example-run",
        }
    ]

    missing = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(
        missing,
        "EFFECT_DOCUMENT_UNAVAILABLE",
        "next_packet_draft.effect_refs[0]",
        expected_ref=draft["effect_refs"][0],
    )
    assert str(tmp_path) not in json.dumps(missing)

    (tmp_path / effect_path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / effect_path).write_text('{"status":', encoding="utf-8")
    invalid = _bind(tmp_path, packet, observed, result, draft)
    _assert_defect(
        invalid,
        "INVALID_EFFECT_DOCUMENT",
        "next_packet_draft.effect_refs[0]",
        expected_ref=draft["effect_refs"][0],
    )

    manifest = json.loads(
        (Path(__file__).parent / "fixtures/hmasd_phase0/run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    manifest["status"] = "UNKNOWN"
    _write_json(tmp_path / effect_path, manifest)
    unknown = _bind(tmp_path, packet, observed, result, draft)
    assert unknown["verb"] == "OBSERVE_EFFECT_ONLY"
    assert unknown["unknown_effect_refs"] == [effect_path]
    assert not (
        tmp_path
        / ".codex"
        / "runtime"
        / "work"
        / "ready"
        / packets.packet_id(draft)
    ).exists()


def test_result_can_bind_only_a_reused_task(tmp_path: Path) -> None:
    packet, _ = _setup(tmp_path)
    plan = _bind(tmp_path, packet, [], _result(packet))
    _assert_defect(plan, "RESULT_TASK_NOT_REUSED", "task_resolution.status")


@pytest.mark.parametrize(
    ("kind", "status", "expected_verb"),
    [
        ("NONE", "COMPLETED", "NOOP_TERMINAL"),
        ("RESUME_SAME_SLICE", "PARTIAL", "DISPATCH_EXISTING"),
    ],
)
def test_nonrequest_result_verbs_are_pure(
    tmp_path: Path, kind: str, status: str, expected_verb: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, kind)
    result["status"] = status
    plan = _bind(tmp_path, packet, observed, result)
    assert plan["verb"] == expected_verb


def test_unknown_effect_and_identity_conflict_keep_stage_a_priority(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    effect_path = "temp/directions/example-direction/exp/example-run/manifest.json"
    manifest = json.loads(
        (Path(__file__).parent / "fixtures/hmasd_phase0/run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    manifest["status"] = "UNKNOWN"
    _write_json(tmp_path / effect_path, manifest)
    source["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": effect_path,
            "resource_id": "example-direction/example-run",
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    invalid_result = {"not": "an agent result"}
    observed = _setup(tmp_path)[1]
    unknown = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=invalid_result,
    )["plan"]
    assert unknown["verb"] == "OBSERVE_EFFECT_ONLY"

    duplicate = [*observed, {**observed[0], "lifecycle": "WAITING"}]
    conflict = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=duplicate,
        agent_result=invalid_result,
    )["plan"]
    assert conflict["verb"] == "CONFLICT"
    assert conflict["conflict_type"] == "TASK_IDENTITY_CONFLICT"


def test_published_intent_is_reconciled_only_by_a_later_exact_wake(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    intent = _bind(tmp_path, packet, observed, result, _draft(tmp_path, "CM-alpha"))
    next_packet = intent["packet"]

    packets.publish_packet(next_packet, repo=tmp_path)
    later = packets.reconcile_once(
        repo=tmp_path,
        work_id=next_packet["work_id"],
        observed_tasks=[],
    )["plan"]
    assert later["verb"] == "CREATE_TASK_INTENT"
    assert later["work_id"] == next_packet["work_id"]


def test_protocol_cli_is_byte_identical_for_same_typed_inputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet, _ = _setup(tmp_path)
    snapshot = tmp_path / ".codex" / "runtime" / "tasks.json"
    result_path = tmp_path / "agent-result.json"
    draft_path = tmp_path / "next-packet.json"
    _write_json(snapshot, {"tasks": _setup(tmp_path)[1]})
    draft = _draft(tmp_path, "CM-alpha")
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    result["next_action"]["input_refs"] = [packets.packet_id(draft)]
    _write_json(result_path, result)
    _write_json(draft_path, draft)
    argv = [
        "reconcile",
        "--once",
        "--repo",
        str(tmp_path),
        "--work-id",
        packet["work_id"],
        "--observed-tasks",
        ".codex/runtime/tasks.json",
        "--agent-result",
        str(result_path),
        "--next-packet-draft",
        str(draft_path),
    ]

    assert packets.main(argv) == 0
    first = capsys.readouterr().out.encode()
    assert packets.main(argv) == 0
    second = capsys.readouterr().out.encode()
    assert first == second
    assert str(tmp_path).encode() not in first
    assert json.loads(first)["plan"]["verb"] == "PUBLISH_PACKET_INTENT"


def test_protocol_cli_defect_is_byte_identical_and_host_path_free(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet, observed = _setup(tmp_path)
    snapshot = tmp_path / ".codex" / "runtime" / "tasks.json"
    result_path = tmp_path / "invalid-agent-result.json"
    invalid = _result(packet)
    invalid["assignment_id"] = "wrong-assignment"
    _write_json(snapshot, {"tasks": observed})
    _write_json(result_path, invalid)
    argv = [
        "reconcile",
        "--once",
        "--repo",
        str(tmp_path),
        "--work-id",
        packet["work_id"],
        "--observed-tasks",
        ".codex/runtime/tasks.json",
        "--agent-result",
        str(result_path),
    ]

    assert packets.main(argv) == 0
    first = capsys.readouterr().out.encode()
    assert packets.main(argv) == 0
    second = capsys.readouterr().out.encode()
    assert first == second
    assert str(tmp_path).encode() not in first
    assert json.loads(first)["plan"]["defect"]["code"] == "ASSIGNMENT_ID_MISMATCH"


def test_next_packet_self_cycle_is_rejected(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    source["sender_identity"] = "EM-alpha"
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    result = _result(packet, "REQUEST_EM_DECISION")
    result["next_action"]["input_refs"] = [packet["work_id"]]
    plan = _bind(tmp_path, packet, _setup(tmp_path)[1], result, copy.deepcopy(source))
    _assert_defect(plan, "NEXT_PACKET_SELF_CYCLE", "next_packet_draft.work_id")


def test_one_result_cannot_bind_two_distinct_drafts(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    first_draft = _draft(tmp_path, "CM-alpha")
    second_draft = copy.deepcopy(first_draft)
    second_draft["objective"] = "a distinct second request"
    result = _result(packet, "REQUEST_CM_ENGINEERING")
    result["next_action"]["input_refs"] = [packets.packet_id(first_draft)]

    assert _bind(tmp_path, packet, observed, result, first_draft)["verb"] == "PUBLISH_PACKET_INTENT"
    second = _bind(tmp_path, packet, observed, result, second_draft)
    _assert_defect(second, "NEXT_PACKET_BINDING_MISMATCH", "next_action.input_refs")


def test_result_refs_and_recursive_payload_refs_must_be_fresh(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    state_path = tmp_path / "experiments" / "candidates" / "alpha" / "state.json"
    payload_path = tmp_path / "experiments" / "candidates" / "alpha" / "conclusion.json"
    _write_json(state_path, {"result": 1})
    _write_json(payload_path, {"conclusion": 1})
    state_ref = {
        "path": state_path.relative_to(tmp_path).as_posix(),
        "sha256": packets.hmasd_state.sha256_bytes(state_path.read_bytes()),
    }
    payload_ref = {
        "path": payload_path.relative_to(tmp_path).as_posix(),
        "sha256": packets.hmasd_state.sha256_bytes(payload_path.read_bytes()),
    }
    result = _result(packet)
    result["state_refs"] = [state_ref]
    result["payload"]["conclusion_refs"] = [payload_ref]
    assert _bind(tmp_path, packet, observed, result)["verb"] == "NOOP_TERMINAL"

    _write_json(payload_path, {"conclusion": 2})
    stale = _bind(tmp_path, packet, observed, result)
    _assert_defect(stale, "STALE_RESULT_REF", "payload.conclusion_refs[0]")

    opaque = _result(packet)
    opaque["artifact_refs"] = ["opaque-artifact-name"]
    invalid = _bind(tmp_path, packet, observed, opaque)
    _assert_defect(invalid, "INVALID_AGENT_RESULT", "artifact_refs")


def test_recursive_artifact_payload_ref_must_be_fresh(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    source.update(
        {
            "sender_identity": "EM-alpha",
            "target_identity": "hmasd-research-artifact-writer",
        }
    )
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "hmasd-research-artifact-writer",
            "kind": "artifact",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-artifact-writer",
        }
    ]
    artifact_path = tmp_path / "experiments/candidates/alpha/evidence.json"
    _write_json(artifact_path, {"evidence": 1})
    artifact_ref = {
        "path": artifact_path.relative_to(tmp_path).as_posix(),
        "sha256": packets.hmasd_state.sha256_bytes(artifact_path.read_bytes()),
    }
    result = {
        "schema_version": 1,
        "role": "hmasd-research-artifact-writer",
        "logical_identity": "hmasd-research-artifact-writer",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "LOCAL",
        "summary": "Published one exact artifact.",
        "changed_paths": [artifact_ref["path"]],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {"kind": "artifact", "artifact_refs": [artifact_ref]},
    }
    assert _bind(tmp_path, packet, observed, result)["verb"] == "NOOP_TERMINAL"

    _write_json(artifact_path, {"evidence": 2})
    stale = _bind(tmp_path, packet, observed, result)
    _assert_defect(stale, "STALE_RESULT_REF", "payload.artifact_refs[0]")


def test_portfolio_project_scope_can_request_explicit_direction_manager(tmp_path: Path) -> None:
    scope_path = "docs/research/portfolio/STATE.json"
    _write_json(tmp_path / scope_path, {"revision": 1})
    source = {
        **_packet_input(tmp_path),
        "scope_ref": {"path": scope_path, "revision": 1},
        "sender_identity": "Root",
        "target_identity": "Portfolio",
        "authority_refs": [],
        "owned_paths": ["docs/research/portfolio/PORTFOLIO.md"],
    }
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "Portfolio",
            "kind": "portfolio",
            "generation": 1,
            "lifecycle": "ACTIVE",
            "thread_id": "thread-portfolio",
        }
    ]
    result = {
        **_result(packet, "REQUEST_EM_DECISION"),
        "role": "hmasd-portfolio",
        "logical_identity": "Portfolio",
        "changed_paths": [],
        "payload": {
            "kind": "portfolio",
            "direction_actions": [],
            "portfolio_ref": {
                "path": "docs/research/portfolio/PORTFOLIO.json",
                "sha256": "",
            },
            "registry_revision": 1,
        },
    }
    portfolio_path = tmp_path / result["payload"]["portfolio_ref"]["path"]
    _write_json(portfolio_path, {"decision": "request EM-alpha"})
    result["payload"]["portfolio_ref"]["sha256"] = packets.hmasd_state.sha256_bytes(
        portfolio_path.read_bytes()
    )
    draft = _draft(tmp_path, "EM-alpha")
    draft["sender_identity"] = "Portfolio"
    plan = _bind(tmp_path, packet, observed, result, draft)
    assert plan["verb"] == "PUBLISH_PACKET_INTENT"
    assert plan["next_target_identity"] == "EM-alpha"


@pytest.mark.parametrize(
    ("kind", "identity", "payload"),
    [
        (
            "implementation",
            "hmasd-implementer",
            {
                "kind": "implementation",
                "changed_paths": ["experiments/candidates/alpha/other.py"],
                "preserved_invariants": [],
                "lsp_evidence_refs": [],
            },
        ),
        (
            "git",
            "Root",
            {
                "kind": "git",
                "direction_id": "alpha",
                "base_sha": "a" * 40,
                "candidate_sha": None,
                "integrated_sha": None,
                "changed_paths": ["experiments/candidates/alpha/other.py"],
            },
        ),
    ],
)
def test_payload_changed_paths_must_match_envelope_set(
    tmp_path: Path, kind: str, identity: str, payload: dict[str, Any]
) -> None:
    source = _packet_input(tmp_path)
    source["sender_identity"] = "CM-alpha"
    source["target_identity"] = identity
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": identity,
            "kind": kind,
            "generation": 1,
            "lifecycle": "ACTIVE",
            "thread_id": f"thread-{kind}",
        }
    ]
    result = {
        **_result(packet),
        "role": "hmasd-git-integration" if kind == "git" else "hmasd-implementer",
        "logical_identity": identity,
        "payload": payload,
    }
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, "PAYLOAD_CHANGED_PATHS_MISMATCH", "payload.changed_paths")


def test_payload_changed_paths_reject_windows_case_alias_duplicates(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    source["sender_identity"] = "CM-alpha"
    source["target_identity"] = "hmasd-implementer"
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "hmasd-implementer",
            "kind": "implementation",
            "generation": 1,
            "lifecycle": "ACTIVE",
            "thread_id": "thread-implementation",
        }
    ]
    path = "experiments/candidates/alpha/result.py"
    result = {
        **_result(packet),
        "role": "hmasd-implementer",
        "logical_identity": "hmasd-implementer",
        "changed_paths": [path],
        "payload": {
            "kind": "implementation",
            "changed_paths": [path, "experiments/candidates/alpha/Result.py"],
            "preserved_invariants": [],
            "lsp_evidence_refs": [],
        },
    }

    plan = _bind(tmp_path, packet, observed, result)

    _assert_defect(plan, "DUPLICATE_CHANGED_PATH", "payload.changed_paths")


def test_changed_path_ownership_and_payload_set_use_windows_casefold(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    source.update(
        {
            "sender_identity": "CM-alpha",
            "target_identity": "hmasd-implementer",
            "owned_paths": ["experiments/candidates/alpha/Foo"],
        }
    )
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "hmasd-implementer",
            "kind": "implementation",
            "generation": 1,
            "lifecycle": "ACTIVE",
            "thread_id": "thread-implementation",
        }
    ]
    result = {
        **_result(packet),
        "role": "hmasd-implementer",
        "logical_identity": "hmasd-implementer",
        "changed_paths": ["experiments/candidates/alpha/foo/bar.py"],
        "payload": {
            "kind": "implementation",
            "changed_paths": ["EXPERIMENTS/CANDIDATES/ALPHA/FOO/BAR.py"],
            "preserved_invariants": [],
            "lsp_evidence_refs": [],
        },
    }

    assert _bind(tmp_path, packet, observed, result)["verb"] == "NOOP_TERMINAL"

    result["changed_paths"] = ["experiments/candidates/alpha/foobar/bar.py"]
    result["payload"]["changed_paths"] = [
        "EXPERIMENTS/CANDIDATES/ALPHA/FOOBAR/BAR.py"
    ]
    outside = _bind(tmp_path, packet, observed, result)
    _assert_defect(outside, "CHANGED_PATH_OUTSIDE_OWNERSHIP", "changed_paths")


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("NONE", "PARTIAL"),
        ("RESUME_SAME_SLICE", "COMPLETED"),
        ("WAIT_FOR_REF", "COMPLETED"),
    ],
)
def test_status_and_action_are_closed(tmp_path: Path, kind: str, status: str) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, kind)
    result["status"] = status
    if kind == "WAIT_FOR_REF":
        result["next_action"]["input_refs"] = ["missing-ref"]
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, "STATUS_ACTION_MISMATCH", "status")


@pytest.mark.parametrize("absolute_ref", ["C:/host/private.txt", "/host/private.txt"])
def test_direct_wait_output_rejects_absolute_input_refs(
    tmp_path: Path, absolute_ref: str
) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet, "WAIT_FOR_REF")
    result["status"] = "PARTIAL"
    result["next_action"]["input_refs"] = [absolute_ref]
    plan = _bind(tmp_path, packet, observed, result)
    _assert_defect(plan, "ABSOLUTE_INPUT_REF", "next_action.input_refs[0]")
    assert absolute_ref not in json.dumps(plan)


def test_explicit_snapshot_and_live_locator_are_required(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    with pytest.raises(packets.InvalidPacket, match="observed_tasks must be explicit"):
        packets.reconcile_once(repo=tmp_path, work_id=packet["work_id"], observed_tasks=None)

    for task in (
        {**observed[0], "thread_id": None},
        {**observed[0], "lifecycle": "FAILED"},
        {**observed[0], "lifecycle": "UNKNOWN"},
    ):
        plan = packets.reconcile_once(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=[task],
        )["plan"]
        assert plan["verb"] == "CONFLICT"
        assert plan["conflict_type"] == "TASK_IDENTITY_CONFLICT"

    for lifecycle in ("CREATED", "RUNNING", "ACTIVE", "PARKED", "IDLE"):
        plan = packets.reconcile_once(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=[{**observed[0], "lifecycle": lifecycle}],
        )["plan"]
        assert plan["verb"] == "DISPATCH_EXISTING"
