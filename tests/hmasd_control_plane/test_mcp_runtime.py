from __future__ import annotations

import json
import os
import inspect
import threading
from pathlib import Path

import pytest

from tools.hmasd_control_plane import mcp_runtime
from tools.hmasd_control_plane.diagnostics import collect_doctor, collect_incidents


def test_multiple_stdio_instances_are_unique_and_not_a_singleton_error(
    tmp_path: Path,
) -> None:
    first = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="one", profile="observability"
    )
    second = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="two", profile="orchestrator"
    )

    index = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert index["registry_exists"] is True
    assert len({item["instance_id"] for item in index["instances"]}) == 2
    assert {item["status"] for item in index["instances"]} == {"ACTIVE"}

    first.close()
    second.close()
    closed = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert {item["status"] for item in closed["instances"]} == {"CLOSED"}


def test_normal_close_is_immutable_and_contains_no_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HMASD_MCP_TEST_SECRET", "must-not-be-recorded")
    registration = mcp_runtime.begin_mcp_instance(
        tmp_path,
        server_name="hmasd_observability",
        profile="observability",
        state_path=tmp_path / "state.sqlite3",
    )
    terminal = registration.close()

    start_path = registration.instance_root / "start.json"
    terminal_path = registration.instance_root / "terminal.json"
    start = json.loads(start_path.read_text(encoding="utf-8"))
    assert start["transport"] == "stdio"
    assert start["pid"] == os.getpid()
    assert terminal["exit_kind"] == "NORMAL"
    assert terminal_path.is_file()
    assert "must-not-be-recorded" not in start_path.read_text(encoding="utf-8")
    with pytest.raises(mcp_runtime.MCPRuntimeRecordError):
        registration.close()


def test_abnormal_disappearance_and_pid_reuse_are_distinguished(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mcp_runtime,
        "process_identity",
        lambda _pid: {
            "probe_state": "RUNNING",
            "process_start_token": "token-old",
            "process_started_at": "2026-08-20T00:00:00Z",
            "probe_error": None,
        },
    )
    missing = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="missing", profile="test"
    )
    reused = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="reused", profile="test"
    )

    def probe(pid: int):
        if pid == missing.start["pid"]:
            # Both records use this process PID, so classify them together in
            # two separate probes below rather than pretending PID is unique.
            return {
                "probe_state": "NOT_FOUND",
                "process_start_token": None,
                "process_started_at": None,
                "probe_error": "fixture",
            }
        raise AssertionError

    monkeypatch.setattr(mcp_runtime, "process_identity", probe)
    gone = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert {item["status"] for item in gone["instances"]} == {"STALE"}
    assert {item["reason"] for item in gone["instances"]} == {
        "pid_not_found_without_terminal"
    }

    monkeypatch.setattr(
        mcp_runtime,
        "process_identity",
        lambda _pid: {
            "probe_state": "RUNNING",
            "process_start_token": "token-new",
            "process_started_at": "2026-08-20T01:00:00Z",
            "probe_error": None,
        },
    )
    reused_index = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert {item["reason"] for item in reused_index["instances"]} == {"pid_reused"}


def test_conflicting_record_identity_is_unknown_not_active(tmp_path: Path) -> None:
    registration = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="server", profile="test"
    )
    start_path = registration.instance_root / "start.json"
    start = json.loads(start_path.read_text(encoding="utf-8"))
    start["instance_id"] = "conflicting-id"
    start_path.write_text(json.dumps(start), encoding="utf-8")

    index = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert index["instances"][0]["status"] == "UNKNOWN"
    assert index["instances"][0]["reason"] == "InstanceIdConflict"
    assert index["record_errors"][0]["error"] == "InstanceIdConflict"


def test_runtime_json_is_not_visible_before_complete_atomic_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_path = tmp_path / "start.json"
    link_reached = threading.Event()
    release_link = threading.Event()
    original_link = mcp_runtime.os.link

    def delayed_link(source, destination):
        link_reached.set()
        assert release_link.wait(timeout=5)
        return original_link(source, destination)

    monkeypatch.setattr(mcp_runtime.os, "link", delayed_link)
    failure: list[BaseException] = []

    def publish() -> None:
        try:
            mcp_runtime._publish_json_no_overwrite(final_path, {"complete": True})
        except BaseException as exc:  # pragma: no cover
            failure.append(exc)

    thread = threading.Thread(target=publish)
    thread.start()
    assert link_reached.wait(timeout=5)
    assert final_path.exists() is False
    release_link.set()
    thread.join(timeout=5)
    assert failure == []
    assert json.loads(final_path.read_text(encoding="utf-8")) == {"complete": True}


def test_missing_registry_is_explicitly_absent(tmp_path: Path) -> None:
    index = mcp_runtime.inspect_mcp_instances(tmp_path)
    assert index["registry_exists"] is False
    assert index["instances"] == []


def test_instance_runtime_has_no_singleton_heartbeat_or_cleanup_loop() -> None:
    source = inspect.getsource(mcp_runtime).lower()
    assert "def heartbeat" not in source
    assert "heartbeat.json" not in source
    assert "def cleanup" not in source
    assert "singleton.lock" not in source
    assert "sleep(" not in source


def test_doctor_treats_multiple_instances_as_info_and_stale_as_incident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="one", profile="test"
    )
    second = mcp_runtime.begin_mcp_instance(
        tmp_path, server_name="two", profile="test"
    )
    doctor, exit_code = collect_doctor(tmp_path, component="mcp-runtime")
    assert exit_code == 0
    assert doctor["status"] == "OK"
    assert doctor["counters"]["mcp_instances_active"] == 2
    assert doctor["findings"][0]["severity"] == "INFO"
    assert "not a singleton or leak failure" in doctor["findings"][0]["observed_fact"]

    monkeypatch.setattr(
        mcp_runtime,
        "process_identity",
        lambda _pid: {
            "probe_state": "NOT_FOUND",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": "fixture",
        },
    )
    stale_doctor, stale_code = collect_doctor(
        tmp_path, component="mcp-runtime"
    )
    incidents, incident_code = collect_incidents(
        tmp_path, component="mcp-runtime"
    )
    assert stale_code == incident_code == 0
    assert stale_doctor["status"] == "ATTENTION"
    assert stale_doctor["counters"]["mcp_instances_stale"] == 2
    assert len(incidents) == 2
    assert all(item["component"] == "mcp-runtime" for item in incidents)
    del first, second
