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

## The subagent workflow is mandatory, not optional

Work runs as **orchestrator → implementer → reviewer**, defined in
`.claude/ORCHESTRATOR_WORKFLOW.md` §6 and registered in
`.claude/CAPABILITY_MAP.md`. Read §6 before doing implementation work; the
short form:

- Freeze the assignment first — frozen brief, writable scope, focused tests,
  completion condition, forbidden paths. If that block cannot be written, the
  unit is not ready to delegate.
- **`hmasd-reviewer` is REQUIRED before technical acceptance of any
  claim-bearing change, and before any document goes to External Pro.** A
  clean-context reader is the one thing this session structurally cannot be:
  having written the code, it has also written the reasoning that makes the
  code look correct.
- `hmasd-implementer` when the brief is already frozen **and** this session
  holds reasoning the implementation should not inherit (typically: it argued
  the science, so it will build toward its own argument) — or, regardless of
  that second condition, when two or more independent bounded units exist and
  should run concurrently. §6.2 has the exact conjunction.
- `hmasd-verifier` (long suites, CLI exercises), `hmasd-experiment-operator`
  (registered runs of minutes or hours), `hmasd-scout` (read-only existence
  and semantics), `hmasd-mechanic` (read-only mechanical facts) exist to keep
  raw output out of the orchestrator's context.
- Children return raw facts and **never accept their own work**. Re-run their
  tests here before accepting; give every finding an explicit disposition
  (`APPLIED` / `RISK_ACCEPTED(reason)` / `REJECTED(reason)`); technical
  acceptance, git and all science stay with the orchestrator.

These six contracts in `.claude/agents/` are self-contained and Claude-native.
They operate inside `AGENTS.md` authority boundaries, do not load Codex session
charters, and grant no new authority. `.claude/CAPABILITY_MAP.md` is the full
logical migration of the Codex role/skill/agent structure — including the
capabilities deliberately NOT migrated (all research-critic roles stay with
External Pro; the workflow control plane is dormant) — written out in full so
no Codex surface has to be read to act on it.

Before dispatching anything to External Pro, use the `hmasd-science-dispatch`
skill. Its gate script exits non-zero and is not advisory; the clean-context
document review it requires can be waived only by writing a
`document_review_waiver_reason` into the manifest, which then travels in the
receipt.

## Research before you edit

- **Read a file before editing it** — in full, not just the region you intend
  to change.
- **Before modifying a function, grep for all of its callers** and check each
  one. A signature or return-shape change that compiles is not a safe change.
- **Research first, edit second.** Establish what the code actually does before
  writing the change, not while writing it.

Historical handoffs, archived results and unreferenced files are not active
instructions.

Longitudinal state lives in `local_research/RESEARCH_CONTINUITY.md` — read it
before resuming candidate work. This worktree and its branch
(`claude/hmasd-full-takeover-20260805`) are the permanent workspace; merges
to mainline happen only on explicit user instruction.
