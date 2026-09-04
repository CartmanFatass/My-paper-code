from __future__ import annotations

from .config import (
    ALGORITHM_SEEDS, ARMS, BANK_ORDER, BATCH_NAMESPACE_BASE, BATCH_ROWS_PER_STRATUM,
    CORPUS_NAMESPACE_BASE, INITIALIZATION_NAMESPACE_BASE, OPTIMIZER_UPDATES, REVISION,
    SCORED_NAMESPACE_BASE, SCORED_REGIMES, STRATUM_ORDER, TRAIN_DURATIONS,
)


def coordinate_manifest(seed: int) -> dict[str, object]:
    if seed not in ALGORITHM_SEEDS:
        raise ValueError(f"B3 seed outside frozen block: {seed}")
    return {
        "revision": REVISION,
        "algorithm_seed": seed,
        "arm_order": list(ARMS),
        "training_schedule": {"major_axis": "update", "updates": 1_000,
                              "arm_order": list(ARMS),
                              "frontier_boundary": "after_complete_three_arm_update"},
        "rng": {
            "generator": "numpy.random.PCG64",
            "draw_api": ["random_raw", "U0", "Umid", "Box-Muller", "QR-sign"],
            "initialization": INITIALIZATION_NAMESPACE_BASE + seed,
            "batch_order": BATCH_NAMESPACE_BASE + seed,
            "corpus_resets": CORPUS_NAMESPACE_BASE + seed,
            "scored_regimes": {
                regime: SCORED_NAMESPACE_BASE + 1_000 * seed + index
                for index, regime in enumerate(SCORED_REGIMES)
            },
        },
        "coordinate_schemas": {
            "corpus": ["revision", "seed", "k", "class", "word", "episode",
                       "primitive_step", "draw_kind", "draw_index"],
            "batch": ["revision", "seed", "update", "bank", "stratum", "row_slot"],
            "audit": ["revision", "seed", "k", "REAL_or_SHAM", "word", "slot",
                      "severity", "boundary"],
            "score": ["revision", "seed", "regime", "episode", "primitive_step",
                      "draw_kind", "draw_index"],
        },
        "materialization": {
            "order": "lexicographic_within_each_registered_coordinate_family",
            "corpus": {
                "durations": list(TRAIN_DURATIONS), "episodes_per_duration": 64,
                "reset_draws_per_episode": {"q": 1, "e": 4, "v": 4},
                "reset_draw_count": 3 * 64 * 9,
            },
            "batch": {
                "updates": OPTIMIZER_UPDATES, "banks": list(BANK_ORDER),
                "strata": [list(x) for x in STRATUM_ORDER],
                "rows_per_stratum": BATCH_ROWS_PER_STRATUM,
                "row_coordinate_count": OPTIMIZER_UPDATES * len(BANK_ORDER)
                                        * len(STRATUM_ORDER) * BATCH_ROWS_PER_STRATUM,
                "shared_across_arms": True,
            },
            "audit": {
                "durations": [6, 12], "states_per_duration": 32,
                "warmup_boundaries": 12,
                "action_index": "(g + 43*(seed-200) + 11*boundary) mod 81",
                "deterministic": True,
            },
            "score": {
                "regimes": list(SCORED_REGIMES), "episodes_per_regime": 32,
                "reset_draws_per_episode": {"q": 1, "e": 4, "v": 4},
                "reset_draw_count": len(SCORED_REGIMES) * 32 * 9,
                "shared_across_arms": True,
            },
        },
        "predecessor_coordinates_admitted": False,
    }


def complete_coordinate_manifest() -> dict[str, object]:
    return {"revision": REVISION, "seed_order": list(ALGORITHM_SEEDS),
            "per_seed": [coordinate_manifest(seed) for seed in ALGORITHM_SEEDS]}
