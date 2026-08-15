# RCLE coarse persistent-commitment mathematical-closure request

Continue the existing dedicated ChatGPT External Pro conversation for exactly
`direction:roster_consistent_latent_exploration`. This is a new result-blind
definition, not a continuation or repair of the completed four-strategy
formulation. Do not import old codebook gates, thresholds, seeds, checkpoints,
results, or claims.

Review exact revision `RCLE-CPC-SCIENCE-20260815-04` for prospective
mathematical and causal closure. No stochastic object, initialization,
coordinate, training episode, evaluation episode, or result exists. Treat
implementation and runtime feasibility as outside your authority.

Revision 04 prospectively accepts the sole defect from your result-blind
revision-03 ruling while retaining all revision-03 repairs. It makes every
mechanism contrast a seed-level effect computed exclusively on the held-out
`N=9`, `handoff=true` panel. No arm, DGP, seed, stochastic family, coefficient,
sample count, threshold, endpoint, observation, or primary estimand changes,
and no scientific activity has begun.

Return exactly `CLOSED` if the complete object below determines every
science-bearing distribution, treatment, comparator, estimand, branch, family
action, activity boundary, and claim. Otherwise return `REVISION_REQUIRED`
with the smallest exact correction and identify every conclusion it could
change.

## Complete frozen object

### Question

On a dual-corridor search/relay handoff task, a roster receives noisy private
target clues, acts, then undergoes role-balanced membership replacement before
acting again. New agents do not see old clues or actions. Does a binary
clue-conditioned common latent, sampled once and preserved through the handoff,
improve held-out-roster mission value or reduce the handoff penalty relative to
a strictly containing learned latent with up to eight effective states under a
fixed finite budget?

If it wins, do the two frozen-checkpoint evaluation cuts show functional
dependence on one shared realization and temporal persistence; does the intact
context-bound coarse package exceed the separately trained-and-evaluated
context-shuffled coarse package; and does coarse reduce the registered
behavioral-fragmentation endpoint?

### Host

`N in {5,7,9}`; training uses `N={5,7}` and final evaluation alone uses held-
out `N=9`. One shared manager and actor cover all sizes. The hidden target
`G` is uniform on `{LEFT,RIGHT}`. Initial roles are a uniformly permuted roster
with exactly `ceil(N/2)` SENSOR and `floor(N/2)` RELAY agents. Each initial
agent independently receives clue `S_i`, correct with probability `0.70`.

The manager observes only the unordered initial `(role_i,S_i)` set and `N`.
Each memoryless shared actor observes only own role, own clue or missing marker,
phase, `N`, and latent. There is no target truth, reward, validity, majority,
other action, ID, history, recurrence, or post-handoff manager call.

There are two simultaneous actions, `PRE` and `POST`, each in
`{LEFT,RIGHT,HOLD}`. Between them no feedback is revealed. The handoff removes
and role-for-role replaces:

```text
N=5: 1 SENSOR + 1 RELAY
N=7: 2 SENSOR + 1 RELAY
N=9: 2 SENSOR + 2 RELAY
```

Removed identities are uniform within role. New agents have no clue or prior
state. Training balances four cells: `(5,no handoff)`, `(5,handoff)`,
`(7,no handoff)`, `(7,handoff)`. Evaluation adds both `N=9` cells.

For phase `p`, physical validity requires every corridor used by a SENSOR also
to contain at least one RELAY. Let `A_p` be the fraction choosing target `G`,
`Q_N=ceil(0.60N)`, and `T_p=1` when at least `Q_N` choose `G` with at least one
SENSOR and one RELAY there. Mission success is

```text
M = V_PRE * V_POST * T_PRE * T_POST.
```

The identical bounded learning/evaluation value for every arm is

```text
Y = 0.65 M + 0.15 A_PRE + 0.15 A_POST
    + 0.025 V_PRE + 0.025 V_POST.
```

There is no semantic, posterior, mutual-information, or latent-identity
auxiliary.

Let `C_PRE` be the unique non-HOLD majority corridor, invalid on a tie or all
HOLD. Behavioral fragmentation is `F=1` if invalid and otherwise

```text
F = 1 - (# POST actions equal C_PRE)/N.
```

It is not rewarded and does not imply target correctness.

### Shared maximum architecture

Every learned arm allocates the same maximum parameters. Each manager element
is role one-hot plus clue in `{-1,+1}`. A `3-32-32` tanh element encoder is
mean-pooled and concatenated with `N/9`. A two-logit macro head gives
`p(C|set,N)=softmax(a)` for unanchored `C in {0,1}`; no label is hardwired to a
corridor. An eight-logit refinement head gives two conditional four-way rows
`q(U|C,set,N)=sparsemax(v_C)`, `U in {1,2,3,4}`.

