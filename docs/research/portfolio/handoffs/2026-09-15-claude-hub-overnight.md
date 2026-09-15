# Root handoff — Claude hub overnight run (2026-09-15, refreshed 14:50 PDT)

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
- No producer. `em:flexible_skill_duration:convergence` answered the direction question at
  20:27Z with **A, `CLOSE_OBJECT`** (`PRO_FINAL`; packet
  `pro_packets/20260915_post_baseline_interruption_convergence/`, response `0712f85df`):
  stage closed at the bounded claim, no new object, B rejected, C/D not bought; three
  narrowing corrections applied. FSD ACTIVE-idle; reopening facts in the direction handoff.
  Remote worktree and task records reclaimed (`CLEANUP.json`, `task_records/`).
- Direction handoff: `docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-15_baseline_interruption.md`.

## ACVC — family concluded; M-deployment transfer result TRANSFERS on one instance, convergence review next

- Block 2 complete and intaken (D2 = F−M −.03919 J, M_ABOVE_MEI; F−C and F−own-dwell UP in
  both blocks; pooled F−M −.0079 J, df = 1 interval [−.406, +.390]). `em:acvc:convergence`
  selected A at 17:08Z (`PRO_FINAL`): the C/M family is concluded at its bounded two-block
  claim; reporting corrections applied; remote worktree and staging reclaimed (CLEANUP.json);
  checkpoints retained locally (PRESERVATION.json). ACTIVE/MEDIUM/recasts2 unchanged.
- Under the owner's 12:57 PDT scope instruction the hub derived the node's unlisted candidate
  into `ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md`; `em:acvc:convergence`
  selected it with corrections at 20:28Z (**B**, `PRO_FINAL`; packet
  `pro_packets/20260915_m_deployment_transfer_convergence/`, response `71a1ca5b7`). One
  fresh M fit with M / F(M) / own-dwell(M) panels.
- `portfolio:cross_direction` granted the one fit at 20:51Z (**G**, `PRO_FINAL / OWNER_DELEGATED`;
  decision `decisions/2026-09-15-acvc-m-deployment-transfer-grant.md`, packet intake
  `pro_packets/20260915_acvc_m_deployment_transfer_investment/INTAKE.md`, ledger row 30,
  owner item `20260915-acvc-005`). L0 at `codex/acvc fb7f859d9` reviewed by Opus (accept after
  fixes; one material: reduce mode bound identities too late), corrections `a741758a1`
  (main `deb0eb357`), eleven tests green, ledger row 31.
- Handle `acvc-transfer-m-b01-28531-a741758a` (launched 21:09:14Z) finished exit 0/0 in 985 s
  native wall; every count as granted; collected, reduced, preserved. **T_F +.018338 J TRANSFERS**
  (53/64), T_D +.00907 and U +.00927 WITHIN_MEI; DM Briers .54 / .635. E0
  `docs/research/candidates/acvc/ACVC_M_DEPLOYMENT_TRANSFER_B01_RESULT_EVIDENCE_20260915.md`,
  intake `..._INTAKE_20260915.md`, ledger row 32, Chinese brief filed. Grant consumed; the next
  object is a direction-tier question to `em:acvc:convergence` (DM recommends one further
  independent M instance). Remote worktree and staging reclaimed (CLEANUP.json).
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Transport and registry

- Six Pro rounds today (FSD correction, ACVC grant, ACVC post-block-2, FSD post-S
  convergence, ACVC transfer convergence, ACVC transfer investment), one accepted submission
  and one tab each; the two afternoon direction rounds ran concurrently on separate keys/tabs;
  the Portfolio round's registry record is ARCHIVED and its tab closed. Registry walks and tab closes for
  the afternoon rounds: see the transport facts under
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/{flexible_skill_duration,acvc}/`.
- Owner 12:57 PDT: deny rules removed, `bind_conversation.py` fix applied (`108f6b277`),
  scope instruction recorded in `CLAUDE.md`.

## Next session

No live handles. FSD: ACTIVE-idle, nothing to do. ACVC: the result review to
`em:acvc:convergence` (packet `pro_packets/20260915_m_deployment_transfer_result_review/`) is the
pending step: send it once if not yet sent, intake the archived answer as `PRO_FINAL`; a new fit
would need a Portfolio investment question first. No launch is authorized.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing; the two
direction branches carry the direction-owned paths of each main commit. Ledger rows in
`docs/research/portfolio/audit/2026-09-15.md` (lines 14–32).
