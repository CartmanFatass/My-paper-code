"""Toy publication and frozen timing/reference arithmetic, never census evidence."""
import importlib.util
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / "scripts/run_flexible_skill_duration_e4_census.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("e4_census_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def arguments(output, mode="census", law="deterministic"):
    return [str(SCRIPT), "--law", law, "--mode", mode, "--horizon", "41",
            "--seed", "0", "--launch-sha", "toy-source", "--node", "toy-node",
            "--output", str(output)]


def test_toy_cli_full_publication(tmp_path):
    output = tmp_path / "summary.json"
    completed = subprocess.run([sys.executable, *arguments(output)], cwd=ROOT,
                               capture_output=True, text=True, timeout=60, check=True)
    summary = json.loads(output.read_text())
    assert summary["status"] == "COMPLETE" and summary["toy"] is True
    assert summary["launch_sha"] == "toy-source" and summary["seed_active"] is False
    assert summary["learner_exposure"] == dict(episodes=0, transitions=0, optimizer_updates=0, checkpoint_selection=0)
    assert summary["config"]["event_process"] == "renewal"
    assert summary["law"]["mean"] == 20 and summary["law"]["variance"] == 0
    assert summary["law"]["hazard"] == [0.0] * 19 + [1.0]
    rows = summary["open_candidates"]
    expected = {(zone_map, period) for zone_map in product(range(2), repeat=4)
                for period in (1, 2, 5, 20, 40, None)}
    assert len(rows) == summary["open_candidate_count"] == 96
    assert {(tuple(row[0]), row[1]) for row in rows} == expected
    best = max(rows, key=lambda row: row[2])
    assert summary["best_open_candidate"] == best[:2]
    assert summary["J_open_best"] == best[2]
    assert summary["J_switch"] == pytest.approx(0.4 * 39 / 41, abs=1e-10)
    assert summary["J_greedy"] == summary["J_switch"]
    assert summary["J_fixed_k"]["20"] == pytest.approx(summary["J_switch"], abs=1e-10)
    assert summary["J_best_fixed_k"] == max(summary["J_fixed_k"].values())
    assert summary["m"] == summary["J_switch"] - best[2]
    assert summary["m_dur"] == summary["J_switch"] - summary["J_best_fixed_k"]
    assert summary["fixed_improvement_over_k20"] == summary["J_best_fixed_k"] - summary["J_fixed_k"]["20"]
    for key, ordering in summary["gap_ordering"].items():
        value = summary[key]
        assert ordering == ("positive" if value > 1e-10 else "opposite" if value < -1e-10 else "unresolved")
    assert json.loads(completed.stdout)["output_seconds"] >= 0


def test_calibration_calls_and_projection(monkeypatch, tmp_path):
    runner = load_runner()
    calls = []

    def fake_dp(hazard, horizon, roles, **kwargs):
        calls.append((hazard.copy(), horizon, roles, kwargs))
        return np.zeros(horizon)

    output = tmp_path / "calibration.json"
    monkeypatch.setattr(runner, "dp_service_profile", fake_dp)
    monkeypatch.setattr(sys, "argv", arguments(output, "calibration"))
    runner.main()
    summary = json.loads(output.read_text())
    assert len(calls) == 6
    assert calls[0][3] == {"renew_on_flag": True}
    assert [(row[3]["stamp"], list(row[3]["boundaries"])) for row in calls[1:]] == [
        ("oracle", list(range(1, 41))), ("oracle", [40]),
        ("open", list(range(1, 41))), ("open", [40]), ("open", [])]
    assert all(row[1:3] == (41, 2) for row in calls)
    assert summary["projection_seconds"] == 2 * (summary["cold_seconds"] + 36 * max(summary["dp_seconds"].values()))
    assert "J_switch" not in summary


def test_nonfinite_calibration_is_incomplete(monkeypatch, tmp_path):
    runner = load_runner()
    output = tmp_path / "incomplete.json"
    monkeypatch.setattr(sys, "argv", arguments(output, "calibration"))
    monkeypatch.setattr(runner, "dp_service_profile", lambda *args, **kwargs: np.array([np.nan]))
    with pytest.raises(AssertionError, match="nonfinite calibration DP"):
        runner.main()
    assert not output.exists()


