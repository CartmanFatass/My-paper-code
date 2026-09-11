import json
from experiments.candidates.variable_n_fleet_churn_causal_headroom.calibration import project
from scripts.run_vnfc_causal_headroom import main


def test_projection_complete_cost_and_boundary():
    native = {"scores": [{"seconds": .01, "candidate_count": 10}],
              "ticks": {"seconds": .001, "count": 10},
              "prehistory": {"seconds": .1, "calls": 6}}
    row = project(native, {"projected_seconds": 3}, {"projected_seconds": 4})
    assert row["full_bcrh_scored_rows_upper"] == 376688 * 1961
    assert row["total_native_ticks_upper"] == 9418560
    assert row["terms_seconds"]["full_bcrh_rows"] == 2 * 738685168 * .001
    assert row["status"] == "BLOCKED_WALL_CAP"
    assert row["native_terms_alone_exceed_cap"]


def test_toy_runner_publication_without_native_or_panel(tmp_path):
    assert main(["--mode", "toy", "--launch-sha", "synthetic-test",
                 "--out", str(tmp_path)]) == 0
    row = json.loads((tmp_path / "summary.json").read_text())
    assert row["scientific_result"] is False
    assert row["native_panel_worlds"] == row["native_candidate_endpoints"] == 0
    assert row["new_rng_draws"] == row["optimizer_updates"] == 0
    assert row["synthetic_solver"]["complete"]
    assert row["wall_seconds"] < 60
