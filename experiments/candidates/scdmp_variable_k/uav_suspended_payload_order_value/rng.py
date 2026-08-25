"""Prospective, lease-gated RNG law for the revision-02 empirical panel.

Importing this module cannot create an identity.  A 256-bit master can be
sampled only by :func:`sample_fresh_master` after the exact lease validator has
returned an :class:`~.lease.ActivityPermit`.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Final

from .lease import ActivityPermit


REPLICATES: Final[tuple[int, ...]] = tuple(range(18))
REPLICATE_PREFIX: Final[bytes] = b"SCDMP-UAV-SP-ORDER-VALUE-r02/replicate/"
DOMAIN_LABELS: Final[tuple[str, ...]] = (
    "initialization",
    "training-initial-state",
    "training-setup-event-order",
    "training-disturbances",
    "training-action-uniforms",
    "training-minibatch-order",
    "evaluation-state",
    "evaluation-setup-event-order",
    "evaluation-switch-time",
    "evaluation-disturbances",
    "support-states",
    "support-disturbances",
)
_DOMAIN_SET = frozenset(DOMAIN_LABELS)
_EVALUATION_REGIMES = frozenset(
    ("fixed-4", "fixed-10", "fixed-6", "fixed-14", "6-to-14", "14-to-6")
)
_UINT64_LIMIT: Final[int] = 1 << 64


class RNGContractError(RuntimeError):
    """The prospective identity or address law was not satisfied."""


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def replicate_message(replicate: int) -> bytes:
    if isinstance(replicate, bool) or replicate not in REPLICATES:
        raise ValueError("replicate must be an integer in [0,18)")
    return REPLICATE_PREFIX + replicate.to_bytes(4, "big", signed=False)


def replicate_key(master: bytes, replicate: int) -> bytes:
    if not isinstance(master, bytes) or len(master) != 32:
        raise ValueError("master must be exactly 256 bits")
    return hmac.new(master, replicate_message(replicate), hashlib.sha256).digest()


def domain_key(master: bytes, replicate: int, domain: str) -> bytes:
    if domain not in _DOMAIN_SET:
        raise ValueError(f"unregistered SCDMP UAV r02 RNG domain: {domain!r}")
    encoded = domain.encode("ascii")
    message = b"domain\0" + len(encoded).to_bytes(2, "big") + encoded
    return hmac.new(replicate_key(master, replicate), message, hashlib.sha256).digest()


def _address_bytes(parts: tuple[object, ...]) -> bytes:
    """Unambiguous typed length-prefix serialization for an RNG address."""

    encoded = bytearray(b"SCDMP-UAV-SP-R02-ADDRESS-v1\0")
    for part in parts:
        if isinstance(part, bool):
            tag, payload = b"b", b"1" if part else b"0"
        elif isinstance(part, int):
            tag, payload = b"i", str(part).encode("ascii")
        elif isinstance(part, str):
            tag, payload = b"s", part.encode("utf-8")
        else:
            raise TypeError("RNG address parts must be bool, int, or str")
        encoded.extend(tag)
        encoded.extend(len(payload).to_bytes(4, "big"))
        encoded.extend(payload)
    return bytes(encoded)


@dataclass(frozen=True)
class AddressRNG:
    """Address-stable HMAC generator within one registered domain."""

    key: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.key, bytes) or len(self.key) != 32:
            raise ValueError("address RNG keys must be exactly 256 bits")

    def raw_u64(self, *parts: object, counter: int = 0) -> int:
        if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
            raise ValueError("counter must be a nonnegative integer")
        message = _address_bytes(tuple(parts)) + counter.to_bytes(8, "big")
        return int.from_bytes(hmac.new(self.key, message, hashlib.sha256).digest()[:8], "big")

    def uniform53(self, *parts: object) -> float:
        return (self.raw_u64(*parts) >> 11) * (2.0 ** -53)

    def uint24(self, *parts: object) -> int:
        """Return the address-stable high 24 bits used by action sampling."""

        return self.raw_u64(*parts) >> 40

    def uniform24(self, *parts: object) -> float:
        """A float32-exact value in {0,...,2^24-1}/2^24; never one."""

        return self.uint24(*parts) * (2.0 ** -24)

    def bounded(self, modulus: int, *parts: object) -> int:
        if isinstance(modulus, bool) or not isinstance(modulus, int) or modulus <= 0:
            raise ValueError("modulus must be a positive integer")
        limit = (_UINT64_LIMIT // modulus) * modulus
        counter = 0
        while True:
            value = self.raw_u64(*parts, counter=counter)
            if value < limit:
                return value % modulus
            counter += 1

    def permutation(self, count: int, *parts: object) -> tuple[int, ...]:
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError("permutation count must be positive")
        values = list(range(count))
        for index in range(count - 1, 0, -1):
            other = self.bounded(index + 1, *parts, "fisher-yates", index)
            values[index], values[other] = values[other], values[index]
        return tuple(values)


class EmpiricalRNG:
    """Lease-bound domain access, including the trainer permutation contract."""

    def __init__(self, master: bytes, permit: ActivityPermit) -> None:
        permit.require_active()
        if not isinstance(master, bytes) or len(master) != 32:
            raise ValueError("master must be exactly 256 bits")
        self.__master = master
        self.__permit = permit

    def for_domain(self, replicate: int, domain: str) -> AddressRNG:
        self.__permit.require_active()
        return AddressRNG(domain_key(self.__master, replicate, domain))

    def initialization_uniforms(
        self,
        replicate: int,
        arm: str,
        tensor_group: str,
        shared_across_arms: bool,
        count: int,
    ) -> tuple[float, ...]:
        """Row-major initialization variates for the model worker's protocol.

        Base/risk/critic tensors use arm-independent addresses.  FREE and SET
        residual-hidden tensors use disjoint arm-qualified addresses.  Zero
        biases and zero residual output layers must not call this function.
        """

        if not isinstance(shared_across_arms, bool):
            raise TypeError("shared_across_arms must be bool")
        if not tensor_group or isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError("initialization requires a tensor group and positive count")
        if shared_across_arms:
            if arm != "SHARED":
                raise ValueError("shared base/risk/critic initialization must use arm='SHARED'")
            if not tensor_group.startswith(("base.", "risk.", "critic.")):
                raise ValueError("only base/risk/critic tensors use shared initialization addresses")
            address_prefix: tuple[object, ...] = ("shared", "tensor-group", tensor_group)
        else:
            if arm not in ("FREE", "SET") or not tensor_group.startswith("residual."):
                raise ValueError("only FREE/SET residual tensors use arm-disjoint addresses")
            address_prefix = ("residual-arm", arm, "tensor-group", tensor_group)
        stream = self.for_domain(replicate, "initialization")
        return tuple(
            stream.uniform24(*address_prefix, "row-major-flat-index", flat_index)
            for flat_index in range(count)
        )

    def training_initial_state_uniform(
        self, replicate: int, update: int, k: int, slot: int, component: str
    ) -> float:
        if update not in range(1, 145) or k not in (4, 10) or slot not in range(6):
            raise ValueError("training initial-state address is outside the frozen panel")
        if component not in ("v", "phi"):
            raise ValueError("training initial-state component must be v or phi")
        # No arm argument: the exact address is paired across learned arms.
        return self.for_domain(replicate, "training-initial-state").uniform53(
            "update", update, "k", k, "slot", slot, "component", component
        )

    def training_setup_order_roster(
        self, replicate: int, update: int, k: int
    ) -> tuple[str, ...]:
        if update not in range(1, 145) or k not in (4, 10):
            raise ValueError("training setup roster requires update 1..144 and k in {4,10}")
        stream = self.for_domain(replicate, "training-setup-event-order")
        permutation = stream.permutation(6, "update", update, "k", k)
        base = ("RG", "RG", "RG", "GR", "GR", "GR")
        return tuple(base[index] for index in permutation)

    def training_disturbance_bit(
        self, replicate: int, update: int, k: int, slot: int, tick: int, component: str
    ) -> int:
        if update not in range(1, 145) or k not in (4, 10) or slot not in range(6):
            raise ValueError("training disturbance address is outside the frozen panel")
        if tick not in range(420) or component not in ("eta_v", "eta_omega"):
            raise ValueError("training disturbance tick/component is invalid")
        return self.for_domain(replicate, "training-disturbances").bounded(
            2, "update", update, "k", k, "slot", slot, "tick", tick, "component", component
        )

    def training_action_uniform(
        self, replicate: int, update: int, k: int, slot: int, renewal: int
    ) -> float:
        if update not in range(1, 145) or k not in (4, 10) or slot not in range(6):
            raise ValueError("training action address is outside the frozen panel")
        if isinstance(renewal, bool) or not isinstance(renewal, int) or renewal < 0:
            raise ValueError("renewal must be a nonnegative integer")
        # No arm argument: inverse-CDF action variates are paired across arms.
        return self.for_domain(replicate, "training-action-uniforms").uniform24(
            "update", update, "k", k, "slot", slot, "renewal", renewal
        )

    def evaluation_state_uniform(
        self, replicate: int, regime: str, scenario: int, component: str
    ) -> float:
        if regime not in _EVALUATION_REGIMES or scenario not in range(120):
            raise ValueError("evaluation state address is outside the frozen panel")
        if component not in ("v", "phi"):
            raise ValueError("evaluation state component must be v or phi")
        # No controller argument: every exogenous target scenario is shared.
        return self.for_domain(replicate, "evaluation-state").uniform53(
            "regime", regime, "scenario", scenario, "component", component
        )

    def evaluation_order_roster(self, replicate: int, regime: str) -> tuple[str, ...]:
        if regime not in _EVALUATION_REGIMES:
            raise ValueError("evaluation regime is unregistered")
        stream = self.for_domain(replicate, "evaluation-setup-event-order")
        permutation = stream.permutation(120, "regime", regime)
        base = ("RG",) * 60 + ("GR",) * 60
        return tuple(base[index] for index in permutation)

    def evaluation_switch_roster(
        self, replicate: int, regime: str, orders: tuple[str, ...]
    ) -> tuple[int, ...]:
        if regime not in ("6-to-14", "14-to-6") or len(orders) != 120:
            raise ValueError("switch roster requires one registered switch regime and 120 orders")
        if any(order not in ("RG", "GR") for order in orders):
            raise ValueError("switch roster contains an unregistered event order")
        stream = self.for_domain(replicate, "evaluation-switch-time")
        result = [0] * 120
        for order in ("RG", "GR"):
            positions = [index for index, value in enumerate(orders) if value == order]
            if len(positions) != 60:
                raise ValueError("switch roster requires 60 scenarios per order")
            permutation = stream.permutation(60, "regime", regime, "order", order)
            ticks = (168,) * 30 + (252,) * 30
            for position, source_index in zip(positions, permutation):
                result[position] = ticks[source_index]
        return tuple(result)

    def evaluation_disturbance_bit(
        self, replicate: int, regime: str, scenario: int, tick: int, component: str
    ) -> int:
        if regime not in _EVALUATION_REGIMES or scenario not in range(120):
            raise ValueError("evaluation disturbance address is outside the frozen panel")
        if tick not in range(420) or component not in ("eta_v", "eta_omega"):
            raise ValueError("evaluation disturbance tick/component is invalid")
        return self.for_domain(replicate, "evaluation-disturbances").bounded(
            2, "regime", regime, "scenario", scenario, "tick", tick, "component", component
        )

    def support_state_uniform(
        self, replicate: int, k: int, state_index: int, component: str
    ) -> float:
        if k not in (6, 14) or state_index not in range(72) or component not in ("v", "phi"):
            raise ValueError("support state address is outside the frozen panel")
        # No history/action argument: public support state is paired.
        return self.for_domain(replicate, "support-states").uniform53(
            "k", k, "state", state_index, "component", component
        )

    def support_disturbance_bit(
        self, replicate: int, k: int, state_index: int, tick: int, component: str
    ) -> int:
        if k not in (6, 14) or state_index not in range(72) or tick not in range(k):
            raise ValueError("support disturbance address is outside the frozen panel")
        if component not in ("eta_v", "eta_omega"):
            raise ValueError("support disturbance component is invalid")
        # No history/action argument: one tape is shared across both histories/all actions.
        return self.for_domain(replicate, "support-disturbances").bounded(
            2, "k", k, "state", state_index, "tick", tick, "component", component
        )

    def permutation_indices(
        self,
        replicate: int,
        arm: str,
        update: int,
        epoch: int,
        count: int,
    ) -> tuple[int, ...]:
        """Exact injected trainer interface; uses only minibatch-order domain."""

        if arm not in ("TREAT", "FREE", "SET"):
            raise ValueError("arm is not a learned-arm identity")
        if isinstance(update, bool) or update not in range(1, 145):
            raise ValueError("update must be globally one-based in [1,144]")
        if isinstance(epoch, bool) or epoch not in range(1, 5):
            raise ValueError("epoch must be one-based in [1,4]")
        return self.for_domain(replicate, "training-minibatch-order").permutation(
            count, "arm", arm, "update", update, "epoch", epoch
        )


def identity_digest_set(master: bytes) -> frozenset[str]:
    """Digest-only collision registry projection; keys themselves never leave."""

    values = [sha256_hex(master)]
    values.extend(sha256_hex(replicate_key(master, replicate)) for replicate in REPLICATES)
    values.extend(
        sha256_hex(domain_key(master, replicate, domain))
        for replicate in REPLICATES
        for domain in DOMAIN_LABELS
    )
    return frozenset(values)


def domain_separation_proof(master: bytes) -> dict[str, object]:
    """Finite collision witness plus the injective registered encodings."""

    replicate_messages = tuple(replicate_message(replicate) for replicate in REPLICATES)
    domain_digests = tuple(
        sha256_hex(domain_key(master, replicate, domain))
        for replicate in REPLICATES
        for domain in DOMAIN_LABELS
    )
    return {
        "schema": "SCDMP_UAV_SP_R02_HMAC_DOMAIN_PROOF_V1",
        "replicate_namespace": "SCDMP-UAV-SP-ORDER-VALUE-r02/replicate/<uint32_be(s)>",
        "replicate_count": 18,
        "replicate_messages_injective": len(set(replicate_messages)) == 18,
        "domain_labels": DOMAIN_LABELS,
        "domain_labels_disjoint": len(set(DOMAIN_LABELS)) == len(DOMAIN_LABELS),
        "derived_domain_key_digests_unique": len(set(domain_digests)) == len(domain_digests),
        "address_serialization": "typed_length_prefixed_v1",
    }


def sample_fresh_master(
    permit: ActivityPermit,
    *,
    occupied_digests: Iterable[str],
    source: Callable[[int], bytes] = os.urandom,
) -> bytes:
    """Draw exactly once from the OS source after future activity admission."""

    permit.require_active()
    master = source(32)
    if not isinstance(master, bytes) or len(master) != 32:
        raise RNGContractError("operating-system cryptographic RNG returned the wrong byte count")
    occupied = {str(value).lower() for value in occupied_digests}
    generated = identity_digest_set(master)
    if occupied.intersection(generated):
        raise RNGContractError("fresh identity digest collided; no automatic resampling is permitted")
    if len(generated) != 1 + 18 + 18 * len(DOMAIN_LABELS):
        raise RNGContractError("derived identity/domain collision detected")
    return master
