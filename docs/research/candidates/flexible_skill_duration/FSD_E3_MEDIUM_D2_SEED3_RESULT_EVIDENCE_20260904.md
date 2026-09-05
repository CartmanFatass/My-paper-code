# FSD E3 medium D2 seed 3 — result evidence

Intake date: 2026-09-04 PDT. Terminal: 2026-09-05 UTC. Class: **B/EXPLORE**.
Cell: `medium_d2_seed3`, attempt 01, binding card `FSD-E3-HET-R01`.

**Valid complete treatment cell; E3 is incomplete at 12/18. No aggregate branch is applied.**
The final single-cell return is `0.35348229980468726`, episode standard error
`0.000670192216097249`. These are raw treatment observations, not a paired gain, a row-shape
comparison or a large-row mechanism verdict.

## Assignment, native trace and claim ceiling

Binding card: `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`.
The question remains whether policy-gap renewal under heterogeneous regional hazards improves
native return over the strongest same-information fixed clock. Binding structure is temporal
abstraction/termination; noisy gaps, optimizer heterogeneity and team-renewal interference are
the live alternatives to useful event-linked renewal.

This medium-row treatment uses hazards `(0.005,0.10)`, `Delta=0.6`, seed 3, `c=c_Z=0.25`,
individual/team caps `40/400`, interruption delta 1 and age off. The registered comparator is
D0 with exact best `k=5` and infinite costs. Observation, action, seed, training-transition budget
and keyed evaluation population are unchanged. Six entities are pinned three per region,
`K=2`, `Z=4`, horizon 400, Bernoulli events, `rho=0`, no probe or coupling.

Native trace: regional event -> lease invalidation -> public change flag and lagged cue -> held
skill gap -> individual/team renewal -> setup-outage step and fresh lease -> service -> shared
return. Membership and entity identity are fixed, with no join/leave, rejoin, replacement,
survivor-state or censoring quantity. CPU/four-thread, numerical precision, RNG/tapes,
normalizer synchronization and checkpoint format preserve the accepted implementation. Host
portability is Windows/Linux CPU; no CUDA or cross-host bit-identity claim is added.

The ceiling remains preliminary B mechanism evidence on the declared corridor rows/budget.
There is no C consumption, confirmation, transfer, stable superiority or direction closure.
The already-open card retains its original sign rule; no retrospective MEI is introduced.

## Provenance and technical acceptance

- Exact pushed launch SHA: `31bfecd79fc0f708546786ee26dfd8faa9e85dfb`.
- Node: `wsl_4070`, `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Sole accepted task: `fsd_e3_medium_d2_seed3_20260904_01`; wrapper/learner PIDs `106154/106170`.
- Original remote cwd: `/home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01`;
  root under it: `temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3`.
- Distinct verified staging:
  `C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_medium_d2_seed3_terminal_01/medium_d2_seed3`.
- Accepted canonical copy:
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3`.
- Exact command, terminal checks and all ten transfer hashes:
  `docs/Claude_docs/experiments/FSD_E3_MEDIUM_D2_SEED3_REMOTE_RUN_20260904.md`.
  Accepted CM terminal commit: `6b0669394eec563e286b61833879e52847be3f41`.
  Summary SHA-256: `7cee34416a1508b900b06715d514273bc195e540109be181c747302595d0167c`.

CM directly verified `finished`, exit 0, tmux inactive. The retained log ends at
`2026-09-05T00:29:52Z` with duration **2603 s**. Later status uptime measures time since start,
not elapsed experiment time, and is not substituted for this duration. The earlier SSH timeout
was an observation interruption; subsequent terminal observation resolved it without another
launch, admission or source change.

CM verified complete E3 publication, 20 learner/path records in each stream, both regions,
four ordered per-episode evaluations, first/final exposure equality with learner logs, finite
learner values and checkpoint tensors/optimizer states. The readable 64,782,527-byte checkpoint
contains all five optimizers, coordinator/discoverer value normalizers and
`hmasd_rollout_sampler_rng_v1`; network tensors are float32. Ten remote/staged hashes matched,
then all ten canonical hashes matched after copying only to an absent cell. No prior valid or
quarantined evidence was overwritten. This is evidence readability, not resume equivalence.

## Counts, admission and exposure

| Quantity | Observed |
| --- | ---: |
| Rollouts requested/completed | 20/20 |
| Lanes/primitive steps per rollout | 16/400 |
| Transitions/training episodes | 128,000/320 |
| Coordinator optimizer steps | 3,075 |
| Discoverer actor/critic optimizer steps | 9,000/9,000 |
| Team/individual discriminator optimizer steps | 300/1,200 |
| Total optimizer steps across five groups | 22,575 |
| Evaluation records/episodes | 4/3,584 |

Environment exposure and optimizer exposure are separate quantities; the table reports actual
updates and does not infer equal optimizer counts from equal transition budgets.

