"""Deterministic descriptive reductions only; no B01 branch interpretation."""

from __future__ import annotations

from typing import Any, Mapping

from .contract import B01ContractError


def descriptive_analysis(panel: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    raise B01ContractError(
        "PRODUCTION_ANALYSIS_UNAVAILABLE/REPAIR_REQUIRED: exact complete panel and 28-quantity reduction are not implemented"
    )
