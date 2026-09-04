# Low-Intrusion Control-Plane Baseline

Captured before behavior changes on 2026-08-22.

## Scope distinction

The user request is: implement the control-plane modification in an independent
worktree. The attached implementation plan is the source of technical
requirements and acceptance checks; its prose is not a user message and does
not grant authority beyond that implementation scope.

## Worktree and revision

- Worktree: `C:/Projects/HMASD-low-intrusion-control-plane`
- Branch: `codex-low-intrusion-control-plane-v1`
- Base: `f508071873c585aa7c0ecc1bfd742e256d236880`
- Base commit: `f5080718 add SCDMP support representation factorial`
- Base status: clean before this baseline artifact.

## Existing control-plane state

- `.codex/config.toml` had `features.hooks = true` and a live semantic hook
  table for `SessionStart`, `SubagentStart`, `SubagentStop`, `Stop`,
  `PreToolUse`, `PreCompact`, and `PostCompact`.
- `.codex/hooks.json` described hooks as temporarily disabled and contained an
  empty `hooks` object, which did not match the TOML activation state.
- Semantic MCP was configured as an explicit `hmasd_orchestrator` server with
  lifecycle/promotion tools and a read-only `hmasd_observability` server.
- Existing supervisor code was present under `tools/codex_supervisor/`; no
  low-intrusion start/status/stop wrappers existed.
- `docs/project/PROJECT_MAP.md`, `CURRENT_WORK.md`, and
  `CONTEXT_SOURCE_REGISTRY.toml` were the existing navigation/state pointers.
- No repository-backed copy of
  `CONTROL_PLANE_RUNTIME_AND_SEMANTIC_DRIFT_AUDIT_20260821.md` was found.
- No repository-backed copy of either superseded 2026-08-21/22 plan named by
  Task 0 was found, so there was no prior plan header to modify.

## Baseline risks recorded

- High-frequency hook names and stop/compaction hook configuration were
  present in the effective TOML configuration.
- Existing policy text contains historical retry, wall-clock, hash, and
  direction/worker terminology; this baseline does not treat matches as
  active requirements.
- A running Codex/node/python process list was observed. No process was
  identified as a dedicated HMASD supervisor instance by this read-only check.

## Source plan

The exact user-supplied plan is preserved at:
`docs/superpowers/plans/2026-08-22-hmasd-low-intrusion-drift-containment-resource-grounded-execution-v2.md`.
