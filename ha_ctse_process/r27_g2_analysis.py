"""Frozen R27-G2 trajectory-effect statistics and decision rules.

The collector owns replay and branch validity.  This module consumes typed,
checkpoint-level arrays derived from its per-reset NPZ files.  Axes are kept
explicit so that reset IDs remain the only independent bootstrap units.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Literal, Sequence

import numpy as np
import torch
import torch.nn.functional as F


N_RESETS = 64
N_AGENTS = 6
N_LABELS = 4
N_ACTIONS = 4
LABEL_PAIRS = tuple(combinations(range(N_LABELS), 2))
N_PAIRS = len(LABEL_PAIRS)

WINDOW_EARLY = slice(0, 10)
WINDOW_MID = slice(10, 20)
WINDOW_LATE = slice(30, 40)
H40_INDEX = 40

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEEDS = {
    "A": 27031,
    "B1": 27041,
    "B2": 27051,
    "B3": 27061,
    "C": 27071,
}

SKL_MIN = 0.02
ACTION_DISTANCE_MIN = 0.20
RHO_MIN = 0.50
HOLD_RATIO_MIN = 1.50
DECODER_SCORE_MIN = 0.40
CHANCE_ACCURACY = 0.25
FAKE_ACCURACY_MAX = 0.35
TRAIN_TEST_GAP_MAX = 0.20

MIN_VALID_RESETS = 48
MIN_PREFIX_RESETS = 14
MIN_HOLD_CELL_RESETS = 40
MIN_PAIR_RESETS = 40
MIN_B3_TRAIN_RESETS = 32
MIN_B3_VALIDATION_RESETS = 9
MIN_B3_TEST_RESETS = 9
MIN_B3_TRAIN_PREFIX = 10
MIN_B3_EVAL_PREFIX = 3

B3_FIT_SEED = 27022
B3_FAKE_LABEL_SEED = 27023
B3_LEARNING_RATE = 3e-3
B3_WEIGHT_DECAY = 1e-4
B3_MAX_STEPS = 1_000
B3_VALIDATE_EVERY = 5
B3_PATIENCE_VALIDATIONS = 20
B3_MIN_DELTA = 1e-4
B3_STANDARD_DEVIATION_FLOOR = 1e-6


class EvidenceError(ValueError):
    """Malformed or non-finite evidence that must fail closed."""


class UnderpoweredEvidenceError(EvidenceError):
    """Well-formed evidence that does not meet a registered support floor."""


@dataclass(frozen=True)
class BootstrapInterval:
    estimate: float
    lower: float
    upper: float
    reps: int
    seed: int


@dataclass(frozen=True)
class ValidityEvidence:
    passed: bool
    failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.passed and self.failures:
            raise EvidenceError("passed validity evidence cannot contain failures")
        if not self.passed and not self.failures:
            raise EvidenceError("failed validity evidence must name a failure")


@dataclass(frozen=True)
class SupportEvidence:
    """Branch support after permitted exclusions.

    ``hold_cell_present`` has shape ``[reset, 6, 4]``.  A true entry means the
    corresponding hold branch is valid.  ``pair_contrast_present`` has shape
    ``[reset, 6]`` for the six unordered label pairs and is already collapsed
    across agents; one reset contributes at most one independent unit.
    ``b3_reset_ids`` may be a stricter retained subset for decoder fitting.
    """

    reset_ids: np.ndarray
    hold_cell_present: np.ndarray
    pair_contrast_present: np.ndarray
    b3_reset_ids: np.ndarray | None = None


@dataclass(frozen=True)
class SupportResult:
    adequate: bool
    reasons: tuple[str, ...]
    valid_resets: int
    prefix_counts: tuple[int, int, int]
    hold_cell_counts: np.ndarray
    pair_counts: np.ndarray
    b3_split_counts: tuple[int, int, int]
    b3_prefix_counts: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class GateAInput:
    """Pair diagnostics with shapes ``[reset, agent, pair]``."""

    reset_ids: np.ndarray
    active_pair_skl: np.ndarray
    inactive_pair_skl: np.ndarray
    active_pair_stdmean_distance: np.ndarray


@dataclass(frozen=True)
class GateAResult:
    passed: bool
    mean_skl: float
    mean_stdmean_distance: float
    active_minus_inactive: BootstrapInterval
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateB1Input:
    """Hold-state diagnostics with shapes ``[reset, 6, 4, step, 6]``."""

    reset_ids: np.ndarray
    active_pair_skl: np.ndarray
    inactive_pair_skl: np.ndarray
    active_pair_action_distance: np.ndarray


@dataclass(frozen=True)
class B1BreadthResult:
    index: int
    passed: bool
    skl_late: float
    action_distance_late: float
    active_minus_inactive: BootstrapInterval
    rho: float


@dataclass(frozen=True)
class GateB1Result:
    passed: bool
    skl_early: float
    skl_mid: float
    skl_late: float
    action_distance_early: float
    action_distance_mid: float
    action_distance_late: float
    active_minus_inactive: BootstrapInterval
    rho: float
    agents: tuple[B1BreadthResult, ...]
    pairs: tuple[B1BreadthResult, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateB2Input:
    """Matched contrasts with shapes ``[reset, 6, 3]``.

    Each agent has exactly the three non-natural target labels.  Distances are
    the W_late means computed from deterministic actions with the frozen
    checkpoint action standardizer.
    """

    reset_ids: np.ndarray
    natural_labels: np.ndarray
    target_labels: np.ndarray
    d_hold: np.ndarray
    d_pulse: np.ndarray


@dataclass(frozen=True)
class ContrastBreadthResult:
    index: int
    passed: bool
    support_resets: int
    hold_distance: float | None
    delta: BootstrapInterval
    ratio: float


@dataclass(frozen=True)
class GateB2Result:
    passed: bool
    hold_distance: float
    delta: BootstrapInterval
    ratio: float
    agents: tuple[ContrastBreadthResult, ...]
    pairs: tuple[ContrastBreadthResult, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateB3Input:
    """Fixed hold features with shape ``[reset, 6, 4, 12]``.

    ``labels`` has shape ``[reset, 6, 4]`` and must contain each label exactly
    once inside every reset-agent group.  Reset IDs determine the frozen split.
    """

    reset_ids: np.ndarray
    features: np.ndarray
    labels: np.ndarray


@dataclass(frozen=True)
class DecoderResult:
    agent: int
    train_accuracy: float
    validation_accuracy: float
    test_accuracy: float
    test_macro_f1: float
    train_minus_test: float
    optimizer_steps: int
    validation_evaluations: int


@dataclass(frozen=True)
class GateB3Result:
    passed: bool
    accuracy: float
    macro_f1: float
    accuracy_interval: BootstrapInterval
    macro_f1_interval: BootstrapInterval
    fake_accuracy: float
    decoders: tuple[DecoderResult, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateCInput:
    """H40 matched effects with shapes ``[reset, 6, 3]``."""

    reset_ids: np.ndarray
    natural_labels: np.ndarray
    target_labels: np.ndarray
    e_hold: np.ndarray
    e_pulse: np.ndarray


@dataclass(frozen=True)
class GateCResult:
    passed: bool
    delta: BootstrapInterval
    ratio: float
    agents: tuple[ContrastBreadthResult, ...]
    pairs: tuple[ContrastBreadthResult, ...]
    reasons: tuple[str, ...]


CheckpointOutcome = Literal[
    "INVALID",
    "UNDERPOWERED",
    "INVALID_SUSPECT",
    "NO_BRANCHPOINT_STATIC_REPLICATION",
    "PERSISTENT_BEHAVIOR_AND_EFFECT",
    "PERSISTENT_ACTION_NO_EFFECT",
    "EFFECT_WITHOUT_PERSISTENT_ACTION",
    "INCONSISTENT_LABEL_MODES",
    "STATIC_CONTROL_WITHOUT_HOLD_ADVANTAGE",
    "TRANSIENT_ACTION_NUDGE",
    "NO_PERSISTENT_SEPARATION",
    "MIXED_OTHER",
]


@dataclass(frozen=True)
class CheckpointDecision:
    outcome: CheckpointOutcome
    status: Literal["PASS", "FAIL", "MIXED", "INVALID", "UNDERPOWERED"]
    gate_a: bool | None
    gate_b1: bool | None
    gate_b2: bool | None
    gate_b3: bool | None
    gate_b: bool | None
    gate_c: bool | None


FamilyOutcome = Literal[
    "INVALID",
    "UNDERPOWERED",
    "PASS_BEHAVIOR_EFFECT",
    "PASS_BEHAVIOR_NO_STABLE_EFFECT",
    "FAIL_BEHAVIOR_FAMILY",
    "MIXED_TEMPORAL_INSTABILITY",
]


@dataclass(frozen=True)
class FamilyDecision:
    outcome: FamilyOutcome
    status: Literal["PASS", "FAIL", "MIXED", "INVALID", "UNDERPOWERED"]


@dataclass(frozen=True)
class CheckpointAnalysisInput:
    validity: ValidityEvidence
    support: SupportEvidence
    gate_a: GateAInput
    gate_b1: GateB1Input
    gate_b2: GateB2Input
    gate_b3: GateB3Input
    gate_c: GateCInput
    gate_a_valid_repetition: bool = False


@dataclass(frozen=True)
class CheckpointAnalysisResult:
    support: SupportResult
    gate_a: GateAResult | None
    gate_b1: GateB1Result | None
    gate_b2: GateB2Result | None
    gate_b3: GateB3Result | None
    gate_c: GateCResult | None
    decision: CheckpointDecision


def _finite_array(name: str, value: np.ndarray, *, ndim: int | None = None) -> np.ndarray:
    array = np.asarray(value)
    if ndim is not None and array.ndim != ndim:
        raise EvidenceError(f"{name} must have {ndim} dimensions, got {array.ndim}")
    if array.size == 0:
        raise EvidenceError(f"{name} must not be empty")
    if not np.issubdtype(array.dtype, np.number):
        raise EvidenceError(f"{name} must be numeric")
    array = np.asarray(array, dtype=np.float64)
    if not np.isfinite(array).all():
        raise EvidenceError(f"{name} contains non-finite evidence")
    return array


def _reset_ids(
    value: np.ndarray,
    *,
    expected_rows: int | None = None,
    allow_empty: bool = False,
) -> np.ndarray:
    raw = np.asarray(value)
    if raw.ndim != 1 or (raw.size == 0 and not allow_empty):
        qualifier = "one-dimensional" if allow_empty else "a non-empty one-dimensional"
        raise EvidenceError(f"reset_ids must be {qualifier} array")
    if not np.issubdtype(raw.dtype, np.integer):
        if not np.issubdtype(raw.dtype, np.number) or not np.equal(raw, np.floor(raw)).all():
            raise EvidenceError("reset_ids must contain integers")
    ids = np.asarray(raw, dtype=np.int64)
    if expected_rows is not None and ids.size != int(expected_rows):
        raise EvidenceError("reset_ids do not align with evidence rows")
    if np.unique(ids).size != ids.size:
        raise EvidenceError("checkpoint evidence must contain one row per reset ID")
    if np.any((ids < 0) | (ids >= N_RESETS)):
        raise EvidenceError("R27-G2 reset IDs must be in the frozen range 0..63")
    return ids


def _positive_scale(name: str, value: np.ndarray, width: int) -> np.ndarray:
    scale = _finite_array(name, value, ndim=1)
    if scale.shape != (int(width),) or np.any(scale <= 0.0):
        raise EvidenceError(f"{name} must contain {width} finite positive values")
    return scale


def _percentile_interval(
    values: np.ndarray,
    *,
    reps: int,
    seed: int,
    statistic: Literal["mean", "median"] = "mean",
) -> BootstrapInterval:
    samples = _finite_array("bootstrap values", values, ndim=1)
    if int(reps) <= 0:
        raise EvidenceError("bootstrap reps must be positive")
    rng = np.random.default_rng(int(seed))
    indices = rng.integers(0, samples.size, size=(int(reps), samples.size))
    drawn = samples[indices]
    if statistic == "mean":
        estimates = drawn.mean(axis=1)
        estimate = float(samples.mean())
    elif statistic == "median":
        estimates = np.median(drawn, axis=1)
        estimate = float(np.median(samples))
    else:  # pragma: no cover - Literal protects ordinary callers
        raise EvidenceError(f"unsupported bootstrap statistic: {statistic}")
    return BootstrapInterval(
        estimate=estimate,
        lower=float(np.quantile(estimates, 0.025)),
        upper=float(np.quantile(estimates, 0.975)),
        reps=int(reps),
        seed=int(seed),
    )


def reset_cluster_bootstrap(
    values: np.ndarray,
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int,
    statistic: Literal["mean", "median"] = "mean",
) -> BootstrapInterval:
    """Bootstrap one already-collapsed value per distinct reset group."""

    return _percentile_interval(values, reps=int(reps), seed=int(seed), statistic=statistic)


def paired_reset_cluster_bootstrap(
    active: np.ndarray,
    inactive: np.ndarray,
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int,
) -> BootstrapInterval:
    left = _finite_array("active reset values", active, ndim=1)
    right = _finite_array("inactive reset values", inactive, ndim=1)
    if left.shape != right.shape:
        raise EvidenceError("paired bootstrap inputs must be row-aligned")
    return _percentile_interval(left - right, reps=int(reps), seed=int(seed))


def standardized_rms_distance(
    first: np.ndarray,
    second: np.ndarray,
    standard_deviation: np.ndarray,
) -> np.ndarray:
    """RMS standardized distance across the final feature dimension."""

    left = _finite_array("first", first)
    right = _finite_array("second", second)
    if left.ndim < 1 or right.ndim < 1 or left.shape[-1] != right.shape[-1]:
        raise EvidenceError("standardized distance inputs must share a final feature axis")
    try:
        left, right = np.broadcast_arrays(left, right)
    except ValueError as error:
        raise EvidenceError("standardized distance inputs are not broadcastable") from error
    scale = _positive_scale("standard_deviation", standard_deviation, left.shape[-1])
    return np.sqrt(np.mean(np.square((left - right) / scale), axis=-1))


def trajectory_distance(
    branch_actions: np.ndarray,
    reference_actions: np.ndarray,
    action_standard_deviation: np.ndarray,
    *,
    window: slice = WINDOW_LATE,
) -> np.ndarray:
    """Mean per-step standardized RMS distance over a frozen time window."""

    branch = _finite_array("branch_actions", branch_actions)
    reference = _finite_array("reference_actions", reference_actions)
    if branch.ndim < 3 or branch.shape[-1] != N_ACTIONS:
        raise EvidenceError("branch actions must end in [step, 4 actions]")
    if (
        reference.ndim == branch.ndim - 1
        and reference.shape[:-2] == branch.shape[:-3]
        and reference.shape[-2:] == branch.shape[-2:]
    ):
        reference = np.expand_dims(reference, axis=-3)
    if reference.ndim < 2 or branch.shape[-2:] != reference.shape[-2:]:
        raise EvidenceError("branch/reference action time and action axes do not align")
    distances = standardized_rms_distance(branch, reference, action_standard_deviation)
    selected = distances[..., window]
    if selected.shape[-1] != 10:
        raise EvidenceError("R27-G2 action windows must contain exactly 10 steps")
    return selected.mean(axis=-1)


def h40_effect_distance(
    branch_observation: np.ndarray,
    reference_observation: np.ndarray,
    observation_standard_deviation: np.ndarray,
) -> np.ndarray:
    """Full focal-local-observation RMS distance at H40."""

    branch = _finite_array("branch_observation", branch_observation)
    reference = _finite_array("reference_observation", reference_observation)
    if (
        reference.ndim == branch.ndim - 1
        and reference.shape[:-1] == branch.shape[:-2]
        and reference.shape[-1] == branch.shape[-1]
    ):
        reference = np.expand_dims(reference, axis=-2)
    return standardized_rms_distance(
        branch, reference, observation_standard_deviation
    )


def symmetric_kl_diag_gaussian(
    mean_a: np.ndarray,
    logstd_a: np.ndarray,
    mean_b: np.ndarray,
    logstd_b: np.ndarray,
) -> np.ndarray:
    """Symmetric KL for row-aligned diagonal Gaussian distributions."""

    ma = _finite_array("mean_a", mean_a)
    la = _finite_array("logstd_a", logstd_a)
    mb = _finite_array("mean_b", mean_b)
    lb = _finite_array("logstd_b", logstd_b)
    if not (ma.shape == la.shape == mb.shape == lb.shape) or ma.ndim < 1:
        raise EvidenceError("Gaussian means and log standard deviations must align")
    var_a = np.exp(2.0 * la)
    var_b = np.exp(2.0 * lb)
    delta_sq = np.square(ma - mb)
    kl_ab = 0.5 * np.sum(2.0 * (lb - la) + (var_a + delta_sq) / var_b - 1.0, axis=-1)
    kl_ba = 0.5 * np.sum(2.0 * (la - lb) + (var_b + delta_sq) / var_a - 1.0, axis=-1)
    result = 0.5 * (kl_ab + kl_ba)
    if not np.isfinite(result).all():
        raise EvidenceError("symmetric KL produced non-finite evidence")
    return result


def enumerated_pair_skl(means: np.ndarray, logstds: np.ndarray) -> np.ndarray:
    """Convert ``[..., label=4, action]`` diagnostics to six pair SKLs."""

    mean = _finite_array("means", means)
    logstd = _finite_array("logstds", logstds)
    if mean.shape != logstd.shape or mean.ndim < 2 or mean.shape[-2] != N_LABELS:
        raise EvidenceError("enumerated Gaussian arrays must end in [4, action]")
    return np.stack(
        [
            symmetric_kl_diag_gaussian(
                mean[..., a, :],
                logstd[..., a, :],
                mean[..., b, :],
                logstd[..., b, :],
            )
            for a, b in LABEL_PAIRS
        ],
        axis=-1,
    )


def enumerated_pair_stdmean_distance(means: np.ndarray, logstds: np.ndarray) -> np.ndarray:
    """R27-G1 pre-tanh mean distance using the first distribution's std."""

    mean = _finite_array("means", means)
    logstd = _finite_array("logstds", logstds)
    if mean.shape != logstd.shape or mean.ndim < 2 or mean.shape[-2] != N_LABELS:
        raise EvidenceError("enumerated Gaussian arrays must end in [4, action]")
    values = []
    for first, second in LABEL_PAIRS:
        scale = np.exp(logstd[..., first, :])
        values.append(np.linalg.norm((mean[..., first, :] - mean[..., second, :]) / scale, axis=-1))
    result = np.stack(values, axis=-1)
    if not np.isfinite(result).all():
        raise EvidenceError("standardized pre-tanh mean distance is non-finite")
    return result


