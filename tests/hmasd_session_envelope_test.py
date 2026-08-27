from __future__ import annotations

import hashlib, json, subprocess, sys, uuid
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/hmasd_session_envelope.py"

def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, check=False, capture_output=True, text=True)

def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value), encoding="utf-8")

def ref(repo: Path, path: str, content: bytes) -> dict[str, str]:
    target = repo / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
    return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}

def assignment_body(repo: Path, direction: str = "ucope") -> dict[str, object]:
    return {"objective": "close one bounded slice", "context_refs": [ref(repo, f"docs/research/candidates/{direction}/DIRECTION.md", b"authority\n")], "owned_paths": [f"docs/research/candidates/{direction}/"], "effects": [], "constraints": ["preserve semantics"], "done_when": ["return once"], "workspace_mode": "shared-main"}

def assign(repo: Path, *, recipient: str = "EM/ucope/g1", direction: str = "ucope") -> dict[str, object]:
    body_path = repo / "body.json"; write_json(body_path, assignment_body(repo, direction))
    result = run_cli("assignment", "--repo", str(repo), "--direction-id", direction, "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk", "--recipient-identity", recipient, "--recipient-thread-id", "participant", "--body", str(body_path))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)

def test_assignment_builds_v2_digest_bound_transport(tmp_path: Path) -> None:
    output = assign(tmp_path); locator = output["locator"]; envelope = json.loads((tmp_path / locator).read_text())
    uuid.UUID(envelope["message_id"])
    assert envelope["schema_version"] == envelope["protocol_epoch"] == 2
    assert envelope["body_sha256"] == "31912ea5da703b9765ad1ab90affb59c2ba82e26b0ee9b2525bb4d0fdd941194"
    assert output["message"] == f"HMASD_SESSION_ENVELOPE_V2 kind=ASSIGNMENT direction=ucope from=Workflow-Clerk to=EM/ucope/g1 next=NONE id={envelope['message_id']} sha256={envelope['body_sha256']} locator={locator}"
    assert set(envelope["git_facts"]) == {"branch", "head", "origin_main", "dirty_paths", "head_published"}
    assert envelope["control_release"]["protocol_epoch"] == 2

def test_return_reverses_endpoints_correlates_and_derives_next_role(tmp_path: Path) -> None:
    assigned = assign(tmp_path); artifact = ref(tmp_path, "docs/research/candidates/ucope/RESULT.md", b"result\n")
    body = {"status": "REQUEST_CM", "summary": "science is frozen", "changed_paths": [artifact["path"]], "artifact_refs": [artifact], "next_objective": "implement it", "failure": None}
    body_path = tmp_path / "return.json"; write_json(body_path, body)
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout); envelope = json.loads((tmp_path / output["locator"]).read_text()); assignment = json.loads((tmp_path / assigned["locator"]).read_text())
    assert envelope["reply_to"] == assignment["message_id"]
    assert envelope["sender"] == assignment["recipient"] and envelope["recipient"] == assignment["sender"]
    assert " next=CM " in output["message"]

def test_return_rejects_done_and_requires_complete_typed_failure(tmp_path: Path) -> None:
    assigned = assign(tmp_path); body_path = tmp_path / "return.json"
    write_json(body_path, {"status": "DONE", "summary": "not legal", "changed_paths": [], "artifact_refs": [], "next_objective": None, "failure": None})
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 2 and "status is invalid" in result.stderr
    failure = {"scope": "direction", "code": "OOM", "fingerprint": "same-oom", "responsible_role": "CM", "retryable": True, "attempt": 4, "max_attempts": 4, "summary": "too many retries"}
    write_json(body_path, {"status": "FAILED", "summary": "bounded failure", "changed_paths": [], "artifact_refs": [], "next_objective": None, "failure": failure})
    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 2 and "max_attempts <= 3" in result.stderr

def test_read_message_rejects_v1_and_detects_transport_or_body_tampering(tmp_path: Path) -> None:
    assigned = assign(tmp_path)
    old = run_cli("read-message", "--repo", str(tmp_path), "--message", f"HMASD_SESSION_ENVELOPE_V1 {assigned['locator']}")
    assert old.returncode == 2
    wrapped = run_cli("read-message", "--repo", str(tmp_path), "--message", assigned["message"] + " please")
    assert wrapped.returncode == 2
    envelope = json.loads((tmp_path / assigned["locator"]).read_text()); envelope["body"]["objective"] = "tampered"; write_json(tmp_path / assigned["locator"], envelope)
    read = run_cli("read", "--repo", str(tmp_path), "--envelope", assigned["locator"])
    assert read.returncode == 2 and "body_sha256" in read.stderr

