# HMASD → HA-CTSE Research Review (senior MARL / option-learning perspective)

Date: 2026-07-01
Reviewer: CC (Cowork), grounded in the HMASD paper (Yang et al., 2023,
*Hierarchical Multi-Agent Skill Discovery*), `memory/ALGORITHM_PRINCIPLES.md`,
`IC_SPL_HAZARD_SMDP_ALTERNATIVE.md`, and code
(`hmasd/agent.py`, `ha_ctse_process/{standalone_agent,skill_effect_discovery,config}.py`).

This is a critical review, not a summary. It builds on cross_validation.md Rounds 7–9
(do not re-read those here) and adds the one thing those rounds did not have:
the HMASD paper's own equations and ablations, cross-checked against what
HA-CTSE actually kept.

---

## 0. Executive verdict (read this first)

HMASD has **four** load-bearing parts. The paper's own ablation (§4.3, Fig. 8)
confirms each is necessary:

```text
(1) team skill Z         — HMASD_NoIndi (team-only) and HMASD_NoTeam (indiv-only)
(2) individual skill z_i   both lose; BOTH skills are needed.
(3) intrinsic discriminator reward (λ_D log q_D(Z|s) + λ_d log q_d(z_i|o_i,Z)):
    HMASD_NoInRew (λ_D=λ_d=0) "can't work on most scenarios" — this is the
    single most load-bearing component.
(4) autoregressive high-level coordinator: HMASD_NoHigh (random assignment)
    loses badly. The coordinator assigns z_i | Z, z_{1:i-1} — COMPLEMENTARY skills.
```

Now map that onto what HA-CTSE actually ships:

```text
HMASD component            HA-CTSE status (verified in code)
------------------------   ------------------------------------------------------
(2) individual skill z_i   KEPT. pi_l(a_i|o_i,z_i), single linear FiLM gate.
(3a) individual discrim.   BEING REBUILT as P3-4 residual discriminator (dense
     q_d(z_i|·)            micro-window, shortcut-residual). This is real inheritance.
(1) team skill Z           BROKEN. g_tau exists but is empirically DECORATIVE
                           (g_itv ~0.03–0.05 across Rounds 3–5); and
                           use_team_code_discriminator = False (config.py:219).
(3b) team discriminator    ABSENT by default. HMASD's q_D(Z|s) — the cooperative
     q_D(Z|s)              diversity pressure — has no live analogue.
(4) autoregressive         REPLACED by PARALLEL per-agent editing. High-level
    complementarity        log-prob is sum_i log pi_term(m_i) + sum_i log pi_z(z_i);
                           z_i depends on the agent's OWN prev skill + g_tau, never
                           on other agents' concurrently-assigned skills
                           (standalone_agent.py:753,782; config low_actor_condition_
                           on_team_code=False). No complementarity channel.
```

**The headline.** HA-CTSE kept the individual half of HMASD and is investing its
current effort (P3-4) in making the individual discriminator cleaner. But the two
components HMASD needs for **cooperation** — the team discriminator and the
autoregressive complementary assignment — are exactly the two HA-CTSE removed and
did not replace. This is not a coincidence with the observed failure; it *is* the
observed failure. The project's own diagnosis ("binding failure is cooperative
credit assignment"; `credit_recovery_rate ~ 0.01` everywhere; `skill_entropy ~
0.998` reward-pure) is the precise signature of a system that discovers
individually-distinguishable skills with **no mechanism forcing them to be
mutually complementary or jointly discriminable**.

Consequence for prioritization: **a cleaner residual individual discriminator
(P3-4c) optimizes the half that was never the bottleneck.** The highest-leverage
next step is to reconstruct, under decoupled lifetimes, the *cooperative* half:
(i) a causally-alive team code `g`, (ii) complementary assignment among
co-editing agents, and (iii) a team/joint discriminator as the cooperative
diversity source. Individual-skill forcing should be the *second* term, not the
headline.

Everything below expands and defends this.

---

## 1. HMASD mechanism dissection (grounded in the paper)

The objective is a structured-variational lower bound (Eq. 3):

```text
log p(O_0:T) >= E_τ [ Σ_t r(s_t,a_t)                              # team reward (usefulness)
                     + Σ_t ( log p(Z|s_t) + Σ_i log p(z_i|o_i_t,Z) )   # DIVERSITY term
                     - Σ_t ( log q(Z|s_t) + Σ_i log q(z_i|o_i_t,Z) )   # SKILL ENTROPY (high-level)
                     - Σ_t Σ_i log q(a_i_t|o_i_t,z_i) ]                # ACTION ENTROPY (low-level)
