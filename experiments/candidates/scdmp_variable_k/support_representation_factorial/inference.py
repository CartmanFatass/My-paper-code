from __future__ import annotations

from itertools import product

import numpy as np
from scipy.stats import t as student_t

from .config import CELLS, EFFECT_NAMES, PRACTICAL_MARGIN, SEED_INDICES


def t_interval(values: list[float], family_members: int = 3) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    coverage = 1.0 - 0.05 / family_members
    quantile_probability = 1.0 - 0.05 / (2.0 * family_members)
    if array.shape != (10,) or not np.all(np.isfinite(array)):
        return {
            "mean": float("nan"),
            "sample_sd": float("nan"),
            "df": 9.0,
            "coverage": coverage,
            "quantile_probability": quantile_probability,
            "quantile": float("nan"),
            "lower": float("nan"),
            "upper": float("nan"),
        }
    mean = float(np.mean(array))
    sample_sd = float(np.std(array, ddof=1))
    quantile = float(student_t.ppf(quantile_probability, df=9))
    half_width = quantile * sample_sd / np.sqrt(10.0)
    return {
        "mean": mean,
        "sample_sd": sample_sd,
        "df": 9.0,
        "coverage": coverage,
        "quantile_probability": quantile_probability,
        "quantile": quantile,
        "lower": mean - half_width,
        "upper": mean + half_width,
    }


def exact_sign_randomization(values: list[float]) -> dict[str, float | int]:
    effects = np.asarray(values, dtype=np.float64)
    if effects.shape != (10,) or not np.all(np.isfinite(effects)):
        return {
            "enumerations": 1_024,
            "observed_mean": float("nan"),
            "one_sided_p_positive": float("nan"),
            "one_sided_p_negative": float("nan"),
            "two_sided_p": float("nan"),
        }
    observed = float(np.mean(effects))
    statistics = np.asarray([
        np.mean(effects * np.asarray(signs, dtype=np.float64))
        for signs in product((-1.0, 1.0), repeat=10)
    ])
    tolerance = 1.0e-15
    return {
        "enumerations": 1_024,
        "observed_mean": observed,
        "one_sided_p_positive": int(np.sum(statistics >= observed - tolerance)) / 1_024.0,
        "one_sided_p_negative": int(np.sum(statistics <= observed + tolerance)) / 1_024.0,
        "two_sided_p": int(np.sum(np.abs(statistics) >= abs(observed) - tolerance)) / 1_024.0,
    }


def _measurement_reasons(cell_packets: list[dict[str, object]]) -> list[str]:
    reasons: list[str] = []
    if len(cell_packets) != 40:
        reasons.append("atomic_panel_not_exactly_40_cell_seed_packets")
        return reasons
    expected = {(seed, cell) for seed in SEED_INDICES for cell in CELLS}
    observed = [(int(packet["seed_index"]), str(packet["cell"])) for packet in cell_packets]
    if len(set(observed)) != 40 or set(observed) != expected:
        reasons.append("cell_seed_packet_identity_mismatch")
    for seed_index in SEED_INDICES:
        identities = {
            str(packet.get("evaluation_identity"))
            for packet in cell_packets
            if int(packet.get("seed_index", -1)) == seed_index
        }
        if len(identities) != 1 or any(
            len(identity) != 64
            or any(character not in "0123456789abcdef" for character in identity)
            for identity in identities
        ):
            reasons.append(f"shared_evaluation_identity_violated_seed_{seed_index}")
    for packet in cell_packets:
        seed_index = int(packet.get("seed_index", -1))
        cell = str(packet.get("cell"))
        prefix = f"seed_{seed_index}_{cell}"
        fit_support = packet.get("fit_support")
        target = packet.get("target")
        if not isinstance(fit_support, dict) or not isinstance(target, dict):
            reasons.append(f"{prefix}_registered_ratio_missing")
            continue
        fit_denominator = float(fit_support.get("E_mean", float("nan")))
        values = (
            fit_denominator,
            float(fit_support.get("ratio", float("nan"))),
            float(target.get("E_mean", float("nan"))),
            float(target.get("ratio", float("nan"))),
        )
        if not np.all(np.isfinite(values)) or fit_denominator <= 0.0 \
                or float(target.get("E_mean", float("nan"))) <= 0.0:
            reasons.append(f"{prefix}_nonfinite_or_nonpositive_registered_ratio")
        for name in ("coordinate_variance", "action_sensitivity"):
            rows = packet.get(name)
            expected_count = 27 if name == "coordinate_variance" else 3
            if not isinstance(rows, list) or len(rows) != expected_count:
                reasons.append(f"{prefix}_{name}_missing")
                continue
            for row in rows:
                if not isinstance(row, dict):
                    reasons.append(f"{prefix}_{name}_invalid")
                    break
                registered = row.get("ratio") if name == "coordinate_variance" \
                    else row.get("fraction")
                if not np.isfinite(float(registered)):
                    reasons.append(f"{prefix}_{name}_nonfinite")
                    break
    return reasons


