# VSP03 B01 — complete three-pair B evidence

All three independent training pairs have **T=G=F at the fixed update-128 primary endpoint**.
Earlier initialization differences survive in the record. This is finite-budget, single-controller
termination exploration on one N1 task; no stable superiority or MARL-specific result follows.

## E0 scope and original reading rule

The original `VSP03_B01_SCIENCE_CARD_20260905.md` selected seed 1. The prospective
`VSP03_B01_SEEDS23_FOLLOWUP_20260905.md` selected seeds 2 and 3 after seed 1, before either
new outcome. All settings and endpoints were retained. No seed 4, extra updates or favourable
checkpoint substitution occurred. A B object has no consumption state.

The applicable card rules, verbatim, are:

> Equality or G>T weakens this prior on this task/budget.

> Intermediate-only gains remain local.

Apply the first sentence to the primary endpoint and preserve the earlier observations under
the second. The main differences all fall inside the card's descriptive 0.02 MEI. That fact is
not a population equivalence test. No result is invalidated because it is zero.

## All selected outcomes

| Seed | Update | T mean return | G mean return | T-G | Conditional episode SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 32 | 0.365390625 | -0.2 | 0.565390625 | 0.0446985064 |
| 1 | 64 | 0.3671875 | -0.2 | 0.5671875 | 0.0444654573 |
| 1 | 128 | 0.3755859375 | 0.3755859375 | 0 | 0 |
| 2 | 32 | 0.26453125 | -0.2 | 0.46453125 | 0.0432005514 |
| 2 | 64 | 0.35453125 | 0.097578125 | 0.256953125 | 0.0425501323 |
| 2 | 128 | 0.363779296875 | 0.363779296875 | 0 | 0 |
| 3 | 32 | 0.288984375 | -0.2 | 0.488984375 | 0.0444903389 |
| 3 | 64 | 0.37109375 | 0.37109375 | 0 | 0 |
| 3 | 128 | 0.385927734375 | 0.385927734375 | 0 | 0 |

Updates 32 and 64 use 128 evaluation episodes per arm; update 128 uses 1,024. At the primary
endpoint, F has the same return as both learners for each seed. All 1,024 sampled per-episode
records match across T/G/F within each seed, including submission time and native components.
These samples do not establish policy equality outside the observed episodes.

At update 32, G never submits in all three 128-episode evaluations. At update 64 its
non-submission counts are 128, 79 and 8 for seeds 1, 2 and 3; T's counts are 4, 10 and 8.
This supports variable catch-up timing. G's early evaluated greedy policy is plainly weak;
the observed differences must not be presented as superiority over a competent early generic
policy. Training was stochastic and had real gradient exposure. Early greedy failure is not
absence of training. F was measured only at the main endpoint, so early T-F advantage is unknown.

The tool-produced primary run summary uses exactly one score per training seed and arm:
T and G each have mean 0.37509765625; all three paired differences and their sample SD are zero.
This describes these three training instances, not zero population uncertainty. The earlier
mean T-G differences are 0.5063020833 at 32 and 0.2747135417 at 64, with across-pair sample SDs
0.0526125522 and 0.2840105444. No checkpoint is promoted to the primary endpoint after observation.

## Actual learning exposure

Every arm has 1,314 actor and 257 critic parameters, completes 16,384 training episodes /
655,360 primitive ticks and 128 joint Adam steps / training backward calls. Each also evaluates
1,280 episodes / 51,200 ticks at the fixed points. All 40 ticks of every episode are executed,
including service and post-submit tails. Policy-dependent decision counts differ despite equal
episodes and updates.

| Seed / arm | Training decision = gradient rows | Initial total L2 / RMS | First displacement / initial-L2 ratio | Final displacement / initial-L2 ratio |
| --- | ---: | --- | --- | --- |
| 1 / T | 53,473 | 6.427330494 / 0.162159562 | 0.017058313 / 0.002654028 | 2.616672277 / 0.407116497 |
| 1 / G | 42,139 | 5.939346313 / 0.149847865 | 0.017058399 / 0.002872100 | 3.095903397 / 0.521253221 |
| 2 / T | 53,848 | 6.561303139 / 0.165539652 | 0.017058564 / 0.002599874 | 2.623161316 / 0.399792733 |
| 2 / G | 40,998 | 6.084073544 / 0.153499305 | 0.017058600 / 0.002803812 | 3.057497740 / 0.502541220 |
| 3 / T | 54,471 | 6.482429028 / 0.163549662 | 0.017058592 / 0.002631512 | 2.684945583 / 0.414188196 |
| 3 / G | 40,416 | 5.998928070 / 0.151351094 | 0.017058546 / 0.002843599 | 2.822717905 / 0.470537048 |

