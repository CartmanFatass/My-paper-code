[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "migrate", "show", "next", "transition", "consent", "round", "validate")]
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
    [string]$DispatchReceipt,
    [string]$CompletionReceipt,
    [string]$ArtifactPath,
    [string]$Blocker,
    [string]$ResolutionReceipt,
    [ValidateSet("ACTIVE", "SUSPENDED", "CLOSED")]
    [string]$RoundStatus,
    [ValidateSet("NOT_REQUIRED", "PENDING", "APPROVED", "REVOKED")]
    [string]$ConsentState,
    [string]$ConsentManifestPath,
    [string]$ConsentManifestCommit,
    [string]$ConsentDestination,
    [string]$ConsentApprovalReceipt
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
$allowedRoundStatuses = @("ACTIVE", "SUSPENDED", "CLOSED")
$expectedRoles = @{
    gemini_divergent = "GEMINI_DIVERGENT"
    open_pro = "OPEN_DIVERGENT"
    convergent_pro = "CONVERGENT"
}
$exchangeTurnReferencePattern = '^turn:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(#item-[A-Za-z0-9._-]+)?$'
$repoRoot = (git -C $round rev-parse --show-toplevel).Trim()
$reviewerRegistryPath = Join-Path $repoRoot "docs/external-review/REVIEWER_CONVERSATIONS.json"
$defaultArtifacts = [ordered]@{
    gemini_divergent      = "11_GEMINI_DIVERGENT_RAW.md"
    open_pro              = "21_PRO_OPEN_RAW.md"
    controller_synthesis  = "30_CONTROLLER_SYNTHESIS.md"
    convergent_pro        = "41_PRO_CONVERGENT_RAW.md"
    controller_disposition = "50_DISPOSITION.md"
}
$localManifestName = "02_GEMINI_LOCAL_SOURCE_MANIFEST.md"
$registeredConsentManifest = (Join-Path ("docs/external-review/rounds/" + (Split-Path -Leaf $round)) $localManifestName).Replace("\", "/")

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Missing review state: $statePath"
    }
    return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -DateKind String
}

