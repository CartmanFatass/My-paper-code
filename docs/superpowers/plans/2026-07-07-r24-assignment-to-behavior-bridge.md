# R24 Assignment-to-Behavior Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the R24 diagnostics that test whether the validated `Z -> xi` assignment path produces persistent behavior/effect separation before any q_D/q_d reward is considered.

**Architecture:** R24 has two reward-off gates. First, an offline checkpoint audit forces alternative `Z/xi/z_i` choices on matched states and measures action/effect separation over `H={10,20,50}`. Second, a default-off team-conditioned `q_d` probe tests whether local effect recovers executed individual skill beyond a condition-only prior.

**Tech Stack:** Python 3.10, NumPy, PyTorch, pytest, existing `ha_ctse_process` training/agent utilities, PowerShell runners.

## Global Constraints

- This plan is diagnostics-first and reward-off. Do not add q_D reward, q_d reward, low-only intrinsic reward, high-level intrinsic reward, or coefficient sweeps.
- Do not use raw communication/backhaul fields as intrinsic targets. Communication metrics remain diagnostics/evaluation only.
- Do not change default training behavior. New probes must be default-off unless an explicit CLI/config flag enables them.
- Do not change low-level actor inputs or bypass the skill bottleneck.
- Offline forced-behavior audit scripts may load checkpoints and call diagnostic forced-action helpers, but must not train, update optimizers, inject reward, or enable reward flags.
- During subagent-driven execution, follow current `AGENTS.md` model-tier routing: use `PlanImplementer` (`gpt-5.5`, high reasoning, fast tier) for accepted-plan core implementation; reserve `PlanImplementerFrontier` (`gpt-5.5`, xhigh reasoning, fast tier) for rare bounded implementation tasks that explicitly require architecture or algorithm judgment while editing. Do not use Spark workers for core code implementation/review.
- Preserve unrelated dirty worktree changes. Do not revert `.codex/agents/*`, `memory/*`, or pytest-temp deletions unless explicitly requested.

---

## File Structure

- `ha_ctse_process/r24_behavior_audit.py`: pure NumPy diagnostic helpers for action/effect distances, cluster spread, record summaries, and CSV writing.
- `tests/r24_behavior_audit_test.py`: unit tests for helper math and CSV output.
- `scripts/r24_forced_behavior_audit.py`: offline checkpoint audit entry point; loads model/env, forces labels, writes `r24_behavior_audit.csv`.
- `scripts/run_r24_behavior_audit_local_cuda.ps1`: local wrapper for the offline audit.
- `ha_ctse_process/team_conditioned_qd.py`: reward-off full-vs-prior q_d probe module.
- `tests/r24_team_conditioned_qd_test.py`: unit tests for the q_d probe and config defaults.
- `ha_ctse_process/config.py`: default-off R24 q_d probe config.
- `ha_ctse_process/train.py`: CLI overrides and TensorBoard logging.
- `ha_ctse_process/standalone_agent.py`: default-off q_d probe update from completed process segments.
- `ha_ctse_process/plotting.py`: CSV field registration for `r24_qd_*`.
- `scripts/run_r24_qd_probe_local_cuda.ps1`: local reward-off q_d probe runner.
- `memory/ExpRecord.md`: factual experiment dashboard handoff; no principle rewrite in this plan.

---

### Task 1: Pure R24 Behavior Audit Helpers

**Files:**
- Create: `ha_ctse_process/r24_behavior_audit.py`
- Create: `tests/r24_behavior_audit_test.py`

**Interfaces:**
- Produces:
  - `R24AuditRecord`
  - `action_feature_distance(forced, base) -> float`
  - `action_feature_kl(p, q) -> np.ndarray`
  - `effect_distance(base_start, base_end, forced_start, forced_end) -> float`
  - `between_within_ratio(features, labels) -> float`
  - `summarize_audit_records(records) -> dict[str, float]`
  - `write_audit_csv(path, metrics) -> None`

- [ ] **Step 1: Write failing helper tests**

Create `tests/r24_behavior_audit_test.py` with:

```python
from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process.r24_behavior_audit import (
    R24AuditRecord,
    action_feature_distance,
    action_feature_kl,
    between_within_ratio,
    effect_distance,
    summarize_audit_records,
    write_audit_csv,
)


def test_action_feature_kl_matches_manual_discrete_kl():
    p = np.asarray([[0.75, 0.25], [0.50, 0.50]], dtype=np.float32)
    q = np.asarray([[0.50, 0.50], [0.25, 0.75]], dtype=np.float32)
    out = action_feature_kl(p, q)
    expected = np.sum(p * (np.log(p + 1e-8) - np.log(q + 1e-8)), axis=-1)
    assert np.allclose(out, expected, atol=1e-6)


def test_action_feature_kl_raises_on_shape_mismatch():
    with pytest.raises(ValueError, match="shape mismatch"):
        action_feature_kl(np.asarray([0.75, 0.25]), np.asarray([[0.5, 0.5], [0.5, 0.5]]))


def test_action_feature_distance_uses_kl_for_probability_rows():
    p = np.asarray([[0.75, 0.25]], dtype=np.float32)
    q = np.asarray([[0.50, 0.50]], dtype=np.float32)
    assert np.isclose(action_feature_distance(p, q), float(action_feature_kl(p, q).mean()))


def test_action_feature_distance_uses_euclidean_for_continuous_rows():
    forced = np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    base = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.float32)
    expected = np.mean(np.linalg.norm(forced - base, axis=-1))
    assert np.isclose(action_feature_distance(forced, base), expected)


def test_effect_distance_is_euclidean_delta_distance():
    assert np.isclose(
        effect_distance(
            np.asarray([0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, 0.0], dtype=np.float32),
            np.asarray([0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, 2.0], dtype=np.float32),
        ),
        2.0,
    )


def test_between_within_ratio_detects_cluster_separation():
    features = np.asarray([[0.0, 0.0], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) > 20.0


def test_between_within_ratio_raises_on_row_mismatch():
    with pytest.raises(ValueError, match="row mismatch"):
        between_within_ratio(np.asarray([[0.0], [1.0]], dtype=np.float32), np.asarray([0, 1, 2]))


def test_between_within_ratio_returns_zero_for_tiny_label_support():
    features = np.asarray([[0.0], [1.0], [2.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) == 0.0


def test_summarize_audit_records_reports_horizon_metrics():
    records = [
        R24AuditRecord(horizon=10, forced_kind="z", action_distance=0.2, effect_distance=1.0, label=0),
        R24AuditRecord(horizon=10, forced_kind="z", action_distance=0.4, effect_distance=3.0, label=1),
        R24AuditRecord(horizon=20, forced_kind="xi", action_distance=0.8, effect_distance=5.0, label=1),
    ]
    out = summarize_audit_records(records)
    assert out["r24_audit_records"] == 3.0
    assert out["r24_z_action_distance_h10"] == 0.3
    assert out["r24_z_effect_distance_h10"] == 2.0
    assert out["r24_xi_action_distance_h20"] == 0.8


def test_write_audit_csv_roundtrip(tmp_path: Path):
    metrics = {"r24_audit_records": 2.0, "r24_z_action_distance_h10": 0.25}
    path = tmp_path / "r24_behavior_audit.csv"
    write_audit_csv(path, metrics)
    text = path.read_text(encoding="utf-8")
    assert "r24_audit_records" in text
    assert "0.25" in text
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q
```

Expected: fail because `ha_ctse_process.r24_behavior_audit` does not exist.

- [ ] **Step 3: Implement pure helper module**

Create `ha_ctse_process/r24_behavior_audit.py` with pure NumPy helpers. Required behavior:

```text
action_feature_kl:
  - convert inputs to 2D float64 arrays;
  - require equal shapes, else ValueError("shape mismatch");
  - clip to eps, normalize rows, return row-wise KL.

action_feature_distance:
  - if both arrays are 2D, same shape, nonnegative, and every row sums to 1 within 1e-4, return mean KL;
  - if shapes match but rows are not probability-like, return mean row-wise Euclidean distance;
  - if shapes mismatch, return 0.0.

between_within_ratio:
  - require features rows == labels rows, else ValueError("row mismatch");
  - return 0.0 for <=1 row, <=1 label, or any label group with fewer than 2 samples;
  - otherwise compute between-centroid variance divided by within-cluster variance.

effect_distance:
  - compare forced delta against base delta using Euclidean norm;
  - return 0.0 if flattened delta shapes differ.

summarize_audit_records:
  - emit `r24_audit_records`;
  - for each forced kind and horizon emit action/effect means and label entropy.

write_audit_csv:
  - create parent directory;
  - write one-row CSV with sorted metric keys.
```

