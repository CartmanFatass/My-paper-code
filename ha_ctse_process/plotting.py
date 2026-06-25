"""Metrics export and plotting for standalone HA-CTSE UAV experiments."""

from __future__ import annotations

import csv
import re
import argparse
from pathlib import Path
from typing import Any

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - plotting is optional in headless smoke.
    plt = None


# Field set follows the Scenario 7/HMASD training monitor categories, trimmed to
# scalar UAV metrics that are meaningful for standalone HA-CTSE eval plots.
UAV_METRIC_FIELDS = (
    "coverage_ratio",
    "effective_connected_users",
    "system_throughput_mbps",
    "avg_throughput_per_user_mbps",
    "capacity_limited_throughput_mbps",
    "effective_end_to_end_throughput_mbps",
    "qos_satisfaction_ratio",
    "qos_met_fraction",
    "qos_target_ratio",
    "mean_user_rate_mbps",
    "std_user_rate_mbps",
    "min_user_rate_mbps",
    "median_user_rate_mbps",
    "p10_user_rate_mbps",
    "p90_user_rate_mbps",
    "max_user_rate_mbps",
    "battery_mean_ratio",
    "battery_min_ratio",
    "low_battery_uav_count",
    "critical_battery_uav_count",
    "energy_failure_uav_count",
    "depleted_uav_count",
    "charging_uav_count",
    "effective_charging_session_count",
    "episode_charging_session_count",
    "episode_first_effective_charge_step",
    "episode_energy_charged_wh",
    "normalized_propulsion_energy",
    "instantaneous_bits_per_joule",
    "return_constraint_cost",
    "return_risk_penalty",
    "return_deficit_max",
    "return_margin_mean",
    "return_margin_min",
    "return_violation_fraction",
    "episode_return_constraint_cost_sum",
    "episode_return_risk_penalty_sum",
    "episode_return_risk_steps",
    "episode_max_return_deficit",
    "episode_final_min_return_margin",
    "cutoff_event_count",
    "depletion_event_count",
    "episode_cutoff_event_count",
    "episode_depletion_event_count",
    "episode_qos_utility_sum",
    "episode_qos_utility_mean",
    "episode_graph_pbrs_sum",
    "task_utility",
    "scenario7_reward",
    "safety_reward_before_pbrs",
    "graph_potential_delta",
    "shaping_potential_delta",
)

COMM_METRIC_FIELDS = (
    "connected_users",
    "access_connected_users",
    "total_connected_users",
    "served_users",
    "connectivity_ratio",
    "connected_uavs",
    "uavs_with_backhaul",
    "avg_hops",
    "relay_route_lost_uavs",
    "relay_route_lost_users",
    "relay_route_loss_ratio",
    "relay_route_loss_prev_served_ratio",
    "prev_backhaul_served_users",
    "current_backhaul_served_users",
    "backhaul_outage_users",
    "backhaul_outage_ratio",
    "service_drop_users",
    "service_drop_ratio",
    "backhaul_drop_users",
    "backhaul_drop_ratio",
    "full_network_disconnect",
    "full_disconnect_streak",
    "coverage_drop_ratio",
    "backhaul_outage_ema",
    "instant_outage_intensity",
    "min_serving_backhaul_bottleneck_mbps",
    "avg_serving_backhaul_bottleneck_mbps",
    "backhaul_margin_penalty_raw",
    "backhaul_outage_penalty",
    "full_disconnect_penalty",
    "coverage_drop_penalty",
    "outage_memory_penalty",
    "relay_break_penalty",
    "backhaul_margin_penalty",
    "backhaul_guard_checked_actions",
    "backhaul_guard_blocked_actions",
    "routing_overhead",
)


