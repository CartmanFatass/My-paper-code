# R27-G1 Low-Actor Capacity Autopsy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a frozen, reward-off CUDA audit that classifies whether the existing strict-HMASD MAPPO low actor has usable individual-skill control capacity, loses that capacity through recurrent carryover, or was missed by the R26 behavior-window instrument.

**Architecture:** Keep every diagnostic outside the live actor and training loop. A focused library owns immutable snapshot data, detached actor-distribution inspection, reset-cluster statistics, synthetic active/sham fitting, and classification; one CLI reconstructs named checkpoints and writes evidence; one PowerShell runner executes the exact three-checkpoint batch and final synthetic control sequentially.

**Tech Stack:** Python 3.10, PyTorch, NumPy, pytest, PowerShell 7/Windows PowerShell, existing `ha_ctse_process.train` checkpoint APIs, and the existing strict-HMASD MAPPO low actor.

## Global Constraints

- Scientific device is CUDA only; a requested or effective CPU device must fail explicitly. Never silently fall back to CPU.
- Scientific run uses exactly R25 arm0 update25, update30, and final; arm2 cannot enter the batch or rescue its classification.
- Collection uses `NResets=64`, fixed reset seeds, `torch.no_grad()`, evaluation mode, and `load_optimizers=False`.
- No environment reward, communication field, coverage, throughput, QoS, backhaul, topology label, recovery flag, q_A, q_d, q_D, PPO continuation, or intrinsic reward may enter an input, loss, gate, or command.
- Do not modify `StrictHMASDMAPPOLowLevelPolicy`, the live actor, training loop, reward composition, collector semantics, environment dynamics, optimizer/checkpoint schema, or source checkpoints.
- Static thresholds are fixed before data: symmetric KL `>= 0.02` nats, standardized mean distance `>= 0.20`, active-minus-inactive reset-bootstrap 95% lower bound `> 0`, and recurrent retention `< 0.50` for washout.
- Synthetic contract is fixed before data: codebook norm `0.5`; Adam `3e-4`; batch `256`; maximum `1000` steps; validation every `25`; patience `20`; minimum improvement `1e-4`; seeds `17,23,41`.
- Synthetic seed gates are fixed: active accuracy and macro-F1 `>= 0.90`; active-minus-sham accuracy `>= 0.50`; reset-bootstrap lower bound `> 0`; sham accuracy `<= 0.35`; train-minus-test accuracy `<= 0.20`.
- Family decisions use two-of-three agreement. Checkpoints are temporal stability snapshots, not independent seeds.
- Every command that writes output must use the assigned timestamped run root. Tests use `tests/.pytest_tmp/r27-g1`; no root-level scratch files.
- Expected scientific runtime is `2.5-3.5 hours` on the local RTX 4070 Laptop GPU. Unit and dry-run verification should finish in under 15 minutes and may use CPU fixtures.

---

## File Map And Ownership

| File | Responsibility | Core status |
|---|---|---|
| `ha_ctse_process/low_actor_capacity_audit.py` | Immutable snapshot schema, shard I/O, grouped split, detached actor forward, static metrics, synthetic clone fitting, bootstrap, gates, and final classification | Core numerical diagnostic; main controller or `SolPlanImplementer` only |
| `scripts/audit_r27_low_actor_capacity.py` | Checkpoint reconstruction, natural-renewal snapshot collection, subcommands, JSON/Markdown reports, and aggregation | Quality-critical experiment interface; main controller or `SolPlanImplementer` |
| `scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1` | Exact sequential three-checkpoint batch, final synthetic phase, aggregation, status/log files, and dry-run | Non-algorithmic runner; may be implemented separately only after CLI contract is fixed |
| `tests/r27_low_actor_capacity_audit_test.py` | Pure numerical, parity, split, synthetic, and classification tests | Same owner as core library |
| `tests/r27_low_actor_capacity_cli_test.py` | Collector immutability, no-grad, report contract, device rejection, and runner dry-run tests | Verification boundary |
| `memory/ExpRecord.md` | Pre-launch factual experiment row and exact command/artifact contract | `TerraExpManager` after implementation verification; not edited by code implementer |

The tasks are sequential because Tasks 1-3 extend the same core module and Task 4 consumes its final API. Task 5 can be reviewed independently after the CLI is stable.

---

### Task 1: Immutable Snapshot Data And Reset-Cluster Statistics

**Files:**
- Create: `ha_ctse_process/low_actor_capacity_audit.py`
- Create: `tests/r27_low_actor_capacity_audit_test.py`

**Interfaces:**
- Consumes: NumPy arrays collected at natural individual-skill renewals.
- Produces: `CapacitySnapshotBatch`, `ResetSplit`, `BootstrapInterval`, `write_capacity_snapshot_shard`, `read_capacity_snapshot_shards`, `grouped_reset_split`, and `cluster_bootstrap_difference`.

- [ ] **Step 1: Write failing snapshot-contract tests**

Create the test file with this fixture and the first tests:

```python
from __future__ import annotations

import numpy as np
import pytest
import torch

from ha_ctse_process.low_actor_capacity_audit import (
    CapacitySnapshotBatch,
    cluster_bootstrap_difference,
    grouped_reset_split,
    read_capacity_snapshot_shards,
    write_capacity_snapshot_shard,
)


def make_snapshots(*, resets: int = 10, rows_per_reset: int = 4) -> CapacitySnapshotBatch:
    reset_id = np.repeat(np.arange(resets, dtype=np.int64), rows_per_reset)
    rows = int(reset_id.size)
    return CapacitySnapshotBatch(
        observation=np.arange(rows * 6, dtype=np.float32).reshape(rows, 6) / 10.0,
        actor_hidden=np.arange(rows * 8, dtype=np.float32).reshape(rows, 8) / 20.0,
        natural_skill=np.arange(rows, dtype=np.int64) % 4,
        previous_skill=(np.arange(rows, dtype=np.int64) + 1) % 4,
        duration_idx=np.arange(rows, dtype=np.int64) % 4,
        skill_age=np.arange(rows, dtype=np.int64) % 9,
        episode_done_mask=np.zeros(rows, dtype=np.bool_),
        reset_id=reset_id,
        reset_seed=27000 + reset_id,
        episode_id=reset_id.copy(),
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        checkpoint_id=np.full(rows, "arm0_final"),
        checkpoint_update=np.full(rows, 32, dtype=np.int64),
    )


def test_snapshot_shard_roundtrip_preserves_every_field(tmp_path):
    expected = make_snapshots()
    write_capacity_snapshot_shard(tmp_path / "reset_0000.npz", expected)
    actual = read_capacity_snapshot_shards(tmp_path)
    for field in CapacitySnapshotBatch.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(actual, field), getattr(expected, field))


def test_grouped_split_is_deterministic_and_never_leaks_resets():
    batch = make_snapshots(resets=10)
    first = grouped_reset_split(batch.reset_id, seed=27011)
    second = grouped_reset_split(batch.reset_id, seed=27011)
    for field in ("train", "validation", "test"):
        np.testing.assert_array_equal(getattr(first, field), getattr(second, field))
    assert first.train_reset_ids == second.train_reset_ids
    assert first.validation_reset_ids == second.validation_reset_ids
    assert first.test_reset_ids == second.test_reset_ids
    assert set(first.train_reset_ids).isdisjoint(first.validation_reset_ids)
    assert set(first.train_reset_ids).isdisjoint(first.test_reset_ids)
    assert set(first.validation_reset_ids).isdisjoint(first.test_reset_ids)
    assert len(first.train_reset_ids) == 6
    assert len(first.validation_reset_ids) == 2
    assert len(first.test_reset_ids) == 2


def test_reset_cluster_bootstrap_is_deterministic_and_positive():
    reset_ids = np.repeat(np.arange(8, dtype=np.int64), 4)
    active = np.linspace(0.2, 0.8, reset_ids.size)
    inactive = active - 0.1
    first = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )
    second = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )
    assert first == second
    assert first.lower > 0.0


def test_snapshot_rejects_nonfinite_hidden_state(tmp_path):
    batch = make_snapshots()
    batch.actor_hidden[3, 2] = np.nan
    with pytest.raises(ValueError, match="actor_hidden contains non-finite"):
        write_capacity_snapshot_shard(tmp_path / "bad.npz", batch)
```

