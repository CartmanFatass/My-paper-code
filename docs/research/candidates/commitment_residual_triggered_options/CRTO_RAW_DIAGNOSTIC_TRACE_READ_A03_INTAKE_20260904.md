# CRTO A03 existing diagnostic trace intake

Date: `2026-09-04`. Object: `CRTO-RAW-DIAGNOSTIC-TRACE-READ-A03`.

Disposition: **accept `A03-DIAGNOSTIC-RAW-TRACE-MEASURED`**, `A/RECON` only: one recorded
diagnostic RAW path, not a residual comparison, stable effect, or relabeling of the original
incomplete A01 attempt.

## What this intake checked

I read the A03 card and explicit signed-score clarification against the unchanged native scoring
source and CM's exact-byte sign-predicate reproduction. Then I checked the same 303,260-byte
input, source/runtime/task provenance, fresh local read admission, every fixed population member
against the B01 card, predictor/RAW counts, information boundaries, threads, both anchors, and
all thirteen exposure lines. I recomputed all 208 rows' legality, oracle ties, action scores,
regrets and exact indicators, followed by every side count/mean, competence, R, D and tie break.

The E0 `CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_RESULT_EVIDENCE_20260904.md` records the card rule
verbatim, every check, counts, receipts, source and artifact identities, complete checkpoint and
exposure tables, and the compact durable result JSON. All recomputations agree within absolute
`1e-12`. Finite signed G16 values, including 689 repeated negative legal entries, are preserved.
All other A03 validity conditions pass; no information-boundary violation or unresolved reading
gap was found. The original A01 nonnegative-G16 condition and emitted INCOMPLETE flag remain
unchanged. A02 remains its declared technical normal-completion/no-fault result.

The corrected read took 0.00454420002643019 seconds after fresh local physical/effective
availability of 11,975,745,536 bytes. It added zero environment steps, learner updates, checkpoints,
or evaluations. Reading peak RSS is unavailable, so this valid non-resource result is marked
`resources_unmeasured`. Generation's 80.505860614001 runner seconds and 1,276,755,968-byte
peak RSS belong to A02 and are reused as provenance, not charged twice.

At the clean boundary owner reviews returned `[]`; today's review and CRTO ledger rows contain
no new instruction, and yesterday's review is absent. No owner prediction reply is present.

## Observation that bounds the result

Updates `252,255,258,261,264` all pass the unchanged two-sided competence predicate with KEEP
`6/8` and regret `0.003754710220270765`, REPLAN `6/8` and regret `0.0038081499511370583`.
These are exactly the phase-0 updates. The other eight checkpoints fail. However every equal-side
regret difference from fixed update 256 lies between `-0.0009494669522523771` and `0`, inside
the absolute `0.0025` MEI, and none improves on update 256. The descriptive best is 253, tied
with 256, and is not competent; these labels select no checkpoint.

The card's measured branch therefore applies under its explicit signed-native-score wording.
Its narrative criterion “or any competent nearby checkpoint” is met even though the aggregate
MEI is not exceeded. The accepted reading is phase-associated movement across a binary
two-sided competence threshold, with no material aggregate-regret gain.

The strongest support is five phase-0 competence passes under complete row, count and anchor
verification. The strongest contradiction to a practical improvement claim is that competent
checkpoints have slightly worse aggregate regret than the weak update-256 anchor. Phase-1 values
also change after update 256, so the full vector is not exactly periodic. No randomized order
intervention isolates cyclic order as the cause; one-seed/panel, predictor/numerical variation,
and the observed aggregate-versus-side tradeoff remain live explanations.

## Predictions and owner flags

- A03's DM prediction that no checkpoint would meet both competence conditions is contradicted.
  The expected phase association is descriptively supported. Owner: `not taken (unattended)`.
- The original failed A01 attempt's prediction is still unscored; it has not been relabeled.
- All EVAL checkpoints are exposed development information. No best or competent checkpoint is
  promoted to a held-out, independently tuned, or deployable comparator.
- No residual arm ran and no residual superiority or inferiority is inferred. B01's accepted
  `BR-E — COMPARATOR_WEAK` result remains unchanged at its own checkpoint.
- Headroom remains absent; these data are not a tuned reusable baseline with seeds and curves.
- R02's native fault remains unexplained. The toy E2E profile still lacks formal-constant
  publication coverage, though A02's real invocation reached publication. Neither issue changes
  this direct existing-artifact reading's ceiling.
- No code, runtime, tests, or engineering-scope machinery changed. No budget breach occurred.

## Decisions this intake produces

### Decision 1 — accept the bounded reading (object tier, technical)

Options: **(a)** accept A03 at its declared path-measurement ceiling, preserving signed-score
adaptation and diagnostic provenance; **(b)** discard the complete legal native data because
original A01 used a different sign restriction; **(c)** treat a passing nearby checkpoint as
an independently competent baseline or a residual-mechanism result.

Recommendation: **(a)**. The declared A03 checks pass and its native scoring domain is correct.
The explicit adaptation preserves both original records while permitting a bounded, reproducible
measurement without any new learner work.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Reversible if a reproduced
source/data defect is later found. There is no C consumption state, new family, Pro request,
promotion, recast, lifecycle, priority, or other Direction/Portfolio decision.

## Next discriminator and clean return

Recommend a later B/EXPLORE comparator readout specified over a complete three-update cycle,
with matched processed examples and transparent development exposure. It should test whether
the readout stabilizes two-sided competence without material native-regret loss. This recommendation
does not choose a checkpoint from these exposed rows and does not launch or freeze the later rung.

The bounded A03 observation and references are added to `DIRECTION.md`; Root owns Portfolio and
research-map integration. All remote tasks are terminal, their roots and original evidence are
preserved, and the complete existing-data reading is committed and pushed. No further process
observation or learner invocation is needed for this slice.
