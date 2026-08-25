#!/usr/bin/env python3
"""Check and repair native-host checkout representation for HMASD authorities.

The repair path never normalizes an unknown document. It replaces a tracked
working file with its exact index bytes only when the sole difference is CRLF
versus LF. Substantive working changes are reported and left untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from typing import Sequence

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREFIXES = (
    "docs/research/portfolio/",
    "docs/research/candidates/",
    "docs/external-review/directions/",
    "tests/fixtures/hmasd_external_review/",
    "tests/fixtures/hmasd_phase0/",
)
TEXT_SUFFIXES = {".md", ".json"}


class HostCompatibilityError(RuntimeError):
    pass


def _git(*args: str, cwd: Path = ROOT, text: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=text,
    )


def _tracked_entries(prefixes: Sequence[str]) -> list[tuple[str, str]]:
    result = _git("ls-files", "-s", "-z")
    if result.returncode != 0:
        raise HostCompatibilityError(result.stderr.decode(errors="replace"))
    entries: list[tuple[str, str]] = []
    for raw in result.stdout.decode("utf-8", errors="strict").split("\0"):
        if not raw:
            continue
        metadata, path = raw.split("\t", 1)
        _mode, object_id, stage = metadata.split(" ", 2)
        if stage != "0":
            raise HostCompatibilityError(f"unmerged index entry: {path}")
        if (
            PurePosixPath(path).suffix.lower() in TEXT_SUFFIXES
            and any(path.startswith(prefix) for prefix in prefixes)
        ):
            entries.append((path, object_id))
    return sorted(
        entries,
        key=lambda item: item[0],
    )


def _index_blobs(entries: Sequence[tuple[str, str]]) -> dict[str, bytes]:
    object_ids = list(dict.fromkeys(object_id for _path, object_id in entries))
    process = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{object_id}\n" for object_id in object_ids).encode("ascii"),
        check=False,
        capture_output=True,
    )
    if process.returncode != 0:
        raise HostCompatibilityError(process.stderr.decode(errors="replace"))
    by_object: dict[str, bytes] = {}
    cursor = 0
    for expected in object_ids:
        line_end = process.stdout.index(b"\n", cursor)
        header = process.stdout[cursor:line_end].decode("ascii").split()
        if len(header) != 3 or header[0] != expected or header[1] != "blob":
            raise HostCompatibilityError(f"unexpected git cat-file header: {header}")
        size = int(header[2])
        start = line_end + 1
        by_object[expected] = process.stdout[start : start + size]
        cursor = start + size + 1
    return {path: by_object[object_id] for path, object_id in entries}


def _lf_equivalent(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def _atomic_write_exact(path: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".host-compat", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise HostCompatibilityError(f"short write for {path}")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        hmasd_platform.fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def inspect_checkout(prefixes: Sequence[str] = DEFAULT_PREFIXES) -> dict[str, object]:
    exact: list[str] = []
    eol_only: list[str] = []
    substantive: list[str] = []
    missing: list[str] = []
    entries = _tracked_entries(prefixes)
    indexed_by_path = _index_blobs(entries)
    for relative, _object_id in entries:
        path = ROOT / Path(relative)
        if not path.is_file():
            missing.append(relative)
            continue
        working = path.read_bytes()
        indexed = indexed_by_path[relative]
        if working == indexed:
            exact.append(relative)
        elif _lf_equivalent(working) == indexed and b"\r\n" in working:
            eol_only.append(relative)
        else:
            substantive.append(relative)
    autocrlf = _git("config", "--get", "core.autocrlf", text=True)
    return {
        "platform": sys.platform,
        "core_autocrlf": autocrlf.stdout.strip() if autocrlf.returncode == 0 else None,
        "exact": exact,
        "eol_only": eol_only,
        "substantive": substantive,
        "missing": missing,
    }


def repair_checkout(prefixes: Sequence[str] = DEFAULT_PREFIXES) -> dict[str, object]:
    before = inspect_checkout(prefixes)
    if before["substantive"] or before["missing"]:
        raise HostCompatibilityError(
            "refusing repair with substantive or missing tracked files: "
            + json.dumps(
                {"substantive": before["substantive"], "missing": before["missing"]},
                ensure_ascii=False,
            )
        )
    entries = _tracked_entries(prefixes)
    indexed_by_path = _index_blobs(entries)
    repaired: list[str] = []
    for relative in before["eol_only"]:
        _atomic_write_exact(ROOT / Path(relative), indexed_by_path[relative])
        repaired.append(relative)
    after = inspect_checkout(prefixes)
    if after["eol_only"] or after["substantive"] or after["missing"]:
        raise HostCompatibilityError("checkout is not byte-exact after repair")
    return {"repaired": repaired, "sha256_by_path": {
        path: hashlib.sha256((ROOT / Path(path)).read_bytes()).hexdigest()
        for path in repaired
    }}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "repair-line-endings"))
    parser.add_argument("--prefix", action="append", dest="prefixes")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prefixes = tuple(args.prefixes or DEFAULT_PREFIXES)
    try:
        result = inspect_checkout(prefixes) if args.mode == "check" else repair_checkout(prefixes)
    except HostCompatibilityError as exc:
        print(str(exc), file=sys.stderr)
        return 5
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if args.mode == "check" and (
        result["eol_only"] or result["substantive"] or result["missing"]
    ):
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
