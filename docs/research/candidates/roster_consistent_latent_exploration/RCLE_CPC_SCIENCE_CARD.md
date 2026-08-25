# RCLE coarse persistent-commitment science card

```text
direction=roster_consistent_latent_exploration
object=RCLE-COARSE-PERSISTENT-COMMITMENT-DEFINITION
exact_revision=RCLE-CPC-SCIENCE-20260815-04
owner=EM_roster_consistent_latent_exploration
stage=definition_only
scientific_activity_started=false
old_rcle_objects=complete_immutable_not_reused
empirical_authorization=false
```

Revision 04 prospectively supersedes revision 03 after result-blind Pro review
and before scientific activity. It preserves revision 03's function-matched
live containing comparator, complete probability law, inference, and branch
actions, while accepting the sole remaining Pro defect: every mechanism
contrast is a seed-level effect computed exclusively on the held-out `N=9`,
`handoff=true` panel. No arm, DGP, seed, sample count, threshold, endpoint,
observation, or primary estimand changes.

## Question and decision value

This object asks whether a deliberately coarse episode-common latent can carry
one hidden deployment commitment across a membership handoff better than a
strictly more flexible learned latent under a fixed finite optimization budget.
The task is a target-bound dual-corridor search/relay handoff. Initial agents
receive noisy private target clues, choose a corridor, then a balanced subset is
replaced before a second decision. New agents do not receive the old clues or
actions. A latent sampled from the initial clue set is the only team-common
object that can preserve the realized plan across that handoff.

The decision is useful because the prior RCLE result supports functional
sensitivity to a common persistent correlation device but does not support its
old four-strategy codebook or a semantic-score advantage. This is a new target,
new treatment, new comparator, new objective, new counts, new thresholds, new
seeds, and new result law. It is not a B2 repair or rerun.

The primary proposition is finite-budget and package-level:

> On this exact roster-change target task, does a binary common persistent
> commitment bottleneck improve held-out-`N` mission value or reduce the
> roster-change value penalty relative to a strictly containing learned latent
> with up to eight effective states, without materially harming the other
> endpoint?

The secondary proposition is narrower:

> If the binary package wins, do the two frozen-checkpoint evaluation cuts show
> functional dependence on one shared realization and temporal persistence;
> does the intact context-bound coarse package exceed the separately trained
> and evaluated context-shuffled coarse package; and does coarse reduce the
> registered behavioral-fragmentation endpoint?

## Isolation from completed RCLE objects

Nothing numerical or learned is inherited from B1 or B2. In particular this
revision uses no four-rotation codebook, posterior-identity objective,
accepted-roster host, B2 thresholds, B2 seed, B2 checkpoint, B2 stochastic
coordinate, or B2 result. The old objects remain immutable.

The only inherited direction-level hypothesis is qualitative and bounded: a
common persistent latent may be useful as a coarse correlation-and-commitment
device even when a richer semantic alphabet is not justified. The present
experiment must establish its own task value and robustness.

## Frozen host: dual-corridor search/relay handoff

### Episode variables

An episode has roster size `N in {5,7,9}`. Training uses `N in {5,7}` only;
`N=9` is held out until final evaluation. One shared manager and one shared
agent policy are used at every size. Neither is retrained or adapted at `N=9`.

The hidden target corridor is

```text
G ~ Uniform({LEFT, RIGHT}).
```

The initial roster contains exactly `ceil(N/2)` SENSOR agents and `floor(N/2)`
RELAY agents. Role assignment is a uniformly random permutation and is public.
Each initial agent independently receives a one-bit private clue `S_i` with

```text
P(S_i = G | G) = 0.70.
```

No agent, policy, or latent manager receives `G`, reward, future membership, or
another agent's action. The manager receives only the unordered multiset of
initial `(role_i, S_i)` pairs and the public current `N`. Each actor receives
its own role, own clue or a missing-clue marker, public phase, current `N`, and
its assigned latent input.

### Decisions and roster handoff

