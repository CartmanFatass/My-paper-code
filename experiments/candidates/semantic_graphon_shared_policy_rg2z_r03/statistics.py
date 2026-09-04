"""Seed-block inference and the frozen RIDGEGATE-2Z decision surface.

Only seed-level means enter this module.  Episode, agent, slot, and report
observations are deliberately unavailable as inferential replicates.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import math
from typing import Any

import numpy as np
from scipy.stats import t as student_t

from .config import SEEDS as REGISTERED_SEEDS


REVISION = "SGSP-RG2Z-SCIENCE-20260815-03"
ACTION = "SGSP-RG2Z-R03-FULL-PANEL"
TRAIN_SIZES = (9, 15)
HELDOUT_SIZES = (6, 21)
ALL_SIZES = (9, 15, 6, 21)
TRAINED_ARMS = ("PHY-TRUST", "EDGE-FLEX")
SEED_COUNT = 24
FAMILY_SIZE = 18
FAMILY_ALPHA = 0.05

DELTA_R = 0.04
DELTA_C = 0.03
DELTA_Z = 0.02
DELTA_CUT_R = 0.05
DELTA_TV = 0.08
DELTA_I = 0.03
EDGE_FLOOR = 0.08


def _float(value: object) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError("registered statistics must be finite")
    return out


def _interval(values: Sequence[float]) -> dict[str, float | bool | int]:
    """Two-sided paired-seed Student-t interval in the fixed 18-way family."""
    sample = np.asarray(values, dtype=np.float64)
    if sample.shape != (SEED_COUNT,) or not bool(np.isfinite(sample).all()):
        return {
            "valid": False,
            "n": int(sample.size),
            "mean": math.nan,
            "lower": math.nan,
            "upper": math.nan,
        }
    mean = float(sample.mean(dtype=np.float64))
    variance = float(sample.var(ddof=1, dtype=np.float64))
    if variance == 0.0:
        if not bool(np.all(sample.view(np.uint64) == sample.view(np.uint64)[0])):
            return {
                "valid": False, "n": SEED_COUNT, "mean": mean,
                "lower": math.nan, "upper": math.nan,
            }
        return {"valid": True, "n": SEED_COUNT, "mean": mean, "lower": mean, "upper": mean}
    quantile = float(student_t.ppf(
        1.0 - FAMILY_ALPHA / (2.0 * FAMILY_SIZE), df=SEED_COUNT - 1,
    ))
    half_width = quantile * math.sqrt(variance / SEED_COUNT)
    return {
        "valid": math.isfinite(half_width),
        "n": SEED_COUNT,
        "mean": mean,
        "lower": mean - half_width,
        "upper": mean + half_width,
    }


def _h(value: float, margin: float) -> float:
    return min(value, 1.0 - value) - margin


def _evaluation(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    value = packet.get("evaluation", packet)
    if not isinstance(value, Mapping):
        raise TypeError("evaluation payload must be a mapping")
    return value


def _cell(packet: Mapping[str, Any], n: int) -> Mapping[str, Any]:
    cells = _evaluation(packet)["cells"]
    return cells[str(n)] if str(n) in cells else cells[n]


def _panel(packet: Mapping[str, Any], n: int, condition: str, arm: str) -> Mapping[str, Any]:
    panel = _cell(packet, n)[condition]
    if arm == "UNIFORM-LEGAL" and "UNIFORM-LEGAL" not in panel:
        # The evaluator emits the uniform cell as one direct metric mapping.
        return panel
    return panel[arm]


def _return(packet: Mapping[str, Any], n: int, condition: str, arm: str) -> float:
    return _float(_panel(packet, n, condition, arm)["mean_return"])


def _zone(packet: Mapping[str, Any], n: int, condition: str, arm: str, zone: str) -> float:
    panel = _panel(packet, n, condition, arm)
    values = panel["mean_timely_delivery_by_basin"]
    return _float(values[zone] if zone in values else values[zone.lower()])


def _shadow_tv(packet: Mapping[str, Any], n: int) -> float:
    panel = _panel(packet, n, "shadow", "PHY-TRUST")
    return _float(panel["mean_legal_action_tv"])


def _tv_support(packet: Mapping[str, Any], n: int) -> float:
    panel = _panel(packet, n, "shadow", "PHY-TRUST")
    return _float(panel["mean_tv_support"])


def seed_quantities(packet: Mapping[str, Any]) -> dict[str, float]:
    """Derive exactly the 18 registered seed-block quantities."""
    direct = {
        n: _return(packet, n, "intact", "PHY-TRUST")
        - _return(packet, n, "intact", "EDGE-FLEX")
        for n in ALL_SIZES
    }
    seen = 0.5 * (direct[9] + direct[15])
    out: dict[str, float] = {f"d({n})": direct[n] for n in ALL_SIZES}
    for n in TRAIN_SIZES:
        out[f"e({n})"] = (
            _return(packet, n, "intact", "EDGE-FLEX")
            - _return(packet, n, "uniform", "UNIFORM-LEGAL")
        )
    for n in HELDOUT_SIZES:
        out[f"c({n})"] = direct[n] - seen
        out[f"z({n})"] = min(
            _zone(packet, n, "intact", "PHY-TRUST", "WEST"),
            _zone(packet, n, "intact", "PHY-TRUST", "EAST"),
        ) - min(
            _zone(packet, n, "intact", "EDGE-FLEX", "WEST"),
            _zone(packet, n, "intact", "EDGE-FLEX", "EAST"),
        )
        c_phy = (
            _return(packet, n, "intact", "PHY-TRUST")
            - _return(packet, n, "rotated", "PHY-TRUST")
        )
        c_edge = (
            _return(packet, n, "intact", "EDGE-FLEX")
            - _return(packet, n, "rotated", "EDGE-FLEX")
        )
        out[f"C_PHY({n})"] = c_phy
        out[f"V({n})"] = _shadow_tv(packet, n)
        out[f"I({n})"] = c_phy - c_edge

        a_dir = min(
            _h(_return(packet, n, "intact", arm), DELTA_R)
            for arm in TRAINED_ARMS
        )
        a_interaction = min(
            _h(_return(packet, m, "intact", arm), DELTA_C)
            for arm in TRAINED_ARMS for m in (n, 9, 15)
        )
        a_zone = min(
            _h(_zone(packet, n, "intact", arm, zone), DELTA_Z)
            for arm in TRAINED_ARMS for zone in ("WEST", "EAST")
        )
        a_cut = min(
            _h(_return(packet, n, condition, "PHY-TRUST"), DELTA_CUT_R)
            for condition in ("intact", "rotated")
        )
        a_atten = min(
            _h(_return(packet, n, condition, arm), DELTA_I)
            for arm in TRAINED_ARMS for condition in ("intact", "rotated")
        )
        a_tv = _tv_support(packet, n) - DELTA_TV
        out[f"A({n})"] = min(a_dir, a_interaction, a_zone, a_cut, a_atten, a_tv)

    expected = {
        *(f"d({n})" for n in ALL_SIZES),
        *(f"e({n})" for n in TRAIN_SIZES),
        *(f"c({n})" for n in HELDOUT_SIZES),
        *(f"z({n})" for n in HELDOUT_SIZES),
        *(f"{name}({n})" for n in HELDOUT_SIZES for name in ("C_PHY", "V", "I")),
        *(f"A({n})" for n in HELDOUT_SIZES),
    }
    if set(out) != expected or len(out) != FAMILY_SIZE:
        raise AssertionError("the registered simultaneous family must contain exactly 18 quantities")
    return out


def _default_packet_valid(packet: Mapping[str, Any]) -> bool:
    try:
        evaluation = _evaluation(packet)
        seed = int(evaluation["seed"])
        if packet["revision"] != REVISION or packet["action"] != ACTION:
            return False
        if int(packet["seed"]) != seed or packet["arms"] != list(TRAINED_ARMS):
            return False
        if packet["atomic_payload_complete"] is not True:
            return False
        if packet["checkpoint_identity"] != "only_evaluable_state_immediately_after_update_512":
            return False
        if packet["worlds_and_agents_are_inferential_replicates"] is not False:
            return False
        if packet["seed_is_inferential_unit"] is not True:
            return False
        lease_digest = packet["production_lease_token_sha256"]
        if not isinstance(lease_digest, str) or len(lease_digest) != 64:
            return False
        int(lease_digest, 16)
        training = packet["training"]
        if int(training["seed"]) != seed or int(training["completed_updates"]) != 512:
            return False
        if training["checkpoint"] != "immediately_after_update_512":
            return False
        if evaluation.get("frozen_checkpoint") != "immediately_after_update_512":
            return False
        if evaluation.get("evaluation_updates") != 0:
            return False
        if evaluation.get("heldout_training_or_adaptation") is not False:
            return False
        if evaluation.get("greedy_evaluation") is not False:
            return False
        if int(evaluation.get("seed", seed)) != seed:
            return False
        if evaluation["registered_rosters"] != [6, 9, 15, 21]:
            return False
        if int(evaluation["worlds_per_roster"]) != 256:
            return False
        if evaluation["arm_independent_world_and_action_coordinates"] is not True:
            return False
        if evaluation["episode_rows_retained"] is not False:
            return False
        if evaluation["seed_is_inferential_unit"] is not True:
            return False
        if evaluation["rotated_panels_only_at_heldout_rosters"] is not True:
            return False
        if evaluation["shadow_cut_only_at_heldout_rosters"] is not True:
            return False
        if evaluation["uniform_legal_only_at_training_rosters"] is not True:
            return False
        if set(evaluation["cells"]) != {"6", "9", "15", "21"}:
            return False
        for n in ALL_SIZES:
            cell = _cell(packet, n)
            if int(cell["n"]) != n or int(cell["world_count"]) != 256:
                return False
            support = cell["registered_support"]
            if support != {
                "basin_count": 2,
                "events_per_basin": 3,
                "public_role_count": 3,
                "agents_per_role": n // 3,
                "balanced_positive_role_support": True,
                "fixed_legal_masks": True,
            }:
                return False
            if set(cell["intact"]) != set(TRAINED_ARMS):
                return False
            if n in TRAIN_SIZES and set(cell["uniform"]) != {"UNIFORM-LEGAL"}:
                return False
            if n in HELDOUT_SIZES and cell["uniform"] != {}:
                return False
            if n in HELDOUT_SIZES:
                if set(cell["rotated"]) != set(TRAINED_ARMS):
                    return False
                if set(cell["shadow"]) != {"PHY-TRUST"}:
                    return False
                shadow = cell["shadow"]["PHY-TRUST"]
                if int(shadow["history_count"]) != 256 * 12 * n:
                    return False
                if shadow["shadow_state_propagated"] is not False:
                    return False
                if shadow["intact_observations_and_incoming_hidden_fixed"] is not True:
                    return False
                shadow_tv = _float(shadow["mean_legal_action_tv"])
                tv_support = _float(shadow["mean_tv_support"])
                if not (0.0 <= shadow_tv <= 1.0 and 0.0 <= tv_support <= 1.0):
                    return False
            elif cell["rotated"] != {} or cell["shadow"] != {}:
                return False
            panels = [*cell["intact"].values(), *cell["uniform"].values()]
            if n in HELDOUT_SIZES:
                panels.extend(cell["rotated"].values())
            for panel in panels:
                if int(panel["world_count"]) != 256:
                    return False
                mean_return = _float(panel["mean_return"])
                west = _float(panel["mean_timely_delivery_by_basin"]["WEST"])
                east = _float(panel["mean_timely_delivery_by_basin"]["EAST"])
                if not all(0.0 <= value <= 1.0 for value in (mean_return, west, east)):
                    return False
        deterministic = packet["deterministic_checkpoint_audit"]
        structural = packet["structural_checkpoint_audit"]
        if deterministic["passed"] is not True or structural["passed"] is not True:
            return False
        seed_quantities(packet)
        return True
    except (KeyError, TypeError, ValueError, OverflowError, AssertionError):
        return False


def analyze_packets(
    packets: Sequence[Mapping[str, Any]],
    *,
    packet_validator: Callable[[Mapping[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Apply the exact structural/answerability/competence/branch precedence."""
    validator = packet_validator or _default_packet_valid
    if len(packets) != SEED_COUNT:
        return {
            "complete_atomic_evidence": False,
            "hard_structural_validity": False,
            "decision": "NO_SCIENTIFIC_RELATION",
            "branch": "INVALID_INCOMPLETE_OR_CONTAMINATED",
            "reason": "exactly 24 complete independent seed blocks are required",
        }
    try:
        seeds = [int(_evaluation(packet)["seed"]) for packet in packets]
    except (KeyError, TypeError, ValueError):
        seeds = []
    if seeds != list(REGISTERED_SEEDS) or not all(
        validator(packet) for packet in packets
    ):
        return {
            "complete_atomic_evidence": len(packets) == SEED_COUNT,
            "hard_structural_validity": False,
            "decision": "NO_SCIENTIFIC_RELATION",
            "branch": "INVALID_INCOMPLETE_OR_CONTAMINATED",
            "reason": "one or more atomic seed packets failed the registered structural contract",
        }

    try:
        by_seed = [seed_quantities(packet) for packet in packets]
    except (KeyError, TypeError, ValueError, OverflowError, AssertionError) as error:
        return {
            "complete_atomic_evidence": True,
            "hard_structural_validity": False,
            "decision": "NO_SCIENTIFIC_RELATION",
            "branch": "INVALID_INCOMPLETE_OR_CONTAMINATED",
            "reason": f"registered seed quantity unavailable: {error}",
        }
    names = list(by_seed[0])
    intervals = {
        name: _interval([quantities[name] for quantities in by_seed])
        for name in names
    }
    if len(intervals) != FAMILY_SIZE or not all(value["valid"] is True for value in intervals.values()):
        return {
            "complete_atomic_evidence": True,
            "hard_structural_validity": False,
            "decision": "NO_SCIENTIFIC_RELATION",
            "branch": "INVALID_INCOMPLETE_OR_CONTAMINATED",
            "reason": "the exact 18-member finite paired-seed interval family was unavailable",
            "intervals": intervals,
        }

    answerability = {
        n: float(intervals[f"A({n})"]["lower"]) > 0.0 for n in HELDOUT_SIZES
    }
    competence_floor = {
        n: float(intervals[f"e({n})"]["lower"]) > EDGE_FLOOR for n in TRAIN_SIZES
    }
    train_equivalence = {
        n: (
            float(intervals[f"d({n})"]["lower"]) >= -DELTA_R
            and float(intervals[f"d({n})"]["upper"]) <= DELTA_R
        )
        for n in TRAIN_SIZES
    }
    competence = all(competence_floor.values()) and all(train_equivalence.values())
    common = {
        "complete_atomic_evidence": True,
        "hard_structural_validity": True,
        "family": {
            "kind": "two-sided paired-seed Student-t Bonferroni",
            "seed_count": SEED_COUNT,
            "member_count": FAMILY_SIZE,
            "family_alpha": FAMILY_ALPHA,
            "per_quantity_alpha": FAMILY_ALPHA / FAMILY_SIZE,
            "df": SEED_COUNT - 1,
        },
        "intervals": intervals,
        "answerability": answerability,
        "edge_competence": {
            "floor": competence_floor,
            "phy_edge_training_equivalence": train_equivalence,
            "passed": competence,
        },
    }
    if not all(answerability.values()) or not competence:
        return {
            **common,
            "decision": "NONIDENTIFIED",
            "branch": "NONANSWERABLE_OR_INCOMPETENT_COMPARATOR",
            "failed_answerability_sizes": [n for n, passed in answerability.items() if not passed],
            "failed_competence_sizes": [
                n for n in TRAIN_SIZES
                if not competence_floor[n] or not train_equivalence[n]
            ],
        }

    direct_pass = all(float(intervals[f"d({n})"]["lower"]) > DELTA_R for n in HELDOUT_SIZES)
    interaction_pass = all(float(intervals[f"c({n})"]["lower"]) > DELTA_C for n in HELDOUT_SIZES)
    zone_pass = all(float(intervals[f"z({n})"]["lower"]) > DELTA_Z for n in HELDOUT_SIZES)
    attribution_pass = all(
        float(intervals[f"{name}({n})"]["lower"]) > margin
        for n in HELDOUT_SIZES
        for name, margin in (("C_PHY", DELTA_CUT_R), ("V", DELTA_TV), ("I", DELTA_I))
    )
    qualification = {
        "heldout_direct_return": direct_pass,
        "coldstart_interaction": interaction_pass,
        "worst_zone_advantage": zone_pass,
        "action_sensitive_attribution": attribution_pass,
    }
    if all(qualification.values()):
        return {
            **common,
            "qualification": qualification,
            "decision": "RETAIN_PHYSICAL_PRIOR_COLDSTART",
            "branch": "RETAIN_BOUNDED_PHYSICAL_PRIOR_COLDSTART_VALUE",
            "failed_qualification_predicates": [],
        }

    failed: list[str] = []
    if not direct_pass:
        failed.append("HELDOUT_DIRECT_RETURN_NOT_ESTABLISHED")
    if not interaction_pass:
        failed.append("COLDSTART_INTERACTION_NOT_ESTABLISHED")
    if not zone_pass:
        failed.append("WORST_ZONE_ADVANTAGE_NOT_ESTABLISHED")
    if not attribution_pass:
        failed.append("ACTION_SENSITIVE_ATTRIBUTION_NOT_ESTABLISHED")
    practical_equivalence = all(
        float(intervals[f"d({n})"]["lower"]) >= -DELTA_R
        and float(intervals[f"d({n})"]["upper"]) <= DELTA_R
        for n in HELDOUT_SIZES
    )
    edge_superior = all(
        float(intervals[f"d({n})"]["upper"]) < -DELTA_R for n in HELDOUT_SIZES
    )
    if practical_equivalence:
        failed.append("PRACTICAL_EQUIVALENCE")
    if edge_superior:
        failed.append("EDGE_MATERIALLY_SUPERIOR")
    return {
        **common,
        "qualification": qualification,
        "decision": "DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT",
        "branch": "DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT",
        "failed_qualification_predicates": failed,
        "practical_equivalence": practical_equivalence,
        "edge_materially_superior": edge_superior,
    }
