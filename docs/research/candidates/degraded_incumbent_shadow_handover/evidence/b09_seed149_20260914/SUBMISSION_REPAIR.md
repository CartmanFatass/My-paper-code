# B09 supervisor serialization repair

The first supervisor handle was accepted but failed with exit2 before memory admission.
Its retained runner reconstructs `bash -lc cd /home/wu/hmasd-worktrees/... && ...` because
`agent-task run` stores its command as `COMMAND="$*"` before a later `eval`. Argument
boundaries of the separately supplied `bash -lc` were lost; the bare `cd` ran in a child
shell and the following preflight was looked up under `/home/wu/scripts`, where it does
not exist. The requested scientific output and intended receipt paths are absent.
The unintended home receipt contains only `preflight_wall.txt`; no memory JSON, scientific
master, model, native trajectory or runner output was created. Exit2, complete failed
wrapper/log, supervisor source and exact path-existence evidence are preserved in
SUBMIT01_RECONCILIATION.json; the original launch/readback/monitor receipts remain intact.
This is verified non-execution of the scientific pair, not an incomplete scientific run.

DM options: repair the shell serialization and execute the frozen pair; abandon this
useful object solely for the wrapper error. Owner-delegated decision (unattended,
2026-09-03 instruction): repair once using EXECUTION_PLAN_SUBMIT02.json. Pass the whole
reviewed shell command as one argument directly to `agent-task run`, using Python
`shlex.join([supervisor, "run", new_handle, command])` for the remote shell. Do not add
separate `bash -lc` arguments. A shlex parse round trip preserves the exact four arguments.
The supervisor then evaluates `cd ... && export ... && admission && runner` in one shell.
Use a new handle ending `-submit02` so the failed handle cannot be overwritten.

Source SHA3a749256, seed149, both fresh arms, output rootrun01, frozen endpoints and all
2700s planning bounds stay unchanged. The180s prelaunch conservative charge includes
failed submission0.7703465s, readback0.4175575s, monitor1.9s, reconciliation0.7063891s and
bounded repair work; these are not reset or double-added. This allocation is not a
measured complete-cost claim. No scientific retry/extra exposure, repeated source test,
platform change or Root escalation is required. Fresh actual-node admission remains
immediately joined to the runner. Reuse the batch's Monitor with its new exact handle.
If another effect is uncertain, reconcile it before any further submission.
