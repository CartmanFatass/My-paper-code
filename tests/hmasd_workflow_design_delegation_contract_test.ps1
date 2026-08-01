[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-RepoFile([string]$Path) {
    Get-Content -Raw -LiteralPath (Join-Path $repo $Path)
}

$config = Read-RepoFile '.codex/config.toml'
$manager = Read-RepoFile '.agents/roles/WORKFLOW_DESIGN_MANAGER.md'
$skill = Read-RepoFile '.agents/skills/hmasd-workflow-change-audit/SKILL.md'

$profiles = @(
    @{
        Path = '.codex/agents/hmasd-workflow-auditor.toml'
        Role = '.agents/roles/WORKFLOW_AUDITOR.md'
        Name = 'hmasd-workflow-auditor'
        Registry = '[agents."HMASDWorkflowAuditor"]'
        Model = 'model = "gpt-5.6-luna"'
        Effort = 'model_reasoning_effort = "high"'
        Sandbox = 'sandbox_mode = "read-only"'
        Packet = 'WORKFLOW_IMPACT_PACKET'
    },
    @{
        Path = '.codex/agents/hmasd-workflow-implementer.toml'
        Role = '.agents/roles/WORKFLOW_IMPLEMENTER.md'
        Name = 'hmasd-workflow-implementer'
        Registry = '[agents."HMASDWorkflowImplementer"]'
        Model = 'model = "gpt-5.6-luna"'
        Effort = 'model_reasoning_effort = "high"'
        Sandbox = 'sandbox_mode = "workspace-write"'
        Packet = 'WORKFLOW_CHANGE_PACKET'
    },
    @{
        Path = '.codex/agents/hmasd-workflow-reviewer.toml'
        Role = '.agents/roles/WORKFLOW_REVIEWER.md'
        Name = 'hmasd-workflow-reviewer'
        Registry = '[agents."HMASDWorkflowReviewer"]'
        Model = 'model = "gpt-5.6-sol"'
        Effort = 'model_reasoning_effort = "xhigh"'
        Sandbox = 'sandbox_mode = "read-only"'
        Packet = 'WORKFLOW_REVIEW_PACKET'
    },
    @{
        Path = '.codex/agents/hmasd-workflow-cost-reviewer.toml'
        Role = '.agents/roles/WORKFLOW_COST_REVIEWER.md'
        Name = 'hmasd-workflow-cost-reviewer'
        Registry = '[agents."HMASDWorkflowCostReviewer"]'
        Model = 'model = "gpt-5.6-sol"'
        Effort = 'model_reasoning_effort = "xhigh"'
        Sandbox = 'sandbox_mode = "read-only"'
        Packet = 'COST_AUDIT_ACCEPT'
    })

foreach ($entry in $profiles) {
    $profile = Read-RepoFile $entry.Path
    $role = Read-RepoFile $entry.Role
    foreach ($required in @(
        "name = `"$($entry.Name)`"",
        $entry.Model,
        $entry.Effort,
        $entry.Sandbox,
        $entry.Role,
        $entry.Packet)) {
        if (-not $profile.Contains($required)) {
            throw "$($entry.Name) profile missing: $required"
        }
    }
    foreach ($required in @(
        "callable_agent_type=$($entry.Name)",
        'parent=assigning_persistent_session',
        'assignment_identity=session_owner_role|session_owner_id|owned_paths|session_workspace',
        'acceptance_authority=none',
        'child_authority=none',
        'current_work_read=forbidden',
        $entry.Packet)) {
        if (-not $role.Contains($required)) {
            throw "$($entry.Name) role missing: $required"
        }
    }
    if (-not $config.Contains($entry.Registry) -or
        -not $config.Contains("config_file = `"./agents/$($entry.Name).toml`"")) {
        throw "$($entry.Name) is not registered exactly by path"
    }
}

$auditorRole = Read-RepoFile '.agents/roles/WORKFLOW_AUDITOR.md'
foreach ($required in @(
    'assignment_modes=impact_map|postchange_verify',
    'workflow_design_authority=none',
    'write_authority=none',
    'git_authority=none',
    'Do not choose authority',
    'Do not repair a failure')) {
    if (-not $auditorRole.Contains($required)) {
        throw "Workflow Auditor boundary missing: $required"
    }
}

$implementerRole = Read-RepoFile '.agents/roles/WORKFLOW_IMPLEMENTER.md'
foreach ($required in @(
    'authority=one_exact_confirmed_workflow_plan_slice',
    'write_authority=assignment_exact_nonoverlapping_paths_only',
    'git_authority=none',
    'Do not choose or change',
    'missing decision',
    'returns `BLOCKED`')) {
    if (-not $implementerRole.Contains($required)) {
        throw "Workflow Implementer boundary missing: $required"
    }
}

$reviewerRole = Read-RepoFile '.agents/roles/WORKFLOW_REVIEWER.md'
foreach ($required in @(
    'authority=one_exact_read_only_integrated_workflow_review',
    'write_authority=none',
    'git_authority=none',
    'Review only when the assigning persistent session names a risk trigger',
    'ACCEPTABLE',
    'REVISION_REQUIRED',
    'are advisory dispositions')) {
    if (-not $reviewerRole.Contains($required)) {
        throw "Workflow Reviewer boundary missing: $required"
    }
}

if (($config | Select-String -Pattern 'config_file = "./agents/hmasd-workflow-auditor.toml"' -AllMatches).Matches.Count -ne 1 -or
    ($config | Select-String -Pattern 'config_file = "./agents/hmasd-workflow-implementer.toml"' -AllMatches).Matches.Count -ne 1 -or
    ($config | Select-String -Pattern 'config_file = "./agents/hmasd-workflow-reviewer.toml"' -AllMatches).Matches.Count -ne 1 -or
    ($config | Select-String -Pattern 'config_file = "./agents/hmasd-workflow-cost-reviewer.toml"' -AllMatches).Matches.Count -ne 1) {
    throw 'A workflow child profile is not registered exactly once'
}

foreach ($required in @(
    'workflow_design_authority=exclusive_for_shared_control_plane_surfaces',
    'workflow_design_acceptance_authority=exclusive_for_shared_control_plane_surfaces',
    'session_owner_role=workflow_design_manager',
    'Shared workflow procedure',
    'single source',
    'shared-surface ownership and prohibitions',
    'exact registered persistent session that',
    'A direct user request returns in this task')) {
    if (-not $manager.Contains($required)) {
        throw "Workflow Design Manager delegation contract missing: $required"
    }
}
if ($manager.Contains('fixed Code Project Manager session')) {
    throw 'Workflow Design Manager retains a CPM-only return route'
}

foreach ($required in @(
    'two or three registered `hmasd-workflow-auditor`',
    'one or two registered',
    '`hmasd-workflow-implementer`',
    'exact nonoverlapping path slices',
    '`WORKFLOW_CHANGE_PACKET`',
    '`WORKFLOW_VERIFY_PACKET`',
    '`hmasd-workflow-reviewer` only when',
    'Ordinary low-risk documentation edits need no reviewer',
    'assigning session still reads the final diff',
    'workflow_child_parent=assigning_persistent_session',
    'workflow_child_assignment_fields=session_owner_role|session_owner_id|owned_paths|session_workspace',
    'workflow_child_acceptance_authority=none',
    'Six paths is a useful dispatch heuristic',
    'exact nonoverlapping path slices',
    'Do not delegate user collaboration',
    'authority or ownership decisions',
    'ambiguous cross-surface semantics, conflict',
    'resolution, final acceptance, Git integration or cross-task routing',
    'is no review of the review')) {
    if (-not $skill.Contains($required)) {
        throw "Workflow change audit delegation contract missing: $required"
    }
}

$legacyVerifier = Read-RepoFile '.agents/roles/VERIFIER.md'
$legacyReviewer = Read-RepoFile '.agents/roles/REVIEWER.md'
if (-not $legacyVerifier.Contains('parent=code_project_manager') -or
    -not $legacyReviewer.Contains('parent=code_project_manager')) {
    throw 'Existing code-side verifier or reviewer ownership drifted'
}
if ($manager.Contains('hmasd-verifier') -or $manager.Contains('`hmasd-reviewer`')) {
    throw 'Workflow Design Manager reuses a code-side child for workflow work'
}
if (-not $config.Contains('max_depth = 1')) {
    throw 'Workflow children are not prevented from spawning descendants'
}

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
