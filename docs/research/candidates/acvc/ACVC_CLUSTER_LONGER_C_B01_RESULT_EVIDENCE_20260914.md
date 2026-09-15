# ACVC longer-C B01 — E0 result evidence

**Technically accepted B/EXPLORE; both separate frozen primary readings are UP.** One fresh1,024-episode C fit, master22319/eval32319, source `914a3d0e78d49d385c54aaec0776ead63712b624`. [Frozen card](ACVC_CLUSTER_LONGER_C_B01_SCIENCE_CARD_20260914.md), [original summary](evidence/cluster_longer_c_b01_20260914/summary.json), [all-row analysis](evidence/cluster_longer_c_b01_20260914/INTAKE_ANALYSIS.json). No initial evaluation, checkpoint selection or scientific retry. This is a changed-exposure object, not a fourth unchanged512-episode programme.

## Frozen comparisons and actual outcomes

J=S/256. Strictly >+.01J is UP; inclusive [−.01,+.01] is WITHIN retaining sign without equivalence; strictly <−.01 is DOWN. Both primaries are separate and share F; dwell−C is descriptive. Native NumPy float64 values and all64 signed differences per contrast remain in the original summary.

| Contrast | Mean J | Sample SD | Conditional SE | Adverse / favorable / zero | Minimum | Maximum | Reading |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| F-C | +0.1292634628 | 0.0746257000 | 0.0093282125 | 1 / 63 / 0 | -0.0532010707 | +0.3004851932 | UP |
| F-dwell | +0.0635578296 | 0.0896257819 | 0.0112032227 | 15 / 49 / 0 | -0.1859325036 | +0.3403342958 | UP |
| dwell-C | +0.0657056332 | 0.0837987125 | 0.0104748391 | 10 / 54 / 0 | -0.2814743148 | +0.2927441895 | UP |

| Arm | Mean S | Mean J |
| --- | ---: | ---: |
| C | 44.658179285461131 | 0.174446012833833 |
| F | 77.749625768854841 | 0.303709475659589 |
| dwell | 61.478821390800618 | 0.240151646057815 |

F made6,595 retraces; own-dwell made4,825 dwell interventions on its own evolving history. Both are package consequences with different trajectories, recurrent state and teammate responses. Useful dwell−C+0.0657056332J and F−dwell's15/64 adverse worlds/worst−0.1859325036J are central qualifications. Neither dose matching nor pure history/retrace causality follows.

## Actual exposure and technical validity

Exactly1,024 training episodes,512 two-episode rollouts,2,048 ordered backward/Adam/update records,one fresh initialization/fit/final checkpoint,three private loads and192 final evaluation episodes. All1,216 episode rows and2,048 ordered update rows passed identity/reset/count/finite checks. Counts are262144 training+49152 evaluation=311296 team ticks. The corrected native `cost_law` reports precisely these counts. Native default scientific paths remain C-only PPO, CPU FP32/intra/inter threads1,clustered5UAV/50users,H256,privateGRU64 and training-only critic; evaluation/selector updates, gate constructions and duration heads are zero.

Actor34,902 plus critic34,177=69,079 parameters. Actor displacement3.1679012775421143/initial norm12.596080780029297 (relative0.2514989648656806); critic displacement9.878192901611328/initial norm9.287044525146484. Actual learning exposure is demonstrated; return improvement from initialization was not measured. Independent stdlib recorded-byte mean/SD checks match native float64 reductions within absolute1e-14; no new model/environment invocation.

## Complete native cost and preservation

Fresh adjacent remote admission at2026-09-14T14:08:46.682793Z passed physical/effective15,632,846,848bytes against4,294,967,296bytes. Supervisor log records start14:08:46Z,exit0 at14:13:42Z,rounded296s. Full native runner/publication/exit wall **296.30s**, peak548,524KiB (**0.5231132507GiB**). Internal publication elapsed282.0058523611s is not the complete process cost. Monitor terminal-observation uptime311s is also not native runtime; local observation and remote wall timestamps are retained as their own clock records without assuming synchronization. No watchdog triggered. The450s native plan and~294.286s doubled-fit reference were estimates, not hard caps or evidence of scaling law; all support/provider/agent cumulative cost remains UNKNOWN.

Native archive **561,848bytes**, SHA256 `1e2d9e304a8c36908ed25710c7c367ac51ba1addfc8cb873e0ca249342f9f7dd`, retained at `temp/directions/acvc/retained/cluster_longer_c_b01_20260914/native_output.tar.gz`. The sole checkpoint282,893bytes, SHA256 `a58961caca5de291f63f0d85c178c9f0ba289f608e966edeed40ebf149a744e3`, remains inside that archive and was not loaded at intake. [Member record](evidence/cluster_longer_c_b01_20260914/NATIVE_ARCHIVE_MANIFEST.json) covers native8 and supervisor6 files. Published raw files preserve original bytes. Remote cleanup is owned by this DM after verified preservation and will be recorded on completion.

Engineering26-test and independent Sol/high review passed; shared workload reporting was repaired prospectively with no learner change. Two test-cleanup commands were policy-rejected before deletion, leaving only that known scratch with original DM ownership. The native Monitor twice returned prematurely while running and was resumed on the same accepted handle; actual terminal facts then arrived directly, with no second launch. These operational limitations are recorded in [intake](ACVC_CLUSTER_LONGER_C_B01_INTAKE_20260914.md) and [execution facts](evidence/cluster_longer_c_b01_20260914/EXECUTION_FACTS.json).

## Scientific meaning and forecast scoring

At this attained higher-exposure endpoint, F exceeds both C and useful own-dwell in the two fixed mean readings. C/F/dwell means are higher than B03, yet C and F remain below K/B01's0.1972374081/0.3213104326J. Changed train/eval roots plus changed exposure prevent attribution to training duration or a pure training-variance/competence effect. Fifteen F−dwell adverse worlds and its wider tail challenge a safe/default-use claim even while mean increment exceeds .01J. Sixty-four worlds describe one learned endpoint, not64 independent fits. Do not pool this changed recipe with the three prior512-episode programmes as a preregistered study.

No training-population stability, calibrated joint confidence, deployment/default, tuned-headroom, component causality, transfer or formal-UAV conclusion. Original uniform C01 and all failed families stay separate. Subjective prospective forecasts scored UP/UP: Brier0.185/0.305,completion0.0025; owner prediction not taken (unattended). A full independent scientific result/next-question review and DM response follow; this evidence acceptance makes no direction-level disposition or automatic successor selection.
