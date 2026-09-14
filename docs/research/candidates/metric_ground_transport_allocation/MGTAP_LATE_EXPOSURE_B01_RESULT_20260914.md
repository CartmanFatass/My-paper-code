# MGTAP-LATE-EXPOSURE-B01 — complete native result

Source90f835e10357fbbf465cc5d500a93f1e2d4ab226; master8254; one new matched COND/DENSE training pair, fixed1e-4,512 training episodes and256/512 observations. All required endpoints completed. Primary final512 **COND−DENSE=-0.005375013231600323 J**, conditional paired-world SE0.004649366246290445: **INSIDE_MEI**.

## Card rule applied verbatim

“Primary strict delta>+0.01: COND_ABOVE_MEI; strict delta<-0.01: COND_ADVERSE; inclusive band: INSIDE_MEI. Every final row stays.”

The original ordered32-world final reducer was reproduced from the complete raw rows; no checkpoint or world was selected after seeing its score.

| Training endpoint | COND mean J | DENSE mean J | Ordered difference | Conditional world SE | Positive / negative worlds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 256 (descriptive) | 0.09595785820780596 | 0.08758757884879717 | +0.008370279359008794 | 0.0014115631565087363 | 26 / 6 |
| 512 (primary) | 0.1277920207332075 | 0.1331670339648078 | -0.005375013231600323 | 0.004649366246290445 | 15 / 17 |

Both endpoints are inside the declared scale. Within this same learning path, COND rose0.03183416252540154 J and DENSE rose0.045579455116010636 J; the gap changed-0.013745292590609116 J. These are changes between two states of one learning process, not two independent seed outcomes or an isolated causal dose effect. Training-population SD is null/unestimated. The conditional evaluation SE does not include new-training uncertainty.

## Execution, counts and technical evidence

Configured hmasd-wsl-node accepted mgtap-late-exposure-b01-8254-20260914, PID3694820, at23:24:56Z. Adjacent4GiB physical/effective admission passed15587618816 bytes. Supervisor finished/exit0 at2026-09-14T23:30:56Z; its+08 log is the same instant. Whole command360.00s, peak561596KiB (548.43359375MiB). COND189.38205022900365s and DENSE168.54817102500238s are fit bodies nested within that command, not additive outside costs. Full support/provider/engineering/lifetime/aggregate CPU totals remain UNKNOWN.

Actual2fits,1024 training+128 evaluation episodes,294912 team ticks,512 rollouts,2048 Adam calls and6717440 configured actor collection/evaluation/replay row uses.1152 episode rows and512 rollout rows match the real emitted counters and card addresses. Each arm's checkpoint Adam states are512 after256 episodes and1024 after512; the same optimizer continues. Total parameter displacements COND2.986039161682129→4.302816867828369, DENSE3.2927403450012207→3.9585959911346436. All recorded required fits/panels are complete, partial_fits and limits empty.

DM data-only readback checked all episode master/rate/phase/address/H bindings, both full panel reductions, actual checkpoint metadata/Adam continuity and finite nonzero learner movement. [Analysis](late_exposure_b01_8254/ANALYSIS.json), [script](late_exposure_b01_8254/analyze_intake.py), [raw summary](late_exposure_b01_8254/RUN_SUMMARY.json), [all paired scores](late_exposure_b01_8254/PAIRED_SCORES.csv), [one-run endpoints](late_exposure_b01_8254/FINAL_RUN_SCORES.csv), [run-level description](late_exposure_b01_8254/FINAL_RUN_DESCRIPTIVE.json).

Independent source/synthetic review found no material defect; DM12 tests/4.69s and independent counterexample4.75s were engineering checks, not native replicates. [Engineering record](late_exposure_b01_8254/ENGINEERING.md) and [full Reviewer return](late_exposure_b01_8254/INDEPENDENT_REVIEW.md) give the coverage and limits.

## Preservation and deviations

All8 native originals and6 supervisor originals match remote/local SHA256 and lengths. [NATIVE_EVIDENCE.zip](late_exposure_b01_8254/NATIVE_EVIDENCE.zip):3334990bytes,15 members including raw MONITOR.json, SHA256 a4aa0713a72396e12c593ae92996850d7e4bcda5a600f2ab9c611bc48f33e935; every member read back. [Collection](late_exposure_b01_8254/COLLECTION.json) records the exact originals, archive and cleanup state. Four original checkpoints are preserved.

No scientific invocation/count/comparison deviation or §5 implementation budget breach was found. Native Monitor initially returned healthy nonterminal facts prematurely and lacked a callable native-message route; DM resumed the same child until its terminal final, without duplicate observation authority or experiment. Raw MONITOR.json overwrote its initial adoption and reused program-finish time as terminal adoption. The engineering/collection record preserves the actual initial23:26:44Z adoption and terminal uptime452s separately; no precise terminal-observation UTC is invented. This observation metadata defect does not damage native rows, checkpoints, exit or command timing.

DM local test scratch remains because the original combined check/deletion command was rejected before process creation (`blocked by policy`); the permitted non-destructive check passed. No alternative deletion mechanism was used. Remote exact-checkout cleanup awaits verified evidence publication at this record's creation; shared authoring/source/evidence remain retained.
