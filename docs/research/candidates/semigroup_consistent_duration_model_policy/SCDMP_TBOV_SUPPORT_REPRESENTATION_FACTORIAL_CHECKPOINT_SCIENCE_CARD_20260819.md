# SCDMP TBOV support-representation factorial checkpoint science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT
revision=SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02
supersedes_revision=SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-01_BRANCH_REGISTRY_REPAIR_ONLY
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
portfolio_envelope=SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT-DEFINITION
old_exact_objects_immutable=true
old_result_coordinate_checkpoint_seed_transfer=false
scientific_activity_started=false
source_change_authorized=false
build_test_probe_authorized=false
coordinate_or_identity_binding_authorized=false
checkpoint_training_evaluation_authorized=false
lease_or_compute_authorized=false
order_treatment_selection_authorized=false
stage_b_authorized=false
```

## Question and answer-changing value

Revision 02 changes only two prospective result-registry definitions requested
by the same-direction ChatGPT Pro review of revision 01: measurement failure
now makes the entire competence vector unavailable rather than converting
unavailable cells into competence failures, and the final valid-measurement
branch is named factorial-effect indeterminacy rather than checkpoint
nonidentification. It changes no factor, cell, row, model, optimizer, seed,
threshold, confidence family, budget, endpoint, treatment, activity boundary
or claim ceiling. No scientific activity occurred under revision 01.

The completed exact r07 Stage-A object established physical order opportunity
but stopped at `MODIFY-CHECKPOINT`: five of ten independently trained direct
checkpoints exceeded the frozen untouched-fit-support error-ratio ceiling.
Target-ratio, coordinate-variance and action-sensitivity gates passed, so the
result did not distinguish finite-sample support allocation from segment
representation or their interaction.

This successor asks exactly one checkpoint-only question:

> At the same fixed 600-step optimizer budget and the same `0.65` per-seed
> untouched-fit-support competence requirement, is checkpoint competence
> materially changed by a prospectively support-stratified equal-row training
> allocation, by one prospectively specified context-conditioned segment
> representation, or by their interaction?

The experiment is one `2 x 2` factorial and no more. It contains no relation
loss, correct/reversed path comparison, order-treatment selection, policy
training or task-value evaluation. Every outcome returns only a checkpoint
support/representation conclusion. No outcome opens Stage B or transfers a
treatment label.

## Inherited target, observable and direct-output law

This card incorporates without scientific change the exact task, observation,
action, word, target and direct-supervision laws in
`SCDMP_TARGET_BOUND_ORDER_TO_VALUE_SCIENCE_CARD_REVISION_07.md`:

- the deterministic fixed-four-carrier payload state
  `(y,v,psi,omega,b,z_FL,z_FR,z_RL,z_RR)`;
- held joint actions `u_i in {-1,0,+1}` and lexicographic 81-action order;
- physical event alphabet `{C,S+,S-,G+,G-}`, micro-dynamics, reward and
  failure law;
- fit durations `K_fit={4,10}` and untouched target durations `{6,8,12}`;
- the prospective product state law and exact sign/orientation balance;
- direct outputs `F_theta` for absolute terminal state and `G_theta` for
  undiscounted segment reward;
- normalized state/action/duration input `q0`, all-contiguous-segment targets,
  standardized direct loss, row weighting, segment-atom weighting and scale
  construction;
- float64 truth and reductions, float32 model/optimizer arithmetic, legal
  action enumeration and lexicographic ties.

No r07 coordinate, row, master, seed key, checkpoint, scale, optimizer state,
assay value or branch fact enters this object. The previously observed r07
result motivates the prospective factors only. All result-bearing coordinates
below are fresh and mutually disjoint.

## Exact `2 x 2` factorial

Let support level `S in {S0,S1}` and representation level `R in {R0,R1}`.
The four indivisible cells are:

| Cell | Training support | Segment representation |
| --- | --- | --- |
| `S0R0` | current r07 allocation | current token-only GRU |
| `S1R0` | support-stratified equal-row allocation | current token-only GRU |
| `S0R1` | current r07 allocation | context-conditioned GRU |
| `S1R1` | support-stratified equal-row allocation | context-conditioned GRU |

There are exactly ten fresh paired seed blocks `s=0,...,9`. Each seed contains
all four cells. Within a seed, the two representation cells at the same support
level receive exactly the same training rows, segment targets, scalers and
minibatch order. The two support cells at the same representation level clone
one byte-identical initialization before their different training rows are
used. All four cells use the same untouched fit-support and target-diagnostic
evaluation rows for that seed.

The factorial estimates total finite-budget package effects. A representation
effect includes the new input parameterization and its optimizer geometry. A
support effect includes its changed training roster and the scaler induced by
that roster. Neither is a unique-mechanism claim.

## Support factor

### `S0`: current allocation

`S0` uses exactly the r07 checkpoint-fit allocation law for 4,096 rows per
seed. The 16 lexicographic word cells
`(k,sigma,gamma,orientation)` are balanced, the 81 joint actions form an
independently balanced roster with counts differing by at most one, continuous
states are independent product-uniform draws, and the word-cell and action
rosters are independently seed-keyed and permuted. Every row carries its
complete word and all legal nonempty contiguous-segment targets.

### `S1`: support-stratified equal-row allocation

`S1` also has exactly 4,096 rows and exactly the same marginal task law,
durations, words, actions, state support, row weight, segment list and direct
loss. It changes only prospective allocation:

1. Each of the 16 lexicographic word cells receives exactly 256 rows.
2. Within each word cell, every one of the 81 lexicographic joint actions
   appears three times, and exactly 13 actions selected by that cell's fresh
   seed-keyed permutation appear once more. Thus every word-action count is
   either three or four and each word cell remains exactly size 256.
3. For each of the nine continuous state coordinates independently, form one
   fresh randomized Latin-hypercube permutation of the integers
   `0,...,4095`. For materialization row `r`, draw one fresh jitter
   `u in [0,1)` and map `(perm[r]+u)/4096` affinely to that coordinate's
   registered product-law interval. Every coordinate therefore occupies each
   of its 4,096 one-dimensional strata exactly once while retaining the exact
   uniform marginal.
4. The complete word-action roster is Fisher-Yates permuted independently of
   every coordinate permutation. No evaluation row, target coordinate or
   observed r07 value enters allocation.

`S1` is not more data, a different loss or a target-informed replay. It is a
same-row-count coverage design for the known prospective product support.

## Representation factor

### `R0`: current token-only GRU

`R0` is the exact r07 direct segment model. A one-layer unidirectional
bias-bearing GRU of hidden width 32 receives only the event one-hot sequence
in public order `(C,S+,S-,G+,G-)` with zero initial hidden state. Its final
hidden state is concatenated with the unchanged two-layer `q0` trunk; the
unchanged two-layer state and reward heads emit `F_theta` and `G_theta`.

### `R1`: context-conditioned GRU

`R1` changes exactly the segment representation and nothing else. For the
actual segment start state, held action and actual segment length, form the
same normalized `q0 in R^14` as r07 and compute

```text
c = SiLU(W_c q0 + b_c) in R^32.
```

At every literal event position `t`, form

```text
v_t = concat(e_t, c) in R^37,
```

where `e_t` is the same fixed five-dimensional event one-hot. Feed `v_t` to a
one-layer unidirectional bias-bearing GRU with hidden width 32, zero initial
hidden state and the exact r07 gate order and equations:

```text
r_t=sigmoid(W_ir v_t+b_ir+W_hr h_(t-1)+b_hr)
z_t=sigmoid(W_iz v_t+b_iz+W_hz h_(t-1)+b_hz)
n_t=tanh(W_in v_t+b_in+r_t*(W_hn h_(t-1)+b_hn))
h_t=(1-z_t)*n_t+z_t*h_(t-1).
```

Only `h_ell` is retained. The unchanged r07 `q0` trunk is still computed and
concatenated with `h_ell`; the state and reward heads, outputs, scales, loss,
precision and masking are unchanged. A contiguous segment receives its true
segment-start state and actual `ell`, never the full parent-word duration.

`R1` has no position input, attention, bidirectionality, oracle feature,
intermediate true state, physical parameter, relation label, correct/reversed
flag or order-specific auxiliary. It is a direct containing alternative whose
only scientific change is allowing literal event processing to depend on the
legal boundary state, held action and segment duration.

### Initialization pairing

All matrices use the r07 row-major Xavier-uniform law with one final float32
cast; every bias is exactly float32 zero. For each seed:

- same-shaped hidden-to-hidden GRU, trunk and output-head matrices use common
  raw draws and therefore identical initial values across `R0` and `R1`;
- `R0`'s `32 x 5` event-input matrices use the `init/R0_input` substream;
- `R1`'s `W_c` and `32 x 37` context-event input matrices use the disjoint
  `init/R1_context` and `init/R1_input` substreams;
- one initialized `R0` model is cloned to `S0R0` and `S1R0`; one initialized
  `R1` model is cloned to `S0R1` and `S1R1`.

The representation contrast therefore includes only the unavoidable new
context projection and event-input parameterization plus their downstream
finite optimizer path, not unrelated changes to the trunk, heads or hidden
recurrence initialization.

## Frozen optimizer and checkpoint law

Every cell uses exactly 600 logical AdamW steps and the closed r07 law:

```text
theta_0 = initialized parameters; m_0=v_0=0
n=1,...,600; b=n-1
epoch=floor(b/16); batch_index=b mod 16
gradient evaluated at theta_(n-1), one global norm clip at 1.0
bias correction denominators 1-beta1^n and 1-beta2^n
sole checkpoint theta_600.
```

Each logical batch has 256 distinct rows. Each support level has its own fresh
4,096-row permutation per epoch; the two representation levels at that support
level use the same permutation. Learning rate `3e-4`, betas `(0.9,0.999)`,
epsilon `1e-8`, weight decay `1e-5`, constant schedule and every other r07
optimizer condition remain unchanged. There is no early stopping, checkpoint
sweep, second budget, representation search or post-result continuation.

The exact panel contains 40 final checkpoints and 24,000 logical AdamW steps.
Under the unchanged direct-loss/example accounting it contains 224,604,160
model-example evaluations. These are prospective scientific counts, not an
activity authorization or wall-time estimate.

## Untouched evaluation and cell competence

For every seed, draw one fresh 1,024-row untouched `K_fit={4,10}` support panel
under the current independent product-coordinate law and current balanced
word/action law. It is disjoint from both `S0` and `S1` training panels and is
shared by all four cells. Draw fresh target-diagnostic base rows at each
`k in {6,8,12}` exactly as r07: 256 base states, both orientations and all 81
actions, shared by all cells and disjoint from every training/support row.

For cell `ab` and seed `s`, define the unchanged fit-support ratio

```text
rho_ab,s = E_model_ab,s(fit_support) / E_mean_ab,s(fit_support),
```

where `E_mean` uses that support level's checkpoint-fit complete-word output
mean exactly as r07. Every denominator must be finite and positive. The
per-seed competence ceiling remains exactly

```text
rho_ab,s <= 0.65 for all s=0,...,9.
```

For each cell separately also retain the complete r07 target-ratio gate, all
270 seed-by-target-duration-by-coordinate variance-ratio gates and all 30
seed-by-target-duration action-sensitivity gates. Define

```text
CELL_COMPETENT_ab =
  all ten fit-support ratios pass
  AND the cell target-ratio mean and upper-bound gates pass
  AND every coordinate-variance gate passes
  AND every action-sensitivity gate passes.
