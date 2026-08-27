from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_session_envelope.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_assignment_builds_fixed_transport_and_locator(tmp_path: Path) -> None:
    body = {
        "objective": "close one bounded science slice",
        "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
        "owned_paths": ["docs/research/candidates/ucope/"],
        "constraints": ["do not modify shared core"],
        "done_when": ["send one RETURN before final"],
    }
    body_path = tmp_path / "assignment-body.json"
    write_json(body_path, body)

    result = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "EM/ucope/g1",
        "--recipient-thread-id",
        "em-thread",
        "--body",
        str(body_path),
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    locator = output["locator"]
    assert locator.startswith(".codex/runtime/session-envelopes/ucope/")
    assert locator.endswith(".assignment.json")
    assert output == {
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": "em-thread",
    }

    envelope = json.loads((tmp_path / locator).read_text(encoding="utf-8"))
    uuid.UUID(envelope["message_id"])
    assert envelope == {
        "schema_version": 1,
        "message_id": envelope["message_id"],
        "direction_id": "ucope",
        "sender": {
            "identity": "Workflow-Clerk",
            "thread_id": "clerk-thread",
        },
        "recipient": {
            "identity": "EM/ucope/g1",
            "thread_id": "em-thread",
        },
        "kind": "ASSIGNMENT",
        "reply_to": None,
        "body": body,
    }


def test_return_copies_assignment_identity_and_targets_original_sender(
    tmp_path: Path,
) -> None:
    assignment_body = {
        "objective": "close one bounded science slice",
        "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
        "owned_paths": ["docs/research/candidates/ucope/"],
        "constraints": ["do not modify shared core"],
        "done_when": ["send one RETURN before final"],
    }
    assignment_body_path = tmp_path / "assignment-body.json"
    write_json(assignment_body_path, assignment_body)
    assignment_result = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "EM/ucope/g1",
        "--recipient-thread-id",
        "em-thread",
        "--body",
        str(assignment_body_path),
    )
    assert assignment_result.returncode == 0, assignment_result.stderr
    assignment_output = json.loads(assignment_result.stdout)
    assignment = json.loads(
        (tmp_path / assignment_output["locator"]).read_text(encoding="utf-8")
    )

    return_body = {
        "status": "REQUEST_CM",
        "summary": "science slice is closed",
        "changed_paths": [
            "docs/research/candidates/ucope/DIRECTION.md",
        ],
        "artifact_refs": [
            "docs/research/candidates/ucope/UCOPE_RESULT.md",
        ],
        "next_objective": "implement the frozen slice",
        "failure": None,
    }
    return_body_path = tmp_path / "return-body.json"
    write_json(return_body_path, return_body)

    result = run_cli(
        "return",
        "--repo",
        str(tmp_path),
        "--assignment",
        assignment_output["locator"],
        "--body",
        str(return_body_path),
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    expected_locator = assignment_output["locator"].replace(
        ".assignment.json", ".return.json"
    )
    assert output == {
        "locator": expected_locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {expected_locator}",
        "recipient_thread_id": "clerk-thread",
    }

    envelope = json.loads((tmp_path / expected_locator).read_text(encoding="utf-8"))
    assert envelope == {
        "schema_version": 1,
        "message_id": f"{assignment['message_id']}:return",
        "direction_id": "ucope",
        "sender": {
            "identity": "EM/ucope/g1",
            "thread_id": "em-thread",
        },
        "recipient": {
            "identity": "Workflow-Clerk",
            "thread_id": "clerk-thread",
        },
        "kind": "RETURN",
        "reply_to": assignment["message_id"],
        "body": return_body,
    }


def test_read_message_accepts_only_the_exact_script_transport(
    tmp_path: Path,
) -> None:
    body = {
        "objective": "close one bounded science slice",
        "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
        "owned_paths": ["docs/research/candidates/ucope/"],
        "constraints": ["do not modify shared core"],
        "done_when": ["send one RETURN before final"],
    }
    body_path = tmp_path / "assignment-body.json"
    write_json(body_path, body)
    created = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "EM/ucope/g1",
        "--recipient-thread-id",
        "em-thread",
        "--body",
        str(body_path),
    )
    assert created.returncode == 0, created.stderr
    transport = json.loads(created.stdout)

    accepted = run_cli(
        "read-message",
        "--repo",
        str(tmp_path),
        "--message",
        transport["message"],
    )

    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout) == {
        "envelope": json.loads(
            (tmp_path / transport["locator"]).read_text(encoding="utf-8")
        ),
        **transport,
    }


