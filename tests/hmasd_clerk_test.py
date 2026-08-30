"""Focused current-only contract tests for the one-shot HMASD Clerk."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import scripts.hmasd_clerk as clerk
from scripts import hmasd_state


SHA256 = "a" * 64
GIT_SHA = "b" * 40


def canonical(value: dict[str, Any]) -> bytes:
    return hmasd_state.canonical_bytes(value)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def content_ref(repo: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    (root / ".omp" / "runtime").mkdir(parents=True)
    return root


def state_packet(
    repo: Path,
    *,
    operation_id: str = "state-cas-operation",
    requires: list[dict[str, Any]] | None = None,
    state_kind: str = "runtime_agents",
) -> tuple[dict[str, Any], Path, Path]:
    state_path = repo / ".omp" / "runtime" / "agents.json"
    input_path = repo / "packets" / f"{operation_id}-input.json"
    write_json(
        state_path,
        {
            "schema_version": 2,
            "revision": 1,
            "updated_at": "2026-08-30T00:00:00Z",
            "writer": "Root",
            "agents": [],
        },
    )
    write_json(
        input_path,
        {
            "schema_version": 2,
            "revision": 2,
            "updated_at": "2026-08-30T00:00:01Z",
            "writer": "Root",
            "agents": [],
        },
    )
    packet: dict[str, Any] = {
        "schema_version": 1,
        "kind": "clerk_operation",
        "operation_id": operation_id,
        "clerk_assignment_id": "state-cas-clerk",
        "executor": {
            "role": "hmasd-clerk",
            "logical_identity": "Clerk-state-cas-clerk",
            "generation": 1,
        },
        "authorizer": {
            "role": "root",
            "logical_identity": "Root",
            "generation": 1,
            "assignment_id": "root-authorizer-one",
        },
        "operation": "STATE_CAS",
        "requires": requires or [],
        "authority": {
            "direction_id": None,
            "document_writer": "Root",
            "git_actor": None,
            "worktree_kind": None,
            "assignment_authority": "SHARED",
        },
        "mutation": {
            "class": "STATE_PATH",
            "resources": [{"kind": "STATE_PATH", "key": str(state_path)}],
        },
        "effect": {
            "attempt": 1,
            "attempt_token": hashlib.sha256(operation_id.encode()).hexdigest(),
            "authorized_effects": ["STATE_CAS"],
            "unknown_outcome": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "target": {
            "state_kind": state_kind,
            "canonical_target_path": str(state_path),
            "expected_revision": 1,
            "input_ref": content_ref(repo, input_path),
            "expected_document_writer": "Root",
        },
        "acceptance_refs": [content_ref(repo, input_path)],
        "postconditions": {
            "success": ["exact replacement observed"],
            "refusal": ["target unchanged"],
            "unknown": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "stop_condition": "Return one terminal fact.",
        "return_owner": "ROOT",
    }
    packet["packet_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    return packet, state_path, input_path


def write_packet(repo: Path, packet: dict[str, Any]) -> Path:
    path = repo / "packets" / f"{packet['operation_id']}.json"
    write_json(path, packet)
    return path


def producer_evidence(dependency: dict[str, Any]) -> dict[str, Any]:
    return {
        "producer": copy.deepcopy(dependency["producer"]),
        "result_sha256": dependency["result_sha256"],
        "status": dependency["required_status"],
        "payload_kind": dependency["required_payload_kind"],
        "refs": copy.deepcopy(dependency["required_refs"]),
    }


def bind_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    repo: Path,
    path: Path,
    packet: dict[str, Any],
    *,
    accepted_producers: list[dict[str, Any]] | None = None,
) -> None:
    dispatch = {
        "packet_ref": content_ref(repo, path),
        "accepted_authorizer_result": {
            "logical_identity": packet["authorizer"]["logical_identity"],
            "generation": packet["authorizer"]["generation"],
            "assignment_id": packet["authorizer"]["assignment_id"],
            "result_sha256": hashlib.sha256(b"accepted-authorizer").hexdigest(),
        },
        "accepted_producer_results": (
            accepted_producers
            if accepted_producers is not None
            else [
                producer_evidence(dependency)
                for dependency in packet["requires"]
                if "producer" in dependency
            ]
        ),
    }
    monkeypatch.setenv(clerk.DISPATCH_ENV, json.dumps(dispatch, sort_keys=True))


def invoke(path: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    code = clerk.main(["execute", "--packet", str(path)])
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


def raw_receipt(repo: Path, result: dict[str, Any]) -> dict[str, Any]:
    ref = result["payload"]["receipt_refs"][0]
    path = repo / ref["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"]
    return json.loads(path.read_text(encoding="utf-8"))


def test_direct_output_is_common_v2_and_raw_receipt_is_referenced(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    packet, state_path, _ = state_packet(repo)
    path = write_packet(repo, packet)
    bind_dispatch(monkeypatch, repo, path, packet)

    def replace(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"revision": 2}

    monkeypatch.setattr(clerk.hmasd_state, "replace", replace)
    code, result = invoke(path, capsys)

    assert code == 0
    assert result["schema_version"] == 2
    assert result["role"] == "hmasd-clerk"
    assert result["logical_identity"] == "Clerk-state-cas-clerk"
    assert result["assignment_id"] == "state-cas-clerk"
    assert result["decision_requests"] == []
    assert result["next_actions"] == []
    assert result["payload"]["kind"] == "clerk"
    assert result["payload"]["resources"] == packet["mutation"]["resources"]
    receipt = raw_receipt(repo, result)
    assert receipt["outcome"] == "SUCCEEDED"
    assert receipt["effect_state"] == "LANDED"
    assert result["checkpoint_sha"] == result["payload"]["receipt_refs"][0]["sha256"]
    assert state_path.is_file()
    hmasd_state.validate_document("agent_result", result)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("producer", {"logical_identity": "Root", "generation": 2, "assignment_id": "other"}),
        ("result_sha256", "f" * 64),
        ("status", "FAILED"),
        ("payload_kind", "review"),
        ("refs", []),
    ],
)
def test_every_producer_evidence_mismatch_refuses_before_started(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    field: str,
    replacement: Any,
) -> None:
    evidence_path = repo / "evidence" / "producer.json"
    write_json(evidence_path, {"accepted": True})
    dependency = {
        "producer": {
            "logical_identity": "CM-example",
            "generation": 3,
            "assignment_id": "cm-example-three",
        },
        "result_sha256": hashlib.sha256(b"producer-result").hexdigest(),
        "required_status": "COMPLETED",
        "required_payload_kind": "cm",
        "required_refs": [content_ref(repo, evidence_path)],
    }
    packet, _state_path, _ = state_packet(
        repo,
        operation_id=f"producer-mismatch-{field}",
        requires=[dependency],
    )
    path = write_packet(repo, packet)
    accepted = producer_evidence(dependency)
    accepted[field] = replacement
    bind_dispatch(monkeypatch, repo, path, packet, accepted_producers=[accepted])
    called = False

    def forbidden_replace(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(clerk.hmasd_state, "replace", forbidden_replace)
    code, result = invoke(path, capsys)

    assert code == 2
    assert called is False
    receipt = raw_receipt(repo, result)
    assert receipt["reason"]["code"] == "PRODUCER_EVIDENCE_MISMATCH"
    claim_path, _ = clerk._claim_paths(repo, packet["operation_id"])
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim["state"] == "REFUSED"


@pytest.mark.parametrize(
    "state_kind",
    ["runtime_worktrees", "runtime_browser_assignments", "external_review_index"],
)
def test_generic_state_cas_excludes_discriminated_ledgers(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state_kind: str,
) -> None:
    packet, state_path, _ = state_packet(
        repo, operation_id=f"forbidden-{state_kind}", state_kind=state_kind
    )
    path = write_packet(repo, packet)
    bind_dispatch(monkeypatch, repo, path, packet)
    before = state_path.read_bytes()
    code, result = invoke(path, capsys)
    assert code == 2
    assert result["payload"]["outcome"] == "REFUSED"
    assert result["payload"]["receipt_refs"] == []
    assert state_path.read_bytes() == before


def test_self_authored_model_environment_is_not_proof_or_input(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    packet, _state_path, _ = state_packet(repo, operation_id="forged-model-env")
    path = write_packet(repo, packet)
    bind_dispatch(monkeypatch, repo, path, packet)
    monkeypatch.setenv(
        "HMASD_CLERK_EXECUTOR_ATTESTATION",
        json.dumps({"resolved_model": "forged", "resolved_model_is_fallback": False}),
    )
    monkeypatch.setattr(clerk.hmasd_state, "replace", lambda *_args, **_kwargs: {"revision": 2})
    code, result = invoke(path, capsys)
    assert code == 0
    receipt = raw_receipt(repo, result)
    assert "resolved_model" not in receipt
    assert "thinking_level" not in receipt
    assert "resolved_model_is_fallback" not in receipt


def test_provision_result_validation_uses_only_provision_fields(
    tmp_path: Path,
) -> None:
    target = {
        "worktree_ref": "wt-example-direction-research-example-assignment",
        "canonical_worktree_path": str(tmp_path / "worktree"),
        "integration_policy": "EXACT_HANDOFF",
        "required_handoff_sha": "b" * 40,
        "required_dependency_refs": [],
        "direction_id": "example-direction",
        "worktree_kind": "research",
        "base_sha": "c" * 40,
    }
    packet = {"operation": "WORKTREE_PROVISION", "target": target}
    result = {
        "operation": "provision",
        "worktree": {
            "worktree_ref": target["worktree_ref"],
            "canonical_absolute_path": target["canonical_worktree_path"],
            "integration_policy": target["integration_policy"],
            "required_handoff_sha": target["required_handoff_sha"],
            "required_dependency_refs": [],
            "direction_id": target["direction_id"],
            "kind": target["worktree_kind"],
            "base_sha": target["base_sha"],
            "lifecycle": "PROVISIONED",
        },
    }

    clerk._validate_primitive_result(packet, tmp_path, result)


def test_mutation_resource_array_must_be_complete_and_canonical(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    packet, state_path, _ = state_packet(repo, operation_id="wrong-resources")
    packet["mutation"]["resources"] = [
        {"kind": "STATE_PATH", "key": str(repo / "wrong.json")}
    ]
    packet["packet_sha256"] = hashlib.sha256(
        canonical({key: value for key, value in packet.items() if key != "packet_sha256"})
    ).hexdigest()
    path = write_packet(repo, packet)
    bind_dispatch(monkeypatch, repo, path, packet)
    before = state_path.read_bytes()
    code, result = invoke(path, capsys)
    assert code == 2
    assert "resource" in result["summary"].lower()
    assert state_path.read_bytes() == before


def test_orphan_started_observes_state_once_then_reuses_terminal_receipt(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    packet, state_path, _ = state_packet(repo, operation_id="orphan-state-cas")
    path = write_packet(repo, packet)
    bind_dispatch(monkeypatch, repo, path, packet)
    claim_path, _ = clerk._claim_paths(repo, packet["operation_id"])
    clerk._write_claim(
        claim_path,
        {
            "schema": clerk.CLAIM_SCHEMA,
            "operation_id": packet["operation_id"],
            "packet_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "state": "STARTED",
            "attempt": 1,
            "receipt_ref": None,
        },
        create=True,
    )
    first_code, first = invoke(path, capsys)
    second_code, second = invoke(path, capsys)
    assert first_code == second_code == 6
    assert first == second
    receipt = raw_receipt(repo, first)
    assert receipt["reason"]["code"] == "ORPHAN_STARTED"
    assert receipt["observation_refs"] == [
        {
            "operation": "STATE_CAS",
            "observation_count": 1,
            "state": {
                "path": state_path.relative_to(repo).as_posix(),
                "sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
                "revision": 1,
            },
        }
    ]


def test_helper_unknown_preserves_validated_phase_remote_local_and_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def helper(_argv: Any) -> int:
        print(
            json.dumps(
                {
                    "ok": False,
                    "operation": "integrate-push",
                    "integration_policy": "EXACT_HANDOFF",
                    "integration_phase": "REMOTE_PUSH_UNKNOWN",
                    "expected_target_predecessor_sha": GIT_SHA,
                    "remote_post_observation_sha": None,
                    "local_sha": GIT_SHA,
                    "reconciliation_observations": 1,
                }
            )
        )
        return 1

    monkeypatch.setattr(clerk.hmasd_worktree, "main", helper)
    with pytest.raises(clerk.ClerkUnknown) as caught:
        clerk._invoke_worktree(["integrate-push"])
    assert caught.value.observations == [
        {
            "helper_code": 1,
            "operation": "integrate-push",
            "integration_policy": "EXACT_HANDOFF",
            "integration_phase": "REMOTE_PUSH_UNKNOWN",
            "expected_target_predecessor_sha": GIT_SHA,
            "remote_post_observation_sha": None,
            "local_sha": GIT_SHA,
            "reconciliation_observations": 1,
        }
    ]


@pytest.mark.parametrize(
    "operation",
    [
        "PATCH_APPLY",
        "CANDIDATE_CREATE",
        "GIT_RECORD",
        "GIT_PREPARE",
        "GIT_INTEGRATE_PUSH",
    ],
)
def test_registered_worktree_authority_requires_exact_direction_kind_and_actor(
    operation: str,
) -> None:
    entry = {"direction_id": "bar", "kind": "engineering"}
    packet = {
        "operation": operation,
        "authorizer": {
            "role": "hmasd-cm",
            "logical_identity": "CM-bar",
            "generation": 1,
            "assignment_id": "cm-bar-one",
        },
        "authority": {
            "direction_id": "bar",
            "worktree_kind": "engineering",
            "git_actor": "cm:bar",
            "document_writer": None,
            "assignment_authority": "DIRECTION",
        },
    }
    clerk._validate_registered_authority(packet, entry)
    for field, wrong in (
        ("direction_id", "foo"),
        ("worktree_kind", "research"),
        ("git_actor", "cm:foo"),
        ("assignment_authority", "SHARED"),
    ):
        tampered = copy.deepcopy(packet)
        tampered["authority"][field] = wrong
        with pytest.raises(clerk.ClerkRefusal):
            clerk._validate_registered_authority(tampered, entry)
    root = copy.deepcopy(packet)
    root["authorizer"] = {
        "role": "root",
        "logical_identity": "Root",
        "generation": 1,
        "assignment_id": "root-recovery",
    }
    root["authority"]["git_actor"] = "root"
    root["authority"]["assignment_authority"] = "RECOVERY"
    clerk._validate_registered_authority(root, entry)


def test_release_result_lifecycle_matches_explicit_disposition(repo: Path) -> None:
    target = {
        "worktree_ref": "wt-bar-engineering-assignment-one",
        "canonical_worktree_path": str(repo / "worktree"),
        "policy": "EXACT_HANDOFF",
        "required_handoff_sha": GIT_SHA,
        "required_dependency_refs": [],
        "direction_id": "bar",
        "worktree_kind": "engineering",
        "base_sha": GIT_SHA,
        "expected_lifecycle": "PROVISIONED",
        "ignored_artifacts": "retain",
    }
    packet = {"operation": "WORKTREE_RELEASE", "target": target}
    worktree_fact = {
        "worktree_ref": target["worktree_ref"],
        "canonical_absolute_path": target["canonical_worktree_path"],
        "integration_policy": "EXACT_HANDOFF",
        "required_handoff_sha": GIT_SHA,
        "required_dependency_refs": [],
        "direction_id": "bar",
        "kind": "engineering",
        "base_sha": GIT_SHA,
        "lifecycle": "RETAINED_FOR_RECOVERY",
    }
    clerk._validate_primitive_result(
        packet,
        repo,
        {
            "operation": "release",
            "status": "RETAINED_FOR_RECOVERY",
            "worktree": worktree_fact,
        },
    )
    packet["target"]["ignored_artifacts"] = "discard"
    with pytest.raises(clerk.ClerkUnknown):
        clerk._validate_primitive_result(
            packet,
            repo,
            {
                "operation": "release",
                "status": "RETAINED_FOR_RECOVERY",
                "worktree": worktree_fact,
            },
        )


def test_build_derives_state_packet_mechanics_and_is_idempotent(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    full_packet, state_path, _input_path = state_packet(repo)
    draft = {
        key: copy.deepcopy(full_packet[key])
        for key in (
            "operation_id",
            "clerk_assignment_id",
            "authorizer",
            "authority",
            "operation",
            "requires",
            "target",
            "acceptance_refs",
        )
    }
    draft_path = repo / "packets" / "draft.json"
    output_path = repo / "packets" / "built.json"
    write_json(draft_path, draft)
    state_before = state_path.read_bytes()

    code = clerk.main(
        [
            "build",
            "--repo",
            str(repo),
            "--draft",
            str(draft_path),
            "--output",
            "packets/built.json",
        ]
    )
    first = json.loads(capsys.readouterr().out)
    assert code == 0
    assert first["ok"] is True
    assert first["created"] is True
    assert state_path.read_bytes() == state_before

    packet = json.loads(output_path.read_text(encoding="utf-8"))
    assert packet["mutation"] == {
        "class": "STATE_PATH",
        "resources": [{"kind": "STATE_PATH", "key": str(state_path)}],
    }
    assert packet["effect"]["authorized_effects"] == ["STATE_CAS"]
    assert packet["executor"]["logical_identity"] == "Clerk-state-cas-clerk"
    unsigned = dict(packet)
    packet_sha256 = unsigned.pop("packet_sha256")
    assert packet_sha256 == hashlib.sha256(canonical(unsigned)).hexdigest()
    hmasd_state.validate_document("clerk_operation", packet)

    code = clerk.main(
        [
            "build",
            "--repo",
            str(repo),
            "--draft",
            str(draft_path),
            "--output",
            str(output_path),
        ]
    )
    second = json.loads(capsys.readouterr().out)
    assert code == 0
    assert second["created"] is False
    assert state_path.read_bytes() == state_before


def test_build_rejects_invalid_operation_id_without_writing_packet(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    full_packet, _state_path, _input_path = state_packet(repo)
    draft = {
        key: copy.deepcopy(full_packet[key])
        for key in (
            "operation_id",
            "clerk_assignment_id",
            "authorizer",
            "authority",
            "operation",
            "requires",
            "target",
            "acceptance_refs",
        )
    }
    draft["operation_id"] = "invalid:timestamp"
    draft_path = repo / "packets" / "invalid-draft.json"
    output_path = repo / "packets" / "must-not-exist.json"
    write_json(draft_path, draft)

    code = clerk.main(
        [
            "build",
            "--repo",
            str(repo),
            "--draft",
            str(draft_path),
            "--output",
            str(output_path),
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result == {
        "ok": False,
        "operation": "build",
        "error": {
            "code": "INVALID_PACKET",
            "message": "operation_id is not a valid identifier",
        },
    }
    assert not output_path.exists()
