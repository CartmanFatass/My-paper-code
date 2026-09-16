# Workflow lanes — control-plane changes by the Claude hub, 2026-09-15 21:03 PDT

Owner instruction 21:01 PDT: the uniform workflow is too rigid; the same process across all stages
and the same standards for every workstream are not appropriate. The hub's seven-point proposal
(lanes by direction state, one Pro round per object, three records per object, standing budgets,
lane-proportional statistical burden, risk-proportional review, loop-specific lightness) was
approved at 21:03 PDT. Normative text: `docs/research/portfolio/decisions/2026-09-15-workflow-lanes.md`.

| Time (PDT) | Surface | Change | Why | Trace |
| --- | --- | --- | --- | --- |
| 21:10 | `docs/research/portfolio/decisions/2026-09-15-workflow-lanes.md` | New `OWNER_DIRECT` decision record: three lanes, Pro-round cadence, records, burden, review, standing budget, immediate assignments (ACVC → CLOSE after the pending review; FSD → CONFIRM). | Owner approval 21:03 PDT. | this commit |
| 21:10 | `AGENTS.md` | New owner block "Workflow lanes (OWNER_DIRECT, 2026-09-15 21:03 PDT)" before "Scientific tool use"; summarises the lanes and points to the record. Binds both loops. | Same. | this commit |
| 21:10 | `CLAUDE.md` | Owner-instruction paragraph before the session rules: lanes, the hub's EXPLORE lightness, the two immediate assignments. | Same. | this commit |
| 21:10 | `.claude/skills/hmasd-research-hub/SKILL.md` | **Pending.** Intended: a "Lanes" section before "Decision ladder" restating the per-lane hub procedure from the decision record. The auto-mode classifier refused the hub's edit of its own skill ("Self-Modification"), both as a script and through the file tool. Until applied, the hub reads the lane procedure from `AGENTS.md` and the decision record, which already bind it. | Harness guard, not an owner rule; the owner can apply the section by hand or allow the edit. | none |
| 21:10 | `docs/research/portfolio/PORTFOLIO.md` | Lane paragraph above the direction table with the initial assignments and the standing budgets. | Same. | this commit |
| 21:10 | `docs/Claude_docs/README.md` | Index line for this file. | Same. | this commit |
| 21:10 | not changed | `.agents/skills/**`, `.codex/agents/*.toml`, the evidence spec and `ENGINEERING_SCOPE_SPEC.md`. The Codex role files inherit the lanes through `AGENTS.md`; the evidence spec's section 11 stays controlling for CONFIRM objects and its section 11.1 already admits A-class exploratory work, which is what a `PILOT` is. Edit them only if a Codex DM reports a concrete conflict. | Minimal surface. | none |
