"""Scalar reconstruction of the unchanged 818b2566 origin-certificate conjunction."""

import json
import math
import time

HOST = "GROUND-TERMINAL-LINEAR-CLEARANCE-A03"
ORIGINS = (340, 364, 388, 596)
CLOSE = 1e-10
CAP_SECONDS = 60.0


def number(value):
    if math.isfinite(value):
        return value
    if math.isnan(value):
        return "NaN"
    return "positive_infinity" if value > 0 else "negative_infinity"


def predictive_q95(values):
    dp = [0.0] * 21
    dp[0] = 1.0
    probabilities = []
    for j in range(20):
        p = float(values[j])
        if p < 1e-6:
            p = 1e-6
        elif 1.0 - 1e-6 < p:
            p = 1.0 - 1e-6
        probabilities.append(p)
        for m in range(j + 1, -1, -1):
            keep = dp[m] * (1.0 - p)
            add = dp[m - 1] * p if m > 0 else 0.0
            dp[m] = keep + add
    tails = []
    selected = None
    for m in range(20, -1, -1):
        tail = 0.0
        for k in range(m, 21):
            tail += dp[k]
        passed = tail >= 0.95
        if selected is None and passed:
            selected = m / 20.0
        tails.append({"m": m, "tail": number(tail), "threshold": 0.95,
                      "signed_distance": number(tail - 0.95), "passes": passed,
                      "numerically_close": abs(tail - 0.95) <= CLOSE})
    return {"q95": selected if selected is not None else 0.0,
            "clipped_probabilities": probabilities, "dp": [number(v) for v in dp],
            "tails_descending_m": tails}


def mahalanobis_position(mean, covariance):
    dx = float(mean[0]) - float(mean[4])
    dy = float(mean[1]) - float(mean[5])
    s00 = float(covariance[0]) + float(covariance[16]) + 1e-6
    s01 = float(covariance[1]) + float(covariance[17])
    s11 = float(covariance[5]) + float(covariance[21]) + 1e-6
    det = s00 * s11 - s01 * s01
    dm = ((dx * dx * s11 - 2 * dx * dy * s01 + dy * dy * s00) / det
          if det > 0 and math.isfinite(det) else float("inf"))
    return dm, {"dx": number(dx), "dy": number(dy), "s00": number(s00),
                "s01": number(s01), "s11": number(s11), "det": number(det), "value": number(dm)}


def norm(x, y):
    return math.sqrt(x * x + y * y)


def clipped(x, y):
    n = norm(x, y)
    if n <= 3.0 or n <= 1e-12:
        return x, y
    q = 3.0 / n
    return x * q, y * q


def comparison(name, group, value, threshold, operator, discrete=False):
    if operator == ">=":
        passed = value >= threshold
    elif operator == "<=":
        passed = value <= threshold
    else:
        passed = value == threshold
    distance = value - threshold
    return {"name": name, "group": group, "value": number(value), "threshold": threshold,
            "operator": operator, "passes": passed, "signed_distance": number(distance),
            "numerically_close": not discrete and abs(distance) <= CLOSE, "discrete": discrete}


