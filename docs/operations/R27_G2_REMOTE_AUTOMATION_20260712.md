# R27-G2 Remote SSH Automation

Date: 2026-07-12

## Boundary

HMASD reuses the passwordless Ed25519 key already installed for the same
AutoDL endpoint and `root` account. The private key remains outside the
repository at `~/.ssh/imod_autodl`; the repository contains only a non-secret
SSH host configuration.

The default action is `prepare`: remote storage/CUDA preflight, registered
checkpoint staging, fast-forward update of a clean Git checkout on the data
disk, and a zero-write runner dry-run. It does not launch an experiment.
R27-G2 pilot and decision-grade launch remain separately gated.

Current operator gate (2026-07-13): the server is asleep. Before any SSH,
`prepare`, status check, or launch action, notify the user and wait for explicit
confirmation that the server has been awakened.

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
  checkpoint preflight/staging, Git source sync, dry-run, guarded `screen`
  launch, polling, and raw-result archive download.
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

`scripts/package_r27_g2_runtime.ps1` remains available only for an optional
structural review ZIP. That ZIP is not deployed and is never a launch source.

After preparation, open the terminal dashboard from Windows:

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

Any authorized long run is started as a detached GNU `screen` session, not as
a foreground SSH child or bare `nohup` job. The session name and launch script
are recorded in `controller/current_run.env`, and status/wait/collect all use
that recorded session identity. SSH disconnection therefore does not terminate
the runner.

An old `batch_status.txt` is never sufficient proof of completion. Reissuing
the guarded launch enters the Git-tracked runner's artifact-aware resume path.
`wait` returns success only after the recorded `screen` session exits and a
single-process `validate-run` pass rechecks all 192 reset manifests, typed
evidence, and the final JSON and Markdown reports. Complete result collection
repeats the same validation before creating its archive. After the reset phase,
the runner always regenerates the aggregate from the current 192 structured
shards; it never reuses an older aggregate status or report.

## Launch gates

The wrapper intentionally rejects launch unless all of these are true:

1. `-LaunchAuthorization` exactly names
   `EXP-20260712-r27-g2-forced-z-trajectory-effect`;
2. the local HMASD worktree is clean and the remote checkout is on the
   registered branch with a clean worktree;
3. `MAX_WORKERS>1` is accompanied by `-ConcurrencyValidated` after a separate
   safe GPU/process topology check;
4. `MAX_WORKERS=1` is accompanied by `-AcceptSerialCost`, acknowledging the
   rough 576-960 collector-hour estimate rather than the registered 12-20h
   decision-grade target.

This file documents the interface; it does not grant any launch authorization.

## Status and result custody

The remote controller stores its current source/run pointer under
`/root/autodl-tmp/HMASD/r27_g2_remote/controller/`. The cloud runner remains
the source of operational and scientific status under the timestamped run
root. Collection archives the complete raw run directory, confirms the TAR is
readable on the server, downloads it, and confirms locally that it is readable
and contains the run status, collection record, and current source record.

Passwords, private keys, checkpoints, and result archives are never committed
to the repository.
