"""Frozen VQFP-B1 periodic field-service experiment.

This package implements the source object closed as
``VQFP-B1-MATH-CLOSURE-20260812-04``.  It deliberately contains no automatic
launch on import; :mod:`run` is the only execution entry point.
"""

from .config import FrozenConfig, VQFP_REVISION
from .models import Arm, VQFPModel

__all__ = ["Arm", "FrozenConfig", "VQFPModel", "VQFP_REVISION"]
