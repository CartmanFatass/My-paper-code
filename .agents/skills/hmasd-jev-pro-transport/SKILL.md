---
name: hmasd-jev-pro-transport
description: On the WSL host, send one committed HMASD Pro question through Jev Ultrafast and a local headless Chrome on the owner's second ChatGPT account, wait read-only for completion, read the complete answer at the assigned repository target (or preserve the chat text), and return facts. Never science, never a resend.
---

# Pro transport (Jev Ultrafast, WSL host)

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 5. The assignment, the target
check before sending, the delivery reading (step 5) and the return facts are those of
`hmasd-chatgpt-pro-transport`; this skill replaces only the browser route. Use it on the WSL
host. The Windows host keeps Agentify.

Jev does the browser work itself: it observes the page as an indexed element table and chooses
each operation and target. The driver `tools/pro_transport/jev_send.py` hands Jev the committed
text verbatim (no model writes or paraphrases it), keeps the books, and guards one click: the
send click is refused unless the effort pill shows the configured label and the box equals the
committed prompt. `send_attempted` is persisted before that click. Settings are `[jev]` in
`.codex/hmasd-transport.toml`; Jev's credentials stay in its own ignored `.env` (the native
TypeSafe key is preferred; the Vercel gateway key rate-limits).

**Account.** This is a different ChatGPT account from the Agentify one. A conversation URL
recorded from the other account does not exist here: send with `--conversation new`, or with a
URL this account returned. Never paste an Agentify-account URL into this route.

**Private facts stay local (owner, 2026-09-18).** This account's conversation URLs, its name
and anything else identifying it live only in the driver's state directory
(`~/.local/state/hmasd-pro-transport/operations/<key>.json`), never in NOTES.md, RESEARCH.md,
a change note, a commit message or anything else that is pushed. Shared records name a
question by its key; the URL for a follow-up is read from the local operation file.

## Steps

Interpreter: `~/test/Jev/jev-ultrafast/.venv/bin/python` (written `$JEV` below), never an HMASD
venv, and nothing is installed into either. `$D` is `tools/pro_transport/jev_send.py`. Output
never prints the conversation address unless `--show-url` is given.

1. **Key.** `$JEV $D key --repository … --branch … --subject … --source-sha … --target-path … --question-heading …`
   prints the question key (`hmasd:` plus the SHA-256 of that JSON array, as in the old skill).
2. **Compose.** Save the author's complete message, unchanged, to a file and run
   `$JEV $D compose --message-file <file> --slug <slug> --subject <direction>`. It writes
   `temp/pro_transport/hmasd-pro-question-<slug>.md` (the complete message) and
   `<slug>.short.txt` (a brief request to read it, write the assigned Answer, or provide the
   complete reply in chat if GitHub writeback is unavailable). Digests stay in local transport
   metadata, outside the visible cover note. The complete question reaches Pro unchanged;
   the driver compares the prepared text and attachment before sending.
