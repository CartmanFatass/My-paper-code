"""Canonical artifact I/O and lifecycle guards for the UAV G0 runner."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


_SHA1 = re.compile(r"^[0-9a-f]{40}$")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    payload = _canonical_bytes(dict(value)) + b"\n"
    if temporary.exists():
        raise ValueError(f"G0 stale temporary artifact exists: {temporary.name}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary.read_bytes() != payload or json.loads(payload) != dict(value):
            raise ValueError("G0 temporary artifact validation failed")
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G0 artifact {path.name} is not a mapping")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_exact_keys(value: Any, keys: frozenset[str], *, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ValueError(f"G0 {label} exact schema mismatch")


def _validate_source_commit(value: str) -> str:
    candidate = str(value)
    if _SHA1.fullmatch(candidate) is None:
        raise ValueError("G0 source commit must be a lowercase 40-character SHA-1")
    return candidate


def _require_fresh_root(path: Path) -> Path:
    root = Path(path).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("G0 run root must be absent or empty")
    return root


def _reference(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _digest(path),
    }


def _assert_exact_files(root: Path, expected: set[str]) -> None:
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise ValueError(
            f"G0 terminal proof inventory mismatch: expected {sorted(expected)}, got {sorted(actual)}"
        )
