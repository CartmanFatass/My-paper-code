from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXIT_OK = 0
EXIT_CHECK_FAILED = 2
EXIT_UNREADABLE = 3


def _sha256_stats(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    data = bytearray()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
            data.extend(chunk)

    raw = bytes(data)
    utf8_valid = True
    char_count: int | None
    try:
        text = raw.decode("utf-8")
        char_count = len(text)
    except UnicodeDecodeError:
        utf8_valid = False
        char_count = None

    return {
        "size_bytes": size,
        "sha256": digest.hexdigest(),
        "utf8": {
            "valid": utf8_valid,
            "char_count": char_count,
            "lf_count": raw.count(b"\n"),
            "crlf_count": raw.count(b"\r\n"),
            "has_bom": raw.startswith(b"\xef\xbb\xbf"),
        },
    }


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def fingerprint(
    path: Path,
    *,
    expect_sha256: str | None = None,
    expect_size_bytes: int | None = None,
    require_utf8: bool = False,
) -> tuple[int, dict[str, Any]]:
    result: dict[str, Any] = {
        "ok": False,
        "path": {
            "input": str(path),
            "absolute": None,
        },
        "file": None,
        "checks": [],
    }

    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        result["error"] = {
            "kind": "path_unreadable",
            "message": str(exc),
        }
        return EXIT_UNREADABLE, result

    result["path"]["absolute"] = str(resolved)

    if not resolved.is_file():
        result["error"] = {
            "kind": "not_a_file",
            "message": "path exists but is not a regular file",
        }
        return EXIT_UNREADABLE, result

    try:
        file_info = _sha256_stats(resolved)
    except OSError as exc:
        result["error"] = {
            "kind": "file_unreadable",
            "message": str(exc),
        }
        return EXIT_UNREADABLE, result

    result["file"] = file_info
    ok = True

    if expect_sha256 is not None:
        expected = expect_sha256.lower()
        actual = str(file_info["sha256"])
        check = {
            "name": "sha256",
            "expected": expected,
            "actual": actual,
            "ok": expected == actual,
        }
        result["checks"].append(check)
        ok = ok and bool(check["ok"])

    if expect_size_bytes is not None:
        actual_size = int(file_info["size_bytes"])
        check = {
            "name": "size_bytes",
            "expected": expect_size_bytes,
            "actual": actual_size,
            "ok": expect_size_bytes == actual_size,
        }
        result["checks"].append(check)
        ok = ok and bool(check["ok"])

    if require_utf8:
        utf8_valid = bool(file_info["utf8"]["valid"])
        check = {
            "name": "utf8",
            "expected": True,
            "actual": utf8_valid,
            "ok": utf8_valid,
        }
        result["checks"].append(check)
        ok = ok and utf8_valid

    result["ok"] = ok
    return (EXIT_OK if ok else EXIT_CHECK_FAILED), result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute and optionally verify the byte identity of one local file. "
            "This is a local reproducibility helper, not a task identity, router, "
            "approval, or authentication layer."
        )
    )
    parser.add_argument("--path", required=True, help="File whose exact bytes are inspected.")
    parser.add_argument(
        "--expect-sha256",
        help="Optional expected SHA-256 hex digest. Mismatch exits nonzero.",
    )
    parser.add_argument(
        "--expect-size-bytes",
        type=int,
        help="Optional expected byte length. Mismatch exits nonzero.",
    )
    parser.add_argument(
        "--require-utf8",
        action="store_true",
        help="Require the file to decode as UTF-8. Invalid UTF-8 exits nonzero.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.expect_sha256 is not None and not _is_sha256(args.expect_sha256):
        parser.error("--expect-sha256 must be a 64-character hexadecimal SHA-256 digest")
    if args.expect_size_bytes is not None and args.expect_size_bytes < 0:
        parser.error("--expect-size-bytes must be nonnegative")

    exit_code, payload = fingerprint(
        Path(args.path),
        expect_sha256=args.expect_sha256,
        expect_size_bytes=args.expect_size_bytes,
        require_utf8=args.require_utf8,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
