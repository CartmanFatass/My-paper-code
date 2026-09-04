# UCOPE exposure ladder — rung 1 result (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the object registered in
`UCOPE_SECTION11_RECAST_INTAKE_20260902.md` section 4, under owner decisions 2 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`.

**Question.** On the frozen eight-context UCOPE host, does a ten-fold larger optimizer-exposure
budget — learning rate `3e-3` instead of `3e-4`, at the unchanged `160` tail / `320` root updates —
produce even-support competence in the `FT-XF-FLEX` and `FT-XF-BC` learner packages, where the same
two packages produced none at lr `3e-4`?

**Claim ceiling: `B/EXPLORE`.** Everything below is a direct observation on the actually observed
panel of 3 seeds x 2 folds x 2 arms. Nothing here establishes acquisition polarity, COUNT/RAW
polarity, a conditioning or representation attribution, stable superiority, a seed-population
effect, generality in `k` or `N`, MARL/UAV relevance, transfer, safety, deployment or real-world
QoS. The intake supplies the reading rule and this document does not go past it.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01-RUNG-1` |
| Ladder object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01` |
| Rung definition | lr `3e-3` at the frozen 160/320 tail/root updates |
| Evidence class | `B/EXPLORE` |
| Launch commit sha (HEAD at launch) | `ce361d40ac7db9cc8ba7714fee278bb62dbf8793` — "Turn the UCOPE refusals and oracle-competence gate into recorded fields" |
| Code object id inside the artifacts | `UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` (the B1 package the ladder reuses); the science object id above is carried in `run-record.json` |
| Run binding | kind `LADDER1_ADMITTED`, source aggregate `882ff69e25000dfbb3e87421e6e92c12f5ddf34741f72a0be6be83c3cc9935fb` over 14 source files |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 1`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/exposure_ladder_r01_rung1_20260902/complete` |
| Branch published | **`R1-C EXPOSURE_DID_NOT_MOVE`** (competence branch `NO_ARM_COMPETENT`), `complete: true`, nothing quarantined |

---

## 1. The recast in force, and what it changed about this launch

Recorded fields that used to be gates (`run-record.json`, `recast_ledger.recorded_not_gating`):
`clean_committed_source_inventory`, `performance_ready_assessment`, `resource_projection_caps`,
`exact_oracle_competence_predicate`, `acquisition_and_count_raw_locks`, `execution_topology`.

| Recorded field | Observed value at this launch |
| --- | --- |
| Source cleanliness (demoted from the `run_ucope_bc_conditioning_discriminator_r01.py:82`-class refusal) | `clean: true`, `porcelain_status: []` over the 14 bound source files; `git_head = ce361d40ac7db9cc8ba7714fee278bb62dbf8793`. It happened to be clean; the run would have proceeded either way |
| Performance assessment (demoted from the `:127` `PERFORMANCE_READY` binding) | `assessment_present: false`, `disposition: NOT_ASSESSED`. No A/RECON assessment object exists for the ladder. Recorded prior from the frozen B1 result: 140.0 s wall and 455 MB peak RSS at three arms; this run has two |
| Resource projection caps | none declared for this object; no cap comparison was made and none was needed |
| Exact-oracle competence predicate | computed at unchanged thresholds and reported in full in section 5; it decided neither completion nor publication |
| Acquisition / COUNT-RAW locks | unchanged: `count_raw_status: LOCKED`, acquisition not evaluated. Recorded as the direction's own sequencing choice, not as a §11 gate |
| Execution topology | as recorded above; no refusal path remains |

Still holding this launch (`recast_ledger.still_gating`): the central 4 GiB admission, the §4
integrity items, the §5.2 nonzero counts, the machine-generated exposure line, and §6.2 learner-side
quarantine. All five held; all five passed.

## 2. Resource admission (a launch condition, unchanged)

`scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`, run by the runner
immediately before any RNG master, model, optimizer, checkpoint or result existed:

```text
passed                      true
captured_at                 2026-09-03T00:53:40.743665Z
minimum_available_bytes     4294967296
available_physical_bytes    11535732736   (10.74 GiB)
effective_available_bytes   11535732736   (10.74 GiB)
physical_floor_pass         true
effective_floor_pass        true
failure_reasons             []
```

## 3. Commands actually run

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py run
  --output-root C:/Projects/HMASD/temp/directions/ucope/exp/exposure_ladder_r01_rung1_20260902
  --thread-cap 1
```

