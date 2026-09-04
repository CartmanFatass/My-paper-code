"""Schema-only prerequisite lifecycle for TBCC r02 construction fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Final, Iterable


class LifecycleError(ValueError):
    pass


FOUNDATION_REPLICATES: Final[frozenset[int]] = frozenset(range(24))
ADAPTER_ARMS: Final[tuple[str, ...]] = ("TREAT", "FREE", "SET")
ADAPTER_SLOTS: Final[frozenset[tuple[int, str]]] = frozenset(
    (replicate, arm) for replicate in range(24) for arm in ADAPTER_ARMS
)


class GateOutcome(str, Enum):
    PASS = "PASS"
    NONPASS = "NONPASS"


class Applicability(str, Enum):
    UNOPENED = "UNOPENED"
    ELIGIBLE = "ELIGIBLE"
    INAPPLICABLE = "INAPPLICABLE"


class PredicateState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class RouteState(str, Enum):
    PASS = "PASS"
    EXCLUDED = "EXCLUDED"
    UNRESOLVED = "UNRESOLVED"


class InferenceBranch(str, Enum):
    INVALID_EVIDENCE = "INVALID-EVIDENCE"
    FOUNDATION_NOT_ESTABLISHED = "COMMON-CONTROLLER-COMPETENCE-NOT-ESTABLISHED"
    OPPORTUNITY_NOT_ESTABLISHED = "TARGET-ORDER-OPPORTUNITY-NOT-ESTABLISHED"
    RETAIN = "RETAIN-ORDERED-SUPPORT-GRAPH-SLACK"
    DECLINE = "DECLINE-ORDERED-SUPPORT-GRAPH-SLACK"
    NONIDENTIFIED = "DIRECT-TARGET-BOUND-ORDER-VALUE-NONIDENTIFIED"


@dataclass(frozen=True)
class InferenceFixture:
    """Pure branch-map inputs; contains no estimates, intervals, or result data."""

    conformance_valid: bool
    foundation_stage_complete: bool
    foundation_gate: GateOutcome | None
    opportunity_stage_complete: bool = False
    opportunity_gate: GateOutcome | None = None
    final_stage_complete: bool = False
    free_competence: PredicateState | None = None
    set_competence: PredicateState | None = None
    v_route: RouteState | None = None
    w_route: RouteState | None = None


def exhaustive_first_true_branch(fixture: InferenceFixture) -> InferenceBranch:
    """Apply the exact prospective branch precedence without opening a stage."""

    # Branch 1: only stages required by the realized prerequisite path count.
    if not fixture.conformance_valid or not fixture.foundation_stage_complete or fixture.foundation_gate is None:
        return InferenceBranch.INVALID_EVIDENCE
    # Branch 2: later stages are prospectively forbidden and thus inapplicable.
    if fixture.foundation_gate is GateOutcome.NONPASS:
        return InferenceBranch.FOUNDATION_NOT_ESTABLISHED
    if not fixture.opportunity_stage_complete or fixture.opportunity_gate is None:
        return InferenceBranch.INVALID_EVIDENCE
    # Branch 3: adapter/final stages are prospectively forbidden and inapplicable.
    if fixture.opportunity_gate is GateOutcome.NONPASS:
        return InferenceBranch.OPPORTUNITY_NOT_ESTABLISHED
    final_fields = (
        fixture.free_competence,
        fixture.set_competence,
        fixture.v_route,
        fixture.w_route,
    )
    if not fixture.final_stage_complete or any(value is None for value in final_fields):
        return InferenceBranch.INVALID_EVIDENCE
    # Branch 4 precedes every negative/nonidentified final disposition.
    if fixture.v_route is RouteState.PASS or fixture.w_route is RouteState.PASS:
        return InferenceBranch.RETAIN
    # Branch 5 requires both registered containing controls to be competent.
    if (
        fixture.free_competence is PredicateState.PASS
        and fixture.set_competence is PredicateState.PASS
        and fixture.v_route is RouteState.EXCLUDED
        and fixture.w_route is RouteState.EXCLUDED
    ):
        return InferenceBranch.DECLINE
    return InferenceBranch.NONIDENTIFIED


@dataclass(frozen=True)
class TechnicalFinal:
    replicate: int
    arm: str
    fake_digest: str
    technically_accepted: bool = True
    test_only: bool = True

    def validate(self, *, foundation: bool) -> None:
        expected = "FOUNDATION" if foundation else self.arm
        if foundation:
            if self.replicate not in FOUNDATION_REPLICATES or self.arm != expected:
                raise LifecycleError("foundation final slot differs")
        elif (self.replicate, self.arm) not in ADAPTER_SLOTS:
            raise LifecycleError("adapter final slot differs")
        if not self.fake_digest.startswith("TEST_ONLY_FAKE_SHA256:"):
            raise LifecycleError("lifecycle digest must be explicitly TEST-only")
        if self.technically_accepted is not True or self.test_only is not True:
            raise LifecycleError("only accepted TEST fixture finals are visible")


@dataclass(frozen=True)
class LifecycleSnapshot:
    foundation_finals: tuple[TechnicalFinal, ...] = ()
    foundation_gate: GateOutcome | None = None
    opportunity_gate: GateOutcome | None = None
    adapter_finals: tuple[TechnicalFinal, ...] = ()

    def validate(self) -> None:
        foundation_slots: list[int] = []
        for item in self.foundation_finals:
            item.validate(foundation=True)
            foundation_slots.append(item.replicate)
        if len(foundation_slots) != len(set(foundation_slots)):
            raise LifecycleError("foundation final slots are duplicated")
        if self.foundation_gate is not None and set(foundation_slots) != FOUNDATION_REPLICATES:
            raise LifecycleError("foundation gate requires all 24 accepted finals")
        if self.opportunity_gate is not None and self.foundation_gate is not GateOutcome.PASS:
            raise LifecycleError("opportunity gate requires a passing foundation gate")
        adapter_slots: list[tuple[int, str]] = []
        for item in self.adapter_finals:
            item.validate(foundation=False)
            adapter_slots.append((item.replicate, item.arm))
        if len(adapter_slots) != len(set(adapter_slots)):
            raise LifecycleError("adapter final slots are duplicated")
        if adapter_slots and not self.adapter_eligible:
            raise LifecycleError("adapter finals exist before both prerequisites pass")

    @property
    def opportunity_applicability(self) -> Applicability:
        if self.foundation_gate is GateOutcome.NONPASS:
            return Applicability.INAPPLICABLE
        if self.foundation_gate is GateOutcome.PASS:
            return Applicability.ELIGIBLE
        return Applicability.UNOPENED

    @property
    def adapter_applicability(self) -> Applicability:
        if self.foundation_gate is GateOutcome.NONPASS or self.opportunity_gate is GateOutcome.NONPASS:
            return Applicability.INAPPLICABLE
        if self.foundation_gate is GateOutcome.PASS and self.opportunity_gate is GateOutcome.PASS:
            return Applicability.ELIGIBLE
        return Applicability.UNOPENED

    @property
    def adapter_eligible(self) -> bool:
        return self.adapter_applicability is Applicability.ELIGIBLE

    @property
    def final_applicability(self) -> Applicability:
        if self.adapter_applicability is Applicability.INAPPLICABLE:
            return Applicability.INAPPLICABLE
        if self.adapter_applicability is Applicability.ELIGIBLE and {
            (item.replicate, item.arm) for item in self.adapter_finals
        } == ADAPTER_SLOTS:
            return Applicability.ELIGIBLE
        return Applicability.UNOPENED

    def require_atomic_final_eligibility(self) -> None:
        self.validate()
        slots = {(item.replicate, item.arm) for item in self.adapter_finals}
        if len(self.adapter_finals) != 72 or slots != ADAPTER_SLOTS:
            raise LifecycleError("atomic final eligibility requires exactly 72 accepted adapter finals")
        if self.final_applicability is not Applicability.ELIGIBLE:
            raise LifecycleError("final stage is not eligible")


def snapshot(
    foundation_finals: Iterable[TechnicalFinal],
    *,
    foundation_gate: GateOutcome | None = None,
    opportunity_gate: GateOutcome | None = None,
    adapter_finals: Iterable[TechnicalFinal] = (),
) -> LifecycleSnapshot:
    value = LifecycleSnapshot(
        foundation_finals=tuple(foundation_finals),
        foundation_gate=foundation_gate,
        opportunity_gate=opportunity_gate,
        adapter_finals=tuple(adapter_finals),
    )
    value.validate()
    return value


@dataclass(frozen=True, repr=False)
class OpportunityExecutionPermit:
    """Opaque proof that the complete foundation gate passed before Stage 1b."""

    foundation_inventory_digest: str
    foundation_final_count: int
    foundation_gate: str
    opportunity_unopened: bool
    downstream_unopened: bool
    _seal: object | None = None


_OPPORTUNITY_PERMIT_SEAL: Final[object] = object()


def _foundation_inventory_digest(finals: Iterable[TechnicalFinal]) -> str:
    ordered = sorted(tuple(finals), key=lambda value: value.replicate)
    payload = [
        {
            "replicate": value.replicate,
            "arm": value.arm,
            "fake_digest": value.fake_digest,
            "technically_accepted": value.technically_accepted,
            "test_only": value.test_only,
        }
        for value in ordered
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()


def issue_opportunity_execution_permit(value: LifecycleSnapshot) -> OpportunityExecutionPermit:
    """Issue only from 24 accepted finals and an unopened passing gate."""

    value.validate()
    if (
        value.foundation_gate is not GateOutcome.PASS
        or value.opportunity_applicability is not Applicability.ELIGIBLE
        or value.opportunity_gate is not None
        or value.adapter_finals
    ):
        raise LifecycleError(
            "opportunity permit requires a complete passing foundation and unopened downstream lifecycle"
        )
    if len(value.foundation_finals) != 24:
        raise LifecycleError("opportunity permit requires all 24 accepted foundation finals")
    permit = OpportunityExecutionPermit(
        foundation_inventory_digest=_foundation_inventory_digest(value.foundation_finals),
        foundation_final_count=24,
        foundation_gate=GateOutcome.PASS.value,
        opportunity_unopened=True,
        downstream_unopened=True,
        _seal=_OPPORTUNITY_PERMIT_SEAL,
    )
    validate_opportunity_execution_permit(permit)
    return permit


def validate_opportunity_execution_permit(permit: OpportunityExecutionPermit) -> None:
    if not isinstance(permit, OpportunityExecutionPermit) or permit._seal is not _OPPORTUNITY_PERMIT_SEAL:
        raise LifecycleError("a validated foundation lifecycle permit is required")
    if (
        len(permit.foundation_inventory_digest) != 64
        or permit.foundation_final_count != 24
        or permit.foundation_gate != GateOutcome.PASS.value
        or permit.opportunity_unopened is not True
        or permit.downstream_unopened is not True
    ):
        raise LifecycleError("foundation lifecycle permit binding differs")
    try:
        int(permit.foundation_inventory_digest, 16)
    except ValueError as error:
        raise LifecycleError("foundation lifecycle permit digest differs") from error


def opportunity_execution_permit_digest(permit: OpportunityExecutionPermit) -> str:
    validate_opportunity_execution_permit(permit)
    payload = {
        "foundation_inventory_digest": permit.foundation_inventory_digest,
        "foundation_final_count": permit.foundation_final_count,
        "foundation_gate": permit.foundation_gate,
        "opportunity_unopened": permit.opportunity_unopened,
        "downstream_unopened": permit.downstream_unopened,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
