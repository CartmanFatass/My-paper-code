from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from scripts import hmasd_state


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "hmasd_state.py"
ENVELOPE_CLI = ROOT / "scripts" / "hmasd_session_envelope.py"


def _bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_bytes(value))


def _snapshot_digest(registry_bytes: bytes, proposed_direction_ids: list[str]) -> str:
    snapshot = {
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "proposed_candidates": [
            {"direction_id": direction_id}
            for direction_id in sorted(proposed_direction_ids)
        ],
    }
    return hashlib.sha256(_bytes(snapshot)).hexdigest()


def _run(repo_root: Path, registry: Path, decision: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "portfolio-apply",
            "--repo-root",
            str(repo_root),
            "--registry",
            str(registry),
            "--input",
            str(decision),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_envelope(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENVELOPE_CLI), *args], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )


def _registry(portfolio_sha: str) -> dict:
    return {
        "schema_version": 1,
        "revision": 7,
        "updated_at": "2026-08-27T20:00:00Z",
        "writer": "Portfolio",
        "workflow_version": "hmasd-autonomous-v1",
        "goal": {
            "path": "docs/research/portfolio/PORTFOLIO.md",
            "sha256": portfolio_sha,
        },
        "directions": [
            {
                "id": "alpha",
                "abbreviation": "ALPHA",
                "path": "docs/research/candidates/alpha",
                "lifecycle": "ACTIVE",
                "dependencies": [],
                "lifecycle_decision_ref": {
                    "path": "docs/research/portfolio/PORTFOLIO.md",
                    "heading": "Initial alpha decision",
                    "sha256": portfolio_sha,
                },
                "reactivation_condition_ref": None,
                "agent": {
                    "logical_identity": "EM-alpha",
                    "job_name": "EMAlpha",
                    "generation": 1,
                    "runtime_ref": None,
                },
                "research_state_path": "docs/research/candidates/alpha/workflow/research/state.json",
                "engineering_state_path": "docs/research/candidates/alpha/workflow/engineering/state.json",
                "external_review_index_path": "docs/research/candidates/alpha/workflow/external-review/index.json",
            }
        ],
    }


def _decision(registry_bytes: bytes, evidence_sha256: str) -> dict:
    evidence = {
        "path": "docs/research/evidence/snapshot-source.md",
        "sha256": evidence_sha256,
    }
    return {
        "schema_version": 1,
        "decision_id": "activate-beta-20260827",
        "decided_at": "2026-08-27T20:05:00Z",
        "summary": "Keep alpha active and activate beta for scientific definition.",
        "expected_registry_revision": 7,
        "expected_registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "snapshot_digest": _snapshot_digest(registry_bytes, ["beta"]),
        "proposed_candidates": [{"direction_id": "beta"}],
        "considered": [
            {
                "direction_id": "alpha",
                "disposition": "KEEP_ACTIVE",
                "priority": 1,
                "summary": "Alpha remains within the active capacity decision.",
                "evidence_refs": [evidence],
            },
            {
                "direction_id": "beta",
                "disposition": "ACTIVATE",
                "priority": 2,
                "summary": "Beta is the selected new scientific definition.",
                "evidence_refs": [evidence],
            },
        ],
        "transitions": [
            {
                "direction_id": "beta",
                "lifecycle": "ACTIVE",
                "summary": "Open beta as the selected new direction.",
                "next_role": "EM",
                "next_objective": "Define the bounded beta scientific question and evidence ceiling.",
                "reactivation_condition": None,
                "new_direction": {
                    "title": "Bounded beta scientific direction",
                    "abbreviation": "BETA",
                    "scientific_question": "Can beta expose a decision-relevant finite mechanism?",
                    "dependencies": [],
                    "base_sha": "0123456789abcdef0123456789abcdef01234567",
                },
            },
            {
                "direction_id": "alpha",
                "lifecycle": "ACTIVE",
                "summary": "Keep alpha active while changing its bounded next objective.",
                "next_role": "EM",
                "next_objective": "Evaluate alpha against the newly compared global cohort.",
                "reactivation_condition": None,
                "new_direction": None,
            },
        ],
        "capacity": {
            "active_limit": 2,
            "active_before": 1,
            "active_after": 2,
            "active_direction_ids": ["alpha", "beta"],
            "resource_constraints": ["Only one new scientific definition can be opened."],
            "unused_capacity_reason": None,
        },
    }


