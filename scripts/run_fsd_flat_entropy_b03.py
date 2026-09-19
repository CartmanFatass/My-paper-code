"""FSD flat entropy B03: the selected central-input flat learner at a smaller entropy coefficient.

Exploration (six fits), prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 15:00 PDT - prospective: flat
learner with a smaller entropy coefficient".

Thin entry over the frozen baseline x interruption B01 runner, as the matched-information and
coordinator-batch entries are: the same collector loop, panel law, summary and fit validation, rebound
to this object's identity. The learner is the matched-information object's stage-1 CF construction
(central snapshot in the flat actor, actor/critic learning rates at the selected multiplier 0.5);
`lambda_l`, the low-level entropy coefficient, is the only field that differs from it.

  CF_E005    lambda_l = 0.005
  CF_E0005   lambda_l = 0.0005     (the completed CF fits ran at 0.05)

Exactly zero is not an arm: the learner records the action entropy as 0 when the coefficient is 0
(hmasd/agent.py), and the entropy trajectory is this object's intermediate observable.

Both arms run on the first three matched-information confirmation blocks. The references are the
completed stage-1 CF and D1280 fits of FSD_MATCHED_INFORMATION_BASELINE_B01 on the same blocks, read
by that object's own validator; they are not contemporaneous.

`fit` is result-bearing and runs only through `scripts/hmasd_launch.py` (runner-side admission).
`reduce` is a pure reading of published summaries and carries no admission.
"""
import argparse
import json
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
OBJECT_ID = "FSD_FLAT_ENTROPY_B03"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 15:00 PDT, flat learner with a smaller entropy coefficient)")
REFERENCE_OBJECT_ID = matched.OBJECT_ID
BLOCKS = {seed: matched.STAGE1_BLOCKS[seed] for seed in (772803, 772903, 773003)}
CF_ARM = matched.CF_ARM  # the frozen runner knows one flat arm by this name
ENTROPY_FIELD = "lambda_l"
ENTROPY_ARMS = {"CF_E005": .005, "CF_E0005": .0005}
REFERENCE_ENTROPY = .05
# runs/flexible_skill_duration/b01_s0_selection/SELECTION.json (committed; a test reads it)
SELECTED_MULTIPLIER = .5
ROLLOUTS = matched.ROLLOUTS
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS
DIAGNOSTIC_ROLLOUTS = (1,) + PANEL_ROLLOUTS  # one-based training rollouts
WALL_PLANS = {CF_ARM: 7000.}  # CF measured about 6,800 s at four concurrent in the reference object
PRIMARY_NAME = f"J_{ROLLOUTS}"
# The only configuration field that may differ between a new fit and the completed CF fit of its block.
PAIR_DIFFERENCES = frozenset({ENTROPY_FIELD})
CURRENT = {"entropy_arm": None, "admission": None}
_orig_make_config = matched._orig_make_config
_orig_base_summary = shared.base_summary
_FLAG = "_flat_entropy_wrapper"


