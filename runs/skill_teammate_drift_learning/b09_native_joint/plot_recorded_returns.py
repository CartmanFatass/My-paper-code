"""Plot all B09 primary trajectories; zero new simulation or learner calls."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


root = Path(__file__).resolve().parent
fig, axes = plt.subplots(3, 4, figsize=(12, 7), sharex=True, sharey=True)
seed_means = []
for row, seed in enumerate((95401, 95402, 95403)):
    values = []
    with np.load(root/f"seed_{seed}"/"evaluation.npz", allow_pickle=False) as data:
        for episode in range(4):
            common = (data["snapshot_step"] == 64) & (data["episode"] == episode)
            j = data["adapter_reward"][common & (data["view"] == 0)]
            m = data["adapter_reward"][common & (data["view"] == 1)]
            difference = np.cumsum(j-m)
            values.append(float(difference[-1]))
            ax = axes[row, episode]
            ax.axhline(0, color="0.6", linewidth=.8)
            ax.plot(np.arange(1, 65), difference, color="#246c82", linewidth=1.8)
            ax.scatter([64], [difference[-1]], color="#246c82", s=13)
            ax.set_title(f"Seed {seed}, episode {episode}: {difference[-1]:+.3f}", fontsize=9)
            ax.set_xlim(0, 66)
            ax.set_ylim(-2.1, 7.6)
            ax.grid(axis="y", alpha=.18)
            if episode == 0:
                ax.set_ylabel("Cumulative J minus M")
            if row == 2:
                ax.set_xlabel("Native tick")
    seed_means.append(float(np.mean(values)))
fig.suptitle("B09: all recorded primary episode return differences", fontsize=15)
fig.text(.5, .02,
         "Frozen target-64 models; actual native adapter reward (team reward / 3). "
         "Shared scales; no episodes omitted.\n"
         f"Seed means: {seed_means[0]:+.3f}, {seed_means[1]:+.3f}, {seed_means[2]:+.3f}. "
         "Episodes are nested observations, not independent training repetitions.",
         ha="center", fontsize=9)
fig.tight_layout(rect=(0, .065, 1, .94))
fig.savefig(root/"recorded_primary_returns.png", dpi=160)
fig.savefig(root/"recorded_primary_returns.pdf")
plt.close(fig)
print("Rendered all 12 stored primary episode differences; no new experiment.")
