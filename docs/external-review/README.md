# HMASD External Review Workflow

This directory contains durable external-review prompts and the exact raw
archives imported from Agentify. The active layout is keyed by a direction and
a deterministic frozen round; the older `rounds/` tree is historical
provenance only and is never parsed as active workflow state.

## Active layout

```text
docs/external-review/directions/<direction-id>/<round-id>/
├── GEMINI_DIVERGENT_PROMPT.md
├── PRO_DIVERGENT_PROMPT.md
├── PRO_CONVERGENCE_PROMPT.md
├── gemini/
│   ├── NATURAL_COMPLETION_ARCHIVE.json
│   └── HANDOFF.md
├── pro-divergent/
│   ├── NATURAL_COMPLETION_ARCHIVE.json
│   └── HANDOFF.md
└── pro-convergence/
    ├── NATURAL_COMPLETION_ARCHIVE.json
    └── HANDOFF.md
```

The provider directories are populated only after the corresponding Agentify
operation returns a verified natural-completion archive. Temporary handoff
inputs used by Artifact Writer remain under the ignored local workflow/runtime
area; `HANDOFF.md` is the durable, EM-authored scientific intake.

A round is identified by the first 20 hexadecimal characters of:

```text
sha256(direction_id + "\n" + question_sha256 + "\n" +
evidence_set_sha256 + "\n" + workflow_version)
```

Consequently, reusing a direction, question, evidence set, and workflow version
reuses the same round identity. A changed frozen question or evidence set creates
a new round and leaves the old round labeled historical provenance.

## Blind provider sequence

1. Freeze the question and declared evidence SHAs.
2. Keep the Gemini divergent and Pro divergent prompts separate and mutually
   blind. Each provider receives only its own provider-specific prompt.
3. Perform local EM research and write the EM-authored local synthesis.
4. Author the Pro convergence prompt from that synthesis and declared repository
   evidence only. It must not include or link either divergent prompt, provider
   response, archive, handoff, conversation, or operation context.
5. Submit through Agentify's provider-specific transport and monitor through
   provider-independent monitor transports.
6. Import the exact archive bytes and give Artifact Writer the ignored handoff
   input. EM owns the scientific handoff and external-review index update.

Gemini is divergent inspiration and Pro convergence is a later synthesis check;
neither provider answer is an authority for portfolio choice, implementation,
or scientific acceptance.

## Agentify boundary

Agentify's Schema-v2 ledger is the sole authority for browser submission,
idempotency, send counts, and commitment. HMASD stores operation references and
validated exact archives; it never reconstructs or writes the ledger, sends a
message, opens a browser, or treats an unknown commitment as resendable.

`scripts/hmasd_external_review.py` is a local Root-only helper:

```text
round-id --direction <id> --question-sha <sha> --evidence-sha <sha> \
  --workflow-version <version>
validate-prompts --round-dir <path>
partition-monitors --sessions <json> --count 1|2|3
validate-archive --operation-ref <json> --archive <json>
validate-archive --operation-ref <json> --archive <json> --out <tracked-json>
render-handoff-input --archive <json> --out <ignored-json>
```

Archive import is create-if-absent. It writes the source bytes exactly, fsyncs
the file and parent directory, accepts a concurrent same-response-SHA writer as
idempotent, and reports a different-SHA destination as a conflict. Archive
validation requires Agentify's native
`agentify_review_natural_completion_archive_v1`, verified natural completion,
at-most-once send counters, matching operation identity, and an exact
`responseSha256` over UTF-8 `responseText`. HMASD does not add
`schema_version`, `revision`, or `writer` to the foreign archive.

## Historical provenance

Existing material under `docs/external-review/rounds/` remains available for
lineage and comparison. It may contain the terminology and layout of the
previous workflow, but it is not a current prompt, archive, handoff, or state
input. New work must use the direction/round layout above.