There are exactly two simultaneous team decisions:

1. `PRE`: every initial agent chooses `LEFT`, `RIGHT`, or `HOLD`.
2. `POST`: after the membership handoff, every active agent chooses the same
   three-way action once.

No reward, target truth, aggregate action, majority, or validity signal is
revealed between the decisions. The shared actor is memoryless and receives no
agent identity, previous action, team history, or recurrent state. A surviving
agent retains only its own clue. A newcomer receives the missing-clue marker.

The handoff replaces a fixed role-balanced subset:

```text
N=5: remove and replace 1 SENSOR + 1 RELAY
N=7: remove and replace 2 SENSOR + 1 RELAY
N=9: remove and replace 2 SENSOR + 2 RELAY
```

Removed identities are sampled uniformly within role. Replacements have the
same roles, no clue, and no access to departed-agent state. Total `N` is held
constant within an episode so the comparison isolates membership turnover;
variable `N` is across episodes and includes the frozen held-out size.

Training contains four cells in equal proportion:

```text
(N=5, no handoff), (N=5, handoff),
(N=7, no handoff), (N=7, handoff).
```

Final evaluation contains those cells plus `(N=9, no handoff)` and
`(N=9, handoff)`. A no-handoff episode keeps the same identities and clues at
`POST` but otherwise uses the identical law.

### Physical validity and target value

For phase `p`, let `n^p_{r,c}` be the number of agents with role `r` choosing
corridor `c`. The phase is physically valid when every corridor used by at
least one SENSOR also has at least one RELAY:

```text
V_p = 1 iff for c in {LEFT,RIGHT},
            n^p_{SENSOR,c} > 0 implies n^p_{RELAY,c} > 0.
```

`HOLD` is legal but contributes to neither corridor. Let

```text
A_p = number of active agents choosing G / N
Q_N = ceil(0.60 N)
T_p = 1 iff number choosing G >= Q_N
              and n^p_{SENSOR,G} >= 1
              and n^p_{RELAY,G} >= 1.
M = V_PRE * V_POST * T_PRE * T_POST.
```

The bounded episode value, used identically by every arm, is

```text
Y = 0.65 M
    + 0.15 A_PRE
    + 0.15 A_POST
    + 0.025 V_PRE
    + 0.025 V_POST.
```

Thus `0 <= Y <= 1`. `M` is the mission-success endpoint. `Y` is the primary
value endpoint. The two validity terms are the only validity shaping; there is
no latent-identity, mutual-information, posterior-confidence, or semantic
auxiliary in any arm.

### Commitment fragmentation observable

Let `C_PRE` be the unique majority corridor among non-`HOLD` `PRE` actions. If
there is a tie or every agent holds, set `C_PRE=invalid`. Define

```text
F = 1,                                      if C_PRE=invalid;
F = 1 - (# POST actions equal C_PRE)/N,     otherwise.
```

`F` is a behavioral fragmentation endpoint, not part of the reward. It measures
whether the post-handoff roster follows the realized pre-handoff commitment;
it does not by itself say that the commitment was target-correct.

## Latent manager and shared actor

All learned arms instantiate the same maximum architecture and allocated
parameter count. The parameterization separates a binary macro commitment from
an optional four-way refinement, making the coarse policy an exact, reachable
subfamily of the flexible policy rather than a masked approximation.

- Each manager element is the concatenation of a two-way role one-hot and a
  clue scalar in `{-1,+1}`. A `3-32-32` `tanh` element MLP mean-pools the
  unordered roster; the pooled vector is concatenated with `N/9`.
- A two-logit macro head produces
  `p(C | set,N)=softmax(a)` for unanchored labels `C in {0,1}`. No hardcoded
  map connects a macro label to a physical corridor.
- A separate eight-logit refinement head is reshaped into two four-logit rows.
  For each macro value `C`, `q(U | C,set,N)=sparsemax(v_C)` for
  `U in {1,2,3,4}`. The flexible effective state is `(C,U)`, giving between two
  and eight positive-probability joint states; the coarse actor ignores `U`.
