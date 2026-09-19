"""FSD matched-information baseline B01: standing D1280 versus a central-input flat (CF).

Thin entry over the frozen baseline x interruption B01 runner (`run_fsd_baseline_interruption_b01`):
the same collector loop, panel law, summary and fit validation, rebound to this object's identity,
blocks, 45 rollouts and nine panels (5, 10, ... 45). The CF arm is the ordinary `off` route with the
`mappo` switch and explicit k = 10, plus the card's central-input pathway
(`use_central_snapshot_in_flat_actor`, off for every other arm and object): each step the actor reads
its own observation, the held central snapshot (normalized global state and the six normalized joint
observations in fixed UAV order), a fixed six-dimensional ego one-hot and the constant skill, with its
own GRU state. Stage 0 tunes only CF's actor/critic learning rate over three multipliers on two blocks
and selects by the card's section 3 rule; stage 1 runs five fresh blocks with one D1280 and one CF fit
each. `reduce` implements card sections 5 and 6 verbatim.

Card: docs/research/candidates/flexible_skill_duration/
      FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md

`fit` is result-bearing and runs only through `scripts/hmasd_launch.py` (runner-side admission).
`select-stage0` and `reduce` are pure readings of already published summaries: they construct no
environment, learner, evaluator or RNG master and therefore carry no admission.
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
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_MATCHED_INFORMATION_BASELINE_B01"
CARD = ("docs/research/candidates/flexible_skill_duration/"
        "FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md")
STAGE0_BLOCKS = {772603: 782603, 772703: 782703}
STAGE1_BLOCKS = {772803: 782803, 772903: 782903, 773003: 783003, 773103: 783103, 773203: 783203}
BLOCKS = {**STAGE0_BLOCKS, **STAGE1_BLOCKS}
ARMS = {"D1280": ("D0", 1280), "CF": ("CF", None)}
CF_ARM = "CF"
ROLLOUTS = 45
PANEL_ROLLOUTS = tuple(range(5, ROLLOUTS + 1, 5))
CURVE_ROLLOUTS = PANEL_ROLLOUTS[:-1]  # card section 5: G_r for r = 5 ... 40; 45 is the primary
# Card section 3: the grid, and the fixed order that breaks an exact tie inside the maximal set.
LR_MULTIPLIERS = (0.5, 1.0, 2.0)
TIE_ORDER = (1.0, 0.5, 2.0)
DEFAULT_MULTIPLIER = 1.0
TUNED_FIELDS = ("lr_discoverer_actor", "lr_discoverer_critic")
CF_FLAG = "use_central_snapshot_in_flat_actor"
WALL_PLANS = {"CF": 12000., "D1280": 10300.}
MEI = .05  # card section 6, absolute J
T975_DF4 = b01.T975[4]
PRIMARY_NAME = f"G_{ROLLOUTS}"
CURRENT = {"stage": None, "lr_multiplier": DEFAULT_MULTIPLIER, "admission": None}
_orig_make_config = b01.make_config
_orig_base_summary = shared.base_summary


def bind():
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand."""
    global shared, _orig_base_summary
    shared = b01.shared
    if not getattr(shared.base_summary, "_matched_information_wrapper", False):
        _orig_base_summary = shared.base_summary
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = dict(ARMS), CF_ARM
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.PLANNED_CONFIG_DIFFERENCES = frozenset(
        b01.PLANNED_CONFIG_DIFFERENCES | set(TUNED_FIELDS) | {CF_FLAG})
    b01.make_config, shared.base_summary = make_config, base_summary


def make_config(arm, envs, seed):
    """CF: the frozen flat construction, then this object's central input and tuned rates."""
    config = _orig_make_config(arm, envs, seed)
    if arm == CF_ARM:
        # After the `mappo` switch and the explicit k = 10 of the frozen flat branch.
        setattr(config, CF_FLAG, True)
        multiplier = float(CURRENT["lr_multiplier"])
        if multiplier != 1.0:
            # Every actor/critic optimizer group that actually trains, multiplied exactly once.
            # No learning-rate schedule is configured (`use_lr_decay` is False); if one were,
            # torch schedulers take these values as `base_lrs`, so the output is scaled once.
            for field in TUNED_FIELDS:
                setattr(config, field, getattr(config, field) * multiplier)
    return config


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    summary.update(stage=CURRENT["stage"], lr_multiplier=float(CURRENT["lr_multiplier"]),
                   matched_information_object=OBJECT_ID, admission=CURRENT["admission"],
                   mei_J=MEI, primary=PRIMARY_NAME)
    return summary


