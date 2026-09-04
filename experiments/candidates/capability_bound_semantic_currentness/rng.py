"""Stateless CBSC-F0-V1 counter addresses and canonical serialization.

There is intentionally no import of ``random``, NumPy, or Torch in this module.
Nuisance identifiers depend only on the seven exogenous binary coordinates; no
controller, action, scientific intervention, or traversal position enters them.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .schema import NuisanceCoordinate, to_jsonable


NUISANCE_VERSION = "CBSC-F0-V1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        to_jsonable(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_dumps(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def _nuisance_digest(coordinate: NuisanceCoordinate) -> str:
    """Typed seven-bit nuisance-only counter primitive."""

    if type(coordinate) is not NuisanceCoordinate:
        raise TypeError("CBSC-F0-V1 accepts only NuisanceCoordinate")
    address = coordinate.address()
    if len(address) != 7 or any(type(value) is not int or value not in (0, 1) for value in address):
        raise ValueError("CBSC-F0-V1 requires exactly seven binary nuisance fields")
    payload = [NUISANCE_VERSION, "NUISANCE", list(address)]
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def nuisance_id(coordinate: NuisanceCoordinate) -> str:
    return f"{NUISANCE_VERSION}:{_nuisance_digest(coordinate)[:24]}"


__all__ = ["NUISANCE_VERSION", "canonical_bytes", "canonical_dumps", "nuisance_id"]
