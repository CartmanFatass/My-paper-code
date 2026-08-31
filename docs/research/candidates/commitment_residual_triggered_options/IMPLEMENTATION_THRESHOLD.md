# CRTO common-history gate implementation threshold

Status: `RESULT_BLIND_PREFLIGHT_COMPLETE_PRODUCTION_BLOCKED`

Object: `CRTO-COMMON-HISTORY-GATE-20260830-01`. This is a fresh prospective object, never an
update-1,000 continuation. It must load no B1 probe, optimizer, checkpoint, cursor, result, or
artifact. The isolated implementation and focused tests are technically accepted. The automatic
wave-2 source audit below freezes the recoverable predictor, behavior/continuation, calibration,
evaluation-population, audit, and support laws. The `2026-08-31` competence/census freeze now defines
the previously missing RAW-LONG numerical gate and replaces decision-bearing Student-t inference
with an exact all-slot finite-panel law. The material-stratum analysis, exact census hulls, strict
result contract, result-blind structural preflight, prospective branch ledger, runtime monitor
seams, and shared resource checks are implemented and focused-test green. A result-bearing run
remains unavailable because the single-pass residual/calibration/first-boundary transaction, staged
RAW-LONG routing, final publication, and second fresh launch admission are not yet connected. The
current fail-closed `run` entry remains correct; it must not be bypassed.

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

## Source-grounded freeze — automatic waves 2 and 3

The following laws are selected from the accepted B1 predictor/calibration/audit sources, the
fresh-object threshold above, the isolated scaffold at source commit `1bea5cc9`, and
`CRTO_COMMON_HISTORY_GATE_R01_COMPETENCE_AND_CENSUS_FREEZE_20260831.md`. This is direction-level
scientific authority for the successor; it is not a claim that the present provisional code
conforms end to end. No result activity may begin until CM implements and checks this complete
freeze, including the material-stratum competence and exact census law below.

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
is reserved for the now-frozen competence law. Average retained rows within each target
regime, then weight fixed K16, `4→16`, and `16→4` equally within the replicate. Episodes are
nested observations; the eight fixed replicates are complete census slots, not inferential samples.

Scan primitive time and then environment slot in canonical order. Retain the first legal
discretionary review with a different legal replacement, continuous commitment, elapsed predictor
horizon in `{4,8,12,16}`, `event_or_pseudo_onset+4 <= t <= event_or_pseudo_onset+20`,
`abs(t-128)>8`, and `t+16<=256`. Boundary selection reads no residual, action, outcome, or future
quantity. An episode without such a row remains in the 64-episode availability denominator.

### Support and RAW-LONG competence

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

K8 competence has an additional two-sided material-decision support law. For every retained K8 row
define `A=max_replacement G16-G16(KEEP)`. `KEEP_MATERIAL` contains rows with `A<=-0.02` and
`REPLAN_MATERIAL` contains rows with `A>=+0.02`; middle rows remain in the representation contrasts
but not in competence. Every replicate must have all 64 unreplaced K8 episodes, at least 48 retained
boundaries, finite/common row labels and keys, valid charge-once common futures, and at least eight
rows in each material stratum. A support failure is `NONIDENTIFYING_K8_COMPETENCE_SUPPORT`.

Within each replicate and stratum, average RAW-LONG native oracle regret. Define

```text
C_RAW = max over replicate 0..7 and {KEEP_MATERIAL,REPLAN_MATERIAL}
        mean(max_legal G16 - G16(RAW_LONG_selected_action)).
```

RAW-LONG is competent if and only if `C_RAW<=0.010000000000`; an arithmetic tolerance no larger
than `1e-12` is permitted but is not a scientific margin. The oracle is the reference. The ceiling
is half the registered `0.02` material KEEP-versus-replan gap in the same G16 units; it is not the
B1 decoder-NMSE threshold. Report logged-script regret and RAW-minus-script regret in all sixteen
cells, but do not use script superiority as a competence gate. All sixteen cells must pass; no
mean, median, seven-of-eight, or cross-stratum compensation is allowed. Valid support with a failed
gate is `STOP_RAW_LONG_INCOMPETENT`, and no TRUE/DERANGED polarity may then be interpreted.

The material strata are necessary. An always-KEEP rule would have overall regret only
`0.2*0.02=0.004` if its entire error were confined to the registered 20% replanning-headroom rows;
an unstratified mean could therefore admit a comparator that never learned the decision of interest.

### Exact fixed-eight simultaneous decision

Replicate addresses `0..7` under namespace `2026083001` and all their preassigned tapes,
initializers, and orders are the complete finite target. They are not treated as a sample from a
seed/address superpopulation. For each replicate, first average retained-row regret within each of
fixed K16, `4->16`, and `16->4`, then weight those three regime means equally.

For budget `b` and replicate `s`, define

```text
x_RT(b,s) = regret_RAW(b,s)       - regret_TRUE(b,s)
x_DT(b,s) = regret_DERANGED(b,s) - regret_TRUE(b,s)
x_RD(b,s) = regret_RAW(b,s)       - regret_DERANGED(b,s)
L_jb = min_s x_j(b,s)
U_jb = max_s x_j(b,s).
```

