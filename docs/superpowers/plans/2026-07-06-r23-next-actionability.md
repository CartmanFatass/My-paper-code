# R23-next: g-info audit → q_A actionability → q_D target audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After the R23 320k read (arch capacity PASS, g-info objective FAIL/null, q_D at chance), diagnose why g-info doesn't learn, then build the accepted successor mechanism: a q_A residual actionability discriminator `I(Z;ξ|c,ω)` and a reward-off q_D effect-target/timescale audit — all default-off, high-level only.

**Architecture:** HA-CTSE standalone three-timescale agent (`ha_ctse_process/standalone_agent.py`). The high-level `SkillDurationPolicy` already has the R23-0 residual path (`z_action_gain·W_Z(team_vector)` into skill/duration logits). The g-info objective (`g_info_objective.py`) enumerates team codes and applies a normalized-MI loss into the high update. New work adds a discriminative q_A head (cross-entropy, strong first-order gradient, unlike the self-stalling second-order MI) and a multi-target reward-off q_D probe.

**Tech Stack:** Python 3, PyTorch, gymnasium 1.0 / pettingzoo 1.24, pytest. Run everything from repo root so `config_1`, `ha_ctse_process`, `hmasd` resolve.

## Global Constraints

- Every new mechanism lands **default-off** behind a config flag + CLI flag; flag-off must keep the S-base path bit-identical.
- **High-level only.** No change to the low-level actor input: `a_i ~ π_l(o_i, z_i)` stays blind to Z/c/ξ.
- **No communication fields as intrinsic reward.** coverage/backhaul/recovery/topology are S7-S1 diagnostics, never intrinsic.
- q_A **may** read ξ (assignment). q_D used as a team-effect discriminator **must not** read ξ or assignment labels as a shortcut — it must recover Z from *future effect* only (context c,ω allowed). This is the PR-1 double-count contract (GPT 2026-07-06).
- Discriminator inputs are **detached** (q_A/q_D are not policy-gradient paths); each new discriminator gets its own optimizer.
- Reward paths are gated: q_A reward only after the q_A probe passes; q_D reward only after a q_D target shows non-chance residual. No q_D reward-on in this plan.
- TDD: write the failing test first, watch it fail, implement minimally, watch it pass, commit.
- Tests live under `tests/` (the tracked suite); run from repo root. Do **not** add root-level `test_*.py` (gitignored).
- No training run is launched by the implementer; the 320k mechanism matrix is prepared for the user's server.

## Key existing interfaces (verified, for reference)

```text
SkillDurationPolicy (standalone_agent.py:797)
  .z_action_gain: float                      # R23-0 residual gain (0.0 => residual modules absent)
  .z_skill_residual: nn.Linear(team_code_dim, n_skills) | None   # W_Z
  .z_duration_residual: nn.Linear(team_code_dim, n_durations) | None  # U_Z
  .input (LayerNorm+MLP trunk), .skill_head, .duration_head, .value_head
  .logits(obs, prev_skills, ages, compact, team_vector, omega=, agent_relevance=, ar_prefix=)
      -> (skill_logits, duration_logits, value)

CompactTeamBridge (standalone_agent.py:208)
  .code_embedding: nn.Embedding(num_team_codes, team_code_dim)   # Z embedding
  .num_team_codes, .bridge_type
  __call__(compact, forced_team_code=None) -> (team_code, team_vector, _, _, logits)

GInfoObjective (g_info_objective.py:69)
  .forward(high_policy=, bridge=, high_obs=, prev_skills=, ages=, compact=,
           omega=, agent_relevance=, total_steps=) -> (loss, metrics)
      loss = -coef_scale*(coef_skill*skill_mi + coef_duration*duration_mi)   # normalized MI
      metrics include g_info_skill_mi, g_itv_kl_skill (forced-Z skill KL), ...

TeamIntentDiscriminator (team_intent.py:83)
  __init__(state_dim, num_team_codes, hidden_dim=128)
  .losses(states, labels, prior_probs) -> {loss, logits, log_q, log_p, residual, acc, prior_entropy}
  .reward(states, labels, prior_probs, coef, clip) -> tensor   # no_grad

High update (standalone_agent.py:5567-5607): g_info_loss added into `loss`, single backward,
  self.high_opt.step(); self._last_forced_z_assignment_kl cached from g_itv_kl_skill.

Capacity-gate harness (scripts/r23_capacity_gate.py): builds cfg via train.load_config +
  apply_standalone_overrides + apply_checkpoint_structure, create_env, create_agent(cfg,args,env,
  num_envs=1,state_dim=sd); resets envs to build (states[R,sd], jobs[R,na,obs_dim]).
```

**Working hypothesis (to be confirmed by T2):** `_normalized_mi` is a near-second-order functional of the logits; when logits are nearly code-invariant (small `W_Z`), both the MI and `dMI/dW_Z` vanish, so the objective cannot bootstrap itself. This predicts the T2 audit shows *non-zero but tiny* g-info gradient to `z_skill_residual`/`code_embedding`, orders below PPO — i.e. "objective form unsuitable," not a wiring bug. q_A (cross-entropy) provides a first-order signal that does not vanish at low MI, which is why it is the accepted successor.