def test_missing_candidate_is_incomplete(monkeypatch, tmp_path):
    runner = load_runner()
    output = tmp_path / "incomplete.json"
    report = SimpleNamespace(j_switch=0.4, j_greedy=0.4, j_open_best=0.2,
                             j_best_fixed_k=0.4, j_fixed_k={20: 0.4}, m=0.2, m_dur=0.0,
                             open_candidates=[((0, 0, 0, 0), None, 0.2)] * 95,
                             as_dict=lambda: {})
    monkeypatch.setattr(sys, "argv", arguments(output))
    monkeypatch.setattr(runner, "enumerate_references", lambda config: report)
    with pytest.raises(AssertionError, match="incomplete open-loop census"):
        runner.main()
    assert not output.exists()


def test_lognormal_moment_publication(monkeypatch, tmp_path):
    runner = load_runner()
    output = tmp_path / "moments.json"
    law = SimpleNamespace(mean=lambda: 20.0, variance=lambda: 400.0,
                          dp_age_cap=lambda horizon: horizon - 1,
                          hazard_table=lambda cap: np.full(cap + 1, 0.05),
                          _moments=lambda: (20.0, 800.0, 1.0 - 1e-13),
                          log_location=2.49, support_cap=98000)
    monkeypatch.setattr(runner.RelayCorridorConfig, "region_laws", lambda self: (law, law))
    monkeypatch.setattr(runner, "dp_service_profile", lambda hazard, horizon, roles, **kwargs: np.zeros(horizon))
    monkeypatch.setattr(sys, "argv", arguments(output, "calibration", "lognormal"))
    runner.main()
    observed = json.loads(output.read_text())["law"]
    assert observed["first_moment"] == 20 and observed["second_moment"] == 800
    assert observed["computed_mass"] == 1.0 - 1e-13
    assert observed["residual_mass"] == 1.0 - observed["computed_mass"]
    assert observed["moment_support_cap"] == 98000
    assert observed["dp_age_cap"] == 40 and len(observed["hazard"]) == 41


def test_geometric_switching_closed_form(monkeypatch, tmp_path):
    runner = load_runner()
    output = tmp_path / "geometric.json"
    argv = arguments(output, law="geometric")
    argv[argv.index("--horizon") + 1] = "40"
    monkeypatch.setattr(sys, "argv", argv)
    runner.main()
    observed = json.loads(output.read_text())
    assert observed["J_switch"] == pytest.approx(0.4 * (1 + 39 * 0.95) / 40, abs=1e-10)
    assert observed["law"]["variance"] == 380
    assert observed["law"]["hazard"] == [0.05, 0.05]


@pytest.mark.parametrize("gap, expected", [
    (1e-10, "unresolved"), (-1e-10, "unresolved"), (0.0, "unresolved"),
    (0.5e-10, "unresolved"), (2e-10, "positive"), (-2e-10, "opposite"),
])
def test_gap_resolution_boundaries(monkeypatch, tmp_path, gap, expected):
    runner = load_runner()
    output = tmp_path / "resolution.json"
    report = SimpleNamespace(j_switch=gap, j_greedy=gap, j_open_best=0.0,
                             j_best_fixed_k=0.0, j_fixed_k={20: -gap}, m=gap, m_dur=gap,
                             open_candidates=[((0, 0, 0, 0), None, 0.0)] * 96,
                             as_dict=lambda: {"m": gap, "m_dur": gap})
    monkeypatch.setattr(sys, "argv", arguments(output, law="geometric"))
    monkeypatch.setattr(runner, "enumerate_references", lambda config: report)
    runner.main()
    observed = json.loads(output.read_text())
    assert observed["gap_ordering"] == dict(m=expected, m_dur=expected,
                                             fixed_improvement_over_k20=expected)


def test_reference_mismatch_logs_discrepancy(monkeypatch, tmp_path):
    runner = load_runner()
    output = tmp_path / "mismatch.json"
    report = SimpleNamespace(j_switch=0.4, j_greedy=0.5, j_open_best=0.2,
                             j_best_fixed_k=0.4, j_fixed_k={20: 0.4}, m=0.2, m_dur=0.0,
                             open_candidates=[((0, 0, 0, 0), None, 0.2)] * 96,
                             as_dict=lambda: {})
    monkeypatch.setattr(sys, "argv", arguments(output))
    monkeypatch.setattr(runner, "enumerate_references", lambda config: report)
    with pytest.raises(AssertionError, match="reference inconsistency") as error:
        runner.main()
    assert "greedy_minus_switch" in str(error.value)
    assert str(0.5 - 0.4) in str(error.value)
    assert not output.exists()
