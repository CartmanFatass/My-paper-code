# FSD E3 large D0 seed 1 — result evidence

Date: 2026-09-04 PDT. Terminal date: 2026-09-05 UTC. Evidence class: **B/EXPLORE**.
Cell: `large_d0_seed1`, attempt 01, unchanged card `FSD-E3-HET-R01`.

**Valid complete comparator cell; E3 remains incomplete at 13/18.** Final return is
`0.5481325276692715`, episode standard error `0.0005496801464339235`; the fixed-clock
reference ratio is `0.8854328421053118`, above the card's descriptive competence line `0.85`.
This is one competent D0 seed, not a completed treatment pair or a mechanism result.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`. The question is whether
policy-gap interruption under heterogeneous hazards improves native return against the strongest
same-information fixed clock. Binding structure is temporal abstraction/termination. Useful
regional renewal competes with noisy gaps, optimizer variation and team-renewal interference.

This comparator has large-row hazards `(0.02,0.20)`, `Delta=1.0`, exact best fixed `k=5`,
infinite individual/team interruption costs, both caps 5, age off and seed 1. Its future paired
D2 has `c=0.25`, caps 40/400 and the same information/transition/evaluation budget. The relay
corridor has six pinned entities, three per region, `K=2`, `Z=4`, horizon 400, Bernoulli events,
`rho=0`, no probe or coupling. CPU/four-thread, current precision, RNG/tapes, evaluation and
normalizer synchronization, checkpoint format, observation/action/reward semantics are preserved.
Host portability remains Windows/Linux CPU, with no GPU substitution or bit-identity claim.

Native trace is event -> lease invalidation -> public change flag and lagged cue -> fixed-clock
renewal -> setup-outage step and fresh lease -> service -> shared return. Entity identity and
membership are fixed; no join/leave/rejoin, replacement, survivor-state or censoring quantity
is introduced. This B cell supports no C confirmation/consumption, transfer, stable superiority,
variable-population or direction-closure claim. The original card rule is not revised.

## Provenance, receipts and conformance

- Exact pushed launch SHA: `f42dcb7a76f6341d3552a27134ca674674b29718`.
- Node: `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Sole accepted task: `fsd_e3_large_d0_seed1_20260904_01`; wrapper/learner PIDs `802417/802469`.
- Original cwd: `/home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01`.
  Root under it: `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1`.
- Distinct staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d0_seed1_terminal_01/large_d0_seed1`.
- Canonical copy:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1`.
- Exact command, checkpoint inspection, terminal witnesses and ten transfer hashes:
  `docs/Claude_docs/experiments/FSD_E3_LARGE_D0_SEED1_REMOTE_RUN_20260904.md`.
  Accepted terminal CM commit: `5c70f068d023f54a20f8d264a52163694280a411`.
  Summary SHA-256: `fc0507d3d5a1fb128c5f2bf9ffa8fced81490e4e62ca073473841ffbca8a4418`.

Original immediate remote admission at `<root>/preflight.json` was assessed at
`2026-09-05T00:52:33.793656Z`: physical/effective available memory each `15,042,007,040`
bytes, floor `4,294,967,296`, all pass fields true. Admission immediately preceded the exact
runner in one `&&`-joined supervisor payload. No second admission/learner was used for collection.

CM verified terminal `finished`, exit 0, tmux inactive. The retained supervisor log ends at
`2026-09-05T01:41:53Z` with duration **2960 s**. Status uptime later includes time after
termination and is not substituted for experiment duration. The complete required learner,
evaluation, two-region path, exposure, checkpoint and E3 publication outputs were inspected;
process exit alone is not the validity evidence. Original and prior quarantined roots remain
unaltered; copied evidence is checked against the original bytes.
All ten remote/staged/canonical hashes agree; the canonical cell was copied only after confirming
absence. The 64,782,527-byte checkpoint retains float32 network tensors, five finite optimizer
states, both value normalizers and `hmasd_rollout_sampler_rng_v1`. Total artifact payload is
67,848,670 bytes, not a peak-scratch measurement. Readability is not resume equivalence.

## Actual work and learner exposure

| Quantity | Observed |
| --- | ---: |
| Requested/completed rollouts | 20/20 |
| Lanes/steps per rollout | 16/400 |
| Transitions/training episodes | 128,000/320 |
| Coordinator optimizer steps | 3,000 |
| Discoverer actor/critic optimizer steps | 72,000/72,000 |
| Team/individual discriminator optimizer steps | 300/1,200 |
| Total actual optimizer steps | 148,500 |
| Evaluation records/episodes | 4/3,584 |

