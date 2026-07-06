# R12-1b Conservative Renewal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reward-pure conservative situation-change renewal gate so R12 Stage 1 can test whether debounced OPT situations help skill renewal without the churn observed in `oracle_change`.

**Architecture:** Keep the existing `diag_only` and `oracle_change` behavior intact. Add an optional conservative guard between `situation_changed` and forced renewal: minimum active-skill age, minimum dwell/confirmation after kappa change, and a rolling forced-renewal-rate cap. Log guard diagnostics so a failed run can be distinguished as "no situation signal", "guard too strict", or "renewal still harmful".

**Tech Stack:** Python, PyTorch, NumPy, pytest, PowerShell runner scripts, existing HA-CTSE CSV/TensorBoard/plotting metrics.

---

## Implementation Note

This plan has been executed. Two corrections were accepted during spec review
and are the source of truth for the final implementation:

```text
1. `SituationState.changed` is a pulse, so the conservative gate carries pending
   situation changes through `ConservativeRenewalDecision.renewal_signal`.
   The standalone agent passes that signal into `should_force_renewal()`.

2. The forced-renewal-rate cap warms up until the rolling window is full.  The
   cap is applied only after `len(_recent_forced) >= rate_window`.
```

The tracked test file is `tests/r12_conservative_renewal_test.py`. An ignored
migration copy at `tests/test_r12_conservative_renewal.py` could not be deleted
locally because Windows denied access; do not use that ignored path as the
canonical test.

## File Structure

- Modify `ha_ctse_process/situation_hazard.py`
  - Add a small pure-Python conservative-renewal guard config/state.
  - Keep `should_force_renewal()` as the final mode decision, but pass in a `guard_allowed` boolean for conservative mode.

- Modify `ha_ctse_process/config.py`
  - Add default-off R12-1b guard config fields.

- Modify `ha_ctse_process/train.py`
  - Add CLI flags, config assignment, manifest logging, TensorBoard scalars, and console fields for conservative renewal metrics.

- Modify `ha_ctse_process/standalone_agent.py`
  - Instantiate/reset guard state.
  - Apply guard before changing `expired[agent_id] = True`.
  - Emit per-update metrics.

- Modify `ha_ctse_process/plotting.py`
  - Add the new guard metrics to CSV plotting fields and the R12 situation plot.

- Modify `scripts/run_r12_stage1_local_cuda.ps1`
  - Add new `oracle_conservative` and `oracle_strict` experiment arms.

- Create `tests/r12_conservative_renewal_test.py`
  - Unit tests for min-age, confirmation, dwell, and rate-cap logic.

---

### Task 1: Add Conservative Renewal Guard Unit Tests

**Files:**
- Create: `tests/r12_conservative_renewal_test.py`
- Modify later: `ha_ctse_process/situation_hazard.py`

- [ ] **Step 1: Write failing tests for the conservative guard**

Create `tests/r12_conservative_renewal_test.py` with this content:

```python
from ha_ctse_process.situation_hazard import (
    ConservativeRenewalConfig,
    ConservativeRenewalGate,
    should_force_renewal,
)


def test_should_force_renewal_respects_guard_allowed():
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=20,
        min_age=10,
        hazard_action=0,
        guard_allowed=True,
    )
    assert not should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=20,
        min_age=10,
        hazard_action=0,
        guard_allowed=False,
    )


def test_conservative_gate_blocks_until_confirmed_change_count():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=2,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=2,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
    )
    second = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=40,
        step=20,
    )

    assert not first.allowed
    assert first.block_reason == "confirm"
    assert second.allowed
    assert second.block_reason == "allow"


def test_conservative_gate_blocks_until_min_dwell_checks():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=3,
            confirm_changes=1,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    blocked = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
        stable_count=2,
    )
    allowed = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=40,
        step=20,
        stable_count=3,
    )

    assert not blocked.allowed
    assert blocked.block_reason == "dwell"
    assert allowed.allowed


def test_conservative_gate_rate_cap_blocks_after_window_is_full():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=1,
            max_force_rate=0.25,
            rate_window=4,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
    )
    assert first.allowed
    gate.record_decision(first, forced=True)

    for step in (20, 30, 40):
        decision = gate.check(
            env_id=0,
            agent_id=0,
            situation_changed=True,
            skill_age=30,
            step=step,
        )
        assert not decision.allowed
        assert decision.block_reason == "rate_cap"
        gate.record_decision(decision, forced=False)

    metrics = gate.metrics(reset=False)
    assert metrics["situation_hazard_guard_rate_cap_block_rate"] == 0.75
    assert metrics["situation_hazard_guard_allow_rate"] == 0.25
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests\r12_conservative_renewal_test.py -q
```

