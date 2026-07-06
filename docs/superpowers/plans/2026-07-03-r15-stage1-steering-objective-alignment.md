# R15 Stage 1 Steering Objective Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the implemented prototype-response path with Round 15: AR-first skill assignment and coordinator-residual intrinsic reward using stored assignment log-prob as the null.

**Implementation status (2026-07-03):** first pass completed and locally validated.  See `memory/ExpRecord.md` -> `EXP-20260703-r15-stage1-steering` and `memory/cross_validation.md` -> `2026-07-03 Codex response: R15 Stage 1 steering objective implemented` for validation commands and next experiment gate.

**Architecture:** Keep the existing R14 prototype-response scaffolding, but replace the normal learned-prior residual with `log q_d(z_i | o'_i, kappa) - stored log pi_h(z_i | kappa, z_{1:i-1})`. Add a minimal autoregressive high-level assignment path by conditioning `SkillDurationPolicy` on an `ar_prefix` vector that summarizes already assigned skills in fixed agent-id order. Preserve the old learned-prior/parallel path only as an explicit R15-P1/R14.1 fallback ablation.

**Tech Stack:** Python 3, PyTorch, NumPy, pytest, existing HA-CTSE standalone trainer.

---

## File Structure

Modify:

- `ha_ctse_process/standalone_agent.py`
  - Add `ar_prefix` conditioning to `SkillDurationPolicy`.
  - Store `skill_assignment_logp`, `duration_assignment_logp`, `ar_prefix_start`, and `ar_parallel_kl_start` in each `Segment`.
  - Implement fixed-order AR selection in `StandaloneProcessAgent.maybe_assign_skills`.
  - Add stored-null fields to `_prototype_discriminator_batch`.
  - Use stored-null residual reward in `process_update`.
  - Add prototype AR/null diagnostics to metrics.

- `ha_ctse_process/prototype_response_discriminator.py`
  - Remove learned prior from the normal path.
  - Add optional learned-prior fallback behind `use_learned_prior`.
  - Compute residual against supplied `null_logp`.
  - Add `proto_disc_null_logp_mean` and keep old prior metrics zero unless fallback is active.

- `ha_ctse_process/config.py`
  - Add `legacy_n_skills_override=0` so A0 can run a four-skill legacy control without changing prototype arms.
  - Add `use_autoregressive_selection` and `parallel_selection`.
  - Add `prototype_disc_use_learned_prior=False`.
  - Keep `prototype_disc_prior_coef` only for fallback compatibility.

- `ha_ctse_process/train.py`
  - Add CLI `--legacy_n_skills`, `--parallel_selection`, and `--prototype_disc_use_learned_prior`.
  - Add manifest/checkpoint metadata for R15 mode.
  - Add TensorBoard/CSV/console metrics:
    `proto_disc_null_logp_mean`, `proto_assignment_logp_mean`,
    `proto_assignment_logp_std`, `proto_ar_parallel_kl`.

- `ha_ctse_process/plotting.py`
  - Add the new prototype metrics to CSV field aliases and plots.

- `scripts/run_r15_stage1_local_cuda.ps1`
  - Create an R15-specific runner with `control_legacy4`, `s1_probe`, `s1_reward`, and `r15_p1_ablation` arms.
  - Use the pre-registered local-read frame from `EXP-20260703-r15-stage1-steering`: S7-S1, 6 agents, 16 envs, 320k steps, `opt_num_prototypes=4`.
  - Keep `s1_reward` and `r15_p1_ablation` launchable by explicit arm name only; normal first launch is A0+A1.

- `tests/r14_prototype_response_test.py`
  - Replace old prior-head test with stored-null residual tests.
  - Add AR prefix/log-prob tests.

- `memory/ATTENTION_POINTER.md`, `memory/IMPLEMENTATION_PLAN.md`, `memory/ExpRecord.md`
  - Update after implementation and validation.

Do not touch:

- `ha_ctse_process/process_posterior.py`
- `ha_ctse_process/topology_potential.py`
- `ha_ctse_process/recovery_potential.py`
- P3 forcing reward modules
- R12 hazard logic

---

### Task 1: Write Failing Tests for the R15 Discriminator Null

**Files:**
- Modify: `tests/r14_prototype_response_test.py`
- Test target: `ha_ctse_process/prototype_response_discriminator.py`

- [ ] **Step 1: Replace the old prior-head test with a stored-null residual test**

Remove `test_prototype_response_prior_is_condition_only` and add:

```python
def test_prototype_response_uses_stored_assignment_null():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
        use_learned_prior=False,
    )
    condition = torch.randn(5, 2)
    obs = torch.randn(5, 4)
    labels = torch.tensor([0, 1, 2, 1, 0])
    null_logp = torch.tensor([-1.0, -0.5, -2.0, -0.25, -1.5])

    q_logits = module(obs, condition)
    q_logp = torch.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
    expected_residual = q_logp - null_logp

    loss, metrics = module.loss_and_metrics(obs, condition, labels, null_logp=null_logp)
    assert loss.ndim == 0
    assert metrics["proto_disc_samples"] == 5.0
    assert metrics["proto_disc_prior_loss"] == 0.0
    assert metrics["proto_disc_prior_acc"] == 0.0
    assert metrics["proto_disc_null_logp_mean"] == float(null_logp.mean())
    assert abs(metrics["proto_disc_residual_mean"] - float(expected_residual.mean())) < 1e-6

    reward = module.residual_reward(obs, condition, labels, null_logp=null_logp, clip=0.1)
    assert reward.shape == (5,)
    assert torch.max(torch.abs(reward)) <= 0.100001
```

- [ ] **Step 2: Add a fallback learned-prior test**

Add:

