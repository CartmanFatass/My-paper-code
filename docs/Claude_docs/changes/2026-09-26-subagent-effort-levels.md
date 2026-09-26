# 2026-09-26 — Explicit reasoning effort in Claude subagent frontmatter

Owner instruction (2026-09-26, Claude WSL session): custom subagent files must state the
reasoning effort level explicitly — Implementer: Opus, high; Scout: Sonnet, medium; simple
mechanical tasks: Haiku, high.

Change: every `.claude/agents/hmasd-*.md` frontmatter now carries `effort:` next to `model:`.
The field and its values (`low`, `medium`, `high`, `xhigh`, `max`) are the documented subagent
frontmatter fields (code.claude.com/docs/en/subagents.md, "Overrides session level").

| Agent | model | effort | Note |
| --- | --- | --- | --- |
| hmasd-implementer | opus | high | as requested |
| hmasd-cm-scout, hmasd-research-scout | sonnet | medium | as requested |
| hmasd-experiment-operator | haiku (was sonnet) | high | the one simple mechanical role: launches one frozen command and returns facts |
| hmasd-verifier | sonnet | medium | bounded probe role; kept Sonnet, effort like the scouts |
| hmasd-reviewer, hmasd-research-critic | opus | high | Opus-class analysis roles; effort set like the Implementer |

Only the frontmatter header changed; generated bodies are untouched and
`tools/publish_claude_control.py --check` reports `drift: 0` (the publisher preserves the header).
Owner may reassign verifier/reviewer/critic levels; they were not named in the instruction.