Expected:

```text
ImportError: cannot import name 'ConservativeRenewalConfig'
```

---

### Task 2: Implement the Pure Conservative Renewal Gate

**Files:**
- Modify: `ha_ctse_process/situation_hazard.py`
- Test: `tests/r12_conservative_renewal_test.py`

- [ ] **Step 1: Add guard dataclasses and state**

In `ha_ctse_process/situation_hazard.py`, add these imports at the top:

```python
from collections import deque
from typing import Deque
```

After `HazardDecision`, add:

```python
@dataclass
class ConservativeRenewalConfig:
    enabled: bool = False
    min_dwell_checks: int = 0
    confirm_changes: int = 1
    max_force_rate: float = 1.0
    rate_window: int = 128


@dataclass
class ConservativeRenewalDecision:
    env_id: int
    agent_id: int
    allowed: bool
    block_reason: str


class ConservativeRenewalGate:
    def __init__(self, *, num_envs: int, n_agents: int, config: ConservativeRenewalConfig):
        self.num_envs = int(num_envs)
        self.n_agents = int(n_agents)
        self.config = config
        self._change_counts = [
            [0 for _ in range(self.n_agents)] for _ in range(self.num_envs)
        ]
        self._recent_forced: Deque[int] = deque(maxlen=max(int(config.rate_window), 1))
        self._counts = {
            "events": 0,
            "allowed": 0,
            "blocked_confirm": 0,
            "blocked_dwell": 0,
            "blocked_rate_cap": 0,
            "blocked_no_change": 0,
        }

    def reset_env(self, env_id: int) -> None:
        env = int(env_id)
        if 0 <= env < self.num_envs:
            for agent_id in range(self.n_agents):
                self._change_counts[env][agent_id] = 0

    def reset_all(self) -> None:
        for env_id in range(self.num_envs):
            self.reset_env(env_id)
        self._recent_forced.clear()
        self.reset_metrics()

    def reset_metrics(self) -> None:
        for key in self._counts:
            self._counts[key] = 0

    def _rate_cap_allows(self) -> bool:
        max_rate = float(self.config.max_force_rate)
        if max_rate >= 1.0:
            return True
        if max_rate <= 0.0:
            return False
        if len(self._recent_forced) < self._recent_forced.maxlen:
            return True
        return (sum(self._recent_forced) / float(len(self._recent_forced))) < max_rate

    def check(
        self,
        *,
        env_id: int,
        agent_id: int,
        situation_changed: bool,
        skill_age: int,
        step: int,
        stable_count: int = 0,
    ) -> ConservativeRenewalDecision:
        env = int(env_id)
        agent = int(agent_id)
        self._counts["events"] += 1

        if not bool(self.config.enabled):
            self._counts["allowed"] += 1
            return ConservativeRenewalDecision(env, agent, True, "allow")

        if not bool(situation_changed):
            self._change_counts[env][agent] = 0
            self._counts["blocked_no_change"] += 1
            return ConservativeRenewalDecision(env, agent, False, "no_change")

        self._change_counts[env][agent] += 1

        if int(stable_count) < int(max(self.config.min_dwell_checks, 0)):
            self._counts["blocked_dwell"] += 1
            return ConservativeRenewalDecision(env, agent, False, "dwell")

        if self._change_counts[env][agent] < int(max(self.config.confirm_changes, 1)):
            self._counts["blocked_confirm"] += 1
            return ConservativeRenewalDecision(env, agent, False, "confirm")

        if not self._rate_cap_allows():
            self._counts["blocked_rate_cap"] += 1
            return ConservativeRenewalDecision(env, agent, False, "rate_cap")

        self._counts["allowed"] += 1
        return ConservativeRenewalDecision(env, agent, True, "allow")

    def record_decision(self, decision: ConservativeRenewalDecision, *, forced: bool) -> None:
        if int(self.config.rate_window) > 0:
            self._recent_forced.append(1 if forced else 0)
        if forced:
            self._change_counts[int(decision.env_id)][int(decision.agent_id)] = 0

    def metrics(self, *, reset: bool = True) -> dict[str, float]:
        events = float(max(int(self._counts["events"]), 1))
        values = {
            "situation_hazard_guard_event_count": float(self._counts["events"]),
            "situation_hazard_guard_allow_rate": float(self._counts["allowed"]) / events,
            "situation_hazard_guard_confirm_block_rate": float(self._counts["blocked_confirm"]) / events,
            "situation_hazard_guard_dwell_block_rate": float(self._counts["blocked_dwell"]) / events,
            "situation_hazard_guard_rate_cap_block_rate": float(self._counts["blocked_rate_cap"]) / events,
            "situation_hazard_guard_no_change_block_rate": float(self._counts["blocked_no_change"]) / events,
            "situation_hazard_guard_recent_force_rate": (
                float(sum(self._recent_forced)) / float(len(self._recent_forced))
                if self._recent_forced
                else 0.0
            ),
        }
        if reset:
            self.reset_metrics()
        return values
```

