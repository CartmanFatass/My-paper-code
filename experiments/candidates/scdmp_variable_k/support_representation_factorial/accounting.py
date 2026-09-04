from __future__ import annotations

from collections.abc import Mapping, Sequence

from .config import (
    CELLS,
    DIRECT_EVALUATION_EXACT,
    DIRECT_PANEL_BASE_EXAMPLES,
    DIRECT_PANEL_EXPECTED_EXAMPLES,
    DIRECT_PANEL_LATTICE_STEP,
    DIRECT_PANEL_MAX_EXAMPLES,
    DIRECT_PANEL_MIN_EXAMPLES,
    DIRECT_PANEL_N10_COEFFICIENT,
    FINAL_PREFIX_ROWS,
    N10_SUM_EXPECTED,
    N10_SUM_MAX,
    N10_SUM_MIN,
    SEED_INDICES,
    SUPERSEDED_R02_EXAMPLE_ASSERTION,
    TRAIN_CELL_BASE_EXAMPLES,
    TRAIN_CELL_N10_COEFFICIENT,
    TRAIN_PANEL_BASE_EXAMPLES,
)

SUPPORT_LEVELS = ("S0", "S1")


def train_cell_examples(n10: int) -> int:
    if isinstance(n10, bool) or not isinstance(n10, int) \
            or not 0 <= n10 <= FINAL_PREFIX_ROWS:
        raise ValueError("final-prefix n10 must be an integer in 0,...,2048")
    return TRAIN_CELL_BASE_EXAMPLES + TRAIN_CELL_N10_COEFFICIENT * n10


def final_prefix_n10(rows: Sequence[object], plan: object) -> int:
    if len(rows) != 4_096:
        raise ValueError("registered support must contain exactly 4,096 rows")
    permutations = getattr(plan, "permutations", None)
    if not isinstance(permutations, list) or len(permutations) != 38:
        raise ValueError("registered minibatch plan must contain exactly 38 epochs")
    prefix = permutations[37][:FINAL_PREFIX_ROWS]
    if len(prefix) != FINAL_PREFIX_ROWS \
            or len({int(index) for index in prefix}) != FINAL_PREFIX_ROWS:
        raise ValueError("epoch-37 prefix must contain 2,048 distinct registered rows")
    n10 = sum(int(getattr(rows[int(index)], "k")) == 10 for index in prefix)
    if not 0 <= n10 <= FINAL_PREFIX_ROWS:
        raise RuntimeError("derived final-prefix n10 is outside its exact support")
    return n10


def complete_count_accounting(
    n10_by_seed_support: Mapping[str, int],
    executed_training_by_cell: Mapping[str, int],
) -> dict[str, object]:
    expected_support_keys = {
        f"{seed_index}:{support}"
        for seed_index in SEED_INDICES for support in SUPPORT_LEVELS
    }
    expected_cell_keys = {
        f"{seed_index}:{cell}"
        for seed_index in SEED_INDICES for cell in CELLS
    }
    if set(n10_by_seed_support) != expected_support_keys:
        raise RuntimeError("complete accounting requires exact ten-seed/two-support n10 keys")
    if set(executed_training_by_cell) != expected_cell_keys:
        raise RuntimeError("complete accounting requires exact forty-cell training counters")

    normalized_n10: dict[str, int] = {}
    validated_executed_training_by_cell: dict[str, int] = {}
    for key in sorted(expected_support_keys):
        raw_n10 = n10_by_seed_support[key]
        if isinstance(raw_n10, bool) or not isinstance(raw_n10, int):
            raise RuntimeError(f"{key} n10 is not an exact integer")
        normalized_n10[key] = raw_n10
        seed_text, support = key.split(":", 1)
        expected = train_cell_examples(raw_n10)
        for representation in ("R0", "R1"):
            cell_key = f"{seed_text}:{support}{representation}"
            executed = executed_training_by_cell[cell_key]
            if isinstance(executed, bool) or not isinstance(executed, int) \
                    or executed != expected:
                raise RuntimeError(
                    f"{cell_key} executed direct-training count does not equal "
                    f"4_945_920 + 45*n10 ({expected})"
                )
            validated_executed_training_by_cell[cell_key] = executed

    sum_n10 = sum(normalized_n10.values())
    training_actual = TRAIN_PANEL_BASE_EXAMPLES \
        + DIRECT_PANEL_N10_COEFFICIENT * sum_n10
    direct_actual = DIRECT_PANEL_BASE_EXAMPLES \
        + DIRECT_PANEL_N10_COEFFICIENT * sum_n10
    if not N10_SUM_MIN <= sum_n10 <= N10_SUM_MAX:
        raise RuntimeError("complete n10 sum is outside its exact attainable bounds")
    if not DIRECT_PANEL_MIN_EXAMPLES <= direct_actual <= DIRECT_PANEL_MAX_EXAMPLES \
            or (direct_actual - DIRECT_PANEL_BASE_EXAMPLES) % DIRECT_PANEL_LATTICE_STEP:
        raise RuntimeError("realized direct count violates its exact lattice or range")
    return {
        "accounting_unit": (
            "one registered training row-segment example or one registered direct "
            "evaluation query evaluated once by one factorial cell"
        ),
        "framework_model_function_invocation_count": False,
        "n10_definition": (
            "count of k=10 rows in the first 2,048 rows of each seed/support "
            "epoch-37 Fisher-Yates permutation"
        ),
        "n10_by_seed_support": normalized_n10,
        "sum_n10": sum_n10,
        "train_cell_formula": "4_945_920 + 45*n10_s,a",
        "validated_executed_training_by_cell": validated_executed_training_by_cell,
        "train_panel_formula": "197_836_800 + 90*sum_n10",
        "training_direct_examples_actual": training_actual,
        "direct_evaluation": {
            "untouched_fit_support": 40_960,
            "target_diagnostic": 4_976_640,
            "exact_total": DIRECT_EVALUATION_EXACT,
        },
        "direct_panel_formula": "202_854_400 + 90*sum_n10",
        "direct_panel_actual": direct_actual,
        "prospective_expected_direct_examples": DIRECT_PANEL_EXPECTED_EXAMPLES,
        "prospective_expected_sum_n10": N10_SUM_EXPECTED,
        "lattice": {
            "base": DIRECT_PANEL_BASE_EXAMPLES,
            "step": DIRECT_PANEL_LATTICE_STEP,
            "sum_n10_min": N10_SUM_MIN,
            "sum_n10_max": N10_SUM_MAX,
        },
        "range": [DIRECT_PANEL_MIN_EXAMPLES, DIRECT_PANEL_MAX_EXAMPLES],
        "superseded_revision_02_assertion": SUPERSEDED_R02_EXAMPLE_ASSERTION,
        "superseded_assertion_is_active_cost": False,
        "no_role": {
            "is_not_stop": True,
            "is_not_competence": True,
            "is_not_inference": True,
            "is_not_branch": True,
            "is_not_claim": True,
            "is_not_covariate": True,
            "is_not_seed_exclusion": True,
            "is_not_repair": True,
            "is_not_partial_scientific_output": True,
        },
        "technical_conformance_only": True,
    }