function Write-State([object]$Document) {
    $Document.updated_at = [DateTimeOffset]::Now.ToString("o")
    $Document | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Resolve-Artifact([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    $resolved = if ([IO.Path]::IsPathRooted($Path)) {
        [IO.Path]::GetFullPath($Path)
    } else {
        [IO.Path]::GetFullPath((Join-Path $round $Path))
    }
    if (-not $resolved.StartsWith($round + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact path escapes round directory: $Path"
    }
    return $resolved
}

function Assert-ArtifactIdentity([string]$StageName, [string]$Path) {
    $actual = Resolve-Artifact $Path
    $expected = Resolve-Artifact ([string]$defaultArtifacts[$StageName])
    if ($null -eq $actual -or
        -not [string]::Equals($actual, $expected, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact path for $StageName must remain $($defaultArtifacts[$StageName])"
    }
    return $expected
}

function Assert-RouteToken([string]$StageName, [object]$Entry) {
    $roundId = [regex]::Escape((Split-Path -Leaf $round))
    $role = [regex]::Escape([string]$expectedRoles[$StageName])
    $repositoryPath = [regex]::Escape(("docs/external-review/rounds/" + (Split-Path -Leaf $round) + "/" + [string]$Entry.artifact_path).Replace("\", "/"))
    if ($Entry.route_token -notmatch "^${roundId}:${role}:[0-9a-fA-F]{40}:${repositoryPath}$") {
        throw "Invalid route_token for ${StageName}: $($Entry.route_token)"
    }
}

function Parse-Receipt([string]$Receipt) {
    if ([string]::IsNullOrWhiteSpace($Receipt)) {
        return $null
    }
    $parsed = @{}
    foreach ($part in $Receipt.Split(";")) {
        $pair = $part.Split("=", 2)
        if ($pair.Count -ne 2 -or [string]::IsNullOrWhiteSpace($pair[0]) -or
            [string]::IsNullOrWhiteSpace($pair[1]) -or $parsed.ContainsKey($pair[0])) {
            throw "Malformed transport receipt"
        }
        $parsed[$pair[0]] = $pair[1]
    }
    $required = @("source", "session", "conversation", "role", "model", "route", "terminal", "reference")
    if ($parsed.Keys.Count -ne $required.Count -or
        @($required | Where-Object { -not $parsed.ContainsKey($_) }).Count -ne 0) {
        throw "Transport receipt must contain exactly: $($required -join ', ')"
    }
    return $parsed
}

function Assert-Consent([object]$Consent) {
    if ($null -eq $Consent -or $Consent.state -notin @("NOT_REQUIRED", "PENDING", "APPROVED", "REVOKED")) {
        throw "Invalid external_source_consent"
    }
    $localManifestExists = Test-Path -LiteralPath (Join-Path $round $localManifestName) -PathType Leaf
    if ($localManifestExists) {
        if ($Consent.state -eq "NOT_REQUIRED" -or
            ([string]$Consent.manifest_path).Replace("\", "/") -ne $registeredConsentManifest) {
            throw "Local-source consent must retain the registered manifest path"
        }
    } elseif ($Consent.state -ne "NOT_REQUIRED") {
        throw "Consent cannot be pending, approved or revoked without the registered local-source manifest"
    }
    if ($Consent.state -eq "APPROVED") {
        if ([string]::IsNullOrWhiteSpace($Consent.manifest_path) -or
            [IO.Path]::IsPathRooted([string]$Consent.manifest_path) -or
            ([string]$Consent.manifest_path).Split('/') -contains '..' -or
            $Consent.manifest_commit -notmatch '^[0-9a-fA-F]{40}$' -or
            [string]::IsNullOrWhiteSpace($Consent.destination) -or
            $Consent.approval_receipt -notmatch '^user:[^:;]+:[^:;]+$' -or
            [string]::IsNullOrWhiteSpace($Consent.approved_at)) {
            throw "APPROVED consent requires manifest path/commit, destination, user receipt and approved_at"
        }
        git -C $repoRoot cat-file -e "$($Consent.manifest_commit):$($Consent.manifest_path)" 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Consent manifest is absent at its approved commit"
        }
        git -C $repoRoot diff --quiet $Consent.manifest_commit -- $Consent.manifest_path
        if ($LASTEXITCODE -ne 0) {
            throw "Consent invalidated because the allowlist differs from its approved commit"
        }
    }
}

function Assert-TransportReceipt(
    [string]$StageName,
    [object]$Entry,
    [string]$ReceiptText,
    [string]$ExpectedTerminal,
    [bool]$AllowManual
) {
    $receipt = Parse-Receipt $ReceiptText
    if ($null -eq $receipt) {
        throw "External $ExpectedTerminal requires a transport receipt: $StageName"
    }
    if ($receipt.source -notin @("chatgpt_control", "exchange", "gemini", "manual") -or
        $receipt.role -ne $expectedRoles[$StageName] -or
        $receipt.route -ne $Entry.route_token -or
        $receipt.terminal -ne $ExpectedTerminal) {
        throw "$ExpectedTerminal receipt identity mismatch: $StageName"
    }
    if ($receipt.source -eq "manual" -and -not $AllowManual) {
        throw "DISPATCHED cannot use a manual receipt"
    }
    if ($StageName -eq "gemini_divergent" -and $receipt.source -notin @("exchange", "gemini", "manual")) {
        throw "Gemini stage requires exchange, gemini, or manual receipt"
    }
    if ($StageName -in @("open_pro", "convergent_pro") -and
        $receipt.source -notin @("chatgpt_control", "exchange", "manual")) {
        throw "Pro stage requires ChatGPT-control, legacy exchange, or manual receipt"
    }
    if ($receipt.source -eq "manual") {
        if ($receipt.session -ne "manual" -or $receipt.conversation -ne "manual" -or
            $receipt.model -ne "manual" -or
            $receipt.reference -notmatch '^user:[^:;]+:[^:;]+$') {
            throw "Manual receipt requires manual identities and a user message reference"
        }
        return $receipt
    } elseif ($receipt.source -eq "gemini") {
        $registry = Get-Content -LiteralPath $reviewerRegistryPath -Raw | ConvertFrom-Json
        $registered = $registry.reviewers.gemini_divergent
        if ($receipt.session -ne $registered.session_id -or
            $receipt.conversation -ne $registered.conversation_id -or
            $receipt.role -ne $registered.role -or
            $receipt.model -ne $registered.expected_model) {
            throw "Gemini receipt does not match reviewer registry"
        }
        if ($receipt.reference -notmatch '^transcript:[A-Za-z0-9._-]+$') {
            throw "Gemini receipt requires transcript:<id> reference"
        }
        return $receipt
    } elseif ($receipt.source -eq "chatgpt_control") {
        if ($StageName -notin @("open_pro", "convergent_pro")) {
            throw "ChatGPT-control receipts are valid only for Pro stages"
        }
        $registry = Get-Content -LiteralPath $reviewerRegistryPath -Raw | ConvertFrom-Json
        $registered = if ($StageName -eq "open_pro") {
            $registry.reviewers.open_divergent
        } else {
            $registry.reviewers.convergent
        }
        $expectedReference = if ($ExpectedTerminal -eq "DISPATCHED") {
            [string]$registry.pro_transport.submission_reference
        } else {
            [string]$registry.pro_transport.completion_reference
        }
        if ($receipt.session -ne $registry.pro_transport.session_id -or
            $receipt.conversation -ne $registered.conversation_id -or
            $receipt.role -ne $registered.role -or
            $receipt.model -ne $registered.expected_model_ui -or
            $receipt.reference -ne $expectedReference) {
            throw "ChatGPT-control receipt does not match reviewer registry: $StageName"
        }
        return $receipt
    } else {
        $registry = Get-Content -LiteralPath $reviewerRegistryPath -Raw | ConvertFrom-Json
        $registered = switch ($StageName) {
            "gemini_divergent" { $registry.reviewers.gemini_divergent }
            "open_pro" { $registry.reviewers.open_divergent }
            "convergent_pro" { $registry.reviewers.convergent }
        }
        $expectedModel = if ($StageName -eq "gemini_divergent") {
            [string]$registered.expected_model
        } else {
            [string]$registered.expected_model_ui
        }
        $legacyExchange = if ($StageName -eq "gemini_divergent") {
            $registered.codex_exchange
        } else {
            $registered.legacy_codex_exchange
        }
        if ($receipt.session -ne $legacyExchange.thread_id -or
            $receipt.conversation -ne $registered.conversation_id -or
            $receipt.role -ne $registered.role -or
            $receipt.model -ne $expectedModel) {
            throw "Exchange receipt does not match reviewer registry: $StageName"
        }
        if ($receipt.reference -notmatch $exchangeTurnReferencePattern) {
            throw "Exchange receipt requires an exact Exchange turn id, optionally qualified by a read_thread item id"
        }
        return $receipt
    }
}

function Assert-DispatchReceipt([string]$StageName, [object]$Entry) {
    [void](Assert-TransportReceipt $StageName $Entry ([string]$Entry.dispatch_receipt) "DISPATCHED" $false)
}

function Assert-CompletionReceipt([string]$StageName, [object]$Entry) {
    $receipt = Assert-TransportReceipt $StageName $Entry ([string]$Entry.completion_receipt) "COMPLETE" $true
    if ($receipt.source -ne "manual") {
        if ([string]::IsNullOrWhiteSpace([string]$Entry.dispatched_at) -or
            [string]::IsNullOrWhiteSpace([string]$Entry.dispatch_receipt)) {
            throw "Non-manual COMPLETE requires a prior verified dispatch: $StageName"
        }
        Assert-DispatchReceipt $StageName $Entry
        $dispatch = Parse-Receipt ([string]$Entry.dispatch_receipt)
        if ($dispatch.reference -eq $receipt.reference) {
            throw "COMPLETE requires a distinct destination-side receipt from DISPATCHED: $StageName"
        }
        if ($dispatch.source -ne $receipt.source -or
            $dispatch.session -ne $receipt.session) {
            throw "COMPLETE must come from the transport that produced DISPATCHED: $StageName"
        }
    }
}

function Get-NextStage([object]$Document) {
    if ($Document.round_status -eq "CLOSED") {
        return "CLOSED"
    }
    if ($Document.round_status -eq "SUSPENDED") {
        return "SUSPENDED"
    }
    $dispatched = @($externalStages | Where-Object { $Document.stages.$_.state -eq "DISPATCHED" })
    if ($dispatched.Count -gt 0) {
        return "WAIT:$($dispatched[0])"
    }
    foreach ($name in @("gemini_divergent", "open_pro")) {
        if ($Document.stages.$name.state -eq "NOT_STARTED") {
            return "NEXT:$name"
        }
    }
    if ($Document.stages.gemini_divergent.state -eq "COMPLETE" -and
        $Document.stages.open_pro.state -eq "COMPLETE") {
        if ($Document.stages.controller_synthesis.state -eq "NOT_STARTED") {
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
    }
    $blocked = @($stageOrder | Where-Object { $Document.stages.$_.state -eq "BLOCKED" })
    if ($blocked.Count -gt 0) {
        return "BLOCKED:$($blocked -join ',')"
    }
    return "NO_ELIGIBLE_STAGE"
}

function Assert-Review-State([object]$Document) {
    if ($Document.schema_version -ne 2) {
        throw "Unsupported review-state schema: $($Document.schema_version)"
    }
    if ($Document.round_id -ne (Split-Path -Leaf $round)) {
        throw "Round identity mismatch: $($Document.round_id)"
    }
    if ($Document.round_status -notin $allowedRoundStatuses) {
        throw "Invalid round_status: $($Document.round_status)"
    }
    Assert-Consent $Document.external_source_consent

    foreach ($name in $stageOrder) {
        $entry = $Document.stages.$name
        if ($null -eq $entry) {
            throw "Missing stage: $name"
        }
        if ($entry.state -notin $allowedStates) {
            throw "Invalid state for ${name}: $($entry.state)"
        }
        [void](Assert-ArtifactIdentity $name ([string]$entry.artifact_path))
        if ($entry.state -eq "DISPATCHED") {
            if ($name -notin $externalStages) {
                throw "Controller stage cannot be DISPATCHED: $name"
            }
            if ([string]::IsNullOrWhiteSpace($entry.route_token) -or
                [string]::IsNullOrWhiteSpace($entry.dispatch_receipt) -or
                [string]::IsNullOrWhiteSpace($entry.dispatched_at)) {
                throw "DISPATCHED requires route_token, dispatch_receipt and dispatched_at: $name"
            }
            Assert-RouteToken $name $entry
            Assert-DispatchReceipt $name $entry
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
                [string]::IsNullOrWhiteSpace($entry.route_token)) {
                throw "External COMPLETE requires route_token: $name"
            }
            if ($name -in $externalStages) {
                Assert-RouteToken $name $entry
                Assert-CompletionReceipt $name $entry
            }
            if ([string]::IsNullOrWhiteSpace($entry.completed_at)) {
                throw "COMPLETE requires completed_at: $name"
            }
        }
    }

    $dispatched = @($externalStages | Where-Object { $Document.stages.$_.state -eq "DISPATCHED" })
    if ($dispatched.Count -gt 1) {
        throw "External reviewers must be dispatched serially"
    }
    if ($Document.stages.gemini_divergent.state -in @("DISPATCHED", "COMPLETE") -and
        $Document.external_source_consent.state -ne "APPROVED") {
        throw "Gemini dispatch requires approved external-source consent"
    }

    if ($Document.stages.controller_synthesis.state -eq "COMPLETE" -and
        ($Document.stages.gemini_divergent.state -ne "COMPLETE" -or
         $Document.stages.open_pro.state -ne "COMPLETE")) {
        throw "Controller synthesis requires both divergent reviews COMPLETE"
    }
    if ($Document.stages.convergent_pro.state -ne "NOT_STARTED" -and
        $Document.stages.controller_synthesis.state -ne "COMPLETE") {
        throw "Convergent review requires controller synthesis COMPLETE"
    }
    if ($Document.stages.controller_disposition.state -ne "NOT_STARTED" -and
        $Document.stages.convergent_pro.state -ne "COMPLETE") {
        throw "Controller disposition requires convergent review COMPLETE"
    }
    if ($Document.round_status -eq "CLOSED" -and
        $Document.stages.controller_disposition.state -ne "COMPLETE") {
        throw "CLOSED round requires controller disposition COMPLETE"
    }
    if ($Document.stages.controller_disposition.state -eq "COMPLETE" -and
        $Document.round_status -ne "CLOSED") {
        throw "Completed disposition requires CLOSED round"
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
            dispatch_receipt   = $null
            dispatched_at      = $null
            completion_receipt = $null
            completed_at       = $null
            artifact_path      = $defaultArtifacts[$name]
            blocker            = $null
            blocker_resolution = $null
        }
    }
    $consentState = if (Test-Path -LiteralPath (Join-Path $round $localManifestName)) {
        "PENDING"
    } else {
        "NOT_REQUIRED"
    }
    $document = [ordered]@{
        schema_version = 2
        round_id       = Split-Path -Leaf $round
        round_status   = "ACTIVE"
        updated_at     = [DateTimeOffset]::Now.ToString("o")
        external_source_consent = [ordered]@{
            state = $consentState
            manifest_path = if ($consentState -eq "PENDING") {
                $registeredConsentManifest
            } else { $null }
            manifest_commit = $null
            destination = $null
            approval_receipt = $null
            approved_at = $null
        }
        stages         = $stages
    }
    Write-State $document
    Write-Output $statePath
    exit 0
}

if ($Mode -eq "migrate") {
    $legacy = Read-State
    if ($legacy.schema_version -ne 1) {
        throw "migrate requires schema_version 1"
    }
    $legacy.schema_version = 2
    $legacy | Add-Member -NotePropertyName round_status -NotePropertyValue "ACTIVE"
    $legacy | Add-Member -NotePropertyName external_source_consent -NotePropertyValue ([pscustomobject]@{
        state = if (Test-Path -LiteralPath (Join-Path $round $localManifestName)) { "PENDING" } else { "NOT_REQUIRED" }
        manifest_path = if (Test-Path -LiteralPath (Join-Path $round $localManifestName)) { $registeredConsentManifest } else { $null }
        manifest_commit = $null
        destination = $null
        approval_receipt = $null
        approved_at = $null
    })
    foreach ($name in $stageOrder) {
        $legacy.stages.$name | Add-Member -NotePropertyName blocker_resolution -NotePropertyValue $null
        $legacy.stages.$name | Add-Member -NotePropertyName dispatch_receipt -NotePropertyValue $null
    }
    Assert-Review-State $legacy
    Write-State $legacy
    Write-Output "review_state=MIGRATED path=$statePath"
    exit 0
}

$document = Read-State

if ($Mode -eq "consent") {
    if ([string]::IsNullOrWhiteSpace($ConsentState)) {
        throw "consent requires -ConsentState"
    }
    if ($document.round_status -eq "CLOSED") {
        throw "CLOSED round consent is immutable"
    }
    if ($ConsentState -eq "APPROVED") {
        $expectedManifest = [string]$document.external_source_consent.manifest_path
        $registry = Get-Content -LiteralPath $reviewerRegistryPath -Raw | ConvertFrom-Json
        $geminiReviewer = $registry.reviewers.gemini_divergent
        $standingConsent = $geminiReviewer.standing_consent
        $registeredDestination = "$($geminiReviewer.expected_model) / Antigravity conversation $($geminiReviewer.conversation_id)"
        if ([string]::IsNullOrWhiteSpace($ConsentApprovalReceipt) -and
            $null -ne $standingConsent -and
            $standingConsent.state -eq "APPROVED" -and
            $standingConsent.scope -eq "tracked_round_gemini_local_source_manifests") {
            $ConsentApprovalReceipt = [string]$standingConsent.approval_receipt
        }
        if ([string]::IsNullOrWhiteSpace($ConsentManifestPath) -or
            $ConsentManifestPath.Replace("\", "/") -ne $expectedManifest -or
            $ConsentManifestCommit -notmatch '^[0-9a-fA-F]{40}$' -or
            $ConsentDestination -ne $registeredDestination -or
            $ConsentApprovalReceipt -notmatch '^user:[^:;]+:[^:;]+$') {
            throw "APPROVED consent requires the registered manifest, commit, Gemini destination and explicit or registered standing user receipt"
        }
        $document.external_source_consent = [pscustomobject]@{
            state = "APPROVED"
            manifest_path = $ConsentManifestPath.Replace("\", "/")
            manifest_commit = $ConsentManifestCommit
            destination = $ConsentDestination
            approval_receipt = $ConsentApprovalReceipt
            approved_at = [DateTimeOffset]::Now.ToString("o")
        }
    } elseif ($ConsentState -eq "PENDING") {
        $expectedManifest = [string]$document.external_source_consent.manifest_path
        if ([string]::IsNullOrWhiteSpace($expectedManifest) -or
            (-not [string]::IsNullOrWhiteSpace($ConsentManifestPath) -and
             $ConsentManifestPath.Replace("\", "/") -ne $expectedManifest)) {
            throw "PENDING consent must retain the registered manifest path"
        }
        $document.external_source_consent = [pscustomobject]@{
            state = "PENDING"
            manifest_path = $expectedManifest
            manifest_commit = $null
            destination = $ConsentDestination
            approval_receipt = $null
            approved_at = $null
        }
    } else {
        if ($ConsentState -eq "NOT_REQUIRED" -and
            (Test-Path -LiteralPath (Join-Path $round $localManifestName))) {
            throw "NOT_REQUIRED is invalid while a Gemini local-source manifest exists"
        }
        $document.external_source_consent = [pscustomobject]@{
            state = $ConsentState
            manifest_path = $document.external_source_consent.manifest_path
            manifest_commit = $null
            destination = $document.external_source_consent.destination
            approval_receipt = $null
            approved_at = $null
        }
    }
    Assert-Review-State $document
    Write-State $document
    Write-Output "review_consent=$ConsentState path=$statePath"
    exit 0
}

if ($Mode -eq "round") {
    if ([string]::IsNullOrWhiteSpace($RoundStatus)) {
        throw "round requires -RoundStatus"
    }
    if ($document.round_status -eq "CLOSED") {
        if ($RoundStatus -eq "CLOSED") {
            Write-Output "review_round=NOOP_CLOSED path=$statePath"
            exit 0
        }
        throw "CLOSED round is immutable"
    }
    $document.round_status = $RoundStatus
    Assert-Review-State $document
    Write-State $document
    Write-Output "review_round=$RoundStatus path=$statePath"
    exit 0
}

if ($Mode -eq "transition") {
    if ([string]::IsNullOrWhiteSpace($Stage) -or [string]::IsNullOrWhiteSpace($State)) {
        throw "transition requires -Stage and -State"
    }
    $entry = $document.stages.$Stage
    if ($entry.PSObject.Properties.Name -notcontains "dispatch_receipt") {
        $entry | Add-Member -NotePropertyName dispatch_receipt -NotePropertyValue $null
    }
    if ($document.round_status -ne "ACTIVE") {
        throw "Stage transitions require round_status ACTIVE"
    }
    if ($entry.state -eq "COMPLETE") {
        throw "COMPLETE is immutable: $Stage"
    }
    $from = [string]$entry.state
    if ($Stage -in $externalStages -and $State -eq "COMPLETE") {
        $candidateReceipt = Parse-Receipt $CompletionReceipt
        if ($null -eq $candidateReceipt) {
            throw "External COMPLETE requires structured completion receipt"
        }
        if ($candidateReceipt.source -ne "manual" -and
            ([string]::IsNullOrWhiteSpace($entry.dispatched_at) -or
             [string]::IsNullOrWhiteSpace($entry.dispatch_receipt))) {
            throw "External COMPLETE requires a prior DISPATCHED state for the same route"
        }
    }
    if ($from -eq "BLOCKED" -and $State -ne "BLOCKED") {
        if ($ResolutionReceipt -notmatch '^(user|tool|evidence|controller):\S+') {
            throw "Leaving BLOCKED requires typed -ResolutionReceipt: $Stage"
        }
        $entry.blocker_resolution = $ResolutionReceipt
    }
    $allowedTargets = switch ($from) {
        "NOT_STARTED" {
            if ($Stage -in $externalStages) { @("DISPATCHED", "COMPLETE", "BLOCKED") }
            else { @("COMPLETE", "BLOCKED") }
        }
        "DISPATCHED" { @("COMPLETE", "BLOCKED") }
        "BLOCKED" {
            if ($Stage -in $externalStages) { @("DISPATCHED", "COMPLETE", "BLOCKED") }
            else { @("COMPLETE", "BLOCKED") }
        }
    }
    if ($State -notin $allowedTargets) {
        throw "Invalid transition: $Stage $from -> $State"
    }
    if (-not [string]::IsNullOrWhiteSpace($ArtifactPath)) {
        [void](Assert-ArtifactIdentity $Stage $ArtifactPath)
    }
    $entry.artifact_path = $defaultArtifacts[$Stage]
    $entry.state = $State

    switch ($State) {
        "NOT_STARTED" {
            $entry.route_token = $null
            $entry.dispatch_receipt = $null
            $entry.dispatched_at = $null
            $entry.completion_receipt = $null
            $entry.completed_at = $null
            $entry.blocker = $null
        }
        "DISPATCHED" {
            if ([string]::IsNullOrWhiteSpace($RouteToken) -or
                [string]::IsNullOrWhiteSpace($DispatchReceipt)) {
                throw "DISPATCHED requires -RouteToken and -DispatchReceipt"
            }
            $entry.route_token = $RouteToken
            $entry.dispatch_receipt = $DispatchReceipt
            Assert-RouteToken $Stage $entry
            Assert-DispatchReceipt $Stage $entry
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
            if ($Stage -in $externalStages) {
                if ([string]::IsNullOrWhiteSpace($entry.route_token)) {
                    if ([string]::IsNullOrWhiteSpace($RouteToken)) {
                        throw "External COMPLETE requires -RouteToken"
                    }
                    $entry.route_token = $RouteToken
                } elseif (-not [string]::IsNullOrWhiteSpace($RouteToken) -and
                          $RouteToken -ne $entry.route_token) {
                    throw "COMPLETE cannot replace the prior DISPATCHED route"
                }
                if ([string]::IsNullOrWhiteSpace($entry.route_token)) {
                    throw "External COMPLETE requires -RouteToken"
                }
            }
            $entry.completion_receipt = if ($Stage -in $externalStages) {
                $CompletionReceipt
            } else {
                $null
            }
            $entry.completed_at = [DateTimeOffset]::Now.ToString("o")
            $entry.blocker = $null
            if ($Stage -eq "controller_disposition") {
                $document.round_status = "CLOSED"
            }
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
    Write-Output "round_status=$($document.round_status) next=$(Get-NextStage $document) consent=$($document.external_source_consent.state)"
    foreach ($name in $stageOrder) {
        [pscustomobject]@{
            stage = $name
            state = $document.stages.$name.state
            artifact = $document.stages.$name.artifact_path
            blocker = $document.stages.$name.blocker
        }
    }
} elseif ($Mode -eq "next") {
    Write-Output (Get-NextStage $document)
} else {
    Write-Output "review_state=VALID path=$statePath"
}
