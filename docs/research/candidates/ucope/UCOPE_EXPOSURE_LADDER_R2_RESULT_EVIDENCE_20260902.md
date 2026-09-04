# UCOPE exposure ladder — rung 2 result (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the object registered in
`UCOPE_SECTION11_RECAST_INTAKE_20260902.md` section 4, under owner decisions 2 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`. Rung 1 was accepted
in Part D of the compliance note; this is the rung its reading rule named as the required next step.

**Question.** On the frozen eight-context UCOPE host, does a ten-fold larger optimizer **budget** —
`1,600` tail / `3,200` root updates at the unchanged learning rate `3e-4` — produce even-support
competence in the `FT-XF-FLEX` and `FT-XF-BC` learner packages, where the same two packages produced
none at `160`/`320` updates?

**Claim ceiling: `B/EXPLORE`.** Everything below is a direct observation on the actually observed
panel of 3 seeds x 2 folds x 2 arms. Nothing here establishes acquisition polarity, COUNT/RAW
polarity, a conditioning or representation attribution, stable superiority, a seed-population
effect, generality in `k` or `N`, MARL/UAV relevance, transfer, safety, deployment or real-world
QoS. The intake supplies the reading rule and this document does not go past it.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01-RUNG-2` |
| Ladder object | `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01` |
| Rung definition (as registered) | lr `3e-4` at 1,600/3,200 tail/root updates |
| Evidence class | `B/EXPLORE` |
| HEAD at launch | `ba8d165fc193cfb0582b15f96fc68c4a9dd3afa6` |
| Working-tree cleanliness at launch | **dirty and recorded, not refused** — `clean: false`, porcelain: `M experiments/candidates/ucope/competence_first_scout_r01/artifact.py`, `M experiments/candidates/ucope/competence_first_scout_r01/contract.py`, `M scripts/run_ucope_exposure_ladder_rung1.py`. Those three files are the rung-2 registration itself; they are committed together with this document (see deviation D1) |
| Bound source | 14 files, aggregate `62f91839d3bc384b8389f5e1469c023c3e49bd6760596617a9ae93222d94ca06` |
| Run binding | kind `LADDER2_ADMITTED`, manifest digest `421b586687da746154039de408cb478a0d6be82ac8f72d08b23754a593d49112` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 1`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/exposure_ladder_r01_rung2_20260902/complete` |
| Branch published | **`R1-C EXPOSURE_DID_NOT_MOVE`** (competence branch `NO_ARM_COMPETENT`), `complete: true`, nothing quarantined |

---

## 1. The recast in force, and what it changed about this launch

| Recorded field | Observed value at this launch |
| --- | --- |
| Source cleanliness | `clean: false` with the three porcelain lines above, `gating: false`. **This launch is the first to exercise the demotion in its intended direction**: before the recast the dirty-source refusal would have stopped it. The 14-file byte inventory and its aggregate are still recorded, so the run remains reproducible |
| Performance assessment | `assessment_present: false`, `disposition: NOT_ASSESSED`, `gating: false`. The ladder has no A/RECON assessment object; the absence is recorded |
| Resource projection caps | none declared for this object; no cap comparison was made |
| Exact-oracle competence predicate | computed at unchanged thresholds, reported in full in section 5; it decided neither completion nor publication |
| Acquisition / COUNT-RAW locks | unchanged: `count_raw_status: LOCKED`, acquisition not evaluated |
| Execution topology | as recorded above |

Still holding this launch: the central 4 GiB admission, the §4 integrity items, the §5.2 nonzero
counts, the machine-generated exposure line, and §6.2 learner-side quarantine. All five held; all
five passed.

## 2. Resource admission (a launch condition, unchanged)

`scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`, run by the runner
immediately before any RNG master, model, optimizer, checkpoint or result existed:

```text
passed                      true
captured_at                 2026-09-03T01:16:33.392625Z
minimum_available_bytes     4294967296
available_physical_bytes    13716115456   (12.77 GiB)
effective_available_bytes   13716115456   (12.77 GiB)
physical_floor_pass         true
effective_floor_pass        true
failure_reasons             []
```

