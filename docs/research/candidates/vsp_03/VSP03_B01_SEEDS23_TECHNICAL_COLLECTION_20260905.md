# VSP03 B01 seeds 2 and 3 technical collection

**Both selected complete invocations are technically accepted.** No required-path defect was found; both terminal witnesses report exit0. The finite extension ends here, with no seed4 or scientific disposition by CM.

Source SHA `b77f897da7dea5df2e9230f43c8f128cc281afb3` was committed/pushed before execution. Its exact source delta from accepted seed1 is only CLI `choices=[1]` to `choices=[1, 2, 3]`, authorized in DM amendment `72b0bcf7f`. AST-extracted actual argparse statements accepted1/2/3 without importing the learner or constructing scientific state. No separate smoke, source-review cycle, profiler, replay or test-model construction was added. Scope:none.

The prospective invocation freeze is `VSP03_B01_SEEDS23_TECHNICAL_LAUNCH_20260905.md`. Original science card, numerical contract, runtime check, quantity, main update128, early updates32/64 and F remain unchanged. Seed3 followed seed2 terminal required-path checks, as selected before either outcome.

## Execution and resource facts

Both used configured node `wsl_4070`, SSH `hmasd-wsl-node`, detached cwd `/home/wu/hmasd-worktrees/vsp03-b01-seeds23-r01` at the exact source SHA, configured Python `/home/wu/.venvs/hmasd/bin/python`, CPU float32. Each existing agent-task command joins fresh actual-node memory admission with `&& timeout 1800s ... scripts/run_vsp03_b01.py --seed <s> --out temp/directions/vsp_03/exp/vsp03_b01_seed<s>_r01`.

| Seed | Supervisor task / PID | Receipt UTC | Physical/effective available bytes | Runner whole wall s | Peak RSS bytes | Supervisor seconds |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 2 | vsp03-b01-seed2-r01-20260905 / 1931875 | 2026-09-06T00:21:40.095988Z | 15677493248 / 15677493248 | 5.905074234994 | 485208064 | 6 |
| 3 | vsp03-b01-seed3-r01-20260905 / 1932339 | 2026-09-06T00:23:11.264171Z | 15676420096 / 15676420096 | 4.023389708993 | 485015552 | 4 |

Summed runner walls are **9.928463943987s**. Supervisor-clock elapsed from first launch to final exit is 95s, including the local collection/control-plane gap between seeds; it is not summed compute. Each independently satisfied its1800s whole-pair cap. Receipts passed the4GiB floor; cgroup readings remain null as in existing admission. Source enforces one BLAS/OpenMP/Torch compute thread, but no live thread census or aggregate CPU-seconds measurement was taken. RSS is each main-process OS high-water mark.

Existing tracker `/root/tracker_tl_experiments` acknowledged both accepted handles, reported both terminals directly, and received CM ACKs. No restart, migration or alternate process occurred. Remote checkout succeeded through configured network shell; its existing gitstatus/auto-GC warnings did not change the verified source or successful fetch/checkout.

## Measured phases

| Seed / arm | I | mean C(128,40) | mean E(128,40) | O | Full I+128C+10E+O seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2/T | 1.183835271 | 0.010118434 | 0.006336037 | 0.097215801 | 2.639570996 |
| 2/G | 0.005837964 | 0.010852712 | 0.018902672 | 0.106376993 | 1.690388752 |
| 3/T | 0.842496038 | 0.006275388 | 0.004217399 | 0.065975193 | 1.753894935 |
| 3/G | 0.001140980 | 0.006130505 | 0.011665043 | 0.063796293 | 0.966292294 |

Seed2 imports/setup=1.386312073s, integrated check=0.128059255s; eight F batch times and all ordinary batch samples remain in summary.

Seed3 imports/setup=1.161908972s, integrated check=0.102239189s; eight F batch times and all ordinary batch samples remain in summary.

O is measured arm wall less I/C/E, including curve/endpoint/state publication and bookkeeping. Original per-arm conditional projections1.037851087s/0.568588821s and whole-pair2.364870157s were planning estimates, not guaranteed speed or caps. No additional timing invocation followed the observed differences.

## Exposure

Every learner completed16384training episodes/655360ticks,128joint Adam steps and128backward calls;1280evaluation episodes/51200ticks at the exact prescribed points. Each learner has1314actor+257critic=1571parameters. Every invocation constructed exactly2learners and completed36360episodes/1454400ticks/256joint steps. Across the selected two invocations:72720episodes,2908800ticks,512joint steps.