def enumerated_pair_action_distance(
    deterministic_actions: np.ndarray,
    action_standard_deviation: np.ndarray,
) -> np.ndarray:
    """Convert ``[..., label=4, action]`` to six calibrated RMS distances."""

    action = _finite_array("deterministic_actions", deterministic_actions)
    if action.ndim < 2 or action.shape[-2:] != (N_LABELS, N_ACTIONS):
        raise EvidenceError("enumerated actions must end in [4 labels, 4 actions]")
    values = [
        standardized_rms_distance(action[..., first, :], action[..., second, :], action_standard_deviation)
        for first, second in LABEL_PAIRS
    ]
    return np.stack(values, axis=-1)


def late_action_features(actions: np.ndarray) -> np.ndarray:
    """Build the fixed 12 features from ``[..., 10, 4]`` W_late actions."""

    values = _finite_array("late actions", actions)
    if values.ndim < 2 or values.shape[-2:] != (10, N_ACTIONS):
        raise EvidenceError("late actions must end in [10 steps, 4 actions]")
    mean = values.mean(axis=-2)
    standard_deviation = values.std(axis=-2, ddof=0)
    time = np.arange(10, dtype=np.float64)
    centered_time = time - time.mean()
    time_shape = (1,) * (values.ndim - 2) + (10, 1)
    slope = np.sum(
        values * centered_time.reshape(time_shape), axis=-2
    ) / np.sum(centered_time**2)
    return np.stack((mean, standard_deviation, slope), axis=-1).reshape(values.shape[:-2] + (12,))


