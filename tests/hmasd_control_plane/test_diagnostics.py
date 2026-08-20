from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from tools.hmasd_control_plane import diagnostics
from tools.hmasd_control_plane.diagnostics import (
    COMPONENTS,
    collect_doctor,
    collect_incidents,
    diagnostic_exit_code,
)


def _semantic_db(root: Path, *, open_obligation: bool = False) -> Path:
    path = root / "runtime/codex-semantic-mvp/state.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE workflows (
          workflow_id TEXT PRIMARY KEY, state TEXT, state_version INTEGER,
          created_at TEXT, updated_at TEXT
        );
        CREATE TABLE tasks (
          workflow_id TEXT, task_id TEXT, lifecycle TEXT, created_at TEXT,
          returned_at TEXT
        );
        CREATE TABLE obligations (
          obligation_id TEXT PRIMARY KEY, workflow_id TEXT, kind TEXT, owner TEXT,
          state TEXT, created_at TEXT, resolved_at TEXT
        );
        CREATE TABLE events (seq INTEGER PRIMARY KEY, created_at TEXT);
        CREATE TABLE reports (report_id TEXT PRIMARY KEY, created_at TEXT);
        INSERT INTO workflows VALUES
          ('wf-1','ACTIVE',1,'2026-08-20T00:00:00Z','2026-08-20T00:00:00Z');
        """
    )
    if open_obligation:
        connection.execute(
            "INSERT INTO obligations VALUES (?,?,?,?,?,?,?)",
            (
                "obl-1",
                "wf-1",
                "REPORT_INTAKE_REQUIRED",
                "/root",
                "OPEN",
                "2026-08-20T00:00:00Z",
                None,
            ),
        )
        connection.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?)",
            ("wf-1", "task-1", "RETURNED_UNTYPED", "2026-08-20T00:00:00Z", None),
        )
    connection.commit()
    connection.close()
    return path


def _supervisor_db(
    path: Path, *, incident: bool = False, resolved_incident: bool = False
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT);
        CREATE TABLE managed_turn_intents (
          turn_intent_id TEXT PRIMARY KEY, submission_state TEXT,
          prepared_at TEXT, incident_json TEXT
        );
        CREATE TABLE wake_batches (
          wake_batch_id TEXT PRIMARY KEY, state TEXT, prepared_at TEXT,
          incident_json TEXT
        );
        CREATE TABLE app_server_effects (
          effect_id TEXT PRIMARY KEY, state TEXT, prepared_at TEXT,
          incident_json TEXT
        );
        INSERT INTO schema_meta VALUES (7,'2026-08-20T00:00:00Z');
        """
    )
    if incident:
        connection.execute(
            "INSERT INTO app_server_effects VALUES (?,?,?,?)",
            ("effect-1", "INCIDENT", "2026-08-20T00:00:00Z", '{"secret":"not indexed"}'),
        )
    if resolved_incident:
        connection.execute(
            "INSERT INTO app_server_effects VALUES (?,?,?,?)",
            (
                "effect-resolved",
                "OPERATOR_RESOLVED",
                "2026-08-20T00:00:00Z",
                '{"secret":"not indexed"}',
            ),
        )
    connection.commit()
    connection.close()
    return path


