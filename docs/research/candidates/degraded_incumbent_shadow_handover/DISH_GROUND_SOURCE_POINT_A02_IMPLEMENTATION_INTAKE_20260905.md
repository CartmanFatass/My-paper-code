# A02 prelaunch scope return and bounded reduction

Date: 2026-09-05 PDT. DM `/root/dm_amx_n3_continue`; object tier, technical.

## Direct observation and decision boundary

CM accepted assembly `3168101b335e1ca4acee80204e152a897f2f1ebf` merges the A02 card
and A01 final intake into the accepted A01/B01 source. Its reused implementer wrote a
147-line runner and 79-line synthetic test in
`C:/Projects/HMASD-worktrees/impl-n3-dish-ground-a02-20260905`. No tests, native point,
models, scientific roots or result invocation had run when the draft was returned.

The independent reviewer names 52 nonblank orchestration lines in the 147-line runner:
imports 3–9 and 15–21; path bootstrap 11–13; run/admission 107–114;
Git/RSS/cap/metadata/publication 117–131; CLI 134–143; entry 146–147.
That is **52/147 = 35.37%**, above the conservative non-test 30% reading retained from
A01. The 79 test lines are not used to dilute this ratio. The draft was not accepted
as the price of a result. A fixed `--seed 11` CLI argument was also missing.
These are directly inspected code/scope facts, not a classified runtime failure.

## Decisions this intake produces

Options: (a) remove redundant startup/admission plumbing using existing module execution
and helpers, then independently recount; (b) enlarge the denominator with tests;
(c) accept the excess; (d) stop the diagnostic without attempting this bounded reduction.
Recommend/select **(a)**. It removes setup while retaining every declared measurement,
original input, precision/RNG boundary, single actual-node admission and publication.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Provenance `OWNER_DELEGATED`, reversible, owner flag `none`; the reviewer is followed.

The bounded reduction is:

- Launch as `python -m scripts.run_dish_ground_source_point_a02` from its recorded
  checkout, eliminating `sys` import and `sys.path` bootstrap. Derive `ROOT` from
  `__file__` for the Git query as before.
- Use ordinary study/backend module imports and qualified helper names, preserving the
  same functions and typed native fields. Do not compress unrelated statements or add
  blank/scientific lines to manipulate the ratio.
- Remove the second in-run admission JSON validator. The actual-node memory preflight
  remains mandatory immediately before the exact runner through `&&`; its receipt path
  remains in the summary. `scripts/AGENTS.md` specifies that this is the only admission.
- Add the runner's fixed seed argument with the only legal choice 11. Keep the original
  reset law and all carded quantities unchanged.

CM owns edits, independent scope/semantic review, exact-source committed/pushed focused
synthetic verification, and the one already carded result invocation. The draft's
projected reduction is not a measured final ratio; CM must return the actual line map.
No additional physics, height, clearance, source condition, host, policy or point is
authorized. No test executes the actual native point before its fresh admitted run.

## Owner boundary and audit

Current integration reviews were `[]` after Root's applied N3 ratification at
`d5a6a2568`. The audit owner column contains no differing N3 object instruction.
This wording is prospective and does not change frozen scientific meaning or create
another scientific launch gate. A02 remains unobserved while the reduction proceeds.

Root owns the shared audit ledger. Item `20260905-dish-006` was created with
`python -X utf8 tools/owner_console/item.py add`. Append under
`n3-ground-source-a02-implementation`.

| Time | Direction | Tier | Kind | Options | Chosen | Reversible | Provenance | Evidence | Owner flag | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T02:50:15-07:00 | degraded_incumbent_shadow_handover (N3) | object | technical | a remove redundant setup and recount; b test denominator; c accept excess; d stop without reduction | a | yes | OWNER_DELEGATED, 2026-09-03 instruction | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-006.json | none | |
