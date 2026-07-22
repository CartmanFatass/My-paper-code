# OMP HMASD Task Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the persistent Research Project Manager and Experiment Monitor sessions plus the Codex code-agent surface with one native OMP Project Manager task tree and one rebuildable low-cost Monitor job, while retaining Open-Pro Exchange as the only persistent non-Controller session.

**Architecture:** Controller remains the workflow control plane and performs direct lightweight Pro-evidence intake. External Pro owns scientific direction; an isolated OMP Project Manager task owns in-scope algorithm realization and nested code-agent management. Formal runs are persistent named `hub` processes; a read-only Monitor task observes authoritative status and can be rebuilt from a run manifest after root OMP restart.

**Tech Stack:** OMP project agents and config, Markdown/YAML frontmatter, OMP `task`/`hub`, PowerShell workflow contract tests, JSON role and monitor contracts.

## Global Constraints

- External GPT-5.6 Pro owns scientific direction, conjectures, mechanism-family selection, estimands and scheduled research actions.
- OMP Project Manager owns core algorithm realization and code-side decisions inside the Pro direction and Controller-authorized resource boundary.
- Controller owns workflow design, routing, direct lightweight evidence intake, resource/formal-compute authorization, Git, evidence integrity and user communication; it does not redesign the Manager's in-scope algorithm.
- There is no independent Research Intake agent.
- Only Open-Pro Exchange remains a persistent non-Controller session.
- Project Manager is always dispatched with `isolated: true`; its queued/running job is the sole tracked-worktree write lease.
- Monitor is non-isolated, read-only, low-cost and rebuildable; it never launches, restarts, repairs, extends or scientifically interprets a run.
- Only Project Manager may spawn child agents, and only `hmasd-code-scout`, `hmasd-implementer`, `hmasd-verifier` and `hmasd-reviewer`.
- Existing `.codex` agents and old Manager/Monitor Skills are deleted only after the OMP runtime path passes focused capability and end-to-end smokes.
- Do not launch formal training during this migration.
- Perform the protected topology switch in an isolated worktree and integrate it as one atomic final Git boundary.

---

### Task 1: Write the Replacement Workflow Contracts First

**Files:**
- Modify: `tests/hmasd_dispatch_task_contract_test.ps1`
- Modify: `tests/hmasd_project_manager_contract_test.ps1`
- Modify: `tests/hmasd_monitor_watcher_test.ps1`
- Modify: `tests/hmasd_research_workflow_contract_test.ps1`

**Interfaces:**
- Consumes: approved design `docs/superpowers/specs/2026-07-22-omp-hmasd-task-workflow-design.md`.
- Produces: executable red/green contracts for persistent topology, OMP agent graph, authority, monitor reconstruction and legacy-path deletion.

- [ ] **Step 1: Rewrite the dispatcher contract for one persistent edge**

Require `session-roles.json` schema version 8 and exact roles
`controller,open_divergent_exchange`. Assert the Exchange binding remains
`OPEN_DIVERGENT`, every stored role omits `hostId`, `model` and `thinking`, and
the dispatcher describes exactly these execution surfaces:

```text
Controller direct control-plane work
OMP hmasd-project-manager task for authorized algorithm realization
OMP hmasd-experiment-monitor task for an authorized run
persistent open_divergent_exchange for external Pro transport
controller <-> open_divergent_exchange
```

Assert the dispatcher does not contain persistent edges for
`research_project_manager` or `experiment_monitor`, and does not route OMP task
results through the session route resolver.

- [ ] **Step 2: Rewrite the Project Manager contract around OMP profiles**

Require these exact files:

```text
.omp/agents/hmasd-project-manager.md
.omp/agents/hmasd-code-scout.md
.omp/agents/hmasd-implementer.md
.omp/agents/hmasd-verifier.md
.omp/agents/hmasd-reviewer.md
.omp/agents/references/hmasd-engineering-principles.md
```

