"""Stateless, arm-independent addressed randomness for FRRIE."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .contracts.core import ContractError, canonical_json_bytes

RNG_DOMAINS = frozenset({
    "INITIALIZATION", "MINIBATCH_ORDER", "POTENTIAL_OUTCOME", "ENVIRONMENT",
    "ACTION", "EVALUATION", "TEST_ONLY",
})
PURPOSES = frozenset({"INITIALIZE", "TRAIN", "EVALUATE", "TEST_ONLY"})


@dataclass(frozen=True, slots=True)
class RNGAddress:
    seed_block: str
    purpose: str
    roster: int
    update: int
    episode: int
    step: int
    entity: int
    draw: int
    domain: str

    def validate(self) -> "RNGAddress":
        if not isinstance(self.seed_block, str) or not self.seed_block:
            raise ContractError("RNG seed_block must be nonempty")
        if self.purpose not in PURPOSES:
            raise ContractError("RNG purpose is outside the frozen domain")
        if self.domain not in RNG_DOMAINS:
            raise ContractError("RNG domain is outside the frozen domain")
        bounds = {
            "roster": (0, 21), "update": (0, 512),
            "episode": (0, 1_000_000_000), "step": (0, 1_000_000),
            "entity": (0, 21), "draw": (0, 1_000_000_000),
        }
        for field, (lower, upper) in bounds.items():
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
                raise ContractError(f"RNG {field} must be in [{lower},{upper}]")
        if self.purpose == "INITIALIZE":
            if self.domain != "INITIALIZATION" or any((self.roster, self.update, self.episode, self.step, self.entity)):
                raise ContractError("INITIALIZE addresses use the zero global coordinate")
        elif self.purpose == "TRAIN":
            if (
                self.roster not in (9, 15) or not 1 <= self.update <= 512
                or not 0 <= self.episode < 64 or not 0 <= self.step < 12
                or not 0 <= self.entity < self.roster
            ):
                raise ContractError("TRAIN RNG coordinate is outside the frozen panel")
        elif self.purpose == "EVALUATE":
            if (
                self.roster not in (6, 9, 15, 21) or not 1 <= self.update <= 512
                or not 0 <= self.episode < 256 or not 0 <= self.step < 12
                or not 0 <= self.entity < self.roster
            ):
                raise ContractError("EVALUATE RNG coordinate is outside the complete panel")
        return self

    def canonical_bytes(self) -> bytes:
        self.validate()
        return canonical_json_bytes(asdict(self))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RNGAddress":
        if any(field in value for field in ("arm", "arm_id", "intervention", "cut")):
            raise ContractError("RNG addresses are arm- and intervention-independent")
        if set(value) != set(cls.__dataclass_fields__):
            raise ContractError("RNG address fields must be exact")
        return cls(**dict(value)).validate()


class AddressedRNG:
    """SHA-256 counter PRF with no mutable stream frontier."""

    def __init__(self, root: bytes | str):
        if isinstance(root, str):
            if len(root) != 64:
                raise ContractError("RNG root string must be a SHA-256 hex value")
            try:
                root_bytes = bytes.fromhex(root)
            except ValueError as exc:
                raise ContractError("RNG root string must be hexadecimal") from exc
        elif isinstance(root, bytes) and len(root) == 32:
            root_bytes = root
        else:
            raise ContractError("RNG root must contain exactly 256 bits")
        self._root = root_bytes

    def block(self, address: RNGAddress | Mapping[str, Any], block_index: int = 0) -> bytes:
        if isinstance(address, Mapping):
            address = RNGAddress.from_mapping(address)
        address.validate()
        if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index < 2**32:
            raise ContractError("RNG block_index must be uint32")
        payload = b"FRRIE-ADDRESSED-RNG-V1\0" + self._root + address.canonical_bytes() + block_index.to_bytes(4, "big")
        return hashlib.sha256(payload).digest()

    def uint64(self, address: RNGAddress | Mapping[str, Any]) -> int:
        return int.from_bytes(self.block(address)[:8], "big", signed=False)

    def uniform01(self, address: RNGAddress | Mapping[str, Any]) -> float:
        return (self.uint64(address) >> 11) * (1.0 / 2**53)

    def integer(self, address: RNGAddress | Mapping[str, Any], upper: int) -> int:
        if isinstance(upper, bool) or not isinstance(upper, int) or not 0 < upper <= 2**64:
            raise ContractError("RNG integer upper bound must be in [1,2^64]")
        limit = 2**64 - (2**64 % upper)
        base = address if isinstance(address, RNGAddress) else RNGAddress.from_mapping(address)
        for retry in range(1_000_000):
            candidate = int.from_bytes(self.block(base, retry)[:8], "big")
            if candidate < limit:
                return candidate % upper
        raise RuntimeError("unreachable RNG rejection bound")

    def tape_words(self, *addresses: RNGAddress) -> tuple[tuple[dict[str, Any], bytes], ...]:
        """Return direct addressed words; callers compare coordinates and bytes literally."""
        return tuple((asdict(address.validate()), self.block(address)) for address in addresses)


def canonical_address(**fields: Any) -> RNGAddress:
    return RNGAddress.from_mapping(fields)


def rollout_tape_contract(
    *, seed_block: str, purpose: str, roster: int, update: int, episode: int,
) -> dict[str, Any]:
    """Intervention-free direct contract shared by intact and rotated cells."""
    if purpose not in {"TRAIN", "EVALUATE"}:
        raise ContractError("rollout tape purpose must be TRAIN or EVALUATE")
    probe = RNGAddress(
        seed_block=seed_block,
        purpose=purpose,
        roster=roster,
        update=update,
        episode=episode,
        step=0,
        entity=0,
        draw=0,
        domain="ENVIRONMENT" if purpose == "TRAIN" else "EVALUATION",
    ).validate()
    return {
        "schema": "FRRIE_ADDRESSED_TAPE_V1",
        "seed_block": probe.seed_block,
        "purpose": probe.purpose,
        "roster": probe.roster,
        "update": probe.update,
        "episode": probe.episode,
    }
