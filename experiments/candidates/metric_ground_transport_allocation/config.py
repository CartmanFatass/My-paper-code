"""Frozen constants for MGTAP-B1-SCIENCE-20260813-04."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

REVISION = "MGTAP-B1-SCIENCE-20260813-04"
ARMS = ("METRIC", "FREE")
BINDINGS = ("INTACT", "CUT")
TRAIN_SIZES = (4, 8)
EVAL_SIZES = (4, 6, 8, 12)
TASKS = (0, 1, 2, 3)
ORDERED_PAIRS = tuple(permutations(TASKS, 2))
LOADS = ("SLACK", "OVERLOAD")
CALIBRATION_SEEDS = (1103, 1129, 1151, 1171)
FINAL_SEEDS = (
    2003, 2027, 2053, 2081, 2111, 2141, 2179, 2203,
    2237, 2269, 2297, 2333, 2357, 2389, 2417, 2447,
)
LEARNING_RATES = (0.01, 0.03, 0.10)
LAMBDAS = (0.0, 0.0001)
CALIBRATION_UPDATES = 64
FINAL_UPDATES = 128
VALIDATION_TAPES = 16
EVALUATION_TAPES = 64
CHECKPOINTS = (32, 64)
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
    "calibration_training_decisions": 589_824,
    "validation_decisions": 294_912,
    "conclusion_training_decisions": 786_432,
    "base_evaluation_decisions": 786_432,
    "replay_evaluation_decisions": 786_432,
    "autoregressive_agent_steps": 21_823_488,
    "optimizer_updates": 14_336,
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
    calibration_training = 4 * 6 * 4 * 64 * 48 * 2
    validation = 4 * 6 * 4 * 2 * 2 * 12 * 2 * 16 * 2
    conclusion_training = 4 * 16 * 128 * 48 * 2
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
        "optimizer_updates": 4 * 6 * 4 * 64 + 4 * 16 * 128,
    }
