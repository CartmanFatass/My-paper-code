"""Frozen episode statistics and first-match analysis for UAV G0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import beta

from ha_ctse_process.uav_episode_schema import (
    GROUND_USERS,
    PHYSICAL_HORIZON,
    SERVICE_TARGET,
    Cell,
    Control,
    EpisodeMetrics,
    G0RealizationError,
)
from ha_ctse_process.uav_g0_geometry import (
    HOTSPOT_COUNT,
    RECOVERY_WINDOW_EXTENSION,
    USERS_PER_HOTSPOT,
)


QOS_RATE_THRESHOLD_MBPS = 1.0
CATASTROPHE_THRESHOLD = 0.60
CATASTROPHE_STREAK = 10

EPISODE_IDS = tuple(range(128))
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 2_026_072_901

INVALID_BRANCH = "INVALID_UAV_G0_REALIZATION"
INFEASIBLE_BRANCH = "INFEASIBLE_UAV_G0_SOURCE"
ORACLE_ONLY_BRANCH = "ORACLE_ONLY_UAV_G0_SOURCE"
NON_CAUSAL_BRANCH = "NON_CAUSAL_UAV_G0_SOURCE"
UNDERPOWERED_BRANCH = "UNDERPOWERED_UAV_G0_SOURCE"
IDENTIFIED_BRANCH = "IDENTIFIED_UAV_G0_SOURCE"
FIRST_MATCH_ORDER = (
    INVALID_BRANCH,
    INFEASIBLE_BRANCH,
    ORACLE_ONLY_BRANCH,
    NON_CAUSAL_BRANCH,
    UNDERPOWERED_BRANCH,
    IDENTIFIED_BRANCH,
)

class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    OPEN = "OPEN"

def weakest_hotspot_service_row(
    delivered_user_rates_mbps: Sequence[float],
    user_hotspots: Sequence[int],
) -> float:
    rates = np.asarray(delivered_user_rates_mbps, dtype=np.float64)
    memberships = np.asarray(user_hotspots, dtype=np.int64)
    if rates.shape != (GROUND_USERS,) or memberships.shape != (GROUND_USERS,):
        raise G0RealizationError("single delivered-rate metric row is malformed")
    if not np.isfinite(rates).all() or np.any(rates < 0.0):
        raise G0RealizationError("single delivered-rate row is nonfinite/negative")
    fractions: list[float] = []
    for hotspot in range(HOTSPOT_COUNT):
        selected = memberships == hotspot
        if int(selected.sum()) != USERS_PER_HOTSPOT:
            raise G0RealizationError("metric hotspot does not contain exactly ten users")
        fractions.append(float(np.mean(rates[selected] >= QOS_RATE_THRESHOLD_MBPS)))
    return min(fractions)


def weakest_hotspot_service(
    delivered_user_rates_mbps: np.ndarray,
    user_hotspots: Sequence[int],
) -> np.ndarray:
    rates = np.asarray(delivered_user_rates_mbps, dtype=np.float64)
    memberships = np.asarray(user_hotspots, dtype=np.int64)
    if rates.shape != (PHYSICAL_HORIZON, GROUND_USERS) or memberships.shape != (
        GROUND_USERS,
    ):
        raise G0RealizationError("delivered-rate metric inventory mismatch")
    if not np.isfinite(rates).all() or np.any(rates < 0.0):
        raise G0RealizationError("delivered-rate rows must be finite and nonnegative")
    rho = np.empty((PHYSICAL_HORIZON, HOTSPOT_COUNT), dtype=np.float64)
    for hotspot in range(HOTSPOT_COUNT):
        selected = memberships == hotspot
        if int(selected.sum()) != USERS_PER_HOTSPOT:
            raise G0RealizationError("metric hotspot does not contain exactly ten users")
        rho[:, hotspot] = np.mean(
            rates[:, selected] >= QOS_RATE_THRESHOLD_MBPS, axis=1, dtype=np.float64
        )
    return np.min(rho, axis=1)


def _has_catastrophic_streak(window_values: np.ndarray) -> bool:
    below = np.asarray(window_values, dtype=np.float64) < CATASTROPHE_THRESHOLD
    streak = 0
    for value in below:
        streak = streak + 1 if bool(value) else 0
        if streak >= CATASTROPHE_STREAK:
            return True
    return False


def compute_episode_metrics(
    weakest_service: Sequence[float],
    *,
    episode_id: int,
    control: Control | str,
    cell: Cell | str,
    onset: int,
    duration: int,
) -> EpisodeMetrics:
    service = np.asarray(weakest_service, dtype=np.float64)
    chosen_cell = Cell(cell)
    if service.shape != (PHYSICAL_HORIZON,) or not np.isfinite(service).all():
        raise G0RealizationError("weakest-hotspot service row is incomplete/nonfinite")
    if np.any(service < 0.0) or np.any(service > 1.0):
        raise G0RealizationError("weakest-hotspot service is outside [0,1]")
    if chosen_cell is Cell.EVENT:
        start = int(onset)
        stop = int(onset) + int(duration) + RECOVERY_WINDOW_EXTENSION
        if start < 0 or stop >= PHYSICAL_HORIZON:
            raise G0RealizationError("event metric window is outside H=500")
        window_mask = np.zeros(PHYSICAL_HORIZON, dtype=np.bool_)
        window_mask[start : stop + 1] = True
        window = service[window_mask]
        deficit = np.maximum(0.0, SERVICE_TARGET - window) / SERVICE_TARGET
        j_event = 1.0 - float(np.mean(deficit, dtype=np.float64))
        q_ordinary = float(np.mean(service[~window_mask], dtype=np.float64))
        m_event = float(np.min(window))
        a_control = min(j_event / SERVICE_TARGET, q_ordinary / SERVICE_TARGET)
        c_cat = int(_has_catastrophic_streak(window))
    else:
        j_event = 1.0
        q_ordinary = float(np.mean(service, dtype=np.float64))
        m_event = float(np.min(service))
        a_control = q_ordinary / SERVICE_TARGET
        c_cat = 0
    return EpisodeMetrics(
        episode_id=int(episode_id),
        control=Control(control),
        cell=chosen_cell,
        onset=int(onset),
        duration=int(duration),
        j_event=j_event,
        q_ordinary=q_ordinary,
        m_event=m_event,
        a_control=a_control,
        b_access=int(a_control >= 1.0),
        c_cat=c_cat,
    )


def make_bootstrap_index_plan() -> np.ndarray:
    indices = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED)).integers(
        0,
        len(EPISODE_IDS),
        size=(BOOTSTRAP_RESAMPLES, len(EPISODE_IDS)),
        dtype=np.int64,
    )
    return indices


def bootstrap_bounds(
    values: Sequence[float], index_plan: np.ndarray
) -> tuple[float, float, float]:
    row = np.asarray(values, dtype=np.float64)
    indices = np.asarray(index_plan, dtype=np.int64)
    if row.shape != (len(EPISODE_IDS),) or not np.isfinite(row).all():
        raise G0RealizationError("continuous estimator requires 128 finite rows")
    if indices.shape != (BOOTSTRAP_RESAMPLES, len(EPISODE_IDS)):
        raise G0RealizationError("bootstrap index matrix is not 10000x128")
    if np.any(indices < 0) or np.any(indices >= len(EPISODE_IDS)):
        raise G0RealizationError("bootstrap index is outside the episode ledger")
    means = np.mean(row[indices], axis=1, dtype=np.float64)
    ordered = np.sort(means, kind="mergesort")
    return float(np.mean(row)), float(ordered[499]), float(ordered[9499])


def clopper_pearson_one_sided(successes: int, n: int = 128) -> tuple[float, float]:
    k, total = int(successes), int(n)
    if total != len(EPISODE_IDS) or not 0 <= k <= total:
        raise G0RealizationError("Clopper-Pearson inventory must be k of n=128")
    lower = 0.0 if k == 0 else float(beta.ppf(0.05, k, total - k + 1))
    upper = 1.0 if k == total else float(beta.ppf(0.95, k + 1, total - k))
    if not (math.isfinite(lower) and math.isfinite(upper)):
        raise G0RealizationError("Clopper-Pearson bound is nonfinite")
    return lower, upper


@dataclass(frozen=True)
class EpisodeValidityRecord:
    """Primitive per-episode certificate counters and matched digests."""

    episode_id: int
    source_event_digest: str
    source_no_event_digest: str
    sameinfo_no_event_digest: str
    no_reallocation_no_event_digest: str
    geometry_support_violations: int
    rng_namespace_violations: int
    pairing_mismatches: int
    assignment_failures: int
    tracker_failures: int
    oracle_qualification_failures: int
    action_support_violations: int
    information_visibility_violations: int
    ownership_violations: int
    survivor_continuity_violations: int
    permutation_mismatches: int
    metric_reconstruction_mismatches: int
    missing_rows: int
    nonfinite_rows: int
    oracle_exact_physical_impossibility: bool = False

    def error_names(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.source_event_digest != self.source_no_event_digest:
            errors.append("event_no_event_source_pairing")
        if self.sameinfo_no_event_digest != self.no_reallocation_no_event_digest:
            errors.append("no_event_control_identity")
        counters = {
            "geometry_support": self.geometry_support_violations,
            "rng_independence": self.rng_namespace_violations,
            "pairing": self.pairing_mismatches,
            "target_assignment": self.assignment_failures,
            "target_tracker": self.tracker_failures,
            "oracle_qualification": self.oracle_qualification_failures,
            "action_support": self.action_support_violations,
            "information_visibility": self.information_visibility_violations,
            "ownership": self.ownership_violations,
            "survivor_continuity": self.survivor_continuity_violations,
            "permutation": self.permutation_mismatches,
            "metric_arithmetic": self.metric_reconstruction_mismatches,
            "row_completeness": self.missing_rows,
            "nonfinite_row": self.nonfinite_rows,
        }
        for name, value in counters.items():
            if int(value) != 0:
                errors.append(name)
        return tuple(errors)

def _cell_rows(
    rows: Mapping[tuple[Control | str, Cell | str], Sequence[EpisodeMetrics]],
    control: Control,
    cell: Cell,
) -> tuple[EpisodeMetrics, ...]:
    candidates = None
    for key, value in rows.items():
        if Control(key[0]) is control and Cell(key[1]) is cell:
            if candidates is not None:
                raise G0RealizationError("duplicate control/cell metric inventory")
            candidates = tuple(value)
    if candidates is None or len(candidates) != len(EPISODE_IDS):
        raise G0RealizationError("control/cell metric inventory is not 128 rows")
    if tuple(row.episode_id for row in candidates) != EPISODE_IDS:
        raise G0RealizationError("episode metric rows are not ordered IDs 0..127")
    if any(row.control is not control or row.cell is not cell for row in candidates):
        raise G0RealizationError("episode metric row identity mismatch")
    return candidates


def _continuous_summary(
    rows: Sequence[EpisodeMetrics],
    attribute: str,
    index_plan: np.ndarray,
) -> dict[str, float]:
    mean, lower, upper = bootstrap_bounds(
        [float(getattr(row, attribute)) for row in rows], index_plan
    )
    return {"mean": mean, "BS_L95": lower, "BS_U95": upper}


def _binary_summary(rows: Sequence[EpisodeMetrics], attribute: str) -> dict[str, float | int]:
    successes = sum(int(getattr(row, attribute)) for row in rows)
    lower, upper = clopper_pearson_one_sided(successes)
    return {"successes": successes, "n": len(EPISODE_IDS), "CP_L95": lower, "CP_U95": upper}


def _build_analysis_from_reconstructed_rows(
    metric_rows: Mapping[tuple[Control | str, Cell | str], Sequence[EpisodeMetrics]],
    validity_records: Sequence[EpisodeValidityRecord],
    *,
    index_plan: np.ndarray | None = None,
) -> dict[str, Any]:
    """Reconstruct every G0 first-match gate from episode-level evidence."""

    if len(validity_records) != len(EPISODE_IDS) or tuple(
        record.episode_id for record in validity_records
    ) != EPISODE_IDS:
        raise G0RealizationError("validity records are not ordered IDs 0..127")
    plan = make_bootstrap_index_plan() if index_plan is None else np.asarray(index_plan)
    if not np.array_equal(plan, make_bootstrap_index_plan()):
        raise G0RealizationError("bootstrap index plan differs from PCG64 seed 2026072901")
    cells = {
        (control, cell): _cell_rows(metric_rows, control, cell)
        for control in Control
        for cell in Cell
    }
    continuous: dict[str, dict[str, float]] = {}
    binary: dict[str, dict[str, float | int]] = {}
    for control in Control:
        for cell in Cell:
            key = f"{control.value}|{cell.value}"
            for prefix, attribute in (
                ("A", "a_control"),
                ("J", "j_event"),
                ("Q", "q_ordinary"),
                ("M", "m_event"),
            ):
                continuous[f"{prefix}|{key}"] = _continuous_summary(
                    cells[(control, cell)], attribute, plan
                )
            binary[f"B|{key}"] = _binary_summary(
                cells[(control, cell)], "b_access"
            )
            binary[f"C|{key}"] = _binary_summary(
                cells[(control, cell)], "c_cat"
            )
    same_event = cells[(Control.SAME_INFORMATION, Cell.EVENT)]
    none_event = cells[(Control.NO_REALLOCATION, Cell.EVENT)]
    delta_j = np.asarray(
        [left.j_event - right.j_event for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    delta_m = np.asarray(
        [left.m_event - right.m_event for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    delta_a = np.asarray(
        [left.a_control - right.a_control for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    for name, values in (("Delta_A", delta_a), ("Delta_J", delta_j), ("Delta_M", delta_m)):
        mean, lower, upper = bootstrap_bounds(values, plan)
        continuous[name] = {"mean": mean, "BS_L95": lower, "BS_U95": upper}

    def cont(control: Control, cell: Cell) -> dict[str, float]:
        return continuous[f"A|{control.value}|{cell.value}"]

    def binary_row(prefix: str, control: Control, cell: Cell) -> dict[str, float | int]:
        return binary[f"{prefix}|{control.value}|{cell.value}"]

    validity_errors = sorted(
        {error for record in validity_records for error in record.error_names()}
    )
    valid = not validity_errors
    oracle_status: GateStatus | None = None
    same_status: GateStatus | None = None
    causal_status: GateStatus | None = None
    if valid:
        oracle_pass = bool(
            cont(Control.ORACLE, Cell.EVENT)["BS_L95"] >= 1.0
            and cont(Control.ORACLE, Cell.NO_EVENT)["BS_L95"] >= 1.0
            and float(binary_row("B", Control.ORACLE, Cell.EVENT)["CP_L95"]) >= 0.90
            and float(binary_row("B", Control.ORACLE, Cell.NO_EVENT)["CP_L95"]) >= 0.90
            and all(
                record.oracle_qualification_failures == 0
                for record in validity_records
            )
        )
        oracle_fail = bool(
            cont(Control.ORACLE, Cell.EVENT)["BS_U95"] < 1.0
            or cont(Control.ORACLE, Cell.NO_EVENT)["BS_U95"] < 1.0
            or float(binary_row("B", Control.ORACLE, Cell.EVENT)["CP_U95"]) < 0.90
            or float(binary_row("B", Control.ORACLE, Cell.NO_EVENT)["CP_U95"]) < 0.90
            or any(
                record.oracle_exact_physical_impossibility
                for record in validity_records
            )
        )
        oracle_status = (
            GateStatus.FAIL
            if oracle_fail
            else GateStatus.PASS
            if oracle_pass
            else GateStatus.OPEN
        )
        if oracle_status is GateStatus.PASS:
            same_pass = bool(
                cont(Control.SAME_INFORMATION, Cell.EVENT)["BS_L95"] >= 1.0
                and cont(Control.SAME_INFORMATION, Cell.NO_EVENT)["BS_L95"] >= 1.0
                and float(
                    binary_row("B", Control.SAME_INFORMATION, Cell.EVENT)["CP_L95"]
                )
                >= 0.90
                and float(
                    binary_row("B", Control.SAME_INFORMATION, Cell.NO_EVENT)["CP_L95"]
                )
                >= 0.90
                and float(
                    binary_row("C", Control.SAME_INFORMATION, Cell.EVENT)["CP_U95"]
                )
                <= 0.05
            )
            same_fail = bool(
                cont(Control.SAME_INFORMATION, Cell.EVENT)["BS_U95"] < 1.0
                or cont(Control.SAME_INFORMATION, Cell.NO_EVENT)["BS_U95"] < 1.0
                or float(
                    binary_row("B", Control.SAME_INFORMATION, Cell.EVENT)["CP_U95"]
                )
                < 0.90
                or float(
                    binary_row("B", Control.SAME_INFORMATION, Cell.NO_EVENT)["CP_U95"]
                )
                < 0.90
                or float(
                    binary_row("C", Control.SAME_INFORMATION, Cell.EVENT)["CP_L95"]
                )
                > 0.05
            )
            same_status = (
                GateStatus.PASS
                if same_pass
                else GateStatus.FAIL
                if same_fail
                else GateStatus.OPEN
            )
            if same_status is GateStatus.PASS:
                causal_pass = bool(
                    cont(Control.NO_REALLOCATION, Cell.EVENT)["BS_U95"] < 1.0
                    and float(
                        binary_row("B", Control.NO_REALLOCATION, Cell.EVENT)["CP_U95"]
                    )
                    < 0.90
                    and continuous["Delta_J"]["BS_L95"] > 0.0
                    and continuous["Delta_M"]["mean"] >= 0.10
                    and continuous["Delta_M"]["BS_L95"] > 0.05
                )
                causal_fail = bool(
                    cont(Control.NO_REALLOCATION, Cell.EVENT)["BS_L95"] >= 1.0
                    or float(
                        binary_row("B", Control.NO_REALLOCATION, Cell.EVENT)["CP_L95"]
                    )
                    >= 0.90
                    or continuous["Delta_J"]["BS_U95"] <= 0.0
                    or continuous["Delta_M"]["mean"] < 0.10
                    or continuous["Delta_M"]["BS_U95"] <= 0.05
                )
                causal_status = (
                    GateStatus.PASS
                    if causal_pass
                    else GateStatus.FAIL
                    if causal_fail
                    else GateStatus.OPEN
                )
    branch = select_result_branch(
        valid=valid,
        oracle_status=oracle_status,
        sameinfo_status=same_status,
        causal_status=causal_status,
    )
    return {
        "continuous": continuous,
        "binary": binary,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_index_sha256": hashlib.sha256(
            np.asarray(plan, dtype=np.int64).tobytes(order="C")
        ).hexdigest(),
        "quantile_rule": "sorted_no_interpolation_x500_x9500",
        "valid": valid,
        "validity_errors": validity_errors,
        "ORACLE_STATUS": None if oracle_status is None else oracle_status.value,
        "SAMEINFO_STATUS": None if same_status is None else same_status.value,
        "CAUSAL_STATUS": None if causal_status is None else causal_status.value,
        "first_match_order": list(FIRST_MATCH_ORDER),
        "result_branch": branch,
    }


def select_result_branch(
    *,
    valid: bool,
    oracle_status: GateStatus | str | None,
    sameinfo_status: GateStatus | str | None,
    causal_status: GateStatus | str | None,
) -> str:
    if not bool(valid):
        return INVALID_BRANCH
    try:
        oracle = GateStatus(oracle_status)
    except (TypeError, ValueError) as error:
        raise G0RealizationError("ORACLE status is required at priority row 2") from error
    if oracle is GateStatus.FAIL:
        return INFEASIBLE_BRANCH
    if oracle is GateStatus.OPEN:
        return UNDERPOWERED_BRANCH
    try:
        sameinfo = GateStatus(sameinfo_status)
    except (TypeError, ValueError) as error:
        raise G0RealizationError("SAMEINFO status is required at priority row 3") from error
    if sameinfo is GateStatus.FAIL:
        return ORACLE_ONLY_BRANCH
    if sameinfo is GateStatus.OPEN:
        return UNDERPOWERED_BRANCH
    try:
        causal = GateStatus(causal_status)
    except (TypeError, ValueError) as error:
        raise G0RealizationError("CAUSAL status is required at priority row 4") from error
    if causal is GateStatus.FAIL:
        return NON_CAUSAL_BRANCH
    if causal is GateStatus.OPEN:
        return UNDERPOWERED_BRANCH
    if causal is GateStatus.PASS:
        return IDENTIFIED_BRANCH
    raise G0RealizationError("first-match status combination is contradictory")
