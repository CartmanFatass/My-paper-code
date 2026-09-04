# CRTO A03 signed-score correction intake

Date: `2026-09-04`. Class: `A/RECON`, object-tier card wording and technical evidence only.

The first A03 read passed input identity, 64-row membership, 48/16 split, counts, information
boundary, thread contract, initial scales, and reported update-256 anchor. It stopped before
phase metrics because the original runner reported thirteen illegal/nonfinite-row issues. The
0.004000599961727858-second stopped read is retained in the A03 temp root as `read_summary.json`;
its fresh local admission reported `12,174,131,200` physical/effective available bytes.

## What this intake checked

CM executed only the AST-extracted exact `trace_measurement_issues` function from source
`8d1c5978` against the unchanged 303,260-byte diagnostic summary. This reproduced all thirteen
recorded issues in 0.082 seconds after a fresh local admission of `12,029,145,088` available bytes.
The engineering evidence is `CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_SIGN_CHECK_EVIDENCE_20260904.md`.

Across all 208 recorded rows, counts of illegal selected actions, empty/mismatched legal vectors,
nonfinite legal G16, nonfinite or negative regret, and independent regret disagreement at absolute
tolerance `1e-12` are all zero. All 208 rows contain a negative legal G16; there are 689 repeated
negative legal scalar values. The first failing row at every checkpoint is
`0/EVALUATION/K8/850/156/0`, with legal scores KEEP `-0.21869770296967378`, TRANSIT-L
`-0.26169344944535616`, and TRANSIT-R `-0.20731001761413503`.

The sole failing conjunct is `value >= 0.0` applied to legal G16. The accepted native return law
subtracts costs, so finite negative scores are permitted. The reference `native_regret` computes
legal-oracle score minus selected score; its nonnegativity does not require nonnegative scores.
This classification follows direct reproduction over recorded bytes, not the broad error name.
No phase, competence, or residual comparison was interpreted by CM or DM at this boundary.

## Decisions this intake produces

Options: **(a)** clarify A03 to accept finite signed native G16 while requiring legal actions,
finite nonnegative recomputed regret, exact anchors/counts, and the unchanged information boundary;
**(b)** keep the inherited nonnegative-score restriction and leave the data unread; **(c)** alter
raw scores, thresholds, model, or learner execution to suppress the flag.

Recommendation: **(a)**. It matches the accepted scoring law without changing any measurement,
comparison, or threshold. Restricting the sign of the score would reject valid cost-bearing native
returns; changing data or rerunning would obscure the existing evidence.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This is the adaptive A03
card-wording/reading decision. It explicitly sets aside only the reproduced inherited sign
predicate and preserves the initial stopped A03 read, original A01 INCOMPLETE output, failed R02,
and A02 technical branch. There is no frozen C object or consumption state, no new family, no
source edit, and no new learner run.

## Owner flags and next discriminator

The initial A03 result is `READ-INCOMPLETE`, not a valid-result brief. Its stop is preserved and
the correction is prospectively recorded before metric reading. The DM prediction stays unchanged;
the owner prediction is `not taken (unattended)`. No new owner review instruction or ledger
override is present. No engineering-scope item or budget breach was introduced.

The next action is the corrected read of the same already completed artifact, under a fresh local
admission and the existing 30-second analysis bound. Recompute every recorded row and all fixed
checkpoint summaries, keeping finite negative scores visible. This carries no new learner
exposure and makes no Direction- or Portfolio-tier decision.
