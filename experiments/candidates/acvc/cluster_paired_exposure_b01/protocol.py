"""Fixed identities and paired endpoint/change publication for ACVC B01."""
import math

import numpy as np

from experiments.candidates.acvc.cluster_deployment_b01.protocol import make_cluster
from experiments.candidates.acvc.native_link_loss_b01.report import reading


OBJECT = "ACVC_CLUSTER_PAIRED_EXPOSURE_B01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_PAIRED_EXPOSURE_B01_SCIENCE_CARD_20260914.md"
MASTER = 22591
EVALUATION_NAMESPACE = 32591
CHECKPOINTS = (512, 1024)
ARMS = ("C", "F", "dwell")
EVALUATION_ORDER = tuple((checkpoint, arm) for checkpoint in CHECKPOINTS for arm in ARMS)
TRAIN_EPISODES = 1024
EVAL_EPISODES = 64
HORIZON = 256
PLANNING_SECONDS = dict(
    native=500, cumulative_runtime_support=2100, complete_charge=2600,
    inner_watchdog=1800, outer_watchdog=1860, outer_kill_after=10,
)


def _sign(value):
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def change_reading(value):
    if value is None or not math.isfinite(value):
        return "INCOMPLETE"
    if value > .01:
        return "INCREASE"
    if value < -.01:
        return "DECREASE"
    return "WITHIN"


def _arm(rows, checkpoint, arm, expected):
    selected = sorted((row for row in rows
                       if row.get("phase") == "eval"
                       and row.get("checkpoint_episode") == checkpoint
                       and row.get("arm") == arm), key=lambda row: row.get("episode", -1))
    complete = len(selected) == expected and [row.get("episode") for row in selected] == list(range(expected))
    complete = complete and all(
        row.get("base") == MASTER
        and row.get("evaluation_namespace") == EVALUATION_NAMESPACE
        and row.get("reset_seed") == 100000 * EVALUATION_NAMESPACE + 2000 + row["episode"]
        and row.get("steps") == HORIZON
        and isinstance(row.get("S"), (int, float)) and math.isfinite(row["S"])
        and isinstance(row.get("J"), (int, float)) and math.isfinite(row["J"])
        and row["J"] == row["S"] / HORIZON
        for row in selected
    )
    values_j = np.asarray([row["J"] for row in selected], dtype=np.float64) if complete else None
    values_s = np.asarray([row["S"] for row in selected], dtype=np.float64) if complete else None
    return {
        "complete": complete,
        "available_rows": len(selected),
        "episode_ids": list(range(expected)) if complete else [row.get("episode") for row in selected],
        "values_J": values_j.tolist() if complete else None,
        "values_S": values_s.tolist() if complete else None,
        "mean_J": float(values_j.mean()) if complete else None,
        "mean_S": float(values_s.mean()) if complete else None,
        "minimum_J": float(values_j.min()) if complete else None,
        "maximum_J": float(values_j.max()) if complete else None,
    }


def _difference(first, second, name):
    if not first["complete"] or not second["complete"]:
        return {"complete": False, "reading": "INCOMPLETE", "mean_J": None,
                "dependent_arms": name.split("-")}
    values = np.asarray(first["values_J"], dtype=np.float64) - np.asarray(second["values_J"], dtype=np.float64)
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    return {
        "complete": True,
        "episode_ids": list(range(len(values))),
        "paired_differences_J": values.tolist(),
        "mean_J": mean,
        "mean_S": mean * HORIZON,
        "sample_SD_J": sd,
        "conditional_SE_J": sd / math.sqrt(len(values)),
        "n_joint_episodes": len(values),
        "minimum_J": float(values.min()),
        "maximum_J": float(values.max()),
        "negative": int((values < 0).sum()),
        "positive": int((values > 0).sum()),
        "zero": int((values == 0).sum()),
        "sign": _sign(mean),
        "reading": reading(mean) if name != "dwell-C" else "DESCRIPTIVE",
    }


def _change(early, late, contrast):
    if not early["complete"] or not late["complete"]:
        return {"complete": False, "reading": "INCOMPLETE", "mean_J": None,
                "dependent_endpoints": [f"512:{contrast}", f"1024:{contrast}"]}
    early_values = np.asarray(early["paired_differences_J"], dtype=np.float64)
    late_values = np.asarray(late["paired_differences_J"], dtype=np.float64)
    values = late_values - early_values
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    return {
        "complete": True,
        "episode_ids": list(range(len(values))),
        "paired_difference_of_differences_J": values.tolist(),
        "mean_J": mean,
        "mean_S": mean * HORIZON,
        "sample_SD_J": sd,
        "conditional_SE_J": sd / math.sqrt(len(values)),
        "n_joint_worlds": len(values),
        "minimum_J": float(values.min()),
        "maximum_J": float(values.max()),
        "negative": int((values < 0).sum()),
        "positive": int((values > 0).sum()),
        "zero": int((values == 0).sum()),
        "sign": _sign(mean),
        "reading": change_reading(mean),
        "MEI_J": .01,
    }


def final_panel(rows, expected=EVAL_EPISODES):
    endpoints = {}
    for checkpoint in CHECKPOINTS:
        arms = {arm: _arm(rows, checkpoint, arm, expected) for arm in ARMS}
        contrasts = {
            "F-C": _difference(arms["F"], arms["C"], "F-C"),
            "F-dwell": _difference(arms["F"], arms["dwell"], "F-dwell"),
            "dwell-C": _difference(arms["dwell"], arms["C"], "dwell-C"),
        }
        endpoints[str(checkpoint)] = {
            "complete": all(item["complete"] for item in arms.values()),
            "arms": arms,
            "contrasts": contrasts,
            "primaries": ["F-C", "F-dwell"],
            "secondary": "dwell-C",
            "MEI_J": .01,
        }
    changes = {
        "G_dwell": _change(endpoints["512"]["contrasts"]["F-dwell"],
                           endpoints["1024"]["contrasts"]["F-dwell"], "F-dwell"),
        "G_C": _change(endpoints["512"]["contrasts"]["F-C"],
                       endpoints["1024"]["contrasts"]["F-C"], "F-C"),
    }
    return {
        "complete": all(stage["complete"] for stage in endpoints.values()),
        "endpoints": endpoints,
        "changes": changes,
        "designated_change": "G_dwell",
        "supporting_change": "G_C",
        "metric": "J=S/256; S is the complete native team reward sum",
        "uncertainty": (
            "Endpoint and direct within-world difference-of-differences sample SD/sqrt(64), "
            "conditional on one correlated fresh programme; no training-population uncertainty or equivalence claim."
        ),
    }
