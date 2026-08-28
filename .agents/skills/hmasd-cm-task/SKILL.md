---
name: hmasd-cm-task
description: Use when a top-level HMASD CM direction task receives a bounded implementation, test, integration, prepare, execution, or technical-repair slice.
---

# HMASD CM Task

Read `docs/project/WORKFLOW_PROTOCOL.md`, native WORK/CONTROL history, direction authority, and current engineering state if it exists. CM implements and verifies ordinary work in its main session.

## Surface first

For a nontrivial unfamiliar code change, call `hmasd-cm-scout` before implementation unless the current milestone/state already has a trustworthy surface map. Freeze affected files, symbols, callers, consumers, tests, shared boundaries, semantics, Effects, and owned paths. Reuse a current map; do not respawn Scout mechanically.

## Direct implementation

CM directly edits code, writes focused tests, diagnoses failures, performs ordinary runtime checks, interprets engineering evidence, updates state, and closes Git. Do not create an Implementer leaf.

CM is the sole Git-visible writer for the direction worktree from acceptance of the EM WORK until
terminal RESULT. Verify that the EM handoff commit and exact baseline are present, modify and commit
only owned paths, and return the known diff. Do not create per-leaf worktrees or worker branches.
When CM returns terminal, writer ownership returns to EM.

Use `hmasd-general-leaf` for weakly coupled chores: fixture generation, formatting, file conversion, dependency download, mechanical inventory, isolated documentation cleanup, or a bounded orthogonal check. Give exact inputs, owned paths, allowed Effects, output shape, and stop condition. CM remains responsible for reviewing and integrating the result.

## Specialist leaves

- Reviewer is mandatory for shared-core or scientific/numerical/RNG/checkpoint/bit-identity/external-Effect semantic change; optional for ordinary direction-local code.
- Verifier is exceptional and answers one independent runtime/equivalence question that CM tests and review cannot answer sufficiently.
- Experiment Operator receives one exact frozen result-bearing argv/cwd/output/stop condition and runs it once.
- External engineering transport performs one explicitly authorized send-once consultation.

## Milestone and return

Use `SCOPE_FROZEN`, `CANDIDATE_READY`, `REVIEW_RESOLVED`, and `RUN_OR_HANDOFF_READY`. Update state only when context loss would repeat costly work or change a material judgment; individual tests, leaf returns, and tool success are not milestones.

Preserve unrelated edits. Do not silently change scientific, numerical, RNG, checkpoint,
bit-identity, or Effect semantics. Return `[RESULT]` directly to the `Return task` that issued the
current WORK; normally this is the direction EM. Operator terminal facts always return to CM first.
Return direct observation, exact commands/tests, artifacts, limitations, and technical failure facts;
never convert test success into scientific acceptance. A negative scientific observation is still a
completed WORK when the frozen engineering contract was satisfied.
For user-direct input, answer the user in the current task without inventing a return ID.
