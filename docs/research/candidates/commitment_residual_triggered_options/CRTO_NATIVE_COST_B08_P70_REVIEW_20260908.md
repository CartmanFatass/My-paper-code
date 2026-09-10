# CRTO B08 P70 independent source review

No material finding remains in the reviewed correction. Parent acceptance identified a material
adverse-reading defect missed by the initial independent review; its evidence and repair are
recorded below. This is independent technical evidence for CM acceptance, not scientific
acceptance or an execution allocation.

Reviewed the working-tree additions on `codex/crto` against base
`de14dbab4bde01c3467885c78270ed73888e13fa`: `native_cost_b08/experiment.py`, its one-line
package initializer, and `scripts/run_crto_native_cost_b08.py`. No source or index was changed
by this review. Also inspected CM's focused `native_cost_b08/test_native_cost.py` and the
final endpoint-local integrity change; this review did not execute or claim test results.

Contract: [science card](CRTO_NATIVE_COST_B08_SCIENCE_CARD_20260908.md) sections 2–4 and 6–8;
MARL_RUNTIME_ENGINEERING_SPEC general requirements; ENGINEERING_SCOPE_SPEC sections 4–5;
MARL_EMPIRICAL_EVIDENCE_SPEC sections 11.8.5–11.8.8. No object-specific runtime appendix
applies to B08. The scientific-tools skill was applied to count/cost inspection; no additional
mode-specific reference or profiler was needed.

- **Loss and training:** `experiment.py:21–27` detaches labels, takes the maximum over legal
  actions, divides costs by .01, masks illegal logits before stable softmax, and averages row
  expected costs. This produces the card's per-row gradient, with an additional batch-mean
  factor and zero illegal-logit gradient. The copied loop at line 95 preserves B04's explicit
  initialization namespace/seed, fresh Adam settings, cyclic batch32 order, clipping and
  in-memory snapshots. The only objective replacement is the selected loss. B04 preparation
  and packet construction remain unchanged and are directly reused. All three paths finish
  before evaluation. No checkpoint, replay, recurrent-state or RNG interface was added.
- **Native measurement:** `score_summary` at line 219 reuses the inspected RAW scorer's legal
  first-printed argmax and FP64 native regret. Its inherited competence predicate requires
  eight rows, at least six exact actions and mean regret <=.005 on each side. B08 uses new
  RAW-LONG competence for both endpoint predicates. The three contrasts are separately
  present, use strict `>.0025`, retain all signed row gains/losses, and mark favorable/adverse
  endpoint combinations as mixed. It does not reuse B04's old branch rule or select a best
  checkpoint. Historical improvements remain descriptive when primary contrasts fail.
- **Historical comparison:** the actual B04 result JSON has the card's launch SHA and RAW
  SHORT/LONG regrets .006581880989529963/.0037814300857039115. `paired_contrast` at line 148
  pairs the same 16 identities, checks side/legal support, publishes old/new native values,
  records maximum legal-label differences, and rescoring uses the old action on new labels.
  A material label discrepancy limits the primary comparison instead of replaying or replacing
  the historical learner. Historical rows are retained in the new summary.
- **Complete cost:** `WallBudget` at line 65 accounts sequential arm intervals separately;
  complete elapsed minus their sum is common time charged in full to every arm. This includes
  active arm time while monitoring. Checks surround publication. Runner timing starts before
  its heavy imports, but is explicitly pre-publication in the summary. The collection reducer
  at line 302 uses terminal supervisor elapsed through command shutdown for final shared and
  per-arm charges, reports breaches, and does not sum per-arm charges as actual machine time.
  Aggregate CPU remains explicitly unmeasured. No new resource-efficiency claim is made.
