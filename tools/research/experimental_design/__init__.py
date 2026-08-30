"""On-demand deterministic experimental-design schedule tooling."""

from .engine import (
    MAX_ARMS,
    MAX_FACTORS,
    MAX_FACTORIAL_RUNS,
    MAX_LEVELS_PER_FACTOR,
    MAX_UNITS,
    DesignValidationError,
    build_schedule,
    validate_schedule,
    write_schedule,
)

__all__ = [
    "MAX_ARMS",
    "MAX_FACTORS",
    "MAX_FACTORIAL_RUNS",
    "MAX_LEVELS_PER_FACTOR",
    "MAX_UNITS",
    "DesignValidationError",
    "build_schedule",
    "validate_schedule",
    "write_schedule",
]
