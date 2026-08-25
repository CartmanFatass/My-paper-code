"""Owner-bound 28-family TEST analyzer for RSCF Gate B.

The twelve support slacks are implemented separately from the exact
non-revision clarification; the former two composite minima are absent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import math
from pathlib import Path
from typing import Iterable, Mapping

from .audits import AuditCertificate
from .evaluation import (
    CompleteEvaluationPanel,
    EDGE,
    HELD_OUT_ROSTERS,
    INTACT,
    PHY,
    ROTATED,
    SEEN_ROSTERS,
    UNIFORM,
)
from .lifecycle import LifecycleContractError, canonical_sha256, validate_test_namespace


ANALYZER_SCHEMA_VERSION = "SGSP_RSCF_28_FAMILY_ANALYZER_V1"
SUPPORT_SLACK_CLARIFICATION_PATH = (
    "docs/research/candidates/semantic_graphon_shared_policy/"
    "SGSP_RG2Z_RSCF_R01_28_FAMILY_SUPPORT_SLACKS_NONREVISION_CLARIFICATION_20260821.md"
)
SUPPORT_SLACK_CLARIFICATION_SHA256 = "53d0bdefc0af54f335f25b6f7304b79a62b8d364ebb7109050e4419b2577559a"
SUPPORT_SLACK_FORMULA_REVISION = "SGSP-RG2Z-RSCF-SCIENCE-20260821-01/NONREVISION-28-SLACKS"
FAMILY_ALPHA = 0.05
FAMILY_SIZE = 28
PER_QUANTITY_TWO_SIDED_ALPHA = FAMILY_ALPHA / FAMILY_SIZE
REQUIRED_SEED_BLOCKS = 24

DIRECT_MARGIN = 0.04
INTERACTION_MARGIN = 0.03
ZONE_MARGIN = 0.02
CUT_RETURN_MARGIN = 0.05
TV_MARGIN = 0.08
ATTENUATION_MARGIN = 0.03
COMPETENCE_MARGIN = 0.08
SEEN_EQUIVALENCE_BAND = (-0.04, 0.04)


DIRECT_NAMES = tuple(f"d.N{n}" for n in (9, 15, 6, 21))
COMPETENCE_NAMES = tuple(f"e.N{n}" for n in SEEN_ROSTERS)
INTERACTION_NAMES = tuple(f"c.N{n}" for n in HELD_OUT_ROSTERS)
ZONE_NAMES = tuple(f"z.N{n}" for n in HELD_OUT_ROSTERS)
CUT_NAMES = tuple(f"{quantity}.N{n}" for n in HELD_OUT_ROSTERS for quantity in ("C_PHY", "V", "I"))
COMPONENT_SUPPORT_NAMES = tuple(
    f"{quantity}.N{n}" for n in HELD_OUT_ROSTERS for quantity in ("A_cut", "A_atten", "A_TV")
)
DIRECT_SUPPORT_NAMES = tuple(
    f"{quantity}.N{n}" for n in HELD_OUT_ROSTERS for quantity in ("A_dir", "A_interaction", "A_zone")
)
SUPPORT_SLACK_NAMES = COMPONENT_SUPPORT_NAMES + DIRECT_SUPPORT_NAMES
KNOWN_QUANTITY_NAMES = DIRECT_NAMES + COMPETENCE_NAMES + INTERACTION_NAMES + ZONE_NAMES + CUT_NAMES
QUANTITY_NAMES = KNOWN_QUANTITY_NAMES + SUPPORT_SLACK_NAMES

if len(QUANTITY_NAMES) != FAMILY_SIZE or len(set(QUANTITY_NAMES)) != FAMILY_SIZE:
    raise RuntimeError("internal RSCF 28-family registry is invalid")


def verify_support_slack_formula_document(path: Path | str | None = None) -> str:
    if path is None:
        path = Path(__file__).resolve().parents[3] / SUPPORT_SLACK_CLARIFICATION_PATH
    observed = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if observed != SUPPORT_SLACK_CLARIFICATION_SHA256:
        raise MissingSupportSlackFormulaError("support-slack clarification document digest mismatch")
    return observed

AUTHORITATIVE_SUPPORT_SIGN_CONVENTIONS = {
    name: (
        "positive means the retained bounded-mean interiority exceeds its frozen margin"
        if not name.startswith("A_TV")
        else "positive means mean legal-simplex TV_sup exceeds delta_TV=0.08"
    )
    for name in SUPPORT_SLACK_NAMES
}


class MissingSupportSlackFormulaError(LifecycleContractError):
    """Backward-compatible name for a formula-document binding mismatch."""


@dataclass(frozen=True)
class SupportSlackFormulaSet:
    """Exact owner-bound implementation of the twelve retained r03 slacks."""

    formula_revision: str = SUPPORT_SLACK_FORMULA_REVISION
    formula_document_sha256: str = SUPPORT_SLACK_CLARIFICATION_SHA256
    sign_conventions: Mapping[str, str] = field(
        default_factory=lambda: dict(AUTHORITATIVE_SUPPORT_SIGN_CONVENTIONS)
    )

    def __post_init__(self) -> None:
        if self.formula_revision != SUPPORT_SLACK_FORMULA_REVISION:
            raise MissingSupportSlackFormulaError("support-slack formula revision does not match owner clarification")
        if self.formula_document_sha256 != SUPPORT_SLACK_CLARIFICATION_SHA256:
            raise MissingSupportSlackFormulaError("support-slack formula document digest does not match owner clarification")
        if dict(self.sign_conventions) != AUTHORITATIVE_SUPPORT_SIGN_CONVENTIONS:
            raise MissingSupportSlackFormulaError("support-slack signs do not match the positive-interiority clarification")

    @property
    def identity_sha256(self) -> str:
        return canonical_sha256(
            {
                "formula_revision": self.formula_revision,
                "formula_document_sha256": self.formula_document_sha256,
                "sign_conventions": dict(self.sign_conventions),
            }
        )

    def compute(self, panel: CompleteEvaluationPanel) -> dict[str, float]:
        cells = panel.by_key

        def h(value: float, delta: float) -> float:
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise LifecycleContractError("support-slack primitive must be a bounded mean in [0,1]")
            return min(value, 1.0 - value) - delta

        def cell(n: int, arm: str, condition: str = INTACT):
            return cells[(n, arm, condition)]

        values: dict[str, float] = {}
        for n in HELD_OUT_ROSTERS:
            values[f"A_dir.N{n}"] = min(
                h(cell(n, arm).mean_return, DIRECT_MARGIN) for arm in (PHY, EDGE)
            )
            values[f"A_interaction.N{n}"] = min(
                h(cell(m, arm).mean_return, INTERACTION_MARGIN)
                for arm in (PHY, EDGE)
                for m in (n, 9, 15)
            )
            values[f"A_zone.N{n}"] = min(
                h(basin_mean, ZONE_MARGIN)
                for arm in (PHY, EDGE)
                for basin_mean in (cell(n, arm).basin_west_mean, cell(n, arm).basin_east_mean)
            )
            values[f"A_cut.N{n}"] = min(
                h(cell(n, PHY, condition).mean_return, CUT_RETURN_MARGIN)
                for condition in (INTACT, ROTATED)
            )
            values[f"A_atten.N{n}"] = min(
                h(cell(n, arm, condition).mean_return, ATTENUATION_MARGIN)
                for arm in (PHY, EDGE)
                for condition in (INTACT, ROTATED)
            )
            tv_sup = cell(n, PHY).mean_legal_simplex_tv_sup
            if tv_sup is None:
                raise LifecycleContractError("A_TV requires the held-out intact-PHY mean TV_sup accumulator")
            values[f"A_TV.N{n}"] = tv_sup - TV_MARGIN
        if set(values) != set(SUPPORT_SLACK_NAMES):
            raise RuntimeError("support-slack implementation drift")
        return {name: values[name] for name in SUPPORT_SLACK_NAMES}


AUTHORITATIVE_SUPPORT_SLACK_FORMULAS = SupportSlackFormulaSet()


def compute_known_seed_quantities(panel: CompleteEvaluationPanel) -> dict[str, float]:
    """Compute the sixteen quantities whose r01 meaning is already explicit."""
    cells = panel.by_key

    def cell(n: int, arm: str, condition: str = INTACT):
        return cells[(n, arm, condition)]

    direct = {
        n: cell(n, PHY).mean_return - cell(n, EDGE).mean_return
        for n in (9, 15, 6, 21)
    }
    seen_direct = 0.5 * (direct[9] + direct[15])
    result: dict[str, float] = {f"d.N{n}": direct[n] for n in (9, 15, 6, 21)}
    result.update(
        {
            f"e.N{n}": cell(n, EDGE).mean_return - cell(n, UNIFORM).mean_return
            for n in SEEN_ROSTERS
        }
    )
    for n in HELD_OUT_ROSTERS:
        phy_intact = cell(n, PHY)
        edge_intact = cell(n, EDGE)
        phy_rotated = cell(n, PHY, ROTATED)
        edge_rotated = cell(n, EDGE, ROTATED)
        c_phy = phy_intact.mean_return - phy_rotated.mean_return
        c_edge = edge_intact.mean_return - edge_rotated.mean_return
        result[f"c.N{n}"] = direct[n] - seen_direct
        result[f"z.N{n}"] = min(phy_intact.basin_west_mean, phy_intact.basin_east_mean) - min(
            edge_intact.basin_west_mean, edge_intact.basin_east_mean
        )
        result[f"C_PHY.N{n}"] = c_phy
        assert phy_intact.mean_legal_action_tv_to_shadow is not None
        result[f"V.N{n}"] = phy_intact.mean_legal_action_tv_to_shadow
        result[f"I.N{n}"] = c_phy - c_edge
    if set(result) != set(KNOWN_QUANTITY_NAMES):
        raise RuntimeError("known-quantity implementation drift")
    if any(not math.isfinite(value) for value in result.values()):
        raise LifecycleContractError("known seed quantity is non-finite")
    return {name: result[name] for name in KNOWN_QUANTITY_NAMES}


@dataclass(frozen=True)
class SeedQuantityVector:
    namespace: str
    test_seed_block_id: str
    evaluation_panel_sha256: str
    audit_certificate_sha256: str
    support_formula_set_sha256: str
    values: Mapping[str, float]

    def __post_init__(self) -> None:
        validate_test_namespace(self.namespace)
        if not self.test_seed_block_id.startswith("TEST_"):
            raise LifecycleContractError("analyzer seed identity must be TEST-only")
        if set(self.values) != set(QUANTITY_NAMES):
            raise LifecycleContractError("seed vector does not contain the exact 28-quantity family")
        if any(not math.isfinite(float(value)) for value in self.values.values()):
            raise LifecycleContractError("seed vector contains a non-finite quantity")
        for name in ("evaluation_panel_sha256", "audit_certificate_sha256", "support_formula_set_sha256"):
            digest = getattr(self, name)
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise LifecycleContractError(f"{name} is invalid")

    @classmethod
    def from_panel(
        cls,
        panel: CompleteEvaluationPanel,
        support_formulas: SupportSlackFormulaSet | None = None,
    ) -> "SeedQuantityVector":
        if support_formulas is None:
            support_formulas = AUTHORITATIVE_SUPPORT_SLACK_FORMULAS
        known = compute_known_seed_quantities(panel)
        support = support_formulas.compute(panel)
        values = {**known, **support}
        audit_digest = next(iter({cell.audit_certificate_sha256 for cell in panel.cells}))
        return cls(
            namespace=panel.namespace,
            test_seed_block_id=panel.test_seed_block_id,
            evaluation_panel_sha256=panel.digest,
            audit_certificate_sha256=audit_digest,
            support_formula_set_sha256=support_formulas.identity_sha256,
            values=values,
        )


@dataclass(frozen=True)
class StudentTInterval:
    quantity: str
    n: int
    mean: float
    lower: float
    upper: float
    standard_error: float
    critical_t: float
    two_sided_alpha: float = PER_QUANTITY_TWO_SIDED_ALPHA


def _student_t_interval(name: str, samples: list[float]) -> StudentTInterval:
    if len(samples) < 2:
        raise LifecycleContractError("Student-t interval requires at least two seed blocks")
    n = len(samples)
    mean = math.fsum(samples) / n
    centered_ss = math.fsum((value - mean) ** 2 for value in samples)
    standard_error = math.sqrt(centered_ss / (n - 1)) / math.sqrt(n)
    try:
        from scipy.stats import t as student_t  # type: ignore
    except ImportError as exc:
        raise LifecycleContractError("scipy is required for exact Student-t critical values") from exc
    critical = float(student_t.ppf(1.0 - PER_QUANTITY_TWO_SIDED_ALPHA / 2.0, df=n - 1))
    if not math.isfinite(critical):
        raise LifecycleContractError("Student-t critical value is non-finite")
    half_width = critical * standard_error
    return StudentTInterval(name, n, mean, mean - half_width, mean + half_width, standard_error, critical)


class ResultBranch(str, Enum):
    STRUCTURAL_INVALID_NO_SCIENTIFIC_RELATION = "STRUCTURAL_INVALID_NO_SCIENTIFIC_RELATION"
    NONIDENTIFIED = "NONIDENTIFIED"
    DO_NOT_RETAIN_COMPONENT_ATTRIBUTION = "DO_NOT_RETAIN_COMPONENT_ATTRIBUTION"
    DO_NOT_RETAIN_DIRECT_VALUE = "DO_NOT_RETAIN_DIRECT_VALUE"
    RETAIN_PHYSICAL_PRIOR_COLDSTART = "RETAIN_PHYSICAL_PRIOR_COLDSTART"


@dataclass(frozen=True)
class PredicateResult:
    name: str
    passed: bool
    relation: str
    interval_name: str
    threshold: float | tuple[float, float]


@dataclass(frozen=True)
class SimultaneousAnalysis:
    namespace: str
    support_formula_set_sha256: str
    intervals: Mapping[str, StudentTInterval]
    predicates: tuple[PredicateResult, ...]
    result_branch: ResultBranch
    additional_labels: tuple[str, ...]
    failed_predicates: tuple[str, ...]
    structural_failures: tuple[str, ...]
    schema_version: str = ANALYZER_SCHEMA_VERSION

    @property
    def digest(self) -> str:
        return canonical_sha256(
            {
                "schema_version": self.schema_version,
                "namespace": self.namespace,
                "support_formula_set_sha256": self.support_formula_set_sha256,
                "intervals": {name: asdict(interval) for name, interval in sorted(self.intervals.items())},
                "predicates": [asdict(item) for item in self.predicates],
                "result_branch": self.result_branch.value,
                "additional_labels": list(self.additional_labels),
                "failed_predicates": list(self.failed_predicates),
                "structural_failures": list(self.structural_failures),
            }
        )


def _lower(name: str, interval: StudentTInterval, threshold: float) -> PredicateResult:
    return PredicateResult(name, interval.lower > threshold, "lower_gt", interval.quantity, threshold)


def analyze_complete_family(
    vectors: Iterable[SeedQuantityVector],
    *,
    support_formulas: SupportSlackFormulaSet | None = None,
    audit_certificates: Iterable[AuditCertificate] = (),
    structural_failures: Iterable[str] = (),
) -> SimultaneousAnalysis:
    if support_formulas is None:
        support_formulas = AUTHORITATIVE_SUPPORT_SLACK_FORMULAS
    vectors = tuple(vectors)
    if len(vectors) != REQUIRED_SEED_BLOCKS:
        raise LifecycleContractError(f"analyzer requires exactly {REQUIRED_SEED_BLOCKS} complete seed vectors")
    namespaces = {vector.namespace for vector in vectors}
    formula_ids = {vector.support_formula_set_sha256 for vector in vectors}
    seed_ids = {vector.test_seed_block_id for vector in vectors}
    if len(namespaces) != 1 or len(formula_ids) != 1 or len(seed_ids) != REQUIRED_SEED_BLOCKS:
        raise LifecycleContractError("analyzer vectors have mixed namespace/formulas or duplicate seed identities")
    if formula_ids != {support_formulas.identity_sha256}:
        raise MissingSupportSlackFormulaError("seed vectors are not bound to the supplied support formula set")

    certificates = tuple(audit_certificates)
    derived_structural_failures = set(structural_failures)
    if len(certificates) != REQUIRED_SEED_BLOCKS:
        derived_structural_failures.add("AUDIT_CERTIFICATE_SET_INCOMPLETE")
    else:
        certificate_by_seed = {certificate.test_seed_block_id: certificate for certificate in certificates}
        if len(certificate_by_seed) != REQUIRED_SEED_BLOCKS or set(certificate_by_seed) != seed_ids:
            derived_structural_failures.add("AUDIT_CERTIFICATE_SEED_IDENTITY_MISMATCH")
        for vector in vectors:
            certificate = certificate_by_seed.get(vector.test_seed_block_id)
            if certificate is None:
                continue
            if certificate.namespace != vector.namespace or certificate.digest != vector.audit_certificate_sha256:
                derived_structural_failures.add(f"AUDIT_BINDING_MISMATCH:{vector.test_seed_block_id}")
            for name in certificate.failed_names:
                derived_structural_failures.add(f"AUDIT_FAILED:{vector.test_seed_block_id}:{name}")

    intervals = {
        name: _student_t_interval(name, [float(vector.values[name]) for vector in vectors])
        for name in QUANTITY_NAMES
    }
    predicates: list[PredicateResult] = []

    component_support = [_lower(f"component_support:{name}", intervals[name], 0.0) for name in COMPONENT_SUPPORT_NAMES]
    direct_support = [_lower(f"direct_support:{name}", intervals[name], 0.0) for name in DIRECT_SUPPORT_NAMES]
    competence = [_lower(f"competence:{name}", intervals[name], COMPETENCE_MARGIN) for name in COMPETENCE_NAMES]
    equivalence = [
        PredicateResult(
            f"seen_equivalence:{name}",
            intervals[name].lower >= SEEN_EQUIVALENCE_BAND[0]
            and intervals[name].upper <= SEEN_EQUIVALENCE_BAND[1],
            "interval_inside",
            name,
            SEEN_EQUIVALENCE_BAND,
        )
        for name in ("d.N9", "d.N15")
    ]
    component_value: list[PredicateResult] = []
    for n in HELD_OUT_ROSTERS:
        component_value.extend(
            [
                _lower(f"component_value:C_PHY.N{n}", intervals[f"C_PHY.N{n}"], CUT_RETURN_MARGIN),
                _lower(f"component_value:V.N{n}", intervals[f"V.N{n}"], TV_MARGIN),
                _lower(f"component_value:I.N{n}", intervals[f"I.N{n}"], ATTENUATION_MARGIN),
            ]
        )
    direct_value: list[PredicateResult] = []
    for n in HELD_OUT_ROSTERS:
        direct_value.extend(
            [
                _lower(f"direct_value:d.N{n}", intervals[f"d.N{n}"], DIRECT_MARGIN),
                _lower(f"direct_value:c.N{n}", intervals[f"c.N{n}"], INTERACTION_MARGIN),
                _lower(f"direct_value:z.N{n}", intervals[f"z.N{n}"], ZONE_MARGIN),
            ]
        )
    predicates.extend(component_support + competence + equivalence + direct_support + component_value + direct_value)

    structural = tuple(sorted(derived_structural_failures))
    prerequisites = component_support + competence + equivalence + direct_support
    if structural:
        branch = ResultBranch.STRUCTURAL_INVALID_NO_SCIENTIFIC_RELATION
    elif not all(item.passed for item in prerequisites):
        branch = ResultBranch.NONIDENTIFIED
    elif not all(item.passed for item in component_value):
        # Component nonretention precedes the direct-value nonretention branch.
        branch = ResultBranch.DO_NOT_RETAIN_COMPONENT_ATTRIBUTION
    elif not all(item.passed for item in direct_value):
        branch = ResultBranch.DO_NOT_RETAIN_DIRECT_VALUE
    else:
        branch = ResultBranch.RETAIN_PHYSICAL_PRIOR_COLDSTART
    labels: tuple[str, ...] = ()
    if branch in (
        ResultBranch.DO_NOT_RETAIN_COMPONENT_ATTRIBUTION,
        ResultBranch.DO_NOT_RETAIN_DIRECT_VALUE,
    ):
        held_out_direct = (intervals["d.N6"], intervals["d.N21"])
        if all(
            interval.lower >= SEEN_EQUIVALENCE_BAND[0] and interval.upper <= SEEN_EQUIVALENCE_BAND[1]
            for interval in held_out_direct
        ):
            labels = ("PRACTICAL_EQUIVALENCE",)
        elif all(interval.upper < -DIRECT_MARGIN for interval in held_out_direct):
            labels = ("EDGE_MATERIALLY_SUPERIOR",)
    failed = tuple(item.name for item in predicates if not item.passed)
    return SimultaneousAnalysis(
        namespace=next(iter(namespaces)),
        support_formula_set_sha256=next(iter(formula_ids)),
        intervals=intervals,
        predicates=tuple(predicates),
        result_branch=branch,
        additional_labels=labels,
        failed_predicates=failed,
        structural_failures=structural,
    )
