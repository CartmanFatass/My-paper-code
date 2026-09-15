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

### 2026-09-15 12:36Z — D1280 elements complete; I1280 elements never started (launch defect)

- All three queues exited 0 at about 12:36Z after their D1280 element only:
  772203 wall 2,642.05 s (user 10,250 s, RSS 2,826,100 KiB), 772303 2,637.78 s
  (RSS 2,881,412 KiB), 772403 2,617.32 s (RSS 2,867,548 KiB); each `summary.json`
  `status: complete`, three panels, `launch_sha dc4dbdfcd`. Under three-way
  contention the D1280 plan of 1,800 s stretched to about 2,640 s (about 3.9 cores
  per fit).
- **Defect (technical, no polarity, no retry budget consumed):** the supervisor's
  recorded command (`~/.agent-tasks/<handle>/runner.sh`) reads
  `BLOCK.sh <W> <seed> D1280 I1280`: the quoted arm list `"D1280 I1280"` was split by
  the nested `ssh … bash -lc '…'` quoting, so BLOCK.sh received `D1280` as its
  third argument and `I1280` as an ignored fourth. No I1280 process was ever
  created (queue jsonl has one line per block). The D1280 results are valid
  originals; the I1280 originals are launched now as single-token queue elements
  (`BLOCK.sh <W> <seed> I1280`, handles `fsd-bi-b01-<seed>-I1280`), same source
  bytes, same launch sha, same fixed seeds. Block 772503 will run as two
  single-arm elements as well. Lesson for the operator prompt: pass one arm per
  element; never rely on a quoted multi-token argument through `agent-task run`.
- I1280 relaunch record (single-arm elements, same worktree and sha):

  | Handle | Launch (UTC) | Remote pid |
  | --- | --- | ---: |
  | fsd-bi-b01-772203-I1280 | 2026-09-15T12:38:30Z | 3729226 |
  | fsd-bi-b01-772303-I1280 | 2026-09-15T12:38:42Z | 3729455 |
  | fsd-bi-b01-772403-I1280 | 2026-09-15T12:38:46Z | 3729527 |

  Each recorded `runner.sh` reads `BLOCK.sh <W> <seed> I1280` (single token). Block
  772503 (D1280 then I1280, one handle per arm) starts when the first I1280 ends.
- Collected D1280 evidence (summary, manifest, admission, resources, training rows,
  queue markers, task log; `learner_logs/`/`evaluation_logs/` were empty on the node)
  under [fits/](fits/): summary sha256 772203 `20cba726…c19f`, 772303 `a32d5465…1969`,
  772403 `2615b720…e47f`.

### 2026-09-15 13:02Z — FLAT arm released and launched (Portfolio correction confirmed)

- `portfolio:cross_direction` confirmed option 1 (FLAT at `k = 10`) at 12:55Z
  ([decision](../../../portfolio/decisions/2026-09-15-fsd-flat-k-correction.md),
  `PRO_FINAL / OWNER_DELEGATED`); the FLAT arm is independent work from that time.
  Same worktree and launch sha `dc4dbdfcd`; one queue element per block
  (`BLOCK.sh <W> <seed> FLAT`, single token), admission inside the supervised command.
- Concurrency: measured D1280 peak RSS is about 2.8 GiB per fit, so a fourth concurrent
  fit is admitted beside the three I1280 elements (available 6,027 MiB before launch,
  admission 5.86 GiB); the remaining elements follow as running fits end, at most four
  concurrent. This is a technical choice, not a scientific parameter.
- FLAT launch record:

  | Handle | Launch (UTC) | Remote pid | Admission |
  | --- | --- | ---: | --- |
  | fsd-bi-b01-772203-FLAT | 2026-09-15T13:02:49Z | 3731471 | passed, 6,287,306,752 B available |

  Pending elements in launch order: 772503-D1280, 772303-FLAT, 772403-FLAT, 772503-I1280,
  772503-FLAT (each `fsd-bi-b01-<seed>-<arm>`).

### 2026-09-15 16:01Z — remaining five elements launched together (morning check-in)

- The three I1280 elements and FLAT 772203 finished with exit 0 by about 14:15Z
  (walls: I1280 6,369 / 6,550 / 6,353 s at peak RSS about 3.8 GiB each under four-fit
  contention; FLAT 772203 2,023 s at 1.25 GiB). The hub's session was rate-limited from
  13:30Z to 15:40Z, so the node idled about two hours before the check-in; no scientific
  effect, recorded as a scheduling gap.
