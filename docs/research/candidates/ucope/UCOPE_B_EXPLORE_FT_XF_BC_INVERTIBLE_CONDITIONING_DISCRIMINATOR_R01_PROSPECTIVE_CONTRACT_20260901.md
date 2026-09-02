# UCOPE FT-XF-BC invertible-conditioning discriminator R01 — prospective science and implementation contract

## Pro-final selection and present boundary

The complete persistent `em:ucope:convergence` response for request
`ucope-em-convergence-20260901-03` is final for this direction-science node:

```text
FINAL_DIRECTION_DECISION=CONTINUE
DECISION_AUTHORITY=PRO_FINAL
DECISION_FORMED=true
BLOCKER=NONE

NEXT_DISCRIMINATOR_COUNT=1
NEXT_OBJECT_ID=UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01
NEXT_EVIDENCE_CLASS=B/EXPLORE
SINGLE_CHANGED_AXIS=BELLMAN_COMPLETE_COORDINATE_CONDITIONING_RAW_VS_INVERTIBLY_WHITENED
PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED
COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE
```

The canonical response is archived at
`temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-convergence-20260901-03/RESPONSE.md`,
SHA-256
`465b4db967dfa3eb36bce4fb8f6ff4591001219418df47277e6204ec4aebf0ba`.

This document freezes the selected science and the meaning-complete CM implementation contract.
It does not launch a result, grant a result slot, change Portfolio lifecycle or priority, open paid
acquisition, or open COUNT/RAW.

```text
OBJECT_ID=UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01
EVIDENCE_CLASS=B/EXPLORE
SCIENTIFIC_SELECTION=YES
PROSPECTIVE_CONTRACT=FROZEN
RESULT_EXECUTION_AUTHORITY=NO
UNCHANGED_B1_REPEAT=false
AUDIT_RERUN=false
AUTOMATIC_BUDGET_ENLARGEMENT=false
```

## Smallest proposition, prediction, and ceiling

Question:

> On fresh paired data from the same finite eight-context host, with the
> target-frozen cross-fitted Bellman-complete function span, FP32 AdamW optimizer,
> data volume, update exposure, folds, information, initialization in score space,
> and evaluator held fixed, does a prospectively defined target-blind invertible
> whitening of the tail and root design coordinates establish competence where
> the raw coordinates do not?

The mechanism hypothesis is deliberately narrow. Raw coordinate scale and correlation may make
finite-step AdamW with gradient clipping fail to reach a useful member of the already available
five-term tail and seven-term root score spans. A target-blind invertible change of coordinates
preserves information, parameter count, and representable functions while changing optimizer
geometry. The differentiating prediction is final even-support competence in the whitened arm but
not the raw arm, accompanied by a stable paired advantage at root updates 160 and 320.

The causal path under test is:

```text
fresh host episodes
-> seed/fold-owned training feature rows
-> RAW or fixed invertibly whitened BC coordinates
-> matched finite FP32 AdamW and clipping exposure
-> tail score function
-> one target-frozen root-target materialization per fold policy
-> root score function
-> odd/even native action and return diagnostics
-> final even-support competence
```

The strongest same-information null is `FT-XF-BC-RAW`. The treatment is
`FT-XF-BC-WHITENED`. Both contain exactly twelve trainable coefficients and exactly the same score
functions in real arithmetic. The strongest live alternatives are target/objective misspecification,
insufficient function span, fold coupling, stochastic seed instability, common root/tail regression
difficulty, another optimizer dynamic, and an additional odd-to-even extrapolation cost.

The maximum claim is one preliminary two-package B/EXPLORE observation on one fresh three-seed,
two-fold finite eight-context host: whether this exact target-blind invertible reparameterization of
the same Bellman-complete span changes competence under the fixed FP32 AdamW exposure. A positive
does not establish pure conditioning or optimizer causality. A negative rejects only the
sufficiency of this intervention at this exposure.

This object cannot establish stable learner superiority or equivalence, a seed-superpopulation
effect, generic paid-information or UCOPE value, COUNT-versus-RAW polarity, variable-`k`,
variable-`N`, MARL or UAV efficacy, transfer, safety, deployment, flight, energy, or real-world
QoS.

## Arms and single changed axis

The object contains exactly two arms:

```text
CONTROL=FT-XF-BC-RAW
TREATMENT=FT-XF-BC-WHITENED
CHANGED_AXIS=BELLMAN_COMPLETE_COORDINATE_CONDITIONING
```

There is no FLEX arm, moving-target arm, factorial arm, ridge arm, truncated-whitening arm,
component-selected arm, larger-budget arm, or best-checkpoint arm.

Both arms use exactly the same Bellman-complete bases, in this exact coordinate order:

```text
z_T = (1, b, k/9, b*k/9, (k/9)^2)

z_R = (1,
       (1-a)*k/9,
       (1-a)*(k/9)^2,
       a,
       a*C,
       a*L,
       a*L*p)
```

Here `a=1` denotes root PROBE, `a=0` denotes root IMMEDIATE, `k=0` for root PROBE and otherwise is
the candidate period, `b=1/2` at root and is the posterior SHORT belief after the six displayed
marks at tail, `C` is total probe cost, `L` is the linkage indicator, and `p` is mark reliability.
The raw arm scores `Q_T=beta_T^T z_T` and `Q_R=beta_R^T z_R`. Neither arm has a residual network,
extra learned scale, bias outside the listed constant term, adaptive normalization, or learned
preconditioner.

