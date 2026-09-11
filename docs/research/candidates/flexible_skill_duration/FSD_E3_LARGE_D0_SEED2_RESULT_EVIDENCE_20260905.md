# FSD E3 large D0 seed 2 — result evidence

Boundary: 2026-09-05T11:00:40Z. Evidence class: **B/EXPLORE**.
Cell: `large_d0_seed2`, attempt 01, unchanged card `FSD-E3-HET-R01`.

**Valid complete comparator cell; E3 is 15/18 valid.** Final return is
`0.5648811848958336`, episode standard error `0.0004164077492897991`; D0/reference ratio
`0.912487998332987` meets this seed's descriptive competence line `0.85`. No paired gain,
row aggregate or E3 branch is read before all 18 cells are valid.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. Binding structure is
temporal abstraction/termination. The question is whether policy-gap interruption captures
heterogeneous-hazard duration value against the strongest same-information exact-best fixed clock.
Useful renewal, noisy gaps, optimizer variation and team-renewal interference remain alternatives.

Large D0 seed 2 uses hazards `(0.02,0.20)`, `Delta=1`, best `k=5`, infinite individual/team
costs, both caps 5 and age off. D0 uses the unchanged D2 implementation route with infinite
costs; its serialized Infinity is intentional. Its future paired D2 uses costs 0.25/caps 40/400.
Both share the original information, interaction and evaluation budgets. Host: six pinned
entities, three per region, `K=2`, `Z=4`, horizon 400, Bernoulli, `rho=0`, no probe/coupling.
CPU/four-thread, precision, RNG/train/eval tapes, observation/action/reward, recurrence,
optimizer, checkpoint, normalizer copying and evaluator RNG preservation stay unchanged.
Windows/Linux CPU portability was prospective; there is no CUDA or cross-host bit-identity claim.

Native trace: event -> lease invalidation -> public flag/lagged cue -> fixed renewal -> setup
outage/fresh lease -> service -> shared return. Membership/entity identity are fixed; no churn,
replacement, survivor-state or censoring quantity is introduced. Ceiling remains preliminary B
mechanism evidence on three declared corridor rows, no C consumption, transfer, stable superiority
or direction-family disposition. The complete-matrix reading rule remains unchanged.

## Provenance and receipts

