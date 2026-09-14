"""Recorded-data intake for one ACVC 1024/4096 programme; never loads a model."""
import argparse
import json
from pathlib import Path

import numpy as np


def describe(values):
    a = np.asarray(values, dtype=np.float64)
    return dict(mean=float(a.mean()), sd=float(a.std(ddof=1)),
                conditional_se=float(a.std(ddof=1) / np.sqrt(a.size)),
                negative_ids=np.flatnonzero(a < 0).tolist(),
                zero_ids=np.flatnonzero(a == 0).tolist(),
                minimum=float(a.min()), maximum=float(a.max()), values=a.tolist())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    raw = args.native_dir
    summary = json.loads((raw / "summary.json").read_text())
    rows = [json.loads(line) for line in (raw / "episodes.jsonl").read_text().splitlines()]
    updates = [json.loads(line) for line in (raw / "updates.jsonl").read_text().splitlines()]
    train = [row for row in rows if row["phase"] == "train"]
    evaluation = [row for row in rows if row["phase"] == "eval"]
    assert summary["status"] == "complete"
    assert len(train) == 4096 and len(evaluation) == 384 and len(updates) == 8192
    assert [r["episode"] for r in train] == list(range(4096))
    assert all(r["reset_seed"] == 27457 * 100000 + 1000 + r["episode"] for r in train)
    assert all(r["steps"] == 256 and r["J"] == r["S"] / 256 for r in rows)
    for row in rows + updates:
        assert all(np.isfinite(v) for v in row.values() if isinstance(v, (int, float)))
    assert [(r["rollout"], r["epoch"], r["episodes"]) for r in updates] == [
        (i // 4, i % 4, [2 * (i // 4), 2 * (i // 4) + 1]) for i in range(8192)]
    expected_counts = dict(train_episodes=4096, eval_episodes=384, optimizer_steps=8192,
                           update_records=8192, team_steps=1146880, fixed_snapshots=2,
                           post_fit_loads=6, new_fits=1)
    assert all(summary["counts"][key] == value for key, value in expected_counts.items())
    result = dict(object=summary["object"], launch_sha=summary["launch_sha"],
                  independent_training_programmes=1, raw_record_checks="passed",
                  counts=summary["counts"], endpoints={}, changes={}, training_blocks=[],
                  exposure=summary["checkpoint_exposures"],
                  intervention_counts=summary["intervention_by_checkpoint_rule"],
                  parameters=summary["parameters"], native_time=(raw / "native_time.txt").read_text(),
                  inference="One correlated learning programme; finite worlds conditional, not training replication.")
    panels = {}
    for stage in (1024, 4096):
        panels[stage] = {}
        for arm in ("C", "F", "dwell"):
            selected = sorted((r for r in evaluation if r["checkpoint_episode"] == stage
                               and r["arm"] == arm), key=lambda r: r["episode"])
            assert len(selected) == 64 and [r["episode"] for r in selected] == list(range(64))
            assert all(r["reset_seed"] == 37457 * 100000 + 2000 + r["episode"]
                       and r["evaluation_namespace"] == 37457 and r["base"] == 27457 for r in selected)
            panels[stage][arm] = np.asarray([r["J"] for r in selected], dtype=np.float64)
        entry = dict(arms={arm: describe(v) for arm, v in panels[stage].items()}, contrasts={})
        for a, b in (("F", "C"), ("F", "dwell"), ("dwell", "C")):
            values = panels[stage][a] - panels[stage][b]
            entry["contrasts"][f"{a}-{b}"] = describe(values)
            published = summary["primary"]["endpoints"][str(stage)]["contrasts"][f"{a}-{b}"]
            assert np.allclose(values, published["paired_differences_J"], rtol=1e-10, atol=1e-12)
            assert np.isclose(values.mean(), published["mean_J"], rtol=1e-10, atol=1e-12)
            assert np.isclose(values.std(ddof=1)/8, published["conditional_SE_J"], rtol=1e-10, atol=1e-12)
            entry["contrasts"][f"{a}-{b}"]["reading"] = published["reading"]
        result["endpoints"][str(stage)] = entry
    for control in ("C", "dwell"):
        early = panels[1024]["F"] - panels[1024][control]
        late = panels[4096]["F"] - panels[4096][control]
        values = late - early
        published = summary["primary"]["changes"][f"G_{control}"]
        assert np.allclose(values, published["paired_difference_of_differences_J"], rtol=1e-10, atol=1e-12)
        assert np.isclose(values.std(ddof=1)/8, published["conditional_SE_J"], rtol=1e-10, atol=1e-12)
        result["changes"][f"G_{control}"] = dict(describe(values), reading=published["reading"],
                                                  endpoint_sample_covariance=float(np.cov(early, late)[0, 1]))
    result["absolute_changes"] = {arm: describe(panels[4096][arm] - panels[1024][arm])
                                   for arm in ("C", "F", "dwell")}
    for start in range(0, 4096, 128):
        result["training_blocks"].append(dict(first_episode=start, last_episode=start+127,
                                               mean_J=float(np.mean([r["J"] for r in train[start:start+128]]))))
    result["update_summary"] = {key: dict(minimum=min(r[key] for r in updates),
                                         maximum=max(r[key] for r in updates),
                                         mean=float(np.mean([r[key] for r in updates])))
                                for key in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm")}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "INTAKE_ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    colors = dict(C="#526177", F="#b34622", dwell="#36856e")
    for arm, color in colors.items():
        axes[0].plot([1024, 4096], [panels[s][arm].mean() for s in (1024, 4096)],
                     "o-", label=arm, color=color)
    axes[0].set(title="Attained endpoint means", xlabel="Training episodes", ylabel="Native J")
    axes[0].legend()
    for control, color in (("C", "#526177"), ("dwell", "#36856e")):
        values = [panels[s]["F"] - panels[s][control] for s in (1024, 4096)]
        axes[1].errorbar([1024, 4096], [v.mean() for v in values],
                         yerr=[v.std(ddof=1)/8 for v in values], marker="o", color=color,
                         label=f"F minus {control}", capsize=3)
    axes[1].axhline(.01, color="black", linestyle="--", linewidth=.8)
    axes[1].axhline(0, color="gray", linewidth=.6)
    axes[1].set(title="Increments (conditional ±1 SE)", xlabel="Training episodes", ylabel="Paired J increment")
    axes[1].legend()
    axes[2].plot([r["last_episode"]+1 for r in result["training_blocks"]],
                 [r["mean_J"] for r in result["training_blocks"]], color=colors["C"])
    axes[2].set(title="C training, 128-episode blocks", xlabel="Training episodes", ylabel="Exploratory training J")
    fig.suptitle("One fresh programme; correlated snapshots, 64 conditional worlds")
    fig.tight_layout()
    fig.savefig(args.out / "RESULT_FIGURE.png", dpi=170)
    plt.close(fig)
    print(json.dumps({"endpoints": {s: {k: dict(mean=v["mean"], se=v["conditional_se"],
                      negative=len(v["negative_ids"]), reading=v["reading"])
                      for k, v in e["contrasts"].items()} for s, e in result["endpoints"].items()},
                      "changes": {k: dict(mean=v["mean"], se=v["conditional_se"], reading=v["reading"])
                                  for k, v in result["changes"].items()}}, indent=2))


if __name__ == "__main__":
    main()
