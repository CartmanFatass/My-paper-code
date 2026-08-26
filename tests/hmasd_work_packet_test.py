"""Focused contract tests for the v1 runtime-only Work Packet helper.

Packets are immutable runtime transport. Reconcile is an exact-work-id,
event-local, stateless planner; it never scans or executes the resulting plan.
"""

from __future__ import annotations

import copy
import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

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
        "non_goals": ["do not run an external send", "do not change shared core"],
        "owned_paths": [f"experiments/candidates/{direction}"],
        "done_criteria": ["write a durable result reference", "return one bounded outcome"],
        "effect_refs": [],
    }


def _publish(repo: Path, source: dict[str, Any]) -> dict[str, Any]:
    packet = packets.build_packet(source, repo=repo)
    packets.publish_packet(packet, repo=repo)
    return packet


def _existing_em(direction: str = "alpha") -> list[dict[str, Any]]:
    return [
        {
            "logical_identity": f"EM-{direction}",
            "kind": "em",
            "direction_id": direction,
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": f"thread-{direction}",
        }
    ]


def _plan(repo: Path, packet: dict[str, Any], observed_tasks: Any = ()) -> dict[str, Any]:
    return packets.reconcile_once(
        repo=repo,
        work_id=packet["work_id"],
        observed_tasks=observed_tasks,
    )["plan"]


def test_canonical_packet_identity_is_order_stable_but_changes_for_material_content(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    reordered = copy.deepcopy(source)
    reordered["non_goals"].reverse()
    reordered["done_criteria"].reverse()
    reordered["authority_refs"] = list(reversed(reordered["authority_refs"]))

    first = packets.build_packet(source, repo=tmp_path)
    second = packets.build_packet(reordered, repo=tmp_path)
    assert first == second
    assert packets.packet_id(source) == packets.packet_id(reordered)

    changed = copy.deepcopy(source)
    changed["objective"] = "advance a materially different discriminator"
    assert packets.packet_id(changed) != packets.packet_id(source)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"unexpected": True}),
        lambda value: value.update({"owned_paths": ["../outside"]}),
        lambda value: value.update({"owned_paths": ["experiments\\alias"]}),
        lambda value: value.update(
            {
                "authority_refs": [
                    {"path": "docs/research/x.json", "revision": 1, "extra": True}
                ]
            }
        ),
    ],
)
def test_packet_schema_and_path_contract_reject_invalid_or_extra_values(
    tmp_path: Path, mutate: Any
) -> None:
    value = _packet_input(tmp_path)
    mutate(value)
    with pytest.raises((packets.InvalidPacket, packets.PathRefusal)):
        packets.build_packet(value, repo=tmp_path)


def test_ordinary_work_packet_cannot_target_workflow_clerk_in_schema_or_python_api(
    tmp_path: Path,
) -> None:
    source = _packet_input(tmp_path)
    source["target_identity"] = "Workflow-Clerk"

    with pytest.raises(
        packets.InvalidPacket,
        match="ordinary Work Packet.*Workflow-Clerk",
    ):
        packets.build_packet(source, repo=tmp_path)

    valid = packets.build_packet(_packet_input(tmp_path), repo=tmp_path)
    clerk_packet = {**valid, "target_identity": "Workflow-Clerk"}
    clerk_content = {key: value for key, value in clerk_packet.items() if key != "work_id"}
    clerk_packet["work_id"] = packets.hmasd_state.sha256_bytes(
        packets.hmasd_state.canonical_bytes(clerk_content)
    )
    schema = json.loads(packets.SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(clerk_packet))
    with pytest.raises(
        packets.InvalidPacket,
        match="ordinary Work Packet.*Workflow-Clerk",
    ):
        packets.validate_packet(clerk_packet, repo=tmp_path)


def test_reconcile_rejects_ready_ordinary_work_packet_targeting_workflow_clerk(
    tmp_path: Path,
) -> None:
    valid = packets.build_packet(_packet_input(tmp_path), repo=tmp_path)
    clerk_packet = {**valid, "target_identity": "Workflow-Clerk"}
    clerk_content = {key: value for key, value in clerk_packet.items() if key != "work_id"}
    clerk_packet["work_id"] = packets.hmasd_state.sha256_bytes(
        packets.hmasd_state.canonical_bytes(clerk_content)
    )
    ready_path = (
        tmp_path
        / ".codex"
        / "runtime"
        / "work"
        / "ready"
        / clerk_packet["work_id"]
        / "packet.json"
    )
    _write_json(ready_path, clerk_packet)

    with pytest.raises(
        packets.InvalidPacket,
        match="ordinary Work Packet.*Workflow-Clerk",
    ):
        packets.reconcile_once(
            repo=tmp_path,
            work_id=clerk_packet["work_id"],
            observed_tasks=[],
        )