base_summary._matched_information_wrapper = True


def stage_guard(arm, seed, stage, lr_multiplier, selection=None):
    """Card sections 3 and 4: who may run, on which block, at which multiplier."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if arm != CF_ARM and lr_multiplier is not None:
        raise SystemExit("only CF carries a learning-rate multiplier")
    if stage == 0:
        if arm != CF_ARM:
            raise SystemExit("stage 0 is the CF tuning stage only")
        if seed not in STAGE0_BLOCKS:
            raise SystemExit("stage 0 runs on the two tuning blocks 772603 and 772703")
        if lr_multiplier is None or float(lr_multiplier) not in LR_MULTIPLIERS:
            raise SystemExit(f"stage 0 needs an explicit grid multiplier in {LR_MULTIPLIERS}")
        return float(lr_multiplier)
    if seed not in STAGE1_BLOCKS:
        raise SystemExit("stage 1 runs on the five confirmation blocks 772803 ... 773203")
    if arm != CF_ARM:
        return DEFAULT_MULTIPLIER
    if selection is None:
        raise SystemExit("stage-1 CF requires the completed stage-0 SELECTION.json")
    selected = selected_multiplier(selection)
    if lr_multiplier is not None and float(lr_multiplier) != selected:
        raise SystemExit(f"stage-1 CF runs at the selected multiplier {selected}")
    return selected


def selected_multiplier(selection):
    if (selection.get("object_id") != OBJECT_ID or selection.get("card") != CARD
            or selection.get("status") != "complete"):
        raise SystemExit("SELECTION.json is not this object's completed stage-0 selection")
    value = selection.get("selected_lr_multiplier")
    if value is None or float(value) not in LR_MULTIPLIERS:
        raise SystemExit("SELECTION.json carries no grid multiplier")
    return float(value)


def run_fit(arm, seed, stage, lr_multiplier, out, selection=None, admission=None):
    multiplier = stage_guard(arm, seed, stage, lr_multiplier, selection)
    bind()
    CURRENT.update(stage=stage, lr_multiplier=multiplier, admission=admission)
    try:
        return b01.run_fit(arm, seed, out)
    finally:
        CURRENT.update(stage=None, lr_multiplier=DEFAULT_MULTIPLIER, admission=None)


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit, by the frozen B01 reader."""
    bind()
    if summary.get("matched_information_object") != OBJECT_ID:
        raise ValueError("not a matched-information baseline fit")
    scores = b01.arm_panels(summary)
    expected_flag = summary["factorial_arm"] == CF_ARM
    for key in ("learner_config", "evaluation_config"):
        if bool(summary[key].get(CF_FLAG, False)) != expected_flag:
            raise ValueError(f"{summary['factorial_arm']} {key} has the wrong central-input setting")
    if summary["factorial_arm"] != CF_ARM and float(summary.get("lr_multiplier", 1.0)) != 1.0:
        raise ValueError("D1280 must run at its standing learning rates")
    return scores


# ---------------------------------------------------------------------------
# Stage 0 (card section 3, verbatim)
# ---------------------------------------------------------------------------


def select_stage0(summaries):
    """Six planned CF fits in, one multiplier or SELECTION_INCOMPLETE out. No fallback."""
    bind()
    values, failures = {}, []
    for summary in summaries:
        try:
            arm, seed = summary["factorial_arm"], int(summary["block_seed"])
            multiplier = float(summary["lr_multiplier"])
            if summary.get("stage") != 0 or arm != CF_ARM:
                raise ValueError("stage-0 selection takes CF stage-0 fits only")
            if seed not in STAGE0_BLOCKS or multiplier not in LR_MULTIPLIERS:
                raise ValueError("unplanned stage-0 block or multiplier")
            if (multiplier, seed) in {(m, s) for m in values for s in values[m]}:
                raise ValueError("duplicate stage-0 candidate")
            j45 = float(np.mean(fit_endpoint(summary)[ROLLOUTS]))
            if not math.isfinite(j45):
                raise ValueError("non-finite J45")
            values.setdefault(multiplier, {})[seed] = j45
        except (KeyError, TypeError, ValueError) as exc:
            failures.append({"summary": summary.get("factorial_arm"), "failure": str(exc)})
    return select_from_values(values, failures)


