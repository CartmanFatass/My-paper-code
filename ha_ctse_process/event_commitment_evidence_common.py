"""Canonical JSON evidence helpers shared by commitment artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import torch


def _json_default(value: Any) -> Any:
    """Encode one unsupported leaf without recursively copying its container."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "__dict__"):
        return vars(value)
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def _digest_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        default=_json_default,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_exact_int(value: Any) -> bool:
    return type(value) is int
