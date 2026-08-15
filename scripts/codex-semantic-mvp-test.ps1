[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [switch]$DryRun,
    [switch]$NativeSmoke,
    [string]$CodexCommand = "codex",
    [ValidateRange(10, 900)]
    [int]$NativeTimeoutSec = 120
)

$ErrorActionPreference = "Stop"
$python = "C:\Users\wu\.conda\envs\SB3\python.exe"
$root = if ([IO.Path]::IsPathRooted($RepoRoot)) { [IO.Path]::GetFullPath($RepoRoot) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $RepoRoot)) }
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Repository root does not exist: $root" }

function Resolve-CodexCommand {
    param([string]$Command)
    $candidate = $null
    if ([IO.Path]::IsPathRooted($Command) -or $Command.Contains([IO.Path]::DirectorySeparatorChar) -or $Command.Contains([IO.Path]::AltDirectorySeparatorChar)) {
        $candidate = Get-Item -LiteralPath $Command -ErrorAction SilentlyContinue
    } else {
        $candidate = Get-Command -Name $Command -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($candidate) { $candidate = Get-Item -LiteralPath ($candidate.Source ?? $candidate.Path) -ErrorAction SilentlyContinue }
    }
    if (-not $candidate) { throw "NATIVE_SMOKE_CODEX_COMMAND_INVALID: cannot resolve '$Command' to an executable .exe/.cmd" }
    $extension = [IO.Path]::GetExtension($candidate.FullName).ToLowerInvariant()
    if ($extension -eq ".ps1") {
        $sibling = Join-Path $candidate.DirectoryName ($candidate.BaseName + ".cmd")
        if (Test-Path -LiteralPath $sibling -PathType Leaf) { return [IO.Path]::GetFullPath($sibling) }
        throw "NATIVE_SMOKE_CODEX_COMMAND_INVALID: PowerShell shim '$($candidate.FullName)' has no executable sibling '$sibling'"
    }
    if ($extension -notin @(".exe", ".cmd")) {
        throw "NATIVE_SMOKE_CODEX_COMMAND_INVALID: '$($candidate.FullName)' is not a directly executable .exe/.cmd"
    }
    return [IO.Path]::GetFullPath($candidate.FullName)
}

