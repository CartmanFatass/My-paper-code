"""Focused read-only Dashboard contract tests.

These tests use the Phase-0 JSON fixtures as isolated authoritative files.  The
service tests intentionally exercise the real ThreadingHTTPServer rather than a
mock request adapter.
"""

from __future__ import annotations

import hashlib
import http.client
import json
from datetime import datetime, timezone
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
    clerk_path = root / ".codex/runtime/clerk-liveness.json"
    clerk_path.parent.mkdir(parents=True, exist_ok=True)
    clerk_path.write_bytes(
        dashboard._json_bytes(
            {
                "schema_version": 1,
                "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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


def test_v2_projections_are_deterministic_and_field_allowlisted(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    first = dashboard.build_snapshot(root)
    second = dashboard.build_snapshot(root)
    assert dashboard._json_text(first) == dashboard._json_text(second)
    assert set(first["data"]) == {"portfolio", "runs", "external_reviews", "clerk"}
    assert first["data"]["portfolio"]["data"]["directions"][0]["id"] == "example-direction"
    assert first["data"]["runs"]["data"]["runs"][0]["run_id"] == "example-run"
    assert first["data"]["external_reviews"]["data"]["rounds"][0]["round_id"]
    clerk_row = first["data"]["clerk"]["data"]["directions"][0]
    assert clerk_row["owner_stage"] == "CM"
    assert clerk_row["observed_at"] != "UNOBSERVED"

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


def test_dashboard_has_no_retired_runtime_projection_surface() -> None:
    source = (ROOT / "scripts" / "hmasd_dashboard.py").read_text(encoding="utf-8")
    for retired in ("runtime_agents", "runtime_tasks", "runtime_worktrees", "agent_result", ".omp/runtime"):
        assert retired not in source


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
        assert json.loads(body)["data"]["directions"][0]["owner_stage"] == "CM"
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


def test_clerk_v2_projection_keeps_provenance_and_never_infers_transport(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    liveness_path = root / dashboard.CLERK_LIVENESS_REL
    liveness = json.loads(liveness_path.read_text(encoding="utf-8"))
    liveness["directions"] = []
    liveness_path.write_bytes(dashboard._json_bytes(liveness))

    clerk = dashboard.build_projection(root, "clerk")
    row = clerk["data"]["directions"][0]

    assert row["lifecycle"] == "REGISTERED"
    assert row["owner_stage"] == "TERMINAL"
    assert row["native_task_id"] == "UNKNOWN"
    assert row["native_task_status"] == "UNOBSERVED"
    assert row["observed_at"] == "UNOBSERVED"
    assert row["assignment_id"] == "UNKNOWN"
    assert row["return_id"] == "UNKNOWN"
    assert row["delivery_state"] == "UNOBSERVED"
    assert row["control_release_adoption"] == "UNOBSERVED"
    assert row["registry_revision"] == 1
    assert row["research_state_revision"] == 1
    assert row["engineering_state_revision"] == 1
    assert row["projection_age_seconds"] == "UNOBSERVED"
    assert row["defect"] is None


def test_clerk_v2_observation_preserves_native_provenance_and_stage(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    registry_path = root / dashboard.REGISTRY_REL
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["directions"][0]["lifecycle"] = "ACTIVE"
    registry_path.write_bytes(dashboard._json_bytes(registry))
    liveness_path = root / dashboard.CLERK_LIVENESS_REL
    liveness = json.loads(liveness_path.read_text(encoding="utf-8"))
    liveness["directions"][0].update(
        stage="CM_EXPERIMENT",
        owner_stage="CM_EXPERIMENT",
        native_task_id="native-cm-thread",
        native_task_status="running",
        assignment_id="assignment-17",
        return_id="UNKNOWN",
        delivery_state="DELIVERED",
        control_release_adoption="ADOPTED",
        next_event="observe the frozen command",
    )
    liveness_path.write_bytes(dashboard._json_bytes(liveness))

    row = dashboard.build_projection(root, "clerk")["data"]["directions"][0]

    assert row["owner_stage"] == "CM_EXPERIMENT"
    assert row["native_task_id"] == "native-cm-thread"
    assert row["native_task_status"] == "running"
    assert row["assignment_id"] == "assignment-17"
    assert row["delivery_state"] == "DELIVERED"
    assert row["control_release_adoption"] == "ADOPTED"
    assert row["next_event"] == "observe the frozen command"


def test_clerk_v2_defects_are_precise_and_do_not_use_runtime_task_maps(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    registry_path = root / dashboard.REGISTRY_REL
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["directions"][0]["lifecycle"] = "CLOSED"
    registry_path.write_bytes(dashboard._json_bytes(registry))
    tasks_path = root / ".codex/runtime/tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text('{"secret": "must not be read"}', encoding="utf-8")

    row = dashboard.build_projection(root, "clerk")["data"]["directions"][0]

    assert row["owner_stage"] == "DEFECT"
    assert row["defect"] == "CLOSED_WITH_INFLIGHT"
    assert "secret" not in dashboard._json_text(row)


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
            ("portfolio", "clerk"),
            "engineering_state:example-direction",
        ),
        (
            "docs/research/candidates/example-direction/workflow/external-review/index.json",
            ("portfolio", "external_reviews"),
            "external_review_index:example-direction",
        ),
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


def test_snapshot_cli_is_deterministic_and_invalid_root_has_exit_two(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    command = [sys.executable, str(ROOT / "scripts" / "hmasd_dashboard.py"), "snapshot", "--root", str(root)]
    first = subprocess.run(command, check=False, capture_output=True, text=True)
    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == second.returncode == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["schema_version"] == second_payload["schema_version"] == 1
    assert first_payload["data"]["clerk"]["data"]["directions"][0]["observed_at"] == second_payload["data"]["clerk"]["data"]["directions"][0]["observed_at"]

    invalid = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "hmasd_dashboard.py"), "snapshot", "--root", str(tmp_path / "missing")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 2
