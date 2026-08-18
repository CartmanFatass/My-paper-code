# Stage 4 Capability Baseline

```text
document_kind=capability_baseline
owner=operational_root
date=2026-08-18
stage_3_synthetic_commit=eec138ea
observer_schema_version=3
codex_binary=C:\Users\fires\AppData\Roaming\npm\codex.cmd
codex_version=codex-cli 0.147.0
phase_1_live_acceptance=absent
stage_3_live_acceptance=absent
stage_4_live_acceptance=absent
user_authorized_synthetic_only=true
```

## User-authorized exception

Stage 4 may not start until Stage 3 live identity canaries are accepted.
The user overrode that gate, and the Phase 1 live gate, for **synthetic
implementation only**. This file is not Stage 4 acceptance.

## Local idle/loaded decision

See `PROTOCOL_EVIDENCE.md`. Automatic wake is implemented against the
fake App Server and local schema. Live wake remains forbidden until
Codex quota is restored and the deferred live tasks close.

## Synthetic capabilities present

```text
supervisor schema version 3
Root↔Portfolio mailbox ACL
durable mailbox store
semantic signal scanner
per-binding scheduler leases
idle-thread wake batch + one-shot turn/start
active-turn queue (no turn/steer)
uncertain-submission no-resend
MAILBOX_ACK / MAILBOX_INTAKE / MANAGED_PACKET_SEND
restart recovery of PREPARED batches
mailbox / wake / binding timelines
mailbox and scheduler CLI (scan-only without live session)
```

## Absent / deferred

```text
live Root↔Portfolio mailbox canary
live identity canaries
Phase 1 live observer canary
STAGE_3_ACCEPTANCE.md
STAGE_4_ACCEPTANCE.md
STAGE_3_LIVE_CANARY_REPORT.md
STAGE_4_LIVE_CANARY_REPORT.md
LIVE_CANARY_REPORT.md
PHASE_1_ACCEPTANCE.md
embedded EM/CM automatic delivery
automatic approval
write-capability roles
```
