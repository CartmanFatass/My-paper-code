# HMASD Claude Code Entry

`AGENTS.md` is the sole workflow, authority and routing contract for this
repository. Read it first, resolve exactly one active role, then load only the
role, Skill and assignment paths it names.

Claude-side subagents in `.claude/agents/` are self-contained Claude-native
task contracts operating inside `AGENTS.md` authority boundaries; they do not
load Codex session charters and grant no new authority. Historical handoffs,
archived results and unreferenced files are not active instructions.

The Claude orchestrator workflow — lanes, subagent/model mapping, transport
and External Pro session separation — is fixed in
`.claude/ORCHESTRATOR_WORKFLOW.md`. That document organizes Claude-side work
only and adds no authority over `AGENTS.md`.
