# Quota-Blocked Live Work — Handoff

```text
document_kind=operational_handoff
owner=operational_root
date=2026-08-18
branch=aggressive
resume_when=codex_quota_restored
synthetic_stage3=done
synthetic_stage4=done
live_work=not_started
```

This is an operational Root resume packet. It is not scientific,
Portfolio, Phase 1 acceptance, Stage 3 acceptance, or Stage 4 acceptance.

Read first:

1. `AGENTS.md`
2. `.agents/roles/ROOT.md`
3. this file
4. `docs/research/workflow-runs/2026-08-18_codex-app-server-observer/PHASE_1_LIVE_AND_REVIEW_DEFERRED.md`
5. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md`
6. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_4_CAPABILITY_BASELINE.md`

Plans:

```text
C:\Users\fires\Downloads\2026-08-18-hmasd-codex-app-server-observer-phase-1.md
C:\Users\fires\Downloads\2026-08-18-hmasd-trusted-managed-actors-and-mailbox.md
```

## Why live work is blocked

Codex usage/quota is exhausted. Every remaining live task needs at least
one real `turn/start` that consumes generation quota and returns an exact
mechanical reply. Synthetic fake-server tests cannot substitute.

Do **not** invent:

```text
LIVE_CANARY_REPORT.md
PHASE_1_ACCEPTANCE.md
STAGE_3_LIVE_CANARY_REPORT.md
STAGE_3_ACCEPTANCE.md
STAGE_4_LIVE_CANARY_REPORT.md
STAGE_4_ACCEPTANCE.md
```

## Blocked tasks, in resume order

When the user says quota is restored, do these in order. Do not skip
ahead to a later live canary.

| Order | Task | What it needs | Output that may then be written |
|---|---|---|---|
| 1 | Observer Task 15 | live ephemeral `turn/start`; exact `HMASD_APP_SERVER_OBSERVER_OK`; unexpected server requests terminate | `LIVE_CANARY_REPORT.md` |
| 2 | Observer Task 16 | independent review of that live evidence | `PHASE_1_ACCEPTANCE.md` only if no Critical/High remains |
| 3 | S3-13 | live Operational Root and Portfolio identity canaries on fresh managed threads; spoof rejected; no automatic turns | `STAGE_3_LIVE_CANARY_REPORT.md` |
| 4 | S3-14 | review of Stage 3 live evidence | `STAGE_3_ACCEPTANCE.md` only if no Critical/High remains |
| 5 | S4-16 | live Root↔Portfolio mailbox/wake canary; one wake per idle target; no `turn/steer`; no blind retry | `STAGE_4_LIVE_CANARY_REPORT.md` |
| 6 | S4-17 | review of Stage 4 live evidence | `STAGE_4_ACCEPTANCE.md` only if no Critical/High remains |

Observer Task 15 baseline commit recorded earlier: `136d2904`. Later
supervisor-compatible commits on `aggressive` may be used if the
observer protocol is unchanged.

## What is already implemented (synthetic only)

Pushed Stage 3 synthetic through S3-12, then Stage 4 synthetic through
S4-15:

```text
observer JSONL-lite client and schema capture
supervisor schema v2 bindings / manual turns / command gateway
supervisor schema v3 mailbox / leases / wake batches
Root↔Portfolio ACL
semantic ledger scanner (no semantic mutation)
wake scheduler (fake server): one batch, one turn/start, no retry
MAILBOX_ACK / MAILBOX_INTAKE / MANAGED_PACKET_SEND
CLI: managed *, mailbox *, scheduler once/status, wake show
PowerShell wrappers under scripts/codex-managed-actor-* and scripts/codex-mailbox-*
```

Still operator-only / scan-only without a live session:

```text
managed create / adopt / verify / turn
scheduler serve
live scheduler once wake submit
```

`scheduler once` currently scans and enqueues only. It does not open a
live App Server process.

## Hard fences that remain

```text
no live canary until the user confirms quota restore
no invented acceptance files
no automatic mutating retry
no turn/steer
no model-supplied identity
no Memory API on this host; operator confirmation only
-32001 retry only for thread/list and thread/read
unexpected server requests terminate
runtime DB stays under %LOCALAPPDATA%\HMASD\codex-supervisor
do not commit the unrelated dirty research/ha_ctse/hmasd/envs tree
project Python = C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
pytest --basetemp must stay inside the repo
```

## Suggested first commands after quota restore

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor -q `
  --basetemp=C:/Projects/HMASD/.tmp_quota_resume

& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_supervisor `
  --repo-root C:\Projects\HMASD `
  doctor
```

Then execute Observer Task 15 from the Phase 1 plan, using official
`openaiDeveloperDocs` and the local 0.147.0 schema. Do not start a
managed-actor or mailbox live canary until Task 15/16 have closed,
unless the user again explicitly overrides that order.
