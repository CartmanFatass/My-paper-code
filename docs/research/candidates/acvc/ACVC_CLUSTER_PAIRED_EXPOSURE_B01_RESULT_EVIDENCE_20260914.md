# ACVC paired-exposure B01 — E0 result evidence

**Technically accepted B/EXPLORE: both fixed endpoints have separate F−C and F−own-dwell UP readings; the designated F−dwell increment DECREASES across snapshots.** One new C-only programme, master22591/eval32591, source `8fd41b61f3c8d3c70057492a18e619ef0faeda78`. [Frozen card](ACVC_CLUSTER_PAIRED_EXPOSURE_B01_SCIENCE_CARD_20260914.md), [original summary](evidence/cluster_paired_exposure_b01_20260914/summary.json), [all-row analysis](evidence/cluster_paired_exposure_b01_20260914/INTAKE_ANALYSIS.json). Both fixed512/1024 checkpoints were saved after their ordered updates; all six private panels occurred only after training ended.

## Separate endpoint readings and absolute arms

J=S/256. Endpoint thresholds are strictly >+.01J UP, inclusive±.01 WITHIN retaining sign without equivalence, strictly <−.01 DOWN. Dwell−C is descriptive. Every64-value vector remains in the original summary; these are conditional worlds under one programme, not independent fits.

| Snapshot | Contrast | Mean J | Sample SD | Conditional SE | Negative / positive / zero | Minimum | Maximum | Reading |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 512 | F-C | +0.1405118427 | 0.0777215541 | 0.0097151943 | 5 / 59 / 0 | -0.0664257065 | +0.3076188638 | UP |
| 512 | F-dwell | +0.1191862743 | 0.0729241226 | 0.0091155153 | 7 / 57 / 0 | -0.0880854107 | +0.2844216352 | UP |
| 512 | dwell-C | +0.0213255684 | 0.0515110909 | 0.0064388864 | 18 / 46 / 0 | -0.1350751525 | +0.1403955907 | DESCRIPTIVE |
| 1024 | F-C | +0.1132431734 | 0.1022810536 | 0.0127851317 | 9 / 55 / 0 | -0.1477754310 | +0.3144799868 | UP |
| 1024 | F-dwell | +0.0687279633 | 0.0955491406 | 0.0119436426 | 10 / 54 / 0 | -0.2238660859 | +0.2932091479 | UP |
| 1024 | dwell-C | +0.0445152100 | 0.0737528270 | 0.0092191034 | 20 / 44 / 0 | -0.1201634602 | +0.2102458149 | DESCRIPTIVE |

| Snapshot | Arm | Mean S | Mean J |
| --- | --- | ---: | ---: |
| 512 | C | 21.385373698172490 | 0.083536616008486 |
| 512 | F | 57.356405422305933 | 0.224048458680883 |
| 512 | dwell | 26.844719203833744 | 0.104862184389976 |
| 1024 | C | 54.037213423888929 | 0.211082864937066 |
| 1024 | F | 83.027465811382967 | 0.324326038325715 |
| 1024 | dwell | 65.433107194391440 | 0.255598074978092 |

## Direct paired changes and preserved covariance

G_Q is the mean of64 worldwise `(F1024−Q1024)−(F512−Q512)` values, computed directly in NumPy float64. The designated G_dwell and supporting G_C use strictly beyond±.01J INCREASE/DECREASE and inclusive WITHIN without equivalence. Endpoints remain separate from these changes.

| Change | Mean J | Sample SD | Conditional SE | Negative / positive / zero | Minimum | Maximum | Reading |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| G_dwell | -0.050458310943 | 0.093611807653 | 0.011701475957 | 46 / 18 / 0 | -0.237714582251 | +0.217168480594 | DECREASE |
| G_C | -0.027268669284 | 0.100998987235 | 0.012624873404 | 43 / 21 / 0 | -0.221516123325 | +0.262237151704 | DECREASE |

Endpoint sample covariance is0.0028421976924286755J² for F−dwell and0.003150629234668905J² for F−C. The direct change sample variances0.008763170531973933/0.010200795422525936J² agree with late variance+early variance−2covariance. Change SE is SD/8; adding independent endpoint variances would discard this pairing. All64 change values, signs and extrema are retained.

F−dwell declines from+0.1191862743 to+0.0687279633J while the later endpoint remains useful by the frozen mean criterion. F−C similarly declines from+0.1405118427 to+0.1132431734J. Absolute C rises0.0835366160→0.2110828649, F0.2240484587→0.3243260383 and dwell0.1048621844→0.2555980750 on the common evaluation worlds. This is attained improvement within this programme, with data and optimizer exposure bundled; no isolated causal factor or neural-training population improvement follows.

