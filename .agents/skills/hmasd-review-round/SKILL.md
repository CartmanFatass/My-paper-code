---
name: hmasd-review-round
description: Use only by the active HMASD Controller for a tracked external GPT-5.6 Pro scientific CDC decision. It prepares one marked question, operates the pinned BrowserMCP exchange directly, archives the natural marked response, performs direct evidence intake, applies durable record deltas, and prepares any later Controller-owned implementation action.
---

# HMASD External Pro Research Round

## Scope

External GPT-5.6 Pro is the scientific decision source. It owns conjecture and
definition correction, derivation, counterexample search, retained lemmas,
portfolio meaning, and selection of one scheduled research action. One
scheduled research action serializes resources; it does not make other
scientifically defensible explanations illegal.

The active Controller owns reviewer-visible Git boundaries, the complete
BrowserMCP state machine, factual reconciliation, Controller direct evidence
intake, durable record writes, executable realization, resource authorization,
and user communication. It uses only the pinned BrowserMCP server and registered
user-connected Pro tab. There is no completion observer or alternate browser
surface. If implementation is later authorized, the Controller freezes
executable architecture inside the accepted Pro scientific direction and
assigns bounded project-local OMP agents.

Use a full plural review for competing explanations, proposed family retirement,
benchmark-identification disputes, repeated ambiguity, or full-algorithm
integration. Use a focused continuation in the same registered Pro conversation
for one local scientific ambiguity or correction. Both use the same pushed
evidence and exact raw-archive discipline.

## Round boundary

```text
docs/external-review/rounds/<round>/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  19_BROWSER_PRO_SUBMISSION.json
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  50_DISPOSITION.md
```

The receipt is absent before submission and immutable afterward. The raw is
absent before stable capture and immutable afterward.

Commit and push evidence first and record its exact 40-character evidence
commit. Then write the brief, manifest, and question with repository, current
review branch, evidence commit, exact result/evidence files, reference-code
paths, relevant symbols, and every scientific-principle path. Commit and push
those review artifacts as the stage commit. A commit cannot contain its own
hash, so the artifacts name the evidence commit while the Controller records
the stage commit that contains them.

An initial no-receipt READY check may run
`.agents/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1`
without expected identity. Verify the pushed boundary with
`.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`.
When raw is absent and a receipt exists, invoke the validator with the complete
trusted `-ExpectedStageCommit`, `-ExpectedEvidenceCommit`,
`-ExpectedRepository`, `-ExpectedReviewBranch`, `-ExpectedConversationUrl`, and
`-ExpectedModel` tuple from pushed-boundary verification and the registered
conversation, never from receipt fields. Require validator and verifier to
return the same canonical question and source manifest, and retain validator
`receipt_sha256` as the exact active receipt identity for archival. Raw-first
`ALREADY_ARCHIVED` remains terminal without receipt compatibility execution.
For `READY_TO_SUBMIT`, run
`.agents/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1`
to obtain the deterministic compact dispatch before touching the browser.
Local, ignored, or unpushed files are not reviewer evidence. Preserve the
pushed-boundary verifier unchanged.

## Mandatory future question envelope

Every future question's first line is exactly
`HMASD_BROWSER_PRO_QUESTION_V1 round=<round> body_sha256=<64 lowercase hex>`,
followed by one blank line and a nonempty body. Compute the digest over the
UTF-8/no-BOM bytes of that remaining body after CRLF/CR normalization to LF,
preserving its trailing LF.
Every canonical V1 question body must contain this exact case-sensitive
instruction as its own line:

    Do not put any triple-backtick sequence or nested fenced block between the response markers.

Every body must instruct Pro to put its complete substantive answer in exactly
one fenced `text` block and put no substantive response outside it. The block
must begin and end on exact own lines:

```text
HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=<round> question_sha256=<digest>
HMASD_BROWSER_PRO_RESPONSE_V1_END round=<round> question_sha256=<digest>
```

The answer belongs strictly between those markers. Any schemas or examples
requested inside that one outer response block must use plain or indented text,
never another fenced block. No triple-backtick sequence may occur between the
response markers.

The scientific question asks for plural live conjectures and scopes; derived intervention, natural, and
held-out consequences; concrete counterexamples and retained lemmas; the
smallest refuted unit; one scheduled action selected by information gain, cost,
and reversibility; evidence semantics to freeze; reactivation conditions for
unscheduled ideas; and a concise Chinese user brief. Pro must not equate one
scheduled action with one legal successor or write an implementation plan. If
implementation is selected, Pro defines the scientific object and estimand; the
Controller later freezes executable architecture.

