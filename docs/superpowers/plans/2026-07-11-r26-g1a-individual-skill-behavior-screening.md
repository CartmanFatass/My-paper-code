# R26-G1a Individual-Skill Behavior Screening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reward-off, frozen-checkpoint screening pipeline that tests whether naturally assigned individual HA-CTSE skills `z_i` leave held-out local behavior signatures beyond context/history and matched nulls.

**Architecture:** A frozen-policy collector writes detached fixed-horizon behavior windows without calling any update path. A separate analyzer performs reset-grouped train/validation/test splitting, equal-capacity early-stopped probes, matched null controls, cluster bootstrap confidence intervals, and the pre-registered G1a gate. The training loop, policy, critic, reward composition, checkpoint format, and environment remain unchanged.

**Tech Stack:** Python 3.10, NumPy, PyTorch, pytest, PowerShell 7, existing `ha_ctse_process.train` checkpoint/environment helpers.

## Global Constraints

- Source design: `docs/superpowers/specs/2026-07-11-r26-g1a-individual-skill-behavior-screening-design.md`.
- This plan belongs to the traditional HA-CTSE R24/R25 line in `C:\project\HMASD`; IMOD is an independent workspace.
- G1a is reward-off. Never enable or modify `q_A`, `q_d`, `q_D`, team-discriminator, process, transition, topology, or communication-specific reward paths.
- Do not modify `ha_ctse_process/standalone_agent.py`, `ha_ctse_process/train.py`, policy/critic modules, collector backends, environment dynamics, checkpoint serialization, or shared behavioral config.
- Real collection and analysis require CUDA and must fail instead of silently falling back to CPU. Synthetic unit tests may use CPU.
- Runtime output belongs under `logs/<run-id>/...`; no root-level logs, CSVs, JSON, or temporary files.
- Use the six existing R25 checkpoints only: arm0 and arm2 at update 25, update 30, and final.
- Arm0 is the primary gate substrate. Arm2 is a contrast and cannot rescue arm0 failure.
- A G1a pass authorizes only a separately designed G1b forced-`z_i` intervention. It never authorizes reward.

## Model And Review Routing

| Work package | Classification | Implementer route | Review route |
| --- | --- | --- | --- |
| Dataset, splits, nulls, probe training, bootstrap, gate | Core numerical/data-contract work | `PlanImplementer`, `gpt-5.6-sol`, xhigh | `ImplementationReviewerFrontier`, `gpt-5.6-sol`, max |
| Frozen checkpoint collector and renewal/window semantics | Core collector/behavioral semantics | `PlanImplementer`, `gpt-5.6-sol`, xhigh | `ImplementationReviewerFrontier`, `gpt-5.6-sol`, max |
| Exact single-file PowerShell runner | Trivial mechanical non-core | `SimplePatcher`, `gpt-5.6-luna`, medium | `FastReviewer`, `gpt-5.6-sol`, high |
| Focused tests, dry-run, smoke output collection | Mechanical execution with large output | `TestRunner`, `gpt-5.6-luna`, medium; write a short file report | Controller reads only the report and selected evidence |
| Checkpoint/log inventories or other large read-only mechanical scans | Mechanical large-context extraction | Partition disjoint scopes across `CodebaseScout`, `gpt-5.6-luna`, medium | Controller integrates short reports |
| Medium multi-file non-core integration when Luna scope is insufficient | Bounded non-core integration | `Implementer`, `gpt-5.6-sol`, high | `ImplementationReviewer`, `gpt-5.6-sol`, xhigh |
| Experiment facts and `ExpRecord.md` launch-ready row | Experiment operations | `ExpManager`, `gpt-5.6-sol`, high | Controller interprets; no scientific decision delegated |
| Compact memory synchronization | Memory-only service | `LongTimeMemoryManager`, `gpt-5.6-sol`, high | Controller owns acceptance and user-facing meaning |
| Final whole-branch review | High-risk integration/data contract | none | `ImplementationReviewerFrontier`, `gpt-5.6-sol`, max |

`PlanImplementerFrontier` is not selected: the user-approved spec fixes the architecture and gates, so implementation should execute rather than redesign. If a core task discovers an unresolved architecture decision, it must return `NEEDS_CONTEXT` or `BLOCKED`; the controller decides whether escalation to frontier is justified.

