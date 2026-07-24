# HMASD Claude Code Entry

`AGENTS.md` is the sole workflow and authority contract for this repository.
Do not maintain a second algorithm, experiment, review, Git, or memory workflow
in this file.

Read `AGENTS.md` first, then use the exact role routing defined there.
Controller work uses the active files in `docs/project/`. Every bounded role is
a subagent defined under `.claude/agents/`; executable implementation
assignments go to `hmasd-implementer`, and `AGENTS.md` holds the full roster
with its model tiers. Project implementation procedure is
`$hmasd-agile-research-development`; external review transport is
`$hmasd-review-round`.

If `CURRENT_WORK.md` names another active controller, remain read-only unless
an explicit handoff changes ownership. Treat Git-tracked current code as the
implementation source and `logs/<run-id>/` as runtime evidence. Historical
modules, commands, rounds, and archived artifacts are not active instructions.
