# R24 Frozen q_d Null-Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reward-off frozen-window q_d null-probe path that can decide whether R24 failed because `z_i` lacks stable behavior semantics, because the online probe is underpowered, or because pre/history/null shortcuts explain the signal.

**Architecture:** Keep the online `TeamConditionedQDProbe` as the training-time diagnostic, but add an explicit export path for detached q_d window tensors. A separate offline script trains same-capacity probes on frozen windows under real labels and null labels, then writes a gate report. This avoids injecting reward and avoids changing PPO or environment semantics.

**Tech Stack:** Python 3.10, PyTorch, NumPy, pytest, existing HA-CTSE q_d tensors and runner/log layout.

## Global Constraints

- Do not enable `q_d`, `q_D`, team-disc, communication, or low-only intrinsic reward.
- Do not change default behavior unless `--r24_qd_export_windows` is passed.
- Keep `xi_context_i` excluding the focal executed `z_i`.
- Keep all exported q_d tensors detached from policy graphs.
- Store runtime outputs under the run log directory, never in the repository root.
- Treat this as R24 diagnostic infrastructure. It does not prove S7-S1 parity and does not supersede HMASD comparison.
- Reward-on remains blocked unless every-seed gates pass: residual gain `>= 0.05`, positive fraction `>= 0.60`, full-prior accuracy gap `>= 0.05`, null residuals near zero, post-window gain over pre-window when pre is predictive, and matched forced-audit controls pass.

## Experiment Meaning

- **Hypothesis:** R24 failed because the current behavior-window q_d evidence is not robust; a frozen same-capacity null suite can localize whether the failure is no behavioral skill semantics, poor representation, history/selection predictability, or label/null leakage.
- **Mechanism path:** `Z -> xi` is already supported by q_A. This plan tests the next bridge: `xi / z_i -> executed low-level behavior window -> q_d-recoverable individual skill semantics`.
- **Core MARL impact:** reward-off diagnostic only. It touches q_d probe/export infrastructure and offline analysis scripts, but not PPO reward, policy/critic architecture, collector semantics, or environment dynamics.
- **Metrics/gates:** held-out residual gain, positive fraction, full-prior accuracy gap, behavior-prior gap, full-pre gap, pre gain, shuffled/fake/duration/phase/agent null residuals, label entropy/max fraction, train-test gap, per-seed consistency.
- **Decision tree:** if real labels beat all nulls across seeds, consider a tiny low-only q_d reward plan; if behavior-only passes but full adds little, claim individual semantics only; if pre matches full, treat as history confound; if nulls pass, fix leakage/split; if all fail, revisit low-level skill execution/representation.
- **Do not change yet:** no q_d/q_D reward, no q_D redesign, no 960k scale-up, no communication-specific intrinsic reward.
- **Status source:** R24 cloud 64env seed1/seed2 q_d null-control gate failed; GPT web Round 4 continuation accepted this as a mechanism gate fail and recommended frozen same-capacity null probes.

---

## File Structure

- Modify `ha_ctse_process/config.py`: add default-off export config.
- Modify `ha_ctse_process/train.py`: add CLI flags, set export directory under `args.log_dir`, include config in manifest/start logs.
- Modify `ha_ctse_process/standalone_agent.py`: export detached q_d tensors during `_team_conditioned_qd_update()` when enabled.
- Create `ha_ctse_process/r24_qd_dataset.py`: small utilities for writing/reading q_d window `.npz` shards and validating schema.
- Create `scripts/analyze_r24_qd_frozen_nulls.py`: offline frozen same-capacity null-probe trainer and gate reporter.
- Modify `scripts/run_r24_qd_null_control_cloud_64env.sh`: optional environment flag to export windows and optional post-run analysis command.
- Create `tests/r24_qd_frozen_nulls_test.py`: unit tests for dataset schema and offline null behavior.
- Modify `tests/r24_team_conditioned_qd_test.py`: targeted test proving exporter receives detached current/pre tensors and labels.

---

### Task 1: q_d Window Dataset Schema

**Files:**
- Create: `ha_ctse_process/r24_qd_dataset.py`
- Test: `tests/r24_qd_frozen_nulls_test.py`

