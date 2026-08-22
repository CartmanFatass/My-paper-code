"""TEST-only Gate A fixtures for the SGSP RSCF native-host benchmark.

Nothing in this package is a production runner, empirical coordinate, learned
model, or scientific activity object.  It is deliberately small and
materialized so the native host can be compared to a transparent Python
reference on the same suffix inputs.
"""

from .contract import (
    ABI_TAG,
    CONCURRENCY_LEVELS,
    NATIVE_THREADS,
    SUPPORTED_WIDTHS,
    validate_fixture_batch,
)
from .fixture_oracle import make_fixture_batch, python_suffix_batch

__all__ = [
    "ABI_TAG",
    "CONCURRENCY_LEVELS",
    "NATIVE_THREADS",
    "SUPPORTED_WIDTHS",
    "make_fixture_batch",
    "python_suffix_batch",
    "validate_fixture_batch",
]
