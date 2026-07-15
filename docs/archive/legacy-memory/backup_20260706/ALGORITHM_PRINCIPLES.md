# HA-CTSE Algorithm Principles

This document is the implementation contract for Horizon-Aware Compact-Team
Skill Editing / process-core exploration, abbreviated HA-CTSE. It intentionally
separates HMASD-inspired controllable skills from OPT-style interaction
representation and from a direct copy of the old HMASD discriminator training
target.

## Active R22 Contract: Two-Clock R21/v6 Mainline

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
D. HA-CTSE per-agent discrete lifetime, reward-pure
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
duration_usage_entropy not collapsed
duration_agent_mi / agent-wise lifetime distribution nontrivial
renewal_pairwise_corr_mean not full-sync
duration_return_range has signal
duration_full_disconnect_range / duration_recovery_range has explanatory value
skill_duration_mi not dominated by duration-only shortcut semantics
```

If reward improves but the policy uses one duration for all agents, renews all
agents together, or merely learns a new fixed-k schedule, the decoupled-K
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

## Horizon-Aware Skill Windows

HMASD refreshes all agent skills synchronously every `k` primitive steps.
HA-CTSE keeps the global synchronization interval but lets each agent decide
whether to keep or edit its active skill at each high-level interval.

Each agent keeps:

```text
active_skill z_i
skill_age age_i
optional window_state w_i
```

At high-level interval `tau`:

```text
m_i ~ pi_term(m | c_tau, g_tau, o_i, z_prev_i, age_i)
```

`m_i = 0` means keep the current skill:

```text
z_i = z_prev_i
age_i = age_i + 1
```

`m_i = 1` means edit:

```text
z_tilde_i ~ pi_z(z | c_tau, g_tau, o_i, z_prev_i, age_i)
z_i = z_tilde_i
age_i = 0
```

The bounded window constraints are:

```text
if age_i < H_min: mask edit before sampling
if age_i >= H_max: force or strongly bias termination
```

Masking must happen before sampling so PPO log-probabilities match executed
actions.

## Skill Process View

After HA-CTSE separates the high-level check interval from individual skill
renewal, `k` and the actual skill lifetime are different objects:

```text
k   = shared high-level check / information synchronization clock
T_i = realized lifetime of agent i's active skill z_i
```

`T_i` is produced by the keep/edit process:

```text
z_i starts at tau_start
z_i remains active while pi_term chooses keep
z_i terminates when edit executes, the episode ends, or a forced boundary closes
```

Thus a skill is not merely a label at one step. It is a variable-duration
process segment:

```text
process_i(z_i) =
    (o_i[t:t+T_i],
     a_i[t:t+T_i],
     delta_o_i[t:t+T_i],
     optional task outcomes,
     mask_i[t:t+T_i])
```

The implementation may start with fixed-`k` segments for stability, but the
research target is variable-lifetime process segments closed by actual skill
termination. Variable durations must be handled through sequence encoders and
masks, not by forcing every skill process into a fake fixed-length meaning.

## Discrete Lifetime Sets

A useful simplification is to let the high-level policy choose skill lifetimes
from a discrete set:

```text
D = {d_1, d_2, ..., d_M}
T_i = d_i * k
```

where `d_i` is measured in high-level check intervals, not necessarily primitive
steps. On initial assignment or executed edit, the high-level policy samples:

```text
d_i ~ pi_duration(d | c_tau, g_tau, o_i, z_i, age_i)
```

The skill then persists until its countdown expires, unless an explicit
early-termination ablation is enabled.

This can simplify training because:

- termination credit assignment becomes a discrete duration-choice problem;
- segment lengths come from a small known set, which simplifies process buffer
  batching and masking;
- high-frequency keep/edit noise is reduced;
- process rewards can be assigned to completed duration buckets more reliably.

This is not free. Duration can become a shortcut for skill identity. Any
discrete-duration implementation must track:

```text
duration_only_accuracy
skill_usage_by_duration
return_by_duration
early_expiry_or_forced_renewal_rate
```

The duration set is therefore a research hypothesis, not a hard requirement.
It may become the preferred core if it stabilizes process learning; otherwise it
should remain an ablation against learned termination.

## On-Policy Update Boundary

HA-CTSE is currently trained with PPO-style on-policy updates. A high-level
decision, low-level action sequence, or process segment may be used for an
update only if it was generated by the policy version that is being updated.

At an update boundary:

- rollout tensors must be cleared after the PPO update;
- pending high-level samples that cannot be closed within the current rollout
  must be dropped or explicitly closed with a valid bootstrap value;
- active process segments must not be reused as training samples in the next
  policy version;
- active high-level skills and recurrent hidden state should be invalidated for
  process/duration-aware HA-CTSE so the next rollout starts from fresh decisions
  sampled by the updated policy.

This is separate from environment episode continuity. The simulator may keep
running, but the learning data contract must not silently mix policy versions.

## High-Level Log Probability

For stochastic bridge:

```text
log_pi_high =
    log pi_g(g_tau | c_tau)
  + sum_i log pi_term(m_i | x_i)
  + sum_{i: m_i = 1} log pi_z(z_tilde_i | x_i)
```

where:

```text
x_i = (c_tau, g_tau, o_i, z_prev_i, age_i)
```

For deterministic bridge, the first term is zero and has no policy-gradient
path.

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

The high-level interval reward is:

```text
R_high =
    sum_env_reward_over_interval
  - alpha * num_executed_edits
  - beta * num_skill_switches
  - eta * sum_i executed_edit_i / (age_i + 1)^p
```

Forced initial skill assignment must not receive edit or switch penalty.

## Process-Centric Exploration

The original discriminator assumption was:

```text
if q_d can infer z_i from state/observation, then z_i has behavioral meaning
```

For HA-CTSE this is too weak. Because `c_tau`, `g_tau`, `z_i`, and `T_i` define
a temporal process, the preferred exploration question is:

```text
does this latent induce a useful, distinguishable, persistent behavior process?
```

The core exploration signal should therefore be process/outcome based. A
general low-level reward target is:

```text
r_i =
    lambda_e * r_env
  + lambda_P * R_process(segment_i, z_i, c_tau, g_tau)
  + optional lambda_MI * R_mi
```

where `R_mi` is a legacy discriminator term. It is excluded from the standalone
process-core algorithm because it mixes a supervised identifiability target into
the process/outcome objective.

Preferred process objectives:

1. Outcome-based skill discovery. A skill should produce predictable and
   meaningfully different future outcome deltas:

   ```text
   y_i = outcome(segment_i)
   y_i may include delta_coverage, delta_qos, delta_energy,
   charger_progress, relay_margin_delta, or other task-relevant deltas.
   ```

2. Contrastive segment alignment. A segment encoder should align the behavior
   process with the executed skill:

   ```text
   h_i = f_segment(segment_i)
   score_i = sim(h_i, e_z[z_i])
   ```

   Positive pairs are executed `(segment_i, z_i)` pairs. Negatives may come
   from other skills, agents, time windows, or environments.

3. Termination-aware exploration. Editing should be learned as a continuation
   decision:

   ```text
   edit if expected advantage(change skill) > expected advantage(continue)
   ```

   Switch/edit costs are anti-churn regularizers. They must not be interpreted
   as saying that switching is inherently good or bad.

The old supervised single-step discriminator terms are not the process-core
target.  However, discriminator-like estimators are valid if they are redesigned
as process-level semantic separation or cooperation-credit probes.  Mixing the
old target into the new core without this reinterpretation confounds the
training target and makes it unclear whether the new algorithm is working.

## Residual Process Posterior

The current process-level replacement for HMASD's discriminator is a segment
posterior with explicit shortcut controls:

```text
q_full(z_i | segment_i, g_tau)
q_duration(z_i | duration_i)
q_length(z_i | length_i)
q_reward(z_i | reward_sum_i)
```

The semantic reward estimate is not plain classifier confidence.  It is the
posterior advantage over the best non-behavior shortcut:

```text
R_residual =
    log q_full(z_i | segment_i, g_tau)
  - max(log p(z_i | g_tau),
        log q_duration(z_i | duration_i),
        log q_length(z_i | length_i),
        log q_reward(z_i | reward_sum_i))
