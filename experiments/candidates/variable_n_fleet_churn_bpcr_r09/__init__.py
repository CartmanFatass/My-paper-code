"""Clean-room native construction for VNFC BPCR science revision 09.

This package contains construction and deterministic conformance surfaces only.
It does not define empirical identities, coordinates, training runs, or results.
"""

from .contracts import CARD_REVISION, DIRECTION_ID, STAGE

__all__ = ["CARD_REVISION", "DIRECTION_ID", "STAGE"]
