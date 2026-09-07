# DISH B06 E0 result and CM technical acceptance â€” 2026-09-07

The sole seed113 invocation **completed and is technically accepted** at the frozen B06
single-training-instance scope. Primary `Delta_exec=-77.5` service ticks. No second invocation,
scientific retry, source edit or altered scientific input occurred. DM owns scientific intake.

## Execution and retained evidence

Root dispatched `P07-DISH-EXEC-01` against the [launch assignment](DISH_SAMPLED_EXECUTION_B06_LAUNCH_ASSIGNMENT_20260907.md)
Â§Â§1â€“4 at main `4219639ae`. Bound source was `373d187200a91942385e9380770dcf9f8098aada`,
node `wsl_4070` via `hmasd-wsl-node`, cwd
`/home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01`.
The accepted supervisor handle is `dish_b06_seed113_20260907_run01`, PID2628131.
Supervisor records start **2026-09-07T12:55:15Z**, terminal **12:58:50Z**, exit0 and duration215s.
Root acknowledged routine observation adoption with the shared heartbeat ACTIVE. CM collected
only after authoritative terminal status. The later status `uptime_seconds` is query age and
was not used as execution duration.

The first Git HTTPS fetch failed before worktree creation with `SSL connection timeout`.
A partial-clone object query also initiated a lazy fetch; its named processes were closed before
Root's Portfolio-directed `P07-DISH-STAGE-REPAIR-01` bundle transport. An ordinary Git bundle of
committed objects, prerequisite `588214ed62af2262fc904f1069eb37a336e9ff96`, was verified/fetched
on the original node, then the original detached worktree was created at the exact bound SHA.
[Staging facts](sampled_execution_b06_20260907_run01/staging_facts.json) preserve the failures,
closure and successful repair. No uncommitted source was transferred. The original
[payload](sampled_execution_b06_20260907_run01/supervisor_payload.sh) was sent once, unchanged.

[Raw summary](sampled_execution_b06_20260907_run01/summary.json),
[paired primary](sampled_execution_b06_20260907_run01/paired.json),
[full stdout](sampled_execution_b06_20260907_run01/stdout.log), empty stderr, admission,
OS timing and complete supervisor records are retained in that evidence directory.
The full scientific envelope, including initialization, recorded resets and update16 checkpoint,
is retained locally at
`temp/directions/degraded_incumbent_shadow_handover/exp/sampled_execution_b06_seed113_20260907_run01`
in the CM worktree, and at the matching relative path under the remote cwd. The files include
`result/shared/initial_state.pt` (836667 bytes), `result/shared/resets.json` (3004 bytes), and
`result/learner/checkpoint_update16.pt` (2356639 bytes). All learner and episode records are in
the raw summary/stdout; raw representations were not rewritten.

## Focused technical acceptance

[Machine acceptance](sampled_execution_b06_20260907_run01/technical_acceptance.json) records the
readback and arithmetic. Summary and paired primary match; the last complete stdout JSON differs
from summary only by the final `completed_wall_seconds` and `charged_wall_seconds` fields.
Both actual master digests match the frozen laws. The recorded configuration is one CPU compute
thread, native float64, policy FP32 and two original optimizer groups at3e-5 for all16 updates.
All16 loss/gradient finiteness receipts pass; parameter L2 movement is1.711241358519297.
The complete learner reports65536 ordinary transitions and512 optimizer steps.

There are exactly4 own-initial modal,4 final modal and8 final sampled rows, with the required
coordinate/sample pairs and matching recorded resets. All16 are complete, each stepped1200 ticks:
19200 actual evaluation ticks, zero unstepped remainder. Initial/final companions, all seven
native hard-event fields, terminal facts, and first-transfer tick/null are readable. All rows
have zero legal transfers, null first-transfer tick and zero post-transfer service.
No scientific test, learner or episode was rerun during collection. Existing independent source
review and focused synthetic coverage remain the implementation evidence.

| Condition | Initial modal | Final modal | Sample0 | Sample1 | Sample mean | Sample mean minus modal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 |250|459|362|371|366.5|-92.5|
| TARGET_VISUAL_MASK / K4_TO_K12 |359|593|497|607|552|-41|
| TERRAIN_RELAY_MASK / K8 |417|454|364|356|360|-94|
| TERRAIN_RELAY_MASK / K4_TO_K12 |453|1143|1146|975|1060.5|-82.5|
| Equal-condition mean |369.75|662.25|â€”|â€”|584.75|-77.5|

`D_modal=292.5`; `G_sampled_vs_init=215.0=D_modal+Delta_exec`. The latter combines learning and
an execution-interface change. These are direct measurements, not a training-population claim.

Native panel means retain equal condition weighting after averaging the two samples. Initial,
final modal and final sampled energy means are268778.5278,273979.2808,278621.9235. Invalid-commit
means are7.75,3.5,31.875 respectively; all other evaluation hard-event counts are zero. Raw counts
and denominators are retained. Training reports1030 invalid commits,3 separation breaches,
35 terminal events and zero legal transfers; these are training facts, not final-evaluation rates.

## Work, resources and limits

Actual sampled renewal count R=1240 gives4960 normal,2480 Bernoulli and12400 uniform draws,
matching4R/2R/10R. Eligible training E=7631. Native consequence H remains unmeasured with
bound0â€“152620, giving recorded native training-call bounds146334â€“298954; no cause or exact H
is inferred from service outcomes. No extra native diagnostic was purchased.

The same-node admission passed at12:55:15.489434Z with physical/effective available memory
15665545216 bytes, above4294967296. This is admission evidence, not a peak-resource claim.
OS whole-chain wall is **215.02s**; adding prior checks10s once gives **225.02s**.
Post-collection JSON readback took less than0.01s internally; conservatively charging another1s
(including interpreter startup) gives **226.02s**, still below1800s. OS user+system CPU is
**221.09s** for this chain; earlier-check CPU is unmeasured. Supervisor study elapsed is215s at integer precision. The runner's narrower wall
is204.713815717s and its resolved prior charge11s gives215.713815717s; do not substitute this
for OS whole-chain timing or add its11s again. Setup, process closure and measurement scope
explain why these timers cannot be treated as interchangeable; no unmeasured causal breakdown
is asserted. Git staging/transport and evidence integration are control-plane work.

OS maximum RSS is656375808 bytes. Runner self/reaped-child maxima are each635867136 bytes;
they are separate scoped maxima, not a summed simultaneous process-tree peak. Scratch peak is
unmeasured and `resources_unmeasured` remains true. Optional resource gaps do not remove the
complete primary. The complete measured wall passes the original cap; no timer setting alone
was used as proof of conformance.

Card Â§5 arithmetic predicates `Delta_exec<=-24` and zero final legal transfers are directly
satisfied. Their scientific interpretation, prediction scoring and next-object selection belong
to DM; no causal noise explanation, source-origin eligibility or source value was measured.
This CM delivery changes no source or engineering-scope Â§4 machinery. Root integrates the evidence
commit; DM performs scientific intake. No retry or further invocation is authorized by this result.
