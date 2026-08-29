---
name: hmasd-browser-conversation
description: Use only when an HMASD browser-conversation leaf is explicitly assigned one owner-frozen external consultation or same-conversation observation.
---

# HMASD Browser Conversation

Own one external conversation as an intelligent browser agent, not a blind sequence of UI calls.
The parent owns prompt authorship and every scientific or engineering judgment. This skill owns only
page understanding, exact transport, causal response recovery, archive completeness, and browser
view cleanup.

## Build the local browser task model

Before touching the page, form a local browser task model containing:

- the consultation purpose and why the response is needed;
- provider and account, plus an exact existing conversation URL/ID or an explicit request for a new
  conversation;
- the agent session, browser tab, and provider conversation as three separate objects;
- the exact visible model required by the owner and any separately frozen reasoning control;
- the exact frozen prompt path, exact response path, completion evidence, allowed non-sending
  recovery, and stop or reentry condition.

Reject missing or unreadable owner inputs before a send-capable action. Never compose, shorten,
summarize, append, translate, wrap, or interpret the frozen prompt. IDs, stable keys, and hashes are
tool-local anchors; they are not task identity or an approval ceremony.

One instance retains one external conversation assignment until it has a legitimate terminal
transport state or one exact nonterminal reentry. It has exclusive writer ownership of that
provider conversation during the assignment. Another leaf, tab, or tool may observe, but must not
inject a competing turn.

Use the live callable schemas rather than a copied parameter manual. The normal Agentify surface is:

- `agentify_tabs`, `agentify_status`, `agentify_tab_create`, `agentify_open_conversation`, and
  `agentify_new_conversation` for view and conversation binding;
- `agentify_operator_observe`, `agentify_operator_wait`, and guarded `agentify_operator_act` for
  non-sending semantic page control;
- `agentify_review_query` for the one strict send and its `verifyExisting` observation mode, plus
  `agentify_review_observe` for ledger-only observation;
- `agentify_wait_response` and `agentify_read_page` for conditional natural-completion evidence;
- `agentify_tab_close` for view cleanup.

If the available schema differs, inspect that schema and adapt within the same semantic contract;
never guess a parameter or substitute an ordinary send call. A content hash required by Agentify is
an internal exact-byte argument, not HMASD authentication or a durable workflow gate. The owner
supplies the archive destination even when the current strict callable returns the full response
instead of accepting that destination directly.

## Understand before acting

Use a semantic closed loop:

`observe → interpret → act → verify`

1. Observe DOM, accessibility, URL, and provider conversation facts first: account/provider,
   conversation identity, visible model control, composer value, user and assistant turn identity,
   generation controls, errors, overlays, and navigation state.
2. Interpret the actual page and current conversation stage. A tool predicate reports one
   automation path; it does not overrule contradictory visible evidence or prove that the page,
   provider, or assignment failed.
3. Choose one guarded action that advances the local browser goal and remains within the frozen
   Effect boundary.
4. Re-observe and verify that action's concrete postcondition before choosing another action.

Use screenshots and Computer Use through the installed `computer-use:computer-use` skill only when
semantic page evidence is insufficient, contradictory, or inaccessible. Inspect the screenshot as evidence and reason
about the current Agentify page; do not replay a fixed coordinate script. Return to
DOM/accessibility facts after the visual action whenever possible.

## Open, select, and prepare

A tab is a replaceable view, not a provider conversation. Reuse or open any usable tab for the exact
known conversation, or open a clean provider root when the assignment explicitly requests a new
conversation. A closed tab does not stop generation or delete the provider conversation.

Recover sign-in, loading, overlays, focus, navigation, model menus, and composer state through
ordinary page-local recovery. Select and verify the exact owner-required visible model on its real
provider control. A separate reasoning control matters only when the owner explicitly froze it;
visible `GPT-5.6 Pro` is not invalid merely because an unrelated reasoning menu is absent or closed.

Before the one Send boundary, establish all of the following from current evidence:

- the exact provider/account and intended existing or new conversation;
- exclusive writer ownership;
- the exact visible model and any separately frozen control;
- the exact baseline turn identity before injection;
- an empty composer or composer content exactly equal to the frozen prompt;
- no residual attachment, staged message, or generation control that changes the send meaning.

Exact existing prompt content may be retained and sent in place. Different, partial, stale, or
rehydrated content must be cleared or moved to a clean conversation and then re-observed. A failed
clear call is not proof that content remains; the rendered composer fact decides the next step.

## Keep one exclusive Send boundary

Agentify strict operation is the exclusive send-capable actuator. Use its strict review operation
with the exact prompt path, response path, provider/model, conversation binding, stable operation
inputs, and first-binding flag when applicable. Invoke that strict operation once for one operation.
Do not use ordinary query calls as a substitute.

Computer Use must not click Send, press Enter in the composer, or activate Retry, Continue,
Regenerate, Answer now, Stop-and-resend, or any other response-producing control. Non-sending
Computer Use may dismiss an overlay, focus a control, inspect a menu, navigate to a known
conversation, or perform another guarded page-local repair only when the intended action and
postcondition are unambiguous. After any ambiguous send-capable event, observe only: never perform a
second injection to discover what happened.

## Bind the causal exchange

After the strict call, prove the conversation advanced from the exact baseline turn identity to
exactly one provider-visible user turn equal to the frozen prompt and its causally associated
assistant turn. Use provider turn IDs when available and corroborate with visible order/content.
Unexpected turn drift, another writer's turn, missing causal binding, or conflicting rendered and
serialized state is observe-only ambiguity. Do not resend and do not complete from an older or
unrelated answer.

Observe a known operation without sending. Reopen the exact provider conversation by URL/ID in a
new tab whenever useful. If natural generation is live, use conditional observation tied to page
facts such as turn growth, disappearance of the live-generation control, stable full response, or
an explicit provider error. A 45-minute window is an ordinary long observation interval for Pro,
not a global deadline; elapsed time alone never proves completion, page unresponsiveness, loss, or
failure.

Mark `COMPLETE` only when the provider-visible prompt and model match, natural generation ended, the
full naturally completed response is written to the exact response path and reread successfully,
and that archive is bound to the causal assistant turn. A clipped tool preview, visible prefix, or
uncertified pre-existing file is not the archive.

## Recover from page and observation problems

Keep local browser-use problems inside this assignment. Inspect the nearest page facts and choose a
different safe action only when a new premise explains why it can work. Selector drift, a stale
composer, a closed menu, a root redirect, a blank semantic snapshot, or a tab failure normally
calls for re-observation, screenshot-assisted understanding, direct conversation reopening, or a
clean view—not escalation to the parent.

Do not loop an unchanged failure. `ZERO_SEND_FAILED` proves no provider conversation was created or
advanced for that operation; after an evidence-changing non-sending repair, the same assignment may
start a fresh strict operation. If commitment might exist, retain and observe the same operation.
Input/model mismatch isolates the old operation and conversation. Positive conversation loss
requires the provider to report the exact known conversation permanently unavailable after
same-account direct reopening and bounded recovery; a missing tab or timeout is insufficient.

The shared transport-state meanings and replacement boundary live only in `AGENTS.md`. This skill
does not invent extra statuses, attempt ledgers, review approvals, or owner conclusions.

## Release the view and return

For cleanup, close the replaceable tab once the conversation URL/ID is known and the current observation has
reached a legitimate terminal transport fact or an exact nonterminal reentry. For `COMPLETE`, close
only after archive write and reread. Closing the tab saves local browser memory and does not stop the
web service; later observation opens the same conversation in another tab. A close failure is only
a cleanup limitation.

Return conclusion-first with only `Browser conversation state`, whether a send occurred, concrete
provider conversation URL/ID, exact model/prompt/causal-turn evidence, response path or NONE, current
page fact, and an exact reentry when nonterminal. Never emit a top-level result field or infer the
parent's scientific, engineering, investment, lifecycle, or capacity conclusion.
