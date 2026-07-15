# R38 Cooperative Two-Timescale Sparse Access Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one swap-equivariant sparse cooperative two-timescale benchmark and determine whether functionally ordinary constant-code recurrent MAPPO can access its short duty, long duty, and joint success within a fixed 320,000-step budget.

**Architecture:** Add a focused PettingZoo parallel environment with a locked anchor holder and a separate shuttle visitor, expose only geometry to the decentralized actors and progress state to the centralized critic, then reuse the existing constant-code recurrent MAPPO path without changing its learner. A single local CUDA runner trains one MAPPO policy, evaluates it on 256 registered resets, evaluates uniform random actions on the same resets, and writes one M0-M2 decision JSON.

**Tech Stack:** Python 3.11, NumPy, Gymnasium, PettingZoo Parallel API, PyTorch recurrent MAPPO, PowerShell, pytest, CUDA, existing HMASD sharded/subprocess collector.

## Global Constraints

- Causal edge: `swap-equivariant simultaneous anchor/shuttle duties -> ordinary recurrent MAPPO accesses both duties and joint sparse success -> benchmark becomes eligible for one later shared-fixed-k versus per-agent-lifetime gate`.
- This is an environment-access gate, not an HMASD, skill-learning, or task-performance result.
- The only environment reward is shared `+1` on full joint success; every partial contact, shuttle stage, anchor streak, holder break, and failed episode gives `0`.
- Set and report `intrinsic_reward=0.0`. Do not add novelty, count, RND, ICM, classifier, discriminator, process, skill, progress, distance, contact, stage, or potential-based reward.
- Any future intrinsic reward must preserve one environment-agnostic mathematical form and input contract across benchmarks. It may not consume or encode CTS anchor/shuttle identities, contacts, stages, distances, holder identity, success predicates, or external reward.
- Do not modify `ha_ctse_process/standalone_agent.py`, `ha_ctse_process/r30_fixed_clock.py`, the old Alice-Bob environment/configurations, or any intrinsic-reward implementation.
- The baseline is functionally ordinary constant-code recurrent MAPPO: skill code `0`, no high-policy update, no process/intrinsic injection, recurrent low actor, centralized recurrent low critic. Dormant skill/high/process modules may remain physically present for checkpoint compatibility.
- Environment constants are exact: world `[0,6]^2`, action scale `0.5`, anchor `(3,3)`, shuttle zones `(1,3)` and `(5,3)`, zone radius `0.75`, anchor requirement `40` post-action states, shuttle sequence `left -> right -> left -> right`, horizon `200`.
- Actor observation is exactly 10 floats containing own absolute position and teammate/anchor/left/right relative positions. It contains no holder, stage, streak, contact, completion, reward, role, agent ID, or future-state field.
- Centralized critic state is exactly 10 floats containing two absolute positions, holder one-hot, normalized shuttle stage, normalized anchor streak, short-complete flag, and long-complete flag.
- Training is exact: seed `39031`, CUDA, `16` parallel spawn environments, rollout length `200`, `320,000` environment steps, `100` outer low PPO updates, `5` PPO epochs, recurrent sequence length `20`, sequence batch size `64`, actor and critic learning rates `3e-4`, gamma `0.99`, GAE lambda `0.95`, PPO clip `0.2`, value clip `0.2`, entropy coefficient `0.01`, value-loss coefficient `1.0`, grad norm `0.5`.
- Final stochastic MAPPO evaluation uses the 256 reset seeds `139031..139286`. Uniform random uses those same resets and a single independent `numpy.random.default_rng(49031)` action stream; do not call `Box.sample()`.
- Paired percentile bootstrap uses `10,000` repetitions, seed `59031`, and paired episode indices. Four repeatability blocks are the contiguous 64-episode slices of the registered 256 resets; they are not independent training seeds.
- A valid scientific FAIL retires this benchmark without shaping, intrinsic reward, added steps, added seeds, threshold changes, or learner changes. A PASS authorizes only registration of one shared-fixed-k versus per-agent-lifetime mechanism gate.

---

## File Structure

**Create**

- `envs/pettingzoo/cooperative_two_timescale_sparse.py` — the complete role-free CTS state machine and PettingZoo interface.
- `ha_ctse_process/config_r38_two_timescale_sparse.py` — the frozen constant-code recurrent MAPPO and environment contract.
- `tests/cooperative_two_timescale_sparse_test.py` — focused state-machine, symmetry, information-boundary, and adapter checks.
- `scripts/analyze_r38_cts_access.py` — paired random evaluation, manifest validation, bootstrap, M0-M2 decisions, and single result JSON.
- `tests/test_r38_cts_analyzer.py` — focused synthetic checks for paired bootstrap and decision branches.
- `scripts/run_r38_cts_access_local.ps1` — neutral initialization, one CUDA training job, analyzer invocation, and runner status.

**Modify**

- `ha_ctse_process/env_factory.py` — register the canonical scenario and construct the new environment.
- `ha_ctse_process/plotting.py` — register the six CTS metrics plus terminal/truncation flags in evaluation CSVs.
- `ha_ctse_process/train.py` — expose the frozen R38 runtime contract in manifests and record terminal/truncation flags in final evaluation rows.
- `memory/ExpRecord.md` — register the single formal experiment contract before launch and record only its final decision afterward.
- `memory/CURRENT_WORK.md` — point the active objective to R38 and later to its single result JSON.

No other production files are in scope.

### Task 1: Register the Formal R38 Contract

**Files:**
- Modify: `memory/ExpRecord.md`
- Modify: `memory/CURRENT_WORK.md`

**Interfaces:**
- Consumes: the accepted-with-modification disposition in `docs/external-review/gpt5_6_pro/20260715_r37_actor_visible_identity_access_result/DISPOSITION.md`.
- Produces: experiment ID `EXP-20260715-r38-cts-access`, one authoritative gate contract, and the active implementation pointer used by Tasks 2-6.

- [ ] **Step 1: Add one R38 dashboard block to `memory/ExpRecord.md`**

Insert this exact contract after the completed R37 row:

