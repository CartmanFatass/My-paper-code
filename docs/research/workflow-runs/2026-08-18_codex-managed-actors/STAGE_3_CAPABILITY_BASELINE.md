# Stage 3 Capability Baseline

```text
stage_3_baseline_commit=136d2904
observer_schema_version=1
codex_binary=C:\Users\fires\AppData\Roaming\npm\codex.cmd
codex_version=codex-cli 0.147.0
schema_root=%LOCALAPPDATA%\HMASD\codex-supervisor\schema\codex-cli_0.147.0
phase_1_live_acceptance=absent
phase_1_review=absent
user_authorized_synthetic_only=true
live_identity_canaries=deferred_until_quota_restore
```

## Predecessor

Pushed observer foundation: `136d2904`.

Doctor on 2026-08-18:

```text
status=OK
observer_only=true
automatic_turn_start_enabled=false
managed_actor_binding_enabled=false
observer_schema_version=1
```

Synthetic observer + Stage 3 tests: 107 passed.

Synthetic Stage 3 implemented without live App Server:

```text
S3-2 semantic bridge
S3-3 binding store / identity
S3-4 memory-off operator confirmation
S3-5 fresh thread provisioning against fake server
S3-6 managed context injection
S3-7 explicit managed turns
S3-8 command envelope parser (Stage 3 actions only)
S3-9 thread-derived command gateway
S3-10 verify/activate runtime
S3-11 legacy thread adoption
S3-12 managed CLI / doctor / PowerShell wrappers
```

Missing, not invented:

```text
LIVE_CANARY_REPORT.md
PHASE_1_ACCEPTANCE.md
```

## User-authorized exception

The Stage 3 plan requires Phase 1 live acceptance before any Stage 3 code.
The user deferred Tasks 15 and 16 until Codex quota returns, and authorized
continuing the managed-actor plan as **synthetic implementation only**.

Stage 3 live Root/Portfolio identity canaries remain forbidden until that
quota restore and Task 15/16 close.

## Protocol fallbacks

See `PROTOCOL_EVIDENCE.md`.

```text
clientUserMessageId          local-schema only; may be sent on turn/start
thread/memoryMode/set        unsupported on this host
memory-off API               unsupported; operator confirmation required
```