```

Low-level reward actually used (Eq. 4), applied **every primitive step**:

```text
r_i_t = λ_e r_t + λ_D log q_D(Z|s_{t+1}) + λ_d log q_d(z_i|o_i_{t+1}, Z)
```

High-level reward = Σ_{p=0}^{k-1} r_{t+p} (env return summed over the fixed
k-window). Discriminators trained supervised (Eq. 8, cross-entropy).

What each part solves:

- **Skill discoverer** `π_l(a_i|o_i,z_i)`: the actuator. Turns a discrete latent
  into a temporally-coherent behavior. Trained by `λ_e r` (usefulness) +
  intrinsic (distinguishability) + action entropy (exploration). Its job is to
  make `z_i` *controllable*.
- **Individual discriminator** `q_d(z_i|o_i,Z)`: makes different `z_i` visit
  different observation regions **given the team skill Z**. This is the dense
  per-step diversity signal. The `Z`-conditioning is what makes individual
  diversity *cooperative* rather than selfish — "be distinguishable in the
  context of what the team is doing."
- **Team discriminator** `q_D(Z|s)`: makes the *whole team* jointly visit
  discriminable global states. This is the cooperative-diversity pressure. It is
  the term that rewards coordinated joint behavior, not per-agent behavior.
- **Skill entropy** (high-level policy entropy, Eq. 6) + **action entropy**
  (low-level, Eq. 7): exploration in skill space and action space. Prevents
  premature collapse.
- **Autoregressive coordinator** `π_h(Z, z_1:n | ŝ, ô, ...)`: assigns `z_i`
  conditioned on `Z` and `z_{1:i-1}`. The paper is explicit (§3.2): this
  "prevents skill duplication and allows agents to choose complementary skills."
  This is the primary **credit-decoupling / role-allocation** mechanism.

How sparse reward + credit assignment are alleviated:

```text
sparse reward  -> intrinsic discriminator reward is DENSE (every step, from the
                  free supervised label z_i), so the discoverer gets gradient long
                  before any env reward appears. HMASD reports ~diverse skills
                  under zero env reward. The diversity loop bootstraps behavior.
credit assign. -> (a) autoregressive complementarity partitions the joint task
                  into non-redundant individual skills (structural credit split);
                  (b) team discriminator + team reward summed over k give the
                  high level a clean per-k credit signal for the joint skill;
                  (c) Z-conditioning ties individual credit to team context.
```

**Which mechanisms depend on fixed k** (these are what break under decoupling):

```text
D1. Label density & purity: skill is constant for exactly k steps for ALL agents,
    so each k-window yields k clean supervised samples (o, Z, z_i) with a STABLE
    label — dense, low-noise discriminator training AND dense intrinsic reward.
D2. Stable conditioning context: q_d conditions on Z, which is constant for the
    whole k-window and shared across all agents. "Given the team is doing Z" is
    well-defined at every step.
D3. Clean high-level MDP: fixed k => discount over a macro-step is γ^k, constant.
    The high level is a standard fixed-horizon MDP; no SMDP bootstrap confound.
D4. Unambiguous attribution: all skills refresh together, so the joint skill
    configuration is piecewise-constant on the k-grid; "the effect of this window"
    has a stable team context.
