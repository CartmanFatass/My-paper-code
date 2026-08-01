[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Assignment')]
    [string]$Mode,

    [Parameter(Mandatory = $true)][string]$Round,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$Question
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$Repository = 'CartmanFatass/My-paper-code'
$Branch = 'aggressive'

function Require-SingleLine([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "[\r\n]") {
        throw "$Name must be one nonempty line."
    }
}

foreach ($field in @{
    Round = $Round
    Question = $Question
}.GetEnumerator()) {
    Require-SingleLine $field.Key $field.Value
}

if ($StageCommit -cnotmatch '^[0-9a-f]{40}$') {
    throw 'StageCommit must be exactly 40 lowercase hexadecimal characters.'
}

$instruction = 'Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.'
$identity = @(
    "repository=$Repository"
    "branch=$Branch"
    "round=$Round"
    "stage_commit=$StageCommit"
    "question=$Question"
    "instruction=$instruction"
)

Write-Output (@('CURRENT_REVIEW_ASSIGNMENT') + $identity -join "`n")