**Interfaces:**
- Produces: `QDWindowBatch` dataclass with fields:
  - `action: np.ndarray`
  - `effect: np.ndarray`
  - `condition: np.ndarray`
  - `labels: np.ndarray`
  - `pre_action: np.ndarray`
  - `pre_effect: np.ndarray`
  - `pre_valid: np.ndarray`
  - `env_id: np.ndarray`
  - `agent_id: np.ndarray`
  - `duration_idx: np.ndarray`
  - `segment_length: np.ndarray`
  - `total_steps: np.ndarray`
  - `update_idx: np.ndarray`
- Produces: `write_qd_window_shard(path: Path, batch: QDWindowBatch) -> None`
- Produces: `read_qd_window_shards(root: Path) -> QDWindowBatch`
- Produces: `sample_qd_rows(batch: QDWindowBatch, max_rows: int, seed: int) -> QDWindowBatch`

- [ ] **Step 1: Write failing schema round-trip test**

```python
def test_qd_window_dataset_roundtrip(tmp_path):
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch, read_qd_window_shards, write_qd_window_shard

    batch = QDWindowBatch(
        action=np.ones((3, 4), dtype=np.float32),
        effect=np.ones((3, 5), dtype=np.float32) * 2,
        condition=np.ones((3, 6), dtype=np.float32) * 3,
        labels=np.asarray([0, 1, 2], dtype=np.int64),
        pre_action=np.zeros((3, 4), dtype=np.float32),
        pre_effect=np.zeros((3, 5), dtype=np.float32),
        pre_valid=np.asarray([1, 0, 1], dtype=np.float32),
        env_id=np.asarray([0, 0, 1], dtype=np.int64),
        agent_id=np.asarray([0, 1, 0], dtype=np.int64),
        duration_idx=np.asarray([1, 2, 1], dtype=np.int64),
        segment_length=np.asarray([30, 70, 30], dtype=np.int64),
        total_steps=np.asarray([160000, 160000, 320000], dtype=np.int64),
        update_idx=np.asarray([5, 5, 10], dtype=np.int64),
    )
    write_qd_window_shard(tmp_path / "update_000005.npz", batch)

    loaded = read_qd_window_shards(tmp_path)

    assert loaded.action.shape == (3, 4)
    assert loaded.effect.shape == (3, 5)
    assert loaded.condition.shape == (3, 6)
    assert loaded.labels.tolist() == [0, 1, 2]
    assert loaded.pre_valid.tolist() == [1.0, 0.0, 1.0]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_qd_frozen_nulls_test.py::test_qd_window_dataset_roundtrip -q
```

Expected: fail because `ha_ctse_process.r24_qd_dataset` does not exist.

- [ ] **Step 3: Implement dataset module**

