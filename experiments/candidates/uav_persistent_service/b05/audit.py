"""Saved-decision diagnostics, with no environment or counterfactual execution."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from .readout import HORIZON, QOS, SEEDS


def stats(values):
    values = np.asarray(values, dtype=float)
    return {"count": int(values.size), "mean": float(values.mean()) if values.size else None,
            "median": float(np.median(values)) if values.size else None,
            "min": float(values.min()) if values.size else None,
            "max": float(values.max()) if values.size else None,
            "mean_absolute": float(np.abs(values).mean()) if values.size else None}


def world_reading(decisions: dict, raw) -> dict:
    qos = np.asarray(raw["metrics"][:, QOS], dtype=float)
    if not decisions["complete"] or len(qos) != HORIZON:
        raise ValueError("diagnostic requires a complete recorded mission")
    counts = Counter()
    reasons = Counter()
    one_clock_errors = []
    release_errors = []
    starts = []
    commitments = {(row["start"], row["member"]): row for row in decisions["commitments"]}
    for macro in decisions["macros"]:
        step = int(macro["macro_start"])
        choice = macro["choice"]
        item = choice["scheduler"]
        counts["clocks"] += 1
        if item["fallback"] is not None:
            counts["fallbacks"] += 1
            continue
        weights = np.asarray(item["weights"], dtype=float)
        scores = {row["action"]: tuple(row["score"]) for row in item["candidate_scores"]}
        selected, reference = item["executed_action"], item["r_action"]
        if selected not in scores or reference not in scores or len(weights) != 8:
            raise ValueError("recorded choice/weight contract differs")
        zero_weights = bool(np.all(weights == 0))
        service_tied = len({score[1:3] for score in scores.values()}) == 1
        multiple = len(scores) > 1
        counts["all_zero_weight_clocks"] += zero_weights
        counts["q0_equal_one_clocks"] += item["q0"] == 1
        counts["multiple_candidate_clocks"] += multiple
        counts["multiple_candidate_all_zero_weight_clocks"] += multiple and zero_weights
        counts["multiple_candidate_service_score_tied_clocks"] += multiple and service_tied
        changed = selected != reference
        counts["changed_clocks"] += changed
        counts["changed_all_zero_weight_clocks"] += changed and zero_weights
        if changed:
            difference = next((i for i, (a, b) in enumerate(zip(scores[selected], scores[reference]))
                               if a != b), None)
            if difference is None or scores[selected] >= scores[reference]:
                raise ValueError("changed choice does not beat the recorded R score")
            reasons[("risk", "minimum_qhat", "integrated_qhat", "reserve")[difference]] += 1
        deferred = item["defer"]["transfer_access_now"] and selected == 0
        counts["deferred_transfer_clocks"] += deferred
        counts["deferred_with_predicted_access_loss"] += deferred and item["defer"]["predicted_access_loss"]
        forecast = item["chosen_forecast"]
        endpoint = min(step + 30, HORIZON) - 1
        one_clock_errors.append(float(forecast["qhat"][0]) - float(qos[endpoint]))
        if selected == 0:
            continue
        member = int(choice["member"])
        observed = commitments[(step, member)]
        predicted_release = forecast["release"][member]
        predicted_ready = forecast["readiness"][member]
        released = observed["end_kind"] == "release"
        actual_release = observed["stop"] - step if released else None
        error = (predicted_release - actual_release
                 if predicted_release is not None and actual_release is not None else None)
        if error is not None:
            release_errors.append(error)
        counts["chosen_starts"] += 1
        counts["chosen_starts_all_zero_weight"] += zero_weights
        counts["predicted_release_missing"] += predicted_release is None
        counts["observed_release_missing"] += not released
        counts["predicted_readiness_missing"] += predicted_ready is None
        counts["charging_without_geometric_arrival"] += (observed["allocated_charging_steps"] > 0
                                                          and observed["first_geometric_arrival"] is None)
        starts.append({"step": step, "member": member, "action": selected,
                       "r_action_at_s_state": reference, "all_zero_weights": zero_weights,
                       "predicted_release_delay_s": predicted_release,
                       "observed_release_delay_s": actual_release,
                       "release_error_s": error, "release_reason": observed["release_reason"],
                       "predicted_nominal_readiness_delay_s": predicted_ready,
                       "observed_assignment_step": observed["assignment_restored"],
                       "observed_connected_load_step": observed["first_post_release_connected_load"],
                       "observed_arrival_step": observed["first_geometric_arrival"],
                       "allocated_charging_steps": observed["allocated_charging_steps"]})
    if counts["clocks"] != 400 or counts["chosen_starts"] != len(commitments):
        raise ValueError("recorded clocks or commitment starts differ")
    return {"counts": dict(counts), "changed_choice_first_decisive_score": dict(reasons),
            "one_clock_qhat_minus_native_qos": stats(one_clock_errors),
            "release_prediction_minus_observed_seconds": stats(release_errors),
            "starts": starts}


def audit(root: Path) -> dict:
    worlds = {}
    bindings = {}
    for seed in SEEDS:
        decision_path = root / f"raw/S_{seed}.decisions.json"
        raw_path = root / f"raw/S_{seed}.npz"
        bindings[str(seed)] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (decision_path, raw_path)}
        with np.load(raw_path, allow_pickle=False) as raw:
            worlds[str(seed)] = world_reading(json.loads(decision_path.read_text()), raw)
    counts, reasons = Counter(), Counter()
    for row in worlds.values():
        counts.update(row["counts"])
        reasons.update(row["changed_choice_first_decisive_score"])
    errors = [start["release_error_s"] for row in worlds.values() for start in row["starts"]
              if start["release_error_s"] is not None]
    return {"scope": "complete saved S artifacts; no simulation, fit or counterfactual policy execution",
            "definitions": {
                "weights": "exact zero at current nominal full-fleet radio snapshot, not zero actual service value",
                "decision_reason": "first differing lexicographic score versus R action at the actual S state",
                "one_clock_error": "qhat at first 30-second endpoint minus native QoS at that endpoint; dynamic users/P10 and coarse model differ",
                "release_error": "initial chosen forecast minus observed release; later decisions can change charging competition",
                "readiness": "nominal deployment readiness is not assignment restoration or connected load; timestamps are retained separately, not treated as identical targets",
                "connected_load": "native connected-load post-transition index; F may remain active; not satisfied QoS or necessarily free deployment",
                "uncertainty": "clock/start summaries are descriptive repeated observations, not independent-world confidence intervals"},
            "artifact_sha256": bindings, "counts": dict(counts),
            "changed_choice_first_decisive_score": dict(reasons),
            "release_prediction_minus_observed_seconds": stats(errors), "worlds": worlds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.root), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
