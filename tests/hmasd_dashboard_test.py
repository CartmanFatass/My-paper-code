"""Focused read-only Dashboard contract tests.

These tests use the Phase-0 JSON fixtures as isolated authoritative files.  The
service tests intentionally exercise the real ThreadingHTTPServer rather than a
mock request adapter.
"""

from __future__ import annotations

import hashlib
import http.client
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from typing import Any

import pytest

import scripts.hmasd_dashboard as dashboard


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "tests" / "fixtures" / "hmasd_phase0"


def _copy_json(source: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PHASE0 / source, target)


def fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    (root / ".omp").mkdir(parents=True)
    (root / ".omp" / "AGENTS.md").write_text("HMASD fixture\n", encoding="utf-8")
    _copy_json("portfolio_registry.json", root / dashboard.REGISTRY_REL)
    _copy_json("runtime_agents.json", root / dashboard.RUNTIME_AGENTS_REL)
    _copy_json("runtime_worktrees.json", root / dashboard.RUNTIME_WORKTREES_REL)
    _copy_json(
        "research_state.json",
        root / "docs/research/candidates/example-direction/workflow/research/state.json",
    )
    _copy_json(
        "engineering_state.json",
        root / "docs/research/candidates/example-direction/workflow/engineering/state.json",
    )
    _copy_json(
        "external_review_index.json",
        root / "docs/research/candidates/example-direction/workflow/external-review/index.json",
    )
    _copy_json(
        "run_manifest.json",
        root / "temp/directions/example-direction/exp/example-run/manifest.json",
    )
    _copy_json(
        "accepted_result.json",
        root / "docs/research/candidates/example-direction/results/example-result.json",
    )
    (root / ".codex/runtime/clerk-liveness.json").write_bytes(
        dashboard._json_bytes(
            {
                "schema_version": 1,
                "observed_at": "2026-08-27T14:30:00Z",
                "actions": [
                    {
                        "kind": "REDELIVER_ASSIGNMENT",
                        "locator": ".codex/runtime/session-envelopes/example-direction/example.assignment.json",
                        "message": "secret transport message",
                        "recipient_thread_id": "secret-thread",
                    }
                ],
                "directions": [
                    {
                        "direction_id": "example-direction",
                        "lifecycle": "ACTIVE",
                        "stage": "CM",
                        "reason": "OWNED_WORK",
                        "owner_identity": "CM/example-direction/g1",
                        "task_status": "active",
                        "next_owner": None,
                        "assignment_locator": ".codex/runtime/session-envelopes/example-direction/example.assignment.json",
                        "return_locator": None,
                        "recovery_kind": "REDELIVER_ASSIGNMENT",
                    }
                ],
            }
        )
    )
    return root


def _install_source_mutator(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    *,
    repeat: bool,
) -> dict[str, int]:
    original = dashboard._read_bytes
    state = {"mutations": 0}

    def mutating_read(path: Path) -> tuple[bytes | None, str | None]:
        raw, error = original(path)
        if path == target and raw is not None and (repeat or state["mutations"] == 0):
            value = json.loads(raw)
            value["revision"] += 1
            value["updated_at"] = f"2026-08-24T00:00:{value['revision']:02d}Z"
            target.write_bytes(dashboard._json_bytes(value))
            state["mutations"] += 1
        return raw, error

    monkeypatch.setattr(dashboard, "_read_bytes", mutating_read)
    return state


def _runtime_agent(
    logical_identity: str,
    agent_type: str,
    parent_identity: str,
    job_ref: str,
    *,
    generation: int = 1,
) -> dict[str, Any]:
    return {
        "agent_type": agent_type,
        "generation": generation,
        "last_seen_at": "2026-08-24T00:00:00Z",
        "lifecycle": "RUNNING",
        "logical_identity": logical_identity,
        "job_ref": job_ref,
        "parent_identity": parent_identity,
        "runtime_ref": f"runtime-{logical_identity.lower()}",
        "session_ref": f"session-{logical_identity.lower()}",
    }


def _request(server: dashboard.DashboardServer, method: str, path: str) -> tuple[int, dict[str, str], bytes]:
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    connection = http.client.HTTPConnection(host, port)
    connection.request(method, path)
    response = connection.getresponse()
    headers = {key.lower(): value for key, value in response.getheaders()}
    body = response.read()
    connection.close()
    return response.status, headers, body


