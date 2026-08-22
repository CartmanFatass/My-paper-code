"""Exact Stage-1b opportunity construction for the frozen TBCC r02 object.

The service is dependency-injected at the native-session and frozen-foundation
boundaries.  It defines the complete production execution contract, while the
construction suite exercises it only with deterministic ``TEST_ONLY`` fixtures.
No random master, scientific identity, coordinate, model, checkpoint, training
loop, or result publication exists here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Final, Iterable, Mapping, Protocol, Sequence

from scipy.stats import t as student_t

from .artifacts import (
    ArtifactContractError,
    Stage1bOpportunityExecutionPermit,
    validate_stage1b_opportunity_execution_permit,
)
from .config import (
    ACTIONS,
    ACTION_COUNT,
    FORMATION_ROTATE,
    HOOK_HANDOFF,
    HORIZON_TICKS,
    MAX_HOLD_TICKS,
)
from .host_types import HostOutput, RenewalLane, ResetLane
from .lifecycle import (
    Applicability,
    LifecycleError,
    LifecycleSnapshot,
    OpportunityExecutionPermit,
    opportunity_execution_permit_digest,
    validate_opportunity_execution_permit,
)
from .synthetic_resume import create_only_commit


class OpportunityContractError(RuntimeError):
    pass


TARGET_K: Final[tuple[int, int]] = (7, 13)
STATE_COUNT_PER_K: Final[int] = 16
TAPE_COUNT: Final[int] = 4
PAIR_ROLLOUT_COUNT: Final[int] = 2 * ACTION_COUNT * TAPE_COUNT
REPLICATE_PAIR_COUNT: Final[int] = len(TARGET_K) * STATE_COUNT_PER_K
REPLICATE_COUNT: Final[int] = 24
BONFERRONI_FAMILY_ERROR: Final[float] = 0.05
BONFERRONI_MEMBER_COUNT: Final[int] = 3
Q_THRESHOLD: Final[float] = 0.20
D_THRESHOLD: Final[float] = 0.025
S_THRESHOLD: Final[float] = 0.060


class NativeOpportunitySession(Protocol):
    initial: tuple[HostOutput, ...]

    def renew(self, rows: Iterable[RenewalLane]) -> tuple[HostOutput, ...]: ...

    def close(self) -> None: ...


NativeSessionFactory = Callable[[Iterable[ResetLane]], NativeOpportunitySession]


class FrozenFoundationPolicy(Protocol):
    def __call__(
        self, observations: tuple[tuple[float, ...], ...]
    ) -> Sequence[Sequence[float]]: ...


@dataclass(frozen=True, slots=True)
class OpportunityState:
    replicate: int
    k: int
    state_index: int
    initial_v: float
    initial_y: float
    initial_phi: float

    def validate(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(REPLICATE_COUNT):
            raise OpportunityContractError("opportunity replicate must lie in [0,24)")
        if self.k not in TARGET_K:
            raise OpportunityContractError("opportunity k must be exactly 7 or 13")
        if isinstance(self.state_index, bool) or self.state_index not in range(STATE_COUNT_PER_K):
            raise OpportunityContractError("opportunity state index must lie in [0,16)")
        ResetLane(
            middle_events=(FORMATION_ROTATE, HOOK_HANDOFF),
            k_initial=self.k,
            initial_v=self.initial_v,
            initial_y=self.initial_y,
            initial_phi=self.initial_phi,
        ).validate()


@dataclass(frozen=True, slots=True)
class DisturbanceTape:
    """One already-bound full-mission disturbance tape.

    ``address`` is opaque to the service.  The service never selects, replaces,
    or derives a tape from an action or graph.
    """

    address: str
    eta_v: tuple[float, ...]
    eta_y: tuple[float, ...]
    eta_omega: tuple[float, ...]

    def validate(self) -> None:
        if not self.address:
            raise OpportunityContractError("tape address must be nonempty")
        for name, values, magnitude in (
            ("eta_v", self.eta_v, 0.003),
            ("eta_y", self.eta_y, 0.002),
            ("eta_omega", self.eta_omega, 0.004),
        ):
            if len(values) != HORIZON_TICKS:
                raise OpportunityContractError(f"{name} tape must contain exactly 364 ticks")
            if any(not math.isfinite(value) or abs(value) != magnitude for value in values):
                raise OpportunityContractError(f"{name} tape differs from the frozen support")

    @property
    def digest(self) -> str:
        self.validate()
        payload = json.dumps(
            {
                "address": self.address,
                "eta_v": self.eta_v,
                "eta_y": self.eta_y,
                "eta_omega": self.eta_omega,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
        return hashlib.sha256(payload).hexdigest()

    def renewal(self, *, tick: int, action: int, active: bool = True) -> RenewalLane:
        if not 0 <= tick < HORIZON_TICKS:
            raise OpportunityContractError("active tape offset lies outside the mission")

        def window(values: tuple[float, ...]) -> tuple[float, ...]:
            selected = values[tick : tick + MAX_HOLD_TICKS]
            # Padding is structurally required by the ABI and lies after the
            # horizon, so the native host never consumes these repeated values.
            return selected + (values[-1],) * (MAX_HOLD_TICKS - len(selected))

        return RenewalLane(
            action=action,
            eta_v=window(self.eta_v),
            eta_y=window(self.eta_y),
            eta_omega=window(self.eta_omega),
            active=active,
        )


@dataclass(frozen=True, slots=True, order=True)
class RolloutAddress:
    q: int
    action: int
    tape_index: int


EXPECTED_ADDRESSES: Final[frozenset[RolloutAddress]] = frozenset(
    RolloutAddress(q, action, tape)
    for q in (0, 1)
    for action in range(ACTION_COUNT)
    for tape in range(TAPE_COUNT)
)


@dataclass(frozen=True, slots=True)
class TapeOutcome:
    address: RolloutAddress
    tape_digest: str
    completion_value: float

    def validate(self) -> None:
        if self.address not in EXPECTED_ADDRESSES:
            raise OpportunityContractError("rollout address is not registered")
        if len(self.tape_digest) != 64:
            raise OpportunityContractError("tape digest must be SHA-256")
        try:
            int(self.tape_digest, 16)
        except ValueError as error:
            raise OpportunityContractError("tape digest must be SHA-256") from error
        if not math.isfinite(self.completion_value) or not 0.0 <= self.completion_value <= 1.0:
            raise OpportunityContractError("completion value must be finite in [0,1]")


@dataclass(frozen=True, slots=True)
class PairOpportunityMetrics:
    replicate: int
    k: int
    state_index: int
    q_value: float
    d_value: float
    s_value: float
    argmax_q0: frozenset[int]
    argmax_q1: frozenset[int]
    tape_digests: tuple[str, ...]
    rollout_count: int = PAIR_ROLLOUT_COUNT

    def validate(self) -> None:
        OpportunityState(self.replicate, self.k, self.state_index, 0.0, 0.0, 0.0).validate()
        if self.q_value not in (0.0, 1.0):
            raise OpportunityContractError("Q_pair must be exactly zero or one")
        if not math.isfinite(self.d_value) or not 0.0 <= self.d_value <= 1.0:
            raise OpportunityContractError("D_pair must be finite in [0,1]")
        if not math.isfinite(self.s_value) or not 0.0 <= self.s_value <= 1.0:
            raise OpportunityContractError("S_pair must be finite in [0,1]")
        if (
            not self.argmax_q0
            or not self.argmax_q1
            or not self.argmax_q0.issubset(range(ACTION_COUNT))
            or not self.argmax_q1.issubset(range(ACTION_COUNT))
        ):
            raise OpportunityContractError("complete nonempty argmax sets are required")
        if self.q_value != float(self.argmax_q0.isdisjoint(self.argmax_q1)):
            raise OpportunityContractError("Q_pair differs from exact argmax-set intersection")
        if len(self.tape_digests) != TAPE_COUNT or len(set(self.tape_digests)) != TAPE_COUNT:
            raise OpportunityContractError("pair metrics require four distinct tape digests")
        for digest in self.tape_digests:
            if len(digest) != 64:
                raise OpportunityContractError("pair tape digest must be SHA-256")
            try:
                int(digest, 16)
            except ValueError as error:
                raise OpportunityContractError("pair tape digest must be SHA-256") from error
        if self.rollout_count != PAIR_ROLLOUT_COUNT:
            raise OpportunityContractError("pair rollout inventory is incomplete")


def _validate_complete_outcomes(outcomes: Iterable[TapeOutcome]) -> tuple[TapeOutcome, ...]:
    values = tuple(outcomes)
    if len(values) != PAIR_ROLLOUT_COUNT:
        raise OpportunityContractError("one pair requires exactly 144 completed rollouts")
    for value in values:
        value.validate()
    addresses = tuple(value.address for value in values)
    if len(set(addresses)) != PAIR_ROLLOUT_COUNT or set(addresses) != EXPECTED_ADDRESSES:
        raise OpportunityContractError("rollout inventory is partial, duplicate, or has extra addresses")
    by_tape: dict[int, set[str]] = {index: set() for index in range(TAPE_COUNT)}
    for value in values:
        by_tape[value.address.tape_index].add(value.tape_digest)
    if any(len(digests) != 1 for digests in by_tape.values()):
        raise OpportunityContractError("tape binding differs across graph modes or actions")
    if len({next(iter(digests)) for digests in by_tape.values()}) != TAPE_COUNT:
        raise OpportunityContractError("the four future-disturbance tapes must be distinct")
    return values


def compute_pair_metrics(
    state: OpportunityState, outcomes: Iterable[TapeOutcome]
) -> PairOpportunityMetrics:
    """Compute tape means before any maximum and preserve every exact tie."""

    state.validate()
    values = _validate_complete_outcomes(outcomes)
    indexed = {value.address: value for value in values}
    tape_digests = tuple(
        indexed[RolloutAddress(0, 0, tape)].tape_digest for tape in range(TAPE_COUNT)
    )
    averaged: dict[tuple[int, int], float] = {}
    for q in (0, 1):
        for action in range(ACTION_COUNT):
            averaged[q, action] = 0.25 * sum(
                indexed[RolloutAddress(q, action, tape)].completion_value
                for tape in range(TAPE_COUNT)
            )
    maxima = {q: max(averaged[q, action] for action in range(ACTION_COUNT)) for q in (0, 1)}
    minima = {q: min(averaged[q, action] for action in range(ACTION_COUNT)) for q in (0, 1)}
    argmax = {
        q: frozenset(action for action in range(ACTION_COUNT) if averaged[q, action] == maxima[q])
        for q in (0, 1)
    }
    common = max(
        0.5 * (averaged[0, action] + averaged[1, action])
        for action in range(ACTION_COUNT)
    )
    return PairOpportunityMetrics(
        replicate=state.replicate,
        k=state.k,
        state_index=state.state_index,
        q_value=float(argmax[0].isdisjoint(argmax[1])),
        d_value=0.5 * (maxima[0] + maxima[1]) - common,
        s_value=0.5 * sum(maxima[q] - minima[q] for q in (0, 1)),
        argmax_q0=argmax[0],
        argmax_q1=argmax[1],
        tape_digests=tape_digests,
    )


def _reset_for(state: OpportunityState, q: int) -> ResetLane:
    events = (
        (FORMATION_ROTATE, HOOK_HANDOFF)
        if q == 0
        else (HOOK_HANDOFF, FORMATION_ROTATE)
    )
    return ResetLane(
        middle_events=events,
        k_initial=state.k,
        initial_v=state.initial_v,
        initial_y=state.initial_y,
        initial_phi=state.initial_phi,
    )


def _lexicographic_argmax(logits: Sequence[float]) -> int:
    if len(logits) != ACTION_COUNT or any(not math.isfinite(float(value)) for value in logits):
        raise OpportunityContractError("foundation must return 18 finite logits per active lane")
    maximum = max(float(value) for value in logits)
    return next(index for index, value in enumerate(logits) if float(value) == maximum)


def run_complete_pair(
    state: OpportunityState,
    tapes: Sequence[DisturbanceTape],
    *,
    permit: OpportunityExecutionPermit | Stage1bOpportunityExecutionPermit,
    foundation: FrozenFoundationPolicy,
    session_factory: NativeSessionFactory,
) -> PairOpportunityMetrics:
    """Run all 144 registered native trajectories in invariant address order."""

    # This check is deliberately first: no reset/session/native side effect may
    # occur without the complete passing-foundation lifecycle proof.
    try:
        if isinstance(permit, OpportunityExecutionPermit):
            validate_opportunity_execution_permit(permit)
        elif isinstance(permit, Stage1bOpportunityExecutionPermit):
            validate_stage1b_opportunity_execution_permit(permit)
        else:
            raise OpportunityContractError("validated passing-foundation permit is required")
    except (LifecycleError, ArtifactContractError) as error:
        raise OpportunityContractError("validated passing-foundation permit is required") from error
    state.validate()
    if len(tapes) != TAPE_COUNT:
        raise OpportunityContractError("exactly four future-disturbance tapes are required")
    tapes = tuple(tapes)
    for tape in tapes:
        tape.validate()
    if len({tape.digest for tape in tapes}) != TAPE_COUNT:
        raise OpportunityContractError("future-disturbance tapes must be distinct")
    addresses = tuple(
        RolloutAddress(q, action, tape)
        for q in (0, 1)
        for action in range(ACTION_COUNT)
        for tape in range(TAPE_COUNT)
    )
    resets = tuple(_reset_for(state, address.q) for address in addresses)
    session = session_factory(resets)
    try:
        outputs = tuple(session.initial)
        if len(outputs) != PAIR_ROLLOUT_COUNT:
            raise OpportunityContractError("native reset width changed")
        # The first actionable public renewal must remain exactly aliased.
        first_public = outputs[0].observation
        if any(output.observation != first_public or output.tick != 0 or not output.active for output in outputs):
            raise OpportunityContractError("paired native reset is not publicly aliased and active")

        forced = tuple(
            tapes[address.tape_index].renewal(tick=0, action=address.action)
            for address in addresses
        )
        outputs = tuple(session.renew(forced))
        if len(outputs) != PAIR_ROLLOUT_COUNT:
            raise OpportunityContractError("native forced-hold width changed")

        prior_outputs = outputs
        renewal_count = 1
        while any(output.active for output in outputs):
            active_indices = tuple(index for index, output in enumerate(outputs) if output.active)
            observations = tuple(outputs[index].observation for index in active_indices)
            logits = tuple(foundation(observations))
            if len(logits) != len(active_indices):
                raise OpportunityContractError("foundation output count differs from active mask")
            chosen = {
                index: _lexicographic_argmax(row)
                for index, row in zip(active_indices, logits)
            }
            rows: list[RenewalLane] = []
            for index, (address, output) in enumerate(zip(addresses, outputs)):
                tape = tapes[address.tape_index]
                if output.active:
                    rows.append(tape.renewal(tick=output.tick, action=chosen[index]))
                else:
                    # This row is masked in its original position.  The native
                    # host must neither query nor advance it.
                    padding_tick = min(output.tick, HORIZON_TICKS - 1)
                    rows.append(tape.renewal(tick=padding_tick, action=0, active=False))
            outputs = tuple(session.renew(rows))
            if len(outputs) != PAIR_ROLLOUT_COUNT:
                raise OpportunityContractError("native renewal width changed")
            for before, after in zip(prior_outputs, outputs):
                if not before.active and after != before:
                    raise OpportunityContractError("masked lane advanced or changed address position")
            prior_outputs = outputs
            renewal_count += 1
            if renewal_count > HORIZON_TICKS + 1:
                raise OpportunityContractError("native opportunity session did not terminate")
        if any(not output.terminal for output in outputs):
            raise OpportunityContractError("complete opportunity inventory contains a nonterminal lane")
        outcomes = tuple(
            TapeOutcome(address, tapes[address.tape_index].digest, output.completion_value)
            for address, output in zip(addresses, outputs)
        )
        return compute_pair_metrics(state, outcomes)
    finally:
        session.close()


@dataclass(frozen=True, slots=True)
class ReplicateOpportunityMetrics:
    replicate: int
    q_value: float
    d_value: float
    s_value: float
    pair_count: int = REPLICATE_PAIR_COUNT

    def validate(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(REPLICATE_COUNT):
            raise OpportunityContractError("replicate summary slot must lie in [0,24)")
        if not all(math.isfinite(value) for value in (self.q_value, self.d_value, self.s_value)):
            raise OpportunityContractError("replicate opportunity metrics must be finite")
        if not 0.0 <= self.q_value <= 1.0:
            raise OpportunityContractError("replicate Q must lie in [0,1]")
        if not 0.0 <= self.d_value <= 1.0 or not 0.0 <= self.s_value <= 1.0:
            raise OpportunityContractError("replicate D/S must lie in [0,1]")
        if self.pair_count != REPLICATE_PAIR_COUNT:
            raise OpportunityContractError("replicate pair inventory is incomplete")


def aggregate_replicate(pairs: Iterable[PairOpportunityMetrics]) -> ReplicateOpportunityMetrics:
    values = tuple(pairs)
    if len(values) != REPLICATE_PAIR_COUNT:
        raise OpportunityContractError("replicate opportunity inventory requires exactly 32 pairs")
    for value in values:
        value.validate()
    replicates = {value.replicate for value in values}
    if len(replicates) != 1:
        raise OpportunityContractError("replicate opportunity inventory mixes replicates")
    slots = {(value.k, value.state_index) for value in values}
    expected = {(k, state) for k in TARGET_K for state in range(STATE_COUNT_PER_K)}
    if slots != expected or len(slots) != len(values):
        raise OpportunityContractError("replicate opportunity inventory is partial or duplicate")
    for value in values:
        if value.rollout_count != PAIR_ROLLOUT_COUNT:
            raise OpportunityContractError("pair rollout inventory is incomplete")
    denominator = float(REPLICATE_PAIR_COUNT)
    return ReplicateOpportunityMetrics(
        replicate=next(iter(replicates)),
        q_value=sum(value.q_value for value in values) / denominator,
        d_value=sum(value.d_value for value in values) / denominator,
        s_value=sum(value.s_value for value in values) / denominator,
    )


@dataclass(frozen=True, slots=True)
class OneSidedLowerBound:
    mean: float
    lower: float
    standard_error: float
    critical: float
    sample_count: int = REPLICATE_COUNT


@dataclass(frozen=True, slots=True)
class OpportunityGateAnalysis:
    q: OneSidedLowerBound
    d: OneSidedLowerBound
    s: OneSidedLowerBound
    passes: bool


def _lower_bound(values: Sequence[float]) -> OneSidedLowerBound:
    if len(values) != REPLICATE_COUNT or any(not math.isfinite(value) for value in values):
        raise OpportunityContractError("one-sided bound requires 24 finite replicate values")
    # Preserve exact constant/boundary fixtures.  Naive repeated addition can
    # round 24 identical threshold values above the strict boundary.
    if all(value == values[0] for value in values):
        mean = values[0]
        variance = 0.0
    else:
        mean = math.fsum(values) / REPLICATE_COUNT
        variance = math.fsum((value - mean) ** 2 for value in values) / (REPLICATE_COUNT - 1)
    standard_error = math.sqrt(variance / REPLICATE_COUNT)
    critical = float(
        student_t.ppf(
            1.0 - BONFERRONI_FAMILY_ERROR / BONFERRONI_MEMBER_COUNT,
            df=REPLICATE_COUNT - 1,
        )
    )
    return OneSidedLowerBound(
        mean=mean,
        lower=mean - critical * standard_error,
        standard_error=standard_error,
        critical=critical,
    )


def analyze_gate(replicates: Iterable[ReplicateOpportunityMetrics]) -> OpportunityGateAnalysis:
    values = tuple(replicates)
    for value in values:
        value.validate()
    if len(values) != REPLICATE_COUNT or {value.replicate for value in values} != set(range(REPLICATE_COUNT)):
        raise OpportunityContractError("gate analyzer requires exact replicates 0 through 23")
    if any(value.pair_count != REPLICATE_PAIR_COUNT for value in values):
        raise OpportunityContractError("gate analyzer rejects an incomplete replicate inventory")
    ordered = sorted(values, key=lambda value: value.replicate)
    q = _lower_bound(tuple(value.q_value for value in ordered))
    d = _lower_bound(tuple(value.d_value for value in ordered))
    s = _lower_bound(tuple(value.s_value for value in ordered))
    return OpportunityGateAnalysis(
        q=q,
        d=d,
        s=s,
        passes=q.lower > Q_THRESHOLD and d.lower > D_THRESHOLD and s.lower > S_THRESHOLD,
    )


def require_opportunity_lifecycle(snapshot: LifecycleSnapshot) -> None:
    snapshot.validate()
    if snapshot.opportunity_applicability is not Applicability.ELIGIBLE:
        raise OpportunityContractError("opportunity requires the complete passing foundation gate")
    if snapshot.opportunity_gate is not None or snapshot.adapter_finals:
        raise OpportunityContractError("opportunity construction requires an unopened downstream lifecycle")


def _pair_payload(value: PairOpportunityMetrics) -> dict[str, object]:
    return {
        "replicate": value.replicate,
        "k": value.k,
        "state_index": value.state_index,
        "q_value": value.q_value,
        "d_value": value.d_value,
        "s_value": value.s_value,
        "argmax_q0": sorted(value.argmax_q0),
        "argmax_q1": sorted(value.argmax_q1),
        "tape_digests": list(value.tape_digests),
        "rollout_count": value.rollout_count,
    }


def publish_test_only_replicate_inventory(
    path: Path, pairs: Iterable[PairOpportunityMetrics]
) -> str:
    """Publish one replicate-local TEST diagnostic, never Stage-1b atomicity."""

    values = tuple(pairs)
    aggregate = aggregate_replicate(values)
    ordered = sorted(values, key=lambda value: (value.k, value.state_index))
    payload = {
        "schema": "TEST_ONLY_TBCC_OPPORTUNITY_REPLICATE_INVENTORY_V1",
        "test_only": True,
        "question_relevant": False,
        "complete": True,
        "replicate": aggregate.replicate,
        "pair_count": REPLICATE_PAIR_COUNT,
        "pairs": [_pair_payload(value) for value in ordered],
    }
    return create_only_commit(path, payload)


def load_test_only_replicate_inventory(path: Path) -> tuple[PairOpportunityMetrics, ...]:
    try:
        payload = json.loads(path.resolve().read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OpportunityContractError("TEST-only opportunity inventory cannot be read") from error
    if not isinstance(payload, Mapping) or payload.get("schema") != "TEST_ONLY_TBCC_OPPORTUNITY_REPLICATE_INVENTORY_V1":
        raise OpportunityContractError("TEST-only opportunity inventory schema differs")
    if payload.get("test_only") is not True or payload.get("question_relevant") is not False or payload.get("complete") is not True:
        raise OpportunityContractError("TEST-only opportunity inventory is not complete and blinded")
    rows = payload.get("pairs")
    if not isinstance(rows, list):
        raise OpportunityContractError("TEST-only opportunity pair rows are absent")
    try:
        values = tuple(
            PairOpportunityMetrics(
                replicate=int(row["replicate"]),
                k=int(row["k"]),
                state_index=int(row["state_index"]),
                q_value=float(row["q_value"]),
                d_value=float(row["d_value"]),
                s_value=float(row["s_value"]),
                argmax_q0=frozenset(int(item) for item in row["argmax_q0"]),
                argmax_q1=frozenset(int(item) for item in row["argmax_q1"]),
                tape_digests=tuple(str(item) for item in row["tape_digests"]),
                rollout_count=int(row["rollout_count"]),
            )
            for row in rows
        )
    except (KeyError, TypeError, ValueError) as error:
        raise OpportunityContractError("TEST-only opportunity pair row differs") from error
    aggregate_replicate(values)
    expected = {
        "schema": "TEST_ONLY_TBCC_OPPORTUNITY_REPLICATE_INVENTORY_V1",
        "test_only": True,
        "question_relevant": False,
        "complete": True,
        "replicate": values[0].replicate,
        "pair_count": REPLICATE_PAIR_COUNT,
        "pairs": [_pair_payload(value) for value in sorted(values, key=lambda value: (value.k, value.state_index))],
    }
    if dict(payload) != expected:
        raise OpportunityContractError("TEST-only opportunity inventory payload changed")
    return values


@dataclass(frozen=True, slots=True)
class TestOnlyCompleteOpportunityStage:
    replicates: tuple[ReplicateOpportunityMetrics, ...]
    analysis: OpportunityGateAnalysis
    prerequisite_permit_digest: str


def _bound_payload(value: OneSidedLowerBound) -> dict[str, object]:
    return {
        "mean": value.mean,
        "lower": value.lower,
        "standard_error": value.standard_error,
        "critical": value.critical,
        "sample_count": value.sample_count,
    }


def _analysis_payload(value: OpportunityGateAnalysis) -> dict[str, object]:
    return {
        "q": _bound_payload(value.q),
        "d": _bound_payload(value.d),
        "s": _bound_payload(value.s),
        "passes": value.passes,
        "family_error": BONFERRONI_FAMILY_ERROR,
        "member_count": BONFERRONI_MEMBER_COUNT,
        "strict_thresholds": {
            "q": Q_THRESHOLD,
            "d": D_THRESHOLD,
            "s": S_THRESHOLD,
        },
    }


def _replicate_payload(value: ReplicateOpportunityMetrics) -> dict[str, object]:
    value.validate()
    return {
        "replicate": value.replicate,
        "q_value": value.q_value,
        "d_value": value.d_value,
        "s_value": value.s_value,
        "pair_count": value.pair_count,
    }


def _complete_stage_payload(
    replicates: Sequence[ReplicateOpportunityMetrics],
    *,
    permit: OpportunityExecutionPermit,
) -> tuple[dict[str, object], OpportunityGateAnalysis]:
    try:
        validate_opportunity_execution_permit(permit)
    except LifecycleError as error:
        raise OpportunityContractError("validated passing-foundation permit is required") from error
    values = tuple(replicates)
    analysis = analyze_gate(values)
    ordered = tuple(sorted(values, key=lambda value: value.replicate))
    payload = {
        "schema": "TEST_ONLY_TBCC_COMPLETE_OPPORTUNITY_STAGE_V1",
        "test_only": True,
        "question_relevant": False,
        "complete": True,
        "private_fixture_values": True,
        "prerequisite_permit_digest": opportunity_execution_permit_digest(permit),
        "foundation_inventory_digest": permit.foundation_inventory_digest,
        "replicate_count": REPLICATE_COUNT,
        "replicates": [_replicate_payload(value) for value in ordered],
        "analysis": _analysis_payload(analysis),
    }
    return payload, analysis


def publish_test_only_complete_opportunity_stage(
    path: Path,
    replicates: Iterable[ReplicateOpportunityMetrics],
    *,
    permit: OpportunityExecutionPermit,
) -> str:
    """Create one atomic private TEST fixture for the entire 24-replicate stage."""

    payload, _ = _complete_stage_payload(tuple(replicates), permit=permit)
    return create_only_commit(path, payload)


def load_test_only_complete_opportunity_stage(
    path: Path,
    *,
    permit: OpportunityExecutionPermit,
) -> TestOnlyCompleteOpportunityStage:
    """Cold-load and independently recompute the bound permit and analysis."""

    try:
        raw = json.loads(path.resolve().read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OpportunityContractError("complete TEST-only opportunity stage cannot be read") from error
    if not isinstance(raw, Mapping) or raw.get("schema") != "TEST_ONLY_TBCC_COMPLETE_OPPORTUNITY_STAGE_V1":
        raise OpportunityContractError("complete TEST-only opportunity stage schema differs")
    if (
        raw.get("test_only") is not True
        or raw.get("question_relevant") is not False
        or raw.get("complete") is not True
        or raw.get("private_fixture_values") is not True
    ):
        raise OpportunityContractError("complete TEST-only opportunity stage is not private and atomic")
    rows = raw.get("replicates")
    if not isinstance(rows, list):
        raise OpportunityContractError("complete TEST-only replicate rows are absent")
    try:
        values = tuple(
            ReplicateOpportunityMetrics(
                replicate=int(row["replicate"]),
                q_value=float(row["q_value"]),
                d_value=float(row["d_value"]),
                s_value=float(row["s_value"]),
                pair_count=int(row["pair_count"]),
            )
            for row in rows
        )
    except (KeyError, TypeError, ValueError) as error:
        raise OpportunityContractError("complete TEST-only replicate row differs") from error
    expected, analysis = _complete_stage_payload(values, permit=permit)
    if dict(raw) != expected:
        raise OpportunityContractError(
            "complete TEST-only stage, prerequisite permit, or recomputed analysis differs"
        )
    return TestOnlyCompleteOpportunityStage(
        replicates=tuple(sorted(values, key=lambda value: value.replicate)),
        analysis=analysis,
        prerequisite_permit_digest=opportunity_execution_permit_digest(permit),
    )


def resume_test_only_complete_opportunity_stage(
    path: Path,
    *,
    permit: OpportunityExecutionPermit,
) -> TestOnlyCompleteOpportunityStage:
    """Exact cold-resume is the same complete-only validation as first load."""

    return load_test_only_complete_opportunity_stage(path, permit=permit)
