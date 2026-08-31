#!/usr/bin/env python3
"""Validate an inbound direction/prompt transport request without sending it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def _error(message: str) -> int:
    print(json.dumps({"valid": False, "error": message}, ensure_ascii=False))
    return 2


def _portfolio_has_direction(portfolio: Path, direction_id: str) -> bool:
    if not portfolio.is_file():
        return False
    pattern = re.compile(rf"^\|\s*{re.escape(direction_id)}\s*\|")
    return any(pattern.search(line) for line in portfolio.read_text(encoding="utf-8").splitlines())


def validate(request: dict, project_root: Path) -> dict:
    request_id = request.get("request_id")
    direction_id = request.get("direction_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")
    if not isinstance(direction_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", direction_id):
        raise ValueError("direction_id must use letters, digits, underscore, or hyphen")

    direction_path = project_root / "docs" / "research" / "candidates" / direction_id / "DIRECTION.md"
    portfolio_path = project_root / "docs" / "research" / "portfolio" / "PORTFOLIO.md"
    if not direction_path.is_file() or not _portfolio_has_direction(portfolio_path, direction_id):
        raise ValueError(f"unknown or unregistered direction_id: {direction_id}")

    prompt = request.get("prompt")
    prompt_path_value = request.get("prompt_path")
    if (prompt is None) == (prompt_path_value is None):
        raise ValueError("provide exactly one of prompt or prompt_path")

    source_mode = "paste"
    prompt_path = None
    if prompt is not None:
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("prompt must be a non-empty string")
        prompt_bytes = prompt.encode("utf-8")
    else:
        source_mode = "upload"
        if not isinstance(prompt_path_value, str) or not Path(prompt_path_value).is_absolute():
            raise ValueError("prompt_path must be an absolute path")
        prompt_path = Path(prompt_path_value)
        if not prompt_path.is_file():
            raise ValueError(f"prompt_path is not a file: {prompt_path}")
        prompt_bytes = prompt_path.read_bytes()
        if not prompt_bytes:
            raise ValueError("prompt_path is empty")

    companion_prompt = request.get("companion_prompt")
    if companion_prompt is not None and (not isinstance(companion_prompt, str) or not companion_prompt):
        raise ValueError("companion_prompt must be a non-empty string when supplied")

    reference_paths_value = request.get("reference_paths", [])
    if reference_paths_value is None:
        reference_paths_value = []
    if not isinstance(reference_paths_value, list):
        raise ValueError("reference_paths must be a list")
    reference_files = []
    seen_references = set()
    for raw_reference in reference_paths_value:
        if not isinstance(raw_reference, str) or not Path(raw_reference).is_absolute():
            raise ValueError("every reference_path must be an absolute path")
        reference_path = Path(raw_reference)
        if not reference_path.is_file():
            raise ValueError(f"reference_path is not a file: {reference_path}")
        resolved_reference = reference_path.resolve()
        if resolved_reference in seen_references:
            raise ValueError(f"duplicate reference_path: {resolved_reference}")
        seen_references.add(resolved_reference)
        reference_bytes = resolved_reference.read_bytes()
        if not reference_bytes:
            raise ValueError(f"reference_path is empty: {resolved_reference}")
        reference_files.append(
            {
                "path": str(resolved_reference),
                "filename": resolved_reference.name,
                "bytes": len(reference_bytes),
                "sha256": hashlib.sha256(reference_bytes).hexdigest(),
            }
        )

    return {
        "valid": True,
        "request_id": request_id,
        "direction_id": direction_id,
        "direction_path": str(direction_path.resolve()),
        "source_mode": source_mode,
        "prompt_path": str(prompt_path.resolve()) if prompt_path else None,
        "prompt_bytes": len(prompt_bytes),
        "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "companion_prompt": companion_prompt,
        "companion_prompt_sha256": hashlib.sha256(companion_prompt.encode("utf-8")).hexdigest() if companion_prompt is not None else None,
        "reference_files": reference_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request_json", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    try:
        request = json.loads(args.request_json.read_text(encoding="utf-8"))
        if not isinstance(request, dict):
            return _error("request JSON must be an object")
        print(json.dumps(validate(request, args.project_root.resolve()), ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
