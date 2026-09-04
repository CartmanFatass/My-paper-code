"""Exact df=17 simultaneous inference and exhaustive first-true result map."""

from __future__ import annotations

import math
from typing import Final, Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t

from .evaluation import CONTROLLERS


N: Final[int] = 18
DF: Final[int] = 17
ALPHA: Final[float] = 0.05
COMPETENCE_FAMILY_MEMBERS: Final[int] = 15
SUPPORT_FAMILY_MEMBERS: Final[int] = 3
DIRECT_FAMILY_MEMBERS: Final[int] = 17
COMPETENCE_KEYS: Final[tuple[str, ...]] = (
    "fixed-4/RG", "fixed-4/GR", "fixed-10/RG", "fixed-10/GR", "pooled"
)
QUALIFICATION_CONTROLLERS: Final[tuple[str, ...]] = ("TREAT", "FREE", "SET")
VALIDITY_FLAGS: Final[tuple[str, ...]] = (
    "atomic_panel_complete",
    "identity_conformance",
    "pairing_conformance",
    "event_slot_equality",
    "public_aliasing",
    "event_noncommutation",
    "strict_containment",
    "tied_reversal",
    "set_invariance",
    "shared_parameter_external_k",
    "equal_opportunity",
    "endpoint_conformance",
    "simultaneous_family_conformance",
    "no_per_k_parameter_or_update",
    "no_post_absorption_policy_query",
)


class InferenceContractError(RuntimeError):
    pass


