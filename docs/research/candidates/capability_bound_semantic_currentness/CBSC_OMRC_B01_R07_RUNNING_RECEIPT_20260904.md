# CBSC-OMRC-B01 r07 running receipt — 2026-09-04

The original `CBSC-OMRC-B1-THREE-SEED-SCOUT` is running as one fresh detached attempt.
This receipt records execution of the object-tier selection in
`CBSC_OMRC_B01_R07_RESUME_INTAKE_20260904.md`; it creates no new scientific decision.
The evidence class remains **B/EXPLORE**, with no complete scientific result or assigned polarity.

Later terminal update: the task exited 6 at `2026-09-04T21:41:56Z`. The observed first-slot
training files are not a complete B1. See `CBSC_OMRC_B01_R07_TELEMETRY_INCIDENT_INTAKE_20260904.md`
for collected evidence, the controlled reproduction and its limits, quarantine and bounded repair.
The timestamped running observations below remain unchanged historical records.

## Accepted invocation

| Field | Recorded value |
| --- | --- |
| Task | `cbsc-b1-r07-b230e476ec-01` |
| Exact launch SHA | `b230e476ec72ca6ac93f9fe3f78bfe5d1d2852c2` |
| Pushed source branch | `origin/codex/dm-cbsc-resume-20260904` |
| Execution node / SSH | `wsl_4070` / `hmasd-wsl-node` |
| Detached checkout | `/home/wu/hmasd-worktrees/cbsc-b1-r07-b230e476ec-01` |
| Supervisor root | `/home/wu/.agent-tasks/cbsc-b1-r07-b230e476ec-01` |
| Supervisor start | `2026-09-04T21:40:26Z`, Unix `1788558026` |
| Supervisor native timestamp | `2026-09-05T05:40:26+08:00` (same instant) |
| Interpreter | `/home/wu/.venvs/hmasd/bin/python` |
| Final root, relative to checkout | `temp/directions/capability_bound_semantic_currentness/exp/b1_scout_r07` |
| Active staging root | `temp/directions/capability_bound_semantic_currentness/exp/.b1_scout_r07.partial-7706c57b48464ae2b2ac6a39769cca2b` |
| Publication entrypoints | final-root `summary.json` and `manifest.json` |
| Source conformance digest | `c3b305f88e4012366fbc13e074af503dd0164a72fdaa0395bbb0d650778c89cf` |

The supervisor's stored `runner.sh` contains this exact result command:

```bash
/usr/bin/env -C /home/wu/hmasd-worktrees/cbsc-b1-r07-b230e476ec-01 /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/capability_bound_semantic_currentness/control/r07-launch-admission.json && /usr/bin/env -C /home/wu/hmasd-worktrees/cbsc-b1-r07-b230e476ec-01 /home/wu/.venvs/hmasd/bin/python scripts/run_cbsc_omrc_b01_b1.py start --output temp/directions/capability_bound_semantic_currentness/exp/b1_scout_r07 --implementation-commit b230e476ec72ca6ac93f9fe3f78bfe5d1d2852c2 --b0-root temp/directions/capability_bound_semantic_currentness/exp/cbsc_omrc_b0_instrument_888bd9f50_r02
```

## What was checked

CM directly checked the old prospective task `cbsc-b1-r07-be2cc5ad6-01` and the new task name,
both `not_found` before launch, with no r07 root or live CBSC worker. It then accepted the new
task exactly once. The already pushed source was fetched through the configured remote network
shell; no bundle, uncommitted source copy, local fallback or source edit was needed. The remote
detached checkout includes the committed CBSC authority documents.

CM's source comparison found no production, runner, preflight or test change against the accepted
interpreter repair at `5a1b1b7feae9f67063ba0a5dd1d66085684a0d4b`. The previous independent PASS,
remote `17 passed` and full publication-path coverage remain the engineering support. No suite
was repeated. Exact-launch read-only readiness returned `B1_FORMAL_READY`,
`COMMIT_CONFORMANT`, `start_authorized=true`, no blockers, and the conformance digest above.