## 3. Commands actually run

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py run
  --rung 2
  --output-root C:/Projects/HMASD/temp/directions/ucope/exp/exposure_ladder_r01_rung2_20260902
  --thread-cap 1
```

Read-only revalidation of the published tree afterwards:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_exposure_ladder_rung1.py validate
  --complete-root C:/Projects/HMASD/temp/directions/ucope/exp/exposure_ladder_r01_rung2_20260902/complete
```

## 4. Work accounting — declared versus actual

Every counter is reconciled by the runner against the exact total the frozen configuration implies;
a mismatch stops the run. All twelve matched.

| Quantity | Declared | Observed | vs rung 1 |
| --- | ---: | ---: | --- |
| Environment episodes | 122,880 | 122,880 | same |
| Environment transitions | 614,400 | 614,400 | same |
| Root optimizer updates | 38,400 | 38,400 | 10x |
| Tail optimizer updates | 19,200 | 19,200 | 10x |
| Root example exposures | 9,830,400 | 9,830,400 | 10x |
| Tail example exposures | 4,915,200 | 4,915,200 | 10x |
| Exact policy evaluations | 480 | 480 | 5 checkpoints instead of 4 |
| Sampled evaluation episodes | 30,720 | 30,720 | 5 checkpoints instead of 4 |
| Checkpoints written | 60 | 60 | 5 x 12 |
| Policies completed | 12 | 12 | same |
| Non-finite events | 0 | 0 | same |
| Support-limited seeds | 0 of 3 | `false` for all three | same |

12 policies = 2 arms x 3 seeds x 2 folds. Checkpoint roots `{40, 80, 160, 320, 3200}`: the four
frozen roots are retained so every quantity is directly comparable with rung 1 and B1 at identical
update counts, and `3200` is added as this rung's final root, which alone controls competence. The
intake registered rung 2 by learning rate and update counts only; this cadence is declared here and
in `contract.py` (deviation D2).

## 5. Competence observation (recorded, deciding nothing)

Exact-oracle predicate, unchanged: `all_scores_finite AND all_choices_unique AND
exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND
minimum_forced_PROBE_tail_agreement >= 19/20`, on even held-out support `K_eval = {2,4,6,8}` at the
final root update 3,200.

```text
competent policies (of 12)                 0
oracle root-vector matches (of 12)         0
arm_competent  FT-XF-FLEX                  false
arm_competent  FT-XF-BC                    false
branch                                     NO_ARM_COMPETENT
count_raw_status                           LOCKED
paid acquisition                           not evaluated
```

Per arm, per seed: `FT-XF-FLEX` 0 of 3 seeds passing both folds; `FT-XF-BC` 0 of 3. Every one of the
twelve final policies fails on the exact oracle root-vector clause, so none could pass regardless of
the regret and agreement clauses.

### Every frozen measurement, per arm / seed / fold / checkpoint

`fin` = all scores finite, `unq` = all choices unique, `orc` = exact eight-context oracle root
vector, `regret` = maximum exact expected regret (gate `<= 0.02`), `agree` = minimum
probability-weighted forced-PROBE tail agreement (gate `>= 0.95`), `nP` = number of the eight
contexts in which the policy selects PROBE, `cmp` = `C_even` pass.

