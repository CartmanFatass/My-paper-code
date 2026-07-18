# HMASD External Review Protocol

## Source and Role Boundaries

Start from `00_REVIEW_BRIEF.md` and `01_SHARED_SOURCE_MANIFEST.md`. Only Gemini
also receives `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Reviewer role and output
contracts live in `10_GEMINI_DIVERGENT_QUESTION.md`,
`20_PRO_OPEN_QUESTION.md`, and `40_PRO_CONVERGENT_QUESTION.md`.

The two divergent reviewers are blind and equal. Controller synthesis precedes
convergent Pro. The convergent review compares a portfolio; it does not turn one
serialized compute choice into the only permitted research direction.

## Subagent Ownership

Use one role-specific Terra Medium child for each external stage and at most one
active external child at a time. The child is the sole owner of its browser or
Antigravity interaction until `COMPLETE` or actionable `BLOCKED`. Open and
convergent Pro never share a child or external conversation.

The controller creates the child once, records the spawn receipt, and remains
idle. The child stays active during external thinking and reports only through
its final answer, which the subagent runtime delivers to `/root`. It never also
calls `collaboration.send_message`, which would duplicate delivery. No other
task monitors the child. There is no cross-thread transport, model override in a message, heartbeat,
automation, sleep loop, controller poll, or nonterminal relay.

## Gemini

Reuse the exact registered Antigravity session and Gemini 3.1 Pro (High). Use
the approved tracked local-source allowlist, plan/sandbox mode, and one live
client. Export the exact completed response from `transcript_full.jsonl`; do not
send an archival prompt. A non-interactive invocation is a failure fallback,
never a concurrent second client.

## GPT-5.6 Pro

Reuse the registered role-specific external conversation. Verify its exact URL,
visible `Pro` label, and stored role ACK without opening the model selector.
Expand the neutral handoff template by replacing only the commit and question
path, then submit it verbatim. Do not paste internal routing metadata.

Wait for natural completion in the child. A browser timeout permits another
bounded read of the same page only. Never stop, shorten, retry, regenerate,
continue, or duplicate the response. Archive the completed response exactly and
verify the archived bytes before reporting `COMPLETE`.

## State and Compatibility

`05_REVIEW_STATE.json` is the only lifecycle authority. A subagent notification
does not advance it; the controller supplies its receipt to
`review_state.ps1`. A nonempty raw without an accepted receipt is incomplete
evidence.

New receipts use `source=subagent` and the exact
`agent:/root/review_<normalized-round>_<role>:spawn|complete` references. The
state script also requires the registry's Terra Medium worker profile.
The state script accepts already-recorded Exchange/Gemini receipts solely so
open rounds and history remain valid; new work never creates them. If a stage
was already `DISPATCHED`, preserve that receipt and route. A new child may adopt
the in-flight stage only after confirming the registered external conversation
and exact response/request boundary. It must not duplicate the prompt. If that
boundary is ambiguous, report `BLOCKED_LEGACY_DISPATCH_UNCERTAIN`.

Only the controller may transition state, interpret a raw, write synthesis or
disposition, or authorize implementation and experiments.
