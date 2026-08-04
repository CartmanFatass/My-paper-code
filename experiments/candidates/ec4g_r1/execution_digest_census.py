"""Pure finite-domain EC4G-R1 versus Direct-tau D1 census.

The bundled cell is a synthetic action-map witness, never natural EC4G data.
This candidate-local module owns no environment, RNG, training, or artifact I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math

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
