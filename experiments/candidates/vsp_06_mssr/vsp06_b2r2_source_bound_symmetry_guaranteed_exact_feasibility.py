"""Stage-1 structural source for the VSP06-B2R2 exact-feasibility candidate.

This module deliberately has no canonical catalog or solver entry point.  It
contains only the frozen serializer, split, OA recipe, algebraic population
proof, and an explicitly synthetic fixed-block nonce exercise.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import unicodedata
from itertools import combinations, product
from typing import Any, Mapping, Sequence


DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v9"
TREATMENT_ID = (
    "VSP06-B2R2-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-SYMMETRY-GUARANTEED-EXACT-FEASIBILITY"
)
SELECTOR_ID = "VSP06-B2R2-SB-SG-EF-CP-SAT-V1"
VERIFIER_ID = "VSP06-B2R2-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
CATALOG_ID = "vsp06_b2r2_authenticated_partner_recall_catalog_v1"
LEDGER_ID = "vsp06_b2r2_constraint_target_ledger_v1"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
IMMEDIATE_PREDECESSOR_IMPLEMENTATION = "7d37be4ff33b2ba4984074383a719390e2cce6b0"

FORMAL = False
K_SEARCH = 0
HYPOTHETICAL_TRANSITIONS = 0
SYNTHETIC_STATUS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
PRECLAIM_FAILURE = "B2R2_SELECTOR_INVALID_NO_RUN"
SEALED_SELECTOR = "B2R2_SELECTOR_VERIFIED_MANIFEST_FIXED"

SPLIT_SALT = b"8100799/"
if len(SPLIT_SALT) != 8:  # defensive import-time literal assertion only
    raise AssertionError("split salt must be eight ASCII bytes")
DECISION_DOMAIN = b"VSP06-B2R2-SB-SG-EF-CP-SAT-V1/decision-order/v1"
DECISION_SEPARATOR = b"\x00"
DECISION_PREFIX = DECISION_DOMAIN + DECISION_SEPARATOR
CP_SAT_RANDOM_SEED = 8100699
NONCE_BLOCK_SIZE = 4096
OA_COLUMN_NAMES = ("identity", "version", "event", "decoy", "reset_y")
ENUMERATION_ORDER = ("pool", "seed", "panel", "branch", "Y", "replicate", "OA row")

TUPLE_FIELDS = (
    "consumer",
    "seed_row",
    "panel",
    "branch",
    "retention_length",
    "y",
    "reset_y",
    "target_identity",
    "target_version",
    "event_type",
    "decoy_sequence",
    "current_bytes",
    "roster",
    "legal_mask",
    "clock",
    "rng_binding",
    "quartet_base",
    "nonce",
)

PRIMARY_REPLICATES = {"KEEP": 72, "RESET": 48, "CURRENT": 12}
CALIBRATION_REPLICATES = {"fit": 32, "check": 8}
CHECKPOINT_REPLICATES = {"KEEP": 4, "RESET": 8, "CURRENT": 2}
PRIMARY_SEEDS = ("primary_1", "primary_2", "primary_3", "primary_4")
CHECKPOINTS = ("0", "512", "1024", "1536", "2048", "2560", "3072", "4096")
SELECTED_TARGET = 22_144
FINAL_KEEP_QUARTETS_PER_SEED = 64
FINAL_KEEP_REPLICATES_PER_OA_ROW = 4

EVENT_TYPES = (
    "target_absent_payload",
    "unauth_target_decoy",
    "renewal_marker",
    "dummy_roster",
)
DECOY_PATTERNS = tuple(
    tuple(tuple(item) for item in (
        [[0, 0, 1, False], [1, 1, 2, True], [2, 2, 3, False], [3, 3, 0, True]][offset:]
        + [[0, 0, 1, False], [1, 1, 2, True], [2, 2, 3, False], [3, 3, 0, True]][:offset]
    ))
    for offset in range(4)
)


class Stage1ContractError(RuntimeError):
    """A Stage-1 structural or provenance invariant failed closed."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _strict_nfc_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
        raise Stage1ContractError(f"{field} must be an NFC string")
    return value