def select_from_values(values, failures=()):
    planned = [(m, s) for m in LR_MULTIPLIERS for s in sorted(STAGE0_BLOCKS)]
    missing = [{"lr_multiplier": m, "block_seed": s} for m, s in planned if s not in values.get(m, {})]
    result = {
        "object_id": OBJECT_ID, "card": CARD, "stage": 0,
        "planned_candidates": len(planned), "available_candidates": len(planned) - len(missing),
        "per_seed_J45": {str(m): {str(s): values[m][s] for s in sorted(values.get(m, {}))}
                         for m in LR_MULTIPLIERS},
        "missing_or_invalid": missing, "invalid_inputs": list(failures),
        "rule": "highest mean J45 over the two tuning blocks; an exact tie inside the maximal set "
                "is broken in the fixed order 1, 0.5, 2; any missing, non-finite or integrity-failed "
                "fit ends the object at SELECTION_INCOMPLETE with no fallback",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
    }
    if missing or failures:
        result.update(status="SELECTION_INCOMPLETE", selected_lr_multiplier=None,
                      means_J45=None, tie=None, maximal_set=None)
        return result
    means = {m: float(np.mean([values[m][s] for s in sorted(STAGE0_BLOCKS)])) for m in LR_MULTIPLIERS}
    best = max(means.values())
    maximal = [m for m in LR_MULTIPLIERS if means[m] == best]
    selected = next(m for m in TIE_ORDER if m in maximal)
    result.update(status="complete", selected_lr_multiplier=selected,
                  means_J45={str(m): means[m] for m in LR_MULTIPLIERS},
                  maximal_set=[m for m in maximal], tie=len(maximal) > 1,
                  selection_basis={"mean_J45": means[selected],
                                   "per_seed_J45": {str(s): values[selected][s]
                                                    for s in sorted(STAGE0_BLOCKS)}})
    return result


# ---------------------------------------------------------------------------
# Stage 1 readout (card sections 5 and 6, verbatim)
# ---------------------------------------------------------------------------


def importance_label(mean):
    if mean is None:
        return None
    if mean > MEI:
        return "D_REFERENCE_ABOVE"
    if mean < -MEI:
        return "CF_REFERENCE_ABOVE"
    return "SMALL_SIGNED"


def interval_label(interval):
    """An endpoint exactly zero counts as including zero (card section 6)."""
    if interval is None:
        return None
    low, high = interval
    if low > 0:
        return "INTERVAL_POSITIVE"
    if high < 0:
        return "INTERVAL_NEGATIVE"
    return "INTERVAL_INCLUDES_ZERO"


def paired_statistics(differences):
    """mean(G), s_G, SE_G and the df = 4 working-model interval over the confirmation blocks."""
    values = [float(v) for v in differences]
    count = len(values)
    mean = float(np.mean(values)) if count else None
    sd = float(np.std(values, ddof=1)) if count >= 2 else None
    se = sd / math.sqrt(count) if sd is not None else None
    t = b01.T975.get(count - 1)
    half = t * se if se is not None and t is not None else None
    interval = [mean - half, mean + half] if half is not None else None
    return {
        "available_blocks": count, "planned_blocks": len(STAGE1_BLOCKS), "mean": mean,
        "sample_sd": sd, "se": se, "t_multiplier": t,
        "working_model_95pct_interval": interval,
        "degenerate_zero_variance": bool(sd == 0.0) if sd is not None else None,
        "positive_blocks": int(sum(v > 0 for v in values)),
        "negative_blocks": int(sum(v < 0 for v in values)),
        "zero_blocks": int(sum(v == 0 for v in values)),
        "working_model": "iid-normal paired block differences; Student-t df=4; conditional on the "
                         "stage-0 multiplier and excluding the variation of rerunning the tuning; "
                         "coverage is not validated by five blocks",
    }


