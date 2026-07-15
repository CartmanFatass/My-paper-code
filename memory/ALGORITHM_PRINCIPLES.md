# HA-CTSE Algorithm Principles

This document is the implementation contract for Horizon-Aware Compact-Team
Skill Editing / process-core exploration, abbreviated HA-CTSE. It intentionally
separates HMASD-inspired controllable skills from OPT-style interaction
representation and from a direct copy of the old HMASD discriminator training
target.

## Active R22 Contract: Two-Clock R21/v6 Mainline

> 2026-07-06 R21 AUTOPSY-CONFIRMED AMENDMENT (accepted from data; CC autopsy +
> GPT concurrence, see `memory/R21_AUTOPSY_REPORT.md`, `cross_validation.md`
> "2026-07-06 R21 autopsy" and "2026-07-06 GPT post-autopsy advice").
> R21 sampled team-intent Z is **mechanism-NEGATIVE, primary cause
> `true-objective-failure` / no actionability** — now autopsied, no longer a
> pending hypothesis:
>
> ```text
> - Team-disc data contract is ALIGNED-REAL (lockstep label/state; no leakage;
>   held-out control reproduces chance) -> team_disc_acc≈chance is genuine, NOT a bug.
> - Forced-Z assignment KL ≈0.002 at BOTH random-init AND final -> Z was NEVER
>   made actionable (not "trained out"). It is behaviorally near-inert on assignment.
> - K_team=48 ≈ episode=50 intervals -> ~one Z commitment/episode; two-clock
>   degenerated to one-clock; duration-truncation reads INVALID. This K≈episode
>   setting is a forbidden two-clock configuration.
> - Task regression is a policy-path effect (forced AR-roster/Z-conditioning),
>   NOT Z-boundary churn.
> ```
>
> Current-state contract consequences (all accepted):
> 1. The "Commitment layer: sampled team intent Z = slow synchronized commitment /
>    cooperative exploration source" claim below is DEMOTED to **negative evidence /
>    autopsy input**. v6 "R21/v6 sampled-Z" is NOT an active mainline success
>    candidate.
> 2. The cross-layer actionability term `I(Z ; xi | c, omega)` is **REQUIRED** (not
>    optional) for any future team intent; the two-clock ELBO (PR-1) must resolve it.
> 3. Any future `q_D(Z | ·)` reward is **FORBIDDEN unless `forced_Z_assignment_KL`
>    passes an actionability floor** (floor value TBD in PR-1) — otherwise it is
>    provably decorative (this run).
> 4. NEW (architecture, from random-init forced-Z KL≈0.002): the Z→assignment
>    architectural gain is itself too weak. Before any R23 build, a STATIC capacity
>    gate must show random-init forced-Z assignment KL clearly above the decorative
>    band (e.g. Z as the true AR first token / Z-FiLM on skill/duration/edit heads),
>    with the low-level actor kept blind to Z/c and the S-base selection path
>    otherwise unchanged to avoid the policy-path confound.
> 5. Future two-clock runs must use `team_intent_k ≪ episode horizon`; because
>    `K ≥ 2·max_duration` is near-impossible at 50 checks / max_duration 24, prefer
>    short duration candidates with K≈8-12 (mechanism test) before attempting truly
>    decoupled parent-child lifetimes. A short-duration mechanism test validates
>    actionability, NOT the decoupled-lifetime contribution — keep the two claims
>    separate.
>
> Forward line (2026-07-06, ACCEPTED as active): **R23 Actionable Team Intent**,
> spec `memory/R23_ACTIONABLE_TEAM_INTENT.md`. Order: Z → ξ (actionability) →
> effect → only then q_D. R23-0 static capacity gate is DONE and the §3
> architecture correction is IMPLEMENTED default-off (`z_assignment_residual_gain`;
> flag-on random-init PASSES the gate at skill KL 0.12, flag-off keeps S-base
> bit-identical). q_D(Z|·) reward stays FORBIDDEN until the forced-Z-KL floor +
> q_A-gain gate pass. Do not sweep R21. The HMASD current-env baseline is NOT a
> blocking premise (user 2026-07-06: solid/well-tested; at most one appendix run).
> Remaining R23 stages (actionability objective, q_D probe/reward, individual q_d)
> need training runs and explicit authorization.

The 2026-07-05 GPT-5.5 Pro review is accepted as a current principles
amendment with one operational constraint: it does not block the already
launch-ready R21 and HMASD baseline runs.  It does change the algorithmic
interpretation:

```text
Recognition layer:
  OPT / omega / compact c / optional kappa
  = continuous interaction-situation substrate.

Commitment layer:
  sampled team intent Z
  = slow synchronized team commitment and cooperative exploration source.

Response layer:
  asynchronous individual skills z_i
  = per-agent response skills docked to current Z and local observation.
```

Therefore the current HA-CTSE mainline is:

```text
OPT recognition substrate -> sampled slow team intent Z ->
asynchronous response skills z_i -> team/individual discriminator-style
pressure under a two-clock SMDP objective.
```

R12 recognition-first / situation-response work is retained as substrate and
control, not as the main cooperation engine.  R19 team-transition residual work
is retained as a recognition-only control unless complete reward-on evidence
later contradicts the current mechanism-negative read.

The next principles task is to derive a two-clock ELBO/objective for the actual
current model.  That derivation must decide whether the following terms compose
or double-count:

```text
team discriminator residual for sampled Z
individual / coordinator residual for z_i
entropy terms for Z, z_i, duration/edit, and action
optional cross-layer term I(Z ; joint response / roster / xi)
```

