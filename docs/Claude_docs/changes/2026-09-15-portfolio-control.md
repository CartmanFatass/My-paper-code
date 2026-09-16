# Portfolio control and the approved set — control-plane changes by the Claude hub, 2026-09-15 21:37 PDT

Owner instruction 21:35 PDT: take Portfolio interaction out of the automated loop; execution follows
the set explicitly selected by Portfolio review; concurrency is a ceiling, not a quota; no refilling
of slots. The hub's redrafted plan was approved at 21:37 PDT. Normative text:
`docs/research/portfolio/decisions/2026-09-15-portfolio-control-and-approved-set.md`.

| Time (PDT) | Surface | Change | Why | Trace |
| --- | --- | --- | --- | --- |
| 21:45 | `docs/research/portfolio/decisions/2026-09-15-portfolio-control-and-approved-set.md` | New `OWNER_DIRECT` decision record: owner-triggered review, approved set as the only runnable set, ceiling not quota, CLOSE leaves the set without refill, batches and stickiness inside the set, dossier format, initial approved set. | Owner approval 21:37 PDT. | this commit |
| 21:45 | `docs/research/portfolio/APPROVED_SET.md` | New authority file, v1: approved = flexible_skill_duration (CONFIRM, priority 1); parked backups vap_folr_core, tail_return_distributional_learning; acvc left the set (CLOSE); queued items for the next review. | Same. | this commit |
| 21:45 | `AGENTS.md` | Owner paragraph "Portfolio control" at the top of section 5; the vacancy-replacement sentence in section 1 and the "fewer than three occupied slots / three is a target" sentences in section 2 replaced by pointers. Remaining "three chains" wording in section 5 is declared superseded by the paragraph rather than rewritten line by line. | Same; minimal, traceable edits. | this commit |
| 21:45 | `.agents/skills/hmasd-loop-dispatch/SKILL.md` | Steps 4 and 5 of the stable next-action trigger replaced: no slot counting, no replacement question; queue memos for the owner-triggered review. | Same. | this commit |
| 21:45 | `.claude/skills/hmasd-research-hub/SKILL.md` | Capacity section: two is a ceiling; hub advances the approved set only; no refill; stickiness. (If this row shows "pending" in the commit, the auto-mode classifier refused the hub's edit of its own skill; the rule binds through `AGENTS.md` and the decision record meanwhile.) | Same. | this commit |
| 21:45 | `CLAUDE.md` | Owner-instruction paragraph before the session rules. | Same. | this commit |
| 21:45 | `docs/research/portfolio/PORTFOLIO.md` | Header paragraph replaced: no "4 occupied / 0 reserved / 0 vacant" working set; points to the approved set. | Same. | this commit |
| 21:45 | not changed | `.agents/skills/hmasd-portfolio-task/SKILL.md` (still the packet format for an owner-triggered review), `.codex/agents/*.toml`, `docs/project/ROOT_OPERATIONS.md`. Their slot/refill wording is superseded by the `AGENTS.md` paragraph; edit only if a Codex session reports a concrete conflict. | Minimal surface. | none |
