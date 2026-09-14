"""Fixed selected configuration, new master, and one conditional pair estimand."""

from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import protocol as prior
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.conditional_pooling import primary as panel_primary


OBJECT, MASTER = "MGTAP-FIXED-LR-B01", 8253
ARMS = prior.ARMS
LEARNING_RATES = {"slow": 1e-4}
HORIZON, TRAIN_EPISODES, EVAL_EPISODES = 256, 256, 32
EPISODES_PER_ROLLOUT = 2
MEI = .01


def randomization(master, phase, episode):
    if type(master) is not int or master != MASTER:
        raise ValueError("uncarded master")
    if phase not in ("train", "eval"):
        raise ValueError("unknown phase")
    size = TRAIN_EPISODES if phase == "train" else EVAL_EPISODES
    if type(episode) is not int or not 0 <= episode < size:
        raise ValueError("uncarded episode")
    base = 100000 * master
    return {
        "reset_seed": base + (1000 if phase == "train" else 2000) + episode,
        "velocity_seed": base + (21 if phase == "train" else 3000 + episode),
        "duration_seed": base + (4000 if phase == "train" else 5000) + episode,
    }


def primary(rows):
    final_rows = [row for row in rows if row.get("phase") == "eval"]
    for row in final_rows:
        if (row.get("object") != OBJECT or row.get("stage") != "fixed"
                or row.get("pair_master") != MASTER or row.get("lr_key") != "slow"
                or row.get("learning_rate") != LEARNING_RATES["slow"]):
            raise ValueError("fixed configuration/master binding mismatch")
        expected = randomization(MASTER, "eval", row.get("episode"))
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError("final randomization mismatch")
    panel = panel_primary(final_rows)
    if not panel["complete"]:
        raise ValueError("incomplete final pair; no replacement or polarity")
    return {
        "object": OBJECT, "master": MASTER, "learning_rate": 1e-4,
        "J_by_arm": panel["J"],
        "ordered_COND_minus_DENSE": panel["COND_minus_DENSE"]["differences"],
        "delta_J": panel["COND_minus_DENSE"]["mean"],
        "conditional_panel_se": panel["COND_minus_DENSE"]["conditional_se"],
        "reading": panel["reading"], "independent_new_training_pairs": 1,
        "new_selection_procedure_replications": 0,
        "claim_limit": "fixed-configuration recurrence conditional on adaptive selection history; no population ordering",
    }


def planned_exposure():
    per_fit = prior.planned_exposure()["per_fit"]
    return {
        "object": OBJECT, "master": MASTER, "learning_rate": 1e-4,
        "per_fit": per_fit,
        "total": {"fits": 2, **{key: 2 * value for key, value in per_fit.items()}},
        "new_selection_fits": 0, "independent_new_training_pairs": 1,
        "status": "PLANNED_NOT_EXECUTED",
    }
