"""The selected A-minus-Z primary; conditional episodes are not training runs."""

from ..entity_history_b01.publication import arm_result as _arm_result


OBJECT = "FOLR_ENTITY_PERSISTENCE_B01_781701"
TRAINING_SEED = 781701
EVALUATION_SEED = 1781701
COMPLETE_EXPOSURE = (5000, 100000, 4969, 128, 2560)


def arm_result(values):
    result = _arm_result(values)
    result["negative_count"] = sum(value < 0 for value in values)
    return result


def _endpoint(summary, arm):
    if (summary.get("object"), summary.get("arm"), summary.get("status")) != (
        OBJECT, arm, "complete"
    ):
        raise ValueError(f"foreign or incomplete {arm} endpoint")
    if (summary.get("training_seed"), summary.get("evaluation_seed")) != (
        TRAINING_SEED, EVALUATION_SEED
    ):
        raise ValueError(f"foreign {arm} seed binding")
    exposure = tuple(summary.get(key) for key in (
        "training_episodes", "training_ticks", "optimizer_steps",
        "evaluation_episodes", "evaluation_ticks"
    ))
    if exposure != COMPLETE_EXPOSURE:
        raise ValueError(f"incomplete {arm} exposure")
    return arm_result(summary.get("evaluation_returns", []))


def pair_result(current_only, persistent):
    z = _endpoint(current_only, "AUGMENTED_CURRENT_ONLY")
    a = _endpoint(persistent, "AUGMENTED_PERSISTENT")
    if not persistent.get("launch_sha") or (
        current_only.get("launch_sha") != persistent["launch_sha"]
    ):
        raise ValueError("different or missing selected source binding")
    difference = a["mean"] - z["mean"]
    return {
        "current_only": z,
        "persistent": a,
        "persistent_minus_current_only": difference,
        "rule": "PERSISTENT_ABOVE_MEI" if difference > 1 else (
            "CURRENT_ONLY_ABOVE_MEI" if difference < -1 else "WITHIN_MEI"
        ),
        "mei": 1.0,
        "training_instances_per_arm": 1,
        "paired_difference_se": None,
        "uncertainty": (
            "Episode dispersion is conditional on each fitted policy; common "
            "seed labels do not establish paired worlds or training-population uncertainty."
        ),
        "claim": "Exploratory persistence design comparison within the augmented program.",
    }


def attach_primary(persistent, current_only):
    try:
        persistent["pair_primary"] = pair_result(current_only, persistent)
    except (AttributeError, TypeError, ValueError) as exc:
        persistent["pair_primary"] = None
        persistent["pair_primary_unavailable"] = (
            f"Selected current-only endpoint is unusable ({exc}); no A-minus-Z polarity."
        )
    return persistent
