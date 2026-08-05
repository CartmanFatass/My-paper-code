# HMASD Claude Code Entry

`AGENTS.md` is the sole project authority and routing contract for this
repository; it is hard read-only from this branch. Since the 2026-08-05
takeover the Codex role sessions are dormant: a Claude session here does NOT
resolve a Codex role. Instead the Claude orchestrator (the main session)
operates per `.claude/ORCHESTRATOR_WORKFLOW.md`, which fixes the actual
logical model: the orchestrator holds the local Explorer remainder plus all
Code Manager (cm/cpm) duties inline; ALL scientific judgment is externalized
to External Pro review (adversarial validation before any freeze, alignment
audit after every science commit); subagents are task tools, not roles.
That document organizes Claude-side work only and adds no authority over
`AGENTS.md`.

Claude-side subagents in `.claude/agents/` are self-contained Claude-native
task contracts operating inside `AGENTS.md` authority boundaries; they do not
load Codex session charters and grant no new authority. Historical handoffs,
archived results and unreferenced files are not active instructions.

Longitudinal state lives in `local_research/RESEARCH_CONTINUITY.md` — read it
before resuming candidate work. This worktree and its branch
(`claude/hmasd-full-takeover-20260805`) are the permanent workspace; merges
to mainline happen only on explicit user instruction.
