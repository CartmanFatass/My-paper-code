param(
    [string]$Root = "."
)

$ErrorActionPreference = "Stop"
$rootPath = Resolve-Path -LiteralPath $Root

$requiredFiles = @(
    "AGENTS.md",
    ".codex/agents/README.md",
    ".codex/agents/exp-manager.toml",
    ".codex/agents/templates/subagent-task-brief.md",
    ".codex/agents/templates/subagent-report.md",
    ".codex/agents/templates/expmanager-checkpoint.md"
)

$requiredPatterns = @{
    "AGENTS.md" = @(
        "bounded soft timeouts",
        "Superpowers defines the process shape",
        "do not duplicate the query"
    )
    ".codex/agents/README.md" = @(
        "bounded soft timeouts",
        ".codex/agents/templates",
        "Superpowers defines the process shape"
    )
    ".codex/agents/exp-manager.toml" = @(
        "gpt-5.4-mini",
        "expmanager_checkpoint.md",
        "DONE_WITH_CONCERNS",
        "controller fallback peek"
    )
}

$failures = New-Object System.Collections.Generic.List[string]

foreach ($rel in $requiredFiles) {
    $path = Join-Path $rootPath $rel
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing file: $rel")
    }
}

foreach ($entry in $requiredPatterns.GetEnumerator()) {
    $path = Join-Path $rootPath $entry.Key
    if (-not (Test-Path -LiteralPath $path)) {
        continue
    }
    $text = Get-Content -Raw -LiteralPath $path
    foreach ($pattern in $entry.Value) {
        if ($text -notmatch [regex]::Escape($pattern)) {
            $failures.Add("Missing pattern '$pattern' in $($entry.Key)")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Subagent handoff contract check FAILED"
    foreach ($failure in $failures) {
        Write-Host " - $failure"
    }
    exit 1
}

Write-Host "Subagent handoff contract check passed"
