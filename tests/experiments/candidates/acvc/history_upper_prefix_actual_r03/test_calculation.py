"""Adapter and rule tests; no actual B4 computation."""
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys

from experiments.candidates.acvc.history_upper_prefix_actual_r03.calculation import (
    BUDGETS, CELLS, DUAL, REFERENCES, branch, load_inputs, profile,
    result_payload, serialize, synthetic_inputs,
)


def fixture(path):
    # Deliberately synthetic p and weights. Decimals are poisoned to prove they
    # cannot accidentally enter exact coefficient construction.
    def field(value):
        return {"numerator": value.numerator, "denominator": value.denominator, "decimal": "NOT AN INPUT"}
    cells = []
    for index, key in enumerate(CELLS):
        p = F(1 + index % 3, 5)
        coefficients = (("EXECUTE", 1-5*p, p, F(0)),
                        ("PROBE", F(2, 5)-p, F(0), F(3, 5)*(1-p)),
                        ("VETO", F(0), F(0), 1-p))
        cells.append({"cell": key, "weight": field(F(1, 24)), "unsafe_probability": field(p),
                      "actions": [{"action": name, "gain": field(g), "unsafe_numerator": field(u),
                                   "clean_loss_numerator": field(l)} for name, g, u, l in coefficients]})
    source = {"REGIME-ORACLE-ENVELOPE": {"coefficient_table": list(reversed(cells)),
              "dual": {name: field(value) for name, value in zip(("unsafe_multiplier", "clean_loss_multiplier"), DUAL)},
              "primal": {name: field(value) for name, value in zip(("unsafe_cap", "clean_loss_cap"), BUDGETS)}},
              "primary": {name: field(REFERENCES[key]) for name, key in
                          (("J_D", "J_D"), ("J_L", "J_L"), ("J_U", "J_U_R02"))}}
    path.write_text(json.dumps(source), encoding="utf-8")
    return source


def test_adapter_exact_order_native_formulas_and_profile(tmp_path):
    path = tmp_path / "fixture.json"
    fixture(path)
    inputs, facts = load_inputs(path)
    atoms, contexts, scores, dual, budgets = inputs
    assert facts["source_facts_match"] and facts["profile"]["within_actual_range"]
    assert facts["cell_mapping"][0]["source_index"] == 23
    assert atoms[0][:2] == (F(1, 15), F(1, 60))
    assert contexts[0][0] == F(1, 12)
    assert scores[0][0] == (-F(38, 1175), F(1, 5), F(0))
    assert dual == DUAL and budgets == BUDGETS
    assert facts["profile"]["fraction_count"] == 150
    assert {key: value["count"] for key, value in facts["profile"]["families"].items()} == {
        "atoms": 48, "marginals": 24, "scores": 72, "multipliers": 2, "budgets": 2, "priors": 2}
    assert all(sum(row) == 1 for row in atoms + contexts)
    source = fixture(path)
    source["REGIME-ORACLE-ENVELOPE"]["coefficient_table"][0]["actions"][0]["gain"]["numerator"] += 1
    path.write_text(json.dumps(source))
    assert not load_inputs(path)[1]["native_coefficients_match"]


def test_profile_family_and_ordered_rule():
    inputs = synthetic_inputs(375000)
    atoms, contexts, scores, dual, budgets = inputs
    assert all(sum(row) == 1 and all(x > 0 for x in row) for row in atoms + contexts)
    assert all(x > 0 for x in dual + budgets)
    assert profile(inputs)["fraction_count"] == 150
    assert 375000 % profile(inputs)["D_star"] == 0
    assert inputs == synthetic_inputs(375000)
    # These hand-selected numbers test branch algebra, never the actual kernel.
    assert branch(REFERENCES["J_L"] - 1) == "INTEGRITY_DISCREPANCY"
    assert branch(REFERENCES["J_U_R02"] + 1) == "INTEGRITY_DISCREPANCY"
    assert branch(REFERENCES["J_D"] + F(1, 4)) .startswith("HC-D")
    assert branch(REFERENCES["J_D"] + F(1, 4) - F(1, 10000)).startswith("HC-C")
    payload = result_payload(F(7, 3), inputs, {}, synthetic=True)
    restored = json.loads(serialize(payload))
    assert restored["primary"]["B4"]["numerator"] == 7
    assert restored["primary"]["B4"]["denominator"] == 3
    assert restored["branch"] == "SYNTHETIC_SERIALIZATION_ONLY"
    assert restored["inequalities"] == {}
    assert restored["primary"]["J_D"]["numerator"] == 0


def test_one_synthetic_publication_smoke(tmp_path):
    path = tmp_path / "fixture.json"
    fixture(path)
    admission = tmp_path / "admission.json"
    admission.write_text('{"test_fixture": true}')
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "output"
    run = subprocess.run([sys.executable, str(root / "scripts/run_acvc_history_upper_prefix_actual_r03.py"),
        "--mode", "profile-cost", "--smoke", "--input", str(path), "--out", str(output),
        "--source-sha", "synthetic-test", "--admission", str(admission)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    summary = json.loads((output / "summary.json").read_text())
    assert summary["complete"] and summary["status"] == "complete"
    assert summary["static_counts"]["histories"] == 3
    assert summary["actual_profile"]["fraction_count"] == 150
    assert summary["resources"]["wall_seconds"] > 0 and summary["resources"]["peak_rss_bytes"] > 0
    assert "primary" not in summary and "branch" not in summary and "inequalities" not in summary