- [ ] **Step 4: Run tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add ha_ctse_process/r24_behavior_audit.py tests/r24_behavior_audit_test.py
git commit -m "R24: add behavior audit helpers"
```

---

### Task 2: Offline Forced Behavior Audit Script

**Files:**
- Create: `scripts/r24_forced_behavior_audit.py`
- Create: `scripts/run_r24_behavior_audit_local_cuda.ps1`
- Test: `tests/r24_behavior_audit_test.py`

**Interfaces:**
- Consumes: Task 1 helpers and `StandaloneProcessAgent._low_actor_forced_skill_outputs`.
- Produces: `run_r24_behavior_audit(args: argparse.Namespace) -> dict[str, float]`
- Produces: `<out_dir>/r24_behavior_audit.csv`

- [ ] **Step 1: Inspect current train/agent APIs**

Before writing script code, confirm the following names in the live repo:

```powershell
rg -n "def create_env|def create_agent|def load_checkpoint|def load_checkpoint_metadata|def apply_checkpoint_structure|def apply_standalone_overrides|def parse_args" ha_ctse_process\train.py
rg -n "def _low_actor_forced_skill_outputs" ha_ctse_process\standalone_agent.py
```

Expected: all required functions exist. If a name differs, adapt to the live repo and document it in `.superpowers/sdd/task-2-report.md`.

- [ ] **Step 2: Create script**

Create `scripts/r24_forced_behavior_audit.py`. Requirements:

```text
CLI args:
  --checkpoint, --out_dir, --config, --scenario, --preset, --seed, --n_agents,
  --device, --horizons, --n_resets, --max_labels.

Diagnostic-only:
  - no training loop;
  - no optimizer updates;
  - load_checkpoint(..., load_optimizers=False);
  - do not pass reward-enable CLI flags in the internal train args.

Internal train args:
  include only structural flags needed to instantiate the checkpoint-compatible
  agent, such as `--enable_team_intent` and relevant probe/architecture flags;
  never include `--enable_*_reward`.

Audit behavior:
  - create eval env and agent;
  - load checkpoint;
  - set networks to eval mode where available;
  - for each reset and label, compare forced output against a base label;
  - use Task 1 `action_feature_distance`;
  - for every horizon, run paired deterministic rollouts from the same reset seed
    and compute Task 1 `effect_distance`;
  - append `R24AuditRecord` and write CSV summary.
```

Implementation note: for discrete/probability action features, choose actions via `argmax`; for continuous action features, pass the continuous action array through as `float32`.

- [ ] **Step 3: Create local wrapper**

Create `scripts/run_r24_behavior_audit_local_cuda.ps1` with parameters:

```powershell
param(
    [string]$Checkpoint = "logs_r23_next_mechanism_matrix_local\arm2_qA_reward\standalone_process_core_update_40.pt",
    [string]$OutDir = "logs_r24_behavior_audit_local",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Device = "cuda",
    [int]$Seed = 1,
    [int]$NResets = 16
)
```

The wrapper must call `scripts\r24_forced_behavior_audit.py` with `--horizons 10,20,50` and `--n_agents 6`.

- [ ] **Step 4: Add script-helper tests if helper functions are factored**

If `scripts/r24_forced_behavior_audit.py` factors any pure helper such as `_rollout_action_from_features`, add focused tests in `tests/r24_behavior_audit_test.py`.

- [ ] **Step 5: Run verification**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_behavior_audit_test.py -q
$env:PYTHONPYCACHEPREFIX=$env:TEMP; & "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile scripts\r24_forced_behavior_audit.py
$ps = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path scripts\run_r24_behavior_audit_local_cuda.ps1), [ref]$null, [ref]$errs); if($errs.Count){ throw $errs[0] }
```

Expected: tests pass, compile succeeds, PowerShell parser finds no errors.

- [ ] **Step 6: Commit**

