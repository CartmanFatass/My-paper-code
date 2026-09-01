"""Independent FRRIE B01 production surface.

Nothing in this namespace imports R01/R02 manifests, result maps, lifecycle
states, or inference rules.  It reuses only the accepted package-native host,
fresh actor/critic, RSCF learner primitives, and direct Adam-state codec.
"""

from .constants import EXPERIMENT_ID
from .contract import B01ContractError, validate_manifest

__all__ = ["EXPERIMENT_ID", "B01ContractError", "validate_manifest"]