The actor input is role one-hot, three-way clue/missing one-hot, phase one-hot,
`N/9`, and an eight-dimensional latent vector, followed by a `64-64-3` tanh
MLP and action softmax. Latent vectors are `e_C+r_CU`, with two macro bases and
eight refinement residuals. Every arm allocates both heads, both base rows,
all residual rows, and the same actor.

Sparsemax is the unique simplex projection
`q_i=max(v_i-tau,0), sum_i q_i=1`. With active set `A={i:q_i>0}`, its registered
derivative is
`dq_i/dv_j=1[i,j in A]*(1[i=j]-1/|A|)`; an exact zero is inactive. Stable
lexicographic order resolves computational sort ties without changing the
unique forward projection. Only a sampled positive-probability refinement is
log-scored, and there is no latent entropy term.

### Arms

`COARSE-PERSISTENT`: sample one macro `C`; broadcast it to every agent at both
decisions, including newcomers; give the actor `e_C`. The refinement head and
residuals have no forward or score path and zero gradient.

`FLEXIBLE-PERSISTENT`: sample `C`, then `U|C`; broadcast the joint `(C,U)` once
under the identical common persistent law; give the actor `e_C+r_CU`. Setting
all residuals to zero reproduces every coarse policy exactly for arbitrary
refinement probabilities. A registered fixture with three positive refinements
and linearly independent action distributions yields a rank-three common-
mixture joint-action matrix, while a binary mixture has rank at most two; its
actor Jacobians must be nonzero. Thus the extension is strict and
output-connected.

All residuals initialize at zero, so coarse and flexible policies are exactly
function-matched on every legal input before update one. Flexible residuals
have nonzero first-order actor Jacobians and are immediately trainable. Its
refinement score is active. This is policy-function containment and a live
strict extension, not optimizer-trajectory containment.

`CONTEXT-SHUFFLED-COARSE`: retain the binary macro treatment. Within each training block
and `(N,handoff)` cell, a frozen science-law cyclic derangement assigns
each recipient another episode's already sampled macro. A source uses its own
manager distribution and source-keyed inverse-CDF uniform; the cyclic map
reassigns that realized draw, preserving the exact within-arm latent multiset.
The score-function term is charged to the source distribution and recipient
outcome. Evaluation uses the same within-
cell derangement. It preserves binary alphabet, commonality, persistence,
latent marginal exposure, calls, update form, and optimizer opportunity while
breaking own-context binding. It does not assert identical realized gradient
direction. Because it is trained and evaluated under derangement,
`CONTEXT-SHUFFLED-COARSE` creates a between-package contrast of intact context
binding throughout learning and evaluation. It is not an evaluation-only
intervention and cannot isolate training-time credit, evaluation-time
misbinding, or their interaction.

Two evaluation-only cuts use the final coarse checkpoint at held-out `N=9`
handoff: `PRIVATE-LATENT-CUT` gives each agent an independent macro draw from
the intact manager distribution, persistent for that identity; newcomers draw
on entry. `TEMPORAL-RESET-CUT` uses one common PRE macro and an independent
common POST redraw from the same stored distribution. Weights, context,
marginals, reward, and panel are otherwise fixed.

Only these private and temporal-reset cuts are frozen-checkpoint functional
interventions. The context-shuffled learned package is not.

### Training and optimizer

Each block contains 64 complete episodes, 16 per training cell. Let `x_b^src`
be the recipient context in intact arms and its deranged same-cell source in
the shuffled arm. The exact score and loss are

```text
ell_b = log p(C_b|x_b^src)
        + 1[FLEXIBLE]*log q(U_b|C_b,x_b^src)
        + sum_i log pi(A_PRE_bi|o_PRE_bi,latent_b)
        + sum_j log pi(A_POST_bj|o_POST_bj,latent_b)
L = -(1/64) sum_b stop(Y_b-b_{a,N_b,h_b})*ell_b.
```

Every cell baseline starts at zero and, only after the parameter update, uses
`b <- .95*b + .05*mean_cell(Y)`. It is stopped and has no optimizer state.
There is no entropy bonus, validity-only auxiliary, reward normalization,
posterior, learned critic, reconstruction, curriculum, early stopping, or
adaptive horizon. Every arm therefore receives the identical task value and
validity shaping; the shuffled arm matches the coarse score dimension and
optimizer rule while breaking own-context binding.

