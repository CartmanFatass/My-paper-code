"""Show every stored B11 paired-world contrast; no simulation or policy query."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


root = Path(__file__).resolve().parent
summary = json.loads((root / "summary.json").read_text())
reduction = summary["reduction"]
names = ("D_source", "D_target")
colors = ("#246c82", "#c46b24")
fig, axes = plt.subplots(3, 2, figsize=(11.5, 8), sharex=True, sharey=True)
for row, seed in enumerate(summary["seeds"]):
    for col, name in enumerate(names):
        values = np.asarray(reduction["paired_world_values_by_base"][name][row])
        assert values.shape == (16,)
        ax = axes[row, col]
        ax.axhline(0, color="0.4", linewidth=.8)
        ax.vlines(np.arange(16), 0, values, color=colors[col], alpha=.35, linewidth=1)
        ax.scatter(np.arange(16), values, color=colors[col], s=28, zorder=3)
        ax.axhline(values.mean(), color=colors[col], linestyle="--", linewidth=1.1)
        ax.set_title(f"Base {seed}: mean {values.mean():+.3f}; "
                     f"positive {np.count_nonzero(values > 0)}/16", fontsize=10)
        ax.set_xlim(-.7, 15.7)
        ax.set_ylim(-5, 14.5)
        ax.set_xticks(np.arange(0, 16, 3))
        ax.grid(axis="y", alpha=.16)
        if row == 2:
            ax.set_xlabel("Paired world (all 16 retained)")
fig.supylabel("64-tick adapter-return difference: matched minus mismatched table", fontsize=10)
fig.suptitle("B11: the two matching directions must be read separately", fontsize=14, y=.985)
fig.text(.29, .928, "Source law: source table minus target table", ha="center", fontsize=10)
fig.text(.76, .928, "Target law: target table minus source table", ha="center", fontsize=10)
means = reduction["equal_weight_three_base_means"]
errors = reduction["conditional_fixed_base_monte_carlo_standard_errors"]
fig.text(.5, .048,
         f"Equal-weight fixed-base means: D_source {means['D_source']:+.3f} "
         f"(conditional MCSE {errors['D_source']:.3f}); "
         f"D_target {means['D_target']:+.3f} (conditional MCSE {errors['D_target']:.3f}).\n"
         "Dashed lines: base means. Shared axes. Zero new fits; 48 paired worlds on three old bases.\n"
         "Conditional deployment uncertainty excludes learning uncertainty. No world removed or relabeled.",
         ha="center", va="center", fontsize=9)
fig.tight_layout(rect=(.015, .105, 1, .913))
fig.savefig(root / "recorded_primary_returns.png", dpi=160)
fig.savefig(root / "recorded_primary_returns.pdf")
plt.close(fig)
print("Rendered both B11 primary contrasts for all 48 worlds from saved outputs.")
