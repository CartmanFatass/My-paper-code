from __future__ import annotations

import math
from typing import Callable

import numpy as np
from scipy.stats import t as student_t

from .config import ARMS, HELDOUT_CELLS, HELDOUT_SIZES, REGISTERED, REVISION, SEEDS
from .evaluation import cell_key


def _bitwise_equal(values: np.ndarray) -> bool:
    return bool(np.all(values.view(np.uint64) == values.view(np.uint64)[0]))


def _two_sided_interval(values: list[float]) -> dict[str, float | bool]:
    sample = np.asarray(values, dtype=np.float64)
    if sample.shape != (16,) or not bool(np.isfinite(sample).all()):
        return {"valid": False, "mean": math.nan, "lower": math.nan, "upper": math.nan}
    mean = float(sample.mean(dtype=np.float64))
    variance = float(sample.var(ddof=1, dtype=np.float64))
    if variance == 0.0:
        if not _bitwise_equal(sample):
            return {"valid": False, "mean": mean, "lower": math.nan, "upper": math.nan}
        return {"valid": True, "mean": mean, "lower": mean, "upper": mean}
    quantile = float(student_t.ppf(1.0 - 0.05 / (2.0 * 4.0), df=15))
    half_width = quantile * math.sqrt(variance / 16.0)
    return {
        "valid": math.isfinite(half_width),
        "mean": mean,
        "lower": mean - half_width,
        "upper": mean + half_width,
    }


def _one_sided_lower(values: list[float]) -> dict[str, float | bool]:
    sample = np.asarray(values, dtype=np.float64)
    if sample.shape != (16,) or not bool(np.isfinite(sample).all()):
        return {"valid": False, "mean": math.nan, "lower": math.nan}
    mean = float(sample.mean(dtype=np.float64))
    variance = float(sample.var(ddof=1, dtype=np.float64))
    if variance == 0.0:
        if not _bitwise_equal(sample):
            return {"valid": False, "mean": mean, "lower": math.nan}
        return {"valid": True, "mean": mean, "lower": mean}
    quantile = float(student_t.ppf(1.0 - 0.05 / 3.0, df=15))
    lower = mean - quantile * math.sqrt(variance / 16.0)
    return {"valid": math.isfinite(lower), "mean": mean, "lower": lower}


def _relation(intervals: dict[str, dict[str, float | bool]], prefix: str,
              adverse_name: str) -> str:
    margin = REGISTERED.material_return_margin
    values = list(intervals.values())
    if all(float(interval["lower"]) > margin for interval in values):
        return f"{prefix}_SGSP_MATERIALLY_BETTER"
    if all(float(interval["upper"]) < -margin for interval in values):
        return f"{prefix}_{adverse_name}_MATERIALLY_BETTER"
    if all(
        float(interval["lower"]) >= -margin and float(interval["upper"]) <= margin
        for interval in values
    ):
        return f"{prefix}_PRACTICALLY_EQUIVALENT"
    if (
        any(float(interval["lower"]) > margin for interval in values)
        and any(float(interval["upper"]) < -margin for interval in values)
    ):
        return f"{prefix}_REGIME_OR_SIZE_INTERACTION"
    return f"{prefix}_UNRESOLVED"


def _all_lower_above(intervals: dict[str, dict[str, float | bool]]) -> bool:
    return all(
        float(interval["lower"]) > REGISTERED.material_return_margin
        for interval in intervals.values()
    )


