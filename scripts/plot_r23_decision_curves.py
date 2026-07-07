"""Plot the 6 R23 decision-critical curves from the downloaded logs (read-only)."""
from __future__ import annotations
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else (
    "dist/r23_extract/logs_cloud_r23_actionable_team_intent_64env/seed1")
ARMS = ["r23_arch_only", "r23_1_action", "r23_3_reward_coef005_floor005"]


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def col(rows, name):
    out = []
    for r in rows:
        try:
            out.append(float(r[name]))
        except (KeyError, ValueError):
            out.append(float("nan"))
    return out


def eval_by_step(rows, name):
    agg = {}
    for r in rows:
        s = int(float(r["total_steps"]))
        try:
            v = float(r.get(name, "nan") or "nan")
        except ValueError:
            v = float("nan")
        agg.setdefault(s, []).append(v)
    steps = sorted(agg)
    return steps, [sum(agg[s]) / len(agg[s]) for s in steps]


train = {a: read_csv(os.path.join(ROOT, a, "metrics/train_updates.csv")) for a in ARMS}
evals = {a: read_csv(os.path.join(ROOT, a, "metrics/eval_episodes.csv")) for a in ARMS}

fig, ax = plt.subplots(2, 3, figsize=(16, 8))
panels = [
    ("forced_Z_skill_KL / z_itv", [("g_itv_kl_skill", "-"), ("z_assignment_itv", "--")]),
    ("g_info MI (skill/dur)", [("g_info_skill_mi", "-"), ("g_info_duration_mi", "--")]),
    ("g_info loss", [("g_info_loss", "-")]),
    ("team_disc_acc (chance=1/6)", [("team_disc_acc", "-")]),
    ("team_disc residual / prior_entropy", [("team_disc_residual_mean", "-"), ("team_disc_prior_entropy", "--")]),
]
for i, (title, series) in enumerate(panels):
    a_ = ax[i // 3][i % 3]
    for arm in ARMS:
        x = col(train[arm], "update")
        for field, ls in series:
            a_.plot(x, col(train[arm], field), ls, label=f"{arm.split('_')[1]}:{field}")
    a_.set_title(title)
    a_.set_xlabel("update")
    a_.legend(fontsize=6)
    if "chance" in title:
        a_.axhline(1 / 6, color="k", lw=0.7, ls=":")

a_ = ax[1][2]
for arm in ARMS:
    xs, cov = eval_by_step(evals[arm], "coverage_ratio")
    _, eq1 = eval_by_step(evals[arm], "coverage_eq1_step_fraction")
    _, zt = eval_by_step(evals[arm], "zero_throughput_step_fraction")
    tag = arm.split("_")[1]
    a_.plot(xs, cov, "-o", label=f"{tag}:cov")
    a_.plot(xs, eq1, "-s", label=f"{tag}:eq1")
    a_.plot(xs, zt, "--", label=f"{tag}:zero_thr")
a_.set_title("task: cov / cov_eq1 / zero_thr")
a_.set_xlabel("steps")
a_.legend(fontsize=6)

fig.tight_layout()
out = os.path.join(os.path.dirname(ROOT.rstrip("/")), "r23_decision_curves.png")
fig.savefig(out, dpi=110)
print("wrote", out)

for arm in ARMS:
    kl = col(train[arm], "g_itv_kl_skill")
    mi = col(train[arm], "g_info_skill_mi")
    acc = col(train[arm], "team_disc_acc")
    print(f"{arm}: KL[0]={kl[0]:.4f} KL[-1]={kl[-1]:.4f} | MI[0]={mi[0]:.4f} MI[-1]={mi[-1]:.4f} "
          f"| disc_acc range [{min(acc):.3f},{max(acc):.3f}] (chance 0.167)")