def _agentify_state(path: Path, *, ambiguous: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    operation = {
        "status": "BLOCKED" if ambiguous else "COMPLETE",
        "terminalState": "SUBMITTED_UNVERIFIED" if ambiguous else "NATURAL_COMPLETION_VERIFIED",
        "failureStage": "send_occurred_or_uncertain" if ambiguous else None,
        "sendActionCount": 1,
        "sendCount": 0,
        "createdAt": 1787184000000,
        "updatedAt": 1787184001000,
        "promptTextModel": "PROVIDER PROMPT MUST NOT APPEAR",
        "responseText": "ASSISTANT RESPONSE MUST NOT APPEAR",
        "provider_prompt": "PROVIDER PROMPT ALIAS MUST NOT APPEAR",
        "assistant_response_text": "ASSISTANT RESPONSE ALIAS MUST NOT APPEAR",
        "renderedText": "RENDERED PROVIDER CONTENT MUST NOT APPEAR",
    }
    if not ambiguous:
        operation["userMessageId"] = "user-1"
    path.write_text(
        json.dumps({"schemaVersion": 2, "operations": {"operation-safe-key": operation}}),
        encoding="utf-8",
    )
    return path


def _events(path: Path, rows: list[dict[str, object]] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = rows or [{"timestamp": "2026-08-20T00:00:00Z", "event": "ordinary"}]
    path.write_text("".join(json.dumps(row) + "\n" for row in payload), encoding="utf-8")
    return path


def _long_effect(root: Path, *, terminal: bool) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    output_path = root.parent / f"{root.name}-result.json"
    (root / "experiment.json").write_text(
        json.dumps(
            {
                "schema": "HMASD_LONG_EFFECT_V1",
                "experiment_id": "experiment-1",
                "component": "canary",
                "metadata": {"direction_id": None},
                "output_refs": [
                    {"name": "secret-domain-output", "path": str(output_path)}
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "owner.json").write_text(
        json.dumps({"owner_pid": 123, "acquired_at": "2026-08-20T00:00:00Z"}),
        encoding="utf-8",
    )
    (root / "stdout.log").write_text("SCIENTIFIC RESULT 99.999\n", encoding="utf-8")
    (root / "stderr.log").write_text("SENSITIVE STDERR\n", encoding="utf-8")
    output_path.write_text('{"scientific_value":99.999}', encoding="utf-8")
    if terminal:
        (root / "terminal.json").write_text(
            json.dumps({"phase": "EXITED", "exit_code": 0}), encoding="utf-8"
        )
    return root


@pytest.fixture
def isolated_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    supervisor_home = tmp_path / "external-supervisor"
    agentify_home = tmp_path / "external-agentify"
    monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(supervisor_home))
    monkeypatch.setenv("AGENTIFY_DESKTOP_STATE_DIR", str(agentify_home))
    semantic = _semantic_db(tmp_path)
    supervisor = _supervisor_db(supervisor_home / "state.sqlite3")
    agentify = _agentify_state(agentify_home / "review-transport.json")
    events = _events(
        tmp_path
        / "docs/research/workflow-runs/2026-08-11_five-round-research-team/events_v2.jsonl"
    )
    long_effect = _long_effect(tmp_path / "runtime/test-long-effects/run-1", terminal=True)
    (tmp_path / "runtime/hmasd-control-plane/mcp-instances").mkdir(parents=True)
    return {
        "repo": tmp_path,
        "semantic": semantic,
        "supervisor": supervisor,
        "agentify": agentify,
        "events": events,
        "long_effect": long_effect,
    }


def test_all_sources_are_byte_immutable(isolated_sources: dict[str, Path]) -> None:
    paths = [
        isolated_sources["semantic"],
        isolated_sources["supervisor"],
        isolated_sources["agentify"],
        isolated_sources["events"],
        isolated_sources["long_effect"] / "experiment.json",
        isolated_sources["long_effect"] / "owner.json",
        isolated_sources["long_effect"] / "terminal.json",
        isolated_sources["long_effect"] / "stdout.log",
        isolated_sources["long_effect"].parent
        / f"{isolated_sources['long_effect'].name}-result.json",
    ]
    before = {path: path.read_bytes() for path in paths}

    doctor, exit_code = collect_doctor(
        isolated_sources["repo"], experiment_roots=[isolated_sources["long_effect"]]
    )
    incidents, incident_exit = collect_incidents(
        isolated_sources["repo"], experiment_roots=[isolated_sources["long_effect"]]
    )

    assert doctor["schema"] == "HMASD_CONTROL_PLANE_DOCTOR_V1"
    assert set(doctor) == {"schema", "generated_at", "status", "sources", "counters", "findings"}
    assert doctor["status"] == "OK"
    assert exit_code == incident_exit == diagnostic_exit_code(doctor) == 0
    assert incidents == []
    assert before == {path: path.read_bytes() for path in paths}


@pytest.mark.parametrize("component", sorted(COMPONENTS))
def test_missing_source_is_unavailable_not_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(tmp_path / "missing-supervisor"))
    monkeypatch.setenv("AGENTIFY_DESKTOP_STATE_DIR", str(tmp_path / "missing-agentify"))
    doctor, exit_code = collect_doctor(
        tmp_path,
        component=component,
        experiment_roots=[tmp_path / "missing-long-effect"],
    )
    assert doctor["status"] == "UNAVAILABLE"
    assert exit_code == 2
    assert doctor["findings"][0]["severity"] == "ERROR"
    assert "no domain conclusion follows" in doctor["findings"][0]["observed_fact"]


@pytest.mark.parametrize("component,relative", [
    ("semantic", "runtime/codex-semantic-mvp/state.sqlite3"),
    ("supervisor", "state.sqlite3"),
])
def test_corrupt_sqlite_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    component: str,
    relative: str,
) -> None:
    if component == "semantic":
        path = tmp_path / relative
    else:
        home = tmp_path / "supervisor"
        monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(home))
        path = home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not sqlite")
    before = path.read_bytes()
    doctor, exit_code = collect_doctor(tmp_path, component=component)
    assert doctor["status"] == "UNAVAILABLE"
    assert exit_code == 2
    assert path.read_bytes() == before


def test_incomplete_supervisor_schema_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "supervisor"
    monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(home))
    path = home / "state.sqlite3"
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE schema_meta(version INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO schema_meta VALUES (7)")
    connection.commit()
    connection.close()

    doctor, exit_code = collect_doctor(tmp_path, component="supervisor")
    assert exit_code == 2
    assert doctor["status"] == "UNAVAILABLE"


def test_locked_sqlite_produces_stable_finding(tmp_path: Path) -> None:
    path = _semantic_db(tmp_path)
    writer = sqlite3.connect(path, timeout=0)
    writer.execute("PRAGMA locking_mode=EXCLUSIVE")
    writer.execute("BEGIN EXCLUSIVE")
    try:
        doctor, exit_code = collect_doctor(tmp_path, component="semantic")
    finally:
        writer.rollback()
        writer.close()
    # SQLite builds differ in whether an existing EXCLUSIVE transaction blocks a
    # read-only connection; either valid observation must be deterministic.
    if exit_code == 2:
        assert doctor["status"] == "UNAVAILABLE"
        assert doctor["findings"][0]["observed_fact"].endswith(
            "; no domain conclusion follows."
        )
    else:
        assert exit_code == 0
        assert doctor["status"] == "OK"


def test_sqlite_lock_error_is_stable_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _semantic_db(tmp_path)
    before = path.read_bytes()

    def locked(_path: Path):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(diagnostics, "_connect_read_only", locked)
    first, first_code = collect_doctor(tmp_path, component="semantic")
    second, second_code = collect_doctor(tmp_path, component="semantic")

    assert first_code == second_code == 2
    assert first["status"] == second["status"] == "UNAVAILABLE"
    assert first["findings"][0]["finding_id"] == second["findings"][0]["finding_id"]
    assert path.read_bytes() == before


def test_open_semantic_debt_is_locatable_without_domain_inference(tmp_path: Path) -> None:
    _semantic_db(tmp_path, open_obligation=True)
    doctor, exit_code = collect_doctor(tmp_path, component="semantic")
    incidents, incident_exit = collect_incidents(tmp_path, component="semantic")
    assert exit_code == incident_exit == 1
    assert doctor["counters"]["semantic_open_obligations"] == 1
    assert doctor["counters"]["semantic_open_tasks"] == 1
    obligation = next(item for item in incidents if "/obligation/" in item["exact_object"])
    assert obligation["owner"] == "/root"
    assert "does not imply a scientific pause or failure" in obligation["observed_fact"]
    assert obligation["evidence_refs"] == [
        f"sqlite-ro://{(tmp_path / 'runtime/codex-semantic-mvp/state.sqlite3').resolve()}#obligations/obl-1"
    ]


def test_ambiguous_agentify_operation_is_observe_only_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "agentify"
    monkeypatch.setenv("AGENTIFY_DESKTOP_STATE_DIR", str(state))
    _agentify_state(state / "review-transport.json", ambiguous=True)
    doctor, exit_code = collect_doctor(tmp_path, component="agentify")
    incidents, _ = collect_incidents(tmp_path, component="agentify")
    encoded = json.dumps({"doctor": doctor, "incidents": incidents})
    assert exit_code == 1
    assert len(incidents) == 1
    assert incidents[0]["exact_object"] == "operation-safe-key"
    assert incidents[0]["local_fence"] == "Observe only; never resend this exact operation identity."
    assert "PROVIDER PROMPT MUST NOT APPEAR" not in encoded
    assert "ASSISTANT RESPONSE MUST NOT APPEAR" not in encoded
    assert "PROMPT ALIAS" not in encoded
    assert "RESPONSE ALIAS" not in encoded
    assert "RENDERED PROVIDER CONTENT" not in encoded


def test_verified_agentify_completion_is_not_reopened_by_stale_failure_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "agentify"
    monkeypatch.setenv("AGENTIFY_DESKTOP_STATE_DIR", str(state))
    path = _agentify_state(state / "review-transport.json", ambiguous=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["operations"]["operation-safe-key"]["failureStage"] = (
        "send_occurred_or_uncertain"
    )
    path.write_text(json.dumps(payload), encoding="utf-8")

    incidents, exit_code = collect_incidents(tmp_path, component="agentify")
    assert exit_code == 0
    assert incidents == []


def test_missing_long_effect_terminal_is_evidence_only_and_outputs_are_not_read(
    tmp_path: Path,
) -> None:
    run_root = _long_effect(tmp_path / "runs/run-1", terminal=False)
    doctor, exit_code = collect_doctor(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )
    incidents, _ = collect_incidents(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )
    encoded = json.dumps({"doctor": doctor, "incidents": incidents})
    assert exit_code == 1
    assert len(incidents) == 1
    assert incidents[0]["exact_object"].startswith("experiment-1@")
    assert str((run_root / "terminal.json").resolve()) in incidents[0]["evidence_refs"]
    assert "no domain outcome is inferred" in incidents[0]["observed_fact"]
    assert "SCIENTIFIC RESULT" not in encoded
    assert "99.999" not in encoded
    assert "SENSITIVE STDERR" not in encoded


def test_long_effect_since_filter_uses_owner_acquired_at(tmp_path: Path) -> None:
    run_root = _long_effect(tmp_path / "runs/run-1", terminal=False)
    before, _ = collect_incidents(
        tmp_path,
        component="long-effect",
        since="2026-08-19T00:00:00Z",
        experiment_roots=[run_root],
    )
    after, _ = collect_incidents(
        tmp_path,
        component="long-effect",
        since="2026-08-21T00:00:00Z",
        experiment_roots=[run_root],
    )
    assert len(before) == 1
    assert after == []


def test_long_effect_experiment_without_owner_is_partial_envelope(tmp_path: Path) -> None:
    run_root = _long_effect(tmp_path / "runs/run-1", terminal=False)
    (run_root / "owner.json").unlink()

    doctor, exit_code = collect_doctor(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )
    incidents, _ = collect_incidents(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )

    assert exit_code == 1
    assert doctor["counters"]["long_effect_partial_envelopes"] == 1
    assert len(incidents) == 1
    assert "owner.json" in incidents[0]["observed_fact"]
    assert "terminal.json" in incidents[0]["observed_fact"]


def test_long_effect_missing_log_is_partial_envelope(tmp_path: Path) -> None:
    run_root = _long_effect(tmp_path / "runs/run-1", terminal=True)
    (run_root / "stderr.log").unlink()

    doctor, exit_code = collect_doctor(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )
    incidents, _ = collect_incidents(
        tmp_path, component="long-effect", experiment_roots=[run_root]
    )

    assert exit_code == 1
    assert doctor["counters"]["long_effect_partial_envelopes"] == 1
    assert len(incidents) == 1
    assert "stderr.log" in incidents[0]["observed_fact"]


def test_explicit_research_incidents_deduplicate_with_stable_id(tmp_path: Path) -> None:
    events = tmp_path / "docs/research/workflow-runs/2026-08-11_five-round-research-team/events_v2.jsonl"
    _events(
        events,
        [
            {
                "timestamp": "2026-08-20T00:00:00Z",
                "incident_id": "native-incident-1",
                "component": "research-events",
                "exact_object": "transport/object-1",
                "observed_fact": "Explicit mechanical incident.",
                "local_fence": "No resend for operation-1.",
                "owner": "/root",
                "provider_prompt": "DO NOT INDEX",
            },
            {
                "timestamp": "2026-08-20T01:00:00Z",
                "incident_id": "native-incident-1",
                "component": "research-events",
                "exact_object": "transport/object-1",
                "observed_fact": "Explicit mechanical incident.",
                "local_fence": "No resend for operation-1.",
                "owner": "/root",
                "assistant_response": "DO NOT INDEX EITHER",
            },
        ],
    )
    first, first_exit = collect_incidents(tmp_path, component="research-events")
    second, second_exit = collect_incidents(tmp_path, component="research-events")
    assert first_exit == second_exit == 0
    assert first == second
    assert len(first) == 1
    assert first[0]["incident_id"] == "native-incident-1"
    assert len(first[0]["evidence_refs"]) == 2
    encoded = json.dumps(first)
    assert "DO NOT INDEX" not in encoded


def test_colliding_native_incident_ids_are_stably_disambiguated(tmp_path: Path) -> None:
    events = tmp_path / "docs/research/workflow-runs/2026-08-11_five-round-research-team/events_v2.jsonl"
    rows = [
        {
            "timestamp": "2026-08-20T00:00:00Z",
            "incident_id": "duplicate-native-id",
            "component": "research-events",
            "exact_object": object_id,
            "observed_fact": "Explicit mechanical incident.",
            "owner": "/root",
        }
        for object_id in ("object-a", "object-b")
    ]
    _events(events, rows)

    first, first_exit = collect_incidents(tmp_path, component="research-events")
    second, second_exit = collect_incidents(tmp_path, component="research-events")
    assert first_exit == second_exit == 0
    assert first == second
    assert len(first) == 2
    assert len({item["incident_id"] for item in first}) == 2


def test_supervisor_incident_indexes_only_safe_columns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "supervisor"
    monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(home))
    _supervisor_db(home / "state.sqlite3", incident=True)
    incidents, exit_code = collect_incidents(tmp_path, component="supervisor")
    assert exit_code == 1
    assert incidents[0]["exact_object"] == "app_server_effects/effect-1"
    assert "not indexed" not in json.dumps(incidents)


def test_resolved_supervisor_incident_is_history_not_active_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "supervisor"
    monkeypatch.setenv("HMASD_CODEX_SUPERVISOR_HOME", str(home))
    _supervisor_db(home / "state.sqlite3", resolved_incident=True)

    doctor, exit_code = collect_doctor(tmp_path, component="supervisor")
    incidents, incident_exit = collect_incidents(tmp_path, component="supervisor")

    assert exit_code == incident_exit == 0
    assert doctor["status"] == "OK"
    assert doctor["findings"] == []
    assert doctor["counters"]["supervisor_active_incidents"] == 0
    assert incidents[0]["resolution"] == {"mechanical_state": "OPERATOR_RESOLVED"}


def test_invalid_filter_or_since_is_configuration_unavailable(tmp_path: Path) -> None:
    doctor, code = collect_doctor(tmp_path, component="not-a-component")
    assert code == 2
    assert doctor["status"] == "UNAVAILABLE"
    doctor, code = collect_doctor(tmp_path, component="semantic", since="not-a-time")
    assert code == 2
    assert doctor["status"] == "UNAVAILABLE"
