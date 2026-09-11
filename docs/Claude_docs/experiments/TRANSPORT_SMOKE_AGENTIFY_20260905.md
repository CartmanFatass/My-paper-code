# Transport smoke: Claude Code -> Agentify Desktop -> ChatGPT 6 Pro (2026-09-05)

This is a transport check, not evidence. It records the one non-scientific Send that
`AGENTS.md` Appendix B requires before the Claude loop may dispatch scientific Pro requests
unattended through `hmasd-pro-transport`. Nothing scientific was asked or answered, no
direction conversation was touched, and the shared HMASD registry was not modified.

Owner instruction 2026-09-05 21:06 PDT: "continue, run the smoke". Executed directly by the
Fable research hub through the `mcp__agentify-desktop__*` tools, as the owner asked for one
end-to-end run before the Sonnet subagent takes over.

## Result: PASSED

| Fact | Value |
| --- | --- |
| Request id / idempotency key | `claude-transport-smoke-20260905-01` |
| Stable key (Agentify-local binding) | `claude--transport--smoke` |
| Conversation | `https://chatgpt.com/c/6a9ce941-e63c-83e8-8873-dee7dcfe378e` (fresh, first binding) |
| Product model label matched | `Latest` (checked `menuitemradio` in the open picker; closed control reads `6Pro`) |
| Reasoning effort matched | `Pro` (slider owner `Power`, value 4 of 0..4, already selected, 0 steps) |
| Prompt | `Reply with the single word READY.` sha256 `a48ba54e9a3e9424e093278ebb22ab78048172fd5d87c7b54c01441252d7e719` (33 bytes) |
| Send | exactly one, `sendAttemptedAt` 1788668195112 (21:16:35 PDT) |
| Provider message ids | user `92e64191-2d52-473d-82fa-e625b42b1c73`, assistant `0f74eb53-ea71-45b0-a700-5c64608f52c9` |
| Response | `READY`, sha256 `c2e3ac47f4a325469c1a2d5f117e463ec943c721986d5d9f09ac4540b7d80526` (5 bytes), page showed "Worked for 10s" |
| Receipt | operation `ce7d5bf7-d1e0-40a7-9dd7-60606aef7724`, archive projection `exact`, error `null` |
| Archive (git-ignored, local) | `temp/sessions/hmasd-chatgpt-pro-transport/archive/transport_smoke/claude-transport-smoke-20260905-01/` (`SMOKE_HANDOFF.json`, `__00_PROMPT.md`, `__02_RESPONSE.md`, `__03_TRANSPORT_FACTS.json`) |
| Tab | agent-created `c83e6da6-3fb0-4f5e-bda5-e7cb28b693c7`, closed after the archive was verified |

## What the run exposed in Agentify Desktop (owner's tree, uncommitted)

1. **Model-menu trigger label.** The strict transport opened the picker only through a composer
   button labelled exactly `High` or `Pro`. Under 6 Pro the live control is labelled `6Pro`, so
   both preflights failed with `chatgpt_target_menu_unavailable` before any Send.
   Fix: `chatgpt-controller.mjs` trigger regex `/^(?:High|Pro|6 ?Pro)$/i` in
   `#openChatgptTargetMenu`. Required one GUI restart (Agentify relaunches its own Chrome; the
   ChatGPT sign-in survived).
2. **Picker label.** `GPT-6 Astra` is not a label in the picker's product list; the checked
   item is `Latest`. The transport agent's order (`GPT-6 Astra` first, then `Latest`) is kept,
   and `Latest` is the label that sends.
3. **Windows directory fsync.** After the response file was linked into place, the archive
   commit fsynced the parent directory handle; Windows rejects that with `EPERM`, so the first
   `agentify_review_query` call returned a tool error although the Send, the observation and the
   response file were all complete. The persisted operation carried `sendAttempted=true`,
   `archive=null`, `error=EPERM_OPERATION_NOT_PERMITTED_FSYNC`. A second call with the identical
   request and `verifyExisting=true` observed only (no Send) and returned the `COMPLETE` receipt.
   Fix: `review-transport.mjs` tolerates `EPERM`/`EISDIR`/`EINVAL` from the directory sync on
   `win32` (the file handle itself is still fsynced). Applied after the run; live only after the
   next GUI restart.
4. **Leftover draft.** The fresh new-chat composer held a 7,272-character draft (a Codex VQFP
   prompt persisted by ChatGPT). Agentify clears the composer (select-all, Backspace) before
   inserting the exact prompt, and the archived user turn equals the smoke prompt.

## Consequence

Per `AGENTS.md` Appendix B and `.claude/skills/hmasd-pro-transport/SKILL.md`, unattended
scientific dispatch through `hmasd-pro-transport` is now enabled on the transport side. It
remains blocked by the research state: the loop is `OWNER_PAUSED` for Pro requests
(`docs/research/portfolio/HANDOFF_20260905.md`) until the owner lifts it.
