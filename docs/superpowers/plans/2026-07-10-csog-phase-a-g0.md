# CSOG Phase A G0 Dynamics Gate Implementation Plan

> **SUPERSEDED 2026-07-10. DO NOT EXECUTE.** IMOD-Direct removes the world
> model from the first individual-skill gate and uses randomized real
> interventions as primary evidence. See
> `docs/superpowers/specs/2026-07-10-imod-direct-design.md`. A replacement plan
> is prohibited until written-spec review and independent cross-family MARL
> review complete.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent, reward-off G0 diagnostic that collects real trajectories from a healthy frozen HMASD+OPT policy and determines whether an action-conditioned distributional model can predict frozen OPT interaction dynamics beyond persistence and same-capacity action-shuffle nulls.

**Architecture:** New code lives under `csog/` and does not modify the legacy agent or trainer. A temporary script boundary loads one healthy legacy checkpoint, executes stochastic real-environment episodes, and encodes every state with one frozen OPT target encoder. Episode-grouped windows feed identically trained real-action and action-shuffle ensembles; a deterministic evaluator writes the registered G0 verdict.

**Tech Stack:** Python, PyTorch, NumPy, pytest, NPZ, JSON, Markdown, existing HMASD environment/checkpoint utilities, cloud CUDA.

## Global Constraints

- Execute this plan in an isolated worktree on branch `codex/csog-radical`; use `superpowers:using-git-worktrees` at execution time.
- Do not modify `ha_ctse_process/standalone_agent.py`, `ha_ctse_process/train.py`, `ha_ctse_process/config.py`, or any legacy reward/probe implementation in Phase A.
- `csog/` must not import a legacy policy, legacy reward, `q_A`, `q_d`, or `q_D` module.
- The only permitted legacy-policy dependency is inside `scripts/export_csog_g0.py`.
- Phase A is diagnostic-only: no policy update, PPO update, optimizer update, reward injection, operator codebook, graph policy, or scheduler.
- Use `h_t = concat(compact_t, omega_t, flatten(agent_relevance_t))` from one frozen target OPT encoder hash for every trajectory in one G0 read, preserving the compact aggregate, global prototype activation, and per-agent interaction structure.
- Environment reward is logged only as external episode health; it is never included in world-model inputs or called intrinsic.
- Do not concatenate reward information, communication indicators, agent identity, skill labels, duration, phase, or history metadata into world-model inputs.
- Phase A supports the current discrete HMASD action space only and stores one-hot joint action features. A continuous action space must fail fast and receive a separately reviewed encoding contract.
- Split by episode before forming windows. One episode id belongs to exactly one of train, validation, or test.
- Aggregate held-out errors and uncertainty at the episode level before computing gate means or rank calibration, so overlapping windows do not create pseudo-replication.
- Train the real-action and action-shuffle variants with identical model class, ensemble size, seeds, batch size, optimizer, epoch cap, early-stopping patience, and device class.
- Validation data selects early stopping. Test data is read once after both variants are frozen.
- Default full analysis device is CUDA. If CUDA is requested but unavailable, raise an error; do not fall back to CPU.
- Put all runtime files under `logs/EXP-20260710-csog-g0-dynamics/` or a caller-supplied run root beneath `logs/`.
- Do not launch the full G0 run while implementing this plan. Packaging and commands may be prepared; launch requires an explicit controller/user decision.
- G0 is `PASS` only when the dataset-validity precondition and every registered dynamics/calibration condition pass.

---

## File Map

| File | Responsibility |
| --- | --- |
| `csog/__init__.py` | Stable Phase A public exports only |
| `csog/trajectory.py` | Validated real-trajectory contract, joint-action encoding, NPZ storage |
| `csog/recognition.py` | Frozen OPT target encoder and deterministic encoder hash |
| `csog/collector.py` | Policy-agnostic real episode collector |
| `csog/dynamics_data.py` | Episode split, standardization, H50 windows, action-shuffle null, data validity |
| `csog/world_model.py` | Distributional recurrent dynamics member, equal-budget fitting, ensemble prediction |
| `csog/g0.py` | Metrics, uncertainty calibration, gate decision, report serialization |
| `scripts/export_csog_g0.py` | Temporary legacy-checkpoint-to-CSOG-trajectory adapter |
| `scripts/analyze_csog_g0.py` | One-shot grouped fit/evaluate/report CLI |
| `scripts/run_csog_g0_cloud.sh` | CUDA-only full diagnostic runner |
| `tests/csog/*.py` | Focused unit and pipeline tests |

## Fixed Phase A Interfaces

Later tasks must use these exact names:

```python
TrajectoryRecord
encode_joint_action(...)
write_trajectory(...)
read_trajectory(...)
load_trajectories(...)

OPTTargetEncoder
EncodedInteraction
load_target_opt_encoder(...)

EpisodePolicy
Transition
collect_episode(...)

TrajectorySplit
LatentStandardizer
WindowBatch
DataValidity
grouped_episode_split(...)
build_windows(...)
shuffle_action_sequences(...)
evaluate_data_validity(...)

DynamicsFitConfig
GaussianLatentDynamics
FittedMember
fit_ensemble(...)
predict_ensemble(...)

G0Metrics
G0Decision
compute_g0_metrics(...)
decide_g0(...)
write_g0_report(...)
```

## Execution Preflight

- [ ] Confirm the isolated branch and clean task scope.

Run:

```powershell
git branch --show-current
git status --short
```

Expected: branch is `codex/csog-radical`; there are no unrelated changes in the isolated worktree.

- [ ] Confirm the known healthy source checkpoint is available for the later smoke.

Run:

```powershell
Test-Path "dist\logs_cloud_r24_frozen_qd_overnight_20260709_005624\qAon\seed1\r24_qd_null_control_seed1\standalone_process_core_final.pt"
```

Expected: `True`. If the execution worktree does not contain the ignored `dist/` archive, copy or mount that exact artifact before the smoke; do not substitute one of the three zero-coverage checkpoints.

### Task 1: Real Trajectory Contract And Storage

**Files:**
- Create: `csog/__init__.py`
- Create: `csog/trajectory.py`
- Create: `tests/csog/test_trajectory.py`

**Interfaces:**
- Consumes: NumPy arrays from a real environment episode.
- Produces: `TrajectoryRecord`, `encode_joint_action`, `write_trajectory`, `read_trajectory`, and `load_trajectories` for Tasks 3-6.

- [ ] **Step 1: Write the failing trajectory tests**

Create `tests/csog/test_trajectory.py`:

```python
from pathlib import Path

import numpy as np
import pytest

from csog.trajectory import (
    TrajectoryRecord,
    encode_joint_action,
    read_trajectory,
    write_trajectory,
)


def make_record() -> TrajectoryRecord:
    return TrajectoryRecord(
        latent=np.arange(20, dtype=np.float32).reshape(5, 4),
        actions=np.eye(4, dtype=np.float32),
        dones=np.asarray([False, False, False, True]),
        episode_id="healthy-seed17-episode000",
        source_checkpoint="standalone_process_core_final.pt",
        encoder_hash="abc123",
        seed=17,
        policy_mode="stochastic",
        action_encoding="discrete_one_hot",
        n_agents=2,
        health={
            "external_return": 3.5,
            "coverage_positive_step_fraction": 0.75,
            "zero_throughput_step_fraction": 0.25,
        },
    )


def test_discrete_joint_action_is_one_hot_per_agent():
    encoded = encode_joint_action(
        np.asarray([2, 0]),
        n_agents=2,
        action_dim=3,
        action_space_type="discrete",
    )
    np.testing.assert_array_equal(
        encoded,
        np.asarray([0, 0, 1, 1, 0, 0], dtype=np.float32),
    )


def test_trajectory_roundtrip_uses_pickle_free_npz(tmp_path: Path):
    path = tmp_path / "episode.npz"
    write_trajectory(path, make_record())
    restored = read_trajectory(path)

    assert restored.episode_id == "healthy-seed17-episode000"
    assert restored.health["external_return"] == 3.5
    np.testing.assert_array_equal(restored.latent, make_record().latent)
    np.testing.assert_array_equal(restored.actions, make_record().actions)
    np.testing.assert_array_equal(restored.dones, make_record().dones)

    with np.load(path, allow_pickle=False) as payload:
        assert set(payload.files) == {"latent", "actions", "dones", "metadata_json"}


def test_trajectory_rejects_transition_length_mismatch():
    record = make_record()
    broken = TrajectoryRecord(
        latent=record.latent[:-1],
        actions=record.actions,
        dones=record.dones,
        episode_id=record.episode_id,
        source_checkpoint=record.source_checkpoint,
        encoder_hash=record.encoder_hash,
        seed=record.seed,
        policy_mode=record.policy_mode,
        action_encoding=record.action_encoding,
        n_agents=record.n_agents,
        health=record.health,
    )
    with pytest.raises(ValueError, match="latent length must equal action length plus one"):
        broken.validate()
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_trajectory.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog'`.

- [ ] **Step 3: Implement the validated record, action encoding, and storage**

