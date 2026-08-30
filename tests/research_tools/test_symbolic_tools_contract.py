from __future__ import annotations

import importlib.metadata

import pytest

from tools.research.symbolic import symbolic_tools


def _base_request(operation: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "operation": operation,
        "assignment_id": "assignment-symbolic-1",
        "gap_id": "gap-algebra-1",
        "task_family": "counterexample/adversarial search",
        "claim": "The frozen encoded identity or constraint has the stated result.",
        "evidence_references": [
            {"reference": "artifact://frozen-claim", "locator": "claim[0]"},
        ],
        "assumptions": ["Only the declared domains and formulas are in scope."],
        "consequence_decision_relevance": "A witness would narrow the target claim; no tool result sets scientific disposition.",
    }


def _sympy_request(lhs: str, rhs: str, points: list[dict[str, str]]) -> dict[str, object]:
    request = _base_request("sympy_identity")
    request.update(
        {
            "variables": [{"name": "x", "domain": "real", "assumptions": []}],
            "lhs": lhs,
            "rhs": rhs,
            "simplification_operations": ["expand", "cancel"],
            "expected_residual": "zero",
            "precision": 40,
            "cross_check_points": points,
        }
    )
    return request


def _z3_request(assertions: list[str]) -> dict[str, object]:
    request = _base_request("z3_check")
    request.update(
        {
            "logic": "QF_LIA",
            "variables": [{"name": "x", "sort": "Int", "lower": 0, "upper": 10}],
            "assertions": assertions,
            "timeout_ms": 1_000,
            "rlimit": 100_000,
            "random_seed": 17,
        }
    )
    return request


def test_valid_identity_records_exact_derivation_without_claiming_proof() -> None:
    sympy = pytest.importorskip("sympy")
    assert sympy.__version__ == "1.13.3"

    result = symbolic_tools.run_request(
        _sympy_request(
            "(x + 1)**2",
            "x**2 + 2*x + 1",
            [{"x": "-2"}, {"x": "0"}, {"x": "3/2"}],
        )
    )

    assert result["schema_version"] == 1
    assert result["status"] == "COMPLETED"
    assert result["observation"]["identity_state"] == "CAS_ZERO_WITH_EXACT_CROSS_CHECKS"
    assert result["observation"]["identity_value"] is True
    assert result["observation"]["proof"] is False
    assert "not a proof" in result["observation"]["proof_semantics"]
    assert all(check["exact_zero"] for check in result["observation"]["cross_checks"])
    assert result["dependency_versions"]["sympy"] == {
        "distribution": "sympy",
        "package_version": importlib.metadata.version("sympy"),
        "runtime_version": sympy.__version__,
    }
    assert result["input_sha256"].startswith("sha256:")
    assert result["scientific_disposition"] == "NOT_PERFORMED"


def test_false_identity_returns_exact_counterexample_witness() -> None:
    pytest.importorskip("sympy")
    request = _sympy_request("x**2", "x", [{"x": "0"}, {"x": "1"}, {"x": "2"}])
    request["expected_residual"] = "unspecified"

    result = symbolic_tools.run_request(request)

    assert result["observation"]["identity_state"] == "COUNTEREXAMPLE_FOUND"
    assert result["observation"]["identity_value"] is False
    assert result["observation"]["proof"] is False
    assert result["product"]["falsifier_or_counterexample"] == {
        "kind": "exact_substitution_witness",
        "point": {"x": "2"},
        "residual": "2",
    }


def test_z3_sat_returns_a_bounded_concrete_witness() -> None:
    z3 = pytest.importorskip("z3")
    assert z3.get_version_string() == "4.13.4"

    result = symbolic_tools.run_request(_z3_request(["x > 7"]))

    assert result["observation"]["solver_status"] == "SAT"
    assert result["observation"]["proof"] is False
    witness_value = int(result["observation"]["witness"]["x"]["value"])
    assert 7 < witness_value <= 10
    assert result["product"]["falsifier_or_counterexample"]["kind"] == "z3_sat_witness"
    assert result["observation"]["encoding_sha256"].startswith("sha256:")
    assert result["dependency_versions"]["z3-solver"]["package_version"] == "4.13.4.0"


