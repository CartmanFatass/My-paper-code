# UCOPE exposure ladder R02 — rung 1 result (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the object registered in
`UCOPE_SECTION11_RECAST_INTAKE_20260902.md` **section 9**, under owner decisions 2 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`.

**Question.** Same workload as R01 rung 1 — learning rate `3e-3` at the frozen `160` tail / `320`
root updates, arms `FT-XF-FLEX` and `FT-XF-BC`, three seeds, two group-disjoint folds — read under a
**per-arm** rule: did *each arm separately* realise the intended displacement budget, and did either
arm reach even-support competence?

**Claim ceiling: `B/EXPLORE`.** Everything below is a direct observation on the actually observed
panel of 3 seeds x 2 folds x 2 arms. Nothing here establishes acquisition polarity, COUNT/RAW
polarity, a conditioning or representation attribution, stable superiority, a seed-population
effect, generality in `k` or `N`, MARL/UAV relevance, transfer, safety, deployment or real-world
QoS. At three seeds no arm-comparison polarity is available. The intake supplies the reading rule
and this document does not go past it.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-1` |
| Ladder object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02` |
| Rung definition | lr `3e-3` at the frozen 160/320 tail/root updates |
| Evidence class | `B/EXPLORE` |
| Launch commit sha (HEAD at launch) | `9ef1b36b68b27160975df202a00bda08f1214c28` — "Register UCOPE exposure ladder R02 with a per-arm reading rule" |
| Bound source inventory | clean at that HEAD (14 files, `git status --porcelain` over those paths empty); the wider working tree carried 38 unrelated entries from concurrent sessions, which is recorded and not gating |
| Code object id inside the artifacts | `UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` (the B1 package both ladders reuse); the science object id above is carried in `run-record.json` |
| Run binding | kind `LADDER1_ADMITTED` (R02 rung 1 reuses R01 rung 1's frozen `LADDER1` config mode unchanged), source aggregate `34c361f126135797bac273d18414e022b5ff534f248b333774480010538f0fe0` over 14 source files |
| Record format string | `UCOPE_EXPOSURE_LADDER_R01_RUNG1_RUN_RECORD_V1` — the record *schema* name, unchanged on purpose; the object identity is in `science_object_id` / `ladder_object_id` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/exposure_ladder_r02_rung1_20260902/complete` |
| Branch published | **`R2-D NEITHER_ARM_MOVED`** (competence branch `NO_ARM_COMPETENT`), `complete: true`, nothing quarantined |

---

## 1. What is new in R02, and what is byte-identical to R01

R02 changes the **reading rule only**. The workload, arms, seeds, folds, host, oracle, competence
predicate, batch law, episode count, checkpoint cadence and counter-addressed RNG are R01's, and the
RNG is keyed on `(namespace, seed, fold, index)` and never on the object label. Verified, not
assumed:

- the 48 evaluation rows of this run are **byte-identical** to R01 rung 1's 48 rows
  (`json.dumps(..., sort_keys=True)` equality);
- all 24 exposure rows are identical to R01 rung 1's on every field R01 recorded
  (`parameter_displacement_l2`, `initialisation_scale_l2`, `beta_displacement_l2`,
  `beta_max_abs_coordinate_move` and identity).

What is genuinely new is one recorded quantity and one rule:

- `exposure_line` now emits a per-row `max_abs_coordinate_move` — the largest absolute
  per-coordinate change over **all trained coordinates of that arm** — and a `per_arm` block. For
  `FT-XF-BC` this equals its `beta_max_abs_coordinate_move` exactly (no residual exists). For
  `FT-XF-FLEX` it includes the paired residual's 4,865 tail coordinates, which R01's statistic
  excluded.
- the branch is decided **per arm**, each arm's own minimum against its own threshold, so no single
  policy of one arm can fix the branch for the other.

The recast ledger is unchanged: `recorded_not_gating` = clean committed source inventory,
performance-ready assessment, resource projection caps, the exact-oracle competence predicate, the
acquisition / COUNT-RAW locks, execution topology; `still_gating` = the central 4 GiB admission, the
§4 integrity items, the §5.2 nonzero counts, one machine-generated exposure line, and §6.2
learner-side quarantine.

