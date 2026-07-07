Task 2 completed for HMASD R24 forced behavior audit.

Commit: 503812f

### Files changed
- `ha_ctse_process/r24_behavior_audit.py` (added `write_audit_csv`)
- `tests/r24_behavior_audit_test.py` (added `test_write_audit_csv_roundtrip`)
- `scripts/r24_forced_behavior_audit.py` (created)
- `scripts/run_r24_behavior_audit_local_cuda.ps1` (created)
- `.superpowers/sdd/task-2-report.md` (created)

### Verification
- `& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py::test_write_audit_csv_roundtrip -q` -> `1 passed`
- `& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q` -> `8 passed`
- `& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile scripts\r24_forced_behavior_audit.py` produced a local pycache permission error under default `scripts/__pycache__`
- `& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile scripts\r24_forced_behavior_audit.py` with `PYTHONPYCACHEPREFIX=$env:TEMP` -> success
- `PowerShell parse check on scripts/run_r24_behavior_audit_local_cuda.ps1` -> ok

### Concerns
- `py_compile` without directing bytecode cache may fail in this workspace due existing permission/lock issues in `scripts/__pycache__`.

### 2026-07-07 Diagnostic-only fix

Applied the reviewer fix for Task-2 on `scripts/r24_forced_behavior_audit.py`:

- Removed `--enable_assignment_actionability_reward` from `_train_args`.
- Left `--enable_team_intent` and `--enable_assignment_actionability_probe` in place because the probe path and checkpoint structure compatibility rely on loading the same assignment-actionability architecture used for diagnostics.
- No other reward-path flags were kept; this script remains checkpoint-load + forward-eval only.
