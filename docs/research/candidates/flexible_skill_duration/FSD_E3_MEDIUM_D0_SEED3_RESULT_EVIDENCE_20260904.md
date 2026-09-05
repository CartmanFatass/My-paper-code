# FSD E3 medium D0 seed 3 — result evidence

Date: 2026-09-04. Evidence class: **B — EXPLORE**. Cell: `medium_d0_seed3`, attempt 01.

**Valid complete D0 cell; E3 remains incomplete at 11/18. No E3 result branch is applied.**
The final 2,048-episode return is `0.40684948730468623`, episode standard error
`0.00022530152199174788`. Its ratio to the registered best fixed-clock reference is
`0.9590508796903731`, above this card's descriptive comparator-competence line `0.85`.
This is a single comparator seed on the medium row, not evidence of a D2 gain or a large-row
mechanism verdict. The absent paired D2 cell is not a zero observation.

## Question, assignment and ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`, `FSD-E3-HET-R01`.
The question is whether heterogeneous regional hazards make existing policy-gap interruption D2
useful against the strongest same-information fixed clock. The binding structure is temporal
abstraction and termination. Heterogeneous actionable renewal competes with a noisy policy gap,
seed-dependent optimization and team-renewal interference.

The completed cell is medium D0: hazards `(0.005, 0.10)`, `Delta=0.6`, fixed `k=5`, both
interruption costs infinity, both caps 5, age off. The unlaunched paired D2 cell keeps `c=0.25`,
individual cap 40 and team cap 400. Both use the same declared observations, information,
learner budget and keyed evaluation tapes. The host is the existing relay corridor, six agents
pinned three per region, `K=2`, `Z=4`, `H=400`, Bernoulli events, `rho=0`, no probe or coupling.

Training seed is 3. Four-thread CPU, numerical precision, learner/environment RNG, evaluator
master `770003`, episode ordering, normalizer synchronization and checkpoint format remain as
launched. This is adaptive B work selected after E2. It supports no C confirmation, transfer,
stable superiority, variable-population or direction-closure claim. No E3 tuning or arm change
was made from this outcome. The pre-existing card's sign-based rule and MEI-description exemption
for already-open ladders remain unchanged.

## Scientific and execution provenance

- Launch/source commit: `9c0a990537a8ffef58306429a1ff402550fc4b82`, pushed before launch.
- Execution node: configured `wsl_4070`, SSH `hmasd-wsl-node`, host `LAPTOP-U9TDKC8A`;
  Linux/Windows host-portable CPU route, with no device substitution.
- Detached task: `fsd_e3_medium_d0_seed3_20260904_01`; original wrapper/learner PIDs
  `74470` / `74473`. Supervisor finished at `2026-09-04T22:26:00Z`, exit 0, tmux inactive.