Each complete invocation includes 36,360 episodes / 1,454,400 ticks / 256 joint optimizer steps.
The unchanged integrated check adds 8 episodes / 320 ticks / 32 gradient rows, one backward and
zero optimizer steps, counted separately from learning. F adds 1,024 episodes and no learner.
Across all three invocations: **109,080 complete episodes, 4,363,200 ticks, 768 joint steps**,
six learners, T training gradient rows 161,792 and G 123,553. Parameter movement establishes
exposure, not a native-return advantage.

## Technical acceptance, source and execution

Seed 1 source is `2c7d7ae08f978aa63d58468f3de1adb372f1339a`; its complete collection is
`7ae597324a696c15721dca2c8d227892b011c225`. Seeds 2/3 use
`b77f897da7dea5df2e9230f43c8f128cc281afb3`; collection is
`a8c34d769751e7b299e0265724b705d2e3bb6b60`. The only source change is the authorized CLI
choices list `[1]` to `[1, 2, 3]`; the real parser statements were checked without a learner
import or rollout. No process launched for the earlier unsupported-argument observation.

All three result-bearing invocations used `wsl_4070`, configured CPU float32 / one compute
thread, detached exact-source worktrees, and one fresh actual-node memory admission immediately
before each supervised `timeout 1800s` runner. Each finished with exit 0 within its complete-pair
cap. The tracker reported terminals directly and CM/DM acknowledged them; there was no restart.

| Seed | Physical/effective available bytes | Whole runner wall s | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| 1 | 15,388,168,192 | 2.364870157 | 484,868,096 |
| 2 | 15,677,493,248 | 5.905074235 | 485,208,064 |
| 3 | 15,676,420,096 | 4.023389709 | 485,015,552 |

The two new runner walls sum to 9.928463944s; all three sum to **12.293334101s**. The extension's
95s supervisor-clock elapsed includes collection/control-plane gaps and is not compute sum.
Aggregate CPU seconds and a live thread census were not measured; no parallel speedup is claimed.

The original per-pair planning estimate of 2.364870157s reused seed 1 rates and was explicitly
conditional. It underestimated both new invocations; actual wall times above replace the estimate
for accounting. Known complete cost remains seconds. The evidence does not identify the cause of
rate variation. No timing pilot, profiling programme or additional run was commissioned for it.
Per-arm `I+128*C(128,40)+10*E(128,40)+O` terms are in the analysis and CM collection. This work
has no nested policy/trajectory search; required learning, evaluation and publication are included.

CM verified all endpoints, curve entries, integer accounting, paired episode identities, required
counts, finite final float32 states and publication read-back. The unchanged source retains its
independent review and focused tests; only the actual CLI delta was newly checked. No required
measurement is missing, no extra machinery was added and no scope-budget breach was reported.
These technical facts support measurement trustworthiness, not scientific superiority.

## Recoverable evidence and limits

The complete first result is `VSP03_B01_SEED1_RESULT_EVIDENCE_20260905.md` and `results/b01_seed1/`.
This intake's executable analysis outputs are `results/b01_seeds123/ANALYSIS.json`, `ENDPOINTS.csv`,
`PRIMARY_RUN_SCORES.csv` and scientific-tools `PRIMARY_RUN_SUMMARY.json`. Exact source summaries,
logs, admission and collection checks for seeds 2/3 are copied beside them. The analysis lists
original artifact hashes and locations; no experiment was run to produce these tables.

Complete local raw roots remain in
`C:/Projects/HMASD-worktrees/cm-vsp03-b01-20260905/temp/directions/vsp_03/exp/` as
`vsp03_b01_seed1_r01/`, `vsp03_b01_seed2_r01/`, `vsp03_b01_seed3_r01/`, with sibling memory receipts.
Seed 1 remote cwd is `/home/wu/hmasd-worktrees/vsp03-b01-seed1-r01`; seeds 2/3 use
`/home/wu/hmasd-worktrees/vsp03-b01-seeds23-r01`. Supervisor tasks are
`vsp03-b01-seed<s>-r01-20260905`, with log/status/exit under `/home/wu/.agent-tasks/<task>/`.

The repeated observation weakens primary initialization gain for this host/configuration/budget.
It supports an earlier useful greedy behavior difference followed by catch-up in these runs.
It does not prove learning necessity, performance beyond F, exact headroom, a unique mechanism,
source authentication, task generality, stable equivalence, transfer or multi-agent value.
