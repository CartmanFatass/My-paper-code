"""Own-history fixed F in training, and the one common-F endpoint comparison."""
import math

import numpy as np

from experiments.candidates.acvc.native_link_loss_b01.binding import Binding
from experiments.candidates.acvc.native_link_loss_b01.report import reading


OBJECT = "ACVC_FIXED_F_TRAINING_USE_B01"
CARD = "docs/research/candidates/acvc/ACVC_FIXED_F_TRAINING_USE_B01_SCIENCE_CARD_20260912.md"
MASTER = 20261
EVALUATION_NAMESPACE = 30261
CAPS = {"whole_supervised_arm": 270, "native_sum": 540,
        "future_support": 660, "future_complete": 1200}


class FixedF:
    """A fresh instance owns one episode; no actor/density or replay state is changed."""
    def __init__(self):
        self.binding = Binding()
        self.counts = dict(training_F_agent_ticks=0, training_F_opportunities=0,
                           training_F_retrace=0)

    def __call__(self, obs, proposal):
        _z, mask, correction = self.binding.observe(obs, proposal)
        self.counts["training_F_agent_ticks"] += len(mask)
        self.counts["training_F_opportunities"] += int(mask.sum())
        self.counts["training_F_retrace"] += int(mask.sum())
        return np.where(mask[:, None], correction, proposal).astype(np.float32)


def final_F_panel(rows, expected):
    panel = [r for r in rows if r.get("phase") == "eval"]
    complete = (len(panel) == expected and all(r["arm"] == "F" for r in panel)
                and {r["episode"] for r in panel} == set(range(expected))
                and all(math.isfinite(r["J"]) and math.isfinite(r["S"]) for r in panel))
    return {"complete": complete, "arm_mean_J": {
        "F": float(np.mean([r["J"] for r in panel])) if complete else None},
        "primaries": [], "contrasts": {},
        "scope": "One fitted arm's final F panel; the primary requires both fresh fits."}


def paired_primary(control, treatment, expected=64):
    panels = [[r for r in rows if r.get("phase") == "eval"]
              for rows in (control, treatment)]
    if not all(final_F_panel(rows, expected)["complete"] for rows in panels):
        return {"complete": False, "reading": "INCOMPLETE",
                "limit": "Both complete final F panels are required; no partial primary."}
    c, t = [{r["episode"]: r for r in rows} for rows in panels]
    if any(c[e]["reset_seed"] != t[e]["reset_seed"] for e in range(expected)):
        return {"complete": False, "reading": "INCOMPLETE", "limit": "Unmatched final worlds."}
    differences = [t[e]["J"] - c[e]["J"] for e in range(expected)]
    mean = float(np.mean(differences))
    return {"complete": True, "n_training_pairs": 1, "n_paired_worlds": expected,
            "paired_differences_J": differences, "mean_J": mean, "mean_S": mean * 256,
            "conditional_SE_J": float(np.std(differences, ddof=1) / math.sqrt(expected)),
            "reading": reading(mean), "minimum_J": min(differences),
            "adverse_worlds": sum(x < 0 for x in differences),
            "control_mean_J": float(np.mean([c[e]["J"] for e in range(expected)])),
            "treatment_mean_J": float(np.mean([t[e]["J"] for e in range(expected)])),
            "uncertainty": "Conditional on this one fitted pair; no training-population uncertainty."}
