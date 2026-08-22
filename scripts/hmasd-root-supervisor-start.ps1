param(
    [string] $RepoRoot = (Get-Location).Path,
    [string] $RuntimeHome = (Join-Path (Get-Location).Path 'runtime/hmasd-root-supervisor'),
    [string] $PythonPath = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    [string] $CodexBin,
    [Nullable[double]] $DurationSeconds
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $RuntimeHome | Out-Null
$identityPath = Join-Path $RuntimeHome 'supervisor-process.json'
if (Test-Path $identityPath) {
    try {
        $old = Get-Content -Raw $identityPath | ConvertFrom-Json
        $running = Get-Process -Id ([int]$old.pid) -ErrorAction SilentlyContinue
        if ($running) { Write-Output 'HMASD_SUPERVISOR_READY_V1'; exit 0 }
    } catch { }
}
$stdout = Join-Path $RuntimeHome 'supervisor.stdout.log'
$stderr = Join-Path $RuntimeHome 'supervisor.stderr.log'
$args = @('-m','tools.codex_supervisor','--repo-root',$RepoRoot,'--runtime-home',$RuntimeHome)
if ($CodexBin) { $args += @('--codex-bin',$CodexBin) }
$args += @('serve')
if ($DurationSeconds.HasValue) { $args += @('--duration-seconds',[string]$DurationSeconds.Value) }
$process = Start-Process -FilePath $PythonPath -ArgumentList $args -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$record = [ordered]@{ schema = 'HMASD_SUPERVISOR_PROCESS_V1'; pid = $process.Id; started_at = [datetime]::UtcNow.ToString('o'); repo_root = (Resolve-Path $RepoRoot).Path; runtime_home = (Resolve-Path $RuntimeHome).Path; automatic_wake = $false }
$record | ConvertTo-Json | Set-Content -Encoding UTF8 $identityPath
Start-Sleep -Milliseconds 300
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) { Write-Output 'HMASD_SUPERVISOR_READY_V1' } else { Write-Output 'HMASD_SUPERVISOR_INCIDENT_V1'; exit 1 }
