# CRTO RAW phase-trace A01 resumed-attempt engineering evidence

Date: 2026-09-04. Object: `CRTO-RAW-PHASE-TRACE-A-RECON-R01`, class A/RECON.

**Engineering conclusion:** exact committed source materialization and command transport were
recovered. One fresh remotely admitted result process started, then terminated with SIGSEGV /
exit 139 after 18 supervisor seconds. Its result directory is empty. No measured trace or
scientific branch exists. The native-runtime cause remains provisional; the failing learner
step has not been reproduced. No code changed, retry ran, or local fallback occurred.

## Contract and source

The DM assigned recovery from the failed old preparation and one fresh observation using the
unchanged science card. Local control work used isolated branch
`codex/cm-crto-resume-20260904` and worktree
`C:/Projects/HMASD-worktrees/cm-crto-resume-20260904`, created from
`8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`. That exact SHA was pushed to
`origin/codex/cm-crto-resume-20260904` before remote preparation. Other checkout changes were
preserved. The later CM evidence commit is documentation only; it is not the launch SHA.

Acceptance remained the fixed 48 TRAIN / 16 EVAL B01 population, source namespace 2026083192,
seed 0, CPU FP32, one computational thread, one predictor fit of 100 updates at batch 128,
one RAW trajectory of 264 updates at batch 32, and 13 in-memory snapshots at updates 252..264
with 16 evaluations each. Initialization and update-256 anchors retain the card's exact values
and tolerances. Snapshot timing, cyclic row ordering, RNG streams, Adam law, legal-action order,
G16 scoring and charge-once semantics remain protected.

The inspected production path reconstructs predictor tapes, fits the predictor, regenerates the
fixed panel, forms RAW packets, trains one gate, deep-copies its declared snapshots, evaluates
after all snapshots exist, and publishes one summary. Predictor/gate/optimizer state belongs to
the invocation; snapshots live in memory. No checkpoint serialization is part of this path.
No TRUE/DERANGED exposure, residual calibration input, confirmation read, architecture change,
threshold change, best-checkpoint claim or residual interpretation was authorized or added.

`git diff --name-only c8247c2d19ac7965208c397a2a87519a1efb6310
8d1c597871b38edc7d5f139f34f5a3ce2941c7d0` showed no changes in the CRTO package, common-history
package, CRTO runner, admission tool, or shared hmasd/ha_ctse_process/envs/environments surfaces.
Other directions changed between the commits; these were not substituted into the CRTO path.

Owned deliverable: this technical evidence file. No research/core/test files were edited.
Engineering-scope section 4 additions: **none**. The accepted implementation remains 751
non-test lines, a 50-line runner and 176 test lines; its prior accepted orchestration share is
208/751 (27.7%). Manual transport used existing Git and SSH tools, not new research machinery.

Per-arm cost projection recorded before launch: one RAW arm, `3 * 434.7066687 = 1304.1200061`
seconds, below the per-arm/invocation cap of 1800 seconds. The project-cost probe emitted this
law, all prospective exposure lines and exact prospective counts.

Post-learner path coverage: the existing end-to-end toy test publishes a summary but uses toy
constants, three updates and six evaluation rows. It does not exercise the formal publication
path with all real constants; this remains an **open engineering item**. Neither prior failed
preparation nor this attempt establishes a failure past the learner, so no offline formal-output
replay was possible or performed.

## Old-task inspection and materialization

The old authoritative task `crto_raw_phase_a01_c8247c2d_01` was finished/exit 0 with duration 0s.
Its script executes only:

```sh
eval 'bash -lc cd /home/wu/hmasd-worktrees/crto-raw-phase-a01-c8247c2d'
```

The expected old result root was absent and no CRTO learner was live. Thus a possible existing
scientific process was not duplicated. The old zero exit establishes no resource or learner fact.

