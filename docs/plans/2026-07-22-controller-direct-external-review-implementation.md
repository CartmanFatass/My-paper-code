# Controller-Direct External Review Implementation Plan

## Goal

Replace persistent Exchange transport with Controller-direct external-Pro
transport while preserving Project Manager semantic ownership and exact raw
evidence.

## RED

1. Record baseline pressure failures for lost browser custody, incomplete Pro
   content and late callbacks after cancellation.
2. Change the workflow contract tests to require exactly three persistent
   roles, Controller-direct review transport, idempotent fence handling,
   Controller-owned heartbeat cleanup and rejection of retired callbacks.
3. Run the focused tests and verify they fail against the current topology.

## GREEN

1. Update `AGENTS.md`, `$hmasd-dispatch-task`, the role registry and route
   resolver to remove `open_divergent_exchange`.
2. Update `$hmasd-review-round` and its agent prompt with the direct transport
   state machine, bounded recovery, exact archival and PM return boundary.
3. Move the heartbeat renderer into `$hmasd-review-round` and delete the
   `$hmasd-review-exchange` Skill directory.
4. Update `REVIEWER_CONVERSATIONS.json`, `CURRENT_WORK.md` and
   `AGENT_CONTEXT.md` to record the new ownership topology.
5. Run all focused workflow tests and `git diff --check`.

## REFACTOR AND PRESSURE VERIFICATION

Re-run fresh pressure scenarios with the new Skill and close any loophole that
permits duplicate submission, Controller semantic rewriting, premature
`BLOCKED`, a second heartbeat, or authority from a late Exchange callback.
Obtain an independent read-only diff review before integration.

## Integration and takeover

Commit and push the workflow migration as one boundary. Then use the registered
conversation directly, inspect for the current focused G1 fence, resume it if
present, and submit only if the conversation proves it absent. No formal compute
or scientific iteration is authorized by this migration.
