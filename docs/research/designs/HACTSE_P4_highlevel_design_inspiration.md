# HA-CTSE P4 — High-Level Design Inspiration (co-design whiteboard)

Date: 2026-07-01
Author: CC (Cowork), co-designing with the user.
Status: design inspiration / living whiteboard for the P4-cooperative high level.
Not a spec. Enriches the agreed P3-individual / P4-cooperative split and respects
the three build gates (G1 capacity, G2 g-revival, G3 fractal-duration) and the
hard constraints (low-level invariant `a_i ~ π_l(a_i|o_i,z_i)`; `g` never enters
the low-level actor; no comm metrics in default reward; env reward is the
high-level SMDP return; variable lifetime must not collapse to fixed).

---

## 0. The one reframe everything hangs on

HMASD's cooperation came from a **synchronous snapshot**: every `k` steps all
agents re-roll `Z, z_{1:n}` together, autoregressively, so "the team plan" is a
single coherent object and individual skills are complementary *within that
snapshot*. Decoupling lifetimes destroys the snapshot — and that is precisely
what broke cooperation.

The instinct "recover synchrony somehow" is wrong; synchrony is the thing we are
paid to remove. The right move:

```text
Replace the synchronous team-skill SNAPSHOT with a persistent team INTENTION:
a slowly-evolving team latent g_t that is the invariant coordination FRAME,
which each agent re-reads only when IT renews.
```

Metaphor: a jazz group. The **key/tempo** (team intention `g`) changes slowly and
everyone hears it continuously. Each **player** (agent) holds a note (skill) for a
self-chosen duration and, when they change notes, they change *into the current
key* and *around what the others are currently playing*. Nobody re-rolls the whole
arrangement on a global downbeat. Harmony (complementarity) comes from everyone
committing *in the same standing key*, not from playing in lockstep.

This single reframe dissolves the central tension: **the team stays coherent
(shared slow key) while individual commitment is fully asynchronous (per-note
durations).** Disentanglement and cooperation stop fighting.

---

## 1. The paradigm in one loop

```text
Persistent team intention:      g_t = f_team(g_{t-1}, c_t)      # slow, recurrent, NOT re-rolled per agent
Per-agent renewal (async):      at agent i's own boundary only:
   dock into current frame:       z_i ~ π_z(z | g_t, o_i, ROSTER_{-i})    # ROSTER = standing teammate commitments
   commit for a lifetime:         T_i emerges (hazard) or d_i chosen
Low-level (unchanged):          a_i ~ π_l(a_i | o_i, z_i)                # g, roster, c never enter here
Ground the frame (G2):          joint discriminator predicts g from the team's joint process -> gives g a JOB
Compose sparse reward (credit): counterfactual contribution of each commitment to team SMDP return
```

Three legs, each solving one thing the decoupling broke:

```text
Leg 1  PERSISTENT INTENTION g      -> restores the stable team context (fixes non-stationary conditioning)
Leg 2  ASYNCHRONOUS DOCKING        -> complementarity without synchrony (fixes lost autoregressive assignment)
Leg 3  COUNTERFACTUAL COMPOSITION  -> assigns sparse team reward to the right commitment (fixes credit)
```

Everything below is the menu of concrete mechanisms for these three legs, with how
each maps onto the existing `ha_ctse_process` code and which gate it discharges.

---

## 2. Leg 1 — Make `g` a persistent team intention (and give it a job)

### M1. `g` as a slowly-evolving recurrent latent, not a per-agent re-sample

Today `g_tau = f_bridge(c_tau)` is re-derived per high-level call and is
decorative. Change it to a **recurrent team state** that persists across
individual edits:

```text
g_t = GRU_team(g_{t-1}, c_t)          # one team-level recurrence, slow
π_g optional: g_t ~ N(μ(h_t), σ) or a discrete code re-sampled on a SLOW team clock k_team >> per-agent edits
```

Why this matters: when agent i edits at t and agent j edits at t+3, they now
condition on the **same evolving `g`**. The team context is piecewise-stable
instead of re-rolled out from under each agent. This is the structural fix for the
"non-stationary conditioning" failure (my review §2.2). Code: make
`CompactTeamBridge` carry hidden state across steps rather than mapping `c_tau`
fresh each call.

Design fork worth deciding early: **two clocks, explicitly.**

```text
k_team  = slow team-intention clock (g may change here)   -- coordination frame
T_i     = per-agent skill lifetime (fast, asynchronous)   -- the disentangle
```

Keeping `k_team` slow and shared is what lets asynchronous agents stay coherent.
`k_team = 1` (g every step) is the smooth limit; `k_team = ∞` (g fixed per
episode) is the "single standing plan" limit. This is a clean, tunable axis.

