# HA-CTSE v6 — Canonical Algorithm Description (2026-07-04)

Status: the detailed restatement produced by the Research Copilot CHECK and
expanded at user request. If confirmed by the user, this is the reference
description; principles/plan express the same design as contracts.
Lineage: Rounds 12 (recognition-first), 14 (prototype basis), 15 (steering
objective), 16 (roster-docking), 18 (atomic variation / kappa*), 19
(dual engines), 21 (team-intent restoration, two-clock hierarchy).

## Implementation / validation status (added 2026-07-05 per Codex review condition)

```text
IMPLEMENTED + EXPERIMENT-SUPPORTED (internal evidence, class b):
  recognition substrate (gate passed at 16env/N=4); prototype-response
  selection + coordinator-residual reward (stabilized S7-S1 baselines:
  coverage_eq1 0.0757 seed1-coef01+floor / reward 71.7 seed2-coef005
  self-sustaining); entropy floor + guards; roster mode (implemented,
  channel measured DECORATIVE, kl_shuf ~4e-6).
IMPLEMENTED + LOCALLY VALIDATED, AWAITING EXPERIMENT (wiring verified,
  no behavioral evidence yet):
  R21 two-clock team intent Z + team discriminator (launch-ready,
  EXP-20260705-r21-team-intent).
IMPLEMENTED + MECHANISM-NEGATIVE SO FAR:
  R19 transition residual (probe team_t_mi = -0.042 at 960k, self_frac
  0.93 — data-starved conditional; reward arm incomplete). Retained as the
  dissociation's negative wing, not as a validated component.
THEORY / INTENDED ONLY (class c/d, no code or no data):
  vacuity lemma (derivation; indirect empirical support via decorative-g/
  kappa observations); validity-hazard lifetimes (Stage 2, not built);
  coverage complementarity (Stage 3, not built); kappa*-style commitment
  claims on deceptive tasks (no such scene exists yet); C4 async-lifetime
  advantage (ZERO confirmatory reads; awaits the two-tempo environment).
```

## Essence

A two-level CTDE MARL algorithm organized around THREE TIMESCALES that
differ in epistemic KIND, not only speed:

```text
RECOGNITION  (continuous)          what the situation IS      recognized
COMMITMENT   (slow, synchronized)  what the team INTENDS      sampled
RESPONSE     (fast, asynchronous)  how each agent ACTS        sampled
```

Organizing theorem (vacuity lemma): a recognized variable is a function of
state, so identifiability rewards on it carry zero policy gradient —
recognized layers can only be paid on the FUTURE (transitions/effects);
sampled variables carry entropy given the state, so HMASD-style
identifiability rewards are live for them. The architecture assigns each
layer exactly the intrinsic pressure that is mathematically possible for
its kind. HMASD is the exact special case where the three timescales
coincide (K_team = 1, all lifetimes = k, recognition unused).

## Layer I — Recognition substrate

```text
OPT-style encoder: state + joint obs
  -> N sparse prototypes (sparsemax; contrastive-disagreement keeps them
     distinct)
  -> omega (active-pattern weights), compact c, discrete slow situation
     kappa (dwell/debounced); per-agent relevance rel_i -> kappa_i.
Decides NOTHING. Must pass the pre-registered substrate gate before
anything builds on it: G-DWELL (vs block-shuffled null), G-OUTCOME
(beats simple-features baseline), G-ROLE (aligns with counterfactual role
labels). Situation-ness can be TRAINED for (slowness, predictability),
one-retrain cap. Needs explicit task grounding (return-prediction head) —
in the source paper TD loss grounds it; ungrounded it drifts.
```

## Layer II — Commitment (team intent Z)

```text
Z ~ pi_Z(Z | c, omega), discrete n_Z codes, sampled at team boundaries,
HELD for K_team check intervals. Prescriptive by construction.
Sampling buys what recognition provably cannot:
  EXOGENOUS VARIATION  — same state, different committed strategies across
    episodes (team-level exploration);
  ATOMIC SWITCHING     — at Z boundaries the WHOLE team reassigns through
    the AR chain; a strategy flip never transits a punished mixed
    configuration (which staggered propagation produces).
Z log-prob in high-level PPO; Z entropy bonused; Z never enters the
low-level actor; low-level centralized critic may see (s, Z).
```