Large-context mechanical work must be split by explicit file/run scope and produce file-based summaries. Do not spend Sol context on raw test logs, checkpoint inventories, dry-run transcripts, or repetitive artifact scans.

The project documentation still contains historical Terra model-family wording.
For this plan, the dispatch brief is binding: `Implementer`, `FastReviewer`,
`ExpManager`, `ResultAnalyst`, `ExternalReviewManager`, and
`LongTimeMemoryManager` route to `gpt-5.6-sol` with high reasoning. If the live
runtime cannot confirm that route, return `BLOCKED`; do not inherit Terra or
silently substitute another model.

---

### Task 1: Dataset, Held-Out Analyzer, Nulls, And Gate

**Owner:** `PlanImplementer` (`gpt-5.6-sol`, xhigh)

**Reviewer:** `ImplementationReviewerFrontier` (`gpt-5.6-sol`, max)

**Files:**

- Create: `ha_ctse_process/r26_g1_dataset.py`
- Create: `scripts/analyze_r26_g1_behavior.py`
- Create: `tests/r26_g1_dataset_test.py`
- Create: `tests/r26_g1_behavior_test.py`

**Interfaces:**

- Consumes: compressed NPZ shards written by Task 2.
- Produces:
  - `G1WindowBatch`
  - `SplitIndices`
  - `window_summary(rows: np.ndarray, feature_dim: int) -> np.ndarray`
  - `build_prior_context(...) -> np.ndarray`
  - `write_g1_window_shard(path: Path, batch: G1WindowBatch) -> None`
  - `read_g1_window_shards(root: Path) -> G1WindowBatch`
  - `grouped_reset_split(batch: G1WindowBatch, seed: int) -> SplitIndices`
  - `G1WindowBatch.take(indices: np.ndarray) -> G1WindowBatch`
  - `variant_batch(batch: G1WindowBatch, variant: str, seed: int) -> tuple[G1WindowBatch, float]`
  - analyzer CLI output `r26_g1_behavior.json` and `r26_g1_behavior.md`.

- [ ] **Step 1: Write failing dataset and leakage tests**

Create `tests/r26_g1_dataset_test.py` with explicit fixtures and these tests:

```python
from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process.r26_g1_dataset import (
    G1WindowBatch,
    build_prior_context,
    grouped_reset_split,
    read_g1_window_shards,
    window_summary,
    write_g1_window_shard,
)


def make_batch(rows: int = 12) -> G1WindowBatch:
    labels = np.arange(rows, dtype=np.int64) % 3
    resets = np.repeat(np.arange(6, dtype=np.int64), 2)
    return G1WindowBatch(
        label=labels,
        post_action=np.arange(rows * 8, dtype=np.float32).reshape(rows, 8),
        post_effect=np.arange(rows * 12, dtype=np.float32).reshape(rows, 12),
        pre_action=np.zeros((rows, 8), dtype=np.float32),
        pre_effect=np.zeros((rows, 12), dtype=np.float32),
        pre_valid=np.ones(rows, dtype=np.float32),
        prior_context=np.arange(rows * 10, dtype=np.float32).reshape(rows, 10),
        reset_id=resets,
        reset_seed=100 + resets,
        episode_id=resets,
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        duration_idx=np.arange(rows, dtype=np.int64) % 4,
        segment_length=np.full(rows, 10, dtype=np.int64),
        checkpoint_id=np.full(rows, "arm0_update25"),
        checkpoint_update=np.full(rows, 25, dtype=np.int64),
    )


def test_round_trip_preserves_every_field(tmp_path: Path):
    batch = make_batch()
    write_g1_window_shard(tmp_path / "reset_000.npz", batch)
    restored = read_g1_window_shards(tmp_path)
    for field in G1WindowBatch.__dataclass_fields__:
        assert np.array_equal(getattr(restored, field), getattr(batch, field))


def test_grouped_split_never_leaks_reset_ids():
    split = grouped_reset_split(make_batch(), seed=26011)
    train = set(split.train_reset_ids.tolist())
    valid = set(split.validation_reset_ids.tolist())
    test = set(split.test_reset_ids.tolist())
    assert train.isdisjoint(valid)
    assert train.isdisjoint(test)
    assert valid.isdisjoint(test)
    assert train | valid | test == set(range(6))


def test_prior_context_has_no_current_focal_skill_argument():
    kwargs = dict(
        focal_agent=1,
        n_agents=3,
        duration_idx=2,
        n_durations=4,
        previous_skill=0,
        n_skills=3,
        previous_age=4,
        team_code=1,
        num_team_codes=2,
        teammate_roster=np.asarray([2, 1, 0], dtype=np.int64),
        assignment_obs=np.asarray([0.1, 0.2], dtype=np.float32),
        omega=np.asarray([0.4, 0.6], dtype=np.float32),
        pre_action=np.asarray([0.0, 1.0], dtype=np.float32),
        pre_effect=np.asarray([1.0, 0.0], dtype=np.float32),
        pre_valid=True,
    )
    context = build_prior_context(**kwargs)
    changed_focal_slot = build_prior_context(
        **{**kwargs, "teammate_roster": np.asarray([2, 0, 0], dtype=np.int64)}
    )
    assert np.isfinite(context).all()
    assert context.ndim == 1
    assert np.array_equal(context, changed_focal_slot)


def test_window_summary_uses_delta_mean_std_and_span():
    rows = np.asarray([[1.0, 2.0], [2.0, 4.0], [4.0, 8.0]], dtype=np.float32)
    summary = window_summary(rows, feature_dim=2)
    assert summary.shape == (8,)
    assert np.allclose(summary[:2], [3.0, 6.0])


def test_writer_rejects_mismatched_row_count(tmp_path: Path):
    batch = make_batch()
    broken = G1WindowBatch(**{**batch.__dict__, "agent_id": np.zeros(3, dtype=np.int64)})
    with pytest.raises(ValueError, match="agent_id"):
        write_g1_window_shard(tmp_path / "broken.npz", broken)
```

