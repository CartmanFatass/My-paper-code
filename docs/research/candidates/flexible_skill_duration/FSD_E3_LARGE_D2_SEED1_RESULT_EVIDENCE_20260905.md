# FSD E3 large D2 seed 1 — result evidence

Boundary: 2026-09-05T10:03:18Z. Evidence class: **B/EXPLORE**.
Cell: `large_d2_seed1`, attempt 01, unchanged card `FSD-E3-HET-R01`.

**Valid complete treatment cell; E3 remains incomplete at 14/18.** Final return is
`0.4767451985677085`, episode standard error `0.0008411905410491914`. This is a single-cell
observation; no paired gain, row aggregate or E3 branch is read before all 18 cells are valid.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. The temporal-abstraction/
termination question is whether policy-gap interruption exploits heterogeneous hazards against
the strongest same-information exact-best fixed clock. Useful renewal competes with noisy gaps,
optimizer variation and team-renewal interference.

This cell uses large hazards `(0.02,0.20)`, `Delta=1`, seed 1, `c=c_Z=0.25`, individual/team
caps 40/400, interruption delta 1 and age off. The unchanged comparator has `k=5`, infinite
costs and both caps 5. Environment: six pinned entities, three per region, `K=2`, `Z=4`,
horizon 400, Bernoulli events, `rho=0`, no probe/coupling. CPU/four-thread execution preserves
precision, RNG/train/evaluation tapes, observation/action/reward, recurrence, optimizer,
checkpoint, evaluator RNG preservation and deep-copied normalizer synchronization. Windows/Linux
CPU portability was prospective; no CUDA or cross-host bit-identity claim is introduced.

Native trace: event -> lease invalidation -> public flag/lagged cue -> held-skill gap -> individual
or team renewal -> setup outage/fresh lease -> service -> shared return. Membership and entity
identity are fixed; no churn, replacement, survivor-state or censoring quantity is introduced.
Claim ceiling remains preliminary mechanism evidence on the three declared corridor rows, with
no C confirmation/consumption, transfer, stable superiority or direction-closure claim.

## Provenance, receipts and conformance

