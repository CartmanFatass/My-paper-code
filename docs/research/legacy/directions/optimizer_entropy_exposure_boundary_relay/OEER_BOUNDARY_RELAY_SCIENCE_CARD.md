# Optimizer-Entropy-Exposure Boundary Relay science card

Owner: `direction:optimizer-entropy-exposure-boundary-relay` Explorer Manager  
Candidate: `CAND-OPTIMIZER-ENTROPY-EXPOSURE-BOUNDARY-RELAY`  
Treatment: `OEER-B1-BOUNDARY-RELAY-v1`

## Question and causal object

At one common parameter-and-data boundary, does carrying nonempty Adam state make
a one-step entropy gradient leave a persistent learning effect that cannot be
explained by the resulting first parameter displacement alone, and is either the
displacement channel or the hidden-state channel additionally amplified when the
learner's actions choose its future training exposure?

This is a new prospective toy-host question. VSP02, G52, and G53 motivated only the
shared unknown and interface shape. Their rows, thresholds, conclusions, code
acceptance, and evidence are not inputs. The parameter and optimizer state below are
hand-specified scientific starting objects, not reconstructions of any prior run.

The treatment is the complete relay, with these orthogonal interventions:

- optimizer memory `M in {CARRY, RESET}`;
- first-update entropy `E in {PULSE, ZERO}`;
- future exposure `X in {YOKED, SELF}`; and
- for every observed `(M,E)` first displacement, an exactly paired `DELTA_MATCH`
  continuation with the same post-update parameters and common fresh Adam.

`RESET/ZERO/YOKED` is the factorial reference. `RESET` removes the inherited Adam
moments and step count; `ZERO` removes only the entropy coefficient while retaining
the entropy calculation in the same graph; `YOKED` cuts the action-to-next-cue
edge. `DELTA_MATCH` distinguishes parameter mutation from optimizer-state history.
Four sign-balanced `GENERIC` shadows provide the strongest planned alternative:
an arbitrary same-size early parameter kick amplified by this root/tape-specific
basin.

## Four-root host and fixed cue panel

A cue is `(q,n) in [-1,1]^2`. The four training roots are the corners
`(-1,-1)`, `(-1,+1)`, `(+1,-1)`, and `(+1,+1)`. `q=+1` has correct action
`PROBE`; `q=-1` has correct action `HALT`. Thus there are two roots of each action,
and every `(q,n)` has the sign mirror `(-q,-n)` with the opposite correct action.
`n` is a payoff-irrelevant nuisance coordinate.

The policy has four trainable corner logits, ordered as the roots above. For any
cue, its PROBE logit is the bilinear interpolation

`z_theta(q,n) = sum_(a,b in {-1,+1}) theta[a,b] (1+a*q)(1+b*n)/4`,

and `p_theta(PROBE|q,n)=sigmoid(z_theta(q,n))`. At a root, exactly one corner
logit is active. An action earns `+1` when correct and `-1` otherwise. After the
action, the host reveals the correct action, and learning minimizes its binary
cross-entropy. This is deliberately a full-feedback online policy toy, not a claim
to reproduce a production actor-critic.

The held-out panel is the 20 interior cues in
`q in {-0.8,-0.4,+0.4,+0.8}` crossed with
`n in {-0.8,-0.4,0,+0.4,+0.8}`. None is a training root. The panel is fixed before
any arm exists, never supplies an update, and is evaluated deterministically from
action probabilities.

## Common boundary object and immutable first batch

All arms start from exactly the same

- `theta0 = (-0.24,-0.12,+0.12,+0.24)`;
- Adam first moment `m0 = (+0.06,+0.02,-0.02,-0.06)`;
- Adam second moment `v0 = (0.0100,0.0025,0.0025,0.0100)`; and
- Adam step count `t0=12`.

