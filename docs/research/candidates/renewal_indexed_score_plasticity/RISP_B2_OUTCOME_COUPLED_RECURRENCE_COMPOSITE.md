# RISP-B2 outcome-coupled direct-renewal recurrence composite

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B2
science_revision=RISP-B2-SCIENCE-20260814-01
owner=/root/em_renewal_indexed_score_plasticity
paired_cm=/root/cm_renewal_indexed_score_plasticity
artifact_status=COMPLETE_FROZEN_DEFINITION_PENDING_CM_GEMINI_AND_SAME_CONVERSATION_PRO
scientific_activity_started=false
construction_authorization=none
source_change_authorization=none
test_or_probe_authorization=none
stochastic_coordinate_binding=none
compute_or_lease_authorization=none
best_reachable_x_authorization=none
```

## Decision question and protected conclusion

RISP-B2 asks whether a fixed, value-aligned completed-outcome/action anchor is
a useful finite-training coordinate prior for one shared-parameter renewal
controller across externally varied skill periods. After a completed
nonterminal hold, the treatment converts only the selected action and its
causally available realized outcome into a bounded local action-affinity state.
That state can affect only the next legal action. The active hold is never
changed, future duration is never read, and no parameter changes at evaluation.

One slow controller and one recurrent parameterization are trained jointly at
`k in {4,8}`. The same frozen tensors are evaluated at held-out `k=12` and at
the external switches `4 -> 12` and `12 -> 4`; there is no per-`k` table, head,
gain, checkpoint, reset, or evaluation-time optimizer. Parameters are shared by
the two agents and all durations. Each agent has its own episode-local fast
state.

The treatment is `DIRECT-ANCHOR`. Its primary comparator is
`DIRECT-CONTAIN`, which has the same state, packet, policy mixture, trainable
matrix, parameter count, information, action support, optimizer exposure,
update opportunities, and reset law, but no fixed outcome/action anchor. The
two recurrent function classes are exactly identical by an affine parameter
translation. A positive result can therefore support only this fixed
coordinate prior under the frozen finite training package; it cannot support
exclusive expressivity.

The conclusion-bearing evaluation crossing is

```text
DIRECT-ANCHOR / INTACT
DIRECT-ANCHOR / MARGINAL-TWIN
DIRECT-CONTAIN / INTACT
DIRECT-CONTAIN / MARGINAL-TWIN.
```

`MARGINAL-TWIN` preserves the recipient controller's conditional outcome-sign
law and every legal update opportunity but severs the realized recipient
outcome lineage. Checkpoints are trained once with intact outcomes and cloned
into both feedback cells. Thus feedback cells have identical parameters and no
differential optimizer exposure.

The maximum positive claim is narrowly this: on the exact finite two-agent toy
and frozen finite budget, the fixed value-aligned completed-outcome/action
coordinate prior improves mean physical-time value over its function-equivalent
containing recurrence on the registered held-out/post-switch mixture, and the
architecture advantage depends on the actual completed-recipient outcome
rather than an outcome-history-independent conditional replicate. It is not a
claim of generic score plasticity, optimality, convergence, arbitrary or
unknown `k`, variable `N`, coordination, UAV value, safety, or deployment
benefit.

## Frozen two-agent renewal toy and physical-time endpoint

There are exactly two parameter-sharing, noncommunicating agents. Their rewards
and hidden processes are independent conditional on the common policy, so the
experiment makes no multi-agent credit or coordination claim. An episode has
`T=192` primitive ticks and action order `(LEFT,HOLD,RIGHT)`.

At renewal `n`, agent `i` has a hidden target `c_i,n` in the three-action set.
`c_i,0` is uniform and never enters the policy observation. At boundary
`tau_n`, the agent selects `a_i,n` and holds it unchanged for
`d_n=k_n` ticks. No action, outcome, fast-state, mask, or policy row changes
inside the hold. One latent outcome is drawn at selection,

```text
P(Y_n=+1 | a_n=c_n)  = 3/4
P(Y_n=+1 | a_n!=c_n) = 1/4,
```

and the primitive reward is `r_t=Y_n` throughout that hold. At completion,

```text
c_(n+1) = a_n                            if Y_n=+1
c_(n+1) = Uniform(A \ {a_n})             if Y_n=-1.
```

The policy-visible boundary observation is only

```text
o_n = [tau_n/T, k_n/12].
```

The policy never receives the hidden target, an unchosen outcome, the next
target, future `k`, future reward, or an experimenter-only belief. The episode
endpoint is primitive-time mean reward,

```text
J = (1/(2*T)) * sum_i sum_(t=0)^(T-1) r_(i,t).
```

The five fixed schedules and their roles are:

| id | schedule | role | decisions | nonterminal updates |
|---:|---|---|---:|---:|
| 0 | fixed `k=4` | seen qualification | 48 | 47 |
| 1 | fixed `k=8` | seen qualification | 24 | 23 |
| 2 | fixed `k=12` | held-out target | 16 | 15 |
| 3 | `k=4` on `[0,96)`, then `k=12` | target switch | 32 | 31 |
| 4 | `k=12` on `[0,96)`, then `k=4` | target switch | 32 | 31 |

At `t=96`, the old hold completes and may update the state; the action selected
there first sees the new `k`. The conclusion-bearing target endpoints exclude
the first completed hold under the new duration, because its action could not
have used a new-duration outcome:

```text
Q(12)      = mean reward over ticks 0,...,191
Q(4->12)   = mean reward over ticks 108,...,191
Q(12->4)   = mean reward over ticks 100,...,191.
```

Every mean includes both agents. The seed-level primary endpoint is the
equal-weight mixture

```text
Q_TARGET = (Q(12)+Q(4->12)+Q(12->4))/3.
```

Full switch episodes, the excluded first new-`k` hold, action entropy, renewal
count, and curves indexed separately by ticks and completed renewals are
diagnostic only. No renewal-indexed quantity may replace the physical-time
endpoint.

## Shared slow policy and direct bounded state

The shared slow policy uses the same bounded three-action head in every arm:

```text
h_n      = tanh(Linear(8,4)(tanh(Linear(2,8)(o_n))))
l_base   = Linear(4,3)(h_n)
z_a      = 6*l_base,a/(6+|l_base,a|)
w_a      = 16+(z_a+6)^2
pi_slow(a|o_n) = w_a/sum_b w_b.
```

For finite parameters, every `pi_slow(a)>1/21`. There is one private fast state
`q_i,n` per agent, with `q_i,0=(1/3,1/3,1/3)`. It lies in the closed
three-simplex and is carried without reset across a schedule switch. The actual
action law is

```text
pi(a|o_n,q_n) = (1/2)*pi_slow(a|o_n) + (1/2)*q_n(a).
```

Thus every action has common support greater than `1/42`, the active macro is
never changed, and a changed state has a direct path to relative action
probability. There is no learned low-rank fast-state policy port.

At selection, the controller stores only `(q_n,a_n,k_n,tau_n)`. After the hold
completes, its legal feedback sign is

```text
s_n = Y_n in {-1,+1}.
```

Define the 13-vector

```text
phi_n = [1,
         q_n(LEFT),q_n(HOLD),q_n(RIGHT),
         onehot(a_n)_LEFT,onehot(a_n)_HOLD,onehot(a_n)_RIGHT,
         s_n,
         s_n*onehot(a_n)_LEFT,
         s_n*onehot(a_n)_HOLD,
         s_n*onehot(a_n)_RIGHT,
         k_n/12,
         tau_n/T].
