"""E2 study-level aggregator - contract section 5's reading rule, applied mechanically.

Launch contract: `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`.

This script measures nothing.  It reads the finished run directories written by
`scripts/run_flexible_skill_duration_e2.py`, differences what they recorded, applies
contract section 5's rule **verbatim and mechanically**, and writes `E2_summary.json`
at the study root.

Contract section 5, quoted so the implementation can be checked against it:

    Let `R_best0` be the best D0 arm's evaluation return at the last checkpoint (per
    seed), `R_c` the D2 arm's at cost `c`, and `s` the larger of the two arms'
    across-seed ranges.

    * Mechanism A is supported if some `c` has `R_c >= R_best0 - s` in both seeds, and
      at that `c` the event-alignment fraction exceeds one half and the mean segment
      length is non-decreasing in `c` across the four `c` arms in both seeds.
    * Mechanism B is supported if no `c` has `R_c >= R_best0 - s` in either seed, and
      the event-alignment fraction at every finite `c` is below one half.
    * Anything else is neither ... if the return condition holds but the alignment does
      not, that is recorded as "D2 pays for a reason other than event alignment".
    * The D0 sanity check ... if the learner's `k` ordering disagrees with the reference
      ordering at the top (the learner's best `k` is not `k*` or its reference-adjacent
      neighbour) in either seed, the study is reported with that fact first ...
    * The reviewer's numerical prediction (section 1) is scored separately: best `c` in
      `[0.5, 1.0]`, and alignment above one half there.

Readings this implementation had to fix, because the rule's wording admits more than one
(each is recorded in the output under `readings`, and in the result document):

1. `s`, "the larger of the two arms' across-seed ranges", is computed as
   `max(range(R_best0 over seeds), range(R_c over seeds))`.  The `R_best0` series may
   name a different `k` at each seed; the range is taken over the series, not over one
   fixed arm.  The fixed-arm alternative is reported as `s_fixed_best_arm`.
2. "the mean segment length is non-decreasing in `c`" is a property of the four `c` arms
   as a whole and is evaluated once per seed over the ordered grid
   `(0.25, 0.5, 1.0, 2.0)`, using the completed-agent-segment mean of the **last**
   rollout.  A tolerance of exactly zero is used.
3. "the event-alignment fraction" is the runner's `aligned_fraction` at the last
   rollout, i.e. the two-step window `{t_flip, t_flip + 1}`.  The one-step reading and
   the gap-caused-only reading are carried beside it.
4. "reference-adjacent neighbour" is reported under both readings: the neighbour of
   `k*` in the reference **ordering** of `J_fixed_k` (the second best `k` by `J`), and
   the neighbours of `k*` in the **grid** of swept `k`.  A disagreement is declared only
   when the learner's best `k` fails both.
5. "best `c`" for the reviewer's clause is the `c` with the largest seed-mean final
   return; the per-seed argmax is reported beside it.

Usage:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        scripts/run_flexible_skill_duration_e2_aggregate.py \
        --study-root temp/directions/flexible_skill_duration/exp/E2_20260903
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_flexible_skill_duration_e2 import (  # noqa: E402
    ARMS,
    ARM_ORDER,
    BIT_IDENTITY_PAIR,
    D0_K_SET,
    D2_C_SET,
    _jsonable,
)

ALIGNMENT_THRESHOLD = 0.5
REVIEWER_C_INTERVAL = (0.5, 1.0)


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------


def load_runs(study_root: Path) -> dict:
    """Every completed run directory under the study root, keyed by (arm, seed)."""
    runs = {}
    skipped = []
    for path in sorted(study_root.iterdir()):
        if not path.is_dir():
            continue
        summary_path = path / "summary.json"
        if not summary_path.exists():
            skipped.append({"dir": path.name, "reason": "no summary.json"})
            continue
        if (path / "QUARANTINED").exists():
            skipped.append({"dir": path.name, "reason": "QUARANTINED"})
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not summary.get("completed"):
            skipped.append({"dir": path.name, "reason": "not completed"})
            continue
        if summary.get("timing_only"):
            skipped.append({"dir": path.name, "reason": "timing_only"})
            continue
        runs[(summary["arm"], int(summary["seed"]))] = {
            "dir": path,
            "summary": summary,
        }
    return {"runs": runs, "skipped": skipped}


def _final_return(summary: dict):
    value = summary.get("final_evaluation_return_mean")
    return None if value is None else float(value)


def _last_interruption(summary: dict) -> dict:
    return summary.get("final_interruption_record") or {}


def _alignment(summary: dict, key: str = "aligned_fraction"):
    record = _last_interruption(summary).get("event_alignment") or {}
    value = record.get(key)
    return None if value is None else float(value)


def _segment_mean(summary: dict):
    record = _last_interruption(summary).get("segment_length_agent") or {}
    value = record.get("mean")
    return None if value is None else float(value)


def _range(values) -> float:
    finite = [float(v) for v in values if v is not None]
    if not finite:
        return 0.0
    return float(max(finite) - min(finite))


# ---------------------------------------------------------------------------
# the rule
# ---------------------------------------------------------------------------


def apply_reading_rule(per_seed: dict, references: dict) -> dict:
    """Contract section 5, applied mechanically.

    ``per_seed`` maps seed -> {
        'd0': {k: final return},
        'd2': {c: final return},
        'alignment': {c: fraction},
        'segment_mean': {c: mean segment length},
    }
    ``references`` is a run manifest's ``references`` block.
    """
    seeds = sorted(per_seed)
    c_grid = list(D2_C_SET)

    # --- R_best0 per seed ------------------------------------------------
    best0 = {}
    best0_arm = {}
    for seed in seeds:
        returns = {k: v for k, v in per_seed[seed]["d0"].items() if v is not None}
        if not returns:
            best0[seed] = None
            best0_arm[seed] = None
            continue
        k_best = max(returns, key=lambda k: returns[k])
        best0[seed] = float(returns[k_best])
        best0_arm[seed] = int(k_best)
    best0_range = _range(best0.values())

    # --- per-c comparison -------------------------------------------------
    per_c = {}
    for c in c_grid:
        returns = {seed: per_seed[seed]["d2"].get(c) for seed in seeds}
        c_range = _range(returns.values())
        s_value = max(best0_range, c_range)
        # the fixed-arm alternative for `s` (reading 1)
        fixed_arm_ranges = []
        for k in D0_K_SET:
            values = [per_seed[seed]["d0"].get(k) for seed in seeds]
            if all(v is not None for v in values):
                fixed_arm_ranges.append(_range(values))
        s_fixed = max(max(fixed_arm_ranges) if fixed_arm_ranges else 0.0, c_range)
        holds = {}
        for seed in seeds:
            r_c = returns.get(seed)
            r_b = best0.get(seed)
            holds[seed] = (None if (r_c is None or r_b is None)
                           else bool(r_c >= r_b - s_value))
        alignment = {seed: per_seed[seed]["alignment"].get(c) for seed in seeds}
        per_c[c] = {
            "returns": {str(seed): returns[seed] for seed in seeds},
            "R_best0": {str(seed): best0[seed] for seed in seeds},
            "R_best0_arm_k": {str(seed): best0_arm[seed] for seed in seeds},
            "across_seed_range_R_best0": best0_range,
            "across_seed_range_R_c": c_range,
            "s": s_value,
            "s_fixed_best_arm": s_fixed,
            "return_condition_per_seed": {str(seed): holds[seed] for seed in seeds},
            "return_condition_both_seeds": bool(
                holds and all(v is True for v in holds.values())),
            "return_condition_any_seed": bool(any(v is True for v in holds.values())),
            "alignment": {str(seed): alignment[seed] for seed in seeds},
            "alignment_above_half_both_seeds": bool(
                alignment and all(v is not None and v > ALIGNMENT_THRESHOLD
                                  for v in alignment.values())),
            "alignment_below_half_all_seeds": bool(
                alignment and all(v is not None and v < ALIGNMENT_THRESHOLD
                                  for v in alignment.values())),
            "segment_mean": {str(seed): per_seed[seed]["segment_mean"].get(c)
                             for seed in seeds},
        }

    # --- monotonicity of the mean segment length in c ---------------------
    monotone = {}
    for seed in seeds:
        values = [per_seed[seed]["segment_mean"].get(c) for c in c_grid]
        if any(v is None for v in values):
            monotone[seed] = None
            continue
        monotone[seed] = bool(all(values[i + 1] >= values[i]
                                  for i in range(len(values) - 1)))
    monotone_both = bool(monotone and all(v is True for v in monotone.values()))

    # --- branches ---------------------------------------------------------
    a_candidates = [c for c in c_grid
                    if per_c[c]["return_condition_both_seeds"]
                    and per_c[c]["alignment_above_half_both_seeds"]]
    return_candidates = [c for c in c_grid if per_c[c]["return_condition_both_seeds"]]
    mechanism_a = bool(a_candidates) and monotone_both
    no_c_any_seed = not any(per_c[c]["return_condition_any_seed"] for c in c_grid)
    alignment_all_below = all(per_c[c]["alignment_below_half_all_seeds"] for c in c_grid)
    mechanism_b = bool(no_c_any_seed and alignment_all_below)

    if mechanism_a and mechanism_b:
        verdict = "contradictory"
    elif mechanism_a:
        verdict = "mechanism_A_supported"
    elif mechanism_b:
        verdict = "mechanism_B_supported"
    else:
        verdict = "neither"

    pays_other_reason = bool(return_candidates and not a_candidates)

    # --- D0 sanity check ---------------------------------------------------
    j_fixed = {int(k): float(v) for k, v in references["J_fixed_k"].items()}
    ordered = sorted(j_fixed, key=lambda k: j_fixed[k], reverse=True)
    k_star = int(references["best_fixed_k"])
    ordering_neighbour = {ordered[1]} if len(ordered) > 1 else set()
    grid = sorted(D0_K_SET)
    index = grid.index(k_star)
    grid_neighbours = set()
    if index > 0:
        grid_neighbours.add(grid[index - 1])
    if index + 1 < len(grid):
        grid_neighbours.add(grid[index + 1])
    accept_ordering = {k_star} | ordering_neighbour
    accept_grid = {k_star} | grid_neighbours
    sanity = {}
    for seed in seeds:
        learner_best = best0_arm[seed]
        sanity[str(seed)] = {
            "learner_best_k": learner_best,
            "reference_best_k": k_star,
            "reference_ordering": ordered,
            "accepted_set_reference_ordering": sorted(accept_ordering),
            "accepted_set_grid_adjacency": sorted(accept_grid),
            "agrees_reference_ordering": (
                None if learner_best is None else bool(learner_best in accept_ordering)),
            "agrees_grid_adjacency": (
                None if learner_best is None else bool(learner_best in accept_grid)),
            "learner_k_ordering_by_return": [
                int(k) for k in sorted(
                    (k for k, v in per_seed[seed]["d0"].items() if v is not None),
                    key=lambda k: per_seed[seed]["d0"][k], reverse=True)],
        }
    disagrees = any(
        row["agrees_reference_ordering"] is False and row["agrees_grid_adjacency"] is False
        for row in sanity.values())

    # --- reviewer's numerical clauses, scored separately -------------------
    seed_mean = {}
    for c in c_grid:
        values = [per_seed[seed]["d2"].get(c) for seed in seeds]
        seed_mean[c] = (float(np.mean(values)) if all(v is not None for v in values)
                        else None)
    ranked = [c for c in c_grid if seed_mean[c] is not None]
    best_c = max(ranked, key=lambda c: seed_mean[c]) if ranked else None
    per_seed_best_c = {}
    for seed in seeds:
        values = {c: per_seed[seed]["d2"].get(c) for c in c_grid}
        finite = {c: v for c, v in values.items() if v is not None}
        per_seed_best_c[str(seed)] = (max(finite, key=lambda c: finite[c])
                                      if finite else None)
    alignment_at_best = ({str(seed): per_seed[seed]["alignment"].get(best_c)
                          for seed in seeds} if best_c is not None else {})
    reviewer = {
        "clause_1_best_c_in_0p5_to_1p0": (
            None if best_c is None
            else bool(REVIEWER_C_INTERVAL[0] <= best_c <= REVIEWER_C_INTERVAL[1])),
        "best_c_by_seed_mean": best_c,
        "seed_mean_return_by_c": {str(c): seed_mean[c] for c in c_grid},
        "best_c_per_seed": per_seed_best_c,
        "clause_2_alignment_above_half_at_best_c": (
            None if best_c is None
            else bool(alignment_at_best
                      and all(v is not None and v > ALIGNMENT_THRESHOLD
                              for v in alignment_at_best.values()))),
        "alignment_at_best_c": alignment_at_best,
        "interval": list(REVIEWER_C_INTERVAL),
        "threshold": ALIGNMENT_THRESHOLD,
    }

    return {
        "seeds": [int(s) for s in seeds],
        "c_grid": [float(c) for c in c_grid],
        "R_best0_per_seed": {str(seed): best0[seed] for seed in seeds},
        "R_best0_arm_per_seed": {str(seed): best0_arm[seed] for seed in seeds},
        "across_seed_range_R_best0": best0_range,
        "per_c": {str(c): per_c[c] for c in c_grid},
        "segment_mean_monotone_in_c_per_seed": {str(s): monotone[s] for s in seeds},
        "segment_mean_monotone_in_c_both_seeds": monotone_both,
        "c_satisfying_return_condition_both_seeds": [float(c) for c in return_candidates],
        "c_satisfying_return_and_alignment": [float(c) for c in a_candidates],
        "mechanism_A_supported": mechanism_a,
        "mechanism_B_supported": mechanism_b,
        "verdict": verdict,
        "d2_pays_for_a_reason_other_than_event_alignment": pays_other_reason,
        "d0_sanity_check": sanity,
        "d0_sanity_disagrees_at_the_top": disagrees,
        "reviewer_numerical_prediction": reviewer,
    }


# ---------------------------------------------------------------------------
# the bit-identity check of contract section 2
# ---------------------------------------------------------------------------


def matched_pair_check(study_root: Path, seed: int,
                       pair=BIT_IDENTITY_PAIR) -> dict:
    """Contract section 2: rollout 1 bit-identical until the first interruption.

    The two arms of the pair share the host master seed and the learner seed, so at
    D0 (`c = inf`, cap 40) and D2 (`c` finite, cap 40) the trajectories can only part
    at the first step whose D2 sampled masks differ.  Everything strictly before that
    step must be equal, array by array.
    """
    left = study_root / f"{pair[0]}_seed{seed}" / "rollout1_match.npz"
    right = study_root / f"{pair[1]}_seed{seed}" / "rollout1_match.npz"
    if not (left.exists() and right.exists()):
        return {"pair": list(pair), "seed": int(seed), "available": False,
                "left": str(left), "right": str(right)}
    a = np.load(left)
    b = np.load(right)
    sampled_a = a["sampled"]
    sampled_b = b["sampled"]
    steps = min(sampled_a.shape[0], sampled_b.shape[0])
    differ = [t for t in range(steps)
              if not np.array_equal(sampled_a[t], sampled_b[t])]
    first = differ[0] if differ else None
    horizon = steps if first is None else first
    identical = {}
    for key in ("sampled", "roles", "service", "agent_cause", "change_flag"):
        identical[key] = bool(np.array_equal(a[key][:horizon], b[key][:horizon]))
    for key in ("rewards", "gap_agent", "gap_team"):
        identical[key] = bool(np.array_equal(
            np.nan_to_num(a[key][:horizon], nan=-12345.0),
            np.nan_to_num(b[key][:horizon], nan=-12345.0)))
    return {
        "pair": list(pair),
        "seed": int(seed),
        "available": True,
        "first_divergent_step": first,
        "steps_compared": int(horizon),
        "identical_before_first_interruption": identical,
        "all_identical_before_first_interruption": bool(all(identical.values())),
        "note": (
            "`first_divergent_step` is the first step whose D2 sampled masks differ; "
            "every recorded array is compared on the steps strictly before it. NaN "
            "gaps (reset steps, where the coordinator is not evaluated) are compared "
            "as equal by substituting a sentinel."),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def build_summary(study_root: Path) -> dict:
    loaded = load_runs(study_root)
    runs = loaded["runs"]
    seeds = sorted({seed for (_arm, seed) in runs})
    references = None
    for (_arm, _seed), row in runs.items():
        references = row["summary"]["references"]
        break

    per_seed = {}
    for seed in seeds:
        d0, d2, alignment, segment_mean = {}, {}, {}, {}
        for arm, row in ARMS.items():
            entry = runs.get((arm, seed))
            if entry is None:
                continue
            summary = entry["summary"]
            value = _final_return(summary)
            if row["family"] == "d0":
                d0[int(row["k"])] = value
            else:
                c = float(row["c"])
                d2[c] = value
                alignment[c] = _alignment(summary)
                segment_mean[c] = _segment_mean(summary)
        per_seed[seed] = {"d0": d0, "d2": d2, "alignment": alignment,
                          "segment_mean": segment_mean}

    rule = (apply_reading_rule(per_seed, references) if references is not None
            else None)

    per_run = []
    for arm in ARM_ORDER:
        for seed in seeds:
            entry = runs.get((arm, seed))
            if entry is None:
                per_run.append({"arm": arm, "seed": int(seed), "present": False})
                continue
            summary = entry["summary"]
            last = _last_interruption(summary)
            per_run.append({
                "arm": arm,
                "seed": int(seed),
                "present": True,
                "run_dir": str(entry["dir"]),
                "family": ARMS[arm]["family"],
                "k": ARMS[arm]["k"],
                "c": ARMS[arm]["c"],
                "completed": bool(summary.get("completed")),
                "rollouts_completed": summary.get("rollouts_completed"),
                "final_evaluation_return_mean": _final_return(summary),
                "final_evaluation_return_stderr": summary.get(
                    "final_evaluation_return_stderr"),
                "final_evaluation": summary.get("final_evaluation"),
                "interruption_rate_per_agent_step": last.get(
                    "interruption_rate_per_agent_step"),
                "event_alignment_fraction": _alignment(summary),
                "event_alignment_fraction_strict": _alignment(
                    summary, "aligned_fraction_strict"),
                "event_alignment_fraction_gap_caused": (
                    (last.get("event_alignment_gap_caused_only") or {}).get(
                        "aligned_fraction")),
                "segment_length_agent": last.get("segment_length_agent"),
                "segment_length_team": last.get("segment_length_team"),
                "fraction_closed_by_cap": last.get("fraction_closed_by_cap"),
                "fraction_closed_by_gap": last.get("fraction_closed_by_gap"),
                "team_switch_rate_gap_per_env_step": last.get(
                    "team_switch_rate_gap_per_env_step"),
                "rows_M_per_rollout": summary.get("rows_M_per_rollout"),
                "wall_seconds_total": summary.get("wall_seconds_total"),
                "launch_commit": summary.get("launch_commit"),
                "code_sha": summary.get("code_sha"),
            })

    pairs = [matched_pair_check(study_root, seed) for seed in seeds]

    return {
        "schema_version": 1,
        "contract": "docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md",
        "study_root": str(study_root),
        "aggregator": "scripts/run_flexible_skill_duration_e2_aggregate.py",
        "runs_loaded": len(runs),
        "runs_skipped": loaded["skipped"],
        "seeds": [int(s) for s in seeds],
        "references": references,
        "per_run": per_run,
        "per_seed_inputs": {
            str(seed): {
                "d0_final_return_by_k": {str(k): v for k, v in per_seed[seed]["d0"].items()},
                "d2_final_return_by_c": {str(c): v for c, v in per_seed[seed]["d2"].items()},
                "alignment_by_c": {str(c): v for c, v in per_seed[seed]["alignment"].items()},
                "segment_mean_by_c": {str(c): v
                                      for c, v in per_seed[seed]["segment_mean"].items()},
            } for seed in seeds},
        "reading_rule": rule,
        "matched_pair_checks": pairs,
        "readings": [
            "s = max(range of R_best0 across seeds, range of R_c across seeds); the "
            "fixed-arm alternative is reported as s_fixed_best_arm",
            "segment-length monotonicity is evaluated over the ordered c grid "
            "(0.25, 0.5, 1.0, 2.0) at the last rollout, tolerance exactly zero",
            "the event-alignment fraction is the two-step window {t_flip, t_flip + 1} "
            "at the last rollout; the one-step and gap-caused-only readings are carried "
            "beside it",
            "reference-adjacent neighbour is reported under both the reference-ordering "
            "and the grid-adjacency readings; a disagreement needs both to fail",
            "best c for the reviewer's clause is the argmax of the seed-mean final "
            "return; the per-seed argmax is reported beside it",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="E2 study-level aggregator")
    parser.add_argument("--study-root", required=True)
    parser.add_argument("--out", default=None,
                        help="default: <study-root>/E2_summary.json")
    args = parser.parse_args(argv)

    study_root = Path(args.study_root).resolve()
    summary = build_summary(study_root)
    out = Path(args.out).resolve() if args.out else study_root / "E2_summary.json"
    out.write_text(json.dumps(_jsonable(summary), indent=2, ensure_ascii=False),
                   encoding="utf-8")
    rule = summary["reading_rule"] or {}
    print(json.dumps(_jsonable({
        "study_root": str(study_root),
        "out": str(out),
        "runs_loaded": summary["runs_loaded"],
        "runs_skipped": summary["runs_skipped"],
        "verdict": rule.get("verdict"),
        "mechanism_A_supported": rule.get("mechanism_A_supported"),
        "mechanism_B_supported": rule.get("mechanism_B_supported"),
        "d2_pays_for_a_reason_other_than_event_alignment": rule.get(
            "d2_pays_for_a_reason_other_than_event_alignment"),
        "d0_sanity_disagrees_at_the_top": rule.get("d0_sanity_disagrees_at_the_top"),
        "reviewer_numerical_prediction": rule.get("reviewer_numerical_prediction"),
    }), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
