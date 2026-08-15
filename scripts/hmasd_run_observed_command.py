#!/usr/bin/env python3
"""Run one exact command and record its directly observed terminal facts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def _activity_value(value: str) -> object:
    if value == "true":
        return True
    if value == "false":
        return False
    return "unknown"


def _write_json(path: Path, record: dict[str, Any]) -> None:
    parent = path.parent
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one caller-supplied command in the foreground and record only "
            "its terminal facts."
        )
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory for the command (default: current directory).",
    )
    parser.add_argument(
        "--record",
        required=True,
        help="JSON path for the terminal record; its parent must already exist.",
    )
    parser.add_argument(
        "--activity-predicate",
        required=True,
        help="Exact caller-named criterion for question-relevant activity.",
    )
    parser.add_argument(
        "--activity-observation",
        required=True,
        choices=("true", "false", "unknown"),
        help="Caller's observation under the named criterion.",
    )
    parser.add_argument(
        "--output-path",
        action="append",
        default=[],
        help="Caller-named output path; repeat for more than one path.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Exact executable and arguments, normally following --.",
    )
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("an exact command is required after --")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    command = list(args.command)
    cwd = os.path.abspath(args.cwd)
    started_at = _timestamp()
    exit_code: int | None = None
    direct_error: str | None = None

    try:
        completed = subprocess.run(command, cwd=cwd, shell=False, check=False)
        exit_code = completed.returncode
        if exit_code != 0:
            direct_error = f"command exited with code {exit_code}"
    except (OSError, ValueError) as error:
        direct_error = str(error)

    ended_at = _timestamp()
    record = {
        "command": command,
        "cwd": cwd,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "direct_error": direct_error,
        "output_paths": list(args.output_path),
        "scientific_activity_predicate": args.activity_predicate,
        "scientific_activity_started": _activity_value(args.activity_observation),
    }
    rendered = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    print(rendered, flush=True)

    try:
        _write_json(Path(args.record), record)
    except OSError as error:
        print(f"terminal record write failed: {error}", file=sys.stderr, flush=True)
        return 1

    if exit_code is None:
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
