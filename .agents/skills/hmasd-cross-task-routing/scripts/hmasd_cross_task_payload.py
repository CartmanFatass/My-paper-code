"""Create and verify owner-scoped UTF-8 files for HMASD task handoffs."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
ROLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")


class HandoffError(RuntimeError):
    """A fail-closed owner, path or UTF-8 error."""


def _repo_root(value: str) -> Path:
    root = Path(value).resolve()
    if not (root / "AGENTS.md").is_file() or not (root / ".git").exists():
        raise HandoffError("repo must contain AGENTS.md and .git")
    return root


def _validate_owner_role(owner_role: str) -> str:
    if not ROLE_RE.fullmatch(owner_role):
        raise HandoffError(
            "owner role must match [A-Za-z0-9][A-Za-z0-9_-]{0,79}"
        )
    return owner_role


def _handoff_root(repo: Path, owner_role: str) -> Path:
    _validate_owner_role(owner_role)
    root = (repo / "temp" / "sessions" / owner_role / "handoffs").resolve()
    try:
        root.relative_to(repo.resolve())
    except ValueError as exc:
        raise HandoffError("owner role path escapes the repository") from exc
    return root


def _decode_utf8(payload: bytes) -> None:
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HandoffError("payload is not valid UTF-8") from exc


def _metadata(repo: Path, path: Path, status: str, owner_role: str) -> dict[str, str]:
    return {
        "status": status,
        "handoff_path": path.relative_to(repo).as_posix(),
        "handoff_owner_role": _validate_owner_role(owner_role),
        "handoff_encoding": "utf-8",
    }


def write_payload(
    repo: Path, label: str, source: str | None, owner_role: str
) -> dict[str, str]:
    _validate_owner_role(owner_role)
    if not LABEL_RE.fullmatch(label):
        raise HandoffError("label must match [A-Za-z0-9][A-Za-z0-9._-]{0,79}")
    payload = Path(source).read_bytes() if source is not None else sys.stdin.buffer.read()
    _decode_utf8(payload)
    root = _handoff_root(repo, owner_role)
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = root / f"{timestamp}_{label}.txt"
    temporary = root / f".{target.name}.{os.getpid()}.tmp"
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
    return _metadata(repo, target, "LONG_TEXT_HANDOFF_WRITTEN", owner_role)


def _resolve_handoff(repo: Path, value: str, owner_role: str) -> Path:
    candidate = Path(value)
    lexical = candidate if candidate.is_absolute() else repo / candidate
    if lexical.is_symlink():
        raise HandoffError("handoff path must not be a symlink")
    path = lexical.resolve()
    root = _handoff_root(repo, owner_role)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise HandoffError(
            "handoff path is outside the owner's temp/sessions/<role>/handoffs"
        ) from exc
    if len(relative.parts) != 1 or not path.is_file():
        raise HandoffError("handoff path must name one existing payload file")
    return path


def verify_payload(repo: Path, path_value: str, owner_role: str) -> dict[str, str]:
    path = _resolve_handoff(repo, path_value, owner_role)
    _decode_utf8(path.read_bytes())
    return _metadata(repo, path, "LONG_TEXT_HANDOFF_VERIFIED", owner_role)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--owner-role", required=True)
    write.add_argument("--label", required=True)
    write.add_argument("--source")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--owner-role", required=True)
    verify.add_argument("--path", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        repo = _repo_root(args.repo)
        result = (
            write_payload(repo, args.label, args.source, args.owner_role)
            if args.command == "write"
            else verify_payload(repo, args.path, args.owner_role)
        )
    except (HandoffError, OSError) as exc:
        print(json.dumps({"status": "LONG_TEXT_HANDOFF_INVALID", "error": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