def test_partial_staging_is_not_runnable_or_replaced_silently(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    packet = packets.build_packet(source, repo=tmp_path)
    partial = tmp_path / ".codex" / "runtime" / "work" / "staging" / packet["work_id"]
    partial.mkdir(parents=True)
    (partial / "packet.json").write_text('{"work_id":', encoding="utf-8")

    with pytest.raises(packets.InvalidPacket, match="ready packet is missing"):
        packets.reconcile_once(repo=tmp_path, work_id=packet["work_id"], observed_tasks=[])
    rebuilt = packets.publish_packet(packet, repo=tmp_path)
    assert rebuilt["published"] is True
    assert Path(rebuilt["path"]).read_bytes() == packets.hmasd_state.canonical_bytes(packet)


def test_publish_is_immutable_and_rebuilt_same_packet_is_idempotent(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    first = packets.build_packet(source, repo=tmp_path)
    result = packets.publish_packet(first, repo=tmp_path)
    assert result["published"] is True

    rebuilt_input = copy.deepcopy(source)
    rebuilt_input["non_goals"].reverse()
    rebuilt = packets.build_packet(rebuilt_input, repo=tmp_path)
    assert rebuilt == first
    repeated = packets.publish_packet(rebuilt, repo=tmp_path)
    assert repeated["published"] is False
    assert Path(repeated["path"]).read_bytes() == packets.hmasd_state.canonical_bytes(first)


def test_reconcile_is_exact_and_ignores_a_corrupt_unrelated_ready_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = _publish(tmp_path, _packet_input(tmp_path, "alpha"))
    unrelated = _publish(tmp_path, _packet_input(tmp_path, "beta"))
    unrelated_path = (
        tmp_path / ".codex" / "runtime" / "work" / "ready" / unrelated["work_id"] / "packet.json"
    )
    unrelated_path.write_text('{"broken":', encoding="utf-8")
    before = unrelated_path.read_bytes()

    def forbid_iterdir(_: Path) -> Any:
        raise AssertionError("event-local reconcile must not scan ready")

    monkeypatch.setattr(Path, "iterdir", forbid_iterdir)
    plan = _plan(tmp_path, selected, _existing_em())

    assert plan["verb"] == "DISPATCH_EXISTING"
    assert plan["work_id"] == selected["work_id"]
    assert unrelated_path.read_bytes() == before


def test_invalid_work_id_is_rejected_before_any_runtime_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_runtime_lookup(_: Path) -> Path:
        raise AssertionError("runtime lookup occurred")

    monkeypatch.setattr(packets, "_work_root", fail_runtime_lookup)
    with pytest.raises(packets.InvalidPacket, match="lowercase SHA256"):
        packets.reconcile_once(repo=tmp_path, work_id="not-a-work-id")


def test_missing_exact_ready_packet_is_an_error(tmp_path: Path) -> None:
    work_id = "a" * 64
    with pytest.raises(packets.InvalidPacket, match=work_id):
        packets.reconcile_once(repo=tmp_path, work_id=work_id, observed_tasks=[])


def test_reconcile_reuses_one_compatible_observed_identity(tmp_path: Path) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    plan = _plan(tmp_path, packet, _existing_em())
    assert plan == {
        "verb": "DISPATCH_EXISTING",
        "delivery_key": packet["work_id"],
        "delivery_semantics": "AT_LEAST_ONCE_IDEMPOTENT_INTAKE",
        "requested_target_identity": "EM-alpha",
        "target_identity": "EM-alpha",
        "task_resolution": {
            "status": "REUSE",
            "logical_identity": "EM-alpha",
            "kind": "em",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-alpha",
        },
        "unknown_effect_refs": [],
        "work_id": packet["work_id"],
    }


def test_reconcile_emits_create_task_intent_without_mutating_snapshot(tmp_path: Path) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    snapshot = tmp_path / ".codex" / "runtime" / "tasks.json"
    _write_json(snapshot, {"tasks": []})
    before = snapshot.read_bytes()

    plan = _plan(tmp_path, packet, ".codex/runtime/tasks.json")

    assert plan["verb"] == "CREATE_TASK_INTENT"
    assert plan["task_resolution"] == {
        "status": "CREATE_TASK",
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 1,
    }
    assert snapshot.read_bytes() == before


def test_reconcile_maps_task_identity_conflict_to_closed_conflict_verb(tmp_path: Path) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    duplicate = [*_existing_em(), {**_existing_em()[0], "lifecycle": "WAITING"}]
    plan = _plan(tmp_path, packet, duplicate)
    assert plan["verb"] == "CONFLICT"
    assert plan["conflict_type"] == "TASK_IDENTITY_CONFLICT"
    assert plan["task_resolution"]["status"] == "TASK_IDENTITY_CONFLICT"


@pytest.mark.parametrize("reference_kind", ["revision", "sha256"])
def test_reconcile_maps_stale_authority_to_closed_conflict_verb(
    tmp_path: Path, reference_kind: str
) -> None:
    source = _packet_input(tmp_path)
    scope_path = tmp_path / source["scope_ref"]["path"]
    if reference_kind == "sha256":
        source["scope_ref"] = {
            "path": source["scope_ref"]["path"],
            "sha256": packets.hmasd_state.sha256_bytes(scope_path.read_bytes()),
        }
    packet = _publish(tmp_path, source)
    _write_json(scope_path, {"revision": 8, "changed": True})

    plan = _plan(tmp_path, packet, _existing_em())
    assert plan["verb"] == "CONFLICT"
    assert plan["conflict_type"] == "STALE_AUTHORITY"
    assert plan["work_id"] == packet["work_id"]


def test_unknown_effect_maps_to_observe_only_without_mutation(tmp_path: Path) -> None:
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
    packet = _publish(tmp_path, source)
    before = (tmp_path / effect_path).read_bytes()

    plan = _plan(tmp_path, packet, _existing_em())

    assert plan["verb"] == "OBSERVE_EFFECT_ONLY"
    assert plan["unknown_effect_refs"] == [effect_path]
    assert (tmp_path / effect_path).read_bytes() == before


def test_same_work_id_concurrent_planners_do_not_overlap_inside_exact_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    active = 0
    peak = 0
    guard = threading.Lock()
    entered = threading.Event()
    real_plan = packets._plan_packet

    def observed_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal active, peak
        with guard:
            active += 1
            peak = max(peak, active)
            entered.set()
        time.sleep(0.08)
        try:
            return real_plan(*args, **kwargs)
        finally:
            with guard:
                active -= 1

    monkeypatch.setattr(packets, "_plan_packet", observed_plan)
    results: list[dict[str, Any]] = []

    def wake() -> None:
        results.append(_plan(tmp_path, packet, _existing_em()))

    threads = [threading.Thread(target=wake), threading.Thread(target=wake)]
    for thread in threads:
        thread.start()
    assert entered.wait(timeout=2)
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()

    assert peak == 1
    assert results[0] == results[1]


def test_reconcile_cli_requires_work_id_and_is_byte_identical_for_same_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    snapshot = tmp_path / ".codex" / "runtime" / "tasks.json"
    _write_json(snapshot, {"tasks": _existing_em()})
    argv = [
        "reconcile",
        "--once",
        "--repo",
        str(tmp_path),
        "--work-id",
        packet["work_id"],
        "--observed-tasks",
        ".codex/runtime/tasks.json",
    ]

    assert packets.main(argv) == 0
    first = capsys.readouterr().out.encode("utf-8")
    assert packets.main(argv) == 0
    second = capsys.readouterr().out.encode("utf-8")

    assert first == second
    assert str(tmp_path).encode() not in first
    assert json.loads(first)["plan"]["verb"] == "DISPATCH_EXISTING"
    with pytest.raises(SystemExit) as missing_snapshot:
        packets.main(
            [
                "reconcile",
                "--once",
                "--repo",
                str(tmp_path),
                "--work-id",
                packet["work_id"],
            ]
        )
    assert missing_snapshot.value.code == 2
    with pytest.raises(SystemExit) as missing:
        packets.main(["reconcile", "--once", "--repo", str(tmp_path)])
    assert missing.value.code == 2


def test_slash_generation_target_creates_and_reuses_runtime_identity(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    source["target_identity"] = "EM/alpha/g2"
    packet = _publish(tmp_path, source)
    created = _plan(tmp_path, packet, [])
    assert created["verb"] == "CREATE_TASK_INTENT"
    assert created["requested_target_identity"] == "EM/alpha/g2"
    assert created["task_resolution"]["logical_identity"] == "EM-alpha"
    assert created["task_resolution"]["generation"] == 2

    observed = [{**_existing_em()[0], "generation": 2}]
    reused = _plan(tmp_path, packet, observed)
    assert reused["verb"] == "DISPATCH_EXISTING"
    assert reused["task_resolution"]["generation"] == 2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"target_identity": "EM-beta"}),
        lambda value: value.update({"owned_paths": ["temp/directions/gamma/test"]}),
    ],
)
def test_direction_inconsistent_target_or_owned_path_is_refused(
    tmp_path: Path, mutate: Any
) -> None:
    source = _packet_input(tmp_path)
    mutate(source)
    with pytest.raises(packets.InvalidPacket, match="direction"):
        packets.build_packet(source, repo=tmp_path)


