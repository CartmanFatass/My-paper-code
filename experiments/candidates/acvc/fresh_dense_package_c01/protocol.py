"""Fixed C01 identities and complete-fit-panel analysis; no learner imports."""
import argparse
import json
import math
from pathlib import Path
import statistics


OBJECT = "ACVC_FRESH_DENSE_PACKAGE_C01"
CARD = "docs/research/candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_SCIENCE_CARD_20260911.md"
UNITS = ((12794, 23947), (11477, 24930), (18150, 21370),
         (12604, 21030), (14295, 23946))
ARMS = ("C", "F", "dwell")
PRIMARIES = ("F-C", "F-dwell")
CONTRASTS = (("F", "C"), ("F", "dwell"), ("dwell", "C"))
MARGIN = 0.01
CAPS = {"whole_supervised_task": 270, "native_sum": 1350,
        "cumulative_runtime_support": 1650, "complete_charge": 3000}
QUALIFICATION = (
    "Provisional single-task, complete-package inference: 97.5% two-sided marginal "
    "and at least 95% simultaneous coverage only under iid-normal complete "
    "fit-panel means; actual neural-training calibration is not established."
)


def interval_reading(lower, upper):
    if upper < 0:
        return "BELOW_ZERO"
    if upper <= MARGIN:
        return "AT_OR_BELOW_MEI"
    if lower > MARGIN:
        return "ABOVE_MEI"
    return "UNRESOLVED"


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


def read_unit(root, master, namespace):
    path = Path(root) / f"unit_{master}"
    result = {"master": master, "evaluation_namespace": namespace,
              "complete": False, "issues": [], "contrasts": {}}
    issues = result["issues"]
    try:
        summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        issues.append(f"summary unavailable: {type(error).__name__}")
        summary = {}
    result["launch_sha"] = summary.get("launch_sha")
    result["resources"] = summary.get("resources", "resources_unmeasured")
    result["counts"] = summary.get("counts", {})
    if (summary.get("status") != "complete" or summary.get("object") != OBJECT
            or summary.get("master") != master
            or summary.get("evaluation_namespace") != namespace
            or not summary.get("fit_complete") or not summary.get("checkpoint_complete")):
        issues.append("unit identity, fit, checkpoint or completion does not match C01")
    required_counts = {"train_episodes": 512, "eval_episodes": 192,
                       "train_team_steps": 131072, "eval_team_steps": 49152,
                       "optimizer_steps": 1024, "update_records": 1024,
                       "new_fits": 1, "post_fit_loads": 3}
    if any(result["counts"].get(key) != value for key, value in required_counts.items()):
        issues.append("required complete learner/panel counts are missing")
    rows = _json_lines(path / "episodes.jsonl", issues)
    training = [row for row in rows if row.get("phase") == "train"]
    evaluation = [row for row in rows if row.get("phase") == "eval"]
    if (len(training) != 512 or [row.get("episode") for row in training] != list(range(512))
            or any(row.get("master") != master or row.get("base") != master
                   or row.get("reset_seed") != 100000 * master + 1000 + e
                   or row.get("steps") != 256
                   or not isinstance(row.get("J"), (int, float)) or not math.isfinite(row["J"])
                   or not isinstance(row.get("S"), (int, float)) or not math.isfinite(row["S"])
                   or row["J"] != row["S"] / 256 for e, row in enumerate(training))):
        issues.append("training episode identities or complete reset sequence differ")
    result["training_curve_J"] = [row.get("J") for row in training]
    updates = _json_lines(path / "updates.jsonl", issues)
    if (len(updates) != 1024 or any(
            row.get("master") != master or row.get("rollout") != k // 4
            or row.get("epoch") != k % 4
            or row.get("episodes") != [2 * (k // 4), 2 * (k // 4) + 1]
            for k, row in enumerate(updates))):
        issues.append("full ordered four-epoch update records differ")
    keys = [(row.get("arm"), row.get("episode")) for row in evaluation]
    expected = {(arm, e) for arm in ARMS for e in range(64)}
    if len(keys) != 192 or set(keys) != expected:
        issues.append("final panels are missing, duplicate or have unexpected world keys")
    values = {}
    for row in evaluation:
        arm, e = row.get("arm"), row.get("episode")
        value, total = row.get("J"), row.get("S")
        if ((arm, e) not in expected or row.get("base") != master
                or row.get("evaluation_namespace") != namespace
                or row.get("reset_seed") != 100000 * namespace + 2000 + e
                or row.get("steps") != 256
                or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not isinstance(total, (int, float)) or not math.isfinite(total)
                or value != total / 256):
            issues.append("final row identity, world pairing or native J=S/256 differs")
            continue
        values[(arm, e)] = value
    for first, second in CONTRASTS:
        episodes = [e for e in range(64) if (first, e) in values and (second, e) in values]
        differences = [values[(first, e)] - values[(second, e)] for e in episodes]
        result["contrasts"][f"{first}-{second}"] = {
            "panel_complete": len(episodes) == 64,
            "episode_ids": episodes, "paired_differences_J": differences,
            "mean_J": statistics.fmean(differences) if differences else None,
            "conditional_SE_J": (statistics.stdev(differences) / math.sqrt(len(differences))
                                 if len(differences) > 1 else None),
            "adverse_episode_ids": [e for e, value in zip(episodes, differences) if value < 0],
            "minimum_J": min(differences) if differences else None,
        }
    result["arm_mean_J"] = {
        arm: statistics.fmean(values[(arm, e)] for e in range(64))
        if all((arm, e) in values for e in range(64)) else None for arm in ARMS
    }
    result["intervention_by_rule"] = summary.get("intervention_by_rule")
    result["complete"] = not issues
    return result


def aggregate(units):
    complete = ([(unit["master"], unit["evaluation_namespace"]) for unit in units] == list(UNITS)
                and all(unit["complete"] for unit in units))
    result = {"object": OBJECT, "card": CARD, "complete": complete, "units": units,
              "independent_unit": "one fresh complete fit plus its finite three-rule panel",
              "qualification": QUALIFICATION, "margin_J": MARGIN,
              "primary": None, "joint_reading": "INCOMPLETE", "caps_s": CAPS}
    if not complete:
        result["limit"] = "No five-unit population interval or successful-survivor substitute."
        return result
    from scipy.stats import t

    critical = float(t.ppf(0.9875, 4))
    primary = {}
    for contrast in PRIMARIES:
        means = [unit["contrasts"][contrast]["mean_J"] for unit in units]
        mean = statistics.fmean(means)
        sd = statistics.stdev(means)
        se = sd / math.sqrt(5)
        lower, upper = mean - critical * se, mean + critical * se
        primary[contrast] = {"unit_means_J": means, "mean_J": mean, "sample_SD_J": sd,
                             "fit_panel_SE_J": se, "lower_J": lower, "upper_J": upper,
                             "reading": interval_reading(lower, upper)}
    result["t_quantile"] = {"probability": 0.9875, "df": 4, "value": critical}
    result["primary"] = primary
    result["joint_reading"] = (
        "JOINT_ABOVE_MEI" if all(x["lower_J"] > MARGIN for x in primary.values())
        else "JOINT_NOT_ESTABLISHED"
    )
    result["secondary_dwell_C_mean_J"] = statistics.fmean(
        unit["contrasts"]["dwell-C"]["mean_J"] for unit in units)
    return result


def analyze(root):
    return aggregate([read_unit(root, master, namespace) for master, namespace in UNITS])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.root)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"complete": result["complete"], "joint_reading": result["joint_reading"]}))


if __name__ == "__main__":
    main()
