"""Return-witness and explicit cross-work comparison tests."""

from __future__ import annotations

import copy
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from scripts import hmasd_work_packet as packets


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _init_git_authority(repo: Path, relative: str) -> tuple[str, Path]:
    _git(repo, "init")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "HMASD tests")
    authority = repo / relative
    authority.parent.mkdir(parents=True, exist_ok=True)
    authority.write_text("# Existing authority\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Test repository\n", encoding="utf-8")
    _git(repo, "add", "AGENTS.md", relative)
    _git(repo, "commit", "-m", "track authority")
    return _git(repo, "rev-parse", "HEAD"), authority


def _init_git_authorities(repo: Path, relatives: list[str]) -> tuple[str, list[Path]]:
    _git(repo, "init")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "HMASD tests")
    paths: list[Path] = []
    for relative in relatives:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Existing authority\n", encoding="utf-8")
        paths.append(path)
    (repo / "AGENTS.md").write_text("# Test repository\n", encoding="utf-8")
    _git(repo, "add", "AGENTS.md", *relatives)
    _git(repo, "commit", "-m", "track authorities")
    return _git(repo, "rev-parse", "HEAD"), paths


def _packet_input(repo: Path, direction: str = "alpha") -> dict[str, Any]:
    root = repo / "docs" / "research" / "candidates" / direction
    _write_json(root / "STATE.json", {"revision": 7, "direction": direction})
    return {
        "schema_version": 1,
        "scope_ref": {
            "path": f"docs/research/candidates/{direction}/STATE.json",
            "revision": 7,
        },
        "sender_identity": "Portfolio",
        "target_identity": f"EM-{direction}",
        "authority_refs": [],
        "objective": "complete one bounded slice",
        "non_goals": ["do not infer natural-language completion"],
        "owned_paths": [f"experiments/candidates/{direction}"],
        "done_criteria": ["return one typed envelope"],
        "effect_refs": [],
    }


def _setup(repo: Path, direction: str = "alpha") -> tuple[dict[str, Any], list[dict[str, Any]]]:
    packet = packets.build_packet(_packet_input(repo, direction), repo=repo)
    packets.publish_packet(packet, repo=repo)
    observed = [
        {
            "logical_identity": f"EM-{direction}",
            "kind": "em",
            "direction_id": direction,
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": f"thread-{direction}",
        }
    ]
    return packet, observed


def _result(packet: dict[str, Any], direction: str = "alpha") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": f"EM-{direction}",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Produced the typed result envelope.",
        "changed_paths": [f"experiments/candidates/{direction}/result.json"],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "em",
            "direction_id": direction,
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [],
            "engineering_request_ref": None,
        },
    }


def _legacy_recovery_result(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "hmasd-workflow-recovery-manager",
        "logical_identity": "hmasd-workflow-recovery-manager",
        "generation": 1,
        "assignment_id": packet["work_id"],
        "status": "COMPLETED",
        "materiality": "LOCAL",
        "summary": "Recorded one historical recovery observation.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "recovery",
            "failure_class": "terminal_without_return",
            "observed_refs": [],
            "attempts": [],
            "outcome": "resume_same_identity",
            "resume_condition": None,
        },
    }


def test_retired_recovery_role_rejects_new_return_and_reconstructs_legacy_witness(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    source["sender_identity"] = "Root"
    source["target_identity"] = "hmasd-workflow-recovery-manager"
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "hmasd-workflow-recovery-manager",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-legacy-recovery",
        }
    ]
    result = _legacy_recovery_result(packet)

    rejected = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=result,
    )["plan"]
    assert rejected["verb"] == "CONFLICT"
    assert rejected["defect"]["code"] == "RETIRED_RUNTIME_ROLE"
    assert rejected["defect"]["field_path"] == "logical_identity"
    with pytest.raises(packets.InvalidPacket, match="RETIRED_RUNTIME_ROLE"):
        packets.publish_return(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=observed,
            agent_result=result,
        )

    witness = {
        "schema_version": 1,
        "work_id": packet["work_id"],
        "receiver": {
            "logical_identity": "hmasd-workflow-recovery-manager",
            "generation": 1,
        },
        "agent_result": result,
    }
    locator = (
        tmp_path
        / ".codex/runtime/work/returns"
        / packet["work_id"]
        / "return.json"
    )
    locator.parent.mkdir(parents=True)
    locator.write_bytes(packets.hmasd_state.canonical_bytes(witness))

    reconstructed = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=[],
    )["plan"]
    assert reconstructed["verb"] == "NOOP_TERMINAL"
    assert reconstructed["task_resolution"] == {
        "status": "RETURN_WITNESS",
        "logical_identity": "hmasd-workflow-recovery-manager",
        "generation": 1,
    }


def test_publish_return_is_one_immutable_entity_under_concurrency(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)

    def publish(_: int) -> dict[str, Any]:
        return packets.publish_return(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=observed,
            agent_result=result,
        )

    with ThreadPoolExecutor(max_workers=10) as pool:
        outcomes = list(pool.map(publish, range(10)))

    locator = (
        tmp_path
        / ".codex/runtime/work/returns"
        / packet["work_id"]
        / "return.json"
    )
    assert locator.is_file()
    assert sum(item["published"] for item in outcomes) == 1
    assert {item["plan"]["verb"] for item in outcomes} == {"NOOP_TERMINAL"}
    assert list(locator.parent.iterdir()) == [locator]
    witness = json.loads(locator.read_text(encoding="utf-8"))
    assert witness == {
        "schema_version": 1,
        "work_id": packet["work_id"],
        "receiver": {"logical_identity": "EM-alpha", "generation": 1},
        "agent_result": result,
    }