Later F−dwell still has10/64 adverse worlds and minimum−0.2238660859J (earlier7/64,minimum−0.0880854107). Later F−C has9/64 adverse worlds/minimum−0.1477754310; later dwell−C has20/64/minimum−0.1201634602. These tails qualify mean usefulness and deny a safety/default guarantee. F/own-dwell interventions were6286/2952 at512 and6422/4724 at1024, each on its private evolving trajectory/history. Dose matching, pure retrace/history causality and universal dwell safety are not established.

## Actual exposure, cost and preservation

All1408 scored episode rows and2048 ordered update records pass identity/reset/finiteness/order checks. Workload262144training+98304evaluation=360448team ticks;512rollouts,2048backward/Adam calls,one fresh fit,two fixed snapshots,six loads,seven environment constructors. Snapshot512 follows rollout255/update1024; snapshot1024 follows rollout511/update2048. Native cost_law exactly matches this complete invocation. Clustered5UAV/50users,H256,privateGRU64,training-only critic,CPU FP32/allthreads1 and unchanged C-only learner are retained. Zero selector/evaluation updates,gate constructions or duration heads. Native limits are empty.

Actor34902+critic34177=69079 parameters. Actor displacement from initialization is2.824805974960327/3.033222198486328 at512/1024 (initial norm12.520986557006836; relative0.2256057030409732/0.2422510546334444). Critic displacement5.939180850982666/9.542083740234375 (initial norm9.308382034301758). These document actual learning exposure, not an unmeasured initial-return comparison.

Fresh adjacent remote admission15:10:31.646436Z passed physical/effective15632191488bytes against4294967296bytes. Supervisor records2026-09-14T15:10:31Z→15:15:56Z,exit0,rounded325s. Complete native wall **324.92s**, peak549536KiB (**0.524078369140625GiB**). Internal publication elapsed311.58278230100404s and collector supervisor uptime403s are separate, incomplete timing boundaries. Native500s and rough330s projections were estimates; full cumulative support/provider/agent cost remains UNKNOWN. Five implementation test commands total13.9843776s observed tool wall, not total engineering cost. No watchdog or scientific retry occurred.

Original archive **837148bytes**, SHA256 `ccd9595e4573cc4ece0a9eb45fa408a7ea4f89a53d1a37769b7365eaffb9fb22`, retained at `temp/directions/acvc/retained/cluster_paired_exposure_b01_20260914/native_output.tar.gz`. It preserves9native+6supervisor files. Both checkpoints remain only in that archive:512 snapshot283165bytes/SHA256`1226b29b0b40288552379fe3d063090031952434205535b56ea4b8a8efdf08ab`;1024 snapshot283189bytes/SHA256`afa40fe225cd059726e1848533174c1da406d672e58aeea70580bbb23c2b7953`. Thirteen published text files preserve original bytes. [Manifest](evidence/cluster_paired_exposure_b01_20260914/NATIVE_ARCHIVE_MANIFEST.json) and [execution facts](evidence/cluster_paired_exposure_b01_20260914/EXECUTION_FACTS.json) retain identities/timing. No model was loaded at intake. DM completed remote cleanup after exact-byte publication and all15-file preservation: execution worktree,supervisor directory,staging archive are absent on disk and from Git. The local original archive remains verified; [cleanup receipt](evidence/cluster_paired_exposure_b01_20260914/REMOTE_CLEANUP.json) records the checks.

Independent Sol/high source review found no material issue;9final synthetic tests passed1.83s. Initial duplicate Torch setup failure and all four reasoned reruns remain documented. Creator-owned policy-blocked scratch/pyc/empty directories remain preserved. Monitor routing/placeholder metadata errors and two premature running finals were corrected through the same child/handle; actual terminal arrived directly with empty active set. Observation gaps are not claimed as active coverage, and no second scientific process occurred.

## Claim ceiling, forecasts and scientific review

This one programme supports attenuation without disappearance of fixed-F mean added value at its later attained endpoint. It does not estimate training-population prevalence, isolate data versus optimizer effects, prove competence calibration, choose a checkpoint or supply a pooled confirmation with old programmes. Both endpoint contrasts share F, snapshots are correlated,64worlds conditional. No deployment/default/safety,component causality,tuned headroom,transfer or formal-UAV claim. Uniform C01 and failed learned-gate/train-through-F/uncertain families remain unchanged.

Prospective endpoint forecasts scored UP at both stages: F−C Brier0.14 each,F−dwell0.245 each; G_dwell DECREASE Brier0.545; completeness0.0025. Owner prediction not taken (unattended). The complete73-line independent review at68fed46f4 is read and all material findings answered in the intake; no empirical repair is identified. The DM selects a complete Portfolio development/retention report now over automatically adding another unpaired/exploratory exposure object; a prospectively sampled fixed-recipe clustered C-BENCH is the strongest live alternative for an expected-population question. This is discretionary next-question judgment, not a lifecycle verdict or automatic empirical successor.
