# FSD B01 P38 terminal collection

All three allocated invocations completed with supervisor exit0 and readable
complete summaries. C and H each performed five real updates, 32,000 training
transitions/80 episodes and one final 32-episode evaluation. H published the
complete H−C and G-reference panel inside its invocation. No missing comparison
was completed after the run, and no scientific process was repeated.

The [exact launch binding](FSD_NATIVE_RENEWAL_LEARNING_B01_P38_ROOT_HANDOFF_20260908.md)
remains controlling: source `b3f86bb28879db239b07291c39d93a1c494abe50`, node
`wsl_4070`, detached cwd `/home/wu/hmasd-worktrees/fsd-native-renewal-b01-p38-b3f86bb28`,
masters770203/770204, CPU4, float32 learner/float64 host and shared reward.
Root accepted and observed the same three handles, without retries:
`fsd_native_b01_p38_{G,C,H}_b3f86bb28`. The collected supervisor wrappers match
the published admission-inclusive timeout commands.

## Raw evidence and readback

The ordinary [results directory](native_renewal_learning_b01_p38_20260908/results/)
archives the terminal received bytes for every arm: `summary.json`,
`admission.json`, `process_time.txt` and the full existing supervisor directory
(`task.log`, `status`, `exit_code`, `pid`, `start_time`, `runner.sh`). Sources are
the exact remote paths in the launch binding, copied by SCP after terminal
receipts. No source/runner/config/test or card changed during collection.

[Readback facts](native_renewal_learning_b01_p38_20260908/results/readback.json)
record measured exposure, walls, RSS, means and the already-published pair
statistics. A short local NumPy/JSON readback of these recorded bytes verified:

- Each identity/config/seed, completed status and null failure matches the
  binding. Admission passes and supervisor exit0 agree with the published wrapper
  and terminal log. Each full/post return vector has 32 finite entries in ID order.
- Learned arms retain all five consumed ID blocks0–15 through64–79; each row
  records400 steps/lane,6,400 stored transitions,16 completed episodes and updated
  status. Native means agree with recorded sums/400. Per-network call deltas sum
  to their final totals; all initial-to-final displacements are finite. Initial
  parameter norms and learner configurations match between the paired starts.
- Each learner's final evaluator reports zero optimizer calls. All three
  endpoints contain400 valid reward steps/lane and32 completed episodes. Full
  and post means agree with recorded reward sums/400 and/399. Eligible/wrong
  counts, conditional rates and reward-unit role loss agree with their published
  denominators; no classifier substitutes for the native return.
- H's six published paired vectors exactly equal the corresponding recorded
  arm differences. Their means and ddof1 SE agree with those vectors. Both panel
  and reference status are complete. This is consistency readback, not a new
  result-bearing aggregation or repair of missing output.

The readback exited0. Its temporary command source is
`temp/directions/flexible_skill_duration/collection/p38/check_readback.py` in the
authoring checkout; retained raw data/readback facts suffice for inspection.
No model, host, optimizer, test suite, profiling or calibration was invoked by
collection. No traceback, nonfinite failure or warning occurs in the full
supervisor logs. Source/check acceptance remains the previously accepted P34
18-test suite and independent review, without repetition.

## Complete cost and admission

| Arm | Complete external wall s | Cap s | Peak RSS KiB | Physical/effective admission bytes | PID |
| --- | ---: | ---: | ---: | ---: | ---: |
| G | 2.47 | 60 | 459268 | 15651823616 | 2769358 |
| C | 371.89 | 900 | 1383224 | 15650422784 | 2769474 |
| H | 333.89 | 900 | 1390068 | 15650050048 | 2769744 |

Fresh on-node receipts were captured respectively at
2026-09-08T08:44:05.731457Z,08:44:41.310199Z,08:53:16.220948Z. Both required
memory floors passed against4,294,967,296 bytes. All three process-time records
report exit_status0. The external timeout wraps admission and the entire runner;
the table therefore uses the complete command, including required startup,
learning/evaluation and closed-file publication, instead of the runner's narrower
wall timestamps (G2.037934174s,C358.867690250s,H322.035028077s).

Summed complete invocation wall is **708.25s**, below the allocated1860s. The
supervisor's first start08:44:05Z through final finish08:58:50Z spans **885s** at
its one-second timestamp resolution, including between-arm observation/dispatch
gaps. Supervisor durations are G3s,C372s,H334s. Aggregate CPU is unmeasured;
unchanged serial CPU/four-thread execution did not add a throughput assessment.
The historical planning anchors were not substituted for these measurements,
and segment rows were not relabelled as the old cost-law M.

## Actual learning and endpoint exposure

| Quantity | G | C | H |
| --- | ---: | ---: | ---: |
| Model constructions | 0 | 2 | 2 |
| Training starts | 0 | 1 | 1 |
| Stored training transitions | 0 | 32000 | 32000 |
| Training episodes / update stages | 0 / 0 | 80 / 5 | 80 / 5 |
| Endpoint episodes / scoring steps | 32 / 12800 | 32 / 12800 | 32 / 12800 |
| Coordinator optimizer calls | 0 | 615 | 495 |
| Actor / critic optimizer calls | 0 / 0 | 2250 / 2250 | 2250 / 2250 |
| Team / individual discriminator calls | 0 / 0 | 75 / 300 | 75 / 300 |

Totals are two training starts, four model constructions,64,000 stored training
transitions,160 training episodes,10 update stages,96 endpoint episodes and38,400
scoring steps. Combined host exposure is102,400 steps and614,400 agent observations.
There are no checkpoint loads or evaluator optimizer calls. The independent
training unit remains one paired seed, not160 training or96 evaluation episodes.

All five rows preserve actual individual/team segment counts and length summaries,
coordinator inference calls, `rows_M_agent`, `rows_M_team`, `rows_M`, internal and
applied renewal counts, per-network call deltas/totals and initialization-relative
displacement. `rows_M` is the core's actual decision-row metric, not the sum of
individual/team segment counts and not an optimizer-call count. Raw summaries
retain first/final exposure for every network; no positive-displacement rule was
used to accept the result.

## Published measurements for DM intake

| Published paired measurement | Mean | Conditional episode SE |
| --- | ---: | ---: |
| H−C full | 0.49738281249999894 | 0.00864640484198601 |
| H−C post | 0.49862938596491124 | 0.008668075029559913 |
| G−H full | 0.021184895833334313 | 0.001613971807427201 |
| G−H post | 0.0187317251461998 | 0.0016180168495510767 |
| G−C full | 0.5185677083333332 | 0.008570016255319007 |
| G−C post | 0.517361111111111 | 0.008591494992801013 |

The archived H summary contains all32 paired values for every row, not just these
means. Full native means are G.8937890625,C.3752213541666668,H.8726041666666656.
Post means are G.8935228696741855,C.37616175856307443,H.8747911445279857.
C has3738 wrong of32555 eligible opportunities; H1435 of68451 (both full and
post because reset renews every learned entity). Their post reward-unit role-loss
means are.048793859649122806 and.01873172514619883. H's published G−H less H-role-loss
residual is.0025000000000009797 full and9.705777848090236e-16 post. These are retained
accounting observations, not a unique attribution or a required zero test.

There is no remaining technical completion/cap/primary-publication gap in the
collected panel. Technical acceptance establishes the named invocation and
measurement conformance only. DM `/root/dm_fsd_p13_reentry` owns the all-outcome
scientific intake, prediction/MEI reading and any next decision through Root.
No additional scientific work follows from this collection.