@pytest.mark.parametrize(
    "message",
    [
        "EM finished; please dispatch CM",
        '{"kind":"RETURN","status":"REQUEST_CM"}',
        "HMASD_SESSION_ENVELOPE_V1 .codex/runtime/session-envelopes/ucope/x.return.json\nplease continue",
        "<codex_delegation><input>HMASD_SESSION_ENVELOPE_V1 .codex/runtime/session-envelopes/ucope/x.return.json</input></codex_delegation>",
    ],
)
def test_read_message_rejects_natural_language_json_and_wrapped_locators(
    tmp_path: Path, message: str
) -> None:
    result = run_cli(
        "read-message",
        "--repo",
        str(tmp_path),
        "--message",
        message,
    )

    assert result.returncode == 2
    assert "exactly HMASD_SESSION_ENVELOPE_V1 plus one locator" in result.stderr


def test_read_validates_and_exposes_fixed_delivery_facts(tmp_path: Path) -> None:
    body = {
        "objective": "close one bounded science slice",
        "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
        "owned_paths": ["docs/research/candidates/ucope/"],
        "constraints": ["do not modify shared core"],
        "done_when": ["send one RETURN before final"],
    }
    body_path = tmp_path / "assignment-body.json"
    write_json(body_path, body)
    created = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "EM/ucope/g1",
        "--recipient-thread-id",
        "em-thread",
        "--body",
        str(body_path),
    )
    assert created.returncode == 0, created.stderr
    locator = json.loads(created.stdout)["locator"]
    envelope = json.loads((tmp_path / locator).read_text(encoding="utf-8"))

    result = run_cli(
        "read",
        "--repo",
        str(tmp_path),
        "--envelope",
        locator,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "envelope": envelope,
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": "em-thread",
    }


def test_same_return_can_be_recovered_without_creating_a_second_envelope(
    tmp_path: Path,
) -> None:
    assignment_body_path = tmp_path / "assignment-body.json"
    write_json(
        assignment_body_path,
        {
            "objective": "close one bounded science slice",
            "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
            "owned_paths": ["docs/research/candidates/ucope/"],
            "constraints": ["do not modify shared core"],
            "done_when": ["send one RETURN before final"],
        },
    )
    assignment = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "EM/ucope/g1",
        "--recipient-thread-id",
        "em-thread",
        "--body",
        str(assignment_body_path),
    )
    assert assignment.returncode == 0, assignment.stderr
    assignment_locator = json.loads(assignment.stdout)["locator"]
    return_body_path = tmp_path / "return-body.json"
    write_json(
        return_body_path,
        {
            "status": "DONE",
            "summary": "slice complete",
            "changed_paths": [],
            "artifact_refs": [],
            "next_objective": None,
            "failure": None,
        },
    )
    command = (
        "return",
        "--repo",
        str(tmp_path),
        "--assignment",
        assignment_locator,
        "--body",
        str(return_body_path),
    )

    first = run_cli(*command)
    second = run_cli(*command)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout) == json.loads(first.stdout)
    return_files = list(
        (tmp_path / ".codex/runtime/session-envelopes/ucope").glob("*.return.json")
    )
    assert len(return_files) == 1


