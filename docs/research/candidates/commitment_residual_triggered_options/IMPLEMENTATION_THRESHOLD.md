# CRTO common-history gate implementation threshold

Status: `IMPLEMENTED_SCIENTIFIC_FREEZE_INCOMPLETE`

Object: `CRTO-COMMON-HISTORY-GATE-20260830-01`. This is a fresh prospective object, never an
update-1,000 continuation. It must load no B1 probe, optimizer, checkpoint, cursor, result, or
artifact. The isolated implementation and focused tests are technically accepted. The automatic
wave-2 source audit below freezes the recoverable predictor, behavior/continuation, calibration,
evaluation-population, audit, and support laws, and records the source-defined Student-t calculation
without treating its sampling-model coverage as established. A result-bearing run is still
scientifically undefined. The primary blocker is that `RAW_LONG_COMPETENCE` has no authorized
reference, aggregation rule, or numerical margin. A second unresolved validity issue is that eight
counter-addressed replicates do not by themselves justify iid-Normal Student-t coverage, and no
distribution-free familywise alternative with an adequate power/width bound is frozen. The current
fail-closed `run` entry remains correct and must not be bypassed.

## Frozen 3 × 2 comparison

All cells use identical gates: `GRU(42,64)` over complete deployable history, a `52→64→32` tanh
packet adapter, and a `96→64→8` tanh action-value head. Output order is KEEP followed by seven
printed options; illegal actions are masked.

| Representation | Packet | SHORT | LONG |
| --- | --- | ---: | ---: |
| `RAW` | `[Y, mu, vech(L)]` | 128 Adam updates | unchanged continuation to 2,048 total |
| `TRUE_RESIDUAL` | aligned clipped/quantile/adverse residual packet padded to 52 | 128 | 2,048 |
| `CALIBRATED_DERANGEMENT` | another row's intact aligned residual packet | 128 | 2,048 |

`e=L^{-1}(Y-mu)`. “True” means aligned to its own realized history, not oracle prediction.
Derangement is a fixed-point-free bijection within split, regime, elapsed horizon, and cost; it
preserves the exact packet multiset while breaking history alignment.