Every arm receives one joint plain-SGD update per block, no momentum, weight
decay, clipping, or adaptive moments. The raw-gradient norm is Euclidean over
the complete concatenated registered parameter tensor. A nonzero raw gradient
is normalized to length `0.10`, then multiplied by learning rate `0.01`, so its
whole-parameter update norm is exactly `0.001`; a zero raw gradient produces no
update. This equalizes only nonzero whole-update norm. Zero-step incidence,
cumulative path length, parameter-group allocation, gradient direction,
per-parameter scale, function-space movement, curvature, visitation, and basin
access remain unmatched. Zero-gradient frequency is descriptive and cannot
support or defeat a branch.

Every affine weight entry is iid uniform on
`[-sqrt(6/(fan_in+fan_out)),+sqrt(6/(fan_in+fan_out))]`; affine biases are zero.
Macro-base entries are iid uniform on `[-1/sqrt(8),+1/sqrt(8)]`, and every
refinement residual is exactly zero. The complete tensor is copied bit-for-bit
across arms within seed. The terminal is exactly update 1,000; no checkpoint
selection or restart selection is allowed.

At the science level, all initialization and episode variates form independent
`Uniform(0,1)` product families indexed by seed, cell, block/panel episode,
variable, phase, and roster slot. Across arms, target, roles, clues, handoff,
macro inverse-CDF variates, and action variates are paired wherever their
semantics coincide; flexible refinement variates are independent. A training
cell uses a uniformly selected nonzero cyclic shift of its 16 episodes for the
shuffled source; evaluation uses a uniformly selected nonzero shift of 2,048.
Shuffled latent draws remain keyed to their source before reassignment.
Cuts retain all unchanged variates and use fresh intervention draws. This is an
abstract probability law, not an RNG-coordinate binding.

The 16 fresh seeds are:

```text
4109, 4217, 4337, 4441, 4561, 4673, 4787, 4903,
5021, 5147, 5261, 5381, 5503, 5623, 5741, 5861.
```

Training has `3*16*1000*64 = 3,072,000` episodes. Ordinary evaluation uses
2,048 episodes per arm/seed/size/handoff cell, totaling 589,824. Each of the
two held-out cuts uses 2,048 episodes per seed, totaling 65,536 cut episodes.

### Estimands and inference

All final panels are paired on target, roles, clues, handoff identities, and
policy randomness where arm semantics permit. Seed is the independent unit.
Let `J` be seed-level mean `Y`, `S` mean `M`, and `F` mean fragmentation.

```text
Delta_VALUE_s = J_COARSE,s,9,handoff - J_FLEX,s,9,handoff
Penalty_a,s = J_a,s,9,no-handoff - J_a,s,9,handoff
Delta_ROBUST_s = Penalty_FLEX,s - Penalty_COARSE,s.
```

Constitutively treat the 16 registered seed-level vectors

```text
(Delta_VALUE_s, Delta_ROBUST_s, Delta_FRAGMENT_s,
 Delta_COMMON_s, Delta_PERSIST_s, Delta_CONTEXT_s)
```

as iid draws from one multivariate Normal seed-effect working model with
unrestricted mean, positive-semidefinite covariance, and arbitrary within-seed
correlation. Coverage statements are nominal and model-based, not
distribution-free. For any scalar effect `d_s`, define

```text
d_bar = (1/16)*sum_s d_s
s_d^2 = (1/15)*sum_s (d_s-d_bar)^2
s_d = sqrt(s_d^2)
L_gamma(d) = d_bar - t_(df=15,gamma)*s_d/4
U_gamma(d) = d_bar + t_(df=15,gamma)*s_d/4.
```

If `s_d=0`, both endpoints equal `d_bar`.

Primary selection uses one four-tail confidence rectangle. Every lower and
upper endpoint uses `gamma=0.9875`, giving nominal Bonferroni familywise 95%
model-based coverage over
`{L_VALUE,U_VALUE,L_ROBUST,U_ROBUST}`:

```text
VALUE_WIN  iff L_VALUE  > 0.06 and L_ROBUST > -0.02
ROBUST_WIN iff L_ROBUST > 0.06 and L_VALUE  > -0.02
COARSE_TARGET_WIN = VALUE_WIN or ROBUST_WIN.
```

The mirror-image `FLEX_TARGET_WIN` uses simultaneous upper bounds:

```text
(U_VALUE < -0.06 and U_ROBUST < 0.02)
or (U_ROBUST < -0.06 and U_VALUE < 0.02).
```