def reconstruct(origin, following):
    prepared = origin["prepared"]
    completed = origin["completion"]["native"]
    inputs = origin["policy_output"]
    dm, dm_details = mahalanobis_position(inputs["prediction_mean"], inputs["prediction_covariance"])
    q = predictive_q95(inputs["service_q"])
    p = prepared["p"]
    separation = math.hypot(float(p[0]) - float(p[2]), float(p[1]) - float(p[3]))
    state_group = "state/support"
    prediction_group = "prediction/service-confidence"
    physical_group = "physical/action"
    predicates = [
        comparison("renewal", state_group, int(origin["arrivals"]["renewal"]), 1, "==", True),
        comparison("handover_unused", state_group, prepared["handover_used"], 0, "==", True),
        comparison("preparation_latched", state_group, int(bool(completed["prepare_latched"])), 1, "==", True),
        comparison("warmup", state_group, completed["warmup"], 10, ">=", True),
        comparison("source_u0_exists", state_group, int(bool(prepared["source_exists"][0])), 1, "==", True),
        comparison("source_u1_exists", state_group, int(bool(prepared["source_exists"][1])), 1, "==", True),
        comparison("source_sequence_match", state_group, prepared["source_sequence"][0], prepared["source_sequence"][1], "==", True),
        comparison("nonterminal", state_group, prepared["terminal"], 0, "==", True),
        comparison("mahalanobis_finite", prediction_group, int(math.isfinite(dm)), 1, "==", True),
        comparison("mahalanobis_limit", prediction_group, dm, 5.99, "<="),
        comparison("predictive_q95", prediction_group, q["q95"], 0.60, ">="),
        comparison("separation", physical_group, separation, 15.0, ">="),
    ]
    commands = []
    for i in range(2):
        raw_x, raw_y = float(inputs["raw_action"][2 * i]), float(inputs["raw_action"][2 * i + 1])
        bounded_x, bounded_y = clipped(raw_x, raw_y)
        held_x, held_y = float(completed["a"][2 * i]), float(completed["a"][2 * i + 1])
        distance = norm(bounded_x - held_x, bounded_y - held_y)
        commands.append({"physical_uav": i, "raw": [raw_x, raw_y],
                         "bounded_raw": [number(bounded_x), number(bounded_y)],
                         "post_projection_held": [held_x, held_y], "norm": number(distance)})
        predicates.append(comparison(f"command_u{i}", physical_group, distance, 1.5 + 1e-12, "<="))
    reconstructed = all(row["passes"] for row in predicates)
    recorded = bool(completed["intent_certificate"])
    failed = [row for row in predicates if not row["passes"]]
    non_close_failed = [row["name"] for row in failed if not row["numerically_close"]]
    next_prepared = following["prepared"]
    next_completed = following["completion"]["native"]
    return {
        "origin_tick": origin["action_tick"], "following_tick": following["action_tick"],
        "observed_identity": {"host": origin["host"], "owner": prepared["owner"],
                              "initial_owner": prepared["initial_owner"],
                              "intent_owner": completed["intent_owner"], "intent_origin_tick": completed["intent_origin_tick"]},
        "observed_inputs": {"renewal": origin["arrivals"]["renewal"], "countdown": prepared["countdown"],
                            "prepared_positions": p, "post_increment_latch": completed["prepare_latched"],
                            "post_increment_warmup": completed["warmup"], "policy_output": inputs},
        "mahalanobis": dm_details, "predictive_service": q, "commands": commands,
        "predicates_native_order": predicates, "failed_predicates": [row["name"] for row in failed],
        "failed_groups": list(dict.fromkeys(row["group"] for row in failed)),
        "non_close_failed_predicates": non_close_failed,
        "recorded_certificate": recorded, "reconstructed_certificate": reconstructed,
        "boolean_match": recorded == reconstructed,
        "following_native_rejection": {"application_reason": next_completed["application_reason"],
                                       "invalid_commit_delta": next_completed["invalid_commit"] - next_prepared["invalid_commit"]},
    }


def read_trace(trace, deadline):
    wanted = set(ORIGINS) | {tick + 1 for tick in ORIGINS}
    selected = {}
    with trace.open(encoding="utf-8") as stream:
        for line in stream:
            if time.perf_counter() >= deadline:
                raise RuntimeError("incomplete A04: 60-second cap reached reading trace")
            record = json.loads(line)
            if record["host"] == HOST and record["action_tick"] in wanted:
                selected[record["action_tick"]] = record
    rows = [reconstruct(selected[tick], selected[tick + 1]) for tick in ORIGINS]
    matches = all(row["boolean_match"] for row in rows)
    supported = all(row["non_close_failed_predicates"] for row in rows if not row["recorded_certificate"])
    return {
        "object": "DISH-ORIGIN-CERTIFICATE-A04", "host": HOST, "seed": 11, "origins": rows,
        "result": "A04-RECORDED-REJECTION-RECONSTRUCTED" if matches and supported else "A04-RECONSTRUCTION-DISCREPANCY",
        "discrepancy": {"boolean_mismatch": not matches, "only_close_boundary_support": matches and not supported},
        "coordinate_reference": "CM-verified original seed11/panel0 retained A03 trace; coordinate is not a per-tick trace field",
        "comparison_convention": "signed_distance=value-threshold; close means abs(distance)<=1e-10, never threshold relaxation",
        "new_exposure": {"trace_reads": 1, "origin_reconstructions": 4, "following_comparisons": 4,
                         "native_prepared_ticks": 0, "native_completed_ticks": 0, "models_initialized": 0,
                         "policies_initialized": 0, "optimizers_initialized": 0, "training_transitions": 0,
                         "learner_updates": 0, "optimizer_steps": 0, "parameter_displacement": None},
    }
