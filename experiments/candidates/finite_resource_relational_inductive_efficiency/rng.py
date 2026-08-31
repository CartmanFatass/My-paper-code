"""Stateless, arm-independent addressed randomness for FRRIE.

SHA-256 is used here only as a deterministic pseudorandom function.  Nothing
in this module treats its output as authentication, integrity evidence, or an
admission gate.
"""

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
FP32_UNIFORM_BITS = 24
FP32_UNIFORM_DENOMINATOR = 1 << FP32_UNIFORM_BITS
FP32_UNIFORM_MAPPING_SCHEMA = "FRRIE_ADDRESSED_FP32_UNIFORM_V1"
SEMANTIC_RANDOM_VARIABLE_KINDS = frozenset({
    "event_time",
    "detection_uniform",
    "uplink_uniform",
    "base_uniform",
    "action_uniform",
    "origin_base_slot",
    "origin_role_local_index",
})
FORBIDDEN_ADDRESS_LABELS = frozenset({
    "arm", "arm_id", "cut", "cut_id", "intervention", "intervention_id",
    "branch", "branch_id",
})


def _reject_forbidden_labels(value: Mapping[str, Any]) -> None:
    for field in value:
        normalized = str(field).strip().lower().replace("-", "_")
        if normalized in FORBIDDEN_ADDRESS_LABELS or any(
            normalized.endswith(f"_{label}") for label in FORBIDDEN_ADDRESS_LABELS
        ):
            raise ContractError(
                "RNG addresses are arm-, cut-, intervention-, and branch-independent"
            )


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
        _reject_forbidden_labels(value)
        if set(value) != set(cls.__dataclass_fields__):
            raise ContractError("RNG address fields must be exact")
        return cls(**dict(value)).validate()


