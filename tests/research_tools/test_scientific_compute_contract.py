from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from hypothesis import strategies as st

from tools.research.scientific_compute import (
    ArrayContract,
    ComparisonContract,
    PropertyTestContract,
    ToleranceContract,
    compare_arrays,
    find_counterexample,
)
from tools.research.scientific_compute.contracts import InfPolicy, NanPolicy, SignedZeroPolicy


ROOT = Path(__file__).resolve().parents[2]


def _array_contract(
    *,
    dtype: str = "float64",
    shape: tuple[int, ...] = (2,),
    nan_policy: NanPolicy = "forbid",
    inf_policy: InfPolicy = "forbid",
    signed_zero_policy: SignedZeroPolicy = "distinguish",
) -> ArrayContract:
    return ArrayContract(
        dtype=dtype,
        shape=shape,
        order="C",
        nan_policy=nan_policy,
        inf_policy=inf_policy,
        signed_zero_policy=signed_zero_policy,
        units="dimensionless",
        device="cpu",
    )


def _exact_contract(*, array: ArrayContract | None = None) -> ComparisonContract:
    return ComparisonContract(
        mode="exact",
        array=array or _array_contract(),
        oracle="recorded reference array",
        algorithm="boundary-fixture",
        algorithm_version="1",
    )


def _approximate_contract(
    *,
    atol: float,
    rtol: float = 0.0,
    array: ArrayContract | None = None,
) -> ComparisonContract:
    return ComparisonContract(
        mode="approximate",
        array=array or _array_contract(signed_zero_policy="equal"),
        oracle="recorded reference array",
        algorithm="boundary-fixture",
        algorithm_version="1",
        tolerance=ToleranceContract(
            atol=atol,
            rtol=rtol,
            justification="Bounded fixture perturbation from the frozen protocol.",
        ),
    )


