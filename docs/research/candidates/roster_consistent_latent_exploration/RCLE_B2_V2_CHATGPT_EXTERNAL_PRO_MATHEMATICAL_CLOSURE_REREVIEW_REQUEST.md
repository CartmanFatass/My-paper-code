# RCLE B2 revision-02 ChatGPT External Pro mathematical-closure rereview

Continue the existing dedicated ChatGPT External Pro conversation for exactly
`direction:roster_consistent_latent_exploration`. Do not open or substitute a
conversation. You previously accepted the complete revision-04 result branch
and converged on one prospective final family-level discriminator:
`VALIDITY_ONLY_SEMANTIC_SPECIFICITY_CONTROL`.

Your first prospective B2 review returned `REVISION_REQUIRED` for exact
revision 01 with two science-bearing defects. The local scientific owner
accepted both and froze the complete revision 02 below. Revision 02 changes no
arm, DGP, stochastic coordinate, seed, coefficient, count, threshold,
inference model, family-ending rule, or claim ceiling.

No B2 stochastic roster, latent, action, posterior-training object, actor or
posterior update, checkpoint, evaluation object, functional cut, or result has
been materialized or inspected. Revision 04 is complete and immutable and will
not be rerun or reused.

Return exactly one authoritative prospective mathematical and causal
disposition for the complete composite below: `CLOSED` or
`REVISION_REQUIRED`.

## Exact revision under review

```text
direction=roster_consistent_latent_exploration
candidate=RCLE-B2
exact_revision=RCLE-B2-SCIENCE-20260814-02
scientific_object=VALIDITY_ONLY_SEMANTIC_SPECIFICITY_CONTROL
result_blind=true
same_conversation=true
```

## Complete indivisible composite

### Question and protected purpose

Does the rotation-identity content of RCLE's actor-facing semantic score add
material held-out roster value beyond a maximum-positive-scale-matched
actor-facing validity signal? This is a fresh paired two-arm assay and the sole
remaining test of the current semantic-diversification formulation.

The two arms are:

1. `RCLE`: exact revision-04 RCLE, trained from a fresh paired initialization,
   with

   ```text
   B_RCLE = V * [1 + log q(Z|K*) / log 4]
   ```

   where invalid episodes have no `K*`, fixed `q(.|bottom)=1/4`, no posterior
   update, and `B_RCLE=0`.
2. `VALIDITY-ONLY`: identical common latent, host, actor, initialization,
   posterior table/training/work, samples, updates, optimizer, coefficient,
   diagnostics, and evaluation, but

   ```text
   B_VALID = V
   ```

   `B_VALID` directly reads only validity and has no direct dependence on
   `K*`, hidden-lock identity, `Z` identity, `q`, a posterior probability, or
   the computed semantic score. The complete stopped actor coefficient is

   ```text
   R + 0.10 * B_VALID - c_N,Z
   ```

   where the shared task reward remains `R=V*1[K*=H]` and the shared
   action-independent baseline remains indexed by causal pre-action `(N,Z)`.
   Those two paths are identical in RCLE and `VALIDITY-ONLY`; they are not
   removed or relabeled. Thus B2 isolates replacement of the additional
   generic-validity auxiliary by the posterior-shaped semantic auxiliary. It
   does not compare RCLE with a complete actor coefficient free of `K*` or `Z`.
   `B_VALID` lies in `[0,1]`, matching RCLE's maximum positive auxiliary value,
   not its negative tail, posterior-confidence weighting, or gradient geometry.

The sole primary contrast is paired frozen held-out-`N=12` campaign value,
`RCLE - VALIDITY-ONLY`, on fresh B2 coordinates. No prior arm, cross-control
ordering, or other direction enters B2.

### Host, observations, actions, and campaign

Training uses `N={4,8}` with equal episode and update weight; evaluation uses
frozen learned objects at `N={4,8,12}`. For each roster, draw
`Xi ~ Uniform[0.3,0.7]`, retain it while drawing iid
`X_i ~ Beta(8 Xi, 8(1-Xi))`, and accept exactly when no one of the four bins

```text
X_i < mu/2
mu/2 <= X_i < mu
mu <= X_i < (1+mu)/2
X_i >= (1+mu)/2
```

contains more than half the roster. Here `mu=N^-1 sum_i X_i` is computed once
on the accepted canonical roster. More than 4,096 proposals makes the run
incomplete; it never redraws `Xi` or weakens acceptance. Rows are permuted only
after acceptance and row order is not an input.

