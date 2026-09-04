"""Length-prefixed HMAC addressing for the fresh VNFC R02 RNG domains."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import itertools
from typing import Callable, Iterable, Mapping, Sequence, TypeVar

from .contract import (
    A0_OBJECT,
    A0_SEED,
    ContractViolation,
    REVISION,
    RNG_RECORD_TAG,
    TOKEN_ROLES,
    UINT256_LIMIT,
)


T = TypeVar("T")
Field = tuple[str, str | int]
DigestCallable = Callable[[bytes, bytes], bytes]


def _text(value: str | int) -> str:
    if isinstance(value, bool):
        raise ContractViolation("booleans are not R02 record integers")
    if isinstance(value, int):
        if value < 0:
            raise ContractViolation("R02 record integers must be unsigned")
        return str(value)
    if not isinstance(value, str):
        raise ContractViolation("R02 record fields must be strings or unsigned integers")
    return value


def lp(value: str | int) -> bytes:
    """Return ``uint32_be(len(UTF8(x))) || UTF8(x)`` exactly."""

    raw = _text(value).encode("utf-8")
    if len(raw) >= 1 << 32:
        raise ContractViolation("length-prefixed value exceeds uint32")
    return len(raw).to_bytes(4, "big") + raw


def record_message(fields: Sequence[Field]) -> bytes:
    """Serialize a keyed record without reordering its declared fields."""

    out = bytearray(lp(RNG_RECORD_TAG))
    seen: set[str] = set()
    for name, value in fields:
        if not isinstance(name, str) or not name or name in seen:
            raise ContractViolation("record field names must be nonempty and unique")
        seen.add(name)
        out.extend(lp(name))
        out.extend(lp(value))
    return bytes(out)


def a0_master() -> bytes:
    payload = f"{A0_OBJECT}\0seed={A0_SEED}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def future_master(phase: str, seed: int) -> bytes:
    if phase not in {"DEBUG", "PRIMARY", "OPTIONAL"}:
        raise ContractViolation("future R02 phase is not declared")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ContractViolation("future R02 seed must be an unsigned integer")
    payload = f"{REVISION}\0phase={phase}\0seed={seed}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def _hmac_sha256(master: bytes, message: bytes) -> bytes:
    return hmac.new(master, message, hashlib.sha256).digest()


@dataclass(frozen=True)
class ActionAddress:
    phase: str
    replicate_role: str
    policy_stream: str
    roster_size: int
    failed_zone: int
    update_or_panel_row: str
    episode_row: int
    physical_time: int
    token_role: str
    draw: int = 0

    def __post_init__(self) -> None:
        if self.phase not in {"A0", "DEBUG", "PRIMARY", "OPTIONAL"}:
            raise ContractViolation("undeclared R02 phase")
        if self.token_role not in TOKEN_ROLES:
            raise ContractViolation("undeclared physical token role")
        for name in ("roster_size", "failed_zone", "episode_row", "physical_time", "draw"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractViolation(f"{name} must be an unsigned integer")
        if self.draw != 0:
            raise ContractViolation("the frozen physical categorical address has draw=0")
        for name in ("replicate_role", "policy_stream", "update_or_panel_row"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"{name} must be a nonempty string")

    def fields(self) -> tuple[Field, ...]:
        return (
            ("revision", REVISION),
            ("domain", f"r02/{self.phase}/physical-categorical/v1"),
            ("replicate_role", self.replicate_role),
            ("policy_stream", self.policy_stream),
            ("roster_size", self.roster_size),
            ("failed_zone", self.failed_zone),
            ("update_or_panel_row", self.update_or_panel_row),
            ("episode_row", self.episode_row),
            ("physical_time", self.physical_time),
            ("token_role", self.token_role),
            ("draw", self.draw),
        )


def action_word(master: bytes, address: ActionAddress) -> int:
    digest = _hmac_sha256(master, record_message(address.fields()))
    return int.from_bytes(digest[:8], "big", signed=False)


def unbiased_index(
    master: bytes,
    fields: Sequence[Field],
    k: int,
    *,
    hmac_digest: DigestCallable = _hmac_sha256,
) -> int:
    """Return an exact rejection-sampled index in ``range(k)``.

    ``hmac_digest`` is an injection seam for bounded unit tests only; production
    callers use the default HMAC-SHA256 callable.
    """

    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ContractViolation("finite-index range must be a positive integer")
    base = record_message(fields)
    threshold = (UINT256_LIMIT // k) * k
    counter = 0
    while True:
        message = base + lp("block") + lp(counter)
        digest = hmac_digest(master, message)
        if not isinstance(digest, bytes) or len(digest) != 32:
            raise ContractViolation("finite-index digest must be exactly 256 bits")
        x = int.from_bytes(digest, "big", signed=False)
        if x < threshold:
            return x % k
        counter += 1
        if counter >= 1 << 32:
            raise ContractViolation("finite-index rejection counter exhausted uint32")


def fisher_yates(
    items: Sequence[T],
    master: bytes,
    fields_for_position: Callable[[int], Sequence[Field]],
    *,
    hmac_digest: DigestCallable = _hmac_sha256,
) -> tuple[T, ...]:
    values = list(items)
    if len(set(values)) != len(values):
        raise ContractViolation("Fisher-Yates labels must be unique")
    for upper in range(len(values) - 1, 0, -1):
        chosen = unbiased_index(
            master,
            fields_for_position(upper),
            upper + 1,
            hmac_digest=hmac_digest,
        )
        values[upper], values[chosen] = values[chosen], values[upper]
    return tuple(values)


def a0_opaque_ranks(
    entities: Sequence[T], roster_size: int, failed_zone: int
) -> dict[T, int]:
    if len(entities) != roster_size + 1:
        raise ContractViolation("opaque order must cover the pre-loss N+1 roster")

    def fields(upper: int) -> tuple[Field, ...]:
        return (
            ("domain", "r02/A0/opaque-order/v1"),
            ("roster_size", roster_size),
            ("failed_zone", failed_zone),
            ("descriptor_family", "PS_B0_CELL"),
            ("episode_row", 0),
            ("membership_epoch", 0),
            ("fisher_position", upper),
        )

    order = fisher_yates(entities, a0_master(), fields)
    return {entity: index + 1 for index, entity in enumerate(order)}


def a0_presentations(
    entities_by_opaque_rank: Sequence[T], roster_size: int, failed_zone: int
) -> dict[str, tuple[T, ...]]:
    canonical = tuple(entities_by_opaque_rank)
    if len(canonical) != roster_size or len(set(canonical)) != roster_size:
        raise ContractViolation("active canonical presentation must contain N unique entities")
    reverse = tuple(reversed(canonical))
    cyclic = canonical[1:] + canonical[:1] if canonical else canonical
    excluded = {canonical, reverse, cyclic}
    remaining = tuple(sorted((p for p in itertools.permutations(canonical) if p not in excluded), key=lambda p: tuple(canonical.index(x) + 1 for x in p)))
    if not remaining:
        raise ContractViolation("no permitted seed-fixed-random presentation remains")
    fields: tuple[Field, ...] = (
        ("domain", "r02/A0/external-presentation/v1"),
        ("roster_size", roster_size),
        ("failed_zone", failed_zone),
        ("descriptor_family", "PS_B0_CELL"),
        ("presentation_slot", "seed_fixed_random"),
        ("permitted_permutation_count", len(remaining)),
    )
    selected = remaining[unbiased_index(a0_master(), fields, len(remaining))]
    return {
        "canonical": canonical,
        "reverse": reverse,
        "cyclic": cyclic,
        "seed_fixed_random": selected,
    }

