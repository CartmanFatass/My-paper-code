# Agentify strict review interface

Implementation: `C:/Projects/agentify-desktop/` (`mcp-server.mjs`, `review-transport.mjs`).
The callable tool schemas prevail over this note.

On the WSL host the same Windows application is driven through `node.exe` over WSL interop
(`.codex/config.toml` on the `wsl` branch; Claude user-level MCP entry). The server and the
application are Windows processes, so a path argument must be one Windows can open: pass
`prompt` inline, and give `responsePath` (or a `promptPath`) as `wslpath -w <posix path>`,
for example `\\wsl.localhost\Ubuntu-24.04\home\fires\hmasd-wsl\temp\sessions\...`. Agentify
fingerprints that spelling as the POSIX path. A bare `/home/...` path is resolved by a Windows
process against its own drive, not against this checkout.

- `agentify_tabs({})` and `agentify_status({tabId})` expose tab identity, protection and the
  stable key. Protected or default tabs are read-only inspection surfaces; send only from a
  dedicated non-protected tab keyed by the committed question, as described in SKILL.md.
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
- After confirmed sendAttempted=true, wait_response/read_page normally suffice. If native
  pairing or exact response recovery is needed, review_query with the same immutable
  arguments and verifyExisting=true observes the existing operation without sending.
  verifyExisting alone is not a no-send guarantee: sendAttempted=false can still send.
  For unknown state reconcile first; never create an operation to observe a prior manual Send.
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
