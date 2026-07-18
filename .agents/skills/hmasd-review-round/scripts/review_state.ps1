[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "show", "transition", "validate")]
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
    [string]$CompletionReceipt,
    [string]$ArtifactPath,
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
$allowedStates = @("NOT_STARTED", "DISPATCHED", "COMPLETE", "BLOCKED")
$defaultArtifacts = [ordered]@{
    gemini_divergent      = "11_GEMINI_DIVERGENT_RAW.md"
    open_pro              = "21_PRO_OPEN_RAW.md"
    controller_synthesis  = "30_CONTROLLER_SYNTHESIS.md"
    convergent_pro        = "41_PRO_CONVERGENT_RAW.md"
    controller_disposition = "50_DISPOSITION.md"
}

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Missing review state: $statePath"
    }
    return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function Write-State([object]$Document) {
    $Document.updated_at = [DateTimeOffset]::Now.ToString("o")
    $Document | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Resolve-Artifact([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    if ([IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return Join-Path $round $Path
}

function Assert-Review-State([object]$Document) {
    if ($Document.schema_version -ne 1) {
        throw "Unsupported review-state schema: $($Document.schema_version)"
    }
    if ($Document.round_id -ne (Split-Path -Leaf $round)) {
        throw "Round identity mismatch: $($Document.round_id)"
    }

    foreach ($name in $stageOrder) {
        $entry = $Document.stages.$name
        if ($null -eq $entry) {
            throw "Missing stage: $name"
        }
        if ($entry.state -notin $allowedStates) {
            throw "Invalid state for ${name}: $($entry.state)"
        }
        if ($entry.state -eq "DISPATCHED") {
            if ($name -notin $externalStages) {
                throw "Controller stage cannot be DISPATCHED: $name"
            }
            if ([string]::IsNullOrWhiteSpace($entry.route_token) -or
                [string]::IsNullOrWhiteSpace($entry.dispatched_at)) {
                throw "DISPATCHED requires route_token and dispatched_at: $name"
            }
        }
        if ($entry.state -eq "BLOCKED" -and
            [string]::IsNullOrWhiteSpace($entry.blocker)) {
            throw "BLOCKED requires a blocker: $name"
        }
        if ($entry.state -eq "COMPLETE") {
            $artifact = Resolve-Artifact $entry.artifact_path
            if ($null -eq $artifact -or
                -not (Test-Path -LiteralPath $artifact -PathType Leaf) -or
                (Get-Item -LiteralPath $artifact).Length -le 0) {
                throw "COMPLETE requires a nonempty artifact: $name"
            }
            if ($name -in $externalStages -and
                [string]::IsNullOrWhiteSpace($entry.completion_receipt)) {
                throw "External COMPLETE requires completion_receipt: $name"
            }
            if ($name -in $externalStages -and
                $entry.completion_receipt -notmatch '^(exchange|gemini|manual):\S+') {
                throw "Invalid completion_receipt source for ${name}: $($entry.completion_receipt)"
            }
            if ([string]::IsNullOrWhiteSpace($entry.completed_at)) {
                throw "COMPLETE requires completed_at: $name"
            }
        }
    }

    if ($Document.stages.controller_synthesis.state -eq "COMPLETE" -and
        ($Document.stages.gemini_divergent.state -ne "COMPLETE" -or
         $Document.stages.open_pro.state -ne "COMPLETE")) {
        throw "Controller synthesis requires both divergent reviews COMPLETE"
    }
    if ($Document.stages.convergent_pro.state -in @("DISPATCHED", "COMPLETE") -and
        $Document.stages.controller_synthesis.state -ne "COMPLETE") {
        throw "Convergent review requires controller synthesis COMPLETE"
    }
    if ($Document.stages.controller_disposition.state -eq "COMPLETE" -and
        $Document.stages.convergent_pro.state -ne "COMPLETE") {
        throw "Controller disposition requires convergent review COMPLETE"
    }
}

if ($Mode -eq "init") {
    if (Test-Path -LiteralPath $statePath) {
        throw "Review state already exists: $statePath"
    }
    $stages = [ordered]@{}
    foreach ($name in $stageOrder) {
        $stages[$name] = [ordered]@{
            state              = "NOT_STARTED"
            route_token        = $null
            dispatched_at      = $null
            completion_receipt = $null
            completed_at       = $null
            artifact_path      = $defaultArtifacts[$name]
            blocker            = $null
        }
    }
    $document = [ordered]@{
        schema_version = 1
        round_id       = Split-Path -Leaf $round
        updated_at     = [DateTimeOffset]::Now.ToString("o")
        stages         = $stages
    }
    Write-State $document
    Write-Output $statePath
    exit 0
}

$document = Read-State

if ($Mode -eq "transition") {
    if ([string]::IsNullOrWhiteSpace($Stage) -or [string]::IsNullOrWhiteSpace($State)) {
        throw "transition requires -Stage and -State"
    }
    $entry = $document.stages.$Stage
    if ($entry.state -eq "COMPLETE") {
        throw "COMPLETE is immutable: $Stage"
    }
    if ($entry.state -eq "DISPATCHED" -and $State -eq "NOT_STARTED") {
        throw "DISPATCHED may advance only to COMPLETE or BLOCKED: $Stage"
    }
    $entry.state = $State
    if (-not [string]::IsNullOrWhiteSpace($ArtifactPath)) {
        $entry.artifact_path = $ArtifactPath
    }

    switch ($State) {
        "NOT_STARTED" {
            $entry.route_token = $null
            $entry.dispatched_at = $null
            $entry.completion_receipt = $null
            $entry.completed_at = $null
            $entry.blocker = $null
        }
        "DISPATCHED" {
            if ([string]::IsNullOrWhiteSpace($RouteToken)) {
                throw "DISPATCHED requires -RouteToken"
            }
            $entry.route_token = $RouteToken
            $entry.dispatched_at = [DateTimeOffset]::Now.ToString("o")
            $entry.completion_receipt = $null
            $entry.completed_at = $null
            $entry.blocker = $null
        }
        "COMPLETE" {
            if ($Stage -in $externalStages -and
                [string]::IsNullOrWhiteSpace($CompletionReceipt)) {
                throw "External COMPLETE requires -CompletionReceipt"
            }
            if (-not [string]::IsNullOrWhiteSpace($RouteToken)) {
                $entry.route_token = $RouteToken
            }
            $entry.completion_receipt = if ($Stage -in $externalStages) {
                $CompletionReceipt
            } else {
                $null
            }
            $entry.completed_at = [DateTimeOffset]::Now.ToString("o")
            $entry.blocker = $null
        }
        "BLOCKED" {
            if ([string]::IsNullOrWhiteSpace($Blocker)) {
                throw "BLOCKED requires -Blocker"
            }
            if (-not [string]::IsNullOrWhiteSpace($RouteToken)) {
                $entry.route_token = $RouteToken
            }
            $entry.blocker = $Blocker
        }
    }

    Assert-Review-State $document
    Write-State $document
}

Assert-Review-State $document

if ($Mode -eq "show") {
    foreach ($name in $stageOrder) {
        [pscustomobject]@{
            stage = $name
            state = $document.stages.$name.state
            artifact = $document.stages.$name.artifact_path
            blocker = $document.stages.$name.blocker
        }
    }
} else {
    Write-Output "review_state=VALID path=$statePath"
}