```

**Which spirits transfer to variable lifetime** (these are architecture-agnostic):

```text
T1. The variational-MI reward form log q(label|behavior) - log p(label).
T2. The two-level discoverer/coordinator split with a skill bottleneck.
T3. The diversity + entropy decomposition (individual diversity, team diversity,
    skill entropy, action entropy) as SEPARATE, separately-tracked channels.
T4. The COMPLEMENTARITY PRINCIPLE — individual skills should be jointly
    non-redundant given team context. This is the transferable heart of HMASD's
    cooperation, and it is the one HA-CTSE dropped.
```

---

## 2. HA-CTSE gap analysis: where the loop is broken

### 2.1 Density: mostly restored (good)

P3's micro-windows (`h∈{5,10,20}`) correctly rebuild D1's density under variable
lifetimes — a long segment yields many samples, and horizon is an explicit
embedded input (not read off pooled length). This is a genuine, correct fix.
Keep it.

### 2.2 Conditioning context: broken (D2) — and this is under-recognized

HMASD's `q_d(z_i|o_i,Z)` is only cooperative because `Z` is a stable, shared team
context. HA-CTSE's analogue conditions on `g_tau`, which is (a) **decorative**
(no causal effect on `π_z`, per the memory's own `g_itv~0.05`) and (b)
**non-stationary within a segment** (other agents edit asynchronously, so the
ambient team context changes mid-window). So the P3 discriminator is effectively
`q(z_i | behavior_i, DEAD_context)` — it can only reward *selfish* individual
distinguishability, never cooperative distinguishability. Conditioning on a dead
variable is the single most important **superficial imitation** in the current
design: the form matches HMASD, the function does not.

### 2.3 Complementarity: severed (D4/T4) — the biggest structural loss

HMASD's cooperation comes substantially from autoregressive assignment. HA-CTSE
edits skills **in parallel, per agent**, with no cross-agent conditioning at
assignment time. Two agents editing at the same k-boundary can (and, at
`skill_entropy~0.998`, do) pick redundant skills. Nothing pressures them to
partition roles. This is why "feeding `g` to the low level didn't help" — the
problem was never that the low level can't see `g`; it is that the *high level
never produces a complementary joint assignment* for the low level to execute.
This maps exactly onto `credit_recovery_rate ~ 0.01`.

### 2.4 SMDP confound: introduced (D3)

Fixed k gave HMASD a clean γ^k high-level MDP. Variable `T_i` reintroduces a
genuine SMDP with γ^{T_i} varying ~20× across the duration set — the
bootstrap/duration-bias confound documented in Rounds 1/3/8. This is a *cost of
decoupling that HMASD never paid*, and it structurally biases the high level
toward long durations for variance reasons unrelated to task value. It is not yet
fully neutralized (only worked around by restricting candidates to a short range).

### 2.5 Duration↔skill shortcut: introduced, structural (not a bug)

`d_i` and `z_i` are sampled by the same head, at the same boundary, on the same
context → `I(d_i; z_i) > 0` by construction. This is the mechanism that broke
Stage A/2b/2c/2d. It is the direct, foreseeable cost of the paper's own central
choice (per-agent discrete duration). It cannot be "fixed"; it can only be taxed
(residualization) or removed by construction (hazard-SMDP, §4.3).

### 2.6 Does P3 forcing correspond to the HMASD discoverer/discriminator spirit?

Partially, and only for the *individual* half:

```text
GENUINE inheritance:
  - dense micro-window intrinsic reward on the low-level discoverer (D1/T1);
  - shortcut-residual individual discriminator (a principled UPGRADE over HMASD,
    which used raw log q_d with no shortcut correction — HA-CTSE is right that
    decoupling makes shortcut correction mandatory);
  - the variational-MI reward form.

SUPERFICIAL imitation:
  - conditioning the discriminator on g_tau while g_tau is causally dead (§2.2);
  - calling the parallel per-agent editor a "coordinator" when it has no
    complementarity channel (§2.3);
  - the "3+1" naming implies parity with HMASD's structure, but HMASD's
    load-bearing q_D (team) and autoregressive assignment are simply not in it.