Create `ha_ctse_process/r24_qd_dataset.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class QDWindowBatch:
    action: np.ndarray
    effect: np.ndarray
    condition: np.ndarray
    labels: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    duration_idx: np.ndarray
    segment_length: np.ndarray
    total_steps: np.ndarray
    update_idx: np.ndarray


FIELDS = tuple(QDWindowBatch.__dataclass_fields__.keys())


def _as_array(value, dtype):
    return np.asarray(value, dtype=dtype)


def _validate(batch: QDWindowBatch) -> QDWindowBatch:
    n = int(np.asarray(batch.labels).reshape(-1).shape[0])
    arrays = {field: np.asarray(getattr(batch, field)) for field in FIELDS}
    for field, array in arrays.items():
        if array.shape[0] != n:
            raise ValueError(f"{field} has {array.shape[0]} rows, expected {n}")
    return QDWindowBatch(
        action=_as_array(batch.action, np.float32),
        effect=_as_array(batch.effect, np.float32),
        condition=_as_array(batch.condition, np.float32),
        labels=_as_array(batch.labels, np.int64).reshape(-1),
        pre_action=_as_array(batch.pre_action, np.float32),
        pre_effect=_as_array(batch.pre_effect, np.float32),
        pre_valid=_as_array(batch.pre_valid, np.float32).reshape(-1),
        env_id=_as_array(batch.env_id, np.int64).reshape(-1),
        agent_id=_as_array(batch.agent_id, np.int64).reshape(-1),
        duration_idx=_as_array(batch.duration_idx, np.int64).reshape(-1),
        segment_length=_as_array(batch.segment_length, np.int64).reshape(-1),
        total_steps=_as_array(batch.total_steps, np.int64).reshape(-1),
        update_idx=_as_array(batch.update_idx, np.int64).reshape(-1),
    )


def write_qd_window_shard(path: Path, batch: QDWindowBatch) -> None:
    batch = _validate(batch)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **{field: getattr(batch, field) for field in FIELDS})


def read_qd_window_shards(root: Path) -> QDWindowBatch:
    root = Path(root)
    paths = sorted(root.glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no q_d window shards found under {root}")
    chunks = {field: [] for field in FIELDS}
    for path in paths:
        with np.load(path) as data:
            missing = [field for field in FIELDS if field not in data]
            if missing:
                raise ValueError(f"{path} missing fields: {missing}")
            for field in FIELDS:
                chunks[field].append(np.asarray(data[field]))
    return _validate(QDWindowBatch(**{field: np.concatenate(chunks[field], axis=0) for field in FIELDS}))


def sample_qd_rows(batch: QDWindowBatch, max_rows: int, seed: int) -> QDWindowBatch:
    batch = _validate(batch)
    n = int(batch.labels.shape[0])
    if max_rows <= 0 or n <= max_rows:
        return batch
    rng = np.random.default_rng(int(seed))
    idx = np.sort(rng.choice(n, size=int(max_rows), replace=False))
    return QDWindowBatch(**{field: getattr(batch, field)[idx] for field in FIELDS})
```

- [ ] **Step 4: Run round-trip test**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_qd_frozen_nulls_test.py::test_qd_window_dataset_roundtrip -q
```

Expected: pass.

---

### Task 2: Training-Time Window Export

**Files:**
- Modify: `ha_ctse_process/config.py`
- Modify: `ha_ctse_process/train.py`
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `tests/r24_team_conditioned_qd_test.py`

**Interfaces:**
- Consumes: `QDWindowBatch`, `sample_qd_rows`, `write_qd_window_shard`
- Produces config/CLI:
  - `r24_qd_export_windows = False`
  - `r24_qd_export_dir = ""`
  - `r24_qd_export_max_rows_per_update = 4096`
  - `r24_qd_export_seed = 17`
  - CLI `--r24_qd_export_windows`
  - CLI `--r24_qd_export_dir`
  - CLI `--r24_qd_export_max_rows_per_update`
- Produces shards under `<log_dir>/r24_qd_windows/update_000010_steps_320000.npz` unless a custom export dir is supplied.

- [ ] **Step 1: Write failing export test**

Add to `tests/r24_team_conditioned_qd_test.py`:

```python
def test_standalone_qd_export_writes_detached_window_shard(tmp_path):
    agent = _make_probe_agent()
    agent.r24_qd_export_windows = True
    agent.r24_qd_export_dir = tmp_path
    agent.r24_qd_export_max_rows_per_update = 8
    agent.r24_qd_export_seed = 3

    metrics = agent._team_conditioned_qd_update([_segment_for_qd(1), _segment_for_qd(2)], total_steps=320000, update_idx=10)

    shards = sorted(tmp_path.glob("*.npz"))
    assert metrics["r24_qd_samples"] == 2.0
    assert len(shards) == 1
    with np.load(shards[0]) as data:
        assert data["action"].shape[0] == 2
        assert data["effect"].shape[0] == 2
        assert data["condition"].shape[0] == 2
        assert data["labels"].tolist() == [1, 2]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py::test_standalone_qd_export_writes_detached_window_shard -q
