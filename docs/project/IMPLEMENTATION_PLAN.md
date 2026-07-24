# OMP workflow-asset consolidation plan

```text
active_boundary=OMP_WORKFLOW_ASSET_CONSOLIDATION
implementation_status=ACCEPTED
branch=Claude
root_bootstrap=AGENTS.md
active_asset_root=.omp
scientific_compute=none
external_submission=ready_after_commit_push
```

## Goal and success criteria

Consolidate every live HMASD orchestration asset under `.omp/` so the workflow
can be migrated as one directory while root `AGENTS.md` remains the only
standalone bootstrap contract.

Success requires:

1. active Skills exist only under `.omp/skills/`;
2. project-local task agents remain under `.omp/agents/`;
3. OMP configuration and BrowserMCP configuration remain under `.omp/`;
4. retained pre-OMP Codex profiles and role charters move under
   `.omp/legacy/` and are explicitly non-active;
5. `.agents/` and `.codex/` no longer exist;
6. the active external-review -> Controller plan -> local implementation and
   collective review -> registered experiment Monitor -> external result-review
   loop remains explicit and contract-tested; and
7. no historical external-review round, scientific evidence record, algorithm
   source or runtime result is moved or rewritten.

## Scope decision

Three approaches were considered.

1. Move the entire repository below `.omp/`. Rejected: source code, scientific
   evidence and immutable review rounds are project payload, not OMP runtime
   assets, and their Git-visible paths carry evidence meaning.
2. Keep `.agents/` and `.codex/` adapters that forward into `.omp/`. Rejected:
   duplicate discovery roots undermine portability and violate clean cutover.
3. Move only orchestration assets into native OMP roots and preserve historical
   scientific paths. Selected: it gives one portable workflow directory
   without mutating evidence identity.

## Exact moves

- `.agents/skills/**` -> `.omp/skills/**` as the sole active Skill tree.
- `.agents/roles/**` -> `.omp/legacy/roles/**` as retained, non-active
  pre-unification charters.
- `.codex/**` -> `.omp/legacy/codex/**` as retained, non-active pre-OMP
  profiles and utilities.
- Keep `.omp/agents/*.md`, `.omp/config.yml` and `.omp/mcp.json` in place.

## Reference cutover

Update the active bootstrap and contracts to use `.omp/skills/`:

- `AGENTS.md`;
- `docs/project/ALGORITHM_PRINCIPLES.md`;
- `docs/project/CURRENT_WORK.md`;
- `docs/project/AGENT_CONTEXT.md`;
- `docs/external-review/README.md`;
- `docs/external-review/REVIEWER_CONVERSATIONS.json`;
- all focused PowerShell workflow-contract tests.

Historical files beneath `docs/external-review/rounds/` and durable CDC evidence
are immutable and remain unchanged even when they mention the former path that
was valid at their evidence commit.

## Invariants

- Native OMP discovers exactly five `hmasd-*` Skills and six local task-agent
  profiles.
- External Pro transport remains Controller-owned through the pinned
  `browsermcp-pro` server, exact V1 question/response envelope, immutable v2
  receipt and stable-twice archival.
- The Controller remains the sole executable-plan author and Git integrator.
- A complete implementation package receives exactly one parallel Reviewer and
  Verifier collective gate.
- `experiment_monitor` remains the only persistent experiment observer and must
  be rebuilt as Spark-medium before the first authorized conclusion-bearing
  run.
- Retained legacy files have no active discovery, routing or authority role.
- No compatibility shim, duplicate Skill, symlink or fallback path remains.

## Red/green checks

Run:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_dispatch_task_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_controller_subagent_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/review_round_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/browser_pro_dispatch_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_research_workflow_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_project_manager_contract_test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_experiment_operator_contract_test.ps1
```

The checks must prove the native `.omp` paths, exact end-to-end research loop,
five-Skill/six-agent inventory, BrowserMCP state machine, registered Monitor
route, absence of active `.agents`/`.codex` roots and no stale active path
references. Then run `git diff --check`.