def canonical_tuple_bytes(row: Mapping[str, Any]) -> bytes:
    """Serialize one tuple as the compact fixed-order UTF-8/NFC JSON array."""

    if not isinstance(row, Mapping) or tuple(row.keys()) != TUPLE_FIELDS:
        raise Stage1ContractError("tuple fields or declared key order changed")
    integer_fields = {
        "retention_length", "y", "reset_y", "target_identity", "target_version", "nonce"
    }
    string_fields = set(TUPLE_FIELDS) - integer_fields - {"decoy_sequence"}
    for field in integer_fields:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise Stage1ContractError(f"{field} must be a nonnegative integer")
    for field in string_fields:
        _strict_nfc_text(row[field], field)
    decoys = row["decoy_sequence"]
    if not isinstance(decoys, list) or not decoys:
        raise Stage1ContractError("decoy_sequence must be a nonempty list")
    normalized: list[list[Any]] = []
    for index, decoy in enumerate(decoys):
        if (
            not isinstance(decoy, list)
            or len(decoy) != 4
            or any(isinstance(decoy[i], bool) or not isinstance(decoy[i], int) for i in (0, 1, 2))
            or not isinstance(decoy[3], bool)
        ):
            raise Stage1ContractError(f"decoy_sequence[{index}] has invalid schema")
        normalized.append([decoy[0], decoy[1], decoy[2], decoy[3]])
    positional = [CATALOG_ID]
    positional.extend(normalized if field == "decoy_sequence" else row[field] for field in TUPLE_FIELDS)
    return _canonical_json_bytes(positional)


def bucket_for_tuple(payload: bytes) -> int:
    if not isinstance(payload, bytes):
        raise Stage1ContractError("serialized tuple must be bytes")
    return hashlib.sha256(SPLIT_SALT + payload).digest()[0] % 8


def split_for_bucket(bucket: int) -> str:
    if isinstance(bucket, bool) or not isinstance(bucket, int) or not 0 <= bucket <= 7:
        raise Stage1ContractError("bucket must be an integer in 0..7")
    return "train" if bucket <= 5 else "calibration" if bucket == 6 else "evaluation"


def decision_key(payload: bytes) -> bytes:
    return hashlib.sha256(DECISION_PREFIX + payload).digest()


def sort_digest_tuple_pairs(pairs: Sequence[tuple[bytes, bytes]]) -> tuple[tuple[bytes, bytes], ...]:
    """Order unsigned digest bytes first and tuple bytes as the collision tie-break."""

    seen: set[bytes] = set()
    normalized: list[tuple[bytes, bytes]] = []
    for digest, tuple_bytes in pairs:
        if not isinstance(digest, bytes) or len(digest) != 32 or not isinstance(tuple_bytes, bytes):
            raise Stage1ContractError("decision-order pair has invalid byte schema")
        if tuple_bytes in seen:
            raise Stage1ContractError("duplicate serialized tuple")
        seen.add(tuple_bytes)
        normalized.append((digest, tuple_bytes))
    return tuple(sorted(normalized, key=lambda item: (item[0], item[1])))


def decision_order(rows: Sequence[Mapping[str, Any]]) -> tuple[bytes, ...]:
    serialized = tuple(canonical_tuple_bytes(row) for row in rows)
    ordered = sort_digest_tuple_pairs(tuple((decision_key(item), item) for item in serialized))
    return tuple(item[1] for item in ordered)


def gf4_add(left: int, right: int) -> int:
    if left not in range(4) or right not in range(4):
        raise Stage1ContractError("GF(4) elements must use the two-bit encoding 0..3")
    return left ^ right


def gf4_alpha_multiply(value: int) -> int:
    table = (0, 2, 3, 1)
    if value not in range(4):
        raise Stage1ContractError("GF(4) elements must use the two-bit encoding 0..3")
    return table[value]


