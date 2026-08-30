# HMASD External Review Workflow

This directory contains durable external-review prompts and exact raw archives
imported from Agentify. The active protocol is keyed by direction, canonical
frozen round, review stage, and provider. Historical layouts remain immutable
provenance and are never parsed as active workflow state or resend authority.

## Active layout

```text
docs/external-review/directions/<direction-id>/<canonical-round-id>/
├── PRO_INNOVATOR_PROMPT.md
├── PRO_CONVERGENCE_PROMPT.md
├── pro_innovator/
│   └── <provider>/
│       └── NATURAL_COMPLETION_ARCHIVE.json
└── pro_convergence/
    └── <provider>/
        └── NATURAL_COMPLETION_ARCHIVE.json
```

A future archive directory is populated only after the corresponding exact
Agentify operation returns a verified natural-completion archive. The stage is
part of the destination, so Innovator and Convergence can coexist for the same
direction, canonical round, and provider without sharing a path.

A round is identified by the first 20 hexadecimal characters of:

```text
sha256(direction_id + "\n" + question_sha256 + "\n" +
       evidence_set_sha256 + "\n" + workflow_version)
```

A future operation ref binds all four frozen inputs, its recomputed canonical
round ID, `review_stage` in `pro_innovator` or `pro_convergence`, provider, and
the exact stage-owned destination. Changed question, evidence, or workflow bytes
create a different round identity; a transposed or caller-supplied noncanonical
ID is rejected.

## Two-stage provider sequence

1. Freeze the question, evidence, workflow version, and canonical round ID.
2. Author the neutral Pro Innovator prompt without EM conclusions or another
   provider result. Root requests the one exact `pro_innovator` operation.
3. Treat committed or uncertain operations as observe-only. Continue to observe
   the same Agentify operation and conversation; never resend or replace it.
4. Complete local EM research and durable synthesis.
5. Author the Pro Convergence prompt from that synthesis and declared evidence.
   Root requests its distinct exact `pro_convergence` operation.
6. Import exact archive bytes to the stage-owned path. Temporary Artifact Writer
   input remains ignored; EM owns scientific intake and index CAS updates.

Provider output is evidence, not authority for Portfolio choice, implementation,
scientific acceptance, research lifecycle, or claim ceiling. The common v1
transport envelope and all Agentify at-most-once mechanisms remain unchanged.

## Root-only archive boundary

Agentify's Schema-v2 ledger is the sole authority for browser submission,
idempotency, send counts, fingerprints, and commitment. HMASD stores operation
references and validates exact archives; it never reconstructs or writes the
ledger, sends a message, opens a browser, or treats unknown commitment as
resendable.

`scripts/hmasd_external_review.py` exposes the local Root-only helpers:

```text
round-id --direction <id> --question-sha <sha> --evidence-sha <sha> \
  --workflow-version <version>
validate-prompts --round-dir <path>
partition-monitors --sessions <json> --count 1|2|3
validate-archive --operation-ref <json> --archive <json>
validate-archive --operation-ref <future-json> --archive <json> --out <tracked-json>
render-handoff-input --archive <json> --out <ignored-json>
```

Read-only `validate-archive` accepts either a canonical future ref or a committed
legacy ref. It validates the provider/session/operation/idempotency/stable
identity, exact archive SHA-256, verified natural completion, at-most-once send
counters, and exact `responseSha256` over UTF-8 `responseText`.

The `--out` import route accepts future refs only. It rejects missing or unknown
stages, noncanonical tuple IDs, wrong providers, and wrong stage-owned paths
before destination creation. Import is create-if-absent: it writes the source
bytes exactly, fsyncs the file and parent, treats identical existing bytes as
idempotent, and reports any different exact bytes at the same stage destination
as a conflict. HMASD adds no `schema_version`, `revision`, or `writer` fields to
the foreign archive.

## Index v2, v3, and historical provenance

External-index v2 remains valid. V3 retains active `rounds` and adds the
separate append-only `historical_archives` array. A generic v2-to-v3 migration
adds only `historical_archives: []` and increments revision once; it creates no
round, disposition, provider effect, prompt, operation, or historical fact.
Historical records bind the observed and recomputed canonical round IDs,
question/evidence hashes, stage/provider, operation identities, completion, and
exact legacy archive/response refs. They can never appear in active `rounds`.
Existing records form an immutable prefix; later verified records may only be
appended.

Committed legacy refs use the old path:

```text
docs/external-review/directions/<direction-id>/<observed-round-id>/<provider>/
  NATURAL_COMPLETION_ARCHIVE.json
```

They are exact-byte validate-only provenance. They can never create, import, or
send even when that destination is absent, and their operation refs, archive
bytes, response bytes, identities, counts, commitments, and hashes are never
moved, copied, rewritten, or synthesized. Existing material under
`docs/external-review/rounds/` is likewise historical-only.
