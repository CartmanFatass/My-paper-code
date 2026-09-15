# FSD handoff — baseline × interruption B01 complete (2026-09-15, Claude hub)

**State: ACTIVE / HIGH, allocation complete, ACTIVE-idle pending one direction-tier
question.** All twelve S-allocation fits are complete, collected, reduced and intaken
([E0](FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md),
[intake](FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md),
[brief](../../portfolio/owner/briefs/flexible_skill_duration/2026-09-15_FSD_BASELINE_INTERRUPTION_B01.md)).
Driven by the Claude Code research hub (owner resume 2026-09-15; two directions, FSD and
ACVC). Authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`; the
hub commits on `main` and mirrors the direction-owned paths onto `codex/fsd`.

## Result in one paragraph

Primary SI1280_15 = I1280 − D1280 mean +.00983744 J (`small_signed`; blocks +.098 / +.045 /
−.083 / −.020), df = 3 interval [−.11564245, +.13531733] including zero and not inside ±.05.
The rollout-5/10 renewal advantage (about +.05 J) is not maintained at rollout 15 on the mean.
Untuned package gaps at rollout 15: GAP_D −.04526346 J [−.13491570, +.04438879], GAP_I
−.03542601 J [−.18359432, +.11274230]; arm means FLAT .4510, D1280 .4058, I1280 .4156. Six-
block rollout-5 accumulation +.04287702 J [−.02320115, +.10895519]. Both hub modal
predictions correct; owner slot not taken. Summed native wall 45,401.07 s.

## Object and authority

- Card §8 (applied S decision, FLAT `k = 10`, GAP labels, split reading, rollout-5
  accumulation) and §9 (result pointer). Portfolio packet and intake:
  `docs/research/portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/`;
  correction decision `docs/research/portfolio/decisions/2026-09-15-fsd-flat-k-correction.md`.
- Runner `scripts/run_fsd_baseline_interruption_b01.py` at `dc4dbdfcd`; execution record
  [baseline_interruption_b01_20260915/EXECUTION.md](baseline_interruption_b01_20260915/EXECUTION.md);
  twelve fit folders and `RESULT_SUMMARY.json` committed beside it.

## Producers

None. All twelve `agent-task` handles (`fsd-bi-b01-<seed>[-<arm>]`) finished with exit 0 and
were collected; the remote worktree and task records were reclaimed after verified
preservation (`baseline_interruption_b01_20260915/CLEANUP.json`; supervisor logs and runner
scripts under `task_records/`). Nothing of this object remains on the node.

## Open direction-tier question (prepared, not sent)

For `em:flexible_skill_duration:convergence` (intake decision 3): (A) conclude the
renewal-versus-flat family at this bounded claim, authentic D0 default, five-rollout optional
I1280 scope unchanged, ACTIVE-idle; (B) a tuned same-information flat baseline as the next
object (first §11.7 headroom record) before any further renewal work; (C) another tranche of
unchanged blocks (Portfolio investment). DM recommendation B over A; C not recommended. The
09:00 PDT check-in scoped the session to collection, intake and report, so the packet is not
yet authored; the owner may redirect before it goes out.

## Commits (main; direction-owned paths mirrored on codex/fsd)

`aff026fea` (twelfth fit), then the closure commit carrying E0, intake, RESULT_SUMMARY.json,
EXECUTION.md, DIRECTION.md, card §9 and this handoff (see `git log --oneline -3 -- docs/research/candidates/flexible_skill_duration`).
Earlier today: `dc4dbdfcd`, `ead3ab1bf`, `5b698cad6`, `7a34308e3`, `550ef2f0a`, `2ea0ed993`,
`8d7656917`, the correction intake/decision commit, `f3d920eba`.

## First resume step

Nothing to launch. If the owner has not redirected, author the direction-tier packet from
intake decision 3 (REQUEST.json under `pro_packets/20260915_post_baseline_interruption_convergence/`,
references at a main commit including the evidence spec), render, publish, bind and send
through `hmasd-pro-transport` on key `em:flexible_skill_duration:convergence`. Otherwise
remain ACTIVE-idle.
