# HMASD External Review Workflow

This directory contains durable external-review prompts, exact raw assistant
responses, and separate immutable operation receipts. The current protocol is
keyed by direction, canonical frozen round, review stage, and provider.
Historical layouts remain inert bytes and are never loaded or parsed as current
workflow state.

## Active layout

After a stage has passed disposable validation and durable registration, its
canonical immutable prompt, raw response, and operation receipt use this
layout:

```text
docs/external-review/directions/<direction-id>/<canonical-round-id>/
├── pro_innovator/
│   ├── PRO_INNOVATOR_PROMPT.md              # registration creates it
│   └── <provider>/
│       ├── response.md                       # exact raw assistant UTF-8 bytes
│       └── operation_ref.json                # immutable current receipt
└── pro_convergence/
    ├── PRO_CONVERGENCE_PROMPT.md             # absent until registration
    └── <provider>/
        ├── response.md
        └── operation_ref.json
```

Before registration, a stage prompt exists only as disposable input outside
this canonical layout. Failed validation creates no canonical prompt, canonical
path, active round, or external-index fact. The stage is part of the archive
destination, so Innovator and Convergence can coexist for the same direction,
canonical round, and provider without sharing a path.

A round is identified by the first 20 hexadecimal characters of:

```text
sha256(direction_id + "\n" + question_sha256 + "\n" +
       evidence_set_sha256 + "\n" + workflow_version)
```

A current schema-v3 operation ref binds all four frozen inputs, its recomputed
canonical round ID, `review_stage`, provider, separate `product_model` and
`reasoning_effort`, immutable operation/idempotency/fingerprint, exact
conversation and message identities, orthogonal transport tuple, and exact raw
response path/SHA/size. Current ChatGPT operations require product model
`GPT-5.6 Sol` and reasoning effort `Pro`. Changed question, evidence, or
workflow bytes create a different round identity; a noncanonical ID is rejected.

## Stage-safe provider sequence

1. Freeze the question, evidence, workflow version, and canonical round ID.
2. Author one neutral disposable Pro Innovator prompt without EM conclusions or
   another provider result. Validate that one stage prompt before registration.
   On validation failure, leave no canonical path, active round, or index fact.
3. Durably register the validated Innovator. Before canonical publication, one
   content-addressed transaction journal under ignored `.omp/runtime` fsyncs
   the exact old/new v4 index hashes and staged bytes, prompt hash and staged
   bytes, writer, paths, stage, round, and expected revision. Publication then
   links the exact prompt bytes and expected-revision replaces only the
   `pro_innovator` prompt slot. This creates the active round with
   `pro_convergence` still null. Registered prompt bytes and references are
   immutable.
4. Root requests the one exact `pro_innovator` provider-visible user message.
   Proven-zero reversible pre-boundary UI failures repair within the same
   assignment and operation. Uncertain activation is sealed and observe-only;
   continue to observe the same Agentify operation and conversation, never
   activate again.
5. Complete local EM research and durable synthesis. Only after its durable ref
   and canonical Innovator prompt references exist may the separate Pro
   Convergence prompt be authored, validated, and registered.
6. Validate that one disposable Convergence stage prompt. Its journaled
   registration publishes exact bytes to
   `pro_convergence/PRO_CONVERGENCE_PROMPT.md` and expected-revision inserts only
   the `pro_convergence` prompt slot. Root then requests its distinct exact
   `pro_convergence` operation.
7. Fingerprint and reread exact raw `response.md`, match it to the immutable
   current operation receipt, and publish separate `operation_ref.json`.
   Temporary Artifact Writer input remains ignored; EM owns scientific intake
   and index CAS updates.

Registration entry and the explicit `recover-registration` command observe the
exact journal, v4 index, canonical prompt, and staged blobs. An early transaction
with exact old index and no canonical prompt deterministically restores the old
terminal state. Once any exact canonical publication is observed, recovery
rolls forward from journal-bound bytes to exact new index plus exact prompt.
Repeated recovery is a no-op. Wrong bytes, identity/hash collision, or any
irreconcilable observation is `UNKNOWN`; recovery does not rewrite canonical
bytes or make a semantic choice. Provider output remains evidence, not
authority for Portfolio choice, implementation, scientific acceptance,
research lifecycle, or claim ceiling.

## Root-only response boundary

Agentify's current Schema-v3 ledger is the sole authority for browser
submission, immutable operation/idempotency/fingerprint, transport tuple,
capability, counters, exact message identities, and archive receipt. HMASD
stores a separate immutable operation ref and validates exact raw response
bytes by path, SHA, size, and reread. It never reconstructs or writes Agentify's
mutable ledger, parses transport identity from response content, treats raw
bytes as a JSON transport envelope, sends a message, opens a browser, or treats
unknown commitment as resendable.

`scripts/hmasd_external_review.py` exposes exactly three current Root-only CLI
operations:

```text
validate-prompt --review-stage pro_innovator|pro_convergence --prompt <disposable-path> \
  --external-index <index> --direction <id> --round-id <canonical-id> \
  --question-sha <sha> --evidence-sha <sha> --workflow-version <version> \
  [--local-synthesis-ref <json>] [--innovator-prompt-ref <json>]
register-prompt --review-stage pro_innovator|pro_convergence --prompt <disposable-path> \
  --external-index <index> --direction <id> --round-id <canonical-id> \
  --question-sha <sha> --evidence-sha <sha> --workflow-version <version> \
  --prompt-sha <sha> --expected-revision <revision> \
  [--local-synthesis-ref <json>] [--innovator-prompt-ref <json>]
recover-registration --transaction-id <sha256>
```

`validate-prompt` accepts one disposable prompt for its declared stage and
creates no journal, canonical prompt, directory, round, or external-index fact.
`register-prompt` is the sole registration authority. It validates exact input
bytes and stage ordering, requires v4 and expected revision, durably creates the
content-addressed transaction, and publishes only that stage's immutable prompt
and index slot. Innovator registration leaves Convergence null. Convergence
validation and registration require durable synthesis and canonical Innovator
references. `recover-registration` accepts only the exact transaction ID and
can neither resend nor choose new bytes. Historical bytes have no current CLI,
loader, validator, registration, import, transition, or emission route.

## Index v4 and inert historical bytes

Current external-review workflow accepts v4 only. The current index contains
active `rounds` and no historical-record collection. Each provider slot carries
only the current orthogonal transport fields and exact current refs.

Older layouts and files may remain tracked as historical evidence, but they are
inert bytes. They cannot be loaded, validated as current, registered, imported,
transitioned, emitted, copied into current paths, or used for active rounds,
provider effects, prompt authority, archive identity, or resend authority.