- [ ] **Step 2: Extend `should_force_renewal()` signature**

Replace `should_force_renewal()` with:

```python
def should_force_renewal(
    *,
    mode: str,
    situation_changed: bool,
    skill_age: int,
    min_age: int,
    hazard_action: int,
    guard_allowed: bool = True,
) -> bool:
    if int(skill_age) < int(max(min_age, 0)):
        return False
    if not bool(guard_allowed):
        return False
    if mode == "oracle_change":
        return bool(situation_changed)
    if mode == "learned_beta":
        return bool(int(hazard_action) > 0)
    return False
```

- [ ] **Step 3: Run tests**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests\r12_conservative_renewal_test.py -q
```

Expected:

```text
4 passed
```

---

### Task 3: Add Config and CLI for Conservative Renewal

**Files:**
- Modify: `ha_ctse_process/config.py`
- Modify: `ha_ctse_process/train.py`

- [ ] **Step 1: Add defaults to config**

In `ha_ctse_process/config.py`, directly after `situation_hazard_reward_coef = 0.0`, add:

```python
    situation_hazard_conservative_guard = False
    situation_hazard_min_dwell_checks = 0
    situation_hazard_confirm_changes = 1
    situation_hazard_max_force_rate = 1.0
    situation_hazard_rate_window = 128
```

- [ ] **Step 2: Add CLI flags**

In `ha_ctse_process/train.py`, after `parser.add_argument("--situation_hazard_reward_coef", type=float, default=None)`, add:

```python
    parser.add_argument("--enable_situation_hazard_conservative_guard", action="store_true")
    parser.add_argument("--situation_hazard_min_dwell_checks", type=int, default=0)
    parser.add_argument("--situation_hazard_confirm_changes", type=int, default=0)
    parser.add_argument("--situation_hazard_max_force_rate", type=float, default=None)
    parser.add_argument("--situation_hazard_rate_window", type=int, default=0)