```

For any positive simplex vector `v`, define its canonical two-logit chart

```text
chart(v) = [log(v_LEFT/v_RIGHT), log(v_HOLD/v_RIGHT)]
Simplex(z) = softmax([z_LEFT,z_HOLD,0]).
```

`Simplex(chart(v))=v` exactly in real arithmetic.

## Fixed value-bearing anchor and containing comparator

For selected action `a`, let `u=(1/3,1/3,1/3)` and define the softened
next-target distributions

```text
b(+1,a) = onehot(a)
b(-1,a) = (1-onehot(a))/2
v(s,a)  = (3/4)*b(s,a) + (1/4)*u.
```

Consequently, `v(+1,a)` places `5/6` on `a` and `1/12` on each
alternative; `v(-1,a)` places `1/12` on `a` and `11/24` on each
alternative. All entries are strictly positive. Let the unique fixed matrix
`G in R^(2x13)` be zero on all columns except the categorical
`onehot(a)` and `s*onehot(a)` columns and satisfy

```text
G*phi_n = chart(v(s_n,a_n))
```

for every one of the six `(s,a)` pairs. Equivalently, its two categorical
column blocks are the unique half-sum/half-difference decomposition of those
six declared chart vectors; this defines every entry of `G` without training.

Both architecture arms have one trainable `W in R^(2x13)` and use one
matrix-vector product plus the same `Simplex` call after every eligible hold:

```text
DIRECT-ANCHOR:  q_(n+1) = Simplex((G+W_A)*phi_n)
DIRECT-CONTAIN: q_(n+1) = Simplex(W_C*phi_n).
```

The terminal hold has no later consumer and produces no update. There is
exactly one update after every other completed hold and before the next legal
action. `W_A=W_C=0` at initialization. The fixed `G` is never optimized or
regularized. Both learned matrices have 26 scalars, use the same initialization,
optimizer, loss, batch order, and update count, and every scalar remains on a
path to the next action distribution.

The comparator algebraically contains the treatment and the two classes are
bidirectionally identical:

```text
W_C = W_A + G
W_A = W_C - G.
```

This equality holds before `Simplex` and therefore for every state trajectory
and policy. The scientific difference is the fixed coordinate/initialization/
regularization path, not capacity or information. Both arms execute the fixed
matrix path, with the comparator's fixed matrix equal to exact zero, so useful
affine work and update opportunities are matched.

The anchor is prospectively value-bearing on the declared toy. Hold the next
observation fixed and define the exact expected next-hold value from the
post-outcome target belief `b` as

```text
V(b,pi) = sum_a pi(a)*(b(a)-1/2).
```

With uniform `pi_slow`, uniform old `q`, and `W_A=0`, a positive update gives
next policy mass `(7/12,5/24,5/24)` around the selected action, increasing
`V` over the uniform no-update policy by exactly `1/4`. A negative update gives
mass `(5/24,19/48,19/48)`, increasing `V` by exactly `1/16` for the uniform
alternative target belief. The corresponding update-induced policy TVs are
`1/4` and `1/8`. These are structural consequences of the frozen DGP and
anchor, not estimates or settings selected from RISP-B1 outcomes.

For every later eligible row, the direct actuation identity is

```text
TV(pi_updated,pi_no_update) = (1/2)*TV(q_(n+1),q_n),
```

where the no-update clone holds `o_(n+1)` and `pi_slow` fixed and merely carries
`q_n`. This identity certifies actuation, not usefulness. Usefulness is measured
separately by

```text
DeltaV_update = V(b(s_n,a_n),pi_updated)
                - V(b(s_n,a_n),pi_no_update).
