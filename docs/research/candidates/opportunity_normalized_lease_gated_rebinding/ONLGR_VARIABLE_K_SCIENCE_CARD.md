# Opportunity-Normalized Lease-Gated Rebinding B1 science card

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager
Candidate: `CAND-OPPORTUNITY-NORMALIZED-LEASE-GATED-REBINDING`
Treatment: `ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1`

## Conclusion and scientific revision

ONLGR is scientifically viable as a direct variable-`k` algorithm candidate
after one important revision to the seed. It is a **marked lease-censored event
policy** rather than a flat three-action softmax: one head determines whether a
voluntary intervention occurs, and a conditional mark head chooses
`REFRESH-SAME` or `REBIND`. The treatment converts its event output to a
boundary probability with a discrete physical-time exposure offset; the primary
matched learner uses a raw per-opportunity probability. This is a boundary
policy link, not an identified literal continuous-time hazard. Both use
ordinary team SMDP-GAE only.

The experiment does not pretend that the raw learner is representationally
incapable. Both learned arms receive the same realized preceding interval and
the same legally eligible exposure. A sufficiently learned raw head can emulate
the rate transform. Therefore a positive primary contrast supports a useful
physical-time-link **inductive bias under the frozen training and held-out
schedules**, not a function-class impossibility theorem. The proposed
probability-exponent expression is exactly the same policy and gradient map as
ONLGR because `-log(1-sigmoid(g))=softplus(g)`. It is therefore retained only
as an analytic identity/conformance check, not trained as a third mechanism.
The third learned arm is instead a timing-only ONLGR ablation that removes task
cues while retaining elapsed, lease, age, busy, cause, role, capacity, and work.

The named schedule cells are evaluator groupings, not explicit actor inputs.
The actor receives legitimate elapsed-time information but no schedule label,
absolute time, callback count, interval history, future `k`, or switch phase.
It is feed-forward. A switch-decision twin proves only same-boundary
nonanticipation; it cannot stop the realized interval from revealing a
deterministic constant or alternating schedule and thereby predicting a later
interval. B1 therefore includes a separate unchanged-checkpoint IID future-`k`
audit in which every next interval is drawn only after the current action and
independently of the complete visible history. Deterministic-panel performance
and schedule-identity-free exposure adaptation have separate claim ceilings.

## Provenance boundary

The candidate reuses only prospective primitives:

- VSP02 motivates immutable owner/behavior/own-boundary identity and explicit
  causal ending codes. Its finite lifecycle and value results do not transfer.
- VSP04 motivates an explicit `KEEP / REFRESH-SAME / REBIND` boundary action
  surface and the warning that a declared legal-boundary table is not a
  generated world. Its certificate does not transfer.
- VSP07/UCOPE motivates scoring unequal opportunities in physical time and an
  exact opportunity-normalized negative boundary. Its host, counts, numerical
  values, thresholds, and conclusions do not transfer.
- VSP08 contributes only the prospective physical-time lease idea. This card
  defines its own lease and safety semantics rather than inferring them from a
  historical name.
- EGRCR contributes only the warning that dense association-specific credit
  rebinding can be redundant with ordinary GAE. No EGRCR result magnitude,
  threshold, acceptance, claim, or authority enters ONLGR. ONLGR therefore has
  no relay label, credit reassignment, escrow, or binding cut in training.

## Scientific question and causal object

Can one parameter-shared policy trained once across external callback periods
`k in {8,24}` and both midpoint switches improve either held-out mean task
return or worst-schedule return over a capacity-, input-, action-, lease-,
optimizer-, work-, and ordinary-GAE-matched raw per-opportunity learner when
evaluated unchanged on:

- constant `k in {4,16,32}`;
- midpoint switches `4 -> 32` and `32 -> 4`; and
- 64-tick alternation starting with `4` or with `32`?

The primary treatment contrast is `ONLGR - RAW-BOUNDARY-LEASE`. The proposed
mechanism is that a physical-time probability link reduces excess short-grid
interventions and long-grid underreaction. This mechanism is supported only if
the return contrast accompanies better event-survival stability under an
equal-time partition probe. The direct algorithm claim and the finer mechanism
claim are reported separately.

## Constructed two-agent host

### Physical process

Every episode contains exactly `H=256` primitive physics ticks and two fixed
roles, tracker `T` and relay `R`. The environment owns one binary mission mode
`z_t`. Its initial value is fair. At the start of each primitive tick it flips
when a counter-keyed uniform is below `1/48`. Mode draws are indexed only by
episode seed and physical tick, are independent of the callback schedule and
all actions, and are paired across arms and controls.

Agent `i` has an active binary tactic/binding `b_i`, a plan age `a_i`, a busy
counter `d_i`, and a physical lease expiry `ell_i`. Initial bindings are fair
and paired; initial plan ages are balanced over `{0,8,16,24}`; `d_i=0`; and
the initial lease is expired with `ell_i=-8`. A common virtual risk boundary at tick `-8`
makes `delta_t=e_i=8` at the tick-zero decision in every schedule. The eight
pre-roll sensor bits use the tick-zero mode without pre-roll mode changes and
do not contribute reward or training transitions. Every primitive tick
produces a local sensor bit

```text
y_i(t) = z_t XOR Bernoulli(0.15).
```

The actor's local mismatch statistic is the fraction of the last eight fixed
physics-tick sensor bits that disagree with `b_i`. The eight-tick window exists
independently of callbacks, so a finer
callback grid never supplies more physical evidence per observation. Each
agent broadcasts its current binding and thresholded mismatch bit every
primitive tick. Every arm therefore transmits exactly four team bits per
physics tick.

After any boundary action on tick `t`, service on that tick is

```text
h_i(t) = max(0, 1 - a_i(t)/64)
service_t = 1[b_T=z_t, b_R=z_t, d_T=0, d_R=0]
            * max(0, 1 - (a_T+a_R)/128)
r_t = service_t - 0.02*n_refresh_t - 0.04*n_rebind_t.
```

The reported episode return is `J=(sum_t r_t)/256`. At tick end, positive busy
counters decrement and plan ages advance by one, capped at 64. The reward and
mode are centralized training/evaluation facts and are not actor inputs.

This surface contains both sides of the cadence tradeoff. Holding a wrong
binding or an old plan loses service in physical time. Refreshing or rebinding
causes immediate cost and task downtime, so gratuitous short-grid intervention
also loses return.

### External callback schedules

A schedule is an exogenous interval tape. Boundaries begin at tick zero and at
the cumulative interval endpoints below `H`; a terminal residual interval is
kept even when `k` does not divide 256. Segment endpoints at ticks 64, 128, and
192 are boundaries. Within a segment, the last interval is truncated to land
exactly on its endpoint. All such boundaries use the single prospective cause
`ROUTINE_CALLBACK`; neither a constant/switch/alternate label nor a segment
boundary flag is exposed.