## Direct BrowserMCP exchange

```text
$hmasd-browser-pro-exchange

BROWSER_PRO_REVIEW
reviewer_role=OPEN_DIVERGENT
round=<id>
stage_commit=<40-character pushed SHA>
evidence_commit=<40-character pushed evidence SHA>
repository=<GitHub owner/repository>
review_branch=<pushed branch>
round_path=docs/external-review/rounds/<id>
source_manifest=01_SHARED_SOURCE_MANIFEST.md
receipt=19_BROWSER_PRO_SUBMISSION.json
question=20_PRO_OPEN_QUESTION.md
raw=21_PRO_OPEN_RAW.md
conversation=<registered ChatGPT conversation URL>
expected_model_ui=Pro
evidence_transport=github_connector
completion_policy=ARCHIVE_NATURAL_RESPONSE_EXACTLY
```

The Controller runs the exchange Skill's exact
`VALIDATED -> RECONCILED_IDLE -> DRAFT_CONFIRMED -> SUBMISSION_CONFIRMED -> GENERATING -> STABLE_TWICE -> ARCHIVED`
state machine inline in the same long-lived session. Every round requires a live
preflight; neither registry state nor an earlier round claims a durable live
connection. Use fresh refs, exactly one `browser_type` action for the no-newline
`HMASD_BP_D1` dispatch of at most 352 UTF-16 code units, a separate
`browser_press_key Enter`, 20-second wait chunks, the immutable v2 receipt, and
two stable temporary snapshots separated by file timestamps of at least ten
seconds. Never type the full question, upload or attach a file, blind retry, or
click Send, Stop answering, Answer now, or Copy response. A `browser_type`
timeout is permanently indeterminate even if a later snapshot looks empty:
never retry, retype, or submit on that live connection; fail closed and require
a fresh BrowserMCP process/extension connection and live preflight. Run
`.agents/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1`
with distinct pre-submit draft and post-submit snapshots and the Controller's
already-owned boundary/registry identity; the recorder threads that tuple
through validation. Its reconstructed draft composer must byte-match the
dispatch plus snapshot normalization LF, and the final user turn must byte-match
the exact no-LF dispatch before an empty submitted composer proves submission.
Run `.agents/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1`
with the receipt, two stable snapshots, and mandatory `StageCommit`,
`EvidenceCommit`, `Repository`, `ReviewBranch`, `ConversationUrl`, and
`ExpectedModel` values from pushed-boundary verification and the registered
conversation. The archiver passes the tuple to receipt validation for exclusive
no-clobber archival, then opens the canonical receipt through a Windows
no-follow final-component handle with read access and reader-only sharing. File
attributes and the normalized final path come from that same handle;
directories, final reparse points, and case-insensitive final-handle-path
mismatches (including reparse ancestry) fail before the handle is wrapped in
the retained read stream. The held bytes must match validator
`receipt_sha256`; any writer/delete-capable handle or byte change fails before
raw publication. The digest-stable receipt handle remains alive throughout
snapshot parsing, temporary raw preparation, atomic move, and exact raw reread,
using only the validator-returned round and question identity.
Every full-page snapshot must be a distinct regular file under the canonical OS
temporary root, outside the repository and free of reparse-point ancestry; the
scripts delete accepted inputs in `finally` on success, receipt-lock failure,
or content failure.

## Controller direct evidence intake

After `ARCHIVED`, write factual `30_EVIDENCE_RECONCILIATION.md` without changing
Pro science. Read `references/cdc-principles.md`, distinguish Pro science from
repository fact and operational inference, and apply the smallest exact
conjecture, lemma, counterexample, portfolio, and evidence-note deltas. Show the
Pro Chinese brief and record one disposition. A material scientific ambiguity
returns as one focused marked continuation in the same Pro conversation.

Review and intake authorize neither implementation nor compute. When a later
resource action is authorized, the Controller freezes the executable plan from
the archived Pro direction, estimand, reconciliation, resource boundary, working
scope, and completion contract, then dispatches project-local OMP agents.

## Recovery

A valid submission receipt matching the complete trusted boundary/registry
identity forbids resubmission and resumes observation; missing expected identity
fails closed. An existing raw forbids all browser work and returns
`ALREADY_ARCHIVED` without receipt compatibility execution. A naturally
completed raw with scientific gaps remains valid transport and is classified
separately. If Pro cannot read
pushed evidence, repair the GitHub-connector boundary rather than pasting local
source. There is no persistent Exchange role, completion-agent route, heartbeat,
or alternate browser fallback. Review and direct evidence intake never authorize
implementation or compute by themselves.
