---
name: hmasd-chatgpt-pro-transport
description: Send one committed HMASD Pro question in the direction's ChatGPT conversation through Agentify, wait for completion, verify the answer landed in NOTES.md through the GitHub connector (or save the page text), close the tab and return facts. Never science, never a resend.
---

# Pro transport (Agentify)

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 5. Input: the exact message text,
the conversation URL (or "new"), the direction id, the branch and the sha. Output: facts.
One send per question. Provider policy and retired conversation ids: `.codex/hmasd-transport.toml`.

## Steps

1. **Tab.** `agentify_tabs`; use or create one dedicated non-protected tab for this
   conversation with `stableKey = <direction id>`. Navigate to the URL, or the provider root
   for a new conversation. Never send from a protected or default tab. One writer per
   conversation at a time.
2. **Preflight.** `agentify_review_preflight` on that tab: product GPT-6 Astra (shown as
   Latest) with Pro effort. Repair the tab or model selection, never the message. Do not repeat
   a passed check.
3. **Send once.** `agentify_review_query` with `idempotencyKey = sha256(direction + sha +
   section heading)`, the exact prompt, and the conversation. The tool attempts at most one
   send per operation. Read its result:
   - `sendAttempted=false` with an error: repair the named fact (tab key, model) and reuse the
     same operation once.
   - `sendAttempted=true`, or unknown: never call `review_query` again; observe only.
4. **Wait.** `agentify_wait_response` in calls of at most 60 s until COMPLETE (stable assistant
   text across two samples, no Stop, Continue or Retry control). Unchanged waits are silent.
   Never click Stop, Regenerate or Continue.
5. **Verify delivery.** `git fetch` the branch. The `### Answer` subsection of the named
   `NOTES.md` section must contain the answer at a new commit; record that sha. If it is absent
   after completion, save the exact assistant text (`agentify_read_page` or
   `agentify_save_artifacts`) to `temp/directions/<direction>/pro/<date>_<slug>.md` and return
   it with "connector write failed".
6. **New conversation.** Record the resulting conversation URL for the DM's `NOTES.md` header.
7. **Close and return.** `agentify_tab_close` the owned tab. Return: conversation URL, send
   effect (sent, uncertain, failed), completion state, answer commit sha or saved text path,
   tab closed, unresolved facts.

## Recovery

An error string, a stale DOM or a timeout does not prove the send failed. Reconcile on the same
conversation: read the current messages and generation state; if the exact prompt is already
submitted, observe its response. Ineffective clicks follow
[send-hit-point-recovery.md](references/send-hit-point-recovery.md). Tool interfaces and the
completion test are in [agentify.md](references/agentify.md). A human-required login, an
inaccessible provider or a CAPTCHA is reported plainly and stops this send; it does not create a
new question, a new conversation or a resend.