3. **Send once, headless by default.**
   `$JEV $D send --key <key> --prompt-file <short> --attach <document> --conversation new|<url>`
   starts the headless Chrome on the logged-in profile if none runs, sets the effort slider to
   its top position (`6 Pro`; a slider is outside Jev's action space, so arrow keys set it and
   the observed pill label is the fact) and empties a restored draft. Jev types; only when the
   box equals the short message does the driver give the document to the composer's own upload
   input (uploads are outside Jev's action space too, and a typing failure then leaves no stray
   copy in the account's file store), wait until the send button is enabled again (it is
   disabled while the file is processed, and a disabled control is not in Jev's element table),
   and let Jev click it. Before each decision the driver states the one fact Jev cannot see:
   whether the box already holds the prepared message. `--dry-run` does all of that and
   withholds the click: use it after a provider UI change, it costs no Pro request.
   `--mode headed` shows the window; use it only when a human must look (login, CAPTCHA) and
   stop the other mode first with `chrome stop`. `HMASD_JEV_DEBUG=1` traces what Jev saw and
   chose at each step. Read the result:
   - `{"error": ..., "pre_send": true}`: nothing was submitted. Repair the named fact and run
     the same command with the same key.
   - `send_attempted: true`: from here on observe only. `send_effect` is `sent` when the exact
     message was seen in the conversation, otherwise `uncertain` with `unresolved`.
   - Running `send` again under an attempted key never sends; it returns the stored operation.
4. **Wait and collect from the existing conversation.**
   `$JEV $D wait --key <key> --prompt-file <short> --answer-file <path>` runs in the background
   (default 3600 s). Once Send is accepted, Pro continues server-side; reopening Chrome does
   not restart the research request. The driver checks Chrome while waiting and, if it closes
   or its connection fails, restarts it as needed and reopens the recorded conversation.
   Browser calls and retries are bounded. The flow is: thinking → wait; stable final reply →
   save the full text; login, human verification or an unrecoverable error → return it promptly.
   `IN_PROGRESS` ends only this observation window: call `wait` again on the same key.
   Transport returns acceptance and material errors to the DM instead of leaving them behind
   an idle agent wait. Completion saves the chat text even when GitHub could not write;
   a hash mentioned in a reply is not evidence of delivery. Step 5 checks actual writeback.
   **Connector consent (owner, 2026-09-19).** When the page shows "Allow GitHub for this
   conversation", Jev answers it with "始终允许" (Always allow); the owner authorised this for the
   GitHub connector, as needed for engineering collaboration (`approval_policy`,
   `approval_connectors` in `[jev]`). The driver executes that one click only on a prompt that
   names a listed connector and records it under `approvals`. A prompt for any other connector,
   or any other consent, returns `NEEDS_HUMAN`: report it to the owner and click nothing.
   If the send could not observe the settled address (a new conversation first shows a
   provisional `/c/WEB:` address that cannot be reopened), find the conversation and pass
   `--conversation-url`. Apart from that consent, nothing here clicks.
5. **Read delivery, not the receipt.**
   `$JEV $D deliver --key <key> --branch … --source-sha … --target-path … --question-heading … --answer-out <path>`
   fetches the branch and finds the commit that filled this question's `### Answer`. `DELIVERED`
   means exactly one such commit, touching only the target file, with the question and every
   other byte unchanged and the subsection empty before; unrelated later commits do not count.
   `CONFLICT` lists what differs: preserve both versions and report, never choose silently.
   `NOT_DELIVERED` with a `"chat answer"` saved in step 4 means the author inserts that text,
   noted "saved from chat"; with only a receipt it is `answer unavailable`.
6. **Return.** Question key (the conversation address stays in the local operation file), send
   effect, completion state, delivery state with the answer commit or the saved text path and
   hash, target and headings, unresolved facts. Jev closes its own tab. Leave the headless
   Chrome running between questions; `chrome stop` ends it.

## Recovery

After an accepted Send, recovery means reopening the same conversation and checking whether
Pro is still thinking or has finished. Run `wait` with the existing key; do not resend the
question because Chrome closed or a local wait timed out. Authentication or an error that
prevents reading is reported with its concrete cause. Leave normal recovery to the driver.

Only a genuine pre-send failure may retry the original key and text. For an uncertain Send,
`reconcile --key <key>` is the existing read-only check: it releases the key once only when no
settled conversation was recorded and the exact text is still the unsent new-chat draft.
This exception does not apply to an accepted conversation. A second uncertain attempt is
reported to the DM. Private conversation URLs remain in local operation files.

Verified 2026-09-19: one real direction question sent headless as short message plus document,
consent answered by Jev, the 21 000-character answer written by Pro into the repository and
confirmed by `deliver`; after the reordering, a dry run reached the send button in two Jev steps. Verified 2026-09-18 on the WSL host: one headed and one headless test question, each typed and
sent by Jev in two steps, completed and read back exactly; a repeated `send` under the same key
did not send.
