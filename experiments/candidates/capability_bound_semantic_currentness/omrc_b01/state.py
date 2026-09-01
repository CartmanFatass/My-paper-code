"""Pure state primitives for the scientifically specified OMRC-B01 rules."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .contract import (
    AccessMode,
    BodySlot,
    Carrier,
    ContractValidationError,
    OPPORTUNITY_COUNT,
    OWNER_EPOCH_TOKEN_MAX,
    OWNER_EPOCH_TOKEN_MIN,
    PayloadRole,
    Receiver,
)


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ContractValidationError(f"{name} must be bool")


def _require_opaque_token(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractValidationError(f"{name} must be an integer opaque token")
    if not OWNER_EPOCH_TOKEN_MIN <= value <= OWNER_EPOCH_TOKEN_MAX:
        raise ContractValidationError(
            f"{name} must be in [{OWNER_EPOCH_TOKEN_MIN}, {OWNER_EPOCH_TOKEN_MAX}]"
        )


def _require_enum(name: str, value: object, enum_type: type) -> None:
    if not isinstance(value, enum_type):
        raise ContractValidationError(f"{name} must be {enum_type.__name__}")


@dataclass(frozen=True)
class ReceiverState:
    current_owner: int
    current_epoch: int
    current_need: bool

    def __post_init__(self) -> None:
        _require_opaque_token("current_owner", self.current_owner)
        _require_opaque_token("current_epoch", self.current_epoch)
        _require_bool("current_need", self.current_need)


@dataclass(frozen=True)
class BodyRecord:
    issuance_owner: int
    issuance_epoch: int
    carrier: Carrier
    addressed_receiver: Receiver
    payload_source_receiver: Receiver | None
    content: bool
    native_neutral: bool

    def __post_init__(self) -> None:
        _require_opaque_token("issuance_owner", self.issuance_owner)
        _require_opaque_token("issuance_epoch", self.issuance_epoch)
        _require_enum("carrier", self.carrier, Carrier)
        _require_enum("addressed_receiver", self.addressed_receiver, Receiver)
        if self.payload_source_receiver is not None:
            _require_enum("payload_source_receiver", self.payload_source_receiver, Receiver)
        _require_bool("content", self.content)
        _require_bool("native_neutral", self.native_neutral)
        if self.native_neutral:
            if self.payload_source_receiver is not None or self.content:
                raise ContractValidationError(
                    "a native-neutral body must have no payload source and content zero"
                )
        elif self.payload_source_receiver is None:
            raise ContractValidationError("a non-neutral body must have a payload source")


@dataclass(frozen=True)
class CarrierState:
    permitted_receiver: Receiver

    def __post_init__(self) -> None:
        _require_enum("permitted_receiver", self.permitted_receiver, Receiver)


@dataclass(frozen=True)
class HostState:
    receivers: tuple[ReceiverState, ReceiverState]
    bodies: tuple[BodyRecord | None, BodyRecord | None]
    carriers: tuple[CarrierState, CarrierState]

    def __post_init__(self) -> None:
        if not isinstance(self.receivers, tuple) or len(self.receivers) != 2:
            raise ContractValidationError("receivers must be a two-entry tuple")
        if not all(isinstance(item, ReceiverState) for item in self.receivers):
            raise ContractValidationError("receivers entries must be ReceiverState")
        if not isinstance(self.bodies, tuple) or len(self.bodies) != 2:
            raise ContractValidationError("bodies must be a two-entry tuple")
        if not all(item is None or isinstance(item, BodyRecord) for item in self.bodies):
            raise ContractValidationError("body entries must be BodyRecord or None")
        if not isinstance(self.carriers, tuple) or len(self.carriers) != 2:
            raise ContractValidationError("carriers must be a two-entry tuple")
        if not all(isinstance(item, CarrierState) for item in self.carriers):
            raise ContractValidationError("carriers entries must be CarrierState")

    def receiver(self, receiver: Receiver) -> ReceiverState:
        _require_enum("receiver", receiver, Receiver)
        return self.receivers[int(receiver)]

    def body(self, slot: BodySlot) -> BodyRecord:
        _require_enum("slot", slot, BodySlot)
        body = self.bodies[int(slot)]
        if body is None:
            raise ContractValidationError("presented body slot is not initialized")
        return body

    def carrier(self, carrier: Carrier) -> CarrierState:
        _require_enum("carrier", carrier, Carrier)
        return self.carriers[int(carrier)]


@dataclass(frozen=True)
class OwnerEvent:
    receiver: Receiver
    old_owner: int
    new_owner: int

    def __post_init__(self) -> None:
        _require_enum("receiver", self.receiver, Receiver)
        _require_opaque_token("old_owner", self.old_owner)
        _require_opaque_token("new_owner", self.new_owner)
        if self.old_owner == self.new_owner:
            raise ContractValidationError("OWNER replacement must change the opaque token")


@dataclass(frozen=True)
class SemanticEvent:
    receiver: Receiver
    old_epoch: int
    new_epoch: int
    old_need: bool
    new_need: bool

    def __post_init__(self) -> None:
        _require_enum("receiver", self.receiver, Receiver)
        _require_opaque_token("old_epoch", self.old_epoch)
        _require_opaque_token("new_epoch", self.new_epoch)
        _require_bool("old_need", self.old_need)
        _require_bool("new_need", self.new_need)
        if self.old_epoch == self.new_epoch:
            raise ContractValidationError("semantic replacement must change the opaque epoch")


@dataclass(frozen=True)
class CapabilityEvent:
    carrier: Carrier
    permitted_receiver: Receiver

    def __post_init__(self) -> None:
        _require_enum("carrier", self.carrier, Carrier)
        _require_enum("permitted_receiver", self.permitted_receiver, Receiver)


@dataclass(frozen=True)
class BodyEvent:
    slot: BodySlot
    addressed_receiver: Receiver
    carrier: Carrier
    payload_role: PayloadRole

    def __post_init__(self) -> None:
        _require_enum("slot", self.slot, BodySlot)
        _require_enum("addressed_receiver", self.addressed_receiver, Receiver)
        _require_enum("carrier", self.carrier, Carrier)
        _require_enum("payload_role", self.payload_role, PayloadRole)


@dataclass(frozen=True)
class DecisionPrimitive:
    opportunity_index: int
    presented_slot: BodySlot
    target_receiver: Receiver
    access_mode: AccessMode
    request_active: bool
    request_need: bool

    def __post_init__(self) -> None:
        if isinstance(self.opportunity_index, bool) or not isinstance(self.opportunity_index, int):
            raise ContractValidationError("opportunity_index must be int")
        if not 0 <= self.opportunity_index < OPPORTUNITY_COUNT:
            raise ContractValidationError("opportunity_index must be in [0, 23]")
        _require_enum("presented_slot", self.presented_slot, BodySlot)
        _require_enum("target_receiver", self.target_receiver, Receiver)
        _require_enum("access_mode", self.access_mode, AccessMode)
        _require_bool("request_active", self.request_active)
        _require_bool("request_need", self.request_need)


@dataclass(frozen=True)
class PreamblePrimitive:
    """A typed clock position only; preamble token fields remain unfrozen."""

    position: int

    def __post_init__(self) -> None:
        if isinstance(self.position, bool) or not isinstance(self.position, int) or not 0 <= self.position < 8:
            raise ContractValidationError("preamble position must be in [0, 7]")


@dataclass(frozen=True)
class SettlementPrimitive:
    """The forced settlement clock position; it carries no learner reward field."""

    opportunity_index: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.opportunity_index, bool)
            or not isinstance(self.opportunity_index, int)
            or not 0 <= self.opportunity_index < OPPORTUNITY_COUNT
        ):
            raise ContractValidationError("opportunity_index must be in [0, 23]")


def apply_owner_event(state: HostState, event: OwnerEvent) -> HostState:
    current = state.receiver(event.receiver)
    if current.current_owner != event.old_owner:
        raise ContractValidationError("OWNER event old token does not match host state")
    updated = replace(current, current_owner=event.new_owner)
    receivers = list(state.receivers)
    receivers[int(event.receiver)] = updated
    return replace(state, receivers=tuple(receivers))


def transition_owner(
    state: HostState, receiver: Receiver, new_owner: int
) -> tuple[HostState, OwnerEvent]:
    event = OwnerEvent(receiver, state.receiver(receiver).current_owner, new_owner)
    return apply_owner_event(state, event), event


def apply_semantic_event(state: HostState, event: SemanticEvent) -> HostState:
    current = state.receiver(event.receiver)
    if current.current_epoch != event.old_epoch or current.current_need is not event.old_need:
        raise ContractValidationError("semantic event old values do not match host state")
    updated = replace(
        current, current_epoch=event.new_epoch, current_need=event.new_need
    )
    receivers = list(state.receivers)
    receivers[int(event.receiver)] = updated
    return replace(state, receivers=tuple(receivers))


def transition_semantic(
    state: HostState, receiver: Receiver, new_epoch: int, new_need: bool
) -> tuple[HostState, SemanticEvent]:
    current = state.receiver(receiver)
    event = SemanticEvent(
        receiver, current.current_epoch, new_epoch, current.current_need, new_need
    )
    return apply_semantic_event(state, event), event


def apply_capability_event(state: HostState, event: CapabilityEvent) -> HostState:
    carriers = list(state.carriers)
    carriers[int(event.carrier)] = CarrierState(event.permitted_receiver)
    return replace(state, carriers=tuple(carriers))


def transition_capability(
    state: HostState, carrier: Carrier, permitted_receiver: Receiver
) -> tuple[HostState, CapabilityEvent]:
    event = CapabilityEvent(carrier, permitted_receiver)
    return apply_capability_event(state, event), event


def apply_body_event(state: HostState, event: BodyEvent) -> HostState:
    addressed = state.receiver(event.addressed_receiver)
    if event.payload_role is PayloadRole.CORRECT:
        source: Receiver | None = event.addressed_receiver
        content = addressed.current_need
        neutral = False
    elif event.payload_role is PayloadRole.SWAPPED:
        source = Receiver.R1 if event.addressed_receiver is Receiver.R0 else Receiver.R0
        content = state.receiver(source).current_need
        neutral = False
    else:
        source = None
        content = False
        neutral = True
    record = BodyRecord(
        issuance_owner=addressed.current_owner,
        issuance_epoch=addressed.current_epoch,
        carrier=event.carrier,
        addressed_receiver=event.addressed_receiver,
        payload_source_receiver=source,
        content=content,
        native_neutral=neutral,
    )
    bodies = list(state.bodies)
    bodies[int(event.slot)] = record
    return replace(state, bodies=tuple(bodies))


def transition_body(
    state: HostState,
    slot: BodySlot,
    addressed_receiver: Receiver,
    carrier: Carrier,
    payload_role: PayloadRole,
) -> tuple[HostState, BodyEvent]:
    event = BodyEvent(slot, addressed_receiver, carrier, payload_role)
    return apply_body_event(state, event), event


def make_decision(
    state: HostState,
    *,
    opportunity_index: int,
    presented_slot: BodySlot,
    target_receiver: Receiver,
    access_mode: AccessMode,
    request_active: bool,
) -> DecisionPrimitive:
    """Expose current request need without repeating current OWNER or epoch."""

    return DecisionPrimitive(
        opportunity_index=opportunity_index,
        presented_slot=presented_slot,
        target_receiver=target_receiver,
        access_mode=access_mode,
        request_active=request_active,
        request_need=state.receiver(target_receiver).current_need,
    )
