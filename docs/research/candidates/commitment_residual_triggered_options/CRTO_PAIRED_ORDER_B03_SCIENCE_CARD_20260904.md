Claim: Labelled interleaving of the original TRAIN pairs may improve RAW native action regret over the canonical order at exactly matched per-row exposure on the selected panel.
Binding MARL structure: `systems / information flow`; the fixed four-agent gate acts on partial common history, while this object measures a training-order package rather than residual information or a general multi-agent effect.

# CRTO paired TRAIN order B03 card

Object `CRTO-PAIRED-ORDER-B03`; **B/EXPLORE**, seed 0, frozen 2026-09-04 before implementation.
Object-tier adaptive successor in the already-open balanced RAW comparator ladder. B02's valid
mean-readout negative, B01's comparator-weak result, A01's unresolved native crash, A02's separate
no-fault result and the natural-support family closure retain their original meanings.

## Question, treatment, comparator and exposure

Does original-pair TRAIN interleaving improve native action regret over the competent canonical
RAW order at update 258, with the same examples per row, optimizer count, initialization and
information? Observe additional complete-cycle endpoints 252 and 255, never a selected best point.

Reuse the exact B01 card's 48 TRAIN /16 EVAL members, predictor, RAW packet, source namespaces,
legal-action/G16 evaluator and fixed four-agent environment-to-consequence path. B01 section 4
remains the full population specification. One persistent option-owning slot receives the same
42-vector history and 52-vector RAW packet, chooses a legal KEEP/replacement action, pays the native
charge once, and is scored on the same 16-step future. There are no roster changes, replacement,
censoring, lifetime effects or partner co-adaptation. No old learner state or confirmation read.

Two from-genesis RAW paths share one predictor fit and one population/packet/label preparation:

- **CANONICAL**, strongest available competent same-information comparator: unchanged ordering
  by `row.key.canonical` (source slot, then episode). Ordinary phase-0 checkpoints passed in A03;
  this fresh path's competence is remeasured, not assumed or gated by historical identity.
- **PAIRED**, treatment: retain the original `SELECTED_ROWS` pair declaration order, filter the
  24 TRAIN pairs, and interleave each original KEEP then REPLAN member. Pair identity is original
  declaration position and both source addresses; event/onset is nonunique and must not define
  new pairs. Apply the same permutation to rows, packet values and packet row keys.

Both use cyclic `np.resize(arange(48),258*32)` in their respective row ordering. Each PAIRED batch
contains 16 complete original pairs, hence 16 KEEP +16 REPLAN. Three consecutive updates visit every
TRAIN row twice. At the only measured endpoints:

| update | processed examples per arm | occurrences per TRAIN row per arm |
| --- | --- | --- |
| 252 | 8064 | 168 |
| 255 | 8160 | 170 |
| 258 (primary) | 8256 | 172 |

The entire per-row training multiset matches between arms at all three points. No intermediate
prefix or arbitrary-ending equality is claimed. This is a labelled TRAIN-order intervention:
the same training targets already available to both learners determine the treatment schedule.
EVAL labels never determine order, stopping, snapshots or selection. No new label information.

This package changes side balance, pair adjacency and event/onset grouping together. Live nulls
are generic order sensitivity, those other grouping features rather than side balance, one-seed
predictor/selected-panel variation, already adequate canonical exposure, or an implementation
defect. A positive result identifies only this complete order package against this comparator.

## Protected learner semantics and implementation boundary

Reuse B02's accepted `train_raw`, `forward_snapshots`, `panel_labels`, `score_readout` and simple
publication helpers; do not modify B01/B02 or invoke B02's cycle-mean/branch orchestration.
Each arm recreates the same namespace/seed-0 model parameters and fresh Adam. Use CPU FP32,
one thread, batch 32, Adam lr .001/betas(.9,.999)/eps1e-8/zero weight decay, gradient clip1 and
the same legal-action MSE. Train CANONICAL then PAIRED without changing the shared initialization
law. Predictor: unchanged128 tapes,100 updates,batch128/lr.001/12,800 processed examples. No
residual calibration, TRUE or DERANGED arm. Keep in-memory snapshots immediately after252/255/258;
score both paths only after all training is complete. No checkpoint files or optimizer-state I/O.