| arm | seed | fold | upd | fin | unq | orc | regret | agree | nP | cmp |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| FT-XF-BC | 00 | 0 | 40 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 0 | 80 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 0 | 160 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 0 | 320 | T | T | F | 0.268000 | 0.000000 | 2 | F |
| FT-XF-BC | 00 | 0 | 3200 | T | T | F | 0.268000 | 0.000000 | 6 | F |
| FT-XF-BC | 00 | 1 | 40 | T | T | F | 0.268000 | 0.000000 | 1 | F |
| FT-XF-BC | 00 | 1 | 80 | T | T | F | 0.268000 | 0.000000 | 2 | F |
| FT-XF-BC | 00 | 1 | 160 | T | T | F | 0.268000 | 0.000000 | 3 | F |
| FT-XF-BC | 00 | 1 | 320 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 00 | 1 | 3200 | T | T | F | 0.268000 | 0.000000 | 4 | F |
| FT-XF-BC | 01 | 0 | 40 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 80 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 160 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 320 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 01 | 0 | 3200 | T | T | F | 0.268000 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 40 | T | T | F | 0.375933 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 80 | T | T | F | 0.375933 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 160 | T | T | F | 0.375933 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 320 | T | T | F | 0.375933 | 0.000000 | 8 | F |
| FT-XF-BC | 01 | 1 | 3200 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 0 | 40 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 80 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 160 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 320 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 0 | 3200 | T | T | F | 0.148000 | 0.000000 | 8 | F |
| FT-XF-BC | 02 | 1 | 40 | T | T | F | 0.061437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 80 | T | T | F | 0.061437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 160 | T | T | F | 0.061437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 320 | T | T | F | 0.189437 | 0.000000 | 0 | F |
| FT-XF-BC | 02 | 1 | 3200 | T | T | F | 0.148000 | 0.000000 | 4 | F |
| FT-XF-FLEX | 00 | 0 | 40 | T | T | F | 0.100000 | 0.611559 | 4 | F |
| FT-XF-FLEX | 00 | 0 | 80 | T | T | F | 0.100000 | 0.611559 | 7 | F |
| FT-XF-FLEX | 00 | 0 | 160 | T | T | F | 0.100000 | 0.611559 | 8 | F |
| FT-XF-FLEX | 00 | 0 | 320 | T | T | F | 0.100000 | 0.611559 | 8 | F |
| FT-XF-FLEX | 00 | 0 | 3200 | T | T | F | 0.100000 | 0.611559 | 7 | F |
| FT-XF-FLEX | 00 | 1 | 40 | T | T | F | 0.100000 | 0.479273 | 8 | F |
| FT-XF-FLEX | 00 | 1 | 80 | T | T | F | 0.168000 | 0.479273 | 2 | F |
| FT-XF-FLEX | 00 | 1 | 160 | T | T | F | 0.100000 | 0.479273 | 8 | F |
| FT-XF-FLEX | 00 | 1 | 320 | T | T | F | 0.100000 | 0.479273 | 8 | F |
| FT-XF-FLEX | 00 | 1 | 3200 | T | T | F | 0.074123 | 0.479273 | 6 | F |
| FT-XF-FLEX | 01 | 0 | 40 | T | T | F | 0.100000 | 0.788446 | 8 | F |
| FT-XF-FLEX | 01 | 0 | 80 | T | T | F | 0.100000 | 0.788446 | 4 | F |
| FT-XF-FLEX | 01 | 0 | 160 | T | T | F | 0.100000 | 0.788446 | 3 | F |
| FT-XF-FLEX | 01 | 0 | 320 | T | T | F | 0.073899 | 0.788446 | 6 | F |
| FT-XF-FLEX | 01 | 0 | 3200 | T | T | F | 0.073899 | 0.788446 | 5 | F |
| FT-XF-FLEX | 01 | 1 | 40 | T | T | F | 0.189437 | 0.764509 | 0 | F |
| FT-XF-FLEX | 01 | 1 | 80 | T | T | F | 0.100000 | 0.764509 | 4 | F |
| FT-XF-FLEX | 01 | 1 | 160 | T | T | F | 0.100000 | 0.764509 | 5 | F |
| FT-XF-FLEX | 01 | 1 | 320 | T | T | F | 0.100000 | 0.764509 | 4 | F |
| FT-XF-FLEX | 01 | 1 | 3200 | T | T | F | 0.030221 | 0.764509 | 2 | F |
| FT-XF-FLEX | 02 | 0 | 40 | T | T | F | 0.189437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 02 | 0 | 80 | T | T | F | 0.061437 | 0.479273 | 0 | F |
| FT-XF-FLEX | 02 | 0 | 160 | T | T | F | 0.081912 | 0.479273 | 4 | F |
| FT-XF-FLEX | 02 | 0 | 320 | T | T | F | 0.081912 | 0.479273 | 6 | F |
| FT-XF-FLEX | 02 | 0 | 3200 | T | T | F | 0.081912 | 0.479273 | 4 | F |
| FT-XF-FLEX | 02 | 1 | 40 | T | T | F | 0.189437 | 0.520727 | 0 | F |
| FT-XF-FLEX | 02 | 1 | 80 | T | T | F | 0.189437 | 0.520727 | 0 | F |
| FT-XF-FLEX | 02 | 1 | 160 | T | T | F | 0.100000 | 0.520727 | 3 | F |
| FT-XF-FLEX | 02 | 1 | 320 | T | T | F | 0.048000 | 0.520727 | 2 | F |
| FT-XF-FLEX | 02 | 1 | 3200 | T | T | F | 0.070609 | 0.520727 | 3 | F |

