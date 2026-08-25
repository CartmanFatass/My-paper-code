"""Exact SCDMP-B1 v5 construction.

Importing this package performs no random draws, model forwards, or scientific
activity.  Production is available only through the explicit CLI flag.
"""

from .config import CANDIDATE, REVISION

__all__ = ["CANDIDATE", "REVISION"]