```python
def test_prototype_response_learned_prior_is_fallback_only():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
        use_learned_prior=True,
        prior_coef=0.5,
    )
    condition = torch.randn(5, 2)
    obs_a = torch.randn(5, 4)
    obs_b = torch.randn(5, 4) + 10.0
    labels = torch.tensor([0, 1, 2, 1, 0])

    q_a, prior_a = module.forward_with_prior(obs_a, condition)
    q_b, prior_b = module.forward_with_prior(obs_b, condition)
    assert q_a.shape == (5, 3)
    assert prior_a.shape == (5, 3)
    assert not torch.allclose(q_a, q_b)
    torch.testing.assert_close(prior_a, prior_b)

    loss, metrics = module.loss_and_metrics(obs_a, condition, labels)
    assert loss.ndim == 0
    assert metrics["proto_disc_prior_loss"] > 0.0
    assert metrics["proto_disc_prior_acc"] >= 0.0
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py::test_prototype_response_uses_stored_assignment_null tests\r14_prototype_response_test.py::test_prototype_response_learned_prior_is_fallback_only -q
```

Expected: both tests fail because `PrototypeResponseDiscriminator` does not accept `use_learned_prior`, does not accept `null_logp`, and `forward()` still returns `(q_logits, prior_logits)`.

---

### Task 2: Refactor PrototypeResponseDiscriminator Around Stored Null Log-Prob

**Files:**
- Modify: `ha_ctse_process/prototype_response_discriminator.py`
- Test: `tests/r14_prototype_response_test.py`

- [ ] **Step 1: Extend the metric field tuple**

Replace `PROTOTYPE_DISC_METRIC_FIELDS` with:

```python
PROTOTYPE_DISC_METRIC_FIELDS = (
    "proto_disc_active",
    "proto_disc_samples",
    "proto_disc_loss",
    "proto_disc_q_loss",
    "proto_disc_prior_loss",
    "proto_disc_acc",
    "proto_disc_prior_acc",
    "proto_disc_null_logp_mean",
    "proto_disc_residual_mean",
    "proto_disc_residual_positive_frac",
    "proto_disc_acc_by_skill_std",
    "proto_disc_reward_mean",
    "proto_disc_reward_unclipped_mean",
    "proto_disc_reward_applied_steps",
    "proto_disc_reward_env_ratio",
)
```

- [ ] **Step 2: Update the config dataclass**

Change `PrototypeDiscConfig` to:

```python
@dataclass(frozen=True)
class PrototypeDiscConfig:
    obs_dim: int
    n_skills: int
    condition_dim: int
    hidden_dim: int = 128
    use_learned_prior: bool = False
    prior_coef: float = 1.0
```

- [ ] **Step 3: Update the module constructor**

Change the constructor signature and prior-head creation:

```python
def __init__(
    self,
    obs_dim: int,
    n_skills: int,
    condition_dim: int,
    hidden_dim: int = 128,
    use_learned_prior: bool = False,
    prior_coef: float = 1.0,
):
    super().__init__()
    self.obs_dim = int(obs_dim)
    self.n_skills = int(max(n_skills, 1))
    self.condition_dim = int(max(condition_dim, 0))
    self.prior_input_dim = max(self.condition_dim, 1)
    self.use_learned_prior = bool(use_learned_prior)
    self.prior_coef = float(prior_coef)
    self.q_head = nn.Sequential(
        nn.LayerNorm(self.obs_dim + self.condition_dim),
        nn.Linear(self.obs_dim + self.condition_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, self.n_skills),
    )
    self.prior_head = (
        nn.Sequential(
            nn.LayerNorm(self.prior_input_dim),
            nn.Linear(self.prior_input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, self.n_skills),
        )
        if self.use_learned_prior
        else None
    )
```

- [ ] **Step 4: Split normal forward from fallback prior forward**

Replace `forward()` with:

```python
def forward(self, next_obs: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
    next_obs = next_obs.float()
    if self.condition_dim > 0:
        condition = condition.float()
        q_input = torch.cat([next_obs, condition], dim=-1)
    else:
        condition = torch.zeros(next_obs.shape[0], 0, dtype=next_obs.dtype, device=next_obs.device)
        q_input = next_obs
    return self.q_head(q_input)

def forward_with_prior(self, next_obs: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    q_logits = self.forward(next_obs, condition)
    if self.prior_head is None:
        raise RuntimeError("learned prior head is disabled; pass null_logp instead")
    return q_logits, self.prior_head(self._prior_input(condition))
```

- [ ] **Step 5: Rewrite `loss_and_metrics()`**

Use this behavior:

```python
def loss_and_metrics(
    self,
    next_obs: torch.Tensor,
    condition: torch.Tensor,
    labels: torch.Tensor,
    null_logp: torch.Tensor | None = None,
) -> tuple[torch.Tensor, dict[str, float]]:
    labels = labels.long().clamp(0, self.n_skills - 1)
    q_logits = self.forward(next_obs, condition)
    q_loss = F.cross_entropy(q_logits, labels)
    q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)

    prior_loss = torch.zeros((), dtype=q_loss.dtype, device=q_loss.device)
    prior_acc = torch.zeros((), dtype=q_loss.dtype, device=q_loss.device)
    if self.use_learned_prior:
        _, prior_logits = self.forward_with_prior(next_obs, condition)
        prior_loss = F.cross_entropy(prior_logits, labels)
        prior_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        prior_acc = self._accuracy(prior_logits, labels)
        null_logp_t = prior_logp.detach()
    else:
        if null_logp is None:
            raise ValueError("null_logp is required when learned prior is disabled")
        null_logp_t = null_logp.to(device=q_logp.device, dtype=q_logp.dtype).reshape_as(q_logp)

    total_loss = q_loss + float(self.prior_coef) * prior_loss
    residual = q_logp - null_logp_t.detach()

    def scalar(value: torch.Tensor) -> float:
        return float(value.detach().cpu().item())

    metrics = empty_prototype_disc_metrics()
    metrics.update(
        {
            "proto_disc_active": 1.0,
            "proto_disc_samples": float(labels.numel()),
            "proto_disc_loss": scalar(total_loss),
            "proto_disc_q_loss": scalar(q_loss),
            "proto_disc_prior_loss": scalar(prior_loss),
            "proto_disc_acc": scalar(self._accuracy(q_logits, labels)),
            "proto_disc_prior_acc": scalar(prior_acc),
            "proto_disc_null_logp_mean": scalar(null_logp_t.mean()),
            "proto_disc_residual_mean": scalar(residual.mean()),
            "proto_disc_residual_positive_frac": scalar((residual > 0.0).float().mean()),
            "proto_disc_acc_by_skill_std": scalar(self._acc_by_skill_std(q_logits, labels, self.n_skills)),
        }
    )
    return total_loss, metrics
```

