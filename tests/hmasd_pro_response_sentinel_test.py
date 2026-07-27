from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "hmasd_pro_response_sentinel.py"
CONVERSATION = "conversation-1"
ROUND = (
    "20260727_continuous_roster_native_six_g31_direction_balance_attribution_"
    "g42_formal_result_review_a6c3c29"
)
FENCE = "\n".join(
    (
        "CURRENT_REVIEW_ASSIGNMENT",
        "repository=CartmanFatass/My-paper-code",
        "branch=aggressive",
        f"round={ROUND}",
        "stage_commit=1b8e97ed1a4ccab37f860068d3fdfe34183b374f",
        "question=20_PRO_OPEN_QUESTION.md",
        "instruction=Ignore earlier rounds and refs. Read only this question and "
        "its listed evidence from stage_commit.",
    )
)
FULL_STAGE_COMMIT = "13ac7eb0eb1adac63a83e55754f7e516d2f40c5b"
SHORT_STAGE_COMMIT = "13ac7eb"
CORRECTED_FENCE = "\n".join(
    (
        "CURRENT_REVIEW_FENCE_CORRECTION",
        f"supersedes_stage_commit={SHORT_STAGE_COMMIT}",
        "repository=CartmanFatass/My-paper-code",
        "branch=aggressive",
        "round=20260727_continuous_roster_native_six_g31_db_norm_schedule_"
        "attribution_g43_formal_result_review",
        f"stage_commit={FULL_STAGE_COMMIT}",
        "question=20_PRO_OPEN_QUESTION.md",
        "instruction=Ignore earlier rounds and refs. Read only this question and "
        "its listed evidence from stage_commit.",
        "correction_scope=stage_commit_prefix_expansion_only; scientific question, "
        "evidence allow-list, and scientific instruction are unchanged and are not "
        "resubmitted.",
    )
)
PREFIX_FENCE = CORRECTED_FENCE.replace(
    f"stage_commit={FULL_STAGE_COMMIT}",
    f"stage_commit={SHORT_STAGE_COMMIT}",
    1,
)


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


def assignment_token(state: Path) -> str:
    initialized = initialize(state)
    token = initialized["monitor_assignment_token"]
    assert isinstance(token, str)
    return token


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
            "--assignment-token",
            str(initial["monitor_assignment_token"]),
            "--max-wait-seconds",
            "0",
        ).stdout
    )
    assert terminal["terminal"] == "COMPLETE"
    assert terminal["answer_now_activated"] is False
    assert terminal["fence_identity"].encode("utf-8") == FENCE.encode("utf-8")
    assert terminal["conversation_id"].encode("utf-8") == CONVERSATION.encode(
        "utf-8"
    )


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


def test_monitor_assignment_token_fails_closed_when_truncated_or_rebound(
    tmp_path: Path,
) -> None:
    state = tmp_path / "monitor.jsonl"
    token = assignment_token(state)

    truncated = run(
        "watch",
        "--state",
        str(state),
        "--assignment-token",
        token[:-1],
        "--max-wait-seconds",
        "0",
        check=False,
    )
    assert truncated.returncode == 2
    assert "monitor assignment token is malformed" in truncated.stderr

    other_state = tmp_path / "other-monitor.jsonl"
    truncated_round = ROUND.removesuffix("_a6c3c29")
    other_fence = FENCE.replace(f"round={ROUND}\n", f"round={truncated_round}\n", 1)
    assert other_fence != FENCE
    other = json.loads(
        run(
            "init",
            "--state",
            str(other_state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            other_fence,
        ).stdout
    )
    rebound = run(
        "watch",
        "--state",
        str(state),
        "--assignment-token",
        str(other["monitor_assignment_token"]),
        "--max-wait-seconds",
        "0",
        check=False,
    )
    assert rebound.returncode == 2
    assert "freshness-fence identity does not match sentinel" in rebound.stderr


def test_full_hash_correction_token_rejects_prefix_fence_identity(
    tmp_path: Path,
) -> None:
    state = tmp_path / "corrected-monitor.jsonl"
    initialized = json.loads(
        run(
            "init",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            CORRECTED_FENCE,
        ).stdout
    )
    for _ in range(2):
        run(
            "record",
            "--state",
            str(state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            CORRECTED_FENCE,
            "--assistant-message-identity",
            "assistant-message-corrected",
            "--snapshot-fingerprint",
            "corrected-response-fingerprint",
            "--generation-controls",
            "inactive",
            "--candidate-available",
            "true",
            "--min-stable-seconds",
            "0",
        )
    terminal = json.loads(
        run(
            "watch",
            "--state",
            str(state),
            "--assignment-token",
            str(initialized["monitor_assignment_token"]),
            "--max-wait-seconds",
            "0",
        ).stdout
    )
    assert terminal["fence_identity"].encode("utf-8") == CORRECTED_FENCE.encode(
        "utf-8"
    )
    assert FULL_STAGE_COMMIT in terminal["fence_identity"]

    prefix_state = tmp_path / "prefix-monitor.jsonl"
    prefix = json.loads(
        run(
            "init",
            "--state",
            str(prefix_state),
            "--conversation-id",
            CONVERSATION,
            "--fence-identity",
            PREFIX_FENCE,
        ).stdout
    )
    rebound = run(
        "watch",
        "--state",
        str(state),
        "--assignment-token",
        str(prefix["monitor_assignment_token"]),
        "--max-wait-seconds",
        "0",
        check=False,
    )
    assert rebound.returncode == 2
    assert "freshness-fence identity does not match sentinel" in rebound.stderr
