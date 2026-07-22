[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string[]]$Terms,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
} else {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

$alwaysInspect = @(
    'AGENTS.md',
    'docs/project/CURRENT_WORK.md',
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-dispatch-task/references/session-roles.json',
    'docs/external-review/REVIEWER_CONVERSATIONS.json',
    'docs/external-review/README.md',
    'tests/hmasd_dispatch_task_contract_test.ps1',
    'tests/hmasd_project_manager_contract_test.ps1',
    'tests/hmasd_research_workflow_contract_test.ps1'
)

$files = [System.Collections.Generic.List[string]]::new()
foreach ($relative in $alwaysInspect) {
    $path = Join-Path $RepoRoot $relative
    if (Test-Path -LiteralPath $path -PathType Leaf) { $files.Add($path) }
}
$skillRoot = Join-Path $RepoRoot '.agents/skills'
if (Test-Path -LiteralPath $skillRoot -PathType Container) {
    Get-ChildItem -LiteralPath $skillRoot -Recurse -File |
        Where-Object { $_.Extension -in @('.md', '.json', '.yaml', '.yml', '.ps1', '.py') } |
        ForEach-Object { $files.Add($_.FullName) }
}
$testsRoot = Join-Path $RepoRoot 'tests'
if (Test-Path -LiteralPath $testsRoot -PathType Container) {
    Get-ChildItem -LiteralPath $testsRoot -File -Filter '*contract_test.ps1' |
        ForEach-Object { $files.Add($_.FullName) }
}

$matches = [System.Collections.Generic.List[object]]::new()
foreach ($file in @($files | Sort-Object -Unique)) {
    foreach ($term in $Terms) {
        if ([string]::IsNullOrWhiteSpace($term)) { continue }
        foreach ($hit in @(Select-String -LiteralPath $file -SimpleMatch -Pattern $term)) {
            $relative = $file.Substring($RepoRoot.Length).TrimStart([char[]]@('\', '/')).Replace('\', '/')
            $matches.Add([pscustomobject]@{term=$term; path=$relative; line=$hit.LineNumber; text=$hit.Line.Trim()})
        }
    }
}

[pscustomobject]@{
    schema_version = 1
    repo_root = $RepoRoot
    terms = @($Terms)
    always_inspect = $alwaysInspect
    matches = @($matches | Sort-Object path, line, term)
} | ConvertTo-Json -Depth 6
