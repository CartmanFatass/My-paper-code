# R12 Stage 1 Situation Hazard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reward-pure Round 12 mechanism: convert the validated OPT situation substrate (`omega_tau` / `compact c_tau`) into debounced situation labels and a default-off situation-change renewal path, without adding SEF/DADS rewards or communication-specific shaping.

**Architecture:** Stage 1 is split into a safe diagnostic layer and a default-off control layer. First, create pure kappa/debounce utilities and log situation-change diagnostics. Then add a small hazard policy that can be trained with task reward through PPO-style high-level returns, but keep the control path disabled unless explicitly requested. The first live control mode is reward-pure: situation changes can trigger high-level reconsideration, but no intrinsic reward is injected.

**Tech Stack:** Python 3.10, NumPy, PyTorch, existing `ha_ctse_process` standalone PPO/MAPPO stack, pytest.

---

## Scope Boundary

This plan implements only R12 Stage 1 infrastructure:

- allowed: `omega` / `compact` to `kappa` situation labels,
- allowed: debounced situation-change diagnostics,
- allowed: default-off hazard/renewal control driven by task returns,
- allowed: CSV/TensorBoard/plotting/smoke coverage,
- forbidden in this plan: SEF/DADS reward, target-situation commitment, co-edit AR, raw communication-metric reward, and direct low-level compact injection.

The substrate gate passed locally at:

```text
logs\r12_substrate_gate_local_duration_short_16env_compact_full\substrate_gate_report.json
```

This plan should still keep the long-run guardrail: before long Round 12 training, re-check HMASD current-env gap and repeat the substrate gate on a true 32env grid if available.

## File Structure

- Create `ha_ctse_process/situation_substrate.py`
  - Pure utilities for converting substrate observations to discrete `kappa`, debouncing labels, tracking dwell/change statistics, and computing unit-testable diagnostics.
- Create `ha_ctse_process/situation_hazard.py`
  - PyTorch hazard policy and small dataclasses for interval-level termination decisions. This file must not know about the energy environment.
- Modify `ha_ctse_process/standalone_agent.py`
  - Add per-env situation tracker state, segment metadata fields, diagnostic logging, and default-off hazard control wiring.
- Modify `ha_ctse_process/config.py`
  - Add default-off Stage 1 config knobs.
- Modify `ha_ctse_process/train.py`
  - Add CLI flags, manifest fields, TensorBoard metrics, and console fields.
- Modify `ha_ctse_process/plotting.py`
  - Add Stage 1 diagnostics to training plots.
- Modify `ha_ctse_process/smoke.py`
  - Add smoke assertions for reward-pure behavior and default-off safety.
- Create `tests/test_r12_situation_stage1.py`
  - Unit tests for pure kappa/debounce utilities and hazard policy behavior.
- Create `scripts/run_r12_stage1_local_cuda.ps1`
  - One-key local sanity runner with `diag_only`, `oracle_change`, and `learned_beta_small` arms.

---

### Task 1: Add Pure Situation Substrate Utilities

**Files:**
- Create: `ha_ctse_process/situation_substrate.py`
- Test: `tests/test_r12_situation_stage1.py`

- [ ] **Step 1: Write failing tests for kappa assignment and debouncing**

Create `tests/test_r12_situation_stage1.py` with this initial content:

```python
import numpy as np

from ha_ctse_process.situation_substrate import (
    SituationDebounceConfig,
    SituationDebouncer,
    assign_kappa_from_omega,
    compact_cluster_predict,
    kappa_transition_metrics,
)


def test_assign_kappa_from_omega_uses_argmax():
    omega = np.asarray([0.1, 0.7, 0.2], dtype=np.float32)
    assert assign_kappa_from_omega(omega) == 1


def test_compact_cluster_predict_nearest_centroid():
    compact = np.asarray([0.9, 0.1], dtype=np.float32)
    centroids = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    assert compact_cluster_predict(compact, centroids) == 1


def test_debouncer_requires_min_stable_count():
    debouncer = SituationDebouncer(SituationDebounceConfig(min_stable_count=2))
    out0 = debouncer.update(env_id=0, raw_kappa=1)
    out1 = debouncer.update(env_id=0, raw_kappa=2)
    out2 = debouncer.update(env_id=0, raw_kappa=2)
    assert out0.kappa == 1
    assert out1.kappa == 1
    assert out1.changed is False
    assert out2.kappa == 2
    assert out2.changed is True


def test_kappa_transition_metrics_reports_dwell_and_changes():
    kappas = np.asarray([1, 1, 1, 2, 2, 3], dtype=np.int64)
    metrics = kappa_transition_metrics(kappas)
    assert metrics["situation_change_rate"] == 2.0 / 5.0
    assert metrics["situation_median_dwell"] == 2.0
    assert metrics["situation_unique_kappa"] == 3.0
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py -q --basetemp .pytest_tmp_r12_stage1_task1
```

Expected:

```text
ModuleNotFoundError: No module named 'ha_ctse_process.situation_substrate'
```

- [ ] **Step 3: Implement pure substrate utilities**