At the final root update 3,200: minimum `regret` `0.030221036` against the `0.02` gate
(`FT-XF-FLEX`, seed 01, fold 1); maximum `agree` `0.788446` against the `0.95` gate (`FT-XF-FLEX`,
seed 01, fold 0); oracle root-vector matches 0 of 12.

Two direct observations about the tail-agreement column, recorded because they are stable across
every checkpoint: `FT-XF-BC`'s minimum forced-PROBE tail agreement is exactly `0.000000` in all 30
of its rows, and each `FT-XF-FLEX` policy holds a single agreement value across all five of its
checkpoints. Neither is interpreted here.

### Sampled diagnostic at update 3,200 (descriptive; cannot replace the exact predicate)

`target` is the action selected in the sole positive-probe context `LINKED-p17_20-c9_100`;
`ret_sum` is the summed external return over 512 fresh paired episodes (64 per context).

| arm | seed | fold | target | nPROBE/8 | ret_sum | PROBE episodes |
| --- | --- | ---: | --- | ---: | ---: | --- |
| FT-XF-BC | 00 | 0 | PROBE | 6 | 279.37600 | 384/512 |
| FT-XF-BC | 00 | 1 | PROBE | 4 | 298.43200 | 256/512 |
| FT-XF-BC | 01 | 0 | PROBE | 8 | 317.73867 | 512/512 |
| FT-XF-BC | 01 | 1 | IMMEDIATE | 0 | 350.27200 | 0/512 |
| FT-XF-BC | 02 | 0 | PROBE | 8 | 370.48533 | 512/512 |
| FT-XF-BC | 02 | 1 | PROBE | 4 | 392.34667 | 256/512 |
| FT-XF-FLEX | 00 | 0 | PROBE | 7 | 398.20000 | 448/512 |
| FT-XF-FLEX | 00 | 1 | PROBE | 6 | 375.50400 | 384/512 |
| FT-XF-FLEX | 01 | 0 | PROBE | 5 | 393.90933 | 320/512 |
| FT-XF-FLEX | 01 | 1 | PROBE | 2 | 389.28800 | 128/512 |
| FT-XF-FLEX | 02 | 0 | PROBE | 4 | 431.22667 | 256/512 |
| FT-XF-FLEX | 02 | 1 | PROBE | 3 | 405.28267 | 192/512 |

11 of 12 final policies select PROBE in the target context, but none selects it in the target context
*and nowhere unwarranted* — `nPROBE` ranges from 2 to 8 of the eight contexts, and the exact oracle
root vector is matched by none. This is a descriptive observation on three seeds; no acquisition
claim follows from it, and acquisition was not evaluated.

Descriptive arm comparison over the six seed/fold units. No polarity is claimed at three seeds.

| checkpoint | FLEX strictly lower `regret` | FLEX strictly higher `agree` |
| ---: | ---: | ---: |
| 40 | 4/6 | 6/6 |
| 80 | 5/6 | 6/6 |
| 160 | 5/6 | 6/6 |
| 320 | 6/6 | 6/6 |
| 3200 | 6/6 | 6/6 |

## 6. The exposure line (a launch condition, §11.4)

Machine-generated by the runner from this run's own final checkpoints against the exact
deterministic initialisation of the same arm/seed/fold. `disp_l2` and `init_l2` are over **all**
trainable parameters of the stage — for `FT-XF-FLEX` that includes the paired 64x64 residual, which
is why its `init_l2` is about 9 and `FT-XF-BC`'s about 1.5. `maxmove` is the largest absolute
per-coordinate change of the **Bellman coefficient vector**, which is the quantity the reading rule
uses.

