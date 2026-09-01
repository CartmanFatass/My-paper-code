"""Frozen, result-blind constants for the CBSC-OMRC-B01 semantic core."""

from __future__ import annotations

from enum import Enum, IntEnum


class ContractValidationError(ValueError):
    """Raised when a value contradicts the frozen OMRC-B01 contract."""


class Controller(IntEnum):
    """The sole learning controller; receivers/carriers are environment entities."""

    C0 = 0
    ONLY = 0


class Receiver(IntEnum):
    R0 = 0
    R1 = 1


class BodySlot(IntEnum):
    S0 = 0
    S1 = 1


class Carrier(IntEnum):
    C0 = 0
    C1 = 1


class Action(IntEnum):
    WAIT = 0
    SERVE = 1
    REFRESH = 2
    SAFE_FALLBACK = 3


class AccessMode(str, Enum):
    OPEN = "OPEN"
    GATED = "GATED"


class PayloadRole(str, Enum):
    CORRECT = "CORRECT"
    SWAPPED = "SWAPPED"
    NEUTRAL = "NEUTRAL"


class PrimitiveKind(str, Enum):
    """Coarse semantic families retained for the host/state API."""

    PREAMBLE = "PREAMBLE"
    OWNER = "OWNER"
    SEMANTIC = "SEMANTIC"
    CAPABILITY = "CAPABILITY"
    BODY = "BODY"
    DECISION = "DECISION"
    SETTLEMENT = "SETTLEMENT"


class EventKind(IntEnum):
    """Literal public event-kind codes fixed by innovator clarification ``.02``."""

    INIT_OWNER = 0x01
    INIT_SEMANTIC = 0x02
    INIT_CAPABILITY = 0x03
    INIT_BODY = 0x04
    OWNER = 0x10
    SEMANTIC = 0x11
    CAPABILITY = 0x12
    BODY = 0x13
    NOOP_OWNER = 0x14
    NOOP_SEMANTIC = 0x15
    NOOP_CAPABILITY = 0x16
    NOOP_BODY = 0x17
    DECISION = 0x20
    SETTLEMENT = 0x21


class PreamblePosition(IntEnum):
    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5
    P6 = 6
    P7 = 7


class OpportunityPosition(IntEnum):
    PREACTION_0 = 0
    PREACTION_1 = 1
    PREACTION_2 = 2
    PREACTION_3 = 3
    DECISION = 4
    SETTLEMENT = 5


PREACTION_KINDS = frozenset(
    {PrimitiveKind.OWNER, PrimitiveKind.SEMANTIC, PrimitiveKind.CAPABILITY, PrimitiveKind.BODY}
)

PREAMBLE_EVENT_KINDS = frozenset(
    {
        EventKind.INIT_OWNER,
        EventKind.INIT_SEMANTIC,
        EventKind.INIT_CAPABILITY,
        EventKind.INIT_BODY,
    }
)
PREACTION_EVENT_KINDS = frozenset(
    {
        EventKind.OWNER,
        EventKind.SEMANTIC,
        EventKind.CAPABILITY,
        EventKind.BODY,
        EventKind.NOOP_OWNER,
        EventKind.NOOP_SEMANTIC,
        EventKind.NOOP_CAPABILITY,
        EventKind.NOOP_BODY,
    }
)
NOOP_EVENT_KINDS = frozenset(
    {
        EventKind.NOOP_OWNER,
        EventKind.NOOP_SEMANTIC,
        EventKind.NOOP_CAPABILITY,
        EventKind.NOOP_BODY,
    }
)

EVENT_KIND_TO_PRIMITIVE_KIND = {
    EventKind.INIT_OWNER: PrimitiveKind.PREAMBLE,
    EventKind.INIT_SEMANTIC: PrimitiveKind.PREAMBLE,
    EventKind.INIT_CAPABILITY: PrimitiveKind.PREAMBLE,
    EventKind.INIT_BODY: PrimitiveKind.PREAMBLE,
    EventKind.OWNER: PrimitiveKind.OWNER,
    EventKind.SEMANTIC: PrimitiveKind.SEMANTIC,
    EventKind.CAPABILITY: PrimitiveKind.CAPABILITY,
    EventKind.BODY: PrimitiveKind.BODY,
    EventKind.NOOP_OWNER: PrimitiveKind.OWNER,
    EventKind.NOOP_SEMANTIC: PrimitiveKind.SEMANTIC,
    EventKind.NOOP_CAPABILITY: PrimitiveKind.CAPABILITY,
    EventKind.NOOP_BODY: PrimitiveKind.BODY,
    EventKind.DECISION: PrimitiveKind.DECISION,
    EventKind.SETTLEMENT: PrimitiveKind.SETTLEMENT,
}

CONTROLLER_COUNT = 1
RECEIVER_COUNT = 2
BODY_SLOT_COUNT = 2
CARRIER_COUNT = 2
PREAMBLE_TRANSITIONS = 8
OPPORTUNITY_COUNT = 24
PREACTION_TRANSITIONS_PER_OPPORTUNITY = 4
DECISION_TRANSITIONS_PER_OPPORTUNITY = 1
SETTLEMENT_TRANSITIONS_PER_OPPORTUNITY = 1
TRANSITIONS_PER_OPPORTUNITY = (
    PREACTION_TRANSITIONS_PER_OPPORTUNITY
    + DECISION_TRANSITIONS_PER_OPPORTUNITY
    + SETTLEMENT_TRANSITIONS_PER_OPPORTUNITY
)
EPISODE_TRANSITIONS = PREAMBLE_TRANSITIONS + OPPORTUNITY_COUNT * TRANSITIONS_PER_OPPORTUNITY

OWNER_EPOCH_TOKEN_MIN = 16
OWNER_EPOCH_TOKEN_MAX = 63

ACTION_ORDER = tuple(Action)
NONDECISION_ACTION_MASK = (True, False, False, False)
DECISION_ACTION_MASK = (False, True, True, True)


def primitive_kind(kind: PrimitiveKind | EventKind) -> PrimitiveKind:
    """Map a literal event code to its coarse host family."""

    if isinstance(kind, PrimitiveKind):
        return kind
    if isinstance(kind, EventKind):
        return EVENT_KIND_TO_PRIMITIVE_KIND[kind]
    raise ContractValidationError("kind must be a PrimitiveKind or EventKind")


def legal_action_mask(
    kind: PrimitiveKind | EventKind,
) -> tuple[bool, bool, bool, bool]:
    """Return the exact mask in :class:`Action` order for a primitive event."""

    return (
        DECISION_ACTION_MASK
        if primitive_kind(kind) is PrimitiveKind.DECISION
        else NONDECISION_ACTION_MASK
    )


def validate_preactivation_order(kinds: tuple[PrimitiveKind, ...]) -> None:
    """Validate one supplied four-position order without generating an order law."""

    if len(kinds) != PREACTION_TRANSITIONS_PER_OPPORTUNITY:
        raise ContractValidationError("an opportunity requires exactly four pre-action kinds")
    if any(not isinstance(kind, PrimitiveKind) for kind in kinds):
        raise ContractValidationError("pre-action entries must be PrimitiveKind values")
    if frozenset(kinds) != PREACTION_KINDS or len(set(kinds)) != len(kinds):
        raise ContractValidationError(
            "pre-action order must contain OWNER, SEMANTIC, CAPABILITY, and BODY exactly once"
        )


assert EPISODE_TRANSITIONS == 152
