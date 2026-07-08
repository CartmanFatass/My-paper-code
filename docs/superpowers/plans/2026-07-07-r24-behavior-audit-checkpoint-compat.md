# R24 Behavior Audit Checkpoint Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the R24 offline forced-behavior audit load existing q_A checkpoints that used `z_assignment_residual_gain` and actionability flags.

**Architecture:** The checkpoint loader must preserve structure-changing q_A fields from either checkpoint payloads or adjacent `metadata/run_manifest.json` files. The offline audit wrapper must point at a real q_A checkpoint path and should fail early with a useful message when the checkpoint is absent.

**Tech Stack:** Python 3.10, PyTorch checkpoint dictionaries, pytest, PowerShell runner.

## Global Constraints

- Diagnostic-only: do not train, inject rewards, or add new reward paths.
- Preserve default training behavior except for richer checkpoint metadata.
- Existing old checkpoints must be loadable through manifest fallback when top-level fields are missing.
- Keep this as a narrow compatibility fix for R24 behavior audit.

---

### Task 1: Checkpoint Metadata Carries q_A Structure

**Files:**
- Modify: `ha_ctse_process/train.py`
- Add: `tests/r24_checkpoint_compat_test.py`

**Interfaces:**
- `load_checkpoint_metadata(path) -> dict[str, Any]` must include:
  - `z_assignment_residual_gain`
  - `enable_assignment_actionability_probe`
  - `enable_assignment_actionability_reward`
  - `assignment_actionability_coef`
  - `assignment_actionability_clip`
  - `assignment_actionability_warmup_steps`
  - `assignment_actionability_include_soft`
- `apply_checkpoint_structure(config, args, metadata)` must restore those fields.
- `checkpoint_payload(...)` must save those fields for future checkpoints.

- [ ] **Step 1: Write failing tests**

Create a test that writes a minimal checkpoint without top-level q_A fields but with adjacent `metadata/run_manifest.json` containing the original args. Assert `load_checkpoint_metadata` recovers the q_A fields and `apply_checkpoint_structure` applies them.

- [ ] **Step 2: Run the focused test and watch it fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_checkpoint_compat_test.py -q
```

Expected: fail before implementation because q_A metadata is missing.

- [ ] **Step 3: Implement checkpoint/manifest metadata fallback**

Update `load_checkpoint_metadata` to read adjacent `metadata/run_manifest.json` when present. Prefer top-level checkpoint keys, then manifest `args`, then manifest `algorithm_config`/`training_config`. Update `apply_checkpoint_structure` and `checkpoint_payload` for q_A fields.

- [ ] **Step 4: Verify**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_checkpoint_compat_test.py tests\r24_behavior_audit_test.py -q
```

Expected: pass.

### Task 2: Behavior Audit Runner Points At A Real Checkpoint

**Files:**
- Modify: `scripts/run_r24_behavior_audit_local_cuda.ps1`

**Interfaces:**
- Default checkpoint path should be `logs_r23_next_mechanism_matrix_local\seed1\arm2_qA_reward_coef002\standalone_process_core_update_40.pt`.
- Runner should fail early if the checkpoint does not exist.

- [ ] **Step 1: Update runner default and validation**
- [ ] **Step 2: Run PowerShell parser check**
- [ ] **Step 3: Run a tiny smoke audit**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" scripts\r24_forced_behavior_audit.py --checkpoint logs_r23_next_mechanism_matrix_local\seed1\arm2_qA_reward_coef002\standalone_process_core_update_40.pt --out_dir logs_r24_behavior_audit_smoke --config ha_ctse_process.config --scenario energy --preset S7-S1 --seed 1 --n_agents 6 --device cuda --horizons 1 --n_resets 1 --max_labels 2
```

Expected: script exits 0 and writes `logs_r24_behavior_audit_smoke\r24_behavior_audit.csv`.
