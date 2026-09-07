# UCOPE B05 result evidence — seed 6701 reconciliation

Technical collector: replacement CM `/root/cm_ucope_p11_b05_collect`. Assignment P11/P12 continuation; original B05 card §§2–5 and execution handoff control. **Seed 6701 COMPLETE; prospective pair INCOMPLETE pending seed 6702.** No scientific intake or next-object selection is made here.

## Terminal identity and complete collection

Root launched accepted distinct handle `ucope-shared-return-b05-seed6701-p12-lf-20260907` after integrating the [transport correction](UCOPE_SHARED_DATA_RETURN_MODEL_B05_TRANSPORT_CORRECTION_20260907.md). The prior failed handle remains preserved there and contributes zero learner exposure. Root verified the committed 687-byte LF seed-6701 artifact digest before staging and execution. The new [supervisor log](b05_result_evidence_20260907/seed6701/task.log) records start `2026-09-08T05:33:19+08:00`, terminal exit **0** at `05:33:23+08:00`, status `finished`. Copied `runner.sh`, `status` and `exit_code` retain the actual supervisor evidence.

Node `wsl_4070`; source/cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907`, exact SHA `71433bfabb70481def4329e622a838fa0cd9eeec`. All files in the remote result root `temp/directions/ucope/exp/shared-data-return-b05-seed6701/` were collected: [summary.json](b05_result_evidence_20260907/seed6701/summary.json) and [resource_admission.json](b05_result_evidence_20260907/seed6701/resource_admission.json). Complete values/counts, eight-context policy results, paired moments, root/tail plans, acquisition, costs and all outcomes remain in that summary. Original remote artifacts remain intact.

Fresh admission assessed `2026-09-07T21:33:19.099257Z`; physical and effective available memory each **15659425792 bytes**, passing the 4294967296-byte floor. The saved command runs preflight immediately before the API call by `&&`. CPU binary64 (53-bit mantissa), one compute thread, Python 3.10.21, seed 6701, B05 identity and 512 batches are recorded.

## Direct measurements

External complete-command wall **4.67 s**, peak RSS **20620 KiB**; runner wall **4.61908938997658 s**. This invocation fits 600 s. Completed invocation wall so far is 4.67 s of the 1200 s pair cap; the prior parse failure reports 0 s supervisor duration. Pair critical path and full sum are pending seed 6702. Aggregate CPU and scratch peak remain unmeasured; retain the runner's `resources_unmeasured`. These gaps do not annul this non-resource endpoint. Existing card cost projection (4.71 s/dataset, 9.42 s pair) and prior publication-path coverage were reused; no timing pilot, replay or extra evaluation was added.

| Contrast | Mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | 0.0028081868489583379 | 0.0005595030492464352 |
| delta_information | 0.0028081868489583379 | 0.0005595030492464352 |
| blind_minus_immediate | 0 | 0 |

The recorded per-dataset branch is **RM-A** under the unchanged rule: native >0.001 and information >0.001 with actual FULL acquisition. This is only the first dataset, not the joint B05 branch. DM owns the pair mean, sample SD, conditional mean MC SE, predictions and scientific interpretation after both selected datasets.

Training: 131072 real episodes, 655360 transitions, 65536 paid episodes, 131072 behavior draws and 512 completed batches. The 264 learned values have 196608 scalar updates; histogram increments 65536. Initial L2 is zero and first observation step size is 1. Final evaluation is 8 contexts × 3 policies × 4096 episodes = 98304 episodes; complete invocation exposure is 229376 episodes. No optimizer steps or additional model/checkpoint selection occurred. Summary retains per-component displacement L2/max movement and all count inventories.

| Policy | Evaluation episodes | Transitions | Probe episodes | Mean return | Mean paid component |
| --- | ---: | ---: | ---: | ---: | ---: |
| FULL | 32768 | 90112 | 4096 | 0.79336580403645829 | -0.0062638346354166657 |
| BLIND | 32768 | 65536 | 0 | 0.79055761718749995 | 0 |
| IMMEDIATE-4 | 32768 | 65536 | 0 | 0.79055761718749995 | 0 |

| Context | FULL minus IMMEDIATE-4 | FULL root | FULL tails (counts 0–6) |
| --- | ---: | --- | --- |
| LINKED-p13_20-c9_100 | 0 | IMMEDIATE | [6, 6, 6, 4, 4, 2, 2] |
| LINKED-p13_20-c7_50 | 0 | IMMEDIATE | [6, 6, 6, 4, 2, 2, 2] |
| LINKED-p17_20-c9_100 | 0.022465494791666703 | PROBE | [8, 6, 6, 6, 2, 2, 2] |
| LINKED-p17_20-c7_50 | 0 | IMMEDIATE | [6, 8, 8, 4, 2, 2, 2] |
| SEVERED-p13_20-c9_100 | 0 | IMMEDIATE | [4, 4, 4, 4, 4, 4, 4] |
| SEVERED-p13_20-c7_50 | 0 | IMMEDIATE | [4, 4, 4, 4, 4, 6, 4] |
| SEVERED-p17_20-c9_100 | 0 | IMMEDIATE | [4, 4, 4, 4, 4, 4, 4] |
| SEVERED-p17_20-c7_50 | 0 | IMMEDIATE | [4, 4, 4, 4, 6, 4, 4] |

BLIND and IMMEDIATE-4 coincide in every context, with zero paid acquisition; all FULL/BLIND/IMMEDIATE-4 context means and plans are preserved in the copied JSON, including every zero contrast. No context or outcome was dropped.

## Technical acceptance and seed-6702 transport artifact

Focused local checks parsed saved evidence only. They established exact seed/object/source/runtime identity; terminal status and passing fresh admission; 512 batches and all training/draw/update/histogram totals; finite 264-value inventory and matching update counts; eight distinct complete contexts, all three policies and 4096 paired indices each; nonzero evaluation transition counts; aggregate paired means and conditional MC SE equal to recomputation from saved context moments; and RM-A with positive actual acquisition. No experiment module was imported, no source was edited, and no simulation/replay was performed. These are conformance facts, not stable-population or causal claims. No technical gap blocks the selected second dataset after Root's prescribed reconciliation.

[Corrected seed6702 command](b05_transport_correction_20260907/seed6702-command.sh): **687 bytes, UTF-8 without BOM, LF**, SHA-256 `65219c4912604374c6bf1b3f543535c94890653b76398f01f32da8f51afc8b81`. It is exactly the original handoff's decoded seed-6702 supervisor payload plus terminal LF. Outer and inner local `bash -n` checks returned 0; no payload execution occurred. The only scientific difference from the seed-6701 command is its originally selected seed/root, with the same API/512 batches/source/order/binary64/metrics/three-policy evaluation and 600 s cap. Root owns staging and any separately authorized distinct handle; this CM did not dispatch 6702. Preserve LF bytes during Windows staging (the committed blob and current file are LF).

ENGINEERING_SCOPE_SPEC §4 additions: none. Root integrates this evidence and returns it to DM `/root/dm_ucope_p10_pair_prep`; DM scientific intake/brief remain separate. Seed 6702 and the joint B05 claim are still pending; this document does not complete the pair or authorize another seed.