def _factor_values(cell_packets: list[dict[str, object]]) -> dict[str, list[float]]:
    lookup = {
        (int(packet["seed_index"]), str(packet["cell"])):
            float(packet["fit_support"]["ratio"])
        for packet in cell_packets
    }
    values = {name: [] for name in EFFECT_NAMES}
    for seed_index in SEED_INDICES:
        rho00 = lookup[(seed_index, "S0R0")]
        rho10 = lookup[(seed_index, "S1R0")]
        rho01 = lookup[(seed_index, "S0R1")]
        rho11 = lookup[(seed_index, "S1R1")]
        values["S"].append(0.5 * ((rho00 - rho10) + (rho01 - rho11)))
        values["R"].append(0.5 * ((rho00 - rho01) + (rho10 - rho11)))
        values["I"].append((rho01 - rho11) - (rho00 - rho10))
    return values


def _factor_flags(interval: dict[str, float]) -> dict[str, bool]:
    lower, upper = interval["lower"], interval["upper"]
    positive = bool(lower > PRACTICAL_MARGIN)
    negative = bool(upper < -PRACTICAL_MARGIN)
    small = bool(lower > -PRACTICAL_MARGIN and upper < PRACTICAL_MARGIN)
    return {
        "POS": positive,
        "NEG": negative,
        "SMALL": small,
        "ACTIVE": positive or negative,
    }


