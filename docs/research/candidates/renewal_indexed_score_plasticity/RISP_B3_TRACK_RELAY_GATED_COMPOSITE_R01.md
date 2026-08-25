# RISP-B3 target-bound tracking/relay G-gated composite

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B3-TRG
science_revision=RISP-B3-TRG-SCIENCE-20260815-01
named_target=TRI-SECTOR-DELAYED-ACK-TRACK-RELAY
owner=/root/em_renewal_indexed_score_plasticity
paired_cm=/root/cm_renewal_indexed_score_plasticity
definition_authority=RISP-TARGET-BOUND-COMBINED-SUCCESSOR-DEFINITION
scientific_activity_started=false
construction_authorization=none
source_change_authorization=none
test_or_probe_authorization=none
stochastic_coordinate_binding=none
training_evaluation_compute_authorization=none
old_object_rerun_authorization=none
standalone_transplant_authorization=none
sign_reversed_center_authorization=none
```

## Decision question and why frozen-G exploitability is necessary

This object asks one target-bound question: in a delayed-acknowledgment
tracking/relay task with an externally imposed skill-hold duration `k`, does a
fixed completed-recipient-outcome/action coordinate prior help one shared
recurrent controller retain physical-time relay value at a held-out duration
and after duration switches, relative to a literally function-equivalent
containing recurrence and to outcome-lineage-independent fixed/global
alternatives?

The object is deliberately indivisible. It contains a registered
`CONTAIN-G-BOUND` cell that freezes the newly trained containing arm's slow
checkpoint and evaluates the exact fixed matrix `G` inside that same target,
on the same complete prospective panel as the matched held-out/switched-`k`
value comparison. `CONTAIN-G-BOUND` is not a standalone checkpoint transplant,
an old-checkpoint assay, or an independent success route. Its only role is a
decision-necessary gate:

- if the frozen containing slow controller cannot exploit exact `G` to become
  competent, action-sensitive, value-aligned, and physically valuable against
  the registered fixed/global alternatives on seen and target schedules, the
  outcome-coupled recurrence component is deleted for this named target and
  finite package;
- if it can, interpretation proceeds immediately to the already computed
  function-equivalent anchor-versus-containing value comparison in the same
  complete panel. No second activity or adaptive coordinate is opened.

Thus a positive exploitability result cannot stand alone, and a negative
result cannot merely request another transplant. The gate decides whether the
named target has a usable direct outcome-affinity substrate; the matched value
cells then decide whether the fixed `G` coordinate prior and realized recipient
lineage add value beyond containing, no-lineage, fixed-persistence, and
global-rate alternatives.

One slow controller and one recurrent parameterization per architecture are
trained jointly at `k in {4,8}`. The same frozen tensors run at held-out
`k=12` and external switches `4->12` and `12->4`. Parameters are shared by both
agents and every duration. There is no per-`k` head, table, gain, checkpoint,
reset, or evaluation optimizer; each agent retains only its own episode-local
fast state.

The maximum positive claim is limited to this exact finite two-agent target and
package: a value-aligned completed-ACK/action coordinate prior improves the
registered physical-time held-out/post-switch value over a function-equivalent
zero-centered recurrence, both qualified recurrent arms outperform their
matched no-recurrence/fixed/global alternatives, and the anchor advantage
depends on actual recipient ACK lineage relative to the conditional-marginal
twin. It is not a claim of exclusive expressivity, convergence, arbitrary
`k`, learned duration selection, variable `N`, multi-agent coordination, real
UAV transfer, safety, or deployment value.

## Named tri-sector delayed-ACK tracking/relay target

There are exactly two parameter-sharing, noncommunicating relay agents. Each
serves an independent moving target and recipient, so this object makes no
coordination or team-credit claim. An episode lasts `T=192` primitive ticks.
The three relay-beam actions are

```text
A = (LEFT_SECTOR, CENTER_SECTOR, RIGHT_SECTOR).
```

At a legal renewal boundary `tau_n`, agent `i` has a hidden current target
sector `c_i,n in A`. The controller observes only

```text
o_n = [tau_n/T, k_n/12]
```

and selects one beam `a_i,n`, which is held unchanged for the next externally
specified `k_n` ticks. The current hold cannot be interrupted. During each
primitive tick the hidden target drifts independently of the selected beam
according to the fixed symmetric physical kernel

```text
P(c_(t+1)=c_t)       = 23/24
P(c_(t+1)=each other)= 1/48.
```

Let `P_k=P^k`. The hidden sector at hold completion is
`c_i,n+1 ~ P_k(c_i,n,.)`. One recipient ACK is then drawn:

```text
P(Y_n=+1 | a_n=c_(n+1))  = 4/5
P(Y_n=+1 | a_n!=c_(n+1)) = 1/5.
```

The completed hold has time-weighted utility `k_n*Y_n`. The recipient ACK and
that utility are unavailable to the controller until the hold has completed.
At completion, the ACK may update the private recurrence before the next legal
action. The hidden completion sector becomes the next boundary sector; it is
never observed by the policy. The drift kernel is reward-independent and
action-independent: an action tracks the target but does not move it.

This is a bounded tracking/relay abstraction with a physical reason for
external-`k` sensitivity. Longer holds allow more target drift before a packet
deadline and reduce the predictive persistence of the last completed ACK. The
per-tick kernel has nontrivial eigenvalue

```text
lambda = 15/16,
P_k(c,c)=1/3+(2/3)*lambda^k,
P_k(c,c')=(1/3)*(1-lambda^k) for c'!=c.
```

No outcome, reward, fast state, mask, or policy row changes inside a hold. The
policy never receives the hidden sector, an unchosen ACK, future `k`, future
reward, another agent's outcome, or an experimenter belief.

The five schedules and roles are:

| id | schedule | role | decisions | nonterminal updates |
|---:|---|---|---:|---:|
| 0 | fixed `k=4` | seen qualification | 48 | 47 |
| 1 | fixed `k=8` | seen qualification | 24 | 23 |
| 2 | fixed `k=12` | held-out target | 16 | 15 |
| 3 | `k=4` on `[0,96)`, then `k=12` | target switch | 32 | 31 |
| 4 | `k=12` on `[0,96)`, then `k=4` | target switch | 32 | 31 |

At `t=96`, the old hold completes, its target motion and ACK are resolved, and
its recurrence update is final before the new duration is latched and the next
policy is queried. The update cannot read the new duration. The target windows
exclude the first completed hold under the new duration because its action had
not yet received an outcome generated under that duration:

For a window `W` of primitive ticks, include only holds fully contained in
`W` and define `Q(W)=(1/(2*|W|))*sum_i sum_n k_n*Y_i,n`. Therefore

```text
Q(12)    uses W={0,...,191}
Q(4->12) uses W={108,...,191}
Q(12->4) uses W={100,...,191}.
```

The seed-level target endpoint is

```text
Q_TARGET = (Q(12)+Q(4->12)+Q(12->4))/3.
```

Full-switch values, excluded first-new-duration holds, renewal-indexed curves,
ACK rates, entropy, and target occupancy are diagnostic only. No renewal count
or per-decision score can replace the physical-time endpoint.

## Shared slow policy and private direct state

Every learned arm uses the same bounded slow head:

```text
h_n      = tanh(Linear(8,4)(tanh(Linear(2,8)(o_n))))
l_base   = Linear(4,3)(h_n)
z_a      = 6*l_base,a/(6+|l_base,a|)
w_a      = 16+(z_a+6)^2
pi_slow(a|o_n) = w_a/sum_b w_b.
```

Each agent has private state `q_i,0=(1/3,1/3,1/3)` in the closed three-simplex.
It persists across duration switches. The deployed action law is

```text
pi(a|o_n,q_n) = (1/2)*pi_slow(a|o_n) + (1/2)*q_n(a).
```

For finite rational `r in Q^3`, define the common exact-rational head

```text
z_a(r)        = 6*r_a/(6+|r_a|)
omega_a(r)    = 16+(z_a(r)+6)^2
Affinity(r)_a = omega_a(r)/sum_b omega_b(r).
```

Every action probability is strictly greater than `1/21`. At selection the
controller stores only `(q_n,a_n,k_n,tau_n)`. After the hold completes, its
legal ACK sign is `s_n=Y_n`, and the common 13-vector is

```text
phi_n = [1,
         q_n(LEFT),q_n(CENTER),q_n(RIGHT),
         onehot(a_n)_LEFT,onehot(a_n)_CENTER,onehot(a_n)_RIGHT,
         s_n,
         s_n*onehot(a_n)_LEFT,
         s_n*onehot(a_n)_CENTER,
         s_n*onehot(a_n)_RIGHT,
         k_n/12,
         tau_n/T].
```

The terminal hold has no later consumer and creates no update. Every other
completed hold creates exactly one update before the next action.

## Frozen G and direct-value certificate

The exact frozen semantic raw maps are unchanged in meaning:

```text
g(+1,a)_j = +30 if j=a, else -30
g(-1,a)_j = -30 if j=a, else   0
v(s,a)    = Affinity(g(s,a)).
```

There is one unique binary64 matrix `G in R^(3x13)`, zero outside the two
action-categorical blocks, satisfying `G*phi=g(s,a)` for all six categorical
pairs. Its entries are only `-30,-15,0,+30`. Exact affinity masses are

```text
v(+1,a): 137/171 on a, 17/171 on each alternative
v(-1,a):  17/121 on a, 52/121 on each alternative.
```

Under a uniform current-sector prior, the completed ACK posterior is

```text
P(c_completion=a | Y=+1,a)=2/3; alternatives=1/6 each
P(c_completion=a | Y=-1,a)=1/9; alternatives=4/9 each.
```

With uniform slow policy and old state, the fixed `G` update changes the next
policy by TV `40/171` after success and `35/363` after failure. If the next
hold has public duration `k`, define exact offline next-hold value

```text
V_k(b,pi) = sum_a pi(a)*[-3/5 + (6/5)*(b*P_k)(a)].
```

Then the local value gains over the no-update policy are exactly

```text
DeltaV_G(+1,k) = (8/57)*(15/16)^k
DeltaV_G(-1,k) = (14/363)*(15/16)^k.
```

They are strictly positive for all registered `k`, including held-out `12`.
This proves that `G` is prospectively value-bearing in a local registered
state; it does not guarantee global physical-time value or competence. Those
are the decision-necessary empirical gates inside this object.

For any eligible row, the no-update fork carries `q_n` while holding the next
observation and slow policy fixed. Define

```text
TV_update = TV(pi_updated,pi_no_update)
DeltaV_update = V_(k_next)(b_(n+1),pi_updated)
                - V_(k_next)(b_(n+1),pi_no_update),
```

where `b_(n+1)` is the exact experimenter posterior for the hidden sector after
the actual completed recipient ACK. `k_next` is used only for offline scoring
after the complete trajectory exists; it is never an update or policy input.
TV certifies motion, while positive `DeltaV` certifies target-aligned motion.

## Function-equivalent treatment and containing recurrence

Both learned architectures deploy one effective matrix
`E in R^(3x13)`:

```text
TRACK-G-ANCHOR: q_(n+1)=Affinity(E_A*phi_n)
TRACK-CONTAIN:  q_(n+1)=Affinity(E_C*phi_n).
```

`E_A=G` and `E_C=0` at initialization. Each has 39 trainable binary64 scalars,
and each deployed domain is literally every finite binary64 `3x13` matrix.
They use the same packet, matrix-vector order, affinity head, slow controller,
action mixture, parameter count, loss, batch order, optimizer work, update
count, legal update opportunities, and reset law. Their only fixed difference
is initialization and centered decay: `E_A` begins and decays about `G`, while
`E_C` begins and decays about zero. The two function classes are equal; the
question concerns a finite coordinate/regularization prior, not capacity.

No RISP-B1 or RISP-B2 checkpoint, optimizer state, seed, random word, partial
value, threshold outcome, or result is reused. The target dynamics, training,
and all evaluation coordinates would be prospectively new.

## One integrated G-exploitability gate

`CONTAIN-G-BOUND` is an evaluation-only cell in this same complete object. It
clones the final `TRACK-CONTAIN` slow-policy checkpoint and reset state, ignores
its learned `E_C`, and applies the exact fixed `G` update after each actual
completed recipient ACK. There is no fitting, checkpoint choice, target-result
selection, old checkpoint, or parameter update.

For that same containing slow checkpoint, three matched outcome-independent
alternatives are also complete evaluation cells:

```text
CONTAIN-NO-RECURRENCE:
    q_(n+1)=q_n.

CONTAIN-FIXED-PERSIST:
    q_(n+1)=v(+1,a_n), ignoring Y_n.

CONTAIN-GLOBAL-RATE:
    p0=2/5,
    q_(n+1)=Affinity(p0*g(+1,a_n)+(1-p0)*g(-1,a_n)), ignoring Y_n.
```

`p0=2/5` is the exact stationary ACK-success probability under a uniform
sector/action law. These cells have the same slow checkpoint, action mixture,
update opportunities, schedule, and causal timing. They distinguish no
recurrence, fixed selected-action persistence, and a global marginal-rate
update from actual completed-recipient lineage. They are alternatives, not
capacity-matched substitutes for `TRACK-CONTAIN`; the latter is the literal
function-equivalent comparator.

For seed `s` and schedule `h`, freeze the strongest matched alternative

```text
Q_C,BEST(s,h)=max(Q_C,NO(s,h),Q_C,FIXED(s,h),Q_C,GLOBAL(s,h)).
```

The within-seed maximum is prospective and cannot select a treatment or
threshold. `CONTAIN-G-BOUND` clears exploitability only if, at each seen
schedule separately and on the registered target mixture:

1. the one-sided 95% lower bound for
   `Q_C,G-BOUND-Q_C,BEST` exceeds `0.02`;
2. on seen schedules the one-sided 95% lower bound for
   `STATE-ORACLE-Q_C,G-BOUND` exceeds `0.02`;
3. the lower bound on the fraction of eligible updates with
   `TV_update>=0.01` exceeds `0.25`;
4. the lower bound on the fraction with `DeltaV_update>0` exceeds `0.55`; and
5. the lower bound on mean `DeltaV_update` exceeds `0.005`.

Every component is conjunctive. Target summaries give the three target
schedules equal seed-level weight. If any component fails, interpretation ends
at `NAMED_TARGET_RECURRENCE_DELETED_G_UNEXPLOITABLE`; the held-out value
contrasts remain descriptive and cannot open a separate transplant or
recurrence repair. If every component passes, the already complete matched
value comparison below is interpreted immediately.

## No-lineage and fixed/global alternatives for both learned arms

Each learned final checkpoint is cloned into `INTACT` and `MARGINAL-TWIN`.
`INTACT` uses the actual recipient ACK. The twin never reads the recipient
hidden sector, actual ACK, reward, next state, performance, or future schedule.

Let `rho_n` be the exact experimenter belief over the hidden sector at the
start of a twin hold, conditional only on that twin controller's visible
history. Before the ACK, compute

```text
mu_n = rho_n*P_(k_n)
pbar_n = 1/5 + (3/5)*mu_n(a_n).
```

Draw the twin sign independently from `Bernoulli(pbar_n)` in `(+1,-1)` order,
and feed only that sign to the recurrence. The actual recipient ACK still
scores utility and the actual completion sector still becomes the next hidden
sector. Because the twin sign is conditionally independent of the actual
sector and ACK, the twin filter advances only by physical motion:

```text
rho_(n+1)=rho_n*P_(k_n).
```

Thus the twin preserves the one-step conditional ACK law and every legal
update opportunity while severing realized recipient lineage. It does not
preserve every serial dependence; equal intact and twin value leaves
outcome-independent persistence and global-rate sufficiency live.

Each learned architecture also receives matched `NO-RECURRENCE`,
`FIXED-PERSIST`, and `GLOBAL-RATE` evaluation clones using its own frozen slow
checkpoint and the equations above. For architecture `X in {A,C}`, define the
prospective per-seed best alternative `Q_X,BEST` as their within-seed maximum.
These controls cannot create a positive route. They must be beaten when a
claim attributes value to learned outcome recurrence.

`UNIFORM` uses exact action mass `1/3`. `STATE-ORACLE` observes only the hidden
sector at the start of the hold and assigns `29/30` to that sector and `1/60`
to each alternative; it has no recurrence or learning. The physical drift
still occurs, so the oracle is a headroom control rather than perfect value.

## Frozen training package

There are sixteen prospective independent algorithm-seed strata. Numeric
seeds, RNG algorithms, addresses, and concrete product coordinates remain
unbound. The two learned arms within a stratum reuse paired slow-policy
initialization and paired training event tapes. Different strata are
independent.

Each architecture receives exactly 512 AdamW updates, batch size 16 complete
two-agent episodes, with eight fixed-`k=4` and eight fixed-`k=8` episodes in
alternating order. There is no `k=12` or switch training. The final update 512
is conclusion-bearing; updates `0,64,128,256,512` are report-only and cannot
select a model, threshold, branch, or new coordinate.

AdamW uses learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, global
gradient clipping `1.0`, and decoupled weight decay `1e-4`. Slow weights decay
about zero. Recurrent effective matrices use identical arithmetic but their
declared centers:

```text
E_arm <- C_arm + (1-lr*1e-4)*(E_arm-C_arm) - lr*AdamDirection_arm
C_A=G; C_C=0.
```

All trainable tensors, gradients, and optimizer states are binary64. Slow
weights use the same prospectively finite-grid symmetric initialization in both
arms; biases begin at zero. The action and affinity probabilities are exact
rationals after the common bounded head.

For the training baseline, let `beta_n` be the exact experimenter belief over
the hidden sector at a boundary given the actual controller-visible completed
ACK history. For proposed action `a` and duration `k`, the expected hold ACK is

```text
EY(beta,k,a) = -3/5 + (6/5)*(beta*P_k)(a).
```

After motion, let `mu=beta_n*P_(k_n)`. The exact posterior used only by the
training baseline is

```text
beta_(n+1)(j) proportional to
    mu(j)*(4/5 if j=a_n else 1/5), when Y_n=+1
    mu(j)*(1/5 if j=a_n else 4/5), when Y_n=-1.
```

It is normalized exactly and never enters the policy or recurrence.

For a batch, define

```text
B_n     = k_n*sum_a pi_n(a)*EY(beta_n,k_n,a)
delta_n = k_n*Y_n-B_n.
```

The common loss is

```text
L_task = -(1/(16*2*T))*sum_n
           [stopgrad(delta_n)*log pi_n(a_n)
            +0.002*k_n*Entropy(pi_n)]

L_align = mean CE(v(Y_n,a_n),q_(n+1))
          over eligible nonterminal agent-renewal rows

L = L_task + L_align.
```

The alignment weight is fixed at `1` to give the containing arm a prospective
direct learning signal toward the exact registered semantic region after the
predecessor's finite-dose nonidentification. It is identical in both arms and
cannot change after any new activity. The target uses only the selected action
and completed ACK; it never receives the hidden sector or future duration.
Complete-episode recurrence is differentiated; sampled actions, motion, ACKs,
beliefs, residuals, and targets are detached.

Evaluation uses 64 complete episodes for every seed, schedule, and registered
cell. The 13 conclusion-bearing cell families are:

```text
2 architectures x {INTACT,MARGINAL-TWIN,NO-RECURRENCE,
                   FIXED-PERSIST,GLOBAL-RATE} = 10
CONTAIN-G-BOUND                                  = 1
UNIFORM + STATE-ORACLE                          = 2.
```

The prospective workload is 262,144 two-agent training episodes and 66,560
two-agent evaluation episodes, all length 192. These counts define scientific
coverage only; they authorize no construction or compute.

## Abstract paired stochastic law without coordinate binding

For every complete abstract event identity `e`, let `U[e]` be an independent
ideal uniform generated by a lazy infinite Bernoulli bit tape. Event identities
include

```text
(algorithm_seed, phase, update_or_schedule, episode, agent, renewal,
 event_kind)

event_kind in {INIT_MODEL,INIT_SECTOR,ACTION,MOTION,ACK,TWIN}.
```

Unequal identities are independent. Every categorical draw uses a literal
inverse CDF and the displayed action/sector order. `MOTION` applies exact
`P_k`; `ACK` applies the exact `4/5` or `1/5` law. Within a seed, corresponding
learned arms and evaluation cells reuse base initialization, sector, action,
motion, and ACK tapes prospectively. Each cell applies the common uniform to
its own policy or conditional law; divergent actions never shift another event
family. Twin cells alone consume the independent `TWIN` family, paired across
architectures at the same abstract event identity.

No concrete random word, seed number, generator, address, finite-word
conversion, checkpoint, or coordinate is bound here. A later materialization
would have to preserve the full identities, independence, reuse relations, and
inverse-CDF orders exactly and use no old RISP coordinate.

## Complete-panel validity and qualifications

Only the complete 16-seed, five-schedule, 13-cell panel can support any branch.
Partial seeds, cells, schedules, checkpoints, learning curves, or values have
no interpretation or selection path. Every conclusion first requires:

1. exact target dynamics, duration schedules, physical windows, action order,
   checkpoint cloning, abstract coupling, and complete counts;
2. no hidden sector, actual ACK in twin, future duration, future reward, or
   cross-agent leakage; completed holds precede every update and every update
   precedes the next legal action;
3. literal equality of the two learned effective-matrix domains, equal 39
   recurrent scalars, common packet/head/loss/work/update opportunities, and
   only the declared initialization/center difference;
4. finite stored values, exact support above `1/21`, exact rational
   normalization, correct no-update forks, correct posterior/value rows, and
   exact zero-residual structural references for both ACK signs and all three
   registered durations;
5. the complete `CONTAIN-G-BOUND` exploitability gate above;
6. both learned `INTACT` arms clear seen competence at `k=4` and `k=8`
   separately: the one-sided 95% lower bound for `Q_X,I-Q_X,BEST` exceeds
   `0.02`, and the lower bound for `STATE-ORACLE-Q_X,I` exceeds `0.02`;
7. for each learned architecture on each seen schedule separately and on the
   equal-weight target mixture, the one-sided 95% lower bounds exceed `0.25`
   for the fraction with `TV_update>=0.01`, `0.55` for the positive-`DeltaV`
   fraction, and `0.005` for mean `DeltaV_update`; and
8. all primary action/value rows use actual completed recipient ACKs. Twin,
   fixed, global, and oracle cells cannot repair an intact qualification.

Items 1--4 failing yield `INVALID_IMPLEMENTATION_OR_PANEL`. Item 5 failing
yields the prospective deletion branch for this named target. Items 6--8
failing after item 5 passes yield
`G_EXPLOITABLE_BUT_MATCHED_VALUE_NONIDENTIFYING`; the G gate remains a bounded
diagnostic fact, but no value or lineage claim follows.

For row qualifications, every eligible two-agent renewal row has equal weight
within seed and schedule. Seen rows are all nonterminal updates. Target rows
are only updates whose affected next action begins within the registered `Q`
window. Target seed summaries average the three schedule summaries equally.
All bounds are one-sample Student-`t` bounds over sixteen seed summaries with
`df=15`.

## Seed-first estimands and branch map

For every architecture `X`, feedback/control cell `f`, seed, and schedule,
first average complete episodes. Form the equal-weight target mixture, then
paired seed contrasts. Define

```text
D_I = Q(A,INTACT)-Q(C,INTACT)
D_M = Q(A,TWIN)-Q(C,TWIN)
PSI = D_I-D_M
C_A = Q(A,INTACT)-Q(A,TWIN)
C_C = Q(C,INTACT)-Q(C,TWIN)
R_A = Q(A,INTACT)-Q(A,BEST)
R_C = Q(C,INTACT)-Q(C,BEST).
```

Directional bounds are one-sided 95% Student-`t` bounds. Equivalence uses
two-sided 90% intervals. Three schedule-specific nonharm statements use
one-sided 98.333% bounds. Harm uses its explicitly family-corrected upper
bounds. Every positive statement is a conjunction.

After validity and qualification precedence, use this complete branch map:

1. **`NAMED_TARGET_RECURRENCE_DELETED_G_UNEXPLOITABLE`.** The integrated
   `CONTAIN-G-BOUND` gate fails any seen or target competence, action-TV, or
   value-alignment component. Delete completed-ACK direct recurrence from
   `TRI-SECTOR-DELAYED-ACK-TRACK-RELAY` under this controller, duration family,
   and package. Do not create a standalone transplant, sign-reversed center,
   or UAV bridge from this outcome. This is not deletion of outcome recurrence
   generally.
2. **`G_EXPLOITABLE_BUT_MATCHED_VALUE_NONIDENTIFYING`.** The G gate passes but
   either learned intact architecture fails a registered competence/action/
   value qualification. Report the gate and observations only. Retain no
   matched value, lineage, prior, or deletion claim.
3. **`NAMED_TARGET_G_CENTERED_TREATMENT_HARM`.** With all gates passed, a
   four-member family fires if the one-sided 98.75% upper bound for pooled
   `D_I` is below `-0.02`, any schedule-specific upper bound is below `-0.03`,
   or the target-mixture upper bound for `R_A` is below `-0.02`. Delete the
   G-centered learned recurrence treatment for this named target/package. Do
   not delete the containing function class or generic recurrence.
4. **`TARGET_EXTERNAL_K_REALIZED_ACK_G_PRIOR_SUPPORTED`.** Require lower bounds
   `D_I>0.02`, `PSI>0.015`, `C_A>0.015`, `R_A>0.02`, and `R_C>0.02`; require
   the 90% interval for `D_M` inside `[-0.01,0.01]`; and require every
   schedule-specific `D_I` lower bound above `-0.01`. This supports only the
   maximum finite target claim stated above.
5. **`TARGET_DIRECT_RECURRENCE_VALUE_WITHOUT_G_PRIOR_SPECIFICITY`.** Require
   lower bounds `R_A>0.02`, `R_C>0.02`, `C_A>0.015`, and `C_C>0.015`, while
   the 90% intervals for `D_I`, `D_M`, and `PSI` all lie inside
   `[-0.01,0.01]`. Retain realized-ACK direct recurrence for the target, but
   delete fixed-G-centered prior specificity.
6. **`TARGET_NO_REALIZED_LINEAGE_OR_FIXED_GLOBAL_ALTERNATIVE_COMPATIBLE`.** This
   branch fires under either one of two prospectively separate conjunctions:
   (a) both intact-minus-twin 90% intervals lie inside `[-0.01,0.01]` and both
   twin arms themselves clear the target competence/action/value gates; or
   (b) the 90% interval for `Q(A,INTACT)-Q(A,BEST)` lies inside
   `[-0.01,0.01]`, while the best-control composite itself clears the seen and
   target physical competence and oracle-headroom gates. Delete the
   realized-recipient-lineage claim and modify the target controller toward
   the sufficient twin or fixed/global alternative named by the firing
   conjunction; do not claim that all recurrence is unnecessary.
7. **`NO_REGISTERED_MINIMUM_G_PRIOR_VALUE`.** With no harm branch, the
   one-sided 95% upper bounds for both `D_I` and `PSI` are at most `0.02` and
   `0.015`. Delete only the registered minimum G-prior and interaction claims
   for this package. Any direct-recurrence value must be established by branch
   5 rather than inferred here.
8. **`VALID_UNRESOLVED`.** Every prerequisite passes but no preceding branch is
   established. Preserve the exact observations and claim ceiling without a
   new treatment or result-selected threshold.

Branches are evaluated in the displayed order after the invalid-panel check.
No checkpoint, cell, control, schedule, seed, or branch can be selected after
observation.

## Strongest alternatives and exact claim ceiling

Even branch 4 cannot isolate outcome meaning from generic shifted
initialization, nonzero centered decay, alignment-loss geometry, conditioning,
or slower finite convergence of the containing arm. The integrated G gate
shows only that the target substrate can use the map; it does not prove why the
trained anchor reached it. Fixed selected-action persistence, stationary global
ACK rate, conditional marginal ACKs, target autocorrelation, and slow-policy
co-adaptation remain live until the registered controls exclude them.

The target is still a bounded abstraction. Its symmetric drift, three fixed
beam sectors, delayed binary ACK, independent agents, absence of masks and
interference, and time-weighted packet utility do not establish a real relay
mission. A real UAV system would add continuous geometry, occlusion, link
quality, collision and energy constraints, team credit, safety overrides, and
possibly nonstationary recipient feedback. No branch proves transfer.

A negative G gate deletes only the recurrence component for the exact named
target/controller/package. A harm branch deletes only the G-centered learned
treatment there. A fixed/global or twin-compatible branch deletes only actual
recipient-lineage specificity. No outcome deletes generic outcome recurrence,
the equal function class, arbitrary future treatments, or another direction.

## Definition-only activity boundary

This file freezes a prospective scientific object and nothing else. No source
may be created or changed; no runner, build, test, probe, seed, random word,
coordinate, checkpoint, training episode, evaluation episode, partial value,
lease, or compute may be created or accessed. RISP-B2 remains complete and
immutable and is not rerun. `CONTAIN-G-BOUND` cannot be split from this object,
and no sign-reversed center, second surface, cross-`N x k` parent, or UAV action
is authorized.

The existing RISP ChatGPT Pro and Gemini conversations may receive only their
independently frozen science questions. Pro mathematical closure, EM intake,
and same-direction CM static bindability/observability/comparator/cost review
are required before this object can return to Root. None authorizes empirical
activity.
