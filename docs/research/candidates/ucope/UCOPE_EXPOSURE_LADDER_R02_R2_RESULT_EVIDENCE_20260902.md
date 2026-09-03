# UCOPE exposure ladder R02 — rung 2 result (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the object registered in
`UCOPE_SECTION11_RECAST_INTAKE_20260902.md` **section 9**, under owner decisions 2 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4, the portfolio decision
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`, and the owner
instruction to close the ladder (compliance note D.8).

**Question.** Same workload as R01 rung 2 — learning rate `3e-4` at `1,600` tail / `3,200` root
updates, arms `FT-XF-FLEX` and `FT-XF-BC`, three seeds, two group-disjoint folds — read under the
**per-arm** rule of intake section 9.4: did *each arm separately* realise the intended displacement
budget, and did either arm reach even-support competence?

**Claim ceiling: `B/EXPLORE`.** Everything below is a direct observation on the actually observed
panel of 3 seeds x 2 folds x 2 arms. Nothing here establishes acquisition polarity, COUNT/RAW
polarity, a conditioning or representation attribution, stable superiority, a seed-population
effect, generality in `k` or `N`, MARL/UAV relevance, transfer, safety, deployment or real-world
QoS. At three seeds no arm-comparison polarity is available. The intake supplies the reading rule
and this document does not go past it.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-2` |
| Ladder object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02` |
| Rung definition | lr `3e-4` at 1,600/3,200 tail/root updates |
| Evidence class | `B/EXPLORE` |
| Launch commit sha (HEAD at launch) | `905ca924661024d734d29cac773b59323626862b` |
| Bound source inventory | clean at that HEAD (14 files, `git status --porcelain` over those paths empty); the wider working tree carried 38 unrelated entries from concurrent sessions, recorded and not gating |
| Code object id inside the artifacts | `UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` (the B1 package both ladders reuse); the science object id above is carried in `run-record.json` |
| Run binding | kind `LADDER2_ADMITTED`, source aggregate `34c361f126135797bac273d18414e022b5ff534f248b333774480010538f0fe0` over 14 source files |
| Record format string | `UCOPE_EXPOSURE_LADDER_R01_RUNG1_RUN_RECORD_V1` — the record *schema* name, unchanged on purpose; object identity is in `science_object_id` / `ladder_object_id` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902/complete` |
| Branch published | **`R2-D NEITHER_ARM_MOVED`** (competence branch `NO_ARM_COMPETENT`), `complete: true`, nothing quarantined |

---

## 1. What is new, and what is byte-identical to R01 rung 2

R02 changes the reading rule only. Verified, not assumed:

- the 60 evaluation rows of this run are **byte-identical** to R01 rung 2's 60 rows;
- all 24 exposure rows are identical to R01 rung 2's on every field R01 recorded.