- [ ] **Step 6: Rewrite `residual_reward()`**

Use:

```python
@torch.no_grad()
def residual_reward(
    self,
    next_obs: torch.Tensor,
    condition: torch.Tensor,
    labels: torch.Tensor,
    *,
    null_logp: torch.Tensor | None = None,
    clip: float = 2.0,
) -> torch.Tensor:
    labels = labels.long().clamp(0, self.n_skills - 1)
    q_logits = self.forward(next_obs, condition)
    q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
    if self.use_learned_prior:
        _, prior_logits = self.forward_with_prior(next_obs, condition)
        baseline_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
    else:
        if null_logp is None:
            raise ValueError("null_logp is required when learned prior is disabled")
        baseline_logp = null_logp.to(device=q_logp.device, dtype=q_logp.dtype).reshape_as(q_logp)
    reward = q_logp - baseline_logp
    if float(clip) > 0.0:
        reward = reward.clamp(-float(clip), float(clip))
    return reward
```

- [ ] **Step 7: Update `prototype_disc_config_from_agent()`**

Add:

```python
use_learned_prior=bool(getattr(agent, "prototype_disc_use_learned_prior", False)),
```

- [ ] **Step 8: Run tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py::test_prototype_response_uses_stored_assignment_null tests\r14_prototype_response_test.py::test_prototype_response_learned_prior_is_fallback_only -q
```

Expected: both pass.

---

### Task 3: Add AR Prefix and Skill-Only Assignment Log-Prob to High Policy

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Test: `tests/r14_prototype_response_test.py`

- [ ] **Step 1: Add the failing high-policy test**

Add:

```python
def test_skill_duration_policy_returns_skill_logp_parts_with_ar_prefix():
    policy = SkillDurationPolicy(
        obs_dim=3,
        n_skills=4,
        n_durations=2,
        hidden_dim=8,
        compact_dim=5,
        team_code_dim=6,
        omega_dim=3,
        agent_relevance_dim=3,
        ar_prefix_dim=4,
    )
    batch = 7
    obs = torch.randn(batch, 3)
    prev = torch.zeros(batch, dtype=torch.long)
    ages = torch.zeros(batch)
    compact = torch.randn(batch, 5)
    team = torch.randn(batch, 6)
    omega = torch.softmax(torch.randn(batch, 3), dim=-1)
    relevance = torch.softmax(torch.randn(batch, 3), dim=-1)
    prefix = torch.zeros(batch, 4)
    prefix[:, 1] = 1.0

    sample = policy.act_with_parts(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=prefix,
        deterministic=False,
    )

    assert sample.skills.shape == (batch,)
    assert sample.durations.shape == (batch,)
    assert sample.logp.shape == (batch,)
    assert sample.skill_logp.shape == (batch,)
    assert sample.duration_logp.shape == (batch,)
    torch.testing.assert_close(sample.logp, sample.skill_logp + sample.duration_logp)

    zero_prefix_logits = policy.logits(obs, prev, ages, compact, team, omega, relevance, torch.zeros_like(prefix))[0]
    one_prefix_logits = policy.logits(obs, prev, ages, compact, team, omega, relevance, prefix)[0]
    assert not torch.allclose(zero_prefix_logits, one_prefix_logits)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py::test_skill_duration_policy_returns_skill_logp_parts_with_ar_prefix -q
```

Expected: FAIL because `SkillDurationPolicy` has no `ar_prefix_dim`, `ar_prefix`, or `act_with_parts`.

- [ ] **Step 3: Add `HighActionSample` dataclass**

Place before `SkillDurationPolicy`:

```python
@dataclass
class HighActionSample:
    skills: torch.Tensor
    durations: torch.Tensor
    logp: torch.Tensor
    entropy: torch.Tensor
    value: torch.Tensor
    skill_logp: torch.Tensor
    duration_logp: torch.Tensor
```

- [ ] **Step 4: Extend `SkillDurationPolicy.__init__()`**

Add parameter:

```python
ar_prefix_dim: int = 0,
```

Store it and add it to `input_dim`:

```python
self.ar_prefix_dim = int(max(ar_prefix_dim, 0))
...
+ self.ar_prefix_dim
```

- [ ] **Step 5: Extend `_features()` and `logits()`**

Add argument:

```python
ar_prefix: torch.Tensor | None = None,
```

Inside `_features()` append:

```python
if self.ar_prefix_dim > 0:
    if ar_prefix is None:
        ar_prefix = torch.zeros(obs.shape[0], self.ar_prefix_dim, dtype=obs.dtype, device=obs.device)
    pieces.append(ar_prefix.float())