- The actor input concatenates a role one-hot, a three-way
  `LEFT/RIGHT/MISSING` clue one-hot, a two-way `PRE/POST` phase one-hot, `N/9`,
  and an eight-dimensional latent vector. It passes through an exact
  `64-64-3` `tanh` MLP and a three-way action softmax.
- Latent vectors are parameterized as a two-row macro base `e_C` plus an
  eight-row refinement residual `r_CU`. `COARSE-PERSISTENT` and its shuffled
  control hard-multiply every residual by zero. `FLEXIBLE-PERSISTENT` uses
  `e_C+r_CU`.
- Every arm allocates the macro head, refinement head, two base embeddings,
  eight residual embeddings, and identical actor. Coarse-only masked residuals
  and refinement-score paths receive exactly zero gradient; no dummy parameter
  contributes to the gradient norm.
- The actor and manager receive no target truth, reward, validity, majority,
  other-agent action, roster identity, or post-handoff message.

For `v in R^4`, sparsemax is the unique Euclidean projection onto the
probability simplex:

```text
q_i = max(v_i - tau, 0),  with sum_i q_i = 1.
```

The active set is `A={i:q_i>0}`. Its registered derivative is
`dq_i/dv_j = 1[i,j in A]*(1[i=j]-1/|A|)`; a coordinate exactly at zero is on
the inactive side. Stable lexicographic index order resolves computational
sort ties but cannot change the unique forward projection. A sampled
refinement always has positive probability, so its log score is finite. No
entropy of a zero-probability sparsemax coordinate is used.

All hidden nonlinearities are `tanh`; every affine layer includes a bias. No
recurrence, attention over actions, agent ID, checkpoint transfer, or
post-handoff manager call is permitted.

## Frozen learned arms

### `COARSE-PERSISTENT` — treatment

One unanchored macro commitment `C in {0,1}` is sampled from `p(C|set,N)` after
the initial set is observed, broadcast to every initial agent, retained
unchanged, and broadcast to every survivor and newcomer at `POST`. The actor
receives `e_C`; the refinement distribution and residuals have no forward or
score path.

### `FLEXIBLE-PERSISTENT` — containing comparator

One macro `C` is sampled from the identical binary head, then one refinement
`U` is sampled from `q(U|C,set,N)`. The joint state `(C,U)` is broadcast once
and persisted under the same law; the actor receives `e_C+r_CU`.

This policy class strictly contains the treatment. Setting every `r_CU=0`
reproduces every coarse policy exactly for every legal input and for any
refinement probabilities. Strictness is witnessed on a hand-specified fixture
of identical local observations by three positive refinement states with
distinct action distributions: their induced common-mixture joint-action
matrix has rank at least three, whereas the binary coarse mixture has rank at
most two. The witness must be output-connected through nonzero actor Jacobians.

All residuals initialize at exactly zero, so the coarse and flexible policies
have identical action distributions on every legal input before the first
update. Flexible residuals nevertheless have nonzero first-order actor
Jacobians and are trainable immediately; sampled refinements can therefore
diverge after the first update. The refinement score is active only in the
flexible arm. This establishes policy-function containment and a live strict
extension, not matched optimization trajectories. Effective cardinality and
occupancy are descriptive and never selected after the result.

### `CONTEXT-SHUFFLED-COARSE` — learned-package context control

The binary macro treatment and all other treatment machinery are retained.
Within each training block and each `(N,handoff)` cell, a frozen science-law
cyclic
derangement maps every episode to another episode in that same cell. Episode
`b` receives the source episode's already sampled common persistent macro
commitment: source `j` uses its own manager distribution and source-keyed
inverse-CDF uniform, and the cyclic map assigns that realized sample to its
recipient. Thus every within-arm cell preserves the exact realized latent
multiset while no recipient uses its own initial set.
The score-function term is charged to the distribution that generated the
sample and to the recipient episode's outcome. The nonzero cyclic shift is
redrawn from the frozen product family each block and has no fixed points.

