# `OUTSOURCE_TASK v1` canonical prompt

Send this as one exact user message to the target Codex task. Replace every `<...>` value. Do not
remove a field; use `NONE` only when the contract explicitly has no value.

```text
OUTSOURCE_TASK v1
REQUEST_ID=<unique opaque request id>
SOURCE_THREAD_ID=<source thread id or UNKNOWN>
TARGET_THREAD_ID=<exact target thread id>
EXECUTION_OWNER=TARGET_THREAD_ID (the destination executes, verifies, and returns this task)
OBJECTIVE=<one observable outcome; one sentence>
CONTEXT=<facts needed to act; cite exact files/commits when available>
REPOSITORY=<absolute repository/worktree path>
BASELINE=<branch or commit to inspect>
GIT_DESTINATION=<worktree/branch/remote target, or NONE when no commit/push is allowed>
OWNED_PATHS=<exact files/directories the destination may change>
ALLOWED_EFFECTS=<read/edit/test/commit/push; list each explicitly>
FORBIDDEN_EFFECTS=<unlisted paths, extra roles/skills/subagents, experiments, external sends, scientific or permission changes>
DELIVERABLES=<files or reports that must exist when done>
ACCEPTANCE_CRITERIA
1. <mechanical condition with expected value>
2. <mechanical condition with expected value>
3. <mechanical condition with expected value>
VERIFICATION_COMMANDS
- <exact command> -> <expected exit/status/output>
STOP_AND_REPORT_IF=<missing input, scope expansion, permission ambiguity, failed verification, or uncertain external effect>
AMA_POLICY=Ask at most one blocking question; otherwise state an explicit assumption and continue.
RETURN=OUTSOURCE_RESULT v1 with status, summary, changed_paths, deliverables, verification_results, acceptance_matrix, assumptions, blockers, and git_facts.

Execution rules:
- Execute only this objective and only within OWNED_PATHS and ALLOWED_EFFECTS.
- The destination task is the execution owner; complete implementation and verification here and
  return `OUTSOURCE_RESULT v1`. Do not delegate the same task recursively or leave an advice-only
  plan when execution is requested.
- Do not spawn subagents, create skills/roles, run experiments, alter scientific meaning, or send another message unless explicitly listed above.
- Do not commit or push unless ALLOWED_EFFECTS says so.
- On any stop condition, make no further mutation and return the exact gap.
```

## Dispatch receipt

The caller records:

```text
OUTSOURCE_DISPATCH v1
request_id=<same id>
target_thread_id=<same target id>
send_state=DISPATCHED|WAITING|COMPLETED|BLOCKED_INPUT|DISPATCH_UNCERTAIN|REJECTED_SCOPE
prompt_sha256=<hash if available>
```

The receipt is provenance, not evidence that the work passed acceptance.