### Exact target-blind transform

For every fresh `seed_id`, `fold_id in {0,1}`, and `stage in {tail,root}`, form one ordered training
feature design matrix `X` from the rows actually available to that fold policy before reading any
training target, held-out evaluation, oracle action, competence value, B1 checkpoint, or audit
metric.

- Tail `X` contains the five-term `z_T` row for every PROBE episode in complementary fold
  `1-fold_id`, ordered by `(episode_index, context_id)`; `n_tail=10,240`.
- Root `X` contains the seven-term `z_R` row for every episode in fold `fold_id`, ordered by
  `(episode_index, context_id)`; `n_root=20,480`.
- The matrix row inventory and ordering are identical between arms. The treatment may not insert,
  remove, weight, deduplicate, shuffle, or resample a row.

For each such matrix, define exactly:

```text
G = (X^T X) / n
G = L L^T
z_w = L^-1 z
```

`L` is the deterministic lower-triangular Cholesky factor with strictly positive diagonal. The
treatment must use that fixed stage/seed/fold `L` for every training row and every later candidate
score, including odd- and even-support evaluation. It must never recompute a transform from an
evaluation inventory.

No ridge, jitter, diagonal loading, truncation, pseudo-inverse, eigenspace selection, component
drop, target-dependent scaling, outcome-conditioned regularization, or post-result repair is
permitted. If any `G` is not positive definite, the object stops before constructing an optimizer
with:

```text
STOP_G_NON_PD_NONDISCRIMINATING_OBJECT
```

That is a nondiscriminating-transform observation, not evidence for or against learner competence,
and no locally repaired transform may inherit this object ID.

The implementation must bind the ordered `X`, `G`, and `L` for all twelve stage/seed/fold cells;
record their shapes, deterministic bytes or canonical values, SHA-256 digests, Cholesky success,
positive diagonals, and reconstruction residuals; and demonstrate that none depends on a target,
reward, oracle, even-`K` outcome, historical checkpoint, or competence field. The numerical
construction must be fixed once by CM before result execution and recorded with its software,
precision, accumulation-order, solve, and serialization semantics. A numerical implementation that
cannot realize the equations and positive-diagonal convention is an implementation blocker, not
authority to change them.

### Function-space initialization parity

For each stage/seed/fold, generate one raw BC coefficient initialization `beta_0` from the same
deterministic BC initialization law and new seed/fold ancestry used for the control. The treatment
does not draw another initialization. It uses exactly:

```text
beta_tilde_0 = L^T beta_0
```

so that

```text
beta_tilde_0^T (L^-1 z) = beta_0^T z
```

for the complete initial training and candidate-score inventory. Initial score-space parity is a
required conformance fact. Both optimizers begin with zero first- and second-moment state and the
same step count. A different random draw, zeroing only one arm, a tolerance-based selection of a
favorable transform, or a warmed optimizer is forbidden. FP32 realization details and the maximum
initial score discrepancy must be reported; failure of the frozen parity check is a technical
non-result and cannot be waived after outcomes are available.

## Fixed host, population, information, and folds

The host remains exactly:

```text
link        in {LINKED, SEVERED}
reliability in {13/20, 17/20}
probe cost  in {9/100, 7/50}
K_train     = {1,3,5,7,9}
K_eval      = {2,4,6,8}
marks       = 6
horizon     = 12
```

Both arms receive only the same BELIEF-level information and the same action, reward, service,
time, and energy accounting law. RAW mark sequences and COUNT inputs are absent. Before training,
the host must reproduce from public equations, without reading an old result, that direct probe
contribution is negative in all eight contexts, exactly
`LINKED x 17/20 x 9/100` has positive oracle net acquisition value, the other seven contexts favor
IMMEDIATE, and all applicable odd- and even-support oracle choices are unique. A failure is a
nondiscriminating-host stop, not learner polarity.

Use exactly these three fresh identifiers, disjoint from B1 and every consumed UCOPE namespace:

```text
ucope-bc-conditioning-r01-fresh-00
ucope-bc-conditioning-r01-fresh-01
ucope-bc-conditioning-r01-fresh-02
```

For every seed and each of the eight contexts, generate exactly `5,120` new environment episodes.
The unique scientific population is therefore `122,880` episodes and `614,400` transitions. Both
arms reuse the same generated population read-only; duplicating it under arm-specific RNG streams
is forbidden.

The arm-independent schedule repeats ten-episode blocks containing exactly one episode for every
training stratum:

```text
PROBE x each k in K_train
IMMEDIATE x each k in K_train
```

Each context has exactly `512` episodes per stratum. The observational group is
`(run_id, seed_id, episode_index)`. The eight context episodes in a group share their designated
paired RNG ancestry and remain together in one fold:

```text
fold_id = floor(episode_index / 10) mod 2
```

Each context/fold has `256` groups per action-period stratum. Data generation, context ordering,
fold ownership, posterior construction, example inventories, cyclic batch order, and evaluation
episode roots are paired exactly across arms. Arm identity may change only the basis coordinates
seen by its scorer. Every RNG root and descendant label must be published; no global RNG state,
seed replacement, seed filtering, fold filtering, or result-dependent replay is permitted.

