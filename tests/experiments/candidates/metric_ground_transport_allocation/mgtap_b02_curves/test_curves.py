"""One toy publication smoke plus frozen numerical and result-rule checks."""

import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.metric_ground_transport_allocation.actor import Actor
from experiments.candidates.metric_ground_transport_allocation.config import LOADS, ORDERED_PAIRS, demand
from experiments.candidates.metric_ground_transport_allocation.mgtap_b02_curves.numerical import (
    EVAL_PHASE, TRAIN_PHASE, decode_group, evaluate, evaluation_groups, training_group, training_loss,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_b02_curves.reporting import (
    MAIN_GRID, MAIN_SEEDS, cost_law, result_branch, summarize,
)
from experiments.candidates.metric_ground_transport_allocation.rng import tapes_for_decisions

ROOT = Path(__file__).resolve().parents[5]


def test_toy_runner_publication(tmp_path):
    out = tmp_path / "smoke"
    marker = tmp_path / "old_activity.json"
    env = dict(os.environ, MGTAP_ACTIVITY_MARKER=str(marker))
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/run_mgtap_b02_curves.py"),
                                "--mode", "smoke", "--seed", "17", "--out", str(out)],
                               cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["branch"] is None
    assert summary["evidence_class"] == "test_only"
    assert not marker.exists()
    assert len(summary["launch_sha"]) == 40
    assert summary["wall_seconds"] > 0 and summary["shared_setup_seconds"] > 0
    assert summary["configuration"]["parameters"] == 60
    arrays = {}
    for arm in ("METRIC", "FREE"):
        row = summary["arms"][arm]
        trace = json.loads((out / row["training_trace"]).read_text())
        arrays[arm] = np.load(out / row["evaluation_arrays"])
        data = arrays[arm]
        assert row["updates"] == 1 and row["training_decisions"] == 96
        assert row["training_agent_steps"] == 576
        assert row["evaluation_episodes"] == 192
        assert row["evaluation_decisions"] == 384 and row["evaluation_agent_steps"] == 2304
        assert data["episode_returns"].shape == (2, 2, 12, 2, 2)
        assert data["parameters"].shape == (2, 60)
        assert np.count_nonzero(data["parameters"][0]) == 0
        assert trace[0]["preclip_gradient_norm"] > 0
        assert trace[0]["step_displacement_l2"] > 0
        assert trace[0]["cumulative_path_l2"] == trace[0]["distance_from_zero_l2"]
        np.testing.assert_allclose(trace[0]["distance_from_zero_l2"], np.linalg.norm(data["parameters"][1]))
        np.testing.assert_allclose([v["return"] for v in row["curve"]], data["episode_returns"].mean(axis=(1, 2, 3, 4)))
        measured = row["cost"]
        assert measured["seconds_per_update"] > 0 and measured["seconds_per_full_evaluation"] > 0
        assert measured["projected_main_seconds_all_three_seeds"] == 6 * (
            256 * row["update_seconds"] + 17 * row["evaluation_seconds"] / 2)
    np.testing.assert_array_equal(arrays["METRIC"]["episode_returns"][0], arrays["FREE"]["episode_returns"][0])


