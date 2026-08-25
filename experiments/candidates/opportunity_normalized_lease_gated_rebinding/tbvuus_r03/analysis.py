"""Pure, exhaustive TBVUUS r03 inference and ordered result-map formulas.

No function reads an artifact, runs the host, selects rows, or writes a result.
All claim-bearing intervals require the complete 128-pair intention-to-treat
panel.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

from .contracts import ARMS, HARD_FAILURE_KEYS, REPLICATES


T_975_DF127 = 1.97882
MEAN_MARGIN = 0.02
TAIL_MARGIN = 0.05
MEAN_SD_LIMIT = 0.080
TAIL_SD_LIMIT = 0.200
GATE_NAMES = ("AN_MEAN", "AN_TAIL", "AH_MEAN", "AH_TAIL")
GATE_STATUS_DOMAIN = (
    "PASS",
    "MATERIALITY_RULE_NONPASS",
    "SIGN_PRECISE_NONPASS",
    "SIGN_POWER_NONIDENTIFYING",
)


@dataclass(frozen=True)
class PairedInterval:
    mean: float
    sample_sd: float
    lower: float
    upper: float
    n: int


def paired_interval(differences: Sequence[float]) -> PairedInterval:
    if len(differences) != REPLICATES:
        raise ValueError("TBVUUS inference requires exactly 128 paired differences")
    values = tuple(float(value) for value in differences)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("paired differences must all be finite")
    mean = math.fsum(values) / REPLICATES
    squared = math.fsum((value - mean) ** 2 for value in values)
    sample_sd = math.sqrt(squared / (REPLICATES - 1))
    radius = T_975_DF127 * sample_sd / math.sqrt(REPLICATES)
    return PairedInterval(mean, sample_sd, mean - radius, mean + radius, REPLICATES)


def gate_status(interval: PairedInterval, *, endpoint: str) -> str:
    if interval.n != REPLICATES:
        raise ValueError("gate classification requires the complete 128-pair interval")
    if endpoint == "mean":
        margin, sd_limit = MEAN_MARGIN, MEAN_SD_LIMIT
    elif endpoint == "tail":
        margin, sd_limit = TAIL_MARGIN, TAIL_SD_LIMIT
    else:
        raise ValueError("endpoint must be mean or tail")
    if interval.mean >= margin and interval.lower > 0.0:
        return "PASS"
    if interval.mean < margin:
        return "MATERIALITY_RULE_NONPASS"
    if interval.sample_sd <= sd_limit:
        return "SIGN_PRECISE_NONPASS"
    return "SIGN_POWER_NONIDENTIFYING"


@dataclass(frozen=True)
class ReplicateEndpoints:
    mean: float
    tail: float

    def __post_init__(self) -> None:
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in (self.mean, self.tail)):
            raise ValueError("replicate endpoints must be finite values in [0,1]")


def replicate_endpoints_from_block_counts(
    block_counts: Sequence[tuple[int, int]],
) -> ReplicateEndpoints:
    """Apply the frozen 20-block pooled mean/lower-CVaR-0.10 functional."""

    if len(block_counts) != 20:
        raise ValueError("replicate endpoint requires exactly 20 paired blocks")
    values: list[float] = []
    for short_valid, long_valid in block_counts:
        if (
            isinstance(short_valid, bool)
            or isinstance(long_valid, bool)
            or not isinstance(short_valid, int)
            or not isinstance(long_valid, int)
            or short_valid not in range(33)
            or long_valid not in range(129)
        ):
            raise ValueError("block service counts exceed SHORT/LONG denominators")
        values.append((short_valid + long_valid) / 160.0)
    ordered = sorted(values)
    return ReplicateEndpoints(
        mean=math.fsum(values) / 20.0,
        tail=math.fsum(ordered[:2]) / 2.0,
    )


@dataclass(frozen=True)
class InferenceBundle:
    intervals: Mapping[str, PairedInterval]
    gate_statuses: Mapping[str, str]


def full_panel_inference(
    endpoints: Mapping[str, Sequence[ReplicateEndpoints]],
) -> InferenceBundle:
    """Compute AN/AH claim gates and descriptive AR intervals from all pairs."""

    if set(endpoints) != set(ARMS):
        raise ValueError("endpoint panel requires exactly the four frozen arms")
    if any(len(endpoints[arm]) != REPLICATES for arm in ARMS):
        raise ValueError("every arm requires exactly 128 replicate endpoints")
    road = endpoints[ARMS[3]]
    contrasts = {
        "AN_MEAN": [road[b].mean - endpoints[ARMS[0]][b].mean for b in range(REPLICATES)],
        "AN_TAIL": [road[b].tail - endpoints[ARMS[0]][b].tail for b in range(REPLICATES)],
        "AH_MEAN": [road[b].mean - endpoints[ARMS[1]][b].mean for b in range(REPLICATES)],
        "AH_TAIL": [road[b].tail - endpoints[ARMS[1]][b].tail for b in range(REPLICATES)],
        "AR_MEAN": [road[b].mean - endpoints[ARMS[2]][b].mean for b in range(REPLICATES)],
        "AR_TAIL": [road[b].tail - endpoints[ARMS[2]][b].tail for b in range(REPLICATES)],
    }
    intervals = {name: paired_interval(values) for name, values in contrasts.items()}
    statuses = {
        name: gate_status(intervals[name], endpoint="mean" if name.endswith("MEAN") else "tail")
        for name in GATE_NAMES
    }
    return InferenceBundle(intervals, statuses)


@dataclass(frozen=True)
class RoadFitAuditFacts:
    every_encounter_audited: bool
    availability_exact: bool
    tie_order_exact: bool
    selected_template_audited: bool
    patch_formula_exact: bool
    identity_fallback_exact: bool
    no_future_or_hidden_input: bool

    @property
    def valid(self) -> bool:
        return all(vars(self).values())


@dataclass(frozen=True)
class ShamValidityFacts:
    common_pre_action_state_equal: bool
    common_tapes_equal: bool
    estimator_bitwise_unchanged: bool
    waypoints_bitwise_unchanged: bool
    only_registered_shell_differences: bool
    tickwise_q_not_greater_than_never: bool
    post_blackout_equal_absent_battery_exhaustion: bool

    @property
    def valid(self) -> bool:
        return all(vars(self).values())


@dataclass(frozen=True)
class PackageValidityFacts:
    exact_identity: bool
    exact_4x128_cells: bool
    exact_20_block_balance: bool
    controller_free_pairing: bool
    no_action_word: bool
    arm_transitions_exact: bool
    ledgers_complete: bool
    raw_conformant: bool
    no_missing_duplicate_substituted_imputed_deleted_or_selected_cell: bool
    atomic_complete_package: bool
    road_fit: RoadFitAuditFacts

    @property
    def valid(self) -> bool:
        booleans = (
            self.exact_identity,
            self.exact_4x128_cells,
            self.exact_20_block_balance,
            self.controller_free_pairing,
            self.no_action_word,
            self.arm_transitions_exact,
            self.ledgers_complete,
            self.raw_conformant,
            self.no_missing_duplicate_substituted_imputed_deleted_or_selected_cell,
            self.atomic_complete_package,
            self.road_fit.valid,
        )
        return all(booleans)


@dataclass(frozen=True)
class HardSafetyFacts:
    terrain_penetrations: int = 0
    geofence_exits: int = 0
    separation_breaches: int = 0
    no_safe_control: int = 0
    no_planner_solution: int = 0
    battery_exhaustions: int = 0
    numerical_faults: int = 0

    @property
    def safe(self) -> bool:
        values = tuple(getattr(self, key) for key in HARD_FAILURE_KEYS)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
            raise ValueError("hard-safety counts must be nonnegative integers")
        return not any(values)

    def concrete_failures(self) -> tuple[str, ...]:
        _ = self.safe
        return tuple(key for key in HARD_FAILURE_KEYS if getattr(self, key) > 0)


def action_shell_support_ok(
    *, scheduled_t0_by_arm: Mapping[str, int], action_shell_by_arm: Mapping[str, int]
) -> bool:
    if set(scheduled_t0_by_arm) != set(ARMS) or set(action_shell_by_arm) != set(ARMS):
        raise ValueError("action support requires exactly the four frozen arms")
    scheduled_expected = 5120
    shell_expected = {ARMS[0]: 0, ARMS[1]: 5120, ARMS[2]: 5120, ARMS[3]: 5120}
    return all(scheduled_t0_by_arm[arm] == scheduled_expected for arm in ARMS) and all(
        action_shell_by_arm[arm] == shell_expected[arm] for arm in ARMS
    )


def effective_road_patch_support_ok(*, encounters: int, replicates_with_any: int) -> bool:
    if encounters < 0 or replicates_with_any < 0 or replicates_with_any > REPLICATES:
        raise ValueError("effective support counts are outside the frozen panel")
    return encounters >= 512 and replicates_with_any >= 96


def never_competent(
    *, package_valid: bool, hard_safety: HardSafetyFacts, mean_value: float, tail_value: float
) -> bool:
    if any(not math.isfinite(value) for value in (mean_value, tail_value)):
        raise ValueError("NEVER endpoints must be finite")
    return (
        package_valid
        and hard_safety.safe
        and mean_value >= 0.25
        and tail_value >= 0.10
        and 1.0 - mean_value >= 0.05
    )


def override_interval(
    road_override_counts: Sequence[int], never_override_counts: Sequence[int]
) -> PairedInterval:
    if len(road_override_counts) != REPLICATES or len(never_override_counts) != REPLICATES:
        raise ValueError("override audit requires 128 paired replicate counts")
    denominator = 3840
    differences: list[float] = []
    for road, never in zip(road_override_counts, never_override_counts):
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value > denominator
            for value in (road, never)
        ):
            raise ValueError("override counts exceed the 3,840-tick replicate denominator")
        differences.append((road - never) / denominator)
    return paired_interval(differences)


def road_nonharm(
    *,
    hard_safety: HardSafetyFacts,
    override_differences: Sequence[float] | None = None,
    road_override_counts: Sequence[int] | None = None,
    never_override_counts: Sequence[int] | None = None,
) -> bool:
    if override_differences is not None:
        if road_override_counts is not None or never_override_counts is not None:
            raise ValueError("provide differences or paired counts, not both")
        interval = paired_interval(override_differences)
    else:
        if road_override_counts is None or never_override_counts is None:
            raise ValueError("ROAD non-harm requires paired override facts")
        interval = override_interval(road_override_counts, never_override_counts)
    return hard_safety.safe and interval.upper <= 0.01


@dataclass(frozen=True)
class ResultMapFacts:
    package_valid: bool
    sham_valid: bool
    common_host_valid: bool
    pairing_valid: bool
    endpoint_audit_valid: bool
    common_package_nonidentification_reason: str | None
    never_is_competent: bool
    action_shell_support: bool
    effective_payload_support: bool
    road_is_nonharmful: bool
    road_nonharm_failure_fact: str | None
    gate_statuses: Mapping[str, str]


@dataclass(frozen=True)
class ResultMapOutcome:
    branch: str
    detail: str | None
    gate_statuses: Mapping[str, str]
    timing_question_portfolio_eligible: bool


def _validate_gate_vector(value: Mapping[str, str]) -> dict[str, str]:
    if set(value) != set(GATE_NAMES):
        raise ValueError("gate vector must contain exactly AN/AH mean/tail")
    if any(value[name] not in GATE_STATUS_DOMAIN for name in GATE_NAMES):
        raise ValueError("gate vector contains an unknown status")
    return {name: value[name] for name in GATE_NAMES}


def evaluate_result_map(facts: ResultMapFacts) -> ResultMapOutcome:
    """Apply the frozen first-match nine-branch map without interpretation."""

    gates = _validate_gate_vector(facts.gate_statuses)
    common_valid = all(
        (
            facts.package_valid,
            facts.sham_valid,
            facts.common_host_valid,
            facts.pairing_valid,
            facts.endpoint_audit_valid,
        )
    )
    if not common_valid:
        if not facts.common_package_nonidentification_reason:
            raise ValueError("invalid common package requires its exact reason")
        return ResultMapOutcome(
            facts.common_package_nonidentification_reason, None, gates, False
        )
    if not facts.never_is_competent:
        return ResultMapOutcome("NEVER_UPDATE_COMPARATOR_NONIDENTIFIED", None, gates, False)
    if not facts.action_shell_support or not facts.effective_payload_support:
        return ResultMapOutcome("ROAD_PATCH_ACTION_SUPPORT_NONIDENTIFIED", None, gates, False)
    if not facts.road_is_nonharmful:
        if not facts.road_nonharm_failure_fact:
            raise ValueError("failed ROAD non-harm requires the concrete physical fact")
        return ResultMapOutcome(
            "ROAD_PATCH_EXACT_PACKAGE_NONHARM_FAILED",
            facts.road_nonharm_failure_fact,
            gates,
            False,
        )
    if all(gates[name] == "PASS" for name in GATE_NAMES):
        return ResultMapOutcome("ROAD_PATCH_DIRECT_UTILITY_QUALIFIES", None, gates, True)
    if any(gates[name] == "SIGN_POWER_NONIDENTIFYING" for name in GATE_NAMES):
        return ResultMapOutcome("ROAD_PATCH_POWER_NONIDENTIFYING", None, gates, False)
    net_pass = all(gates[name] == "PASS" for name in ("AN_MEAN", "AN_TAIL"))
    payload_pass = all(gates[name] == "PASS" for name in ("AH_MEAN", "AH_TAIL"))
    if net_pass and not payload_pass:
        return ResultMapOutcome("NET_VALUE_WITHOUT_PAYLOAD_ISOLATION", None, gates, False)
    if payload_pass and not net_pass:
        return ResultMapOutcome(
            "PAYLOAD_BENEFIT_WITHOUT_MATERIAL_NET_UTILITY", None, gates, False
        )
    return ResultMapOutcome("VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS", None, gates, False)