## Credit construction, optimizer, and work exposure

Both arms are target-frozen and group-cross-fitted. For root fold `f`, train the tail scorer only on
PROBE rows from complementary fold `1-f`. Tail targets are the same realized tail returns. Finish
all tail updates, freeze that arm's tail scorer, and materialize all root targets exactly once
before any root optimization:

```text
y_PROBE = realized_probe_primitive
          + max_{k in K_train} Q_tail_frozen(b,k)

y_IMMEDIATE = realized_tail_return
```

The construction law, materialization clock, row order, and candidate inventory are identical.
The numerical root targets may differ as a downstream consequence of the conditioning intervention's
tail learning; that is inside the frozen causal path and must be reported, not artificially forced
equal.

For every arm/seed/fold policy, freeze:

```text
precision                    FP32 model, prediction, loss, gradient, and AdamW state
loss                         squared regression
optimizer                    AdamW
learning rate                3e-4
betas                        (0.9, 0.999)
epsilon                      1e-8
weight decay                 0
gradient clipping            per scorer, global norm 1
batch size                   256
tail optimizer updates       160
root optimizer updates       320
root checkpoints             40, 80, 160, 320
model/checkpoint selection   none
early stopping               none
```

Across the complete two-arm object this is exactly twelve final fold policies, 48 checkpoints,
`1,920` tail updates, `3,840` root updates, `491,520` tail-example exposures, and `983,040`
root-example exposures. There are exactly twelve root-target materialization events, covering
`245,760` arm-specific root rows in total. The treatment receives no additional row, update,
example, target refresh, checkpoint, or evaluation.

All losses, pre-clip gradient norms, clip events, parameters, optimizer states, and checkpoint
payloads must remain finite FP32. A nonfinite event, missing update, mismatched exposure, missing
checkpoint, wrong precision, unequal data/batch ancestry, or telemetry gap is an incomplete
attempt with no scientific observation. It is not a negative result and does not consume this
adaptive B object.

## Evaluation, competence, and stable separation

Every checkpoint is evaluated without selection on both:

- odd training-period support `K_odd={1,3,5,7,9}`; and
- even held-out support `K_even={2,4,6,8}`.

The evaluator must independently regenerate the exact oracles from public host equations. It may
not read B1 or audit runtime rows. For every checkpoint and support, publish all root and tail
candidate scores, finite and unique flags, the eight-context binary root vector, exact root-vector
Hamming distance, maximum exact expected regret, and minimum probability-weighted forced-PROBE
tail agreement. Exact rational host values control thresholds; decimal renderings are descriptive.
The same deterministic candidate order and tie semantics apply to both arms.

Retain the B1 sampled diagnostic unchanged: 64 fresh paired evaluation episodes per context,
fold, seed, arm, and checkpoint, with shared evaluation roots across arms. Sampled returns and
probe rates are descriptive and cannot replace an exact competence or separation predicate.

For a final even-support fold policy `P`:

```text
C_even(P) =
    all_scores_finite
AND all_choices_unique
AND exact_eight_context_oracle_root_vector
AND maximum_expected_regret <= 1/50
AND minimum_forced_PROBE_tail_agreement >= 19/20
```

A seed passes an arm only if both final fold policies pass. An arm is `B_COMPETENT` only if at
least two of its three fresh seeds pass both folds. Update 320 alone controls competence.

Odd-support competence uses the same policy and seed thresholds and is a mechanism diagnostic
only. It cannot substitute for the even-support gate. Preserve the prior near-competence routing
definition:

```text
odd_near_policy =
    all_scores_finite
AND all_choices_unique
AND root_hamming <= 1
AND maximum_expected_regret <= 1/25
AND minimum_forced_PROBE_tail_agreement >= 9/10
```

An odd-near seed requires both final folds. No threshold is relaxed, tuned, or chosen after the
run.

For each matched seed/fold checkpoint, define the metric triple

```text
M = (root_hamming, maximum_expected_regret, minimum_tail_agreement)
```

`WHITENED` materially dominates `RAW` only when it is nonworse on all three dimensions and is
better by at least one root context, `1/50` regret, or `1/20` tail agreement. At a checkpoint,
`WHITENED` has a clear paired advantage only when it materially dominates in at least four of six
matched seed/fold pairs and `RAW` dominates in at most one. A stable clear paired advantage requires
that same whitened-over-raw direction at both updates 160 and 320. Update 40 and 80 remain visible
descriptive curve points; no checkpoint is selected.

## Frozen observations and result interpretation

A conditioning-positive observation requires every predicate below:

```text
FT-XF-BC-WHITENED is B_COMPETENT
FT-XF-BC-RAW is not B_COMPETENT
WHITENED has clear paired advantage at update 160
WHITENED has clear paired advantage at update 320
```

Even this branch supports only a preliminary conditioning-package signal on this finite setup. It
does not prove pure optimizer causality, because whitening interacts with AdamW, clipping, finite
precision, and the arm-specific frozen tail consequence used in root targets.

The exact falsifier is:

```text
FALSIFIER=
FT-XF-BC-WHITENED_IS_NOT_B_COMPETENT
AND
NO_CLEAR_PAIRED_ADVANTAGE_IS_PRESENT_AT_BOTH_UPDATES_160_AND_320
```

