# RCLE TBCFV A02 — CM implementation and launch record

Contract: [frozen card](RCLE_TBCFV_A02_FROZEN_SCORE_ALLOCATION_SCIENCE_CARD_20260906.md)
§§2–6, DM freeze `25d6aff6a`. Source base `4572ab1a7727c8d1098e5c52ac8a9bb7a8a3ff4c`;
CM branch `codex/cm-rcle-a02-20260906`, worktree
`C:/Projects/HMASD-worktrees/cm-rcle-a02-20260906`. The primary checkout's unrelated
Portfolio/handoff changes were preserved. No result invocation has occurred at this revision.

## Delivered implementation

- `experiments/candidates/roster_consistent_latent_exploration/tbcfv_a02/study.py`:
  four single-constructed models; original seed18 initialization law; loaded final states;
  frozen baseline reconstruction; actual manager/actor/original-joint loss derivatives and
  same-graph zero-baseline derivatives; all five named tensor groups; direct tensor differences;
  256 raw fixed inputs and three conditional probability panels.
- `scripts/run_rcle_tbcfv_a02.py`: CPU single-thread environment set before torch import;
  one POSIX result invocation with a wall alarm covering imports/build/loading/publication.
- `empirical_runner.py`: optional read-only pre-claim observer and optional
  `SemanticRNG.arm_only_domain=None`. The original default is unchanged. A02 replaces only
  nonempty `arm_only_variable` addresses with `post-b02-frozen-probe` in the batched uniform
  path used by FLEX noise. Shared empty address fields remain empty. No five-arm factory,
  learner step, baseline update, sampler replacement, environment copy, or new native backend.

State ownership remains native batch/snapshot -> existing per-lane plan and score graphs ->
the two separate episode-score means -> stopped advantage -> autograd. Input capture occurs
after event handling and before the original claim draw; it clones detached raw features and
the actual member latent, and neither samples nor changes the live graph. The conditionally
recomputed probability library reruns both encoders and the pointer at fixed latent/input.

Population SD (`correction=0`) and local additivity tolerance
`1e-10 + 1e-8*(norm(g_M)+norm(g_A))` match the card. Zero denominator ratios remain null.
No graph and numerical-zero tensor gradients are distinct. Progress counts are completed
operations; derivative attempts are also counted before each call. A stopped in-flight batch/derivative/vector is explicitly labelled as potentially
partial rather than charged as zero work. Captured inputs are retained at completed C1P1 blocks
and on a caught stop. Complete conditional snapshot panels are retained separately from counts
of probability vectors completed inside an interrupted panel. Summary publication uses a
sibling temporary file and replace so an interrupted write leaves the preceding summary intact.

## Actual saved-input facts

Execution-node origin:
`/home/wu/hmasd-worktrees/rcle-b02-8ad01cb/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b02_20260906`.
Both final `parameters.pt` files loaded read-only with `weights_only=True`: 30 named tensors each.

| File | SHA256 |
| --- | --- |
| `c1p1/parameters.pt` | `3c277fee5ec01adbdd259bc809126bd6eaaa85affbe7b716425d2da14895d13e` |
| `flex/parameters.pt` | `66d23ae708edbf6ab02003400bdd961451b81dc6f68b6c0e55118b1478e490f0` |

B02 saved no initial tensor or baseline buffer. Rebuild theta0 from the same seed18 key and
original affine addresses; compare its norm to retained `21.205717682888885`. Final baselines
use each arm's retained 200 ordered per-cell Y means, FP64 recurrence with original
`BASELINE_DECAY` and expression `(1.0 - BASELINE_DECAY)`. Curve means were JSON full-precision
Python floats from `math.fsum/len`; the original learner used `torch.mean`. This is a documented
reduction-order limitation, not recovered buffer bits. Missing/insufficient curves invoke the
card's explicitly labelled baseline-unavailable fallback, with zero-baseline gradients only.

Seed root: `fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093`.
Derived probe blocks under `post-b02-frozen-probe`:

- 19001: `7a7d963c9119a497d04cd8a423fdb41784ceceb32bbd2e898526fd074da7f8ba`
- 19002: `e92ec9e8d13ff494c1bc663696eb589d989bc671f765c00a66b167c7c3285268`

## Focused acceptance and independent review