## Layer III — Response (skills z_i)

```text
Skills = prototype-response codes z_i in {1..N} ("respond to pattern n");
skill space inherits substrate semantics + CD distinctness.
Two renewal modes:
  Z BOUNDARY: full-team autoregressive assignment
    z_i | Z, c, omega, o_i, z_{<i}   (HMASD coordinator, verbatim;
    within-boundary later agents see earlier agents' NEW skills)
  BETWEEN BOUNDARIES: asynchronous individual renewal; the renewing agent
    DOCKS: z_i | Z, c, omega, o_i, roster
    roster = teammates' active skills + ages, SNAPSHOTTED at renewal for
    PPO logp consistency. Sequential coordination generalizes from "agent
    order in one instant" to "temporal order against a persistent
    configuration".
SKILL BOTTLENECK (invariant): pi_l(a_i | o_i, z_i) only — no c/omega/
kappa/Z leaks to the low-level actor, or the hierarchy collapses into a
contextual flat policy.
```

## Intrinsic pressure system (layer-matched; bootstrap scale; ships WITH mechanisms)

```text
INDIVIDUAL ENGINE (role diversity; bounded by ln N — cannot explore state
space):
  r_i = log q_d(z_i | o_{i,t+1}, kappa, Z) - log pi_h(z_i | ...)
  label = currently ACTIVE skill (well-defined under variable lifetimes);
  null = STORED assignment log-prob (the AR policy itself)
  = HMASD's diversity + skill-entropy pair fused pointwise;
  usage-imbalance-immune (null IS usage) and duration-shortcut-immune
  (per-step, no segment features); supplies identifiability pressure +
  assignment entropy + anti-duplication in one term.
TEAM ENGINE (state diversification; the S7-S1 bottleneck per the
dual-engine analysis):
  r_i += lambda_D * (log q_D(Z | s_{t+1}) - log p_hat(Z)), per-step,
  low-level (HMASD-faithful) — NON-VACUOUS because Z is sampled.
COMPLEMENTARY (the recognized layer's only legal pressure):
  R_team = log q(kappa' | kappa, xi) - log q(kappa' | kappa), high-level,
  xi = active-skill count profile, SELF-TRANSITIONS INCLUDED so
  stabilization pays (hold-the-chain is a xi-dependent predictable
  self-transition). Also the dissociation probe vs the commitment engine.
ENV REWARD is the only task return. Communication metrics never enter any
intrinsic term. Discipline: bootstrap pressure may be crude but must be
dense and non-negligible; semantic validation is diagnostics, never the
drive.
```

## Training and stability

```text
Two-level PPO; on-policy contracts: every sampled decision stores logp +
the exact conditioning snapshot (roster, Z) it was sampled under; masks
before sampling; forced Z-boundary renewals exempt from switch penalties.
Discriminators: CE on own optimizers, detached inputs — classifiers
observe, rewards teach.
Stability machinery (forensics-earned): duration-entropy floor (honestly
labeled: permanently-active floor = scaffolded heterogeneity, a qualified
mechanism claim per R10.2-F); reward/env ratio guards (warn/kill);
dual-mode eval (stochastic + deterministic).
```

## Provided vs claimed

```text
PROVIDED BY CONSTRUCTION:
  async per-agent lifetimes; atomic strategy switching; HMASD as the
  K_team=1 / all-lifetimes=k special case.
CLAIMED (falsifiable):
  C3 the sampled-Z engine restores exploration under the async fast clock
     (earliest signal: team_disc_acc trajectory shape at 160k);
  C5 the two-clock interface loses nothing full synchronization had
     (z_boundary_trunc_rate << 1; task metrics vs stabilized base);
  C4 async lifetimes beat fixed k WHERE TASK TEMPOS ARE HETEROGENEOUS —
     per the 2x2 task matrix this CANNOT be shown on S7-S1; it awaits the
     two-tempo mechanism scene and currently has zero confirmatory reads.
PAPER SPINE (per the Research Copilot CHECK, pending user decision):
  the hierarchy itself — vacuity as organizing theorem, layer-matched
  pressures, commitment-vs-steering dissociation (R19 vs R21).
```
