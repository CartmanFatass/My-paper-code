"""Pure scientific-semantic core for CBSC-OMRC-B01.

No RNG, tape generation, learner, PPO, adapter, artifact, CLI, or result
interpretation is defined in this package slice.
"""

from .contract import (
    ACTION_ORDER,
    BODY_SLOT_COUNT,
    CARRIER_COUNT,
    CONTROLLER_COUNT,
    DECISION_ACTION_MASK,
    EPISODE_TRANSITIONS,
    NONDECISION_ACTION_MASK,
    OPPORTUNITY_COUNT,
    PREAMBLE_TRANSITIONS,
    RECEIVER_COUNT,
    TRANSITIONS_PER_OPPORTUNITY,
    AccessMode,
    Action,
    BodySlot,
    Carrier,
    Controller,
    ContractValidationError,
    OpportunityPosition,
    PayloadRole,
    PreamblePosition,
    PrimitiveKind,
    Receiver,
    legal_action_mask,
    validate_preactivation_order,
)
from .ledger import (
    VALID,
    NativeLedger,
    apply_native_action,
    evaluator_oracle_action,
    evaluator_valid,
    native_ledger,
)
from .engine import LiteralB0Engine, b0_engine, build_observations
from .evaluator import EvaluationError, aggregate_evaluations, evaluate_episode
from .state import (
    BodyEvent,
    BodyRecord,
    CapabilityEvent,
    CarrierState,
    DecisionPrimitive,
    HostState,
    OwnerEvent,
    PreamblePrimitive,
    ReceiverState,
    SemanticEvent,
    SettlementPrimitive,
    apply_body_event,
    apply_capability_event,
    apply_owner_event,
    apply_semantic_event,
    make_decision,
    transition_body,
    transition_capability,
    transition_owner,
    transition_semantic,
)
from .token import (
    ABSENT_BYTE,
    BYTE_COUNT,
    BYTE_FIELD_ORDER,
    CHANNEL_COUNT,
    FLAG_COUNT,
    FLAG_FIELD_ORDER,
    NEUTRAL_PAYLOAD_SOURCE,
    ByteField,
    CanonicalTokenCodec,
    EventKindLayout,
    FlagField,
    LearnerProjection,
    PrimitiveToken,
    TokenValidationError,
)

__all__ = [name for name in globals() if not name.startswith("_")]