Training uses exactly four equally represented tapes:

```text
CONST-8
CONST-24
MID-8-TO-24   (switch after tick 127)
MID-24-TO-8   (switch after tick 127)
```

Held-out conclusion tapes are:

```text
CONST-4
CONST-16
CONST-32
MID-4-TO-32
MID-32-TO-4
ALT-4-32-4-32       (change every 64 ticks)
ALT-32-4-32-4       (change every 64 ticks)
```

One additional held-out leakage audit, `RAND-IID-4-16-32`, is not included in
the seven-cell primary `P` or `W`. It uses the unchanged final checkpoint. At
tick zero and after every subsequent routine joint action, the evaluator draws
the next interval independently and uniformly from `{4,16,32}` with a counter
keyed only by `(seed,episode_index,routine_boundary_index)`. The draw occurs
after the action and is independent of the complete actor-visible history,
current action, state, reward, and prior intervals. It is paired across arms.
An interval crossing `H` is terminally censored at `H` and creates no terminal
policy decision. Each learned arm receives 32 episodes per seed in this audit.

The realized `delta_t` at a boundary is the number of primitive ticks since
the preceding routine or safety boundary. It is backward-looking. The next
interval is selected by the exogenous tape after the current action and is not
observable. Direction-reversed switch and alternation tapes are equally
weighted. The switch-decision twin supplies an exact same-boundary
nonanticipation check. Only `RAND-IID-4-16-32` makes the next interval
independent of the visible history; deterministic cells may reveal their own
future cadence through the realized preceding interval.

### Action meanings

At a routine boundary the joint action is sampled simultaneously and
factorizes by agent from one parameter-shared actor:

- `KEEP`: preserve binding, plan, busy state, and lease.
- `REFRESH-SAME`: retain `b_i`, reconstruct the low-level plan from the current
  fixed eight-tick sensor window, set `a_i=0`, set `d_i=1` for the current
  service tick, and start a new 12-tick physical lease.
- `REBIND`: set `b_i=1-b_i`, reconstruct the plan from the same current window,
  set `a_i=0`, set `d_i=2` for the current and next service ticks, and start the
  same 12-tick physical lease.

There is no target search, escrow, delayed request, partner credit, or hidden
coordinator. In this binary host `REBIND` has one legal target, so target
selection cannot differ across treatments. The partner communication and
simultaneous-action rule are identical in all arms.

### Lease, eligible exposure, and safety bypass

An executed `REFRESH-SAME` or `REBIND`, voluntary or forced, sets
`ell_i=t+12`. Before tick `ell_i`, both voluntary non-`KEEP` marks are masked;
`KEEP` is always legal. At and after `ell_i`, both marks are legal. The gate is
applied before sampling in every arm. A masked routine boundary still performs
an actor-sized dummy forward call but contributes no policy log-probability.

Let `b_prev` be the previous actual routine or forced-safety boundary for this
agent. Boundary processing occurs after the tick-`t` mode/sensor update and
before the tick-`t` action/service transition. B1 uses the right-closed integer-
slot convention

```text
delta_t = t-b_prev
I_i(t) = {b_prev+1,...,t}
e_i(t) = count{u in I_i(t) : u >= ell_i}.
```

Thus adjacent intervals are disjoint on the integer lattice, lease-masked slots
never enter the offset, and an endpoint at which the lease first becomes legal
contributes exactly one slot. The initial virtual boundary `-8` yields
`I_i(0)={-7,...,0}` and `delta_t=e_i=8`. A terminal residual ending at `H`
is right-censored: its rewards remain in the preceding SMDP return, but there is
no terminal action, event likelihood, entropy, or exposure reset. If `e_i=0`,
the routine action is deterministically `KEEP`. After every actual routine
opportunity, including `KEEP`, the next interval begins at that boundary. A
safety action resets the affected agent's lease and interval origin. This is a
discrete exposure-offset boundary convention, not a claim that the endpoint
score was a predictable intensity operating throughout the preceding interval.

The primary task and training panels contain no safety event. A separate
safety panel contains exactly one counter-keyed event per episode, balanced
over agents and ticks `32..223`. A safety event creates an immediate off-grid
boundary. If the affected binding differs from current `z_t`, the host forces
`REBIND`; otherwise it forces `REFRESH-SAME`. It bypasses the lease, executes on
that same primitive tick, pays the ordinary action cost, resets only the
affected agent's lease, and has no policy log-probability. When safety and a
routine callback coincide, safety has precedence and there is exactly one
executed action; the routine output is dummy only. The other agent is never
forced. Safety predicates, forced actions, costs, clocks, masks, and reset
semantics are identical in every arm.

The coincident-boundary bookkeeping is per agent and has no implicit second
opportunity. For the affected agent, the single `SAFETY_BYPASS` record advances
`own_boundary_index` once, sets `b_prev=t`, and resets its lease; the suppressed
routine callback creates no second record and no second reset. For the
unaffected agent, the suppressed routine callback creates no action or policy
row, does not advance `own_boundary_index`, does not change `b_prev`, and does
not reset or truncate accumulated eligible exposure. Scheduled actor-sized
dummy calls are still made for both agents and counted, but dummy calls alter no
state or clock. Hence at the next unsuppressed routine callback, `delta_t` and
`e` are measured from the safety boundary for the affected agent and from the
last actual routine-or-safety boundary for the unaffected agent. The same rules
apply in all learned, fixed, degenerate, oracle, native, and safety arms.

“No policy log-probability” means only that the forced current action has zero
actor score. A safety boundary is not an environment terminal: it never resets
the discounted return, critic bootstrap, GAE recursion, or trace. Its action
cost, downtime, state transition, and all later rewards remain available to
credit earlier voluntary actions. The B1 safety tape contains one affected
agent event, so a two-agent simultaneous safety event is outside this card.

Every record carries immutable identity
`(episode_id, agent_role, owner_epoch, own_boundary_index, behavior_version)`.
Prospective input cause is only `ROUTINE_CALLBACK` or `SAFETY_BYPASS`.
Post-action endings are logged as `CONTINUED_KEEP`, `ENDED_REFRESH_SAME`,
`ENDED_REBIND`, `FORCED_SAFETY_REFRESH`, or `FORCED_SAFETY_REBIND`; a realized
ending is never fed into the action that caused it.

## Observations, policy, and probability laws

The feed-forward shared actor receives, for each agent:

