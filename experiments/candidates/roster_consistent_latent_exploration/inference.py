from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.stats import t as student_t

from .config import ARMS, COMMON_ARMS, EVAL_SIZES, REGISTERED, REVISION, SEEDS


def _all_finite(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_finite(item) for item in value)
    return True


def _bound(values: list[float], probability: float, side: str) -> dict[str, float | bool]:
    sample = np.asarray(values, dtype=np.float64)
    if sample.shape != (12,) or not bool(np.isfinite(sample).all()):
        return {"valid": False, "mean": math.nan, side: math.nan}
    mean = float(sample.mean(dtype=np.float64))
    variance = float(sample.var(ddof=1, dtype=np.float64))
    if variance == 0.0:
        return {"valid": True, "mean": mean, side: mean}
    radius = float(student_t.ppf(probability, df=11)) * math.sqrt(variance / 12.0)
    endpoint = mean - radius if side == "lower" else mean + radius
    return {"valid": math.isfinite(endpoint), "mean": mean, side: endpoint}


def _complete(packet: dict[str, Any]) -> bool:
    try:
        if (
            packet["revision"] != REVISION
            or packet["arms"] != list(ARMS)
            or packet["atomic_payload_complete"] is not True
            or packet["training"]["updates_completed"] != REGISTERED.train_updates
            or packet["training"]["training_episodes"]
            != len(ARMS) * len((4, 8)) * REGISTERED.train_updates * 16
            or packet["evaluation"]["ordinary_episodes"]
            != len(ARMS) * len(EVAL_SIZES) * REGISTERED.eval_campaigns_per_size * 4
            or packet["evaluation"]["cut_episodes"]
            != 2 * len(EVAL_SIZES) * REGISTERED.eval_campaigns_per_size * 4
            or packet["evaluation"]["evaluation_updates"] != 0
            or packet["evaluation"]["selected_latents"] is not False
            or packet["evaluation"]["greedy_decoding"] is not False
            or packet["certificate_passed"] is not True
            or not _all_finite(packet["evaluation"])
        ):
            return False
        for n in EVAL_SIZES:
            for arm in ARMS:
                cell = packet["evaluation"]["cells"][str(n)][arm]
                if cell["campaigns"] != REGISTERED.eval_campaigns_per_size:
                    return False
                if cell["episodes"] != REGISTERED.eval_campaigns_per_size * 4:
                    return False
                if sum(cell["route_histogram"]) != cell["episodes"] * n:
                    return False
                if sum(cell["relative_rotation_histogram"]) != cell["episodes"] * n:
                    return False
                if arm in COMMON_ARMS:
                    semantic = cell["common_semantics"]
                    if semantic["semantic_denominator"] != [2048, 2048, 2048, 2048]:
                        return False
                    if n == 4 and (
                        semantic["anchor_denominator"] != [1024, 1024, 1024, 1024]
                        or semantic["scoring_denominator"] != [1024, 1024, 1024, 1024]
                    ):
                        return False
            for cut in ("PRIVATE-LATENT-CUT", "TEMPORAL-LATENT-CUT"):
                if packet["evaluation"]["cuts"][str(n)][cut]["campaigns"] != 2048:
                    return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def _posterior_restriction(packet: dict[str, Any]) -> bool:
    try:
        if packet["training"]["invalid_posterior_symbols"] != 0:
            return False
        if packet["training"]["posterior_invalid_fixed_uniform"] is not True:
            return False
        for arm in ARMS:
            values = np.asarray(
                packet["evaluation"]["posterior_probabilities"][arm], dtype=np.float64,
            )
            if values.shape != (4, 4) or not np.isfinite(values).all():
                return False
            if not np.allclose(values.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def analyze_packets(packets: list[dict[str, Any]]) -> dict[str, Any]:
    exact_order = len(packets) == len(SEEDS) and [packet.get("seed") for packet in packets] == list(SEEDS)
    completeness = exact_order and all(_complete(packet) for packet in packets)
    posterior_ok = completeness and all(_posterior_restriction(packet) for packet in packets)
    if not completeness:
        return {
            "revision": REVISION,
            "complete_panel": False,
            "completeness_ok": False,
            "branch": "INVALID_OR_INCOMPLETE",
            "reason": "all 12 exact atomic seed packets and registered panels are required",
        }

    contrasts: dict[str, list[float]] = {}
    names = {
        "COMMON": "COMMON-Z",
        "SHUFFLED": "SHUFFLED-MI",
        "INDEP": "INDEPENDENT-ENTROPY",
    }
    for name, arm in names.items():
        contrasts[name] = [
            float(packet["evaluation"]["cells"]["12"]["RCLE"]["campaign_task_value"])
            - float(packet["evaluation"]["cells"]["12"][arm]["campaign_task_value"])
            for packet in packets
        ]
    primary: dict[str, Any] = {}
    for name, values in contrasts.items():
        positive = _bound(values, 1.0 - 0.05 / 3.0, "lower")
        no_material = _bound(values, 0.95, "upper")
        if positive["valid"] and float(positive["lower"]) > REGISTERED.positive_margin:
            label = f"POS_{name}"
        elif no_material["valid"] and float(no_material["upper"]) < REGISTERED.no_material_margin:
            label = f"NO_MAT_{name}"
        else:
            label = f"UNRES_{name}"
        primary[name] = {
            "per_seed": values,
            "positive_bound": positive,
            "no_material_bound": no_material,
            "classification": label,
        }
    primary_positive = all(primary[name]["classification"] == f"POS_{name}" for name in names)

    maps: dict[str, list[int]] = {}
    per_seed_unique_bijection: dict[str, bool] = {}
    fidelity_values: dict[str, list[float]] = {
        f"z{z}|N{n}": [] for z in range(4) for n in EVAL_SIZES
    }
    for packet in packets:
        seed_key = str(packet["seed"])
        anchor = np.asarray(
            packet["evaluation"]["cells"]["4"]["RCLE"]["common_semantics"]["anchor_counts"],
            dtype=np.int64,
        )
        maxima = anchor.argmax(axis=1).tolist()
        unique_rows = all(int((anchor[z] == anchor[z].max()).sum()) == 1 for z in range(4))
        bijection = sorted(maxima) == [0, 1, 2, 3]
        maps[seed_key] = [int(value) for value in maxima]
        per_seed_unique_bijection[seed_key] = bool(unique_rows and bijection)
        for n in EVAL_SIZES:
            semantic = packet["evaluation"]["cells"][str(n)]["RCLE"]["common_semantics"]
            counts_key = "scoring_counts" if n == 4 else "semantic_counts"
            denominator_key = "scoring_denominator" if n == 4 else "semantic_denominator"
            counts = np.asarray(semantic[counts_key], dtype=np.int64)
            denominator = np.asarray(semantic[denominator_key], dtype=np.int64)
            for z in range(4):
                fidelity_values[f"z{z}|N{n}"].append(
                    int(counts[z, maxima[z]]) / int(denominator[z])
                )
    fidelity_bounds = {
        key: _bound(values, 1.0 - 0.05 / 12.0, "lower")
        for key, values in fidelity_values.items()
    }
    codebook_supported = all(per_seed_unique_bijection.values()) and all(
        bound["valid"] and float(bound["lower"]) > REGISTERED.fidelity_margin
        for bound in fidelity_bounds.values()
    )

    private_cut = [
        float(packet["evaluation"]["cells"]["12"]["RCLE"]["campaign_task_value"])
        - float(packet["evaluation"]["cuts"]["12"]["PRIVATE-LATENT-CUT"]["campaign_task_value"])
        for packet in packets
    ]
    temporal_cut = [
        float(packet["evaluation"]["cells"]["12"]["RCLE"]["campaign_task_value"])
        - float(packet["evaluation"]["cuts"]["12"]["TEMPORAL-LATENT-CUT"]["campaign_task_value"])
        for packet in packets
    ]
    cut_bounds = {
        "PRIVATE-LATENT-CUT": _bound(private_cut, 0.95, "lower"),
        "TEMPORAL-LATENT-CUT": _bound(temporal_cut, 0.95, "lower"),
    }
    cuts_ok = (
        cut_bounds["PRIVATE-LATENT-CUT"]["valid"]
        and float(cut_bounds["PRIVATE-LATENT-CUT"]["lower"]) > REGISTERED.private_cut_margin
        and cut_bounds["TEMPORAL-LATENT-CUT"]["valid"]
        and float(cut_bounds["TEMPORAL-LATENT-CUT"]["lower"]) > REGISTERED.temporal_cut_margin
    )
    support_ok = all(packet["support_headroom_invariance_ok"] is True for packet in packets)
    mechanism_supported = bool(
        primary_positive and codebook_supported and cuts_ok and posterior_ok
        and support_ok and completeness
    )
    zero_learned_validity = all(
        packet["evaluation"]["cells"][str(n)][arm]["validity"] == 0.0
        for packet in packets for n in EVAL_SIZES for arm in ARMS
    )

    if not (posterior_ok and support_ok):
        branch = "INVALID_OR_INCOMPLETE"
    elif zero_learned_validity:
        branch = "ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY"
    elif mechanism_supported:
        branch = "MECHANISM_SUPPORTED"
    elif primary_positive:
        branch = "BOUNDED_PACKAGE_EFFECT_ONLY"
    else:
        branch = "CONTRAST_SPECIFIC_RESULTS_ONLY"

    return {
        "revision": REVISION,
        "complete_panel": True,
        "completeness_ok": completeness,
        "posterior_restriction_ok": posterior_ok,
        "support_headroom_invariance_ok": support_ok,
        "primary": primary,
        "primary_positive": primary_positive,
        "anchored_maps": maps,
        "per_seed_unique_bijection": per_seed_unique_bijection,
        "fidelity_per_seed": fidelity_values,
        "fidelity_bounds": fidelity_bounds,
        "codebook_supported": codebook_supported,
        "cut_per_seed": {
            "PRIVATE-LATENT-CUT": private_cut,
            "TEMPORAL-LATENT-CUT": temporal_cut,
        },
        "cut_bounds": cut_bounds,
        "cuts_ok": cuts_ok,
        "mechanism_supported": mechanism_supported,
        "oracle_headroom_with_zero_learned_validity": zero_learned_validity,
        "branch": branch,
        "seed_is_inferential_unit": True,
        "campaign_is_inferential_unit": False,
    }
