# Generic Experiment Progress Watcher Design

Date: 2026-07-11
Status: user-approved design, pending implementation

## Goal

Add a reusable PowerShell watcher that monitors an existing HA-CTSE/HMASD
experiment directory and atomically refreshes `<RunRoot>/progress.md` every ten
minutes. It is observability-only: it never starts, stops, retries, resumes, or
modifies the experiment.

The first target is:

```text
logs/r26_g1a_screening_20260711_105522
```

The script must remain generic enough for later sequential arm-based runs that
use the same status/log conventions.

## Interface

Create:

```text
scripts/watch_experiment_progress.ps1
```

Parameters:

```powershell
param(
    [Parameter(Mandatory = $true)]
    [string]$RunRoot,
    [int]$IntervalMinutes = 10,
    [int]$StaleMinutes = 20,
    [int]$ExpectedResets = 64,
    [int]$LauncherPid = 0,
    [switch]$Once
)
```

Rules:

- Resolve `RunRoot` to an existing directory before writing.
- Require `IntervalMinutes >= 1`, `StaleMinutes >= 1`, and
  `ExpectedResets >= 1`.
- Write only `<RunRoot>/progress.md` and a temporary sibling used for atomic
  replacement.
- `-Once` performs one update and exits.
- Normal mode updates immediately, sleeps `IntervalMinutes`, and repeats.
- Normal mode writes one final snapshot and exits automatically when the batch
  reaches a terminal success or failure state.

## Data Sources

Read, when present:

- `<RunRoot>/batch_status.txt`;
- `<RunRoot>/arm*/runner_status.txt`;
- `<RunRoot>/arm*/windows/reset_*.npz`;
- `<RunRoot>/arm*/windows/collector_manifest.json`;
- `<RunRoot>/arm*/analysis/r26_g1_behavior.json` and Markdown;
- `<RunRoot>/arm*/collector_output.log` and `analyzer_output.log`;
- optional launcher PID and its descendants from `Win32_Process`;
- `nvidia-smi` GPU summary and compute-process rows.

The watcher must tolerate missing/not-yet-created files and partially written
status files. Read failures become explicit `unknown`/warning fields; they must
not terminate monitoring unless `RunRoot` itself is invalid.

## Progress Model

Discover arms from child directories named `arm*`, sorted by name. For every
arm report:

- state and phase from `runner_status.txt`;
- shard count and `ExpectedResets` fraction;
- manifest presence and recorded skill cardinality when available;
- analyzer JSON/Markdown presence;
- latest evidence timestamp and age;
- compact error state.

Batch progress is the count of terminal arms divided by discovered arms. The
active arm is the first arm in a running state. ETA is derived only after at
least one arm has completed, using measured completed-arm duration when status
timestamps permit; otherwise report `unknown`. ETA is operational only and is
not a scientific metric.

## Error And Staleness Detection

Scan only bounded tails of runner/collector/analyzer logs for:

```text
Traceback
RuntimeError
BrokenPipe
CUDA out of memory
out of memory
OOM
NaN
KeyboardInterrupt
failed with exit code
```

Avoid treating ordinary status text or checkpoint paths as errors. Report at
most the latest ten unique matches with relative paths.

Mark evidence stale when the latest relevant status, shard, manifest, analysis,
or log file is older than `StaleMinutes` while the batch is non-terminal.
Process absence is a warning unless the batch status is terminal. GPU absence
is a warning, not a reason to mutate the run.

## Markdown Contract

`progress.md` contains:

1. snapshot time and configured refresh interval;
2. run root, batch state, elapsed time, completion count, current arm/phase,
   and ETA;
3. launcher/child process and GPU summary;
4. warning/error summary;
5. an arm table with state, phase, shards, manifest, analysis, last update, and
   age;
6. a note that the file is operational evidence only and does not authorize a
   scientific or reward decision;
7. on terminal state, a final line saying the watcher exited automatically.

The script writes the complete content to `progress.md.tmp`, then replaces
`progress.md` in one filesystem operation so readers never observe a partial
document. Cleanup removes an abandoned temporary file in `finally`.

## Terminal Conditions

After each snapshot:

- `succeeded`, `finished`, or `completed` batch state: write final success
  snapshot and exit zero;
- `failed`, `error`, `crashed`, or any failed arm after the batch stops: write
  final failure snapshot and exit nonzero;
- absent/unknown/running state: continue monitoring.

The watcher does not infer completion solely from process absence when status
files remain non-terminal.

## Verification

1. PowerShell parser check.
2. `-Once` smoke against the active R26 run; verify `<RunRoot>/progress.md` is
   well-formed and reflects current arm/shards without changing any other run
   artifact.
3. Synthetic temporary run fixtures covering running, stale, successful, and
   failed states; verify terminal exit codes and final text.
4. Atomic-write cleanup check: no `.tmp` remains after success or failure.
5. Start the active watcher as a hidden detached process with
   `-IntervalMinutes 10`, then verify its PID and first generated snapshot.

## Non-Goals

- No Codex/LLM invocation.
- No automatic repair, retry, checkpoint resume, process termination, or new
  experiment launch.
- No scientific metric interpretation and no `memory/ExpRecord.md` updates.
- No changes to training, reward, policy, critic, collector, analyzer, or
  environment code.
