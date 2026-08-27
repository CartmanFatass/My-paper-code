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
