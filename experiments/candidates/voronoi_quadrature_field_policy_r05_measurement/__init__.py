"""TEST-only VQFP-FERL r05 numeric/ANALYTIC measurement package.

This package has no production namespace, coordinate, seed, model, checkpoint,
training, evaluation, or result API.  It only exposes the bounded fixture
measurement authorized on 2026-08-22.
"""

from .contracts import (
    ANALYTIC_STATE_COUNT,
    TEST_NAMESPACE,
    WORKER_SWEEP,
    WIDTH_SWEEP,
)
from .measurement import run_measurement

__all__ = [
    "ANALYTIC_STATE_COUNT",
    "TEST_NAMESPACE",
    "WIDTH_SWEEP",
    "WORKER_SWEEP",
    "run_measurement",
]

