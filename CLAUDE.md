# HMASD Claude Code Entry

`AGENTS.md` is the sole workflow and authority contract for this repository.
Do not maintain a second algorithm, experiment, review, Git, or memory workflow
in this file.

Read `docs/project/CURRENT_WORK.md` first. Load the other files in
`docs/project/` only through the routing rules in `AGENTS.md`:

- `ALGORITHM_PRINCIPLES.md` for scientific decisions;
- `MARL_ENGINEERING_PRINCIPLES.md` for executable MARL work;
- `IMPLEMENTATION_PLAN.md` for the one active staged contract;
- `ExpRecord.md` for formal experiment contracts and dispositions.

If `CURRENT_WORK.md` names another active controller, remain read-only unless
an explicit handoff changes ownership. Treat Git-tracked current code as the
implementation source and `logs/<run-id>/` as runtime evidence. Historical
modules, commands, rounds, and archived artifacts are not active instructions.
