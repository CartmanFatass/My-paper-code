# Repository Context Lifecycle Baseline

Captured at Task 1 of
`2026-08-17-hmasd-repository-owned-context-lifecycle.md`.
This file binds every later context-lifecycle interface to the accepted
actor-scoped overlay. It does not create scientific, technical, or portfolio
authority.

```text
baseline_commit=1df15d13dd3b8e2d779508148c07c43033af18ad
baseline_branch=aggressive
worktree=C:\Projects\HMASD
Python executable=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
Codex version=unobserved in this batch
semantic schema version=2
test count=211 passed in 94.53s
previous-plan acceptance report path=docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/ACCEPTANCE_REPORT.md
previous-plan source path=C:\Users\fires\Downloads\2026-08-17-hmasd-codex-actor-scoped-compaction-resilience.md
previous-plan repo copy=docs/superpowers/plans/2026-08-17-hmasd-codex-actor-scoped-compaction-resilience.md (absent at capture)
```

## Worktree and working tree

The capture used the main workspace `C:\Projects\HMASD` on `aggressive` at
`1df15d13`. An isolated empty worktree was not created because the same
checkout already holds the accepted overlay and later tasks share
`db.py` / `store.py` / `mcp_server.py`. Unrelated research, environment, and
`.tmp_*` dirty files were present and were not part of this baseline.

`git status --short` was therefore not empty. The accepted overlay commit
itself is `1df15d13` (`docs: accept actor-scoped compaction resilience`).

## Previous-plan gates observed at capture

| Gate | Observation |
| --- | --- |
| Required public modules | All eleven expected files exist |
| `tests/codex_semantic_mvp` | `211 passed in 94.53s` |
| Doctor | `actor_schema_ready=true`, `compaction_hooks_ready=true`, `runtime_is_canonical_memory=false`, `schema_version=2` |
| Doctor mode | `unknown` because the live `.codex/config.toml` hook block predates the six-event ACTIVE set |
| Automatic rehydration | Portfolio and Operational Root enabled; EM/CM/LEAF disabled |
| Live eight-canary Codex compact/resume | Not executed; recorded as explicit observed fallback |
| PowerShell 5.1 live disable/restore | Outstanding; not required to mutate the live config in this capture |

The acceptance report and topology probe already record the same fallback:
EM/CM/leaf automatic rehydration stays off until a live identity probe exists.
That is an explicit observed fallback, not an unrecorded gap.

This plan continues because the synthetic/control-plane overlay is stable, the
user previously deferred live Codex canaries, and the remaining previous-plan
items are live host operations this CLI cannot perform.

## Accepted public interfaces

Recorded by source inspection of `tools/codex_semantic_mvp/` at `1df15d13`.

| Concept | Implementation |
| --- | --- |
| `ActorKind` | `tools.codex_semantic_mvp.actor_models.ActorKind` |
| `ActorContext` | `tools.codex_semantic_mvp.actor_models.ActorContext` |
| current actor lookup | `actor_registry.resolve_actor_context`, `register_session_root`, `register_child_actor` |
| open/current epoch | `epochs.plan_epoch_open`, `epochs.plan_epoch_current`, `epochs.revise_epoch`, `epochs.plan_epoch_close` |
| semantic commit write/current | `semantic_commits.semantic_commit_write`, `semantic_commits.semantic_commit_current` |
| checkpoint materialize/current | `checkpoints.materialize_checkpoint`, `checkpoints.current_checkpoint` |
| packet reference | `packet_refs.packet_register`, `packet_mark_delivery`, `packet_acknowledge`, `packet_mark_intaken`, `packet_mark_applied` |
| working capsule builder | `capsules.build_capsule`, `capsules.render_capsule` |
| `state_version` source | `store.SemanticStore` workflow row `state_version` via `_touch_workflow` |
| reanchor acknowledgment | `checkpoints.context_reanchor_ack`, `ensure_reanchor_obligation`, `is_actor_reanchored` |

Supporting types used unchanged: `ActorState`, `EpochKind`, `SemanticCommitKind`,
`ObligationKind` (includes `CONTEXT_REANCHOR_REQUIRED` and
`PACKET_INTAKE_REQUIRED`), owner-local workflows via
`SemanticStore.open_actor_workflow` / `current_actor_workflow`.

## Known fallback layers

- Live Portfolio / Operational Root / EM / CM / leaf compact-resume canaries
  remain unobserved. Automatic rehydration stays limited to Portfolio and
  Operational Root session-root identity.
- Narrow `PreToolUse` matcher is unverified and is not part of ACTIVE.
- Doctor `mode=unknown` until the live workspace is re-enabled with the
  six-event ACTIVE hook set.
- Codex version and live identity fields are unobserved.
- Compaction summaries and automatic Memory remain non-authoritative hints.

Later context-lifecycle tasks must import these public names. They must not
recreate a competing actor, epoch, checkpoint, packet, or capsule store.