- [ ] **Step 2: Run dataset tests and verify RED**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r26_g1_dataset_test.py -q --basetemp tests/.pytest_tmp/r26-g1a-task1-red
```

Expected: import failure for `ha_ctse_process.r26_g1_dataset`.

- [ ] **Step 3: Implement the dataset contract and generic feature builders**

Create `ha_ctse_process/r26_g1_dataset.py` with this public structure:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class G1WindowBatch:
    label: np.ndarray
    post_action: np.ndarray
    post_effect: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: np.ndarray
    prior_context: np.ndarray
    reset_id: np.ndarray
    reset_seed: np.ndarray
    episode_id: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    duration_idx: np.ndarray
    segment_length: np.ndarray
    checkpoint_id: np.ndarray
    checkpoint_update: np.ndarray

    def take(self, indices: np.ndarray) -> "G1WindowBatch":
        idx = np.asarray(indices, dtype=np.int64)
        return G1WindowBatch(
            **{field: np.asarray(getattr(self, field))[idx] for field in FIELDS}
        )


@dataclass(frozen=True)
class SplitIndices:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    train_reset_ids: np.ndarray
    validation_reset_ids: np.ndarray
    test_reset_ids: np.ndarray


FIELDS = tuple(G1WindowBatch.__dataclass_fields__)
FLOAT_FIELDS = (
    "post_action", "post_effect", "pre_action", "pre_effect",
    "pre_valid", "prior_context",
)
INT_FIELDS = (
    "label", "reset_id", "reset_seed", "episode_id", "env_id",
    "agent_id", "duration_idx", "segment_length", "checkpoint_update",
)


def window_summary(rows: np.ndarray, feature_dim: int) -> np.ndarray:
    matrix = np.asarray(rows, dtype=np.float32).reshape(-1, int(feature_dim))
    if matrix.shape[0] == 0:
        return np.zeros(int(feature_dim) * 4, dtype=np.float32)
    delta = matrix[-1] - matrix[0]
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    span = matrix.max(axis=0) - matrix.min(axis=0)
    return np.concatenate([delta, mean, std, span]).astype(np.float32, copy=False)


def one_hot(index: int, size: int) -> np.ndarray:
    values = np.zeros(max(int(size), 1), dtype=np.float32)
    values[int(np.clip(index, 0, values.size - 1))] = 1.0
    return values


def build_prior_context(
    *, focal_agent: int, n_agents: int, duration_idx: int, n_durations: int,
    previous_skill: int, n_skills: int, previous_age: int, team_code: int,
    num_team_codes: int, teammate_roster: np.ndarray,
    assignment_obs: np.ndarray, omega: np.ndarray, pre_action: np.ndarray,
    pre_effect: np.ndarray, pre_valid: bool,
) -> np.ndarray:
    roster = np.asarray(teammate_roster, dtype=np.int64).reshape(-1)
    teammate_parts = [
        one_hot(int(skill), n_skills)
        for agent, skill in enumerate(roster)
        if int(agent) != int(focal_agent)
    ]
    parts = [
        one_hot(focal_agent, n_agents),
        one_hot(duration_idx, n_durations),
        one_hot(previous_skill, n_skills),
        np.asarray([float(previous_age)], dtype=np.float32),
        one_hot(team_code, num_team_codes),
        *teammate_parts,
        np.asarray(assignment_obs, dtype=np.float32).reshape(-1),
        np.asarray(omega, dtype=np.float32).reshape(-1),
        np.asarray(pre_action, dtype=np.float32).reshape(-1),
        np.asarray(pre_effect, dtype=np.float32).reshape(-1),
        np.asarray([float(bool(pre_valid))], dtype=np.float32),
    ]
    result = np.concatenate(parts).astype(np.float32, copy=False)
    if not np.isfinite(result).all():
        raise ValueError("prior_context contains non-finite values")
    return result
```