def test_participant_cannot_create_assignment_for_another_participant(
    tmp_path: Path,
) -> None:
    body_path = tmp_path / "assignment-body.json"
    write_json(
        body_path,
        {
            "objective": "perform one bounded engineering slice",
            "context_refs": ["docs/research/candidates/ucope/DIRECTION.md"],
            "owned_paths": ["experiments/candidates/ucope/"],
            "constraints": ["return the decision to Workflow-Clerk"],
            "done_when": ["send one RETURN before final"],
        },
    )

    for recipient_identity, recipient_thread in (
        ("CM/ucope/g1", "cm-thread"),
        ("Root", "root-thread"),
    ):
        result = run_cli(
            "assignment",
            "--repo",
            str(tmp_path),
            "--direction-id",
            "ucope",
            "--sender-identity",
            "Portfolio",
            "--sender-thread-id",
            "portfolio-thread",
            "--recipient-identity",
            recipient_identity,
            "--recipient-thread-id",
            recipient_thread,
            "--body",
            str(body_path),
        )

        assert result.returncode == 2
        assert result.stdout == ""
        assert "only Workflow-Clerk may assign a participant" in result.stderr
    assert not (tmp_path / ".codex/runtime/session-envelopes").exists()


def test_legacy_participant_assignment_can_finish_but_cannot_be_created(
    tmp_path: Path,
) -> None:
    message_id = str(uuid.uuid4())
    relative = Path(
        f".codex/runtime/session-envelopes/ucope/{message_id}.assignment.json"
    )
    write_json(
        tmp_path / relative,
        {
            "schema_version": 1,
            "message_id": message_id,
            "direction_id": "ucope",
            "sender": {
                "identity": "Portfolio",
                "thread_id": "portfolio-thread",
            },
            "recipient": {
                "identity": "CM/ucope/g1",
                "thread_id": "cm-thread",
            },
            "kind": "ASSIGNMENT",
            "reply_to": None,
            "body": {
                "objective": "finish one in-flight legacy slice",
                "context_refs": [
                    "docs/research/candidates/ucope/DIRECTION.md"
                ],
                "owned_paths": ["experiments/candidates/ucope/"],
                "constraints": ["do not create another assignment"],
                "done_when": ["send one RETURN to the original sender"],
            },
        },
    )

    read_result = run_cli(
        "read",
        "--repo",
        str(tmp_path),
        "--envelope",
        relative.as_posix(),
    )

    assert read_result.returncode == 0, read_result.stderr
    assert json.loads(read_result.stdout)["recipient_thread_id"] == "cm-thread"

    return_body = tmp_path / "legacy-return-body.json"
    write_json(
        return_body,
        {
            "status": "REQUEST_CM",
            "summary": "legacy slice finished without creating a new direct edge",
            "changed_paths": [],
            "artifact_refs": [],
            "next_objective": "continue through a Clerk-generated CM assignment",
            "failure": None,
        },
    )
    returned = run_cli(
        "return",
        "--repo",
        str(tmp_path),
        "--assignment",
        relative.as_posix(),
        "--body",
        str(return_body),
    )

    assert returned.returncode == 0, returned.stderr
    assert json.loads(returned.stdout)["recipient_thread_id"] == "portfolio-thread"


def test_global_portfolio_assignment_cannot_use_ordinary_return(tmp_path: Path) -> None:
    assignment_body = tmp_path / "portfolio-assignment-body.json"
    write_json(
        assignment_body,
        {
            "objective": "choose one low-frequency investment disposition",
            "context_refs": ["docs/research/portfolio/PORTFOLIO.md"],
            "owned_paths": ["docs/research/portfolio/PORTFOLIO.md"],
            "constraints": ["return the decision to Workflow-Clerk"],
            "done_when": ["return REQUEST_EM, REQUEST_CM, REQUEST_USER, or DONE"],
        },
    )
    assigned = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "portfolio",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(assignment_body),
    )
    assert assigned.returncode == 0, assigned.stderr
    assignment_locator = json.loads(assigned.stdout)["locator"]

    return_body = tmp_path / "portfolio-return-body.json"
    write_json(
        return_body,
        {
            "status": "REQUEST_EM",
            "summary": "attempt to bypass the global action list",
            "changed_paths": [],
            "artifact_refs": [],
            "next_objective": "continue one direction outside the action list",
            "failure": None,
        },
    )
    returned = run_cli(
        "return",
        "--repo",
        str(tmp_path),
        "--assignment",
        assignment_locator,
        "--body",
        str(return_body),
    )

    assert returned.returncode == 2
    assert "global Portfolio assignment requires portfolio-return" in returned.stderr
    assert not (tmp_path / assignment_locator.replace(".assignment.json", ".return.json")).exists()


