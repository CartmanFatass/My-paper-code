# RISP-B2 same-conversation mathematical and causal closure request

Please continue the established Renewal-Indexed Score Plasticity conversation.
Review the complete prospective object below as a new, definition-only
candidate. No construction, stochastic coordinate, training, evaluation, or
partial result exists. The predecessor's complete panel was nonidentifying:
both learned recurrent architectures lacked seen competence and failed the
registered target policy-TV gate, while timing, support, causal-yoke, and
mechanism-read checks passed. The successor does not reuse predecessor data,
checkpoints, random words, or target estimates.

Return exactly one disposition on the first line:

```text
CLOSED
```

if the complete object is mathematically and causally coherent for its literal
finite claim, or

```text
REVISION_REQUIRED
```

followed by every remaining science-bearing defect, the smallest exact repair,
and the resulting claim ceiling. Mathematical closure concerns the complete
object, not implementation, code, tests, random-number addresses, compute,
portfolio priority, or deployment approval.

## Exact question and toy

The question is whether a fixed, value-aligned completed-outcome/action anchor
is a useful finite-training coordinate prior for one shared-parameter renewal
controller across externally varied skill periods. One slow controller and one
recurrent parameterization train jointly at `k in {4,8}`. The same frozen
tensors evaluate at held-out `k=12` and switches `4->12` and `12->4`; there is
no per-`k` lookup, gain, head, checkpoint, reset, or evaluation-time optimizer.
Two independent noncommunicating agents share all parameters and keep separate
episode-local fast states.

An episode has 192 primitive ticks and actions `(LEFT,HOLD,RIGHT)`. At renewal
`n`, hidden target `c_n` is not observed. `c_0` is uniform. The selected action
is held unchanged for `d_n=k_n` ticks. One outcome is drawn,

```text
P(Y_n=+1 | a_n=c_n)=3/4,
P(Y_n=+1 | a_n!=c_n)=1/4,
```

and primitive reward equals `Y_n` throughout the hold. At completion,

```text
c_(n+1)=a_n                         if Y_n=+1,
c_(n+1)=Uniform(A\{a_n})           if Y_n=-1.
```

The policy sees only `o_n=[tau_n/192,k_n/12]`. It never sees the target,
unchosen outcome, next target, future `k`, future reward, or experimenter
belief. No action, update, mask, or policy row occurs inside a hold.

The schedules are fixed `k=4`, fixed `k=8`, fixed held-out `k=12`, `4->12` at
tick 96, and `12->4` at tick 96. Fast state persists across switches. Physical-
time target endpoints average both agents over ticks `0:191` for fixed 12,
`108:191` for `4->12`, and `100:191` for `12->4`. The seed-level primary
endpoint is their equal-weight mean. The switch windows begin only after the
first new-duration hold has completed, updated state, and a later action can
consume it. Renewal-indexed curves are diagnostic only.

## Policy, state, treatment, and containing control

The shared slow head is

```text
h=tanh(Linear(8,4)(tanh(Linear(2,8)(o))))
l=Linear(4,3)(h)
z_a=6*l_a/(6+|l_a|)
w_a=16+(z_a+6)^2
pi_slow(a)=w_a/sum_b w_b.
```

It has `pi_slow(a)>1/21`. Each agent's bounded state starts at
`q_0=(1/3,1/3,1/3)` and lies in the three-simplex. The next legal action law is

```text
pi(a|o,q)=0.5*pi_slow(a|o)+0.5*q(a),
```

so every action has support above `1/42` and there is no learned fast-state
policy port.

After a completed nonterminal hold, the only runtime feedback is `s_n=Y_n`.
The stored packet is

```text
phi=[1,q,onehot(a),s,s*onehot(a),k/12,tau/192] in R^13.
```

For a positive simplex vector `v`, define

```text
chart(v)=[log(v_LEFT/v_RIGHT),log(v_HOLD/v_RIGHT)],
Simplex(z)=softmax([z_LEFT,z_HOLD,0]).
```

Let `u=(1/3,1/3,1/3)`,

```text
b(+1,a)=onehot(a),
b(-1,a)=(1-onehot(a))/2,
v(s,a)=0.75*b(s,a)+0.25*u.
```