Entropy is not a direct reward for heterogeneity.  It may be part of a derived
objective or target-entropy constraint, just as HMASD's entropy terms were part
of its lower-bound objective.  Duration or Z entropy floors remain explicitly
labeled stabilizers unless and until they are replaced by a principled
per-head target-entropy mechanism.

Mechanism budget rule:

```text
Every new mechanism must retire, absorb, or formally supersede one existing
mechanism.  Terms absent from the R22 two-clock objective default to deletion
candidates, not protected modules.
```

## Primary Benchmark Objective

The corrected near-term objective is S7-S1 parity with HMASD, not immediate
S7-S3 optimization.  The earlier "100M steps" wording was a misstatement; a
budget on the order of `1e6` environment steps is the more normal first long-run
scale for the current S7-S1 tests.

S7-S1 is a relatively simple calibration scene where HMASD is already close to
solving the task.  HA-CTSE should first reach the same level on this scene under
matched physical settings, comparable network scale, and comparable training
budget.  Failing S7-S1 usually means the new asynchronous lifetime design or its
credit signals are not yet competitive enough to justify harder benchmarks.

User clarification 2026-07-01: "HMASD-level" on S7-S1 primarily means the
policy can sustain near-perfect communication coverage for a relatively long
time in the environment's UAV/base-station service metric, not merely produce a
high average return spike.  Reward mean alone is insufficient; the parity read
must include stability, long-window coverage, and the fraction of failed /
zero-service episodes.  This is an evaluation milestone, not permission to make
communication metrics the intrinsic reward target.

Additional clarification 2026-07-01: the concrete S7-S1 coverage gate is that
at least half of evaluation primitive steps should reach `coverage == 1.0`
under the environment's UAV/base-station communication coverage metric.  This
does not replace the need to check variance and failed episodes; it defines the
minimum "long enough near-perfect coverage" signal.

User clarification 2026-07-03: HMASD's useful convergence on S7-S1 should be
read at roughly the `1e6`-step scale, where it can maintain a high average
coverage level.  Therefore 160k/320k HA-CTSE runs are mechanism gates and
debugging reads, not final performance comparisons against HMASD.  A 320k read
can falsify a broken mechanism (collapse, reward contamination, no residual
signal), but it should not be used to claim that HA-CTSE cannot match HMASD
unless the same mechanism also fails at the agreed long-run scale.

S7-S3 and other harder long-horizon UAV service settings remain the later
motivation: HMASD performs poorly there, and HA-CTSE should eventually aim to
match or outperform it while retaining the central structural claim:

```text
different agents may need different high-level skill lifetimes under different
local roles and topology situations
```

Therefore the current experimental hierarchy is:

1. Use S7-S1 as the active near-term milestone: match HMASD-level behavior,
   service metrics, and stability before moving on.
2. Use S7-S1 diagnostics to validate implementation, network-scale parity, data
   flow, asynchronous lifetime usage, and cooperative credit.
3. Defer S7-S3 until the S7-S1 parity gate is credible.
4. Judge P1/P2/P2-lite as support mechanisms for restoring or improving
   cooperative credit under the asynchronous lifetime design, not as the final
   thesis by themselves.

For both S7-S1 and later S7-S3, the mechanism evidence should include not only
reward/coverage/QoS/throughput, but also whether per-agent lifetime selection is
used nontrivially and whether it improves cooperation instead of producing
unstable desynchronization.

## Falsifiable Decoupled-K Hypothesis

The core mechanism claim must be falsifiable:

```text
Under the same global high-level check interval k,
per-agent realized lifetime T_i improves cooperative MARL compared with
full-sync or shared/fixed lifetimes.
```

Definitions:

```text
k   = global team information/check clock
T_i = realized lifetime of agent i's active skill process
```

Main hypothesis:

```text
Different agents in different local roles/topology states need different T_i.
Decoupling T_i from the global k can improve stable cooperation under sparse
team reward.
```

Required controls:

```text
A. HMASD original baseline
B. HA-CTSE full-sync fixed-k / T_i = 1 check interval, reward-pure
C. HA-CTSE shared fixed duration, reward-pure
D. HA-CTSE fixed-clock per-agent KEEP/SET lifetime, reward-pure
E. best fixed/shared + P2-lite H0/H1
F. best decoupled + P2-lite H0/H1
```

P2-lite cannot prove decoupled-K by itself.  The question is:

```text
Effect_decoupling_reward_pure = D_reward_pure - max(B_reward_pure, C_reward_pure)
Effect_decoupling_with_P2     = D_P2 - max(B_P2, C_P2)
Effect_credit                 = D_P2 - D_reward_pure
Interaction                   = Effect_decoupling_with_P2 - Effect_decoupling_reward_pure
```

The decoupled-K claim is supported only if D beats the best fixed/shared control
and the mechanism does not collapse to synchronized or homogeneous lifetimes.

Mechanism gates:

```text
lifetime_heterogeneity up
renewal_full_sync_rate not near 1
survival beyond the retired duration cap is nonzero
agent-wise lifetime distribution nontrivial
renewal_pairwise_corr_mean not full-sync
KEEP does not collapse to always-keep or always-switch
switch-time skill usage is non-degenerate
```

If reward improves but the policy uses one survival pattern for all agents,
renews all agents together, or merely learns a new fixed-k schedule, the decoupled-K
mechanism has not been demonstrated.

User clarification 2026-07-01: collapse to a fixed/shared lifetime is not an
acceptable HA-CTSE mechanism outcome.  It may indicate that the current
environment/run found a fixed-period local optimum, but the intended UAV
cooperation setting contains heterogeneous roles such as stable relay behavior
and user/service tracking; a variable-lifetime algorithm that cannot maintain
nontrivial heterogeneous lifetimes has not delivered the intended contribution.

