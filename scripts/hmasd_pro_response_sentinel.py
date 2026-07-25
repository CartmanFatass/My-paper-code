"""Broker stable Pro-page observations to the read-only response monitor.

The Project Manager remains the sole browser owner.  It appends metadata-only
observations to a JSONL sentinel; the Luna-low child reads that sentinel and
reports only a terminal COMPLETE or ERROR state.  The append-only format avoids
Windows replace races and tolerates a partially written final line.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
TERMINAL_STATES = {"COMPLETE", "ERROR"}
CONTROL_STATES = {"active", "inactive", "error", "unavailable"}


class SentinelError(RuntimeError):
    """Fail-closed sentinel contract violation."""


def _utc_timestamp(now: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))


def _load_last(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SentinelError(f"sentinel does not exist: {path}")
    last: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                # A concurrent reader may see the final append mid-write.  A
                # later poll will consume it once complete.
                continue
            if isinstance(candidate, dict):
                last = candidate
    if last is None:
        raise SentinelError(f"sentinel has no complete record: {path}")
    if last.get("schema_version") != SCHEMA_VERSION:
        raise SentinelError("unsupported sentinel schema")
    return last


def _append(path: Path, payload: dict[str, Any], *, create: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if create else "a"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _require_identity(
    payload: dict[str, Any], conversation_id: str, fence_identity: str
) -> None:
    if payload.get("conversation_id") != conversation_id:
        raise SentinelError("conversation identity does not match sentinel")
    if payload.get("fence_identity") != fence_identity:
        raise SentinelError("freshness-fence identity does not match sentinel")


def initialize(
    path: Path, conversation_id: str, fence_identity: str, now: float
) -> dict[str, Any]:
    if not conversation_id.strip() or not fence_identity.strip():
        raise SentinelError("conversation and fence identities must be non-empty")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "sequence": 0,
        "status": "PENDING",
        "conversation_id": conversation_id,
        "fence_identity": fence_identity,
        "assistant_message_identity": "unavailable",
        "snapshot_fingerprint": "unavailable",
        "stable_snapshots": 0,
        "first_stable_epoch": None,
        "generation_controls": "unavailable",
        "candidate_available": False,
        "answer_now_activated": False,
        "reason": "initialized",
        "observed_at": _utc_timestamp(now),
    }
    try:
        _append(path, payload, create=True)
    except FileExistsError as exc:
        raise SentinelError(f"sentinel already exists: {path}") from exc
    return payload


def record(
    path: Path,
    conversation_id: str,
    fence_identity: str,
    assistant_message_identity: str,
    snapshot_fingerprint: str,
    generation_controls: str,
    candidate_available: bool,
    reason: str,
    min_stable_seconds: float,
    now: float,
) -> dict[str, Any]:
    previous = _load_last(path)
    _require_identity(previous, conversation_id, fence_identity)
    if previous.get("status") in TERMINAL_STATES:
        raise SentinelError("terminal sentinel is immutable")
    if generation_controls not in CONTROL_STATES:
        raise SentinelError("invalid generation-controls state")
    if min_stable_seconds < 0:
        raise SentinelError("min-stable-seconds must be non-negative")

    status = "PENDING"
    stable_snapshots = 0
    first_stable_epoch: float | None = None
    terminal_reason = reason or "pending"

    if generation_controls == "error":
        status = "ERROR"
        terminal_reason = reason or "browser or response control error"
    elif (
        candidate_available
        and generation_controls == "inactive"
        and assistant_message_identity != "unavailable"
        and snapshot_fingerprint != "unavailable"
    ):
        same_candidate = (
            previous.get("assistant_message_identity")
            == assistant_message_identity
            and previous.get("snapshot_fingerprint") == snapshot_fingerprint
            and previous.get("generation_controls") == "inactive"
            and previous.get("candidate_available") is True
        )
        if same_candidate:
            stable_snapshots = int(previous.get("stable_snapshots", 0)) + 1
            raw_first = previous.get("first_stable_epoch")
            first_stable_epoch = float(raw_first) if raw_first is not None else now
        else:
            stable_snapshots = 1
            first_stable_epoch = now
        if stable_snapshots >= 2 and now - first_stable_epoch >= min_stable_seconds:
            status = "COMPLETE"
            terminal_reason = "natural completion stable across two snapshots"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "sequence": int(previous.get("sequence", 0)) + 1,
        "status": status,
        "conversation_id": conversation_id,
        "fence_identity": fence_identity,
        "assistant_message_identity": assistant_message_identity,
        "snapshot_fingerprint": snapshot_fingerprint,
        "stable_snapshots": stable_snapshots,
        "first_stable_epoch": first_stable_epoch,
        "generation_controls": generation_controls,
        "candidate_available": candidate_available,
        "answer_now_activated": False,
        "reason": terminal_reason,
        "observed_at": _utc_timestamp(now),
    }
    _append(path, payload)
    return payload


def terminal_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "terminal": payload["status"],
        "conversation_id": payload["conversation_id"],
        "fence_identity": payload["fence_identity"],
        "assistant_message_identity": payload["assistant_message_identity"],
        "stable_snapshots": payload["stable_snapshots"],
        "generation_controls": payload["generation_controls"],
        "answer_now_activated": False,
        "candidate_available": payload["candidate_available"],
        "reason": payload["reason"],
    }


def watch(
    path: Path,
    conversation_id: str,
    fence_identity: str,
    poll_seconds: float,
    max_wait_seconds: float,
) -> dict[str, Any] | None:
    if poll_seconds <= 0 or max_wait_seconds < 0:
        raise SentinelError("invalid watch interval")
    deadline = time.monotonic() + max_wait_seconds
    while True:
        payload = _load_last(path)
        _require_identity(payload, conversation_id, fence_identity)
        if payload.get("status") in TERMINAL_STATES:
            return terminal_payload(payload)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        time.sleep(min(poll_seconds, remaining))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--state", required=True, type=Path)
    init_parser.add_argument("--conversation-id", required=True)
    init_parser.add_argument("--fence-identity", required=True)

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--state", required=True, type=Path)
    record_parser.add_argument("--conversation-id", required=True)
    record_parser.add_argument("--fence-identity", required=True)
    record_parser.add_argument("--assistant-message-identity", required=True)
    record_parser.add_argument("--snapshot-fingerprint", required=True)
    record_parser.add_argument(
        "--generation-controls", required=True, choices=sorted(CONTROL_STATES)
    )
    record_parser.add_argument(
        "--candidate-available", required=True, choices=("true", "false")
    )
    record_parser.add_argument("--reason", default="")
    record_parser.add_argument("--min-stable-seconds", type=float, default=3.0)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--state", required=True, type=Path)
    status_parser.add_argument("--conversation-id", required=True)
    status_parser.add_argument("--fence-identity", required=True)

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--state", required=True, type=Path)
    watch_parser.add_argument("--conversation-id", required=True)
    watch_parser.add_argument("--fence-identity", required=True)
    watch_parser.add_argument("--poll-seconds", type=float, default=2.0)
    watch_parser.add_argument("--max-wait-seconds", type=float, default=45.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    now = time.time()
    try:
        if args.command == "init":
            result = initialize(
                args.state, args.conversation_id, args.fence_identity, now
            )
        elif args.command == "record":
            result = record(
                args.state,
                args.conversation_id,
                args.fence_identity,
                args.assistant_message_identity,
                args.snapshot_fingerprint,
                args.generation_controls,
                args.candidate_available == "true",
                args.reason,
                args.min_stable_seconds,
                now,
            )
        elif args.command == "status":
            payload = _load_last(args.state)
            _require_identity(payload, args.conversation_id, args.fence_identity)
            result = payload
        else:
            watched = watch(
                args.state,
                args.conversation_id,
                args.fence_identity,
                args.poll_seconds,
                args.max_wait_seconds,
            )
            if watched is None:
                return 0
            result = watched
    except SentinelError as exc:
        print(f"PRO_RESPONSE_SENTINEL_ERROR {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
