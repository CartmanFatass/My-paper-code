"""Synthetic SCOPE-1S Q16 unit certificate and actual-binding validator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from fractions import Fraction
import itertools
import json
from typing import Mapping, Sequence


F = Fraction
HORIZON = 64
TARGET_BITS = (0, 0, 0, 0, 1, 1, 1, 1)
DONOR_PERMUTATION = (1, 4, 5, 0, 2, 3, 7, 6)


class Category(str, Enum):
    CURRENT = "current-only"
    HISTORY = "historical-payload"
    AUDIT = "audit-only"
    FORBIDDEN = "forbidden-leakage"
    POST = "post-treatment"


class Choice(str, Enum):
    RESET = "Reset"
    Z0 = "z0"
    Z1 = "z1"


CHOICES = (Choice.RESET, Choice.Z0, Choice.Z1)


@dataclass(frozen=True)
class ByteField:
    name: str
    start: int
    stop: int
    category: Category


@dataclass(frozen=True)
class AncestryManifest:
    source_bytes: bytes
    fields: tuple[ByteField, ...]
    actor_edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CompatibilityKey:
    task_hash: str
    environment_hash: str
    roster_n: int
    anonymous_role: int
    absence: int
    schema_hash: str
    quantizer_hash: str
    writer_hash: str
    reader_hash: str
    actor_hash: str
    recurrent_manifest: str
    normalizer_hash: str
    action_mask_hash: str
    partner_checkpoint: str
    import_adapter_hash: str
    cost_schedule: str


@dataclass(frozen=True)
class Cell:
    name: str
    weight: F
    x: bytes
    key: CompatibilityKey


@dataclass(frozen=True)
class Q16Atom:
    name: str
    payload: bytes


@dataclass(frozen=True)
class Carrier:
    cell_name: str
    unit: int
    x: bytes
    key: CompatibilityKey
    target_bit: int
    atom: Q16Atom
    source_owner: str
    source_epoch: int


@dataclass(frozen=True)
class ClusterCertificate:
    cluster_ids: tuple[str, ...]
    horizons: tuple[int, ...]
    cross_cluster_edges: tuple[tuple[str, str], ...]
    source_actor_hash: str
    evaluated_actor_hash: str


@dataclass(frozen=True)
class BoundCell:
    name: str
    x_closed: bool
    prior_epoch_descendants_in_x: bool
    distinct_complete_atoms: int
    same_x_k_outcome_divergent: bool
    tv: F
    crossover_gaps: tuple[F, F]
    current_only_gap: F
    donor_valid: bool
    h64_closed: bool
    zero_policy_generation_distance: bool


@dataclass(frozen=True)
class CertificateResult:
    terminal: str
    actual_instance_status: str
    missing_actual_objects: tuple[str, ...]
    actor_tv: F
    crossover_gaps: tuple[F, F]
    correct_value: F
    reset_value: F
    current_only_value: F
    deranged_value: F
    current_only_maps: int
    donor_table: tuple[tuple[str, int], ...]
    invariants: tuple[tuple[str, bool], ...]

    def to_bytes(self) -> bytes:
        return json.dumps(
            _jsonable(self), separators=(",", ":"), sort_keys=True
        ).encode()


def build_manifest() -> AncestryManifest:
    return AncestryManifest(
        source_bytes=bytes(range(38)),
        fields=(
            ByteField("current_state", 0, 4, Category.CURRENT),
            ByteField("action_mask", 4, 6, Category.CURRENT),
            ByteField("recurrent_state", 6, 10, Category.CURRENT),
            ByteField("q16_atom", 10, 26, Category.HISTORY),
            ByteField("audit_record", 26, 30, Category.AUDIT),
            ByteField("source_owner_epoch", 30, 34, Category.FORBIDDEN),
            ByteField("outcome", 34, 38, Category.POST),
        ),
        actor_edges=(
            ("current_state", "actor"),
            ("action_mask", "actor"),
            ("recurrent_state", "actor"),
            ("q16_atom", "import_adapter"),
            ("import_adapter", "actor"),
        ),
    )


def validate_manifest(manifest: AncestryManifest) -> bool:
    fields = tuple(sorted(manifest.fields, key=lambda item: item.start))
    contiguous = fields[0].start == 0 and fields[-1].stop == len(manifest.source_bytes)
    contiguous &= all(left.stop == right.start for left, right in zip(fields, fields[1:]))
    categories = {field.category for field in fields}
    current_names = {field.name for field in fields if field.category is Category.CURRENT}
    history_to_current = any(
        source == "q16_atom" and target in current_names
        for source, target in manifest.actor_edges
    )
    return contiguous and categories == set(Category) and not history_to_current


def current_x(manifest: AncestryManifest) -> bytes:
    if not validate_manifest(manifest):
        raise ValueError("incomplete or leaking X ancestry manifest")
    chunks = (
        manifest.source_bytes[field.start : field.stop]
        for field in manifest.fields
        if field.category is Category.CURRENT
    )
    return b"".join(chunks)


def build_key(role: int, absence: int) -> CompatibilityKey:
    if (role, absence) not in ((0, 4), (1, 8)):
        raise ValueError("unit compatibility role/absence mismatch")
    return CompatibilityKey(
        "task-v1",
        "env-v1",
        3,
        role,
        absence,
        "q16-schema-v1",
        "quantizer-v1",
        "writer-v1",
        "reader-v1",
        "actor-v1",
        "recurrent-v1",
        "normalizer-v1",
        "mask-v1",
        "partner-chi",
        "adapter-v1",
        "import-cost-4",
    )


def build_cells() -> tuple[Cell, Cell]:
    x = current_x(build_manifest())
    return (
        Cell("s0", F(1, 2), x, build_key(0, 4)),
        Cell("s1", F(1, 2), x, build_key(1, 8)),
    )


def q16_atom(bit: int) -> Q16Atom:
    if bit not in (0, 1):
        raise ValueError("Q16 atom bit must be binary")
    return Q16Atom(f"z{bit}", bytes((bit,)) * 16)


def actor_kernel(choice: Choice) -> tuple[F, F]:
    if choice in (Choice.RESET, Choice.Z0):
        return F(1), F(0)
    return F(0), F(1)


def total_variation(left: Sequence[F], right: Sequence[F]) -> F:
    return sum((abs(a - b) for a, b in zip(left, right)), F(0)) / 2


def value(target_bit: int, choice: Choice) -> F:
    action = 0 if choice in (Choice.RESET, Choice.Z0) else 1
    import_cost = 0 if choice is Choice.RESET else 4
    return F(HORIZON if action == target_bit else 0) - import_cost


def enumerate_current_only_maps(cells: Sequence[Cell]) -> tuple[tuple[tuple[Choice, ...], F], ...]:
    rows = []
    for mapping in itertools.product(CHOICES, repeat=len(cells)):
        expected = F(0)
        for cell, choice in zip(cells, mapping):
            cell_value = sum((value(bit, choice) for bit in TARGET_BITS), F(0)) / len(TARGET_BITS)
            expected += cell.weight * cell_value
        rows.append((mapping, expected))
    return tuple(rows)


def build_carriers(cell: Cell) -> tuple[Carrier, ...]:
    return tuple(
        Carrier(
            cell.name,
            index,
            cell.x,
            cell.key,
            bit,
            q16_atom(bit),
            f"source-{index % 3}",
            100 + index,
        )
        for index, bit in enumerate(TARGET_BITS)
    )


def donor_rows(carriers: Sequence[Carrier]) -> tuple[tuple[Carrier, Carrier], ...]:
    if len(carriers) != len(DONOR_PERMUTATION):
        raise ValueError("donor population must have eight units")
    return tuple(
        (target, carriers[DONOR_PERMUTATION[index]])
        for index, target in enumerate(carriers)
    )


def verify_donors(rows: Sequence[tuple[Carrier, Carrier]]) -> bool:
    no_fixed_points = all(target.unit != donor.unit for target, donor in rows)
    same_cell_x_k = all(
        target.cell_name == donor.cell_name
        and target.x == donor.x
        and target.key == donor.key
        for target, donor in rows
    )
    whole_payload = all(donor.atom.payload == bytes((donor.target_bit,)) * 16 for _, donor in rows)
    table = {
        (target_bit, donor_bit): sum(
            target.target_bit == target_bit and donor.target_bit == donor_bit
            for target, donor in rows
        )
        for target_bit in (0, 1)
        for donor_bit in (0, 1)
    }
    return no_fixed_points and same_cell_x_k and whole_payload and set(table.values()) == {2}


def cluster_certificate(cells: Sequence[Cell]) -> ClusterCertificate:
    return ClusterCertificate(
        tuple(f"cluster-{cell.name}" for cell in cells),
        tuple(HORIZON for _ in cells),
        (),
        "actor-v1",
        "actor-v1",
    )


def validate_cluster(certificate: ClusterCertificate) -> bool:
    return (
        len(set(certificate.cluster_ids)) == len(certificate.cluster_ids)
        and all(horizon == HORIZON for horizon in certificate.horizons)
        and not certificate.cross_cluster_edges
        and certificate.source_actor_hash == certificate.evaluated_actor_hash
    )


def unit_bound_cell() -> BoundCell:
    cells = build_cells()
    current_best = max(score for _, score in enumerate_current_only_maps(cells))
    correct = F(60)
    rows = donor_rows(build_carriers(cells[0]))
    return BoundCell(
        "synthetic-unit-cell",
        True,
        False,
        2,
        True,
        total_variation(actor_kernel(Choice.Z0), actor_kernel(Choice.Z1)),
        (
            value(0, Choice.Z0) - value(0, Choice.Z1),
            value(1, Choice.Z1) - value(1, Choice.Z0),
        ),
        correct - current_best,
        verify_donors(rows),
        validate_cluster(cluster_certificate(cells)),
        True,
    )


def validate_bound_cell(cell: BoundCell) -> tuple[str, ...]:
    issues = []
    if not cell.x_closed or cell.prior_epoch_descendants_in_x:
        issues.append("incomplete_X")
    if cell.distinct_complete_atoms < 2:
        issues.append("insufficient_complete_atoms")
    if not cell.same_x_k_outcome_divergent:
        issues.append("missing_same_X_K_pair")
    if cell.tv < F(1, 4):
        issues.append("actor_TV_below_1/4")
    if any(gap < 8 for gap in cell.crossover_gaps):
        issues.append("crossover_gap_below_8")
    if cell.current_only_gap <= 4:
        issues.append("current_only_gap_not_above_4")
    if not cell.donor_valid:
        issues.append("invalid_donor")
    if not cell.h64_closed:
        issues.append("H64_interference_leak")
    if not cell.zero_policy_generation_distance:
        issues.append("nonzero_policy_generation_distance")
    return tuple(issues)


def bind_actual_instances(cells: Sequence[BoundCell]) -> tuple[str, tuple[str, ...]]:
    if not cells:
        return (
            "ABSENT_ACTIVE_Q16_OBJECTS",
            (
                "registered_complete_Q16_atom_schema_writer_reader_actor_binding",
                "supported_same_X_K_outcome_divergent_pair",
                "H64_cluster_and_zero_generation_distance_certificate",
            ),
        )
    issues = tuple(f"{cell.name}:{issue}" for cell in cells for issue in validate_bound_cell(cell))
    return ("BOUND_ACTUAL_INSTANCE_PASS" if not issues else "BOUND_ACTUAL_INSTANCE_INVALID", issues)


def run_instance_certificate(actual_cells: Sequence[BoundCell] = ()) -> CertificateResult:
    manifest = build_manifest()
    cells = build_cells()
    maps = enumerate_current_only_maps(cells)
    current_best = max(score for _, score in maps)
    correct, reset, deranged = F(60), F(32), F(28)
    z0, z1 = actor_kernel(Choice.Z0), actor_kernel(Choice.Z1)
    tv = total_variation(z0, z1)
    gaps = (
        value(0, Choice.Z0) - value(0, Choice.Z1),
        value(1, Choice.Z1) - value(1, Choice.Z0),
    )
    all_donor_rows = tuple(donor_rows(build_carriers(cell)) for cell in cells)
    donor_table = tuple(
        (f"{target_bit}{donor_bit}", count)
        for target_bit in (0, 1)
        for donor_bit in (0, 1)
        for count in (
            sum(
                target.target_bit == target_bit and donor.target_bit == donor_bit
                for target, donor in all_donor_rows[0]
            ),
        )
    )
    actual_status, missing = bind_actual_instances(actual_cells)
    unit = unit_bound_cell()
    negative_branch = replace(unit, current_only_gap=F(4))
    invariants = (
        (
            "complete_byte_level_X_ancestry",
            validate_manifest(manifest) and len(current_x(manifest)) == 10,
        ),
        ("two_exact_cells_and_complete_atoms", len(cells) == 2 and len(q16_atom(0).payload) == 16),
        ("actor_TV_and_crossover", tv >= F(1, 4) and all(gap >= 8 for gap in gaps)),
        ("nine_map_current_only_envelope", len(maps) == 9 and current_best == 32),
        (
            "value_witness",
            (correct - reset, correct - current_best, correct - deranged)
            == (28, 28, 32),
        ),
        ("whole_payload_deranged_balance", all(verify_donors(rows) for rows in all_donor_rows)),
        (
            "source_owner_epoch_excluded_from_K",
            all(len({row.key for row in build_carriers(cell)}) == 1 for cell in cells),
        ),
        ("H64_and_zero_generation_distance", validate_cluster(cluster_certificate(cells))),
        (
            "validator_positive_and_negative_branches",
            not validate_bound_cell(unit)
            and validate_bound_cell(negative_branch)
            == ("current_only_gap_not_above_4",),
        ),
    )
    passed = all(value for _, value in invariants)
    return CertificateResult(
        "PASS_SYNTHETIC_UNIT_CERTIFICATE" if passed else "INVALID_UNIT_CERTIFICATE",
        actual_status,
        missing,
        tv,
        gaps,
        correct,
        reset,
        current_best,
        deranged,
        len(maps),
        donor_table,
        invariants,
    )


def _jsonable(value: object) -> object:
    if isinstance(value, F):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
