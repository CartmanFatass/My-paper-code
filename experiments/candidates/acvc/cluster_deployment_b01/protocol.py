"""One C-trained cluster endpoint and its three private deployment panels."""
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.candidates.acvc.native_link_loss_b01.report import reading
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real


OBJECT = "ACVC_CLUSTER_DEPLOYMENT_B01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B01_SCIENCE_CARD_20260912.md"
MASTER = 21457
EVALUATION_NAMESPACE = 31457
ARMS = ("C", "F", "dwell")
CAPS = dict(whole_supervised_task=600, cumulative_runtime_support=600, complete_charge=1200)


def make_cluster(seed, base_class=None, adapter_class=None):
    if base_class is None:
        from envs.pettingzoo.uav_env import MultiUAVEnv
        base_class = MultiUAVEnv

    def cluster_constructor(**kwargs):
        kwargs["user_distribution"] = "cluster"
        return base_class(**kwargs)

    return make_real(seed, base_class=cluster_constructor, adapter_class=adapter_class)


def final_panel(rows):
    panels = {}
    values = {}
    for arm in ARMS:
        selected = sorted((r for r in rows if r.get("phase") == "eval" and r.get("arm") == arm),
                          key=lambda r: r["episode"])
        complete = len(selected) == 64 and [r["episode"] for r in selected] == list(range(64))
        complete = complete and all(
            r["master"] == MASTER and r["evaluation_namespace"] == EVALUATION_NAMESPACE
            and r["reset_seed"] == 100000 * EVALUATION_NAMESPACE + 2000 + r["episode"]
            and r["steps"] == 256 and r["S"] is not None and r["J"] is not None
            and math.isfinite(r["S"]) and math.isfinite(r["J"]) and r["J"] == r["S"] / 256
            for r in selected
        )
        panels[arm] = {"complete": complete, "available_episodes": len(selected),
                       "mean_S": float(np.mean([r["S"] for r in selected])) if complete else None,
                       "mean_J": float(np.mean([r["J"] for r in selected])) if complete else None}
        if complete:
            values[arm] = np.asarray([r["J"] for r in selected], dtype=np.float64)
    contrasts = {}
    for first, second in (("F", "C"), ("F", "dwell"), ("dwell", "C")):
        name = first + "-" + second
        if first not in values or second not in values:
            contrasts[name] = {"complete": False, "reading": "INCOMPLETE", "mean_J": None,
                               "dependent_arms": [first, second]}
            continue
        difference = values[first] - values[second]
        mean = float(np.mean(difference))
        sd = float(np.std(difference, ddof=1))
        contrasts[name] = {
            "complete": True, "episode_ids": list(range(64)), "n_joint_episodes": 64,
            "paired_differences_J": difference.tolist(), "mean_J": mean, "mean_S": mean * 256,
            "sample_SD_J": sd, "conditional_SE_J": sd / math.sqrt(64),
            "minimum_J": float(difference.min()), "maximum_J": float(difference.max()),
            "adverse": int((difference < 0).sum()), "favorable": int((difference > 0).sum()),
            "zero": int((difference == 0).sum()), "reading": reading(mean),
            "sign": "positive" if mean > 0 else "negative" if mean < 0 else "zero",
        }
    return {
        "complete": all(p["complete"] for p in panels.values()), "arms": panels,
        "arm_mean_J": {a: p["mean_J"] for a, p in panels.items()},
        "arm_mean_S": {a: p["mean_S"] for a, p in panels.items()},
        "primaries": ["F-C", "F-dwell"], "secondary": "dwell-C", "contrasts": contrasts,
        "MEI_J": .01, "metric": "J=S/256; S is the complete native team reward sum",
        "uncertainty": "Sample SD and SE conditional on one fitted endpoint; no training-population or joint-C confidence.",
    }


def publish(output, process_start):
    output = Path(output)
    path = output / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (output / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    summary["configuration"].update(user_distribution="cluster", training_rule="C")
    summary["primary"] = final_panel(rows)
    if not summary["primary"]["complete"]:
        summary["status"] = "incomplete"
    summary["process_wall_s_to_cluster_publication"] = time.monotonic() - process_start
    summary["timing_boundary"] = "Both summary publications/readbacks and actual exit are enclosed by the whole native command timer."
    payload = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8")
    if path.read_text(encoding="utf-8") != payload:
        raise RuntimeError("cluster summary readback differs")
    return summary["status"] == "complete"
