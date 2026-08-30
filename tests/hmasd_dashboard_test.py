"""Focused read-only Dashboard contract tests.

These tests use the Phase-0 JSON fixtures as isolated authoritative files.  The
service tests intentionally exercise the real ThreadingHTTPServer rather than a
mock request adapter.
"""

from __future__ import annotations

import hashlib
import http.client
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
    agents = root / ".omp" / "agents"
    agents.mkdir()
    (agents / "hmasd-em.md").write_text(
        "---\nname: hmasd-em\nmodel: openai-codex/gpt-test-em\nthinking-level: max\n---\n",
        encoding="utf-8",
    )
    (agents / "hmasd-cm.md").write_text(
        "---\nname: hmasd-cm\nmodel: openai-codex/gpt-test-cm\nthinking-level: high\n---\n",
        encoding="utf-8",
    )
    _copy_json("portfolio_registry.json", root / dashboard.REGISTRY_REL)
    _copy_json("runtime_agents.json", root / dashboard.RUNTIME_AGENTS_REL)
    _copy_json("runtime_worktrees.json", root / dashboard.RUNTIME_WORKTREES_REL)
    browser_assignments = root / dashboard.RUNTIME_BROWSER_ASSIGNMENTS_REL
    browser_assignments.parent.mkdir(parents=True, exist_ok=True)
    browser_assignments.write_bytes(
        dashboard._json_bytes(
            {
                "assignments": [],
                "revision": 1,
                "schema_version": 2,
                "updated_at": "2026-08-24T00:00:00Z",
                "writer": "Root",
            }
        )
    )
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


