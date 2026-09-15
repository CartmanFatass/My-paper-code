# Root handoff — Claude hub overnight run (2026-09-15, refreshed 15:15 PDT)

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

## ACVC — transfer result reviewed (B02 selected); one-fit B02 investment question with Portfolio

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
- `em:acvc:convergence` reviewed the result at 21:57Z (**B**, `PRO_FINAL`; packet
  `pro_packets/20260915_m_deployment_transfer_result_review/`, response `1fb3d9e14`, one Send,
  COMPLETE, ARCHIVED, tab closed): one further independently initialised M fit,
  `ACVC_M_DEPLOYMENT_TRANSFER_B02` (28631/38631, same three panels, T_F,2 primary,
  per-instance display beside B01 with no pooled verdict, end after one); three narrative
  corrections applied to B01's E0/intake/DIRECTION; B02 card written; ledger row 33; owner
  item `20260915-acvc-006`; main `6d00be0e8`.
- One-fit B02 investment request sent to `portfolio:cross_direction` (packet
  `docs/research/portfolio/pro_packets/20260915_acvc_m_deployment_transfer_b02_investment/`,
  TASK `92c5957c7`, HANDOFF `4ebfad9df`, references at `74d49807b` / main `3580587ac`).
  Transport: one Send at 22:13:13Z (first call errored review_user_message_not_observed_after_click with persisted sendAttempted=true; the identical verifyExisting observation confirmed the single send, user message 721f8b05-4e0f-4a28-a556-d778056ebfc6, operation 5b50fcbb-a76b-4427-b9b4-02bb6fd65252), matched labels Latest / Pro, tab fee2561b-aa1e-43aa-905d-44dc1a80dd76 open for phase 2, prompt sha256 9ca41561260fdaa363fe5018dad2fe6fd13a7ced3fc4527d980c23fe5b1d9728; the registry binding's history lists the one-block replication round as its last request (the transfer-investment round has an archive folder but no history row), state ARCHIVED before this send.
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Transport and registry

- Eight Pro rounds today (FSD correction, ACVC grant, ACVC post-block-2, FSD post-S
  convergence, ACVC transfer convergence, ACVC transfer investment, ACVC transfer result
  review, ACVC B02 investment), one accepted submission and one tab each; the two afternoon direction rounds ran concurrently on separate keys/tabs;
  the Portfolio round's registry record is ARCHIVED and its tab closed. Registry walks and tab closes for
  the afternoon rounds: see the transport facts under
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/{flexible_skill_duration,acvc}/`.
- Owner 12:57 PDT: deny rules removed, `bind_conversation.py` fix applied (`108f6b277`),
  scope instruction recorded in `CLAUDE.md`.

## Next session

No live handles. FSD: ACTIVE-idle, nothing to do. ACVC: the one-fit B02 investment request to
`portfolio:cross_direction` (packet
`docs/research/portfolio/pro_packets/20260915_acvc_m_deployment_transfer_b02_investment/`) is
the pending step: GitHub readback of its response path, transport phase 2 (archive, registry
ARCHIVED, tab close), intake as `PRO_FINAL / OWNER_DELEGATED` with a decision record and a P1
`portfolio` item. If G2: B02 binding change and focused test, independent review, technical
acceptance, fresh admission, launch only through `hmasd-experiment-operator` (plan about
1,200 s). No launch is authorized before that.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing; the two
direction branches carry the direction-owned paths of each main commit. Ledger rows in
`docs/research/portfolio/audit/2026-09-15.md` (lines 14–32).