```

- [ ] **Step 3: Wire CLI flags into config**

In `ha_ctse_process/train.py`, after:

```python
    if args.enable_situation_hazard_control:
        config.enable_situation_hazard_control = True
```

add:

```python
    if args.enable_situation_hazard_conservative_guard:
        config.situation_hazard_conservative_guard = True
```

Then extend the existing integer config loop by adding:

```python
        "situation_hazard_min_dwell_checks",
        "situation_hazard_confirm_changes",
        "situation_hazard_rate_window",
```

After the float config loop, add:

```python
    if args.situation_hazard_max_force_rate is not None:
        config.situation_hazard_max_force_rate = float(args.situation_hazard_max_force_rate)
```

- [ ] **Step 4: Run syntax check**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m py_compile ha_ctse_process\config.py ha_ctse_process\train.py
```

Expected: no output and exit code 0.

---

### Task 4: Apply the Conservative Guard in `StandaloneProcessAgent`

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `ha_ctse_process/train.py`
- Test: `tests/r12_conservative_renewal_test.py`

- [ ] **Step 1: Import guard classes**

In `ha_ctse_process/standalone_agent.py`, replace:

```python
from ha_ctse_process.situation_hazard import SituationHazardPolicy, should_force_renewal
```

with:

```python
from ha_ctse_process.situation_hazard import (
    ConservativeRenewalConfig,
    ConservativeRenewalGate,
    SituationHazardPolicy,
    should_force_renewal,
)
```

- [ ] **Step 2: Initialize guard config and state**

In `StandaloneProcessAgent.__init__`, after `self.situation_hazard_reward_coef = ...`, add:

```python
        self.situation_hazard_conservative_guard = bool(
            getattr(config, "situation_hazard_conservative_guard", False)
        )
        self.situation_hazard_guard = ConservativeRenewalGate(
            num_envs=self.num_envs,
            n_agents=self.n_agents,
            config=ConservativeRenewalConfig(
                enabled=self.situation_hazard_conservative_guard,
                min_dwell_checks=int(max(getattr(config, "situation_hazard_min_dwell_checks", 0), 0)),
                confirm_changes=int(max(getattr(config, "situation_hazard_confirm_changes", 1), 1)),
                max_force_rate=float(getattr(config, "situation_hazard_max_force_rate", 1.0)),
                rate_window=int(max(getattr(config, "situation_hazard_rate_window", 128), 1)),
            ),
        )
```

- [ ] **Step 3: Reset guard state**

In `reset_env_state()`, after `self.situation_debouncer.reset_env(env_id)`, add:

```python
        self.situation_hazard_guard.reset_env(env_id)
```

In `reset_all_policy_state()`, after resetting `self.situation_debouncer`, add:

```python
        self.situation_hazard_guard.reset_all()
```

- [ ] **Step 4: Apply guard before forced renewal**

In `maybe_assign_skills()`, inside the hazard loop just before `if should_force_renewal(...):`, add:

```python
                guard_decision = self.situation_hazard_guard.check(
                    env_id=env_id,
                    agent_id=agent_id,
                    situation_changed=changed,
                    skill_age=skill_age,
                    step=int(step),
                    stable_count=int(getattr(situation_state, "stable_count", 0)),
                )
```

Then update the call:

```python
                forced = should_force_renewal(
                    mode=self.situation_hazard_mode,
                    situation_changed=changed,
                    skill_age=skill_age,
                    min_age=self.situation_hazard_min_age,
                    hazard_action=hazard_action,
                    guard_allowed=guard_decision.allowed,
                )
                self.situation_hazard_guard.record_decision(guard_decision, forced=forced)
                if forced:
                    expired[agent_id] = True
                    self._situation_hazard_forced_renewals += 1
```

Replace the old `if should_force_renewal(...):` block with the new `forced` block above.

- [ ] **Step 5: Add metrics into `_situation_metrics()`**

In `_situation_metrics()`, after `hazard_metrics = {...}`, add:

```python
        guard_metrics = self.situation_hazard_guard.metrics(reset=reset)
        hazard_metrics.update(
            {
                "situation_hazard_conservative_guard": 1.0
                if self.situation_hazard_conservative_guard
                else 0.0,
                **guard_metrics,
            }
        )
```

- [ ] **Step 6: Add TensorBoard scalar fields**

In `ha_ctse_process/train.py`, near the existing `Situation/HazardForcedRenewalRate` scalar, add:

```python
    writer.add_scalar(
        "Situation/HazardGuardAllowRate",
        process_metrics.get("situation_hazard_guard_allow_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardRateCapBlockRate",
        process_metrics.get("situation_hazard_guard_rate_cap_block_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardDwellBlockRate",
        process_metrics.get("situation_hazard_guard_dwell_block_rate", 0.0),
        total_steps,
    )
```

- [ ] **Step 7: Run targeted validation**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests\r12_conservative_renewal_test.py -q
& C:\Users\wu\.conda\envs\SB3\python.exe -m py_compile ha_ctse_process\situation_hazard.py ha_ctse_process\standalone_agent.py ha_ctse_process\train.py
```

Expected:

```text
4 passed
```

The `py_compile` command should print no output.

---

### Task 5: Add CSV/Plotting/Console Visibility

**Files:**
- Modify: `ha_ctse_process/plotting.py`
- Modify: `ha_ctse_process/train.py`

- [ ] **Step 1: Add plotting metric fields**

In `ha_ctse_process/plotting.py`, add these fields to the existing situation metric list after `situation_hazard_forced_renewal_rate`:

```python
    "situation_hazard_conservative_guard",
    "situation_hazard_guard_allow_rate",
    "situation_hazard_guard_confirm_block_rate",
    "situation_hazard_guard_dwell_block_rate",
    "situation_hazard_guard_rate_cap_block_rate",
    "situation_hazard_guard_recent_force_rate",
```

In the situation plotting series near the existing "Situation forced renewal rate" item, add:

```python
        ("situation_hazard_guard_allow_rate", "Guard allow rate"),
        ("situation_hazard_guard_dwell_block_rate", "Guard dwell block"),
        ("situation_hazard_guard_rate_cap_block_rate", "Guard rate-cap block"),
        ("situation_hazard_guard_recent_force_rate", "Guard recent force rate"),
```

- [ ] **Step 2: Add console fields**

In `ha_ctse_process/train.py`, near the console fields that print `situation_hazard_force`, add:

```python
                f"situation_guard={process_metrics.get('situation_hazard_conservative_guard', 0.0):.0f} "
                f"situation_guard_allow={process_metrics.get('situation_hazard_guard_allow_rate', 0.0):.3f} "
                f"situation_guard_ratecap={process_metrics.get('situation_hazard_guard_rate_cap_block_rate', 0.0):.3f} "
```

- [ ] **Step 3: Run syntax validation**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m py_compile ha_ctse_process\plotting.py ha_ctse_process\train.py
```

Expected: no output and exit code 0.

---

### Task 6: Add Conservative Arms to the Local CUDA Runner

**Files:**
- Modify: `scripts/run_r12_stage1_local_cuda.ps1`

- [ ] **Step 1: Update unknown-experiment help text**

Replace:

```powershell
throw "No experiments requested. Use diag_only, oracle_change, or learned_beta_small."
```

with:

```powershell
throw "No experiments requested. Use diag_only, oracle_change, oracle_conservative, oracle_strict, or learned_beta_small."
```

Replace the default-case error similarly:

```powershell
throw "Unknown experiment '$exp'. Use diag_only, oracle_change, oracle_conservative, oracle_strict, learned_beta_small."
```

- [ ] **Step 2: Add `oracle_conservative` arm**

In the `switch ($exp)` block, after `oracle_change`, add:

