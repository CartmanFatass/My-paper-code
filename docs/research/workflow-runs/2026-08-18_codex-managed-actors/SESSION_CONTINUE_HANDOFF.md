# Continue: Codex Supervisor Control Plane

```text
document_kind=operational_session_handoff
owner=operational_root
date=2026-08-18
branch=aggressive
head=c1e2d2e260e1b4765a2f35e4f64309f7bd0e1fe9
pushed=origin/aggressive
synthetic_observer=done
synthetic_stage3=done
synthetic_stage4=done
live_work=deferred_until_quota_restore
```

This is an operational Root resume packet. It is not scientific,
Portfolio, Phase 1 acceptance, Stage 3 acceptance, or Stage 4 acceptance.

Do not resume from chat transcripts. Reconstruct from this file, the
named plans, and the Git history on `aggressive`.

## Read first

1. `AGENTS.md`
2. `.agents/roles/ROOT.md`
3. this file
4. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/QUOTA_BLOCKED_HANDOFF.md`
5. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md`
6. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md`
7. `docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_4_CAPABILITY_BASELINE.md`
8. `docs/research/workflow-runs/2026-08-18_codex-app-server-observer/PHASE_1_LIVE_AND_REVIEW_DEFERRED.md`

Plans (local Downloads, not in the repo):

```text
C:\Users\fires\Downloads\2026-08-18-hmasd-codex-app-server-observer-phase-1.md
C:\Users\fires\Downloads\2026-08-18-hmasd-trusted-managed-actors-and-mailbox.md
```

Project Python:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
```

## What is already on origin/aggressive

| Commit | What it is |
|---|---|
| `136d2904` | Phase 1 observer foundation (JSONL-lite, schema capture, doctor, fake-server tests) |
| `c249fa40` | Defer live Tasks 15/16; start Stage 3 schema v2 |
| `1ba2d702` | Semantic bridge, bindings, provisioning |
| `eec138ea` | Manual turns, command gateway, activation, managed CLI |
| `c1e2d2e2` | Stage 4 synthetic mailbox, ACL, scanner, wake scheduler, recovery, CLI |

Latest control-plane HEAD: `c1e2d2e2`.

Unrelated dirty files (`docs/research/candidates`, `ha_ctse_process`,
`hmasd`, `envs`, experiment trees, `.tmp_*`) were **not** staged, committed,
or pushed by this control-plane work. Leave them alone.

## What is implemented (synthetic only)

```text
observer JSONL-lite client; no outbound "jsonrpc"
initialize then initialized
unexpected server requests terminate
-32001 retry only for thread/list and thread/read
no automatic mutating retry
threadId → binding_id → actor_context_id
operator Memory confirmation (no thread/memoryMode/set on 0.147.0)
Stage 3 actions: NO_CONTROL_ACTION, CONTEXT_REANCHOR_ACK
schema v3 mailbox + leases + wake batches
Root↔Portfolio ACL; EM/CM/Leaf not auto-delivered
semantic scan writes only supervisor mailbox
idle wake: one batch, one turn/start, clientUserMessageId = hmasd-wake:<id>
active turn: queue; never turn/steer
uncertain submission: mark, do not resend
MAILBOX_ACK / MAILBOX_INTAKE / MANAGED_PACKET_SEND
CLI mailbox list/show/send-operator/dead-letter
CLI scheduler once = scan only (no live App Server)
runtime DB: %LOCALAPPDATA%\HMASD\codex-supervisor
```

Tests last run on this slice:

```text
tests/codex_supervisor  127 passed
--basetemp=C:/Projects/HMASD/.tmp_stage4_s4b
```

## What is not done

Do not invent these files:

```text
LIVE_CANARY_REPORT.md
PHASE_1_ACCEPTANCE.md
STAGE_3_LIVE_CANARY_REPORT.md
STAGE_3_ACCEPTANCE.md
STAGE_4_LIVE_CANARY_REPORT.md
STAGE_4_ACCEPTANCE.md
```

Still require a live Codex session / quota:

```text
Observer Task 15  live ephemeral turn/start canary
Observer Task 16  review of that live evidence
S3-13             live Root/Portfolio identity canaries
S3-14             Stage 3 acceptance
S4-16             live mailbox/wake canary
S4-17             Stage 4 acceptance
managed create / adopt / verify / turn against a real App Server
scheduler serve / live scheduler once wake submit
```

## What the next session should do

If the user asked another model to review: give them
`SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md` and the commit range
`136d2904^..c1e2d2e2` on `origin/aggressive`. Review is advisory. It
does not accept Phase 1 / Stage 3 / Stage 4 and does not authorize live
canaries.

If the user says Codex quota is restored: follow
`QUOTA_BLOCKED_HANDOFF.md` in order. Do not skip to a later live canary.

If the user says continue synthetic work: there is no remaining Stage 4
synthetic task from the plan except review findings. Do not start Stage 5.

If review returns Critical/High on the synthetic code: fix only the named
supervisor/test/doc files; do not touch the dirty research tree; do not
write acceptance files.

## Hard fences

```text
no live turn/start until the user confirms quota restore
no invented acceptance or live-canary reports
no Codex SDK / Agents SDK
no outbound JSON-RPC "jsonrpc" field
no model-supplied identity or authority keys
no automatic Memory
no turn/steer
no mutating retry
no commit of unrelated dirty workspace
pytest --basetemp must stay inside the repo
```

## Superseded review pointer

```text
superseded_by=19a80529fa9b0ff7327d704cef92fe2fd065ae2e
prior_rereview=0520df87ee2dd1dd70c1bdade34889980c4c7a44
reviewed_range=0520df87ee2dd1dd70c1bdade34889980c4c7a44..19a80529fa9b0ff7327d704cef92fe2fd065ae2e
historical_head_in_this_file=c1e2d2e260e1b4765a2f35e4f64309f7bd0e1fe9
tests/codex_supervisor=167 passed
```

Do not rewrite the historical sections above. The 2026-08-18 synthetic
rereview of `0520df87` returned `REVISION_REQUIRED`. The corrective
commit is `19a80529`. Use
`SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md` for the next review, not
the pre-fix prompt pinned to `c1e2d2e2`.

```text
superseded_by=883eb028c3cbdadf99159869ea722e8a4a6a5f6d
prior_rereview=19a80529fa9b0ff7327d704cef92fe2fd065ae2e
reviewed_range=19a80529fa9b0ff7327d704cef92fe2fd065ae2e..883eb028c3cbdadf99159869ea722e8a4a6a5f6d
tests/codex_supervisor=177 passed
```

The later rereview of `19a80529` also returned `REVISION_REQUIRED`. The
corrective commit is `883eb028`. Use the current
`SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md` for that slice.

```text
superseded_by=f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
prior_rereview=883eb028c3cbdadf99159869ea722e8a4a6a5f6d
reviewed_range=883eb028c3cbdadf99159869ea722e8a4a6a5f6d..f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
tests/codex_supervisor=194 passed
```

The later rereview of `883eb028` also returned `REVISION_REQUIRED`. The
corrective commit is `f7a53045`. Use the current
`SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md` for that slice.

```text
superseded_by=868cb383ab087e63e6071be26d3d107118481f7c
prior_rereview=f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
reviewed_range=f7a5304560e52b2b78faadb6d6de4049a5b9a5f9..868cb383ab087e63e6071be26d3d107118481f7c
tests/codex_supervisor=201 passed
```

The later rereview of `f7a53045` also returned `REVISION_REQUIRED`. The
corrective commit is `868cb383`. Use the current
`SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md` for that slice.