At evaluation, the same construction pairs each episode to another episode in
the same cell. It preserves the binary macro alphabet, commonality, persistence, latent
marginal exposure, manager/actor calls, update count, score-function form, and
optimizer opportunity while breaking the episode's clue-to-latent binding. It
does not claim exact equality of realized gradient direction or trajectory.
Because this arm is trained and evaluated under the derangement, its contrast
with intact coarse is a between-package effect of preserving own-context
binding throughout learning and evaluation. It is not an evaluation-only
intervention on one frozen checkpoint and cannot isolate training-time credit,
evaluation-time misbinding, or their interaction.

## Commonality and persistence interventions

Two frozen evaluation-only interventions are applied to the final
`COARSE-PERSISTENT` checkpoint on the same held-out `N=9` handoff panels:

1. `PRIVATE-LATENT-CUT`: each active agent independently samples its own macro
   commitment from the intact episode's manager distribution. A survivor retains
   its own draw; each newcomer draws independently on entry. No common realized
   latent exists.
2. `TEMPORAL-RESET-CUT`: one common macro commitment is used at `PRE`; at the
   handoff a second common commitment is independently redrawn from the same stored
   manager distribution and used at `POST`.

Both cuts retain weights, signals, manager distribution, latent alphabet,
actor, roster, actions, reward, evaluation budget, and stochastic marginal.
They change only the realized commonality or temporal identity. They are
functional interventions on the learned package, not claims of natural
mediation. The context-shuffled learned-package contrast is not one of these
two frozen-checkpoint interventions.

## Training law and optimizer matching

Every learned arm uses the same task coefficient, cell baseline rule, action
score, optimizer, and update schedule. A block contains 64 complete episodes,
16 from each training cell. For recipient episode `b`, let `x_b^src=x_b` for
the two intact arms and let it be the deranged same-cell context for the
shuffled arm. The exact latent/action log score is

```text
ell_b = log p(C_b | x_b^src)
        + 1[FLEXIBLE-PERSISTENT] * log q(U_b | C_b,x_b^src)
        + sum_i log pi(A^PRE_bi | o^PRE_bi, latent_b)
        + sum_j log pi(A^POST_bj | o^POST_bj, latent_b).

L_a = -(1/64) * sum_b stop(Y_b - b_{a,N_b,h_b}) * ell_b.
```

There is no entropy bonus, validity-only auxiliary, reward normalization,
posterior, reconstruction, learned critic, curriculum, early stopping, or
adaptive horizon. Thus all arms receive the identical task value—including
the identical validity shaping—and the shuffled control matches the coarse
score dimension and optimizer opportunity while removing own-context binding.

Every cell baseline starts at zero. After the parameter update, all four cell
baselines update exactly once using that block's 16-episode cell mean:

```text
b_{a,N,h} <- 0.95*b_{a,N,h} + 0.05*mean_cell(Y).
```

Baselines are stopped scalars and are not optimizer parameters.

All arms use one joint plain-SGD update per complete block, no momentum, no
weight decay, and no adaptive moments. `||g_raw||_2` is the Euclidean norm of
the concatenated gradient over the complete registered parameter tensor. The
raw joint gradient is converted to

```text
g_update = 0                         if ||g_raw||_2 = 0;
g_update = 0.10 * g_raw/||g_raw||_2  otherwise,
theta <- theta - 0.01 * g_update.
```

Every nonzero raw block gradient therefore produces a whole-parameter update
of Euclidean norm exactly `0.001`; an exact zero gradient produces no update.
The rule removes variation in nonzero whole-parameter update norm and avoids
clipping/adaptive-moment differences. It does not equalize zero-update
incidence, cumulative path length, parameter-group allocation, per-parameter
scale, gradient direction, function-space movement, curvature, visitation, or
basin access. Zero-gradient frequency remains descriptive and cannot support
or defeat a branch. Any positive result is a finite-budget package claim, not
optimizer-independent cardinality causation.

