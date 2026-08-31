"""Prospective CRTO common-history action-gate experiment.

This package is intentionally isolated from the historical CRTO-B1 execution
surface.  In particular, importing it never reads an old result, checkpoint,
optimizer, cursor, or probe artifact.
"""

from .config import OBJECT_ID, PRODUCTION_CONFIG, RunConfig
from .contracts import ACTION_ORDER, Budget, PanelRow, Representation, Split

__all__ = [
    "ACTION_ORDER", "Budget", "OBJECT_ID", "PRODUCTION_CONFIG", "PanelRow",
    "Representation", "RunConfig", "Split",
]
