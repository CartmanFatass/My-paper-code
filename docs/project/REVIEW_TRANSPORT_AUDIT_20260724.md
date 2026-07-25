# Review-transport workflow audit

Date: 2026-07-24

```text
scope=external_review_round_transport
trigger=user_requested_stability_audit_after_round_retirement
method=direct_inspection_of_scripts_transcripts_and_the_live_conversation
findings=7
fixed=6
open=1
compute=zero
iteration_consumed=false
```

The G20 credit-rule round was dispatched, fragmented, retired, and re-opened in
one session. This audit establishes why, from evidence rather than recollection,
and records what changed. Every finding below was reproduced or read directly
out of a transcript, a script, or the reviewer conversation.

## Findings

### F1 — the mandatory pre-dispatch gate crashed on its own default, and the round shipped anyway

`verify_pro_review_boundary.ps1` defaulted `-Remote` to `My-paper-code`, the
GitHub slug, and passed it to `git ls-remote`, which needs a git remote *name*.
The only configured remote is `origin`, so every production call died with
`fatal: 'My-paper-code' does not appear to be a git repository`.

That exact error signature appears in the round-1 exchanger transcript, and I
reproduced it. The gate also encoded the requirement round 1 actually violated —
it demanded `ALGORITHM_PRINCIPLES.md` and `OPEN_REVIEW_PRINCIPLES.md` appear in
the question — so **a working gate would have stopped the round before any
browser session opened**.

The child treated a crashed gate as a passed gate. That is the more dangerous
half of the finding.

### F2 — two scripts in one workflow disagreed on what "evidence declaration" means

| Script | Contract it enforced |
|---|---|
| `verify_pro_review_boundary.ps1` | any backticked path matching `^(docs\|ha_ctse_process\|scripts\|tests\|ref)/` anywhere in the question |
| `build_review_evidence_archive.ps1` | a literal `## Evidence to read` heading followed by `` - `path` `` items |

A question could satisfy the first and be refused by the second. That is exactly
what happened: the round passed dispatch and then the recovery archive could not
be built, with `Question has no exact evidence allow-list`.

### F3 — the commit-time contract test exercised a parameter set production never uses

`review_round_contract_test.ps1` called the gate with `-Remote $repo`, a local
path, which `ls-remote` accepts. The test therefore passed on every commit while
the production default was broken. A guard that only exercises a synthetic
configuration proves nothing about the real call path.

### F4 — a newline is a send, so one fence became five messages

The `computer` `type` action delivers each `\n` as an Enter keypress, and Enter
submits in this composer. A multi-line fence was therefore chopped into
progressively truncated `CURRENT_REVIEW_ASSIGNMENT` messages. The reviewer
replied asking for the complete fields.

The visible symptom read as "the exchanger keeps re-sending the same content."
It was one message being fragmented, not a retry loop — and that misreading cost
time, because it also produced a **false diagnosis** that the GitHub connector
could not see `untied-k`. The connector was fine: the bootstrap round records
`Snapshot reviewed: d07eda4b…`, and the eventual round-2 trace shows
`Fetched lines 700–755 of the screening script`. The fence had simply never
arrived intact.

### F5 — the tool the skill prescribed for composing does not work here

The skill's transport table routed fence composition to `form_input`. The
composer is a contenteditable `DIV`, so `form_input` returns
`Element type "DIV" is not a supported form input`. The prescription was
unexecutable, which is what pushed the child onto `type` and into F4.

An unexecutable instruction is not a neutral error — it silently delegates the
mechanism choice back to whoever hits it.

### F6 — a mid-generation thinking trace was archived as scientific raw

An archival pass captured 794 bytes consisting of extended-reasoning progress
labels (`Answer now`, `Clarifying file search`, `Formulated the response`),
wrote it to `21_PRO_OPEN_RAW.md`, and asserted byte equality — while the
conversation still showed an active `Stop answering` control. Two stable
snapshots certified a trace that merely sat still between snapshots.

Had this reached reconciliation it would have become a fabricated external
result. It was caught by inspecting the archive rather than trusting the
completion report, and deleted.

### F7 — a wrong brief overrode a skill the child had read correctly

The exchanger read `SKILL.md` and `EXTERNAL_PRO.md` and had the recovery
procedure loaded; `build_review_evidence_archive` appears in its transcript
though no brief mentioned it. It stopped at the right moment and asked. The
Project Manager answered "submit the question body verbatim, splitting across
messages if needed," contradicting `SKILL.md` line 116 — *the question carries
exact paths, not file contents*.

The child was not the failure. A child follows the brief, so a brief that
contradicts the governing procedure is strictly worse than no brief.

## What changed

- **One gate replaces two.** `preflight_review_round.ps1` is now the entire
  pre-dispatch contract: commit pushed and reachable, question present at it,
  non-empty `## Evidence to read` allow-list with every path present and no
  duplicates, standing contracts allow-listed, fence-artifact fields matching
  the round, and the recovery archive actually building.
  `verify_pro_review_boundary.ps1` is deleted, so the conflicting definition in
  F2 cannot return.
- **The gate is validated in both directions.** Round 2 returns
  `ROUND_PREFLIGHT_READY` with 15 allow-listed paths; the retired round returns
  `ROUND_PREFLIGHT_FAILED` naming all four of its real defects. A gate that
  cannot fail is decoration.
- **The contract test now guards the production path** (F3): the gate exists,
  the superseded one is absent, its default `-Remote` is a configured git
  remote, and it still rejects the retired round.
- **Transport composes by paste** (F4, F5): the message is authored as a
  committed round artifact, loaded to the clipboard with a verified `-ceq`
  round trip, and pasted once. Soft line breaks are the documented fallback.
  This also makes "submit verbatim" auditable from Git rather than from a
  browser transcript.
- **Completion detection hardened** (F6): an active stop control ends the
  question outright, and a capture is sanity-checked against the question's
  asks and plausible size before it may be written.
- **A crashed gate is a failed gate** is now stated in both the skill and the
  exchanger definition (F1).
- **Brief authoring is bound** (F7): `AGENT_CONTEXT.md` requires quoting the
  governing procedure rather than paraphrasing it, and pins the two traps hit.

## Open

**O1 — file upload to the reviewer is blocked by the harness classifier.** The
evidence-archive recovery path in the skill cannot currently execute: the upload
is refused as bulk archive exfiltration to an external host. It was not needed
in the end, because the connector reads the repository correctly once the fence
arrives intact, so the documented fallback is untested rather than known-good.
It stays open and must not be assumed available.

## What this audit does not cover

The experiment-operator and implementer paths were not audited here. The
implementer lap in this session behaved correctly against its brief and its
finding was independently reproduced, but that is one observation, not a review
of that workflow.