Create `csog/trajectory.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class TrajectoryRecord:
    latent: np.ndarray
    actions: np.ndarray
    dones: np.ndarray
    episode_id: str
    source_checkpoint: str
    encoder_hash: str
    seed: int
    policy_mode: str
    action_encoding: str
    n_agents: int
    health: Mapping[str, float]

    def validate(self) -> None:
        latent = np.asarray(self.latent)
        actions = np.asarray(self.actions)
        dones = np.asarray(self.dones)
        if latent.ndim != 2 or actions.ndim != 2 or dones.ndim != 1:
            raise ValueError("latent/actions/dones must have ranks 2/2/1")
        if latent.shape[0] != actions.shape[0] + 1:
            raise ValueError("latent length must equal action length plus one")
        if dones.shape[0] != actions.shape[0]:
            raise ValueError("done length must equal action length")
        if actions.shape[0] == 0:
            raise ValueError("trajectory must contain at least one transition")
        if np.any(dones[:-1]):
            raise ValueError("terminal transition may only appear at the end of a record")
        if not np.all(np.isfinite(latent)) or not np.all(np.isfinite(actions)):
            raise ValueError("trajectory arrays must be finite")
        if not self.episode_id or not self.source_checkpoint or not self.encoder_hash:
            raise ValueError("trajectory metadata identifiers must be non-empty")
        if int(self.n_agents) <= 0:
            raise ValueError("n_agents must be positive")
        if self.policy_mode not in {"deterministic", "stochastic"}:
            raise ValueError("policy_mode must be deterministic or stochastic")
        if self.action_encoding != "discrete_one_hot":
            raise ValueError("unknown action_encoding")
        if not all(np.isfinite(float(value)) for value in self.health.values()):
            raise ValueError("health metrics must be finite scalars")


def encode_joint_action(
    action: np.ndarray,
    *,
    n_agents: int,
    action_dim: int,
    action_space_type: str,
) -> np.ndarray:
    values = np.asarray(action)
    if action_space_type == "discrete":
        indices = values.astype(np.int64, copy=False).reshape(-1)
        if indices.size != int(n_agents):
            raise ValueError("discrete action must contain one index per agent")
        if np.any(indices < 0) or np.any(indices >= int(action_dim)):
            raise ValueError("discrete action index is outside the action space")
        return np.eye(int(action_dim), dtype=np.float32)[indices].reshape(-1)
    raise ValueError(f"unsupported action_space_type: {action_space_type}")


def write_trajectory(path: str | Path, record: TrajectoryRecord) -> None:
    record.validate()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "episode_id": record.episode_id,
        "source_checkpoint": record.source_checkpoint,
        "encoder_hash": record.encoder_hash,
        "seed": int(record.seed),
        "policy_mode": record.policy_mode,
        "action_encoding": record.action_encoding,
        "n_agents": int(record.n_agents),
        "health": {key: float(value) for key, value in sorted(record.health.items())},
    }
    np.savez_compressed(
        target,
        latent=np.asarray(record.latent, dtype=np.float32),
        actions=np.asarray(record.actions, dtype=np.float32),
        dones=np.asarray(record.dones, dtype=np.bool_),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True, separators=(",", ":"))),
    )


def read_trajectory(path: str | Path) -> TrajectoryRecord:
    with np.load(Path(path), allow_pickle=False) as payload:
        metadata = json.loads(str(payload["metadata_json"].item()))
        record = TrajectoryRecord(
            latent=np.asarray(payload["latent"], dtype=np.float32),
            actions=np.asarray(payload["actions"], dtype=np.float32),
            dones=np.asarray(payload["dones"], dtype=np.bool_),
            episode_id=str(metadata["episode_id"]),
            source_checkpoint=str(metadata["source_checkpoint"]),
            encoder_hash=str(metadata["encoder_hash"]),
            seed=int(metadata["seed"]),
            policy_mode=str(metadata["policy_mode"]),
            action_encoding=str(metadata["action_encoding"]),
            n_agents=int(metadata["n_agents"]),
            health={key: float(value) for key, value in metadata["health"].items()},
        )
    record.validate()
    return record


def load_trajectories(directory: str | Path) -> list[TrajectoryRecord]:
    paths = sorted(Path(directory).glob("episode_*.npz"))
    if not paths:
        raise FileNotFoundError(f"no trajectory shards found in {directory}")
    records = [read_trajectory(path) for path in paths]
    ids = [record.episode_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("episode ids must be unique")
    return records
```

Create `csog/__init__.py`:

```python
from csog.trajectory import (
    TrajectoryRecord,
    encode_joint_action,
    load_trajectories,
    read_trajectory,
    write_trajectory,
)

__all__ = [
    "TrajectoryRecord",
    "encode_joint_action",
    "load_trajectories",
    "read_trajectory",
    "write_trajectory",
]
```

- [ ] **Step 4: Run the trajectory tests**

Run:

```powershell
pytest tests/csog/test_trajectory.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit the trajectory contract**

```powershell
git add csog/__init__.py csog/trajectory.py tests/csog/test_trajectory.py
git commit -m "feat: add CSOG trajectory contract"
```

### Task 2: Frozen OPT Target Encoder

**Files:**
- Create: `csog/recognition.py`
- Create: `tests/csog/test_recognition.py`

**Interfaces:**
- Consumes: the `compact` state dict from an HMASD checkpoint plus state and joint observation tensors.
- Produces: `EncodedInteraction`, `OPTTargetEncoder`, and `load_target_opt_encoder`; `EncodedInteraction.h` is `concat(compact, omega, flatten(agent_relevance))`.

- [ ] **Step 1: Write the failing frozen-encoder tests**

Create `tests/csog/test_recognition.py`:

```python
from pathlib import Path

import torch

from csog.recognition import OPTTargetEncoder, load_target_opt_encoder


def test_checkpoint_loader_freezes_and_reproduces_interaction_state(tmp_path: Path):
    torch.manual_seed(7)
    source = OPTTargetEncoder(
        state_dim=5,
        obs_dim=3,
        hidden_dim=8,
        compact_dim=4,
        num_prototypes=3,
        use_sparsemax=True,
    )
    checkpoint = tmp_path / "checkpoint.pt"
    torch.save({"compact": source.state_dict()}, checkpoint)

    restored = load_target_opt_encoder(checkpoint, device="cpu")
    state = torch.randn(2, 5)
    joint_obs = torch.randn(2, 2, 3)
    expected = source(state, joint_obs)
    actual = restored(state, joint_obs)

    torch.testing.assert_close(actual.h, expected.h)
    torch.testing.assert_close(actual.compact, expected.compact)
    torch.testing.assert_close(actual.omega, expected.omega)
    assert actual.h.shape == (2, 13)
    assert restored.training is False
    assert all(parameter.requires_grad is False for parameter in restored.parameters())
    assert len(restored.encoder_hash) == 64


def test_encoder_hash_changes_when_a_weight_changes():
    first = OPTTargetEncoder(5, 3, 8, 4, 3)
    second = OPTTargetEncoder(5, 3, 8, 4, 3)
    second.load_state_dict(first.state_dict())
    same_hash = first.compute_hash()
    with torch.no_grad():
        second.prototypes[0, 0].add_(1.0)
    assert second.compute_hash() != same_hash
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_recognition.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog.recognition'`.

- [ ] **Step 3: Implement the checkpoint-compatible frozen encoder**

Create `csog/recognition.py`:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def sparsemax(logits: torch.Tensor, dim: int = -1) -> torch.Tensor:
    shifted = logits - logits.max(dim=dim, keepdim=True).values
    ordered = torch.sort(shifted, dim=dim, descending=True).values
    cumulative = torch.cumsum(ordered, dim=dim)
    ranks = torch.arange(
        1,
        shifted.shape[dim] + 1,
        dtype=shifted.dtype,
        device=shifted.device,
    )
    shape = [1] * shifted.ndim
    shape[dim] = -1
    ranks = ranks.view(shape)
    support = 1 + ranks * ordered > cumulative
    support_size = support.sum(dim=dim, keepdim=True).clamp_min(1)
    threshold = (
        cumulative.gather(dim, support_size.long() - 1) - 1
    ) / support_size.to(shifted.dtype)
    return torch.clamp(shifted - threshold, min=0.0)


@dataclass(frozen=True)
class EncodedInteraction:
    h: torch.Tensor
    compact: torch.Tensor
    omega: torch.Tensor
    agent_relevance: torch.Tensor


class OPTTargetEncoder(nn.Module):
    def __init__(
        self,
        state_dim: int,
        obs_dim: int,
        hidden_dim: int,
        compact_dim: int,
        num_prototypes: int,
        use_sparsemax: bool = True,
    ) -> None:
        super().__init__()
        self.state_dim = int(state_dim)
        self.obs_dim = int(obs_dim)
        self.compact_dim = int(compact_dim)
        self.num_prototypes = int(num_prototypes)
        self.use_sparsemax = bool(use_sparsemax)
        self.state_proj = nn.Sequential(
            nn.LayerNorm(self.state_dim),
            nn.Linear(self.state_dim, self.compact_dim),
            nn.GELU(),
        )
        self.obs_proj = nn.Sequential(
            nn.LayerNorm(self.obs_dim),
            nn.Linear(self.obs_dim, self.compact_dim),
            nn.GELU(),
        )
        self.prototype_logits = nn.Linear(self.compact_dim, self.num_prototypes)
        self.prototypes = nn.Parameter(
            torch.randn(self.num_prototypes, self.compact_dim) * 0.02
        )
        self.register_buffer("prototype_bank_ema", self.prototypes.detach().clone())
        self.output = nn.Sequential(
            nn.LayerNorm(self.compact_dim * 2),
            nn.Linear(self.compact_dim * 2, int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), self.compact_dim),
        )
        self.encoder_hash = ""

    def forward(
        self,
        state: torch.Tensor,
        joint_obs: torch.Tensor,
    ) -> EncodedInteraction:
        batch, n_agents, obs_dim = joint_obs.shape
        if state.shape != (batch, self.state_dim):
            raise ValueError("state tensor has the wrong shape")
        if obs_dim != self.obs_dim:
            raise ValueError("joint observation tensor has the wrong feature width")
        state_token = self.state_proj(state.float()).unsqueeze(1)
        obs_tokens = self.obs_proj(joint_obs.float().reshape(-1, obs_dim)).reshape(
            batch,
            n_agents,
            self.compact_dim,
        )
        pooled = torch.cat([state_token, obs_tokens], dim=1).mean(dim=1)
        logits = self.prototype_logits(pooled)
        omega = sparsemax(logits, dim=-1) if self.use_sparsemax else F.softmax(logits, dim=-1)
        agent_logits = self.prototype_logits(obs_tokens.reshape(-1, self.compact_dim)).reshape(
            batch,
            n_agents,
            self.num_prototypes,
        )
        agent_relevance = (
            sparsemax(agent_logits, dim=-1)
            if self.use_sparsemax
            else F.softmax(agent_logits, dim=-1)
        )
        compact = self.output(torch.cat([pooled, omega @ self.prototypes], dim=-1))
        return EncodedInteraction(
            h=torch.cat([compact, omega, agent_relevance.flatten(start_dim=1)], dim=-1),
            compact=compact,
            omega=omega,
            agent_relevance=agent_relevance,
        )

    def compute_hash(self) -> str:
        digest = hashlib.sha256()
        for name, tensor in sorted(self.state_dict().items()):
            array = tensor.detach().cpu().contiguous().numpy()
            digest.update(name.encode("utf-8"))
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
            digest.update(array.tobytes())
        return digest.hexdigest()

    def freeze(self) -> "OPTTargetEncoder":
        self.eval()
        for parameter in self.parameters():
            parameter.requires_grad_(False)
        self.encoder_hash = self.compute_hash()
        return self

    @torch.no_grad()
    def encode_numpy(self, state: np.ndarray, joint_obs: np.ndarray) -> np.ndarray:
        device = next(self.parameters()).device
        encoded = self(
            torch.as_tensor(state, dtype=torch.float32, device=device).reshape(1, -1),
            torch.as_tensor(joint_obs, dtype=torch.float32, device=device).unsqueeze(0),
        )
        return encoded.h.squeeze(0).cpu().numpy().astype(np.float32)