def _prefix_counts(reset_ids: np.ndarray) -> tuple[int, int, int]:
    return tuple(int(np.sum(reset_ids % 3 == stratum)) for stratum in range(3))


def _b3_split(
    reset_ids: np.ndarray, *, allow_empty: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ids = _reset_ids(reset_ids, allow_empty=allow_empty)
    return ids >= 24, (ids >= 12) & (ids <= 23), ids <= 11


def _b3_support_reasons(
    reset_ids: np.ndarray, *, allow_empty: bool = False
) -> tuple[str, ...]:
    ids = _reset_ids(reset_ids, allow_empty=allow_empty)
    train, validation, test = _b3_split(ids, allow_empty=allow_empty)
    masks = (train, validation, test)
    minimums = (MIN_B3_TRAIN_RESETS, MIN_B3_VALIDATION_RESETS, MIN_B3_TEST_RESETS)
    prefix_minimums = (MIN_B3_TRAIN_PREFIX, MIN_B3_EVAL_PREFIX, MIN_B3_EVAL_PREFIX)
    names = ("train", "validation", "test")
    reasons: list[str] = []
    for name, mask, minimum, prefix_minimum in zip(
        names, masks, minimums, prefix_minimums, strict=True
    ):
        count = int(mask.sum())
        if count < minimum:
            reasons.append(f"B3 {name} reset support {count} < {minimum}")
        for stratum in range(3):
            stratum_count = int(np.sum(mask & (ids % 3 == stratum)))
            if stratum_count < prefix_minimum:
                reasons.append(
                    f"B3 {name} prefix stratum {stratum} support "
                    f"{stratum_count} < {prefix_minimum}"
                )
    return tuple(reasons)


def assess_support(evidence: SupportEvidence) -> SupportResult:
    ids = _reset_ids(evidence.reset_ids, allow_empty=True)
    hold = np.asarray(evidence.hold_cell_present)
    pair = np.asarray(evidence.pair_contrast_present)
    if hold.shape != (ids.size, N_AGENTS, N_LABELS) or hold.dtype != np.bool_:
        raise EvidenceError("hold_cell_present must be bool [reset, 6, 4]")
    if pair.shape != (ids.size, N_PAIRS) or pair.dtype != np.bool_:
        raise EvidenceError("pair_contrast_present must be bool [reset, 6]")
    b3_ids = (
        ids
        if evidence.b3_reset_ids is None
        else _reset_ids(evidence.b3_reset_ids, allow_empty=True)
    )
    if not np.isin(b3_ids, ids).all():
        raise EvidenceError("B3 retained resets must be a subset of valid resets")

    prefix_counts = _prefix_counts(ids)
    hold_counts = hold.sum(axis=0, dtype=np.int64)
    pair_counts = pair.sum(axis=0, dtype=np.int64)
    train, validation, test = _b3_split(b3_ids, allow_empty=True)
    masks = (train, validation, test)
    b3_split_counts = tuple(int(mask.sum()) for mask in masks)
    b3_prefix_counts = tuple(
        tuple(int(np.sum(mask & (b3_ids % 3 == stratum))) for stratum in range(3))
        for mask in masks
    )

    reasons: list[str] = []
    if ids.size < MIN_VALID_RESETS:
        reasons.append(f"valid reset support {ids.size} < {MIN_VALID_RESETS}")
    for stratum, count in enumerate(prefix_counts):
        if count < MIN_PREFIX_RESETS:
            reasons.append(
                f"prefix stratum {stratum} support {count} < {MIN_PREFIX_RESETS}"
            )
    for agent, label in np.argwhere(hold_counts < MIN_HOLD_CELL_RESETS):
        reasons.append(
            f"hold cell agent={int(agent)} label={int(label)} support "
            f"{int(hold_counts[agent, label])} < {MIN_HOLD_CELL_RESETS}"
        )
    for pair_index in np.flatnonzero(pair_counts < MIN_PAIR_RESETS):
        reasons.append(
            f"unordered pair {LABEL_PAIRS[int(pair_index)]} reset support "
            f"{int(pair_counts[pair_index])} < {MIN_PAIR_RESETS}"
        )
    reasons.extend(_b3_support_reasons(b3_ids, allow_empty=True))
    return SupportResult(
        adequate=not reasons,
        reasons=tuple(reasons),
        valid_resets=int(ids.size),
        prefix_counts=prefix_counts,
        hold_cell_counts=hold_counts,
        pair_counts=pair_counts,
        b3_split_counts=b3_split_counts,
        b3_prefix_counts=b3_prefix_counts,
    )


def evaluate_gate_a(
    evidence: GateAInput,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> GateAResult:
    active = _finite_array("A active_pair_skl", evidence.active_pair_skl, ndim=3)
    inactive = _finite_array("A inactive_pair_skl", evidence.inactive_pair_skl, ndim=3)
    distance = _finite_array(
        "A active_pair_stdmean_distance", evidence.active_pair_stdmean_distance, ndim=3
    )
    if active.shape[1:] != (N_AGENTS, N_PAIRS):
        raise EvidenceError("Gate A pair arrays must have shape [reset, 6, 6]")
    if not (active.shape == inactive.shape == distance.shape):
        raise EvidenceError("Gate A arrays must align")
    _reset_ids(evidence.reset_ids, expected_rows=active.shape[0])
    active_reset = active.mean(axis=(1, 2))
    inactive_reset = inactive.mean(axis=(1, 2))
    interval = paired_reset_cluster_bootstrap(
        active_reset,
        inactive_reset,
        reps=int(bootstrap_reps),
        seed=BOOTSTRAP_SEEDS["A"],
    )
    mean_skl = float(active_reset.mean())
    mean_distance = float(distance.mean())
    checks = (
        (mean_skl >= SKL_MIN, f"mean SKL {mean_skl:.6g} < {SKL_MIN}"),
        (
            mean_distance >= ACTION_DISTANCE_MIN,
            f"standardized mean distance {mean_distance:.6g} < {ACTION_DISTANCE_MIN}",
        ),
        (
            interval.lower > 0.0,
            f"active-minus-inactive lower bound {interval.lower:.6g} <= 0",
        ),
    )
    reasons = tuple(reason for passed, reason in checks if not passed)
    return GateAResult(
        passed=not reasons,
        mean_skl=mean_skl,
        mean_stdmean_distance=mean_distance,
        active_minus_inactive=interval,
        reasons=reasons,
    )


def _b1_breadth(
    active_early: np.ndarray,
    active_late: np.ndarray,
    inactive_late: np.ndarray,
    action_late: np.ndarray,
    *,
    bootstrap_reps: int,
    index: int,
) -> B1BreadthResult:
    interval = paired_reset_cluster_bootstrap(
        active_late,
        inactive_late,
        reps=int(bootstrap_reps),
        seed=BOOTSTRAP_SEEDS["B1"],
    )
    skl_late = float(active_late.mean())
    distance_late = float(action_late.mean())
    rho = float(np.median(active_late / np.maximum(active_early, 1e-8)))
    passed = bool(
        skl_late >= SKL_MIN
        and distance_late >= ACTION_DISTANCE_MIN
        and interval.lower > 0.0
        and rho >= RHO_MIN
    )
    return B1BreadthResult(
        index=int(index),
        passed=passed,
        skl_late=skl_late,
        action_distance_late=distance_late,
        active_minus_inactive=interval,
        rho=rho,
    )


def evaluate_gate_b1(
    evidence: GateB1Input,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> GateB1Result:
    active = _finite_array("B1 active_pair_skl", evidence.active_pair_skl, ndim=5)
    inactive = _finite_array("B1 inactive_pair_skl", evidence.inactive_pair_skl, ndim=5)
    action = _finite_array(
        "B1 active_pair_action_distance", evidence.active_pair_action_distance, ndim=5
    )
    if not (active.shape == inactive.shape == action.shape):
        raise EvidenceError("Gate B1 arrays must align")
    if active.shape[1] != N_AGENTS or active.shape[2] != N_LABELS or active.shape[3] < 40 or active.shape[4] != N_PAIRS:
        raise EvidenceError("Gate B1 arrays must have shape [reset, 6, 4, >=40, 6]")
    _reset_ids(evidence.reset_ids, expected_rows=active.shape[0])

    def window(values: np.ndarray, selected: slice) -> np.ndarray:
        result = values[:, :, :, selected, :]
        if result.shape[3] != 10:
            raise EvidenceError("Gate B1 windows must contain exactly 10 steps")
        return result

    active_early_raw = window(active, WINDOW_EARLY)
    active_mid_raw = window(active, WINDOW_MID)
    active_late_raw = window(active, WINDOW_LATE)
    inactive_late_raw = window(inactive, WINDOW_LATE)
    action_early_raw = window(action, WINDOW_EARLY)
    action_mid_raw = window(action, WINDOW_MID)
    action_late_raw = window(action, WINDOW_LATE)

    # Checkpoint values: labels, agents, steps, and pairs collapse inside reset.
    checkpoint_axes = (1, 2, 3, 4)
    active_early = active_early_raw.mean(axis=checkpoint_axes)
    active_mid = active_mid_raw.mean(axis=checkpoint_axes)
    active_late = active_late_raw.mean(axis=checkpoint_axes)
    inactive_late = inactive_late_raw.mean(axis=checkpoint_axes)
    action_early = action_early_raw.mean(axis=checkpoint_axes)
    action_mid = action_mid_raw.mean(axis=checkpoint_axes)
    action_late = action_late_raw.mean(axis=checkpoint_axes)
    interval = paired_reset_cluster_bootstrap(
        active_late,
        inactive_late,
        reps=int(bootstrap_reps),
        seed=BOOTSTRAP_SEEDS["B1"],
    )
    rho = float(np.median(active_late / np.maximum(active_early, 1e-8)))

    # Fix agent before labels, steps, and pairs.
    agents = tuple(
        _b1_breadth(
            active_early_raw[:, agent].mean(axis=(1, 2, 3)),
            active_late_raw[:, agent].mean(axis=(1, 2, 3)),
            inactive_late_raw[:, agent].mean(axis=(1, 2, 3)),
            action_late_raw[:, agent].mean(axis=(1, 2, 3)),
            bootstrap_reps=int(bootstrap_reps),
            index=agent,
        )
        for agent in range(N_AGENTS)
    )
    # Fix unordered pair before agents, labels, and steps.
    pairs = tuple(
        _b1_breadth(
            active_early_raw[..., pair_index].mean(axis=(1, 2, 3)),
            active_late_raw[..., pair_index].mean(axis=(1, 2, 3)),
            inactive_late_raw[..., pair_index].mean(axis=(1, 2, 3)),
            action_late_raw[..., pair_index].mean(axis=(1, 2, 3)),
            bootstrap_reps=int(bootstrap_reps),
            index=pair_index,
        )
        for pair_index in range(N_PAIRS)
    )
    mean_late = float(active_late.mean())
    mean_action_late = float(action_late.mean())
    checks = (
        (mean_late >= SKL_MIN, f"late SKL {mean_late:.6g} < {SKL_MIN}"),
        (
            mean_action_late >= ACTION_DISTANCE_MIN,
            f"late action distance {mean_action_late:.6g} < {ACTION_DISTANCE_MIN}",
        ),
        (
            interval.lower > 0.0,
            f"late active-minus-inactive lower bound {interval.lower:.6g} <= 0",
        ),
        (rho >= RHO_MIN, f"median rho {rho:.6g} < {RHO_MIN}"),
        (
            sum(item.passed for item in agents) >= 4,
            f"agent breadth {sum(item.passed for item in agents)}/6 < 4/6",
        ),
        (
            sum(item.passed for item in pairs) >= 3,
            f"pair breadth {sum(item.passed for item in pairs)}/6 < 3/6",
        ),
    )
    reasons = tuple(reason for passed, reason in checks if not passed)
    return GateB1Result(
        passed=not reasons,
        skl_early=float(active_early.mean()),
        skl_mid=float(active_mid.mean()),
        skl_late=mean_late,
        action_distance_early=float(action_early.mean()),
        action_distance_mid=float(action_mid.mean()),
        action_distance_late=mean_action_late,
        active_minus_inactive=interval,
        rho=rho,
        agents=agents,
        pairs=pairs,
        reasons=reasons,
    )


def _integer_labels(name: str, value: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    raw = np.asarray(value)
    if raw.shape != shape:
        raise EvidenceError(f"{name} must have shape {shape}")
    if not np.issubdtype(raw.dtype, np.integer):
        if not np.issubdtype(raw.dtype, np.number) or not np.equal(raw, np.floor(raw)).all():
            raise EvidenceError(f"{name} must contain integers")
    labels = np.asarray(raw, dtype=np.int64)
    if np.any((labels < 0) | (labels >= N_LABELS)):
        raise EvidenceError(f"{name} contains labels outside 0..3")
    return labels


def _validate_contrasts(
    *,
    reset_ids: np.ndarray,
    natural_labels: np.ndarray,
    target_labels: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    metric_name: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    left = _finite_array(f"{metric_name} hold", first, ndim=3)
    right = _finite_array(f"{metric_name} pulse", second, ndim=3)
    if left.shape != right.shape or left.shape[1:] != (N_AGENTS, N_LABELS - 1):
        raise EvidenceError(
            f"{metric_name} contrast arrays must align as [reset, 6, 3]"
        )
    ids = _reset_ids(reset_ids, expected_rows=left.shape[0])
    natural = _integer_labels(
        f"{metric_name} natural_labels", natural_labels, (ids.size, N_AGENTS)
    )
    target = _integer_labels(
        f"{metric_name} target_labels",
        target_labels,
        (ids.size, N_AGENTS, N_LABELS - 1),
    )
    expected = set(range(N_LABELS))
    for reset_index in range(ids.size):
        for agent in range(N_AGENTS):
            values = target[reset_index, agent]
            if len(set(int(value) for value in values)) != N_LABELS - 1:
                raise EvidenceError(
                    f"{metric_name} targets must be distinct within reset-agent"
                )
            required = expected - {int(natural[reset_index, agent])}
            if set(int(value) for value in values) != required:
                raise EvidenceError(
                    f"{metric_name} targets must be exactly the three non-natural labels"
                )
    return ids, natural, target, left, right


def _contrast_pair_indices(natural: np.ndarray, target: np.ndarray) -> np.ndarray:
    lookup = {pair: index for index, pair in enumerate(LABEL_PAIRS)}
    result = np.empty(target.shape, dtype=np.int64)
    for index in np.ndindex(target.shape):
        reset_index, agent, _ = index
        pair = tuple(sorted((int(natural[reset_index, agent]), int(target[index]))))
        result[index] = lookup[pair]
    return result


def _contrast_breadth(
    hold: np.ndarray,
    pulse: np.ndarray,
    *,
    index: int,
    seed: int,
    bootstrap_reps: int,
    require_hold_distance: bool,
) -> ContrastBreadthResult:
    if hold.shape != pulse.shape or hold.ndim != 2 or hold.shape[0] == 0:
        raise EvidenceError("contrast breadth inputs must be non-empty [reset, contrast]")
    hold_reset = hold.mean(axis=1)
    delta_reset = (hold - pulse).mean(axis=1)
    ratio_reset = np.median(hold / np.maximum(pulse, 1e-6), axis=1)
    interval = reset_cluster_bootstrap(
        delta_reset, reps=int(bootstrap_reps), seed=int(seed)
    )
    hold_distance = float(hold_reset.mean()) if require_hold_distance else None
    ratio = float(np.median(ratio_reset))
    passed = bool(
        interval.lower > 0.0
        and ratio >= HOLD_RATIO_MIN
        and (not require_hold_distance or float(hold_distance) >= ACTION_DISTANCE_MIN)
    )
    return ContrastBreadthResult(
        index=int(index),
        passed=passed,
        support_resets=int(hold.shape[0]),
        hold_distance=hold_distance,
        delta=interval,
        ratio=ratio,
    )


def _pair_contrast_breadth(
    hold: np.ndarray,
    pulse: np.ndarray,
    pair_indices: np.ndarray,
    *,
    pair_index: int,
    seed: int,
    bootstrap_reps: int,
    require_hold_distance: bool,
) -> ContrastBreadthResult:
    hold_rows: list[np.ndarray] = []
    pulse_rows: list[np.ndarray] = []
    for reset_index in range(hold.shape[0]):
        selected = pair_indices[reset_index] == int(pair_index)
        if np.any(selected):
            hold_rows.append(np.asarray(hold[reset_index][selected], dtype=np.float64))
            pulse_rows.append(np.asarray(pulse[reset_index][selected], dtype=np.float64))
    if not hold_rows:
        raise UnderpoweredEvidenceError(
            f"unordered pair {LABEL_PAIRS[pair_index]} has no reset support"
        )
    # Eligible-agent multiplicity is collapsed inside each reset.  The number
    # of eligible agents can vary, so store one reset-level aggregate per row.
    hold_reset = np.asarray([row.mean() for row in hold_rows], dtype=np.float64)
    pulse_reset = np.asarray([row.mean() for row in pulse_rows], dtype=np.float64)
    interval = reset_cluster_bootstrap(
        hold_reset - pulse_reset, reps=int(bootstrap_reps), seed=int(seed)
    )
    ratio_reset = np.asarray(
        [
            np.median(h / np.maximum(p, 1e-6))
            for h, p in zip(hold_rows, pulse_rows, strict=True)
        ],
        dtype=np.float64,
    )
    hold_distance = float(hold_reset.mean()) if require_hold_distance else None
    ratio = float(np.median(ratio_reset))
    passed = bool(
        interval.lower > 0.0
        and ratio >= HOLD_RATIO_MIN
        and (not require_hold_distance or float(hold_distance) >= ACTION_DISTANCE_MIN)
    )
    return ContrastBreadthResult(
        index=int(pair_index),
        passed=passed,
        support_resets=len(hold_rows),
        hold_distance=hold_distance,
        delta=interval,
        ratio=ratio,
    )


def evaluate_gate_b2(
    evidence: GateB2Input,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> GateB2Result:
    _, natural, target, hold, pulse = _validate_contrasts(
        reset_ids=evidence.reset_ids,
        natural_labels=evidence.natural_labels,
        target_labels=evidence.target_labels,
        first=evidence.d_hold,
        second=evidence.d_pulse,
        metric_name="B2",
    )
    pair_indices = _contrast_pair_indices(natural, target)
    hold_reset = hold.mean(axis=(1, 2))
    delta_reset = (hold - pulse).mean(axis=(1, 2))
    ratio_reset = np.median(hold / np.maximum(pulse, 1e-6), axis=(1, 2))
    interval = reset_cluster_bootstrap(
        delta_reset, reps=int(bootstrap_reps), seed=BOOTSTRAP_SEEDS["B2"]
    )
    hold_distance = float(hold_reset.mean())
    ratio = float(np.median(ratio_reset))
    agents = tuple(
        _contrast_breadth(
            hold[:, agent, :],
            pulse[:, agent, :],
            index=agent,
            seed=BOOTSTRAP_SEEDS["B2"],
            bootstrap_reps=int(bootstrap_reps),
            require_hold_distance=True,
        )
        for agent in range(N_AGENTS)
    )
    pairs = tuple(
        _pair_contrast_breadth(
            hold,
            pulse,
            pair_indices,
            pair_index=pair_index,
            seed=BOOTSTRAP_SEEDS["B2"],
            bootstrap_reps=int(bootstrap_reps),
            require_hold_distance=True,
        )
        for pair_index in range(N_PAIRS)
    )
    checks = (
        (
            hold_distance >= ACTION_DISTANCE_MIN,
            f"mean hold distance {hold_distance:.6g} < {ACTION_DISTANCE_MIN}",
        ),
        (
            interval.lower > 0.0,
            f"Delta_B lower bound {interval.lower:.6g} <= 0",
        ),
        (ratio >= HOLD_RATIO_MIN, f"median R_B {ratio:.6g} < {HOLD_RATIO_MIN}"),
        (
            sum(item.passed for item in agents) >= 4,
            f"agent breadth {sum(item.passed for item in agents)}/6 < 4/6",
        ),
        (
            sum(item.passed for item in pairs) >= 3,
            f"pair breadth {sum(item.passed for item in pairs)}/6 < 3/6",
        ),
    )
    reasons = tuple(reason for passed, reason in checks if not passed)
    return GateB2Result(
        passed=not reasons,
        hold_distance=hold_distance,
        delta=interval,
        ratio=ratio,
        agents=agents,
        pairs=pairs,
        reasons=reasons,
    )


def evaluate_gate_c(
    evidence: GateCInput,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> GateCResult:
    _, natural, target, hold, pulse = _validate_contrasts(
        reset_ids=evidence.reset_ids,
        natural_labels=evidence.natural_labels,
        target_labels=evidence.target_labels,
        first=evidence.e_hold,
        second=evidence.e_pulse,
        metric_name="C",
    )
    pair_indices = _contrast_pair_indices(natural, target)
    delta_reset = (hold - pulse).mean(axis=(1, 2))
    ratio_reset = np.median(hold / np.maximum(pulse, 1e-6), axis=(1, 2))
    interval = reset_cluster_bootstrap(
        delta_reset, reps=int(bootstrap_reps), seed=BOOTSTRAP_SEEDS["C"]
    )
    ratio = float(np.median(ratio_reset))
    agents = tuple(
        _contrast_breadth(
            hold[:, agent, :],
            pulse[:, agent, :],
            index=agent,
            seed=BOOTSTRAP_SEEDS["C"],
            bootstrap_reps=int(bootstrap_reps),
            require_hold_distance=False,
        )
        for agent in range(N_AGENTS)
    )
    pairs = tuple(
        _pair_contrast_breadth(
            hold,
            pulse,
            pair_indices,
            pair_index=pair_index,
            seed=BOOTSTRAP_SEEDS["C"],
            bootstrap_reps=int(bootstrap_reps),
            require_hold_distance=False,
        )
        for pair_index in range(N_PAIRS)
    )
    checks = (
        (
            interval.lower > 0.0,
            f"Delta_C lower bound {interval.lower:.6g} <= 0",
        ),
        (ratio >= HOLD_RATIO_MIN, f"median R_C {ratio:.6g} < {HOLD_RATIO_MIN}"),
        (
            sum(item.passed for item in agents) >= 4,
            f"agent breadth {sum(item.passed for item in agents)}/6 < 4/6",
        ),
        (
            sum(item.passed for item in pairs) >= 3,
            f"pair breadth {sum(item.passed for item in pairs)}/6 < 3/6",
        ),
    )
    reasons = tuple(reason for passed, reason in checks if not passed)
    return GateCResult(
        passed=not reasons,
        delta=interval,
        ratio=ratio,
        agents=agents,
        pairs=pairs,
        reasons=reasons,
    )


@dataclass(frozen=True)
class _FitResult:
    train_prediction: np.ndarray
    validation_prediction: np.ndarray
    test_prediction: np.ndarray
    train_truth: np.ndarray
    validation_truth: np.ndarray
    test_truth: np.ndarray
    optimizer_steps: int
    validation_evaluations: int


def _accuracy(truth: np.ndarray, prediction: np.ndarray) -> float:
    left = np.asarray(truth, dtype=np.int64).reshape(-1)
    right = np.asarray(prediction, dtype=np.int64).reshape(-1)
    if left.shape != right.shape or left.size == 0:
        raise EvidenceError("classification truth and prediction must align")
    return float(np.mean(left == right))


def _macro_f1(truth: np.ndarray, prediction: np.ndarray) -> float:
    left = np.asarray(truth, dtype=np.int64).reshape(-1)
    right = np.asarray(prediction, dtype=np.int64).reshape(-1)
    if left.shape != right.shape or left.size == 0:
        raise EvidenceError("classification truth and prediction must align")
    scores: list[float] = []
    for label in range(N_LABELS):
        true_positive = int(np.sum((left == label) & (right == label)))
        false_positive = int(np.sum((left != label) & (right == label)))
        false_negative = int(np.sum((left == label) & (right != label)))
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(0.0 if denominator == 0 else 2.0 * true_positive / denominator)
    return float(np.mean(scores))


def _fit_linear_decoder(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    validation_features: np.ndarray,
    validation_labels: np.ndarray,
    test_features: np.ndarray,
    test_labels: np.ndarray,
    *,
    device: str | torch.device = "cpu",
) -> _FitResult:
    train_x = _finite_array("B3 train features", train_features, ndim=2)
    validation_x = _finite_array("B3 validation features", validation_features, ndim=2)
    test_x = _finite_array("B3 test features", test_features, ndim=2)
    if train_x.shape[1] != 12 or validation_x.shape[1] != 12 or test_x.shape[1] != 12:
        raise EvidenceError("B3 decoder features must have width 12")
    train_y = _integer_labels("B3 train labels", train_labels, (train_x.shape[0],))
    validation_y = _integer_labels(
        "B3 validation labels", validation_labels, (validation_x.shape[0],)
    )
    test_y = _integer_labels("B3 test labels", test_labels, (test_x.shape[0],))

    feature_mean = train_x.mean(axis=0, dtype=np.float64)
    feature_std = np.maximum(
        train_x.std(axis=0, ddof=0, dtype=np.float64),
        B3_STANDARD_DEVIATION_FLOOR,
    )

    target_device = torch.device(device)
    if target_device.type not in {"cpu", "cuda"}:
        raise EvidenceError(f"unsupported B3 decoder device: {target_device}")
    if target_device.type == "cuda" and not torch.cuda.is_available():
        raise EvidenceError("B3 decoder requested CUDA but CUDA is unavailable")

    def tensor(values: np.ndarray) -> torch.Tensor:
        standardized = (values - feature_mean) / feature_std
        if not np.isfinite(standardized).all():
            raise EvidenceError("B3 train-only feature standardization is non-finite")
        return torch.as_tensor(
            standardized, dtype=torch.float32, device=target_device
        )

    train_tensor = tensor(train_x)
    validation_tensor = tensor(validation_x)
    test_tensor = tensor(test_x)
    train_target = torch.as_tensor(
        train_y, dtype=torch.long, device=target_device
    )
    validation_target = torch.as_tensor(
        validation_y, dtype=torch.long, device=target_device
    )

    # Every active/fake and per-agent fit starts from the exact registered seed.
    # fork_rng prevents analysis from perturbing collector or caller RNG state.
    fork_devices: list[int] = []
    if target_device.type == "cuda":
        fork_devices = [
            torch.cuda.current_device()
            if target_device.index is None
            else int(target_device.index)
        ]
    with torch.random.fork_rng(devices=fork_devices):
        torch.manual_seed(B3_FIT_SEED)
        if fork_devices:
            torch.cuda.manual_seed_all(B3_FIT_SEED)
        model = torch.nn.Linear(12, N_LABELS).to(target_device)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=B3_LEARNING_RATE,
            weight_decay=B3_WEIGHT_DECAY,
        )
        best_loss = float("inf")
        best_state: dict[str, torch.Tensor] | None = None
        stale_validations = 0
        validation_evaluations = 0
        optimizer_steps = 0
        for step in range(1, B3_MAX_STEPS + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(train_tensor), train_target)
            if not bool(torch.isfinite(loss).item()):
                raise EvidenceError("B3 decoder produced non-finite training loss")
            loss.backward()
            optimizer.step()
            optimizer_steps = step
            if step % B3_VALIDATE_EVERY != 0:
                continue
            model.eval()
            with torch.no_grad():
                validation_loss = float(
                    F.cross_entropy(model(validation_tensor), validation_target).item()
                )
            if not np.isfinite(validation_loss):
                raise EvidenceError("B3 decoder produced non-finite validation loss")
            validation_evaluations += 1
            if validation_loss < best_loss - B3_MIN_DELTA:
                best_loss = validation_loss
                best_state = {
                    name: value.detach().clone()
                    for name, value in model.state_dict().items()
                }
                stale_validations = 0
            else:
                stale_validations += 1
            if stale_validations >= B3_PATIENCE_VALIDATIONS:
                break
        if best_state is None:
            raise EvidenceError("B3 decoder never produced a valid validation state")
        model.load_state_dict(best_state, strict=True)
        model.eval()
        with torch.no_grad():
            train_prediction = model(train_tensor).argmax(dim=1).cpu().numpy()
            validation_prediction = model(validation_tensor).argmax(dim=1).cpu().numpy()
            test_prediction = model(test_tensor).argmax(dim=1).cpu().numpy()
    return _FitResult(
        train_prediction=np.asarray(train_prediction, dtype=np.int64),
        validation_prediction=np.asarray(validation_prediction, dtype=np.int64),
        test_prediction=np.asarray(test_prediction, dtype=np.int64),
        train_truth=train_y,
        validation_truth=validation_y,
        test_truth=test_y,
        optimizer_steps=int(optimizer_steps),
        validation_evaluations=int(validation_evaluations),
    )


def _classification_bootstrap(
    truth_by_reset: np.ndarray,
    prediction_by_reset: np.ndarray,
    *,
    reps: int,
    seed: int,
) -> tuple[BootstrapInterval, BootstrapInterval]:
    truth = np.asarray(truth_by_reset, dtype=np.int64)
    prediction = np.asarray(prediction_by_reset, dtype=np.int64)
    if truth.shape != prediction.shape or truth.ndim != 2 or truth.shape[0] == 0:
        raise EvidenceError("B3 reset-grouped truth and prediction must align")
    if int(reps) <= 0:
        raise EvidenceError("bootstrap reps must be positive")
    rng = np.random.default_rng(int(seed))
    sampled_indices = rng.integers(0, truth.shape[0], size=(int(reps), truth.shape[0]))
    sampled_truth = truth[sampled_indices].reshape(int(reps), -1)
    sampled_prediction = prediction[sampled_indices].reshape(int(reps), -1)
    accuracy_samples = np.mean(sampled_truth == sampled_prediction, axis=1)
    macro_f1_samples = np.asarray(
        [
            _macro_f1(sampled_truth[index], sampled_prediction[index])
            for index in range(int(reps))
        ],
        dtype=np.float64,
    )
    accuracy = _accuracy(truth, prediction)
    macro_f1 = _macro_f1(truth, prediction)
    return (
        BootstrapInterval(
            estimate=accuracy,
            lower=float(np.quantile(accuracy_samples, 0.025)),
            upper=float(np.quantile(accuracy_samples, 0.975)),
            reps=int(reps),
            seed=int(seed),
        ),
        BootstrapInterval(
            estimate=macro_f1,
            lower=float(np.quantile(macro_f1_samples, 0.025)),
            upper=float(np.quantile(macro_f1_samples, 0.975)),
            reps=int(reps),
            seed=int(seed),
        ),
    )


def evaluate_gate_b3(
    evidence: GateB3Input,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    device: str | torch.device = "cpu",
) -> GateB3Result:
    features = _finite_array("B3 features", evidence.features, ndim=4)
    if features.shape[1:] != (N_AGENTS, N_LABELS, 12):
        raise EvidenceError("B3 features must have shape [reset, 6, 4, 12]")
    ids = _reset_ids(evidence.reset_ids, expected_rows=features.shape[0])
    labels = _integer_labels(
        "B3 labels", evidence.labels, (ids.size, N_AGENTS, N_LABELS)
    )
    for reset_index in range(ids.size):
        for agent in range(N_AGENTS):
            if set(int(value) for value in labels[reset_index, agent]) != set(range(N_LABELS)):
                raise EvidenceError("B3 labels must contain each class once per reset-agent")
    support_reasons = _b3_support_reasons(ids)
    if support_reasons:
        raise UnderpoweredEvidenceError("; ".join(support_reasons))

    # Canonical reset ordering makes seed-27023 fake permutations independent
    # of filesystem/manifest order.
    order = np.argsort(ids)
    ids = ids[order]
    features = features[order]
    labels = labels[order]
    train_mask, validation_mask, test_mask = _b3_split(ids)
    fake_labels = labels.copy()
    fake_rng = np.random.default_rng(B3_FAKE_LABEL_SEED)
    for reset_index in range(ids.size):
        for agent in range(N_AGENTS):
            fake_labels[reset_index, agent] = fake_rng.permutation(
                labels[reset_index, agent]
            )

    active_test_predictions: list[np.ndarray] = []
    active_test_truth: list[np.ndarray] = []
    fake_test_predictions: list[np.ndarray] = []
    decoder_results: list[DecoderResult] = []
    for agent in range(N_AGENTS):
        active_fit = _fit_linear_decoder(
            features[train_mask, agent].reshape(-1, 12),
            labels[train_mask, agent].reshape(-1),
            features[validation_mask, agent].reshape(-1, 12),
            labels[validation_mask, agent].reshape(-1),
            features[test_mask, agent].reshape(-1, 12),
            labels[test_mask, agent].reshape(-1),
            device=device,
        )
        fake_fit = _fit_linear_decoder(
            features[train_mask, agent].reshape(-1, 12),
            fake_labels[train_mask, agent].reshape(-1),
            features[validation_mask, agent].reshape(-1, 12),
            fake_labels[validation_mask, agent].reshape(-1),
            features[test_mask, agent].reshape(-1, 12),
            fake_labels[test_mask, agent].reshape(-1),
            device=device,
        )
        train_accuracy = _accuracy(active_fit.train_truth, active_fit.train_prediction)
        validation_accuracy = _accuracy(
            active_fit.validation_truth, active_fit.validation_prediction
        )
        test_accuracy = _accuracy(active_fit.test_truth, active_fit.test_prediction)
        test_macro_f1 = _macro_f1(active_fit.test_truth, active_fit.test_prediction)
        decoder_results.append(
            DecoderResult(
                agent=agent,
                train_accuracy=train_accuracy,
                validation_accuracy=validation_accuracy,
                test_accuracy=test_accuracy,
                test_macro_f1=test_macro_f1,
                train_minus_test=train_accuracy - test_accuracy,
                optimizer_steps=active_fit.optimizer_steps,
                validation_evaluations=active_fit.validation_evaluations,
            )
        )
        active_test_predictions.append(
            active_fit.test_prediction.reshape(int(test_mask.sum()), N_LABELS)
        )
        active_test_truth.append(
            active_fit.test_truth.reshape(int(test_mask.sum()), N_LABELS)
        )
        fake_test_predictions.append(
            fake_fit.test_prediction.reshape(int(test_mask.sum()), N_LABELS)
        )

    # Stack as [test reset, agent, label-row], yielding exactly 24 rows/reset.
    truth_by_reset = np.stack(active_test_truth, axis=1).reshape(int(test_mask.sum()), -1)
    prediction_by_reset = np.stack(active_test_predictions, axis=1).reshape(
        int(test_mask.sum()), -1
    )
    fake_prediction_by_reset = np.stack(fake_test_predictions, axis=1).reshape(
        int(test_mask.sum()), -1
    )
    # Fake truth is its independently permuted target mapping, not active truth.
    fake_truth_by_reset = fake_labels[test_mask].reshape(int(test_mask.sum()), -1)
    accuracy_interval, macro_f1_interval = _classification_bootstrap(
        truth_by_reset,
        prediction_by_reset,
        reps=int(bootstrap_reps),
        seed=BOOTSTRAP_SEEDS["B3"],
    )
    accuracy = accuracy_interval.estimate
    macro_f1 = macro_f1_interval.estimate
    fake_accuracy = _accuracy(fake_truth_by_reset, fake_prediction_by_reset)
    checks = (
        (accuracy >= DECODER_SCORE_MIN, f"accuracy {accuracy:.6g} < {DECODER_SCORE_MIN}"),
        (macro_f1 >= DECODER_SCORE_MIN, f"macro-F1 {macro_f1:.6g} < {DECODER_SCORE_MIN}"),
        (
            accuracy_interval.lower > CHANCE_ACCURACY,
            f"accuracy lower bound {accuracy_interval.lower:.6g} <= {CHANCE_ACCURACY}",
        ),
        (
            sum(item.test_accuracy >= DECODER_SCORE_MIN for item in decoder_results) >= 4,
            "fewer than four per-agent decoders reach test accuracy 0.40",
        ),
        (
            fake_accuracy <= FAKE_ACCURACY_MAX,
            f"fake-label accuracy {fake_accuracy:.6g} > {FAKE_ACCURACY_MAX}",
        ),
        (
            all(item.train_minus_test <= TRAIN_TEST_GAP_MAX for item in decoder_results),
            f"at least one train-test gap exceeds {TRAIN_TEST_GAP_MAX}",
        ),
    )
    reasons = tuple(reason for passed, reason in checks if not passed)
    return GateB3Result(
        passed=not reasons,
        accuracy=accuracy,
        macro_f1=macro_f1,
        accuracy_interval=accuracy_interval,
        macro_f1_interval=macro_f1_interval,
        fake_accuracy=fake_accuracy,
        decoders=tuple(decoder_results),
        reasons=reasons,
    )


def classify_checkpoint(
    *,
    validity: ValidityEvidence,
    support: SupportResult,
    gate_a: GateAResult | None = None,
    gate_b1: GateB1Result | None = None,
    gate_b2: GateB2Result | None = None,
    gate_b3: GateB3Result | None = None,
    gate_c: GateCResult | None = None,
    gate_a_valid_repetition: bool = False,
) -> CheckpointDecision:
    """Apply the frozen checkpoint precedence without metric disjunctions."""

    if not validity.passed:
        return CheckpointDecision(
            outcome="INVALID",
            status="INVALID",
            gate_a=None,
            gate_b1=None,
            gate_b2=None,
            gate_b3=None,
            gate_b=None,
            gate_c=None,
        )
    if not support.adequate:
        return CheckpointDecision(
            outcome="UNDERPOWERED",
            status="UNDERPOWERED",
            gate_a=None,
            gate_b1=None,
            gate_b2=None,
            gate_b3=None,
            gate_b=None,
            gate_c=None,
        )
    if gate_a is None:
        raise EvidenceError("valid, adequately powered classification requires Gate A")
    if not gate_a.passed:
        if gate_a_valid_repetition:
            outcome: CheckpointOutcome = "NO_BRANCHPOINT_STATIC_REPLICATION"
            status: Literal["PASS", "FAIL", "MIXED", "INVALID", "UNDERPOWERED"] = "FAIL"
        else:
            outcome = "INVALID_SUSPECT"
            status = "INVALID"
        return CheckpointDecision(
            outcome=outcome,
            status=status,
            gate_a=False,
            gate_b1=None,
            gate_b2=None,
            gate_b3=None,
            gate_b=None,
            gate_c=None,
        )
    if gate_b1 is None or gate_b2 is None or gate_b3 is None or gate_c is None:
        raise EvidenceError("passing Gate A requires complete B1/B2/B3/C evidence")

    b1 = bool(gate_b1.passed)
    b2 = bool(gate_b2.passed)
    b3 = bool(gate_b3.passed)
    b = b1 and b2 and b3
    c = bool(gate_c.passed)
    if b and c:
        outcome = "PERSISTENT_BEHAVIOR_AND_EFFECT"
        status = "PASS"
    elif b:
        outcome = "PERSISTENT_ACTION_NO_EFFECT"
        status = "PASS"
    elif c:
        outcome = "EFFECT_WITHOUT_PERSISTENT_ACTION"
        status = "MIXED"
    elif b1 and b2 and not b3:
        outcome = "INCONSISTENT_LABEL_MODES"
        status = "MIXED"
    elif b1 and not b2:
        outcome = "STATIC_CONTROL_WITHOUT_HOLD_ADVANTAGE"
        status = "MIXED"
    else:
        all_fail = not b1 and not b2 and not b3 and not c
        exact_transient = bool(
            all_fail
            and gate_b1.rho < RHO_MIN
            and gate_b2.delta.lower <= 0.0
            and gate_b2.ratio < HOLD_RATIO_MIN
            and gate_b3.accuracy <= FAKE_ACCURACY_MAX
            and gate_b3.macro_f1 <= FAKE_ACCURACY_MAX
            and gate_b3.accuracy_interval.lower <= CHANCE_ACCURACY
        )
        if exact_transient:
            outcome = "TRANSIENT_ACTION_NUDGE"
            status = "FAIL"
        elif all_fail:
            outcome = "NO_PERSISTENT_SEPARATION"
            status = "FAIL"
        else:
            outcome = "MIXED_OTHER"
            status = "MIXED"
    return CheckpointDecision(
        outcome=outcome,
        status=status,
        gate_a=True,
        gate_b1=b1,
        gate_b2=b2,
        gate_b3=b3,
        gate_b=b,
        gate_c=c,
    )


def classify_family(decisions: Sequence[CheckpointDecision]) -> FamilyDecision:
    """Apply the registered two-of-three temporal family rule."""

    values = tuple(decisions)
    if len(values) != 3:
        raise EvidenceError("R27-G2 family classification requires exactly three checkpoints")
    if any(item.outcome in {"INVALID", "INVALID_SUSPECT"} for item in values):
        return FamilyDecision(outcome="INVALID", status="INVALID")
    if any(item.outcome == "UNDERPOWERED" for item in values):
        return FamilyDecision(outcome="UNDERPOWERED", status="UNDERPOWERED")
    behavior_count = sum(item.gate_b is True for item in values)
    behavior_effect_count = sum(
        item.gate_b is True and item.gate_c is True for item in values
    )
    if behavior_effect_count >= 2:
        return FamilyDecision(outcome="PASS_BEHAVIOR_EFFECT", status="PASS")
    if behavior_count >= 2:
        return FamilyDecision(
            outcome="PASS_BEHAVIOR_NO_STABLE_EFFECT", status="PASS"
        )
    fail_outcomes = {
        "TRANSIENT_ACTION_NUDGE",
        "NO_PERSISTENT_SEPARATION",
        "NO_BRANCHPOINT_STATIC_REPLICATION",
    }
    if sum(item.outcome in fail_outcomes for item in values) >= 2:
        return FamilyDecision(outcome="FAIL_BEHAVIOR_FAMILY", status="FAIL")
    return FamilyDecision(outcome="MIXED_TEMPORAL_INSTABILITY", status="MIXED")


def analyze_checkpoint(
    evidence: CheckpointAnalysisInput,
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    b3_device: str | torch.device = "cpu",
) -> CheckpointAnalysisResult:
    """Evaluate one checkpoint, stopping before metrics when precedence does."""

    support = assess_support(evidence.support)
    if not evidence.validity.passed or not support.adequate:
        decision = classify_checkpoint(validity=evidence.validity, support=support)
        return CheckpointAnalysisResult(
            support=support,
            gate_a=None,
            gate_b1=None,
            gate_b2=None,
            gate_b3=None,
            gate_c=None,
            decision=decision,
        )
    gate_a = evaluate_gate_a(evidence.gate_a, bootstrap_reps=int(bootstrap_reps))
    if not gate_a.passed:
        decision = classify_checkpoint(
            validity=evidence.validity,
            support=support,
            gate_a=gate_a,
            gate_a_valid_repetition=evidence.gate_a_valid_repetition,
        )
        return CheckpointAnalysisResult(
            support=support,
            gate_a=gate_a,
            gate_b1=None,
            gate_b2=None,
            gate_b3=None,
            gate_c=None,
            decision=decision,
        )
    gate_b1 = evaluate_gate_b1(evidence.gate_b1, bootstrap_reps=int(bootstrap_reps))
    gate_b2 = evaluate_gate_b2(evidence.gate_b2, bootstrap_reps=int(bootstrap_reps))
    gate_b3 = evaluate_gate_b3(
        evidence.gate_b3,
        bootstrap_reps=int(bootstrap_reps),
        device=b3_device,
    )
    gate_c = evaluate_gate_c(evidence.gate_c, bootstrap_reps=int(bootstrap_reps))
    decision = classify_checkpoint(
        validity=evidence.validity,
        support=support,
        gate_a=gate_a,
        gate_b1=gate_b1,
        gate_b2=gate_b2,
        gate_b3=gate_b3,
        gate_c=gate_c,
        gate_a_valid_repetition=evidence.gate_a_valid_repetition,
    )
    return CheckpointAnalysisResult(
        support=support,
        gate_a=gate_a,
        gate_b1=gate_b1,
        gate_b2=gate_b2,
        gate_b3=gate_b3,
        gate_c=gate_c,
        decision=decision,
    )
