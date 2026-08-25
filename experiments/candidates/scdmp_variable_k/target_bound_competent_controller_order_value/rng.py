"""Pure HMAC-SHA256 RNG/address APIs for an externally supplied master.

There is intentionally no operating-system RNG import and no master-creation
function in this module.  Production authority must supply one exact 32-byte
master only after the separate Root lease gate has passed.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Final

from .empirical_contract import DOMAIN_ADDRESS_SCHEMAS, DOMAIN_LABELS, REPLICATES


REPLICATE_PREFIX: Final[bytes] = b"SCDMP-TBCC-ORDER-VALUE-r01/replicate/"
ADDRESS_PREFIX: Final[bytes] = b"SCDMP-TBCC-R02-ADDRESS-v1\0"
_DOMAIN_SET = frozenset(DOMAIN_LABELS)
_DOMAIN_FIELDS = dict(DOMAIN_ADDRESS_SCHEMAS)
_UINT64_LIMIT = 1 << 64


class RNGContractError(ValueError):
    pass


def validate_external_master(master: bytes) -> bytes:
    if type(master) is not bytes or len(master) != 32:
        raise RNGContractError("external master must be exactly 32 bytes")
    return master


def master_digest(master: bytes) -> str:
    return hashlib.sha256(validate_external_master(master)).hexdigest()


def replicate_message(replicate: int) -> bytes:
    if isinstance(replicate, bool) or replicate not in REPLICATES:
        raise RNGContractError("replicate must be an integer in [0,24)")
    return REPLICATE_PREFIX + replicate.to_bytes(4, "big", signed=False)


def replicate_key(master: bytes, replicate: int) -> bytes:
    return hmac.new(validate_external_master(master), replicate_message(replicate), hashlib.sha256).digest()


def domain_key(master: bytes, replicate: int, domain: str) -> bytes:
    if domain not in _DOMAIN_SET:
        raise RNGContractError(f"unregistered TBCC RNG domain: {domain!r}")
    label = domain.encode("ascii")
    message = b"domain\0" + len(label).to_bytes(2, "big") + label
    return hmac.new(replicate_key(master, replicate), message, hashlib.sha256).digest()


def encode_address(parts: tuple[object, ...]) -> bytes:
    encoded = bytearray(ADDRESS_PREFIX)
    for part in parts:
        if isinstance(part, bool):
            tag, payload = b"b", b"1" if part else b"0"
        elif isinstance(part, int):
            tag, payload = b"i", str(part).encode("ascii")
        elif isinstance(part, str):
            tag, payload = b"s", part.encode("utf-8")
        else:
            raise RNGContractError("address parts must be bool, int, or str")
        encoded.extend(tag)
        encoded.extend(len(payload).to_bytes(4, "big"))
        encoded.extend(payload)
    return bytes(encoded)


@dataclass(frozen=True)
class AddressRNG:
    key: bytes

    def __post_init__(self) -> None:
        if type(self.key) is not bytes or len(self.key) != 32:
            raise RNGContractError("domain key must be exactly 32 bytes")

    def raw_u64(self, *parts: object, counter: int = 0) -> int:
        if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
            raise RNGContractError("counter must be a nonnegative integer")
        message = encode_address(tuple(parts)) + counter.to_bytes(8, "big")
        return int.from_bytes(hmac.new(self.key, message, hashlib.sha256).digest()[:8], "big")

    def uniform53(self, *parts: object) -> float:
        return (self.raw_u64(*parts) >> 11) * (2.0 ** -53)

    def uniform24(self, *parts: object) -> float:
        return (self.raw_u64(*parts) >> 40) * (2.0 ** -24)

    def bounded(self, modulus: int, *parts: object) -> int:
        if isinstance(modulus, bool) or not isinstance(modulus, int) or modulus <= 0:
            raise RNGContractError("modulus must be a positive integer")
        limit = (_UINT64_LIMIT // modulus) * modulus
        counter = 0
        while True:
            value = self.raw_u64(*parts, counter=counter)
            if value < limit:
                return value % modulus
            counter += 1

    def permutation(self, count: int, *parts: object) -> tuple[int, ...]:
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise RNGContractError("permutation count must be positive")
        values = list(range(count))
        for index in range(count - 1, 0, -1):
            other = self.bounded(index + 1, *parts, "fisher-yates", index)
            values[index], values[other] = values[other], values[index]
        return tuple(values)


def for_domain(master: bytes, replicate: int, domain: str) -> AddressRNG:
    return AddressRNG(domain_key(master, replicate, domain))


def raw_u64(master: bytes, replicate: int, domain: str, **address: object) -> int:
    """Draw from one registered address after exact field-inventory checking."""

    if domain not in _DOMAIN_FIELDS:
        raise RNGContractError(f"unregistered TBCC RNG domain: {domain!r}")
    fields = _DOMAIN_FIELDS[domain]
    if set(address) != set(fields):
        raise RNGContractError(f"address field inventory differs for domain {domain!r}")
    parts: list[object] = []
    for field in fields:
        value = address[field]
        if not isinstance(value, (bool, int, str)):
            raise RNGContractError("registered address values must be bool, int, or str")
        parts.extend((field, value))
    return for_domain(master, replicate, domain).raw_u64(*parts)


def uniform53(master: bytes, replicate: int, domain: str, **address: object) -> float:
    return (raw_u64(master, replicate, domain, **address) >> 11) * (2.0 ** -53)


def uniform24(master: bytes, replicate: int, domain: str, **address: object) -> float:
    return (raw_u64(master, replicate, domain, **address) >> 40) * (2.0 ** -24)


def domain_separation_proof(master: bytes) -> dict[str, object]:
    validate_external_master(master)
    replicate_messages = tuple(replicate_message(value) for value in REPLICATES)
    digests = tuple(
        hashlib.sha256(domain_key(master, replicate, domain)).hexdigest()
        for replicate in REPLICATES
        for domain in DOMAIN_LABELS
    )
    return {
        "schema": "SCDMP_TBCC_R02_HMAC_DOMAIN_PROOF_V1",
        "replicate_messages_injective": len(set(replicate_messages)) == len(REPLICATES),
        "domain_labels_disjoint": len(set(DOMAIN_LABELS)) == len(DOMAIN_LABELS),
        "derived_domain_key_digests_unique": len(set(digests)) == len(digests),
        "address_serialization": "typed_length_prefixed_v1",
    }
