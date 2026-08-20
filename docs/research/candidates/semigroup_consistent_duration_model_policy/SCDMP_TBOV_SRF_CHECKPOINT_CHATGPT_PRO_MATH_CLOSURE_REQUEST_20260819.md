# SCDMP TBOV support-representation factorial checkpoint Pro closure

Continue the existing dedicated ChatGPT Pro conversation for
`direction:semigroup_consistent_duration_model_policy`. The completed r07
Stage-A result converged in this conversation at `MODIFY-CHECKPOINT`. This is a
new prospective definition-only successor, not a rerun or a continuation of
r07 coordinates.

Review only mathematical and causal closure. Do not review code, files, tests,
runtime, hashes, receipts or technical implementation. Do not authorize
construction, coordinates, training, compute, an order treatment, Stage B,
another surface or UAV work.

## Exact successor identity and question

The frozen revision is
`SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-01`. It asks whether direct
checkpoint competence at the unchanged 600-step AdamW budget and unchanged
per-seed `0.65` untouched-fit-support ceiling is materially changed by:

1. current versus support-stratified equal-row training allocation;
2. current token-only versus one context-conditioned segment representation;
3. their interaction.

It is exactly one `2 x 2` factorial across ten fresh paired seeds. It contains
no relation loss or correct/reversed comparison. No outcome may select
`ORDER-TR`, select `ORDER-Q`, or open Stage B.

The deterministic fixed-four-carrier task, legal observations/actions, event
words, fit durations `{4,10}`, target diagnostics `{6,8,12}`, state product
law, direct terminal-state/reward outputs, all-contiguous-segment targets,
standardized direct loss, row/atom weights, precision and r07 one-based AdamW
law are unchanged. No r07 seed, coordinate, row, scale, checkpoint, optimizer
state, assay value or branch fact transfers.

## Four cells and pairing

The cells are:

```text
S0R0 = current allocation x current token-only GRU
S1R0 = support-stratified allocation x current token-only GRU
S0R1 = current allocation x context-conditioned GRU
S1R1 = support-stratified allocation x context-conditioned GRU.
```

There are ten fresh seed blocks, each containing all four cells. At a support
level, both representations receive identical training rows, targets, scalers
and minibatch order. At a representation level, the two support cells clone
the same initialized parameters before their different data are used. All four
cells share one fresh untouched fit-support panel and target-diagnostic panels
within the seed.

## Support factor

`S0` is the exact current 4,096-row law: 16 balanced
`(k,sigma,gamma,orientation)` word cells, an independently balanced global
81-action roster, and independent product-uniform states.

`S1` also has exactly 4,096 equally weighted rows and the same marginal task
law. Each of 16 word cells receives exactly 256 rows. Within each word cell all
81 actions appear three times and 13 seed-permuted actions appear a fourth
time. For each of nine continuous state coordinates independently, one fresh
randomized Latin-hypercube permutation and independent jitter place exactly
one coordinate in each of 4,096 marginal strata. The complete word-action
roster is independently permuted. Every row retains the complete word and all
legal contiguous-segment targets. No evaluation coordinate enters allocation.

Thus `S1` changes coverage allocation only: not row count, task support,
duration set, loss, target information or evaluation law.

## Representation factor

`R0` is the exact r07 token-only, width-32, zero-initial-state unidirectional
GRU followed by the unchanged `q0` trunk and state/reward heads.

For `R1`, form the same legal normalized boundary-state/action/actual-duration
input `q0 in R^14`, then

```text
c=SiLU(W_c q0+b_c) in R^32
v_t=concat(e_t,c) in R^37.
```

A one-layer width-32, zero-initial-state unidirectional GRU applies the exact
r07 gate order to `v_t`; its final hidden state is concatenated with the
unchanged `q0` trunk, and the unchanged heads emit direct terminal state and
reward. A contiguous segment receives its own true start state and actual
length. `R1` has no position input, attention, bidirectionality, oracle,
intermediate true-state feature, physical coefficient, correct/reversed flag
or relation loss.

All matrices use the same Xavier-uniform/float32 law and zero biases. Same-
shaped hidden-recurrent, trunk and head matrices are paired identically across
`R0/R1`; representation-specific input matrices use disjoint substreams. One
`R0` initialization is cloned across support levels, and one `R1`
initialization is cloned across support levels.

This is a finite-package representation factor. It changes context input,
parameter count and optimizer geometry and therefore cannot uniquely identify
state conditioning as a mechanism.

## Optimizer, evaluation and competence

Each of the 40 cell-seed models receives exactly 600 logical AdamW steps:
`theta_0`, zero moments, `n=1,...,600`, zero-based batch `b=n-1`, one global
clip, one-based bias correction and sole checkpoint `theta_600`. Each batch has
256 distinct rows, each support level supplies its own fresh epoch
permutations, and both representations at that support level share the order.
No early stop, sweep, second budget or continuation is legal.