def _serve_in_thread(root: Path) -> tuple[dashboard.DashboardServer, threading.Thread]:
    server = dashboard.DashboardServer(dashboard.resolve_root(root), 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class _Cp1252Stdout:
    """Minimal Windows-like text stream whose binary buffer accepts UTF-8."""

    encoding = "cp1252"

    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, value: str) -> int:
        # The old text write path would fail here for non-ASCII task titles.
        encoded = value.encode(self.encoding)
        return len(encoded)

    def flush(self) -> None:
        self.buffer.flush()


def test_all_six_projections_are_deterministic_and_field_allowlisted(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    first = dashboard.build_snapshot(root)
    second = dashboard.build_snapshot(root)
    assert dashboard._json_text(first) == dashboard._json_text(second)
    assert set(first["data"]) == {"portfolio", "agents", "runs", "external_reviews", "worktrees", "clerk"}
    assert first["data"]["portfolio"]["data"]["directions"][0]["id"] == "example-direction"
    assert first["data"]["agents"]["data"]["agents"][0]["logical_identity"]
    assert first["data"]["runs"]["data"]["runs"][0]["run_id"] == "example-run"
    assert first["data"]["external_reviews"]["data"]["rounds"][0]["round_id"]
    assert first["data"]["worktrees"]["data"]["worktrees"][0]["worktree_ref"] == "wt-example"
    clerk_row = first["data"]["clerk"]["data"]["directions"][0]
    assert clerk_row == {
        "direction_id": "example-direction",
        "lifecycle": "ACTIVE",
        "stage": "CM",
        "reason": "OWNED_WORK",
        "owner_identity": "CM/example-direction/g1",
        "task_status": "active",
        "next_owner": None,
        "assignment_locator": ".codex/runtime/session-envelopes/example-direction/example.assignment.json",
        "return_locator": None,
        "recovery_kind": "REDELIVER_ASSIGNMENT",
    }

    forbidden = {
        "command",
        "cwd",
        "environment",
        "captured_variables",
        "responseText",
        "transcript",
        "pid",
        "execution_token",
        "canonical_absolute_path",
        "recipient_thread_id",
        "message",
    }

    def walk(value: Any) -> list[str]:
        if isinstance(value, dict):
            found: list[str] = []
            for key, child in value.items():
                if key in forbidden:
                    found.append(key)
                found.extend(walk(child))
            return found
        if isinstance(value, list):
            return [item for child in value for item in walk(child)]
        return []

    assert walk(first) == []


def test_service_is_loopback_static_allowlisted_and_read_only(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    before = hashlib.sha256((root / dashboard.REGISTRY_REL).read_bytes()).digest()
    server, thread = _serve_in_thread(root)
    try:
        assert server.server_address[0] == "127.0.0.1"
        for path in ("/", "/app.js", "/style.css"):
            status, headers, body = _request(server, "GET", path)
            assert status == 200
            assert body
            assert headers["content-length"] == str(len(body))
        status, _, body = _request(server, "GET", "/api/clerk")
        assert status == 200
        assert json.loads(body)["data"]["directions"][0]["stage"] == "CM"
        status, _, _ = _request(server, "GET", "/../scripts/hmasd_dashboard.py")
        assert status == 404
        status, _, _ = _request(server, "GET", "/%2e%2e/scripts/hmasd_dashboard.py")
        assert status == 404
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            status, headers, body = _request(server, method, "/api/snapshot")
            assert status == 405
            assert headers["allow"] == "GET"
            assert json.loads(body)["error"] == "read_only"
        assert hashlib.sha256((root / dashboard.REGISTRY_REL).read_bytes()).digest() == before
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_clerk_projection_age_is_visible_as_stale(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    path = root / dashboard.CLERK_LIVENESS_REL
    value = json.loads(path.read_text(encoding="utf-8"))
    value["observed_at"] = "2020-01-01T00:00:00Z"
    path.write_bytes(dashboard._json_bytes(value))

    clerk = dashboard.build_snapshot(root)["data"]["clerk"]

    assert clerk["status"] == "stale"
    assert clerk["warnings"] == ["stale:clerk_liveness_age"]


def test_optional_runtime_failures_are_isolated(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / dashboard.RUNTIME_AGENTS_REL).unlink()
    (root / dashboard.RUNTIME_WORKTREES_REL).write_text("{broken", encoding="utf-8")
    snapshot = dashboard.build_snapshot(root)
    # Codex task/process maps are disposable.  A fresh checkout without one
    # still has a healthy empty projection derived from durable state.
    assert snapshot["data"]["agents"]["status"] == "ok"
    assert snapshot["data"]["agents"]["warnings"] == []
    assert snapshot["data"]["worktrees"]["status"] == "invalid"
    assert snapshot["data"]["portfolio"]["status"] == "ok"
    assert snapshot["data"]["portfolio"]["data"]["directions"]


@pytest.mark.parametrize(
    ("relative", "section_names", "revision_key"),
    [
        (
            "docs/research/candidates/example-direction/workflow/research/state.json",
            ("portfolio",),
            "research_state:example-direction",
        ),
        (
            "docs/research/candidates/example-direction/workflow/engineering/state.json",
            ("portfolio", "agents"),
            "engineering_state:example-direction",
        ),
        (
            "docs/research/candidates/example-direction/workflow/external-review/index.json",
            ("portfolio", "external_reviews"),
            "external_review_index:example-direction",
        ),
        (dashboard.RUNTIME_AGENTS_REL, ("agents",), "runtime_agents"),
        (dashboard.RUNTIME_WORKTREES_REL, ("worktrees",), "runtime_worktrees"),
    ],
)
def test_source_change_retries_the_whole_snapshot_generation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    relative: str,
    section_names: tuple[str, ...],
    revision_key: str,
) -> None:
    root = fixture_root(tmp_path)
    state = _install_source_mutator(monkeypatch, root / relative, repeat=False)

    snapshot = dashboard.build_snapshot(root)

    assert state["mutations"] == 1
    for section_name in section_names:
        assert snapshot["data"][section_name]["revision_refs"][revision_key] == 2


@pytest.mark.parametrize(
    "relative",
    [
        dashboard.REGISTRY_REL,
        "docs/research/candidates/example-direction/workflow/research/state.json",
        "docs/research/candidates/example-direction/workflow/engineering/state.json",
        "docs/research/candidates/example-direction/workflow/external-review/index.json",
        dashboard.RUNTIME_AGENTS_REL,
        dashboard.RUNTIME_WORKTREES_REL,
    ],
)
def test_any_persistently_changing_source_returns_http_conflict_without_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    relative: str,
) -> None:
    root = fixture_root(tmp_path)
    state = _install_source_mutator(monkeypatch, root / relative, repeat=True)
    server, thread = _serve_in_thread(root)
    try:
        status, _, body = _request(server, "GET", "/api/snapshot")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    payload = json.loads(body)
    assert state["mutations"] >= dashboard.MAX_SNAPSHOT_ATTEMPTS
    assert status == 409
    assert payload["status"] == "stale"
    assert payload["data"] == {}


def test_valid_root_em_and_cm_runtime_rows_are_reconciled(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    runtime_path = root / dashboard.RUNTIME_AGENTS_REL
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["agents"] = [
        _runtime_agent("Root", "hmasd-root", "Root", "Root"),
        runtime["agents"][0],
        _runtime_agent("CM-example-direction", "hmasd-cm", "Root", "CMExampleDirection"),
    ]
    runtime_path.write_bytes(dashboard._json_bytes(runtime))

    agents = dashboard.build_snapshot(root)["data"]["agents"]

    assert agents["status"] == "ok"
    assert agents["warnings"] == []
    by_identity = {item["logical_identity"]: item for item in agents["data"]["agents"]}
    assert set(by_identity) == {"Root", "Portfolio", "EM-example-direction", "CM-example-direction"}
    assert by_identity["Root"]["agent_type"] == "hmasd-root"
    assert by_identity["Portfolio"]["agent_type"] == "hmasd-portfolio"
    assert by_identity["EM-example-direction"]["parent_identity"] == "Root"
    assert by_identity["EM-example-direction"]["direction_id"] == "example-direction"
    assert by_identity["CM-example-direction"]["agent_type"] == "hmasd-cm"
    assert by_identity["CM-example-direction"]["parent_identity"] == "Root"
    assert by_identity["CM-example-direction"]["phase"] == "SCOPING"


def test_legacy_omp_runtime_maps_remain_read_only_compatible(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / dashboard.RUNTIME_AGENTS_REL).unlink()
    (root / dashboard.RUNTIME_WORKTREES_REL).unlink()
    _copy_json("runtime_agents.json", root / dashboard.LEGACY_RUNTIME_AGENTS_REL)
    _copy_json("runtime_worktrees.json", root / dashboard.LEGACY_RUNTIME_WORKTREES_REL)

    snapshot = dashboard.build_snapshot(root)

    assert snapshot["data"]["agents"]["status"] == "ok"
    assert snapshot["data"]["worktrees"]["status"] == "ok"
    assert snapshot["data"]["agents"]["revision_refs"]["runtime_agents"] == 1
    assert snapshot["data"]["worktrees"]["revision_refs"]["runtime_worktrees"] == 1


def test_codex_task_map_projects_top_level_tasks_and_direct_leaves(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    tasks_path = root / dashboard.RUNTIME_TASKS_REL
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_bytes(
        dashboard._json_bytes(
            {
                "schema_version": 1,
                "revision": 3,
                "updated_at": "2026-08-24T00:00:03Z",
                "writer": "Root",
                "tasks": [
                    {
                        "logical_identity": "Portfolio",
                        "kind": "portfolio",
                        "generation": 1,
                        "task_title": "HMASD Portfolio",
                        "thread_id": "secret-thread",
                        "host_id": "secret-host",
                        "last_cursor": "secret-cursor",
                        "project_root": str(root),
                        "lifecycle": "IDLE",
                    },
                    {
                        "logical_identity": "Implementer-example-direction",
                        "kind": "implementer",
                        "generation": 1,
                        "task_title": "Candidate implementation",
                        "parent_identity": "CM-example-direction",
                        "lifecycle": "RUNNING",
                    },
                ],
            }
        )
    )

    agents = dashboard.build_snapshot(root)["data"]["agents"]

    assert agents["status"] == "ok"
    assert agents["revision_refs"]["runtime_tasks"] == 3
    by_identity = {item["logical_identity"]: item for item in agents["data"]["agents"]}
    assert by_identity["Portfolio"]["task_level"] == "top-level"
    assert by_identity["Portfolio"]["job_name"] == "HMASD Portfolio"
    assert by_identity["Implementer-example-direction"]["task_level"] == "leaf"
    assert by_identity["Implementer-example-direction"]["parent_identity"] == "CM-example-direction"
    assert "thread_id" not in dashboard._json_text(agents)
    assert "secret-thread" not in dashboard._json_text(agents)
    assert "project_root" not in dashboard._json_text(agents)


def test_runtime_manager_generation_mismatch_remains_stale(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    runtime_path = root / dashboard.RUNTIME_AGENTS_REL
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["agents"].append(
        _runtime_agent(
            "CM-example-direction",
            "hmasd-cm",
            "Root",
            "CMExampleDirection",
            generation=2,
        )
    )
    runtime_path.write_bytes(dashboard._json_bytes(runtime))

    agents = dashboard.build_snapshot(root)["data"]["agents"]

    assert agents["status"] == "stale"
    assert "stale:agent_generation:CM-example-direction" in agents["warnings"]


def test_snapshot_cli_is_deterministic_and_invalid_root_has_exit_two(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    command = [sys.executable, str(ROOT / "scripts" / "hmasd_dashboard.py"), "snapshot", "--root", str(root)]
    first = subprocess.run(command, check=False, capture_output=True, text=True)
    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert json.loads(first.stdout)["schema_version"] == 1

    invalid = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "hmasd_dashboard.py"), "snapshot", "--root", str(tmp_path / "missing")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 2


def test_snapshot_cli_writes_utf8_bytes_for_non_ascii_task_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = fixture_root(tmp_path)
    task_title = "中文运行任务"
    tasks_path = root / dashboard.RUNTIME_TASKS_REL
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_bytes(
        dashboard._json_bytes(
            {
                "schema_version": 1,
                "revision": 1,
                "updated_at": "2026-08-24T00:00:01Z",
                "writer": "Root",
                "tasks": [
                    {
                        "logical_identity": "CM-example-direction",
                        "kind": "cm",
                        "generation": 1,
                        "task_title": task_title,
                        "lifecycle": "RUNNING",
                    }
                ],
            }
        )
    )

    stdout = _Cp1252Stdout()
    monkeypatch.setattr(sys, "stdout", stdout)

    result = dashboard.main(
        ["snapshot", "--root", str(root)]
    )

    assert result == 0
    raw = stdout.buffer.getvalue()
    assert task_title.encode("utf-8") in raw
    payload = json.loads(raw.decode("utf-8"))
    agents = payload["data"]["agents"]["data"]["agents"]
    projected = next(
        item for item in agents if item["logical_identity"] == "CM-example-direction"
    )
    assert projected["job_name"] == task_title
