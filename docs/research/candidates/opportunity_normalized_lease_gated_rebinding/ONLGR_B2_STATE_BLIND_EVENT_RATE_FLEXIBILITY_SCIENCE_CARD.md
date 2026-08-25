# ONLGR-B2 state-blind event-rate flexibility science card

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Candidate: `ONLGR-B2-STATE-BLIND-EVENT-RATE-FLEXIBILITY`  
Revision: `ONLGR-B2-SCIENCE-20260814-02`  
Classification: prospective single-axis variable-`k` rate-family discriminator  
Scientific activity started: `false`  

## Conclusion and purpose

ONLGR-B2 asks the one question left open by the completed r04 result: does a
task-content-blind event rate need to depend on observed timing, tenure, and
own-action state, or is one learned global rate sufficient?

The experiment contains exactly two learned arms:

```text
RATE-FLEX:  lambda = softplus(g_theta(z_timing))
RATE-CONST: lambda = softplus(g_theta(0)) = softplus(g0)
```

Both convert the rate to the same boundary event probability
`u=1-exp(-lambda*e)`, use the same fixed conditional mark probability
`rho=0.5`, and otherwise share the complete host, lease, action, safety,
training, optimizer, work, and IID evaluation contract. The sole treatment
axis is whether the event head sees `z_timing` or an equal-shaped all-zero
placeholder. This is not a renewed ONLGR-versus-RAW link test.

The sole claim-bearing contrast is

```text
R_IID_RATE-FLEX - R_IID_RATE-CONST.
```

Passage retains only the task-content-blind timing-dependent rate family for
future study. Statistical nonpassage absorbs the direction into the simpler
global-rate family under the portfolio-authorized decision rule. Neither
branch restores an eligible-exposure-normalization, task-content, lease,
`REBIND`, hazard, within-resource-cap, arbitrary-`k`, or UAV claim.

## Provenance and isolation

The completed r04 result supplies only the prospective question and claim
warning:

- ONLGR and its task-content-blind TIMING-ONLY ablation were indistinguishable
  on IID return and service;
- a validation-selected state-blind fixed-rate policy was descriptively
  sufficient or stronger;
- the r04 operational partition estimand had no common unsplit-activity
  support; and
- r04 exceeded its registered cumulative resource condition.

No r04 checkpoint, learned parameter, trajectory, panel row, threshold repair,
or observed numerical value enters B2. B2 uses fresh seeds and namespaces and
trains both arms from initialization. The r04 content-conditioned parent is
complete and receives no current investment. It is not rerun, modified, or
used as a B2 comparator.

The exact unchanged host, physical reward, callback, lease, safety, action,
identity, and SMDP-GAE definitions are inherited from the corresponding
sections of `ONLGR_VARIABLE_K_SCIENCE_CARD.md`, with only the explicit B2
deltas below. The final r04 mathematical-closure overlay remains provenance,
not authority to change B2. Every fact needed for B2 is restated or explicitly
bound here.

## Scientific question

For one parameter-shared policy trained once over external callback periods
`k in {8,24}` and both midpoint switches, does allowing its task-content-blind
event rate to depend on current timing/tenure/own-action-state coordinates
improve mean return on a held-out IID future-`k` process over a matched policy
whose event rate is one learned global constant?

The question is about rate flexibility under unpredictable next-interval
timing. Because both arms use the same eligible-exposure boundary link, a
positive result cannot identify or validate that link against another link.

## Exact inherited host

Every episode has `H=256` primitive ticks and two fixed agents, tracker `T`
and relay `R`. A binary mission mode starts fair and flips at each physical
tick under a counter-keyed probability `1/48`. Each agent has a binary active
binding, plan age capped at 64, busy counter, and 12-tick physical lease.
Initial bindings are fair and paired; initial ages are balanced over
`{0,8,16,24}`; busy counters are zero; and the lease is initially expired with
the same virtual boundary at tick `-8` used by r04.

Each physical tick supplies a local sensor bit equal to the mission mode XOR
Bernoulli noise `0.15`. The local mismatch cue is the fraction of the last
eight fixed-tick sensor bits disagreeing with the active binding. The sensor
window exists independently of callbacks. Each agent broadcasts its binding
and thresholded mismatch bit every physical tick, exactly as in r04, although
neither B2 actor receives those task-content values.

