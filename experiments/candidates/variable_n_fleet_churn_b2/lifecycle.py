"""Fail-closed typed lifecycle registry for VNFC-B2.

Opaque identifiers remain dictionary keys.  Only validity bits and payload bits
cross the numerical-policy boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import C0, C1, C2, C3


@dataclass(frozen=True)
class Authority:
    entity: str
    owner_generation: int
    membership_epoch: int
    role: int
    lease_generation: int


@dataclass
class CapsulePair:
    authority: Authority
    entity_payload: int | None = None
    role_payload: int | None = None
    entity_scope: tuple[str, int] | None = None
    role_scope: tuple[str, int, int, int] | None = None


class LifecycleRegistry:
    """External registry with the card's exact two-mask lifecycle table."""

    def __init__(self) -> None:
        self._pairs: dict[tuple[str, int], CapsulePair] = {}
        self._broken_keys: set[tuple[str, int]] = set()

    def bind(self, authority: Authority) -> CapsulePair:
        key = (authority.entity, authority.owner_generation)
        pair = self._pairs.get(key)
        if pair is None:
            pair = CapsulePair(authority=authority)
            self._pairs[key] = pair
        else:
            pair.authority = authority
        return pair

    def observe_entity(self, authority: Authority, payload: int) -> None:
        pair = self.bind(authority)
        pair.entity_payload = int(payload)
        pair.entity_scope = (authority.entity, authority.owner_generation)

    def observe_role(self, authority: Authority, payload: int) -> None:
        pair = self.bind(authority)
        pair.role_payload = int(payload)
        pair.role_scope = (
            authority.entity, authority.owner_generation,
            authority.role, authority.lease_generation,
        )

    def transition(self, before: Authority, after: Authority, cell: str) -> None:
        old_key = (before.entity, before.owner_generation)
        old = self._pairs.get(old_key)
        if cell == C0:
            if before != after:
                self._pairs.pop(old_key, None)
                return
        elif cell == C1:
            continuous = (
                before.entity == after.entity
                and before.owner_generation == after.owner_generation
                and before.role == after.role
                and before.lease_generation == after.lease_generation
                and after.membership_epoch != before.membership_epoch
            )
            if not continuous:
                self._pairs.pop(old_key, None)
                return
        elif cell == C2:
            same_owner_new_lease = (
                before.entity == after.entity
                and before.owner_generation == after.owner_generation
                and (before.role != after.role or before.lease_generation != after.lease_generation)
            )
            if not same_owner_new_lease:
                self._pairs.pop(old_key, None)
                return
            if old is not None:
                old.role_payload = None
                old.role_scope = None
        elif cell == C3:
            self._broken_keys.add(old_key)
            self._pairs.pop(old_key, None)
            self._pairs.pop((after.entity, after.owner_generation), None)
            self.bind(after)
            return
        else:
            self._pairs.pop(old_key, None)
            return
        if old is not None:
            old.authority = after

    def exposed(self, authority: Authority) -> tuple[float, float, float, float]:
        pair = self._pairs.get((authority.entity, authority.owner_generation))
        if pair is None:
            return (0.0, 0.0, 0.0, 0.0)
        entity_valid = pair.entity_scope == (authority.entity, authority.owner_generation)
        role_valid = pair.role_scope == (
            authority.entity, authority.owner_generation,
            authority.role, authority.lease_generation,
        )
        entity_payload = pair.entity_payload if entity_valid else None
        role_payload = pair.role_payload if role_valid else None
        return (
            float(entity_payload is not None), float(entity_payload or 0),
            float(role_payload is not None), float(role_payload or 0),
        )

    def clear_both(self, authority: Authority) -> None:
        self._pairs.pop((authority.entity, authority.owner_generation), None)

    def hard_stale_errors(self, active: list[Authority]) -> dict[str, int]:
        invalid_entity = invalid_role = 0
        for authority in active:
            pair = self._pairs.get((authority.entity, authority.owner_generation))
            if pair is None:
                continue
            invalid_entity += int(
                pair.entity_payload is not None
                and pair.entity_scope != (authority.entity, authority.owner_generation)
            )
            invalid_role += int(
                pair.role_payload is not None
                and pair.role_scope != (
                    authority.entity, authority.owner_generation,
                    authority.role, authority.lease_generation,
                )
            )
        return {
            "entity_payload_under_zero_mask": invalid_entity,
            "role_payload_under_zero_mask": invalid_role,
            # Owner-break transitions delete the keyed pair synchronously.  A
            # temporarily inactive but still-authorized owner is not an error.
            "capsule_across_owner_break": sum(
                key in self._pairs for key in self._broken_keys
            ),
        }
