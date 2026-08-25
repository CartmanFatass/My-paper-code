# Repository Context Lifecycle Remediation Acceptance

```text
phase_0_gate_commit=ad91385d6defbc6fb786ea5e75802b556c5d961e
phase_0_gate_status=PASSED
supersedes=ed3992ae82aeaf55801a528227344b879ca8724b
test_count=308 passed
doctor_schema=3
memory_authority=none
physical_deletion_enabled=false
active_PreToolUse=absent
```

This artifact records the control-plane safety closure required before
Codex App Server observer Phase 1 live activation. It is not scientific,
technical, or portfolio authority.

## Closed review findings

| Finding | Closure |
| --- | --- |
| Trusted mutation requester identity or mutation unavailability | MCP write tools have no `USER_AUTHORITY` default. Unbound MCP is mutation-read-only. Bound requester must be an ACTIVE registered actor and the object owner. P0 requires a typed `user_authority_grants` row. |
| Checkpoint compatibility | `current_checkpoint()` matches current open epoch, revision, `state_version`, and semantic commit. Compact/resume rematerializes when incompatible. |
| Promotion exact owner/scope/target/file/writer receipt | Requester equals owner; direction/scope and repository containment are checked; `canonical_ref` equals `target_ref`; existing file is required; writer receipt is recorded without file-hash gates. |
| Atomic rollover carry | `apply_rollover` is one SQLite transaction. New epoch inherits refs and owner-confirmed frontier. Carried promotions rebind. Injected failure rolls back. |
| Working-set retention exclusion | Audit-only marks remove refs from the active working set and capsule. |
| Released/closed/stale exclusion | Released actors have empty active sets. Closed-epoch commits are historical only. Stale checkpoints are not injected. |

## Doctor snapshot

```text
schema_version=3
memory_authority=none
compaction_summary_authority=none
physical_deletion_enabled=false
```

## ACTIVE hook surface

Live `.codex/config.toml` activates SessionStart, SubagentStart, SubagentStop,
and Stop. There is no unfiltered ACTIVE `PreToolUse` handler. Shadow
`PreToolUse` remains observational and is not ACTIVE.

## Remaining non-blocking limitations

Live Codex eight-canary compact/resume and live `enable -Mode Active` remain
operator-owned. They are not open Critical or High control-plane defects.
