"""Effect-free 4 GiB admission for the isolated SCDMP B01 runner."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable


FOUR_GIB = 4 * 1024**3
_REPO = Path(__file__).resolve().parents[4]
_RESOURCE_SCRIPT = _REPO / "scripts" / "hmasd_resource_preflight.py"


class PreflightError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PreflightReceipt:
    path: Path
    available_physical_bytes: int
    effective_available_bytes: int
    passed: bool


def preflight_run(
    receipt: str | Path,
    *,
    command_runner: Callable[..., object] = subprocess.run,
) -> PreflightReceipt:
    """Measure both memory floors before any RNG/model/native/result effect."""

    path = Path(receipt)
    if path.exists():
        raise PreflightError("preflight receipt must be create-only")
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = command_runner(
        [sys.executable, str(_RESOURCE_SCRIPT), "admit-memory", "--out", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    observed = validate_preflight_receipt(path)
    if getattr(completed, "returncode", 1) != 0:
        raise PreflightError("fresh physical and effective 4 GiB admission failed")
    return observed


def validate_preflight_receipt(path: str | Path) -> PreflightReceipt:
    """Deeply validate one persisted admission receipt without rerunning admission."""

    receipt_path = Path(path)
    try:
        direct = receipt_path.read_bytes()
    except OSError as error:
        raise PreflightError("4 GiB admission receipt is missing or unreadable") from error
    return validate_preflight_receipt_bytes(direct, path=receipt_path)


def validate_preflight_receipt_bytes(direct: bytes, *, path: str | Path) -> PreflightReceipt:
    """Validate already-opened receipt bytes without reopening their path."""

    receipt_path = Path(path)
    try:
        value = json.loads(direct)
    except (UnicodeError, json.JSONDecodeError, TypeError) as error:
        raise PreflightError("4 GiB admission receipt is missing or unreadable") from error
    required = {
        "minimum_available_bytes", "available_physical_bytes", "effective_available_bytes",
        "physical_floor_pass", "effective_floor_pass", "passed",
    }
    physical = value.get("available_physical_bytes") if isinstance(value, dict) else None
    effective = value.get("effective_available_bytes") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict) or not required <= set(value)
        or value.get("minimum_available_bytes") != FOUR_GIB
        or value.get("physical_floor_pass") is not True
        or value.get("effective_floor_pass") is not True
        or value.get("passed") is not True
        or isinstance(physical, bool) or not isinstance(physical, int) or physical < FOUR_GIB
        or isinstance(effective, bool) or not isinstance(effective, int) or effective < FOUR_GIB
    ):
        raise PreflightError("fresh physical and effective 4 GiB admission failed")
    return PreflightReceipt(receipt_path, physical, effective, True)


def admission_receipt_passed(path: str | Path) -> bool:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(value, dict) and value.get("passed") is True


__all__ = [
    "FOUR_GIB", "PreflightError", "PreflightReceipt", "admission_receipt_passed",
    "preflight_run", "validate_preflight_receipt", "validate_preflight_receipt_bytes",
]