```

Pass `ar_prefix` through `logits()`.

- [ ] **Step 6: Implement `act_with_parts()` and keep `act()` backward compatible**

Add:

```python
def act_with_parts(
    self,
    obs: torch.Tensor,
    prev_skills: torch.Tensor,
    ages: torch.Tensor,
    compact: torch.Tensor,
    team_vector: torch.Tensor,
    omega: torch.Tensor | None = None,
    agent_relevance: torch.Tensor | None = None,
    ar_prefix: torch.Tensor | None = None,
    deterministic: bool = False,
) -> HighActionSample:
    skill_logits, duration_logits, value = self.logits(
        obs,
        prev_skills,
        ages,
        compact,
        team_vector,
        omega=omega,
        agent_relevance=agent_relevance,
        ar_prefix=ar_prefix,
    )
    skill_dist = Categorical(logits=skill_logits)
    duration_dist = Categorical(logits=duration_logits)
    if deterministic:
        skills = torch.argmax(skill_logits, dim=-1)
        durations = torch.argmax(duration_logits, dim=-1)
    else:
        skills = skill_dist.sample()
        durations = duration_dist.sample()
    skill_logp = skill_dist.log_prob(skills)
    duration_logp = duration_dist.log_prob(durations)
    return HighActionSample(
        skills=skills,
        durations=durations,
        logp=skill_logp + duration_logp,
        entropy=skill_dist.entropy() + duration_dist.entropy(),
        value=value,
        skill_logp=skill_logp,
        duration_logp=duration_logp,
    )
```

Change `act()` to call `act_with_parts()` and return the original 5-tuple:

```python
sample = self.act_with_parts(...same args...)
return sample.skills, sample.durations, sample.logp, sample.entropy, sample.value
```

- [ ] **Step 7: Extend `evaluate()`**

Add `ar_prefix` argument and pass it to `logits()`. Keep the returned value as the original 3-tuple.

- [ ] **Step 8: Run test**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py::test_skill_duration_policy_returns_skill_logp_parts_with_ar_prefix -q
```

Expected: PASS.

---

### Task 4: Store R15 Assignment Nulls in Segment Lifecycle

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Test: `tests/r14_prototype_response_test.py`

- [ ] **Step 1: Add Segment fields**

In `Segment`, after `high_logp`, add:

```python
    skill_assignment_logp: float = 0.0
    duration_assignment_logp: float = 0.0
    ar_parallel_kl_start: float = 0.0
    ar_prefix_start: np.ndarray | None = None
```

- [ ] **Step 2: Add `SegmentManager.renew()` parameters**

Add:

```python
        skill_assignment_logp: float = 0.0,
        duration_assignment_logp: float = 0.0,
        ar_parallel_kl_start: float = 0.0,
        ar_prefix_start=None,
```

Set them in the new `Segment(...)`.

- [ ] **Step 3: Extend `_prototype_discriminator_batch()` rows**

Add lists:

```python
        null_logp_rows: list[float] = []
        ar_kl_rows: list[float] = []
```

Inside the per-step loop append:

```python
                null_logp_rows.append(float(segment.skill_assignment_logp))
                ar_kl_rows.append(float(segment.ar_parallel_kl_start))
```

Return arrays:

```python
            "null_logp": np.asarray(null_logp_rows, dtype=np.float32)[chosen],
            "ar_parallel_kl": np.asarray(ar_kl_rows, dtype=np.float32)[chosen],
```

- [ ] **Step 4: Add a narrow batch test**

Add a small helper test using `Segment` directly:

```python
def test_prototype_batch_broadcasts_skill_assignment_null():
    from ha_ctse_process.standalone_agent import Segment

    seg = Segment(
        env_id=0,
        agent_id=1,
        skill=2,
        duration_idx=0,
        start_step=0,
        high_obs=torch.zeros(3).numpy(),
        high_logp=-3.0,
        skill_assignment_logp=-1.25,
        duration_assignment_logp=-0.75,
        high_value=0.0,
        high_entropy=0.0,
        duration_target=1,
        kappa_start=1,
        omega_start=torch.tensor([0.2, 0.8]).numpy(),
        agent_relevance_start=torch.tensor([0.7, 0.3]).numpy(),
    )
    seg.append(
        obs=torch.zeros(3).numpy(),
        action=torch.zeros(1).numpy(),
        reward=0.5,
        next_obs=torch.ones(3).numpy(),
        rollout_idx=4,
    )

    agent = object.__new__(StandaloneProcessAgent)
    agent.prototype_discriminator = object()
    agent.obs_dim = 3
    agent.opt_num_prototypes = 2
    agent.transition_skill_max_samples = 8192
    batch = StandaloneProcessAgent._prototype_discriminator_batch(agent, [seg])

    assert batch is not None
    assert batch["labels"].tolist() == [2]
    assert batch["null_logp"].tolist() == [-1.25]
    assert batch["rollout_indices"].tolist() == [4]
```

- [ ] **Step 5: Run the new batch test**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py::test_prototype_batch_broadcasts_skill_assignment_null -q
```

Expected: PASS after the Segment and batch changes.

---

### Task 5: Implement AR-First Selection and R15-P1 Parallel Fallback

**Files:**
- Modify: `ha_ctse_process/config.py`
- Modify: `ha_ctse_process/standalone_agent.py`
- Modify: `ha_ctse_process/train.py`

- [ ] **Step 1: Add config defaults**

In `ha_ctse_process/config.py`, near prototype settings, add:

```python
    legacy_n_skills_override = 0
    use_autoregressive_selection = True
    parallel_selection = False
    prototype_disc_use_learned_prior = False