Local interpreter `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

1. `-m pytest -q -p no:cacheprovider --basetemp
   C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/a02_cm_20260906
   tests/experiments/candidates/roster_consistent_latent_exploration/tbcfv_a02`:
   **5 passed in 9.70 s**. Synthetic conformance source only, no seed18 model or card probes.
   This exercises 16 non-card native episodes, 11 derivative evaluations (eight on actual host
   score graphs, three on synthetic fallback rows), zero optimizer steps. Native C1P1/FLEX
   forward returns agree at the fixture's zero final heads, while FLEX actor derivatives reach
   its final heads and retain zero gradients in the connected preceding layers. It checks
   loss additivity, both baseline branches, complete parameter-group coverage, raw input capture,
   changed pointer probabilities, summary and tensor-output readback, and RNG mapping/defaults.
2. After partial-stop repair, selected `::test_partial_derivative_counts` and
   `::test_missing_baseline_is_explicit`: **2 passed in 2.14 s**, complete process stopwatch
   **3.0002317 s**. Zero episodes, five completed synthetic derivatives; a synthetic third-call
   interruption before execution is labelled in-flight. This verifies the repaired partial
   derivative accounting without repeating the native smoke.

The only pytest warning is the existing `cache_dir` configuration option while its plugin is
disabled. No new issue follows. `git diff --check` passed. These checks establish the measured
path and publication behavior, not scientific truth or historical cross-host bit equivalence.

Independent reviewer `rev_ah_rcle_a02` inspected the actual diff against card §§2–6. It found no
material core gradient, RNG, stopped-graph, host or fixed-input semantic issue. Its publication
findings (metadata, partial counts/raw inputs, interrupted final summary write, timing scope)
were repaired as described above. The reviewer ran no compute or experiment. Final focused
repair disposition: **no material findings remain**. The DM also requested the explicit
attempted/completed derivative counters above; across the two focused checks there were
17 derivative attempts, 16 completed evaluations, and one synthetic pre-execution interruption.

## Scope and cost

Engineering scope §4 additions: **none**. Existing resource preflight and detached supervisor
are reused. Scientific output tables and ordinary partial-result publication are card-required
measurements, not a registry, telemetry service, provenance guard, retry mechanism or scheduler.
Source delta: **410 added / 1 deleted** non-test lines (including the new package initializer);
runner **64 lines**; focused tests **135 lines**. The implementation stays within 2,000/600.
No line-by-line orchestration census is required for ordinary research (§11.8).

Per-configuration cost law: two 64-episode blocks, 8,192 ticks per configuration;
six derivatives for each initialization configuration, ten for each final configuration;
library work is 256 points x three snapshots. Summed result exposure is 512 episodes,
32,768 ticks, at most 32 derivatives, 768 vectors, no learning updates. Dominant time terms are
native rollouts/model graphs, repeated retained-graph derivatives and startup/native build.
B02's complete 152.6 s is contextual evidence; neither isolated panel nor A02 derivative cost
was measured. Per-configuration machine-time predictions remain **unknown**, not zero or a
claimed 30 s. No calibration probe was run and no known over-cap arm was dropped.

DM conservatively debits the known supporting focused-check wall, **12.7002317 s**, against
the 300 s spend. Proposed single result process external timeout **287 s**, internal alarm
**285 s** reserves publication, leaving **0.2997683 s** unallocated. Scientific counts remain
unchanged. Technical exposure is separate from result denominators. Source-reading/ordinary
Git/SSH activity is not result machine time. No extra build invocation precedes the result:
imports, any required source-keyed native build, loading, initialization reconstruction,
all graphs, probability/statistical calculations and output writes are inside the process cap.
GNU `time -v` supplies complete process wall/RSS and available cumulative CPU. Summary wall is
explicitly labelled through measurement/intermediate publication, excluding final summary write.
For this one process, result critical path and result invocation wall are the same; supporting
checks are additionally charged once. Aggregate CPU is reported only to the tool's actual scope.

## Proposed exact launch shape (integration SHA to be bound before execution)

Node `wsl_4070`, CPU FP64 one compute thread; no node switch or retry. Supervisor name
`rcle-a02-20260906`. Root must first integrate accepted source and send the exact pushed SHA.
Create `/home/wu/hmasd-worktrees/rcle-a02-<SHA7>` detached at that SHA. Cwd is this worktree;
output root is its `temp/directions/roster_consistent_latent_exploration/exp/tbcfv_a02_20260906`.
Use both state-root and summary-root at the retained B02 origin above; no input/source staging.

The supervisor command is the following single command, with concrete absolute paths and SHA
filled before acceptance:

```text
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <OUT>/memory.json &&
/usr/bin/time -v -o <OUT>/complete.time /usr/bin/timeout --signal=TERM --kill-after=2s 287s
/home/wu/.venvs/hmasd/bin/python scripts/run_rcle_tbcfv_a02.py
--out <OUT> --state-root <B02_ORIGIN> --summary-root <B02_ORIGIN>
--launch-sha <SHA> --admission-receipt <OUT>/memory.json --seed 18 --wall-cap 285
```

The preflight runs on the execution node immediately before the runner via `&&` in the same
configured `agent-task` command. Require measured physical and effective available memory
at least 4 GiB. One accepted handle only: inspect uncertain acceptance, never relaunch.
At timeout/failure retain the result root and report dependent limitations; no automatic retry.
CM observes until configured independent Monitor ACK, then retains collection/technical acceptance.
Monitor handoff goes directly through the app to `01a0791b-0d2d-7b43-85b6-cd5632e0b007`, return
through research Root `01a07249-b095-7821-8ce2-e9c32ba85267` to DM/CM. Scientific intake remains DM's.

scope: none