def oa_rows() -> tuple[tuple[int, int, int, int, int], ...]:
    """Return OA(16,5,4,2) in fixed ``a`` then ``b`` enumeration order."""

    rows = []
    for a, b in product(range(4), repeat=2):
        alpha_b = gf4_alpha_multiply(b)
        rows.append((a, b, a ^ b, a ^ alpha_b, a ^ alpha_b ^ b))
    return tuple(rows)


def oa_balance_proof(rows: Sequence[Sequence[int]] | None = None) -> dict[str, Any]:
    candidate = tuple(tuple(row) for row in (oa_rows() if rows is None else rows))
    if len(candidate) != 16 or any(len(row) != 5 for row in candidate):
        raise Stage1ContractError("OA shape must be exactly 16 by 5")
    single_counts = []
    for column in range(5):
        counts = tuple(sum(row[column] == value for row in candidate) for value in range(4))
        if counts != (4, 4, 4, 4):
            raise Stage1ContractError("OA column is not exactly balanced")
        single_counts.append(counts)
    pair_counts: dict[str, tuple[int, ...]] = {}
    for left, right in combinations(range(5), 2):
        counts = tuple(
            sum(row[left] == a and row[right] == b for row in candidate)
            for a, b in product(range(4), repeat=2)
        )
        if counts != (1,) * 16:
            raise Stage1ContractError("OA column pair is not exactly balanced")
        pair_counts[f"{OA_COLUMN_NAMES[left]}:{OA_COLUMN_NAMES[right]}"] = counts
    return {
        "row_count": 16,
        "column_counts": tuple(single_counts),
        "pair_counts": pair_counts,
        "column_binding": OA_COLUMN_NAMES,
    }


def catalog_count_proof() -> dict[str, Any]:
    """Prove the frozen catalog size from literals without enumerating its rows."""

    primary = 2 * 4 * 1 * sum(PRIMARY_REPLICATES.values()) * 4 * 16
    calibration = 1 * 1 * sum(CALIBRATION_REPLICATES.values()) * 4 * 16
    checkpoint = 1 * 4 * 8 * sum(CHECKPOINT_REPLICATES.values()) * 4 * 16
    if FINAL_KEEP_REPLICATES_PER_OA_ROW * len(oa_rows()) != FINAL_KEEP_QUARTETS_PER_SEED:
        raise Stage1ContractError("final-KEEP quartet construction changed")
    final_keep = 1 * 4 * 1 * 1 * 4 * FINAL_KEEP_REPLICATES_PER_OA_ROW * 16
    components = {
        "primary": primary,
        "calibration": calibration,
        "checkpoint": checkpoint,
        "final_keep": final_keep,
    }
    if components != {
        "primary": 67_584,
        "calibration": 2_560,
        "checkpoint": 28_672,
        "final_keep": 1_024,
    }:
        raise Stage1ContractError("frozen algebraic catalog components changed")
    total = sum(components.values())
    if total != 99_840:
        raise Stage1ContractError("frozen algebraic catalog cardinality changed")
    return {
        "components": components,
        "total": total,
        "selected_target": SELECTED_TARGET,
        "enumerated_canonical_rows": 0,
    }


def relabeling_multiplicity_proof(
    axes: Mapping[str, Sequence[str]], relabelings: Mapping[str, Mapping[str, str]]
) -> dict[str, int]:
    """Check bijective pool/seed/panel/branch/Y relabelings preserve products."""

    required = ("pool", "seed", "panel", "branch", "Y")
    if tuple(axes) != required or tuple(relabelings) != required:
        raise Stage1ContractError("relabeling axes or declared order changed")
    before_axes = []
    after_axes = []
    for axis in required:
        labels = tuple(axes[axis])
        mapping = relabelings[axis]
        if not labels or set(mapping) != set(labels) or len(set(mapping.values())) != len(labels):
            raise Stage1ContractError(f"{axis} relabeling is not a bijection")
        before_axes.append(labels)
        after_axes.append(tuple(mapping[label] for label in labels))
    before_cells = tuple(product(*before_axes))
    after_cells = tuple(product(*after_axes))
    before_histogram = Counter(Counter(before_cells).values())
    after_histogram = Counter(Counter(after_cells).values())
    if before_histogram != after_histogram or len(before_cells) != len(after_cells):
        raise Stage1ContractError("relabeling changed multiplicity")
    return {
        "before": len(before_cells),
        "after": len(after_cells),
        "multiplicity_histogram": dict(sorted(before_histogram.items())),
    }


