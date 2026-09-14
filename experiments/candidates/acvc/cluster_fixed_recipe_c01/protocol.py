"""Fixed indexed clustered fits and complete six-unit C01 inference."""
import argparse
import json
import math
from pathlib import Path
import signal
import statistics
import time

from experiments.candidates.acvc.cluster_deployment_b01 import protocol as shared


OBJECT = "ACVC_CLUSTER_FIXED_RECIPE_C01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_RECIPE_C01_SCIENCE_CARD_20260914.md"
UNITS = (
    (1, 13783, 22845),
    (2, 17291, 22568),
    (3, 14179, 21574),
    (4, 13325, 26056),
    (5, 11751, 28453),
    (6, 17639, 20217),
)
ARMS = ("C", "F", "dwell")
CONTRASTS = (("F", "C"), ("F", "dwell"), ("dwell", "C"))
PRIMARIES = ("F-C", "F-dwell")
TRAIN_EPISODES = 1024
EVAL_EPISODES = 64
MARGIN = 0.01
CRITICAL = 3.1633814497486235
INNER_TIMEOUT_SECONDS = 1800.0
PLANNING_SECONDS = {
    "whole_supervised_task": 500,
    "native_sum": 3000,
    "cumulative_runtime_support": 4800,
    "complete_charge": 7800,
}
QUALIFICATION = (
    "Provisional single-task complete-package inference: the two 97.5% two-sided "
    "marginal intervals provide at least 95% simultaneous coverage only under the "
    "prespecified iid-normal working model for complete fit-panel contrast means; "
    "actual neural-training calibration is not established."
)
make_cluster = shared.make_cluster


def unit_identity(unit_index):
    return UNITS[unit_index - 1]


def interval_reading(lower, upper):
    if upper < 0:
        return "BELOW_ZERO"
    if upper <= MARGIN:
        return "AT_OR_BELOW_MEI"
    if lower > MARGIN:
        return "ABOVE_MEI"
    return "UNRESOLVED"


def _write_summary_readback(path, summary):
    payload = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8")
    if path.read_text(encoding="utf-8") != payload:
        raise RuntimeError("fixed-recipe summary readback differs")


def publish(output, process_start, unit_index, *, clock=None):
    clock = time.monotonic if clock is None else clock
    _, master, namespace = unit_identity(unit_index)
    path = Path(output) / "summary.json"
    now = clock()
    remaining = INNER_TIMEOUT_SECONDS - (now - process_start)
    if remaining <= 0:
        raise TimeoutError(f"{OBJECT} complete invocation timed out before publication")
    old_handler = None
    alarm_installed = False

    def timeout(*_):
        raise TimeoutError(f"{OBJECT} complete invocation timed out during publication")

    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, remaining))
        alarm_installed = True
    try:
        complete = shared.publish(
            output, process_start, master=master, evaluation_namespace=namespace
        )
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary.update(
            unit_index=unit_index,
            indexed_identity={
                "unit_index": unit_index,
                "master": master,
                "evaluation_namespace": namespace,
            },
            population=(
                "One fresh complete clustered C fit and its finite C/F/dwell panel; "
                "unit index remains identity even if numerical seed pairs repeat."
            ),
        )
        summary["configuration"].update(
            fixed_recipe="clustered_C_only_1024_final_only",
            unit_index=unit_index,
        )
        pre_write_elapsed = clock() - process_start
        summary["complete_invocation_timeout"] = {
            "limit_s": INNER_TIMEOUT_SECONDS,
            "boundary": (
                "process start before imports through clustered publication, fixed-recipe "
                "publication and final summary readback"
            ),
            "pre_final_summary_write_elapsed_s": pre_write_elapsed,
            "publication_payload_readback_elapsed_s": None,
            "final_readback_check": "requires zero process exit and native_time wall<1800s",
        }
        if pre_write_elapsed >= INNER_TIMEOUT_SECONDS:
            raise TimeoutError(f"{OBJECT} timed out before final summary write")
        _write_summary_readback(path, summary)
        first_readback_elapsed = clock() - process_start
        if first_readback_elapsed >= INNER_TIMEOUT_SECONDS:
            summary["status"] = "incomplete"
            summary["error"] = f"TimeoutError: {OBJECT} final summary readback crossed 1800s"
            summary["complete_invocation_timeout"].update(
                publication_payload_readback_elapsed_s=first_readback_elapsed,
                final_readback_within_limit=False,
            )
            _write_summary_readback(path, summary)
            return False
        summary["complete_invocation_timeout"].update(
            publication_payload_readback_elapsed_s=first_readback_elapsed,
            final_readback_within_limit=True,
        )
        _write_summary_readback(path, summary)
        final_readback_elapsed = clock() - process_start
        if final_readback_elapsed >= INNER_TIMEOUT_SECONDS:
            summary["status"] = "incomplete"
            summary["error"] = f"TimeoutError: {OBJECT} final evidence readback crossed 1800s"
            summary["complete_invocation_timeout"].update(
                final_readback_within_limit=False,
                failed_final_readback_elapsed_s=final_readback_elapsed,
            )
            _write_summary_readback(path, summary)
            return False
        return complete and summary["status"] == "complete"
    finally:
        if alarm_installed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)