The state is nonempty and sign-balanced: mirrored HALT/PROBE coordinates have
opposite first moments and equal second moments. Adam uses learning rate `0.02`,
`beta1=0.9`, `beta2=0.999`, `epsilon=1e-8`, ordinary bias correction, no AMSGrad,
and no weight decay.

`B0` is immutable and contains each of the four roots exactly once with its correct
action target and weight `1/4`. Define

`L_beta(theta;B0) = mean_B0 BCE(target,p_theta) - beta * mean_B0 H(p_theta)`.

Both BCE and binary entropy use natural logarithms, with
`H(p)=-p*log(p)-(1-p)*log(1-p)`. For gradient `g`, Adam increments `t` first and
uses `m'=beta1*m+(1-beta1)*g`, `v'=beta2*v+(1-beta2)*g^2`,
`mhat=m'/(1-beta1^t)`, `vhat=v'/(1-beta2^t)`, and
`theta'=theta-0.02*mhat/(sqrt(vhat)+1e-8)`, elementwise.

`PULSE` takes one Adam step on `L_0.01`. `ZERO` takes one step through the identical
operations on `L_0.00`: the entropy tensor is computed and connected, then
multiplied by the numeric coefficient `0.0`. `CARRY` begins that step from
`(m0,v0,t0)`; `RESET` begins from `(0,0,0)`. No arm label is a model input.

For each main cell, record

`Delta[m,e] = theta1_MAIN[m,e] - theta0`

and the complete post-step Adam state. The assignment-scoped scientific object is
the standard mathematical Adam update; a framework implementation may use ordinary
floating arithmetic.

## First-step mutation barrier and shadows

Before the four main first steps, materialize `theta0`, the common Adam state,
`B0`, the held-out panel, and every future exogenous tape. Between arm cloning and
completion of all four first steps there is no action draw, environment transition,
future-cue read, validation, selection, restart, or arm-specific data access.
Continuation cannot begin until all four deltas have been recorded.

For every `(m,e)`, `DELTA_MATCH[m,e]` is then made by direct parameter assignment:

`theta1_DELTA_MATCH[m,e] = theta0 + Delta[m,e]`.

Every such shadow receives the same fresh future Adam state `(m=0,v=0,t=0)`. The
direct assignment does not itself advance Adam or create moments. Therefore a main
cell and its shadow have the same first post-boundary policy, while only the main
cell retains optimizer state produced by or carried through the boundary update.
This is the mutation barrier; replacing it with a calibrated pseudo-gradient would
change the treatment because it would also create shadow moments.

Categorical objects and root identities must agree exactly. Ordinary floating
comparisons use `rtol=1e-6, atol=1e-8`. A delta match is adequate when every
coordinate differs from its target by at most
`1e-8 + 1e-6*max(1,abs(Delta_coordinate))` and held-panel probabilities agree to
`1e-6`. These are implementation tolerances, not scientific effect thresholds; no
bitwise float identity, hash, or serialized-byte condition is part of the science.

## Future exposure dynamics

Each continuation starts at one of the four roots and takes 64 online updates.
At future step `j`, the current policy first samples PROBE iff a common exogenous
uniform `u_j < p_theta(PROBE|root_j)`. Reward and correct action are revealed, one
Adam step is taken on single-root BCE with the same-graph entropy coefficient
`0.0`, and then the next root is chosen.

- `YOKED`: the 64 current roots come from a precommitted arm-independent tape.
  Each consecutive four-root block is a permutation containing every root once,
  and the first entry is the assigned start root. The same root tape is used by all
  main, matched, and generic cells for a given `(master_seed,start_root)`. Actions
  cannot alter it.
- `SELF`: the next root has `q=+1` after PROBE and `q=-1` after HALT. Its nuisance
  sign is the next common exogenous nuisance bit. Thus action changes only the
  future cue/exposure, not the reward rule, optimizer, or current update.