After boundary action processing, service and reward are exactly:

```text
service_t = 1[b_T=z_t, b_R=z_t, d_T=0, d_R=0]
            * max(0, 1-(a_T+a_R)/128)
r_t = service_t - 0.02*n_refresh_t - 0.04*n_rebind_t
J = (sum_t r_t)/256.
```

At tick end, positive busy counters decrement and plan ages advance by one,
capped at 64. Mode, sensors, initialization, action uniforms, and interval
draws use counter-keyed namespaces paired across the two B2 arms before either
arm acts. Trajectories become arm-local after actions diverge.

## Actions, lease, exposure, and safety

At a routine boundary, simultaneous per-agent actions are sampled from one
parameter-shared actor:

- `KEEP` preserves binding, plan, busy state, and lease;
- `REFRESH-SAME` retains the binding, resets plan age, costs `0.02`, occupies
  the current service tick, and starts a 12-tick lease; and
- `REBIND` flips the binary binding, resets plan age, costs `0.04`, occupies
  the current and next service ticks, and starts the same lease.

Before lease expiry, both voluntary non-`KEEP` marks are masked and `KEEP` is
deterministic. At and after expiry, both marks are legal. The mask is applied
before sampling. A masked routine callback performs the same actor-sized dummy
forward in both arms but contributes no actor score.

For the previous actual routine or safety boundary `b_prev`, use the same
right-closed integer-slot convention:

```text
delta_t = t-b_prev
I(t) = {b_prev+1,...,t}
e(t) = count{u in I(t): u >= lease_expiry}.
```

The tick-zero virtual boundary gives `delta=e=8`. Terminal residual intervals
retain reward but create no action, likelihood, or exposure reset. After every
actual routine opportunity, including `KEEP`, the next interval begins at that
boundary. This is a discrete eligible-exposure offset, not a literal hazard.

The claim-bearing IID panel has no safety event. A separate safety-conformance
panel uses the same IID interval law and exactly one counter-keyed event per
episode, balanced over agents and ticks `32..223`. It forces same-tick `REBIND`
on true mismatch and otherwise same-tick `REFRESH-SAME`, bypasses the lease,
pays the ordinary cost, resets only the affected agent's lease and boundary
origin, and has no policy score. Safety takes precedence over a coincident
routine callback; the unaffected agent receives no forced action and its
boundary/exposure clock is not advanced. Safety never terminates or clears
the SMDP return or GAE recursion.

Every record preserves immutable identity
`(episode_id,agent_role,owner_epoch,own_boundary_index,behavior_version)`.
Prospective causes are only `ROUTINE_CALLBACK` and `SAFETY_BYPASS`; realized
post-action endings are never actor inputs.

## Training and held-out interval processes

Training uses exactly four equally represented exogenous tapes:

```text
CONST-8
CONST-24
MID-8-TO-24
MID-24-TO-8
```

Boundaries start at tick zero. Segment endpoints and terminal censoring follow
the r04 host exactly. Training contains no safety event. A schedule name,
absolute time, boundary count, interval history, next interval, switch phase,
or future `k` is never an actor input.

The sole claim-bearing evaluation process is `RAND-IID-4-16-32`. In this
no-safety panel, at tick zero and after every subsequent routine joint action,
the evaluator draws the next interval independently and uniformly from
`{4,16,32}`. The draw occurs after the current action and is counter-keyed only by
`(B2 seed,episode_index,routine_boundary_index)`. It is independent of the
complete actor-visible history, current action, state, reward, and all prior
intervals. It is paired across arms. An interval crossing `H` is terminally
censored and creates no terminal policy decision.

`RAND_IID_NEXT_K` uses one global exogenous routine-draw ordinal, distinct from
every per-agent `own_boundary_index`. Emit exactly one next-`k` draw after
processing every scheduled routine boundary. If safety coincides with that
boundary, first execute the single forced safety transition and suppress the
routine policy action, then emit the next-`k` draw and advance the global
routine-draw ordinal exactly once. An off-grid safety boundary does not emit a
next-`k` draw and does not advance that ordinal. Terminal censoring remains
unchanged. This rule affects only the declared safety-conformance panel because
training and claim-bearing IID evaluation contain no safety event.