function Invoke-NativeSmoke {
    param(
        [string]$Root,
        [string]$Command,
        [int]$TimeoutSec
    )

    $resolvedCommand = Resolve-CodexCommand -Command $Command
    $configPath = Join-Path $Root ".codex\config.toml"
    $config = [IO.File]::ReadAllText($configPath)
    $begin = "# BEGIN HMASD CODEX SEMANTIC HOOKS"
    $end = "# END HMASD CODEX SEMANTIC HOOKS"
    $mcpBegin = "# BEGIN HMASD CODEX SEMANTIC MVP"
    $mcpEnd = "# END HMASD CODEX SEMANTIC MVP"
    $markers = @($begin, $end, $mcpBegin, $mcpEnd)
    foreach ($marker in $markers) {
        if (([regex]::Matches($config, [regex]::Escape($marker))).Count -ne 1) {
            throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: expected exactly one marker '$marker' in $configPath"
        }
    }
    $hookBeginAt = $config.IndexOf($begin)
    $hookEndAt = $config.IndexOf($end)
    $mcpBeginAt = $config.IndexOf($mcpBegin)
    $mcpEndAt = $config.IndexOf($mcpEnd)
    if ($hookEndAt -le $hookBeginAt -or $mcpEndAt -le $mcpBeginAt) {
        throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: malformed managed marker ordering in $configPath"
    }
    $hookBlock = $config.Substring($hookBeginAt + $begin.Length, $hookEndAt - $hookBeginAt - $begin.Length)
    $mcpBlock = $config.Substring($mcpBeginAt + $mcpBegin.Length, $mcpEndAt - $mcpBeginAt - $mcpBegin.Length)
    foreach ($event in @("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse")) {
        $eventHeader = '(?m)^\[\[hooks\.' + $event + '\]\][ \t]*\r?$'
        if (([regex]::Matches($hookBlock, $eventHeader)).Count -ne 1) {
            throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: missing hooks.$event handler"
        }
        $eventSection = [regex]::Match($hookBlock, '(?ms)^\[\[hooks\.' + $event + '\]\][ \t]*\r?\n(.*?)(?=^\[\[hooks\.[A-Za-z]+\]\][ \t]*\r?$|\z)').Groups[1].Value
        $nestedHeaders = @([regex]::Matches($eventSection, '(?m)^\[\[hooks\.[^\]]+\]\][ \t]*\r?$') | ForEach-Object { $_.Value.Trim() })
        $nestedExpected = "[[hooks.$event.hooks]]"
        $typeLines = @([regex]::Matches($eventSection, '(?m)^type[ \t]*=[ \t]*"[^"]*"[ \t]*\r?$'))
        $commandLines = @([regex]::Matches($eventSection, '(?m)^command[ \t]*=[ \t]*"[^"]*"[ \t]*\r?$'))
        if ($nestedHeaders.Count -ne 1 -or $nestedHeaders[0] -ne $nestedExpected -or
            $typeLines.Count -ne 1 -or $typeLines[0].Value.Trim() -ne 'type = "command"' -or
            $commandLines.Count -ne 1 -or $commandLines[0].Value.Trim() -ne 'command = "C:\\Users\\wu\\.conda\\envs\\SB3\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"') {
            throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: missing hooks.$event handler"
        }
    }
    $features = [regex]::Match($config, '(?ms)^\[features\][ \t]*\r?\n(.*?)(?=^\[|\z)').Groups[1].Value
    if (-not $features -or $features -notmatch '(?m)^hooks[ \t]*=[ \t]*true[ \t]*\r?$') {
        throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: live hooks/config state is incomplete"
    }
    $mcpSectionMatch = [regex]::Match($mcpBlock, '(?ms)^\[mcp_servers\.hmasd_orchestrator\][ \t]*\r?\n(.*?)(?=^\[|\z)')
    $mcpSection = $mcpSectionMatch.Groups[1].Value
    $argsMatch = [regex]::Match($mcpSection, '(?ms)^args[ \t]*=[ \t]*\[\s*(.*?)^\s*\][ \t]*\r?$')
    $argLines = @()
    if ($argsMatch.Success) { $argLines = @($argsMatch.Groups[1].Value -split "`r?`n" | ForEach-Object { $_.Trim().TrimEnd(',') } | Where-Object { $_ }) }
    $expectedArgs = @('"-m"', '"tools.codex_semantic_mvp.mcp_server"', '"--state-dir"', '"runtime/codex-semantic-mvp"')
    if (-not $mcpSectionMatch.Success -or
        ([regex]::Matches($mcpSection, '(?m)^command[ \t]*=')).Count -ne 1 -or
        $mcpSection -notmatch '(?m)^command[ \t]*=[ \t]*"C:\\\\Users\\\\wu\\\\\.conda\\\\envs\\\\SB3\\\\python\.exe"[ \t]*\r?$' -or
        $argLines.Count -ne $expectedArgs.Count -or
        (@(0..($expectedArgs.Count - 1) | Where-Object { $argLines[$_] -ne $expectedArgs[$_] }).Count -ne 0) -or
        ([regex]::Matches($mcpSection, '(?m)^enabled[ \t]*=[ \t]*(?:true|false)')).Count -ne 1 -or
        $mcpSection -notmatch '(?m)^enabled[ \t]*=[ \t]*true[ \t]*\r?$') {
        throw "NATIVE_SMOKE_REQUIRES_INLINE_TOML: hmasd_orchestrator section must use the vetted SB3 command, relative state, and enabled=true"
    }

    $auditPath = Join-Path $Root "runtime\codex-semantic-mvp\audit.jsonl"
    $activationPath = Join-Path $Root "runtime\codex-semantic-mvp\activation-state.json"
    $configBefore = [IO.File]::ReadAllBytes($configPath)
    $activationBeforeExists = Test-Path -LiteralPath $activationPath -PathType Leaf
    $activationBefore = if ($activationBeforeExists) { [IO.File]::ReadAllBytes($activationPath) } else { $null }
    $beforeBytes = if (Test-Path -LiteralPath $auditPath -PathType Leaf) { [IO.File]::ReadAllBytes($auditPath).Length } else { 0 }
    $beforeCount = if ($beforeBytes -gt 0) { @([IO.File]::ReadAllLines($auditPath)).Count } else { 0 }
    $tempBase = Join-Path ([IO.Path]::GetTempPath()) ("codex-semantic-native-smoke-" + [guid]::NewGuid().ToString("N"))
    $stdoutPath = "$tempBase.out"
    $stderrPath = "$tempBase.err"
    $prompt = "Read-only smoke check. Do not edit files, run commands, or change configuration. Reply with exactly NATIVE_SEMANTIC_SMOKE_OK."
    $process = $null
    try {
        $startInfo = [Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $resolvedCommand
        $startInfo.WorkingDirectory = $Root
        $startInfo.UseShellExecute = $false
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        foreach ($argument in @(
            "exec", "--json", "--dangerously-bypass-hook-trust", "--skip-git-repo-check",
            "--cd", $Root, "--model", "gpt-5.6-luna", $prompt
        )) { [void]$startInfo.ArgumentList.Add($argument) }
        $process = [Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        [void]$process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSec * 1000)) {
            try { $process.Kill($true) } catch { $process.Kill() }
            throw "NATIVE_SMOKE_TIMEOUT: codex exec exceeded ${TimeoutSec}s"
        }
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        [IO.File]::WriteAllText($stdoutPath, $stdout)
        [IO.File]::WriteAllText($stderrPath, $stderr)
        if ($process.ExitCode -ne 0) {
            throw "NATIVE_SMOKE_CLI_FAILED: exit=$($process.ExitCode) stderr=$($stderr.Trim()) stdout=$($stdout.Trim())"
        }
    }
    finally {
        if ($process -and -not $process.HasExited) { try { $process.Kill($true) } catch {} }
        foreach ($path in @($stdoutPath, $stderrPath)) { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force } }
    }

    if ([Convert]::ToBase64String($configBefore) -ne [Convert]::ToBase64String([IO.File]::ReadAllBytes($configPath))) {
        throw "NATIVE_SMOKE_CONFIG_MUTATED: .codex/config.toml changed during smoke"
    }
    $activationAfterExists = Test-Path -LiteralPath $activationPath -PathType Leaf
    if ($activationBeforeExists -ne $activationAfterExists -or ($activationBeforeExists -and [Convert]::ToBase64String($activationBefore) -ne [Convert]::ToBase64String([IO.File]::ReadAllBytes($activationPath)))) {
        throw "NATIVE_SMOKE_ACTIVATION_STATE_MUTATED: activation-state.json changed during smoke"
    }
    $jsonEvents = @()
    foreach ($line in ($stdout -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try { $jsonEvents += ($line | ConvertFrom-Json) } catch { }
    }
    $sessionIds = @($jsonEvents | ForEach-Object { if ($_.thread_id) { [string]$_.thread_id } elseif ($_.session_id) { [string]$_.session_id } } | Where-Object { $_ })
    if ($sessionIds.Count -ne 1) { throw "NATIVE_SMOKE_SESSION_ID_REQUIRED: codex exec --json did not yield exactly one session identifier" }
    $nativeSessionId = [string]$sessionIds[0]
    $afterBytes = if (Test-Path -LiteralPath $auditPath -PathType Leaf) { [IO.File]::ReadAllBytes($auditPath).Length } else { 0 }
    $afterCount = if ($afterBytes -gt 0) { @([IO.File]::ReadAllLines($auditPath)).Count } else { 0 }
    $newEvents = @()
    if ($afterBytes -gt $beforeBytes) {
        $suffix = [Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($auditPath), $beforeBytes, $afterBytes - $beforeBytes)
        foreach ($line in ($suffix -split "`r?`n")) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            try {
                $record = $line | ConvertFrom-Json
                if ($record.event -in @("SESSION_STARTED", "SUBAGENT_STARTED", "SUBAGENT_STOPPED", "STOP_OBSERVED", "PRE_TOOL_USE_OBSERVED") -and
                    [string]$record.session_id -eq $nativeSessionId -and [string]$record.mode -eq "active") { $newEvents += $record }
            } catch { }
        }
    }
    if ($newEvents.Count -eq 0) {
        throw "NATIVE_HOOK_EVENT_REQUIRED: codex exec exited 0 but audit cursor did not contain a new native hook event (session_id=$nativeSessionId before_count=$beforeCount after_count=$afterCount before_bytes=$beforeBytes after_bytes=$afterBytes)"
    }
    Write-Output "NATIVE_SMOKE_VERIFIED=true"
    Write-Output "NATIVE_SMOKE_AUDIT_BEFORE_COUNT=$beforeCount"
    Write-Output "NATIVE_SMOKE_AUDIT_AFTER_COUNT=$afterCount"
    Write-Output "NATIVE_SMOKE_NEW_EVENTS=$($newEvents.Count)"
}

