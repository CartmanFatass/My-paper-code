# FSD E3 large D0 seed 3 — result evidence

Boundary: 2026-09-05T12:53:31Z. Evidence class: **B/EXPLORE**.
Cell: `large_d0_seed3`, attempt 01, unchanged card `FSD-E3-HET-R01`.

**Valid complete comparator cell; E3 is 17/18 valid.** Final return is
`0.5477905273437504`, episode SE `0.0004625852203950785`; this seed's D0/reference ratio
`0.8848803875346725` exceeds the card's descriptive competence line `0.85`. No paired gain,
row aggregate or E3 branch is read before all 18 cells are valid.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. Binding structure is
temporal abstraction/termination. Policy-gap interruption is tested under heterogeneous hazards
against the strongest same-information exact-best fixed clock. Useful renewal competes with
noisy gaps, optimizer variation and team interference. This cell measures the original comparator.

Large D0 seed 3 uses hazards `(0.02,0.20)`, `Delta=1`, best `k=5`, infinite individual/team
costs, both caps 5 and age off. Infinite costs use the unchanged D2 implementation route;
Infinity serialization is intentional. Future paired D2 retains costs 0.25/caps 40/400 and
the same information/interaction/evaluation budget. Host: six pinned entities, three per region,
`K=2`, `Z=4`, horizon 400, Bernoulli, `rho=0`, no probe/coupling. CPU/four-thread, precision,
RNG/tapes, observation/action/reward, recurrence, optimizer, checkpoint, normalizer copying and
evaluator RNG preservation are unchanged. Windows/Linux CPU portability was prospective;
no CUDA or cross-host bit-identity claim.

Native trace: event -> lease invalidation -> public flag/lagged cue -> fixed renewal -> setup
outage/fresh lease -> service -> shared return. Fixed entity identity/membership introduces no
churn, replacement, survivor-state or censoring quantity. Claim ceiling remains preliminary B
mechanism evidence on the declared rows, no C consumption, transfer, stable superiority or
direction disposition. Original full-matrix reading rule is unchanged.

## Provenance, receipts and conformance

