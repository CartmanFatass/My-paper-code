from __future__ import annotations

import ctypes
from pathlib import Path

import pytest

from experiments.candidates.voronoi_quadrature_field_policy_r05_measurement.contracts import (
    ANALYTIC_STATE_COUNT,
    Q_E,
    TEST_NAMESPACE,
    WIDTH_SWEEP,
    require_test_namespace,
)
from experiments.candidates.voronoi_quadrature_field_policy_r05_measurement.fixtures import (
    analytic_states,
    numeric_batch,
    synthetic_chain_fixtures,
)
from experiments.candidates.voronoi_quadrature_field_policy_r05_measurement.lifecycle import (
    publish_frontier,
    restore_frontier,
)
from experiments.candidates.voronoi_quadrature_field_policy_r05_measurement.measurement import (
    _records_digest,
    _solve_rows,
)
from experiments.candidates.voronoi_quadrature_field_policy_r05_measurement.native_backend import (
    AnalyticResult,
    AnalyticState,
    CheckResult,
    require_native_pair,
    run_numeric_batch,
    solve_analytic_batch,
)


def test_fixture_inventory_is_exact_and_balanced() -> None:
    rows = analytic_states()
    assert len(rows) == ANALYTIC_STATE_COUNT
    assert {int(row.n_agents) for row in rows} == {4, 6, 8, 12}
    assert {int(row.kind) for row in rows} == set(range(8))
    assert all(int(row.q_e) == Q_E for row in rows)
    assert all(
        sum(int(row.n_agents) == n and int(row.kind) == kind for row in rows) == 128
        for n in (4, 6, 8, 12)
        for kind in range(8)
    )
    chain = synthetic_chain_fixtures()
    assert len(chain) == 32
    assert all(row.namespace == TEST_NAMESPACE for row in chain)
    assert {row.analyzer_branch_fixture for row in chain} == set(range(1, 16))


def test_numeric_certificates_pass_every_registered_width() -> None:
    for width in WIDTH_SWEEP:
        output = run_numeric_batch(numeric_batch(width))
        assert len(output) == width
        assert all(result.evaluated == 1 and result.exact_match == 1 for result in output)


def test_analytic_solver_checker_is_exact_across_widths() -> None:
    rows = analytic_states()
    baseline = _solve_rows(rows, 1)
    assert len(baseline) == ANALYTIC_STATE_COUNT
    assert all(record[-1] == 1 for record in baseline)
    for width in WIDTH_SWEEP[1:]:
        observed = _solve_rows(rows, width)
        assert observed == baseline
        assert _records_digest(observed) == _records_digest(baseline)


def test_independent_checker_rejects_tampered_allocation() -> None:
    state = analytic_states()[0]
    result = solve_analytic_batch((state,))[0]
    result.counts[0] -= 1
    result.counts[1] += 1
    _, checker = require_native_pair()
    inputs = (AnalyticState * 1)(state)
    outputs = (AnalyticResult * 1)(result)
    checks = (CheckResult * 1)()
    assert checker.vqfp_r05_check_analytic_batch(inputs, outputs, 1, checks) == 0
    assert checks[0].accepted == 0


def test_test_namespace_and_atomic_resume_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        require_test_namespace("VQFPFERL05")
    payload = {
        "namespace": TEST_NAMESPACE,
        "generation": 0,
        "scientific_output": False,
    }
    publish_frontier(tmp_path, 0, payload)
    restored = restore_frontier(tmp_path)
    assert restored["payload"] == payload
    with pytest.raises(FileExistsError):
        publish_frontier(tmp_path, 0, payload)

