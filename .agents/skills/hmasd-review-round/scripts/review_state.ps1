[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "show", "next", "transition", "resume", "validate")]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$RoundPath,

    [ValidateSet(
        "gemini_divergent",
        "open_pro",
        "evidence_reconciliation",
        "convergent_pro",
        "controller_disposition"
    )]
    [string]$Stage,

    [ValidateSet("NOT_STARTED", "DISPATCHED", "COMPLETE", "BLOCKED")]
    [string]$State,

    [string]$RouteToken,
    [string]$DeadlineAt,
    [string]$Blocker,
    [string]$ResolvedBlocker
)

$ErrorActionPreference = "Stop"

$round = (Resolve-Path -LiteralPath $RoundPath).Path
$statePath = Join-Path $round "05_REVIEW_STATE.json"
$stageOrder = @(
    "gemini_divergent",
    "open_pro",
    "evidence_reconciliation",
    "convergent_pro",
    "controller_disposition"
)
$externalStages = @("gemini_divergent", "open_pro", "convergent_pro")
$roles = @{
    gemini_divergent = "GEMINI_DIVERGENT"
    open_pro = "OPEN_DIVERGENT"
    convergent_pro = "CONVERGENT"
}
$artifacts = [ordered]@{
    gemini_divergent = "11_GEMINI_DIVERGENT_RAW.md"
    open_pro = "21_PRO_OPEN_RAW.md"
    evidence_reconciliation = "30_EVIDENCE_RECONCILIATION.md"
    convergent_pro = "41_PRO_CONVERGENT_RAW.md"
    controller_disposition = "50_DISPOSITION.md"
}

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Missing review state: $statePath"
    }
    Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function Write-State([object]$Document) {
    $Document.updated_at = [DateTimeOffset]::Now.ToString("o")
    $Document | ConvertTo-Json -Depth 6 |
        Set-Content -LiteralPath $statePath -Encoding utf8NoBOM
}

function Resolve-Artifact([string]$Name) {
    $path = [IO.Path]::GetFullPath((Join-Path $round $Name))
    if (-not $path.StartsWith(
        $round + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Artifact escapes round directory: $Name"
    }
    $path
}

function Parse-Time([string]$Value, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "$Label is required"
    }
    try {
        [DateTimeOffset]::Parse(
            $Value,
            [Globalization.CultureInfo]::InvariantCulture
        )
    } catch {
        throw "Invalid $Label timestamp: $Value"
    }
}

function Assert-Route([string]$StageName, [object]$Entry) {
    $roundId = [regex]::Escape((Split-Path -Leaf $round))
    $role = [regex]::Escape([string]$roles[$StageName])
    $relative = "docs/external-review/rounds/$(Split-Path -Leaf $round)/$($Entry.artifact_path)"
    $artifact = [regex]::Escape($relative)
    if ($Entry.route_token -notmatch "^${roundId}:${role}:[0-9a-fA-F]{40}:${artifact}$") {
        throw "Invalid route token for ${StageName}: $($Entry.route_token)"
    }
}

