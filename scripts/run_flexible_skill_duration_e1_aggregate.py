"""E1 study-level aggregator - per-pair differences and the contract section 5 reading.

Launch contract: `docs/Claude_docs/experiments/E1_AGE_INPUT_20260902.md` sections 5 and 6.
Reads the finished E1 run directories written by `run_flexible_skill_duration_e1.py` and
writes `E1_summary.json` at the study root.  It measures nothing itself: every number it
prints is read from a run's `e1_probe_summary.json` / `summary.json` and differenced.

Contract section 5's reading rule is applied verbatim, with the two places where its
wording leaves a choice recorded rather than resolved silently:

* **which accuracy.**  Section 5 says "probe-accuracy" without saying team or individual.
  The rule is evaluated on **both**, and both verdicts are reported.
* **"more than the across-seed spread of either".**  Read strictly, the excess must exceed
  *both* spreads (the maximum of the two); read loosely, *at least one*.  Both are
  computed; the strict reading is the one reported as the verdict.

The window is the contract's own `r >= R/2` window; the final-rollout values are reported
beside it.

Usage:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        scripts/run_flexible_skill_duration_e1_aggregate.py \
        --output-root C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E1_20260902 \
        --seeds 1 2 3 --rollouts 20
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BUCKETS = ("0-2", "3-6", "7-9")
ACCURACY_KINDS = ("team", "individual")


def resolve_run_dir(output_root: Path, arm: str, seed: int):
    """The one completed, non-quarantined run directory for `arm` at `seed`.

    A run whose first attempt was quarantined (spec 6.2) is re-run from scratch under a new
    run name, so `<arm>_seed<S>` is not always the directory that carries the observation.
    Every directory matching `<arm>_seed<S>*` is considered; a `QUARANTINED` marker or a
    `summary.json` that is absent or not `completed` disqualifies it.  Returns `None` when
    nothing qualifies, and raises when more than one directory does.
    """
    output_root = Path(output_root)
    candidates = []
    for path in sorted(output_root.glob(f"{arm}_seed{seed}*")):
        if not path.is_dir():
            continue
        if (path / "QUARANTINED").exists():
            continue
        summary_path = path / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not summary.get("completed"):
            continue
        if not (path / "e1_probe_summary.json").exists():
            continue
        candidates.append(path)
    if len(candidates) > 1:
        raise RuntimeError(
            f"more than one completed run for {arm} seed {seed}: "
            f"{[p.name for p in candidates]}"
        )
    return candidates[0] if candidates else None


def _load(run_dir: Path):
    probe = json.loads((run_dir / "e1_probe_summary.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    return probe, summary


def _accuracy(probe, kind, where):
    """`where` is "window" (mean over r >= R/2) or "final" (the last rollout)."""
    derived = probe["derived"]
    if where == "window":
        return {key: derived.get(f"{kind}_accuracy_{key}_mean_window")
                for key in ("overall",) + BUCKETS}
    final = derived.get(f"{kind}_accuracy_final") or {}
    return {key: final.get(key) for key in ("overall",) + BUCKETS}


def _difference(left, right):
    out = {}
    for key in left:
        a, b = left[key], right[key]
        out[key] = None if (a is None or b is None) else float(a - b)
    return out


def _spread(values):
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return None
    return float(max(values) - min(values))


def _range(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"min": float(min(values)), "max": float(max(values)),
            "range": float(max(values) - min(values)),
            "mean": float(np.mean(values))}


def build(output_root: Path, seeds, rollouts):
    pairs = {}
    runs = {}
    run_dirs = {}
    for seed in seeds:
        d0_dir = resolve_run_dir(output_root, "d0", seed)
        d1_dir = resolve_run_dir(output_root, "d1", seed)
        if d0_dir is None or d1_dir is None:
            continue
        run_dirs[f"seed{seed}"] = {"d0": d0_dir.name, "d1": d1_dir.name}
        d0_probe, d0_summary = _load(d0_dir)
        d1_probe, d1_summary = _load(d1_dir)
        runs[f"d0_seed{seed}"] = {
            "run_dir": d0_dir.name,
            "completed": d0_summary["completed"],
            "rollouts_completed": d0_summary["rollouts_completed"],
            "transitions_total": d0_summary["transitions_total"],
            "episodes_total": d0_summary["episodes_total"],
            "optimizer_steps_total": d0_summary["optimizer_steps_total"],
            "evaluation_count": d0_summary["evaluation_count"],
            "final_evaluation_return_mean": d0_summary["final_evaluation_return_mean"],
            "wall_seconds_total": d0_summary["wall_seconds_total"],
        }
        runs[f"d1_seed{seed}"] = {
            "run_dir": d1_dir.name,
            "completed": d1_summary["completed"],
            "rollouts_completed": d1_summary["rollouts_completed"],
            "transitions_total": d1_summary["transitions_total"],
            "episodes_total": d1_summary["episodes_total"],
            "optimizer_steps_total": d1_summary["optimizer_steps_total"],
            "evaluation_count": d1_summary["evaluation_count"],
            "final_evaluation_return_mean": d1_summary["final_evaluation_return_mean"],
            "wall_seconds_total": d1_summary["wall_seconds_total"],
        }

        pair = {"seed": int(seed)}
        for kind in ACCURACY_KINDS:
            for where in ("window", "final"):
                d0_acc = _accuracy(d0_probe, kind, where)
                d1_acc = _accuracy(d1_probe, kind, where)
                pair[f"{kind}_accuracy_{where}_d0"] = d0_acc
                pair[f"{kind}_accuracy_{where}_d1"] = d1_acc
                pair[f"{kind}_accuracy_{where}_gain"] = _difference(d1_acc, d0_acc)

        for key in ("team_label_agreement_mean_window",
                    "individual_label_agreement_mean_window",
                    "team_value_mean_abs_change_mean_window",
                    "agent_value_mean_abs_change_mean_window",
                    "team_value_mean_abs_change_var_window",
                    "agent_value_mean_abs_change_var_window"):
            a = d0_probe["derived"].get(key)
            b = d1_probe["derived"].get(key)
            pair[f"{key}_d0"] = a
            pair[f"{key}_d1"] = b
            pair[f"{key}_diff"] = None if (a is None or b is None) else float(b - a)

        for side in ("d0", "d1"):
            probe = d0_probe if side == "d0" else d1_probe
            variance = probe["derived"].get("value_variance_across_rollouts") or {}
            for key, value in variance.items():
                if key == "window_start_rollout":
                    continue
                pair[f"{key}_{side}"] = value
        for key in ("team_value_var_across_rollouts_mean_over_probes",
                    "agent_value_var_across_rollouts_mean_over_probes"):
            a, b = pair.get(f"{key}_d0"), pair.get(f"{key}_d1")
            pair[f"{key}_diff"] = None if (a is None or b is None) else float(b - a)

        pair["final_evaluation_return_mean_d0"] = d0_summary["final_evaluation_return_mean"]
        pair["final_evaluation_return_mean_d1"] = d1_summary["final_evaluation_return_mean"]
        pair["final_evaluation_return_mean_diff"] = (
            None if (d0_summary["final_evaluation_return_mean"] is None
                     or d1_summary["final_evaluation_return_mean"] is None)
            else float(d1_summary["final_evaluation_return_mean"]
                       - d0_summary["final_evaluation_return_mean"]))

        share = d1_probe["derived"].get("age_weight_share_final")
        pair["d1_age_weight_share_first"] = d1_probe["derived"].get("age_weight_share_first")
        pair["d1_age_weight_share_final"] = share
        pairs[f"seed{seed}"] = pair

    return runs, pairs, run_dirs


def reading_rule(pairs, where="window"):
    """Contract section 5, applied verbatim; both ambiguous readings are reported."""
    out = {}
    seeds = sorted(pairs)
    for kind in ACCURACY_KINDS:
        gains = {b: [pairs[s][f"{kind}_accuracy_{where}_gain"][b] for s in seeds]
                 for b in BUCKETS}
        spreads = {b: _spread(gains[b]) for b in BUCKETS}
        per_seed = []
        for index, seed in enumerate(seeds):
            high = gains["7-9"][index]
            low = gains["0-2"][index]
            excess = None if (high is None or low is None) else float(high - low)
            strict_threshold = None
            loose_threshold = None
            if spreads["7-9"] is not None and spreads["0-2"] is not None:
                strict_threshold = float(max(spreads["7-9"], spreads["0-2"]))
                loose_threshold = float(min(spreads["7-9"], spreads["0-2"]))
            per_seed.append({
                "seed": seed,
                "gain_7_9": high,
                "gain_0_2": low,
                "excess_7_9_over_0_2": excess,
                "exceeds_strict": (
                    None if (excess is None or strict_threshold is None)
                    else bool(excess > strict_threshold)),
                "exceeds_loose": (
                    None if (excess is None or loose_threshold is None)
                    else bool(excess > loose_threshold)),
            })
        strict_count = sum(1 for row in per_seed if row["exceeds_strict"])
        loose_count = sum(1 for row in per_seed if row["exceeds_loose"])
        contradicted_strict = strict_count >= 2 and len(seeds) >= 2
        contradicted_loose = loose_count >= 2 and len(seeds) >= 2

        # "supported ... if the gains are within the spread in every bucket":
        # every seed's gain, in every bucket, has magnitude no larger than that bucket's
        # across-seed spread.
        within = {}
        for b in BUCKETS:
            values = [g for g in gains[b] if g is not None]
            spread = spreads[b]
            within[b] = (
                None if (spread is None or not values)
                else bool(all(abs(g) <= spread for g in values)))
        supported = (all(v for v in within.values() if v is not None)
                     and all(v is not None for v in within.values()))

        if contradicted_strict:
            verdict = "contradicted"
        elif supported:
            verdict = "supported"
        else:
            verdict = "neither"

        out[kind] = {
            "where": where,
            "seeds": seeds,
            "gains": gains,
            "across_seed_spread": spreads,
            "per_seed": per_seed,
            "seed_pairs_exceeding_strict": strict_count,
            "seed_pairs_exceeding_loose": loose_count,
            "contradicted_strict_reading": bool(contradicted_strict),
            "contradicted_loose_reading": bool(contradicted_loose),
            "gains_within_spread_by_bucket": within,
            "supported": bool(supported),
            "verdict": verdict,
        }
    return out


def return_rule(runs, pairs):
    """Contract section 5's return clause."""
    seeds = sorted(pairs)
    d0 = [runs[f"d0_seed{s[4:]}"]["final_evaluation_return_mean"] for s in seeds]
    d1 = [runs[f"d1_seed{s[4:]}"]["final_evaluation_return_mean"] for s in seeds]
    diffs = [pairs[s]["final_evaluation_return_mean_diff"] for s in seeds]
    range_d0 = _range(d0)
    range_d1 = _range(d1)
    verdict = None
    if range_d0 is not None and range_d1 is not None and all(d is not None for d in diffs):
        threshold = max(range_d0["range"], range_d1["range"])
        verdict = ("no difference observed at this budget"
                   if all(abs(d) <= threshold for d in diffs)
                   else "a difference outside the across-seed range of both arms")
    return {
        "seeds": seeds,
        "d0_final_evaluation_return_mean": d0,
        "d1_final_evaluation_return_mean": d1,
        "difference_d1_minus_d0": diffs,
        "across_seed_range_d0": range_d0,
        "across_seed_range_d1": range_d1,
        "verdict": verdict,
        "caveat": ("the E0 caveat: two seeds of a lightly trained learner carried no "
                   "ordering at E0, and E1's returns are counters, not a result"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="E1 study-level aggregator")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--rollouts", type=int, default=20)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    runs, pairs, run_dirs = build(output_root, args.seeds, args.rollouts)
    payload = {
        "schema_version": 1,
        "contract": "docs/Claude_docs/experiments/E1_AGE_INPUT_20260902.md",
        "claim_ceiling": "B (EXPLORE)",
        "output_root": str(output_root),
        "rollouts": int(args.rollouts),
        "seeds_requested": list(args.seeds),
        "pairs_present": sorted(pairs),
        "run_directories": run_dirs,
        "runs": runs,
        "pairs": pairs,
        "reading_rule_window": reading_rule(pairs, "window") if pairs else None,
        "reading_rule_final_rollout": reading_rule(pairs, "final") if pairs else None,
        "return_rule": return_rule(runs, pairs) if pairs else None,
        "agreement_summary": {
            seed: {
                "team_d1_minus_d0": pairs[seed]["team_label_agreement_mean_window_diff"],
                "individual_d1_minus_d0":
                    pairs[seed]["individual_label_agreement_mean_window_diff"],
            } for seed in sorted(pairs)
        },
    }
    if pairs:
        payload["agreement_three_seed_range"] = {
            "team_d1_minus_d0": _range(
                [pairs[s]["team_label_agreement_mean_window_diff"] for s in sorted(pairs)]),
            "individual_d1_minus_d0": _range(
                [pairs[s]["individual_label_agreement_mean_window_diff"]
                 for s in sorted(pairs)]),
        }
    out_path = Path(args.out) if args.out else output_root / "E1_summary.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "written": str(out_path),
        "pairs_present": sorted(pairs),
        "verdict_team_window": (payload["reading_rule_window"]["team"]["verdict"]
                                if pairs else None),
        "verdict_individual_window": (payload["reading_rule_window"]["individual"]["verdict"]
                                      if pairs else None),
        "return_verdict": payload["return_rule"]["verdict"] if pairs else None,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