1. role one-hot;
2. active binding one-hot;
3. own last-eight mismatch fraction;
4. clipped plan age divided by 64;
5. clipped physical lease remaining divided by 12;
6. busy counter divided by two;
7. partner's latest transmitted binding and mismatch bit;
8. prospective cause one-hot;
9. realized preceding `delta_t/32`, clipped at one; and
10. legally eligible exposure `e_i/32`, clipped at one.

It receives no `z_t`, reward, schedule/cell label, absolute task time, boundary
index, callback count, prior interval sequence, next interval, future `k`,
switch direction, seed, environment ID, or recurrent state. Feature
normalization constants are declared above and never fit separately by
schedule. The centralized training-only critic sees the current full physical
state and both current actor observations, including the same elapsed fields,
but no future interval or schedule label.

All three learned arms use the same two-layer `(32,32)` tanh actor trunk, one
scalar event output, one scalar conditional mark output, the same separate
`(64,64)` tanh team critic, parameter count, and conditional mark law
`rho=Pr(REFRESH-SAME | event)`. The primary pair differs only in its event link:

```text
ONLGR:
  lambda = softplus(g_theta(o, delta_t, e))
  u = 1 - exp(-lambda * e)

RAW-BOUNDARY-LEASE:
  u = sigmoid(g_theta(o, delta_t, e))

for e>0:
  Pr(KEEP)         = 1-u
  Pr(REFRESH-SAME) = u*rho
  Pr(REBIND)       = u*(1-rho)
```

For `e=0`, all arms return `KEEP`. Numerically stable `expm1`/`log1p`
implementations are CM choices that cannot change these equations.

`TIMING-ONLY-ONLGR` is the third learned diagnostic. It uses the ONLGR link,
same parameter dimensions and critic inputs, but replaces the actor's active-
binding one-hot, own mismatch fraction, and both partner-summary bits with
their frozen zero placeholders. It still sees role, plan age, lease remaining,
busy state, prospective cause, realized `delta_t`, and `e`. Thus it can learn a
history-free timing/tenure heuristic with identical action, lease, safety,
optimizer, work, and communication semantics but cannot condition action or
mark on current task mismatch or binding content. It is an intentional input
ablation, not the input-matched primary comparator.

`PROB-EXP-IDENTITY` is analytic only:

```text
q_1 = sigmoid(g)
1-(1-q_1)^e = 1-exp(-softplus(g)*e) exactly.
```

It has no checkpoint, trajectory, optimizer step, or independent result. Its
float64 conformance calculation must agree with ONLGR to absolute tolerance
`1e-10`; a failure is an implementation/formula mismatch, not evidence for a
second mechanism. Because RAW receives the same `delta_t`, `e`, and task inputs
as ONLGR in the same-width head, it can learn the same conditional boundary
probability on this finite observation surface. A RAW loss is not evidence that
RAW lacked information or capacity.

At initialization, output biases are set so a zero-feature, `e=8` routine
opportunity has `u=0.20` in every learned arm and `rho=0.50`. ONLGR and
TIMING-ONLY share the same link bias. Trunk and mark weights use identical
paired draws; the timing-only masked-input coordinates are retained so
parameter count is equal. The corresponding link-specific scalar bias is set
analytically once and is not tuned by arm or schedule. Since one-point action-
space matching does not equalize the complete `u(e)` curve, the initial
probabilities, entropy, and saturation at `e in {1,4,8,16,24,32}` are always
reported. That exposure-dependent initialization/gradient prior is part of the
finite-budget treatment package, not controlled away.

## Ordinary physical-time SMDP-GAE and optimization

There is no dense event credit, association label, auxiliary reward, escrow,
or counterfactual relay. Each actual routine or safety boundary defines one
SMDP segment through the next actual boundary or terminal. With

```text
gamma_tick = 0.99^(1/8)
lambda_tick = 0.95^(1/8),
```

the segment reward, discount, TD residual, and team GAE are

```text
R_j = sum_{h=0}^{Delta_j-1} gamma_tick^h * r_{t_j+h}
Gamma_j = gamma_tick^Delta_j
Lambda_j = lambda_tick^Delta_j
delta_j = R_j + Gamma_j*V(s_{j+1}) - V(s_j)
A_j = delta_j + Gamma_j*Lambda_j*A_{j+1}.
```

At a routine boundary, define one team actor row if at least one agent has
`e_i>0`. Each stochastic agent uses one full categorical likelihood:

```text
log pi_i(KEEP)         = log(1-u_i)
log pi_i(REFRESH-SAME) = log(u_i) + log(rho_i)
log pi_i(REBIND)       = log(u_i) + log(1-rho_i).
```

The joint log-probability is the sum over stochastic agents; deterministic
`e_i=0` agents add no score. The PPO ratio is formed from the complete joint
log-probability and clipped once. Event and mark ratios are never clipped
separately, and the mark score appears only for a sampled non-`KEEP` action.
B1's routine lease mask always enables or disables both non-`KEEP` marks
together, so no selective mark renormalization occurs. Forced and fully masked
actions remain in critic returns but are absent from actor rows. A safety or
dummy boundary does not break the GAE recursion.

Following-duration weights are prohibited. They would count persistence already
present in `A_j` a second time and would weight the current action by a future
interval chosen after that action. Every update contains exactly eight complete
episodes from each of the four training schedules. For schedule `c`, episode
`n`, and its genuine stochastic joint-decision set `D_cn`, the maximized actor
surrogate is exactly

```text
L_actor = (1/4) * sum_c (1/8) * sum_n
            (1/256) * sum_{j in D_cn}
            min(r_j*A_j, clip(r_j,0.8,1.2)*A_j).
```

The `1/256` factor is the same global scale for every episode and arm; the
inner operation is a sum, never a row mean. There is no physical-duration
weight, pooled-row average, or row-count advantage normalization. Advantages
are not normalized. Thus every schedule and episode has fixed outer weight,
while extra genuine decisions remain the score terms of the policy itself.

The separate critic uses the same SMDP targets. Within each episode its squared
value errors are averaged over that episode's actual critic-boundary rows, then
episodes and schedules receive the same `1/8` and `1/4` outer weights. The
critic is never duration-weighted and shares no representation with the actor.

Each learned arm uses PPO with clip `0.20`, Adam learning rate `3e-4`, value
coefficient `0.5`, entropy coefficient exactly `0`, gradient-norm cap `1.0`,
four full-batch epochs and four Adam steps per update, and 32 complete episodes
per update. The marked categorical entropy remains a required diagnostic:

```text
H_marked = H_Bernoulli(u) + u*H_Bernoulli(rho).
```

