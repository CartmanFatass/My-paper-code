"""FSD host headroom B01: tuned FLAT versus D1280 / I1280 at 45 rollouts, five seeds, and the readout.

Thin entry over the frozen baseline x interruption B01 runner (`run_fsd_baseline_interruption_b01.py`):
the same collector loop, arms, panel law and fit validation, rebound to this object's identity, blocks,
45 rollouts and nine panels. Stage 0 tunes only the FLAT learning rates over three multipliers on two
seeds and selects by mean J45; stage 1 runs FLAT at the selected multiplier, D1280 and I1280 at their
standing recipes on five fresh seeds. The reduce applies the card's pre-registered 2s / 1s rule.
Card: docs/research/candidates/flexible_skill_duration/FSD_HOST_HEADROOM_B01_PROSPECTIVE_CARD_20260916.md
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

import run_fsd_baseline_interruption_b01 as b01

shared = b01.shared
OBJECT_ID = "FSD_HOST_HEADROOM_B01"
CARD = ("docs/research/candidates/flexible_skill_duration/"
        "FSD_HOST_HEADROOM_B01_PROSPECTIVE_CARD_20260916.md")
STAGE0_BLOCKS = {772603: 782603, 772703: 782703}
STAGE1_BLOCKS = {772803: 782803, 772903: 782903, 773003: 783003, 773103: 783103, 773203: 783203}
BLOCKS = {**STAGE0_BLOCKS, **STAGE1_BLOCKS}
ROLLOUTS = 45
PANEL_ROLLOUTS = tuple(range(5, ROLLOUTS + 1, 5))
LR_MULTIPLIERS = (0.5, 1.0, 2.0)
DEFAULT_MULTIPLIER = 1.0
WALL_PLANS = {"FLAT": 7800., "D1280": 10300., "I1280": 19700.}
MEI_PRIOR = .08  # recorded block SD of an arm level on this host (B01, rollout 15); the rule uses the measured s
CONTRASTS = {"H": {"D1280": 1., "FLAT": -1.}, "HI": {"I1280": 1., "FLAT": -1.}, "SI": {"I1280": 1., "D1280": -1.}}
LABELS = {"H": ("HIERARCHY_ABOVE", "FLAT_ABOVE"), "HI": ("HIERARCHY_ABOVE", "FLAT_ABOVE"),
          "SI": ("INTERRUPTION_ABOVE", "INTERRUPTION_BELOW")}
SIGN_COUNT = 4  # of 5 seeds
TUNED_FIELDS = ("lr_discoverer_actor", "lr_discoverer_critic")
CURRENT = {"stage": None, "lr_multiplier": DEFAULT_MULTIPLIER}
_orig_make_config, _orig_base_summary = b01.make_config, shared.base_summary


def bind():
    """Rebind the frozen runner's identities to this object; the loop, arms and validation are unchanged."""
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.PLANNED_CONFIG_DIFFERENCES = frozenset(b01.PLANNED_CONFIG_DIFFERENCES | set(TUNED_FIELDS))
    b01.make_config, shared.base_summary = make_config, base_summary


def make_config(arm, envs, seed):
    config = _orig_make_config(arm, envs, seed)
    if arm == "FLAT" and CURRENT["lr_multiplier"] != 1.0:
        for field in TUNED_FIELDS:
            setattr(config, field, getattr(config, field) * CURRENT["lr_multiplier"])
    return config


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    summary.update(stage=CURRENT["stage"], lr_multiplier=CURRENT["lr_multiplier"], headroom_object=OBJECT_ID)
    return summary