def test_new_portfolio_assignment_requires_global_transport_direction(
    tmp_path: Path,
) -> None:
    body = tmp_path / "portfolio-assignment-body.json"
    write_json(
        body,
        {
            "objective": "compare the global portfolio",
            "context_refs": ["docs/research/portfolio/PORTFOLIO.md"],
            "owned_paths": ["docs/research/portfolio/"],
            "constraints": ["do not split this wake by direction"],
            "done_when": ["send one portfolio return"],
        },
    )

    result = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "ucope",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(body),
    )

    assert result.returncode == 2
    assert "Portfolio assignment direction_id must be portfolio" in result.stderr
    assert not (tmp_path / ".codex/runtime/session-envelopes").exists()


def test_portfolio_return_carries_multiple_direction_actions_from_one_global_wake(
    tmp_path: Path,
) -> None:
    assignment_body_path = tmp_path / "portfolio-assignment-body.json"
    write_json(
        assignment_body_path,
        {
            "objective": "compare the portfolio and choose all material next actions",
            "context_refs": [
                "docs/research/portfolio/PORTFOLIO.md",
                "docs/research/portfolio/workflow/registry.json",
            ],
            "owned_paths": ["docs/research/portfolio/"],
            "constraints": ["maintain the total research picture"],
            "done_when": ["return every material direction action to Clerk"],
        },
    )
    assigned = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "portfolio",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(assignment_body_path),
    )
    assert assigned.returncode == 0, assigned.stderr
    assignment_locator = json.loads(assigned.stdout)["locator"]
    assignment = json.loads((tmp_path / assignment_locator).read_text(encoding="utf-8"))

    body = {
        "summary": "one global wake selected three independent actions",
        "changed_paths": ["docs/research/portfolio/PORTFOLIO.md"],
        "artifact_refs": ["docs/research/portfolio/workflow/registry.json"],
        "actions": [
            {
                "direction_id": "new_uav_direction",
                "lifecycle": "ACTIVE",
                "status": "REQUEST_EM",
                "summary": "open the new direction with a scientific definition slice",
                "artifact_refs": ["docs/research/portfolio/PORTFOLIO.md"],
                "next_objective": "freeze the new direction science card",
                "failure": None,
            },
            {
                "direction_id": "metric_ground_transport_allocation",
                "lifecycle": "ACTIVE",
                "status": "REQUEST_CM",
                "summary": "continue the accepted engineering investment",
                "artifact_refs": [
                    "docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md"
                ],
                "next_objective": "complete the accepted implementation slice",
                "failure": None,
            },
            {
                "direction_id": "retired_direction",
                "lifecycle": "CLOSED",
                "status": "DONE",
                "summary": "close the direction with its durable portfolio reason",
                "artifact_refs": ["docs/research/portfolio/PORTFOLIO.md"],
                "next_objective": None,
                "failure": None,
            },
        ],
        "failure": None,
    }
    body_path = tmp_path / "portfolio-return-body.json"
    write_json(body_path, body)
    registry_path = tmp_path / "docs/research/portfolio/workflow/registry.json"
    write_json(
        registry_path,
        {
            "directions": [
                {"id": action["direction_id"], "lifecycle": action["lifecycle"]}
                for action in body["actions"]
            ]
        },
    )

    returned = run_cli(
        "portfolio-return",
        "--repo",
        str(tmp_path),
        "--assignment",
        assignment_locator,
        "--body",
        str(body_path),
    )

    assert returned.returncode == 0, returned.stderr
    output = json.loads(returned.stdout)
    expected_locator = assignment_locator.replace(
        ".assignment.json", ".portfolio-return.json"
    )
    assert output == {
        "locator": expected_locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {expected_locator}",
        "recipient_thread_id": "clerk-thread",
    }
    envelope = json.loads((tmp_path / expected_locator).read_text(encoding="utf-8"))
    assert envelope == {
        "schema_version": 1,
        "message_id": f"{assignment['message_id']}:portfolio-return",
        "direction_id": "portfolio",
        "sender": assignment["recipient"],
        "recipient": assignment["sender"],
        "kind": "PORTFOLIO_RETURN",
        "reply_to": assignment["message_id"],
        "body": {
            **body,
            "actions": sorted(body["actions"], key=lambda action: action["direction_id"]),
        },
    }

    read_back = run_cli(
        "read",
        "--repo",
        str(tmp_path),
        "--envelope",
        expected_locator,
    )
    assert read_back.returncode == 0, read_back.stderr
    assert json.loads(read_back.stdout)["envelope"] == envelope