def _finite_vector(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (N,) or not np.all(np.isfinite(array)):
        raise InferenceContractError("registered inference vector must contain 18 finite values")
    return array


def one_sided_lower_bound(values: Sequence[float], *, family_members: int) -> dict[str, float]:
    array = _finite_vector(values)
    if family_members <= 0:
        raise ValueError("family_members must be positive")
    probability = 1.0 - ALPHA / family_members
    quantile = float(student_t.ppf(probability, df=DF))
    mean = float(np.mean(array))
    sample_sd = float(np.std(array, ddof=1))
    lower = mean - quantile * sample_sd / math.sqrt(N)
    return {
        "mean": mean,
        "sample_sd": sample_sd,
        "n": float(N),
        "df": float(DF),
        "family_members": float(family_members),
        "family_error": ALPHA,
        "quantile_probability": probability,
        "quantile": quantile,
        "lower": lower,
    }


def two_sided_interval(values: Sequence[float], *, family_members: int = DIRECT_FAMILY_MEMBERS) -> dict[str, float]:
    array = _finite_vector(values)
    probability = 1.0 - ALPHA / (2.0 * family_members)
    quantile = float(student_t.ppf(probability, df=DF))
    mean = float(np.mean(array))
    sample_sd = float(np.std(array, ddof=1))
    half_width = quantile * sample_sd / math.sqrt(N)
    return {
        "mean": mean,
        "sample_sd": sample_sd,
        "n": float(N),
        "df": float(DF),
        "family_members": float(family_members),
        "family_error": ALPHA,
        "quantile_probability": probability,
        "quantile": quantile,
        "lower": mean - half_width,
        "upper": mean + half_width,
    }


def qualification_state(lower: float, threshold: float) -> str:
    if not math.isfinite(lower):
        raise InferenceContractError("qualification bound is nonfinite")
    return "PASS" if lower > threshold else "UNRESOLVED"


def higher_better_state(interval: Mapping[str, float], margin: float) -> str:
    lower, upper = float(interval["lower"]), float(interval["upper"])
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise InferenceContractError("direct interval is nonfinite")
    if lower > margin:
        return "PASS"
    if upper <= margin:
        return "FAIL"
    return "UNRESOLVED"


def lower_better_state(interval: Mapping[str, float], margin: float) -> str:
    lower, upper = float(interval["lower"]), float(interval["upper"])
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise InferenceContractError("direct interval is nonfinite")
    if upper < margin:
        return "PASS"
    if lower >= margin:
        return "FAIL"
    return "UNRESOLVED"


def _route_state(items: Sequence[str]) -> str:
    if any(item == "FAIL" for item in items):
        return "EXCLUDED"
    if items and all(item == "PASS" for item in items):
        return "PASS"
    return "UNRESOLVED"


def _invalid(reasons: Sequence[str]) -> dict[str, object]:
    return {
        "schema": "SCDMP_UAV_SP_R02_COMPLETE_INFERENCE_V1",
        "evidence_valid": False,
        "invalid_reasons": list(reasons),
        "branch": "INVALID-EVIDENCE",
        "partial_inspection_permitted": False,
    }


def _packet_map(packets: Sequence[Mapping[str, object]]) -> dict[int, Mapping[str, object]]:
    if len(packets) != 18:
        raise InferenceContractError("atomic inference requires exactly 18 replicate packets")
    mapped: dict[int, Mapping[str, object]] = {}
    for packet in packets:
        replicate = packet.get("replicate")
        if isinstance(replicate, bool) or not isinstance(replicate, int) or replicate not in range(18):
            raise InferenceContractError("replicate packet identity is invalid")
        if replicate in mapped:
            raise InferenceContractError("replicate packet identity is duplicated")
        mapped[replicate] = packet
    if set(mapped) != set(range(18)):
        raise InferenceContractError("replicate packet inventory is incomplete")
    return mapped


def complete_inference(
    packets: Sequence[Mapping[str, object]],
    *,
    validity: Mapping[str, bool],
) -> dict[str, object]:
    """Apply only the registered families and exhaustive first-true map."""

    invalid_reasons = [flag for flag in VALIDITY_FLAGS if validity.get(flag) is not True]
    if set(validity) != set(VALIDITY_FLAGS):
        invalid_reasons.append("validity_flag_inventory_mismatch")
    try:
        mapped = _packet_map(packets)
        controller_values: dict[str, dict[str, list[float]]] = {
            controller: {name: [] for name in ("P", "W", "T", "E", "O", "G", "F")}
            for controller in CONTROLLERS
        }
        competence_values = {
            controller: {key: [] for key in COMPETENCE_KEYS}
            for controller in QUALIFICATION_CONTROLLERS
        }
        support_values = {key: [] for key in ("Q_order", "D_order", "D_action")}
        for replicate in range(18):
            packet = mapped[replicate]
            controllers = packet.get("controllers")
            support = packet.get("support")
            if not isinstance(controllers, Mapping) or set(controllers) != set(CONTROLLERS):
                raise InferenceContractError("controller endpoint inventory differs")
            if not isinstance(support, Mapping) or set(support) != set(support_values):
                raise InferenceContractError("support endpoint inventory differs")
            for key in support_values:
                value = float(support[key])
                if not math.isfinite(value):
                    raise InferenceContractError("support endpoint is nonfinite")
                support_values[key].append(value)
            for controller in CONTROLLERS:
                row = controllers[controller]
                if not isinstance(row, Mapping):
                    raise InferenceContractError("controller endpoint row is not a mapping")
                for endpoint in controller_values[controller]:
                    value = float(row[endpoint])
                    if not math.isfinite(value):
                        raise InferenceContractError("registered direct endpoint is nonfinite")
                    controller_values[controller][endpoint].append(value)
                if controller in QUALIFICATION_CONTROLLERS:
                    competence = row.get("competence")
                    if not isinstance(competence, Mapping) or set(competence) != set(COMPETENCE_KEYS):
                        raise InferenceContractError("competence endpoint inventory differs")
                    for key in COMPETENCE_KEYS:
                        value = float(competence[key])
                        if not math.isfinite(value):
                            raise InferenceContractError("competence endpoint is nonfinite")
                        competence_values[controller][key].append(value)
    except (InferenceContractError, KeyError, TypeError, ValueError, OverflowError) as error:
        invalid_reasons.append(str(error))
        return _invalid(invalid_reasons)
    if invalid_reasons:
        return _invalid(invalid_reasons)

    competence_bounds: dict[str, dict[str, object]] = {}
    competence_states: dict[str, str] = {}
    for controller in QUALIFICATION_CONTROLLERS:
        bounds: dict[str, object] = {}
        states: list[str] = []
        for key in COMPETENCE_KEYS:
            bound = one_sided_lower_bound(
                competence_values[controller][key], family_members=COMPETENCE_FAMILY_MEMBERS
            )
            threshold = 0.70 if key == "pooled" else 0.58
            state = qualification_state(bound["lower"], threshold)
            bounds[key] = {"bound": bound, "threshold": threshold, "state": state}
            states.append(state)
        competence_bounds[controller] = bounds
        competence_states[controller] = "PASS" if all(state == "PASS" for state in states) else "UNRESOLVED"

    support_thresholds = {"Q_order": 0.20, "D_order": 0.05, "D_action": 0.10}
    support_bounds: dict[str, object] = {}
    support_states: dict[str, str] = {}
    for key, threshold in support_thresholds.items():
        bound = one_sided_lower_bound(support_values[key], family_members=SUPPORT_FAMILY_MEMBERS)
        state = qualification_state(bound["lower"], threshold)
        support_bounds[key] = {"bound": bound, "threshold": threshold, "state": state}
        support_states[key] = state

    pairs: list[tuple[str, str, str]] = []
    for endpoint in ("P", "W"):
        for control in ("FREE", "REVERSED", "SET"):
            pairs.append((f"{endpoint}_T_minus_{control}", endpoint, control))
    pairs.extend((("T_T_minus_FREE", "T", "FREE"), ("E_T_minus_FREE", "E", "FREE")))
    for endpoint in ("O", "G", "F"):
        for control in ("FREE", "REVERSED", "SET"):
            pairs.append((f"{endpoint}_T_minus_{control}", endpoint, control))
    if len(pairs) != 17:
        raise AssertionError("direct family must contain exactly 17 intervals")
    direct_intervals: dict[str, dict[str, float]] = {}
    for name, endpoint, control in pairs:
        differences = [
            treatment - comparator
            for treatment, comparator in zip(
                controller_values["TREAT"][endpoint], controller_values[control][endpoint]
            )
        ]
        direct_intervals[name] = two_sided_interval(differences)

    common_qualifications = [
        competence_states["TREAT"],
        competence_states["FREE"],
        competence_states["SET"],
        support_states["Q_order"],
        support_states["D_order"],
        support_states["D_action"],
    ]
    nonharm_states = [
        lower_better_state(direct_intervals["T_T_minus_FREE"], 1.5),
        lower_better_state(direct_intervals["E_T_minus_FREE"], 0.04),
    ]
    for endpoint in ("O", "G", "F"):
        for control in ("FREE", "REVERSED", "SET"):
            nonharm_states.append(
                lower_better_state(direct_intervals[f"{endpoint}_T_minus_{control}"], 0.015)
            )

    primary_margins = {
        "P": {"FREE": 0.035, "REVERSED": 0.025, "SET": 0.025},
        "W": {"FREE": 0.045, "REVERSED": 0.035, "SET": 0.035},
    }
    route_details: dict[str, dict[str, object]] = {}
    for route_endpoint, other_endpoint in (("P", "W"), ("W", "P")):
        superiority = {
            control: higher_better_state(
                direct_intervals[f"{route_endpoint}_T_minus_{control}"],
                primary_margins[route_endpoint][control],
            )
            for control in ("FREE", "REVERSED", "SET")
        }
        noninferiority = higher_better_state(
            direct_intervals[f"{other_endpoint}_T_minus_FREE"], -0.025
        )
        items = (
            common_qualifications
            + list(superiority.values())
            + [noninferiority]
            + nonharm_states
        )
        route_details[route_endpoint] = {
            "state": _route_state(items),
            "superiority": superiority,
            "other_primary_noninferiority": noninferiority,
            "nonharm_states": list(nonharm_states),
        }

    p_state = str(route_details["P"]["state"])
    w_state = str(route_details["W"]["state"])
    if p_state == "PASS" or w_state == "PASS":
        branch = "RETAIN-TAUT-GUST-RISK-TILT"
    elif (
        p_state == "EXCLUDED"
        and w_state == "EXCLUDED"
        and competence_states["FREE"] == "PASS"
        and competence_states["SET"] == "PASS"
        and all(support_states[key] == "PASS" for key in support_states)
    ):
        branch = "DECLINE-TAUT-GUST-RISK-TILT"
    else:
        branch = "DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED"

    return {
        "schema": "SCDMP_UAV_SP_R02_COMPLETE_INFERENCE_V1",
        "evidence_valid": True,
        "invalid_reasons": [],
        "competence_family": {
            "members": 15,
            "bounds": competence_bounds,
            "controller_states": competence_states,
        },
        "support_action_family": {
            "members": 3,
            "bounds": support_bounds,
            "states": support_states,
        },
        "direct_family": {"members": 17, "intervals": direct_intervals},
        "routes": route_details,
        "branch": branch,
        "partial_inspection_permitted": False,
    }
