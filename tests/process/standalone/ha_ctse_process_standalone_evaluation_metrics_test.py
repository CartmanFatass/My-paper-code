import ast
import csv
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from ha_ctse_process import standalone_evaluation
from ha_ctse_process import standalone_metrics
from ha_ctse_process.plotting import UPDATE_FIELDS


RETIRED_METRIC_FUNCTIONS = {
    "empty_r37_identity_metrics",
    "audit_r37_identity_observation",
}
RETIRED_METRIC_PREFIXES = (
    "r28_g1_",
    "r29_action_info_",
    "r31_effect_",
    "aem_",
    "r37_identity_",
    "r37_critic_identity_",
)


def _top_level_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_evaluation_and_metric_helpers_have_single_owners():
    root = Path(__file__).parents[3]
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
        }
    )
    assert {"numeric_metric", "extract_eval_metrics", "evaluate"}.issubset(evaluation_functions)
    assert {
        "log_train_metrics",
        "export_update_metrics",
        "log_eval_metrics",
        "emit",
    }.issubset(metrics_functions)
    assert metrics_functions.isdisjoint(RETIRED_METRIC_FUNCTIONS)


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
    assert "backhaul_connected_flag" not in metrics
    assert standalone_evaluation.format_optional_metric(
        metrics, "backhaul_connected_flag"
    ) == "NA"
    assert standalone_evaluation.format_optional_metric(
        {"backhaul_connected_flag": 0.0}, "backhaul_connected_flag"
    ) == "0.000000"


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
    assert not any(field.startswith(RETIRED_METRIC_PREFIXES) for field in UPDATE_FIELDS)
    assert writer.flush_count == 2

    plot_calls = []
    monkeypatch.setattr(standalone_metrics, "save_update_plots", lambda log_dir: plot_calls.append(log_dir))
    disabled_log_dir = tmp_path / "plotting_disabled"
    disabled_args = SimpleNamespace(log_dir=str(disabled_log_dir), plot_interval=0)
    standalone_metrics.export_update_metrics(
        disabled_args, 3, 12, 2.0, process_metrics, low_metrics
    )

    with (disabled_log_dir / "metrics" / "train_updates.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        disabled_rows = list(csv.reader(handle))
    assert disabled_rows[0] == list(UPDATE_FIELDS)
    assert plot_calls == []

    enabled_log_dir = tmp_path / "plotting_enabled"
    enabled_args = SimpleNamespace(log_dir=str(enabled_log_dir), plot_interval=1)
    standalone_metrics.export_update_metrics(
        enabled_args, 3, 12, 2.0, process_metrics, low_metrics
    )
    with (enabled_log_dir / "metrics" / "train_updates.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        assert list(csv.reader(handle)) == disabled_rows
    assert plot_calls == [str(enabled_log_dir)]

    plot_calls.clear()
    cadence_log_dir = tmp_path / "plotting_cadence"
    cadence_args = SimpleNamespace(log_dir=str(cadence_log_dir), plot_interval=2)
    for update_idx in (1, 2, 3, 4):
        standalone_metrics.export_update_metrics(
            cadence_args, update_idx, 12, 2.0, process_metrics, low_metrics
        )
    assert plot_calls == [str(cadence_log_dir), str(cadence_log_dir)]