MISSING entirely (must be reinvented under variable lifetime):
  - team-level / joint distinguishability pressure (q_D analogue);
  - complementary assignment (T4);
  - a causally-live team code.
```

### 2.7 Most likely failure mode, ranked

```text
1. MISSING COOPERATIVE STRUCTURE (highest): diverse-but-uncoordinated skills.
   P3-4 will raise force_disc_acc while selection entropy stays ~max and task
   metrics stay flat. This is the predicted, and most likely, outcome.
2. DEAD g: no team channel to carry cooperation even if individual skills improve.
3. Duration shortcut / SMDP confound: real, but secondary — they corrupt the
   signal, they are not the reason cooperation is absent.
4. Low-level capacity: single linear FiLM may be too weak for z to induce
   distinct persistent MODES (untested — P3-2e never run). Cheap to rule out.
5. Missing usefulness coupling: matters only AFTER 1–2 are fixed; irrelevant
   while there is no cooperative structure to make useful.
```

Note the ordering contradicts the current roadmap, which is spending its next
cycle on #3 (residualize effect) and treating #1/#2 as deferred.

---

## 3. P3/P4 intrinsic-reward redesign (general, no comm metrics)

Design principle: **reward joint/complementary distinguishability and individual
controllability, and couple to usefulness through advantage (task-generic), never
through communication fields.** Concretely, a four-channel intrinsic reward that
mirrors HMASD's four load-bearing parts under variable lifetimes:

### 3.1 Channel A — Complementary assignment (STRUCTURE, not reward; do this first)

This is the highest-leverage change and it is mostly not a reward at all.

```text
When >1 agent edits at a k-boundary, assign new skills so they are jointly
non-redundant. Two implementable options, cheapest first:

A1 (reward/regularizer, minimal code): add a co-edit REPULSION term to the
   high-level objective: penalize sum over co-editing pairs of
   sim(z_i, z_j) or agreement of induced effect-embeddings e(z_i), e(z_j),
   conditioned on g. Task-generic; directly fights redundancy.

A2 (structural, faithful to HMASD): make editing autoregressive OVER THE SUBSET
   of agents editing this boundary — z_i ~ π_z(·| g, o_i, z_{prev}, {z_j already
   assigned this boundary}). This restores T4 exactly, at the cost of a small
   sequential loop at edit time (n is small).
```

Do A1 immediately (it is a few lines and testable), design A2 as the principled
target. Either way, add the diagnostic `co_edit_skill_redundancy` and
`induced_effect_overlap`.

### 3.2 Channel B — Revive `g` causally BEFORE using it (gate everything on this)

Every team-conditioned term is vacuous while `g` is dead. Add an explicit
`g`-use objective and make it a hard gate:

```text
Δ_z(g_k, g_j) = KL( π_z(·|o, g_k) || π_z(·|o, g_j) )     # intervention sensitivity
L_g_use = - I(g ; induced skill/effect distribution)      # maximize g's causal effect
GATE: do not trust ANY team-discriminator or complementarity result while
      mean pairwise Δ_z is below a threshold (e.g. the 0.05 "decorative" band).
```

This is lifted directly from the hazard-SMDP note's coordination-mixture section
and is the correct prerequisite. It is also nearly free (the KL is a diagnostic
you can compute today).

### 3.3 Channel C — Team / joint discriminator (the missing cooperative source)

The variable-lifetime analogue of `q_D(Z|s)`. Task-general, no comm fields:

```text
R_team = log q_D(g | joint_state_window) - log p(g)
```

where `q_D` reads a window of the **joint** state (or the set of agents'
effect-embeddings), not any single agent. This rewards the team for driving the
joint state into `g`-discriminable regions — cooperative diversity. Inject at the
**high level** (it is a team signal; do not pollute primitive actions with it).
This is what actually pushes coordinated joint behavior, and it is exactly the
component HA-CTSE dropped. It only works once Channel B opens `g`.

### 3.4 Channel D — Individual residual discriminator (current P3, demoted to secondary)

Keep it, fix it, but stop treating it as the headline:

```text
R_disc_i = log q_d(z_i | effect_window_i, g)
         - max_shortcut log q_s(z_i | duration, length, reward, phase, agent, g, JOINT)