`TARGET_NO_MATERIAL` requires that same rectangle to satisfy
`L_VALUE>=-0.03`, `U_VALUE<=0.03`, `L_ROBUST>=-0.03`, and
`U_ROBUST<=0.03`. Those four equality boundaries are inclusive; every other
displayed branch inequality is strict. All other primary states are unresolved.
The single rectangle controls data-dependent coarse, flexible, and equivalence
language.

All mechanism contrasts are seed-level effects computed exclusively on the
held-out `N=9`, `handoff=true` panel:

```text
Delta_FRAGMENT_s =
  F_FLEX,s,N=9,handoff - F_COARSE,s,N=9,handoff
Delta_COMMON_s =
  J_COARSE-intact,s,N=9,handoff - J_PRIVATE-LATENT-CUT,s,N=9,handoff
Delta_PERSIST_s =
  J_COARSE-intact,s,N=9,handoff - J_TEMPORAL-RESET-CUT,s,N=9,handoff
Delta_CONTEXT_s =
  J_COARSE,s,N=9,handoff - J_CONTEXT-SHUFFLED-COARSE,s,N=9,handoff.
```

No `N=9` no-handoff episode and no average across the two held-out
handoff-status cells enters `Delta_FRAGMENT`, `Delta_COMMON`, `Delta_PERSIST`,
`Delta_CONTEXT`, or the six-lower-bound mechanism family.

For a mechanism-positive claim, a separate six-lower-bound family jointly
covers the two primaries and four mechanism contrasts. Each uses
`gamma=1-0.05/6=0.991666666666...` for nominal Bonferroni familywise 95%
model-based coverage. Gates are
`L6_FRAGMENT>0.08` and each value-cut `L6>0.04`. Define
`COARSE_TARGET_WIN_6` by applying the primary win law to
`L6_VALUE,L6_ROBUST`. Mechanism support requires all four gates plus
`COARSE_TARGET_WIN_6`; the primary rectangle alone cannot license mechanism
language.

`Delta_COMMON` and `Delta_PERSIST` support functional dependence only under
their registered frozen-checkpoint cuts. `Delta_CONTEXT` supports only that
the intact context-bound learned package exceeded the separately trained and
evaluated context-shuffled package. It is not evaluation-only context
dependence, and none of the three contrasts establishes natural mediation.

Mission success, per-size results, histograms, macro/refinement occupancy and
effective cardinality, manager distribution by clue majority, gradient-
direction cosine, and zero-gradient frequency are descriptive only.

### Support

A full-information common-binary oracle must obtain `Y=M=1` in every cell. A
same-information majority-clue Bayes oracle must, by exhaustive rational
enumeration of all `2^N` clue vectors, have exact mission-success probability
`sum_{k=(N+1)/2}^N choose(N,k)*(7/10)^k*(3/10)^(N-k)` at each odd `N`.
No stochastic oracle panel exists. Deterministic static fixtures must
show exact coarse reproduction for arbitrary refinement probabilities when
all residuals are zero, and an output-connected rank-three flexible witness
outside the rank-at-most-two binary mixture class.

### Literal precedence and actions

1. `INVALID_OR_INCOMPLETE`: missing arm/seed/cell, changed law, forbidden input,
   nonfinite endpoint, evaluation adaptation, failed oracle, failed containing
   proof, or incomplete panel. No science or family action.
2. `ALL_LEARNED_ZERO_MISSION`: on a valid complete panel, deterministic support
   passes but `M=0` on every ordinary-evaluation episode for all three arms,
   all 16 seeds, every `N in {5,7,9}`, and both handoff cells. Report the
   finite-budget comparison nonidentified; retain neither target package; make
   no superiority, equivalence, no-effect, representability, or general-family
   claim; and end the exact CPC formulation.
3. `COARSE_MECHANISM_SUPPORTED`: `COARSE_TARGET_WIN_6` plus all mechanism gates.
   Retain the coarse package for this named target and permit the bounded
   mechanism wording.
4. `COARSE_PACKAGE_ONLY`: coarse target win but branch 3 does not hold, whether
   because its stricter six-bound target gate or a mechanism gate fails. Retain
   only the exact value/robustness package, with no fragmentation/commonality/
   persistence/context-binding attribution.
5. `FLEXIBLE_CONTAINING_SUPERIOR`: flexible target win. Delete the fixed binary
   restriction for this target; make no general persistent-latent claim.
6. `NO_COARSE_ADVANTAGE`: both primary effects fall inside the equivalence
   region. Do not retain the fixed coarse restriction.
