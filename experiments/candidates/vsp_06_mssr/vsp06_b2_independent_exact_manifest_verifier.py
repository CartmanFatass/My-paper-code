"""Independent stdlib-only exact verifier for VSP06-B2 manifests.

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
import struct
import sys
import unicodedata
from itertools import product
from typing import Any, Mapping, Sequence


VERIFIER_ID = "VSP06-B2-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
SELECTOR_ID = "VSP06-B2-SB-EF-CP-SAT-V1"
TREATMENT_ID = (
    "VSP06-B2-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-EXACT-FEASIBILITY"
)
CATALOG_ID = "vsp06_b2_authenticated_partner_recall_catalog_v1"
LEDGER_ID = "constraint_target_ledger_v1"
SALT = "8100699/"
REQUIRED_ORTOOLS = "9.12.4544"
INVALID = "B2_SELECTOR_INVALID_NO_RUN"
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


class VerificationError(RuntimeError):
    """Independent exact-verification failure."""


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


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise VerificationError(f"JSON root must be an object: {path}")
    return value


def _tuple_bytes(row: Mapping[str, Any]) -> bytes:
    if not isinstance(row, Mapping) or set(row) != set(TUPLE_FIELDS):
        raise VerificationError("catalog tuple schema mismatch")
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
    positional = [CATALOG_ID]
    for field in TUPLE_FIELDS:
        positional.append(normalized if field == "decoy_sequence" else row[field])
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
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in selected:
        if row["tuple"]["consumer"] == "final_keep":
            groups.setdefault(row["tuple"]["quartet_base"], []).append(row["tuple"])
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


def _check_live_binding(expected: Mapping[str, Any]) -> None:
    if platform.python_implementation() != "CPython" or sys.version_info[:2] != (3, 11):
        raise VerificationError("canonical verifier requires live CPython 3.11")
    if (
        expected["python_implementation"] != platform.python_implementation()
        or expected["python_version"] != platform.python_version()
        or Path(str(expected["python_executable"])).resolve() != Path(sys.executable).resolve()
        or expected["python_executable_sha256"] != _file_digest(Path(sys.executable).resolve())
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
    actual_artifacts = sorted(
        [str(Path(distribution.locate_file(item)).resolve()), _file_digest(Path(distribution.locate_file(item)).resolve())]
        for item in (distribution.files or ())
        if Path(str(item)).suffix.lower() in {".pyd", ".so", ".dll"}
        and Path(distribution.locate_file(item)).is_file()
    )
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


def verify(
    *, catalog_path: Path, ledger_path: Path, witness_path: Path,
    manifest_path: Path, bindings_path: Path,
) -> dict[str, Any]:
    raw_catalog = _load(catalog_path)
    raw_ledger = _load(ledger_path)
    witness = _load(witness_path)
    manifest = _load(manifest_path)
    bindings = _load(bindings_path)
    rows = _parse_catalog(raw_catalog)
    equations = _parse_ledger(raw_ledger)
    expected = bindings.get("expected")
    if not isinstance(expected, Mapping):
        raise VerificationError("frozen binding envelope is absent")
    required_binding_keys = {
        "selector_source_sha256", "verifier_source_sha256", "catalog_sha256",
        "ledger_sha256", "python_implementation", "python_version",
        "python_executable", "python_executable_sha256", "ortools_version",
        "ortools_source_tag", "solver_artifacts", "solver_artifact_set_sha256",
        "sat_parameters_sha256", "sat_parameters_hex", "sat_parameter_assignments",
        "sat_parameter_assignments_sha256", "os", "os_release",
        "architecture",
    }
    if set(expected) != required_binding_keys:
        raise VerificationError("source/build/parameter binding key set changed")
    synthetic_only = bindings.get("synthetic_only") is True
    if set(bindings) != {"selector_path", "verifier_path", "synthetic_only", "expected"}:
        raise VerificationError("binding envelope key set changed")
    selector_path = Path(str(bindings.get("selector_path", ""))).resolve()
    verifier_path = Path(str(bindings.get("verifier_path", ""))).resolve()
    if (
        verifier_path != Path(__file__).resolve()
        or expected["verifier_source_sha256"] != _file_digest(verifier_path)
        or expected["selector_source_sha256"] != _file_digest(selector_path)
        or expected["catalog_sha256"] != _file_digest(catalog_path)
        or expected["ledger_sha256"] != _file_digest(ledger_path)
    ):
        raise VerificationError("source/input binding mismatch")
    if not synthetic_only:
        if raw_ledger.get("family_counts") != CANONICAL_FAMILY_COUNTS:
            raise VerificationError("canonical constraint-family counts mismatch")
        _check_live_binding(expected)
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
        manifest.get("manifest_id") != "vsp06_b2_authenticated_partner_recall_manifest_v1"
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
        "catalog_sha256": _file_digest(catalog_path),
        "ledger_sha256": _file_digest(ledger_path),
        "selector_source_sha256": expected["selector_source_sha256"],
        "solver_artifact_set_sha256": expected["solver_artifact_set_sha256"],
        "sat_parameters_sha256": expected["sat_parameters_sha256"],
        "python_executable_sha256": expected["python_executable_sha256"],
        "membership_witness_sha256": _file_digest(witness_path),
        "membership_vector_sha256": witness["membership_vector_sha256"],
        "manifest_sha256": manifest_digest,
        "verifier_source_sha256": expected["verifier_source_sha256"],
        "common_two_arm_order_digest": order_digest,
        "global_rank_claim": False,
    }


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
    args = parser.parse_args(argv)
    try:
        report = verify(
            catalog_path=Path(args.catalog).resolve(),
            ledger_path=Path(args.ledger).resolve(),
            witness_path=Path(args.witness).resolve(),
            manifest_path=Path(args.manifest).resolve(),
            bindings_path=Path(args.bindings).resolve(),
        )
        _write_new(Path(args.report).resolve(), report)
        return 0
    except Exception as exc:
        sys.stderr.write(f"{INVALID}: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["VerificationError", "verify", "INVALID", "VERIFIER_ID"]