At each of two binary decisions, agent `i` observes only `X_i`, public mean
`mu`, phase, the uniform episode-common four-valued `Z`, and its own first
action at phase two. It receives no roster count, identity, slot, rank, roster
tensor, other-agent field, bin, rotation, validity, hidden lock, reward,
posterior state, seed, or arm label.

The route is `R_i=2 A_i^1+A_i^2`; relative rotation is
`D_i=(R_i-B_i) mod 4`; `V=1` iff some rotation is used by at least three
quarters of agents. `K*` is unique when valid and nonexistent when invalid.
One campaign fixes a roster and an independent uniform hidden lock `H`, then
uses each common `Z` once in a fresh random four-probe order with independent
action uniforms and no updates or memory. Probe reward is
`R=V*1[K*=H]`; campaign value is the maximum reward among the four probes.
Training crosses one accepted roster at each training size with all four locks
and all four latents before an update.

### Actor, posterior, and learning law

Both float64 arms use the exact 1,506-parameter actor

```text
input = [X_i, mu, X_i-mu, phase_1, phase_2,
         previous_action_available, signed_previous_action_or_zero,
         one_hot_Z_0..3]
Linear(11,32) -> tanh -> Linear(32,32) -> tanh -> Linear(32,2)
```

with a sampled temperature-one binary categorical law. There is no critic,
recurrence, per-`N` head, greedy evaluation, or checkpoint selection. Both arms
have a disjoint `4x4` posterior table `q(z|K*)`, compute the same entropy,
posterior, semantic, validity, rotation, and diagnostic work, and train the
posterior on true valid `(Z,K*)` pairs. Corresponding actor and posterior
tensors start byte-identically within seed; actor weights are Xavier-uniform
with tanh gain, biases zero, and posterior logits zero.

Each arm/seed has 2,000 updates. One update has 16 episodes at each training
size. For both arms,

```text
T_e = R_e + 0.10 * B_e
L_actor = -1/2 sum_N (1/16) sum_e:N
          stop(T_e-c_N,Z) * log P_e
```

where `log P_e` sums selected-action log probabilities over both phases and all
agents. There is no extra `1/N`. Each arm's action-independent `(N,Z)` EMA
baseline starts at zero and, after the actor step, updates with decay `0.95`
from the same bucket's mean stopped `T_e`. Actor Adam has learning rate `1e-3`,
betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay, global norm clip `1.0`,
and one step per block.

The pre-update posterior scores the block. After the actor step, each arm takes
one posterior step on

```text
L_q = -1/2 sum_N (1/16) sum_e:N V_e log q(Z_e|K*_e)
```

without valid-count renormalization. Posterior Adam uses learning rate `1e-2`
and the same remaining Adam/clip settings. There is no replay, tuning, early
stop, curriculum, sweep, or selected checkpoint; only update 2,000 is
evaluable.

### Fresh coordinates, counts, and activity

The fixed fresh seeds are

```text
[2371,2473,2591,2683,2791,2903,3011,3121,3251,3371,3491,3613]
```

The exact revision and a new versioned address schema define a new PCG64 root
with independent addresses for environment, roster proposals, row permutation,
lock, common latent, probe order, both action phases, initialization,
optimization/evaluation, and cuts. No revision-04 stochastic object,
checkpoint, baseline, posterior, anchor, or evaluation object is reused.
Matched semantic coordinates are paired across the two B2 arms, and divergence
never shifts another address.

Question-relevant activity starts at the first materialized or inspected
registered B2 stochastic object or optimizer update. Static source parsing,
shape checks, information-boundary checks, and algebra on hand-specified
nonrandom fixtures remain preactivity. Partial values may not be interpreted or
used to alter the object. A scientific result requires all 12 atomic seeds.

Exact counts are 1,536,000 training episodes, 589,824 ordinary evaluation
episodes, and 589,824 RCLE-only cut episodes. At all `N={4,8,12}`, each cut
shares intact RCLE's fresh accepted roster, hidden lock, probe index, and action
uniforms and changes only its named latent intervention; only `N=12` is
inferential. The inherited ceiling is 8,000,000 episodes including gates, one
CPU, 2 GiB, 45 minutes. An incomplete resource or engineering event is repaired
without changing science and is not an outcome.

### Evaluation, anchor, fidelity, and cuts