That rejects only the proposition that this target-blind invertible conditioning intervention is
sufficient to produce competence at the unchanged exposure. It does not show that every optimizer,
representation, objective, or learner family fails.

The contrary observation identified by Pro for a later PARK decision is:

```text
BOTH_ARMS_NONCOMPETENT_IN_ALL_THREE_SEEDS
AND NEITHER_ARM_HAS_AN_ODD_COMPETENT_OR_ODD_NEAR_SEED
AND WHITENED_HAS_NO_CLEAR_PAIRED_ADVANTAGE_AT_BOTH_160_AND_320
```

An odd-competent or odd-near but even-noncompetent whitened result instead supplies a potential
generalization-recast signal. Raw competence, competence in both arms, competence asymmetry without
stable curve separation, or stable subcompetence separation is reported without local rescue or
invented routing.

Every valid complete branch returns to the persistent `em:ucope:convergence` node before a new
direction conclusion, PARK, RECAST, successor, acquisition action, or COUNT/RAW action. This
contract does not pre-authorize any of those effects.

## Zero-effect and historical-artifact firewall

The result implementation must make all of these counts exactly zero:

```text
old B1 result/checkpoint/control/journal reads       0
old odd-support audit artifact/control reads         0
consumed BELIEF tape/checkpoint/result reads          0
structural fit/certificate/policy reads               0
historical R03 runtime reads                          0
acquisition evaluation                                0
COUNT/RAW data, model, evaluation, or unlock           0
checkpoint selection                                  0
budget adaptation                                     0
network or provider effects                           0
```

The corresponding decision literals remain:

```text
UNCHANGED_B1_REPEAT=false
AUDIT_RERUN=false
AUDIT_RETRY=false
ADDITIONAL_B1_OR_AUDIT_SCORE_READ=false
OLD_B1_ATTEMPT_ACCESS=false
CHECKPOINT_SELECTION=false
AUTOMATIC_BUDGET_ENLARGEMENT=false
ACQUISITION_EVALUATION=false
COUNT_RAW_WORK=false
PORTFOLIO_PRIORITY_OR_CAPACITY_EFFECT=false
```

In particular, no path under the old B1 or audit runtime families may be accepted as a CLI input,
discovered by glob, imported as data, traversed for calibration, or copied into the new runtime:

```text
temp/directions/ucope/exp/ucope-scout-r01-b1-*/
temp/directions/ucope/recon/ucope-scout-r01-b1-*/
```

The implementation may reuse public host equations, action semantics, BELIEF posterior
construction, context definitions, evaluator definitions, and source modules whose import graph is
demonstrated not to read historical runtime. It may not use old data, tensors, learned coefficients,
checkpoints, scores, outcomes, resource ledgers, failed identities, or audit values for
initialization, targets, tuning, selection, performance calibration, or causal controls.

The new scientific runtime may write only inside its own create-once control, scratch, and result
roots. It must not mutate repository sources, another direction, an old UCOPE root, or an external
system. Incomplete private staging is quarantined outside `complete/`; it must never be interpreted,
resumed after outcome inspection, or silently promoted.

## CM conformance, performance, and readiness evidence

Before any result-bearing invocation, CM must return implementation evidence showing:

1. exact arm inventory, five/seven basis order, twelve-parameter count, and absence of residual or
   extra trainable state;
2. deterministic ordered `X`, `G`, positive-diagonal `L`, inverse-coordinate scoring, and
   `beta_tilde_0=L^T beta_0` for both stages;
3. a deliberate non-positive-definite fixture that stops without ridge, truncation, optimizer
   construction, or result publication;
4. target-blindness tests using sentinel targets/oracles and a static/import firewall against every
   old runtime family;
5. exact score-space initialization parity, zero AdamW state parity, paired data/fold/batch/RNG
   ancestry, and transformed evaluation scoring;
6. target-frozen tail-first/root-materialization clocks, exact update/exposure/checkpoint counts,
   and no checkpoint selection;
7. independently recomputed odd/even evaluator, competence, near, material dominance, stable
   separation, falsifier, and branch predicates;
8. create-once manifest/checkpoint/result binding, full activity and resource telemetry,
   complete-only publication, and incomplete-attempt quarantine; and
9. real environment, learner, trainer, checkpoint, and evaluator calls with nonzero transitions,
   updates, and evaluations in the result path.

CM must also produce outcome-blind A/RECON performance evidence for the exact implementation. It
may use a separately named technical population and reduced work solely to measure and project
wall/CPU time, process-tree RSS, processes, threads, workers, scratch, durable bytes, aggregate I/O,
and publication headroom. It must publish no loss, coefficient, policy, checkpoint, oracle vector,
regret, agreement, competence, separation, acquisition, score, root vector, branch, or other
scientific outcome, and it may not use any of the three scientific seed identifiers or any
historical runtime.

### Retained assessment-01 and assessment-02 evidence

The create-once artifact
`temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-01.json`,
SHA-256
`1dea9ee1762c1198b4cb71a10ac2450b8a6eadfd28edf3251f30151ffd9fb452`, is retained unchanged as
valid engineering evidence with disposition `REPAIR_REQUIRED`. It measured:

```text
wall_seconds                    3.7865412999999535
process_tree_peak_rss_bytes     255455232
process_count_peak              1
child_process_count_peak        0
thread_count_peak               27
scratch_high_water_bytes        63824
durable_high_water_bytes        63824
aggregate_io_bytes              33406115
scientific seeds/results read   0
scientific outcomes published   0
```

Its RSS guard, `ceil(255455232 * 5/4) = 319319040` bytes, fits the frozen ceiling. Its wall
projection does not: it applies the largest total-work ratio `384` and the `5/4` guard to the
entire `3.7865412999999535 s`, producing `1817.5398239999777 s`. That multiplication treats
one-time entry/import work and sixfold snapshot work as if each scaled 384-fold. The disposition is
correct for that assessment schema, but the blanket estimator is not a decision-relevant estimate
of the production command.

The separately registered create-once V2 assessment then ran once after a fresh admission of
`14520963072` physical and effective available bytes. Its immutable artifact is
`temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-02.json`,
SHA-256
`1456280de0bde1be6d8bb73448b5918d3ad5be963a1f1f6d5bf9862c32878a20`.
It contains no scientific seed, outcome, prepare, manifest, result, acquisition, or COUNT/RAW
effect. Its direct engineering measurements remain usable, including `4.30020660000082 s` wall,
`258134016` bytes peak RSS, one process, zero children, and 27 peak threads.

Its self-reported `PERFORMANCE_READY` disposition is not accepted. The guarded numbers
`155.03638762588025 s` wall and `322667520` bytes RSS are mechanically reproducible from its schema,
but its readiness estimand is invalid for two prospective reasons:

1. Each technical learner setup and full reload traversed only `80` tail plus `160` root training
   feature rows, or `240` rows, while the corresponding production policy traverses `10240` plus
   `20480`, or `30720` rows. Multipliers `3` and `6` accounted only for policy and snapshot counts;
   they omitted the 128-fold row ratio inside those timed regions.
2. Assessment tensor construction began before the result path had frozen the same deterministic,
   CPU, one-intra-op-thread and one-inter-op-thread Torch topology. The observed wall/RSS envelope
   therefore did not measure the intended production topology.

```text
ASSESSMENT_02_ARTIFACT=RETAINED_UNCHANGED
ASSESSMENT_02_ENGINEERING_MEASUREMENTS=USABLE_BOUNDED_FACTS
ASSESSMENT_02_READINESS=INVALID_NOT_ADOPTED
ASSESSMENT_02_PREPARE_ELIGIBLE=false
CURRENT_READINESS=REPAIR_REQUIRED
```

### Lawful assessment-03 resource-only repair

A source refactor followed by one new outcome-blind assessment is lawful because no scientific
result or manifest exists and the repair changes only data reuse, read-only rehydration, topology
placement, timers, and resource estimation. It must not change any generated row, tensor value,
coordinate transform, initialization, target, optimizer operation, update, snapshot payload,
evaluator, predicate, or claim. Register exactly:

```text
ASSESSMENT_ID=ucope-bc-conditioning-r01-assessment-03
ASSESSMENT_SCHEMA=UCOPE_BC_CONDITIONING_R01_A_RECON_PERFORMANCE_V3
PROJECTION_LAW=DECOMPOSED_STAGE_SCALING_V2_CONSTANT_SHAPE_SETUP_RELOAD
ASSESSMENT_01_DISPOSITION=RETAINED_REPAIR_REQUIRED
ASSESSMENT_02_READINESS=INVALID_NOT_ADOPTED
SCIENTIFIC_CHANGE=false
RESULT_EXECUTION_AUTHORITY=NO
```

`assessment-03` uses the same one technical seed, two arms, two folds, `40` episodes per context,
two tail updates, four root updates, technical snapshots at root updates 2 and 4, batch size 256,
592 odd/even candidate values per snapshot, and 128 predetermined worst-path technical episodes as
assessment-02. The fixed episodes use PROBE plus a fixed tail-period schedule, discard actions and
returns, and publish counts and resource time only. No learned choice or scientific metric is
computed.

### Identical topology and constant-shape implementation law

Before the first tensor allocation, basis tensor, matrix multiplication, factorization, model,
optimizer, snapshot load, or evaluation call, `assessment-03`, `run`, and `validate` must each
execute the same entry helper and verify:

```text
device                         cpu
torch.use_deterministic_algorithms(True)
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.are_deterministic_algorithms_enabled() == True
torch.get_num_threads() == 1
torch.get_num_interop_threads() == 1
```

No later function may change that topology. The topology receipt contains only these literals,
software versions, and observed process/thread counts; it contains no tensor or outcome. A late,
different, or unverifiable topology is `REPAIR_REQUIRED` and cannot be hidden by projection
headroom.

The production and technical paths must create each ordered root/tail feature matrix exactly once
per seed/fold/stage and reuse it read-only across both arms. Matrix bytes, shapes, row order, and
digests must equal independent regeneration. Training and setup functions may not call the feature
constructor again. Initialization parity is removed from object construction and timed explicitly
over (a) training rows and (b) the fixed odd/even candidate inventory. Learner/optimizer setup then
constructs only fixed-size five- and seven-coefficient scorers, their two AdamW states, and bound
transform records; it receives no population, row set, or row-sized matrix.

