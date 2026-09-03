# Owner decision — unattended running with delegated option selection (2026-09-03)

Recorded by Claude Code (Fable 5.1) from the owner's instruction at 13:58 PDT, 2026-09-03.

## The instruction

The reviewer keeps the research pipeline running without the owner present. At every point that
would previously have been put to the owner, the reviewer still lists the options and names the
recommended one, then selects the recommended option itself and records the selection as an
owner-delegated decision. Records must be complete enough that the owner can audit every
selection afterwards.

## How it is applied

1. Every intake keeps its "Decisions this intake produces" section with the options and the
   reviewer's recommendation, followed by the line
   `Owner-delegated decision (unattended, 2026-09-03 instruction): (x)`.
2. Predict-then-verify continues: the reviewer's prediction is recorded before each launch; the
   owner's prediction slot is marked `not taken (unattended)` rather than filled by the reviewer.
3. The two-direction concurrency cap (owner, 13:33 PDT) stays in force; agents commit early and
   launch runs detached; a recurring session wakeup resumes agents killed by rate limits.
4. Decisions that change lifecycle, priority, fusion, separation, capacity or investment across
   directions remain reserved for the owner and are not selected under this delegation; the
   reviewer records the recommendation and holds.
5. Destructive or irreversible actions outside the ordinary research loop (history rewrites,
   deletions of evidence roots, changes to frozen scientific meaning) are not covered.

## Scope and revocation

Applies from 13:58 PDT 2026-09-03 until the owner says otherwise. Compliance note:
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`; review:
`docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`.
