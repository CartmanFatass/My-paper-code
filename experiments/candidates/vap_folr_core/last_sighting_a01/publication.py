"""Fixed six-fit binding and descriptive LAST_SIGHTING reading."""

import statistics

from ..entity_history_b01.publication import arm_result


OBJECT = "FOLR_LAST_SIGHTING_A01"
ARMS = ("GENERIC_RETAIN", "LAST_SIGHTING")
TRAINING_SEEDS = (784101, 784201, 784301)
EVALUATION_SEED = 1784101
TRAIN_EPISODES = 5000
HORIZON = 20
OPTIMIZER_STEPS = 4969
PANEL_EPISODES = 128
COMPLETE_EXPOSURE = (
    TRAIN_EPISODES,
    TRAIN_EPISODES * HORIZON,
    OPTIMIZER_STEPS,
    PANEL_EPISODES,
    PANEL_EPISODES * HORIZON,
    0,
)


def require_endpoint(summary, arm, seed):
    if (summary.get("object"), summary.get("arm"), summary.get("status")) != (
        OBJECT,
        arm,
        "complete",
    ):
        raise ValueError(f"foreign or incomplete {arm} endpoint")
    if (summary.get("training_seed"), summary.get("evaluation_seed")) != (
        seed,
        EVALUATION_SEED,
    ):
        raise ValueError(f"foreign {arm} seed binding")
    exposure = tuple(
        summary.get(key)
        for key in (
            "training_episodes",
            "training_transitions",
            "optimizer_steps",
            "evaluation_episodes",
            "evaluation_transitions",
            "evaluation_optimizer_steps",
        )
    )
    if exposure != COMPLETE_EXPOSURE:
        raise ValueError(f"incomplete {arm} exposure")
    return arm_result(summary.get("evaluation_returns", []))


def study_result(summaries):
    """Read exactly the three prospectively bound within-label contrasts."""
    endpoints = {}
    for summary in summaries:
        key = (summary.get("arm"), summary.get("training_seed"))
        if key in endpoints:
            raise ValueError(f"duplicate endpoint {key}")
        endpoints[key] = summary
    expected = {(arm, seed) for arm in ARMS for seed in TRAINING_SEEDS}
    if set(endpoints) != expected:
        raise ValueError("the fixed six endpoints are required")

    arms = {
        arm: {
            str(seed): require_endpoint(endpoints[(arm, seed)], arm, seed)
            for seed in TRAINING_SEEDS
        }
        for arm in ARMS
    }
    contrasts = [
        {
            "training_seed": seed,
            "last_sighting_minus_generic": (
                arms["LAST_SIGHTING"][str(seed)]["mean"]
                - arms["GENERIC_RETAIN"][str(seed)]["mean"]
            ),
        }
        for seed in TRAINING_SEEDS
    ]
    values = [row["last_sighting_minus_generic"] for row in contrasts]
    return {
        "arms": arms,
        "within_label_contrasts": contrasts,
        "contrast_mean": statistics.mean(values),
        "contrast_range": [min(values), max(values)],
        "training_instances_per_arm": 3,
        "evaluation_seed": EVALUATION_SEED,
        "uncertainty": (
            "Independent fitted policies are the replication units. Shared seed labels "
            "do not establish paired counterfactual training worlds; three instances "
            "do not support a population-precision claim."
        ),
        "claim": "Exploratory whole-package native last-sighting cache comparison.",
    }

