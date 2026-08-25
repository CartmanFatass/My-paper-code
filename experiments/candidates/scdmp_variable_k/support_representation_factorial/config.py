from __future__ import annotations

from dataclasses import dataclass

CANDIDATE = "SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT"
RESULT_OBJECT = "SCDMP-TBOV-SRF-R02-FULL-FACTORIAL"
REVISION = "SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260820-03"
BASE_CARD_SHA256 = "04f5bd7de229ea7cd996704e30589501b9b6dce5a7017bdc3ff5d02c271e859b"
COUNT_CORRECTION_SHA256 = "5d73825c539cce7dd005cac506ac2b0af8e122c8228a4c0258b9c4db1ae0005a"
PRO_CLOSED_INTAKE_SHA256 = "79ce96b6e60851734b13bc732c198081a03425076376458fe49af0490122063b"
HMAC_SEED_NAMESPACE = b"SCDMP-TBOV-SRF-CHECKPOINT-r02/seed/"

EVENTS = ("C", "S+", "S-", "G+", "G-")
EVENT_TO_INDEX = {event: index for index, event in enumerate(EVENTS)}
ACTIONS = tuple(
    (fl, fr, rl, rr)
    for fl in (-1, 0, 1)
    for fr in (-1, 0, 1)
    for rl in (-1, 0, 1)
    for rr in (-1, 0, 1)
)
STATE_COORDINATES = ("y", "v", "psi", "omega", "b", "z_FL", "z_FR", "z_RL", "z_RR")
STATE_BOUNDS = (
    (-0.25, 0.25), (-0.15, 0.15), (-0.20, 0.20),
    (-0.12, 0.12), (-0.40, 0.40),
    (-0.20, 0.20), (-0.20, 0.20), (-0.20, 0.20), (-0.20, 0.20),
)
STATE_SCALE = (0.50, 0.30, 0.40, 0.24, 0.80, 0.40, 0.40, 0.40, 0.40)
K_FIT = (4, 10)
K_TARGET = (6, 8, 12)
SEED_INDICES = tuple(range(10))
SUPPORT_LEVELS = ("S0", "S1")
REPRESENTATION_LEVELS = ("R0", "R1")
CELLS = ("S0R0", "S1R0", "S0R1", "S1R1")
CELL_SUPPORT = {cell: cell[:2] for cell in CELLS}
CELL_REPRESENTATION = {cell: cell[2:] for cell in CELLS}

TRAIN_ROWS = 4_096
S1_WORD_CELL_ROWS = 256
S1_ACTION_BASE_REPEATS = 3
S1_ACTION_EXTRAS = 13
FIT_SUPPORT_ROWS = 1_024
TARGET_BASE_ROWS = 256
LOGICAL_STEPS = 600
LOGICAL_BATCH_ROWS = 256
BATCHES_PER_EPOCH = 16
PERMUTATION_EPOCHS = 38
PRACTICAL_MARGIN = 0.01
FULL_EPOCH_TRAINING_EXAMPLES_PER_CELL = 4_925_440
FINAL_PREFIX_ROWS = 2_048
TRAIN_CELL_BASE_EXAMPLES = 4_945_920
TRAIN_CELL_N10_COEFFICIENT = 45
TRAIN_PANEL_BASE_EXAMPLES = 197_836_800
DIRECT_EVALUATION_EXACT = 5_017_600
DIRECT_PANEL_BASE_EXAMPLES = 202_854_400
DIRECT_PANEL_N10_COEFFICIENT = 90
DIRECT_PANEL_EXPECTED_EXAMPLES = 204_697_600
DIRECT_PANEL_LATTICE_STEP = 90
DIRECT_PANEL_MIN_EXAMPLES = 202_854_400
DIRECT_PANEL_MAX_EXAMPLES = 206_540_800
N10_SUM_MIN = 0
N10_SUM_EXPECTED = 20_480
N10_SUM_MAX = 40_960
SUPERSEDED_R02_EXAMPLE_ASSERTION = 224_604_160

SHARED_MATRIX_SPECS = (
    ("W_hr", (32, 32)), ("W_hz", (32, 32)), ("W_hn", (32, 32)),
    ("W_t1", (128, 14)), ("W_t2", (128, 128)),
    ("W_f1", (128, 160)), ("W_f2", (128, 128)), ("W_F", (9, 128)),
    ("W_g1", (128, 160)), ("W_g2", (128, 128)), ("W_G", (1, 128)),
)
R0_INPUT_MATRIX_SPECS = (
    ("W_ir", (32, 5)), ("W_iz", (32, 5)), ("W_in", (32, 5)),
)
R1_CONTEXT_MATRIX_SPECS = (("W_c", (32, 14)),)
R1_INPUT_MATRIX_SPECS = (
    ("W_ir", (32, 37)), ("W_iz", (32, 37)), ("W_in", (32, 37)),
)
COMMON_BIAS_SPECS = (
    ("b_ir", 32), ("b_iz", 32), ("b_in", 32),
    ("b_hr", 32), ("b_hz", 32), ("b_hn", 32),
    ("b_t1", 128), ("b_t2", 128),
    ("b_f1", 128), ("b_f2", 128), ("b_F", 9),
    ("b_g1", 128), ("b_g2", 128), ("b_G", 1),
)


