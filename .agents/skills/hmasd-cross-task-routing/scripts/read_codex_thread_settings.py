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


def emit(status: str, *, exit_code: int, **fields: object) -> int:
    print(json.dumps({"status": status, **fields}, sort_keys=True))
    return exit_code


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


def main() -> int:
    args = parse_args()
    state_db = args.state_db.expanduser().resolve()
    if not state_db.is_file():
        return emit("STATE_DB_UNAVAILABLE", exit_code=2, state_db=str(state_db))

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
            return emit(
                "STATE_SCHEMA_UNSUPPORTED",
                exit_code=3,
                missing_columns=missing,
            )
        row = connection.execute(
            "SELECT id, cwd, archived, model, reasoning_effort, updated_at_ms "
            "FROM threads WHERE id = ?",
            (args.thread_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        return emit("STATE_DB_READ_ERROR", exit_code=4, error=str(exc))
    finally:
        if "connection" in locals():
            connection.close()

    if row is None:
        return emit("THREAD_NOT_FOUND", exit_code=5, thread_id=args.thread_id)
    if bool(row["archived"]):
        return emit("THREAD_ARCHIVED", exit_code=6, thread_id=args.thread_id)

    model = str(row["model"] or "").strip()
    thinking = str(row["reasoning_effort"] or "").strip()
    if not model or thinking not in SUPPORTED_THINKING:
        return emit(
            "THREAD_SETTINGS_INCOMPLETE",
            exit_code=7,
            thread_id=args.thread_id,
        )

    actual_cwd = normalize_workspace(str(row["cwd"] or ""))
    expected_cwd = normalize_workspace(args.expect_cwd)
    if actual_cwd != expected_cwd:
        return emit(
            "THREAD_WORKSPACE_MISMATCH",
            exit_code=8,
            thread_id=args.thread_id,
            cwd=actual_cwd,
        )

    if (
        (args.expect_model is not None and model != args.expect_model)
        or (
            args.expect_thinking is not None
            and thinking != args.expect_thinking
        )
    ):
        return emit(
            "SETTINGS_DRIFT",
            exit_code=9,
            thread_id=args.thread_id,
            model=model,
            thinking=thinking,
        )

    return emit(
        "LIVE_SETTINGS",
        exit_code=0,
        thread_id=args.thread_id,
        model=model,
        thinking=thinking,
        cwd=actual_cwd,
        updated_at_ms=row["updated_at_ms"],
    )


if __name__ == "__main__":
    sys.exit(main())
