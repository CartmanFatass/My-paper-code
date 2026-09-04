# FSD E2 interruption-cost sweep — DM intake

Intake date: 2026-09-04

Direction: `flexible_skill_duration`

Tier of the decision below: **object**

Provenance: `OWNER_DELEGATED` under the owner's unattended instruction of 2026-09-03

Result evidence:
`FSD_E2_INTERRUPTION_COST_SWEEP_RESULT_EVIDENCE_20260904.md`

## Intake disposition

**ACCEPT as a valid B — EXPLORE result with the frozen verdict `NEITHER`.**

The result does not support mechanism A, does not satisfy mechanism B's stronger null branch, and
does not consume a C object. The direction remains open at the B claim ceiling.

## What I checked

1. **Result against the frozen card.** I read the card's question, non-goals, treatment, D0
   comparator, seeds, budget, stop rule, measurements, and section 5 rule. I independently
   recomputed `R_best0`, every across-seed range `s`, each seed/cost return pass, the two segment
   monotonicity checks, the alignment threshold, D0 sanity, and the two reviewer clauses from the
   per-run `summary.json` files. The recomputation agrees with `E2_summary.json`.
2. **Counts.** All 15 accepted summaries say `completed: true`, `rollouts_completed: 20`,
   128,000 transitions, 320 training episodes, four evaluations totalling 3,584 episodes, and
   nonzero optimizer steps for all five trained network groups. Totals are recorded in the result
   evidence.
3. **Receipts.** Each accepted run has a passing `preflight.json`, clean manifest, 20 learner,
   interruption, and gap records, four evaluation records, a finite positive exposure line, and a
   final checkpoint. Effective available memory was 8.713–13.753 GiB. The scientific code surface
   is unchanged from the launch commit despite later queue/document commits.
4. **Excluded attempts.** Both `d0_k1` directories carry `QUARANTINED`, stop at 8/20 by an explicit
   budget decision, and have no `summary.json`; no value from them enters the result. `d0_k2` seed 2
   never launched. These facts have no scientific polarity.
5. **Rule applied verbatim.** `k=20` is the best D0 arm in both seeds. Only `c=0.25` passes the
   range-tolerant return bar, and only in seed 1. Segment means rise monotonically with `c` in both
   seeds. Alignment is below `0.5` for all `c` and seeds. That maps to `NEITHER`, not A and not B.
6. **Engineering conformance.** The 10.236 h elapsed study breached its frozen 8 h whole-study cap
   by 28.0%; the outcome-blind re-projections and arm decisions are on record. The final 15 runs
   retain every deciding quantity. The historical queue and liveness probe are the two declared
   engineering-scope section 4 items; no successor object needs them.

Test success, the presence of checkpoints, and the aggregator's exit are treated only as technical
facts. The mechanism reading comes from the frozen rule and the observed numbers above.

Focused technical verification after the intake: the first pytest invocation reached 31 passes
and five setup errors because the requested `--basetemp` parent did not exist. Repeating the same
test bytes after creating that temporary parent produced **36 passed**. This reproduces and
classifies the first failure as an invocation-path setup issue; no source or evidence byte changed,
and it contributes no scientific polarity.

## Observation that bounds the result

On the homogeneous corridor, D2's threshold controls persistence but does not behave as the
card's event-driven boundary: mean segment length is monotone in both seeds, while the largest
event-alignment fraction is only `0.124684`. D2 is below the best learned fixed clock in raw return
at every finite `c` and both seeds. Wide seed variation lets `c=0.25` pass the card's tolerant bar in
seed 1, preventing the stronger mechanism-B branch.

The smallest scientific update is therefore local: the observed D2 implementation has a usable
duration knob, but E2 supplies no two-seed support for an event-aligned return match on this
homogeneous host. It does not answer whether heterogeneous hazards make adaptive renewal valuable.

## Predictions and live explanations

- Owner prediction: not borne out on this setup; no finite `c` reaches the best D0 raw return and
  mechanism A is not supported by the frozen rule.
- Reviewer prediction: not borne out; seed-mean best `c=0.25`, not `[0.5,1.0]`, and alignment is
  nowhere above `0.5`.
- Strongest support for D2: segment length increases monotonically with `c`; `c=0.25` is the
  highest seed-mean D2 return and passes the tolerant return bar in seed 1.
- Strongest contradiction: no `c` passes both seeds, raw D2 return loses in every comparison, and
  event alignment remains very low.
- Surviving alternative: a homogeneous population gives a tuned fixed clock no compromise to
  solve; the registered heterogeneous rows create different renewal optima by region. The
  competing explanation is that the learned policy gap is optimizer noise and will remain
  non-actionable even when hazards differ.

## Flags for the owner

- E2's best `c` is not stable by seed (`0.25` versus `2.0`). Any negative successor result is
  bounded to the prospectively chosen `c=0.25`; it cannot close every D2 threshold.
- E2 did not form paired per-episode arm differences even though it used matched tapes. The E3
  card requires the paired difference directly.
- The 8 h study cap was materially breached. The successor uses the current per-arm cap and a
  conservative per-arm projection; it does not recreate the historical whole-study queue.
- Raw run roots and checkpoints remain local to this worktree. The deciding numbers and receipts
  are preserved in the tracked result evidence; deleting the raw root is not part of this intake.

## Decisions this intake produces

### Decision 1 — next rung inside the accepted D2 mechanism

Options:

- **(a) E2b:** transfer E2's seed-mean best `c=0.25` to UAV scenario 1 against D0. This tests host
  transfer, but E2 supplied neither a stable chosen `c` nor the event-aligned mechanism that would
  make transfer the most informative next question.
- **(b) E3:** run the registered heterogeneous-hazard discriminator at the three exact proposal
  rows, with D2 `c=0.25` against the exact best fixed-`k` D0 arm. Add paired per-episode return
  differences and region-specific renewal/action-path measurements. This directly tests the
  direction's native claim: whether one global fixed clock loses when regions have different
  hazards.

Recommendation: **(b)**. It is the narrower, higher-information next rung. It preserves D2 and the
same-information comparator, changes only the host quantity the direction says should make adaptive
duration useful, and is reversible B exploration. E2b remains available only if a stable corridor
signal later supplies a defensible transfer point.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).**

Provenance label: `OWNER_DELEGATED`.

This is an object-tier next-rung decision inside the already accepted E-series. It does not change
lifecycle, priority, capacity, direction registration, frozen E2 meaning, or Portfolio investment.
No Direction Pro round is required. Opening D3, promoting to C-BENCH, or deciding what follows a
valid E3 result would be separate decisions at their applicable tiers.

## Decision boundary and next discriminator

The selected E3 object is frozen in
`FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. No result-bearing E3 invocation may start
until the E2 evidence, this intake, the card, the direction update, and the audit row are committed;
each invocation then requires its own fresh 4 GiB admission receipt.

The next discriminator is whether D2 at the prospectively selected `c=0.25` produces a positive
paired return difference against the best fixed `k` on the large heterogeneous row, with the
native action path visible as more frequent, event-linked renewal and shorter segments in the
high-hazard region.
