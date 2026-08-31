"""Isolated contextual paid-acquisition R01 implementation.

Importing this package performs no materialization, training, or evaluation.
"""

from .contract import CONTRACT_ID, FEATURE_NAMES, validate_contract
from .oracle import build_flip_certificate, construct_flip_certificate
from .support import build_fixed_behavior_plan, materialize_fixed_behavior_plan, validate_support

__all__ = [
    "CONTRACT_ID",
    "FEATURE_NAMES",
    "validate_contract",
    "build_flip_certificate",
    "construct_flip_certificate",
    "build_fixed_behavior_plan",
    "materialize_fixed_behavior_plan",
    "validate_support",
]
