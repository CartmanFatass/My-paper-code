# VSPC1 B03 terminal collection

The sole corrected P60 scientific handle
`vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1` finished with exit0 and inactive tmux.
Native summary is COMPLETE with complete publication readback, no limits and no cap
breach. [Machine evidence](VSPC1_NATIVE_HOLD_VALUE_B03_COLLECTION_EVIDENCE_20260908.json)
retains the exact summary, all endpoint values/differences, collection checks,
admission, supervisor script/log and artifact hashes. The original pre-admission
cwd failure remains separately preserved in the
[cwd evidence](VSPC1_NATIVE_HOLD_VALUE_B03_CWD_CORRECTION_EVIDENCE_20260908.json).
No second scientific invocation, replay, evaluation or fit was executed in collection.

## Identity and technical acceptance

Source: `7a8ed3aa5d25ded71164aa338749d09318124dcf`; seed8201, B03 card/object,
CPU FP32, common cumulative population normalization and entropy.01. Remote cwd:
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`.
Exact result root:
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`.
The terminal output files were copied under the designated local checkout's
`temp/directions/vsp_c1/collection/native_hold_value_b03_8201_7a8ed3aa5d25/`.
Remote SHA256 values match local bytes for summary, episodes, rollouts, both final
checkpoints and the sibling admission receipt. Supervisor terminal files are retained.

Executed collection check (read-only existing artifacts;2.291s command wall):

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' temp/directions/vsp_c1/collection/native_hold_value_b03_8201_7a8ed3aa5d25/check_collection.py
```

Exit0/PASS. Checks reconcile1120 complete episode rows,512 rollout rows and2048
four-epoch records against native counters:286720 team steps,262144 train/24576 eval,
2048 Adam,1024 train/96 eval episodes, two constructor resets, zero partial steps.
All retained numerical values are finite. Every episode reward decomposition and J,
held-action decision count, seed/reset identity and all32 matched final endpoints
reconcile. Both checkpoint identities, FP32 tensor shapes/counts/finiteness and final
parameter/gate norms agree with the summary. No model reconstruction/forward was used.

Each arm records exactly256 moment merges and131072 scalar targets. Per-rollout n
advances by512 and updates by1; final moments match both checkpoint and summary,
and are identical before/after learned evaluation and after H. Every epoch/rollout
labels normalized-squared value loss. Final state:

| Arm | mean | M2 | scale |
| --- | ---: | ---: | ---: |
| GATED-V |17.709501266479492|25492082|13.945937156677246|
| MLP-V |17.751535415649414|24964986|13.801004409790039|

This establishes recorded state/count/publication conformance. Complete raw RTG
arrays were not separately archived/replayed; normalization arithmetic and native
advantage timing retain the accepted source and focused-check evidence.

## Native endpoints for DM intake

| Endpoint | Mean native J |
| --- | ---: |
| GATED-V |.18306017943960662|
| MLP-V |.14325846413504909|
| H |.14784738196394714|

| Matched contrast | Mean | Conditional SE |
| --- | ---: | ---: |
| GATED-V minus MLP-V |.03980171530455754|.006008657101475142|
| GATED-V minus H |.03521279747565949|.010408850908328956|
| MLP-V minus H |-.004588917828898052|.012026063667580491|

Recomputed from all32 identity-matched native endpoint rows using sample SD/sqrt32;
all three differences/means/SEs exactly match published primary arithmetic. The
runner's card-region reading is UP. These SEs condition on one training pair and do
not estimate training-seed uncertainty. DM owns interpretation and all-outcome intake,
including the negative MLP-minus-H point estimate and every adverse episode.

Exposure from the executed summary: total relative displacement GATED
.2621670954795077 / MLP .25396332210330247; gate absolute displacement
.6060495972633362 from zero (relative null). Duration-head legacy relative values use
the historical epsilon denominator from zero initialization; their absolute
movements are .11403322219848633 / .10539168864488602. These are exposure facts,
not a performance explanation.

## Admission and complete wall

The actual remote admission passed physical/effective availability15,634,731,008
bytes, measured2026-09-08T22:53:22.837261Z. Local preflight was not substituted for
this actual-node receipt. Supervisor started2026-09-09T06:53:22+08:00 and exited
06:58:33+08:00, duration311s. `/usr/bin/time` reports enclosing310.79s and peak
RSS562504KiB (549.3203125MiB), covering admission plus native process through exit.

Internal wall310.41653345897794s; MLP transition160.96011829999043s. The nonnegative
unpartitioned residual is.37346654102208277s. Charging the entire residual to each
arm gives conservative upper bounds161.3335848410125s GATED and149.8298817000096s
MLP. Both conform to1800s/arm and enclosing wall conforms to3600s/pair, with startup
charged to GATED and H/publication/readback/exit included for MLP. Residual allocation
is conservative, not an exact phase-time measurement. One serial logical invocation
means study critical path and summed invocation wall are310.79s; aggregate CPU and
normalization-specific overhead remain unmeasured. Peak RSS is observed process
memory, not total machine usage.

P60 collection is complete. Root integrates these technical records and continues
the same DM for scientific intake; no additional execution is allocated.