def _target_ratio_bound(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (10,) or not np.all(np.isfinite(array)):
        return {
            "mean": float("nan"), "sample_sd": float("nan"),
            "quantile": float("nan"), "lower": float("nan"), "upper": float("nan"),
        }
    mean = float(np.mean(array))
    sample_sd = float(np.std(array, ddof=1))
    quantile = float(student_t.ppf(0.95, df=9))
    half_width = quantile * sample_sd / np.sqrt(10.0)
    return {
        "mean": mean, "sample_sd": sample_sd, "quantile": quantile,
        "lower": mean - half_width, "upper": mean + half_width,
    }


def _competence(cell_packets: list[dict[str, object]]) -> tuple[dict[str, bool], dict[str, object]]:
    vector: dict[str, bool] = {}
    diagnostics: dict[str, object] = {}
    for cell in CELLS:
        packets = [packet for packet in cell_packets if packet["cell"] == cell]
        target_values = [float(packet["target"]["ratio"]) for packet in packets]
        target_bound = _target_ratio_bound(target_values)
        target_gate = bool(
            target_bound["mean"] <= 0.85 and target_bound["upper"] < 0.95
        )
        fit_gate = all(bool(packet["fit_support"]["passed"]) for packet in packets)
        variance_gate = all(
            bool(row["passed"])
            for packet in packets for row in packet["coordinate_variance"]
        )
        sensitivity_gate = all(
            bool(row["passed"])
            for packet in packets for row in packet["action_sensitivity"]
        )
        vector[cell] = fit_gate and target_gate and variance_gate and sensitivity_gate
        diagnostics[cell] = {
            "fit_support_all_ten": fit_gate,
            "target_ratios": target_values,
            "target_ratio_bound": target_bound,
            "target_ratio_gate": target_gate,
            "coordinate_variance_all_270": variance_gate,
            "action_sensitivity_all_30": sensitivity_gate,
        }
    return vector, diagnostics


def _modifier(vector: dict[str, bool]) -> str:
    competent = [cell for cell in CELLS if vector[cell]]
    if not competent:
        return "NO-COMPETENT-CELL"
    if len(competent) == 1:
        return f"ONE-COMPETENT-CELL:{competent[0]}"
    if len(competent) == len(CELLS):
        return "ALL-CELLS-COMPETENT"
    return "MULTIPLE-COMPETENT-CELLS:" + ",".join(competent)


def complete_inference(cell_packets: list[dict[str, object]]) -> dict[str, object]:
    reasons = _measurement_reasons(cell_packets)
    if reasons:
        return {
            "measurement_valid": False,
            "measurement_reasons": reasons,
            "branch": "FACTORIAL-MEASUREMENT-NONIDENTIFICATION",
            "competence_modifier": "COMPETENCE-VECTOR-UNAVAILABLE",
            "competence_vector": None,
            "partial_inspection_permitted": False,
        }

    factor_values = _factor_values(cell_packets)
    if not all(np.all(np.isfinite(values)) for values in factor_values.values()):
        return {
            "measurement_valid": False,
            "measurement_reasons": ["nonfinite_registered_factor_effect"],
            "branch": "FACTORIAL-MEASUREMENT-NONIDENTIFICATION",
            "competence_modifier": "COMPETENCE-VECTOR-UNAVAILABLE",
            "competence_vector": None,
            "partial_inspection_permitted": False,
        }
    factors: dict[str, dict[str, object]] = {}
    for name in EFFECT_NAMES:
        interval = t_interval(factor_values[name])
        factors[name] = {
            "seed_values": factor_values[name],
            "interval": interval,
            "margin": PRACTICAL_MARGIN,
            "flags": _factor_flags(interval),
            "paired_sign_randomization": exact_sign_randomization(factor_values[name]),
        }
    support = factors["S"]["flags"]
    representation = factors["R"]["flags"]
    interaction = factors["I"]["flags"]
    if interaction["ACTIVE"]:
        branch = "INTERACTION-EFFECT"
    elif interaction["SMALL"] and support["ACTIVE"] and representation["ACTIVE"]:
        branch = "ADDITIVE-SUPPORT-AND-REPRESENTATION-EFFECTS"
    elif interaction["SMALL"] and support["ACTIVE"] and representation["SMALL"]:
        branch = "SUPPORT-EFFECT"
    elif interaction["SMALL"] and representation["ACTIVE"] and support["SMALL"]:
        branch = "REPRESENTATION-EFFECT"
    elif support["SMALL"] and representation["SMALL"] and interaction["SMALL"]:
        branch = "NO-USEFUL-FACTOR-EFFECT"
    elif support["ACTIVE"] or representation["ACTIVE"] or interaction["ACTIVE"]:
        branch = "MIXED-FACTOR-EVIDENCE"
    else:
        branch = "FACTORIAL-EFFECT-INDETERMINATE"
    competence_vector, competence_diagnostics = _competence(cell_packets)
    active_signs = {
        name: "POS" if factors[name]["flags"]["POS"]
        else "NEG" if factors[name]["flags"]["NEG"] else None
        for name in EFFECT_NAMES
    }
    return {
        "measurement_valid": True,
        "measurement_reasons": [],
        "factors": factors,
        "active_signs": active_signs,
        "branch": branch,
        "main_effect_interpretation":
            "conditional_diagnostics_only" if branch == "INTERACTION-EFFECT"
            else "registered_first_true_factorial_interpretation",
        "competence_modifier": _modifier(competence_vector),
        "competence_vector": competence_vector,
        "competence_diagnostics": competence_diagnostics,
        "partial_inspection_permitted": False,
    }
