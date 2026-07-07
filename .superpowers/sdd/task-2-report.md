# R24 Task 2 Report: Offline Forced Behavior Audit Script

## Scope

- Created `scripts/r24_forced_behavior_audit.py`.
- Created `scripts/run_r24_behavior_audit_local_cuda.ps1`.
- Added focused pure-helper tests to `tests/r24_behavior_audit_test.py`.
- No trainer, agent, config, plotting, or memory files were edited.

## Live API Inspection

The required names exist in the live repo:

```text
ha_ctse_process/train.py:
  parse_args
  apply_standalone_overrides
  create_env
  create_agent
  load_checkpoint
  load_checkpoint_metadata
  apply_checkpoint_structure

ha_ctse_process/standalone_agent.py:
  StandaloneProcessAgent._low_actor_forced_skill_outputs
```

No API-name adaptation was required.

## Implementation Notes

- `run_r24_behavior_audit(args: argparse.Namespace) -> dict[str, float]` loads an eval env and checkpoint-compatible agent, calls `load_checkpoint(..., load_optimizers=False)`, sets modules to eval mode, runs paired deterministic reset-seeded rollouts, summarizes `R24AuditRecord` rows, and writes `<out_dir>/r24_behavior_audit.csv`.
- `forced_kind="z"` forces a team code before deterministic high-level assignment, then measures the resulting low-level action features and rollout effects.
- `forced_kind="xi"` directly forces executable skill labels for all agents, then measures low-level action features and rollout effects.
- Discrete/probability action features are converted with `argmax`; continuous features pass through as `float32`.

## Diagnostic-Only Check

- No training loop is added.
- No optimizer update path is called.
- Checkpoint loading uses `load_optimizers=False`.
- No `--enable_*_reward` flag appears in `scripts/r24_forced_behavior_audit.py`.
- The local wrapper also passes no reward-enable flag.

## TDD / Verification

Red check:

```text
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q
```

Expected failure observed before script creation:

```text
ModuleNotFoundError: No module named 'scripts.r24_forced_behavior_audit'
```

Green checks:

```text
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q
14 passed in 0.13s

$env:PYTHONPYCACHEPREFIX=$env:TEMP; & "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile scripts\r24_forced_behavior_audit.py
passed

$errs = $null; $ps = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path scripts\run_r24_behavior_audit_local_cuda.ps1), [ref]$null, [ref]$errs); if($errs.Count){ throw $errs[0] }
passed
```

Reward flag grep:

```text
rg -n -- "--enable_.*_reward" scripts\r24_forced_behavior_audit.py scripts\run_r24_behavior_audit_local_cuda.ps1
```

Result: no matches.

## Concerns

- The checks verify helper behavior, syntax, and wrapper parsing. The full offline audit was not launched against the checkpoint as part of this task brief's verification list.