```

Expected: fail because `_team_conditioned_qd_update()` does not accept export metadata and no exporter exists.

- [ ] **Step 3: Add config and CLI flags**

In `ha_ctse_process/config.py`, add defaults:

```python
r24_qd_export_windows = False
r24_qd_export_dir = ""
r24_qd_export_max_rows_per_update = 4096
r24_qd_export_seed = 17
```

In `ha_ctse_process/train.py`, add parser flags:

```python
parser.add_argument("--r24_qd_export_windows", action="store_true")
parser.add_argument("--r24_qd_export_dir", default="")
parser.add_argument("--r24_qd_export_max_rows_per_update", type=int, default=None)
parser.add_argument("--r24_qd_export_seed", type=int, default=None)
```

When applying args:

```python
if args.r24_qd_export_windows:
    config.r24_qd_export_windows = True
if args.r24_qd_export_dir:
    config.r24_qd_export_dir = args.r24_qd_export_dir
if args.r24_qd_export_max_rows_per_update is not None:
    config.r24_qd_export_max_rows_per_update = int(args.r24_qd_export_max_rows_per_update)
if args.r24_qd_export_seed is not None:
    config.r24_qd_export_seed = int(args.r24_qd_export_seed)
if config.r24_qd_export_windows and not config.r24_qd_export_dir:
    config.r24_qd_export_dir = str(Path(args.log_dir) / "r24_qd_windows")
```

- [ ] **Step 4: Export in `_team_conditioned_qd_update()`**

Change signature:

```python
def _team_conditioned_qd_update(
    self,
    valid_segments: list[Segment],
    total_steps: int = 0,
    update_idx: int = 0,
) -> dict[str, float]:
```

Before optimizer update, if export is enabled, build `QDWindowBatch` from detached CPU tensors and segment metadata, sample rows with `sample_qd_rows`, and write one shard per update:

```python
path = self.r24_qd_export_dir / f"update_{int(update_idx):06d}_steps_{int(total_steps):012d}.npz"
write_qd_window_shard(path, sampled_batch)
metrics["r24_qd_export_rows"] = float(sampled_batch.labels.shape[0])
```

Add `r24_qd_export_rows` to metric fields if this metric is logged.

- [ ] **Step 5: Pass update metadata from `process_update()`**

At the call site, use the current standalone update index if available, otherwise infer from total steps:

```python
team_conditioned_qd_metrics = self._team_conditioned_qd_update(
    valid,
    total_steps=total_steps,
    update_idx=int(self.update_count),
)
```

Use the existing update counter name in `StandaloneProcessAgent`; if no stable counter exists, pass `0` and rely on `total_steps` for uniqueness.

- [ ] **Step 6: Run export test**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py::test_standalone_qd_export_writes_detached_window_shard -q
```

Expected: pass.

---

### Task 3: Offline Same-Capacity Null-Probe Script

**Files:**
- Create: `scripts/analyze_r24_qd_frozen_nulls.py`
- Test: `tests/r24_qd_frozen_nulls_test.py`

**Interfaces:**
- Consumes q_d window shards from `ha_ctse_process.r24_qd_dataset.read_qd_window_shards`.
- Consumes `TeamConditionedQDProbe`.
- Produces JSON and Markdown:
  - `r24_qd_frozen_nulls.json`
  - `r24_qd_frozen_nulls.md`

- [ ] **Step 1: Write failing synthetic null test**

Add:

```python
def test_frozen_null_analyzer_real_labels_beat_shuffled_on_synthetic_data(tmp_path):
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch, write_qd_window_shard
    from scripts.analyze_r24_qd_frozen_nulls import run_frozen_null_analysis

    rng = np.random.default_rng(123)
    labels = np.repeat(np.arange(4, dtype=np.int64), 64)
    action_means = rng.normal(size=(4, 6)).astype(np.float32)
    effect_means = rng.normal(size=(4, 8)).astype(np.float32)
    action = action_means[labels] + 0.1 * rng.normal(size=(labels.size, 6)).astype(np.float32)
    effect = effect_means[labels] + 0.1 * rng.normal(size=(labels.size, 8)).astype(np.float32)
    condition = rng.normal(size=(labels.size, 5)).astype(np.float32)
    batch = QDWindowBatch(
        action=action,
        effect=effect,
        condition=condition,
        labels=labels,
        pre_action=rng.normal(size=(labels.size, 6)).astype(np.float32),
        pre_effect=rng.normal(size=(labels.size, 8)).astype(np.float32),
        pre_valid=np.ones(labels.size, dtype=np.float32),
        env_id=np.zeros(labels.size, dtype=np.int64),
        agent_id=np.zeros(labels.size, dtype=np.int64),
        duration_idx=np.zeros(labels.size, dtype=np.int64),
        segment_length=np.ones(labels.size, dtype=np.int64),
        total_steps=np.ones(labels.size, dtype=np.int64),
        update_idx=np.ones(labels.size, dtype=np.int64),
    )
    write_qd_window_shard(tmp_path / "update_000001.npz", batch)

    result = run_frozen_null_analysis(tmp_path, tmp_path, num_skills=4, steps=80, seed=7)

    assert result["real"]["residual_gain"] > result["shuffled"]["residual_gain"] + 0.20
    assert (tmp_path / "r24_qd_frozen_nulls.json").exists()
    assert (tmp_path / "r24_qd_frozen_nulls.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_qd_frozen_nulls_test.py::test_frozen_null_analyzer_real_labels_beat_shuffled_on_synthetic_data -q
```

Expected: fail because script does not exist.

- [ ] **Step 3: Implement analyzer variants**

`scripts/analyze_r24_qd_frozen_nulls.py` must implement:

```text
real:
  train/eval on true labels
shuffled:
  labels permuted after stratifying by seed-stable RNG
fake_marginal:
  labels sampled from observed marginal distribution
duration_matched:
  labels shuffled within duration_idx bucket
agent_matched:
  labels shuffled within agent_id bucket
behavior_only:
  read q_behavior vs majority/prior behavior
pre_only:
  train/eval q_pre on pre windows
action_only:
  zero effect stream
effect_only:
  zero action stream
```

The function `run_frozen_null_analysis(input_dir: Path, output_dir: Path, *, num_skills: int, steps: int, seed: int) -> dict[str, dict[str, float]]` must:

1. read shards;
2. split by `env_id` if at least two envs exist, otherwise deterministic row split;
3. train one `TeamConditionedQDProbe` per variant with the same hidden size and steps;
4. evaluate on held-out rows;
5. write JSON and Markdown gate table.

- [ ] **Step 4: Add CLI**

CLI:

```text
python scripts/analyze_r24_qd_frozen_nulls.py \
  --input_dir <log_dir>/r24_qd_windows \
  --output_dir <log_dir>/r24_qd_frozen_nulls \
  --num_skills 6 \
  --steps 300 \
  --seed 17
```

Arguments:

```python
--input_dir
--output_dir
--num_skills
--hidden_dim
--steps
--lr
--seed
--max_rows
```

