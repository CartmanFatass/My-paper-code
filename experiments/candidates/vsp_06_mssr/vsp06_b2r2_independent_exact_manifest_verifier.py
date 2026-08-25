"""Independent Stage-1 verifier for the VSP06-B2R2 structural recipe.

The verifier intentionally imports no candidate generator, solver, Torch, or
runtime module.  It re-derives the OA, serializer, split, fixed-block nonce,
and algebraic population facts.  It cannot verify or create a manifest.
"""

from __future__ import annotations

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
IMMEDIATE_PREDECESSOR_IMPLEMENTATION = "7d37be4ff33b2ba4984074383a719390e2cce6b0"
SYNTHETIC_STATUS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
SPLIT_SALT = b"8100799/"
DECISION_DOMAIN = b"VSP06-B2R2-SB-SG-EF-CP-SAT-V1/decision-order/v1"
DECISION_SEPARATOR = b"\x00"
NONCE_BLOCK_SIZE = 4096
OA_COLUMN_NAMES = ("identity", "version", "event", "decoy", "reset_y")

TUPLE_FIELDS = (
    "consumer", "seed_row", "panel", "branch", "retention_length", "y", "reset_y",
    "target_identity", "target_version", "event_type", "decoy_sequence", "current_bytes",
    "roster", "legal_mask", "clock", "rng_binding", "quartet_base", "nonce",
)


class IndependentVerificationError(RuntimeError):
    """The independent reconstruction or supplied synthetic proof failed."""


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
        raise IndependentVerificationError(f"{field} must be an NFC string")
    return value


def canonical_tuple_bytes(row: Mapping[str, Any]) -> bytes:
    if not isinstance(row, Mapping) or tuple(row.keys()) != TUPLE_FIELDS:
        raise IndependentVerificationError("tuple fields or declared key order changed")
    integer_fields = {
        "retention_length", "y", "reset_y", "target_identity", "target_version", "nonce"
    }
    for field in integer_fields:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise IndependentVerificationError(f"{field} must be a nonnegative integer")
    for field in set(TUPLE_FIELDS) - integer_fields - {"decoy_sequence"}:
        _text(row[field], field)
    decoys = row["decoy_sequence"]
    if not isinstance(decoys, list) or not decoys:
        raise IndependentVerificationError("decoy_sequence must be a nonempty list")
    normalized = []
    for decoy in decoys:
        if (
            not isinstance(decoy, list)
            or len(decoy) != 4
            or any(isinstance(decoy[i], bool) or not isinstance(decoy[i], int) for i in (0, 1, 2))
            or not isinstance(decoy[3], bool)
        ):
            raise IndependentVerificationError("decoy_sequence item has invalid schema")
        normalized.append([decoy[0], decoy[1], decoy[2], decoy[3]])
    positional = [CATALOG_ID]
    positional.extend(normalized if field == "decoy_sequence" else row[field] for field in TUPLE_FIELDS)
    return _json_bytes(positional)


def _bucket(payload: bytes) -> int:
    return hashlib.sha256(SPLIT_SALT + payload).digest()[0] % 8


def _split(bucket: int) -> str:
    if bucket not in range(8):
        raise IndependentVerificationError("bucket is outside 0..7")
    return "train" if bucket <= 5 else "calibration" if bucket == 6 else "evaluation"


def _decision_key(payload: bytes) -> bytes:
    return hashlib.sha256(DECISION_DOMAIN + DECISION_SEPARATOR + payload).digest()


def reconstruct_oa_rows() -> tuple[tuple[int, int, int, int, int], ...]:
    alpha = (0, 2, 3, 1)
    return tuple(
        (a, b, a ^ b, a ^ alpha[b], a ^ alpha[b] ^ b)
        for a, b in product(range(4), repeat=2)
    )


def verify_oa() -> dict[str, Any]:
    rows = reconstruct_oa_rows()
    for column in range(5):
        if tuple(sum(row[column] == value for row in rows) for value in range(4)) != (4,) * 4:
            raise IndependentVerificationError("independent OA column balance failed")
    pair_names = []
    for left, right in combinations(range(5), 2):
        counts = tuple(
            sum(row[left] == a and row[right] == b for row in rows)
            for a, b in product(range(4), repeat=2)
        )
        if counts != (1,) * 16:
            raise IndependentVerificationError("independent OA pair balance failed")
        pair_names.append(f"{OA_COLUMN_NAMES[left]}:{OA_COLUMN_NAMES[right]}")
    return {"rows": rows, "balanced_columns": 5, "balanced_pairs": tuple(pair_names)}


def independent_count_proof() -> dict[str, Any]:
    components = {
        "primary": 2 * 4 * 1 * (72 + 48 + 12) * 4 * 16,
        "calibration": 1 * 1 * (32 + 8) * 4 * 16,
        "checkpoint": 1 * 4 * 8 * (4 + 8 + 2) * 4 * 16,
        "final_keep": 1 * 4 * 1 * 1 * 4 * 4 * 16,
    }
    expected = {
        "primary": 67_584, "calibration": 2_560,
        "checkpoint": 28_672, "final_keep": 1_024,
    }
    if components != expected or sum(components.values()) != 99_840:
        raise IndependentVerificationError("independent algebraic population proof failed")
    return {"components": components, "total": 99_840, "selected_target": 22_144}


