# Codex Supervisor Durability Kernel V1

This is the durable-transition contract for the Codex App Server supervisor.
It replaces module-local state mutation rules after cutover.

## Guarantee

The kernel does **not** provide distributed exactly-once execution. SQLite
and App Server stdin do not share a transaction. The accepted contract is:

```text
at-most-one automatic submission attempt
+
durable possible-submission state
+
stable idempotency key
+
evidence-based reconciliation
+
idempotent downstream application
```

## Effect states

```text
PREPARED
= no write claim exists; automatic cancellation is safe.

WRITE_STARTED or later
= submission may have occurred; automatic resend is forbidden.
```

`PREPARED` is the only automatically cancelable effect state. An effect in
`WRITE_STARTED` or later is never automatically submitted again.

`SUBMITTING` on a managed turn or wake batch means only:

```text
the linked App Server effect reached WRITE_STARTED
```

A newly prepared turn or wake batch is `PREPARED`, never `SUBMITTING`.
There is no domain-only wake claim API. `SUBMITTING` is recorded only together
with effect `WRITE_STARTED` through `submit_effect`. The write-start
transaction must commit before `send_prepared()`. Stored resume evidence
compares `raw_message_seq` values only, never normalized `event_seq` against
raw sequences.

Completion of an `ACTIVE` wake accepts a linked effect that is
`EFFECT_CONFIRMED`, or `OPERATOR_RESOLVED` with disposition
`TURN_OBSERVED_ACTIVE` / `TURN_OBSERVED_COMPLETED`.

## Single writers

There is one transition kernel (`TransitionKernel`). After cutover, these
columns may be modified only through that kernel:

```text
managed_actor_bindings.binding_state
managed_turn_intents.submission_state
wake_batches.state
mailbox_messages.delivery_state
mailbox_messages.intake_state
managed_actor_commands.validation_state
app_server_effects.state
```

There is one process-lifetime session owner. Mutating App Server requests
may be sent only through:

```text
AppServerSessionOwner.submit_effect(effect_id)
```

Business modules may request transitions. They may not write protected state
columns or call mutating `AppServerClient.request()` after cutover.

## Incidents and operator resolution

`INCIDENT` is terminal except through one explicit operator-resolution
transaction. Operator resolution is one-shot and evidence-bound. A second
resolution for the same aggregate is rejected. No branch automatically
resends an unknown mutation.

## Identity and authority

```text
threadId → binding_id → actor_context_id
```

is the only managed runtime identity. Operational Root and Portfolio remain
the only managed actor kinds. Model text may not supply identity, source,
or operator fields. Raw prose never becomes a state name, routing key, ACL
input, retry decision, or operator-resolution fact.

App Server mechanical status never creates scientific, technical, workflow,
direction, or Portfolio disposition.

## Non-goals

This kernel does not add:

```text
OpenAI Agents SDK
Codex SDK
another agent loop or conversation-memory layer
a durable workflow product
Stage 5 task DAG, write roles, approval routing, or automatic work retry
live App Server acceptance
```

Live Phase 1 / Stage 3 / Stage 4 acceptance remains a later gate. Missing
live artifacts are not code defects.

## Schema

Observer schema version 7 is additive. Existing `mutation_intents` rows
remain queryable. After cutover they are legacy evidence only.

State graphs live in `tools/codex_supervisor/durability/graphs.py`. A
transition not listed there is illegal.
