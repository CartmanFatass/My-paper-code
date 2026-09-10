# VSP03 B04 consumed invocation: pre-admission engineering failure

The sole accepted P65→P64 handle failed with actual exit2 before admission or
scientific execution. Python could not open scripts/hmasd_resource_preflight.py in
the exact detached cwd. The adjacent && therefore never invoked the seed6 runner.
This consumes the single invocation; no repair, staging correction, retry, extra seed,
probe or successor is selected. DM owns the all-outcome intake, then safe pause.

## Binding and raw evidence

Source b5d605bf4f39b5ab18f01c98e04dc07e53764354; accepted binding671619257;
[card](VSP03_B04_SCIENCE_CARD_20260908.md) section8 and
[launch boundary](VSP03_B04_LAUNCH_BOUNDARY_20260908.md).
Root executed the sole handle vsp03-b04-p64-20260908 on wsl_4070. The actual cwd was
`/home/wu/hmasd-worktrees/vsp03-b04-p64-b5d605bf4f39b5ab18f01c98e04dc07e53764354`.
The unchanged supervisor accepted the private tmux session. The
[actual generated wrapper](VSP03_B04_RESULT_ARTIFACTS_20260908/supervisor_runner.sh)
and [manager journal](VSP03_B04_RESULT_ARTIFACTS_20260908/journal.txt) preserve argv.
The [raw collection](VSP03_B04_RESULT_ARTIFACTS_20260908/collection.json) retains
source paths, contents, manager state, output existence and descendant observations.

The [supervisor log](VSP03_B04_RESULT_ARTIFACTS_20260908/supervisor_task.log) records
Errno2 for the missing admission script. This is a concrete missing-file execution
failure; collection does not diagnose why that file was absent or repair staging.
The [payload receipt](VSP03_B04_RESULT_ARTIFACTS_20260908/b04_seed6_p64_20260908_terminal.payload.json)
and [whole-task receipt](VSP03_B04_RESULT_ARTIFACTS_20260908/b04_seed6_p64_20260908_terminal.json)
both report2, timed_out=false, and no adapter exception. Actual supervisor exit_code
is2 and status is failed; manager ExecMainCode=1, ExecMainStatus=2, Result=exit-code.
These are observed process exits, not an inference from systemd-run's client return.

## Exposure, terminal boundary and resources

Accepted invocations:1. Executed admission-script bodies:0; successful admissions:0;
scientific runner/model/episodes/updates/optimizer steps:0. No admission JSON or
scientific output root exists. These zero-exposure facts follow from the explicit
file-open failure and && ordering, not merely absent output. Primary, counts/weights
from learning, treatment contrasts and scientific performance are unavailable; no
missing endpoint is represented as a measured zero.

All required task receipts were published within the original120s boundary. The
single manager origin is375534.924519 monotonic seconds. Payload readback occurred
at0.075041s; final controller readback at0.098729s. Manager origin through main exit
is0.102436s and through terminal failed state is0.102563s. The configured119s hard
cgroup deadline was not reached. For this one invocation, study critical path and
summed invocation wall are both0.102563s on this manager boundary; this is failure
handling cost and says nothing about learner runtime or the former3.50s projection.

The payload reports no remaining scientific descendants. The controller killed/reaped
its private control descendants3015793,3015794,3015803 and reports none remaining.
Collection confirmed those recorded PIDs absent and the unit cgroup empty. The failed
unit is retained as observed; CM did not reset it or alter supervisor bookkeeping.
Manager CPUUsageNSec=77808000 (0.077808 aggregate CPU seconds) and MemoryPeak=8785920
bytes describe this failed task cgroup only. MemoryCurrent/TasksCurrent are unset.
No admission ran, so physical/effective memory-floor conformance is unestablished;
these small observed resource values do not substitute for an admission receipt.

## Technical disposition and stop

The task exit/termination/publication boundary behaved as recorded, while the
scientific invocation failed before admission. This is not a valid scientific result,
and engineering containment success does not establish scientific conformance.
Only existing-handle collection and local evidence publication were performed after
Root's failure return. No source edit, staging action, extra check or relaunch occurred;
old scratch cleanup was not retried. Raw scientific/supervisor evidence stays in place.
Return this consumed invocation to DM for all-outcome intake/archive, then safe pause.
