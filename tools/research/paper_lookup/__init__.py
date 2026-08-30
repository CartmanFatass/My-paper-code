"""Recorded-response paper lookup normalizers.

Adapted from K-Dense Inc.'s MIT-licensed skills/paper-lookup at commit
f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f. Copyright (c) 2025 K-Dense Inc.
MIT License: permission is hereby granted to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies, subject to inclusion of this notice.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""

from .normalizers import (
    PaperLookupInputError,
    normalize_arxiv_atom,
    normalize_jats,
    normalize_openalex,
    reconcile_pagination,
)

__all__ = [
    "PaperLookupInputError",
    "normalize_arxiv_atom",
    "normalize_jats",
    "normalize_openalex",
    "reconcile_pagination",
]
