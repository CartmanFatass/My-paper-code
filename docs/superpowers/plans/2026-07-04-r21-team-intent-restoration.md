# R21 Team-Intent Restoration — Implementation Spec (for Codex)

Author: CC (Architect+Reviewer, under explicit user override 2026-07-04:
"bring the autoregressive team skill back, keep asynchronous low-level
skills; highest priority; no team_bridge_none ablation").
Supersedes: Round 20 D2 (ablation dropped) and D3 (reservation dissolved
into this build). Single source of truth for the R21 build; wins conflicts.

## Thesis

Restore HMASD's proven team engine — sampled team intent Z upstream of
autoregressive assignment, with the team discriminator reward — inside the
asynchronous-lifetime architecture, via a TWO-CLOCK HIERARCHY:

```text
SLOW CLOCK (synchronized): Z_m ~ pi_Z(Z | c, omega), held for K_team check
  intervals. At each Z boundary: ATOMIC full-team reassignment through the
  HMASD AR chain  z_i | Z, c, o_i, z_{<i}  (R18.1: commitment must buy
  atomic switching; staggered propagation is what kills deceptive/strategy
  coherence).
FAST CLOCK (asynchronous, unchanged): between Z boundaries, individual
  renewals fire per existing lifetime machinery and DOCK against the
  current Z and standing roster:  z_i | Z, c, o_i, roster (R16 machinery,
  now Z-conditioned).
HMASD recovered as the special case K_team=1, all lifetimes = k.
```

Vacuity note (why this is sound where kappa was not): Z is SAMPLED, so
H(Z|s) > 0 and the team discriminator reward is non-vacuous — the original
HMASD engine transplants nearly verbatim. The vacuity lemma applies only to
recognized latents; it now delimits the two layers: substrate (c/omega/
kappa, recognized) vs intent (Z, sampled).

## Components

### C1. TeamIntent policy (refactor of CompactTeamBridge — user-authorized)

```text
pi_Z(Z | c_tau, omega_tau): stochastic categorical, n_Z = num_team_codes
  (keep 6). Reuse code_embedding. Sampled ONLY at Z boundaries; held
  constant between them (store Z, Z_age per env).
Z log-prob enters high-level PPO at Z boundaries (the existing team_logp /
  team_logp_weight pathway is the natural wiring point).
Z entropy bonus in the high-level loss (HMASD skill-entropy term).
K_team: fixed integer config (default 48 check intervals — AMENDED
  2026-07-05: K_team must be >= 2x the max lifetime candidate, because
  atomic reassignment makes K_team the effective maximum lifetime; the
  original default 12 structurally truncated the 13- and 24-candidates
  every time, manufacturing an artificial duration collapse. Log
  truncation PER DURATION BUCKET. CLI-overridable; K_team sensitivity
  {24, 48} is a later pre-registered knob). Hazard/situation-triggered Z
  renewal is a LATER ablation, not this build.
```

### C2. Atomic reassignment at Z boundaries

```text
At each Z boundary: all agents' skills renew through the AR chain in fixed
id order, conditioned on the NEW Z; individual lifetimes/countdowns reset;
within-boundary later renewers see earlier renewers' new skills (the R16
full-sync reduction property, now exercised every K_team).
Renewal penalties: Z-boundary reassignments are FORCED renewals — exempt
from edit/switch penalties (the existing forced-assignment exemption rule).
Log: z_boundary_trunc_rate (fraction of individual lifetimes truncated by
Z boundaries) — if ~1.0, K_team is too short relative to lifetimes and the
async fast clock is decorative; target << 1.
```

### C3. Team discriminator (the engine — ships in the SAME build)

```text
q_D(Z | s_{t+1}): MLP, state -> n_Z logits. Trained per-step by CE on the
  SAMPLED Z labels, current rollout only, own optimizer, detached inputs
  (CE trains only q_D; the reward trains the policy — g-revival rule).
Reward, HMASD-faithful, injected LOW-LEVEL per-step (as in the paper):
  r_i += lambda_D * clip(log q_D(Z|s_{t+1}) - log p_hat(Z), +-clip)
  p_hat(Z) = running usage prior (prior-corrected so uniform q_D gives ~0).
  lambda_D = 0.05 (AMENDED 2026-07-05 per the R16.5 dose-response finding;
  see C4), clip 2.0, warmup 20k,
  probe/reward flag split, ratio metric + guard (warn/kill modes reused).
Individual discriminator conditioning gains Z:
  q_d(z_i | o'_i, kappa, Z)  — the paper-faithful HMASD form (R11.4);
  the R15 coordinator-residual null (stored log pi_h) is unchanged.
Boundary: q_D input is the state vector only — no comm-metric features.
```

### C4. Config (all default-off; one master flag)

```text
enable_team_intent = False          # master: C1+C2 structure
enable_team_disc_probe = False      # q_D trains, no reward
enable_team_disc_reward = False     # requires probe
team_intent_k = 48                  # K_team in check intervals (>= 2x max
                                    # lifetime candidate; see C1 amendment)
team_disc_coef = 0.05          # AMENDED 2026-07-05: the R16.5
                               # dose-response finding (0.1 collapses,
                               # 0.05 self-sustains) postdates this spec;
                               # start at 0.05, watch the COMBINED
                               # intrinsic/env ratio in [0.05,0.5],
                               # escalate only by one pre-registered step
team_disc_clip = 2.0
team_disc_warmup_steps = 20000
team_disc_lr = 5e-4
(reuse reward_ratio_guard_mode for the new ratio guard)
z_entropy_floor_enabled = False   # AMENDED 2026-07-05: head-generic floor
                                  # flag, default-off, "decorative until
                                  # the red flag fires"; Z-usage entropy
                                  # logged with the standard alarms from
                                  # day one (pi_Z inherits the documented
                                  # late-entropy-collapse risk)
```

## Metrics (CSV/TB/console per convention)

```text
z_usage_entropy, z_dwell (should be ~K_team), z_boundary_trunc_rate
team_disc_acc          # healthy band: above 1/n_Z, below saturation;
                       # ~1.0 early = leak suspect (Z visible in state?)
team_disc_reward_env_ratio, team_disc_reward_applied_steps (guard)
z_assignment_itv       # forced-Z intervention KL on the AR assignment —
                       # mechanically nonzero BY CONSTRUCTION (Z is
                       # upstream); log to verify wiring, not emergence
lifetime metrics unchanged (duration entropy, heterogeneity, renewal stats)
```

## Experiment pre-registration (create ExpRecord entry before launch)

```text
EXP-2026070X-r21-team-intent: local CUDA, 16 env, 960k, seed 1 then 2.
BASE: the stabilized entfloor configuration (launch AFTER the entfloor
  480k read confirms the floor works; do not run on a decaying base).
ARMS: r21_z_probe (structure on, q_D probe, no reward)
      r21_z_reward (full engine)
  vs the entfloor run as matched control. ONE structural variable (Z system)
  — accepted deviation from strict single-variable, justified by the
  channel-pressure rule: intent without pressure = decorative channel #4.
GATES (vs stabilized base): IMPROVEMENT REQUIRED on coverage and
  zero_throughput_ep_frac (this is the restored engine, not a garnish);
  z_usage_entropy not collapsed (> 50% uniform); team_disc_acc in the
  healthy band; ratio in [0.05, 0.5]; no lifetime-metric regression;
  z_boundary_trunc_rate << 1.
BYPRODUCT READ (log explicitly): this arm vs the recognition-only base IS
  the commitment-vs-recognition decisive experiment (R14.0) on S7-S1.
STOP: if r21_z_reward fails the improvement gate on 2 seeds with healthy
  mechanism metrics, HMASD's team engine does not transfer to the async
  fast clock — escalate to the K_team sweep {24, 96} once (both respect
  K_team >= 2x max candidate only if candidates are trimmed for the 24 arm
  — log that pairing explicitly), then to the R18.3 matrix read. No
  coefficient sweeps.
```

## Sequencing and priority (user-set)

```text
1. Codex builds R21 NOW (highest priority; default-off, parallel to the
   running entfloor cycle).
2. Launch on the stabilized base after the entfloor 480k read.
3. a2_plus_t (R19 heads) DEMOTED to complementary: it remains built and
   trigger-available; the transition residual may later condition on Z and
   add stabilization credit q_D does not give. Not launched before R21
   reads unless the user reorders.
4. team_bridge_none ablation: DROPPED (user decision). The bridge code path
   is absorbed: pi_g machinery becomes pi_Z; the old decorative g wiring is
   removed as part of C1 (this deletion is IN-SCOPE for the refactor).
```

## Fidelity notes

- Z is a commitment: never derived deterministically from c; never
  recomputed mid-hold; stored with its log-prob for PPO consistency
  (snapshot rules as in R16 G1).
- The two-layer vocabulary holds: substrate (c/omega/kappa, recognized)
  conditions pi_Z; intent (Z, sampled) constrains assignment. Z does NOT
  enter the low-level actor (skill bottleneck invariant unchanged);
  low-level critic MAY condition on Z (HMASD-faithful, V_l(s, Z)).
- Resolution order: this spec -> Round 21 ledger entry -> R18/R19
  principles -> HMASD paper -> ask, do not guess.
