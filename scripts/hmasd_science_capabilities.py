#!/usr/bin/env python3
"""List and observe the current HMASD scientific capability catalog."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project runtime
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "configs" / "scientific-capabilities-v1.toml"
FIELDS = {"capability", "status", "purpose", "entrypoint", "environment", "allowed_effects"}


class CapabilityError(Exception):
    pass


def load_catalog(path: Path) -> dict[str, Any]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CapabilityError(f"cannot read catalog: {exc}") from exc
    if set(value) != {"catalog", "capability"} or value.get("catalog") != {"version": 1}:
        raise CapabilityError("catalog header is invalid")
    items = value.get("capability")
    if not isinstance(items, list) or not items:
        raise CapabilityError("catalog requires capabilities")
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise CapabilityError(f"capability[{index}] fields are invalid")
        identifier = item["capability"]
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise CapabilityError(f"capability[{index}].capability is invalid or duplicate")
        seen.add(identifier)
        if item["status"] not in {"active", "unavailable"}:
            raise CapabilityError(f"capability[{index}].status is invalid")
        if not isinstance(item["purpose"], str) or not item["purpose"].strip():
            raise CapabilityError(f"capability[{index}].purpose is required")
        for field in ("entrypoint", "environment"):
            if not isinstance(item[field], str):
                raise CapabilityError(f"capability[{index}].{field} must be a string")
        effects = item["allowed_effects"]
        if not isinstance(effects, list) or not effects or any(
            not isinstance(effect, str) or not effect for effect in effects
        ) or len(effects) != len(set(effects)):
            raise CapabilityError(f"capability[{index}].allowed_effects is invalid")
        if item["status"] == "active" and (not item["entrypoint"] or not item["environment"]):
            raise CapabilityError(f"active capability {identifier} lacks entrypoint/environment")
        if item["status"] == "unavailable" and (item["entrypoint"] or item["environment"]):
            raise CapabilityError(f"unavailable capability {identifier} must not claim an installation")
    return value


def find_capability(catalog: dict[str, Any], identifier: str) -> dict[str, Any]:
    for item in catalog["capability"]:
        if item["capability"] == identifier:
            return item
    raise CapabilityError(f"unknown capability: {identifier}")


def doctor(item: dict[str, Any]) -> dict[str, Any]:
    result = dict(item)
    result["observed"] = {"available": False, "version": None, "reason": None}
    if item["status"] == "unavailable":
        result["observed"]["reason"] = "catalog status is unavailable"
        return result
    entrypoint = Path(item["entrypoint"])
    environment = ROOT / item["environment"]
    if not entrypoint.is_file():
        result["observed"]["reason"] = f"entrypoint is absent: {entrypoint}"
        return result
    if not environment.is_file():
        result["observed"]["reason"] = f"environment record is absent: {item['environment']}"
        return result
    completed = subprocess.run(
        [str(entrypoint), "--version"], check=False, capture_output=True, text=True, timeout=15
    )
    result["observed"] = {
        "available": completed.returncode == 0,
        "version": (completed.stdout or completed.stderr).strip() or None,
        "reason": None if completed.returncode == 0 else f"version probe exited {completed.returncode}",
    }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    show = commands.add_parser("show")
    show.add_argument("--id", required=True)
    check = commands.add_parser("doctor")
    check.add_argument("--id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        catalog = load_catalog(Path(args.catalog))
        if args.command == "list":
            result: Any = {
                "version": catalog["catalog"]["version"],
                "capabilities": [
                    {"capability": item["capability"], "status": item["status"], "purpose": item["purpose"]}
                    for item in catalog["capability"]
                ],
            }
        else:
            item = find_capability(catalog, args.id)
            result = item if args.command == "show" else doctor(item)
    except CapabilityError as exc:
        print(f"hmasd science capability refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
