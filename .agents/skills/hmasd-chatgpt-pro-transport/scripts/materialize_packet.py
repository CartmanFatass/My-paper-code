#!/usr/bin/env python3
"""Materialize one canonical transport packet without changing its content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from transport_contract import (  # noqa: E402
    canonical_packet_manifest,
    packet_artifacts,
    materialized_file_sha256,
)
from validate_request import validate  # noqa: E402


def _write_idempotent(path: Path, content: bytes) -> None:
    """Write a packet artifact once; identical existing bytes are idempotent."""

    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"packet artifact conflict: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def materialize(
    request: Mapping[str, Any],
    *,
    project_root: Path,
    out_dir: Path,
    attempt: int = 1,
) -> dict[str, Any]:
    validation = validate(dict(request), project_root.resolve())
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    references = list(validation["reference_files"])
    names = packet_artifacts(
        str(validation["request_id"]),
        str(validation["direction_id"]),
        [str(item["filename"]) for item in references],
        attempt=attempt,
    )
    prompt_path_value = request.get("prompt_path")
    if prompt_path_value is not None:
        body_bytes = Path(str(prompt_path_value)).resolve().read_bytes()
    else:
        body_value = request.get("prompt")
        if not isinstance(body_value, str):
            raise ValueError("prompt must be a string when prompt_path is absent")
        body_bytes = body_value.encode("utf-8")
    body_path = out_dir / names["body_filename"]
    _write_idempotent(body_path, body_bytes)

    for reference, named in zip(references, names["reference_filenames"], strict=True):
        source_path = Path(str(reference["path"])).resolve()
        destination = out_dir / named["canonical_filename"]
        _write_idempotent(destination, source_path.read_bytes())

    manifest = canonical_packet_manifest(
        request,
        validation,
        attempt=attempt,
        materialized_dir=out_dir,
    )
    manifest["body"]["materialized_path"] = str(body_path.resolve())
    manifest["materialized_artifacts"] = {
        "body": str(body_path.resolve()),
        "references": [
            str((out_dir / item["canonical_filename"]).resolve())
            for item in names["reference_filenames"]
        ],
    }
    manifest_path = out_dir / names["manifest_filename"]
    # Re-read every materialized body/reference so the manifest is also a
    # mechanical receipt, not merely a planned filename list.  The manifest's
    # own hash is returned separately to avoid a self-referential field.
    manifest["materialized_hashes"] = {
        "body": materialized_file_sha256(body_path),
        "references": [
            materialized_file_sha256(out_dir / item["canonical_filename"])
            for item in names["reference_filenames"]
        ],
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _write_idempotent(manifest_path, manifest_bytes)
    manifest["manifest_sha256"] = materialized_file_sha256(manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request_json", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    try:
        request = json.loads(args.request_json.read_text(encoding="utf-8"))
        if not isinstance(request, dict):
            raise ValueError("request JSON must be an object")
        result = materialize(
            request,
            project_root=args.project_root,
            out_dir=args.out_dir,
            attempt=args.attempt,
        )
        print(json.dumps({"valid": True, **result}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(
            json.dumps(
                {"valid": False, "error": {"kind": "packet_error", "message": str(exc)}},
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