def test_portfolio_apply_records_a_declined_proposal_without_registering_it(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    portfolio = repo_root / "docs/research/portfolio/PORTFOLIO.md"
    portfolio.parent.mkdir(parents=True)
    portfolio.write_text("# Test portfolio\n", encoding="utf-8", newline="\n")
    registry = repo_root / "docs/research/portfolio/workflow/registry.json"
    initial = _registry(hashlib.sha256(portfolio.read_bytes()).hexdigest())
    _write(registry, initial)
    registry_before = registry.read_bytes()
    evidence = repo_root / "docs/research/evidence/snapshot-source.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("# Stable snapshot evidence\n", encoding="utf-8", newline="\n")
    evidence_ref = {
        "path": "docs/research/evidence/snapshot-source.md",
        "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
    }
    decision = _decision(registry_before, evidence_ref["sha256"])
    decision.update(
        decision_id="decline-gamma-20260827",
        summary="Keep alpha active and decline the proposed gamma candidate.",
        snapshot_digest=_snapshot_digest(registry_before, ["gamma"]),
        proposed_candidates=[{"direction_id": "gamma"}],
        considered=[
            decision["considered"][0],
            {
                "direction_id": "gamma",
                "disposition": "DECLINE",
                "priority": 2,
                "summary": "Gamma does not justify scarce scientific capacity.",
                "evidence_refs": [evidence_ref],
            },
        ],
        transitions=[],
        capacity={
            "active_limit": 1,
            "active_before": 1,
            "active_after": 1,
            "active_direction_ids": ["alpha"],
            "resource_constraints": ["No capacity remains for gamma."],
            "unused_capacity_reason": None,
        },
    )
    decision_path = tmp_path / "declined.json"
    _write(decision_path, decision)

    result = _run(repo_root, registry, decision_path)

    assert result.returncode == 0, result.stderr
    updated = json.loads(registry.read_text(encoding="utf-8"))
    assert updated["revision"] == 8
    assert [item["id"] for item in updated["directions"]] == ["alpha"]
    assert not (repo_root / "docs/research/candidates/gamma").exists()
    authority = repo_root / "docs/research/portfolio/decisions/decline-gamma-20260827.json"
    assert authority.read_bytes() == _bytes(decision)
    portfolio_text = portfolio.read_text(encoding="utf-8")
    assert "Considered `gamma` — priority `2`, disposition `DECLINE`" in portfolio_text
    assert "- No lifecycle transition." in portfolio_text


def test_portfolio_apply_is_one_atomic_public_decision_boundary(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    portfolio = repo_root / "docs/research/portfolio/PORTFOLIO.md"
    portfolio.parent.mkdir(parents=True)
    portfolio.write_text("# Test portfolio\n", encoding="utf-8", newline="\n")
    registry = repo_root / "docs/research/portfolio/workflow/registry.json"
    initial = _registry(hashlib.sha256(portfolio.read_bytes()).hexdigest())
    _write(registry, initial)
    registry_before = registry.read_bytes()
    portfolio_before = portfolio.read_bytes()
    evidence = repo_root / "docs/research/evidence/snapshot-source.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("# Stable snapshot evidence\n", encoding="utf-8", newline="\n")
    valid = _decision(registry_before, hashlib.sha256(evidence.read_bytes()).hexdigest())

    invalid_cases = []
    stale = copy.deepcopy(valid)
    stale["expected_registry_revision"] = 6
    invalid_cases.append(("stale", stale, "expected revision 6, observed 7"))
    stale_registry = copy.deepcopy(valid)
    stale_registry["expected_registry_sha256"] = "f" * 64
    invalid_cases.append(("registry-sha", stale_registry, "expected_registry_sha256"))
    invalid_snapshot = copy.deepcopy(valid)
    invalid_snapshot["snapshot_digest"] = "not-a-sha"
    invalid_cases.append(("snapshot", invalid_snapshot, "snapshot_digest"))
    incomplete = copy.deepcopy(valid)
    incomplete["considered"] = [valid["considered"][1]]
    invalid_cases.append(("coverage", incomplete, "does not cover snapshot directions"))
    outside = copy.deepcopy(valid)
    outside["transitions"][0]["direction_id"] = "gamma"
    invalid_cases.append(("subset", outside, "transition direction is not considered"))
    undefined = copy.deepcopy(valid)
    undefined["considered"].append(
        {
            "direction_id": "alpah",
            "disposition": "KEEP_ACTIVE",
            "priority": 3,
            "summary": "A typo must not become an implicit proposal.",
            "evidence_refs": valid["considered"][0]["evidence_refs"],
        }
    )
    invalid_cases.append(("undefined-typo", undefined, "considered contains undefined directions"))
    changed_snapshot_cohort = copy.deepcopy(valid)
    changed_snapshot_cohort["proposed_candidates"].append({"direction_id": "gamma"})
    changed_snapshot_cohort["considered"].append(
        {
            "direction_id": "gamma",
            "disposition": "DECLINE",
            "priority": 3,
            "summary": "Gamma is part of a different frozen cohort.",
            "evidence_refs": valid["considered"][0]["evidence_refs"],
        }
    )
    invalid_cases.append(("snapshot-cohort", changed_snapshot_cohort, "snapshot_digest mismatch"))
    nonexact_proposal = copy.deepcopy(valid)
    nonexact_proposal["proposed_candidates"][0]["extra"] = "not in the contract"
    invalid_cases.append(("proposal-shape", nonexact_proposal, "must contain exactly direction_id"))
    bad_evidence = copy.deepcopy(valid)
    bad_evidence["considered"][0]["evidence_refs"][0]["sha256"] = "f" * 64
    invalid_cases.append(("evidence", bad_evidence, "evidence_refs[0].sha256 does not match"))
    nonexact_transition = copy.deepcopy(valid)
    nonexact_transition["transitions"][0]["extra"] = "not in the contract"
    invalid_cases.append(("transition-shape", nonexact_transition, "must contain exactly"))
    nonexact_new_direction = copy.deepcopy(valid)
    nonexact_new_direction["transitions"][0]["new_direction"]["extra"] = "not in the contract"
    invalid_cases.append(("new-direction-shape", nonexact_new_direction, "new_direction must contain exactly"))
    active_reactivation = copy.deepcopy(valid)
    active_reactivation["transitions"][0]["reactivation_condition"] = "after another result"
    invalid_cases.append(("active-reactivation", active_reactivation, "ACTIVE reactivation_condition must be null"))
    parked_without_condition = copy.deepcopy(valid)
    parked_without_condition["transitions"][0].update(
        lifecycle="PARKED",
        next_role="Root",
        next_objective="Should beta receive a later scientific investment?",
        reactivation_condition=None,
    )
    invalid_cases.append(("parked", parked_without_condition, "PARKED reactivation_condition is required"))
    closed_with_route = copy.deepcopy(valid)
    closed_with_route["transitions"][0]["lifecycle"] = "CLOSED"
    invalid_cases.append(("closed", closed_with_route, "CLOSED next fields must be null"))
    inconsistent_before = copy.deepcopy(valid)
    inconsistent_before["capacity"]["active_before"] = 0
    invalid_cases.append(("capacity-before", inconsistent_before, "capacity active_before"))
    inconsistent_after = copy.deepcopy(valid)
    inconsistent_after["capacity"]["active_after"] = 1
    invalid_cases.append(("capacity-after", inconsistent_after, "capacity active_after"))
    unused_without_reason = copy.deepcopy(valid)
    unused_without_reason["capacity"]["active_limit"] = 3
    invalid_cases.append(("capacity-unused", unused_without_reason, "unused_capacity_reason is required"))
    nonexact_capacity = copy.deepcopy(valid)
    nonexact_capacity["capacity"]["active_count"] = 2
    invalid_cases.append(("capacity-shape", nonexact_capacity, "capacity must contain exactly"))

    for label, decision, error in invalid_cases:
        decision_path = tmp_path / f"{label}.json"
        _write(decision_path, decision)
        result = _run(repo_root, registry, decision_path)
        assert result.returncode != 0, result.stdout
        assert error in result.stderr
        assert registry.read_bytes() == registry_before
        assert portfolio.read_bytes() == portfolio_before
        assert not (repo_root / "docs/research/candidates/beta").exists()
        assert not (repo_root / "docs/research/portfolio/decisions").exists()

    collision_root = repo_root / "docs/research/candidates/beta"
    collision_root.mkdir(parents=True)
    collision_marker = collision_root / "existing.txt"
    collision_marker.write_text("preserve me\n", encoding="utf-8")
    collision_decision = tmp_path / "collision.json"
    _write(collision_decision, valid)
    collision_result = _run(repo_root, registry, collision_decision)
    assert collision_result.returncode != 0
    assert "new direction path already exists" in collision_result.stderr
    assert registry.read_bytes() == registry_before
    assert portfolio.read_bytes() == portfolio_before
    assert collision_marker.read_text(encoding="utf-8") == "preserve me\n"
    assert not (repo_root / "docs/research/portfolio/decisions").exists()
    collision_marker.unlink()
    collision_root.rmdir()

    decision_path = tmp_path / "valid.json"
    _write(decision_path, valid)
    result = _run(repo_root, registry, decision_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok\n"

    decision_authority = repo_root / "docs/research/portfolio/decisions/activate-beta-20260827.json"
    decision_bytes = _bytes(valid)
    assert decision_authority.read_bytes() == decision_bytes
    decision_sha = hashlib.sha256(decision_bytes).hexdigest()

    updated = json.loads(registry.read_text(encoding="utf-8"))
    assert updated["revision"] == 8
    assert updated["updated_at"] == valid["decided_at"]
    assert updated["goal"]["sha256"] == hashlib.sha256(portfolio.read_bytes()).hexdigest()
    beta = next(item for item in updated["directions"] if item["id"] == "beta")
    assert beta["lifecycle"] == "ACTIVE"
    assert beta["lifecycle_decision_ref"] == {
        "path": "docs/research/portfolio/decisions/activate-beta-20260827.json",
        "heading": valid["summary"],
        "sha256": decision_sha,
    }
    assert beta["agent"] == {
        "logical_identity": "EM-beta",
        "job_name": "EMBeta",
        "generation": 1,
        "runtime_ref": None,
    }

    direction_root = repo_root / "docs/research/candidates/beta"
    direction_bytes = (direction_root / "DIRECTION.md").read_bytes()
    direction_text = direction_bytes.decode("utf-8")
    assert "Can beta expose a decision-relevant finite mechanism?" in direction_text
    assert "Next role: `EM`" in direction_text
    assert valid["transitions"][0]["next_objective"] in direction_text
    direction_sha = hashlib.sha256(direction_bytes).hexdigest()

    research = json.loads((direction_root / "workflow/research/state.json").read_text())
    engineering = json.loads((direction_root / "workflow/engineering/state.json").read_text())
    external = json.loads((direction_root / "workflow/external-review/index.json").read_text())
    assert research["writer"] == "EM-beta"
    assert research["registry_revision_seen"] == 8
    assert research["actionable"] is True
    assert research["direction_ref"]["sha256"] == direction_sha
    assert research["next_action"]["input_refs"] == [
        {"path": "docs/research/portfolio/decisions/activate-beta-20260827.json", "sha256": decision_sha}
    ]
    assert engineering["writer"] == "CM-beta"
    assert engineering["phase"] == "UNREQUESTED"
    assert engineering["scope_ref"]["sha256"] == direction_sha
    assert external == {
        "direction_id": "beta",
        "revision": 1,
        "rounds": [],
        "schema_version": 1,
        "updated_at": valid["decided_at"],
        "workflow_version": "hmasd-external-review-v1",
        "writer": "EM-beta",
    }
    portfolio_text = portfolio.read_text(encoding="utf-8")
    assert "activate-beta-20260827" in portfolio_text
    assert "docs/research/portfolio/decisions/activate-beta-20260827.json" in portfolio_text
    assert f"Snapshot provenance: `{valid['snapshot_digest']}`" in portfolio_text
    assert "Active capacity: `1 -> 2 / 2`" in portfolio_text
    assert "Considered `alpha` — priority `1`, disposition `KEEP_ACTIVE`" in portfolio_text
    assert "Only one new scientific definition can be opened." in portfolio_text

    portfolio_return = {
        "registry_revision": 8,
        "snapshot_digest": valid["snapshot_digest"],
        "considered": valid["considered"],
        "transitions": valid["transitions"],
        "capacity": valid["capacity"],
        "summary": valid["summary"],
        "decision_ref": {
            "path": "docs/research/portfolio/decisions/activate-beta-20260827.json",
            "sha256": decision_sha,
        },
        "artifact_refs": [],
        "failure": None,
    }
    validated = hmasd_state.validate_portfolio_return(repo_root, portfolio_return)
    assert validated["decision_id"] == valid["decision_id"]

    for path, text in (
        ("docs/project/WORKFLOW_PROTOCOL.md", "protocol\n"),
        (".codex/prompts/hmasd-portfolio.md", "portfolio prompt\n"),
    ):
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    release = {
        "control_release_id": "a" * 64, "protocol_epoch": 2,
        "head": "1" * 40, "origin_main": "1" * 40, "branch": "main",
        "control_paths": ["AGENTS.md"], "dirty_control_paths": [],
        "publishable": True, "observed_at": "2026-08-27T20:10:00Z",
    }
    ingress_body = {
        "objective": "route one bounded Portfolio slice", "context_refs": [],
        "owned_paths": [], "effects": ["native_message_send:Portfolio"],
        "constraints": ["preserve semantics"], "done_when": ["route once"],
        "workspace_mode": "shared-main",
    }
    message_id = str(uuid.uuid4())
    body_digest = hashlib.sha256(json.dumps(
        ingress_body, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode()).hexdigest()
    ingress = {
        "schema_version": 2, "protocol_epoch": 2, "message_id": message_id,
        "direction_id": "portfolio", "sender": {"identity": "Root", "thread_id": "root"},
        "recipient": {"identity": "Workflow-Clerk", "thread_id": "clerk"},
        "kind": "ASSIGNMENT", "reply_to": None, "body_sha256": body_digest,
        "control_release": release, "body": ingress_body,
    }
    ingress_path = (
        repo_root / ".codex/runtime/session-envelopes/portfolio"
        / f"{message_id}.assignment.json"
    )
    _write(ingress_path, ingress)
    assigned = _run_envelope(
        "assignment-from-brief", "--repo", str(repo_root), "--direction-id", "portfolio",
        "--sender-identity", "Workflow-Clerk", "--sender-thread-id", "clerk",
        "--recipient-identity", "Portfolio", "--recipient-thread-id", "portfolio",
        "--objective", "return the already committed global Portfolio decision",
        "--owned-path", "docs/research/portfolio/",
        "--constraint", "do not repeat portfolio-apply",
        "--done-when", "send one validated PORTFOLIO_RETURN",
        "--control-release-envelope", ingress_path.relative_to(repo_root).as_posix(),
    )
    assert assigned.returncode == 0, assigned.stderr
    assignment_output = json.loads(assigned.stdout)
    return_path = tmp_path / "portfolio-return.json"
    _write(return_path, portfolio_return)
    returned = _run_envelope(
        "portfolio-return", "--repo", str(repo_root),
        "--assignment", assignment_output["locator"], "--body", str(return_path),
    )
    assert returned.returncode == 0, returned.stderr
    return_output = json.loads(returned.stdout)
    read = _run_envelope(
        "read", "--repo", str(repo_root), "--envelope", return_output["locator"],
    )
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout)["envelope"]["body"]["decision_ref"] == portfolio_return["decision_ref"]

    envelope_path = repo_root / return_output["locator"]
    tampered_envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    tampered_envelope["body"]["considered"][0]["extra"] = "invalid on read"
    tampered_envelope["body_sha256"] = hashlib.sha256(
        json.dumps(
            tampered_envelope["body"], ensure_ascii=False,
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    _write(envelope_path, tampered_envelope)
    rejected_read = _run_envelope(
        "read", "--repo", str(repo_root), "--envelope", return_output["locator"],
    )
    assert rejected_read.returncode == 2
    assert "considered[0]" in rejected_read.stderr

    malformed = copy.deepcopy(portfolio_return)
    malformed["considered"][0]["extra"] = "not exact"
    with pytest.raises(hmasd_state.ValidationError, match=r"considered\[0\].*exactly"):
        hmasd_state.validate_portfolio_return(repo_root, malformed)


def test_failed_portfolio_return_binds_attempt_but_reports_current_committed_state(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    portfolio = repo_root / "docs/research/portfolio/PORTFOLIO.md"
    portfolio.parent.mkdir(parents=True)
    portfolio.write_text("# Test portfolio\n", encoding="utf-8", newline="\n")
    registry = repo_root / "docs/research/portfolio/workflow/registry.json"
    initial = _registry(hashlib.sha256(portfolio.read_bytes()).hexdigest())
    _write(registry, initial)
    registry_bytes = registry.read_bytes()
    evidence = repo_root / "docs/research/evidence/snapshot-source.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("# Stable snapshot evidence\n", encoding="utf-8", newline="\n")
    attempted = _decision(registry_bytes, hashlib.sha256(evidence.read_bytes()).hexdigest())
    attempt_path = repo_root / ".codex/runtime/attempted-portfolio-decision.json"
    _write(attempt_path, attempted)
    failed_return = {
        "registry_revision": 7,
        "snapshot_digest": attempted["snapshot_digest"],
        "considered": attempted["considered"],
        "transitions": [],
        "capacity": {
            "active_limit": 2, "active_before": 1, "active_after": 1,
            "active_direction_ids": ["alpha"],
            "resource_constraints": ["The attempted atomic apply did not commit."],
            "unused_capacity_reason": "Beta remains only proposed after the failed apply.",
        },
        "summary": "The attempted apply failed and the committed registry remains unchanged.",
        "decision_ref": {
            "path": ".codex/runtime/attempted-portfolio-decision.json",
            "sha256": hashlib.sha256(attempt_path.read_bytes()).hexdigest(),
        },
        "artifact_refs": [],
        "failure": {"typed": "validated by the envelope"},
    }

    validated = hmasd_state.validate_portfolio_return(repo_root, failed_return)
    assert validated["decision_id"] == attempted["decision_id"]
    assert registry.read_bytes() == registry_bytes
    assert not (repo_root / "docs/research/portfolio/decisions").exists()

    pretended_commit = copy.deepcopy(failed_return)
    pretended_commit["transitions"] = attempted["transitions"]
    with pytest.raises(hmasd_state.ValidationError, match="must not report committed transitions"):
        hmasd_state.validate_portfolio_return(repo_root, pretended_commit)
