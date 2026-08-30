#!/usr/bin/env python3
"""Bounded, deterministic SymPy and Z3 observations for HMASD research gaps.

This module is original HMASD code. It calls public dependency APIs and does not
copy SymPy or Z3 source code. Dependency provenance is recorded in
``DEPENDENCY_METADATA`` below.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

TOOL_ID = "hmasd-symbolic-counterexample-tools"
SCHEMA_VERSION = 1

MAX_INPUT_BYTES = 65_536
MAX_VARIABLES = 12
MAX_EXPRESSION_CHARS = 2_048
MAX_EXPRESSION_NODES = 256
MAX_TOTAL_ASSERTION_CHARS = 8_192
MAX_ASSERTIONS = 48
MAX_INTEGER_ABS = 1_000_000_000
MAX_POWER_ABS = 16
MAX_CROSS_CHECK_POINTS = 32
MIN_PRECISION = 15
MAX_PRECISION = 100
MIN_SOLVER_TIMEOUT_MS = 1
MAX_SOLVER_TIMEOUT_MS = 5_000
MIN_SOLVER_RLIMIT = 1
MAX_SOLVER_RLIMIT = 1_000_000
MAX_RANDOM_SEED = 2_147_483_647

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_PREFIX = "sha256:"

DEPENDENCY_METADATA: dict[str, dict[str, Any]] = {
    "sympy": {
        "distribution": "sympy",
        "reviewed_package_version": "1.13.3",
        "runtime_version_api": "sympy.__version__",
        "source_repository": "https://github.com/sympy/sympy",
        "source_release": "sympy-1.13.3",
        "source_tag_object_sha": "e7c0f3d9002e88ae2518961a22b9aff019615146",
        "source_commit_sha": "b4ce69ad5d40e4e545614b6c76ca9b0be0b98f0b",
        "license": "BSD-3-Clause",
        "license_url": "https://github.com/sympy/sympy/blob/b4ce69ad5d40e4e545614b6c76ca9b0be0b98f0b/LICENSE",
        "copied_code": False,
        "public_apis": [
            "Symbol",
            "Integer",
            "Rational",
            "Add",
            "Mul",
            "Pow",
            "Abs",
            "sin",
            "cos",
            "exp",
            "log",
            "sqrt",
            "expand",
            "cancel",
            "together",
            "factor",
            "trigsimp",
            "count_ops",
            "srepr",
            "N",
            "Basic.subs",
            "Expr.free_symbols",
            "Expr.is_number",
            "Expr.is_zero",
            "oo",
            "zoo",
            "nan",
        ],
    },
    "z3-solver": {
        "distribution": "z3-solver",
        "reviewed_package_version": "4.13.4.0",
        "reviewed_runtime_version": "4.13.4",
        "runtime_version_api": "z3.get_version_string()",
        "source_repository": "https://github.com/Z3Prover/z3",
        "source_release": "z3-4.13.4",
        "source_commit_sha": "6f24123f0c9d1d8bd84dec275c5c7aea939a19fe",
        "license": "MIT",
        "license_url": "https://github.com/Z3Prover/z3/blob/6f24123f0c9d1d8bd84dec275c5c7aea939a19fe/LICENSE.txt",
        "copied_code": False,
        "public_apis": [
            "Bool",
            "Int",
            "Real",
            "BoolVal",
            "IntVal",
            "RealVal",
            "is_bool",
            "is_real",
            "And",
            "Or",
            "Not",
            "Implies",
            "If",
            "Distinct",
            "SolverFor",
            "Solver.set",
            "Solver.add",
            "Solver.check",
            "Solver.model",
            "Solver.reason_unknown",
            "Solver.sexpr",
            "ModelRef.evaluate",
            "Z3Exception",
        ],
    },
}

_BASE_PROPERTIES: dict[str, Any] = {
    "schema_version": {"type": "integer", "const": 1},
    "operation": {"type": "string"},
    "assignment_id": {"type": "string", "pattern": r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
    "gap_id": {"type": "string", "pattern": r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
    "task_family": {"type": "string", "minLength": 1, "maxLength": 128},
    "claim": {"type": "string", "minLength": 1, "maxLength": 4096},
    "evidence_references": {
        "type": "array",
        "minItems": 1,
        "maxItems": 64,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["reference", "locator"],
            "properties": {
                "reference": {"type": "string", "minLength": 1, "maxLength": 1024},
                "locator": {"type": "string", "minLength": 1, "maxLength": 1024},
            },
        },
    },
    "assumptions": {
        "type": "array",
        "maxItems": 64,
        "items": {"type": "string", "minLength": 1, "maxLength": 1024},
    },
    "consequence_decision_relevance": {"type": "string", "minLength": 1, "maxLength": 4096},
}

_BASE_REQUIRED = [
    "schema_version",
    "operation",
    "assignment_id",
    "gap_id",
    "task_family",
    "claim",
    "evidence_references",
    "assumptions",
    "consequence_decision_relevance",
]

SYMPY_IDENTITY_INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "hmasd-symbolic-sympy-identity-input-v1",
    "type": "object",
    "additionalProperties": False,
    "required": _BASE_REQUIRED
    + [
        "variables",
        "lhs",
        "rhs",
        "simplification_operations",
        "expected_residual",
        "precision",
        "cross_check_points",
    ],
    "properties": {
        **_BASE_PROPERTIES,
        "operation": {"const": "sympy_identity"},
        "variables": {
            "type": "array",
            "maxItems": MAX_VARIABLES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "domain", "assumptions"],
                "properties": {
                    "name": {"type": "string", "pattern": _IDENTIFIER.pattern},
                    "domain": {"enum": ["integer", "rational", "real", "complex"]},
                    "assumptions": {
                        "type": "array",
                        "uniqueItems": True,
                        "items": {
                            "enum": [
                                "positive",
                                "nonnegative",
                                "negative",
                                "nonpositive",
                                "nonzero",
                                "even",
                                "odd",
                                "finite",
                            ]
                        },
                    },
                },
            },
        },
        "lhs": {"type": "string", "minLength": 1, "maxLength": MAX_EXPRESSION_CHARS},
        "rhs": {"type": "string", "minLength": 1, "maxLength": MAX_EXPRESSION_CHARS},
        "simplification_operations": {
            "type": "array",
            "maxItems": 5,
            "uniqueItems": True,
            "items": {"enum": ["expand", "cancel", "together", "factor", "trigsimp"]},
        },
        "expected_residual": {"enum": ["zero", "nonzero", "unspecified"]},
        "precision": {"type": "integer", "minimum": MIN_PRECISION, "maximum": MAX_PRECISION},
        "cross_check_points": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_CROSS_CHECK_POINTS,
            "items": {
                "type": "object",
                "additionalProperties": {"type": "string", "minLength": 1, "maxLength": 256},
            },
        },
    },
}

Z3_CHECK_INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "hmasd-symbolic-z3-check-input-v1",
    "type": "object",
    "additionalProperties": False,
    "required": _BASE_REQUIRED
    + ["logic", "variables", "assertions", "timeout_ms", "rlimit", "random_seed"],
    "properties": {
        **_BASE_PROPERTIES,
        "operation": {"const": "z3_check"},
        "logic": {"enum": ["QF_LIA", "QF_LRA", "QF_NIA", "QF_NRA", "QF_UF"]},
        "variables": {
            "type": "array",
            "maxItems": MAX_VARIABLES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "sort"],
                "properties": {
                    "name": {"type": "string", "pattern": _IDENTIFIER.pattern},
                    "sort": {"enum": ["Bool", "Int", "Real"]},
                    "lower": {"type": "integer", "minimum": -MAX_INTEGER_ABS, "maximum": MAX_INTEGER_ABS},
                    "upper": {"type": "integer", "minimum": -MAX_INTEGER_ABS, "maximum": MAX_INTEGER_ABS},
                },
            },
        },
        "assertions": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_ASSERTIONS,
            "items": {"type": "string", "minLength": 1, "maxLength": MAX_EXPRESSION_CHARS},
        },
        "timeout_ms": {
            "type": "integer",
            "minimum": MIN_SOLVER_TIMEOUT_MS,
            "maximum": MAX_SOLVER_TIMEOUT_MS,
        },
        "rlimit": {
            "type": "integer",
            "minimum": MIN_SOLVER_RLIMIT,
            "maximum": MAX_SOLVER_RLIMIT,
        },
        "random_seed": {"type": "integer", "minimum": 0, "maximum": MAX_RANDOM_SEED},
    },
}

INPUT_SCHEMAS = {
    "sympy_identity": SYMPY_IDENTITY_INPUT_SCHEMA,
    "z3_check": Z3_CHECK_INPUT_SCHEMA,
}

PERMITTED_SYMPY_FUNCTIONS = ("Abs", "sin", "cos", "exp", "log", "sqrt")
PERMITTED_SYMPY_OPERATIONS = ("expand", "cancel", "together", "factor", "trigsimp")
PERMITTED_Z3_FUNCTIONS = ("And", "Or", "Not", "Implies", "If", "Distinct")
PERMITTED_Z3_LOGICS = ("QF_LIA", "QF_LRA", "QF_NIA", "QF_NRA", "QF_UF")


class ContractError(ValueError):
    """A deterministic, user-actionable request rejection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sha256(value: Any) -> str:
    return _SHA256_PREFIX + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("INVALID_TYPE", f"{label} must be a JSON object")
    return value