## 2. Resource admission (a launch condition, unchanged)

`scripts/hmasd_resource_preflight.py admit-memory`, run by the runner immediately before any RNG
master, model, optimizer or checkpoint existed; receipt at
`temp/directions/ucope/exp/exposure_ladder_r02_rung1_20260902/preflight.json`.

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `10,943,807,488` (10.19 GiB) |
| `effective_available_bytes` | `10,943,807,488` (10.19 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` | `GlobalMemoryStatusEx` |
| `captured_at` / `assessed_at` | `2026-09-03T02:29:32.596028Z` / `2026-09-03T02:29:32.626617Z` |

## 3. Commands actually run

```
git rev-parse HEAD
  -> 9ef1b36b68b27160975df202a00bda08f1214c28

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py run \
  --output-root temp/directions/ucope/exp/exposure_ladder_r02_rung1_20260902 \
  --thread-cap 4 --rung 1 --ladder-object R02
  -> {"path": ".../exposure_ladder_r02_rung1_20260902/complete/run-record.json"}

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py validate \
  --complete-root temp/directions/ucope/exp/exposure_ladder_r02_rung1_20260902/complete
  -> {"branch": "NO_ARM_COMPETENT", "resources_unmeasured": false,
      "science_object_id": "UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-1", "valid": true}
```

## 4. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies | 12 (2 arms x 3 seeds x 2 folds) | 12 |
| Episodes generated | 122,880 | 122,880 |
| Environment transitions | — | 614,400 |
| Root optimizer updates | 320 x 12 = 3,840 | 3,840 |
| Tail optimizer updates | 160 x 12 = 1,920 | 1,920 |
| Root example exposures | 3,840 x 256 = 983,040 | 983,040 |
| Tail example exposures | 1,920 x 256 = 491,520 | 491,520 |
| Frozen-target materialisations | 12 (one per FT policy) | 12 events, 245,760 rows |
| Moving-target refreshes | 0 (no `MT-` arm in this object) | 0 |
| Checkpoints written | 4 roots x 12 = 48 | 48 |
| Exact policy evaluations | 48 x 8 contexts = 384 | 384 |
| Sampled evaluation episodes | 384 x 64 = 24,576 | 24,576 |
| Sampled evaluation transitions | — | 106,368 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | root 655, tail 576 |
| Gradient-norm maxima | — | root 8.214277, tail 9.768999 |

Every §5.2 count is nonzero and reconciles exactly.

## 5. Competence observation (recorded, deciding nothing)

Final checkpoint, root update 320. `C_even` is unchanged.

| Arm | Seed | Fold | finite | oracle root vector | max regret | min tail agreement | competent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-BC` | `00` | 0 | True | False | 0.218000000 | 0.000000 | False |
| `FT-XF-BC` | `00` | 1 | True | False | 0.268000000 | 0.000000 | False |
| `FT-XF-BC` | `01` | 0 | True | False | 0.268000000 | 0.000000 | False |
| `FT-XF-BC` | `01` | 1 | True | False | 0.189437101 | 0.000000 | False |
| `FT-XF-BC` | `02` | 0 | True | False | 0.148000000 | 0.000000 | False |
| `FT-XF-BC` | `02` | 1 | True | False | 0.148000000 | 0.000000 | False |
| `FT-XF-FLEX` | `00` | 0 | True | False | 0.100000000 | 1.000000 | False |
| `FT-XF-FLEX` | `00` | 1 | True | False | 0.069437101 | 0.764509 | False |
| `FT-XF-FLEX` | `01` | 0 | True | False | 0.069437101 | 0.479273 | False |
| `FT-XF-FLEX` | `01` | 1 | True | False | 0.028562899 | 1.000000 | False |
| `FT-XF-FLEX` | `02` | 0 | True | False | 0.148000000 | 0.000000 | False |
| `FT-XF-FLEX` | `02` | 1 | True | False | 0.048000000 | 0.611559 | False |

Per arm: `FT-XF-FLEX` 0 of 6 policies competent, 0 of 6 seeds passing, `B_COMPETENT = false`;
`FT-XF-BC` 0 of 6, 0 of 6, `B_COMPETENT = false`. Branch `NO_ARM_COMPETENT`. No policy matched the
exact oracle root vector (all 12 chose `IMMEDIATE` in all eight contexts; the oracle chooses `PROBE`
at `LINKED-p17_20-c9_100`). Closest approaches: regret `0.028562899` against the `0.02` gate
(`FT-XF-FLEX/01/fold 1`), tail agreement `1.000000` against the `0.95` gate (two `FT-XF-FLEX`
policies) — but never both in the same policy, and never with the oracle root vector.

These 48 rows are byte-identical to R01 rung 1's, and the instrumentation check
`UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01` (result dated 2026-09-02, 77 tests,
all passing) verified that each of these fields is a correct measurement, that the predicate returns
`True` for an exactly-optimal policy on both arms, and that `FT-XF-BC`'s `0.000000` is a property of
the learned policies rather than of the instrument.

## 6. The exposure line (a launch condition, §11.4), per policy and stage

Machine-generated by the runner from this run's own final checkpoints against the exact
deterministic initialisation of the same arm/seed/fold. `beta move` is R01's statistic
(Bellman vector only); `all-coord move` is R02's (all trained coordinates of that arm).

| Arm | Seed | Fold | Stage | displacement L2 | init scale L2 | ratio | beta move | all-coord move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-BC` | 00 | 0 | root | 0.882420 | 1.446244 | 0.610146 | 0.421736 | 0.421736 |
| `FT-XF-BC` | 00 | 0 | tail | 0.870836 | 1.550220 | 0.561750 | 0.424281 | 0.424281 |
| `FT-XF-BC` | 00 | 1 | root | 1.515004 | 1.805032 | 0.839323 | 0.833301 | 0.833301 |
| `FT-XF-BC` | 00 | 1 | tail | 0.546454 | 1.467383 | 0.372400 | 0.363256 | 0.363256 |
| `FT-XF-BC` | 01 | 0 | root | 1.261378 | 0.942638 | 1.338137 | 0.608588 | 0.608588 |
| `FT-XF-BC` | 01 | 0 | tail | 0.977361 | 1.472988 | 0.663523 | 0.495109 | 0.495109 |
| `FT-XF-BC` | 01 | 1 | root | 1.134736 | 1.359693 | 0.834553 | 0.615725 | 0.615725 |
| `FT-XF-BC` | 01 | 1 | tail | 0.394405 | 1.265327 | 0.311702 | **0.250245** | **0.250245** |
| `FT-XF-BC` | 02 | 0 | root | 0.555818 | 1.229253 | 0.452159 | 0.318753 | 0.318753 |
| `FT-XF-BC` | 02 | 0 | tail | 0.581466 | 1.727099 | 0.336672 | 0.365870 | 0.365870 |
| `FT-XF-BC` | 02 | 1 | root | 1.184795 | 1.320451 | 0.897265 | 0.673930 | 0.673930 |
| `FT-XF-BC` | 02 | 1 | tail | 0.637967 | 1.328049 | 0.480379 | 0.338913 | 0.338913 |
| `FT-XF-FLEX` | 00 | 0 | root | 1.778138 | 8.953642 | 0.198594 | 0.089176 | 0.220516 |
| `FT-XF-FLEX` | 00 | 0 | tail | 2.417135 | 9.102437 | 0.265548 | 0.128577 | 0.199232 |
| `FT-XF-FLEX` | 00 | 1 | root | 2.372498 | 9.220365 | 0.257311 | 0.112537 | 0.221577 |
| `FT-XF-FLEX` | 00 | 1 | tail | 1.940658 | 9.006284 | 0.215478 | 0.126136 | 0.212331 |
| `FT-XF-FLEX` | 01 | 0 | root | 1.949576 | 9.010496 | 0.216367 | 0.077334 | 0.200745 |
| `FT-XF-FLEX` | 01 | 0 | tail | 2.656543 | 8.934944 | 0.297321 | 0.131479 | 0.296063 |
| `FT-XF-FLEX` | 01 | 1 | root | 1.749412 | 9.112920 | 0.191971 | 0.113220 | 0.172840 |
| `FT-XF-FLEX` | 01 | 1 | tail | 1.820693 | 8.960461 | 0.203192 | 0.055614 | 0.169857 |
| `FT-XF-FLEX` | 02 | 0 | root | 1.844164 | 9.079610 | 0.203110 | 0.100170 | 0.188154 |
| `FT-XF-FLEX` | 02 | 0 | tail | 2.048313 | 9.042602 | 0.226518 | 0.104321 | 0.170139 |
| `FT-XF-FLEX` | 02 | 1 | root | 2.241179 | 9.225770 | 0.242926 | 0.107826 | 0.130041 |
| `FT-XF-FLEX` | 02 | 1 | tail | 1.252568 | 9.011697 | 0.138994 | **0.046434** | **0.108116** |

`learner_can_move_in_its_budget = true` (every beta coordinate move is strictly positive).

Per-arm block as recorded in `run-record.json` `exposure_line.per_arm`:

| Arm | rows | min beta move | max beta move | **min all-coord move** | max all-coord move | threshold | residual inside |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FT-XF-FLEX` | 12 | 0.046434 | 0.131479 | **0.108116** | 0.296063 | 0.30 | yes |
| `FT-XF-BC` | 12 | 0.250245 | 0.833301 | **0.250245** | 0.833301 | 0.30 | no |

## 7. The reading rule applied verbatim, with the deciding numbers

Intake section 9.4, applied exactly as written and using only the quantities named there.

1. **Competence.** No arm is `B_COMPETENT` — `FT-XF-FLEX` 0 of 3 seeds, `FT-XF-BC` 0 of 3 seeds,
   each requiring 2 of 3. So **R2-A does not apply.**
2. **Movement, `FT-XF-FLEX`.** `m_FT-XF-FLEX = 0.108116` (minimum over that arm's 12 rows of the
   all-coordinate move; attained at seed `…fresh-02`, fold 1, tail stage). Threshold
   `t_FT-XF-FLEX = 0.30`. `0.108116 < 0.30` → **`NOT_MOVED`.**
3. **Movement, `FT-XF-BC`.** `m_FT-XF-BC = 0.250245` (seed `…fresh-01`, fold 1, tail stage; this arm
   has no residual, so the statistic equals R01's for this arm). Threshold `t_FT-XF-BC = 0.30`.
   `0.250245 < 0.30` → **`NOT_MOVED`.**
4. Neither arm `MOVED`, no arm `B_COMPETENT` → **`R2-D NEITHER_ARM_MOVED`.**

**Registered reading of `R2-D`:** the rung did not deliver the intended exposure increase for either
arm and is uninformative for the ladder's question. Nothing here says anything about mechanism A for
either arm.

**What the per-arm fix actually changed, quantitatively.** Bringing `FT-XF-FLEX`'s residual inside
its own statistic raises that arm's minimum by a factor of 2.33, from `0.046434` to `0.108116` —
the same policy and stage (`…fresh-02` / fold 1 / tail) sets it in both cases. `FT-XF-BC`'s number
is unchanged at `0.250245` by construction. So R01's `m = 0.046434` did materially understate
`FT-XF-FLEX`'s movement, and R01's single cross-arm minimum did let one arm's number decide the
whole rung; but with both defects removed, the rung-1 branch is still a not-moved branch, now for
both arms independently rather than for one arm's tail policy. R01 rung 1's published `R1-C` reading
is not disturbed by this.

`FT-XF-BC` being `NOT_MOVED` was declared in advance in intake section 9.6 (its rung-1 number was
already published as `0.250245`), so the only quantity this run decided that was genuinely unseen
when the rule was fixed is `m_FT-XF-FLEX = 0.108116`.

## 8. Verbatim summary lines

```
science_object_id  UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02-RUNG-1
ladder_object_id   UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02
branch             NO_ARM_COMPETENT  (reading rule branch: R2-D NEITHER_ARM_MOVED)
valid              true
complete           true
resources_unmeasured  false
m_FT-XF-FLEX = 0.10811613500118256   t = 0.30   NOT_MOVED
m_FT-XF-BC   = 0.25024527311325073   t = 0.30   NOT_MOVED
```

## 9. Resource telemetry (measured; not `resources_unmeasured`)

| Field | Value |
| --- | --- |
| `wall_seconds` | `108.65446249999513` |
| `cpu_seconds` | `198.3125` |
| `peak_rss_bytes` | `433,033,216` (412.97 MiB) |
| `scratch_bytes` | `7,363,558` |
| `durable_bytes` | `7,362,504` |
| `resources_unmeasured` | `false`, `unmeasured_reasons: []` |
| `gating` / `downgrade_only` | `false` / `true` (owner decision 7) |

CPU seconds exceed wall seconds because this run used `torch_intraop_threads = 4`; R01 rung 1 ran at
`1` intraop thread (89.29 s wall, 87.56 s CPU). The evaluation rows are byte-identical across the
two, so the thread count changed the timing and nothing else. Two other agent sessions were running
on the same machine throughout, which is expected and is why wall time is not comparable to R01's.

## 10. Deviations

1. **CPU threads.** R02 rung 1 ran with `--thread-cap 4` (the instruction's ceiling); R01 rung 1 ran
   at 1. Recorded, not gating; determinism is demonstrated by the byte-identical evaluation rows.
2. **Record format string.** `run-record.json` still carries
   `format: UCOPE_EXPOSURE_LADDER_R01_RUNG1_RUN_RECORD_V1`. That string names the record *schema*,
   which is unchanged apart from two added exposure fields; the object identity is carried
   explicitly in `science_object_id` and `ladder_object_id`. It was left alone rather than renamed
   because renaming it would invalidate nothing and confuse the already-published R01 records.
3. **Run binding kind.** `LADDER1_ADMITTED`, because R02 rung 1 reuses R01 rung 1's frozen `LADDER1`
   `ScoutConfig` mode without modification. The binding's `source_aggregate` differs from R01's
   (`34c361f1…` vs `882ff69e…`) because `contract.py` gained the R02 identifiers.
4. **`exposure_line` gained two recorded fields** (`max_abs_coordinate_move` per row and the
   `per_arm` block) between R01 rung 2 and this run. Every field R01 recorded is unchanged in name,
   definition and value; this was verified row by row against R01 rung 1's published exposure line.
5. **The wider working tree was dirty** (38 entries) from concurrent unrelated sessions. The bound
   14-file source inventory was clean at HEAD and is recorded with per-file digests; working-tree
   cleanliness is a recorded field, not a gate, under §11.4.

## 11. Could not verify

- Whether `FT-XF-FLEX` would cross `0.30` at some other rung: rung 2 of R02 is registered but was
  not run, per instruction.
- Why the two learners settle where they do — objective, target package, basis span, conditioning,
  fold coupling and seed instability are untouched by this object.
- Any behaviour of the whitening discriminator: it is held by the owner and was neither read nor run.
- Anything about the `MT-XF-FLEX` arm, which is not part of either ladder object.

## 12. Interpretation boundary

`R2-D` is an uninformative branch by construction: it says the rung did not realise the intended
displacement for either arm, so it supports no statement about whether optimizer exposure explains
the observed incompetence. It is **not** evidence that the learners cannot become competent, that
one arm is better than the other, or that the exposure ladder as a whole has failed. It does record
one new and precise thing: with the residual counted, `FT-XF-FLEX` still moves at least one
coordinate by only `0.108116` out of a `0.96` per-coordinate budget at some policy and stage, and
`FT-XF-BC` by only `0.250245` — so on this host, at this rung, both learner packages leave a large
part of the declared budget unused somewhere in their parameter sets.
