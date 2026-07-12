# R27-G2 Remote SSH Automation

Date: 2026-07-12

## Boundary

HMASD reuses the passwordless Ed25519 key already installed for the same
AutoDL endpoint and `root` account. The private key remains outside the
repository at `~/.ssh/imod_autodl`; the repository contains only a non-secret
SSH host configuration.

The legacy wrapper's default action is `prepare`: remote storage/CUDA preflight, registered
checkpoint staging, fast-forward update of a clean Git checkout on the data
disk, and a zero-write runner dry-run. It does not launch an experiment.
The 2026-07-13 overnight authorization is implemented by the separate guarded
orchestrator described below; legacy `launch`/`all` are disabled.

Source sync defaults to the GitHub SSH remote
`git@github.com:CartmanFatass/My-paper-code.git`. The AutoDL host can reach this
remote through its existing GitHub SSH credentials; HTTPS clone is not used
because outbound GitHub HTTPS was unreliable on this host.

Server-availability policy (2026-07-13 user directive): assume the server is
available and attempt the scoped SSH action directly. Notify the user to wake
it only after the connection fails or the host is unreachable; do not require
a pre-SSH confirmation.

All large or persistent remote state is rooted under
`/root/autodl-tmp/HMASD/`. The wrapper rejects a source/run/checkpoint root on
the small system disk. On 2026-07-12 the read-only preflight observed roughly
6.6 GiB free on `/` and 50 GiB free on the separate `/root/autodl-tmp`
filesystem. Every preflight rechecks that the filesystems differ and that the
data disk has at least 20 GiB free (configurable upward with
`-MinimumDataDiskFreeGiB`).

## Files

- `scripts/remote/hmasd_autodl_ssh_config`: host, port, account, shared key
  path, BatchMode, host-key policy, and keepalive settings.
- `scripts/remote/run_hmasd_r27_g2.ps1`: local validation, remote CUDA and
  checkpoint preflight/staging, Git source sync, dry-run, historical-run
  polling, and raw-result archive download. Its launch entries are disabled.
- `scripts/remote/run_hmasd_r27_g2_overnight.ps1`: authorized fail-closed
  topology-probe, quarantined-pilot, and conditional decision-grade chain.
- `scripts/remote/watch_r27_g2_status.sh`: dependency-light, read-only terminal
  dashboard for reset progress, scientific counts, process/GPU state, and log
  tails.

## Safe preparation

After committing and pushing the intended R27-G2 source branch:

```powershell
pwsh -File scripts/remote/run_hmasd_r27_g2.ps1 -Action validate-local
pwsh -File scripts/remote/run_hmasd_r27_g2.ps1 -Action prepare
```

`prepare` requires the three registered checkpoint filenames to exist and be
nonempty, copies each missing file through a temporary path into
`/root/autodl-tmp/HMASD/checkpoint_dist/`, then updates
`/root/autodl-tmp/HMASD/source/` with `git fetch`, branch checkout, and
`git pull --ff-only`. The worktree must be clean before and after the update.
It then renders the exact 192-reset dry-run. Checkpoint update and model
metadata are checked by the collector when each file is loaded. The old
`/root/HMASD/dist/` copies are read-only sources; they are never deleted by
this workflow.

## Authorized overnight chain

After committing and pushing the exact clean branch, preview and start the
2026-07-13 user-authorized chain with:

```powershell
pwsh -File scripts/remote/run_hmasd_r27_g2_overnight.ps1 -Action dry-run
pwsh -File scripts/remote/run_hmasd_r27_g2_overnight.ps1 -Action launch `
  -LaunchAuthorization EXP-20260712-r27-g2-overnight-authorized
pwsh -File scripts/remote/run_hmasd_r27_g2_overnight.ps1 -Action status
```

The generated detached `screen` controller executes exactly:

```text
probe8 -> pilot8 WIRING_PASS -> probe64
                              -> RESOURCE_CAPACITY only: probe32
         -> highest PASS topology (64 or 32) -> decision grade