7. `TARGET_UNRESOLVED`: no positive, superiority, equivalence, failure, or
   no-effect claim; the assay supplies no retention evidence.

Branches 2 and 5-7 allow no coefficient, cardinality, seed, extra-seed,
threshold, optimizer, horizon, checkpoint, roster, reward, or repeated-assay
rescue of this object. A materially different future theory requires a newly
authorized object and is not a continuation of CPC.

### Strongest alternative and claim ceiling

The strongest alternative is finite-budget regularization and gradient-
direction/representation-search geometry. Exact initial-policy matching,
fixed-norm nonadaptive SGD, and the shuffled arm remove initial-function,
nonzero whole-update-norm, clipping, and adaptive-moment explanations as simple
accounts, but they do not equalize zero-step incidence, cumulative path length,
parameter-group allocation, per-parameter scale, gradient direction,
function-space displacement, curvature, visitation, or basin access. The
shuffled package also cannot separate training-time credit from evaluation-time
misbinding. The latent centrally aggregates private clues, so the functional
cuts do not prove natural temporal mediation.

Maximum mechanism-positive language is limited to this exact finite task: one
shared policy trained at `N={5,7}` with a binary clue-conditioned common latent
showed a registered held-out-`N=9` task-value or handoff-robustness advantage
over the live two-to-eight-state containing latent; it passed the registered
commonality and temporal-persistence functional cuts, exceeded the
separately trained-and-evaluated context-shuffled coarse package, and had
lower registered fragmentation than flexible.

For `ALL_LEARNED_ZERO_MISSION`, maximum language is only that deterministic
support passed but all three learned packages produced zero mission success
throughout the complete ordinary panel, leaving the finite-budget comparison
nonidentified. The exact formulation ends without retaining either package or
implying representability/general-family failure.

After either coarse-positive branch, the sole prospective next discriminator
is a new `SHARED-SUBSPACE-AND-NONZERO-STEP-MATCHED-FLEXIBLE-CONTROL` that
preserves containment while matching the coarse-compatible group's nonzero
update norm and controlling zero-step incidence. It requires a new portfolio
decision and is not authorized. After branch 2 or branches 5-7, no within-CPC
discriminator is justified.

No branch establishes uniquely correct cardinality, optimizer-independent
causation, natural mediation, arbitrary/continuous `N`, within-episode total-
count change, unseen clue laws, communication optimality, safety, a four-state
codebook, second surface, UAV-simulator value, or flight performance.

### Activity and authority boundary

Scientific activity begins at the first materialized or inspected random
initialization, target, clue, role permutation, handoff identity, latent,
action, rollout, optimizer state, stochastic coordinate, training/evaluation/
cut object, or parameter update. Definition, algebra, static source
reading, parameter arithmetic, deterministic shape checks, and hand-written
fixtures are preactivity.

No source change, build, test, probe, coordinate, initialization, stochastic
object, training, evaluation, compute, second surface, or UAV action is
authorized by this review.

## Required audit

Stress-test at least:

1. whether the task actually distinguishes hidden-plan fragmentation from
   clue aggregation or ordinary target inference;
2. whether the hierarchical flexible class exactly contains the binary policy,
   has a live strict witness, is function-matched at initialization, and fences
   rather than overclaims its unmatched optimization trajectory;
3. whether context derangement, commonality, and temporal-reset controls have
   the stated marginals and causal limits;
4. whether the normalized-gradient rule and objective are fully defined and
   correctly fence conditional nonzero-step matching and remaining optimizer
   alternatives;
5. whether seed-level pairing, bounds, equivalence logic, and precedence are
   exhaustive and mutually exclusive;
6. whether any result can be mislabeled as package value, robustness,
   mechanism, equivalence, or family deletion; and
7. whether the activity and claim boundaries are complete.

## Required response format

Return each heading exactly once:

### CLOSURE_AUTHORITY_DECISION

`CLOSED` or `REVISION_REQUIRED`, exact revision, and defect count.

### MATHEMATICAL_AND_CAUSAL_AUDIT

Audit host, arms, containment, learning law, controls, inference, and branches.

### DEFECT_LEDGER

For every defect give the smallest prospective repair and affected conclusions.

### STRONGEST_ALTERNATIVE

Give the strongest surviving explanation after the controls.

### MAXIMUM_CLAIM_CEILING

Give exact permitted language for every scientifically distinct branch.

### NEXT_HIGHEST_INFORMATION_DISCRIMINATOR

Name one only if it is prospectively coherent; do not authorize it.

Do not review implementation, tests, runtime, transport mechanics, resource
compliance, technical acceptance, or portfolio ranking.