Each `[L_jb,U_jb]` is the exact hull of all eight registered effects, not a confidence interval.
Report all replicate/regime effects, all six hulls, and the equal-slot means; means are descriptive
only. The six hulls are observed simultaneously, so alpha, probability coverage, multiplicity,
standard error, and power do not apply. Their width is registered-slot heterogeneity. Missing,
nonfinite, replaced, or dropped slots make the complete family `NONIDENTIFYING`.

Every row-level native regret and every base `regret_REPRESENTATION(b,s)` value must be finite and
nonnegative. Derive all three contrasts from the same base regrets rather than accept independent
contrast inputs; `x_RT=x_RD+x_DT` must hold by construction. Exactly eight slots, these numeric
requirements, and every preceding structural/admission gate define branch validity. Failure is
`NONIDENTIFYING` and never enters the truth table.

With `delta=0.005`, define `SUP(j,b)` as `L_jb>delta`, `EQ(j,b)` as
`L_jb>=-delta && U_jb<=delta`, and `NO_TRUE_BENEFIT(b)` as `U_RTb<=delta`. Also define

```text
RAW_GAIN = min_s [regret_RAW(SHORT,s)-regret_RAW(LONG,s)] > delta
TRUE_NO_MATERIAL_DEGRADE =
    max_s [regret_TRUE(LONG,s)-regret_TRUE(SHORT,s)] <= delta.
```

After every earlier gate passes, route the first exact match:

```text
PERSISTENT_ALIGNED_BIAS =
    SUP(RT,SHORT) && SUP(RT,LONG) && SUP(DT,SHORT) && SUP(DT,LONG)

GENERIC_PREPROCESSING =
    SUP(RT,SHORT) && SUP(RT,LONG)
    && SUP(RD,SHORT) && SUP(RD,LONG)
    && EQ(DT,SHORT) && EQ(DT,LONG)

OPTIMIZATION_EXPOSURE_ONLY =
    SUP(RT,SHORT) && SUP(DT,SHORT)
    && EQ(RT,LONG) && EQ(DT,LONG) && EQ(RD,LONG)
    && RAW_GAIN && TRUE_NO_MATERIAL_DEGRADE

CLOSE_TESTED_MECHANISM =
    NO_TRUE_BENEFIT(SHORT) && NO_TRUE_BENEFIT(LONG)

otherwise UNRESOLVED.
```

The SHORT DT term excludes derangement-insensitive preprocessing from the optimization branch; all
three LONG equivalences exclude persistent alignment use. `RAW_GAIN` and
`TRUE_NO_MATERIAL_DEGRADE` prevent a worsening TRUE arm from manufacturing apparent RAW catch-up.
`CLOSE_TESTED_MECHANISM` closes only material TRUE-over-RAW benefit. It deliberately includes
negative RAW superiority and must not be reported as equivalence unless both `EQ(RT,SHORT)` and
`EQ(RT,LONG)` also hold. Equality at `delta` is not superiority; `+/-delta` are inside equivalence.

For each budget inside CLOSE, report `RAW_SUPERIOR` when `U_RTb < -delta`,
`PRACTICAL_EQUIVALENCE` when `EQ(RT,b)`, and `MIXED_OR_SMALL_TRUE_EFFECT` otherwise. These are
descriptions, not new branches. A combined equality statement requires both budget-specific EQ
predicates.

The historical iid-Normal Student-t/Bonferroni calculation may be retained only as an explicitly
model-conditional descriptive sensitivity analysis and may not route any branch. Bonferroni cannot
repair an invalid marginal model: if an iid effect is zero with probability `0.9` and `0.1` with
probability `0.1`, eight zeros occur with probability `0.9^8=0.43046721`; the zero-SD point interval
`[0,0]` then misses the population mean `0.01`. The fixed census law avoids that unsupported target
by narrowing the claim rather than inventing sampling coverage.

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
equally per replicate. Replicate is one fixed census slot.

Strong nulls are RAW-LONG, calibrated derangement, short-to-long exposure, logged scripted action,
zero-regret oracle, and absent action headroom. With `delta=0.005`, build the exact all-slot hulls
for RAW-minus-TRUE, DERANGED-minus-TRUE, and RAW-minus-DERANGED at both budgets.

First-match interpretations: persistent aligned bias; generic preprocessing; optimization-exposure
only; close tested mechanism; unresolved. The claim ceiling is finite-budget action-gate
representation/optimization bias on script-reachable histories, never information gain,
hypothesis-class superiority, full-policy return, MARL, warehouse, UAV, safety, or deployment value.

## Admission and stop law

Require disjoint panels; directly equal canonical history/tape/label structures; byte-identical initialization,
parameters, order, updates and work; persisted zero-fixed-point derangement with exact packet-multiset
equality; minimum retained-row support; finite packets/Cholesky factors; exactly 16 common-future
steps and charge once; target action headroom and KEEP-optimal support; both K8 material strata; all
six exact census hulls; and all-slot RAW-LONG competence. A failed support/structure gate is
`NONIDENTIFYING`, never residual polarity; valid RAW incompetence stops residual interpretation.