The fixed B0 manifest/inventory matched the resume intake: 33 files, 12,807,274 bytes,
manifest `c7c6f73be17e785cbe6ffaba6cfd30c4c8483ecf23e43bbd48df535c676bc298`, inventory
`184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5`.
Its manifest is inside the new checkout at
`temp/directions/capability_bound_semantic_currentness/exp/cbsc_omrc_b0_instrument_888bd9f50_r02/manifest.json`.
The three fixed archived responses were already staged under
`/home/wu/hmasd-inputs/cbsc-defect8-profile-20260904/archive`; their digests matched the bound
`.01/.02/.03` responses. Readiness inspected locator and raw-byte identity, not outcome values.

I inspected the captured admission, readiness, stored supervisor command, start time and status
snapshot bytes returned by CM. The outer admission was captured at
`2026-09-04T21:40:26.759658Z` and assessed at `2026-09-04T21:40:26.759961Z`, from
`/proc/meminfo`. Physical and effective available memory were each **13,225,099,264 bytes**,
above the **4,294,967,296-byte** floor. Both floor flags and `passed` are true; failure reasons
are empty. This receipt admits only this invocation, not a future launch or node.

## Last observation and bounded reading

At **2026-09-04T21:41:30Z**, the supervisor reported `running`, null exit code, active tmux,
wrapper PID `74925`, runner PID `74930`, and 64 seconds elapsed. The first
`STRUCT-CURRENTNESS-GRU / seed 21101` worker, PID `75194`, was in slice `24:48` using the
configured virtual-environment interpreter. Checkpoint filenames `0/12/24` and result filenames
for slices `0:12` and `12:24` existed. CM read filenames and process facts only, not learning
values. Their existence is progress evidence, not yet a validated complete arm-seed or B1 result.

Earlier RSS snapshots were 580,832 KiB for the first worker and 354,920 KiB for the runner.
These are instantaneous snapshots, not peaks or a full resource-conformance conclusion.
The exposure, 12 arm-seeds, FP32 CPU semantics, paired RNG, seeds, 48 updates/768 Adam steps per
slot, four checkpoints and 7,200-second invocation cap remain exactly as in the resume intake.
The 333.2708638-second per-slot cost envelope implies roughly 66.7 minutes for 12 slots; that is
a planning projection from prior engineering telemetry, not a task-wide deadline or new stop rule.

No complete result, RAW-competence adjudication, scientific branch, return contrast, MEI reading
or headroom update exists at this boundary. r06 remains quarantined historical engineering evidence.
A and B objects have no consumption state. Technical passage beyond the previous import failure
does not establish currentness value; the competent same-information RAW comparison remains the
next scientific discriminator. Missing resource telemetry alone would remain
`resources_unmeasured`; a new learner/integrity failure must be reproduced over the recorded
bytes before classification and any repair selection.

## Recovery and ownership

Read-only status and log commands:

```powershell
ssh hmasd-wsl-node '/usr/local/bin/agent-task status cbsc-b1-r07-b230e476ec-01'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs cbsc-b1-r07-b230e476ec-01 40'
```

Root requested the shared tracker `/root/tracker_lxh_experiments` to take routine observation.
The handoff names this exact task/node/SHA, both output roots, admission, cost projection and
callback `/root/dm_amx_cbsc_resume`. CM has returned at the running boundary and performs no
routine polling. On terminal status, CM collects and technically checks the same result; DM
performs the scientific intake, checks all declared counts and receipts and writes the owner brief
if the result is valid. A failure is not restarted automatically. No second r07, r06 resume,
local fallback, new seed, B2, Pro round or additional automation is authorized by this receipt.
Root maintains its existing resume schedule and owns Portfolio integration.

Captured local runtime records are under the DM worktree at
`temp/directions/capability_bound_semantic_currentness/exp/r07_launch_handoff/`:
`r07-launch-admission.json`, `r07-readiness.json`, `runner.sh`, `start_time` and
`status-snapshot.json`. They are copied unchanged from CM's capture directory. The remote
supervisor, exact command, source SHA and locators above make the running state recoverable
without relying on either agent's process. This change adds documentation only, `scope: none`.

Owner reviews returned `[]` at selection and again at this clean boundary, including in Root's
integration checkout. No CBSC owner override was present. The sole selection is recorded by
`docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-012.json`, with its exact shared-ledger
row in the resume intake for Root integration. `DIRECTION.md` is unchanged because no new
mechanism-level science has been accepted.