The original immediate destination-node receipt `<run-root>/preflight.json`, assessed at
`2026-09-04T23:46:29.300533Z`, reports physical and effective available memory each
`15,432,294,400` bytes, above the `4,294,967,296`-byte floor, with all pass fields true. Its
admission and the exact runner shared one supervisor payload joined by `&&`; the receipt was
not reused. No training or new evaluation was performed during collection/intake.

Machine-generated float64 `||theta-theta_0||_2 / ||theta_0||_2`:

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| Coordinator | 0.028561278072037403 | 0.12703892421509116 |
| Discoverer actor | 0.07535687324368119 | 0.4260967307456796 |
| Discoverer critic | 0.10545783232374614 | 0.40127404889520485 |
| Team discriminator | 0.013571879290845029 | 0.05824783929347061 |
| Individual discriminator | 0.016231476440611046 | 0.08319374434299935 |

## Direct single-cell observations

| Rollout | Episodes | Return mean | Episode standard error |
| --- | ---: | ---: | ---: |
| 5 | 512 | 0.21447167968749947 | 0.0027773935314051156 |
| 10 | 512 | 0.3022158203124993 | 0.0017377939757053295 |
| 15 | 512 | 0.31425976562499924 | 0.0016345603021624894 |
| 20 | 2,048 | 0.35348229980468726 | 0.000670192216097249 |

DM recomputed every mean and sample-based standard error from the corresponding finite ordered
episode returns; all four exactly match the reported numbers. Episode IDs are `0..n-1` at each
checkpoint. This uncertainty is for one trained seed's episode population, not training-seed
stability or paired-arm uncertainty.

Cumulative training-path observations are retained without applying the large-row branch:

| Quantity | Low-hazard region | High-hazard region |
| --- | ---: | ---: |
| Agent steps/environment steps | 384,000/128,000 | 384,000/128,000 |
| Segment count | 31,073 | 31,515 |
| Mean segment length | 12.357995687574421 | 12.184673964778677 |
| Segment 10th–90th deciles | 1,1,1,1,1,4,15,40,40 | 1,1,1,1,1,4,14,40,40 |
| Regional events | 637 | 12,700 |
| Gap renewals | 23,752 | 24,373 |
| Gap renewals per agent step | 0.06185416666666667 | 0.06347135416666666 |
| Gap-renewal event precision | 0.028292354328056584 | 0.3920321667418865 |
| Event recall | 0.40345368916797486 | 0.25606299212598427 |
| Team-gap decisions | 5,039 | 5,039 |
| Cap/reset boundaries | 6,361/960 | 6,182/960 |
| Renewal-outage count | 31,073 | 31,515 |
| Fresh correct-role service count | 208,735 | 64,400 |
| Stale service/stale correct-role opportunities | 0/12,429 | 0/119,729 |
| Mean shared-return contribution during training | 0.16307421875 | 0.050312499999999996 |

The two recorded team counts describe the same team decisions from each regional record; they
are not summed into independent events. Raw medium-row quantities do not stand in for missing
large-row measurements. D0 competence and large-row event-path summary fields are inapplicable
to this medium D2 cell; their null values are not learner instrumentation defects.

## Rule, cost, deviations and bounded reading

Rule applied verbatim:

> Do not apply the frozen E3 result rule until all 18 required invocations are validly complete.

There are **12 valid cells**, zero running at this intake, and six unlaunched large-row cells.
Therefore no `G`, paired standard error, `Q`, row-shape comparison or aggregate E3 branch is
computed here. The five card branches, their order, comparator competence line `0.85` and the
large-row three-part event-path rule remain unchanged. Missing large-row pairs are not failures
or zero effects. DM prediction `E3-H0-NO-ADVANTAGE` remains unscored; owner prediction is
`not taken (unattended)`, with no reply found at this boundary.

Measured runner wall is **2525.5407063739985 s** (42.0923 minutes), and retained supervisor
duration is separately 2603 s. The frozen D2 projection is
`[20*(64.6+0.769*750)+3584*0.46]*1.15=16646.986 s`, reported as 4.63 h; both observed
durations are below the 8 h cap. Valid-result machine usage increases by the measured runner
wall above. No wall/nonfinite truncation, selection exposure or extra learner invocation occurred.

Peak RSS is null, `resources_unmeasured`; payload 67,315,167 bytes is not peak scratch. Resource
limitations do not annul this non-resource claim. There was no source change, scope-section-4
machinery, section-5 code-budget breach, numerical/RNG/checkpoint change or missing required
learner output. The accepted repair's offline publication coverage and 13/13 focused suite
remain applicable; no new suite or uncovered publication path was introduced.

The smallest supported update is a valid medium treatment cell with a measured native path and
positive learner exposure. No new mechanism-level conclusion is entered in `DIRECTION.md`.
Existing support remains controllable durations; E2 `NEITHER`, weak alignment and seed dependence
remain contrary evidence. The next discriminator is the unchanged full matrix, completed by
large-row D0/D2 seeds 1, 2 and 3.
