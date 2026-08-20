"""Focused coverage for explicit control-plane workflow rollover."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.codex_semantic_mvp import cli
from tools.codex_semantic_mvp.models import ObligationKind
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def _snapshot(store: SemanticStore, workflow_id: str) -> dict[str, object]:
    return {
        "workflow": tuple(
            store.connection.execute(
                "SELECT state, state_version FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()
        ),
        "tasks": [
            tuple(row)
            for row in store.connection.execute(
                "SELECT task_id, lifecycle FROM tasks WHERE workflow_id = ? ORDER BY task_id",
                (workflow_id,),
            )
        ],
        "obligations": [
            tuple(row)
            for row in store.connection.execute(
                """SELECT obligation_id, state, resolution_json FROM obligations
                WHERE workflow_id = ? ORDER BY obligation_id""",
                (workflow_id,),
            )
        ],
        "reports": [
            tuple(row)
            for row in store.connection.execute(
                """SELECT report_id, raw_message, typed_json, raw_sha256 FROM reports
                WHERE workflow_id = ? ORDER BY report_id""",
                (workflow_id,),
            )
        ],
        "intakes": [
            tuple(row)
            for row in store.connection.execute(
                "SELECT intake_id, report_id, translation_json FROM intakes WHERE workflow_id = ?",
                (workflow_id,),
            )
        ],
        "events": [
            tuple(row)
            for row in store.connection.execute(
                """SELECT seq, event_id, kind, subject_id, payload_json, dedupe_key
                FROM events WHERE workflow_id = ? ORDER BY seq""",
                (workflow_id,),
            )
        ],
        "receipts": int(
            store.connection.execute(
                "SELECT COUNT(*) FROM closure_receipts WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()[0]
        ),
    }


def _populated_workflow(store: SemanticStore, workflow_id: str = "wf-roll") -> tuple[int, int]:
    store.open_workflow(workflow_id, "session-1", "turn-1", "session", "always-on")
    store.register_task(workflow_id, "task-open", "worker", "open task", True)
    store.register_task(workflow_id, "task-returned", "worker", "returned task", True)
    store.record_untyped_return(
        workflow_id, "task-returned", "agent-returned", "worker", "unconsumed report"
    )
    store.register_task(workflow_id, "task-intaken", "worker", "intaken task", True)
    report_id = store.record_untyped_return(
        workflow_id, "task-intaken", "agent-intaken", "worker", "consumed report"
    )
    store.record_intake(
        workflow_id,
        report_id,
        "INTEGRATE",
        {"observed_fact": "mechanical report accepted"},
        {"owner": "/root", "action": "none"},
        "test intake",
    )
    state = store.workflow_state(workflow_id)
    return int(state["state_version"]), int(state["await_cursor"])


def test_reconcile_dry_run_is_read_only(store: SemanticStore) -> None:
    version, cursor = _populated_workflow(store)
    before = _snapshot(store, "wf-roll")
    statements: list[str] = []
    store.connection.set_trace_callback(statements.append)

    plan = store.reconcile_workflow(
        "wf-roll",
        expected_state_version=version,
        expected_await_cursor=cursor,
        reconciliation_id="reconcile-stable-1",
        reason="retire legacy delivery debt",
        apply=False,
    )
    store.connection.set_trace_callback(None)

    assert plan["eligible"] is True
    assert plan["applied"] is False
    assert plan["cancelled_obligation_count"] == 1
    assert plan["cancelled_task_count"] == 2
    assert plan["preserved_intaken_task_count"] == 1
    assert any(statement == "BEGIN" for statement in statements)
    assert not any(statement == "BEGIN IMMEDIATE" for statement in statements)
    assert _snapshot(store, "wf-roll") == before


def test_control_plane_rollover_cannot_use_generic_close(store: SemanticStore) -> None:
    store.open_workflow("wf-empty", "session-empty", "turn-1", "session", "always-on")
    with pytest.raises(ValueError, match="requires workflow-reconcile"):
        store.create_closure_receipt("wf-empty", "CONTROL_PLANE_ROLLOVER", "bypass")


def test_reconcile_apply_preserves_reports_events_and_intakes(store: SemanticStore) -> None:
    version, cursor = _populated_workflow(store)
    before = _snapshot(store, "wf-roll")
    statements: list[str] = []
    store.connection.set_trace_callback(statements.append)

    result = store.reconcile_workflow(
        "wf-roll",
        expected_state_version=version,
        expected_await_cursor=cursor,
        reconciliation_id="reconcile-stable-1",
        reason="retire legacy delivery debt",
        apply=True,
        operator_id="/root",
    )
    store.connection.set_trace_callback(None)

    after = _snapshot(store, "wf-roll")
    assert result["applied"] is True
    assert result["replayed"] is False
    assert any(statement == "BEGIN IMMEDIATE" for statement in statements)
    assert after["reports"] == before["reports"]
    assert after["intakes"] == before["intakes"]
    assert after["events"][:-1] == before["events"]
    assert after["events"][-1][2] == "WORKFLOW_ROLLED_OVER"
    assert after["workflow"][0] == "CANCELLED"
    assert dict(after["tasks"]) == {
        "task-intaken": "INTAKEN",
        "task-open": "CANCELLED",
        "task-returned": "CANCELLED",
    }
    obligation = next(item for item in after["obligations"] if item[1] == "CANCELLED")
    assert obligation[1] == "CANCELLED"
    resolution = json.loads(obligation[2])
    assert resolution["resolution_kind"] == "CONTROL_PLANE_EPOCH_ROLLOVER"
    assert store.connection.execute("SELECT COUNT(*) FROM intakes").fetchone()[0] == 1
    receipt = store.connection.execute(
        "SELECT closure_kind, summary FROM closure_receipts WHERE workflow_id = 'wf-roll'"
    ).fetchone()
    assert receipt["closure_kind"] == "CONTROL_PLANE_ROLLOVER"
    payload = json.loads(receipt["summary"])
    assert payload["reconciliation_id"] == "reconcile-stable-1"
    assert payload["old_state_version"] == version
    assert payload["old_await_cursor"] == cursor
    assert payload["preserved_report_count"] == 2
    assert payload["preserved_event_count"] == len(before["events"])


def test_reconcile_same_id_replays_original_receipt(store: SemanticStore) -> None:
    version, cursor = _populated_workflow(store)
    first = store.reconcile_workflow(
        "wf-roll",
        expected_state_version=version,
        expected_await_cursor=cursor,
        reconciliation_id="reconcile-stable-1",
        reason="retire legacy delivery debt",
        apply=True,
        operator_id="/root",
    )
    before = _snapshot(store, "wf-roll")

    replay = store.reconcile_workflow(
        "wf-roll",
        expected_state_version=version,
        expected_await_cursor=cursor,
        reconciliation_id="reconcile-stable-1",
        reason="ignored on exact idempotent replay",
        apply=True,
        operator_id="/root",
    )

    assert replay["replayed"] is True
    assert replay["receipt_id"] == first["receipt_id"]
    assert replay["reason"] == "retire legacy delivery debt"
    assert _snapshot(store, "wf-roll") == before


@pytest.mark.parametrize("field", ["version", "cursor"])
def test_reconcile_expected_snapshot_mismatch_writes_nothing(
    store: SemanticStore, field: str
) -> None:
    version, cursor = _populated_workflow(store)
    before = _snapshot(store, "wf-roll")
    if field == "version":
        version += 1
    else:
        cursor += 1

    with pytest.raises(ValueError, match=f"expected_{'state_version' if field == 'version' else 'await_cursor'} mismatch"):
        store.reconcile_workflow(
            "wf-roll",
            expected_state_version=version,
            expected_await_cursor=cursor,
            reconciliation_id="reconcile-stable-1",
            reason="retire legacy delivery debt",
            apply=True,
            operator_id="/root",
        )

    assert _snapshot(store, "wf-roll") == before


def test_reconcile_reports_non_session_and_user_decision_exclusions(store: SemanticStore) -> None:
    store.open_workflow("wf-other", "session-other", "turn-1", "direction", "other")
    store.open_obligation(
        "wf-other",
        ObligationKind.USER_DECISION_REQUIRED,
        "/root",
        "choice",
        "requires user decision",
        "choice-1",
    )
    state = store.workflow_state("wf-other")
    before = _snapshot(store, "wf-other")

    result = store.reconcile_workflow(
        "wf-other",
        expected_state_version=int(state["state_version"]),
        expected_await_cursor=int(state["await_cursor"]),
        reconciliation_id="reconcile-excluded",
        reason="must not touch excluded workflow",
        apply=True,
        operator_id="/root",
    )

    assert result["eligible"] is False
    assert result["applied"] is False
    assert {item["kind"] for item in result["exclusions"]} == {
        "NON_SESSION_SCOPE",
        "USER_DECISION_OBLIGATION",
    }
    assert _snapshot(store, "wf-other") == before


def _write_pause_baseline(repo_root: Path, *, hooks: bool, sentinel: bool) -> None:
    codex = repo_root / ".codex"
    codex.mkdir()
    (codex / "config.toml").write_text(
        f"[features]\nhooks = {'true' if hooks else 'false'}\n", encoding="utf-8"
    )
    if sentinel:
        (codex / "semantic-hooks.paused").write_text("paused\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("hooks", "sentinel", "message"),
    [
        (False, False, "requires .codex/semantic-hooks.paused"),
        (True, True, "requires features.hooks=false"),
    ],
)
def test_cli_reconcile_requires_paused_hooks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    hooks: bool,
    sentinel: bool,
    message: str,
) -> None:
    _write_pause_baseline(tmp_path, hooks=hooks, sentinel=sentinel)
    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(
        [
            "--state-dir",
            str(tmp_path / "state"),
            "workflow-reconcile",
            "--workflow-id",
            "wf-missing",
            "--expected-state-version",
            "1",
            "--expected-await-cursor",
            "1",
            "--reconciliation-id",
            "reconcile-1",
            "--reason",
            "test",
            "--dry-run",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert message in output["message"]
    assert not (tmp_path / "state" / "state.sqlite3").exists()


def test_cli_apply_requires_exact_root_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_pause_baseline(tmp_path, hooks=False, sentinel=True)
    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(
        [
            "--state-dir",
            str(tmp_path / "state"),
            "workflow-reconcile",
            "--workflow-id",
            "wf-missing",
            "--expected-state-version",
            "1",
            "--expected-await-cursor",
            "1",
            "--reconciliation-id",
            "reconcile-1",
            "--reason",
            "test",
            "--apply",
            "--operator-id",
            "/root",
            "--confirm-workflow-id",
            "wrong-workflow",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "must exactly match" in output["message"]


def test_cli_dry_run_returns_plan_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_pause_baseline(tmp_path, hooks=False, sentinel=True)
    state_dir = tmp_path / "state"
    prepared = SemanticStore(state_dir / "state.sqlite3").initialize()
    prepared.open_workflow("wf-cli", "session-cli", "turn-1", "session", "always-on")
    state = prepared.workflow_state("wf-cli")
    before = _snapshot(prepared, "wf-cli")
    prepared.close()
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(
        [
            "--state-dir",
            str(state_dir),
            "workflow-reconcile",
            "--workflow-id",
            "wf-cli",
            "--expected-state-version",
            str(state["state_version"]),
            "--expected-await-cursor",
            str(state["await_cursor"]),
            "--reconciliation-id",
            "reconcile-cli-1",
            "--reason",
            "dry run only",
            "--dry-run",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["eligible"] is True
    assert output["applied"] is False

    reopened = SemanticStore(state_dir / "state.sqlite3").initialize()
    assert _snapshot(reopened, "wf-cli") == before
    reopened.close()