```

Probe 8 is expected to take 5-15 minutes. The exact final-checkpoint pilot is
83,600 environment steps and is expected to take 3-5 hours on cloud CUDA; its
metrics are quarantined and cannot enter a scientific gate. Probe 64 is
expected to take 7-15 minutes. Decision grade is 2,124,000 environment steps,
estimated at 12-20 hours with 64 workers or 24-40 hours with the permitted
32-worker resource-capacity fallback. An execution failure, invalid/incomplete
pilot, or failed 32-worker probe stops the chain. CPU, serial, and fewer than
32 decision workers are forbidden.

The overnight wrapper requires a clean local worktree whose HEAD exactly
matches the fetched remote branch, then fast-forwards the clean remote Git
checkout to that exact commit. It also checks CUDA, the three registered
checkpoints, a separate data-disk filesystem with at least 20 GiB free, and the
absence of another R27-G2 `screen` session or an existing overnight pointer.
Its structured status is under the timestamped orchestration root in
`/root/autodl-tmp/HMASD/r27_g2_remote/runs/`.

`scripts/package_r27_g2_runtime.ps1` remains available only for an optional
structural review ZIP. That ZIP is not deployed and is never a launch source.

For a historical legacy run, open its terminal dashboard from Windows:

```powershell
pwsh -File scripts/remote/run_hmasd_r27_g2.ps1 -Action watch
```

Or, from a shell already open on the server:

```bash
source /root/autodl-tmp/HMASD/r27_g2_remote/controller/current_source.env
bash "$repo_dir/scripts/remote/watch_r27_g2_status.sh"
```

Use `Ctrl+C` to leave the dashboard. It never starts, stops, or resumes work.
The dashboard shows each checkpoint's 64-reset progress bar, operational and
scientific counts, `screen` session state, GPU utilization, data-disk space,
active shards, and launcher log tail.

For the overnight chain, use its own structured view:

```powershell
pwsh -File scripts/remote/run_hmasd_r27_g2_overnight.ps1 -Action status
pwsh -File scripts/remote/run_hmasd_r27_g2_overnight.ps1 -Action watch
```

The overnight wrapper starts authorized work as a detached GNU `screen`
session, not as a foreground SSH child or bare `nohup` job. Historical runs
created by the legacy wrapper recorded their session name and launch script
are recorded in `controller/current_run.env`, and status/wait/collect all use
that recorded session identity. The overnight wrapper instead records
`controller/current_overnight.env`, supports status/watch rather than
wait/collect, and deliberately rejects an implicit rerun while that pointer
exists. SSH disconnection therefore does not terminate either runner.

The controller `.env` files are emitted as newline-separated safe shell
assignments with a single-quoted `printf` format. This is intentional: Windows
OpenSSH may otherwise remove a double-quoted remote format before Bash parses
its `\n` escapes.

For the legacy wrapper, an old `batch_status.txt` is never sufficient proof of completion. Reissuing
the guarded launch enters the Git-tracked runner's artifact-aware resume path.
`wait` returns success only after the recorded `screen` session exits and a
single-process `validate-run` pass rechecks all 192 reset manifests, typed
evidence, and the final JSON and Markdown reports. Complete result collection
repeats the same validation before creating its archive. After the reset phase,
the runner always regenerates the aggregate from the current 192 structured
shards; it never reuses an older aggregate status or report.

## Disabled legacy launch entry

The legacy wrapper now rejects both `-Action launch` and `-Action all` before
any SSH action. This closes the older direct-decision path so it cannot bypass
probe 8, the quarantined pilot, the exact worker topology checks, or the
32-worker floor. Use the guarded overnight wrapper for the authorized chain.
The legacy wrapper remains available for preparation, status/watch/wait, and
collection of runs created under its historical interface.

This file documents the interface; it does not grant any launch authorization.

## Status and result custody

The remote controller stores its source/run pointers under
`/root/autodl-tmp/HMASD/r27_g2_remote/controller/`. The cloud runner remains
the source of operational and scientific status under the timestamped run
root. Legacy `collect` can archive and download a historical `current_run.env`
run. The overnight chain retains raw artifacts on the data disk and exposes
them through `current_overnight.env`; it does not automatically archive or
download them while compute is active.

Passwords, private keys, checkpoints, and result archives are never committed
to the repository.