An initial read-only remote `git cat-file -t` for the new SHA entered the same unavailable
promisor transport. The specifically observed cat-file/fetch/HTTPS child processes were terminated;
no result task had been submitted. The authorized manual Git-object route then supplied only
committed objects: the launch commit, recursive trees, and blobs selected by the configured nine
sparse directories plus root files. Local `git pack-objects --stdout` produced 2,661 objects,
10,330,528 bytes, SHA-256
`70ec056d40b360879d999ad8d2a88ad5bca973d53d6bce0e0572a08ba8edacdd`.

```sh
scp source.pack hmasd-wsl-node:/tmp/crto-resume-8d1c5978-source.pack
git -C /home/wu/projects/HMASD index-pack --stdin < /tmp/crto-resume-8d1c5978-source.pack
git -C /home/wu/projects/HMASD worktree add --detach --no-checkout /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 8d1c597871b38edc7d5f139f34f5a3ce2941c7d0
git -C /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 sparse-checkout set hmasd ha_ctse_process envs environments experiments scripts tools tests manifold_hmasd
git -C /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 read-tree -mu HEAD
```

Remote pack SHA-256 matched; `index-pack` returned `f8356873e4331a34441ddb40502675f67c0e8d01`.
The new worktree HEAD matched the launch SHA and porcelain was empty. Direct null-delimited
`ls-tree -rz HEAD` and `hash-object --no-filters` inspection found all 1,954 selected files,
including all 1,938 configured-surface files, present and byte-equal to their Git blobs. An earlier
line-based check misparsed one Git-quoted non-ASCII root PDF name; the null-delimited check
resolved that inspection defect. No source materialization defect was found.

The exact-source remote focused command was:

```sh
cd /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02
/home/wu/.venvs/hmasd/bin/python -m pytest -q tests/experiments/candidates/commitment_residual_triggered_options/raw_phase_trace_a01
```

Result: **6 passed in 1.72s**, including the single toy end-to-end smoke. This establishes
focused engineering conformance, not real-population runtime completion or scientific value.

## Probe and exact result command

One non-result task, `crto_raw_phase_probe_8d1c5978_r02`, ran from the new worktree at
2026-09-04T21:36:36Z and finished exit 0 at 21:36:37Z. Its inner command was:

```sh
cd /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_probe_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_crto_raw_phase_trace_a01.py project-cost --seed 0
```

Its authoritative script preserved the full command, and its output included admission,
projection, initialization anchor and Torch thread counts 1/1. Probe available physical and
effective memory were both 15,441,698,816 bytes. This probe did not run the formal learner.

The exact result inner command, frozen before submission, was:

```sh
cd /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_crto_raw_phase_trace_a01.py run --seed 0 --admission-receipt temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_admission.json --output-dir temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02 --execution-node wsl_4070
```

Both submissions used Python `subprocess.run(['ssh', 'hmasd-wsl-node', remote_command])`, where
`remote_command` was `/usr/local/bin/agent-task run <task> ` plus `shlex.quote(command)`, and
`command` was `bash -lc ` plus `shlex.quote(inner_command)`. Thus the supervisor received one
argument containing the full shell command. The generated result `runner.sh` was inspected
directly and retained the complete joined admission/runner payload.

Execution node: configured `wsl_4070`, host `LAPTOP-U9TDKC8A`, Linux
6.6.87.2-microsoft-standard-WSL2, CPU only. Prospectively portable CPU semantics were retained;
no GPU or local fallback ran. One process/thread, expected RSS below 2 GiB, actual available
physical/effective memory at least 4 GiB. Stop: one complete summary or first admission,
integrity, learner-measurement or 1800-second wall-cap failure.

## Terminal observation and limits

