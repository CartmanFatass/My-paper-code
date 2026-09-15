"""Prospective selection/holdout contract; importing this performs no learning.

The selection grid shares one training master. Only a separately trained holdout
pair supplies the new comparison. Synthetic tests never invoke a native host.
"""

import argparse
import json
import math
from pathlib import Path
import statistics


OBJECT = "MGTAP-LR-SELECTION-B01"
ARMS = ("COND", "DENSE")
# Order is also the exact-tie rule: inherited setting, then lower, then higher.
LEARNING_RATES = {"base": 3e-4, "slow": 1e-4, "fast": 1e-3}
SELECTION_MASTER, HOLDOUT_MASTER = 8251, 8252
HORIZON, TRAIN_EPISODES, EVAL_EPISODES = 256, 256, 32
EPISODES_PER_ROLLOUT, EPOCHS, AGENTS = 2, 4, 5
MEI = 0.01


def randomization(master, phase, episode):
    """Arm/candidate-owned RNGs use matched addresses, not shared live streams."""
    if type(master) is not int or master not in (SELECTION_MASTER, HOLDOUT_MASTER):
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


def _panels(rows, stage, master, expected):
    """Reject missing, duplicate, nonfinite, wrong-role or misbound input rows."""
    panels = {key: {} for key in expected}
    for row in rows:
        key = (row.get("arm"), row.get("lr_key"))
        if key not in panels:
            raise ValueError("unexpected arm or learning-rate candidate")
        if (row.get("stage") != stage or row.get("phase") != "eval"
                or type(row.get("pair_master")) is not int
                or row["pair_master"] != master):
            raise ValueError("selection/holdout role or master mismatch")
        episode, score = row.get("episode"), row.get("J")
        if (type(episode) is not int or not 0 <= episode < EVAL_EPISODES
                or episode in panels[key]):
            raise ValueError("duplicate or invalid evaluation episode")
        if type(score) not in (int, float) or not math.isfinite(score):
            raise ValueError("nonfinite or invalid score")
        if (type(row.get("steps")) is not int or row["steps"] != HORIZON
                or row.get("learning_rate") != LEARNING_RATES[key[1]]):
            raise ValueError("endpoint or learning-rate binding mismatch")
        expected_rng = randomization(master, "eval", episode)
        if any(type(row.get(name)) is not int or row[name] != seed
               for name, seed in expected_rng.items()):
            raise ValueError("evaluation randomization mismatch")
        panels[key][episode] = score
    if any(set(panel) != set(range(EVAL_EPISODES)) for panel in panels.values()):
        raise ValueError("incomplete evaluation panel; no candidate replacement")
    return {key: [panel[e] for e in range(EVAL_EPISODES)]
            for key, panel in panels.items()}


def select_learning_rates(rows):
    """Select each arm by its OWN validation J, never by the arm difference."""
    expected = [(arm, lr_key) for arm in ARMS for lr_key in LEARNING_RATES]
    panels = _panels(rows, "selection", SELECTION_MASTER, expected)
    means = {arm: {key: statistics.mean(panels[arm, key]) for key in LEARNING_RATES}
             for arm in ARMS}
    selected = {arm: max(LEARNING_RATES, key=lambda key: means[arm][key]) for arm in ARMS}
    return {
        "object": OBJECT,
        "selection_master": SELECTION_MASTER,
        "selected_lr_key": selected,
        "selected_learning_rate": {arm: LEARNING_RATES[key] for arm, key in selected.items()},
        "validation_mean_J": means,
        "exact_tie_order": list(LEARNING_RATES),
        "holdout_used_for_selection": False,
    }


