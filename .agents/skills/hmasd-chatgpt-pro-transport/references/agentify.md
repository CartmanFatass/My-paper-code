# Agentify strict review interface

Implementation: `C:/Projects/agentify-desktop/` (`mcp-server.mjs`, `review-transport.mjs`).
The callable tool schemas prevail over this note.

- `agentify_tabs({})` and `agentify_status({tabId})` expose tab identity, protection and the
  stable key. Protected or default tabs are read-only inspection surfaces; send only from a
  dedicated non-protected tab keyed by the assigned subject key (direction id or portfolio).
- `agentify_review_preflight({tabId, productModel, reasoningEffort, timeoutMs:60000})` checks
  the tab without sending. Product is GPT-6 Astra (the picker may show `Latest`); effort is
  `Pro`. An account badge alone is not proof; the composer's current model and effort must be
  paired. Call it once, or again only after a repair.
- `agentify_review_query({stableKey, provider:"chatgpt", productModel, reasoningEffort:"Pro",
  conversationUrl, conversationId, idempotencyKey, prompt, responsePath, existingTabId,
  timeoutMs:60000})` persists one strict operation and attempts at most one send. `promptPath`
  is an alternative text source; never supply both. Persisted `sendAttempted=false` after an
  error (for example `TAB_KEY_MISMATCH`) is a pre-send failure: repair the keyed tab and call
  again with the same arguments and the repaired `existingTabId`. `sendAttempted=true` is
  written before the external click; from then on only observe. For a new conversation use
  the provider root URL, `conversationId="__new__"` and `firstBinding=true` on a clean tab,
  and record the observed conversation URL afterwards.
- After sendAttempted=true or uncertain acceptance, this workflow uses wait_response and
  read_page to observe the same operation; do not call review_query again to recover it.
- `agentify_wait_response({tabId, timeoutMs:60000})` never sends. `IN_PROGRESS` means keep
  waiting; `COMPLETE` is the observation. Strict completion needs matching assistant text
  across two samples at least three seconds apart and no Stop, Continue or Retry control in
  the current response area; sidebar titles and older answers do not count.
- `agentify_read_page` and `agentify_save_artifacts` capture the exact assistant text when the
  GitHub connector write did not land; keep the hash and source.
- Do not use plain `agentify_query` as a send shortcut, and do not use `agentify_stop_query`
  during normal observation.

Agentify serialises per tab and controller. Separate conversations may proceed concurrently;
one conversation has one writer at a time.