Twenty ordered records exist in each learner/path stream, with both regions present; actual
optimizer steps are reported separately from environmental interaction. All five trained groups
have positive updates and finite first/final parameter-displacement ratios. Machine-generated
float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.03963771164671024 | 0.12392500707800136 |
| Discoverer actor | 0.15977620771044398 | 0.8630096950038654 |
| Discoverer critic | 0.2305541232709665 | 0.8745928208891488 |
| Team discriminator | 0.010203675033779294 | 0.03338753931700782 |
| Individual discriminator | 0.013056890182455691 | 0.053849379252340644 |

## Direct observations

| Evaluation rollout | Episodes | Published return mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.511727701822917 | 0.0009085444689766701 |
| 10 | 512 | 0.521028645833334 | 0.0011370648387067398 |
| 15 | 512 | 0.5319368489583337 | 0.001079320716471969 |
| 20 | 2,048 | 0.5481325276692715 | 0.0005496801464339235 |

DM read all four ordered finite episode-return arrays and independently recomputed their means
and sample-based standard errors. They agree to floating-point rounding; DM final mean is
`0.5481325276692713`, standard error exactly `0.0005496801464339235`. Dividing by registered
`J_k=0.619056016` gives `0.8854328421053117`, consistent with the published ratio and the
card's descriptive competence line. Episode uncertainty does not establish seed stability.
The public upper remains `0.8902749999999997`, and the structural duration margin is
`0.27121898399999966`; neither is an observed D2 gain or a complete trained-baseline row.

| Cumulative training-path quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent steps/environment steps | 384,000/128,000 | 384,000/128,000 |
| Completed segments | 76,800 | 76,800 |
| Segment mean, minimum, maximum and every decile | 5 | 5 |
| Regional events | 2,539 | 25,600 |
| Gap renewals/team-gap decisions | 0/0 | 0/0 |
| Gap-renewal event precision/recall | undefined/0 | undefined/0 |
| Cap boundaries/reset boundaries | 75,840/960 | 75,840/960 |
| Renewal-outage count/rate | 76,800/0.2 | 76,800/0.2 |
| Fresh correct-role service count | 187,077 | 106,153 |
| Stale service/stale correct-role opportunities | 0/6,905 | 0/62,827 |
| Mean shared-return contribution | 0.24358984374999998 | 0.13822005208333332 |

Undefined gap-event precision follows from zero gap renewals in the infinite-cost arm. It is
not missing instrumentation. The fixed-clock path is present and does not supply a D2 event-path
measurement. The unlaunched paired D2 return is not zero.

## Rule, cost, deviations and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

At **13 valid cells**, five large-row cells are unlaunched. No paired `G`, standard error,
`Q`, row-shape aggregate or E3 branch is computed. The five unchanged card branches remain
inapplicable; missing pairs are not failed comparators. DM prediction `E3-H0-NO-ADVANTAGE`
remains unscored. Owner prediction remains `not taken (unattended)` with no reply at intake.

Runner wall is **2837.5571884999954 s** (47.2926 minutes); retained supervisor duration is
separately 2960 s. Frozen D0 projection is
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s`, 1.68 h. Both durations are below the
8 h cap. Valid-result machine charge is the runner wall above. No wall/nonfinite stop, extra
training, retuning, evaluation or model-selection exposure occurred at intake.

Missing peak RSS/scratch is `resources_unmeasured`, not a learner defect or resource result.
Source remains the accepted repaired E3 route; no scientific/numerical/RNG/checkpoint change,
new scope machinery or section-5 code budget breach was introduced. Accepted offline publication
coverage and 13/13 focused checks remain applicable; no repeated suite or new publication gap.
The earlier remote Git auto-gc preparation diagnostic remains an unresolved maintenance fact;
clean exact source/worktree creation succeeded and the existing run was not repaired or restarted.

The smallest supported update is one complete, competent large-row comparator seed. It prepares
an interpretable comparison but adds no evidence that D2 captures the structural margin. Existing
support for duration control and E2 `NEITHER`/weak alignment/seed dependence remain visible.
Under the owner's latest instruction, this result is the round's final cell: stop before
`large_d2_seed1`; no successor, retry or Pro is created.