Important correction: the decoupled-K experiment is not the final research
target.  Variable lifetime is a larger policy class that can include fixed
lifetimes as a special case.  Therefore a fixed-duration control outperforming a
variable-duration run should not be read as "variable lifetimes are useless"; it
usually means the current optimization, intrinsic reward, or credit mechanism
does not yet let the variable-lifetime controller find the useful special case.

The real research target is:

```text
Under asynchronous / variable skill lifetimes, reconstruct the HMASD-like
internal drive that makes skills discovered, differentiated, and useful.
```

This means the central problem is not candidate-set tuning.  It is how to make
the larger variable-lifetime system develop:

```text
skill discovery       -> skills acquire temporally coherent effects;
skill differentiation -> different skills/roles induce distinguishable behavior;
actually-work drive   -> intrinsic pressure helps solve sparse cooperative reward
                         instead of only producing diagnostic classifier scores.
```

The K-matrix is therefore an inclusion/optimization sanity gate.  It checks
whether the variable-lifetime implementation can at least approach strong fixed
controls and whether asynchronous renewal creates obvious instability.  It does
not by itself establish the scientific value of decoupled lifetimes.

## General MARL Objective Boundary

HA-CTSE is intended to be a general MARL algorithm, not a UAV-backhaul heuristic.
The Scenario-7 UAV communication task is used because it is a representative
hard cooperation benchmark: reward is sparse/complex, credit assignment is
difficult, and stable team behavior is required before the task reward becomes
consistently available.

Backhaul, relay recovery, full-disconnect rate, and conditional throughput are
diagnostic probes for whether cooperation and credit assignment are working in
this benchmark.  They must not become the definition of the algorithm objective.
Directly aiming the policy at "make backhaul" would introduce strong
task-specific bias and weaken the claim that HA-CTSE is a transferable MARL
method.

Allowed use:

```text
backhaul/recovery metrics -> diagnose cooperation, sparse-reward access, and
credit assignment; optionally provide small, gated shaping probes.
```

Disallowed use:

```text
backhaul/recovery metrics -> replace the task objective or become the main
algorithmic target.
communication-specific fields -> direct intrinsic reward or direct usefulness
                                  coupling for the general MARL algorithm.
```

P1/P2/P2-lite must be interpreted under this boundary.  A run that improves
backhaul metrics but does not improve reward, QoS, throughput, coverage, or
variance is not a success for HA-CTSE.  Conversely, a useful credit-shaping
mechanism should help the policy discover generally better cooperative behavior,
not merely hard-code one communication-topology preference.

User clarification 2026-07-01: for P3/P4, do not use raw communication
indicators as the forcing reward or usefulness multiplier.  They remain
evaluation/diagnostic signals for this benchmark.  If usefulness coupling is
needed, prefer task-generic MARL quantities such as policy advantage, TD/value
improvement, or non-domain-specific controllability/progress estimates.

Additional clarification 2026-07-01: do not turn environment reward into an
"intrinsic" reward surrogate.  HMASD's intrinsic terms come from discoverer /
discriminator-style skill pressure, while environment reward remains the
external task return.  HA-CTSE should preserve that separation.  High-level
targets may still include cumulative environment reward over the skill lifetime
plus separately defined intrinsic terms, but the intrinsic terms themselves
should not be direct functions of communication reward or raw task reward.

User clarification 2026-07-14: the original HMASD sparse-exploration claim was
not obtained by adding task-distance potential shaping to the environment.
Any HA-CTSE experiment used to support sparse exploration or HMASD parity must
therefore keep the benchmark's external reward sparse and treat distance,
contact, progress, coverage, or other environment-derived shaping as a separate
task-specific ablation.  Environment shaping is neither algorithmic intrinsic
reward nor evidence that the algorithm reconstructed HMASD's exploration loop.

User clarification 2026-07-15: intrinsic reward is environment-agnostic by
contract. It may not read, encode, or be redesigned around benchmark-specific
goals, objects, identities, contacts, phases, distances, success predicates, or
external reward. Its mathematical form and input contract must remain the same
across environments. Benchmark access failures are handled through observation,
dynamics, and an ordinary-policy access gate; intrinsic reward must not be used
to conceal or repair them.

## HMASD As Inspiration

HMASD contributes useful structural ideas and cooperation priors, not a block to
copy unchanged:

- explicit team skill or team coordination latent;
- executable individual skill `z_i`;
- autoregressive high-level assignment spirit, where each individual skill can
  depend on the team latent and previous individual decisions;
- a global high-level information/check interval `k`;
- low-level actor `pi_l(a_i | o_i, z_i)`;
- optional centralized low-level value estimation.

HMASD's discoverer/discriminator architecture has real value for cooperative
tasks.  The discoverer gives low-level skills temporal control capacity, while
the discriminator reward supplies skill-semantic pressure that can make
cooperative roles separable.  The process-core algorithm should distill these
functions, not blindly inherit the exact one-step discriminator target.

2026-07-01 Claude/GPT review synthesis:

HMASD's paper-grounded lesson is not exhausted by the individual discriminator.
The cooperative part of HMASD also depends on a live team skill / team context,
team-level distinguishability, and complementary high-level assignment.  In the
original algorithm this is expressed through the team skill `Z`, team
discriminator `q_D(Z|s)`, and autoregressive individual assignment
`z_i | Z, z_{1:i-1}`.  HA-CTSE currently keeps the individual skill bottleneck
and is rebuilding individual skill differentiation through P3, but it must also
rebuild the cooperative half under asynchronous lifetimes:

```text
live team/coordination context
-> complementary or non-redundant co-editing decisions
-> team/joint distinguishability or cooperative diversity signal
-> high-level composition of individually executable skills
```

