"""Create-once B01 five-root production packet and separate TEST double."""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .constants import (
    ROOT_LABELS, SEED_PACKET_SCHEMA, TEST_SEED_LABELS, TEST_SEED_PACKET_SCHEMA,
)
from .contract import B01ContractError, canonical_json_bytes


def _canonical_root(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise B01ContractError(f"{name} must contain 64 lowercase hex digits")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise B01ContractError(f"{name} is not hexadecimal") from exc
    if len(decoded) != 32 or decoded.hex() != value:
        raise B01ContractError(f"{name} is not canonical 32-byte lowercase hex")
    return value


def _publish(path: str | Path, value: Mapping[str, Any]) -> Path:
    target = Path(path).resolve(strict=False)
    temporary = target.with_name(target.name + ".creating")
    if target.exists() or temporary.exists():
        raise B01ContractError("seed packet target is not fresh")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(value)
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
        temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def validate_production_seed_packet(value: Any) -> dict[str, Any]:
    fields = {
        "schema", "labels", "roots_hex", "created_at", "generation_source",
        "complete", "test_only",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("production seed packet fields differ")
    packet = dict(value)
    if (
        packet["schema"] != SEED_PACKET_SCHEMA or packet["labels"] != list(ROOT_LABELS)
        or packet["generation_source"] != "OS_CSPRNG"
        or not isinstance(packet["created_at"], str) or not packet["created_at"].strip()
        or packet["complete"] is not True or packet["test_only"] is not False
    ):
        raise B01ContractError("production seed packet identity differs")
    roots = packet["roots_hex"]
    if not isinstance(roots, list) or len(roots) != 5:
        raise B01ContractError("production seed packet requires five roots")
    decoded = [bytes.fromhex(_canonical_root(root, f"roots_hex[{index}]")) for index, root in enumerate(roots)]
    if len(set(decoded)) != 5:
        raise B01ContractError("production seed packet root bytes must be unique")
    return packet


def validate_test_seed_packet(value: Any) -> dict[str, Any]:
    fields = {"schema", "labels", "roots_hex", "complete", "test_only"}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("TEST seed packet fields differ")
    packet = dict(value)
    if (
        packet["schema"] != TEST_SEED_PACKET_SCHEMA or packet["labels"] != list(TEST_SEED_LABELS)
        or packet["complete"] is not True or packet["test_only"] is not True
    ):
        raise B01ContractError("TEST seed packet identity differs")
    roots = packet["roots_hex"]
    if not isinstance(roots, list) or len(roots) != 5:
        raise B01ContractError("TEST seed packet requires five roots")
    decoded = [bytes.fromhex(_canonical_root(root, f"TEST roots_hex[{index}]"))
               for index, root in enumerate(roots)]
    if len(set(decoded)) != 5:
        raise B01ContractError("TEST seed packet roots must be unique")
    return packet


def read_production_seed_packet(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_absolute():
        raise B01ContractError("production seed packet path must be absolute")
    try:
        data = target.read_bytes()
        value = json.loads(data.decode("ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B01ContractError("production seed packet is unreadable") from exc
    if canonical_json_bytes(value) != data:
        raise B01ContractError("production seed packet bytes are not canonical")
    return validate_production_seed_packet(value)


def read_test_seed_packet(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_absolute():
        raise B01ContractError("TEST seed packet path must be absolute")
    try:
        data = target.read_bytes()
        value = json.loads(data.decode("ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B01ContractError("TEST seed packet is unreadable") from exc
    if canonical_json_bytes(value) != data:
        raise B01ContractError("TEST seed packet bytes are not canonical")
    return validate_test_seed_packet(value)


def create_production_seed_packet(path: str | Path) -> Path:
    """Generate all five roots together from the OS CSPRNG.

    There is intentionally no root, RNG, callback, or count parameter.  Tests
    must use :func:`create_test_seed_packet` and never call this function.
    """

    roots = [secrets.token_bytes(32) for _ in ROOT_LABELS]
    if len(set(roots)) != len(roots):  # astronomically unlikely, fail closed without retry selection
        raise B01ContractError("OS CSPRNG produced duplicate B01 roots")
    return _publish(path, {
        "schema": SEED_PACKET_SCHEMA, "labels": list(ROOT_LABELS),
        "roots_hex": [root.hex() for root in roots],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_source": "OS_CSPRNG",
        "complete": True, "test_only": False,
    })


def create_test_seed_packet(
    path: str | Path, *, roots: tuple[bytes, ...] | None = None,
) -> Path:
    values = roots if roots is not None else tuple(bytes([index]) * 32 for index in range(81, 86))
    if (
        not isinstance(values, tuple) or len(values) != 5
        or any(type(root) is not bytes or len(root) != 32 for root in values)
        or len(set(values)) != 5
    ):
        raise B01ContractError("TEST double requires five unique 32-byte roots")
    return _publish(path, {
        "schema": TEST_SEED_PACKET_SCHEMA, "labels": list(TEST_SEED_LABELS),
        "roots_hex": [root.hex() for root in values],
        "complete": True, "test_only": True,
    })