```powershell
        "oracle_conservative" {
            Invoke-R12Stage1Run "oracle_conservative_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "30",
                "--enable_situation_hazard_conservative_guard",
                "--situation_hazard_min_dwell_checks", "3",
                "--situation_hazard_confirm_changes", "2",
                "--situation_hazard_max_force_rate", "0.03",
                "--situation_hazard_rate_window", "256"
            )
        }
```

- [ ] **Step 3: Add `oracle_strict` arm**

After `oracle_conservative`, add:

```powershell
        "oracle_strict" {
            Invoke-R12Stage1Run "oracle_strict_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "50",
                "--enable_situation_hazard_conservative_guard",
                "--situation_hazard_min_dwell_checks", "5",
                "--situation_hazard_confirm_changes", "3",
                "--situation_hazard_max_force_rate", "0.015",
                "--situation_hazard_rate_window", "256"
            )
        }
```

- [ ] **Step 4: Dry-run the runner**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_conservative,oracle_strict `
  -TotalTimesteps 32000 `
  -NumEnvs 4 `
  -DryRun
```

Expected:

```text
R12 Stage 1 situation hazard local CUDA runner
...
===== R12 Stage 1 situation hazard: diag_only_reward_pure =====
...
===== R12 Stage 1 situation hazard: oracle_conservative_reward_pure =====
...
--enable_situation_hazard_conservative_guard
--situation_hazard_max_force_rate 0.03
...
===== R12 Stage 1 situation hazard: oracle_strict_reward_pure =====
...
--situation_hazard_max_force_rate 0.015
```

---

### Task 7: Smoke Test a Tiny Reward-Pure Run

**Files:**
- Runtime output only under `logs\ha_ctse_r12_1b_tiny_smoke`

- [ ] **Step 1: Run a tiny single-arm smoke**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 4 `
  --rollout_length 64 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7,13,24 `
  --total_timesteps 256 `
  --eval_interval 1000000 `
  --save_interval 1000000 `
  --plot_interval 1000000 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cuda `
  --enable_situation_diagnostics `
  --enable_situation_hazard_control `
  --situation_hazard_mode oracle_change `
  --situation_hazard_min_age 30 `
  --enable_situation_hazard_conservative_guard `
  --situation_hazard_min_dwell_checks 3 `
  --situation_hazard_confirm_changes 2 `
  --situation_hazard_max_force_rate 0.03 `
  --situation_hazard_rate_window 256 `
  --log_dir logs\ha_ctse_r12_1b_tiny_smoke
```

Expected:

```text
Training starts and exits without argument errors.
```

- [ ] **Step 2: Verify reward guards remain zero**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -c "import csv; from pathlib import Path; rows=list(csv.DictReader(open(Path('logs/ha_ctse_r12_1b_tiny_smoke/metrics/train_updates.csv'), newline=''))); assert rows, 'no update rows'; last=rows[-1]; [(_ for _ in ()).throw(AssertionError((k, last[k]))) for k in ('process_high_reward_mean','process_low_reward_mean','force_reward_low_mean','topology_reward_low_mean') if k in last and abs(float(last[k])) != 0.0]; [(_ for _ in ()).throw(AssertionError('missing '+k)) for k in ('situation_hazard_conservative_guard','situation_hazard_guard_allow_rate') if k not in last]; print('R12-1b smoke metrics OK')"
```

Expected:

```text
R12-1b smoke metrics OK
```

---

### Task 8: Update Memory After Implementation

**Files:**
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Modify: `memory/ExpRecord.md`
- Modify: `memory/ATTENTION_POINTER.md`

- [ ] **Step 1: Add implementation note to plan**

In `memory/IMPLEMENTATION_PLAN.md`, under `R12-1a local CUDA readout (2026-07-03)`, add:

```text
R12-1b conservative renewal implementation status:
  Implemented default-off conservative guard controls:
    situation_hazard_min_dwell_checks
    situation_hazard_confirm_changes
    situation_hazard_max_force_rate
    situation_hazard_rate_window
  Added oracle_conservative and oracle_strict runner arms.
  Reward path remains pure; learned_beta PPO remains blocked until a
  conservative oracle arm is neutral-to-positive against diag_only.
