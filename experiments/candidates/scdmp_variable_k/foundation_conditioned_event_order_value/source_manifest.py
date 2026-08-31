"""Direct FCEOV source manifest; no derived identity or authorization fields."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Mapping

from .contracts import Manifest


class SourceManifestError(ValueError):
    pass


def build_source_manifest() -> dict[str, object]:
    return Manifest().to_dict()


def validate_source_manifest(value: Mapping[str, object]) -> Manifest:
    expected = build_source_manifest()
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise SourceManifestError("source manifest differs from the frozen direct contract")
    manifest = Manifest()
    manifest.validate()
    package_root = Path(__file__).resolve().parent
    actual = tuple(sorted(path.stem for path in package_root.glob("*.py")))
    if actual != tuple(sorted(manifest.source_modules)):
        raise SourceManifestError("source module inventory differs from the direct allowlist")
    return manifest


def load_source_manifest(path: str | Path) -> Manifest:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SourceManifestError("source manifest is not readable canonical JSON") from error
    if not isinstance(value, dict):
        raise SourceManifestError("source manifest root must be an object")
    return validate_source_manifest(value)


def write_source_manifest(path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(build_source_manifest(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
    except FileExistsError as error:
        raise SourceManifestError("source manifest is create-only") from error
    finally:
        temporary.unlink(missing_ok=True)


load_and_validate_source_manifest = load_source_manifest


__all__ = [
    "SourceManifestError", "build_source_manifest", "load_and_validate_source_manifest",
    "load_source_manifest", "validate_source_manifest", "write_source_manifest",
]