### M2. Ground `g` with a JOINT discriminator — this is the G2 reviver, not the co-edit editor

`g` is decorative because *nothing requires it to carry information*. The reviver
is a loss that gives `g` a job independent of current return:

```text
R_joint_residual =  log q_D(g_t | JOINT effect-window, {z_i}, {age_i})
                 -  max( q_context(g | global ctx, phase),
                         q_marg(g | pooled INDIVIDUAL effects),     # <- the load-bearing shortcut
                         q_dur(g | {d_i} pattern),
                         q_reward(g | segment reward) )
```

The critical shortcut head is `q_marg`: does the **joint** process carry `g`-info
*beyond the sum of individuals*? If not, `g` is not encoding cooperation, only
aggregated solo behavior. **Wire this discriminator's gradient to flow into `g`
(the team recurrence), not only into `q_D`'s params** — that is the exact wiring
question I handed back to Codex, and it is the highest-leverage line in the plan.
Diagnostic-first (reward-off): gate any `g`-reward on `joint_residual_gain > 0`
AND `g` intervention KL above the decorative band.

Note (G3, fractal duration): the `{d_i}` shortcut head here is where the
duration↔skill co-selection re-appears at the team level. If `q_dur` keeps winning,
that is the trigger to move to hazard lifetimes (M6), not to add more heads.

---

## 3. Leg 2 — Asynchronous docking = complementarity without synchrony

The question decoupling makes hard: *how do agents pick complementary skills when
they choose at different times?* Three mechanisms, weakest→strongest, all
task-generic (no comm fields). The recommendation is M4.

### M3. Stigmergic roster conditioning (cheapest)

Make the **standing roster of teammate commitments observable to the editor** and
condition on it:

```text
ROSTER_{-i} = { (z_j, age_j, remaining_i, e_j = effect_embed(z_j)) : j ≠ i }
z_i ~ π_z(z | g_t, o_i, pool(ROSTER_{-i}))
```

Agents coordinate *through the shared observable roster* (stigmergy) rather than
through a central synchronous assignment. An editing agent sees what everyone is
currently committed to and can avoid redundancy. This is the async-native version
of "condition on teammates." Nearly free; a good first step. Weakness: it only
*enables* complementarity, it doesn't *pressure* it.

### M4. Roster-attention autoregressive docking editor (recommended)

Extend GPT's co-edit AR editor with a transformer (HMASD-MAT-style) that attends
over the **full roster** (kept + editing agents), and assigns skills to the
editing subset autoregressively:

```text
E_t = agents editing this boundary
h = TransformerEncoder( [g_t] + { token_j = (o_j, z_j, age_j, kept/editing flag) } )
for i in order(E_t):          # autoregressive over the editing subset only
    z_i ~ π_z(z | h, previously-assigned edits this boundary)
    append z_i to context
```

Properties:
- **Contains HMASD as a special case**: when everyone edits at once (`E_t = all`),
  this *is* HMASD's autoregressive coordinator. So the mechanism strictly
  generalizes HMASD to the asynchronous regime — a clean paper story.
- Kept agents' standing skills are the team context tokens; new edits are
  complementary to them by construction.
- Known limitation (state it honestly): assignment is **asymmetric** — kept agents
  don't re-adapt to a newly-edited teammate until their own renewal. This is the
  price of asynchrony; it is also *why* you still want a persistent `g` (M1) as the
  slower coherence glue that both kept and editing agents share.

Code: replaces the per-agent MLP high-level (`standalone_agent.py` high head) with
an attention module over agents. Bigger change, but it is the faithful migration.

### M5. Set-coverage over effect-prototypes (the complementarity OBJECTIVE, task-generic)

M3/M4 are architecture; this is the *pressure*. Don't reward "all skills different"
(that manufactures useless diversity — HMASD itself finds only ~24% of skills
useful). Reward the **team's active skill set for COVERING the effect-prototype
space, gated by usefulness:**

```text
prototypes μ_1..μ_P = learned effect-mode centroids (from generic motion/energy effects, NOT comm)
coverage_t = | { p : some active z_i has effect-embedding near μ_p } |   (soft, differentiable)
R_comp = stopgrad( clip_pos( DEBIASED team advantage ) ) * ( coverage_t - redundancy_penalty )
```

Two things make this right:
- **Set-level, not pairwise**: cooperation is a property of the joint set of
  commitments, not of pairs. Coverage is a set function → naturally expresses
  "we need a relay AND a server," not "agents 1 and 2 must differ."
- **Advantage-gated**: complementarity is only rewarded where it *pays off* in team
  return. This is the task-generic usefulness coupling (advantage carries env
  reward; no comm fields), and it prevents diverse-but-useless collapse.