def _packet_hard_valid(packet: dict[str, object]) -> bool:
    try:
        evaluation = packet["evaluation"]
        dense = packet["dense_reference_audit"]
        structural = packet["structural_checkpoint_audit"]
        cells = evaluation["cells"]
        required_dense_panels = {
            "SGSP-W|intact", "ALT-CENTER|intact", "EDGE-PE|intact",
            "SGSP-W|sender_reassociation", "ALT-CENTER|sender_reassociation",
            "EDGE-PE|sender_reassociation", "SGSP-W|center_swap",
        }
        if set(dense["per_panel_max_error"]) != required_dense_panels:
            return False
        for n in (6, 8, 12, 16):
            for regime in ("SAME", "OPPOSED"):
                cell = cells[cell_key(n, regime)]
                panels = set(cell["identity_replay_by_panel"])
                required = {f"{arm}|intact" for arm in (
                    "SGSP-W", "ALT-CENTER", "EDGE-PE", "ANON-MEAN",
                )}
                if n in HELDOUT_SIZES and regime == "OPPOSED":
                    required.update({
                        "SGSP-W|sender_reassociation",
                        "ALT-CENTER|sender_reassociation",
                        "EDGE-PE|sender_reassociation",
                        "SGSP-W|center_swap",
                    })
                if panels != required:
                    return False
        return bool(
            packet.get("revision") == REVISION
            and packet.get("arms") == list(ARMS)
            and packet.get("atomic_payload_complete") is True
            and evaluation.get("seed") == packet.get("seed")
            and packet["training"]["updates_completed"] == 240
            and packet["training"]["only_evaluable_checkpoint"]
            == "immediately_after_optimizer_update_240"
            and dense["E_finite_pass"] is True
            and dense["E_graph"] == 0.0
            and dense["all_panel_declared_centers_match"] is True
            and structural["parameter_counts_pass"] is True
            and evaluation["common_support"]["finite_logits_and_probabilities"] is True
            and evaluation["common_support"]["floor_pass"] is True
            and evaluation["common_support"]["ceiling_pass"] is True
            and evaluation["identity_replay"]["max_error_pass"] is True
            and evaluation["identity_replay"]["inverse_permuted_actions_equal"] is True
            and evaluation["identity_replay"]["team_return_equal"] is True
            and all(
                cell["intact_edge_arm_work_exactly_equal"] is True
                and cell["common_structural_replay_work_exactly_equal"] is True
                and all(
                    ratio == 1
                    for ratio in cell["intact_edge_arm_work_ratio_to_sgsp"].values()
                )
                and all(
                    ratio == 1
                    for panel in cell["common_structural_replay_work_ratio_to_sgsp"].values()
                    for ratio in panel.values()
                )
                for cell in cells.values()
            )
        )
    except (KeyError, TypeError, AttributeError, IndexError, ValueError):
        return False


