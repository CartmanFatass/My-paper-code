# Claude Code subagent workflow for HMASD research

Owner instruction, 2026-09-05 20:31 PDT: build a Claude-flavoured subagent workflow in which the
Fable session is the research hub (Portfolio plus EM), code tasks go to Opus, scout and
mechanical tasks go to Sonnet, and everything outside the research side is delegated. Follow-up
20:39 PDT: Pro transport is to run through Agentify Desktop, once end to end, then through a
Sonnet subagent, following the Codex GitHub-collaboration flow.

This document records what was built, how it maps onto the Codex roles, and what the owner still
has to do before the first transport run. Nothing here changes scientific meaning, lifecycle, or
priority; the loop remains `OWNER_PAUSED` for Pro requests until the owner resumes it.

## 1. What was built

| Surface | Path | Role |
| --- | --- | --- |
| Hub procedure | `.claude/skills/hmasd-research-hub/SKILL.md` | Fable as Root and DM: what it keeps, what it delegates, the ladder without a Pro node, capacity, session shape |
| Transport procedure | `.claude/skills/hmasd-pro-transport/SKILL.md` | Authoring through the Codex renderer in caller-direct mode, the smoke-first rule, dispatch and intake |
| Subagents | `.claude/agents/*.md` | Eleven definitions, listed in section 2 |
| Authority | `AGENTS.md` Appendix B | Rewritten to name the hub, the two-direction cap, the worktree rule and the transport route |

Same specification files as Codex: `MARL_EMPIRICAL_EVIDENCE_SPEC.md`, `ENGINEERING_SCOPE_SPEC.md`,
`MARL_RUNTIME_ENGINEERING_SPEC.md`, all at their 2026-09-05 versions. `CLAUDE.md` imports
`AGENTS.md`; nothing is duplicated.

## 2. Role mapping

| Codex role (`.codex/agents/`) | Claude agent | Model | Change in porting |
| --- | --- | --- | --- |
| `hmasd-direction-manager` | none: the hub itself | Fable | DM procedure moved into the hub skill; Pro packets authored by the hub |
| `hmasd-cm` + `hmasd-implementer` | `hmasd-cm` | Opus | Merged: subagents cannot spawn subagents, so CM implements; it asks the hub for scout, reviewer, verifier, operator |
| `hmasd-reviewer` | `hmasd-reviewer` | Opus | Unchanged, read-only |
| `hmasd-research-critic` | `hmasd-research-critic` | Opus | Unchanged, read-only, ends with `MATERIAL_DISSENT` |
| `hmasd-cm-scout` | `hmasd-cm-scout` | Sonnet | Unchanged |
| `hmasd-routine-implementer` | `hmasd-routine-implementer` | Sonnet | Unchanged; refuses semantic choices with `REPAIR_REQUIRED` |
| `hmasd-verifier` | `hmasd-verifier` | Sonnet | Unchanged |
| `hmasd-experiment-operator` | `hmasd-experiment-operator` | Sonnet | Launch only; returns the handle, does not poll |
| `hmasd-experiment-tracker` | `hmasd-experiment-tracker` | Sonnet | Bounded observer and collector invoked by the hub; no sibling messaging exists |
| skills `hmasd-owner-item`, integration duties of Root | `hmasd-clerk` | Sonnet | New: ledger rows, `item.py` items, brief filing, cherry-pick integration, named checks, dictated commits |
| research scout mentioned by the critic | `hmasd-research-scout` | Sonnet | New: repository, literature and inventory facts with quotes |
| `hmasd-chatgpt-pro-transport` skill + Transport singleton | `hmasd-pro-transport` | Sonnet | Uses Agentify Desktop's strict `agentify_review_query` instead of `cua_repl`; GitHub-delivery mode only |

Model routing follows the owner's instruction: Opus where code is written or judged, Sonnet
where the task is retrieval, launch, observation, or a dictated mechanical edit.

## 3. Deviations from the Codex topology, stated

- **Flat dispatch.** Codex nests DM -> CM -> implementer/reviewer. Claude subagents cannot spawn
  subagents, so the hub dispatches every specialist and relays CM's requests. Follow-up messages
  to the same CM agent carry the results back.