function Assert-State([object]$Document) {
    if ($Document.schema_version -ne 5 -or
        $Document.round_id -ne (Split-Path -Leaf $round)) {
        throw "Review state identity or schema mismatch"
    }
    if ($Document.round_status -notin @("ACTIVE", "CLOSED")) {
        throw "Invalid round status: $($Document.round_status)"
    }

    foreach ($name in $stageOrder) {
        $entry = $Document.stages.$name
        if ($null -eq $entry -or
            $entry.state -notin @("NOT_STARTED", "DISPATCHED", "COMPLETE", "BLOCKED")) {
            throw "Invalid stage state: $name"
        }
        if ($entry.artifact_path -ne $artifacts[$name]) {
            throw "Artifact path changed for $name"
        }
        if ($entry.dispatch_count -notin @(0, 1)) {
            throw "dispatch_count must be 0 or 1: $name"
        }
        if ($entry.state -eq "BLOCKED" -and
            [string]::IsNullOrWhiteSpace($entry.blocker)) {
            throw "BLOCKED requires a reason: $name"
        }

        if ($name -in $externalStages) {
            if ($entry.dispatch_count -eq 0) {
                if ($entry.state -in @("DISPATCHED", "COMPLETE") -or
                    -not [string]::IsNullOrWhiteSpace($entry.route_token) -or
                    -not [string]::IsNullOrWhiteSpace($entry.dispatched_at) -or
                    -not [string]::IsNullOrWhiteSpace($entry.deadline_at)) {
                    throw "Undispatched external stage has dispatch evidence: $name"
                }
            } else {
                if ($entry.state -eq "NOT_STARTED") {
                    throw "Dispatched external stage returned to NOT_STARTED: $name"
                }
                Assert-Route $name $entry
                $dispatched = Parse-Time ([string]$entry.dispatched_at) "$name dispatched_at"
                $deadline = Parse-Time ([string]$entry.deadline_at) "$name deadline_at"
                if ($deadline -le $dispatched) {
                    throw "deadline_at must follow dispatched_at: $name"
                }
            }
        } elseif ($entry.dispatch_count -ne 0 -or
                  -not [string]::IsNullOrWhiteSpace($entry.route_token) -or
                  -not [string]::IsNullOrWhiteSpace($entry.dispatched_at) -or
                  -not [string]::IsNullOrWhiteSpace($entry.deadline_at)) {
            throw "Internal stage contains dispatch evidence: $name"
        }

        if ($entry.state -eq "COMPLETE") {
            $artifact = Resolve-Artifact $entry.artifact_path
            if (-not (Test-Path -LiteralPath $artifact -PathType Leaf) -or
                (Get-Item -LiteralPath $artifact).Length -le 0) {
                throw "COMPLETE requires a nonempty artifact: $name"
            }
        }
    }

    if (@($externalStages | Where-Object {
        $Document.stages.$_.state -eq "DISPATCHED"
    }).Count -gt 1) {
        throw "External transport must remain serialized"
    }
    if ($Document.stages.open_pro.state -ne "NOT_STARTED" -and
        $Document.stages.gemini_divergent.state -ne "COMPLETE") {
        throw "Open Pro requires completed Gemini raw"
    }
    if ($Document.stages.evidence_reconciliation.state -ne "NOT_STARTED" -and
        ($Document.stages.gemini_divergent.state -ne "COMPLETE" -or
         $Document.stages.open_pro.state -ne "COMPLETE")) {
        throw "Evidence reconciliation requires both divergent raws"
    }
    if ($Document.stages.convergent_pro.state -ne "NOT_STARTED" -and
        $Document.stages.evidence_reconciliation.state -ne "COMPLETE") {
        throw "Convergent Pro requires evidence reconciliation"
    }
    if ($Document.stages.controller_disposition.state -ne "NOT_STARTED" -and
        $Document.stages.convergent_pro.state -ne "COMPLETE") {
        throw "Disposition requires convergent raw"
    }
    if (($Document.round_status -eq "CLOSED") -ne
        ($Document.stages.controller_disposition.state -eq "COMPLETE")) {
        throw "Round closure and disposition disagree"
    }
}

function Get-Next([object]$Document) {
    if ($Document.round_status -eq "CLOSED") { return "CLOSED" }
    $waiting = @($externalStages | Where-Object {
        $Document.stages.$_.state -eq "DISPATCHED"
    })
    if ($waiting.Count -eq 1) { return "WAIT:$($waiting[0])" }
    $blocked = @($stageOrder | Where-Object {
        $Document.stages.$_.state -eq "BLOCKED"
    })
    if ($blocked.Count -gt 0) { return "BLOCKED:$($blocked -join ',')" }
    foreach ($name in $stageOrder) {
        if ($Document.stages.$name.state -eq "NOT_STARTED") {
            return "NEXT:$name"
        }
    }
    "NO_ELIGIBLE_STAGE"
}

if ($Mode -eq "init") {
    if (Test-Path -LiteralPath $statePath) {
        throw "Review state already exists: $statePath"
    }
    $stages = [ordered]@{}
    foreach ($name in $stageOrder) {
        $stages[$name] = [ordered]@{
            state = "NOT_STARTED"
            dispatch_count = 0
            route_token = $null
            dispatched_at = $null
            deadline_at = $null
            artifact_path = $artifacts[$name]
            blocker = $null
        }
    }
    $document = [ordered]@{
        schema_version = 5
        round_id = Split-Path -Leaf $round
        round_status = "ACTIVE"
        updated_at = [DateTimeOffset]::Now.ToString("o")
        stages = $stages
    }
    Write-State $document
} else {
    $document = Read-State
}