def _json_lines(path, issues):
    if not path.exists():
        issues.append(f"missing {path.name}")
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            issues.append(f"incomplete JSON at {path.name}:{line_number}")
            break
    return rows


def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _native_resources(path, issues):
    try:
        lines = (path / "native_time.txt").read_text(encoding="utf-8").splitlines()
        fields = dict(line.split("=", 1) for line in lines)
        if set(fields) != {"native_wall_s", "user_cpu_s", "system_cpu_s",
                           "peak_rss_kib", "exit_code"}:
            raise ValueError("unexpected native time fields")
        result = {
            "native_wall_s": float(fields["native_wall_s"]),
            "user_cpu_s": float(fields["user_cpu_s"]),
            "system_cpu_s": float(fields["system_cpu_s"]),
            "peak_rss_kib": int(fields["peak_rss_kib"]),
            "exit_code": int(fields["exit_code"]),
        }
        if (not all(math.isfinite(result[key]) and result[key] >= 0
                    for key in ("native_wall_s", "user_cpu_s", "system_cpu_s"))
                or result["peak_rss_kib"] <= 0 or result["exit_code"] != 0
                or result["native_wall_s"] >= INNER_TIMEOUT_SECONDS):
            raise ValueError("native resource or successful inner-time boundary differs")
        return result
    except (FileNotFoundError, UnicodeDecodeError, ValueError) as error:
        issues.append(f"native time/CPU/RSS evidence unavailable: {type(error).__name__}: {error}")
        return None