```

- [ ] **Step 2: Add agent flags**

In `StandaloneProcessAgent.__init__`, after prototype response flags:

```python
self.parallel_selection = bool(getattr(config, "parallel_selection", False))
self.use_autoregressive_selection = bool(
    self.use_prototype_response_skills
    and getattr(config, "use_autoregressive_selection", True)
    and not self.parallel_selection
)
self.prototype_disc_use_learned_prior = bool(getattr(config, "prototype_disc_use_learned_prior", False))
```

- [ ] **Step 3: Add legacy skill-count override**

Replace the legacy skill-count initialization in `StandaloneProcessAgent.__init__` with:

```python
self.n_skills = int(getattr(config, "n_z", 3))
legacy_override = int(getattr(config, "legacy_n_skills_override", 0) or 0)
if legacy_override > 0 and not self.use_prototype_response_skills:
    self.n_skills = int(legacy_override)
if self.use_prototype_response_skills:
    self.n_skills = int(self.opt_num_prototypes + self.prototype_skill_extra_codes)
```

- [ ] **Step 4: Pass AR input dimension to high policy**

Where `SkillDurationPolicy(...)` is constructed, pass:

```python
ar_prefix_dim=(self.n_skills if self.use_autoregressive_selection else 0),
```

- [ ] **Step 5: Instantiate discriminator with fallback flag**

Change the `PrototypeResponseDiscriminator(...)` call to:

```python
PrototypeResponseDiscriminator(
    obs_dim=self.obs_dim,
    n_skills=self.n_skills,
    condition_dim=self.prototype_disc_condition_dim,
    hidden_dim=self.prototype_disc_hidden_dim,
    use_learned_prior=self.prototype_disc_use_learned_prior,
    prior_coef=self.prototype_disc_prior_coef,
).to(self.device)
```

- [ ] **Step 6: Add helper for AR prefix vectors**

Add inside `StandaloneProcessAgent`:

```python
def _ar_prefix_tensor(self, counts: np.ndarray, denom: int, batch: int = 1) -> torch.Tensor:
    prefix = np.asarray(counts, dtype=np.float32).reshape(1, -1)
    if int(denom) > 0:
        prefix = prefix / float(max(denom, 1))
    if prefix.shape[1] != int(self.n_skills):
        fitted = np.zeros((1, int(self.n_skills)), dtype=np.float32)
        fitted[:, : min(fitted.shape[1], prefix.shape[1])] = prefix[:, : min(fitted.shape[1], prefix.shape[1])]
        prefix = fitted
    if int(batch) != 1:
        prefix = np.repeat(prefix, int(batch), axis=0)
    return torch.as_tensor(prefix, dtype=torch.float32, device=self.device)
```

- [ ] **Step 7: Add helper for AR-vs-parallel KL**

Add:

```python
@torch.no_grad()
def _skill_parallel_kl(
    self,
    obs_t: torch.Tensor,
    prev_t: torch.Tensor,
    age_t: torch.Tensor,
    compact_t: torch.Tensor,
    team_vector_t: torch.Tensor,
    omega_t: torch.Tensor | None,
    agent_relevance_t: torch.Tensor | None,
    ar_prefix_t: torch.Tensor | None,
) -> float:
    if ar_prefix_t is None or not self.use_autoregressive_selection:
        return 0.0
    ar_skill_logits, _ar_dur_logits, _ = self.high.logits(
        obs_t,
        prev_t,
        age_t,
        compact_t,
        team_vector_t,
        omega=omega_t,
        agent_relevance=agent_relevance_t,
        ar_prefix=ar_prefix_t,
    )
    zero_prefix = torch.zeros_like(ar_prefix_t)
    par_skill_logits, _par_dur_logits, _ = self.high.logits(
        obs_t,
        prev_t,
        age_t,
        compact_t,
        team_vector_t,
        omega=omega_t,
        agent_relevance=agent_relevance_t,
        ar_prefix=zero_prefix,
    )
    ar_logp = F.log_softmax(ar_skill_logits, dim=-1)
    par_logp = F.log_softmax(par_skill_logits, dim=-1)
    ar_prob = ar_logp.exp()
    return float((ar_prob * (ar_logp - par_logp)).sum(dim=-1).mean().detach().cpu().item())
```

- [ ] **Step 8: Replace parallel high selection in `maybe_assign_skills()`**

In the `has_expired` branch, keep the existing parallel path when `not self.use_autoregressive_selection`. Add an AR branch when true:

```python
if self.use_autoregressive_selection:
    chosen_skills = []
    chosen_duration_idx = []
    old_logp = []
    old_entropy = []
    old_value = []
    skill_assignment_logp = []
    duration_assignment_logp = []
    ar_parallel_kl = []
    ar_prefix_rows = []
    prefix_counts = np.zeros(int(self.n_skills), dtype=np.float32)
    for order_idx, agent_id in enumerate(expired_ids):
        obs_one = torch.as_tensor(joint_obs[[agent_id]], dtype=torch.float32, device=self.device)
        prev_one = torch.as_tensor([self.active_skills[env_id, agent_id]], dtype=torch.long, device=self.device)
        age_one = torch.as_tensor([self.skill_age[env_id, agent_id]], dtype=torch.float32, device=self.device)
        compact_one = compact.expand(1, -1)
        team_one = team_vector.expand(1, -1)
        omega_one = weights.expand(1, -1) if self.high_condition_on_omega else None
        rel_one = None
        if self.use_agent_prototype_relevance:
            rel_one = agent_relevance[0, int(agent_id), :].reshape(1, -1)
        prefix_one = self._ar_prefix_tensor(prefix_counts, order_idx, batch=1)
        sample = self.high.act_with_parts(
            obs_one,
            prev_one,
            age_one,
            compact_one,
            team_one,
            omega=omega_one,
            agent_relevance=rel_one,
            ar_prefix=prefix_one,
            deterministic=deterministic,
        )
        selected_skill = int(sample.skills.detach().cpu().item())
        selected_duration = int(sample.durations.detach().cpu().item())
        chosen_skills.append(selected_skill)
        chosen_duration_idx.append(selected_duration)
        old_logp.append(float((sample.logp + team_logp * team_logp_weight).detach().cpu().item()))
        old_entropy.append(float((sample.entropy + team_entropy * team_logp_weight).detach().cpu().item()))
        old_value.append(float(sample.value.detach().cpu().item()))
        skill_assignment_logp.append(float(sample.skill_logp.detach().cpu().item()))
        duration_assignment_logp.append(float(sample.duration_logp.detach().cpu().item()))
        ar_parallel_kl.append(self._skill_parallel_kl(obs_one, prev_one, age_one, compact_one, team_one, omega_one, rel_one, prefix_one))
        ar_prefix_rows.append(prefix_one.detach().cpu().numpy().reshape(-1))
        prefix_counts[selected_skill] += 1.0
    chosen_skills = np.asarray(chosen_skills, dtype=np.int64)
    chosen_duration_idx = np.asarray(chosen_duration_idx, dtype=np.int64)
    old_logp = np.asarray(old_logp, dtype=np.float32)
    old_entropy = np.asarray(old_entropy, dtype=np.float32)
    old_value = np.asarray(old_value, dtype=np.float32)
    skill_assignment_logp = np.asarray(skill_assignment_logp, dtype=np.float32)
    duration_assignment_logp = np.asarray(duration_assignment_logp, dtype=np.float32)
    ar_parallel_kl = np.asarray(ar_parallel_kl, dtype=np.float32)