def read_primary(statistics):
    mean, interval = statistics["mean"], statistics["working_model_95pct_interval"]
    complete = statistics["available_blocks"] == len(STAGE1_BLOCKS) and mean is not None
    reading = dict(statistics, name=PRIMARY_NAME, mei_J=MEI)
    reading["importance_label"] = importance_label(mean) if complete else None
    reading["interval_label"] = interval_label(interval) if complete else None
    reading["interval_inside_mei"] = (
        None if interval is None else bool(-MEI <= interval[0] and interval[1] <= MEI))
    reading["status"] = "complete" if complete else "PRIMARY_INCOMPLETE_OR_INVALID"
    if statistics["degenerate_zero_variance"]:
        reading["degenerate_note"] = ("s_G = 0: the interval is the point estimate and the "
                                      "working-model computation is degenerate")
    if not complete:
        reading["incomplete_note"] = (
            "fewer than five complete, comparable, finite stage-1 pairs; every credible completed "
            "arm, pair and actual exposure is kept with its available n; n = 1 has no sample SD/SE")
    return reading


def reduce_stage1(summaries, selection):
    bind()
    selected = selected_multiplier(selection)
    levels, endpoints, rows, failures, views, supplied = {}, {}, {}, {}, {}, set()
    for summary in summaries:
        arm, seed = summary.get("factorial_arm"), int(summary.get("block_seed", -1))
        key = (seed, arm)
        if arm not in ARMS or seed not in STAGE1_BLOCKS:
            raise ValueError("stage-1 reduce takes this object's arms on the five fresh blocks")
        if key in supplied:  # a second fit of the same cell, credible or not, is never a choice
            raise ValueError("duplicate stage-1 arm/block")
        supplied.add(key)
        expected = selected if arm == CF_ARM else DEFAULT_MULTIPLIER
        try:
            if summary.get("stage") != 1:
                raise ValueError("not a stage-1 fit")
            if float(summary["lr_multiplier"]) != expected:
                raise ValueError(f"multiplier {summary['lr_multiplier']}, expected {expected}")
            scores = fit_endpoint(summary)
            levels[key] = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
            endpoints[key] = np.asarray(scores[ROLLOUTS], dtype=np.float64)
            rows[key] = {"J_by_rollout": {str(r): levels[key][r] for r in PANEL_ROLLOUTS},
                         "endpoint_scores_J": endpoints[key].tolist(),
                         "launch_sha": summary["launch_sha"], "counts": summary["counts"],
                         "optimizer_calls": summary["optimizer_calls"],
                         "lr_multiplier": float(summary["lr_multiplier"]),
                         "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
                         "peak_rss_bytes": summary.get("peak_rss_bytes")}
            views[key] = b01.comparable_view(summary)
        except (KeyError, TypeError, ValueError) as exc:
            failures[key] = str(exc)
    blocks, differences, curve_values = [], [], {r: [] for r in CURVE_ROLLOUTS}
    for seed in sorted(STAGE1_BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": STAGE1_BLOCKS[seed],
                 "arms": {arm: rows[(seed, arm)] for arm in ARMS if (seed, arm) in rows},
                 "missing_or_invalid_arms": {arm: failures[(seed, arm)] for arm in ARMS
                                             if (seed, arm) in failures}}
        for arm in ARMS:
            if (seed, arm) not in rows and (seed, arm) not in failures:
                entry["missing_or_invalid_arms"][arm] = "not supplied"
        pair = [(seed, "D1280"), (seed, CF_ARM)]
        if all(key in levels for key in pair):
            if views[pair[0]] != views[pair[1]]:
                entry["pair"] = {"status": "incomplete", "failure": "unplanned comparator difference"}
            else:
                world = endpoints[pair[0]] - endpoints[pair[1]]
                value = float(levels[pair[0]][ROLLOUTS] - levels[pair[1]][ROLLOUTS])
                entry["pair"] = {
                    "status": "complete", "G_45": value,
                    "J45": {"D1280": levels[pair[0]][ROLLOUTS], CF_ARM: levels[pair[1]][ROLLOUTS]},
                    "ordered_world_differences": world.tolist(),
                    "conditional_world_sd": float(world.std(ddof=1)),
                    "conditional_world_se": float(world.std(ddof=1) / math.sqrt(shared.EVAL_LANES)),
                    "G_by_rollout": {str(r): float(levels[pair[0]][r] - levels[pair[1]][r])
                                     for r in PANEL_ROLLOUTS}}
                differences.append(value)
                for r in CURVE_ROLLOUTS:
                    curve_values[r].append(float(levels[pair[0]][r] - levels[pair[1]][r]))
        else:
            entry["pair"] = {"status": "incomplete",
                             "missing_operands": [a for a in ARMS if (seed, a) not in levels]}
        blocks.append(entry)
    statistics = paired_statistics(differences)
    primary = read_primary(statistics)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "stage": 1,
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "status": "complete" if primary["status"] == "complete" else "incomplete",
        "stage0_selection": selection, "selected_lr_multiplier": selected,
        "quantity": "G_b = J45(D1280, b) - J45(CF, b); J45 = mean of the 32 final world scores",
        "blocks": blocks, "primary": primary,
        "curves": {str(r): paired_statistics(curve_values[r]) for r in CURVE_ROLLOUTS},
        "levels": {arm: level_statistics(levels, arm) for arm in ARMS},
        "sign_counts": {"positive": primary["positive_blocks"], "negative": primary["negative_blocks"],
                        "zero": primary["zero_blocks"],
                        "listed": {str(seed): (blocks[i]["pair"].get("G_45"))
                                   for i, seed in enumerate(sorted(STAGE1_BLOCKS))},
                        "note": "listed, never used as a pass gate"},
        "interpretation_limit": (
            "five independent confirmation blocks, conditional on the stage-0 multiplier; panel "
            "worlds are nested endpoint conditions; curves are reported, never selected among and "
            "never pooled with older objects; level SDs are descriptive only"),
    }
    return result


