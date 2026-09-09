"""Fixed paired contrasts; evaluation episodes are conditional sampling units."""
import json
from pathlib import Path

import numpy as np


def reading(value):
    return "UP" if value > .01 else "DOWN" if value < -.01 else "WITHIN"


def panel(rows):
    scores = {a: np.array([r["J"] for r in sorted(rows, key=lambda r: r["episode"])
                           if r["phase"] == "eval" and r["arm"] == a], dtype=np.float64)
              for a in ("T", "G", "C", "F")}
    contrasts = {}
    for a, b in (("T", "C"), ("T", "F"), ("T", "G"), ("G", "C"), ("G", "F")):
        difference = scores[a] - scores[b]
        mean = float(difference.mean())
        contrasts[a + "-" + b] = dict(mean_J=mean, mean_S=mean * 256,
                                       conditional_SE_J=float(difference.std(ddof=1) / np.sqrt(len(difference))),
                                       n_joint_episodes=len(difference), reading=reading(mean),
                                       exceeds_quarter_S=mean * 256 > .25,
                                       paired_differences_J=difference.tolist())
    summary = min(contrasts["T-C"]["mean_J"], contrasts["T-F"]["mean_J"])
    return dict(arm_mean_J={a: float(v.mean()) for a, v in scores.items()}, contrasts=contrasts,
                primary_min_of_means_J=summary, primary_min_of_means_S=summary * 256,
                primary_summary_SE=None,
                uncertainty="Fixed contrasts: paired episode sample SD/sqrt(n), conditional on one fitted instance. No training-seed uncertainty or selected-max SE.")


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
