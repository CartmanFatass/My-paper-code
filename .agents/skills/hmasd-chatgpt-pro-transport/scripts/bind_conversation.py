#!/usr/bin/env python3
"""Bind one direction to one provider conversation without overwriting conflicts."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path


UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _result(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def _load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "directions": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("directions", {}), dict):
        raise ValueError("registry must be an object with a directions object")
    value.setdefault("version", 1)
    return value


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def bind(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.direction_id):
        return _result({"bound": False, "state": "DIRECTION_UNVERIFIED", "error": "invalid direction_id"}, 2)
    if not UUID_RE.fullmatch(args.conversation_id):
        return _result({"bound": False, "state": "CONVERSATION_UNVERIFIED", "error": "conversation_id must be UUID"}, 2)
    expected_url = f"https://chatgpt.com/c/{args.conversation_id}"
    if args.provider_url != expected_url:
        return _result({"bound": False, "state": "CONVERSATION_UNVERIFIED", "error": "provider_url does not match conversation_id"}, 2)

    registry_path = args.registry.resolve()
    registry = _load(registry_path)
    directions = registry["directions"]
    old = directions.get(args.direction_id)
    if old is not None:
        if old.get("conversation_id") != args.conversation_id:
            return _result(
                {
                    "bound": False,
                    "state": "BINDING_CONFLICT",
                    "direction_id": args.direction_id,
                    "existing_conversation_id": old.get("conversation_id"),
                    "requested_conversation_id": args.conversation_id,
                },
                3,
            )
        return _result({"bound": True, "idempotent": True, "state": "BOUND", "record": old})

    record = {
        "direction_id": args.direction_id,
        "conversation_id": args.conversation_id,
        "provider_url": args.provider_url,
        "tab_id": args.tab_id,
        "request_id": args.request_id,
        "visible_model": args.visible_model,
        "underlying_model": args.underlying_model,
        "thinking_effort": args.thinking_effort,
        "source_mode": args.source_mode,
        "prompt_sha256": args.prompt_sha256,
        "state": "BOUND",
        "send_click_count": 1,
    }
    directions[args.direction_id] = record
    _atomic_write(registry_path, registry)
    return _result({"bound": True, "idempotent": False, "state": "BOUND", "record": record})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--direction-id", required=True)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--provider-url", required=True)
    parser.add_argument("--tab-id", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--visible-model", required=True)
    parser.add_argument("--underlying-model", required=True)
    parser.add_argument("--thinking-effort", required=True)
    parser.add_argument("--source-mode", choices=("paste", "upload"), required=True)
    parser.add_argument("--prompt-sha256", required=True)
    args = parser.parse_args()
    try:
        return bind(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _result({"bound": False, "state": "REGISTRY_ERROR", "error": str(exc)}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
