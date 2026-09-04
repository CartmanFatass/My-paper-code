# Repository-Owned Context Lifecycle Acceptance

```text
previous-plan accepted baseline=1df15d13dd3b8e2d779508148c07c43033af18ad
schema version=3
context hierarchy=P0-P9 in docs/project/CONTEXT_PRECEDENCE.md and tools/codex_context_lifecycle/precedence.py
existing PROJECT_MAP reuse=docs/project/PROJECT_MAP.md remains the sole stable map
ADR IDs=ADR-0001, ADR-0002, ADR-0003, ADR-0004
test command=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/codex_semantic_mvp tests/codex_context_lifecycle -q --basetemp=C:/Projects/HMASD/.tmp_ctx_full
test count=277 passed in 96.21s
doctor=schema 3, registry valid, PROJECT_MAP valid, decision index current, memory authority none, physical deletion disabled
GC dry-run=deletions []
live canaries=synthetic only; live Codex compact/resume outstanding
```

## What was accepted

- Context sources are registered by path, not copied into SQLite.
- Promotion requires owner disposition and a real canonical file; MCP never
  writes that file.
- Epoch rollover is prepare/confirm/apply and cannot drop open obligations.
- Working sets exclude closed/stale objects. Forgetting is exclusion.
- Automatic memory and compaction summaries cannot create authority or state
  transitions.
- `AGENTS.md` gained one compact non-authority pointer. Roles were not copied.

## Known limitations

- Live eight-canary Codex compact/resume from the previous plan remains
  unobserved. EM/CM/leaf automatic rehydration stays disabled.
- The host interpreter is Python 3.10; TOML parsing uses `tomli` when
  `tomllib` is absent.
- Doctor mode on the live `.codex/config.toml` may remain `unknown` until the
  workspace is re-enabled with the six-event ACTIVE hook set.

## Rollback

Revert to `1df15d13`. Schema v3 migration is additive. It does not delete v2
rows. A newer-than-supported schema still fails closed.
