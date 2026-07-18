[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "show", "next", "transition", "validate")]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$RoundPath,

    [ValidateSet(
        "gemini_divergent",
        "open_pro",
        "controller_synthesis",
        "convergent_pro",
        "controller_disposition"
    )]
    [string]$Stage,

    [ValidateSet("NOT_STARTED", "DISPATCHED", "COMPLETE", "BLOCKED")]
    [string]$State,

    [string]$RouteToken,
    [string]$Blocker
)

$ErrorActionPreference = "Stop"

$round = (Resolve-Path -LiteralPath $RoundPath).Path
$statePath = Join-Path $round "05_REVIEW_STATE.json"
$stageOrder = @(
    "gemini_divergent",
    "open_pro",
    "controller_synthesis",
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
    controller_synthesis = "30_CONTROLLER_SYNTHESIS.md"
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
    $Document | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statePath -Encoding utf8NoBOM
}

function Resolve-Artifact([string]$Name) {
    $path = [IO.Path]::GetFullPath((Join-Path $round $Name))
    if (-not $path.StartsWith($round + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact escapes round directory: $Name"
    }
    $path
}

function Assert-Route([string]$StageName, [object]$Entry) {
    $roundId = [regex]::Escape((Split-Path -Leaf $round))
    $role = [regex]::Escape([string]$roles[$StageName])
    $artifact = [regex]::Escape(("docs/external-review/rounds/" + (Split-Path -Leaf $round) + "/" + $Entry.artifact_path))
    if ($Entry.route_token -notmatch "^${roundId}:${role}:[0-9a-fA-F]{40}:${artifact}$") {
        throw "Invalid route token for ${StageName}: $($Entry.route_token)"
    }
}

function Get-Next([object]$Document) {
    if ($Document.round_status -eq "CLOSED") {
        return "CLOSED"
    }
    $running = @($externalStages | Where-Object { $Document.stages.$_.state -eq "DISPATCHED" })
    if ($running.Count -gt 0) {
        return "WAIT:$($running[0])"
    }
    foreach ($name in @("gemini_divergent", "open_pro")) {
        if ($Document.stages.$name.state -eq "NOT_STARTED") {
            return "NEXT:$name"
        }
    }
    if ($Document.stages.gemini_divergent.state -eq "COMPLETE" -and
        $Document.stages.open_pro.state -eq "COMPLETE" -and
        $Document.stages.controller_synthesis.state -eq "NOT_STARTED") {
        return "NEXT:controller_synthesis"
    }
    if ($Document.stages.controller_synthesis.state -eq "COMPLETE" -and
        $Document.stages.convergent_pro.state -eq "NOT_STARTED") {
        return "NEXT:convergent_pro"
    }
    if ($Document.stages.convergent_pro.state -eq "COMPLETE" -and
        $Document.stages.controller_disposition.state -eq "NOT_STARTED") {
        return "NEXT:controller_disposition"
    }
    $blocked = @($stageOrder | Where-Object { $Document.stages.$_.state -eq "BLOCKED" })
    if ($blocked.Count -gt 0) {
        return "BLOCKED:$($blocked -join ',')"
    }
    "NO_ELIGIBLE_STAGE"
}

function Assert-State([object]$Document) {
    if ($Document.schema_version -ne 3 -or $Document.round_id -ne (Split-Path -Leaf $round)) {
        throw "Review state identity or schema mismatch"
    }
    if ($Document.round_status -notin @("ACTIVE", "CLOSED")) {
        throw "Invalid round status: $($Document.round_status)"
    }
    foreach ($name in $stageOrder) {
        $entry = $Document.stages.$name
        if ($null -eq $entry -or $entry.state -notin @("NOT_STARTED", "DISPATCHED", "COMPLETE", "BLOCKED")) {
            throw "Invalid stage state: $name"
        }
        if ($entry.artifact_path -ne $artifacts[$name]) {
            throw "Artifact path changed for $name"
        }
        if ($entry.state -eq "BLOCKED" -and [string]::IsNullOrWhiteSpace($entry.blocker)) {
            throw "BLOCKED requires a reason: $name"
        }
        if ($name -in $externalStages -and $entry.state -in @("DISPATCHED", "COMPLETE")) {
            Assert-Route $name $entry
        }
        if ($entry.state -eq "COMPLETE") {
            $artifact = Resolve-Artifact $entry.artifact_path
            if (-not (Test-Path -LiteralPath $artifact -PathType Leaf) -or
                (Get-Item -LiteralPath $artifact).Length -le 0) {
                throw "COMPLETE requires a nonempty artifact: $name"
            }
        }
    }

    $running = @($externalStages | Where-Object { $Document.stages.$_.state -eq "DISPATCHED" })
    if ($running.Count -gt 1) {
        throw "External transport must remain serialized"
    }
    if ($Document.stages.controller_synthesis.state -eq "COMPLETE" -and
        ($Document.stages.gemini_divergent.state -ne "COMPLETE" -or
         $Document.stages.open_pro.state -ne "COMPLETE")) {
        throw "Controller synthesis requires both divergent raws"
    }
    if ($Document.stages.convergent_pro.state -ne "NOT_STARTED" -and
        $Document.stages.controller_synthesis.state -ne "COMPLETE") {
        throw "Convergent Pro requires controller synthesis"
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

if ($Mode -eq "init") {
    if (Test-Path -LiteralPath $statePath) {
        throw "Review state already exists: $statePath"
    }
    $stages = [ordered]@{}
    foreach ($name in $stageOrder) {
        $stages[$name] = [ordered]@{
            state = "NOT_STARTED"
            route_token = $null
            artifact_path = $artifacts[$name]
            blocker = $null
        }
    }
    $document = [ordered]@{
        schema_version = 3
        round_id = Split-Path -Leaf $round
        round_status = "ACTIVE"
        updated_at = [DateTimeOffset]::Now.ToString("o")
        stages = $stages
    }
    Write-State $document
    Write-Output "review_state=INITIALIZED path=$statePath"
    exit 0
}

$document = Read-State

if ($Mode -eq "transition") {
    if ([string]::IsNullOrWhiteSpace($Stage) -or [string]::IsNullOrWhiteSpace($State)) {
        throw "transition requires -Stage and -State"
    }
    if ($document.round_status -ne "ACTIVE") {
        throw "Closed review rounds are immutable"
    }
    $entry = $document.stages.$Stage
    if ($entry.state -eq "COMPLETE") {
        throw "COMPLETE is immutable: $Stage"
    }
    $external = $Stage -in $externalStages
    $allowed = if ($external) {
        switch ($entry.state) {
            "NOT_STARTED" { @("DISPATCHED", "BLOCKED") }
            "DISPATCHED" { @("COMPLETE", "BLOCKED") }
            "BLOCKED" { @("DISPATCHED", "BLOCKED") }
        }
    } else {
        switch ($entry.state) {
            "NOT_STARTED" { @("COMPLETE", "BLOCKED") }
            "BLOCKED" { @("COMPLETE", "BLOCKED") }
        }
    }
    if ($State -notin $allowed) {
        throw "Invalid transition: $Stage $($entry.state) -> $State"
    }

    if ($State -eq "DISPATCHED") {
        if ([string]::IsNullOrWhiteSpace($RouteToken)) {
            throw "DISPATCHED requires -RouteToken"
        }
        $entry.route_token = $RouteToken
        $entry.blocker = $null
    } elseif ($State -eq "COMPLETE") {
        if ($external) {
            if ([string]::IsNullOrWhiteSpace($entry.route_token)) {
                throw "External COMPLETE requires a prior DISPATCHED route"
            }
            if (-not [string]::IsNullOrWhiteSpace($RouteToken) -and $RouteToken -ne $entry.route_token) {
                throw "COMPLETE cannot change the route"
            }
        }
        $entry.blocker = $null
        if ($Stage -eq "controller_disposition") {
            $document.round_status = "CLOSED"
        }
    } else {
        if ([string]::IsNullOrWhiteSpace($Blocker)) {
            throw "BLOCKED requires -Blocker"
        }
        $entry.blocker = $Blocker
    }
    $entry.state = $State
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
            artifact = $document.stages.$name.artifact_path
            blocker = $document.stages.$name.blocker
        }
    }
} elseif ($Mode -eq "next") {
    Write-Output (Get-Next $document)
} else {
    Write-Output "review_state=VALID path=$statePath"
}