def run_fit(arm, seed, stage, lr_multiplier, out):
    if stage == 0 and (arm != "FLAT" or seed not in STAGE0_BLOCKS or lr_multiplier not in LR_MULTIPLIERS):
        raise SystemExit("stage 0 is FLAT only, on the two tuning blocks, at a grid multiplier")
    if stage == 1 and (seed not in STAGE1_BLOCKS or (arm != "FLAT" and lr_multiplier != 1.0)):
        raise SystemExit("stage 1 uses the five fresh blocks; only FLAT carries a multiplier")
    bind()
    CURRENT.update(stage=stage, lr_multiplier=float(lr_multiplier))
    return b01.run_fit(arm, seed, out)


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit (the frozen B01 reader), keyed by panel rollout."""
    bind()
    if summary.get("headroom_object") != OBJECT_ID:
        raise ValueError("not a host-headroom fit")
    return b01.arm_panels(summary)


def select_stage0(summaries):
    bind()
    values = {}
    for s in summaries:
        if s.get("stage") != 0 or s["factorial_arm"] != "FLAT":
            raise ValueError("stage-0 selection takes FLAT stage-0 fits only")
        j45 = float(np.mean(fit_endpoint(s)[ROLLOUTS]))
        values.setdefault(float(s["lr_multiplier"]), {})[int(s["block_seed"])] = j45
    return select_from_values(values)


def select_from_values(values):
    """Highest mean J45 over the two tuning seeds; ties go to the default multiplier."""
    means = {}
    for m in LR_MULTIPLIERS:
        per_seed = values.get(m, {})
        if set(per_seed) != set(STAGE0_BLOCKS):
            raise ValueError(f"multiplier {m} lacks both tuning seeds")
        means[m] = float(np.mean(list(per_seed.values())))
    best = max(means.values())
    winners = [m for m in LR_MULTIPLIERS if means[m] == best]
    selected = DEFAULT_MULTIPLIER if DEFAULT_MULTIPLIER in winners else winners[0]
    return {"object_id": OBJECT_ID, "card": CARD, "selected_lr_multiplier": selected, "means_J45": means,
            "per_seed_J45": {str(m): {str(k): v for k, v in values[m].items()} for m in LR_MULTIPLIERS},
            "rule": "highest mean J45 over the two stage-0 seeds; ties go to the default multiplier 1.0",
            "tie": len(winners) > 1}


def read_rule(vals, s, names):
    """The card's pre-registered rule: above (> +2s, positive in 4 of 5), inside +/-1s, below (< -2s, negative in 4 of 5)."""
    vals = [float(v) for v in vals]
    mean = float(np.mean(vals))
    positive, negative = sum(v > 0 for v in vals), sum(v < 0 for v in vals)
    if s is None or not s > 0 or len(vals) != len(STAGE1_BLOCKS):
        return "UNRESOLVED"
    if mean > 2 * s and positive >= SIGN_COUNT:
        return names[0]
    if abs(mean) < s:
        return "INDISTINGUISHABLE"
    if mean < -2 * s and negative >= SIGN_COUNT:
        return names[1]
    return "UNRESOLVED"


def contrasts_from_levels(levels, s=None):
    """levels: {arm: {seed: {panel_rollout: J}}} -> contrast statistics and labels; pooled s from the endpoint."""
    seeds = sorted(STAGE1_BLOCKS)
    arms = tuple(CONTRAST_ARMS)
    if s is None:
        variances = [float(np.var([levels[a][k][ROLLOUTS] for k in seeds], ddof=1)) for a in arms]
        s = math.sqrt(float(np.mean(variances)))
    out = {"pooled_seed_sd_J45": s, "pooled_df": len(arms) * (len(seeds) - 1), "mei_prior": MEI_PRIOR,
           "mei_used_2s": 2 * s, "contrasts": {}, "curves": {}, "levels": {}}
    for a in arms:
        end = [levels[a][k][ROLLOUTS] for k in seeds]
        out["levels"][a] = {"per_seed_J45": dict(zip(map(str, seeds), map(float, end))),
                            **b01.block_statistics(end, len(seeds)), "reference_context_J": .67}
    for name, weights in CONTRASTS.items():
        per_seed = [sum(w * levels[a][k][ROLLOUTS] for a, w in weights.items()) for k in seeds]
        stats = b01.block_statistics(per_seed, len(seeds))
        stats.update(name=f"{name}_{ROLLOUTS}", per_seed=dict(zip(map(str, seeds), map(float, per_seed))),
                     positive_seeds=int(sum(v > 0 for v in per_seed)), negative_seeds=int(sum(v < 0 for v in per_seed)),
                     label=read_rule(per_seed, s, LABELS[name]))
        out["contrasts"][name] = stats
        out["curves"][name] = {str(r): b01.block_statistics(
            [sum(w * levels[a][k][r] for a, w in weights.items()) for k in seeds], len(seeds)) for r in PANEL_ROLLOUTS}
    out["primary"] = out["contrasts"]["H"]["label"]
    return out