def _require_exact_keys(
    value: Mapping[str, Any], *, required: Sequence[str], optional: Sequence[str] = (), label: str
) -> None:
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - set(value))
    extra = sorted(set(value) - allowed)
    if missing:
        raise ContractError("MISSING_FIELD", f"{label} is missing: {', '.join(missing)}")
    if extra:
        raise ContractError("UNKNOWN_FIELD", f"{label} has unknown fields: {', '.join(extra)}")


def _require_string(value: Any, label: str, *, maximum: int, identifier: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ContractError("INVALID_STRING", f"{label} must be a non-empty string of at most {maximum} characters")
    if identifier and _IDENTIFIER.fullmatch(value) is None:
        raise ContractError("INVALID_IDENTIFIER", f"{label} is not a permitted identifier")
    return value


def _require_integer(value: Any, label: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ContractError("LIMIT_EXCEEDED", f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


def _require_string_list(value: Any, label: str, *, maximum_items: int, maximum_length: int) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise ContractError("LIMIT_EXCEEDED", f"{label} must contain at most {maximum_items} strings")
    result = []
    for index, item in enumerate(value):
        result.append(_require_string(item, f"{label}[{index}]", maximum=maximum_length))
    return result


def _validate_base(request: dict[str, Any], operation_required: Sequence[str]) -> None:
    _require_exact_keys(request, required=[*_BASE_REQUIRED, *operation_required], label="request")
    if request["schema_version"] != SCHEMA_VERSION:
        raise ContractError("UNSUPPORTED_SCHEMA", "schema_version must be 1")
    assignment_id = _require_string(request["assignment_id"], "assignment_id", maximum=128)
    gap_id = _require_string(request["gap_id"], "gap_id", maximum=128)
    if _RECORD_ID.fullmatch(assignment_id) is None or _RECORD_ID.fullmatch(gap_id) is None:
        raise ContractError("INVALID_IDENTIFIER", "assignment_id and gap_id must match the published schema")
    _require_string(request["task_family"], "task_family", maximum=128)
    _require_string(request["claim"], "claim", maximum=4096)
    _require_string(request["consequence_decision_relevance"], "consequence_decision_relevance", maximum=4096)
    _require_string_list(request["assumptions"], "assumptions", maximum_items=64, maximum_length=1024)
    refs = request["evidence_references"]
    if not isinstance(refs, list) or not 1 <= len(refs) <= 64:
        raise ContractError("LIMIT_EXCEEDED", "evidence_references must contain between 1 and 64 entries")
    for index, raw_ref in enumerate(refs):
        ref = _require_object(raw_ref, f"evidence_references[{index}]")
        _require_exact_keys(ref, required=["reference", "locator"], label=f"evidence_references[{index}]")
        _require_string(ref["reference"], f"evidence_references[{index}].reference", maximum=1024)
        _require_string(ref["locator"], f"evidence_references[{index}].locator", maximum=1024)


def _dependency_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ContractError("DEPENDENCY_UNAVAILABLE", f"required distribution {distribution!r} is not installed") from exc


def _load_sympy() -> tuple[Any, dict[str, str]]:
    try:
        sympy = importlib.import_module("sympy")
    except ImportError as exc:
        raise ContractError("DEPENDENCY_UNAVAILABLE", "required distribution 'sympy' is not installed") from exc
    package_version = _dependency_version("sympy")
    runtime_version = str(sympy.__version__)
    expected = DEPENDENCY_METADATA["sympy"]["reviewed_package_version"]
    if package_version != expected or runtime_version != expected:
        raise ContractError(
            "UNREVIEWED_DEPENDENCY_VERSION",
            f"sympy runtime/package versions must both be {expected}; observed {runtime_version}/{package_version}",
        )
    return sympy, {"distribution": "sympy", "package_version": package_version, "runtime_version": runtime_version}


def _load_z3() -> tuple[Any, dict[str, str]]:
    try:
        z3 = importlib.import_module("z3")
    except ImportError as exc:
        raise ContractError("DEPENDENCY_UNAVAILABLE", "required distribution 'z3-solver' is not installed") from exc
    package_version = _dependency_version("z3-solver")
    runtime_version = str(z3.get_version_string())
    expected_package = DEPENDENCY_METADATA["z3-solver"]["reviewed_package_version"]
    expected_runtime = DEPENDENCY_METADATA["z3-solver"]["reviewed_runtime_version"]
    if package_version != expected_package or runtime_version != expected_runtime:
        raise ContractError(
            "UNREVIEWED_DEPENDENCY_VERSION",
            "z3-solver runtime/package versions must be "
            f"{expected_runtime}/{expected_package}; observed {runtime_version}/{package_version}",
        )
    return z3, {
        "distribution": "z3-solver",
        "package_version": package_version,
        "runtime_version": runtime_version,
    }


def _parse_tree(expression: str, label: str) -> ast.Expression:
    _require_string(expression, label, maximum=MAX_EXPRESSION_CHARS)
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise ContractError("INVALID_EXPRESSION", f"{label} is not a valid permitted expression") from exc
    node_count = sum(1 for _ in ast.walk(tree))
    if node_count > MAX_EXPRESSION_NODES:
        raise ContractError("LIMIT_EXCEEDED", f"{label} exceeds {MAX_EXPRESSION_NODES} syntax nodes")
    return tree


def _integer_literal(node: ast.AST, label: str) -> int:
    sign = 1
    raw = node
    if isinstance(raw, ast.UnaryOp) and isinstance(raw.op, (ast.UAdd, ast.USub)):
        sign = -1 if isinstance(raw.op, ast.USub) else 1
        raw = raw.operand
    if isinstance(raw, ast.Constant) and isinstance(raw.value, int) and not isinstance(raw.value, bool):
        value = sign * raw.value
        if abs(value) <= MAX_INTEGER_ABS:
            return value
    raise ContractError("INVALID_EXPRESSION", f"{label} must be an integer literal with magnitude <= {MAX_INTEGER_ABS}")


def _build_sympy_expression(sympy: Any, node: ast.AST, symbols: Mapping[str, Any], label: str) -> Any:
    if isinstance(node, ast.Expression):
        return _build_sympy_expression(sympy, node.body, symbols, label)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ContractError("INVALID_EXPRESSION", f"{label} does not permit Boolean literals")
        if isinstance(node.value, int):
            if abs(node.value) > MAX_INTEGER_ABS:
                raise ContractError("LIMIT_EXCEEDED", f"{label} integer literal exceeds {MAX_INTEGER_ABS}")
            return sympy.Integer(node.value)
        if isinstance(node.value, float):
            text = repr(node.value)
            if len(text) > 64:
                raise ContractError("LIMIT_EXCEEDED", f"{label} decimal literal is too long")
            return sympy.Rational(text)
        raise ContractError("INVALID_EXPRESSION", f"{label} permits only numeric literals")
    if isinstance(node, ast.Name):
        if node.id not in symbols:
            raise ContractError("UNKNOWN_SYMBOL", f"{label} references undeclared symbol {node.id!r}")
        return symbols[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _build_sympy_expression(sympy, node.operand, symbols, label)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp):
        left = _build_sympy_expression(sympy, node.left, symbols, label)
        right = _build_sympy_expression(sympy, node.right, symbols, label)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            exponent = _integer_literal(node.right, f"{label} exponent")
            if abs(exponent) > MAX_POWER_ABS:
                raise ContractError("LIMIT_EXCEEDED", f"{label} exponent magnitude exceeds {MAX_POWER_ABS}")
            return left**exponent
        raise ContractError("INVALID_EXPRESSION", f"{label} contains an unpermitted operator")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in PERMITTED_SYMPY_FUNCTIONS:
            raise ContractError(
                "UNSAFE_EXPRESSION",
                f"{label} permits only functions: {', '.join(PERMITTED_SYMPY_FUNCTIONS)}",
            )
        if node.keywords or len(node.args) != 1:
            raise ContractError("INVALID_EXPRESSION", f"{label} function calls require exactly one positional argument")
        argument = _build_sympy_expression(sympy, node.args[0], symbols, label)
        return getattr(sympy, node.func.id)(argument)
    raise ContractError("UNSAFE_EXPRESSION", f"{label} contains an unpermitted syntax node {type(node).__name__}")


def _bounded_sympy_expression(sympy: Any, text: str, symbols: Mapping[str, Any], label: str) -> Any:
    expression = _build_sympy_expression(sympy, _parse_tree(text, label), symbols, label)
    if int(sympy.count_ops(expression, visual=False)) > MAX_EXPRESSION_NODES:
        raise ContractError("LIMIT_EXCEEDED", f"{label} exceeds {MAX_EXPRESSION_NODES} symbolic operations")
    return expression


def _sympy_symbols(sympy: Any, raw_variables: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(raw_variables, list) or len(raw_variables) > MAX_VARIABLES:
        raise ContractError("LIMIT_EXCEEDED", f"variables must contain at most {MAX_VARIABLES} entries")
    symbols: dict[str, Any] = {}
    frozen: list[dict[str, Any]] = []
    domain_flags = {"integer": "integer", "rational": "rational", "real": "real", "complex": "complex"}
    permitted_assumptions = {
        "positive",
        "nonnegative",
        "negative",
        "nonpositive",
        "nonzero",
        "even",
        "odd",
        "finite",
    }
    for index, raw in enumerate(raw_variables):
        variable = _require_object(raw, f"variables[{index}]")
        _require_exact_keys(variable, required=["name", "domain", "assumptions"], label=f"variables[{index}]")
        name = _require_string(variable["name"], f"variables[{index}].name", maximum=64, identifier=True)
        if name in symbols:
            raise ContractError("DUPLICATE_SYMBOL", f"duplicate symbol {name!r}")
        domain = variable["domain"]
        if domain not in domain_flags:
            raise ContractError("INVALID_DOMAIN", f"variables[{index}].domain is not permitted")
        assumptions = variable["assumptions"]
        if not isinstance(assumptions, list) or len(assumptions) != len(set(assumptions)):
            raise ContractError("INVALID_ASSUMPTIONS", f"variables[{index}].assumptions must be a unique array")
        if not all(item in permitted_assumptions for item in assumptions):
            raise ContractError("INVALID_ASSUMPTIONS", f"variables[{index}] contains an unpermitted assumption")
        flags = {domain_flags[domain]: True, **{item: True for item in assumptions}}
        try:
            symbols[name] = sympy.Symbol(name, **flags)
        except (TypeError, ValueError) as exc:
            raise ContractError("INCONSISTENT_ASSUMPTIONS", f"assumptions for symbol {name!r} are inconsistent") from exc
        frozen.append({"name": name, "domain": domain, "assumptions": list(assumptions)})
    return symbols, frozen


def _sympy_cross_checks(
    sympy: Any,
    residual: Any,
    symbols: Mapping[str, Any],
    raw_points: Any,
    precision: int,
) -> list[dict[str, Any]]:
    if not isinstance(raw_points, list) or not 1 <= len(raw_points) <= MAX_CROSS_CHECK_POINTS:
        raise ContractError(
            "LIMIT_EXCEEDED",
            f"cross_check_points must contain between 1 and {MAX_CROSS_CHECK_POINTS} entries",
        )
    expected_names = set(symbols)
    checks: list[dict[str, Any]] = []
    for point_index, raw_point in enumerate(raw_points):
        point = _require_object(raw_point, f"cross_check_points[{point_index}]")
        if set(point) != expected_names:
            missing = sorted(expected_names - set(point))
            extra = sorted(set(point) - expected_names)
            raise ContractError(
                "INVALID_CROSS_CHECK_POINT",
                f"cross_check_points[{point_index}] must assign every variable; missing={missing}, extra={extra}",
            )
        substitutions: dict[Any, Any] = {}
        frozen_point: dict[str, str] = {}
        for name in sorted(point):
            raw_value = _require_string(point[name], f"cross_check_points[{point_index}].{name}", maximum=256)
            value = _bounded_sympy_expression(sympy, raw_value, {}, f"cross_check_points[{point_index}].{name}")
            if value.free_symbols:
                raise ContractError("INVALID_CROSS_CHECK_POINT", f"cross-check value for {name!r} is not constant")
            substitutions[symbols[name]] = value
            frozen_point[name] = str(value)
        exact = residual.subs(substitutions)
        is_defined_number = bool(exact.is_number) and exact not in (sympy.zoo, sympy.nan, sympy.oo, -sympy.oo)
        exact_zero = bool(is_defined_number and exact == 0)
        exact_nonzero = bool(is_defined_number and getattr(exact, "is_zero", None) is False)
        checks.append(
            {
                "point": frozen_point,
                "defined_number": is_defined_number,
                "exact_residual": str(exact),
                "numeric_residual": str(sympy.N(exact, precision)) if is_defined_number else None,
                "exact_zero": exact_zero,
                "exact_nonzero": exact_nonzero,
            }
        )
    return checks


def _base_product(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "assignment_id": request["assignment_id"],
        "gap_id": request["gap_id"],
        "task_family": request["task_family"],
        "claim": request["claim"],
        "evidence_references": request["evidence_references"],
        "assumptions": request["assumptions"],
        "falsifier_or_counterexample": None,
        "uncertainty_limitations": [],
        "consequence_decision_relevance": request["consequence_decision_relevance"],
        "recommendation": "Treat this tool result as bounded evidence; EM retains scientific disposition authority.",
    }


def _success_envelope(
    request: Mapping[str, Any], dependency_versions: Mapping[str, Any], observation: Mapping[str, Any], product: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_ID,
        "operation": request["operation"],
        "status": "COMPLETED",
        "input_sha256": _sha256(request),
        "dependency_versions": dict(dependency_versions),
        "limits": {
            "max_input_bytes": MAX_INPUT_BYTES,
            "max_variables": MAX_VARIABLES,
            "max_expression_chars": MAX_EXPRESSION_CHARS,
            "max_expression_nodes": MAX_EXPRESSION_NODES,
            "max_assertions": MAX_ASSERTIONS,
            "max_total_assertion_chars": MAX_TOTAL_ASSERTION_CHARS,
            "max_cross_check_points": MAX_CROSS_CHECK_POINTS,
            "max_solver_timeout_ms": MAX_SOLVER_TIMEOUT_MS,
            "max_solver_rlimit": MAX_SOLVER_RLIMIT,
        },
        "request": dict(request),
        "observation": dict(observation),
        "product": dict(product),
        "scientific_disposition": "NOT_PERFORMED",
    }


def run_sympy_identity(request: Mapping[str, Any]) -> dict[str, Any]:
    """Run one bounded identity/residual observation using the reviewed SymPy release."""

    row = _require_object(request, "request")
    operation_fields = [
        "variables",
        "lhs",
        "rhs",
        "simplification_operations",
        "expected_residual",
        "precision",
        "cross_check_points",
    ]
    _validate_base(row, operation_fields)
    if row["operation"] != "sympy_identity":
        raise ContractError("INVALID_OPERATION", "operation must be 'sympy_identity'")
    sympy, version = _load_sympy()
    symbols, frozen_variables = _sympy_symbols(sympy, row["variables"])
    lhs = _bounded_sympy_expression(sympy, row["lhs"], symbols, "lhs")
    rhs = _bounded_sympy_expression(sympy, row["rhs"], symbols, "rhs")
    operations = row["simplification_operations"]
    if (
        not isinstance(operations, list)
        or len(operations) > 5
        or len(operations) != len(set(operations))
        or not all(operation in PERMITTED_SYMPY_OPERATIONS for operation in operations)
    ):
        raise ContractError("INVALID_SIMPLIFICATION", "simplification_operations contains an invalid or duplicate operation")
    expected_residual = row["expected_residual"]
    if expected_residual not in ("zero", "nonzero", "unspecified"):
        raise ContractError("INVALID_EXPECTATION", "expected_residual must be zero, nonzero, or unspecified")
    precision = _require_integer(row["precision"], "precision", minimum=MIN_PRECISION, maximum=MAX_PRECISION)

    raw_residual = lhs - rhs
    residual = raw_residual
    operation_trace = []
    for operation in operations:
        residual = getattr(sympy, operation)(residual)
        if int(sympy.count_ops(residual, visual=False)) > MAX_EXPRESSION_NODES * 4:
            raise ContractError("LIMIT_EXCEEDED", "simplified residual exceeds the symbolic output complexity limit")
        operation_trace.append({"operation": operation, "result_srepr": sympy.srepr(residual)})

    checks = _sympy_cross_checks(sympy, residual, symbols, row["cross_check_points"], precision)
    cas_zero = bool(residual == 0)
    witness = next((check for check in checks if check["exact_nonzero"]), None)
    if witness is not None:
        identity_state = "COUNTEREXAMPLE_FOUND"
        identity_value: bool | None = False
    elif cas_zero and all(check["exact_zero"] for check in checks):
        identity_state = "CAS_ZERO_WITH_EXACT_CROSS_CHECKS"
        identity_value = True
    else:
        identity_state = "NOT_ESTABLISHED"
        identity_value = None

    expectation_matches = (
        expected_residual == "unspecified"
        or (expected_residual == "zero" and cas_zero)
        or (expected_residual == "nonzero" and not cas_zero)
    )
    observation = {
        "identity_state": identity_state,
        "identity_value": identity_value,
        "proof": False,
        "proof_semantics": "SymPy output is a derivation aid, not a proof.",
        "variables": frozen_variables,
        "permitted_functions": list(PERMITTED_SYMPY_FUNCTIONS),
        "lhs_srepr": sympy.srepr(lhs),
        "rhs_srepr": sympy.srepr(rhs),
        "raw_residual_srepr": sympy.srepr(raw_residual),
        "residual_srepr": sympy.srepr(residual),
        "residual_text": str(residual),
        "simplification_trace": operation_trace,
        "expected_residual": expected_residual,
        "expectation_matches": expectation_matches,
        "precision_digits": precision,
        "cross_checks": checks,
    }
    product = _base_product(row)
    product["uncertainty_limitations"] = [
        "CAS simplification and finite substitution checks do not constitute a formal proof.",
        "The conclusion is limited to the declared symbols, assumptions, expressions, operations, and exact check points.",
    ]
    if witness is not None:
        product["falsifier_or_counterexample"] = {
            "kind": "exact_substitution_witness",
            "point": witness["point"],
            "residual": witness["exact_residual"],
        }
        product["recommendation"] = "Inspect the exact witness; it falsifies the declared identity if the encoding matches the intended claim."
    elif cas_zero:
        product["recommendation"] = "Use the recorded derivation as an aid and obtain an independent proof before asserting the identity."
    else:
        product["recommendation"] = "The bounded CAS check is inconclusive; refine the derivation or supply a discriminating exact point."
    return _success_envelope(row, {"sympy": version}, observation, product)


def _z3_variables(z3: Any, raw_variables: Any) -> tuple[dict[str, Any], list[Any], list[dict[str, Any]]]:
    if not isinstance(raw_variables, list) or len(raw_variables) > MAX_VARIABLES:
        raise ContractError("LIMIT_EXCEEDED", f"variables must contain at most {MAX_VARIABLES} entries")
    variables: dict[str, Any] = {}
    domain_constraints: list[Any] = []
    frozen: list[dict[str, Any]] = []
    constructors = {"Bool": z3.Bool, "Int": z3.Int, "Real": z3.Real}
    for index, raw in enumerate(raw_variables):
        variable = _require_object(raw, f"variables[{index}]")
        _require_exact_keys(
            variable,
            required=["name", "sort"],
            optional=["lower", "upper"],
            label=f"variables[{index}]",
        )
        name = _require_string(variable["name"], f"variables[{index}].name", maximum=64, identifier=True)
        if name in variables:
            raise ContractError("DUPLICATE_SYMBOL", f"duplicate symbol {name!r}")
        sort = variable["sort"]
        if sort not in constructors:
            raise ContractError("INVALID_DOMAIN", f"variables[{index}].sort must be Bool, Int, or Real")
        lower = variable.get("lower")
        upper = variable.get("upper")
        if sort == "Bool" and (lower is not None or upper is not None):
            raise ContractError("INVALID_DOMAIN", f"Boolean variable {name!r} cannot have numeric bounds")
        if sort != "Bool" and (lower is None or upper is None):
            raise ContractError("UNBOUNDED_DOMAIN", f"numeric variable {name!r} requires lower and upper bounds")
        symbol = constructors[sort](name)
        variables[name] = symbol
        frozen_variable: dict[str, Any] = {"name": name, "sort": sort}
        if sort != "Bool":
            checked_lower = _require_integer(lower, f"variables[{index}].lower", minimum=-MAX_INTEGER_ABS, maximum=MAX_INTEGER_ABS)
            checked_upper = _require_integer(upper, f"variables[{index}].upper", minimum=-MAX_INTEGER_ABS, maximum=MAX_INTEGER_ABS)
            if checked_lower > checked_upper:
                raise ContractError("INVALID_DOMAIN", f"variable {name!r} has lower > upper")
            domain_constraints.extend([symbol >= checked_lower, symbol <= checked_upper])
            frozen_variable.update({"lower": checked_lower, "upper": checked_upper})
        frozen.append(frozen_variable)
    return variables, domain_constraints, frozen

def _contains_declared_symbol(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(item, ast.Name) and item.id in names for item in ast.walk(node))


def _validate_z3_logic(tree: ast.Expression, logic: str, variable_names: set[str], label: str) -> None:
    if logic == "QF_UF":
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, int)
                and not isinstance(node.value, bool)
            ):
                raise ContractError("LOGIC_MISMATCH", f"{label} uses an integer literal outside QF_UF")
            if isinstance(node, ast.BinOp):
                raise ContractError("LOGIC_MISMATCH", f"{label} uses arithmetic outside QF_UF")
            if isinstance(node, ast.Compare) and any(
                not isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops
            ):
                raise ContractError("LOGIC_MISMATCH", f"{label} uses ordering outside QF_UF")
        return
    if logic not in ("QF_LIA", "QF_LRA"):
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp):
            continue
        if isinstance(node.op, ast.Mult):
            if _contains_declared_symbol(node.left, variable_names) and _contains_declared_symbol(
                node.right, variable_names
            ):
                raise ContractError("LOGIC_MISMATCH", f"{label} contains nonlinear multiplication in {logic}")
        elif isinstance(node.op, (ast.Div, ast.Mod)):
            if _contains_declared_symbol(node.right, variable_names):
                raise ContractError("LOGIC_MISMATCH", f"{label} contains a variable divisor in {logic}")
            if isinstance(node.op, ast.Mod) and logic == "QF_LRA":
                raise ContractError("LOGIC_MISMATCH", f"{label} uses modulo in real arithmetic")
        elif isinstance(node.op, ast.Pow):
            exponent = _integer_literal(node.right, f"{label} exponent")
            if exponent not in (0, 1):
                raise ContractError("LOGIC_MISMATCH", f"{label} contains a nonlinear power in {logic}")



def _build_z3_expression(z3: Any, node: ast.AST, variables: Mapping[str, Any], label: str) -> Any:
    if isinstance(node, ast.Expression):
        return _build_z3_expression(z3, node.body, variables, label)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return z3.BoolVal(node.value)
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            if abs(node.value) > MAX_INTEGER_ABS:
                raise ContractError("LIMIT_EXCEEDED", f"{label} integer literal exceeds {MAX_INTEGER_ABS}")
            constructor = z3.RealVal if any(z3.is_real(symbol) for symbol in variables.values()) else z3.IntVal
            return constructor(node.value)
        raise ContractError("INVALID_EXPRESSION", f"{label} permits only Boolean and integer literals")
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ContractError("UNKNOWN_SYMBOL", f"{label} references undeclared symbol {node.id!r}")
        return variables[node.id]
    if isinstance(node, ast.UnaryOp):
        operand = _build_z3_expression(z3, node.operand, variables, label)
        if isinstance(node.op, ast.Not):
            return z3.Not(operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ContractError("INVALID_EXPRESSION", f"{label} contains an unpermitted unary operator")
    if isinstance(node, ast.BoolOp):
        values = [_build_z3_expression(z3, item, variables, label) for item in node.values]
        if isinstance(node.op, ast.And):
            return z3.And(*values)
        if isinstance(node.op, ast.Or):
            return z3.Or(*values)
        raise ContractError("INVALID_EXPRESSION", f"{label} contains an unpermitted Boolean operator")
    if isinstance(node, ast.BinOp):
        left = _build_z3_expression(z3, node.left, variables, label)
        right = _build_z3_expression(z3, node.right, variables, label)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            exponent = _integer_literal(node.right, f"{label} exponent")
            if not 0 <= exponent <= MAX_POWER_ABS:
                raise ContractError("LIMIT_EXCEEDED", f"{label} exponent must be in [0, {MAX_POWER_ABS}]")
            return left**exponent
        raise ContractError("INVALID_EXPRESSION", f"{label} contains an unpermitted arithmetic operator")
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise ContractError("INVALID_EXPRESSION", f"{label} does not permit chained comparisons")
        left = _build_z3_expression(z3, node.left, variables, label)
        right = _build_z3_expression(z3, node.comparators[0], variables, label)
        operator = node.ops[0]
        if isinstance(operator, ast.Eq):
            return left == right
        if isinstance(operator, ast.NotEq):
            return left != right
        if isinstance(operator, ast.Lt):
            return left < right
        if isinstance(operator, ast.LtE):
            return left <= right
        if isinstance(operator, ast.Gt):
            return left > right
        if isinstance(operator, ast.GtE):
            return left >= right
        raise ContractError("INVALID_EXPRESSION", f"{label} comparison operator is not permitted")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in PERMITTED_Z3_FUNCTIONS:
            raise ContractError(
                "UNSAFE_EXPRESSION",
                f"{label} permits only functions: {', '.join(PERMITTED_Z3_FUNCTIONS)}",
            )
        if node.keywords:
            raise ContractError("INVALID_EXPRESSION", f"{label} function calls do not accept keyword arguments")
        args = [_build_z3_expression(z3, item, variables, label) for item in node.args]
        arity = len(args)
        if node.func.id in ("Not",) and arity != 1:
            raise ContractError("INVALID_EXPRESSION", f"{node.func.id} requires one argument")
        if node.func.id in ("Implies",) and arity != 2:
            raise ContractError("INVALID_EXPRESSION", f"{node.func.id} requires two arguments")
        if node.func.id == "If" and arity != 3:
            raise ContractError("INVALID_EXPRESSION", "If requires three arguments")
        if node.func.id in ("And", "Or", "Distinct") and not 1 <= arity <= MAX_VARIABLES:
            raise ContractError("LIMIT_EXCEEDED", f"{node.func.id} requires 1..{MAX_VARIABLES} arguments")
        return getattr(z3, node.func.id)(*args)
    raise ContractError("UNSAFE_EXPRESSION", f"{label} contains an unpermitted syntax node {type(node).__name__}")


def _bounded_z3_expression(
    z3: Any, text: str, variables: Mapping[str, Any], logic: str, label: str
) -> Any:
    tree = _parse_tree(text, label)
    _validate_z3_logic(tree, logic, set(variables), label)
    try:
        expression = _build_z3_expression(z3, tree, variables, label)
    except z3.Z3Exception as exc:
        raise ContractError("INVALID_EXPRESSION", f"{label} is ill-typed for the declared Z3 sorts") from exc
    if not z3.is_bool(expression):
        raise ContractError("INVALID_ASSERTION", f"{label} must produce a Boolean formula")
    return expression


def run_z3_check(request: Mapping[str, Any]) -> dict[str, Any]:
    """Run one resource-bounded Z3 check without converting UNKNOWN to proof."""

    row = _require_object(request, "request")
    operation_fields = ["logic", "variables", "assertions", "timeout_ms", "rlimit", "random_seed"]
    _validate_base(row, operation_fields)
    if row["operation"] != "z3_check":
        raise ContractError("INVALID_OPERATION", "operation must be 'z3_check'")
    logic = row["logic"]
    if logic not in PERMITTED_Z3_LOGICS:
        raise ContractError("INVALID_LOGIC", f"logic must be one of {', '.join(PERMITTED_Z3_LOGICS)}")
    timeout_ms = _require_integer(
        row["timeout_ms"],
        "timeout_ms",
        minimum=MIN_SOLVER_TIMEOUT_MS,
        maximum=MAX_SOLVER_TIMEOUT_MS,
    )
    rlimit = _require_integer(row["rlimit"], "rlimit", minimum=MIN_SOLVER_RLIMIT, maximum=MAX_SOLVER_RLIMIT)
    random_seed = _require_integer(row["random_seed"], "random_seed", minimum=0, maximum=MAX_RANDOM_SEED)
    assertions_text = row["assertions"]
    if not isinstance(assertions_text, list) or not 1 <= len(assertions_text) <= MAX_ASSERTIONS:
        raise ContractError("LIMIT_EXCEEDED", f"assertions must contain between 1 and {MAX_ASSERTIONS} entries")
    if sum(len(item) for item in assertions_text if isinstance(item, str)) > MAX_TOTAL_ASSERTION_CHARS:
        raise ContractError("LIMIT_EXCEEDED", f"assertions exceed {MAX_TOTAL_ASSERTION_CHARS} total characters")

    z3, version = _load_z3()
    variables, domain_constraints, frozen_variables = _z3_variables(z3, row["variables"])
    numeric_sorts = {item["sort"] for item in frozen_variables if item["sort"] != "Bool"}
    permitted_numeric_sort = {
        "QF_LIA": {"Int"},
        "QF_NIA": {"Int"},
        "QF_LRA": {"Real"},
        "QF_NRA": {"Real"},
        "QF_UF": set(),
    }[logic]
    if not numeric_sorts <= permitted_numeric_sort:
        raise ContractError("LOGIC_MISMATCH", f"declared variable sorts do not match logic {logic}")
    assertions = [
        _bounded_z3_expression(z3, text, variables, logic, f"assertions[{index}]")
        for index, text in enumerate(assertions_text)
    ]
    try:
        solver = z3.SolverFor(logic)
        solver.set(timeout=timeout_ms, rlimit=rlimit, random_seed=random_seed)
        solver.add(*domain_constraints)
        solver.add(*assertions)
        frozen_smt2 = solver.sexpr()
    except z3.Z3Exception as exc:
        raise ContractError("SOLVER_CONFIGURATION_FAILED", "Z3 rejected the frozen encoding or solver options") from exc
    encoding = {
        "kind": "generated_smtlib2_from_safe_json_dsl",
        "logic": logic,
        "variables": frozen_variables,
        "assertions": list(assertions_text),
        "solver_options": {"timeout_ms": timeout_ms, "rlimit": rlimit, "random_seed": random_seed},
        "solver_sexpr": frozen_smt2,
    }
    encoding_sha256 = _sha256(encoding)
    try:
        check_result = solver.check()
    except z3.Z3Exception as exc:
        raise ContractError("SOLVER_FAILED", "Z3 failed while checking the frozen encoding") from exc

    witness = None
    reason_unknown = None
    if check_result == z3.sat:
        solver_status = "SAT"
        model = solver.model()
        witness = {
            name: {
                "sort": next(item["sort"] for item in frozen_variables if item["name"] == name),
                "value": model.evaluate(symbol, model_completion=True).sexpr(),
            }
            for name, symbol in sorted(variables.items())
        }
        proof_semantics = "SAT supplies a concrete witness for the frozen encoding; it is not a broader scientific conclusion."
    elif check_result == z3.unsat:
        solver_status = "UNSAT"
        proof_semantics = "UNSAT applies only to the frozen encoding, logic, bounds, assumptions, and solver result."
    else:
        solver_status = "UNKNOWN"
        reason_unknown = str(solver.reason_unknown())
        proof_semantics = "UNKNOWN is inconclusive and is never translated into a proof or UNSAT claim."

    observation = {
        "solver_status": solver_status,
        "proof": False,
        "proof_semantics": proof_semantics,
        "witness": witness,
        "reason_unknown": reason_unknown,
        "encoding": encoding,
        "encoding_sha256": encoding_sha256,
        "encoding_audit": {
            "safe_json_dsl": True,
            "arbitrary_python": False,
            "shell_execution": False,
            "permitted_functions": list(PERMITTED_Z3_FUNCTIONS),
            "declared_logic": logic,
        },
    }
    product = _base_product(row)
    product["uncertainty_limitations"] = [
        "The solver result applies only to the recorded encoding, declared logic, bounded domains, and solver options.",
        "A SAT model is a witness for the encoding; UNSAT is encoding-relative; UNKNOWN is inconclusive.",
    ]
    if solver_status == "SAT":
        product["falsifier_or_counterexample"] = {
            "kind": "z3_sat_witness",
            "encoding_sha256": encoding_sha256,
            "model": witness,
        }
        product["recommendation"] = "Audit the encoding, then inspect the SAT witness against the target claim."
    elif solver_status == "UNSAT":
        product["recommendation"] = "Audit the frozen encoding before using the encoding-relative UNSAT result in further reasoning."
    else:
        product["recommendation"] = "Record UNKNOWN as inconclusive; do not infer proof, satisfiability, or unsatisfiability."
    return _success_envelope(row, {"z3-solver": version}, observation, product)


def run_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and execute one supported request."""

    row = _require_object(request, "request")
    operation = row.get("operation")
    if operation == "sympy_identity":
        return run_sympy_identity(row)
    if operation == "z3_check":
        return run_z3_check(row)
    raise ContractError("INVALID_OPERATION", "operation must be 'sympy_identity' or 'z3_check'")


def _failure_envelope(error: ContractError) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_ID,
        "status": "FAILED",
        "scientific_disposition": "NOT_PERFORMED",
        "error": {"code": error.code, "message": str(error)},
    }


def _read_request(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError("INPUT_READ_FAILED", f"cannot read input file: {exc.strerror or type(exc).__name__}") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise ContractError("LIMIT_EXCEEDED", f"input file exceeds {MAX_INPUT_BYTES} bytes")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("INVALID_JSON", "input file must contain one UTF-8 JSON object") from exc
    return _require_object(value, "request")


def _emit(value: Any) -> None:
    sys.stdout.buffer.write(_canonical_json_bytes(value) + b"\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bounded SymPy identity checks or Z3 counterexample searches from a JSON request."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", metavar="PATH", help="UTF-8 JSON request file")
    group.add_argument(
        "--schema",
        choices=sorted(INPUT_SCHEMAS),
        help="print the exact JSON input schema for one operation",
    )
    group.add_argument("--metadata", action="store_true", help="print dependency provenance and API metadata")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.schema:
        _emit(INPUT_SCHEMAS[args.schema])
        return 0
    if args.metadata:
        _emit({"schema_version": SCHEMA_VERSION, "tool": TOOL_ID, "dependencies": DEPENDENCY_METADATA})
        return 0
    try:
        result = run_request(_read_request(args.input))
    except ContractError as exc:
        _emit(_failure_envelope(exc))
        return 2
    except Exception:
        _emit(
            _failure_envelope(
                ContractError(
                    "TOOL_EXECUTION_FAILED",
                    "the dependency failed while executing the validated bounded request",
                )
            )
        )
        return 3
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
