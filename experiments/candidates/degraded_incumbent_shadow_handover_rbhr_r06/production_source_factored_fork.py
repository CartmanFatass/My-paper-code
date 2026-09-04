"""Three-way policy-state fork and causal replay shell; no rollout is run here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Iterable, Mapping, Sequence

import numpy as np

from .production_backend import NativeBatch
from .production_source_factored_contract import FUTURE_TICKS


class SourceFactoredForkError(RuntimeError):
    pass


class PolicyStateMode(str, Enum):
    RETAIN = "RETAIN"
    COPY = "COPY"
    SHADOW = "SHADOW"


TRANSACTION_TO_POLICY_STATE: Final = {
    "RETAIN": PolicyStateMode.RETAIN,
    "TRANSFER_COPY": PolicyStateMode.COPY,
    "TRANSFER_SHADOW": PolicyStateMode.SHADOW,
}


FORBIDDEN_REPLAY_SOURCES: Final = frozenset({
    "future_tape", "evaluator", "critic", "source", "SOURCE", "extra_training",
    "optimizer_update", "extra_optimizer_update", "extra_wire", "post_deadline",
})
ALLOWED_REPLAY_SOURCES: Final = frozenset({"actor_observation", "snapshot", "message"})


def _hidden_array(value: object) -> np.ndarray:
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach().cpu().numpy()
    hidden = np.asarray(value)
    if hidden.shape[-2:] != (4, 128) or hidden.dtype.kind != "f" or not np.isfinite(hidden).all():
        raise SourceFactoredForkError("policy state must have finite 4x128 recurrent semantics")
    return hidden.copy()


def fork_policy_state(hidden: object, owner: Sequence[int], mode: PolicyStateMode | str) -> np.ndarray:
    result = _hidden_array(hidden)
    if result.ndim != 3:
        raise SourceFactoredForkError("policy state batch rank differs")
    owners = np.asarray(owner, dtype=np.int64)
    if owners.shape != (result.shape[0],) or not np.isin(owners, (0, 1)).all():
        raise SourceFactoredForkError("fork owner inventory differs")
    selected = PolicyStateMode(mode)
    if selected is PolicyStateMode.RETAIN:
        return result
    for lane, incumbent in enumerate(owners):
        standby = 1 - int(incumbent)
        incumbent_active = result[lane, 2 * int(incumbent)].copy()
        source = (incumbent_active if selected is PolicyStateMode.COPY
                  else result[lane, 2 * standby + 1].copy())
        promoted = np.clip(source, -1.0, 1.0)
        result[lane, 2 * standby] = promoted
        result[lane, 2 * int(incumbent) + 1] = incumbent_active
    return result


@dataclass(frozen=True)
class ReplayRecord:
    tick: int
    ordinal: int
    source: str
    payload: bytes


@dataclass(frozen=True)
class CausalReplayWorkShell:
    origin_tick: int
    application_tick: int
    captured_prefix: tuple[ReplayRecord, ...]
    records: tuple[ReplayRecord, ...]
    completion_tick: int
    optimizer_updates: int = 0
    extra_wire_bytes: int = 0

    def validate(self) -> None:
        if self.origin_tick < 0 or self.application_tick != self.origin_tick + 1:
            raise SourceFactoredForkError("replay deadline differs from t*")
        if not self.captured_prefix or self.records != self.captured_prefix:
            raise SourceFactoredForkError("replay work differs from captured causal prefix")
        if not self.origin_tick <= self.completion_tick <= self.application_tick:
            raise SourceFactoredForkError("replay completion misses the application boundary")
        if self.optimizer_updates or self.extra_wire_bytes:
            raise SourceFactoredForkError("replay acquired forbidden work or wire")
        order = [(row.tick, row.ordinal) for row in self.records]
        if order != sorted(order) or len(set(order)) != len(order):
            raise SourceFactoredForkError("replay prefix is not ordered causal information")
        for row in self.records:
            if type(row) is not ReplayRecord or row.tick < 0 or row.ordinal < 0:
                raise SourceFactoredForkError("replay record type or coordinate differs")
            if row.source in FORBIDDEN_REPLAY_SOURCES or row.source not in ALLOWED_REPLAY_SOURCES:
                raise SourceFactoredForkError("replay source is forbidden")
            if row.tick > self.origin_tick or type(row.payload) is not bytes or not row.payload:
                raise SourceFactoredForkError("replay accesses future or empty information")

    @property
    def ordered_work(self) -> tuple[tuple[int, int, str, bytes], ...]:
        self.validate()
        return tuple((row.tick, row.ordinal, row.source, bytes(row.payload)) for row in self.records)


@dataclass(frozen=True)
class SourceFactoredForkPlan:
    checkpoint_bytes: bytes
    normalization_bytes: bytes
    rng_frontier_bytes: bytes
    future_addresses: tuple[str, ...]
    future_ticks: int = FUTURE_TICKS
    optimizer_updates: int = 0

    def validate(self) -> None:
        direct = (self.checkpoint_bytes, self.normalization_bytes, self.rng_frontier_bytes)
        if any(not isinstance(value, bytes) or not value for value in direct):
            raise SourceFactoredForkError("fork direct byte inventory differs")
        if self.future_ticks != 100 or self.optimizer_updates != 0:
            raise SourceFactoredForkError("fork horizon or optimizer boundary differs")
        if len(self.future_addresses) != 100 or len(set(self.future_addresses)) != 100:
            raise SourceFactoredForkError("future physical address inventory differs")

    def branch_binding(self) -> Mapping[str, Mapping[str, object]]:
        self.validate()
        common = {
            "checkpoint_bytes": self.checkpoint_bytes,
            "normalization_bytes": self.normalization_bytes,
            "rng_frontier_bytes": self.rng_frontier_bytes,
            "future_addresses": self.future_addresses,
            "future_ticks": 100, "optimizer_updates": 0,
        }
        return {
            branch: dict(common, transaction_branch=branch, policy_state_mode=mode.value)
            for branch, mode in TRANSACTION_TO_POLICY_STATE.items()
        }


def clone_test_only(
    *, native: NativeBatch, step_rows: np.ndarray,
) -> tuple[Mapping[str, NativeBatch], Mapping[str, Mapping[str, np.ndarray]], Mapping[str, object]]:
    return native.clone_promotion_source_batches(step_rows)


def future_address_equality(branches: Mapping[str, Iterable[str]]) -> bool:
    if set(branches) != set(TRANSACTION_TO_POLICY_STATE):
        return False
    rows = [tuple(branches[branch]) for branch in TRANSACTION_TO_POLICY_STATE]
    return len(rows[0]) == 100 and rows[0] == rows[1] == rows[2]


__all__ = [
    "ALLOWED_REPLAY_SOURCES", "CausalReplayWorkShell", "FORBIDDEN_REPLAY_SOURCES",
    "PolicyStateMode", "ReplayRecord", "SourceFactoredForkError", "SourceFactoredForkPlan",
    "TRANSACTION_TO_POLICY_STATE",
    "clone_test_only", "fork_policy_state", "future_address_equality",
]