After the first optimizer update all paths must reach LONG. No early result inspection, tuning, seed
substitution, retry, or post-result margin change. Planning ceiling: one CPU, no GPU, 2 GiB RSS, 120
minutes, and at most 2,596,864 primitive team steps.

Immediately before every result-bearing development or confirmation invocation, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require at least 4 GiB
physical and effective available memory. A resource refusal is engineering-only and cannot alter a
scientific branch.

The prospective preflight now charges the complete `8*1088*256 = 2,228,224` base-tape population,
performs a result-blind first-boundary scan, counts KEEP plus every legal changed-option G16 branch,
and refuses when `2,228,224 + 16*branch_count` exceeds the fixed ceiling. The runtime ledger binds
that expected branch count to actual branches and exposes one-worker, one-thread, wall, RSS, and
optimizer-loop monitor seams. Official preflight creates fresh shared 4 GiB and `assess-run`
receipts, but deliberately retains a failed `single_pass_production_pipeline` gate.

The first official final-namespace preflight completed on `2026-08-31`: it observed
`15,023,247,360` physical/effective available bytes, retained all `6,144/6,144` structural
boundaries, passed every per-slot support gate, and counted `19,295` prospective branches. Its
exact charged total was `2,536,944`, leaving `59,920` below the ceiling. All question-relevant
activity counters were zero. See
`CRTO_COMMON_HISTORY_GATE_R01_RESULT_BLIND_PREFLIGHT_20260831.md`.

The remaining exact blocker is
`ENGINEERING_SINGLE_PASS_RESIDUAL_CALIBRATION_PIPELINE_INCOMPLETE`: all-horizon residual collection,
first-boundary G16, calibration aggregation, staged RAW-LONG competence, final analysis publication,
and a second fresh memory admission immediately before production are not yet wired into one
transaction. Therefore `ready_for_optimizer=false`; development and confirmation runs are both
ineligible. This engineering gap creates no scientific polarity.

### Optional two-slot development pilot

Before a full confirmation, CM may implement one RAW-only B-level feasibility pilot with two
development slots in an RNG namespace disjoint from final `2026083001`. It uses the same predictor,
2,048-update RAW checkpoint, 64 fixed-K8 development tapes, material strata, support rules, and
`0.01` competence ceiling. It does not train or inspect TRUE/DERANGED and cannot read final slots,
select a checkpoint/address, or change `0.02`, `0.01`, `0.005`, exposure, or row laws. A pass shows
feasibility only. A fail updates only that development architecture-budget object; any repair needs
fresh confirmation addresses. The 4 GiB admission applies immediately before this pilot.

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
  ledger.py
  preflight.py
  production.py
  result.schema.json
  run.py

tests/experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/
  test_contract_and_cli.py
  test_common_history_panel.py
  test_packet_views_and_derangement.py
  test_common_future_g16.py
  test_matched_exposure.py
  test_analysis_schema.py
  test_preflight_pipeline.py
```

Core API materializes panels, enumerates common-future action returns, constructs packet views and
derangement, trains all paths through checkpoints `(128,2048)`, evaluates native regret, and
assembles a complete result. Only old host/tape primitives, stateless predictor packet math, and
common-future G16/regret equations may be extracted. The old v4 config/run/execution/training route
remains immutable provenance.

## CLI shape

```text
python -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 source-check
python -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 preflight \
  --output-root <fresh-root> --result <fresh-result.json> \
  --resource-receipt <fresh-memory-receipt.json> \
  --run-resource-receipt <fresh-run-resource-receipt.json> \
  --receipt <fresh-preflight-receipt.json>
python -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 run \
  --output-root <fresh-root> --result <fresh-result.json> \
  --resource-receipt <fresh-launch-memory-receipt.json> \
  --run-resource-receipt <fresh-launch-run-resource-receipt.json> \
  --preflight-receipt <fresh-launch-preflight-receipt.json>
```

Expose no checkpoint, resume, legacy-result, or update-1,000 option. Focused tests cover common
history/tape/label identity, split isolation, RNG domains, derangement invariants, charge-once G16,
masking/ties, matched work/continuation, RAW competence routing, atomic fresh-root output, schema
validation, and legacy-schema rejection.

## Evidence

- `DIRECTION.md`
- `CRTO_COMMON_HISTORY_GATE_R01_COMPETENCE_AND_CENSUS_FREEZE_20260831.md`
- `CRTO_COMMON_HISTORY_GATE_R01_RESULT_BLIND_PREFLIGHT_20260831.md`
- `CRTO_B1_SCIENCE_CARD.md`
- `CRTO_PROBE_CUT_R01_REVIEW_AND_HANDOFF.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `experiments/candidates/commitment_residual_triggered_options/host.py`
- `experiments/candidates/commitment_residual_triggered_options/predictor.py`
