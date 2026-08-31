"""Result-blind FRRIE construction surface.

This package deliberately contains no production simulator loader.  Production
activity is admitted only through a caller-supplied direct native
backend at :mod:`.host`.
"""

from .contracts.core import (
    FRRIE_CHECKPOINT_V1,
    FRRIE_COMPLETE_PANEL_RESULT_V1,
    FRRIE_MANIFEST_V1,
    FRRIE_SEALED_SEED_PACKET_V1,
    FRRIE_TERMINAL_V1,
    ContractError,
    validate_manifest,
)

__all__ = [
    "FRRIE_MANIFEST_V1", "FRRIE_CHECKPOINT_V1",
    "FRRIE_SEALED_SEED_PACKET_V1", "FRRIE_COMPLETE_PANEL_RESULT_V1",
    "FRRIE_TERMINAL_V1", "ContractError", "validate_manifest",
]
