"""CCIC-B1 revision-06 experiment package.

Importing this package performs no training, evaluation, random draws, or I/O.
"""

from .config import REVISION, ExperimentConfig

__all__ = ["REVISION", "ExperimentConfig"]