def read_unit(root, unit_index, master, namespace, launch_sha):
    path = Path(root) / f"unit_{unit_index:02d}"
    result = {
        "unit_index": unit_index,
        "master": master,
        "evaluation_namespace": namespace,
        "path": str(path),
        "complete": False,
        "issues": [],
        "contrasts": {},
    }
    issues = result["issues"]
    try:
        summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        issues.append(f"summary unavailable: {type(error).__name__}")
        summary = {}
    result["summary"] = summary
    result["native_resources"] = _native_resources(path, issues)
    identity = summary.get("indexed_identity", {})
    if (
        summary.get("status") != "complete"
        or summary.get("object") != OBJECT
        or summary.get("unit_index") != unit_index
        or summary.get("master") != master
        or summary.get("evaluation_namespace") != namespace
        or summary.get("launch_sha") != launch_sha
        or identity != {
            "unit_index": unit_index,
            "master": master,
            "evaluation_namespace": namespace,
        }
        or not summary.get("fit_complete")
        or not summary.get("checkpoint_complete")
    ):
        issues.append("unit identity, launch SHA, fit, checkpoint or completion differs")

    counts = summary.get("counts", {})
    required_counts = {
        "train_episodes": 1024,
        "eval_episodes": 192,
        "train_team_steps": 262144,
        "eval_team_steps": 49152,
        "optimizer_steps": 2048,
        "backward_calls": 2048,
        "update_records": 2048,
        "rollouts": 512,
        "new_fits": 1,
        "final_checkpoints": 1,
        "selected_final_checkpoints": 1,
        "post_fit_loads": 3,
        "environment_constructors": 4,
    }
    if any(counts.get(key) != value for key, value in required_counts.items()):
        issues.append("required complete learner/panel counts differ")
    configuration = summary.get("configuration", {})
    required_configuration = {
        "horizon": 256,
        "training_episodes": 1024,
        "episodes_per_rollout": 2,
        "ppo_epochs_per_rollout": 4,
        "chunk": 32,
        "evaluation_episodes_per_arm": 64,
        "evaluation_order": list(ARMS),
        "ratio_grouping": "agent_compound",
        "value_moments": None,
        "renewal": False,
        "duration_support": [1, 4],
        "velocity_mode": "sampled",
        "entropy_coef": 0.01,
        "device": "cpu",
        "dtype": "float32",
        "intraop_threads": 1,
        "interop_threads": 1,
        "training_rule": "C",
        "user_distribution": "cluster",
        "fixed_recipe": "clustered_C_only_1024_final_only",
        "unit_index": unit_index,
    }
    if any(configuration.get(key) != value for key, value in required_configuration.items()):
        issues.append("frozen clustered learner configuration differs")
    timeout_evidence = summary.get("complete_invocation_timeout", {})
    if (
        timeout_evidence.get("limit_s") != INNER_TIMEOUT_SECONDS
        or timeout_evidence.get("boundary") != (
            "process start before imports through clustered publication, fixed-recipe "
            "publication and final summary readback"
        )
        or not _finite_number(timeout_evidence.get("pre_final_summary_write_elapsed_s"))
        or not 0 <= timeout_evidence["pre_final_summary_write_elapsed_s"] < INNER_TIMEOUT_SECONDS
        or not _finite_number(timeout_evidence.get("publication_payload_readback_elapsed_s"))
        or not 0 <= timeout_evidence["publication_payload_readback_elapsed_s"] < INNER_TIMEOUT_SECONDS
        or timeout_evidence.get("final_readback_within_limit") is not True
        or timeout_evidence.get("final_readback_check") != (
            "requires zero process exit and native_time wall<1800s"
        )
    ):
        issues.append("complete-invocation timeout/publication evidence differs")
    if not (path / "final_DENSE.pt").is_file():
        issues.append("final checkpoint file is missing")

    rows = _json_lines(path / "episodes.jsonl", issues)
    training = [row for row in rows if row.get("phase") == "train"]
    evaluation = [row for row in rows if row.get("phase") == "eval"]
    if (
        len(training) != 1024
        or [row.get("episode") for row in training] != list(range(1024))
        or any(
            row.get("master") != master
            or row.get("base") != master
            or row.get("reset_seed") != 100000 * master + 1000 + episode
            or row.get("steps") != 256
            or not _finite_number(row.get("J"))
            or not _finite_number(row.get("S"))
            or row["J"] != row["S"] / 256
            for episode, row in enumerate(training)
        )
    ):
        issues.append("training episode identities, reset law or complete rows differ")
    updates = _json_lines(path / "updates.jsonl", issues)
    if (
        len(updates) != 2048
        or any(
            row.get("master") != master
            or row.get("rollout") != k // 4
            or row.get("epoch") != k % 4
            or row.get("episodes") != [2 * (k // 4), 2 * (k // 4) + 1]
            for k, row in enumerate(updates)
        )
    ):
        issues.append("full ordered four-epoch update records differ")

    expected_order = [(arm, episode) for arm in ARMS for episode in range(64)]
    expected_keys = set(expected_order)
    observed_order = [(row.get("arm"), row.get("episode")) for row in evaluation]
    if observed_order != expected_order:
        issues.append("final rows are missing, duplicate, unexpected or out of order")
    values = {}
    invalid_keys = set()
    for row in evaluation:
        arm, episode = row.get("arm"), row.get("episode")
        key = (arm, episode)
        value, total = row.get("J"), row.get("S")
        if (
            key not in expected_keys
            or row.get("base") != master
            or row.get("evaluation_namespace") != namespace
            or row.get("reset_seed") != 100000 * namespace + 2000 + episode
            or row.get("steps") != 256
            or not _finite_number(value)
            or not _finite_number(total)
            or value != total / 256
            or key in values
        ):
            invalid_keys.add(key)
            continue
        values[key] = value
    if invalid_keys or len(values) != 192:
        issues.append("final row identity, pairing, finiteness or native J=S/256 differs")

    for first, second in CONTRASTS:
        episode_ids = [
            episode for episode in range(64)
            if (first, episode) in values and (second, episode) in values
        ]
        differences = [
            values[(first, episode)] - values[(second, episode)]
            for episode in episode_ids
        ]
        result["contrasts"][f"{first}-{second}"] = {
            "panel_complete": len(episode_ids) == 64,
            "episode_ids": episode_ids,
            "paired_differences_J": differences,
            "mean_J": statistics.fmean(differences) if differences else None,
            "sample_SD_J": statistics.stdev(differences) if len(differences) > 1 else None,
            "conditional_SE_J": (
                statistics.stdev(differences) / math.sqrt(len(differences))
                if len(differences) > 1 else None
            ),
            "minimum_J": min(differences) if differences else None,
            "maximum_J": max(differences) if differences else None,
            "adverse_episode_ids": [
                episode for episode, value in zip(episode_ids, differences) if value < 0
            ],
            "favorable_episode_ids": [
                episode for episode, value in zip(episode_ids, differences) if value > 0
            ],
            "zero_episode_ids": [
                episode for episode, value in zip(episode_ids, differences) if value == 0
            ],
        }
    result["arm_mean_J"] = {
        arm: (
            statistics.fmean(values[(arm, episode)] for episode in range(64))
            if all((arm, episode) in values for episode in range(64)) else None
        )
        for arm in ARMS
    }
    result["training_records"] = training
    result["update_records"] = updates
    result["evaluation_records"] = evaluation
    result["complete"] = not issues
    return result


def aggregate(units, launch_sha):
    identities = [
        (unit.get("unit_index"), unit.get("master"), unit.get("evaluation_namespace"))
        for unit in units
    ]
    complete = identities == list(UNITS) and all(unit.get("complete") for unit in units)
    result = {
        "object": OBJECT,
        "card": CARD,
        "launch_sha": launch_sha,
        "complete": complete,
        "units": units,
        "independent_unit": "one fresh complete fit plus its finite three-arm final panel",
        "qualification": QUALIFICATION,
        "margin_J": MARGIN,
        "primary": None,
        "joint_reading": "INCOMPLETE",
        "planning_seconds": PLANNING_SECONDS,
    }
    if not complete:
        result["limit"] = (
            "No six-unit inference or successful-survivor substitute; all six original "
            "indexed identities are required."
        )
        return result

    from scipy.stats import t

    critical = float(t.ppf(0.9875, 5))
    primary = {}
    for contrast in PRIMARIES:
        means = [unit["contrasts"][contrast]["mean_J"] for unit in units]
        mean = statistics.fmean(means)
        sd = statistics.stdev(means)
        if sd == 0.0:
            primary[contrast] = {
                "unit_means_J": means,
                "mean_J": mean,
                "sample_SD_J": 0.0,
                "fit_panel_SE_J": 0.0,
                "lower_J": None,
                "upper_J": None,
                "reading": "ZERO_VARIANCE_UNRESOLVED",
            }
            continue
        se = sd / math.sqrt(6)
        lower, upper = mean - critical * se, mean + critical * se
        primary[contrast] = {
            "unit_means_J": means,
            "mean_J": mean,
            "sample_SD_J": sd,
            "fit_panel_SE_J": se,
            "lower_J": lower,
            "upper_J": upper,
            "reading": interval_reading(lower, upper),
        }
    result["t_quantile"] = {
        "probability": 0.9875,
        "df": 5,
        "value": critical,
        "frozen_reference": CRITICAL,
        "n_units": 6,
    }
    result["primary"] = primary
    result["joint_reading"] = (
        "JOINT_ABOVE_MEI"
        if all(item["lower_J"] is not None and item["lower_J"] > MARGIN
               for item in primary.values())
        else "JOINT_NOT_ESTABLISHED"
    )
    result["secondary_dwell_C_mean_J"] = statistics.fmean(
        unit["contrasts"]["dwell-C"]["mean_J"] for unit in units
    )
    return result


def analyze(root, launch_sha):
    return aggregate(
        [read_unit(root, unit, master, namespace, launch_sha)
         for unit, master, namespace in UNITS],
        launch_sha,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    result = analyze(args.root, args.launch_sha)
    args.output.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"complete": result["complete"],
                      "joint_reading": result["joint_reading"]}))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
