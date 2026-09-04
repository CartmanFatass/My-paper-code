"""Frozen paired seed-level analysis for VNFC-B2."""

from __future__ import annotations

import math
import statistics
from typing import Mapping, Sequence

from .config import C0, C1, C2, C3, LEARNED_ARMS, ORACLE, RAW, RESET, TYPED


T95_DF7 = 2.3646242515927844
T90_DF7 = 1.894578605061305
JOINT = "joint_holdout"


def interval(values: Sequence[float], critical: float) -> dict[str, object]:
    if len(values) != 8:
        raise ValueError("VNFC-B2 intervals require eight paired seeds")
    mean = statistics.fmean(values)
    deviation = statistics.stdev(values)
    margin = critical * deviation / math.sqrt(8)
    return {
        "seed_values": list(values), "mean": mean,
        "standard_deviation": deviation, "lower": mean - margin,
        "upper": mean + margin,
    }


def _cell(seed: Mapping[str, object], arm: str, cell: str) -> Mapping[str, object]:
    return seed["arms"][arm]["cells"][f"{JOINT}:{cell}"]  # type: ignore[index]


def paired(
    seeds: Sequence[Mapping[str, object]], left: str, right: str,
    metric: str, cell: str,
) -> dict[str, object]:
    pairs = [(_cell(seed, left, cell)[metric], _cell(seed, right, cell)[metric]) for seed in seeds]
    if any(left_value is None or right_value is None for left_value, right_value in pairs):
        return {
            "left": left, "right": right, "metric": metric, "cell": cell,
            "available": False,
            "reason": "required arm has zero eligible service decisions in at least one paired seed",
        }
    values = [float(left_value) - float(right_value) for left_value, right_value in pairs]
    return {
        "left": left, "right": right, "metric": metric, "cell": cell,
        "available": True,
        "student_t_95": interval(values, T95_DF7),
        "student_t_90": interval(values, T90_DF7),
    }


def paired_panel(
    seeds: Sequence[Mapping[str, object]], left: str, right: str,
    metric: str, panel: str, cell: str,
) -> dict[str, object]:
    pairs = [
        (
            seed["arms"][left]["cells"][f"{panel}:{cell}"][metric],  # type: ignore[index]
            seed["arms"][right]["cells"][f"{panel}:{cell}"][metric],  # type: ignore[index]
        )
        for seed in seeds
    ]
    if any(left_value is None or right_value is None for left_value, right_value in pairs):
        return {
            "left": left, "right": right, "metric": metric,
            "panel": panel, "cell": cell, "available": False,
            "reason": "required arm has zero eligible service decisions in at least one paired seed",
        }
    values = [float(left_value) - float(right_value) for left_value, right_value in pairs]
    return {
        "left": left, "right": right, "metric": metric,
        "panel": panel, "cell": cell,
        "available": True,
        "student_t_95": interval(values, T95_DF7),
        "student_t_90": interval(values, T90_DF7),
    }


