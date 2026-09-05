# FSD E3 large D2 seed 2 — result evidence

Boundary: 2026-09-05T11:58:52Z. Evidence class: **B/EXPLORE**.
Cell: `large_d2_seed2`, attempt 01, unchanged card `FSD-E3-HET-R01`.

**Valid complete treatment cell; E3 is 16/18 valid.** Final return is
`0.455985310872396`, episode standard error `0.0008124099606355347`. No paired gain,
row aggregate or E3 branch is read before all 18 cells are valid.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. The temporal-abstraction/
termination question is whether policy-gap interruption captures heterogeneous-hazard duration
value against the strongest same-information exact-best fixed clock. Useful regional renewal,
noisy gaps, optimizer variation and team-renewal interference remain live explanations.

Large D2 seed 2 has hazards `(0.02,0.20)`, `Delta=1`, `c=c_Z=0.25`, caps 40/400, delta 1,
age off; comparator remains best D0 `k=5`, infinite costs/both caps 5. Host: six pinned entities,
three per region, `K=2`, `Z=4`, horizon 400, Bernoulli, `rho=0`, no probe/coupling. Original
information, training and evaluation budgets remain fixed. CPU/four-thread, precision, RNG/tapes,
observation/action/reward, recurrence, optimizer, checkpoint, normalizer copying and evaluator RNG
preservation are unchanged. Windows/Linux CPU portability was prospective; no CUDA/bit-identity claim.

Native trace: event -> lease invalidation -> public flag/lagged cue -> held-skill gap -> individual/
team renewal -> setup outage/fresh lease -> service -> shared return. Fixed membership/entity
identity introduces no churn, replacement, survivor-state or censoring quantity. Claim ceiling
remains preliminary B mechanism evidence on the declared corridor rows, no C consumption,
stable superiority, transfer or direction-family disposition.

## Provenance, receipts and conformance

