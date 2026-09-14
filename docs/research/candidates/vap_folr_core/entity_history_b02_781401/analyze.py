"""Recompute the frozen B02 observation; conditional panels are not training fits."""
import csv
import json
import math
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


root = Path(__file__).resolve().parent
arms = ("GENERIC_RETAIN", "BANK")
data = {arm: json.loads((root / f"{arm.split('_')[0]}_SUMMARY.json").read_text()) for arm in arms}
panels = {}
for arm, summary in data.items():
    assert summary["object"] == "FOLR_ENTITY_HISTORY_B02_781401" and summary["arm"] == arm
    assert summary["status"] == "complete"
    assert (summary["training_seed"], summary["evaluation_seed"]) == (781401, 1781401)
    assert tuple(summary[k] for k in ("training_episodes", "training_ticks", "optimizer_steps",
                                      "evaluation_episodes", "evaluation_ticks")) == (5000, 100000, 4969, 128, 2560)
    train, values = summary["training_returns"], summary["evaluation_returns"]
    assert len(train) == 5000 and len(values) == 128 and all(map(math.isfinite, train + values))
    sd = statistics.stdev(values)
    panel = dict(mean=statistics.mean(values), sample_sd=sd,
                 conditional_episode_se=sd / math.sqrt(128), minimum=min(values),
                 maximum=max(values), n=128, negative_episodes=sum(x < 0 for x in values))
    for key, value in summary["native_panel"].items():
        assert math.isclose(value, panel[key], rel_tol=1e-12, abs_tol=1e-12), key
    panels[arm] = panel

difference = panels["BANK"]["mean"] - panels["GENERIC_RETAIN"]["mean"]
rule = "BANK_ABOVE_MEI" if difference > 1 else "GENERIC_ABOVE_MEI" if difference < -1 else "WITHIN_MEI"
native = data["BANK"]["pair_primary"]
assert math.isclose(difference, native["bank_minus_generic"], rel_tol=1e-12, abs_tol=1e-12)
assert rule == native["rule"]
result = dict(object="FOLR_ENTITY_HISTORY_B02_781401", panels=panels,
              bank_minus_generic=difference, mei=1, rule=rule,
              fresh_fit_realizations=2, training_blocks=1, per_arm_training_runs=1,
              training_population_uncertainty=None, paired_episode_se=None,
              uncertainty="128 episodes per fitted policy; no exogenous pairing or across-training uncertainty estimate.",
              claim="Exploratory whole-learning-package comparison on this exact equally informed H20 host.")
(root / "RESULT_SUMMARY.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
with (root / "scores.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["task", "seed", "arm", "score"])
    writer.writerows(["FOLR_ENTITY_HISTORY_B02_H20", 781401, arm, panels[arm]["mean"]] for arm in arms)

fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
colors = {"GENERIC_RETAIN": "#0072B2", "BANK": "#D55E00"}
for arm in arms:
    train, values = data[arm]["training_returns"], sorted(data[arm]["evaluation_returns"])
    window_means = [statistics.mean(train[i:i + 100]) for i in range(0, 5000, 100)]
    axes[0].plot(range(100, 5001, 100), window_means, label=arm, color=colors[arm], linewidth=1.4)
    axes[1].step(values, [(i + 1) / 128 for i in range(128)], where="post",
                 label=f"{arm}: mean {panels[arm]['mean']:.3f}", color=colors[arm], linewidth=1.6)
axes[0].set(title="Training: fixed 100-episode means", xlabel="Training episodes", ylabel="Native team return")
axes[1].set(title="Final greedy panels: all 128 returns", xlabel="Native team return", ylabel="Empirical cumulative fraction")
axes[1].set_ylim(0, 1.02)
axes[1].axvline(0, color="#666666", linewidth=.7, linestyle=":")
for ax in axes:
    ax.grid(alpha=.18)
    ax.legend(fontsize=8, loc="best")
fig.suptitle(f"FOLR B02 | one fresh fit per arm | BANK minus Generic = {difference:.3f}", fontsize=11)
fig.savefig(root / "RESULT_FIGURE.png", dpi=180)
plt.close(fig)
print(json.dumps(result, allow_nan=False))