```markdown
## EXP-20260715-r38-cts-access — Cooperative Two-Timescale Sparse Access

- Question: can functionally ordinary constant-code recurrent MAPPO access a
  swap-equivariant task that structurally requires one simultaneous long-lived
  anchor duty and one short shuttle duty?
- Causal edge: simultaneous anchor/shuttle duties -> recurrent MAPPO accesses
  both duties and joint sparse success -> one later lifetime-controller gate is
  eligible.
- Baselines: Level 1 trained constant-code recurrent MAPPO versus paired
  uniform-random actions on identical reset seeds. This is an environment
  access gate, not an algorithm comparison.
- Reward: shared +1 only on full success; otherwise zero. Intrinsic reward is
  identically zero and no environment-specific auxiliary signal is allowed.
- Budget: train seed 39031; CUDA; 16 parallel environments; rollout 200;
  320,000 environment steps; 100 outer low PPO updates; final stochastic eval
  seeds 139031..139286. Random action RNG seed 49031. Paired bootstrap 10,000
  repetitions with seed 59031.
- M0 implementation: exact scenario/config/seed/budget; 256 unique paired
  reset rows per policy; finite actions and metrics; MAPPO success rows end by
  termination and failures at step 200 by truncation; task reward equals the
  full-success indicator; all non-full rewards and all intrinsic rewards are
  zero.
- M1 access: MAPPO short-duty rate >= 0.10, long-duty rate >= 0.05, full-success
  rate > 0.10 (at least 26/256), and the paired MAPPO-minus-random bootstrap
  lower bound is > 0 for all three indicators.
- M2 repeatability: at least three of the four contiguous 64-reset MAPPO blocks
  contain at least one full success.
- PASS_R38_CTS_ACCESS: M0, M1, and M2 pass; authorize only registration of one
  shared-fixed-k versus per-agent-lifetime mechanism gate.
- INVALID_R38_IMPLEMENTATION: M0 fails; fix only the concrete wiring defect and
  rerun the unchanged contract.
- FAIL_R38_CTS_ACCESS: M0 passes and M1 or M2 fails; retire the benchmark with
  no shaping, intrinsic reward, budget, seed, threshold, or learner rescue.
- Prohibited: old Alice-Bob logic, identity cues, role labels, low-learner
  changes, high-policy updates, process/skill rewards, threshold changes after
  results, and environment-specific intrinsic reward.
- Expected wall clock: one local 320K CUDA training job plus 512 total final
  evaluation episodes; use the existing dedicated training monitor.
- Status source: `<run-root>/runner_status.txt`; decision source:
  `<run-root>/result/r38_cts_access.json`.
- Status: REGISTERED.
```

- [ ] **Step 2: Replace the active objective in `memory/CURRENT_WORK.md` with one compact pointer**

Use this wording without duplicating the thresholds:

```markdown
- Active objective: implement and run `EXP-20260715-r38-cts-access` from the
  single contract in `memory/ExpRecord.md`. R37 is retired; do not return to the
  Alice-Bob access family.
- Immediate next action: implement the CTS environment, ordinary constant-code
  recurrent MAPPO configuration, and the single local runner/analyzer described
  in `docs/superpowers/plans/2026-07-15-r38-cts-access-gate.md`.
```

- [ ] **Step 3: Check that the contract has one route and no reward exception**

Run:

```powershell
rg -n "EXP-20260715-r38|intrinsic|PASS_R38|INVALID_R38|FAIL_R38" memory/ExpRecord.md memory/CURRENT_WORK.md
```

Expected: one R38 contract, `intrinsic reward is identically zero`, and exactly the three registered result statuses.

- [ ] **Step 4: Commit the formal contract**

```powershell
git add memory/ExpRecord.md memory/CURRENT_WORK.md
git commit -m "docs: register R38 CTS access gate"
```

Expected: one commit containing only the two compact memory files.

### Task 2: Implement the Cooperative Two-Timescale Sparse Environment

**Files:**
- Create: `envs/pettingzoo/cooperative_two_timescale_sparse.py`
- Create: `tests/cooperative_two_timescale_sparse_test.py`

**Interfaces:**
- Consumes: Gymnasium `Box`, PettingZoo `ParallelEnv`, and a config object with the `r38_*` constants defined in Task 3.
- Produces: `CooperativeTwoTimescaleSparseEnv(ParallelEnv)` with `reset(seed, options)`, `step(actions)`, `observation_space(agent)`, `action_space(agent)`, `get_obs_dim() -> int`, `get_state_dim() -> int`, `_get_state() -> np.ndarray`, and `get_current_state() -> dict`.
- Produces metrics: `r38_short_duty_complete`, `r38_long_duty_complete`, `r38_full_cycle_success`, `r38_anchor_streak_max`, `r38_shuttle_stage_max`, and `r38_sparse_reward`.

- [ ] **Step 1: Write the failing environment contract and symmetry tests**

Create `tests/cooperative_two_timescale_sparse_test.py` with these concrete cases:

```python
from types import SimpleNamespace

import numpy as np

from envs.pettingzoo.cooperative_two_timescale_sparse import (
    CooperativeTwoTimescaleSparseEnv,
)


def config():
    return SimpleNamespace(
        r38_world_size=6.0,
        r38_action_scale=0.5,
        r38_zone_radius=0.75,
        r38_anchor_required_steps=40,
        r38_shuttle_stages=4,
        max_steps=200,
    )


def zeros():
    return {
        "agent_0": np.zeros(2, dtype=np.float32),
        "agent_1": np.zeros(2, dtype=np.float32),
    }


def test_reset_is_exchangeable_and_hides_attempt_state_from_actor():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=7)
    anchor_agent_ids = set()
    for seed in range(32):
        obs, _ = env.reset(seed=seed)
        distances = np.linalg.norm(env.positions - env.anchor, axis=1)
        anchor_agent_ids.add(int(np.argmin(distances)))
    assert anchor_agent_ids == {0, 1}
    assert env.get_obs_dim() == 10
    assert env.get_state_dim() == 10
    assert obs["agent_0"].shape == (10,)
    assert obs["agent_1"].shape == (10,)
    assert env.action_space("agent_0").shape == (2,)
    assert np.all(np.isfinite(np.stack(list(obs.values()))))


def test_simultaneous_anchor_and_four_stage_shuttle_pays_once():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=1)
    env.reset(seed=1)
    env.positions[:] = np.asarray([[3.0, 3.0], [1.0, 3.0]], dtype=np.float32)
    _, rewards, terms, truncs, infos = env.step(zeros())
    assert infos["agent_0"]["reward_info"]["r38_shuttle_stage_max"] == 1.0
    for direction in (1.0, -1.0, 1.0):
        for _ in range(8):
            actions = zeros()
            actions["agent_1"][0] = direction
            _, rewards, terms, truncs, infos = env.step(actions)
    while not any(terms.values()):
        _, rewards, terms, truncs, infos = env.step(zeros())
    metrics = infos["agent_0"]["reward_info"]
    assert metrics["r38_short_duty_complete"] == 1.0
    assert metrics["r38_long_duty_complete"] == 1.0
    assert metrics["r38_full_cycle_success"] == 1.0
    assert rewards == {"agent_0": 1.0, "agent_1": 1.0}
    assert all(terms.values()) and not any(truncs.values())


def test_holder_break_resets_before_visitor_contact_and_cannot_rearm_same_step():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=2)
    env.reset(seed=2)
    env.positions[:] = np.asarray([[3.0, 3.0], [1.0, 3.0]], dtype=np.float32)
    env.step(zeros())
    env.positions[0] = np.asarray([3.7, 3.0], dtype=np.float32)
    actions = zeros()
    actions["agent_0"][:] = (1.0, 0.0)
    _, rewards, terms, _, infos = env.step(actions)
    metrics = infos["agent_0"]["reward_info"]
    assert env.active_holder == -1
    assert metrics["r38_short_duty_complete"] == 0.0
    assert metrics["r38_long_duty_complete"] == 0.0
    assert metrics["r38_full_cycle_success"] == 0.0
    assert rewards == {"agent_0": 0.0, "agent_1": 0.0}
    assert not any(terms.values())


def test_locked_holder_cannot_advance_the_shuttle_duty():
    env = CooperativeTwoTimescaleSparseEnv(config=config(), seed=4)
    env.reset(seed=4)
    env.positions[:] = np.asarray([[3.0, 3.0], [2.0, 3.0]], dtype=np.float32)
    env.step(zeros())
    assert env.active_holder == 0
    env.positions[:] = np.asarray([[1.0, 3.0], [3.0, 3.0]], dtype=np.float32)
    _, rewards, terms, _, infos = env.step(zeros())
    metrics = infos["agent_0"]["reward_info"]
    assert env.active_holder == -1
    assert env.shuttle_stage == 0
    assert metrics["r38_full_cycle_success"] == 0.0
    assert rewards == {"agent_0": 0.0, "agent_1": 0.0}
    assert not any(terms.values())


def test_agent_swap_is_transition_and_reward_equivariant():
    env_a = CooperativeTwoTimescaleSparseEnv(config=config(), seed=3)
    env_b = CooperativeTwoTimescaleSparseEnv(config=config(), seed=3)
    env_a.reset(seed=3)
    env_b.reset(seed=3)
    env_a.positions[:] = np.asarray([[3.0, 3.0], [2.0, 3.0]], dtype=np.float32)
    env_b.positions[:] = env_a.positions[::-1]
    actions_a = {"agent_0": np.zeros(2, np.float32), "agent_1": np.asarray([-1.0, 0.0], np.float32)}
    actions_b = {"agent_0": actions_a["agent_1"], "agent_1": actions_a["agent_0"]}
    out_a = env_a.step(actions_a)
    out_b = env_b.step(actions_b)
    assert np.allclose(out_a[0]["agent_0"], out_b[0]["agent_1"])
    assert np.allclose(out_a[0]["agent_1"], out_b[0]["agent_0"])
    assert out_a[1]["agent_0"] == out_b[1]["agent_1"]
    assert out_a[4]["agent_0"]["reward_info"]["r38_shuttle_stage_max"] == out_b[4]["agent_1"]["reward_info"]["r38_shuttle_stage_max"]
```

- [ ] **Step 2: Run the new tests and confirm the module is absent**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py -q
```

Expected: collection fails with `ModuleNotFoundError: envs.pettingzoo.cooperative_two_timescale_sparse`.

- [ ] **Step 3: Implement the exact state machine and information boundary**

Create `envs/pettingzoo/cooperative_two_timescale_sparse.py`. The implementation must use these exact transition rules:

```python
class CooperativeTwoTimescaleSparseEnv(ParallelEnv):
    metadata = {"name": "cooperative_two_timescale_sparse_v0"}
    possible_agents = ["agent_0", "agent_1"]

    def _advance_duty_cycle(self) -> bool:
        anchor = self._anchor_contacts()
        if self.active_holder < 0:
            if int(anchor.sum()) == 1:
                self.active_holder = int(np.flatnonzero(anchor)[0])
                self.anchor_streak = 1
                self.anchor_streak_max = max(self.anchor_streak_max, 1)
                self._accept_expected_shuttle_contact(1 - self.active_holder)
            return False

        holder = self.active_holder
        if not bool(anchor[holder]):
            self._reset_attempt()
            return False

        self.anchor_streak += 1
        self.anchor_streak_max = max(self.anchor_streak_max, self.anchor_streak)
        self._accept_expected_shuttle_contact(1 - holder)
        self.short_complete = self.shuttle_stage >= self.shuttle_stages
        self.long_complete = self.anchor_streak >= self.anchor_required_steps
        return bool(self.short_complete and self.long_complete)

    def _accept_expected_shuttle_contact(self, visitor: int) -> None:
        if self.shuttle_stage >= self.shuttle_stages:
            return
        expected_zone = self.shuttle_sequence[self.shuttle_stage]
        contacts = self._shuttle_contacts()
        if bool(contacts[visitor, expected_zone]):
            self.shuttle_stage += 1
            self.shuttle_stage_max = max(self.shuttle_stage_max, self.shuttle_stage)

    def step(self, actions):
        if not self.agents:
            raise RuntimeError("step() called after the episode ended")
        self._update_positions(actions)
        self.elapsed_steps += 1
        success = self._advance_duty_cycle()
        self.full_success = bool(self.full_success or success)
        reward = 1.0 if success else 0.0
        terminated = bool(success)
        truncated = bool(not terminated and self.elapsed_steps >= self.max_steps)
        observations = self._get_obs()
        rewards = {agent: reward for agent in self.possible_agents}
        terminations = {agent: terminated for agent in self.possible_agents}
        truncations = {agent: truncated for agent in self.possible_agents}
        infos = self._get_infos(reward)
        if terminated or truncated:
            self.agents = []
        return observations, rewards, terminations, truncations, infos