UPDATE_FIELDS = (
    "update",
    "total_steps",
    "env_reward_mean",
    "process_segments",
    "process_loss",
    "process_outcome_loss",
    "process_contrastive_loss",
    "process_prior_loss",
    "process_posterior_acc",
    "process_mi_estimate_mean",
    "process_log_q_mean",
    "process_log_p_mean",
    "process_reward_mean",
    "outcome_available_mean",
    "outcome_abs_mean",
    "duration_only_accuracy",
    "skill_switch_rate",
    "segment_length_mean",
    "segment_length_max",
    "duration_target_mean",
    "skill_usage_entropy",
    "skill_usage_max_frac",
    "duration_usage_entropy",
    "duration_usage_max_frac",
    "skill_duration_mi",
    "team_code_usage_entropy",
    "team_code_usage_max_frac",
    "team_code_skill_mi",
    "high_loss",
    "high_policy_loss",
    "high_value_loss",
    "high_entropy_loss",
    "high_aux_loss",
    "high_entropy",
    "high_return_mean",
    "team_code_entropy",
    "compact_norm_mean",
    "opt_cd_loss",
    "opt_cmi_loss",
    "opt_aggregation_entropy",
    "low_loss",
    "low_policy_loss",
    "low_value_loss",
    "low_entropy_loss",
    "low_entropy",
    "return_mean",
)

EVAL_FIELDS = (
    "checkpoint",
    "total_steps",
    "episode",
    "reward",
    "length",
    *UAV_METRIC_FIELDS,
    *COMM_METRIC_FIELDS,
)