- **Counts, topology and scope:** inspected loop/configuration counts are three paths ×258
  updates ×32 examples =774 updates/24,768 gate examples, plus 100×128 predictor examples;
  six readouts ×16 identities =96 decisions. New host/branch counts derive from returned row
  times and legal masks; calibration reports its actual example count. The reused import path
  sets native thread environment before NumPy/Torch imports and sets both Torch thread counts
  to one. B08 adds no compute team, mutable shared worker state, native build or device change.
  Tool-counted additions were 314 module lines before the one-line adverse-reading correction,
  one initializer line and 43 runner lines (359 total after correction), within 2,000/600.
  No uncarded prohibited item or concrete scope-budget breach
  was found. Required wall accounting and scientific comparison checks serve card sections
  4/6; no separate orchestration-ratio gate was imposed.
- **Focused test coverage:** inspected the synthetic algebra test's independent explicit
  gradient formula with unequal legal-set sizes and detached labels, large-logit/single-action
  fixture, printed ties, competence counts, all three strict-threshold cases, historical-floor
  failure, weak RAW, mixed endpoints and endpoint-local integrity limitation. Clock fixtures
  cover shared overhead/per-arm breaches; JSON readback covers summary and accounting; assembly
  replaces preparation, real training and forward calls and checks that all three trajectories
  precede readout. These test interfaces and changed behavior; they do not establish scientific
  value, host agreement or actual runtime feasibility.

Residual limits: this was read-only source and existing-artifact inspection, with zero scientific
invocations, reconstruction, staging, model creation/training, or synthetic fixture execution.
Numerical fixture evidence remains CM-owned. Actual historical-panel agreement, calibration/work
counts, runtime resource compliance and complete publication can only be assessed on the later
authorized invocation. Its collector must supply the terminal supervisor's complete elapsed to
the account command; the inner timestamp alone cannot establish complete wall compliance.
The final code limits an untrustworthy contrast to its affected endpoint's alignment flag,
while retaining the other endpoint's trustworthy signal and narrower native measurements.
The follow-up `result_reading` correction also preserves missing RAW-LONG competence as
`None`: both dependent alignment flags remain unknown and the description is
`PRIMARY_COMPARISON_LIMITED`, rather than observed weak RAW. Inspected the exact conditional
and its added fixture assertions; no material finding. CM reports 13 fixtures passing in
2.16s after endpoint-local handling and the modified weak/unknown-RAW fixture passing in
1.95s after this correction. These are CM execution results, not reviewer reruns.

**Parent-discovered finding and repair, same P70 source-only batch:** At `5fab87c44`,
`result_reading` filtered `losses` only by negative delta. With an untrustworthy SHORT
historical contrast of -.004 and trustworthy LONG contrasts of +.004, the implementation
correctly left SHORT alignment unknown but incorrectly labelled that unsupported comparison
adverse and set `mixed_budget=True`. This gave damaged primary measurement scientific polarity,
contrary to card section 4 and evidence-spec section 11.8.7. This was a material correctness
finding (P2), missed in the earlier review.

The inspected correction at `experiment.py:193–197` requires each adverse contrast's own
`comparison_trustworthy` flag as well as a negative delta. It does not require the entire
endpoint to be trustworthy: a valid SHORT new-RAW loss still supports mixed-budget reading
alongside a valid LONG signal even when SHORT's historical comparison is unavailable. Full
contrast values and signed row facts remain unchanged. This implements the suggested repair
at the actual dependency, with no new machinery or scientific exposure.

Inspected `test_adverse_and_mixed_reading_requires_individual_contrast_trust`: its first case
excludes an untrustworthy negative from both adverse and mixed reading, while its second case
retains a trustworthy new-RAW negative at that otherwise limited endpoint. The fixture also
checks that the original untrustworthy numerical delta remains available. CM reports this
regression and the existing mixed-budget test passed together (2 tests, 1.93s pytest wall;
3.102s process wall). No reviewer rerun, source edit, index change or scientific work occurred.
The parent-discovered defect is repaired in the inspected working-tree diff against `5fab87c44`;
the runtime and scientific-evidence limits above remain.
