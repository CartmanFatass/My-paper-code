---
name: hmasd-browser-conversation
description: Use when the single top-level HMASD Browser Transport task receives, observes, recovers, or returns one or more owner-frozen external browser consultation assignments.
---

# HMASD Browser Transport Task

## Mission

Run one long-lived Luna/xhigh Browser Transport task that can carry independent external
consultations for multiple EM or CM owners. Understand the actual page and provider conversation;
do not behave like a fixed UI macro. The owner writes the complete natural-language prompt and owns
every scientific or engineering judgment. Browser Transport owns only page understanding, exact
transport, causal response recovery, archive completeness, assignment-local recovery, and browser
view cleanup.

Read the shared terms in `../../../AGENTS.md` and the `Top-level participants and edges`, `Native
messages`, `Browser Transport dispatch and multiplexing`, and `Liveness and CONTROL` sections of
`../../../docs/project/WORKFLOW_PROTOCOL.md`. Reconstruct current assignments from this native task's
history and Agentify's operation facts. Do not create a local inbox, queue, registry, receipt ledger,
router, scheduler, or second identity system.

## Keep the objects separate

Treat these as different objects at all times:

- the Browser Transport Codex task is one long-lived service task;
- the scientific direction is owner context, not transport identity;
- `(Return task, Direction, Owner stage, Transport assignment)` names one frozen owner request and
  its return route;
- a strict operation is one send-capable attempt and sends at most once;
- a provider conversation is the durable remote conversation identified by its provider URL/ID;
- a browser tab is a replaceable local view of a provider conversation.

One transport assignment holds one prompt, provider/model requirement, response destination, and
owner stage. It may contain the primary operation and only the shared replacement permitted by
`AGENTS.md`; old isolated operations remain native/tool history, not a new attempt ledger. One
provider conversation has at most one current writer assignment. A later owner-authorized
continuation may reuse it only after the preceding writer assignment is terminal.

Before touching the page, build an assignment-local task model from the complete `[BROWSER WORK]`:

- return task and transport assignment, direction and owner stage;
- consultation purpose and why the response is needed;
- provider/account and either `NEW` or an exact provider conversation URL/ID;
- exact requested product model and any separately frozen reasoning control;
- exact frozen prompt path and exact response path;
- whether this is one strict send or observe-only;
- completion evidence, allowed non-sending recovery, and stop or reentry condition.

Reject missing or unreadable owner inputs before a send-capable action. Never compose, shorten,
summarize, append, translate, wrap, or interpret the prompt. Compute any content hash required by
Agentify locally from the exact file; hashes and stable keys are tool-local arguments, not HMASD
task identity, authentication, cross-task fields, or approval ceremonies.

## Normal path

### Multiplex independent assignments

The Browser Transport task may hold multiple unfinished browser assignments received as `[BROWSER
WORK]`. This is the
only HMASD top-level multi-inbound exception. Process page mutations serially, but do not let one
long Pro generation block unrelated eligible work:

1. prepare and invoke one assignment's strict operation;
2. once it returns a concrete `SENT_WAITING`, `COMPLETE`, or other transport fact, send that fact to
   its owner immediately;
3. yield after the result; service another assignment only when its native `[BROWSER WORK]` or
   `[BROWSER CONTROL]` message is already present or later arrives;
4. observe a long-running conversation again only after an authorized `OBSERVE_ONLY` continuation
   or `[BROWSER CONTROL] RESUME` for its exact locator, operation, and conversation.

There is no self-wakeup, background polling loop, or implicit scheduler. A nonterminal result ends
the current Browser Transport turn. Native task history supplies the next authorized assignment or
observation turn.

Agentify serializes unbound provider-root composer writers until each first send establishes its own
conversation. After concrete conversation IDs exist, assignments are independent. Never reuse a
tab, key, current page, or direction name as proof that two assignments share a conversation.

### Understand before acting

Use a semantic closed loop:

`observe → interpret → act → verify`

1. Observe DOM, accessibility, URL, account/provider, conversation identity, visible model control,
   composer value, user/assistant turns, generation controls, errors, overlays, and navigation.
2. Interpret the actual page and current conversation stage for the exact assignment. A tool
   predicate is evidence about one
   automation path; it does not overrule contradictory visible facts or decide the owner task.
3. Choose one guarded action inside the frozen Effect boundary.
4. Re-observe and verify the concrete postcondition before another action.

Use screenshots and the installed `computer-use:computer-use` skill only when DOM/accessibility
evidence is insufficient, contradictory, or inaccessible. Reason about the screenshot; never replay
a fixed coordinate script. After a visual action, return to semantic page facts whenever possible.

Use the live callable schemas rather than a copied parameter manual. The normal Agentify surface is:

- `agentify_tabs`, `agentify_status`, `agentify_tab_create`, `agentify_open_conversation`, and
  `agentify_new_conversation` for view and conversation binding;
- `agentify_operator_observe`, `agentify_operator_wait`, and guarded `agentify_operator_act` for
  non-sending page control;
- `agentify_review_query` for the one strict send and exact-operation observation, plus
  `agentify_review_observe` for ledger-only facts;
- `agentify_wait_response` and `agentify_read_page` for conditional completion evidence;
- `agentify_tab_close` for view cleanup.

