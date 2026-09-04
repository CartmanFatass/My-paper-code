# Rollout Acceptance

Acceptance evidence for the isolated worktree:

- Behavioral Hooks: disabled (`features.hooks=false`, zero TOML hook tables).
- Native auto-compaction: untouched.
- Assignment/result validators, E0–E5 routing, resource preflight, manifest
  and runtime plausibility: focused tests green.
- No fixed direction cap and no worker-count default/cap: active registry
  nonrequirements plus constraint lint.
- Result-bearing available route: C++ and parallel manifest enforcement.
- Internal repository handoff: no SHA-256 requirement.
- Supervisor lifecycle: explicit READY/STATUS/STOPPED wrappers,
  `automatic_wake=false`.
- Stage 5/unattended scheduler behavior: not authorized or added.

The final mixed suite completed with `698 passed, 66 skipped` in 99.51s. The
two boundary scripts (`hmasd-constraint-lint.ps1` and
`hmasd-requirements.ps1 validate`) also returned valid/clean from this isolated
worktree.
