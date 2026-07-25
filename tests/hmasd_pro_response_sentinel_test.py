from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "hmasd_pro_response_sentinel.py"
CONVERSATION = "conversation-1"
FENCE = "round=round-1|stage_commit=abc|question=q.md"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed


def initialize(state: Path) -> dict[str, object]:
    return json.loads(
        run(
            "init",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            FENCE,
        ).stdout
    )


def record(
    state: Path,
    *,
    controls: str,
    available: bool,
    fingerprint: str = "visible-text-fingerprint",
    reason: str = "",
) -> dict[str, object]:
    return json.loads(
        run(
            "record",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            FENCE,
            "--assistant-message-identity",
            "assistant-message-1" if available else "unavailable",
            "--snapshot-fingerprint",
            fingerprint if available else "unavailable",
            "--generation-controls",
            controls,
            "--candidate-available",
            str(available).lower(),
            "--reason",
            reason,
            "--min-stable-seconds",
            "0",
        ).stdout
    )


def test_two_stable_inactive_snapshots_complete_without_answer_now(tmp_path: Path) -> None:
    state = tmp_path / "monitor.jsonl"
    initial = initialize(state)
    assert initial["status"] == "PENDING"
    first = record(state, controls="inactive", available=True)
    assert first["status"] == "PENDING"
    assert first["stable_snapshots"] == 1
    second = record(state, controls="inactive", available=True)
    assert second["status"] == "COMPLETE"
    assert second["stable_snapshots"] == 2
    assert second["answer_now_activated"] is False

    terminal = json.loads(
        run(
            "watch",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            FENCE,
            "--max-wait-seconds",
            "0",
        ).stdout
    )
    assert terminal["terminal"] == "COMPLETE"
    assert terminal["answer_now_activated"] is False


def test_changed_or_active_snapshot_never_completes(tmp_path: Path) -> None:
    state = tmp_path / "monitor.jsonl"
    initialize(state)
    record(state, controls="inactive", available=True, fingerprint="first")
    changed = record(state, controls="inactive", available=True, fingerprint="second")
    assert changed["status"] == "PENDING"
    assert changed["stable_snapshots"] == 1
    active = record(state, controls="active", available=True, fingerprint="second")
    assert active["status"] == "PENDING"
    assert active["stable_snapshots"] == 0


def test_error_is_terminal_and_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    state = tmp_path / "monitor.jsonl"
    initialize(state)
    mismatch = run(
        "status",
        "--state",
        str(state),
        "--conversation-id",
        "wrong-conversation",
        "--fence-identity",
        FENCE,
        check=False,
    )
    assert mismatch.returncode == 2
    assert "conversation identity does not match" in mismatch.stderr

    failed = record(
        state,
        controls="error",
        available=False,
        reason="registered page unavailable",
    )
    assert failed["status"] == "ERROR"
    immutable = run(
        "record",
        "--state",
        str(state),
        "--conversation-id",
        CONVERSATION,
        "--fence-identity",
        FENCE,
        "--assistant-message-identity",
        "unavailable",
        "--snapshot-fingerprint",
        "unavailable",
        "--generation-controls",
        "active",
        "--candidate-available",
        "false",
        check=False,
    )
    assert immutable.returncode == 2
    assert "terminal sentinel is immutable" in immutable.stderr


def test_reader_ignores_partial_final_append(tmp_path: Path) -> None:
    state = tmp_path / "monitor.jsonl"
    initialize(state)
    with state.open("a", encoding="utf-8") as handle:
        handle.write('{"schema_version":1')
    status = json.loads(
        run(
            "status",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            FENCE,
        ).stdout
    )
    assert status["sequence"] == 0
    assert status["status"] == "PENDING"
