# Supervisor Durability Kernel V1 Baseline

```text
document_kind=durability_kernel_baseline
recorded_at=2026-08-19
worktree=C:\Projects\HMASD-durability-kernel-v1
branch=codex-supervisor-durability-kernel-v1
tracks=origin/aggressive
```

## Exact HEAD

```text
durability_kernel_baseline_commit=04eb640f4090993b251b204096cff26b44350b90
durability_kernel_baseline_message=docs: pin supervisor rereview prompt to 3d6b87f2
code_commit=3d6b87f20863c7a593e0dbbd8e6a59b307edb265
code_commit_message=fix: close null-lease claim, wake incident, and canary leftovers
prompt_pin_commit=04eb640f4090993b251b204096cff26b44350b90
prompt_pin_behavior_change=false
observer_schema_version=6
live_acceptance=absent
```

Worktree status at freeze: clean (no local edits). Isolated from the dirty
main checkout at `C:\Projects\HMASD`.

## Comparison with `3d6b87f2`

```text
git diff --stat 3d6b87f20863c7a593e0dbbd8e6a59b307edb265..HEAD
```

```text
 .../SESSION_CONTINUE_HANDOFF.md                    |  11 +
 .../SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md     | 237 ++++++++++++---------
 2 files changed, 149 insertions(+), 99 deletions(-)
```

### Post-`3d6b87f2` commit table

| commit | files | behavioral / documentation | durability-kernel impact |
|---|---|---|---|
| `04eb640f` | `SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md`, `SESSION_CONTINUE_HANDOFF.md` | documentation only | none; pins the prior rereview target. No Stage 5, schema, or transport change. |

No unrelated Stage 5 work is present between `3d6b87f2` and this baseline.

Recent log:

```text
04eb640f docs: pin supervisor rereview prompt to 3d6b87f2
3d6b87f2 fix: close null-lease claim, wake incident, and canary leftovers
20509602 docs: pin supervisor rereview prompt to 868cb383
868cb383 fix: close uncertain-turn incident escape and atomic wake claim
a5cd3fa0 docs: pin supervisor rereview prompt to f7a53045
f7a53045 fix: sink incident terminality and close resume/session leftovers
d13760d8 docs: pin supervisor rereview prompt to 883eb028
883eb028 fix: make incident terminal and recover prepared siblings
```

## Exact test command

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_semantic_mvp `
  tests/codex_context_lifecycle `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-durability-kernel-v1/.tmp_baseline
```

Result recorded on this host:

```text
517 passed in 136.90s
exit_code=0
interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
```

Existing test failures at freeze: none.

## Known open findings

These are not hidden failures. They remain open after the last synthetic
rereview slice and are the reason this kernel exists.

1. Protected aggregate state is written by many business modules. There is no
   single transition kernel, version column, or transition journal.
2. Mutating App Server requests are sent through `ManagedAppServerSession.request`
   / `guard.request` / `ObserverService._session_request`, not a single
   `AppServerSessionOwner.submit_effect`. A second wrapper can still send a
   mutation.
3. `mutation_intents` remains the live mutation ledger. There is no
   `app_server_effects` journal and no `WRITE_STARTED` claim.
4. `SUBMITTING` is used as a domain sendable/claim state, not as “the linked
   effect reached `WRITE_STARTED`”.
5. Wake `INCIDENT` recovery is operator-only in the last slice, but resolution
   is not one-shot, not uniquely constrained, and not bound to an effect
   journal.
6. Live App Server / Phase 1 / Stage 3 / Stage 4 acceptance is absent and
   deferred. That absence is not a code defect.
7. Schema version is 6. Version columns, effect references, `control_transitions`,
   and `operator_resolutions` do not exist.

## Direct-write inventory

Exact command:

```powershell
git grep -n -E `
  "UPDATE (managed_actor_bindings|managed_turn_intents|wake_batches|mailbox_messages|managed_actor_commands|mutation_intents)" `
  -- tools/codex_supervisor