else:
    # existing parallel branch, plus:
    skill_assignment_logp = logp.cpu().numpy()  # overwritten by Step 9 with skill-only logp
    duration_assignment_logp = np.zeros_like(skill_assignment_logp)
    ar_parallel_kl = np.zeros_like(skill_assignment_logp)
    ar_prefix_rows = [np.zeros(int(self.n_skills), dtype=np.float32) for _ in expired_ids]
```

- [ ] **Step 9: In the parallel branch, use `act_with_parts()`**

Replace `self.high.act(...)` with `self.high.act_with_parts(...)` and derive:

```python
skills = sample.skills
duration_idx = sample.durations
logp = sample.logp
entropy = sample.entropy
value = sample.value
skill_assignment_logp = sample.skill_logp.cpu().numpy()
duration_assignment_logp = sample.duration_logp.cpu().numpy()
```

- [ ] **Step 10: Pass stored fields to `segments.renew()`**

Add:

```python
skill_assignment_logp=float(skill_assignment_logp[local_idx]),
duration_assignment_logp=float(duration_assignment_logp[local_idx]),
ar_parallel_kl_start=float(ar_parallel_kl[local_idx]),
ar_prefix_start=ar_prefix_rows[local_idx],
```

- [ ] **Step 11: Update high-level PPO evaluation**

In `update_high_from_segments()`, build:

```python
ar_prefix_np = np.asarray([
    np.zeros(int(self.n_skills), dtype=np.float32)
    if s.ar_prefix_start is None
    else self._fit_vector(s.ar_prefix_start, int(self.n_skills))
    for s in segments
], dtype=np.float32)
ar_prefix_t = (
    torch.as_tensor(ar_prefix_np, dtype=torch.float32, device=self.device)
    if self.use_autoregressive_selection
    else None
)
```

Pass `ar_prefix=ar_prefix_t` into `self.high.evaluate(...)`.

- [ ] **Step 12: Run targeted tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py -q
```

Expected: all tests pass.

---

### Task 6: Wire Stored Null Into Prototype Discriminator Update and Reward

**Files:**
- Modify: `ha_ctse_process/standalone_agent.py`
- Test: `tests/r14_prototype_response_test.py`

- [ ] **Step 1: Convert batch null logp to tensor**

In `process_update()` after `proto_condition_t`, add:

```python
proto_null_logp_t = torch.as_tensor(
    prototype_batch["null_logp"],
    dtype=torch.float32,
    device=self.device,
)
```

- [ ] **Step 2: Pass null into reward preview**

Change:

```python
prototype_reward_t = self.prototype_discriminator.residual_reward(
    proto_next_obs_t,
    proto_condition_t,
    proto_labels_t,
    clip=self.prototype_disc_clip,
)
```

to:

```python
prototype_reward_t = self.prototype_discriminator.residual_reward(
    proto_next_obs_t,
    proto_condition_t,
    proto_labels_t,
    null_logp=proto_null_logp_t,
    clip=self.prototype_disc_clip,
)
```

- [ ] **Step 3: Pass null into training loss**

Change:

```python
proto_loss, prototype_metrics = self.prototype_discriminator.loss_and_metrics(
    proto_next_obs_t,
    proto_condition_t,
    proto_labels_t,
)
```

to:

```python
proto_loss, prototype_metrics = self.prototype_discriminator.loss_and_metrics(
    proto_next_obs_t,
    proto_condition_t,
    proto_labels_t,
    null_logp=proto_null_logp_t,
)
```

- [ ] **Step 4: Add assignment diagnostics**

After metrics are returned:

```python
prototype_metrics["proto_assignment_logp_mean"] = float(np.mean(prototype_batch["null_logp"]))
prototype_metrics["proto_assignment_logp_std"] = float(np.std(prototype_batch["null_logp"]))
prototype_metrics["proto_ar_parallel_kl"] = float(np.mean(prototype_batch["ar_parallel_kl"]))
```

