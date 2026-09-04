# SCDMP TBOV support-representation factorial revision 02 Pro closure

Continue the existing dedicated ChatGPT Pro conversation for
`direction:semigroup_consistent_duration_model_policy`. Your immediately prior
review returned `REVISION_REQUIRED` for exactly two branch-registry defects in
revision 01. This message freezes the complete prospective successor
`SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02` by incorporating the entire
revision 01 composite and replacing only those two definitions. No scientific
activity occurred under revision 01.

Review only mathematical and causal closure. Do not review code, files, tests,
runtime, hashes, receipts or technical implementation. Do not authorize
construction, coordinates, training, compute, an order treatment, Stage B,
another surface or UAV work. This request does not include or reveal the
independent Gemini answer.

## Complete successor question and invariant object

The object is exactly one checkpoint-only `2 x 2` factorial across ten fresh
paired seeds at the unchanged 600-step AdamW budget and unchanged per-seed
`0.65` untouched-fit-support competence ceiling. It asks whether direct
checkpoint competence is materially changed by:

1. current versus support-stratified equal-row training allocation;
2. current token-only versus one context-conditioned segment representation;
3. their interaction.

The deterministic fixed-four-carrier task, legal observations/actions, event
words, fit durations `{4,10}`, target diagnostics `{6,8,12}`, state product
law, direct terminal-state/reward outputs, all-contiguous-segment targets,
standardized direct loss, row/atom weights, precision and one-based AdamW law
are unchanged from the reviewed revision 01 composite. There is no relation
loss or correct/reversed comparison. No outcome may select `ORDER-TR`, select
`ORDER-Q`, open Stage B or transfer an old treatment label.

No r07 or revision 01 seed, coordinate, row, scale, checkpoint, optimizer
state, assay value or branch fact transfers. The operative prospective HMAC
namespace is newly `SCDMP-TBOV-SRF-CHECKPOINT-r02/...`.

## Exact four cells, support and representation

```text
S0R0 = current 4,096-row allocation x current token-only GRU
S1R0 = support-stratified 4,096-row allocation x current token-only GRU
S0R1 = current 4,096-row allocation x context-conditioned GRU
S1R1 = support-stratified 4,096-row allocation x context-conditioned GRU.
```

Each fresh seed contains all four cells. At a support level both
representations receive identical rows, targets, scalers and minibatch order.
At a representation level the two support cells clone the same initialized
parameters before their different data are used. All four cells share one
fresh untouched fit-support panel and target-diagnostic panels within a seed.

`S0` is the exact current allocation: 16 balanced
`(k,sigma,gamma,orientation)` word cells, an independently balanced global
81-action roster and independent product-uniform states.

`S1` has the same 4,096 equally weighted rows and marginal task law. Each word
cell has 256 rows; all 81 actions occur three times and 13 fresh seed-permuted
actions occur a fourth time. Independently for each of nine continuous state
coordinates, a randomized 4,096-stratum Latin-hypercube permutation with
independent jitter supplies the exact uniform marginal. The complete
word-action roster is independently permuted. Every row retains the complete
word and every legal contiguous-segment target. `S1` changes coverage
allocation only, not data count, task support, duration set, loss or evaluation
law.

`R0` is the exact current token-only width-32 unidirectional GRU with zero
initial state, followed by the unchanged `q0` trunk and direct state/reward
heads.

For `R1`, the same normalized legal boundary-state/action/actual-duration
input `q0 in R^14` gives

```text
c=SiLU(W_c q0+b_c) in R^32
v_t=concat(e_t,c) in R^37.
```

The exact current width-32, zero-initial-state unidirectional GRU gate law is
applied to `v_t`; its final state is concatenated with the unchanged `q0`
trunk, and the unchanged heads emit direct terminal state and reward. `R1` has
no position, attention, bidirectionality, oracle, intermediate true state,
physical coefficient, correct/reversed flag or relation loss. Same-shaped
recurrent/trunk/head matrices are paired identically across representations;
representation-specific input matrices use disjoint substreams. One `R0`
initialization and one `R1` initialization are each cloned across support
levels.

These are total finite-package effects. The support package includes changed
roster/scaler/gradient geometry. The representation package includes new input
parameters, parameter count, initialization and optimizer geometry. Neither is
a unique-mechanism estimand.

## Optimizer, evaluation, competence and effects

Every cell uses exactly 600 logical AdamW steps:

```text
theta_0=initialized parameters; m_0=v_0=0
n=1,...,600; b=n-1
gradient at theta_(n-1), one global clip
bias correction 1-beta1^n and 1-beta2^n
sole checkpoint theta_600.
```

There is no early stopping, sweep, second budget or continuation. The complete
atomic panel contains 40 checkpoints, 24,000 logical steps and 224,604,160
model-example evaluations.