The factor `u` is the current policy probability, not a sampled-event
indicator. When `e=0`, when the lease masks both non-`KEEP` marks, or when
safety forces an action, diagnostic policy entropy is zero. Report
`H_Bernoulli(u)`, conditional `H_Bernoulli(rho)`, and
`u*H_Bernoulli(rho)` separately, but none enters optimization. Actor, critic,
optimizer tensors, batch order, and random namespaces are paired by seed;
trajectories are arm-local after actions differ. Runtime rebinding never resets
the optimizer.

For each seed and arm, exactly 256 training episodes are used: 64 from each of
the four training tapes. There are eight analysis seeds
`[17,31,47,61,79,97,109,127]`. The final optimizer state after the eighth batch
is the sole checkpoint. It is evaluated unchanged on all held-out schedules;
there is no per-`k` model, early stopping, held-out checkpoint selection,
restart, sweep, rescue, or threshold repair.

## Controls that identify the mechanism

### Exogenous grid-only equality

For paired exogenous tapes, an action-forced `KEEP` replay on every schedule
must produce identical primitive-tick mode, sensor, readiness, plan-age, and
reward trajectories after conditioning on the same initial state. Only the
declared callback/dummy-call ledger may differ. This confirms that changing
`k` changes opportunities and action latency, not physics or evidence rate.

At every midpoint or 64-tick switch, a separate no-learning twin clones the
entire pre-action host and policy state, evaluates the actor once, and only then
branches the next interval to the two possible values. Actor inputs, logits,
probabilities, sampled action under a common uniform, and current reward must be
identical before the branch. Any difference is future-`k` or schedule-phase
leakage and invalidates even deterministic-panel interpretation. Passing the
twin establishes only same-boundary nonanticipation; it does not prove that
visible history cannot predict a later interval. `RAND-IID-4-16-32` is the
separate audit that makes future cadence history-independent while retaining
legitimate backward-looking `delta_t` and `e`.

### Equal-time partition-refinement probe

At each final checkpoint, freeze actor-visible non-time state, cause, and legal
mask in exactly 16 predeclared cells crossing role `{T,R}`,
active binding `{0,1}`, mismatch cue `{0.25,0.75}`, and plan age `{16,32}`.
The remaining actor inputs are fixed to busy `0`, expired lease, partner binding
equal to the focal binding, partner mismatch bit `1[cue>=0.5]`, and cause
`ROUTINE_CALLBACK`. Starting fully lease-eligible, expose the same 32 physical
ticks as partitions `[32]`, `[16,16]`, `[8,8,8,8]`, and eight `4`-tick
intervals. Hold all non-time inputs fixed and use the analytic no-event path.

The first part is a frozen-score algebraic conformance check. Evaluate the
ONLGR checkpoint once at `delta_t=e=32` to obtain `(g*,rho*)`, hold both fixed,
and compose each partition. The ONLGR exponential and
`PROB-EXP-IDENTITY` expressions must give the same no-event, first-refresh, and
first-rebind probabilities for every partition to float64 absolute tolerance
`1e-10`. Failure invalidates the link implementation; it is not an empirical
arm contrast.

The operational part re-evaluates both event and mark heads at every
subboundary with that subinterval's `delta_t=e` while keeping the declared non-
time inputs fixed. For partition `P`, compute

```text
S_a(P) = product_j (1-u_a,j)
R_a(P) = sum_j [product_{l<j}(1-u_a,l)] * u_a,j * rho_a,j
B_a(P) = sum_j [product_{l<j}(1-u_a,l)] * u_a,j * (1-rho_a,j)
TV_a(P,Q) = 0.5*(|S_a(P)-S_a(Q)|
                 +|R_a(P)-R_a(Q)|+|B_a(P)-B_a(Q)|)
MPI_a(seed) = mean_common_cell max_{P,Q} TV_a(P,Q)
HPI_a(seed) = mean_common_cell max_{P,Q}
              |[-log S_a(P)]-[-log S_a(Q)]|.
```

For a seed/cell to enter an ONLGR-versus-RAW stability contrast, every
partition's `1-S` must lie in `[0.05,0.95]` for both arms and the unsplit
`|F_ONLGR-F_RAW|` must be at most `0.05`. This prevents saturation or unequal
one-block activity from manufacturing apparent stability. At least 12 of 16
common valid cells are required in every seed; otherwise the operational
mechanism estimand is unavailable. Always report excluded cells and `HPI`.

This probe uses no task reward and no schedule label. It establishes only
bounded learned marked-composition behavior on these cells. ONLGR operational
stability is material when mean `MPI_ONLGR<=0.02` and its two-sided 95% upper
confidence limit is below `0.03`. Separation from RAW additionally requires
paired mean `MPI_RAW-MPI_ONLGR>=0.02` with its 95% lower limit above zero. If
RAW is equally stable, it learned the same composition. Lower `MPI` without a
qualifying return effect is not task-useful; a return effect without lower
`MPI` supports only the broader finite-budget link package.

### Exposure-clamp diagnostic

This is a closed-loop evaluation intervention, not off-policy observation
replay. For every learned checkpoint, restart the first 16 native no-safety
episode indices in each held-out schedule from their paired initial states and
the same counter-keyed mode, sensor, and action-uniform tapes. Physics, callback
boundaries, current lease masks, action costs, safety semantics, and reward are
unchanged. At each routine boundary where the live native lease state makes both
voluntary marks legal, replace only the actor and critic inputs `delta_t` and
`e` by the common value eight; then sample the live marked action, execute it,
and let the resulting state, observations, actions, and rewards evolve normally.
At masked boundaries, keep the ordinary deterministic-`KEEP`/dummy semantics
and do not override the mask or create a policy row. There is no learning.

Report clamp return and behavior for all three learned arms using the original
seed/schedule/episode identities and paired random namespaces. Clamp returns
are diagnostic and never replace any native primary row. A native ONLGR-over-
RAW advantage that survives in this closed-loop clamped contrast is not
attributable to varying physical exposure alone; disappearance is consistent
with, but does not by itself prove, the exposure-link mechanism.

### State-blind and degenerate controls

`FIXED-RATE-LEASE` has the identical lease, safety path, event link, action
costs, and a state-blind constant rate and mark probability. A single pair
`(lambda,rho)` is selected from
`lambda in {1/64,1/32,1/16,1/8}` and
`rho in {0.25,0.50,0.75}` by highest mean return on two disjoint validation
roots `[1009,1013]` over the four training schedules; ties choose the lower
rate, then the smallest `abs(rho-0.5)`, then the lower `rho`. Equivalently, the
fixed total order within each ascending-rate row is `rho=0.50`, `0.25`, `0.75`.
This order resolves every possible tied subset without held-out information.
The selected pair is fixed for every analysis seed and held-out schedule.
Evaluation also reports `ALWAYS-KEEP`,
`ALWAYS-REFRESH-WHEN-LEGAL`, `ALWAYS-REBIND-WHEN-LEGAL`, and a current-state
oracle that obeys the same lease/safety rules, rebinds on true mismatch, and
otherwise refreshes at plan age 24. These are diagnostic ceilings/nulls, not
resource-matched learned baselines.