def load_target_opt_encoder(
    checkpoint_path: str | Path,
    *,
    device: str,
) -> OPTTargetEncoder:
    payload = torch.load(Path(checkpoint_path), map_location="cpu")
    if "compact" not in payload:
        raise KeyError("checkpoint does not contain compact encoder weights")
    state_dict = payload["compact"]
    state_dim = int(state_dict["state_proj.1.weight"].shape[1])
    obs_dim = int(state_dict["obs_proj.1.weight"].shape[1])
    compact_dim = int(state_dict["prototypes"].shape[1])
    num_prototypes = int(state_dict["prototypes"].shape[0])
    hidden_dim = int(state_dict["output.1.weight"].shape[0])
    encoder = OPTTargetEncoder(
        state_dim=state_dim,
        obs_dim=obs_dim,
        hidden_dim=hidden_dim,
        compact_dim=compact_dim,
        num_prototypes=num_prototypes,
        use_sparsemax=True,
    )
    encoder.load_state_dict(state_dict, strict=True)
    return encoder.to(device).freeze()
```

- [ ] **Step 4: Run the frozen-encoder tests**

Run:

```powershell
pytest tests/csog/test_recognition.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit the target encoder**

```powershell
git add csog/recognition.py tests/csog/test_recognition.py
git commit -m "feat: add frozen CSOG OPT encoder"
```

### Task 3: Policy-Agnostic Episode Collector And Legacy Export Boundary

**Files:**
- Create: `csog/collector.py`
- Create: `scripts/export_csog_g0.py`
- Create: `tests/csog/test_collector.py`

**Interfaces:**
- Consumes: an environment with Gymnasium `reset`/`step`, an `EpisodePolicy`, an encoder exposing `encode_numpy`, and a health-metric reader.
- Produces: one validated `TrajectoryRecord` per real episode. The script is the only Phase A file allowed to import legacy checkpoint utilities.

- [ ] **Step 1: Write the failing collector test**

Create `tests/csog/test_collector.py`:

```python
import numpy as np

from csog.collector import Transition, collect_episode


class DummyEnv:
    def __init__(self):
        self.step_index = 0

    def reset(self, seed=None):
        self.step_index = 0
        return np.zeros((2, 2), dtype=np.float32), {"state": np.zeros(3, dtype=np.float32)}

    def step(self, action):
        self.step_index += 1
        done = self.step_index == 3
        obs = np.full((2, 2), self.step_index, dtype=np.float32)
        info = {
            "next_state": np.full(3, self.step_index, dtype=np.float32),
            "coverage": 1.0 if self.step_index >= 2 else 0.0,
            "throughput": float(self.step_index),
        }
        return obs, np.asarray([1.0, 1.0]), done, False, info


class DummyEncoder:
    encoder_hash = "frozen-encoder"

    def encode_numpy(self, state, joint_obs):
        return np.asarray([np.mean(state), np.mean(joint_obs)], dtype=np.float32)


class DummyPolicy:
    n_agents = 2
    action_dim = 3
    action_space_type = "discrete"
    policy_mode = "stochastic"

    def __init__(self):
        self.transitions: list[Transition] = []

    def reset(self, seed: int) -> None:
        self.transitions.clear()

    def act(self, obs, state, step: int):
        return np.asarray([step % 3, (step + 1) % 3])

    def observe(self, transition: Transition) -> None:
        self.transitions.append(transition)


def test_collect_episode_records_real_transitions_and_external_health():
    policy = DummyPolicy()
    record = collect_episode(
        env=DummyEnv(),
        policy=policy,
        encoder=DummyEncoder(),
        episode_id="episode-17",
        source_checkpoint="healthy.pt",
        seed=17,
        max_steps=10,
        health_reader=lambda info: {
            "coverage": float(info.get("coverage", 0.0)),
            "throughput": float(info.get("throughput", 0.0)),
        },
    )

    assert record.latent.shape == (4, 2)
    assert record.actions.shape == (3, 6)
    assert record.dones.tolist() == [False, False, True]
    assert record.health["external_return"] == 6.0
    assert record.health["coverage_positive_step_fraction"] == 2.0 / 3.0
    assert record.health["zero_throughput_step_fraction"] == 0.0
    assert len(policy.transitions) == 3
```

- [ ] **Step 2: Run the test and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_collector.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog.collector'`.

- [ ] **Step 3: Implement the pure episode collector**

Create `csog/collector.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

import numpy as np

from csog.trajectory import TrajectoryRecord, encode_joint_action


@dataclass(frozen=True)
class Transition:
    obs: np.ndarray
    state: np.ndarray
    action: np.ndarray
    reward: np.ndarray
    next_obs: np.ndarray
    next_state: np.ndarray
    terminated: bool
    truncated: bool
    info: Mapping[str, Any]
    step: int


class EpisodePolicy(Protocol):
    n_agents: int
    action_dim: int
    action_space_type: str
    policy_mode: str

    def reset(self, seed: int) -> None: ...

    def act(self, obs: np.ndarray, state: np.ndarray, step: int) -> np.ndarray: ...

    def observe(self, transition: Transition) -> None: ...


class InteractionEncoder(Protocol):
    encoder_hash: str

    def encode_numpy(self, state: np.ndarray, joint_obs: np.ndarray) -> np.ndarray: ...


def _state_from_info(info: Mapping[str, Any], fallback: np.ndarray) -> np.ndarray:
    value = info.get("next_state", info.get("state", fallback))
    return np.asarray(value, dtype=np.float32).reshape(-1)


def collect_episode(
    *,
    env: Any,
    policy: EpisodePolicy,
    encoder: InteractionEncoder,
    episode_id: str,
    source_checkpoint: str,
    seed: int,
    max_steps: int,
    health_reader: Callable[[Mapping[str, Any]], Mapping[str, float]],
) -> TrajectoryRecord:
    obs, info = env.reset(seed=int(seed))
    info = info if isinstance(info, Mapping) else {}
    obs = np.asarray(obs, dtype=np.float32)
    state = _state_from_info(info, obs.reshape(-1))
    policy.reset(int(seed))

    latent = [encoder.encode_numpy(state, obs)]
    actions: list[np.ndarray] = []
    dones: list[bool] = []
    external_return = 0.0
    coverage_positive = 0
    zero_throughput = 0

    for step in range(int(max_steps)):
        action = np.asarray(policy.act(obs, state, step))
        next_obs, reward, terminated, truncated, next_info = env.step(action)
        next_info = next_info if isinstance(next_info, Mapping) else {}
        next_obs = np.asarray(next_obs, dtype=np.float32)
        next_state = _state_from_info(next_info, state)
        reward_vector = np.asarray(reward, dtype=np.float32).reshape(-1)
        done = bool(terminated or truncated)

        policy.observe(
            Transition(
                obs=obs.copy(),
                state=state.copy(),
                action=action.copy(),
                reward=reward_vector.copy(),
                next_obs=next_obs.copy(),
                next_state=next_state.copy(),
                terminated=bool(terminated),
                truncated=bool(truncated),
                info=next_info,
                step=int(step),
            )
        )
        actions.append(
            encode_joint_action(
                action,
                n_agents=policy.n_agents,
                action_dim=policy.action_dim,
                action_space_type=policy.action_space_type,
            )
        )
        dones.append(done)
        latent.append(encoder.encode_numpy(next_state, next_obs))
        external_return += float(np.sum(reward_vector))
        metrics = health_reader(next_info)
        coverage = float(metrics.get("coverage", metrics.get("coverage_ratio", 0.0)))
        throughput = float(
            metrics.get("throughput", metrics.get("system_throughput_mbps", 0.0))
        )
        coverage_positive += int(coverage > 1e-6)
        zero_throughput += int(throughput <= 1e-6)
        obs, state = next_obs, next_state
        if done:
            break

    count = len(actions)
    if count == 0:
        raise ValueError("environment produced no transitions")
    record = TrajectoryRecord(
        latent=np.asarray(latent, dtype=np.float32),
        actions=np.asarray(actions, dtype=np.float32),
        dones=np.asarray(dones, dtype=np.bool_),
        episode_id=str(episode_id),
        source_checkpoint=str(source_checkpoint),
        encoder_hash=str(encoder.encoder_hash),
        seed=int(seed),
        policy_mode=str(policy.policy_mode),
        action_encoding="discrete_one_hot",
        n_agents=int(policy.n_agents),
        health={
            "external_return": external_return,
            "coverage_positive_step_fraction": coverage_positive / count,
            "zero_throughput_step_fraction": zero_throughput / count,
        },
    )
    record.validate()
    return record
```

- [ ] **Step 4: Run the pure collector test**

Run:

```powershell
pytest tests/csog/test_collector.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Implement the temporary healthy-checkpoint export script**

Create `scripts/export_csog_g0.py` with this structure. Keep every legacy import in this script:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from csog.collector import Transition, collect_episode
from csog.recognition import OPTTargetEncoder, load_target_opt_encoder
from csog.trajectory import write_trajectory
from ha_ctse_process.export_substrate_gate import (
    _build_agent_for_checkpoint,
    _ensure_training_override_defaults,
    _reward_info,
    _reward_vector,
    _state_info,
)
from ha_ctse_process.plotting import extract_uav_metrics
from ha_ctse_process.standalone_agent import SegmentManager
from ha_ctse_process.train import apply_standalone_overrides, create_env, load_config


class FrozenEncoderAdapter:
    def __init__(self, encoder: OPTTargetEncoder, agent) -> None:
        self.encoder = encoder
        self.agent = agent
        self.encoder_hash = encoder.encoder_hash

    def encode_numpy(self, state, joint_obs) -> np.ndarray:
        fitted_obs = self.agent._joint_obs_array(joint_obs)
        fitted_state = self.agent._state_array(state, fitted_obs)
        return self.encoder.encode_numpy(fitted_state, fitted_obs)


class LegacyPolicyAdapter:
    def __init__(self, agent, *, skill_interval: int, policy_mode: str) -> None:
        self.agent = agent
        self.skill_interval = int(skill_interval)
        self.policy_mode = str(policy_mode)
        self.n_agents = int(agent.n_agents)
        self.action_dim = int(agent.action_dim)
        self.action_space_type = str(agent.action_space_type)
        if self.action_space_type != "discrete":
            raise ValueError("CSOG G0 Phase A currently requires a discrete action space")

    def reset(self, seed: int) -> None:
        self.agent.reset_env_state(0)
        self.agent.segments = SegmentManager(1, self.agent.n_agents)

    def act(self, obs, state, step: int) -> np.ndarray:
        deterministic = self.policy_mode == "deterministic"
        self.agent.maybe_assign_skills(
            obs,
            state=state,
            step=int(step),
            k=self.skill_interval,
            env_id=0,
            deterministic=deterministic,
        )
        actions, _logp, _values = self.agent.act_low(
            obs,
            env_id=0,
            deterministic=deterministic,
            state=state,
        )
        return np.asarray(actions)

    def observe(self, transition: Transition) -> None:
        info = dict(transition.info)
        self.agent.segments.append(
            env_id=0,
            obs=transition.obs,
            actions=transition.action,
            rewards=_reward_vector(transition.reward, self.n_agents),
            next_obs=transition.next_obs,
            rollout_idx=transition.step,
            reward_info=_reward_info(info),
            state_info=_state_info(info),
            next_state=transition.next_state,
            done=bool(transition.terminated or transition.truncated),
            pre_state_info={},
            pre_reward_info={},
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export real trajectories for CSOG G0.")
    parser.add_argument("--policy_checkpoint", required=True)
    parser.add_argument("--target_encoder_checkpoint", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=17000)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--max_steps", type=int, default=500)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--policy_mode", choices=("deterministic", "stochastic"), default="stochastic")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _ensure_training_override_defaults(args)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for CSOG G0 export but is unavailable")
    if args.episodes < 1 or args.max_steps < 51:
        raise ValueError("export requires at least one episode and max_steps >= 51")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(output_dir.glob("episode_*.npz"))
    if existing and not args.overwrite:
        raise FileExistsError(f"trajectory shards already exist in {output_dir}")
    if args.overwrite:
        for path in existing:
            path.unlink()

    checkpoint = Path(args.policy_checkpoint)
    encoder_checkpoint = Path(args.target_encoder_checkpoint)
    config = load_config(args.config, args.preset or None)
    config.scenario = str(args.scenario)
    apply_standalone_overrides(config, args)
    agent, total_steps, update_idx = _build_agent_for_checkpoint(config, args, checkpoint)
    for module_name in ("high", "low", "compact", "bridge"):
        getattr(agent, module_name).eval()
    encoder = load_target_opt_encoder(encoder_checkpoint, device=args.device)
    policy = LegacyPolicyAdapter(
        agent,
        skill_interval=args.skill_interval,
        policy_mode=args.policy_mode,
    )
    encoder_adapter = FrozenEncoderAdapter(encoder, agent)
    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="eval")
    try:
        for episode in range(args.episodes):
            episode_seed = int(args.seed) + episode
            record = collect_episode(
                env=env,
                policy=policy,
                encoder=encoder_adapter,
                episode_id=f"seed{episode_seed}-episode{episode:03d}",
                source_checkpoint=str(checkpoint.resolve()),
                seed=episode_seed,
                max_steps=args.max_steps,
                health_reader=lambda info: extract_uav_metrics(_reward_info(dict(info))),
            )
            write_trajectory(output_dir / f"episode_{episode:03d}.npz", record)
    finally:
        env.close()

    manifest = {
        "policy_checkpoint": str(checkpoint.resolve()),
        "target_encoder_checkpoint": str(encoder_checkpoint.resolve()),
        "encoder_hash": encoder.encoder_hash,
        "policy_total_steps": int(total_steps),
        "policy_update_idx": int(update_idx),
        "policy_mode": args.policy_mode,
        "episodes": int(args.episodes),
        "max_steps": int(args.max_steps),
        "reward_use": "external_health_logging_only",
        "world_model_inputs": ["frozen_opt_h", "encoded_joint_action"],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify script syntax and imports without collecting an episode**

Run:

```powershell
python -m py_compile scripts/export_csog_g0.py csog/collector.py
python scripts/export_csog_g0.py --help
```

Expected: both commands exit `0`; help lists both checkpoint arguments and defaults to `--device cuda` and `--policy_mode stochastic`.

- [ ] **Step 7: Run the focused tests and commit**

Run:

```powershell
pytest tests/csog/test_trajectory.py tests/csog/test_recognition.py tests/csog/test_collector.py -q
```

Expected: `6 passed`.

Commit:

```powershell
git add csog/collector.py scripts/export_csog_g0.py tests/csog/test_collector.py
git commit -m "feat: export real CSOG G0 trajectories"
```

### Task 4: Episode Splits, Dynamics Windows, Nulls, And Data Validity

**Files:**
- Create: `csog/dynamics_data.py`
- Create: `tests/csog/test_dynamics_data.py`

**Interfaces:**
- Consumes: validated `TrajectoryRecord` objects from Task 3.
- Produces: `TrajectorySplit`, `LatentStandardizer`, `WindowBatch`, `DataValidity`, grouped splits, H50 windows, action-shuffle batches, and a machine-readable real/non-collapsed data precondition.

- [ ] **Step 1: Write failing split, window, and validity tests**

Create `tests/csog/test_dynamics_data.py`:

```python
import numpy as np

from csog.dynamics_data import (
    LatentStandardizer,
    build_windows,
    evaluate_data_validity,
    grouped_episode_split,
    shuffle_action_sequences,
)
from csog.trajectory import TrajectoryRecord


def make_records(count: int = 12, length: int = 60, collapsed: bool = False):
    records = []
    for episode in range(count):
        rng = np.random.default_rng(episode)
        actions = rng.integers(0, 2, size=(length, 4)).astype(np.float32)
        if collapsed:
            actions.fill(0.0)
        increments = actions[:, :2] * np.asarray([0.2, -0.1], dtype=np.float32)
        latent = np.concatenate(
            [np.zeros((1, 2), dtype=np.float32), np.cumsum(increments, axis=0)],
            axis=0,
        )
        if collapsed:
            latent.fill(0.0)
        records.append(
            TrajectoryRecord(
                latent=latent,
                actions=actions,
                dones=np.asarray([False] * (length - 1) + [True]),
                episode_id=f"episode-{episode:03d}",
                source_checkpoint="healthy.pt",
                encoder_hash="one-frozen-hash",
                seed=episode,
                policy_mode="stochastic",
                action_encoding="discrete_one_hot",
                n_agents=2,
                health={
                    "external_return": 1.0,
                    "coverage_positive_step_fraction": 0.5 if not collapsed else 0.0,
                    "zero_throughput_step_fraction": 0.2 if not collapsed else 1.0,
                },
            )
        )
    return records


def test_grouped_split_has_no_episode_overlap():
    split = grouped_episode_split(make_records(), seed=17)
    train_ids = {record.episode_id for record in split.train}
    val_ids = {record.episode_id for record in split.validation}
    test_ids = {record.episode_id for record in split.test}
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)
    assert train_ids | val_ids | test_ids == {f"episode-{index:03d}" for index in range(12)}


def test_windows_are_standardized_and_shuffle_moves_whole_action_sequences():
    records = make_records(count=4)
    scaler = LatentStandardizer.fit(records[:2])
    batch = build_windows(records, scaler=scaler, horizons=(10, 20, 50), stride=5)
    shuffled = shuffle_action_sequences(batch, seed=31)

    assert batch.h0.shape[1] == 2
    assert batch.actions.shape[1:] == (50, 4)
    assert batch.targets.shape[1:] == (50, 2)
    assert batch.horizons == (10, 20, 50)
    assert not np.array_equal(shuffled.actions, batch.actions)
    original_rows = {row.tobytes() for row in batch.actions}
    assert all(row.tobytes() in original_rows for row in shuffled.actions)
    np.testing.assert_array_equal(shuffled.targets, batch.targets)


def test_data_validity_rejects_collapsed_behavior_and_accepts_healthy_behavior():
    healthy = evaluate_data_validity(
        make_records(count=8),
        horizons=(10, 20, 50),
        stride=2,
        min_episodes=8,
        min_windows=40,
    )
    collapsed = evaluate_data_validity(
        make_records(count=8, collapsed=True),
        horizons=(10, 20, 50),
        stride=2,
        min_episodes=8,
        min_windows=40,
    )
    assert healthy.passed is True
    assert collapsed.passed is False
    assert "healthy_episode_fraction" in collapsed.failed_checks
    assert "active_action_feature_fraction" in collapsed.failed_checks
    assert "latent_variance_mean" in collapsed.failed_checks
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_dynamics_data.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog.dynamics_data'`.

- [ ] **Step 3: Implement grouped data preparation and validity checks**