Every snapshot transaction must publish a full training-state shard and a fixed-size read-only
evaluation projection under one create-once binding. The full shard retains scorer state, optimizer
state, frozen targets, transforms, identity, progress, and activity. The projection retains only
identity, root/tail scorer state, and the same transform bytes. The writer validates and hashes the
entire full shard and binds the projection digest before either can be evaluated.

Result evaluation may open only the fixed-size projection. Its rehydrator instantiates two
fixed-size scorers and loads their state tensors; it must not open the full shard or accept or
reconstruct a population, training row set, training feature matrix, frozen target vector, or
optimizer object. Full-shard validation, hashing, staging, and publication remain in the separately
row-scaled snapshot timer. On technical fixtures, the full shard and read-only projection must have
byte-identical scorer/transform tensors and produce byte-identical candidate scores. Any mismatch,
projection/full-shard binding failure, or accidental full-shard read by evaluation is an
implementation non-result.

### Exact assessment-03 sanitized stage ledger

The V3 artifact exposes exactly the following mutually exclusive timers. Each row contains only
`wall_seconds`, `cpu_seconds`, `io_read_bytes`, `io_write_bytes`, `scratch_bytes_created`,
`durable_bytes_created`, and its integer work-unit count. No coefficient, prediction, selection,
action, return, metric, tensor, optimizer state, snapshot payload, or outcome enters the artifact.

| Timer key | Assessment-03 work units | Science work units | Frozen multiplier |
| --- | ---: | ---: | ---: |
| `entry_fixed` | one import/binding/topology/monitor envelope | one | `1` |
| `environment_rows` | `320` technical episodes | `122880` episodes | `384` |
| `feature_row_assembly` | `480` ordered feature rows | `184320` rows | `384` |
| `gram_design_binding_rows` | `480` Gram/hash rows | `184320` rows | `384` |
| `cholesky_factorization` | `4` fixed-dimension factors | `12` factors | `3` |
| `learner_optimizer_setup` | `8` fixed-size scorer/optimizer pairs | `24` pairs | `3` |
| `initialization_parity_training_rows` | `960` arm-owned training-row checks | `368640` checks | `384` |
| `initialization_parity_candidate_rows` | `2336` candidate-row checks | `7008` checks | `3` |
| `tail_update_steps` | `8` updates | `1920` updates | `240` |
| `root_target_rows` | `640` materialized rows | `245760` rows | `384` |
| `root_update_steps` | `16` updates | `3840` updates | `240` |
| `snapshot_full_binding_rows` | `1280` frozen-target rows across `8` full shards plus projections | `983040` rows across `48` shards plus projections | `768` |
| `evaluation_projection_reload` | `8` fixed-shape projection rehydrations | `48` rehydrations | `6` |
| `candidate_evaluation` | `4736` candidate values | `28416` values | `6` |
| `sampled_episode_work` | `128` fixed technical episodes | `24576` paired sampled episodes | `192` |
| `sanitized_assembly` | `8` structural records | `48` result records | `6` |

`gram_design_binding_rows` includes ordered-design hashing, `X^T X/n` accumulation, and no
Cholesky work. `cholesky_factorization` begins only from the completed fixed-size Gram matrices.
`learner_optimizer_setup` is invalid if its timer receives a row-sized tensor.
`snapshot_full_binding_rows` includes full-shard serialization, complete validation and hashing,
projection creation/binding, and create-once staging; it must also report the separate `8 -> 48`
snapshot-count check. `evaluation_projection_reload` is invalid if its timer or call graph opens a
full shard or reaches a population, frozen-target, optimizer, or training-row constructor.
`candidate_evaluation` executes production odd/even candidate shapes without ranking, oracle
construction, regret, agreement, competence, or reduction. `sampled_episode_work` remains fixed
technical environment work, not evaluation evidence.

Timers are non-overlapping. Any unclassified measured time is assigned prospectively to
`entry_fixed`, never distributed after observing the projection. Stage CPU and I/O deltas must
reconcile to invocation totals and every work-unit count must match exactly. Missing, overlapping,
negative, nonfinite, row-shape-contaminated, topology-inconsistent, or unreconciled evidence yields
`REPAIR_REQUIRED`.

For each timer row `i`, let `w_i`, `c_i`, `r_i`, `q_i`, `s_i`, and `d_i` be its measured wall, CPU,
read, write, scratch-created, and durable-created values, and let `f_i` be the multiplier above.
Freeze:

```text
central_wall_seconds = sum_i(f_i * w_i)
guarded_wall_seconds = 60 + (5/4) * central_wall_seconds

central_cpu_seconds  = sum_i(f_i * c_i)
guarded_cpu_seconds  = 60 + (5/4) * central_cpu_seconds

read_cap_bytes       = 33554432 + ceil((5/4) * sum_i(f_i * r_i))
write_cap_bytes      = 33554432 + ceil((5/4) * sum_i(f_i * q_i))
aggregate_io_cap     = read_cap_bytes + write_cap_bytes

scratch_cap_bytes    = round_up_MiB(67108864 + ceil((5/4) * sum_i(f_i * s_i)))
durable_cap_bytes    = round_up_MiB(67108864 + ceil((5/4) * sum_i(f_i * d_i)))

rss_cap_bytes        = ceil((5/4) * max(255455232, 258134016, assessment_03_peak_rss_bytes))
thread_cap           = 32
process_cap          = 1
child_process_cap    = 0
```

