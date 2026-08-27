from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path


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


def test_portfolio_cannot_request_itself_again(tmp_path: Path) -> None:
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
        str(assignment_body),
    )
    assert assigned.returncode == 0, assigned.stderr
    assignment_locator = json.loads(assigned.stdout)["locator"]

    return_body = tmp_path / "portfolio-return-body.json"
    write_json(
        return_body,
        {
            "status": "REQUEST_PORTFOLIO",
            "summary": "ask Portfolio to decide again",
            "changed_paths": [],
            "artifact_refs": [],
            "next_objective": "repeat the same Portfolio decision",
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
    assert "Portfolio cannot return REQUEST_PORTFOLIO" in returned.stderr
    assert not (tmp_path / assignment_locator.replace(".assignment.json", ".return.json")).exists()
