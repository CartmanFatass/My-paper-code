# Experiment observation ownership

This document owns experiment observation and handover procedure. AGENTS §5–7 controls
scientific execution, resources and Git; ROOT_OPERATIONS.md assigns planning and acceptance.
Independent Transport observes Pro requests under its own skill.

## Assignment and handover

The assigned CM or Experiment Operator observes the exact accepted handle through terminal
collection by default. The CM owns technical acceptance even when an Operator executes. The
existing run record and EXPERIMENT_TRACKING.md identify the actual observer, node, supervisor
handle, launch SHA, cwd, result/receipt paths and responsible CM/DM. An accepted-handle return
is a state change, not a request for Root to poll in parallel. No new registry is required.

If the observer must end its assignment before termination, or loses access, request a concrete
handover to Root (endpoint in `.codex/hmasd-monitor.toml`) or the named existing executor. The
recipient verifies access to the same supervisor/witness, records adoption in current tracking
and confirms it to the assigning parent. Until confirmed, the prior observer retains responsibility
or explicitly records that observation is lost. A sender's return alone does not transfer ownership.
Root reconciles an idle/unavailable observer at the next event boundary and takes over or assigns
recovery of that same handle. This never authorizes another launch.

Use SIBLING_COMMUNICATION.md for native/app addressing. Do not send adoption requests to yourself.
A private exec session number alone cannot transfer access; local work requires PID/start identity
and the existing exit witness. Preserve owner pause and existing launch bounds.

## Bounded observation and collection

Observe only assigned handles, batch independent read-only checks and retain exact unknown state.
Use the configured node/supervisor from `.codex/hmasd-compute.toml`; for the current remote node:
`ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status <accepted-name>`.
Read bounded logs only when useful. Quote supplied names as data. SSH failure or PID absence alone
is unknown; a wait timeout is not terminal. Exit zero is a process fact, not scientific validity.

Healthy unchanged state needs no repeated messages or commits. At terminal status, the assigned
executor collects the named outputs and direct process facts, verifies artifact integrity and
returns them to the actual assigning parent. CM performs technical acceptance; DM performs
scientific intake. Lost observation or a material bound/dependency failure returns promptly with
evidence. Follow the loop skill for continuation; do not wait for unrelated directions.

Root maintains compact current tracking at meaningful adoption, terminal and continuation changes,
linking the original run/collection/intake records. Record observer changes explicitly; the act of
tracking a handle does not make Root its observer. Historical handles are not adopted by scanning
archives. No standing monitor agent, scheduler, per-run observation worktree or parallel polling
loop is added. The owner's active goal and assigned native work drive observation. On owner pause,
preserve accepted handles and arrange the observation handover or closeout specified by that pause.