- [ ] **Step 2: Run the tests and verify the module is absent**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task1
```

Expected: collection fails with `ModuleNotFoundError: No module named 'ha_ctse_process.low_actor_capacity_audit'`.

- [ ] **Step 3: Implement the immutable schema, validation, shard I/O, split, and bootstrap**

Start `ha_ctse_process/low_actor_capacity_audit.py` with these declarations and exact public signatures:

```python
"""Frozen low-actor capacity diagnostics for R27-G1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CapacitySnapshotBatch:
    observation: np.ndarray
    actor_hidden: np.ndarray
    natural_skill: np.ndarray
    previous_skill: np.ndarray
    duration_idx: np.ndarray
    skill_age: np.ndarray
    episode_done_mask: np.ndarray
    reset_id: np.ndarray
    reset_seed: np.ndarray
    episode_id: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    checkpoint_id: np.ndarray
    checkpoint_update: np.ndarray

    def take(self, indices: np.ndarray) -> "CapacitySnapshotBatch":
        idx = np.asarray(indices, dtype=np.int64)
        return CapacitySnapshotBatch(
            **{
                field: np.asarray(getattr(self, field))[idx]
                for field in self.__dataclass_fields__
            }
        )


@dataclass(frozen=True)
class ResetSplit:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    train_reset_ids: tuple[int, ...]
    validation_reset_ids: tuple[int, ...]
    test_reset_ids: tuple[int, ...]


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float


FLOAT_FIELDS = ("observation", "actor_hidden")
INT_FIELDS = (
    "natural_skill", "previous_skill", "duration_idx", "skill_age",
    "reset_id", "reset_seed", "episode_id", "env_id", "agent_id",
    "checkpoint_update",
)


def validate_capacity_snapshots(batch: CapacitySnapshotBatch) -> CapacitySnapshotBatch:
    arrays = {
        field: np.asarray(getattr(batch, field))
        for field in CapacitySnapshotBatch.__dataclass_fields__
    }
    rows = int(arrays["natural_skill"].reshape(-1).size)
    for field, values in arrays.items():
        if values.ndim == 0 or int(values.shape[0]) != rows:
            raise ValueError(f"{field} must have {rows} rows")
    for field in FLOAT_FIELDS:
        if not np.isfinite(arrays[field]).all():
            raise ValueError(f"{field} contains non-finite values")
    if arrays["observation"].ndim != 2 or arrays["actor_hidden"].ndim != 2:
        raise ValueError("observation and actor_hidden must be rank-2")
    values: dict[str, np.ndarray] = {}
    for field, array in arrays.items():
        if field in FLOAT_FIELDS:
            values[field] = np.asarray(array, dtype=np.float32)
        elif field in INT_FIELDS:
            values[field] = np.asarray(array, dtype=np.int64).reshape(-1)
        elif field == "episode_done_mask":
            values[field] = np.asarray(array, dtype=np.bool_).reshape(-1)
        else:
            values[field] = np.asarray(array, dtype=np.str_).reshape(-1)
    return CapacitySnapshotBatch(**values)


def write_capacity_snapshot_shard(path: Path, batch: CapacitySnapshotBatch) -> None:
    validated = validate_capacity_snapshots(batch)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        **{
            field: getattr(validated, field)
            for field in CapacitySnapshotBatch.__dataclass_fields__
        },
    )


def read_capacity_snapshot_shards(root: Path) -> CapacitySnapshotBatch:
    paths = sorted(Path(root).glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no capacity snapshot shards under {root}")
    fields = tuple(CapacitySnapshotBatch.__dataclass_fields__)
    chunks: dict[str, list[np.ndarray]] = {field: [] for field in fields}
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            missing = [field for field in fields if field not in data]
            if missing:
                raise ValueError(f"{path} missing fields: {missing}")
            shard = validate_capacity_snapshots(
                CapacitySnapshotBatch(**{field: data[field] for field in fields})
            )
            for field in fields:
                chunks[field].append(np.asarray(getattr(shard, field)))
    return validate_capacity_snapshots(
        CapacitySnapshotBatch(
            **{field: np.concatenate(chunks[field], axis=0) for field in fields}
        )
    )


def grouped_reset_split(reset_id: np.ndarray, seed: int) -> ResetSplit:
    ids = np.unique(np.asarray(reset_id, dtype=np.int64).reshape(-1))
    if ids.size < 5:
        raise ValueError("at least five reset groups are required")
    shuffled = ids.copy()
    np.random.default_rng(int(seed)).shuffle(shuffled)
    n_test = max(1, int(np.floor(0.2 * shuffled.size)))
    n_validation = max(1, int(np.floor(0.2 * shuffled.size)))
    test_ids = np.sort(shuffled[:n_test])
    validation_ids = np.sort(shuffled[n_test:n_test + n_validation])
    train_ids = np.sort(shuffled[n_test + n_validation:])
    reset_values = np.asarray(reset_id, dtype=np.int64).reshape(-1)
    return ResetSplit(
        train=np.flatnonzero(np.isin(reset_values, train_ids)),
        validation=np.flatnonzero(np.isin(reset_values, validation_ids)),
        test=np.flatnonzero(np.isin(reset_values, test_ids)),
        train_reset_ids=tuple(int(value) for value in train_ids),
        validation_reset_ids=tuple(int(value) for value in validation_ids),
        test_reset_ids=tuple(int(value) for value in test_ids),
    )


def cluster_bootstrap_difference(
    active: np.ndarray,
    control: np.ndarray,
    reset_ids: np.ndarray,
    *,
    reps: int,
    seed: int,
) -> BootstrapInterval:
    active_values = np.asarray(active, dtype=np.float64).reshape(-1)
    control_values = np.asarray(control, dtype=np.float64).reshape(-1)
    groups = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    if active_values.shape != control_values.shape or active_values.shape != groups.shape:
        raise ValueError("active, control, and reset_ids must be row-aligned")
    unique_groups = np.unique(groups)
    if unique_groups.size < 5:
        raise ValueError("at least five reset groups are required for bootstrap")
    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(reps), dtype=np.float64)
    for index in range(int(reps)):
        sampled = rng.choice(unique_groups, size=unique_groups.size, replace=True)
        rows = np.concatenate([np.flatnonzero(groups == group) for group in sampled])
        estimates[index] = float((active_values[rows] - control_values[rows]).mean())
    return BootstrapInterval(
        mean=float((active_values - control_values).mean()),
        lower=float(np.quantile(estimates, 0.025)),
        upper=float(np.quantile(estimates, 0.975)),
    )
```

- [ ] **Step 4: Run Task 1 tests**

Run the command from Step 2 again.

Expected: `4 passed`; no directory is created outside `tests/.pytest_tmp/r27-g1/task1`.

- [ ] **Step 5: Commit the independently reviewable snapshot contract**

```powershell
git add ha_ctse_process/low_actor_capacity_audit.py tests/r27_low_actor_capacity_audit_test.py
git commit -m "feat: add R27 capacity snapshot contract"
```

Review gate: a task reviewer must verify row alignment, dtype normalization, no reset leakage, cluster rather than row bootstrap, and no task/communication field in the schema.

---

### Task 2: Detached Static Actor-Distribution Audit

**Files:**
- Modify: `ha_ctse_process/low_actor_capacity_audit.py`
- Modify: `tests/r27_low_actor_capacity_audit_test.py`

**Interfaces:**
- Consumes: `StrictHMASDMAPPOLowLevelPolicy`, `CapacitySnapshotBatch`.
- Produces: `ActorForwardBatch`, `forward_actor_snapshot`, `symmetric_kl_diag_gaussian`, `evaluate_static_checkpoint`, and `gate_static_family`.

- [ ] **Step 1: Add failing live-parity and inactive-control tests**

Append these tests and helper:

```python
from ha_ctse_process.low_actor_capacity_audit import (
    evaluate_static_checkpoint,
    forward_actor_snapshot,
    gate_static_family,
)
from ha_ctse_process.standalone_agent import StrictHMASDMAPPOLowLevelPolicy


def make_continuous_actor() -> StrictHMASDMAPPOLowLevelPolicy:
    torch.manual_seed(27020)
    return StrictHMASDMAPPOLowLevelPolicy(
        obs_dim=6,
        state_dim=7,
        n_skills=4,
        num_team_codes=2,
        action_dim=4,
        hidden_dim=8,
        action_space_type="continuous",
        continuous_action_distribution="tanh_gaussian",
        actor_condition_on_team_code=False,
        device="cpu",
    ).eval()


def test_detached_forward_matches_live_actor_distribution():
    actor = make_continuous_actor()
    obs = torch.randn(5, 6)
    skills = torch.tensor([0, 1, 2, 3, 0])
    hidden = torch.randn(5, 8)
    result = forward_actor_snapshot(actor, obs, skills, hidden, inactive_film=False)
    with torch.no_grad():
        actions, _, _, _, live_hidden, _ = actor.act(
            obs,
            skills,
            hidden.clone(),
            torch.zeros(5, 7),
            torch.zeros(5, dtype=torch.long),
            torch.zeros(5, 8),
            deterministic=True,
        )
    torch.testing.assert_close(result.deterministic_action, actions, atol=1e-6, rtol=1e-6)
    torch.testing.assert_close(result.new_hidden, live_hidden, atol=1e-6, rtol=1e-6)
    assert not result.action_mean.requires_grad


def test_identity_film_has_zero_skill_pair_separation():
    actor = make_continuous_actor()
    batch = make_snapshots(resets=10)
    report = evaluate_static_checkpoint(
        actor,
        batch,
        checkpoint_id="fixture",
        bootstrap_reps=200,
        bootstrap_seed=27021,
    )
    assert report["inactive_control"]["max_abs_symmetric_kl"] <= 1e-8
    assert report["inactive_control"]["max_stdmean_distance"] <= 1e-8


def test_static_family_requires_two_of_three_agreement():
    passing = {"zero_h_pass": True, "rollout_h_pass": True, "retention": 0.8}
    failing = {"zero_h_pass": False, "rollout_h_pass": False, "retention": 0.0}
    family = gate_static_family([passing, passing, failing])
    assert family["zero_h_pass"] is True
    assert family["rollout_h_pass"] is True
    assert family["recurrent_washout"] is False
```

- [ ] **Step 2: Run only the new tests and confirm missing symbols**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task2
```

Expected: import failure naming `evaluate_static_checkpoint` or `forward_actor_snapshot`.

- [ ] **Step 3: Implement one localized diagnostic traversal of the private actor API**

Add these types and functions. Do not add a method to the actor itself.

```python
from itertools import combinations
from typing import Any

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class ActorForwardBatch:
    gamma: torch.Tensor
    beta: torch.Tensor
    film_feature: torch.Tensor
    post_gru_feature: torch.Tensor
    action_mean: torch.Tensor
    action_logstd: torch.Tensor
    deterministic_action: torch.Tensor
    new_hidden: torch.Tensor


def forward_actor_snapshot(
    actor: Any,
    observations: torch.Tensor,
    skills: torch.Tensor,
    actor_hidden: torch.Tensor,
    *,
    inactive_film: bool,
) -> ActorForwardBatch:
    if actor.action_space_type != "continuous":
        raise ValueError("R27 static audit requires a continuous low actor")
    action_out = actor.actor_act.action_out
    if type(action_out).__name__ != "TanhDiagGaussian":
        raise ValueError("R27 static audit requires TanhDiagGaussian")
    obs = observations.to(dtype=torch.float32, device=actor.device)
    skill = skills.to(dtype=torch.long, device=actor.device)
    hidden = actor_hidden.to(dtype=torch.float32, device=actor.device)
    with torch.no_grad():
        base = actor.actor_base(obs)
        raw_film = actor.actor_film(F.one_hot(skill, actor.n_skills).float())
        gamma, beta = torch.chunk(raw_film, 2, dim=-1)
        if inactive_film:
            gamma = torch.ones_like(gamma)
            beta = torch.zeros_like(beta)
        film_feature = gamma * base + beta
        masks = torch.ones(obs.shape[0], 1, dtype=torch.float32, device=actor.device)
        post_gru, new_hidden = actor.actor_rnn(film_feature, hidden, masks)
        distribution = action_out._distribution(post_gru)
        action_mean = distribution.mean
        action_logstd = distribution.scale.log()
        deterministic_action = torch.tanh(action_mean)
    return ActorForwardBatch(
        gamma=gamma.detach(),
        beta=beta.detach(),
        film_feature=film_feature.detach(),
        post_gru_feature=post_gru.detach(),
        action_mean=action_mean.detach(),
        action_logstd=action_logstd.detach(),
        deterministic_action=deterministic_action.detach(),
        new_hidden=new_hidden.detach(),
    )


def symmetric_kl_diag_gaussian(
    mean_a: torch.Tensor,
    logstd_a: torch.Tensor,
    mean_b: torch.Tensor,
    logstd_b: torch.Tensor,
) -> torch.Tensor:
    var_a = torch.exp(2.0 * logstd_a)
    var_b = torch.exp(2.0 * logstd_b)
    delta_sq = (mean_a - mean_b).pow(2)
    kl_ab = 0.5 * (
        2.0 * (logstd_b - logstd_a) + (var_a + delta_sq) / var_b - 1.0
    ).sum(dim=-1)
    kl_ba = 0.5 * (
        2.0 * (logstd_a - logstd_b) + (var_b + delta_sq) / var_a - 1.0
    ).sum(dim=-1)
    return 0.5 * (kl_ab + kl_ba)
```

Keep all `_distribution` access inside `forward_actor_snapshot`; no other R27 file may traverse `actor_act.action_out`.

- [ ] **Step 4: Implement enumeration and exact static gates**

Add a private `_condition_metrics(active: ActorForwardBatch, inactive: ActorForwardBatch, reset_ids: np.ndarray, num_skills: int, bootstrap_reps: int, bootstrap_seed: int) -> dict[str, object]` that reshapes results to `[rows, skills, feature]`, enumerates `combinations(range(K), 2)`, and returns per-row pair means for active and inactive paths. The public function must have this exact signature and output keys:

```python
def evaluate_static_checkpoint(
    actor: Any,
    batch: CapacitySnapshotBatch,
    *,
    checkpoint_id: str,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    """Evaluate zero-h and rollout-h skill separation without mutating actor state."""
```

Implementation requirements:

```python
STATIC_SKL_MIN = 0.02
STATIC_STDMEAN_MIN = 0.20
INACTIVE_TOLERANCE = 1e-8
PARITY_TOLERANCE = 1e-6

skills = torch.arange(actor.n_skills, device=actor.device).repeat(rows)
observations = torch.as_tensor(batch.observation, device=actor.device).repeat_interleave(actor.n_skills, 0)
rollout_hidden = torch.as_tensor(batch.actor_hidden, device=actor.device).repeat_interleave(actor.n_skills, 0)
zero_hidden = torch.zeros_like(rollout_hidden)
```

For each condition:

- compute active and identity-FiLM outputs on identical expanded rows;
- verify all action log standard deviations are shared across enumerated skills to `1e-6`;
- compute per-row mean pairwise symmetric KL and standardized mean distance;
- compute mean pairwise L2 separation for FiLM and post-GRU features;
- bootstrap active-minus-inactive symmetric KL by `batch.reset_id`;
- fail the checkpoint as `INVALID` if any value is non-finite, the inactive maximum exceeds `1e-8`, or deterministic action parity with `actor.act` exceeds `1e-6` on the same rows;
- set condition pass only when KL, standardized distance, and bootstrap lower bound all pass.

Return these exact top-level keys; every named metric value is a computed finite `float` and every `pass` value is a `bool`:

```python
STATIC_REPORT_KEYS = {
    "checkpoint_id",
    "rows",
    "num_skills",
    "zero_h",
    "rollout_h",
    "hidden_retention_ratio",
    "inactive_control",
    "parity",
    "status",
}
CONDITION_KEYS = {
    "mean_skl",
    "mean_stdmean_distance",
    "bootstrap",
    "film_feature_between",
    "post_gru_feature_between",
    "pass",
}
INACTIVE_KEYS = {"max_abs_symmetric_kl", "max_stdmean_distance"}
PARITY_KEYS = {"max_action_abs_error", "max_hidden_abs_error", "pass"}
```

Set `hidden_retention_ratio = rollout_skl / max(zero_skl, 1e-8)` and set `status` to exactly one of `PASS`, `FAIL`, `INVALID`, or `UNDERPOWERED`.

Implement `gate_static_family(reports)` with two-of-three counts. Set `recurrent_washout=True` only when at least two reports have `zero_h_pass=True`, `rollout_h` KL below `0.02`, and retention below `0.50`.

- [ ] **Step 5: Run static tests and the existing actor regression subset**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_audit_test.py tests/ha_ctse_process_standalone_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task2
```

Expected: all selected tests pass; parity errors are at most `1e-6`; the actor file has no diff.

- [ ] **Step 6: Commit the static audit**

```powershell
git add ha_ctse_process/low_actor_capacity_audit.py tests/r27_low_actor_capacity_audit_test.py
git commit -m "feat: audit frozen low-actor skill capacity"
```

Review gate: standard Sol review. The reviewer must recompute the symmetric-KL formula, inspect raw pre-squash means/logstd, confirm inactive control is identity realization rather than module deletion, and confirm zero-h versus rollout-h differs only in hidden input.

---

### Task 3: Synthetic Active/Sham Positive Control And Classification

**Files:**
- Modify: `ha_ctse_process/low_actor_capacity_audit.py`
- Modify: `tests/r27_low_actor_capacity_audit_test.py`

**Interfaces:**
- Consumes: final-checkpoint actor clone and final `CapacitySnapshotBatch` reset split.
- Produces: `SyntheticRows`, `SyntheticFitConfig`, `build_orthogonal_codebook`, `build_balanced_synthetic_rows`, `fit_synthetic_clone`, `evaluate_synthetic_seed`, `gate_synthetic_family`, and `classify_capacity_autopsy`.

- [ ] **Step 1: Add failing codebook, sham, isolation, and classification tests**

Append tests that use a small continuous actor and CPU fixtures:

```python
from ha_ctse_process.low_actor_capacity_audit import (
    SyntheticFitConfig,
    build_balanced_synthetic_rows,
    build_orthogonal_codebook,
    classify_capacity_autopsy,
    evaluate_synthetic_seed,
)


def test_codebook_is_orthogonal_and_has_fixed_norm():
    codebook = build_orthogonal_codebook(4, 4, seed=27030, norm=0.5)
    np.testing.assert_allclose(np.linalg.norm(codebook, axis=1), 0.5, atol=1e-6)
    np.testing.assert_allclose(codebook @ codebook.T, np.eye(4) * 0.25, atol=1e-6)


def test_balanced_rows_have_exact_true_and_fake_marginals():
    batch = make_snapshots(resets=10)
    rows = build_balanced_synthetic_rows(batch, np.arange(batch.reset_id.size), 4, seed=27031)
    np.testing.assert_array_equal(np.bincount(rows.true_skill, minlength=4), np.full(4, batch.reset_id.size))
    np.testing.assert_array_equal(np.bincount(rows.fake_skill, minlength=4), np.full(4, batch.reset_id.size))
    assert np.any(rows.true_skill != rows.fake_skill)


def test_synthetic_fit_never_accepts_test_rows(monkeypatch):
    import ha_ctse_process.low_actor_capacity_audit as audit
    batch = make_snapshots(resets=10)
    split = grouped_reset_split(batch.reset_id, seed=27011)
    actor = make_continuous_actor()
    codebook = build_orthogonal_codebook(4, 4, seed=27030, norm=0.5)
    original = audit.fit_synthetic_clone

    def checked_fit(*, train, validation, **kwargs):
        assert set(train.reset_id).isdisjoint(validation.reset_id)
        return original(train=train, validation=validation, **kwargs)

    monkeypatch.setattr(audit, "fit_synthetic_clone", checked_fit)
    result = evaluate_synthetic_seed(
        actor,
        batch,
        split,
        codebook,
        seed=17,
        config=SyntheticFitConfig(max_steps=100, validation_interval=10, patience=5),
        device=torch.device("cpu"),
        bootstrap_reps=100,
    )
    assert result["test_evaluations"] == {"active": 1, "sham": 1}


@pytest.mark.parametrize(
    ("static_family", "synthetic_family", "expected"),
    [
        ({"zero_h_pass": True, "rollout_h_pass": False, "recurrent_washout": True}, {"pass": True}, "RECURRENT_WASHOUT"),
        ({"zero_h_pass": False, "rollout_h_pass": False, "recurrent_washout": False}, {"pass": True}, "CAPACITY_PRESENT_OBJECTIVE_MISSING"),
        ({"zero_h_pass": False, "rollout_h_pass": False, "recurrent_washout": False}, {"pass": False, "failed_seeds": 2}, "STATIC_PATH_CAPACITY_WEAK"),
        ({"zero_h_pass": True, "rollout_h_pass": True, "recurrent_washout": False}, {"pass": True}, "STATIC_USED_OBSERVATIONAL_MISS"),
    ],
)
def test_every_primary_classification_branch_is_reachable(static_family, synthetic_family, expected):
    result = classify_capacity_autopsy(static_family, synthetic_family)
    assert result["classification"] == expected
```

Add separate fixtures asserting `UNDERPOWERED` takes precedence over scientific classifications and `INVALID` takes precedence over all other results.

- [ ] **Step 2: Verify the synthetic API is absent**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task3
```

Expected: import failure for `SyntheticFitConfig` or `build_orthogonal_codebook`.

- [ ] **Step 3: Implement balanced synthetic rows and a fixed orthogonal codebook**

Add these contracts:

```python
import copy


@dataclass(frozen=True)
class SyntheticRows:
    observation: np.ndarray
    actor_hidden: np.ndarray
    true_skill: np.ndarray
    fake_skill: np.ndarray
    reset_id: np.ndarray


@dataclass(frozen=True)
class SyntheticFitConfig:
    learning_rate: float = 3e-4
    batch_size: int = 256
    max_steps: int = 1000
    validation_interval: int = 25
    patience: int = 20
    min_delta: float = 1e-4


def build_orthogonal_codebook(
    num_skills: int,
    action_dim: int,
    *,
    seed: int,
    norm: float,
) -> np.ndarray:
    if int(num_skills) > int(action_dim):
        raise ValueError("orthogonal codebook requires num_skills <= action_dim")
    matrix = np.random.default_rng(int(seed)).normal(size=(int(action_dim), int(num_skills)))
    q, _ = np.linalg.qr(matrix)
    return (q[:, : int(num_skills)].T * float(norm)).astype(np.float32)


def build_balanced_synthetic_rows(
    batch: CapacitySnapshotBatch,
    indices: np.ndarray,
    num_skills: int,
    *,
    seed: int,
) -> SyntheticRows:
    source = batch.take(np.asarray(indices, dtype=np.int64))
    rows = int(source.reset_id.size)
    observations = np.repeat(source.observation, int(num_skills), axis=0)
    hidden = np.repeat(source.actor_hidden, int(num_skills), axis=0)
    reset_ids = np.repeat(source.reset_id, int(num_skills), axis=0)
    true_skill = np.tile(np.arange(int(num_skills), dtype=np.int64), rows)
    rng = np.random.default_rng(int(seed))
    fake_skill = np.concatenate(
        [rng.permutation(int(num_skills)) for _ in range(rows)]
    ).astype(np.int64)
    return SyntheticRows(observations, hidden, true_skill, fake_skill, reset_ids)
```

The per-source-row random permutation gives the sham the exact marginal while making the fake-to-true mapping reset/observation-specific; held-out reset groups prevent memorized row mappings from validating the sham.

- [ ] **Step 4: Implement identical active/sham actor-clone fitting**

Use `copy.deepcopy(source_actor)` for both clones before either optimizer step. Optimize only `clone.actor_update_parameters()`. Build one seeded list of minibatch index arrays and pass that same list to active and sham fits.

The fit API must not accept test rows:

```python
def fit_synthetic_clone(
    *,
    source_actor: object,
    train: SyntheticRows,
    validation: SyntheticRows,
    input_label_field: str,
    codebook: np.ndarray,
    minibatches: tuple[np.ndarray, ...],
    config: SyntheticFitConfig,
    device: torch.device,
) -> dict[str, object]:
```

At each step, call a private `_actor_raw_mean_for_training(actor: object, observations: torch.Tensor, skills: torch.Tensor, actor_hidden: torch.Tensor) -> torch.Tensor`. Because the detached public helper deliberately uses `torch.no_grad()`, this private function duplicates only the localized active forward without `no_grad`, returns `distribution.mean`, and is covered by a numerical equality test against `forward_actor_snapshot` before optimization.

Use this exact loss and stop logic:

```python
target = torch.as_tensor(codebook[true_skill], dtype=torch.float32, device=device)
loss = torch.nn.functional.mse_loss(predicted_raw_mean, target)

if validation_loss < best_validation_loss - config.min_delta:
    best_validation_loss = validation_loss
    best_step = step
    best_state = copy.deepcopy(clone.state_dict())
    stale_checks = 0
else:
    stale_checks += 1
if stale_checks >= config.patience:
    break
```

Reload `best_state` before returning. Return the clone, best step, train loss trajectory, validation loss trajectory, and `validation_evaluations`; do not calculate a test metric inside this function.

- [ ] **Step 5: Implement one-time test scoring, paired reset bootstrap, and seed/family gates**

Decode raw predicted means by nearest Euclidean codebook row. Compute accuracy, macro-F1 over all four labels, MSE, per-row correctness, and reset ids. `evaluate_synthetic_seed` must:

1. create active and sham clones from the same source state;
2. use true skill for active input and fake skill for sham input;
3. use the same target true skill and minibatch schedule;
4. call test scoring exactly once for each best-validation clone;
5. bootstrap active correctness minus sham correctness by test reset;
6. emit all fixed thresholds and source hashes.

Set seed pass exactly as specified in Global Constraints. `gate_synthetic_family` returns pass only for at least two passing seeds, fail only for at least two failing seeds, and otherwise returns `UNDERPOWERED`.

Implement classification with this precedence:

```python
def classify_capacity_autopsy(
    static_family: dict[str, object],
    synthetic_family: dict[str, object],
) -> dict[str, object]:
    if static_family.get("status") == "INVALID" or synthetic_family.get("status") == "INVALID":
        return {"classification": "INVALID", "reasons": ["instrument contract failed"]}
    if static_family.get("status") == "UNDERPOWERED" or synthetic_family.get("status") == "UNDERPOWERED":
        return {"classification": "UNDERPOWERED", "reasons": ["family support is insufficient"]}
    if synthetic_family["pass"] and static_family["recurrent_washout"]:
        return {"classification": "RECURRENT_WASHOUT", "reasons": ["zero-h capacity is lost under rollout hidden state"]}
    if synthetic_family["pass"] and static_family["rollout_h_pass"]:
        return {"classification": "STATIC_USED_OBSERVATIONAL_MISS", "reasons": ["trained actor has immediate z-conditioned action separation"]}
    if synthetic_family["pass"] and not static_family["rollout_h_pass"]:
        return {"classification": "CAPACITY_PRESENT_OBJECTIVE_MISSING", "reasons": ["clone learns the code but trained actor does not use it"]}
    if int(synthetic_family.get("failed_seeds", 0)) >= 2:
        return {"classification": "STATIC_PATH_CAPACITY_WEAK", "reasons": ["active clone fails the fixed synthetic gate"]}
    return {"classification": "UNDERPOWERED", "reasons": ["no classification has two-of-three support"]}
```

- [ ] **Step 6: Run focused synthetic and classification tests**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task3
```

Expected: all tests pass; the synthetic fixture finishes in under 90 seconds on CPU by using its reduced test-only `SyntheticFitConfig`; production defaults remain unchanged.

- [ ] **Step 7: Commit the positive control**

```powershell
git add ha_ctse_process/low_actor_capacity_audit.py tests/r27_low_actor_capacity_audit_test.py
git commit -m "feat: add R27 synthetic capacity control"
```

Review gate: standard Sol review. It must verify same initialization, same batch schedule, actor-only optimizer, exact fake-label marginal, test isolation, source immutability, macro-F1, and two-of-three logic.

---

### Task 4: Frozen Checkpoint CLI, Natural-Renewal Collector, And Reports

**Files:**
- Create: `scripts/audit_r27_low_actor_capacity.py`
- Create: `tests/r27_low_actor_capacity_cli_test.py`

**Interfaces:**
- Consumes: the public library from Tasks 1-3 and existing checkpoint APIs in `ha_ctse_process.train`.
- Produces: CLI subcommands `collect-static`, `synthetic`, and `aggregate`; per-checkpoint and batch output contracts from the approved spec.

- [ ] **Step 1: Write failing collector and CLI-contract tests**

Create tests that define a two-agent fake environment/agent with `low_actor_hxs`, natural segment object replacement, and forbidden update methods. Import `SimpleNamespace`, `json`, `subprocess`, `Path`, `numpy`, `pytest`, `torch`, `CapacitySnapshotBatch`, and `scripts.audit_r27_low_actor_capacity as collector`. The required assertions are:

```python
def test_collector_records_hidden_state_before_natural_assignment(fake_env, fake_agent):
    fake_agent.low_actor_hxs[0, 0] = np.asarray([1.0, 2.0, 3.0, 4.0])
    batch, stats = collector.collect_capacity_reset(
        fake_env, fake_agent, reset_id=3, reset_seed=27003,
        episode_id=3, skill_interval=10, episode_max_steps=2,
        checkpoint_id="fixture", checkpoint_update=25,
    )
    np.testing.assert_array_equal(batch.actor_hidden[0], [1.0, 2.0, 3.0, 4.0])
    assert batch.natural_skill.tolist() == [1]
    assert stats.renewal_events == 1
    assert fake_agent.assignment_grad_enabled == [False, False]
    assert fake_agent.action_grad_enabled == [False, False]


def test_collector_does_not_store_task_or_communication_fields(fake_env, fake_agent):
    batch, _ = collector.collect_capacity_reset(
        fake_env,
        fake_agent,
        reset_id=3,
        reset_seed=27003,
        episode_id=3,
        skill_interval=10,
        episode_max_steps=2,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )
    forbidden = {"reward", "coverage", "throughput", "qos", "backhaul", "topology", "recovery"}
    assert forbidden.isdisjoint(CapacitySnapshotBatch.__dataclass_fields__)


def test_collect_static_rejects_cpu_before_checkpoint_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(collector, "_configure_agent", lambda args: pytest.fail("checkpoint loaded"))
    args = collector.parse_args(["collect-static", "--checkpoint", "missing.pt", "--output-dir", str(tmp_path), "--device", "cpu"])
    with pytest.raises(ValueError, match="requires --device cuda"):
        collector.run_collect_static(args)


def test_aggregate_writes_exact_registered_classification(tmp_path):
    static = {
        "status": "FAIL",
        "zero_h": {"pass": False, "mean_skl": 0.0},
        "rollout_h": {"pass": False, "mean_skl": 0.0},
        "hidden_retention_ratio": 0.0,
    }
    for checkpoint_id in ("arm0_update25", "arm0_update30", "arm0_final"):
        root = tmp_path / checkpoint_id
        root.mkdir()
        payload = dict(static, checkpoint_id=checkpoint_id)
        (root / "static_capacity.json").write_text(json.dumps(payload), encoding="utf-8")
    synthetic = {"status": "PASS", "pass": True, "failed_seeds": 0}
    (tmp_path / "synthetic_control.json").write_text(json.dumps(synthetic), encoding="utf-8")
    args = SimpleNamespace(
        run_root=str(tmp_path),
        checkpoint_ids=["arm0_update25", "arm0_update30", "arm0_final"],
    )
    result = collector.run_aggregate(args)
    assert result["classification"] == "CAPACITY_PRESENT_OBJECTIVE_MISSING"
    assert "CAPACITY_PRESENT_OBJECTIVE_MISSING" in (tmp_path / "r27_capacity_autopsy.md").read_text()
```

- [ ] **Step 2: Run the CLI tests and verify the script is absent**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task4
```

Expected: import failure for `scripts.audit_r27_low_actor_capacity`.

- [ ] **Step 3: Implement checkpoint reconstruction and CUDA guard**

Use these exact existing calls in `_configure_agent(args)`:

```python
config = train_mod.load_config(args.config, args.preset or None)
config.scenario = train_mod.normalize_scenario(args.scenario)
metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
train_mod.apply_checkpoint_structure(config, args, metadata)
env = train_mod.create_env(config, config.scenario, int(args.seed), rank=0, scale_mode="eval")
_obs, info = env.reset(seed=int(args.seed))
state = _state_from_info(info)
agent = train_mod.create_agent(config, args, env, num_envs=1, state_dim=None if state is None else int(state.size))
_steps, update = train_mod.load_checkpoint(args.checkpoint, agent, load_optimizers=False)
_set_eval_mode(agent)
```

Copy the bounded implementations of `_state_from_info`, `_set_eval_mode`, `preserve_agent_runtime`, `policy_parameter_sha256`, and file SHA256 from `scripts/collect_r26_g1_windows.py` into this script instead of importing private script symbols. Include every `_RUNTIME_ATTRIBUTES` member from R26. The immutability tests must compare both checkpoint file SHA256 and agent parameter SHA256 before/after.

`require_cuda_device` accepts `cuda` and `cuda:N`, rejects all CPU strings, and raises if `torch.cuda.is_available()` is false.

- [ ] **Step 4: Implement natural-renewal snapshot collection**

`collect_capacity_reset` follows this exact ordering:

```python
with preserve_agent_runtime(agent):
    obs, info = env.reset(seed=int(reset_seed))
    state = _state_from_info(info)
    agent.reset_env_state(0)
    for step in range(int(episode_max_steps)):
        previous_segments = list(agent.segments.active[0])
        pre_assignment_hidden = np.asarray(agent.low_actor_hxs[0], dtype=np.float32).copy()
        with torch.no_grad():
            agent.maybe_assign_skills(
                obs, state=state, step=step, k=skill_interval,
                env_id=0, deterministic=False,
            )
        current_segments = list(agent.segments.active[0])
        changed = [
            agent_id for agent_id, (before, after) in enumerate(zip(previous_segments, current_segments))
            if after is not None and after is not before
        ]
        for agent_id in changed:
            segment = current_segments[agent_id]
            rows.append({
                "observation": np.asarray(obs[agent_id], dtype=np.float32).copy(),
                "actor_hidden": pre_assignment_hidden[agent_id].copy(),
                "natural_skill": int(segment.skill),
                "previous_skill": int(getattr(segment, "prev_skill", 0)),
                "duration_idx": int(segment.duration_idx),
                "skill_age": int(getattr(segment, "skill_age_prev", 0)),
                "episode_done_mask": False,
                "reset_id": int(reset_id), "reset_seed": int(reset_seed),
                "episode_id": int(episode_id), "env_id": 0, "agent_id": int(agent_id),
                "checkpoint_id": str(checkpoint_id), "checkpoint_update": int(checkpoint_update),
            })
        with torch.no_grad():
            actions, _, _ = agent.act_low(obs, env_id=0, deterministic=False, state=state)
        obs, _reward, terminated, truncated, info = env.step(actions)
        state = _state_from_info(info, previous=state)
        if bool(terminated or truncated):
            break
```

The `_reward` value is discarded immediately and never enters a row, metric, or report. Write one shard per reset below `capacity_snapshots/`.

- [ ] **Step 5: Implement the three subcommands and output contract**

Use `argparse` subparsers:

```text
collect-static --checkpoint --output-dir --checkpoint-id --checkpoint-update
               --config --scenario --preset --seed --n-agents --device
               --skill-interval --n-resets --episode-max-steps
               --bootstrap-reps --bootstrap-seed
synthetic      --checkpoint --snapshot-dir --output-dir --device
               --split-seed --codebook-seed --bootstrap-reps
aggregate      --run-root --checkpoint-ids arm0_update25 arm0_update30 arm0_final
```

`collect-static` writes:

```text
collector_manifest.json
capacity_snapshots/reset_0000.npz through capacity_snapshots/reset_0063.npz
static_capacity.json
static_capacity.md
```

The manifest includes checkpoint/file/parameter hashes, loaded update, reset seeds, row count, field names, dimensions, device, parameter counts, and `status`. `synthetic` writes `synthetic_control.json` and `.md` at the batch root. `aggregate` reads only registered paths and writes `r27_capacity_autopsy.json`, `.md`, and a classification reason list.

Markdown writers must include every threshold and prohibited action. Serialize each named `payload` with `json.dumps(payload, indent=2, sort_keys=True)` and UTF-8 with a final newline.

- [ ] **Step 6: Run CLI tests and a no-write help smoke**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task4
& "C:\Users\wu\.conda\envs\SB3\python.exe" scripts/audit_r27_low_actor_capacity.py --help
```

Expected: tests pass; help lists exactly `collect-static`, `synthetic`, and `aggregate`; no run directory is created.

- [ ] **Step 7: Commit the frozen CLI**

```powershell
git add scripts/audit_r27_low_actor_capacity.py tests/r27_low_actor_capacity_cli_test.py
git commit -m "feat: add R27 frozen capacity audit CLI"
```

Review gate: frontier review because checkpoint reconstruction, hidden-state timing, no-grad ownership, private actor parity, and artifact contracts are shared-state/data-contract risks.

---

### Task 5: Exact Three-Checkpoint CUDA Runner And Dry-Run Contract

**Files:**
- Create: `scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1`
- Modify: `tests/r27_low_actor_capacity_cli_test.py`

**Interfaces:**
- Consumes: Task 4 CLI.
- Produces: one restartable sequential run root with three checkpoint phases, one synthetic phase, one aggregate phase, and status/transcript files.

- [ ] **Step 1: Add failing dry-run tests**

The test invokes PowerShell and asserts:

```python
def test_runner_dry_run_has_exact_arm0_checkpoints_and_no_forbidden_flags():
    result = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", "scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1",
            "-DryRun", "-RunRoot", "logs/r27_dry_run_fixture",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    output = result.stdout + result.stderr
    assert output.count("PHASE collect-static") == 3
    assert "arm0_update25" in output
    assert "arm0_update30" in output
    assert "arm0_final" in output
    assert "arm2_" not in output
    for forbidden in ("process_reward", "prototype_disc", "team_disc", "q_A", "q_d", "q_D", "total_timesteps"):
        assert forbidden not in output
    assert "PHASE synthetic" in output
    assert "PHASE aggregate" in output


def test_runner_rejects_cpu_in_dry_run():
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", "scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1", "-DryRun", "-Device", "cpu"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "requires -Device cuda" in result.stdout + result.stderr
```

- [ ] **Step 2: Run the runner tests and verify the script is absent**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task5
```

Expected: failure because `run_r27_g1_capacity_autopsy_local_cuda.ps1` does not exist.

- [ ] **Step 3: Implement the runner with the exact arm map**

Use these parameters and arm entries:

```powershell
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs/r27_g1_capacity_autopsy",
    [string]$Device = "cuda",
    [int]$NResets = 64,
    [switch]$DryRun,
    [switch]$ContinueOnError
)

$arms = @(
    @{ Name = "arm0_update25"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt"; Update = 25 },
    @{ Name = "arm0_update30"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt"; Update = 30 },
    @{ Name = "arm0_final"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt"; Update = 32 }
)
```

Port the tested `Format-CommandLine`, `Write-RunnerStatus`, and `Invoke-PythonPhase` bodies from `scripts/run_r26_g1_screening_local_cuda.ps1`. Reject non-CUDA before any filesystem write. In non-dry-run mode verify Python, CLI, and all three checkpoints before creating the run root.

For each arm execute:

```text
python scripts/audit_r27_low_actor_capacity.py collect-static
  --checkpoint <path> --output-dir <run>/<arm>
  --checkpoint-id <arm> --checkpoint-update <update>
  --device cuda --n-resets 64
```

Then execute once:

```text
python scripts/audit_r27_low_actor_capacity.py synthetic
  --checkpoint <arm0_final path>
  --snapshot-dir <run>/arm0_final/capacity_snapshots
  --output-dir <run> --device cuda
```

Finally execute:

```text
python scripts/audit_r27_low_actor_capacity.py aggregate
  --run-root <run>
  --checkpoint-ids arm0_update25 arm0_update30 arm0_final
```

Write `command.txt`, `runner_status.txt`, and phase logs below each arm. Write root `batch_status.txt`; update it before and after every phase. `-ContinueOnError` may collect later checkpoint evidence after one checkpoint failure, but synthetic and aggregate run only when their required artifacts exist. Return exit code 1 if any required phase fails.

- [ ] **Step 4: Run dry-run, parser, and focused tests**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1 -DryRun -RunRoot logs/r27_dry_run_fixture
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py -q --basetemp tests/.pytest_tmp/r27-g1/task5
```

Expected: dry-run prints exactly three `collect-static` commands plus one `synthetic` and one `aggregate`; it creates no `logs/r27_dry_run_fixture`; all CLI tests pass.

- [ ] **Step 5: Commit the runner**

```powershell
git add scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1 tests/r27_low_actor_capacity_cli_test.py
git commit -m "feat: add R27 capacity autopsy runner"
```

Review gate: fast mechanical review is insufficient because the runner is the experiment identity boundary. Use standard Sol review to verify checkpoint paths, update labels, CUDA/no-write ordering, exact phase count, and prohibited flags.

---

### Task 6: Full Verification, Pre-Launch Record, And Review Package

**Files:**
- Modify: `memory/ExpRecord.md` through `TerraExpManager` only after tests pass.
- Create at verification time: `logs/r27_g1_capacity_autopsy_build_<timestamp>/verification.md`
- Create at review time: `logs/r27_g1_capacity_autopsy_build_<timestamp>/review_package.md`

**Interfaces:**
- Consumes: Tasks 1-5 commits and approved design spec.
- Produces: launch-ready verification evidence, factual experiment registration, and final whole-branch review disposition. It does not launch the 2.5-3.5 hour run without a separate user instruction.

- [ ] **Step 1: Run the focused regression suite**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest `
  tests/r27_low_actor_capacity_audit_test.py `
  tests/r27_low_actor_capacity_cli_test.py `
  tests/r26_g1_dataset_test.py `
  tests/r26_g1_collector_test.py `
  tests/ha_ctse_process_standalone_test.py `
  -q --basetemp tests/.pytest_tmp/r27-g1/final
```

Expected: all selected tests pass. Remove `tests/.pytest_tmp/r27-g1` after preserving any failure extract under the build log root.

- [ ] **Step 2: Run static hygiene and forbidden-diff checks**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile `
  ha_ctse_process/low_actor_capacity_audit.py `
  scripts/audit_r27_low_actor_capacity.py
git diff --check -- `
  ha_ctse_process/low_actor_capacity_audit.py `
  scripts/audit_r27_low_actor_capacity.py `
  scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1 `
  tests/r27_low_actor_capacity_audit_test.py `
  tests/r27_low_actor_capacity_cli_test.py
git diff a9b257d -- ha_ctse_process/standalone_agent.py ha_ctse_process/train.py ha_ctse_process/config.py hmasd/r_mappo_utils.py
```

Expected: compile and diff checks pass; the final command shows no R27 implementation diff in the actor, train loop, config, or MAPPO utilities. Existing unrelated user changes must be identified separately rather than reverted.

- [ ] **Step 3: Write the verification artifact**

Record exact commands, exit codes, test count, dry-run output, changed files, source commit, and the expected scientific command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1 `
  -RunRoot logs/r27_g1_capacity_autopsy_<timestamp> `
  -Device cuda -NResets 64
```

The artifact states expected wall time `2.5-3.5 hours`, local CUDA, and that no long run was launched during implementation verification.

- [ ] **Step 4: Ask `TerraExpManager` to pre-register the experiment**

The dispatch brief assigns only the R27 factual row in `memory/ExpRecord.md`. It records:

- experiment id `EXP-20260711-r27-g1-low-actor-capacity-autopsy`;
- hypothesis, mechanism path, reward-off/core-impact classification;
- exact three checkpoints and fixed thresholds;
- command, local CUDA device, `NResets=64`, and expected `2.5-3.5 hours`;
- expected artifacts and the five scientific classifications;
- status `ready_not_launched`;
- prohibited actions: actor redesign, q_A/q_d/q_D, reward injection, and scale-up before classification review.

The controller reviews the factual row and does not allow TerraExpManager to edit principle, plan, or result interpretation files.

- [ ] **Step 5: Run final whole-branch review**

Use `SolImplementationReviewerFrontier` with the approved spec, this plan, the task commits, verification artifact, and exact diff. Required review questions:

1. Does the collector capture pre-assignment hidden state at a natural renewal without mutating runtime?
2. Does the diagnostic forward match the live tanh-Gaussian actor exactly?
3. Are static inactive and synthetic sham controls capacity/compute matched?
4. Can test rows influence fitting or early stopping?
5. Are reset clusters preserved in splits and bootstraps?
6. Can any task/communication metric or reward enter the audit?
7. Does every classification follow the pre-registered two-of-three rules?
8. Can the runner silently use CPU, arm2, or an unregistered checkpoint?

Accepted findings go through fix and re-review before launch readiness.

- [ ] **Step 6: Commit the factual record and any reviewed integration fixes**

Tasks 1-5 already committed their implementation. Stage the TerraExpManager-authored ExpRecord row and only files changed by accepted final-review fixes; do not use `git add .` in the dirty worktree.

```powershell
git add memory/ExpRecord.md
git commit -m "docs: register R27 capacity autopsy"
```

If final review required code fixes, commit each accepted fix with its test before the record commit and obtain re-review on that fix.

Completion condition: implementation is reviewed and launch-ready, the factual experiment row exists, and the user receives the experiment-meaning block plus exact launch command. The scientific run remains a separate explicit action.

---

## Experiment Meaning At Launch Handoff

- **Hypothesis:** The current strict-HMASD low actor either has unexploited `z_i`-conditioned control capacity, loses existing static sensitivity through recurrent hidden-state carryover, or already changes immediate actions in a way the R26 behavior-window probe missed.
- **Mechanism path:** `z_i -> low-level action distribution -> persistent executable behavior`; this is upstream of q_A/q_d/q_D and intrinsic reward.
- **Core MARL impact:** Reward-off diagnostic only. It reads the current actor architecture and hidden state; it does not alter reward, policy/critic architecture, optimizer, PPO advantage logic, collector semantics, environment dynamics, or checkpoint identity.
- **Metrics/gates:** Per-checkpoint zero-h/rollout-h symmetric KL, standardized mean distance, FiLM/post-GRU separation, hidden retention, inactive bootstrap; per-seed active/sham accuracy, macro-F1, MSE, bootstrap, generalization gap; two-of-three classification.
- **Time cost/device:** `2.5-3.5 hours`, local CUDA RTX 4070 Laptop GPU, `NResets=64`; no CPU fallback.
- **Decision tree:** Objective-missing permits design of a reward-off skill-use objective; recurrent-washout permits a post-GRU FiLM comparison; static-path-weak permits capacity-matched post-GRU/action-head architecture comparisons; observational-miss requires focused review before a forced multi-step audit; invalid/underpowered repeats the same instrument without threshold changes.
- **Do not change yet:** No actor redesign, hidden reset, post-GRU FiLM, action-head residual, q_A/q_d/q_D, intrinsic reward, long training, or HMASD parity claim before R27 classification review.
- **Status source:** Approved R27 design, R26 arm0 failure review, controller code map, and frozen checkpoint contracts.
