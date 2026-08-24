"""Frozen request contract for the explicit one-shot App Server canary."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Mapping


CANARY_PROMPT = "Reply exactly: HMASD_APP_SERVER_OBSERVER_OK\nDo not use tools."
CANARY_TEXT = "HMASD_APP_SERVER_OBSERVER_OK"
CANARY_APPROVAL_POLICY = "never"

_CANARY_ID = re.compile(r"canary_[0-9a-f]{32}\Z")


def require_canonical_canary_id(canary_id: str) -> str:
    """Return a generated canary id, rejecting aliases and path components."""

    if type(canary_id) is not str or _CANARY_ID.fullmatch(canary_id) is None:
        raise ValueError("canary id is not canonical")
    return canary_id


def canonical_canary_scratch(runtime_home: Path | str, canary_id: str) -> Path:
    """Return the sole cwd authorized for one canary invocation."""

    canonical_id = require_canonical_canary_id(canary_id)
    home = Path(runtime_home).resolve()
    scratch_root = (home / "scratch").resolve()
    scratch = (scratch_root / canonical_id).resolve()
    if scratch.parent != scratch_root:
        raise ValueError("canary scratch is outside the canonical runtime")
    return scratch


def canonical_canary_thread_start_request(
    runtime_home: Path | str, canary_id: str
) -> dict[str, object]:
    """Build the exact allowed thread/start request."""

    return {
        "cwd": str(canonical_canary_scratch(runtime_home, canary_id)),
        "ephemeral": True,
        "approvalPolicy": CANARY_APPROVAL_POLICY,
    }


def canonical_canary_input() -> list[dict[str, str]]:
    """Return a fresh copy of the exact canary input item."""

    return [{"type": "text", "text": CANARY_PROMPT}]


def canonical_canary_turn_start_request(thread_id: str) -> dict[str, object]:
    """Build the exact allowed turn/start request for the observed thread."""

    if type(thread_id) is not str or not thread_id:
        raise ValueError("canary thread id is required")
    return {
        "threadId": thread_id,
        "input": canonical_canary_input(),
        "approvalPolicy": CANARY_APPROVAL_POLICY,
    }


def is_exact_json_value(actual: object, expected: object) -> bool:
    """Compare JSON structures without Python's bool/numeric coercions.

    Object key insertion order is immaterial.  Array order is material, and
    every scalar must have the same native JSON type on both sides.  Values
    outside the JSON data model fail closed instead of being normalized.
    """

    if expected is None:
        return actual is None
    if type(expected) is bool:
        return type(actual) is bool and actual is expected
    if type(expected) is int:
        return type(actual) is int and actual == expected
    if type(expected) is float:
        if type(actual) is not float:
            return False
        if not math.isfinite(expected) or not math.isfinite(actual):
            return False
        if actual != expected:
            return False
        # Preserve the only distinct finite float values hidden by equality.
        return actual != 0.0 or math.copysign(1.0, actual) == math.copysign(
            1.0, expected
        )
    if type(expected) is str:
        return type(actual) is str and actual == expected
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            return False
        expected_keys = list(expected.keys())
        actual_keys = list(actual.keys())
        if any(type(key) is not str for key in (*expected_keys, *actual_keys)):
            return False
        if set(actual_keys) != set(expected_keys):
            return False
        return all(
            is_exact_json_value(actual[key], expected[key]) for key in expected_keys
        )
    if type(expected) is list:
        return (
            type(actual) is list
            and len(actual) == len(expected)
            and all(
                is_exact_json_value(actual_item, expected_item)
                for actual_item, expected_item in zip(actual, expected)
            )
        )
    return False


def is_exact_canary_request(
    request: object, expected: Mapping[str, object]
) -> bool:
    """Compare the complete decoded request, including its exact key set."""

    return isinstance(request, Mapping) and is_exact_json_value(request, expected)