def test_z3_unsat_is_explicitly_relative_to_the_frozen_encoding() -> None:
    pytest.importorskip("z3")

    result = symbolic_tools.run_request(_z3_request(["x > 7", "x < 3"]))

    assert result["observation"]["solver_status"] == "UNSAT"
    assert result["observation"]["witness"] is None
    assert result["observation"]["reason_unknown"] is None
    assert result["observation"]["proof"] is False
    assert "only to the frozen encoding" in result["observation"]["proof_semantics"]


def test_z3_unknown_remains_inconclusive(monkeypatch: pytest.MonkeyPatch) -> None:
    z3 = pytest.importorskip("z3")

    class UnknownSolver:
        def set(self, **_options: object) -> None:
            return None

        def add(self, *_constraints: object) -> None:
            return None

        def sexpr(self) -> str:
            return "(assert true)"

        def check(self) -> object:
            return z3.unknown

        def reason_unknown(self) -> str:
            return "contract-test-resource-limit"

    monkeypatch.setattr(z3, "SolverFor", lambda _logic: UnknownSolver())
    request = _z3_request(["x >= 0"])

    result = symbolic_tools.run_request(request)

    assert result["observation"]["solver_status"] == "UNKNOWN"
    assert result["observation"]["reason_unknown"] == "contract-test-resource-limit"
    assert result["observation"]["witness"] is None
    assert result["observation"]["proof"] is False
    assert "never translated into a proof" in result["observation"]["proof_semantics"]
    assert result["product"]["falsifier_or_counterexample"] is None
    assert result["status"] == "COMPLETED"


@pytest.mark.parametrize(
    "unsafe_expression",
    [
        "evil(x)",
        "x.__class__",
        "__import__('os').system('id')",
        "(lambda y: y)(x)",
    ],
)
def test_invalid_or_unsafe_sympy_functions_are_rejected(unsafe_expression: str) -> None:
    pytest.importorskip("sympy")
    request = _sympy_request(unsafe_expression, "x", [{"x": "1"}])

    with pytest.raises(symbolic_tools.ContractError) as caught:
        symbolic_tools.run_request(request)

    assert caught.value.code in {"UNSAFE_EXPRESSION", "UNKNOWN_SYMBOL"}

def test_unsafe_z3_function_is_rejected_before_solver_execution() -> None:
    pytest.importorskip("z3")
    request = _z3_request(["ExecutePython(x)"])

    with pytest.raises(symbolic_tools.ContractError) as caught:
        symbolic_tools.run_request(request)

    assert caught.value.code == "UNSAFE_EXPRESSION"



def test_variable_and_solver_limits_are_enforced() -> None:
    pytest.importorskip("sympy")
    too_many_variables = _sympy_request("x", "x", [{"x": "1"}])
    too_many_variables["variables"] = [
        {"name": f"x{index}", "domain": "integer", "assumptions": []}
        for index in range(symbolic_tools.MAX_VARIABLES + 1)
    ]

    with pytest.raises(symbolic_tools.ContractError) as variable_error:
        symbolic_tools.run_request(too_many_variables)
    assert variable_error.value.code == "LIMIT_EXCEEDED"

    too_slow = _z3_request(["x >= 0"])
    too_slow["timeout_ms"] = symbolic_tools.MAX_SOLVER_TIMEOUT_MS + 1
    with pytest.raises(symbolic_tools.ContractError) as timeout_error:
        symbolic_tools.run_request(too_slow)
    assert timeout_error.value.code == "LIMIT_EXCEEDED"


def test_input_schemas_are_closed_and_publish_all_resource_limits() -> None:
    sympy_schema = symbolic_tools.INPUT_SCHEMAS["sympy_identity"]
    z3_schema = symbolic_tools.INPUT_SCHEMAS["z3_check"]

    assert sympy_schema["additionalProperties"] is False
    assert z3_schema["additionalProperties"] is False
    assert sympy_schema["properties"]["variables"]["maxItems"] == symbolic_tools.MAX_VARIABLES
    assert sympy_schema["properties"]["cross_check_points"]["maxItems"] == symbolic_tools.MAX_CROSS_CHECK_POINTS
    assert z3_schema["properties"]["assertions"]["maxItems"] == symbolic_tools.MAX_ASSERTIONS
    assert z3_schema["properties"]["timeout_ms"]["maximum"] == symbolic_tools.MAX_SOLVER_TIMEOUT_MS
    assert z3_schema["properties"]["rlimit"]["maximum"] == symbolic_tools.MAX_SOLVER_RLIMIT
    assert "evil" not in symbolic_tools.PERMITTED_SYMPY_FUNCTIONS
