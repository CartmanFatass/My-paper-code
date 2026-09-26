"""Plot all stored B10 primary paths; no simulation, model query or fitting."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


root = Path(__file__).resolve().parent
fig, axes = plt.subplots(3, 4, figsize=(12, 7), sharex=True, sharey=True)
for row, seed in enumerate((95401, 95402, 95403)):
    with np.load(root / f"seed_{seed}" / "trajectory.npz", allow_pickle=False) as data:
        for episode in range(4):
            common = data["episode"] == episode
            rewards = [data["adapter_reward"][common & (data["policy_index"] == p)]
                       for p in range(4)]
            assert all(r.shape == (64,) for r in rewards)
            assert np.array_equal(rewards[1], rewards[3])
            ax = axes[row, episode]
            ax.axhline(0, color="0.6", linewidth=.8)
            for baseline, label, color in ((2, "J minus IN", "#246c82"),
                                            (3, "J minus OUT (= J minus M)", "#c46b24")):
                difference = np.cumsum(rewards[0] - rewards[baseline])
                ax.plot(np.arange(1, 65), difference, color=color, linewidth=1.6,
                        label=label if row == 0 and episode == 0 else None)
                ax.scatter([64], [difference[-1]], color=color, s=10)
            ax.set_title(f"Base {seed}, world {episode}", fontsize=9)
            ax.set_xlim(0, 66)
            ax.set_ylim(-5, 10)
            ax.grid(axis="y", alpha=.18)
            if row == 2:
                ax.set_xlabel("Native tick")
fig.supylabel("Cumulative return difference", fontsize=11)
fig.suptitle("B10: all 12 fresh paired worlds, three previously exposed models", fontsize=14)
fig.legend(loc="upper center", bbox_to_anchor=(.5, .94), ncol=2, frameon=False)
fig.text(.5, .02,
         "Actual adapter reward (team reward / 3); shared axes, every world retained. "
         "No per-world best-rule selection.\n"
         "Zero new fits. These worlds add conditional deployment evidence, not fresh training replications.",
         ha="center", fontsize=9)
fig.tight_layout(rect=(0, .065, 1, .90))
fig.savefig(root / "recorded_primary_returns.png", dpi=160)
fig.savefig(root / "recorded_primary_returns.pdf")
plt.close(fig)
print("Rendered all 12 B10 paired worlds from saved rewards; no new experiment.")
