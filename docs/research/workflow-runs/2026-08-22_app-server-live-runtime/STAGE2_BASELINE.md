# Stage 2 Baseline

- Branch: `codex-app-server-live-runtime-v1`
- HEAD / accepted Stage 1 merge: `ae61835d72a90101913d4e6230e39a8f0767e593`
- Pre-document git status: clean.
- Stage 1 acceptance path: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_ACCEPTANCE.md` exists.
- Its file history includes `05561aaa docs: accept context foundation closure`.
- `git merge-base --is-ancestor ae61835d72a90101913d4e6230e39a8f0767e593 HEAD` exited `0`.

## Baseline check

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/codex_supervisor -q --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_stage2_baseline
```

Result: `337 passed in 70.87s`, exit `0`.

## Boundaries

- Stage 1 context foundation accepted.
- Stage 2 runtime implementation and live acceptance not yet attempted.
- `behavioral_hooks=false`.
- `native_auto_compaction=unchanged`.
- External runtime/process lifecycle/model-turn/provider-send facts are not established by this baseline.