Complete `_validate`, NPZ read/write, deterministic sampling, and
`grouped_reset_split` with these exact rules:

```python
def grouped_reset_split(batch: G1WindowBatch, seed: int) -> SplitIndices:
    reset_ids = np.unique(batch.reset_id.astype(np.int64))
    if reset_ids.size < 5:
        raise ValueError("at least five reset groups are required")
    shuffled = reset_ids.copy()
    np.random.default_rng(int(seed)).shuffle(shuffled)
    n_test = max(1, int(np.floor(0.2 * shuffled.size)))
    n_valid = max(1, int(np.floor(0.2 * shuffled.size)))
    test_ids = np.sort(shuffled[:n_test])
    valid_ids = np.sort(shuffled[n_test:n_test + n_valid])
    train_ids = np.sort(shuffled[n_test + n_valid:])
    return SplitIndices(
        train=np.flatnonzero(np.isin(batch.reset_id, train_ids)),
        validation=np.flatnonzero(np.isin(batch.reset_id, valid_ids)),
        test=np.flatnonzero(np.isin(batch.reset_id, test_ids)),
        train_reset_ids=train_ids,
        validation_reset_ids=valid_ids,
        test_reset_ids=test_ids,
    )
```

- [ ] **Step 4: Run dataset tests and verify GREEN**

Run the Step 2 command again. Expected: all tests pass.

- [ ] **Step 5: Write failing analyzer/null/early-stop tests**

Create `tests/r26_g1_behavior_test.py` covering:

```python
import numpy as np
import torch

from ha_ctse_process.r26_g1_dataset import G1WindowBatch, grouped_reset_split
from scripts.analyze_r26_g1_behavior import (
    FitConfig,
    cluster_bootstrap_difference,
    fit_classifier,
    gate_checkpoint,
    score_classifier,
    variant_batch,
)


def test_grouped_null_does_not_fallback_for_singletons(g1_batch):
    variant, unchanged = variant_batch(g1_batch, "agent_duration_matched", seed=17)
    groups = np.stack([g1_batch.agent_id, g1_batch.duration_idx], axis=1)
    for group in np.unique(groups, axis=0):
        idx = np.flatnonzero(np.all(groups == group, axis=1))
        if idx.size == 1:
            assert variant.label[idx[0]] == g1_batch.label[idx[0]]
    assert 0.0 <= unchanged <= 1.0


def test_fit_does_not_accept_test_rows(g1_behavior_batch):
    split = grouped_reset_split(g1_behavior_batch, seed=26011)
    fitted = fit_classifier(
        kind="behavior",
        train=g1_behavior_batch.take(split.train),
        validation=g1_behavior_batch.take(split.validation),
        num_skills=3,
        config=FitConfig(max_steps=200, patience=10, hidden_dim=32, lr=3e-3),
        device=torch.device("cpu"),
        seed=19,
    )
    metrics = score_classifier(fitted.model, "behavior", g1_behavior_batch.take(split.test))
    assert metrics.accuracy > 0.70
    assert fitted.best_step < 200


def test_noise_behavior_does_not_clear_gate(g1_noise_batch):
    result = run_synthetic_checkpoint_analysis(g1_noise_batch)
    decision = gate_checkpoint(result)
    assert decision.status != "PASS"


def test_cluster_bootstrap_is_deterministic():
    reset_ids = np.repeat(np.arange(8), 4)
    real = np.linspace(0.2, 0.8, reset_ids.size)
    null = real - 0.1
    first = cluster_bootstrap_difference(real, null, reset_ids, reps=200, seed=7)
    second = cluster_bootstrap_difference(real, null, reset_ids, reps=200, seed=7)
    assert first == second
    assert first.lower > 0.0
```

