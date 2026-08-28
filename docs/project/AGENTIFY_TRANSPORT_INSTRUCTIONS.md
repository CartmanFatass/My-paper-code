# HMASD strict Agentify transport

This is the sole current mechanics reference for HMASD external consultations. It assumes the
trusted local Codex Desktop project. It creates no HMASD authentication, receipt, operation ledger,
task registry, retry state machine, or UI control checklist.

## Ownership

The parent writes the complete exact UTF-8 prompt before dispatch and supplies its path, review
mode/purpose, required provider and visible model, archive path, one operation label, observation
bound, and stop condition. For research review, EM owns all scientific prose and includes only the
needed GitHub remote, origin-reachable commit, repository-relative refs, evidence, question, and
limits. Repository code is a scientific reference, not a request for general code review.

The transport must not compose, summarize, append, truncate, translate, or rewrite the prompt. It
must not paste a `[WORK]`, `[RESULT]`, state table, JSON packet, or machine heading into the provider
conversation. It owns only send, provider-visible fidelity, natural-completion, response-availability,
and exact-archive facts.

## One strict send

1. Read the exact frozen prompt file and reject an empty or unreadable file before any send-capable
   call.
2. Derive one immutable `idempotencyKey` and one `stableKey` for this operation. Compute the exact
   prompt SHA-256 only because `agentify_review_query` requires `promptSha256`. These values remain
   tool-local and are never copied into HMASD workflow state or used as task identity.
   A temporary stale view, redirect, or unreadable readiness control receives bounded non-sending
   recovery while each action has a new evidence-based reason. Do not block on the first stale view,
   and do not loop or follow a fixed UI checklist when no new information is available.
3. When the required inputs and provider/model readiness are established and no user waiver applies,
   call `agentify_review_query` exactly once with `promptPath`, the tool-local `promptSha256`, exact
   provider/model, exact conversation binding, the two keys, and one bounded `timeoutMs`. A failed
   precondition stops before any send-capable call; a valid unwaived assignment is not silently left
   unsent. For a first ChatGPT binding use the provider root, `conversationId=__new__`, and
   `firstBinding=true` as required by the tool. For an existing binding use only its exact registered
   conversation.
4. Never make a second send-capable call. The Send path must not use ordinary `agentify_query`. It
   must not activate Retry, Continue,
   Answer-now, Stop-and-resend, or any other response-producing control.

For Pro research, require visible model `GPT-5.6 Pro`. The owner prompt may direct Pro to use its
GitHub connector. Innovator/Convergence evidence separation is already frozen by EM and must not be
changed by transport.

## Non-sending observation and full-response recovery

After a send-capable call, every further action is tied to the same exact operation and cannot send:

- use `agentify_review_observe` for a durable no-send observation; or
- call `agentify_review_query` with `verifyExisting=true` and the exact same binding, keys,
  `promptPath`, `promptSha256`, provider, and model.

Observe only until natural completion or the assigned bound. A clipped tool display, response
prefix, mode label, loading screen, or generated-but-unreadable page is not a complete answer. Use
the same no-send observation to recover the full assistant turn. Never replace it with a summary and
never open a fresh operation to obtain missing text.

Renaming the WORK, assignment, operation, key, conversation, leaf, or task never authorizes another
send of the same owner-frozen request to the same provider. Consult native history and the prompt;
do not create a local cross-task ledger.

Before mapping any state, collect these strict operation facts when they are available:

- how many requests the provider received;
- whether the provider-visible user turn equals the exact frozen prompt file;
- which provider and visible model are evidenced;
- whether generation reached natural completion; and
- whether the complete assistant turn, not a truncated prefix, is available and archived with the
  exact prompt at the owner-supplied path.

Archive the exchange verbatim enough to preserve the complete owner prompt and complete provider
response plus provider/model/conversation facts. Do not add scientific or engineering conclusions.

## Return mapping

`AGENTS.md` is the only human-readable glossary for transport state names and meanings. Select the
one existing state whose definition matches the strict tool evidence; do not restate the glossary or
invent a synonym here. Mechanics-specific decisions are limited to these cases:

- an error without strict proof of zero provider request and zero operation cannot use the
  zero-send state;
- a confirmed provider-visible prompt difference uses the input-mismatch state and stops that
  operation;
- a clipped or unavailable complete assistant turn cannot use the complete state; and
- an unknown or sent operation receives only same-operation non-sending observation.

Return the leaf's own state field, direct fact, locator, archive path or `NONE`, and limitations. Do
not map it to scientific status, technical acceptance, Portfolio action, lifecycle, or assignment
cancellation.