Both ordinary readouts use the existing printed-order legal maximum and first exact tie; native
G16 is finite signed and regret is finite nonnegative oracle-minus-selected. No averaging or
new numerical precision. Protect the exact population/split, namespaces, packet equations,
initialization/RNG, per-arm Adam/order, legal labels/masks, charge/denominator, EVAL isolation and
one-output-root side effects. Historical anchors are descriptive only.

## Observable, primary estimand and first-matching rule

Record the two TRAIN index/address sequences and original pair identifiers, the three endpoint
per-row occurrence counts, all six snapshot exposure lines, every legal prediction and native
label/action/regret, and each side's count/exact/mean. For each arm and U:

```text
R(arm,U) = (mean_KEEP_regret + mean_REPLAN_regret)/2
C(arm,U) = each side has8 rows, >=6 exact actions and mean regret<=.005
D(U) = R(CANONICAL,U)-R(PAIRED,U)
primary = D(258); delta=.0025
```

For a technically valid complete result apply the first matching branch:

1. **`B03-COMPARATOR-WEAK`**: not `C(CANONICAL,258)`. Retain the diagnostic but make no
   competent-comparator order claim.
2. **`B03-MATERIAL-REGRET-LOSS`**: any `D(U)<-delta`. The paired order has a material cost
   at a declared matched-exposure point; do not adopt it from this result.
3. **`B03-PAIRED-ORDER-SIGNAL`**: `C(PAIRED,258)` and `D(258)>delta`, with every `D(U)>=-delta`.
   A preliminary order-package signal on this seed/panel; it does not isolate side balance.
4. **`B03-PAIRED-ORDER-NO-MATERIAL-GAIN`**: `C(PAIRED,258)` and `D(258)<=delta`, with every
   `D(U)>=-delta`. Competence is preserved at the primary endpoint without a material gain.
5. **`B03-PAIRED-ORDER-INCOMPETENT`**: not `C(PAIRED,258)`, with every `D(U)>=-delta`.
   The paired order does not supply the desired primary comparator, even if some aggregate improves.

Report all earlier endpoint competence and signed D values; no point/arm selection, retuning or
result-sensitive stop. Missing required learner measurements, row/packet/order mismatch, unequal
declared per-row exposure, unauthorized semantics, nonfinite learner activity or incomplete output
produces no scientific branch. Resource telemetry gaps alone leave a valid non-resource result
`resources_unmeasured`. Tests/exit do not establish an order effect. B has no consumption state.

## Claim ceiling, MEI, headroom and predictions

This is one-seed, outcome-informed development on an already exposed finite panel. It cannot
establish stable or independent performance, general side-balance or cyclic-order causality,
residual value, information/function-class advantage, natural K8 prevalence, tuned headroom,
policy/MARL/variable-K-or-N value, transfer, safety or deployment.

MEI is absolute .0025 native-G16 regret, retaining one quarter of the panel's minimum selected
advantage; relative scaling is unsuitable near zero. Above-MEI primary benefit with competence
would motivate independent-seed/order-control work. Inside-MEI would keep canonical as the simpler
known comparator; opposite-sign material cost would drop this order candidate. The branch rule
controls. Headroom remains absent: no tuned same-information baseline/upper package with seeds
and curves exists. Other host baselines mismatch this panel's information/action/population/budget.

DM prediction: **`B03-PAIRED-ORDER-NO-MATERIAL-GAIN`**, primary D inside MEI. The existing complete-
cycle canonical comparator is competent; balancing order may change boundary decisions without
the large aggregate gain required here. Owner: `not taken (unattended)`. Existing ladder: no new
first-card prediction item or C freeze.