Create `csog/dynamics_data.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from csog.trajectory import TrajectoryRecord


@dataclass(frozen=True)
class TrajectorySplit:
    train: tuple[TrajectoryRecord, ...]
    validation: tuple[TrajectoryRecord, ...]
    test: tuple[TrajectoryRecord, ...]


@dataclass(frozen=True)
class LatentStandardizer:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, records: Sequence[TrajectoryRecord]) -> "LatentStandardizer":
        if not records:
            raise ValueError("cannot fit latent standardizer without training records")
        values = np.concatenate([record.latent for record in records], axis=0).astype(np.float64)
        mean = values.mean(axis=0)
        scale = values.std(axis=0)
        scale = np.where(scale < 1e-6, 1.0, scale)
        return cls(mean=mean.astype(np.float32), scale=scale.astype(np.float32))

    def transform(self, values: np.ndarray) -> np.ndarray:
        return ((np.asarray(values, dtype=np.float32) - self.mean) / self.scale).astype(np.float32)


@dataclass(frozen=True)
class WindowBatch:
    h0: np.ndarray
    actions: np.ndarray
    targets: np.ndarray
    episode_ids: tuple[str, ...]
    start_steps: np.ndarray
    horizons: tuple[int, ...]

    def validate(self) -> None:
        count = self.h0.shape[0]
        max_horizon = max(self.horizons)
        if self.h0.ndim != 2:
            raise ValueError("h0 must be rank two")
        if self.actions.ndim != 3 or self.actions.shape[:2] != (count, max_horizon):
            raise ValueError("actions must have shape [N, max_horizon, action_dim]")
        if self.targets.ndim != 3 or self.targets.shape[:2] != (count, max_horizon):
            raise ValueError("targets must have shape [N, max_horizon, latent_dim]")
        if self.targets.shape[2] != self.h0.shape[1]:
            raise ValueError("target latent width must match h0")
        if len(self.episode_ids) != count or self.start_steps.shape != (count,):
            raise ValueError("window metadata length mismatch")


@dataclass(frozen=True)
class DataValidity:
    passed: bool
    metrics: dict[str, float]
    failed_checks: tuple[str, ...]


def grouped_episode_split(
    records: Sequence[TrajectoryRecord],
    *,
    seed: int,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> TrajectorySplit:
    if len(records) < 5:
        raise ValueError("grouped split requires at least five episodes")
    ids = [record.episode_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("episode ids must be unique before splitting")
    rng = np.random.default_rng(int(seed))
    order = rng.permutation(len(records))
    train_count = max(1, int(np.floor(len(records) * float(train_fraction))))
    validation_count = max(1, int(np.floor(len(records) * float(validation_fraction))))
    if train_count + validation_count >= len(records):
        validation_count = 1
        train_count = len(records) - 2
    train_indices = order[:train_count]
    val_indices = order[train_count : train_count + validation_count]
    test_indices = order[train_count + validation_count :]
    return TrajectorySplit(
        train=tuple(records[index] for index in train_indices),
        validation=tuple(records[index] for index in val_indices),
        test=tuple(records[index] for index in test_indices),
    )


def build_windows(
    records: Sequence[TrajectoryRecord],
    *,
    scaler: LatentStandardizer,
    horizons: tuple[int, ...] = (10, 20, 50),
    stride: int = 5,
) -> WindowBatch:
    if tuple(sorted(set(horizons))) != horizons or horizons[0] <= 0:
        raise ValueError("horizons must be positive, unique, and sorted")
    if stride <= 0:
        raise ValueError("stride must be positive")
    hashes = {record.encoder_hash for record in records}
    if len(hashes) != 1:
        raise ValueError("one window batch must use exactly one frozen encoder hash")
    max_horizon = max(horizons)
    h0_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    target_rows: list[np.ndarray] = []
    episode_ids: list[str] = []
    start_steps: list[int] = []
    for record in records:
        transition_count = record.actions.shape[0]
        for start in range(0, transition_count - max_horizon + 1, int(stride)):
            stop = start + max_horizon
            h0_rows.append(scaler.transform(record.latent[start]))
            action_rows.append(record.actions[start:stop])
            target_rows.append(scaler.transform(record.latent[start + 1 : stop + 1]))
            episode_ids.append(record.episode_id)
            start_steps.append(start)
    if not h0_rows:
        raise ValueError("no complete dynamics windows were available")
    batch = WindowBatch(
        h0=np.asarray(h0_rows, dtype=np.float32),
        actions=np.asarray(action_rows, dtype=np.float32),
        targets=np.asarray(target_rows, dtype=np.float32),
        episode_ids=tuple(episode_ids),
        start_steps=np.asarray(start_steps, dtype=np.int64),
        horizons=tuple(int(value) for value in horizons),
    )
    batch.validate()
    return batch


def _sattolo_permutation(count: int, rng: np.random.Generator) -> np.ndarray:
    if count < 2:
        raise ValueError("action shuffle requires at least two windows")
    permutation = np.arange(count)
    for index in range(count - 1, 0, -1):
        other = int(rng.integers(0, index))
        permutation[index], permutation[other] = permutation[other], permutation[index]
    return permutation


def shuffle_action_sequences(batch: WindowBatch, *, seed: int) -> WindowBatch:
    permutation = _sattolo_permutation(batch.h0.shape[0], np.random.default_rng(int(seed)))
    shuffled = WindowBatch(
        h0=batch.h0.copy(),
        actions=batch.actions[permutation].copy(),
        targets=batch.targets.copy(),
        episode_ids=batch.episode_ids,
        start_steps=batch.start_steps.copy(),
        horizons=batch.horizons,
    )
    shuffled.validate()
    return shuffled


def evaluate_data_validity(
    records: Sequence[TrajectoryRecord],
    *,
    horizons: tuple[int, ...] = (10, 20, 50),
    stride: int = 5,
    min_episodes: int = 30,
    min_windows: int = 2000,
) -> DataValidity:
    if not records:
        return DataValidity(False, {"episodes": 0.0}, ("episodes",))
    max_horizon = max(horizons)
    windows = sum(
        max(0, 1 + (record.actions.shape[0] - max_horizon) // int(stride))
        for record in records
    )
    all_actions = np.concatenate([record.actions for record in records], axis=0)
    all_latent = np.concatenate([record.latent for record in records], axis=0)
    action_variance = np.var(all_actions.astype(np.float64), axis=0)
    healthy_episode_fraction = float(
        np.mean(
            [
                float(record.health.get("coverage_positive_step_fraction", 0.0)) >= 0.10
                for record in records
            ]
        )
    )
    metrics = {
        "episodes": float(len(records)),
        "complete_windows": float(windows),
        "encoder_hash_count": float(len({record.encoder_hash for record in records})),
        "healthy_episode_fraction": healthy_episode_fraction,
        "active_action_feature_fraction": float(np.mean(action_variance > 1e-6)),
        "latent_variance_mean": float(np.mean(np.var(all_latent.astype(np.float64), axis=0))),
    }
    checks = {
        "episodes": metrics["episodes"] >= int(min_episodes),
        "complete_windows": metrics["complete_windows"] >= int(min_windows),
        "encoder_hash_count": metrics["encoder_hash_count"] == 1.0,
        "healthy_episode_fraction": metrics["healthy_episode_fraction"] >= 0.25,
        "active_action_feature_fraction": metrics["active_action_feature_fraction"] >= 0.25,
        "latent_variance_mean": metrics["latent_variance_mean"] >= 1e-4,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return DataValidity(passed=not failed, metrics=metrics, failed_checks=failed)
```

- [ ] **Step 4: Run the dynamics-data tests**

Run:

```powershell
pytest tests/csog/test_dynamics_data.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit grouped dynamics data preparation**

```powershell
git add csog/dynamics_data.py tests/csog/test_dynamics_data.py
git commit -m "feat: prepare grouped CSOG dynamics windows"
```

### Task 5: Distributional Multi-Horizon Dynamics Ensemble

**Files:**
- Create: `csog/world_model.py`
- Create: `tests/csog/test_world_model.py`

**Interfaces:**
- Consumes: train and validation `WindowBatch` objects.
- Produces: `DynamicsFitConfig`, `GaussianLatentDynamics`, `FittedMember`, `EnsemblePrediction`, `fit_ensemble`, and `predict_ensemble` for both the real and shuffled variants.

- [ ] **Step 1: Write the failing distributional-model tests**

Create `tests/csog/test_world_model.py`:

```python
import numpy as np
import torch

from csog.dynamics_data import WindowBatch
from csog.world_model import (
    DynamicsFitConfig,
    GaussianLatentDynamics,
    fit_ensemble,
    predict_ensemble,
)


def make_batch(count: int, seed: int) -> WindowBatch:
    rng = np.random.default_rng(seed)
    h0 = rng.normal(size=(count, 2)).astype(np.float32)
    actions = rng.normal(size=(count, 5, 2)).astype(np.float32)
    targets = h0[:, None, :] + np.cumsum(actions * 0.25, axis=1)
    return WindowBatch(
        h0=h0,
        actions=actions,
        targets=targets.astype(np.float32),
        episode_ids=tuple(f"episode-{seed}-{index}" for index in range(count)),
        start_steps=np.zeros(count, dtype=np.int64),
        horizons=(1, 3, 5),
    )


def test_distributional_model_returns_mean_and_bounded_log_variance():
    model = GaussianLatentDynamics(latent_dim=3, action_dim=4, hidden_dim=16)
    mean, log_variance = model(torch.zeros(2, 3), torch.zeros(2, 5, 4))
    assert mean.shape == (2, 5, 3)
    assert log_variance.shape == (2, 5, 3)
    assert torch.all(log_variance >= -8.0)
    assert torch.all(log_variance <= 4.0)


def test_equal_budget_fit_returns_calibrated_ensemble_prediction():
    train = make_batch(96, seed=1)
    validation = make_batch(32, seed=2)
    config = DynamicsFitConfig(
        hidden_dim=16,
        learning_rate=1e-3,
        batch_size=32,
        max_epochs=25,
        patience=5,
        ensemble_size=2,
    )
    members = fit_ensemble(train, validation, config=config, device="cpu", seed=11)
    prediction = predict_ensemble(members, validation, device="cpu", batch_size=32)

    assert len(members) == 2
    assert prediction.mean.shape == validation.targets.shape
    assert prediction.variance.shape == validation.targets.shape
    assert np.all(prediction.variance > 0.0)
    assert all(np.isfinite(member.best_validation_nll) for member in members)
    assert all(0 <= member.best_epoch < config.max_epochs for member in members)
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_world_model.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog.world_model'`.

- [ ] **Step 3: Implement the recurrent Gaussian model and equal-budget trainer**

Create `csog/world_model.py`:

```python
from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from csog.dynamics_data import WindowBatch


@dataclass(frozen=True)
class DynamicsFitConfig:
    hidden_dim: int = 128
    learning_rate: float = 3e-4
    weight_decay: float = 1e-5
    batch_size: int = 256
    max_epochs: int = 200
    patience: int = 15
    min_delta: float = 1e-4
    grad_clip: float = 5.0
    ensemble_size: int = 5


@dataclass(frozen=True)
class FittedMember:
    model: "GaussianLatentDynamics"
    best_epoch: int
    best_validation_nll: float
    seed: int


@dataclass(frozen=True)
class EnsemblePrediction:
    mean: np.ndarray
    variance: np.ndarray
    member_means: np.ndarray


class GaussianLatentDynamics(nn.Module):
    def __init__(self, latent_dim: int, action_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.latent_dim = int(latent_dim)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.initial = nn.Sequential(
            nn.LayerNorm(self.latent_dim),
            nn.Linear(self.latent_dim, self.hidden_dim),
            nn.Tanh(),
        )
        self.state_features = nn.Sequential(
            nn.LayerNorm(self.latent_dim),
            nn.Linear(self.latent_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.action_features = nn.Sequential(
            nn.LayerNorm(self.action_dim),
            nn.Linear(self.action_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.cell = nn.GRUCell(self.hidden_dim * 2, self.hidden_dim)
        self.delta_head = nn.Linear(self.hidden_dim, self.latent_dim)
        self.log_variance_head = nn.Linear(self.hidden_dim, self.latent_dim)

    def forward(
        self,
        h0: torch.Tensor,
        actions: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if h0.ndim != 2 or actions.ndim != 3:
            raise ValueError("h0/actions must have ranks two and three")
        if h0.shape[0] != actions.shape[0]:
            raise ValueError("h0/actions batch sizes must match")
        hidden = self.initial(h0.float())
        current = h0.float()
        means = []
        log_variances = []
        for step in range(actions.shape[1]):
            recurrent_input = torch.cat(
                [self.state_features(current), self.action_features(actions[:, step].float())],
                dim=-1,
            )
            hidden = self.cell(recurrent_input, hidden)
            current = current + self.delta_head(hidden)
            means.append(current)
            log_variances.append(torch.clamp(self.log_variance_head(hidden), -8.0, 4.0))
        return torch.stack(means, dim=1), torch.stack(log_variances, dim=1)


def gaussian_nll(
    mean: torch.Tensor,
    log_variance: torch.Tensor,
    target: torch.Tensor,
) -> torch.Tensor:
    squared_error = torch.square(target.float() - mean)
    return 0.5 * (torch.exp(-log_variance) * squared_error + log_variance).mean()


def _device_or_raise(device: str) -> torch.device:
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for CSOG world-model fitting but is unavailable")
    return torch.device(device)


def _loader(
    batch: WindowBatch,
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
) -> DataLoader:
    dataset = TensorDataset(
        torch.from_numpy(batch.h0),
        torch.from_numpy(batch.actions),
        torch.from_numpy(batch.targets),
    )
    generator = torch.Generator().manual_seed(int(seed))
    return DataLoader(
        dataset,
        batch_size=int(batch_size),
        shuffle=bool(shuffle),
        generator=generator if shuffle else None,
        drop_last=False,
    )


@torch.no_grad()
def _mean_nll(
    model: GaussianLatentDynamics,
    loader: DataLoader,
    device: torch.device,
) -> float:
    model.eval()
    weighted = 0.0
    count = 0
    for h0, actions, targets in loader:
        h0, actions, targets = h0.to(device), actions.to(device), targets.to(device)
        mean, log_variance = model(h0, actions)
        loss = gaussian_nll(mean, log_variance, targets)
        weighted += float(loss.item()) * h0.shape[0]
        count += int(h0.shape[0])
    return weighted / max(count, 1)


def fit_member(
    train: WindowBatch,
    validation: WindowBatch,
    *,
    config: DynamicsFitConfig,
    device: str,
    seed: int,
) -> FittedMember:
    torch.manual_seed(int(seed))
    target_device = _device_or_raise(device)
    model = GaussianLatentDynamics(
        latent_dim=train.h0.shape[1],
        action_dim=train.actions.shape[2],
        hidden_dim=config.hidden_dim,
    ).to(target_device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    train_loader = _loader(
        train,
        batch_size=config.batch_size,
        shuffle=True,
        seed=seed,
    )
    validation_loader = _loader(
        validation,
        batch_size=config.batch_size,
        shuffle=False,
        seed=seed,
    )
    best_state = copy.deepcopy(model.state_dict())
    best_epoch = 0
    best_validation = float("inf")
    stale_epochs = 0
    for epoch in range(config.max_epochs):
        model.train()
        for h0, actions, targets in train_loader:
            h0, actions, targets = h0.to(target_device), actions.to(target_device), targets.to(target_device)
            mean, log_variance = model(h0, actions)
            loss = gaussian_nll(mean, log_variance, targets)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
            optimizer.step()
        validation_nll = _mean_nll(model, validation_loader, target_device)
        if validation_nll < best_validation - config.min_delta:
            best_validation = validation_nll
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= config.patience:
            break
    model.load_state_dict(best_state)
    model.eval()
    return FittedMember(
        model=model,
        best_epoch=int(best_epoch),
        best_validation_nll=float(best_validation),
        seed=int(seed),
    )


def fit_ensemble(
    train: WindowBatch,
    validation: WindowBatch,
    *,
    config: DynamicsFitConfig,
    device: str,
    seed: int,
) -> tuple[FittedMember, ...]:
    train.validate()
    validation.validate()
    if train.h0.shape[1:] != validation.h0.shape[1:]:
        raise ValueError("train and validation latent widths differ")
    return tuple(
        fit_member(
            train,
            validation,
            config=config,
            device=device,
            seed=int(seed) + member_index * 1009,
        )
        for member_index in range(config.ensemble_size)
    )


@torch.no_grad()
def predict_ensemble(
    members: tuple[FittedMember, ...],
    batch: WindowBatch,
    *,
    device: str,
    batch_size: int,
) -> EnsemblePrediction:
    if not members:
        raise ValueError("ensemble must contain at least one fitted member")
    target_device = _device_or_raise(device)
    loader = _loader(batch, batch_size=batch_size, shuffle=False, seed=0)
    member_means = []
    member_variances = []
    for fitted in members:
        fitted.model.to(target_device).eval()
        mean_parts = []
        variance_parts = []
        for h0, actions, _targets in loader:
            mean, log_variance = fitted.model(h0.to(target_device), actions.to(target_device))
            mean_parts.append(mean.cpu().numpy())
            variance_parts.append(torch.exp(log_variance).cpu().numpy())
        member_means.append(np.concatenate(mean_parts, axis=0))
        member_variances.append(np.concatenate(variance_parts, axis=0))
    means = np.asarray(member_means, dtype=np.float32)
    aleatoric = np.asarray(member_variances, dtype=np.float32)
    predictive_mean = means.mean(axis=0)
    predictive_variance = means.var(axis=0) + aleatoric.mean(axis=0)
    return EnsemblePrediction(
        mean=predictive_mean.astype(np.float32),
        variance=np.maximum(predictive_variance, 1e-8).astype(np.float32),
        member_means=means,
    )
```

- [ ] **Step 4: Run the world-model tests**

Run:

```powershell
pytest tests/csog/test_world_model.py -q
```

Expected: `2 passed` in under 30 seconds on CPU.

- [ ] **Step 5: Commit the distributional ensemble**

```powershell
git add csog/world_model.py tests/csog/test_world_model.py
git commit -m "feat: add CSOG distributional dynamics ensemble"
```

### Task 6: Registered G0 Metrics, Decision, And Analysis CLI

**Files:**
- Create: `csog/g0.py`
- Create: `scripts/analyze_csog_g0.py`
- Create: `tests/csog/test_g0.py`

**Interfaces:**
- Consumes: frozen test `WindowBatch`, real and shuffled `EnsemblePrediction`, and `DataValidity`.
- Produces: deterministic `G0Metrics`, `G0Decision`, JSON/Markdown reports, frozen model artifacts, split manifest, and a CLI that treats scientific `FAIL` as a valid completed analysis.

- [ ] **Step 1: Write the failing gate tests**

Create `tests/csog/test_g0.py`:

```python
from pathlib import Path

import numpy as np

from csog.dynamics_data import DataValidity, WindowBatch
from csog.g0 import compute_g0_metrics, decide_g0, write_g0_report
from csog.world_model import EnsemblePrediction


def test_g0_passes_only_when_all_horizons_and_calibration_pass(tmp_path: Path):
    count = 20
    targets = np.full((count, 50, 1), 2.0, dtype=np.float32)
    h0 = np.zeros((count, 1), dtype=np.float32)
    actions = np.zeros((count, 50, 2), dtype=np.float32)
    batch = WindowBatch(
        h0=h0,
        actions=actions,
        targets=targets,
        episode_ids=tuple(f"episode-{index}" for index in range(count)),
        start_steps=np.zeros(count, dtype=np.int64),
        horizons=(10, 20, 50),
    )
    error = np.linspace(0.05, 0.5, count, dtype=np.float32).reshape(count, 1, 1)
    real_mean = targets + np.broadcast_to(error, targets.shape)
    real_variance = np.broadcast_to(np.square(error) + 0.01, targets.shape).copy()
    shuffle_mean = targets + 1.0
    real = EnsemblePrediction(real_mean, real_variance, real_mean[None, ...])
    shuffled = EnsemblePrediction(
        shuffle_mean,
        np.ones_like(targets),
        shuffle_mean[None, ...],
    )
    validity = DataValidity(
        passed=True,
        metrics={"episodes": 64.0, "complete_windows": 5000.0},
        failed_checks=(),
    )

    metrics = compute_g0_metrics(batch, real, shuffled, data_validity=validity)
    decision = decide_g0(metrics)

    assert decision.status == "PASS"
    assert all(decision.checks.values())
    assert metrics.h50_improvement_vs_best_null >= 0.10
    assert metrics.uncertainty_error_spearman >= 0.3
    write_g0_report(tmp_path, metrics, decision)
    assert (tmp_path / "g0_metrics.json").exists()
    assert "G0 status: PASS" in (tmp_path / "g0_report.md").read_text(encoding="utf-8")


def test_invalid_dataset_cannot_pass_even_with_good_predictions():
    targets = np.ones((4, 50, 1), dtype=np.float32)
    batch = WindowBatch(
        h0=np.zeros((4, 1), dtype=np.float32),
        actions=np.zeros((4, 50, 1), dtype=np.float32),
        targets=targets,
        episode_ids=("a", "b", "c", "d"),
        start_steps=np.zeros(4, dtype=np.int64),
        horizons=(10, 20, 50),
    )
    perfect = EnsemblePrediction(targets, np.ones_like(targets), targets[None, ...])
    null = EnsemblePrediction(targets + 1.0, np.ones_like(targets), (targets + 1.0)[None, ...])
    invalid = DataValidity(False, {"episodes": 4.0}, ("episodes",))
    decision = decide_g0(compute_g0_metrics(batch, perfect, null, data_validity=invalid))
    assert decision.status == "INVALID"
    assert decision.checks["data_validity"] is False
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```powershell
pytest tests/csog/test_g0.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'csog.g0'`.

- [ ] **Step 3: Implement metrics, rank calibration, and exact gate logic**

Create `csog/g0.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from csog.dynamics_data import DataValidity, WindowBatch
from csog.world_model import EnsemblePrediction


@dataclass(frozen=True)
class G0Metrics:
    real_mse: dict[int, float]
    persistence_mse: dict[int, float]
    shuffled_mse: dict[int, float]
    uncertainty_error_spearman_by_horizon: dict[int, float]
    uncertainty_error_spearman: float
    h50_improvement_vs_best_null: float
    data_validity: DataValidity


@dataclass(frozen=True)
class G0Decision:
    status: str
    checks: dict[str, bool]
    failed_checks: tuple[str, ...]


def _average_ranks(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=np.float64)
    start = 0
    while start < values.size:
        stop = start + 1
        while stop < values.size and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def spearman_rank(values_a: np.ndarray, values_b: np.ndarray) -> float:
    first = _average_ranks(values_a)
    second = _average_ranks(values_b)
    if first.size < 2 or np.std(first) < 1e-12 or np.std(second) < 1e-12:
        return 0.0
    return float(np.corrcoef(first, second)[0, 1])


def _episode_means(values: np.ndarray, episode_ids: tuple[str, ...]) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    ids = np.asarray(episode_ids)
    if values.size != ids.size:
        raise ValueError("one episode id is required per held-out window")
    return np.asarray(
        [np.mean(values[ids == episode_id]) for episode_id in sorted(set(episode_ids))],
        dtype=np.float64,
    )


