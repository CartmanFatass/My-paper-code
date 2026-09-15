"""The selected Z-minus-G primary for two fresh complete endpoints."""

from ..entity_persistence_b01.publication import arm_result


OBJECT = "FOLR_ENTITY_CURRENT_INCREMENT_B01_781801"
TRAINING_SEED = 781801
EVALUATION_SEED = 1781801
COMPLETE_EXPOSURE = (5000, 100000, 4969, 128, 2560)


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


def pair_result(generic, current_only):
    g = _endpoint(generic, "GENERIC_RETAIN")
    z = _endpoint(current_only, "AUGMENTED_CURRENT_ONLY")
    if not current_only.get("launch_sha") or (
        generic.get("launch_sha") != current_only["launch_sha"]
    ):
        raise ValueError("different or missing selected source binding")
    difference = z["mean"] - g["mean"]
    return {
        "generic": g,
        "current_only": z,
        "current_only_minus_generic": difference,
        "rule": "CURRENT_ONLY_ABOVE_MEI" if difference > 1 else (
            "GENERIC_ABOVE_MEI" if difference < -1 else "WITHIN_MEI"
        ),
        "mei": 1.0,
        "training_instances_per_arm": 1,
        "paired_difference_se": None,
        "uncertainty": (
            "Episode dispersion is conditional on each fitted policy; common "
            "seed labels do not establish paired worlds or training-population uncertainty."
        ),
        "claim": "Exploratory whole-program current-only augmentation increment over Generic.",
    }


def attach_primary(current_only, generic):
    try:
        current_only["pair_primary"] = pair_result(generic, current_only)
    except (AttributeError, TypeError, ValueError) as exc:
        current_only["pair_primary"] = None
        current_only["pair_primary_unavailable"] = (
            f"Selected Generic endpoint is unusable ({exc}); no Z-minus-G polarity."
        )
    return current_only
