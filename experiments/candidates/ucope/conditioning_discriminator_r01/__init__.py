"""Semantic core for the UCOPE BC invertible-conditioning discriminator."""

from .conditioning import (
    ConditioningTransformError,
    ScoreEquivalence,
    TransformRecord,
    build_transform,
    pair_initial_coefficients,
    transform_features,
)
from .contract import (
    ARM_IDS,
    OBJECT_ID,
    ConditioningConfig,
    OptimizerContract,
)

__all__ = [
    "ARM_IDS",
    "OBJECT_ID",
    "ConditioningConfig",
    "ConditioningTransformError",
    "OptimizerContract",
    "ScoreEquivalence",
    "TransformRecord",
    "build_transform",
    "pair_initial_coefficients",
    "transform_features",
]
