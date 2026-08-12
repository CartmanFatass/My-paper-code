---
name: hmasd-external-gemini
description: Run the default additional divergent Gemini innovator consultation for one eligible HMASD direction through Agentify, with visible Gemini 3.1 Pro and Extended thinking preflight, exact-one strict first binding, natural-completion observation, and assignment-scoped archival. Use only in the registered External Gemini transport leaf for an already frozen science-only innovation question; never use it to replace ChatGPT External Pro or request convergence or acceptance.
---

# HMASD External Gemini transport

Operate one frozen, science-only Gemini consultation. Never choose the research question, interpret the answer, contact the user, use Git, or write outside the exact requester partition.

This is the direction's additional divergent-innovation route. The caller uses
Gemini for broad world/domain mechanisms, analogies, overlooked regimes,
counterexamples, scenario families, controls, and toy-to-UAV bridges. Reject a
request that asks Gemini to replace the direction's ChatGPT External Pro, make
the final convergence or causal-closure decision, accept results or code, or
select the portfolio. Provider transport capacity may serialize the two reviews
but never merges their prompts, conversations, archives, or intakes.

## Contract

1. Read the assignment's `batch.json`, local `context.md`, and sole question. Reject provider-visible local paths, hashes, receipts, raw/blob URLs, and code/test/runtime requests.
2. Inspect Agentify tabs, status, page, and existing archives. If a send may exist, observe it; never resend. Require `activeQuery=null` and `inflightQueries=0` before any reload or new send.
3. Use a clean disposable non-default `https://gemini.google.com/app` tab. Run `scripts/gemini_preflight.mjs` with a new output path in the assignment partition. Proceed only when its receipt reports both `3.1 Pro` visibly selected and `Extended thinking` visibly enabled. The script activates no response control.
4. Call strict `agentify_review_query` with provider `gemini`, model `Gemini 3.1 Pro extended`, first binding, the inspected tab ID, provider-root URL, `conversationId=__new__`, exact question `promptPath`, caller-computed SHA-256, a new immutable idempotency key, and `timeoutMs=2700000`.
5. A click or `sendActionCount` is not proof of submission. A committed Gemini send requires a visible user turn and a concrete `/app/<conversation-id>`; `sendCount=1` is additional supporting evidence. If stable reconciliation instead shows zero user and assistant turns, no conversation ID, the complete question retained in the composer, and no active generation, archive and return `ERROR` with `terminal_state=SEND_NOT_COMMITTED`, `prompt_sent=false`, and `response_received=false`. Do not retry inside the same transport call. A later attempt requires explicit Root authorization and a fresh tab. Once a provider turn, concrete conversation identity, or `sendCount=1` exists, never resend.
6. Observe natural generation only. Never operate Stop, Continue, Retry, Answer now, or an acceleration control. Treat a short label or partial preview as nonterminal even if a tool prematurely reports completion.
7. After the visible response is inactive, unchanged for five seconds, and contains every required heading exactly once, run `scripts/gemini_archive_terminal.mjs`. It reconciles the live response with the strict receipt and preflight and creates the exact `results.json` without overwrite.
8. Run the shared Agentify result-path guard with the project interpreter. Return the concrete conversation URL/ID, model/thinking evidence, response/archive evidence, send-commit facts, and residual uncertainty. A transport error must be returned to the invoker, not only written to `results.json`.
9. After the complete response or terminal error is archived and no generation is active, close the Gemini tab immediately. A later question reopens the saved conversation URL in a new tab. If close fails, report that failure explicitly.

Do not close the conversation tab before the complete archive or terminal error exists. Do not restart Agentify during any active provider generation.
