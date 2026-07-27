$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$codePmPath = Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md'
$operationsPath = Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md'
$oldPmPath = Join-Path $repo '.agents/roles/PROJECT_MANAGER.md'
$oldOperatorPath = Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md'
$codePm = Get-Content -Raw -LiteralPath $codePmPath
$operations = Get-Content -Raw -LiteralPath $operationsPath
$codePmNormalized = $codePm -replace '\s+', ' '
$operationsNormalized = $operations -replace '\s+', ' '
$workflow = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$agileNormalized = $agile -replace '\s+', ' '
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$handoff = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/RESTART_HANDOFF.md')
$readinessScriptPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py'
$hooksPath = Join-Path $repo '.codex/hooks.json'

if ((Test-Path $oldPmPath) -or (Test-Path $oldOperatorPath)) {
    throw 'Retired manager role path remains live'
}

$routerRequired = @(
    'code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'code_project_manager_code_authority=exclusive',
    'code_project_manager_technical_acceptance_authority=exclusive',
    'code_project_manager_runtime_authority=none',
    'code_project_manager_current_work_read=bounded_read_only_on_demand',
    'code_project_manager_current_work_write_authority=none',
    'research_operations_manager_runtime_authority=exclusive',
    'research_operations_manager_current_work_authority=exclusive',
    'research_operations_manager_external_review_transport_authority=exclusive',
    'research_operations_manager_mechanical_result_acceptance=exclusive',
    'research_operations_manager_code_authority=none',
    'research_operations_manager_code_acceptance_authority=none',
    'operational_recovery_owner=research_operations_manager',
    '.agents/roles/CODE_PROJECT_MANAGER.md',
    '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md'
)
foreach ($required in $routerRequired) {
    if (-not $agents.Contains($required)) { throw "AGENTS split authority missing: $required" }
}

$codeRequired = @(
    'role=code_project_manager',
    'code_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'runtime_authority=none',
    'current_work_read=bounded_read_only_on_demand',
    'current_work_write_authority=none',
    'scientific_authority=none',
    'git_execution=direct_for_code_tests_and_code_science_index',
    'code_children=code_scout|implementer|reviewer|verifier',
    'may read `docs/project/CURRENT_WORK.md` only to check the current',
    'not replace a complete incoming assignment',
    'Never edit, stage, commit or advance',
    'CODE_ACCEPTED',
    'CODE_SCIENCE_INDEX.md',
    'execution_readiness_owner=code_project_manager',
    'execution_readiness_receipt=required_when_triggered',
    'Focused tests alone are insufficient',
    '`interface_smoke`',
    '`bounded_exercise`',
    '`artifact_validation`',
    '`artifact_reload`',
    '`evaluate_entry`',
    '`analyze_entry`',
    'Research Operations Manager',
    'Workflow Design Manager'
)
foreach ($required in $codeRequired) {
    if (-not $codePmNormalized.Contains($required)) { throw "Code Project Manager contract missing: $required" }
}

$operationsRequired = @(
    'role=research_operations_manager',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'external_review_transport_authority=exclusive',
    'experiment_dispatch_and_result_routing=exclusive',
    'mechanical_result_acceptance=exclusive',
    'code_authority=none',
    'code_acceptance_authority=none',
    'scientific_authority=none',
    'MECHANICALLY_VALID_RESULT',
    'OPERATIONAL_FAILURE',
    'CODE_DIAGNOSIS_REQUIRED',
    'EXTERNAL_TECHNICAL_BLOCKER',
    'changed_source_commit_execution_mode=fresh',
    'changed_source_commit_run_root=new_independent',
    '`mode=fresh`',
    'new independent run root',
    'Use `$hmasd-review-round` directly in this task',
    'Code Project Manager',
    'Workflow Design Manager'
)
foreach ($required in $operationsRequired) {
    if (-not $operationsNormalized.Contains($required)) { throw "Research Operations Manager contract missing: $required" }
}

