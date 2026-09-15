# FSD handoff — baseline × interruption B01 in flight (2026-09-15, Claude hub)

**State: ACTIVE / HIGH. Portfolio decision S applied and the FLAT k = 10 correction
confirmed (`PRO_FINAL / OWNER_DELEGATED`, 12:55Z); 7 of 12 fits complete and collected
(D1280 × 3, I1280 × 3, FLAT 772203), the last 5 running since 16:01Z.** Driven by the
Claude Code research hub (owner resume 2026-09-15; two directions, FSD and ACVC).
Authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`; the hub
cherry-picks accepted commits into `main`.

## Object and authority

- Card: [FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md](FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md)
  §8 (applied S decision, FLAT `k = 10` deviation). Arms FLAT / D1280 / I1280 ×
  blocks 772203, 772303, 772403, 772503; 15 rollouts, panels 5/10/15; primary
  SI1280 at rollout 15, MEI .05 J; GAP_D, GAP_I; rollout-5 accumulation 4 + 2.
- Portfolio packet and intake: `docs/research/portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/`
  (response `5c6053f4a`, INTAKE.md with the correction map, review and launch addendum).
- Runner `scripts/run_fsd_baseline_interruption_b01.py`, tests under
  `tests/experiments/candidates/flexible_skill_duration/baseline_interruption_b01/`
  (16 synthetic + 2 real tiny-host, green at `dc4dbdfcd`). Independent Opus
  review: ACCEPT_WITH_CORRECTIONS, corrections applied at `dc4dbdfcd`.
- Execution record: [baseline_interruption_b01_20260915/EXECUTION.md](baseline_interruption_b01_20260915/EXECUTION.md).

## Live producers (launch sha `dc4dbdfcd`)

Worktree `/home/wu/hmasd-worktrees/fsd-baseline-b01-dc4dbdfcd`, output root
`<W>/temp/directions/flexible_skill_duration/exp/baseline_interruption_b01_20260915/`.
One queue element per handle (`BLOCK.sh <W> <seed> <arm>`, single-token arm; the
12:36Z quoting defect is recorded in `EXECUTION.md`).

| Handle | Arm | Launched (UTC) | State at writing |
| --- | --- | --- | --- |
| fsd-bi-b01-772203 / 772303 / 772403 | D1280 | 11:52Z | complete, collected (`fits/`), walls 2,617–2,642 s |
| fsd-bi-b01-7722/3/403-I1280 | I1280 | 12:38Z | complete, collected, walls 6,353–6,550 s, peak RSS 3.8 GiB |
| fsd-bi-b01-772203-FLAT | FLAT | 13:02:49Z | complete, collected, wall 2,023 s, peak RSS 1.25 GiB |
| fsd-bi-b01-772403-FLAT | FLAT | 16:01:14Z | running (pid 3735333), expected end about 16:40Z |
| fsd-bi-b01-772503-FLAT | FLAT | 16:01:15Z | running (pid 3735439), about 16:40Z |
| fsd-bi-b01-772503-I1280 | I1280 | 16:01:31Z | running (pid 3735922), about 17:50Z (critical path) |
| fsd-bi-b01-772303-FLAT | FLAT | 16:01:40Z | running (pid 3736070), about 16:40Z |
| fsd-bi-b01-772503-D1280 | D1280 | 16:02:04Z | running (pid 3736794), about 16:50Z |

The last five run together (projected peak RSS about 10.9 GiB with the ACVC M fit; the node
has 15.8 GiB); the node idled 14:15Z–16:01Z while the hub's session was rate-limited. Status: `agent-task status <handle>` on the node; a per-fit `summary.json`
is complete only with `status: complete` plus exit 0 in `block_<seed>_queue.jsonl`
(the early `summary.json` is the runner's setup publication). Ordinary plans 1,800 s
(D1280, observed about 2,640 s with three concurrent), 4,000 s (I1280), 1,200–1,600 s
(FLAT, unmeasured).

## FLAT correction (closed)

The k = 10 deviation was returned to `portfolio:cross_direction` and confirmed as
option 1 ([decision](../../portfolio/decisions/2026-09-15-fsd-flat-k-correction.md),
[intake](../../portfolio/pro_packets/20260915_fsd_flat_k_correction/INTAKE.md)). GAP_D
and GAP_I are untuned package gaps, never headroom. The registry key was archived by the
transport after the round; the Claude-side bind script still lacks the singular
`direction_id` write (fix pending in `docs/Claude_docs/changes/2026-09-15-control-plane-changes.md`),
but the portfolio record now carries the field, so later rounds on that key archive
normally.

## Reduce

After the available summaries: `reduce --summaries <summary.json…>
--historical-factorial-summary docs/research/candidates/flexible_skill_duration/interruption_batch_b01_20260914/RESULT_SUMMARY.json
--output-root <reduce root>`. With FLAT missing, SI1280 and the rollout-5
accumulation are computable; GAP_D/GAP_I report `incomplete`. Do not intake GAP
readings from a partial factorial; with all twelve summaries the intake reports SI1280
(importance and uncertainty separately) and both GAPs.

## Commits on codex/fsd (all integrated into main at writing)

`dc4dbdfcd` (review corrections, launch sha), `ead3ab1bf` (intake addendum),
`5b698cad6` (launch record), `7a34308e3` (handoff), `550ef2f0a` (correction request
bound), `2ea0ed993` (D1280 evidence, I1280 relaunch), `8d76569178` (Pro's correction
response), then the correction intake/decision/launch-record commit (see `git log`).

## First resume step

Monitor the five running handles (`agent-task status`); collect each finished element into
`fits/<seed>_<arm>/` (same file set as the existing folders, plus the refreshed
`block_772503_queue.jsonl`). When all twelve summaries exist run `reduce` with the historical
factorial summary and write the intake (SI1280 primary with importance and uncertainty read
separately, GAP_D/GAP_I as untuned package gaps, rollout-5 accumulation 4 + 2), the Chinese
brief, the ledger row, then integrate to `main`. No further launches are authorized under
the S allocation after these five.