```

Fixes required: (i) residualize the effect "+1" term against duration/reward
baselines (the R8.3 bug — still live in code, `compose(disc_residual, gain_np)`
at skill_effect_discovery.py:1627-1630); (ii) add a kitchen-sink joint shortcut
head (marginal heads don't remove joint confounding); (iii) condition on `g`
only after Channel B. This channel makes `z_i` a controllable actuator; it does
not, by itself, make the team cooperate. That is the correct, humble role for it.

### 3.5 Should you use a conditional effect predictor?

Yes, but as a **controllability audit / grounding auxiliary**, not a diversity
source. `R_eff = log p(y|x,z) - max(log p(y|x), log p(y|x,d), log p(y|x,r))`
answers "does z control a short-horizon effect beyond shortcuts." Its best use is
to *gate* the discriminator (if z can't control any effect, don't reward
decoding it) and to feed Channel A's effect-overlap repulsion. Keep it low-weight.

### 3.6 Is usefulness coupling needed? Yes — via advantage, annealed

The task-generic usefulness signal is **advantage** (it already encodes env
reward, so usefulness enters exactly through HMASD's `λ_e r` path, NOT through
comm fields):

```text
R_intr_i = λ_ctrl · center_clip(force_i)
         + λ_use(t) · stopgrad(clip_pos(A_i)) · clip_pos(force_i)
```

To handle the circularity (advantage is sparse early, exactly when you need
diversity): **anneal λ_use from ~0 to positive** — a diversity-first curriculum.
Early training rewards pure controllability/complementarity (bootstrap skills);
as cooperative structure forms and advantage becomes informative, usefulness
coupling amplifies the skills that pay off. This mirrors HMASD's own weight
schedule (`w_intrinsic 3.0→1.0`, `w_extrinsic 0.5→1.5` in hmasd/agent.py). It
does NOT encode environment-specific metrics: `A_i` is defined for any MARL task.

### 3.7 Duration entropy: anneal as exploration, never force heterogeneity

```text
R_dur_explore = β_T(t) · H(π_duration(·|context)),  β_T decreasing to ~0.
```

Rules: (i) it is an *exploration bonus*, off by the end of training; (ii) do NOT
add a homogeneity penalty or a heterogeneity reward — forcing lifetime variance
is cheating and would manufacture the very result you want to claim is emergent;
(iii) **lifetime heterogeneity must be an emergent DIAGNOSTIC, not an objective.**
If, with complementarity + live g + usefulness coupling in place, lifetimes still
collapse to a shared period, that is an honest (partial) falsification of the
decoupling thesis on this task — report it, do not paper over it with a variance
bonus.

---

## 4. Theoretical positioning of variable lifetime

### 4.1 What is the contribution?

Not "decoupled lifetime" alone: variable lifetime is a strict superclass of fixed
k, so in principle it can only help; a bare superclass is not a contribution and,
worse, it inherits the SMDP + shortcut costs (§2.4–2.5) that can make it *worse*
in optimization. Not "the forcing loop" alone: that is HMASD's, re-derived.

The defensible contribution is the **conjunction**:

```text
"A mechanism that reconstructs HMASD's cooperative skill-discovery loop
 (complementary assignment + team/individual distinguishability + entropy)
 under ASYNCHRONOUS per-agent skill lifetimes, enabling heterogeneous temporal
 commitment (e.g. persistent relays alongside fast-switching servers) that a
 single shared k cannot express — and doing so without task-specific reward."