---

### Task 1: Plot the 6 decision curves (T1)

**Files:**
- Create: `scripts/plot_r23_decision_curves.py`
- Output: `dist/r23_extract/r23_decision_curves.png` (+ a printed text table)

**Interfaces:**
- Consumes: the 3 arms' `metrics/train_updates.csv` and `metrics/eval_episodes.csv` under
  `dist/r23_extract/logs_cloud_r23_actionable_team_intent_64env/seed1/{r23_arch_only,r23_1_action,r23_3_reward_coef005_floor005}`.
- Produces: a 6-panel figure and a console summary confirming GPT's A/B/C
  (arch KL stable early / g-info flat / disc at chance throughout).

- [ ] **Step 1: Write the script** (pure matplotlib + csv; no new deps)

```python
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
        try: out.append(float(r[name]))
        except (KeyError, ValueError): out.append(float("nan"))
    return out

def eval_by_step(rows, name):
    agg = {}
    for r in rows:
        s = int(float(r["total_steps"]))
        agg.setdefault(s, []).append(float(r.get(name, "nan") or "nan"))
    return sorted(agg), [sum(agg[s])/len(agg[s]) for s in sorted(agg)]

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
    a_.set_title(title); a_.set_xlabel("update"); a_.legend(fontsize=6)
    if "chance" in title: a_.axhline(1/6, color="k", lw=0.7, ls=":")
# task panel (eval)
a_ = ax[1][2]
for arm in ARMS:
    xs, cov = eval_by_step(evals[arm], "coverage_ratio")
    _, eq1 = eval_by_step(evals[arm], "coverage_eq1_step_fraction")
    _, zt = eval_by_step(evals[arm], "zero_throughput_step_fraction")
    a_.plot(xs, cov, "-o", label=f"{arm.split('_')[1]}:cov")
    a_.plot(xs, eq1, "-s", label=f"{arm.split('_')[1]}:eq1")
    a_.plot(xs, zt, "--", label=f"{arm.split('_')[1]}:zero_thr")
a_.set_title("task: cov / cov_eq1 / zero_thr"); a_.set_xlabel("steps"); a_.legend(fontsize=6)
fig.tight_layout()
out = os.path.join(os.path.dirname(ROOT.rstrip("/")), "r23_decision_curves.png")
fig.savefig(out, dpi=110)
print("wrote", out)
# console A/B/C confirmation
for arm in ARMS:
    kl = col(train[arm], "g_itv_kl_skill"); mi = col(train[arm], "g_info_skill_mi")
    acc = col(train[arm], "team_disc_acc")
    print(f"{arm}: KL[0]={kl[0]:.4f} KL[-1]={kl[-1]:.4f} | MI[0]={mi[0]:.4f} MI[-1]={mi[-1]:.4f} "
          f"| disc_acc range [{min(acc):.3f},{max(acc):.3f}] (chance 0.167)")
```

- [ ] **Step 2: Run it**

Run: `cd /c/project/HMASD && python scripts/plot_r23_decision_curves.py`
Expected: prints `wrote .../r23_decision_curves.png` and the A/B/C lines showing KL flat & elevated, MI flat, disc range straddling 0.167.

- [ ] **Step 3: Commit**

```bash
git add scripts/plot_r23_decision_curves.py
git commit -m "R23: decision-curve plotter for the 320k read"
```

---

### Task 2: g-info gradient audit (T2) — the decisive diagnostic

**Files:**
- Create: `scripts/r23_ginfo_grad_audit.py`

**Interfaces:**
- Consumes: the capacity-gate harness pattern (create_agent + env resets), `GInfoObjective.forward`,
  `SkillDurationPolicy` residual params, `bridge.code_embedding`.
- Produces: a printed report of grad-norms of the g-info loss w.r.t. {code_embedding,
  z_skill_residual, z_duration_residual, skill_head, duration_head, shared input trunk} and the
  ratio to a reference PPO-style policy-loss gradient; a wiring/scale/form classification.

- [ ] **Step 1: Write the audit script** (reuse the capacity-gate batch construction, but run WITH grad)

