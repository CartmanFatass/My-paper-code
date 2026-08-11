
"""Source-bound exact-feasibility selector for the VSP06-B2R1 treatment.

This module is import-safe without OR-Tools.  The canonical selector entry
point fails closed unless the exact pinned CPython/OR-Tools identity is
available.  It has no alternative solver and never interprets infeasibility as
a scientific conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from itertools import product
from typing import Any, Iterable, Mapping, Sequence


SELECTOR_ID = "VSP06-B2R1-SB-EF-CP-SAT-V1"
VERIFIER_ID = "VSP06-B2R1-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
TREATMENT_ID = (
    "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-EXACT-FEASIBILITY"
)
CATALOG_ID = "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CATALOG-V1"
LEDGER_ID = "VSP06-B2R1-CONSTRAINT-TARGET-LEDGER-V1"
SALT = "8100799/"
DECISION_PREFIX = b"VSP06-B2R1-SB-EF-CP-SAT-V1/decision-order/v1\0"
REQUIRED_ORTOOLS = "9.12.4544"
REQUIRED_PYTHON = (3, 11)
WALL_SECONDS = 1800
MEMORY_BYTES = 4096 * 1024 * 1024
INVALID = "B2R1_SELECTOR_INVALID_NO_RUN"
VALID = "B2R1_SELECTOR_VERIFIED_MANIFEST_FIXED"

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

DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v8"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
ACTIVITY_NAMES = (
    "canonical_generator_calls", "canonical_rows_observed", "canonical_ortools_processes",
    "replicas", "canonical_verifier_admissions", "witnesses", "manifests", "model_fits",
    "trainer_calls", "environment_episodes", "environment_transitions", "policy_forwards",
    "learner_updates", "optimizer_steps", "evaluator_calls", "evaluation_episodes",
    "environment_rng_calls", "action_rng_calls",
)


def validate_stage2_authorization(value: Mapping[str, Any]) -> Mapping[str, Any]:
    required = {
        "direction", "candidate", "treatment_id", "selector_id", "verifier_id",
        "scientific_parent", "final_commit", "source_build_read_allowlist",
        "formal", "synthetic_only", "zero_start_activity",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise SelectorInvalid("missing or malformed Stage-2 authorization")
    fixed = {
        "direction": DIRECTION_ID, "candidate": CANDIDATE_ID, "treatment_id": TREATMENT_ID,
        "selector_id": SELECTOR_ID, "verifier_id": VERIFIER_ID,
        "scientific_parent": SCIENTIFIC_PARENT, "formal": False, "synthetic_only": False,
    }
    if any(value[key] != expected for key, expected in fixed.items()):
        raise SelectorInvalid("Stage-2 authorization binding mismatch")
    commit = value["final_commit"]
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SelectorInvalid("Stage-2 final commit must be one exact lowercase 40-hex binding")
    allowlist = value["source_build_read_allowlist"]
    if not isinstance(allowlist, list) or not allowlist or any(
        not isinstance(item, str) or not item or not Path(item).is_absolute()
        or ".." in Path(item).parts or any(char in item for char in "*?[")
        for item in allowlist
    ) or len(set(allowlist)) != len(allowlist):
        raise SelectorInvalid("Stage-2 source/build/read allowlist is absent")
    activity = value["zero_start_activity"]
    if not isinstance(activity, Mapping) or set(activity) != set(ACTIVITY_NAMES) or any(v != 0 or isinstance(v, bool) for v in activity.values()):
        raise SelectorInvalid("Stage-2 zero-start activity binding failed")
    return value


def _is_reparse(path: Path) -> bool:
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_existing_path(path: Path) -> Path:
    text = str(path)
    if not text or any(char in text for char in "*?[") or ".." in path.parts:
        raise SelectorInvalid("glob, empty, and parent-traversal locators are forbidden")
    absolute = Path(os.path.abspath(path))
    component = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        component = component / part
        if component.exists() and (component.is_symlink() or _is_reparse(component)):
            raise SelectorInvalid("link/junction/reparse read locator is forbidden")
    resolved = path.resolve(strict=True)
    if resolved != absolute or not resolved.is_file():
        raise SelectorInvalid("read locator alias or non-regular file is forbidden")
    predecessor = "vsp06_" + "b2_"
    if predecessor in resolved.as_posix().casefold():
        raise SelectorInvalid("predecessor read locator is forbidden")
    return resolved


def authorize_read_path(authorization: Mapping[str, Any], path: Path) -> Path:
    validate_stage2_authorization(authorization)
    resolved = safe_existing_path(path)
    if str(path) != str(resolved) or str(resolved) not in authorization["source_build_read_allowlist"]:
        raise SelectorInvalid("read locator is not the exact authorized canonical path")
    return resolved


class SelectorInvalid(RuntimeError):
    """Fail-closed selector/config/lifecycle error."""


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
        raise SelectorInvalid(f"{field} must be an NFC string")
    return value


def canonical_tuple_bytes(row: Mapping[str, Any]) -> bytes:
    """Serialize one catalog tuple as a fixed-schema canonical JSON array."""

    if not isinstance(row, Mapping) or tuple(row) != TUPLE_FIELDS:
        raise SelectorInvalid("catalog tuple fields do not match declared order")
    integers = {"retention_length", "y", "reset_y", "target_identity", "target_version", "nonce"}
    strings = set(TUPLE_FIELDS) - integers - {"decoy_sequence"}
    for field in integers:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SelectorInvalid(f"{field} must be a nonnegative integer")
    for field in strings:
        _strict_text(row[field], field)
    decoys = row["decoy_sequence"]
    if not isinstance(decoys, list) or not decoys:
        raise SelectorInvalid("decoy_sequence must be a nonempty list")
    normalized_decoys: list[list[Any]] = []
    for index, decoy in enumerate(decoys):
        if (
            not isinstance(decoy, list)
            or len(decoy) != 4
            or any(isinstance(decoy[i], bool) or not isinstance(decoy[i], int) for i in (0, 1, 2))
            or not isinstance(decoy[3], bool)
        ):
            raise SelectorInvalid(f"decoy_sequence[{index}] has invalid schema")
        normalized_decoys.append([int(decoy[0]), int(decoy[1]), int(decoy[2]), decoy[3]])
    positional = [normalized_decoys if field == "decoy_sequence" else row[field] for field in TUPLE_FIELDS]
    return _canonical_json_bytes(positional)


def bucket_for_tuple(payload: bytes) -> int:
    return hashlib.sha256(SALT.encode("utf-8") + payload).digest()[0] % 8


def split_for_bucket(bucket: int) -> str:
    if isinstance(bucket, bool) or not isinstance(bucket, int) or not 0 <= bucket <= 7:
        raise SelectorInvalid("bucket must be an integer in 0..7")
    return "train" if bucket <= 5 else "calibration" if bucket == 6 else "evaluation"


def decision_key(payload: bytes) -> bytes:
    return hashlib.sha256(DECISION_PREFIX + payload).digest()


@dataclass(frozen=True)
class CatalogRow:
    source_index: int
    tuple_value: Mapping[str, Any]
    tuple_bytes: bytes
    tuple_sha256: str
    bucket: int
    split: str
    decision_key: bytes


def parse_catalog(raw: Mapping[str, Any]) -> tuple[CatalogRow, ...]:
    if (
        not isinstance(raw, Mapping)
        or raw.get("catalog_id") != CATALOG_ID
        or raw.get("salt") != SALT
        or set(raw) != {"catalog_id", "salt", "rows"}
        or not isinstance(raw.get("rows"), list)
        or not raw["rows"]
    ):
        raise SelectorInvalid("raw catalog envelope is invalid")

    parsed: list[CatalogRow] = []
    seen: set[bytes] = set()
    for index, row in enumerate(raw["rows"]):
        payload = canonical_tuple_bytes(row)
        if payload in seen:
            raise SelectorInvalid("catalog tuples are not unique")
        seen.add(payload)
        bucket = bucket_for_tuple(payload)
        parsed.append(
            CatalogRow(
                source_index=index,
                tuple_value=dict(row),
                tuple_bytes=payload,
                tuple_sha256=sha256_bytes(payload),
                bucket=bucket,
                split=split_for_bucket(bucket),
                decision_key=decision_key(payload),
            )
        )
    canonical = tuple(sorted(parsed, key=lambda item: item.tuple_bytes))
    if tuple(item.tuple_bytes for item in canonical) != tuple(
        sorted(item.tuple_bytes for item in parsed)
    ):
        raise SelectorInvalid("catalog canonical ordering failed")
    return canonical


def _validate_predicate(predicate: Mapping[str, Any]) -> None:
    if not isinstance(predicate, Mapping) or set(predicate) - {"eq", "in"}:
        raise SelectorInvalid("ledger predicate has unsupported operators")
    if not predicate:
        raise SelectorInvalid("ledger predicate may not be empty")
    for operator, clauses in predicate.items():
        if not isinstance(clauses, Mapping) or not clauses:
            raise SelectorInvalid("ledger predicate clauses are invalid")
        for field, value in clauses.items():
            if field not in TUPLE_FIELDS and field not in {"split", "bucket"}:
                raise SelectorInvalid(f"ledger predicate field is unknown: {field}")
            if operator == "in" and (not isinstance(value, list) or not value):
                raise SelectorInvalid("ledger 'in' values must be a nonempty list")


def parse_ledger(raw: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    required = {"ledger_id", "equation_semantics", "equation_templates", "family_counts", "ledger_digest"}
    if not isinstance(raw, Mapping) or set(raw) != required or raw.get("ledger_id") != LEDGER_ID:
        raise SelectorInvalid("raw target ledger envelope is invalid")
    digest_body = {key: value for key, value in raw.items() if key != "ledger_digest"}
    if raw["ledger_digest"] != sha256_bytes(_canonical_json_bytes(digest_body)):
        raise SelectorInvalid("target ledger digest mismatch")
    if raw.get("equation_semantics") != "sum(integer_coefficient * selected_row_indicator) == integer_rhs":
        raise SelectorInvalid("target ledger semantics changed")
    templates = raw.get("equation_templates")
    if not isinstance(templates, list) or not templates:
        raise SelectorInvalid("target ledger has no equation templates")
    equations: list[Mapping[str, Any]] = []
    def substitute(value: Any, bindings: Mapping[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            if value[1:] not in bindings:
                raise SelectorInvalid("ledger template references an unknown axis")
            return bindings[value[1:]]
        if isinstance(value, list):
            return [substitute(item, bindings) for item in value]
        if isinstance(value, Mapping):
            return {key: substitute(item, bindings) for key, item in value.items()}
        return value
    for template in templates:
        if not isinstance(template, Mapping) or set(template) != {"name_template", "family", "axes", "terms", "rhs"}:
            raise SelectorInvalid("ledger equation-template schema is invalid")
        axes = template["axes"]
        if not isinstance(axes, Mapping) or any(not isinstance(values, list) or not values for values in axes.values()):
            raise SelectorInvalid("ledger equation-template axes are invalid")
        axis_names = tuple(axes)
        for values in product(*(axes[name] for name in axis_names)):
            bindings = dict(zip(axis_names, values))
            equations.append({
                "name": str(template["name_template"]).format(**bindings),
                "family": template["family"],
                "terms": substitute(template["terms"], bindings),
                "rhs": substitute(template["rhs"], bindings),
            })
    names: set[str] = set()
    observed_families: dict[str, int] = {}
    for equation in equations:
        if not isinstance(equation, Mapping) or set(equation) != {"name", "family", "terms", "rhs"}:
            raise SelectorInvalid("ledger equation schema is invalid")
        name = _strict_text(equation["name"], "equation.name")
        family = _strict_text(equation["family"], "equation.family")
        if name in names:
            raise SelectorInvalid("ledger equation names are not unique")
        names.add(name)
        rhs = equation["rhs"]
        if isinstance(rhs, bool) or not isinstance(rhs, int):
            raise SelectorInvalid("ledger RHS must be integer")
        terms = equation["terms"]
        if not isinstance(terms, list) or not terms:
            raise SelectorInvalid("ledger equation must have terms")
        for term in terms:
            if not isinstance(term, Mapping) or set(term) != {"coefficient", "predicate"}:
                raise SelectorInvalid("ledger term schema is invalid")
            coefficient = term["coefficient"]
            if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient == 0:
                raise SelectorInvalid("ledger coefficients must be nonzero integers")
            _validate_predicate(term["predicate"])
        observed_families[family] = observed_families.get(family, 0) + 1
    if raw["family_counts"] != observed_families:
        raise SelectorInvalid("ledger family counts mismatch")
    return tuple(equations)


def _field(row: CatalogRow, name: str) -> Any:
    if name == "split":
        return row.split
    if name == "bucket":
        return row.bucket
    return row.tuple_value[name]


def predicate_matches(row: CatalogRow, predicate: Mapping[str, Any]) -> bool:
    for field, expected in predicate.get("eq", {}).items():
        if _field(row, field) != expected:
            return False
    for field, allowed in predicate.get("in", {}).items():
        if _field(row, field) not in allowed:
            return False
    return True


def compile_equations(
    rows: Sequence[CatalogRow], equations: Sequence[Mapping[str, Any]]
) -> tuple[tuple[str, str, tuple[tuple[int, int], ...], int], ...]:
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
            key = _canonical_json_bytes(_field(row, field))
            inverted[field].setdefault(key, set()).add(index)

    def matching(predicate: Mapping[str, Any]) -> set[int]:
        candidates: list[set[int]] = []
        for field, expected in predicate.get("eq", {}).items():
            candidates.append(inverted[field].get(_canonical_json_bytes(expected), set()))
        for field, allowed in predicate.get("in", {}).items():
            union: set[int] = set()
            for value in allowed:
                union.update(inverted[field].get(_canonical_json_bytes(value), set()))
            candidates.append(union)
        if not candidates:
            raise SelectorInvalid("ledger predicate has no indexed clauses")
        result = set(candidates[0])
        for candidate in candidates[1:]:
            result.intersection_update(candidate)
        return result

    compiled = []
    for equation in equations:
        coefficients: dict[int, int] = {}
        for term in equation["terms"]:
            coefficient = int(term["coefficient"])
            for index in matching(term["predicate"]):
                coefficients[index] = coefficients.get(index, 0) + coefficient
        sparse = tuple((index, value) for index, value in sorted(coefficients.items()) if value)
        if not sparse:
            raise SelectorInvalid(f"ledger equation has empty support: {equation['name']}")
        compiled.append((equation["name"], equation["family"], sparse, int(equation["rhs"])))
    return tuple(compiled)


def canonical_order(rows: Sequence[CatalogRow]) -> tuple[int, ...]:
    return tuple(
        sorted(
            range(len(rows)),
            key=lambda index: (rows[index].decision_key, rows[index].tuple_bytes),
        )
    )



def validate_final_keep_support(rows: Sequence[CatalogRow]) -> dict[str, Any]:
    """Reject structurally impossible final-KEEP support before CP-SAT."""

    final_rows = [row for row in rows if row.tuple_value["consumer"] == "final_keep"]
    expected_seeds = {"primary_1", "primary_2", "primary_3", "primary_4"}
    groups: dict[tuple[str, str], list[CatalogRow]] = {}
    for row in final_rows:
        value = row.tuple_value
        if row.split != "evaluation" or value["branch"] != "KEEP" or value["retention_length"] != 6:
            raise SelectorInvalid("final-KEEP row is structurally ineligible")
        groups.setdefault((value["seed_row"], value["quartet_base"]), []).append(row)
    if {seed for seed, _base in groups} != expected_seeds:
        raise SelectorInvalid("final-KEEP seed support is incomplete")
    structural_fields = tuple(field for field in TUPLE_FIELDS if field not in {"y", "nonce"})
    for key, group in groups.items():
        if len(group) != 4 or {row.tuple_value["y"] for row in group} != {0, 1, 2, 3}:
            raise SelectorInvalid(f"final-KEEP quartet is incomplete: {key}")
        reference = tuple(group[0].tuple_value[field] for field in structural_fields)
        if any(tuple(row.tuple_value[field] for field in structural_fields) != reference for row in group[1:]):
            raise SelectorInvalid(f"final-KEEP quartet is not structurally identical: {key}")
    event_domain = {"target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster"}
    for seed in sorted(expected_seeds):
        seed_rows = [row for row in final_rows if row.tuple_value["seed_row"] == seed]
        seed_groups = {row.tuple_value["quartet_base"] for row in seed_rows}
        if len(seed_rows) != 256 or len(seed_groups) != 64:
            raise SelectorInvalid("final-KEEP requires exactly 64 complete quartets per seed")
        for field, domain in (
            ("target_identity", set(range(4))),
            ("target_version", set(range(4))),
            ("event_type", event_domain),
        ):
            counts = {value: sum(row.tuple_value[field] == value for row in seed_rows) for value in domain}
            if set(counts.values()) != {64}:
                raise SelectorInvalid(f"final-KEEP {field} support is not exactly balanced")
        decoy_counts: dict[bytes, int] = {}
        for row in seed_rows:
            key = _canonical_json_bytes(row.tuple_value["decoy_sequence"])
            decoy_counts[key] = decoy_counts.get(key, 0) + 1
        if len(decoy_counts) != 4 or set(decoy_counts.values()) != {64}:
            raise SelectorInvalid("final-KEEP ordered-decoy support is not exactly balanced")
    return {
        "selected_count_required": 1024,
        "quartet_count": len(groups),
        "per_seed_quartets": 64,
        "balanced_fields": ["target_identity", "target_version", "event_type", "decoy_sequence"],
        "digest": sha256_bytes(_canonical_json_bytes(sorted((key[0], key[1]) for key in groups))),
    }


def validate_catalog_structural_support(rows: Sequence[CatalogRow]) -> dict[str, Any]:
    """Necessary frozen count/marginal support check before model construction."""

    final_report = validate_final_keep_support(rows)
    minima: list[tuple[str, Mapping[str, Any], int]] = []
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for branch, target in (("KEEP", 384), ("RESET", 64), ("CURRENT", 64)):
            for length in (4, 8):
                for y in range(4):
                    minima.append((
                        f"primary/{seed}/{branch}/{length}/{y}",
                        {"consumer": "primary_fit", "seed_row": seed, "branch": branch,
                         "retention_length": length, "y": y}, target,
                    ))
    for consumer, target in (("calibration_fit", 128), ("calibration_check", 32)):
        for y in range(4):
            minima.append((f"{consumer}/{y}", {"consumer": consumer, "y": y}, target))
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for panel in ("0", "512", "1024", "1536", "2048", "2560", "3072", "4096"):
            for branch, target in (("KEEP", 16), ("RESET", 8), ("CURRENT", 8)):
                for y in range(4):
                    minima.append((
                        f"checkpoint/{seed}/{panel}/{branch}/{y}",
                        {"consumer": "checkpoint", "seed_row": seed, "panel": panel,
                         "branch": branch, "y": y}, target,
                    ))
    for name, clauses, target in minima:
        support = [row for row in rows if all(row.tuple_value[field] == value for field, value in clauses.items())]
        if len(support) < target:
            raise SelectorInvalid(f"canonical structural support below target: {name}")
        for field in ("target_identity", "target_version", "event_type", "decoy_sequence"):
            values = {_canonical_json_bytes(row.tuple_value[field]) for row in support}
            if len(values) != 4:
                raise SelectorInvalid(f"canonical marginal support incomplete: {name}/{field}")
        if clauses.get("branch") == "RESET":
            for reset_y in range(4):
                if sum(row.tuple_value["reset_y"] == reset_y for row in support) < target // 4:
                    raise SelectorInvalid(f"fresh reset-Y support incomplete: {name}/{reset_y}")
    reset_strata = []
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for length in (4, 8):
            reset_strata.append((
                f"primary/{seed}/{length}",
                {"consumer": "primary_fit", "seed_row": seed, "branch": "RESET", "retention_length": length},
                16,
            ))
        for panel in ("0", "512", "1024", "1536", "2048", "2560", "3072", "4096"):
            reset_strata.append((
                f"checkpoint/{seed}/{panel}",
                {"consumer": "checkpoint", "seed_row": seed, "panel": panel, "branch": "RESET"},
                2,
            ))
    for name, clauses, minimum in reset_strata:
        support = [row for row in rows if all(row.tuple_value[field] == value for field, value in clauses.items())]
        for reset_y in range(4):
            for field in ("target_identity", "target_version", "event_type", "decoy_sequence"):
                values = {_canonical_json_bytes(row.tuple_value[field]) for row in support}
                for value in values:
                    count = sum(
                        row.tuple_value["reset_y"] == reset_y
                        and _canonical_json_bytes(row.tuple_value[field]) == value
                        for row in support
                    )
                    if count < minimum:
                        raise SelectorInvalid(f"fresh reset-Y pairwise support incomplete: {name}/{reset_y}/{field}")
    return {
        "final_keep": final_report,
        "minimum_strata_checked": len(minima),
        "reset_pairwise_strata_checked": len(reset_strata),
        "catalog_row_count": len(rows),
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise SelectorInvalid(f"JSON root must be an object: {path}")
    return value


def _ortools_bindings() -> tuple[Any, Any, Any]:
    if sys.version_info[:2] != REQUIRED_PYTHON:
        raise SelectorInvalid("CPython 3.11 ABI is required")
    try:
        version = importlib.metadata.version("ortools")
    except importlib.metadata.PackageNotFoundError as exc:
        raise SelectorInvalid(f"ortools=={REQUIRED_ORTOOLS} is not installed") from exc
    if version != REQUIRED_ORTOOLS:
        raise SelectorInvalid(f"ortools build mismatch: {version!r}")
    try:
        from ortools.sat.python import cp_model
        from ortools.sat import sat_parameters_pb2
        import ortools
    except Exception as exc:
        raise SelectorInvalid("pinned OR-Tools CP-SAT import failed") from exc
    return cp_model, sat_parameters_pb2, ortools


def _parameters(sat_parameters_pb2: Any) -> Any:
    parameters = sat_parameters_pb2.SatParameters()
    for name, value in PARAMETER_ASSIGNMENTS.items():
        if name == "search_branching":
            value = sat_parameters_pb2.SatParameters.FIXED_SEARCH
        setattr(parameters, name, value)
    return parameters


def selector_environment(stage2_authorization: Mapping[str, Any]) -> dict[str, Any]:
    validate_stage2_authorization(stage2_authorization)
    cp_model, sat_parameters_pb2, ortools = _ortools_bindings()
    del cp_model
    parameters = _parameters(sat_parameters_pb2)
    distribution = importlib.metadata.distribution("ortools")
    inventory = distribution.files
    if inventory is None:
        raise SelectorInvalid("OR-Tools distribution metadata inventory is absent")
    artifacts = []
    for item in sorted(inventory, key=lambda entry: str(entry)):
        if Path(str(item)).suffix.lower() not in {".pyd", ".so", ".dll"}:
            continue
        artifact = safe_existing_path(Path(distribution.locate_file(item)))
        if str(artifact) not in stage2_authorization["source_build_read_allowlist"]:
            raise SelectorInvalid("OR-Tools artifact is outside the exact authorized read set")
        artifacts.append(artifact)
    if not artifacts:
        raise SelectorInvalid("OR-Tools native solver artifact is absent")
    artifact_rows = [[str(path), sha256_file(path)] for path in artifacts]
    parameter_bytes = parameters.SerializeToString(deterministic=True)
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_sha256": sha256_file(Path(sys.executable).resolve()),
        "ortools_version": REQUIRED_ORTOOLS,
        "ortools_source_tag": "v9.12",
        "solver_artifacts": artifact_rows,

        "solver_artifact_set_sha256": sha256_bytes(_canonical_json_bytes(artifact_rows)),
        "sat_parameters_sha256": sha256_bytes(parameter_bytes),
        "sat_parameters_hex": parameter_bytes.hex(),
        "sat_parameter_assignments": dict(PARAMETER_ASSIGNMENTS),
        "sat_parameter_assignments_sha256": sha256_bytes(
            _canonical_json_bytes(PARAMETER_ASSIGNMENTS)
        ),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
    }


def source_bindings(selector_path: Path, verifier_path: Path) -> dict[str, str]:
    return {
        "selector_source_sha256": sha256_file(selector_path),
        "verifier_source_sha256": sha256_file(verifier_path),
    }


def _manifest_body(
    rows: Sequence[CatalogRow], vector: Sequence[int], bindings: Mapping[str, Any]
) -> dict[str, Any]:
    selected = [row for row, value in zip(rows, vector) if value == 1]
    selected_rows = [
        {
            "tuple": dict(row.tuple_value),
            "tuple_sha256": row.tuple_sha256,
            "bucket": row.bucket,
            "split": row.split,
        }
        for row in selected
    ]
    order_digest = sha256_bytes(
        _canonical_json_bytes([item["tuple_sha256"] for item in selected_rows])
    )
    return {
        "manifest_id": "vsp06_b2r1_authenticated_partner_recall_manifest_v1",
        "treatment": TREATMENT_ID,
        "selector_identity": SELECTOR_ID,
        "bindings": dict(bindings),
        "selected_count": len(selected_rows),
        "selected_rows": selected_rows,
        "common_two_arm_order_digest": order_digest,
        "rank_claim": False,
    }


def solve_replica(catalog_path: Path, ledger_path: Path, bindings_path: Path, stage2_authorization: Mapping[str, Any]) -> dict[str, Any]:
    validate_stage2_authorization(stage2_authorization)
    catalog_path = authorize_read_path(stage2_authorization, catalog_path)
    ledger_path = authorize_read_path(stage2_authorization, ledger_path)
    bindings_path = authorize_read_path(stage2_authorization, bindings_path)
    raw_catalog = _load_json(catalog_path)
    raw_ledger = _load_json(ledger_path)
    expected_bindings = _load_json(bindings_path)
    rows = parse_catalog(raw_catalog)
    equations = parse_ledger(raw_ledger)
    validate_catalog_structural_support(rows)
    compiled = compile_equations(rows, equations)
    environment = selector_environment(stage2_authorization)
    declared_expected = expected_bindings.get("expected")
    if not isinstance(declared_expected, Mapping) or not isinstance(declared_expected.get("universe_sha256"), str):
        raise SelectorInvalid("independent universe binding absent")
    actual = {
        **source_bindings(Path(__file__).resolve(), Path(expected_bindings["verifier_path"]).resolve()),
        "catalog_sha256": sha256_file(catalog_path),
        "ledger_sha256": sha256_file(ledger_path),
        "final_commit": stage2_authorization["final_commit"],
        "stage2_authorization_sha256": sha256_bytes(_canonical_json_bytes(stage2_authorization)),
        "universe_sha256": declared_expected["universe_sha256"],
        **environment,
    }
    expected = declared_expected
    if not isinstance(expected, Mapping) or dict(expected) != actual:
        raise SelectorInvalid("source/build/input/parameter binding mismatch")

    cp_model, sat_parameters_pb2, _ortools = _ortools_bindings()
    model = cp_model.CpModel()
    variables = [model.NewBoolVar(f"x_{index}") for index in range(len(rows))]
    for _name, _family, sparse, rhs in compiled:
        model.Add(sum(coefficient * variables[index] for index, coefficient in sparse) == rhs)
    order = canonical_order(rows)
    model.AddDecisionStrategy(
        [variables[index] for index in order],
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MAX_VALUE,
    )
    solver = cp_model.CpSolver()
    solver.parameters.CopyFrom(_parameters(sat_parameters_pb2))
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    if status_name not in {"FEASIBLE", "OPTIMAL"}:
        raise SelectorInvalid(f"non-admissible CP-SAT terminal status: {status_name}")
    vector = [int(solver.Value(variable)) for variable in variables]
    if len(vector) != len(rows) or any(value not in (0, 1) for value in vector):
        raise SelectorInvalid("CP-SAT returned a partial/nonbinary witness")
    manifest = _manifest_body(rows, vector, actual)
    return {
        "selector_identity": SELECTOR_ID,
        "terminal_status": status_name,
        "membership_vector": vector,
        "membership_vector_sha256": sha256_bytes(_canonical_json_bytes(vector)),
        "selected_tuple_sha256": [row.tuple_sha256 for row, value in zip(rows, vector) if value],
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(_canonical_json_bytes(manifest)),
        "solver_response_stats": solver.ResponseStats(),
    }


def compare_replicas(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "selector_identity",
        "terminal_status",
        "membership_vector",
        "membership_vector_sha256",
        "selected_tuple_sha256",
        "manifest",
        "manifest_sha256",
    )
    if left.get("terminal_status") not in {"FEASIBLE", "OPTIMAL"} or any(left.get(key) != right.get(key) for key in keys):
        raise SelectorInvalid("two mandatory cold replicas disagree")
    vector = left.get("membership_vector")
    if not isinstance(vector, list) or not vector or any(value not in (0, 1) for value in vector):
        raise SelectorInvalid("replica witness is incomplete or nonbinary")
    return dict(left)


def write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as exc:
        raise SelectorInvalid(f"write-once destination already exists: {path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    write_exclusive(path, _canonical_json_bytes(value) + b"\n")


def _apply_resource_cap(process: subprocess.Popen[bytes]) -> Any:
    """Bind one logical CPU and 4096 MiB; child waits for a start token."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        kernel32.SetProcessAffinityMask.restype = wintypes.BOOL
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process_handle = wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
        if not kernel32.SetProcessAffinityMask(process_handle, 1):
            raise SelectorInvalid("failed to enforce one-logical-CPU affinity")

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]


        class EXTENDED(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BASIC),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            raise SelectorInvalid("failed to create Windows selector job")
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x100 | 0x2000  # kill-on-close + process-memory
        info.ProcessMemoryLimit = MEMORY_BYTES
        if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            kernel32.CloseHandle(job)
            raise SelectorInvalid("failed to enforce selector memory cap")
        if not kernel32.AssignProcessToJobObject(job, process_handle):
            kernel32.CloseHandle(job)
            raise SelectorInvalid("failed to assign selector resource job")
        return (kernel32, job)
    try:
        os.sched_setaffinity(process.pid, {min(os.sched_getaffinity(0))})
    except (AttributeError, OSError) as exc:
        raise SelectorInvalid("failed to enforce one-logical-CPU affinity") from exc
    return None