if ($Mode -eq "transition") {
    if ([string]::IsNullOrWhiteSpace($Stage) -or
        [string]::IsNullOrWhiteSpace($State)) {
        throw "transition requires -Stage and -State"
    }
    if ($document.round_status -ne "ACTIVE") {
        throw "Closed review rounds are immutable"
    }
    $entry = $document.stages.$Stage
    if ($entry.state -in @("COMPLETE", "BLOCKED")) {
        throw "Terminal stage is immutable: $Stage"
    }

    $external = $Stage -in $externalStages
    if ($State -eq "DISPATCHED") {
        if (-not $external -or $entry.state -ne "NOT_STARTED") {
            throw "Only an unstarted external stage may be dispatched"
        }
        if ([string]::IsNullOrWhiteSpace($RouteToken) -or
            [string]::IsNullOrWhiteSpace($DeadlineAt)) {
            throw "DISPATCHED requires -RouteToken and -DeadlineAt"
        }
        $now = [DateTimeOffset]::Now
        $deadline = Parse-Time $DeadlineAt "DeadlineAt"
        if ($deadline -le $now) { throw "DeadlineAt must be in the future" }
        $entry.state = "DISPATCHED"
        $entry.dispatch_count = 1
        $entry.route_token = $RouteToken
        $entry.dispatched_at = $now.ToString("o")
        $entry.deadline_at = $deadline.ToString("o")
        $entry.blocker = $null
    } elseif ($State -eq "COMPLETE") {
        if ($external -and $entry.state -ne "DISPATCHED") {
            throw "External COMPLETE requires prior DISPATCHED"
        }
        if (-not $external -and $entry.state -ne "NOT_STARTED") {
            throw "Internal COMPLETE requires NOT_STARTED"
        }
        $entry.state = "COMPLETE"
        $entry.blocker = $null
        if ($Stage -eq "controller_disposition") {
            $document.round_status = "CLOSED"
        }
    } elseif ($State -eq "BLOCKED") {
        if ([string]::IsNullOrWhiteSpace($Blocker)) {
            throw "BLOCKED requires -Blocker"
        }
        $entry.state = "BLOCKED"
        $entry.blocker = $Blocker
    } else {
        throw "Invalid transition target: $State"
    }
    Assert-State $document
    Write-State $document
}

if ($Mode -eq "resume") {
    if ([string]::IsNullOrWhiteSpace($Stage) -or
        [string]::IsNullOrWhiteSpace($ResolvedBlocker)) {
        throw "resume requires -Stage and -ResolvedBlocker"
    }
    if ($document.round_status -ne "ACTIVE") {
        throw "Closed review rounds are immutable"
    }
    $entry = $document.stages.$Stage
    if ($entry.state -ne "BLOCKED") {
        throw "Only a BLOCKED stage may resume: $Stage"
    }
    if (-not [string]::Equals(
        [string]$entry.blocker,
        $ResolvedBlocker,
        [StringComparison]::Ordinal
    )) {
        throw "Resolved blocker does not match recorded blocker: $Stage"
    }
    if ($entry.dispatch_count -ne 0 -or
        -not [string]::IsNullOrWhiteSpace($entry.route_token) -or
        -not [string]::IsNullOrWhiteSpace($entry.dispatched_at) -or
        -not [string]::IsNullOrWhiteSpace($entry.deadline_at)) {
        throw "A dispatched or accepted external stage cannot resume: $Stage"
    }

    $stageIndex = [Array]::IndexOf($stageOrder, $Stage)
    if ($stageIndex -gt 0) {
        foreach ($prior in $stageOrder[0..($stageIndex - 1)]) {
            if ($document.stages.$prior.state -ne "COMPLETE") {
                throw "Cannot resume $Stage before completed prior stage: $prior"
            }
        }
    }

    $entry.state = "NOT_STARTED"
    $entry.route_token = $null
    $entry.dispatched_at = $null
    $entry.deadline_at = $null
    $entry.blocker = $null
    Assert-State $document
    Write-State $document
}

Assert-State $document

if ($Mode -eq "show") {
    Write-Output "round_status=$($document.round_status) next=$(Get-Next $document)"
    foreach ($name in $stageOrder) {
        [pscustomobject]@{
            stage = $name
            state = $document.stages.$name.state
            dispatch_count = $document.stages.$name.dispatch_count
            artifact = $document.stages.$name.artifact_path
            deadline = $document.stages.$name.deadline_at
            blocker = $document.stages.$name.blocker
        }
    }
} elseif ($Mode -eq "next") {
    Write-Output (Get-Next $document)
} else {
    Write-Output "review_state=VALID path=$statePath"
}
