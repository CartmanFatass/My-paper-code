
"""Independent stdlib-only exact verifier for VSP06-B2R1 manifests.

This source intentionally duplicates its parsing, tuple serialization,
constraint evaluation, and structural checks.  It must not import OR-Tools,
the selector, or a shared constraint helper.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import stat
import struct
import sys
import unicodedata
from itertools import product
from typing import Any, Mapping, Sequence


VERIFIER_ID = "VSP06-B2R1-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
SELECTOR_ID = "VSP06-B2R1-SB-EF-CP-SAT-V1"
TREATMENT_ID = (
    "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-EXACT-FEASIBILITY"
)
CATALOG_ID = "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CATALOG-V1"
LEDGER_ID = "VSP06-B2R1-CONSTRAINT-TARGET-LEDGER-V1"
SALT = "8100799/"
REQUIRED_ORTOOLS = "9.12.4544"
INVALID = "B2R1_SELECTOR_INVALID_NO_RUN"
SYNTHETIC_DOMAIN = "VSP06-B2R1-SYNTHETIC-NONCANONICAL-V1"
SYNTHETIC_SUCCESS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
UNIVERSE_SPEC_ID = "VSP06-B2R1-INDEPENDENT-CANONICAL-UNIVERSE-SPEC-V1"
SYNTHETIC_UNIVERSE_SPEC_ID = "VSP06-B2R1-INDEPENDENT-SYNTHETIC-UNIVERSE-SPEC-V1"
PARAMETER_ASSIGNMENTS = {
    "num_search_workers": 1,
    "search_branching": "FIXED_SEARCH",
    "randomize_search": False,
    "random_seed": 8100699,
    "stop_after_first_solution": True,
    "enumerate_all_solutions": False,
    "cp_model_presolve": True,
    "symmetry_level": 0,
    "use_lns": False,
    "log_search_progress": True,
    "max_time_in_seconds": 1800.0,
    "max_deterministic_time": 1000.0,
}

# Frozen v9.12 SatParameters wire schema for the only fields assigned by the
# selector.  Keeping this table in the independent verifier ties the claimed
# semantic assignments to the actual serialized protobuf bytes without
# importing OR-Tools or protobuf generated code.
_SAT_PARAMETER_WIRE = {
    "random_seed": (31, "varint", 8100699),
    "max_time_in_seconds": (36, "double", 1800.0),
    "log_search_progress": (41, "varint", 1),
    "max_deterministic_time": (67, "double", 1000.0),
    "search_branching": (82, "varint", 1),  # FIXED_SEARCH
    "cp_model_presolve": (86, "varint", 1),
    "enumerate_all_solutions": (87, "varint", 0),
    "stop_after_first_solution": (98, "varint", 1),
    "num_search_workers": (100, "varint", 1),
    "randomize_search": (103, "varint", 0),
    "symmetry_level": (183, "varint", 0),
    "use_lns": (283, "varint", 0),
}
CANONICAL_FAMILY_COUNTS = {
    "split_bucket_disjointness": 3,
    "primary_counts": 144,
    "calibration_counts": 10,
    "checkpoint_counts": 660,
    "y_conditional_marginals": 6048,
    "reset_fresh_y_independence": 3200,
    "keep_quartets": 16,
    "anti_lookup_coverage": 60,
    "structural_eligibility": 5,
}

TUPLE_FIELDS = (
    "consumer", "seed_row", "panel", "branch", "retention_length", "y", "reset_y",
    "target_identity", "target_version", "event_type", "decoy_sequence",
    "current_bytes", "roster", "legal_mask", "clock", "rng_binding",
    "quartet_base", "nonce",
)
DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v8"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
ACTIVITY_NAMES = (
    "canonical_generator_calls", "canonical_rows_observed", "canonical_ortools_processes", "replicas",
    "canonical_verifier_admissions", "witnesses", "manifests", "model_fits", "trainer_calls",
    "environment_episodes", "environment_transitions", "policy_forwards", "learner_updates",
    "optimizer_steps", "evaluator_calls", "evaluation_episodes", "environment_rng_calls", "action_rng_calls",
)
SOURCE_CONFIG_RELATIVE_PATHS = (
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_source_bound_exact_feasibility.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_independent_exact_manifest_verifier.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "scripts/run_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_CONSTRAINT_TARGET_LEDGER_V1.json",
    "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_CODE_SCIENCE_INDEX.md",
)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class VerificationError(RuntimeError):
    """Independent exact-verification failure."""


def _validate_stage2_authorization(value: Mapping[str, Any]) -> None:
    required = {"direction", "candidate", "treatment_id", "selector_id", "verifier_id", "scientific_parent", "final_commit", "source_build_read_allowlist", "source_config_digest_map", "source_config_digest_map_sha256", "formal", "synthetic_only", "zero_start_activity"}
    fixed = {"direction": DIRECTION_ID, "candidate": CANDIDATE_ID, "treatment_id": TREATMENT_ID, "selector_id": SELECTOR_ID, "verifier_id": VERIFIER_ID, "scientific_parent": SCIENTIFIC_PARENT, "formal": False, "synthetic_only": False}
    if not isinstance(value, Mapping) or set(value) != required or any(value.get(k) != v for k, v in fixed.items()):
        raise VerificationError("missing or invalid Stage-2 authorization binding")
    commit = value.get("final_commit")
    allowlist = value.get("source_build_read_allowlist")
    activity = value.get("zero_start_activity")
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise VerificationError("invalid Stage-2 final commit binding")
    if not isinstance(allowlist, list) or not allowlist or any(
        not isinstance(item, str) or not Path(item).is_absolute() or ".." in Path(item).parts
        or any(char in item for char in "*?[") for item in allowlist
    ) or len(set(allowlist)) != len(allowlist) or not isinstance(activity, Mapping) or set(activity) != set(ACTIVITY_NAMES) or any(v != 0 or isinstance(v, bool) for v in activity.values()):
        raise VerificationError("invalid Stage-2 allowlist or zero-start binding")
    digest_map = value.get("source_config_digest_map")
    digest_map_digest = value.get("source_config_digest_map_sha256")
    if (
        not isinstance(digest_map, Mapping)
        or set(digest_map) != set(SOURCE_CONFIG_RELATIVE_PATHS)
        or any(
            not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            for digest in digest_map.values()
        )
        or not isinstance(digest_map_digest, str) or len(digest_map_digest) != 64
        or any(char not in "0123456789abcdef" for char in digest_map_digest)
        or digest_map_digest != _digest(_json_bytes(dict(digest_map)))
    ):
        raise VerificationError("invalid Explorer-audited source/config digest map")


def _is_reparse(path: Path) -> bool:
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_existing_path(path: Path) -> Path:
    text = str(path)
    if not text or any(char in text for char in "*?[") or ".." in path.parts:
        raise VerificationError("glob, empty, and parent-traversal locators are forbidden")
    absolute = Path(os.path.abspath(path))
    component = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        component = component / part
        if component.exists() and (component.is_symlink() or _is_reparse(component)):
            raise VerificationError("link/junction/reparse read locator is forbidden")
    resolved = path.resolve(strict=True)
    if resolved != absolute or not resolved.is_file():
        raise VerificationError("read locator alias or non-regular file is forbidden")
    if ("vsp06_" + "b2_") in resolved.as_posix().casefold():
        raise VerificationError("predecessor read locator is forbidden")
    return resolved


def authorize_read_path(authorization: Mapping[str, Any], path: Path) -> Path:
    _validate_stage2_authorization(authorization)
    resolved = safe_existing_path(path)
    if str(path) != str(resolved) or str(resolved) not in authorization["source_build_read_allowlist"]:
        raise VerificationError("read locator is not the exact authorized canonical path")
    return resolved


def _authorized_bytes(authorization: Mapping[str, Any], path: Path) -> bytes:
    resolved = authorize_read_path(authorization, path)
    before = os.stat(resolved, follow_symlinks=False)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(resolved, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
        ) != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
            raise VerificationError("authorized file changed between validation and open")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.stat(authorize_read_path(authorization, path), follow_symlinks=False)
    identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    if identity != (
        after_open.st_dev, after_open.st_ino, after_open.st_size, after_open.st_mtime_ns
    ) or identity != (
        after_path.st_dev, after_path.st_ino, after_path.st_size, after_path.st_mtime_ns
    ):
        raise VerificationError("authorized file changed during or after read")
    return b"".join(chunks)


def _authorized_digest(authorization: Mapping[str, Any], path: Path) -> str:
    return _digest(_authorized_bytes(authorization, path))


def _authorized_load(
    authorization: Mapping[str, Any], path: Path,
) -> Mapping[str, Any]:
    try:
        value = json.loads(_authorized_bytes(authorization, path).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"authorized JSON is invalid: {path}") from exc
    if not isinstance(value, Mapping):
        raise VerificationError(f"JSON root must be an object: {path}")
    return value


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _encode_varint(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise VerificationError("invalid frozen protobuf varint")
    encoded = bytearray()
    while value > 0x7F:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def _expected_sat_parameter_bytes() -> bytes:
    """Reconstruct the exact deterministic v9.12 SatParameters wire bytes."""

    if set(_SAT_PARAMETER_WIRE) != set(PARAMETER_ASSIGNMENTS):
        raise VerificationError("frozen SatParameters wire schema is incomplete")
    encoded = bytearray()
    for name, (field_number, wire_type, wire_value) in sorted(
        _SAT_PARAMETER_WIRE.items(), key=lambda item: item[1][0]
    ):
        semantic_value = PARAMETER_ASSIGNMENTS[name]
        if name == "search_branching":
            if semantic_value != "FIXED_SEARCH" or wire_value != 1:
                raise VerificationError("FIXED_SEARCH wire semantic mismatch")
        elif isinstance(semantic_value, bool):
            if wire_value != int(semantic_value):
                raise VerificationError(f"boolean wire semantic mismatch: {name}")
        elif semantic_value != wire_value:
            raise VerificationError(f"wire semantic mismatch: {name}")
        if wire_type == "varint":
            encoded.extend(_encode_varint((field_number << 3) | 0))
            encoded.extend(_encode_varint(int(wire_value)))
        elif wire_type == "double":
            encoded.extend(_encode_varint((field_number << 3) | 1))
            encoded.extend(struct.pack("<d", float(wire_value)))
        else:
            raise VerificationError("unknown frozen protobuf wire type")
    return bytes(encoded)


def _load(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise VerificationError(f"JSON root must be an object: {path}")
    return value


def _tuple_bytes(row: Mapping[str, Any]) -> bytes:
    if not isinstance(row, Mapping) or tuple(row) != TUPLE_FIELDS:
        raise VerificationError("catalog tuple schema/order mismatch")
    integers = {"retention_length", "y", "reset_y", "target_identity", "target_version", "nonce"}
    strings = set(TUPLE_FIELDS) - integers - {"decoy_sequence"}
    for field in integers:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise VerificationError(f"invalid integer tuple field: {field}")
    for field in strings:
        value = row[field]
        if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
            raise VerificationError(f"invalid text tuple field: {field}")
    decoys = row["decoy_sequence"]
    if not isinstance(decoys, list) or not decoys:
        raise VerificationError("invalid decoy sequence")
    normalized = []
    for decoy in decoys:
        if (
            not isinstance(decoy, list) or len(decoy) != 4
            or any(isinstance(decoy[i], bool) or not isinstance(decoy[i], int) for i in (0, 1, 2))
            or not isinstance(decoy[3], bool)

        ):
            raise VerificationError("invalid ordered decoy tuple")
        normalized.append([int(decoy[0]), int(decoy[1]), int(decoy[2]), decoy[3]])
    positional = [normalized if field == "decoy_sequence" else row[field] for field in TUPLE_FIELDS]
    return _json_bytes(positional)


def _bucket(payload: bytes) -> int:
    return hashlib.sha256(SALT.encode("utf-8") + payload).digest()[0] % 8


def _split(bucket: int) -> str:
    return "train" if bucket <= 5 else "calibration" if bucket == 6 else "evaluation"


def _parse_catalog(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    if (
        set(raw) != {"catalog_id", "salt", "rows"}
        or raw.get("catalog_id") != CATALOG_ID or raw.get("salt") != SALT
        or not isinstance(raw.get("rows"), list) or not raw["rows"]
    ):
        raise VerificationError("raw catalog envelope mismatch")
    parsed = []
    seen: set[bytes] = set()
    for source_index, row in enumerate(raw["rows"]):
        payload = _tuple_bytes(row)
        if payload in seen:
            raise VerificationError("duplicate canonical catalog tuple")
        seen.add(payload)
        bucket = _bucket(payload)
        parsed.append({
            "source_index": source_index,
            "tuple": dict(row),
            "bytes": payload,
            "tuple_sha256": _digest(payload),
            "bucket": bucket,
            "split": _split(bucket),
        })
    return sorted(parsed, key=lambda item: item["bytes"])


def _universe_decoy_patterns() -> tuple[list[list[Any]], ...]:
    base = [[0, 0, 1, False], [1, 1, 2, True], [2, 2, 3, False], [3, 3, 0, True]]
    return tuple(base[index:] + base[:index] for index in range(4))


def _universe_raw_row(
    *, consumer: str, seed_row: str, panel: str, branch: str,
    retention_length: int, y: int, logical_index: int, nonce: int,
) -> dict[str, Any]:
    feature = logical_index % 4
    identity = feature
    version = (logical_index // 4) % 4
    event_index = (logical_index // 16) % 4
    decoy_index = (logical_index // 64) % 4
    event_types = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")
    quartet = (
        f"{seed_row}_q{logical_index // 4:04d}"
        if consumer == "final_keep"
        else f"{consumer}_{seed_row}_{panel}_{branch}_{retention_length}_{logical_index:06d}"
    )
    binding = _digest(_json_bytes([
        consumer, seed_row, panel, branch, retention_length, y, logical_index
    ]))
    return {
        "consumer": consumer, "seed_row": seed_row, "panel": panel,
        "branch": branch, "retention_length": retention_length, "y": y,
        "reset_y": (identity + version + event_index + decoy_index) % 4,
        "target_identity": identity, "target_version": version,
        "event_type": event_types[event_index],
        "decoy_sequence": _universe_decoy_patterns()[decoy_index],
        "current_bytes": _digest(_json_bytes(["current", quartet])),
        "roster": "P0,P1,P2,P3,focal", "legal_mask": "1111",
        "clock": f"L={retention_length}", "rng_binding": binding,
        "quartet_base": quartet, "nonce": nonce,
    }


def _expected_universe_spec() -> dict[str, Any]:
    primary = ["primary_1", "primary_2", "primary_3", "primary_4"]
    return {
        "universe_id": UNIVERSE_SPEC_ID,
        "schema_version": 1,
        "salt": SALT,
        "tuple_fields": list(TUPLE_FIELDS),
        "actions": [0, 1, 2, 3],
        "primary_seeds": primary,
        "checkpoints": [0, 512, 1024, 1536, 2048, 2560, 3072, 4096],
        "regular_pools": [
            {
                "consumer": "primary_fit", "seed_rows": primary, "panels": ["fit"],
                "branch_targets": {"KEEP": 384, "RESET": 64, "CURRENT": 64},
                "retention_lengths": [4, 8], "required_split": "train",
                "oversupply_multiplier": 4, "reset_multiplier": 4,
            },
            {
                "consumer": "calibration_fit", "seed_rows": ["calibration"],
                "panels": ["fit"], "branch_targets": {"CURRENT": 128},
                "retention_lengths": [4], "required_split": "calibration",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
            {
                "consumer": "calibration_check", "seed_rows": ["calibration"],
                "panels": ["check"], "branch_targets": {"CURRENT": 32},
                "retention_lengths": [4], "required_split": "calibration",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
            {
                "consumer": "checkpoint", "seed_rows": primary,
                "panels": ["0", "512", "1024", "1536", "2048", "2560", "3072", "4096"],
                "branch_targets": {"KEEP": 16, "RESET": 8, "CURRENT": 8},
                "retention_lengths": [6], "required_split": "evaluation",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
        ],
        "final_keep": {
            "consumer": "final_keep", "seed_rows": primary,
            "panel": "4096_keep_extra", "branch": "KEEP", "retention_length": 6,
            "quartets_per_seed": 64, "nonce_start": 0, "nonce_stop": 256,
            "required_split": "evaluation", "first_matching_nonce": True,
            "reset_y": 0,
        },
        "derivation": {
            "row_formula": "VSP06-B2R1-RAW-ROW-V1",
            "final_keep_formula": "VSP06-B2R1-FINAL-KEEP-FIRST-EVAL-V1",
            "bucket_formula": "sha256(utf8(salt)||canonical_tuple_bytes)[0]%8",
        },
    }


def validate_declarative_universe_spec(spec: Mapping[str, Any]) -> None:
    """Pure exact recipe validation; performs no canonical row reconstruction."""

    if not isinstance(spec, Mapping) or dict(spec) != _expected_universe_spec():
        raise VerificationError("declarative universe specification differs from frozen recipe")


def _reconstruct_universe(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Reconstruct the catalog from a recipe; no selector/generator is imported."""

    validate_declarative_universe_spec(spec)

    keys = {
        "universe_id", "schema_version", "salt", "tuple_fields", "actions",
        "primary_seeds", "checkpoints", "regular_pools", "final_keep", "derivation",
    }
    if (
        not isinstance(spec, Mapping) or set(spec) != keys
        or spec.get("universe_id") != UNIVERSE_SPEC_ID
        or spec.get("schema_version") != 1 or spec.get("salt") != SALT
        or spec.get("tuple_fields") != list(TUPLE_FIELDS)
        or spec.get("actions") != [0, 1, 2, 3]
        or spec.get("primary_seeds") != ["primary_1", "primary_2", "primary_3", "primary_4"]
        or spec.get("checkpoints") != [0, 512, 1024, 1536, 2048, 2560, 3072, 4096]
        or spec.get("derivation") != {
            "row_formula": "VSP06-B2R1-RAW-ROW-V1",
            "final_keep_formula": "VSP06-B2R1-FINAL-KEEP-FIRST-EVAL-V1",
            "bucket_formula": "sha256(utf8(salt)||canonical_tuple_bytes)[0]%8",
        }
    ):
        raise VerificationError("declarative universe specification envelope mismatch")
    pools = spec["regular_pools"]
    if not isinstance(pools, list) or len(pools) != 4:
        raise VerificationError("declarative universe pool set mismatch")
    pool_keys = {
        "consumer", "seed_rows", "panels", "branch_targets", "retention_lengths",
        "required_split", "oversupply_multiplier", "reset_multiplier",
    }
    rows: list[dict[str, Any]] = []
    for pool in pools:
        if not isinstance(pool, Mapping) or set(pool) != pool_keys:
            raise VerificationError("declarative universe pool schema mismatch")
        axes = (pool["seed_rows"], pool["panels"], pool["branch_targets"], pool["retention_lengths"])
        if any(not isinstance(axis, (list, Mapping)) or not axis for axis in axes):
            raise VerificationError("declarative universe pool axes are empty")
        if not isinstance(pool["oversupply_multiplier"], int) or not isinstance(pool["reset_multiplier"], int):
            raise VerificationError("declarative universe multiplier is invalid")
        for seed in pool["seed_rows"]:
            for panel in pool["panels"]:
                for branch, target in pool["branch_targets"].items():
                    for length in pool["retention_lengths"]:
                        for y in spec["actions"]:
                            multiplier = pool["oversupply_multiplier"]
                            if branch == "RESET":
                                multiplier *= pool["reset_multiplier"]
                            for logical in range(target * multiplier):
                                row = _universe_raw_row(
                                    consumer=pool["consumer"], seed_row=seed, panel=panel,
                                    branch=branch, retention_length=length, y=y,
                                    logical_index=logical, nonce=logical,
                                )
                                if _split(_bucket(_tuple_bytes(row))) == pool["required_split"]:
                                    rows.append(row)
    final = spec["final_keep"]
    final_keys = {
        "consumer", "seed_rows", "panel", "branch", "retention_length",
        "quartets_per_seed", "nonce_start", "nonce_stop", "required_split",
        "first_matching_nonce", "reset_y",
    }
    if (
        not isinstance(final, Mapping) or set(final) != final_keys
        or final["consumer"] != "final_keep" or final["seed_rows"] != spec["primary_seeds"]
        or final["panel"] != "4096_keep_extra" or final["branch"] != "KEEP"
        or final["retention_length"] != 6 or final["quartets_per_seed"] != 64
        or final["nonce_start"] != 0 or final["nonce_stop"] != 256
        or final["required_split"] != "evaluation" or final["first_matching_nonce"] is not True
        or final["reset_y"] != 0
    ):
        raise VerificationError("declarative final-KEEP universe specification mismatch")
    events = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")
    for seed in final["seed_rows"]:
        for quartet_index in range(final["quartets_per_seed"]):
            identity = quartet_index % 4
            version = (quartet_index // 4) % 4
            event_index = (quartet_index // 16) % 4
            decoy_index = (identity + version + event_index) % 4
            for y in spec["actions"]:
                for nonce in range(final["nonce_start"], final["nonce_stop"]):
                    row = _universe_raw_row(
                        consumer="final_keep", seed_row=seed, panel=final["panel"],
                        branch="KEEP", retention_length=6, y=y,
                        logical_index=quartet_index, nonce=nonce,
                    )
                    row["quartet_base"] = f"{seed}_q{quartet_index:04d}"
                    row["target_identity"] = identity
                    row["target_version"] = version
                    row["event_type"] = events[event_index]
                    row["decoy_sequence"] = _universe_decoy_patterns()[decoy_index]
                    row["current_bytes"] = _digest(_json_bytes(["current", row["quartet_base"]]))
                    row["rng_binding"] = _digest(_json_bytes(["quartet", row["quartet_base"]]))
                    row["reset_y"] = 0
                    if _split(_bucket(_tuple_bytes(row))) == "evaluation":
                        rows.append(row)
                        break
                else:
                    raise VerificationError("declarative final-KEEP nonce domain is incomplete")
    return rows


def _parse_ledger(raw: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    required = {"ledger_id", "equation_semantics", "equation_templates", "family_counts", "ledger_digest"}
    if set(raw) != required or raw.get("ledger_id") != LEDGER_ID:
        raise VerificationError("raw target ledger envelope mismatch")
    body = {key: value for key, value in raw.items() if key != "ledger_digest"}
    if raw["ledger_digest"] != _digest(_json_bytes(body)):
        raise VerificationError("raw target ledger digest mismatch")
    if raw.get("equation_semantics") != "sum(integer_coefficient * selected_row_indicator) == integer_rhs":
        raise VerificationError("ledger equation semantics mismatch")
    templates = raw.get("equation_templates")
    if not isinstance(templates, list) or not templates:
        raise VerificationError("ledger equation templates absent")
    equations: list[Mapping[str, Any]] = []
    def substitute(value: Any, bindings: Mapping[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            if value[1:] not in bindings:
                raise VerificationError("ledger template references unknown axis")
            return bindings[value[1:]]
        if isinstance(value, list):
            return [substitute(item, bindings) for item in value]
        if isinstance(value, Mapping):
            return {key: substitute(item, bindings) for key, item in value.items()}
        return value
    for template in templates:
        if not isinstance(template, Mapping) or set(template) != {"name_template", "family", "axes", "terms", "rhs"}:
            raise VerificationError("ledger equation-template schema mismatch")
        axes = template["axes"]
        if not isinstance(axes, Mapping) or any(not isinstance(values, list) or not values for values in axes.values()):
            raise VerificationError("ledger equation-template axes invalid")
        names = tuple(axes)
        for values in product(*(axes[name] for name in names)):
            bindings = dict(zip(names, values))
            equations.append({
                "name": str(template["name_template"]).format(**bindings),
                "family": template["family"],
                "terms": substitute(template["terms"], bindings),
                "rhs": substitute(template["rhs"], bindings),
            })
    names: set[str] = set()
    counts: dict[str, int] = {}
    for equation in equations:
        if not isinstance(equation, Mapping) or set(equation) != {"name", "family", "terms", "rhs"}:
            raise VerificationError("ledger equation schema mismatch")
        if not isinstance(equation["name"], str) or equation["name"] in names:
            raise VerificationError("ledger equation name invalid/duplicate")
        names.add(equation["name"])
        family = equation["family"]
        if not isinstance(family, str):
            raise VerificationError("ledger equation family invalid")
        if isinstance(equation["rhs"], bool) or not isinstance(equation["rhs"], int):
            raise VerificationError("ledger RHS is not integer")
        if not isinstance(equation["terms"], list) or not equation["terms"]:
            raise VerificationError("ledger equation terms absent")
        for term in equation["terms"]:
            if not isinstance(term, Mapping) or set(term) != {"coefficient", "predicate"}:
                raise VerificationError("ledger term schema mismatch")
            coefficient = term["coefficient"]
            if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient == 0:
                raise VerificationError("ledger coefficient is not a nonzero integer")
            predicate = term["predicate"]
            if not isinstance(predicate, Mapping) or not predicate or set(predicate) - {"eq", "in"}:
                raise VerificationError("ledger predicate invalid")
            for operator, clauses in predicate.items():
                if not isinstance(clauses, Mapping) or not clauses:
                    raise VerificationError("ledger predicate clauses invalid")
                for field, value in clauses.items():
                    if field not in TUPLE_FIELDS and field not in {"split", "bucket"}:
                        raise VerificationError("ledger predicate field unknown")
                    if operator == "in" and (not isinstance(value, list) or not value):
                        raise VerificationError("ledger in-predicate invalid")
        counts[family] = counts.get(family, 0) + 1
    if raw["family_counts"] != counts:
        raise VerificationError("ledger family-count report mismatch")
    return list(equations)


def _value(row: Mapping[str, Any], field: str) -> Any:
    return row[field] if field in {"split", "bucket"} else row["tuple"][field]


def _matches(row: Mapping[str, Any], predicate: Mapping[str, Any]) -> bool:
    for field, expected in predicate.get("eq", {}).items():
        if _value(row, field) != expected:
            return False
    for field, allowed in predicate.get("in", {}).items():
        if _value(row, field) not in allowed:
            return False
    return True


def _evaluate_equations(
    rows: Sequence[Mapping[str, Any]], vector: Sequence[int],
    equations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    referenced = {
        field
        for equation in equations
        for term in equation["terms"]
        for clauses in term["predicate"].values()
        for field in clauses
    }
    inverted: dict[str, dict[bytes, set[int]]] = {field: {} for field in referenced}
    for index, row in enumerate(rows):
        for field in referenced:
            key = _json_bytes(_value(row, field))
            inverted[field].setdefault(key, set()).add(index)

    def matching(predicate: Mapping[str, Any]) -> set[int]:
        candidates: list[set[int]] = []
        for field, expected in predicate.get("eq", {}).items():
            candidates.append(inverted[field].get(_json_bytes(expected), set()))
        for field, allowed in predicate.get("in", {}).items():
            union: set[int] = set()
            for value in allowed:
                union.update(inverted[field].get(_json_bytes(value), set()))
            candidates.append(union)
        if not candidates:
            raise VerificationError("ledger predicate has no indexed clauses")
        result = set(candidates[0])
        for candidate in candidates[1:]:
            result.intersection_update(candidate)
        return result

    reports: dict[str, list[dict[str, Any]]] = {}
    for equation in equations:
        lhs = 0
        support = 0
        coefficients: dict[int, int] = {}
        for term in equation["terms"]:
            for index in matching(term["predicate"]):
                coefficients[index] = coefficients.get(index, 0) + int(term["coefficient"])
        for index, coefficient in coefficients.items():
            if coefficient:
                support += 1
                lhs += coefficient * vector[index]
        if support == 0 or lhs != equation["rhs"]:
            raise VerificationError(

                f"integer equation mismatch: {equation['name']} lhs={lhs} rhs={equation['rhs']}"
            )
        reports.setdefault(equation["family"], []).append({
            "name": equation["name"], "lhs": lhs, "rhs": equation["rhs"],
            "support_count": support,
        })
    selected_count = sum(vector)
    result: dict[str, Any] = {}
    for family, rows_report in sorted(reports.items()):
        result[family] = {
            "equation_count": len(rows_report),
            "selected_count": selected_count,
            "digest": _digest(_json_bytes(rows_report)),
        }
    return result


def _check_structural_eligibility(selected: Sequence[Mapping[str, Any]]) -> None:
    allowed_seed_rows = {"primary_1", "primary_2", "primary_3", "primary_4", "calibration"}
    expected_split = {
        "primary_fit": "train", "calibration_fit": "calibration",
        "calibration_check": "calibration", "checkpoint": "evaluation",
        "final_keep": "evaluation",
    }
    for row in selected:
        value = row["tuple"]
        consumer = value["consumer"]
        if consumer not in expected_split or row["split"] != expected_split[consumer]:
            raise VerificationError("consumer split/bucket structural eligibility failed")
        if value["seed_row"] not in allowed_seed_rows or value["y"] not in range(4) or value["reset_y"] not in range(4):
            raise VerificationError("seed/Y structural eligibility failed")
        if value["target_identity"] not in range(4) or value["target_version"] not in range(4):
            raise VerificationError("identity/version anti-lookup domain failed")
        if value["legal_mask"] != "1111" or value["roster"] != "P0,P1,P2,P3,focal":
            raise VerificationError("roster/legal-mask structural eligibility failed")
        if consumer == "primary_fit":
            if value["seed_row"] == "calibration" or value["panel"] != "fit" or value["branch"] not in {"KEEP", "RESET", "CURRENT"} or value["retention_length"] not in {4, 8}:
                raise VerificationError("primary-fit structural eligibility failed")
        elif consumer in {"calibration_fit", "calibration_check"}:
            expected_panel = "fit" if consumer == "calibration_fit" else "check"
            if value["seed_row"] != "calibration" or value["panel"] != expected_panel or value["branch"] != "CURRENT" or value["retention_length"] != 4:
                raise VerificationError("calibration structural eligibility failed")
        elif consumer == "checkpoint":
            if value["seed_row"] == "calibration" or value["panel"] not in {str(item) for item in (0, 512, 1024, 1536, 2048, 2560, 3072, 4096)} or value["retention_length"] != 6:
                raise VerificationError("checkpoint structural eligibility failed")
        elif consumer == "final_keep":
            if value["seed_row"] == "calibration" or value["panel"] != "4096_keep_extra" or value["branch"] != "KEEP" or value["retention_length"] != 6:
                raise VerificationError("final-KEEP structural eligibility failed")


def _check_quartets(selected: Sequence[Mapping[str, Any]]) -> None:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in selected:
        if row["tuple"]["consumer"] == "final_keep":
            value = row["tuple"]
            groups.setdefault((value["seed_row"], value["quartet_base"]), []).append(value)
    if not groups:
        raise VerificationError("held-out KEEP quartets are absent")
    structural = (
        "consumer", "seed_row", "panel", "branch", "retention_length", "reset_y",
        "target_identity", "target_version", "event_type", "decoy_sequence",
        "current_bytes", "roster", "legal_mask", "clock", "rng_binding",
        "quartet_base",
    )
    for base, group in groups.items():
        if len(group) != 4 or {row["y"] for row in group} != {0, 1, 2, 3}:
            raise VerificationError(f"incomplete/duplicate KEEP quartet: {base}")
        reference = tuple(group[0][field] for field in structural)
        if any(tuple(row[field] for field in structural) != reference for row in group[1:]):
            raise VerificationError(f"KEEP quartet structural mismatch: {base}")


def _check_canonical_catalog_support(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Independent necessary support audit before any canonical admission."""

    final_rows = [row for row in rows if row["tuple"]["consumer"] == "final_keep"]
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in final_rows:
        value = row["tuple"]
        groups.setdefault((value["seed_row"], value["quartet_base"]), []).append(row)
    expected_seeds = {"primary_1", "primary_2", "primary_3", "primary_4"}
    if {seed for seed, _base in groups} != expected_seeds:
        raise VerificationError("canonical final-KEEP seed support incomplete")
    structural = tuple(field for field in TUPLE_FIELDS if field not in {"y", "nonce"})
    for key, group in groups.items():
        if len(group) != 4 or {row["tuple"]["y"] for row in group} != {0, 1, 2, 3}:
            raise VerificationError(f"canonical final-KEEP quartet incomplete: {key}")
        reference = tuple(group[0]["tuple"][field] for field in structural)
        if any(tuple(row["tuple"][field] for field in structural) != reference for row in group[1:]):
            raise VerificationError(f"canonical final-KEEP quartet mismatch: {key}")
    event_domain = {"target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster"}
    for seed in sorted(expected_seeds):
        seed_rows = [row for row in final_rows if row["tuple"]["seed_row"] == seed]
        if len(seed_rows) != 256 or len({row["tuple"]["quartet_base"] for row in seed_rows}) != 64:
            raise VerificationError("canonical final-KEEP quartet cardinality mismatch")
        for field, domain in (("target_identity", set(range(4))), ("target_version", set(range(4))), ("event_type", event_domain)):
            counts = {value: sum(row["tuple"][field] == value for row in seed_rows) for value in domain}
            if set(counts.values()) != {64}:
                raise VerificationError(f"canonical final-KEEP {field} balance mismatch")
        decoys: dict[bytes, int] = {}
        for row in seed_rows:
            key = _json_bytes(row["tuple"]["decoy_sequence"])
            decoys[key] = decoys.get(key, 0) + 1
        if len(decoys) != 4 or set(decoys.values()) != {64}:
            raise VerificationError("canonical final-KEEP ordered-decoy balance mismatch")
    return {"final_keep_rows": len(final_rows), "quartet_count": len(groups)}


def _check_live_binding(
    expected: Mapping[str, Any], authorization: Mapping[str, Any]
) -> None:
    if platform.python_implementation() != "CPython" or sys.version_info[:2] != (3, 11):
        raise VerificationError("canonical verifier requires live CPython 3.11")
    if (
        expected["python_implementation"] != platform.python_implementation()
        or expected["python_version"] != platform.python_version()
        or authorize_read_path(
            authorization, Path(str(expected["python_executable"]))
        ) != authorize_read_path(authorization, Path(sys.executable).resolve())
        or expected["python_executable_sha256"] != _authorized_digest(
            authorization, Path(sys.executable).resolve()
        )
        or expected["os"] != platform.system()
        or expected["os_release"] != platform.release()
        or expected["architecture"] != platform.machine()
    ):
        raise VerificationError("live Python/OS/architecture binding mismatch")
    try:
        distribution = importlib.metadata.distribution("ortools")
    except importlib.metadata.PackageNotFoundError as exc:
        raise VerificationError(f"live ortools=={REQUIRED_ORTOOLS} is absent") from exc
    if distribution.version != REQUIRED_ORTOOLS or expected["ortools_version"] != REQUIRED_ORTOOLS or expected["ortools_source_tag"] != "v9.12":
        raise VerificationError("live OR-Tools version/source binding mismatch")
    actual_artifacts = []
    for item in distribution.files or ():
        if Path(str(item)).suffix.lower() not in {".pyd", ".so", ".dll"}:
            continue
        artifact = authorize_read_path(
            authorization, Path(distribution.locate_file(item)).resolve()
        )
        actual_artifacts.append([
            str(artifact), _authorized_digest(authorization, artifact)
        ])
    actual_artifacts.sort()
    if not actual_artifacts or expected["solver_artifacts"] != actual_artifacts:
        raise VerificationError("live solver artifact set mismatch")
    if expected["solver_artifact_set_sha256"] != _digest(_json_bytes(actual_artifacts)):
        raise VerificationError("live solver artifact-set digest mismatch")
    if expected["sat_parameter_assignments"] != PARAMETER_ASSIGNMENTS:
        raise VerificationError("frozen SatParameters semantics mismatch")
    if expected["sat_parameter_assignments_sha256"] != _digest(_json_bytes(PARAMETER_ASSIGNMENTS)):
        raise VerificationError("frozen SatParameters semantic digest mismatch")
    try:
        parameter_bytes = bytes.fromhex(str(expected["sat_parameters_hex"]))
    except ValueError as exc:
        raise VerificationError("serialized SatParameters bytes are invalid") from exc
    if parameter_bytes != _expected_sat_parameter_bytes():
        raise VerificationError("serialized SatParameters wire semantics mismatch")
    if expected["sat_parameters_sha256"] != _digest(parameter_bytes):
        raise VerificationError("serialized SatParameters digest mismatch")


def _expected_sealed_path_schema() -> dict[str, str]:
    root = PROJECT_ROOT / "temp/sessions/code_project_manager/vsp06_b2r1_source_bound_exact_feasibility_credit_efficiency"
    selector_root = root / "selector"
    result = {
        "claim": str((root / "stage2_namespace_claim.json").resolve()),
        "catalog": str((root / "canonical_catalog.json").resolve()),
        "universe_spec": str((root / "declarative_universe_spec.json").resolve()),
        "ledger": str((PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[5]).resolve()),
        "bindings": str((selector_root / "frozen_bindings.json").resolve()),
        "replica_1": str((selector_root / "cold_replica_1.json").resolve()),
        "replica_2": str((selector_root / "cold_replica_2.json").resolve()),
        "witness": str((selector_root / "membership_witness.json").resolve()),
        "proposed_manifest": str((selector_root / "proposed_manifest.json").resolve()),
        "verifier_report": str((selector_root / "independent_verifier_report.json").resolve()),
        "receipt": str((selector_root / "selector_success_receipt.json").resolve()),
        "manifest": str((root / "frozen_manifest.json").resolve()),
    }
    for replica in (1, 2):
        base = selector_root / f"cold_replica_{replica}.json"
        result[f"replica_{replica}_stdout"] = str(base.with_name(base.stem + ".stdout.log").resolve())
        result[f"replica_{replica}_stderr"] = str(base.with_name(base.stem + ".stderr.log").resolve())
        result[f"replica_{replica}_resource"] = str(base.with_name(base.stem + ".resource.json").resolve())
    return result


def verify(
    *, catalog_path: Path, ledger_path: Path, witness_path: Path,
    manifest_path: Path, bindings_path: Path, replica_paths: Sequence[Path],
    stage2_authorization_path: Path, universe_path: Path,
) -> dict[str, Any]:
    stage2_authorization_path = safe_existing_path(stage2_authorization_path)
    bootstrap_authorization = _load(stage2_authorization_path)
    _validate_stage2_authorization(bootstrap_authorization)
    authorize_read_path(bootstrap_authorization, stage2_authorization_path)
    authorization = _authorized_load(bootstrap_authorization, stage2_authorization_path)
    _validate_stage2_authorization(authorization)
    if authorization != bootstrap_authorization:
        raise VerificationError("Stage-2 authorization changed during secure load")
    catalog_path = authorize_read_path(authorization, catalog_path)
    universe_path = authorize_read_path(authorization, universe_path)
    ledger_path = authorize_read_path(authorization, ledger_path)
    witness_path = authorize_read_path(authorization, witness_path)
    manifest_path = authorize_read_path(authorization, manifest_path)
    bindings_path = authorize_read_path(authorization, bindings_path)
    replica_paths = tuple(authorize_read_path(authorization, path) for path in replica_paths)
    if len(replica_paths) != 2:
        raise VerificationError("exactly two replica reports are required")
    sealed = _expected_sealed_path_schema()
    exact_inputs = {
        "catalog": catalog_path, "universe_spec": universe_path,
        "ledger": ledger_path, "witness": witness_path,
        "proposed_manifest": manifest_path, "bindings": bindings_path,
    }
    if any(str(path) != sealed[name] for name, path in exact_inputs.items()) or [
        str(path) for path in replica_paths
    ] != [sealed["replica_1"], sealed["replica_2"]]:
        raise VerificationError("verifier input used an alternate sealed locator")
    replicas = [_authorized_load(authorization, path) for path in replica_paths]
    replica_keys = ("selector_identity", "terminal_status", "membership_vector", "membership_vector_sha256", "selected_tuple_sha256", "manifest", "manifest_sha256")
    if replicas[0].get("terminal_status") not in {"FEASIBLE", "OPTIMAL"} or any(replicas[0].get(key) != replicas[1].get(key) for key in replica_keys):
        raise VerificationError("two complete replica reports disagree, including terminal status")
    raw_catalog = _authorized_load(authorization, catalog_path)
    raw_universe = _authorized_load(authorization, universe_path)
    raw_ledger = _authorized_load(authorization, ledger_path)
    witness = _authorized_load(authorization, witness_path)
    manifest = _authorized_load(authorization, manifest_path)
    bindings = _authorized_load(authorization, bindings_path)
    rows = _parse_catalog(raw_catalog)
    universe_rows = _parse_catalog({
        "catalog_id": CATALOG_ID, "salt": SALT,
        "rows": _reconstruct_universe(raw_universe),
    })
    if [row["bytes"] for row in universe_rows] != [row["bytes"] for row in rows]:
        raise VerificationError("catalog is partial, mutated, or out of independent universe")
    equations = _parse_ledger(raw_ledger)
    expected = bindings.get("expected")
    if not isinstance(expected, Mapping):
        raise VerificationError("frozen binding envelope is absent")
    required_binding_keys = {
        "selector_source_sha256", "verifier_source_sha256", "catalog_sha256",
        "source_config_digest_map", "source_config_digest_map_sha256",
        "ledger_sha256", "python_implementation", "python_version",
        "python_executable", "python_executable_sha256", "ortools_version",
        "ortools_source_tag", "solver_artifacts", "solver_artifact_set_sha256",
        "sat_parameters_sha256", "sat_parameters_hex", "sat_parameter_assignments",
        "sat_parameter_assignments_sha256", "os", "os_release",
        "architecture", "final_commit", "stage2_authorization_sha256",
        "universe_spec_sha256", "sealed_path_schema", "sealed_path_schema_sha256",
    }
    if set(expected) != required_binding_keys:
        raise VerificationError("source/build/parameter binding key set changed")
    if expected["final_commit"] != authorization["final_commit"] or expected["stage2_authorization_sha256"] != _digest(_json_bytes(authorization)):
        raise VerificationError("final-commit or Stage-2 authorization digest binding mismatch")
    synthetic_only = bindings.get("synthetic_only") is True
    if set(bindings) != {"selector_path", "verifier_path", "synthetic_only", "expected"}:
        raise VerificationError("binding envelope key set changed")
    selector_path = Path(str(bindings.get("selector_path", "")))
    verifier_path = Path(str(bindings.get("verifier_path", "")))
    selector_path = authorize_read_path(authorization, selector_path)
    verifier_path = authorize_read_path(authorization, verifier_path)

    source_map = expected["source_config_digest_map"]
    if not isinstance(source_map, Mapping) or set(source_map) != set(SOURCE_CONFIG_RELATIVE_PATHS):
        raise VerificationError("seven-path source/config digest map is incomplete")
    actual_source_map = {
        relative: _authorized_digest(authorization, PROJECT_ROOT / relative)
        for relative in SOURCE_CONFIG_RELATIVE_PATHS
    }
    if (
        dict(source_map) != dict(authorization["source_config_digest_map"])
        or actual_source_map != dict(authorization["source_config_digest_map"])
        or expected["source_config_digest_map_sha256"] != authorization["source_config_digest_map_sha256"]
        or authorization["source_config_digest_map_sha256"] != _digest(_json_bytes(actual_source_map))
    ):
        raise VerificationError("seven-path final-commit source/config binding mismatch")

    if (
        verifier_path != Path(__file__).resolve()
        or selector_path != (PROJECT_ROOT / SOURCE_CONFIG_RELATIVE_PATHS[0]).resolve()
        or expected["verifier_source_sha256"] != _authorized_digest(authorization, verifier_path)
        or expected["selector_source_sha256"] != _authorized_digest(authorization, selector_path)
        or expected["catalog_sha256"] != _authorized_digest(authorization, catalog_path)
        or expected["ledger_sha256"] != _authorized_digest(authorization, ledger_path)
        or expected["universe_spec_sha256"] != _authorized_digest(authorization, universe_path)
        or expected["sealed_path_schema_sha256"] != _digest(
            _json_bytes(expected["sealed_path_schema"])
        )
        or expected["sealed_path_schema"] != _expected_sealed_path_schema()
    ):
        raise VerificationError("source/input binding mismatch")
    if not synthetic_only:
        if raw_ledger.get("family_counts") != CANONICAL_FAMILY_COUNTS:
            raise VerificationError("canonical constraint-family counts mismatch")
        _check_live_binding(expected, authorization)
        _check_canonical_catalog_support(rows)
    if witness.get("selector_identity") != SELECTOR_ID:
        raise VerificationError("membership witness selector identity mismatch")
    vector = witness.get("membership_vector")
    if not isinstance(vector, list) or len(vector) != len(rows) or any(
        isinstance(value, bool) or value not in (0, 1) for value in vector
    ):
        raise VerificationError("membership witness is partial/nonbinary")
    if witness.get("membership_vector_sha256") != _digest(_json_bytes(vector)):
        raise VerificationError("membership witness digest mismatch")
    if (
        manifest.get("manifest_id") != "vsp06_b2r1_authenticated_partner_recall_manifest_v1"
        or manifest.get("treatment") != TREATMENT_ID
        or manifest.get("selector_identity") != SELECTOR_ID
        or manifest.get("bindings") != expected
        or manifest.get("rank_claim") is not False
    ):
        raise VerificationError("proposed manifest envelope/bindings mismatch")
    selected = [row for row, value in zip(rows, vector) if value]
    proposed = manifest.get("selected_rows")
    expected_rows = [
        {"tuple": row["tuple"], "tuple_sha256": row["tuple_sha256"],
         "bucket": row["bucket"], "split": row["split"]}
        for row in selected
    ]
    if proposed != expected_rows or manifest.get("selected_count") != len(selected):
        raise VerificationError("bidirectional witness-to-manifest mapping mismatch")
    if len({_json_bytes(row["tuple"]) for row in selected}) != len(selected):
        raise VerificationError("manifest has duplicate selected rows")
    order_digest = _digest(_json_bytes([row["tuple_sha256"] for row in selected]))
    if manifest.get("common_two_arm_order_digest") != order_digest:
        raise VerificationError("canonical/two-arm order digest mismatch")
    _check_structural_eligibility(selected)
    _check_quartets(selected)
    family_reports = _evaluate_equations(rows, vector, equations)
    required_families = {
        "split_bucket_disjointness", "primary_counts", "calibration_counts",
        "checkpoint_counts", "y_conditional_marginals", "keep_quartets",
        "anti_lookup_coverage", "structural_eligibility",
        "reset_fresh_y_independence",
    }
    if set(family_reports) != required_families:
        raise VerificationError("constraint-family coverage mismatch")
    manifest_digest = _digest(_json_bytes(manifest))
    return {
        "verifier_identity": VERIFIER_ID,
        "verdict": "SYNTHETIC_STRUCTURAL_VALID_ONLY" if synthetic_only else "VERIFIED",
        "synthetic_only": synthetic_only,
        "selected_count": len(selected),
        "constraint_families": family_reports,
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": _digest(_json_bytes(authorization)),
        "source_config_digest_map_sha256": expected["source_config_digest_map_sha256"],
        "catalog_sha256": _authorized_digest(authorization, catalog_path),
        "universe_spec_sha256": _authorized_digest(authorization, universe_path),
        "ledger_sha256": _authorized_digest(authorization, ledger_path),
        "selector_source_sha256": expected["selector_source_sha256"],
        "solver_artifact_set_sha256": expected["solver_artifact_set_sha256"],
        "sat_parameters_sha256": expected["sat_parameters_sha256"],
        "python_executable_sha256": expected["python_executable_sha256"],
        "membership_witness_sha256": _authorized_digest(authorization, witness_path),
        "replica_sha256": [
            _authorized_digest(authorization, path) for path in replica_paths
        ],
        "membership_vector_sha256": witness["membership_vector_sha256"],
        "manifest_sha256": manifest_digest,
        "verifier_source_sha256": expected["verifier_source_sha256"],
        "common_two_arm_order_digest": order_digest,
        "global_rank_claim": False,
    }


def _claimed_entries(entries: Any, label: str) -> list[tuple[str, bytes]]:
    if not isinstance(entries, list) or not entries:
        raise VerificationError(f"{label} entries are absent")
    claimed: dict[str, bytes] = {}
    payloads: set[bytes] = set()
    result = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"tuple_sha256", "tuple_bytes_hex"}:
            raise VerificationError(f"{label} entry schema mismatch")
        try:
            payload = bytes.fromhex(entry["tuple_bytes_hex"])
        except (TypeError, ValueError) as exc:
            raise VerificationError(f"{label} bytes are invalid") from exc
        digest = entry["tuple_sha256"]
        if digest in claimed and claimed[digest] != payload:
            raise VerificationError("same claimed digest maps to unequal tuple bytes")
        if payload in payloads:
            raise VerificationError(f"{label} duplicate tuple bytes")
        claimed[digest] = payload
        payloads.add(payload)
        if not isinstance(digest, str) or _digest(payload) != digest:
            raise VerificationError(f"{label} digest mismatch")
        result.append((digest, payload))
    return result


def _reconstruct_synthetic_universe(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    required = {
        "universe_id", "salt", "synthetic_only", "domain", "fixture_id", "parameters"
    }
    if (
        not isinstance(spec, Mapping) or set(spec) != required
        or spec.get("universe_id") != SYNTHETIC_UNIVERSE_SPEC_ID
        or spec.get("salt") != SALT or spec.get("synthetic_only") is not True
        or spec.get("domain") != SYNTHETIC_DOMAIN
        or spec.get("fixture_id") != "VSP06-B2R1-HAND-AUTHORED-20-ROW-PROOF-V1"
        or spec.get("parameters") != {
            "keep_y": [0, 1, 2, 3], "reset_cross_product": [0, 1, 2, 3]
        }
    ):
        raise VerificationError("independent universe specification synthetic mismatch")

    def base(y: int, nonce: int, quartet: str, branch: str) -> dict[str, Any]:
        return {
            "consumer": "synthetic", "seed_row": "s", "panel": "p",
            "branch": branch, "retention_length": 6, "y": y, "reset_y": 0,
            "target_identity": 0, "target_version": 0, "event_type": "e",
            "decoy_sequence": [[0, 1, 2, False]], "current_bytes": "c",
            "roster": "r", "legal_mask": "1111", "clock": "clock",
            "rng_binding": "none", "quartet_base": quartet, "nonce": nonce,
        }

    rows = []
    for y in range(4):
        value = base(y, y, "q", "KEEP")
        value["consumer"] = "final_keep"
        rows.append(value)
    events = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")
    for index, (y, fresh) in enumerate(product(range(4), repeat=2)):
        value = base(y, 4 + index, f"reset-{index}", "RESET")
        value["reset_y"] = fresh
        value["target_identity"] = (y + fresh) % 4
        value["target_version"] = (2 * y + fresh) % 4
        value["event_type"] = events[(y + fresh) % 4]
        value["decoy_sequence"] = [[
            (y + fresh) % 4, (y + fresh + 1) % 4,
            (y + fresh + 2) % 4, bool((y + fresh) % 2),
        ]]
        rows.append(value)
    return rows


def verify_synthetic(
    *, catalog: Mapping[str, Any], universe_spec: Mapping[str, Any], ledger: Mapping[str, Any],
    witness: Mapping[str, Any], replicas: Sequence[Mapping[str, Any]], proposed_manifest: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Independent in-memory noncanonical proof; never admits canonical state."""
    catalog_keys = {"catalog_id", "salt", "synthetic_only", "domain", "rows"}
    universe_keys = {"universe_id", "salt", "synthetic_only", "domain", "fixture_id", "parameters"}
    if not isinstance(catalog, Mapping) or set(catalog) != catalog_keys or catalog.get("synthetic_only") is not True or catalog.get("domain") != SYNTHETIC_DOMAIN:
        raise VerificationError("synthetic catalog envelope mismatch")
    if not isinstance(universe_spec, Mapping) or set(universe_spec) != universe_keys or universe_spec.get("universe_id") != SYNTHETIC_UNIVERSE_SPEC_ID or universe_spec.get("synthetic_only") is not True or universe_spec.get("domain") != SYNTHETIC_DOMAIN:
        raise VerificationError("synthetic universe envelope mismatch")
    rows = _parse_catalog({"catalog_id": catalog["catalog_id"], "salt": catalog["salt"], "rows": catalog["rows"]})
    universe = _parse_catalog({"catalog_id": CATALOG_ID, "salt": universe_spec["salt"], "rows": _reconstruct_synthetic_universe(universe_spec)})
    if [row["bytes"] for row in rows] != [row["bytes"] for row in universe]:
        raise VerificationError("catalog is missing, mutated, or out of independent universe")
    witness_keys = {"synthetic_only", "domain", "selected_count", "vector", "selected"}
    if not isinstance(witness, Mapping) or set(witness) != witness_keys or witness.get("synthetic_only") is not True or witness.get("domain") != SYNTHETIC_DOMAIN:
        raise VerificationError("synthetic witness envelope mismatch")
    vector = witness["vector"]
    if not isinstance(vector, list) or len(vector) != len(rows) or any(isinstance(v, bool) or v not in (0, 1) for v in vector):
        raise VerificationError("synthetic witness is partial/nonbinary")
    selected = [row for row, value in zip(rows, vector) if value]
    entries = _claimed_entries(witness["selected"], "witness")
    expected_pairs = [(row["tuple_sha256"], row["bytes"]) for row in selected]
    if witness["selected_count"] != len(selected) or entries != expected_pairs:
        raise VerificationError("witness is partial, mutated, or out of universe")
    equations = _parse_ledger(ledger)
    reports = _evaluate_equations(rows, vector, equations)
    if set(reports) != set(CANONICAL_FAMILY_COUNTS):
        raise VerificationError("synthetic proof does not cover all nine families")
    _check_quartets(selected)
    reset_pairs = {(row["tuple"]["y"], row["tuple"]["reset_y"]) for row in selected if row["tuple"]["branch"] == "RESET"}
    if reset_pairs and reset_pairs != {(y, fresh) for y in range(4) for fresh in range(4)}:
        raise VerificationError("synthetic RESET independence cross-product is incomplete")
    for field in ("target_identity", "target_version", "y", "event_type", "decoy_sequence"):
        if len({_json_bytes(row["tuple"][field]) for row in selected}) < 2:
            raise VerificationError("synthetic anti-lookup coverage is degenerate")
    if not isinstance(replicas, Sequence) or isinstance(replicas, (str, bytes)) or len(replicas) != 2:
        raise VerificationError("exactly two synthetic replicas are required")
    replica_keys = {"status", "complete", "synthetic_only", "domain", "vector", "selected", "manifest_digest"}
    for replica in replicas:
        if not isinstance(replica, Mapping) or set(replica) != replica_keys or replica.get("complete") is not True or replica.get("synthetic_only") is not True or replica.get("domain") != SYNTHETIC_DOMAIN:
            raise VerificationError("synthetic replica envelope mismatch")
        _claimed_entries(replica["selected"], "replica")
    compared = ("status", "vector", "selected", "manifest_digest")
    if replicas[0]["status"] not in {"FEASIBLE", "OPTIMAL"} or any(replicas[0][key] != replicas[1][key] for key in compared) or replicas[0]["vector"] != vector or replicas[0]["selected"] != witness["selected"]:
        raise VerificationError("synthetic replica status/vector/order/digest mismatch")
    manifest_keys = {"verifier_id", "selector_id", "synthetic_only", "domain", "catalog_digest", "universe_digest", "ledger_digest", "selected_count", "entries"}
    if not isinstance(proposed_manifest, Mapping) or set(proposed_manifest) != manifest_keys or proposed_manifest.get("verifier_id") != VERIFIER_ID or proposed_manifest.get("selector_id") != SELECTOR_ID or proposed_manifest.get("synthetic_only") is not True or proposed_manifest.get("domain") != SYNTHETIC_DOMAIN:
        raise VerificationError("synthetic proposed-manifest envelope mismatch")
    prefix = b"VSP06-B2R1-SB-EF-CP-SAT-V1/decision-order/v1" + bytes((0,))
    ordered = sorted(selected, key=lambda row: (hashlib.sha256(prefix + row["bytes"]).digest(), row["bytes"]))
    expected_manifest_entries = [{"tuple_sha256": row["tuple_sha256"], "tuple_bytes_hex": row["bytes"].hex(), "arm": arm} for row in ordered for arm in ("MSSR_P_FIXED_VALIDITY_CARRIER", "GENERIC_PROVENANCE_CONDITIONED_CARRIER")]
    bindings = {"catalog_digest": _digest(_json_bytes(catalog)), "universe_digest": _digest(_json_bytes(universe_spec)), "ledger_digest": ledger["ledger_digest"]}
    if any(proposed_manifest[key] != value for key, value in bindings.items()) or proposed_manifest["selected_count"] != len(selected) or proposed_manifest["entries"] != expected_manifest_entries:
        raise VerificationError("synthetic manifest order/source binding mismatch")
    manifest_digest = _digest(_json_bytes(proposed_manifest))
    if replicas[0]["manifest_digest"] != manifest_digest:
        raise VerificationError("synthetic replica manifest digest mismatch")
    return {"synthetic_only": True, "domain": SYNTHETIC_DOMAIN, "status": SYNTHETIC_SUCCESS,
            "selected_count": len(selected), "constraint_families": reports, "manifest_digest": manifest_digest,
            "canonical_rank_claim": False}


def reject_synthetic_for_canonical(envelope: Mapping[str, Any]) -> None:
    if isinstance(envelope, Mapping) and (envelope.get("synthetic_only") is True or envelope.get("domain") == SYNTHETIC_DOMAIN or envelope.get("status") == SYNTHETIC_SUCCESS):
        raise VerificationError("synthetic envelopes cannot enter canonical verification")
    raise VerificationError("canonical verification requires Stage-2 file bindings")


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as exc:
        raise VerificationError("verifier report destination already exists") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(_json_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--witness", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--bindings", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--replica", action="append", required=True)
    parser.add_argument("--stage2-authorization", required=True)
    args = parser.parse_args(argv)
    try:
        report = verify(
            catalog_path=Path(args.catalog), ledger_path=Path(args.ledger),
            witness_path=Path(args.witness), manifest_path=Path(args.manifest),
            bindings_path=Path(args.bindings), replica_paths=tuple(Path(item) for item in args.replica),
            stage2_authorization_path=Path(args.stage2_authorization), universe_path=Path(args.universe),
        )
        authorization_path = safe_existing_path(Path(args.stage2_authorization))
        bootstrap_authorization = _load(authorization_path)
        _validate_stage2_authorization(bootstrap_authorization)
        authorize_read_path(bootstrap_authorization, authorization_path)
        authorization = _authorized_load(bootstrap_authorization, authorization_path)
        _validate_stage2_authorization(authorization)
        if authorization != bootstrap_authorization:
            raise VerificationError("Stage-2 authorization changed before report write")
        report_path = Path(args.report)
        expected_report = _expected_sealed_path_schema()["verifier_report"]
        if (
            str(report_path) != str(report_path.resolve())
            or str(report_path) != expected_report
            or str(report_path) not in authorization["source_build_read_allowlist"]
        ):
            raise VerificationError("verifier report output is not an exact fixed-root locator")
        _write_new(report_path, report)
        return 0
    except Exception as exc:
        sys.stderr.write(f"{INVALID}: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "VerificationError", "verify", "verify_synthetic", "reject_synthetic_for_canonical",
    "validate_declarative_universe_spec", "INVALID", "VERIFIER_ID",
]
