"""Typed fresh-production seam; intentionally closed until single-pass integration lands."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping


def execute_fresh_pipeline(
    *, output_root: Path, result_path: Path, preflight: Mapping[str, object],
) -> Mapping[str, object]:
    """Refuse before roots while the declared engineering gate remains incomplete."""

    _ = (Path(output_root), Path(result_path))
    if preflight.get("ready_for_optimizer") is not True:
        raise PermissionError("production requires a passed prospective preflight")
    raise PermissionError(
        "ENGINEERING_SINGLE_PASS_RESIDUAL_CALIBRATION_PIPELINE_INCOMPLETE: no production "
        "implementation is authorized until TRAIN/EVALUATION all-horizon residual collection, "
        "first-boundary G16, staged RAW-LONG competence, and final analysis share one exact "
        "full-tape traversal and the prospective branch ledger"
    )


__all__ = ["execute_fresh_pipeline"]
