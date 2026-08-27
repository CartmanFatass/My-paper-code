from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe")
SCRIPT = ROOT / "scripts/hmasd_session_envelope.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PYTHON), str(SCRIPT), *args], cwd=ROOT, check=False,
        capture_output=True, text=True,
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def ref(repo: Path, path: str, content: bytes) -> dict[str, str]:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}


def release_record(*, release_id: str = "a" * 64, publishable: bool = True) -> dict[str, Any]:
    head = "1" * 40
    return {
        "control_release_id": release_id, "protocol_epoch": 2, "head": head,
        "origin_main": head if publishable else "2" * 40, "branch": "main",
        "control_paths": ["AGENTS.md"], "dirty_control_paths": [],
        "publishable": publishable, "observed_at": "2026-08-27T00:00:00Z",
    }


def assignment_body(repo: Path, direction: str = "ucope") -> dict[str, object]:
    return {
        "objective": "close one bounded slice",
        "context_refs": [ref(repo, f"docs/research/candidates/{direction}/DIRECTION.md", b"authority\n")],
        "owned_paths": [f"docs/research/candidates/{direction}/"],
        "effects": [], "constraints": ["preserve semantics"],
        "done_when": ["return once"], "workspace_mode": "shared-main",
    }


def assign(
    repo: Path, *, recipient: str = "EM/ucope/g1", direction: str = "ucope",
    release: dict[str, Any] | None = None,
) -> dict[str, Any]:
    token = uuid.uuid4()
    body_path, release_path = repo / f"body-{token}.json", repo / f"release-{token}.json"
    write_json(body_path, assignment_body(repo, direction))
    write_json(release_path, release or release_record())
    result = run_cli(
        "assignment", "--repo", str(repo), "--direction-id", direction,
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", recipient, "--recipient-thread-id", "participant",
        "--body", str(body_path), "--control-release", str(release_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def git_closure(*, changed: bool) -> dict[str, Any]:
    if not changed:
        return {"kind": "NO_CHANGES"}
    return {
        "kind": "PUBLISHED", "branch": "main", "commit_sha": "3" * 40,
        "remote": "origin", "ref": "refs/heads/main", "push_outcome": "SUCCEEDED",
    }


def return_body(
    *, status: str = "REQUEST_CM", changed_paths: list[str] | None = None,
    failure: dict[str, Any] | None = None,
    wait_resource: dict[str, Any] | None = None,
) -> dict[str, Any]:
    changed = list(changed_paths or [])
    return {
        "status": status, "summary": "one correlated result", "changed_paths": changed,
        "artifact_refs": [],
        "next_objective": "implement it" if status.startswith("REQUEST_") else None,
        "failure": failure, "wait_resource": wait_resource,
        "git_closure": git_closure(changed=bool(changed)),
    }


def make_return(repo: Path, assignment: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    body_path = repo / f"return-{uuid.uuid4()}.json"
    write_json(body_path, body)
    result = run_cli(
        "return", "--repo", str(repo), "--assignment", assignment["locator"],
        "--body", str(body_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_assignment_uses_explicit_publishable_release_without_git_facts(tmp_path: Path) -> None:
    expected_release = release_record()
    output = assign(tmp_path, release=expected_release)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    uuid.UUID(envelope["message_id"])
    assert envelope["schema_version"] == envelope["protocol_epoch"] == 2
    assert envelope["control_release"] == expected_release
    assert "git_facts" not in envelope
    assert output["message"].startswith(
        "HMASD_SESSION_ENVELOPE_V2 kind=ASSIGNMENT direction=ucope "
        "from=Workflow-Clerk to=EM/ucope/g1 next=NONE"
    )


def test_assignment_rejects_malformed_or_unpublishable_control_release(tmp_path: Path) -> None:
    body_path, release_path = tmp_path / "body.json", tmp_path / "release.json"
    write_json(body_path, assignment_body(tmp_path))
    common = [
        "assignment", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "c",
        "--recipient-identity", "EM/ucope/g1", "--recipient-thread-id", "e",
        "--body", str(body_path), "--control-release", str(release_path),
    ]
    malformed = release_record(); malformed["extra"] = True
    write_json(release_path, malformed)
    result = run_cli(*common)
    assert result.returncode == 2 and "control release" in result.stderr
    write_json(release_path, release_record(publishable=False))
    result = run_cli(*common)
    assert result.returncode == 2 and "publishable" in result.stderr


def test_return_copies_release_reverses_endpoints_and_requires_git_closure(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    artifact = ref(tmp_path, "docs/research/candidates/ucope/RESULT.md", b"result\n")
    body = return_body(changed_paths=[artifact["path"]]); body["artifact_refs"] = [artifact]
    output = make_return(tmp_path, assigned, body)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    assignment = json.loads((tmp_path / assigned["locator"]).read_text())
    assert envelope["reply_to"] == assignment["message_id"]
    assert envelope["sender"] == assignment["recipient"]
    assert envelope["recipient"] == assignment["sender"]
    assert envelope["control_release"] == assignment["control_release"]
    assert envelope["body"]["git_closure"] == git_closure(changed=True)
    assert " next=CM " in output["message"]


def test_git_closure_must_exactly_match_changed_paths(tmp_path: Path) -> None:
    assigned = assign(tmp_path); body_path = tmp_path / "return.json"
    body = return_body(); body["git_closure"] = git_closure(changed=True)
    write_json(body_path, body)
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 2 and "NO_CHANGES" in result.stderr
    body = return_body(changed_paths=["docs/research/candidates/ucope/RESULT.md"])
    body["git_closure"] = {"kind": "NO_CHANGES"}
    write_json(body_path, body)
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 2 and "PUBLISHED" in result.stderr


def test_wait_resource_has_an_exact_machine_checkable_contract(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="CM/ucope/g1")
    immutable = ref(tmp_path, "docs/research/candidates/ucope/RETRY.json", b"{}\n")
    wait = {
        "resource_fingerprint": "4" * 64,
        "frozen_command_or_operation": {"kind": "command", "value": ["python", "run.py", "--run", "r7"]},
        "immutable_refs": [immutable], "retry_condition": "memory_available_bytes >= 1000000",
        "earliest_retry_at": "2026-08-28T00:00:00Z", "direction_id": "ucope", "run_id": "r7",
        "heartbeat": {"binding_id": "heartbeat-ucope-r7", "target_thread_id": "participant"},
    }
    output = make_return(tmp_path, assigned, return_body(status="WAIT_RESOURCE", wait_resource=wait))
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    assert envelope["body"]["wait_resource"] == wait
    assert " next=CM " in output["message"]
    assigned_again = assign(tmp_path, recipient="CM/ucope/g1")
    body_path = tmp_path / "smuggled.json"; write_json(body_path, return_body(wait_resource=wait))
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned_again["locator"], "--body", str(body_path))
    assert result.returncode == 2 and "only WAIT_RESOURCE" in result.stderr


def test_read_validates_assignment_and_return_edges(tmp_path: Path) -> None:
    assigned = assign(tmp_path); returned = make_return(tmp_path, assigned, return_body())
    return_path = tmp_path / returned["locator"]
    document = json.loads(return_path.read_text())
    document["recipient"] = {"identity": "CM/ucope/g2", "thread_id": "peer"}
    write_json(return_path, document)
    result = run_cli("read", "--repo", str(tmp_path), "--envelope", returned["locator"])
    assert result.returncode == 2 and "endpoints" in result.stderr
    assignment_path = tmp_path / assigned["locator"]
    document = json.loads(assignment_path.read_text())
    document["sender"] = {"identity": "EM/ucope/g2", "thread_id": "peer"}
    write_json(assignment_path, document)
    result = run_cli("read", "--repo", str(tmp_path), "--envelope", assigned["locator"])
    assert result.returncode == 2 and "assignment" in result.stderr.lower()


def test_control_notice_flows_participant_to_clerk_then_clerk_to_target(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    release_path = tmp_path / "notice-release.json"; write_json(release_path, release_record())
    initiating_body = {
        "action": "PAUSE", "reason": "user paused this exact assignment",
        "target_identity": "EM/ucope/g1",
        "scope": {"direction_id": "ucope", "affected_locator": assigned["locator"]},
    }
    initiating_path = tmp_path / "initiating.json"; write_json(initiating_path, initiating_body)
    first = run_cli(
        "control-notice", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Root", "--sender-thread-id", "root",
        "--recipient-identity", "Workflow-Clerk", "--recipient-thread-id", "clerk",
        "--body", str(initiating_path), "--control-release", str(release_path),
    )
    assert first.returncode == 0, first.stderr
    first_output = json.loads(first.stdout)
    first_envelope = json.loads((tmp_path / first_output["locator"]).read_text())
    assignment = json.loads((tmp_path / assigned["locator"]).read_text())
    assert first_envelope["reply_to"] == assignment["message_id"]
    relay_body = dict(initiating_body)
    relay_body["scope"] = {"direction_id": "ucope", "affected_locator": first_output["locator"]}
    relay_path = tmp_path / "relay.json"; write_json(relay_path, relay_body)
    relayed = run_cli(
        "control-notice", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "EM/ucope/g1", "--recipient-thread-id", "participant",
        "--body", str(relay_path), "--control-release", str(release_path),
    )
    assert relayed.returncode == 0, relayed.stderr
    relay_envelope = json.loads((tmp_path / json.loads(relayed.stdout)["locator"]).read_text())
    assert relay_envelope["reply_to"] == first_envelope["message_id"]
    direct = run_cli(
        "control-notice", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "EM/ucope/g1", "--sender-thread-id", "participant",
        "--recipient-identity", "CM/ucope/g1", "--recipient-thread-id", "peer",
        "--body", str(initiating_path), "--control-release", str(release_path),
    )
    assert direct.returncode == 2 and "CONTROL_NOTICE" in direct.stderr
    relay_path_on_disk = tmp_path / json.loads(relayed.stdout)["locator"]
    tampered = json.loads(relay_path_on_disk.read_text())
    tampered["recipient"] = {"identity": "CM/ucope/g1", "thread_id": "peer"}
    write_json(relay_path_on_disk, tampered)
    reread = run_cli(
        "read", "--repo", str(tmp_path), "--envelope", json.loads(relayed.stdout)["locator"],
    )
    assert reread.returncode == 2 and "recipient" in reread.stderr


def test_reanchor_requires_matching_new_publishable_release(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    new_release = release_record(release_id="b" * 64)
    release_path = tmp_path / "new-release.json"; write_json(release_path, new_release)
    body = {
        "action": "REANCHOR", "reason": "adopt the new same-epoch control release",
        "target_identity": "EM/ucope/g1",
        "scope": {"direction_id": "ucope", "affected_locator": assigned["locator"],
                  "expected_control_release_id": "b" * 64},
    }
    body_path = tmp_path / "reanchor.json"; write_json(body_path, body)
    result = run_cli(
        "control-notice", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Root", "--sender-thread-id", "root",
        "--recipient-identity", "Workflow-Clerk", "--recipient-thread-id", "clerk",
        "--body", str(body_path), "--control-release", str(release_path),
    )
    assert result.returncode == 0, result.stderr
    envelope = json.loads((tmp_path / json.loads(result.stdout)["locator"]).read_text())
    assert envelope["control_release"] == new_release

    old_release_path = tmp_path / "old-release.json"; write_json(old_release_path, release_record())
    body["scope"]["expected_control_release_id"] = "a" * 64
    old_body_path = tmp_path / "old-reanchor.json"; write_json(old_body_path, body)
    unchanged = run_cli(
        "control-notice", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Root", "--sender-thread-id", "root",
        "--recipient-identity", "Workflow-Clerk", "--recipient-thread-id", "clerk",
        "--body", str(old_body_path), "--control-release", str(old_release_path),
    )
    assert unchanged.returncode == 2 and "new control release" in unchanged.stderr


def test_read_message_rejects_v1_and_detects_body_tampering(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    old = run_cli("read-message", "--repo", str(tmp_path), "--message", f"HMASD_SESSION_ENVELOPE_V1 {assigned['locator']}")
    assert old.returncode == 2
    wrapped = run_cli("read-message", "--repo", str(tmp_path), "--message", assigned["message"] + " please")
    assert wrapped.returncode == 2
    envelope = json.loads((tmp_path / assigned["locator"]).read_text())
    envelope["body"]["objective"] = "tampered"; write_json(tmp_path / assigned["locator"], envelope)
    read = run_cli("read", "--repo", str(tmp_path), "--envelope", assigned["locator"])
    assert read.returncode == 2 and "body_sha256" in read.stderr


def test_failure_history_requires_exact_order_and_reports_eligibility(tmp_path: Path) -> None:
    fingerprint, locators = "immutable-oom-fingerprint", []
    for attempt in (1, 2):
        assigned = assign(tmp_path, recipient="CM/ucope/g1")
        failure = {
            "scope": "direction", "code": "OOM", "fingerprint": fingerprint,
            "responsible_role": "CM", "retryable": True,
            "attempt": attempt, "max_attempts": 3, "summary": "same frozen plan",
        }
        locators.append(make_return(tmp_path, assigned, return_body(status="FAILED", failure=failure))["locator"])
    args = ["failure-history", "--repo", str(tmp_path), "--fingerprint", fingerprint]
    for locator in locators: args.extend(["--return", locator])
    result = run_cli(*args)
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed == {
        "exhausted": False, "fingerprint": fingerprint, "max_attempts": 3,
        "next_attempt": 3, "observed_attempts": 2, "responsible_role": "CM",
        "retry_eligible": True, "return_locators": locators,
    }
    out_of_order = run_cli(
        "failure-history", "--repo", str(tmp_path), "--fingerprint", fingerprint,
        "--return", locators[1], "--return", locators[0],
    )
    assert out_of_order.returncode == 2 and "attempts 1..N" in out_of_order.stderr

    assigned = assign(tmp_path, recipient="CM/ucope/g1")
    failure = {
        "scope": "direction", "code": "OOM", "fingerprint": fingerprint,
        "responsible_role": "CM", "retryable": True,
        "attempt": 3, "max_attempts": 3, "summary": "same frozen plan",
    }
    locators.append(make_return(tmp_path, assigned, return_body(status="FAILED", failure=failure))["locator"])
    exhausted_args = ["failure-history", "--repo", str(tmp_path), "--fingerprint", fingerprint]
    for locator in locators: exhausted_args.extend(["--return", locator])
    exhausted = run_cli(*exhausted_args)
    assert exhausted.returncode == 0, exhausted.stderr
    assert json.loads(exhausted.stdout)["retry_eligible"] is False
    assert json.loads(exhausted.stdout)["exhausted"] is True


def test_portfolio_return_copies_release_and_has_legal_global_edge(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="Portfolio", direction="portfolio")
    artifact = ref(tmp_path, "docs/research/portfolio/PORTFOLIO.md", b"portfolio\n")
    body = {
        "registry_revision": 7, "snapshot_digest": "b" * 64,
        "considered": ["ucope"], "transitions": [{"direction_id": "ucope", "next": "EM"}],
        "capacity": {"slots": 1}, "summary": "one bounded decision",
        "artifact_refs": [artifact], "failure": None,
    }
    body_path = tmp_path / "portfolio.json"; write_json(body_path, body)
    result = run_cli("portfolio-return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    assignment = json.loads((tmp_path / assigned["locator"]).read_text())
    assert envelope["control_release"] == assignment["control_release"]
    assert envelope["sender"]["identity"] == "Portfolio"
    assert envelope["recipient"]["identity"] == "Workflow-Clerk"
    assert " next=NONE " in output["message"]
    document = json.loads((tmp_path / output["locator"]).read_text())
    document["sender"] = {"identity": "Root", "thread_id": "root"}
    write_json(tmp_path / output["locator"], document)
    reread = run_cli("read", "--repo", str(tmp_path), "--envelope", output["locator"])
    assert reread.returncode == 2 and "endpoints" in reread.stderr