def compute_g0_metrics(
    test: WindowBatch,
    real: EnsemblePrediction,
    shuffled: EnsemblePrediction,
    *,
    data_validity: DataValidity,
) -> G0Metrics:
    if real.mean.shape != test.targets.shape or shuffled.mean.shape != test.targets.shape:
        raise ValueError("prediction shapes must match held-out targets")
    if real.variance.shape != test.targets.shape:
        raise ValueError("real predictive variance must match held-out targets")
    real_mse: dict[int, float] = {}
    persistence_mse: dict[int, float] = {}
    shuffled_mse: dict[int, float] = {}
    rho_by_horizon: dict[int, float] = {}
    pooled_error = []
    pooled_uncertainty = []
    for horizon in test.horizons:
        index = int(horizon) - 1
        target = test.targets[:, index]
        real_error = np.mean(np.square(real.mean[:, index] - target), axis=-1)
        persistence_error = np.mean(np.square(test.h0 - target), axis=-1)
        shuffled_error = np.mean(np.square(shuffled.mean[:, index] - target), axis=-1)
        uncertainty = np.mean(real.variance[:, index], axis=-1)
        episode_real_error = _episode_means(real_error, test.episode_ids)
        episode_persistence_error = _episode_means(persistence_error, test.episode_ids)
        episode_shuffled_error = _episode_means(shuffled_error, test.episode_ids)
        episode_uncertainty = _episode_means(uncertainty, test.episode_ids)
        real_mse[int(horizon)] = float(np.mean(episode_real_error))
        persistence_mse[int(horizon)] = float(np.mean(episode_persistence_error))
        shuffled_mse[int(horizon)] = float(np.mean(episode_shuffled_error))
        rho_by_horizon[int(horizon)] = spearman_rank(
            episode_uncertainty,
            episode_real_error,
        )
        pooled_error.append(episode_real_error)
        pooled_uncertainty.append(episode_uncertainty)
    strongest_h50_null = min(persistence_mse[50], shuffled_mse[50])
    improvement = 1.0 - real_mse[50] / max(strongest_h50_null, 1e-12)
    return G0Metrics(
        real_mse=real_mse,
        persistence_mse=persistence_mse,
        shuffled_mse=shuffled_mse,
        uncertainty_error_spearman_by_horizon=rho_by_horizon,
        uncertainty_error_spearman=spearman_rank(
            np.concatenate(pooled_uncertainty),
            np.concatenate(pooled_error),
        ),
        h50_improvement_vs_best_null=float(improvement),
        data_validity=data_validity,
    )