```

The same file must implement these exact representations:

```python
def _get_obs(self):
    result = {}
    for i, agent in enumerate(self.possible_agents):
        other = 1 - i
        own = self.positions[i]
        result[agent] = np.concatenate(
            (
                2.0 * own / self.world_size - 1.0,
                (self.positions[other] - own) / self.world_size,
                (self.anchor - own) / self.world_size,
                (self.shuttle_zones[0] - own) / self.world_size,
                (self.shuttle_zones[1] - own) / self.world_size,
            )
        ).astype(np.float32)
    return result

def _get_state(self):
    holder = np.zeros(2, dtype=np.float32)
    if self.active_holder >= 0:
        holder[self.active_holder] = 1.0
    return np.concatenate(
        (
            (2.0 * self.positions.reshape(-1) / self.world_size - 1.0),
            holder,
            np.asarray(
                [
                    self.shuttle_stage / self.shuttle_stages,
                    min(self.anchor_streak / self.anchor_required_steps, 1.0),
                    float(self.short_complete),
                    float(self.long_complete),
                ],
                dtype=np.float32,
            ),
        )
    ).astype(np.float32)
```

Define every remaining environment method with the following signatures and behavior so no task state leaks into actor observations:

```python
def __init__(self, config, render_mode=None, seed=None):
    self.config = config
    self.render_mode = render_mode
    self.world_size = float(getattr(config, "r38_world_size", 6.0))
    self.action_scale = float(getattr(config, "r38_action_scale", 0.5))
    self.zone_radius = float(getattr(config, "r38_zone_radius", 0.75))
    self.anchor_required_steps = int(getattr(config, "r38_anchor_required_steps", 40))
    self.shuttle_stages = int(getattr(config, "r38_shuttle_stages", 4))
    self.max_steps = int(getattr(config, "max_steps", 200))
    self.anchor = np.asarray([3.0, 3.0], dtype=np.float32)
    self.shuttle_zones = np.asarray([[1.0, 3.0], [5.0, 3.0]], dtype=np.float32)
    self.shuttle_sequence = (0, 1, 0, 1)
    self._action_space = Box(-1.0, 1.0, shape=(2,), dtype=np.float32)
    self._observation_space = Box(-1.0, 1.0, shape=(10,), dtype=np.float32)
    self.np_random = np.random.default_rng(seed)
    self.agents = list(self.possible_agents)
    self.positions = np.zeros((2, 2), dtype=np.float32)
    self._reset_episode_state()

def action_space(self, agent):
    return self._action_space

def observation_space(self, agent):
    return self._observation_space

def get_obs_dim(self):
    return 10

def get_state_dim(self):
    return 10

def _reset_episode_state(self):
    self.elapsed_steps = 0
    self.active_holder = -1
    self.anchor_streak = 0
    self.shuttle_stage = 0
    self.short_complete = False
    self.long_complete = False
    self.anchor_streak_max = 0
    self.shuttle_stage_max = 0
    self.full_success = False

def _reset_attempt(self):
    self.active_holder = -1
    self.anchor_streak = 0
    self.shuttle_stage = 0
    self.short_complete = False
    self.long_complete = False

def reset(self, seed=None, options=None):
    del options
    if seed is not None:
        self.np_random = np.random.default_rng(seed)
    anchor_spawn = self.anchor + self.np_random.uniform(-0.1, 0.1, size=2)
    visitor_spawn = np.asarray([2.0, 3.0]) + self.np_random.uniform(-0.1, 0.1, size=2)
    unordered = np.stack((anchor_spawn, visitor_spawn)).astype(np.float32)
    self.positions = unordered[self.np_random.permutation(2)].copy()
    self.agents = list(self.possible_agents)
    self._reset_episode_state()
    return self._get_obs(), self._get_infos(0.0)

def _update_positions(self, actions):
    for i, agent in enumerate(self.possible_agents):
        action = np.asarray(actions[agent], dtype=np.float32)
        if action.shape != (2,) or not np.all(np.isfinite(action)):
            raise ValueError(f"{agent} action must be a finite shape-(2,) vector")
        self.positions[i] = np.clip(
            self.positions[i] + self.action_scale * np.clip(action, -1.0, 1.0),
            0.0,
            self.world_size,
        )

def _anchor_contacts(self):
    return np.linalg.norm(self.positions - self.anchor, axis=1) <= self.zone_radius

def _shuttle_contacts(self):
    return np.linalg.norm(
        self.positions[:, None, :] - self.shuttle_zones[None, :, :], axis=2
    ) <= self.zone_radius

def _task_metrics(self, reward):
    return {
        "r38_short_duty_complete": float(self.shuttle_stage_max >= self.shuttle_stages),
        "r38_long_duty_complete": float(self.anchor_streak_max >= self.anchor_required_steps),
        "r38_full_cycle_success": float(self.full_success),
        "r38_anchor_streak_max": float(self.anchor_streak_max),
        "r38_shuttle_stage_max": float(self.shuttle_stage_max),
        "r38_sparse_reward": float(reward),
        "task_reward": float(reward),
        "intrinsic_reward": 0.0,
    }