```

This is the process-core interpretation of discriminator pressure:

- `q_full` asks whether the realized behavior process identifies the executed
  skill;
- shortcut heads expose whether the classifier is only reading scheduling,
  segment length, or aggregate return artifacts;
- `posterior_acc_minus_shortcut_max` is the first diagnostic gate before
  trusting process semantic reward;
- negative residual MI is allowed and should be logged, because it means the
  behavior process is less informative than the shortcuts.

Recommended first reward-injection experiment:

```text
process_reward_mode = residual_mi
process_reward_injection = low_only
process_reward_coef = 0.05
process_shortcut_coef = 0.5
```

Rationale: HMASD's discriminator primarily pressured the discoverer/low-level
skill realization.  Injecting the residual term into the low-level reward tests
that role first while keeping high-level task credit dominated by environment
return.  `high_and_low` and larger coefficients are later ablations, not the
initial default.

## Future Cooperation Outcome Residual

The context-residual classifier probe showed an important negative result:
after controlling for context, duration, phase, agent id, reward sum, and the
team-code prior, segment/transition skill classifiers can fail to provide
positive residual semantics.  This means raw skill classifiability is not a
sufficient intrinsic reward target for the UAV cooperation task.

The next process-core principle is:

```text
Skill meaning should be defined by residual predictive contribution to future
team cooperation outcomes.
```

The diagnostic objective is:

```text
Full:
  y_future <- h_segment, z_i, g_tau, context shortcut features

Baseline:
  y_future <- o_start, g_tau, agent_id, phase, duration, reward_sum

Residual gain:
  || y_future - y_base ||^2 - || y_future - y_full ||^2
```

The first future outcome vector should be physically interpretable rather than
learned from a black-box reward:

```text
coverage_delta_h
qos_delta_h
full_disconnect_improvement_h
relay_margin_delta_h
connected_components_improvement_h
teammate_service_gain_h
bottleneck_link_gain_h
```

Stage order:

1. Train full and baseline predictors only; inject no reward.
2. If residual gain is positive and topology-relevant field gains are positive,
   inject a small low-level residual reward.
3. Only after low-level shaping improves future cooperation diagnostics,
   consider high-level gated outcome residual reward.

Do not raise classifier residual coefficients, force the high intrinsic gate
open, or add more shortcut classifier heads when residual classifier MI is
negative.  That would optimize an invalidated signal rather than solving the
cooperative credit problem.

## Role Of The Discoverer

In original HMASD, the low-level discoverer is mainly trained to execute
individual skills while discriminator rewards make those skills identifiable.
Under the HA-CTSE process view, this role must be broadened.

The discoverer is the module that realizes:

```text
z_i -> behavior process over T_i
```

It should therefore be evaluated by whether `pi_l(a_i | o_i, z_i)` can turn an
executed skill into a temporally coherent and task-relevant process, not only by
whether a discriminator can classify the resulting next observation.

Core responsibilities:

1. Preserve the skill bottleneck:

   ```text
   a_i ~ pi_l(a_i | o_i, z_i)
   ```

   In the core algorithm, `c_tau`, `g_tau`, and process outcomes must not be fed
   directly into the low-level actor. Direct compact/team conditioning belongs
   only in explicit ablations.

2. Learn from process-level or semantic reward. The discoverer should receive
   task reward plus carefully validated exploration pressure redistributed over
   the segment or assigned at termination.  Old HMASD MI reward should not be
   copied blindly, but its role as semantic pressure should be replaced by a
   process-level posterior, classifier, or contribution diagnostic that beats
   duration/length shortcuts.

3. Maintain action exploration. Low-level action entropy remains important, but
   its target should be judged against process diversity and task progress, not
   only instantaneous action randomness.

4. Support persistence. If `z_i` is kept across several high-level checks, the
   discoverer should make the behavior process remain coherent instead of
   drifting into unrelated actions before termination.

5. Avoid bypassing high-level semantics. If an ablation allows the low-level
   actor to observe compact context directly, improvements from that ablation
   cannot be claimed as evidence that HA-CTSE's skill process mechanism works.

This means discoverer training is not a fixed inherited block. Its recurrent
capacity, reward decomposition, entropy target, critic conditioning, semantic
pressure, and diagnostics should be reviewed whenever the process objective
changes.

## Legacy Discriminator Reward

This section describes the old HMASD-compatible objective for reference. It is
not enabled as-is in the standalone `ha_ctse_process` trainer.

The legacy discriminator reward design is:

```text
r_i =
    lambda_e * r_env
  + lambda_G * log q_G(g_tau | s_next or c_next)
  + lambda_d * log q_d(z_i | o_next_i, c_tau, g_tau)
```

If used, it should be prior-corrected or normalized so a uniform classifier does
not create a systematic negative exploration reward:

```text
R_mi = log q(label | input) - log p(label)
```

The individual discriminator label must be the active executed skill `z_i`, not
a candidate skill sampled during no-edit.

If a segment discriminator is added, it should be interpreted as one possible
process encoder/classifier and semantic-pressure mechanism, not as the only
valid process objective:

```text
q_d(z_i | segment_i, c_tau, g_tau)
```

Avoid duration-only shortcuts. If a discriminator or process encoder can infer
skill identity from `T_i` alone, it may be learning a scheduling artifact rather
than behavior semantics. Track a duration-only baseline when variable-lifetime
segments are introduced.

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

The negative context-residual and future-outcome residual probes showed that
raw skill classifiability and learned future outcome prediction are not yet
strong enough bootstrap signals for cooperative relay behavior.

The next HMASD-inspired replacement is not a raw skill discriminator.  It is a
topology-conditioned role discriminator:

```text
role_i <- topology counterfactual contribution of UAV i

q_full(role_i | segment_i, topology_cf_i, z_i, g_tau, OPT_context)
q_shortcut(role_i | o_start_i, OPT_context, g_tau, agent_id, phase, duration, reward_sum)

R_role_residual =
    log q_full(role_i)
  - log q_shortcut(role_i)