Parse each Markdown frontmatter block. Require exact name/model/thinking/tools
and `spawns`; only Project Manager has a nonempty `spawns` array. Assert the
Manager contract gives it algorithm-realization decisions, an isolated job
write lease, `IMPLEMENTATION_PLAN.md` ownership, one repair cycle and terminal
ready/blocked output while withholding scientific-direction, formal-compute,
Git, external-review and project-control authority.

- [ ] **Step 3: Rewrite the Monitor contract around rebuildable jobs**

Require:

```text
.omp/agents/hmasd-experiment-monitor.md
.omp/agents/references/hmasd-experiment-monitor-protocol.md
.omp/agents/references/hmasd-monitor-manifest.schema.json
```

Parse the schema and require run ID, hub process name, absolute run/status
paths, progress sources, deadline, task name and terminal idempotency key.
Require `monitor-<run-id>` naming, authoritative-status-first precedence,
bounded `hub` waits, rebuild-after-root-restart semantics and terminal-only
relay. Reject `heartbeat`, persistent role IDs, route resolver fields, launch,
restart, repair, extension and scientific interpretation authority.

- [ ] **Step 4: Rewrite the whole-workflow contract**

Require active Skills exactly:

```text
hmasd-dispatch-task
hmasd-review-exchange
hmasd-review-round
```

Require the six OMP profiles (Project Manager, Monitor and four code agents),
one persistent Exchange edge, Controller direct evidence intake and Manager
algorithm authority. Reject active references to `.codex/agents`,
`HMASDCodeScout`, `HMASDImplementer`, `HMASDVerifier`, `HMASDReviewer`,
`.agents/skills/hmasd-project-manager`, `.agents/skills/hmasd-experiment`,
`research_project_manager` and `experiment_monitor` outside explicit retired-
path assertions.

