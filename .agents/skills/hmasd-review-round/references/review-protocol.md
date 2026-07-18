# HMASD External Review Protocol

## Source and Role Boundaries

Start from `00_REVIEW_BRIEF.md` and `01_SHARED_SOURCE_MANIFEST.md`. Only Gemini
also receives `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Reviewer role and output
contracts live in `10_GEMINI_DIVERGENT_QUESTION.md`,
`20_PRO_OPEN_QUESTION.md`, and `40_PRO_CONVERGENT_QUESTION.md`.

The two divergent reviewers are blind and equal. Controller synthesis precedes
convergent Pro. The convergent review compares a portfolio; it does not turn one
serialized compute choice into the only permitted research direction.

## Exchange Ownership

Use the three persistent one-to-one Codex Exchange tasks registered in
`REVIEWER_CONVERSATIONS.json`. Each Exchange owns only its external session and
role-specific raw path. Open and convergent Pro never share an Exchange or
external conversation.

Both directions use `codex_app__send_message_to_thread` with only `hostId`,
`threadId` and `prompt`. Omitting `model` and `thinking` preserves the target's
current settings under the current tool contract; supplying either field is
forbidden. Verify the target task with `read_thread` before and after delivery.
There is no review transport subagent, collaboration relay, heartbeat,
automation, shell sleep or substitute task.

## Gemini

The Gemini Exchange reuses the exact registered Antigravity session and Gemini
3.1 Pro (High). Use the approved tracked local-source allowlist, plan/sandbox
mode and one live client. Export the exact completed response from
`transcript_full.jsonl`; do not send an archival prompt. A non-interactive
invocation is a failure fallback, never a concurrent second client.

## GPT-5.6 Pro

Each Pro Exchange reuses its registered role-specific external conversation.
Verify its exact URL, visible `Pro` label and stored role ACK without opening
any model selector. Expand the neutral handoff template by replacing only the
commit and question path, then submit it verbatim. Do not paste internal routing
metadata.

Wait for natural completion inside the same Exchange turn. A browser timeout
permits another bounded read of the same page only. Never stop, shorten, retry,
regenerate, continue, or duplicate the response. Archive and byte-verify the
completed response before the Exchange sends its terminal relay.

## State and Compatibility

`05_REVIEW_STATE.json` is the only lifecycle authority. A relay does not advance
it; the controller supplies the exact Exchange turn/item receipt to
`review_state.ps1`. A nonempty raw without an accepted receipt is incomplete
evidence.

New receipts use `source=exchange`, the registered Exchange task ID as session,
the registered external conversation, and exact `read_thread` turn/item
references. Existing `source=gemini` transcript and manual receipts remain
valid history. If a stage is already `DISPATCHED`, preserve its route and
inspect only the existing external response; never duplicate the prompt. An
ambiguous response/request boundary is `BLOCKED_LEGACY_DISPATCH_UNCERTAIN`.

Before ending, every Exchange sends exactly one `REVIEW_RELAY` to the controller
task named in the current dispatch, again without `model` or `thinking`, and
verifies delivery. A local final answer alone is not notification. If external
thinking outlives the Exchange turn, relay `WAIT_PRO_THINKING`; only that same
Exchange may later perform read-only recovery.

Only the controller may transition state, interpret a raw, write synthesis or
disposition, or authorize implementation and experiments.