```python
"""R23 g-info gradient audit (diagnostic-only, single-batch backward, no training).

Answers: does the g-info loss actually move Z-embedding / assignment-head params, and
how large is that gradient vs a PPO-style policy-loss gradient on the same batch?
Classifies: wiring (grad~0) / scale (grad << PPO) / form (grad present but MI can't move).
"""
from __future__ import annotations
import argparse, sys, numpy as np, torch


def _build_high_batch(agent, states_np, jobs_np):
    """Reproduce the g-info high_obs/prev/ages/compact/omega/relevance batch (per-agent rows)."""
    dev = agent.device; na = int(agent.n_agents); R = states_np.shape[0]
    st = torch.as_tensor(states_np, dtype=torch.float32, device=dev)
    jo = torch.as_tensor(jobs_np, dtype=torch.float32, device=dev)
    compact, _cd, _cmi, weights, _ent, agent_rel = agent.compact(st, jo)
    B = R * na
    comp_b = compact.repeat_interleave(na, dim=0)
    obs_b = jo.reshape(B, agent.obs_dim)
    agent_ids = torch.arange(na, device=dev).repeat(R)
    prev_skills = torch.zeros(B, dtype=torch.long, device=dev)
    ages = torch.zeros(B, dtype=torch.float32, device=dev)
    omega_b = weights.repeat_interleave(na, dim=0) if agent.high_condition_on_omega else None
    rel_b = None
    if agent.use_agent_prototype_relevance:
        rel_b = agent_rel[torch.arange(R, device=dev).repeat_interleave(na), agent_ids]
    return obs_b, prev_skills, ages, comp_b, omega_b, rel_b


def _grad_norm(loss, params):
    ps = [p for p in params if p is not None and p.requires_grad]
    grads = torch.autograd.grad(loss, ps, retain_graph=True, allow_unused=True)
    tot = 0.0
    for g in grads:
        if g is not None:
            tot += float(g.detach().pow(2).sum().cpu())
    return tot ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="random")
    ap.add_argument("--structure-from", default="")
    ap.add_argument("--n-resets", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--gain", type=float, default=0.5)
    ap.add_argument("--coef-skill", type=float, default=0.02)
    a = ap.parse_args()

    struct_path = a.structure_from or (a.checkpoint if a.checkpoint != "random" else "")
    extra = f"--z_assignment_residual_gain {a.gain} --enable_g_info_objective --g_info_coef_skill {a.coef_skill}"
    base = ["train", "--config", "ha_ctse_process.config", "--scenario", "energy",
            "--preset", "S7-S1", "--n_agents", "6", "--num_envs", "1", "--device", "cpu",
            "--skill_lifetime_candidates", "1,2,3,4", "--skill_interval", "10",
            "--opt_num_prototypes", "4", "--prototype_skill_extra_codes", "0",
            "--team_bridge_type", "stochastic", "--enable_situation_diagnostics",
            "--enable_prototype_response_skills", "--enable_high_omega_conditioning",
            "--enable_agent_prototype_relevance", "--enable_per_agent_kappa",
            "--enable_prototype_disc_probe", "--prototype_disc_condition", "kappa",
            "--enable_team_intent", "--enable_team_disc_probe", "--team_intent_k", "8",
            "--seed", str(a.seed)] + extra.split()
    sys.argv = base
    from ha_ctse_process import train
    from ha_ctse_process.train import (load_config, normalize_scenario, apply_standalone_overrides,
                                        apply_checkpoint_structure, create_env, create_agent,
                                        load_checkpoint, load_checkpoint_metadata)
    args = train.parse_args()
    cfg = load_config(args.config, args.preset or None)
    cfg.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(cfg, args)
    if struct_path:
        apply_checkpoint_structure(cfg, args, load_checkpoint_metadata(struct_path))
    env = create_env(cfg, cfg.scenario, int(args.seed), rank=0, scale_mode="eval")
    try:
        _o, info = env.reset(seed=int(args.seed))
        sd = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
        agent = create_agent(cfg, args, env, num_envs=1, state_dim=sd)
    finally:
        env.close()
    if a.checkpoint != "random":
        load_checkpoint(a.checkpoint, agent, load_optimizers=False)

    env = create_env(cfg, cfg.scenario, 1234, rank=0, scale_mode="eval")
    states, jobs = [], []
    try:
        for r in range(a.n_resets):
            obs, info = env.reset(seed=1000 + r)
            states.append(np.asarray(info.get("state"), dtype=np.float32).reshape(-1))
            jobs.append(np.asarray(obs, dtype=np.float32).reshape(agent.n_agents, agent.obs_dim))
    finally:
        env.close()

    obs_b, prev, ages, comp_b, omega_b, rel_b = _build_high_batch(agent, np.stack(states), np.stack(jobs))
    high = agent.high

    # --- g-info loss backward ---
    g_loss, g_metrics = agent.g_info_objective(
        high_policy=high, bridge=agent.bridge, high_obs=obs_b, prev_skills=prev,
        ages=ages, compact=comp_b, omega=omega_b, agent_relevance=rel_b, total_steps=10**9)
    groups = {
        "code_embedding(Z)": list(agent.bridge.code_embedding.parameters()),
        "z_skill_residual(W_Z)": list(high.z_skill_residual.parameters()) if high.z_skill_residual else [],
        "z_duration_residual(U_Z)": list(high.z_duration_residual.parameters()) if high.z_duration_residual else [],
        "skill_head": list(high.skill_head.parameters()),
        "duration_head": list(high.duration_head.parameters()),
        "shared_input_trunk": list(high.input.parameters()),
    }
    g_norms = {k: (_grad_norm(g_loss, v) if v else 0.0) for k, v in groups.items()}

    # --- reference PPO-style policy loss on the same batch (mean NLL of sampled argmax) ---
    codes = torch.zeros(obs_b.shape[0], dtype=torch.long, device=agent.device)
    _c, tvec, *_ = agent.bridge(comp_b, forced_team_code=codes)
    sl, dl, _v = high.logits(obs_b, prev, ages, comp_b, tvec, omega=omega_b, agent_relevance=rel_b)
    ppo_like = torch.nn.functional.log_softmax(sl, -1).mean() + torch.nn.functional.log_softmax(dl, -1).mean()
    ppo_norms = {k: (_grad_norm(ppo_like, v) if v else 0.0) for k, v in groups.items()}

    print(f"R23 g-info GRADIENT AUDIT  gain={a.gain} coef_skill={a.coef_skill}  "
          f"g_info_skill_mi={g_metrics['g_info_skill_mi']:.5f} loss={g_metrics['g_info_loss']:.6e}")
    print(f"{'param group':26s} {'grad|g_info|':>14s} {'grad|ppo-ref|':>14s} {'ratio':>10s}")
    for k in groups:
        r = g_norms[k] / ppo_norms[k] if ppo_norms[k] > 0 else float('nan')
        print(f"{k:26s} {g_norms[k]:14.3e} {ppo_norms[k]:14.3e} {r:10.2e}")
    # classification
    key = g_norms["z_skill_residual(W_Z)"] + g_norms["code_embedding(Z)"]
    ref = ppo_norms["z_skill_residual(W_Z)"] + ppo_norms["code_embedding(Z)"] + 1e-12
    if key < 1e-9:
        verdict = "WIRING: g-info grad ~0 to Z path -> detach/enumeration bug; fix before any sweep."
    elif key / ref < 1e-2:
        verdict = "SCALE/FORM: g-info grad present but <<1% of ref; MI is near-flat -> self-stalling MI form; move to q_A."
    else:
        verdict = "FORM/OTHER: g-info grad non-trivial; if MI still won't move it is cancelled by PPO/entropy -> q_A."
    print("VERDICT:", verdict)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the audit**

Run: `cd /c/project/HMASD && PYTHONPATH=. python scripts/r23_ginfo_grad_audit.py --checkpoint random --gain 0.5 --coef-skill 0.02`
Expected: a table of grad norms + a VERDICT line. Record the numbers.

- [ ] **Step 3: Interpret + record** — write the verdict into ExpRecord + cross_validation (branch per GPT's tree). If WIRING, add a T2b sub-task to fix g-info before T3; otherwise T3 (q_A) proceeds as the main line.

- [ ] **Step 4: Commit**

```bash
git add scripts/r23_ginfo_grad_audit.py
git commit -m "R23: g-info single-batch gradient audit (wiring vs scale vs form)"
```

---

### Task 3: q_A residual actionability module (T3)

**Files:**
- Create: `ha_ctse_process/assignment_actionability.py`
- Create: `tests/r23_assignment_actionability_test.py`
- Modify: `ha_ctse_process/config.py` (add default-off flags)
- Modify: `ha_ctse_process/standalone_agent.py` (construct module; train it in the high update; log metrics; optional gated reward)
- Modify: `ha_ctse_process/train.py` (CLI + override wiring)

**Interfaces:**
- Produces:
  - `AssignmentActionabilityConfig.from_config(config)` with fields `probe_on`, `reward_on`,
    `coef`, `clip`, `warmup_steps`, `include_soft`, `hidden_dim`.
  - `AssignmentActionabilityDiscriminator(nn.Module)`:
    - `__init__(xi_dim:int, context_dim:int, num_team_codes:int, hidden_dim:int=128)`
    - `.losses(xi, context, labels, prior_probs) -> {loss_full, loss_prior, acc_full, acc_prior, residual, residual_gain, prior_entropy}` where `residual = log q_A_full(Z|ξ,c,ω) - log q_A_prior(Z|c,ω)` at the true label, `residual_gain = acc_full - acc_prior`.
    - `.reward(xi, context, labels, prior_probs, coef, clip) -> tensor` (no_grad, clipped).
  - `ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS` + `empty_assignment_actionability_metrics()`.
- Consumes: executed skill/duration ids + soft probs + context (compact c, omega ω) from the high update's per-boundary batch; team code labels Z; code prior probs (uniform or measured usage).

**ξ feature contract (first version, no edit head — none exists):** per high-level assignment
boundary, concatenate over the batch row: executed skill one-hot, executed duration one-hot,
optional soft skill probs and soft duration probs (`include_soft`), and an age/roster scalar
(`log1p(age)/10`). Context = `[compact, omega?]`. All **detached**. q_A_full sees `[ξ, context]`;
q_A_prior sees `[context]` only. Labels = the boundary's sampled team code Z.

- [ ] **Step 1: Write the failing test** (`tests/r23_assignment_actionability_test.py`)

```python
import torch
from ha_ctse_process.assignment_actionability import (
    AssignmentActionabilityDiscriminator, empty_assignment_actionability_metrics,
    ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS)


