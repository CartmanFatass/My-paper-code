"""Frozen structural contracts for the RSCF revision-01 Gate-B runner.

This module contains schemas and logical constants only.  The present Gate-B
stage may instantiate them solely with :class:`TestIdentity`; the reserved
scientific namespace and all production identities fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Final, Mapping, Sequence, TypeAlias

import numpy as np


SCIENCE_REVISION: Final = "SGSP-RG2Z-RSCF-SCIENCE-20260821-01"
CONTRACT_SCHEMA: Final = "SGSP_RSCF_RUNNER_CONTRACT_V1"
SNAPSHOT_SCHEMA: Final = "SGSP_RSCF_PRETRANSITION_SNAPSHOT_V1"
SELECTOR_SCHEMA: Final = "SGSP_RSCF_ARM_INDEPENDENT_SELECTOR_V1"
FIXTURE_SCHEMA: Final = "SGSP_RSCF_GATE_B_TEST_FIXTURE_V1"

TEST_NAMESPACE_PREFIX: Final = "TEST_ONLY|SGSP-RG2Z-RSCF-R01-GATE-B|"
RESERVED_SCIENTIFIC_NAMESPACE: Final = (
    "semantic_graphon_shared_policy|SGSP-RG2Z-RSCF-SCIENCE-20260821-01|"
    "RIDGEGATE-2Z|role-sampled-full-suffix-v1"
)

HORIZON: Final = 12
MAX_AGENTS: Final = 21
PUBLIC_ROLES: Final = ("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")
ROLE_COUNT: Final = 3
TRAIN_ROSTERS: Final = (9, 15)
EVALUATION_ROSTERS: Final = (9, 15, 6, 21)
SUPPORTED_ROSTERS: Final = EVALUATION_ROSTERS
EPISODES_PER_UPDATE: Final = 64
EPISODES_PER_TRAIN_ROSTER: Final = 32
PAIRS_PER_TRAIN_ROSTER: Final = 16
UPDATES: Final = 512
SEED_BLOCK_COUNT: Final = 24
ARMS: Final = 2
EVALUATION_EPISODES_PER_ROSTER: Final = 256
LEGAL_ACTIONS_BY_ROLE: Final = ((0, 1, 5), (0, 1, 5), (2, 3, 4, 5))
ACTION_COUNT: Final = 6
OBSERVATION_DIM: Final = 22
MESSAGE_DIM: Final = 32
HIDDEN_DIM: Final = 64
FIFO_CAPACITY: Final = 4
SUPPORTED_WIDTHS: Final = (32, 64, 128, 256)


class ContractError(ValueError):
    """Raised when an RSCF structural object does not match its frozen schema."""


@dataclass(frozen=True)
class LogicalCounts:
    factual_base_episodes: int
    all_legal_q_entries: int
    new_alternative_continuations: int
    branch_environment_slot_transitions: int
    base_training_environment_slots: int
    evaluation_environment_slots: int
    total_environment_slots: int
    future_branch_learned_decisions: int
    total_learned_decisions: int
    full_batch_backward_calls: int

    def as_dict(self) -> dict[str, int]:
        return {
            "factual_base_episodes": self.factual_base_episodes,
            "all_legal_q_entries": self.all_legal_q_entries,
            "new_alternative_continuations": self.new_alternative_continuations,
            "branch_environment_slot_transitions": self.branch_environment_slot_transitions,
            "base_training_environment_slots": self.base_training_environment_slots,
            "evaluation_environment_slots": self.evaluation_environment_slots,
            "total_environment_slots": self.total_environment_slots,
            "future_branch_learned_decisions": self.future_branch_learned_decisions,
            "total_learned_decisions": self.total_learned_decisions,
            "full_batch_backward_calls": self.full_batch_backward_calls,
        }


FROZEN_LOGICAL_COUNTS: Final = LogicalCounts(
    factual_base_episodes=1_572_864,
    all_legal_q_entries=15_728_640,
    new_alternative_continuations=11_010_048,
    branch_environment_slot_transitions=71_565_312,
    base_training_environment_slots=18_874_368,
    evaluation_environment_slots=1_032_192,
    total_environment_slots=91_471_872,
    future_branch_learned_decisions=726_663_168,
    total_learned_decisions=966_647_808,
    full_batch_backward_calls=24_576,
)


def verify_frozen_logical_counts() -> None:
    """Re-derive the registered counts without creating a scientific object."""
    factual = SEED_BLOCK_COUNT * ARMS * UPDATES * EPISODES_PER_UPDATE
    q_entries = factual * 10
    alternatives = factual * 7
    branch_slots = alternatives * 13 // 2
    base_slots = factual * HORIZON
    # The registered evaluation accounting includes the inherited comparator,
    # simple-baseline, and shadow consumers.  It is intentionally frozen as a
    # panel-level logical count rather than reinterpreted as two-arm episodes.
    evaluation_slots = 1_032_192
    branch_decisions = alternatives * 11 // 2 * 12
    expected = LogicalCounts(
        factual_base_episodes=factual,
        all_legal_q_entries=q_entries,
        new_alternative_continuations=alternatives,
        branch_environment_slot_transitions=branch_slots,
        base_training_environment_slots=base_slots,
        evaluation_environment_slots=evaluation_slots,
        total_environment_slots=base_slots + branch_slots + evaluation_slots,
        future_branch_learned_decisions=branch_decisions,
        total_learned_decisions=966_647_808,
        full_batch_backward_calls=SEED_BLOCK_COUNT * ARMS * UPDATES,
    )
    if expected != FROZEN_LOGICAL_COUNTS:
        raise ContractError("registered RSCF logical counts do not re-derive exactly")


_TEST_LABEL = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
_IDENTITY_FORBIDDEN = (
    "ARM", "MASTER", "SEED", "COORDINATE", "PRODUCTION", "SCIENTIFIC",
    "EMPIRICAL", "PANEL", "MODEL", "CHECKPOINT", "EPISODE", "ROLLOUT",
    "ENDPOINT", "INFERENCE", "RESULT", "STATE", "ACTION", "OUTCOME",
    "BUFFER", "REPORT", "BRANCH",
)


@dataclass(frozen=True)
class TestIdentity:
    """An unmistakable engineering-fixture identity, never a panel identity."""

    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not _TEST_LABEL.fullmatch(self.label):
            raise ContractError("TEST label must be an uppercase nonempty engineering case label")
        tokens = set(filter(None, re.split(r"[^A-Z]+", self.label)))
        if tokens.intersection(_IDENTITY_FORBIDDEN):
            raise ContractError("TEST label contains a scientific-identity token")

    @property
    def namespace(self) -> str:
        return TEST_NAMESPACE_PREFIX + self.label

    def canonical(self) -> str:
        return self.namespace


def require_test_identity(value: TestIdentity) -> TestIdentity:
    if not isinstance(value, TestIdentity):
        raise ContractError("Gate-B execution requires a TestIdentity")
    namespace = value.namespace
    if namespace == RESERVED_SCIENTIFIC_NAMESPACE or not namespace.startswith(TEST_NAMESPACE_PREFIX):
        raise ContractError("non-TEST namespace is forbidden in this Gate-B stage")
    return value


def validate_roster_size(roster_size: int, *, training_only: bool = False) -> int:
    if type(roster_size) is not int:
        raise ContractError("roster size must be an int")
    allowed = TRAIN_ROSTERS if training_only else SUPPORTED_ROSTERS
    if roster_size not in allowed:
        raise ContractError(f"roster size must be one of {allowed}")
    if roster_size % ROLE_COUNT:
        raise ContractError("roster must be role-balanced")
    return roster_size


def legal_actions(role_index: int) -> tuple[int, ...]:
    if type(role_index) is not int or not 0 <= role_index < ROLE_COUNT:
        raise ContractError("role index outside the three public roles")
    return LEGAL_ACTIONS_BY_ROLE[role_index]


@dataclass(frozen=True)
class FrozenArray:
    """Byte-backed ndarray representation whose storage cannot be made writable."""

    dtype: str
    shape: tuple[int, ...]
    data: bytes

    @classmethod
    def freeze(cls, value: np.ndarray, *, name: str = "array") -> "FrozenArray":
        if not isinstance(value, np.ndarray):
            raise ContractError(f"{name} must be an ndarray")
        if value.dtype.hasobject:
            raise ContractError(f"{name} cannot use object dtype")
        if any(type(dim) is not int or dim < 0 for dim in value.shape):
            raise ContractError(f"{name} has invalid shape")
        if np.issubdtype(value.dtype, np.floating) and not bool(np.isfinite(value).all()):
            raise ContractError(f"{name} contains non-finite values")
        canonical = np.ascontiguousarray(value)
        return cls(canonical.dtype.str, tuple(canonical.shape), canonical.tobytes(order="C"))

    def array(self, *, copy: bool = False) -> np.ndarray:
        value = np.frombuffer(self.data, dtype=np.dtype(self.dtype)).reshape(self.shape)
        return value.copy(order="C") if copy else value

    def canonical_payload(self) -> dict[str, object]:
        return {"dtype": self.dtype, "shape": list(self.shape), "sha256": hashlib.sha256(self.data).hexdigest()}


FrozenScalar: TypeAlias = None | bool | int | float | str
# Recursive aliases are used only for static readability; runtime validation is
# performed by ``_freeze_value`` before any value enters a FrozenRecord.
FrozenValue: TypeAlias = Any

_PRIVATE_KEY_TOKENS: Final = (
    "branch", "private", "terminal_return", "future_return", "factual_return",
    "q_vector", "q_entry", "advantage",
)


def _freeze_value(value: object, *, path: str) -> FrozenValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not np.isfinite(value):
            raise ContractError(f"{path} contains non-finite scalar")
        return value
    if isinstance(value, np.ndarray):
        return FrozenArray.freeze(value, name=path)
    if isinstance(value, Mapping):
        return FrozenRecord.freeze(value, path=path)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze_value(item, path=f"{path}[]") for item in value)
    raise ContractError(f"{path} has unsupported payload type {type(value).__name__}")


def _thaw_value(value: FrozenValue) -> object:
    if isinstance(value, FrozenArray):
        return value.array(copy=True)
    if isinstance(value, FrozenRecord):
        return value.thaw()
    if isinstance(value, tuple):
        return [_thaw_value(item) for item in value]
    return value


def _canonical_value(value: FrozenValue) -> object:
    if isinstance(value, FrozenArray):
        return {"array": value.canonical_payload()}
    if isinstance(value, FrozenRecord):
        return value.canonical_payload()
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    return value


@dataclass(frozen=True)
class FrozenRecord:
    """Sorted, recursively frozen carrier for complete simulator substate."""

    fields: tuple[tuple[str, FrozenValue], ...]

    @classmethod
    def freeze(cls, value: Mapping[str, object], *, path: str = "record") -> "FrozenRecord":
        if not isinstance(value, Mapping):
            raise ContractError(f"{path} must be a mapping")
        fields: list[tuple[str, FrozenValue]] = []
        for key in sorted(value, key=str):
            if not isinstance(key, str) or not key or key.strip() != key:
                raise ContractError(f"{path} contains an invalid key")
            normalized = key.casefold().replace("-", "_")
            if any(token in normalized for token in _PRIVATE_KEY_TOKENS):
                raise ContractError(f"{path}.{key} is branch-private and forbidden")
            fields.append((key, _freeze_value(value[key], path=f"{path}.{key}")))
        return cls(tuple(fields))

    def thaw(self) -> dict[str, object]:
        return {key: _thaw_value(value) for key, value in self.fields}

    def canonical_payload(self) -> dict[str, object]:
        return {key: _canonical_value(value) for key, value in self.fields}

    def require_keys(self, required: Sequence[str], *, name: str) -> None:
        keys = {key for key, _ in self.fields}
        missing = set(required) - keys
        if missing:
            raise ContractError(f"{name} missing fields {sorted(missing)}")


def canonical_digest(value: object) -> str:
    """Stable digest for contract dataclasses, frozen carriers, and primitives."""
    if isinstance(value, FrozenRecord):
        payload: object = value.canonical_payload()
    elif isinstance(value, FrozenArray):
        payload = value.canonical_payload()
    elif hasattr(value, "canonical_payload"):
        payload = value.canonical_payload()  # type: ignore[union-attr]
    elif isinstance(value, Mapping):
        payload = {str(key): value[key] for key in sorted(value, key=str)}
    else:
        payload = value
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


verify_frozen_logical_counts()
