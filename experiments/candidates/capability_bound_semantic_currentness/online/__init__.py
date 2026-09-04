"""General online-learning pilot infrastructure for CBSC.

This package does not define a scientific transition/reward schedule or a
scientific result polarity.
"""

from .evaluator import EvaluationReceipt, PredictivePolicy, evaluate_adaptation_free
from .learner import LearnerValidationError, PredictiveStep, QStep, RecurrentQLearner
from .performance import PERFORMANCE_DISPOSITION, PERFORMANCE_LIMITATIONS
from .tape import (
    PotentialOutcomeTape,
    StepBatch,
    TapeValidationError,
    VectorizedPotentialOutcomeBatch,
)
from .trainer import (
    BoundedReplay,
    OnlineQTrainer,
    TrainerConfig,
    TrainerValidationError,
    TrainingReceipt,
)

__all__ = [
    "BoundedReplay",
    "EvaluationReceipt",
    "LearnerValidationError",
    "OnlineQTrainer",
    "PERFORMANCE_DISPOSITION",
    "PERFORMANCE_LIMITATIONS",
    "PotentialOutcomeTape",
    "PredictivePolicy",
    "PredictiveStep",
    "QStep",
    "RecurrentQLearner",
    "StepBatch",
    "TapeValidationError",
    "TrainerConfig",
    "TrainerValidationError",
    "TrainingReceipt",
    "VectorizedPotentialOutcomeBatch",
    "evaluate_adaptation_free",
]
