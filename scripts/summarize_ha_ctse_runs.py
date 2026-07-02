"""Summarize HA-CTSE run directories without external dependencies."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


UPDATE_KEYS = [
    "env_reward_mean",
    "credit_full_disconnect_mean",
    "credit_recovery_rate",
    "credit_backhaul_connected_step_fraction",
    "credit_throughput_when_backhaul_connected_mbps",
    "lifetime_heterogeneity",
    "renewal_full_sync_rate",
    "renewal_pairwise_corr_mean",
    "duration_agent_mi",
    "duration_return_range",
    "duration_recovery_range",
    "p2_available_frac",
    "p2_corr_phi_recovery_event",
    "p2_partial_recovery_frac",
    "topology_potential_active",
    "topology_potential_reward_mean",
]

EVAL_RE = re.compile(
    r"standalone_eval\s+total_steps=(?P<steps>\d+)\s+episodes=(?P<episodes>\d+)\s+"
    r"reward_mean=(?P<reward>[-+0-9.eE]+)\s+reward_std=(?P<std>[-+0-9.eE]+)\s+"
    r"length_mean=(?P<length>[-+0-9.eE]+)\s+coverage=(?P<coverage>[-+0-9.eE]+)\s+"
    r"qos=(?P<qos>[-+0-9.eE]+)\s+throughput=(?P<throughput>[-+0-9.eE]+)\s+"
    r"(?:backhaul_connected_frac=(?P<backhaul_frac>[-+0-9.eE]+)\s+"
    r"throughput_when_backhaul_connected=(?P<backhaul_throughput>[-+0-9.eE]+)\s+)?"
    r"battery_min=(?P<battery>[-+0-9.eE]+)"
)


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def mean(rows: list[dict[str, str]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(as_float(row, key) for row in rows) / float(len(rows))


def read_updates(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_latest_eval(run_dir: Path) -> dict[str, float] | None:
    log_path = run_dir / "standalone_train.log"
    if not log_path.exists():
        return None
    latest = None
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = EVAL_RE.search(line)
        if not match:
            continue
        latest = {
            key: float(value) if value is not None else 0.0
            for key, value in match.groupdict().items()
        }
    return latest


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def summarize(root: Path, tail: int) -> int:
    csv_paths = sorted(root.glob("**/metrics/train_updates.csv"))
    if not csv_paths:
        print(f"No train_updates.csv found under {root}")
        return 1

    header = [
        "run",
        "steps",
        "eval_steps",
        "eval_reward",
        "eval_cov",
        "eval_qos",
        "eval_thr",
        "env_tail",
        "disc_tail",
        "rec_tail",
        "bh_frac",
        "bh_thr",
        "life_het",
        "sync",
        "renew_corr",
        "dur_mi",
        "dur_ret_rng",
        "dur_rec_rng",
        "p2_avail",
        "p2_rec_corr",
        "p2_partial",
        "topo_active",
        "topo_rew",
    ]
    print("\t".join(header))

    for csv_path in csv_paths:
        run_dir = csv_path.parents[1]
        rows = read_updates(csv_path)
        if not rows:
            continue
        last = rows[-1]
        tail_rows = rows[-max(int(tail), 1) :]
        latest_eval = read_latest_eval(run_dir)
        eval_steps = eval_reward = eval_cov = eval_qos = eval_thr = "-"
        if latest_eval is not None:
            eval_steps = str(int(latest_eval["steps"]))
            eval_reward = fmt(latest_eval["reward"])
            eval_cov = fmt(latest_eval["coverage"])
            eval_qos = fmt(latest_eval["qos"])
            eval_thr = fmt(latest_eval["throughput"])

        values = {
            key: mean(tail_rows, key)
            for key in UPDATE_KEYS
        }
        fields = [
            run_dir.name,
            str(int(as_float(last, "total_steps"))),
            eval_steps,
            eval_reward,
            eval_cov,
            eval_qos,
            eval_thr,
            fmt(values["env_reward_mean"]),
            fmt(values["credit_full_disconnect_mean"]),
            fmt(values["credit_recovery_rate"]),
            fmt(values["credit_backhaul_connected_step_fraction"]),
            fmt(values["credit_throughput_when_backhaul_connected_mbps"]),
            fmt(values["lifetime_heterogeneity"]),
            fmt(values["renewal_full_sync_rate"]),
            fmt(values["renewal_pairwise_corr_mean"]),
            fmt(values["duration_agent_mi"]),
            fmt(values["duration_return_range"]),
            fmt(values["duration_recovery_range"]),
            fmt(values["p2_available_frac"]),
            fmt(values["p2_corr_phi_recovery_event"]),
            fmt(values["p2_partial_recovery_frac"]),
            fmt(values["topology_potential_active"]),
            fmt(values["topology_potential_reward_mean"], digits=5),
        ]
        print("\t".join(fields))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-root", default="logs/local_s7s1_overnight")
    parser.add_argument("--tail", type=int, default=5)
    args = parser.parse_args()
    return summarize(Path(args.log_root), tail=args.tail)


if __name__ == "__main__":
    raise SystemExit(main())
