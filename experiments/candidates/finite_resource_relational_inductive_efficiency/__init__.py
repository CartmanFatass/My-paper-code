"""FRRIE V2 result-blind construction surface.

The package owns the external-action native source and adapter, paired model,
RSCF training primitives, checkpoint codec, and descriptive 28-quantity
reduction.  Result activity remains fail-closed because no simultaneous mean
inference law is frozen for the 24-block object.  V1 identifiers are retained
only so legacy scaffold inputs can be rejected explicitly.
"""

from .contracts.core import (
    FRRIE_CHECKPOINT_V1,
    FRRIE_CHECKPOINT_V2,
    FRRIE_COMPLETE_PANEL_RESULT_V1,
    FRRIE_COMPLETE_PANEL_RESULT_V2,
    FRRIE_COMPLETE_PANEL_ANALYSIS_V2,
    FRRIE_MANIFEST_V1,
    FRRIE_MANIFEST_V2,
    FRRIE_SEALED_SEED_PACKET_V1,
    FRRIE_SEALED_SEED_PACKET_V2,
    FRRIE_TERMINAL_V1,
    FRRIE_TERMINAL_V2,
    INFERENCE_CONTRACT,
    ContractError,
    structural_description,
    validate_manifest,
)

__all__ = [
    "FRRIE_MANIFEST_V2", "FRRIE_CHECKPOINT_V2",
    "FRRIE_SEALED_SEED_PACKET_V2", "FRRIE_COMPLETE_PANEL_RESULT_V2",
    "FRRIE_COMPLETE_PANEL_ANALYSIS_V2", "FRRIE_TERMINAL_V2",
    "INFERENCE_CONTRACT", "ContractError", "validate_manifest",
    "structural_description",
    # Legacy scaffold identities; production V2 validators reject them.
    "FRRIE_MANIFEST_V1", "FRRIE_CHECKPOINT_V1",
    "FRRIE_SEALED_SEED_PACKET_V1", "FRRIE_COMPLETE_PANEL_RESULT_V1",
    "FRRIE_TERMINAL_V1",
]
