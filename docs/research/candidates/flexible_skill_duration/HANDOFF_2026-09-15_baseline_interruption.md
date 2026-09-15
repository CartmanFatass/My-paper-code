# FSD handoff — baseline × interruption B01 in flight (2026-09-15, Claude hub)

**State: ACTIVE / HIGH. Portfolio decision S applied and the FLAT k = 10 correction
confirmed (`PRO_FINAL / OWNER_DELEGATED`, 12:55Z); 3 of 12 fits complete (D1280 ×
772203/772303/772403), 4 running (I1280 × 3, FLAT 772203), 5 pending.** Driven by the
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
| fsd-bi-b01-772203 / 772303 / 772403 | D1280 | 11:52Z | complete, collected under `fits/` |
| fsd-bi-b01-772203-I1280 | I1280 | 12:38:30Z | running |
| fsd-bi-b01-772303-I1280 | I1280 | 12:38:42Z | running |
| fsd-bi-b01-772403-I1280 | I1280 | 12:38:46Z | running |
| fsd-bi-b01-772203-FLAT | FLAT | 13:02:49Z | running |
| 772503-D1280, 772303-FLAT, 772403-FLAT, 772503-I1280, 772503-FLAT | | as slots free | pending, in that order |

At most four concurrent fits (measured peak RSS about 2.8 GiB per fit; the node has
15.8 GiB). Status: `agent-task status <handle>` on the node; a per-fit `summary.json`
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

Run the status check (Monitor or `hmasd-experiment-tracker`); collect every finished
fit's `summary.json`, `whole_command_resources.json`, `admission.json`, queue markers and
task log into `fits/<seed>_<arm>/`; launch the next pending element through
`hmasd-experiment-operator` whenever fewer than four fits run (order above); when all
twelve summaries exist run `reduce` and write the intake (SI1280 primary, GAP_D/GAP_I,
rollout-5 accumulation) with the Chinese brief.
