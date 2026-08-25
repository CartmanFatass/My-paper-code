# HMASD Codex capability matrix

Status: runtime Work packages A/B, the first native Windows peer-task smoke,
and the local selective integration into `main` completed on 2026-08-25. No
branch was pushed. Fresh-host depth and task-recovery evidence remain outstanding.

## Smoke boundary

- Workspace: saved local project at `C:/Projects/HMASD`, branch
  `omp/workflow`; no migration worktree.
- Tasks: current Root plus disposable `Portfolio-SMOKE-G1`,
  `EM-ucope-SMOKE-G1`, and `CM-ucope-SMOKE-G1` peer tasks.
- Requested runtime: `gpt-5.6-luna`, `xhigh` for all three fixture tasks.
- Effects forbidden: durable authority writes, experiments, external sends,
  worktree creation, commit, and push.
- Existing uncommitted Root changes had to remain byte-for-byte in place.

## Observations

| Capability | Evidence | Result |
| --- | --- | --- |
| Create peer task in saved project | Three tasks were created with the local project environment and independent titles/history. | PASS |
| Direct user-visible task input | Each creation prompt appears as the initial user-visible message in that task. | PASS |
| Project instruction/skill visibility | All fixtures read root `AGENTS.md`, `.codex/config.toml`, and their project skills. | PASS |
| Shared local checkout | EM/CM read current `omp/workflow` and observed the same Root-owned dirty state without changing it. | PASS |
| Direct leaf dispatch | Portfolio created a research scout; EM created a research scout; CM created a code scout. | PASS |
| Cross-task wait | Root followed all three tasks with bounded cursor-aware waits and received independent terminal results. | PASS |
| Cross-task follow-up | Root sent a later bounded engineering request to the existing CM task. | PASS |
| Runtime task reference map | Root recorded reconstructable task references in ignored `.codex/runtime/tasks.json`. | PASS |
| Runtime model evidence | Task creation accepted Luna/xhigh, but the returned task/leaf records did not expose a resolved runtime model echo. | PARTIAL |
| `agents.max_depth = 1` | The smoke reused a Codex host started before the project config change; a nested child completed, but the result is invalid for post-restart enforcement. | UNVERIFIED AFTER RESTART |
| Worktree preservation | No fixture created a worktree; Git branch/HEAD and Root-owned changes remained present. | PASS |

## Runtime control-plane contract evidence

| Capability | Evidence | Result |
| --- | --- | --- |
| Root-owned `runtime_tasks` cache | `hmasd_state.py` schema/path/writer/expected-revision CAS accepts `.codex/runtime/tasks.json` and rejects wrong path/writer, duplicate identity, and stale revision. | PASS |
| Root-owned `runtime_worktrees` cache | Worktree helper uses `.codex/runtime/worktrees.json` and state CLI/CAS for initialize and replacement; later operations do not write the legacy journal. | PASS |
| Validated legacy worktree import | Legacy-only input is checked for schema, receipt, Git registration/path facts, then imported once; the `.omp` source remains byte-for-byte unchanged. | PASS |
| Missing receipt safety boundary | A legacy row without its receipt returns code 6 before canonical import or Git orphan classification; a repeated provision attempt has no filesystem, journal, or worktree effect. | PASS |
| Legacy/canonical dual-map ownership | Canonical-only is allowed; canonical revision ahead of legacy is normal forward progress; same-revision rows must agree; legacy-ahead or same-revision fact conflict fails closed. | PASS |
| `runtime_agents` ownership | Native task listing plus `runtime_tasks` replaces the retired OMP agent/session map; no Codex canonical `runtime_agents` writer is defined. | PASS |
| Dashboard transition policy | Codex runtime/task projection has priority; OMP runtime is read-only fallback during transition and is not clean-cutover evidence. | PARTIAL |

## Depth finding

The project config is intentionally main-compatible and contains both:

```toml
[features]
multi_agent_v2 = true

[agents]
max_depth = 1
```

`agents.max_depth = 1` is valid project configuration. The configured bound is
loaded when Codex starts, so the first smoke cannot test it because that host
predated the project-config change.

Consequences:

1. `max_depth = 1` is valid syntax and remains the required main-derived value.
2. The current host result is not valid evidence for or against enforcement
   after restart.
3. Restart Codex completely, create a new top-level task, then repeat one direct
   leaf plus one nested spawn attempt.
4. Until that passes, top-level task skills and bounded assignments must still
   never ask a leaf to delegate.

## Still unverified

- Task restart/compaction followed by identity reconciliation.
- `handoff`, pin, archive/unarchive, and stale-cursor recovery.
- Resolved `gpt-5.6-sol` max evidence for a real Portfolio decision.
- Direct user interaction with final non-fixture Portfolio/EM/CM tasks.
- Whether native task listing is sufficient to remove the ignored task map.
- Shadow operation and clean OMP-to-Codex ownership cutover.

## Explicit cutover boundary

The code, durable authority layout, and local Git target have been migrated to
`main`; this does not claim the remaining product smoke has passed. Work package
E still requires a complete Codex restart and fresh-host proof of
`max_depth = 1`, task recovery, and runtime-map rebuild. Local `.omp` runtime
residue remains ignored and is not a Codex authority.
