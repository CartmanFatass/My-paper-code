import hashlib
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from ha_ctse_process.metrics_io import append_csv
from ha_ctse_process.metrics_io import read_csv_records
from ha_ctse_process import plotting
from ha_ctse_process.process_outcomes import ProcessOutcomeExtractor
from ha_ctse_process import uav_g0_statistics
from tools.analysis import p2_gate_check
from tools.analysis import paper_experiment_report
from tools.analysis import visualize_evaluation
from tools.benchmarks import benchmark_analysis_io


def test_extract_uav_metrics_preserves_missing_backhaul_inputs():
    missing = plotting.extract_uav_metrics(
        {"system_throughput_mbps": 4.0, "current_backhaul_served_users": 2.0}
    )
    assert "backhaul_connected_flag" not in missing
    assert "throughput_when_backhaul_connected_mbps" not in missing

    disconnected = plotting.extract_uav_metrics(
        {
            "system_throughput_mbps": 0.0,
            "current_backhaul_served_users": 0.0,
            "full_network_disconnect": 1.0,
            "backhaul_outage_ratio": 1.0,
        }
    )
    assert disconnected["backhaul_connected_flag"] == 0.0


def test_eval_series_separates_checkpoint_step_run_and_evaluation_seed_groups():
    records = [
        {"checkpoint": "a.pt", "eval_step": 10.0, "total_steps": 10.0, "run_seed": 1.0, "seed": 41.0, "reset_seed": 41000.0, "episode": 0.0, "reward": 1.0},
        {"checkpoint": "a.pt", "eval_step": 10.0, "total_steps": 10.0, "run_seed": 1.0, "seed": 41.0, "reset_seed": 41001.0, "episode": 1.0, "reward": 2.0},
        {"checkpoint": "a.pt", "eval_step": 10.0, "total_steps": 10.0, "run_seed": 2.0, "seed": 41.0, "reset_seed": 41000.0, "episode": 0.0, "reward": 3.0},
    ]
    x, y = plotting._series(records, "reward")
    np.testing.assert_equal(x, np.array([10.0, 10.0, np.nan, 10.0]))
    np.testing.assert_equal(y, np.array([1.0, 2.0, np.nan, 3.0]))
    smoothed = plotting.moving_average(y, 2)
    assert math.isnan(smoothed[2])
    assert smoothed[3] == 3.0
    train_x, train_y = plotting._series(
        [{"total_steps": 1.0, "env_reward_mean": 2.0}], "env_reward_mean"
    )
    np.testing.assert_array_equal(train_x, np.array([1.0]))
    np.testing.assert_array_equal(train_y, np.array([2.0]))


def test_incremental_eval_loader_matches_reference_and_rejects_prefix_change(tmp_path):
    assert plotting.EVAL_PLOT_DEFAULT_MODE == "optimized"
    path = tmp_path / "metrics" / "eval_episodes.csv"
    fields = (
        "checkpoint",
        "total_steps",
        "eval_step",
        "run_seed",
        "seed",
        "reset_seed",
        "episode",
        "reward",
    )
    append_csv(
        path,
        {
            "checkpoint": "a.pt",
            "total_steps": 10,
            "eval_step": 10,
            "run_seed": 101,
            "seed": 41,
            "reset_seed": 41000,
            "episode": 0,
            "reward": 1.5,
        },
        fields,
    )
    plotting._EVAL_RECORD_CACHE.clear()
    optimized = plotting.load_eval_plot_records(path, mode="optimized")
    assert optimized == plotting.load_eval_plot_records(path, mode="reference")

    append_csv(
        path,
        {
            "checkpoint": "b.pt",
            "total_steps": 20,
            "eval_step": 20,
            "run_seed": 101,
            "seed": 42,
            "reset_seed": 42000,
            "episode": 0,
            "reward": 2.5,
        },
        fields,
    )
    assert plotting.load_eval_plot_records(path, mode="optimized") == plotting.load_eval_plot_records(
        path, mode="reference"
    )
    sidecar = path.with_name(f"{path.name}.plot-cache.json")
    assert sidecar.exists()

    raw = bytearray(path.read_bytes())
    raw[raw.index(b"a.pt")] = ord("z")
    path.write_bytes(raw)
    with pytest.raises(RuntimeError, match="prefix changed"):
        plotting.load_eval_plot_records(path, mode="optimized")


def test_process_outcome_delta_requires_same_metric_at_exact_endpoints():
    extractor = ProcessOutcomeExtractor(normalize=False)
    segment = SimpleNamespace(
        reward_info_seq=[
            {"effective_connected_users": 1.0},
            {"effective_connected_users": 100.0},
            {"effective_connected_users": 3.0},
        ],
        obs=[],
        end_obs=None,
        rewards=[],
    )
    raw, mask = extractor.extract_raw(segment)
    index = extractor.field_names.index("delta_effective_connected_users")
    assert mask[index]
    assert raw[index] == 2.0

    segment.reward_info_seq = [
        {"effective_connected_users": 1.0},
        {"effective_connected_users": 100.0},
        {"connected_users": 3.0},
    ]
    raw, mask = extractor.extract_raw(segment)
    assert not mask[index]
    assert raw[index] == 0.0


