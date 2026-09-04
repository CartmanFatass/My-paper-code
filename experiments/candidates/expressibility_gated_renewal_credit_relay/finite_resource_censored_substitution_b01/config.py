"""Frozen constants for EGRCR-FRCS-B01."""

from __future__ import annotations

OBJECT_ID = "EGRCR-FRCS-B01-20260904"
SCIENTIFIC_SEED = 2026090401

SOURCES = (0, 1, 2, 3)
CONTENTS = (-1, 1)
ACTIONS = (-1, 1)
MODES = ("PERSIST", "REPLACE", "EXPIRE")
TRANSITIONS_PER_EPISODE = 3

TRAIN_EPISODES = 192
TRAIN_TRANSITIONS = TRAIN_EPISODES * TRANSITIONS_PER_EPISODE
UPDATES = 128
BATCH_SIZE = 32
EXAMPLE_EXPOSURES = UPDATES * BATCH_SIZE
EVALUATION_EPISODES = 256
EVALUATION_TRANSITIONS = EVALUATION_EPISODES * TRANSITIONS_PER_EPISODE
EXACT_EVALUATION_CELLS = len(SOURCES) * len(CONTENTS) * len(ACTIONS) * len(MODES)
ACTION_TIME_MODEL_CELLS = len(SOURCES) * len(CONTENTS) * len(ACTIONS)

PARAMETERS = 32
FP32_BYTES = 4
ADAM_MOMENT_BYTES = 2 * PARAMETERS * FP32_BYTES
ADAM_STEP_BYTES = FP32_BYTES
ADAM_STATE_BYTES = ADAM_MOMENT_BYTES + ADAM_STEP_BYTES
LEARNING_RATE = 0.01
ADAM_BETAS = (0.9, 0.999)
ADAM_EPS = 1e-8
INIT_HALF_RANGE = 0.05
ARM_ORDER = ("GENERIC_PAIR", "ASSOCIATION_FACTOR")
TIE_RULE = "choose relation -1 when Q(-1) == Q(+1)"

PROJECTED_ARM_SECONDS = round(3.0 * (
    5.0
    + 0.01 * TRAIN_TRANSITIONS
    + 0.005 * EXAMPLE_EXPOSURES
    + 0.01 * EVALUATION_TRANSITIONS
    + 0.02 * EXACT_EVALUATION_CELLS
), 2)
ARM_WALL_CAP_SECONDS = 600.0
INVOCATION_WALL_CAP_SECONDS = 1200.0

EXPOSURE_LINE = (
    "updates=128; adam_lr=0.01; nominal_lr_exposure=1.28; "
    "init_half_range=0.05; nominal_exposure_over_init_half_range=25.6"
)

GENERIC_LAYOUT = (
    {"name": "T1", "shape": [4, 2, 2], "flat": [0, 16]},
    {"name": "T2", "shape": [4, 2, 2], "flat": [16, 32]},
)
FACTOR_LAYOUT = (
    {"name": "U1", "shape": [4, 2], "flat": [0, 8]},
    {"name": "V1", "shape": [2, 2], "flat": [8, 12]},
    {"name": "U2", "shape": [4, 2], "flat": [12, 20]},
    {"name": "V2", "shape": [2, 2], "flat": [20, 24]},
    {"name": "B", "shape": [4], "flat": [24, 28]},
    {"name": "D", "shape": [2], "flat": [28, 30]},
    {"name": "E", "shape": [2], "flat": [30, 32]},
)

RNG_NAMESPACES = {
    "initialization": 11,
    "training_source": 101,
    "training_content": 102,
    "training_action": 103,
    "training_mode": 104,
    "minibatch_permutation": 201,
    "evaluation_source": 301,
    "evaluation_content": 302,
    "evaluation_mode": 303,
    "evaluation_action_uniform": 304,
}


def prospective_counts() -> dict[str, int]:
    return {
        "training_episodes": TRAIN_EPISODES,
        "training_environment_transitions": TRAIN_TRANSITIONS,
        "optimizer_updates_per_learned_arm": UPDATES,
        "minibatch_size": BATCH_SIZE,
        "optimizer_example_exposures_per_learned_arm": EXAMPLE_EXPOSURES,
        "evaluation_episodes_per_arm_or_reference": EVALUATION_EPISODES,
        "evaluation_environment_transitions_per_arm_or_reference": EVALUATION_TRANSITIONS,
        "exact_evaluation_cells_per_arm_or_reference": EXACT_EVALUATION_CELLS,
        "trainable_parameters_per_learned_arm": PARAMETERS,
    }


def project_cost_payload() -> dict[str, object]:
    return {
        "mode": "project-cost",
        "object_id": OBJECT_ID,
        "prospective_static_calculation": True,
        "creates_trajectories_models_optimizers_or_results": False,
        "benchmarks_runtime": False,
        "counts": prospective_counts(),
        "cost_law": {
            "formula": (
                "3 * (5 + 0.01*training_environment_transitions + "
                "0.005*optimizer_example_exposures + "
                "0.01*evaluation_environment_transitions + 0.02*exact_evaluation_cells)"
            ),
            "coefficients_are_prospective_planning_weights": True,
            "projected_seconds_per_learned_arm": PROJECTED_ARM_SECONDS,
            "learned_arms": 2,
            "arm_wall_cap_seconds": ARM_WALL_CAP_SECONDS,
            "sequential_invocation_wall_cap_seconds": INVOCATION_WALL_CAP_SECONDS,
        },
        "exposure_line": EXPOSURE_LINE,
    }