@pytest.mark.parametrize("output", ["../escaped.json", "C:/outside/packet.json"])
def test_build_cli_refuses_absolute_and_alias_output_paths(tmp_path: Path, output: str) -> None:
    source = _packet_input(tmp_path)
    input_path = tmp_path / "input.json"
    _write_json(input_path, source)
    result = packets.main(
        ["build", "--repo", str(tmp_path), "--input", str(input_path), "--output", output]
    )
    assert result in {2, 5}
    assert not (tmp_path.parent / "escaped.json").exists()


def test_repeated_exact_plan_preserves_at_least_once_delivery_key(tmp_path: Path) -> None:
    packet = _publish(tmp_path, _packet_input(tmp_path))
    first = _plan(tmp_path, packet, [])
    second = _plan(tmp_path, packet, [])
    assert first == second
    assert first["delivery_semantics"] == "AT_LEAST_ONCE_IDEMPOTENT_INTAKE"
    assert first["delivery_key"] == packet["work_id"]


def test_canonical_manager_with_other_nonterminal_scope_alias_conflicts(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    source["target_identity"] = "EM/alpha/g1"
    packet = _publish(tmp_path, source)
    observed = [
        *_existing_em(),
        {
            "logical_identity": "EM-alpha-shadow",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "PARKED",
        },
    ]
    plan = _plan(tmp_path, packet, observed)
    assert plan["verb"] == "CONFLICT"
    assert "multiple observed tasks represent" in plan["task_resolution"]["reason"]


@pytest.mark.parametrize(
    "owned_root",
    [
        "experiments/candidates",
        "tests/experiments/candidates",
        "docs/research/candidates",
        "temp/directions",
    ],
)
def test_owned_paths_reject_bare_direction_roots(tmp_path: Path, owned_root: str) -> None:
    source = _packet_input(tmp_path)
    source["owned_paths"] = [owned_root]
    with pytest.raises(packets.WorkPacketError, match="bare direction roots"):
        packets.build_packet(source, repo=tmp_path)


@pytest.mark.parametrize(
    "path",
    [
        "temp/directions/alpha/file.txt:stream",
        "temp/directions/alpha/file.",
        "temp/directions/alpha/file ",
        "temp/directions/alpha/\x01file",
    ],
)
def test_windows_ambiguous_ads_trailing_and_control_paths_are_refused(
    tmp_path: Path, path: str
) -> None:
    source = _packet_input(tmp_path)
    source["owned_paths"] = [path]
    with pytest.raises(packets.PathRefusal):
        packets.build_packet(source, repo=tmp_path)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"owned_paths": ["a//b"]}),
        lambda value: value.update({"owned_paths": ["a/./b"]}),
        lambda value: value.update({"owned_paths": ["a/"]}),
        lambda value: value.update({"owned_paths": ["a:b"]}),
        lambda value: value.update({"objective": "   \t"}),
        lambda value: value.update({"non_goals": ["  "]}),
        lambda value: value.update({"done_criteria": ["\t"]}),
    ],
)
def test_schema_and_normalizer_reject_the_same_boundary_inputs(
    tmp_path: Path, mutate: Any
) -> None:
    schema = json.loads(packets.SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    valid = packets.build_packet(_packet_input(tmp_path), repo=tmp_path)
    assert list(validator.iter_errors(valid)) == []
    assert packets.build_packet(valid, repo=tmp_path) == valid

    invalid = copy.deepcopy(valid)
    mutate(invalid)
    assert list(validator.iter_errors(invalid)), invalid
    with pytest.raises(packets.WorkPacketError):
        packets.build_packet(invalid, repo=tmp_path)
