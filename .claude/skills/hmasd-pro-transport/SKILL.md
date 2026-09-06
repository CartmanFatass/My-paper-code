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
3. **Create the delivery surface**: a dedicated branch `claude/pro-<direction>-<round>-<date>` at
   the full base sha, pushed; reuse the direction's substantive Issue or open one.
4. **Render** with the Codex renderer in caller-direct mode, so no Codex singleton is implied:

   ```
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe .agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py REQUEST.json --out-dir <packet folder>
   ```

   `REQUEST.json` carries `execution_mode: "CALLER_DIRECT"`, `owner_execution_instruction` quoting
   the owner's instruction that Claude may operate transport, `delivery_mode: "github_delivery"`,
   `github_delivery {branch, base_sha, response_path, issue_url}`, `commit_or_ref` = full sha, and
   `conversation_id` when the key is already bound. The renderer requires UUID-shaped
   `source_thread_id` and `parent_thread_id`: use one UUID5 derived from this Claude session URL
   for both (`uuid.uuid5(uuid.NAMESPACE_URL, "<session url>")`), and record that derivation in the
   packet's `DISPATCH_RECORD.json`. They are routing metadata, never prose.
5. **Commit and push `TASK.md`** by explicit pathspec, resolve its full sha, then
   `render_packet.py --bind-task-sha <sha> --handoff-path <HANDOFF.json>`; commit and push the
   bound handoff. `dispatch_state` must read `READY_TO_DISPATCH`.
6. **Dispatch** `hmasd-pro-transport` once with the handoff path and `mode: scientific`, an
   observation window, and nothing else. Read its return as transport facts. An uncertain send is
   terminal for that request id; a new request id is a new decision, not a retry.
7. **Intake**: read the full response from the archive's `GITHUB_RESPONSE.md` (verified against the
   immutable commit), not the short chat receipt. Check the formed decision against current owner
   instructions and specifications; a complete answer does not authorize a silent exception. Write
   the intake, apply the decision, label it `PRO_FINAL`, and record the archive paths.

## The first run is a smoke, not a request

Before any scientific dispatch from Claude, run one non-scientific transport check:

- Preconditions the owner controls: Agentify Desktop GUI running and signed in to ChatGPT in
  its Chrome CDP profile; the Agentify MCP server registered for Claude Code
  (`claude mcp add -s user --transport stdio agentify-desktop -- node C:\Projects\agentify-desktop\bin\agentify-desktop.mjs mcp`)
  and the session restarted so the `mcp__agentify-desktop__*` tools exist; the strict transport's
  compiled model label accepting the current provider selection in `.codex/hmasd-transport.toml`.
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
