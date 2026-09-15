# FSD baseline × interruption B01 — execution record

Object `FSD_BASELINE_INTERRUPTION_B01`, card
[FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md](../FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md)
§8 (Portfolio S decision applied). Twelve originals: arms FLAT, D1280, I1280 ×
training bases 772203, 772303, 772403, 772503 (evaluation bases 782203–782503).
Scientific source: `scripts/run_fsd_baseline_interruption_b01.py` at `db0b11bd8`
(byte-identical at every later `codex/fsd` commit until noted here). Launch sha,
handles and receipts are appended at launch.

## Exact command form

Each training block is one `agent-task` on `hmasd-wsl-node`:

```
agent-task run HANDLE /bin/bash <checkout>/docs/research/candidates/flexible_skill_duration/baseline_interruption_b01_20260915/commands/BLOCK.sh <checkout> SEED
```

[BLOCK.sh](commands/BLOCK.sh) runs the block's three arms in the order D1280,
I1280, FLAT as three queue elements; each element joins a fresh destination
`admit-memory` (≥ 4 GiB physical and effective) with the exact fit by `&&` under
GNU time, so no receipt admits a later fit. A failed element records its exit and
the queue continues; nothing is retried, replaced or extended. CPU FP32, Torch
intra-op 4 and OMP/MKL/OpenBLAS/NumExpr 4 are fixed. No `timeout` wrapper.

| Handle | SEED | Elements (in order) | Output root (relative to the checkout) |
| --- | ---: | --- | --- |
| fsd-bi-b01-772203 | 772203 | D1280, I1280, FLAT | `temp/directions/flexible_skill_duration/exp/baseline_interruption_b01_20260915/772203_<ARM>` |
| fsd-bi-b01-772303 | 772303 | D1280, I1280, FLAT | `…/772303_<ARM>` |
| fsd-bi-b01-772403 | 772403 | D1280, I1280, FLAT | `…/772403_<ARM>` |
| fsd-bi-b01-772503 | 772503 | D1280, I1280, FLAT | `…/772503_<ARM>` |

Concurrency plan: three block queues at once (peak about 10.5 GB RSS by the
completed factorial's per-fit peaks, 12 threads on 20 cores), the fourth when
the first finishes. Ordinary per-fit plans 1,800 / 4,000 / 1,600 s are
observations to compare with progress, not deadlines; contention may stretch
them. Reduce after all twelve summaries:

```
python scripts/run_fsd_baseline_interruption_b01.py reduce --summaries <12 summary.json> \
  --historical-factorial-summary docs/research/candidates/flexible_skill_duration/interruption_batch_b01_20260914/RESULT_SUMMARY.json \
  --output-root <reduce root>
```

## Launch conditions (evidence spec §11.4)

- Integrity: exact committed and pushed source; detached exact-sha worktree with
  `configs` and this evidence folder added to the sparse checkout; no
  uncommitted source on the node.
- Nonzero learner counts: established by the real tiny-host test
  (`test_real_tiny.py`, FLAT and D1280, 15 updates, three panels, actor/critic
  displacement > 0, FLAT coordinator/discriminators 0) and the synthetic suite.
- Resource admission: per element, on the node, immediately before the fit.
- Exposure line: S counts in the card §8 / PROSPECTIVE_COUNTS.json.
- Independent Opus review of the runner: recorded below before the first launch.

## Launch record

(appended at launch)

### 2026-09-15 pre-launch record

- Independent Opus review of `db0b11bd8`: **ACCEPT_WITH_CORRECTIONS** (M1a/b/c on
  the FLAT `k` justification and its deviation from the decision, M2 launch-sha
  comparability); all four applied in the commit that carries this record; the
  reviewer's own real-host probe found the D1280 training trajectory bit-identical
  with and without the three panels, and FLAT learning only actor/critic.
- **Arm split at launch:** D1280 and I1280 launch now as independent authorized
  work (`BLOCK.sh <checkout> SEED "D1280 I1280"`); the FLAT arm is dependent work
  under AGENTS §3 until the `k = 10` deviation note has been returned to
  `portfolio:cross_direction` (the shared Portfolio binding is presently stuck at
  `DIRECTION_VERIFIED` by a Codex-side archive-script defect; owner action
  requested). FLAT queues run later at the same source bytes with
  `BLOCK.sh <checkout> SEED FLAT`; block pairing is by fixed base seeds, so the
  order of arms within a block does not change the object.
- Concurrency: three block queues at once, the fourth when the first finishes.

### Launch record — D1280/I1280 arms (2026-09-15, launch sha `dc4dbdfcd`)

Source `scripts/run_fsd_baseline_interruption_b01.py` at `dc4dbdfcd`
(`dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`; review corrections applied, science
of the fit unchanged from `db0b11bd8` except the recorded FLAT comment). Node
`hmasd-wsl-node` (`wsl_4070`), detached worktree
`/home/wu/hmasd-worktrees/fsd-baseline-b01-dc4dbdfcd` (clean, exact sha verified
by each operator). Each queue launched by one `hmasd-experiment-operator` with
`BLOCK.sh <W> SEED "D1280 I1280"`; the D1280 `admit-memory` receipt of each
queue passed on the node (available ≥ 10.9 GiB at the first launch, ≈ 8 GiB with
three fits running). Output root
`<W>/temp/directions/flexible_skill_duration/exp/baseline_interruption_b01_20260915/`.

| Handle | Arms | Launch (UTC) | Remote pid | Remote log |
| --- | --- | --- | ---: | --- |
| fsd-bi-b01-772303 | D1280, I1280 | 2026-09-15T11:52:19Z | 3727157 | `~/.agent-tasks/fsd-bi-b01-772303/task.log` |
| fsd-bi-b01-772203 | D1280, I1280 | 2026-09-15T11:52:26Z | 3727295 | `~/.agent-tasks/fsd-bi-b01-772203/task.log` |
| fsd-bi-b01-772403 | D1280, I1280 | 2026-09-15T11:52:52Z | 3727655 | `~/.agent-tasks/fsd-bi-b01-772403/task.log` |
| fsd-bi-b01-772503 | D1280, I1280 | (launched when the first queue above ends) | | |

The `summary.json` present in a fit directory before its `whole_command_resources.json`
is non-empty is the runner's `setup` publication, not a result; a fit is complete only
when its summary carries `status: complete` and the queue jsonl records exit 0.
FLAT queues: not launched (dependent work, see the pre-launch record).
