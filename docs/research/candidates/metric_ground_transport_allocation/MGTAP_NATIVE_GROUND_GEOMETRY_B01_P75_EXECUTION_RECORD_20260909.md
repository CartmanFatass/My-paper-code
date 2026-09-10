# MGTAP B01 P75 technical execution record - 2026-09-09

Latest state: COMPLETE, technically accepted. Both native pairs and the single
offline aggregate have exited and been collected. See Terminal technical
acceptance below; the preceding preparation/handle entries retain chronology.

P75 execution task at main 4a20de760 authorizes this batch. Source is fixed at
4f65eefb1b15e44b42d694376630fba0c230cc6c; production source is unchanged.
CM /root/cm_mgtap_p72_repair is sole executor and observer through collection.
Original DM /root/dm_mgtap_p51_geometry_question receives scientific intake
through Root. Authoring checkout is dm-n5-continue-20260904, codex/mgtap.

Per-arm projection: P74 analog REL148.267066867s + unknown delta_REL,
DENSE141.371892048s + unknown delta_DENSE, pair289.638958915s plus deltas.
Design caps remain1800s/complete arm and3600s/pair. This is a forecast, not an
upper bound. No calibration, pilot, smoke, retry, replacement or new arm.
Post-learner coverage: accepted P72 changed-path/publication/aggregate checks
and independent review are reused. Native publication and runtime remain to
be observed; no duplicate fixture is selected.

Exact LF inputs are p75_execution_inputs/run_8201.sh, run_8202.sh and aggregate.sh.
They bind the P74 cwd, node wsl_4070, configured interpreter and source revision.
Run8201 then8202, at most one accepted supervisor submission per master, fresh
joined physical/effective >=4GiB admission each. H remains diagnostic only.
Signed outcomes do not gate the second master. Aggregate is existing offline
publication, measured separately. No source changes or extra evaluations.

Pre-staging reconciliation: both exact handles returned not_found, and the
specified detached remote worktree was absent. Local declared source comparison
against fixed4f65eefb1 was empty. Input publication precedes remote staging.
No scientific invocation had been accepted at this record's preparation.

Pending: exact-SHA source/input staging, syntax/byte verification, single native
submissions, observation, complete collection and technical acceptance. Remote
source checkout/evidence will be retained until Root's integration/cleanup event.

## Staging and first accepted handle

Published inputs7990ff5b0 were staged with matching SHA-256:
run_8201.sh=8d13770130c7e2d9ff16d87117b9c74f91f9cb529081d5a0d4e0bdbf9b478997;
run_8202.sh=29c7d7fc627dd6076e8330adce32f345f01869a18cc5b4e9397142a8cb818122;
aggregate.sh=b8161087d451c03bb6ed0a56e277bd0a63a7b5bbc9a5cf90e34f9d0a62e621ed.
Remote HEAD is fixed4f65eefb1; declared source diff is empty and all staged
wrappers pass bash -n. Retrieval required the configured zsh -lic network
shell; two stalled plain-shell retrieval checks were terminated before staging
completed. This was source retrieval, not a scientific submission or retry.

Master8201 was accepted once as
mgtap-b01-8201-4f65eefb1b15e44b42d694376630fba0c230cc6c,
supervisor PID3034957. First observation: running, joined memory admission
passed, effective available15635890176 bytes and physical floor passed.
Actual task log and admission are collected at terminal state. Master8202 is
not yet submitted. Sole observer remains /root/cm_mgtap_p72_repair.

## Master8201 terminal collection

Supervisor finished/exit0 at2026-09-09T16:28:36+08:00. Complete external wall
353.71s; REL173.65472108195536s; DENSE/H/publication/exit remainder
180.05527891804462s. Collection/validation wall8.782s. All declared learner,
episode/rollout/optimizer counts, zero duration decisions, primary endpoints,
checkpoint finiteness/FP32 and copied size/SHA-256 comparisons pass.
Counts:286720 native team steps,2048 Adam calls,1120 complete episodes,
96 evaluations (32 each REL/DENSE/H), no partial steps and no limits.
The per-master reported difference is -0.04468252516448091; conditional SE
0.003273643145587254. This sign does not gate master8202.