def test_publish_return_rejects_different_bytes_for_same_work_id(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=_result(packet),
    )
    changed = _result(packet)
    changed["summary"] = "A conflicting second return."

    with pytest.raises(packets.PacketConflict, match="conflicting return"):
        packets.publish_return(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=observed,
            agent_result=changed,
        )


def test_reconcile_reconstructs_return_without_live_task_and_never_dispatches(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=result,
    )

    first = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=[]
    )
    second = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=[]
    )

    assert first == second
    assert first["plan"]["verb"] == "NOOP_TERMINAL"
    assert first["plan"]["task_resolution"] == {
        "status": "RETURN_WITNESS",
        "logical_identity": "EM-alpha",
        "generation": 1,
    }


def test_reconcile_with_explicit_result_conflicts_with_existing_return(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=_result(packet),
    )
    changed = _result(packet)
    changed["summary"] = "Different explicit bytes."

    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=[],
        agent_result=changed,
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["conflict_type"] == "RETURN_CONFLICT"


def test_return_reconstruction_revalidates_fresh_result_refs(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    artifact = tmp_path / "experiments/candidates/alpha/evidence.json"
    _write_json(artifact, {"value": 1})
    result = _result(packet)
    result["artifact_refs"] = [
        {
            "path": "experiments/candidates/alpha/evidence.json",
            "sha256": packets.hmasd_state.sha256_bytes(artifact.read_bytes()),
        }
    ]
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=result,
    )
    _write_json(artifact, {"value": 2})

    plan = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=[]
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == "STALE_RESULT_REF"


def test_crash_before_return_still_resumes_but_after_return_reconstructs(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)

    before = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=observed
    )["plan"]
    assert before["verb"] == "DISPATCH_EXISTING"

    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=_result(packet),
    )
    after = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=[]
    )["plan"]
    assert after["verb"] == "NOOP_TERMINAL"


def test_resumable_result_cannot_be_frozen_as_return(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    result = _result(packet)
    result["status"] = "PARTIAL"
    result["next_action"] = {"kind": "RESUME_SAME_SLICE", "input_refs": []}

    with pytest.raises(packets.InvalidPacket, match="RESUME_SAME_SLICE"):
        packets.publish_return(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=observed,
            agent_result=result,
        )
    assert not (
        tmp_path / ".codex/runtime/work/returns" / packet["work_id"] / "return.json"
    ).exists()


def test_return_runtime_has_no_completion_ledger_or_lifecycle_files(tmp_path: Path) -> None:
    packet, observed = _setup(tmp_path)
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=observed,
        agent_result=_result(packet),
    )

    names = {path.name.lower() for path in (tmp_path / ".codex/runtime/work").rglob("*")}
    assert not names & {"queue.json", "ledger.json", "lease.json", "cursor.json", "status.json"}


def test_return_publish_observes_typed_unknown_effect_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _packet_input(tmp_path)
    source["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-unknown/manifest.json",
            "resource_id": "alpha/run-unknown",
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
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

    def observe(_: Path, reference: dict[str, Any]) -> Any:
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "UNKNOWN", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)

    with pytest.raises(packets.InvalidPacket, match="OBSERVE_EFFECT_ONLY"):
        packets.publish_return(
            repo=tmp_path,
            work_id=packet["work_id"],
            observed_tasks=observed,
            agent_result=_result(packet),
        )
    assert packets.read_return(repo=tmp_path, work_id=packet["work_id"]) is None