No deterministic seven-schedule learned-arm evaluation, `P`, `W`, r04
partition probe, RAW arm, content-conditioned arm, validation-selected fixed
rate, clamp, oracle, degenerate-policy, yoke, or UAV panel is part of B2. Their
absence is prospective and cannot be repaired after observing B2.

## Actor inputs and exact treatment axis

Define the seven-dimensional task-content-blind vector:

```text
z_timing = [
  clipped plan age / 64,
  clipped physical lease remaining / 12,
  busy counter / 2,
  1[cause=ROUTINE_CALLBACK],
  1[cause=SAFETY_BYPASS],
  clipped realized preceding delta_t / 32,
  clipped legally eligible exposure e / 32
].
```

Both actors exclude role, active binding, local mismatch, partner binding,
partner mismatch, mission mode, reward, schedule identity, absolute time,
callback count, interval history, next interval, future `k`, seed, environment
ID, and recurrent state.

Both arms use an identical parameter-shared `(32,32)` tanh event network with
one scalar output and the same parameter tensors:

- `RATE-FLEX` receives the realized `z_timing` above;
- `RATE-CONST` receives an equal-shaped vector of seven exact zeros at every
  real, masked, dummy, and safety boundary.

`RATE-CONST` therefore has a global learned scalar rate as a function, even
though it retains the same redundant event-network parameter slots, forward
calls, backward graph, optimizer state, and update count. All parameters remain
in the same optimizer; zero input makes its input weights receive exact zero
data gradient without removing or replacing them. No parameter slot is added,
removed, frozen, or specially regularized by arm.

Both arms still use the live legal exposure `e` outside the event head in the
common probability law. Thus `RATE-CONST` has constant `lambda`, not constant
boundary probability: its `u` changes with eligible exposure through the same
exponential link.

## Initialization and action law

All event-network parameters are paired bit-for-bit across arms at
initialization. Hidden-layer parameters use the same paired draws. The final
event-output weights are initialized to exact zero in both arms, so every
observation initially produces the same scalar output. Set the shared output
bias analytically using

```text
lambda_ref = -log(0.8)/8
g_ref = softplus_inverse(lambda_ref)
```

so every legal row with `e=8` has initial event probability `u=0.20`. Because
the output weights start at zero, the complete initial probability curve is
identical between arms for every observation and exposure. Report the initial
curve at `e in {1,4,8,16,24,32}`. The output weights may learn from the first
update; hidden layers acquire gradient once the output path becomes nonzero.
This short common learning geometry is part of both arms and is not repaired
by arm-specific warm-up.

For legal `e>0` rows:

```text
lambda = softplus(g)
u = 1-exp(-lambda*e)
rho = 0.5 exactly

Pr(KEEP)         = 1-u
Pr(REFRESH-SAME) = 0.5*u
Pr(REBIND)       = 0.5*u.
```

For `e=0`, action is deterministically `KEEP`. The fixed mark has no learned
parameter, calibration, or arm-specific random source. Paired counter-keyed
event and mark uniforms are used across arms. Numerically stable `expm1` and
`log1p` realizations must preserve the equations. Float64 probability and full
Jacobian conformance is required to absolute tolerance `1e-10`.

The full categorical log likelihood is:

```text
log pi(KEEP)         = log(1-u)
log pi(REFRESH-SAME) = log(u)-log(2)
log pi(REBIND)       = log(u)-log(2).
```

Per-agent scores sum into one joint score and one PPO ratio clipped once.
Masked, dummy, and forced actions have no actor score. The fixed `-log(2)` mark
term has zero gradient. Diagnostic marked entropy is
`H_Bernoulli(u)+u*log(2)` and never enters optimization.

## Critic, credit, optimizer, and work matching

Both arms use the same separate `(64,64)` tanh centralized team critic. In both
arms it sees the current complete physical state and both agents' realized
`z_timing` vectors; RATE-CONST's actor-side zeroing is not applied to either
critic. The critic sees no future interval or schedule label. Critic
architecture, inputs, initialization, targets, optimizer, and calls are paired
across arms, so the treatment axis exists only at the event actor input.

Credit is the same ordinary physical-time SMDP-GAE as r04:

```text
gamma_tick = 0.99^(1/8)
lambda_tick = 0.95^(1/8)
R_j = sum_h gamma_tick^h * r_(t_j+h)
Gamma_j = gamma_tick^Delta_j
Lambda_j = lambda_tick^Delta_j
delta_j = R_j + Gamma_j*V(s_(j+1)) - V(s_j)
A_j = delta_j + Gamma_j*Lambda_j*A_(j+1).
```

Before PPO epoch one, cache every rollout joint behavior log probability and
the behavior critic `V^-`. Set `V^-(s_H)=0` and `A^-_K=0`. Compute once,
backward over the actual SMDP boundaries,

```text
delta^-_j = R_j + Gamma_j*V^-(s_(j+1)) - V^-(s_j)
A^-_j = delta^-_j + Gamma_j*Lambda_j*A^-_(j+1)
G^lambda_j = stopgrad(V^-(s_j)+A^-_j).
```

Cache `A^-` and `G^lambda` unchanged for all four PPO epochs. For every genuine
stochastic joint row use

```text
omega_j = exp(log_pi_theta(a_j|s_j)-log_pi_behavior(a_j|s_j)).
```

The actor uses cached `A^-_j`. For each training episode, the critic-boundary
set contains every actual routine boundary, including lease-masked routine
boundaries, and excludes terminal `H`; no dummy or deterministic factor resets
the recursion. The critic target is cached `G^lambda_j`, detached from both
actor and critic graphs. Apply value coefficient `0.5` exactly once. Value
clipping is prohibited. These behavior-frozen targets are part of B2 itself;
they do not silently import any other r04 overlay provision.

Every update has eight complete episodes from each training tape. The actor
objective is the same schedule- and episode-balanced sum of genuine joint PPO
terms with common `1/256` scale. It has no physical-duration weights, row
means, pooled-row mean, or advantage normalization. The critic averages value
errors within episode and gives episodes/schedules equal outer weight. Safety
and dummy boundaries do not break GAE.

Both arms use PPO clip `0.20`, Adam learning rate `3e-4`, value coefficient
`0.5`, entropy coefficient `0`, gradient-norm cap `1.0`, four full-batch epochs
and Adam steps per update, and 32 complete episodes per update. There are eight
updates and exactly 256 training episodes per arm/seed, 64 from each training
tape. The final state after update eight is the sole checkpoint. There is no
early stop, sweep, rescue, per-`k` checkpoint, warm-up, calibration, threshold
repair, or held-out checkpoint selection.

Actor and critic tensor shapes, parameter count, initialization namespaces,
batch order, complete episodes, physics ticks, schedules, calls, messages,
bits, optimizer tensors, PPO epochs, and optimizer steps are matched. Runtime
rebinding never resets the optimizer.

## Fresh coordinates and exact panels

Use exactly eight fresh analysis seeds:

```text
[137,149,163,181,199,223,239,257]
```

These seeds and all B2 namespaces are disjoint from r04. Within each seed:

- training uses 64 episode indices per each of the four training tapes;
- claim-bearing IID evaluation uses 32 paired no-safety episodes per arm;
- IID safety conformance uses 16 paired episodes per arm; and
- an IID action-forced-KEEP equality replay uses 16 paired episodes per arm.

The exact trajectory ledger is:

```text
training:          2 arms * 8 seeds * 256 episodes * 256 ticks = 1,048,576
IID evaluation:   2 arms * 8 seeds *  32 episodes * 256 ticks =   131,072
IID safety:       2 arms * 8 seeds *  16 episodes * 256 ticks =    65,536
IID KEEP replay:  2 arms * 8 seeds *  16 episodes * 256 ticks =    65,536
total trajectory work                                            1,310,720
```

This exact count is a treatment/work-matching fact, not a within-resource-cap
claim. Wall time, RSS, and resource slicing are reported descriptively and
have no scientific stop authority. A slice may pause execution but must retain
a blinded, atomic, same-coordinate frontier until the complete package exists.

## Claim-bearing estimand and decision rule

For seed `s` and arm `a`, define

```text
R_IID[s,a] = mean normalized return over its 32 RAND-IID-4-16-32 episodes
Delta[s] = R_IID[s,RATE-FLEX] - R_IID[s,RATE-CONST].
```

