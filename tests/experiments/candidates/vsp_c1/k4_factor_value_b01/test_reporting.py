"""No model construction, RNG, environment or learning exposure in this profile."""
import ast
from pathlib import Path

import pytest

from experiments.candidates.vsp_c1.k4_factor_value_b01.reporting import curve_metrics, write_read

ROOT = Path(__file__).resolve().parents[5]


def test_prespecified_auc_preserves_adverse_and_initial_values():
    curve = [{"update": 16 * i, "mean_return": 1 - i / 8} for i in range(9)]
    assert curve_metrics(curve) == {"initial_return": 1, "final_return": 0,
                                    "learning_gain": -1, "normalized_auc": 0.5}


def test_primary_json_roundtrip(tmp_path):
    payload = {"arm": "GENERIC", "status": "incomplete", "curve": [],
               "primary_dependency_defects": ["missing primary measurement"]}
    assert write_read(tmp_path / "summary.json", payload) == payload
    with pytest.raises(ValueError):
        write_read(tmp_path / "invalid.json", {"return": float("nan")})


def test_source_parses_without_executing_scientific_path():
    paths = [ROOT / "scripts/run_vspc1_k4_factor_value_b01.py"]
    paths += list((ROOT / "experiments/candidates/vsp_c1/k4_factor_value_b01").glob("*.py"))
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_card_arithmetic_without_a_model_or_rollout():
    assert (6 * 16 + 16) + (16 * 4 + 4) + 2 * 4 == 188
    assert (8 * 19 + 19) + (19 + 1) == 191
    assert (16 * 3 + 16) * 128 == 8192
    assert 32 * 128 * 6 + 9 * 8 * 6 == 25008
    assert 48 * (2 / (6 * 32)) == 16 * (6 / (6 * 32)) == 0.5