- Exact pushed launch SHA: `96ca5fbf815f142008d6622759014a98bd915d6f`.
- Node `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Original task `fsd_e3_large_d0_seed3_20260905_01`; wrapper/learner PIDs `1670783/1670799`.
- Remote cwd `/home/wu/hmasd-worktrees/fsd_e3_large_d0_seed3_20260905_01`;
  cell beneath it `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed3`.
- Staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d0_seed3_terminal_01/large_d0_seed3`.
- Canonical:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed3`.
- CM command/checks/ten matching remote/staged/canonical hashes:
  `docs/Claude_docs/experiments/FSD_E3_LARGE_D0_SEED3_REMOTE_RUN_20260905.md`, terminal commit
  `0789a185ec5146d733e333d5a05de42121457075`.
  Summary SHA-256 `2dae386c8ce4077057aa7f6165e094c02d60d80a0410ec04fe52844cdbddc099`.

Original `<root>/preflight.json`, assessed `2026-09-05T12:04:59.381927Z`, measured physical/
effective availability each **15,420,182,528 bytes**, above the 4,294,967,296-byte floor;
all pass fields true. Actual-node admission immediately preceded the exact runner through
`&&` in one detached command. Collection read existing evidence without new learner/evaluation.

Direct original status is finished/exit 0/tmux inactive. Retained log terminal
`2026-09-05T12:49:08Z`, duration **2649 s**; later uptime is not runtime. Full learner,
evaluation, two-region path/publication, exposure and finite checkpoint support acceptance;
exit alone does not. All ten hashes match at three locations. Canonical copy followed absence
check, preserving prior roots/quarantine. Checkpoint 64,782,527 bytes retains float32 tensors,
five optimizer states, both value normalizers and `hmasd_rollout_sampler_rng_v1`; readability is
not resume equivalence. Artifact payload 67,848,013 bytes is not peak scratch.

## Work, exposure and direct observations

Twenty rollouts × 16 lanes × 400 steps = **128,000 transitions/320 training episodes**.
Actual optimizer steps: coordinator 3,000; actor/critic 72,000 each; team/individual 300/1,200;
**148,500 total**, positive in every group. Each learner/path stream contains 20 ordered
records and both regions. Four deterministic evaluations total 3,584 episodes, master 770003,
chunk 512, ordered IDs starting 0.

Machine-generated float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.03863921908980191 | 0.11931666592589114 |
| Discoverer actor | 0.16420479766145465 | 0.8699752052554447 |
| Discoverer critic | 0.23738037406343426 | 0.895350160692678 |
| Team discriminator | 0.009393721505804307 | 0.036233958172901634 |
| Individual discriminator | 0.011595851021922685 | 0.05383100832758749 |

| Evaluation rollout | Episodes | Published mean | Episode SE |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.45693766276041703 | 0.0012958060783048301 |
| 10 | 512 | 0.5316927083333336 | 0.0009595888114296442 |
| 15 | 512 | 0.5104777018229174 | 0.0014586791101470031 |
| 20 | 2,048 | 0.5477905273437504 | 0.0004625852203950785 |

DM independently read all four finite ordered episode arrays and recomputed means/sample SE.
They match to rounding; final mean matches exactly, DM SE `0.00046258522039507844`.
Division by registered `J_k=0.619056016` gives `0.8848803875346725`, above this seed's
`0.85` competence line. No checkpoint selection; episode SE does not establish seed stability.
Public upper `0.8902749999999997` and structural margin `0.27121898399999966` remain references,
not observed treatment gains.

| Cumulative training-path quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent/environment steps | 384,000/128,000 | 384,000/128,000 |
| Segments | 76,800 | 76,800 |
| Segment mean/min/max/every decile | 5 | 5 |
| Regional events | 2,595 | 25,479 |
| Gap renewals/team-gap decisions | 0/0 | 0/0 |
| Gap-event precision/recall | undefined/0 | undefined/0 |
| Cap/reset boundaries | 75,840/960 | 75,840/960 |
| Renewal-outage count/rate | 76,800/0.2 | 76,800/0.2 |
| Fresh correct-role service count | 180,316 | 103,989 |
| Stale service/correct-role opportunities | 0/7,042 | 0/63,060 |
| Mean shared-return contribution | 0.2347864583333333 | 0.13540234375 |

Undefined precision follows from zero gap renewals, not missing instrumentation. This comparator
path is not an observation of the still-unlaunched paired treatment cell.

## Rule, cost, deviations and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

At **17 valid cells**, only `large_d2_seed3` remains unlaunched. No paired `G`, uncertainty,
`Q`, row aggregate or E3 branch is read. DM prediction `E3-H0-NO-ADVANTAGE` stays unscored;
owner not taken (unattended). No threshold or result branch changes.

Valid-cell machine charge is runner wall **2445.5143795790063 s** (40.7586 minutes), separate
from supervisor duration 2649 s. Frozen D0 projection
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s` (1.68 h), cap 8 h per invocation.
Both durations are below cap; no nonfinite/time stop or extra exposure. Peak RSS/scratch remain
`resources_unmeasured`, allowed for this non-resource claim.

No source/scope addition, section-5 budget breach, repeated test or publication gap occurred.
Accepted repaired E3 publication coverage and 13/13 focused checks remain applicable. Earlier
remote auto-gc preparation warning remains unresolved maintenance evidence; exact checkout/run
succeeded without history repair or restart.

The smallest supported update is this complete competent comparator seed. Duration control/
comparator readiness remain support; E2 `NEITHER`, weak alignment and seed dependence remain
contrary evidence. All original D0 cells now exist; headroom/row summaries remain unread until
the full-matrix boundary. A1 census remains the headroom reference, with no new tuning/MEI.
Next and last unchanged cell is `large_d2_seed3`; original paired return and regional path
after 18 valid cells remain the scientific discriminator.