The test file must define deterministic fixtures `g1_batch`,
`g1_behavior_batch`, `g1_noise_batch`, and helper
`run_synthetic_checkpoint_analysis` locally. Behavior-coded fixtures use a
per-skill action/effect mean plus Gaussian noise; context is independent.

- [ ] **Step 6: Run analyzer tests and verify RED**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r26_g1_behavior_test.py -q --basetemp tests/.pytest_tmp/r26-g1a-task1-analyzer-red
```

Expected: import failure for `scripts.analyze_r26_g1_behavior`.

- [ ] **Step 7: Implement the analyzer with separated fit and score APIs**

Create `scripts/analyze_r26_g1_behavior.py` with:

```python
@dataclass(frozen=True)
class FitConfig:
    max_steps: int = 1000
    patience: int = 20
    hidden_dim: int = 128
    lr: float = 3e-3
    validation_interval: int = 5


@dataclass(frozen=True)
class FitResult:
    model: torch.nn.Module
    best_step: int
    train_loss: float
    validation_loss: float


@dataclass(frozen=True)
class Score:
    accuracy: float
    macro_f1: float
    cross_entropy: float
    true_log_prob: np.ndarray
    correct: np.ndarray


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float
```

Implement three independent classifier kinds with the same hidden width and
depth: `behavior`, `prior`, and `full`. `fit_classifier` accepts only train and
validation batches. `score_classifier` is the only function that accepts test
data. Save the best validation `state_dict` in memory and restore it before
returning. Never inspect test metrics inside `fit_classifier`.

Implement these exact variants:

```python
VARIANTS = (
    "real", "shuffled", "fake_marginal", "agent_matched",
    "duration_matched", "agent_duration_matched", "pre_only",
    "action_only", "effect_only", "context_only",
)
```

`gate_checkpoint` returns `PASS`, `FAIL`, `MIXED`, `UNDERPOWERED`, or `INVALID`
and checks the five numeric conditions in the design. Reports must include all
variant results, unchanged fractions, split identities, early-stop steps,
train/test gaps, bootstrap intervals, and gate reasons.

CLI arguments:

```text
--input_dir --output_dir --num_skills --device
--split_seed 26011 --model_seed 26012 --null_seed 26013
--max_steps 1000 --patience 20 --validation_interval 5
--hidden_dim 128 --lr 0.003 --bootstrap_reps 2000 --bootstrap_seed 26014
```

The CLI must reject `--device cpu` for a real run. Unit tests call functions
directly with a CPU device.

- [ ] **Step 8: Run Task 1 focused tests and verify GREEN**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r26_g1_dataset_test.py tests/r26_g1_behavior_test.py -q --basetemp tests/.pytest_tmp/r26-g1a-task1-green
```

Expected: all Task 1 tests pass with no warnings or runtime files outside the
test-local base directory.

- [ ] **Step 9: Prepare Task 1 report and review package**

Write:

- `.superpowers/sdd/r26-g1a-task-1-report.md`
- `.superpowers/sdd/r26-g1a-task-1-review-package.md`
- `.superpowers/sdd/r26-g1a-task-1.diff`

The report records red/green commands, changed files, API signatures, null
semantics, early-stop evidence, and scope confirmation. Dispatch
`ImplementationReviewerFrontier`; accepted findings follow fix -> re-review.

- [ ] **Step 10: Commit Task 1 after review passes**

