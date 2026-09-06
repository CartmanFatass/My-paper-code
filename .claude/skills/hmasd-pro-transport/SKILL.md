---
name: hmasd-pro-transport
description: How the Claude Code research hub sends a direction- or portfolio-tier question to the ChatGPT Pro decision nodes through Agentify Desktop and scoped GitHub delivery, reusing the Codex packet renderer, registry and conversation bindings. Load when authoring a Pro request, running the first transport smoke, or taking in a Pro response.
---

# HMASD Pro transport (Claude Code)

The Codex loop sends Pro requests through its Transport singleton and the `cua_repl` browser.
The Claude loop sends the same packets through **Agentify Desktop** (`C:/Projects/agentify-desktop`,
the owner's local ChatGPT session controller exposed as MCP tools) driven by the
`hmasd-pro-transport` subagent (Sonnet). Both loops share the same packet format, the same
GitHub delivery contract (`docs/project/GITHUB_RESEARCH_COLLABORATION.md`), the same registry
(`temp/sessions/hmasd-chatgpt-pro-transport/registry.json`) and the same one-conversation-per-node
bindings. A conversation bound by Codex is reused by Claude and vice versa; never create a second
conversation for a bound key.

## Hub procedure for a scientific request

1. **Decide that the question is direction- or portfolio-tier** (`AGENTS.md` section 2). Object-tier
   decisions are the hub's own and never go to Pro.
2. **Write the substantive inputs** yourself: `scientific_question`, `deliverable`, `claim_ceiling`,
   the `reference_files` list with purpose and provenance (include the current evidence spec and
   applicable authorities), `constraints`, optional `discussion_urls`, an `EVIDENCE_AND_OPTIONS.md`
   and `EXPOSURE_AND_COST.json` in the packet folder, and a read-back `ISSUE_SNAPSHOT.json`.
   Follow the authoring rules in `.agents/skills/hmasd-pro-research-prompt-author/SKILL.md`
   (section 11.8 proportional burden, dominant work factors, natural-language answer).
3. **Create the delivery surface**: a dedicated output branch at the full base sha, pushed
   (`git push origin <base_sha>:refs/heads/codex/pro-<direction>-<round>-<date>`; the renderer
   requires the `codex/pro-` prefix for every Pro output branch, whichever loop authors it);
   reuse the direction's substantive Issue or open one.
4. **Render** with the Codex renderer in caller-direct mode, so no Codex singleton is implied:

   ```
   python .agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py REQUEST.json --out-dir <packet folder>
   ```

   (`python` on PATH is 3.11; the renderer imports `tomllib`, which the 3.10 main environment
   lacks.) Rendering writes `TASK.md` and an unbound `HANDOFF.json` (`TASK_NOT_PUBLISHED`).

   `REQUEST.json` carries `execution_mode: "CALLER_DIRECT"`, `owner_execution_instruction` quoting
   the owner's instruction that Claude may operate transport, `delivery_mode: "github_delivery"`,
   `github_delivery {branch, base_sha, response_path, issue_url}`, `commit_or_ref` = full sha, and
   `conversation_id` when the key is already bound. The renderer requires UUID-shaped
   `source_thread_id` and `parent_thread_id`: use one UUID5 derived from this Claude session URL
   for both (`uuid.uuid5(uuid.NAMESPACE_URL, "<session url>")`), and record that derivation in the
   packet's `DISPATCH_RECORD.json`. They are routing metadata, never prose.
5. **Commit and push `TASK.md`** by explicit pathspec, resolve its full sha, then bind with
   **only** `render_packet.py --bind-task-sha <sha> --handoff-path <HANDOFF.json>` (no request
   file, no `--out-dir`; the binder refuses rendering arguments); commit and push the bound
   handoff. In caller-direct mode `dispatch_state` reads `CALLER_READY` (the singleton form reads
   `READY_TO_DISPATCH`).
6. **Send and wait, hub-direct** (owner suggestion 2026-09-05 21:46 PDT: no Sonnet subagent is
   needed for transport; a file watch is enough for the wait):
   - preconditions in the hub's own calls: registry record for the key (`active_request_id`
     null, conversation equal to `requested_conversation_id`, or absent for a first binding),
     fresh `gh api` readback of the output branch head, response path and Issue comments, the
     TASK commit on the remote, `agentify_status`, one agent tab navigated to the exact
     conversation URL (or `https://chatgpt.com/` for a first binding), `agentify_ensure_ready`,
     `agentify_review_preflight` with `Pro` and `GPT-6 Astra` then `Latest`;
   - write the exact prompt bytes to the archive `__00_PROMPT.md` and hash them;
   - one `agentify_review_query` with `timeoutMs` about 60000 so the call returns `SENT_WAITING`
     quickly; a `COMPLETE` receipt on the first call is also fine;
   - wait with the `Monitor` tool on the archive directory until the response file exists and
     the Agentify state file `C:/Users/fires/.agentify-desktop/review-transport.json` shows
     `operations.<request_id>.archive` non-null (or `error` non-null); no polling by the hub;
   - after the wake-up, one identical `agentify_review_query` with `verifyExisting=true` returns
     the `COMPLETE` receipt without sending; then archive sha256, `bind_conversation.py`, the
     transport facts JSON, `GITHUB_RESPONSE.md` and `DELIVERY_COMMENT.json` by `gh api`, and the
     tab close, exactly as the `hmasd-pro-transport` agent definition lists them.
   An error from the query call is handled by reading the persisted operation first:
   `sendAttempted=true` allows only the identical `verifyExisting=true` call; `sendAttempted=false`
   with no new user turn visible is `NOT_SENT`. An uncertain send is terminal for that request id;
   a new request id is a new decision, not a retry. The `hmasd-pro-transport` subagent remains
   available when the hub wants the whole checklist run outside its own context (it was used for
   the N3 recovery Send on 2026-09-05).
