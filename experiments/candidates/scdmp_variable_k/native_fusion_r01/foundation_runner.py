"""Inspection-only S2 runner that cannot launch foundation activity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, NoReturn

from .foundation_activity_contract import prospective_counts


class ActivityBlocked(PermissionError):
    pass


@dataclass(frozen=True)
class PreactivityInspection:
    schema: str
    roster_count: int
    updates_per_foundation: int
    total_foundation_episodes: int
    total_foundation_steps: int
    lifecycle_schema: str
    evidence_schema: str
    registered_identity_present: bool
    activity_authorized: bool
    effect_refs: tuple[object, ...]


class FoundationPreactivityRunner:
    def inspect(self) -> PreactivityInspection:
        counts = prospective_counts()
        return PreactivityInspection(
            schema="SCDMP_NATIVE_FUSION_R01_S2_PREACTIVITY_INSPECTION_V1",
            roster_count=counts.replicates,
            updates_per_foundation=counts.updates_per_foundation,
            total_foundation_episodes=counts.total_foundation_episodes,
            total_foundation_steps=counts.total_foundation_steps,
            lifecycle_schema="SCDMP_NATIVE_FUSION_R01_S2_LIFECYCLE_V1",
            evidence_schema="SCDMP_NATIVE_FUSION_R01_S2_EVIDENCE_V1",
            registered_identity_present=False,
            activity_authorized=False,
            effect_refs=(),
        )

    def attempt_activity(
        self,
        *,
        command: tuple[str, ...],
        registered_identity_present: bool,
        activity_authorized: bool,
        immutable_run_manifest_ref: Mapping[str, str] | None,
    ) -> NoReturn:
        if registered_identity_present:
            raise ActivityBlocked("registered identity is forbidden in S2")
        if activity_authorized:
            raise ActivityBlocked("activity flag is forbidden in S2")
        if command and immutable_run_manifest_ref is None:
            raise ActivityBlocked("command lacks a later immutable run manifest")
        if command or immutable_run_manifest_ref is not None:
            raise ActivityBlocked("S2 cannot accept a run manifest or activity command")
        raise ActivityBlocked("S2 runner is inspection-only")