def _synthetic_batch(n=512, C=8, xi_dim=20, ctx_dim=6, seed=0):
    g = torch.Generator().manual_seed(seed)
    labels = torch.randint(0, C, (n,), generator=g)
    context = torch.randn(n, ctx_dim, generator=g)
    # ξ carries Z (a per-code mean) + noise => q_A_full should beat q_A_prior
    code_means = torch.randn(C, xi_dim, generator=g)
    xi = code_means[labels] + 0.5 * torch.randn(n, xi_dim, generator=g)
    prior = torch.full((C,), 1.0 / C)
    return xi, context, labels, prior


def test_q_a_full_beats_prior_when_xi_carries_Z():
    xi, ctx, labels, prior = _synthetic_batch()
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    opt = torch.optim.Adam(disc.parameters(), lr=1e-2)
    for _ in range(300):
        opt.zero_grad()
        t = disc.losses(xi, ctx, labels, prior)
        (t["loss_full"] + t["loss_prior"]).backward()
        opt.step()
    t = disc.losses(xi, ctx, labels, prior)
    assert t["acc_full"].item() > t["acc_prior"].item() + 0.15   # full recovers Z from ξ
    assert t["residual_gain"].item() > 0.0
    assert float(t["residual"].mean()) > 0.0


def test_q_a_full_equals_prior_when_xi_is_noise():
    xi, ctx, labels, prior = _synthetic_batch()
    xi = torch.randn_like(xi)   # ξ carries no Z
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    opt = torch.optim.Adam(disc.parameters(), lr=1e-2)
    for _ in range(300):
        opt.zero_grad()
        t = disc.losses(xi, ctx, labels, prior)
        (t["loss_full"] + t["loss_prior"]).backward()
        opt.step()
    t = disc.losses(xi, ctx, labels, prior)
    assert t["acc_full"].item() < t["acc_prior"].item() + 0.10   # no recoverable Z


