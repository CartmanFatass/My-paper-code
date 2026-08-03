from __future__ import annotations

import ast
from copy import deepcopy
import inspect
from pathlib import Path
import subprocess

import pytest

from ha_ctse_process import event_commitment_replay_evidence
from ha_ctse_process.noncalendar_commitment_testbed import (
    EVENT_JOINT_FACTOR_COUNT,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    REPLAY_LOG_COMPONENT_ATOL,
    REPLAY_LOG_COMPONENT_RTOL,
    REPLAY_LOG_RATIO_DRIFT_CAP,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_STATE_ATOL,
    float32_reduction_gamma,
)
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


BASE_COMMIT = "bddb4311227741139c00c0a51ac7b1f3e4358caf"
MOVED_NAMES = {
    "_finite_leaves",
    "_record_severity",
    "merge_replay_records",
    "_consistent",
    "_joint_factor_error_cap",
    "_ordered_float32_encoding",
    "_recompute_ulp",
    "_likelihood_record_valid",
    "_replay_record_valid",
}


def _function_node(source: str, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _synthetic_replay_record() -> dict[str, object]:
    def joint(factor_count: float, magnitude: float) -> dict[str, float]:
        allowance = float(float32_reduction_gamma(factor_count) * magnitude)
        return {
            "error": 0.0,
            "component_sum": 0.0,
            "allowance": allowance,
            "bound": allowance,
            "excess": -allowance,
            "factor_count": factor_count,
            "float64_error": 0.0,
            "assembly_residual": 0.0,
            "assembly_allowance": allowance,
            "assembly_excess": -allowance,
            "rows": 1280.0,
        }

    def worst(dimensions: int) -> dict[str, object]:
        spacing, distance = event_commitment_replay_evidence._recompute_ulp(0.0, 0.0)
        return {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "absolute_error": 0.0,
            "mixed_bound": REPLAY_LOG_COMPONENT_ATOL,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "float32_ulp_at_max_magnitude": spacing,
            "ulp_distance": distance,
            "coordinate": [0] * dimensions,
        }

    return {
        "schema_version": REPLAY_RECORD_SCHEMA_VERSION,
        "errors": {
            name: 0.0
            for name in (
                REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
            )
        },
        "joints": {
            "primitive_joint": joint(3.0, 12.0),
            "event_joint": joint(float(EVENT_JOINT_FACTOR_COUNT), 16.0),
        },
        "likelihood_components": {
            "primitive_component": worst(3),
            "categorical_component": worst(3),
            "mark_component": worst(4),
        },
        "event_joint_ratio": {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "coordinate": [0, 0, 0],
        },
        "log_component_atol": REPLAY_LOG_COMPONENT_ATOL,
        "log_component_rtol": REPLAY_LOG_COMPONENT_RTOL,
        "ratio_drift_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "state_atol": REPLAY_STATE_ATOL,
        "failures": [],
        "passed": True,
    }


def test_replay_evidence_has_one_true_owner_without_reverse_edge_or_aliases() -> None:
    evidence_source = inspect.getsource(event_commitment_replay_evidence)
    runner_source = inspect.getsource(benchmark_runner)
    evidence_tree = ast.parse(evidence_source)
    runner_tree = ast.parse(runner_source)
    evidence_definitions = {
        node.name for node in evidence_tree.body if isinstance(node, ast.FunctionDef)
    }
    runner_definitions = {
        node.name for node in runner_tree.body if isinstance(node, ast.FunctionDef)
    }
    evidence_imports = {
        node.module
        for node in ast.walk(evidence_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    evidence_imports.update(
        alias.name
        for node in ast.walk(evidence_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert MOVED_NAMES <= evidence_definitions
    assert not MOVED_NAMES & runner_definitions
    assert "scripts.run_noncalendar_commitment_benchmark_g0" not in evidence_imports
    assert all(not hasattr(benchmark_runner, name) for name in MOVED_NAMES)

    bare_calls = {
        node.func.id
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in MOVED_NAMES
    }
    replay_validator_calls = [
        node
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "event_commitment_replay_evidence"
        and node.func.attr == "_replay_record_valid"
    ]
    assert not bare_calls
    assert len(replay_validator_calls) == 3
    assert benchmark_runner.event_commitment_replay_evidence is (
        event_commitment_replay_evidence
    )


def test_moved_replay_evidence_definitions_match_the_ticket_base_ast() -> None:
    repository = Path(__file__).resolve().parents[1]
    base_source = subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "show",
            f"{BASE_COMMIT}:scripts/run_noncalendar_commitment_benchmark_g0.py",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    evidence_source = inspect.getsource(event_commitment_replay_evidence)

    for name in MOVED_NAMES:
        expected = _function_node(base_source, name)
        actual = _function_node(evidence_source, name)
        assert ast.dump(actual, include_attributes=False) == ast.dump(
            expected, include_attributes=False
        ), name


def test_merge_preserves_factorwise_records_and_fails_closed_on_nonfinite() -> None:
    left = _synthetic_replay_record()
    right = deepcopy(left)
    right["errors"]["mark_component"] = 7e-7
    right["errors"]["event_joint"] = 3e-6
    allowance = float(right["joints"]["event_joint"]["allowance"])
    bound = 2e-6 + allowance
    right["joints"]["event_joint"] |= {
        "error": 3e-6,
        "component_sum": 2e-6,
        "bound": bound,
        "excess": 3e-6 - bound,
        "rows": 600.0,
    }

    merged = event_commitment_replay_evidence.merge_replay_records([left, right])
    assert merged["errors"]["mark_component"] == 7e-7
    assert merged["errors"]["event_joint"] == 3e-6
    assert merged["joints"]["event_joint"]["error"] == 3e-6
    assert merged["joints"]["event_joint"]["bound"] == bound
    assert merged["joints"]["event_joint"]["rows"] == 1880.0
    assert event_commitment_replay_evidence._replay_record_valid(merged)

    degraded = deepcopy(left)
    degraded["errors"]["mark_component"] = float("nan")
    for ordered in ([left, degraded], [degraded, left]):
        with pytest.raises(ValueError, match="non-finite"):
            event_commitment_replay_evidence.merge_replay_records(ordered)


def test_validator_rederives_schema_likelihood_and_joint_invariants() -> None:
    clean = _synthetic_replay_record()
    assert event_commitment_replay_evidence._replay_record_valid(clean)
    with pytest.raises(ValueError, match="at least one"):
        event_commitment_replay_evidence.merge_replay_records([])

    truncated = deepcopy(clean)
    truncated["joints"]["event_joint"] = {
        key: clean["joints"]["event_joint"][key]
        for key in ("excess", "assembly_excess", "bound")
    }
    assert not event_commitment_replay_evidence._replay_record_valid(truncated)
    assert set(clean["joints"]["event_joint"]) == set(REPLAY_JOINT_RECORD_FIELDS)

    wrong_ulp = deepcopy(clean)
    wrong_ulp["likelihood_components"]["mark_component"]["ulp_distance"] += 1
    assert not event_commitment_replay_evidence._replay_record_valid(wrong_ulp)

    unsupported_bound = deepcopy(clean)
    unsupported_bound["errors"]["event_joint"] = 1e9
    unsupported_bound["joints"]["event_joint"] |= {
        "error": 1e9,
        "component_sum": 1e10,
        "bound": 1e10,
        "excess": -9e9,
    }
    assert not event_commitment_replay_evidence._replay_record_valid(
        unsupported_bound
    )

    ordinary = deepcopy(clean)
    ordinary["joints"]["event_joint"] = {
        key: 0.0 for key in REPLAY_JOINT_RECORD_FIELDS
    }
    assert not event_commitment_replay_evidence._replay_record_valid(ordinary)
    assert event_commitment_replay_evidence._replay_record_valid(
        ordinary, event_rows_required=False
    )
