"""Counter-addressed randomness for the frozen CBSC-OMRC-B01 object.

The functions in this module are deliberately stateless.  Every random value
is a pure function of its complete address, and no address contains an arm or
evaluation-checkpoint identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Callable, Iterable, Sequence, TypeVar


OBJECT_ID = "CBSC-OMRC-B01"

B0_RUN = "CBSC-OMRC-B0-INSTRUMENT"
B1_RUN = "CBSC-OMRC-B1-THREE-SEED-SCOUT"
B2_RUN = "CBSC-OMRC-B2-TWO-SEED-STABILITY"
RUN_NAMES = frozenset({B0_RUN, B1_RUN, B2_RUN})

TRAIN = "TRAIN"
EVAL_STOCHASTIC = "EVAL_STOCHASTIC"
EVAL_MOTIF = "EVAL_MOTIF"
SPLITS = frozenset({TRAIN, EVAL_STOCHASTIC, EVAL_MOTIF})

INITIAL_DRAW_LABELS = (
    "OWNER_PERM",
    "EPOCH_PERM",
    "NEED_0",
    "NEED_1",
    "CAPABILITY_0",
    "CAPABILITY_1",
    "BODY_0_ADDRESS",
    "BODY_0_CARRIER",
    "BODY_0_ROLE",
    "BODY_1_ADDRESS",
    "BODY_1_CARRIER",
    "BODY_1_ROLE",
)

OPPORTUNITY_DRAW_LABELS = (
    "EVENT_PERM",
    "OWNER_OCCURS",
    "OWNER_SUBJECT",
    "SEMANTIC_OCCURS",
    "SEMANTIC_SUBJECT",
    "SEMANTIC_NEW_NEED",
    "CAPABILITY_OCCURS",
    "CAPABILITY_CARRIER",
    "CAPABILITY_RECEIVER",
    "BODY_OCCURS",
    "BODY_SLOT",
    "BODY_ADDRESS",
    "BODY_CARRIER",
    "BODY_ROLE",
    "DECISION_SLOT",
    "DECISION_TARGET_MATCH",
    "DECISION_GATED",
    "DECISION_ACTIVE",
)

AddressAtom = str | int
Address = tuple[AddressAtom, ...]
T = TypeVar("T")


class AddressValidationError(ValueError):
    """Raised when a counter address is not one of the frozen forms."""


def _integer(name: str, value: object, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AddressValidationError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise AddressValidationError(f"{name} must be >= {minimum}")
    return value


def _string(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise AddressValidationError(f"{name} must be a nonempty string")
    return value


def canonical_json(address: Sequence[AddressAtom]) -> bytes:
    """Return the exact canonical UTF-8 JSON representation of an address."""

    if isinstance(address, (str, bytes)) or not isinstance(address, Sequence):
        raise AddressValidationError("address must be a sequence")
    values = tuple(address)
    if any(isinstance(item, bool) or not isinstance(item, (str, int)) for item in values):
        raise AddressValidationError("addresses contain strings and integers only")
    return json.dumps(
        list(values), ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(address: Sequence[AddressAtom]) -> bytes:
    return hashlib.sha256(canonical_json(address)).digest()


def u64(address: Sequence[AddressAtom]) -> int:
    return int.from_bytes(digest(address)[:8], byteorder="big", signed=False)


def uniform(address: Sequence[AddressAtom]) -> Fraction:
    """Return exact ``(u64 + 0.5) / 2**64`` without binary64 rounding."""

    return Fraction(2 * u64(address) + 1, 1 << 65)


def env_address(
    run_name: str,
    seed: int,
    split: str,
    episode_id: int,
    opportunity_id: int,
    family: str,
    draw_label: str,
    draw_index: int = 0,
    retry: int = 0,
) -> Address:
    if run_name not in RUN_NAMES:
        raise AddressValidationError("unknown run_name")
    if split not in SPLITS:
        raise AddressValidationError("unknown split")
    _integer("seed", seed)
    _integer("episode_id", episode_id, minimum=0)
    _integer("opportunity_id", opportunity_id)
    if opportunity_id < -1 or opportunity_id > 23:
        raise AddressValidationError("opportunity_id must be -1 or in [0, 23]")
    _string("family", family)
    _string("draw_label", draw_label)
    _integer("draw_index", draw_index, minimum=0)
    _integer("retry", retry, minimum=0)
    return (
        OBJECT_ID,
        "ENV",
        run_name,
        seed,
        split,
        episode_id,
        opportunity_id,
        family,
        draw_label,
        draw_index,
        retry,
    )


def action_address(
    run_name: str, seed: int, episode_id: int, opportunity_id: int
) -> Address:
    if run_name not in RUN_NAMES:
        raise AddressValidationError("unknown run_name")
    _integer("seed", seed)
    _integer("episode_id", episode_id, minimum=0)
    _integer("opportunity_id", opportunity_id, minimum=0)
    if opportunity_id > 23:
        raise AddressValidationError("opportunity_id must be in [0, 23]")
    return (
        OBJECT_ID,
        "ACTION",
        run_name,
        seed,
        TRAIN,
        episode_id,
        opportunity_id,
    )


def parameter_address(seed: int, logical_parameter_name: str, flat_index: int) -> Address:
    _integer("seed", seed)
    _string("logical_parameter_name", logical_parameter_name)
    _integer("row_major_flat_index", flat_index, minimum=0)
    return (OBJECT_ID, "PARAM", seed, logical_parameter_name, flat_index)


def order_address(
    run_name: str,
    seed: int,
    rollout_update: int,
    ppo_epoch: int,
    fisher_yates_position: int,
    retry: int = 0,
) -> Address:
    if run_name not in RUN_NAMES:
        raise AddressValidationError("unknown run_name")
    _integer("seed", seed)
    _integer("rollout_update", rollout_update, minimum=0)
    _integer("ppo_epoch", ppo_epoch, minimum=0)
    _integer("fisher_yates_position", fisher_yates_position, minimum=0)
    _integer("retry", retry, minimum=0)
    return (
        OBJECT_ID,
        "ORDER",
        run_name,
        seed,
        rollout_update,
        ppo_epoch,
        fisher_yates_position,
        retry,
    )


def unbiased_integer(n: int, address_for_retry: Callable[[int], Address]) -> int:
    """Draw uniformly from ``range(n)`` by literal 64-bit rejection sampling."""

    _integer("n", n, minimum=1)
    limit = ((1 << 64) // n) * n
    retry = 0
    while True:
        value = u64(address_for_retry(retry))
        if value < limit:
            return value % n
        retry += 1


def fisher_yates(
    values: Sequence[T], address_for_position_retry: Callable[[int, int], Address]
) -> tuple[T, ...]:
    """Return the descending, unbiased Fisher-Yates permutation."""

    result = list(values)
    for position in range(len(result) - 1, 0, -1):
        selected = unbiased_integer(
            position + 1,
            lambda retry, position=position: address_for_position_retry(position, retry),
        )
        result[position], result[selected] = result[selected], result[position]
    return tuple(result)


@dataclass(frozen=True)
class DrawRecord:
    address: Address
    value: int


class AuditedCounterPRF:
    """Pure counter PRF with a unique-address audit trail for one tape build."""

    def __init__(self) -> None:
        self._records: dict[Address, int] = {}

    def raw(self, address: Address) -> int:
        value = u64(address)
        previous = self._records.setdefault(address, value)
        if previous != value:  # pragma: no cover - guards impossible digest instability.
            raise AssertionError("counter address changed value")
        return value

    def u(self, address: Address) -> Fraction:
        return Fraction(2 * self.raw(address) + 1, 1 << 65)

    def index(self, n: int, address_for_retry: Callable[[int], Address]) -> int:
        _integer("n", n, minimum=1)
        limit = ((1 << 64) // n) * n
        retry = 0
        while True:
            value = self.raw(address_for_retry(retry))
            if value < limit:
                return value % n
            retry += 1

    def permutation(
        self,
        values: Sequence[T],
        address_for_position_retry: Callable[[int, int], Address],
    ) -> tuple[T, ...]:
        result = list(values)
        for position in range(len(result) - 1, 0, -1):
            selected = self.index(
                position + 1,
                lambda retry, position=position: address_for_position_retry(position, retry),
            )
            result[position], result[selected] = result[selected], result[position]
        return tuple(result)

    @property
    def records(self) -> tuple[DrawRecord, ...]:
        return tuple(DrawRecord(address, value) for address, value in self._records.items())

    @property
    def addresses(self) -> tuple[Address, ...]:
        return tuple(self._records)

    def audit_digest(self) -> str:
        hasher = hashlib.sha256()
        for address, value in self._records.items():
            encoded = canonical_json(address)
            hasher.update(len(encoded).to_bytes(4, "big"))
            hasher.update(encoded)
            hasher.update(value.to_bytes(8, "big"))
        return hasher.hexdigest()


def address_set_digest(addresses: Iterable[Address]) -> str:
    hasher = hashlib.sha256()
    for encoded in sorted(canonical_json(address) for address in addresses):
        hasher.update(len(encoded).to_bytes(4, "big"))
        hasher.update(encoded)
    return hasher.hexdigest()
