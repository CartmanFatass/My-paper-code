# Root handoff — Claude hub overnight run (2026-09-15, refreshed 09:05 PDT)

Owner instruction 04:27 PDT: rest until 09:00 PDT; the hub runs the FSD fits overnight and
reports at the 09:00 cron check-in. Two directions driven: FSD and ACVC. Owner 05:45 PDT:
the control-plane edit restriction is lifted (any file, if traceable in Git and documented
under `docs/Claude_docs/changes/`). Nothing here changes lifecycle, priority or slots.

## FSD (flexible_skill_duration) — advancing, 7 of 12 fits complete

- Portfolio S decision applied; runner reviewed and corrected at `dc4dbdfcd`; the FLAT
  `k = 10` deviation confirmed by `portfolio:cross_direction` at 12:55Z
  (`docs/research/portfolio/decisions/2026-09-15-fsd-flat-k-correction.md`).
- Complete and collected under `baseline_interruption_b01_20260915/fits/`: D1280 × 772203/
  772303/772403 (walls about 2,630 s), I1280 × the same seeds (6,353–6,550 s, peak RSS
  3.8 GiB), FLAT 772203 (2,023 s). Running since 16:01Z: 772303-FLAT, 772403-FLAT,
  772503-FLAT (about 16:40Z), 772503-D1280 (about 16:50Z), 772503-I1280 (about 17:50Z).
  One `agent-task` handle per element, `fsd-bi-b01-<seed>-<arm>`.
- Scheduling gap: the hub's session was rate-limited 13:30Z–15:40Z, so the node idled about
  two hours between the first wave finishing and the check-in. No scientific effect.
- Direction handoff: `docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-15_baseline_interruption.md`;
  launch facts in `baseline_interruption_b01_20260915/EXECUTION.md`.

## ACVC — one-block grant executing

- `em:acvc:convergence` selected A (k = 1); `portfolio:cross_direction` granted G at 13:19Z
  (`docs/research/portfolio/decisions/2026-09-15-acvc-one-block-replication-grant.md`, P1 item
  `20260915-acvc-002`). Launch source `codex/acvc 2dc9631c8`, on-policy `de66d7a4b` re-staged.
- C fit finished exit 0 (native wall 2,495.72 s) and is collected under
  `evidence/cluster_mappo_comparison_b02_20260915/native/C/`; M fit running since 16:01:41Z
  (pid 3736172, about 16:45Z). Then wrapper reduce, intake with the equal-block accumulation,
  Chinese brief, preservation, cleanup. The grant ends there.
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Transport and registry

- Both Pro rounds today (FSD correction, ACVC grant) went out with one Send and one tab each;
  both keys are `ARCHIVED`; only the protected `default` Agentify tab remains. The ACVC
  transport agent was cut off by the session rate limit after archiving; the hub verified
  the tab close, registry state and response digest itself (noted in the facts file).
- Still pending on the owner: the one-line `bind_conversation.py` fix (singular
  `direction_id`); the harness refused both the file tools and a Bash script. Apply by hand
  or remove the six deny rules in `.claude/settings.json`. It matters only for a first binding
  on a new key through the Claude route. Record:
  `docs/Claude_docs/changes/2026-09-15-control-plane-changes.md`.

## Next cron or session

Monitor the six running handles; collect each finished element; FSD `reduce` and intake once
all twelve summaries exist; ACVC reduce and intake once M is collected; refresh the three
handoffs; owner report. No further launches are authorized under either allocation.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing; the two
direction branches carry the direction-owned paths of each main commit (see `git log` for
`codex/fsd 593be0b50…` and `codex/acvc 0360df016…` onward). Ledger rows in
`docs/research/portfolio/audit/2026-09-15.md` (lines 14–24).