Thus `v(+1,a)` is `(5/6,1/12,1/12)` around `a` and `v(-1,a)` is
`(1/12,11/24,11/24)`. The unique fixed `2x13` matrix `G`, zero outside the
`onehot(a)` and `s*onehot(a)` blocks, is defined by
`G*phi=chart(v(s,a))` for all six categorical pairs. The half-sum/half-
difference of the positive/negative chart vectors uniquely fixes its columns.

Both arms have one zero-initialized learned `W in R^(2x13)`:

```text
DIRECT-ANCHOR:  q_next=Simplex((G+W_A)phi)
DIRECT-CONTAIN: q_next=Simplex(W_C phi).
```

The terminal hold has no later consumer and no update. Every other completed
hold updates once before the next legal action. `G` is fixed and never trained
or decayed. Both arms execute the same packet, one fixed-plus-learned affine
path, one Simplex call, 26 learned scalars, and identical action, optimizer, and
update opportunities. The comparator's fixed matrix is zero. The recurrent
classes are exactly identical in both directions by

```text
W_C=W_A+G,
W_A=W_C-G.
```

The difference is therefore a finite coordinate/initialization/regularization
path, never capacity, information, or exclusive expressivity.

Define exact expected next-hold value from the post-outcome target belief as

```text
V(b,pi)=sum_a pi(a)*(b(a)-1/2).
```

With uniform slow policy, uniform old state, and zero residual, the positive
anchor update raises `V` over no update by exactly `1/4` and induces policy TV
`1/4`; the negative update raises `V` by exactly `1/16` and induces TV `1/8`.
For every row, holding the next observation and slow policy fixed,

```text
TV(pi_updated,pi_no_update)=0.5*TV(q_next,q_old),
DeltaV=V(b(s,a),pi_updated)-V(b(s,a),pi_no_update).
```

TV is only actuation. Positive `DeltaV` is separately required for useful
semantics.

## Timing and no future leakage

The deployable path is exactly

```text
pre-outcome history -> selected action -> completed outcome
-> local state update -> later legal action.
```

The update may use old state, selected action, completed sign, old duration,
and old boundary time. It may not use next duration, future schedule, hidden or
next target, unchosen outcome, next action, future reward/value, another
agent's outcome, or an evaluation statistic. The newly latched `k` is first
read by the later policy only after the old hold/update is complete. Evaluation
parameters are frozen.

## Outcome-history-independent control

Each update-256 checkpoint is cloned into `INTACT` and `MARGINAL-TWIN` cells.
Training is intact-only, so feedback cells have identical tensors and no
differential optimizer exposure. The twin maintains

```text
rho_n(c)=P(c_n=c | controller-visible pre-outcome history),
rho_0=uniform,
pbar_n=1/4+0.5*rho_n(a_n).
```

It independently draws a sign with positive probability `pbar_n`; only this
sign drives the twin recurrence. It never reads target, actual outcome, reward,
next target/state, unchosen action, performance, or future schedule. Because
the twin is independent of the actual lineage conditional on history/action,
observing it conveys no actual-state information, and its filter advances by

```text
rho_(n+1)(a_n)=pbar_n,
rho_(n+1)(c')=(1-pbar_n)/2 for c'!=a_n.
```

Actual outcomes still score reward and advance the actual hidden process.
Every eligible recipient boundary has one twin update; terminal holds have
none. This matches conditional sign marginals, packet/state dimension, affine
work, schedule, renewal density, and legal opportunities while removing only
realized-outcome lineage. Similar intact and twin value therefore leaves
stationary persistence and global-rate sufficiency live.

## Training and prospective sampling

There are sixteen independent algorithm-seed inference strata; concrete RNG
seeds/addresses remain deliberately unbound. Within each future stratum, arms
reuse paired slow initialization and paired environment/action tapes. No
predecessor data or stochastic object is reused.

Every learned tensor, optimizer state, forward value, state, packet, and fixed
anchor value is IEEE binary64. For each slow-policy weight, an abstract
independent integer `R_INIT` is uniform on `{0,...,2^53-1}` and
`U53=R_INIT*2^-53`; row-major initialization is
`sqrt(6/(fan_in+fan_out))*(2*U53-1)`, rounded once to binary64. All biases and
both learned recurrent matrices start at exact binary64 zero. Paired arms clone
the same slow tensors. `G` is the correctly rounded binary64 evaluation of its
declared real chart constants. Concrete finite-word conversion and RNG
addresses are intentionally unbound, but any later binding must realize this
law without an arm-specific draw or cast.