```

The forcing loop is the *enabling machinery*; decoupled lifetime is the *policy
class*; the claim is that the machinery makes the larger class usable and that
the larger class buys something a fixed k cannot.

### 4.2 Fair fixed/shared control

Hold **everything** constant except the lifetime mechanism, and run the SAME
forcing/discovery reward on all arms:

```text
B_fixed_sync   : k=1 edit-every-boundary (HMASD-like sync), + forcing.
C_shared_dur   : all agents share ONE learned duration d_t (may vary over time), + forcing.
D_decoupled    : per-agent independent duration/lifetime, + forcing.
```

Decoupling is supported iff `D > max(B, C)` on the coverage gate AND lifetime
heterogeneity/causal-use diagnostics are non-trivial. If `D ≈ B ≈ C`, decoupling
is inert here (report honestly). If `D < max(B,C)`, the optimization/credit
machinery is not yet good enough to use the larger class — a mechanism problem,
not a refutation.

### 4.3 If a task genuinely prefers a fixed period

Then the honest paper claim is *adaptivity*: variable lifetime **discovers** the
fixed period as a special case when that is optimal, while adapting when it is
not — provided you exhibit **at least one regime** (e.g. S7-S3, or a designed
mixed-role scenario) where heterogeneous lifetimes strictly help. Without that
one regime, the contribution collapses to "no worse than fixed," which is not
publishable. The whole empirical program should be organized around finding and
characterizing that regime, not around beating HMASD on S7-S1 (where, by the
project's own statement, HMASD already nearly saturates and fixed k is fine).

### 4.4 A note the memory should internalize

S7-S1 is a *parity/sanity* benchmark, not where the thesis lives. Matching HMASD
on a scene HMASD already solves cannot, even in principle, demonstrate the value
of decoupling (fixed k suffices there). S7-S1 parity is necessary to show the
machinery is not broken; the *contribution* can only be shown where fixed k is
insufficient. Budget accordingly: get S7-S1 parity cheaply, then move the whole
matrix to a heterogeneous-temporal regime.

---

## 5. Experiment & ablation matrix (priority-ordered)

Priorities reflect §0/§2.7: cooperative structure and cheap capacity/decoupling
tests come before more individual-discriminator engineering.

```text
P0. forced-z TRAJECTORY-spread capacity audit (P3-2e — never run)
    Purpose: is z a strong gate (distinct persistent modes) or a weak nudge?
    Expected: unknown; single linear FiLM makes weak-nudge plausible.
    Falsify: forced-z trajectories overlap at fixed o-history => architecture
             problem; NO reward will fix it. Fix conditioning first.
    Metrics: trajectory divergence vs one-step action_l2; FiLM γ/β magnitudes;
             fraction of actor variance explained by z vs o.
    If fail: strengthen conditioning (per-layer FiLM, skill-indexed GRU state,
             or hypernet) before ANY forcing sweep.

P1. reward-pure decoupling gate: D_decoupled vs B_fixed_sync vs C_shared_dur,
    NO forcing (finally complete the kmatrix treatment arms)
    Purpose: does decoupling help at all before semantics?
    Expected: likely D ≈ B ≈ C (cooperation absent regardless).
    Falsify: D not > max(B,C) AND heterogeneity trivial => decoupling inert here;
             the value must come from the forcing loop or a harder scene.
    Metrics: coverage==1.0 step-fraction, reward_std/mean, lifetime histogram,
             renewal_full_sync_rate, duration_usage_entropy.
    If fail: proceed to cooperative-structure mechanisms (P2), not to S7-S3.

P2. g-revival + complementarity (Channels B + A1), reward-pure-ish
    Purpose: turn the dead team channel on and stop redundant co-edits.
    Expected: g_itv/Δ_z rises above decorative band; co-edit redundancy falls;
              selection entropy starts to fall from ~0.998.
    Falsify: Δ_z stays ~0 even with L_g_use => the bridge/coordinator capacity is
             the bottleneck; redesign g (mixture, hazard-SMDP g).
    Metrics: pairwise Δ_z KL, g_to_skill_MI, co_edit_skill_redundancy,
             high-level selection entropy trend.