```bash
git add scripts/r24_forced_behavior_audit.py scripts/run_r24_behavior_audit_local_cuda.ps1 tests/r24_behavior_audit_test.py
git commit -m "R24: add offline forced behavior audit"
```

---

### Task 3: Team-Conditioned q_d Probe Module

**Files:**
- Create: `ha_ctse_process/team_conditioned_qd.py`
- Create: `tests/r24_team_conditioned_qd_test.py`

**Interfaces:**
- Produces:
  - `TEAM_CONDITIONED_QD_METRIC_FIELDS`
  - `empty_team_conditioned_qd_metrics() -> dict[str, float]`
  - `TeamConditionedQDConfig.from_config(config)`
  - `TeamConditionedQDProbe.losses(effect, condition, labels) -> dict[str, torch.Tensor]`

- [ ] **Step 1: Write failing tests**

Create tests that verify:

```text
1. full classifier beats condition-only prior when effect carries skill label;
2. full classifier does not strongly beat prior when effect is noise;
3. `effect` and `condition` are detached from policy graph inside losses;
4. metric field names all start with `r24_qd_`;
5. default config is probe-off.
```

Use deterministic seeds for both generated data and model initialization with `torch.manual_seed(...)`.

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py -q
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement module**

Create `ha_ctse_process/team_conditioned_qd.py`:

```text
Metric fields:
  r24_qd_active
  r24_qd_samples
  r24_qd_loss_full
  r24_qd_loss_prior
  r24_qd_acc_full
  r24_qd_acc_prior
  r24_qd_residual_gain
  r24_qd_residual_mean
  r24_qd_positive_frac

Probe:
  q_full(label | effect, condition)
  q_prior(label | condition)
  residual = log q_full(executed label) - log q_prior(executed label)

Detach rule:
  effect = effect.detach().float()
  condition = condition.detach().float()
  labels = labels.detach().long()
```

Use a small `LayerNorm -> Linear -> GELU -> Linear -> GELU -> Linear` MLP.

- [ ] **Step 4: Run tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add ha_ctse_process/team_conditioned_qd.py tests/r24_team_conditioned_qd_test.py
git commit -m "R24: add team-conditioned qd probe"
```

---

### Task 4: Wire q_d Probe Into Training Metrics Default-Off

**Files:**
- Modify: `ha_ctse_process/config.py`
- Modify: `ha_ctse_process/train.py`
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `ha_ctse_process/plotting.py`
- Test: `tests/r24_team_conditioned_qd_test.py`

**Interfaces:**
- Consumes Task 3 q_d module.
- Produces stable `r24_qd_*` fields in `process_metrics`, TensorBoard, and `metrics/train_updates.csv`.

- [ ] **Step 1: Add config defaults**

Add default-off config fields:

```python
enable_team_conditioned_qd_probe = False
team_conditioned_qd_hidden_dim = 128
team_conditioned_qd_lr = 1e-3
team_conditioned_qd_min_samples = 64
```

- [ ] **Step 2: Add CLI and overrides**

Add CLI flags:

```python
--enable_team_conditioned_qd_probe
--team_conditioned_qd_hidden_dim
--team_conditioned_qd_lr
--team_conditioned_qd_min_samples
```

Override config only when flags are explicitly supplied.

- [ ] **Step 3: Add CSV/TensorBoard fields**

Import `TEAM_CONDITIONED_QD_METRIC_FIELDS` in `plotting.py` and include it in `UPDATE_FIELDS`.

In `train.py::log_train_metrics`, write each `r24_qd_*` metric under `R24QD/<key>`.

- [ ] **Step 4: Wire probe in `StandaloneProcessAgent`**

In `standalone_agent.py`:

```text
import TeamConditionedQDConfig, TeamConditionedQDProbe, empty_team_conditioned_qd_metrics.
Initialize cfg/probe/optimizer in __init__.
Add `_r24_qd_segment_tensors(valid_segments)` to build:
  effect = end_obs - high_obs using safe fallbacks;
  condition = generic non-communication features only:
    team code/Z one-hot when present,
    executed skill one-hot or xi summary,
    duration index one-hot,
    normalized age/length scalar,
    optional compact/omega only if already present on Segment and generic.
  labels = executed individual skill.
