---
name: hmasd-chatgpt-pro-transport
description: "Use when an author-owned native Transport executes or recovers an exact Agentify Pro handoff, from one preflight through Send or observation, immutable archive and direct parent receipt."
---

# Native Agentify Pro Transport

The author DM owns one reusable native Luna/high leaf Transport. Root uses this route for its
own Portfolio vacancy request. Execute the assigned request; the author reads the full answer
and decides scientific/specification conformance. The current native assignment supplies the
direct return parent. Preserve frozen HANDOFF IDs as provenance when recovering an older request.
No singleton app task, relay, ACK loop, new scientific prompt or science selection belongs here.

## DM-local repair default

Transport failures that are engineering defects (selector/model aliasing, tab binding,
preflight state, receipt handling or workflow sequencing) are owned by the author DM by default.
The DM may patch its direction-owned Transport helpers, fixtures and related skill/control
instructions in place, run proportional focused tests and independent review, and recover the
same unchanged operation when the effect is verified nonacceptance. Preserve the original
operation, prompt hash, idempotency key, binding and all failure receipts. Do not create a
replacement request or alter scientific meaning. Escalate to Root only when the repair requires a
shared application runtime/load, a cross-direction resource or a scientific/Portfolio decision;
Root then coordinates that dependency while the DM retains Transport acceptance.

## Unrecoverable-conversation fallback

If the original conversation cannot be recovered after the supported same-request repair path,
the author DM may use a new conversation only when the old operation is positively verified as
`sendAttempted=false` with no provider pairing or accepted effect. Record the old operation as
`VERIFIED_NONACCEPTANCE / CONVERSATION_UNRECOVERABLE` and preserve its HANDOFF, prompt hash,
idempotency key, tab facts and receipts. Then create a new handoff/conversation and idempotency
key carrying the identical scientific prompt and frozen inputs, bind it as a new operation, and
link both records. This is a recovery rebind, not a resend of an uncertain effect. Never use this
fallback when `sendAttempted=true`, acceptance is unknown, or any provider pairing may exist; in
those cases observe and reconcile the original operation only.

For a failed initial homepage operation with no registry binding, use
`bind_conversation.prepare_unaccepted_first_binding_rebind` with the validated replacement
request and the fresh preserved operation audit. It reserves one deterministic generation,
retains the prior audit in request history, and admits only explicit OWNER_DIRECT recovery with
identical prompt/model/effort. It does not invent or quarantine a conversation UUID. Then use
normal firstBinding and bind only the actual post-Send URL with the same reset evidence.
An existing binding requires its own reconciliation or concrete-context replacement route.

## One preflight, one action, one return

```text
READY_UNSENT --strict query--> SEND_ATTEMPTED
    ^                           | verified pre-Send failure
    +------ repair same input --+
                                | uncertain effect / accepted
                                v
                             OBSERVE --full bytes verified--> ARCHIVE --> RECEIPT
```

1. **Preflight once.** Read the committed HANDOFF and fixed TASK bytes, validate its logical
   manifest, prompt hash/path and caller/parent/operator IDs. For GitHub handoffs on an existing
   conversation use
   `scripts/native_transport.py` with full `--handoff-sha`, repository-relative `--handoff-path`,
   current `--parent`, `--operator`, `--assignment`, and immutable `--out`; pass existing
   `--manifest` and `--prompt` together. It validates frozen routing separately from the current
   native child route. New requests still use `REUSE_DM_TRANSPORT`; historical requests are never
   rewritten to fit current configuration. First-binding uses the existing route in agentify.md;
   this recovery helper rejects it. Explicit attachment contracts retain their input mode.

   Read the absolute registry from live `C:/Projects/HMASD/.codex/hmasd-transport.toml`.
   `--claim-registry` makes one brief locked claim of the exact request/binding. A different
   unfinished request or live executor is a real writer conflict. Keep ownership through failure,
   uncertainty and generation; release only after full archival. Never hold the file lock across
   a browser wait. [State records](references/state-schema.md) preserve earlier evidence.

   Reuse the matching Agentify operation and its original arguments. Inspect one clear screenshot
   with CUA when useful to understand the real page; one scoped UI sample is enough. Read the
   actual composer/model/current response, excluding sidebar titles and historical receipts.
   Screenshot interpretation is a human observation, not OCR or proof of Send history. Supplement
   only missing hidden facts: exact conversation, dedicated tab key, protected-tab exclusion and
   persisted operation. Any accessible logged-in surface is usable regardless of its task owner.
   Send uses a dedicated non-protected Agentify tab with the recorded stable key. Require
   GPT-6 Astra (verified `Latest`) and `Pro`, not merely an account subscription. Strict query
   already checks its target before Send; call separate non-sending preflight only for an unresolved
   or repaired model/tab fact. Do not repeat identity, DOM or model-menu checks without new evidence.