```

- [ ] **Step 2: Add experiment entry**

In `memory/ExpRecord.md`, add a new entry at the top of Active / Planned Experiments:

```markdown
### EXP-20260703-r12-1b-conservative-renewal

Experiment name: `r12_1b_conservative_renewal`

Created at: 2026-07-03

Planned location: local CUDA first.

Command/script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_conservative,oracle_strict `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Purpose:

```text
Test whether conservative situation-change renewal removes the churn observed
in R12-1a oracle_change while keeping reward path pure.
```

Hypothesis:

```text
Stronger dwell/confirmation and a forced-renewal-rate cap should keep useful
situation boundaries while avoiding frequent reactive renewal.
```

Controls / comparison:

```text
diag_only: situation diagnostics only.
oracle_conservative: min_age=30, min_dwell=3, confirm_changes=2, max_force_rate=0.03.
oracle_strict: min_age=50, min_dwell=5, confirm_changes=3, max_force_rate=0.015.
```

Metrics to read:

```text
situation_hazard_forced_renewal_rate
situation_hazard_guard_allow_rate
situation_hazard_guard_dwell_block_rate
situation_hazard_guard_confirm_block_rate
situation_hazard_guard_rate_cap_block_rate
segment_length_mean
skill_switch_rate
duration_usage_entropy
skill_usage_entropy
coverage_eq1_step_frac
zero_throughput_ep_frac
reward_mean / reward_std
reward-path guard fields
```

Meaning of possible outcomes:

```text
conservative arm neutral-to-positive vs diag_only:
  design proper learned_beta PPO with conservative guard priors.

conservative arm still worse but guard allows many renewals:
  make renewal criterion stricter or return to substrate/change representation.

conservative arm blocks almost everything:
  loosen dwell/confirm/rate-cap before judging situation renewal.

reward guards nonzero:
  invalid run.
```

Stop / continue rule:

```text
Do not proceed to learned_beta PPO unless a conservative oracle arm is
neutral-to-positive on stability without entropy collapse and without reward
contamination.
```

Result status: planned
```

- [ ] **Step 3: Update attention pointer**

In `memory/ATTENTION_POINTER.md`, set the active next action to:

```text
Implement/run EXP-20260703-r12-1b-conservative-renewal: diag_only vs
oracle_conservative vs oracle_strict. learned_beta PPO remains blocked until
conservative oracle renewal is neutral-to-positive.
```

- [ ] **Step 4: Verify memory anchors**

Run:

```powershell
rg -n "EXP-20260703-r12-1b|oracle_conservative|R12-1b conservative" memory docs\superpowers\plans
```

Expected: matches in `ExpRecord.md`, `IMPLEMENTATION_PLAN.md`, `ATTENTION_POINTER.md`, and this plan file.

---

## Self-Review

Spec coverage:

- The plan addresses the failed R12-1a `oracle_change` gate by adding debounce/min-age/hysteresis-style confirmation and a forced-renewal-rate cap.
- The plan keeps reward path pure and does not add SEF/DADS reward, communication-specific intrinsic reward, or learned hazard PPO.
- The plan adds metrics needed to interpret "too much churn" versus "guard too strict".
- The plan creates a new experiment entry before launching the next run.

Placeholder scan:

- No placeholder or open-ended test steps remain.
- Code snippets define the new classes, CLI flags, runner arms, and tests.

Type consistency:

- `ConservativeRenewalConfig`, `ConservativeRenewalGate`, and `ConservativeRenewalDecision` are introduced before use.
- Metric names use the `situation_hazard_guard_*` prefix consistently.
- Runner experiment names are `oracle_conservative` and `oracle_strict` throughout.
