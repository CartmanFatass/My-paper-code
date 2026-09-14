"""One fresh pair, two fixed observations, and a final512 primary."""

import statistics

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.conditional_pooling import primary as panel_primary

OBJECT, MASTER = "MGTAP-LATE-EXPOSURE-B01", 8254
ARMS = ("COND", "DENSE")
HORIZON, TRAIN_EPISODES, EVAL_EPISODES = 256, 512, 32
ENDPOINTS = (256, 512)
LEARNING_RATE, MEI = 1e-4, .01
EPISODES_PER_ROLLOUT, EPOCHS, AGENTS = 2, 4, 5


def randomization(phase, episode):
    size = TRAIN_EPISODES if phase == "train" else EVAL_EPISODES
    if phase not in ("train", "eval") or type(episode) is not int or not 0 <= episode < size:
        raise ValueError("uncarded phase/episode")
    base = 100000 * MASTER
    return {
        "reset_seed": base + (1000 if phase == "train" else 2000) + episode,
        "velocity_seed": base + (21 if phase == "train" else 3000 + episode),
        "duration_seed": base + (4000 if phase == "train" else 5000) + episode,
    }


def planned_exposure():
    train = TRAIN_EPISODES * HORIZON
    evaluation = len(ENDPOINTS) * EVAL_EPISODES * HORIZON
    rollouts = TRAIN_EPISODES // EPISODES_PER_ROLLOUT
    per_fit = {
        "train_episodes": TRAIN_EPISODES,
        "evaluation_episodes": len(ENDPOINTS) * EVAL_EPISODES,
        "train_team_ticks": train, "evaluation_team_ticks": evaluation,
        "total_team_ticks": train + evaluation,
        "rollouts": rollouts, "adam_calls": rollouts * EPOCHS,
        "actor_row_uses_collection_evaluation_replay": AGENTS * (train + evaluation + EPOCHS * train),
    }
    return {"per_fit": per_fit, "total": {"fits": len(ARMS), **{
        key: len(ARMS) * value for key, value in per_fit.items()}},
        "independent_training_pairs": 1, "selection_fits": 0,
        "nested_search": "none", "status": "PLANNED_NOT_EXECUTED"}


def primary(rows):
    panels = {}
    for row in rows:
        if row.get("phase") == "eval":
            if (row.get("object") != OBJECT or row.get("pair_master") != MASTER
                    or row.get("learning_rate") != LEARNING_RATE
                    or row.get("train_endpoint") not in ENDPOINTS):
                raise ValueError("evaluation contract mismatch")
            if any(row.get(k) != v for k, v in randomization("eval", row.get("episode")).items()):
                raise ValueError("evaluation randomization mismatch")
    for endpoint in ENDPOINTS:
        panel = panel_primary([row for row in rows if row.get("phase") == "eval"
                               and row.get("train_endpoint") == endpoint])
        if not panel["complete"]:
            raise ValueError(f"incomplete endpoint{endpoint}; no replacement or pair polarity")
        panels[str(endpoint)] = panel
    early, late = [panels[str(ep)]["COND_minus_DENSE"]["mean"] for ep in ENDPOINTS]
    return {
        "primary_endpoint": TRAIN_EPISODES, "delta_J": late,
        "reading": panels[str(TRAIN_EPISODES)]["reading"],
        "conditional_panel_se": panels[str(TRAIN_EPISODES)]["COND_minus_DENSE"]["conditional_se"],
        "panels": panels, "secondary_late_minus_early_delta_J": late - early,
        "secondary_arm_changes": {arm: statistics.mean(panels["512"]["J"][arm])
                                   - statistics.mean(panels["256"]["J"][arm]) for arm in ARMS},
        "independent_training_pairs": 1,
        "claim_limit": "one fresh fixed-rate learning path; checkpoints/worlds are not training replicates; no isolated dose or pooling effect",
    }