def level_statistics(levels, arm):
    values = [levels[(seed, arm)][ROLLOUTS] for seed in sorted(STAGE1_BLOCKS) if (seed, arm) in levels]
    return {"per_block_J45": {str(seed): levels[(seed, arm)][ROLLOUTS]
                              for seed in sorted(STAGE1_BLOCKS) if (seed, arm) in levels},
            "available_blocks": len(values),
            "mean": float(np.mean(values)) if values else None,
            "sample_sd": float(np.std(values, ddof=1)) if len(values) >= 2 else None,
            "note": "descriptive; never a substitute for the paired-difference SD"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--stage", type=int, choices=(0, 1), required=True)
    fit.add_argument("--lr-multiplier", type=float, default=None,
                     help="CF only; stage 0 takes a grid value, stage 1 the selected one")
    fit.add_argument("--selection", type=Path, help="stage-0 SELECTION.json; required for stage-1 CF")
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    sel = sub.add_parser("select-stage0")
    sel.add_argument("--summaries", type=Path, nargs="+", required=True)
    sel.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True)
    red.add_argument("--selection", type=Path, required=True)
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "fit":
        selection = load(args.selection) if args.selection is not None else None
        if args.stage == 1 and args.arm == CF_ARM and selection is None:
            parser.error("stage-1 CF requires --selection with the completed SELECTION.json")
        if args.stage == 0 and selection is not None:
            parser.error("stage 0 precedes the selection")
        # Refuse an out-of-plan stage, block or multiplier before the single-use admission is spent.
        stage_guard(args.arm, args.seed, args.stage, args.lr_multiplier, selection)
        # Nothing scientific has happened yet: no output, environment, learner or evaluator.
        # The literal direction is the launch kernel's guard contract; keep it inline.
        admission = require_admission(__file__, direction="flexible_skill_duration")
        if args.launch_sha is not None and args.launch_sha != admission["sha"]:
            parser.error("--launch-sha must equal the admitted source SHA")
        head = shared.e0._git("rev-parse", "HEAD")
        if head and head != admission["sha"]:
            parser.error("runner source HEAD is not the admitted SHA")
        return run_fit(args.arm, args.seed, args.stage, args.lr_multiplier,
                       args.output_root.resolve(), selection=selection,
                       admission={"sha": admission["sha"],
                                  "command_sha256": admission["command_sha256"]})

    args.output_root.mkdir(parents=True, exist_ok=True)
    if args.command == "select-stage0":
        result = select_stage0([load(p) for p in args.summaries])
        result["input_summaries"] = [str(p) for p in args.summaries]
        shared.write_json(args.output_root / "SELECTION.json", result)
        print(json.dumps({"status": result["status"],
                          "selected_lr_multiplier": result["selected_lr_multiplier"],
                          "means_J45": result["means_J45"]}))
        return 0 if result["status"] == "complete" else 1
    result = reduce_stage1([load(p) for p in args.summaries], load(args.selection))
    result["input_summaries"] = [str(p) for p in args.summaries]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"], "mean_G": result["primary"]["mean"],
                      "importance_label": result["primary"]["importance_label"],
                      "interval_label": result["primary"]["interval_label"]}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
