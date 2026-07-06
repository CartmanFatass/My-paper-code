# R22 Two-Clock ELBO Sketch

## 1. Purpose / Status

> 2026-07-06 R21 AUTOPSY AMENDMENT (evidence, see `memory/R21_AUTOPSY_REPORT.md`).
> The R21 autopsy makes four ELBO-shaping findings, now load-bearing for this note:
> (1) The missing ingredient is confirmed to be a **cross-layer actionability term
> `I(Z ; ξ | c, ω)`** (ξ = joint assignment/roster/duration structure). Forced-Z
> assignment KL ≈ 0.002 at BOTH random-init and final → Z was never actionable, so
> this ELBO is a *rewrite around a never-actionable Z*, not "stop suppressing Z."
> (2) The team discriminator `I(Z ; s_next)` is downstream-useless until behavior
> depends on Z (disc measured at chance, verified genuine not a bug) → **gate any
> `q_D(Z|·)` reward behind a `forced_Z_assignment_KL` floor**, else decorative.
> (3) No team-disc / coordinator-residual double-count exists in R21 *because the
> team channel is inert*; the composition question only becomes real once
> actionability exists. (4) Experimental confound to fix before any two-clock
> rerun: `team_intent_k=48 ≈ episode=50` intervals ⇒ ~one Z commitment per episode,
> so the two-clock degenerated to ~one-clock and starved within-episode Z variation
> — require `team_intent_k ≪ episode horizon`. The R21 task regression is a
> policy-path effect (forced AR-roster/Z-conditioning), not Z-boundary churn.
>
> 2026-07-06 GPT post-autopsy addendum (accepted; see `cross_validation.md`
> "2026-07-06 GPT post-autopsy advice"). Additional ELBO/design constraints:
> (5) ARCHITECTURE CAPACITY GATE precedes objective work: since random-init
> forced-Z KL≈0.002 is also weak, first make Z structurally able to move ξ (Z as
> true AR first token / Z-FiLM on skill/duration/edit heads), keep the low-level
> actor blind to Z/c, and do NOT alter the S-base selection path (avoid the
> policy-path confound). Falsifier: random-init forced-Z assignment KL must clear
> a decorative band (value TBD) before any reward term.
> (6) LIFETIME TENSION is now empirical, not theoretical: `K≪episode` conflicts
> with long-lifetime protection (`K≥2·max_dur` ~impossible at 50 checks/dur24).
> Resolve via Choice 1 (short duration candidates, K≈8-12 — cleanest mechanism
> test) before Choice 2 (decoupled parent-child lifetimes: Z boundaries do not
> truncate active z_i; each z_i stores birth_Z/birth_context, new renewals dock to
> current Z). Choice 1 tests actionability, NOT the decoupled-lifetime thesis —
> keep separate.
> (7) The ELBO must explicitly answer: is `I(Z;ξ|c,ω)` required; is `I(Z; future
> joint effect|c,ω)` enabled ONLY after actionability; does `I(z_i; local
> effect|Z,ξ,c,ω)` replace the old `q_d`; which of `H(Z),H(ξ),H(z_i),H(dur/edit),
> H(a)` are derived constraints vs stabilizers; how two-clock credit handles K_team
> and rollout truncation. Do NOT implement SAC-style auto-temperature yet — write
> the derived-vs-stabilizer split in the ELBO first. Do NOT code `I(Z;ξ)` as a
> reward before the theory note + double-count audit are complete.

This note is the R22-1 derivation sketch for the current HA-CTSE mainline:

```text
OPT recognition substrate
  -> slow sampled team commitment Z
  -> asynchronous individual response skills z_i
  -> low-level actions
```

Status: theory-first design note, not a formal theorem and not an implementation
authorization.  It is meant to make the current R21/v6 objective explicit enough
to audit double-counting before new rewards, target-entropy mechanisms, or
cross-layer terms are added.

The key correction is that R12 is now substrate/control and R19 is a
mechanism-negative control unless later complete reward-on evidence contradicts
that read.  The active algorithmic question is whether the two-clock hierarchy
can reproduce HMASD's useful commitment/discriminator loop under asynchronous
individual skill lifetimes.

Evidence status:

```text
R21/v6 hierarchy: implemented default-off, launch-ready, not yet performance-read.
Two-clock objective: derivation sketch only.
Entropy target design: not implemented.
Cross-layer term: optional and unreviewed.
R12/R19: controls, not current cooperation engine.
```

## 2. Variables And Clocks

Model variables:

```text
s_t, o_{i,t}                       environment state and local observations
c_t, omega_t = OPT(s_t, o_{1:n,t})  continuous recognition substrate
Z_m ~ pi_Z(Z | c_t, omega_t)        slow sampled team commitment
z_{i,r} ~ pi_z(z_i | Z_m, c_t, omega_t, o_{i,r}, roster_r)
a_{i,t} ~ pi_l(a_i | o_{i,t}, z_{i,active_i(t)})
T_i                                asynchronous individual skill lifetime
```

Clock relation:

```text
Recognition clock:
  c_t and omega_t are refreshed every check interval.

Team commitment clock:
  Z_m is sampled every K_team checks or at rollout reset.
  Between team boundaries, Z_m is held fixed.

Individual response clock:
  each agent renews z_i asynchronously according to its own lifetime T_i,
  while docking to the currently held Z_m and the renewal-time roster.
```

Notation used below:

```text
m                 team-commitment index
r                 individual renewal index
m(r)              team-commitment index active at renewal r
active_i(t)       renewal r whose z_{i,r} controls agent i at primitive time t
ctx_m             (c_m, omega_m, roster_m or other allowed context)
ctx_{i,r}         (Z_{m(r)}, c_r, omega_r, o_{i,r}, roster_r)
tau               rollout block with primitive steps and segment records
```

The important structural asymmetry is that `Z_m` is shared and slow, while
`z_{i,r}` is per-agent and asynchronous.  A valid objective has to charge the
sampled `Z_m` once per team commitment interval, then charge each individual
renewal conditional on the held `Z_m` without recharging `Z_m`.

## 3. Factorization Over Rollout Blocks

For one rollout block, the intended generative/control factorization is:

```text
p_theta(tau, Z, z_{1:n})
= p(env)
  * product_m
      pi_Z(Z_m | c_m, omega_m)
  * product_i product_{renewals r}
      pi_z(z_{i,r} | Z_{m(r)}, c_r, omega_r, o_{i,r}, roster_r)
  * product_t product_i
      pi_l(a_{i,t} | o_{i,t}, z_{i,active_i(t)})
```

This is not claiming that OPT is a learned latent-variable model with a complete
likelihood.  In the current code, `c_t` and `omega_t` are recognition features
used as context.  The objective should therefore be read as an SMDP policy
objective with variational-discriminator-style auxiliary terms, not as a fully
specified density model for observations.

The rollout-block log policy contribution separates naturally:

```text
log p_theta(Z, z, a | tau context)
= sum_m log pi_Z(Z_m | c_m, omega_m)
  + sum_i sum_r log pi_z(z_{i,r} | Z_{m(r)}, c_r, omega_r, o_{i,r}, roster_r)
  + sum_t sum_i log pi_l(a_{i,t} | o_{i,t}, z_{i,active_i(t)})
```

The slow term should be aligned with team-level credit over the held interval.
The fast term should be aligned with individual renewal segments.  Any
implementation that adds a team reward at every asynchronous z renewal risks
turning one sampled commitment into many counted rewards.

## 4. ELBO / Objective Candidate

The practical candidate is a lower-bound-inspired actor objective, not a proof
of a tight ELBO.  It combines environment return with residual predictability
terms and entropy regularizers:

```text
J(theta)
= E_tau [
    R_env(tau)

    + lambda_team *
        sum_m (
          log q_D(Z_m | joint_future_or_state_m)
          - log p_hat(Z_m | context_m)
        )

    + lambda_ind *
        sum_i sum_r (
          log q_d(z_{i,r} | o'_{i,r}, kappa_or_c_r, Z_{m(r)})
          - log pi_z_stored(z_{i,r} | Z_{m(r)}, context_{i,r}, roster_r)
        )

    + alpha_Z * sum_m H(pi_Z(. | c_m, omega_m))
    + alpha_z * sum_i sum_r H(pi_z(. | Z_{m(r)}, context_{i,r}, roster_r))
    + alpha_T * sum_i sum_r H(pi_T(. | Z_{m(r)}, context_{i,r}, roster_r))
    + alpha_a * sum_t sum_i H(pi_l(. | o_{i,t}, z_{i,active_i(t)}))

    + optional lambda_cross *
        I(Z ; joint response / roster / xi)
  ]
```

Clock-count normalization caveat:

```text
The sums above live on different event counts:
  team terms       scale with number of Z boundaries,
  individual terms scale with number of agent renewals,
  action terms     scale with primitive steps,
  environment return may be per-step, per-segment, or SMDP-aggregated.

Before tuning lambda/alpha values, every term must be reported per event type
and, where used as reward, normalized or clipped on its own clock.  A coefficient
that is safe per Z boundary can be unsafe when accidentally broadcast over
individual renewals or primitive steps.
```

Term meanings:

