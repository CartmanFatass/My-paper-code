"""Frozen labels and per-operand publication for one C/M training block."""
import math

import numpy as np

from experiments.candidates.acvc.cluster_deployment_b01.protocol import make_cluster

OBJECT = "ACVC_CLUSTER_MAPPO_COMPARISON_B01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_MAPPO_COMPARISON_B01_SCIENCE_CARD_20260914.md"
MASTER = 28331
EVALUATION_NAMESPACE = 38331
UPSTREAM_SHA = "de66d7a4b23fac2513f56f96f73b3f5cb96695ac"
TRAIN_EPISODES, EVAL_EPISODES, HORIZON = 4096, 64, 256
ARMS = {"C": ("C", "F", "dwell"), "M": ("M",)}
PLANS = {"C": 1400, "M": 2400}


def panel(rows, arm):
    selected = sorted((r for r in rows if r.get("phase") == "eval" and r.get("arm") == arm),
                      key=lambda r: r.get("episode", -1))
    complete = len(selected) == EVAL_EPISODES and [r.get("episode") for r in selected] == list(range(EVAL_EPISODES))
    complete = complete and all(
        r.get("master") == MASTER and r.get("evaluation_namespace") == EVALUATION_NAMESPACE
        and r.get("checkpoint_episode") == TRAIN_EPISODES
        and r.get("reset_seed") == 100000 * EVALUATION_NAMESPACE + 2000 + r["episode"]
        and r.get("steps") == HORIZON
        and isinstance(r.get("S"), (float, int)) and math.isfinite(r["S"])
        and isinstance(r.get("J"), (float, int)) and math.isfinite(r["J"])
        and r["J"] == r["S"] / HORIZON for r in selected)
    scores = [r["J"] for r in selected] if complete else None
    return dict(complete=complete, available_episodes=len(selected), scores_J=scores,
                mean_J=float(np.mean(scores)) if complete else None,
                mean_S=float(np.mean([r["S"] for r in selected])) if complete else None)


def fit_eligible(summary, fitted_arm):
    if not summary:
        return False
    c = summary.get("counts", {})
    common = (summary.get("object") == OBJECT and summary.get("arm") == fitted_arm
              and summary.get("master") == MASTER
              and summary.get("evaluation_namespace") == EVALUATION_NAMESPACE
              and summary.get("fit_complete") is True
              and c.get("train_episodes") == TRAIN_EPISODES
              and c.get("train_team_steps") == TRAIN_EPISODES * HORIZON
              and c.get("rollouts") == TRAIN_EPISODES // 2
              and c.get("final_checkpoints") == 1)
    if fitted_arm == "C":
        return common and c.get("optimizer_steps") == 8192
    return common and c.get("actor_optimizer_steps") == 8192 and c.get("critic_optimizer_steps") == 8192


def contrast(left, right, *, primary=False):
    if left is None or right is None:
        return dict(complete=False, reading="INCOMPLETE", mean_J=None)
    d = np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)
    mean = float(np.mean(d))
    label = "UP" if mean > .01 else "DOWN" if mean < -.01 else "WITHIN_MEI"
    if primary:
        label = {"UP": "F_ABOVE_MEI", "DOWN": "M_ABOVE_MEI", "WITHIN_MEI": "WITHIN_MEI"}[label]
    sd = float(np.std(d, ddof=1))
    return dict(complete=True, reading=label, mean_J=mean, mean_S=mean * HORIZON,
                sample_SD_J=sd, conditional_SE_J=sd / math.sqrt(len(d)),
                paired_world_differences_J=d.tolist(), n_worlds=len(d),
                adverse=int((d < 0).sum()), favorable=int((d > 0).sum()), zero=int((d == 0).sum()),
                minimum_J=float(d.min()), maximum_J=float(d.max()))


def reduce_pair(summaries):
    values, panels, eligible = {}, {}, {}
    for fit in ("C", "M"):
        s = summaries.get(fit)
        eligible[fit] = fit_eligible(s, fit)
        for arm in ARMS[fit]:
            raw = s.get("panels", {}).get(arm, {}) if s else {}
            scores = raw.get("scores_J")
            valid = (eligible[fit] and raw.get("complete") is True
                     and isinstance(scores, list) and len(scores) == EVAL_EPISODES
                     and all(isinstance(x, (int, float)) and math.isfinite(x) for x in scores))
            panels[arm] = dict(raw, eligible_for_bound_comparison=valid)
            values[arm] = scores if valid else None
    comparisons = {a + "-" + b: contrast(values[a], values[b], primary=(a, b) == ("F", "M"))
                   for a, b in (("F", "M"), ("C", "M"), ("F", "C"), ("F", "dwell"))}
    return dict(object=OBJECT, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE,
                complete=all(v["complete"] for v in comparisons.values()), eligible_fits=eligible,
                panels=panels, primary="F-M", contrasts=comparisons, MEI_J=.01,
                training_blocks=1, claim_ceiling="One complete-method training block; conditional-world SD/SE only.")
