# FSD E3 medium D0 seed 3 — DM intake and safe execution drain

Intake date: 2026-09-04. Direction: `flexible_skill_duration`. Tier: **object**.
Result evidence: `FSD_E3_MEDIUM_D0_SEED3_RESULT_EVIDENCE_20260904.md`.

## Disposition

**Accept `medium_d0_seed3` attempt 01 as one valid complete B/EXPLORE cell.** E3 now has
11 valid cells, zero running and seven never-launched cells. One historical medium-D0-seed-1
attempt remains quarantined. E3 is incomplete; no aggregate result branch or C consumption
state exists at this boundary.

The owner has requested completion of the current round followed by a safe stop for a later
Root/config restart. Accordingly, the current result is taken in and the direction stops before
`medium_d2_seed3`. This is an execution drain, not a lifecycle, priority, family or card change.

## What I checked

1. **Card and result.** I checked the unchanged E3 question, B ceiling, frozen medium D0/seed-3
   assignment, CPU/four-thread semantics, budget, stop rule and required observables against
   CM's terminal receipt and the verified original summary. CM commit
   `570670403f48ba0f2a3d64e6f47799a8354128d2` retains exact launch provenance and all ten
   transfer hashes. Original launch SHA is `9c0a990537a8ffef58306429a1ff402550fc4b82`.
2. **Actual work.** The summary reports 20/20 rollouts, 128,000 transitions, 320 training
   episodes, 3,584 evaluations and 148,500 optimizer steps across five positively updated
   groups. CM checked each learner/path stream, both regions, all four per-episode evaluation
   inputs, finite learner values, checkpoint state and completed E3 publication. First/final
   exposure is present for every trained network; minimum final displacement ratio is
   `0.03807650598342086`.
3. **Admission and artifacts.** The immediate remote preflight passed both 4 GiB floors with
   `15,429,533,696` bytes each. Ten remote/staged/canonical artifact hashes agree. The original
   remote root and every older valid or quarantined root remain unchanged. The canonical new
   cell was created only after verifying its absence.
4. **Direct arithmetic.** From 2,048 finite ordered final episode returns I recomputed mean
   `0.40684948730468623`, sample-based episode standard error `0.00022530152199174783`,
   and D0/reference ratio `0.9590508796903731`. They match publication to floating-point
   rounding. This seed meets the card's descriptive `0.85` competence line. I did not compute
   a D2-D0 comparison, a paired gain or a row-shape comparison.
5. **Native path.** Both regions have mean/decile segment length 5 and zero gap-caused renewals,
   as expected for the infinite-cost fixed-clock arm. Gap-renewal precision is undefined
   because its denominator is zero; the two-region path is complete. This is not an
   instrumentation defect or a D2 event-path observation.
6. **Costs and engineering limits.** Runner wall `2687.7446834669972 s` and supervisor interval
   `2773 s` are separately recorded, both below the projected 1.68 hours and 8-hour cap.
   Missing RSS is `resources_unmeasured`; it does not invalidate this non-resource claim.
   No source edit, new machinery, repeated suite, new publication defect or engineering-scope
   budget breach occurred. Readable checkpoint evidence is not a resume-equivalence claim.
7. **Rule applied verbatim.** “Do not apply the frozen E3 result rule until all 18 required
   invocations are validly complete.” Only 11 are valid. The five unchanged card branches
   are reproduced in the result evidence but none is selected. Unlaunched large-row cells are
   not counted as failed comparators, and the missing paired D2 value is not zero.
8. **Owner surfaces.** The primary and Root-integration `item.py reviews --json` commands
   returned no unapplied instructions. Today's actual review contains only the already-seen
   Root Portfolio item; yesterday's file is absent. The FSD owner columns in the actual
   Root-integration audit are empty. No E3 owner prediction or contrary instruction was found.
   The owner's present drain instruction came directly through Root and is applied here.

## Observation that bounds the result

This medium-row, seed-3 fixed clock is a valid, competent comparator observation under the
declared budget. It adds no evidence that D2's policy gap responds usefully to regional events.
The paired treatment has not run, and the mechanism rule reads the three large-row pairs, all
of which remain uncreated. Episode uncertainty does not establish seed stability.

Strongest new support is comparator readiness: complete exposure and 95.9% of its exact fixed-
clock reference at the final checkpoint. The strongest existing contradiction to an event-driven
D2 advantage remains E2's `NEITHER`, weak event alignment and seed dependence. The surviving
alternative remains that heterogeneous hazards create useful local renewal opportunities, with
noisy policy gaps and team renewal as competing explanations. Accepted mechanism-level science
in `DIRECTION.md` is unchanged.