Every arm/seed receives 2,048 fresh campaigns per evaluation size, 512 per
lock. At `N=4`, within each lock stratum indices `0..255` are the fixed anchor
half and `256..511` the scoring half. For each RCLE seed and latent, the anchor
half chooses the most frequent valid winning rotation. A tied row fails, and
the four unique row maxima must be a bijection in every seed. `N=8` and `N=12`
never select or realign the map.

For each seed, latent, and size, anchored fidelity is the probability of both
validity and the seed's chosen `N=4` rotation. `N=4` uses only the scoring half;
the other sizes use all campaigns. All 12 `(z,N)` across-seed one-sided
Student-t lower bounds must exceed `0.70`; they retain the 95% Bonferroni family
from revision 04, hence each marginal bound is `99.583333%` with 11 degrees of
freedom.

The exact RCLE-only cuts are preserved: iid per-agent latents in both phases,
and a common latent resampled between phases. Their intact-minus-cut `N=12`
one-sided 95% lower bounds must respectively exceed `0.10` and `0.05`. They are
functional dependence checks, not natural-mediation proof. Posterior
restriction, deterministic scripted oracle/collapse, both actions/phases, all
locks/rotations, row invariance, forbidden-input exclusion, and nonempty
accepted fixtures retain their revision-04 gates.

### Sole contrast and exhaustive outcome law

For each seed define

```text
Delta_s = C_RCLE,s,N12 - C_VALIDITY,s,N12
```

Seeds are the independent units. Under the inherited independent Normal
seed-effect model, use one-sided Student-t bounds with 11 degrees of freedom.
Because this is the sole primary contrast, the familywise one-sided level is
95% without the former three-contrast Bonferroni division:

```text
POS_VALIDITY    iff lower_95(Delta) > 0.10
NO_MAT_VALIDITY iff upper_95(Delta) < 0.05
UNRES_VALIDITY  otherwise
```

Define `INVALID_OR_INCOMPLETE` iff any one of the following is true:

- any registered arm, seed, training block, ordinary campaign, or RCLE cut is
  missing;
- any required scientific output is nonfinite;
- the exact source revision, hyperparameter set, DGP, accepted-roster law,
  rejection rule, or fresh-coordinate prohibition is violated;
- any forbidden actor or posterior information path exists;
- the posterior restriction is false;
- the deterministic host/oracle/headroom/action/lock/rotation/row-invariance/
  information-boundary/nonempty-support gate is false;
- an evaluation adaptation, checkpoint selection, leakage path, or partial-
  result selection occurs; or
- a resource terminal leaves the exact panel incomplete.

Define `VALID_COMPLETE = not INVALID_OR_INCOMPLETE`.

Define `ZERO_LEARNED_VALIDITY` iff `V=0` on every ordinary-evaluation probe for
both learned arms, all 12 seeds, and every `N in {4,8,12}`. Define
`ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY` iff the scripted oracle passes and
`ZERO_LEARNED_VALIDITY` is true.

Define `SCIENTIFIC_RETENTION_GATES_OK` iff all are true:

```text
every seed has unique N=4 row maxima and a four-rotation bijection
all 12 anchored-fidelity lower bounds exceed 0.70
private-cut lower bound exceeds 0.10
temporal-cut lower bound exceeds 0.05
```

Define

```text
FAMILY_RETAINED =
  VALID_COMPLETE and
  POS_VALIDITY and
  SCIENTIFIC_RETENTION_GATES_OK
```

Apply this exact precedence:

0. If `INVALID_OR_INCOMPLETE`, support no scientific comparison; CM completes
   or repairs the unchanged object, and the formulation does not end from that
   panel.
1. Else if `ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY`, report the finite-
   budget optimization question nonidentified and end the exact formulation.
2. Else if `FAMILY_RETAINED`, retain the narrowed package family.
3. Else if `POS_VALIDITY`, report a bounded positive package contrast without
   family retention, state which scientific retention gate failed, and end the
   formulation.
4. Else if `NO_MAT_VALIDITY`, report only that the one-sided upper bound places
   the directional `RCLE - VALIDITY-ONLY` effect below `0.05`; this is not
   equivalence, and end the formulation.
5. Else report `UNRES_VALIDITY` without parity, equivalence, failure, or effect-
   absence language, and end the formulation.