Each arm receives 256 AdamW updates, batch size 16 complete episodes, with
eight fixed-4 and eight fixed-8 episodes in alternating order. AdamW has
learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-4`
on learned scalars only, and global gradient clipping at `1.0`. There is no
held-out/switch training, early stopping, or target-selected checkpoint.

For training only, the experimenter maintains
`beta_n(c)=P(c_n=c|past selected actions and completed outcomes)`, with uniform
initial belief and `beta_(n+1)=b(Y_n,a_n)`. It never enters the policy or
runtime recurrence. For interval duration `d`, define
`B=d*sum_a pi(a)*(beta_n(a)-1/2)` and `delta=d*Y-B`. The identical arm loss is

```text
L_task=-(1/(batch*2*192))*sum
       [stopgrad(delta)*log pi(a)+0.002*d*Entropy(pi)]
L_align=mean over all eligible nonterminal agent-renewal batch rows
        of CE(v(Y,a),q_next)
L=L_task+0.25*L_align.
```

The alignment label uses only the completed outcome/action, never the hidden
or sampled next target. The full recurrence is differentiated; sampled actions,
outcomes, beliefs, residual, and target are detached. Update 256 is
conclusion-bearing. Fixed checkpoints 0,32,64,128,256 are report-only and
cannot select a model or branch.

Each seed/schedule/architecture/feedback cell receives 64 complete evaluation
episodes. Uniform and privileged hidden-state oracle controllers are
descriptive. Future event families must be independent except for declared
paired common tapes, and twins must be independent of actual outcome lineages;
no concrete coordinate binding is part of this definition-only object.

## Qualifications, estimands, and decision branches

Only the complete four-cell panel over every seed, schedule, and episode is
interpretable. Before any value conclusion, require exact treatment identity,
counts, windows, paired checkpoint cloning, no old-data reuse/leakage, one legal
update per completed nonterminal hold, no switch reset/evaluation optimizer,
containment translation, matched packet/capacity/work/exposure/support, exact
twin law/independence, finite outputs, and support above `1/42`. The real-valued
direct-TV and zero-residual anchor certificates are analytic reference
identities. Binary64 no-update forks must agree within absolute tolerance
`2^-40` for every reported probability, TV, and `DeltaV` scalar; the exact real
references are `DeltaV=1/4`, TV=`1/4` after success and `DeltaV=1/16`,
TV=`1/8` after failure.

Both INTACT architecture cells must also, at both seen durations, have a one-sided 95%
lower bound for seed-level physical-time advantage over uniform above `0.08`
and a lower bound for oracle-minus-arm headroom above `0.02`. For each
architecture, these action/value qualifications use only INTACT rows and the
actual completed sign. On seen schedules and again on the target mixture, the
one-sided 95% lower bounds must exceed: `0.25` for the fraction of eligible
rows with update TV at least `0.01`; `0.55` for the fraction with positive
`DeltaV`; and `0.005` for mean `DeltaV`. Twin rows cannot satisfy or repair
these primary qualifications. Structural violations make the panel invalid. A
complete exact panel failing competence/headroom/action/value qualifications is
nonidentifying for benefit, harm, equivalence, or deletion.

For the separately named twin diagnostic, `TV_TWIN` compares the twin-sign
update with a no-update clone. Offline scoring may use the actual recipient sign
only in

```text
DeltaV_TWIN_RECIPIENT=V(b(Y_RECIPIENT,a),pi_after_twin_update)
                       -V(b(Y_RECIPIENT,a),pi_no_update),