def _publish_with_paths(
    repo: Path,
    *,
    objective: str,
    owned_paths: list[str],
    authority_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _packet_input(repo)
    source["objective"] = objective
    source["owned_paths"] = owned_paths
    source["authority_refs"] = authority_refs or []
    packet = packets.build_packet(source, repo=repo)
    packets.publish_packet(packet, repo=repo)
    return packet


def test_compare_detects_segment_parent_child_but_not_string_prefix(tmp_path: Path) -> None:
    parent = _publish_with_paths(
        tmp_path,
        objective="parent",
        owned_paths=["experiments/candidates/alpha"],
    )
    child = _publish_with_paths(
        tmp_path,
        objective="child",
        owned_paths=["experiments/candidates/alpha/variant"],
    )
    prefix_only = _publish_with_paths(
        tmp_path,
        objective="prefix only",
        owned_paths=["experiments/candidates/alphabet"],
    )

    overlap = packets.compare_work_ids(
        tmp_path, [child["work_id"], parent["work_id"]]
    )
    disjoint = packets.compare_work_ids(
        tmp_path, [parent["work_id"], prefix_only["work_id"]]
    )

    assert overlap["outcome"] == "CONFLICT"
    assert overlap["pairs"][0]["reasons"] == [
        {
            "type": "OWNED_PATH_OVERLAP",
            "left": "experiments/candidates/alpha/variant",
            "right": "experiments/candidates/alpha",
        }
    ]
    assert disjoint["outcome"] == "DISJOINT"
    assert disjoint["pairs"][0]["reasons"] == []


def test_compare_conflicts_on_same_authority_path_with_different_binding(tmp_path: Path) -> None:
    authority_path = tmp_path / "docs/research/candidates/alpha/SHARED.json"
    _write_json(authority_path, {"revision": 1})
    first = _publish_with_paths(
        tmp_path,
        objective="first authority view",
        owned_paths=["experiments/candidates/alpha/a"],
        authority_refs=[
            {
                "path": "docs/research/candidates/alpha/SHARED.json",
                "revision": 1,
            }
        ],
    )
    second = _publish_with_paths(
        tmp_path,
        objective="second authority view",
        owned_paths=["experiments/candidates/alpha/b"],
        authority_refs=[
            {
                "path": "docs/research/candidates/alpha/SHARED.json",
                "revision": 2,
            }
        ],
    )

    result = packets.compare_work_ids(tmp_path, [first["work_id"], second["work_id"]])

    assert result["outcome"] == "CONFLICT"
    assert result["pairs"][0]["reasons"][0]["type"] == "AUTHORITY_BINDING_CONFLICT"
    assert result["pairs"][0]["reasons"][0]["path"] == (
        "docs/research/candidates/alpha/SHARED.json"
    )


def test_compare_detects_bidirectional_owned_path_to_read_ref_overlap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _publish_with_paths(
        tmp_path,
        objective="write the second packet scope",
        owned_paths=["docs/research/candidates/alpha/STATE.json"],
    )
    second_source = _packet_input(tmp_path)
    second_source["objective"] = "read scope and write effect locator"
    second_source["owned_paths"] = [
        "temp/directions/alpha/exp/run-one/manifest.json"
    ]
    second_source["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": "experiments/candidates/alpha/model.py",
            "resource_id": "alpha/run-one",
        }
    ]
    second = packets.build_packet(second_source, repo=tmp_path)
    packets.publish_packet(second, repo=tmp_path)
    third = _publish_with_paths(
        tmp_path,
        objective="write the second packet effect locator",
        owned_paths=["experiments/candidates/alpha/model.py/weights"],
    )

    monkeypatch.setattr(
        packets.hmasd_protocol_contracts,
        "observe_effect_ref",
        lambda _repo, ref: packets.hmasd_protocol_contracts.EffectObservation(
            ref["kind"], ref["resource_id"], "IN_PROGRESS", ref["path"]
        ),
    )

    scope_overlap = packets.compare_work_ids(
        tmp_path, [first["work_id"], second["work_id"]]
    )
    effect_overlap = packets.compare_work_ids(
        tmp_path, [second["work_id"], third["work_id"]]
    )

    assert scope_overlap["pairs"][0]["outcome"] == "CONFLICT"
    assert any(
        reason["type"] == "READ_WRITE_OVERLAP"
        and reason["write"] == "docs/research/candidates/alpha/STATE.json"
        and reason["read_field"] == "scope_ref"
        for reason in scope_overlap["pairs"][0]["reasons"]
    )
    assert effect_overlap["pairs"][0]["outcome"] == "CONFLICT"
    assert any(
        reason["type"] == "READ_WRITE_OVERLAP"
        and reason["write"] == "experiments/candidates/alpha/model.py/weights"
        and reason["read_field"] == "effect_refs[0]"
        for reason in effect_overlap["pairs"][0]["reasons"]
    )


def test_compare_uses_windows_casefold_for_paths_and_authority_aliases(
    tmp_path: Path,
) -> None:
    first = _publish_with_paths(
        tmp_path,
        objective="upper-case writer",
        owned_paths=["EXPERIMENTS/CANDIDATES/ALPHA/Model.py"],
        authority_refs=[
            {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            }
        ],
    )
    second = _publish_with_paths(
        tmp_path,
        objective="lower-case writer",
        owned_paths=["experiments/candidates/alpha/model.py"],
        authority_refs=[
            {
                "path": "DOCS/RESEARCH/CANDIDATES/ALPHA/state.JSON",
                "revision": 8,
            }
        ],
    )

    result = packets.compare_work_ids(tmp_path, [first["work_id"], second["work_id"]])

    assert result["pairs"][0]["outcome"] == "CONFLICT"
    assert {reason["type"] for reason in result["pairs"][0]["reasons"]} >= {
        "OWNED_PATH_OVERLAP",
        "AUTHORITY_BINDING_CONFLICT",
    }


def test_compare_is_exact_deterministic_and_does_not_enumerate_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packets_by_name = {
        name: _publish_with_paths(
            tmp_path,
            objective=name,
            owned_paths=[f"experiments/candidates/alpha/{name}"],
        )
        for name in ("a", "b", "c")
    }
    corrupt_sibling = (
        tmp_path / ".codex/runtime/work/ready" / ("f" * 64) / "packet.json"
    )
    corrupt_sibling.parent.mkdir(parents=True)
    corrupt_sibling.write_text('{"broken":', encoding="utf-8")

    def forbid_iterdir(_: Path) -> Any:
        raise AssertionError("compare must not enumerate ready siblings")

    monkeypatch.setattr(Path, "iterdir", forbid_iterdir)
    ids = [packets_by_name[name]["work_id"] for name in ("c", "a", "b")]
    first = packets.compare_work_ids(tmp_path, ids)
    second = packets.compare_work_ids(tmp_path, list(reversed(ids)))

    assert first == second
    assert first["work_ids"] == sorted(ids)
    assert first["outcome"] == "DISJOINT"
    assert [(pair["left_work_id"], pair["right_work_id"]) for pair in first["pairs"]] == [
        (left, right)
        for index, left in enumerate(sorted(ids))
        for right in sorted(ids)[index + 1 :]
    ]