| arm | seed | fold | stage | disp_l2 | init_l2 | disp/init | maxmove |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| FT-XF-BC | 00 | 0 | root | 0.87801 | 1.44624 | 0.6071 | 0.437747 |
| FT-XF-BC | 00 | 0 | tail | 0.85135 | 1.55022 | 0.5492 | 0.417038 |
| FT-XF-BC | 00 | 1 | root | 1.53279 | 1.80503 | 0.8492 | 0.843375 |
| FT-XF-BC | 00 | 1 | tail | 0.56182 | 1.46738 | 0.3829 | 0.365717 |
| FT-XF-BC | 01 | 0 | root | 1.23311 | 0.94264 | 1.3081 | 0.612136 |
| FT-XF-BC | 01 | 0 | tail | 0.96100 | 1.47299 | 0.6524 | 0.495335 |
| FT-XF-BC | 01 | 1 | root | 1.13106 | 1.35969 | 0.8318 | 0.640824 |
| FT-XF-BC | 01 | 1 | tail | 0.39301 | 1.26533 | 0.3106 | 0.249392 |
| FT-XF-BC | 02 | 0 | root | 0.56611 | 1.22925 | 0.4605 | 0.321863 |
| FT-XF-BC | 02 | 0 | tail | 0.58850 | 1.72710 | 0.3407 | 0.369368 |
| FT-XF-BC | 02 | 1 | root | 1.20098 | 1.32045 | 0.9095 | 0.692509 |
| FT-XF-BC | 02 | 1 | tail | 0.63261 | 1.32805 | 0.4763 | 0.339870 |
| FT-XF-FLEX | 00 | 0 | root | 1.72360 | 8.95364 | 0.1925 | 0.132471 |
| FT-XF-FLEX | 00 | 0 | tail | 2.27167 | 9.10244 | 0.2496 | 0.079066 |
| FT-XF-FLEX | 00 | 1 | root | 2.29781 | 9.22037 | 0.2492 | 0.075846 |
| FT-XF-FLEX | 00 | 1 | tail | 2.01060 | 9.00628 | 0.2232 | 0.070453 |
| FT-XF-FLEX | 01 | 0 | root | 1.48502 | 9.01050 | 0.1648 | 0.059071 |
| FT-XF-FLEX | 01 | 0 | tail | 2.65421 | 8.93494 | 0.2971 | 0.070034 |
| FT-XF-FLEX | 01 | 1 | root | 1.76605 | 9.11292 | 0.1938 | 0.092168 |
| FT-XF-FLEX | 01 | 1 | tail | 1.62444 | 8.96046 | 0.1813 | 0.042410 |
| FT-XF-FLEX | 02 | 0 | root | 1.53459 | 9.07961 | 0.1690 | 0.067830 |
| FT-XF-FLEX | 02 | 0 | tail | 2.29925 | 9.04260 | 0.2543 | 0.072873 |
| FT-XF-FLEX | 02 | 1 | root | 2.02987 | 9.22577 | 0.2200 | 0.068815 |
| FT-XF-FLEX | 02 | 1 | tail | 0.97002 | 9.01170 | 0.1076 | 0.025254 |

```text
minimum displacement / initialisation ratio     0.1076
maximum displacement / initialisation ratio     1.3081
minimum beta max-abs coordinate move  (m)       0.025254   (FT-XF-FLEX, seed 02, fold 1, tail)
maximum beta max-abs coordinate move            0.843375   (FT-XF-BC,   seed 00, fold 1, root)
FT-XF-BC   beta max-move  min / median / max    0.249392 / 0.427392 / 0.843375
FT-XF-FLEX beta max-move  min / median / max    0.025254 / 0.070243 / 0.132471
learner_can_move_in_its_budget                  true
```

## 7. The reading rule applied verbatim, with the deciding numbers

The rule is `UCOPE_SECTION11_RECAST_INTAKE_20260902.md` section 4.5, frozen before any ladder data
existed and applied here exactly as it was to rung 1. `m` is defined there as "the **minimum**, over
all 12 policies and both stages, of the largest absolute per-coordinate change of the Bellman
coefficient vector from its exact initialisation, taken at the final checkpoint".

