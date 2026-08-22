# Stage 1 Baseline — Context Foundation Closure

## Scope

Task 0 freezes the repository baseline only.  It makes no behavioral
modification.  The pytest `--basetemp` directory is transient test output and
is not a publication artifact.

## Isolated worktree and effective baseline

- Linked worktree: `C:/Projects/HMASD-context-foundation-closure`
- Branch: `codex-context-foundation-closure-v1`
- Original `origin/aggressive` source commit:
  `7cc1a56c188d39af61ee70979adc4e2dd1e9c0ae`
- The initial hard gate on that source failed before implementation:
  `1 failed, 372 passed, 66 skipped in 50.61s`.
- Failing test:
  `tests/codex_context_lifecycle/test_source_registry.py::test_operational_root_projection_excludes_em_cm_internals`.
- Cause: the registry referenced the missing canonical artifact
  `docs/research/workflow-runs/2026-08-11_five-round-research-team/P0_HIDDEN_LIMIT_CONTROL_PLANE_CORRECTION_20260821.md`.
- Operational Root repaired that exact baseline inconsistency in
  `530f827d5fdc482c0f79534f1785c4968808c278`
  (`fix: publish hidden-limit control-plane correction`), adding only the
  missing operational_root-owned canonical artifact.  Root reported the
  focused test passed and the repaired baseline as `373 passed, 66 skipped in
  43.20s`.
- Effective Task 0 baseline / HEAD:
  `530f827d5fdc482c0f79534f1785c4968808c278`.
- The worktree was clean after the prior basetemp cleanup and before the CM
  rerun.

## CM baseline rerun

Exact command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest tests/codex_context_lifecycle tests/hmasd_control_plane tests/codex_semantic_mvp -q --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_stage1_baseline
```

Result: `373 passed, 66 skipped in 36.52s` (exit 0).

## Foundation commands

Exact decisions-index command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m tools.codex_context_lifecycle.cli decisions-index --repo-root C:/Projects/HMASD-context-foundation-closure
```

It exited 0 with empty stdout.  Its output file was content-identical to HEAD
with hash `d3b0e4230b1607cc5f2d6862fd7f8e5cee765686`.

Exact doctor command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m tools.codex_context_lifecycle.cli doctor --repo-root C:/Projects/HMASD-context-foundation-closure
```

It exited 0 and reported:

```text
schema_version=3
previous_plan_baseline_present=true
source_registry_valid=true
project_map_contract_valid=true
decision_index_current=true
memory_authority=none
compaction_summary_authority=none
physical_deletion_enabled=false
active_actor_count=0
open_promotion_count=0
prepared_rollover_count=0
archive_candidate_count=0
```

`.codex/config.toml` line 7 is `hooks = false`; the adjacent comments state
that behavioral lifecycle Hooks are disabled and native auto-compaction remains
unchanged.

## Current log — 8 entries

```text
530f827d fix: publish hidden-limit control-plane correction
7cc1a56c chore: consolidate control-plane and experiment workspace changes
1abf9c76 feat: add low-intrusion control-plane boundaries
d45a4006 docs: freeze low-intrusion control-plane baseline
f4aacb98 docs: freeze low-intrusion control-plane baseline
f5080718 add SCDMP support representation factorial
fc85fa11 add cost-aware agent model routing
11b0a63c record MCP control-plane v1.1 acceptance
```

## Plan artifact

The execution plan is copied byte-for-byte from
`C:/Users/fires/Downloads/2026-08-22-hmasd-context-foundation-and-app-server-runtime-two-stage-plan.md`
to `docs/superpowers/plans/2026-08-22-hmasd-context-foundation-and-app-server-runtime-two-stage-plan.md`.
The verified SHA-256 for both files is
`21E0F0938C23AAEF7BEE9F6D6ECAB8C3E797AAD81FECFA6AFB4E38EE47BFA631`.