- Exact pushed launch SHA: `6d64a95a1189523e39abb184ef284a574050b748`.
- Node `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Original task `fsd_e3_large_d2_seed2_20260905_01`; wrapper/learner PIDs `1663230/1663246`.
- Remote cwd `/home/wu/hmasd-worktrees/fsd_e3_large_d2_seed2_20260905_01`;
  cell beneath it `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed2`.
- Staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d2_seed2_terminal_01/large_d2_seed2`.
- Canonical:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed2`.
- CM record with exact command/checks/ten matching remote/staged/canonical hashes:
  `docs/Claude_docs/experiments/FSD_E3_LARGE_D2_SEED2_REMOTE_RUN_20260905.md`, terminal commit
  `d7f0089700c731290abcca2eeb4d14d04edb6e5d`.
  Summary SHA-256 `5c106f64790f833faa8d43e7af8e872f7ea9e00df2d8349a3a742fbfa3776f22`.

Original `<root>/preflight.json`, assessed `2026-09-05T11:07:08.744562Z`, measured physical/
effective availability each **15,425,314,816 bytes**, above the 4,294,967,296-byte floor; all pass
fields true. Destination admission immediately preceded the exact runner through `&&` in one
detached supervisor command. Collection read existing evidence, without new learner/evaluation.

Direct original status is finished/exit 0/tmux inactive. Retained log terminal
`2026-09-05T11:54:29Z`, duration **2841 s**; later uptime is not run duration. Complete learner,
evaluation, two-region path/publication, exposure and finite checkpoint support acceptance;
exit alone does not. All ten hashes match at three locations. Canonical copy followed an absence
check; prior roots/quarantine are preserved. Checkpoint 64,782,527 bytes retains float32 tensors,
five optimizer states, both value normalizers and `hmasd_rollout_sampler_rng_v1`; readability is
not resume equivalence. Artifact payload 67,783,078 bytes is not peak scratch.

## Actual work and exposure

Twenty rollouts × 16 lanes × 400 steps give **128,000 transitions/320 training episodes**.
Actual optimizer steps: coordinator 4,350; actor/critic 9,000 each; team/individual 300/1,200;
**23,850 total**, with positive updates in every group. Each learner/path stream has 20 ordered
records and both regions. Four deterministic evaluations total 3,584 episodes, master 770003,
chunk 512, ordered episode IDs starting 0.

Machine-generated float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.02043369954191478 | 0.15875599390994485 |
| Discoverer actor | 0.07680369771717817 | 0.4604798051816602 |
| Discoverer critic | 0.10591535982546985 | 0.3987952546815615 |
| Team discriminator | 0.013602222092439449 | 0.05589034614402242 |
| Individual discriminator | 0.017309193735545046 | 0.08089895164710789 |

## Direct observations

| Evaluation rollout | Episodes | Published mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.4004606119791665 | 0.0018831116806533657 |
| 10 | 512 | 0.44155598958333353 | 0.0019065470116194415 |
| 15 | 512 | 0.4409480794270835 | 0.001888977391603647 |
| 20 | 2,048 | 0.455985310872396 | 0.0008124099606355347 |

DM independently read all four finite ordered episode arrays and recomputed means/sample standard
errors. They match to rounding; final DM mean `0.45598531087239597`, SE matches exactly.
No checkpoint is selected from the curve; episode uncertainty does not establish seed stability.

| Cumulative training-path quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent/environment steps | 384,000/128,000 | 384,000/128,000 |
| Segments | 52,424 | 54,805 |
| Mean segment length | 7.324889363650237 | 7.006659976279536 |
| Segment minimum/maximum | 1/40 | 1/40 |
| Segment deciles | 1,1,1,1,1,2,3,9,37 | 1,1,1,1,1,2,4,9,30 |
| Regional events | 2,520 | 25,352 |
| Gap renewals/rate per agent-step | 46,610/0.12138020833333334 | 49,747/0.12954947916666668 |
| Team-gap decisions | 11,004 | 11,004 |
| Gap-renewal event precision | 0.08897232353572194 | 0.5750698534585 |
| Event recall | 0.5916666666666667 | 0.40691069738087726 |
| Cap/reset boundaries | 4,854/960 | 4,098/960 |
| Renewal-outage count/rate | 52,424/0.13652083333333334 | 54,805/0.14272135416666668 |
| Fresh correct-role service count | 161,418 | 47,422 |
| Stale service/correct-role opportunities | 0/32,532 | 0/123,961 |
| Mean shared-return contribution | 0.21017968750000002 | 0.061747395833333316 |

Team decisions are shared events, not independent region counts to sum. Training-path quantities
are distinct from deterministic evaluation returns; these are this seed's raw inputs, not a
full-matrix mechanism verdict.

## Rule, cost, deviations and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

At **16 valid cells**, two cells remain unlaunched. No paired `G`, paired uncertainty, `Q`, row
aggregate or E3 branch is read. DM prediction `E3-H0-NO-ADVANTAGE` stays unscored; owner prediction
is `not taken (unattended)`. No original threshold or branch is revised.

Valid-cell measured charge is runner wall **2646.4799736300047 s** (44.1080 minutes), separately
supervisor duration 2841 s. Frozen D2 projection remains
`[20*(64.6+0.769*750)+3584*0.46]*1.15=16646.986 s` (4.63 h), cap 8 h per invocation.
Both durations are below the cap; no nonfinite/time stop, extra exposure or retuning occurred.
Peak RSS/scratch stay `resources_unmeasured`, allowed for this non-resource claim.

There is no source/scope addition, section-5 budget breach, repeated test or publication gap.
Accepted repaired E3 publication coverage and 13/13 focused checks remain applicable. Earlier
remote auto-gc preparation warnings remain unresolved maintenance observations; exact checkout
and this run succeeded without history repair/restart.

The smallest supported update is a complete treatment seed with its required return/path inputs.
Duration control/comparator readiness remain support; E2 `NEITHER`, weak alignment and seed
dependence remain contrary evidence. The A1 census is the headroom record; final large D0 seed
coverage is still pending. No duplicate headroom run or new MEI is introduced. Next unchanged
cell is `large_d0_seed3`; scientific discrimination remains the original paired-return/regional-
path reading after 18 valid cells.