```

never as a twin input. A twin cell clears that diagnostic exactly when, on the
target mixture, its lower bound for physical-time advantage over uniform is
above `0.08`, its lower bound for the fraction with `TV_TWIN>=0.01` is above
`0.25`, its lower bound for the fraction with positive
`DeltaV_TWIN_RECIPIENT` is above `0.55`, and its lower bound for mean
`DeltaV_TWIN_RECIPIENT` is above `0.005`.

At each seed, average episodes inside cells/schedules, form the equal target
mixture, then paired contrasts:

```text
D_I=Q(ANCHOR,INTACT)-Q(CONTAIN,INTACT)
D_M=Q(ANCHOR,TWIN)-Q(CONTAIN,TWIN)
PSI=D_I-D_M
C_A=Q(ANCHOR,INTACT)-Q(ANCHOR,TWIN)
C_C=Q(CONTAIN,INTACT)-Q(CONTAIN,TWIN).
```

Seeds are the only inference units. Directional bounds are paired one-sided
95% Student-t bounds; equivalence uses two-sided 90% t intervals. Three
schedule nonharm bounds are each one-sided 98.333%, a Bonferroni 0.05 family.
Positive conclusions are intersection-union conjunctions.

After all prerequisites, precedence is:

1. exact-anchor harm if pooled `D_I` upper 95% is below `-0.02` or a
   simultaneous schedule upper bound is below `-0.03`;
2. realized-outcome-coupled prior support if lower bounds give `D_I>0.02`,
   `PSI>0.015`, `C_A>0.015`, the `D_M` 90% interval is inside
   `[-0.01,0.01]`, and each schedule `D_I` lower bound exceeds `-0.01`;
3. package-level direct-recurrence support without anchor specificity if both
   `C_A,C_C` lower bounds exceed `0.015` and the `D_I,PSI` 90% intervals are
   inside `[-0.01,0.01]`;
4. global-rate/outcome-independent persistence compatible if both
   architecture intact-minus-twin 90% intervals are inside `[-0.01,0.01]`
   and at least one twin cell clears the exact separately named twin diagnostic;
5. no registered minimum anchor benefit if upper 95% bounds for `D_I` and
   `PSI` are at most `0.02` and `0.015`, without harm;
6. valid unresolved otherwise.

The maximum positive claim is only the exact finite-toy, finite-budget,
registered target-mixture coordinate-prior effect dependent on realized
outcome coupling. Strong alternatives remain toy-specific handcrafted
win-stay/lose-suppress semantics, coordinate/initialization/weight-decay and
optimizer geometry, slower containing-control convergence, residual/slow-policy
cancellation, global renewal rate or stationary persistence, and high-TV but
value-negative behavior. Predecessor finite-budget training, learned transition,
and learned policy-port failure remain unresolved. A separate package-specific
SCDMP convergence explanation is not tested or displaced.

## Frozen later-probe and UAV boundaries

A later `BEST-REACHABLE-X` probe is not authorized here. Its four possible
meanings are prospectively frozen:

- old-port competence+TV reachable: retain the old port and focus repair on
  transition/training; direct bypass remains optional;
- TV reachable but competence not: retain old actuation but demote its
  semantics; keep the value-semantic direct treatment and require value, not
  TV;
- no admissible old state clears TV: delete the old learned-port branch for
  this host and retain the direct bypass, still subject to competence/value;
- TV clears without expected-value gain: delete TV-only/actuation-only
  explanations; retain only a value-bearing semantic map, deleting this
  treatment/bridge too if its structural certificate fails.

No later row may tune this treatment, thresholds, or budget.

The only UAV bridge hypothesis maps external `k` to a held macro duration. A
shared slow controller plus private bounded affinity state would update after a
completed macro using a duration-correct local advantage sign and affect only
the next macro. A UAV science object would still need safe macro semantics,
changing masks, mask-aware normalization, deployable critic, local/team credit,
delays, wind/link effects, coordination stability, safety overrides, matched
controls, and physical-time mission value. The toy's exact next-target rule is
generally false for UAVs and can turn the anchor into high-TV harm.

Please scrutinize especially: whether the fixed `G` is truly value-bearing yet
function-equivalent to the comparator; whether the marginal twin is well
defined and severs only realized lineage; whether the auxiliary label or twin
creates leakage or over-determines the result; whether the competence/action-
value gates and branch logic identify the literal claim; and whether the
four-outcome and UAV ceilings prevent policy-port, convergence, arbitrary-`k`,
or deployment overclaim. Name the strongest remaining alternative and the
single highest-information post-result discriminator in either disposition.