P3. force_disc_only (individual discriminator, residual, gated on P0/P2)
    Purpose: dense individual controllability pressure, HMASD's q_d spirit.
    Expected: force_disc_acc rises; alone, task metrics stay flat (predicted).
    Falsify: force_disc_acc does NOT rise even forced => back to P0 (capacity).
    Metrics: force_disc_acc, force_shortcut_best_acc, force_margin, effect gain.

P4. force_disc_effect, RESIDUAL-CORRECTED (fix R8.3 first)
    Purpose: add process-grounding without duration/reward contamination.
    Falsify: effect_gain_minus_duration_baseline <= 0 sustained => effect term is
             duration; drop it, do not raise its coef.
    Metrics: gain vs gain_minus_{duration,reward,context} baselines.

P5. team discriminator (Channel C) at high level, gated on P2 (g alive)
    Purpose: the missing cooperative diversity source.
    Expected: joint-state discriminability rises; recovery/coverage co-move.
    Falsify: q_D accuracy rises but coverage flat => joint diversity is
             task-orthogonal; couple to usefulness (P7) or revisit effect space.
    Metrics: team_disc_acc, coverage step-fraction, credit_recovery (DIAGNOSTIC).

P6. fixed-duration + SAME forcing control (B/C with P3–P5 on)
    Purpose: isolate decoupling from forcing (the R7.9/R8.1 control).
    Falsify: fixed+forcing >= decoupled+forcing => decoupling not the source of
             any gain; the paper claim must change.
    Metrics: the full D-vs-B/C comparison with all mechanisms on.

P7. usefulness coupling, annealed λ_use (Channel D of §3.6)
    Purpose: convert diverse+cooperative skills into useful ones.
    Falsify: adding λ_use changes nothing => separation-of-concerns was fine;
             or degrades => advantage too noisy, adjust anneal.
    Metrics: coverage step-fraction, selection entropy, return variance.

P8. duration-entropy anneal on/off (exploration only)
    Purpose: prevent early period collapse without forcing heterogeneity.
    Falsify: heterogeneity only survives WITH a variance bonus => not emergent;
             report as negative for the decoupling thesis.
```

Rule: **P0, P1, P2 come before pouring more into P3/P4.** The current plan runs
P3/P4 first; that ordering tests the least-likely bottleneck first.

---

## 6. Success & diagnostic metrics (general MARL, not comm-specific)

Gate (diagnostic only, never a reward): ≥ 50% of eval primitive steps reach
`coverage == 1.0`, plus low return variance and low zero-service-episode fraction.

General mechanism diagnostics (these are the ones to publish and to steer on):

```text
Skill discovery / differentiation:
  - forced-z TRAJECTORY spread (not one-step action_l2)
  - conditional effect gain, residualized vs {duration, reward, context}
  - shortcut gap = force_disc_acc - force_shortcut_best_acc (must stay > 0)
  - skill-action intervention KL: KL(π_l(·|o,z_k) || π_l(·|o,z_j))

Cooperation (the ones HA-CTSE currently lacks):
  - g intervention KL Δ_z(g_k,g_j) and g_to_skill_MI (is the team channel alive?)
  - co-edit skill redundancy / induced-effect overlap (complementarity)
  - team/joint discriminability accuracy (cooperative diversity)

Temporal structure (the thesis-defining ones):
  - skill lifetime distribution per agent + across-agent heterogeneity
  - renewal_full_sync_rate (must NOT be ~1), pairwise renewal correlation
  - duration_usage_entropy (annealing, not pinned high or collapsed)
  - skill_duration_MI (should be modest, not the source of "skill signal")

Selection health:
  - high-level skill SELECTION entropy TREND (should fall from ~max as skills
    specialize — flat-at-max = interchangeable skills = force not biting)
  - return mean AND variance; coverage==1.0 step-fraction (gate)
```

The one-line reading rule for the next sweep: `force_disc_acc ↑` with
`selection_entropy ≈ max` and `coverage_step_fraction` flat means
"distinguishable but not cooperative/useful" — i.e. evidence for §0, and the
signal to build Channels A/B/C, **not** to add a sixth debiasing head.

---

## 7. Prioritized code changes

```text
1. [cheap, high info] Run P3-2e forced-z TRAJECTORY-spread audit.
   Add a diagnostic that rolls out fixed o-history under each z and logs
   trajectory divergence + FiLM γ/β magnitudes. Decides whether the whole
   forcing direction is even well-posed. (standalone_agent.py actor path.)