$forbiddenCodePm = @(
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'external_review_transport_authority=exclusive',
    'experiment_dispatch_and_result_routing=exclusive'
)
foreach ($forbidden in $forbiddenCodePm) {
    if ($codePm.Contains($forbidden)) { throw "Code Project Manager claims operations authority: $forbidden" }
}
if ($codePm.Contains('Never load `docs/project/CURRENT_WORK.md`')) {
    throw 'Code Project Manager retains the obsolete CURRENT_WORK read prohibition'
}

$forbiddenOperations = @(
    'code_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'git_execution=direct_for_code_tests_and_code_science_index'
)
foreach ($forbidden in $forbiddenOperations) {
    if ($operations.Contains($forbidden)) { throw "Research Operations Manager claims code authority: $forbidden" }
}

if (-not $workflow.Contains('fixed Code Project Manager or Research') -or
    -not $workflow.Contains('Operations Manager session that made the request')) {
    throw 'Workflow Design Manager does not return to either exact requester'
}
if (-not $agileNormalized.Contains('Code Project Manager alone accepts code') -or
    -not $agileNormalized.Contains('Research Operations Manager owns runtime and transport')) {
    throw 'Agile Skill does not preserve code/runtime split'
}
if ($agile.Contains('External Review Operator') -or
    -not $agileNormalized.Contains('returns its exact commit and index to Research Operations Manager') -or
    -not $agileNormalized.Contains('Research Operations Manager routes the one comparison-only')) {
    throw 'Agile Skill retains a stale or ambiguous review route'
}
if ($assertionNormalized.Contains('Research Operations Manager executes the smallest repair') -or
    -not $assertionNormalized.Contains('sends one exact correction assignment to Code Project Manager') -or
    -not $assertionNormalized.Contains('After `CODE_ACCEPTED`')) {
    throw 'Alignment mismatch repair ownership is ambiguous'
}
if (-not $handoff.Contains('Code Project Manager inspects only the G35 diff') -or
    -not $handoff.Contains('and updates the code-science index') -or
    -not $handoff.Contains('docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md') -or
    -not $handoff.Contains('stages exactly the three G35 code/index paths') -or
    -not $handoff.Contains('returns `CODE_ACCEPTED`') -or
    -not $handoff.Contains('Research Operations Manager dispatches exactly one fresh') -or
    $handoff.Contains('Research Operations Manager updates the G35 prelaunch note, code-science index')) {
    throw 'Restart handoff assigns code work to the wrong role'
}
if ($workflow.Contains('Project-Manager workflow-design assignment')) {
    throw 'Workflow Design Manager retains the retired requester identity'
}

foreach ($required in @(
    'Mechanical execution readiness',
    'focused tests alone are insufficient',
    'interface_smoke -> bounded_exercise -> artifact_validation -> artifact_reload -> evaluate_entry -> analyze_entry',
    'Calling a lower-level projection method directly is not a substitute',
    'executes argv arrays without a shell',
    'Git-private receipt',
    'runs no validation command')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill missing execution-readiness rule: $required"
    }
}
if (-not (Test-Path -LiteralPath $readinessScriptPath -PathType Leaf)) {
    throw 'Execution-readiness script is missing'
}
$readinessScript = Get-Content -Raw -LiteralPath $readinessScriptPath
if ($readinessScript.Contains('019f9e4f-f4d0-7fe0-b214-c47fd034e84d') -or
    -not $readinessScript.Contains('code_project_manager_session=')) {
    throw 'Execution-readiness hook duplicates the fixed Code PM session instead of reading the router'
}
if (-not (Test-Path -LiteralPath $hooksPath -PathType Leaf)) {
    throw 'Code acceptance hook configuration is missing'
}
$hooks = Get-Content -Raw -LiteralPath $hooksPath | ConvertFrom-Json
$stopHooks = @($hooks.hooks.Stop)
if ($stopHooks.Count -ne 1 -or
    @($stopHooks[0].hooks).Count -ne 1 -or
    $stopHooks[0].hooks[0].type -ne 'command' -or
    $stopHooks[0].hooks[0].command -notmatch 'hmasd_execution_readiness\.py.*hook-stop' -or
    $stopHooks[0].hooks[0].timeout -ne 10) {
    throw 'Code acceptance Stop hook is not narrow and deterministic'
}
$configuredHookPayload = @{ session_id = 'non-code-pm-hook-command-smoke'; stop_hook_active = $false; last_assistant_message = 'ordinary turn' } | ConvertTo-Json -Compress
Push-Location $repo
try {
    $configuredHookOutput = $configuredHookPayload | & cmd.exe /d /s /c $stopHooks[0].hooks[0].command
    if ($LASTEXITCODE -ne 0 -or $configuredHookOutput) {
        throw 'Configured Stop hook command is not executable from the repository root'
    }
}
finally {
    Pop-Location
}