Therefore P3 individual forcing is necessary but insufficient.  A run where
`force_disc_acc` rises while high-level selection stays near-uniform and
coverage/reward stability do not improve should be read as "distinguishable but
not cooperative/useful", not as evidence that more individual discriminator
pressure alone is the right next step.

Accepted implementation implication: before trusting more long P3-4 sweeps, add
short diagnostics for skill-conditioning capacity and cooperative structure:
forced-z trajectory spread, pairwise `g` intervention sensitivity, co-edit
redundancy/complementarity, and teammate-churn / async-confound metrics.  Then
design a cooperative-half mechanism, such as live-`g` revival,
co-edit complementarity pressure, and a team/joint discriminator, with
communication metrics remaining diagnostics rather than default reward terms.

In this reconstruction, skill exploration is judged by whether latents induce
useful and persistent behavior processes.  A classifier can be used as a
variational tool for semantic separation or credit diagnostics, but single-step
label recovery alone is not sufficient evidence that the skill process is useful.

## Decoupled Skill Cycles With HMASD's Cooperative Spirit

The core HA-CTSE hypothesis is:

```text
decouple each agent's high-level skill cycle/lifetime,
then rebuild the HMASD-style mechanisms that overcome sparse reward and
cooperative credit assignment under this asynchronous temporal structure.
```

This means HA-CTSE should not merely remove HMASD's fixed synchronized skill
interval.  Once skill cycles are decoupled, the algorithm must explicitly
reconstruct the functions that made HMASD effective in cooperative sparse-reward
tasks:

1. **Low-level execution capacity** from the discoverer: skills must control
   temporally coherent behavior, not just label actions.
2. **Skill/role semantic pressure** from the discriminator: different latents
   should become behaviorally and cooperatively distinguishable, but the target
   must be redesigned for process segments rather than copied as a one-step
   label classifier.
3. **Exploration pressure** from high-level, low-level, and latent entropy:
   decoupled lifetimes make exploration more fragile, so entropy and usage
   diagnostics must be tracked separately for team code, skill, duration, and
   primitive action.
4. **Credit densification** for sparse cooperative rewards: auxiliary signals
   should help assign delayed team outcomes to useful skill processes without
   turning the algorithm into a task-specific heuristic.

### 2026-07-01 Cooperative-half correction (Round 10, user-confirmed)

Reframing after the HMASD-paper-grounded review
(`memory/HMASD_HACTSE_research_review_20260701_Claude.md`, digested as cross_validation
Round 10). The program has been over-translating the **cooperation problem** into
the **individual-skill-semantics problem**. P3/P3-4 implements only:

```text
z_i -> low-level behavior/effect -> discriminator/forcing -> skill differentiation
```

which is the individual half of HMASD (individual skill + individual
discriminator). HMASD's ablation (§4.3) shows the load-bearing cooperative half is
separate and equally necessary:

```text
team skill Z
team discriminator q_D(Z | s)
autoregressive complementary assignment  z_i | Z, z_{1:i-1}
individual discriminator CONDITIONED on team skill  q_d(z_i | o_i, Z)
```

HA-CTSE currently has none of these live: `g` is empirically decorative,
`use_team_code_discriminator=False`, editing is parallel per-agent (no
complementarity), and the P3 discriminator conditions on the dead `g`. Therefore:

```text
P3-4 individual forcing = NECESSARY BUT NOT SUFFICIENT. It makes skills
  distinguishable; it does not make them cooperate. It is no longer the main line.
The active PRIMARY reconstruction target is the cooperative half above.
```

Critical sequencing nuance: the halves are **not** sequential. HMASD's individual
discriminator is already team-conditioned (`q_d(z_i | o_i, Z)`), so P3 forcing only
becomes HMASD-faithful once `g` is a *live* team context. Reviving `g` is thus a
prerequisite for the individual half, not a later stage. The corrected route:

```text
1. Keep P3 individual forcing, but not as the answer.
2. P3-2e first: confirm z_i induces sustained behavioral MODES, not one-step nudges.
3. Add PASSIVE cooperative diagnostics: g-intervention KL, co-edit redundancy,
   teammate-churn / async confound (log on runs already happening).
4. Rebuild the cooperative half: live g (gate on g-intervention KL), co-edit
   complementarity, team/joint discriminator (generic joint features only).
5. Only then judge whether usefulness coupling + variable lifetime beat
   fixed/shared controls under the SAME forcing.
```

The thesis is therefore: **skills must be complementary under team context, carry
joint semantics, and be composable at the high level** — not merely decodable.
This supersedes earlier "P3-4 low-level forcing is the P3 mainline" framing below;
those P3-4 sections remain valid as the *individual-half* specification.

**Formal split (Round 9 cross-validation of the GPT staged plan):**

```text
P3-individual: z_i -> persistent, controllable, shortcut-resistant behavior process.
P4-cooperative: live g -> complementary joint skill/duration assignment ->
                team/joint process semantics -> sparse-team-reward composition.
```

Three non-negotiable build gates that correct the naive "finish P3, then P4" order:

```text
G1 CAPACITY GATE: the P3-4 forcing matrix is BLOCKED until P3-2e shows z induces
   sustained MODES (between/within trajectory-spread ratio grows with h AND
   persists to h=50), not one-step nudges. If z is a nudge, fix actor conditioning
   (per-layer FiLM / skill-indexed recurrent state / hypernet) FIRST — a
   discriminator cannot force modes the actor cannot express.

G2 g-REVIVAL GATE: g is decorative because nothing in the objective REQUIRES it to
   carry information (if local obs + z_i achieve individual reward, g's advantage
   ~0 and it collapses). Autoregressive co-edit ALONE will NOT revive g. g-revival
   needs an explicit training pressure giving g a job independent of current
   return. Valid paths are:
     (a) a high-level PPO reward from a generic team/joint discriminator,
         e.g. R_team = log q(g | joint_effect) - max(shortcuts), so the
         advantage updates log pi_g / bridge and the associated high-level
         skill-duration-edit decisions;
     (b) a decision-level differentiable usage loss such as
         I(g; joint skill/duration/edit decisions | context);
     (c) both.
   A discriminator trained only by its own supervised CE/NLL loss does NOT revive
   g; it only trains q. Build the g-info / team-reward path WITH (not after) the
   co-edit editor, and run g diagnostics DURING P3. Correct P3 is team-conditioned
   individual forcing q_d(z_i|o_i,g), which already depends on a live g.

G3 FRACTAL-DURATION TRIGGER: the discrete duration<->skill co-selection shortcut
   recurs at the JOINT level (g co-selected with {d_i}). If BOTH the individual and
   joint residual gates are duration-dominated, that is ONE root cause, not two
   bugs -> switch the temporal model to hazard/stopping-time rather than adding
   more debiasing heads at either level.
```

Usefulness gates must use the DEBIASED high-level advantage (raw SMDP advantage
favors long T via γ^T); comm fields never enter default P3/P4 reward. The full
staged plan (Stages A-E, diagnostics-first) and metric definitions live in
`memory/HMASD_HACTSE_research_review_20260701_gpt.md` and the cross_validation Round 9
cross-validation entries.

2026-07-01 g-revival precision update:

Do not write the contract as "joint discriminator gradient directly backprops
into g" without qualification.  HMASD does not revive skills by directly applying
the discriminator CE loss to the sampler.  It trains the discriminator as a
classifier, then uses the discriminator log-probability as intrinsic reward.  The
HA-CTSE analogue must be equally explicit:

```text
CE/NLL(q_team) only trains q_team.
R_team or a usage loss trains the g-generating / g-using path.
```

For a stochastic bridge, a team intrinsic reward can update `log pi_g(g_tau |
c_tau)` through the high-level advantage.  For a deterministic bridge, there is
no policy-gradient log-prob for `g`; reviving `g` then requires a differentiable
auxiliary usage loss or switching the bridge to a stochastic/team-code policy.

Therefore, P1/P2/P2-lite should be read as attempts to restore HMASD's sparse
reward / credit-assignment advantages after the skill-cycle decoupling.  They
are not separate task objectives and they are not a license to optimize
backhaul directly.

The primary reconstruction problem is now sharper:

```text
Find the variable-lifetime analogue of HMASD's discoverer + discriminator +
entropy system: an intrinsic training loop that makes asynchronous skills
emerge, separate, and actually improve sparse-reward cooperation.
```

Backhaul/recovery probes can reveal whether this loop works in Scenario 7, but
the loop itself should be phrased in general MARL terms: process effect,
role/skill separability, controllable temporal behavior, and improved task
return under sparse cooperative rewards.

Current maturity checkpoint:

```text
decoupled agent skill cycles: implemented mechanically, not yet proven better
  than fixed/shared lifetime controls.
HMASD-scale discoverer/executor: structurally implemented with recurrent
  MAPPO-style actor/critic, effect still pending long-run validation.
discriminator-style semantic pressure: the largest missing function; current
  posterior/role/classifier variants are mostly diagnostic or retired.
entropy/exploration pressure: present as coefficients and diagnostics, but not
  yet the full HMASD-style multi-channel exploration loop.
sparse-reward credit densification: P1 and P2-lite are implemented as support
  mechanisms, but still need to prove they bridge sparse reward as effectively
  as HMASD intrinsic rewards.
```

If P2-lite fails to close the S7-S1 gap to HMASD, the next step should not be a
P1/P2 coefficient sweep.  The next algorithmic object should be P3: dense
process-effect semantic pressure (defined below), i.e. a reconstruction of the
HMASD discriminator spirit for asynchronous process segments.

The low-level actor invariant is:

```text
a_t_i ~ pi_l(a_i | o_t_i, z_i)
```

By default, neither OPT compact `c_tau` nor team bridge code `g_tau` may enter
the low-level actor.

For fair comparison against HMASD, the default standalone low-level executor
must match HMASD's MAPPO-style discoverer capacity rather than a smaller MLP
baseline.  The default `ha_ctse_process` path therefore uses:

```text
MLPBase(o_i) -> skill-conditioned FiLM -> RNNLayer -> ACTLayer
```

for the actor, and a centralized recurrent critic:

```text
MLPBase(global_state) -> team-code FiLM -> RNNLayer -> V
```

with per-env GAE(lambda), rollout-end bootstrap, sequence PPO, ValueNorm,
normalized target clipping, and PPO value prediction clipping.  Feedforward or
simplified GRU low-level policies are valid ablations, but they are not the
default baseline for claims about replacing HMASD.

## Inherited From OPT

OPT contributes an interaction representation module:

```text
c_tau = f_OPT(s_tau, joint_obs_tau)
```

OPT decomposes entity interactions into sparse and diverse prototypes, uses
sparsemax for sparse interaction weights, uses contrastive disagreement to
separate prototypes, and uses a prototype aggregator to produce a compact
interaction structure representation.

`c_tau` is not a team option, team skill, or executable controller. It is
interaction context.

## Compact-Team Bridge

HA-CTSE must not replace a controllable team code directly with OPT compact
`c`.
Instead:

```text
c_tau = f_OPT(s_tau, joint_obs_tau)
g_tau = f_bridge(c_tau)
```

or:

```text
g_tau ~ pi_g(g | c_tau)
```