Freeze batch 64, Adam `1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay, global gradient
clip `1.0`, legal-state masked MSE to exact `G16`, and one canonical nonreshuffled permutation.
Initialization bytes, optimizer law, row order, processed examples, and logical work are identical.
SHORT is not inspected before all paths reach LONG.

## Population, RNG, histories, and clocks

Use eight fresh replicates and counter-addressed RNG namespace `2026083001`, with disjoint purposes
for panel/tape, predictor initialization/order, gate initialization/order, and derangement. Ambient
RNG is forbidden.

Per replicate: fit a fresh predictor from genesis on 256 balanced K4/K8 episodes; train gates on 512
balanced fixed-K8 episodes; evaluate on fresh fixed-K8, fixed-K16, `4→16`, and `16→4` panels. The
arm-independent behavior uses pre-materialized tapes and no learned arm acts during history
collection.

A row is the first agent at the first legal discretionary review with a different legal replacement,
continuous commitment, predictor horizon in `{4,8,12,16}`, valid event window, protected switch
boundary, and at least 16 primitive steps remaining. The 42-vector history runs from reset through
predecision observation.

Keep primitive time, four-step review opportunity, option age/external K, predictor-anchor elapsed
horizon, 16-step credit, optimizer update, and processed-state exposure as distinct clocks.

## Source-grounded partial freeze — automatic wave 2

The following laws are selected from the accepted B1 predictor/calibration/audit sources, the
fresh-object threshold above, and the isolated scaffold at source commit `1bea5cc9`. This is
direction-level scientific authority for a possible completed successor; it is not a claim that the
present provisional code conforms end to end. No implementation or result activity may begin until
the primary competence blocker and the separate inference-validity issue below are resolved
prospectively.

### Predictor

Each replicate fits one fresh predictor from genesis on 256 preassigned balanced fixed-K4/K8
episodes. Eligible examples obey the one continuous-commitment law at elapsed predictor horizons
`{4,8,12,16}`; a target observed immediately before a same-boundary re-anchor remains with the old
commitment, and a missing horizon is never borrowed from a successor commitment. The predictor is
`GRU(42,64)`, followed from the commitment origin by `GRUCell(9,64)` unrolled in four-step
increments and a `64→64(tanh)→44(linear)` readout. It emits an eight-vector mean and 36
lower-triangular coordinates, with diagonal `softplus(d)+1e-3` and no adaptive jitter.

Fit mean Gaussian NLL for exactly 400 Adam updates, batch 256, learning rate `1e-3`, betas
`(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-5`, global gradient clip `1.0`, and one canonical
cyclic order without reshuffling. This successor selects the isolated scaffold initializer, not the
different B1 initializer: traverse `named_parameters()` in registered order; for every matrix draw
independent entries from unit-gain Xavier uniform
`[-sqrt(6/(fan_in+fan_out)), +sqrt(6/(fan_in+fan_out))]`; set every one-dimensional parameter to
zero; and assign in the parameter's FP32 dtype. In particular, each GRU recurrent matrix is one
whole Xavier draw, not a per-gate orthogonal initialization. Predictor initialization and order use
only the new counter-addressed `2026083001` predictor streams. The final predictor is frozen and
shared byte-identically by all three representations. No B1 parameter, optimizer, cursor,
checkpoint, result, or state is an input.

The same initializer traversal and distribution applies to `CommonHistoryGate` from its per-
replicate `gate_initialization` stream. RAW, TRUE, and DERANGED reconstruct that same addressed
stream separately, so their corresponding initial tensor bytes are identical within a replicate;
distinct replicates use distinct addressed streams. This initialization choice is part of the
scientific object and may not be replaced by the B1 tanh-gain/orthogonal law.

### Behavior and continuation

All predictor, calibration, gate-training, and evaluation histories use the exact deterministic
`scripted_decisions` law in the isolated `host_bridge.py`: printed option score
`-0.07*option_index + 0.01*agent + 0.02*queue_skew` for even option indices and the same expression
with `-0.02*queue_skew` for odd indices, locked host decisions, zero residual score, and the native
legal mask and charge law. No learned representation acts while histories are collected.

At an audit boundary, other agents retain the precomputed aligned scripted decisions, the target
agent receives the enumerated action, and the same script controls every agent from the next
primitive step through the common 16-step suffix. Every branch shares the immutable future tape.

### Calibration

Per replicate, reserve a preassigned 64-episode balanced fixed-K4/K8 calibration population that is
disjoint from predictor fit, gate training, and every evaluation panel. Use the same
continuous-commitment eligibility law, pool eligible residuals across the two K values and four
horizons, and freeze one midpoint empirical-CDF table per coordinate before any gate packet is
constructed:

```text
F_d(x) = (count(e_d < x) + 0.5*count(e_d = x) + 0.5) / (n_d + 1).
```

On the untouched aligned fixed-K16 evaluation histories, each replicate must supply at least 32
eligible targets at each horizon. For every eligible target define
`q=||solve(L_h,Y-mu_h)||_2^2`; its 90% ellipsoid is covered exactly when
`q<=13.3615661365`. First compute the coverage fraction within each replicate, then average the
eight fractions equally; the result must lie in `[0.80,0.98]` at every horizon.

For PIT set `u_d=F_d(e_d)` and bin it by `min(9,floor(10*u_d))`, with the right endpoint in the last
bin. For each `(h,d)`, compute the ten bin frequencies within each replicate, average those vectors
equally across the eight replicates, and set
`PIT_ECE_h,d=0.5*sum_b |frequency_h,d,b-0.1|`. The maximum over coordinates must be at most `0.10`
at every horizon. The clip-saturation statistic is the replicate-balanced fraction of whitened
coordinates with `|e_d|>=6` and must be below `0.05` at every horizon. Switch-regime calibration is
reported separately and never substituted for fixed K16. Failure of any calibration admission
makes every first-match calibrated-residual conclusion `NONIDENTIFYING`, never polarity.

### Canonical population and RNG instantiation

Within every replicate, episode indices are globally disjoint and frozen as follows:

| Population | Regime | Episode indices | Count |
| --- | --- | ---: | ---: |
| predictor fit | K4 | `0..127` | 128 |
| predictor fit | K8 | `128..255` | 128 |
| calibration | K4 | `256..287` | 32 |
| calibration | K8 | `288..319` | 32 |
| gate training | K8 | `320..831` | 512 |
| evaluation | K8 | `832..895` | 64 |
| evaluation | K16 | `896..959` | 64 |
| evaluation | 4→16 | `960..1023` | 64 |
| evaluation | 16→4 | `1024..1087` | 64 |

For predictor fit, gate training, and evaluation, use the exact isolated
`build_balanced_tapes`/legacy `balanced_scenario_specs` construction with the displayed count and
first episode index. The predictor-fit and fixed-K8 training counts are complete multiples of the
64 fixed-regime event×cost×onset cells; each fixed-regime evaluation cell appears once, and each
32-cell switch-regime evaluation cell appears twice.

The 64 calibration episodes use the accepted B1 stratification law: 32 per K, with four episodes in
each `(K,event,cost)` cell and equal marginal use of all eight fixed-regime onsets. In canonical
printed event order followed by cost `(0.25,4.0)`, number the eight event×cost cells `c=0..7`; for
within-cell row `j=0..3`, assign onset `FIXED_ONSETS[(c+j) mod 8]`. Enumerate K4 then K8 and assign
episode index `256+4*c+j` for K4 and `288+4*c+j` for K8. The calibration manifest is not shuffled;
this formula is its complete order. No caller may choose a different subset, order, or onset after
execution begins.

For every row above, let `split_ordinal` follow
`(PREDICTOR_FIT,CALIBRATION,TRAIN,EVALUATION)` and `regime_ordinal` follow
`(K4,K8,K16,K4_TO_16,K16_TO_4)`. The tape root is
`counter_seed("panel_tape",replicate,split_ordinal,regime_ordinal) mod 2^63`, and each episode seed is
that root plus its displayed episode index. Non-calibration manifest ordering, tape materialization,
and all other RNG purposes remain exactly the counter-addressed source laws; calibration uses the
explicit unpermuted order above and otherwise the same tape materialization. No retry, replacement,
ambient RNG, or caller-selected first index is permitted.

### Evaluation population and audit boundary

Each replicate has exactly 64 preassigned, unreplaced episodes in each of fixed K8, fixed K16,
`4→16`, and `16→4`, with eight episodes in every event-by-cost cell and the inherited onset
schedules. All tapes are fresh and disjoint from predictor fit, calibration, and gate training. K8
is diagnostic and reserved for the missing competence law. Average retained rows within each target
regime, then weight fixed K16, `4→16`, and `16→4` equally within the replicate. Episodes are
nested observations; the eight fresh replicates are the inferential units.

Scan primitive time and then environment slot in canonical order. Retain the first legal
discretionary review with a different legal replacement, continuous commitment, elapsed predictor
horizon in `{4,8,12,16}`, `event_or_pseudo_onset+4 <= t <= event_or_pseudo_onset+20`,
`abs(t-128)>8`, and `t+16<=256`. Boundary selection reads no residual, action, outcome, or future
quantity. An episode without such a row remains in the 64-episode availability denominator.

### Support and conditional simultaneous calculation

At least 48 of 64 episodes must yield the audit boundary in every replicate and evaluation regime. A
derangement cell is exactly `(split, regime, elapsed_horizon, cost)`; each retained cell has at least
eight rows, and cells below that floor are declared unsupported before assignment. Within each
replicate and separately within each deranged split (`TRAIN` and `EVALUATION`), pool otherwise
eligible rows across that split's regimes; at least 80% of that fixed denominator must remain in
supported cells. All representations must retain identical row keys. The persisted derangement is
an intact-packet, fixed-point-free bijection with exact packet-multiset
equality. Every replicate/target regime must have positive KEEP-optimal support. Within each
replicate, pool audited states across the three target regimes; at least 20% of that pooled set must
have replacement headroom
`max_replacement G16 - G16(KEEP) >= 0.02`.

For each of `regret_RAW-regret_TRUE`, `regret_DERANGED-regret_TRUE`, and
`regret_RAW-regret_DERANGED` at SHORT and LONG, form the eight paired equal-target-regime regret
differences. The accepted source defines the conditional model
`d_s iid Normal(theta,sigma^2)`, `n=8`, `df=7`, and the following two-sided Bonferroni calculation
at familywise alpha `0.05` across the six intervals:

```text
mean(d) +/- t_(1 - 0.05/(2*6), 7) * sd(d) / sqrt(8).
```

If the seed standard deviation is zero, the interval is the point estimate. Report every replicate
and regime. This formula is descriptive/model-conditional unless the inference-validity issue below
is resolved; it does not presently supply decision-bearing finite-sample coverage. Do not apply a
first-match interpretation merely because the numeric intervals exclude a margin.

### Primary scientific blocker

`NONIDENTIFYING_MISSING_RAW_LONG_COMPETENCE_LAW`: current CRTO authority does not define whether
RAW-LONG competence is absolute oracle-regret proximity, superiority or noninferiority to the logged
script, or an across-replicate inferential condition. It defines neither the aggregation rule nor a
numerical margin. `delta=0.005` belongs only to the six representation-by-budget contrasts, while
B1's `0.01` normalized-MSE and `0.95` sign gates measure a different decoder endpoint and do not
transfer. The same observed RAW-LONG panel could therefore be admitted or rejected by a post-result
choice.

The missing object is exactly the prospective tuple
`RAW_LONG_COMPETENCE = (K8 regret reference, replicate aggregation/bound, acceptance inequality and
numeric margin)`. Root may separately invest in a result-blind competence-definition/development
cycle to choose and justify that tuple. Such work must use development data and fresh later
confirmation; it cannot inspect this object's evaluation results or retroactively qualify them.
Until that tuple is frozen, retain result refusal and perform no optimizer update or scientific run.

### Second unresolved inference-validity issue

`NONIDENTIFYING_MISSING_REPLICATE_SAMPLING_AND_COVERAGE_LAW`: the eight replicate effects are
generated at fixed counter addresses. That construction isolates streams and makes reruns
deterministic, but it does not establish that the eight effects are an iid sample from a Normal
superpopulation, nor any other sampling law under which the Student-t intervals above have their
nominal finite-sample familywise coverage. Discreteness of the host and addressed pseudorandomness do
not supply that premise. Exact sign-flip or treatment-randomization inference is also unavailable:
the three representations were not randomly assigned under a sharp exchangeable null.

Current accepted CRTO evidence supplies neither a defensible replicate-population argument nor a
distribution-free simultaneous alternative with a prospective n=8 power or maximum-width bound at
the `0.005` material margin. The missing inference object is exactly
`SIMULTANEOUS_INFERENCE_VALIDITY = (target randomness/population law, coverage method, familywise
calibration, n=8 power-or-width bound, failure handling)`. Root may separately invest either in a
defensible sampling-model justification or in a distribution-free familywise construction with a
precomputed adequacy bound. It must be frozen before evaluation and cannot be chosen from observed
contrast signs or widths. Until both this object and `RAW_LONG_COMPETENCE` are frozen, no first-match
branch, READY command, or scientific run exists.

## Native endpoint and nulls

For every state enumerate KEEP and each legal replacement on the same scripted continuation and
immutable future tape:

\[
G_{16}(a;s)=\frac{\sum_{j=0}^{15}0.99^j r_{t+j}^{(a)}
+0.99^{16}\Phi(s_{t+16}^{(a)})}
{\max(1,\text{complete-tape physical arrivals})}.
\]

The target action's real charge occurs exactly once. Printed order breaks ties. Regret is the oracle
maximum minus the selected `G16`; average rows within regime and weight the three target regimes
equally per replicate. Replicate is the inferential unit.

Strong nulls are RAW-LONG, calibrated derangement, short-to-long exposure, logged scripted action,
zero-regret oracle, and absent action headroom. With `delta=0.005`, build simultaneous intervals for
RAW-minus-TRUE, DERANGED-minus-TRUE, and RAW-minus-DERANGED at both budgets.

First-match interpretations: persistent aligned bias; optimization-exposure only; generic
preprocessing; close tested mechanism; unresolved. The claim ceiling is finite-budget action-gate
representation/optimization bias on script-reachable histories, never information gain,
hypothesis-class superiority, full-policy return, MARL, warehouse, UAV, safety, or deployment value.

## Admission and stop law

Require disjoint panels; directly equal canonical history/tape/label structures; byte-identical initialization,
parameters, order, updates and work; persisted zero-fixed-point derangement with exact packet-multiset
equality; minimum retained-row support; finite packets/Cholesky factors; exactly 16 common-future
steps and charge once; target action headroom and KEEP-optimal support; and RAW-LONG in-support
competence. A failed gate is `NONIDENTIFYING`, never residual polarity.

After the first optimizer update all paths must reach LONG. No early result inspection, tuning, seed
substitution, retry, or post-result margin change. Planning ceiling: one CPU, no GPU, 2 GiB RSS, 120
minutes, and at most 2,596,864 primitive team steps.

That ceiling remains a planning limit, not an accepted complete execution ledger. The newly explicit
64-episode calibration population contributes `8*64*256 = 131,072` base primitive team steps, and
the current scaffold neither accounts for every training/evaluation common-future branch nor
enforces wall/RSS/step limits. A complete nonoverlapping ledger, runtime counters, thread law, and
resource preflight remain CM work only after `RAW_LONG_COMPETENCE` is frozen. This engineering gap
creates no scientific polarity and there is presently no valid READY or result command.

## Isolated implementation surface

```text
experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/
  __init__.py
  __main__.py
  config.py
  contracts.py
  host_bridge.py
  packets.py
  derangement.py
  models.py
  training.py
  evaluation.py
  analysis.py
  result.schema.json
  run.py

tests/experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/
  test_contract_and_cli.py
  test_common_history_panel.py
  test_packet_views_and_derangement.py
  test_common_future_g16.py
  test_matched_exposure.py
  test_analysis_schema.py
```

Core API materializes panels, enumerates common-future action returns, constructs packet views and
derangement, trains all paths through checkpoints `(128,2048)`, evaluates native regret, and
assembles a complete result. Only old host/tape primitives, stateless predictor packet math, and
common-future G16/regret equations may be extracted. The old v4 config/run/execution/training route
remains immutable provenance.

## CLI shape

```text
python -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 source-check
python -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 run \
  --output-root <fresh-root> --result <fresh-result.json>
```

Expose no checkpoint, resume, legacy-result, or update-1,000 option. Focused tests cover common
history/tape/label identity, split isolation, RNG domains, derangement invariants, charge-once G16,
masking/ties, matched work/continuation, RAW competence routing, atomic fresh-root output, schema
validation, and legacy-schema rejection.

## Evidence

- `DIRECTION.md`
- `CRTO_B1_SCIENCE_CARD.md`
- `CRTO_PROBE_CUT_R01_REVIEW_AND_HANDOFF.md`
- `experiments/candidates/commitment_residual_triggered_options/host.py`
- `experiments/candidates/commitment_residual_triggered_options/predictor.py`
