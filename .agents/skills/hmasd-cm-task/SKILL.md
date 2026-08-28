---
name: hmasd-cm-task
description: Use when a top-level HMASD CM direction task receives a bounded implementation, test, integration, prepare, execution, or technical-repair slice.
---

# HMASD CM Task

Read `docs/project/WORKFLOW_PROTOCOL.md`, native WORK/CONTROL history, direction authority, and the
current engineering snapshot. CM owns direction implementation, focused tests, ordinary runtime
checks, engineering interpretation, milestone state, and Git closure. It does not make scientific
or Portfolio judgments.

For a nontrivial unfamiliar surface, use CM Scout unless the current milestone already contains a
trustworthy map. Implement directly in this main session; there is no Implementer leaf. Use General
leaf only for weakly coupled chores, Reviewer for the high-impact semantic boundaries defined by
the protocol, Verifier for one exceptional independent runtime question, and Operator for one exact
result-bearing command. Preserve unrelated work and the protocol's single-writer Git boundary.

CM's RESULT slice is exactly:

- `Engineering status: IN_PROGRESS | IMPLEMENTED | UNCHANGED | BLOCKED | NOT_REACHED`
- `Observation status: IN_PROGRESS | OBSERVED | NOT_OBSERVED | NOT_REQUIRED`
- `Verification status: IN_PROGRESS | SATISFIED | UNSATISFIED | NOT_RUN`
- `Commit: <sha or NONE>`

Apply the shared `Outcome:` semantics from the protocol without redefining them here. Test success
is engineering evidence, never scientific acceptance. Update the one milestone snapshot only when
context loss would repeat costly work or alter a material engineering judgment. Complete the
current interaction through the protocol-defined return transport or answer a user-direct request
here.
