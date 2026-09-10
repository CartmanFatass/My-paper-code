# VSPC1 B04 P67 terminal technical collection

The single newly allocated P67 handle `vspc1_hold_value_b04_p67_8202` completed
with exit0 and inactive tmux. Native status is COMPLETE, publication readback
complete, with no limits/cap breach. This establishes technical conformance for
DM intake. P66's failed submission/evidence remain unchanged and separate.
[Machine evidence](VSPC1_NATIVE_HOLD_VALUE_B04_P67_COLLECTION_EVIDENCE_20260908.json)
retains exact native summary, every endpoint/difference, checks, hashes, full
supervisor log/wrapper and executed script. No second submission occurred.

## Source, artifacts and checks

Launch SHA `ec8b7c458b038b3a375ec5639834d0f3527fdf8c`; unchanged B04/master8202
scientific surface accepted at `a33a3820fe9d4a46a3231bcf267afc956554b6c5`.
Node `hmasd-wsl-node`, CPU FP32, fixed one numerical thread. Source cwd:
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b04-p67-8202`.
Output: `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_p67_8202`.
Direct staged-input and acceptance facts are linked in the
[technical execution record](VSPC1_NATIVE_HOLD_VALUE_B04_P67_TECHNICAL_20260908.md).

Terminal output and supervisor files plus adjacent admission were copied to this
checkout's `temp/directions/vsp_c1/collection/native_hold_value_b04_p67_8202/`.
Remote/local SHA256 values match for summary, episodes, rollouts, both final
checkpoints and admission. Collection check command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' temp/directions/vsp_c1/collection/native_hold_value_b04_p67_8202/check_collection.py
```

Exit0/PASS,5.5786043s artifact-only process wall. No model reconstruction,
forward, native evaluation, learning or scientific replay was used. Checks cover:
1120 scored episode rows,512 rollouts/2048 epoch records,286720 native team steps
(262144 training/24576 evaluation),2048 Adam,1024 training/96 final evaluations,
two constructor resets and zero partial steps. Native J/reward decompositions,
held-decision counts, full8202 reset identities, all three primary arithmetic
contrasts and sample-SD/sqrt32 SEs reconcile with the summary. FP32 checkpoint
identities, parameter counts/shapes/finiteness and final parameter/gate norms agree.

Both arms have131072 target rows/256 moment merges, recorded512-row increments
per rollout, normalized-squared value loss, and matching final checkpoint/summary
moments frozen before/after learned evaluation and H. Final moments:

| Arm | mean | M2 | scale |
| --- | ---: | ---: | ---: |
| GATED-V |19.78407096862793|30108494|15.156172752380371|
| MLP-V |20.633365631103516|29706446|15.054640769958496|

Raw full RTG arrays are not separately replayed/archived. Accepted arithmetic
source/tests and actual recorded state/publication cover this boundary.

## Endpoint facts for DM

| Arm | Mean native J |
| --- | ---: |
| GATED-V |.19726280882081323|
| MLP-V |.17416448243082688|
| H |.14136717177746932|

| Matched contrast | Mean | Conditional SE |
| --- | ---: | ---: |
| GATED-V minus MLP-V |.02309832638998633|.008740309282664975|
| GATED-V minus H |.055895637043343896|.01402017897123588|
| MLP-V minus H |.03279731065335756|.012954036294274218|

The published card-region reading is UP. All32 matched values and adverse
identities remain in the evidence; conditional SE does not measure training-seed
uncertainty. This CM does not aggregate8201/8202 or infer stable superiority.
DM owns all-outcome interpretation, forecast scoring and any next scientific choice.

Machine-reported total relative displacement is GATED .2534176631653249 /
MLP .23690194561741526. Gate absolute movement .5487287640571594 from zero;
duration absolute movement .1657041609287262 / .11938440799713135 from zero.
Their relative displacement is undefined. Raw legacy epsilon duration ratios are
preserved in native summary only; the collection's explicit zero-initial-norm
reporting maps them to null, not numerical exposure evidence. Nonzero hold-input
rows are GATED1497 train/90 eval and MLP1488 train/90 eval.

## Actual admission and complete resource accounting

Remote admission at2026-09-09T02:40:39.232806Z passed both physical/effective
availability15,639,040,000 bytes. This actual-node receipt admitted the adjacent
invocation. Supervisor started2026-09-09T10:40:39+08:00 and ended10:45:51+08:00;
its integer timestamp difference is312s. Enclosing `/usr/bin/time` wall is312.77s
through admission/native process exit; peak RSS555844KiB (542.81640625MiB).
Integer supervisor duration and fractional timer have different granularity;
complete cap assessment uses the enclosing timer.

Internal wall305.7251625119825s, MLP transition159.03897231799783s, unpartitioned
nonnegative residual7.044837488017492s. Assigning its full amount to each arm gives
conservative upper bounds166.08380980601532s GATED and153.73102768200215s MLP.
Both meet1800s/arm; enclosing312.77s meets3600s/pair. Startup/common initialization
is charged to GATED and H/publication/readback/exit to MLP. Residual bounds do not
claim an exact phase-time split. The serial study critical path and summed
invocation wall are312.77s. Aggregate CPU and normalization-specific overhead
remain unmeasured; observed process RSS is not aggregate machine memory.

P67 technical execution and collection are complete. No live observer handover or
additional invocation remains. The same DM receives this result for intake; Root
integrates named commits and maintains tracking. P66 remains closed with its
original failure, and P67 allocates no successor.