def analyze(seeds: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if len(seeds) != 8:
        raise ValueError("VNFC-B2 requires eight complete seed panels")
    contrasts: dict[str, object] = {}
    panel_contrasts: dict[str, object] = {}
    panels = (
        "seen_size_seen_schedule", "held_out_size_only",
        "held_out_schedule_only", "joint_holdout",
    )
    for panel in panels:
        for cell in (C0, C1, C2, C3):
            for left, right in (
                (TYPED, RESET), (TYPED, RAW), (RESET, TYPED),
                (RAW, TYPED), (TYPED, ORACLE), (ORACLE, TYPED),
            ):
                for metric in ("J", "RR3", "SCR"):
                    key = f"{panel}:{left}_minus_{right}:{metric}:{cell}"
                    panel_contrasts[key] = paired_panel(
                        seeds, left, right, metric, panel, cell,
                    )
    for cell in (C0, C1, C2, C3):
        for left, right in (
            (TYPED, RESET), (TYPED, RAW), (RESET, TYPED),
            (RAW, TYPED), (TYPED, ORACLE), (ORACLE, TYPED),
        ):
            for metric in ("J", "RR3", "SCR"):
                key = f"{left}_minus_{right}:{metric}:{cell}"
                contrasts[key] = paired(seeds, left, right, metric, cell)

    d_e_values = []
    d_er_values = []
    scr_values_by_cell: dict[str, list[float] | None] = {C2: [], C3: []}
    for seed in seeds:
        reset_c1 = float(_cell(seed, RESET, C1)["RR3"])
        reset_c2 = float(_cell(seed, RESET, C2)["RR3"])
        reset_c3 = float(_cell(seed, RESET, C3)["RR3"])
        typed_c1 = float(_cell(seed, TYPED, C1)["RR3"])
        typed_c2 = float(_cell(seed, TYPED, C2)["RR3"])
        typed_c3 = float(_cell(seed, TYPED, C3)["RR3"])
        d_e_values.append((reset_c2 - typed_c2) - (reset_c3 - typed_c3))
        d_er_values.append((reset_c1 - typed_c1) - (reset_c3 - typed_c3))
        for cell in (C2, C3):
            typed_scr = _cell(seed, TYPED, cell)["SCR"]
            reset_scr = _cell(seed, RESET, cell)["SCR"]
            if typed_scr is None or reset_scr is None:
                scr_values_by_cell[cell] = None
            elif scr_values_by_cell[cell] is not None:
                scr_values_by_cell[cell].append(float(typed_scr) - float(reset_scr))
    named = {
        "D_E": {"student_t_95": interval(d_e_values, T95_DF7),
                "student_t_90": interval(d_e_values, T90_DF7)},
        "D_ER": {"student_t_95": interval(d_er_values, T95_DF7),
                 "student_t_90": interval(d_er_values, T90_DF7)},
        "SCR_TYPED_minus_RESET_by_cell": {
            cell: (
                {
                    "available": True,
                    "student_t_95": interval(scr_values_by_cell[cell], T95_DF7),  # type: ignore[arg-type]
                    "student_t_90": interval(scr_values_by_cell[cell], T90_DF7),  # type: ignore[arg-type]
                }
                if scr_values_by_cell[cell] is not None
                else {
                    "available": False,
                    "reason": "required arm has zero eligible service decisions in at least one paired seed",
                }
            ) for cell in (C2, C3)
        },
    }
    oracle_headroom: dict[str, object] = {}
    for arm in LEARNED_ARMS:
        gap_j = [
            statistics.fmean(
                float(_cell(seed, ORACLE, cell)["J"]) - float(_cell(seed, arm, cell)["J"])
                for cell in (C1, C2)
            ) for seed in seeds
        ]
        gap_rr3 = [
            statistics.fmean(
                float(_cell(seed, arm, cell)["RR3"]) - float(_cell(seed, ORACLE, cell)["RR3"])
                for cell in (C1, C2)
            ) for seed in seeds
        ]
        j_interval = interval(gap_j, T95_DF7)
        rr3_interval = interval(gap_rr3, T95_DF7)
        oracle_headroom[arm] = {
            "OracleGap_J": {"student_t_95": j_interval},
            "OracleGap_RR3": {"student_t_95": rr3_interval},
            "J_rule": float(j_interval["mean"]) >= .05 and float(j_interval["lower"]) > 0.0,
            "RR3_rule": float(rr3_interval["mean"]) >= .10 and float(rr3_interval["lower"]) > 0.0,
        }
    named["oracle_headroom_C1_C2_equal_weight"] = oracle_headroom

    def stats(key: str, confidence: str = "student_t_95") -> Mapping[str, object]:
        row = contrasts[key]
        if not row.get("available", True):  # type: ignore[union-attr]
            raise ValueError(f"contrast unavailable: {key}")
        return row[confidence]  # type: ignore[index]

    def material(key: str, threshold: float) -> bool:
        row = stats(key)
        return float(row["mean"]) >= threshold and float(row["lower"]) > 0.0

    def equivalent(key: str) -> bool:
        row = stats(key, "student_t_90")
        return float(row["lower"]) >= -.03 and float(row["upper"]) <= .03

    d_e = named["D_E"]["student_t_95"]  # type: ignore[index]
    d_er = named["D_ER"]["student_t_95"]  # type: ignore[index]
    stale_errors = {
        name: sum(
            int(seed["arms"][TYPED]["cells"][f"{panel}:{cell}"]["hard_stale_errors"].get(name, 0))  # type: ignore[index,union-attr]
            for seed in seeds for panel in panels for cell in (C0, C1, C2, C3)
        )
        for name in (
            "entity_payload_under_zero_mask", "role_payload_under_zero_mask",
            "capsule_across_owner_break",
        )
    }
    conditions = {
        "D_E_material": float(d_e["mean"]) >= .10 and float(d_e["lower"]) > 0.0,
        "D_ER_material": float(d_er["mean"]) >= .10 and float(d_er["lower"]) > 0.0,
        "typed_vs_reset_same_metric_both_C1_C2": (
            (
                material(f"{TYPED}_minus_{RESET}:J:{C1}", .05)
                and material(f"{TYPED}_minus_{RESET}:J:{C2}", .05)
            ) or (
                material(f"{RESET}_minus_{TYPED}:RR3:{C1}", .10)
                and material(f"{RESET}_minus_{TYPED}:RR3:{C2}", .10)
            )
        ),
        "C3_J_practical_equivalence": equivalent(f"{TYPED}_minus_{RESET}:J:{C3}"),
        "C3_RR3_practical_equivalence": equivalent(f"{RESET}_minus_{TYPED}:RR3:{C3}"),
        "typed_hard_stale_errors_zero": all(value == 0 for value in stale_errors.values()),
        "SCR_C2_C3_each_available_and_upper_at_most_plus_0_02": all(
            bool(named["SCR_TYPED_minus_RESET_by_cell"][cell]["available"])  # type: ignore[index]
            and float(named["SCR_TYPED_minus_RESET_by_cell"][cell]["student_t_95"]["upper"]) <= .02  # type: ignore[index]
            for cell in (C2, C3)
        ),
        "fresh_oracle_room": any(
            bool(row["J_rule"]) or bool(row["RR3_rule"])
            for row in oracle_headroom.values()  # type: ignore[union-attr]
        ),
    }
    raw_conditions = {
        "C2_J_or_RR3_material": (
            material(f"{TYPED}_minus_{RAW}:J:{C2}", .05)
            or material(f"{RAW}_minus_{TYPED}:RR3:{C2}", .10)
        ),
        "C0_J_practical_equivalence": equivalent(f"{TYPED}_minus_{RAW}:J:{C0}"),
        "C0_RR3_practical_equivalence": equivalent(f"{RAW}_minus_{TYPED}:RR3:{C0}"),
    }
    return {
        "contrasts": contrasts, "panel_contrasts": panel_contrasts,
        "named_estimands": named,
        "typed_hard_stale_errors": stale_errors,
        "registered_support_conditions": conditions,
        "typed_over_raw_additional_conditions": raw_conditions,
    }
