---
name: hmasd-workflow-change-audit
description: Use when changing HMASD routers, role charters, procedural Skills, native-agent profiles or registry, active workflow documents, or their contract tests.
---

# HMASD Workflow Change Audit

## Contract boundary

This is a Project Manager control-plane procedure. It grants no scientific,
formal-compute, external-review or child acceptance authority. External Pro
continues to own science and Project Manager remains the only code and workflow
acceptance owner. Generic planning, ticket, TDD and review-stack Skills remain
disabled.

Use this Skill when a mutation touches any of these coupled surfaces:

- `AGENTS.md` or `.agents/roles/*.md`;
- `.agents/skills/*/SKILL.md` or their reusable scripts;
- `.codex/config.toml` or `.codex/agents/*.toml`;
- active workflow state, routing, restart or contract documents; or
- tests that enforce those surfaces.

`docs/project/RESTART_HANDOFF.md` is not routine workflow state. Create or
update it only when the user explicitly requests a handoff; a normal restart or
safe stop uses `CURRENT_WORK.md` and Git without generating that document.

Ordinary algorithm implementation stays on
`hmasd-agile-research-development`. A scientific authority or evidence change
first follows `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.

## One continuous change loop

1. **Inventory.** Search the active control plane for the changed identity,
   path, authority term and every retired name. Include router, roles, Skills,
   registry, profiles, active project documents and contract tests. Historical
   external-review evidence and scientific uses of words such as controller are
   evidence, not automatic repair targets.
2. **Classify.** Before editing, keep a task-local impact matrix with one row per
   discovered surface: `path | relation | action | evidence`. Every row is
   exactly one of `modify`, `add`, `delete`, `unchanged-valid` or
   `historical-exempt`. Declare the exact owned path set and preserve any
   pre-existing dirty changes outside the task.
   If any child uses an isolated worktree, create its identity and path scope
   with `scripts/hmasd_workspace_ticket.py`; pass only the ticket path, require
   child-side `resolve`, and run PM-side `verify`. Never transcribe a UUID-heavy
   worktree path into an assignment.
3. **Probe.** Run the smallest existing contract that should expose the change.
   If it passes despite a known missing relation, add one negative regression
   for that relation rather than expanding a coverage suite.
4. **Implement.** Close the smallest active-line dependency set. A registered
   profile names exactly one existing role charter. Every profile is registered
   exactly once; every role and Skill is routed. Remove superseded live paths
   instead of keeping compatibility aliases. Use
   `hmasd-agile-research-development` for any source-code slice.
5. **Verify closure.** Run the bundled checker, the affected focused contract
   tests and targeted negative searches from the impact matrix. Inspect the
   actual diff path set and `git diff --check`. The checker is structural; it
   does not replace change-specific semantic checks.
6. **Reload smoke.** If router, registry or profiles changed, start a fresh
   Codex task before relying on discovery. Smoke every changed callable profile
   against its exact fail-closed boundary. Do not substitute a default child
   when a registered type is unavailable.

Run the structural checker with the Python interpreter registered in
`docs/project/CURRENT_WORK.md`:

```powershell
& '<registered-python>' .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py --repo .
```

Add change-specific active files or retired terms when needed:

```powershell
& '<registered-python>' .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py --repo . --active-path docs/project/CURRENT_WORK.md --forbid hmasd-old-agent
```

## Acceptance and stop

Accept only when the impact matrix is classified, structural closure passes,
focused contracts pass, targeted stale-reference searches are explained, and
the exact changed path set is inspected. A fresh-task profile smoke may remain
an explicit post-restart condition when the current task cannot reload its own
router.

Stop for a missing authority decision, an ambiguous active-versus-historical
surface, same-file collision or unavailable required profile. Do not resolve a
scientific ambiguity or weaken the checker locally.