- Exact pushed launch SHA: `ac4db77371659c25d4ac39e1a20990fe098bc42d`.
- Node `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Original task `fsd_e3_large_d0_seed2_20260905_01`; wrapper/learner PIDs `1656091/1656107`.
- Remote cwd `/home/wu/hmasd-worktrees/fsd_e3_large_d0_seed2_20260905_01`;
  cell beneath it `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed2`.
- Staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d0_seed2_terminal_01/large_d0_seed2`.
- Canonical:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed2`.
- CM record with exact command, inspection and ten identical remote/staging/canonical hashes:
  `docs/Claude_docs/experiments/FSD_E3_LARGE_D0_SEED2_REMOTE_RUN_20260905.md`, terminal commit
  `c2da7f5f60484323f731c5efa2642f9a65b3357a`.
  Summary SHA-256 `2d41dd5a3eaf02968806ec1c325c3fba128699c7d53dde09ab59ba599d834b73`.

Original `<root>/preflight.json`, assessed `2026-09-05T10:09:55.213783Z`, measured physical
and effective availability each **15,430,356,992 bytes**, above the 4,294,967,296-byte floor;
all pass fields true. The destination admission immediately preceded the exact runner through
`&&` in one detached supervisor command. Collection reads existing evidence only.

Direct original status is finished/exit 0/tmux inactive. Retained log terminal is
`2026-09-05T10:56:19Z`, duration **2784 s**; later uptime includes post-terminal time.
CM checked complete learner/evaluation/two-region path/publication, exposure and finite checkpoint;
exit 0 alone does not establish validity. All ten transferred files match at three locations.
Canonical copy followed an absence check; previous roots/quarantine remain unchanged.
Checkpoint 64,782,527 bytes retains float32 tensors, five optimizer states, both value normalizers
and `hmasd_rollout_sampler_rng_v1`. Readability is not resume equivalence. Artifact payload
67,845,846 bytes is not peak scratch.

## Work, learner exposure and observations

Twenty rollouts × 16 lanes × 400 steps give **128,000 transitions/320 training episodes**.
Actual optimizer steps are coordinator 3,000; actor/critic 72,000 each; team/individual 300/1,200;
**148,500 total**, with positive updates in every group. Each learner/path stream has 20 ordered
records and both regions. Four evaluations total 3,584 episodes, deterministic master 770003,
chunk 512, ordered episode IDs starting 0.

Machine-generated float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.04180633304054413 | 0.10621772056692431 |
| Discoverer actor | 0.15479584233213217 | 0.8433220458564978 |
| Discoverer critic | 0.2172988190776331 | 0.8944677205866685 |
| Team discriminator | 0.009429305303445627 | 0.03559481001200934 |
| Individual discriminator | 0.012601989682234131 | 0.054078531885410966 |

| Evaluation rollout | Episodes | Published mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.5936360677083337 | 0.0008057307641947364 |
| 10 | 512 | 0.5682853190104172 | 0.0007811659933446816 |
| 15 | 512 | 0.5572184244791669 | 0.0008400097772878067 |
| 20 | 2,048 | 0.5648811848958336 | 0.0004164077492897991 |

DM independently read all four finite ordered episode arrays and recomputed means/sample standard
errors. They agree to rounding; final mean/SE match exactly. Division by declared `J_k=0.619056016`
gives `0.912487998332987`, above `0.85` for this seed. No checkpoint is selected from the curve.
Episode uncertainty does not establish seed stability. Public upper `0.8902749999999997` and
structural margin `0.27121898399999966` remain reference quantities, not observed treatment gains.

| Cumulative training-path quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent/environment steps | 384,000/128,000 | 384,000/128,000 |
| Segments | 76,800 | 76,800 |
| Segment mean/min/max/every decile | 5 | 5 |
| Regional events | 2,520 | 25,352 |
| Gap renewals/team-gap decisions | 0/0 | 0/0 |
| Gap-event precision/recall | undefined/0 | undefined/0 |
| Cap/reset boundaries | 75,840/960 | 75,840/960 |
| Renewal-outage count/rate | 76,800/0.2 | 76,800/0.2 |
| Fresh correct-role service count | 180,402 | 107,114 |
| Stale service/correct-role opportunities | 0/7,371 | 0/63,819 |
| Mean shared-return contribution | 0.23489843749999997 | 0.13947135416666664 |

Undefined gap-event precision follows from zero gap renewals in the infinite-cost comparator;
it is not missing instrumentation or a measurement of the absent paired treatment cell.

## Rule, cost, deviations and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

At **15 valid cells**, three cells remain unlaunched. No paired `G`, paired uncertainty, `Q`,
row aggregate or E3 branch is computed. DM prediction `E3-H0-NO-ADVANTAGE` stays unscored;
owner prediction is `not taken (unattended)`. No original threshold or branch is revised.

Measured charge for this valid cell is runner wall **2603.2776923269994 s** (43.3880 minutes),
separate from supervisor duration 2784 s. D0 projection remains
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s` (1.68 h), cap 8 h per invocation.
Both actual durations are below the cap; no nonfinite/time stop or extra exposure occurred.
Peak RSS/scratch are `resources_unmeasured`, allowed for this non-resource claim.

No code/scope addition, section-5 budget breach, repeated test or new publication gap occurred.
Accepted repaired E3 publication coverage and 13/13 focused checks remain applicable. Earlier
remote auto-gc preparation warnings remain unresolved maintenance observations; exact source
checkout succeeded, and no history repair or restart was attempted.

The smallest supported update is this complete competent comparator seed. Duration control and
comparator readiness support the original test; E2 `NEITHER`, weak event alignment and seed
dependence remain contrary evidence. The A1 census is the headroom record; full large-row trained
baseline coverage still awaits its final seed. No duplicate headroom run or new MEI is introduced.
The next unchanged cell is `large_d2_seed2`; scientific discrimination remains the original
paired-return/regional-path reading after 18 valid cells.
