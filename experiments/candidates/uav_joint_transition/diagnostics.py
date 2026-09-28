"""Additional descriptive B01 audits using only saved arrays and probabilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .motion import toward


def distribution(values):
    values = np.asarray(values, dtype=np.float64)
    if not values.size:
        return {"count": 0, "minimum": None, "mean": None, "maximum": None}
    return {"count": int(values.size), "minimum": float(values.min()),
            "mean": float(values.mean()), "maximum": float(values.max())}


def probability_reading(records, training):
    direct, gaps, any_non_direct, entropy = [], [], [], []
    log_errors, argmax_non_direct = [], 0
    for record in records:
        policy = record if training else record["policy"]
        probabilities = np.asarray(policy["probabilities"], dtype=np.float64)
        eligible = np.asarray(record["eligible"], dtype=bool)
        if probabilities.shape != (8, 4) or np.any(probabilities < 0):
            raise ValueError("invalid saved mode probabilities")
        if not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=2e-7):
            raise ValueError("saved probabilities do not sum to one")
        direct.extend(probabilities[eligible, 0])
        gaps.extend(probabilities[eligible, 0] - probabilities[eligible, 1:].max(axis=1))
        argmax_non_direct += int(np.sum(np.argmax(probabilities, axis=1)[eligible] != 0))
        any_non_direct.append(policy["any_non_direct_probability"] if training
                              else policy["non_direct_probability"])
        entropy.append(policy["joint_entropy"])
        if training:
            modes = np.asarray(record["requested_modes"], dtype=np.int64)
            if np.any(modes[~eligible]):
                raise ValueError("ineligible requested mode")
            calculated = np.log(probabilities[np.arange(8), modes]).sum()
            log_errors.append(abs(calculated - policy["sampled_log_probability"]))
    if log_errors and max(log_errors) > 2e-5:
        raise ValueError("sampled log probability differs from requested labels")
    return {"clocks": len(records), "eligible_p_D": distribution(direct),
            "eligible_D_minus_best_non_D_probability": distribution(gaps),
            "eligible_argmax_non_D_members": argmax_non_direct,
            "joint_any_non_D_probability": distribution(any_non_direct),
            "joint_entropy": distribution(entropy),
            "sampled_log_probability_max_error": max(log_errors, default=None)}


def execution_reading(raw, records):
    displacement = np.diff(raw["physical_xyz_m"], axis=0)
    result = {"eligible_member_windows": 0, "eligible_alternative_mode_members": 0,
              "eligible_nominal_D_alias_mode_members": 0,
              "eligible_members_all_three_alternatives_aliased": 0,
              "requested_non_D_changed_proposal_member_ticks": 0,
              "requested_non_D_changed_submitted_member_ticks": 0,
              "requested_non_D_changed_submitted_moving_member_ticks": 0,
              "windows_at_least_two_members_with_changed_submitted_motion": 0,
              "windows_with_simultaneous_changed_submitted_motion": 0,
              "ticks_with_simultaneous_changed_submitted_motion": 0}
    score_gain, tie_travel, non_direct_clocks = [], [], 0
    for record in records:
        start = record["step"]
        stop = start + 30
        eligible = np.asarray(record["eligible"], dtype=bool)
        modes = np.asarray(record["requested_modes"])
        aliases = np.asarray(record["nominal_aliases"])
        result["eligible_member_windows"] += int(eligible.sum())
        result["eligible_alternative_mode_members"] += 3 * int(eligible.sum())
        result["eligible_nominal_D_alias_mode_members"] += int(aliases[eligible].sum())
        result["eligible_members_all_three_alternatives_aliased"] += int(np.sum(aliases[eligible] == 3))
        proposal = raw["proposal_actions"][start:stop]
        submitted = raw["submitted_actions"][start:stop]
        direct = np.zeros_like(proposal)
        direct[:, :, :3] = toward(raw["own_xyz"][start:stop],
                                  np.asarray(record["R_targets_xyz"])[None]) / [30, 30, 5]
        changed = np.any(np.abs(proposal - direct) > 1e-6, axis=2)
        changed &= (eligible & (modes != 0))[None]
        survived = changed & ~np.any(np.abs(proposal - submitted) > 1e-6, axis=2)
        moving = survived & (np.linalg.norm(displacement[start:stop], axis=2) > 1e-6)
        result["requested_non_D_changed_proposal_member_ticks"] += int(changed.sum())
        result["requested_non_D_changed_submitted_member_ticks"] += int(survived.sum())
        result["requested_non_D_changed_submitted_moving_member_ticks"] += int(moving.sum())
        result["windows_at_least_two_members_with_changed_submitted_motion"] += int(np.any(moving, axis=0).sum() >= 2)
        simultaneous = moving.sum(axis=1) >= 2
        result["windows_with_simultaneous_changed_submitted_motion"] += int(simultaneous.any())
        result["ticks_with_simultaneous_changed_submitted_motion"] += int(simultaneous.sum())
        candidates = record["candidate_scores"]
        if candidates:
            accepted = [candidate for candidate in candidates if candidate.get("accepted")]
            selected = accepted[-1] if accepted else candidates[0]
            if selected["modes"] != record["selected_modes"]:
                raise ValueError("selected ordinary history mismatch")
            delta = selected["score"] - candidates[0]["score"]
            if delta < -1e-8:
                raise ValueError("ordinary search decreased its own score")
            if np.any(modes):
                non_direct_clocks += 1
                score_gain.append(delta)
                if abs(delta) <= 1e-8:
                    tie_travel.append(selected["travel_m"] - candidates[0]["travel_m"])
    if score_gain:
        result["ordinary_non_D_clocks"] = non_direct_clocks
        result["ordinary_selected_minus_all_D_score_on_non_D_clocks"] = distribution(score_gain)
        result["ordinary_score_tied_non_D_clocks"] = len(tie_travel)
        result["ordinary_travel_delta_on_score_ties_m"] = distribution(tie_travel)
    return result


def read(out, bulk_root=None):
    out = Path(out)
    bulk = Path(bulk_root) if bulk_root is not None else out
    rows = json.loads((out / "perworld.json").read_text())
    training_rows = json.loads((out / "training_perworld.json").read_text())
    paired = {(row["arm"], row["seed"]): row for row in rows}
    identity = []
    for seed in sorted({row["seed"] for row in rows}):
        with np.load(bulk / paired["L", seed]["raw_path"], allow_pickle=False) as left:
            with np.load(bulk / paired["R", seed]["raw_path"], allow_pickle=False) as right:
                fields = sorted(set(left.files) - {"planner_records_json"})
                if set(left.files) != set(right.files):
                    raise ValueError("L/R saved array fields differ")
                unequal = [field for field in fields if left[field].dtype != right[field].dtype
                           or left[field].shape != right[field].shape
                           or left[field].tobytes() != right[field].tobytes()]
                identity.append({"seed": seed, "fields": fields, "unequal_fields": unequal,
                                 "all_array_bytes_equal": not unequal})
    perworld, eval_records = [], []
    for row in training_rows + rows:
        if row["arm"] not in ("L_train", "L", "O"):
            continue
        with np.load(bulk / row["raw_path"], allow_pickle=False) as raw:
            records = json.loads(str(raw["planner_records_json"]))
            perworld.append({"arm": row["arm"], "seed": row["seed"],
                             **execution_reading(raw, records)})
            if row["arm"] == "L":
                eval_records.extend(records)
    exposure = [json.loads(line) for line in (bulk / "training/exposure.jsonl").read_text().splitlines()]
    updates = [json.loads(line) for line in (bulk / "training/updates.jsonl").read_text().splitlines()]
    integer_fields = [key for key, value in perworld[0].items()
                      if isinstance(value, int) and key != "seed"]
    totals = {arm: {key: sum(row[key] for row in perworld if row["arm"] == arm)
                   for key in integer_fields} for arm in ("L_train", "L", "O")}
    return {"scope": "Descriptive saved-evidence audit; no environment step, fit or new policy evaluation.",
            "limitations": ["A changed submitted proposal plus nonzero displacement is not an unguarded counterfactual path effect.",
                            "Nominal aliases concern conditional single-member prediction features, not exact native equivalence.",
                            "O's surrogate improvement is relative to all-D on its own diverged state, not R's future native value.",
                            "Saved stochastic probabilities do not evaluate stochastic endpoint deployment."],
            "L_R_array_identity": identity, "training_probabilities": probability_reading(exposure, True),
            "first_200_training_probabilities": probability_reading(exposure[:200], True),
            "last_200_training_probabilities": probability_reading(exposure[-200:], True),
            "endpoint_probabilities": probability_reading(eval_records, False),
            "update_statistics": {key: distribution([row["losses"][key] for row in updates])
                                  for key in ("train/approx_kl", "train/clip_fraction", "train/explained_variance",
                                              "train/value_loss", "train/policy_gradient_loss")},
            "last_update": updates[-1], "execution_totals": totals, "perworld": perworld}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bulk-root", type=Path)
    args = parser.parse_args()
    result = read(args.out, args.bulk_root)
    (args.out / "diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"worlds": len(result["perworld"]),
                      "bitwise_L_R_worlds": sum(row["all_array_bytes_equal"] for row in result["L_R_array_identity"]),
                      "execution_totals": result["execution_totals"]}, sort_keys=True))


if __name__ == "__main__":
    main()