def test_portfolio_return_keeps_scoped_failure_beside_independent_action(
    tmp_path: Path,
) -> None:
    assignment_body = tmp_path / "assignment-body.json"
    write_json(
        assignment_body,
        {
            "objective": "decide two independent direction outcomes",
            "context_refs": ["docs/research/portfolio/PORTFOLIO.md"],
            "owned_paths": ["docs/research/portfolio/"],
            "constraints": ["keep direction failures isolated"],
            "done_when": ["send one complete action list"],
        },
    )
    assigned = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "portfolio",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(assignment_body),
    )
    assert assigned.returncode == 0, assigned.stderr
    locator = json.loads(assigned.stdout)["locator"]
    actions = [
        {
            "direction_id": "failed_direction",
            "lifecycle": "ACTIVE",
            "status": "FAILED",
            "summary": "registry CAS failed for this direction only",
            "artifact_refs": ["docs/research/portfolio/workflow/registry.json"],
            "next_objective": "repair the exact registry CAS conflict",
            "failure": {"scope": "direction", "summary": "revision conflict"},
        },
        {
            "direction_id": "ready_direction",
            "lifecycle": "ACTIVE",
            "status": "REQUEST_EM",
            "summary": "continue independent science",
            "artifact_refs": ["docs/research/portfolio/workflow/registry.json"],
            "next_objective": "run the accepted scientific slice",
            "failure": None,
        },
    ]
    write_json(
        tmp_path / "docs/research/portfolio/workflow/registry.json",
        {
            "directions": [
                {"id": action["direction_id"], "lifecycle": action["lifecycle"]}
                for action in actions
            ]
        },
    )
    body = tmp_path / "portfolio-return-body.json"
    write_json(
        body,
        {
            "summary": "one direction failed without delaying the other",
            "changed_paths": [],
            "artifact_refs": ["docs/research/portfolio/workflow/registry.json"],
            "actions": actions,
            "failure": None,
        },
    )

    result = run_cli(
        "portfolio-return",
        "--repo",
        str(tmp_path),
        "--assignment",
        locator,
        "--body",
        str(body),
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads((tmp_path / json.loads(result.stdout)["locator"]).read_text())
    by_direction = {
        action["direction_id"]: action for action in envelope["body"]["actions"]
    }
    assert by_direction["failed_direction"]["failure"] == {
        "scope": "direction",
        "summary": "revision conflict",
    }
    assert by_direction["ready_direction"]["status"] == "REQUEST_EM"


def test_portfolio_terminal_action_requires_current_registry_closed(
    tmp_path: Path,
) -> None:
    assignment_body = tmp_path / "assignment-body.json"
    write_json(
        assignment_body,
        {
            "objective": "close one direction",
            "context_refs": ["docs/research/portfolio/PORTFOLIO.md"],
            "owned_paths": ["docs/research/portfolio/"],
            "constraints": ["bind terminal status to registry"],
            "done_when": ["send one complete action list"],
        },
    )
    assigned = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "portfolio",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(assignment_body),
    )
    locator = json.loads(assigned.stdout)["locator"]
    write_json(
        tmp_path / "docs/research/portfolio/workflow/registry.json",
        {"directions": [{"id": "still_active", "lifecycle": "ACTIVE"}]},
    )
    body = tmp_path / "portfolio-return-body.json"
    write_json(
        body,
        {
            "summary": "incorrectly claim terminal",
            "changed_paths": [],
            "artifact_refs": ["docs/research/portfolio/workflow/registry.json"],
            "actions": [
                {
                    "direction_id": "still_active",
                    "lifecycle": "CLOSED",
                    "status": "DONE",
                    "summary": "claim closed",
                    "artifact_refs": [
                        "docs/research/portfolio/workflow/registry.json"
                    ],
                    "next_objective": None,
                    "failure": None,
                }
            ],
            "failure": None,
        },
    )

    result = run_cli(
        "portfolio-return",
        "--repo",
        str(tmp_path),
        "--assignment",
        locator,
        "--body",
        str(body),
    )

    assert result.returncode == 2
    assert "does not match current Portfolio registry lifecycle" in result.stderr


