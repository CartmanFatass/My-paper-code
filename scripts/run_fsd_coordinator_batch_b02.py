"""FSD coordinator batch B02: the standing D recipe at coordinator batch 128 against 1280, 45 rollouts.

Exploration (six fits), prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 05:20 PDT - prospective:
coordinator batch, D1280 versus D128 at 45 rollouts".

Thin entry over the frozen baseline x interruption B01 runner, as the matched-information runner is:
the same collector loop, panel law, summary and fit validation, rebound to this object's identity, the
five matched-information confirmation blocks, 45 rollouts and nine panels. Both arms are the ordinary
D0 fixed-clock construction; `coordinator_batch_size` is the only field that differs.

  D128   five new fits, one per block
  D1280  one new fit on block 772803 only: a rerun of a completed matched-information fit at this
         object's source, the measured size of rerun variation at a fixed seed

The D1280 side of M_b = J45(D1280, b) - J45(D128, b) is the five completed stage-1 D1280 fits of
FSD_MATCHED_INFORMATION_BASELINE_B01, read by that object's own validator. The rerun is reported next
to the M_b and never replaces one of them (fixed in the notebook entry before any fit).

`fit` is result-bearing and runs only through `scripts/hmasd_launch.py` (runner-side admission).
`reduce` is a pure reading of published summaries and carries no admission.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01
import run_fsd_matched_information_baseline_b01 as matched
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_COORDINATOR_BATCH_B02"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 05:20 PDT, coordinator batch D1280 versus D128 at 45 rollouts)")
REFERENCE_OBJECT_ID = matched.OBJECT_ID
BLOCKS = dict(matched.STAGE1_BLOCKS)
ARMS = {"D128": ("D0", 128), "D1280": ("D0", 1280)}
TREATMENT, REFERENCE = "D128", "D1280"
RERUN_BLOCK = 772803
ROLLOUTS = matched.ROLLOUTS
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS
CURVE_ROLLOUTS = PANEL_ROLLOUTS[:-1]
WALL_PLANS = {"D128": 10300., "D1280": 8250.}  # D1280 measured in the reference object; D128 unmeasured
PRIMARY_NAME = f"M_{ROLLOUTS}"
# The only configuration field, and the only summary field, that may differ inside a pair.
PAIR_DIFFERENCES = frozenset({"coordinator_batch_size"})
CURRENT = {"admission": None}
_orig_make_config = matched._orig_make_config
_orig_base_summary = shared.base_summary


def _is_wrapper(function, flag="_coordinator_batch_wrapper"):
    return bool(getattr(function, flag, False))


def bind():
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand."""
    global shared, _orig_base_summary
    shared = b01.shared
    # `reduce` reads both objects in one process, so the matched-information wrapper may be installed
    # (and may itself hold this one). Only ever wrap the plain function, exactly once.
    current = shared.base_summary
    if _is_wrapper(current, "_matched_information_wrapper"):
        current = matched._orig_base_summary
    if not _is_wrapper(current):
        _orig_base_summary = current
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = dict(ARMS), None  # no flat arm: both arms train a coordinator
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.make_config, shared.base_summary = _orig_make_config, base_summary


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    summary.update(coordinator_batch_object=OBJECT_ID, admission=CURRENT["admission"],
                   primary=PRIMARY_NAME)
    return summary


base_summary._coordinator_batch_wrapper = True


def plan_guard(arm, seed):
    """The notebook entry's six fits: D128 on the five blocks, D1280 on the rerun block only."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on the five blocks 772803 ... 773203")
    if arm == REFERENCE and seed != RERUN_BLOCK:
        raise SystemExit(f"D1280 is rerun on block {RERUN_BLOCK} only; the other blocks use the "
                         "completed matched-information fits")


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind()
    CURRENT.update(admission=admission)
    try:
        return b01.run_fit(arm, seed, out)
    finally:
        CURRENT.update(admission=None)


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit of this object."""
    bind()
    if summary.get("coordinator_batch_object") != OBJECT_ID:
        raise ValueError("not a coordinator-batch fit")
    plan_guard(summary["factorial_arm"], int(summary["block_seed"]))
    return b01.arm_panels(summary)


def reference_endpoint(summary):
    """A completed stage-1 D1280 fit of the matched-information object, by its own validator."""
    if (summary.get("factorial_arm") != REFERENCE or summary.get("stage") != 1
            or int(summary.get("block_seed", -1)) not in BLOCKS):
        raise ValueError("the reference arm is the matched-information stage-1 D1280 fits")
    return matched.fit_endpoint(summary)


def pair_view(summary):
    """Everything a pair must share. The launch sha differs by design and is reported, not compared."""
    common = {k: summary[k] for k in ("host", "device", "torch_threads", "learner_precision",
                                      "reward_return_precision", "native_score_factor", "rollouts",
                                      "panel_rollouts", "training_seed", "evaluation_seed")}
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in PAIR_DIFFERENCES}
    return common