- **No sibling messaging.** The Codex tracker sends reminders to DMs. Here the tracker is
  invoked with a bounded window and returns; the hub schedules the next observation itself.
- **Two directions, not five.** The Codex working set of five chains does not apply to a Claude
  session (owner, 2026-09-03 and 2026-09-05).
- **Transport tool.** Agentify Desktop replaces the `cua_repl` browser. The registry, bindings,
  packet renderer and GitHub delivery contract are shared unchanged, so a conversation bound by
  one loop is reused by the other.

## 4. Transport: facts found and what blocks the first run

Facts verified on 2026-09-05 evening:

- Agentify Desktop at `C:/Projects/agentify-desktop` is the owner's source checkout at commit
  `9bb2275` with a large uncommitted working tree (ten files, about 1,300 insertions and 3,000
  deletions) that implements the strict v4 review transport.
- Its GUI was last started 2026-08-31 and is not running now; its API port is not listening. Two
  `agentify-desktop mcp` stdio processes started today belong to Codex's MCP registration.
- Claude Code had no Agentify MCP registration. The session registered it at user scope with
  `claude mcp add -s user --transport stdio agentify-desktop -- node C:\Projects\agentify-desktop\bin\agentify-desktop.mjs mcp`;
  the tools appear after the Claude session restarts.
- The strict transport hard-coded the provider model label `GPT-5.6 Sol` with effort `Pro` in
  three gates: `review-transport.mjs` line 159, `http-api.mjs` line 824, `state.mjs` line 89. The
  owner's provider requirement since 2026-09-04 (`.codex/hmasd-transport.toml`) is GPT-6 Astra in
  Pro mode, visible label `6 Pro`, selector `Latest`. With the old gate, a `6 Pro` request was
  rejected before any Send.
- **Gate updated 2026-09-05 20:54 PDT on the owner's instruction** ("更新到6Pro"), in the owner's
  Agentify working tree (still uncommitted there, on top of the owner's own diff): `state.mjs` now
  exports `CHATGPT_REVIEW_PRODUCT_MODELS = ['GPT-6 Astra', 'Latest']`,
  `CHATGPT_REVIEW_LEGACY_PRODUCT_MODELS = ['GPT-5.6 Sol']` and `CHATGPT_REVIEW_REASONING_EFFORT =
  'Pro'`; `review-transport.mjs` and `http-api.mjs` gate new requests on the first list;
  `validateTargetAxes` also accepts the legacy label so the persisted `review-transport.json`
  with its one historical operation still loads; the MCP tool description names the new target.
  Checked directly: the persisted state loads; `GPT-5.6 Sol` and `GPT-5.6 Pro` are rejected with
  `review_invalid_request {field: productModel}`; `GPT-6 Astra` and `Latest` pass the gate. The
  Agentify test suite could not confirm this: at baseline all four affected test files already
  fail at import (`inspectReviewAdmission` no longer exported by the owner's rewrite), unrelated
  to this change.
- The model-menu reader matches the requested label exactly against the open picker's
  `menuitemradio` entries. Whether the live picker shows `GPT-6 Astra` or `Latest` as the checked
  item can only be observed live; the transport agent preflights `GPT-6 Astra` first, then
  `Latest`, and sends with whichever matched.

Owner actions before the smoke, in order:

1. Start the Agentify GUI (`npm run start` in the checkout) and sign in to ChatGPT in its Chrome
   CDP profile.
2. Restart the Claude Code session so the `mcp__agentify-desktop__*` tools load.
3. Ask the hub to run the smoke described in `.claude/skills/hmasd-pro-transport/SKILL.md`. It uses
   a fresh conversation and a plain prompt; it never touches a bound node and does not count as a
   Pro request under the pause.

After a passing smoke, the first scientific dispatch from Claude waits for the owner to lift the
`OWNER_PAUSED` state on Pro requests; the recorded direction handoffs of 2026-09-05 name what each
direction would send next.

## 5. What was deliberately not built

No heartbeat automation, no standing tracker, no registry or validator beyond the Codex scripts
already in `.agents/skills/`, no change to `.codex/`, no change to the Agentify checkout, no new
owner-console surface. `ENGINEERING_SCOPE_SPEC.md` section 4 applies to workflow code as it does
to research code.