Create `ha_ctse_process/situation_substrate.py`:

```python
"""Round-12 situation substrate utilities.

This module is pure Python/NumPy.  It converts validated OPT substrate outputs
into slow situation labels and diagnostics.  It must not depend on environment-
specific communication metrics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SituationDebounceConfig:
    min_stable_count: int = 2
    missing_kappa: int = -1


@dataclass(frozen=True)
class SituationState:
    env_id: int
    raw_kappa: int
    kappa: int
    previous_kappa: int
    stable_count: int
    changed: bool


def assign_kappa_from_omega(omega: np.ndarray, *, missing_kappa: int = -1) -> int:
    values = np.asarray(omega, dtype=np.float64).reshape(-1)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return int(missing_kappa)
    return int(np.argmax(values))


def compact_cluster_predict(
    compact: np.ndarray,
    centroids: np.ndarray,
    *,
    missing_kappa: int = -1,
) -> int:
    vector = np.asarray(compact, dtype=np.float64).reshape(-1)
    centers = np.asarray(centroids, dtype=np.float64)
    if vector.size == 0 or centers.ndim != 2 or centers.shape[0] == 0:
        return int(missing_kappa)
    if centers.shape[1] != vector.size:
        return int(missing_kappa)
    if not np.all(np.isfinite(vector)) or not np.all(np.isfinite(centers)):
        return int(missing_kappa)
    distances = np.sum((centers - vector[None, :]) ** 2, axis=1)
    return int(np.argmin(distances))


class SituationDebouncer:
    def __init__(self, config: SituationDebounceConfig | None = None):
        self.config = config or SituationDebounceConfig()
        self._current: dict[int, int] = {}
        self._candidate: dict[int, int] = {}
        self._count: dict[int, int] = {}

    def reset_env(self, env_id: int) -> None:
        env = int(env_id)
        self._current.pop(env, None)
        self._candidate.pop(env, None)
        self._count.pop(env, None)

    def update(self, *, env_id: int, raw_kappa: int) -> SituationState:
        env = int(env_id)
        raw = int(raw_kappa)
        previous = int(self._current.get(env, raw))
        if env not in self._current:
            self._current[env] = raw
            self._candidate[env] = raw
            self._count[env] = 1
            return SituationState(env, raw, raw, raw, 1, False)

        if raw == self._candidate.get(env):
            self._count[env] = int(self._count.get(env, 0)) + 1
        else:
            self._candidate[env] = raw
            self._count[env] = 1

        changed = False
        if (
            raw != self._current[env]
            and self._count[env] >= max(int(self.config.min_stable_count), 1)
        ):
            self._current[env] = raw
            changed = True

        return SituationState(
            env_id=env,
            raw_kappa=raw,
            kappa=int(self._current[env]),
            previous_kappa=previous,
            stable_count=int(self._count[env]),
            changed=bool(changed),
        )


def kappa_transition_metrics(kappas: np.ndarray) -> dict[str, float]:
    values = np.asarray(kappas, dtype=np.int64).reshape(-1)
    if values.size == 0:
        return {
            "situation_change_rate": 0.0,
            "situation_median_dwell": 0.0,
            "situation_unique_kappa": 0.0,
        }
    if values.size == 1:
        return {
            "situation_change_rate": 0.0,
            "situation_median_dwell": 1.0,
            "situation_unique_kappa": 1.0,
        }
    changes = values[1:] != values[:-1]
    boundaries = np.concatenate(([0], np.nonzero(changes)[0] + 1, [values.size]))
    dwell = np.diff(boundaries).astype(np.float64)
    return {
        "situation_change_rate": float(np.mean(changes)),
        "situation_median_dwell": float(np.median(dwell)) if dwell.size else 0.0,
        "situation_unique_kappa": float(np.unique(values).size),
    }
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py -q --basetemp .pytest_tmp_r12_stage1_task1
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit**

```bash
git add ha_ctse_process/situation_substrate.py tests/test_r12_situation_stage1.py
git commit -m "feat: add r12 situation substrate utilities"
```

---

### Task 2: Add Hazard Policy Module

**Files:**
- Create: `ha_ctse_process/situation_hazard.py`
- Modify: `tests/test_r12_situation_stage1.py`

- [ ] **Step 1: Add failing tests for hazard policy outputs**

Append to `tests/test_r12_situation_stage1.py`:

```python
import torch

from ha_ctse_process.situation_hazard import SituationHazardPolicy