Roles:

```text
c_tau = interaction structure / OPT compact
g_tau = team coordination code / compact-conditioned team latent
z_i   = executable individual skill
a_i   = primitive action
```

The bridge exists because OPT compact is descriptive, while the policy needs a
controllable latent that can shape skill selection and process-level behavior.

R30 correction (2026-07-14): the fixed-clock editor does not sample a team code
as part of its high action. It uses the deterministic expectation of the
existing bridge code embeddings under `softmax(code_logits(c))`. This expected
embedding is representation context only: its R30 log-probability and entropy
are zero. Historical stochastic-bridge modes remain frozen comparators.

## Horizon-Aware Skill Windows

2026-07-14 amendment: the active core uses a fixed global check clock and
all-agent autoregressive editing. Discrete duration selection is retired from
the core. HMASD refreshes all agent skills synchronously every `k0` primitive
steps; HA-CTSE checks every agent at the same `k0` clock but lets each agent
independently keep or edit its active skill.

Each agent keeps:

```text
active_skill z_i
skill_age age_i
optional window_state w_i
```

At every high-level interval `tau`, all agents participate in one stored order.
The effective token set for an active agent is:

```text
E_i(z_prev_i) = {KEEP} union {SET(z): z != z_prev_i}
```

With `K` skills this is `K` effective choices, not `K*D`. Initial assignment
masks `KEEP`; normal checks mask `SET(current_skill)`.

`KEEP` means:

```text
z_i = z_prev_i
age_i continues
```

`SET(z)` means:

```text
z_i = z
age_i = 0
```

After each token, apply it immediately to a working roster. Later agents are
conditioned on earlier applied edits plus the still-active skills of agents not
yet processed. Thus checking is synchronous while realized skill renewal and
lifetime remain asynchronous.

The active core has no forced `H_max`, no duration candidate set, and no
default minimum-age mask beyond the one-block check interval. A minimum-age
mask is allowed only as a later explicit churn-control ablation after evidence
of pathological rapid switching. Any mask must be applied before sampling so
stored and executed PPO log-probabilities match.

The keep and switch-skill probabilities are factorized:

```text
P(KEEP)   = p_keep
P(SET(z)) = (1 - p_keep) * pi_z(z | SWITCH), z != current
```

There is no entropy bonus on `KEEP/SWITCH`. Conditional switch-skill entropy
may preserve skill supply, but for this regularizer its switch-probability
weight and shared feature input must be detached so only the switch-skill branch
receives the entropy gradient. It must not pay the keep path to switch more
often, directly or through the shared trunk.

## Skill Process View

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- After HA-CTSE separates the high-level check interval from individual skill
- renewal, `k` and the actual skill lifetime are different objects:

## Retired Discrete Lifetime Sets

Discrete lifetime selection `(z_i, d_i)` is retired from the active core. It
expanded each agent's effective choice from `K` to `K*D`, trained short
durations more frequently because high samples were completed segments, and
allowed duration to substitute for skill semantics. Frozen discrete-duration
runs remain historical comparators only; do not enlarge, retune, or restore the
duration head or its entropy floor.

Actual lifetime is now the run length of consecutive `KEEP` decisions. The
initial keep bias is derived once from the retired source distribution:

```text
p_keep_init = 1 - 1 / mean(duration_blocks)
```

For the active `{1,2,3,4}`-block source this is `0.6`. It is an initialization,
not a sweep parameter or a lifetime reward.

## On-Policy Update Boundary

HA-CTSE is currently trained with PPO-style on-policy updates. A high-level
decision, low-level action sequence, or process segment may be used for an
update only if it was generated by the policy version that is being updated.

At an update boundary:

- rollout tensors must be cleared after the PPO update;
- an open R30 high row is closed with a valid old-critic bootstrap and
  `policy_truncated=True`;
- active process segments must not be reused as training samples in the next
  policy version;
- R30 preserves active skills, primitive-step ages, per-environment check clock,
  simulator continuity, and low recurrent hidden state. The next rollout uses
  an actor-invalid critic-only continuation row until the next real check; it
  must not create an extra edit opportunity.

This is separate from environment episode continuity. The simulator may keep
running, but the learning data contract must not silently mix policy versions.

## High-Level Log Probability

For each all-agent autoregressive edit sequence:

```text
log pi(e_i) =
    log p_keep_i                                      if KEEP
    log(1 - p_keep_i) + log pi_z(z_i | SWITCH, prefix) if SET(z_i)
```

The R30 sequence log-probability is the sum of the token log-probabilities; its
deterministic expected bridge contributes no action log-probability.
The stored teacher-forcing prefix is the applied working roster, not merely a
count of prior tokens.

High PPO is owned by fixed check transitions, not variable process segments:

```text
R_tau^H = sum_{r=0}^{L_tau-1} gamma^r r_env[tau*k0+r]
Gamma_tau = gamma^L_tau
```

Normally `L_tau=k0`; an episode-terminal block may be shorter. Compute GAE on
each environment's check sequence. One check advantage is shared across its
agent tokens, and the token dimension is averaged so gradient scale does not
grow with agent count. This is MAT-style autoregressive PPO, not a claim of the
full MAT monotonic-improvement theorem.

The R30 high critic emits one scalar from the pre-action centralized context
and normalized per-environment countdown. It is independent of token prefix,
executed edits, sampled team codes, and process segments. A `SET(z)` token uses
one combined log-probability and one clipped ratio; keep and skill factors are
not clipped separately. At an update truncation the critic bootstraps, but the
GAE trace is broken before the next policy version. Critic loss must not update
the compact/bridge actor representation path.

Hard skill replacement is not differentiable:

```text
z_i = keep(z_prev_i) or replace(z_tilde_i)
```

The learning path is PPO:

```text
reward / advantage
  -> log_prob(pi_term)
  -> log_prob(pi_z)
  -> log_prob(pi_g), if stochastic
  -> high-level parameters
```

Do not expect gradients through the hard mask itself.

## High-Level Reward

The active R30 high-level interval reward is only the discounted environment
reward over the fixed check block:

```text
R_high = sum_env_reward_over_check_block
```

No edit penalty, switch penalty, positive lifetime reward, or semantic
intrinsic reward enters the active `KEEP/SET` return. Such terms would hard-code
persistence or let long skills earn more merely by surviving. A later accepted
fixed-window semantic target may enter low-level GAE only.

## Process-Centric Exploration

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The original discriminator assumption was:
- if q_d can infer z_i from state/observation, then z_i has behavioral meaning

## Residual Process Posterior

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The current process-level replacement for HMASD's discriminator is a segment
- posterior with explicit shortcut controls:

## Future Cooperation Outcome Residual

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The context-residual classifier probe showed an important negative result:
- after controlling for context, duration, phase, agent id, reward sum, and the

## Role Of The Discoverer

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- In original HMASD, the low-level discoverer is mainly trained to execute
- individual skills while discriminator rewards make those skills identifiable.

## Legacy Discriminator Reward

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- This section describes the old HMASD-compatible objective for reference. It is
- not enabled as-is in the standalone `ha_ctse_process` trainer.

## Implementation Invariants

1. Keep HA-CTSE process-core outside the `hmasd` package. It may reuse
   environment/config/logging infrastructure, but its trainer, agent, buffers,
   losses, process objectives, and checkpoints must live in a separate
   algorithm directory.
2. Preserve original HMASD behavior under `hmasd` and `hmasd_original`.
3. Do not silently change low-level actor inputs.
4. Do not let `c_tau` or `g_tau` bypass the skill bottleneck except under an
   explicit ablation flag.
5. Do not treat OPT compact as a team skill.
6. Treat `g_tau` as the compact-conditioned team coordination code.
7. Mask edit before sampling for `H_min`.
8. Store log-probabilities for executed high-level decisions.
9. Train hard masks and discrete skills through PPO log-probabilities.
10. Track whether the method collapses to full-sync skill assignment.
11. Treat process/outcome objectives as first-class exploration mechanisms.
12. Do not enable old single-step HMASD discriminator training or rewards in the
    process-core algorithm unchanged.  If discriminator-like modules are used,
    implement them as explicit process-level semantic/cooperation-credit
    ablations with shortcut diagnostics.
13. Do not treat single-step discriminator accuracy as sufficient evidence that
    skills have meaningful process semantics.
14. When variable skill lifetimes are modeled, use masks/sequence encoders and
    track duration-only shortcut baselines.
15. Compare against HMASD under an explicit network-scale profile.  If hidden
    size, skill cardinality, recurrent state size, PPO epochs, or critic
    capacity differ, label the run as a capacity ablation rather than an
    algorithmic comparison.

## Baselines And Ablations

Stable external baselines:

- `hmasd_original`
- `opt_mappo_k`

Historical/first-pass HA-CTSE names:

- `opt_full_sync_skill`
- `ctb_sse_no_horizon`
- `horizon_ctb_sse_core`
- `horizon_ctb_sse_no_discriminator`
- `horizon_ctb_sse_compact_low_level_ablation`
- `deterministic_bridge`
- `stochastic_bridge`
- `parallel_editor`
- `autoregressive_editor`

These names do not imply that every old mechanism remains scientifically
meaningful under the process-centric algorithm. Ablations are not a museum of
all past structures. Keep an ablation only if it answers a coherent question
about the current algorithm.

Ablation selection rule:

```text
keep an ablation if removing/replacing the component tests a live hypothesis
of the current process-centric framework;
retire or downgrade it to legacy diagnostic if the component no longer has a
well-defined role in the new framework.
```

Examples:

- `hmasd_original` remains a stable external baseline.
- `deterministic_bridge` remains useful only if stochastic team-code learning
  is still a live hypothesis.
- `horizon_ctb_sse_no_discriminator` is no longer a meaningful core ablation
  once the standalone process-core trainer excludes discriminators by design.
  Better process-era ablations are `process_no_reward`, `process_no_contrast`,
  or `process_no_outcome`.
- `ctb_sse_no_horizon` may become obsolete if discrete/process lifetimes
  replace learned keep/edit as the core temporal mechanism.
- `opt_full_sync_skill` remains useful only as a collapse/control reference,
  not as a serious alternative to process lifetimes.

The allowed scientific claim is:

```text
The method introduces an inductive bias for tasks with heterogeneous temporal
coordination structure, where global information synchronization should be
separated from individual skill renewal, and where skill latents should induce
distinguishable behavior processes over their realized lifetimes.
```

Do not claim universal dominance over OPT-MAPPO-K.

## Failure Modes

- OPT compact is uninformative.
- Bridge code collapses to one team code.
- Termination policy always edits.
- Termination policy never edits.
- Full-sync rate stays near one.
- Skill lifetimes are homogeneous.
- Legacy discriminator rewards dominate task reward if accidentally re-enabled.
- Low-level actor ablation is the only variant that works.
- Candidate skills leak into labels when no edit executes.
- PPO old log-probabilities do not match executed masks.
- Process objectives collapse to task-irrelevant diversity.
- Outcome objectives become too task-specific to generalize.
- Segment encoders identify skills only from duration or scheduling artifacts.
- Delayed process rewards add variance faster than they add useful exploration.

