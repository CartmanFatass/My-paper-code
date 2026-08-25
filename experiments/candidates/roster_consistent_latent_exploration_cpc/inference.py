from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.stats import t as student_t

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, EVAL_SIZES, REGISTERED, REVISION, SEEDS


_VERIFIED_PACKET_SENTINEL = object()


class VerifiedSeedPacket:
    def __init__(self, sentinel: object, payload: dict[str, Any]) -> None:
        if sentinel is not _VERIFIED_PACKET_SENTINEL:
            raise PermissionError("verified seed packets are created only by the atomic reader")
        self.payload = payload


class VerifiedAnalysis:
    def __init__(self, sentinel: object, payload: dict[str, Any]) -> None:
        if sentinel is not _VERIFIED_PACKET_SENTINEL:
            raise PermissionError("verified analyses are created only by the protected analyzer")
        self.payload = payload

    def __getitem__(self, key: str):
        return self.payload[key]


def _verified_seed_packet(payload: dict[str, Any]) -> VerifiedSeedPacket:
    return VerifiedSeedPacket(_VERIFIED_PACKET_SENTINEL, payload)


def _finite(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    return True


def _bound(values: list[float], gamma: float) -> dict[str, float | bool]:
    sample = np.asarray(values, dtype=np.float64)
    if sample.shape != (16,) or not np.isfinite(sample).all():
        return {"valid": False, "mean": math.nan, "lower": math.nan, "upper": math.nan}
    mean = float(sample.mean())
    variance = float(sample.var(ddof=1))
    radius = 0.0 if variance == 0.0 else float(student_t.ppf(gamma, df=15)) * math.sqrt(variance) / 4.0
    return {"valid": True, "mean": mean, "lower": mean - radius, "upper": mean + radius}


def _strictly_above(value: object, threshold: float) -> bool:
    return float(value) > threshold


def _strictly_below(value: object, threshold: float) -> bool:
    return float(value) < threshold


def _probability(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and 0.0 <= float(value) <= 1.0


def _counts(value: object, length: int, total: int) -> bool:
    return (
        isinstance(value, list) and len(value) == length
        and all(type(item) is int and item >= 0 for item in value)
        and sum(value) == total
    )


def _cell_complete(cell: dict[str, Any], arm: str, n: int) -> bool:
    if not all(_probability(cell[name]) for name in (
        "mean_value", "mission_success", "fragmentation", "pre_target_accuracy",
        "post_target_accuracy", "pre_validity", "post_validity",
    )):
        return False
    if cell.get("episodes") != REGISTERED.eval_episodes_per_cell:
        return False
    if not _counts(cell.get("macro_occupancy"), 2, REGISTERED.eval_episodes_per_cell):
        return False
    majorities = cell.get("manager_by_clue_majority")
    if not isinstance(majorities, list) or len(majorities) != 3:
        return False
    if [entry.get("majority") for entry in majorities] != ["LEFT", "TIE", "RIGHT"]:
        return False
    if sum(entry.get("episodes", -1) for entry in majorities) != REGISTERED.eval_episodes_per_cell:
        return False
    if not all(_probability(entry.get("mean_p_macro_1")) for entry in majorities):
        return False
    expected_fixed = 0 if arm == "CONTEXT-SHUFFLED-COARSE" else REGISTERED.eval_episodes_per_cell
    if cell.get("source_map_fixed_points") != expected_fixed:
        return False
    histograms = cell.get("role_corridor_histograms")
    if not isinstance(histograms, dict) or set(histograms) != {"PRE", "POST"}:
        return False
    sensor_total = math.ceil(n / 2) * REGISTERED.eval_episodes_per_cell
    relay_total = math.floor(n / 2) * REGISTERED.eval_episodes_per_cell
    for phase in ("PRE", "POST"):
        rows = histograms[phase]
        if not isinstance(rows, list) or len(rows) != 2:
            return False
        if not _counts(rows[0], 3, sensor_total) or not _counts(rows[1], 3, relay_total):
            return False
    refinement = cell.get("refinement_occupancy")
    if arm == "FLEXIBLE-PERSISTENT":
        if not _counts(refinement, 8, REGISTERED.eval_episodes_per_cell):
            return False
        if cell.get("effective_cardinality") != sum(item > 0 for item in refinement):
            return False
    elif not _counts(refinement, 8, 0) or cell.get("effective_cardinality") != sum(
        item > 0 for item in cell["macro_occupancy"]
    ):
        return False
    return True


def packet_is_semantically_complete(packet: dict[str, Any]) -> bool:
    try:
        if (packet["revision"] != REVISION or packet["arms"] != list(ARMS)
                or packet["atomic_payload_complete"] is not True
                or packet["training"]["updates_completed"] != 1000
                or packet["training"]["training_episodes"] != 192_000
                or packet["training"]["optimizer_steps"] != 3_000
                or packet["training"]["complete_registered_parameter_count_per_arm"] != REGISTERED.parameters_per_arm
                or packet["training"]["initial_coarse_flexible_action_distributions_bit_identical"] is not True
                or not all(packet["training"]["initial_residual_output_jacobian_nonzero"].values())
                or packet["training"]["only_evaluable_checkpoint"] != "immediately_after_update_1000"
                or packet["training"]["validation_selection"] is not False
                or packet["training"]["early_stopping"] is not False
                or packet["training"]["checkpoint_selection"] is not False
                or packet["evaluation"]["ordinary_episodes"] != 36_864
                or packet["evaluation"]["cut_episodes"] != 4_096
                or packet["evaluation"]["evaluation_updates"] != 0
                or packet["evaluation"]["heldout_training_or_adaptation"] is not False
                or packet["evaluation"]["selected_checkpoint"] is not False
                or packet["evaluation"]["mechanism_index"] != {"N": 9, "handoff": True}
                or packet["certificate_passed"] is not True
                or packet["support_oracles_passed"] is not True
                or packet["containment_and_strictness_passed"] is not True
                or packet["source_revision_and_hyperparameters_exact"] is not True
                or packet["partial_result_interpretation_allowed"] is not False
                or not _finite(packet["evaluation"])):
            return False
        for n in EVAL_SIZES:
            for handoff in ("no_handoff", "handoff"):
                for arm in ARMS:
                    cell = packet["evaluation"]["cells"][str(n)][handoff][arm]
                    if not _cell_complete(cell, arm, n):
                        return False
        for cut in ("PRIVATE-LATENT-CUT", "TEMPORAL-RESET-CUT"):
            cut_value = packet["evaluation"]["cuts"][cut]
            if cut_value["episodes"] != 2048 or not all(_probability(cut_value[name]) for name in (
                "mean_value", "mission_success", "fragmentation",
            )):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def _target_win(value: dict[str, float | bool], robust: dict[str, float | bool]) -> bool:
    return bool(
        (_strictly_above(value["lower"], 0.06) and _strictly_above(robust["lower"], -0.02))
        or (_strictly_above(robust["lower"], 0.06) and _strictly_above(value["lower"], -0.02))
    )


def _analyze_packet_payloads(packets: list[dict[str, Any]]) -> dict[str, Any]:
    exact = len(packets) == 16 and [packet.get("seed") for packet in packets] == list(SEEDS)
    complete = exact and all(packet_is_semantically_complete(packet) for packet in packets)
    if not complete:
        return {
            "revision": REVISION,
            "complete_panel": False,
            "completeness_ok": False,
            "valid_complete": False,
            "branch": "INVALID_OR_INCOMPLETE",
            "reason": "all 16 exact atomic three-arm seed packets and every registered cell are required",
        }

    effects: dict[str, list[float]] = {name: [] for name in (
        "VALUE", "ROBUST", "FRAGMENT", "COMMON", "PERSIST", "CONTEXT",
    )}
    all_zero_mission = True
    for packet in packets:
        cells = packet["evaluation"]["cells"]
        coarse_h = cells["9"]["handoff"][ARMS[0]]
        flexible_h = cells["9"]["handoff"][ARMS[1]]
        shuffled_h = cells["9"]["handoff"][ARMS[2]]
        coarse_n = cells["9"]["no_handoff"][ARMS[0]]
        flexible_n = cells["9"]["no_handoff"][ARMS[1]]
        effects["VALUE"].append(float(coarse_h["mean_value"]) - float(flexible_h["mean_value"]))
        effects["ROBUST"].append(
            (float(flexible_n["mean_value"]) - float(flexible_h["mean_value"]))
            - (float(coarse_n["mean_value"]) - float(coarse_h["mean_value"]))
        )
        effects["FRAGMENT"].append(float(flexible_h["fragmentation"]) - float(coarse_h["fragmentation"]))
        effects["COMMON"].append(
            float(coarse_h["mean_value"]) - float(packet["evaluation"]["cuts"]["PRIVATE-LATENT-CUT"]["mean_value"])
        )
        effects["PERSIST"].append(
            float(coarse_h["mean_value"]) - float(packet["evaluation"]["cuts"]["TEMPORAL-RESET-CUT"]["mean_value"])
        )
        effects["CONTEXT"].append(float(coarse_h["mean_value"]) - float(shuffled_h["mean_value"]))
        for n in EVAL_SIZES:
            for handoff in ("no_handoff", "handoff"):
                for arm in ARMS:
                    all_zero_mission &= float(cells[str(n)][handoff][arm]["mission_success"]) == 0.0

    primary = {name: _bound(effects[name], REGISTERED.primary_gamma) for name in ("VALUE", "ROBUST")}
    value, robust = primary["VALUE"], primary["ROBUST"]
    coarse_target_win = _target_win(value, robust)
    flex_target_win = bool(
        (_strictly_below(value["upper"], -0.06) and _strictly_below(robust["upper"], 0.02))
        or (_strictly_below(robust["upper"], -0.06) and _strictly_below(value["upper"], 0.02))
    )
    target_no_material = bool(
        float(value["lower"]) >= -0.03 and float(value["upper"]) <= 0.03
        and float(robust["lower"]) >= -0.03 and float(robust["upper"]) <= 0.03
    )
    six = {name: _bound(effects[name], REGISTERED.mechanism_gamma) for name in effects}
    coarse_target_win_6 = _target_win(six["VALUE"], six["ROBUST"])
    predicates = {
        "FRAGMENTATION_REDUCED": _strictly_above(six["FRAGMENT"]["lower"], 0.08),
        "COMMONALITY_FUNCTIONAL": _strictly_above(six["COMMON"]["lower"], 0.04),
        "PERSISTENCE_FUNCTIONAL": _strictly_above(six["PERSIST"]["lower"], 0.04),
        "CONTEXT_BINDING_VALUE": _strictly_above(six["CONTEXT"]["lower"], 0.04),
    }
    mechanism_supported = coarse_target_win_6 and all(predicates.values())
    if all_zero_mission:
        branch = "ALL_LEARNED_ZERO_MISSION"
    elif mechanism_supported:
        branch = "COARSE_MECHANISM_SUPPORTED"
    elif coarse_target_win:
        branch = "COARSE_PACKAGE_ONLY"
    elif flex_target_win:
        branch = "FLEXIBLE_CONTAINING_SUPERIOR"
    elif target_no_material:
        branch = "NO_COARSE_ADVANTAGE"
    else:
        branch = "TARGET_UNRESOLVED"
    return {
        "revision": REVISION,
        "complete_panel": True,
        "completeness_ok": True,
        "valid_complete": True,
        "seed_order": list(SEEDS),
        "seed_is_inferential_unit": True,
        "seed_df": 15,
        "effect_index": {"mechanisms": {"N": 9, "handoff": True}},
        "per_seed_effects": effects,
        "primary_rectangle": primary,
        "coarse_target_win": coarse_target_win,
        "flex_target_win": flex_target_win,
        "target_no_material": target_no_material,
        "six_lower_bound_family": six,
        "coarse_target_win_6": coarse_target_win_6,
        "mechanism_predicates": predicates,
        "mechanism_supported": mechanism_supported,
        "all_learned_zero_mission": all_zero_mission,
        "branch": branch,
    }


def analyze_packets(
    packets: list[VerifiedSeedPacket],
    permit: ProductionPermit,
    certificate_path,
) -> VerifiedAnalysis:
    require_active_permit(permit)
    if certificate_path.resolve() != permit.certificate_path.resolve():
        raise PermissionError("analysis certificate differs from the active permit")
    if not packets or not all(isinstance(packet, VerifiedSeedPacket) for packet in packets):
        raise PermissionError("analysis requires packets returned by the protected atomic reader")
    result = _analyze_packet_payloads([packet.payload for packet in packets])
    require_active_permit(permit)
    if result.get("valid_complete") is not True or result.get("completeness_ok") is not True:
        raise RuntimeError("protected analyzer refused an incomplete atomic panel")
    return VerifiedAnalysis(_VERIFIED_PACKET_SENTINEL, result)