def _publish_with_effect(
    repo: Path,
    *,
    objective: str,
    owned_path: str,
    effect_ref: dict[str, Any],
) -> dict[str, Any]:
    source = _packet_input(repo)
    source["objective"] = objective
    source["owned_paths"] = [owned_path]
    source["effect_refs"] = [effect_ref]
    packet = packets.build_packet(source, repo=repo)
    packets.publish_packet(packet, repo=repo)
    return packet


def test_compare_uses_typed_effect_resource_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def observe(_: Path, reference: dict[str, Any]) -> Any:
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "IN_PROGRESS", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    first = _publish_with_effect(
        tmp_path,
        objective="effect a",
        owned_path="experiments/candidates/alpha/a",
        effect_ref={
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-one/manifest.json",
            "resource_id": "alpha/run-one",
        },
    )
    same = _publish_with_effect(
        tmp_path,
        objective="same effect another locator",
        owned_path="experiments/candidates/alpha/b",
        effect_ref={
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-one/copy.json",
            "resource_id": "alpha/run-one",
        },
    )
    different = _publish_with_effect(
        tmp_path,
        objective="different effect",
        owned_path="experiments/candidates/alpha/c",
        effect_ref={
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-two/manifest.json",
            "resource_id": "alpha/run-two",
        },
    )

    conflict = packets.compare_work_ids(tmp_path, [first["work_id"], same["work_id"]])
    disjoint = packets.compare_work_ids(
        tmp_path, [first["work_id"], different["work_id"]]
    )

    assert conflict["outcome"] == "CONFLICT"
    assert conflict["pairs"][0]["reasons"] == [
        {
            "type": "EFFECT_RESOURCE_OVERLAP",
            "kind": "run_manifest",
            "resource_id": "alpha/run-one",
        }
    ]
    assert disjoint["outcome"] == "DISJOINT"


def test_compare_marks_legacy_or_unknown_effects_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def observe(_: Path, reference: dict[str, Any]) -> Any:
        if set(reference) == {"path"}:
            return packets.hmasd_protocol_contracts.EffectObservation(
                "legacy", "", "LEGACY_UNTYPED", reference["path"]
            )
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "UNKNOWN", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    legacy = _publish_with_effect(
        tmp_path,
        objective="legacy effect",
        owned_path="experiments/candidates/alpha/a",
        effect_ref={"path": "temp/directions/alpha/exp/legacy/effect.json"},
    )
    unknown = _publish_with_effect(
        tmp_path,
        objective="unknown effect",
        owned_path="experiments/candidates/alpha/b",
        effect_ref={
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-unknown/manifest.json",
            "resource_id": "alpha/run-unknown",
        },
    )

    result = packets.compare_work_ids(tmp_path, [unknown["work_id"], legacy["work_id"]])

    assert result["outcome"] == "UNKNOWN"
    assert result["pairs"][0]["outcome"] == "UNKNOWN"
    assert {reason["type"] for reason in result["pairs"][0]["reasons"]} == {
        "EFFECT_STATE_UNKNOWN",
        "EFFECT_UNTYPED",
    }


def test_three_way_compare_observes_each_explicit_effect_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def observe(_: Path, reference: dict[str, Any]) -> Any:
        calls.append(reference["resource_id"])
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "IN_PROGRESS", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    work = [
        _publish_with_effect(
            tmp_path,
            objective=f"effect {index}",
            owned_path=f"experiments/candidates/alpha/{index}",
            effect_ref={
                "kind": "run_manifest",
                "path": f"temp/directions/alpha/exp/run-{index}/manifest.json",
                "resource_id": f"alpha/run-{index}",
            },
        )
        for index in range(3)
    ]

    result = packets.compare_work_ids(tmp_path, [packet["work_id"] for packet in work])

    assert result["outcome"] == "DISJOINT"
    assert sorted(calls) == ["alpha/run-0", "alpha/run-1", "alpha/run-2"]


def test_return_publish_and_read_cli_emit_locator_and_reconstructed_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet, observed = _setup(tmp_path)
    observed_path = tmp_path / "observed.json"
    result_path = tmp_path / "result.json"
    _write_json(observed_path, {"tasks": observed})
    _write_json(result_path, _result(packet))

    code = packets.main(
        [
            "return-publish",
            "--repo",
            str(tmp_path),
            "--work-id",
            packet["work_id"],
            "--observed-tasks",
            str(observed_path),
            "--agent-result",
            str(result_path),
        ]
    )
    published = json.loads(capsys.readouterr().out)
    assert code == 0
    assert published["operation"] == "return-publish"
    assert published["plan"]["verb"] == "NOOP_TERMINAL"
    assert Path(published["path"]).is_file()

    code = packets.main(
        [
            "return-read",
            "--repo",
            str(tmp_path),
            "--work-id",
            packet["work_id"],
        ]
    )
    read = json.loads(capsys.readouterr().out)
    assert code == 0
    assert read["operation"] == "return-read"
    assert read["witness"]["work_id"] == packet["work_id"]
    assert read["plan"]["verb"] == "NOOP_TERMINAL"


