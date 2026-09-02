"""Relay corridor host family for duration-plan experiments E2-E4.

Normative specification:

* ``docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md`` (revision 4, accepted)
* ``docs/Claude_docs/plans/RELAY_CORRIDOR_MECHANICS_20260902.md`` (finalised companion)
* ``docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`` Parts IV and V

The host core (:mod:`envs.relay_corridor.host`) is pure NumPy: batch dimension
first, no torch, no native code, and no imports from ``experiments/candidates``.
:mod:`envs.relay_corridor.references` computes the reference returns and both
registered margins by exact dynamic programming / enumeration, and
:mod:`envs.relay_corridor.adapter` presents the host to the HMASD base route.
"""

from envs.relay_corridor.config import (
    PROPOSAL_GRID,
    RelayCorridorConfig,
    HorizonValidationError,
    proposal_config,
    rows_per_rollout,
    validate_horizon,
)
from envs.relay_corridor.renewal import (
    BernoulliHazard,
    RenewalLaw,
    make_renewal_law,
)
from envs.relay_corridor.rng import (
    STREAM_ENTITY,
    STREAM_REGION_EVENT,
    stream_generator,
    stream_key,
)
from envs.relay_corridor.host import (
    KEEP,
    RENEW,
    RelayCorridorHost,
    obs_layout,
    state_layout,
)
from envs.relay_corridor.references import (
    FixedKOracle,
    GreedyOnPublicState,
    OpenLoopPlan,
    ReferenceReport,
    SwitchingOracle,
    dp_service_profile,
    enumerate_references,
    rollout_reference,
)
from envs.relay_corridor.adapter import RelayCorridorAdapter

__all__ = [
    "PROPOSAL_GRID",
    "RelayCorridorConfig",
    "HorizonValidationError",
    "proposal_config",
    "rows_per_rollout",
    "validate_horizon",
    "BernoulliHazard",
    "RenewalLaw",
    "make_renewal_law",
    "STREAM_ENTITY",
    "STREAM_REGION_EVENT",
    "stream_generator",
    "stream_key",
    "KEEP",
    "RENEW",
    "RelayCorridorHost",
    "obs_layout",
    "state_layout",
    "ReferenceReport",
    "dp_service_profile",
    "enumerate_references",
    "FixedKOracle",
    "GreedyOnPublicState",
    "OpenLoopPlan",
    "SwitchingOracle",
    "rollout_reference",
    "RelayCorridorAdapter",
]
