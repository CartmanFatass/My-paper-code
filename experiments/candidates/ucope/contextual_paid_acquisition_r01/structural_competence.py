"""Exact two-fold structural competence certificate over the retained CPA rows."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from io import BytesIO
from math import comb, isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import gzip
import json
import os
import re


PROJECT_ROOT = Path(__file__).resolve().parents[4]
RETAINED_ROOT = Path("temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production")
FIXED_BUNDLE_ROOT = PROJECT_ROOT / "temp/directions/ucope/exp/ucope-structural-competence-reference-bundle"
REFERENCE_BUNDLE_FORMAT = "UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V1"
FIT_FORMAT = "UCOPE_STRUCTURAL_EXACT_FIT_V1"
CERTIFICATE_FORMAT = "UCOPE_STRUCTURAL_COMPETENCE_CERTIFICATE_V1"
K_TRAIN = (1, 3, 5, 7, 9)
SEED_SLOTS = tuple(f"cpa-r01-fresh-slot-{index:02d}" for index in range(10))
CONTEXT_IDS = (
    "LINKED-p13_20-c9_100",
    "LINKED-p13_20-c7_50",
    "LINKED-p17_20-c9_100",
    "LINKED-p17_20-c7_50",
    "SEVERED-p13_20-c9_100",
    "SEVERED-p13_20-c7_50",
    "SEVERED-p17_20-c9_100",
    "SEVERED-p17_20-c7_50",
)
TAIL_BASIS = ("1", "b", "k/9", "b*k/9", "(k/9)^2")
ROOT_BASIS = (
    "1",
    "(1-a)*k/9",
    "(1-a)*(k/9)^2",
    "a",
    "a*C",
    "a*L",
    "a*L*p",
)
EXACT_SOLVER_LAW = "UNWEIGHTED_NORMAL_EQUATIONS_FIRST_NONZERO_PIVOT_FRACTION_V1"
EXACT_ARITHMETIC_LAW = "JSON_BINARY64_RN_TIES_EVEN_TO_REDUCED_DYADIC_RATIONAL_V1"
FOLD_DEPENDENCE_CLAIM = "COMPLEMENTARY_GROUP_DISJOINT_NO_CROSS_FOLD_INDEPENDENCE_CLAIM"
FIT_DATA_DEPENDENCY_CLAIM = "AUDITABLE_FIT_DATA_DEPENDENCY_NO_PROCESS_ISOLATION_CLAIM"
ASSESSMENT_PADDING_LAW = "TECHNICAL_ONLY_ZERO_TAIL_VECTOR_FIXED_ROOT_WORK_V1"
ASSESSMENT_PADDING_TAIL_COEFFICIENTS = tuple(Fraction(0) for _ in range(5))
FIT_ACTIVITY = {
    "model_constructions": 0,
    "optimizer_constructions": 0,
    "optimizer_updates": 0,
    "checkpoint_reads": 0,
    "checkpoint_writes": 0,
    "heldout_outcome_rows_read": 0,
    "policy_evaluations_before_seal": 0,
}
_POSTSEAL_RUNTIME: Mapping[str, Any] | None = None


class StructuralCertificateError(ValueError):
    """Raised when exact structural fitting or checking cannot continue."""


class NonUniquePolicyStop(StructuralCertificateError):
    """A complete exact fit produced a tied held-out policy choice."""


def expected_prefit_reference_bundle_members() -> tuple[tuple[str, str], ...]:
    data_prefix = (
        "temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/"
        "preflight/support/materialized"
    )
    members: list[tuple[str, str]] = [
        (f"{data_prefix}/cell-{seed:02d}-{cell:02d}.jsonl.gz", "retained_gzip_tape")
        for seed in range(10)
        for cell in range(8)
    ]
    members.extend(
        (
            (f"{RETAINED_ROOT.as_posix()}/manifest.json", "retained_manifest"),
            (
                f"{RETAINED_ROOT.as_posix()}/preflight/production-preflight.json",
                "retained_preflight",
            ),
            (
                f"{RETAINED_ROOT.as_posix()}/preflight/support/support-preflight.json",
                "retained_support",
            ),
        )
    )
    package = "experiments/candidates/ucope/contextual_paid_acquisition_r01"
    members.extend(
        (f"{package}/{name}.py", f"frozen_{name}_source")
        for name in ("contract", "schema", "training", "rng", "structural_replay")
    )
    members.extend(
        (
            (f"{package}/structural_competence.py", "structural_source"),
            ("scripts/run_ucope_structural_competence_certificate.py", "runner_source"),
        )
    )
    return tuple(members)


def expected_postfit_reference_bundle_members() -> tuple[tuple[str, str], ...]:
    package = "experiments/candidates/ucope/contextual_paid_acquisition_r01"
    return ((f"{package}/oracle.py", "frozen_oracle_source"),)


def expected_reference_bundle_members() -> tuple[tuple[str, str], ...]:
    return expected_prefit_reference_bundle_members() + expected_postfit_reference_bundle_members()


def fold_group_key(seed_slot: str, index: int) -> tuple[str, int]:
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown fixed seed slot")
    if type(index) is not int or index < 0:
        raise ValueError("episode index must be a nonnegative integer")
    return seed_slot, index


def fold_id(seed_slot: str, index: int) -> int:
    fold_group_key(seed_slot, index)
    return (index // 10) % 2


def _fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError("bool is not an exact numeric value")
    if isinstance(value, Mapping):
        if set(value) != {"numerator", "denominator"}:
            raise ValueError("malformed rational mapping")
        return Fraction(int(value["numerator"]), int(value["denominator"]))
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("nonfinite binary64 value is forbidden")
        return Fraction.from_float(value)
    if isinstance(value, Decimal):
        raise ValueError("Decimal bypasses the frozen binary64 input law")
    return Fraction(value)


def _reject_json_constant(value: str) -> None:
    raise StructuralCertificateError(f"nonfinite JSON constant is forbidden: {value}")


def _fraction_text(value: Fraction) -> str:
    value = Fraction(value)
    return f"{value.numerator}/{value.denominator}"


def _json_ready(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _fraction_text(value)
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _json_ready(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def tail_basis(belief: Fraction, period: int) -> tuple[Fraction, ...]:
    b = _fraction(belief)
    if not 0 <= b <= 1:
        raise ValueError("belief outside [0,1]")
    if type(period) is not int or not 1 <= period <= 9:
        raise ValueError("tail basis period outside 1..9")
    k = Fraction(period, 9)
    return Fraction(1), b, k, b * k, k * k


def root_basis(
    action_is_probe: bool,
    period: int,
    total_cost: Fraction,
    linked: bool,
    reliability: Fraction,
) -> tuple[Fraction, ...]:
    if type(action_is_probe) is not bool or type(linked) is not bool:
        raise ValueError("root indicators must be exact booleans")
    if type(period) is not int or (action_is_probe and period != 0) or (
        not action_is_probe and not 1 <= period <= 9
    ):
        raise ValueError("root action/period mismatch")
    a = Fraction(int(action_is_probe))
    k = Fraction(period, 9)
    cost = _fraction(total_cost)
    link = Fraction(int(linked))
    p = _fraction(reliability)
    return (
        Fraction(1),
        (1 - a) * k,
        (1 - a) * k * k,
        a,
        a * cost,
        a * link,
        a * link * p,
    )


def score(coefficients: Sequence[Fraction], basis: Sequence[Fraction]) -> Fraction:
    if len(coefficients) != len(basis):
        raise ValueError("coefficient/basis width mismatch")
    return sum((_fraction(c) * _fraction(x) for c, x in zip(coefficients, basis)), Fraction(0))


def probe_root_target(
    realized_probe_primitive: Fraction,
    belief: Fraction,
    complementary_tail_coefficients: Sequence[Fraction],
) -> Fraction:
    continuation = max(
        score(complementary_tail_coefficients, tail_basis(belief, period)) for period in K_TRAIN
    )
    return _fraction(realized_probe_primitive) + continuation


def _zero_normal(width: int) -> tuple[list[list[Fraction]], list[Fraction]]:
    return (
        [[Fraction(0) for _ in range(width)] for _ in range(width)],
        [Fraction(0) for _ in range(width)],
    )


def _accumulate_normal(
    matrix: list[list[Fraction]],
    rhs: list[Fraction],
    row: Sequence[Fraction],
    target: Fraction,
    weight: int = 1,
) -> None:
    values = tuple(_fraction(value) for value in row)
    if len(values) != len(rhs):
        raise ValueError("normal-equation row width mismatch")
    if type(weight) is not int or weight <= 0:
        raise ValueError("normal-equation weight must be a positive integer")
    y = _fraction(target)
    for i, left in enumerate(values):
        rhs[i] += weight * left * y
        for j, right in enumerate(values):
            matrix[i][j] += weight * left * right


def _eliminate(
    matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]
) -> tuple[int, tuple[Fraction, ...] | None]:
    width = len(rhs)
    if len(matrix) != width or any(len(row) != width for row in matrix):
        raise ValueError("normal-equation matrix must be square")
    work = [[_fraction(value) for value in row] + [_fraction(rhs[index])] for index, row in enumerate(matrix)]
    pivot_row = 0
    pivot_columns: list[int] = []
    for column in range(width):
        selected = next((row for row in range(pivot_row, width) if work[row][column] != 0), None)
        if selected is None:
            continue
        if selected != pivot_row:
            work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot = work[pivot_row][column]
        work[pivot_row] = [value / pivot for value in work[pivot_row]]
        for row in range(width):
            if row == pivot_row or work[row][column] == 0:
                continue
            factor = work[row][column]
            work[row] = [left - factor * right for left, right in zip(work[row], work[pivot_row])]
        pivot_columns.append(column)
        pivot_row += 1
    rank = pivot_row
    if rank != width:
        return rank, None
    solution = [Fraction(0) for _ in range(width)]
    for row, column in enumerate(pivot_columns):
        solution[column] = work[row][-1]
    return rank, tuple(solution)


def _fit_from_normal(
    matrix: Sequence[Sequence[Fraction]],
    rhs: Sequence[Fraction],
    *,
    expected_rank: int,
    row_count: int,
) -> dict[str, Any]:
    rank, coefficients = _eliminate(matrix, rhs)
    return {
        "solver": EXACT_SOLVER_LAW,
        "expected_rank": expected_rank,
        "rank": rank,
        "rank_status": "FULL_RANK" if rank == expected_rank else "RANK_DEFICIENT_STOP",
        "row_count": row_count,
        "normal_matrix": tuple(tuple(value for value in row) for row in matrix),
        "normal_rhs": tuple(rhs),
        "coefficients": coefficients,
    }


def exact_least_squares(
    rows: Iterable[Sequence[Fraction]], targets: Iterable[Fraction], *, expected_rank: int
) -> dict[str, Any]:
    row_values = [tuple(_fraction(value) for value in row) for row in rows]
    target_values = [_fraction(value) for value in targets]
    if not row_values or len(row_values) != len(target_values):
        raise ValueError("least-squares rows and targets must be nonempty and aligned")
    width = len(row_values[0])
    if expected_rank != width or any(len(row) != width for row in row_values):
        raise ValueError("least-squares width/rank contract mismatch")
    matrix, rhs = _zero_normal(width)
    for row, target in zip(row_values, target_values):
        _accumulate_normal(matrix, rhs, row, target)
    return _fit_from_normal(matrix, rhs, expected_rank=expected_rank, row_count=len(row_values))


def _belief(row: Mapping[str, Any]) -> Fraction:
    if row["link"] == "SEVERED":
        return Fraction(1, 2)
    if row["link"] != "LINKED":
        raise ValueError("unknown linkage")
    p = _fraction(row["reliability"])
    count = row["displayed_short_count"]
    if type(count) is not int or not 0 <= count <= 6:
        raise ValueError("displayed count outside 0..6")
    short = Fraction(1, 2) * comb(6, count) * p**count * (1 - p) ** (6 - count)
    long = Fraction(1, 2) * comb(6, count) * (1 - p) ** count * p ** (6 - count)
    return short / (short + long)


def _probe_primitive(row: Mapping[str, Any]) -> Fraction:
    ledger = row["primitive_ledger"]
    return sum(
        (_fraction(ledger[name]) for name in ("probe_service", "probe_time", "probe_energy")),
        Fraction(0),
    )


def reference_tape_member(seed_slot: str, context_index: int) -> Path:
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown fixed seed slot")
    if type(context_index) is not int or not 0 <= context_index < 8:
        raise ValueError("context index outside 0..7")
    ordinal = SEED_SLOTS.index(seed_slot) * 8 + context_index
    return FIXED_BUNDLE_ROOT / f"members/{ordinal:03d}.bin"


def reference_tape_ordinal(seed_slot: str, context_index: int) -> int:
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown fixed seed slot")
    if type(context_index) is not int or not 0 <= context_index < 8:
        raise ValueError("context index outside 0..7")
    return SEED_SLOTS.index(seed_slot) * 8 + context_index


def _validate_tape_bytes(tape_bytes: tuple[bytes, ...]) -> None:
    if type(tape_bytes) is not tuple or len(tape_bytes) != 80 or any(type(item) is not bytes for item in tape_bytes):
        raise StructuralCertificateError("fit requires exactly 80 captured tape byte strings")


def _iter_seed_rows(seed_slot: str, tape_bytes: tuple[bytes, ...]) -> Iterable[dict[str, Any]]:
    _validate_tape_bytes(tape_bytes)
    for context_index in range(8):
        member = reference_tape_member(seed_slot, context_index)
        ordinal = int(member.stem)
        with gzip.GzipFile(fileobj=BytesIO(tape_bytes[ordinal]), mode="rb") as stream:
            for raw_line in stream:
                row = json.loads(raw_line, parse_constant=_reject_json_constant)
                if row.get("seed_slot") != seed_slot or row.get("context_id") is None:
                    raise StructuralCertificateError("retained row binding mismatch")
                if row.get("period") not in K_TRAIN:
                    raise StructuralCertificateError("non-training period reached exact fit")
                yield row


def _new_counter() -> dict[str, Any]:
    return {
        "rows": 0,
        "groups": set(),
        "contexts": {},
        "strata": {},
    }


def _count_row(counter: dict[str, Any], row: Mapping[str, Any]) -> None:
    counter["rows"] += 1
    counter["groups"].add(f"{row['seed_slot']}|{row['index']}")
    cell = str(row["context_id"])
    counter["contexts"][cell] = counter["contexts"].get(cell, 0) + 1
    stratum = f"{row['root_action']}:{row['period']}"
    counter["strata"][stratum] = counter["strata"].get(stratum, 0) + 1


def _finish_counter(counter: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rows": counter["rows"],
        "groups": len(counter["groups"]),
        "contexts": dict(sorted(counter["contexts"].items())),
        "strata": dict(sorted(counter["strata"].items())),
    }


def _fit_seed(seed_slot: str, tape_bytes: tuple[bytes, ...]) -> dict[str, Any]:
    tail_groups: list[dict[tuple[tuple[Fraction, ...], Fraction], int]] = [{}, {}]
    tail_counts = [_new_counter(), _new_counter()]
    for row in _iter_seed_rows(seed_slot, tape_bytes):
        if row["root_action"] != "PROBE":
            continue
        source_fold = fold_id(seed_slot, int(row["index"]))
        key = (tail_basis(_belief(row), int(row["period"])), _fraction(row["tail_return"]))
        tail_groups[source_fold][key] = tail_groups[source_fold].get(key, 0) + 1
        _count_row(tail_counts[source_fold], row)

    tail_fits = []
    for fold in (0, 1):
        matrix, rhs = _zero_normal(5)
        for (basis, target), weight in tail_groups[fold].items():
            _accumulate_normal(matrix, rhs, basis, target, weight)
        tail_fits.append(
            _fit_from_normal(matrix, rhs, expected_rank=5, row_count=tail_counts[fold]["rows"])
        )
    policies = []
    for policy_fold in (0, 1):
        complement = 1 - policy_fold
        tail_fit = tail_fits[complement]
        root_groups: dict[tuple[tuple[Fraction, ...], Fraction], int] = {}
        root_count = _new_counter()
        coefficients = tail_fit["coefficients"]
        for row in _iter_seed_rows(seed_slot, tape_bytes):
            if fold_id(seed_slot, int(row["index"])) != policy_fold:
                continue
            _count_row(root_count, row)
            if coefficients is None:
                continue
            is_probe = row["root_action"] == "PROBE"
            basis = root_basis(
                is_probe,
                0 if is_probe else int(row["period"]),
                _fraction(row["total_cost"]),
                row["link"] == "LINKED",
                _fraction(row["reliability"]),
            )
            target = (
                probe_root_target(_probe_primitive(row), _belief(row), coefficients)
                if is_probe
                else _fraction(row["tail_return"])
            )
            key = (basis, target)
            root_groups[key] = root_groups.get(key, 0) + 1
        root_matrix, root_rhs = _zero_normal(7)
        for (basis, target), weight in root_groups.items():
            _accumulate_normal(root_matrix, root_rhs, basis, target, weight)
        root_fit = _fit_from_normal(
            root_matrix, root_rhs, expected_rank=7, row_count=root_count["rows"]
        )
        policies.append(
            {
                "policy_fold": policy_fold,
                "root_source_fold": policy_fold,
                "tail_source_fold": complement,
                "root": root_fit,
                "tail": tail_fit,
                "root_support": _finish_counter(root_count),
                "tail_support": _finish_counter(tail_counts[complement]),
            }
        )
    return {"seed_slot": seed_slot, "policies": policies}


def _assessment_empty_root_fit(row_count: int) -> dict[str, Any]:
    """Reproduce the scientific no-tail-solution root record without a second solve."""
    return {
        "solver": EXACT_SOLVER_LAW,
        "expected_rank": 7,
        "rank": 0,
        "rank_status": "RANK_DEFICIENT_STOP",
        "row_count": row_count,
        "normal_matrix": tuple(
            tuple(Fraction(0) for _ in range(7)) for _ in range(7)
        ),
        "normal_rhs": tuple(Fraction(0) for _ in range(7)),
        "coefficients": None,
    }


def _assessment_fit_seed(
    seed_slot: str, tape_bytes: tuple[bytes, ...]
) -> dict[str, Any]:
    """Perform fixed root work while preserving the scientific fit document.

    A missing scientific tail solution selects the fixed zero vector only for
    technical resource work. The computed padding root system is discarded and
    the returned root record remains the exact scientific no-solution record.
    """
    tail_groups: list[dict[tuple[tuple[Fraction, ...], Fraction], int]] = [{}, {}]
    tail_counts = [_new_counter(), _new_counter()]
    for row in _iter_seed_rows(seed_slot, tape_bytes):
        if row["root_action"] != "PROBE":
            continue
        source_fold = fold_id(seed_slot, int(row["index"]))
        key = (
            tail_basis(_belief(row), int(row["period"])),
            _fraction(row["tail_return"]),
        )
        tail_groups[source_fold][key] = tail_groups[source_fold].get(key, 0) + 1
        _count_row(tail_counts[source_fold], row)

    tail_fits = []
    for fold in (0, 1):
        matrix, rhs = _zero_normal(5)
        for (basis, target), weight in tail_groups[fold].items():
            _accumulate_normal(matrix, rhs, basis, target, weight)
        tail_fits.append(
            _fit_from_normal(
                matrix, rhs, expected_rank=5, row_count=tail_counts[fold]["rows"]
            )
        )

    policies = []
    for policy_fold in (0, 1):
        complement = 1 - policy_fold
        tail_fit = tail_fits[complement]
        scientific_coefficients = tail_fit["coefficients"]
        work_coefficients = (
            scientific_coefficients
            if scientific_coefficients is not None
            else ASSESSMENT_PADDING_TAIL_COEFFICIENTS
        )
        work_root_matrix, work_root_rhs = _zero_normal(7)
        root_count = _new_counter()
        for row in _iter_seed_rows(seed_slot, tape_bytes):
            if fold_id(seed_slot, int(row["index"])) != policy_fold:
                continue
            _count_row(root_count, row)
            is_probe = row["root_action"] == "PROBE"
            basis = root_basis(
                is_probe,
                0 if is_probe else int(row["period"]),
                _fraction(row["total_cost"]),
                row["link"] == "LINKED",
                _fraction(row["reliability"]),
            )
            target = (
                probe_root_target(
                    _probe_primitive(row), _belief(row), work_coefficients
                )
                if is_probe
                else _fraction(row["tail_return"])
            )
            _accumulate_normal(work_root_matrix, work_root_rhs, basis, target)
        work_root_fit = _fit_from_normal(
            work_root_matrix,
            work_root_rhs,
            expected_rank=7,
            row_count=root_count["rows"],
        )
        root_fit = (
            work_root_fit
            if scientific_coefficients is not None
            else _assessment_empty_root_fit(root_count["rows"])
        )
        policies.append(
            {
                "policy_fold": policy_fold,
                "root_source_fold": policy_fold,
                "tail_source_fold": complement,
                "root": root_fit,
                "tail": tail_fit,
                "root_support": _finish_counter(root_count),
                "tail_support": _finish_counter(tail_counts[complement]),
            }
        )
    return {"seed_slot": seed_slot, "policies": policies}


def _assessment_fit_document(
    binding_receipt: Mapping[str, Any], tape_bytes: tuple[bytes, ...]
) -> dict[str, Any]:
    """Return one unsealed in-memory exact document for technical assessment."""
    _validate_tape_bytes(tape_bytes)
    seeds = [_assessment_fit_seed(seed_slot, tape_bytes) for seed_slot in SEED_SLOTS]
    full_rank = all(
        policy["root"]["rank"] == 7 and policy["tail"]["rank"] == 5
        for seed in seeds
        for policy in seed["policies"]
    )
    return {
        "format": FIT_FORMAT,
        "complete": True,
        "sealed": True,
        "binding_receipt": dict(binding_receipt),
        "fold_law": {
            "group_key": "(seed_slot,index)",
            "fold_id": "(index//10)%2",
            "dependence_claim": FOLD_DEPENDENCE_CLAIM,
            "source_assignment": "GLOBAL_BALANCED_RANK_WITH_CROSS_FOLD_DEPENDENCE",
            "behavior_strata": "ACTION_PERIOD_GROUP_COUNTS_EXACTLY_EQUAL_WITHIN_EACH_HALF",
            "combination": "BOTH_FOLD_POLICIES_MUST_PASS",
        },
        "tail_basis": list(TAIL_BASIS),
        "root_basis": list(ROOT_BASIS),
        "solver": EXACT_SOLVER_LAW,
        "arithmetic": EXACT_ARITHMETIC_LAW,
        "expected_ranks": {"tail": 5, "root": 7},
        "activity": dict(FIT_ACTIVITY),
        "process_boundary_claim": FIT_DATA_DEPENDENCY_CLAIM,
        "full_rank": full_rank,
        "seeds": seeds,
    }


def _fit_document(binding_receipt: Mapping[str, Any], tape_bytes: tuple[bytes, ...]) -> dict[str, Any]:
    _validate_tape_bytes(tape_bytes)
    seeds = [_fit_seed(seed_slot, tape_bytes) for seed_slot in SEED_SLOTS]
    full_rank = all(
        policy["root"]["rank"] == 7 and policy["tail"]["rank"] == 5
        for seed in seeds
        for policy in seed["policies"]
    )
    return {
        "format": FIT_FORMAT,
        "complete": True,
        "sealed": True,
        "binding_receipt": dict(binding_receipt),
        "fold_law": {
            "group_key": "(seed_slot,index)",
            "fold_id": "(index//10)%2",
            "dependence_claim": FOLD_DEPENDENCE_CLAIM,
            "source_assignment": "GLOBAL_BALANCED_RANK_WITH_CROSS_FOLD_DEPENDENCE",
            "behavior_strata": "ACTION_PERIOD_GROUP_COUNTS_EXACTLY_EQUAL_WITHIN_EACH_HALF",
            "combination": "BOTH_FOLD_POLICIES_MUST_PASS",
        },
        "tail_basis": list(TAIL_BASIS),
        "root_basis": list(ROOT_BASIS),
        "solver": EXACT_SOLVER_LAW,
        "arithmetic": EXACT_ARITHMETIC_LAW,
        "expected_ranks": {"tail": 5, "root": 7},
        "activity": dict(FIT_ACTIVITY),
        "process_boundary_claim": FIT_DATA_DEPENDENCY_CLAIM,
        "full_rank": full_rank,
        "seeds": seeds,
    }


def _create_once(path: Path, payload: bytes) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def fit_structural_artifact(
    *, binding_receipt: Mapping[str, Any], tape_bytes: tuple[bytes, ...], output_path: str | Path
) -> Path:
    """Fit only from odd-period retained rows and publish one exact sealed value."""
    document = _fit_document(binding_receipt, tape_bytes)
    return _create_once(Path(output_path), canonical_bytes(document))


FIT_PHASE_FUNCTIONS = (
    "fold_group_key",
    "fold_id",
    "_fraction",
    "_reject_json_constant",
    "_fraction_text",
    "_json_ready",
    "canonical_bytes",
    "tail_basis",
    "root_basis",
    "score",
    "probe_root_target",
    "_zero_normal",
    "_accumulate_normal",
    "_eliminate",
    "_fit_from_normal",
    "exact_least_squares",
    "_belief",
    "_probe_primitive",
    "reference_tape_member",
    "reference_tape_ordinal",
    "_validate_tape_bytes",
    "_iter_seed_rows",
    "_new_counter",
    "_count_row",
    "_finish_counter",
    "_fit_seed",
    "_fit_document",
    "_create_once",
)


def _parse_fraction(value: Any) -> Fraction:
    if not isinstance(value, str) or "/" not in value:
        raise StructuralCertificateError("exact rational text required")
    numerator, denominator = value.split("/", 1)
    try:
        parsed = Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError) as exc:
        raise StructuralCertificateError("noncanonical rational text") from exc
    if _fraction_text(parsed) != value:
        raise StructuralCertificateError("noncanonical rational text")
    return parsed


_RATIONAL_TEXT = re.compile(r"[+-]?\d+/[+-]?\d+")


def _decode_exact(value: Any) -> Any:
    if isinstance(value, str) and _RATIONAL_TEXT.fullmatch(value):
        return _parse_fraction(value)
    if isinstance(value, list):
        return [_decode_exact(item) for item in value]
    if isinstance(value, dict):
        return {key: _decode_exact(item) for key, item in value.items()}
    return value


def _load_sealed(path: str | Path) -> tuple[bytes, dict[str, Any]]:
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw, parse_constant=_reject_json_constant)
        canonical = canonical_bytes(value)
    except (
        UnicodeDecodeError, json.JSONDecodeError, StructuralCertificateError,
        ValueError, TypeError,
    ) as exc:
        raise StructuralCertificateError("sealed fit is not canonical JSON") from exc
    if raw != canonical:
        raise StructuralCertificateError("sealed fit bytes are not canonical")
    decoded = _decode_exact(value)
    if decoded.get("format") != FIT_FORMAT or decoded.get("complete") is not True or decoded.get("sealed") is not True:
        raise StructuralCertificateError("sealed fit envelope mismatch")
    return raw, decoded


def _validate_fit_structure(fit: Mapping[str, Any], binding_receipt: Mapping[str, Any]) -> None:
    required = {
        "format", "complete", "sealed", "binding_receipt", "fold_law", "tail_basis",
        "root_basis", "solver", "arithmetic", "expected_ranks", "activity", "full_rank", "seeds",
        "process_boundary_claim",
    }
    if set(fit) != required or fit["binding_receipt"] != dict(binding_receipt):
        raise StructuralCertificateError("fit envelope or source binding receipt mismatch")
    if fit["tail_basis"] != list(TAIL_BASIS) or fit["root_basis"] != list(ROOT_BASIS):
        raise StructuralCertificateError("fit basis law mismatch")
    if fit["solver"] != EXACT_SOLVER_LAW or fit["expected_ranks"] != {"tail": 5, "root": 7}:
        raise StructuralCertificateError("fit solver/rank law mismatch")
    if fit["arithmetic"] != EXACT_ARITHMETIC_LAW:
        raise StructuralCertificateError("fit arithmetic law mismatch")
    if fit["activity"] != FIT_ACTIVITY:
        raise StructuralCertificateError("fit activity counters are not zero")
    if fit["process_boundary_claim"] != FIT_DATA_DEPENDENCY_CLAIM:
        raise StructuralCertificateError("fit process-boundary claim mismatch")
    fold_law = fit["fold_law"]
    if fold_law != {
        "group_key": "(seed_slot,index)",
        "fold_id": "(index//10)%2",
        "dependence_claim": FOLD_DEPENDENCE_CLAIM,
        "source_assignment": "GLOBAL_BALANCED_RANK_WITH_CROSS_FOLD_DEPENDENCE",
        "behavior_strata": "ACTION_PERIOD_GROUP_COUNTS_EXACTLY_EQUAL_WITHIN_EACH_HALF",
        "combination": "BOTH_FOLD_POLICIES_MUST_PASS",
    }:
        raise StructuralCertificateError("fit fold/dependence law mismatch")
    if [seed.get("seed_slot") for seed in fit["seeds"]] != list(SEED_SLOTS):
        raise StructuralCertificateError("fit fixed-slot order mismatch")
    observed_full_rank = True
    expected_root_strata = {f"{action}:{period}" for action in ("PROBE", "IMMEDIATE") for period in K_TRAIN}
    expected_tail_strata = {f"PROBE:{period}" for period in K_TRAIN}
    for seed in fit["seeds"]:
        policies = seed.get("policies")
        if not isinstance(policies, list) or [item.get("policy_fold") for item in policies] != [0, 1]:
            raise StructuralCertificateError("fit policy-fold order mismatch")
        for policy in policies:
            fold = policy["policy_fold"]
            if policy["root_source_fold"] != fold or policy["tail_source_fold"] != 1 - fold:
                raise StructuralCertificateError("fit complementary-fold pairing mismatch")
            for name, width in (("tail", 5), ("root", 7)):
                record = policy[name]
                expected_keys = {
                    "solver", "expected_rank", "rank", "rank_status", "row_count",
                    "normal_matrix", "normal_rhs", "coefficients",
                }
                if set(record) != expected_keys or record["solver"] != EXACT_SOLVER_LAW:
                    raise StructuralCertificateError("fit exact-system schema mismatch")
                expected_rows = 40_960 if name == "tail" else 81_920
                if record["row_count"] != expected_rows:
                    raise StructuralCertificateError("fit exact-system row count mismatch")
                rank, coefficients = _rank_and_solution(record, width)
                expected_status = "FULL_RANK" if rank == width else "RANK_DEFICIENT_STOP"
                if record["rank_status"] != expected_status:
                    raise StructuralCertificateError("fit rank status mismatch")
                observed_full_rank &= coefficients is not None
            root_support = policy["root_support"]
            tail_support = policy["tail_support"]
            if (
                set(root_support) != {"rows", "groups", "contexts", "strata"}
                or root_support["rows"] != 81_920
                or root_support["groups"] != 10_240
                or set(root_support["contexts"]) != set(CONTEXT_IDS)
                or set(root_support["contexts"].values()) != {10_240}
                or set(root_support["strata"]) != expected_root_strata
                or set(root_support["strata"].values()) != {8_192}
            ):
                raise StructuralCertificateError("root fold support mismatch")
            if (
                set(tail_support) != {"rows", "groups", "contexts", "strata"}
                or tail_support["rows"] != 40_960
                or tail_support["groups"] != 5_120
                or set(tail_support["contexts"]) != set(CONTEXT_IDS)
                or set(tail_support["contexts"].values()) != {5_120}
                or set(tail_support["strata"]) != expected_tail_strata
                or set(tail_support["strata"].values()) != {8_192}
            ):
                raise StructuralCertificateError("tail complementary-fold support mismatch")
    if fit["full_rank"] is not observed_full_rank:
        raise StructuralCertificateError("fit aggregate rank state mismatch")


def _rank_and_solution(fit: Mapping[str, Any], expected: int) -> tuple[int, tuple[Fraction, ...] | None]:
    matrix = fit["normal_matrix"]
    rhs = fit["normal_rhs"]
    if (
        type(matrix) not in (list, tuple)
        or len(matrix) != expected
        or any(type(row) not in (list, tuple) or len(row) != expected for row in matrix)
        or any(type(value) is not Fraction for row in matrix for value in row)
        or type(rhs) not in (list, tuple)
        or len(rhs) != expected
        or any(type(value) is not Fraction for value in rhs)
    ):
        raise StructuralCertificateError("exact rational normal system must contain only Fraction values")
    stored = fit["coefficients"]
    if stored is not None and (
        type(stored) not in (list, tuple)
        or len(stored) != expected
        or any(type(value) is not Fraction for value in stored)
    ):
        raise StructuralCertificateError("exact rational coefficients must be None or a Fraction sequence")
    rank, coefficients = _eliminate(matrix, rhs)
    if rank != fit["rank"] or fit["expected_rank"] != expected:
        raise StructuralCertificateError("stored exact rank mismatch")
    if (stored is None) != (coefficients is None) or (
        coefficients is not None and tuple(stored) != coefficients
    ):
        raise StructuralCertificateError("stored exact coefficients mismatch")
    return rank, coefficients


def _strict_choice(values: Mapping[Any, Fraction]) -> tuple[Any, Fraction]:
    ranked = sorted(((value, str(label), label) for label, value in values.items()), reverse=True)
    if len(ranked) < 2 or ranked[0][0] <= ranked[1][0]:
        raise NonUniquePolicyStop("score tie or missing alternative")
    return ranked[0][2], ranked[0][0] - ranked[1][0]


def configure_postseal_runtime(runtime: Mapping[str, Any]) -> None:
    required = {
        "K_TEST", "as_fraction", "context_id", "contexts", "direct_probe_value",
        "expected_tail_value", "informed_value", "joint_count_probability", "optimal_tail",
        "posterior_short",
    }
    if not isinstance(runtime, Mapping) or set(runtime) != required:
        raise StructuralCertificateError("post-seal runtime surface mismatch")
    global _POSTSEAL_RUNTIME
    _POSTSEAL_RUNTIME = dict(runtime)


def _postseal_contexts():
    if _POSTSEAL_RUNTIME is None:
        raise StructuralCertificateError("post-seal runtime has not been bound")
    return tuple(
        _POSTSEAL_RUNTIME[name]
        for name in (
            "K_TEST", "as_fraction", "context_id", "contexts", "direct_probe_value",
            "expected_tail_value", "informed_value", "joint_count_probability", "optimal_tail",
            "posterior_short",
        )
    )


def _assess_policy_strict(policy: Mapping[str, Any]) -> dict[str, Any]:
    (
        K_TEST,
        as_fraction,
        context_id,
        contexts,
        direct_probe_value,
        expected_tail_value,
        informed_value,
        joint_count_probability,
        optimal_tail,
        posterior_short,
    ) = _postseal_contexts()
    _, tail_coefficients = _rank_and_solution(policy["tail"], 5)
    _, root_coefficients = _rank_and_solution(policy["root"], 7)
    if tail_coefficients is None or root_coefficients is None:
        return {"pass": False, "reason": "RANK_DEFICIENT_STOP", "rank_pass": False, "unique": False}
    root_vector: dict[str, str] = {}
    expected_root_vector: dict[str, str] = {}
    root_margins: list[Fraction] = []
    tail_margins: list[Fraction] = []
    regrets: list[Fraction] = []
    agreements: dict[str, Fraction] = {}
    selected_tail: dict[str, dict[str, int]] = {}
    for context in contexts():
        cell = context_id(context)
        p = as_fraction(context["reliability"])
        cost = as_fraction(context["total_cost"])
        linked = context["link"] == "LINKED"
        tail_policy: dict[str, int] = {}
        agreement = Fraction(0)
        continuation = Fraction(0)
        for count in range(7):
            belief = posterior_short(p, count) if linked else Fraction(1, 2)
            scores = {
                period: score(tail_coefficients, (
                    Fraction(1), belief, Fraction(period, 9), belief * Fraction(period, 9), Fraction(period, 9) ** 2
                ))
                for period in K_TEST
            }
            selected, margin = _strict_choice(scores)
            tail_policy[str(count)] = int(selected)
            tail_margins.append(margin)
            mass = joint_count_probability("SHORT", p, count) + joint_count_probability("LONG", p, count)
            expected_period = optimal_tail(K_TEST, belief)[0]
            if selected == expected_period:
                agreement += mass
            continuation += mass * expected_tail_value(int(selected), belief)
        selected_tail[cell] = tail_policy
        agreements[cell] = agreement
        root_scores: dict[str, Fraction] = {
            "PROBE": score(root_coefficients, (
                Fraction(1), Fraction(0), Fraction(0), Fraction(1), cost,
                Fraction(int(linked)), Fraction(int(linked)) * p,
            ))
        }
        for period in K_TEST:
            scaled = Fraction(period, 9)
            root_scores[f"IMMEDIATE:{period}"] = score(
                root_coefficients,
                (Fraction(1), scaled, scaled * scaled, Fraction(0), Fraction(0), Fraction(0), Fraction(0)),
            )
        selected_root, root_margin = _strict_choice(root_scores)
        root_margins.append(root_margin)
        root_vector[cell] = "PROBE" if selected_root == "PROBE" else "IMMEDIATE"
        immediate_values = {period: expected_tail_value(period, Fraction(1, 2)) for period in K_TEST}
        baseline = max((value, -period, period) for period, value in immediate_values.items())[0]
        expected_probe = (informed_value(p, K_TEST) if linked else baseline) + direct_probe_value(cost)
        oracle_values = {"PROBE": expected_probe, **{f"IMMEDIATE:{k}": v for k, v in immediate_values.items()}}
        oracle_root, _ = _strict_choice(oracle_values)
        expected_root_vector[cell] = "PROBE" if oracle_root == "PROBE" else "IMMEDIATE"
        realized = continuation + direct_probe_value(cost) if selected_root == "PROBE" else immediate_values[int(str(selected_root).split(":")[1])]
        regrets.append(max(oracle_values.values()) - realized)
    maximum_regret = max(regrets)
    minimum_agreement = min(agreements.values())
    passed = bool(
        root_vector == expected_root_vector
        and maximum_regret <= Fraction(1, 50)
        and minimum_agreement >= Fraction(19, 20)
        and min(root_margins) > 0
        and min(tail_margins) > 0
    )
    return {
        "pass": passed,
        "reason": "PASS" if passed else "COMPETENCE_PREDICATE_STOP",
        "rank_pass": True,
        "unique": True,
        "root_vector": root_vector,
        "expected_root_vector": expected_root_vector,
        "selected_tail_periods": selected_tail,
        "maximum_regret": maximum_regret,
        "minimum_forced_probe_tail_agreement": minimum_agreement,
        "minimum_root_margin": min(root_margins),
        "minimum_tail_margin": min(tail_margins),
        "root_unique": min(root_margins) > 0,
        "tail_unique": min(tail_margins) > 0,
    }


def _assess_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return _assess_policy_strict(policy)
    except NonUniquePolicyStop:
        return {
            "pass": False,
            "reason": "NONUNIQUE_POLICY_STOP",
            "rank_pass": True,
            "unique": False,
        }


def _certificate_document(
    fit: Mapping[str, Any],
    binding_receipt: Mapping[str, Any],
    postfit_binding_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_fit_structure(fit, binding_receipt)
    seed_results = []
    for seed in fit["seeds"]:
        folds = [
            {"policy_fold": policy["policy_fold"], **_assess_policy(policy)}
            for policy in seed["policies"]
        ]
        seed_results.append(
            {"seed_slot": seed["seed_slot"], "folds": folds, "pass": all(item["pass"] for item in folds)}
        )
    policy_results = [fold for seed in seed_results for fold in seed["folds"]]
    rank_pass = all(item["rank_pass"] for item in policy_results)
    unique = rank_pass and all(item["unique"] for item in policy_results)
    competent = unique and all(item["pass"] for item in policy_results)
    if not rank_pass:
        disposition = "STOP_FOLD_RANK"
    elif not unique:
        disposition = "STOP_NONUNIQUE_POLICY"
    elif not competent:
        disposition = "STOP_STRUCTURAL_COMPETENCE"
    else:
        disposition = "STRUCTURAL_PREREQUISITE_PASS"
    return {
        "format": CERTIFICATE_FORMAT,
        "complete": True,
        "binding_receipt": dict(binding_receipt),
        "postfit_binding_receipt": dict(postfit_binding_receipt),
        "fit_format": FIT_FORMAT,
        "fold_combination": "AND",
        "fixed_seed_slots": list(SEED_SLOTS),
        "seeds": seed_results,
        "gate_counts": {
            "fold_policies": len(policy_results),
            "rank_pass": sum(item["rank_pass"] for item in policy_results),
            "unique": sum(item["unique"] for item in policy_results),
            "competent": sum(item["pass"] for item in policy_results),
        },
        "disposition": disposition,
        "prerequisite_pass": competent,
        "admit": False,
        "next_action": "ROOT_NEW_OBJECT_DECISION_REQUIRED" if competent else "NONE",
        "process_boundary_claim": FIT_DATA_DEPENDENCY_CLAIM,
        "claim": "EXACT_FIXED_PANEL_STRUCTURAL_PRIOR_COMPETENCE_ONLY_NO_SEED_SUPERPOPULATION",
    }


def evaluate_sealed_fit(
    *,
    fit_path: str | Path,
    fit_reference_path: str | Path,
    binding_receipt: Mapping[str, Any],
    postfit_binding_receipt: Mapping[str, Any],
    output_path: str | Path,
) -> Path:
    raw, fit = _load_sealed(fit_path)
    if raw != Path(fit_reference_path).read_bytes():
        raise StructuralCertificateError("sealed fit/reference byte mismatch")
    document = _certificate_document(fit, binding_receipt, postfit_binding_receipt)
    return _create_once(Path(output_path), canonical_bytes(document))


def validate_certificate(
    *,
    fit_path: str | Path,
    fit_reference_path: str | Path,
    certificate_path: str | Path,
    binding_receipt: Mapping[str, Any],
    postfit_binding_receipt: Mapping[str, Any],
    tape_bytes: tuple[bytes, ...],
    recomputed_fit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    raw, fit = _load_sealed(fit_path)
    if raw != Path(fit_reference_path).read_bytes():
        raise StructuralCertificateError("sealed fit/reference byte mismatch")
    exact_recomputation = (
        _fit_document(binding_receipt, tape_bytes)
        if recomputed_fit is None
        else dict(recomputed_fit)
    )
    if raw != canonical_bytes(exact_recomputation):
        raise StructuralCertificateError("stored fit differs from full exact recomputation")
    _validate_fit_structure(fit, binding_receipt)
    expected = _certificate_document(fit, binding_receipt, postfit_binding_receipt)
    raw_certificate = Path(certificate_path).read_bytes()
    observed = json.loads(raw_certificate)
    if raw_certificate != canonical_bytes(observed) or observed != _json_ready(expected):
        raise StructuralCertificateError("certificate structure or exact metrics mismatch")
    return observed