Use the eight seed-level paired differences. Report their mean and ordinary
two-sided Student-t 95% interval. The sole positive gate is:

```text
mean_s Delta[s] >= 0.02
AND paired two-sided 95% lower confidence bound > 0.
```

Always report the point estimate, interval, exact paired sign-flip p-value,
and leave-one-seed-out point estimates. The p-value and leave-one-out values
are non-gating. No other return, safety, behavior, rate-dispersion, resource,
training-tape, or per-episode statistic can trigger retention.

Define `PACKAGE_VALID` as completion and conformance of every mandatory
checkpoint, panel, coordinate, probability, filtration, learning-target, work,
and safety requirement. Define `MARK_SUPPORT_OK` as passage of the frozen
post-startup `64/4/4/4` rule for both arms in every seed-level IID cell.

```text
RETAIN_RATE_FLEX =
  PACKAGE_VALID
  AND MARK_SUPPORT_OK
  AND mean_s Delta[s] >= 0.02
  AND paired two-sided 95% lower confidence bound > 0.

ABSORB_TO_GLOBAL_RATE =
  PACKAGE_VALID
  AND MARK_SUPPORT_OK
  AND NOT(
      mean_s Delta[s] >= 0.02
      AND paired two-sided 95% lower confidence bound > 0
  ).
```

If `RETAIN_RATE_FLEX=true`, retain only the task-content-blind timing-dependent
event-rate family for further scientific study. This is not evidence for
content use, the exposure link versus another link, or a UAV successor.

If `ABSORB_TO_GLOBAL_RATE=true`, select the simpler global-rate family under
the portfolio-frozen action. Statistical nonpassage establishes only that this
frozen experiment did not demonstrate the registered material advantage of
RATE-FLEX. The selection is not an equivalence, noninferiority,
representational-sufficiency, general no-benefit, or harm claim.

If `PACKAGE_VALID=false`, neither scientific branch activates and the package
returns to CM for unchanged-science completion. If `PACKAGE_VALID=true` but
`MARK_SUPPORT_OK=false`, report `INCONCLUSIVE_INSUFFICIENT_VOLUNTARY_SUPPORT`;
neither retention nor absorption activates, and no threshold or support rule
may be changed after observing the result. A mixed-revision or preactivity-only
package also activates neither branch.

## Activity, support, completeness, and required reports

Question-relevant scientific activity begins at the earliest of:

- retention, inspection, or use of any B2 learned-arm task trajectory, action,
  reward, service, cost, rate, value, support count, or statistic intended for
  or capable of informing a required B2 panel or scientific revision; or
- retention of any actor-parameter, critic-parameter, or optimizer-state update
  using a B2 task transition.

A purely analytic probability/Jacobian calculation or a discarded contract dry
run remains preactivity only when no learned state, task trajectory, task
statistic, or outcome is retained or used to revise the science. After activity
begins, no arm, feature, initialization, seed, tape, count, threshold, analyzer,
learning target, or decision branch may be changed.

For every seed's claim-bearing IID cell, each arm must contain at least 64
post-startup agent-level routine rows satisfying

```text
initial_anchor_action=false AND both voluntary marks legal
```

and at least four stochastic `KEEP`, four voluntary `REFRESH-SAME`, and four
voluntary `REBIND` actions on those rows. Initial-anchor, masked, forced,
dummy, and terminal rows do not count. Failure preserves a numerical return
but makes the rate-flexibility comparison non-identified through insufficient
voluntary action support; it does not become statistical nonpassage.

A complete package requires both final checkpoints for every seed, all 32 IID
episodes per seed/arm, the full safety and KEEP panels, exact training and work
counts, probability/Jacobian conformance, IID draw filtration, reward/service/
cost decomposition, activity/support facts, and all required diagnostics under
one revision. No partial-result selection or exposure is allowed.

Required reports include:

- every seed/arm `R_IID`, service, explicit action cost, and within-cell episode
  uncertainty;
- the paired contrast, interval, sign-flip result, and leave-one-out values;
- learned `lambda` and event-probability distributions by exposure, plan age,
  busy state, preceding interval, role for reporting only, and seed;
