# FSD handoff — baseline × interruption B01 in flight (2026-09-15, Claude hub)

**State: ACTIVE / HIGH. Portfolio decision S applied (`PRO_FINAL / OWNER_DELEGATED`);
eight of twelve fits running on `hmasd-wsl-node`; four FLAT fits held as dependent
work.** Driven by the Claude Code research hub (owner resume 2026-09-15; two
directions, FSD and ACVC). Authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`,
branch `codex/fsd`; the hub cherry-picks accepted commits into `main`.

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

| Handle | Arms | Launched (UTC) | State at writing |
| --- | --- | --- | --- |
| fsd-bi-b01-772303 | D1280 → I1280 | 11:52:19Z | running (D1280) |
| fsd-bi-b01-772203 | D1280 → I1280 | 11:52:26Z | running (D1280) |
| fsd-bi-b01-772403 | D1280 → I1280 | 11:52:52Z | running (D1280) |
| fsd-bi-b01-772503 | D1280 → I1280 | when the first queue ends | not launched |

Status: `agent-task status <handle>` on the node; a per-fit `summary.json` is
complete only with `status: complete` plus exit 0 in `block_<seed>_queue.jsonl`
(the early `summary.json` is the runner's setup publication). Ordinary plans
1,800 s (D1280) and 4,000 s (I1280) per fit; three concurrent fits stretch them.

## Dependent work held (AGENTS §3)

The FLAT arm deviates from the decision's "switch-selected long k" (`k = 10`;
true reason: `config.k` is also the truncated-BPTT chunk length, card §8). The
correction note must be returned to `portfolio:cross_direction` before FLAT
launches, and that key is stuck at `DIRECTION_VERIFIED` because the Codex-side
`archive_delivered_claude_request.py` raises `KeyError: 'direction_id'` on
records carrying only `direction_ids`. **Owner decision needed**: approve a
manual registry reconciliation or a Codex-side script fix (or rule on the
deviation directly as `OWNER_DIRECT`). After the answer: `BLOCK.sh <W> SEED FLAT`
for the four seeds through `hmasd-experiment-operator`.

## Reduce

After the available summaries: `reduce --summaries <summary.json…>
--historical-factorial-summary docs/research/candidates/flexible_skill_duration/interruption_batch_b01_20260914/RESULT_SUMMARY.json
--output-root <reduce root>`. With FLAT missing, SI1280 and the rollout-5
accumulation are computable; GAP_D/GAP_I report `incomplete`. Do not intake GAP
readings from a partial factorial.

## Commits on codex/fsd (all integrated into main at writing)

`dc4dbdfcd` (review corrections, launch sha), `ead3ab1bf` (intake addendum),
`5b698cad6` (launch record), this handoff.

## First resume step

Run the status check; for each finished queue collect `summary.json`,
`whole_command_resources.json`, `admission.json` and the queue jsonl into the
evidence folder (`hmasd-experiment-tracker`); launch 772503 when the first
queue ends (operator, arms `"D1280 I1280"`); when all eight D/I fits are
complete run `reduce` and write the intake for SI1280 with GAP marked pending
FLAT.
