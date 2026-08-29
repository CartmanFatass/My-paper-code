"""Length-prefixed SHA-256 semantic random coordinates."""

from __future__ import annotations

import hashlib
import math
from statistics import NormalDist
from typing import Iterable

from .config import RNG_DOMAIN, ROOT_LABELS

_NORMAL = NormalDist()


def _field(value: object) -> bytes:
    raw = str(value).encode("utf-8")
    return len(raw).to_bytes(4, "big", signed=False) + raw


def digest(*fields: object) -> bytes:
    payload = b"".join(_field(x) for x in (RNG_DOMAIN, *fields))
    return hashlib.sha256(payload).digest()


def uniform(*fields: object) -> float:
    """Return the registered open-interval uniform for a semantic key."""
    k = int.from_bytes(digest(*fields)[:8], "big", signed=False)
    # ldexp avoids an intermediate integer-to-integer division.  Clamp only the
    # unrepresentable endpoint caused by IEEE rounding; the mathematical value
    # is always strictly inside (0, 1).
    value = math.ldexp(float(k), -64) + math.ldexp(1.0, -65)
    return min(max(value, math.nextafter(0.0, 1.0)), math.nextafter(1.0, 0.0))


def normal(*fields: object) -> float:
    return _NORMAL.inv_cdf(uniform(*fields))


def root_label(root: int) -> str:
    return ROOT_LABELS[root]


def ordered_without_replacement(
    candidates: Iterable[int], count: int, *fields: object
) -> list[int]:
    ranked = sorted(candidates, key=lambda item: uniform(*fields, "candidate", item))
    return ranked[:count]
