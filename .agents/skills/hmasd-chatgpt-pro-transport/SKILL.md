---
name: hmasd-chatgpt-pro-transport
description: In the current authoring session, send one committed HMASD Pro question through Agentify, arm deterministic observation, read the complete answer at the assigned repository target or preserve a complete chat fallback, and close the tab. Never science, never a resend.
---

# Pro browser procedure (Agentify)

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 5. The existing assignment carries
exact message text, conversation URL (or "new"), subject key (direction id or `portfolio`),
repository, branch, source_sha, target_path, question_heading and answer_heading. These are
fields in the assignment, not another record or registry. Output: factual delivery evidence.
Direction questions target NOTES.md; owner-triggered Portfolio questions target RESEARCH.md.
Do not infer the target from the role name. Read the pinned question and confirm that its
answer subsection is empty and the heading uniquely identifies this question before sending.
One send per question. Provider settings come from `.codex/hmasd-transport.toml`.
The author's message includes the question's reading instructions and source precedence.
Send them unchanged with the question URL; do not shorten to a link, choose scientific sources,
or substitute conversation memory. Context selection and scientific source-use assessment belong
to the author. A context correction never authorizes resending an accepted or uncertain question.

## Steps

1. **Tab.** Derive one question key from an unambiguous encoding of repository, branch,
   subject key, source_sha, target_path and question_heading (for example `hmasd:` plus
   their JSON array's SHA-256). Use it as both Agentify stableKey and idempotencyKey.
   `agentify_tabs`; use or create one dedicated non-protected tab for this question.
   Navigate to the conversation URL, or the provider root
   for a new conversation. Never send from a protected or default tab. One writer per
   conversation at a time. Each new question has its own tool key, so changing conversations
   needs no binding-generation workflow. Recovery of an existing operation always retains
   its original keys and arguments, including legacy operations; never derive replacement
   keys to escape an uncertain send.
2. **Preflight.** `agentify_review_preflight` on that tab: product GPT-6 Astra (shown as
   Latest) with Pro effort. Repair the tab or model selection, never the message. Do not repeat
   a passed check.
3. **Send once.** `agentify_review_query` with those keys, the exact prompt, and the conversation. The tool attempts at most one
   send per operation. Read its result:
   - `sendAttempted=false` with an error: repair the named fact (tab key, model) and reuse the
     same operation once.
   - `sendAttempted=true`: observe only. Normally use wait_response. When native pairing or
     exact response recovery is needed, the same operation with unchanged arguments and
     `verifyExisting=true` observes without another send.
   - unknown: inspect the existing operation/page first; do not assume verifyExisting is
     send-free when sendAttempted is false or unknown, and do not create a replacement.
4. **Observe without a waiting subagent.** After `sendAttempted=true`, use a deterministic
   external observer only where that host route has been implemented and verified, then return
   from the active model turn. The WSL Codex path is specified in `hmasd-jev-pro-transport` and
   arms `tools/hmasd_wait.py`, which queues only the assigning session. For Agentify/Claude,
   use a verified native external observer when available; otherwise retain the same accepted
   operation, report the route limit and continue manually when the runtime returns. Never move
   an accepted Agentify conversation to Jev, whose account is different. A direct short diagnostic
   may use `agentify_wait_response`; repeated unchanged model turns are not the waiting mechanism.
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
   task-local scratch. After Pro relinquishes the subsection, the DM inserts that text into the
   same target subsection. A commit SHA,
   download link or short chat receipt is not an answer. Follow its actual delivery reference;
   if no full body is available, report `answer unavailable`, not successful fallback. Do not
   resend the question. Missing optional delivery bookkeeping does not block reading an
   already recovered complete answer.
6. **New conversation.** Record the actual Agentify URL in the notebook header or Portfolio
   section after taking back writer ownership. This public-record policy does not apply to the
   private WSL/Jev account URLs, which stay in local operation state.
7. **Close and finish.** `agentify_tab_close` the owned tab. Preserve: conversation URL, send
   effect (sent, uncertain, failed), completion state, answer commit sha or saved text path,
   target_path and headings, tab closed, unresolved facts. The authoring session owns this
   procedure; it does not write NOTES.md or RESEARCH.md while Pro owns that section.

## Recovery

An error string, a stale DOM or a timeout does not prove the send failed. Reconcile on the same
conversation: read the current messages and generation state; if the exact prompt is already
submitted, observe its response. Ineffective clicks follow
[send-hit-point-recovery.md](references/send-hit-point-recovery.md). Tool interfaces and the
completion test are in [agentify.md](references/agentify.md). A human-required login, an
inaccessible provider or a CAPTCHA is reported plainly and stops this send; it does not create a
new question, a new conversation or a resend.