def _release_resource_cap(token: Any) -> None:
    if token is not None:
        kernel32, job = token
        kernel32.CloseHandle(job)


def _self_memory_cap() -> None:
    if os.name == "nt":
        return
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    except (ImportError, OSError, ValueError) as exc:
        raise SelectorInvalid("failed to enforce selector 4096-MiB memory cap") from exc
    if soft != MEMORY_BYTES or hard != MEMORY_BYTES:
        raise SelectorInvalid("selector memory cap did not bind exactly")


def _run_cold_replica(
    *, selector_path: Path, catalog_path: Path, ledger_path: Path,
    bindings_path: Path, output_path: Path, authorization_path: Path,
) -> Mapping[str, Any]:
    command = [
        sys.executable, "-I", "-B", str(selector_path), "replica",
        "--catalog", str(catalog_path), "--ledger", str(ledger_path),
        "--bindings", str(bindings_path), "--output", str(output_path),
        "--stage2-authorization", str(authorization_path),
        "--await-start-token",
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    cap = None
    try:
        cap = _apply_resource_cap(process)
        assert process.stdin is not None
        process.stdin.write(b"START\n")
        process.stdin.flush()
        process.stdin.close()
        process.stdin = None
        stdout, stderr = process.communicate(timeout=WALL_SECONDS)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise SelectorInvalid("cold replica exceeded 1800 wall seconds") from exc
    except Exception:
        process.kill()
        process.communicate()
        raise
    finally:
        _release_resource_cap(cap)
    elapsed = time.monotonic() - started
    write_exclusive(output_path.with_name(output_path.stem + ".stdout.log"), stdout)
    write_exclusive(output_path.with_name(output_path.stem + ".stderr.log"), stderr)
    if process.returncode != 0:
        raise SelectorInvalid(
            "cold replica failed closed: "
            + stderr.decode("utf-8", errors="replace")[:500]
        )
    telemetry = {
        "wall_seconds": elapsed,
        "wall_cap_seconds": WALL_SECONDS,
        "logical_cpu_cap": 1,
        "process_memory_cap_bytes": MEMORY_BYTES,
        "return_code": process.returncode,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
    }
    _write_json_exclusive(
        output_path.with_name(output_path.stem + ".resource.json"), telemetry
    )
    result = dict(_load_json(output_path))
    result["resource_telemetry"] = telemetry
    return result


def run_two_replica_sequence(
    *, catalog_path: Path, ledger_path: Path, manifest_path: Path,
    verifier_path: Path, universe_path: Path, work_root: Path, stage2_authorization_path: Path,
) -> dict[str, Any]:
    """One external invocation: exactly two cold replicas, verifier, publish."""

    stage2_authorization_path = safe_existing_path(stage2_authorization_path)
    authorization = _load_json(stage2_authorization_path)
    validate_stage2_authorization(authorization)
    authorize_read_path(authorization, stage2_authorization_path)
    catalog_path = authorize_read_path(authorization, catalog_path)
    universe_path = authorize_read_path(authorization, universe_path)
    ledger_path = authorize_read_path(authorization, ledger_path)
    verifier_path = authorize_read_path(authorization, verifier_path)
    authorize_read_path(authorization, Path(__file__).resolve())
    if manifest_path.exists():
        raise SelectorInvalid("canonical manifest destination already exists")
    receipt_path = work_root / "selector_success_receipt.json"
    declared_outputs = (
        work_root / "frozen_bindings.json",
        work_root / "cold_replica_1.json", work_root / "cold_replica_2.json",
        work_root / "membership_witness.json",
        work_root / "proposed_manifest.json",
        work_root / "independent_verifier_report.json",
        receipt_path,
    )
    if any(path.exists() for path in declared_outputs):
        raise SelectorInvalid("pre-existing selector output invalidates the one invocation")
    work_root.mkdir(parents=True, exist_ok=True)
    selector_path = Path(__file__).resolve()
    expected = {
        **source_bindings(selector_path, verifier_path.resolve()),
        "catalog_sha256": sha256_file(catalog_path),
        "ledger_sha256": sha256_file(ledger_path),
        "universe_sha256": sha256_file(universe_path),
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": sha256_bytes(_canonical_json_bytes(authorization)),
        **selector_environment(authorization),
    }
    bindings = {
        "selector_path": str(selector_path),
        "verifier_path": str(verifier_path.resolve()),
        "synthetic_only": False,
        "expected": expected,
    }
    bindings_path = work_root / "frozen_bindings.json"
    _write_json_exclusive(bindings_path, bindings)
    replicas = []
    for replica_index in (1, 2):
        output = work_root / f"cold_replica_{replica_index}.json"
        replicas.append(
            _run_cold_replica(
                selector_path=selector_path,
                catalog_path=catalog_path,
                ledger_path=ledger_path,
                bindings_path=bindings_path,
                output_path=output,
                authorization_path=stage2_authorization_path,
            )
        )
    agreed = compare_replicas(replicas[0], replicas[1])
    witness_path = work_root / "membership_witness.json"
    witness = {
        "selector_identity": SELECTOR_ID,
        "membership_vector": agreed["membership_vector"],
        "membership_vector_sha256": agreed["membership_vector_sha256"],
    }
    _write_json_exclusive(witness_path, witness)
    proposal_path = work_root / "proposed_manifest.json"
    _write_json_exclusive(proposal_path, agreed["manifest"])
    verifier_report_path = work_root / "independent_verifier_report.json"
    verifier_command = [
        sys.executable, "-I", "-B", str(verifier_path.resolve()),
        "--catalog", str(catalog_path), "--ledger", str(ledger_path),
        "--universe", str(universe_path),
        "--witness", str(witness_path), "--manifest", str(proposal_path),
        "--bindings", str(bindings_path), "--report", str(verifier_report_path),
        "--replica", str(work_root / "cold_replica_1.json"),
        "--replica", str(work_root / "cold_replica_2.json"),
        "--stage2-authorization", str(stage2_authorization_path),
    ]
    completed = subprocess.run(
        verifier_command, capture_output=True, timeout=WALL_SECONDS, check=False
    )
    if completed.returncode != 0 or completed.stdout or completed.stderr:
        raise SelectorInvalid("independent verifier failed closed")
    report = _load_json(verifier_report_path)
    if report.get("verdict") != "VERIFIED" or report.get("manifest_sha256") != agreed["manifest_sha256"]:

        raise SelectorInvalid("independent verifier report mismatch")
    manifest_bytes = _canonical_json_bytes(agreed["manifest"]) + b"\n"
    write_exclusive(manifest_path, manifest_bytes)
    if sha256_file(manifest_path) != sha256_bytes(manifest_bytes):
        raise SelectorInvalid("published manifest reload digest mismatch")
    try:
        manifest_path.chmod(0o444)
    except OSError as exc:
        raise SelectorInvalid("published manifest could not be made read-only") from exc
    success = {
        "branch": VALID,
        "replica_count": 2,
        "replica_2_role": "prospective_determinism_gate_not_retry",
        "catalog_path": str(catalog_path.resolve()),
        "catalog_sha256": sha256_file(catalog_path),
        "ledger_path": str(ledger_path.resolve()),
        "ledger_sha256": sha256_file(ledger_path),
        "bindings_path": str(bindings_path.resolve()),
        "bindings_sha256": sha256_file(bindings_path),
        "witness_path": str(witness_path.resolve()),
        "witness_sha256": sha256_file(witness_path),
        "manifest_path": str(manifest_path),
        "manifest_file_sha256": sha256_file(manifest_path),
        "manifest_content_sha256": agreed["manifest_sha256"],
        "verifier_report_path": str(verifier_report_path),
        "verifier_report_sha256": sha256_file(verifier_report_path),
        "replica_resource_telemetry": [
            replicas[0]["resource_telemetry"], replicas[1]["resource_telemetry"]
        ],
    }
    _write_json_exclusive(receipt_path, success)
    success["selector_success_receipt_path"] = str(receipt_path.resolve())
    success["selector_success_receipt_sha256"] = sha256_file(receipt_path)
    return success


def _replica_cli(args: argparse.Namespace) -> int:
    authorization_path = safe_existing_path(Path(args.stage2_authorization))
    authorization = _load_json(authorization_path)
    validate_stage2_authorization(authorization)
    authorize_read_path(authorization, authorization_path)
    if args.await_start_token:
        _self_memory_cap()
        if sys.stdin.buffer.readline() != b"START\n":
            raise SelectorInvalid("cold replica start-token gate failed")
    result = solve_replica(
        Path(args.catalog), Path(args.ledger), Path(args.bindings), authorization
    )
    _write_json_exclusive(Path(args.output), result)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    replica = sub.add_parser("replica")
    replica.add_argument("--catalog", required=True)
    replica.add_argument("--ledger", required=True)
    replica.add_argument("--stage2-authorization", required=True)
    replica.add_argument("--bindings", required=True)
    replica.add_argument("--output", required=True)
    replica.add_argument("--await-start-token", action="store_true")
    args = parser.parse_args(argv)
    try:
        return _replica_cli(args)
    except Exception as exc:
        sys.stderr.write(f"{INVALID}: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CatalogRow", "SelectorInvalid", "canonical_tuple_bytes", "bucket_for_tuple",
    "split_for_bucket", "decision_key", "parse_catalog", "parse_ledger",
    "compile_equations", "canonical_order", "compare_replicas", "write_exclusive",
    "validate_final_keep_support", "validate_catalog_structural_support",
    "selector_environment", "run_two_replica_sequence", "INVALID", "VALID",
]
