#!/usr/bin/env python3
"""Append one owner-supplied factual event to a JSONL workflow log."""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Iterator, Sequence


DEFAULT_LOG = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "research"
    / "workflow-runs"
    / "2026-08-11_five-round-research-team"
    / "events_v2.jsonl"
)


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def _truth_value(value: str) -> object:
    if value == "true":
        return True
    if value == "false":
        return False
    return "unknown"


@contextmanager
def _exclusive_lock(lock_path: Path) -> Iterator[None]:
    lock_file = open(lock_path, "a+b")
    try:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        _lock_one_byte(lock_file)
        try:
            yield
        finally:
            lock_file.seek(0)
            _unlock_one_byte(lock_file)
    finally:
        lock_file.close()


if os.name == "nt":
    import msvcrt

    def _lock_one_byte(lock_file: BinaryIO) -> None:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_one_byte(lock_file: BinaryIO) -> None:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock_one_byte(lock_file: BinaryIO) -> None:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

    def _unlock_one_byte(lock_file: BinaryIO) -> None:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _append_line(log_path: Path, payload: bytes) -> None:
    lock_path = log_path.with_name(f"{log_path.name}.lock")
    with _exclusive_lock(lock_path):
        descriptor = os.open(
            log_path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0),
            0o666,
        )
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written == 0:
                    raise OSError("workflow log append wrote zero bytes")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append one owner-supplied factual JSON object to a workflow log."
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG),
        help=f"JSONL destination (default: {DEFAULT_LOG}).",
    )
    parser.add_argument("--timestamp", default=None, help="Event time (default: now).")
    parser.add_argument("--event", default=None, help="Optional descriptive event label.")
    parser.add_argument("--owner", required=True, help="Owner of the event truth.")
    parser.add_argument(
        "--scope", required=True, help="Direction name or portfolio scope."
    )
    parser.add_argument("--treatment", default=None, help="Treatment, when one exists.")
    parser.add_argument("--action", required=True, help="Natural-language action.")
    parser.add_argument("--outcome", required=True, help="Natural-language outcome.")
    parser.add_argument(
        "--scientific-activity-started",
        required=True,
        choices=("true", "false", "unknown"),
    )
    parser.add_argument(
        "--scientific-meaning-changed",
        required=True,
        choices=("true", "false", "unknown"),
    )
    parser.add_argument(
        "--next",
        dest="next_action",
        required=True,
        help="Next owner or next action.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Optional repository-relative artifact path; repeat as needed.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    record = {
        "timestamp": args.timestamp or _timestamp(),
        "owner": args.owner,
        "scope": args.scope,
        "treatment": args.treatment,
        "action": args.action,
        "outcome": args.outcome,
        "scientific_activity_started": _truth_value(
            args.scientific_activity_started
        ),
        "scientific_meaning_changed": _truth_value(args.scientific_meaning_changed),
        "next": args.next_action,
    }
    if args.event is not None:
        record["event"] = args.event
    if args.artifact:
        record["artifacts"] = list(args.artifact)

    payload = (
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    try:
        _append_line(Path(args.log), payload)
    except OSError as error:
        print(f"workflow event append failed: {error}", file=sys.stderr, flush=True)
        return 1

    print(json.dumps(record, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