def test_hazard_policy_shapes_and_logprob():
    policy = SituationHazardPolicy(
        obs_dim=4,
        n_skills=3,
        compact_dim=5,
        team_code_dim=2,
        n_kappa=4,
        hidden_dim=16,
    )
    obs = torch.zeros(6, 4)
    prev_skill = torch.zeros(6, dtype=torch.long)
    age = torch.ones(6)
    compact = torch.zeros(6, 5)
    team_vector = torch.zeros(6, 2)
    kappa = torch.zeros(6, dtype=torch.long)
    changed = torch.zeros(6)
    action, logp, entropy, value = policy.act(
        obs, prev_skill, age, compact, team_vector, kappa, changed
    )
    assert action.shape == (6,)
    assert logp.shape == (6,)
    assert entropy.shape == (6,)
    assert value.shape == (6,)
    eval_logp, eval_entropy, eval_value = policy.evaluate(
        obs, prev_skill, age, compact, team_vector, kappa, changed, action
    )
    assert eval_logp.shape == (6,)
    assert eval_entropy.shape == (6,)
    assert eval_value.shape == (6,)
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py::test_hazard_policy_shapes_and_logprob -q --basetemp .pytest_tmp_r12_stage1_task2
```

Expected:

```text
ModuleNotFoundError: No module named 'ha_ctse_process.situation_hazard'
```

- [ ] **Step 3: Implement `SituationHazardPolicy`**

Create `ha_ctse_process/situation_hazard.py`:

```python
"""Reward-pure situation-change hazard components for Round 12 Stage 1."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Bernoulli


@dataclass
class HazardDecision:
    env_id: int
    agent_id: int
    step: int
    kappa: int
    previous_kappa: int
    changed: bool
    prev_skill: int
    skill_age: int
    action: int
    logp: float
    value: float
    reward_start: int


class SituationHazardPolicy(nn.Module):
    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        compact_dim: int,
        team_code_dim: int,
        n_kappa: int,
        hidden_dim: int,
    ):
        super().__init__()
        self.n_skills = int(n_skills)
        self.n_kappa = int(max(n_kappa, 1))
        input_dim = obs_dim + n_skills + 1 + compact_dim + team_code_dim + self.n_kappa + 1
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.logit_head = nn.Linear(hidden_dim, 1)
        self.value_head = nn.Linear(hidden_dim, 1)

    def _features(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
    ) -> torch.Tensor:
        prev_onehot = F.one_hot(
            prev_skill.long().clamp(0, self.n_skills - 1),
            num_classes=self.n_skills,
        ).float()
        kappa_onehot = F.one_hot(
            kappa.long().clamp(0, self.n_kappa - 1),
            num_classes=self.n_kappa,
        ).float()
        age_feature = torch.log1p(age.float()).unsqueeze(-1) / 10.0
        changed_feature = changed.float().unsqueeze(-1)
        return self.net(torch.cat([
            obs.float(),
            prev_onehot,
            age_feature,
            compact.float(),
            team_vector.float(),
            kappa_onehot,
            changed_feature,
        ], dim=-1))

    def logits(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self._features(obs, prev_skill, age, compact, team_vector, kappa, changed)
        return self.logit_head(hidden).squeeze(-1), self.value_head(hidden).squeeze(-1)

    def act(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
        deterministic: bool = False,
    ):
        logits, value = self.logits(obs, prev_skill, age, compact, team_vector, kappa, changed)
        dist = Bernoulli(logits=logits)
        action = (torch.sigmoid(logits) >= 0.5).float() if deterministic else dist.sample()
        logp = dist.log_prob(action)
        entropy = dist.entropy()
        return action.long(), logp, entropy, value

    def evaluate(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
        action: torch.Tensor,
    ):
        logits, value = self.logits(obs, prev_skill, age, compact, team_vector, kappa, changed)
        dist = Bernoulli(logits=logits)
        action_f = action.float().clamp(0.0, 1.0)
        return dist.log_prob(action_f), dist.entropy(), value
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py -q --basetemp .pytest_tmp_r12_stage1_task2
```

Expected:

```text
5 passed
```

- [ ] **Step 5: Commit**

```bash
git add ha_ctse_process/situation_hazard.py tests/test_r12_situation_stage1.py
git commit -m "feat: add r12 situation hazard policy"
```

---

### Task 3: Add Default-Off Config and CLI

**Files:**
- Modify: `ha_ctse_process/config.py`
- Modify: `ha_ctse_process/train.py`
- Test: `tests/test_r12_situation_stage1.py`

- [ ] **Step 1: Add a failing config test**

Append to `tests/test_r12_situation_stage1.py`:

```python
from ha_ctse_process.config import Config


def test_r12_stage1_defaults_are_safe():
    cfg = Config()
    assert cfg.situation_substrate_source == "omega"
    assert cfg.enable_situation_diagnostics is False
    assert cfg.enable_situation_hazard_control is False
    assert cfg.situation_hazard_mode == "diagnostic"
    assert cfg.situation_hazard_reward_coef == 0.0
```

- [ ] **Step 2: Run the config test and verify it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py::test_r12_stage1_defaults_are_safe -q --basetemp .pytest_tmp_r12_stage1_task3
```

Expected:

```text
AttributeError: 'Config' object has no attribute 'situation_substrate_source'
```

- [ ] **Step 3: Add safe defaults to `Config`**

In `ha_ctse_process/config.py`, add this block near the Round 12 / high-level config area:

```python
    # Round 12 Stage 1: OPT situation substrate and reward-pure hazard renewal.
    # Safe by default: diagnostics and control are both off unless explicitly
    # requested.  This stage must not inject SEF/DADS or communication rewards.
    situation_substrate_source = "omega"  # omega, compact_cluster
    situation_num_kappa = 4
    situation_debounce_steps = 2
    enable_situation_diagnostics = False
    enable_situation_hazard_control = False
    situation_hazard_mode = "diagnostic"  # diagnostic, oracle_change, learned_beta
    situation_hazard_check_interval = 10
    situation_hazard_min_age = 1
    situation_hazard_hidden_dim = 128
    situation_hazard_entropy_coef = 0.005
    situation_hazard_value_coef = 0.5
    situation_hazard_clip_epsilon = 0.2
    situation_hazard_reward_coef = 0.0
```

- [ ] **Step 4: Add CLI parser args and config override plumbing**

In `ha_ctse_process/train.py`, add these parser args near existing algorithm flags:

```python
    parser.add_argument("--enable_situation_diagnostics", action="store_true")
    parser.add_argument("--enable_situation_hazard_control", action="store_true")
    parser.add_argument("--situation_substrate_source", choices=("omega", "compact_cluster"), default="")
    parser.add_argument("--situation_num_kappa", type=int, default=0)
    parser.add_argument("--situation_debounce_steps", type=int, default=0)
    parser.add_argument(
        "--situation_hazard_mode",
        choices=("diagnostic", "oracle_change", "learned_beta"),
        default="",
    )
    parser.add_argument("--situation_hazard_check_interval", type=int, default=0)
    parser.add_argument("--situation_hazard_min_age", type=int, default=0)
    parser.add_argument("--situation_hazard_hidden_dim", type=int, default=0)
    parser.add_argument("--situation_hazard_entropy_coef", type=float, default=None)
    parser.add_argument("--situation_hazard_reward_coef", type=float, default=None)
```

In the config-override section, add:

```python
    if args.enable_situation_diagnostics:
        config.enable_situation_diagnostics = True
    if args.enable_situation_hazard_control:
        config.enable_situation_hazard_control = True
    if args.situation_substrate_source:
        config.situation_substrate_source = args.situation_substrate_source
    if args.situation_hazard_mode:
        config.situation_hazard_mode = args.situation_hazard_mode
    for name in (
        "situation_num_kappa",
        "situation_debounce_steps",
        "situation_hazard_check_interval",
        "situation_hazard_min_age",
        "situation_hazard_hidden_dim",
    ):
        value = getattr(args, name, 0)
        if value:
            setattr(config, name, int(value))
    for name in (
        "situation_hazard_entropy_coef",
        "situation_hazard_reward_coef",
    ):
        value = getattr(args, name, None)
        if value is not None:
            setattr(config, name, float(value))
```

Add the new field names to the manifest/config lists where `train.py` serializes config values:

```python
    "situation_substrate_source",
    "situation_num_kappa",
    "situation_debounce_steps",
    "enable_situation_diagnostics",
    "enable_situation_hazard_control",
    "situation_hazard_mode",
    "situation_hazard_check_interval",
    "situation_hazard_min_age",
    "situation_hazard_hidden_dim",
    "situation_hazard_entropy_coef",
    "situation_hazard_reward_coef",
```

- [ ] **Step 5: Run tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py -q --basetemp .pytest_tmp_r12_stage1_task3
```

Expected:

```text
6 passed
```

- [ ] **Step 6: Commit**

```bash
git add ha_ctse_process/config.py ha_ctse_process/train.py tests/test_r12_situation_stage1.py
git commit -m "feat: add r12 situation stage1 config flags"
```

---

### Task 4: Wire Situation Diagnostics Into the Agent Without Control

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `ha_ctse_process/train.py`
- Modify: `ha_ctse_process/plotting.py`
- Test: `ha_ctse_process/smoke.py`

- [ ] **Step 1: Extend `Segment` metadata**

In `ha_ctse_process/standalone_agent.py`, extend the `Segment` dataclass:

```python
    kappa_start: int = -1
    kappa_end: int = -1
    raw_kappa_start: int = -1
    raw_kappa_end: int = -1
    situation_changed_during_segment: bool = False
```

- [ ] **Step 2: Initialize debouncer state**

Import utilities at the top:

```python
from ha_ctse_process.situation_substrate import (
    SituationDebounceConfig,
    SituationDebouncer,
    assign_kappa_from_omega,
)
```

In `StandaloneProcessAgent.__init__`, add:

```python
        self.enable_situation_diagnostics = bool(getattr(config, "enable_situation_diagnostics", False))
        self.enable_situation_hazard_control = bool(getattr(config, "enable_situation_hazard_control", False))
        self.situation_substrate_source = str(getattr(config, "situation_substrate_source", "omega"))
        self.situation_num_kappa = int(max(getattr(config, "situation_num_kappa", 4), 1))
        self.situation_debouncer = SituationDebouncer(
            SituationDebounceConfig(
                min_stable_count=int(max(getattr(config, "situation_debounce_steps", 2), 1))
            )
        )
        self._last_situation_state = [None for _ in range(self.num_envs)]
        self._situation_diag_events: list[dict[str, float]] = []
```

- [ ] **Step 3: Reset debouncer state on env reset**

In `reset_env_state`, add:

```python
        self.situation_debouncer.reset_env(env_id)
        self._last_situation_state[env_id] = None
```

In `reset_all_policy_state`, add:

```python
        self.situation_debouncer = SituationDebouncer(self.situation_debouncer.config)
        self._last_situation_state = [None for _ in range(self.num_envs)]
        self._situation_diag_events = []
```

- [ ] **Step 4: Add helper to compute current kappa**

Add this method inside `StandaloneProcessAgent`:

```python
    def _situation_state_from_context(self, env_id: int, weights: torch.Tensor):
        if not (self.enable_situation_diagnostics or self.enable_situation_hazard_control):
            return None
        omega = weights.detach().cpu().numpy().reshape(-1)
        raw_kappa = assign_kappa_from_omega(omega)
        state = self.situation_debouncer.update(env_id=env_id, raw_kappa=raw_kappa)
        self._last_situation_state[env_id] = state
        self._situation_diag_events.append({
            "kappa": float(state.kappa),
            "raw_kappa": float(state.raw_kappa),
            "changed": float(state.changed),
            "stable_count": float(state.stable_count),
        })
        return state
```

- [ ] **Step 5: Record kappa when renewing segments**

In `maybe_assign_skills`, when `_context_tensors(...)` returns `weights`, compute:

```python
            situation_state = self._situation_state_from_context(env_id, weights)
            kappa_value = int(situation_state.kappa) if situation_state is not None else -1
            raw_kappa_value = int(situation_state.raw_kappa) if situation_state is not None else -1
```

Pass these fields into `self.segments.renew(...)`:

```python
                    kappa_start=kappa_value,
                    raw_kappa_start=raw_kappa_value,
```

Then update `SegmentManager.renew` signature and constructor call to accept:

```python
        kappa_start: int = -1,
        raw_kappa_start: int = -1,
```

and set:

```python
            kappa_start=int(kappa_start),
            raw_kappa_start=int(raw_kappa_start),
```

- [ ] **Step 6: Add process metrics**

Where `process_update()` builds `process_metrics`, merge:

```python
        process_metrics.update(self._situation_diagnostics(valid))
```

Add this method:

```python
    def _situation_diagnostics(self, segments: list[Segment]) -> dict[str, float]:
        if not (self.enable_situation_diagnostics or self.enable_situation_hazard_control):
            return {
                "situation_enabled": 0.0,
                "situation_change_rate": 0.0,
                "situation_unique_kappa": 0.0,
                "situation_segment_change_frac": 0.0,
            }
        events = self._situation_diag_events
        changed = [row["changed"] for row in events]
        kappas = [row["kappa"] for row in events]
        segment_changed = [
            1.0 for s in segments
            if int(getattr(s, "kappa_start", -1)) >= 0
            and int(getattr(s, "kappa_end", getattr(s, "kappa_start", -1))) != int(getattr(s, "kappa_start", -1))
        ]
        metrics = {
            "situation_enabled": 1.0,
            "situation_change_rate": float(np.mean(changed)) if changed else 0.0,
            "situation_unique_kappa": float(len(set(int(v) for v in kappas))) if kappas else 0.0,
            "situation_segment_change_frac": float(np.mean(segment_changed)) if segment_changed else 0.0,
        }
        self._situation_diag_events = []
        return metrics
```

- [ ] **Step 7: Add train/TensorBoard/plot fields**

In `ha_ctse_process/train.py`, add TensorBoard scalars:

```python
    writer.add_scalar("Situation/Enabled", process_metrics.get("situation_enabled", 0.0), total_steps)
    writer.add_scalar("Situation/ChangeRate", process_metrics.get("situation_change_rate", 0.0), total_steps)
    writer.add_scalar("Situation/UniqueKappa", process_metrics.get("situation_unique_kappa", 0.0), total_steps)
    writer.add_scalar("Situation/SegmentChangeFrac", process_metrics.get("situation_segment_change_frac", 0.0), total_steps)
```

Ensure these fields are included in `train_updates.csv`:

```python
    "situation_enabled",
    "situation_change_rate",
    "situation_unique_kappa",
    "situation_segment_change_frac",
```

In `ha_ctse_process/plotting.py`, add these fields to the process diagnostics plot group:

```python
SITUATION_STAGE1_FIELDS = (
    "situation_change_rate",
    "situation_unique_kappa",
    "situation_segment_change_frac",
)
```

- [ ] **Step 8: Run a diagnostic-only smoke**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.smoke `
  --enable_situation_diagnostics `
  --total_timesteps 1024 `
  --num_envs 2 `
  --log_dir logs\ha_ctse_smoke_r12_stage1_diag
```

Expected:

```text
smoke passed
```

Then check:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -c "import csv; p=r'logs\ha_ctse_smoke_r12_stage1_diag\train_updates.csv'; rows=list(csv.DictReader(open(p, encoding='utf-8'))); print(rows[-1]['situation_enabled'], rows[-1]['situation_unique_kappa'])"
```

Expected:

```text
1.0 <non-negative number>
```

- [ ] **Step 9: Commit**

```bash
git add ha_ctse_process/standalone_agent.py ha_ctse_process/train.py ha_ctse_process/plotting.py ha_ctse_process/smoke.py
git commit -m "feat: log r12 situation diagnostics"
```

---

### Task 5: Add Default-Off Reward-Pure Situation Renewal Control

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `ha_ctse_process/situation_hazard.py`
- Modify: `ha_ctse_process/train.py`
- Test: `tests/test_r12_situation_stage1.py`

- [ ] **Step 1: Add tests for control mode selection**

Append to `tests/test_r12_situation_stage1.py`:

```python
from ha_ctse_process.situation_hazard import should_force_renewal


def test_oracle_change_requires_change_and_min_age():
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=5,
        min_age=2,
        hazard_action=0,
    ) is True
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=1,
        min_age=2,
        hazard_action=0,
    ) is False
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=False,
        skill_age=5,
        min_age=2,
        hazard_action=0,
    ) is False


def test_learned_beta_uses_hazard_action_and_min_age():
    assert should_force_renewal(
        mode="learned_beta",
        situation_changed=False,
        skill_age=5,
        min_age=2,
        hazard_action=1,
    ) is True
    assert should_force_renewal(
        mode="learned_beta",
        situation_changed=False,
        skill_age=1,
        min_age=2,
        hazard_action=1,
    ) is False
```

- [ ] **Step 2: Implement `should_force_renewal`**

In `ha_ctse_process/situation_hazard.py`, add:

```python
def should_force_renewal(
    *,
    mode: str,
    situation_changed: bool,
    skill_age: int,
    min_age: int,
    hazard_action: int,
) -> bool:
    if int(skill_age) < int(max(min_age, 0)):
        return False
    if mode == "oracle_change":
        return bool(situation_changed)
    if mode == "learned_beta":
        return bool(int(hazard_action) > 0)
    return False
```

- [ ] **Step 3: Instantiate hazard policy only when needed**

In `StandaloneProcessAgent.__init__`, import:

```python
from ha_ctse_process.situation_hazard import SituationHazardPolicy, should_force_renewal
```

Add:

```python
        self.situation_hazard_mode = str(getattr(config, "situation_hazard_mode", "diagnostic"))
        self.situation_hazard_min_age = int(max(getattr(config, "situation_hazard_min_age", 1), 0))
        self.situation_hazard_entropy_coef = float(getattr(config, "situation_hazard_entropy_coef", 0.005))
        self.situation_hazard_reward_coef = float(getattr(config, "situation_hazard_reward_coef", 0.0))
        if self.enable_situation_hazard_control and self.situation_hazard_mode == "learned_beta":
            self.situation_hazard = SituationHazardPolicy(
                obs_dim=self.obs_dim,
                n_skills=self.n_skills,
                compact_dim=self.compact_dim,
                team_code_dim=self.team_code_dim,
                n_kappa=self.situation_num_kappa,
                hidden_dim=int(getattr(config, "situation_hazard_hidden_dim", 128)),
            ).to(self.device)
            self.high_opt.add_param_group({"params": self.situation_hazard.parameters()})
        else:
            self.situation_hazard = None
```

- [ ] **Step 4: Apply safe renewal control before high-level assignment**

In `maybe_assign_skills`, compute context when either agents expired or situation diagnostics/control is enabled:

```python
        needs_context = bool(np.any(expired) or self.enable_situation_diagnostics or self.enable_situation_hazard_control)
        situation_state = None
        if needs_context:
            compact, team_code, team_vector, team_logp, team_entropy, _cd, _cmi, _agg = self._context_tensors(
                state_arr,
                joint_obs,
                deterministic=deterministic,
            )
            situation_state = self._situation_state_from_context(env_id, _agg if False else weights)
```

Do not use the literal `_agg if False else weights` expression.  Instead, keep the existing `_context_tensors` return variable named `weights`:

```python
            compact, team_code, team_vector, team_logp, team_entropy, cd_loss, cmi_loss, aggregation_entropy, weights = ...
```

To support that, update `_context_tensors` so it returns `weights` as the last value:

```python
        return compact, team_code, team_vector, team_logp, team_entropy, cd_loss, cmi_loss, aggregation_entropy, weights
```

Then, before computing `expired_ids`, add:

```python
        if self.enable_situation_hazard_control and situation_state is not None:
            changed = bool(situation_state.changed)
            for agent_id in range(self.n_agents):
                if not self.has_active_skill[env_id, agent_id]:
                    continue
                hazard_action = 0
                if self.situation_hazard is not None:
                    obs_t = torch.as_tensor(joint_obs[agent_id:agent_id + 1], dtype=torch.float32, device=self.device)
                    prev_t = torch.as_tensor([self.active_skills[env_id, agent_id]], dtype=torch.long, device=self.device)
                    age_t = torch.as_tensor([self.skill_age[env_id, agent_id]], dtype=torch.float32, device=self.device)
                    compact_t = compact.expand(1, -1)
                    team_vector_t = team_vector.expand(1, -1)
                    kappa_t = torch.as_tensor([max(int(situation_state.kappa), 0)], dtype=torch.long, device=self.device)
                    changed_t = torch.as_tensor([float(changed)], dtype=torch.float32, device=self.device)
                    with torch.no_grad():
                        action_t, _logp_t, _entropy_t, _value_t = self.situation_hazard.act(
                            obs_t, prev_t, age_t, compact_t, team_vector_t, kappa_t, changed_t,
                            deterministic=deterministic,
                        )
                    hazard_action = int(action_t.detach().cpu().numpy()[0])
                if should_force_renewal(
                    mode=self.situation_hazard_mode,
                    situation_changed=changed,
                    skill_age=int(self.skill_age[env_id, agent_id]),
                    min_age=self.situation_hazard_min_age,
                    hazard_action=hazard_action,
                ):
                    expired[agent_id] = True
```

This first pass uses reward-pure renewal control but does not yet train a separate hazard PPO buffer.  `oracle_change` is the first scientifically clean arm; `learned_beta` should remain experimental until Task 6 adds the hazard-decision update path.

- [ ] **Step 5: Add hazard metrics**

Add process metrics:

```python
    "situation_hazard_control_enabled",
    "situation_hazard_forced_renewal_rate",
    "situation_hazard_mode_code",
```

Use mode codes:

```python
diagnostic=0.0, oracle_change=1.0, learned_beta=2.0
```

- [ ] **Step 6: Run targeted tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py -q --basetemp .pytest_tmp_r12_stage1_task5
```

Expected:

```text
all tests passed
```

- [ ] **Step 7: Run a small reward-pure control smoke**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 4 `
  --rollout_length 100 `
  --total_timesteps 800 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7,13,24 `
  --enable_situation_diagnostics `
  --enable_situation_hazard_control `
  --situation_hazard_mode oracle_change `
  --situation_hazard_min_age 10 `
  --device cuda `
  --log_dir logs\ha_ctse_smoke_r12_stage1_oracle_change
```

Expected:

```text
training reaches at least one standalone_update line
train_updates.csv contains situation_hazard_control_enabled=1.0
force/process/topology intrinsic reward fields remain zero unless explicitly enabled
```

- [ ] **Step 8: Commit**

```bash
git add ha_ctse_process/standalone_agent.py ha_ctse_process/situation_hazard.py ha_ctse_process/train.py tests/test_r12_situation_stage1.py
git commit -m "feat: add reward-pure situation renewal control"
```

---

### Task 6: Add Local Runner and Experiment Record

**Files:**
- Create: `scripts/run_r12_stage1_local_cuda.ps1`
- Modify: `memory/ExpRecord.md`
- Modify: `memory/ATTENTION_POINTER.md`

- [ ] **Step 1: Create the local runner script**

Create `scripts/run_r12_stage1_local_cuda.ps1`:

```powershell
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path ".").Path
$logRoot = "logs\ha_ctse_r12_stage1_local_cuda"
$common = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
    "--seed", "1",
    "--n_agents", "6",
    "--collector_backend", "subproc",
    "--collector_start_method", "spawn",
    "--num_envs", "$NumEnvs",
    "--rollout_length", "500",
    "--skill_interval", "10",
    "--skill_lifetime_candidates", "3,7,13,24",
    "--total_timesteps", "$TotalTimesteps",
    "--eval_interval", "160000",
    "--eval_episodes", "20",
    "--save_interval", "20",
    "--checkpoint_keep_last", "4",
    "--plot_interval", "10",
    "--low_clip_epsilon", "0.1",
    "--smdp_bootstrap_coef", "0.25",
    "--device", $Device,
    "--enable_situation_diagnostics"
)

function Invoke-Run {
    param([string]$Name, [string[]]$Extra)
    $logDir = Join-Path $logRoot $Name
    $cmd = @($Python) + $common + $Extra + @("--log_dir", $logDir)
    Write-Host ""
    Write-Host "===== R12 Stage1: $Name ====="
    Write-Host ($cmd -join " ")
    if (-not $DryRun) {
        & $cmd[0] @($cmd[1..($cmd.Count - 1)])
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
}

$requested = $Experiments.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
foreach ($exp in $requested) {
    switch ($exp) {
        "diag_only" {
            Invoke-Run "diag_only_reward_pure" @()
        }
        "oracle_change" {
            Invoke-Run "oracle_change_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "10"
            )
        }
        "learned_beta_small" {
            Invoke-Run "learned_beta_small_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "learned_beta",
                "--situation_hazard_min_age", "10",
                "--situation_hazard_entropy_coef", "0.005",
                "--situation_hazard_reward_coef", "0.0"
            )
        }
        default {
            throw "Unknown experiment '$exp'. Use diag_only, oracle_change, learned_beta_small."
        }
    }
}
```

- [ ] **Step 2: Dry-run the script**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_change `
  -TotalTimesteps 32000 `
  -NumEnvs 4 `
  -DryRun
```

Expected:

```text
prints two python commands and exits 0
```

- [ ] **Step 3: Add ExpRecord entry before real runs**

Add to `memory/ExpRecord.md`:

```markdown
### EXP-20260702-r12-stage1-situation-hazard

Experiment name: `r12_stage1_situation_hazard`

Created at: 2026-07-02

Planned location: local CUDA first.

Purpose:

```text
Test whether the validated OPT situation substrate can drive reward-pure skill
renewal without adding intrinsic reward or communication-specific shaping.
```

Arms:

```text
diag_only: log kappa/change metrics only, no control.
oracle_change: renew eligible active skills when debounced kappa changes.
learned_beta_small: default experimental arm; hazard samples renewal but has no
intrinsic reward coefficient.
```

Metrics to read:

```text
situation_change_rate
situation_unique_kappa
situation_segment_change_frac
situation_hazard_forced_renewal_rate
duration_usage_entropy
skill_entropy
coverage_eq1_step_fraction
reward_mean and reward_std
```

Decision rule:

```text
If oracle_change improves coverage_eq1_step_fraction or reduces variance without
collapsing duration/skill entropy, keep Stage 1 and design learned_beta PPO
properly.  If oracle_change hurts and diagnostics show high churn, add stronger
debounce/min-age before learned_beta.  If diag_only shows kappa nearly static or
one-step noisy, return to substrate representation rather than adding rewards.
```
```

- [ ] **Step 4: Update attention pointer**

In `memory/ATTENTION_POINTER.md`, set active experiment to:

```text
EXP-20260702-r12-stage1-situation-hazard
```

and next action to:

```text
Run local R12 Stage 1 diag_only and oracle_change reward-pure controls; do not
enable SEF/DADS reward.
```

- [ ] **Step 5: Commit**

```bash
git add scripts/run_r12_stage1_local_cuda.ps1 memory/ExpRecord.md memory/ATTENTION_POINTER.md
git commit -m "chore: add r12 stage1 local experiment runner"
```

---

### Task 7: Final Validation and Handoff

**Files:**
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Modify: `memory/cross_validation.md`

- [ ] **Step 1: Run full targeted validation**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_situation_stage1.py tests\test_r12_substrate_gate.py -q --basetemp .pytest_tmp_r12_stage1_final
```

Expected:

```text
all tests passed
```

Run AST validation without writing `__pycache__`:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -c "import ast,pathlib; files=[r'ha_ctse_process\situation_substrate.py',r'ha_ctse_process\situation_hazard.py',r'ha_ctse_process\standalone_agent.py',r'ha_ctse_process\train.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8'), filename=f) for f in files]; print('ast_ok', len(files))"
```

Expected:

```text
ast_ok 4
```

- [ ] **Step 2: Run a tiny end-to-end train**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 4 `
  --rollout_length 100 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7,13,24 `
  --total_timesteps 800 `
  --enable_situation_diagnostics `
  --enable_situation_hazard_control `
  --situation_hazard_mode oracle_change `
  --device cuda `
  --log_dir logs\ha_ctse_r12_stage1_tiny_e2e
```

Expected:

```text
train exits 0
logs\ha_ctse_r12_stage1_tiny_e2e\train_updates.csv exists
```

- [ ] **Step 3: Record implementation result**

Add to `memory/IMPLEMENTATION_PLAN.md` under Round 12:

```markdown
R12-1a implemented: situation substrate diagnostics and reward-pure oracle
change renewal control.  Default behavior remains off.  No SEF/DADS reward or
communication-specific reward was added.
```

Add to `memory/cross_validation.md` Dialogue Log:

```markdown
### 2026-07-02 Codex result: R12 Stage 1 first-pass implementation
- Added pure situation substrate utilities, default-off hazard policy, and
  reward-pure oracle-change renewal control.
- Validation: targeted pytest and tiny S7-S1 train passed.
- Next experiment: `EXP-20260702-r12-stage1-situation-hazard`.
```

- [ ] **Step 4: Commit**

```bash
git add ha_ctse_process scripts tests memory
git commit -m "feat: implement r12 stage1 situation hazard"
```

---

## Self-Review

1. Spec coverage:
   - Situation substrate: Task 1 and Task 4.
   - Reward-pure hazard/renewal: Task 2 and Task 5.
   - Default-off safety: Task 3 and Task 5.
   - No communication-metric reward: explicitly preserved in scope and no task adds such reward.
   - Experiment alignment: Task 6.
   - Memory sync: Task 6 and Task 7.

2. Placeholder scan:
   - No placeholder markers or unspecified "handle edge cases" steps remain.
   - Every code-changing task includes concrete snippets and commands.

3. Type consistency:
   - `SituationDebouncer.update(...)` returns `SituationState`.
   - `SituationHazardPolicy.act(...)` returns `(action, logp, entropy, value)`.
   - Config names match CLI names and planned agent attributes.

4. Known execution caveat:
   - Task 5 intentionally makes `oracle_change` the first clean reward-pure control.  `learned_beta` is wired for later work, but a scientifically clean learned-beta PPO update needs a separate hazard-decision buffer and should not be treated as complete until a follow-up plan explicitly implements that buffer.