```powershell
git add ha_ctse_process/r26_g1_dataset.py scripts/analyze_r26_g1_behavior.py tests/r26_g1_dataset_test.py tests/r26_g1_behavior_test.py
git commit -m "feat: add R26 G1a behavior analyzer"
```

---

### Task 2: Frozen Natural-Policy Window Collector

**Owner:** `PlanImplementer` (`gpt-5.6-sol`, xhigh)

**Reviewer:** `ImplementationReviewerFrontier` (`gpt-5.6-sol`, max)

**Files:**

- Create: `scripts/collect_r26_g1_windows.py`
- Create: `tests/r26_g1_collector_test.py`

**Interfaces:**

- Consumes Task 1 `G1WindowBatch`, `build_prior_context`,
  `window_summary`, and `write_g1_window_shard`.
- Reuses `load_config`, `normalize_scenario`, `load_checkpoint_metadata`,
  `apply_checkpoint_structure`, `create_env`, `create_agent`, and
  `load_checkpoint` from `ha_ctse_process.train`.
- Produces one NPZ shard per reset plus `collector_manifest.json` under the
  assigned output directory.

- [ ] **Step 1: Write failing collector state-machine tests**

Create `tests/r26_g1_collector_test.py` using fake env/agent objects. Tests must
exercise:

```python
def test_new_assignment_opens_exactly_one_pending_window(): ...
def test_same_label_reassignment_still_opens_a_window(): ...
def test_window_finalizes_after_exactly_skill_interval_steps(): ...
def test_episode_end_discards_incomplete_post_window(): ...
def test_collector_does_not_call_update_backward_or_optimizer(): ...
def test_prior_context_excludes_current_focal_label(): ...
def test_collector_rejects_non_cuda_real_run(): ...
```

The fake agent exposes the same fields used by the collector:

```python
active_skills, active_duration_indices, duration_remaining, skill_age,
has_active_skill, active_team_codes, segments, n_agents, n_skills,
num_team_codes, duration_candidates
```

Its `maybe_assign_skills` replaces selected active segment objects at specified
steps, and `act_low` returns deterministic fixture actions.

- [ ] **Step 2: Run collector tests and verify RED**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r26_g1_collector_test.py -q --basetemp tests/.pytest_tmp/r26-g1a-task2-red
```

Expected: import failure for `scripts.collect_r26_g1_windows`.

- [ ] **Step 3: Implement a per-agent pending-window state machine**

Create `scripts/collect_r26_g1_windows.py` with these structures:

```python
@dataclass
class PendingWindow:
    agent_id: int
    label: int
    duration_idx: int
    previous_skill: int
    previous_age: int
    team_code: int
    assignment_obs: np.ndarray
    omega: np.ndarray
    teammate_roster: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: bool
    actions: list[np.ndarray]
    observations: list[np.ndarray]


@dataclass(frozen=True)
class CollectorStats:
    resets: int
    completed_windows: int
    discarded_incomplete: int
    renewal_events: int
```

At each primitive step:

1. Save the current `agent.segments.active[0][i]` object identities.
2. Call `agent.maybe_assign_skills(..., deterministic=False)`.
3. Detect renewals by changed segment object identity. This captures same-label
   reassignments and team-boundary renewals without duplicating expiration
   logic.
4. Open/replace a `PendingWindow` using the new segment's assignment-time
   fields. Replacing a still-incomplete window counts as discarded and is
   reported.
5. Call `agent.act_low(..., deterministic=False)` under `torch.no_grad()`.
6. Execute the environment step and append focal action plus the focal local
   observation transition to every pending window.
7. Finalize a row after exactly `skill_interval` actions and
   `skill_interval + 1` observations.
8. On termination/truncation, discard all incomplete pending windows and write
   one reset shard.

The collector backs up and restores agent runtime state if it is called from a
reused process. It does not call `process_update`, `update_high_from_segments`,
`update_low`, `backward`, or any optimizer.

CLI arguments:

```text
--checkpoint --output_dir --config ha_ctse_process.config
--scenario energy --preset S7-S1 --seed 1 --n_agents 6
--device cuda --skill_interval 10 --n_resets 64 --episode_max_steps 500
--checkpoint_id --checkpoint_update
```

The manifest records checkpoint SHA256, checkpoint metadata, seeds, discarded
windows, feature dimensions, and policy parameter SHA256 before and after
collection. A mismatch is an error.

- [ ] **Step 4: Run collector tests and verify GREEN**

Run the Step 2 command again. Expected: all collector tests pass.

- [ ] **Step 5: Run the checkpoint-load collection smoke**

Expected time: 2-5 minutes on local CUDA for one reset and one checkpoint.

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" scripts/collect_r26_g1_windows.py `
  --checkpoint "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt" `
  --output_dir "logs/r26_g1a_implementation_smoke/arm0_update25/windows" `
  --config ha_ctse_process.config --scenario energy --preset S7-S1 `
  --seed 1 --n_agents 6 --device cuda --skill_interval 10 `
  --n_resets 5 --episode_max_steps 50 `
  --checkpoint_id arm0_update25 --checkpoint_update 25
```

