from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "id",
    "cwd",
    "archived",
    "model",
    "reasoning_effort",
    "updated_at_ms",
}
SUPPORTED_THINKING = {
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
}


def normalize_workspace(value: str) -> str:
    text = value.strip()
    if text.startswith("\\\\?\\"):
        text = text[4:]
    return os.path.normcase(os.path.abspath(os.path.normpath(text)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read one Codex task's live model and thinking without mutation."
    )
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--expect-cwd", required=True)
    parser.add_argument(
        "--state-db",
        type=Path,
        default=Path.home() / ".codex" / "state_5.sqlite",
    )
    parser.add_argument("--expect-model")
    parser.add_argument("--expect-thinking")
    return parser.parse_args()


def query_thread_settings(
    *,
    thread_id: str,
    expect_cwd: str,
    state_db: Path,
    expect_model: str | None = None,
    expect_thinking: str | None = None,
) -> tuple[int, dict[str, object]]:
    state_db = state_db.expanduser().resolve()
    if not state_db.is_file():
        return 2, {"status": "STATE_DB_UNAVAILABLE", "state_db": str(state_db)}

    try:
        connection = sqlite3.connect(
            f"{state_db.as_uri()}?mode=ro", uri=True, timeout=1.0
        )
        connection.row_factory = sqlite3.Row
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(threads)")
        }
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            return 3, {
                "status": "STATE_SCHEMA_UNSUPPORTED",
                "missing_columns": missing,
            }
        row = connection.execute(
            "SELECT id, cwd, archived, model, reasoning_effort, updated_at_ms "
            "FROM threads WHERE id = ?",
            (thread_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        return 4, {"status": "STATE_DB_READ_ERROR", "error": str(exc)}
    finally:
        if "connection" in locals():
            connection.close()

    if row is None:
        return 5, {"status": "THREAD_NOT_FOUND", "thread_id": thread_id}
    if bool(row["archived"]):
        return 6, {"status": "THREAD_ARCHIVED", "thread_id": thread_id}

    model = str(row["model"] or "").strip()
    thinking = str(row["reasoning_effort"] or "").strip()
    if not model or thinking not in SUPPORTED_THINKING:
        return 7, {"status": "THREAD_SETTINGS_INCOMPLETE", "thread_id": thread_id}

    actual_cwd = normalize_workspace(str(row["cwd"] or ""))
    expected_cwd = normalize_workspace(expect_cwd)
    if actual_cwd != expected_cwd:
        return 8, {
            "status": "THREAD_WORKSPACE_MISMATCH",
            "thread_id": thread_id,
            "cwd": actual_cwd,
        }

    if (
        (expect_model is not None and model != expect_model)
        or (
            expect_thinking is not None
            and thinking != expect_thinking
        )
    ):
        return 9, {
            "status": "SETTINGS_DRIFT",
            "thread_id": thread_id,
            "model": model,
            "thinking": thinking,
        }

    return 0, {
        "status": "LIVE_SETTINGS",
        "thread_id": thread_id,
        "model": model,
        "thinking": thinking,
        "cwd": actual_cwd,
        "updated_at_ms": row["updated_at_ms"],
    }


def main() -> int:
    args = parse_args()
    exit_code, payload = query_thread_settings(
        thread_id=args.thread_id,
        expect_cwd=args.expect_cwd,
        state_db=args.state_db,
        expect_model=args.expect_model,
        expect_thinking=args.expect_thinking,
    )
    print(json.dumps(payload, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
