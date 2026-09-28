# 2026-09-28 — Oracle subagent at max effort; daily delegation keeps high

Owner instruction (2026-09-27 PDT / 2026-09-28 UTC, Claude WSL session): most work does not need
Fable at max effort. Daily delegation keeps the current default `high` for cost and time; an
**Oracle** subagent runs Fable 5.1 at **max** effort and is used only for research decisions and
planning.

## Change

- New `.claude/agents/hmasd-oracle.md`: `model: fable`, `effort: max`, read-only tools
  (Read, Grep, Glob, Bash, WebSearch, WebFetch). Both values are accepted by the installed CLI
  (2.1.283: model aliases `sonnet/opus/haiku/fable`, effort `low/medium/high/xhigh/max`).
  The body is directly maintained as a Claude-only role: the session's own DM reasoning at higher
  effort for question/approach selection, experiment design, material interpretation or route
  correction. It returns a decision memo; the session accepts, reviews and publishes. It edits,
  launches, sends and spawns nothing. It is not the Scientific Reviewer: an Oracle plan still goes
  to `hmasd-research-critic` in a separate context under constitution section 5, and
  MATERIAL_DISSENT stays with that reviewer. No section-2 role or authority is added.
- `tools/publish_claude_control.py`: `DIRECT_AGENTS = {'hmasd-oracle'}` — `--check` neither
  regenerates nor reports a directly maintained Claude-only agent; every other `hmasd-*.md`
  stray is still reported. Test `test_direct_agent_is_not_reported_but_strays_still_are`.
- `CLAUDE.md`: one sentence naming the Oracle and the effort policy (separate commit).
- Other agents' `model`/`effort` unchanged (see 2026-09-26-subagent-effort-levels.md); AGENTS.md,
  the constitution, Codex role files and generated bodies untouched.

Effort is configured through the documented subagent frontmatter field; whether the runtime honours
it is not observable from inside a session (CLAUDE.md rule), so report it as configured, not verified.

Owner authority: 2026-09-15 lifting of the control-plane restriction (any file, traceable in Git,
documented here). No science, run, record type or message channel changed.