`round_up_MiB(x)=ceil(x/1048576)*1048576`. The fixed 60-second wall/CPU and 32-MiB-per-direction
I/O terms cover interpreter, atomic-publication, ledger, and final-rename work that is not repeated
with scientific rows. The 64-MiB storage terms cover complete-result serialization and publication
headroom. None is fitted after `assessment-03`.

`assessment-03` is `PERFORMANCE_READY` only when the topology, constant-shape, exact stage, and
sanitization checks pass and:

```text
guarded_wall_seconds       <= 900
rss_cap_bytes              <= 603979776
scratch_cap_bytes          <= 268435456
durable_cap_bytes          <= 268435456
aggregate_io_cap           <= 2147483648
root_process_count         == 1
process_count_peak         == 1
child_process_count_peak   == 0
thread_count_peak          <= 32
worker_count               == 1
```

Otherwise it remains `REPAIR_REQUIRED` with no science. `assessment-01` can never be reclassified,
overwritten, migrated, or used by `prepare-run`; assessment-02 likewise remains immutable and
ineligible. A later manifest may bind only the exact create-once `assessment-03` bytes, their source
aggregate, V3 schema, V2 projection law, frozen topology, and `PERFORMANCE_READY` disposition.

Immediately before every result-bearing attempt, run the central memory admission and require both
physical and effective available memory to be at least `4,294,967,296` bytes. The result manifest
must bind a clean committed source revision, source-byte inventory, exact config, three seeds,
RNG/data ancestry law, arm order, numerical transform implementation, performance assessment,
resource caps, scratch/result paths, and zero-effect firewall. Missing admission, missing readiness,
wrong binding, resource/telemetry failure, or incomplete output is no scientific observation.

## Exact command and effect boundary

CM must implement one CLI surface at:

```text
scripts/run_ucope_bc_conditioning_discriminator_r01.py
```

The registered subcommands have these effects:

| Subcommand | Boundary |
| --- | --- |
| `--help` and source tests | Non-result; no scientific root, data, RNG master, model, optimizer, checkpoint, evaluation, or outcome. |
| `assess-run` | Non-result A/RECON performance only; technical namespace and sanitized resource/activity output; no scientific seeds or metrics. |
| `prepare-run` | Non-result; creates one immutable manifest only after `PERFORMANCE_READY`; creates no scientific state. |
| `run` | The sole result-bearing command; after a fresh central 4 GiB admission it may create the new scientific data, transforms, models, optimizers, checkpoints, evaluations, and complete result. |
| `validate` | Post-result read-only recomputation/inspection of one complete publication; no training, optimizer step, environment episode, checkpoint write, selection, or alternate result. |

The first prospective namespaces are:

```text
control root             = temp/directions/ucope/controls/ucope-bc-conditioning-r01
retained assessment-01  = temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-01.json
retained assessment-02  = temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-02.json
current assessment      = temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-03.json
assessment admission    = temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/assessment-03.json
assessment scratch      = temp/directions/ucope/controls/ucope-bc-conditioning-r01/scratch/assessment-03
manifest                = temp/directions/ucope/controls/ucope-bc-conditioning-r01/manifests/result-01.json
output root             = temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01
```

The exact intended command sequence, once CM has implemented and independently accepted the surface
and Root separately grants result execution, is:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/assessment-03.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_bc_conditioning_discriminator_r01.py assess-run --admission-receipt 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/assessment-03.json' --output 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-03.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_bc_conditioning_discriminator_r01.py prepare-run --assessment 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-03.json' --manifest 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/manifests/result-01.json' --output-root 'temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/result-01.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_bc_conditioning_discriminator_r01.py run --manifest 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/manifests/result-01.json' --admission-receipt 'temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/result-01.json' --output-root 'temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_bc_conditioning_discriminator_r01.py validate --complete-root 'temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01/complete'
```

Only the fifth line is result-bearing. None of these commands is executed or authorized by this
resource-only amendment; the first two lines are the exact updated `assessment-03` command
transaction. The runner must reject alternate arm lists, seed lists, data/update/checkpoint budgets,
transform variants, old-runtime inputs, output-root aliases, overwrite, best-checkpoint selection,
acquisition flags, COUNT/RAW flags, and unbound manifests. A result-attempt failure leaves
`complete/` absent and quarantines the attempt. A fresh replacement requires a new attempt identity
and admission while preserving this scientific contract; any outcome-informed scientific change
is a separately named B object and cannot reuse `result-01`.

## Required complete publication and EM return

A valid complete result must make discoverable:

- source revision and byte inventory; manifest/config/RNG/data bindings;
- exact environment episode/transition, row, update, exposure, target-materialization, checkpoint,
  exact-evaluation, and sampled-evaluation counts;
- all stage/seed/fold ordered-design, `G`, `L`, PD, reconstruction, transform, and initialization
  parity evidence;
- every arm/seed/fold/checkpoint odd/even metric and sampled diagnostic;
- individual learning curves, competence/near summaries, six paired dominance rows per checkpoint,
  stable-separation predicates, positive predicate, falsifier, and contrary-decision predicate;
- parameter count, optimizer/config/checkpoint bindings, gradient/clipping/nonfinite telemetry;
- complete process-tree and filesystem resource ledger; and
- explicit zero old-runtime reads, acquisition evaluations, COUNT/RAW effects, selections, network
  effects, and Portfolio effects.

CM owns direct runtime observation and technical acceptance. EM must verify conformance and
interpret the smallest supported proposition; test success, process exit, or `PERFORMANCE_READY`
does not establish conditioning value. Every valid result retains adverse and outlying rows and is
sent to a fresh `em:ucope:convergence` round before direction-local convergence or lifecycle advice.

## Evidence paths

- `temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-01.json`
- `temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/assessment-01.json`
- `temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-02.json`
- `temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/assessment-02.json`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-convergence-20260901-03/RESPONSE.md`
- `docs/research/candidates/ucope/DIRECTION.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_CONVERGENCE_DECISION_INTAKE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_PROSPECTIVE_CONTRACT_20260901.md`
- `docs/research/candidates/ucope/UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_RESULT_EVIDENCE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_B_EXPLORE_MT_XF_BC_COMPETENCE_FIRST_SCOUT_R01_INNOVATOR_INTAKE_20260901.md`
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
---