```text
R_env:
  the external task return.  Backhaul, coverage, recovery, and throughput are
  diagnostics unless they are already part of the environment reward.

team residual:
  asks whether sampled Z predicts a team-level future/state better than a
  context-only prior.  It is load-bearing only if Z is sampled and not directly
  leaked into q_D through trivial inputs.  The prior/null term p_hat is a
  stored or detached baseline for scoring; actor gradients must not flow
  through p_hat as a live policy term.

individual residual:
  asks whether each z_i predicts an individual response beyond the stored
  assignment probability.  Conditioning on Z is allowed, but the term must not
  become a second team discriminator under another name.  log pi_z_stored is
  the behavior/null log-prob recorded at sampling time and is detached when
  used inside the residual score; it is not a second live actor loss.

entropy:
  exploration/anti-collapse pressure for Z, z_i, duration/edit, and action.
  Entropy is not a reward for heterogeneity by itself.  R22-4 should recast
  these as per-head target-entropy constraints before automatic temperatures
  or new floors are added.

cross-layer term:
  optional pressure that Z should organize the joint pattern of individual
  responses, roster states, or an interaction summary xi.  This term is not
  currently implemented and must survive leak and double-count audits first.
```

A more conservative target-entropy form for a head `h` would replace fixed
bonus coefficients with:

```text
minimize over log_alpha_h:
  L_alpha_h = -log_alpha_h * stopgrad(H_target_h - H_observed_h)
```

Under standard gradient descent this increases alpha when observed entropy is
below target and decreases alpha when observed entropy is above target.  Any
implementation using a different optimizer convention must state the sign
explicitly in tests.

That conversion is a later design step.  Current entropy floors should be
described as stabilizers until that design is reviewed.

## 5. Double-Count Audit Table

| Term | Current code source | What it explains | Possible double count | Decision rule |
| --- | --- | --- | --- | --- |
| team discriminator | `ha_ctse_process/team_intent.py` | team-level commitment semantics for sampled `Z` | overlaps with cross-layer response term if both reward the same joint future signal | keep unless team term is fully explained by individual residual or direct leak |
| individual residual | `ha_ctse_process/prototype_response_discriminator.py` and prototype-discriminator path in `standalone_agent.py` | per-agent skill response semantics conditioned on substrate and optional `Z` | can double-count team if `Z` is directly leakable or if the classifier learns team identity instead of individual response | keep only with stored assignment/null baseline and leak audit |
| coordinator residual | R15/R16 roster/coordinator path in `prototype_response_discriminator.py` and `standalone_agent.py` | AR/roster assignment pressure for asynchronous docking | stale if R21 sampled `Z` supplies the real team pressure and roster KL remains decorative | prune, absorb, or demote after R21 read |
| entropy/floor | `config.py`, `standalone_agent.py`, and train guards | exploration and non-collapse for `Z`, `z_i`, duration/edit, and action | can become forced heterogeneity detached from task usefulness | convert to target-entropy constraint; keep floors labeled as stabilizers meanwhile |
| R19 transition residual | `outcome_residual` / transition heads and `intrinsic_rewards.py` | recognition-only transition control around situation changes | competes with team intent if treated as another cooperation engine | control only unless complete reward-on evidence shows positive MI plus task gain |
| optional cross-layer `I(Z ; joint response / roster / xi)` | not implemented | whether slow team intent organizes the asynchronous response layer | may duplicate team discriminator and coordinator residual | design only; require ablation and leak audit before adding |
| environment reward | environment / PPO return path | external task success | can be relabeled as intrinsic and contaminate mechanism claims | keep separate from intrinsic residuals |

## 6. Credit Tension Triangle

R22 has a three-way tension.  Any proposed term should say which corner it
helps and which corner it stresses:

```text
1. Team commitment credit
   Z must be slow enough and shared enough to create cooperative exploration.
   If the clock is too fast or the reward is charged too often, Z degenerates
   into another per-step label.

2. Individual response credit
   z_i must remain agent-specific and useful under asynchronous lifetimes.
   If Z explains everything, z_i becomes decorative; if z_i explains
   everything, Z is not a team commitment.

3. Sample efficiency / anti-collapse
   both Z and z_i need enough samples per label to train discriminators.
   If Z has too few boundaries, team_disc_acc and reward estimates are noisy;
   if entropy floors dominate, diversity can be forced without usefulness.
```

The likely failure is not a clean "recognition versus commitment" verdict.  A
bad run can reflect any side of the triangle: insufficient `Z` samples,
over-scaled residual rewards, leak-prone discriminators, or a useful team code
whose credit does not reach the low-level behavior.

## 7. Mapping To Current Code / Modules

Current R21/v6 surfaces:

```text
ha_ctse_process/team_intent.py
  TeamIntentDiscriminator and Z-label entropy helpers.
  This is the natural home for q_D(Z | joint_future_or_state) and its
  prior-corrected reward diagnostics.

ha_ctse_process/standalone_agent.py
  Rollout segments, team-intent boundary state, async renewal docking,
  high/low reward composition, and metrics.  This is where clock accounting
  must stay correct: charge Z at team boundaries, z_i at agent renewals.

ha_ctse_process/prototype_response_discriminator.py
  Individual residual q_d(z_i | next observation, condition), stored-null
  residual logic, and roster/selection independence diagnostics.

ha_ctse_process/config.py
  Default-off switches and coefficients such as enable_team_intent,
  team_intent_k, team_disc_coef, prototype discriminator flags, transition
  residual flags, and entropy-floor stabilizers.

ha_ctse_process/train.py and ha_ctse_process/plotting.py
  Metric propagation, CSV/TensorBoard fields, and diagnostic plots.

tests/r21_team_intent_test.py
  Regression tests for boundary semantics, async docking, team-code
  conditioning, and prior-corrected detached discriminator reward.

scripts/run_r21_team_intent_cloud_64env.sh
  Launch-ready R21 mechanism read.

scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
  Matched HMASD current-environment calibration read.
```

R12/R19 mapping:

```text
R12 / OPT substrate:
  Keep omega/c/kappa as recognition context and diagnostic/control substrate.
  Do not expand situation hazard or SEF/DADS-style reward before R21/HMASD
  reads and R22 objective review.

R19 transition residual:
  Keep transition/outcome residual heads as mechanism-negative controls unless
  complete reward-on logs show sustained positive transition MI and task gain.
```

## 8. Falsifiable Predictions And Failure Interpretations

Prediction 1: sampled commitment should matter.

```text
If sampled slow Z is the missing engine, R21 team-disc reward should improve
Z usage and task stability beyond the matched S-base.  Expected early signs:
team_disc_acc rises gradually rather than instantly saturating; Z usage does
not collapse; task metrics are not worse at the 320k gate.
```

Failure interpretation:

```text
If team_disc_acc stays flat and Z usage is low, the issue is likely credit
triangle/sample efficiency or broken discriminator input, not proof that the
recognition substrate alone is enough.
```

Prediction 2: discriminator health is not sufficient.

```text
If team_disc_acc is healthy but reward, coverage, throughput, or zero-service
metrics do not improve, the bound is likely missing cross-layer usefulness or
has scale/double-count issues.
```

Failure interpretation:

```text
Inspect reward ratios, Z-boundary counts, z advantage variance, and whether the
team reward is being paid at the wrong clock.  Do not add another residual term
before this audit.
```

Prediction 3: collapse is a clock/credit failure first.

```text
If Z collapses or has too few effective samples, treat it as a
credit-triangle/sample-efficiency failure.  It is not by itself evidence that
OPT recognition or R19 transition residuals should replace sampled team intent.
```

Failure interpretation:

```text
First check K_team, boundary truncation, Z entropy, z renewal counts, and
stored log-prob accounting.  Only then consider target-entropy or cross-layer
terms.
```

Prediction 4: R19 should dissociate recognition from commitment.

```text
If R19 transition residual remains negative while R21 improves Z/task behavior,
that supports the commitment-specific hypothesis.  If R19 improves and R21
does not, revisit whether the team commitment clock is mis-specified or whether
the relevant signal is situation transition rather than held commitment.
```

## 9. What Must NOT Be Implemented Before Review

Do not implement any of the following before this note is reviewed against the
R21/HMASD read plan:

```text
1. No new intrinsic reward term from the optional cross-layer I(Z ; ...).

2. No automatic target-entropy temperature or new entropy floor claimed as a
   principled mechanism.  R22-4 must specify the target-entropy design first.

3. No expansion of R12 situation hazard, SEF/DADS reward, or target kappa*
   before R21/HMASD reads identify that failure mode.

4. No broad R19 coefficient sweep unless complete reward-on evidence overturns
   the current mechanism-negative transition-residual read.

5. No revival of g/team bridge or new mechanism conditioned on g.

6. No use of raw topology, communication, coverage, backhaul, or recovery
   metrics as intrinsic rewards.  They remain diagnostics unless already part
   of the external environment reward.

7. No claim that R21/v6 is validated from discriminator accuracy alone.
   Team_disc_acc is a mechanism signal; S7-S1 parity still needs task metrics.

8. No promotion of this sketch to a formal theorem or paper claim without
   ablations showing that team, individual, entropy, and optional cross-layer
   terms each add non-duplicated value.
```

Review checklist before implementation:

```text
double-count audit accepted
leak audit specified for q_D and q_d
clock accounting verified for Z boundaries and z_i renewals
diagnostics present for reward ratios and sample counts
R21 and HMASD baseline reads preserved as the immediate experiment track
```