```

Exact results at `04eb640f`:

```text
tools/codex_supervisor/binding_store.py:237:                """UPDATE managed_actor_bindings
tools/codex_supervisor/binding_store.py:252:                    """UPDATE mutation_intents
tools/codex_supervisor/binding_store.py:270:                "UPDATE managed_actor_bindings SET binding_state = ? WHERE binding_id = ?",
tools/codex_supervisor/binding_store.py:287:                """UPDATE managed_actor_bindings
tools/codex_supervisor/binding_store.py:434:                """UPDATE managed_actor_bindings
tools/codex_supervisor/binding_store.py:471:                "UPDATE managed_actor_bindings SET binding_state = ?, suspended_at = ? WHERE binding_id = ?",
tools/codex_supervisor/binding_store.py:488:                "UPDATE managed_actor_bindings SET binding_state = ?, revoked_at = ? WHERE binding_id = ?",
tools/codex_supervisor/command_gateway.py:404:                f"UPDATE managed_actor_commands SET {assignments} WHERE command_id = ?",
tools/codex_supervisor/mailbox_store.py:192:                f"UPDATE mailbox_messages SET {', '.join(assignments)} WHERE message_id = ?",
tools/codex_supervisor/mailbox_store.py:227:                """UPDATE mailbox_messages
tools/codex_supervisor/mailbox_store.py:265:                """UPDATE wake_batches
tools/codex_supervisor/mailbox_store.py:290:                            """UPDATE mailbox_messages
tools/codex_supervisor/mailbox_store.py:297:                        """UPDATE mailbox_messages
tools/codex_supervisor/mailbox_store.py:331:                    """UPDATE mailbox_messages
tools/codex_supervisor/mailbox_store.py:351:                    """UPDATE mailbox_messages
tools/codex_supervisor/managed_turns.py:98:        sql = f"UPDATE managed_turn_intents SET {assignments} WHERE turn_intent_id = ?"
tools/codex_supervisor/managed_turns.py:116:                """UPDATE managed_turn_intents
tools/codex_supervisor/managed_turns.py:213:                    "UPDATE managed_actor_bindings SET last_turn_id = ? WHERE binding_id = ?",
tools/codex_supervisor/managed_turns.py:274:                """UPDATE managed_turn_intents
tools/codex_supervisor/mutation_intents.py:117:        sql = f"UPDATE mutation_intents SET {', '.join(assignments)} WHERE intent_id = ?"
tools/codex_supervisor/provisioning.py:70:                    "UPDATE managed_actor_bindings SET memory_policy_state = ? WHERE binding_id = ?",
tools/codex_supervisor/session_guard.py:79:    turn_sql = """UPDATE managed_turn_intents
tools/codex_supervisor/session_guard.py:83:    batch_sql = """UPDATE wake_batches
tools/codex_supervisor/session_guard.py:106:            """UPDATE mutation_intents
tools/codex_supervisor/wake_batches.py:210:                    """UPDATE wake_batches
tools/codex_supervisor/wake_batches.py:257:        sql = f"UPDATE wake_batches SET {assignments} WHERE wake_batch_id = ?"
```

Count: 26 matching `UPDATE` sites across 8 modules.

## Direct mutation-call inventory

Exact command from the plan:

```powershell
git grep -n -E `
  "client\.request\(\"(thread/start|thread/resume|thread/fork|turn/start|turn/steer|turn/interrupt|thread/compact/start|review/start)" `
  -- tools/codex_supervisor
```

Exact results: no matches.

That regex is empty because mutating calls currently go through wrappers, not
`client.request("thread/start", ...)`. Additional inventory at the same commit:

```text
tools/codex_supervisor/managed_turns.py:163:            response = await guard.request("turn/start", params)
tools/codex_supervisor/provisioning.py:65:                await self.client.request(MEMORY_MODE_METHOD, {"threadId": binding.thread_id, "mode": "disabled"})
tools/codex_supervisor/provisioning.py:104:            response = await guard.request("thread/start", params)
tools/codex_supervisor/provisioning.py:185:            await guard.request("thread/resume", {"threadId": thread_id})
tools/codex_supervisor/wake_recovery.py:118:            await guard.request("thread/resume", {"threadId": binding.thread_id})
tools/codex_supervisor/wake_scheduler.py:190:            response = await guard.request("turn/start", params)
tools/codex_supervisor/observer.py:220:            response = await self.client.request(method, params)
tools/codex_supervisor/observer.py:432:            start = await self._session_request("thread/start", ...)
tools/codex_supervisor/observer.py:449:            turn = await self._session_request("turn/start", ...)
tools/codex_supervisor/session_guard.py:175:        send = asyncio.create_task(self.client.request(method, params, timeout=timeout))
```

`MEMORY_MODE_METHOD` is a thread-scoped policy call, not one of the listed
mutating methods. `observer.py:220` is the generic `_session_request` wrapper
used for both reads (`thread/list`, `thread/read`) and canary mutations.

## Feature freeze

```text
No Stage 5 capability will be added before durability-kernel acceptance.
Live App Server remains deferred and is not a defect.
```

Frozen out of this milestone:

```text
task DAG
capability-based write roles
approval routing
automatic work retry
stalled-owner adjudication
Agents SDK
Codex SDK
durable workflow product
Codex Rust core changes
new managed actor kinds
automatic turn/steer
automatic approval
```

No behavior changed in this baseline task.