def _parameter_count(representation: str) -> int:
    matrices = SHARED_MATRIX_SPECS + (
        R0_INPUT_MATRIX_SPECS if representation == "R0"
        else R1_CONTEXT_MATRIX_SPECS + R1_INPUT_MATRIX_SPECS
    )
    biases = COMMON_BIAS_SPECS + (() if representation == "R0" else (("b_c", 32),))
    return sum(rows * columns for _name, (rows, columns) in matrices) \
        + sum(width for _name, width in biases)


MODEL_PARAMETER_COUNTS = {"R0": _parameter_count("R0"), "R1": _parameter_count("R1")}

DOMAIN_LABELS = (
    "train/S0/state", "train/S0/word_cells", "train/S0/action",
    *(f"train/S1/state_lhs/{name}" for name in STATE_COORDINATES),
    *(f"train/S1/jitter/{name}" for name in STATE_COORDINATES),
    "train/S1/word_action",
    "eval/fit_support/state", "eval/fit_support/word_cells", "eval/fit_support/action",
    "eval/target_k6/state", "eval/target_k6/cells",
    "eval/target_k8/state", "eval/target_k8/cells",
    "eval/target_k12/state", "eval/target_k12/cells",
    "init/shared", "init/R0_input", "init/R1_context", "init/R1_input",
    "minibatch/S0", "minibatch/S1",
)

EFFECT_NAMES = ("S", "R", "I")
BRANCHES = (
    "FACTORIAL-MEASUREMENT-NONIDENTIFICATION",
    "INTERACTION-EFFECT",
    "ADDITIVE-SUPPORT-AND-REPRESENTATION-EFFECTS",
    "SUPPORT-EFFECT",
    "REPRESENTATION-EFFECT",
    "NO-USEFUL-FACTOR-EFFECT",
    "MIXED-FACTOR-EVIDENCE",
    "FACTORIAL-EFFECT-INDETERMINATE",
)

PROSPECTIVE_COST = {
    "paired_seed_blocks": 10,
    "cells": 4,
    "checkpoints": 40,
    "adamw_steps": 24_000,
    "registered_direct_example_accounting_unit":
        "one training row-segment or direct evaluation example evaluated once by one cell",
    "expected_direct_examples": DIRECT_PANEL_EXPECTED_EXAMPLES,
    "expected_training_direct_examples": 199_680_000,
    "exact_direct_evaluation_examples": DIRECT_EVALUATION_EXACT,
    "realized_direct_example_range": [
        DIRECT_PANEL_MIN_EXAMPLES, DIRECT_PANEL_MAX_EXAMPLES,
    ],
    "expected_equals_realized_asserted": False,
}

HISTORICAL_SUPERSEDED_COST = {
    "revision": "SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02",
    "superseded_executed_example_assertion": SUPERSEDED_R02_EXAMPLE_ASSERTION,
    "active_prospective_cost": False,
}


@dataclass(frozen=True)
class AdamWLaw:
    learning_rate: float = 3.0e-4
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1.0e-8
    weight_decay: float = 1.0e-5
    max_grad_norm: float = 1.0


ADAMW = AdamWLaw()


def static_contract() -> dict[str, object]:
    return {
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "composite_sha256": {
            "base_revision_02_card": BASE_CARD_SHA256,
            "revision_03_count_correction": COUNT_CORRECTION_SHA256,
            "revision_03_pro_closed_intake": PRO_CLOSED_INTAKE_SHA256,
        },
        "scientific_activity_started": False,
        "hmac_seed_namespace": HMAC_SEED_NAMESPACE.decode("ascii"),
        "domain_labels": list(DOMAIN_LABELS),
        "seed_indices": list(SEED_INDICES),
        "cells": list(CELLS),
        "row_counts": {
            "training_per_support_seed": TRAIN_ROWS,
            "fit_support_per_seed": FIT_SUPPORT_ROWS,
            "target_base_per_k_seed": TARGET_BASE_ROWS,
        },
        "optimizer": {
            "steps_per_cell": LOGICAL_STEPS,
            "batch_rows": LOGICAL_BATCH_ROWS,
            "batch_index": "b=n-1 for n=1,...,600",
            "checkpoint": "theta_600",
            **ADAMW.__dict__,
        },
        "model_parameter_counts": dict(MODEL_PARAMETER_COUNTS),
        "branches": list(BRANCHES),
        "partial_inspection_permitted": False,
        "stage_b_implemented": False,
        "order_or_relation_observable_implemented": False,
        "evidence_complexity": {
            "hypothetical_trajectory_search": False,
            "candidate_trajectory_count": 0,
            "future_simulated_search_transitions": 0,
            "fixed_small_n_exact_reference": 4,
        },
        "prospective_cost": dict(PROSPECTIVE_COST),
        "historical_superseded_cost": dict(HISTORICAL_SUPERSEDED_COST),
    }