def test_compare_cli_requires_repeated_explicit_work_ids(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = _publish_with_paths(
        tmp_path,
        objective="first cli packet",
        owned_paths=["experiments/candidates/alpha/a"],
    )
    second = _publish_with_paths(
        tmp_path,
        objective="second cli packet",
        owned_paths=["experiments/candidates/alpha/b"],
    )

    code = packets.main(
        [
            "compare",
            "--repo",
            str(tmp_path),
            "--work-id",
            second["work_id"],
            "--work-id",
            first["work_id"],
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert code == 0
    assert result["operation"] == "compare"
    assert result["work_ids"] == sorted([first["work_id"], second["work_id"]])


def test_legacy_unknown_json_is_untyped_conflict_not_a_typed_observation(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    effect_path = "temp/directions/alpha/exp/legacy/effect.json"
    _write_json(tmp_path / effect_path, {"status": "UNKNOWN"})
    source["effect_refs"] = [{"path": effect_path}]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=_setup(tmp_path)[1],
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["conflict_type"] == "PROTOCOL_DEFECT"
    assert plan["defect"]["code"] == "UNTYPED_EFFECT_REF"
    assert plan["defect"]["field_path"] == "effect_refs[0]"


def test_invalid_typed_effect_is_precise_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _packet_input(tmp_path)
    source["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-bad/manifest.json",
            "resource_id": "alpha/run-bad",
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    def reject(_: Path, __: dict[str, Any]) -> Any:
        raise packets.hmasd_protocol_contracts.ProtocolContractError(
            "INVALID_EFFECT_DOCUMENT", "bad manifest"
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", reject)
    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=_setup(tmp_path)[1],
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == "INVALID_EFFECT_DOCUMENT"
    assert plan["defect"]["failure_scope"] == "effect"
    assert plan["defect"]["ref"] == source["effect_refs"][0]


def test_compare_reports_stale_packet_instead_of_disjoint(tmp_path: Path) -> None:
    first = _publish_with_paths(
        tmp_path,
        objective="stale compare packet",
        owned_paths=["experiments/candidates/alpha/a"],
    )
    second = _publish_with_paths(
        tmp_path,
        objective="fresh compare packet",
        owned_paths=["experiments/candidates/alpha/b"],
    )
    _write_json(
        tmp_path / first["scope_ref"]["path"],
        {"revision": 8, "direction": "alpha"},
    )

    result = packets.compare_work_ids(tmp_path, [first["work_id"], second["work_id"]])

    assert result["outcome"] == "CONFLICT"
    assert result["packet_conflicts"] == [
        {
            "work_id": work_id,
            "code": "STALE_AUTHORITY",
            "field_path": "scope_ref",
        }
        for work_id in sorted([first["work_id"], second["work_id"]])
    ]


def _cm_shared_packet_source(repo: Path) -> dict[str, Any]:
    source = _packet_input(repo)
    source["target_identity"] = "CM-alpha"
    source["owned_paths"] = ["scripts/shared_algorithm.py"]
    source["objective"] = "Modify the exact shared algorithm path."
    source["non_goals"] = ["Do not change RNG semantics"]
    return source


def _observed_cm() -> list[dict[str, Any]]:
    return [
        {
            "logical_identity": "CM-alpha",
            "kind": "cm",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-cm-alpha",
        }
    ]


@pytest.mark.parametrize(
    ("target_identity", "observed"),
    [
        (
            "EM-alpha",
            [
                {
                    "logical_identity": "EM-alpha",
                    "kind": "em",
                    "direction_id": "alpha",
                    "generation": 1,
                    "lifecycle": "RUNNING",
                    "thread_id": "thread-em-alpha",
                }
            ],
        ),
        (
            "Portfolio",
            [
                {
                    "logical_identity": "Portfolio",
                    "kind": "portfolio",
                    "generation": 1,
                    "lifecycle": "RUNNING",
                    "thread_id": "thread-portfolio",
                }
            ],
        ),
        (
            "Artifact-Writer-alpha",
            [
                {
                    "logical_identity": "Artifact-Writer-alpha",
                    "kind": "artifact-writer",
                    "generation": 1,
                    "lifecycle": "RUNNING",
                    "thread_id": "thread-writer-alpha",
                }
            ],
        ),
        (
            "CM/alpha/g1",
            [
                {
                    "logical_identity": "CM-alpha",
                    "kind": "cm",
                    "direction_id": "alpha",
                    "generation": 1,
                    "lifecycle": "RUNNING",
                    "thread_id": "thread-cm-alpha",
                }
            ],
        ),
    ],
)
def test_shared_core_path_rejects_every_non_root_noncanonical_cm_target(
    tmp_path: Path,
    target_identity: str,
    observed: list[dict[str, Any]],
) -> None:
    source = _packet_input(tmp_path)
    source["target_identity"] = target_identity
    source["owned_paths"] = ["scripts/shared_algorithm.py"]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    plan = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=observed
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["conflict_type"] == "PROTOCOL_DEFECT"
    assert plan["defect"]["code"] == "SHARED_CORE_TARGET_FORBIDDEN"
    assert plan["defect"]["field_path"] == "target_identity"


def test_shared_core_record_requires_allowed_existing_authority_root_and_base_tracking(
    tmp_path: Path,
) -> None:
    base_sha, authority = _init_git_authority(
        tmp_path, "docs/research/candidates/alpha/DIRECTION.md"
    )
    source = _cm_shared_packet_source(tmp_path)
    record = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS"],
    )
    fence = packets.hmasd_protocol_contracts.render_shared_core_action_record(record)

    scratch = tmp_path / "notes/scratch.md"
    scratch.parent.mkdir(parents=True)
    scratch.write_text(fence, encoding="utf-8")
    source["authority_refs"] = [
        {
            "path": "notes/scratch.md",
            "sha256": packets.hmasd_state.sha256_bytes(scratch.read_bytes()),
        }
    ]
    outside = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(outside, repo=tmp_path)
    outside_plan = packets.reconcile_once(
        repo=tmp_path, work_id=outside["work_id"], observed_tasks=_observed_cm()
    )["plan"]
    assert outside_plan["defect"]["code"] == "SHARED_CORE_AUTHORITY_PATH_FORBIDDEN"

    untracked = tmp_path / "docs/project/WORKFLOW_PROTOCOL.md"
    untracked.parent.mkdir(parents=True)
    untracked.write_text(fence, encoding="utf-8")
    source["authority_refs"] = [
        {
            "path": "docs/project/WORKFLOW_PROTOCOL.md",
            "sha256": packets.hmasd_state.sha256_bytes(untracked.read_bytes()),
        }
    ]
    untracked_packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(untracked_packet, repo=tmp_path)
    untracked_plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=untracked_packet["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert untracked_plan["defect"]["code"] == "SHARED_CORE_AUTHORITY_NOT_TRACKED_AT_BASE"

    authority.write_text("# Existing authority\n\n" + fence, encoding="utf-8")
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
        }
    ]
    accepted = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(accepted, repo=tmp_path)
    accepted_plan = packets.reconcile_once(
        repo=tmp_path, work_id=accepted["work_id"], observed_tasks=_observed_cm()
    )["plan"]
    assert accepted_plan["verb"] == "DISPATCH_EXISTING"


def test_shared_core_fence_uses_only_exact_v1_authority_allowlist(
    tmp_path: Path,
) -> None:
    relatives = [
        "docs/project/WORKFLOW_PROTOCOL.md",
        "docs/project/WORKFLOW_DESIGN_PHILOSOPHY.md",
        "docs/research/candidates/beta/DIRECTION.md",
    ]
    base_sha, authority_paths = _init_git_authorities(tmp_path, relatives)
    source = _cm_shared_packet_source(tmp_path)
    record = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS"],
    )
    fence = packets.hmasd_protocol_contracts.render_shared_core_action_record(record)

    for authority in authority_paths:
        authority.write_text("# Existing authority\n\n" + fence, encoding="utf-8")

    for relative, authority in zip(relatives[1:], authority_paths[1:], strict=True):
        source["authority_refs"] = [
            {
                "path": relative,
                "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
            }
        ]
        packet = packets.build_packet(source, repo=tmp_path)
        packets.publish_packet(packet, repo=tmp_path)
        plan = packets.reconcile_once(
            repo=tmp_path, work_id=packet["work_id"], observed_tasks=_observed_cm()
        )["plan"]
        assert plan["verb"] == "CONFLICT"
        assert plan["defect"]["code"] == "SHARED_CORE_AUTHORITY_PATH_FORBIDDEN"

    protocol = authority_paths[0]
    source["authority_refs"] = [
        {
            "path": relatives[0],
            "sha256": packets.hmasd_state.sha256_bytes(protocol.read_bytes()),
        }
    ]
    allowed = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(allowed, repo=tmp_path)
    allowed_plan = packets.reconcile_once(
        repo=tmp_path, work_id=allowed["work_id"], observed_tasks=_observed_cm()
    )["plan"]
    assert allowed_plan["verb"] == "DISPATCH_EXISTING"


def test_shared_core_parser_rehashes_the_same_frozen_bytes_after_prior_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha, authority = _init_git_authority(
        tmp_path, "docs/research/candidates/alpha/DIRECTION.md"
    )
    source = _cm_shared_packet_source(tmp_path)
    record = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS"],
    )
    raw = (
        "# Existing authority\n\n"
        + packets.hmasd_protocol_contracts.render_shared_core_action_record(record)
    ).encode()
    authority.write_bytes(raw)
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(raw),
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    original = packets._authority_matches
    replaced = False

    def validate_then_replace(
        repo: Path, reference: dict[str, Any], *, label: str
    ) -> None:
        nonlocal replaced
        original(repo, reference, label=label)
        if label == "authority_refs[0]" and not replaced:
            replaced = True
            authority.write_bytes(raw + b"\nreplacement bytes\n")

    monkeypatch.setattr(packets, "_authority_matches", validate_then_replace)

    plan = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=_observed_cm()
    )["plan"]

    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == "SHARED_CORE_AUTHORITY_STALE"


def test_cm_shared_core_requires_one_exact_fresh_root_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha = "1" * 40
    monkeypatch.setattr(packets, "_current_git_head", lambda _: base_sha, raising=False)
    monkeypatch.setattr(
        packets.hmasd_worktree,
        "path_is_tracked_at_commit",
        lambda _repo, _commit, _path: True,
    )
    source = _cm_shared_packet_source(tmp_path)
    missing = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(missing, repo=tmp_path)

    missing_plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=missing["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert missing_plan["verb"] == "CONFLICT"
    assert missing_plan["defect"]["code"] == "SHARED_CORE_AUTHORITY_REQUIRED"

    record = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS"],
    )
    authority = tmp_path / "docs/research/candidates/alpha/DIRECTION.md"
    authority.parent.mkdir(parents=True, exist_ok=True)
    authority.write_text(
        "# Direction authority\n\n"
        + packets.hmasd_protocol_contracts.render_shared_core_action_record(record)
        + "\n",
        encoding="utf-8",
    )
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
        }
    ]
    accepted = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(accepted, repo=tmp_path)

    accepted_plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=accepted["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert accepted_plan["verb"] == "DISPATCH_EXISTING"
    assert accepted_plan["shared_core_action_digest"] == record["action_digest"]


@pytest.mark.parametrize(
    "owned_path",
    [
        "docs/research/portfolio/PORTFOLIO.md",
        "docs/research/portfolio/workflow/registry.json",
    ],
)
def test_portfolio_exact_writer_authority_path_does_not_trigger_shared_core_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owned_path: str
) -> None:
    scope = "docs/research/portfolio/STATE.json"
    _write_json(tmp_path / scope, {"revision": 1})
    source = _packet_input(tmp_path)
    source.update(
        scope_ref={"path": scope, "revision": 1},
        target_identity="Portfolio",
        owned_paths=[owned_path],
        authority_refs=[],
    )
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    def forbid(_: Any) -> Any:
        raise AssertionError("Portfolio authority must not request shared-core confirmation")

    monkeypatch.setattr(
        packets.hmasd_protocol_contracts,
        "parse_shared_core_action_records",
        forbid,
    )
    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=[
            {
                "logical_identity": "Portfolio",
                "kind": "portfolio",
                "generation": 1,
                "lifecycle": "ACTIVE",
                "thread_id": "thread-portfolio",
            }
        ],
    )["plan"]
    assert plan["verb"] == "DISPATCH_EXISTING"


