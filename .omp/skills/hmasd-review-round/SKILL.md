---
name: hmasd-review-round
description: Define one tracked GPT-5.6 Pro scientific question, evidence boundary, response acceptance contract, and Controller intake envelope.
---

# HMASD External Pro Research Round

## Scope

External GPT-5.6 Pro is the scientific decision source. It owns conjecture and
definition correction, derivation, counterexample search, retained lemmas,
portfolio meaning, estimands, evidence meaning, and selection of one scheduled
research action. One scheduled action serializes resources; it does not make
other scientifically defensible explanations illegal.

The Controller owns reviewer-visible Git boundaries, factual reconciliation,
direct evidence intake, durable record writes, executable realization, resource
authorization, and user communication. Review and intake authorize neither
implementation nor compute.

Use a full plural review for competing explanations, proposed family retirement,
benchmark-identification disputes, repeated ambiguity, or full-algorithm
integration. Use a focused continuation in the same registered Pro conversation
for one local scientific ambiguity or correction.

## Transport execution boundary

`hmasd-browser-pro-exchange` is not an active Skill and must not be invoked.
The user-approved Luna-high `hmasd-exchange-review` local task agent performs one
Controller-frozen mechanical BrowserMCP exchange. It may validate, submit the
deterministic dispatch, publish the receipt, observe, click the page-provided
`Copy response` button and archive the exact response. It never defines the
question, chooses science, performs factual reconciliation or starts a
successor. `hmasd-review-scout` retains factual transport experience only.

The authenticated registered Pro page is a one-time environmental prerequisite,
not a per-round user action. If that prerequisite is absent, transport fails
closed. Routine human recovery, another browser, keyboard-copy shortcuts and
local scientific substitution are forbidden. The Controller alone owns
question preparation, direct evidence intake and every transition after the
agent returns immutable receipt/raw evidence.

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

The receipt is absent before a proven submission and immutable afterward. The
raw response is absent before accepted stable capture and immutable afterward.
An absent receipt and raw response mean `READY_TO_SUBMIT`; transport attempts
do not change that durable state.

Commit and push evidence first and record its exact 40-character evidence
commit. Then write the brief, manifest, and question with repository, review
branch, evidence commit, exact evidence files, reference-code paths, relevant
symbols, and every scientific-principle path. Commit and push those artifacts
as the stage commit.

## Integrity interfaces

These retained scripts validate identity, receipt and no-clobber archival. They
are invoked only by the bounded exchange agent or by focused contract tests:

- `.omp/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1`
- `.omp/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1`
- `.omp/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1`
- `.omp/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1`
- `.omp/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`

The canonical validator and pushed-boundary verifier must agree on the question
and source manifest. When a receipt exists, expected stage/evidence commits,
repository, review branch, registered conversation URL, and model come from the
verified boundary and registry, never from receipt fields. Raw-first
`ALREADY_ARCHIVED` remains terminal. Local, ignored, or unpushed files are not
reviewer evidence.

## Mandatory question envelope

Every future question begins exactly:

`HMASD_BROWSER_PRO_QUESTION_V1 round=<round> body_sha256=<64 lowercase hex>`

One blank line and a nonempty body follow. The digest covers UTF-8/no-BOM body
bytes after CRLF/CR normalization to LF, preserving the trailing LF. The body
must contain this exact own line:

    Do not put any triple-backtick sequence or nested fenced block between the response markers.

The complete substantive answer belongs in exactly one fenced `text` block,
with no substantive response outside it. Its exact first and last lines are:

```text
HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=<round> question_sha256=<digest>
HMASD_BROWSER_PRO_RESPONSE_V1_END round=<round> question_sha256=<digest>
```

The answer sits strictly between those markers. Schemas and examples inside
the outer block use plain or indented text, never another fence.

The scientific question asks for plural live conjectures and scopes; derived
intervention, natural, and held-out consequences; concrete counterexamples and
retained lemmas; the smallest refuted unit; one scheduled action selected by
information gain, cost, and reversibility; evidence semantics to freeze;
reactivation conditions for unscheduled ideas; and a concise Chinese user
brief. Pro must not equate one scheduled action with one legal successor or
write an implementation plan. If implementation is selected, Pro defines the
scientific object and estimand; the Controller later freezes architecture.

## Response acceptance and intake

A raw response is acceptable only when it is bound to the verified identity,
contains exactly one correct marked substantive block, appears identically in
two stable BrowserMCP snapshots and is captured by clicking the latest
page-provided `Copy response` button. The retained no-clobber archive interface
validates the copied outer fence and markers before publishing only the exact
body. A valid receipt forbids resubmission. An existing raw response forbids
browser work. Transport gaps never authorize rewriting raw text.

After accepted archival, write factual `30_EVIDENCE_RECONCILIATION.md` without
changing Pro science. Read `references/cdc-principles.md`, distinguish Pro
science from repository fact and operational inference, and apply the smallest
exact conjecture, lemma, counterexample, portfolio, and evidence-note deltas.
Show the Pro Chinese brief and record one disposition. A material scientific
ambiguity returns as one focused marked continuation in the same conversation.

If Pro cannot read pushed evidence, repair the GitHub-connector boundary rather
than pasting local source. No local model, Controller inference, persistent
role, or local agent substitutes for a missing Pro decision. Only after valid
intake may the Controller freeze an executable plan within the accepted
scientific direction and existing resource authority.
