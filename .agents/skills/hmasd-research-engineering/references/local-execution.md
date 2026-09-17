# Local Windows result execution

Use when local Windows is the suitable declared node. This is an alternative to remote
`agent-task`, not a new supervisor framework. Read the interpreter and project location from
`.codex/hmasd-compute.toml`. Commit/publish the inputs and use an unchanged source snapshot
while the process runs; a detached Git worktree is convenient if authoring will continue.

Prepare one run-specific PowerShell wrapper under the assigned scratch/output directory.
Substitute concrete absolute paths and runner arguments below; do not execute placeholders.
Keep the wrapper as part of the run's command evidence. The output directory is unique to this
attempt and already exists; status, stdout and stderr are native run outputs, not approval receipts.

```powershell
# run.ps1: the actual interpreter, source and outputs of this one attempt
$ErrorActionPreference = 'Stop'
$runPython = '<configured absolute python.exe>'
$runSource = '<unchanged source snapshot>'
$runOutput = '<unique absolute output directory>'
$runExit = 1
try {
    Set-Location -LiteralPath $runSource
    & $runPython 'scripts/hmasd_resource_preflight.py' admit-memory --out "$runOutput/preflight.json"
    if ($LASTEXITCODE -ne 0) { throw 'Memory admission failed; runner not started' }
    & $runPython '<runner path>' '<actual arguments as separate array elements>'
    $runExit = $LASTEXITCODE
} catch {
    $_ | Out-String | Add-Content -LiteralPath "$runOutput/wrapper-error.txt"
} finally {
    @{ exit_code = $runExit; finished_utc = [DateTime]::UtcNow.ToString('o') } |
        ConvertTo-Json | Set-Content -LiteralPath "$runOutput/process-exit.json"
}
exit $runExit
```

Launch the concrete wrapper with native `Start-Process` using `-WindowStyle Hidden`,
`-PassThru`, a configured working directory and separate redirected stdout/stderr files.
Use the actual PowerShell executable path and quote the wrapper path as a single `-File`
argument, particularly if it contains spaces. The scientific runner stays in that wrapper;
the wrapper waits for it, so preflight failure cannot fall through into training.

Record the returned process ID and start time, node, wrapper/source sha, cwd and outputs in
the existing run note. Observe that identity and `process-exit.json`, not a PID alone. A missing
process without terminal evidence is unknown; reconcile logs/identity instead of relaunching.
An exit file is process evidence, not scientific success. On hard termination it may never be
written; preserve that uncertainty. Direct observation is fine; a delegated observer receives
these same facts. This document does not authorize a result run or lift the owner's pause.