def test_return_reconstruction_rechecks_current_shared_core_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha = "1" * 40
    current = {"sha": base_sha}
    monkeypatch.setattr(
        packets, "_current_git_head", lambda _: current["sha"], raising=False
    )
    monkeypatch.setattr(
        packets.hmasd_worktree,
        "path_is_tracked_at_commit",
        lambda _repo, _commit, _path: True,
    )
    source = _cm_shared_packet_source(tmp_path)
    record = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS"],
    )
    authority = tmp_path / "docs/research/candidates/alpha/DIRECTION.md"
    authority.parent.mkdir(parents=True, exist_ok=True)
    authority.write_text(
        packets.hmasd_protocol_contracts.render_shared_core_action_record(record),
        encoding="utf-8",
    )
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    result = _result(packet)
    result["role"] = "hmasd-cm"
    result["logical_identity"] = "CM-alpha"
    result["changed_paths"] = ["scripts/shared_algorithm.py"]
    result["payload"] = {
        "kind": "cm",
        "direction_id": "alpha",
        "scope_ref": source["authority_refs"][0],
        "base_sha": base_sha,
        "candidate_sha": None,
        "verification_refs": [],
        "integrated_sha": None,
    }
    packets.publish_return(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=_observed_cm(),
        agent_result=result,
    )
    current["sha"] = "2" * 40

    plan = packets.reconcile_once(
        repo=tmp_path, work_id=packet["work_id"], observed_tasks=[]
    )["plan"]
    assert plan["verb"] == "CONFLICT"
    assert plan["defect"]["code"] == "SHARED_CORE_RECORD_NOT_FOUND"


