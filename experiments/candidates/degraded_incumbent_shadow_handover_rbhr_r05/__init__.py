"""Native construction and TEST-only preactivity surfaces for DISH RBHR r05.

Nothing in this package creates a scientific master, coordinate, model,
checkpoint, training rollout, evaluation result, or empirical authority.
"""

from .contracts import Arm, GateAFixture, GateAResult, TEST_NAMESPACE
from .production_contract import COMPONENT, PREACTIVITY_NAMESPACE, SCIENCE_REVISION

__all__ = [
    "Arm", "COMPONENT", "GateAFixture", "GateAResult",
    "PREACTIVITY_NAMESPACE", "SCIENCE_REVISION", "TEST_NAMESPACE",
]