| Rule input | Value |
| --- | --- |
| Arms with `B_COMPETENT` (at least 2 of 3 seeds passing both folds) | **0 of 2** |
| `m` | **0.025254** |
| Frozen threshold | `0.30` |

Branches, in the frozen order:

- **R1-A** requires at least one `B_COMPETENT` arm. **Not satisfied** — zero arms, zero seeds, zero
  policies.
- **R1-B** requires no `B_COMPETENT` arm **and** `m >= 0.30`. **Not satisfied** — `m = 0.025254 < 0.30`.
- **R1-C** requires no `B_COMPETENT` arm **and** `m < 0.30`. **Satisfied.**

**Branch: `R1-C EXPOSURE_DID_NOT_MOVE`**, the same branch rung 1 produced. The rule's registered
reading is that the rung "did not deliver the intended exposure increase, so it says nothing about
mechanism A", and that rung 2 must run before an exposure conclusion — which is this run.

Three direct observations, recorded so the branch is not over-read, and one methodological note:

1. As in rung 1, `m` is set by the `FT-XF-FLEX` arm, whose Bellman coefficient vector is only part
   of its model; its residual absorbs displacement the coefficient statistic does not see. All twelve
   `FT-XF-FLEX` Bellman max-moves lie in `0.025`–`0.132`, while its whole-parameter displacement
   ratio is `0.108`–`0.297`.
2. The branch does not change on `FT-XF-BC` alone, where the Bellman vector **is** the whole model:
   its minimum max-move is `0.249392`, still below `0.30` — and, notably, essentially identical to
   rung 1's `0.250245`.
3. Ten times the update budget at the same learning rate moved the Bellman coefficients **no
   further** than rung 1 did, and by this statistic slightly less: `m` fell from `0.046434` to
   `0.025254`, and the `FT-XF-BC` median from `0.423009` to `0.427392` (unchanged to within noise).
   That is a direct observation about this optimizer on this objective; it is not interpreted here.
4. `m` is a **minimum over 24 stage-policies of a maximum over coordinates**, so a single
   low-displacement policy fixes it. Both rungs have now been decided by that single minimum while
   the majority of policies moved far more. Whether that statistic is the right instrument for the
   exposure question is a live methodological question for the owner; it is **not** changed here,
   because moving a prospective threshold or its statistic after seeing two outcomes would be an
   outcome-informed rewrite of a frozen rule.

## 8. Verbatim summary lines

```text
{"path": "C:\\Projects\\HMASD\\temp\\directions\\ucope\\exp\\exposure_ladder_r01_rung2_20260902\\complete\\run-record.json"}
```

```text
{"branch": "NO_ARM_COMPETENT", "resources_unmeasured": false, "science_object_id": "UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01-RUNG-2", "valid": true}
```

## 9. Resource telemetry (measured; not `resources_unmeasured`)

```text
resources_unmeasured        false
unmeasured_reasons          []
wall_seconds (in-runner)    359.2933880999917
cpu_seconds                 356.578125
peak_rss_bytes              431079424        (411.1 MiB)
scratch_bytes               9204192          (8.78 MiB)
durable_bytes               9203130          (8.78 MiB)
```

End-to-end wall clock for the invocation, including interpreter start and the preflight subprocess:
`2026-09-03T01:16:32Z` to `2026-09-03T01:22:41Z`, 369 s. Published tree: 60 checkpoint `.pt` files
plus `result.json`, `run-manifest.json` and `run-record.json`. The decision-7 downgrade path was not
exercised. Against rung 1: 4.02x the wall time for 10x the optimizer updates, at essentially the same
peak RSS (411.1 MiB versus 411.5 MiB).

## 10. Deviations

- **D1 — launched from a dirty working tree, recorded not refused.** The three files that register
  rung 2 (`contract.py`, `artifact.py`, `run_ucope_exposure_ladder_rung1.py`) were uncommitted at
  launch, so `clean: false` with the porcelain lines is recorded in the run record, and HEAD at launch
  was `ba8d165fc193cfb0582b15f96fc68c4a9dd3afa6`. They are committed together with this document, in
  the single commit the coordinator asked for; the launched bytes are pinned by the recorded 14-file
  inventory and its aggregate `62f91839d3bc384b8389f5e1469c023c3e49bd6760596617a9ae93222d94ca06`, so
  the exact source is recoverable from that commit. This is precisely the demotion the recast made:
  before it, the clean-source refusal would have stopped this launch.