Durable collection facts: MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_8201_TECHNICAL_COLLECTION.json.
Complete raw files/checkpoints and supervisor witnesses are retained at
C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/mgtap_b01_8201_4f65eefb1b15e44b42d694376630fba0c230cc6c/,
as well as the unchanged remote root. CM retains observation for master8202.

## Second accepted handle

Master8202 was accepted once as
mgtap-b01-8202-4f65eefb1b15e44b42d694376630fba0c230cc6c,
supervisor PID3036438. Its handle was reconciled as not_found immediately
before submission; remote source bytes still matched fixed4f65eefb1.
First observation was running, with fresh joined admission passed:
effective available15318556672 bytes and physical floor passed.
CM /root/cm_mgtap_p72_repair remains sole observer through terminal collection
and the existing timed offline aggregate. No further scientific run is selected.

## Terminal technical acceptance

Both accepted native handles are finished with exit0, and the one existing
offline aggregate command returned exit0. Exactly two native submissions were
accepted (8201 then8202); no retry, resume, replacement, extra evaluation,
calibration, source change or successor occurred. Complete collection and
technical acceptance are finished; no observation transfer is pending.

| master | native process wall | REL arm | DENSE/H/publication/exit | collection/validation |
| --- | ---: | ---: | ---: | ---: |
| 8201 | 353.71s | 173.654721s | 180.055279s | 8.782s |
| 8202 | 368.12s | 187.954188s | 180.165812s | 8.328s |

Master8202 finished at2026-09-09T16:36:51+08:00. Both arms and both pairs remain
well within1800/3600s, including a conservative charge of collection/validation
to the final arm. The aggregate process took0.81s. Summed remote native and
aggregate process wall is722.64s. Study critical path from first supervisor
start through aggregate timing-file completion is899.395665s (start recorded
to whole seconds); it includes observation/collection/inter-invocation gaps.
Control-plane collection timings are separately retained in JSON. Peak RSS,
activation memory and aggregate CPU work remain unmeasured; admission is not
a runtime memory-use measurement. GNU time wall is rounded to hundredths.

Both source/launch bindings, complete learner counts, episode/rollout counters,
all retained endpoint rows, zero duration decisions, finite FP32 checkpoints,
and remote/local file sizes and SHA-256 values pass. There are no limits,
partial episode steps or missing H endpoints. Counts across both masters:
573440 native team steps,4096 Adam calls,2048 training episodes,128 learned
sampled evaluations and64 diagnostic H evaluations:2240 episodes total.

| master | mean REL | mean DENSE | mean H | paired REL-DENSE |
| --- | ---: | ---: | ---: | ---: |
| 8201 | .147553181120 | .192235706284 | .147847381964 | -.0446825251645 |
| 8202 | .165518134487 | .168761817933 | .141367171777 | -.00324368344565 |

The existing aggregate reports mean-.02396310430506595,
training-pair sample SD .029301685983900646, and combined conditional evaluation
SE .0026485358205291165, with errors=[] and primary.complete=true. Independent
arithmetic over the collected pair summaries matches those quantities and the
fixed runner branch REL_ADVERSE. This is a technical application of the frozen
rule, not a new direction decision, causal claim, stable-superiority claim or
competence certification. The original DM performs scientific intake.

Durable artifacts:
- MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_8201_TECHNICAL_COLLECTION.json
- MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_8202_TECHNICAL_COLLECTION.json
- MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_TECHNICAL_RESULT.json

The complete raw run roots and checkpoints remain both remotely and in the
P74-named local collection roots. Aggregate files and their hashes are at
C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/mgtap_b01_p75_aggregate_4f65eefb1b15e44b42d694376630fba0c230cc6c/.
The actual observer through collection was /root/cm_mgtap_p72_repair.
Root is next owner for integration and forwarding to original DM. The designated
authoring checkout remains in use. The detached remote source/evidence checkout
is retained for source/result acceptance; Root owns its later reclamation after
verified evidence preservation, not deletion during this technical return.