For every affine weight with fan-in `d_in` and fan-out `d_out`, entries are iid
uniform on `[-sqrt(6/(d_in+d_out)), +sqrt(6/(d_in+d_out))]`; every affine bias
is zero. Macro-base embedding entries are iid uniform on
`[-1/sqrt(8),+1/sqrt(8)]`. Every refinement residual is exactly zero. Within a
seed, the complete initial tensor is copied bit-for-bit across all arms; no
arm-specific initialization is permitted. All optimizer state is initially
empty. Every arm receives the same number of episodes, complete blocks,
actor/manager forwards, joint updates, and final-checkpoint evaluations. The
fixed terminal is update 1,000; no checkpoint selection or restart selection
is permitted.

### Science-level probability and coupling law

Before any materializer is chosen, the scientific probability object is a
product family of independent continuous `Uniform(0,1)` variables indexed by
seed, initialization entry, training/evaluation cell, block or panel episode,
variable kind, phase, and active roster slot. Distinct semantic indices are
independent except for the following frozen pairings:

- target, role permutation, clues, handoff identities, and no-handoff/handoff
  status are identical across arms within a seed and episode;
- the macro-latent and action inverse-CDF uniforms are paired across arms when
  the corresponding conditional distribution and recipient semantics exist;
- flexible refinement uniforms are independent of all macro and action
  uniforms;
- each 16-episode training cell uses a uniformly selected cyclic shift in
  `{1,...,15}` for the shuffled source map; each 2,048-episode evaluation cell
  uses a uniformly selected shift in `{1,...,2047}`; shuffled latent draws stay
  keyed to their source episode before that realized draw is reassigned; and
- intervention draws are fresh but paired on every unchanged exogenous
  variable and action uniform.

This is an abstract distribution and coupling, not an RNG address binding or
coordinate materialization. A later CM would need a versioned materializer
only after a separate empirical authorization.

## Fresh experimental units and budgets

The 16 fresh independent training seeds are:

```text
4109, 4217, 4337, 4441, 4561, 4673, 4787, 4903,
5021, 5147, 5261, 5381, 5503, 5623, 5741, 5861
```

They were not used by B1 or B2. Each seed trains all three arms with paired
initialization and the independent science-level product families above. A seed packet
is complete only when all three final checkpoints and all evaluation cells are
present.

Prospective work counts are:

```text
training: 3 arms * 16 seeds * 1,000 blocks * 64 episodes = 3,072,000 episodes
ordinary evaluation:
  3 arms * 16 seeds * 3 N values * 2 handoff cells * 2,048 episodes
  = 589,824 episodes
held-out cuts:
  2 cuts * 16 seeds * 2,048 episodes = 65,536 episodes
```

The counts are scientific design inputs, not an execution authorization or a
runtime forecast.

## Evaluation, estimands, and inference

All evaluation is frozen before activity, uses no learning or adaptation, and
is paired across arms by exogenous target, roles, clues, handoff identities,
and policy-randomness variates wherever the arm semantics permit.

For arm `a`, seed `s`, size `N`, and handoff indicator `h`, let

```text
J_{a,s,N,h} = mean Y
S_{a,s,N,h} = mean M
F_{a,s,N,h} = mean F.
```

The two co-primary held-out comparisons are

```text
Delta_VALUE_s = J_COARSE,s,9,1 - J_FLEX,s,9,1
Penalty_a,s    = J_a,s,9,0 - J_a,s,9,1
Delta_ROBUST_s = Penalty_FLEX,s - Penalty_COARSE,s.
```

Positive `Delta_ROBUST` means the coarse arm loses less value to handoff.
Seed, not episode, is the independent inferential unit. Constitutively treat
the 16 registered seed-level vectors

```text
(Delta_VALUE_s, Delta_ROBUST_s, Delta_FRAGMENT_s,
 Delta_COMMON_s, Delta_PERSIST_s, Delta_CONTEXT_s)
```

