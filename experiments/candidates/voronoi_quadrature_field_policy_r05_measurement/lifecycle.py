"""Atomic TEST-only measurement publication and exact resume seam."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .contracts import TEST_NAMESPACE, require_test_namespace


class TestLifecycleError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"


def _exclusive_atomic(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"TEST-only write-once path already exists: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(payload).hexdigest()


def publish_frontier(root: Path, generation: int, payload: Mapping[str, Any]) -> dict[str, object]:
    if generation < 0:
        raise ValueError("generation must be nonnegative")
    if payload.get("namespace") != TEST_NAMESPACE:
        raise PermissionError("frontier payload is outside the TEST namespace")
    require_test_namespace(str(payload["namespace"]))
    body = canonical_json_bytes(dict(payload))
    path = root / "frontier" / f"generation-{generation:04d}.json"
    digest = _exclusive_atomic(path, body)
    marker = {
        "namespace": TEST_NAMESPACE,
        "generation": generation,
        "payload": str(path.relative_to(root)).replace("\\", "/"),
        "payload_sha256": digest,
        "test_only": True,
        "scientific_output": False,
    }
    marker_path = root / "commits" / f"generation-{generation:04d}.json"
    marker_digest = _exclusive_atomic(marker_path, canonical_json_bytes(marker))
    return {"generation": generation, "payload_sha256": digest, "marker_sha256": marker_digest}


def restore_frontier(root: Path) -> dict[str, object]:
    commits = sorted((root / "commits").glob("generation-*.json"))
    if not commits:
        raise TestLifecycleError("TEST frontier has no committed generation")
    latest = commits[-1]
    marker = json.loads(latest.read_text(encoding="ascii"))
    if marker.get("namespace") != TEST_NAMESPACE or marker.get("test_only") is not True:
        raise TestLifecycleError("TEST frontier marker identity is invalid")
    payload_path = root / str(marker["payload"])
    payload_bytes = payload_path.read_bytes()
    if hashlib.sha256(payload_bytes).hexdigest() != marker.get("payload_sha256"):
        raise TestLifecycleError("TEST frontier payload digest mismatch")
    payload = json.loads(payload_bytes.decode("ascii"))
    if payload.get("namespace") != TEST_NAMESPACE:
        raise TestLifecycleError("TEST frontier payload namespace mismatch")
    return {"marker": marker, "payload": payload}


def publish_report(path: Path, payload: Mapping[str, Any]) -> str:
    if payload.get("namespace") != TEST_NAMESPACE:
        raise PermissionError("measurement report is outside the TEST namespace")
    return _exclusive_atomic(path, canonical_json_bytes(dict(payload)))

