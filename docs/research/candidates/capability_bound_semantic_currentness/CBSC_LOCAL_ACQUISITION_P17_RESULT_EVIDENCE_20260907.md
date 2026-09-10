# CBSC P17 execution evidence

Technical outcome: **PATH_PREPARED**. The sole allocated invocation completed
with both terminal exits zero, matching published/read-back metadata and complete
wall time below 600 s. This is environment preparation evidence; DM owns intake
and any later scientific or execution selection.

## Binding and reading

Allocation: P17 CBSC section at `a787ff12cd0212b9fd23d9d861d5d192186028fe`,
recorded in the P16 card at authoring revision `e612ccbd1`.
Command source `5828af584c5f5e6764f5a44c9951473d82bf04ad`; exact literal from
`CBSC_LOCAL_ACQUISITION_P16_ROOT_HANDOFF_20260907.md` at
`35a4fcaeabb8f8590ac0ac4a410327414bc4ef63`. Separate unchanged preflight source:
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`.

Card reading, verbatim:

> Prospective reading: `PATH_PREPARED` requires observed successful local terminal
> exit and remote terminal exit, complete primary metadata publication/readback with
> `metadata_matches=true`, and the actual complete invocation within 600 s. A ready
> flag, file, test result or SSH success alone is insufficient. `PATH_INCOMPLETE`
> records failure, timeout, missing/mismatching primary metadata, uncertain terminal
> completion or cap breach, while retaining independently observed narrower facts.

## Accepted identity and initial facts

Local cwd `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch `codex/cbsc`.
Remote detached source checkout
`/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907` was observed clean
at the exact command SHA before acceptance. Local command and preflight source
surfaces matched their bindings; later documentation HEAD was not substituted.

Hidden wrapper PID 10696 started `2026-09-08T02:46:39.3752536Z`; actual Python
controller PID 28812 started `2026-09-08T02:46:40.334933Z`. Root adopted the
accepted identity. The wrapper executes the bound literal once and retains its
independent stopwatch/exit witness. Logs are in the existing exp parent; the
command created its own fresh `local_acquisition_p16_20260907` output directory.

Local admission captured `2026-09-08T02:46:40.751575Z`: physical and effective
available memory both 7191392256 bytes, above the 4294967296-byte floors;
`passed=true`, source `GlobalMemoryStatusEx`. This is admission, not a measurement
of runtime resource use. Initial observation reached the first Torch GET after
that admission and the one clock sample. The recorded remote BOOTTIME deadline
is 301764.6118587743 seconds; it never starts another 540 s allocation.

## Terminal outcome

Root observed local completion; CM collected the local receipts and, in one
read-only remote collection, the existing supervisor status, terminal record,
primary metadata, admission, install log and wheel inventory. No package import,
installation, runtime probe or candidate retry was added during collection.

| Witness | Observed value |
| --- | --- |
| Local controller result | exit 0; phase complete; ready true; metadata collected true |
| Independent wrapper | exit 0; error null; ended 2026-09-08T02:49:34.8247584Z |
| Complete controller wall, original origin through final publication | 174.35900000005495 s |
| Independent stopwatch around the exact literal, including startup/teardown | 174.5612299 s |
| Remote terminal | exit 0; error null; same fixed BOOTTIME deadline |
| Remote supervisor | finished; exit 0; PID 2755729; tmux inactive |
| Primary metadata | remote summary equals collected local JSON; metadata_matches true |

The worker's 174.328 s is a narrower interval and is not substituted for complete
wall. The supervisor's reported 8 s duration covers only the remote setup subset;
its collection-time uptime is not invocation wall. The complete chain finished
before both the 540 s work deadline and 600 s cap. Aggregate CPU, summed per-host
process wall and runtime peak memory were not measured. Deadline kill paths were
not exercised by this successful run; P16's documented relative clock-rate and
no-host-suspend assumptions remain explicit.

## Acquired inputs and environment

The local and remote retained Torch wheel lengths are both 955455844 bytes;
Triton lengths are both 156503769 bytes. Remote inventory contains 23 wheels:
these two complete files and the 21 named retained A03 container symlinks. The
bound production path and successful artifacts establish two sequential whole
GETs, one two-file transfer, one fresh venv, one offline full-resolution install
of all 23 pins, and one metadata process importing NumPy and Torch once each.
These operation counts are execution-path facts, not a packet capture.

The candidate is
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907`.
Metadata observes lexical `bin/python` under that prefix, resolved/base executable
`/usr/bin/python3.12`, CPython 3.12.3 (main, Jul 15 2026; GCC 13.3.0), NumPy 1.26.3,
Torch 2.7.0+cu118 and Torch CUDA build 11.8. All 23 installed versions match the
bound inputs; distribution and module locations are recorded in the primary JSON.
This checks package import/metadata, not GPU execution or the B04 learner path.
Host episodes, model calls, optimizer steps and policy evaluations remain zero.

Remote admission captured 2026-09-08T02:49:26.381669Z and assessed
2026-09-08T02:49:26.381973Z: physical/effective available memory 15647854592 bytes,
`passed=true`, from `/proc/meminfo`. Both node admissions exceeded 4 GiB; neither
establishes runtime resource peaks. Install log reports resolution of 23 packages
in 21 ms, preparation in 5.03 s and installation in 159 ms. These are phase
subtimes, not a replacement for the complete measured wall.

## Source provisioning and retained evidence

Before candidate acceptance, source fetch encountered an existing remote-tracking
ref prefix collision; its historical ref was preserved. A lazy-blob worktree
checkout without the existing proxy environment stalled. The identified Git
transport chain was stopped and observed gone; Git cleaned its incomplete checkout.
Applying the existing proxy environment to the same source provisioning operation
then produced the clean exact-SHA checkout. This was source provisioning outside
the candidate invocation, not a result-bearing retry. No source repair or historical
ref deletion occurred.

All local raw evidence is retained under
`temp/directions/capability_bound_semantic_currentness/exp/` in the authoring checkout:

- `local_acquisition_p17_launch.ps1`, `local_acquisition_p17_launch_receipt.json`,
  `local_acquisition_p17_controller_identity.json`, `local_acquisition_p17_terminal.json`
  and wrapper stdout/stderr logs preserve the exact launch and independent witness.
- `local_acquisition_p16_20260907/` retains `command_result.json`, worker result,
  local admission, collected primary metadata, complete wheels and phase logs.
- `local_acquisition_p17_remote_collection.json` retains the remote primary bytes,
  terminal/admission/install records, supervisor records and full wheel inventory;
  its companion stderr is empty.
- `local_acquisition_p17_source_provision*.txt` and provision inventory/stopped
  receipts preserve source staging and the terminated staging transport chain.

Remote outputs remain at the exact source checkout's
`temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907`;
supervisor records remain under
`/home/wu/.agent-tasks/cbsc-local-acquisition-p16-20260907`.

The one P17 invocation allocation is consumed. No retry, B04 rerun or further
candidate work follows from this technical record. Root integrates this evidence;
DM owns card/intake, prediction assessment and the next authorized return route.