@pytest.mark.parametrize(
    ("actions", "expected_error"),
    [
        (
            [
                {
                    "direction_id": "ucope",
                    "lifecycle": "ACTIVE",
                    "status": "DONE",
                    "summary": "invalid terminal action",
                    "artifact_refs": [],
                    "next_objective": None,
                    "failure": None,
                }
            ],
            "lifecycle/status combination is invalid",
        ),
        (
            [
                {
                    "direction_id": "ucope",
                    "lifecycle": "ACTIVE",
                    "status": "REQUEST_EM",
                    "summary": "first route",
                    "artifact_refs": [],
                    "next_objective": "continue science",
                    "failure": None,
                },
                {
                    "direction_id": "ucope",
                    "lifecycle": "ACTIVE",
                    "status": "REQUEST_CM",
                    "summary": "conflicting route",
                    "artifact_refs": [],
                    "next_objective": "continue engineering",
                    "failure": None,
                },
            ],
            "duplicate direction_id",
        ),
    ],
)
def test_portfolio_return_rejects_invalid_or_duplicate_direction_actions(
    tmp_path: Path,
    actions: list[dict[str, object]],
    expected_error: str,
) -> None:
    assignment_body = tmp_path / "assignment-body.json"
    write_json(
        assignment_body,
        {
            "objective": "make one global portfolio decision",
            "context_refs": ["docs/research/portfolio/PORTFOLIO.md"],
            "owned_paths": ["docs/research/portfolio/"],
            "constraints": ["return one complete action list"],
            "done_when": ["send the portfolio return to Clerk"],
        },
    )
    assigned = run_cli(
        "assignment",
        "--repo",
        str(tmp_path),
        "--direction-id",
        "portfolio",
        "--sender-identity",
        "Workflow-Clerk",
        "--sender-thread-id",
        "clerk-thread",
        "--recipient-identity",
        "Portfolio",
        "--recipient-thread-id",
        "portfolio-thread",
        "--body",
        str(assignment_body),
    )
    assert assigned.returncode == 0, assigned.stderr
    locator = json.loads(assigned.stdout)["locator"]
    body_path = tmp_path / "portfolio-return-body.json"
    write_json(
        body_path,
        {
            "summary": "invalid action list",
            "changed_paths": [],
            "artifact_refs": [],
            "actions": actions,
            "failure": None,
        },
    )

    returned = run_cli(
        "portfolio-return",
        "--repo",
        str(tmp_path),
        "--assignment",
        locator,
        "--body",
        str(body_path),
    )

    assert returned.returncode == 2
    assert expected_error in returned.stderr
    assert not (
        tmp_path / locator.replace(".assignment.json", ".portfolio-return.json")
    ).exists()