Random draws are counter-keyed by `(master_seed,start_root,step,kind)`, so divergent
trajectories cannot shift later RNG consumption. Main, matched, generic, YOKED, and
SELF branches see the same coordinate-wise action uniforms and nuisance bits. For
the mirror-root pairs `(+1,+1)<->(-1,-1)` and
`(+1,-1)<->(-1,+1)`, action uniforms are antithetic (`u` versus `1-u`) and nuisance
and yoked-root tapes are sign mirrored. Each master seed is averaged over all four
starts before inference; roots or time points are never treated as independent.

Tape construction uses NumPy `Generator(Philox(SeedSequence(words)))`. For each
master seed, make the two canonical starts `(+1,+1)` and `(+1,-1)` with seed words
`[master_seed,pair_index,stream]`, where `pair_index in {0,1}` and stream is
`1=action_uniform`, `2=nuisance_bit`, or `3=yoked_permutation`. Draw all 64 values
for a stream before constructing any arm. A nuisance bit is `+1` iff its uniform is
at least `0.5`. For each of 16 yoked blocks, apply the stream's next four uniforms
as stable ascending sort keys to the root order stated above, then swap the
canonical start root into the first position of the first block. The two negative-q
mirror starts use `1-u` for action uniforms and negate the canonical nuisance and
yoked roots; they do not draw new values. These tapes are science-bearing seeds and
are frozen, not tuned or regenerated in response to outcomes.

## Continuous observables

Let

`C_a(j) = mean_panel p_theta(correct_action|cue)`

for arm `a`, where `j=0` is immediately after the boundary mutation and before any
future update, and `j=1..64` is after each future update. Retain every value, not
only checkpoints. The primary scalar is normalized trajectory area

`U_a = (1/65) * sum_(j=0)^64 C_a(j)`.

An effect of `0.02` in `U` is the target materiality: two percentage points of
mean correct-action probability across the post-boundary trajectory. Also report
at every `j` the panel BCE, panel entropy, mean signed logit margin, all four root
probabilities, parameter displacement from `theta0`, PROBE-action rate, and
PROBE-target exposure occupancy. Report endpoint `C(64)` and all primary effects
as trajectories and as `U` effects.

For any arm, define `O_a=(1/64)*sum_j 1[q_j=+1]`. Exposure is realized for `A_M`
when
`X_M=0.25*sum_(m,e) abs(O^D[m,e,SELF]-O^D[m,e,YOKED]) >= 0.10`.
It is realized for `A_H` when
`X_H=0.125*sum_(a in {A,D},m,e) abs(O^a[m,e,SELF]-O^a[m,e,YOKED]) >= 0.10`.
Report both unit-level values and means; they are exposure checks, not additional
outcome effects.

For a master seed, first average `U` over its four sign-balanced start roots. Write
`U^A[m,e,x]` for a main cell and `U^D[m,e,x]` for its DELTA_MATCH shadow, and define

`P[m,x] = U^D[m,PULSE,x] - U^D[m,ZERO,x]`,

`R[m,e,x] = U^A[m,e,x] - U^D[m,e,x]`, and

`H[x] = 0.5 * sum_e (R[CARRY,e,x] - R[RESET,e,x])`.

The four prespecified factorial relay effects are:

- `D_M = 0.5 * sum_m P[m,YOKED]`: direct first-parameter-mutation effect under
  common future exposure and fresh Adam;
- `D_H = H[YOKED]`: direct inherited-Adam-history effect after subtracting the
  state produced by an otherwise fresh RESET boundary step;
- `A_M = 0.5 * sum_m (P[m,SELF] - P[m,YOKED])`: additional on-policy exposure
  amplification of the mutation channel; and
- `A_H = H[SELF] - H[YOKED]`: additional on-policy exposure amplification of the
  inherited-state channel.