- RATE-CONST equality of `lambda` across all actor rows and RATE-FLEX rate
  dispersion on the exact zero-trajectory diagnostic grid
  `plan_age in {0,16,32,64}` crossed with
  `(delta,e) in {(4,4),(8,8),(16,16),(24,24),(32,32)}`, with lease remaining
  `0`, busy `0`, cause `ROUTINE_CALLBACK`, and every omitted actor coordinate
  fixed zero; report all 20 lambdas, their range and standard deviation for
  both arms and every final checkpoint, with no gate or cell selection;
- post-startup legal rows, all three voluntary actions, masks, eligible
  exposure, event-free survival, dwell, stale-binding, plan-age, service,
  downtime, and action-cost facts;
- exact IID interval-draw counts and proof that every draw occurs after the
  current action independently of visible history;
- safety response, affected/unaffected action, coincident-boundary clock
  behavior, violations, and forced-action score exclusion;
- KEEP replay equality for physics, sensor, state, reward, interval, and dummy-
  call ledgers;
- actor/critic calls, parameters, episodes, ticks, messages, bits, PPO work,
  optimizer steps, latency, RSS, wall time, and slice/frontier facts; and
- anomalies, missing facts, and the exact strongest remaining alternative.

## Strongest alternative explanation

If RATE-FLEX passes, the strongest alternative is generic finite-budget
functional flexibility or optimization geometry in the larger effective
input-dependent function class, combined with this host's reward/lease/callback
geometry. A pass cannot localize value to `delta`, `e`, age, busy state, or
cause, and cannot prove that the learned variation is an ontologically correct
time process. The matched initialization eliminates r04's initial operating-
point gap but not the intentional function-class difference.

If the gate does not pass with `PACKAGE_VALID=true` and
`MARK_SUPPORT_OK=true`, the frozen experiment did not demonstrate the
registered material advantage of RATE-FLEX. The portfolio-frozen selection of
the global-rate family is a simplicity action attached to that evidence, not a
proof that the global rate is sufficient. More seeds on the same frozen
contrast would not repair a missed materiality rule.

## Claim ceiling

The strongest possible B2 claim is:

> On this registered constructed two-agent host, with both task-content-blind
> arms using the same eligible-exposure probability law, fixed 50/50 mark split,
> lease, action surface, safety semantics, initialization, PPO work, and fresh
> IID future-interval panel, allowing the event rate to depend on the registered
> timing/tenure/own-action-state vector improved mean IID normalized return over
> one learned global event rate under the frozen finite training budget.

B2 cannot establish eligible-exposure normalization against another link,
task-content use, causal value of any individual timing coordinate, lease or
`REBIND` causality, literal hazard semantics, representational impossibility,
within-resource-cap success, deterministic-schedule robustness, arbitrary or
continuous `k`, variable `N`, UAV causality or transfer, learned safety, or
general algorithm superiority. A nonpassing result is equally local.

## Production and result-convergence boundary

Before activity, the exact complete revision must receive `CLOSED` from the
existing ONLGR ChatGPT Pro conversation and same-direction EM intake. No new
provider identity is authorized. Pro closure does not authorize construction,
technical acceptance, resource allocation, or production.

After CM returns one technically accepted complete result directly to this EM,
the EM performs preliminary intake and sends exactly one result-convergence
request in that same Pro conversation. No result sign may skip or duplicate
that request. CM owns code, tests, environment, execution, unchanged-science
repair, and technical acceptance. Root owns compute scheduling, Git, user
contact, and portfolio relay.

## Exact same-conversation Pro mathematical-closure request

Review this complete revision as one indivisible prospective scientific object.
Check whether the two arms differ only through actor access to `z_timing`;
whether RATE-CONST is a valid learned global-rate comparator under matched
parameter slots, initialization and PPO work; whether the fixed mark law,
likelihood, fresh coordinates, IID filtration, support/completeness rules,
decision branches, strongest alternative, and claim ceiling are mathematically
and causally coherent; and whether any stated conclusion exceeds the sole
registered contrast.

Return exactly one leading disposition:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

If `CLOSED`, state that there is no science-bearing defect and restate the
maximum claim in one bounded paragraph. If `REVISION_REQUIRED`, enumerate every
exact mathematical or causal defect, the smallest required correction, and the
claim boundary until corrected. Do not review code, tests, runtime mechanics,
hashes, receipts, or implementation acceptance.
