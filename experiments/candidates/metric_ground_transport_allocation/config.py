"""Frozen constants for MGTAP matched-update-support R01."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

REVISION = "MGTAP-B1-MATCHED-UPDATE-SUPPORT-20260827-R01"
STOCHASTIC_NAMESPACE = "mgtap_b1_matched_update_support_20260827_r01"
ARMS = ("METRIC", "FREE")
BINDINGS = ("INTACT", "CUT")
TRAIN_SIZES = (4, 8)
EVAL_SIZES = (4, 6, 8, 12)
TASKS = (0, 1, 2, 3)
ORDERED_PAIRS = tuple(permutations(TASKS, 2))
LOADS = ("SLACK", "OVERLOAD")
CALIBRATION_SEEDS = (3109, 3119, 3121, 3137)
FINAL_SEEDS = (
    4001, 4003, 4007, 4013, 4019, 4021, 4027, 4049,
    4051, 4057, 4073, 4079, 4091, 4093, 4099, 4111,
)
LEARNING_RATES = (0.01, 0.03, 0.10)
LAMBDAS = (0.0, 0.0001)
CALIBRATION_UPDATES = 256
FINAL_UPDATES = 512
VALIDATION_TAPES = 16
EVALUATION_TAPES = 64
STATIONARITY_REFERENCE = 224
SELECTION_CHECKPOINT = 256
CONCLUSION_CHECKPOINT = 512
CHECKPOINTS = (STATIONARITY_REFERENCE, SELECTION_CHECKPOINT)
STATIONARITY_TOLERANCE = 0.005
ENTROPY_COEFFICIENT = 0.005
UNIFORM_MIXTURE = 0.05
LOGIT_CLIP = 6.0
GRAD_CLIP = 5.0
DISPLAYED_COORDINATES = {
    "INTACT": (0.0, 2.0, 4.0, 6.0),
    "CUT": (6.0, 2.0, 4.0, 0.0),
}
ROLE_COORDINATES = (0.0, 6.0)
TRUE_UTILITY = (
    (1.0, 2.0 / 3.0, 1.0 / 3.0, 0.0),
    (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0),
)
HEADROOM_MARGIN = 1.0 / 12.0
PERFORMANCE_MARGIN = 0.02
ROBUSTNESS_MARGIN = 0.02
NONINFERIORITY_MARGIN = -0.01
BINDING_VALUE_MARGIN = 0.02
INERT_VALUE_EPSILON = 0.02
BINDING_ACTION_MARGIN = 0.10
INERT_ACTION_EPSILON = 0.02
EXPECTED_COUNTS = {
    "calibration_training_decisions": 2_359_296,
    "validation_decisions": 294_912,
    "conclusion_training_decisions": 3_145_728,
    "base_evaluation_decisions": 786_432,
    "replay_evaluation_decisions": 786_432,
    "autoregressive_agent_steps": 46_596_096,
    "optimizer_updates": 57_344,
}
GATE_ONLY_COUNTS = {
    "calibration_training_decisions": 2_359_296,
    "validation_decisions": 294_912,
    "conclusion_training_decisions": 0,
    "base_evaluation_decisions": 0,
    "replay_evaluation_decisions": 0,
    "autoregressive_agent_steps": 15_925_248,
    "optimizer_updates": 24_576,
}


@dataclass(frozen=True)
class HyperParameters:
    learning_rate: float
    weight_decay: float


GRID = tuple(HyperParameters(lr, wd) for lr in LEARNING_RATES for wd in LAMBDAS)


def demand(n: int, pair: tuple[int, int], load: str, epoch: int) -> tuple[int, int, int, int]:
    a, b = pair
    values = [0, 0, 0, 0]
    if epoch == 1:
        values[a] = n // 2
        values[b] = n // 2
    elif epoch == 2 and load == "SLACK":
        values[a] = n // 2
    elif epoch == 2 and load == "OVERLOAD":
        values[a] = n
        values[b] = n
    else:
        raise ValueError((n, pair, load, epoch))
    return tuple(values)


def workload_counts() -> dict[str, int]:
    calibration_training = 4 * 6 * 4 * CALIBRATION_UPDATES * 48 * 2
    validation = 4 * 6 * 4 * 2 * 2 * 12 * 2 * 16 * 2
    conclusion_training = 4 * 16 * FINAL_UPDATES * 48 * 2
    evaluation = 4 * 16 * 4 * 12 * 2 * 64 * 2
    # Each decision has N steps. Training is balanced over N=4,8 and evaluation
    # over N=4,6,8,12.
    calibration_steps = calibration_training * 6
    validation_steps = validation * 6
    conclusion_steps = conclusion_training * 6
    evaluation_steps = 4 * 16 * 12 * 2 * 64 * 2 * sum(EVAL_SIZES)
    return {
        "calibration_training_decisions": calibration_training,
        "validation_decisions": validation,
        "conclusion_training_decisions": conclusion_training,
        "base_evaluation_decisions": evaluation,
        "replay_evaluation_decisions": evaluation,
        "autoregressive_agent_steps": calibration_steps + validation_steps + conclusion_steps + 2 * evaluation_steps,
        "optimizer_updates": (
            4 * 6 * 4 * CALIBRATION_UPDATES + 4 * 16 * FINAL_UPDATES
        ),
    }
