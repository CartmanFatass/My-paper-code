"""Exact, zero-learning RISP event-conditioned Bayes certificate package.

Importing this package is inert.  In particular, it does not load a registered
specification, enumerate a census, evaluate a controller, or publish an
artifact.  The result-bearing route is available only through the explicit
``certify`` CLI command.
"""

from .contract import (
    COMPLETE_RESULT_SCHEMA,
    CONTROLLERS,
    DIRECTION_ID,
    PUBLIC_HISTORY_SCHEMA,
    SPEC_SCHEMA,
    TWIN_CENSUS_SCHEMA,
    registered_spec,
)

__all__ = [
    "COMPLETE_RESULT_SCHEMA",
    "CONTROLLERS",
    "DIRECTION_ID",
    "PUBLIC_HISTORY_SCHEMA",
    "SPEC_SCHEMA",
    "TWIN_CENSUS_SCHEMA",
    "registered_spec",
]
