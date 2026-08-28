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
        "control_release_id": release_id, "protocol_epoch": 3, "head": head,
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
    ingress = root_ingress(repo, direction, release=release)
    recipient_role = recipient.split("/", 1)[0]
    fixed = [
        ("docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n"),
        (f".codex/prompts/hmasd-{recipient_role.lower()}.md", b"role prompt\n"),
    ]
    if recipient_role in {"EM", "CM"}:
        base = f"docs/research/candidates/{direction}"
        fixed.extend([
            (f"{base}/DIRECTION.md", b"authority\n"),
            (f"{base}/workflow/research/state.json", b"{}\n"),
            (f"{base}/workflow/engineering/state.json", b"{}\n"),
        ])
    elif recipient_role == "Portfolio":
        fixed.extend([
            ("docs/research/portfolio/PORTFOLIO.md", b"portfolio\n"),
            ("docs/research/portfolio/workflow/registry.json", b"{}\n"),
        ])
    for path, content in fixed:
        target = repo / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    result = run_cli(
        "assignment-from-brief", "--repo", str(repo), "--direction-id", direction,
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", recipient, "--recipient-thread-id", "participant",
        "--objective", "close one bounded slice",
        "--owned-path", f"docs/research/candidates/{direction}/",
        "--constraint", "preserve semantics",
        "--done-when", "return once",
        "--control-release-envelope", ingress["locator"],
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def root_ingress(
    repo: Path, direction: str = "ucope", *, release: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message_id = str(uuid.uuid4())
    body = {
        "objective": "route one bounded slice",
        "context_refs": [ref(repo, f"authority/{direction}.md", b"authority\n")],
        "owned_paths": [],
        "effects": ["native_message_send:participant"],
        "constraints": ["preserve semantics"],
        "done_when": ["route once"],
        "workspace_mode": "shared-main",
    }
    envelope = {
        "schema_version": 3,
        "protocol_epoch": 3,
        "message_id": message_id,
        "direction_id": direction,
        "sender": {"identity": "Root", "thread_id": "root"},
        "recipient": {"identity": "Workflow-Clerk", "thread_id": "clerk"},
        "kind": "ASSIGNMENT",
        "reply_to": None,
        "control_release": release or release_record(),
        "body": body,
    }
    locator = f".codex/runtime/session-envelopes/{direction}/{message_id}.assignment.json"
    write_json(repo / locator, envelope)
    message = (
        f"HMASD_SESSION_ENVELOPE_V3 kind=ASSIGNMENT direction={direction} "
        f"from=Root to=Workflow-Clerk next=NONE id={message_id} "
        f"locator={locator}"
    )
    return {"locator": locator, "message": message, "recipient_thread_id": "clerk"}


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


def run_notice(
    repo: Path, body: dict[str, Any], *, sender: str = "Root",
    sender_thread: str = "root", recipient: str = "Workflow-Clerk",
    recipient_thread: str = "clerk", release: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess[str]:
    token = uuid.uuid4()
    body_path, release_path = repo / f"notice-{token}.json", repo / f"notice-release-{token}.json"
    write_json(body_path, body); write_json(release_path, release or release_record())
    return run_cli(
        "control-notice", "--repo", str(repo), "--direction-id", "ucope",
        "--sender-identity", sender, "--sender-thread-id", sender_thread,
        "--recipient-identity", recipient, "--recipient-thread-id", recipient_thread,
        "--body", str(body_path), "--control-release", str(release_path),
    )


def test_assignment_uses_explicit_publishable_release_without_git_facts(tmp_path: Path) -> None:
    expected_release = release_record()
    output = assign(tmp_path, release=expected_release)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    uuid.UUID(envelope["message_id"])
    assert envelope["schema_version"] == envelope["protocol_epoch"] == 3
    assert "body_sha256" not in envelope
    assert envelope["control_release"] == expected_release
    assert "git_facts" not in envelope
    assert output["message"].startswith(
        "HMASD_SESSION_ENVELOPE_V3 kind=ASSIGNMENT direction=ucope "
        "from=Workflow-Clerk to=EM/ucope/g1 next=NONE"
    )
    assert " sha256=" not in output["message"]


def test_assignment_from_brief_generates_mechanical_body_fields(tmp_path: Path) -> None:
    direction = "ucope"
    ingress = root_ingress(tmp_path, direction)
    protocol = ref(tmp_path, "docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n")
    prompt = ref(tmp_path, ".codex/prompts/hmasd-em.md", b"em prompt\n")
    authority = ref(
        tmp_path, f"docs/research/candidates/{direction}/DIRECTION.md", b"direction\n",
    )
    research = ref(
        tmp_path,
        f"docs/research/candidates/{direction}/workflow/research/state.json",
        b"{}\n",
    )
    engineering = ref(
        tmp_path,
        f"docs/research/candidates/{direction}/workflow/engineering/state.json",
        b"{}\n",
    )
    evidence = ref(tmp_path, f"docs/research/candidates/{direction}/RESULT.md", b"result\n")
    result = run_cli(
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", direction,
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "EM/ucope/g2", "--recipient-thread-id", "em",
        "--objective", "Interpret the bounded result and choose the next scientific slice.",
        "--context-path", evidence["path"],
        "--constraint", "Preserve the accepted result firewall.",
        "--owned-path", f"docs/research/candidates/{direction}/",
        "--control-release-envelope", ingress["locator"],
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    assert envelope["body"] == {
        "objective": "Interpret the bounded result and choose the next scientific slice.",
        "context_refs": [protocol, prompt, authority, research, engineering, evidence],
        "owned_paths": [f"docs/research/candidates/{direction}/"],
        "effects": ["native_message_send:Workflow-Clerk"],
        "constraints": [
            "Work only inside this bounded EM direction slice.",
            "Return to Workflow-Clerk; do not contact another top-level manager.",
            "Preserve the accepted result firewall.",
        ],
        "done_when": [
            "Before final, send exactly one correlated v3 RETURN to Workflow-Clerk."
        ],
        "workspace_mode": "shared-main",
    }
    assert not list(tmp_path.rglob("*.body.json"))


def test_assignment_from_brief_uses_portfolio_return_boundary(tmp_path: Path) -> None:
    ingress = root_ingress(tmp_path, "portfolio")
    ref(tmp_path, "docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n")
    ref(tmp_path, ".codex/prompts/hmasd-portfolio.md", b"portfolio prompt\n")
    ref(tmp_path, "docs/research/portfolio/PORTFOLIO.md", b"portfolio\n")
    ref(tmp_path, "docs/research/portfolio/workflow/registry.json", b"{}\n")
    result = run_cli(
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", "portfolio",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "Portfolio", "--recipient-thread-id", "portfolio",
        "--objective", "Choose the next bounded portfolio transition.",
        "--control-release-envelope", ingress["locator"],
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads((tmp_path / json.loads(result.stdout)["locator"]).read_text())
    assert envelope["body"]["done_when"] == [
        "Before final, send exactly one correlated v3 PORTFOLIO_RETURN to Workflow-Clerk."
    ]


def test_assignment_from_brief_copies_release_from_ingress_envelope(tmp_path: Path) -> None:
    ingress = root_ingress(tmp_path)
    ref(tmp_path, "docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n")
    ref(tmp_path, ".codex/prompts/hmasd-em.md", b"em prompt\n")
    ref(tmp_path, "docs/research/candidates/ucope/DIRECTION.md", b"direction\n")
    ref(tmp_path, "docs/research/candidates/ucope/workflow/research/state.json", b"{}\n")
    ref(tmp_path, "docs/research/candidates/ucope/workflow/engineering/state.json", b"{}\n")

    result = run_cli(
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "EM/ucope/g2", "--recipient-thread-id", "em",
        "--objective", "Continue the bounded scientific slice.",
        "--control-release-envelope", ingress["locator"],
    )

    assert result.returncode == 0, result.stderr
    generated = json.loads((tmp_path / json.loads(result.stdout)["locator"]).read_text())
    source = json.loads((tmp_path / ingress["locator"]).read_text())
    assert generated["control_release"] == source["control_release"]


def test_assignment_from_brief_rejects_non_ingress_release_source(tmp_path: Path) -> None:
    outbound = assign(tmp_path)
    ref(tmp_path, "docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n")
    ref(tmp_path, ".codex/prompts/hmasd-em.md", b"em prompt\n")
    ref(tmp_path, "docs/research/candidates/ucope/workflow/research/state.json", b"{}\n")
    ref(tmp_path, "docs/research/candidates/ucope/workflow/engineering/state.json", b"{}\n")

    result = run_cli(
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "EM/ucope/g2", "--recipient-thread-id", "em",
        "--objective", "Continue the bounded scientific slice.",
        "--control-release-envelope", outbound["locator"],
    )

    assert result.returncode == 2
    assert "recipient must be Workflow-Clerk" in result.stderr


def test_assignment_from_brief_builds_root_to_clerk_from_current_release(
    tmp_path: Path,
) -> None:
    for path, content in (
        ("AGENTS.md", b"instructions\n"),
        ("docs/project/WORKFLOW_PROTOCOL.md", b"protocol\n"),
        (".codex/prompts/hmasd-workflow-clerk.md", b"clerk prompt\n"),
    ):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for command in (
        ("git", "init", "-b", "main"),
        ("git", "config", "user.email", "test@example.invalid"),
        ("git", "config", "user.name", "HMASD Test"),
        ("git", "add", "."),
        ("git", "commit", "-m", "published control"),
        ("git", "remote", "add", "origin", str(tmp_path)),
        ("git", "update-ref", "refs/remotes/origin/main", "HEAD"),
    ):
        completed = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr

    result = run_cli(
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", "portfolio",
        "--sender-identity", "Root", "--sender-thread-id", "root",
        "--recipient-identity", "Workflow-Clerk", "--recipient-thread-id", "clerk",
        "--objective", "Route one bounded coordination slice.",
        "--effect", "native_message_send:Portfolio",
        "--current-control-release",
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads((tmp_path / json.loads(result.stdout)["locator"]).read_text())
    assert envelope["sender"]["identity"] == "Root"
    assert envelope["recipient"]["identity"] == "Workflow-Clerk"
    assert envelope["control_release"]["publishable"] is True
    assert envelope["body"]["effects"] == ["native_message_send:Portfolio"]
    assert envelope["body"]["done_when"] == [
        "Before final, complete every ready native send and the bounded final drain."
    ]


def test_assignment_rejects_malformed_or_unpublishable_control_release(tmp_path: Path) -> None:
    for path in (
        "docs/project/WORKFLOW_PROTOCOL.md",
        ".codex/prompts/hmasd-em.md",
        "docs/research/candidates/ucope/DIRECTION.md",
        "docs/research/candidates/ucope/workflow/research/state.json",
        "docs/research/candidates/ucope/workflow/engineering/state.json",
    ):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"{}\n" if path.endswith(".json") else b"context\n")
    common = [
        "assignment-from-brief", "--repo", str(tmp_path), "--direction-id", "ucope",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "c",
        "--recipient-identity", "EM/ucope/g1", "--recipient-thread-id", "e",
        "--objective", "close one bounded slice",
    ]
    malformed = release_record(); malformed["extra"] = True
    malformed_ingress = root_ingress(tmp_path, release=malformed)
    result = run_cli(*common, "--control-release-envelope", malformed_ingress["locator"])
    assert result.returncode == 2 and "control release" in result.stderr
    unpublished_ingress = root_ingress(tmp_path, release=release_record(publishable=False))
    result = run_cli(*common, "--control-release-envelope", unpublished_ingress["locator"])
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


def test_control_notice_actions_require_exact_correlations_and_replacement(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    for action in ("PAUSE", "CANCEL"):
        missing = {
            "action": action, "reason": "control this exact assignment",
            "target_identity": "EM/ucope/g1",
            "scope": {"direction_id": "ucope", "affected_locator": None},
        }
        rejected = run_notice(tmp_path, missing)
        assert rejected.returncode == 2
        assert f"{action} requires an affected locator" in rejected.stderr

    override = {
        "action": "OVERRIDE", "reason": "replace the bounded slice",
        "target_identity": "EM/ucope/g1",
        "scope": {"direction_id": "ucope", "affected_locator": assigned["locator"]},
    }
    missing_replacement = run_notice(tmp_path, override)
    assert missing_replacement.returncode == 2
    assert "OVERRIDE requires exact scope.replacement" in missing_replacement.stderr
    override["scope"]["replacement"] = {"objective": "new bounded objective", "effects": "none"}
    malformed_replacement = run_notice(tmp_path, override)
    assert malformed_replacement.returncode == 2
    assert "replacement.effects" in malformed_replacement.stderr

    pause = {
        "action": "PAUSE", "reason": "pause the current bounded work",
        "target_identity": "EM/ucope/g1",
        "scope": {"direction_id": "ucope", "affected_locator": assigned["locator"]},
    }
    paused = run_notice(tmp_path, pause)
    assert paused.returncode == 0, paused.stderr
    paused_locator = json.loads(paused.stdout)["locator"]
    resume = {
        "action": "RESUME", "reason": "the named pause condition is cleared",
        "target_identity": "EM/ucope/g1",
        "scope": {"direction_id": "ucope", "affected_locator": paused_locator},
    }
    resumed = run_notice(tmp_path, resume)
    assert resumed.returncode == 0, resumed.stderr
    resume["scope"]["affected_locator"] = assigned["locator"]
    invalid_resume = run_notice(tmp_path, resume)
    assert invalid_resume.returncode == 2
    assert "RESUME must correlate to PAUSE or CANCEL" in invalid_resume.stderr


def test_clerk_relay_cannot_weaken_override_semantics(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    initiating = {
        "action": "OVERRIDE", "reason": "replace this bounded objective and Effect fence",
        "target_identity": "EM/ucope/g1",
        "scope": {
            "direction_id": "ucope", "affected_locator": assigned["locator"],
            "replacement": {
                "objective": "evaluate only the replacement discriminator",
                "effects": ["no external send", "write only direction authority"],
            },
        },
    }
    initiated = run_notice(tmp_path, initiating)
    assert initiated.returncode == 0, initiated.stderr
    relay = json.loads(json.dumps(initiating))
    relay["scope"]["affected_locator"] = json.loads(initiated.stdout)["locator"]
    relay["scope"]["replacement"]["effects"] = ["external send is now allowed"]
    weakened = run_notice(
        tmp_path, relay, sender="Workflow-Clerk", sender_thread="clerk",
        recipient="EM/ucope/g1", recipient_thread="participant",
    )
    assert weakened.returncode == 2
    assert "relay must copy initiating body semantics" in weakened.stderr


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


def test_read_message_requires_exact_v3_line_and_reads_trusted_local_body(
    tmp_path: Path,
) -> None:
    assigned = assign(tmp_path)
    wrong_header = assigned["message"].replace(
        "HMASD_SESSION_ENVELOPE_V3", "HMASD_SESSION_ENVELOPE"
    )
    assert run_cli(
        "read-message", "--repo", str(tmp_path), "--message", wrong_header,
    ).returncode == 2
    wrapped = run_cli("read-message", "--repo", str(tmp_path), "--message", assigned["message"] + " please")
    assert wrapped.returncode == 2
    envelope = json.loads((tmp_path / assigned["locator"]).read_text())
    envelope["body"]["objective"] = "trusted local update"
    write_json(tmp_path / assigned["locator"], envelope)
    read = run_cli("read", "--repo", str(tmp_path), "--envelope", assigned["locator"])
    assert read.returncode == 0, read.stderr
    observed = json.loads(read.stdout)
    assert observed["envelope"]["body"]["objective"] == "trusted local update"
    assert "body_sha256" not in observed["envelope"]


def test_correlated_return_accepts_owned_context_mutation_after_intake(
    tmp_path: Path,
) -> None:
    assigned = assign(tmp_path)
    intake = run_cli(
        "read-message", "--repo", str(tmp_path), "--message", assigned["message"],
    )
    assert intake.returncode == 0, intake.stderr

    context_path = "docs/research/candidates/ucope/DIRECTION.md"
    changed_content = b"participant-owned research authority after the slice\n"
    (tmp_path / context_path).write_bytes(changed_content)
    body = return_body(changed_paths=[context_path])
    body["artifact_refs"] = [{
        "path": context_path, "sha256": hashlib.sha256(changed_content).hexdigest(),
    }]

    returned = make_return(tmp_path, assigned, body)
    returned_message = run_cli(
        "read-message", "--repo", str(tmp_path), "--message", returned["message"],
    )
    assert returned_message.returncode == 0, returned_message.stderr


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


def test_external_effect_unknown_is_never_retryable_or_history_eligible(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="CM/ucope/g1")
    failure = {
        "scope": "effect", "code": "PUSH_OUTCOME_UNKNOWN",
        "fingerprint": "unknown-push-effect", "responsible_role": "CM",
        "retryable": True, "attempt": 1, "max_attempts": 3,
        "summary": "the external push commitment cannot yet be determined",
    }
    body_path = tmp_path / "retryable-unknown.json"
    write_json(body_path, return_body(status="FAILED", failure=failure))
    rejected = run_cli(
        "return", "--repo", str(tmp_path), "--assignment", assigned["locator"],
        "--body", str(body_path),
    )
    assert rejected.returncode == 2
    assert "UNKNOWN external Effect" in rejected.stderr

    failure["retryable"] = False
    output = make_return(tmp_path, assigned, return_body(status="FAILED", failure=failure))
    history = run_cli(
        "failure-history", "--repo", str(tmp_path),
        "--fingerprint", failure["fingerprint"], "--return", output["locator"],
    )
    assert history.returncode == 0, history.stderr
    observed = json.loads(history.stdout)
    assert observed["retry_eligible"] is False
    assert observed["exhausted"] is True
    assert observed["next_attempt"] is None


def test_portfolio_return_rejects_unbound_unvalidated_decision(tmp_path: Path) -> None:
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
    assert result.returncode == 2
    assert "decision_ref" in result.stderr