```

The complete result reports the four-cell competence vector. It may name which
checkpoint packages are prospectively competent, but that vector does not
select an order treatment, authorize a later relation assay or open Stage B.

## Paired factorial estimands

Lower `rho` is better. Within each seed define:

```text
S_s = 0.5 * [(rho_00,s-rho_10,s) + (rho_01,s-rho_11,s)]
R_s = 0.5 * [(rho_00,s-rho_01,s) + (rho_10,s-rho_11,s)]
I_s = (rho_01,s-rho_11,s) - (rho_00,s-rho_10,s).
```

`S_s>0` favors support stratification, `R_s>0` favors the context-conditioned
representation, and `I_s>0` means the support benefit is larger under `R1`
than under `R0`. Negative values mean the opposite direction.

For each of `S,R,I`, compute the across-seed mean and one two-sided Student-t
confidence interval using the ten paired seed values and `df=9`. The three
intervals form one simultaneous family with Bonferroni family error `0.05`:
each interval has coverage `1-0.05/3`, using critical quantile
`t_(1-0.05/(2*3),9)`. Exact paired sign-randomization results accompany but do
not replace these intervals.

Freeze one practical factor margin

```text
delta = 0.01 error-ratio units.
```

For factor `X in {S,R,I}`:

```text
X_POS   := lower_X > +delta
X_NEG   := upper_X < -delta
X_SMALL := lower_X > -delta AND upper_X < +delta
X_ACTIVE := X_POS OR X_NEG.
```

`X_SMALL` is only bounded practical smallness of this exact paired factor
contrast; it is not a universal null or family equivalence claim. An interval
that is neither active nor small is unresolved.

## Result-blind simultaneous precedence

The complete 40-checkpoint panel is atomic. No seed, cell, checkpoint,
evaluation block or effect may be inspected or interpreted before all four
cells for all ten seeds and every registered competence/effect family exist.
After technical acceptance, apply exactly this first-true law:

1. **FACTORIAL-MEASUREMENT-NONIDENTIFICATION** if the atomic panel is
   incomplete, any `rho` denominator is nonfinite/nonpositive, any registered
   ratio/effect is nonfinite, or the shared evaluation identity is violated.
   No factor or cell-competence claim follows.
2. **INTERACTION-EFFECT** if `I_ACTIVE`. Report its sign. Main effects may be
   reported only as conditional diagnostics because a material interaction
   controls.
3. **ADDITIVE-SUPPORT-AND-REPRESENTATION-EFFECTS** if `I_SMALL` and both
   `S_ACTIVE` and `R_ACTIVE`. Report each sign; do not claim unique mechanism.
4. **SUPPORT-EFFECT** if `I_SMALL`, `S_ACTIVE` and `R_SMALL`. Report the sign
   of the isolated support-allocation package effect.
5. **REPRESENTATION-EFFECT** if `I_SMALL`, `R_ACTIVE` and `S_SMALL`. Report the
   sign of the isolated context-representation package effect.
6. **NO-USEFUL-FACTOR-EFFECT** if `S_SMALL`, `R_SMALL` and `I_SMALL`. This
   excludes only effects outside `[-0.01,+0.01]` for the exact factorial and
   fixed budget; it is not a zero-effect or family-deletion conclusion.
7. **MIXED-FACTOR-EVIDENCE** if at least one factor is active but the preceding
   isolation patterns do not hold. Report every active sign and every
   unresolved factor without selecting a single cause.
8. **FACTORIAL-EFFECT-INDETERMINATE** otherwise. The complete four-cell panel
   validly measured checkpoint competence as stated by its attached competence
   vector, but the simultaneous intervals did not establish an active or
   bounded-small registered factorial pattern. This branch does not imply that
   no cell is competent or that the original checkpoint problem necessarily
   persists. No threshold, seed, allocation, representation or budget change
   follows automatically.

On `FACTORIAL-MEASUREMENT-NONIDENTIFICATION`, attach only:

```text
COMPETENCE-VECTOR-UNAVAILABLE.
```

No cell may be called competent or incompetent and no partial competence
vector may be reported on that branch. On every other branch, valid complete
measurement exists and exactly one orthogonal cell modifier is attached:

```text
NO-COMPETENT-CELL
ONE-COMPETENT-CELL:<cell>
MULTIPLE-COMPETENT-CELLS:<ordered list>
ALL-CELLS-COMPETENT.
```

Those four modifiers report the frozen cell-competence vector only.
`COMPETENCE-VECTOR-UNAVAILABLE` reports measurement unavailability, not a
competence failure. No branch or modifier selects `ORDER-TR`, `ORDER-Q`, any
correct/reversed path, a Stage-B arm, another budget, a second surface or UAV
work. Any later order-value object requires a new Portfolio decision, a new
meaning-complete EM definition and same-conversation Pro closure.

## Fresh identity and coordinate law

Immediately before a later separately authorized scientific activity, sample
one fresh 256-bit master `M` from the operating-system cryptographic RNG under
the same create-only collision-rejection rule as r07. Derive ten keys using

```text
HMAC-SHA256(M, UTF8("SCDMP-TBOV-SRF-CHECKPOINT-r02/seed/") || uint32_be(s)).
```

Use the r07 HMAC block, `U53`, unbiased-integer and Fisher-Yates laws with new,
disjoint domain labels:

```text
train/S0/state, train/S0/word_cells, train/S0/action,
train/S1/state_lhs/<coordinate>, train/S1/jitter/<coordinate>,
train/S1/word_action, eval/fit_support/state,
eval/fit_support/word_cells, eval/fit_support/action,
eval/target_k6/state, eval/target_k6/cells,
eval/target_k8/state, eval/target_k8/cells,
eval/target_k12/state, eval/target_k12/cells,
init/shared, init/R0_input, init/R1_context, init/R1_input,
minibatch/S0, minibatch/S1.
```

All panels, manifests and cell packets are create-only and blinded until the
complete atomic result. The master, seed keys, raw coordinates, checkpoints
and partial effects remain sealed. No r07 namespace, master, key, coordinate,
row, checkpoint or optimizer state is imported.

## Strongest alternatives and claim ceiling

Even a clean factor branch estimates a finite-package effect. Support
stratification changes joint roster regularity and its fitted scales; it does
not uniquely identify continuous coverage as the cause. `R1` changes input
parameterization, parameter count, initialization distribution for new
matrices, curvature, clipping and AdamW history; it does not uniquely identify
state-conditioned recurrence as the cause. A material interaction is a package
interaction, not a biological or algebraic mechanism.

The maximum possible positive claim is:

> On this exact fixed-four-carrier direct checkpoint task, under ten fresh
> paired seeds, 600 AdamW steps, the frozen `0.65` untouched-fit-support rule
> and simultaneous three-effect family, the prospectively specified training-
> support allocation, context-conditioned segment representation, or their
> interaction materially changed the direct checkpoint error ratio, with the
> reported four-cell competence vector.

No outcome establishes correct relation direction, semigroup or reward-cocycle
value, policy value, held-out/switch-`k` return or failure robustness,
arbitrary `k`, variable `N`, unique mediation, second-surface, UAV, safety or
deployment value.

## Activity and authority boundary

Scientific activity begins immediately before the first new master candidate,
seed identity, stochastic row, coordinate, scale atom or parameter is
materialized, whichever occurs first. From that moment every factor, row law,
representation, initialization, seed, threshold, confidence family, branch and
claim boundary is immutable.

The current definition stage authorizes only science-card authoring,
independent same-direction ChatGPT Pro mathematical/causal closure, independent
Gemini advisory intake, and later paired-CM read-only static
bindability/observability/comparator/cost assessment. It authorizes no source,
build, test, probe, fixture, identity, coordinate, checkpoint, training,
evaluation, lease, compute, order treatment, Stage B, second surface or UAV
action.