- **D2 — checkpoint cadence declared here.** The intake registered rung 2 by learning rate and update
  counts only. The cadence `{40, 80, 160, 320, 3200}` was chosen and frozen in `contract.py` before
  the run, to keep rung 1 and B1 comparability at identical update counts and to add this rung's own
  final root. Competence is judged at 3,200 alone, as the frozen predicate requires.
- **D3 — no A/RECON performance assessment.** The object has none and none was produced; recorded as
  `assessment_present: false`. This is the recast itself.
- **D4 — arm inventory.** Two arms, `FT-XF-FLEX` and `FT-XF-BC`, as the ladder is registered; the RNG
  is counter-addressed on `(namespace, seed, fold, index)` and never on arm order.
- **D5 — `scripts/hmasd_run.py` not used.** The object's own runner owns its manifest, admission
  receipt, publication and quarantine. Consistent with E0 and with rung 1.
- **D6 — concurrency.** Other work was running on the same machine throughout. This run used 1
  intraop and 1 interop thread as the frozen topology requires. Wall time is an upper bound under
  contention; no scientific quantity depends on it.
- **D7 — no native build cache involved, no TMP redirect.** This package touches no C++ extension, so
  the `%LOCALAPPDATA%\Temp\hmasd_*_native` roots were not exercised and `TMPDIR`/`TEMP`/`TMP` were
  left at their defaults.
- **D8 — runner file name.** Rung 2 is run by `scripts/run_ucope_exposure_ladder_rung1.py --rung 2`.
  The script now carries a rung registry and its rung-1 name is stale; it was not renamed because
  rung 1's published record was produced by that path and the committed recast tests address it.

## 11. Could not verify

- Whether a `B_COMPETENT` policy exists on this host at any exposure. Two of the three registered
  rungs have now run and neither produced one; rung 3 (lr `3e-3` at 1,600/3,200) was not run and is
  not requested.
- Whether `0.30`, or the minimum-over-policies statistic itself, is the right separator for the
  exposure question. Both were fixed prospectively; two runs have now been decided by that minimum,
  and this document does not move either.
- Why `FT-XF-BC`'s minimum forced-PROBE tail agreement is exactly `0.000000` in all 30 of its rows,
  and why each `FT-XF-FLEX` policy's agreement is constant across all five of its checkpoints. Both
  are recorded as observations; neither was investigated.
- Any comparison against B1 runtime rows. No B1 or audit runtime row was read, by design and by the
  §4.5 leakage boundary. The rung-1 comparisons above use rung 1's own published record.
- Whether the `FT-XF-FLEX` residual absorbed displacement that would otherwise appear in its Bellman
  coefficients. The exposure line records both statistics; this run does not decompose them.

## 12. Interpretation boundary

This is a single `B/EXPLORE` observation on one finite eight-context host, two learner packages,
three seeds and two folds, at one optimizer budget. It establishes: zero even-support competence at
`1,600`/`3,200` updates and lr `3e-4` under the unchanged exact-oracle criterion, with every activity
counter reconciled and no non-finite event; and a measured parameter-displacement distribution whose
minimum again falls below the threshold the ladder's rule fixed in advance, so the registered branch
is again `R1-C`. It establishes nothing about paid acquisition, COUNT versus RAW, conditioning, the
host margin, arm superiority, seed populations, variable `k`, variable `N`, MARL, UAV autonomy,
transfer, safety or deployment. It does not retire the direction and it consumes no object beyond
itself. The acquisition and COUNT/RAW locks remain closed.

Two rungs have now returned `R1-C` for the same structural reason — a single low-displacement
`FT-XF-FLEX` tail policy fixes `m` below `0.30` while most policies move far more. Whether to run
rung 3, to recast the exposure statistic, or to move to the margin-scaled falsifier the review holds
in reserve is an owner decision and is not taken here.