### Preselected exact cyclic yoke

Primary evidence is always native, on-policy, and unyoked. This secondary
evaluation-only object is a support-conditioned sensitivity transformation,
not an exogenous mediator intervention and not an explanation of why native
arms differ. It uses only the first 16 original native no-safety episode slots
per seed and held-out schedule.

For each matched ONLGR/RAW pair, collect within each arm the ordered joint
sequence of executed voluntary non-`KEEP` action tuples and complete physical
dwell blocks between them. Let `m` be the number of complete interior blocks.
Pair support requires the two arms to have the same `m>=2`; `m<2` and unequal
`m` remain in the denominator as unsupported.

Index blocks by `i in {0,...,m-1}`. Let `p` be the zero-based seed ordinal,
`c` the zero-based held-out-schedule ordinal in the declared seven-cell order,
and `n in {0,...,15}` the original matched native slot. Never renumber `n`.
Preselect exactly one nonzero cyclic shift before checking legality:

```text
s = 1 + ((17*p + 31*c + n) mod (m-1))
pi: destination slot i receives source block (i+s) mod m.
```

For `m=2`, this is the swap. Use the same one joint-team rotation in both arms;
never rotate agents independently. There is no first-legal fallback. Starting
from the destination initial state and exogenous tape, reconstruct the imposed
ordered joint action schedule and recompute live binding, plan age, busy state,
lease, masks, and legal exposure at every destination tick. Native masks are
not copied onto the transformed path. The preselected rotation is supported
only if all conditions hold in both arms:

1. every reconstructed non-`KEEP` action lands on a pre-existing
   `ROUTINE_CALLBACK` and is legal under the recomputed state and lease;
2. exact joint action count, conditional-mark/tactic multiset, ordered tactic
   sequence, physical inter-event-dwell multiset, per-agent lease-duration
   multiset, routine cause multiset, simultaneity pattern, and total eligible
   exposure summed over ordered interior event slots are unchanged;
3. the 256-tick counts of every joint active-binding tuple `(b_T,b_R)` and each
   agent's binding are exactly equal to native time-weighted occupancy;
4. initial and terminal censored blocks remain fixed at destination ticks; and
5. physics, sensor tape, communication, action costs, and budget remain
   destination-local. Safety episodes are never yoked.

The shift and support predicate may inspect only frozen counter ordinals,
boundary times, causes, action/tactic records, recomputed masks/leases/busy
state, dwell durations, and binding occupancy. They may not inspect mode or
sensor values when choosing the shift, reward, return, advantage, learned
value, policy probability, or any yoked outcome. Report `m`, preselected shift,
support, and exact structural failure reason. An unsupported pair is never
repaired. No second shift, permutation, subset, block reorder, merge/split,
approximate match, or adaptive search is allowed. Complexity is one candidate
and `O(HN)` (`N=2`).

Common support uses all 16 original pairs per seed/schedule as denominator and
requires at least 15/16 supported pairs in every seed/schedule cell. For each
supported arm/pair, let `e^N_{i,r}` and `e^Y_{i,r}` be the eligible exposure
immediately before ordered interior voluntary event slot `r`. Since total
eligible exposure is preserved, define the target-specific reassignment

```text
M_exp = sum_{i,r}|e^Y_{i,r}-e^N_{i,r}|
        / (2*sum_{i,r} e^N_{i,r}).
```

A zero denominator is unsupported. For every arm/schedule, mean `M_exp` across
the eight seed-level common-support means must be at least `0.10` with a two-
sided 95% lower limit above `0.05`. The preselected shift is tested before this
gate; low materiality never triggers another transformation.

Yoked runs execute the imposed action schedule with the same dummy actor calls.
Native and yoked means use exactly the common supported pairs. Define

```text
Psi[p] = mean_c {[(J_ONLGR-J_RAW)_NATIVE,common
                  -(J_ONLGR-J_RAW)_YOKED,common]_{p,c}}.
```

If common support, materiality, mean `Psi>=0.01`, and its paired two-sided 95%
lower limit above zero all hold, report only that the native arm difference is
sensitive to this one predeclared cyclic exposure reassignment on common legal
support. `Psi` is not an average over shifts, a controlled direct effect, a
state-alignment explanation, or evidence about all legal permutations. Missing
support/materiality suppresses only `Psi`; no search or repair follows. Because
this is an off-policy post-treatment controlled action sequence, it cannot
support the primary algorithm comparison.

## Held-out evaluation, outcomes, and inference

Each final learned checkpoint receives 32 paired no-safety episodes per held-
out conclusion schedule and 32 paired episodes in `RAND-IID-4-16-32`. Each
diagnostic control receives 16 paired episodes per applicable deterministic
schedule. The exposure-clamp and preselected exact-yoke diagnostics use the
first 16 predeclared native episode indices in each applicable arm/schedule
cell; the yoke applies only to ONLGR and RAW. Each
`FIXED-RATE-LEASE` validation grid point receives 16 episodes for each of four
training schedules on each of the two validation roots. The safety panel
contains 16 paired episodes per learned arm and schedule. Exogenous mode,
sensor, initial-state, safety, and tie namespaces are
paired by seed, schedule, and episode before any arm acts.

For seed `s`, arm `a`, and the seven held-out schedules `c`, let
`J[s,a,c]` be mean normalized return. The two project-facing estimands are

```text
P[s,a] = equally weighted mean_c J[s,a,c]
W[s,a] = min_c J[s,a,c].
```

`W` is the minimum schedule expectation inside each seed, never the minimum
sampled episode. Report every seed/cell mean, paired effect, and ordinary two-
sided 95% Student-t interval across the eight seeds. Because either co-primary
outcome may independently trigger project value, claim-bearing sign inference
uses Bonferroni-adjusted two-sided 97.5% Student-t intervals for both contrasts.
Performance support is `mean(P_ONLGR-P_RAW)>=0.02` with its adjusted lower
limit above zero. Robustness support is
`mean(W_ONLGR-W_RAW)>=0.03` with its adjusted lower limit above zero. These
rules support an estimate that meets the materiality margin with familywise
sign evidence; they do not claim that the true effect exceeds the margin. Both
outcomes and both ordinary/adjusted intervals are always reported, together
with the exact paired sign-flip p-value and leave-one-seed-out point estimates
as non-gating sensitivity summaries. The margins correspond respectively to
roughly five additional full-service ticks and one avoided long
rebind/recovery episode on this normalized 256-tick surface.