@dataclass(frozen=True, slots=True)
class SemanticRNGAddress:
    """One complete semantic coordinate for a rollout random variable.

    Optional coordinates remain explicit ``None`` values in canonical form.
    This prevents absence/presence of an action, collision, listener, event, or
    intervention from changing the coordinate layout.
    """

    seed_block: str
    purpose: str
    roster: int
    update: int
    episode: int
    basin: int | None
    event_ordinal: int | None
    slot: int | None
    public_role: int | None
    role_local_index: int | None
    sender: int | None
    receiver: int | None
    kind: str
    draw: int

    def validate(self) -> "SemanticRNGAddress":
        if not isinstance(self.seed_block, str) or not self.seed_block.startswith("FRRIE-"):
            raise ContractError("semantic RNG seed_block must be a fresh FRRIE label")
        if self.purpose not in {"TRAIN", "EVALUATE", "TEST_ONLY"}:
            raise ContractError("semantic RNG purpose is outside the rollout domain")
        if type(self.roster) is not int or self.roster not in (6, 9, 15, 21):
            raise ContractError("semantic RNG roster must be one of 6, 9, 15, or 21")
        if type(self.update) is not int or not 0 <= self.update <= 512:
            raise ContractError("semantic RNG update must be in [0,512]")
        if type(self.episode) is not int or self.episode < 0:
            raise ContractError("semantic RNG episode must be nonnegative")
        if self.purpose == "TRAIN":
            if self.roster not in (9, 15) or not 1 <= self.update <= 512 or self.episode >= 32:
                raise ContractError("TRAIN semantic coordinate is outside its per-roster panel")
        elif self.purpose == "EVALUATE":
            if not 1 <= self.update <= 512 or self.episode >= 256:
                raise ContractError("EVALUATE semantic coordinate is outside its panel")
        elif self.episode >= 256:
            raise ContractError("TEST_ONLY semantic episode must be in [0,255]")
        if self.kind not in SEMANTIC_RANDOM_VARIABLE_KINDS:
            raise ContractError("semantic RNG kind is outside the frozen domain")
        if type(self.draw) is not int or not 0 <= self.draw < 2**32:
            raise ContractError("semantic RNG draw must be uint32")

        bounds = {
            "basin": 2,
            "event_ordinal": 3,
            "slot": 12,
            "public_role": 3,
            "role_local_index": self.roster // 3,
            "sender": self.roster,
            "receiver": self.roster,
        }
        for field, upper in bounds.items():
            coordinate = getattr(self, field)
            if coordinate is not None and (
                type(coordinate) is not int or not 0 <= coordinate < upper
            ):
                raise ContractError(f"semantic RNG {field} must be absent or in [0,{upper - 1}]")

        present = {
            field for field in bounds if getattr(self, field) is not None
        }
        agent_fields = {"slot", "public_role", "role_local_index", "sender"}
        if self.kind == "event_time":
            expected = {"basin", "event_ordinal"}
        elif self.kind == "detection_uniform":
            expected = agent_fields
            if self.public_role not in (0, 1):
                raise ContractError("detection uniforms exist only for the two surveyor roles")
        elif self.kind == "uplink_uniform":
            expected = agent_fields | {"receiver"}
        elif self.kind in {"base_uniform", "action_uniform"}:
            expected = agent_fields
        elif self.kind in {"origin_base_slot", "origin_role_local_index"}:
            expected = {"public_role"}
        else:  # pragma: no cover - guarded by the exact kind set above
            raise RuntimeError("unreachable semantic RNG kind")
        if present != expected:
            raise ContractError(
                f"semantic RNG {self.kind} coordinates must be exactly {sorted(expected)}"
            )
        if agent_fields <= present:
            expected_sender = self.public_role * (self.roster // 3) + self.role_local_index
            if self.sender != expected_sender:
                raise ContractError(
                    "semantic RNG sender must equal the public-role/role-local simulator identity"
                )
        return self

    def canonical_bytes(self) -> bytes:
        self.validate()
        return canonical_json_bytes(asdict(self))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SemanticRNGAddress":
        _reject_forbidden_labels(value)
        if set(value) != set(cls.__dataclass_fields__):
            raise ContractError("semantic RNG address fields must be exact")
        return cls(**dict(value)).validate()


class AddressedRNG:
    """SHA-256 counter PRF with no mutable stream frontier."""

    def __init__(self, root: bytes | str):
        if isinstance(root, str):
            if len(root) != 64:
                raise ContractError("RNG root string must contain exactly 64 hexadecimal digits")
            try:
                root_bytes = bytes.fromhex(root)
            except ValueError as exc:
                raise ContractError("RNG root string must be hexadecimal") from exc
        elif isinstance(root, bytes) and len(root) == 32:
            root_bytes = root
        else:
            raise ContractError("RNG root must contain exactly 256 bits")
        self._root = root_bytes

    def block(
        self,
        address: RNGAddress | SemanticRNGAddress | Mapping[str, Any],
        block_index: int = 0,
    ) -> bytes:
        if isinstance(address, Mapping):
            _reject_forbidden_labels(address)
            if set(address) == set(SemanticRNGAddress.__dataclass_fields__):
                address = SemanticRNGAddress.from_mapping(address)
            else:
                address = RNGAddress.from_mapping(address)
        address.validate()
        if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index < 2**32:
            raise ContractError("RNG block_index must be uint32")
        schema = (
            b"FRRIE-SEMANTIC-ADDRESSED-RNG-V1\0"
            if isinstance(address, SemanticRNGAddress)
            else b"FRRIE-ADDRESSED-RNG-V1\0"
        )
        payload = schema + self._root + address.canonical_bytes() + block_index.to_bytes(4, "big")
        return hashlib.sha256(payload).digest()

    def uint64(self, address: RNGAddress | SemanticRNGAddress | Mapping[str, Any]) -> int:
        return int.from_bytes(self.block(address)[:8], "big", signed=False)

    def uniform01(self, address: RNGAddress | SemanticRNGAddress | Mapping[str, Any]) -> float:
        """Return an explicit binary64 uniform using the top 53 PRF bits."""

        return (self.uint64(address) >> 11) * (1.0 / 2**53)

    def uniform_float32(
        self, address: RNGAddress | SemanticRNGAddress | Mapping[str, Any],
    ) -> float:
        """Return the exact FP32 lattice uniform encoded by the top 24 PRF bits.

        Every possible result is ``k / 2**24`` for
        ``k in {0, ..., 2**24 - 1}``.  These dyadic values are exactly
        representable in binary32 and the maximum is therefore strictly below
        one without relying on a binary64-to-binary32 cast.
        """

        numerator = int.from_bytes(self.block(address)[:3], "big", signed=False)
        return numerator * (1.0 / FP32_UNIFORM_DENOMINATOR)

    def integer(
        self,
        address: RNGAddress | SemanticRNGAddress | Mapping[str, Any],
        upper: int,
    ) -> int:
        if isinstance(upper, bool) or not isinstance(upper, int) or not 0 < upper <= 2**64:
            raise ContractError("RNG integer upper bound must be in [1,2^64]")
        limit = 2**64 - (2**64 % upper)
        if isinstance(address, (RNGAddress, SemanticRNGAddress)):
            base = address
        elif set(address) == set(SemanticRNGAddress.__dataclass_fields__):
            base = SemanticRNGAddress.from_mapping(address)
        else:
            base = RNGAddress.from_mapping(address)
        for retry in range(1_000_000):
            candidate = int.from_bytes(self.block(base, retry)[:8], "big")
            if candidate < limit:
                return candidate % upper
        raise RuntimeError("unreachable RNG rejection bound")

    def tape_words(
        self, *addresses: RNGAddress | SemanticRNGAddress,
    ) -> tuple[tuple[dict[str, Any], bytes], ...]:
        """Return direct addressed words; callers compare coordinates and bytes literally."""
        return tuple((asdict(address.validate()), self.block(address)) for address in addresses)


def canonical_address(**fields: Any) -> RNGAddress:
    return RNGAddress.from_mapping(fields)


def float32_uniform_mapping_contract() -> dict[str, Any]:
    """Return the direct, root-free mapping contract for FP32 tape values."""

    return {
        "schema": FP32_UNIFORM_MAPPING_SCHEMA,
        "prf": "SHA-256",
        "prf_word_bits": 256,
        "selected_bits": FP32_UNIFORM_BITS,
        "selection": "MOST_SIGNIFICANT_BITS",
        "numerator_min": 0,
        "numerator_max": FP32_UNIFORM_DENOMINATOR - 1,
        "denominator": FP32_UNIFORM_DENOMINATOR,
        "formula": "TOP24 / 2**24",
        "support": "K_OVER_2_POW_24",
        "upper_endpoint_excluded": True,
    }


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