def test_all_five_projections_are_deterministic_and_field_allowlisted(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    first = dashboard.build_snapshot(root)
    second = dashboard.build_snapshot(root)
    assert dashboard._json_text(first) == dashboard._json_text(second)
    assert set(first["data"]) == {"portfolio", "agents", "runs", "external_reviews", "worktrees"}
    portfolio = first["data"]["portfolio"]["data"]
    assert portfolio["directions"][0]["id"] == "example-direction"
    assert portfolio["directions"][0]["current_route"]["owner"] == "CM"
    assert portfolio["summary"] == {
        "total": 1,
        "lifecycle_counts": {"REGISTERED": 1},
        "owner_counts": {"CM": 1},
        "actionable_count": 1,
        "queued_count": 0,
    }
    assert first["data"]["agents"]["data"]["role_configs"] == [
        {
            "role": "hmasd-cm",
            "model": "openai-codex/gpt-test-cm",
            "thinking_level": "high",
            "definition_path": ".omp/agents/hmasd-cm.md",
        },
        {
            "role": "hmasd-em",
            "model": "openai-codex/gpt-test-em",
            "thinking_level": "max",
            "definition_path": ".omp/agents/hmasd-em.md",
        },
    ]
    assert first["data"]["agents"]["data"]["transport_assignments"] == []
    assert (
        first["data"]["agents"]["revision_refs"]["runtime_browser_assignments"]
        == 1
    )
    cm_agent = next(
        agent
        for agent in first["data"]["agents"]["data"]["agents"]
        if agent["agent_type"] == "hmasd-cm"
    )
    assert cm_agent["configured_model"] == "openai-codex/gpt-test-cm"
    assert cm_agent["thinking_level"] == "high"
    assert first["data"]["runs"]["data"]["runs"][0]["run_id"] == "example-run"
    assert first["data"]["external_reviews"]["data"]["rounds"][0]["round_id"]
    assert first["data"]["worktrees"]["data"]["worktrees"][0]["worktree_ref"] == "wt-example"

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
        "prompt",
        "prompt_body",
        "prompt_path",
        "provider_prompt",
        "secret",
        "session_ref",
        "runtime_ref",
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

def test_external_provider_projection_uses_only_minimal_receipt_facts(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    root.mkdir()
    operation_path = (
        "docs/external-review/directions/example-direction/round-one/"
        "pro_innovator/chatgpt/operation_ref.json"
    )
    response_path = (
        "docs/external-review/directions/example-direction/round-one/"
        "pro_innovator/chatgpt/response.md"
    )
    digests = {operation_path: "a" * 64, response_path: "b" * 64}

    class Sources:
        @staticmethod
        def read_digest(path: str) -> str | None:
            return digests.get(path)

    warnings: list[str] = []
    projected = dashboard._safe_provider(
        {
            "provider": "chatgpt",
            "product_model": "GPT-5.6 Sol",
            "reasoning_effort": "Pro",
            "target_conversation_url": None,
            "target_conversation_id": None,
            "prompt_ref": {"path": "prompt.md", "sha256": "c" * 64},
            "response_path": response_path,
            "operation_id": "operation-one",
            "idempotency_key": "idempotency-one",
            "request_fingerprint": "d" * 64,
            "stable_key": "stable-one",
            "operation_ref": {"path": operation_path, "sha256": "a" * 64},
            "created_at": 1788000000000,
            "updated_at": 1788000002000,
            "send_attempted": True,
            "send_attempted_at": 1788000001000,
            "observed_conversation_url": "https://chatgpt.com/c/conversation-one",
            "observed_conversation_id": "conversation-one",
            "provider_user_message_id": "user-one",
            "provider_assistant_message_id": "assistant-one",
            "archive": {
                "path": response_path,
                "sha256": "b" * 64,
                "size_bytes": 5,
                "projection": "exact",
                "verified_at": 1788000000000,
            },
            "error": None,
        },
        root,
        warnings,
        "round-one",
        "pro_innovator",
        Sources(),
    )

    assert projected is not None
    assert projected["review_stage"] == "pro_innovator"
    assert projected["product_model"] == "GPT-5.6 Sol"
    assert projected["reasoning_effort"] == "Pro"
    assert projected["send_attempted"] is True
    assert projected["provider_user_message_id"] == "user-one"
    assert projected["provider_assistant_message_id"] == "assistant-one"
    assert projected["operation_receipt"]["path"] == operation_path
    assert projected["archive"]["path"] == response_path
    assert "phase" not in projected
    assert "commitment" not in projected
    assert warnings == []


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



def test_portfolio_semantics_accept_more_than_eight_active_queues() -> None:
    directions = [
        {"id": f"direction-{index}", "lifecycle": "ACTIVE", "dependencies": []}
        for index in range(9)
    ]
    assert dashboard._semantic_valid("portfolio_registry", {"directions": directions})

def test_parked_direction_requires_and_projects_reactivation_condition(
    tmp_path: Path,
) -> None:
    root = fixture_root(tmp_path)
    registry_path = root / dashboard.REGISTRY_REL
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    direction = registry["directions"][0]
    direction["lifecycle"] = "PARKED"
    direction["reactivation_condition_ref"] = {
        "path": "docs/research/portfolio/PORTFOLIO.md",
        "heading": "Reactivation condition for example-direction",
        "sha256": "c" * 64,
    }
    registry_path.write_bytes(dashboard._json_bytes(registry))

    portfolio = dashboard.build_snapshot(root)["data"]["portfolio"]

    assert portfolio["status"] == "ok"
    assert portfolio["data"]["summary"]["lifecycle_counts"] == {"PARKED": 1}
    parked = portfolio["data"]["directions"][0]
    assert parked["lifecycle"] == "PARKED"
    assert parked["reactivation_condition_ref"] == direction["reactivation_condition_ref"]


def test_parked_direction_without_reactivation_condition_is_semantically_invalid() -> None:
    assert not dashboard._semantic_valid(
        "portfolio_registry",
        {
            "directions": [
                {
                    "id": "parked-direction",
                    "lifecycle": "PARKED",
                    "dependencies": [],
                    "reactivation_condition_ref": None,
                }
            ]
        },
    )


def test_optional_runtime_failures_are_isolated(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / dashboard.RUNTIME_AGENTS_REL).unlink()
    (root / dashboard.RUNTIME_WORKTREES_REL).write_text("{broken", encoding="utf-8")
    snapshot = dashboard.build_snapshot(root)
    assert snapshot["data"]["agents"]["status"] == "missing"
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
    assert set(by_identity) == {"Root", "EM-example-direction", "CM-example-direction"}
    assert by_identity["Root"]["agent_type"] == "hmasd-root"
    assert by_identity["EM-example-direction"]["parent_identity"] == "Root"
    assert by_identity["EM-example-direction"]["direction_id"] == "example-direction"
    assert by_identity["CM-example-direction"]["agent_type"] == "hmasd-cm"
    assert by_identity["CM-example-direction"]["parent_identity"] == "Root"
    assert by_identity["CM-example-direction"]["phase"] == "SCOPING"

def test_browser_transport_runtime_row_is_reconciled_without_sensitive_fields(
    tmp_path: Path,
) -> None:
    root = fixture_root(tmp_path)
    runtime_path = root / dashboard.RUNTIME_AGENTS_REL
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["agents"].append(
        _runtime_agent(
            "BrowserTransport",
            "hmasd-browser-transport",
            "Root",
            "BrowserTransport",
        )
    )
    runtime_path.write_bytes(dashboard._json_bytes(runtime))

    agents = dashboard.build_snapshot(root)["data"]["agents"]

    assert agents["status"] == "ok"
    assert agents["warnings"] == []
    browser = next(
        item
        for item in agents["data"]["agents"]
        if item["logical_identity"] == "BrowserTransport"
    )
    assert browser["agent_type"] == "hmasd-browser-transport"
    assert browser["parent_identity"] == "Root"
    assert browser["lifecycle"] == "RUNNING"
    assert {
        "prompt",
        "prompt_body",
        "prompt_path",
        "provider_prompt",
        "secret",
        "session_ref",
        "runtime_ref",
    }.isdisjoint(browser)


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