## Addendum — section 11 recast, 2026-09-02 (appended; the frozen body above is unchanged)

Authority: owner decisions 2 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4;
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`;
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11, which prevails over this contract
wherever this contract asks more of a `B/EXPLORE` object than §11 does. The §11.6 record of the
demotion, with every condition quoted at its `file:line`, is
`UCOPE_SECTION11_RECAST_INTAKE_20260902.md`.

Nothing in the frozen body above is edited, and no scientific factor of
`UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` changes: the two arms, three
fresh seeds, two group-disjoint folds, 5,120 episodes per context, batch 256, `160`/`320` updates at
lr `3e-4`, checkpoints `{40, 80, 160, 320}`, the target-blind positive-diagonal Cholesky transform
and function-space-matched initialisation, the exact oracles, the `C_even` thresholds, the positive
and falsifier definitions, and the claim ceiling all stand exactly as written above.

**Demoted from launch condition to recorded field** (each is quoted from the body above at the line
the compliance note's Part B section 5 gives):

| # | Body clause | Line | Now |
| --- | --- | --- | --- |
| 1 | "Before any result-bearing invocation, CM must return implementation evidence showing: … 8. create-once manifest/checkpoint/result binding, full activity and resource telemetry, complete-only publication, and incomplete-attempt quarantine" | :462, :478-479 | the binding, complete-only publication and incomplete-attempt quarantine stand; "full … resource telemetry" as a pre-launch condition is recorded, and a missing measurement sets `resources_unmeasured` with reasons (decision 7) |
| 2 | "CM must also produce outcome-blind A/RECON performance evidence for the exact implementation." | :483-484 | recorded field `performance_assessment` with `gating: false` |
| 3 | "A later manifest may bind only the exact create-once `assessment-03` bytes, their source aggregate, V3 schema, V2 projection law, frozen topology, and `PERFORMANCE_READY` disposition." | :705-708 | recorded. `assessment-03` does not exist; `assessment-02.json` does, is `PERFORMANCE_READY` on disk, and is declared `ASSESSMENT_02_READINESS=INVALID_NOT_ADOPTED` at :561. Both facts are recorded; neither gates |
| 4 | "The result manifest must bind a clean committed source revision, source-byte inventory, …" | :711-714 | the revision, inventory, exact config, three seeds, RNG/data-ancestry law, arm order, transform implementation and zero-effect firewall are still bound and validated; only "clean committed" is recorded rather than required |
| 5 | `C_even(P) = … AND exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND minimum_forced_PROBE_tail_agreement >= 19/20`; "Update 320 alone controls competence." | :324-333 | computed unchanged at the same exact thresholds and **reported per run as a recorded observation**. It gates neither the run's completion nor its publication |
| 6 | "A late, different, or unverifiable topology is `REPAIR_REQUIRED`" | :589-592 | the topology is still configured (1 intraop thread, 1 interop thread, deterministic algorithms) and recorded in the manifest and run record; it no longer refuses |
| 7 | the projection resource caps derived from the assessment | :705-708 and the readiness block above them | recorded as `cap_exceedances` beside the observed telemetry, with `gating: false`, because they descend from an assessment this contract itself declares ineligible |

**Still holding this launch, unchanged:** the §4 integrity items; "9. real environment, learner,
trainer, checkpoint, and evaluator calls with nonzero transitions, updates, and evaluations in the
result path" (:480-481); "Immediately before every result-bearing attempt, run the central memory
admission and require both physical and effective available memory to be at least `4,294,967,296`
bytes" (:710-711); "Group-disjoint folds", the odd/even support separation and "It may not read B1
or audit runtime rows" (:305-311); the non-positive-definite `G` stop; one machine-generated
exposure line (§11.4); create-once binding and complete-only publication; and §6.2 quarantine of an
incomplete attempt on a learner-side instrumentation failure.

**Sequencing.** Under decision 2 this object runs **alongside** the named exposure ladder
`UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01`, not instead of it, and the ladder runs first. A
both-arms-noncompetent outcome here is not `PARK` support on its own before the ladder has run.

**Result.** `UCOPE_BC_CONDITIONING_DISCRIMINATOR_R01_RESULT_EVIDENCE_20260902.md`.
