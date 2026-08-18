# Codex App Server Observer Policy

Phase 1 is an observer. It launches one dedicated `codex app-server` process,
records mechanical transport evidence, and never becomes project authority.

## Authority

- Observer events are mechanical evidence.
- Observer state is external and noncanonical.
- There is no actor binding in Phase 1.
- There is no automatic turn start.
- There is no automatic approval.
- There is no semantic transition.
- Raw logs may contain project text and remain local.

## Forbidden in Phase 1

The observer must not write scientific, technical, portfolio, epoch,
promotion, rollover, working-set, obligation, or checkpoint state. It must
not expose App Server mutations through `hmasd_orchestrator`. It must not
trust model-supplied `actor_context_id`, `source_kind`, role, or ownership.

## Runtime

Default state lives at `%LOCALAPPDATA%\HMASD\codex-supervisor`. Tests use
`tmp_path` and never write that directory. Repository configuration contains
no thread IDs, session IDs, credentials, or user-level Codex configuration.