Use the same equations pointwise on `C(j)` to show when separation begins. Also
report the unaveraged `M`, `E`, and `M x E` contrasts of `Delta`, `C(j)`, and `U`,
plus the pulse-specific history interaction
`(R[CARRY,PULSE,x]-R[RESET,PULSE,x]) -
 (R[CARRY,ZERO,x]-R[RESET,ZERO,x])`. These prevent averaging from hiding an
opposite-sign cell without multiplying primary claims.

## Same-size generic-perturbation alternative

For each `m`, define the entropy-induced first-displacement difference
`d[m]=Delta[m,PULSE]-Delta[m,ZERO]`. From the matched ZERO state and common fresh
Adam, construct four `GENERIC[m,k]` states by adding

- `+J1(d)`, `-J1(d)`, `+J2(d)`, and `-J2(d)`, where
- `J1(d1,d2,d3,d4)=(d2,-d1,d4,-d3)` and
- `J2(d1,d2,d3,d4)=(d3,d4,-d1,-d2)`.

Each generic kick is orthogonal to `d`, has exactly the same Euclidean parameter
norm, and the four kicks sum to zero. They use the same YOKED/SELF continuations,
tapes, panel, and fresh Adam as DELTA_MATCH. If `d` is numerically zero, the generic
arms correctly collapse to the ZERO matched state; that observation is not a
runner failure.

For each seed, report the largest absolute generic direct effect over `k`, and the
largest absolute generic `SELF-YOKED` amplification over `k`, each averaged over
`m`. Explicitly, after the four-root average, compute

`G_D = 0.5 * sum_m max_k abs(U^G[m,k,YOKED]-U^D[m,ZERO,YOKED])`

and

`G_A = 0.5 * sum_m max_k abs((U^G[m,k,SELF]-U^D[m,ZERO,SELF])
                            -(U^G[m,k,YOKED]-U^D[m,ZERO,YOKED]))`.

Use seed-level margins `abs(D_M)-G_D` and `abs(A_M)-G_A`. A mutation or
amplification pattern is not entropy-direction-specific if its
magnitude is within `0.02` of this conservative generic envelope. Fixed-panel
entropy-direction separation additionally requires the paired seed-level margin
`abs(actual effect)-generic_envelope` to average at least `0.02` with a 95% lower
confidence limit above zero. Even that eliminates only these four fixed
sign-balanced same-size alternatives, not every possible perturbation.

## Analysis, smallest useful budget, and activity start

Use master seeds
`[31013,31033,31051,31069,31091,31121,31139,31159]`. A master seed's average over
the four starts is the analysis unit. Eight units are the smallest useful panel
here: they preserve four-root sign balance while permitting exact enumeration of
all `2^8` paired sign flips.

For each of `D_M,D_H,A_M,A_H`, report the eight unit values, mean, standard
deviation, two-sided 95% Student-t interval, and exact two-sided sign-flip p-value.
Apply Holm correction across the four primary p-values at familywise `alpha=0.10`.
A directional material effect requires all of: absolute mean at least `0.02`,
Holm-adjusted significance, and the same nonzero sign in at least seven of eight
units. A 90% interval wholly inside `[-0.02,+0.02]` supports only practical absence
at this host/budget. Every other finite pattern is unresolved rather than forced
positive or negative.

The registered scientific budget is one complete run with:

- four common main boundary updates;
- eight seeds x four sign-balanced starts;
- 8 main, 8 DELTA_MATCH, and 16 GENERIC exposure continuations per start;
- 64 future actions and optimizer updates per continuation, for 65,536 future
  action/update rows; and
- the 20-cue fixed panel at all 65 post-boundary time points.

This is the smallest useful budget; there is no reduced scientific smoke run.
Ordinary focused construction checks do not consume or replace it.

Question-relevant scientific activity starts when one complete master-seed quartet
has finite deltas for all four main `(M,E)` cells, adequate DELTA_MATCH policies,
the `j=0` held-panel rows, and the first paired YOKED and SELF future-update rows for
all main and matched cells. Checkpoint loading, graph construction, unit checks, or
only a partial root/cell is not question-relevant activity.