def fixed_cell_index(
    coordinates: Mapping[str, int], axis_sizes: Mapping[str, int]
) -> int:
    """Map coordinates to a cell ordinal with ``OA row`` as the fastest axis."""

    if tuple(coordinates) != ENUMERATION_ORDER or tuple(axis_sizes) != ENUMERATION_ORDER:
        raise Stage1ContractError("cell coordinates must follow the fixed enumeration order")
    ordinal = 0
    for axis in ENUMERATION_ORDER:
        coordinate = coordinates[axis]
        size = axis_sizes[axis]
        if (
            isinstance(coordinate, bool)
            or not isinstance(coordinate, int)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
            or not 0 <= coordinate < size
        ):
            raise Stage1ContractError(f"invalid fixed enumeration coordinate: {axis}")
        ordinal = ordinal * size + coordinate
    return ordinal


def nonce_block(cell_index: int) -> range:
    if isinstance(cell_index, bool) or not isinstance(cell_index, int) or cell_index < 0:
        raise Stage1ContractError("cell index must be a nonnegative integer")
    start = cell_index * NONCE_BLOCK_SIZE
    return range(start, start + NONCE_BLOCK_SIZE)


def emission_request(cell_index: int, expected_split: str) -> dict[str, Any]:
    if expected_split not in {"train", "calibration", "evaluation"}:
        raise Stage1ContractError("expected split is invalid")
    return {
        "cell_index": cell_index,
        "nonce_block_size": NONCE_BLOCK_SIZE,
        "expected_split": expected_split,
        "split_salt": SPLIT_SALT.decode("ascii"),
        "bucket_override": None,
        "cell_conditional": False,
        "salt_resample": False,
        "domain_extension": 0,
    }


def _validate_emission_request(request: Mapping[str, Any]) -> tuple[int, str]:
    if not isinstance(request, Mapping) or set(request) != {
        "cell_index", "nonce_block_size", "expected_split", "split_salt",
        "bucket_override", "cell_conditional", "salt_resample", "domain_extension",
    }:
        raise Stage1ContractError("fixed-block emission request schema changed")
    cell_index = request["cell_index"]
    expected_split = request["expected_split"]
    nonce_block(cell_index)
    if expected_split not in {"train", "calibration", "evaluation"}:
        raise Stage1ContractError("expected split is invalid")
    if (
        request["nonce_block_size"] != NONCE_BLOCK_SIZE
        or request["split_salt"] != SPLIT_SALT.decode("ascii")
        or request["bucket_override"] is not None
        or request["cell_conditional"] is not False
        or request["salt_resample"] is not False
        or request["domain_extension"] != 0
    ):
        raise Stage1ContractError("override, resample, conditional repair, or domain extension is forbidden")
    return int(cell_index), str(expected_split)


def synthetic_tuple_template(tag: str = "proof") -> dict[str, Any]:
    _strict_nfc_text(tag, "tag")
    if not tag or "/" in tag:
        raise Stage1ContractError("synthetic tag must be one nonempty path atom")
    values: dict[str, Any] = {
        "consumer": f"synthetic_{tag}",
        "seed_row": f"synthetic_seed_{tag}",
        "panel": f"synthetic_panel_{tag}",
        "branch": "KEEP",
        "retention_length": 4,
        "y": 0,
        "reset_y": 0,
        "target_identity": 0,
        "target_version": 0,
        "event_type": EVENT_TYPES[0],
        "decoy_sequence": [list(item) for item in DECOY_PATTERNS[0]],
        "current_bytes": f"synthetic_current_{tag}",
        "roster": "P0,P1,P2,P3,focal",
        "legal_mask": "1111",
        "clock": "L=4",
        "rng_binding": f"synthetic_binding_{tag}",
        "quartet_base": f"synthetic/{tag}",
        "nonce": 0,
    }
    return {field: values[field] for field in TUPLE_FIELDS}


