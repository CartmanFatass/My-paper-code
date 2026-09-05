# MGTAP B03 main panel — complete and technically conformant

The frozen 24-fit panel exists, with every required learner trace and all 17
checkpoints. The ordered card rule returns **B03_SELECTED_INSIDE_MEI**:
selected METRIC-minus-FREE normalized AUC is **0.0006554780183014955**, below
absolute MEI 0.01. Both actors select rate **3.0** by mean AUC over all three
seeds; both are edge-of-grid winners. This is a same-panel development statistic,
not independent confirmation, equivalence, or metric-specific causal evidence.
DM owns interpretation and the next object.

Card: `MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md`. Technical review and
implementation: `MGTAP_B03_TECHNICAL_EVIDENCE_20260904.md`. Complete seed/config/
N/load curves, AUCs, exact argv, admissions and counts are in
`MGTAP_B03_MAIN_SUMMARY_20260904.json`.

## Exact execution and evidence

Launch source **19531d07023637a0940fd9c6cfa51005d13fe0a7** was committed and pushed
before remote preparation. Configured node `wsl_4070`, SSH `hmasd-wsl-node`,
CPU float64, one thread. Detached cwd:
`/home/wu/hmasd-worktrees/mgtap_b03_20260904`.

Accepted once: `mgtap_b03_main_307_311_313_19531d07`, existing agent-task supervisor,
PID 108608. Tracker `/root/tracker_tl_experiments` acknowledged adoption and
reported FINISHED/exit 0, terminal `2026-09-05T07:58:54+08:00` (23:58:54Z),
log elapsed 41 seconds. Log and exit:
`/home/wu/.agent-tasks/mgtap_b03_main_307_311_313_19531d07/{task.log,exit_code}`.
No polling duplicate or relaunch occurred after adoption.

For seed s in the exact order 307,311,313, the accepted command joins each pair
with `&&`, and joins the three pairs with `&&`, after cd to the cwd above.
Every command uses `/home/wu/.venvs/hmasd/bin/python`:

```text
scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b03_main_<s>/admission.json
scripts/run_mgtap_b03_stepsize.py --mode main --seed <s> --oracle /home/wu/hmasd-worktrees/mgtap_b02_20260904/temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/oracle_returns.npy --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b03_main_<s>
```

The existing B02 oracle was loaded read-only. Each destination-local admission
passed physical and effective 4-GiB floors immediately before its seed runner;
full measurements/timestamps are in the summary. Git fetch and lazy worktree
checkout initially stalled under the ordinary shell; no science was launched.
Those preparation processes were terminated and the exact operations completed
under configured `zsh -lic`. Its interactive gitstatus warning was nonfatal.

Raw roots were copied unchanged to the same relative paths under
`C:/Projects/HMASD-worktrees/cm-n5-b03-20260904`. Each contains admission,
summary, oracle and 8 training JSON/8 evaluation NPZ files. Supervisor evidence
is copied under `temp/directions/metric_ground_transport_allocation/exp/mgtap_b03_supervisor`.
Offline publication used the committed runner's `--mode summarize --inputs`
with the three local summary paths and `--out` the sibling `mgtap_b03_panel`.
This operation does not train or sample.

## Direct measurements and ordered rule

| Rate | METRIC mean AUC | FREE mean AUC |
| --- | ---: | ---: |
| 0.1 | 0.406183906837746 | 0.397773770932798 |
| 0.3 | 0.493172765661169 | 0.488168645788122 |
| 1.0 | 0.562689576325593 | 0.561284100567853 |
| 3.0 | 0.599301882143374 | 0.598646404125072 |

Selected per-seed d for 307/311/313:
`[0.0009539286295572325, -0.000671047634548616, 0.0016835530598958703]`.
Mean 0.0006554780183014955; range [-0.000671047634548616,
0.0016835530598958703]; sample SD 0.0012053384101939199. Rule1 fails D>=.01;
rule2 fails D<=-.01; rule3 abs(D)<.01 is true. No per-seed rate selection occurs.

Common-rate-0.1 contrast is 0.008410135904947899. Selection gains over 0.1:
METRIC 0.19311797530562788, FREE 0.20087263319227425. H (selected FREE minus
METRIC 0.1) is 0.19246249728732637. All individual seed values, ranges and
sample SDs are preserved in the summary. Oracle mean is 0.66875; selected
FREE endpoint mean is 0.628151222511574, leaving 0.040598777488426 headroom.
This diagnostic is grid restricted, same-panel selected, and only at trained
N=4/8; it does not create held-out N transfer evidence.

## Counts, resources and technical acceptance

Exactly 24 fits x256 = **6,144 optimizer updates**, **589,824 training
transitions**, **3,538,944 training agent steps**, **313,344 evaluation episodes**,
**626,688 evaluation decisions**, **3,760,128 evaluation agent steps**.
Model selection exposure is 4 configurations x3 seeds per actor, no extra pilot.
All zero-initial parameter arrays and initial evaluation arrays agree across
actor/rate choices within seed. All 6,144 loss/gradient/displacement/path/distance
rows are finite; all parameter and return arrays are finite. Every aggregate,
N and load curve point exactly equals recomputation from retained episode arrays.
Checkpoint parameter norms agree with learner distance traces and cumulative
path equals summed steps. Old source files remain unchanged.

| Configuration | Actual total fit seconds | Projection | Cap |
| --- | ---: | ---: | ---: |
| METRIC 0.1 | 6.205033 | 11.479243 | 60 |
| METRIC 0.3 | 4.097830 | 11.479243 | 60 |
| METRIC 1.0 | 4.181497 | 11.479243 | 60 |
| METRIC 3.0 | 4.386536 | 11.479243 | 60 |
| FREE 0.1 | 4.397693 | 6.155356 | 60 |
| FREE 0.3 | 4.504880 | 6.155356 | 60 |
| FREE 1.0 | 4.282750 | 6.155356 | 60 |
| FREE 3.0 | 4.210884 | 6.155356 | 60 |

Shared setup total 0.037501 seconds. Seed runner wall seconds are
12.216408,12.274268,11.823558 (sum36.314234); peak RSS bytes respectively
483786752,483717120,483131392. Each fit was below20 seconds, each setup below20,
each configuration below60, total below540. Actual per-update and full-evaluation
cost units remain in each fit's summary. Resource measurements are available;
no budget breach or truncated fit occurred. Scratch is not instrumented: this
card permits only wall/RSS telemetry and makes no resource-performance claim.

Remote prelaunch suite: 7 passed in3.52 seconds, one unrelated unknown cache_dir
warning. Local implementation checks and independent read-only review are in
technical evidence. Actual formal publication completed without failure, and
full raw evidence verification above establishes learner/publication coverage;
no open publication coverage item remains. No test or exit code establishes
scientific truth.

Scope:272 source lines,173 runner,127 tests. Reviewer orchestration estimate
110/399=27.57% of the whole research diff; source-only89/272=32.72%, disclosed
and accepted using the literal whole-diff denominator. No tests or numerical
code were added to change the ratio. Section4 additions none. No scientific
meaning, seed, rate, endpoint, budget or stop rule changed after observations.
