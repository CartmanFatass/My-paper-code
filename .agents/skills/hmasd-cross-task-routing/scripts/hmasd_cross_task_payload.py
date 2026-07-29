"""Create and verify local UTF-8 payloads for HMASD cross-task handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class HandoffError(RuntimeError):
    """A fail-closed handoff identity or filesystem error."""


def _repo_root(value: str) -> Path:
    root = Path(value).resolve()
    if not (root / "AGENTS.md").is_file() or not (root / ".git").exists():
        raise HandoffError("repo must contain AGENTS.md and .git")
    return root


def _handoff_root(repo: Path) -> Path:
    return (repo / "temp" / "handoffs").resolve()


def _valid_utf8(payload: bytes) -> None:
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HandoffError("payload is not valid UTF-8") from exc


def _metadata(repo: Path, path: Path, payload: bytes, status: str) -> dict[str, object]:
    return {
        "status": status,
        "handoff_path": path.relative_to(repo).as_posix(),
        "handoff_bytes": len(payload),
        "handoff_sha256": hashlib.sha256(payload).hexdigest(),
        "handoff_encoding": "utf-8",
    }


def write_payload(repo: Path, label: str, source: str | None) -> dict[str, object]:
    if not LABEL_RE.fullmatch(label):
        raise HandoffError("label must match [A-Za-z0-9][A-Za-z0-9._-]{0,79}")
    payload = Path(source).read_bytes() if source is not None else sys.stdin.buffer.read()
    _valid_utf8(payload)
    digest = hashlib.sha256(payload).hexdigest()
    handoff_root = _handoff_root(repo)
    handoff_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = handoff_root / f"{timestamp}_{label}_{digest[:12]}.txt"
    temporary = handoff_root / f".{target.name}.{os.getpid()}.tmp"
    if target.exists() or temporary.exists():
        raise HandoffError("generated handoff path already exists")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return _metadata(repo, target, payload, "LONG_TEXT_HANDOFF_WRITTEN")


def _resolve_handoff(repo: Path, value: str) -> Path:
    candidate = Path(value)
    path = candidate.resolve() if candidate.is_absolute() else (repo / candidate).resolve()
    handoff_root = _handoff_root(repo)
    try:
        relative = path.relative_to(handoff_root)
    except ValueError as exc:
        raise HandoffError("handoff path is outside temp/handoffs") from exc
    if len(relative.parts) != 1 or not path.is_file():
        raise HandoffError("handoff path must name one existing payload file")
    return path


def verify_payload(
    repo: Path, path_value: str, expected_bytes: int, expected_sha256: str
) -> dict[str, object]:
    if expected_bytes < 0:
        raise HandoffError("expected byte count must be nonnegative")
    if not SHA256_RE.fullmatch(expected_sha256):
        raise HandoffError("expected SHA-256 must be 64 lowercase hex characters")
    path = _resolve_handoff(repo, path_value)
    payload = path.read_bytes()
    _valid_utf8(payload)
    actual = _metadata(repo, path, payload, "LONG_TEXT_HANDOFF_VERIFIED")
    if actual["handoff_bytes"] != expected_bytes:
        raise HandoffError("handoff byte count mismatch")
    if actual["handoff_sha256"] != expected_sha256:
        raise HandoffError("handoff SHA-256 mismatch")
    return actual


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--label", required=True)
    write.add_argument("--source")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--path", required=True)
    verify.add_argument("--bytes", type=int, required=True)
    verify.add_argument("--sha256", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        repo = _repo_root(args.repo)
        if args.command == "write":
            result = write_payload(repo, args.label, args.source)
        else:
            result = verify_payload(repo, args.path, args.bytes, args.sha256)
    except (HandoffError, OSError) as exc:
        print(json.dumps({"status": "LONG_TEXT_HANDOFF_INVALID", "error": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