CONTRAST_ARMS = ("FLAT", "D1280", "I1280")


def reduce_stage1(summaries, selection):
    bind()
    selected = float(selection["selected_lr_multiplier"])
    levels = {a: {} for a in CONTRAST_ARMS}
    views = {}
    for s in summaries:
        arm, seed = s["factorial_arm"], int(s["block_seed"])
        if s.get("stage") != 1 or seed not in STAGE1_BLOCKS:
            raise ValueError("stage-1 reduce takes stage-1 fits on the five fresh blocks")
        expected = selected if arm == "FLAT" else 1.0
        if float(s["lr_multiplier"]) != expected:
            raise ValueError(f"{arm} {seed} at multiplier {s['lr_multiplier']}, expected {expected}")
        scores = fit_endpoint(s)
        levels[arm][seed] = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
        views.setdefault(seed, {})[arm] = b01.comparable_view(s)
    complete = all(set(levels[a]) == set(STAGE1_BLOCKS) for a in CONTRAST_ARMS)
    for seed, by_arm in views.items():
        if len({json.dumps(v, sort_keys=True) for v in by_arm.values()}) != 1:
            raise ValueError(f"arms of block {seed} differ outside the planned fields")
    result = {"object_id": OBJECT_ID, "card": CARD, "launch_sha": shared.e0._git("rev-parse", "HEAD"),
              "status": "complete" if complete else "incomplete", "stage0_selection": selection,
              "rule": "pre-registered: above = mean > +2s and same sign in 4 of 5 seeds; inside = |mean| < 1s; "
                      "below = mean < -2s and same sign in 4 of 5; otherwise UNRESOLVED; s = pooled across-seed SD of J45",
              "interpretation_limit": "five independent training seeds per arm; panel worlds are nested endpoint conditions; "
                                      "no pooling with earlier objects; lifecycle consequences are queued, not decided"}
    if complete:
        result.update(contrasts_from_levels(levels))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(b01.ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--stage", type=int, choices=(0, 1), required=True)
    fit.add_argument("--lr-multiplier", type=float, default=DEFAULT_MULTIPLIER)
    fit.add_argument("--output-root", type=Path, required=True)
    sel = sub.add_parser("select-stage0")
    sel.add_argument("--summaries", type=Path, nargs="+", required=True)
    sel.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True)
    red.add_argument("--selection", type=Path, required=True)
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "fit":
        return run_fit(args.arm, args.seed, args.stage, args.lr_multiplier, args.output_root.resolve())
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    if args.command == "select-stage0":
        result = select_stage0([load(p) for p in args.summaries])
        result["input_summaries"] = [str(p) for p in args.summaries]
        args.output_root.mkdir(parents=True, exist_ok=True)
        shared.write_json(args.output_root / "SELECTION.json", result)
        print(json.dumps({"selected_lr_multiplier": result["selected_lr_multiplier"], "means_J45": result["means_J45"]}))
        return 0
    result = reduce_stage1([load(p) for p in args.summaries], load(args.selection))
    result["input_summaries"] = [str(p) for p in args.summaries]
    args.output_root.mkdir(parents=True, exist_ok=True)
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"], "primary": result.get("primary")}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