def test_structured_refs_and_changed_paths_are_repository_contained(tmp_path: Path) -> None:
    body = assignment_body(tmp_path); body["context_refs"] = [{"path": "../escape", "sha256": "0" * 64}]; body_path = tmp_path / "bad.json"; write_json(body_path, body)
    result = run_cli("assignment", "--repo", str(tmp_path), "--direction-id", "ucope", "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "c", "--recipient-identity", "EM/ucope/g1", "--recipient-thread-id", "e", "--body", str(body_path))
    assert result.returncode == 2 and "repository-relative POSIX" in result.stderr

def test_control_notice_supports_reanchor_without_becoming_release_action(tmp_path: Path) -> None:
    body = {"action": "REANCHOR", "reason": "epoch migration", "target_identity": "EM/ucope/g1", "scope": {"expected_control_release_id": "a" * 64}}
    body_path = tmp_path / "notice.json"; write_json(body_path, body)
    result = run_cli("control-notice", "--repo", str(tmp_path), "--direction-id", "ucope", "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "c", "--recipient-identity", "EM/ucope/g1", "--recipient-thread-id", "e", "--body", str(body_path))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout); assert "kind=CONTROL_NOTICE" in output["message"] and " next=NONE " in output["message"]

def test_portfolio_return_uses_global_body_and_never_compresses_next(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="Portfolio", direction="portfolio"); artifact = ref(tmp_path, "docs/research/portfolio/PORTFOLIO.md", b"portfolio\n")
    body = {"registry_revision": 7, "snapshot_digest": "b" * 64, "considered": ["ucope"], "transitions": [{"direction_id": "ucope", "next": "EM"}], "capacity": {"slots": 1}, "summary": "one bounded decision", "artifact_refs": [artifact], "failure": None}
    body_path = tmp_path / "portfolio.json"; write_json(body_path, body)
    result = run_cli("portfolio-return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))
    assert result.returncode == 0, result.stderr
    assert "kind=PORTFOLIO_RETURN" in json.loads(result.stdout)["message"] and " next=NONE " in json.loads(result.stdout)["message"]

def test_portfolio_return_accepts_typed_failure_and_keeps_next_none(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="Portfolio", direction="portfolio")
    failure = {"scope": "direction", "code": "REGISTRY_CONFLICT", "fingerprint": "registry-ucope-r7", "responsible_role": "Portfolio", "retryable": True, "attempt": 1, "max_attempts": 3, "summary": "registry revision changed"}
    body = {"registry_revision": 7, "snapshot_digest": "c" * 64, "considered": ["ucope"], "transitions": [], "capacity": {"slots": 1}, "summary": "bounded portfolio failure", "artifact_refs": [], "failure": failure}
    body_path = tmp_path / "portfolio-failure.json"; write_json(body_path, body)

    result = run_cli("portfolio-return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    envelope = json.loads((tmp_path / output["locator"]).read_text())
    assert envelope["body"]["failure"] == failure
    assert " next=NONE " in output["message"]

def test_portfolio_return_rejects_invalid_typed_failure(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="Portfolio", direction="portfolio")
    invalid_failure = {"scope": "direction", "code": "REGISTRY_CONFLICT", "responsible_role": "Portfolio", "retryable": True, "attempt": 1, "max_attempts": 3, "summary": "missing fingerprint"}
    body = {"registry_revision": 7, "snapshot_digest": "d" * 64, "considered": ["ucope"], "transitions": [], "capacity": {"slots": 1}, "summary": "malformed failure", "artifact_refs": [], "failure": invalid_failure}
    body_path = tmp_path / "invalid-portfolio-failure.json"; write_json(body_path, body)

    result = run_cli("portfolio-return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))

    assert result.returncode == 2
    assert "failure fields are invalid" in result.stderr

def test_portfolio_assignment_cannot_use_ordinary_return(tmp_path: Path) -> None:
    assigned = assign(tmp_path, recipient="Portfolio", direction="portfolio")
    body = {"status": "REQUEST_EM", "summary": "must use global return", "changed_paths": [], "artifact_refs": [], "next_objective": "continue science", "failure": None}
    body_path = tmp_path / "ordinary-return.json"; write_json(body_path, body)

    result = run_cli("return", "--repo", str(tmp_path), "--assignment", assigned["locator"], "--body", str(body_path))

    assert result.returncode == 2
    assert "global Portfolio assignment requires portfolio-return" in result.stderr
