"""Endpoint binding and primary for the fresh augmented-versus-Generic object."""

from ..entity_history_b01.publication import arm_result


OBJECT = "FOLR_ENTITY_HISTORY_AUGMENTATION_B01_781601"
TRAINING_SEED = 781601
EVALUATION_SEED = 1781601
COMPLETE_EXPOSURE = (5000, 100000, 4969, 128, 2560)


def _require_endpoint(summary, arm):
    if (
        summary.get("object"),
        summary.get("arm"),
        summary.get("status"),
    ) != (OBJECT, arm, "complete"):
        raise ValueError(f"foreign or incomplete {arm} endpoint")
    if (summary.get("training_seed"), summary.get("evaluation_seed")) != (
        TRAINING_SEED,
        EVALUATION_SEED,
    ):
        raise ValueError(f"foreign {arm} seed binding")
    exposure = tuple(
        summary.get(key)
        for key in (
            "training_episodes",
            "training_ticks",
            "optimizer_steps",
            "evaluation_episodes",
            "evaluation_ticks",
        )
    )
    if exposure != COMPLETE_EXPOSURE:
        raise ValueError(f"incomplete {arm} exposure")
    return arm_result(summary.get("evaluation_returns", []))


def pair_result(generic, augmented):
    """Read the one selected whole-package comparison with strict MEI ties."""
    g = _require_endpoint(generic, "GENERIC_RETAIN")
    a = _require_endpoint(augmented, "AUGMENTED_PERSISTENT")
    difference = a["mean"] - g["mean"]
    rule = (
        "AUGMENTED_ABOVE_MEI"
        if difference > 1
        else "GENERIC_ABOVE_MEI"
        if difference < -1
        else "WITHIN_MEI"
    )
    return {
        "generic": g,
        "augmented": a,
        "augmented_minus_generic": difference,
        "rule": rule,
        "mei": 1.0,
        "training_pairs": 1,
        "paired_difference_se": None,
        "uncertainty": (
            "Per-arm episode dispersion is conditional on each fitted policy; "
            "shared seed labels do not establish paired trajectories or "
            "training-population uncertainty."
        ),
        "claim": (
            "Exploratory whole-package native comparison on the selected "
            "public-lifecycle host."
        ),
    }


def attach_primary(augmented, generic):
    """Keep a valid augmented endpoint when its comparator cannot bind."""
    if generic is None:
        augmented["pair_primary"] = None
        augmented["pair_primary_unavailable"] = (
            "Selected Generic endpoint was not supplied; no A-minus-G polarity."
        )
        return augmented
    try:
        augmented["pair_primary"] = pair_result(generic, augmented)
    except (AttributeError, TypeError, ValueError) as exc:
        augmented["pair_primary"] = None
        augmented["pair_primary_unavailable"] = (
            f"Selected Generic endpoint is unusable ({exc}); no A-minus-G polarity."
        )
    return augmented