| Seed / arm | Training valid decisions = gradient rows | Training actor forwards incl loss | Eval decision rows / actor forwards | Initial total L2 / RMS | First displacement / ratio | Final displacement / ratio |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 2/T | 53848 | 1271 | 4821 / 90 | 6.561303139 / 0.165539652 | 0.017058564 / 0.002599874 | 2.623161316 / 0.399792733 |
| 2/G | 40998 | 1226 | 6034 / 90 | 6.084073544 / 0.153499305 | 0.017058600 / 0.002803812 | 3.057497740 / 0.502541220 |
| 3/T | 54471 | 1278 | 4777 / 90 | 6.482429028 / 0.163549662 | 0.017058592 / 0.002631512 | 2.684945583 / 0.414188196 |
| 3/G | 40416 | 1230 | 5413 / 90 | 5.998928070 / 0.151351094 | 0.017058546 / 0.002843599 | 2.822717905 / 0.470537048 |

Actor/critic-specific exposure remains in each summary. Each integrated check accounts separately for8episodes/320ticks/32decision and gradient rows, one actor/critic forward/backward, zero optimizer steps, and clears gradients. Each F has1024episodes/40960ticks and zero model/optimizer work.

| Seed | Whole decision rows | Rollout actor forwards | F decisions |
| --- | ---: | ---: | ---: |
| 2 | 109542 | 2421 | 3809 |
| 3 | 108883 | 2432 | 3774 |

## All fixed endpoint observations

| Seed | Update | T mean | G mean | T-G | Conditional episode SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 | 32 | 0.264531250000 | -0.200000000000 | 0.464531250000 | 0.043200551385 |
| 2 | 64 | 0.354531250000 | 0.097578125000 | 0.256953125000 | 0.042550132341 |
| 2 | 128 | 0.363779296875 | 0.363779296875 | 0.000000000000 | 0.000000000000 |
| 3 | 32 | 0.288984375000 | -0.200000000000 | 0.488984375000 | 0.044490338884 |
| 3 | 64 | 0.371093750000 | 0.371093750000 | 0.000000000000 | 0.000000000000 |
| 3 | 128 | 0.385927734375 | 0.385927734375 | 0.000000000000 | 0.000000000000 |

Update32/64 each uses128episodes per arm; main128 uses1024. Main T/G/F per-episode records are equal for all1024episodes within each seed, including native components and submission times. This is sampled-record equality, not global policy equivalence or scientific interpretation. All earlier values remain at their actual endpoints.

| Seed main T=G=F | Return | Success | Attempts | Failed attempts | No submission | Waiting ticks | Pre-submit reentry count / mean return |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 | 0.363779296875 | 0.467773437500 | 0.959960937500 | 0.492187500000 | 0.040039062500 | 11.199218750000 | 540 / 0.358740740741 |
| 3 | 0.385927734375 | 0.489257812500 | 0.961914062500 | 0.472656250000 | 0.038085937500 | 11.046875000000 | 542 / 0.415129151292 |

## Artifact collection and acceptance limits

Remote outputs remain under the exact cwd above, `temp/directions/vsp_03/exp/vsp03_b01_seed2_r01/` and `vsp03_b01_seed3_r01/`; fresh receipts are sibling `<root>_memory.json`. Durable supervisor logs/status/exit are `/home/wu/.agent-tasks/vsp03-b01-seed<s>-r01-20260905/`.

All original artifacts were copied to `C:/Projects/HMASD-worktrees/cm-vsp03-b01-20260905/temp/directions/vsp_03/exp/vsp03_b01_seed<s>_r01/`, with receipt siblings. Each root contains summary, focused_check, T/G endpoints32/64/128, F_endpoint_128, T/G_curve.jsonl, T/G_final.pt, copied task.log/status/exit, and collection_checks.json. These local outputs are ignored scratch; the committed record fixes their recoverable locations.

Both existing integrated checks passed. CM independently read every endpoint row, recomputed integer accounting/division/waiting/failed-attempt relations and endpoint/paired means; verified episode identities and128curve rows per learner with128episodes each; summed gradient rows; read both final state dictionaries as1571finite float32 parameters; and checked memory receipts, complete counts, terminal within-cap status and exit0. The timed runner had already compared each saved state to its live state. Collection makes no new model or rollout and consumes no optimizer step. No required measurement is missing.

The unchanged scientific source inherits its prior independent review and focused-test evidence. This one-line CLI extension needed only the exact-delta/argument check. Acceptance establishes the selected completed invocations and trustworthy sampled measurements; it does not certify generic optimality, stable superiority, across-seed uncertainty, learning necessity, historical source validity or MARL value. Both returns now go to DM for combined scientific intake. No further seed is selected.
