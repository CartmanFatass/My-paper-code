"""Finite addressed CBSC-LR01 population and exact full-Q targets."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from experiments.candidates.capability_bound_semantic_currentness.factorial import construct_world
from experiments.candidates.capability_bound_semantic_currentness.policies import action_vector
from experiments.candidates.capability_bound_semantic_currentness.schema import (
    AccessState,
    BindingState,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    PolicyArm,
    SemanticState,
)

from .support import Address, Purpose, Split, canonical_bits, panel_addresses


_OWNERS: Final = (OwnerState.LIVE, OwnerState.BROKEN)
_SEMANTICS: Final = (SemanticState.PERSIST, SemanticState.REFRESH)
_BINDINGS: Final = (BindingState.AUTHENTIC, BindingState.WHOLE_CARRIER_REASSOCIATED)
_ACCESSES: Final = (AccessState.OPEN, AccessState.BINDING_GATED)
_PAYLOADS: Final = (
    PayloadState.RECEIVER_CORRECT,
    PayloadState.SWAPPED,
    PayloadState.NATIVE_NEUTRAL,
)
@dataclass(frozen=True)
class Cell:
    owner: OwnerState
    semantic: SemanticState
    binding: BindingState
    access: AccessState
    payload: PayloadState


@dataclass(frozen=True)
class Context:
    address: Address
    cell: Cell
    fields: dict[str, int]
    canonical: tuple[int, ...]
    target_q: tuple[Fraction, Fraction, Fraction]
    oracle_action: int


def decode_cell(cell: int) -> Cell:
    if type(cell) is not int or not 0 <= cell < 48:
        raise ValueError("cell must be in [0,48)")
    owner, remainder = divmod(cell, 24)
    semantic, remainder = divmod(remainder, 12)
    binding, remainder = divmod(remainder, 6)
    access, payload = divmod(remainder, 3)
    return Cell(_OWNERS[owner], _SEMANTICS[semantic], _BINDINGS[binding], _ACCESSES[access], _PAYLOADS[payload])


def _slot_values(slot: int) -> tuple[int, int, int, int, int, int]:
    receiver = slot & 1
    presentation = (slot >> 1) & 1
    old0 = (slot >> 2) & 1
    old1 = (slot >> 3) & 1
    z0 = ((slot >> 1) ^ (slot >> 2)) & 1
    z1 = ((slot >> 1) ^ (slot >> 3)) & 1
    return receiver, presentation, old0, old1, z0, z1


def _exact_world(cell: Cell, slot: int):
    receiver, presentation, old0, old1, z0, z1 = _slot_values(slot)
    old = (old0, old1)
    coordinate = NuisanceCoordinate(
        physical_receiver=receiver,
        old_bit=old[receiver],
        current_bit=1 - old[receiver],
        donor_bit=old[1 - receiver],
        z0=z0,
        z1=z1,
        presentation_permutation=presentation,
    )
    return construct_world(cell.owner, cell.semantic, cell.binding, cell.access, cell.payload, coordinate)


def _fields(address: Address, cell: Cell) -> dict[str, int]:
    q = address.slot
    receiver, presentation, old0, old1, z0, z1 = _slot_values(q)
    old = (old0, old1)
    owner_predecessor = 16 + 2 * ((q >> 2) & 1)
    owner_current = owner_predecessor if cell.owner is OwnerState.LIVE else owner_predecessor + 1
    body_epoch = 32 + 2 * ((q >> 3) & 1)
    current_epoch = body_epoch if cell.semantic is SemanticState.PERSIST else body_epoch + 1
    associated = receiver if cell.binding is BindingState.AUTHENTIC else 1 - receiver
    execution = receiver if cell.access is AccessState.OPEN else associated
    if cell.payload is PayloadState.NATIVE_NEUTRAL:
        payload_source = 255
        body_content = 0
    else:
        payload_source = execution if cell.payload is PayloadState.RECEIVER_CORRECT else 1 - execution
        body_content = old[payload_source] ^ (z0 if payload_source == 0 else z1)
    focal_base = old[receiver] if cell.semantic is SemanticState.PERSIST else 1 - old[receiver]
    focal_need = focal_base ^ (z0 if receiver == 0 else z1)
    return {
        "physical_receiver": receiver,
        "owner_predecessor": owner_predecessor,
        "owner_current": owner_current,
        "body_epoch": body_epoch,
        "current_epoch": current_epoch,
        "associated_carrier_issued_to": associated,
        "execution_carrier_issued_to": execution,
        "body_addressed_receiver": execution,
        "payload_source_receiver": payload_source,
        "carrier_nonce": address.carrier_nonce,
        "body_nonce": address.body_nonce,
        "presentation_slot": 128 + (receiver ^ presentation),
        "public_phase": 144 + ((z0 << 1) | z1),
        "focal_need_active": int(cell.payload is not PayloadState.NATIVE_NEUTRAL),
        "access_binding_gated": int(cell.access is AccessState.BINDING_GATED),
        "body_native_neutral": int(cell.payload is PayloadState.NATIVE_NEUTRAL),
        "body_content_bit": body_content,
        "focal_need_bit": focal_need,
        "public_z0": z0,
        "public_z1": z1,
        "presentation_flip": presentation,
    }


def context(address: Address) -> Context:
    cell = decode_cell(address.cell)
    fields = _fields(address, cell)
    vector = action_vector(_exact_world(cell, address.slot), PolicyArm.CBSC_RULE)
    target = (vector.serve, vector.refresh, vector.safe_fallback)
    maximum = max(target)
    winners = [index for index, value in enumerate(target) if value == maximum]
    if len(winners) != 1:
        raise RuntimeError("CBSC-LR01 exact target does not have a unique oracle action")
    return Context(address, cell, fields, canonical_bits(fields, address), target, winners[0])


def panel(purpose: Purpose, block: int, split: Split) -> tuple[Context, ...]:
    return tuple(context(address) for address in panel_addresses(purpose, block, split))


__all__ = ["Cell", "Context", "context", "decode_cell", "panel"]