Push-Location $root
try {
    if ($NativeSmoke) {
        Invoke-NativeSmoke -Root $root -Command $CodexCommand -TimeoutSec $NativeTimeoutSec
        return
    }
    & $python -m pytest tests\codex_semantic_mvp -q
    if ($LASTEXITCODE -ne 0) { throw "semantic MVP tests exited with code $LASTEXITCODE" }
    & $python -m tools.codex_semantic_mvp.doctor --repo-root .
    if ($LASTEXITCODE -ne 0) { throw "doctor exited with code $LASTEXITCODE" }

    if ($DryRun) {
        $scriptDir = Join-Path $root "scripts"
        foreach ($activationMode in @("Shadow", "Active")) {
            $stage = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-codex-semantic-mvp-test-" + [guid]::NewGuid().ToString("N"))
            try {
                New-Item -ItemType Directory -Path (Join-Path $stage ".codex") -Force | Out-Null
                foreach ($name in @("hooks.json", "config.toml", "hooks.semantic-mvp.shadow.json", "hooks.semantic-mvp.active.json")) {
                    Copy-Item -LiteralPath (Join-Path $root ".codex\$name") -Destination (Join-Path $stage ".codex\$name")
                }
                $before = [IO.File]::ReadAllBytes((Join-Path $stage ".codex\hooks.json"))
                $baselineHash = (Get-FileHash -LiteralPath (Join-Path $stage ".codex\hooks.json") -Algorithm SHA256).Hash.ToLowerInvariant()
                & (Join-Path $scriptDir "codex-semantic-mvp-enable.ps1") -RepoRoot $stage -Mode $activationMode -ExpectedHooksHash $baselineHash
                if ($LASTEXITCODE -ne 0) { throw "dry-run $activationMode enable failed" }
                & (Join-Path $scriptDir "codex-semantic-mvp-disable.ps1") -RepoRoot $stage
                if ($LASTEXITCODE -ne 0) { throw "dry-run $activationMode disable failed" }
                $after = [IO.File]::ReadAllBytes((Join-Path $stage ".codex\hooks.json"))
                if (-not [Linq.Enumerable]::SequenceEqual($before, $after)) { throw "DRY_RUN_$activationMode_ROLLBACK_BYTES_CHANGED" }
                Write-Output "DRY_RUN_$($activationMode.ToUpperInvariant())_ROLLBACK_VERIFIED=true"
            }
            finally {
                if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
            }
        }
    }
}
finally {
    Pop-Location
}
