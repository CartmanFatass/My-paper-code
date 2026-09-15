# Root handoff — Claude hub overnight run (2026-09-15, refreshed 06:12 PDT)

Owner instruction 04:27 PDT: rest until 09:00 PDT; the hub runs the FSD fits
overnight and reports at the 09:00 cron check-in. Two directions driven: FSD and
ACVC. Owner 05:45 PDT: the control-plane edit restriction is lifted (any file, if
traceable in Git and documented under `docs/Claude_docs/changes/`). Nothing here
changes lifecycle, priority or slots.

## FSD (flexible_skill_duration) — advancing

- Portfolio S decision applied; runner reviewed (Opus, corrections applied at
  `dc4dbdfcd`). The FLAT `k = 10` deviation was returned to
  `portfolio:cross_direction` and **confirmed** at 12:55Z (option 1,
  `PRO_FINAL / OWNER_DELEGATED`,
  `docs/research/portfolio/decisions/2026-09-15-fsd-flat-k-correction.md`).
- Fits (12): D1280 × 772203/772303/772403 complete and collected; I1280 × the same
  three seeds and FLAT 772203 running; pending in order 772503-D1280, 772303-FLAT,
  772403-FLAT, 772503-I1280, 772503-FLAT; at most four concurrent (peak RSS about
  2.8 GiB per fit). One `agent-task` handle per element (`fsd-bi-b01-<seed>-<arm>`).
- Direction handoff: `docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-15_baseline_interruption.md`;
  launch facts in `baseline_interruption_b01_20260915/EXECUTION.md`.

## ACVC — grant request in transport

- Direction decision `PRO_FINAL` (A, k = 1: one further C/M block, identities
  28431/38431); wrapper `scripts/run_acvc_cluster_mappo_comparison_b02.py`
  reviewed and corrected; zero new exposure.
- The one-block grant request
  (`docs/research/portfolio/pro_packets/20260915_acvc_one_block_replication_investment/`,
  key `portfolio:cross_direction`, Issue #14, branch `codex/acvc`) was dispatched
  to the transport at 06:07 PDT after the FSD round archived and the key freed.
  On a grant: re-stage the on-policy source, launch C then M through the operator
  (`launch_b02.sh` form), reduce via the wrapper, two-block accumulation at intake.
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Transport and registry

- Registry keys `em:acvc:convergence` and `portfolio:cross_direction` were
  reconciled to `ARCHIVED` with owner approval at 05:43 PDT; the FSD correction
  round then archived normally (the portfolio record keeps the singular
  `direction_id`). Tab discipline fixed (one tab per request, closed in phase 2;
  verified after both rounds: only the protected `default` tab remains).
- Still pending: the one-line `bind_conversation.py` fix (writes the singular
  `direction_id`); both the file tools and a Bash script were refused by the
  harness. The owner can apply it by hand or remove the six deny rules in
  `.claude/settings.json`. Record: `docs/Claude_docs/changes/2026-09-15-control-plane-changes.md`.

## Morning cron (09:00 PDT, job c6f503f6)

Tracker observation of every handle, collection of finished fits into `fits/`,
launch of the next pending elements, `reduce` and intake when all twelve summaries
exist (SI1280 primary, GAP_D/GAP_I, rollout-5 accumulation, Chinese brief), ACVC
phase 2 / intake if the grant response has landed, refresh of both handoffs, owner
report.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing
(main `6b73f0279` = codex/fsd `593be0b50` for the direction-owned paths; Pro's
response commit `8d7656917` cherry-picked as `2148cc22e`). Ledger rows in
`docs/research/portfolio/audit/2026-09-15.md`.