- [ ] **Step 5: Run synthetic analyzer test**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_qd_frozen_nulls_test.py -q
```

Expected: pass.

---

### Task 4: Runner Wiring And Experiment Record

**Files:**
- Modify: `scripts/run_r24_qd_null_control_cloud_64env.sh`
- Modify: `memory/ExpRecord.md` through ExpManager only

**Interfaces:**
- Consumes new CLI:
  - `EXPORT_QD_WINDOWS=1`
  - `QD_EXPORT_MAX_ROWS=4096`
  - `RUN_FROZEN_NULL_ANALYSIS=1`
- Produces per-seed:
  - `<log_dir>/r24_qd_windows/*.npz`
  - `<log_dir>/r24_qd_frozen_nulls/r24_qd_frozen_nulls.json`
  - `<log_dir>/r24_qd_frozen_nulls/r24_qd_frozen_nulls.md`

- [ ] **Step 1: Update cloud runner flags**

In `scripts/run_r24_qd_null_control_cloud_64env.sh`, add defaults:

```bash
EXPORT_QD_WINDOWS="${EXPORT_QD_WINDOWS:-0}"
QD_EXPORT_MAX_ROWS="${QD_EXPORT_MAX_ROWS:-4096}"
RUN_FROZEN_NULL_ANALYSIS="${RUN_FROZEN_NULL_ANALYSIS:-0}"
```

When `EXPORT_QD_WINDOWS=1`, append to command:

```bash
--r24_qd_export_windows
--r24_qd_export_max_rows_per_update "$QD_EXPORT_MAX_ROWS"
```

After the Python training command succeeds, when `RUN_FROZEN_NULL_ANALYSIS=1`, run:

```bash
"$PYTHON_BIN" scripts/analyze_r24_qd_frozen_nulls.py \
  --input_dir "$log_dir/r24_qd_windows" \
  --output_dir "$log_dir/r24_qd_frozen_nulls" \
  --num_skills 6 \
  --steps 300 \
  --seed "$seed"
```

- [ ] **Step 2: Dry-run check**

Run:

```bash
EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh --dry-run
```

Expected: printed command includes `--r24_qd_export_windows` and `--r24_qd_export_max_rows_per_update`.

- [ ] **Step 3: Ask ExpManager to update factual experiment row**

ExpManager update should record:

```text
Experiment: EXP-20260708-r24-frozen-qd-null-probes
Purpose: frozen same-capacity q_d null controls after cloud q_d gate fail
Location: local smoke first, then cloud if smoke passes
Core MARL impact: reward-off diagnostic; no reward path
Artifacts to read: r24_qd_windows shards and r24_qd_frozen_nulls reports
```

---

### Task 5: Verification And Review

**Files:**
- All files touched by Tasks 1-4.

- [ ] **Step 1: Run focused q_d tests**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py tests\r24_qd_frozen_nulls_test.py -q
```

Expected: all pass.

- [ ] **Step 2: Run compile check**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile `
  ha_ctse_process\r24_qd_dataset.py `
  ha_ctse_process\team_conditioned_qd.py `
  ha_ctse_process\standalone_agent.py `
  ha_ctse_process\train.py `
  scripts\analyze_r24_qd_frozen_nulls.py
```

Expected: no output and exit code 0.

- [ ] **Step 3: Tiny smoke export**

Run a short local CPU smoke with `--enable_team_conditioned_qd_probe --r24_qd_export_windows --total_timesteps 1024 --num_envs 2 --rollout_length 64 --disable_eval`.

Expected:

```text
<log_dir>/r24_qd_windows/*.npz exists
scripts/analyze_r24_qd_frozen_nulls.py can read it and write json/md
```

- [ ] **Step 4: Prepare review package**

Create `.superpowers/sdd/review-package-r24-frozen-qd-null-probes.md` with:

```text
Goal: review reward-off q_d frozen-window export and offline null probes.
Risk: core diagnostic infrastructure, no reward path.
Changed files.
Diff summary.
Tests run.
Questions:
  - Are exported tensors detached and schema-stable?
  - Does default-off behavior remain unchanged?
  - Could the analyzer accidentally train on labels leaked through condition?
  - Are runtime outputs under log_dir only?
```

Use `ImplementationReviewer` for this task review. Use `ImplementationReviewerFrontier` only if review raises architecture/data-contract concerns that affect reward gating.

---

## Self-Review

Spec coverage:

- GPT's main request for separate same-capacity null probes is covered by Task 3.
- Current lack of raw frozen windows is covered by Task 2.
- No reward injection is preserved by the global constraints and task scopes.
- Runtime-output and ExpManager ownership are explicit in Task 4.

Placeholder scan:

- No placeholder markers or "repeat the previous task" shortcuts are used as implementation instructions.

Type consistency:

- `QDWindowBatch` fields are named once and reused by writer/reader/export/analyzer.
- Export shards use `.npz`; analyzer input and runner output refer to the same `r24_qd_windows` directory.

## Execution Handoff

Recommended execution path for this repository:

1. Keep Task 1-3 controller-owned or assign them as one bounded `PlanImplementer` package only after the controller confirms the work package. These tasks touch core q_d diagnostic plumbing and should not go to `SparkImplementer`.
2. Task 4 runner wiring is non-core mechanical after Tasks 1-3 pass, so it may go to `SparkImplementer` or ExpManager depending on whether it is code edit or experiment-record work.
3. Task 5 review package and verification are controller-owned, with reviewer dispatch after focused tests pass.
