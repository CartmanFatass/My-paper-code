"""RSCF r01 native full-suffix boundary.

Only deterministic TEST construction/oracle helpers and the fail-closed native
V2 ABI are exported here.  The Python oracle is never a production fallback.
"""

from .native_contract import (
    ABI_VERSION,
    ALLOWED_ROSTERS,
    ALLOWED_WIDTHS,
    HOST_KIND,
    MAX_AGENTS,
    MODE_FULL_ROTATED,
    MODE_INTACT,
    NATIVE_THREADS,
    ActorParameters,
    FactualEpisodeBatch,
    FactualTrajectory,
    NativeSuffixResult,
    ShadowTrajectory,
    SuffixBatch,
    make_test_actor_parameters,
    make_test_factual_episode_batch,
    make_test_suffix_batch,
    validate_actor_parameters,
    validate_factual_episode_batch,
    validate_suffix_batch,
    with_factual_actions,
    with_factual_terminal,
    suffix_batch_from_factual_trajectory,
)
from .native_loader import (
    NativeHostIdentity,
    load_native_host,
    native_factual_trajectory,
    native_full_suffix,
    native_shadow_trajectory,
)
from .native_oracle import (
    python_factual_trajectory,
    python_full_suffix,
    python_shadow_trajectory,
    run_gate_a_self_check,
)

__all__ = [
    "ABI_VERSION",
    "ALLOWED_ROSTERS",
    "ALLOWED_WIDTHS",
    "HOST_KIND",
    "MAX_AGENTS",
    "MODE_FULL_ROTATED",
    "MODE_INTACT",
    "NATIVE_THREADS",
    "ActorParameters",
    "FactualEpisodeBatch",
    "FactualTrajectory",
    "NativeHostIdentity",
    "NativeSuffixResult",
    "ShadowTrajectory",
    "SuffixBatch",
    "load_native_host",
    "make_test_actor_parameters",
    "make_test_factual_episode_batch",
    "make_test_suffix_batch",
    "native_factual_trajectory",
    "native_full_suffix",
    "native_shadow_trajectory",
    "python_factual_trajectory",
    "python_full_suffix",
    "python_shadow_trajectory",
    "run_gate_a_self_check",
    "suffix_batch_from_factual_trajectory",
    "validate_actor_parameters",
    "validate_factual_episode_batch",
    "validate_suffix_batch",
    "with_factual_actions",
    "with_factual_terminal",
]
