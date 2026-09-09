# VSPC1 NATIVE HOLD VALUE B06 - E0 result evidence

The sole P71 invocation completed with exit 0, native status COMPLETE, complete
publication readback and no limit/cap breach. Technical acceptance is PASS.
The frozen point-estimate reading is WITHIN, with negative GATED-minus-MLP sign.
No second submission, retry, extra evaluation or successor was executed.

[Collected evidence](results/native_hold_value_b06_8302_20260908/evidence.json)
contains the native summary, all 96 evaluation rows and matched contrast values,
every adverse identity, artifact-check source/results, remote/local hashes,
admission and complete terminal receipts. Exact inputs are in the
[staging evidence](VSPC1_NATIVE_HOLD_VALUE_B06_P71_STAGING_EVIDENCE_20260908.json)
and [execution record](VSPC1_NATIVE_HOLD_VALUE_B06_P71_TECHNICAL_20260908.md).
This record applies frozen arithmetic; DM owns scientific intake and any next
bounded recommendation. B05 remains separately preserved without extra evaluation.

## Fixed binding and terminal facts

Scientific SHA `fd4c9f4a65c7c4049f9c0e5f18b28534f14abe01`, master 8302, extra initialization 830200012.
Literal-wrapper commit `3949ae971a344a83910e8fe495eb8cce917f5f72`. Handle `vspc1_hold_value_b06_8302_fd4c9f4a65c7`,
PID 3023178, node hmasd-wsl-node, CPU FP32, one process/numerical thread.
Detached cwd: `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b06-8302-fd4c9f4a65c7`.
Output: `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b06_8302_fd4c9f4a65c7`.
Started 2026-09-09 05:23:49 UTC; terminal 05:30:37 UTC, exit 0 and tmux inactive.
Raw local collection remains at `temp/directions/vsp_c1/collection/native_hold_value_b06_8302_fd4c9f4a65c7/`.
The supervisor's whole-second duration is 408s; enclosing /usr/bin/time is 407.33s.

## Native endpoints and fixed all-outcome reading

| Arm | Mean native J |
| --- | ---: |
| GATED-V | 0.16886691046202362 |
| MLP-V | 0.17550142866866406 |
| H | 0.1491892365481063 |

MLP-V is the unchanged width-133 ordinary comparator. Each contrast contains
32 identity-matched evaluation differences conditional on one new trained pair.

| Contrast | Mean | Conditional SE | Negative differences |
| --- | ---: | ---: | ---: |
| GATED-V_minus_MLP-V | -0.006634518206640422 | 0.006982194296842694 | 18 |
| GATED-V_minus_H | 0.0196776739139173 | 0.01388034917333274 | 11 |
| MLP-V_minus_H | 0.02631219212055772 | 0.011853226104441108 | 8 |

Card section 4's applicable rule is retained verbatim:

| Observation | Bounded reading |
| --- | --- |
| -.01≤Delta≤.01, including endpoints | WITHIN: no selected-scale advantage in this instance; retain sign/noise and8301 without equivalence or an automatic negative family judgment. |

The point estimate lies within [-.01,.01], with wider MLP ahead by sign.
Conditional SE and all adverse identities remain reportable; this is not
an equivalence or stable population finding. Both learned mean returns exceed H,
while 11 GATED and 8 MLP evaluation identities are below H. H remains untuned,
and matching tuned headroom remains absent. One new matched training pair is the
independent unit; 32 evaluations do not become 32 training seeds. Any joint
8301/8302 descriptive interpretation belongs to the DM intake, separate from old
width-128 and unnormalized regimes.

## Collection acceptance and exposure

Artifact-only checker PASS, exit 0, 2.334662099950947s complete process wall.
No model construction, forward, native episode, evaluation or training replay
was performed. Remote/local hashes match summary, episodes, rollouts, both final
checkpoints and admission. All 1120 episode rows, 512 rollouts and 2048 epoch
records reconcile with 286720 native steps (262144 train /24576 eval), 2048 Adam
calls, 1024 training episodes, 96 final evaluations, two constructor resets and
zero partial steps. Reward/J decompositions, held-decision counts, full reset/
master identities and all three contrast means/conditional SEs agree.

Both checkpoint identities agree with the accepted source/object/configuration
and actual FP32 finite tensors. GATED has 34817 critic parameters; MLP has 34827,
with second weight/bias (133,128)/(133,) and output weight (1,133). Final parameter
and gate norms agree with exposure. Total relative parameter movements are
0.2887399636093637 GATED and
0.2833553890787584 MLP. Gate absolute movement
is 0.6655405759811401; duration absolute movements are
0.22281232476234436 /0.1754722148180008.
Their initial norms are zero, so relative movement is undefined. The collection
check records null for that reading while preserving raw summary reporting.

Both arms record 131072 target rows and 256 merges, adding 512 rows each rollout.
Normalized-squared value losses and final moments agree across checkpoints,
summary and before/after learned evaluation; MLP moments remain fixed through H.

| Arm | Final mean | Final M2 | Final scale |
| --- | ---: | ---: | ---: |
| GATED-V | 15.098034858703613 | 23365812.0 | 13.351666450500488 |
| MLP-V | 14.530430793762207 | 24520682.0 | 13.677644729614258 |

Nonzero held rows are 1503 training /93 evaluation for each arm. Full raw
return-to-go arrays were not separately archived/replayed; unchanged accepted
source checks and actual moment/publication state cover that boundary.

## Complete resources, limitations and next owner

Canonical actual-node admission passed physical and effective floors with
14689787904 available bytes. Complete enclosing wall
407.33s includes H/publication/readback/exit. Internal pair wall
395.74447249498917s and MLP transition 196.92065112799173s leave
11.585527505010816s unpartitioned residual. Conservatively charging
that residual to each arm yields GATED 208.50617863300255s
and MLP 210.40934887200825s, below 1800s each. Whole pair is
below 3600s. Serial critical path and summed invocation wall are both 407.33s.
Peak RSS is 558000 KiB (544.921875 MiB). Aggregate CPU and isolated
width/normalization overhead remain unmeasured; no cause of timing differences
is assigned and no performance-equivalence conclusion follows.

No scientific or execution-binding deviation was observed. B06's 11 source
checks and prior pipeline review were reused; P69's historical unmeasured first
enclosing-test-wall qualification remains unchanged. All new published text is
strict UTF-8. P71's one accepted submission is spent and observation is complete.
DM is next owner for all-outcome intake and the final Root relay.
