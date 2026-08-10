"""Pure finite-domain EC4G-R1 versus Direct-tau D1 census.

The bundled cell is a synthetic action-map witness, never natural EC4G data.
This candidate-local module owns no environment, RNG, training, or artifact I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
import math
import re

import numpy as np


ARMS = ("R0", "RV", "RB", "RS", "PV", "PB", "PS")
GATES = ("registered", "positivity", "executor", "receipt", "fold", "clock", "cost", "fallback")


class CensusClassification(str, Enum):
    INCOMPLETE_CONTRACT = "INCOMPLETE_CONTRACT"
    EQUIVALENCE = "EQUIVALENCE"
    LABEL_ONLY_DIFFERENCE = "LABEL_ONLY_DIFFERENCE"
    BEHAVIORAL_DISCORDANCE = "BEHAVIORAL_DISCORDANCE"


class Action(str, Enum):
    PROBE = "P"
    NO_PROBE = "N"
    ABSTAIN = "A"


@dataclass(frozen=True)
class ReceiptContract:
    schema_id: str
    authorized: bool
    executor_id: str
    source_id: str
    source_version: str
    latency_class: str
    byte_length_class: str
    timestamp_representation: str
    delivery_channel: str
    public_observability_id: str
    payload_support_id: str
    safe_action_mask_digest: str
    event_id: str
    trajectory_id: str
    event_time: int
    visible_payload: bytes
    blinded_payload: bytes
    shuffled_payload: bytes
    assignment_visible: bool
    donor_event_id: str
    donor_trajectory_id: str
    donor_time: int
    donor_source_id: str
    donor_owner_epoch: int
    registered_donors: tuple[tuple[str, int], ...]


_REGISTERED_RECEIPT = ReceiptContract(
    schema_id="synthetic.receipt.v1", authorized=True,
    executor_id="synthetic-executor", source_id="synthetic-source", source_version="v1",
    latency_class="fixed-one-tick", byte_length_class="bytes:4",
    timestamp_representation="integer-tick-v1", delivery_channel="synthetic-channel",
    public_observability_id="public-envelope-v1", payload_support_id="four-byte-support-v1",
    safe_action_mask_digest=hashlib.sha256(b"safe-actions").hexdigest(),
    event_id="event-x0", trajectory_id="trajectory-x0", event_time=10,
    visible_payload=b"GOOD", blinded_payload=b"\x00\x00\x00\x00",
    shuffled_payload=b"SWAP", assignment_visible=False,
    donor_event_id="event-donor", donor_trajectory_id="trajectory-donor", donor_time=5,
    donor_source_id="registered-donor", donor_owner_epoch=3,
    registered_donors=(("registered-donor", 3),),
)


@dataclass(frozen=True)
class Continuation:
    action: Action
    execution_path: str; receipt_variant: str; delivery_channel: str; envelope_id: str
    envelope_bytes: bytes; body: bytes
    external_cost: float
    digest: str


@dataclass(frozen=True)
class Cell:
    """Immutable z_x; nu is measured mean minus external cost exactly once."""

    cell_id: str
    measured_means: tuple[float, ...]
    external_costs: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    support_gates: tuple[tuple[str, bool], ...]
    executor_measure: float
    crossfit_id: str
    receipts: ReceiptContract
    fallback_policy: str
    fallback_interval: tuple[float, float]
    fallback_digest: str
    margins: tuple[float, float, float]
    kappa: float
    continuations: tuple[Continuation, ...]

    @property
    def nu(self) -> tuple[float, ...]:
        return tuple(
            float(mean) - float(cost)
            for mean, cost in zip(self.measured_means, self.external_costs)
        )

    @property
    def supported(self) -> bool:
        return all(value for _, value in self.support_gates)

    def continuation(self, action: Action) -> Continuation:
        return next(item for item in self.continuations if item.action is action)


@dataclass(frozen=True)
class FrozenCensus:
    expected_cell_ids: tuple[str, ...]
    cells: tuple[Cell, ...]


@dataclass(frozen=True)
class Estimate:
    point: float
    standard_error: float
    lower: float
    upper: float


@dataclass(frozen=True)
class Contrasts:
    tau_t: Estimate
    tau_b: Estimate
    tau_a: Estimate
    tau_c: Estimate
    tau_v: Estimate


@dataclass(frozen=True)
class Decision:
    action: Action
    execution_path: str; receipt_variant: str; delivery_channel: str; envelope_id: str
    envelope_bytes: bytes; body: bytes
    external_cost: float
    digest: str


@dataclass(frozen=True)
class Comparison:
    cell_id: str
    supported: bool
    executor_measure: float
    nu: tuple[float, ...]
    contrasts: Contrasts
    ec4g: Decision
    direct_tau: Decision
    point_difference: float | None
    confidence_upper_bound: float

    @property
    def label_equal(self) -> bool:
        return self.ec4g.action is self.direct_tau.action

    @property
    def behavior_equal(self) -> bool:
        return _behavior(self.ec4g) == _behavior(self.direct_tau)


@dataclass(frozen=True)
class CensusResult:
    classification: CensusClassification
    comparisons: tuple[Comparison, ...] = ()
    issues: tuple[str, ...] = ()

    def to_bytes(self) -> bytes:
        payload = {
            "cells": [_comparison_payload(item) for item in self.comparisons],
            "classification": self.classification.value,
            "issues": list(self.issues),
        }
        return json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")


def continuation_digest(
    execution_path: str,
    receipt_variant: str,
    delivery_channel: str,
    envelope_id: str,
    envelope_bytes: bytes,
    body: bytes,
    external_cost: float,
) -> str:
    strings = (execution_path, receipt_variant, delivery_channel, envelope_id)
    if any(not isinstance(value, str) or not value for value in strings):
        raise ValueError("continuation identity fields must be nonempty strings")
    if not isinstance(envelope_bytes, bytes) or not isinstance(body, bytes):
        raise TypeError("continuation envelope and body must be bytes")
    cost = float(external_cost)
    if not math.isfinite(cost) or cost < 0.0:
        raise ValueError("continuation cost must be finite and nonnegative")
    payload = json.dumps([*strings, envelope_bytes.hex(), body.hex(), format(cost, ".17g")], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(b"ec4g-r1-continuation-v2\x00" + payload).hexdigest()


def compute_contrasts(cell: Cell) -> Contrasts:
    index = {name: position for position, name in enumerate(ARMS)}
    covariance = np.asarray(cell.covariance, dtype=np.float64)

    def one(left: str, right: str) -> Estimate:
        i, j = index[left], index[right]
        point = cell.nu[i] - cell.nu[j]
        variance = float(
            covariance[i, i] + covariance[j, j] - 2.0 * covariance[i, j]
        )
        if variance < -1e-12:
            raise ValueError(f"negative contrast variance for {left}-{right}")
        standard_error = math.sqrt(max(0.0, variance))
        radius = float(cell.kappa) * standard_error
        return Estimate(point, standard_error, point - radius, point + radius)

    return Contrasts(
        tau_t=one("RV", "R0"),
        tau_b=one("RB", "R0"),
        tau_a=one("RS", "RB"),
        tau_c=one("RV", "RS"),
        tau_v=one("RV", "RB"),
    )


def ec4g_gate(cell: Cell) -> Decision:
    values = compute_contrasts(cell)
    delta_t, delta_c, delta_v = cell.margins
    fallback_upper = float(cell.fallback_interval[1])
    if not cell.supported:
        action = Action.ABSTAIN
    elif (
        values.tau_t.lower > max(0.0, fallback_upper) + delta_t
        and values.tau_c.lower > delta_c
        and values.tau_v.lower > delta_v
    ):
        action = Action.PROBE
    elif values.tau_t.upper <= 0.0 and fallback_upper <= 0.0:
        action = Action.NO_PROBE
    else:
        action = Action.ABSTAIN
    return _decision(cell, action)


def direct_tau_gate(cell: Cell) -> Decision:
    values = compute_contrasts(cell)
    fallback_upper = float(cell.fallback_interval[1])
    if not cell.supported:
        action = Action.ABSTAIN
    elif values.tau_t.lower > max(0.0, fallback_upper) + cell.margins[0]:
        action = Action.PROBE
    elif values.tau_t.upper <= 0.0 and fallback_upper <= 0.0:
        action = Action.NO_PROBE
    else:
        action = Action.ABSTAIN
    return _decision(cell, action)


def run_census(frozen: FrozenCensus) -> CensusResult:
    """Run both fixed maps once per exact cell on the same object."""

    try:
        issues = _validate(frozen)
    except Exception as exc:
        issues = (f"contract validation failed: {type(exc).__name__}: {exc}",)
    if issues:
        return CensusResult(CensusClassification.INCOMPLETE_CONTRACT, issues=issues)
    comparisons: list[Comparison] = []
    try:
        for cell in frozen.cells:
            values = compute_contrasts(cell)
            ec4g, direct = ec4g_gate(cell), direct_tau_gate(cell)
            left_interval = _action_interval(cell, values, ec4g.action)
            right_interval = _action_interval(cell, values, direct.action)
            comparisons.append(
                Comparison(
                    cell.cell_id,
                    cell.supported,
                    float(cell.executor_measure),
                    cell.nu,
                    values,
                    ec4g,
                    direct,
                    _point_difference(cell, values, ec4g.action, direct.action),
                    left_interval[1] - right_interval[0],
                )
            )
    except Exception as exc:
        return CensusResult(
            CensusClassification.INCOMPLETE_CONTRACT,
            issues=(f"gate execution failed: {type(exc).__name__}: {exc}",),
        )

    if any(not item.behavior_equal for item in comparisons):
        result = CensusClassification.BEHAVIORAL_DISCORDANCE
    elif any(not item.label_equal for item in comparisons):
        result = CensusClassification.LABEL_ONLY_DIFFERENCE
    else:
        result = CensusClassification.EQUIVALENCE
    return CensusResult(result, tuple(comparisons))


def build_synthetic_witness() -> FrozenCensus:
    """Return the exact fully-supported x0 witness from the execution brief."""

    continuations = (
        _continuation(Action.PROBE, "probe", "RV", b"probe-once-then-frozen-continuation"),
        _continuation(Action.NO_PROBE, "no-probe", "RB", b"no-probe-frozen-continuation"),
        _continuation(Action.ABSTAIN, "fallback", "RS", b"fallback-r0-frozen-continuation"),
    )
    diagonal = (0.0003, 0.0001, 0.000125, 0.0003, 0.0, 0.0, 0.0)
    covariance = tuple(
        tuple(value if i == j else 0.0 for j in range(7))
        for i, value in enumerate(diagonal)
    )
    cell = Cell(
        cell_id="x0",
        measured_means=(0.0, 0.10, 0.12, 0.14, 0.0, 0.0, 0.0),
        external_costs=(0.0,) * 7,
        covariance=covariance,
        support_gates=tuple((name, True) for name in GATES),
        executor_measure=1.0,
        crossfit_id="synthetic-crossfit-v1",
        receipts=_REGISTERED_RECEIPT,
        fallback_policy="R0",
        fallback_interval=(0.0, 0.0),
        fallback_digest=continuations[2].digest,
        margins=(0.0, 0.0, 0.0),
        kappa=1.0,
        continuations=continuations,
    )
    return FrozenCensus(("x0",), (cell,))


def _validate(frozen: FrozenCensus) -> tuple[str, ...]:
    issues: list[str] = []
    actual = tuple(cell.cell_id for cell in frozen.cells)
    if not frozen.expected_cell_ids or len(set(frozen.expected_cell_ids)) != len(
        frozen.expected_cell_ids
    ):
        issues.append("expected finite cell domain must be nonempty and unique")
    if actual != frozen.expected_cell_ids:
        issues.append("cell rows must exactly match frozen domain and order")
    for cell in frozen.cells:
        issues.extend(_validate_cell(cell))
    return tuple(issues)


def _validate_cell(cell: Cell) -> tuple[str, ...]:
    issues: list[str] = []
    prefix = f"cell {cell.cell_id!r}"
    for name, values in (
        ("measured means", cell.measured_means),
        ("external costs", cell.external_costs),
    ):
        if len(values) != 7 or not all(math.isfinite(float(value)) for value in values):
            issues.append(f"{prefix} {name} must contain seven finite values")
    if any(float(value) < 0.0 for value in cell.external_costs):
        issues.append(f"{prefix} external costs must be nonnegative")
    covariance = np.asarray(cell.covariance, dtype=np.float64)
    if covariance.shape != (7, 7) or not bool(np.isfinite(covariance).all()):
        issues.append(f"{prefix} covariance must be finite 7x7")
    elif not bool(np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-12)):
        issues.append(f"{prefix} covariance must be symmetric")
    elif float(np.linalg.eigvalsh(covariance).min()) < -1e-12:
        issues.append(f"{prefix} covariance must be positive semidefinite")
    gates_valid = tuple(name for name, _ in cell.support_gates) == GATES and all(
        type(value) is bool for _, value in cell.support_gates
    )
    if not gates_valid:
        issues.append(f"{prefix} support gates must be the exact boolean conjunction")
    elif not cell.supported:
        issues.append(f"{prefix} expected row must be fully supported")
    measure = float(cell.executor_measure)
    if not math.isfinite(measure) or measure <= 0.0:
        issues.append(f"{prefix} executor measure must be finite and strictly positive")
    if not cell.cell_id or not cell.crossfit_id or not cell.fallback_policy:
        issues.append(f"{prefix} identity/crossfit/fallback fields must be nonempty")
    if not math.isfinite(float(cell.kappa)) or cell.kappa < 0.0:
        issues.append(f"{prefix} kappa must be finite and nonnegative")
    if len(cell.margins) != 3 or any(
        not math.isfinite(float(value)) or value < 0.0 for value in cell.margins
    ):
        issues.append(f"{prefix} margins must be three finite nonnegative values")
    lower, upper = (float(value) for value in cell.fallback_interval)
    if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper:
        issues.append(f"{prefix} fallback interval is invalid")
    if tuple(item.action for item in cell.continuations) != tuple(Action):
        issues.append(f"{prefix} must contain P/N/A continuations in exact order")
    else:
        for item in cell.continuations:
            variants = {
                "RV": cell.receipts.visible_payload,
                "RB": cell.receipts.blinded_payload,
                "RS": cell.receipts.shuffled_payload,
            }
            if item.execution_path not in {"probe", "no-probe", "fallback"}:
                issues.append(f"{prefix} {item.action.value} execution path is invalid")
            if item.receipt_variant not in variants:
                issues.append(f"{prefix} {item.action.value} receipt variant is invalid")
            elif item.envelope_bytes != variants[item.receipt_variant]:
                issues.append(f"{prefix} {item.action.value} envelope bytes mismatch")
            if item.delivery_channel != cell.receipts.delivery_channel:
                issues.append(f"{prefix} {item.action.value} delivery channel mismatch")
            if item.envelope_id != cell.receipts.public_observability_id:
                issues.append(f"{prefix} {item.action.value} envelope identity mismatch")
            try:
                expected = continuation_digest(*_behavior(item)[:-1])
            except Exception as exc:
                issues.append(f"{prefix} invalid {item.action.value} continuation: {exc}")
            else:
                if item.digest != expected:
                    issues.append(f"{prefix} {item.action.value} digest mismatch")
        if cell.continuation(Action.ABSTAIN).digest != cell.fallback_digest:
            issues.append(f"{prefix} abstain continuation does not bind fallback")
    issues.extend(f"{prefix} {issue}" for issue in _validate_receipts(cell.receipts))
    return tuple(issues)


def _validate_receipts(item: ReceiptContract) -> tuple[str, ...]:
    issues: list[str] = []
    groups = (
        ("schema/executor/source/version", (
            "schema_id", "authorized", "executor_id", "source_id", "source_version",
        )),
        ("latency/timestamp/delivery channel", (
            "latency_class", "timestamp_representation", "delivery_channel",
        )),
        ("payload support/byte-length/safe-action mask", (
            "payload_support_id", "byte_length_class", "safe_action_mask_digest",
        )),
        ("public envelope identity", ("public_observability_id",)),
        ("exact RV/RB/RS payloads", (
            "visible_payload", "blinded_payload", "shuffled_payload",
        )),
        ("exact event/donor relation", (
            "event_id", "trajectory_id", "event_time", "assignment_visible",
            "donor_event_id", "donor_trajectory_id", "donor_time",
            "donor_source_id", "donor_owner_epoch", "registered_donors",
        )),
    )
    for label, fields in groups:
        if any(getattr(item, name) != getattr(_REGISTERED_RECEIPT, name) for name in fields):
            issues.append(f"receipt does not match registered {label}")
    if item.blinded_payload == item.shuffled_payload:
        issues.append("receipt blinded and shuffled variants must differ")
    try:
        donor_time_is_finite = math.isfinite(float(item.donor_time))
    except (TypeError, ValueError):
        donor_time_is_finite = False
    if not donor_time_is_finite:
        issues.append("receipt donor time must be finite")
    return tuple(issues)


def _behavior(item: Continuation | Decision) -> tuple[object, ...]:
    return (
        item.execution_path, item.receipt_variant, item.delivery_channel,
        item.envelope_id, item.envelope_bytes, item.body, item.external_cost, item.digest,
    )


def _continuation(
    action: Action, execution_path: str, receipt_variant: str, body: bytes, cost: float = 0.0
) -> Continuation:
    payloads = {
        "RV": _REGISTERED_RECEIPT.visible_payload,
        "RB": _REGISTERED_RECEIPT.blinded_payload,
        "RS": _REGISTERED_RECEIPT.shuffled_payload,
    }
    values = (
        execution_path, receipt_variant, _REGISTERED_RECEIPT.delivery_channel,
        _REGISTERED_RECEIPT.public_observability_id, payloads[receipt_variant], body,
        float(cost),
    )
    return Continuation(action, *values, continuation_digest(*values))


def _decision(cell: Cell, action: Action) -> Decision:
    item = cell.continuation(action)
    return Decision(action, *_behavior(item))


def _action_interval(
    cell: Cell, values: Contrasts, action: Action
) -> tuple[float, float]:
    if action is Action.PROBE:
        return values.tau_t.lower, values.tau_t.upper
    if action is Action.NO_PROBE:
        return 0.0, 0.0
    return tuple(float(value) for value in cell.fallback_interval)


def _point_difference(
    cell: Cell, values: Contrasts, left: Action, right: Action
) -> float | None:
    def point(action: Action) -> float | None:
        if action is Action.PROBE:
            return values.tau_t.point
        if action is Action.NO_PROBE:
            return 0.0
        lower, upper = cell.fallback_interval
        return float(lower) if lower == upper else None

    left_value, right_value = point(left), point(right)
    return (
        None
        if left_value is None or right_value is None
        else left_value - right_value
    )


def _comparison_payload(item: Comparison) -> dict[str, object]:
    def estimate(value: Estimate) -> dict[str, float]:
        return {
            "estimate": _clean(value.point),
            "lower": _clean(value.lower),
            "standard_error": _clean(value.standard_error),
            "upper": _clean(value.upper),
        }

    return {
        "behavior_equal": item.behavior_equal,
        "cell_id": item.cell_id,
        "confidence_upper_bound": _clean(item.confidence_upper_bound),
        "contrasts": {
            "tau_A": estimate(item.contrasts.tau_a),
            "tau_B": estimate(item.contrasts.tau_b),
            "tau_C": estimate(item.contrasts.tau_c),
            "tau_T": estimate(item.contrasts.tau_t),
            "tau_V": estimate(item.contrasts.tau_v),
        },
        "direct_tau": _decision_payload(item.direct_tau),
        "ec4g": _decision_payload(item.ec4g),
        "executor_measure": _clean(item.executor_measure),
        "label_equal": item.label_equal,
        "nu": [_clean(value) for value in item.nu],
        "point_value_difference": (
            None if item.point_difference is None else _clean(item.point_difference)
        ),
        "support": item.supported,
    }


def _decision_payload(item: Decision) -> dict[str, object]:
    return {
        "action": item.action.value,
        "body_hex": item.body.hex(),
        "continuation_digest": item.digest,
        "delivery_channel": item.delivery_channel,
        "envelope_bytes_hex": item.envelope_bytes.hex(),
        "envelope_id": item.envelope_id,
        "execution_path": item.execution_path,
        "external_cost": _clean(item.external_cost),
        "receipt_variant": item.receipt_variant,
    }


def _clean(value: float) -> float:
    value = round(float(value), 12)
    return 0.0 if value == 0.0 else value


# The project-binding A1 census below is deliberately separate from the
# synthetic single-cell conformance unit above.  It never promotes the x0
# witness into the project decision domain.

PROJECT_DESIGN_ID = "EC4G-EXECUTION-DIGEST-CENSUS-D1"
PROJECT_TREATMENT_ID = "EC4G-A1-EXECUTION-DIGEST-CENSUS"
PROJECT_CANDIDATE_VERSION = "CAND-VAP-EC4G-R1@adversarial-revision-v7"
PROJECT_RESULT_SCHEMA_VERSION = 1
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_PROJECT_OBJECTS = (
    "objective_contract",
    "decision_cell_registry",
    "receipt_registry",
    "seven_arm_joint_moments",
    "cost_contract",
    "decision_parameter_registry",
    "ec4g_action_map",
    "direct_tau_action_map",
    "fallback_program_registry",
    "payload_preserving_donor_operator",
    "canonical_execution_compiler",
    "prospective_support_registry",
    "prospective_deployed_mass_registry",
    "freeze_manifest",
)


class ProjectCensusBranch(str, Enum):
    INCOMPLETE_CONTRACT = "INCOMPLETE_CONTRACT"
    SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE = (
        "SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE"
    )
    LABEL_ONLY_DIFFERENCE = "LABEL_ONLY_DIFFERENCE"
    EXECUTION_EQUIVALENT = "EXECUTION_EQUIVALENT"


@dataclass(frozen=True)
class FrozenObjectBinding:
    object_id: str
    identity: str | None
    source_locator: str | None
    frozen: bool
    total: bool
    coherent: bool
    detail: str
    affected_rows: tuple[str, ...] = ("*",)


@dataclass(frozen=True)
class ExecutionBranch:
    """One literal receipt/donor branch of a complete execution program."""

    branch_id: str
    receipt_id: str
    donor_id: str
    command: str
    command_parameters: tuple[tuple[str, str], ...]
    timing: str
    receipt_access: str
    donor_operation: str
    donor_arguments: tuple[tuple[str, str], ...]
    downstream_payload_rule: str
    fallback: str
    resources: tuple[tuple[str, str], ...]
    charged_cost: Decimal
    randomization_kernel: str

    def payload(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "charged_cost": _decimal_text(self.charged_cost),
            "command": self.command,
            "command_parameters": [list(item) for item in self.command_parameters],
            "donor_arguments": [list(item) for item in self.donor_arguments],
            "donor_id": self.donor_id,
            "donor_operation": self.donor_operation,
            "downstream_payload_rule": self.downstream_payload_rule,
            "fallback": self.fallback,
            "randomization_kernel": self.randomization_kernel,
            "receipt_access": self.receipt_access,
            "receipt_id": self.receipt_id,
            "resources": [list(item) for item in self.resources],
            "timing": self.timing,
        }


@dataclass(frozen=True)
class CanonicalExecutionProgram:
    branches: tuple[ExecutionBranch, ...]
    # A supplied digest is audit evidence only.  Exact branch equality remains
    # authoritative even when two unequal programs carry the same digest.
    supplied_digest: str | None = None

    @property
    def computed_digest(self) -> str:
        encoded = json.dumps(
            [branch.payload() for branch in self.branches],
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return hashlib.sha256(b"ec4g-a1-canonical-program-v1\x00" + encoded).hexdigest()

    def execution_equal(self, other: "CanonicalExecutionProgram") -> bool:
        return self.branches == other.branches

    def payload(self) -> dict[str, object]:
        return {
            "branches": [branch.payload() for branch in self.branches],
            "computed_digest": self.computed_digest,
            "supplied_digest": self.supplied_digest,
        }


@dataclass(frozen=True)
class ProjectCensusRow:
    row_key: str
    ec4g_label: str
    direct_tau_label: str
    ec4g_program: CanonicalExecutionProgram
    direct_tau_program: CanonicalExecutionProgram
    supported: bool
    deployed_mass: Decimal


@dataclass(frozen=True)
class ProjectCensusBinding:
    source_revision: str
    run_id: str
    object_order: tuple[str, ...]
    object_bindings: tuple[FrozenObjectBinding, ...]
    row_order: tuple[str, ...]
    rows: tuple[ProjectCensusRow, ...]


@dataclass(frozen=True)
class MissingObjectWitness:
    object_id: str
    failure: str
    detail: str
    affected_rows: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "affected_rows": list(self.affected_rows),
            "detail": self.detail,
            "failure": self.failure,
            "object_id": self.object_id,
        }


@dataclass(frozen=True)
class ProjectCensusResult:
    terminal_branch: ProjectCensusBranch
    source_revision: str
    run_id: str
    contract_complete: bool
    freeze_manifest: dict[str, object]
    object_bindings: tuple[dict[str, object], ...]
    missing_object_witnesses: tuple[MissingObjectWitness, ...]
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]
    vacuous_active_domain: bool | None
    activity_counts: dict[str, int]

    def payload(self) -> dict[str, object]:
        return {
            "activity_counts": dict(self.activity_counts),
            "candidate_version": PROJECT_CANDIDATE_VERSION,
            "contract_complete": self.contract_complete,
            "design_id": PROJECT_DESIGN_ID,
            "document_kind": "ec4g_a1_execution_digest_census_result",
            "freeze_manifest": dict(self.freeze_manifest),
            "missing_object_witnesses": [
                witness.payload() for witness in self.missing_object_witnesses
            ],
            "object_bindings": list(self.object_bindings),
            "rows": list(self.rows),
            "run_id": self.run_id,
            "schema_version": PROJECT_RESULT_SCHEMA_VERSION,
            "source_revision": self.source_revision,
            "summary": dict(self.summary),
            "terminal_branch": self.terminal_branch.value,
            "treatment_id": PROJECT_TREATMENT_ID,
            "vacuous_active_domain": self.vacuous_active_domain,
        }

    def to_bytes(self) -> bytes:
        return json.dumps(
            self.payload(), ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")


def build_registered_project_binding(
    *, source_revision: str, run_id: str
) -> ProjectCensusBinding:
    """Bind only project objects that exist at the frozen source revision.

    The current project package exposes a synthetic conformance witness but no
    registered prospective project objects.  Those absent objects remain
    explicit witnesses; this function must not manufacture decision rows from
    the synthetic predecessor.
    """

    bindings = tuple(
        FrozenObjectBinding(
            object_id=object_id,
            identity=None,
            source_locator=None,
            frozen=False,
            total=False,
            coherent=False,
            detail=(
                "no project-bound prospective object is registered at the frozen "
                "source revision; the synthetic x0 conformance unit is excluded"
            ),
        )
        for object_id in REQUIRED_PROJECT_OBJECTS
    )
    return ProjectCensusBinding(
        source_revision=source_revision,
        run_id=run_id,
        object_order=REQUIRED_PROJECT_OBJECTS,
        object_bindings=bindings,
        row_order=(),
        rows=(),
    )


def run_project_census(binding: ProjectCensusBinding) -> ProjectCensusResult:
    """Validate and classify one frozen project binding without any runtime calls."""

    witnesses = _validate_project_binding(binding)
    activity = _zero_activity_counts()
    freeze_manifest = {
        "object_order": list(binding.object_order),
        "row_order": list(binding.row_order),
        "run_id": binding.run_id,
        "source_revision": binding.source_revision,
    }
    object_evidence = tuple(_binding_payload(item) for item in binding.object_bindings)
    if witnesses:
        return ProjectCensusResult(
            terminal_branch=ProjectCensusBranch.INCOMPLETE_CONTRACT,
            source_revision=binding.source_revision,
            run_id=binding.run_id,
            contract_complete=False,
            freeze_manifest=freeze_manifest,
            object_bindings=object_evidence,
            missing_object_witnesses=witnesses,
            rows=(),
            summary={
                "N": None,
                "active_domain_mass": None,
                "active_domain_size": None,
                "behavioral_discordance_count": None,
                "D_A": None,
                "domain_checksum": None,
                "mass_checksum": None,
                "reason": "required project contract is incomplete; estimands undefined",
            },
            vacuous_active_domain=None,
            activity_counts=activity,
        )

    row_payloads: list[dict[str, object]] = []
    discordance_mass = Decimal("0")
    active_mass = Decimal("0")
    active_count = 0
    active_discordance_count = 0
    active_label_only_count = 0
    active_equivalent_count = 0
    unsupported_or_zero_difference_count = 0
    same_label_different_execution = 0
    different_label_same_execution = 0
    cross_tab: dict[str, dict[str, object]] = {}

    for row in binding.rows:
        execution_equal = row.ec4g_program.execution_equal(row.direct_tau_program)
        label_equal = row.ec4g_label == row.direct_tau_label
        positive_mass = row.deployed_mass > 0
        active = row.supported and positive_mass
        if active:
            active_count += 1
            active_mass += row.deployed_mass
        if not label_equal and execution_equal:
            different_label_same_execution += 1
        if label_equal and not execution_equal:
            same_label_different_execution += 1
        if active and not execution_equal:
            row_class = "SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE"
            row_reason = "supported positive-mass row has unequal complete programs"
            active_discordance_count += 1
            discordance_mass += row.deployed_mass
        elif active and not label_equal:
            row_class = "LABEL_ONLY_DIFFERENCE"
            row_reason = "supported positive-mass row changes label only"
            active_label_only_count += 1
        elif active:
            row_class = "EXECUTION_EQUIVALENT"
            row_reason = "supported positive-mass row agrees in label and execution"
            active_equivalent_count += 1
        else:
            row_class = "AUDIT_ONLY_OUTSIDE_ACTIVE_DOMAIN"
            row_reason = (
                "row is unsupported or has zero deployed mass and cannot promote "
                "the terminal branch"
            )
            if not execution_equal or not label_equal:
                unsupported_or_zero_difference_count += 1

        bits = (
            f"support={int(row.supported)}|positive_mass={int(positive_mass)}|"
            f"label_difference={int(not label_equal)}|"
            f"execution_difference={int(not execution_equal)}"
        )
        cell = cross_tab.setdefault(bits, {"count": 0, "mass": Decimal("0")})
        cell["count"] = int(cell["count"]) + 1
        cell["mass"] = Decimal(cell["mass"]) + row.deployed_mass

        row_payloads.append(
            {
                "active": active,
                "deployed_mass": _decimal_text(row.deployed_mass),
                "direct_tau_label": row.direct_tau_label,
                "direct_tau_program": row.direct_tau_program.payload(),
                "ec4g_label": row.ec4g_label,
                "ec4g_program": row.ec4g_program.payload(),
                "execution_difference": not execution_equal,
                "label_difference": not label_equal,
                "positive_mass": positive_mass,
                "row_class": row_class,
                "row_key": row.row_key,
                "row_reason": row_reason,
                "supported": row.supported,
                "supplied_digest_collision": (
                    not execution_equal
                    and row.ec4g_program.supplied_digest is not None
                    and row.ec4g_program.supplied_digest
                    == row.direct_tau_program.supplied_digest
                ),
            }
        )

    if discordance_mass > 0:
        terminal = ProjectCensusBranch.SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE
    elif active_label_only_count > 0:
        terminal = ProjectCensusBranch.LABEL_ONLY_DIFFERENCE
    else:
        terminal = ProjectCensusBranch.EXECUTION_EQUIVALENT

    domain_checksum = hashlib.sha256(
        json.dumps(
            list(binding.row_order),
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    mass_checksum = hashlib.sha256(
        json.dumps(
            [
                [row.row_key, _decimal_text(row.deployed_mass)]
                for row in binding.rows
            ],
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()

    return ProjectCensusResult(
        terminal_branch=terminal,
        source_revision=binding.source_revision,
        run_id=binding.run_id,
        contract_complete=True,
        freeze_manifest=freeze_manifest,
        object_bindings=object_evidence,
        missing_object_witnesses=(),
        rows=tuple(row_payloads),
        summary={
            "N": len(binding.rows),
            "active_domain_mass": _decimal_text(active_mass),
            "active_domain_size": active_count,
            "active_behavioral_discordance_count": active_discordance_count,
            "active_equivalent_count": active_equivalent_count,
            "active_label_only_count": active_label_only_count,
            "D_A": _decimal_text(discordance_mass),
            "different_label_same_execution_count": different_label_same_execution,
            "domain_checksum": domain_checksum,
            "mass_checksum": mass_checksum,
            "same_label_different_execution_count": same_label_different_execution,
            "unsupported_or_zero_mass_difference_count": (
                unsupported_or_zero_difference_count
            ),
            "cross_tab": {
                key: {
                    "count": value["count"],
                    "mass": _decimal_text(Decimal(value["mass"])),
                }
                for key, value in sorted(cross_tab.items())
            },
        },
        vacuous_active_domain=active_count == 0,
        activity_counts=activity,
    )


def _validate_project_binding(
    binding: ProjectCensusBinding,
) -> tuple[MissingObjectWitness, ...]:
    witnesses: list[MissingObjectWitness] = []
    if _REVISION_RE.fullmatch(binding.source_revision) is None:
        witnesses.append(
            MissingObjectWitness(
                "freeze_manifest",
                "INVALID_SOURCE_REVISION",
                "source_revision must be lowercase 40-hex",
                ("*",),
            )
        )
    if not binding.run_id:
        witnesses.append(
            MissingObjectWitness(
                "freeze_manifest", "MISSING_RUN_ID", "run_id must be nonempty", ("*",)
            )
        )
    if binding.object_order != REQUIRED_PROJECT_OBJECTS:
        witnesses.append(
            MissingObjectWitness(
                "freeze_manifest",
                "INVALID_OBJECT_ORDER",
                "object_order must exactly match the registered required-object order",
                ("*",),
            )
        )

    by_id: dict[str, FrozenObjectBinding] = {}
    for item in binding.object_bindings:
        if item.object_id not in REQUIRED_PROJECT_OBJECTS:
            witnesses.append(
                MissingObjectWitness(
                    item.object_id,
                    "UNREGISTERED_OBJECT_BINDING",
                    "object binding is outside the registered freeze order",
                    item.affected_rows,
                )
            )
        if item.object_id in by_id:
            witnesses.append(
                MissingObjectWitness(
                    item.object_id,
                    "DUPLICATE_OBJECT_BINDING",
                    "required object has more than one binding",
                    item.affected_rows,
                )
            )
        else:
            by_id[item.object_id] = item
    for object_id in REQUIRED_PROJECT_OBJECTS:
        item = by_id.get(object_id)
        if item is None:
            witnesses.append(
                MissingObjectWitness(
                    object_id,
                    "MISSING_OBJECT",
                    "required project object has no binding",
                    ("*",),
                )
            )
            continue
        failures = []
        if not item.identity or not item.source_locator:
            failures.append("identity/source locator absent")
        if not item.frozen:
            failures.append("object is not frozen")
        if not item.total:
            failures.append("object is non-total")
        if not item.coherent:
            failures.append("object is incoherent")
        if failures:
            witnesses.append(
                MissingObjectWitness(
                    object_id,
                    "INVALID_OR_INCOMPLETE_OBJECT",
                    f"{item.detail}; " + "; ".join(failures),
                    item.affected_rows,
                )
            )

    actual_row_order = tuple(row.row_key for row in binding.rows)
    if actual_row_order != binding.row_order or len(set(binding.row_order)) != len(
        binding.row_order
    ):
        witnesses.append(
            MissingObjectWitness(
                "decision_cell_registry",
                "ROW_ORDER_MISMATCH",
                "rows must exactly match the frozen unique row_order",
                actual_row_order or ("*",),
            )
        )
    if not binding.rows:
        witnesses.append(
            MissingObjectWitness(
                "decision_cell_registry",
                "EMPTY_DECISION_CELL_REGISTRY",
                "a complete project census requires at least one frozen decision row",
                ("*",),
            )
        )
    total_mass = Decimal("0")
    for row in binding.rows:
        if not row.row_key or not row.ec4g_label or not row.direct_tau_label:
            witnesses.append(
                MissingObjectWitness(
                    "decision_cell_registry",
                    "INVALID_ROW_IDENTITY_OR_LABEL",
                    "row key and literal labels must be nonempty",
                    (row.row_key or "<empty>",),
                )
            )
        try:
            mass = Decimal(row.deployed_mass)
        except (InvalidOperation, TypeError, ValueError):
            mass = Decimal("NaN")
        if not mass.is_finite() or mass < 0:
            witnesses.append(
                MissingObjectWitness(
                    "prospective_deployed_mass_registry",
                    "INVALID_ROW_MASS",
                    "row mass must be exact, finite and nonnegative",
                    (row.row_key,),
                )
            )
        else:
            total_mass += mass
        for side, program in (
            ("EC4G", row.ec4g_program),
            ("Direct-tau", row.direct_tau_program),
        ):
            issues = _validate_program(program)
            if issues:
                witnesses.append(
                    MissingObjectWitness(
                        "canonical_execution_compiler",
                        "INVALID_CANONICAL_PROGRAM",
                        f"{side} row {row.row_key}: " + "; ".join(issues),
                        (row.row_key,),
                    )
                )
    if total_mass != Decimal("1"):
        witnesses.append(
            MissingObjectWitness(
                "prospective_deployed_mass_registry",
                "MASS_NOT_NORMALIZED",
                f"exact total deployed mass is {_decimal_text(total_mass)}, expected 1",
                binding.row_order,
            )
        )
    return tuple(witnesses)


def _validate_program(program: CanonicalExecutionProgram) -> tuple[str, ...]:
    issues: list[str] = []
    if not program.branches:
        issues.append("complete program must contain at least one receipt/donor branch")
    branch_ids = tuple(branch.branch_id for branch in program.branches)
    if len(set(branch_ids)) != len(branch_ids) or any(not item for item in branch_ids):
        issues.append("branch ids must be nonempty and unique")
    for branch in program.branches:
        string_fields = (
            branch.receipt_id,
            branch.donor_id,
            branch.command,
            branch.timing,
            branch.receipt_access,
            branch.donor_operation,
            branch.downstream_payload_rule,
            branch.fallback,
            branch.randomization_kernel,
        )
        if any(not isinstance(value, str) or not value for value in string_fields):
            issues.append(f"branch {branch.branch_id!r} has an empty execution field")
        if not branch.charged_cost.is_finite() or branch.charged_cost < 0:
            issues.append(f"branch {branch.branch_id!r} charged_cost is invalid")
    if program.supplied_digest is not None and _DIGEST_RE.fullmatch(
        program.supplied_digest
    ) is None:
        issues.append("supplied digest must be lowercase 64-hex when present")
    return tuple(issues)


def _binding_payload(item: FrozenObjectBinding) -> dict[str, object]:
    return {
        "affected_rows": list(item.affected_rows),
        "coherent": item.coherent,
        "detail": item.detail,
        "frozen": item.frozen,
        "identity": item.identity,
        "object_id": item.object_id,
        "source_locator": item.source_locator,
        "total": item.total,
    }


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite Decimal cannot be serialized")
    normalized = value.normalize()
    text = format(normalized, "f")
    return "0" if text in {"-0", ""} else text


def _zero_activity_counts() -> dict[str, int]:
    return {
        "environment_transitions": 0,
        "learner_calls": 0,
        "model_fits": 0,
        "optimizer_updates": 0,
        "policy_calls": 0,
        "registered_census_runs": 1,
        "return_evaluations": 0,
        "trainer_calls": 0,
    }