def _get_infos(self, reward):
    metrics = self._task_metrics(reward)
    return {
        agent: {
            "scenario": "cooperative_two_timescale_sparse",
            "reward_info": dict(metrics),
        }
        for agent in self.possible_agents
    }

def get_current_state(self):
    return {
        "positions": self.positions.copy(),
        "active_holder": int(self.active_holder),
        "anchor_streak": int(self.anchor_streak),
        "shuttle_stage": int(self.shuttle_stage),
        "short_complete": bool(self.short_complete),
        "long_complete": bool(self.long_complete),
        "full_success": bool(self.full_success),
        "elapsed_steps": int(self.elapsed_steps),
    }

def close(self):
    self.agents = []
```

The file imports `numpy as np`, `Box` from `gymnasium.spaces`, and `ParallelEnv` from `pettingzoo`. Current-attempt `short_complete` and `long_complete` reset on holder break; the registered short/long metrics remain monotone episode access indicators through the max fields. The fixed shuttle sequence and reset distribution are identical for every agent identity.

- [ ] **Step 4: Run the focused state-machine tests**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py -q
```

Expected: `5 passed`; the success test terminates with shared reward one, the two holder tests stay reward-zero, and the swap test matches after exchanging agent indices.

- [ ] **Step 5: Commit the self-contained environment**

```powershell
git add envs/pettingzoo/cooperative_two_timescale_sparse.py tests/cooperative_two_timescale_sparse_test.py
git commit -m "feat: add cooperative two-timescale sparse environment"
```

Expected: one environment/test commit with no training-code changes.

### Task 3: Register the Scenario and Frozen MAPPO Configuration

**Files:**
- Create: `ha_ctse_process/config_r38_two_timescale_sparse.py`
- Modify: `ha_ctse_process/env_factory.py`
- Modify: `tests/cooperative_two_timescale_sparse_test.py`

**Interfaces:**
- Consumes: `CooperativeTwoTimescaleSparseEnv` from Task 2 and `ParallelToArrayAdapter`.
- Produces: scenario name `cooperative_two_timescale_sparse` and config module `ha_ctse_process.config_r38_two_timescale_sparse.Config` with observation/state/action shapes `10/10/2`.

- [ ] **Step 1: Add a failing factory/config test**

Append this case to `tests/cooperative_two_timescale_sparse_test.py`:

```python
from ha_ctse_process.config_r38_two_timescale_sparse import Config
from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario


def test_factory_adapter_preserves_sparse_shared_reward_and_shapes():
    assert normalize_scenario("cts") == "cooperative_two_timescale_sparse"
    env = make_env(
        Config,
        EnvSpec(scenario="cooperative_two_timescale_sparse", seed=11),
    )()
    obs, info = env.reset(seed=11)
    assert obs.shape == (2, 10)
    assert info["state"].shape == (10,)
    next_obs, reward, terminated, truncated, step_info = env.step(
        np.zeros((2, 2), dtype=np.float32)
    )
    assert next_obs.shape == (2, 10)
    assert reward == 0.0
    assert not terminated and not truncated
    reward_info = step_info["reward_info"]
    assert reward_info["r38_sparse_reward"] == 0.0
    assert reward_info["intrinsic_reward"] == 0.0
```