Each seed's 1,024-row untouched fit-support panel is fresh, disjoint and shared
across all four cells. Fresh target diagnostic panels at `k={6,8,12}` are also
shared across cells. For cell `ab` and seed `s`, retain the exact r07 ratio

```text
rho_ab,s=E_model/E_mean,
rho_ab,s<=0.65 for every seed.
```

Every denominator must be finite and positive. For each cell retain the r07
target-ratio mean/upper gate, all 270 coordinate-variance gates and all 30
action-sensitivity gates. `CELL_COMPETENT_ab` requires every one of those
conditions. The four-cell competence vector is only a checkpoint modifier; it
never selects an order treatment.

## Factor estimands and simultaneous inference

Lower `rho` is better. Within seed define:

```text
S_s=0.5[(rho_00-rho_10)+(rho_01-rho_11)]
R_s=0.5[(rho_00-rho_01)+(rho_10-rho_11)]
I_s=(rho_01-rho_11)-(rho_00-rho_10).
```

Positive `S` favors stratification; positive `R` favors the context GRU;
positive `I` means the support benefit is larger under `R1`. For each effect,
compute one paired-seed two-sided Student-t interval with `df=9`. The three
intervals use one Bonferroni family error `0.05`: per-interval coverage
`1-0.05/3` and critical quantile `t_(1-0.05/(2*3),9)`. Exact paired sign-
randomization accompanies but does not replace the intervals.

The single practical margin is `delta=0.01` error-ratio units:

```text
X_POS: lower_X>+delta
X_NEG: upper_X<-delta
X_SMALL: lower_X>-delta and upper_X<+delta
X_ACTIVE: X_POS or X_NEG.
```

## Result-blind first-true map

The 40-checkpoint panel is atomic. No partial cell/seed/effect interpretation
is allowed. After complete technical acceptance:

1. `FACTORIAL-MEASUREMENT-NONIDENTIFICATION` for incomplete identity,
   nonfinite/nonpositive denominator, nonfinite registered outcome or broken
   shared evaluation.
2. `INTERACTION-EFFECT` if `I_ACTIVE`; report sign and keep main effects
   conditional.
3. `ADDITIVE-SUPPORT-AND-REPRESENTATION-EFFECTS` if `I_SMALL` and both main
   effects are active; report both signs.
4. `SUPPORT-EFFECT` if `I_SMALL`, `S_ACTIVE` and `R_SMALL`.
5. `REPRESENTATION-EFFECT` if `I_SMALL`, `R_ACTIVE` and `S_SMALL`.
6. `NO-USEFUL-FACTOR-EFFECT` if all three are small; this is bounded practical
   smallness only for the exact factorial, not universal null/family deletion.
7. `MIXED-FACTOR-EVIDENCE` if at least one factor is active but no preceding
   isolation pattern holds.
8. `CONTINUED-CHECKPOINT-NONIDENTIFICATION` otherwise.

Attach exactly one competence-vector modifier: no competent cell, one named
cell, multiple named cells, or all cells. No branch/modifier opens a relation
assay or Stage B.

## Freshness and claim boundary

One new OS-random 256-bit master derives ten keys under the new
`SCDMP-TBOV-SRF-CHECKPOINT-r01` HMAC namespace. Training support levels,
evaluation panels, two representation initializations and minibatch tapes use
disjoint domains. Identities, coordinates and checkpoints are sealed until the
complete result. Scientific activity begins before the first master candidate,
identity, coordinate, scale atom or parameter is materialized.

The maximum positive claim is only that the prospectively specified support
allocation, context-conditioned segment representation, or their interaction
materially changed the direct checkpoint error ratio at the exact fixed budget,
with the reported four-cell competence vector. No unique mechanism, relation-
direction, semigroup, task-value, held-out/switch-`k` benefit, arbitrary `k`,
variable `N`, second-surface, UAV, safety or deployment claim is available.

## Required disposition

Return exactly one leading line:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

Then audit:

1. whether the support and representation factors are single-valued and the
   factorial contrasts have the claimed direction;
2. whether initialization/data/evaluation pairing identifies the intended
   finite-package effects without illegal evidence transfer;
3. whether the simultaneous confidence family, `delta` predicates and
   precedence are complete, reachable and noncontradictory;
4. whether cell competence can remain an orthogonal modifier without opening
   order work;
5. the strongest alternative and exact claim ceiling; and
6. every exact mathematical or causal defect if revision is required.

Do not propose threshold relaxation, seed replacement, coordinate reuse,
budget search, source work, construction, activity, Stage B or a portfolio
decision.

