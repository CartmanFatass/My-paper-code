# Agentify strict review interface

Historical basis: parent-frozen request and leaf transport in the pre-bd1ecac2a
hmasd-agentify-transport skill. Current implementation is C:/Projects/agentify-desktop/
mcp-server.mjs and review-transport.mjs; current callable tool schemas prevail over old examples.

- Use one tab inventory plus one scoped screenshot/UI sample when those facts are missing.
  agentify_tabs({}) and agentify_status({tabId}) expose hidden key/protection and exact tab facts;
  they are not repeated checkpoints. CUA may clarify the actual composer/current response.
- agentify_review_preflight({tabId, productModel, reasoningEffort, timeoutMs:60000}) checks the
  inspected tab without Send. Product is GPT-6 Astra or visibly verified Latest; effort is Pro.
  Strict query already performs target preflight. Call this separate tool only to resolve an
  unknown or repaired tab/model fact; do not repeat successful checks for confirmation.
- agentify_review_query({stableKey, provider:"chatgpt", productModel, reasoningEffort:"Pro",
  conversationUrl, conversationId, idempotencyKey, prompt, responsePath, existingTabId,
  timeoutMs:60000}) persists the strict operation and attempts at most one Send. promptPath is an
  alternative UTF-8 text source; never supply both. Optional promptSha256 checks exact input.
- Persisted `sendAttempted=false` after TAB_KEY_MISMATCH is a pre-Send failure. Repair the
  dedicated keyed tab and reuse this operation, changing only existingTabId; there is no new
  request or approval step. Preserve earlier error receipts. A true value is written before
  the external click and prevents the strict controller from sending again on continuation.
- A first binding uses provider root URL, conversationId="__new__", firstBinding=true and a
  dedicated clean inspected tab. Preserve these original operation arguments on continuation;
  retain the concrete observed conversation identity separately from first-binding input.
- For an existing exact operation with sendAttempted=true, repeat review_query with identical
  immutable arguments and verifyExisting=true for strict observation/archive continuation.
  If sendAttempted=false, this call may Send. If no exact Agentify operation exists (for example
  a prior CUA Send), verifyExisting is not an import mechanism; do not create an operation to
  observe a previously accepted provider request.
- agentify_wait_response({tabId,timeoutMs:60000}) never sends. IN_PROGRESS means continue waiting;
  COMPLETE supplies observation, not the strict immutable archive receipt. Use for read-only
  reconciliation, preserving expected conversation/user/assistant identity. It cannot establish
  a request binding merely from the latest answer. Use operator_observe/read_page and save_artifacts
  as available for matching existing response evidence; preserve byte hashes and exact source.

Strict completion requires matching assistant identity/hash across snapshots at least three
seconds apart and no Stop/Continue/Retry controls. Verified archive metadata includes path,
sha256, sizeBytes and projection=exact. Preserve the returned receipt verbatim. A GitHub task's
short chat reply is not the full research response. Save the immutable scoped GitHub artifact or
paired downloadable answer separately.
These are the single strict completion test, not a reason for another operator stability loop.
Only current response/composer controls count: sidebar chat titles containing Continue/Stop or
historical answers do not establish generation or completion for this request.

Agentify serializes per tab/controller, not all tabs sharing a conversation. Enforce one active
writer per binding in the shared absolute registry_path from the live control-checkout config
before any mutation; never resolve that registry relative to a direction worktree. Separate conversations
may progress concurrently. Protected/default tabs are read-only inspection surfaces.
Do not use removed agentify_review_observe, ordinary agentify_query as a strict-Send shortcut,
or break-glass agentify_stop_query during normal observation.

## Binding generations

HMASD conversation_binding_key remains the scientific node identity. Agentify stableKey identifies
one concrete provider-conversation generation of that node. Persist the exact agentify_stable_key
alongside the current shared registry binding and reuse it for every request in that generation.
For an existing Agentify binding, recover its recorded key; never change it for a retry, timeout,
new DM, or ordinary next round. Preserve operation arguments and receipts in request history.

Only after the explicit provider-conversation replacement rules in state-schema.md admit a new
generation, use the reset helper's distinct deterministic stableKey before the firstBinding call:
hmasd-gen: plus SHA-256 of the JSON-encoded [node key, replacement request ID]. This stays within
Agentify's 128-character key limit even for long direction/request names. Keep the previous key/operation/receipt
with its old generation. Repeated replacement preparation reuses the recorded new key; never
reset/delete Agentify state or reuse the old bound key with firstBinding=true. An unknown or
accepted operation still requires its original non-sending reconciliation. This mapping does
not authorize a replacement or a Send by itself.
