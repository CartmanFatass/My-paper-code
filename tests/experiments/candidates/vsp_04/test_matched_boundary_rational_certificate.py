from __future__ import annotations

import itertools
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
from pathlib import Path

import pytest

from experiments.candidates.vsp_04 import matched_boundary_rational_certificate as cert


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "experiments/candidates/vsp_04/matched_boundary_rational_certificate.py"
INDEX = ROOT / "docs/research/legacy/directions/vsp_04/CODE_SCIENCE_INDEX.md"


def test_primary_exact_a_b_and_fixed_instance() -> None:
    assert cert.PRIMARY_SYSTEM.cells == ("w0", "w1", "w2")
    assert cert.OMEGA == (F(1, 4), F(1, 2), F(1, 4))
    assert cert.P_H == F(1, 2)
    expected = (
        ((F(1, 4), F(1, 2), F(1, 4)), F(1, 2)),
        ((F(1, 4), F(0), F(0)), F(1, 8)),
        ((F(0), F(0), F(1, 4)), F(1, 8)),
        ((F(0), F(1, 2), F(0)), F(1, 4)),
        ((F(1, 4), F(0), F(1, 4)), F(1, 4)),
        ((F(1, 4), F(0), F(0)), F(1, 8)),
        ((F(0), F(0), F(1, 4)), F(1, 8)),
        ((F(0), F(1, 2), F(0)), F(3, 8)),
        ((F(1, 4), F(0), F(1, 4)), F(1, 4)),
        ((F(1, 4), F(0), F(0)), F(1, 8)),
        ((F(0), F(0), F(1, 4)), F(1, 8)),
        ((F(1, 4), F(1, 2), F(0)), F(3, 8)),
        ((F(0), F(1, 2), F(1, 4)), F(3, 8)),
    )
    assert tuple((row.coefficients, row.target) for row in cert.PRIMARY_SYSTEM.rows) == expected


def test_immutable_ledger_and_excluded_u_rejection() -> None:
    cert.PRIMARY_LEDGER.validate()
    assert cert.PRIMARY_LEDGER.h == (cert.PRIMARY_LEDGER.x, cert.PRIMARY_LEDGER.m_minus)
    assert cert.PRIMARY_LEDGER.w == (cert.PRIMARY_LEDGER.h, cert.PRIMARY_LEDGER.g)
    with pytest.raises(FrozenInstanceError):
        cert.PRIMARY_LEDGER.g = ("changed",)
    leaked = replace(cert.PRIMARY_LEDGER, g=cert.PRIMARY_LEDGER.g + ("outcome_proxy",))
    with pytest.raises(ValueError, match="leaked"):
        leaked.validate()
    incomplete = replace(cert.PRIMARY_LEDGER, u=("source_private",))
    with pytest.raises(ValueError, match="transitively"):
        incomplete.validate()


def test_support_floor_positive_and_negative() -> None:
    cert.validate_support(cert.OMEGA, cert.P_H)
    with pytest.raises(ValueError, match="support floor"):
        cert.validate_support((F(1, 8), F(1, 2), F(3, 8)), F(1, 2))
    with pytest.raises(ValueError, match="propensity"):
        cert.validate_support(cert.OMEGA, F(1, 8))


def test_primary_has_no_witness_and_exact_sparse_dual() -> None:
    assert cert.solve_primal_vertices(cert.PRIMARY_SYSTEM) is None
    dual = cert.search_sparse_dual(cert.PRIMARY_SYSTEM)
    assert dual is not None
    assert dual.forcing_rows == ("IND.risk.ACK", "OR.risk.ACK")
    assert (dual.lhs, dual.rhs, dual.margin) == (F(1, 8), F(0), F(1, 8))
    assert cert.validate_dual(cert.PRIMARY_SYSTEM, dual.y) == dual


def test_deleting_or_ack_leaves_all_other_twelve_rows_feasible() -> None:
    without_or_ack = replace(
        cert.PRIMARY_SYSTEM,
        rows=tuple(row for row in cert.PRIMARY_SYSTEM.rows if row.name != "OR.risk.ACK"),
    )
    witness = cert.solve_primal_vertices(without_or_ack)
    assert witness == (F(1, 2), F(1, 2), F(1, 2))
    assert cert.validate_witness(without_or_ack, witness)
    assert cert.solve_primal_vertices(cert.PRIMARY_SYSTEM) is None
    dual = cert.search_sparse_dual(cert.PRIMARY_SYSTEM)
    assert dual is not None
    assert (dual.forcing_rows, dual.lhs, dual.rhs, dual.margin) == (
        ("IND.risk.ACK", "OR.risk.ACK"),
        F(1, 8),
        F(0),
        F(1, 8),
    )