def analyze_packets(packets: list[dict[str, object]]) -> dict[str, object]:
    if len(packets) != len(SEEDS) or [int(packet["seed"]) for packet in packets] != list(SEEDS):
        return {
            "complete_atomic_evidence": False,
            "hard_structural_validity": False,
            "branch": "TECHNICAL_INVALIDITY_OR_INCOMPLETE_EVIDENCE",
            "reason": "all 16 registered seed packets in exact seed order are required",
        }
    hard_valid = all(_packet_hard_valid(packet) for packet in packets)
    if not hard_valid:
        return {
            "complete_atomic_evidence": True,
            "hard_structural_validity": False,
            "branch": "TECHNICAL_INVALIDITY_OR_INCOMPLETE_EVIDENCE",
            "reason": "one or more atomic packets failed structural/schema validation",
        }

    contrasts: dict[str, dict[str, list[float]]] = {
        family: {} for family in ("GE", "GA", "GM", "EM", "AM")
    }
    arm_pairs = {
        "GE": ("SGSP-W", "EDGE-PE"),
        "GA": ("SGSP-W", "ALT-CENTER"),
        "GM": ("SGSP-W", "ANON-MEAN"),
        "EM": ("EDGE-PE", "ANON-MEAN"),
        "AM": ("ALT-CENTER", "ANON-MEAN"),
    }
    for n, regime in HELDOUT_CELLS:
        key = cell_key(n, regime)
        for family, (left, right) in arm_pairs.items():
            contrasts[family][key] = [
                float(packet["evaluation"]["cells"][key]["mean_intact_return"][left])
                - float(packet["evaluation"]["cells"][key]["mean_intact_return"][right])
                for packet in packets
            ]
    intervals = {
        family: {key: _two_sided_interval(values) for key, values in cells.items()}
        for family, cells in contrasts.items()
    }
    interval_valid = all(
        interval["valid"] is True
        for family in intervals.values() for interval in family.values()
    )
    hard_valid = hard_valid and interval_valid
    ge_relation = _relation(intervals["GE"], "GE", "EDGE")
    ga_relation = _relation(intervals["GA"], "GA", "ALT")
    anonymous_labels = {
        "SGSP_BEATS_ANON": _all_lower_above(intervals["GM"]),
        "EDGE_BEATS_ANON": _all_lower_above(intervals["EM"]),
        "ALT_BEATS_ANON": _all_lower_above(intervals["AM"]),
    }

    mean_u: dict[str, float] = {}
    mean_l: dict[str, float] = {}
    mean_return: dict[str, dict[str, float]] = {}
    for n, regime in HELDOUT_CELLS:
        key = cell_key(n, regime)
        mean_u[key] = float(np.mean([
            packet["evaluation"]["cells"][key]["sampled_return_envelope"]["upper"]
            for packet in packets
        ], dtype=np.float64))
        mean_l[key] = float(np.mean([
            packet["evaluation"]["cells"][key]["sampled_return_envelope"]["lower"]
            for packet in packets
        ], dtype=np.float64))
        mean_return[key] = {
            arm: float(np.mean([
                packet["evaluation"]["cells"][key]["mean_intact_return"][arm]
                for packet in packets
            ], dtype=np.float64))
            for arm in ("SGSP-W", "ALT-CENTER", "EDGE-PE", "ANON-MEAN")
        }

    margin = REGISTERED.material_return_margin
    availability = {
        "GE_TWO_SIDED_AVAILABLE": all(
            mean_u[cell_key(n, regime)] - mean_return[cell_key(n, regime)]["EDGE-PE"] > margin
            and mean_return[cell_key(n, regime)]["EDGE-PE"] - mean_l[cell_key(n, regime)] > margin
            for n, regime in HELDOUT_CELLS
        ),
        "GA_TWO_SIDED_AVAILABLE": all(
            mean_u[cell_key(n, regime)] - mean_return[cell_key(n, regime)]["ALT-CENTER"] > margin
            and mean_return[cell_key(n, regime)]["ALT-CENTER"] - mean_l[cell_key(n, regime)] > margin
            for n, regime in HELDOUT_CELLS
        ),
        "ANON_POSITIVE_AVAILABLE": all(
            mean_u[cell_key(n, regime)] - mean_return[cell_key(n, regime)]["ANON-MEAN"] > margin
            for n, regime in HELDOUT_CELLS
        ),
    }

    sender_minima: dict[str, list[float]] = {"return": [], "tv": [], "attenuation": []}
    center_minima: dict[str, list[float]] = {"return": [], "tv": [], "attenuation": []}
    return_caps: list[float] = []
    tv_caps: list[float] = []
    ge_attenuation_caps: list[float] = []
    ga_attenuation_caps: list[float] = []
    for packet in packets:
        by_n: dict[int, dict[str, float]] = {}
        for n in HELDOUT_SIZES:
            key = cell_key(n, "OPPOSED")
            cell = packet["evaluation"]["cells"][key]
            intact = cell["mean_intact_return"]
            reassoc = cell["mean_sender_reassociation_return"]
            upper = float(cell["sampled_return_envelope"]["upper"])
            lower = float(cell["sampled_return_envelope"]["lower"])
            d_ge = float(intact["SGSP-W"]) - float(intact["EDGE-PE"])
            d_ga = float(intact["SGSP-W"]) - float(intact["ALT-CENTER"])
            by_n[n] = {
                "sender_return": float(intact["SGSP-W"]) - float(reassoc["SGSP-W"]),
                "sender_tv": float(cell["mean_sender_reassociation_tv"]["SGSP-W"]),
                "ge_attenuation": d_ge - (
                    float(reassoc["SGSP-W"]) - float(reassoc["EDGE-PE"])
                ),
                "center_return": float(intact["SGSP-W"]) - float(
                    cell["mean_sgsp_center_swap_return"]
                ),
                "center_tv": float(cell["mean_sgsp_center_swap_tv"]),
                "ga_attenuation": d_ga - (
                    float(reassoc["SGSP-W"]) - float(reassoc["ALT-CENTER"])
                ),
                "return_cap": float(intact["SGSP-W"]) - lower,
                "tv_cap": float(cell["mean_sgsp_tv_support_cap"]),
                "ge_attenuation_cap": d_ge + upper - lower,
                "ga_attenuation_cap": d_ga + upper - lower,
            }
        sender_minima["return"].append(min(by_n[n]["sender_return"] for n in HELDOUT_SIZES))
        sender_minima["tv"].append(min(by_n[n]["sender_tv"] for n in HELDOUT_SIZES))
        sender_minima["attenuation"].append(min(
            by_n[n]["ge_attenuation"] for n in HELDOUT_SIZES
        ))
        center_minima["return"].append(min(by_n[n]["center_return"] for n in HELDOUT_SIZES))
        center_minima["tv"].append(min(by_n[n]["center_tv"] for n in HELDOUT_SIZES))
        center_minima["attenuation"].append(min(
            by_n[n]["ga_attenuation"] for n in HELDOUT_SIZES
        ))
        return_caps.append(min(by_n[n]["return_cap"] for n in HELDOUT_SIZES))
        tv_caps.append(min(by_n[n]["tv_cap"] for n in HELDOUT_SIZES))
        ge_attenuation_caps.append(min(
            by_n[n]["ge_attenuation_cap"] for n in HELDOUT_SIZES
        ))
        ga_attenuation_caps.append(min(
            by_n[n]["ga_attenuation_cap"] for n in HELDOUT_SIZES
        ))

    availability.update({
        "CUT_RETURN_DROP_AVAILABLE": float(np.mean(return_caps, dtype=np.float64))
        > REGISTERED.reassociation_return_threshold,
        "CUT_ACTION_TV_AVAILABLE": float(np.mean(tv_caps, dtype=np.float64))
        > REGISTERED.reassociation_tv_threshold,
        "GE_ATTENUATION_AVAILABLE": float(np.mean(ge_attenuation_caps, dtype=np.float64))
        > REGISTERED.attenuation_threshold,
        "GA_ATTENUATION_AVAILABLE": float(np.mean(ga_attenuation_caps, dtype=np.float64))
        > REGISTERED.attenuation_threshold,
    })

    sender_bounds = {name: _one_sided_lower(values) for name, values in sender_minima.items()}
    center_bounds = {name: _one_sided_lower(values) for name, values in center_minima.items()}
    bound_valid = all(
        bound["valid"] is True for family in (sender_bounds, center_bounds)
        for bound in family.values()
    )
    hard_valid = hard_valid and bound_valid
    sender_pass = bool(
        float(sender_bounds["return"]["lower"]) > REGISTERED.reassociation_return_threshold
        and float(sender_bounds["tv"]["lower"]) > REGISTERED.reassociation_tv_threshold
        and float(sender_bounds["attenuation"]["lower"]) > REGISTERED.attenuation_threshold
    )
    center_pass = bool(
        float(center_bounds["return"]["lower"]) > REGISTERED.reassociation_return_threshold
        and float(center_bounds["tv"]["lower"]) > REGISTERED.reassociation_tv_threshold
        and float(center_bounds["attenuation"]["lower"]) > REGISTERED.attenuation_threshold
    )

    ge_two = availability["GE_TWO_SIDED_AVAILABLE"]
    ga_two = availability["GA_TWO_SIDED_AVAILABLE"]
    all_mechanism_available = all(availability[name] for name in (
        "CUT_RETURN_DROP_AVAILABLE", "CUT_ACTION_TV_AVAILABLE",
        "GE_ATTENUATION_AVAILABLE", "GA_ATTENUATION_AVAILABLE",
    ))
    if not hard_valid:
        branch = "TECHNICAL_INVALIDITY_OR_INCOMPLETE_EVIDENCE"
    elif (
        ge_two and ga_two and availability["ANON_POSITIVE_AVAILABLE"]
        and all_mechanism_available
        and ge_relation == "GE_SGSP_MATERIALLY_BETTER"
        and ga_relation == "GA_SGSP_MATERIALLY_BETTER"
        and anonymous_labels["SGSP_BEATS_ANON"] and sender_pass and center_pass
    ):
        branch = "PROMOTE_FIXED_SEMANTIC_GRAPHON_SECOND_SURFACE"
    elif ga_two and ga_relation in (
        "GA_ALT_MATERIALLY_BETTER", "GA_PRACTICALLY_EQUIVALENT",
    ):
        branch = "DELETE_CORRECT_CENTER_SPECIFIC_FAMILY"
    elif (
        ge_two and availability["ANON_POSITIVE_AVAILABLE"]
        and ge_relation == "GE_EDGE_MATERIALLY_BETTER"
        and anonymous_labels["EDGE_BEATS_ANON"]
        and not anonymous_labels["SGSP_BEATS_ANON"]
    ):
        branch = "BOUNDED_GENERIC_EDGE_EVIDENCE"
    elif ge_two and ge_relation in (
        "GE_EDGE_MATERIALLY_BETTER", "GE_PRACTICALLY_EQUIVALENT",
    ):
        branch = "CAPACITY_COMPARATOR_DELETION_OR_EQUIVALENCE"
    elif (
        ge_two and ga_two and all_mechanism_available
        and ge_relation == "GE_SGSP_MATERIALLY_BETTER"
        and ga_relation == "GA_SGSP_MATERIALLY_BETTER"
        and not (sender_pass and center_pass)
    ):
        branch = "ANSWERABLE_MECHANISM_FAILURE"
    elif (
        ge_two and ge_relation == "GE_REGIME_OR_SIZE_INTERACTION"
    ) or (
        ga_two and ga_relation == "GA_REGIME_OR_SIZE_INTERACTION"
    ):
        branch = "IDENTIFYING_SIZE_OR_REGIME_INTERACTION"
    elif not all(availability.values()):
        branch = "FAILED_ENDPOINT_CUT_OR_ATTENUATION_AVAILABILITY"
    else:
        branch = "BOUNDED_NONIDENTIFICATION"

    return {
        "complete_atomic_evidence": True,
        "hard_structural_validity": hard_valid,
        "intervals": intervals,
        "relations": {"GE": ge_relation, "GA": ga_relation, **anonymous_labels},
        "availability": availability,
        "availability_seed_minimum_caps": {
            "R_CAP": return_caps,
            "TV_CAP": tv_caps,
            "I_CAP_GE": ge_attenuation_caps,
            "I_CAP_GA": ga_attenuation_caps,
        },
        "mechanism": {
            "sender_association": {"bounds": sender_bounds, "passed": sender_pass},
            "correct_center": {"bounds": center_bounds, "passed": center_pass},
            "within_seed_minimum_precedes_across_seed_inference": True,
        },
        "branch": branch,
    }