as iid draws from one multivariate Normal seed-effect working model with an
unrestricted mean vector, positive-semidefinite covariance, and arbitrary
within-seed correlation. All coverage language below is nominal and
model-based under this working model, not distribution-free.

For any scalar seed effect `d_s`, define exactly

```text
d_bar = (1/16) * sum_s d_s
s_d^2 = (1/15) * sum_s (d_s - d_bar)^2
s_d = sqrt(s_d^2)
L_gamma(d) = d_bar - t_(df=15,gamma) * s_d/4
U_gamma(d) = d_bar + t_(df=15,gamma) * s_d/4.
```

Here `t_(df=15,gamma)` is the gamma quantile of Student's `t` distribution.
If `s_d=0`, both endpoints equal `d_bar`.

For primary selection, compute one simultaneous confidence rectangle for both
effects and both directions. Every lower and upper endpoint uses the one-sided
`gamma=0.9875` Student-`t` critical value (`alpha/4` for four tails), giving
nominal Bonferroni familywise 95% model-based coverage over
`{L_VALUE,U_VALUE,L_ROBUST,U_ROBUST}`. Define from this same rectangle

```text
VALUE_WIN  iff L_VALUE  >  0.06 and L_ROBUST > -0.02
ROBUST_WIN iff L_ROBUST >  0.06 and L_VALUE  > -0.02
COARSE_TARGET_WIN = VALUE_WIN or ROBUST_WIN.
```

The `0.06` margin is six points on the unit task-value scale; `0.02` is the
prospective nonharm allowance for the companion endpoint.

Define the mirror-image `FLEX_TARGET_WIN` using simultaneous upper bounds:

```text
(U_VALUE < -0.06 and U_ROBUST < 0.02)
or
(U_ROBUST < -0.06 and U_VALUE < 0.02).
```

`TARGET_NO_MATERIAL` holds only when that same simultaneous rectangle satisfies
all four inclusive conditions

```text
L_VALUE  >= -0.03
U_VALUE  <=  0.03
L_ROBUST >= -0.03
U_ROBUST <=  0.03.
```

Every other primary state is `TARGET_UNRESOLVED`; all other displayed branch
inequalities remain strict. Reusing one four-tail rectangle
prevents data-dependent choice of coarse, flexible, or equivalence language
from creating an unregistered directional family.

Mechanism and information contrasts at held-out `N=9` handoff are

```text
Delta_FRAGMENT_s = F_FLEX,s,9,1 - F_COARSE,s,9,1
Delta_COMMON_s   = J_COARSE-intact,s,9,1 - J_PRIVATE-CUT,s,9,1
Delta_PERSIST_s  = J_COARSE-intact,s,9,1 - J_RESET-CUT,s,9,1
Delta_CONTEXT_s  = J_COARSE,s,9,1 - J_SHUFFLED,s,9,1.
```

The final cell index `1` means `handoff=true`. No `N=9` no-handoff episode and
no average across the two held-out handoff-status cells enters any of these
four mechanism effects or the six-lower-bound mechanism family.

For the maximum mechanism-positive claim, compute a separate joint family over
the two primary lower bounds and these four mechanism lower bounds. Every one
of the six uses `gamma=1-0.05/6=0.991666666666...`, giving nominal Bonferroni
familywise 95% model-based coverage. Define

```text
FRAGMENTATION_REDUCED iff L6_FRAGMENT > 0.08
COMMONALITY_FUNCTIONAL iff L6_COMMON > 0.04
PERSISTENCE_FUNCTIONAL iff L6_PERSIST > 0.04
CONTEXT_BINDING_VALUE iff L6_CONTEXT > 0.04.
```