Read-only revalidation of the published tree afterwards:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py validate
  --complete-root C:/Projects/HMASD/temp/directions/ucope/exp/exposure_ladder_r01_rung1_20260902/complete
```

## 4. Work accounting — declared versus actual

Every counter below is reconciled by the runner against the exact total the frozen configuration
implies; a mismatch stops the run. All twelve matched.

| Quantity | Declared | Observed |
| --- | ---: | ---: |
| Environment episodes | 122,880 | 122,880 |
| Environment transitions | 614,400 | 614,400 |
| Root optimizer updates | 3,840 | 3,840 |
| Tail optimizer updates | 1,920 | 1,920 |
| Root example exposures | 983,040 | 983,040 |
| Tail example exposures | 491,520 | 491,520 |
| Exact policy evaluations | 384 | 384 |
| Sampled evaluation episodes | 24,576 | 24,576 |
| Checkpoints written | 48 | 48 |
| Policies completed | 12 | 12 |
| Non-finite events | 0 | 0 |
| Support-limited seeds | 0 of 3 | `false` for all three seeds |

12 policies = 2 arms x 3 seeds x 2 folds; 48 checkpoints = 12 x `{40, 80, 160, 320}`.

## 5. Competence observation (recorded, deciding nothing)

Exact-oracle predicate, unchanged: `all_scores_finite AND all_choices_unique AND
exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND
minimum_forced_PROBE_tail_agreement >= 19/20`, on even held-out support `K_eval = {2,4,6,8}` at root
update 320.

```text
competent policies (of 12)                 0
oracle root-vector matches (of 12)         0
arm_competent  FT-XF-FLEX                  false
arm_competent  FT-XF-BC                    false
branch                                     NO_ARM_COMPETENT
count_raw_status                           LOCKED
paid acquisition                           not evaluated
```

Per seed and fold, all flags are `false` for both arms; no seed passed either arm.

### Every frozen measurement, per arm / seed / fold / checkpoint

`fin` = all scores finite, `unq` = all choices unique, `orc` = exact eight-context oracle root
vector, `regret` = maximum exact expected regret (gate `<= 0.02`), `agree` = minimum
probability-weighted forced-PROBE tail agreement (gate `>= 0.95`), `nP` = number of the eight
contexts in which the policy selects PROBE, `cmp` = `C_even` pass.

| arm | seed | fold | upd | fin | unq | orc | regret | agree | nP | cmp |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| FT-XF-BC | 00 | 0 | 40 | T | T | F | 0.268000 | 0.000000 | 2 | F |
| FT-XF-BC | 00 | 0 | 80 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 00 | 0 | 160 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 00 | 0 | 320 | T | T | F | 0.218000 | 0.000000 | 2 | F |
| FT-XF-BC | 00 | 1 | 40 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 1 | 80 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 1 | 160 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 1 | 320 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 01 | 0 | 40 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 80 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 160 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 320 | T | T | F | 0.268000 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 40 | T | T | F | 0.375933 | 0.000000 | 6 | F |
| FT-XF-BC | 01 | 1 | 80 | T | T | F | 0.375933 | 0.000000 | 4 | F |
| FT-XF-BC | 01 | 1 | 160 | T | T | F | 0.375933 | 0.000000 | 4 | F |
| FT-XF-BC | 01 | 1 | 320 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 0 | 40 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 80 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 160 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 320 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 1 | 40 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 80 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 160 | T | T | F | 0.168000 | 0.000000 | 4 | F |
| FT-XF-BC | 02 | 1 | 320 | T | T | F | 0.148000 | 0.000000 | 4 | F |
| FT-XF-FLEX | 00 | 0 | 40 | T | T | F | 0.100000 | 1.000000 | 8 | F |
| FT-XF-FLEX | 00 | 0 | 80 | T | T | F | 0.100000 | 1.000000 | 8 | F |
| FT-XF-FLEX | 00 | 0 | 160 | T | T | F | 0.100000 | 1.000000 | 8 | F |
| FT-XF-FLEX | 00 | 0 | 320 | T | T | F | 0.100000 | 1.000000 | 7 | F |
| FT-XF-FLEX | 00 | 1 | 40 | T | T | F | 0.069437 | 0.764509 | 0 | F |
| FT-XF-FLEX | 00 | 1 | 80 | T | T | F | 0.069437 | 0.764509 | 0 | F |
| FT-XF-FLEX | 00 | 1 | 160 | T | T | F | 0.069437 | 0.764509 | 0 | F |
| FT-XF-FLEX | 00 | 1 | 320 | T | T | F | 0.069437 | 0.764509 | 0 | F |
| FT-XF-FLEX | 01 | 0 | 40 | T | T | F | 0.069437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 01 | 0 | 80 | T | T | F | 0.069437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 01 | 0 | 160 | T | T | F | 0.069437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 01 | 0 | 320 | T | T | F | 0.069437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 01 | 1 | 40 | T | T | F | 0.100000 | 1.000000 | 5 | F |
| FT-XF-FLEX | 01 | 1 | 80 | T | T | F | 0.100000 | 1.000000 | 3 | F |
| FT-XF-FLEX | 01 | 1 | 160 | T | T | F | 0.028563 | 1.000000 | 2 | F |
| FT-XF-FLEX | 01 | 1 | 320 | T | T | F | 0.028563 | 1.000000 | 2 | F |
| FT-XF-FLEX | 02 | 0 | 40 | T | T | F | 0.098000 | 0.000000 | 2 | F |
| FT-XF-FLEX | 02 | 0 | 80 | T | T | F | 0.148000 | 0.000000 | 5 | F |
| FT-XF-FLEX | 02 | 0 | 160 | T | T | F | 0.148000 | 0.000000 | 5 | F |
| FT-XF-FLEX | 02 | 0 | 320 | T | T | F | 0.148000 | 0.000000 | 4 | F |
| FT-XF-FLEX | 02 | 1 | 40 | T | T | F | 0.048000 | 0.611559 | 2 | F |
| FT-XF-FLEX | 02 | 1 | 80 | T | T | F | 0.048000 | 0.611559 | 2 | F |
| FT-XF-FLEX | 02 | 1 | 160 | T | T | F | 0.048000 | 0.611559 | 2 | F |
| FT-XF-FLEX | 02 | 1 | 320 | T | T | F | 0.048000 | 0.611559 | 2 | F |

Closest approaches at update 320: minimum `regret` `0.02856289875` against the `0.02` gate
(`FT-XF-FLEX`, seed 01, fold 1); maximum `agree` `1.000000` against the `0.95` gate (three
`FT-XF-FLEX` policies). No policy satisfied the exact oracle root-vector clause, so no policy could
pass regardless of the other two clauses.

### Sampled diagnostic at update 320 (descriptive; cannot replace the exact predicate)

`target` is the action selected in the sole positive-probe context `LINKED-p17_20-c9_100`;
`ret_sum` is the summed external return over 512 fresh paired episodes (64 per context).

| arm | seed | fold | target | nPROBE/8 | ret_sum | PROBE episodes |
| --- | --- | ---: | --- | ---: | ---: | --- |
| FT-XF-BC | 00 | 0 | IMMEDIATE | 2 | 366.27733 | 128/512 |
| FT-XF-BC | 00 | 1 | PROBE | 4 | 260.88533 | 256/512 |
| FT-XF-BC | 01 | 0 | PROBE | 8 | 233.52533 | 512/512 |
| FT-XF-BC | 01 | 1 | IMMEDIATE | 0 | 350.27200 | 0/512 |
| FT-XF-BC | 02 | 0 | PROBE | 8 | 357.68533 | 512/512 |
| FT-XF-BC | 02 | 1 | PROBE | 4 | 351.62667 | 256/512 |
| FT-XF-FLEX | 00 | 0 | PROBE | 7 | 400.98933 | 448/512 |
| FT-XF-FLEX | 00 | 1 | IMMEDIATE | 0 | 404.96000 | 0/512 |
| FT-XF-FLEX | 01 | 0 | IMMEDIATE | 0 | 363.71200 | 0/512 |
| FT-XF-FLEX | 01 | 1 | PROBE | 2 | 409.08267 | 128/512 |
| FT-XF-FLEX | 02 | 0 | IMMEDIATE | 4 | 392.50667 | 256/512 |
| FT-XF-FLEX | 02 | 1 | PROBE | 2 | 372.66133 | 128/512 |

Descriptive arm comparison over the six seed/fold units. No polarity is claimed at three seeds.

| checkpoint | FLEX strictly lower `regret` | FLEX strictly higher `agree` |
| ---: | ---: | ---: |
| 40 | 6/6 | 5/6 |
| 80 | 5/6 | 5/6 |
| 160 | 5/6 | 5/6 |
| 320 | 5/6 | 5/6 |

## 6. The exposure line (a launch condition, §11.4)

Machine-generated by the runner from this run's own final checkpoints against the exact
deterministic initialisation of the same arm/seed/fold. `disp_l2` and `init_l2` are over **all**
trainable parameters of the stage — for `FT-XF-FLEX` that includes the paired 64x64 residual, which
is why its `init_l2` is about 9 and `FT-XF-BC`'s about 1.5. `maxmove` is the largest absolute
per-coordinate change of the **Bellman coefficient vector**, which is the quantity the reading rule
uses.

| arm | seed | fold | stage | disp_l2 | init_l2 | disp/init | maxmove |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| FT-XF-BC | 00 | 0 | root | 0.88242 | 1.44624 | 0.6101 | 0.42174 |
| FT-XF-BC | 00 | 0 | tail | 0.87084 | 1.55022 | 0.5617 | 0.42428 |
| FT-XF-BC | 00 | 1 | root | 1.51500 | 1.80503 | 0.8393 | 0.83330 |
| FT-XF-BC | 00 | 1 | tail | 0.54645 | 1.46738 | 0.3724 | 0.36326 |
| FT-XF-BC | 01 | 0 | root | 1.26138 | 0.94264 | 1.3381 | 0.60859 |
| FT-XF-BC | 01 | 0 | tail | 0.97736 | 1.47299 | 0.6635 | 0.49511 |
| FT-XF-BC | 01 | 1 | root | 1.13474 | 1.35969 | 0.8346 | 0.61572 |
| FT-XF-BC | 01 | 1 | tail | 0.39441 | 1.26533 | 0.3117 | 0.25025 |
| FT-XF-BC | 02 | 0 | root | 0.55582 | 1.22925 | 0.4522 | 0.31875 |
| FT-XF-BC | 02 | 0 | tail | 0.58147 | 1.72710 | 0.3367 | 0.36587 |
| FT-XF-BC | 02 | 1 | root | 1.18479 | 1.32045 | 0.8973 | 0.67393 |
| FT-XF-BC | 02 | 1 | tail | 0.63797 | 1.32805 | 0.4804 | 0.33891 |
| FT-XF-FLEX | 00 | 0 | root | 1.77814 | 8.95364 | 0.1986 | 0.08918 |
| FT-XF-FLEX | 00 | 0 | tail | 2.41713 | 9.10244 | 0.2655 | 0.12858 |
| FT-XF-FLEX | 00 | 1 | root | 2.37250 | 9.22037 | 0.2573 | 0.11254 |
| FT-XF-FLEX | 00 | 1 | tail | 1.94066 | 9.00628 | 0.2155 | 0.12614 |
| FT-XF-FLEX | 01 | 0 | root | 1.94958 | 9.01050 | 0.2164 | 0.07733 |
| FT-XF-FLEX | 01 | 0 | tail | 2.65654 | 8.93494 | 0.2973 | 0.13148 |
| FT-XF-FLEX | 01 | 1 | root | 1.74941 | 9.11292 | 0.1920 | 0.11322 |
| FT-XF-FLEX | 01 | 1 | tail | 1.82069 | 8.96046 | 0.2032 | 0.05561 |
| FT-XF-FLEX | 02 | 0 | root | 1.84416 | 9.07961 | 0.2031 | 0.10017 |
| FT-XF-FLEX | 02 | 0 | tail | 2.04831 | 9.04260 | 0.2265 | 0.10432 |
| FT-XF-FLEX | 02 | 1 | root | 2.24118 | 9.22577 | 0.2429 | 0.10783 |
| FT-XF-FLEX | 02 | 1 | tail | 1.25257 | 9.01170 | 0.1390 | 0.04643 |

```text
minimum displacement / initialisation ratio     0.1390
maximum displacement / initialisation ratio     1.3381
minimum beta max-abs coordinate move  (m)       0.046434   (FT-XF-FLEX, seed 02, fold 1, tail)
maximum beta max-abs coordinate move            0.833301   (FT-XF-BC,   seed 00, fold 1, root)
FT-XF-BC   beta max-move  min / median / max    0.250245 / 0.423009 / 0.833301
FT-XF-FLEX beta max-move  min / median / max    0.046434 / 0.106074 / 0.131479
learner_can_move_in_its_budget                  true
```

## 7. The reading rule applied verbatim, with the deciding numbers

The rule is `UCOPE_SECTION11_RECAST_INTAKE_20260902.md` section 4.5, frozen before this run existed.
`m` is defined there as "the **minimum**, over all 12 policies and both stages, of the largest
absolute per-coordinate change of the Bellman coefficient vector from its exact initialisation,
taken at the final checkpoint".

| Rule input | Value |
| --- | --- |
| Arms with `B_COMPETENT` (at least 2 of 3 seeds passing both folds) | **0 of 2** |
| `m` | **0.046434** |
| Frozen threshold | `0.30` |

Branches, in the frozen order:

- **R1-A** requires at least one `B_COMPETENT` arm. **Not satisfied** — zero arms, zero seeds, zero
  policies.
- **R1-B** requires no `B_COMPETENT` arm **and** `m >= 0.30`. **Not satisfied** — `m = 0.046434 < 0.30`.
- **R1-C** requires no `B_COMPETENT` arm **and** `m < 0.30`. **Satisfied.**

**Branch: `R1-C EXPOSURE_DID_NOT_MOVE`.** The rule's reading, verbatim: "rung 1 did not deliver the
intended exposure increase, so it says nothing about mechanism A. It is uninformative for the
ladder's question. Next: rung 2 (lr `3e-4` at 1,600/3,200 updates) must run before any exposure
conclusion is drawn."

Two direct observations a reader needs in order not to over-read that branch:

1. `m` is set by the `FT-XF-FLEX` arm, whose Bellman coefficient vector is only part of its model —
   its paired 64x64 residual absorbs displacement the coefficient statistic does not see. All six
   `FT-XF-FLEX` Bellman max-moves lie in `0.046`–`0.131`, while its whole-parameter displacement
   ratio is `0.139`–`0.297`.
2. The branch does not change if `FT-XF-BC` is taken alone, where the Bellman vector **is** the whole
   model: its minimum max-move is `0.250245`, still below `0.30`. So R1-C is not an artefact of
   mixing the two arms.

The threshold `0.30` was fixed in the intake before the run and is not adjusted here. Moving it after
seeing these numbers would be an outcome-informed change to a prospective rule, and is not done.

## 8. Verbatim summary lines

```text
{"path": "C:\\Projects\\HMASD\\temp\\directions\\ucope\\exp\\exposure_ladder_r01_rung1_20260902\\complete\\run-record.json"}
```

```text
{"branch": "NO_ARM_COMPETENT", "resources_unmeasured": false, "science_object_id": "UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01-RUNG-1", "valid": true}
```

## 9. Resource telemetry (measured; not `resources_unmeasured`)

```text
resources_unmeasured        false
unmeasured_reasons          []
wall_seconds (in-runner)    89.28577390000282
cpu_seconds                 87.5625
peak_rss_bytes              431472640        (411.5 MiB)
scratch_bytes               7363558          (7.02 MiB)
durable_bytes               7362504          (7.02 MiB)
```

End-to-end wall clock for the invocation, including interpreter start and the preflight subprocess:
`2026-09-03T00:53:40Z` to `2026-09-03T00:55:17Z`, 97 s. Published tree: 48 checkpoint `.pt` files
plus `result.json`, `run-manifest.json` and `run-record.json`. The decision-7 downgrade path was not
exercised.

## 10. Deviations

- **D1 — no A/RECON performance assessment.** The object has none and none was produced; the absence
  is recorded as `performance_assessment.assessment_present = false`. This is the recast itself
  (decision 2), not an unplanned departure.
- **D2 — arm inventory.** The ladder runs two arms, `FT-XF-FLEX` and `FT-XF-BC`, where the B1 object
  ran three. This is the object as registered — the independent review specifies this pair — and
  `MT-XF-FLEX` with the target-schedule question it carried is not part of it. Because the RNG is
  counter-addressed on `(namespace, seed, fold, index)` and never on arm order, the two retained
  arms' data, initialisation and batches are unaffected by the omission.
- **D3 — `scripts/hmasd_run.py` not used.** This object's own runner owns its manifest, admission
  receipt, publication and quarantine, as the SCDMP recast did. Consistent with E0.
- **D4 — concurrency.** The `flexible_skill_duration` E1 study was running two 4-thread processes on
  the same machine throughout. This run used 1 intraop and 1 interop thread as its frozen topology
  requires. Wall time is therefore an upper bound under contention; no scientific quantity here
  depends on it.
- **D5 — no native build cache involved, no TMP redirect.** Neither this object nor its package
  touches a C++ extension, so the `%LOCALAPPDATA%\Temp\hmasd_*_native` cache roots the owner cleared
  were not exercised, and `TMPDIR`/`TEMP`/`TMP` were left at their defaults.
- **D6 — a `ScoutConfig.learning_rate` field was added to the shared B1 package.** Its B1 and ASSESS
  value is unchanged at `3e-4` and `from_dict` accepts pre-recast payloads that lack it, so every
  artifact written before 2026-09-02 still loads as the same configuration. Recorded in the intake
  section 7.

## 11. Could not verify

- Whether a `B_COMPETENT` policy exists anywhere on this host at any exposure. Rung 1 is one point on
  the ladder, and R1-C says it is not even a usable point for the exposure question.
- Whether `0.30` is the right separator between "the ten-fold increase was realised" and "it was
  not". It was derived from the review's per-step displacement arithmetic and fixed prospectively;
  this run is the first evidence about its calibration and that evidence is not used to move it.
- Any comparison against the B1 numbers beyond the two the audit already published (closest regret
  `0.0214`, maximum tail agreement `0.829`). No B1 or audit runtime row was read by this object, by
  design and by the §4.5 leakage boundary.
- Whether `FT-XF-FLEX`'s residual network absorbed displacement that would otherwise have appeared in
  its Bellman coefficients. The exposure line records both statistics; this run does not decompose
  them.

## 12. Interpretation boundary

This is a single `B/EXPLORE` observation on one finite eight-context host, two learner packages,
three seeds and two folds, at one learning rate. It establishes: zero even-support competence at lr
`3e-3` under the unchanged exact-oracle criterion, with every activity counter reconciled and no
non-finite event; and a measured parameter-displacement distribution whose minimum falls below the
threshold the ladder's own rule fixed in advance. It establishes nothing about paid acquisition,
COUNT versus RAW, conditioning, the host margin, arm superiority, seed populations, variable `k`,
variable `N`, MARL, UAV autonomy, transfer, safety or deployment. It does not retire the direction and
it consumes no object beyond itself. The acquisition and COUNT/RAW locks remain closed.

Per the rule, the direction's next step on this ladder is rung 2 (`lr 3e-4` at 1,600/3,200 updates),
already declared in the intake, which needs its own launch, admission and result document.
