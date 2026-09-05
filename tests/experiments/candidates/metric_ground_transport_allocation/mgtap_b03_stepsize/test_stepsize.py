"""One toy publication run plus global-selection and ordered-rule checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.metric_ground_transport_allocation.mgtap_b02_curves.reporting import curve_point
from experiments.candidates.metric_ground_transport_allocation.mgtap_b03_stepsize.reporting import (
    ARMS, MAIN_GRID, MAIN_SEEDS, RATES, result_branch, summarize,
)

ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts/run_mgtap_b03_stepsize.py"


def panel():
    packets = []
    for i, seed in enumerate(MAIN_SEEDS):
        arms = {}
        for arm in ARMS:
            arms[arm] = {}
            for rate in RATES:
                # Per-seed winners differ; global tie at .3 and 1 must select .3.
                value = {0.1: 0.1, 0.3: (0.4, 0.2, 0.3)[i],
                         1.0: (0.2, 0.4, 0.3)[i], 3.0: 0.2}[rate]
                value += 0.03 if arm == "METRIC" else 0.0
                curve = [curve_point(t, np.full((2, 12, 2, 16), value), np.ones((2, 12, 2)))
                         for t in MAIN_GRID]
                arms[arm][str(rate)] = dict(status="complete", updates=256, curve=curve,
                    training_decisions=24576, training_agent_steps=147456, evaluation_episodes=13056,
                    evaluation_decisions=26112, evaluation_agent_steps=156672, wall_seconds=1.0)
        packets.append(dict(seed=seed, mode="main", status="complete", arms=arms,
                            oracle={"return": 1.0}, launch_sha="test_fixture", output_root="fixture",
                            shared_setup_seconds=0.1))
    return packets


def test_toy_runner_and_offline_publication(tmp_path):
    oracle = tmp_path / "fixture_oracle.npy"
    np.save(oracle, np.ones((2, 12, 2), dtype=np.float64))
    out = tmp_path / "smoke"
    done = subprocess.run([sys.executable, str(RUNNER), "--mode", "smoke", "--seed", "17",
                           "--oracle", str(oracle), "--out", str(out)], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["branch"] is None
    assert summary["evidence_class"] == "test_only"
    assert len(summary["launch_sha"]) == 40
    assert summary["wall_seconds"] > 0
    assert (summary["peak_rss_bytes"] is None and summary["resource_status"] == "resources_unmeasured") or summary["peak_rss_bytes"] > 0
    zero_returns = None
    for arm in ARMS:
        baseline = None
        for rate in RATES:
            row = summary["arms"][arm][str(rate)]
            trace = json.loads((out / row["training_trace"]).read_text())
            with np.load(out / row["evaluation_arrays"]) as data:
                assert data["parameters"].shape == (2, 60)
                assert data["episode_returns"].shape == (2, 2, 12, 2, 2)
                assert np.count_nonzero(data["parameters"][0]) == 0
                if zero_returns is None:
                    zero_returns = data["episode_returns"][0].copy()
                np.testing.assert_array_equal(zero_returns, data["episode_returns"][0])
                if baseline is None:
                    baseline = data["parameters"][1].copy()
                np.testing.assert_allclose(data["parameters"][1], baseline * (rate / 0.1), atol=1e-15)
                np.testing.assert_allclose(trace[0]["distance_from_zero_l2"], np.linalg.norm(data["parameters"][1]))
                np.testing.assert_allclose([v["return"] for v in row["curve"]],
                    data["episode_returns"].mean(axis=(1, 2, 3, 4)))
            assert row["updates"] == 1 and row["training_decisions"] == 96
            assert row["training_agent_steps"] == 576 and row["evaluation_episodes"] == 192
            assert row["evaluation_decisions"] == 384 and row["evaluation_agent_steps"] == 2304
            assert trace[0]["preclip_gradient_norm"] > 0
            assert row["cost"]["seconds_per_update"] > 0
            assert row["cost"]["seconds_per_full_evaluation"] > 0
    inputs = []
    for packet in panel():
        path = tmp_path / f"{packet['seed']}.json"
        path.write_text(json.dumps(packet))
        inputs.append(str(path))
    publication = tmp_path / "publication"
    done = subprocess.run([sys.executable, str(RUNNER), "--mode", "summarize", "--inputs", *inputs,
                           "--out", str(publication)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    result = json.loads((publication / "summary.json").read_text())
    assert result["branch"] == "B03_METRIC_RESIDUAL_SIGNAL"
    print("toy wall/RSS:", summary["wall_seconds"], summary["peak_rss_bytes"])
    print("toy measured cost:", {a: {r: v["cost"] for r, v in rows.items()} for a, rows in summary["arms"].items()})


def test_global_selection_and_complete_panel_only():
    packets = panel()
    result = summarize(packets)
    assert result["selected_rates"] == {"METRIC": 0.3, "FREE": 0.3}
    assert result["selected_auc_contrast"]["mean"] == pytest.approx(0.03)
    assert result["anchor_auc_contrast"]["mean"] == pytest.approx(0.03)
    assert result["H"]["mean"] == pytest.approx(0.17)
    assert result["selection_gain"]["FREE"]["mean"] == pytest.approx(0.2)
    assert result["selected_free_endpoint_headroom"]["mean"] == pytest.approx(0.7)
    assert result["counts"] == dict(updates=6144, training_decisions=589824,
        training_agent_steps=3538944, evaluation_episodes=313344,
        evaluation_decisions=626688, evaluation_agent_steps=3760128)
    assert summarize(packets[:2])["branch"] is None
    broken = copy.deepcopy(packets)
    broken[0]["arms"]["FREE"]["3.0"]["status"] = "budget_truncated"
    assert summarize(broken)["branch"] is None
    broken = copy.deepcopy(packets)
    broken[0]["arms"]["FREE"]["3.0"]["curve"].pop()
    assert summarize(broken)["branch"] is None
    packets[0]["mode"] = "smoke"
    assert summarize(packets)["branch"] is None


@pytest.mark.parametrize("deltas,expected", [
    ([0.01] * 3, "B03_METRIC_RESIDUAL_SIGNAL"),
    ([-0.01] * 3, "B03_FREE_SELECTED_SIGNAL"),
    ([0.009] * 3, "B03_SELECTED_INSIDE_MEI"),
    ([0.06, -0.01, -0.01], "B03_MIXED_SEEDS"),
    ([-0.06, 0.01, 0.01], "B03_MIXED_SEEDS"),
])
def test_ordered_rule(deltas, expected):
    assert result_branch(deltas) == expected