def numeric_scalar(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None
    return float(np.mean(finite))


def extract_uav_metrics(info: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(info, dict):
        return {}
    reward_info = info.get("reward_info", {})
    reward_components = info.get("reward_components", {})
    if isinstance(reward_components, dict) and isinstance(reward_components.get("reward_info"), dict):
        reward_components = {**reward_components, **reward_components["reward_info"]}
    source = {}
    for key, value in info.items():
        if key in {"reward_info", "reward_components", "infos_dict", "terminations_dict", "truncations_dict"}:
            continue
        source[key] = value
    if isinstance(reward_components, dict):
        source.update(reward_components)
    if isinstance(reward_info, dict):
        source.update(reward_info)

    aliases = {
        "coverage_ratio": ("coverage_ratio", "coverage", "final_coverage", "current_coverage"),
        "qos_satisfaction_ratio": (
            "qos_satisfaction_ratio",
            "qos_satisfaction",
            "qos_met_fraction",
            "qos_score",
            "current_qos",
        ),
        "system_throughput_mbps": (
            "system_throughput_mbps",
            "total_throughput_mbps",
            "throughput",
        ),
        "battery_min_ratio": ("battery_min_ratio", "min_battery_ratio", "min_energy_ratio"),
        "connected_users": ("connected_users", "effective_connected_users", "served_users"),
        "served_users": ("served_users", "effective_connected_users", "connected_users"),
        "connected_uavs": ("connected_uavs", "uavs_with_backhaul"),
    }
    metrics = {}
    for key in (*UAV_METRIC_FIELDS, *COMM_METRIC_FIELDS):
        scalar = numeric_scalar(source.get(key))
        if scalar is not None:
            metrics[key] = scalar
    for canonical, keys in aliases.items():
        if canonical in metrics:
            continue
        for key in keys:
            scalar = numeric_scalar(source.get(key))
            if scalar is not None:
                metrics[canonical] = scalar
                break
    return metrics


def append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            old_fields = tuple(reader.fieldnames or ())
            rows = list(reader)
        if old_fields != fields:
            preserved = tuple(field for field in old_fields if field not in fields)
            merged_fields = (*fields, *preserved)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(merged_fields), extrasaction="ignore")
                writer.writeheader()
                for old_row in rows:
                    writer.writerow({field: old_row.get(field, "") for field in merged_fields})
            fields = merged_fields
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_records(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    records: list[dict[str, float]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = {}
            for key, value in row.items():
                if value == "":
                    continue
                try:
                    record[key] = float(value)
                except ValueError:
                    continue
            if record:
                records.append(record)
    return records


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    window = max(1, min(int(window), values.size))
    kernel = np.ones(window, dtype=float) / float(window)
    return np.convolve(values, kernel, mode="same")


def _series(records: list[dict[str, float]], key: str) -> tuple[np.ndarray, np.ndarray]:
    xs = []
    ys = []
    for idx, record in enumerate(records):
        if key not in record:
            continue
        xs.append(record.get("total_steps", idx + 1))
        ys.append(record[key])
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def save_update_plots(log_dir: str | Path, window: int = 5) -> None:
    if plt is None:
        return
    log_dir = Path(log_dir)
    records = read_csv_records(log_dir / "metrics" / "train_updates.csv")
    if not records:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("env_reward_mean", "Env reward mean"),
        ("return_mean", "Low return mean"),
        ("process_reward_mean", "Process reward mean"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Standalone HA-CTSE Training Rewards", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_training_rewards.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("process_loss", "Process loss"),
        ("process_contrastive_loss", "Process contrast"),
        ("process_prior_loss", "Process prior"),
        ("process_outcome_loss", "Process outcome"),
        ("high_loss", "High loss"),
        ("high_value_loss", "High value"),
        ("high_policy_loss", "High policy"),
        ("low_loss", "Low loss"),
        ("low_value_loss", "Low value"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Standalone HA-CTSE Losses", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_losses.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("duration_only_accuracy", "Duration-only accuracy"),
        ("skill_switch_rate", "Skill switch rate"),
        ("segment_length_mean", "Segment length mean"),
        ("skill_usage_entropy", "Skill usage entropy"),
        ("duration_usage_entropy", "Duration usage entropy"),
        ("team_code_usage_entropy", "Team-code usage entropy"),
        ("skill_usage_max_frac", "Skill max fraction"),
        ("duration_usage_max_frac", "Duration max fraction"),
        ("team_code_usage_max_frac", "Team-code max fraction"),
        ("skill_duration_mi", "Skill-duration MI"),
        ("team_code_skill_mi", "Team-code/skill MI"),
        ("process_posterior_acc", "Process posterior acc"),
        ("process_mi_estimate_mean", "Process MI estimate"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Process Segment Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_process_diagnostics.png", dpi=180)
    plt.close(fig)


def save_eval_plots(log_dir: str | Path, window: int = 5) -> None:
    if plt is None:
        return
    log_dir = Path(log_dir)
    records = read_csv_records(log_dir / "metrics" / "eval_episodes.csv")
    if not records:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    x, reward = _series(records, "reward")
    if reward.size:
        ax.plot(x, reward, color="steelblue", alpha=0.35, linewidth=0.9, label="Episode reward")
        ax.plot(x, moving_average(reward, window), color="black", linewidth=2.0, label="Moving average")
    ax.set(title="Eval Reward", xlabel="Env steps", ylabel="Reward")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "eval_reward.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("coverage_ratio", "Coverage"),
        ("qos_satisfaction_ratio", "QoS satisfaction"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Eval Service Quality", xlabel="Env steps", ylabel="Ratio")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    ax2 = ax.twinx()
    x, y = _series(records, "system_throughput_mbps")
    if y.size:
        ax2.plot(x, moving_average(y, window), color="purple", label="Throughput Mbps")
        ax2.set_ylabel("Mbps")
        ax2.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(log_dir / "eval_service_quality.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("battery_min_ratio", "Min battery"),
        ("battery_mean_ratio", "Mean battery"),
        ("return_violation_fraction", "Return violation"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Eval Safety and Energy", xlabel="Env steps", ylabel="Ratio / fraction")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "eval_safety_energy.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("episode_charging_session_count", "Charging sessions"),
        ("effective_charging_session_count", "Effective charging sessions"),
        ("episode_energy_charged_wh", "Energy charged Wh"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Eval Charging Progress", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "eval_charging_progress.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("avg_hops", "Average hops"),
        ("connectivity_ratio", "Connectivity ratio"),
        ("connected_uavs", "Connected UAVs"),
        ("uavs_with_backhaul", "UAVs with backhaul"),
        ("total_connected_users", "Access-connected users"),
        ("effective_connected_users", "Effectively served users"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Communication Topology", xlabel="Env steps")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(log_dir / "eval_communication_topology.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("relay_route_loss_ratio", "Relay route loss ratio"),
        ("relay_route_loss_prev_served_ratio", "Loss / previous served"),
        ("backhaul_outage_ratio", "Backhaul outage ratio"),
        ("service_drop_ratio", "Service drop ratio"),
        ("backhaul_drop_ratio", "Backhaul drop ratio"),
        ("coverage_drop_ratio", "Coverage drop ratio"),
        ("full_network_disconnect", "Full disconnect flag"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Backhaul Robustness", xlabel="Env steps", ylabel="Ratio / flag")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(log_dir / "eval_backhaul_robustness.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_left = False
    for key, label in (
        ("min_serving_backhaul_bottleneck_mbps", "Min serving bottleneck Mbps"),
        ("avg_serving_backhaul_bottleneck_mbps", "Avg serving bottleneck Mbps"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_left = True
            ax.plot(x, moving_average(y, window), label=label)
    ax2 = ax.twinx()
    any_right = False
    for key, label in (
        ("backhaul_margin_penalty_raw", "Margin penalty raw"),
        ("backhaul_guard_checked_actions", "Guard checked actions"),
        ("backhaul_guard_blocked_actions", "Guard blocked actions"),
        ("routing_overhead", "Routing overhead"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_right = True
            ax2.plot(x, moving_average(y, window), linestyle="--", label=label)
    if any_left or any_right:
        ax.set(title="Eval Backhaul Capacity and Guard", xlabel="Env steps")
        ax.set_ylabel("Mbps")
        ax2.set_ylabel("Penalty / count")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        if any_left:
            ax.legend(loc="upper left")
        if any_right:
            ax2.legend(loc="upper right")
        fig.tight_layout()
        fig.savefig(log_dir / "eval_backhaul_capacity_guard.png", dpi=180)
    plt.close(fig)


LOG_KEY_ALIASES = {
    "duration_only_acc": "duration_only_accuracy",
    "switch_rate": "skill_switch_rate",
    "seg_len_mean": "segment_length_mean",
    "process_mi": "process_mi_estimate_mean",
    "posterior_acc": "process_posterior_acc",
    "skill_entropy": "skill_usage_entropy",
    "duration_entropy": "duration_usage_entropy",
    "g_entropy": "team_code_usage_entropy",
    "g_skill_mi": "team_code_skill_mi",
}


def parse_standalone_train_log(log_dir: str | Path) -> list[dict[str, float]]:
    log_dir = Path(log_dir)
    log_path = log_dir / "standalone_train.log"
    if not log_path.exists():
        return []
    rows: list[dict[str, float]] = []
    pattern = re.compile(r"([A-Za-z0-9_]+)=(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "standalone_update" not in line:
            continue
        row: dict[str, float] = {}
        for key, value in pattern.findall(line):
            key = LOG_KEY_ALIASES.get(key, key)
            try:
                row[key] = float(value)
            except ValueError:
                continue
        if "update" in row and "total_steps" in row:
            rows.append(row)
    if rows:
        csv_path = log_dir / "metrics" / "train_updates.csv"
        merged: dict[tuple[int, int], dict[str, Any]] = {}
        if csv_path.exists():
            with csv_path.open("r", newline="", encoding="utf-8") as handle:
                for existing in csv.DictReader(handle):
                    try:
                        key = (
                            int(float(existing.get("update", ""))),
                            int(float(existing.get("total_steps", ""))),
                        )
                    except ValueError:
                        continue
                    merged[key] = dict(existing)
        for row in rows:
            key = (int(row["update"]), int(row["total_steps"]))
            merged.setdefault(key, {}).update(row)
        ordered = [
            merged[key]
            for key in sorted(merged, key=lambda item: (item[0], item[1]))
        ]
        write_csv(csv_path, ordered, UPDATE_FIELDS)
        save_update_plots(log_dir)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone HA-CTSE plots from metrics/log files.")
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--from_log", action="store_true")
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    if args.from_log:
        rows = parse_standalone_train_log(args.log_dir)
        print(f"parsed_updates={len(rows)} log_dir={args.log_dir}")
    save_update_plots(args.log_dir, window=args.window)
    save_eval_plots(args.log_dir, window=args.window)


if __name__ == "__main__":
    main()
