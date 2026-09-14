---
name: hmasd-chatgpt-pro-transport
description: "Execute or recover an author-owned Agentify Pro handoff: operate the bound browser tab, preserve at-most-one Send, and return the full archived response. Not scientific authorship or decision-making."
---

# Agentify Pro Transport

Complete the author's exact request and return its full response to the actual assigning parent.
Use the committed HANDOFF; keep its prompt, inputs, provider/model/effort, conversation binding,
idempotency key and response path unchanged during recovery. Historical parent/operator IDs are
provenance; the current native assignment supplies the return route. Owner pauses and actual
permission limits still apply. Editing this workflow does not authorize another Send.

The parent creates one Luna/high leaf Transport per request batch. Reuse that child through
same-request repair, observation and archive; a new independent request gets a fresh child with
fork_turns=none. Child lifetime and provider-conversation lifetime are separate. Do not author
science, spawn children, create an app relay or wait for a parent ACK.

## Keep the objects separate

Agentify is a browser controller with a strict review transaction, not a single readiness flag.
Use each interface for the facts it actually supplies:

| Object | Evidence | Does not establish |
| --- | --- | --- |
| Browser/tab | `agentify_status` / `agentify_tabs`: handle, key, URL, browser provenance, protection | Correct model, successful Send, or completed answer |
| Current page | `operator_observe` / action's `after`: controls, composer bytes, interaction revision | Persistent send history or full-response archival |
| Review operation | Exact operation receipt: immutable request identity, `sendAttempted`, paired message IDs | `false` does not mean an empty composer; `true` alone does not mean provider acceptance |
| Response artifact | Task-bound complete bytes, source, hash and size | A short chat receipt is not the GitHub research response |

Read [agentify.md](references/agentify.md) when using an interface or diagnosing a mismatch.
Use its field meanings rather than inferring semantics from a field name. An interface error
belongs to that interface until evidence connects it to another layer. Trust a tool's supported
receipt for its own facts; investigate a concrete contradiction, not every successful check.

## Normal path

1. **Load and claim once.** For existing-conversation GitHub handoffs, validate the fixed
   HANDOFF/TASK and packet with the current control checkout's `scripts/native_transport.py`.
   First-binding/attachment contracts use their corresponding route. Reuse a matching result on
   same-request continuation. Claim the exact binding in the shared registry from live
   `C:/Projects/HMASD/.codex/hmasd-transport.toml`; retain that claim until full archival. One
   writer per conversation, no lock held during browser waits. See [helper usage](references/agentify.md#handoff-and-binding).
2. **Use the bound tab.** Reuse known tab/key/URL facts; obtain only missing facts from Agentify.
   Send only on the dedicated non-protected tab. Any accessible logged-in surface is usable
   regardless of which task opened it, subject to the actual tool permissions. The strict query
   checks page, model/effort, exact composer and Send target itself. Do not precede a normal query
   with a separate model preflight, screenshot, manual paste or repeated readiness checklist.
3. **Run the appropriate operation branch below.** Preserve the returned receipt. A separate
   model preflight is a diagnostic for a specific unresolved model-control defect, not routine
   preparation or a post-repair confirmation required before every query.
4. **Observe, archive and return.** Continue the same request in bounded observation calls
   (at most 60000 ms per call). Normal generation and unchanged timeouts require no new claim,
   preflight, parent message or dispatch. Archive the full task-bound response, then return it.

## Send state determines the next action

These are decision cases, not new persisted schema fields or extra checks:

| Known state of this request | Next action |
| --- | --- |
| New authorized handoff; no earlier attempt or possible accepted effect | Start `agentify_review_query` with its exact inputs. |
| Exact operation has `sendAttempted=false` and no conflicting acceptance/history | Repair the specific pre-Send problem, then continue that operation with `verifyExisting=true`. The strict tool may Send. |
| `sendAttempted=true`, paired turn, or other possible acceptance | Never Send again. A matching strict operation with `true` may be continued using `verifyExisting=true` for observation/archive only. |
| Recovering a request whose operation/history is missing or contradictory | Use non-sending observation and reconciliation. Do not manufacture a new operation to recover the old one. |
| Full response already verified | Archive/return it; do not keep waiting on a stale page. |

A timeout or error label alone proves neither acceptance nor nonacceptance. A populated composer
may be an unsent draft left by a failed strict call. Preserve it; the strict query retains exact
existing text. Do not clear/re-paste it merely to restart the sequence. Never change immutable
arguments, reset the ledger, or use manual Send/ordinary query to escape a strict failure.

## Repair the failed interaction, not the whole workflow

Transport owns ordinary browser work: selecting/recovering its tab, waiting for page loading,
opening or closing a menu and correcting a known UI prerequisite. Use a current
`operator_observe` target, perform the scoped non-sending action, then inspect the returned
`after` state. Reuse that observation; do not immediately request the same state again.
Stale targets need a fresh observation. An unchanged failed action needs a concrete repair or
new evidence before repetition. No parent permission handshake is needed for these steps.

Use Computer Use when visual context would resolve an actual ambiguity. Match the real
browser/window/tab to the Agentify target; a same-URL page in another profile is not that tab.
Follow the Computer Use skill and its stop/permission rules. Its URL-identification failure is
not evidence of Agentify disconnection, failed login or failed Send. Do not switch tools to
bypass a rejected action. Screenshots clarify layout; they do not reconstruct send history.

Return a concrete missing capability or code defect to the parent DM: affected interface,
last completed boundary, observed state and needed repair. DM owns helper/adapter code and
acceptance; Clerk coordinates actual shared-runtime/writer dependencies. Ordinary repair is
not a Root ACK or scientific decision. Preserve the request for recovery. Conversation
replacement is exceptional; use [the existing replacement rules](references/state-schema.md#explicit-provider-conversation-replacement),
not a new tab/request as an error reset.

## Full response and direct return

Agentify already performs strict user/assistant pairing and completion sampling; do not add
another stability loop. Never click Stop, Retry, Regenerate or Continue as observation.
For GitHub delivery, preserve the chat receipt separately and retrieve the complete scoped
`RESPONSE.md` at its immutable delivery commit, or the task's paired downloadable fallback.
On strict pairing/archive failure, check that GitHub scope and delivery comment before claiming
no answer exists; check again at natural completion if it was previously absent. A verified
task-bound GitHub answer may be returned with provider IDs null. Never invent IDs or bytes.

Verify archive source/hash/size, preserve conflicting candidates without overwrite, and use the
existing `native_receipt` helper to send one factual native message to the actual parent:
request, effect, operation/pairing, full archive, cleanup and any concrete missing fact.
Completion, material conflict and no-current-work are reportable boundaries; unchanged waiting
is not. Record the actual delivery outcome and preserve earlier receipts. Native final closes
the same assignment; when messaging is unavailable, it is the direct return, not an app relay.
Close only owned non-protected tabs after pending work is secured under the applicable cleanup
rule. The parent reads the full review and owns scientific intake.

[state-schema.md](references/state-schema.md) is for helper calls, archive fields and historical
record reconciliation. Its legacy state names are storage compatibility, not extra UI steps.