The counter-addressed RNG is keyed on `(namespace, seed, fold, index)` and never on the object
label, so R02 rung 2 reproduces R01 rung 2's training exactly. The only new recorded quantities are
the per-row `max_abs_coordinate_move` (largest absolute per-coordinate change over **all trained
coordinates of that arm**, so `FT-XF-FLEX`'s paired residual is inside its own statistic and
`FT-XF-BC`'s equals its Bellman-vector move) and the `per_arm` block.

The recast ledger is unchanged: `recorded_not_gating` = clean committed source inventory,
performance-ready assessment, resource projection caps, the exact-oracle competence predicate, the
acquisition / COUNT-RAW locks, execution topology; `still_gating` = the central 4 GiB admission, the
§4 integrity items, the §5.2 nonzero counts, one machine-generated exposure line, and §6.2
learner-side quarantine.

## 2. Resource admission (a launch condition, unchanged)

`scripts/hmasd_resource_preflight.py admit-memory`, run by the runner immediately before any RNG
master, model, optimizer or checkpoint existed; receipt at
`temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902/preflight.json`.

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `11,484,102,656` (10.70 GiB) |
| `effective_available_bytes` | `11,484,102,656` (10.70 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` | `GlobalMemoryStatusEx` |
| `captured_at` / `assessed_at` | `2026-09-03T02:46:54.994569Z` / `2026-09-03T02:46:55.021247Z` |

## 3. Commands actually run

```
git rev-parse HEAD
  -> 905ca924661024d734d29cac773b59323626862b

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py run \
  --output-root temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902 \
  --thread-cap 4 --rung 2 --ladder-object R02
  -> {"path": ".../exposure_ladder_r02_rung2_20260902/complete/run-record.json"}

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py validate \
  --complete-root temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902/complete
  -> {"branch": "NO_ARM_COMPETENT", "resources_unmeasured": false,
      "science_object_id": "UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-2", "valid": true}
```

## 4. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies | 12 (2 arms x 3 seeds x 2 folds) | 12 |
| Episodes generated | 122,880 | 122,880 |
| Environment transitions | — | 614,400 |
| Root optimizer updates | 3,200 x 12 = 38,400 | 38,400 |
| Tail optimizer updates | 1,600 x 12 = 19,200 | 19,200 |
| Root example exposures | 38,400 x 256 = 9,830,400 | 9,830,400 |
| Tail example exposures | 19,200 x 256 = 4,915,200 | 4,915,200 |
| Frozen-target materialisations | 12 (one per FT policy) | 12 events, 245,760 rows |
| Moving-target refreshes | 0 (no `MT-` arm in this object) | 0 |
| Checkpoints written | 5 roots `{40, 80, 160, 320, 3200}` x 12 = 60 | 60 |
| Exact policy evaluations | 60 x 8 contexts = 480 | 480 |
| Sampled evaluation episodes | 480 x 64 = 30,720 | 30,720 |
| Sampled evaluation transitions | — | 156,288 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | root 5,970, tail 4,935 |
| Gradient-norm maxima | — | root 8.116724, tail 10.296667 |

Every §5.2 count is nonzero and reconciles exactly.

## 5. Competence observation (recorded, deciding nothing)

Final checkpoint, root update 3,200. `C_even` is unchanged.

| Arm | Seed | Fold | finite | oracle root vector | max regret | min tail agreement | competent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-BC` | `00` | 0 | True | False | 0.268000000 | 0.000000 | False |
| `FT-XF-BC` | `00` | 1 | True | False | 0.268000000 | 0.000000 | False |
| `FT-XF-BC` | `01` | 0 | True | False | 0.268000000 | 0.000000 | False |
| `FT-XF-BC` | `01` | 1 | True | False | 0.189437101 | 0.000000 | False |
| `FT-XF-BC` | `02` | 0 | True | False | 0.148000000 | 0.000000 | False |
| `FT-XF-BC` | `02` | 1 | True | False | 0.148000000 | 0.000000 | False |
| `FT-XF-FLEX` | `00` | 0 | True | False | 0.100000000 | 0.611559 | False |
| `FT-XF-FLEX` | `00` | 1 | True | False | 0.074123271 | 0.479273 | False |
| `FT-XF-FLEX` | `01` | 0 | True | False | 0.073898660 | 0.788446 | False |
| `FT-XF-FLEX` | `01` | 1 | True | False | 0.030221036 | 0.764509 | False |
| `FT-XF-FLEX` | `02` | 0 | True | False | 0.081912234 | 0.479273 | False |
| `FT-XF-FLEX` | `02` | 1 | True | False | 0.070608669 | 0.520727 | False |

Per arm: `FT-XF-FLEX` 0 of 6 policies competent, 0 of 3 seeds passing, `B_COMPETENT = false`;
`FT-XF-BC` 0 of 6, 0 of 3, `B_COMPETENT = false`. Branch `NO_ARM_COMPETENT`. No policy matched the
exact oracle root vector — all 12 chose `IMMEDIATE` in all eight contexts, where the oracle chooses
`PROBE` at `LINKED-p17_20-c9_100`. Closest approaches at update 3,200: regret `0.030221036` against
the `0.02` gate and tail agreement `0.788446` against the `0.95` gate, in different policies.

These 60 rows are byte-identical to R01 rung 2's, and the instrumentation check
`UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01` (result 2026-09-02, 77 tests, all
passing) verified that each of these fields is a correct measurement on both arms.

## 6. The exposure line (a launch condition, §11.4), per policy and stage

`beta move` is R01's statistic (Bellman vector only); `all-coord move` is R02's (all trained
coordinates of that arm). Final checkpoint, root update 3,200 / tail update 1,600.

| Arm | Seed | Fold | Stage | displacement L2 | init scale L2 | ratio | beta move | all-coord move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-BC` | 00 | 0 | root | 0.878010 | 1.446244 | 0.607097 | 0.437747 | 0.437747 |
| `FT-XF-BC` | 00 | 0 | tail | 0.851351 | 1.550220 | 0.549181 | 0.417038 | 0.417038 |
| `FT-XF-BC` | 00 | 1 | root | 1.532788 | 1.805032 | 0.849175 | 0.843375 | 0.843375 |
| `FT-XF-BC` | 00 | 1 | tail | 0.561820 | 1.467383 | 0.382872 | 0.365717 | 0.365717 |
| `FT-XF-BC` | 01 | 0 | root | 1.233108 | 0.942638 | 1.308147 | 0.612136 | 0.612136 |
| `FT-XF-BC` | 01 | 0 | tail | 0.961001 | 1.472988 | 0.652416 | 0.495335 | 0.495335 |
| `FT-XF-BC` | 01 | 1 | root | 1.131058 | 1.359693 | 0.831848 | 0.640824 | 0.640824 |
| `FT-XF-BC` | 01 | 1 | tail | 0.393010 | 1.265327 | 0.310600 | **0.249392** | **0.249392** |
| `FT-XF-BC` | 02 | 0 | root | 0.566106 | 1.229253 | 0.460529 | 0.321863 | 0.321863 |
| `FT-XF-BC` | 02 | 0 | tail | 0.588505 | 1.727099 | 0.340748 | 0.369368 | 0.369368 |
| `FT-XF-BC` | 02 | 1 | root | 1.200983 | 1.320451 | 0.909525 | 0.692509 | 0.692509 |
| `FT-XF-BC` | 02 | 1 | tail | 0.632614 | 1.328049 | 0.476348 | 0.339870 | 0.339870 |
| `FT-XF-FLEX` | 00 | 0 | root | 1.723597 | 8.953642 | 0.192502 | 0.132471 | 0.298904 |
| `FT-XF-FLEX` | 00 | 0 | tail | 2.271667 | 9.102437 | 0.249567 | 0.079066 | 0.190950 |
| `FT-XF-FLEX` | 00 | 1 | root | 2.297807 | 9.220365 | 0.249210 | 0.075846 | 0.234921 |
| `FT-XF-FLEX` | 00 | 1 | tail | 2.010600 | 9.006284 | 0.223244 | 0.070453 | 0.250053 |
| `FT-XF-FLEX` | 01 | 0 | root | 1.485017 | 9.010496 | 0.164810 | 0.059071 | 0.134173 |
| `FT-XF-FLEX` | 01 | 0 | tail | 2.654210 | 8.934944 | 0.297059 | 0.070034 | 0.237132 |
| `FT-XF-FLEX` | 01 | 1 | root | 1.766047 | 9.112920 | 0.193796 | 0.092168 | 0.298364 |
| `FT-XF-FLEX` | 01 | 1 | tail | 1.624439 | 8.960461 | 0.181290 | 0.042410 | 0.150368 |
| `FT-XF-FLEX` | 02 | 0 | root | 1.534588 | 9.079610 | 0.169015 | 0.067830 | 0.182830 |
| `FT-XF-FLEX` | 02 | 0 | tail | 2.299247 | 9.042602 | 0.254268 | 0.072873 | 0.245055 |
| `FT-XF-FLEX` | 02 | 1 | root | 2.029866 | 9.225770 | 0.220021 | 0.068815 | 0.272202 |
| `FT-XF-FLEX` | 02 | 1 | tail | 0.970017 | 9.011697 | 0.107640 | **0.025254** | **0.107457** |

`learner_can_move_in_its_budget = true`.

Per-arm block as recorded in `run-record.json` `exposure_line.per_arm`:

| Arm | rows | min beta move | max beta move | **min all-coord move** | max all-coord move | threshold | residual inside |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-FLEX` | 12 | 0.025254 | 0.132471 | **0.107457** | 0.298904 | 0.30 | yes |
| `FT-XF-BC` | 12 | 0.249392 | 0.843375 | **0.249392** | 0.843375 | 0.30 | no |

## 7. The reading rule applied verbatim, with the deciding numbers

Intake section 9.4, applied exactly as written and using only the quantities named there.

1. **Competence.** No arm is `B_COMPETENT` — `FT-XF-FLEX` 0 of 3 seeds, `FT-XF-BC` 0 of 3 seeds,
   each requiring 2 of 3. **R2-A does not apply.**
2. **Movement, `FT-XF-FLEX`.** `m_FT-XF-FLEX = 0.107457` (minimum over that arm's 12 rows of the
   all-coordinate move; attained at seed `…fresh-02`, fold 1, tail stage). `t_FT-XF-FLEX = 0.30`.
   `0.107457 < 0.30` → **`NOT_MOVED`.**
3. **Movement, `FT-XF-BC`.** `m_FT-XF-BC = 0.249392` (seed `…fresh-01`, fold 1, tail stage; this arm
   has no residual, so the statistic equals R01's for this arm). `t_FT-XF-BC = 0.30`.
   `0.249392 < 0.30` → **`NOT_MOVED`.**
4. Neither arm `MOVED`, no arm `B_COMPETENT` → **`R2-D NEITHER_ARM_MOVED`.**

**Registered reading of `R2-D`:** the rung did not deliver the intended exposure increase for either
arm and is uninformative for the ladder's question. Nothing here says anything about mechanism A for
either arm.

**The ladder now closes on a stable, and rather striking, number.** Across the two rungs — a ten-fold
change in learning rate traded against a ten-fold change in update count, so that `steps x lr` is
`0.96` at both — the per-arm displacement floors are essentially unchanged:

| Arm | rung 1 `m_A` | rung 2 `m_A` | change |
| --- | --- | --- | --- |
| `FT-XF-FLEX` | 0.108116 | 0.107457 | −0.61 % |
| `FT-XF-BC` | 0.250245 | 0.249392 | −0.34 % |

The same policy and stage sets the floor at both rungs for each arm (`…fresh-02`/fold 1/tail for
FLEX, `…fresh-01`/fold 1/tail for BC). Ten times the optimizer budget at one tenth the step size
moved the least-moving coordinate of each arm by less than one percent. That is an observation about
where the optimizer settles, not a claim about why; it is what motivates the training-target
diagnostic object registered separately.

`FT-XF-BC` being `NOT_MOVED` at this rung was declared in advance in intake section 9.6 (its rung-2
number was already published as `0.249392`). The quantity that was genuinely unseen when the rule was
fixed is `m_FT-XF-FLEX = 0.107457`; including the residual raises it 4.25x over R01's beta-only
`0.025254`, and it is still below `0.30`.

## 8. Verbatim summary lines

```
science_object_id  UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-2
ladder_object_id   UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02
branch             NO_ARM_COMPETENT  (reading rule branch: R2-D NEITHER_ARM_MOVED)
valid              true
complete           true
resources_unmeasured  false
m_FT-XF-FLEX = 0.10745692253112793   t = 0.30   NOT_MOVED
m_FT-XF-BC   = 0.24939179420471191   t = 0.30   NOT_MOVED
```

## 9. Resource telemetry (measured; not `resources_unmeasured`)

| Field | Value |
| --- | --- |
| `wall_seconds` | `631.0644205999997` |
| `cpu_seconds` | `1515.8125` |
| `peak_rss_bytes` | `432,537,600` (412.50 MiB) |
| `scratch_bytes` | `9,204,192` |
| `durable_bytes` | `9,203,130` |
| `resources_unmeasured` | `false`, `unmeasured_reasons: []` |
| `gating` / `downgrade_only` | `false` / `true` (owner decision 7) |

CPU seconds exceed wall seconds because this run used `torch_intraop_threads = 4`; R01 rung 2 ran at
`1` intraop thread (359.29 s wall, 356.58 s CPU). The evaluation rows are byte-identical across the
two, so the thread count changed timing and nothing else. Other agent sessions were running on the
same machine throughout, so wall time is not comparable to R01's.

## 10. Deviations

1. **CPU threads.** R02 rung 2 ran with `--thread-cap 4` (the instruction's ceiling); R01 rung 2 ran
   at 1. Recorded, not gating; determinism is demonstrated by the byte-identical evaluation rows.
2. **Record format string** still reads `UCOPE_EXPOSURE_LADDER_R01_RUNG1_RUN_RECORD_V1` — a record
   *schema* name, deliberately unchanged; the object identity is in `science_object_id` and
   `ladder_object_id`.
3. **Run binding kind** `LADDER2_ADMITTED`, because R02 rung 2 reuses R01 rung 2's frozen `LADDER2`
   `ScoutConfig` mode without modification.
4. **The wider working tree was dirty** (38 entries) from concurrent unrelated sessions. The bound
   14-file source inventory was clean at HEAD and is recorded with per-file digests; working-tree
   cleanliness is a recorded field, not a gate, under §11.4.
5. **Rung 3 was not run**, per instruction. The three registered rungs of the R01 ladder therefore
   remain two-run; R02 registered and ran the same two.

## 11. Could not verify

- Whether either arm would cross `0.30` at any other rung or schedule: rung 3 was not run and no
  further R02 rung is registered.
- Why the learned coefficients settle where they do. Nothing in this object separates the target
  package, the objective's own fixed point, the training order or fold coupling; that is the
  question of the separately carded training-target diagnostic object.
- Any behaviour of the whitening discriminator: it is held by the owner and was neither read nor run.
- Anything about the `MT-XF-FLEX` arm, which is not part of either ladder object.

## 12. Interpretation boundary

`R2-D` is an uninformative branch by construction: it says the rung did not realise the intended
displacement for either arm, so it supports no statement about whether optimizer exposure explains
the observed incompetence. It is **not** evidence that the learners cannot become competent, that
one arm is better than the other, or that the ladder has been falsified. What the two R02 rungs
jointly record is narrower and firmer: on this host, under two schedules with the same `steps x lr`
budget, each arm leaves at least one coordinate almost exactly as far from its initialisation as the
other schedule did, and the arm that can move 4,870 coordinates does not use that freedom to move its
least-moving one. Whether that is a property of the target package, of the objective's fixed point,
of the training order, or of the optimizer is not decided here.