def test_common_raw_plus_or_is_already_infeasible_with_explicit_forced_q() -> None:
    path_raw_names = {
        "COMMON.raw_propensity",
        "OR.path.timing_metadata",
        "OR.path.queue_retry_ack_cost",
    }
    path_raw = replace(cert.PRIMARY_SYSTEM, rows=tuple(row for row in cert.PRIMARY_ROWS if row.name in path_raw_names))
    assert cert.solve_primal_vertices(path_raw) == (F(1, 2), F(1, 2), F(1, 2))
    or_ack = next(row for row in cert.PRIMARY_ROWS if row.name == "OR.risk.ACK")
    assert or_ack.coefficients == (F(0), F(1, 2), F(0))
    assert or_ack.target / or_ack.coefficients[1] == F(3, 4)
    common_or = replace(cert.PRIMARY_SYSTEM, rows=tuple(row for row in cert.PRIMARY_ROWS if row.mode in ("COMMON", "OR")))
    assert cert.solve_primal_vertices(common_or) is None
    assert cert.literal_subsystem_diagnostics() == {
        "common_raw_plus_or": {
            "infeasible": True,
            "or_ack_forced_q1": "3/4",
            "path_raw_forced_q": ["1/2", "1/2", "1/2"],
        },
        "delete_or_risk_ack": {"remaining_rows": 12, "witness": ["1/2", "1/2", "1/2"]},
    }


def test_literal_subsystem_diagnostic_fails_closed_on_changed_declared_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = list(cert.PRIMARY_ROWS)
    rows[7] = replace(rows[7], target=F(1, 4))
    monkeypatch.setattr(cert, "PRIMARY_ROWS", tuple(rows))
    with pytest.raises(AssertionError, match=r"OR\.risk\.ACK equation changed"):
        cert.literal_subsystem_diagnostics()


def test_dual_rejected_after_forcing_target_or_coefficient_mutation() -> None:
    dual = cert.search_sparse_dual(cert.PRIMARY_SYSTEM)
    assert dual is not None
    rows = list(cert.PRIMARY_SYSTEM.rows)
    rows[7] = replace(rows[7], target=F(1, 4))
    with pytest.raises(ValueError, match="invalid"):
        cert.validate_dual(replace(cert.PRIMARY_SYSTEM, rows=tuple(rows)), dual.y)
    rows = list(cert.PRIMARY_SYSTEM.rows)
    rows[7] = replace(rows[7], coefficients=(F(0), F(1), F(1)))
    with pytest.raises(ValueError, match="invalid"):
        cert.validate_dual(replace(cert.PRIMARY_SYSTEM, rows=tuple(rows)), dual.y)


def test_solver_exercises_separately_named_feasible_and_infeasible_units() -> None:
    feasible = cert.solve_primal_vertices(cert.FEASIBLE_ENGINEERING_SYSTEM)
    assert cert.FEASIBLE_ENGINEERING_SYSTEM.name == "engineering_minimal_feasible"
    assert feasible == (F(1, 2), F(1, 2), F(1, 2))
    assert cert.validate_witness(cert.FEASIBLE_ENGINEERING_SYSTEM, feasible)
    assert cert.INFEASIBLE_ENGINEERING_SYSTEM.name == "engineering_minimal_infeasible"
    assert cert.solve_primal_vertices(cert.INFEASIBLE_ENGINEERING_SYSTEM) is None
    dual = cert.search_sparse_dual(cert.INFEASIBLE_ENGINEERING_SYSTEM)
    assert dual is not None and dual.margin == F(1, 2)


def test_full_path_action_row_inventory_and_conflict() -> None:
    assert cert.row_inventory(cert.PRIMARY_SYSTEM) == {
        "action_risk": {"IND": 2, "OR": 2, "SOFT": 2},
        "path": {"IND": 2, "OR": 2, "SOFT": 2},
        "raw": 1,
        "total": 13,
    }
    ind, or_row = (next(row for row in cert.PRIMARY_ROWS if row.name == name) for name in ("IND.risk.ACK", "OR.risk.ACK"))
    expected = tuple(weight * feature for weight, feature in zip(cert.OMEGA, cert.ACK_FEATURE))
    assert cert.ACK_FEATURE == (F(0), F(1), F(0))
    assert cert.WEIGHTED_ACK_COEFFICIENT == expected == (F(0), F(1, 2), F(0))
    assert ind.coefficients == or_row.coefficients == expected
    assert (ind.target, or_row.target, or_row.target - ind.target) == (F(1, 4), F(3, 8), F(1, 8))


def test_all_mode_label_permutations_preserve_infeasibility_and_margin() -> None:
    for labels in itertools.permutations(cert.MODES):
        permuted = cert.permute_mode_labels(cert.PRIMARY_SYSTEM, dict(zip(cert.MODES, labels)))
        assert cert.solve_primal_vertices(permuted) is None
        dual = cert.search_sparse_dual(permuted)
        assert dual is not None and dual.margin == F(1, 8)