def _checks(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {check["name"]: check for check in result["checks"]}


def test_exact_mode_detects_byte_mismatch_including_signed_zero() -> None:
    expected = np.array([0.0, 1.0], dtype=np.float64)
    actual = np.array([-0.0, 1.0], dtype=np.float64)

    result = compare_arrays(expected, actual, _exact_contract())

    assert result["ok"] is False
    assert result["status"] == "MISMATCH"
    assert _checks(result)["values.signed_zero_policy"]["ok"] is False
    assert _checks(result)["values.exact_canonical_bytes"]["ok"] is False
    assert result["expected"]["canonical_sha256"] != result["actual"]["canonical_sha256"]
    assert result["contract"]["tolerance"] is None


def test_approximate_mode_has_explicit_bounded_pass_and_fail() -> None:
    expected = np.array([10.0, -2.0], dtype=np.float64)
    passing = np.array([10.09, -2.09], dtype=np.float64)
    failing = np.array([10.11, -2.0], dtype=np.float64)
    contract = _approximate_contract(atol=0.1)

    passed = compare_arrays(expected, passing, contract)
    failed = compare_arrays(expected, failing, contract)

    assert passed["ok"] is True
    assert failed["ok"] is False
    assert _checks(passed)["values.approximate"]["expected"]["formula"] == (
        "abs(actual - expected) <= atol + rtol * abs(expected)"
    )
    assert _checks(failed)["values.approximate"]["details"]["max_abs_error"] == pytest.approx(0.11)
    with pytest.raises(ValueError, match="requires an explicit ToleranceContract"):
        ComparisonContract(
            mode="approximate",
            array=_array_contract(signed_zero_policy="equal"),
            oracle="fixture",
            algorithm="fixture",
            algorithm_version="1",
        )


def test_dtype_and_shape_mismatches_are_separate_contract_failures() -> None:
    expected = np.array([1.0, 2.0], dtype=np.float64)
    wrong_dtype = np.array([1.0, 2.0], dtype=np.float32)
    wrong_shape = np.array([[1.0, 2.0]], dtype=np.float64)
    contract = _exact_contract()

    dtype_result = compare_arrays(expected, wrong_dtype, contract)
    shape_result = compare_arrays(expected, wrong_shape, contract)

    assert _checks(dtype_result)["actual.dtype"]["ok"] is False
    assert _checks(dtype_result)["actual.shape"]["ok"] is True
    assert _checks(shape_result)["actual.shape"]["ok"] is False
    assert _checks(shape_result)["actual.dtype"]["ok"] is True
    assert _checks(shape_result)["values.exact_canonical_bytes"]["ok"] is False


@pytest.mark.parametrize(
    ("nan_policy", "actual", "expected_ok"),
    [
        ("equal", np.array([np.nan, 1.05]), True),
        ("unequal", np.array([np.nan, 1.05]), False),
        ("forbid", np.array([np.nan, 1.05]), False),
        ("equal", np.array([0.0, 1.05]), False),
    ],
)
def test_nan_policy_is_explicit(nan_policy: NanPolicy, actual: np.ndarray, expected_ok: bool) -> None:
    expected = np.array([np.nan, 1.0], dtype=np.float64)
    array = _array_contract(nan_policy=nan_policy, signed_zero_policy="equal")

    result = compare_arrays(expected, actual, _approximate_contract(atol=0.1, array=array))

    assert result["ok"] is expected_ok
    assert result["contract"]["array"]["nan_policy"] == nan_policy


def _property_contract() -> PropertyTestContract:
    return PropertyTestContract(
        property_id="successor-square-boundary",
        property_description="(x + 1)^2 remains at most 25",
        generator_domain={"x": {"integer_max": 100, "integer_min": 0}},
        filters=(),
        explicit_examples=({"x": 0}, {"x": 4}),
        seed=90210,
        profile_name="boundary-search-v1",
        max_examples=200,
        deadline_ms=None,
        phases=("generate", "shrink"),
        suppress_health_checks=(),
        report_multiple_bugs=False,
    )


def test_fixed_seed_replay_metadata_records_complete_profile() -> None:
    contract = _property_contract()

    first = contract.replay_metadata(minimal_counterexample=5)
    second = contract.replay_metadata(minimal_counterexample=5)

    assert first == second
    assert first["replay"]["seed"] == 90210
    assert first["replay"]["seed_decorator"] == "@hypothesis.seed(90210)"
    assert first["profile"] == {
        "database": None,
        "deadline_ms": None,
        "explicit_examples": [{"x": 0}, {"x": 4}],
        "filters": [],
        "max_examples": 200,
        "name": "boundary-search-v1",
        "phases": ["generate", "shrink"],
        "report_multiple_bugs": False,
        "suppress_health_checks": [],
    }
    assert first["hypothesis_version"]
    assert "not a proof" in first["limitations"][1]


def _violates_successor_square(x: int) -> bool:
    return (x + 1) ** 2 > 25


def test_hypothesis_discovers_and_shrinks_real_boundary_case() -> None:
    artifact = find_counterexample(
        _property_contract(),
        st.integers(min_value=0, max_value=100),
        _violates_successor_square,
    )

    assert artifact.value == 5
    assert artifact.metadata["counterexample"] == 5
    assert artifact.metadata["property_id"] == "successor-square-boundary"
    assert artifact.metadata["search_execution"] == {
        "api": "hypothesis.find",
        "explicit_examples_applied": False,
        "health_checks": "all suppressed internally by hypothesis.find",
        "report_multiple_bugs": False,
    }


def test_cli_emits_deterministic_json_with_visible_exact_contract(tmp_path: Path) -> None:
    expected_path = tmp_path / "expected.npy"
    actual_path = tmp_path / "actual.npy"
    np.save(expected_path, np.array([1.0, 2.0], dtype=np.float64))
    np.save(actual_path, np.array([1.0, 2.0], dtype=np.float64))
    command = [
        sys.executable,
        "-m",
        "tools.research.scientific_compute",
        "compare",
        "--expected",
        str(expected_path),
        "--actual",
        str(actual_path),
        "--mode",
        "exact",
        "--dtype",
        "float64",
        "--shape",
        "2",
        "--order",
        "C",
        "--nan-policy",
        "forbid",
        "--inf-policy",
        "forbid",
        "--signed-zero-policy",
        "distinguish",
        "--units",
        "dimensionless",
        "--device",
        "cpu",
        "--oracle",
        "recorded-fixture",
        "--algorithm",
        "fixture",
        "--algorithm-version",
        "1",
    ]

    first = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    second = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert result["schema_version"] == 1
    assert result["ok"] is True
    assert result["contract"]["mode"] == "exact"
    assert result["contract"]["tolerance"] is None