def verify_generator_proof(proof: Mapping[str, Any]) -> None:
    if not isinstance(proof, Mapping):
        raise IndependentVerificationError("generator proof is not an object")
    if (
        proof.get("status") != SYNTHETIC_STATUS
        or proof.get("immediate_predecessor_implementation") != IMMEDIATE_PREDECESSOR_IMPLEMENTATION
        or proof.get("formal") is not False
        or proof.get("K_search") != 0
        or proof.get("hypothetical_transitions") != 0
        or proof.get("canonical_rows_enumerated") != 0
        or proof.get("cp_sat_models_constructed") != 0
        or proof.get("manifests_created") != 0
    ):
        raise IndependentVerificationError("generator proof crosses the Stage-1 boundary")
    independent_oa = verify_oa()
    supplied_oa = proof.get("oa")
    if (
        not isinstance(supplied_oa, Mapping)
        or tuple(supplied_oa.get("column_binding", ())) != OA_COLUMN_NAMES
        or supplied_oa.get("row_count") != len(independent_oa["rows"])
        or len(supplied_oa.get("pair_counts", {})) != 10
    ):
        raise IndependentVerificationError("generator OA proof disagrees with independent recipe")
    counts = proof.get("counts")
    independent_counts = independent_count_proof()
    if (
        not isinstance(counts, Mapping)
        or counts.get("components") != independent_counts["components"]
        or counts.get("total") != independent_counts["total"]
        or counts.get("selected_target") != independent_counts["selected_target"]
        or counts.get("enumerated_canonical_rows") != 0
    ):
        raise IndependentVerificationError("generator count proof mismatch")
    relabeling = proof.get("relabeling")
    if not isinstance(relabeling, Mapping) or relabeling.get("before") != relabeling.get("after"):
        raise IndependentVerificationError("generator relabeling proof mismatch")


def verify_synthetic_envelopes(envelopes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not envelopes:
        raise IndependentVerificationError("synthetic envelope set is empty")
    seen: set[bytes] = set()
    decision_pairs: list[tuple[bytes, bytes]] = []
    splits = []
    for envelope in envelopes:
        if not isinstance(envelope, Mapping) or set(envelope) != {
            "tuple", "tuple_sha256", "bucket", "split", "cell_index",
            "block_start", "block_stop",
        }:
            raise IndependentVerificationError("synthetic envelope schema mismatch")
        row = envelope["tuple"]
        if (
            not isinstance(row, Mapping)
            or not str(row.get("consumer", "")).startswith("synthetic_")
            or not str(row.get("quartet_base", "")).startswith("synthetic/")
        ):
            raise IndependentVerificationError("canonical-looking row is forbidden in Stage 1")
        payload = canonical_tuple_bytes(row)
        if payload in seen:
            raise IndependentVerificationError("duplicate synthetic tuple")
        seen.add(payload)
        digest = hashlib.sha256(payload).hexdigest()
        bucket = _bucket(payload)
        split = _split(bucket)
        cell_index = envelope["cell_index"]
        if isinstance(cell_index, bool) or not isinstance(cell_index, int) or cell_index < 0:
            raise IndependentVerificationError("cell index is invalid")
        start = cell_index * NONCE_BLOCK_SIZE
        stop = start + NONCE_BLOCK_SIZE
        nonce = row["nonce"]
        if (
            envelope["tuple_sha256"] != digest
            or envelope["bucket"] != bucket
            or envelope["split"] != split
            or envelope["block_start"] != start
            or envelope["block_stop"] != stop
            or nonce not in range(start, stop)
        ):
            raise IndependentVerificationError("synthetic digest/split/block claim mismatch")
        template = dict(row)
        for earlier_nonce in range(start, nonce):
            template["nonce"] = earlier_nonce
            earlier_payload = canonical_tuple_bytes({field: template[field] for field in TUPLE_FIELDS})
            if _split(_bucket(earlier_payload)) == split:
                raise IndependentVerificationError("emitted nonce is not the first split match")
        decision_pairs.append((_decision_key(payload), payload))
        splits.append(split)
    ordered = tuple(sorted(decision_pairs, key=lambda item: (item[0], item[1])))
    return {
        "verified_rows": len(envelopes),
        "splits": tuple(splits),
        "decision_order_sha256": hashlib.sha256(b"".join(item[1] for item in ordered)).hexdigest(),
    }


def stage1_verification_report(
    generator_proof: Mapping[str, Any], envelopes: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    verify_generator_proof(generator_proof)
    synthetic = verify_synthetic_envelopes(envelopes)
    return {
        "verdict": SYNTHETIC_STATUS,
        "candidate": CANDIDATE_ID,
        "treatment": TREATMENT_ID,
        "selector": SELECTOR_ID,
        "verifier": VERIFIER_ID,
        "immediate_predecessor_implementation": IMMEDIATE_PREDECESSOR_IMPLEMENTATION,
        "oa": verify_oa(),
        "counts": independent_count_proof(),
        "synthetic": synthetic,
        "formal": False,
        "canonical_manifest_verified": False,
        "global_rank_claim": False,
    }


__all__ = [
    "IndependentVerificationError", "canonical_tuple_bytes", "reconstruct_oa_rows",
    "verify_oa", "independent_count_proof", "verify_generator_proof",
    "verify_synthetic_envelopes", "stage1_verification_report",
]