- Remote worktree: `/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01`.
- Original run root: that worktree's
  `temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.
- Verified local staging root:
  `C:/Projects/HMASD-worktrees/cm-fsd-seed3-resume-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_seed3_terminal_01/medium_d0_seed3`.
- Accepted canonical copy:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.
  It was created after confirming absence; all ten file hashes matched staging again.
- CM command and terminal verification record:
  `docs/Claude_docs/experiments/FSD_E3_MEDIUM_D0_SEED3_REMOTE_RUN_20260904.md`.
  Terminal CM receipt commit: `570670403f48ba0f2a3d64e6f47799a8354128d2`.
- The accepted repaired E3 runner has SHA-256
  `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1`.
  Its publication path and 13-test focused suite were already accepted at
  `69b24de052f19d3fbdf457358edd1a9c222585f4`. Source was unchanged for this invocation;
  the wider source difference is an E0 docstring example only. No repeated suite was run.

## Counts, receipts and exposure

CM verified all ten top-level artifact hashes against the original remote bytes after transfer.
The cell contains summary, manifest, preflight, metrics, interruptions, gaps, regional path,
evaluation records and final checkpoint. Twenty records are present in each learner/path stream,
with both regions present. The checkpoint is readable and retains float32 network tensors,
normalizer state and RNG state. Final E3 publication fields are complete, with no instability
or quarantine marker. Supervisor success was not used as a substitute for these checks.

| Quantity | Observed |
| --- | ---: |
| Completed rollouts | 20 of 20 |
| Lanes / steps per rollout | 16 / 400 |
| Environment transitions / training episodes | 128,000 / 320 |
| Coordinator samples per rollout | 1,280 in all 20 rollouts |
| Coordinator optimizer steps | 3,000 |
| Discoverer actor / critic optimizer steps | 72,000 / 72,000 |
| Team / individual discriminator optimizer steps | 300 / 1,200 |
| Total optimizer steps, all five groups | 148,500 |
| Evaluation records / total evaluation episodes | 4 / 3,584 |

The node-local receipt at `<run-root>/preflight.json` was assessed at
`2026-09-04T21:39:47.176686Z`, immediately before the exact runner in one supervised payload
joined with `&&`. Physical and effective availability were each `15,429,533,696` bytes;
both exceeded `4,294,967,296` bytes. All pass fields were true. No other invocation used this
receipt, and no new invocation was launched during collection or intake.

The CM receipt records all ten transfer hashes. Key raw evidence SHA-256 values are:

| Artifact | SHA-256 |
| --- | --- |
| summary.json | `4895b4c92ed28f5e36b4e92ca407a952b22011faac3218b0ede7233ed1b52a52` |
| eval.jsonl | `dcb14e5f52c1f6398c56901fd29457578cf11b4e2f358b47d8c1ca59c47eef9c` |
| path.jsonl | `75be6bb5b3280d2402e03557b3c3058d6dad892da8dd75050d33b625673f8cbb` |
| preflight.json | `d0cf5a6731fe6037b3b33dcaa5b08db25c2c25196de585e8865c8324bac97d89` |
| checkpoint_final.pt | `92fa61b25076d215769adc990aa203616c061214593cb9b9b89373df5eaea022` |

The machine-generated exposure is `||theta-theta_0||_2 / ||theta_0||_2`, evaluated in float64:

| Network | After rollout 1 | After rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.04080823588801077 | 0.11708156078197213 |
| Discoverer actor | 0.16684791425000306 | 0.8676006529359155 |
| Discoverer critic | 0.24597084848341444 | 0.9337023457398214 |
| Team discriminator | 0.009194614542247207 | 0.03807650598342086 |
| Individual discriminator | 0.012286576779590372 | 0.05680384685020319 |

All five groups moved and have nonzero updates. This is observed learner exposure, separate from
environment interactions and evaluation episodes. No model selection or extra training occurred
at intake.

## Direct observations

| Evaluation rollout | Episodes | Return mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.3883491210937492 | 0.0007100039457109109 |
| 10 | 512 | 0.3811855468749987 | 0.0005715164081601962 |
| 15 | 512 | 0.39958984374999895 | 0.0004620773947036388 |
| 20 | 2,048 | 0.40684948730468623 | 0.00022530152199174788 |

DM recomputation from the 2,048 finite, ordered final episode returns gives mean
`0.40684948730468623` and sample-based standard error `0.00022530152199174783`, agreeing
with the published record to floating-point rounding. This uncertainty is across evaluation
episodes for one trained seed; it is not across training seeds or a paired D2-D0 uncertainty.

Registered references remain `J_greedy=J_switch=0.56857875`, `J_best_fixed_k=0.4242209625375001`
at `k=5`, and structural duration margin `0.14435778746249994`. The independently recomputed
D0/reference ratio is `0.9590508796903731`. These quantities characterize this comparator;
they do not substitute for a D2 return or for the missing large-row pairs.

The native trace remains event → lease invalidation → public change flag and lagged cue → held
skill evaluation → renewal boundary → setup outage/fresh lease → service → shared return.
For the infinite-cost D0 arm the fixed clock supplies the renewal boundary. Membership stays
fixed; no join/leave, survivor state, replacement or censoring interpretation is involved.

Cumulative training-path quantities:

| Quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Hazard | 0.005 | 0.10 |
| Agent steps / primitive environment steps | 384,000 / 128,000 | 384,000 / 128,000 |
| Completed segments | 76,800 | 76,800 |
| Segment mean, minimum, maximum and every decile | 5 | 5 |
| Regional events | 637 | 12,700 |
| Gap-caused renewals / team-gap decisions | 0 / 0 | 0 / 0 |
| Event precision / recall | undefined / 0 | undefined / 0 |
| Cap boundaries / resets | 75,840 / 960 | 75,840 / 960 |
| Renewal-outage count / per-agent-step rate | 76,800 / 0.2 | 76,800 / 0.2 |
| Fresh correct-role service count / rate | 205,038 / 0.533953125 | 149,831 / 0.3901848958333333 |
| Stale service count | 0 | 0 |
| Stale correct-role opportunities | 1,630 | 33,308 |
| Mean shared-return contribution during training | 0.16018593750000001 | 0.11705546874999999 |

Undefined gap-renewal precision is the zero-denominator consequence of infinite costs, not
missing learner instrumentation. The regional path is present. The medium cell's large-row
event-path field is inapplicable; it is not a failed large-row measurement.

## Frozen rule and its applicability

The existing run-state instruction is applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

There are now 11 valid cells and seven unlaunched cells. Thus the aggregate rule is **not yet
applicable**. In particular, unlaunched large-row seeds are not failed-competence seeds, and an
absent D2 value is not zero. `G`, paired standard error and `Q` are not computed for this unpaired
cell. The card's branches remain unchanged:

1. **E3-COMPETENCE-BLOCKED:** fewer than two of three large-row seed pairs have a competent D0
   comparator. Report all observations; make no D2 gain claim.
2. **E3-H1-ACTIONABLE:** among competent large-row pairs, `G > 0` in at least two seeds and the
   `event_path` holds in at least those same two seeds. H1 receives preliminary support.
3. **E3-RETURN-WITHOUT-PATH:** `G > 0` in at least two competent seeds but the event path does not
   hold in two. D2 pays for a reason not identified as event-driven renewal.
4. **E3-H0-NO-ADVANTAGE:** `G <= 0` in at least two competent seeds. H0 receives preliminary
   support; this closes only `c=0.25` on the declared large row and budget.
5. **E3-UNSTABLE:** anything else. Report individual seeds and the row shape; do not select a
   mechanism polarity.

Competence remains `R_D0/J_k >= 0.85`. At the large row, `event_path` requires shorter
high-hazard mean segments, higher high-hazard gap-renewal rate per agent-step, and high-hazard
gap-renewal event precision above `0.5`. None is tested as an aggregate branch here.

DM's prediction remains `E3-H0-NO-ADVANTAGE`, pending complete E3 evidence. Owner's E3 prediction
is `not taken (unattended)`; actual owner reviews contain no E3 prediction reply. The prior E2
prediction is not an E3 prediction.

## Cost, deviations and bounded reading

Measured runner wall is `2687.7446834669972 s` (44.7957 minutes); supervisor duration is
2,773 seconds and also includes startup/teardown. The runner's prospective D0 cost law was
`[20*(64.6+0.769*150)+3584*0.46]*1.15=6034.786 s`, approximately 1.68 hours. Both observed
times are below the 8-hour per-cell cap. Twenty rollouts completed; no nonfinite stop or wall
truncation occurred. Accounted valid-cell machine usage is the measured runner wall above,
with the supervisor interval separately reported.

Peak RSS is null and the record is `resources_unmeasured`, as allowed by the repository telemetry
rule. Collected artifact payload is 67,857,158 bytes; it is not a peak-scratch measurement.
No missing learner measurement, source change, scientific/numerical/RNG/checkpoint change,
new engineering machinery or section-5 code budget breach was found. Previously accepted E3
publication-path coverage remains applicable; no new uncovered publication path was introduced.

The smallest update is a valid, competent medium-row D0 seed ready for its future paired D2
measurement. This strengthens the availability of the comparator, not H1 or H0. E2's monotone
duration response remains the strongest existing support for controllability; its `NEITHER`
verdict and weak event alignment remain contrary evidence for the event-driven benefit story.
This cell does not settle that story. The owner's execution-drain instruction now holds the
direction before `medium_d2_seed3`; six large-row cells also remain uncreated.