2. [cheap, high info] Add g-intervention diagnostics: pairwise Δ_z KL and
   g_to_skill_MI, logged every update. Gate all team-conditioned rewards on
   Δ_z exceeding the decorative band. (Already specified in the hazard-SMDP note.)

3. [structural, highest leverage] Complementarity: implement Channel A1 co-edit
   repulsion in the high-level objective now; design A2 autoregressive-over-
   editing-subset as the faithful target. Add co_edit_redundancy metric.

4. [correctness] Fix R8.3: compose the effect term as
   gain - max(duration_base, reward_base), not raw gain
   (skill_effect_discovery.py:1627-1630). Keep effect_coef=0 until then.

5. [structural] Add the fixed-duration + same-forcing control ARM to
   run_p3_4_forcing_cloud_32env.sh (all arms currently share one
   SKILL_LIFETIME_CANDIDATES; add a candidates=(7,) + forcing arm). Enables P6.

6. [cooperative source] Implement Channel C team/joint discriminator at the high
   level (reads joint-state window or the set of effect-embeddings), gated on #2.

7. [usefulness] Wire annealed usefulness coupling from stopgrad(clip_pos(A_i))
   (advantage already available); λ_use anneals 0→positive. No comm fields.

8. [hygiene] Kitchen-sink joint shortcut head; wire OR remove the duration-entropy
   bonus (currently computed-and-logged, never composed — compose() ignores
   duration_entropy_coef).

9. [named alternative] If, across #3/#4 with the shortcut gap still ~0, the
   shortcut heads keep matching the discriminator, stand up the hazard-SMDP
   variant's Stage-1 (coordination-mixture diagnostics) as a PARALLEL cheap
   probe — termination-as-stopping-time removes the duration↔skill co-selection
   by construction (§2.5), serving the disentanglement goal more natively than
   the discrete-duration core. Do not treat this as break-glass only.
```

Ordering rationale: 1–3 test/repair the actual bottleneck (capacity + cooperative
structure) cheaply; 4–5 make the existing forcing read interpretable; 6–7 rebuild
the cooperative half of HMASD; 8 is hygiene; 9 is the principled fork if the
discrete-duration shortcut proves unremovable.

---

## 8. Direct answers to "which is which"

```text
GENUINELY inherits HMASD spirit:
  - dense micro-window intrinsic reward on the low-level discoverer;
  - shortcut-RESIDUAL individual discriminator (a correct upgrade for the
    decoupled setting — HMASD didn't need it, HA-CTSE does);
  - keeping env return as the high-level SMDP target (usefulness at the RL level).

SUPERFICIAL imitation (form without function):
  - conditioning discriminators/skills on a causally-DEAD g_tau;
  - a parallel per-agent editor labeled a "coordinator" with no complementarity;
  - "3+1 forcing" framed as HMASD-parity while omitting q_D (team) and
    autoregressive assignment — HMASD's two cooperation mechanisms.

MUST be reinvented under variable lifetime:
  - complementary assignment among asynchronously-editing agents (T4);
  - a team/joint distinguishability signal with non-stationary membership (q_D);
  - a stable team-context conditioning variable when the team context is no
    longer piecewise-constant on a shared k-grid;
  - clean high-level credit under γ^{T_i} (the SMDP confound).

MOST worthwhile next step:
  Stop hardening the individual discriminator. Run the two ~free diagnostics
  (P0 capacity, P2 g-intervention), then rebuild the cooperative half:
  co-edit complementarity (A1) + revive g (B) + team discriminator (C),
  gated in that order. The individual forcing loop (P3-4) is the SECOND term,
  and it should be read against the falsification "distinguishable but not
  cooperative," not against reward-off effect gain.
```