7. **Intake**: read the full response from the archive's `GITHUB_RESPONSE.md` (verified against the
   immutable commit), not the short chat receipt. Check the formed decision against current owner
   instructions and specifications; a complete answer does not authorize a silent exception. Write
   the intake, apply the decision, label it `PRO_FINAL`, and record the archive paths.

## The first run is a smoke, not a request

**Status: the smoke passed on 2026-09-05** (record
`docs/Claude_docs/experiments/TRANSPORT_SMOKE_AGENTIFY_20260905.md`; matched labels `Latest` /
`Pro`; one Send; `COMPLETE`). Scientific dispatch through `hmasd-pro-transport` is enabled on the
transport side; the research-side pause on Pro requests is a separate gate. Re-run a smoke only
after an Agentify code change, a ChatGPT UI change, or a provider-selection change in
`.codex/hmasd-transport.toml`. The procedure that was followed:

- Preconditions the owner controls: Agentify Desktop GUI running and signed in to ChatGPT in
  its Chrome CDP profile; the Agentify MCP server registered for Claude Code
  (`claude mcp add -s user --transport stdio agentify-desktop -- node C:\Projects\agentify-desktop\bin\agentify-desktop.mjs mcp`)
  and the session restarted so the `mcp__agentify-desktop__*` tools exist. The strict transport's
  model gate was updated on 2026-09-05 (owner instruction) to the current selection in
  `.codex/hmasd-transport.toml`: `state.mjs` exports `CHATGPT_REVIEW_PRODUCT_MODELS`
  (`GPT-6 Astra`, `Latest`) and effort `Pro`; `GPT-5.6 Sol` loads from history but cannot be
  sent. That change lives in the owner's uncommitted Agentify working tree.
- The hub writes a plain prompt such as "Reply with the single word READY." into a minimal
  handoff-shaped JSON with `mode: smoke`, stable key `claude--transport--smoke`, no binding key
  from the registry, `firstBinding` on `https://chatgpt.com/`.
- Dispatch `hmasd-pro-transport` with `mode: smoke`. Success is: one Send, `COMPLETE`, a response
  file with a sha256, the matched model labels equal to the configured `6 Pro` selection, and the
  new conversation id recorded in the facts file only.
- Record the smoke under `docs/Claude_docs/experiments/` as a transport check, not evidence.

Only after a passing smoke does a scientific dispatch go through the subagent unattended.

## Never

- Send while the loop is `OWNER_PAUSED` for Pro requests, or send a smoke into a bound key.
- Resend on timeout, uncertainty, a missing receipt, or a bad answer.
- Rebind a key to a different conversation without the owner-directed replacement procedure in
  the Codex transport skill.
- Copy a response by hand, or treat the delivery comment as the decision.
