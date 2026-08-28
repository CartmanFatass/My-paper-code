"""Atomic, identity-free foundation lifecycle fixtures for S2 preactivity."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .foundation_activity_contract import REPLICATES, UPDATES_PER_FOUNDATION


class LifecycleError(ValueError):
    pass


def _require_sha(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise LifecycleError(f"{label} must be a SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise LifecycleError(f"{label} must be a SHA-256") from error


@dataclass(frozen=True)
class AtomicUpdateTransition:
    replicate_index: int
    update_index: int
    immutable_old_state_sha256: str
    step_start: int
    step_end: int
    registered_identity_present: bool = False
    activity_authorized: bool = False


@dataclass(frozen=True)
class TechnicalFoundationSlot:
    replicate_index: int
    completed_updates: int
    persistent_step_index: int
    technical_state_sha256: str
    materialized: bool = False
    eligible: bool = False
    technically_accepted: bool = False


@dataclass(frozen=True)
class FoundationLifecycle:
    replicate_index: int
    completed_updates: int
    persistent_step_index: int
    technical_state_sha256: str
    registered_identity_present: bool
    activity_authorized: bool

    @classmethod
    def initial(
        cls, replicate_index: int, *, technical_state_sha256: str
    ) -> "FoundationLifecycle":
        if (
            isinstance(replicate_index, bool)
            or not isinstance(replicate_index, int)
            or not 0 <= replicate_index < REPLICATES
        ):
            raise LifecycleError("replicate_index must be in [0,24)")
        _require_sha(technical_state_sha256, "technical_state_sha256")
        return cls(replicate_index, 0, 0, technical_state_sha256, False, False)

    def begin_update(self, *, observed_old_state_sha256: str) -> AtomicUpdateTransition:
        if self.completed_updates >= UPDATES_PER_FOUNDATION:
            raise LifecycleError("all 192 prospective updates are already represented")
        if observed_old_state_sha256 != self.technical_state_sha256:
            raise LifecycleError("immutable old-state boundary differs")
        next_update = self.completed_updates + 1
        step_start = self.persistent_step_index + 1
        return AtomicUpdateTransition(
            replicate_index=self.replicate_index,
            update_index=next_update,
            immutable_old_state_sha256=self.technical_state_sha256,
            step_start=step_start,
            step_end=step_start + 15,
        )

    def accept_update(
        self,
        transition: AtomicUpdateTransition,
        *,
        observed_old_state_sha256: str,
        technical_state_sha256: str,
    ) -> "FoundationLifecycle":
        _require_sha(technical_state_sha256, "technical_state_sha256")
        expected_update = self.completed_updates + 1
        if transition.replicate_index != self.replicate_index or transition.update_index != expected_update:
            raise LifecycleError("transition is not the next atomic update")
        if (
            observed_old_state_sha256 != self.technical_state_sha256
            or transition.immutable_old_state_sha256 != self.technical_state_sha256
        ):
            raise LifecycleError("immutable old-state boundary differs")
        if (
            transition.step_start != self.persistent_step_index + 1
            or transition.step_end != self.persistent_step_index + 16
        ):
            raise LifecycleError("persistent step range is not contiguous")
        if transition.registered_identity_present or transition.activity_authorized:
            raise LifecycleError("S2 transition contains forbidden activity state")
        return FoundationLifecycle(
            replicate_index=self.replicate_index,
            completed_updates=expected_update,
            persistent_step_index=transition.step_end,
            technical_state_sha256=technical_state_sha256,
            registered_identity_present=False,
            activity_authorized=False,
        )

    def snapshot(self) -> dict[str, object]:
        return asdict(self)

    def technical_slot(self) -> TechnicalFoundationSlot:
        if self.completed_updates != UPDATES_PER_FOUNDATION:
            raise LifecycleError("technical slot requires all 192 update transitions")
        return TechnicalFoundationSlot(
            replicate_index=self.replicate_index,
            completed_updates=self.completed_updates,
            persistent_step_index=self.persistent_step_index,
            technical_state_sha256=self.technical_state_sha256,
        )


def cold_resume(value: Mapping[str, object]) -> FoundationLifecycle:
    expected = {
        "replicate_index",
        "completed_updates",
        "persistent_step_index",
        "technical_state_sha256",
        "registered_identity_present",
        "activity_authorized",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise LifecycleError("cold-resume snapshot fields differ")
    lifecycle = FoundationLifecycle(**dict(value))
    if lifecycle.registered_identity_present or lifecycle.activity_authorized:
        raise LifecycleError("cold-resume snapshot contains forbidden activity state")
    if lifecycle.persistent_step_index != lifecycle.completed_updates * 16:
        raise LifecycleError("cold resume would repeat or skip a persistent index")
    if not 0 <= lifecycle.completed_updates <= UPDATES_PER_FOUNDATION:
        raise LifecycleError("cold-resume update count is outside the frozen budget")
    _require_sha(lifecycle.technical_state_sha256, "technical_state_sha256")
    return lifecycle