def test_paper_summary_uses_seed_means_and_rejects_duplicate_episode_identity():
    rows = [
        {"preset": "P", "checkpoint": "c", "eval_step": 10, "run_seed": 1, "seed": 41, "episode": i, "reward": 0.0}
        for i in range(100)
    ]
    rows.append(
        {"preset": "P", "checkpoint": "c", "eval_step": 10, "run_seed": 2, "seed": 41, "episode": 0, "reward": 10.0}
    )
    frame = pd.DataFrame(rows)
    summary = paper_experiment_report._summarize(frame, ["preset"], ["reward"])
    row = summary.iloc[0]
    assert row["mean"] == 5.0
    assert row["n_seeds"] == 2
    assert row["episode_count"] == 101
    assert row["count"] == 2

    duplicate = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate paper episode"):
        paper_experiment_report._summarize(duplicate, ["preset"], ["reward"])


def test_p2_gate_tail_requires_every_hard_value_to_be_finite():
    rows = [{"hard": "1"}, {"hard": "2"}, {"hard": ""}, {"hard": "nan"}]
    assert p2_gate_check._tail_mean(rows, "hard", require_complete=True) is None
    assert p2_gate_check._tail_mean(rows, "hard") is None
    assert p2_gate_check._tail_mean([{"hard": "0"}, {"hard": "2"}], "hard", require_complete=True) == 2.0


def test_p2_gate_requires_exact_path_and_rejects_missing_tail_value(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["p2_gate_check.py"])
    with pytest.raises(SystemExit):
        p2_gate_check.main()

    path = tmp_path / "gate.csv"
    key_a, key_b = p2_gate_check.HARD_KEYS
    path.write_text(f"{key_a},{key_b}\n1,1\n1,1\n1,\n1,1\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["p2_gate_check.py", "--gate-csv", str(path)])
    assert p2_gate_check.main() == 1


def test_g0_bootstrap_plan_is_shared_immutable_and_fingerprint_exact():
    first = uav_g0_statistics.make_bootstrap_index_plan()
    second = uav_g0_statistics.make_bootstrap_index_plan()
    assert first is second
    assert first.flags.writeable is False
    assert hashlib.sha256(first.tobytes(order="C")).hexdigest() == uav_g0_statistics.BOOTSTRAP_INDEX_SHA256
    with pytest.raises(ValueError):
        first[0, 0] = 1


def test_visualizer_requires_explicit_random_and_model_load_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        visualize_evaluation,
        "parse_args",
        lambda: SimpleNamespace(use_random=False, model_path=None),
    )
    with pytest.raises(SystemExit, match="model_path is required"):
        visualize_evaluation.main()

    model = tmp_path / "bad-model.pt"
    model.write_bytes(b"not a checkpoint")
    args = SimpleNamespace(
        use_random=False,
        model_path=str(model),
        config="fake_config",
        preset="",
        scenario=4,
        seed=7,
    )
    monkeypatch.setattr(visualize_evaluation, "parse_args", lambda: args)

    class Config:
        n_agents = 2
        n_users = 3
        area_size = 10
        max_hops = 2
        user_distribution = "uniform"
        channel_model = "free_space"
        use_fdma = False

        def update_env_dims(self, state_dim, obs_dim):
            self.state_dim = state_dim
            self.obs_dim = obs_dim

    monkeypatch.setattr(
        visualize_evaluation.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Config=Config),
    )
    monkeypatch.setattr(
        visualize_evaluation,
        "create_env",
        lambda *_args, **_kwargs: SimpleNamespace(state_dim=4, obs_dim=2, close=lambda: None),
    )

    class BrokenAgent:
        def __init__(self, *_args, **_kwargs):
            pass

        def load_model(self, _path):
            raise RuntimeError("invalid model")

    monkeypatch.setattr(visualize_evaluation, "HMASDAgent", BrokenAgent)
    with pytest.raises(RuntimeError, match="invalid model"):
        visualize_evaluation.main()


def test_analysis_benchmark_requires_run_seed_and_odd_minimum_sample_count(tmp_path):
    with pytest.raises(ValueError, match="odd value >= 31"):
        benchmark_analysis_io.run_benchmark(episodes_per_group=8, repeats=30)
    with pytest.raises(ValueError, match="positive"):
        benchmark_analysis_io.run_benchmark(episodes_per_group=0, repeats=31)
    with pytest.raises(ValueError, match="run_seed"):
        benchmark_analysis_io.run_benchmark(
            episodes_per_group=8, repeats=31, run_seed=-1
        )

    csv_path = tmp_path / "metrics" / "eval_episodes.csv"
    benchmark_analysis_io._append_eval_group(
        csv_path, group_index=3, episodes=2, run_seed=12345
    )
    rows = read_csv_records(csv_path)
    assert [row["run_seed"] for row in rows] == [12345.0, 12345.0]
    assert [row["seed"] for row in rows] == [10003.0, 10003.0]