Expected:

- exit code 0;
- at least one shard or an explicit `UNDERPOWERED` collection manifest with the
  exact reason;
- before/after policy SHA256 equal;
- no checkpoint or optimizer output written.

- [ ] **Step 6: Run one-shard analyzer smoke**

Expected time: 2-5 minutes on local CUDA with reduced diagnostic settings.

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" scripts/analyze_r26_g1_behavior.py `
  --input_dir "logs/r26_g1a_implementation_smoke/arm0_update25/windows" `
  --output_dir "logs/r26_g1a_implementation_smoke/arm0_update25/analysis" `
  --num_skills 6 --device cuda --max_steps 20 --patience 2 `
  --validation_interval 2 --bootstrap_reps 20
```

The analyzer catches grouped-split or label-support insufficiency, writes an
`UNDERPOWERED` report, and exits successfully. The smoke verifies the pipeline,
not the scientific gate.

- [ ] **Step 7: Prepare Task 2 report and review package**

Write `.superpowers/sdd/r26-g1a-task-2-report.md`, review package, and prepared
diff. Include state-machine evidence, parameter hash equality, smoke artifacts,
and runtime placement. Dispatch `ImplementationReviewerFrontier`; accepted
findings follow fix -> re-review.

- [ ] **Step 8: Commit Task 2 after review passes**

```powershell
git add scripts/collect_r26_g1_windows.py tests/r26_g1_collector_test.py
git commit -m "feat: collect frozen R26 G1a windows"
```

---

### Task 3: Six-Checkpoint Sequential Runner

**Owner:** `SimplePatcher` (`gpt-5.6-luna`, medium)

**Reviewer:** `FastReviewer` (`gpt-5.6-sol`, high)

**Files:**

- Create: `scripts/run_r26_g1_screening_local_cuda.ps1`

**Interfaces:**

- Consumes Task 1 and Task 2 CLIs.
- Produces per-arm `command.txt`, `runner_status.txt`, `collector_output.log`,
  `analyzer_output.log`, `windows/`, `analysis/`, and a batch status file under
  the chosen run root.

- [ ] **Step 1: Implement the exact mechanical runner**

Use this arm table and no others:

```powershell
$arms = @(
    @{ Name = "arm0_update25"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt"; Update = 25 },
    @{ Name = "arm0_update30"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt"; Update = 30 },
    @{ Name = "arm0_final"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt"; Update = 32 },
    @{ Name = "arm2_update25"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_25.pt"; Update = 25 },
    @{ Name = "arm2_update30"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_30.pt"; Update = 30 },
    @{ Name = "arm2_final"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_final.pt"; Update = 32 }
)
```

Parameters:

```powershell
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs/r26_g1a_screening",
    [string]$Device = "cuda",
    [int]$NResets = 64,
    [switch]$DryRun,
    [switch]$ContinueOnError
)
```

The runner must reject any device other than `cuda`, verify all checkpoints
before the first arm, print the expected artifact paths, run collection then
analysis for each arm, and never include reward flags or invoke
`ha_ctse_process.train`.

- [ ] **Step 2: Run dry-run verification**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/run_r26_g1_screening_local_cuda.ps1 `
  -RunRoot logs/r26_g1a_runner_dryrun -DryRun
```

Expected:

- exactly six collector commands and six analyzer commands;
- every command contains `--device cuda`;
- no command contains `reward`, `train`, `resume`, or `optimizer`;
- no runtime directory is created in dry-run mode.

