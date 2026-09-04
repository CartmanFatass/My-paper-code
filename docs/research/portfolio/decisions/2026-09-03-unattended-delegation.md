# Owner decision — unattended running with delegated option selection (2026-09-03)

Recorded by Claude Code (Fable 5.1) from the owner's instruction at 13:58 PDT, 2026-09-03.

> **Current-status overlay (2026-09-04).** This record preserves the delegation as issued. Its
> item 3 concurrency cap was superseded by the owner's
> `2026-09-04-dm-max-and-unbounded-research-capacity.md` decision: the repository now has no fixed
> limit on concurrent implementer sessions or result-bearing runs. Runtime availability,
> dependency ownership, per-arm caps, and the fresh memory admission still apply. The other
> exclusions and audit requirements remain current through root `AGENTS.md` section 4.

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
3. At issuance, the two-direction concurrency cap (owner, 13:33 PDT) stayed in force. That cap is
   superseded as noted above; agents still commit early, launch runs detached, and use a recurring
   session wakeup to resume work interrupted by rate limits.
4. Decisions that change lifecycle, priority, fusion, separation, capacity or investment across
   directions remain reserved for the owner and are not selected under this delegation; the
   reviewer records the recommendation and holds.
5. Destructive or irreversible actions outside the ordinary research loop (history rewrites,
   deletions of evidence roots, changes to frozen scientific meaning) are not covered.

## Scope and revocation

Applies from 13:58 PDT 2026-09-03 until the owner says otherwise. Compliance note:
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`; review:
`docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`.
