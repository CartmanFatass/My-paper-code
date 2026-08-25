# Controller Transport Correction

After Stage 3 completed, the user identified a previously established runtime
contract that the tracked workflow had incorrectly reversed.

For an existing custom Luna Codex task, `send_message_to_thread` must carry the
target task's exact registered `model` and `thinking` together with `hostId`,
`threadId`, and `prompt`. Omitting those fields can replace the target task's
routing with the sender's model. Passing the exact target pair preserves rather
than overrides the task model.

The Open Exchange route in this retry used the stale omission rule. Its external
Pro response and archived raw remain review evidence, but retry3 does not by
itself prove Open Exchange model preservation. No corrective or duplicate Open
route will be sent. Live task metadata identifies the Exchange route as
`model=gpt-5.6-luna`, `thinking=high`, and the controller return route as
`model=gpt-5.6-sol`, `thinking=ultra`. The Convergent Exchange must use both
exact route pairs, and the final disposition must decide whether a fresh
transport-only round is required before algorithm research.

The correction is now centralized in `.agents/skills/hmasd-task-router/`.
Before a cross-task send it resolves both live routes from the local Codex task
database, blocks a registry mismatch, and requires the exact five-field send in
both directions. The external-review and experiment-monitor workflows both
depend on this Skill.

A new persistent monitor task was created as
`019f772b-355f-79f3-abbc-2f08800738f8`, with live route
`gpt-5.6-luna/medium`. A bidirectional transport self-test sent one controller
route to that task and received exactly one return message. Live metadata after
the exchange remained `gpt-5.6-sol/ultra` for the controller and
`gpt-5.6-luna/medium` for the monitor. This proves the shared routing primitive
without resubmitting either completed divergent review.