DM prediction `E3-H0-NO-ADVANTAGE` remains **unscored pending the full E3 study**. Owner E3
prediction is **not taken (unattended)**. No E2 prediction is reused as an E3 prediction.

## Flags for the owner

- This is one valid comparator cell, not a completed E3 study or a treatment advantage.
- RSS/peak scratch remain unmeasured; measured wall and artifact payload are preserved separately.
- The valid cell adds `2687.7446834669972 s` of measured runner machine usage. No extra learner,
  evaluation, tuning or admission was used for intake.
- Seven cells remain uncreated. No next cell will start until the later explicit resume.
- There is no close call, critic dissent, recast, Portfolio recommendation or lifecycle action.

## Decisions this intake produces

### Decision 1 — disposition of the completed cell

Options:

- **(a)** Accept this complete cell and update E3 to 11/18, retaining the full-study reading rule
  and preserving all original evidence.
- **(b)** Leave the cell unaccepted until the full matrix exists, despite its complete required
  outputs and the distinction between cell validity and aggregate interpretation.

Recommendation: **(a)**. All required measurements are present, the receipt and transfer checks
pass, and no learner instrumentation defect was found. Deferring cell validity would conflate
technical acceptance with the scientific aggregate rule.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Provenance: `OWNER_DELEGATED`; kind: `technical`; owner flag: `none`; reversible: yes.

### Owner-direct execution boundary

Execute the owner's requested safe end-of-round drain: retain the completed cell and stop before
the next E3 cell. Provenance: `OWNER_DIRECT`. The recommendation is to preserve exactly that
boundary for restart. Launching `medium_d2_seed3` now is outside the present instruction.
This introduces no direction-tier park decision and no change to the frozen object.

The valid-result Chinese brief and the technical decision are written to the owner surfaces
through `tools/owner_console/item.py`. Their audit rows are returned to Root under
`docs/research/portfolio/audit/2026-09-04.md#fsd-e3-seed3-terminal-20260904`.

Decision item: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-003.json`.
Brief item: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-004.json`.
Chinese brief:
`docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-04_E3_medium_d0_seed3.md`.

Audit rows for Root integration:

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T22:44:05Z | `flexible_skill_duration` | object | technical | (a) accept the complete cell and retain the aggregate rule; (b) defer cell validity until the full matrix | (a) valid `medium_d0_seed3`; E3 11/18, no aggregate branch | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-003.json` | none | |
| 2026-09-04T22:44:05Z | `flexible_skill_duration` | object | selection | owner instruction: finish current round and stop before the next cell | complete current intake; hold before uncreated `medium_d2_seed3` for later restart | yes | `OWNER_DIRECT` — execution drain only | `docs/research/candidates/flexible_skill_duration/FSD_E3_MEDIUM_D0_SEED3_INTAKE_20260904.md` | none | |
| 2026-09-04T22:44:05Z | `flexible_skill_duration` | object | technical | reading-agreed; reading-disputed | publish the valid-cell brief; no owner reading auto-applied | yes | `VALID_RESULT_INTAKE` | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-fsd-004.json` | none | |

## Exact recovery boundary

Terminal handle: `wsl_4070` / `fsd_e3_medium_d0_seed3_20260904_01`, finished at
`2026-09-04T22:26:00Z`, exit 0, tmux inactive. The original detached worktree is
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01`, at launch SHA
`9c0a990537a8ffef58306429a1ff402550fc4b82`. Full source, command, receipt, remote, staging
and canonical local evidence locators are preserved in the CM record and result evidence.

Next cell after a later resume is exactly `medium_d2_seed3` (seed 3, medium row, `c=0.25`,
individual cap 40, team cap 400, CPU/four threads, unchanged 20-rollout budget and evaluation).
Its conservative per-cell projection stays 4.63 hours against an 8-hour cap. The remaining
sequence then contains the six large-row D0/D2 cells for seeds 1, 2 and 3. Each future invocation
needs its own fresh remote admission immediately before the exact committed/pushed runner.

No task, preflight, learner or scientific root for a successor was created by this closeout.
Do not resume the completed checkpoint or the historical quarantine, and do not re-run the
completed cell. After all 18 cells are valid, the next discriminator remains the frozen paired
return and regional event-path reading at the large row. No Pro round is needed for this drain.