$registeredPython = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
$unicodePathSegment = ([char]0x6587).ToString() + ([char]0x6863).ToString()
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-readiness-contract-" + $unicodePathSegment + '-' + [guid]::NewGuid().ToString('N'))
$savedOutputEncoding = $OutputEncoding
$OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    & git.exe -C $tempRoot init --quiet
    & git.exe -C $tempRoot config user.email 'workflow-contract@example.invalid'
    & git.exe -C $tempRoot config user.name 'Workflow Contract'
    [IO.File]::WriteAllText((Join-Path $tempRoot 'accepted.py'), "VALUE = 1`n")
    [IO.File]::WriteAllText((Join-Path $tempRoot 'AGENTS.md'), "code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d`n")
    & git.exe -C $tempRoot add accepted.py AGENTS.md
    & git.exe -C $tempRoot commit --quiet -m 'fixture'
    $fixtureCommit = (& git.exe -C $tempRoot rev-parse HEAD).Trim()
    $artifactPath = Join-Path $tempRoot 'exercise/artifact.json'
    $phaseArgv = @($registeredPython, '-c', "from pathlib import Path; p=Path(r'$artifactPath'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text('{}', encoding='utf-8')")
    $phases = [ordered]@{}
    foreach ($phase in @('interface_smoke','bounded_exercise','artifact_validation','artifact_reload','evaluate_entry','analyze_entry')) {
        $phases[$phase] = [ordered]@{ argv = $phaseArgv; timeout_seconds = 10 }
    }
    $spec = [ordered]@{
        schema_version = 1
        source_commit = $fixtureCommit
        trigger = 'contract_fixture'
        exact_paths = @('accepted.py')
        formal = $false
        scientific_iteration_cost = 0
        exercise_root = (Join-Path $tempRoot 'exercise')
        expected_artifacts = @($artifactPath)
        phases = $phases
    }
    $specPath = Join-Path $tempRoot 'readiness-spec.json'
    [IO.File]::WriteAllText($specPath, ($spec | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
    Push-Location $tempRoot
    try {
        $runOutput = & $registeredPython $readinessScriptPath run --spec $specPath
        if ($LASTEXITCODE -ne 0 -or $runOutput -notcontains 'HMASD_EXECUTION_READINESS_OK') {
            throw 'Execution-readiness script did not create a successful fixture receipt'
        }
        $receiptRecord = $runOutput[-1] | ConvertFrom-Json
        $fixtureReceipt = $receiptRecord.receipt
        $checkOutput = & $registeredPython $readinessScriptPath check --commit $fixtureCommit
        if ($LASTEXITCODE -ne 0 -or $checkOutput -notcontains 'HMASD_EXECUTION_READINESS_RECEIPT_OK') {
            throw 'Execution-readiness receipt check failed'
        }

        $validMessage = @"
CODE_ACCEPTED
commit=$fixtureCommit
exact_paths=accepted.py
verification=fixture
execution_readiness=passed
execution_readiness_receipt=$fixtureReceipt
execution_readiness_reason=contract_fixture
code_science_index=not-triggered
blockers=none
"@
        $validHook = @{ session_id = '019f9e4f-f4d0-7fe0-b214-c47fd034e84d'; stop_hook_active = $false; last_assistant_message = $validMessage } | ConvertTo-Json -Compress
        $validHookOutput = $validHook | & $registeredPython $readinessScriptPath hook-stop
        if ($LASTEXITCODE -ne 0 -or $validHookOutput) {
            throw 'Stop hook rejected a matching execution-readiness receipt'
        }

        $otherHook = @{ session_id = 'not-code-pm'; stop_hook_active = $false; last_assistant_message = $validMessage } | ConvertTo-Json -Compress
        $otherHookOutput = $otherHook | & $registeredPython $readinessScriptPath hook-stop
        if ($LASTEXITCODE -ne 0 -or $otherHookOutput) {
            throw 'Stop hook affects a non-Code-PM session'
        }

        $missingMessage = $validMessage -replace $fixtureCommit, ('0' * 40)
        $missingHook = @{ session_id = '019f9e4f-f4d0-7fe0-b214-c47fd034e84d'; stop_hook_active = $false; last_assistant_message = $missingMessage } | ConvertTo-Json -Compress
        $missingHookOutput = ($missingHook | & $registeredPython $readinessScriptPath hook-stop) | ConvertFrom-Json
        if ($missingHookOutput.decision -ne 'block' -or $missingHookOutput.reason -notmatch 'CODE_ACCEPTANCE_BLOCKED') {
            throw 'Stop hook does not request one repair for a missing receipt'
        }
        $activeHook = @{ session_id = '019f9e4f-f4d0-7fe0-b214-c47fd034e84d'; stop_hook_active = $true; last_assistant_message = $missingMessage } | ConvertTo-Json -Compress
        $activeHookOutput = ($activeHook | & $registeredPython $readinessScriptPath hook-stop) | ConvertFrom-Json
        if ($activeHookOutput.continue -ne $false -or $activeHookOutput.stopReason -ne 'invalid_code_acceptance') {
            throw 'Stop hook can create an unbounded continuation loop'
        }

        $notTriggeredMessage = $validMessage -replace 'execution_readiness=passed', 'execution_readiness=not_triggered' -replace 'execution_readiness_reason=contract_fixture', 'execution_readiness_reason=none'
        $notTriggeredHook = @{ session_id = '019f9e4f-f4d0-7fe0-b214-c47fd034e84d'; stop_hook_active = $false; last_assistant_message = $notTriggeredMessage } | ConvertTo-Json -Compress
        $notTriggeredOutput = ($notTriggeredHook | & $registeredPython $readinessScriptPath hook-stop) | ConvertFrom-Json
        if ($notTriggeredOutput.decision -ne 'block') {
            throw 'Stop hook accepts an untriggered readiness state without a bounded reason'
        }

        $savedErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $badSource = $spec | ConvertTo-Json -Depth 8 | ConvertFrom-Json
            $badSource.source_commit = '0' * 40
            $badSource.exercise_root = Join-Path $tempRoot 'bad-source-exercise'
            $badSource.expected_artifacts = @(Join-Path $badSource.exercise_root 'artifact.json')
            $badSourcePath = Join-Path $tempRoot 'bad-source.json'
            [IO.File]::WriteAllText($badSourcePath, ($badSource | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
            $badSourceOutput = & $registeredPython $readinessScriptPath run --spec $badSourcePath 2>&1
            if ($LASTEXITCODE -eq 0 -or ($badSourceOutput -join ' ') -notmatch 'source_commit') {
                throw 'Execution-readiness script accepts a mismatched source commit'
            }

            $badArgv = $spec | ConvertTo-Json -Depth 8 | ConvertFrom-Json
            $badArgv.exercise_root = Join-Path $tempRoot 'bad-argv-exercise'
            $badArgv.expected_artifacts = @(Join-Path $badArgv.exercise_root 'artifact.json')
            $badArgv.phases.interface_smoke.argv = "$registeredPython -c pass"
            $badArgvPath = Join-Path $tempRoot 'bad-argv.json'
            [IO.File]::WriteAllText($badArgvPath, ($badArgv | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
            $badArgvOutput = & $registeredPython $readinessScriptPath run --spec $badArgvPath 2>&1
            if ($LASTEXITCODE -eq 0 -or ($badArgvOutput -join ' ') -notmatch 'argv') {
                throw 'Execution-readiness script accepts a shell command string'
            }

            [IO.File]::AppendAllText((Join-Path $tempRoot 'accepted.py'), "DIRTY = 1`n")
            $dirtySpec = $spec | ConvertTo-Json -Depth 8 | ConvertFrom-Json
            $dirtySpec.exercise_root = Join-Path $tempRoot 'dirty-exercise'
            $dirtySpec.expected_artifacts = @(Join-Path $dirtySpec.exercise_root 'artifact.json')
            $dirtySpecPath = Join-Path $tempRoot 'dirty-spec.json'
            [IO.File]::WriteAllText($dirtySpecPath, ($dirtySpec | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
            $dirtyOutput = & $registeredPython $readinessScriptPath run --spec $dirtySpecPath 2>&1
            if ($LASTEXITCODE -eq 0 -or ($dirtyOutput -join ' ') -notmatch 'uncommitted') {
                throw 'Execution-readiness script accepts dirty implementation paths'
            }
            [IO.File]::WriteAllText((Join-Path $tempRoot 'accepted.py'), "VALUE = 2`n")
            & git.exe -C $tempRoot add accepted.py
            & git.exe -C $tempRoot commit --quiet -m 'failed phase fixture'
            $failedCommit = (& git.exe -C $tempRoot rev-parse HEAD).Trim()
            $failedSpec = $spec | ConvertTo-Json -Depth 8 | ConvertFrom-Json
            $failedSpec.source_commit = $failedCommit
            $failedSpec.exercise_root = Join-Path $tempRoot 'failed-phase-exercise'
            $failedArtifact = Join-Path $failedSpec.exercise_root 'artifact.json'
            $failedSpec.expected_artifacts = @($failedArtifact)
            $failedArgv = @($registeredPython, '-c', "from pathlib import Path; p=Path(r'$failedArtifact'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text('{}', encoding='utf-8')")
            foreach ($phase in @('interface_smoke','bounded_exercise','artifact_validation','artifact_reload','evaluate_entry','analyze_entry')) {
                $failedSpec.phases.$phase.argv = $failedArgv
            }
            $failedSpec.phases.interface_smoke.argv = @($registeredPython, '-c', 'raise SystemExit(7)')
            $failedSpecPath = Join-Path $tempRoot 'failed-phase.json'
            [IO.File]::WriteAllText($failedSpecPath, ($failedSpec | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
            $failedOutput = & $registeredPython $readinessScriptPath run --spec $failedSpecPath 2>&1
            if ($LASTEXITCODE -eq 0 -or ($failedOutput -join ' ') -notmatch 'interface_smoke') {
                throw 'Execution-readiness script does not fail at the first unsuccessful phase'
            }
            $failedCheck = & $registeredPython $readinessScriptPath check --commit $failedCommit 2>&1
            if ($LASTEXITCODE -eq 0 -or ($failedCheck -join ' ') -notmatch 'receipt') {
                throw 'A failed execution-readiness run produced a successful receipt'
            }
        }
        finally {
            $ErrorActionPreference = $savedErrorActionPreference
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ((Test-Path -LiteralPath $tempRoot) -and $tempRoot.StartsWith([IO.Path]::GetTempPath(), [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
    $OutputEncoding = $savedOutputEncoding
}

$parentContracts = @{
    '.agents/roles/CODE_SCOUT.md' = 'parent=code_project_manager'
    '.agents/roles/IMPLEMENTER.md' = 'parent=code_project_manager'
    '.agents/roles/REVIEWER.md' = 'parent=code_project_manager'
    '.agents/roles/VERIFIER.md' = 'parent=code_project_manager'
    '.agents/roles/EXPERIMENT_OPERATOR.md' = 'parent=research_operations_manager'
    '.agents/roles/PRO_RESPONSE_MONITOR.md' = 'parent=research_operations_manager'
}
foreach ($entry in $parentContracts.GetEnumerator()) {
    $text = Get-Content -Raw -LiteralPath (Join-Path $repo $entry.Key)
    if (-not $text.Contains($entry.Value)) {
        throw "Child ownership mismatch: $($entry.Key) requires $($entry.Value)"
    }
}

Write-Output 'HMASD_CODE_PROJECT_MANAGER_CONTRACT_OK'
