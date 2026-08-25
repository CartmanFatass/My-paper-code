"""Proof-sized access/resource certificate for one roster linear total.

The candidate binds exactly one registered feature from a production
``BoundarySnapshot``.  It proves the full-access census branch and keeps exact
finite-design HT arithmetic only as counterfactual evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import json
from typing import Mapping, Sequence

import numpy as np

from ha_ctse_process.variable_roster_event_types import BoundaryMember, BoundarySnapshot


FEATURE_NAME = "critic_member_features[0]"
TERMINAL = "CENSUS_CONFORMANT_PRODUCTION_HT_RETIRED"


class ClosureError(ValueError):
    """The frozen access, resource, snapshot, or estimand contract is open."""


class AccessRegime(str, Enum):
    FULL_ACCESS = "FULL_ACCESS"
    SAMPLING_NEEDED = "SAMPLING_NEEDED"


@dataclass(frozen=True)
class FeatureAccess:
    name: str = FEATURE_NAME
    index: int = 0
    dtype: str = "float32"
    reduction_order: str = "protected_then_snapshot_bulk"
    gradient_mode: str = "detached_boundary_numpy"
    exact_aggregate_service: bool = True
    full_roster_stream: bool = True
    sampler_dependency: str = "cheap_g0_pair_sampler"
    sampler_commitment: str = "finite-pair-table/N3-m2/precommitted@1"

    def validate(self) -> None:
        expected = FeatureAccess()
        if self != expected:
            raise ClosureError("feature access registry differs from the frozen unit feature")


@dataclass(frozen=True)
class ResourceVector:
    row_reads: int
    accumulator_ops: int
    resident_rows: int

    def within(self, maximum: "ResourceVector") -> bool:
        return all(
            value <= limit
            for value, limit in zip(
                (self.row_reads, self.accumulator_ops, self.resident_rows),
                (maximum.row_reads, maximum.accumulator_ops, maximum.resident_rows),
                strict=True,
            )
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "row_reads": self.row_reads,
            "accumulator_ops": self.accumulator_ops,
            "resident_rows": self.resident_rows,
        }


R_MAX = ResourceVector(4, 3, 4)
R_ALL = ResourceVector(4, 3, 4)
R_SELECTED = ResourceVector(3, 2, 3)


@dataclass(frozen=True)
class AccessFacts:
    access_registered: bool
    full_stream: bool
    sampler_available: bool
    unbiased_design: bool
    resources_all: bool
    resources_selected: bool


def resolve_access_regime(facts: AccessFacts) -> AccessRegime:
    full = facts.access_registered and facts.full_stream and facts.resources_all
    sampled = (
        facts.access_registered
        and facts.sampler_available
        and facts.unbiased_design
        and facts.resources_selected
        and not facts.resources_all
    )
    if full and sampled:
        raise ClosureError("ambiguous access regime")
    if full:
        return AccessRegime.FULL_ACCESS
    if sampled:
        return AccessRegime.SAMPLING_NEEDED
    raise ClosureError("unresolved access regime")


@dataclass(frozen=True)
class RosterToken:
    physical_time: int
    membership: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class BoundRow:
    lifecycle_key: str
    membership_epoch: int
    value: Fraction


@dataclass(frozen=True)
class SnapshotBinding:
    token: RosterToken
    protected: BoundRow
    bulk: tuple[BoundRow, ...]
    registry: FeatureAccess

    @property
    def bulk_keys(self) -> tuple[str, ...]:
        return tuple(row.lifecycle_key for row in self.bulk)

    @property
    def census_total(self) -> Fraction:
        return self.protected.value + sum((row.value for row in self.bulk), Fraction())


def snapshot_token(snapshot: BoundarySnapshot) -> RosterToken:
    return RosterToken(
        physical_time=int(snapshot.physical_time),
        membership=tuple(
            (member.lifecycle_key, int(member.membership_epoch))
            for member in snapshot.members
        ),
    )


def bind_snapshot(
    snapshot: BoundarySnapshot,
    *,
    protected_keys: Sequence[str],
    bulk_keys: Sequence[str],
    registry: FeatureAccess,
    expected_token: RosterToken | None = None,
) -> SnapshotBinding:
    if not isinstance(snapshot, BoundarySnapshot):
        raise ClosureError("snapshot must be the production BoundarySnapshot DTO")
    registry.validate()
    token = snapshot_token(snapshot)
    if expected_token is not None and token != expected_token:
        raise ClosureError("snapshot token or membership epoch changed")
    protected = tuple(str(key) for key in protected_keys)
    bulk = tuple(str(key) for key in bulk_keys)
    if len(protected) != 1 or len(bulk) != 3:
        raise ClosureError("fixture requires one protected and three bulk members")
    if len(set(protected + bulk)) != 4 or set(protected) & set(bulk):
        raise ClosureError("protected and bulk membership must be unique and disjoint")
    if set(snapshot.keys) != set(protected + bulk):
        raise ClosureError("snapshot membership does not equal the registered sample frame")

    rows: dict[str, BoundRow] = {}
    for member in snapshot.members:
        features = np.asarray(member.critic_member_features)
        if features.dtype != np.dtype(np.float32) or features.ndim != 1:
            raise ClosureError("registered feature requires a one-dimensional float32 row")
        if registry.index >= features.shape[0]:
            raise ClosureError("registered feature index is absent")
        value = Fraction(float(np.float32(features[registry.index])))
        rows[member.lifecycle_key] = BoundRow(
            member.lifecycle_key,
            int(member.membership_epoch),
            value,
        )
    return SnapshotBinding(
        token=token,
        protected=rows[protected[0]],
        bulk=tuple(rows[key] for key in bulk),
        registry=registry,
    )


@dataclass(frozen=True)
class AccessEvent:
    token: RosterToken
    lifecycle_key: str
    kind: str
    feature: str = FEATURE_NAME


class AccessSession:
    def __init__(
        self,
        binding: SnapshotBinding,
        regime: AccessRegime,
        *,
        selected_bulk: Sequence[str] = (),
    ) -> None:
        selected = tuple(str(key) for key in selected_bulk)
        if len(selected) != len(set(selected)) or not set(selected).issubset(binding.bulk_keys):
            raise ClosureError("selected sample does not belong to the bulk frame")
        if regime is AccessRegime.SAMPLING_NEEDED and len(selected) != 2:
            raise ClosureError("sampling fixture requires exactly two bulk rows")
        if regime is AccessRegime.FULL_ACCESS and selected:
            raise ClosureError("full-access census cannot carry a sampled subset")
        self.binding = binding
        self.regime = regime
        self.selected_bulk = selected
        self.trace: list[AccessEvent] = []

    def _check_token(self, token: RosterToken) -> None:
        if token != self.binding.token:
            raise ClosureError("mixed or mutated snapshot token")

    def protected_exact(self, token: RosterToken) -> Fraction:
        self._check_token(token)
        row = self.binding.protected
        self.trace.append(AccessEvent(token, row.lifecycle_key, "protected_exact"))
        return row.value

    def expensive_bulk(self, key: str, token: RosterToken) -> Fraction:
        self._check_token(token)
        if key not in self.binding.bulk_keys:
            raise ClosureError("bulk access is outside the registered frame")
        if self.regime is AccessRegime.SAMPLING_NEEDED and key not in self.selected_bulk:
            raise ClosureError("unsampled expensive bulk access")
        row = next(row for row in self.binding.bulk if row.lifecycle_key == key)
        kind = "bulk_exact" if self.regime is AccessRegime.FULL_ACCESS else "bulk_sampled"
        self.trace.append(AccessEvent(token, key, kind))
        return row.value

    def exact_census(self, token: RosterToken) -> Fraction:
        if self.regime is not AccessRegime.FULL_ACCESS:
            raise ClosureError("exact census is reserved for FULL_ACCESS")
        total = self.protected_exact(token)
        for key in self.binding.bulk_keys:
            total += self.expensive_bulk(key, token)
        self.validate_trace()
        return total

    def sampled_reads(self, token: RosterToken) -> tuple[Fraction, ...]:
        if self.regime is not AccessRegime.SAMPLING_NEEDED:
            raise ClosureError("sampled reads are reserved for SAMPLING_NEEDED")
        values = (self.protected_exact(token),) + tuple(
            self.expensive_bulk(key, token) for key in self.selected_bulk
        )
        self.validate_trace()
        return values

    def validate_trace(self) -> None:
        expected = (
            ((self.binding.protected.lifecycle_key, "protected_exact"),)
            + tuple((key, "bulk_exact") for key in self.binding.bulk_keys)
            if self.regime is AccessRegime.FULL_ACCESS
            else ((self.binding.protected.lifecycle_key, "protected_exact"),)
            + tuple((key, "bulk_sampled") for key in self.selected_bulk)
        )
        if tuple((event.lifecycle_key, event.kind) for event in self.trace) != expected:
            raise ClosureError("access trace is incomplete, duplicated, or out of order")
        if any(event.token != self.binding.token for event in self.trace):
            raise ClosureError("access trace mixes snapshot tokens")


@dataclass(frozen=True)
class SampleOutcome:
    selected: tuple[str, str]
    probability: Fraction


@dataclass(frozen=True)
class FiniteDesign:
    frame: tuple[str, str, str]
    outcomes: tuple[SampleOutcome, ...]

    def inclusion_probabilities(
        self,
    ) -> tuple[dict[str, Fraction], dict[tuple[str, str], Fraction]]:
        if len(set(self.frame)) != 3:
            raise ClosureError("finite design frame must contain three unique bulk members")
        if not self.outcomes or sum((o.probability for o in self.outcomes), Fraction()) != 1:
            raise ClosureError("finite design probabilities must sum exactly to one")
        canonical: set[frozenset[str]] = set()
        for outcome in self.outcomes:
            selected = frozenset(outcome.selected)
            if outcome.probability <= 0 or len(selected) != 2 or not selected.issubset(self.frame):
                raise ClosureError("finite design has a nonpositive or invalid pair")
            if selected in canonical:
                raise ClosureError("finite design repeats a sampled pair")
            canonical.add(selected)
        pi_i = {
            key: sum(
                (outcome.probability for outcome in self.outcomes if key in outcome.selected),
                Fraction(),
            )
            for key in self.frame
        }
        pi_ij = {
            (left, right): (
                pi_i[left]
                if left == right
                else sum(
                    (
                        outcome.probability
                        for outcome in self.outcomes
                        if left in outcome.selected and right in outcome.selected
                    ),
                    Fraction(),
                )
            )
            for left in self.frame
            for right in self.frame
        }
        if any(value <= 0 for value in (*pi_i.values(), *pi_ij.values())):
            raise ClosureError("all first- and second-order inclusion probabilities must be positive")
        return pi_i, pi_ij


@dataclass(frozen=True)
class DesignEvidence:
    census_total: Fraction
    expectation: Fraction
    design_variance: Fraction
    covariance_variance: Fraction
    sample_totals: tuple[Fraction, ...]
    common_weight_expectation: Fraction
    raw_expectation: Fraction


def evaluate_design(
    design: FiniteDesign,
    values: Mapping[str, Fraction],
    *,
    protected_key: str = "protected",
    protected_value: Fraction = Fraction(),
) -> DesignEvidence:
    if protected_key in design.frame or set(values) != set(design.frame):
        raise ClosureError("protected row entered the sample frame or bulk frame mismatched")
    pi_i, pi_ij = design.inclusion_probabilities()
    census = protected_value + sum(values.values(), Fraction())
    sample_totals = tuple(
        protected_value
        + sum((values[key] / pi_i[key] for key in outcome.selected), Fraction())
        for outcome in design.outcomes
    )
    expectation = sum(
        (outcome.probability * total for outcome, total in zip(design.outcomes, sample_totals, strict=True)),
        Fraction(),
    )
    variance = sum(
        (
            outcome.probability * (total - expectation) ** 2
            for outcome, total in zip(design.outcomes, sample_totals, strict=True)
        ),
        Fraction(),
    )
    covariance = sum(
        (
            (pi_ij[left, right] - pi_i[left] * pi_i[right])
            / (pi_i[left] * pi_i[right])
            * values[left]
            * values[right]
            for left in design.frame
            for right in design.frame
        ),
        Fraction(),
    )
    common_weight = Fraction(len(design.frame), 2)
    common_expectation = sum(
        (
            outcome.probability
            * (protected_value + common_weight * sum(values[key] for key in outcome.selected))
            for outcome in design.outcomes
        ),
        Fraction(),
    )
    raw_expectation = sum(
        (
            outcome.probability
            * (protected_value + sum(values[key] for key in outcome.selected))
            for outcome in design.outcomes
        ),
        Fraction(),
    )
    if expectation != census or variance != covariance:
        raise ClosureError("HT expectation or variance identity failed")
    return DesignEvidence(
        census,
        expectation,
        variance,
        covariance,
        sample_totals,
        common_expectation,
        raw_expectation,
    )


def validate_claim(quantity: str, *, unbiased: bool) -> None:
    if unbiased and quantity != "linear_pretransform_total":
        raise ClosureError("HT-unbiased labeling is forbidden downstream of the linear total")


def emulate_float32_census(
    binding: SnapshotBinding,
    *,
    dtype: str = "float32",
    reduction_order: str = "protected_then_snapshot_bulk",
) -> float:
    if dtype != binding.registry.dtype or reduction_order != binding.registry.reduction_order:
        raise ClosureError("mixed dtype or reduction order")
    accumulator = np.float32(binding.protected.value)
    for row in binding.bulk:
        accumulator = np.float32(accumulator + np.float32(row.value))
    return float(accumulator)


def pair_design(probabilities: Sequence[Fraction]) -> FiniteDesign:
    if len(probabilities) != 3:
        raise ClosureError("pair design requires three probabilities")
    return FiniteDesign(
        frame=("bulk-1", "bulk-2", "bulk-3"),
        outcomes=(
            SampleOutcome(("bulk-1", "bulk-2"), probabilities[0]),
            SampleOutcome(("bulk-1", "bulk-3"), probabilities[1]),
            SampleOutcome(("bulk-2", "bulk-3"), probabilities[2]),
        ),
    )


def build_bound_snapshot() -> BoundarySnapshot:
    def member(key: str, epoch: int, value: float) -> BoundaryMember:
        return BoundaryMember.make(
            key,
            epoch,
            observation=[0.0],
            critic_member_features=[value],
            obs_dim=1,
            critic_member_dim=1,
        )

    return BoundarySnapshot.make(
        physical_time=41,
        members=(
            member("protected", 7, 10.0),
            member("bulk-1", 11, 1.0),
            member("bulk-2", 13, 2.0),
            member("bulk-3", 17, 4.0),
        ),
        critic_global_features=[0.0],
        critic_global_dim=1,
    )


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def run_certificate() -> dict[str, object]:
    registry = FeatureAccess()
    binding = bind_snapshot(
        build_bound_snapshot(),
        protected_keys=("protected",),
        bulk_keys=("bulk-1", "bulk-2", "bulk-3"),
        registry=registry,
    )
    facts = AccessFacts(True, True, True, True, R_ALL.within(R_MAX), R_SELECTED.within(R_MAX))
    regime = resolve_access_regime(facts)
    session = AccessSession(binding, regime)
    census = session.exact_census(binding.token)

    positive = evaluate_design(
        pair_design((Fraction(1, 3),) * 3),
        {"bulk-1": Fraction(1), "bulk-2": Fraction(2), "bulk-3": Fraction(4)},
    )
    signed = evaluate_design(
        pair_design((Fraction(1, 3),) * 3),
        {"bulk-1": Fraction(1), "bulk-2": Fraction(-1), "bulk-3": Fraction(0)},
    )
    unequal = evaluate_design(
        pair_design((Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))),
        {"bulk-1": Fraction(1), "bulk-2": Fraction(2), "bulk-3": Fraction(4)},
    )
    protected = evaluate_design(
        pair_design((Fraction(1, 3),) * 3),
        {"bulk-1": Fraction(1), "bulk-2": Fraction(2), "bulk-3": Fraction(4)},
        protected_value=Fraction(10),
    )
    return {
        "actual_binding": "BOUND_VARIABLE_ROSTER_SNAPSHOT_FULL_ACCESS",
        "regime": regime.value,
        "terminal": TERMINAL,
        "feature": registry.name,
        "gradient_mode": registry.gradient_mode,
        "snapshot_token": {
            "physical_time": binding.token.physical_time,
            "membership": [list(item) for item in binding.token.membership],
        },
        "resources": {
            "R_max": R_MAX.as_dict(),
            "R_all": R_ALL.as_dict(),
            "R_selected": R_SELECTED.as_dict(),
        },
        "sampler_dependency": {
            "name": registry.sampler_dependency,
            "commitment": registry.sampler_commitment,
            "present": True,
            "active": False,
            "reason": "retired_on_full_access",
        },
        "access_trace": [
            {"key": event.lifecycle_key, "kind": event.kind}
            for event in session.trace
        ],
        "census_total": _fraction(census),
        "float32_census": emulate_float32_census(binding),
        "fixtures": {
            "uniform_positive": {
                "expectation": _fraction(positive.expectation),
                "variance": _fraction(positive.design_variance),
            },
            "uniform_signed": {
                "expectation": _fraction(signed.expectation),
                "variance": _fraction(signed.design_variance),
            },
            "unequal": {
                "expectation": _fraction(unequal.expectation),
                "variance": _fraction(unequal.design_variance),
                "common_weight_expectation": _fraction(unequal.common_weight_expectation),
                "raw_expectation": _fraction(unequal.raw_expectation),
            },
            "protected_exact": {
                "expectation": _fraction(protected.expectation),
                "variance": _fraction(protected.design_variance),
            },
        },
    }


def canonical_bytes(result: Mapping[str, object] | None = None) -> bytes:
    payload = run_certificate() if result is None else result
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


if __name__ == "__main__":
    print(canonical_bytes().decode("utf-8"), end="")
