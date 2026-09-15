# Intake — ACVC one-block replication investment (portfolio:cross_direction)

Request `2026-09-15-acvc-one-block-replication-investment-01` (task `84ba08ad0`, bound handoff
`5846a1dab`, base sha `d4317ddcf` on `codex/acvc`). Author DM: the Claude hub. Sent
2026-09-15 13:10Z, one Send, one tab. Response delivered by the ChatGPT GitHub connector at
`codex/acvc 2dc9631c8644464b8c4189a53344b2956c3eb3b4` ("Add ACVC one-block replication
Portfolio investment decision", 13:19:54Z): [`archive/RESPONSE.md`](archive/RESPONSE.md)
(blob `f56da8cf5e107eb679f34cf0344e478c5dfe6f07`, 9,995 bytes); Issue #14 delivery comment
recorded in the transport facts. Read from the immutable commit, not from the chat receipt.

## Question posed

Grant (G) or decline (N) the finite allocation the direction decision withheld: one further
unchanged C/M paired block (two original fits, master 28431 / evaluation namespace 38431,
plans C 1,800 s and M 1,600 s), plus bounded staging, verification, execution, intake and
preservation support.

## Formed decision

**G, `PRO_FINAL / OWNER_DELEGATED`.** Exactly one additional unchanged C/M block: two original
fresh fits and the bounded remaining support. ACVC stays ACTIVE/MEDIUM/recasts2 at the lowest
sequencing priority with optional-F status; the selected object and analysis are unchanged.

Points the response fixes, checked against the card, the direction decision and evidence
spec §11:

- Reason: recurrence, reversal or a small second contrast can change optional-F development
  advice; the block-1 facts (F−M +.0234 J above .01, C−M −.0113, 22/64 adverse worlds, worst
  −.2115, F−own-dwell +.0122 with 23 adverse) are not precise enough on their own. N was the
  strongest alternative; longer-budget and crossed alternatives stay unselected.
- Exact exposure: master 28431 / namespace 38431, one C-only fit and one M fit, inherited
  reset/action-stream partition, no transferred model/optimizer/buffer; each 4,096 H256
  training episodes, 2,048 two-episode rollouts, 8,192 PPO minibatches; private 108 actors,
  training-only critic 136, clustered 5-UAV/50-user host, native S and J = S/256, true
  termination, CPU FP32 single-thread, complete C/M recipes and the bounded-action adapter.
  F executes the C-trained proposer, not a trained arm. Totals: 2 fits, 2,162,688 team ticks,
  16,384 PPO minibatches, 24,576 optimizer steps, two final snapshots, four sole-final 64-world
  panels (C, F, own-dwell, M). No nested search, tuning or interim evaluation.
- Reading: D2 = mean64(J_F − J_M) alone first (> +.01 F_ABOVE_MEI; inclusive ±.01 WITHIN_MEI,
  not equivalence; < −.01 M_ABOVE_MEI); C−M, F−C, F−own-dwell supporting. Then D1 and D2
  individually, then the fixed equal-block accumulation:
  `pooled_mean = (D1 + D2)/2`, `block_SD = |D2 − D1|/√2`, `block_SE = block_SD/√2`,
  interval `pooled_mean ± 12.706 × block_SE` (df = 1), labelled an iid-normal complete-block
  working-model description; same accumulation separately for supporting contrasts. No
  pooling of 128 worlds as training samples, no precision weighting, no panel-noise adjustment,
  no older fixed-1024 C units; block 1 not rescored; invalid primary operands mean no
  imputation and no two-block primary aggregate.
- Sequencing: ready FSD work has first access; ACVC is lower-priority backfill, C then M,
  one original at a time, overlapping FSD only when actual CPU/memory leave room without
  displacing FSD's ready work; never interrupt an accepted original. The hub owns dispatch.
- Costs: C 1,800 s / M 1,600 s (3,400 s summed native) are adjustable ordinary plans, not
  caps; fresh ≥ 4 GiB admission joined by `&&` to each runner on the executing node; exact
  committed detached source; operator launch; truthful observation and terminal collection;
  the GNU timer starts after admission, so support is accounted separately.
- Reuse the reviewed wrapper and its three identity tests without another launch review;
  re-stage the unchanged on-policy dependency `de66d7a4b` from its preservation receipts
  before M; reduce through the block-2 wrapper; accumulation at intake with provenance;
  collection, intake/review and preservation within this grant. End after the two originals
  and required panels regardless of outcome; zero automatic replacements, retries, third
  fits or extensions; no peer/lifecycle change or Root ratification.

## Conformance check (AGENTS §2, §4.8)

No concrete conflict with owner instructions, the B01 card, the direction decision
(`em:acvc:convergence`, option A, k = 1) or evidence spec §11 (§11.4 launch conditions,
§11.8 burden, §11.11 accumulation). The response decides the bound investment question within
scope and is final for its node. The direction handoff's stale "Opus-review the wrapper"
resume line is superseded by the completed review, as the response notes.

## Application

- Launch source: `codex/acvc 2dc9631c8` (contains the reviewed wrapper bytes of `3ae041d9e`
  unchanged; `git diff 3ae041d9e 2dc9631c8` over the runner, wrapper, launch scripts and
  `hmasd/` is empty). Remote detached worktree `/home/wu/hmasd-worktrees/acvc-b02-2dc9631c8`.
- On-policy staging re-created at `/home/wu/hmasd-inputs/acvc-mappo-b02-28431/on-policy`
  from the preserved local archive (sha256 `0f151fea…cf19c`, 1,157,120 bytes); receipts in
  the block-2 evidence folder.
- Fits through `hmasd-experiment-operator`, `launch_b02.sh <sha> <output> <arm> <upstream>`
  with `HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python`, handles
  `acvc-mappo-c-b02-28431-2dc9631c` then `acvc-mappo-m-b02-28431-2dc9631c`; C first while the
  node's actual memory leaves ≥ 4 GiB beside the running FSD fits, M after C ends.
- Decision record: [`decisions/2026-09-15-acvc-one-block-replication-grant.md`](../../decisions/2026-09-15-acvc-one-block-replication-grant.md);
  ledger row in `docs/research/portfolio/audit/2026-09-15.md`; P1 `portfolio` owner item.
- Evidence folder for block 2:
  `docs/research/candidates/acvc/evidence/cluster_mappo_comparison_b02_20260915/`.