Within each seed, all cells share one fresh disjoint 1,024-row untouched
fit-support panel and the complete fresh target diagnostics at `k={6,8,12}`.
For cell `ab` and seed `s`, lower is better:

```text
rho_ab,s=E_model_ab,s/E_mean_ab,s
rho_ab,s<=0.65 for every s=0,...,9.
```

Every denominator is finite and positive. `CELL_COMPETENT_ab` additionally
requires the exact current target-ratio mean/upper gates, all 270 coordinate-
variance gates and all 30 action-sensitivity gates. The valid four-cell
competence vector is orthogonal to the factor-effect branch.

Within seed:

```text
S_s=0.5[(rho_00-rho_10)+(rho_01-rho_11)]
R_s=0.5[(rho_00-rho_01)+(rho_10-rho_11)]
I_s=(rho_01-rho_11)-(rho_00-rho_10).
```

Positive `S` favors stratification; positive `R` favors the context GRU;
positive `I` means the support benefit is larger under `R1`. Across the ten
paired seed blocks, each effect receives a two-sided Student-t interval with
`df=9`. The three intervals use Bonferroni family error `0.05`, per-interval
coverage `1-0.05/3` and critical quantile
`t_(1-0.05/(2*3),9)`. Exact sign randomization is secondary.

The single practical margin remains `delta=0.01`:

```text
X_POS: lower_X>+delta
X_NEG: upper_X<-delta
X_SMALL: lower_X>-delta and upper_X<+delta
X_ACTIVE: X_POS or X_NEG.
```

## Complete revised first-true map

The 40-checkpoint panel is atomic. No partial cell, seed, checkpoint,
evaluation or effect is inspected or interpreted. After complete technical
acceptance apply exactly this first-true map:

1. `FACTORIAL-MEASUREMENT-NONIDENTIFICATION` for incomplete atomic identity,
   a nonfinite/nonpositive denominator, nonfinite registered outcome or broken
   shared evaluation. Attach only `COMPETENCE-VECTOR-UNAVAILABLE`; call no cell
   competent or incompetent and report no partial vector.
2. `INTERACTION-EFFECT` if `I_ACTIVE`; report its sign and keep main effects
   conditional diagnostics.
3. `ADDITIVE-SUPPORT-AND-REPRESENTATION-EFFECTS` if `I_SMALL` and both main
   effects are active; report both signs.
4. `SUPPORT-EFFECT` if `I_SMALL`, `S_ACTIVE` and `R_SMALL`.
5. `REPRESENTATION-EFFECT` if `I_SMALL`, `R_ACTIVE` and `S_SMALL`.
6. `NO-USEFUL-FACTOR-EFFECT` if all three are small; this is bounded practical
   smallness only for the exact factorial, not equality or family deletion.
7. `MIXED-FACTOR-EVIDENCE` if at least one factor is active but no preceding
   isolation pattern holds; report every active sign and unresolved factor.
8. `FACTORIAL-EFFECT-INDETERMINATE` otherwise: the valid complete panel
   measured checkpoint competence as stated by the attached vector, but the
   simultaneous intervals established neither an active nor a bounded-small
   registered factorial pattern. This does not imply that no cell is competent
   or that the original checkpoint problem persists.

For branches 2--8 attach exactly one of: no competent cell; one named competent
cell; multiple named competent cells; all cells competent. The modifier never
changes the effect branch, selects an order treatment or opens Stage B.

## Exact revision delta, alternatives and claim ceiling

Relative to revision 01, revision 02 changes only:

1. measurement nonidentification now has competence vector `UNAVAILABLE`; and
2. the final branch is `FACTORIAL-EFFECT-INDETERMINATE` with the interpretation
   above.

It changes no factor, cell, data/model law, optimizer, seed, threshold,
confidence family, budget, endpoint, treatment, activity boundary or claim
ceiling. The namespace suffix changes to `r02` solely to bind the operative
prospective revision identity.

The strongest alternative remains finite package geometry: changed scales,
output weighting, finite coverage, parameter count, initialization, curvature,
clipping and AdamW history can explain favorable effects without a unique
support-coverage or context-conditioning mechanism.

The maximum possible claim is only that the prospectively specified support
allocation package, context-conditioned representation package or their
interaction materially changed the direct checkpoint error ratio at the exact
600-step budget, with the valid four-cell competence vector reported
separately. No unique mechanism, relation direction, semigroup or task value,
held-out/switch-`k` benefit, arbitrary `k`, variable `N`, treatment selection,
Stage B, second surface, UAV, safety or deployment claim follows.

## Required disposition

Return exactly one leading line:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

Then state whether the two revision 01 defects are closed, whether the complete
map is exhaustive/reachable/noncontradictory with the orthogonal competence
modifier, the strongest alternative, the exact claim ceiling and every exact
remaining mathematical or causal defect. Do not propose threshold relaxation,
seed replacement, coordinate reuse, budget search, construction, activity,
Stage B or a portfolio decision.
