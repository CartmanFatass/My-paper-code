# Retired-role remnants removed — Claude hub, 2026-09-16 17:20 PDT

Owner instruction 17:13 PDT: Root/DM, Portfolio (owner-triggered), Transport and Monitor stay;
the other roles were already deprecated and their remnants in the active workspace may be
cleaned up. CM and Implementer were suspended by OWNER_DIRECT 2026-09-12 and had no accepted
work pending closeout on any current handoff.

| Time (PDT) | Surface | Change | Why | Trace |
| --- | --- | --- | --- | --- |
| 17:18 | `.codex/agents/hmasd-implementer.toml` | Deleted. Not registered in `.codex/config.toml` since the migration; no live reference in AGENTS, CLAUDE, skills or the publisher. | Retired role. | this commit |
| 17:18 | `.claude/agents/hmasd-cm.md` | Deleted (Opus CM role, suspended, closeout-only). | Retired role. | this commit |
| 17:18 | `.claude/agents/hmasd-routine-implementer.md` | Deleted (Sonnet implementer, suspended, closeout-only). | Retired role. | this commit |
| 17:18 | `.agents/skills/hmasd-direction-management/` | Empty untracked directory removed (only an empty `references/` inside). | Leftover from an earlier skill removal. | not in Git |
| 17:19 | verification | `python tools/publish_claude_control.py --check` → drift 0; `tests/skills/test_control_publication.py` 3 passed on the `hmasd-science-tools` (3.11) environment. The 3.10 main environment cannot import `tomllib`, so the publisher and its test need the 3.11 interpreter. | Publisher ROLE_MAP never mapped the deleted roles. | this commit |
| 17:19 | not changed | `.claude/agents/hmasd-clerk.md`, `.claude/skills/hmasd-grok-cm/SKILL.md`, `hmasd-cm-scout.md` (scout, not CM). The AGENTS/CLAUDE sentences saying CM/Implementer "remain suspended" stay true and were not rewritten (owner: no further governance rewrite). Whether Grok clerk mode and the Sonnet clerk survive is an `[ASK]` in `docs/Claude_docs/plans/OPERATING_CONSTITUTION_DRAFT_20260916.md`. | Owner decision pending. | none |

Historical evidence that names the deleted files (migration BASELINE/CHECKS JSON, older
handoffs) is unchanged; the files remain readable at any earlier commit.
