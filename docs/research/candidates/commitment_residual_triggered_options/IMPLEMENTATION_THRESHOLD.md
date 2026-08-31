# CRTO common-history gate implementation threshold

Status: `IMPLEMENTED_SCIENTIFIC_FREEZE_INCOMPLETE`

Object: `CRTO-COMMON-HISTORY-GATE-20260830-01`. This is a fresh prospective object, never an
update-1,000 continuation. It must load no B1 probe, optimizer, checkpoint, cursor, result, or
artifact. The isolated implementation and focused tests are technically accepted, but a
result-bearing run is not scientifically defined until the remaining predictor, behavior,
calibration, evaluation-population, competence, and simultaneous-inference laws are frozen.

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
