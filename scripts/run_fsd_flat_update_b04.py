"""FSD flat update B04: the central-input flat learner with a conventional large-minibatch update.

Exploration (six fits, package screen), prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 18:15 PDT - prospective: flat
learner with a conventional large-minibatch update".

Thin entry over the frozen baseline x interruption B01 runner, as the flat-entropy entry is. The
learner is that object's CF_E0005 construction (matched-information CF, `lambda_l` = 0.0005) with two
things changed together:

  sequence_batch_size   32 (the learner's default) -> 1200 ten-step sequences per low-level minibatch:
                        four minibatches per epoch, 60 optimizer steps per rollout instead of 2,250
  actor/critic rate     CF_M1: 1e-4 (the standing base rate)      CF_M5: 5e-4

`sequence_batch_size` is not among the frozen configuration-snapshot fields, so the fit validator
checks the behaviour it causes: the number of low-level optimizer steps of the fit.

Both arms run on blocks 772803, 772903, 773003. The references are the completed CF_E0005 fits of
FSD_FLAT_ENTROPY_B03 and the completed stage-1 D1280 fits of FSD_MATCHED_INFORMATION_BASELINE_B01 on
the same blocks, each read by its own object's validator; they are not contemporaneous.

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
import run_fsd_flat_entropy_b03 as entropy
import run_fsd_matched_information_baseline_b01 as matched
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_FLAT_UPDATE_B04"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 18:15 PDT, flat learner with a conventional large-minibatch update)")
BLOCKS = dict(entropy.BLOCKS)
CF_ARM = matched.CF_ARM  # the frozen runner knows one flat arm by this name
FLAT_REFERENCE = "CF_E0005"
SKILL_REFERENCE = "D1280"
ENTROPY_COEFFICIENT = entropy.ENTROPY_ARMS[FLAT_REFERENCE]
SEQUENCE_BATCH_SIZE = 1200
UPDATE_ARMS = {"CF_M1": 1., "CF_M5": 5.}  # multiplier on the standing base actor/critic rate
ROLLOUTS = matched.ROLLOUTS
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS
EARLY_PANELS, LATE_PANELS = PANEL_ROLLOUTS[:4], PANEL_ROLLOUTS[-4:]  # declared in the notebook entry
DIAGNOSTIC_ROLLOUTS = (1,) + PANEL_ROLLOUTS  # one-based training rollouts
WALL_PLANS = {CF_ARM: 7000.}  # unmeasured for this update law; CF's measured wall as the plan
PRIMARY_NAME = f"J_{ROLLOUTS}"
# Snapshot fields that may differ between a new fit and the CF_E0005 fit of its block.
PAIR_DIFFERENCES = frozenset(matched.TUNED_FIELDS)
LOW_LEVEL_OPTIMIZERS = ("discoverer_actor", "discoverer_critic")  # one step each per minibatch
CURRENT = {"update_arm": None, "admission": None}
_orig_make_config = matched._orig_make_config
_orig_base_summary = shared.base_summary
_FLAG = "_flat_update_wrapper"


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
        current = shared.base_summary  # only ever wrap a plain function, exactly once
        for flag, module in (("_matched_information_wrapper", matched), (entropy._FLAG, entropy)):
            if getattr(current, flag, False):
                current = module._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary


def make_config(arm, envs, seed):
    """The CF_E0005 construction, then this object's minibatch size and learning rate."""
    config = _orig_make_config(arm, envs, seed)
    setattr(config, matched.CF_FLAG, True)
    setattr(config, entropy.ENTROPY_FIELD, ENTROPY_COEFFICIENT)
    update_arm = CURRENT["update_arm"]
    multiplier = entropy.SELECTED_MULTIPLIER if update_arm is None else UPDATE_ARMS[update_arm]
    if multiplier != 1.:
        for field in matched.TUNED_FIELDS:
            setattr(config, field, getattr(config, field) * multiplier)
    if update_arm is not None:  # None reproduces the CF_E0005 construction (tests)
        config.sequence_batch_size = SEQUENCE_BATCH_SIZE
    return config


