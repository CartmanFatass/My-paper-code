"""Guarded isolated runner shell for SCDMP-MF-RS-MK-ORDER-VALUE-B01.

Only the effect-free preflight seam is enabled in the current engineering
milestone. The scientific entry remains disabled until the complete native,
training, artifact, parity, and performance acceptance is integrated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .preflight import PreflightError, PreflightReceipt, preflight_run


class ResultExecutionDisabled(RuntimeError):
    pass


# Component readiness is not full-run readiness. The bounded engineering pilot
# may measure the integrated native/telemetry path, while long scientific work
# remains withheld until the full 9,328-mission orchestration and end-to-end
# performance record exist.  The constrained source-q seam itself is frozen.
A_PILOT_PERFORMANCE_DISPOSITION = "PILOT_ONLY"
RUN_01_PERFORMANCE_DISPOSITION = "REPAIR_REQUIRED"


def _validate_new_result_root(result_root: str | Path) -> Path:
    root = Path(result_root).resolve(strict=False)
    normalized = str(root).replace("\\", "/").lower()
    if "foundation_conditioned_event_order_value" in normalized or "2026-08-31." in normalized:
        raise PreflightError("old FCEOV .1/.2/.3 result coordinates are isolated")
    if root.exists():
        raise PreflightError("prospective B01 result root must not exist during preflight")
    return root


def preflight_only(
    *,
    receipt: str | Path,
    result_root: str | Path,
    command_runner: Callable[..., object],
) -> PreflightReceipt:
    _validate_new_result_root(result_root)
    return preflight_run(receipt, command_runner=command_runner)


def run_result(*, result_root: str | Path) -> None:
    _validate_new_result_root(result_root)
    raise ResultExecutionDisabled(
        "SCDMP B01 RUN-01 remains disabled until complete orchestration and end-to-end acceptance"
    )


__all__ = [
    "A_PILOT_PERFORMANCE_DISPOSITION", "RUN_01_PERFORMANCE_DISPOSITION",
    "ResultExecutionDisabled", "preflight_only", "run_result",
]