def bind(wrap=False):
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand.

    Readers need the identities only. A fit also wraps `shared.base_summary`, and `run_fit` takes the
    wrapper off again, so a later reader or fit of another object in the same process is not marked.
    """
    global shared, _orig_base_summary
    shared = b01.shared
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = {CF_ARM: matched.ARMS[CF_ARM]}, CF_ARM
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.make_config = make_config
    if wrap:
        # Only ever wrap the plain function, exactly once.
        current = shared.base_summary
        if getattr(current, "_matched_information_wrapper", False):
            current = matched._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary


def make_config(arm, envs, seed):
    """The matched-information stage-1 CF construction, then this object's entropy coefficient."""
    config = _orig_make_config(arm, envs, seed)
    setattr(config, matched.CF_FLAG, True)
    for field in matched.TUNED_FIELDS:
        setattr(config, field, getattr(config, field) * SELECTED_MULTIPLIER)
    if CURRENT["entropy_arm"] is not None:  # None reproduces the reference construction (tests)
        setattr(config, ENTROPY_FIELD, ENTROPY_ARMS[CURRENT["entropy_arm"]])
    return config


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["entropy_arm"]
    summary.update(flat_entropy_object=OBJECT_ID, entropy_arm=arm,
                   entropy_coefficient=ENTROPY_ARMS.get(arm), lr_multiplier=SELECTED_MULTIPLIER,
                   admission=CURRENT["admission"], primary=PRIMARY_NAME)
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's six fits: both entropy arms on the three blocks."""
    if arm not in ENTROPY_ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(entropy_arm=arm, admission=admission)
    try:
        return b01.run_fit(CF_ARM, seed, out)
    finally:
        CURRENT.update(entropy_arm=None, admission=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit of this object."""
    bind()
    if summary.get("flat_entropy_object") != OBJECT_ID:
        raise ValueError("not a flat-entropy fit")
    arm = summary.get("entropy_arm")
    if arm not in ENTROPY_ARMS or int(summary["block_seed"]) not in BLOCKS:
        raise ValueError("not one of this object's six planned fits")
    scores = b01.arm_panels(summary)
    for key in ("learner_config", "evaluation_config"):
        if summary[key].get(ENTROPY_FIELD) != ENTROPY_ARMS[arm] or not summary[key].get(matched.CF_FLAG):
            raise ValueError(f"{arm} {key} is not the declared construction")
    return scores


def reference_endpoint(summary):
    """A completed stage-1 fit of the matched-information object, by its own validator."""
    if (summary.get("factorial_arm") not in matched.ARMS or summary.get("stage") != 1
            or int(summary.get("block_seed", -1)) not in BLOCKS):
        raise ValueError("the references are the matched-information stage-1 fits of the three blocks")
    scores = matched.fit_endpoint(summary)
    if summary["factorial_arm"] == CF_ARM and (
            float(summary.get("lr_multiplier", 0.)) != SELECTED_MULTIPLIER
            or summary["learner_config"].get(ENTROPY_FIELD) != REFERENCE_ENTROPY):
        raise ValueError("the CF reference is not the selected construction")
    return scores


def host_view(summary):
    """What every fit of a block must share, whatever its learner."""
    return {k: summary[k] for k in ("host", "device", "torch_threads", "learner_precision",
                                    "reward_return_precision", "native_score_factor", "rollouts",
                                    "panel_rollouts", "training_seed", "evaluation_seed")}


def pair_view(summary):
    """Everything a new fit shares with the CF fit of its block. The launch sha is reported, not compared."""
    common = host_view(summary)
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in PAIR_DIFFERENCES}
    return common


def diagnostics(summary):
    """Per-rollout learner records already in the summary; absent fields stay None."""
    rows = summary["training_rows"]
    result = {}
    for rollout in DIAGNOSTIC_ROLLOUTS:
        row = rows[rollout - 1]
        losses = row.get("losses") or {}
        displacement = row.get("relative_initialization_displacement") or {}
        returns = row.get("episode_returns_U") or []
        result[str(rollout)] = {
            "action_entropy": losses.get("action_entropy"),
            "discoverer_value_loss": losses.get("discoverer_value_loss"),
            "actor_displacement": displacement.get("discoverer_actor"),
            "training_return_U": float(np.mean(returns)) if len(returns) else None}
    return result


def fit_row(summary, scores):
    return {"J_by_rollout": {str(r): float(np.mean(scores[r])) for r in PANEL_ROLLOUTS},
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            ENTROPY_FIELD: summary["learner_config"].get(ENTROPY_FIELD),
            "diagnostics": diagnostics(summary),
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def described(values):
    """Three pairs: a description, not an interval anyone should lean on."""
    values = [float(v) for v in values]
    count = len(values)
    sd = float(np.std(values, ddof=1)) if count >= 2 else None
    t = b01.T975.get(count - 1)
    half = t * sd / count ** .5 if sd is not None and t is not None else None
    mean = float(np.mean(values)) if count else None
    return {"available_blocks": count, "planned_blocks": len(BLOCKS), "mean": mean,
            "min": min(values) if count else None, "max": max(values) if count else None,
            "sample_sd": sd, "t_multiplier": t,
            "working_model_95pct_interval": [mean - half, mean + half] if half is not None else None,
            "positive_blocks": int(sum(v > 0 for v in values)),
            "negative_blocks": int(sum(v < 0 for v in values)),
            "working_model": "iid-normal paired block differences; Student-t on the available blocks; "
                             "references not contemporaneous; coverage not validated"}


def reduce_fits(summaries, references):
    """Six new fits in `summaries`; the completed CF and D1280 fits of the three blocks in `references`."""
    scores, rows, sources, failures, supplied = {}, {}, {}, {}, set()
    for summary, reader, side in ([(s, fit_endpoint, "new") for s in summaries]
                                  + [(s, reference_endpoint, "reference") for s in references]):
        arm = summary.get("entropy_arm") if side == "new" else summary.get("factorial_arm")
        key = (int(summary.get("block_seed", -1)), arm)
        if key in supplied:  # a second fit of the same cell, credible or not, is never a choice
            raise ValueError("duplicate arm/block")
        supplied.add(key)
        try:
            values = reader(summary)
        except (KeyError, TypeError, ValueError) as exc:
            failures[key] = str(exc)
            continue
        scores[key], rows[key], sources[key] = values, fit_row(summary, values), summary
    level = lambda key, rollout=ROLLOUTS: float(np.mean(scores[key][rollout]))
    blocks, arms = [], {}
    for seed in sorted(BLOCKS):
        cells = [(seed, arm) for arm in (*ENTROPY_ARMS, CF_ARM, "D1280")]
        blocks.append({"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                       "arms": {arm: rows[(s, arm)] for s, arm in cells if (s, arm) in rows},
                       "missing_or_invalid_arms": {arm: failures.get((s, arm), "not supplied")
                                                   for s, arm in cells if (s, arm) not in rows}})
    for arm in ENTROPY_ARMS:
        pairs, against_cf, against_d, rises = [], [], [], []
        for seed in sorted(BLOCKS):
            new, flat, skills = (seed, arm), (seed, CF_ARM), (seed, "D1280")
            entry = {"training_seed": seed}
            if not all(key in scores for key in (new, flat, skills)):
                entry.update(status="incomplete",
                             missing_operands=[a for _, a in (new, flat, skills) if (seed, a) not in scores])
            elif pair_view(sources[new]) != pair_view(sources[flat]):
                entry.update(status="incomplete", failure="unplanned difference from the CF reference")
            elif host_view(sources[new]) != host_view(sources[skills]):
                entry.update(status="incomplete", failure="unplanned difference from the D1280 reference")
            else:
                entry.update(
                    status="complete",
                    J45={arm: level(new), CF_ARM: level(flat), "D1280": level(skills)},
                    rise_J45_minus_J5=level(new) - level(new, PANEL_ROLLOUTS[0]),
                    new_minus_CF_J45=level(new) - level(flat),
                    D1280_minus_new_J45=level(skills) - level(new),
                    D1280_minus_CF_J45=level(skills) - level(flat),
                    new_minus_CF_by_rollout={str(r): level(new, r) - level(flat, r) for r in PANEL_ROLLOUTS},
                    D1280_minus_new_by_rollout={str(r): level(skills, r) - level(new, r)
                                                for r in PANEL_ROLLOUTS})
                against_cf.append(entry["new_minus_CF_J45"])
                against_d.append(entry["D1280_minus_new_J45"])
                rises.append(entry["rise_J45_minus_J5"])
            pairs.append(entry)
        complete = [p for p in pairs if p["status"] == "complete"]
        arms[arm] = {
            ENTROPY_FIELD: ENTROPY_ARMS[arm], "pairs": pairs,
            "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
            "new_minus_CF_J45": described(against_cf), "D1280_minus_new_J45": described(against_d),
            "fits_with_J45_at_least_J5": int(sum(v >= 0 for v in rises)),
            "fits_above_CF_at_J45": int(sum(v > 0 for v in against_cf)),
            "fits_with_smaller_gap_than_CF": int(sum(p["D1280_minus_new_J45"] < p["D1280_minus_CF_J45"]
                                                     for p in complete)),
            "J_by_rollout_mean": {str(r): float(np.mean([level((p["training_seed"], arm), r) for p in complete]))
                                  for r in PANEL_ROLLOUTS} if complete else None}
    return {
        "object_id": OBJECT_ID, "card": CARD, "reference_object_id": REFERENCE_OBJECT_ID,
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "status": "complete" if all(a["status"] == "complete" for a in arms.values()) else "incomplete",
        "quantity": "J45 = mean of the 32 final world scores; differences are taken on the same training and "
                    "evaluation seeds against the completed matched-information stage-1 fits",
        "blocks": blocks, "arms": arms,
        "invalid_inputs": {f"{seed}:{arm}": text for (seed, arm), text in failures.items()},
        "interpretation_limit": (
            "exploration; three blocks, references not contemporaneous; two entropy values were tried on the "
            "blocks the D1280 comparison is read on, so any remaining-gap number is selected on its own "
            "evaluation blocks; no MEI verdict and no claim about the size of a matched-information gap"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ENTROPY_ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True, help="this object's six fits")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the completed matched-information stage-1 CF and D1280 summaries of the three blocks")
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
    result = reduce_fits([load(p) for p in args.summaries], [load(p) for p in args.references])
    result["input_summaries"] = [str(p) for p in args.summaries]
    result["reference_summaries"] = [str(p) for p in args.references]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"],
                      "new_minus_CF_mean": {a: v["new_minus_CF_J45"]["mean"] for a, v in result["arms"].items()},
                      "D1280_minus_new_mean": {a: v["D1280_minus_new_J45"]["mean"]
                                               for a, v in result["arms"].items()}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