Let `R[s,a]` be mean return in `RAND-IID-4-16-32`. A schedule-identity-free
exposure-link interpretation additionally requires
`mean(R_ONLGR-R_RAW)>=0.02` with its paired two-sided 95% lower limit above
zero. A task-state-conditioned timing interpretation additionally requires
`mean(R_ONLGR-R_TIMING_ONLY)>=0.02` with its paired 95% lower limit above zero.
These are separate secondary gates. Failure of either does not erase a valid
seven-cell `P` or `W` result, but lowers its claim respectively to deterministic-
cadence package value or to a timing/tenure heuristic.

`PROB-EXP-IDENTITY` supplies only the declared algebraic conformance result. It
has no return, equivalence interval, or independent scientific vote.

Required diagnostics by seed, schedule, cause, role, and arm are:

- voluntary event count per eligible physical tick and event-free survival;
- attempted and executed `KEEP`, `REFRESH-SAME`, and `REBIND` counts;
- lease-masked fraction, eligible exposure, lease-grid overshoot, and physical
  inter-event dwell histogram;
- cue-conditioned event and mark probabilities, event/mark entropy, and
  saturation fractions `u<0.01` and `u>0.99`, including the initialization
  exposure grid;
- mismatch-to-rebind latency, stale-binding ticks, plan age, service, action
  downtime, and action cost, with service utility and explicit action-cost
  components reported separately;
- forced-safety count, same-tick response, affected/unaffected agent action,
  and safety violations;
- actor/critic calls, policy-bearing rows, episode weights, PPO updates,
  parameters, messages, bits, physics ticks, optimizer steps, decision latency,
  peak RSS, and wall time; and
- identity/partition-probe, IID-future-`k`, timing-only, exposure-clamp,
  fixed-rate, oracle, degenerate-control, and yoke-support/materiality facts.

The learned arms must have identical declared parameter count, complete
episodes, physical ticks, training schedules, actor/critic calls for a given
schedule, messages, bits, full-batch PPO epochs, optimizer steps, and held-out
panels. ONLGR versus RAW differs only in the scalar link; TIMING-ONLY is the
explicit input ablation. A project-facing claim additionally requires no cap
violation, no missing required cell, no delayed or pair-forced safety action,
and ONLGR p95 actor latency no more than 10% above RAW on the same host. Wall
time and RSS are reported rather than synthetically padded.

## Activity boundary, support, and completeness

Question-relevant scientific activity begins when ONLGR and RAW have each used
their first complete paired training episode from every training schedule in a
valid SMDP-GAE PPO update and the retained record contains at least one
lease-eligible routine event and one conditional-mark log-probability for each
role. A process launch, host contract check, forced-KEEP replay, fixed-rate
selection, partial episode, dummy forward pass, or critic-only update is
preactivity.

The full three-action mechanism is exposed for a seed/schedule only when ONLGR
and RAW each contain at least 64 agent-level routine rows with both voluntary
marks legal and each arm executes at least four voluntary refreshes and four
voluntary rebinds in that cell. Check all seven native conclusion schedules and
the IID audit separately. The legality count is host support; failure is non-
identification for the full marked mechanism in that cell. With adequate
legality, an always-KEEP or single-mark policy is an observed degenerate
behavior: its return remains valid, but it cannot support lease-gated rebinding.
Forced safety actions never satisfy voluntary support.

State-conditioned adaptation additionally requires the registered ONLGR-
versus-TIMING-ONLY IID contrast. The state oracle must exceed the best of
TIMING-ONLY, FIXED-RATE, and the three degenerate policies by at least `0.02` in
equal-weight seven-cell mean return for the host to establish material adaptive
headroom. Without that headroom, no state-adaptation claim follows even if a
finite link contrast is positive.

Complete package interpretation requires all three learned final checkpoints
for every seed, all seven native held-out schedules, the IID future-`k` audit,
the analytic identity and operational partition probes, the safety panel,
resource facts, and the fixed-rate diagnostic. A missing IID or timing-only row
removes the schedule-identity-free or task-state-conditioned interpretation but
does not erase a complete seven-cell ONLGR-versus-RAW return contrast. Missing
yokes remove only `Psi`. Missing exposure-clamp or degenerate rows remove only
their finer interpretation. No new seed, schedule, threshold, or arm may be
added after observing a primary contrast.

## Outcome and decision map

- **ONLGR beats RAW on `P` or `W`, with safety/resource facts valid:** retain
  ONLGR as a direct variable-`k` algorithm candidate on the seven deterministic
  cells. Name the supported estimand; the other is not implied. This alone is a
  finite-budget parameterization/initialization/optimization package result.
- **ONLGR also beats RAW in `RAND-IID-4-16-32` and passes the operational marked
  partition probe:** support a useful eligible-exposure link inductive bias
  under unpredictable next-interval timing on the registered support.
- **Deterministic `P` or `W` passes but the IID contrast does not:** deterministic
  cadence prediction remains sufficient; do not claim schedule-identity-free
  opportunity normalization.
- **IID ONLGR beats RAW but not TIMING-ONLY:** a learned timing/tenure heuristic
  remains sufficient; do not claim use of task state or mismatch cues.
- **IID ONLGR beats both RAW and TIMING-ONLY, with oracle headroom and marked
  activity:** support task-state-conditioned exposure timing on this toy, not
  the causal value of the lease or of REBIND separately.
- **The analytic probability-exponent identity fails:** the formula or
  implementation is nonconformant; do not interpret an exposure-link mechanism.
- **Return improves but marked partition stability does not:** claim at most a
  frozen parameterization/initialization/optimization benefit.
- **RAW is also partition-stable and matches ONLGR:** the raw learner acquired
  the relevant mapping; prefer the simpler learner on this surface.
- **Partition stability improves but return does not:** normalization works as
  a behavioral invariant, but cadence is not a task bottleneck here. Do not add
  credit or capacity merely to rescue it.
- **ONLGR beats RAW but not FIXED-RATE-LEASE:** the lease plus a state-blind
  cadence remains the strongest explanation; do not claim learned
  state-conditioned timing.
- **Return gain comes only from lower explicit action cost while service utility
  does not improve:** report useful churn/cost regularization, not adaptive task
  rebinding.
- **Native benefit vanishes under the exposure clamp:** consistent with an
  exposure-link mechanism. If it persists, some learned representation or
  optimization difference remains sufficient.
- **The preselected cyclic `Psi` passes:** report only sensitivity of the native
  arm difference to that exact exposure reassignment on common legal support.
  Neither passage nor persistence identifies why the native algorithms differ.
