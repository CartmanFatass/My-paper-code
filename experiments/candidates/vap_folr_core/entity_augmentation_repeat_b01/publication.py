"""Own-block A-G endpoints and the ordered two-block exploratory primary."""

from ..entity_persistence_b01.publication import arm_result


OBJECT = "FOLR_ENTITY_AUGMENTATION_REPEAT_B01_781901_782001"
BLOCKS = {1: (781901, 1781901), 2: (782001, 1782001)}
COMPLETE_EXPOSURE = (5000, 100000, 4969, 128, 2560)


def _endpoint(summary, arm, block):
    if block not in BLOCKS or (
        summary.get("object"), summary.get("arm"), summary.get("status"), summary.get("block")
    ) != (OBJECT, arm, "complete", block):
        raise ValueError(f"foreign block or incomplete {arm} endpoint")
    if (summary.get("training_seed"), summary.get("evaluation_seed")) != BLOCKS[block]:
        raise ValueError(f"foreign {arm} seed binding")
    exposure = tuple(summary.get(key) for key in (
        "training_episodes", "training_ticks", "optimizer_steps",
        "evaluation_episodes", "evaluation_ticks"
    ))
    if exposure != COMPLETE_EXPOSURE:
        raise ValueError(f"incomplete {arm} exposure")
    return arm_result(summary.get("evaluation_returns", []))


def pair_result(generic, persistent):
    block = persistent.get("block")
    a = _endpoint(persistent, "AUGMENTED_PERSISTENT", block)
    g = _endpoint(generic, "GENERIC_RETAIN", block)
    if not persistent.get("launch_sha") or generic.get("launch_sha") != persistent["launch_sha"]:
        raise ValueError("different or missing selected source binding")
    difference = a["mean"] - g["mean"]
    return {
        "block": block, "training_seed": BLOCKS[block][0],
        "evaluation_seed": BLOCKS[block][1], "launch_sha": persistent["launch_sha"],
        "generic": g, "persistent": a, "persistent_minus_generic": difference,
        "rule": "A_ABOVE_MEI" if difference > 1 else (
            "G_ABOVE_MEI" if difference < -1 else "WITHIN_MEI"
        ),
        "mei": 1.0, "training_instances_per_arm": 1,
        "population_interval": None,
        "uncertainty": "Conditional policy panels; no episode-paired worlds or population precision.",
    }


def attach_primary(persistent, generic):
    try:
        persistent["pair_primary"] = pair_result(generic, persistent)
    except (AttributeError, TypeError, ValueError) as exc:
        persistent["pair_primary"] = None
        persistent["pair_primary_unavailable"] = (
            f"Selected own-block Generic endpoint is unusable ({exc}); no A-minus-G polarity."
        )
    return persistent


def study_result(generic1, persistent1, generic2, persistent2):
    pairs = [pair_result(generic1, persistent1), pair_result(generic2, persistent2)]
    if [p["block"] for p in pairs] != [1, 2]:
        raise ValueError("study requires the two original blocks in fixed order")
    if pairs[0]["launch_sha"] != pairs[1]["launch_sha"]:
        raise ValueError("study endpoints have different selected sources")
    differences = [p["persistent_minus_generic"] for p in pairs]
    rules = [p["rule"] for p in pairs]
    rule = {
        ("A_ABOVE_MEI", "A_ABOVE_MEI"): "BOTH_A_ABOVE_MEI",
        ("G_ABOVE_MEI", "G_ABOVE_MEI"): "BOTH_G_ABOVE_MEI",
        ("WITHIN_MEI", "WITHIN_MEI"): "BOTH_WITHIN_MEI",
    }.get(tuple(rules), "MIXED_BLOCK_PATTERN")
    return {
        "object": OBJECT, "blocks": pairs, "ordered_differences": differences,
        "descriptive_mean_difference": sum(differences) / 2,
        "rule": rule, "mei_per_block": 1.0, "training_instances_per_arm": 2,
        "independent_contrast_blocks": 2, "population_interval": None,
        "claim": "Two fresh whole-program A-G realizations; no stable rank or isolated persistence effect.",
        "uncertainty": (
            "Block independence is a working design assumption; within-block common labels "
            "do not prove paired evaluation worlds. The mean is descriptive, not the reading rule."
        ),
    }
