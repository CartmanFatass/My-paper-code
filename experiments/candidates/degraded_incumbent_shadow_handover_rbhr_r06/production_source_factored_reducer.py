"""Result-blind endpoint/accounting reducer for the 6,912 source-factored cells."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Sequence

import numpy as np

from .production_source_factored_contract import (
    CLAIM_ROWS, CLAIM_SCHEDULES, ENDPOINTS, PACKAGES, PREVALENCE_REJECTION_THRESHOLD,
    ROOT_BYTES, ROOT_COUNT, SPEEDS, TRANSACTION_BRANCHES, ClaimCoordinate,
    complete_claim_inventory,
)


SIGNS: Final = {"MEAN": 1, "TAIL": 1, "DEFICIT": -1, "DELAY": -1}
MATERIAL_MARGINS: Final = {"MEAN": 0.03, "TAIL": 0.05, "DEFICIT": 0.25, "DELAY": 0.5}
NONINFERIORITY_MARGINS: Final = {"MEAN": 0.01, "TAIL": 0.02, "DEFICIT": 0.25, "DELAY": 0.5}
class SourceFactoredReducerError(RuntimeError):
    pass


_AXES: Final = ("COPY-RETAIN", "SHADOW-COPY")
_BENEFIT_SHAPE: Final = (len(PACKAGES), len(CLAIM_SCHEDULES), len(SPEEDS), len(ENDPOINTS))
_CELL_SHAPE: Final = _BENEFIT_SHAPE[:-1]
_TYPED_TERMINAL_KIND: Final = "ALGORITHM_RUNTIME_OR_NONFINITE"
_TYPED_TERMINAL_PRODUCER_SCHEMA: Final = "DISH_R02_BRANCH_PRODUCER_TERMINAL_V1"
_TYPED_TERMINAL_PHASE: Final = "BEFORE_MEASUREMENT_AND_REDUCTION"
_TYPED_TERMINAL_STAGES: Final = ("APPLICATION_POLICY_FORWARD", "FUTURE_TICKS")


@dataclass(frozen=True)
class TypedTerminalRecord:
    """Producer-written terminal fact whose branch fixes contrast dependencies."""

    root_index: int
    package: str
    schedule: str
    speed: int
    slot: int
    branch: str
    stage: str
    kind: str
    producer_schema: str
    phase: str
    finite_worst_case_materialized: bool
    hard_event_flag: bool

    def __post_init__(self) -> None:
        ClaimCoordinate(self.root_index, self.package, self.schedule, self.speed, self.slot)
        if self.branch not in TRANSACTION_BRANCHES:
            raise ValueError("typed terminal branch differs")
        if self.stage not in _TYPED_TERMINAL_STAGES:
            raise ValueError("typed terminal stage differs")
        if self.kind != _TYPED_TERMINAL_KIND:
            raise ValueError("typed terminal kind differs")
        if (
            self.producer_schema != _TYPED_TERMINAL_PRODUCER_SCHEMA
            or self.phase != _TYPED_TERMINAL_PHASE
        ):
            raise ValueError("typed terminal producer provenance differs")
        if self.finite_worst_case_materialized is not True or self.hard_event_flag is not True:
            raise ValueError("typed terminal materialization differs")


def terminal_indicator_dependencies(records: Sequence[TypedTerminalRecord]) -> Mapping[str, bool]:
    dependencies = {
        "COPY-RETAIN": False,
        "SHADOW-COPY": False,
        "SHADOW-RETAIN-TOTAL": False,
    }
    branch_dependencies = {
        "RETAIN": ("COPY-RETAIN", "SHADOW-RETAIN-TOTAL"),
        "TRANSFER_COPY": ("COPY-RETAIN", "SHADOW-COPY", "SHADOW-RETAIN-TOTAL"),
        "TRANSFER_SHADOW": ("SHADOW-COPY", "SHADOW-RETAIN-TOTAL"),
    }
    for record in records:
        if not isinstance(record, TypedTerminalRecord):
            raise ValueError("typed terminal record differs")
        for dependency in branch_dependencies[record.branch]:
            dependencies[dependency] = True
    return dependencies


@dataclass(frozen=True)
class RootAxisIndicators:
    root_index: int
    root: bytes
    axis: str
    assignment_complete: bool
    value_indicator: int | None
    no_material_indicator: int | None
    diagnostics: tuple[str, ...]
    qualifying_witnesses: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.root_index < ROOT_COUNT:
            raise ValueError("root index differs")
        if not isinstance(self.root, bytes) or len(self.root) != ROOT_BYTES:
            raise ValueError("root bytes differ")
        if self.axis not in _AXES:
            raise ValueError("root axis differs")
        indicators = (self.value_indicator, self.no_material_indicator)
        if self.assignment_complete:
            if any(value not in (0, 1) for value in indicators) or indicators == (1, 1):
                raise ValueError("root indicators differ")
        elif indicators != (None, None):
            raise ValueError("incomplete root exposes indicators")
        if not isinstance(self.qualifying_witnesses, tuple) or any(
            not isinstance(row, tuple)
            or len(row) != 2
            or row[0] not in ENDPOINTS
            or row[1] not in SPEEDS
            for row in self.qualifying_witnesses
        ):
            raise ValueError("qualifying witness differs")
        canonical = tuple(sorted(
            set(self.qualifying_witnesses),
            key=lambda row: (ENDPOINTS.index(row[0]), SPEEDS.index(row[1])),
        ))
        if canonical != self.qualifying_witnesses or bool(canonical) != (self.value_indicator == 1):
            raise ValueError("qualifying witness differs")


def _incomplete_root(root_index: int, root: bytes, axis: str) -> RootAxisIndicators:
    return RootAxisIndicators(
        root_index=root_index,
        root=root,
        axis=axis,
        assignment_complete=False,
        value_indicator=None,
        no_material_indicator=None,
        diagnostics=("INCOMPLETE_ASSIGNMENT",),
    )


def _finite_array(value: object, shape: tuple[int, ...]) -> np.ndarray | None:
    try:
        rows = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if rows.shape != shape or not np.isfinite(rows).all():
        return None
    return rows


def reduce_root_axis(
    *,
    root_index: int,
    root: bytes,
    axis: str,
    assignment_complete: bool,
    protocol_complete: bool,
    transaction_complete: bool,
    competence: np.ndarray,
    trigger_counts: np.ndarray,
    signed_benefits: np.ndarray,
    nonharm_pass: bool,
    separation_diagnostic_pass: bool | None,
    shadow_retain_signed_benefits: np.ndarray | None = None,
    shadow_retain_nonharm_pass: bool | None = None,
    terminal_records: Sequence[TypedTerminalRecord] = (),
) -> RootAxisIndicators:
    """Reduce one complete root/axis census to the two frozen Bernoulli indicators."""

    # Validate immutable identity even when the assignment is incomplete.
    RootAxisIndicators(root_index, root, axis, False, None, None, ("INCOMPLETE_ASSIGNMENT",))
    if not (assignment_complete and protocol_complete and transaction_complete):
        return _incomplete_root(root_index, root, axis)

    competence_rows = _finite_array(competence, _CELL_SHAPE)
    trigger_rows = _finite_array(trigger_counts, _CELL_SHAPE)
    benefits = _finite_array(signed_benefits, _BENEFIT_SHAPE)
    total_benefits = None
    if axis == "SHADOW-COPY":
        total_benefits = _finite_array(shadow_retain_signed_benefits, _BENEFIT_SHAPE)
        if shadow_retain_nonharm_pass is None:
            return _incomplete_root(root_index, root, axis)
    if (
        competence_rows is None
        or trigger_rows is None
        or benefits is None
        or separation_diagnostic_pass is None
        or (axis == "SHADOW-COPY" and total_benefits is None)
    ):
        return _incomplete_root(root_index, root, axis)

    integral_triggers = np.equal(trigger_rows, np.floor(trigger_rows)).all()
    if (
        np.any((competence_rows < 0.0) | (competence_rows > 1.0))
        or not integral_triggers
        or np.any((trigger_rows < 0) | (trigger_rows > 16))
    ):
        return _incomplete_root(root_index, root, axis)

    if any(record.root_index != root_index for record in terminal_records):
        return _incomplete_root(root_index, root, axis)
    terminal_dependencies = terminal_indicator_dependencies(terminal_records)

    diagnostics: list[str] = []
    if not separation_diagnostic_pass:
        diagnostics.append("EPSILON_SEPARATION_DIAGNOSTIC_FAILED")

    common_gate = bool(
        np.all(competence_rows >= 0.85)
        and np.all((trigger_rows >= 2) & (trigger_rows <= 14))
    )
    if not common_gate:
        diagnostics.append("COMMON_GATE_FAILED")
        return RootAxisIndicators(
            root_index, root, axis, True, 0, 0, tuple(diagnostics),
        )

    if terminal_dependencies[axis]:
        diagnostics.append("TYPED_TERMINAL_HARM")
        return RootAxisIndicators(
            root_index, root, axis, True, 0, 0, tuple(diagnostics),
        )

    if not nonharm_pass:
        diagnostics.append("NONHARM_FAILURE")
        return RootAxisIndicators(
            root_index, root, axis, True, 0, 0, tuple(diagnostics),
        )

    margins = np.asarray([MATERIAL_MARGINS[name] for name in ENDPOINTS], dtype=np.float64)
    ni_margins = np.asarray([NONINFERIORITY_MARGINS[name] for name in ENDPOINTS], dtype=np.float64)
    noninferior = bool(np.all(benefits >= -ni_margins))
    within = bool(np.all((benefits > -margins) & (benefits < margins)))

    qualifying_witnesses: list[tuple[str, int]] = []
    for endpoint_index, endpoint in enumerate(ENDPOINTS):
        for speed_index, speed in enumerate(SPEEDS):
            if np.all(benefits[:, :, speed_index, endpoint_index] >= margins[endpoint_index]):
                qualifying_witnesses.append((endpoint, speed))

    value = bool(noninferior and qualifying_witnesses)
    if axis == "SHADOW-COPY":
        assert total_benefits is not None
        total_noninferior = bool(np.all(total_benefits >= -ni_margins))
        total_safe = bool(
            total_noninferior
            and shadow_retain_nonharm_pass
            and not terminal_dependencies["SHADOW-RETAIN-TOTAL"]
        )
        if not total_safe:
            diagnostics.append("SHADOW_RETAIN_TOTAL_SAFEGUARD_FAILED")
            value = False

    if not value and not within and not diagnostics:
        diagnostics.append("MIXED")
    return RootAxisIndicators(
        root_index=root_index,
        root=root,
        axis=axis,
        assignment_complete=True,
        value_indicator=int(value),
        no_material_indicator=int(within),
        diagnostics=tuple(diagnostics),
        qualifying_witnesses=tuple(qualifying_witnesses) if value else (),
    )


@dataclass(frozen=True)
class WeightingSensitivity:
    block_first_complete: bool
    event_first_complete: bool
    copy_retain_sign_or_materiality_flip: bool
    shadow_copy_sign_or_materiality_flip: bool

    @property
    def complete(self) -> bool:
        return bool(self.block_first_complete and self.event_first_complete)


@dataclass(frozen=True)
class ReplayContainmentEvidence:
    all_endpoint_rows_covered: bool
    post_cas_native_state_equal: bool
    policy_state_equal: bool
    welford_state_equal: bool
    rng_state_equal: bool
    hundred_tick_twin_equal: bool
    deadline_met: bool

    @property
    def structure_valid(self) -> bool:
        return bool(
            self.all_endpoint_rows_covered
            and self.post_cas_native_state_equal
            and self.policy_state_equal
            and self.welford_state_equal
            and self.rng_state_equal
            and self.hundred_tick_twin_equal
        )

    @property
    def complete(self) -> bool:
        return bool(self.structure_valid and self.deadline_met)


def exact_prevalence_preview(
    rows: Sequence[RootAxisIndicators],
    *,
    weighting: WeightingSensitivity,
    replay: ReplayContainmentEvidence | None = None,
) -> Mapping[str, object]:
    """Preview the frozen algebra without producing or accepting scientific evidence."""

    if not isinstance(weighting, WeightingSensitivity) or not weighting.complete:
        raise SourceFactoredReducerError("weighting sensitivity is incomplete")
    if len(rows) != ROOT_COUNT * len(_AXES) or any(
        not isinstance(row, RootAxisIndicators) for row in rows
    ):
        raise SourceFactoredReducerError("24-root Cartesian indicator inventory differs")

    inventory: dict[tuple[int, str], RootAxisIndicators] = {}
    for row in rows:
        key = (row.root_index, row.axis)
        if key in inventory:
            raise SourceFactoredReducerError("duplicate root-axis indicator")
        inventory[key] = row
    expected = {(root_index, axis) for root_index in range(ROOT_COUNT) for axis in _AXES}
    if set(inventory) != expected:
        raise SourceFactoredReducerError("24-root Cartesian indicator inventory differs")
    for root_index in range(ROOT_COUNT):
        if inventory[(root_index, _AXES[0])].root != inventory[(root_index, _AXES[1])].root:
            raise SourceFactoredReducerError("root bytes differ across axes")

    incomplete = sorted(
        {row.root_index for row in inventory.values() if not row.assignment_complete}
    )
    replay_valid = bool(replay is not None and replay.structure_valid)
    if incomplete or not replay_valid:
        reasons = []
        if incomplete:
            reasons.append("ROOT_AXIS_INCOMPLETE")
        if not replay_valid:
            reasons.append("REPLAY_INVALID_OR_INCOMPLETE")
        return {
            "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_REDUCER_PREVIEW_V2",
            "status": "TEST_ONLY_NOT_READY",
            "preview_input_status": "INCOMPLETE_ASSIGNMENT",
            "scientific_object_consumed": False,
            "prevalence_tests_executed": False,
            "scientific_tests_executed": False,
            "preview_tests_computed": False,
            "production_result_authority": False,
            "question_relevant_output": False,
            "replay_status": "INVALID_OR_INCOMPLETE",
            "incomplete_root_indices": incomplete,
            "incomplete_reasons": reasons,
            "same_root_panel_required_for_retry": True,
            "redraw_allowed": False,
        }

    counts: dict[str, dict[str, int]] = {}
    tests: dict[str, Mapping[str, object]] = {}
    axes: dict[str, Mapping[str, object]] = {}
    alpha = {"numerator": 1, "denominator": 80}
    boundary_tail = {"numerator": 190051, "denominator": 16777216}
    for axis in _AXES:
        axis_rows = [inventory[(root_index, axis)] for root_index in range(ROOT_COUNT)]
        value_count = sum(int(row.value_indicator) for row in axis_rows)
        no_material_count = sum(int(row.no_material_indicator) for row in axis_rows)
        counts[axis] = {"VALUE": value_count, "NO_MATERIAL": no_material_count}
        for claim, count in (("VALUE", value_count), ("NO_MATERIAL", no_material_count)):
            tests[f"{axis}/{claim}"] = {
                "count": count,
                "root_count": ROOT_COUNT,
                "null": "p<=1/2",
                "alpha": dict(alpha),
                "reject_when_count_at_least": PREVALENCE_REJECTION_THRESHOLD,
                "rejected": count >= PREVALENCE_REJECTION_THRESHOLD,
                "exact_null_tail": dict(boundary_tail),
            }
        if value_count >= PREVALENCE_REJECTION_THRESHOLD:
            disposition = "ROOT_PREVALENCE_VALUE"
        elif no_material_count >= PREVALENCE_REJECTION_THRESHOLD:
            disposition = "ROOT_PREVALENCE_NO_MATERIAL"
        else:
            disposition = "ROOT_PREVALENCE_UNRESOLVED"
        axes[axis] = {
            "disposition": disposition,
            "value_count": value_count,
            "no_material_count": no_material_count,
        }

    fixed_roots = []
    for root_index in range(ROOT_COUNT):
        root_axes: dict[str, Mapping[str, object]] = {}
        for axis in _AXES:
            row = inventory[(root_index, axis)]
            root_axes[axis] = {
                "value": int(row.value_indicator),
                "no_material": int(row.no_material_indicator),
                "diagnostics": list(row.diagnostics),
                "qualifying_witnesses": [list(witness) for witness in row.qualifying_witnesses],
            }
        fixed_roots.append({
            "root_index": root_index,
            "root_hex": inventory[(root_index, _AXES[0])].root.hex(),
            "axes": root_axes,
        })

    assert replay is not None
    replay_complete = replay.complete
    replay_status = "CONTAINED" if replay_complete else "RESOURCE_LIMITED"
    shadow_disposition = str(axes["SHADOW-COPY"]["disposition"])
    copy_disposition = str(axes["COPY-RETAIN"]["disposition"])
    return {
        "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_REDUCER_PREVIEW_V2",
        "status": "TEST_ONLY_NOT_READY",
        "preview_input_status": "COMPLETE_SYNTHETIC_INPUT",
        "scientific_object_consumed": False,
        "prevalence_tests_executed": False,
        "scientific_tests_executed": False,
        "preview_tests_computed": True,
        "production_result_authority": False,
        "question_relevant_output": False,
        "axes": axes,
        "combined": f"SHADOW_COPY_{shadow_disposition} + COPY_RETAIN_{copy_disposition}",
        "tests": tests,
        "counts": counts,
        "no_alpha_recycling": True,
        "familywise_error_bound": {"numerator": 190051, "denominator": 4194304},
        "planning_power_at_p_0_8": {
            "numerator": 48343602127962112,
            "denominator": 59604644775390625,
        },
        "threshold_cp_lower_98_75_percent": 0.503888100451766,
        "fixed_panel": {
            "roots": fixed_roots,
            "counts": counts,
            "weighting_sensitivity": {
                "block_first": {
                    "complete": True,
                    "prospective_weighting_rule": True,
                    "scientific_evidence_authority": False,
                },
                "event_first": {
                    "complete": True,
                    "sensitivity_only": True,
                    "scientific_evidence_authority": False,
                },
                "sign_or_materiality_flip": {
                    "COPY-RETAIN": weighting.copy_retain_sign_or_materiality_flip,
                    "SHADOW-COPY": weighting.shadow_copy_sign_or_materiality_flip,
                },
            },
            "descriptive_only": True,
            "superpopulation_mean_authority": False,
        },
        "duplicate_roots_retained": True,
        "endpoint_anchor_scope": "ROOT_LOCAL_EXISTENTIAL_MAY_VARY",
        "fixed_endpoint_anchor_prevalence_authority": False,
        "replay_scope": ["SHADOW-COPY"],
        "replay_status": replay_status,
        "replay_containment_complete": replay_complete,
        "modifiers": [
            "SHADOW_REPLAY_CONTAINED" if replay_complete
            else "SHADOW_REPLAY_RESOURCE_LIMITED"
        ],
        "shadow_claim_ceiling": (
            "NO_UNIQUE_INFORMATION_OR_NECESSITY"
            if replay_complete
            else "FIXED_RESOURCE_SOURCE_COMPATIBILITY_OR_PRECOMPUTE_ADVANTAGE_ONLY"
        ),
    }


def fractional_worst_10(values: Sequence[float]) -> float:
    rows = np.sort(np.asarray(values, dtype=np.float64))
    if rows.ndim != 1 or rows.size == 0 or not np.isfinite(rows).all():
        raise SourceFactoredReducerError("tail rows differ")
    mass = 0.1 * rows.size; whole = int(np.floor(mass)); total = float(rows[:whole].sum())
    if whole < rows.size:
        total += (mass - whole) * float(rows[whole])
    return total / mass


def recovery_delay(row: np.ndarray) -> float:
    original = np.asarray(row)
    try:
        valid = np.isfinite(original).all() and np.logical_or(original == 0, original == 1).all()
    except TypeError:
        valid = False
    if original.shape != (100,) or not valid:
        raise SourceFactoredReducerError("recovery row differs")
    service = original.astype(np.int8)
    failures = np.flatnonzero(service == 0)
    if failures.size == 0:
        return 0.0
    origin = int(failures[0])
    for tick in range(origin, 91):
        if bool(np.all(service[tick:tick + 10] == 1)):
            return 0.1 * (tick - origin)
    return 10.0


@dataclass(frozen=True)
class EndpointRows:
    service: np.ndarray

    def reduce(self) -> Mapping[str, float]:
        original = np.asarray(self.service)
        try:
            valid = np.isfinite(original).all() and np.logical_or(original == 0, original == 1).all()
        except TypeError:
            valid = False
        if original.ndim != 2 or original.shape[0] == 0 or original.shape[1] != 100 or not valid:
            raise SourceFactoredReducerError("100-tick endpoint rows differ")
        rows = original.astype(np.int8)
        fractions = rows.mean(axis=1)
        values = {
            "MEAN": float(fractions.mean()),
            "TAIL": fractional_worst_10(fractions),
            "DEFICIT": float((0.1 * (100 - rows.sum(axis=1))).mean()),
            "DELAY": float(np.mean([recovery_delay(row) for row in rows])),
        }
        if tuple(values) != ENDPOINTS:
            raise SourceFactoredReducerError("endpoint order differs")
        return values


def signed_benefit(treatment: Mapping[str, float], comparator: Mapping[str, float]) -> Mapping[str, float]:
    if set(treatment) != set(ENDPOINTS) or set(comparator) != set(ENDPOINTS):
        raise SourceFactoredReducerError("endpoint comparison inventory differs")
    return {name: SIGNS[name] * (float(treatment[name]) - float(comparator[name])) for name in ENDPOINTS}


@dataclass(frozen=True)
class NonharmObservation:
    invalid_commit_events: int
    token_gap_events: int
    dual_owner_events: int
    dual_payload_events: int
    buffer_clear_events: int
    command_slew_breach_events: int
    separation_breach_events: int
    min_separation_m: float
    energy_ratio: float
    receipt_schema_valid: bool
    extra_application_ticks: int = 0

    def passes(self) -> bool:
        return bool(
            all(value == 0 for value in (
                self.invalid_commit_events, self.token_gap_events, self.dual_owner_events,
                self.dual_payload_events, self.buffer_clear_events,
                self.command_slew_breach_events, self.separation_breach_events,
            )) and
            np.isfinite(self.min_separation_m) and self.min_separation_m >= 15.0 and
            np.isfinite(self.energy_ratio) and self.energy_ratio <= 0.03 and
            self.receipt_schema_valid and self.extra_application_ticks == 0
        )


class CompleteClaimAccounting:
    """Tracks all cells including explicit no-trigger rows; exposes no effect."""

    def __init__(self) -> None:
        self._keys = tuple(row.key() for row in complete_claim_inventory())
        self._written: dict[str, bool] = {}

    def put(self, coordinate: ClaimCoordinate, *, trigger_present: bool) -> None:
        key = coordinate.key()
        if key not in self._keys or key in self._written:
            raise SourceFactoredReducerError("claim accounting row is absent or duplicate")
        self._written[key] = bool(trigger_present)

    @property
    def complete(self) -> bool:
        return len(self._written) == CLAIM_ROWS and set(self._written) == set(self._keys)

    def seal_scaffold(self) -> Mapping[str, object]:
        if not self.complete:
            raise SourceFactoredReducerError("6,912-row claim accounting is incomplete")
        return {
            "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_ACCOUNTING_V2",
            "row_count": CLAIM_ROWS, "trigger_rows": sum(self._written.values()),
            "no_trigger_rows": CLAIM_ROWS - sum(self._written.values()),
            "no_trigger_rows_preserved": True, "result_values_exposed": False,
            "question_relevant_output": False,
        }


__all__ = [
    "CompleteClaimAccounting", "EndpointRows", "MATERIAL_MARGINS", "NONINFERIORITY_MARGINS",
    "NonharmObservation", "ReplayContainmentEvidence", "RootAxisIndicators", "SIGNS",
    "SourceFactoredReducerError", "TypedTerminalRecord", "WeightingSensitivity",
    "exact_prevalence_preview", "fractional_worst_10", "recovery_delay", "reduce_root_axis",
    "signed_benefit", "terminal_indicator_dependencies",
]