- With the node idle (14.9 GiB available) all five remaining elements were launched by
  five operators within one minute, one handle per element, plus the ACVC B02 M fit as
  single-thread backfill. Peak-RSS projection 2.8 + 3.8 + 3 × 1.25 + 0.56 ≈ 10.9 GiB;
  21 threads on 20 cores while the FLAT fits run (about 35 min), then 8 + 1.

  | Handle | Launch (UTC) | Remote pid | Admission (available bytes) |
  | --- | --- | ---: | --- |
  | fsd-bi-b01-772403-FLAT | 2026-09-15T16:01:14Z | 3735333 | passed, 15,613,427,712 |
  | fsd-bi-b01-772503-FLAT | 2026-09-15T16:01:15Z | 3735439 | passed, 15,424,118,784 |
  | fsd-bi-b01-772503-I1280 | 2026-09-15T16:01:31Z | 3735922 | passed, 13,899,333,632 |
  | fsd-bi-b01-772303-FLAT | 2026-09-15T16:01:40Z | 3736070 | passed, 13,265,879,040 |
  | fsd-bi-b01-772503-D1280 | 2026-09-15T16:02:04Z | 3736794 | passed, 12,005,937,152 |

  Every recorded `runner.sh` ends `BLOCK.sh <W> <seed> <arm>` (single token). Expected
  ends: FLAT about 16:40Z, D1280 about 16:50Z, I1280 about 17:50Z (critical path).

### 2026-09-15 17:26Z — all twelve elements complete; collected, reduced, intaken

- The five 16:01Z elements finished with exit 0: FLAT 772403/772503/772303 at about 16:44Z,
  D1280 772503 at 16:59Z (wall 3,428.12 s, RSS 2,846,552 KiB), I1280 772503 at 17:25:36Z
  (wall 5,045.10 s, RSS 3,877,192 KiB, pid 3735922). Each `summary.json` `status: complete`;
  every `block_<seed>_queue.jsonl` records exit 0 for its elements. Collected by
  `hmasd-experiment-tracker` into `fits/<seed>_<arm>/` (same file set as the first fits;
  `learner_logs/` and `evaluation_logs/` empty on the node; the runner writes no checkpoint).
- Summary sha256 of the committed `summary.json` blobs, equal to the node originals (first 8 /
  last 6 hex; Windows working copies of the three earliest D1280 folders differ only by CRLF
  checkout normalization):
  772203: FLAT `e9379731…01edf0`, D1280 `20cba726…c5c19f`, I1280 `76d8328c…e6dd66`
  772303: FLAT `e5c80b76…0cee35`, D1280 `a32d5465…8c1969`, I1280 `e544f7cf…2e1e5c`
  772403: FLAT `6745c5bb…4b4256`, D1280 `2615b720…53e47f`, I1280 `f8a5be98…308152`
  772503: FLAT `9b508235…af7ef2`, D1280 `dd799d35…56de9c`, I1280 `72eba4a6…0ff3c3`
- Whole-command walls and peak RSS (GNU time):

  | Fit | Wall s | RSS KiB | Fit | Wall s | RSS KiB | Fit | Wall s | RSS KiB |
  | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
  | 772203_FLAT | 2022.50 | 1,251,540 | 772203_D1280 | 2642.05 | 2,826,100 | 772203_I1280 | 6369.48 | 3,825,768 |
  | 772303_FLAT | 2589.24 | 1,234,008 | 772303_D1280 | 2637.78 | 2,881,412 | 772303_I1280 | 6550.17 | 3,817,448 |
  | 772403_FLAT | 2551.63 | 1,234,756 | 772403_D1280 | 2617.32 | 2,867,548 | 772403_I1280 | 6353.28 | 3,837,196 |
  | 772503_FLAT | 2594.40 | 1,249,204 | 772503_D1280 | 3428.12 | 2,846,552 | 772503_I1280 | 5045.10 | 3,877,192 |

  Sum 45,401.07 s (FLAT 9,757.77; D1280 11,325.27; I1280 24,318.03) against the serial plan of
  24,000–30,000 s; three to four fits ran concurrently with the ACVC block-2 fits.
- Reduce (control checkout, main `aff026fea`, `hmasd-amd-cpu` interpreter) with the completed
  factorial's `RESULT_SUMMARY.json`: `status: complete`; primary SI1280_15 +.00983744 J,
  `small_signed`, `interval_includes_zero`, interval [−.11564245, +.13531733]; GAP_D_15
  −.04526346, GAP_I_15 −.03542601; six-block rollout-5 accumulation +.04287702
  [−.02320115, +.10895519]. Output committed as [RESULT_SUMMARY.json](RESULT_SUMMARY.json);
  [E0](../FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md) and
  [intake](../FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md) written. The S allocation ends
  here; nothing further is launched under it.

### 2026-09-15 18:05Z — remote reclaim

All 88 committed fit files verified byte-identical (blob sha256) to the node originals and
the twelve supervisor `task.log`/`runner.sh` preserved as tracked text under
[task_records/](task_records/) (digests equal to the node copies); the runner writes no
checkpoint. The detached worktree `/home/wu/hmasd-worktrees/fsd-baseline-b01-dc4dbdfcd`
(clean at `dc4dbdfcd`) and the twelve `~/.agent-tasks/fsd-bi-b01-*` records were then
removed; worktree registrations 166 → 165 ([CLEANUP.json](CLEANUP.json)). Nothing of this
object remains on the node.