2. **Take the unique effect branch.** Use `next_step` or its rule below, recording the exact
   operation receipt. A timeout or failed tool label alone does not prove nonacceptance.

   | Effect | Evidence | Only next action |
   | --- | --- | --- |
   | VERIFIED_NONACCEPTANCE | Same request, no acceptance evidence; strict operation explicitly `sendAttempted=false`, or positively reconciled never-Send history | Repair the failed fact, then continue this same unchanged operation once. No extra parent confirmation. |
   | UNCERTAIN_EFFECT | `sendAttempted=true` without a paired user turn, missing/unknown operation history, or another possible accepted effect | Non-sending reconciliation/observation of this request. Never create a new operation or change its idempotency key. |
   | ACCEPTED | Exact current request paired with provider user/assistant identity or verified archive | Observe/archive that response only. |

   `agentify_review_query` preserves its operation on pre-Send failure: changing only the repaired
   `existingTabId` can recover TAB_KEY_MISMATCH. Keep prompt/hash, provider/model/effort,
   binding/conversation, response path and idempotency key fixed. `verifyExisting=true` can still
   Send when its operation says false; it is observation-only only after true. If the operation
   is absent or effect uncertain, use non-sending tools, not a new strict query. Exact interfaces
   and first-binding exceptions are in [agentify.md](references/agentify.md).

3. **Observe and archive.** Bound each observation call to at most 60000 ms. Continue the same
   request while work is in progress; unchanged observations need no new inventory/preflight,
   parent message or polling relay. Report a concrete external prerequisite once and retain
   same-request recovery. Never click Stop, Regenerate or Continue as natural observation.
   Agentify's two stable completion samples and exact user/assistant pairing protect completeness;
   do not add another independent stability loop.

   Save exact assistant UTF-8 bytes and its hash/size receipt. In GitHub delivery this may be only
   the short chat receipt: obtain the full scoped RESPONSE.md at the immutable delivery commit,
   or its paired downloadable fallback. Keep these separate; never overwrite the operation's
   fixed responsePath to rename a historical attempt. Preserve full answer source, paired IDs,
   path/hash/size and Git commit (or download evidence). A conflicting file is ARCHIVE_CONFLICT:
   retain both candidates and return the conflict. Delivery failure alone does not erase a formed
   decision. Never synthesize a missing GitHub response.

   On strict pairing/archive failure, check the fixed GitHub response scope and its delivery
   comment; check again at natural completion if the earlier target was absent. Page absence is
   not GitHub absence. Read response bytes at the observed full commit, verify the Git blob/hash/
   size and comment pairing to the exact fixed TASK. `verify_github_pairing` tests this route.
   A complete task-bound GitHub response can be archived/returned with provider IDs still null;
   retain the strict mismatch instead of inventing IDs or waiting on a stale page after delivery.

4. **Return once.** Verify the full archive, stage `native_receipt` for the current direct parent,
   then send one factual `collaboration.send_message` with request/binding, effect, operation,
   paired IDs, full archive source/hash/size, cleanup and missing facts. Record the actual tool
   outcome. Delivered or uncertain receipts are reconciled without repetition; a rejected-before-
   delivery receipt may recover to the same parent. Native final closes this same assignment,
   not a second dispatch. No ACK is required. Close only owned non-protected tabs after the
   archive or exact recoverable conversation is secured. The parent performs full scientific intake.

   At completion, a material conflict, or no-current-work while the direction remains ACTIVE,
   send one direct native action message before ending: assignment, status, evidence/commit and
   next step. `stage_native_receipt` supports COMPLETE, CONFLICT and NO_CURRENT_WORK; only COMPLETE
   requires the full archive. UNCHANGED_WAIT stages nothing. Preserve earlier boundary receipts
   when a later changed boundary occurs. Active generation is ongoing work, not a reason to end
   as blocked. The author DM sends the same concise action update to Root at its own boundary;
   ordinary unchanged waits remain silent. A missing archive never prevents reporting a real conflict.
   If this runtime lacks `collaboration.send_message`, return those same actionable fields once
   in native final, which reaches the assigning parent directly. Record `transport=native_final`
   and the actual native outcome; do not invent a tool success, create an app relay or require
   another handshake. Tool availability does not hold a verified full answer away from its author.
