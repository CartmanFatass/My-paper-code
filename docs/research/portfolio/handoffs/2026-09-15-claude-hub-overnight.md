# Root handoff — Claude hub overnight run (2026-09-15, refreshed 10:50 PDT)

Owner instruction 04:27 PDT: rest until 09:00 PDT; the hub runs the FSD fits overnight and
reports at the 09:00 cron check-in. Two directions driven: FSD and ACVC. Owner 05:45 PDT:
the control-plane edit restriction is lifted (any file, if traceable in Git and documented
under `docs/Claude_docs/changes/`). Nothing here changes lifecycle, priority or slots.

## FSD (flexible_skill_duration) — S allocation complete and intaken

- Twelve of twelve fits complete at `dc4dbdfcd`, collected under
  `docs/research/candidates/flexible_skill_duration/baseline_interruption_b01_20260915/fits/`,
  reduced (`RESULT_SUMMARY.json`) and intaken: SI1280_15 +.00983744 J `small_signed`, df = 3
  interval [−.11564245, +.13531733]; GAP_D_15 −.04526346 J and GAP_I_15 −.03542601 J (untuned
  package gaps, intervals include zero; FLAT not below the package); rollout-5 six-block
  accumulation +.04287702 J [−.02320115, +.10895519]. Both hub modal predictions correct.
  Summed native wall 45,401.07 s. E0, intake, Chinese brief, ledger row (line 27),
  DIRECTION.md, card §9, EXECUTION.md and the direction handoff are committed on `main` and
  mirrored on `codex/fsd`.
- No producer. Direction-tier question prepared in the intake (A conclude / B tuned
  same-information flat baseline, recommended / C more blocks) for
  `em:flexible_skill_duration:convergence`; not sent (check-in scope). Remote worktree and
  task records reclaimed after verified preservation (`CLEANUP.json`, `task_records/`).
- Direction handoff: `docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-15_baseline_interruption.md`.

## ACVC — family concluded, ACTIVE-idle

- Block 2 complete and intaken (D2 = F−M −.03919 J, M_ABOVE_MEI; F−C and F−own-dwell UP in
  both blocks; pooled F−M −.0079 J, df = 1 interval [−.406, +.390]). `em:acvc:convergence`
  selected A at 17:08Z (`PRO_FINAL`): the C/M family is concluded at its bounded two-block
  claim; reporting corrections applied; remote worktree and staging reclaimed (CLEANUP.json);
  checkpoints retained locally (PRESERVATION.json). ACTIVE/MEDIUM/recasts2 unchanged; no
  pending producer, request or transport effect. Reopening condition in the handoff.
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Transport and registry

- Three Pro rounds today (FSD correction, ACVC grant, ACVC post-block-2) went out with one
  Send and one tab each; all keys are `ARCHIVED`; only the protected `default` Agentify tab
  remains.
- Still pending on the owner: the one-line `bind_conversation.py` fix (singular
  `direction_id`); the harness refused both the file tools and a Bash script. Apply by hand
  or remove the six deny rules in `.claude/settings.json`. It matters only for a first binding
  on a new key through the Claude route. Record:
  `docs/Claude_docs/changes/2026-09-15-control-plane-changes.md`.

## Next session

No live handles. FSD: unless the owner redirects, author and send the direction-tier packet
from intake decision 3. ACVC:
ACTIVE-idle, nothing to do. No launches are authorized under either allocation.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing; the two
direction branches carry the direction-owned paths of each main commit. Ledger rows in
`docs/research/portfolio/audit/2026-09-15.md` (lines 14–27).