def test_timing_metadata_queue_retry_ack_cost_recurrent_and_shadow_invariance() -> None:
    cert.validate_frozen_contract()
    assert tuple(name for name, _ in cert.INTERFACE_TABLES) == ("timing", "metadata", "queue", "retry", "ack", "cost")
    assert cert.FROZEN_POLICY[-1] == "fixed"
    assert cert.FROZEN_RECURRENT == ("hidden", F(2, 5), "cell", F(-1, 7))
    assert all(signature[1:] == cert.SHADOW_SIGNATURES[0][1:] for signature in cert.SHADOW_SIGNATURES)
    assert {(mode, action) for mode, action, _, _ in cert.FULL_ASYMMETRIC_LOSSES} == set(itertools.product(cert.MODES, cert.LEGAL_ACTIONS))


def test_finite_rational_tape_and_exact_threshold_rule() -> None:
    assert cert.TAPE == (F(0), F(1, 4), F(1, 2), F(3, 4))
    assert all(isinstance(value, F) and F(0) <= value <= F(1) for value in cert.TAPE)
    q = cert.solve_primal_vertices(cert.FEASIBLE_ENGINEERING_SYSTEM)
    assert q is not None
    assert [int(value <= q[0]) for value in cert.TAPE] == [1, 1, 1, 0]


def test_feasible_unit_exhaustive_tk_zero_and_a0_u_independence() -> None:
    q = cert.solve_primal_vertices(cert.FEASIBLE_ENGINEERING_SYSTEM)
    assert q is not None
    checks = cert.paired_tk_a0_checks(q, cert.FEASIBLE_ENGINEERING_SYSTEM)
    assert checks == {"a0_u_independent": True, "comparisons": 72, "delta_tk": "0", "finite_tape_size": 4}


def test_no_post_result_feature_adaptation() -> None:
    cert.validate_feature_transition(cert.FEATURE_SNAPSHOT, cert.FEATURE_SNAPSHOT, True)
    cert.validate_feature_transition(cert.FEATURE_SNAPSHOT, ("replacement",), False)
    with pytest.raises(ValueError, match="forbidden"):
        cert.validate_feature_transition(cert.FEATURE_SNAPSHOT, cert.FEATURE_SNAPSHOT + ("outcome_proxy",), True)


def _run_cli() -> bytes:
    return subprocess.run([sys.executable, "-B", str(SOURCE)], cwd=ROOT, check=True, capture_output=True).stdout


def test_cli_is_byte_stable_compact_sorted_json_and_narrow() -> None:
    first = _run_cli()
    second = _run_cli()
    assert first == second
    payload = json.loads(first)
    assert first == (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert payload["conclusion"] == "literal stacked PRIMARY_ROWS matrix is set-theoretically infeasible"
    assert payload["primary"]["witness"] is None
    assert payload["primary"]["table_scope"] == {
        "declared_finite_table": True,
        "marginally_validated_by_lower_level_objects": False,
        "mechanically_generated_from_lower_level_objects": False,
    }
    assert payload["literal_subsystems"]["common_raw_plus_or"] == {
        "infeasible": True,
        "or_ack_forced_q1": "3/4",
        "path_raw_forced_q": ["1/2", "1/2", "1/2"],
    }
    assert payload["literal_subsystems"]["delete_or_risk_ack"] == {
        "remaining_rows": 12,
        "witness": ["1/2", "1/2", "1/2"],
    }
    assert payload["engineering_units"]["scope"] == "solver_checks_only"
    assert payload["engineering_units"]["does_not_repair"] == ["coherence", "provenance", "exact Bernoulli calibration"]
    assert payload["certificate"]["margin"] == "1/8"


def test_code_science_index_binds_exact_raw_cli_output_and_nonclaims() -> None:
    text = INDEX.read_text(encoding="utf-8")
    bound = text.split("```json\n", 1)[1].split("\n```", 1)[0].encode() + b"\n"
    assert bound == _run_cli()
    for nonclaim in (
        "authentic-request value",
        "cellwise H/W/U ancestry",
        "coherent IND/OR/SOFT matched-boundary triad",
        "cross-mode shared-K obstruction",
        "exact Bernoulli calibration",
        "generator-safe semantic binding",
        "lower-level path/risk provenance",
        "matched-carrier independence",
        "training benefit",
        "return",
        "causality",
        "deployment",
        "universal impossibility",
    ):
        assert nonclaim in text
    assert "path/raw rows force `q=(1/2,1/2,1/2)`" in text
    assert "`OR.risk.ACK` forces `q1=3/4`" in text
    assert "deleting `OR.risk.ACK` leaves all other 12 rows feasible" in text
