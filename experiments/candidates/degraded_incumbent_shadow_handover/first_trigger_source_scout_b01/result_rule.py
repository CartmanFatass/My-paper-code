"""Frozen ordered result rule for DISH first-trigger source scout B01."""

from __future__ import annotations

from typing import Mapping, Sequence


def classify_three_seed_result(seeds: Sequence[Mapping[str, object]]) -> str:
    if len(seeds) != 3:
        raise ValueError("B01 result rule requires three complete seeds")
    usable = [row for row in seeds if bool(row["usable_trigger_support"])]
    if len(usable) < 2:
        return "FTS-B0"
    if sum(not bool(row["shadow_nonharm"]) for row in usable) >= 2:
        return "FTS-BH"
    positive = [row for row in usable if float(row["delta_shadow"]) > 0 and bool(row["shadow_nonharm"])]
    positive_tail = [row for row in positive if float(row["delta_shadow_worst20"]) > 0]
    if len(positive_tail) >= 2:
        return "FTS-BS"
    if len(positive) >= 2:
        return "FTS-BR"
    if sum(float(row["delta_copy"]) > 0 and float(row["delta_shadow"]) <= 0 for row in usable) >= 2:
        return "FTS-BC"
    if sum(float(row["delta_shadow"]) <= 0 for row in usable) >= 2:
        return "FTS-BN"
    return "FTS-BU"


__all__ = ["classify_three_seed_result"]
