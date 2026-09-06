# `OUTSOURCE_TASK v1` canonical prompt

For an initial task, create one native `gpt-5.6-terra` / `high` subagent and pass
this as its initial message. For a same-task follow-up, reuse the agent handle in
the prior dispatch receipt. Replace every `<...>` value. Do not remove a field; use
`NONE` only when the contract explicitly has no value.

```text
OUTSOURCE_TASK v1
REQUEST_ID=<unique opaque request id>
TASK_IDENTITY=<stable task identity; normally the same value as REQUEST_ID>
SOURCE_THREAD_ID=<source thread id or UNKNOWN>
DISPATCH_MODE=INITIAL|FOLLOW_UP_REUSE|REPLACEMENT
TARGET_AGENT=<FRESH_NATIVE_TERRA_HIGH for INITIAL/REPLACEMENT, or original returned agent handle for FOLLOW_UP_REUSE>
ORIGINAL_AGENT_HANDLE=<NONE for INITIAL, otherwise original returned agent handle when known>
REPLACEMENT_REASON=<NONE unless DISPATCH_MODE=REPLACEMENT; concrete unrecoverable/unavailable reason>
EXECUTION_OWNER=TARGET_AGENT (the assigned agent executes, verifies, and returns this task)
OBJECTIVE=<one observable outcome; one sentence>
CONTEXT=<facts needed to act; cite exact files/commits when available>
REPOSITORY=<absolute repository/worktree path>
BASELINE=<branch or commit to inspect>
GIT_DESTINATION=<worktree/branch/remote target, or NONE when no commit/push is allowed>
OWNED_PATHS=<exact files/directories the fresh agent may change>
ALLOWED_EFFECTS=<read/edit/test/commit/push; list each explicitly>
FORBIDDEN_EFFECTS=<unlisted paths, extra roles/skills/subagents, experiments, external sends, scientific or permission changes>
SCOPE=<none, or each docs/project/ENGINEERING_SCOPE_SPEC.md section 4 item this contract authorizes and why>
DELIVERABLES=<files or reports that must exist when done>
ACCEPTANCE_CRITERIA
1. <mechanical condition with expected value>
2. <mechanical condition with expected value>
3. <mechanical condition with expected value>
VERIFICATION_COMMANDS
- <exact command> -> <expected exit/status/output>
STOP_AND_REPORT_IF=<essential unresolved input/authorization, protected-semantic or scope conflict, unrecoverable in-scope verification failure, or uncertain external effect>
AMA_POLICY=Recover facts from context first; resolve routine choices locally. Ask one focused question only for an essential unresolved fact, and continue independent authorized work.
RETURN=OUTSOURCE_RESULT v1 with status, summary, changed_paths, deliverables, verification_results, acceptance_matrix, assumptions, blockers, and git_facts.

Execution rules:
- Execute only this objective and only within OWNED_PATHS and ALLOWED_EFFECTS.
- The assigned agent is the execution owner; complete implementation and verification here and return `OUTSOURCE_RESULT v1`.
- A `FOLLOW_UP_REUSE` message continues the same bounded task on its original agent. Do not delegate the same task recursively, create a user-visible task, or leave an advice-only plan when execution is requested.
- Do not spawn agents, create skills/roles, run experiments, alter scientific meaning, or send another message unless explicitly listed above.
- Do not commit or push unless ALLOWED_EFFECTS says so.
- Repair ordinary in-scope verification failures and complete required checks. Repeat or broaden checks only for a new change, failure or unresolved concern.
- On a stop condition, pause the affected action, preserve its state and report the exact gap; continue independent authorized work. Never retry an uncertain external effect without authoritative reconciliation.
```

## Dispatch receipt

The caller records:

```text
OUTSOURCE_DISPATCH v1
request_id=<same id>
task_identity=<same stable task identity>
dispatch_mode=INITIAL|FOLLOW_UP_REUSE|REPLACEMENT
target_agent=<returned or reused native agent handle>
original_agent_handle=<NONE for INITIAL, otherwise original handle when known>
model=gpt-5.6-terra
reasoning_effort=high
replacement_reason=<NONE unless replacement; concrete recovery/unavailability reason>
send_state=DISPATCHED|WAITING|COMPLETED|BLOCKED_INPUT|DISPATCH_UNCERTAIN|REJECTED_SCOPE
```

The receipt is provenance, not evidence that the work passed acceptance.
