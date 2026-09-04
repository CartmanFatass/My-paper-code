# Singleton Transport task

Date: 2026-09-04

Provenance: `OWNER_DIRECT`

## Decision

HMASD uses one long-lived local Codex Transport task instead of creating one task
per Pro handoff. The active task is declared in `.codex/hmasd-transport.toml` and
runs with `gpt-5.6-luna` at `xhigh` reasoning effort.

Prompt Author renders `dispatch_mode=REUSE_SINGLETON` and sends exactly one
execution message per handoff to that configured task. It must not call
`create_thread` or create a replacement when the singleton is unavailable.

The singleton task ID is only the reusable Codex execution endpoint. Every
handoff retains its own `source_thread_id`, `parent_thread_id`, provider
conversation binding, tab, heartbeat, archive, receipt, and idempotency state.
The sole receipt destination remains the handoff-specific `parent_thread_id`.
Provider `conversation_binding_key` rules are unchanged.

The singleton remains unarchived after request cleanup. Transport tasks that were
already active when this decision was made may finish their current request and
are then retired; they are not reused.

## Reason

Creating a local Codex task presents a task-creation approval event even when the
saved HMASD project is configured for Full Access. Reusing one task removes that
repeated creation event without changing provider-conversation continuity or
receipt routing.