- Exact pushed launch SHA: `e6d049849f717b2aca98ab1bb77092e000cd06d9`.
- Node: `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Sole accepted task: `fsd_e3_large_d2_seed1_20260905_01`; wrapper/learner PIDs `1609006/1609022`.
- Remote cwd: `/home/wu/hmasd-worktrees/fsd_e3_large_d2_seed1_20260905_01`.
  Cell root beneath it: `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed1`.
- Distinct staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d2_seed1_terminal_01/large_d2_seed1`.
- Canonical cell:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed1`.
- Exact command, technical checks and all ten matching remote/staged/canonical hashes:
  `docs/Claude_docs/experiments/FSD_E3_LARGE_D2_SEED1_REMOTE_RUN_20260905.md`.
  Accepted terminal CM commit: `f190fa89d1ab6050177ce160eadf65f8c41be970`.
  Summary SHA-256: `d6801ec6a0c7ef47706768382f6ee008f105854b88d41036c391177c5f9dbc98`.

Original `<root>/preflight.json`, assessed `2026-09-05T09:06:33.522186Z`, measured physical and
effective available memory each **15,434,289,152 bytes**, above 4,294,967,296; every pass field
was true. It immediately preceded the exact runner in one `&&`-joined supervisor command.
No learner, replay, evaluation or new admission was invoked during existing-evidence collection.

The original supervisor finished exit 0, tmux inactive. Its retained log records terminal
`2026-09-05T09:56:07Z`, duration **2974 s**. Later status uptime includes post-terminal time.
CM checked all learner/evaluation/path/publication outputs, finite checkpoint and original
receipt; exit alone is not validity. Ten file hashes match across all three locations. Canonical
copy occurred only after an absence check; older cells and quarantine remain preserved.
Checkpoint is 64,782,527 bytes with float32 network tensors, five finite optimizer states,
both value normalizers and `hmasd_rollout_sampler_rng_v1`. Readability is not resume equivalence.
Payload 67,981,559 bytes is not peak scratch.

## Actual work and exposure

Twenty completed rollouts, each 16 lanes by 400 steps, give **128,000 transitions and 320
training episodes**. Metrics/path/interruptions/gaps each contain 20 ordered records and both
regions. Actual optimizer steps: coordinator 4,560; actor 9,000; critic 9,000; team 300;
individual 1,200; **24,060 total**, positive for each group. Four evaluations total 3,584
episodes, deterministic master 770003, ordered IDs `0..n-1`, chunk 512.

Machine-generated float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.02026678921206913 | 0.1667955154349446 |
| Discoverer actor | 0.0733190219723839 | 0.4491235564251638 |
| Discoverer critic | 0.12772162122146374 | 0.44350370966282976 |
| Team discriminator | 0.012265348298618074 | 0.05833616468318452 |
| Individual discriminator | 0.017766117417165165 | 0.07370210335342033 |

## Direct observations

| Evaluation rollout | Episodes | Published mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.39751790364583334 | 0.001978029926622355 |
| 10 | 512 | 0.4061637369791667 | 0.0016934020713787346 |
| 15 | 512 | 0.4778084309895836 | 0.001476102436623097 |
| 20 | 2,048 | 0.4767451985677085 | 0.0008411905410491914 |

DM independently read the four ordered finite per-episode arrays and recomputed means/sample
standard errors. They match publication to rounding; final DM mean is `0.47674519856770853`.
Episode uncertainty does not establish seed stability.

| Cumulative training-path quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent/environment steps | 384,000/128,000 | 384,000/128,000 |
| Segments | 70,651 | 69,683 |
| Mean segment length | 5.435167230470906 | 5.51066974728413 |
| Segment minimum/maximum | 1/40 | 1/40 |
| Segment deciles | 1,1,1,1,1,1,2,4,17 | 1,1,1,1,1,1,2,5,18 |
| Events | 2,539 | 25,600 |
| Gap renewals/rate per agent-step | 65,627/0.17090364583333334 | 64,409/0.16773177083333332 |
| Team-gap decisions | 17,516 | 17,516 |
| Gap-renewal event precision | 0.0786109375714264 | 0.495676070114425 |
| Event recall | 0.5659708546671918 | 0.3572265625 |
| Cap/reset boundaries | 4,064/960 | 4,314/960 |
| Renewal-outage count/rate | 70,651/0.18398697916666668 | 69,683/0.18146614583333334 |
| Fresh correct-role service count | 160,913 | 42,648 |
| Stale service/correct-role opportunities | 0/27,527 | 0/122,776 |
| Mean shared-return contribution | 0.20952213541666662 | 0.05553124999999999 |

The team decisions are shared events, not independent region counts to sum. These training-path
measurements are distinct from deterministic evaluation returns. They preserve this seed's raw
regional inputs without reading the full-matrix event-path or paired-return branch.

## Rule, cost and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

At **14 valid cells**, four cells remain unlaunched. No paired `G`, paired uncertainty, `Q`,
row-shape aggregate or E3 branch is computed. DM `E3-H0-NO-ADVANTAGE` prediction stays unscored;
owner prediction is `not taken (unattended)`. No threshold or original branch is revised.

Runner wall **2795.3028715779947 s** (46.5884 minutes) is this valid cell's measured machine
charge; supervisor duration is separately 2974 s. Frozen D2 projection
`[20*(64.6+0.769*750)+3584*0.46]*1.15=16646.986 s` (4.63 h) and cap 8 h remain unchanged.
Both durations are below the cap; no nonfinite/cap stop, extra training or retuning occurred.

Peak RSS/scratch remain `resources_unmeasured`, allowed for this non-resource claim. There is
no source change, new scope machinery or engineering section-5 budget breach. Accepted repaired
publication coverage and 13/13 focused checks remain applicable; no repeated suite or new
publication gap. The remote Git auto-gc preparation warning is an unresolved maintenance fact;
exact source/worktree creation succeeded and no history repair or restart was attempted.

This is a complete treatment observation within the original mechanism test. Existing duration
control and a competent comparator seed are supporting context; E2 `NEITHER`, weak event
alignment and seed dependence remain contrary evidence. The A1 census/structural references
remain the headroom record; the full trained large-row baseline set is incomplete. No investment
threshold or duplicate headroom run follows. Next discriminator remains original paired return
and regional event path after all 18 valid cells; next unchanged invocation is `large_d0_seed2`.
