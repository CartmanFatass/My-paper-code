"""Fixed recipe identities and direct conditional paired-world publication."""
import math

import numpy as np

from experiments.candidates.acvc.cluster_deployment_b01.protocol import make_cluster
from experiments.candidates.acvc.native_link_loss_b01.report import reading

OBJECT = "ACVC_CLUSTER_FIXED_LR_PAIR_B01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_LR_PAIR_B01_SCIENCE_CARD_20260914.md"
MASTER = 27931
EVALUATION_NAMESPACE = 37931
RECIPES = {"low": 1e-4, "reference": 3e-4}
CHECKPOINTS = (4096,)
ARMS = ("C", "F", "dwell")
EVALUATION_ORDER = tuple((4096, arm) for arm in ARMS)
TRAIN_EPISODES = 4096
EVAL_EPISODES = 64
HORIZON = 256
PLANNING_SECONDS = dict(
    native=1400, cumulative_runtime_support=3600, complete_charge=5000,
    inner_watchdog=3600, outer_watchdog=3660, outer_kill_after=10,
)


def _arm(rows, recipe, arm):
    selected = sorted((row for row in rows if row.get("phase") == "eval" and row.get("arm") == arm),
                      key=lambda row: row.get("episode", -1))
    complete = len(selected) == EVAL_EPISODES and [row.get("episode") for row in selected] == list(range(EVAL_EPISODES))
    complete = complete and all(
        row.get("base") == MASTER and row.get("recipe") == recipe
        and row.get("learning_rate") == RECIPES[recipe]
        and row.get("checkpoint_episode") == 4096
        and row.get("evaluation_namespace") == EVALUATION_NAMESPACE
        and row.get("reset_seed") == 100000 * EVALUATION_NAMESPACE + 2000 + row["episode"]
        and row.get("steps") == HORIZON
        and isinstance(row.get("S"), (int, float)) and math.isfinite(row["S"])
        and isinstance(row.get("J"), (int, float)) and math.isfinite(row["J"])
        and row["J"] == row["S"] / HORIZON for row in selected
    )
    values = np.asarray([row["J"] for row in selected], dtype=np.float64) if complete else None
    return dict(complete=complete, available_rows=len(selected),
                episode_ids=[row.get("episode") for row in selected],
                values_J=values.tolist() if complete else None,
                mean_J=float(values.mean()) if complete else None,
                mean_S=float(values.mean()) * HORIZON if complete else None,
                minimum_J=float(values.min()) if complete else None,
                maximum_J=float(values.max()) if complete else None)


def _difference(first, second, name, descriptive=False):
    if not first["complete"] or not second["complete"]:
        return dict(complete=False, reading="INCOMPLETE", mean_J=None, dependent_arms=name)
    values = np.asarray(first["values_J"], dtype=np.float64) - np.asarray(second["values_J"], dtype=np.float64)
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    return dict(complete=True, episode_ids=list(range(len(values))), paired_differences_J=values.tolist(),
                mean_J=mean, mean_S=mean * HORIZON, sample_SD_J=sd,
                conditional_SE_J=sd / math.sqrt(len(values)), n_joint_worlds=len(values),
                minimum_J=float(values.min()), maximum_J=float(values.max()),
                negative=int((values < 0).sum()), positive=int((values > 0).sum()), zero=int((values == 0).sum()),
                sign="positive" if mean > 0 else "negative" if mean < 0 else "zero",
                reading="DESCRIPTIVE" if descriptive else reading(mean))


def final_panel(rows, recipe):
    arms = {arm: _arm(rows, recipe, arm) for arm in ARMS}
    return dict(complete=all(value["complete"] for value in arms.values()), recipe=recipe,
                learning_rate=RECIPES[recipe], arms=arms,
                contrasts={"F-C": _difference(arms["F"], arms["C"], "F-C"),
                           "F-dwell": _difference(arms["F"], arms["dwell"], "F-dwell"),
                           "dwell-C": _difference(arms["dwell"], arms["C"], "dwell-C", descriptive=True)},
                primaries=["F-C", "F-dwell"], MEI_J=.01)


def paired_panel(recipe_rows):
    panels = {recipe: final_panel(recipe_rows.get(recipe, []), recipe) for recipe in RECIPES}
    low, reference = panels["low"]["arms"], panels["reference"]["arms"]
    comparisons = {f"low_{arm}-reference_{arm}": _difference(low[arm], reference[arm],
                   f"low_{arm}-reference_{arm}", descriptive=arm != "C") for arm in ARMS}
    return dict(complete=all(value["complete"] for value in panels.values()), recipes=panels,
                cross_recipe=comparisons, designated_contrast="low_C-reference_C",
                within_recipe_contrasts=["F-C", "F-dwell"], MEI_J=.01,
                metric="J=S/256; S is the complete native team reward sum",
                uncertainty="Direct paired-world sample SD/sqrt(64), conditional on one matched fitted recipe pair; no training-population uncertainty or equivalence.")