## Cost, exposure planning, execution and stop

Runner non-result `project-cost` emits this stage law from measured B02 runner seconds:

```text
B=86.52683217800222-14.290888625997468-.015708084996731486-.0031209949956974015
t=14.290888625997468/257; f=.015708084996731486/5; r=.0031209949956974015
per_arm=3*(B+258*t+3*f+r) ~=259.728466544 seconds
shared=3*(B+2*258*t+6*f+r) ~=302.796226686 seconds
per-arm cap=600 seconds; shared invocation cap=600 seconds
```

Formula controls ordinary floating rounding. Factor3 covers preparation/order/publication load;
both arm forecasts conservatively include shared preparation, actual time is charged once.
No sweep or new pilot. One invocation; two RAW paths total516 updates/16,512 examples; six
snapshots×16=96 forward/scored rows,16 unique EVAL rows. Predictor/host preparation occurs once;
report measured environment/branch/predictor counts separately.

The machine-generated planning exposure cites unchanged initial L2/RMS/Linf
18.87916908516977/.10402732933491829/.28862619400024414 and nominal LR exposure .258.
A03 measured this RAW budget moving by L2/initial-L2 .136922756396 and Linf/initial-Linf
.915735779253. This demonstrates usable budget, not identical future paired weights. Emit both
arms' own finite positive displacement ratios and full exposure fields at every saved endpoint.

One CPU process/thread, expected peakRSS<2GiB. Host CPU identity is not the estimand; portable
configured CPU execution with the same FP32/RNG law, no GPU or bit-identity claim. Remote-first
exact committed/pushed source, detached worktree and agent-task; adjacent fresh destination
admit-memory (physical/effective>=4GiB) joined to `python -X faulthandler` and the runner. The
existing shared600s monitor applies across both arms. Stop at one complete summary or first
admission/integrity/nonfinite/measurement/cap failure. No retry loop, row replacement or resume.
Local fallback only under the configured prospective portability/no-remote-acceptance rule.

## Scope, ownership and next step

**Engineering scope section4: none of its prohibited machinery is needed.** Reuse accepted
training/readout/publication functions; only construct a different TRAIN ordering and new object
summary/rule. Own new `experiments/candidates/commitment_residual_triggered_options/paired_order_b03/`,
`scripts/run_crto_paired_order_b03.py`, mirrored tests and technical E0. Runtime root:
`temp/directions/commitment_residual_triggered_options/exp/paired_order_b03_20260904/`.
Stay below2000 research lines,600 runner lines,30% orchestration. Return unrequested additions.
Use one toy E2E smoke and focused original-pair/packet-binding/per-batch16-16/per-row-exposure,
two-fresh-initializations and branch tests. Exercise six actual-sized16-row summaries to publication
offline with marked synthetic scores, reusing native-label fixture. No new validator framework.

CM owns implementation/review/launch/collection; tracker `/root/tracker_tl_experiments` observes
each accepted handle and reminds DM `/root/dm_amx_crto_continue` directly. DM checks E0 against
this card and independently takes in every result. Technical conformance has no mechanism polarity.
Owner surfaces are asynchronous; Root owns shared audit/integration and lifecycle/priority.

Options: **(a)** this two-path exact-row-exposure paired-order discriminator; **(b)** increase
RAW budget/capacity first; **(c)** reopen residual comparisons before testing the concrete order
alternative. Recommendation **(a)**. **Owner-delegated decision (unattended,2026-09-03 instruction):
(a)**, continued by owner2026-09-04 resume. This changes comparator treatment within the accepted
family only; no Direction or Portfolio choice and no Pro launch condition.

References: `CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md` section4;
`CRTO_RAW_CYCLE_READOUT_B02_INTAKE_20260904.md`;
`CRTO_RAW_CYCLE_READOUT_B02_RESULT_EVIDENCE_20260904.md`;
`CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_RESULT_EVIDENCE_20260904.md` exposure table.