def test_factorial_sampling_and_inherited_loss():
    torch.set_num_threads(1)
    groups = {n: training_group(17, 1, n) for n in (4, 8)}
    actor = Actor("METRIC", "INTACT")
    manual = torch.zeros((), dtype=torch.float64)
    for n, group in groups.items():
        rows = {(tuple(pair), int(load), int(epoch)) for pair, load, epoch in
                zip(group["pairs"], group["loads"], group["epochs"])}
        assert len(rows) == 48
        for i, (pair, load, epoch) in enumerate(zip(group["pairs"], group["loads"], group["epochs"])):
            np.testing.assert_array_equal(group["demands"][i], demand(n, pair, LOADS[load], epoch))
        repeat = training_group(17, 1, n)
        for key in group:
            np.testing.assert_array_equal(group[key], repeat[key])
        decoded, rewards = decode_group(actor, group)
        manual = manual + torch.sum(-0.5 * rewards / n * decoded.log_probability - 0.5 * 0.005 * decoded.mean_entropy)
    actual = training_loss(actor, groups)
    assert actual.dtype == torch.float64
    torch.testing.assert_close(actual, manual / 48.0, rtol=0, atol=0)
    actual.backward()
    assert sum(p.numel() for p in actor.parameters()) == 60
    assert all(torch.count_nonzero(p.grad) > 0 for p in actor.parameters())
    assert 256 * sum(len(g["roles"]) for g in groups.values()) == 24576
    assert 256 * sum(g["roles"].size for g in groups.values()) == 147456
    assert TRAIN_PHASE != EVAL_PHASE


def test_batched_evaluation_matches_addressed_blocks():
    groups = evaluation_groups(19, 16)
    actor = Actor("FREE", "INTACT")
    actor.load_parameter_vector(np.linspace(-0.2, 0.3, 60))
    values = evaluate(actor, groups, 16)
    for ni, n in enumerate((4, 8)):
        pi, li = 5, 1
        epochs = []
        for epoch in (1, 2):
            start = ((pi * 2 + li) * 2 + epoch - 1) * 16
            block = {key: value[start:start + 16] for key, value in groups[n].items()}
            tapes = tapes_for_decisions(EVAL_PHASE, 19, (n, pi, li, epoch), 16, n)
            np.testing.assert_array_equal(block["uniforms"], tapes["action_uniforms"])
            np.testing.assert_array_equal(block["priorities"], tapes["priority_ranks"])
            with torch.no_grad():
                _, rewards = decode_group(actor, block)
            epochs.append(rewards.numpy())
        np.testing.assert_array_equal(values[ni, pi, li], (epochs[0] + epochs[1]) / (2 * n))
    assert values.size * 17 == 13056
    assert values.size * 2 * 17 == 26112
    assert sum(g["roles"].size for g in groups.values()) * 17 == 156672


@pytest.mark.parametrize("deltas,expected", [
    ([0.01] * 3, "B02_METRIC_CURVE_SIGNAL"),
    ([-0.01] * 3, "B02_FREE_CURVE_SIGNAL"),
    ([0.009] * 3, "B02_INSIDE_MEI"),
    ([0.06, -0.01, -0.01], "B02_MIXED_SEEDS"),
    ([-0.06, 0.01, 0.01], "B02_MIXED_SEEDS"),
])
def test_reading_rule(deltas, expected):
    assert result_branch(deltas) == expected


def test_complete_main_aggregate_only():
    packets = [{"seed": seed, "mode": "main", "status": "complete", "arms": {
        arm: {"status": "complete", "updates": 256,
              "curve": [{"update": t, "return": value} for t in MAIN_GRID]}
        for arm, value in (("METRIC", 0.03), ("FREE", 0.0))}} for seed in MAIN_SEEDS]
    result = summarize(packets)
    assert result["branch"] == "B02_METRIC_CURVE_SIGNAL"
    assert result["auc_contrast_mean"] == pytest.approx(0.03)
    assert result["auc_contrast_sample_sd"] == 0
    for row in result["by_seed"].values():
        assert row["named_budget_contrasts"] == {"16": 0.03, "64": 0.03, "256": 0.03}
    assert summarize(packets[:2])["branch"] is None
    packets[0]["mode"] = "pilot"
    assert summarize(packets)["branch"] is None
    packets[0]["mode"] = "main"
    packets[0]["arms"]["METRIC"]["curve"].pop()
    assert summarize(packets)["branch"] is None
    measured = cost_law(2, 4, 3, 6)
    assert measured["projected_main_seconds_all_three_seeds"] == 6 * (256 * 0.5 + 17 * 0.5)