## Outcome map and failure semantics

1. Nonfinite values, a changed `B0`, an arm-dependent yoked tape, an inadequate
   delta match, or missing required cells prevents the affected causal contrast.
   Before activity start this is CM engineering provenance, not evidence against
   the treatment. After activity starts, complete unaffected contrasts remain
   observations; the incomplete contrast has no conclusion.
2. A numerically negligible `d[m]` is a valid finding that coefficient `0.01` did
   not materially mutate the first RESET and/or CARRY update at this boundary. It
   does not invalidate history contrasts that remain exposed.
3. Material `D_M` with negligible `D_H` supports persistence through the first
   parameter displacement on common data, without a separable inherited-state
   legacy. Material `D_H` supports a carried-Adam legacy beyond matched first
   parameters and beyond state created by the RESET boundary update.
4. `A_M` or `A_H` is interpreted as closed-loop amplification only if its
   corresponding `X_M` or `X_H` exposure check is at least `0.10`. Without that
   realized exposure separation, the corresponding amplification estimand is
   unexposed at this budget, not evidence that amplification is absent.
5. A material SELF-YOKED effect with no corresponding mutation/history component
   is reported from the full cell table as an unattributed exposure interaction; it
   is not relabeled as either channel.
6. If a same-size GENERIC envelope matches an apparent mutation or amplification
   effect, the strongest explanation is a generic early kick entering a favorable
   root/tape basin. The result supports sensitivity to perturbation, not an
   entropy-specific route. Separation from the fixed generic envelope narrows but
   does not eliminate that explanation.
7. Opposite signs across memory cells, root mirrors, or seeds are reported as
   heterogeneity. A mean obtained by cancellation cannot support a directional
   mechanism claim. Finite submaterial or imprecise effects remain unresolved
   unless the practical-absence interval is wholly inside the materiality band.

## Strongest alternative and claim ceiling

The strongest alternative is that nothing special about entropy or hidden Adam
state is being relayed: any early parameter kick of the same size can enter a
self-confirming PROBE/HALT exposure basin on a favorable root/tape. DELTA_MATCH
removes first-position mismatch from the history contrast, YOKED cuts the feedback
edge, RESET subtracts boundary-created optimizer state, root mirrors remove a
single action/sign preference, and GENERIC supplies a conservative fixed
same-size-kick envelope. Finite seeds, fixed generic directions, and this toy
geometry still leave host-specific basin structure as an admissible limitation.

The maximum supported claim is causal only within this constructed four-root,
bilinear-logit, full-feedback policy host; the stated hand-specified boundary
state; Adam hyperparameters; entropy coefficient `0.01`; 64-step horizon; fixed
panel; and eight-seed sign-balanced tape set. A material `D_H` can establish that
carried Adam state changes later learning despite matched first parameters here. A
material `D_M` can establish a persistent entropy-induced first-displacement
effect here. Material `A_M/A_H` can establish additional action-to-exposure
amplification only when the exposure edge is realized. No outcome establishes the
mechanism in VSP02, G52, G53, production actor-critics, other optimizers,
coefficients, checkpoints, data regimes, or longer horizons; optimizer-state
necessity; entropy regularization's general value; or immunity to arbitrary
perturbations.

## CM-buildable request

CM should construct the isolated four-root host, common boundary object, factorial
main updates, direct-assignment DELTA_MATCH and GENERIC shadows, counter-keyed
YOKED/SELF tapes, fixed-panel trajectory recorder, and paired analyzer exactly as
defined above. Return the complete cell trajectories, first deltas and optimizer
states, exposure occupancies, per-seed effects and uncertainty, generic envelopes,
material anomalies, and whether the activity-start criterion was reached. A
missing host, optimizer adapter, graph hook, runner, or analyzer is CM construction
work and does not change or defer the scientific treatment.
