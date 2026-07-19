# HMASD Claude Code Entry

`AGENTS.md` is the sole workflow and authority contract for this repository.
Do not maintain a second algorithm, experiment, review, Git, or memory workflow
in this file.

Read `AGENTS.md` and `.agents/skills/hmasd-task-router/SKILL.md` first, then use
the exact role routing defined there. Controller work uses the active files in
`docs/project/`; executable implementation assignments use
`$hmasd-implementer`; external review and monitoring use only their dedicated
role Skills.

If `CURRENT_WORK.md` names another active controller, remain read-only unless
an explicit handoff changes ownership. Treat Git-tracked current code as the
implementation source and `logs/<run-id>/` as runtime evidence. Historical
modules, commands, rounds, and archived artifacts are not active instructions.