- [ ] **Step 3: Prepare the small-diff review package**

Write `.superpowers/sdd/r26-g1a-task-3-review-package.md` plus prepared diff.
Dispatch `FastReviewer`; accepted findings follow fix -> re-review.

- [ ] **Step 4: Commit Task 3 after review passes**

```powershell
git add scripts/run_r26_g1_screening_local_cuda.ps1
git commit -m "chore: add R26 G1a screening runner"
```

---

### Task 4: Verification, Experiment Record, Memory Sync, And Final Review

**Owners:** `TestRunner` for execution summary, `ExpManager` for factual
experiment record, `LongTimeMemoryManager` for compact memory, controller for
scientific interpretation and Git.

**Files:**

- Modify: `memory/ExpRecord.md`
- Modify: `memory/CURRENT_WORK.md`
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Create: `.superpowers/sdd/r26-g1a-final-verification.md`
- Create: `.superpowers/sdd/r26-g1a-final-review-package.md`

- [ ] **Step 1: Delegate full verification output to `TestRunner`**

The `TestRunner` brief owns only test execution and
`.superpowers/sdd/r26-g1a-final-verification.md`. It runs:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest `
  tests/r26_g1_dataset_test.py `
  tests/r26_g1_behavior_test.py `
  tests/r26_g1_collector_test.py `
  tests/r24_team_conditioned_qd_test.py `
  tests/r24_qd_frozen_nulls_test.py `
  -q --basetemp tests/.pytest_tmp/r26-g1a-final
```

It also runs `py_compile` on the three new Python files and the PowerShell
dry-run. The report contains command, exit code, pass/fail count, selected
failure excerpts, smoke artifact inventory, and unexpected root-file scan. Raw
output stays in the assigned test-local or run-local directory; chat returns
only the report path and summary.

- [ ] **Step 2: Measure smoke pace before proposing the six-checkpoint run**

Read timestamps from the Task 2 smoke and estimate full wall-clock cost. Do not
launch the six-checkpoint run. The user must receive the estimated CUDA time
before launch.

- [ ] **Step 3: Route launch-ready facts to `ExpManager`**

`ExpManager` adds one dashboard row:

```text
EXP-20260711-r26-g1a-individual-skill-screening
status=launch-ready
stage=R26-G1a reward-off screening
location=local CUDA, six frozen R25 checkpoints
next_read=per-checkpoint gate plus arm0 2-of-3 family gate
decision=no reward; pass authorizes only G1b design
```

The row records measured time, run root, exact checkpoints, command, expected
artifacts, gates, and prohibited actions. `ExpManager` does not decide PASS or
FAIL.

- [ ] **Step 4: Route compact memory synchronization to `LongTimeMemoryManager`**

Update the dual-track correction and R26 status without rewriting history:

- HMASD continues the traditional R24/R25/R26 line.
- IMOD remains separate.
- R26-G1a code is implemented and verified but the scientific experiment is
  not launched.
- `q_A/q_d/q_D` rewards remain blocked/default-off.

- [ ] **Step 5: Run final whole-branch review**

Prepare one diff package covering only R26 implementation and its memory rows.
Dispatch `ImplementationReviewerFrontier`. Required verdicts:

```text
Spec Compliance: PASS
Code Quality: PASS
```

Accepted findings follow fix -> focused verification -> re-review. Rejected or
deferred findings are recorded and not silently implemented.

- [ ] **Step 6: Final controller verification and handoff**

The controller independently checks:

```powershell
git status --short
git diff --check
```

It confirms no user-owned files were reverted or accidentally staged, reports
all subagent ids/status/lifetime decisions, summarizes implementation and
remaining scientific gates, and asks the user separately before launching the
compute-bearing six-checkpoint experiment.

---

## Execution Order And Parallelism

1. Task 1 is first because it fixes the data and analyzer interfaces.
2. Task 2 depends on Task 1 and runs second.
3. Task 3 depends on both CLIs and runs third.
4. Task 4 follows implementation and review.

The implementation tasks are intentionally serial: they share interfaces and a
wrong data contract would invalidate downstream work. Parallelism is reserved
for bounded read-only mechanical work such as checkpoint inventory, test-output
collection, and artifact scans, split across Luna roles with disjoint scopes.

No experiment is launched by this implementation plan.
