# HMASD External Review Protocol

## Source and Role Boundaries

Start from `00_REVIEW_BRIEF.md` and `01_SHARED_SOURCE_MANIFEST.md`. Only Gemini
also receives `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Reviewer role and output
contracts live in `10_GEMINI_DIVERGENT_QUESTION.md`,
`20_PRO_OPEN_QUESTION.md`, and `40_PRO_CONVERGENT_QUESTION.md`.

The two divergent reviewers are blind and equal. Controller synthesis precedes
convergent Pro. Reviewers advise; only the controller changes the research
portfolio, implementation, compute, or disposition.

## Transport Ownership

Transport is serialized but role-specific:

- Gemini reuses its registered one-to-one Codex Exchange and persistent
  Antigravity session.
- Open and convergent Pro are controlled directly by the active controller via
  `codex-chatgpt-control` and their two registered visible ChatGPT URLs.

Never route a new Pro stage through a Codex Exchange, subagent, heartbeat,
automation, shell sleep, or cross-task relay. Legacy Exchange receipts remain
valid history only.

## Gemini

The Gemini Exchange verifies its exact registered task, then receives one
internal route via `codex_app__send_message_to_thread` using only `hostId`,
`threadId`, and `prompt`. It reuses the exact registered Antigravity session and
Gemini 3.1 Pro (High), reads only the approved per-round local-source manifest,
and writes only `11_GEMINI_DIVERGENT_RAW.md`.

Export the exact naturally completed response from `transcript_full.jsonl`; do
not issue an archival prompt. The Exchange sends one terminal relay to the
controller. Supplying model or thinking fields, opening a substitute task, or
starting a concurrent CLI client is forbidden.

## GPT Pro

Use the `chatgpt-delegate` workflow from the pinned plugin recorded in
`REVIEWER_CONVERSATIONS.json`. The controller opens Chat, verifies the visible
`Pro` intelligence setting, selects the registered role-specific URL, and
submits the expanded neutral handoff once.

Submission and completion are separate. While generation is active, use only
bounded `messages.status` or `messages.waitAndRead` calls on the same visible
thread. Never resubmit, shorten, stop, retry, regenerate, continue, or use a
different conversation. Archive the completed Markdown exactly and compare it
with the in-memory response before recording completion.

The plugin's structured blocker is authoritative. `login_required`, captcha,
rate limit, permission, confirmation, bridge loss, or selector drift stops the
stage without a workaround. The verified claim is the visible `Pro` setting,
not an unexposed model identifier.

## State and Compatibility

`05_REVIEW_STATE.json` is the only lifecycle authority. For new Pro work,
`DISPATCHED` uses `source=chatgpt_control` with `reference=plugin:submitted`;
`COMPLETE` uses the same session and conversation with
`reference=plugin:completed`. The controller alone writes both transitions.

Existing `source=exchange`, `source=gemini`, and manual receipts remain valid
history. A nonempty raw without an accepted completion receipt is incomplete
evidence. If a stage is already `DISPATCHED`, preserve its route and inspect
only that response; never duplicate the prompt.

Only the controller may interpret a raw, write synthesis or disposition, or
authorize implementation and experiments.