def test_shared_core_record_cli_renders_only_without_writing_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    base_sha = "1" * 40
    monkeypatch.setattr(packets, "_current_git_head", lambda _: base_sha, raising=False)
    source = _cm_shared_packet_source(tmp_path)
    source["effect_refs"] = [
        {
            "kind": "run_manifest",
            "path": "temp/directions/alpha/exp/run-one/manifest.json",
            "resource_id": "alpha/run-one",
        },
        {
            "kind": "worktree",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        },
    ]
    packet_input = tmp_path / "packet-input.json"
    _write_json(packet_input, source)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    code = packets.main(
        [
            "shared-core-record",
            "--repo",
            str(tmp_path),
            "--packet",
            str(packet_input),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert code == 0
    assert output["operation"] == "shared-core-record"
    assert output["record"]["allowed_effects"] == [
        "MODIFY_PATHS",
        "OBSERVE_RUN_MANIFEST",
        "OBSERVE_WORKTREE",
    ]
    assert output["fence"].startswith("```hmasd-shared-core-action-v1\n")
    assert after == before


def test_effect_operation_is_closed_and_old_typed_work_id_is_unchanged(
    tmp_path: Path,
) -> None:
    old = _packet_input(tmp_path)
    old["effect_refs"] = [
        {
            "kind": "worktree",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        }
    ]
    assert packets.packet_id(old) == (
        "47f96fc58946fa2726a95d5a34d897822c0c0a0cacb457b935eeb5d190b147e4"
    )

    with_operation = copy.deepcopy(old)
    with_operation["effect_refs"][0]["operation"] = "APPLY_INTEGRATION"
    normalized = packets.build_packet(with_operation, repo=tmp_path)
    assert normalized["effect_refs"] == [
        {
            "kind": "worktree",
            "operation": "APPLY_INTEGRATION",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        }
    ]

    invalid = copy.deepcopy(old)
    invalid["effect_refs"] = [
        {
            "kind": "run_manifest",
            "operation": "PUSH",
            "path": "temp/directions/alpha/exp/run-one/manifest.json",
            "resource_id": "alpha/run-one",
        }
    ]
    with pytest.raises(packets.InvalidPacket, match="operation"):
        packets.build_packet(invalid, repo=tmp_path)


def test_operation_is_passed_to_read_only_observer_without_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _packet_input(tmp_path)
    source["effect_refs"] = [
        {
            "kind": "worktree",
            "operation": "APPLY_INTEGRATION",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed_refs: list[dict[str, Any]] = []

    def observe(_: Path, reference: dict[str, Any]) -> Any:
        observed_refs.append(dict(reference))
        return packets.hmasd_protocol_contracts.EffectObservation(
            "worktree", "alpha/assignment-one", "IN_PROGRESS", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=_setup(tmp_path)[1],
    )["plan"]

    assert plan["verb"] == "DISPATCH_EXISTING"
    assert observed_refs == [
        {
            "kind": "worktree",
            "operation": "APPLY_INTEGRATION",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        }
    ]


def test_comparator_resource_identity_ignores_effect_operation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def observe(_: Path, reference: dict[str, Any]) -> Any:
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "IN_PROGRESS", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    first = _publish_with_effect(
        tmp_path,
        objective="apply worktree",
        owned_path="experiments/candidates/alpha/a",
        effect_ref={
            "kind": "worktree",
            "operation": "APPLY_INTEGRATION",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        },
    )
    second = _publish_with_effect(
        tmp_path,
        objective="push same worktree",
        owned_path="experiments/candidates/alpha/b",
        effect_ref={
            "kind": "worktree",
            "operation": "PUSH",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        },
    )

    result = packets.compare_work_ids(tmp_path, [first["work_id"], second["work_id"]])

    assert result["outcome"] == "CONFLICT"
    assert {
        (reason.get("kind"), reason.get("resource_id"))
        for reason in result["pairs"][0]["reasons"]
        if reason["type"] == "EFFECT_RESOURCE_OVERLAP"
    } == {("worktree", "alpha/assignment-one")}


def test_shared_core_record_binds_real_worktree_apply_and_push_actions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha = "1" * 40
    monkeypatch.setattr(packets, "_current_git_head", lambda _: base_sha)
    monkeypatch.setattr(
        packets.hmasd_worktree,
        "path_is_tracked_at_commit",
        lambda _repo, _commit, _path: True,
    )

    def observe(_: Path, reference: dict[str, Any]) -> Any:
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "IN_PROGRESS", reference["path"]
        )

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    source = _cm_shared_packet_source(tmp_path)
    source["effect_refs"] = [
        {
            "kind": "worktree",
            "operation": "APPLY_INTEGRATION",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        },
        {
            "kind": "worktree",
            "operation": "PUSH",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        },
    ]
    authority = tmp_path / "docs/research/candidates/alpha/DIRECTION.md"
    authority.parent.mkdir(parents=True, exist_ok=True)
    wrong = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=["MODIFY_PATHS", "WORKTREE_APPLY_INTEGRATION"],
    )
    authority.write_text(
        packets.hmasd_protocol_contracts.render_shared_core_action_record(wrong),
        encoding="utf-8",
    )
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
        }
    ]
    wrong_packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(wrong_packet, repo=tmp_path)
    wrong_plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=wrong_packet["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert wrong_plan["verb"] == "CONFLICT"
    assert wrong_plan["defect"]["code"] == "SHARED_CORE_RECORD_NOT_FOUND"

    exact = packets.hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=base_sha,
        paths=source["owned_paths"],
        objective=source["objective"],
        non_goals=source["non_goals"],
        allowed_effects=[
            "MODIFY_PATHS",
            "WORKTREE_APPLY_INTEGRATION",
            "WORKTREE_PUSH",
        ],
    )
    authority.write_text(
        packets.hmasd_protocol_contracts.render_shared_core_action_record(exact),
        encoding="utf-8",
    )
    source["authority_refs"] = [
        {
            "path": "docs/research/candidates/alpha/DIRECTION.md",
            "sha256": packets.hmasd_state.sha256_bytes(authority.read_bytes()),
        }
    ]
    exact_packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(exact_packet, repo=tmp_path)
    exact_plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=exact_packet["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert exact_plan["verb"] == "DISPATCH_EXISTING"
    assert exact_plan["shared_core_action_digest"] == exact["action_digest"]


def test_direction_owned_cm_with_real_action_does_not_add_confirmation_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _packet_input(tmp_path)
    source["target_identity"] = "CM-alpha"
    source["owned_paths"] = ["experiments/candidates/alpha/variant"]
    source["effect_refs"] = [
        {
            "kind": "worktree",
            "operation": "RECORD_CANDIDATE",
            "path": ".codex/runtime/worktrees.json",
            "resource_id": "alpha/assignment-one",
        }
    ]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    def observe(_: Path, reference: dict[str, Any]) -> Any:
        return packets.hmasd_protocol_contracts.EffectObservation(
            reference["kind"], reference["resource_id"], "IN_PROGRESS", reference["path"]
        )

    def forbid(_: str) -> Any:
        raise AssertionError("direction-owned CM work must not parse shared-core records")

    monkeypatch.setattr(packets.hmasd_protocol_contracts, "observe_effect_ref", observe)
    monkeypatch.setattr(
        packets.hmasd_protocol_contracts, "parse_shared_core_action_records", forbid
    )
    plan = packets.reconcile_once(
        repo=tmp_path,
        work_id=packet["work_id"],
        observed_tasks=_observed_cm(),
    )["plan"]
    assert plan["verb"] == "DISPATCH_EXISTING"
