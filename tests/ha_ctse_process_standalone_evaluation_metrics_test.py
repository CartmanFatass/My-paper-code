import ast
import csv
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from ha_ctse_process import standalone_evaluation
from ha_ctse_process import standalone_metrics
from ha_ctse_process.plotting import UPDATE_FIELDS


def _top_level_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_evaluation_and_metric_helpers_have_single_owners():
    root = Path(__file__).parents[1]
    train_functions = _top_level_functions(root / "ha_ctse_process" / "train.py")
    evaluation_functions = _top_level_functions(root / "ha_ctse_process" / "standalone_evaluation.py")
    metrics_functions = _top_level_functions(root / "ha_ctse_process" / "standalone_metrics.py")

    assert not train_functions.intersection(
        {
            "numeric_metric",
            "extract_eval_metrics",
            "evaluate",
            "log_train_metrics",
            "export_update_metrics",
            "log_eval_metrics",
            "emit",
            "empty_r37_identity_metrics",
            "audit_r37_identity_observation",
        }
    )
    assert {"numeric_metric", "extract_eval_metrics", "evaluate"}.issubset(evaluation_functions)
    assert {
        "log_train_metrics",
        "export_update_metrics",
        "log_eval_metrics",
        "emit",
        "empty_r37_identity_metrics",
        "audit_r37_identity_observation",
    }.issubset(metrics_functions)


def test_evaluation_numeric_and_alias_metric_schema_are_preserved():
    assert standalone_evaluation.numeric_metric(np.array([1.0, 3.0])) == 2.0
    assert standalone_evaluation.numeric_metric([]) is None
    assert standalone_evaluation.numeric_metric(float("nan")) is None

    metrics = standalone_evaluation.extract_eval_metrics(
        {
            "reward_info": {
                "coverage_ratio": 0.5,
                "qos_satisfaction_ratio": 0.25,
                "system_throughput_mbps": 7.0,
                "battery_min_ratio": 0.8,
                "energy_failure_uav_count": 2,
            }
        }
    )
    assert [key for key in ("coverage", "qos", "throughput", "battery_min", "energy_failures") if key in metrics] == [
        "coverage",
        "qos",
        "throughput",
        "battery_min",
        "energy_failures",
    ]
    assert metrics["coverage"] == 0.5
    assert metrics["throughput"] == 7.0


class _Writer:
    def __init__(self):
        self.scalars = []
        self.flush_count = 0

    def add_scalar(self, name, value, step):
        self.scalars.append((name, value, step))

    def flush(self):
        self.flush_count += 1


def test_metric_writers_preserve_tensorboard_and_update_csv_schema(tmp_path, monkeypatch):
    writer = _Writer()
    process_metrics = defaultdict(float)
    low_metrics = defaultdict(float)
    process_metrics.update(
        process_segments=2.0,
        process_loss=0.5,
        process_reward_mean=0.25,
        outcome_available_mean=1.0,
        outcome_abs_mean=0.0,
        high_loss=0.75,
        high_entropy=0.1,
        high_return_mean=0.2,
    )
    low_metrics.update(low_loss=0.3, low_entropy=0.4, return_mean=0.5)

    standalone_metrics.log_train_metrics(writer, 12, [1.0, 3.0], process_metrics, low_metrics)
    standalone_metrics.log_eval_metrics(writer, 12, {"reward_mean": 2.0})
    assert ("Train/EnvRewardMean", 2.0, 12) in writer.scalars
    assert ("Eval/reward_mean", 2.0, 12) in writer.scalars
    assert writer.flush_count == 2

    plot_calls = []
    monkeypatch.setattr(standalone_metrics, "save_update_plots", lambda log_dir: plot_calls.append(log_dir))
    args = SimpleNamespace(log_dir=str(tmp_path), plot_interval=1)
    standalone_metrics.export_update_metrics(args, 3, 12, 2.0, process_metrics, low_metrics)

    with (tmp_path / "metrics" / "train_updates.csv").open(newline="", encoding="utf-8") as handle:
        assert next(csv.reader(handle)) == list(UPDATE_FIELDS)
    assert plot_calls == [str(tmp_path)]
