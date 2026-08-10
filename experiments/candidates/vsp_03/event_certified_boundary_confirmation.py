"""Pure VSP03-A1 event-certified boundary contract audit.

The registered audit is deliberately source-free at this revision.  It cannot
turn timestamps, roster observations, or a generic debouncer into the missing
target-negative causal event.  Future authenticated sources can be represented
by :class:`EventSourceBinding` and checked against the same frozen tables and
traces without changing the audit semantics.
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
CANDIDATE_ID = "CAND-VSP-03-BCTT"
VERSION_ID = "CAND-VSP-03-BCTT@event-certified-boundary-revision-v4"
TREATMENT_ID = "VSP03-A1-EVENT-CERTIFIED-BOUNDARY-CONFIRMATION"
ARTIFACT_KIND = "VSP03_A1_EVENT_CERTIFIED_BOUNDARY_CONFIRMATION"


class ContractViolation(ValueError):
    """A serialized audit or typed manifest violates the frozen contract."""


class ScopeClass(str, Enum):
    PERSISTENT_OCCUPANCY = "PERSISTENT_OCCUPANCY"
    FIRST_PASSAGE = "FIRST_PASSAGE"
    ABSORBING = "ABSORBING"
    SAFETY_HANDOFF = "SAFETY_HANDOFF"


class Arm(str, Enum):
    EXACT_BOUNDARY_DEBOUNCE = "EXACT_BOUNDARY_DEBOUNCE"
    BCTT_EC = "BCTT_EC"


class TerminalBranch(str, Enum):
    INVALID_EVENT_CAUSALITY_OR_SCOPE = "A1_INVALID_EVENT_CAUSALITY_OR_SCOPE"
    INVALID_PARITY_OR_CAUSE_CONTRACT = "A1_INVALID_PARITY_OR_CAUSE_CONTRACT"
    EXACT_DEBOUNCE_NOT_REPRODUCED = "A1_EXACT_DEBOUNCE_NOT_REPRODUCED"
    BCTT_EC_HOLD_REGRESSION = "A1_BCTT_EC_HOLD_REGRESSION"
    BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE = "A1_BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE"
    LATCH_RESET_OR_REARM_FAILED = "A1_LATCH_RESET_OR_REARM_FAILED"
    EVENT_CERTIFIED_BOUNDARY_DIVERGENCE_SUPPORTED = "A1_EVENT_CERTIFIED_BOUNDARY_DIVERGENCE_SUPPORTED"


BRANCH_PRECEDENCE = tuple(branch.value for branch in TerminalBranch)
BYPASS_SCOPES = (
    ScopeClass.FIRST_PASSAGE,
    ScopeClass.ABSORBING,
    ScopeClass.SAFETY_HANDOFF,
)


@dataclass(frozen=True, order=True)
class TruthInput:
    armed: bool
    positive: bool
    negative_event_latched: bool

    @property
    def bits(self) -> str:
        return f"{int(self.armed)}{int(self.positive)}{int(self.negative_event_latched)}"


@dataclass(frozen=True)
class LookupOutput:
    exact_boundary_debounce: bool
    bctt_ec: bool

    @property
    def bits(self) -> str:
        return f"{int(self.exact_boundary_debounce)}{int(self.bctt_ec)}"


@dataclass(frozen=True)
class LookupRow:
    inputs: TruthInput
    outputs: LookupOutput


FROZEN_TRUTH_TABLE = (
    LookupRow(TruthInput(False, False, False), LookupOutput(False, False)),
    LookupRow(TruthInput(False, False, True), LookupOutput(False, False)),
    LookupRow(TruthInput(False, True, False), LookupOutput(False, False)),
    LookupRow(TruthInput(False, True, True), LookupOutput(False, False)),
    LookupRow(TruthInput(True, False, False), LookupOutput(False, False)),
    LookupRow(TruthInput(True, False, True), LookupOutput(False, False)),
    LookupRow(TruthInput(True, True, False), LookupOutput(True, True)),
    LookupRow(TruthInput(True, True, True), LookupOutput(True, False)),
)
FROZEN_TRUTH_MAP = {row.inputs: row.outputs for row in FROZEN_TRUTH_TABLE}
INVALID_CAUSAL_ROWS = {"001", "011"}


@dataclass(frozen=True)
class EventSourceBinding:
    source_id: str
    authentication_id: str
    authentication_verified: bool
    primitive_event_name: str
    scope: ScopeClass
    prospectively_declared_before_trace: bool
    target_negative_is_primitive_event: bool
    target_causal_identity_bound: bool
    strictly_inside_open_boundary_interval: bool
    available_before_boundary_decision: bool
    boundaries_strictly_ordered: bool
    tied_events_forbidden: bool


@dataclass(frozen=True)
class ParityCauseCreditContract:
    bit_identical_inputs: bool = True
    bit_identical_primitive_events: bool = True
    bit_identical_clocks: bool = True
    bit_identical_eligibility_classes: bool = True
    bit_identical_resets: bool = True
    bit_identical_termination_causes: bool = True
    bit_identical_credit_assignment: bool = True
    armed_bits_exact: int = 1
    armed_bits_bctt_ec: int = 1
    event_latches_exact: int = 1
    event_latches_bctt_ec: int = 1
    lookup_width_exact: int = 3
    lookup_width_bctt_ec: int = 3
    event_latch_is_costed_in_both_arms: bool = True


@dataclass(frozen=True)
class LifecycleContract:
    evaluate_before_update: bool = True
    continuing_sets_armed_to_current_positive: bool = True
    continuing_clears_event_latch: bool = True
    first_negative_while_armed_sets_latch: bool = True
    latch_sticky_through_reentry: bool = True
    termination_clears_armed_and_latch: bool = True
    reset_clears_armed_and_latch: bool = True
    identity_change_clears_armed_and_latch: bool = True
    bypass_completes_on_first_positive: bool = True


@dataclass(frozen=True)
class AuditManifest:
    source: EventSourceBinding | None
    parity: ParityCauseCreditContract
    lifecycle: LifecycleContract
    lookup_rows: tuple[LookupRow, ...]


@dataclass
class BoundaryState:
    armed: bool = False
    negative_event_latched: bool = False


@dataclass
class Activity:
    registered_audits: int = 1
    lookup_evaluations: int = 0
    environment_calls: int = 0
    environment_episodes: int = 0
    environment_transitions: int = 0
    policy_calls: int = 0
    learner_calls: int = 0
    trainer_calls: int = 0
    optimizer_updates: int = 0
    evaluation_calls: int = 0
    model_fit_calls: int = 0
    return_computations: int = 0
    rng_draws: int = 0
    retries_or_recoveries: int = 0


ZERO_RUNTIME_FIELDS = (
    "environment_calls",
    "environment_episodes",
    "environment_transitions",
    "policy_calls",
    "learner_calls",
    "trainer_calls",
    "optimizer_updates",
    "evaluation_calls",
    "model_fit_calls",
    "return_computations",
    "rng_draws",
    "retries_or_recoveries",
)


@dataclass(frozen=True)
class AuditResult:
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(dict(self.payload))

    def to_bytes(self) -> bytes:
        return (json.dumps(self.payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def unbound_manifest() -> AuditManifest:
    """Return the registered current-revision manifest: no causal source exists."""

    return AuditManifest(
        source=None,
        parity=ParityCauseCreditContract(),
        lifecycle=LifecycleContract(),
        lookup_rows=FROZEN_TRUTH_TABLE,
    )


def future_bound_manifest(source_id: str = "future-authenticated-target-negative-source") -> AuditManifest:
    """Construct the complete typed contract expected of a future real source.

    This helper does not authenticate a repository seam and is never used by the
    registered runner.  Tests use it only to exercise the frozen future-source
    truth table and lifecycle.
    """

    return replace(
        unbound_manifest(),
        source=EventSourceBinding(
            source_id=source_id,
            authentication_id="test-only-future-source-binding",
            authentication_verified=True,
            primitive_event_name="target_negative_primitive_event",
            scope=ScopeClass.PERSISTENT_OCCUPANCY,
            prospectively_declared_before_trace=True,
            target_negative_is_primitive_event=True,
            target_causal_identity_bound=True,
            strictly_inside_open_boundary_interval=True,
            available_before_boundary_decision=True,
            boundaries_strictly_ordered=True,
            tied_events_forbidden=True,
        ),
    )


def _truth_rows_receipt() -> list[dict[str, Any]]:
    return [
        {
            "a_y_e": row.inputs.bits,
            "debounce_bctt_ec": row.outputs.bits,
            "causal_state": "INVALID_UNARMED_LATCH" if row.inputs.bits in INVALID_CAUSAL_ROWS else "VALID",
        }
        for row in FROZEN_TRUTH_TABLE
    ]


def _contract_receipt() -> dict[str, Any]:
    return {
        "armed_bit": "a",
        "boundary_order": "tau_0<tau_1<tau_2; no tied event",
        "availability": "y_k and e_k are available before the decision at tau_k",
        "bctt_ec_rule": "a AND y AND NOT e",
        "bypass_behavior": "complete on first positive",
        "bypass_scopes": [scope.value for scope in BYPASS_SCOPES],
        "debounce_rule": "a AND y",
        "eligible_scope": ScopeClass.PERSISTENT_OCCUPANCY.value,
        "event_latch": "while armed, first target-negative primitive event strictly inside interval; sticky through reentry",
        "inference_boundary": "truth-table and causal-information-interface evidence only; no value or novelty claim",
        "order": "evaluate lookup; if continuing set a=y and clear e; termination, identity change, or reset clears both",
        "trace_specifications": {
            "INITIAL": "a_-1=0,y0=1 => 00 then a0=1",
            "HOLD": "e1=0,y1=1 => 11 and both target-terminate at tau1",
            "EXCURSION_REENTRY": "tau0<t_minus<t_plus<tau1; target-negative at t_minus; reentry at t_plus; e1=1,y1=1 => 10",
            "CLEAN_TAU2": "continuing BCTT-EC has a1=1, cleared latch, y2=1,e2=0 => target-terminate at tau2",
        },
        "truth_rows": _truth_rows_receipt(),
    }


def _source_failures(source: EventSourceBinding | None) -> list[str]:
    if source is None:
        return ["NO_AUTHENTICATED_CAUSAL_SOURCE_BOUND"]
    failures: list[str] = []
    exact = {
        "EMPTY_OR_UNTYPED_SOURCE_ID": type(source.source_id) is str and bool(source.source_id.strip()),
        "EMPTY_OR_UNTYPED_AUTHENTICATION_ID": type(source.authentication_id) is str and bool(source.authentication_id.strip()),
        "AUTHENTICATION_NOT_VERIFIED": source.authentication_verified is True,
        "EMPTY_OR_UNTYPED_PRIMITIVE_EVENT_NAME": type(source.primitive_event_name) is str and bool(source.primitive_event_name.strip()),
        "SCOPE_NOT_PERSISTENT_OCCUPANCY": source.scope is ScopeClass.PERSISTENT_OCCUPANCY,
        "NOT_PROSPECTIVELY_DECLARED": source.prospectively_declared_before_trace is True,
        "NOT_TARGET_NEGATIVE_PRIMITIVE_EVENT": source.target_negative_is_primitive_event is True,
        "TARGET_CAUSAL_IDENTITY_UNBOUND": source.target_causal_identity_bound is True,
        "EVENT_NOT_STRICTLY_INSIDE_INTERVAL": source.strictly_inside_open_boundary_interval is True,
        "EVENT_NOT_AVAILABLE_BEFORE_DECISION": source.available_before_boundary_decision is True,
        "BOUNDARIES_NOT_STRICTLY_ORDERED": source.boundaries_strictly_ordered is True,
        "TIED_EVENTS_NOT_FORBIDDEN": source.tied_events_forbidden is True,
    }
    for failure, passed in exact.items():
        if not passed:
            failures.append(failure)
    return failures


def _parity_failures(contract: ParityCauseCreditContract) -> list[str]:
    failures: list[str] = []
    boolean_fields = (
        "bit_identical_inputs",
        "bit_identical_primitive_events",
        "bit_identical_clocks",
        "bit_identical_eligibility_classes",
        "bit_identical_resets",
        "bit_identical_termination_causes",
        "bit_identical_credit_assignment",
        "event_latch_is_costed_in_both_arms",
    )
    failures.extend(name.upper() for name in boolean_fields if getattr(contract, name) is not True)
    if any(type(value) is not int for value in (contract.armed_bits_exact, contract.armed_bits_bctt_ec)) or (contract.armed_bits_exact, contract.armed_bits_bctt_ec) != (1, 1):
        failures.append("ARMED_BIT_PARITY")
    if any(type(value) is not int for value in (contract.event_latches_exact, contract.event_latches_bctt_ec)) or (contract.event_latches_exact, contract.event_latches_bctt_ec) != (1, 1):
        failures.append("EVENT_LATCH_COST_PARITY")
    if any(type(value) is not int for value in (contract.lookup_width_exact, contract.lookup_width_bctt_ec)) or (contract.lookup_width_exact, contract.lookup_width_bctt_ec) != (3, 3):
        failures.append("THREE_INPUT_LOOKUP_WIDTH_PARITY")
    return failures


def _lifecycle_failures(contract: LifecycleContract) -> list[str]:
    return [
        name.upper()
        for name in contract.__dataclass_fields__
        if type(getattr(contract, name)) is not bool or getattr(contract, name) is not True
    ]


def _lookup_map(rows: Sequence[LookupRow]) -> dict[TruthInput, LookupOutput]:
    output: dict[TruthInput, LookupOutput] = {}
    for row in rows:
        if row.inputs in output:
            raise ContractViolation(f"duplicate lookup row: {row.inputs.bits}")
        output[row.inputs] = row.outputs
    return output


def _lookup(
    rows: Mapping[TruthInput, LookupOutput],
    arm: Arm,
    state: BoundaryState,
    positive: bool,
    activity: Activity,
) -> bool:
    key = TruthInput(state.armed, positive, state.negative_event_latched)
    if key not in rows:
        raise ContractViolation(f"lookup row absent: {key.bits}")
    activity.lookup_evaluations += 1
    output = rows[key]
    return output.exact_boundary_debounce if arm is Arm.EXACT_BOUNDARY_DEBOUNCE else output.bctt_ec


def observe_negative_event(state: BoundaryState, lifecycle: LifecycleContract) -> None:
    if state.armed and lifecycle.first_negative_while_armed_sets_latch:
        state.negative_event_latched = True


def observe_reentry(state: BoundaryState, lifecycle: LifecycleContract) -> None:
    if not lifecycle.latch_sticky_through_reentry:
        state.negative_event_latched = False


def reset_state(state: BoundaryState, lifecycle: LifecycleContract, *, identity_change: bool = False) -> None:
    should_clear = lifecycle.identity_change_clears_armed_and_latch if identity_change else lifecycle.reset_clears_armed_and_latch
    if should_clear:
        state.armed = False
        state.negative_event_latched = False


def evaluate_boundary(
    *,
    rows: Mapping[TruthInput, LookupOutput],
    arm: Arm,
    state: BoundaryState,
    positive: bool,
    scope: ScopeClass,
    lifecycle: LifecycleContract,
    activity: Activity,
) -> bool:
    """Evaluate from pre-update state, then apply the frozen boundary update."""

    if scope in BYPASS_SCOPES:
        complete = bool(positive and lifecycle.bypass_completes_on_first_positive)
    else:
        if not lifecycle.evaluate_before_update:
            state.armed = positive
            if lifecycle.continuing_clears_event_latch:
                state.negative_event_latched = False
        complete = _lookup(rows, arm, state, positive, activity)

    if complete:
        if lifecycle.termination_clears_armed_and_latch:
            state.armed = False
            state.negative_event_latched = False
    elif lifecycle.evaluate_before_update:
        if lifecycle.continuing_sets_armed_to_current_positive:
            state.armed = positive
        if lifecycle.continuing_clears_event_latch:
            state.negative_event_latched = False
    return complete


def _truth_table_audit(rows: Mapping[TruthInput, LookupOutput], activity: Activity) -> tuple[list[dict[str, Any]], bool, bool, bool]:
    receipt: list[dict[str, Any]] = []
    exact_ok = True
    bctt_nonrepair_rows_ok = True
    repair_ok = True
    for frozen in FROZEN_TRUTH_TABLE:
        # Both lookups are explicitly evaluated for equal-width comparator parity.
        exact = _lookup(rows, Arm.EXACT_BOUNDARY_DEBOUNCE, BoundaryState(frozen.inputs.armed, frozen.inputs.negative_event_latched), frozen.inputs.positive, activity)
        bctt = _lookup(rows, Arm.BCTT_EC, BoundaryState(frozen.inputs.armed, frozen.inputs.negative_event_latched), frozen.inputs.positive, activity)
        exact_ok &= exact is frozen.outputs.exact_boundary_debounce
        if frozen.inputs.bits == "111":
            repair_ok &= bctt is False and exact is True
        else:
            # The existing BCTT regression branch guards every non-repair row,
            # not only the named clean-hold row 110.  Together with repair_ok
            # this admits support only when every complete two-bit row matches.
            bctt_nonrepair_rows_ok &= bctt is frozen.outputs.bctt_ec
        receipt.append({
            "a_y_e": frozen.inputs.bits,
            "actual": f"{int(exact)}{int(bctt)}",
            "expected": frozen.outputs.bits,
            "causal_state": "INVALID_UNARMED_LATCH" if frozen.inputs.bits in INVALID_CAUSAL_ROWS else "VALID",
        })
    collapses = all(row["actual"][0] == row["actual"][1] for row in receipt)
    return receipt, exact_ok, bctt_nonrepair_rows_ok, repair_ok and not collapses


def _evaluate_pair(
    rows: Mapping[TruthInput, LookupOutput],
    states: Mapping[Arm, BoundaryState],
    positive: bool,
    lifecycle: LifecycleContract,
    activity: Activity,
    scope: ScopeClass = ScopeClass.PERSISTENT_OCCUPANCY,
) -> dict[str, bool]:
    return {
        arm.value: evaluate_boundary(
            rows=rows,
            arm=arm,
            state=states[arm],
            positive=positive,
            scope=scope,
            lifecycle=lifecycle,
            activity=activity,
        )
        for arm in Arm
    }


def _trace_audit(rows: Mapping[TruthInput, LookupOutput], lifecycle: LifecycleContract, activity: Activity) -> tuple[dict[str, Any], bool]:
    initial_states = {arm: BoundaryState() for arm in Arm}
    initial = _evaluate_pair(rows, initial_states, True, lifecycle, activity)

    hold_states = {arm: BoundaryState(armed=True) for arm in Arm}
    hold = _evaluate_pair(rows, hold_states, True, lifecycle, activity)
    hold_post = {
        arm.value: {
            "armed": hold_states[arm].armed,
            "event_latched": hold_states[arm].negative_event_latched,
        }
        for arm in Arm
    }

    excursion_states = {arm: BoundaryState(armed=True) for arm in Arm}
    for state in excursion_states.values():
        observe_negative_event(state, lifecycle)
        observe_reentry(state, lifecycle)
    excursion = _evaluate_pair(rows, excursion_states, True, lifecycle, activity)
    excursion_bctt_post_armed = excursion_states[Arm.BCTT_EC].armed
    excursion_bctt_post_latch = excursion_states[Arm.BCTT_EC].negative_event_latched
    clean_tau2 = evaluate_boundary(
        rows=rows,
        arm=Arm.BCTT_EC,
        state=excursion_states[Arm.BCTT_EC],
        positive=True,
        scope=ScopeClass.PERSISTENT_OCCUPANCY,
        lifecycle=lifecycle,
        activity=activity,
    )

    reset = BoundaryState(armed=True, negative_event_latched=True)
    reset_state(reset, lifecycle)
    reset_after_clear = {"armed": reset.armed, "event_latched": reset.negative_event_latched}
    reset_first = evaluate_boundary(rows=rows, arm=Arm.BCTT_EC, state=reset, positive=True, scope=ScopeClass.PERSISTENT_OCCUPANCY, lifecycle=lifecycle, activity=activity)
    reset_second = evaluate_boundary(rows=rows, arm=Arm.BCTT_EC, state=reset, positive=True, scope=ScopeClass.PERSISTENT_OCCUPANCY, lifecycle=lifecycle, activity=activity)

    identity = BoundaryState(armed=True, negative_event_latched=True)
    reset_state(identity, lifecycle, identity_change=True)
    identity_after_clear = {"armed": identity.armed, "event_latched": identity.negative_event_latched}
    identity_first = evaluate_boundary(rows=rows, arm=Arm.BCTT_EC, state=identity, positive=True, scope=ScopeClass.PERSISTENT_OCCUPANCY, lifecycle=lifecycle, activity=activity)
    identity_second = evaluate_boundary(rows=rows, arm=Arm.BCTT_EC, state=identity, positive=True, scope=ScopeClass.PERSISTENT_OCCUPANCY, lifecycle=lifecycle, activity=activity)

    bypass: dict[str, Any] = {}
    for scope in BYPASS_SCOPES:
        states = {arm: BoundaryState() for arm in Arm}
        bypass[scope.value] = _evaluate_pair(rows, states, True, lifecycle, activity, scope)

    receipt = {
        "INITIAL": {"decision": initial, "post_armed": {arm.value: initial_states[arm].armed for arm in Arm}},
        "HOLD": {"decision": hold, "post_state": hold_post},
        "EXCURSION_REENTRY": {
            "decision": excursion,
            "bctt_post_armed": excursion_bctt_post_armed,
            "bctt_post_latch": excursion_bctt_post_latch,
        },
        "CLEAN_TAU2": {"bctt_ec": clean_tau2},
        "RESET_REARM": {"after_reset": reset_after_clear, "first": reset_first, "second": reset_second},
        "IDENTITY_CHANGE_REARM": {"after_identity_change": identity_after_clear, "first": identity_first, "second": identity_second},
        "BYPASS": bypass,
    }
    expected = {
        "INITIAL": {"decision": {arm.value: False for arm in Arm}, "post_armed": {arm.value: True for arm in Arm}},
        "HOLD": {
            "decision": {arm.value: True for arm in Arm},
            "post_state": {arm.value: {"armed": False, "event_latched": False} for arm in Arm},
        },
        "EXCURSION_REENTRY": {
            "decision": {Arm.EXACT_BOUNDARY_DEBOUNCE.value: True, Arm.BCTT_EC.value: False},
            "bctt_post_armed": True,
            "bctt_post_latch": False,
        },
        "CLEAN_TAU2": {"bctt_ec": True},
        "RESET_REARM": {"after_reset": {"armed": False, "event_latched": False}, "first": False, "second": True},
        "IDENTITY_CHANGE_REARM": {"after_identity_change": {"armed": False, "event_latched": False}, "first": False, "second": True},
        "BYPASS": {
            scope.value: {arm.value: True for arm in Arm}
            for scope in BYPASS_SCOPES
        },
    }
    return receipt, receipt == expected


def _choose_branch(
    *,
    source_failures: Sequence[str],
    parity_failures: Sequence[str],
    exact_ok: bool,
    hold_ok: bool,
    repair_ok: bool,
    lifecycle_ok: bool,
) -> TerminalBranch:
    if source_failures:
        return TerminalBranch.INVALID_EVENT_CAUSALITY_OR_SCOPE
    if parity_failures:
        return TerminalBranch.INVALID_PARITY_OR_CAUSE_CONTRACT
    if not exact_ok:
        return TerminalBranch.EXACT_DEBOUNCE_NOT_REPRODUCED
    if not hold_ok:
        return TerminalBranch.BCTT_EC_HOLD_REGRESSION
    if not repair_ok:
        return TerminalBranch.BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE
    if not lifecycle_ok:
        return TerminalBranch.LATCH_RESET_OR_REARM_FAILED
    return TerminalBranch.EVENT_CERTIFIED_BOUNDARY_DIVERGENCE_SUPPORTED


def _source_receipt(source: EventSourceBinding | None, failures: Sequence[str]) -> dict[str, Any]:
    if source is None:
        return {
            "status": "UNBOUND",
            "source_id": None,
            "authentication_id": None,
            "event_observations": [],
            "fabricated_event_latches": 0,
            "failures": list(failures),
        }
    return {
        "status": "AUTHENTICATED" if not failures else "INVALID",
        "source_id": source.source_id,
        "authentication_id": source.authentication_id,
        "event_observations": [],
        "fabricated_event_latches": 0,
        "failures": list(failures),
        "declared_contract": {
            "primitive_event_name": source.primitive_event_name,
            "authentication_verified": source.authentication_verified,
            "scope": source.scope.value if isinstance(source.scope, ScopeClass) else repr(source.scope),
            "prospectively_declared_before_trace": source.prospectively_declared_before_trace,
            "target_negative_is_primitive_event": source.target_negative_is_primitive_event,
            "target_causal_identity_bound": source.target_causal_identity_bound,
            "strictly_inside_open_boundary_interval": source.strictly_inside_open_boundary_interval,
            "available_before_boundary_decision": source.available_before_boundary_decision,
            "boundaries_strictly_ordered": source.boundaries_strictly_ordered,
            "tied_events_forbidden": source.tied_events_forbidden,
        },
    }


def _build_result(manifest: AuditManifest) -> AuditResult:
    activity = Activity()
    source_failures = _source_failures(manifest.source)
    parity_failures = _parity_failures(manifest.parity)
    lifecycle_failures = _lifecycle_failures(manifest.lifecycle)
    truth_receipt: dict[str, Any] = {"status": "NOT_EVALUATED", "rows": []}
    trace_receipt: dict[str, Any] = {"status": "NOT_EVALUATED", "traces": {}}
    exact_ok = hold_ok = repair_ok = lifecycle_ok = False

    # Causality and scope dominate parity and all lookup work.  Parity dominates
    # lookup work as well.  This is what prevents an unbound manifest from
    # manufacturing e by exercising the reference state machine.
    if not source_failures and not parity_failures:
        try:
            lookup_rows = _lookup_map(manifest.lookup_rows)
            if set(lookup_rows) != set(FROZEN_TRUTH_MAP):
                raise ContractViolation("lookup domain is not the full three-input truth table")
            truth_rows, exact_ok, hold_ok, repair_ok = _truth_table_audit(lookup_rows, activity)
            traces, lifecycle_ok = _trace_audit(lookup_rows, manifest.lifecycle, activity)
            lifecycle_ok = lifecycle_ok and not lifecycle_failures
            truth_receipt = {"status": "EVALUATED", "rows": truth_rows}
            trace_receipt = {"status": "EVALUATED", "traces": traces}
        except ContractViolation as exc:
            truth_receipt = {"status": "INVALID_LOOKUP_MANIFEST", "rows": [], "failure": str(exc)}
            trace_receipt = {"status": "NOT_EVALUATED", "traces": {}}

    branch = _choose_branch(
        source_failures=source_failures,
        parity_failures=parity_failures,
        exact_ok=exact_ok,
        hold_ok=hold_ok,
        repair_ok=repair_ok,
        lifecycle_ok=lifecycle_ok,
    )
    failures = (
        [{"kind": "EVENT_CAUSALITY_OR_SCOPE", "detail": item} for item in source_failures]
        + [{"kind": "PARITY_OR_CAUSE_CONTRACT", "detail": item} for item in parity_failures]
        + ([] if source_failures or parity_failures or exact_ok else [{"kind": "EXACT_DEBOUNCE_NOT_REPRODUCED"}])
        + ([] if source_failures or parity_failures or not exact_ok or hold_ok else [{"kind": "BCTT_EC_HOLD_REGRESSION"}])
        + ([] if source_failures or parity_failures or not exact_ok or not hold_ok or repair_ok else [{"kind": "BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE"}])
        + (
            []
            if source_failures or parity_failures or not exact_ok or not hold_ok or not repair_ok or lifecycle_ok
            else [{"kind": "LATCH_RESET_OR_REARM", "detail": item} for item in (lifecycle_failures or ["TRACE_MISMATCH"])]
        )
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "version_id": VERSION_ID,
        "treatment_id": TREATMENT_ID,
        "registered_source_status": "NO_GENUINE_TARGET_NEGATIVE_CAUSAL_DEPLOYMENT_EVENT_SEAM" if manifest.source is None else "FUTURE_SOURCE_MANIFEST",
        "source_receipt": _source_receipt(manifest.source, source_failures),
        "frozen_contract": _contract_receipt(),
        "parity_cause_credit_receipt": {"contract": asdict(manifest.parity), "failures": list(parity_failures)},
        "lifecycle_contract_receipt": {"contract": asdict(manifest.lifecycle), "failures": lifecycle_failures},
        "truth_table_audit": truth_receipt,
        "trace_audit": trace_receipt,
        "contract_failures": failures,
        "terminal_branch": branch.value,
        "branch_precedence_applied": list(BRANCH_PRECEDENCE),
        "activity": asdict(activity),
        "claim_boundary": "causal-information-interface and truth-table evidence only; no natural value, novelty, return, or deployment claim",
        "scientific_disposition": None,
        "successor_selected": False,
    }
    return AuditResult(payload)


def audit_manifest(manifest: AuditManifest) -> AuditResult:
    """Run one deterministic, pure, zero-runtime audit of a typed manifest."""

    result = _build_result(manifest)
    validate_audit_result(result, manifest)
    return result


def validate_audit_result(result: AuditResult | Mapping[str, Any], manifest: AuditManifest) -> None:
    """Reject every serialized mutation by exact recomputation from the manifest."""

    actual = result.to_dict() if isinstance(result, AuditResult) else copy.deepcopy(dict(result))
    expected = _build_result(manifest).to_dict()
    if actual != expected:
        raise ContractViolation("serialized audit disagrees with deterministic manifest recomputation")
    activity = actual.get("activity")
    if not isinstance(activity, Mapping) or set(activity) != set(asdict(Activity())):
        raise ContractViolation("activity receipt fields drifted")
    if activity["registered_audits"] != 1:
        raise ContractViolation("registered audit count is not one")
    for name in ZERO_RUNTIME_FIELDS:
        if type(activity[name]) is not int or activity[name] != 0:
            raise ContractViolation(f"prohibited runtime activity is nonzero: {name}")
    if manifest.source is None:
        if activity["lookup_evaluations"] != 0:
            raise ContractViolation("unbound source performed lookup activity")
        if actual["source_receipt"]["fabricated_event_latches"] != 0:
            raise ContractViolation("unbound source fabricated event latch evidence")
        if actual["terminal_branch"] != TerminalBranch.INVALID_EVENT_CAUSALITY_OR_SCOPE.value:
            raise ContractViolation("unbound source escaped the fail-closed branch")


def publish_registered_audit_once(path: str | Path, manifest: AuditManifest | None = None) -> AuditResult:
    """Reserve the output claim before auditing, then publish without overwrite."""

    destination = Path(path)
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"output parent does not exist: {destination.parent}")
    selected = unbound_manifest() if manifest is None else manifest
    try:
        handle = destination.open("xb")
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite one-shot A1 artifact: {destination}") from exc
    # An audit failure intentionally leaves the empty reservation in place: a
    # failed registered attempt must not silently release and reuse its claim.
    with handle:
        result = audit_manifest(selected)
        handle.write(result.to_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    return result