## Topology Counterfactual Role Semantics

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The negative context-residual and future-outcome residual probes showed that
- raw skill classifiability and learned future outcome prediction are not yet

## Cooperative Topology-Potential Credit Shaping

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The Round-5 implementation gate changed the active HA-CTSE question from
- "can a skill be recovered from its segment?" to:

## Topology-Role Coordination Code

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- If P1 topology potential improves service opportunistically but does not raise
- `credit_recovery_rate`, HA-CTSE should not return to generic

## Intrinsic Reward As Topology Contribution Residual

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- The HA-CTSE replacement for HMASD discriminator/discoverer intrinsic pressure
- should be written explicitly as cooperative contribution credit:

## P2-lite: Recovery-Window Contribution Credit

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- This section supersedes the monolithic three-part P2 above as the active design.
- The `Topology-Role Coordination Code` and `Intrinsic Reward As Topology

## P3: Conditional Skill-Effect Discovery

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/ALGORITHM_PRINCIPLES.md`._
- P3 is the variable-lifetime version of HMASD's closed intrinsic loop:
- skill is sampled


---

# Research Causal Discipline

_Moved verbatim from `AGENTS.md` on 2026-07-13. This is the research contract:
it belongs with the principles, not in the always-injected instruction file.
`AGENTS.md` now points here._

## Falsifiable Causal Edges

HA-CTSE research advances through falsifiable causal edges, not by accumulating
round numbers, classifiers, modules, reward terms, or unreviewed experiments.

```text
individual skill z_i -> persistent executable behavior
distinct z_i -> behaviorally differentiated skills
team intent g/Z -> complementary joint assignment
joint assignment -> complementary joint behavior/effect
joint behavior/effect -> recoverable q_d/q_D residual
intrinsic reward -> improved policy without collapse or shortcut dominance
policy -> sparse-reward task improvement and HMASD parity
```

Do not promote a downstream edge while a required upstream edge is failed,
invalid, mixed, or underpowered. Classifier accuracy, a positive residual, or
high latent entropy does not by itself prove behavioral control, cooperation,
credit assignment, reward usefulness, or task improvement.

### Causal-Claim Record

Before launching a meaningful experiment, register in the accepted plan and
`memory/ExpRecord.md`:

- the exact causal edge and hypothesis;
- upstream evidence that authorizes testing it;
- baseline level and exact comparator;
- metrics, thresholds, nulls, seeds, timesteps, and optimizer-update exposure;
- PASS, FAIL, MIXED, UNDERPOWERED, INVALID, and crash branches;
- the only next action authorized by each branch;
- changes prohibited while the gate remains open.

Experiments are evidence for claims, not disposable module trials. Preserve
negative results as constraints. Do not silently rename, delete, reinterpret,
or rerun a failed line until it looks favorable.

### Four-Level Baseline Hierarchy

Use the lowest level that directly answers the question.

1. **Diagnostic null.** Use context/prior-only, pre-window, shuffled,
   fake-label or fake-marginal, agent-matched, duration-matched,
   agent-duration-matched, and action/effect ablations as applicable. Match
   held-out split, capacity, optimizer, stopping rule, and device. This proves
   incremental signal only.
2. **Mechanism-matched HA-CTSE control.** Match surrounding architecture,
   capacity, parameter/update budget, training contract, commit, environment
   count, rollout length, optimizer updates, seed, and evaluation protocol.
   Change only the intended causal intervention. Added capacity requires a
   capacity-matched inactive, sham, or ablated pathway.
3. **Async temporal control.** Compare asynchronous per-agent variable
   lifetimes with full-sync/fixed and shared-fixed controls under identical
   mechanisms, rewards, network, environments, updates, seeds, and evaluation.
   Run this only after the skill mechanism works.
4. **HMASD parity reference.** Compare complete algorithms only after matching
   scenario, agent count, network/parameter budget, environment count or
   optimizer-update exposure, action mode, episode count, metrics, seeds, and
   training budget as closely as practical.

Historical runs are references, not exact causal controls after architecture or
training contracts change. Equal environment steps do not imply equal
optimization exposure. Always report environment steps and optimizer-update
count. Label comparisons that change seed, environment count, updates, network
size, evaluation, or multiple algorithm flags as `reference-only` or
`confounded`.

### Experiment Promotion Ladder

Advance new latent, discriminator, assignment, reward, or credit mechanisms in
this order:

```text
0. wiring and synthetic positive/negative controls
1. reward-off held-out observational signal against diagnostic nulls
2. reward-off causal intervention with persistent behavior/effect separation
3. small clipped reward against a mechanism-matched HA-CTSE control
4. long-run verification at the declared horizon with paired seeds
5. async temporal ablation for a decoupled-lifetime claim
6. matched HMASD parity for the complete algorithm
```

Failure at one level blocks later levels. Instrument repair may repeat the same
gate only when the result is explicitly `INVALID` or `UNDERPOWERED` and the
scientific thresholds remain unchanged. Do not redesign metrics after viewing
results.

### Failure Review Gate

After `FAIL`, `MIXED`, `UNDERPOWERED`, or `INVALID`, complete a review before a
new core algorithm change or reward experiment. Separate:

- verified mechanism evidence;
- instrumentation and data-quality failures;
- optimization or capacity failures;
- confounded or incomparable task evidence;
- reusable negative conclusions;
- unresolved hypotheses and the single next causal edge.

If two related gates fail or the proposed action changes research direction,
produce a cross-round failure matrix and baseline matrix from existing
artifacts before new implementation.

Blind exploration is prohibited. A new module, reward, target, sweep, or large
run must name the failed causal edge it addresses, explain why prior evidence
supports the repair, identify its exact comparator, and state what evidence
would cause abandonment or revision.