- **Only short schedules improve while long schedules degrade:** report a
  cadence bias, not variable-`k` robustness. **Only long schedules fail:** the
  missing-action latency of coarse callbacks or endpoint aliasing remains a
  likely boundary that normalization cannot remove.
- **The lease masks nearly all opportunities or safety actions dominate:** the
  voluntary mechanism is not exposed. Revise the host support, not the result
  threshold.
- **Adequate legal opportunities but ONLGR chooses only KEEP or one mark:** this
  is a degenerate learned behavior. It may support a narrow return statement
  but not lease-gated rebinding.
- **Any safety delay, affected-agent omission, unaffected-agent forced action,
  or reset asymmetry occurs:** make no safety or complete algorithm claim.
- **Neither ONLGR nor TIMING-ONLY beats RAW while the state oracle has material
  headroom:** the frozen features, PPO access, or mark learning failed. The next
  discriminator is access, not more seeds. If the oracle also lacks headroom,
  this host does not materially reward adaptive timing under the frozen costs.

## Strongest alternative explanation

The 12-tick lease plus the ONLGR link's exposure-dependent initialization and
gradient conditioning may suppress costly actions, while realized `delta_t`
reveals a deterministic cadence and makes current task cues unnecessary.
`TIMING-ONLY-ONLGR`, `FIXED-RATE-LEASE`, the IID future-`k` audit, operational
marked partition probe, service/cost decomposition, exposure clamp, and native
mark-activity rules divide this explanation on their declared supports. The
probability-exponent identity adds no independent evidence. Even a complete
positive result cannot show the causal benefit of the lease or REBIND, give a
coarse callback fine-grid reaction latency, establish a literal hazard, or
generalize the yoke beyond its one preselected rotation.

## Small registered budget

Training uses
`3 arms * 8 seeds * 256 episodes * 256 ticks = 1,572,864` team ticks.
Native conclusion evaluation uses
`3 * 8 * 7 * 32 * 256 = 1,376,256` team ticks. The exact conservative ledger is

```text
training                         1,572,864
native learned-arm evaluation   1,376,256
IID future-k audit                 196,608
safety panel                       688,128
closed-loop exposure clamp         688,128
four degenerate/oracle controls    917,504
fixed-rate validation              393,216
fixed-rate held-out evaluation     229,376
preselected yoke maximum           458,752
KEEP-grid replay                   229,376
total                            6,750,208
cap                              7,000,000
remaining margin                   249,792
```

The identity and partition probes are analytic and consume no trajectory ticks.
The yoke checks exactly one hypothetical rotation per paired ONLGR/RAW episode
in `O(HN)` work. The registered
cap remains one CPU worker, 45 wall minutes, and 2 GiB peak RSS. The run must
not silently reduce arms, seeds, episodes, schedules, controls, or panels. A
cap stop before complete primary output is inconclusive CM engineering work,
not evidence against ONLGR.

## Second surface and UAV-simulator bridge

The next surface, only after a useful toy result, is a continuous planar
two-UAV tracking-relay mission with fixed physics/sensor ticks and persistent
low-level controllers. External `k` is the high-level replanning or
communication callback interval. `KEEP` continues the current option;
`REFRESH-SAME` replans a trajectory or relay geometry while retaining target,
role, partner, and formation slot; `REBIND` changes one of those assignments.
The physical lease is minimum dwell before another voluntary role/target/slot
change. Collision, geofence, separation, and hard flight-envelope events use
the same immediate forced bypass in every arm.

The second-surface discriminator trains one checkpoint over two callback
intervals and evaluates an evaluator-randomized, unannounced within-episode
fine/coarse grid switch plus a held-out interval. The switch is independent of
mission state. Outcomes are time-integrated tracking error, end-to-end relay
availability/link margin, formation RMS error, energy, replan/handoff settling
loss, safety response, and voluntary events per eligible second. The low-level
controller, radio/flight physics, masks, lease seconds, safety thresholds,
messages, optimizer work, and simulated time remain matched. A toy result does
not transfer as UAV evidence; the same policy must again beat RAW or another
matched adaptive baseline on performance or worst-condition robustness.

The transfer fails if callbacks deliver genuinely new independent evidence per
arrival, state changes too quickly for an endpoint rate to summarize the
interval, safety or lease censor nearly all voluntary exposure, or coarse `k`
removes indispensable reaction opportunities. A later cause-specific impulse
head would be a new treatment and is not silently included here.

## Claim ceiling

The strongest positive B1 claim is:

> In this constructed two-agent tracking-relay host, one shared final policy
> trained across two callback periods and their midpoint switches used a
> lease-eligible exposure-offset boundary link and improved the named seven-cell
> held-out mean or worst-schedule normalized return over an input-, capacity-,
> action-, lease-, optimizer-, work-, and ordinary-SMDP-GAE-matched raw
> per-opportunity learner, without safety or resource failure.

If the IID future-`k` contrast and operational marked partition gates also pass,
the claim may add that the eligible-exposure inductive bias remained useful when
the next callback interval was independent of visible history. If ONLGR also
beats TIMING-ONLY with oracle headroom, service rather than cost-only support,
and nondegenerate marked activity, it may add task-state-conditioned timing on
this host. A passing `Psi` adds only sensitivity to one preselected legal cyclic
reassignment on common support and never explains the native treatment effect.

B1 cannot establish representational impossibility of RAW, a literal or
ontologically correct continuous-time hazard, the causal value of the lease or
REBIND versus REFRESH-SAME, removal of coarse-grid reaction latency, arbitrary
`k`, learned safety, general tactic libraries, more than two agents, variable
`N`, UAV performance, general PPO superiority, or benefit outside the named
host, schedules, seeds, budget, and margins. A null is equally local. Missing
code, runtime, or a partial result changes none of these claim boundaries.

## Exact Root-to-CM packet

If Root allocates construction, relay this packet unchanged in scientific
meaning:

```text
scope=direction:opportunity_normalized_lease_gated_rebinding
treatment=ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1
revision=ONLGR-PRO-PREACTIVITY-CORRECTION-20260812-01
classification=direct variable-k algorithm candidate
construct=new isolated H=256 two-agent tracking-relay host; fixed physical
          sensor/physics stream; external callback tapes; exposure-offset marked
          boundary actor; ordinary physical-time SMDP-GAE; ONLGR, RAW, and
          TIMING-ONLY learned arms; native, IID-future-k, safety, identity/
          partition, clamp, fixed-rate, degenerate/oracle, KEEP, and one-shift
          yoke evaluators; analyzer; one train/evaluate/analyze entry point
varying_axis=one final checkpoint per arm/seed trained jointly on CONST-8,
             CONST-24, MID-8-TO-24, MID-24-TO-8; evaluated unchanged on
             CONST-4/16/32, MID-4-TO-32, MID-32-TO-4, ALT-4-32-4-32,
             ALT-32-4-32-4; separate RAND-IID-4-16-32 draws every next interval
             after the current action, independently of complete visible history
actions=KEEP preserves state; REFRESH-SAME keeps binding, resets plan age,
        costs 0.02 and one busy tick; REBIND flips binary binding, resets plan
        age, costs 0.04 and two busy ticks
lease=both voluntary non-KEEP marks masked for 12 physical ticks after every
      executed non-KEEP; KEEP always legal; mask before sampling; same reset
      and costs in every arm
exposure=right-closed integer slots I=(b_prev,t]; e_i(t)=count legal slots in I;
         delta_t=t-b_prev; endpoint first-legal slot contributes one; terminal
         residual is censored with reward but no action/likelihood/reset; this is
         an exposure-offset boundary link, not a literal predictable hazard
safety=separate panel, one event/episode; immediate same-tick forced REBIND on
       mismatch else REFRESH-SAME; bypass lease; affected agent only; ordinary
       costs/reset; safety precedence over coincident routine callback; no
       policy logprob; coincidence suppresses routine for both agents, resets
       b_prev/index once only for affected, leaves unaffected clocks intact,
       and never terminates/clears return or GAE credit from prior actions
primary_actor_inputs=identical role, binding, fixed-eight-tick mismatch, plan
                     age, lease, busy, partner two-bit summary, cause, realized
                     delta_t, and e for ONLGR/RAW; no schedule label, absolute
                     time, count/history, future k, mode, reward, seed, recurrence
timing_only=ONLGR link and same dimensions/work, but binding, own mismatch, and
            partner task-summary actor coordinates are fixed zero; retains role,
            age, lease, busy, cause, delta_t, and e; critic remains matched
leakage_control=switch twin proves same-boundary nonanticipation only;
                RAND-IID-4-16-32 provides history-independent future-k audit
action_law=event u followed by common conditional refresh mark rho;
           P(KEEP)=1-u, P(REFRESH)=u*rho, P(REBIND)=u*(1-rho)
treatment_link=u=1-exp(-softplus(g)*e)
primary_comparator=RAW-BOUNDARY-LEASE with u=sigmoid(g), same delta_t/e access
identity_control=analytic PROB-EXP-IDENTITY only; exact same map/gradient as
                 ONLGR; float64 probability/mark conformance tolerance 1e-10;
                 no checkpoint, trajectory, optimizer, or independent evidence
likelihood=one full per-agent categorical logprob; sum stochastic agents into
           one joint logprob and one PPO ratio clipped once; deterministic,
           masked, dummy, and forced actions add no actor score
credit=ordinary team SMDP-GAE only; gamma_tick=0.99^(1/8),
       lambda_tick=0.95^(1/8); actor is schedule/episode-balanced sum of genuine
       joint PPO terms scaled only by common 1/256; no duration weights, row
       means, pooled-row averages, or advantage normalization; critic is
       schedule/episode-balanced mean of SMDP value rows; no dense relay,
       escrow, association label, or auxiliary reward
entropy=coefficient exactly zero; diagnostic marked entropy is
        H_Bernoulli(u)+u*H_Bernoulli(rho), zero on masked/e=0/forced rows
learner=paired (32,32) actor and (64,64) centralized critic; PPO clip .20,
        Adam 3e-4, value .5, entropy 0, grad cap 1.0, four full-batch epochs/
        steps, 8 episodes per each of four schedules/update; 256 episodes/arm/
        seed; final checkpoint only
seeds=[17,31,47,61,79,97,109,127]
primary_outcomes=P=equal mean of seven held-out schedule means;
                 W=minimum of those seven schedule means inside seed
materiality=ONLGR-RAW mean P >=.02 or mean W >=.03, named separately, with
            paired Bonferroni two-sided 97.5% Student-t lower bound >0 across
            eight seeds; ordinary 95%, sign-flip, and leave-one-seed-out reported
IID_gates=for schedule-identity-free link claim mean R_ONLGR-R_RAW>=.02 and
          paired 95% lower>0; for task-state timing claim mean
          R_ONLGR-R_TIMING_ONLY>=.02 and paired 95% lower>0
mechanism_controls=equal-time partition refinement; exposure clamp; fixed-rate
                   lease control selected only on validation roots 1009/1013;
                   preselected exact cyclic yoke; KEEP grid equality;
                   degenerate policies and state oracle
partition_cells=role{T,R} x binding{0,1} x cue{.25,.75} x age{16,32}=16
partition_rule=frozen-score ONLGR/PROB identity plus operational marked
               cumulative S/R/B total-variation MPI; >=12/16 common nonsaturated
               one-block-matched cells/seed; mean MPI_ONLGR<=.02 and 95%
               upper<.03; RAW-ONLGR MPI mean>=.02 and paired 95% lower>0
yoke=secondary only; preselect exactly one counter-keyed nonzero joint cyclic
     shift, same shift paired ONLGR/RAW, recompute masks/leases/busy/exposure,
     preserve time-weighted binding occupancy, no fallback/outcome use/repair;
     >=15/16 common support per seed/schedule and exposure-reassignment M_exp
     mean>=.10 with 95% lower>.05; Psi is bounded sensitivity only
clamp=closed-loop evaluation of all three learned arms on first 16 native
      indices; live masks/actions/state/reward, only actor/critic delta_t/e set
      to 8 at lease-eligible routine rows; paired tapes; no learning
fixed_rate_tie=highest validation mean, then ascending lambda, then ascending
               abs(rho-.5), then ascending rho; no held-out use
safety_resource_gate=all cells complete; zero delayed/missed/pair-forced safety
                     actions and cap violations; matched params, ticks, calls,
                     messages, bits, PPO work; ONLGR p95 actor latency <=1.10x
                     RAW
activity=first valid paired update containing complete episodes from all four
         training schedules, at least one lease-eligible routine event and one
         conditional mark logprob for each role in ONLGR and RAW
required_return=whether activity began; exact host/support facts; final
                checkpoints; every seed/schedule P/W/R row and intervals; all
                behavior/safety/resource/identity/partition/IID/timing-only/
                clamp/fixed-rate/yoke facts; anomalies and remaining unknowns;
                no CM scientific conclusion
budget=exact conservative maximum 6,750,208 team ticks under a 7,000,000 cap;
       one CPU worker, 45 minutes, 2 GiB RSS; no restart, sweep, seed/schedule
       reduction, threshold repair, or post-result arm
```

CM owns source, tests, runner, environment, technical acceptance, and any
unchanged-science repair. This card authorizes no EM code, test, runtime, or
technical judgment.
