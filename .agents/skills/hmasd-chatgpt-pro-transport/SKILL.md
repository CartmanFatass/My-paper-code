---
name: hmasd-chatgpt-pro-transport
description: Send one committed HMASD Pro question in the assigned ChatGPT conversation through Agentify, wait for completion, read the complete answer at the assigned repository target (or preserve a complete chat fallback), close the tab and return facts. Never science, never a resend.
---

# Pro transport (Agentify)

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 5. The existing assignment carries
exact message text, conversation URL (or "new"), subject key (direction id or `portfolio`),
repository, branch, source_sha, target_path, question_heading and answer_heading. These are
fields in the assignment, not another record or registry. Output: factual delivery evidence.
Direction questions target NOTES.md; owner-triggered Portfolio questions target RESEARCH.md.
Do not infer the target from the role name. Read the pinned question and confirm that its
answer subsection is empty and the heading uniquely identifies this question before sending.
One send per question. Provider settings and historical exclusion data come from
`.codex/hmasd-transport.toml`; historical registry state is not used for new requests.

## Steps

1. **Tab.** `agentify_tabs`; use or create one dedicated non-protected tab for this
   conversation with `stableKey = <subject key>`. Navigate to the URL, or the provider root
   for a new conversation. Never send from a protected or default tab. One writer per
   conversation at a time.
2. **Preflight.** `agentify_review_preflight` on that tab: product GPT-6 Astra (shown as
   Latest) with Pro effort. Repair the tab or model selection, never the message. Do not repeat
   a passed check.
3. **Send once.** `agentify_review_query` with `idempotencyKey` derived from an unambiguous encoding of
   repository, branch, subject key, source_sha, target_path and question_heading, the exact prompt, and the conversation. The tool attempts at most one
   send per operation. Read its result:
   - `sendAttempted=false` with an error: repair the named fact (tab key, model) and reuse the
     same operation once.
   - `sendAttempted=true`, or unknown: never call `review_query` again; observe only.
4. **Wait.** `agentify_wait_response` in calls of at most 60 s until COMPLETE (stable assistant
   text across two samples, no Stop, Continue or Retry control). Unchanged waits are silent.
   Never click Stop, Regenerate or Continue.
5. **Read delivery, not merely a receipt.** Fetch the specified branch and locate the actual
   answer commit, including when chat/page pairing failed but GitHub delivery succeeded. Read
   the complete answer_heading subsection inside question_heading at target_path at that
   immutable commit. Compare the question against source_sha and the delivery diff against
   its parent: no overwritten answer, changed question, or edits outside the assigned answer
   section. Unrelated intervening commits are not a conflict. Check the actual branch contains
   the delivery commit. Preserve both versions on a conflict and report it; never silently
   choose a candidate, fabricate pairing ids, or discard a trustworthy narrower observation.
   A nonempty heading or a new commit alone is not evidence of a complete paired answer.
   If writing did not land, preserve the exact complete assistant answer and its source in
   assigned scratch for the parent to insert into this same target subsection. A commit SHA,
   download link or short chat receipt is not an answer. Follow its actual delivery reference;
   if no full body is available, report `answer unavailable`, not successful fallback. Do not
   resend the question. Missing optional delivery bookkeeping does not block reading an
   already recovered complete answer.
6. **New conversation.** Return the actual URL to the author, who records it in the notebook
   header or the Portfolio section. Do not edit the shared file yourself.
7. **Close and return.** `agentify_tab_close` the owned tab. Return: conversation URL, send
   effect (sent, uncertain, failed), completion state, answer commit sha or saved text path,
   target_path and headings, tab closed, unresolved facts. Return to the assigning author;
   Transport does not write NOTES.md or RESEARCH.md while the author/Pro owns that section.

## Recovery

An error string, a stale DOM or a timeout does not prove the send failed. Reconcile on the same
conversation: read the current messages and generation state; if the exact prompt is already
submitted, observe its response. Ineffective clicks follow
[send-hit-point-recovery.md](references/send-hit-point-recovery.md). Tool interfaces and the
completion test are in [agentify.md](references/agentify.md). A human-required login, an
inaccessible provider or a CAPTCHA is reported plainly and stops this send; it does not create a
new question, a new conversation or a resend.