Within item 3, a failed scientific retention gate means only unique-bijection,
12-cell fidelity, private-cut, or temporal-cut nonpass. A forbidden information
path, posterior-restriction failure, failed support/headroom/invariance gate,
leakage, source/DGP/coordinate violation, nonfinite output, or incompleteness
belongs to item 0 and permits no positive package claim.

Threshold nonpass is not affirmative absence; unresolved is not equivalence;
ending the current formulation is the frozen action rule, not a broader
negative scientific claim. There is no coefficient, capacity, alphabet,
threshold, seed, extra-seed, optimizer, horizon, checkpoint, host, or repeated-
tuning rescue.

### Strongest alternative and maximum claim

Even with `FAMILY_RETAINED=true`, the strongest alternative is posterior-
confidence-weighted validity shaping and optimizer geometry rather than
rotation identity itself. RCLE and `VALIDITY-ONLY` differ in posterior-dependent
magnitude, negative tail, variance, task-gradient covariance, clipping
exposure, and Adam moment trajectories. Therefore the maximum positive claim is
that the exact RCLE package materially exceeded the exact validity-only package
on this accepted-roster finite toy while meeting the unique-codebook, fidelity,
and cut criteria. It cannot attribute the advantage to semantic identity
independently of those optimization properties.

No outcome supports arbitrary or continuous roster sizes, membership churn,
variable skill period, continuous control, a second surface, UAV simulation,
or flight. A positive does not activate a second surface. After a complete
result, return to this same Pro conversation for result convergence. If the
family is retained, a future gradient-geometry-matched nonsemantic control is
the only coherent next causal discriminator, but it is not authorized here. If
the family is not retained, no successor inside the current formulation is
allowed.

## Required closure audit

Audit the complete composite, not only `B_VALID=V`. In particular decide
whether:

1. `VALIDITY-ONLY` has no direct paired `(Z,K*)` or posterior-semantic content
   in `B_VALID`, while the shared task reward and `(N,Z)` baseline remain
   explicit, and its maximum positive auxiliary scale is correctly matched;
2. the two arms, posterior work, stopped score-function laws, fresh pairing,
   and sole `N=12` estimand are unambiguous;
3. changing the primary family from three contrasts to one correctly changes
   the positive bound to one-sided 95% while preserving seed-level inference;
4. the unique-bijection, 12-cell fidelity, and two cut gates are jointly
   sufficient for the deliberately narrow retained-package claim;
5. invalid/conformance failures are partitioned from valid scientific
   retention-gate nonpasses, and the family-ending rule is exhaustive without
   converting threshold nonpass into an unsupported negative claim;
   and
6. the strongest optimizer alternative and finite-toy ceiling remain explicit.

Return `CLOSED` only if every science-bearing distribution, observation,
action, learning law, estimand, predicate, branch, activity boundary, and
maximum claim is fixed before production. Do not review code or runtime, make a
portfolio decision, authorize construction, relax the family-ending rule, add
a rescue, or create a new provider identity.

## Required response format

Return each heading exactly once.

### CLOSURE_AUTHORITY_DECISION

Include exactly one of:

```text
CLOSURE_AUTHORITY_DECISION=CLOSED
```

or

```text
CLOSURE_AUTHORITY_DECISION=REVISION_REQUIRED
```

Also include:

```text
EXACT_REVISION=RCLE-B2-SCIENCE-20260814-02
RESULT_BLIND=true
SAME_CONVERSATION=true
```

### PRIOR_DEFECT_DISPOSITION

For each revision-01 defect, write `RESOLVED` or identify the exact remaining
science-bearing ambiguity.

### COMPOSITE_MATHEMATICAL_AND_CAUSAL_AUDIT

Audit the control, learning law, pairing, estimand, gates, precedence, and claim
ceiling.

### DEFECT_LEDGER

If closed, write `SCIENCE_BEARING_DEFECT_COUNT=0` and separate any ordinary
implementation-conformance note. If revision is required, number every defect,
give the smallest exact prospective repair, and identify the affected arm,
estimand, predicate, branch, or claim.

### STRONGEST_ALTERNATIVE

State the strongest explanation a complete retained result would not remove.

### MAXIMUM_CLAIM_CEILING

Give the maximum language for retained, positive-but-not-retained,
no-material, unresolved, zero-validity, and invalid/incomplete outcomes.

### NEXT_HIGHEST_INFORMATION_DISCRIMINATOR

State the next discriminator for retained and non-retained outcomes without
authorizing it or a second surface.