| Fact | Observation |
| --- | --- |
| Result task | `crto_raw_phase_a01_8d1c5978_resume_r02` |
| Supervisor / learner PID | 73153 / 73156 |
| Start / end UTC | 2026-09-04T21:37:50Z / 21:38:08Z |
| Terminal status | failed, exit 139, tmux inactive |
| Supervisor duration | 18 seconds |
| Fresh admission time | 2026-09-04T21:37:51.040763Z |
| Physical / effective availability | 15,424,868,352 / 15,424,868,352 bytes; both passed |
| Live RSS sample at about 11s | 709,756 KiB; not peak RSS |
| Result root | present, empty; preserved |
| Summary, trace, anchors, work counts | absent / unmeasured |
| Learner updates actually completed | unknown, not inferred to be zero |
| Peak RSS and learner wall telemetry | unavailable |

The task log reports `Segmentation fault (core dumped)`. Kernel output reports fatal signal 11
and a WSL CaptureCrash event for PID 73156, executable
`/home/wu/.local/share/uv/python/cpython-3.10.21-linux-x86_64-gnu/bin/python3.10`.
Read-only package metadata reports Python 3.10.21 (Clang 22.1.3), NumPy 1.26.3 and Torch
2.7.0+cu118; these match the configured numerical dependency versions. GPU was not selected.

The adjacent kernel register/instruction record names Python PID 74008, which was not independently
mapped to CRTO learner PID 73156. It is preserved as adjacent evidence, not attributed to the
CRTO failing step. The CaptureCrash line itself explicitly names PID 73156 and signal 11.

No core file was found in the worktree root, `/var/crash`, or `/var/lib/systemd/coredump`.
The kernel core pattern is `|/wsl-capture-crash %t %E %p %s`; the helper itself is not visible
at that path in this distribution. `gdb` is present; `coredumpctl` is not. No debugger replay
was possible over an existing core. The failing learner step was not rerun, no new learner
exposure was generated for diagnosis, and no source/dependency repair was made. The SIGSEGV
event is directly corroborated; its native-runtime cause and precise failing step remain
provisional. A minimal next diagnostic would first obtain the existing WSL crash capture, or,
under a separate bounded assignment, reproduce the failing path with stack capture at these
same source/dependency bytes. No such diagnostic launch is included here.

The complete frozen assignment did not publish. Admission and test success cannot compensate
for missing learner measurements. No residual, competence, checkpoint-phase or other scientific
polarity follows. Final remote porcelain remained empty; no live CRTO result process remained.

## Preserved evidence

Remote task root: `/home/wu/.agent-tasks/crto_raw_phase_a01_8d1c5978_resume_r02/`.
Remote result root: `/home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02/temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02/`.

Local byte-preserving copies are under
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_artifacts/`.
There is no local raw summary because no remote summary exists. The directory also holds
`status.json`, `dependencies.json`, `kernel_excerpt.txt`, and `root_listing.txt` from direct
read-only queries. Status uptime is query-relative; start/end in the immutable task log are
the duration evidence.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| old_runner.sh | 1042 | `9089b7dedfcc8602837121d046c5f6a2e924eb24662947b43d1e9537b611ccb1` |
| old_task.log | 192 | `2cb2620564993115f10061a690925d01db8b83c66cad2b66f3ebc7ecdcffe05a` |
| probe_runner.sh | 1386 | `7a1a407c02f2e2db930d7392ad88cac135d76323e2facd651cf9d6e72273078b` |
| probe_task.log | 9068 | `ff580a51cd2afd6fb0d01ac2e8cbc82886ffc3b2656204ecabbd299f2f33ac17` |
| runner.sh | 1686 | `904d935f00785349c61718ec98fd84b7d178dd103365dab9b93500ceb9b58fff` |
| task.log | 1470 | `be94234da279be9712b58a822ffbf420d769f26f5156a864a187ed9e828bef50` |
| admission.json | 504 | `fe1029e1bee859bc6e90a23ab0489e60adbc01f55f077a8bfb6a19ec1f53f709` |

The old/new task script and log plus admission digests were compared against remote
`sha256sum`; copies match. Historical roots and this empty attempted root were left in place.