def test_reward_is_clipped_and_nograd():
    xi, ctx, labels, prior = _synthetic_batch()
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    r = disc.reward(xi, ctx, labels, prior, coef=0.05, clip=1.0)
    assert r.shape == (xi.shape[0],)
    assert not r.requires_grad
    assert float(r.abs().max()) <= 0.05 * 1.0 + 1e-6


def test_metric_fields_present():
    assert "q_a_residual_gain" in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS
    m = empty_assignment_actionability_metrics()
    assert all(k in m for k in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /c/project/HMASD && python -m pytest tests/r23_assignment_actionability_test.py -q`
Expected: FAIL (module `assignment_actionability` not found).

- [ ] **Step 3: Implement `ha_ctse_process/assignment_actionability.py`**

```python
"""q_A residual actionability discriminator for HA-CTSE R23 (Option-B).

Asks: given OPT context (c, omega), does the executed joint assignment xi carry
extra information that recovers the sampled team intent Z, beyond the context prior?
Two heads q_A_full(Z|xi,c,omega) and q_A_prior(Z|c,omega); residual = log q_full - log q_prior.
Discriminator-only: inputs are detached, own optimizer, high-level only. Reward is
clipped, no_grad, and gated by a probe pass elsewhere. Not a communication reward.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import torch
import torch.nn as nn
import torch.nn.functional as F

ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS = (
    "q_a_active", "q_a_reward_active", "q_a_samples",
    "q_a_loss_full", "q_a_loss_prior", "q_a_acc_full", "q_a_acc_prior",
    "q_a_residual_gain", "q_a_residual_mean", "q_a_prior_entropy",
    "q_a_reward_mean", "q_a_reward_applied_steps",
)


def empty_assignment_actionability_metrics() -> dict[str, float]:
    return {k: 0.0 for k in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS}


@dataclass(frozen=True)
class AssignmentActionabilityConfig:
    probe_on: bool = False
    reward_on: bool = False
    coef: float = 0.05
    clip: float = 1.0
    warmup_steps: int = 20000
    include_soft: bool = True
    hidden_dim: int = 128

    @classmethod
    def from_config(cls, config: Any) -> "AssignmentActionabilityConfig":
        reward_on = bool(getattr(config, "enable_assignment_actionability_reward", False))
        probe_on = bool(getattr(config, "enable_assignment_actionability_probe", False)) or reward_on
        return cls(
            probe_on=probe_on,
            reward_on=reward_on,
            coef=float(getattr(config, "assignment_actionability_coef", 0.05)),
            clip=float(getattr(config, "assignment_actionability_clip", 1.0)),
            warmup_steps=int(max(getattr(config, "assignment_actionability_warmup_steps", 20000), 0)),
            include_soft=bool(getattr(config, "assignment_actionability_include_soft", True)),
            hidden_dim=int(max(getattr(config, "assignment_actionability_hidden_dim", 128), 1)),
        )


def _mlp(in_dim: int, hidden: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(in_dim), nn.Linear(in_dim, hidden), nn.GELU(),
        nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, out_dim),
    )


class AssignmentActionabilityDiscriminator(nn.Module):
    def __init__(self, xi_dim: int, context_dim: int, num_team_codes: int, hidden_dim: int = 128):
        super().__init__()
        self.xi_dim = int(xi_dim)
        self.context_dim = int(context_dim)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.q_full = _mlp(self.xi_dim + self.context_dim, hidden_dim, self.num_team_codes)
        self.q_prior = _mlp(max(self.context_dim, 1), hidden_dim, self.num_team_codes)

    def _logits(self, xi, context):
        xi = xi.detach().float(); context = context.detach().float()
        if context.shape[-1] == 0:
            context = torch.zeros(xi.shape[0], 1, device=xi.device)
        full = self.q_full(torch.cat([xi, context], dim=-1))
        prior = self.q_prior(context)
        return full, prior

    def losses(self, xi, context, labels, prior_probs):
        labels = labels.detach().long().clamp(0, self.num_team_codes - 1)
        prior_probs = prior_probs.detach().float().clamp_min(1e-8)
        prior_probs = prior_probs / prior_probs.sum().clamp_min(1e-8)
        full, prior = self._logits(xi, context)
        loss_full = F.cross_entropy(full, labels)
        loss_prior = F.cross_entropy(prior, labels)
        row = torch.arange(labels.shape[0], device=labels.device)
        log_qf = F.log_softmax(full, dim=-1)[row, labels]
        log_qp = F.log_softmax(prior, dim=-1)[row, labels]
        residual = log_qf - log_qp
        acc_full = (full.argmax(-1) == labels).float().mean()
        acc_prior = (prior.argmax(-1) == labels).float().mean()
        return {
            "loss_full": loss_full, "loss_prior": loss_prior,
            "acc_full": acc_full, "acc_prior": acc_prior,
            "residual": residual, "residual_gain": acc_full - acc_prior,
            "prior_entropy": -torch.sum(prior_probs * torch.log(prior_probs)),
        }

    @torch.no_grad()
    def reward(self, xi, context, labels, prior_probs, coef: float, clip: float) -> torch.Tensor:
        residual = self.losses(xi, context, labels, prior_probs)["residual"]
        return float(coef) * torch.clamp(residual, -float(clip), float(clip))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd /c/project/HMASD && python -m pytest tests/r23_assignment_actionability_test.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add ha_ctse_process/assignment_actionability.py tests/r23_assignment_actionability_test.py
git commit -m "R23 T3: q_A residual actionability discriminator (module + tests)"
```

- [ ] **Step 6: Add default-off config flags** (`ha_ctse_process/config.py`) — near the other team-intent flags:

```python
        self.enable_assignment_actionability_probe = False
        self.enable_assignment_actionability_reward = False
        self.assignment_actionability_coef = 0.05
        self.assignment_actionability_clip = 1.0
        self.assignment_actionability_warmup_steps = 20000
        self.assignment_actionability_include_soft = True
        self.assignment_actionability_hidden_dim = 128
```

- [ ] **Step 7: Wire into the agent** (`standalone_agent.py`) — construct next to `g_info_objective`, build the module lazily once xi_dim/context_dim are known (first high update), then in the high update: build detached ξ + context from the boundary batch, run `.losses`, add `q_a_loss_full + q_a_loss_prior` to a **separate** `self.q_a_opt` step (not the policy loss), log metrics, and if `reward_on` and warmup passed and the probe gate is open, add `.reward(...)` to the high-level assignment reward only. Cache `q_a_residual_gain` for gating. Default-off => module `None` => S-base identical.

- [ ] **Step 8: Add CLI** (`train.py`): `--enable_assignment_actionability_probe`,
  `--enable_assignment_actionability_reward`, `--assignment_actionability_coef`,
  `--assignment_actionability_clip`, `--assignment_actionability_warmup_steps`,
  `--no_assignment_actionability_soft` (store_false), and copy into cfg in the override function.

- [ ] **Step 9: Regression + wiring tests** — extend the test file with an agent-construction test
  (flag-off => `agent.assignment_actionability is None`; flag-on => module present, low actor input
  dim unchanged), then:

Run: `cd /c/project/HMASD && python -m pytest tests/r23_assignment_actionability_test.py tests/r21_team_intent_test.py tests/r23_actionable_team_intent_test.py -q`
Expected: all pass.

- [ ] **Step 10: Smoke** (tiny CPU run, probe-only, reward off)

Run:
```bash
cd /c/project/HMASD && PYTHONPATH=. python -m ha_ctse_process.train --preset S7-S1 --scenario energy \
  --n_agents 6 --num_envs 2 --collector_backend subproc --total_timesteps 64 --rollout_length 16 \
  --skill_interval 8 --skill_lifetime_candidates 1,2,3,4 --team_intent_k 8 --enable_team_intent \
  --z_assignment_residual_gain 0.5 --enable_assignment_actionability_probe --device cpu \
  --log_dir logs/tmp_r23_qa_smoke
```
Expected: exit 0; `q_a_active=1`, `q_a_acc_full`/`q_a_acc_prior` logged, reward off.

- [ ] **Step 11: Commit**

```bash
git add ha_ctse_process/config.py ha_ctse_process/standalone_agent.py ha_ctse_process/train.py tests/r23_assignment_actionability_test.py
git commit -m "R23 T3: wire q_A probe/reward default-off into the high update + CLI"
```

---

### Task 4: q_D effect-target / timescale audit (T4) — reward-off

**Files:**
- Create: `ha_ctse_process/team_effect_targets.py` (target extractors + a light multi-head q_D probe)
- Create: `tests/r23_team_effect_target_test.py`
- Modify: `ha_ctse_process/config.py` (flags), `ha_ctse_process/standalone_agent.py` (buffer H-windows at Z boundaries; run the probe reward-off), `ha_ctse_process/train.py` (CLI)

**Interfaces:**
- Produces:
  - target extractors mapping a stored H-window to a fixed vector, for targets
    `s_next`, `joint_action_summary`, `joint_effect_window`, `delta_omega`.
  - `TeamEffectTargetProbe(nn.Module)` holding one `TeamIntentDiscriminator`-style head per
    (target, H) pair; `.update(window_batch, labels, prior) -> metrics` training each head
    reward-off and reporting `q_d_acc[target,H]`, `residual_gain[target,H]`, `best_target`.
  - `TEAM_EFFECT_TARGET_METRIC_FIELDS` + empty-metrics helper.
- Consumes: at each Z boundary, buffer the next H∈{10,20,50} primitive steps of: global state
  `s`, joint action summary (mean/one-hot histogram of primitive actions across agents), a joint
  effect window (Δ of the env effect vector the outcome-residual path already extracts), and the
  OPT `omega` trajectory (for Δω). All detached. **q_D must not read ξ or Z labels as input.**

**Double-count guard (enforced in code + test):** the q_D probe input builders take only
`{state, action-summary, effect-window, omega}`; a test asserts the assembled q_D feature tensor
has no overlap with the q_A ξ features (no skill/duration ids, no assignment probs).

- [ ] **Step 1: Write the failing test** (`tests/r23_team_effect_target_test.py`)

```python
import torch
from ha_ctse_process.team_effect_targets import (
    TeamEffectTargetProbe, TEAM_EFFECT_TARGET_METRIC_FIELDS, summarize_joint_actions)


def test_probe_recovers_Z_from_informative_target_only():
    torch.manual_seed(0)
    C, n = 8, 512
    labels = torch.randint(0, C, (n,))
    code_means = torch.randn(C, 12)
    informative = code_means[labels] + 0.3 * torch.randn(n, 12)   # carries Z
    noise = torch.randn(n, 12)                                     # carries nothing
    prior = torch.full((C,), 1.0 / C)
    probe = TeamEffectTargetProbe(target_dims={"good": 12, "bad": 12}, num_team_codes=C)
    for _ in range(300):
        probe.update({"good": informative, "bad": noise}, labels, prior)
    m = probe.metrics()
    assert m["q_d_acc_good"] > m["q_d_acc_bad"] + 0.15
    assert m["q_d_residual_gain_good"] > 0.0


def test_joint_action_summary_shape():
    acts = torch.randint(0, 5, (16, 6))   # 16 boundaries, 6 agents, 5 discrete actions
    summ = summarize_joint_actions(acts, num_actions=5)
    assert summ.shape == (16, 5)          # normalized histogram over agents


def test_metric_fields_present():
    assert any("q_d_acc" in f for f in TEAM_EFFECT_TARGET_METRIC_FIELDS)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /c/project/HMASD && python -m pytest tests/r23_team_effect_target_test.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `ha_ctse_process/team_effect_targets.py`** — a `summarize_joint_actions`
  helper (normalized per-boundary action histogram across agents), the four target extractors, and
  `TeamEffectTargetProbe` holding a small classifier head per target that trains reward-off with
  cross-entropy and reports per-target `q_d_acc`, `residual_gain` (acc − prior_acc), and the argmax
  `best_target`. Mirror `TeamIntentDiscriminator.losses` (detach states, prior-correct).

- [ ] **Step 4: Run tests to verify pass**

Run: `cd /c/project/HMASD && python -m pytest tests/r23_team_effect_target_test.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit the module**

```bash
git add ha_ctse_process/team_effect_targets.py tests/r23_team_effect_target_test.py
git commit -m "R23 T4: multi-target/timescale q_D probe module + tests (reward-off)"
```

- [ ] **Step 6: Config flags** (`config.py`): `enable_team_effect_target_audit=False`,
  `team_effect_audit_horizons="10,20,50"`, `team_effect_audit_targets="s_next,joint_action,joint_effect,delta_omega"`.

- [ ] **Step 7: Buffer H-windows + run probe in the agent** (`standalone_agent.py`): at each Z
  boundary record the boundary's Z label and the following H-step windows for each target
  (detached); after the rollout, if `enable_team_effect_target_audit`, call `probe.update(...)`
  reward-off and merge `probe.metrics()` into the update dict. Default-off => no buffering.
  **No reward path is added in this task.**

- [ ] **Step 8: CLI** (`train.py`): `--enable_team_effect_target_audit`,
  `--team_effect_audit_horizons`, `--team_effect_audit_targets`; copy to cfg.

- [ ] **Step 9: Double-count guard test** — assert the q_D window feature builder rejects/omits any
  ξ field (skill ids, duration ids, assignment probs); run the full new-tests set.

Run: `cd /c/project/HMASD && python -m pytest tests/r23_team_effect_target_test.py tests/r23_assignment_actionability_test.py -q`
Expected: all pass.

- [ ] **Step 10: Smoke** the audit path on a tiny CPU run (`--enable_team_effect_target_audit`,
  horizons `10,20`), expect exit 0 and `q_d_acc_*` fields logged.

- [ ] **Step 11: Commit**

```bash
git add ha_ctse_process/config.py ha_ctse_process/standalone_agent.py ha_ctse_process/train.py tests/r23_team_effect_target_test.py
git commit -m "R23 T4: wire reward-off q_D target/timescale audit (default-off) + CLI"
```

---

### Task 5: 320k mechanism-matrix runners (T5)

**Files:**
- Create: `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh`
- Create: `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1`

**Interfaces:**
- Consumes: the T3/T4 CLI flags; the existing R23 shared config (S7-S1, 6 agents, gain 0.5,
  team_intent_k 8, durations 1,2,3,4, 64 env, 320k, eval @160k/320k).
- Produces: four arms — `arm0_arch_only` (known-pass control), `arm1_qA_probe`
  (`--enable_assignment_actionability_probe`, reward off), `arm2_qA_reward`
  (`--enable_assignment_actionability_reward --assignment_actionability_coef 0.02`, q_D reward off),
  `arm3_qD_target_audit` (`--enable_team_effect_target_audit`, reward off). `--dry-run` preflight.

- [ ] **Step 1: Write the cloud `.sh`** modeled on `scripts/run_r23_actionable_team_intent_cloud_64env.sh`
  (same base flags; per-arm deltas above; `EXPERIMENTS=` selector; `--dry-run` prints the 4 commands).

- [ ] **Step 2: Write the local `.ps1`** mirror (device cuda, smaller num_envs default).

- [ ] **Step 3: Dry-run validate**

Run: `cd /c/project/HMASD && bash scripts/run_r23_next_mechanism_matrix_cloud_64env.sh --dry-run`
Expected: prints 4 arm commands, no launch.

- [ ] **Step 4: Commit**

```bash
git add scripts/run_r23_next_mechanism_matrix_cloud_64env.sh scripts/run_r23_next_mechanism_matrix_local_cuda.ps1
git commit -m "R23 T5: 320k mechanism-matrix runners (arm0..3), dry-run validated"
```

---

## Self-Review

- **Spec coverage:** T1 = GPT §1 curves; T2 = GPT §2 gradient audit; T3 = GPT §4 Option-B q_A
  (probe then gated reward); T4 = GPT §5 q_D target/timescale audit (four targets × H∈{10,20,50},
  reward-off); T5 = GPT §6 mechanism matrix Arm0–3; PR-1 double-count contract enforced by the
  q_D "no ξ input" guard test in T4-9. Stop list (no coef sweep, no q_D reward-on, no 960k, no new
  kappa*/hazard/DADS, no comm-as-intrinsic) honored: no coef sweep task, no q_D reward task, all
  runs are 320k, no new branches, discriminators never read comm fields as reward.
- **Placeholder scan:** T1/T2 ship complete scripts; T3 ships the full module + tests. T3 steps
  7–8 and all of T4 steps 3/7 describe wiring against a 6369-line file whose exact insertion lines
  are pinned during execution — the interfaces, field names, and behavior are fully specified, but
  the literal diff hunks are resolved at edit time (normal for this file).
- **Type consistency:** `residual_gain` = acc_full − acc_prior in both the q_A module and its
  tests; metric field names (`q_a_*`, `q_d_*`) match between module constants and tests.

## Sequencing note

T1 and T2 run **now** (cheap, decisive). **T2's verdict gates T3:** if the audit says WIRING,
insert a g-info fix sub-task before T3; if SCALE/FORM (expected), T3 (q_A) is the main line. T4
depends only on T3's context/label plumbing being in place, not on q_A passing. T5 depends on
T3+T4 CLI flags existing. No q_D reward is built anywhere in this plan.
