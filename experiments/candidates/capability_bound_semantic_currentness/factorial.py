"""Exhaustive CBSC host construction with whole-carrier reassociation."""

from __future__ import annotations

from itertools import product

from .registered import validate_registered_spec
from .rng import canonical_dumps, nuisance_id
from .schema import (
    AccessState,
    BindingState,
    Body,
    Carrier,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    RegisteredSpec,
    SemanticState,
    World,
)


def nuisance_coordinates() -> tuple[NuisanceCoordinate, ...]:
    return tuple(NuisanceCoordinate(*bits) for bits in product((0, 1), repeat=7))


def _structural_id(kind: str, **coordinates: object) -> str:
    """Transparent canonical identity; never an admission or authenticity token."""

    return f"{kind}:{canonical_dumps(coordinates)}"


def _body_for(receiver: int, payload: PayloadState, coordinate: NuisanceCoordinate) -> Body:
    # Truth is keyed by physical receiver, never by presentation slot.  The
    # nuisance coordinate names the focal receiver's cached bit explicitly;
    # donor_bit belongs to the other physical receiver.
    own_bit = coordinate.old_bit if receiver == coordinate.physical_receiver else coordinate.donor_bit
    other_bit = coordinate.old_bit if receiver != coordinate.physical_receiver else coordinate.donor_bit
    own_phase = coordinate.z0 if receiver == 0 else coordinate.z1
    other_receiver = 1 - receiver
    other_phase = coordinate.z0 if other_receiver == 0 else coordinate.z1
    if payload is PayloadState.RECEIVER_CORRECT:
        source, content, neutral, phase = receiver, own_bit ^ own_phase, False, own_phase
    elif payload is PayloadState.SWAPPED:
        source, content, neutral, phase = other_receiver, other_bit ^ other_phase, False, other_phase
    else:
        source, content, neutral, phase = None, None, True, own_phase
    body_id = _structural_id(
        "body",
        addressed_receiver=receiver,
        payload_source_receiver=source,
        content_bit=content,
        native_neutral=neutral,
        public_phase=phase,
        epoch=0,
    )
    return Body(
        body_id=body_id,
        addressed_receiver=receiver,
        payload_source_receiver=source,
        content_bit=content,
        native_neutral=neutral,
        epoch=0,
        public_phase=phase,
    )


def _carrier_for(receiver: int, payload: PayloadState, coordinate: NuisanceCoordinate) -> Carrier:
    body = _body_for(receiver, payload, coordinate)
    carrier_id = _structural_id(
        "carrier",
        issued_to_receiver=receiver,
        body=body,
    )
    return Carrier(carrier_id, receiver, body)


def construct_world(
    owner: OwnerState,
    semantic: SemanticState,
    binding: BindingState,
    access: AccessState,
    payload: PayloadState,
    nuisance: NuisanceCoordinate,
) -> World:
    """Construct one world without consulting registration or an ambient RNG."""

    # All immutable bodies/carriers exist before PAYLOAD selects which pair is
    # exposed.  Consequently inventory identities are paired across payload
    # cells and the treatment never mutates carrier fields.
    inventory = tuple(
        _carrier_for(receiver, payload_role, nuisance)
        for payload_role in PayloadState
        for receiver in (0, 1)
    )
    offset = tuple(PayloadState).index(payload) * 2
    issued = (inventory[offset], inventory[offset + 1])
    assigned = issued if binding is BindingState.AUTHENTIC else (issued[1], issued[0])
    presented = assigned if nuisance.presentation_permutation == 0 else (assigned[1], assigned[0])
    nid = nuisance_id(nuisance)
    wid = _structural_id(
        "world",
        owner=owner.value,
        semantic=semantic.value,
        binding=binding.value,
        access=access.value,
        payload=payload.value,
        nuisance_id=nid,
    )
    return World(
        world_id=wid,
        nuisance_id=nid,
        owner=owner,
        semantic=semantic,
        binding=binding,
        access=access,
        payload=payload,
        nuisance=nuisance,
        focal_need_active=payload is not PayloadState.NATIVE_NEUTRAL,
        issued_inventory=inventory,
        issued_carriers=issued,
        carriers_by_physical_receiver=assigned,
        presented_carriers=presented,
    )


def enumerate_worlds(spec: RegisteredSpec) -> tuple[World, ...]:
    audit = validate_registered_spec(spec)
    if not audit.valid:
        raise ValueError(f"registered spec failed validation: {', '.join(audit.errors)}")
    worlds = tuple(
        construct_world(owner, semantic, binding, access, payload, coordinate)
        for owner, semantic, binding, access, payload in product(
            spec.owner_levels,
            spec.semantic_levels,
            spec.binding_levels,
            spec.access_levels,
            spec.payload_levels,
        )
        for coordinate in nuisance_coordinates()
    )
    if len(worlds) != spec.world_count or len({world.world_id for world in worlds}) != len(worlds):
        raise RuntimeError("exhaustive world construction violated registered support")
    return worlds


def whole_carrier_reassociation_is_valid(world: World) -> bool:
    if world.binding is BindingState.AUTHENTIC:
        return world.carriers_by_physical_receiver == world.issued_carriers
    assigned = world.carriers_by_physical_receiver
    issued = world.issued_carriers
    return (
        assigned == (issued[1], issued[0])
        and all(assigned[index].carrier_id != issued[index].carrier_id for index in (0, 1))
        and sorted(assigned, key=lambda carrier: carrier.issued_to_receiver)
        == sorted(issued, key=lambda carrier: carrier.issued_to_receiver)
    )


def world_inventory_record(world: World) -> dict[str, object]:
    """Direct structural record used by complete-result inventory validation."""

    from .schema import to_jsonable

    return {
        "world_id": world.world_id,
        "nuisance_id": world.nuisance_id,
        "owner": world.owner.value,
        "semantic": world.semantic.value,
        "binding": world.binding.value,
        "access": world.access.value,
        "payload": world.payload.value,
        "nuisance": to_jsonable(world.nuisance),
        "focal_need_active": world.focal_need_active,
        "issued_inventory": to_jsonable(world.issued_inventory),
        "carrier_assignment": [carrier.carrier_id for carrier in world.carriers_by_physical_receiver],
        "presentation": [carrier.carrier_id for carrier in world.presented_carriers],
    }


__all__ = ["construct_world", "enumerate_worlds", "nuisance_coordinates", "whole_carrier_reassociation_is_valid", "world_inventory_record"]