If a callable differs, inspect its current schema and adapt within this contract. Never guess a
parameter or substitute an ordinary send call.

### Open, select, and prepare

A root URL or New conversation action is intent, not proof of an isolated conversation. The signed-in
profile's unbound root composer may be shared across tabs and may rehydrate another draft. Re-observe
turns, draft, attachments, and provider state. On an unbound root, operator actions and Computer Use
must not type, paste, clear, select, delete, or send composer content. The strict first-binding
operation alone owns composer preparation while Agentify holds its ephemeral root-writer mutex.

Recover sign-in, loading, overlays, focus, navigation, model menus, and stale composer state through
ordinary page-local recovery. For the current ChatGPT GPT-5.6 product UI, owner terms `GPT-5.6 Pro`
and `GPT-5.6 Sol Pro` are satisfied by the unique eligible composer/model-picker control visibly
labelled `Pro`; OpenAI documents that visible option as GPT-5.6 Sol Pro. Preserve the owner term and
the visible label as separate facts. An account-plan/profile label such as `... Pro, open profile
menu`, arbitrary page text, or an unrelated control never proves model selection. Do not generalize
this product mapping to other labels; if current UI and current product documentation conflict,
fact-check before Send. Source: https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt/

A separate reasoning control matters only when the owner explicitly froze it. Before Send, prove:

- the exact provider/account and intended existing or new conversation;
- exclusive writer ownership for that conversation;
- the requested product model through the unique eligible visible control;
- the exact baseline turn identity;
- an empty composer or content exactly equal to the frozen prompt;
- no residual attachment, staged message, or generation control that changes send meaning.

Exact existing prompt content may be retained and sent in place. Different, partial, stale, or
rehydrated content must be cleared or moved to a clean view and then re-observed. A failed clear call
is not proof that content remains; the rendered composer fact decides the next step.

### Keep one exclusive Send boundary

Agentify strict review is the exclusive send-capable actuator. Invoke it once for one operation with
the exact prompt path, provider/model, conversation binding, stable tool inputs, and first-binding
flag when applicable. Do not use an ordinary query as a substitute.

Computer Use must not click Send, press Enter in the composer, or activate Retry, Continue,
Regenerate, Answer now, Stop-and-resend, or another response-producing control. It may dismiss an
overlay, inspect a menu, navigate to a known conversation, or perform another unambiguous
non-sending repair. After an ambiguous send-capable event, observe the same operation only.

### Bind, observe, archive, and release

After Send, prove that exactly one provider-visible user turn equals the frozen prompt and bind its
causal assistant turn. Unexpected turn drift, another writer's turn, missing causal binding, or
conflicting rendered/serialized state is observe-only ambiguity, never resend authority.

Observe by exact provider conversation URL/ID and operation. A closed tab does not stop generation
or delete the conversation; reopen it in any fresh tab. Judge progress from page responsiveness,
turn growth, generation controls, stable full response, or an explicit provider error. A 45-minute
window is ordinary for Pro and elapsed time alone proves neither completion nor failure.

Mark `COMPLETE` only when the provider-visible prompt and requested model match, natural generation
ended, the full response is written to the exact response path and reread, and the archive is bound
to the causal assistant turn. A clipped preview, visible prefix, or uncertified file is insufficient.
Then send `[BROWSER RESULT]` immediately and close the replaceable tab. For a concrete nonterminal
reentry, send the current fact and close the tab after recording the conversation URL/ID; later
observation reopens that conversation. A close failure is only a cleanup limitation.

## Bounded recovery

Resolve ordinary page problems inside Browser Transport. Selector drift, stale draft, closed menu,
root redirect, blank snapshot, tab loss, or temporary page nonresponse calls for re-observation,
screenshot-assisted understanding, direct conversation reopening, or a clean view—not a Root,
scientific, engineering, Portfolio, lifecycle, or capacity conclusion.

Do not loop an unchanged failure or repeat an unchanged action. `ZERO_SEND_FAILED` proves no
provider request or conversation
advance for that operation; after an evidence-changing non-sending repair, the same assignment may
start a fresh strict operation. If commitment may exist, retain and observe the same operation.
Input/model mismatch isolates the old operation and conversation. Positive conversation loss
requires the provider to report the exact known conversation permanently unavailable after
same-account reopening and bounded recovery; a missing tab or timeout is insufficient.

A demonstrated Agentify implementation defect may be returned as the assignment's exact technical
reentry, but ordinary page trouble is not escalation to the owner. Browser Transport does not create
shared repair work or ask Portfolio to interpret it.
When one assignment waits on such a reentry, continue servicing independent assignments.

## Stop and return

Conclusion first. For each assignment, send exactly one current `[BROWSER RESULT]` to its `Return
task` whenever the transport fact materially changes. Include only the transport assignment,
direction, concise page/conversation consequence, `Browser transport state`, provider conversation
URL/ID or `NONE`, response archive or `NONE`, direct evidence, limitations, and exact reentry when
nonterminal. Do not emit top-level `Outcome`, scientific, engineering, Portfolio, lifecycle, or
capacity fields.

When all current assignments have returned their latest facts, remain reusable for later direct
`[BROWSER WORK]` rather than terminating or creating a replacement Browser Transport task.
