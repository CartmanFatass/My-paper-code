<#
.SYNOPSIS
    Scaffold a review round directory so preflight can pass, instead of
    re-deriving five file names and a fence format from memory each time.

.DESCRIPTION
    Five rounds this session were scaffolded by hand. The file names, the fence's
    exact opening line, and the two standing contracts that must appear in the
    allow-list are all fixed, and preflight_review_round.ps1 already refuses a
    round that gets any of them wrong. Producing them by hand only moves the
    discovery of a mistake to preflight.

    Creates:
      10_FENCE.txt                     complete and correct, from the arguments
      20_PRO_OPEN_QUESTION.md          skeleton with the allow-list pre-seeded
      30_PM_SCIENTIFIC_RECONCILIATION.md   skeleton
      50_MECHANICAL_INTAKE_RECORD.md       skeleton

    It deliberately does NOT create `21_PRO_OPEN_RAW.md`. That file is the
    verbatim capture and is written once, by archive_pro_response.ps1, which
    refuses if it already exists. A scaffolded empty file would defeat that
    write-once guard on its first use.

    The question body is left for you: this scaffolds the shape, never the
    science. The allow-list is seeded with the two standing contracts preflight
    requires and a marker for the round's own evidence -- add yours, and read
    `$hmasd-review-round` on what belongs there.

.EXAMPLE
    new_review_round.ps1 -Round 20260728_r5_something -StageCommit b977e188...
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Round,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [string]$Branch = 'untied-k',
    [string]$Repository = 'CartmanFatass/My-paper-code',
    [string]$Title = 'TITLE THIS ROUND'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
# Prove the root before writing anything into it. The first version walked one
# level too few, created the whole round tree under .claude/, and reported
# ROUND_SCAFFOLD_OK -- a scaffolder that writes to the wrong place and calls it
# success is the same defect class this repository has been removing all day.
if (-not (Test-Path -LiteralPath (Join-Path $repo 'AGENTS.md'))) {
    @{ status = 'ROUND_SCAFFOLD_REFUSED'
       reason = "Resolved repository root '$repo' has no AGENTS.md, so it is not this repository. Nothing was written." } |
        ConvertTo-Json; exit 1
}
$roundRel = "docs/external-review/rounds/$Round"
$dir = Join-Path $repo $roundRel

if (Test-Path -LiteralPath $dir) {
    @{ status = 'ROUND_SCAFFOLD_REFUSED'
       reason = "Round directory already exists: $roundRel. Rounds are sealed once reconciled; open a new one rather than reusing it." } |
        ConvertTo-Json; exit 1
}
if ($StageCommit.Length -lt 7) {
    @{ status = 'ROUND_SCAFFOLD_REFUSED'
       reason = "stage_commit '$StageCommit' is too short to identify a commit. The fence is the reviewer's only anchor to a tree." } |
        ConvertTo-Json; exit 1
}

New-Item -ItemType Directory -Path $dir -Force | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Write-File([string]$name, [string]$body) {
    [System.IO.File]::WriteAllText((Join-Path $dir $name), $body, $utf8)
}

# The fence must OPEN with a bare CURRENT_REVIEW_ASSIGNMENT line -- preflight
# checks exactly that, and a leading blank line has failed a round before.
Write-File '10_FENCE.txt' @"
CURRENT_REVIEW_ASSIGNMENT
repository=$Repository
branch=$Branch
round=$Round
stage_commit=$StageCommit
question=$roundRel/20_PRO_OPEN_QUESTION.md
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
"@

Write-File '20_PRO_OPEN_QUESTION.md' @"
# $Title

<!-- The question carries decisions and never assigns verification labour to
     Pro. Read `$hmasd-review-round` before writing it. -->

## What is being decided

TODO

## What I did and what it returned

TODO

## Evidence to read

- ``docs/project/ALGORITHM_PRINCIPLES.md``
- ``docs/external-review/OPEN_REVIEW_PRINCIPLES.md``
- TODO: this round's own evidence, one backticked path per line

<!-- The allow-list is the ONLY thing the reviewer can open. A path named in
     prose, in a side manifest, or in the fence but not listed here never
     reaches it. A closure claim whose evidence is missing here cannot be
     adjudicated, and will be returned as a PM-owned premise. -->
"@

Write-File '30_PM_SCIENTIFIC_RECONCILIATION.md' @"
# Reconciliation — $Round

Ruling: ``21_PRO_OPEN_RAW.md``, stage commit ``$StageCommit``.

## What was decided

TODO

## Where I was corrected

TODO — record these even when the conclusion survived. A right answer reached
through an argument that does not support it is a finding, not a pass.

## Next action

TODO
"@

Write-File '50_MECHANICAL_INTAKE_RECORD.md' @"
# Mechanical intake record — transport facts only

``````text
round         = $Round
reviewer_key  = open_divergent
branch        = $Branch
conversation  = TODO
stage_commit  = $StageCommit
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = TODO of 3
``````

## Preflight

TODO — paste the preflight JSON.

## Capture

TODO — paste the archive_pro_response.ps1 JSON: chars, exact_equal, first_line,
last_line. Do not summarise it.

## Transport faults

TODO, or ``none``. Record deviations even when they worked.
"@

@{ status = 'ROUND_SCAFFOLD_OK'; round = $roundRel
   created = @('10_FENCE.txt', '20_PRO_OPEN_QUESTION.md', '30_PM_SCIENTIFIC_RECONCILIATION.md', '50_MECHANICAL_INTAKE_RECORD.md')
   not_created = '21_PRO_OPEN_RAW.md is written once by archive_pro_response.ps1; scaffolding it empty would defeat that write-once guard.'
   next = "Write the question, COMMIT the round, then run preflight against the commit you just made. Preflight resolves the question through `git cat-file` at the stage_commit, so it necessarily fails on an uncommitted scaffold -- the fence anchors the reviewer to a tree, and a question that is not in that tree is not readable from it. Pass the new commit as -Commit, not the one scaffolded into the fence, and update 10_FENCE.txt to match." } |
    ConvertTo-Json -Depth 4
exit 0