- [ ] **Step 2: Run the new factory test and confirm registration is missing**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py::test_factory_adapter_preserves_sparse_shared_reward_and_shapes -q
```

Expected: FAIL because the config module or scenario alias is not registered.

- [ ] **Step 3: Create the frozen R38 config**

Create `ha_ctse_process/config_r38_two_timescale_sparse.py` with this contract:

```python
"""R38 constant-code recurrent MAPPO access gate for the CTS benchmark."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_sparse_mappo import Config as SparseMAPPOConfig


class Config(SparseMAPPOConfig):
    algorithm = "r38_cts_constant_code_recurrent_mappo"
    scenario = "cooperative_two_timescale_sparse"
    scenario_label = "cooperative_two_timescale_sparse"

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 10
    obs_dim = 10
    action_dim = 2
    episode_length = 200
    max_steps = 200

    r38_world_size = 6.0
    r38_action_scale = 0.5
    r38_zone_radius = 0.75
    r38_anchor_required_steps = 40
    r38_shuttle_stages = 4

    constant_skill_no_high = True
    alice_bob_semantic_reward_enabled = False
    aem_joint_novelty_enabled = False
    r31_effect_mode = "off"
    transition_skill_reward_coef = 0.0
    process_reward_injection = "none"
    outcome_residual_injection = "none"
    topology_role_injection = "none"
    topology_potential_injection = "none"
    skill_effect_reward_injection = "none"
    skill_force_reward_injection = "none"

    lr_discoverer_actor = 3e-4
    lr_discoverer_critic = 3e-4
    gamma = 0.99
    low_gae_lambda = 0.95
    low_clip_epsilon = 0.2
    low_value_clip = 0.2
    low_value_loss_coef = 1.0
    low_entropy_coef = 0.01
    low_max_grad_norm = 0.5
    low_rnn_hidden_size = 64
    low_sequence_length = 20
    low_sequence_batch_size = 64
    low_ppo_epochs = 5
    ppo_epochs = 5
    use_recurrent_low_level = True
    use_centralized_low_value = True
    use_low_value_norm = True
```

Do not remove inherited modules: `constant_skill_no_high=True` is the existing behavior switch that pins the codes and skips high/process learning.

- [ ] **Step 4: Register the scenario in `ha_ctse_process/env_factory.py`**

Add the import, aliases, and construction branch:

```python
from envs.pettingzoo.cooperative_two_timescale_sparse import (
    CooperativeTwoTimescaleSparseEnv,
)

SCENARIO_ALIASES.update(
    {
        "cooperative_two_timescale_sparse": "cooperative_two_timescale_sparse",
        "cooperative-two-timescale-sparse": "cooperative_two_timescale_sparse",
        "r38_cts": "cooperative_two_timescale_sparse",
        "cts": "cooperative_two_timescale_sparse",
    }
)
```

In `_init()` add:

```python
elif scenario == "cooperative_two_timescale_sparse":
    raw_env = CooperativeTwoTimescaleSparseEnv(**kwargs)
```

- [ ] **Step 5: Run the focused environment/factory file once**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py -q
```

Expected: `6 passed`.

- [ ] **Step 6: Commit scenario integration**

```powershell
git add ha_ctse_process/config_r38_two_timescale_sparse.py ha_ctse_process/env_factory.py tests/cooperative_two_timescale_sparse_test.py
git commit -m "feat: register R38 CTS MAPPO access config"
```

Expected: one commit containing only scenario/config integration and its focused adapter test.

### Task 4: Expose the Evaluation and Manifest Contract

**Files:**
- Modify: `ha_ctse_process/plotting.py`
- Modify: `ha_ctse_process/train.py`
- Test: `tests/cooperative_two_timescale_sparse_test.py`

**Interfaces:**
- Consumes: the six environment metrics and existing `extract_eval_metrics`, `append_csv`, `ALGORITHM_MANIFEST_FIELDS`, `TRAINING_MANIFEST_FIELDS`, and `evaluate` paths.
- Produces: final `metrics/eval_episodes.csv` rows with the six CTS fields plus `terminated_flag` and `truncated_flag`, and manifests that expose all frozen R38 values.

- [ ] **Step 1: Register the exact evaluation fields in `ha_ctse_process/plotting.py`**

Add:

```python
R38_CTS_METRIC_FIELDS = (
    "r38_short_duty_complete",
    "r38_long_duty_complete",
    "r38_full_cycle_success",
    "r38_anchor_streak_max",
    "r38_shuttle_stage_max",
    "r38_sparse_reward",
)
```

Include `*R38_CTS_METRIC_FIELDS` in `extract_uav_metrics`' scalar-field loop and add these to `EVAL_FIELDS` immediately after `length`:

```python
"terminated_flag",
"truncated_flag",
*R38_CTS_METRIC_FIELDS,
```

- [ ] **Step 2: Extend the manifest allowlists in `ha_ctse_process/train.py`**

Add the environment and optimizer fields to the existing allowlists:

```python
# ALGORITHM_MANIFEST_FIELDS
"r38_world_size",
"r38_action_scale",
"r38_zone_radius",
"r38_anchor_required_steps",
"r38_shuttle_stages",
"lr_discoverer_actor",
"lr_discoverer_critic",

# TRAINING_MANIFEST_FIELDS
"low_gae_lambda",
"low_value_clip",
"low_value_loss_coef",
"low_sequence_length",
"low_sequence_batch_size",
"low_ppo_epochs",
```

The analyzer must read actual command-line exposure (`scenario`, `seed`, `num_envs`, `rollout_length`, `total_timesteps`, `device`, `eval_episodes`, `eval_action_mode`) from `manifest["args"]`; it must not infer CLI overrides from config defaults.

- [ ] **Step 3: Record the environment's terminal semantics in each eval row**

In `evaluate`, retain the final `terminated` and `truncated` booleans and add:

```python
eval_record = {
    "checkpoint": str(getattr(args, "eval_checkpoint_name", "")),
    "total_steps": int(total_steps),
    "episode": episode_idx,
    "reset_seed": reset_seed,
    "action_mode_code": 0.0 if deterministic_eval else 1.0,
    "reward": episode_reward,
    "length": episode_length,
    "terminated_flag": float(bool(terminated)),
    "truncated_flag": float(bool(truncated)),
    **r37_eval_metrics,
    **episode_metrics,
}
```

This instrumentation is required because M0 distinguishes success termination from horizon truncation; it does not alter training.

- [ ] **Step 4: Add one direct field-propagation assertion**

Extend the adapter test's final assertions:

```python
for field in (
    "r38_short_duty_complete",
    "r38_long_duty_complete",
    "r38_full_cycle_success",
    "r38_anchor_streak_max",
    "r38_shuttle_stage_max",
    "r38_sparse_reward",
):
    assert field in reward_info
```

- [ ] **Step 5: Run only the focused CTS test file**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py -q
```

Expected: `6 passed`; no broad regression suite is required at this algorithm-exploration boundary.

- [ ] **Step 6: Commit the evidence instrumentation**

```powershell
git add ha_ctse_process/plotting.py ha_ctse_process/train.py tests/cooperative_two_timescale_sparse_test.py
git commit -m "feat: record R38 CTS evaluation contract"
```

Expected: one commit containing only manifest/evaluation evidence fields and the direct propagation assertion.

### Task 5: Implement the Paired Analyzer and Local Runner

**Files:**
- Create: `scripts/analyze_r38_cts_access.py`
- Create: `tests/test_r38_cts_analyzer.py`
- Create: `scripts/run_r38_cts_access_local.ps1`

**Interfaces:**
- Consumes: trained checkpoint `<run-root>/runs/constant_code_mappo/seed39031/standalone_process_core_final.pt`, MAPPO eval CSV in that run, config module `ha_ctse_process.config_r38_two_timescale_sparse`, and `scripts/run_python_worker.ps1`.
- Produces: `<run-root>/result/r38_uniform_random_eval_episodes.csv`, `<run-root>/result/r38_cts_access.json`, and `<run-root>/runner_status.txt`.
- Produces statuses: `PASS_R38_CTS_ACCESS`, `FAIL_R38_CTS_ACCESS`, or `INVALID_R38_IMPLEMENTATION`; operational crashes set runner `state=failed` and do not manufacture a scientific status.

- [ ] **Step 1: Write failing analyzer tests for paired confidence bounds and branch order**

Create `tests/test_r38_cts_analyzer.py` around public functions `paired_bootstrap_ci(mappo, random, *, repetitions, seed)` and `decide_result(m0, m1, m2)`:

```python
import numpy as np

from scripts.analyze_r38_cts_access import decide_result, paired_bootstrap_ci


def test_paired_bootstrap_uses_episode_differences():
    mappo = np.ones(256, dtype=np.float64)
    random = np.zeros(256, dtype=np.float64)
    estimate, lower, upper = paired_bootstrap_ci(
        mappo, random, repetitions=10_000, seed=59_031
    )
    assert (estimate, lower, upper) == (1.0, 1.0, 1.0)


def test_decision_checks_implementation_before_science():
    assert decide_result(False, True, True) == "INVALID_R38_IMPLEMENTATION"
    assert decide_result(True, False, True) == "FAIL_R38_CTS_ACCESS"
    assert decide_result(True, True, False) == "FAIL_R38_CTS_ACCESS"
    assert decide_result(True, True, True) == "PASS_R38_CTS_ACCESS"
```

- [ ] **Step 2: Run the analyzer tests and confirm the module is absent**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/test_r38_cts_analyzer.py -q
```

Expected: collection fails with `ModuleNotFoundError: scripts.analyze_r38_cts_access`.

- [ ] **Step 3: Implement the analyzer's paired statistics and result branches**

In `scripts/analyze_r38_cts_access.py`, implement the public functions exactly as follows:

```python
def paired_bootstrap_ci(mappo, random, *, repetitions: int, seed: int):
    paired = np.asarray(mappo, dtype=np.float64) - np.asarray(random, dtype=np.float64)
    if paired.shape != (256,) or not np.all(np.isfinite(paired)):
        raise ValueError("paired bootstrap requires exactly 256 finite episode pairs")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, paired.size, size=(repetitions, paired.size))
    means = paired[draws].mean(axis=1)
    return (
        float(paired.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def decide_result(m0: bool, m1: bool, m2: bool) -> str:
    if not m0:
        return "INVALID_R38_IMPLEMENTATION"
    if not m1 or not m2:
        return "FAIL_R38_CTS_ACCESS"
    return "PASS_R38_CTS_ACCESS"
```

The script's random evaluator must instantiate `ParallelToArrayAdapter` through `make_env`, use reset seeds `139031..139286`, and draw each two-agent action array with:

```python
action_rng = np.random.default_rng(49_031)
actions = action_rng.uniform(-1.0, 1.0, size=(2, 2)).astype(np.float32)
```

For each episode, store the reset seed, reward, length, terminal flags, and six CTS metrics. Never call `Box.sample()` and never reseed the action RNG between episodes.

- [ ] **Step 4: Implement exact M0-M2 checks and one result schema**

The analyzer must apply these expressions without fallback branches:

```python
m1 = (
    rates["r38_short_duty_complete"] >= 0.10
    and rates["r38_long_duty_complete"] >= 0.05
    and rates["r38_full_cycle_success"] > 0.10
    and full_success_count >= 26
    and all(ci[1] > 0.0 for ci in paired_cis.values())
)
block_successes = [
    int(mappo_full[start : start + 64].sum())
    for start in range(0, 256, 64)
]
m2 = sum(count >= 1 for count in block_successes) >= 3
status = decide_result(m0, m1, m2)
```

M0 must fail closed on any of these facts: wrong config/scenario/seed/device/budget; not exactly 100 outer updates; not exactly 256 unique registered reset seeds in each policy; reset-order mismatch; non-finite action or metric; reward not equal to full-success indicator; nonzero reward before full success; nonzero intrinsic reward; success without termination; failed episode without step-200 truncation; nonconstant active skill/team code; high/process update count above zero; low update count other than 100; or any frozen optimizer/hyperparameter mismatch.

Write one JSON with these top-level fields:

```python
result = {
    "experiment_id": "EXP-20260715-r38-cts-access",
    "status": status,
    "scope": "single-seed environment-access gate; not algorithm efficacy evidence",
    "train_seed": 39031,
    "total_timesteps": 320000,
    "neutral_init_checkpoint": str(neutral_init_checkpoint),
    "implementation_valid": bool(m0),
    "invalid_reasons": invalid_reasons,
    "evaluation_contract": evaluation_contract,
    "policies": {"constant_code_mappo": mappo_summary, "uniform_random": random_summary},
    "paired_comparison": paired_comparison,
    "gates": {"M0": m0_payload, "M1": m1_payload, "M2": m2_payload},
    "decision": decision_payload,
}
```

- [ ] **Step 5: Run the analyzer tests**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/test_r38_cts_analyzer.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Implement the single-job PowerShell runner**

Create `scripts/run_r38_cts_access_local.ps1` with parameters `PythonExe`, `RunRoot`, and `Device="cuda"`. It must:

1. Reject a run root that already contains `runner_status.txt`.
2. Write `runner_status.txt` with `state=running`, first `phase=neutral_init`, then `phase=training_mappo`, then `phase=uniform_random_and_analysis`.
3. Create a zero-step neutral checkpoint at `<run-root>/init/neutral_cts_seed39031/standalone_process_core_final.pt` using config `ha_ctse_process.config_r38_two_timescale_sparse`.
4. Launch exactly one training worker through `scripts/run_python_worker.ps1` with this argument vector:

```powershell
$initArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config_r38_two_timescale_sparse",
    "--scenario", "cooperative_two_timescale_sparse",
    "--seed", "39031",
    "--n_agents", "2",
    "--collector_backend", "sync",
    "--num_envs", "1",
    "--rollout_length", "200",
    "--skill_interval", "10",
    "--total_timesteps", "0",
    "--eval_interval", "0",
    "--eval_episodes", "1",
    "--eval_max_steps", "200",
    "--eval_action_mode", "stochastic",
    "--save_interval", "0",
    "--checkpoint_keep_last", "1",
    "--plot_interval", "0",
    "--high_controller", "r30_fixed_clock_ar_edit",
    "--device", $Device,
    "--log_dir", $initRoot
)

$trainArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config_r38_two_timescale_sparse",
    "--scenario", "cooperative_two_timescale_sparse",
    "--seed", "39031",
    "--n_agents", "2",
    "--device", $Device,
    "--collector_backend", "subproc",
    "--collector_start_method", "spawn",
    "--num_envs", "16",
    "--rollout_length", "200",
    "--skill_interval", "10",
    "--total_timesteps", "320000",
    "--eval_interval", "320000",
    "--eval_episodes", "256",
    "--eval_action_mode", "stochastic",
    "--eval_max_steps", "200",
    "--save_interval", "0",
    "--checkpoint_keep_last", "1",
    "--plot_interval", "0",
    "--high_controller", "r30_fixed_clock_ar_edit",
    "--resume_from", $neutralCheckpoint,
    "--log_dir", $mappoRoot
)
```

5. Invoke `scripts/analyze_r38_cts_access.py --run-root $RunRoot` only after the worker exits zero.
6. Set runner `state=completed`, `phase=result`, and `result_path=<run-root>/result/r38_cts_access.json` for every scientific result, including valid FAIL.
7. On a process exception, set `state=failed`, `phase=runner`, preserve the error text, and do not write a scientific result JSON.

The default run root is:

```powershell
logs\r38_cts_access_320k_$(Get-Date -Format 'yyyyMMdd_HHmmss')
```

- [ ] **Step 7: Exercise only the runner's argument construction without training**

Use PowerShell's parser to load the script and the Python parser to import the analyzer:

```powershell
$null = [scriptblock]::Create((Get-Content -Raw scripts/run_r38_cts_access_local.ps1))
& C:\Users\wu\.conda\envs\SB3\python.exe -m py_compile scripts/analyze_r38_cts_access.py
```

Expected: both commands exit zero and create no run directory.

- [ ] **Step 8: Commit the runner and analyzer**

```powershell
git add scripts/analyze_r38_cts_access.py scripts/run_r38_cts_access_local.ps1 tests/test_r38_cts_analyzer.py
git commit -m "feat: add R38 CTS access runner and analyzer"
```

Expected: one commit containing the single-job runner, paired analyzer, and two focused analyzer tests.

### Task 6: Launch, Monitor, and Resolve the Registered Gate

**Files:**
- Modify after result: `memory/ExpRecord.md`
- Modify after result: `memory/CURRENT_WORK.md`
- Runtime output: `logs/r38_cts_access_320k_<timestamp>/runner_status.txt`
- Runtime output: `logs/r38_cts_access_320k_<timestamp>/result/r38_cts_access.json`

**Interfaces:**
- Consumes: all Tasks 1-5, local CUDA, and the existing dedicated experiment-monitor task/conversation.
- Produces: exactly one registered R38 scientific decision and one next action.

- [ ] **Step 1: Run the two focused test files once at the coherent implementation boundary**

Run:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m pytest tests/cooperative_two_timescale_sparse_test.py tests/test_r38_cts_analyzer.py -q
```

Expected: `8 passed`. Do not add a broad regression, smoke matrix, or artifact audit.

- [ ] **Step 2: Commit and push the exact experiment implementation**

Run:

```powershell
git status --short
git push origin aggressive
git rev-parse HEAD
```

Expected: only intended R38 files are committed, the aggressive branch push succeeds, and the printed commit is recorded in the run's `command.txt` or manifest by the runner.

- [ ] **Step 3: Launch the registered local CUDA experiment**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_r38_cts_access_local.ps1 -PythonExe C:\Users\wu\.conda\envs\SB3\python.exe -Device cuda
```

Expected immediately: one timestamped `logs/r38_cts_access_320k_*` root and `runner_status.txt` with `state=running`; training uses 16 parallel environments and no second algorithm arm.

- [ ] **Step 4: Point the existing dedicated monitor at the new run root**

Update the existing single-thread monitor rather than creating a new task/conversation. Its visible progress report must include phase, worker PID, completed environment steps out of 320,000, completed outer low updates out of 100, latest elapsed time, and current result path. It reports to the controller only on `state=completed`, `state=failed`, or a direct traceback; it does not infer a stall during final evaluation.

Expected: exactly one reusable monitor conversation and no heartbeat or per-update controller polling.

- [ ] **Step 5: Read the single result JSON once after completion**

Run:

```powershell
Get-Content -Raw <run-root>\result\r38_cts_access.json
```

Expected: one of `PASS_R38_CTS_ACCESS`, `FAIL_R38_CTS_ACCESS`, or `INVALID_R38_IMPLEMENTATION`, with M0-M2 fields and exactly 256 paired episodes per policy. Replace `<run-root>` with the timestamped path printed by the runner; do not scan other artifacts unless M0 or the runner names a concrete defect.

- [ ] **Step 6: Apply exactly one registered outcome branch**

- `PASS_R38_CTS_ACCESS`: update the R38 row to PASS, point `memory/CURRENT_WORK.md` to the result JSON, and make the sole next action “register one shared-fixed-k versus per-agent-lifetime mechanism gate.”
- `FAIL_R38_CTS_ACCESS`: update the row to FAIL, retire CTS, and return to algorithm design without changing reward, intrinsic, budget, seeds, learner, or thresholds.
- `INVALID_R38_IMPLEMENTATION`: record only the named M0 defect, fix that defect, and rerun the unchanged R38 contract.
- Runner `state=failed`: diagnose the direct operational traceback and retry only the failed runner phase; do not create a scientific decision.

- [ ] **Step 7: Commit and push the compact result boundary**

```powershell
git add memory/ExpRecord.md memory/CURRENT_WORK.md
git commit -m "docs: record R38 CTS access decision"
git push origin aggressive
```

Expected: the result remains owned by the timestamped `logs/` JSON; compact memory contains only the status, interpretation, pointer, and sole next action.

## Completion Criteria

- The environment structurally prevents one agent from completing both duties in one successful attempt.
- Swapping agent identities, positions, and actions preserves transitions and reward.
- The actor has geometry-only 10-dimensional observations; progress exists only in the 10-dimensional centralized critic state and diagnostic info.
- All reward before full success is zero, full success pays exactly shared `+1`, and intrinsic reward is always zero.
- The existing learner runs unchanged as functionally ordinary constant-code recurrent MAPPO for exactly 320,000 steps and 100 outer low updates.
- The analyzer compares MAPPO and uniform random on the same 256 resets with the registered paired bootstrap and applies M0 before M1/M2.
- One result JSON selects exactly one registered branch; no environment-specific intrinsic reward or rescue experiment is introduced.