- [ ] **Step 5: Run tests**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py -q
```

Expected: all tests pass.

---

### Task 7: CLI, Manifest, Logging, Plotting, and R15 Runner Alignment

**Files:**
- Modify: `ha_ctse_process/train.py`
- Modify: `ha_ctse_process/plotting.py`
- Create: `scripts/run_r15_stage1_local_cuda.ps1`

- [ ] **Step 1: Add metric fields to train CSV/TensorBoard**

In `train.py`, add these fields next to prototype discriminator fields:

```python
"proto_disc_null_logp_mean",
"proto_assignment_logp_mean",
"proto_assignment_logp_std",
"proto_ar_parallel_kl",
```

In `write_tensorboard_metrics()`, include those keys in the `PrototypeDisc/*` loop.

- [ ] **Step 2: Add CLI flags**

Add parser flags:

```python
parser.add_argument("--legacy_n_skills", type=int, default=0)
parser.add_argument("--parallel_selection", action="store_true")
parser.add_argument("--prototype_disc_use_learned_prior", action="store_true")
```

In config application:

```python
if int(args.legacy_n_skills) > 0:
    config.legacy_n_skills_override = int(args.legacy_n_skills)
    if not bool(getattr(config, "use_prototype_response_skills", False)):
        config.n_z = int(args.legacy_n_skills)
        config.n_Z = int(args.legacy_n_skills)
if args.parallel_selection:
    config.parallel_selection = True
    config.use_autoregressive_selection = False
if args.prototype_disc_use_learned_prior:
    config.prototype_disc_use_learned_prior = True
```

- [ ] **Step 3: Add run header fields**

In the startup emit block, add:

```python
f"ar_selection={bool(getattr(config, 'use_autoregressive_selection', True) and not getattr(config, 'parallel_selection', False))} "
f"parallel_selection={bool(getattr(config, 'parallel_selection', False))} "
f"proto_disc_learned_prior={bool(getattr(config, 'prototype_disc_use_learned_prior', False))} "
```

- [ ] **Step 4: Add console metrics**

In `standalone_update` emit, add:

```python
f"proto_null={process_metrics.get('proto_disc_null_logp_mean', 0.0):.6f} "
f"proto_ar_kl={process_metrics.get('proto_ar_parallel_kl', 0.0):.6f} "
```

- [ ] **Step 5: Add plotting fields**

In `plotting.py`, add the four new metrics to the prototype diagnostics list and CLI aliases:

```python
"proto_disc_null_logp_mean",
"proto_assignment_logp_mean",
"proto_assignment_logp_std",
"proto_ar_parallel_kl",
```

Aliases:

```python
"proto_null": "proto_disc_null_logp_mean",
"proto_ar_kl": "proto_ar_parallel_kl",
```

- [ ] **Step 6: Create R15 runner**

Create `scripts/run_r15_stage1_local_cuda.ps1` by copying the structure of
`scripts/run_r14_stage1_local_cuda.ps1`, then set these R15-specific defaults:

```powershell
param(
  [string]$Experiments = "control_legacy4,s1_probe",
  [int]$TotalTimesteps = 320000,
  [int]$NumEnvs = 16,
  [string]$Device = "cuda",
  [int]$Seed = 1,
  [switch]$DryRun
)
```

Required common arguments for all arms:

```powershell
--scenario energy
--preset S7-S1
--n_agents 6
--collector_backend subproc
--collector_start_method spawn
--num_envs $NumEnvs
--rollout_length 500
--skill_interval 10
--skill_lifetime_candidates 3,7,13,24
--total_timesteps $TotalTimesteps
--eval_interval 160000
--eval_episodes 20
--low_clip_epsilon 0.1
--smdp_bootstrap_coef 0.25
--device $Device
--opt_num_prototypes 4
--prototype_skill_extra_codes 0
--disable_process_posterior_mi
--disable_outcome_residual_probe
--disable_process_reward
--disable_transition_skill_discriminator
--disable_topology_role_probe
```

Normal `s1_probe` and `s1_reward` must not pass `--parallel_selection` or `--prototype_disc_use_learned_prior`.

Arm definitions:

```powershell
"control_legacy4" {
  $extra = @(
    "--legacy_n_skills", "4"
  )
}

"s1_probe" {
  $extra = @(
    "--enable_prototype_response_skills",
    "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance",
    "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe"
  )
}

"s1_reward" {
  $extra = @(
    "--enable_prototype_response_skills",
    "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance",
    "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe",
    "--enable_prototype_disc_reward",
    "--prototype_disc_reward_coef", "0.1",
    "--prototype_disc_clip", "2.0",
    "--prototype_disc_warmup_steps", "20000"
  )
}

"r15_p1_ablation" {
  $extra = @(
    "--enable_prototype_response_skills",
    "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance",
    "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe",
    "--enable_prototype_disc_reward",
    "--prototype_disc_reward_coef", "0.1",
    "--prototype_disc_clip", "2.0",
    "--prototype_disc_warmup_steps", "20000",
    "--parallel_selection",
    "--prototype_disc_use_learned_prior"
  )
}
```

Use timestamped log roots under `logs\ha_ctse_r15_stage1_local_cuda\run_<timestamp>\<arm>`.

- [ ] **Step 7: Dry-run runner**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_r15_stage1_local_cuda.ps1 -Experiments control_legacy4,s1_probe,r15_p1_ablation -TotalTimesteps 320000 -NumEnvs 16 -Device cuda -DryRun
```

Expected:

- `control_legacy4` uses four legacy skills and does not enable prototype-response flags.
- `s1_probe` includes prototype-response flags but does not include `--parallel_selection` or `--prototype_disc_use_learned_prior`.
- `r15_p1_ablation` includes both fallback flags.
- The first real launch should use `-Experiments control_legacy4,s1_probe`; `s1_reward` launches only after the A1 probe-health checklist passes.

---

### Task 8: Smoke Validation

**Files:**
- No new source files.
- Uses touched trainer code.

- [ ] **Step 1: Run full R14/R15 unit test file**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r14_prototype_response_test.py -q
```

Expected: PASS.

- [ ] **Step 2: Run AST parse without pycache writes**

Run:

```powershell
$code = @'
import ast
from pathlib import Path
paths = [
    Path("ha_ctse_process/standalone_agent.py"),
    Path("ha_ctse_process/prototype_response_discriminator.py"),
    Path("ha_ctse_process/config.py"),
    Path("ha_ctse_process/train.py"),
    Path("ha_ctse_process/plotting.py"),
    Path("tests/r14_prototype_response_test.py"),
]
for path in paths:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("AST_OK")
'@
& "C:\Users\wu\.conda\envs\SB3\python.exe" -c $code
```

Expected: `AST_OK`.

- [ ] **Step 3: Run tiny probe smoke**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend sync `
  --num_envs 2 `
  --rollout_length 16 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7 `
  --total_timesteps 64 `
  --eval_interval 1000000 `
  --save_interval 1000000 `
  --device cuda `
  --log_dir logs\ha_ctse_r15_tiny_probe `
  --enable_prototype_response_skills `
  --enable_high_omega_conditioning `
  --enable_agent_prototype_relevance `
  --enable_per_agent_kappa `
  --enable_prototype_disc_probe `
  --disable_process_posterior_mi `
  --disable_outcome_residual_probe `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe
```

Expected:

- process completes without traceback;
- `standalone_train.log` contains `ar_selection=True`;
- metrics contain `proto_disc_null_logp_mean` and `proto_ar_parallel_kl`;
- prototype reward applied steps stay `0` because reward flag is off.

- [ ] **Step 4: Run tiny reward-on smoke**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend sync `
  --num_envs 2 `
  --rollout_length 16 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7 `
  --total_timesteps 64 `
  --eval_interval 1000000 `
  --save_interval 1000000 `
  --device cuda `
  --log_dir logs\ha_ctse_r15_tiny_reward `
  --enable_prototype_response_skills `
  --enable_high_omega_conditioning `
  --enable_agent_prototype_relevance `
  --enable_per_agent_kappa `
  --enable_prototype_disc_probe `
  --enable_prototype_disc_reward `
  --prototype_disc_warmup_steps 0 `
  --prototype_disc_reward_coef 0.1 `
  --disable_process_posterior_mi `
  --disable_outcome_residual_probe `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe
```

Expected:

- process completes without traceback;
- prototype reward applied steps become positive after first process update;
- process/topology/transition reward guards remain zero.

---

### Task 9: Memory Sync and Experiment Command Update

**Files:**
- Modify: `memory/ATTENTION_POINTER.md`
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Modify: `memory/ExpRecord.md`
- Modify: `memory/cross_validation.md` only if implementation changes the accepted/deferred status.

- [ ] **Step 1: Update implementation plan**

Add a block under the existing R15 audit:

```text
R15 Stage-1 code alignment implemented:
  - AR-first response selection is the normal path.
  - Stored skill assignment log-prob is used as prototype discriminator null.
  - Learned prior head is fallback-only under explicit R15-P1 flags.
  - New diagnostics: proto_disc_null_logp_mean, proto_assignment_logp_mean/std,
    proto_ar_parallel_kl.
  - Validation: list exact pytest/smoke commands and results.
```

- [ ] **Step 2: Update experiment record**

In `EXP-20260703-r15-stage1-steering`, change status to:

```text
R15-aligned implementation ready for rerun.
```

Record the first launch command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r15_stage1_local_cuda.ps1 `
  -Experiments control_legacy4,s1_probe `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Record the conditional reward-arm command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r15_stage1_local_cuda.ps1 `
  -Experiments s1_reward `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Record the fallback ablation command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r15_stage1_local_cuda.ps1 `
  -Experiments r15_p1_ablation `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

- [ ] **Step 3: Update attention pointer**

Set active next action to:

```text
Run R15-aligned s1_probe first.  Do not run s1_reward until s1_probe reaches
at least 160k and shows non-vacuous coordinator-residual signal without
skill/duration collapse.
```

- [ ] **Step 4: Review diff checkpoint**

Run:

```powershell
git diff -- ha_ctse_process\prototype_response_discriminator.py ha_ctse_process\standalone_agent.py ha_ctse_process\config.py ha_ctse_process\train.py ha_ctse_process\plotting.py scripts\run_r15_stage1_local_cuda.ps1 tests\r14_prototype_response_test.py memory\ATTENTION_POINTER.md memory\IMPLEMENTATION_PLAN.md memory\ExpRecord.md
```

Expected: diff only touches the listed R15 alignment surfaces.

---

## Self-Review

Spec coverage:

- AR-first selection: Tasks 3 and 5.
- Stored assignment null: Tasks 4 and 6.
- Learned prior deleted from normal path: Task 2 and Task 7.
- R15-P1 fallback ablation: Task 5 and Task 7.
- Metrics `proto_disc_null_logp_mean` and `proto_ar_parallel_kl`: Tasks 2, 6, and 7.
- Tests: Tasks 1, 3, 4, and 8.
- Memory sync: Task 9.

Placeholder scan:

- No task uses placeholder language.
- Each code-changing task includes the exact file and code shape to apply.
- No experiment is launched before the implementation and smoke validation tasks.

Type consistency:

- `SkillDurationPolicy.logits()` receives `ar_prefix` consistently from `act_with_parts()`, `act()`, and `evaluate()`.
- `Segment.skill_assignment_logp` is the stored null used by `_prototype_discriminator_batch()`.
- `PrototypeResponseDiscriminator.loss_and_metrics()` and `residual_reward()` both accept `null_logp` and use learned prior only when `use_learned_prior=True`.
- Experiment settings match `EXP-20260703-r15-stage1-steering`: 16 envs, `opt_num_prototypes=4`, A0 `control_legacy4`, A1 probe before A2 reward, A3 fallback conditional.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-03-r15-stage1-steering-objective-alignment.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.