def decide_g0(metrics: G0Metrics) -> G0Decision:
    checks = {
        "data_validity": bool(metrics.data_validity.passed),
        "beats_persistence_h10_h20_h50": all(
            metrics.real_mse[horizon] < metrics.persistence_mse[horizon]
            for horizon in (10, 20, 50)
        ),
        "beats_action_shuffle_h10_h20_h50": all(
            metrics.real_mse[horizon] < metrics.shuffled_mse[horizon]
            for horizon in (10, 20, 50)
        ),
        "h50_improvement_at_least_10pct": metrics.h50_improvement_vs_best_null >= 0.10,
        "uncertainty_error_spearman_at_least_0_3": metrics.uncertainty_error_spearman >= 0.30,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    if not checks["data_validity"]:
        status = "INVALID"
    else:
        status = "PASS" if not failed else "FAIL"
    return G0Decision(status=status, checks=checks, failed_checks=failed)


def _metrics_payload(metrics: G0Metrics, decision: G0Decision) -> dict:
    return {
        "gate": "G0",
        "status": decision.status,
        "checks": decision.checks,
        "failed_checks": list(decision.failed_checks),
        "real_mse": {str(key): value for key, value in metrics.real_mse.items()},
        "persistence_mse": {str(key): value for key, value in metrics.persistence_mse.items()},
        "shuffled_mse": {str(key): value for key, value in metrics.shuffled_mse.items()},
        "uncertainty_error_spearman_by_horizon": {
            str(key): value for key, value in metrics.uncertainty_error_spearman_by_horizon.items()
        },
        "uncertainty_error_spearman": metrics.uncertainty_error_spearman,
        "h50_improvement_vs_best_null": metrics.h50_improvement_vs_best_null,
        "data_validity": {
            "passed": metrics.data_validity.passed,
            "metrics": metrics.data_validity.metrics,
            "failed_checks": list(metrics.data_validity.failed_checks),
        },
    }


def write_g0_report(
    output_dir: str | Path,
    metrics: G0Metrics,
    decision: G0Decision,
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    payload = _metrics_payload(metrics, decision)
    (target / "g0_metrics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    rows = [
        "# CSOG G0 Dynamics Gate",
        "",
        f"G0 status: {decision.status}",
        "",
        "| Horizon | Real MSE | Persistence MSE | Action-shuffle MSE | Uncertainty/error rho |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for horizon in (10, 20, 50):
        rows.append(
            f"| H{horizon} | {metrics.real_mse[horizon]:.6g} | "
            f"{metrics.persistence_mse[horizon]:.6g} | "
            f"{metrics.shuffled_mse[horizon]:.6g} | "
            f"{metrics.uncertainty_error_spearman_by_horizon[horizon]:.4f} |"
        )
    rows.extend(
        [
            "",
            f"- H50 improvement versus best null: {metrics.h50_improvement_vs_best_null:.4f}",
            f"- Pooled uncertainty/error Spearman rho: {metrics.uncertainty_error_spearman:.4f}",
            f"- Data validity: {metrics.data_validity.passed}",
            f"- Failed checks: {', '.join(decision.failed_checks) if decision.failed_checks else 'none'}",
            "",
        ]
    )
    (target / "g0_report.md").write_text("\n".join(rows), encoding="utf-8")
```

- [ ] **Step 4: Run the gate tests**

Run:

```powershell
pytest tests/csog/test_g0.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Implement the one-shot analysis CLI**

Create `scripts/analyze_csog_g0.py`:

```python
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

from csog.dynamics_data import (
    LatentStandardizer,
    build_windows,
    evaluate_data_validity,
    grouped_episode_split,
    shuffle_action_sequences,
)
from csog.g0 import compute_g0_metrics, decide_g0, write_g0_report
from csog.trajectory import load_trajectories
from csog.world_model import DynamicsFitConfig, fit_ensemble, predict_ensemble


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fit and evaluate the CSOG G0 dynamics gate.")
    parser.add_argument("--trajectory_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--hidden_dim", type=int, default=128)
    parser.add_argument("--learning_rate", type=float, default=3e-4)
    parser.add_argument("--weight_decay", type=float, default=1e-5)
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--max_epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--ensemble_size", type=int, default=5)
    return parser.parse_args()


def _save_models(output_dir: Path, variant: str, members, config: DynamicsFitConfig) -> None:
    model_dir = output_dir / "models" / variant
    model_dir.mkdir(parents=True, exist_ok=True)
    for index, fitted in enumerate(members):
        torch.save(
            {
                "state_dict": fitted.model.state_dict(),
                "latent_dim": fitted.model.latent_dim,
                "action_dim": fitted.model.action_dim,
                "hidden_dim": fitted.model.hidden_dim,
                "seed": fitted.seed,
                "best_epoch": fitted.best_epoch,
                "best_validation_nll": fitted.best_validation_nll,
                "fit_config": asdict(config),
            },
            model_dir / f"member_{index:02d}.pt",
        )


def main() -> None:
    args = parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for CSOG G0 analysis but is unavailable")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = load_trajectories(args.trajectory_dir)
    validity = evaluate_data_validity(records, horizons=(10, 20, 50), stride=args.stride)
    (output_dir / "data_validity.json").write_text(
        json.dumps(
            {
                "passed": validity.passed,
                "metrics": validity.metrics,
                "failed_checks": list(validity.failed_checks),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if not validity.passed:
        raise RuntimeError(f"G0 dataset is invalid: {', '.join(validity.failed_checks)}")

    split = grouped_episode_split(records, seed=args.seed)
    split_payload = {
        "encoder_hash": records[0].encoder_hash,
        "train": [record.episode_id for record in split.train],
        "validation": [record.episode_id for record in split.validation],
        "test": [record.episode_id for record in split.test],
    }
    (output_dir / "split_manifest.json").write_text(
        json.dumps(split_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    scaler = LatentStandardizer.fit(split.train)
    np.savez_compressed(output_dir / "latent_standardizer.npz", mean=scaler.mean, scale=scaler.scale)
    train = build_windows(split.train, scaler=scaler, horizons=(10, 20, 50), stride=args.stride)
    validation = build_windows(
        split.validation,
        scaler=scaler,
        horizons=(10, 20, 50),
        stride=args.stride,
    )
    test = build_windows(split.test, scaler=scaler, horizons=(10, 20, 50), stride=args.stride)
    shuffled_train = shuffle_action_sequences(train, seed=args.seed + 101)
    shuffled_validation = shuffle_action_sequences(validation, seed=args.seed + 202)
    shuffled_test = shuffle_action_sequences(test, seed=args.seed + 303)

    config = DynamicsFitConfig(
        hidden_dim=args.hidden_dim,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        batch_size=args.batch_size,
        max_epochs=args.max_epochs,
        patience=args.patience,
        ensemble_size=args.ensemble_size,
    )
    real_members = fit_ensemble(
        train,
        validation,
        config=config,
        device=args.device,
        seed=args.seed,
    )
    shuffled_members = fit_ensemble(
        shuffled_train,
        shuffled_validation,
        config=config,
        device=args.device,
        seed=args.seed,
    )
    _save_models(output_dir, "real", real_members, config)
    _save_models(output_dir, "action_shuffle", shuffled_members, config)
    real_prediction = predict_ensemble(
        real_members,
        test,
        device=args.device,
        batch_size=args.batch_size,
    )
    shuffled_prediction = predict_ensemble(
        shuffled_members,
        shuffled_test,
        device=args.device,
        batch_size=args.batch_size,
    )
    np.savez_compressed(
        output_dir / "heldout_predictions.npz",
        episode_ids=np.asarray(test.episode_ids),
        start_steps=test.start_steps,
        targets=test.targets,
        real_mean=real_prediction.mean,
        real_variance=real_prediction.variance,
        shuffled_mean=shuffled_prediction.mean,
    )
    (output_dir / "fit_summary.json").write_text(
        json.dumps(
            {
                "fit_config": asdict(config),
                "real": [
                    {
                        "seed": member.seed,
                        "best_epoch": member.best_epoch,
                        "best_validation_nll": member.best_validation_nll,
                    }
                    for member in real_members
                ],
                "action_shuffle": [
                    {
                        "seed": member.seed,
                        "best_epoch": member.best_epoch,
                        "best_validation_nll": member.best_validation_nll,
                    }
                    for member in shuffled_members
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    metrics = compute_g0_metrics(
        test,
        real_prediction,
        shuffled_prediction,
        data_validity=validity,
    )
    decision = decide_g0(metrics)
    write_g0_report(output_dir, metrics, decision)
    print(json.dumps({"gate": "G0", "status": decision.status}, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify CLI syntax, help, and focused tests**

Run:

```powershell
python -m py_compile scripts/analyze_csog_g0.py csog/g0.py
python scripts/analyze_csog_g0.py --help
pytest tests/csog/test_g0.py tests/csog/test_world_model.py -q
```

Expected: compile/help commands exit `0`; pytest reports `4 passed`.

- [ ] **Step 7: Commit the registered gate analyzer**

```powershell
git add csog/g0.py scripts/analyze_csog_g0.py tests/csog/test_g0.py
git commit -m "feat: add registered CSOG G0 gate"
```

### Task 7: CUDA Runner, Real Checkpoint Smoke, And Final Verification

**Files:**
- Create: `scripts/run_csog_g0_cloud.sh`
- Create: `tests/csog/test_g0_runner_contract.py`

**Interfaces:**
- Consumes: the exporter and analyzer CLIs from Tasks 3 and 6 plus the known healthy checkpoint artifact.
- Produces: a self-contained CUDA-only runner and a verified Phase A implementation boundary. This task prepares but does not launch the full experiment.

- [ ] **Step 1: Write the failing runner contract test**

Create `tests/csog/test_g0_runner_contract.py`:

```python
from pathlib import Path


def test_g0_runner_is_cuda_only_and_uses_run_local_artifacts():
    script = Path("scripts/run_csog_g0_cloud.sh").read_text(encoding="utf-8")
    assert "logs/EXP-20260710-csog-g0-dynamics" in script
    assert "torch.cuda.is_available()" in script
    assert "scripts/export_csog_g0.py" in script
    assert "scripts/analyze_csog_g0.py" in script
    assert script.count("--device cuda") == 2
    assert "|| true" not in script
    assert "q_d" not in script
    assert "q_D" not in script
```

- [ ] **Step 2: Run the test and verify the missing runner failure**

Run:

```powershell
pytest tests/csog/test_g0_runner_contract.py -q
```

Expected: `FileNotFoundError` for `scripts/run_csog_g0_cloud.sh`.

- [ ] **Step 3: Implement the cloud CUDA runner**

Create `scripts/run_csog_g0_cloud.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT="${RUN_ROOT:-logs/EXP-20260710-csog-g0-dynamics}"
POLICY_CHECKPOINT="${POLICY_CHECKPOINT:-dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/qAon/seed1/r24_qd_null_control_seed1/standalone_process_core_final.pt}"
TARGET_ENCODER_CHECKPOINT="${TARGET_ENCODER_CHECKPOINT:-${POLICY_CHECKPOINT}}"
TRAJECTORY_DIR="${RUN_ROOT}/trajectories"
ANALYSIS_DIR="${RUN_ROOT}/analysis"
STATUS_FILE="${RUN_ROOT}/runner_status.txt"

mkdir -p "${TRAJECTORY_DIR}" "${ANALYSIS_DIR}"

on_exit() {
  code=$?
  if [[ ${code} -ne 0 ]]; then
    printf 'status=failed\nexit_code=%s\n' "${code}" > "${STATUS_FILE}"
  fi
}
trap on_exit EXIT

python - <<'PY'
import torch
if not torch.cuda.is_available():
    raise SystemExit("CUDA is required for the CSOG G0 runner")
print(torch.cuda.get_device_name(0))
PY

if [[ ! -f "${POLICY_CHECKPOINT}" ]]; then
  printf 'missing healthy policy checkpoint: %s\n' "${POLICY_CHECKPOINT}" >&2
  exit 2
fi
if [[ ! -f "${TARGET_ENCODER_CHECKPOINT}" ]]; then
  printf 'missing target encoder checkpoint: %s\n' "${TARGET_ENCODER_CHECKPOINT}" >&2
  exit 2
fi

printf 'status=collecting\n' > "${STATUS_FILE}"
python scripts/export_csog_g0.py \
  --policy_checkpoint "${POLICY_CHECKPOINT}" \
  --target_encoder_checkpoint "${TARGET_ENCODER_CHECKPOINT}" \
  --output_dir "${TRAJECTORY_DIR}" \
  --scenario energy \
  --seed 17000 \
  --episodes 64 \
  --max_steps 500 \
  --skill_interval 10 \
  --policy_mode stochastic \
  --device cuda \
  --overwrite \
  2>&1 | tee "${RUN_ROOT}/export.log"

printf 'status=analyzing\n' > "${STATUS_FILE}"
python scripts/analyze_csog_g0.py \
  --trajectory_dir "${TRAJECTORY_DIR}" \
  --output_dir "${ANALYSIS_DIR}" \
  --device cuda \
  --seed 17 \
  --stride 5 \
  --hidden_dim 128 \
  --learning_rate 3e-4 \
  --weight_decay 1e-5 \
  --batch_size 256 \
  --max_epochs 200 \
  --patience 15 \
  --ensemble_size 5 \
  2>&1 | tee "${RUN_ROOT}/analysis.log"

GATE_STATUS="$(python - "${ANALYSIS_DIR}/g0_metrics.json" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle)["status"])
PY
)"
printf 'status=complete\ngate=G0\ngate_status=%s\n' "${GATE_STATUS}" > "${STATUS_FILE}"
printf 'CSOG G0 complete: %s\n' "${GATE_STATUS}"
```

- [ ] **Step 4: Run the runner contract test**

Run:

```powershell
pytest tests/csog/test_g0_runner_contract.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Run a two-episode CUDA export smoke against the known healthy checkpoint**

First verify CUDA without falling back:

```powershell
python -c "import torch; assert torch.cuda.is_available(), 'CUDA required'; print(torch.cuda.get_device_name(0))"
```

Expected: exits `0` and prints the CUDA device. If the GPU is occupied, stop here and report the expected smoke cost instead of using CPU. The smoke is expected to take approximately 2-5 minutes on CUDA.

Then run:

```powershell
python scripts/export_csog_g0.py --policy_checkpoint "dist\logs_cloud_r24_frozen_qd_overnight_20260709_005624\qAon\seed1\r24_qd_null_control_seed1\standalone_process_core_final.pt" --target_encoder_checkpoint "dist\logs_cloud_r24_frozen_qd_overnight_20260709_005624\qAon\seed1\r24_qd_null_control_seed1\standalone_process_core_final.pt" --output_dir "logs\EXP-20260710-csog-g0-smoke\trajectories" --scenario energy --seed 17000 --episodes 2 --max_steps 64 --skill_interval 10 --policy_mode stochastic --device cuda --overwrite
```

Expected: exits `0`, writes exactly two `episode_*.npz` files plus `manifest.json`, and reports one encoder hash.

- [ ] **Step 6: Validate the smoke artifacts without fitting a gate model**

Run:

```powershell
python -c "from csog.trajectory import load_trajectories; rows=load_trajectories(r'logs\EXP-20260710-csog-g0-smoke\trajectories'); assert len(rows)==2; assert len({r.encoder_hash for r in rows})==1; assert all(r.actions.shape[0]>=51 for r in rows); print([(r.latent.shape, r.actions.shape, r.health) for r in rows])"
```

Expected: exits `0`; both records have `latent length = action length + 1`, at least 51 transitions, finite health metrics, and the same encoder hash. Do not lower full-run data-validity thresholds to make this smoke produce a G0 verdict.

- [ ] **Step 7: Run the complete Phase A test suite and boundary scans**

Run:

```powershell
pytest tests/csog -q
python -m py_compile csog/__init__.py csog/trajectory.py csog/recognition.py csog/collector.py csog/dynamics_data.py csog/world_model.py csog/g0.py scripts/export_csog_g0.py scripts/analyze_csog_g0.py
rg -n "ha_ctse_process|q_A|q_d|q_D|team_disc|assignment_actionability" csog
```

Expected:

- pytest reports `14 passed`;
- compilation exits `0`;
- `rg` returns no matches from `csog/` and exits `1` because the legacy boundary is script-only.

- [ ] **Step 8: Inspect the final Phase A diff and commit the runner**

Run:

```powershell
git diff --check
git status --short
git diff --name-only HEAD~6..HEAD
```

Expected: no whitespace errors; files are limited to `csog/`, `scripts/export_csog_g0.py`, `scripts/analyze_csog_g0.py`, `scripts/run_csog_g0_cloud.sh`, and `tests/csog/`. In particular, no legacy agent, trainer, configuration, or reward file appears.

Commit:

```powershell
git add scripts/run_csog_g0_cloud.sh tests/csog/test_g0_runner_contract.py
git commit -m "chore: add CSOG G0 CUDA runner"
```

## Full G0 Launch Handoff

The implementation phase ends before this command. After controller review, cloud packaging, commit, push, and explicit user authorization, the full diagnostic command is:

```bash
bash scripts/run_csog_g0_cloud.sh
```

Expected wall-clock cost on one cloud CUDA device:

- real trajectory collection: approximately 15-30 minutes;
- five-member real ensemble plus five-member action-shuffle ensemble: approximately 1-2 hours;
- total expected wall time: approximately 1.25-2.5 hours, recalibrated after the smoke.

Expected artifacts:

```text
logs/EXP-20260710-csog-g0-dynamics/
  runner_status.txt
  export.log
  analysis.log
  trajectories/
    manifest.json
    episode_000.npz ... episode_063.npz
  analysis/
    data_validity.json
    split_manifest.json
    latent_standardizer.npz
    heldout_predictions.npz
    fit_summary.json
    g0_metrics.json
    g0_report.md
    models/real/member_00.pt ... member_04.pt
    models/action_shuffle/member_00.pt ... member_04.pt
```

## Experiment Meaning

- **Hypothesis:** Frozen OPT interaction dynamics on real healthy-policy behavior are predictably action-conditioned and uncertainty-calibrated at H10/H20/H50.
- **Mechanism path:** Recognition substrate and training-only world model only. No operator, graph, duration, intrinsic reward, or credit-assignment mechanism is active.
- **Core MARL impact:** Reward-off diagnostic only. Policy, critic, optimizer, PPO advantages, collector semantics, and environment dynamics are unchanged.
- **Metrics/gates:** Data validity passes; real MSE beats persistence and action shuffle at H10/H20/H50; H50 MSE is at least 10% below the stronger null; pooled held-out uncertainty/error Spearman rho is at least 0.3.
- **Time cost/device:** Approximately 1.25-2.5 hours on one cloud CUDA GPU. No CPU fallback.
- **Decision tree:** `PASS` opens Phase B1 planning; `FAIL` stops CSOG operator/graph implementation; `INVALID` permits only data/instrument repair; `MIXED` is treated as `FAIL` for progression.
- **Do not change yet:** Do not implement operators, distillation, forced-operator rewards, graph policy, event scheduler, q_A/q_d/q_D, or 160k/320k training arms.
- **Status source:** The approved CSOG design, repository interface inspection, and the known qAon/seed1 checkpoint evidence in `memory/ExpRecord.md`. That legacy policy is only a healthy real-behavior generator; its task result and q_A history are not evidence for CSOG.

## Phase A Completion Criteria

Phase A implementation is complete when:

1. All 14 focused tests pass.
2. A real two-episode CUDA smoke produces valid, same-hash trajectory shards.
3. `csog/` has no import or semantic dependency on the legacy algorithm.
4. The runner fails rather than falling back when CUDA or the healthy checkpoint is absent.
5. The full run remains unlaunched until explicit authorization.
6. A reviewer can trace each G0 condition directly from `g0_metrics.json` and `g0_report.md`.

After a full run, a `PASS` authorizes writing the Phase B1 executable plan; it does not authorize operator reward, graph code, or scale-up by itself.