Add `_team_conditioned_qd_update(valid_segments)`.
Call it in process_update after valid segments are built.
Merge empty metrics in disabled/no-segment paths.
```

Do not use reward/backhaul/coverage/QoS/throughput fields in q_d effect or condition.

- [ ] **Step 5: Add config test**

Append to `tests/r24_team_conditioned_qd_test.py`:

```python
from ha_ctse_process.config import Config
from ha_ctse_process.team_conditioned_qd import TeamConditionedQDConfig


def test_config_defaults_probe_off():
    cfg = TeamConditionedQDConfig.from_config(Config())
    assert cfg.probe_on is False
    assert cfg.hidden_dim == 128
```

- [ ] **Step 6: Run verification**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py tests\r23_assignment_actionability_test.py tests\r23_team_effect_target_test.py -q
$env:PYTHONPYCACHEPREFIX=$env:TEMP; & "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile ha_ctse_process\team_conditioned_qd.py ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py
```

Expected: tests pass and compile succeeds.

- [ ] **Step 7: Commit**

```bash
git add ha_ctse_process/team_conditioned_qd.py ha_ctse_process/config.py ha_ctse_process/train.py ha_ctse_process/standalone_agent.py ha_ctse_process/plotting.py tests/r24_team_conditioned_qd_test.py
git commit -m "R24: wire team-conditioned qd probe"
```

---

### Task 5: Experiment Handoff And Local Runners

**Files:**
- Create: `scripts/run_r24_qd_probe_local_cuda.ps1`
- Modify: `memory/ExpRecord.md`

**Interfaces:**
- Consumes Task 2 offline audit script and Task 4 q_d metrics.
- Produces launch-ready local diagnostic commands only.

- [ ] **Step 1: Create q_d reward-off local runner**

Create `scripts/run_r24_qd_probe_local_cuda.ps1` that launches a short diagnostic run:

```powershell
param(
    [string]$LogRoot = "logs_r24_qd_probe_local_cuda",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [int]$TotalTimesteps = 160000,
    [int]$NumEnvs = 16,
    [int]$Seed = 1
)
```

Required flags:

```text
--enable_team_intent
--z_assignment_residual_gain 1.0
--enable_assignment_actionability_probe
--enable_assignment_actionability_reward
--assignment_actionability_coef 0.05
--enable_team_conditioned_qd_probe
```

Do not enable q_D reward, q_d reward, topology-role reward, transition skill reward, or process reward.

- [ ] **Step 2: Update `memory/ExpRecord.md`**

Update `EXP-20260707-r24-assignment-to-behavior-bridge` with:

```text
Implementation handoff:
- R24-0 behavior audit is offline/checkpoint-based and writes `r24_behavior_audit.csv`.
- R24-1 q_d probe is reward-off and logs `r24_qd_*`.
- Reward-on low-only q_d remains blocked until behavior audit and q_d residual both pass.
```

Add script references:

```text
scripts/r24_forced_behavior_audit.py
scripts/run_r24_behavior_audit_local_cuda.ps1
scripts/run_r24_qd_probe_local_cuda.ps1
```

- [ ] **Step 3: Run dry checks**

Run:

```powershell
$ps = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path scripts\run_r24_qd_probe_local_cuda.ps1), [ref]$null, [ref]$errs); if($errs.Count){ throw $errs[0] }
```

Expected: no parser errors.

- [ ] **Step 4: Commit**

```bash
git add memory/ExpRecord.md scripts/run_r24_qd_probe_local_cuda.ps1
git commit -m "R24: add qd probe runner and experiment handoff"
```

---

## Self-Review

**Spec coverage:** R24-0 forced behavior audit is implemented by Tasks 1-2. R24-1 team-conditioned q_d reward-off probe is implemented by Tasks 3-4. Experiment handoff is Task 5. No reward-on arm is added.

**Placeholder scan:** No task contains TBD/TODO/fill-later language. Where live repo names may differ, tasks require inspection and report the adaptation.

**Type consistency:** Task 1 helper names are consumed by Task 2. Task 3 q_d names are consumed by Task 4. Task 5 uses scripts and metrics from prior tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-r24-assignment-to-behavior-bridge.md`.

Execution mode for this repository is already specified by the user: use subagents. Per `AGENTS.md`, use `PlanImplementer` for code tasks and `ImplementationReviewer` for task/final reviews.