def expected_low_level_steps(config):
    """Optimizer steps of one fit under this object's minibatch size (hmasd/utils.py sampler law)."""
    sequences = shared.TRAIN_LANES * shared.N_UAVS * (shared.HORIZON // int(config["k"]))
    return int(config["ppo_epochs"]) * math.ceil(sequences / SEQUENCE_BATCH_SIZE) * ROLLOUTS


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["update_arm"]
    summary.update(flat_update_object=OBJECT_ID, update_arm=arm, lr_multiplier=UPDATE_ARMS.get(arm),
                   sequence_batch_size=SEQUENCE_BATCH_SIZE, entropy_coefficient=ENTROPY_COEFFICIENT,
                   admission=CURRENT["admission"], primary=PRIMARY_NAME)
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's six fits: both update arms on the three blocks."""
    if arm not in UPDATE_ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(update_arm=arm, admission=admission)
    try:
        return b01.run_fit(CF_ARM, seed, out)
    finally:
        CURRENT.update(update_arm=None, admission=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit of this object."""
    bind()
    if summary.get("flat_update_object") != OBJECT_ID:
        raise ValueError("not a flat-update fit")
    arm = summary.get("update_arm")
    if arm not in UPDATE_ARMS or int(summary["block_seed"]) not in BLOCKS:
        raise ValueError("not one of this object's six planned fits")
    scores = b01.arm_panels(summary)
    if summary.get("lr_multiplier") != UPDATE_ARMS[arm]:
        raise ValueError(f"{arm} does not carry its declared learning-rate multiplier")
    for key in ("learner_config", "evaluation_config"):
        if (summary[key].get(entropy.ENTROPY_FIELD) != ENTROPY_COEFFICIENT
                or not summary[key].get(matched.CF_FLAG)):
            raise ValueError(f"{arm} {key} is not the declared construction")
    steps = expected_low_level_steps(summary["learner_config"])
    if any(summary["optimizer_calls"][k] != steps for k in LOW_LEVEL_OPTIMIZERS):
        raise ValueError(f"{arm} did not take the {steps} low-level steps of the declared minibatch size")
    return scores


def reference_endpoint(summary):
    """A completed CF_E0005 fit or a completed stage-1 D1280 fit, each by its own object's validator."""
    if int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("the references are fits of the three blocks")
    if summary.get("entropy_arm") == FLAT_REFERENCE:
        return FLAT_REFERENCE, entropy.fit_endpoint(summary)
    if summary.get("factorial_arm") == SKILL_REFERENCE and summary.get("stage") == 1:
        return SKILL_REFERENCE, matched.fit_endpoint(summary)
    raise ValueError("the references are the CF_E0005 and the matched-information D1280 fits")


def pair_view(summary):
    """Everything a new fit shares with the CF_E0005 fit of its block. The launch sha is reported only."""
    common = entropy.host_view(summary)
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in PAIR_DIFFERENCES}
    return common


def diagnostics(summary):
    """Per-rollout learner records already in the summary; absent fields stay None."""
    rows, result = summary["training_rows"], {}
    for rollout in DIAGNOSTIC_ROLLOUTS:
        row = rows[rollout - 1]
        losses = row.get("losses") or {}
        displacement = row.get("relative_initialization_displacement") or {}
        returns = row.get("episode_returns_U") or []
        result[str(rollout)] = {
            "discoverer_policy_loss": losses.get("discoverer_policy_loss"),
            "discoverer_value_loss": losses.get("discoverer_value_loss"),
            "action_entropy": losses.get("action_entropy"),
            "actor_displacement": displacement.get("discoverer_actor"),
            "training_return_U": float(np.mean(returns)) if len(returns) else None}
    losses = [(row.get("losses") or {}).get("discoverer_policy_loss") for row in rows]
    late = [float(np.mean(row["episode_returns_U"])) for row in rows[-11:] if row.get("episode_returns_U")]
    result["mean_policy_loss"] = float(np.mean(losses)) if all(v is not None for v in losses) else None
    result["training_return_U_rollouts_35_45"] = float(np.mean(late)) if late else None
    return result


def fit_row(summary, scores):
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "J_early_window": float(np.mean([level[r] for r in EARLY_PANELS])),
            "J_late_window": float(np.mean([level[r] for r in LATE_PANELS])),
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "lr_discoverer_actor": summary["learner_config"].get("lr_discoverer_actor"),
            "diagnostics": diagnostics(summary),
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def reduce_fits(summaries, references):
    """Six new fits in `summaries`; the CF_E0005 and D1280 fits of the three blocks in `references`."""
    rows, sources, failures, supplied = {}, {}, {}, set()
    for summary, side in [(s, "new") for s in summaries] + [(s, "reference") for s in references]:
        seed = int(summary.get("block_seed", -1))
        label = (summary.get("update_arm") if side == "new"
                 else summary.get("entropy_arm") or summary.get("factorial_arm"))
        try:
            arm, values = ((label, fit_endpoint(summary)) if side == "new" else reference_endpoint(summary))
        except (KeyError, TypeError, ValueError) as exc:
            arm, values = label, None
            failures[(seed, arm)] = str(exc)
        if (seed, arm, side) in supplied:  # a second fit of the same cell is never a choice
            raise ValueError("duplicate arm/block")
        supplied.add((seed, arm, side))
        if values is not None:
            rows[(seed, arm)], sources[(seed, arm)] = fit_row(summary, values), summary
    blocks, arms = [], {}
    for seed in sorted(BLOCKS):
        cells = [(seed, arm) for arm in (*UPDATE_ARMS, FLAT_REFERENCE, SKILL_REFERENCE)]
        blocks.append({"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                       "arms": {arm: rows[(s, arm)] for s, arm in cells if (s, arm) in rows},
                       "missing_or_invalid_arms": {arm: failures.get((s, arm), "not supplied")
                                                   for s, arm in cells if (s, arm) not in rows}})
    for arm in UPDATE_ARMS:
        pairs = []
        for seed in sorted(BLOCKS):
            new, flat, skills = (seed, arm), (seed, FLAT_REFERENCE), (seed, SKILL_REFERENCE)
            entry = {"training_seed": seed}
            if not all(key in rows for key in (new, flat, skills)):
                entry.update(status="incomplete",
                             missing_operands=[a for _, a in (new, flat, skills) if (seed, a) not in rows])
            elif pair_view(sources[new]) != pair_view(sources[flat]):
                entry.update(status="incomplete", failure="unplanned difference from the CF_E0005 reference")
            elif entropy.host_view(sources[new]) != entropy.host_view(sources[skills]):
                entry.update(status="incomplete", failure="unplanned difference from the D1280 reference")
            else:
                entry["status"] = "complete"
                for name, value in (("J45", lambda cell: rows[cell]["J_by_rollout"][str(ROLLOUTS)]),
                                    ("late", lambda cell: rows[cell]["J_late_window"])):
                    entry[f"new_minus_flat_{name}"] = value(new) - value(flat)
                    entry[f"D1280_minus_new_{name}"] = value(skills) - value(new)
                    entry[f"D1280_minus_flat_{name}"] = value(skills) - value(flat)
                entry["late_minus_early_window"] = rows[new]["J_late_window"] - rows[new]["J_early_window"]
                entry["training_return_U_rollouts_35_45"] = {
                    a: rows[(seed, a)]["diagnostics"]["training_return_U_rollouts_35_45"]
                    for a in (arm, FLAT_REFERENCE, SKILL_REFERENCE)}
            pairs.append(entry)
        complete = [p for p in pairs if p["status"] == "complete"]
        arms[arm] = {"lr_multiplier": UPDATE_ARMS[arm], "pairs": pairs,
                     "status": "complete" if len(complete) == len(BLOCKS) else "incomplete"}
        for name in ("new_minus_flat_J45", "D1280_minus_new_J45", "new_minus_flat_late", "D1280_minus_new_late"):
            arms[arm][name] = entropy.described([p[name] for p in complete])
        arms[arm]["blocks_above_flat_in_late_window"] = int(sum(p["new_minus_flat_late"] > 0 for p in complete))
    return {
        "object_id": OBJECT_ID, "card": CARD,
        "reference_object_ids": [entropy.OBJECT_ID, matched.OBJECT_ID],
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "status": "complete" if all(a["status"] == "complete" for a in arms.values()) else "incomplete",
        "quantity": "J45 = mean of the 32 final world scores; window means over panels 5-20 and 30-45; "
                    "differences on the same training and evaluation seeds against completed fits",
        "blocks": blocks, "arms": arms,
        "invalid_inputs": {f"{seed}:{arm}": text for (seed, arm), text in failures.items()},
        "interpretation_limit": (
            "exploration and a package screen (minibatch size, step count and learning rate change "
            "together); three blocks, references not contemporaneous; settings tried on the blocks the "
            "D1280 comparison is read on; no MEI verdict and no claim about the size of a gap"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(UPDATE_ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True, help="this object's six fits")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the completed CF_E0005 (B03) and D1280 (B01 stage 1) summaries of the three blocks")
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
                      "new_minus_flat_late_mean": {a: v["new_minus_flat_late"]["mean"]
                                                   for a, v in result["arms"].items()},
                      "D1280_minus_new_late_mean": {a: v["D1280_minus_new_late"]["mean"]
                                                    for a, v in result["arms"].items()}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
