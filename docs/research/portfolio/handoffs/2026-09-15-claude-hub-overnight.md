# Root handoff — Claude hub overnight run (2026-09-15 04:58 PDT)

Owner instruction 04:27 PDT: rest until 09:00 PDT; the hub runs the FSD fits
overnight and reports at the 09:00 cron check-in. Two directions driven: FSD and
ACVC. Nothing here changes lifecycle, priority or slots.

## FSD (flexible_skill_duration) — advancing

- Portfolio S decision applied; runner reviewed (Opus, accepted with corrections
  applied); eight D1280/I1280 fits running on `hmasd-wsl-node` at `dc4dbdfcd`
  (queues `fsd-bi-b01-772203/772303/772403`; `772503` follows the first to end).
- FLAT (4 fits) held under AGENTS §3 until the `k = 10` correction note reaches
  `portfolio:cross_direction`.
- Direction handoff: `docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-15_baseline_interruption.md`.

## ACVC — ACTIVE, waiting on the Portfolio key

- Direction decision `PRO_FINAL` (A, k = 1: one further C/M block, identities
  28431/38431); wrapper `scripts/run_acvc_cluster_mappo_comparison_b02.py`
  prepared and tested; zero new exposure.
- The one-block grant request cannot be sent: same registry blocker.
- Direction handoff: `docs/research/candidates/acvc/HANDOFF_2026-09-15_post_cm_decision.md`.

## Owner decisions needed (both directions)

1. **Transport registry**: `temp/sessions/hmasd-chatgpt-pro-transport/registry.json`
   keys `em:acvc:convergence` and `portfolio:cross_direction` rest at
   `DIRECTION_VERIFIED` because the Codex-side archive script fails on records
   that carry `direction_ids` without `direction_id`. Approve a manual registry
   reconciliation by the hub, or have Codex Root fix the script. Until then no
   Portfolio Send (FSD correction note, ACVC grant) is possible.
2. Optionally rule directly on the FLAT `k = 10` deviation (`OWNER_DIRECT`), which
   would release the four FLAT fits without the Portfolio round.

## Morning cron (09:00 PDT, job c6f503f6)

Tracker observation of the four queues, collection of finished fits, launch of
772503 if not yet launched, reduce when all eight D/I fits are complete, refresh
of both handoffs, owner report.

## Integration state

`main` carries every accepted `codex/fsd` and `codex/acvc` commit at writing
(latest cherry-picks: review corrections, intake addendum, launch record, FSD
handoff). Ledger rows in `docs/research/portfolio/audit/2026-09-15.md`.
