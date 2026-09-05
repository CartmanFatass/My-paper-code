"""Descriptive run-level summaries; no significance, exclusion or success decision."""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def describe(values):
    return {"n": len(values), "mean": statistics.mean(values),
            "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
            "min": min(values), "max": max(values)}


def summarize(path, baseline=None):
    groups = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"task", "seed", "arm", "score"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV requires task,seed,arm,score columns")
        for row in reader:
            task, seed, arm = (row[k].strip() for k in ("task", "seed", "arm"))
            score = float(row["score"])
            if not all((task, seed, arm)) or not math.isfinite(score):
                raise ValueError("IDs must be nonempty and scores finite")
            group = groups.setdefault((task, arm), {})
            if seed in group:
                raise ValueError("Duplicate task/arm/seed: aggregate episodes or select endpoint first")
            group[seed] = score
    if not groups:
        raise ValueError("No run rows")
    output = {"unit": "caller-declared independent training run",
              "inference": "descriptive only; no confidence interval or success classification",
              "groups": [], "paired_differences": []}
    for (task, arm), runs in sorted(groups.items()):
        output["groups"].append({"task": task, "arm": arm,
                                  **describe(list(runs.values())), "runs": runs})
        if baseline and arm != baseline:
            reference = groups.get((task, baseline), {})
            common = sorted(runs.keys() & reference.keys())
            differences = {seed: runs[seed] - reference[seed] for seed in common}
            output["paired_differences"].append({
                "task": task, "arm": arm, "baseline": baseline,
                "summary": describe(list(differences.values())) if common else None,
                "differences": differences,
                "unmatched_arm_seeds": sorted(runs.keys() - reference.keys()),
                "unmatched_baseline_seeds": sorted(reference.keys() - runs.keys())})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline")
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    result = summarize(args.csv, args.baseline)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        tasks = sorted({g["task"] for g in result["groups"]})
        fig, axes = plt.subplots(len(tasks), 1, figsize=(7, 3 * len(tasks)), squeeze=False)
        for ax, task in zip(axes[:, 0], tasks):
            selected = [g for g in result["groups"] if g["task"] == task]
            for i, group in enumerate(selected):
                values = list(group["runs"].values())
                ax.scatter([i] * len(values), values, alpha=.7)
                ax.scatter(i, group["mean"], marker="_", s=250, color="black")
            ax.set_xticks(range(len(selected)), [g["arm"] for g in selected])
            ax.set(title=task, ylabel="Declared endpoint score")
        fig.suptitle("Each point: training run; black mark: mean; no uncertainty interval")
        fig.tight_layout()
        args.plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.plot, dpi=150)
        plt.close(fig)
    print(args.out)


if __name__ == "__main__":
    main()
