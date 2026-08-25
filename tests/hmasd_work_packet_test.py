"""Focused contract tests for the v1 runtime-only Work Packet helper.

These tests use its public Python API.  Packets are intentionally runtime
transport: durable authority remains ordinary repository files, while the
ignored ``.codex/runtime/work`` tree only carries an immutable delivery copy.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts import hmasd_work_packet as packets


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _packet_input(repo: Path, direction: str = "alpha") -> dict[str, Any]:
    root = repo / "docs" / "research" / "candidates" / direction
    _write_json(root / "STATE.json", {"revision": 7, "direction": direction})
    _write_json(root / "DIRECTION.json", {"revision": 3, "direction": direction})
    return {
        "schema_version": 1,
        "scope_ref": {"path": f"docs/research/candidates/{direction}/STATE.json", "revision": 7},
        "sender_identity": "Portfolio",
        "target_identity": f"EM-{direction}",
        "authority_refs": [
            {"path": f"docs/research/candidates/{direction}/DIRECTION.json", "revision": 3}
        ],
        "objective": "advance one bounded discriminator",
        "non_goals": ["do not run an external send", "do not change shared core"],
        "owned_paths": [f"experiments/candidates/{direction}"],
        "done_criteria": ["write a durable result reference", "return one bounded outcome"],
        "effect_refs": [],
    }


def test_canonical_packet_identity_is_order_stable_but_changes_for_material_content(tmp_path: Path) -> None:
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
        lambda value: value.update({"authority_refs": [{"path": "docs/research/x.json", "revision": 1, "extra": True}]}),
    ],
)
def test_packet_schema_and_path_contract_reject_invalid_or_extra_values(
    tmp_path: Path, mutate: Any
) -> None:
    value = _packet_input(tmp_path)
    mutate(value)
    with pytest.raises((packets.InvalidPacket, packets.PathRefusal)):
        packets.build_packet(value, repo=tmp_path)


def test_partial_staging_is_not_runnable_or_replaced_silently(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    packet = packets.build_packet(source, repo=tmp_path)
    partial = tmp_path / ".codex" / "runtime" / "work" / "staging" / packet["work_id"]
    partial.mkdir(parents=True)
    (partial / "packet.json").write_text('{"work_id":', encoding="utf-8")

    observed = packets.reconcile_once(repo=tmp_path)
    assert observed["actions"] == []
    assert observed["errors"] == []
    # A staging residue is never runnable.  It may be safely rebuilt because
    # this exact directory is ignored, digest-scoped runtime transport.
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


def test_reconcile_same_key_is_serial_across_concurrent_wakes(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    active = 0
    peak = 0
    guard = threading.Lock()
    entered = threading.Event()

    def handler(_: dict[str, Any], __: dict[str, Any]) -> None:
        nonlocal active, peak
        with guard:
            active += 1
            peak = max(peak, active)
            entered.set()
        time.sleep(0.08)
        with guard:
            active -= 1

    threads = [threading.Thread(target=packets.reconcile_once, kwargs={"repo": tmp_path, "handler": handler}) for _ in range(2)]
    for thread in threads:
        thread.start()
    assert entered.wait(timeout=2)
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert peak == 1


def test_reconcile_advances_independent_directions_and_isolates_local_failure(tmp_path: Path) -> None:
    alpha = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    beta = packets.build_packet(_packet_input(tmp_path, "beta"), repo=tmp_path)
    packets.publish_packet(alpha, repo=tmp_path)
    packets.publish_packet(beta, repo=tmp_path)
    called: list[str] = []

    def handler(packet: dict[str, Any], _: dict[str, Any]) -> str:
        direction = packet["target_identity"].removeprefix("EM-")
        called.append(direction)
        if direction == "alpha":
            raise RuntimeError("alpha local failure")
        return "beta advanced"

    result = packets.reconcile_once(repo=tmp_path, handler=handler)
    assert sorted(called) == ["alpha", "beta"]
    assert [item["target_identity"] for item in result["actions"]] == ["EM-beta"]
    assert len(result["errors"]) == 1
    assert result["errors"][0]["work_id"] == alpha["work_id"]


def test_superseded_authority_is_not_runnable(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    _write_json(tmp_path / source["scope_ref"]["path"], {"revision": 8})

    result = packets.reconcile_once(repo=tmp_path)
    assert result["actions"] == []
    assert len(result["stale"]) == 1
    assert result["stale"][0]["work_id"] == packet["work_id"]


def test_sha256_authority_advance_is_not_runnable(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    scope_path = tmp_path / source["scope_ref"]["path"]
    source["scope_ref"] = {
        "path": source["scope_ref"]["path"],
        "sha256": packets.hmasd_state.sha256_bytes(scope_path.read_bytes()),
    }
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    _write_json(scope_path, {"revision": 7, "changed": True})

    result = packets.reconcile_once(repo=tmp_path)
    assert result["actions"] == []
    assert result["stale"] == [{"work_id": packet["work_id"], "reason": "scope_ref sha256 advanced"}]


def test_unknown_effect_is_observed_without_dispatching_new_effect(tmp_path: Path) -> None:
    source = _packet_input(tmp_path)
    effect_path = "temp/directions/alpha/exp/run-1/effect.json"
    _write_json(tmp_path / effect_path, {"status": "UNKNOWN", "send_count": 1})
    source["effect_refs"] = [{"path": effect_path}]
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed: list[dict[str, Any]] = []

    def handler(_: dict[str, Any], action: dict[str, Any]) -> None:
        observed.append(action)

    result = packets.reconcile_once(repo=tmp_path, handler=handler)
    assert result["errors"] == []
    # UNKNOWN is a pure observation boundary: the generic dispatcher is not
    # invoked, but reconcile reports the observable action for a caller that
    # owns an effect-specific observer.
    assert observed == []
    assert result["actions"][0]["action"] == "OBSERVE_EFFECT"
    assert result["actions"][0]["observe_only"] is True
    assert result["actions"][0]["unknown_effect_refs"] == [effect_path]
    assert json.loads((tmp_path / effect_path).read_text(encoding="utf-8"))["send_count"] == 1


def test_lazy_manager_resolution_reuses_one_compatible_observed_identity(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "RUNNING",
            "thread_id": "thread-existing",
        }
    ]

    result = packets.reconcile_once(repo=tmp_path, observed_tasks=observed)
    action = result["actions"][0]
    assert action["action"] == "DISPATCH"
    assert action["task_resolution"] == {
        "status": "REUSE",
        "logical_identity": "EM-alpha",
        "kind": "em",
        "generation": 1,
        "lifecycle": "RUNNING",
        "thread_id": "thread-existing",
    }


def test_lazy_manager_resolution_emits_create_intent_when_absent(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)

    result = packets.reconcile_once(repo=tmp_path, observed_tasks=[])
    action = result["actions"][0]
    assert action["action"] == "CREATE_TASK"
    assert action["task_resolution"] == {
        "status": "CREATE_TASK",
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 1,
    }


def test_lazy_manager_resolution_reports_duplicate_identity_conflict(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    duplicate = [
        {"logical_identity": "EM-alpha", "kind": "em", "direction_id": "alpha", "generation": 1, "lifecycle": "RUNNING"},
        {"logical_identity": "EM-alpha", "kind": "em", "direction_id": "alpha", "generation": 1, "lifecycle": "WAITING"},
    ]

    result = packets.reconcile_once(repo=tmp_path, observed_tasks=duplicate)
    action = result["actions"][0]
    assert action["action"] == "TASK_IDENTITY_CONFLICT"
    assert action["task_resolution"]["status"] == "TASK_IDENTITY_CONFLICT"
    assert "multiple observed tasks" in action["task_resolution"]["reason"]


def test_two_concurrent_reconciles_reload_task_snapshot_under_key_lock(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    snapshot = tmp_path / ".codex" / "runtime" / "tasks.json"
    initial = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": "2026-08-25T00:00:00Z",
        "writer": "Root",
        "tasks": [],
    }
    packets.hmasd_state.atomic_write(snapshot, packets.hmasd_state.canonical_bytes(initial))
    create_count = 0
    guard = threading.Lock()
    results: list[dict[str, Any]] = []

    def handler(_: dict[str, Any], action: dict[str, Any]) -> None:
        nonlocal create_count
        if action["action"] != "CREATE_TASK":
            return
        with guard:
            create_count += 1
        created = {
            "schema_version": 1,
            "revision": 2,
            "updated_at": "2026-08-25T00:00:01Z",
            "writer": "Root",
            "tasks": [
                {
                    "logical_identity": action["task_resolution"]["logical_identity"],
                    "kind": "em",
                    "direction_id": "alpha",
                    "generation": 1,
                    "task_title": "Alpha EM",
                    "lifecycle": "ACTIVE",
                }
            ],
        }
        packets.hmasd_state.atomic_write(snapshot, packets.hmasd_state.canonical_bytes(created))

    def wake() -> None:
        results.append(
            packets.reconcile_once(
                repo=tmp_path,
                observed_tasks=".codex/runtime/tasks.json",
                handler=handler,
            )
        )

    threads = [threading.Thread(target=wake), threading.Thread(target=wake)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()

    assert create_count == 1
    actions = [result["actions"][0] for result in results]
    assert {action["action"] for action in actions} == {"CREATE_TASK", "DISPATCH"}
    assert {result["task_observation_semantics"] for result in results} == {"RELOAD_PATH_UNDER_KEY_LOCK"}


def test_slash_generation_target_creates_and_reuses_runtime_task_identity(tmp_path: Path) -> None:
    source = _packet_input(tmp_path, "alpha")
    source["target_identity"] = "EM/alpha/g2"
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    created = packets.reconcile_once(repo=tmp_path, observed_tasks=[])["actions"][0]
    assert created["action"] == "CREATE_TASK"
    assert created["requested_target_identity"] == "EM/alpha/g2"
    assert created["task_resolution"] == {
        "status": "CREATE_TASK",
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 2,
    }
    runtime = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": "2026-08-25T00:00:00Z",
        "writer": "Root",
        "tasks": [
            {
                "logical_identity": "EM-alpha",
                "kind": "em",
                "direction_id": "alpha",
                "generation": 2,
                "task_title": "Alpha EM generation 2",
                "lifecycle": "ACTIVE",
            }
        ],
    }
    packets.hmasd_state.validate_document("runtime_tasks", runtime)
    reused = packets.reconcile_once(repo=tmp_path, observed_tasks=runtime["tasks"])["actions"][0]
    assert reused["action"] == "DISPATCH"
    assert reused["task_resolution"]["status"] == "REUSE"
    assert reused["task_resolution"]["logical_identity"] == "EM-alpha"
    assert reused["task_resolution"]["generation"] == 2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"target_identity": "EM-beta"}),
        lambda value: value.update({"owned_paths": ["temp/directions/gamma/test"]}),
    ],
)
def test_direction_inconsistent_target_or_owned_path_is_refused(tmp_path: Path, mutate: Any) -> None:
    source = _packet_input(tmp_path, "alpha")
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


def test_repeated_reconcile_preserves_at_least_once_delivery_key(tmp_path: Path) -> None:
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    first = packets.reconcile_once(repo=tmp_path, observed_tasks=[])["actions"][0]
    second = packets.reconcile_once(repo=tmp_path, observed_tasks=[])["actions"][0]
    assert first["delivery_semantics"] == "AT_LEAST_ONCE_IDEMPOTENT_INTAKE"
    assert second["delivery_semantics"] == "AT_LEAST_ONCE_IDEMPOTENT_INTAKE"
    assert first["delivery_key"] == second["delivery_key"] == packet["work_id"]


def test_same_reconcile_key_with_distinct_packet_content_conflicts_before_handlers(tmp_path: Path) -> None:
    first_input = _packet_input(tmp_path, "alpha")
    second_input = copy.deepcopy(first_input)
    second_input["objective"] = "same authority but a different bounded objective"
    first = packets.build_packet(first_input, repo=tmp_path)
    second = packets.build_packet(second_input, repo=tmp_path)
    assert first["work_id"] != second["work_id"]
    packets.publish_packet(first, repo=tmp_path)
    packets.publish_packet(second, repo=tmp_path)
    invoked: list[str] = []

    result = packets.reconcile_once(
        repo=tmp_path,
        observed_tasks=[],
        handler=lambda packet, _: invoked.append(packet["work_id"]),
    )
    assert result["actions"] == []
    assert invoked == []
    assert result["errors"] == [
        {
            "code": "PACKET_KEY_CONFLICT",
            "error": "one reconcile key has multiple Work Packets",
            "key": packets._reconcile_key(first),
            "type": "PacketConflict",
            "work_id": min(first["work_id"], second["work_id"]),
            "work_ids": sorted([first["work_id"], second["work_id"]]),
        }
    ]


def test_canonical_manager_with_other_nonterminal_scope_alias_conflicts(tmp_path: Path) -> None:
    source = _packet_input(tmp_path, "alpha")
    source["target_identity"] = "EM/alpha/g1"
    packet = packets.build_packet(source, repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    observed = [
        {"logical_identity": "EM-alpha", "kind": "em", "direction_id": "alpha", "generation": 1, "lifecycle": "ACTIVE"},
        {"logical_identity": "EM-alpha-shadow", "kind": "em", "direction_id": "alpha", "generation": 1, "lifecycle": "PARKED"},
    ]
    result = packets.reconcile_once(repo=tmp_path, observed_tasks=observed)
    action = result["actions"][0]
    assert action["action"] == "TASK_IDENTITY_CONFLICT"
    assert action["task_resolution"]["logical_identity"] == "EM-alpha"
    assert "multiple observed tasks represent the same non-terminal manager scope" in action["task_resolution"]["reason"]


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
    source = _packet_input(tmp_path, "alpha")
    source["owned_paths"] = [owned_root]
    with pytest.raises(packets.WorkPacketError, match="bare direction roots"):
        packets.build_packet(source, repo=tmp_path)


@pytest.mark.parametrize(
    "path",
    ["temp/directions/alpha/file.txt:stream", "temp/directions/alpha/file.", "temp/directions/alpha/file ", "temp/directions/alpha/\x01file"],
)
def test_windows_ambiguous_ads_trailing_and_control_paths_are_refused(tmp_path: Path, path: str) -> None:
    source = _packet_input(tmp_path, "alpha")
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
def test_schema_and_normalizer_reject_the_same_boundary_inputs(tmp_path: Path, mutate: Any) -> None:
    schema = json.loads(packets.SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    valid = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    assert list(validator.iter_errors(valid)) == []
    assert packets.build_packet(valid, repo=tmp_path) == valid

    invalid = copy.deepcopy(valid)
    mutate(invalid)
    assert list(validator.iter_errors(invalid)), invalid
    with pytest.raises(packets.WorkPacketError):
        packets.build_packet(invalid, repo=tmp_path)


def test_windows_subprocesses_do_not_overlap_one_reconcile_key_handler(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("cross-process lock regression is specific to the Windows host contract")
    packet = packets.build_packet(_packet_input(tmp_path, "alpha"), repo=tmp_path)
    packets.publish_packet(packet, repo=tmp_path)
    marker = tmp_path / "handler-active.marker"
    overlap = tmp_path / "handler-overlap.marker"
    started = tmp_path / "handler-started.marker"
    code = "\n".join(
        [
            "import sys, time",
            "from pathlib import Path",
            "from scripts import hmasd_work_packet as packets",
            "repo = Path(sys.argv[1])",
            "marker, overlap, started = (Path(value) for value in sys.argv[2:5])",
            "def handler(packet, action):",
            "    if marker.exists(): overlap.write_text('overlap', encoding='utf-8')",
            "    marker.write_text('active', encoding='utf-8')",
            "    started.write_text('started', encoding='utf-8')",
            "    time.sleep(0.35)",
            "    marker.unlink(missing_ok=True)",
            "packets.reconcile_once(repo=repo, observed_tasks=[], handler=handler)",
        ]
    )
    arguments = [sys.executable, "-c", code, str(tmp_path), str(marker), str(overlap), str(started)]
    first = subprocess.Popen(arguments, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 5
    while not started.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert started.exists(), first.communicate(timeout=5)
    second = subprocess.Popen(arguments, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    first_out, first_err = first.communicate(timeout=10)
    second_out, second_err = second.communicate(timeout=10)
    assert first.returncode == 0, (first_out, first_err)
    assert second.returncode == 0, (second_out, second_err)
    assert not overlap.exists()