def holdout_primary(rows, selection):
    """Conditional on the fixed selection record and one fresh fitted pair."""
    if (selection.get("object") != OBJECT
            or selection.get("selection_master") != SELECTION_MASTER
            or selection.get("holdout_used_for_selection") is not False):
        raise ValueError("invalid selection provenance")
    selected = selection.get("selected_lr_key", {})
    rates = selection.get("selected_learning_rate", {})
    if (set(selected) != set(ARMS) or set(rates) != set(ARMS)
            or any(key not in LEARNING_RATES for key in selected.values())
            or any(rates[arm] != LEARNING_RATES[selected[arm]] for arm in ARMS)):
        raise ValueError("invalid selected rates")
    means = selection.get("validation_mean_J", {})
    if (set(means) != set(ARMS)
            or any(not isinstance(means[arm], dict) or set(means[arm]) != set(LEARNING_RATES)
                   for arm in ARMS)):
        raise ValueError("incomplete selection score record")
    if any(type(value) not in (int, float) or not math.isfinite(value)
           for arm in ARMS for value in means[arm].values()):
        raise ValueError("invalid selection score record")
    if (selection.get("exact_tie_order") != list(LEARNING_RATES)
            or any(selected[arm] != max(LEARNING_RATES, key=lambda key: means[arm][key])
                   for arm in ARMS)):
        raise ValueError("selected rates do not follow the frozen validation rule")
    expected = [(arm, selected[arm]) for arm in ARMS]
    panels = _panels(rows, "holdout", HOLDOUT_MASTER, expected)
    differences = [a - b for a, b in zip(panels[expected[0]], panels[expected[1]])]
    delta = statistics.mean(differences)
    return {
        "object": OBJECT,
        "holdout_master": HOLDOUT_MASTER,
        "selected_lr_key": selected.copy(),
        "J_by_arm": {arm: panels[arm, selected[arm]] for arm in ARMS},
        "mean_J_by_arm": {arm: statistics.mean(panels[arm, selected[arm]]) for arm in ARMS},
        "ordered_COND_minus_DENSE": differences,
        "delta_J": delta,
        "conditional_panel_se": statistics.stdev(differences) / math.sqrt(EVAL_EPISODES),
        "reading": "COND_ABOVE_MEI" if delta > MEI else "COND_ADVERSE" if delta < -MEI else "INSIDE_MEI",
        "independent_final_training_pairs": 1,
        "independent_selection_replications": 1,
        "claim_limit": "one fresh pair conditional on one finite-grid selection; no population ordering",
    }


def planned_exposure():
    """Compute the planned work from the actual protocol, without a simulation."""
    rollouts = TRAIN_EPISODES // EPISODES_PER_ROLLOUT
    per_fit = {
        "train_episodes": TRAIN_EPISODES,
        "evaluation_episodes": EVAL_EPISODES,
        "train_team_ticks": TRAIN_EPISODES * HORIZON,
        "evaluation_team_ticks": EVAL_EPISODES * HORIZON,
        "rollouts": rollouts,
        "adam_calls": rollouts * EPOCHS,
    }
    per_fit["total_team_ticks"] = per_fit["train_team_ticks"] + per_fit["evaluation_team_ticks"]
    per_fit["actor_row_uses_collection_evaluation_replay"] = AGENTS * (
        per_fit["total_team_ticks"] + EPOCHS * per_fit["train_team_ticks"])
    stages = {}
    for name, fits in (("selection", len(ARMS) * len(LEARNING_RATES)), ("holdout", len(ARMS))):
        stages[name] = {"fits": fits, **{key: fits * value for key, value in per_fit.items()}}
    return {
        "object": OBJECT,
        "status": "PLANNED_NOT_EXECUTED",
        "learning_rates": LEARNING_RATES,
        "selection_master": SELECTION_MASTER,
        "holdout_master": HOLDOUT_MASTER,
        "per_fit": per_fit,
        "stages": stages,
        "total": {key: sum(stage[key] for stage in stages.values()) for key in stages["selection"]},
        "independence": {
            "selection_training_masters": 1,
            "holdout_training_pairs": 1,
            "whole_selection_procedure_replications": 1,
            "notes": "six candidate fits are not six independent selected-program replications",
        },
        "nested_work": "three learning-rate candidates per arm; no trajectory, policy or checkpoint search",
        "actual_new_native_exposure_at_protocol_preparation": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the derived planned-exposure JSON")
    args = parser.parse_args()
    body = json.dumps(planned_exposure(), indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    print(body, end="")


if __name__ == "__main__":
    main()
