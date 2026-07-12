# HMASD Temporary AGENTS Workflow Reset Design

Date: 2026-07-12

## Goal

Temporarily remove the obsolete project-specific subagent and Superpowers
prompting rules from `AGENTS.md` so a replacement workflow can be explored for
the new model generation. Do not disable runtime capabilities or delete any
configuration, research history, experiment evidence, or agent definitions.

## Runtime And Configuration Boundary

- Keep `.codex/config.toml` unchanged, including `multi_agent = true` and all
  registered custom agents.
- Keep `.codex/agents/*.toml` and `.claude/agents/` unchanged.
- Do not delete or move `.claude/agents/`, `.superpowers/`, `docs/subagents/`,
  or `docs/superpowers/`.
- Do not uninstall or disable globally installed Codex plugins.
- Runtime multi-agent support remains available, but no old HMASD-specific
  routing, role, lifecycle, or automatic-hook policy remains authoritative.

## Controller Contract

Rewrite `AGENTS.md` as a compact controller and research contract. Preserve:

- first-read project memory order;
- direct controller responsibility for understanding, implementation,
  verification, explanation, and decisions;
- experiment-meaning reporting, time/device disclosure, and cloud-CUDA default;
- causal-claim discipline, baseline hierarchy, promotion ladder, and failure
  review gate;
- filesystem, Git, test hygiene, dirty-worktree, and no-unrelated-revert rules.

Remove active requirements for:

- subagent dispatch, role/model routing, briefs, reports, reviewer waves,
  lifecycle/cache management, and automatic memory/experiment hooks;
- `.superpowers/sdd/progress.md` and Superpowers execution-plan handling;
- project-level mandatory Superpowers skill invocation.

Add one short transition statement: the old project-specific delegated-work
policy is retired pending a separately reviewed replacement for the new model
generation. Until that replacement exists, the controller works directly by
default and must not infer the removed role/router rules from historical files.

The controller may still read historical files whose existing paths contain
`docs/superpowers/`; those paths are research provenance, not an active
workflow requirement.

## File Scope

The implementation changes only `AGENTS.md`. Keep `.codex/config.toml`, all
agent files, `.superpowers/`, `docs/subagents/`, `docs/superpowers/`, and all
`memory/` files unchanged. Historical references remain provenance, not active
workflow authority.

## Verification

- Confirm `.codex/config.toml` is byte-for-byte unchanged and still exposes the
  configured runtime capabilities.
- Confirm `AGENTS.md` contains no active subagent dispatch, model-routing,
  lifecycle, or Superpowers process requirements.
- Confirm agent definitions and historical research documents still exist.
- Run `git diff --check` on the changed files.
- Do not run algorithm or experiment tests because no algorithm/runtime code is
  modified.

## Reversibility

Keep the `AGENTS.md` reset in one focused commit. A future model-aware workflow
must be designed and reviewed from current model behavior rather than restoring
the old prompt wholesale. The previous contract remains recoverable from Git.

## Non-Goals

- No deletion or relocation of historical plans/specs.
- No changes to HA-CTSE/HMASD algorithms, environments, rewards, collectors,
  experiments, checkpoints, or results.
- No global Codex plugin installation changes.
- No `.codex/config.toml`, agent-profile, or memory changes.