def _require_synthetic_template(template: Mapping[str, Any]) -> None:
    canonical_tuple_bytes(template)
    if (
        not template["consumer"].startswith("synthetic_")
        or not template["seed_row"].startswith("synthetic_seed_")
        or not template["panel"].startswith("synthetic_panel_")
        or not template["quartet_base"].startswith("synthetic/")
    ):
        raise Stage1ContractError("Stage-1 emitter accepts only explicit synthetic templates")


@dataclass(frozen=True)
class SyntheticEmission:
    tuple_value: Mapping[str, Any]
    tuple_sha256: str
    bucket: int
    split: str
    cell_index: int
    block_start: int
    block_stop: int


def emit_synthetic_cell(
    template: Mapping[str, Any], request: Mapping[str, Any]
) -> SyntheticEmission:
    """Emit the first matching nonce in exactly one fixed, disjoint block."""

    _require_synthetic_template(template)
    cell_index, expected_split = _validate_emission_request(request)
    block = nonce_block(cell_index)
    for nonce in block:
        row = dict(template)
        row["nonce"] = nonce
        ordered_row = {field: row[field] for field in TUPLE_FIELDS}
        payload = canonical_tuple_bytes(ordered_row)
        bucket = bucket_for_tuple(payload)
        split = split_for_bucket(bucket)
        if split == expected_split:
            return SyntheticEmission(
                tuple_value=ordered_row,
                tuple_sha256=sha256_bytes(payload),
                bucket=bucket,
                split=split,
                cell_index=cell_index,
                block_start=block.start,
                block_stop=block.stop,
            )
    raise Stage1ContractError("fixed nonce block has no split match; cell is terminal")


def verify_synthetic_emission(
    template: Mapping[str, Any], request: Mapping[str, Any], emission: SyntheticEmission | None
) -> None:
    if emission is None:
        raise Stage1ContractError("missing fixed-block emission is terminal")
    expected = emit_synthetic_cell(template, request)
    if emission != expected:
        raise Stage1ContractError("emitted row, split, bucket, digest, or first nonce mismatched")


def stage1_structural_proof() -> dict[str, Any]:
    axes = {
        "pool": ("p0", "p1"),
        "seed": ("s0", "s1", "s2", "s3"),
        "panel": ("n0", "n1"),
        "branch": ("KEEP", "RESET", "CURRENT"),
        "Y": ("0", "1", "2", "3"),
    }
    relabelings = {
        axis: {label: labels[(index + 1) % len(labels)] for index, label in enumerate(labels)}
        for axis, labels in axes.items()
    }
    return {
        "status": SYNTHETIC_STATUS,
        "immediate_predecessor_implementation": IMMEDIATE_PREDECESSOR_IMPLEMENTATION,
        "formal": FORMAL,
        "K_search": K_SEARCH,
        "hypothetical_transitions": HYPOTHETICAL_TRANSITIONS,
        "oa": oa_balance_proof(),
        "counts": catalog_count_proof(),
        "relabeling": relabeling_multiplicity_proof(axes, relabelings),
        "canonical_rows_enumerated": 0,
        "cp_sat_models_constructed": 0,
        "manifests_created": 0,
    }


__all__ = [
    "Stage1ContractError", "SyntheticEmission", "canonical_tuple_bytes", "bucket_for_tuple",
    "split_for_bucket", "decision_key", "sort_digest_tuple_pairs", "decision_order", "gf4_add",
    "gf4_alpha_multiply", "oa_rows", "oa_balance_proof", "catalog_count_proof",
    "relabeling_multiplicity_proof", "fixed_cell_index", "nonce_block", "emission_request", "synthetic_tuple_template",
    "emit_synthetic_cell", "verify_synthetic_emission", "stage1_structural_proof",
]