- [ ] **Step 5: Run the four rewritten tests and observe RED**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_dispatch_task_contract_test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_project_manager_contract_test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_monitor_watcher_test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_research_workflow_contract_test.ps1
```

Expected: all fail because OMP profiles/schema are absent and the persistent
registry still contains Manager and Monitor. A test that passes without the
migration is incorrectly specified and must be tightened before implementation.

---

### Task 2: Install the Native OMP Task Tree

**Files:**
- Modify: `.gitignore`
- Create: `.omp/config.yml`
- Create: `.omp/agents/hmasd-project-manager.md`
- Create: `.omp/agents/hmasd-experiment-monitor.md`
- Create: `.omp/agents/hmasd-code-scout.md`
- Create: `.omp/agents/hmasd-implementer.md`
- Create: `.omp/agents/hmasd-verifier.md`
- Create: `.omp/agents/hmasd-reviewer.md`
- Create: `.omp/agents/references/hmasd-engineering-principles.md`
- Create: `.omp/agents/references/hmasd-experiment-monitor-protocol.md`
- Create: `.omp/agents/references/hmasd-monitor-manifest.schema.json`

**Interfaces:**
- Consumes: semantic role bodies in `.codex/agents/*.toml`, Manager engineering principles, old experiment protocol and the approved replacement design.
- Produces: exact OMP runtime names, static least-privilege tool sets, nested-spawn graph, task isolation and monitor recovery contract.

- [ ] **Step 1: Track native OMP definitions and scratch state**

Append to `.gitignore`:

```gitignore
# Native OMP task-agent definitions are durable project tooling.
!.omp/agents/*.md
!.omp/agents/references/*.md
!.omp/agents/references/*.json
# Visual brainstorming and runtime capability probes are local scratch.
.superpowers/
```

- [ ] **Step 2: Enable isolated Project Manager tasks**

Create `.omp/config.yml`:

```yaml
task:
  isolation:
    mode: auto
```

Keep the existing effective `task.maxRecursionDepth=2`,
`task.maxConcurrency=32` and `task.maxRuntimeMs=0`; do not duplicate defaults in
project config.

- [ ] **Step 3: Create the Project Manager profile**

Use this exact frontmatter:

```yaml
---
name: hmasd-project-manager
description: HMASD algorithm-realization and implementation manager for one externally selected scientific direction.
model: openai-codex/gpt-5.6-sol
thinking-level: xhigh
tools:
  - read
  - grep
  - glob
  - lsp
  - edit
  - write
  - bash
  - task
  - hub
spawns:
  - hmasd-code-scout
  - hmasd-implementer
  - hmasd-verifier
  - hmasd-reviewer
blocking: false
autoload-skills: false
---
```

The body must encode the approved authority matrix, require an isolated
Controller assignment, freeze the complete executable algorithm before child
spawn, enforce one writer per path, send one non-blocking plan brief through
`hub`, manage one repair cycle, and return one terminal package. It must state
that algorithm realization—including network/state/probability/gradient/clock/
replay/checkpoint and batching choices—is the Manager's decision inside the Pro
direction. It must block on changes to scientific direction, estimand, formal
compute, Git, external review, workflow topology or scope.

- [ ] **Step 4: Create the Monitor profile**

Use this exact frontmatter:

```yaml
---
name: hmasd-experiment-monitor
description: Rebuildable low-cost read-only monitor for one authorized HMASD run.
model: openai-codex/gpt-5.6-luna
thinking-level: medium
tools:
  - read
  - grep
  - hub
spawns: []
blocking: false
autoload-skills: false
---
```

The body must implement authoritative-status-first checks, bounded `hub` waits,
registered-path-only progress reads, terminal/actionable/deadline output,
run-id/task-name validation and idempotency. It must reject launch, restart,
repair, extension, scientific interpretation, writes, Git, persistent routing,
heartbeats, Skills and child spawn.

- [ ] **Step 5: Create the four code profiles**

Use YAML arrays, not comma-separated tool strings, to avoid ambiguous parser
normalization.

| Agent | Model / thinking | Tools | Spawns |
| --- | --- | --- | --- |
| `hmasd-code-scout` | `openai-codex/gpt-5.6-luna` / `medium` | `read,grep,glob,lsp` | `[]` |
| `hmasd-implementer` | `openai-codex/gpt-5.6-sol` / `high` | `read,grep,glob,lsp,edit,write,bash` | `[]` |
| `hmasd-verifier` | `openai-codex/gpt-5.6-luna` / `high` | `read,grep,glob,bash` | `[]` |
| `hmasd-reviewer` | `openai-codex/gpt-5.6-sol` / `xhigh` | `read,grep,glob,lsp` | `[]` |

Translate each corresponding TOML `developer_instructions` body to OMP tool
names. Preserve scientific, algorithm, CUDA/performance, scope and return
contracts. Remove Codex sandbox/approval prose that OMP cannot enforce and do
not grant `task`. Reviewer omits `bash` to make read-only authority structural;
Verifier retains `bash` only for exact assigned runtime checks and explicit
evidence-root writes.

- [ ] **Step 6: Create OMP references and monitor schema**

Move the unique engineering rules from
`.agents/skills/hmasd-project-manager/references/engineering-principles.md` to
`.omp/agents/references/hmasd-engineering-principles.md` without semantic loss.
Rewrite the old heartbeat protocol as
`.omp/agents/references/hmasd-experiment-monitor-protocol.md` using task jobs,
`hub`, automatic result delivery and reconstruction.

Create a JSON Schema requiring:

```json
{
  "schema_version": 1,
  "run_id": "nonempty string",
  "hub_process_name": "nonempty string",
  "run_root": "absolute path",
  "status_path": "absolute path",
  "progress_sources": "nonempty array",
  "deadline": "ISO-8601 timestamp",
  "monitor_task_name": "monitor-<run_id>",
  "terminal_idempotency_key_fields": ["run_id", "terminal_state", "status_updated_at"]
}
```

Represent this as real JSON Schema properties and required fields, not as an
example-only object.

- [ ] **Step 7: Run profile/static contract tests**

Run the Project Manager and Monitor contract tests. Expected: both pass; the
dispatcher and whole-workflow tests remain red until Task 3.

---

### Task 3: Replace Persistent Routing with Task/Hub Routing

**Files:**
- Modify: `AGENTS.md`
- Modify: `.agents/skills/hmasd-dispatch-task/SKILL.md`
- Modify: `.agents/skills/hmasd-dispatch-task/references/session-roles.json`
- Modify: `.agents/skills/hmasd-dispatch-task/scripts/audit_session_topology.ps1`
- Modify: `.agents/skills/hmasd-review-round/SKILL.md`
- Move: `.agents/skills/hmasd-project-manager/references/cdc-principles.md` → `.agents/skills/hmasd-review-round/references/cdc-principles.md`
- Modify: `docs/external-review/README.md`
- Modify: `docs/project/CURRENT_WORK.md`

**Interfaces:**
- Consumes: six native OMP profiles and the persistent Open-Pro Exchange contract.
- Produces: one persistent edge, Controller direct intake, Manager task dispatch/write lease and Monitor job/rebuild routing.

- [ ] **Step 1: Rewrite `AGENTS.md` authority and dispatch**

State the final authority matrix from the approved design. Replace Manager and
Monitor persistent surfaces with exact native OMP task names. Define Manager
queued/running state as the sole write lease and require `isolated: true`.
Define Monitor as non-isolated and rebuildable. Keep persistent routing only for
Open-Pro Exchange. Remove the current rule that temporary code agents belong to
a persistent Research Project Manager session; they instead belong only to the
OMP Project Manager task tree.

- [ ] **Step 2: Rewrite the dispatcher Skill**

Classification becomes:

```text
controller direct -> workflow, Git, direct Pro evidence intake, user communication
hmasd-project-manager task -> authorized algorithm realization and implementation
hmasd-experiment-monitor task -> one authorized run
open_divergent_exchange persistent session -> external Pro transport
```

For OMP tasks, require exact profile name, complete batch/task context, stable
name/work ID, `isolated: true` only for Manager, automatic result delivery and
`agent://`/`history://` evidence. Do not resolve or send a persistent route.
For Exchange only, retain pre/post route resolution and callback validation.

- [ ] **Step 3: Reduce the session registry**

Set schema version 8 and retain only:

```json
"controller"
"open_divergent_exchange"
```

Preserve their existing stable task IDs and Exchange role binding. Update policy
language so OMP task agents are explicitly outside the persistent registry.

- [ ] **Step 4: Move evidence intake into the controller review round**

Update `hmasd-review-round` so after exact raw archival it performs factual
reconciliation, applies the direct CDC record deltas, shows the Pro Chinese
brief and gates the next resource action. Remove `CDC_DECISION_INTAKE`,
`CDC_DECISION_BRIEF` and Project Manager session dispatch. When Pro selects an
implementation action, the round produces the exact scientific direction and
estimand inputs that a later Controller-authorized OMP Project Manager task
consumes.

Move `cdc-principles.md` into this Skill's references and update its explicit
read list.

- [ ] **Step 5: Expand topology audit scope**

Include `.omp/config.yml`, `.omp/agents/**/*.md`, `.omp/agents/**/*.json` and all
four workflow tests in `alwaysInspect`/scan scope. Ensure the audit can prove no
active Manager/Monitor session edge, heartbeat or Codex profile remains.

- [ ] **Step 6: Update active documentation**

Update `docs/external-review/README.md` to point scientific intake to the
Controller review-round Skill and algorithm realization to the OMP Project
Manager. Update `CURRENT_WORK.md` with the selected topology and new engineering
reference paths. Record that this is workflow migration only and does not resume
formal compute.

- [ ] **Step 7: Run dispatcher and whole-workflow tests**

Expected: dispatcher contract passes. Whole-workflow test remains red only on
legacy files scheduled for Task 4 removal; no topology or authority assertion
may remain red.

---

### Task 4: Delete the Superseded Session and Codex Surfaces

**Files:**
- Delete: `.agents/skills/hmasd-project-manager/SKILL.md`
- Delete: `.agents/skills/hmasd-project-manager/agents/openai.yaml`
- Delete: `.agents/skills/hmasd-project-manager/references/cdc-principles.md` after move
- Delete: `.agents/skills/hmasd-project-manager/references/engineering-principles.md` after move
- Delete: `.agents/skills/hmasd-experiment/SKILL.md`
- Delete: `.agents/skills/hmasd-experiment/agents/openai.yaml`
- Delete: `.agents/skills/hmasd-experiment/references/experiment-protocol.md`
- Delete: `.agents/skills/hmasd-experiment/references/monitor-task.json`
- Delete: `.codex/agents/hmasd-code-scout.toml`
- Delete: `.codex/agents/hmasd-implementer.toml`
- Delete: `.codex/agents/hmasd-verifier.toml`
- Delete: `.codex/agents/hmasd-reviewer.toml`
- Delete: `.codex/config.toml`
- Delete: `.codex/refresh-model-catalog-v2-workaround.ps1`
- Delete: `runtime/model-catalog-v2-workaround.json`

**Interfaces:**
- Consumes: green OMP profile and routing contracts.
- Produces: clean active-line cutover with no duplicate agent, heartbeat, session or model-catalog path.

- [ ] **Step 1: Prove the new path is statically green before deletion**

Run Project Manager, Monitor and dispatcher tests. All must pass. Do not delete
legacy paths if any native OMP assertion fails.

- [ ] **Step 2: Delete all listed legacy files**

The Codex config exists only for the superseded multi-agent surface and Luna v2
catalog workaround; delete it with the generated catalog and refresh helper.
Preserve no aliases, shims, deprecated registry entries or fallback dispatch.

- [ ] **Step 3: Run all four workflow contracts**

Expected exact outputs:

```text
HMASD_DISPATCH_TASK_CONTRACT_OK
HMASD_PROJECT_MANAGER_CONTRACT_OK
HMASD_MONITOR_TASK_CONTRACT_OK
HMASD_RESEARCH_WORKFLOW_CONTRACT_OK
```

- [ ] **Step 4: Run the topology audit for retired terms**

Audit at least:

```text
research_project_manager
experiment_monitor
hmasd-project-manager/SKILL.md
hmasd-experiment/SKILL.md
HMASDCodeScout
HMASDImplementer
HMASDVerifier
HMASDReviewer
monitor heartbeat
```

Expected: matches occur only in explicit retired-path assertions or immutable
historical evidence, never active Skills, registry, config or control plane.

---

### Task 5: Exercise the OMP Runtime End to End

**Files:**
- Create temporarily, then remove: `tests/fixtures/omp_manager_smoke_target.txt`
- Create temporarily, then remove: `logs/omp-monitor-smoke/`
- No permanent source files beyond Tasks 1–4.

**Interfaces:**
- Consumes: live OMP profile discovery, task isolation, nested spawn, hub process supervision and monitor manifest.
- Produces: controller-observed runtime evidence for the actual OMP execution path.

- [ ] **Step 1: Run six-agent discovery and least-privilege smoke**

From the isolated worktree, run `omp -p --no-session` and require one batch that
resolves all six exact profile names. Use each exact task `name` equal to its
agent type. Require profile-role output, model resolution and no unknown-agent,
frontmatter or tool error.

For read-only profiles, record pre/post sentinel absence and inspect task output/
transcript for no mutation tool call. For Manager, verify the child roster lists
only the four allowed code agents. Treat agent self-report alone as
insufficient; Controller checks filesystem and task artifacts.

- [ ] **Step 2: Exercise a harmless isolated Manager task tree**

Create a tracked smoke target containing `before`. Dispatch
`hmasd-project-manager` with `isolated: true` and a workflow-only frozen
assignment that authorizes changing it to `after`, requires one Code Scout to
map the file, one Implementer to edit it and one Reviewer to review the package.
No scientific or experiment files are in scope.

Expected: Manager sends one plan brief, uses only allowed children, returns one
integrated package, task isolation applies the single intended change, and no
other file changes. Restore and remove the smoke target after capturing proof.

- [ ] **Step 3: Exercise Monitor terminal observation**

Start a short named persistent `hub` process that writes a valid nonterminal
status, waits, writes terminal `COMPLETE`, then exits. Write a valid manifest
under `logs/omp-monitor-smoke/`. Dispatch the exact Monitor name
`monitor-omp-monitor-smoke` non-isolated.

Expected: Monitor reports the authoritative terminal payload without launching,
restarting or modifying the process. Controller observes unchanged process
identity and no source/control mutation.

- [ ] **Step 4: Exercise Monitor reconstruction**

Run a second short process. Start then cancel/abort the first Monitor while the
process remains nonterminal. From a fresh `omp -p` root, read the same manifest,
confirm the persistent process still exists, and create the same named Monitor
only because no matching job exists.

Expected: exactly one replacement Monitor reports terminal state; process start
identity is unchanged; terminal idempotency key is stable; no duplicate callback,
heartbeat or experiment restart occurs.

- [ ] **Step 5: Remove smoke artifacts and rerun four contracts**

Delete the temporary fixture and smoke log root. Run all four workflow tests
again. Expected: all exact OK outputs, no warnings and no smoke artifact in the
tracked package.

---

### Task 6: Independent Review, Active-Line Cleanup and Atomic Commit

**Files:**
- Delete: `docs/superpowers/specs/2026-07-22-omp-hmasd-agents-design.md`
- Delete: `docs/superpowers/plans/2026-07-22-omp-hmasd-agents.md`
- Retain: `docs/superpowers/specs/2026-07-22-omp-hmasd-task-workflow-design.md`
- Retain: `docs/superpowers/plans/2026-07-22-omp-hmasd-task-workflow.md`

**Interfaces:**
- Consumes: green static contracts and successful runtime smokes.
- Produces: independently reviewed, active-line-only workflow package.

- [ ] **Step 1: Dispatch the new OMP Reviewer over the complete package**

Use exact profile `hmasd-reviewer`. Give it the approved spec, plan, complete
changed-path list, four contract outputs and raw runtime-smoke artifacts. Require
findings by severity, authority fidelity, OMP capability mapping, persistent
edge audit, Manager algorithm authority, monitor reconstruction and obsolete
path detection.

- [ ] **Step 2: Fix every Critical or Important finding once**

Return a concrete defect to its owning path. Rerun the directly implicated
contract/smoke. A repeated substantive boundary blocks completion rather than
adding compatibility fallbacks.

- [ ] **Step 3: Delete the superseded simple-copy spec and plan**

Delete only after the replacement path demonstrably works. Git history retains
the earlier design; the active tree keeps one workflow design and one executable
plan.

- [ ] **Step 4: Run final focused verification**

Run all four PowerShell contracts, the six-agent discovery smoke, one bounded
Manager child-roster smoke and one Monitor manifest/status smoke. Confirm no
formal experiment runs, no legacy Codex/session files remain, and only the
listed intended paths are changed.

- [ ] **Step 5: Commit the atomic protected topology boundary**

Stage only the intended workflow files and commit:

```bash
git commit -m "refactor: migrate HMASD workflow to OMP task agents"
```

Do not push or merge until the Controller repeats the focused verification on
the integrated result.