def fit_row(summary, scores):
    return {"J_by_rollout": {str(r): float(np.mean(scores[r])) for r in PANEL_ROLLOUTS},
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "coordinator_batch_size": summary["coordinator_batch_size"],
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def paired_statistics(differences):
    values = [float(v) for v in differences]
    count = len(values)
    mean = float(np.mean(values)) if count else None
    sd = float(np.std(values, ddof=1)) if count >= 2 else None
    se = sd / math.sqrt(count) if sd is not None else None
    t = b01.T975.get(count - 1)
    half = t * se if se is not None and t is not None else None
    return {"available_blocks": count, "planned_blocks": len(BLOCKS), "mean": mean, "sample_sd": sd,
            "se": se, "t_multiplier": t,
            "working_model_95pct_interval": [mean - half, mean + half] if half is not None else None,
            "positive_blocks": int(sum(v > 0 for v in values)),
            "negative_blocks": int(sum(v < 0 for v in values)),
            "zero_blocks": int(sum(v == 0 for v in values)),
            "working_model": "iid-normal paired block differences; Student-t on the available blocks; "
                             "the reference arm is not contemporaneous; coverage is not validated"}


def rerun_comparison(rerun, rerun_scores, reference, reference_scores):
    """The D1280 rerun against the completed fit of the same block: reported, never substituted."""
    if pair_view(rerun) != pair_view(reference) or (
            rerun["coordinator_batch_size"] != reference["coordinator_batch_size"]):
        return {"status": "incomplete", "failure": "the rerun is not the reference construction"}
    panel = {str(r): float(np.mean(rerun_scores[r]) - np.mean(reference_scores[r])) for r in PANEL_ROLLOUTS}
    world = max(float(np.max(np.abs(np.asarray(rerun_scores[r]) - np.asarray(reference_scores[r]))))
                for r in PANEL_ROLLOUTS)
    return {"status": "complete", "block_seed": RERUN_BLOCK,
            "rerun_launch_sha": rerun["launch_sha"], "reference_launch_sha": reference["launch_sha"],
            "panel_means_reproduce_exactly": all(v == 0.0 for v in panel.values()),
            "world_scores_reproduce_exactly": world == 0.0,
            "rerun_minus_reference_J_by_rollout": panel,
            "max_abs_panel_mean_difference": max(abs(v) for v in panel.values()),
            "max_abs_world_score_difference": world,
            "rerun_minus_reference_J45": panel[str(ROLLOUTS)],
            "note": "rerun variation at a fixed seed; M_b uses the completed reference fits as declared"}


def reduce_pairs(summaries, references):
    """Five new D128 fits and the rerun in `summaries`; the five completed D1280 fits in `references`."""
    scores, rows, views, failures, supplied = {}, {}, {}, {}, set()
    rerun = None
    for summary, reader, side in ([(s, fit_endpoint, "new") for s in summaries]
                                  + [(s, reference_endpoint, "reference") for s in references]):
        arm, seed = summary.get("factorial_arm"), int(summary.get("block_seed", -1))
        key = (seed, arm, side)
        if key in supplied:  # a second fit of the same cell, credible or not, is never a choice
            raise ValueError("duplicate arm/block")
        supplied.add(key)
        try:
            values = reader(summary)
        except (KeyError, TypeError, ValueError) as exc:
            failures[key] = str(exc)
            continue
        if side == "new" and arm == REFERENCE:
            rerun = (summary, values)
            continue
        scores[(seed, arm)], rows[(seed, arm)], views[(seed, arm)] = values, fit_row(summary, values), pair_view(summary)
    blocks, differences, curve_values = [], [], {r: [] for r in CURVE_ROLLOUTS}
    for seed in sorted(BLOCKS):
        pair = [(seed, REFERENCE), (seed, TREATMENT)]
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                 "arms": {arm: rows[(seed, arm)] for _, arm in pair if (seed, arm) in rows},
                 "missing_or_invalid_arms": {
                     arm: failures.get((seed, arm, side), "not supplied")
                     for (_, arm), side in zip(pair, ("reference", "new")) if (seed, arm) not in rows}}
        if all(key in scores for key in pair):
            if views[pair[0]] != views[pair[1]]:
                entry["pair"] = {"status": "incomplete", "failure": "unplanned difference inside the pair"}
            else:
                level = {key: {r: float(np.mean(scores[key][r])) for r in PANEL_ROLLOUTS} for key in pair}
                world = np.asarray(scores[pair[0]][ROLLOUTS]) - np.asarray(scores[pair[1]][ROLLOUTS])
                value = level[pair[0]][ROLLOUTS] - level[pair[1]][ROLLOUTS]
                entry["pair"] = {
                    "status": "complete", PRIMARY_NAME: value,
                    "J45": {REFERENCE: level[pair[0]][ROLLOUTS], TREATMENT: level[pair[1]][ROLLOUTS]},
                    "ordered_world_differences": world.tolist(),
                    "conditional_world_sd": float(world.std(ddof=1)),
                    "conditional_world_se": float(world.std(ddof=1) / math.sqrt(len(world))),
                    "M_by_rollout": {str(r): level[pair[0]][r] - level[pair[1]][r] for r in PANEL_ROLLOUTS}}
                differences.append(value)
                for r in CURVE_ROLLOUTS:
                    curve_values[r].append(level[pair[0]][r] - level[pair[1]][r])
        else:
            entry["pair"] = {"status": "incomplete",
                             "missing_operands": [arm for _, arm in pair if (seed, arm) not in scores]}
        blocks.append(entry)
    primary = dict(paired_statistics(differences), name=PRIMARY_NAME)
    primary["status"] = "complete" if primary["available_blocks"] == len(BLOCKS) else "incomplete"
    if rerun is None:
        comparison = {"status": "incomplete",
                      "failure": failures.get((RERUN_BLOCK, REFERENCE, "new"), "not supplied")}
    elif (RERUN_BLOCK, REFERENCE) not in scores:
        comparison = {"status": "incomplete", "failure": "the reference fit of the rerun block is missing"}
    else:
        reference = next(s for s in references if int(s.get("block_seed", -1)) == RERUN_BLOCK)
        comparison = rerun_comparison(rerun[0], rerun[1], reference, scores[(RERUN_BLOCK, REFERENCE)])
    levels = {}
    for arm in (REFERENCE, TREATMENT):
        values = {seed: float(np.mean(scores[(seed, arm)][ROLLOUTS])) for seed in sorted(BLOCKS)
                  if (seed, arm) in scores}
        levels[arm] = {"per_block_J45": {str(s): v for s, v in values.items()},
                       "mean": float(np.mean(list(values.values()))) if values else None,
                       "sample_sd": float(np.std(list(values.values()), ddof=1)) if len(values) >= 2 else None,
                       "J_by_rollout_mean": {str(r): float(np.mean([np.mean(scores[(s, arm)][r]) for s in values]))
                                             for r in PANEL_ROLLOUTS} if values else None,
                       "note": "descriptive; never a substitute for the paired-difference SD"}
    return {
        "object_id": OBJECT_ID, "card": CARD, "reference_object_id": REFERENCE_OBJECT_ID,
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "status": "complete" if primary["status"] == "complete" and comparison["status"] == "complete"
                  else "incomplete",
        "quantity": "M_b = J45(D1280, b) - J45(D128, b); J45 = mean of the 32 final world scores; the "
                    "D1280 operand is the completed matched-information stage-1 fit of the same block",
        "blocks": blocks, "primary": primary,
        "curves": {str(r): paired_statistics(curve_values[r]) for r in CURVE_ROLLOUTS},
        "levels": levels, "d1280_rerun": comparison,
        "invalid_inputs": {f"{seed}:{arm}:{side}": text for (seed, arm, side), text in failures.items()},
        "interpretation_limit": (
            "exploration; five paired blocks with a non-contemporaneous reference arm; the treatment is "
            "the batch law as a package (batch size, coordinator optimizer steps, normalisation groups); "
            "no CF arm, so nothing here apportions the matched-information D - CF difference"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True,
                     help="this object's fits: five D128 and the D1280 rerun")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the five completed matched-information stage-1 D1280 summaries")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "fit":
        # Refuse an out-of-plan arm or block before the single-use admission is spent.
        plan_guard(args.arm, args.seed)
        # Nothing scientific has happened yet: no output, environment, learner or evaluator.
        # The literal direction is the launch kernel's guard contract; keep it inline.
        admission = require_admission(__file__, direction="flexible_skill_duration")
        if args.launch_sha is not None and args.launch_sha != admission["sha"]:
            parser.error("--launch-sha must equal the admitted source SHA")
        head = shared.e0._git("rev-parse", "HEAD")
        if head and head != admission["sha"]:
            parser.error("runner source HEAD is not the admitted SHA")
        return run_fit(args.arm, args.seed, args.output_root.resolve(),
                       admission={"sha": admission["sha"],
                                  "command_sha256": admission["command_sha256"]})

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_pairs([load(p) for p in args.summaries], [load(p) for p in args.references])
    result["input_summaries"] = [str(p) for p in args.summaries]
    result["reference_summaries"] = [str(p) for p in args.references]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"], "mean_M": result["primary"]["mean"],
                      "interval": result["primary"]["working_model_95pct_interval"],
                      "d1280_rerun_exact": result["d1280_rerun"].get("panel_means_reproduce_exactly")}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