Within that six-bound family, define `COARSE_TARGET_WIN_6` by replacing the
primary-family lower bounds in `VALUE_WIN` and `ROBUST_WIN` with
`L6_VALUE,L6_ROBUST`. Mechanism support requires all four mechanism predicates
and `COARSE_TARGET_WIN_6`; the looser primary rectangle alone cannot license
mechanism language. `Delta_COMMON` and `Delta_PERSIST` support functional
dependence only under their registered frozen-checkpoint interventions.
`Delta_CONTEXT` supports only that the intact context-bound learned package
exceeded the separately trained-and-evaluated context-shuffled package; it
cannot establish evaluation-only context dependence. None proves natural
mediation. Mission success, role/corridor histograms,
macro/refinement occupancy and effective cardinality, manager distribution by
clue majority, gradient-direction cosine across paired arms, zero-gradient
frequency, and per-size results are descriptive diagnostics only and cannot
replace a registered predicate.

## Support and headroom

A deterministic full-information oracle that receives `G`, uses one common
persistent macro commitment, and routes a valid role mixture to `G` must attain
`Y=M=1` at every size and handoff cell. A same-information Bayes oracle uses
the majority of the initial clues with a fixed fair tie rule and the same
common persistent macro commitment. Exhaustive rational enumeration of all
`2^N` clue vectors must give exact mission-success probability

```text
sum_{k=(N+1)/2}^N choose(N,k) * (7/10)^k * (3/10)^(N-k)
```

for each odd `N`. Both oracle checks are deterministic preactivity support
facts; no stochastic oracle panel is part of this revision.

The containing relation has two required static support facts. First, copying
all coarse parameters into `FLEXIBLE-PERSISTENT` and setting every refinement
residual to zero must reproduce the coarse action distribution exactly on all
hand-specified legal fixtures for arbitrary refinement probabilities. Second,
a fixture with at least three positive refinements must exhibit a rank-three
common-mixture joint-action matrix with nonzero actor Jacobians, proving an
output-connected flexible policy outside the binary mixture class. These are
support checks, not evidence that a trained flexible arm found or needed the
extra capacity.

## Literal result map and family action

Apply the following precedence:

1. `INVALID_OR_INCOMPLETE`: any missing seed/arm/cell, changed host or score,
   forbidden information, nonfinite registered endpoint, failed oracle, failed
   containing proof, evaluation adaptation, or incomplete panel. No scientific
   comparison or family action follows from that panel.
2. `ALL_LEARNED_ZERO_MISSION`: on a valid complete panel, the deterministic
   support checks pass but `M=0` on every ordinary-evaluation episode for all
   three learned arms, all 16 seeds, every `N in {5,7,9}`, and both handoff
   cells. Report the registered finite-budget comparison nonidentified; retain
   neither `COARSE-PERSISTENT` nor `FLEXIBLE-PERSISTENT`; make no superiority,
   equivalence, no-effect, representability, or general latent-family claim;
   and end this exact CPC formulation.
3. `COARSE_MECHANISM_SUPPORTED`: `COARSE_TARGET_WIN_6` plus all four mechanism
   predicates. Retain the coarse persistent-commitment package for this named
   target and permit the maximum bounded mechanism language below.
4. `COARSE_PACKAGE_ONLY`: `COARSE_TARGET_WIN` but branch 3 does not hold,
   whether because the six-bound target gate or any mechanism predicate fails.
   Retain only the exact finite-budget coarse package as a
   target-value candidate; do not attribute the result to hidden-plan
   commonality, persistence, or clue binding.
5. `FLEXIBLE_CONTAINING_SUPERIOR`: `FLEX_TARGET_WIN`. Delete the fixed binary
   restriction for this target. The result does not by itself establish why
   the flexible controller won or that persistent latents are generally useful.
6. `NO_COARSE_ADVANTAGE`: `TARGET_NO_MATERIAL`. The flexible containing class
   matches the coarse package within the registered band, so the fixed coarse
   restriction is not retained for this target.
7. `TARGET_UNRESOLVED`: none of the preceding valid-complete branches. No
   positive, superiority, equivalence, failure, or no-effect claim is allowed;
   the exact assay supplies no retention evidence.