```

Role pseudo labels are generated from graph-removal marginal contributions,
for example:

```text
cf_backhaul_i = connected_uavs(G_t) - connected_uavs(G_t^{-i})
cf_components_i = components(G_t^{-i}) - components(G_t)
cf_disconnect_i = full_disconnect(G_t^{-i}) - full_disconnect(G_t)
service_i = users directly served by UAV i
```

The first implementation uses four coarse roles:

```text
idle
relay
service
relay_service
```

This module is allowed to use OPT compact context, but only as a conditioning
variable.  OPT context alone must also be part of the shortcut baseline.
Otherwise the role probe can collapse into a context classifier and falsely
claim that skills have learned cooperative roles.

Default status:

- train the role full/shortcut heads as diagnostics;
- inject no reward by default;
- consider low-level reward only if `topology_role_resid_gain_mean > 0` and
  full role accuracy beats the OPT/context shortcut over a sustained run.

This is the current process-core interpretation of HMASD's useful
discriminator spirit: create dense semantic pressure for cooperative roles, but
derive semantics from topology contribution rather than from raw skill labels.

## Cooperative Topology-Potential Credit Shaping

The Round-5 implementation gate changed the active HA-CTSE question from
"can a skill be recovered from its segment?" to:

```text
does the latent/process policy receive enough credit to form and recover
cooperative relay topology?
```

This is now the active P1 direction.  The empirical P0 result is that four
controls moved temporal/access knobs without moving relay recovery:

- long learned duration;
- short learned duration `(1, 2, 3)`;
- fixed duration `(7,)`;
- low-level access to the current `g` code.

Across these controls, `credit_full_disconnect_mean` stayed high and
`credit_recovery_rate` stayed near zero.  Therefore the current binding failure
is cooperative topology credit, not simply duration frequency, low-level access
to `g`, or raw process posterior semantics.

The P1 mechanism is topology-potential shaping:

```text
Phi(s) = bounded topology/service potential from reward_info
F = discount * Phi(s_end) - Phi(s_start)
```

The first implementation uses a global potential, because the per-agent
graph-removal counterfactual fields are available only when the topology-role
probe is explicitly enabled.  The global potential is computed from populated
credit/service fields such as:

```text
credit_delta_uavs_with_backhaul
credit_delta_backhaul_served_users
credit_bh_frac
credit_bh_thr
coverage / qos / throughput
full_disconnect / outage / relay-loss penalties
```

This signal is not the legacy HMASD discriminator reward.  It is an
HMASD-inspired replacement for dense cooperative credit: instead of rewarding
skill-label identifiability, it rewards changes in the cooperative topology that
make service possible.

Important constraints:

1. `delta` mode and segment-level injection are potential-inspired credit
   shaping, not a theorem-guaranteed policy-invariant PBRS transformation.
   Strict `smdp` mode remains an ablation.
2. P1 should be built on short or fixed-short duration bases, not on the old
   long learned set, because P0 showed long learned duration drifts into a
   harmful over-commitment regime.
3. `low_only` signed topology-potential reward is risky.  The complete 640k
   P1 cloud sweep confirms it is the weakest topology-potential arm: signed
   segment-level topology deltas are a poor low-level execution target.
4. `high_only` topology potential has real early signal, but it is unstable:
   it can improve early service/backhaul metrics without directly polluting
   primitive action learning, then regress by 640k.
5. `high_and_low` and `low_only + positive_only` are useful diagnostics.  In the
   complete 640k P1 sweep, `low_only + positive_only` gives the best 640k service
   metrics (`reward ~= 43.4`, `coverage ~= 0.252`, `qos ~= 0.152`,
   `backhaul_connected_frac ~= 0.370`) and `high_and_low` improves throughput,
   but neither solves recovery.

The P1 hard gate is:

```text
credit_full_disconnect_mean down
credit_recovery_rate up
credit_bh_frac up
credit_bh_thr up
reward_std / reward_mean down
```

Coverage, QoS, and throughput are important, but they are not sufficient by
themselves.  A run can improve service in connected episodes while still failing
to learn relay recovery.  The method should be judged by whether it makes
backhaul formation and recovery more reliable, not only by whether lucky
episodes score higher.

Objective-boundary guard: P1 is a diagnostic and auxiliary shaping mechanism for
the general cooperative-credit problem.  Backhaul/recovery movement alone is not
a valid success condition.  A P1 variant is useful only if it improves task
metrics and stability expected of a general MARL algorithm while preserving the
asynchronous skill-lifetime claim.

If stronger topology potential improves coverage/backhaul but leaves
`credit_recovery_rate` near zero, the next algorithmic object should be an
explicit topology/relay-role coordination mechanism, not another generic
segment posterior.  In that case, `g_tau` should be reconsidered as a trained
coordination variable whose target is topology recovery or role assignment,
rather than a decorative latent sampled from OPT context.

P1 cloud conclusion (2026-06-29, complete 32-env S7-S1 640k sweep): P1 does not
pass the recovery hard gate.  `credit_recovery_rate` stays in the same near-zero
band across all arms (roughly `0.0038` to `0.0060` last-10 update mean), while
service metrics can move substantially.  Therefore P1 should be treated as an
opportunistic service/backhaul shaping baseline, not the recovery-credit
solution.  Use `topopot_low_pos_coef1` as the strongest P1 service baseline, keep
`topopot_high_coef1` and `topopot_highlow_coef05` as secondary references, and
retire signed `topopot_low_coef1` from the mainline.

## Topology-Role Coordination Code

> STATUS: superseded as the active P2 by `P2-lite: Recovery-Window Contribution
> Credit` (below). Retained as the deferred P2b (`g` coordination) design and as
> an optional diagnostic. The role-classifier reward is retired from the active
> gate.

If P1 topology potential improves service opportunistically but does not raise
`credit_recovery_rate`, HA-CTSE should not return to generic
`q(z | segment)` posterior rewards.  The next live hypothesis is:

```text
g_tau -> desired topology-role allocation / recovery mode
z_i   -> executable role-conditioned behavior process
```

This keeps the core skill bottleneck intact.  In the default algorithm,
`g_tau` should affect high-level assignment, duration choice, and edit/renewal
decisions, but the primitive actor should still satisfy:

```text
a_i ~ pi_l(a_i | o_i, z_i)
```

Directly feeding `g_tau` to the low-level actor remains an ablation, not the
core mechanism.  A successful low-level-`g` ablation would prove an information
bypass can help; it would not prove that HA-CTSE's skill-process mechanism
works.

The first topology-role coordination targets should be the coarse roles already
defined by graph-removal counterfactuals:

```text
idle
relay
service
relay_service
```

The role target should be derived from topology contribution, not from skill id.
Valid supervision sources include:

```text
connected_uavs(G) - connected_uavs(G^{-i})
components(G^{-i}) - components(G)
full_disconnect(G^{-i}) - full_disconnect(G)
direct_service_i
backhaul_path_margin_i
bottleneck_link_gain_i
teammate_service_gain_due_to_i
```

The scientific claim should remain residual.  A role probe is meaningful only
if the full segment/topology-conditioned head beats the shortcut head that sees
OPT/context, agent id, phase, duration, and reward summary.  Otherwise the role
code is probably classifying context, not learning cooperative process
semantics.

## Intrinsic Reward As Topology Contribution Residual

> STATUS: superseded as the active P2 by `P2-lite: Recovery-Window Contribution
> Credit` (below). The `R_role_residual` classifier term is retired from the
> active gate (diagnostic-only). The `F_topology_high` / `R_recovery_event` ideas
> are carried forward and refined in P2-lite (soft signed potential, not a
> positive-only window-gated reward over still-sparse global deltas).

The HA-CTSE replacement for HMASD discriminator/discoverer intrinsic pressure
should be written explicitly as cooperative contribution credit:

```text
R_intr_i =
    lambda_phi  * F_topology_high
  + lambda_role * stopgrad_positive(R_role_residual_i)
  + lambda_rec  * R_recovery_event_i
```

where:

```text
F_topology_high = discount * Phi(s_end) - Phi(s_start)
R_role_residual_i = log q_full(role_i | segment_i, topology_i, z_i, g_tau)
                  - log q_shortcut(role_i | context, agent_id, phase, duration, reward_sum)