```

High TV with nonpositive `DeltaV_update` is policy motion without task-aligned
semantics.

## Causal timing and future-leakage boundary

The only deployable information path is

```text
pre-outcome history -> selected action -> completed hold/outcome
-> local recurrent update -> later legal action.
```

The update may use old `q_n`, the selected action, the completed outcome sign,
old `k_n`, and old boundary time. It may not use `k_(n+1)`, a future schedule,
the hidden target, the sampled next target, an unchosen outcome, next action,
future reward, a bootstrapped future value, another agent's outcome, or any
evaluation statistic. The next policy may observe the newly latched `k` only
after the prior hold has completed and the prior-outcome update is final.

Training may backpropagate through completed episode histories and may use the
registered physical-reward objective below. That offline training credit is not
a runtime input. At evaluation, slow and recurrent parameters are frozen; only
the declared per-agent `q` changes.

## Outcome-history-independent marginal twin

`MARGINAL-TWIN` is evaluation-only. It never reads the recipient hidden target,
realized outcome, sampled next target, current or past reward, next state,
unchosen action, performance, or future schedule. It maintains an exact
experimenter-side rational filter

```text
rho_n(c) = P(c_n=c | recipient controller-visible pre-outcome history H_n),
rho_0    = (1/3,1/3,1/3).
```

Given the recipient's selected action,

```text
pbar_n = P(Y_n=+1 | H_n,a_n) = 1/4 + (1/2)*rho_n(a_n).
```

An independent twin sign is drawn from `Bernoulli(pbar_n)` in `(+1,-1)` order
and only that sign enters the twin recurrence packet. Because this draw is
conditionally independent of the recipient outcome lineage, observing it does
not update the filter about the actual hidden process. The filter advances by
marginalizing the unobserved actual outcome:

```text
rho_(n+1)(c') = pbar_n                         if c'=a_n
rho_(n+1)(c') = (1-pbar_n)/2                  if c'!=a_n.
```

The actual recipient outcome still scores physical reward and advances the
actual hidden target. The twin sign drives `q`, all later policy-visible state,
and nothing else. Every eligible recipient update has exactly one twin update;
terminal holds have neither. The twin uses an independent abstract random
family while architecture and feedback cells reuse paired environment/action
tapes prospectively. No concrete RNG seed, address, stream, or stochastic
coordinate is bound by this definition-only object.

This control preserves schedule, renewal density, legal action opportunities,
conditional sign frequency, packet dimension, state dimension, affine work,
and checkpoint. It removes only coupling to the realized recipient outcome.
Therefore equal or similar intact and twin value leaves stationary persistence,
temporal correlation, and global renewal-rate sufficiency live; the twin is not
evidence that those alternatives are absent.

## Frozen training package

There are sixteen prospective independent algorithm-seed inference strata.
Their concrete numeric seeds and product-coordinate materialization remain
unbound and require later authority. Within each future stratum, the two
architecture arms will reuse paired slow-policy initialization and paired
environment/action tapes. `W_A` and `W_C` start at exact zero. Different strata
are independent. No RISP-B1 checkpoint, optimizer state, random word, seed,
partial value, or result enters this object.

All slow-policy weights, learned recurrent weights, optimizer states, forward
values, `q`, `phi`, and fixed-`G` values are IEEE binary64. The abstract
initialization law supplies independent integers
`R_INIT~Uniform({0,...,2^53-1})` within each stratum and sets
`U53=R_INIT*2^-53`. In row-major order, each slow-policy weight matrix is
initialized as

```text
sqrt(6/(fan_in+fan_out))*(2*U53-1),
```

then rounded once to binary64; all slow-policy biases are exact binary64 zero.
The same initialized slow tensors are cloned into both architecture arms.
`W_A` and `W_C` and their implicit constant columns are exact binary64 zero;
there is no separately learned recurrent bias because `phi` already begins
with `1`. `G` is the correctly rounded binary64 evaluation of the declared
real chart constants. Concrete seed numbers, RNG algorithm, and addresses
remain unbound, but any later binding must realize this finite-grid law
symmetrically and may not add an architecture-specific draw or cast.

Each architecture/stratum receives exactly 256 AdamW updates, batch size 16
complete two-agent episodes, with eight fixed-`k=4` and eight fixed-`k=8`
episodes in alternating order. There is no switch or `k=12` training. AdamW
uses learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, decoupled
weight decay `1e-4` on every learned scalar, and global gradient clipping at
`1.0`. The fixed `G` is never decayed. Both arms receive the same number and
ordering of optimizer steps and complete episodes.

For training only, maintain the exact controller-history belief
`beta_n(c)=P(c_n=c | a_0,Y_0,...,a_(n-1),Y_(n-1))`, with `beta_0` uniform and
`beta_(n+1)=b(Y_n,a_n)`. It is an experimenter-side baseline input and never a
policy or runtime-recurrence input. For a batch, let `d_n=k_n` and define the
exact pre-outcome expected interval reward and detached residual

```text
B_n     = d_n*sum_a pi_n(a)*(beta_n(a)-1/2)
delta_n = d_n*Y_n - B_n.
```

The common loss is

```text
L_task = -(1/(16*2*T))*sum_n
           [stopgrad(delta_n)*log pi_n(a_n)
            + 0.002*d_n*Entropy(pi_n)]

L_align = mean over every eligible nonterminal agent-renewal row in the batch
          of CE(v(Y_n,a_n), q_(n+1))

L = L_task + (1/4)*L_align.
```

The alignment target uses only the completed outcome and selected action. It
never uses the hidden or sampled next target. It is applied identically to both
architectures and is part of the finite toy package, not a claim that UAV
transitions obey the toy rule. The recurrence is differentiated through the
complete episode; sampled actions, outcomes, beliefs, `delta`, and target `v`
are detached. There is no target-selected checkpoint or early stopping.
Update 256 is conclusion-bearing. Updates `0,32,64,128,256` are fixed
report-only learning/contraction diagnostics and cannot select a model,
threshold, branch, or successor.

Evaluation uses 64 complete episodes for each seed, schedule, architecture,
and feedback cell. The two feedback cells clone the same update-256 checkpoint.
`UNIFORM` and privileged `STATE-ORACLE` descriptive controllers use the same
episode count and paired prospective environment families. `UNIFORM` chooses
each action with probability `1/3`. `STATE-ORACLE` observes the hidden target
and chooses it with probability `29/30`, allocating `1/60` to each other
action. Neither is a primary comparator.

The future stochastic law must use independent abstract event families for
initial targets, actions, actual outcomes, alternative targets, and twin draws,
with deliberate common-tape reuse only for corresponding paired cells. The
recipient outcome and its twin are independent conditional on the recipient's
pre-outcome controller history and action. Exact concrete seeds, RNG families,
addresses, event keys, traversal, and ledger are intentionally not authorized
or bound here; CM may assess whether they can be bound later without changing
this probability law, sample counts, coupling, or inference.

## Complete-panel validity and qualifications

Only a complete four-cell panel over all sixteen seed strata, all five
schedules, and all 64 episodes may support any conclusion. Partial seeds,
checkpoints, schedules, cells, learning curves, or values have no selection or
interpretation path. Every conclusion first requires:

1. exact treatment/comparator identity, paired checkpoint cloning, complete
   counts, declared schedule windows, no RISP-B1 data reuse, and no future or
   hidden-variable leakage;
2. one update after every eligible completed nonterminal hold, no terminal or
   mid-hold update, no state reset at switches, no evaluation-time parameter
   update, and identical legal action opportunities;
3. the algebraic containment translation, common packet, equal trainable
   parameter count, common action law/support, equal optimizer exposure, and
   correct marginal-twin filter/independence;
4. finite parameters and outputs, every action probability above `1/42`, and
   binary64 no-update-fork agreement with the analytic direct-TV identity and
   zero-residual anchor reference values within absolute tolerance `2^-40` for
   every reported probability, TV, and `DeltaV` scalar; the analytic reference
   values themselves remain exact reals (`DeltaV=1/4`, TV=`1/4` after `+1`;
   `DeltaV=1/16`, TV=`1/8` after `-1`);
5. both **INTACT** architecture cells clear seen competence at both `k=4` and
   `k=8`: the
   one-sided 95% lower confidence bound for their paired seed-level physical-
   time advantage over `UNIFORM` exceeds `0.08`;
6. both **INTACT** architecture cells retain headroom at both seen durations:
   the one-sided 95% lower bound for `STATE-ORACLE - architecture` exceeds
   `0.02`;
7. in each architecture, pooling **INTACT** eligible rows over seen schedules, the
   one-sided 95% lower bound on the seed-level fraction with
   `TV(pi_updated,pi_no_update)>=0.01` exceeds `0.25`, the lower bound on the
   fraction with `DeltaV_update>0` exceeds `0.55`, and the lower bound on mean
   `DeltaV_update` exceeds `0.005`; and
8. the same three action-sensitivity/value-alignment lower bounds clear on
   **INTACT** rows in the registered three-schedule target mixture for each
   architecture.

For items 7--8, both the update and `b(s_n,a_n)` use the actual completed
recipient sign. Twin rows never satisfy or repair these primary qualifications.
They have a separately named outcome-independent sufficiency diagnostic:
`TV_TWIN` compares the policy after the twin-sign update with its no-update
clone, while

```text
DeltaV_TWIN_RECIPIENT = V(b(Y_RECIPIENT,a),pi_after_twin_update)
                        - V(b(Y_RECIPIENT,a),pi_no_update)
```

uses the actual recipient sign only as an offline scoring label and never as a
twin-generator, recurrence, or policy input. A twin architecture
`clears_twin_value_diagnostic` exactly when, on the target mixture, its
one-sided 95% lower bound for physical-time advantage over `UNIFORM` exceeds
`0.08`, its lower bound on the fraction with `TV_TWIN>=0.01` exceeds `0.25`,
its lower bound on the fraction with `DeltaV_TWIN_RECIPIENT>0` exceeds `0.55`,
and its lower bound on mean `DeltaV_TWIN_RECIPIENT` exceeds `0.005`.

Failure of items 1--4 is `INVALID_IMPLEMENTATION_OR_PANEL`. A complete exact
panel that fails any of items 5--8 is
`EXACT_PACKAGE_NONIDENTIFYING_FOR_VALUE_ATTRIBUTION`. Such a panel may describe
observations but cannot support benefit, harm, equivalence, deletion, generic
recurrence, arbitrary-`k`, bridge, or policy-port conclusions.

## Seed-first estimands and frozen interpretation

For each seed, first average episodes within schedule/cell, form the
equal-weight target mixture, and then form paired contrasts. Seeds, not episodes
or renewals, are the inference units:

```text
D_I   = Q(ANCHOR,INTACT) - Q(CONTAIN,INTACT)
D_M   = Q(ANCHOR,TWIN)   - Q(CONTAIN,TWIN)
PSI   = D_I - D_M
C_A   = Q(ANCHOR,INTACT) - Q(ANCHOR,TWIN)
C_C   = Q(CONTAIN,INTACT)- Q(CONTAIN,TWIN).
```

Directional bounds are one-sample paired Student-`t` one-sided 95% bounds over
the sixteen seed values. Equivalence uses two-sided 90% `t` intervals. The
three schedule-specific nonharm bounds use one-sided 98.333% `t` bounds, one
per schedule, giving a Bonferroni family level of 0.05. Required positive
claims are conjunctions and use intersection-union logic; no favorable
component can compensate for a failed component. No row, seed, checkpoint,
schedule, or test is selected after observation.

Interpretation precedence after all validity/qualification gates is:

1. `HARM_FOR_EXACT_ANCHOR`: the one-sided 95% upper bound of pooled `D_I` is
   below `-0.02`, or a simultaneous schedule upper bound is below `-0.03`.
   This is harm only for the exact finite package.
2. `FINITE_TOY_REALIZED_OUTCOME_COUPLED_PRIOR_SUPPORTED`: the lower bounds
   satisfy `D_I>0.02`, `PSI>0.015`, and `C_A>0.015`; the 90% interval for
   `D_M` lies within `[-0.01,0.01]`; and every simultaneous schedule lower
   bound for `D_I` exceeds `-0.01`.
3. `DIRECT_RECURRENCE_PACKAGE_WITHOUT_ANCHOR_SPECIFICITY`: both `C_A` and
   `C_C` have lower bounds above `0.015`, while the 90% intervals for `D_I`
   and `PSI` lie within `[-0.01,0.01]`. Realized feedback helps this direct
   recurrence package, but the fixed anchor is not identified as the cause.
4. `GLOBAL_RATE_OR_OUTCOME_INDEPENDENT_PERSISTENCE_COMPATIBLE`: both
   architecture-specific intact-minus-twin 90% intervals lie within
   `[-0.01,0.01]`, and at least one architecture's twin cell satisfies the
   exact `clears_twin_value_diagnostic` definition above. This does not prove
   global-rate sufficiency; it says realized-outcome lineage was not needed in
   this package.
5. `NO_REGISTERED_MINIMUM_ANCHOR_BENEFIT`: the one-sided 95% upper bounds for
   both `D_I` and `PSI` are at most their positive margins (`0.02` and
   `0.015`), with no harm branch. This deletes only the registered minimum
   benefit claim for this exact anchor/package.
6. `VALID_UNRESOLVED`: every prerequisite passes but none of the preceding
   branches is established.

Branches 3--5 are bounded scientific dispositions, not equivalence or generic
null claims beyond their explicit intervals. Learning curves, projection-free
state occupancy, entropy, update counts, `C_C`, fixed-schedule values, and
renewal-indexed curves cannot create an extra success route.

## Strongest live alternatives and claim ceiling

Even a positive branch cannot distinguish the fixed semantic prior from its
initialization, regularization immunity, coordinate geometry, or finite-budget
optimizer path. The known toy transition makes win-stay/lose-suppress unusually
well aligned and may amount to a handcrafted finite-task solution. The learned
residual or slow controller may cancel, preserve, or exploit the anchor for
package-specific reasons. The containing comparator may converge more slowly
despite equal function class. A global renewal-rate or stationary action-
persistence strategy can outperform uniform without using realized outcome
lineage; the marginal twin is retained to expose, not assume away, that
alternative. High policy TV can be value-negative. RISP-B1 remains compatible
with shared finite-budget training failure, transition failure, and learned
policy-port failure. A separate package-specific SCDMP convergence explanation
is neither tested nor displaced by this direction-local object.

No result may claim an unbiased natural policy gradient, necessity of the sign
or score, convergence of either recurrent class, benefit at every `k`, unknown
duration generalization, continual learning, learned termination, variable
rosters, cooperation, or real-UAV value. A negative result deletes at most the
exact anchor/package or its registered minimum; it never deletes outcome-
coupled recurrence generally.

## Frozen BEST-REACHABLE-X four-outcome map

`BEST-REACHABLE-X` is not authorized, designed, bound, or run here. The table
only freezes how each possible later result would change the candidate graph so
that a future probe cannot be used to tune this composite retrospectively.

| Later BEST-REACHABLE-X outcome | Treatment and bridge consequence | Old policy-port / transition consequence |
|---|---|---|
| Competence and target TV are reachable from a frozen old checkpoint although learned states failed | Retain the outcome-coupled recurrence idea, but treat this direct bypass as an optional backup rather than a necessary repair; keep the toy-to-UAV bridge conditional on later physical value. | Retain the old port. Modify the leading repair toward transition reachability, training dose, or optimizer geometry. |
| Target TV is reachable but competence is not | Retain this value-semantic direct treatment as the leading bypass candidate, but delete TV alone as a success qualification; require `DeltaV` and physical value. | Retain actuation capability but demote the old transition/semantic geometry; policy-port presence is not sufficient. |
| No admissible old fast state clears target TV | Retain the direct policy-mixture treatment as the decisive actuation bypass, still subject to competence and value. | Delete the old learned low-rank port branch for this bounded host; do not infer that outcome feedback or recurrence is useless. |
| Target TV clears but expected next-hold value does not improve | Retain only a prospectively value-bearing semantic map such as the declared anchor; if its structural certificate also fails, delete this treatment and its UAV bridge. | Delete actuation-only and TV-only explanations; modify any transition branch to require outcome-aligned value, not mere policy motion. |

No row changes this frozen treatment, thresholds, training budget, or current
authorization. Any future BEST result can only choose among the prospectively
named retain/modify/delete consequences.

## Toy-to-UAV bridge and broken assumptions

The narrow bridge maps external `k` to a commanded macro-action duration or
communication/skill hold. Each UAV would run the same slow controller and keep
one private bounded action-affinity state across duration changes. A completed
macro supplies a deployable duration-correct local advantage sign; positive
evidence raises that macro's next-boundary affinity and negative evidence
suppresses it. The current macro is never interrupted.

The bridge is not established by toy success. A UAV treatment would require a
new science object defining three or more safe macro semantics, action masks,
mask-aware normalization, a deployable critic or outcome baseline fixed before
feedback, local-versus-team credit, delayed effects, wind/link dynamics,
coordination stability, safety overrides, simulator cost, matched containing
and no-lineage controls, and physical-time mission value. UAV transitions do
not generally make the next latent target equal to the previous action after
success or uniform over alternatives after failure. That broken assumption can
turn win-stay/lose-suppress into high-TV harm. Thus this card supports only a
mechanistic bridge hypothesis, never transfer or safety.

## Definition-only authority boundary

This artifact freezes a scientific object but authorizes no activity. It does
not bind stochastic coordinates, create or modify source, construct a runner,
run a test or probe, request a compute lease, launch training/evaluation, inspect
partial values, or authorize `BEST-REACHABLE-X`. CM may perform only the named
static bindability, observability, comparator-feasibility, and science-
definition ambiguity assessment. The existing direction-specific ChatGPT Pro
conversation must return literal mathematical/causal closure on the complete
object, and the independently frozen Gemini question may be sent only through
a concrete direction-specific conversation established or supplied by Root.
Neither provider ruling grants construction, coordinates, tests, or compute.