Branches 2 and 5 through 7 permit no coefficient, cardinality, seed,
extra-seed, threshold, optimizer, horizon, checkpoint, roster, reward, or
repeated-assay rescue of this exact object. A later materially different theory
requires a newly authorized object and is not a continuation of CPC. A valid
package-positive branch does not itself authorize source,
construction, coordinates, training, evaluation, compute, a second surface,
or UAV work.

## Strongest alternative

Even a complete mechanism-positive result does not identify a universal need
for binary latents. The binary effective-state restriction may regularize a
finite-budget search and produce more favorable gradient directions or basins
than the live two-to-eight-state containing controller. Exact initial-policy
matching, context shuffling, and fixed-norm nonadaptive optimization remove
initial function, treatment-specific semantic-score, adaptive-moment,
nonzero whole-update-norm, and clipping differences as simple explanations,
but they do not equalize zero-step incidence, cumulative path length,
parameter-group allocation, gradient direction, per-parameter scale,
function-space displacement, curvature, state visitation, or representational
search difficulty.

The cuts show only functional dependence under registered interventions. They
do not establish natural mediation. The latent also carries a centralized
summary of private clues, so a positive result can reflect clue aggregation as
well as temporal commitment. The claim language must preserve both
alternatives.

## Maximum claim ceiling

If `COARSE_MECHANISM_SUPPORTED`, the maximum claim is:

> On this exact finite dual-corridor search/relay handoff toy, one shared policy
> trained at `N={5,7}` with a binary clue-conditioned common latent achieved a
> registered held-out-`N=9` value or roster-change robustness advantage over an
> live two-to-eight-state containing latent under the fixed training budget. Its held-out
> value also passed the registered commonality and temporal-persistence
> functional cuts, it exceeded the separately trained-and-evaluated
> context-shuffled coarse package, and it had lower registered behavioral
> fragmentation than the flexible package.

This remains an exact-package result. It does not establish binary cardinality
as uniquely correct, optimizer-independent causation, natural mediation,
arbitrary or continuous `N`, changing total cardinality within an episode,
unseen clue laws, communication optimality, safety, a second surface, UAV
simulation value, or flight performance.

If only `COARSE_PACKAGE_ONLY` holds, remove every commonality, persistence,
fragmentation-mechanism, and clue-binding attribution. Other branches use only
their literal contrast-specific language. No outcome may reuse the old
four-strategy semantic codebook claim.

For `ALL_LEARNED_ZERO_MISSION`, the maximum language is only that deterministic
host and class support passed but all three learned packages produced zero
mission success throughout the complete ordinary panel, leaving the registered
finite-budget package comparison nonidentified. The exact CPC formulation ends
without retaining either package or implying a representability/general-family
failure.

If either coarse-positive branch retains the exact package, the one
highest-information prospective discriminator is a separately frozen
`SHARED-SUBSPACE-AND-NONZERO-STEP-MATCHED-FLEXIBLE-CONTROL` that preserves the
containing class while matching the coarse-compatible parameter group's
nonzero update norm and controlling zero-update incidence. It is a new object
requiring a later portfolio decision and is not authorized here. After branch
2 or branches 5-7, no within-CPC next discriminator is justified.

## Scientific activity boundary and current authorization

Question-relevant scientific activity begins at the earliest materialization or
inspection of any revision-04 random initialization, target, clue, role
permutation, handoff identity, latent, action, rollout, optimizer state,
training episode, evaluation episode, cut episode, or registered stochastic
coordinate, or at the first parameter update,
whichever occurs first. Discarding an object does not restore preactivity.

Pure ordinary-language definition, algebra, static source reading, parameter-
count arithmetic, deterministic shape checks, and explicitly hand-written
nonrandom fixtures remain preactivity.

This definition stage authorizes only the science card, mutually blind use of
the already authorized same-direction Pro/Gemini conversations, EM scientific
intake, and named-CM read-only static bindability/observability/comparator/cost
assessment after Pro closure. It authorizes no source change, build, test,
probe, coordinate materialization, initialization, stochastic object, training,
evaluation, compute lease, second surface, or UAV activity.