```

`F_topology_high` should first be injected at the high level.  Low-level
injection is live only as a controlled ablation, preferably positive-only or
otherwise clipped to avoid making signed segment deltas a noisy primitive-action
target.

`R_role_residual_i` must remain off until the role full/shortcut probe is
sustainably positive.  It is a semantic/cooperation-credit residual, not a raw
skill discriminator.

`R_recovery_event_i` should activate only around disconnect/recovery windows.
It should not reward the fact that the whole team recovered; it should reward
the marginal process contribution of agent `i` to making recovery possible.
Candidate terms include:

```text
Delta connected_components_without_i
Delta backhaul_path_margin_i
Delta bottleneck_link_gain_i
Delta teammate_service_gain_due_to_i
```

This is the key difference from asking "can `z_i` be decoded from the segment?".
The active HA-CTSE question is:

```text
Does choosing, keeping, or editing z_i under g_tau make a recoverable
difference to relay topology, backhaul connectivity, and cooperative role
allocation?
```

## P2-lite: Recovery-Window Contribution Credit

> STATUS 2026-06-29: IMPLEMENTED (default OFF). Module
> `ha_ctse_process/recovery_potential.py` (soft per-agent `phi_i`, `W_recovery`,
> signed segment shaping, CF-audit diagnostics) with smoke test
> `test_recovery_potential.py` (4 tests pass, including the load-bearing
> "phi rises during disconnect approach" property). Wired into
> `standalone_agent.py` mirroring the P1 `topology_potential` path; config flags
> in `config.py` (`p2_*`, all OFF); CLI flags in `train.py`
> (`--enable_p2_recovery_compute`, `--enable_p2_recovery_reward`,
> `--p2_recovery_reward_level/coef/clip`); staged runner
> `scripts/run_p2_recovery_experiments.{sh,ps1}`. First run must be
> `p2_recovery_precheck` (compute-on / reward-off) to validate Pre-check 2.
>
> STATUS 2026-06-29 (UPDATE, Codex-cross-checked): three Pre-check-2-blocking bugs
> fixed before any reward run. (1) P2 metrics were computed but silently dropped by
> the CSV writer — all `empty_p2_metrics()` keys added to `plotting.UPDATE_FIELDS`,
> plus a `P2/*` TensorBoard group and console fields in `train.py`. (2)
> `recovery_flags` was never passed to `aggregate_p2_metrics`, so
> `p2_corr_phi_recovery_event` was structurally always 0 — flags (started
> disconnected -> ended reconnected) are now built in `standalone_agent.py` and
> passed. (3) segment start used the post-first-step `state_info` — the true
> pre-step state is now captured as `Segment.start_state_info` and consumed in
> `compute_segment_shaping`. The gate is now ENFORCED, not advisory:
> `scripts/p2_gate_check.py` reads the precheck `train_updates.csv` (tail-half mean)
> and the runners abort before h0/h1/l1 unless Pre-check 2 is positive
> (`--skip-gate` / `-SkipGate` overrides).

This section supersedes the monolithic three-part P2 above as the active design.
The `Topology-Role Coordination Code` and `Intrinsic Reward As Topology
Contribution Residual` sections remain valid as *diagnostics and future options*,
but the active P2 mechanism is the lightweight credit defined here.

P2 is no longer a cooperative-role discriminator. The active mechanism is:

```text
Within recovery-relevant windows, distribute global topology progress to the
agents most likely responsible for recovering / maintaining the relay chain,
using a SOFT connectivity potential that changes BEFORE formal reconnection.
```

Motivation. Across P0 (long/short/fixed duration, low-level `g` access),
`credit_full_disconnect_mean` stayed ~0.55 and `credit_recovery_rate` stayed
~0.01. The binding failure is cooperative recovery credit, not skill semantics.
But three traps make a naive credit term fail:

1. exact per-agent graph-removal counterfactual (CF) is too heavy on the hot path;
2. exact CF goes to ZERO during full disconnect (`connected_uavs(G)=0`, every
   leave-one-out is also 0) — least signal exactly when recovery is needed;
3. even with a good responsibility weight, `pos(Delta Phi_global)` is ~0 across a
   disconnect window and only fires at the reconnection instant, so the reward is
   as sparse as the env reward in the regime that matters.

Therefore the core of P2-lite is SOFT recovery potential shaping; window gating is
only for the SCOPE of expensive CF computation, NOT for defining the main reward.

### Soft connectivity potential (the load-bearing requirement)

The soft potential MUST be computed from positions / distances / link margins /
soft edge weights, not only from binary graph connectivity. Binary
largest-component size and Fiedler value can stay 0 for long periods under a
disconnected graph and are therefore still sparse.

IMPLEMENTATION LESSON (2026-06-29). A *saturating* soft edge (`sigmoid((R-d)/temp)`)
is NOT enough: it goes to ~0 beyond `R + a few*temp`, so a bridge UAV in a gap
larger than the comm range sits in a flat "dead zone" mid-gap and gets no
gradient — the same sparsity, relocated. The smoke test caught this directly
(phi was flat/decreasing across the approach). The approach term must therefore
use a NON-saturating closeness that has gradient across the whole area:

```text
closeness(d) = exp(-d / approach_scale)         # approach_scale ~ 0.5 * area_size
```

The shipped module uses this. Distances are from `state_info` positions
(`uav_positions`, `ground_bs_positions`, `user_positions`, `area_size`), and the
binary `uav_connections`/`uav_bs_connections` matrices are used only to identify
the BS-connected anchor set (with self-exclusion), not for the gradient.

```text
phi_i_recovery(s) =
    w_bs   * bs_approach_potential_i     # closeness to nearest BS-connected anchor
  + w_brid * bridge_potential_i          # bs_approach_i * disc_approach_i (soft AND)
  + w_disc * disconnected_component_approach_i
```

`bridge_potential_i` (the product of both proximities) rewards a UAV MOVING toward
a position that can bridge two components, not only one that is already a bridge,
and peaks mid-gap. The anchor set always includes BS nodes, so `phi` never
collapses to zero even under full disconnect.

### Reward form (signed, high-level by default)

```text
Phi_total(s) =
    Phi_base_topology_service(s)            # P1 global potential from reward_info
  + lambda_rec * W_recovery(s) * sum_i phi_i_recovery(s)

W_recovery(s) = sigmoid((bh_threshold - credit_bh_frac) / temp)   # smooth STATE weight

F_high_team = gamma^dt * Phi_total(s_end) - Phi_total(s_start)
```

Optional per-agent high-level credit (better attribution; rewards the agent whose
OWN recovery potential improved, not a positioned bystander):

```text
F_high_i = gamma^dt * [W_recovery(s_end) * phi_i_recovery(s_end)]
                    -  [W_recovery(s_start) * phi_i_recovery(s_start)]
```

Rules:

- Use SIGNED potential shaping at the high level (telescopes; penalizes
  topology-breaking, avoids firefighter/arsonist farming). `positive_only` is
  allowed ONLY for low-level ablations.
- The window must be a smooth STATE weight `W_recovery(s)`, folded INTO the
  potential, not an external `if not window: reward=0` reward gate. The latter is
  non-stationary and boundary-gameable. Historical/hysteresis windows are not pure
  state functions and weaken the potential interpretation; keep them as a separate
  logged ablation, not the default.
- This is potential-INSPIRED credit shaping, not a theorem-guaranteed PBRS
  transformation once per-agent `F_i` are assigned to different agents/log-probs.
  Do not overclaim policy invariance (consistent with the P1 `delta`-mode note).

### Compute-gating is NOT reward-gating

```text
Exact leave-one-out CF is NOT a default hot-path reward.
exact_cf_reward_on  = false   (default)
exact_cf_compute_on = true    ONLY for diagnostics/audit, and only when:
    p2_cf_compute_window == true
    and (high_level_boundary or t % p2_cf_stride == 0 or disconnect/recovery transition)
    and candidate_agent_i == true
candidate_i = degree_i>=2 or near_backhaul_component_i or near_disconnected_component_i
              or serves_users_i or high_link_margin_i or on_component_bridge_i
```

The MAIN reward (soft `phi_i_recovery`) is cheap and computed from positions;
exact CF is retained only to (1) audit whether `phi_i_recovery` corresponds to
real relay contribution, (2) diagnose who is relay-critical in near-connected
states, (3) provide a teacher signal for later role/`g` training.

### Sequencing

```text
P2-lite-H0:  high-level shared signed Phi_total only            (first mainline)
P2-lite-H1:  add per-agent signed phi_i high-level credit
P2-lite-L0:  no low-level P2 reward                             (default)
P2-lite-L1:  small positive-only low-level phi_i progress       (ablation only)
```

High-level signed shaping is reasonable because it acts on skill / duration /
edit decisions; signed low-only easily pollutes primitive execution (P1 evidence),
so the low level stays positive-only and ablation-only.

Objective-boundary guard: P2-lite should be read as a way to densify sparse
cooperative credit, not as a task-specific "build a backhaul chain" objective.
Its reward variants must remain small, clipped, and ablation-gated.  The
decisive question is whether the mechanism helps HA-CTSE learn robust
cooperative behavior and service return under sparse reward; backhaul/recovery
metrics are probes of that question, not the final target.

### Two pre-checks (hard gate before any reward)

Pre-check 1 — fields. `state_info` must expose positions / link margins for the
soft potential. CONFIRMED PASS for S7 energy scenario: `uav_positions`,
`ground_bs_positions`, `user_positions`, `area_size`, and connection matrices are
present per step. (If a scenario lacked them, the first task would be to extend
`state_info`, NOT to write reward.)

Pre-check 2 — does the soft potential actually move during disconnect? Run
compute-on / reward-OFF first and require:

```text
delta_phi_soft_nonzero_rate_when_full_disconnect   > 0
delta_phi_soft_nonzero_rate_when_near_disconnect    > 0
corr(phi_i_recovery, later_recovery_event)          > 0
```

PASS is not "Phi can be computed" but "Phi_soft has non-zero deltas during
full/near disconnect windows AND change direction correlates with subsequent
recovery." Otherwise it is a pretty but useless shaping term.

RESULT 2026-06-29 (320k precheck, preset S7-S1, scenario energy, 8 env, reward-OFF;
partial at ~62%/update 50 of 80). The two delta-phi conditions PASS strongly:
`delta_phi_soft_nonzero_rate_when_full_disconnect` and `..._near_disconnect` both
~1.0 (the soft potential moves in essentially every disconnect segment — the
load-bearing property holds). The correlation condition is INCONCLUSIVE because it
is EVENT-STARVED: `p2_corr_phi_recovery_event` is nonzero in only ~13/55 updates,
peaks ~0.044, and flips sign — backhaul *recovery* (start disconnected -> end
`bh_frac >= bh_threshold=0.6` within one ~20-step segment) is rare, so the
correlation has almost nothing to bind to (`p2_credit_by_recovery_event` ~0 too).
This is a regime property, not a wiring bug (the wiring is proven: a synthetic
recovery signal yields corr ~0.996).

PROPOSED GATE REFINEMENT (decide when run completes): keep the two delta-phi rates
as the HARD gate (they directly test the load-bearing "moves before reconnection"
property), and demote `corr(phi, recovery_event)` to INFORMATIONAL unless the
recovery-event definition is broadened so it has signal — e.g. count PARTIAL
recovery (`bh_frac` rises by a margin, or ends above a threshold lower than 0.6)
rather than only full reconnection within a single short segment. A strict
`corr > 0` gate on an event-starved metric is a coin-flip and should not block
h0/h1/l1 on its own.

### Retired / deferred

```text
P2c role-classifier reward: RETIRED from the active gate. The topology-role
  discriminator stays an optional diagnostic only; it cannot block, justify, or
  define P2-lite. (Skill diversity is not the bottleneck: skill_entropy ~0.998
  even reward-pure, and HMASD itself reports ~24% task-useful individual skills
  on SMAC with zero-reward exploration in large spaces.)

P2b normative g training: DEFERRED until P2-lite shows measurable movement on
  credit_recovery_rate (up), credit_full_disconnect_mean (down),
  credit_bh_frac / credit_bh_thr (up). Training g before recovery credit moves
  risks another descriptive latent; g_tau must remain the compact-conditioned
  controllable coordination code, and the low-level actor must not consume
  c_tau / g_tau by default (skill bottleneck preserved).
```

## P3: Conditional Skill-Effect Discovery

> STATUS: conditional next stage. Activate only if the S7-S1 P1/P2-lite parity
> sweep remains clearly below HMASD or improves only diagnostic topology fields
> without task-metric and variance improvement.

P3 is the variable-lifetime version of HMASD's closed intrinsic loop:

```text
skill is sampled
-> low-level discoverer executes it as a sustained process
-> intrinsic pressure makes different skills induce distinguishable processes
-> credit/usefulness pressure pulls part of those processes toward task value
-> high level composes those processes across agents and lifetimes
```

HMASD's old discriminator form `q(z|s)` was not valuable because the classifier
itself was magic.  It was valuable because it directly fed dense low-level
intrinsic reward into the discoverer.  P3 must recover that closed loop after
skill lifetimes become asynchronous.

Therefore P3 is not a return to the legacy single-step classifier:

```text
bad question:   can q decode z_i from o_{t+1} or a segment label?
right question: given the same context x_i(t), does knowing z_i improve
                prediction/control of a short-horizon effect y_i(t,h) beyond
                context, phase, duration, reward, and agent-id shortcuts?
```

P3 should satisfy five constraints:

```text
dense enough to train the discoverer;
skill-conditioned enough to make z_i matter;
prior/shortcut corrected enough to avoid fake semantics;
outcome/process grounded enough to matter for the task;
low-level owned enough to shape executable behavior.
```

P3 uses micro-windows inside an active skill lifetime, not only completed
segments:

```text
h in {5, 10, 20} primitive steps
sample = (agent i, start time t, active skill z_i, context x_i(t),
          short-horizon effect y_i(t,h))
```

This restores HMASD-like dense discoverer pressure.  A long active lifetime
should produce multiple micro-window samples; one completed lifetime should not
be the only training example.

Context and effect definitions:

```text
x_i(t) =
  o_start_i, g_tau, agent_id, phase_bin,
  skill_age_i, duration_bucket,
  optional local topology / service / battery summaries

y_i(t,h) =
  short-horizon effect over h primitive steps
```

Candidate effect fields:

```text
delta position in agent-centric frame
delta velocity / movement direction
delta energy or charging progress
delta local service/access
delta soft recovery phi_i
delta link margin / local graph margin
delta connected users or access users
end-state local service/access/topology summaries
window-mean local service/link/backhaul-disconnect observables
```

After the P3-2c intervention audit, the target cannot stay delta-only.  P3-2c
showed that `z_i` changes low-level actions, but the delta target/model still
does not capture stable useful consequences.  The revised reward-off target
therefore includes absolute end-state and within-window occupancy summaries in
addition to deltas.  These are diagnostics for effect discovery, not new task
rewards.

2026-07-01 correction after Round 7 external review:

```text
Reward-off effect gain is a diagnostic, not a permanent gate.
```

The HMASD lesson is that diversity/semantics are not merely discovered
passively; they are created by dense intrinsic pressure.  If no reward path
encourages `z_i` to induce a stable process, then `p_full(y|x,z)` can fail even
when `z_i` is wired into the actor.  Therefore P3-2d should be treated as the
last reward-off target/extractor audit.  If it fails, the next principle is not
"keep adding passive classifiers"; it is to turn on a controlled forcing loop
with strict shortcut residualization and usefulness coupling.

User priority 2026-07-01: the forcing reward is the load-bearing part of P3.
P3-2e may still check that `z_i` has enough actuator capacity to create
persistent behavior modes, but it must remain a short architectural audit rather
than another long passive-probe phase.  The mainline is to design and test a
controlled low-level forcing reward that reconstructs HMASD's discoverer /
discriminator intrinsic pressure under variable lifetimes.

Chosen P3-4 first forcing form (2026-07-01):

```text
3 + 1 forcing reward =
  main: shortcut-residual skill discriminator over effect windows
  aux:  effect prediction residual
```

The residual discriminator is the HMASD-faithful component: it forces skill
differentiation by rewarding behavior/effect windows that make the active skill
identifiable after subtracting shortcut heads.  The effect prediction residual
keeps the signal process-grounded: it asks whether `z_i` helps predict the
short-horizon effect beyond context.  The two terms should be independently
weighted so experiments can switch them on/off:

```text
R_force_i =
    w_disc   * R_disc_residual_i
  + w_effect * R_effect_residual_i
  + w_durent * annealed_duration_entropy_bonus

R_disc_residual_i =
    log q_disc(z_i | effect_window_i, context_controlled)
  - max_shortcut log q_shortcut(z_i | duration, length, reward_sum,
                                phase, agent_id, context)

R_effect_residual_i =
    log p_full(y_i | x_i, z_i) - log p_base(y_i | x_i)
```

`R_disc_residual` should be the default load-bearing term.  `R_effect_residual`
is a stabilizing/grounding auxiliary term, not the sole forcing mechanism.  After
Round 8 audit, this auxiliary must also be residualized against duration/reward
shortcut baselines before it is trusted as a live reward:

```text
R_effect_residual_i =
    log p_full(y_i | x_i, z_i)
  - max(log p_base(y_i | x_i),
        log p_duration(y_i | x_i, d_i),
        log p_reward(y_i | x_i, reward_sum_i))
```

Equivalent conservative formulations are acceptable, but the key constraint is
that the live effect reward cannot be explained by duration/reward shortcut
predictors.  Both forcing terms must remain low-level, micro-window distributed,
warmup-gated, clipped/centered, and disabled if shortcut heads dominate.

Implementation boundary for the first P3-4 version:

```text
The forcing reward must not directly optimize communication/backhaul metrics.
The default residual discriminator feature set should use behavior/action plus
generic motion/energy effect fields.  Service/topology/communication fields can
remain probe diagnostics and may only enter the intrinsic reward under an
explicit ablation flag, not as the default algorithm claim.
```

The corrected P3 gate is:

```text
Before reward:
  verify data path, target availability, shortcut heads, and z->actor capacity.

With reward:
  require effect gain / behavioral differentiation to rise,
  require skill selection entropy to move away from inert max-entropy uniformity,
  require duration/reward/context shortcut gaps not to dominate,
  require task metrics and variance not to regress.
```

High skill selection entropy alone is not evidence of skill discovery.  It may
mean skills are interchangeable.  Successful P3 should create behavioral
differentiation and then allow context-dependent specialization, not maximize
uniform skill use forever.

2026-07-01 Round 8 decoupling control correction:

```text
A positive P3-4 forcing result proves only that the forcing mechanism helped,
unless the same forcing condition is compared against a fixed/shared-lifetime
control.  Before claiming the central HA-CTSE decoupling mechanism, run at least
one fixed-duration + same-forcing control, e.g. candidates=(7,) with disc_only.
```

2026-07-01 Round 8 hazard-SMDP trigger:

```text
If shortcut heads keep matching or exceeding the discriminator across disc_only
and the revised residual effect/discriminator path, treat that as evidence that
discrete duration labels are structurally contaminating skill semantics.  At
that point, revisit the hazard-SMDP alternative instead of endlessly adding
new debiasing heads.
```

Estimator structure:

```text
Full:
  p_full(y_i | x_i, z_i)

Baseline:
  p_base(y_i | x_i)

Effect gain:
  R_effect_i = log p_full(y_i | x_i, z_i) - log p_base(y_i | x_i)
```

This asks whether `z_i` controls a behavior effect, not whether a classifier can
recover `z_i` from a whole segment.

Optional skill-effect prototype pressure may be added after the predictive-gain
probe is positive:

```text
e_i = f_effect(y_i)
mu_z = learnable effect prototype for skill z

L_proto =
  - log exp(sim(e_i, mu_z_i) / tau)
        / sum_z' exp(sim(e_i, mu_z') / tau)
```

Negative samples must be context controlled, e.g. same phase bin, similar
backhaul/service state, duration bucket, and preferably agent-id controlled.
Otherwise the model learns context usage (`this state tends to choose z`) rather
than skill-effect semantics (`this z causes this effect`).

Actually-work coupling remains an open design point and must preserve reward
separation.  The tempting form is:

```text
R_intr_i =
    lambda_ctrl * center_clip(R_effect_i)
  + lambda_use  * stopgrad(U_i) * clip_pos(R_effect_i)
```

but `U_i` must not be a raw communication metric or a disguised copy of
environment reward.  For the first with-force version, prefer separating:

```text
low-level intrinsic:
  skill controllability / effect differentiation / shortcut-residual signal

high-level target:
  skill-lifetime cumulative environment reward
  + explicitly separated intrinsic terms, if used
```

This follows the HMASD separation: environment return expresses task usefulness
at the RL target level, while discoverer/discriminator-style intrinsic pressure
creates executable skill semantics.  Raw communication fields such as
service/QoS, throughput, backhaul, or recovery remain diagnostics for S7-S1
rather than direct P3/P4 reward terms.

Duration exploration may use an annealed high-level entropy bonus over duration
selection:

```text
R_duration_explore = beta_T(t) * H(pi_T(. | context))
beta_T(t) decreases over training
```

This is an exploration aid, not a permanent objective.  It should prevent early
fixed-duration collapse while still allowing context-dependent specialization.
If duration entropy remains high forever, it may indicate indecision rather than
useful heterogeneous lifetimes.  If it collapses too early, the variable-lifetime
mechanism is not being explored.

First implementation rules:

```text
inject low_only
small coefficient: lambda_ctrl/lambda_use roughly 0.02-0.05
warmup enabled
shortcut gate mandatory
high-level gate closed
on-policy only
```

P2-lite remains separate:

```text
P3 answers:
  Do skill latents become controllable, distinguishable, persistent behavior
  effects that can be composed?

P2-lite answers:
  Does the policy receive dense enough cooperative credit to use those effects?
```

Final intended loop:

```text
P3 creates useful skill effects.
P2-lite supplies cooperation-credit repair.
Variable lifetime lets different agents keep/edit those effects at different
horizons.
```

Superseded sequencing note (2026-07-01): the older "train `g_tau` later after P3"
framing is no longer the active contract.  `g_tau` still must not become a direct
topology-role classifier or low-level actor shortcut, but it must be made live
early enough for P3 to be HMASD-faithful team-conditioned individual forcing.
The accepted replacement is a generic g-revival path: high-level PPO reward from
a team/joint discriminator and/or a decision-level `I(g; joint
skill/duration/edit decisions | context)` usage loss, with communication fields
kept out of the default reward path.

This preserves the HA-CTSE skill bottleneck (`z_i -> behavior process`) while
restoring HMASD's missing dense semantic pressure on the discoverer. A P3
variant is valid only if it improves task metrics and cooperation stability, not
merely classifier accuracy.

2026-07-01 G2 Stage-A implementation note:

```text
The first code implementation for g-revival is intentionally not a team
discriminator and not a communication heuristic.  It is a high-level,
decision-level usage pressure:

  enumerate g under the same OPT context
  measure whether pi_z and pi_duration change
  optionally maximize I(g; skill decisions | context)
             + I(g; duration decisions | context)

This makes g testably non-decorative in the high-level controller while keeping
the primitive actor bottleneck intact.  It is only a prerequisite signal for the
cooperative half.  Passing this gate does not prove cooperation; failing it means
team-conditioned individual forcing and later team/joint discriminator designs
are conditioning on a dead context variable.

Current limitation:
  edit is not yet a separate stochastic high-level head in standalone HA-CTSE,
  so edit MI/KL/TV metrics are logged as zero until co-edit is implemented.
```

2026-07-02 OPT-specific Round 10 correction:

```text
OPT is not a generic hidden-state encoder.  In HA-CTSE it is the descriptive
interaction-structure decomposition layer:

  OPT prototypes P_n:
    sparse/diverse interaction basis

  omega_tau:
    current aggregation weights over interaction prototypes

  c_tau:
    compact descriptive interaction context

  g_tau:
    controllable team coordination response over the OPT interaction basis

  z_i:
    executable individual child option under g_tau

  T_i:
    child option commitment
```

Therefore `g_tau` must not be a discretized `c_tau`, an argmax of OPT weights,
or a duplicate label for the current interaction pattern.  The correct
intervention question is:

```text
same c_tau, same omega_tau, same state, forced g = 0..G-1
  -> do pi_z / pi_duration / pi_edit and later joint process change?
```

The g-revival objective should be read as:

```text
I(g ; joint skill/duration/edit decisions | c_tau, omega_tau)
```

not merely `I(g; decisions | context)`.  This prevents g from re-encoding what
OPT already described.

P3/P4 residuals must subtract OPT shortcuts:

```text
P3 individual forcing:
  q_full(z_i | effect_i, c_tau, omega_tau, g_tau)
  - max(q_opt(z_i | c_tau, omega_tau),
        q_opt_g_prior(z_i | c_tau, omega_tau, g_tau),
        q_duration(z_i | d_i),
        q_reward(z_i | reward_sum_i),
        q_phase_agent(z_i | phase, agent_id))

P3 effect prediction:
  p_full(y_i | x_i, c_tau, omega_tau, g_tau, z_i)
  - max(p_opt(y_i | x_i, c_tau, omega_tau),
        p_opt_g(y_i | x_i, c_tau, omega_tau, g_tau),
        p_duration(y_i | x_i, d_i),
        p_reward(y_i | reward_sum_i))

P4 team forcing:
  q_full(g_tau | joint_effect_window, c_tau, omega_tau)
  - max(q_opt(g_tau | c_tau, omega_tau),
        q_duration(g_tau | joint_duration_pattern),
        q_reward(g_tau | segment_reward_summary),
        q_assignment_only(g_tau | joint z/d/edit labels),
        q_prior(g_tau | c_tau))
```

The preferred P4 team effect window is generic MARL structure, not
communication metrics:

```text
future change in OPT interaction pattern
delta omega_tau_to_tau+h
prototype occupancy / membership changes
prototype attention-map summary changes
joint action / observation dynamics
pooled individual effect embeddings
```

Engineering consequence:

```text
P4-1b must not only scale up g_info.  First expose/log omega_tau and
prototype-response diagnostics, then make g_info explicitly conditioned on
fixed (c_tau, omega_tau).  If q_opt or q_opt_g_prior explains z_i/g_tau as well
as the full model, the algorithm learned an OPT-context shortcut, not skill
semantics.
```

2026-07-02 Round 12 substrate-gate correction:

Round 12 changes the status of OPT `omega_tau` / `c_tau` from a useful feature
to a hypothesized **situation substrate**.  That hypothesis must be proven before
HA-CTSE builds hazard renewal, SEF/DADS reward, target-situation commitment, or
co-edit complementarity on top of it.

The offline dwell diagnostic is therefore upgraded into a pre-registered
substrate gate:

```text
G-DWELL:
  discretized omega / prototype membership has dwell substantially longer than
  a single check interval, and its transition matrix is more diagonal than a
  block-shuffled null over the same trajectories.

G-OUTCOME:
  early-window omega predicts chain-holding vs zero-service episode mode across
  episodes/seeds, and beats simple-feature shortcut baselines.

G-ROLE:
  omega membership pattern carries positive information about generic
  counterfactual role labels and stays stable within role phases.
```

G-ROLE has an additional validity condition: the topology-role counterfactual
labels must be explicitly computed for the diagnostic dump and must have
nonzero variance.  If `topology_cf_*` defaults to all-zero labels because the
probe/counterfactual path was not enabled, the G-ROLE read is structurally
invalid rather than empirical evidence against the substrate.

Autocorrelation alone is not enough: slow but semantically empty features can
pass autocorrelation.  The substrate must show temporal, outcome, and role/event
structure.

Decision tree:

```text
gate passes:
  proceed to reward-pure situation-change hazard, then SEF/DADS.

omega fails but compact c has structure:
  cluster c instead of raw weights and re-gate.

omega and c both fail:
  allow exactly one offline encoder retrain on pooled logs with explicit
  situation-ness objectives (slowness, next-omega predictability, discreteness),
  then re-gate.

retrain fails:
  validate the Round 12 paradigm on a hand-crafted topology situation space
  before returning to learned omega.
```

2026-07-02 Round 12 Stage 1 boundary:

The first mechanism after a passed substrate gate is **reward-pure
situation-change renewal**, not a new intrinsic reward.  The intended test is:

```text
Does debounced kappa_t identify useful situation boundaries such that renewing
eligible active skills at those boundaries improves task learning or stability
using only the external environment return?
```

Stage 1 therefore permits:

```text
diagnostic-only kappa logging
oracle_change renewal: renew eligible active skills when debounced kappa changes
default-off hazard-control plumbing
```

Stage 1 does not permit:

```text
SEF/DADS reward injection
communication-specific intrinsic reward
target-situation commitment
co-edit complementarity reward
claiming learned hazard control without a real hazard PPO buffer/update
```

The `learned_beta` branch, until a proper hazard-decision buffer and PPO-style
update are implemented, is only an inference-only wiring probe.  It must not be
interpreted as evidence for a learned situation-validity hazard.

2026-07-03 Round 13 implementation caveat:

Current Stage 1 code still computes one env-global `kappa` from OPT membership
weights and feeds the same debounced `kappa` change pulse to all eligible
agents.  That is useful as a global-boundary renewal diagnostic, but it is not
the intended R12 mechanism:

```text
per-agent local situation kappa_i
-> per-agent situation-validity hazard beta_i
-> asynchronous skill renewal because each agent's local role/context becomes
   invalid at different times
```

Therefore R12-1b conservative renewal can evaluate guard/rate effects around a
global boundary trigger, but it cannot validate or falsify per-agent
situation-validity hazard semantics.  Before treating Stage 1 as an algorithmic
mechanism, implement or explicitly test `kappa_i` and boundary actionability.

2026-07-03 Round 14 Stage 1 prototype-response principle:

Round 14 re-centers the next probe on OPT as a coordinate system rather than a
generic encoder.  OPT provides a descriptive interaction basis:

```text
omega_t / compact context:
  what interaction situation is present

prototype relevance for agent i:
  which interaction substructure agent i is currently exposed to

z_i:
  a sampled prototype-response code, not a recognized state label
```

The critical distinction is:

```text
recognition variable kappa = f(state):
  can describe the present but cannot by itself create HMASD-style intrinsic
  pressure, because q(kappa | state) is vacuous.

sampled response variable z_i:
  remains a real decision.  A discriminator can ask whether z_i changes the next
  local observation / short response distribution under the same situation.
```

Therefore the first Round 14 intrinsic candidate is the individual half that
survives recognition:

```text
r_proto_i =
  log q_phi(z_i | o_i,t+1, situation_t)
  - log p_phi(z_i | situation_t)
```

where `situation_t` may be kappa, omega, or no condition for ablation.  The
prior must be situation-conditioned because a useful response distribution is
expected to depend on the situation; an unconditional prior would incorrectly
reward usage imbalance.

Design boundaries:

```text
1. This is not a communication/backhaul reward.
2. This is not the legacy HMASD discriminator transplanted directly.
3. This is not a process posterior over whole segments.
4. The reward path is low-only, default-off, warmup-gated, and must be tested
   after a diagnostic-only probe.
5. Stage 2 omega-space commitment, coverage complementarity, and team transition
   reward are blocked until Stage 1 shows non-vacuous residual signal.
```

2026-07-04 channel-pressure rule after the R15 A1 AR-prefix read:

```text
Every new latent/control channel must ship with one of two labels:

1. active channel:
   the code includes an objective, loss, reward, or supervised target that
   requires the channel to change decisions, values, or predictions.

2. decorative-until-stage-X channel:
   the code explicitly marks the channel as untrained/diagnostic only, and no
   reward-off probe is allowed to treat spontaneous use of that channel as a
   hard success criterion.

Wiring diagnostics, training-pressure diagnostics, and mechanism-performance
diagnostics must be separated.  A channel that can move logits under forced
intervention but stays unused in a reward-off rollout is not a wiring failure;
it is evidence that no current objective requires the channel to carry
coordination information.
```

2026-07-04 Round 16 roster-docking principle:

```text
HMASD's autoregressive complementary assignment is synchronized: z_{1:i-1}
means "agents already edited in this same high-level decision event."

HA-CTSE intentionally decouples skill lifetimes.  Under this asynchronous
structure, same-check AR can be starved because most renewal checks contain
only one or a few agents.  The measured R15 A1 last-10 renewal statistics were:

  renewal_agents_mean    ~= 1.44 of 6
  renewal_full_sync_rate = 0.0
  renewal_pairwise_corr  < 0

Therefore the honest asynchronous analogue of sequential assignment is not
"order agents inside the current check"; it is:

  renewing agent docks against the standing roster of teammates' active skills
  and ages.

The sequential structure becomes temporal rather than instantaneous:

  prefix_i(t) = roster(z_{-i}^{active}(t), age_{-i}^{active}(t))

This preserves the HMASD spirit of complementary skill selection while fitting
decoupled lifetimes.  Same-check AR remains a valid control/ablation, but it is
not sufficient evidence that sequential assignment works under asynchrony.
```

Roster-docking invariants:

```text
1. Roster conditioning uses the renewal-time snapshot, not live state at update
   time.  Stored assignment log-prob and PPO evaluation must be conditioned on
   the same roster snapshot.

2. In a forced full-sync renewal, roster mode must reduce to HMASD/same-check
   AR: later renewers see earlier renewers' newly sampled skills.

3. Roster identity matters.  The coordination diagnostic is:
     KL(selection | true roster || shuffled roster)
   not only KL against a zero embedding.  The zeroed-roster KL is mechanical
   capability; shuffled-roster KL is content/coordination use.

4. Skill age is part of the roster state.  Docking against a nearly expired
   teammate commitment is not the same as docking against a fresh commitment.
```

2026-07-04 Rounds 17-19 principle corrections (cross-model review cycle):

```text
1. EXOGENOUS VARIATION, not persistence, is what commitment buys (R17.2):
   sampled Z varies GIVEN THE SAME STATE — team-level exploration through
   committed behavioral diversity. Recognized kappa is also persistent but
   provides zero exogenous variation. Persistence does not distinguish
   commitment from recognition; variation does.

2. TWO-LAYER SYMMETRY THEORY (R18): role-allocation symmetry ("who does
   what") is solved by sequential structure (AR chain / roster-docking);
   global-strategy symmetry (Alpha vs Beta from the same state) is NOT —
   and the deficit is specifically ATOMIC variation: under async docking a
   strategy flip propagates through staggered renewals, leaving a punished
   mixed configuration in between. Team commitment buys exogenous variation
   AND atomic coordinated switching.

3. KAPPA* IS THE CANONICAL COMMITMENT FORM (R18.2): injecting exploration
   noise into the recognition encoder is REJECTED — kappa is dual-use
   (policy input AND hazard/termination signal), so dithered recognition =
   spurious renewals; and any noise held fixed over a window IS a
   commitment latent. Every correct patch collapses into a thin stochastic
   commitment layer pi(kappa*|kappa) on top of clean recognition.

4. 2x2 TASK MATRIX (R18.3): axes {sync-friendly | heterogeneous-tempo} x
   {coverage-bound | deceptive}. Validity-hazard lifetimes load-bearing iff
   heterogeneous-tempo; kappa* commitment load-bearing iff deceptive.
   S7-S1 is (sync-friendly, coverage-bound): NEITHER headline mechanism is
   load-bearing there — S7-S1 parity must come from the dense intrinsic
   bootstrap. Do not read S7-S1 results as verdicts on the two mechanisms.

5. DUAL-ENGINE PRINCIPLE (R19): the individual coordinator-residual term is
   a ROLE-DIVERSITY drive (expectation bounded by ln n_skills; saturates
   once local behaviors are distinguishable; no pressure toward unvisited
   states). HMASD's team term was the STATE-DIVERSIFICATION engine; vacuity
   killed it; its unique structural replacement is the situation-transition
   residual log q(kappa'|kappa,xi) - log q(kappa'|kappa) with
   SELF-TRANSITIONS INCLUDED (stabilization must pay: holding the relay
   chain is a xi-dependent predictable self-transition). Neither engine
   substitutes for the other.

6. KAPPA DUAL-USE CAUTION (R19.3): the team-transition reward pays for
   controlling kappa transitions; the validity hazard fires on kappa
   transitions. Both live => reward-induced churn risk (R12-1a via the
   objective). corr(team_transition_reward, renewal_rate) is a MANDATORY
   input to any hazard go decision. Corollary: the team term is SAFER
   before the hazard exists than after.

7. MOVING-NULL MITIGATION (R17): if the coordinator-residual reward
   self-extinguishes before separation (pre-registered red flag), the
   sanctioned fix is the prior-mixed null (1-beta)*pi_h + beta*uniform,
   beta ~ 0.1, default off — not a reward floor, not a coefficient raise.

8-SUPERSEDED note (2026-07-04, same day): the disposition below is
   OVERRIDDEN by the user Architect decision (Round 21): the coordination
   intent is built NOW as sampled Z on a slow synchronized clock with
   atomic AR reassignment, engine included (team discriminator reward,
   non-vacuous because Z is sampled). The two-layer vocabulary and the
   never-refactor-g-into-intent rule survive: pi_Z is a clean rebuild on
   the bridge's machinery with the decorative wiring deleted; the
   deceptive-axis gating of R18.3 is replaced by the user's proven-
   structure-first judgment, recorded as an override.

8A. R21 LAUNCH-PREFLIGHT CONSTRAINTS (2026-07-05): sampled team-intent Z
   creates an atomic reassignment boundary, so K_team becomes the effective
   maximum lifetime unless it exceeds the individual duration set.  Therefore
   K_team must be >= 2x the largest active duration candidate for the main
   R21 read (current default 48 for candidates 3/7/13/24), or the experiment
   fabricates a false duration-collapse pathology.  Log truncation by duration
   bucket, especially for long candidates.  The team discriminator coefficient
   starts at 0.05, not 0.1, because R16.5 measured 0.1 as a collapse/ratio
   risk and 0.05 as the cleaner stabilized base.  A default-off Z entropy floor
   is allowed only as an explicitly labeled stabilizer/insurance flag; if it
   remains active late, task gains may count as scaffolded performance but not
   as self-sustained team-intent heterogeneity