This is the variable-lifetime analogue of the team discriminator's *purpose*
(make the team's joint behavior structured and useful), expressed as a set-coverage
credit rather than a single-label classification.

---

## 4. Leg 2b — Let `g` select a TARGET effect-mixture (the controllable team code, done right)

The principles want `g` to be "a compact-conditioned controllable team coordination
code," verified by intervention on `π_z`. Concrete, task-generic realization:

```text
g_t  ->  target distribution over effect-prototypes  ρ_target(g_t) ∈ Δ^P
docking picks z_i to fill the GAP between ρ_target and what the roster already covers:
   z_i ~ π_z( · | g_t, o_i, ρ_target - coverage(ROSTER_{-i}) )
```

Now `g` has a crisp, controllable, testable meaning: **`g` says what mixture of
behavior-modes the team should be producing; agents asynchronously fill the mixture.**
Intervention test (G2): force `g = g_k` vs `g_j`, check `ρ_target` and the induced
`π_z` shift (KL). If `Δ_z ≈ 0`, `g` still isn't controlling anything. This turns the
vague "revive g" into a falsifiable target-mixture controller.

---

## 5. Leg 3 — Counterfactual composition credit (the actual binding failure)

`credit_recovery_rate ≈ 0.01` everywhere says the real wall is **assigning sparse
team reward to the right commitment.** The task-generic tool is a difference /
counterfactual reward over *skill choices* (COMA-style, but at the skill level, and
using the centralized critic you already have):

```text
A_i^skill = Q_team(s, z_i, z_{-i}) - Σ_{z'} π_z(z'|·) Q_team(s, z', z_{-i})
```

- Uses only the centralized value `V_l(s, joint skills)` / `Q_team` you already
  train — **no comm fields**, purely task return.
- Credits agent i's *skill commitment* by its marginal effect on team return,
  holding teammates' commitments fixed. This is exactly "which skill process
  deserves the delayed team reward," and it is what P1/P2-lite were groping toward
  without the counterfactual structure.
- **Debias the SMDP horizon**: because lifetimes vary, weight by a horizon-normalized
  advantage (divide out `γ^{T_i}` scale, or use per-duration value normalization),
  so long commitments aren't credited merely for reducing critic variance. This is
  the G3-adjacent fix at the credit level.

Pair this with M5's advantage gate (same debiased advantage) so *discovery*
(coverage) and *credit* (counterfactual) are driven by the same task-generic signal.

---

## 6. Leg 1b (optional, powerful) — Hazard lifetimes make disentanglement native and kill the shortcut

Discrete duration buckets `d_i` co-selected with `z_i` are the root of the fractal
shortcut (G3). The clean alternative: **lifetime as an emergent stopping time.**

```text
β_i,t = σ( h_β(o_i,t, z_i, g_t) )        # per-step continue/terminate hazard
T_i = first t where Bernoulli(β) fires (or episode/rollout boundary)
```

Why this is the *native* disentangle mechanism, not just a debias:
- Duration stops being a **label chosen beside the skill** and becomes a
  **consequence of the running skill under the state** → the duration↔skill MI is
  now *behavioral* (right kind) not *co-selected* (shortcut kind). G3 dissolved by
  construction.
- Lifetimes are maximally, continuously asynchronous — the strongest form of the
  disentangle claim, and it can't collapse to a shared grid unless the *states*
  make it.
- `g_t` in the hazard is a subtle, powerful coordination channel: the team intention
  can modulate *when* agents renew (synchronize a shared push, desynchronize to keep
  a relay standing) without touching primitive actions.

Migration: keep discrete `d_i` as the stable baseline/control (per the on-policy
boundary rules), introduce hazard as a named variant, store per-step termination
log-probs for PPO. The IC-SPL note already sketches this; the reframe here is that
it is not a break-glass fallback — **it is the most honest realization of "disentangle
the skill cycle."**

---

## 7. Why heterogeneous lifetime becomes LOAD-BEARING (anti-collapse by design)

The requirement "must not collapse to fixed" needs a *reason* heterogeneity is
useful, or it will collapse. This paradigm supplies one:

```text
Under M4 + M5, the team intention is filled by agents committing at DIFFERENT
horizons: a stable relay must hold its skill LONG (persistent coverage of one
prototype), while a server re-docks SHORT (chases a moving target prototype).
The COMMITMENT-DURATION PATTERN is itself part of the coordination: heterogeneous
T_i is how the team covers a mix of stable and volatile roles simultaneously.
```

So collapse-to-fixed would *destroy* the ability to cover stable + volatile roles
at once → the mechanism has an intrinsic gradient toward heterogeneity *when the
task has heterogeneous temporal structure*, and legitimately toward homogeneity
when it doesn't (fixed is then the correct special case, honestly reported). This
is the principled anti-collapse argument, and it's also the paper's core empirical
claim: **find the regime where the commitment pattern must be heterogeneous.**
Duration entropy stays a *decaying exploration bonus only* (never a heterogeneity
reward) — the heterogeneity must emerge from coverage+credit, or it isn't real.

---

## 8. Minimal first-implementable version (don't boil the ocean)

Tie to the agreed staged plan; this is the smallest thing that tests the paradigm:

```text
MVP-P4 (diagnostics-first, reward-off where possible):
1. M1  persistent recurrent g (make CompactTeamBridge carry hidden state).       [small]
2. M2  joint discriminator, gradient WIRED INTO g; reward-off; log
       joint_residual_gain + g intervention KL.                                   [core: G2 test]
3. M3  roster conditioning on the existing per-agent editor (cheap M4 stand-in).  [small]
4. M5  effect-prototype coverage metric (reward-off diagnostic first).            [small]
5. Credit: counterfactual A_i^skill from the existing centralized critic,
       debiased by horizon; start as a DIAGNOSTIC, then a small high-level term.   [medium]

Defer to MVP+1: M4 full roster-attention editor; M6 hazard lifetimes; g->target
effect-mixture controller (M4/§4). Keep discrete durations first.
```

Gate order (respecting G1/G2/G3):
```text
G1 first: P3-2e says z induces MODES  -> else fix conditioning, do not build P4 on sand.
G2 gate:  joint-disc gradient reaches g AND g-intervention KL rises  -> else g stays decorative.
then:     turn on coverage + counterfactual credit at small coef; read task metrics + heterogeneity.
```

---

## 9. Falsifiable predictions (so we know if the paradigm is real)

```text
If the paradigm is right, turning on M1+M2+M3+M5+credit should produce:
  - g intervention KL rises above the decorative band (g controls π_z/target mixture);
  - joint_residual_gain > 0 beyond the q_marg (pooled-individual) shortcut;
  - co-edit redundancy FALLS; effect-prototype coverage RISES;
  - high-level selection entropy falls from ~0.998 toward context-specialization;
  - coverage==1.0 step-fraction rises (the gate) WITH lower return variance;
  - lifetime heterogeneity emerges WITHOUT a duration-variance bonus.

Kill conditions (paradigm wrong or mis-built):
  - g-KL stays ~0 even with joint-disc gradient into g  -> g has no capacity/path; redesign the team recurrence, not the reward.
  - coverage rises but task flat                          -> coverage is task-orthogonal; the advantage gate is too weak or effect space is wrong.
  - counterfactual credit adds variance faster than signal -> critic can't estimate Q_team(s, z_i, z_{-i}); need a better joint-skill value head first.
  - heterogeneity only with the entropy bonus             -> the task has no heterogeneous-temporal structure; narrow the claim (fixed is fine here), move to a regime that does (S7-S3 / designed mixed-role scene).
```

---

## 10. Honest risks / open questions

```text
1. Counterfactual credit needs Q_team(s, z_i, z_{-i}); the current critic is
   V_l(s, Z)-style. Estimating skill-counterfactuals may need a joint-skill-
   conditioned value head or a learned marginalization — non-trivial; prototype it
   as a diagnostic before trusting it as reward.
2. Roster-attention editor + persistent g is a real architecture change to the
   high level and its on-policy update boundary (async terminations, per-step
   hazard log-probs). Get the PPO data contract right (close segments at
   hazard-fire / episode-end / rollout-boundary; invalidate cross-version samples).
3. The paradigm has more moving parts than P3-4. Resist turning them all on at
   once — the MVP order exists so each leg is falsifiable in isolation.
4. "Persistent g + target mixture" risks becoming a second decorative latent if
   the joint discriminator gradient into g is weak. The g-intervention KL is the
   permanent tripwire; keep it logged on every run.
5. Effect prototypes are learned from generic motion/energy effects — verify they
   are rich enough to express the roles the task needs WITHOUT reading comm fields.
   If generic effects can't express the needed role structure, that is a real
   tension between the generality boundary and task-fit (my Round 9 §4 concern),
   and it should be surfaced, not hidden.
```

---

## 11. One-paragraph paper framing (if this works)

> We introduce **asynchronous option composition** for cooperative MARL: a
> persistent team-intention latent provides a slow, shared coordination frame into
> which agents dock skills at heterogeneous, individually-determined horizons. A
> joint discriminator grounds the team latent as a controllable target over
> behavior-effect modes; agents achieve complementarity by asynchronously covering
> that target given teammates' standing commitments; and a horizon-debiased
> counterfactual reward composes sparse team return across asynchronous
> commitments. The framework contains synchronous hierarchical skill discovery
> (HMASD) as the all-agents-edit-together special case, while enabling heterogeneous
> temporal commitment that a single shared skill interval cannot express.
```
