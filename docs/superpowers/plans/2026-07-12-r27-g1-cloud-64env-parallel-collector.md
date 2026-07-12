# R27-G1 Cloud 64-Environment Parallel Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the frozen R27-G1 capacity autopsy on Linux with exactly 64 environment workers collecting exactly 64 reset groups, one shared CUDA agent, and the unchanged 3+1+1 scientific gate.

**Architecture:** Extend `SubprocEnvCollector` with selected-worker stepping, then add an R27-only step-major parallel collection path that maps `env_id == reset_id` for 64 single-episode workers. Keep the frozen actor, static evaluator, synthetic control, aggregate thresholds, and reward paths unchanged; add a Bash runner that validates the three registered checkpoint identities before creating output.

**Tech Stack:** Python 3.10+, PyTorch, NumPy, multiprocessing `spawn`, pytest, Bash.

## Global Constraints

- Scientific collection is exactly `num_envs=64`, `n_resets=64`, `collector_backend=subproc`, and `collector_start_method=spawn`.
- Reset identity is exactly `reset_id=env_id`, `reset_seed=base_seed+env_id`, and `episode_id=reset_id` for `env_id` 0 through 63.
- Scheduling is `step_major_env_id_ascending`; it supersedes the unlaunched sequential schedule and is not claimed bitwise-identical to it.
- Use one main-process CUDA `StandaloneProcessAgent` with 64 runtime slots; never create 64 CUDA processes and never fall back to CPU.
- Keep task reward, intrinsic reward, q_A, q_d, q_D, actor/critic/PPO/loss semantics, environment dynamics, thresholds, and source checkpoints unchanged.
- Keep the synthetic active-vs-sham phase on its existing disposable single-agent path.
- Scientific output remains exactly three collect-static phases, one synthetic phase, and one aggregate phase.
- Reduced fixtures must be explicitly non-scientific and aggregate-ineligible.
- New runtime artifacts must live under the caller-provided run root; dry-run creates no output.

---

## File Structure

- Modify `ha_ctse_process/collectors.py`: additive selected-worker stepping API only.
- Modify `scripts/audit_r27_low_actor_capacity.py`: parallel R27 collection, scientific contract fields, manifest evidence, and aggregate validation.
- Create `scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh`: Linux/CUDA 64-env 3+1+1 runner.
- Modify `tests/r27_low_actor_capacity_cli_test.py`: fake parallel collector, contract, manifest, and aggregate-invalid tests.
- Create `tests/r27_parallel_collector_test.py`: isolated `step_selected` behavior tests.
- Create `tests/r27_cloud_runner_test.py`: Bash dry-run/no-write contract test.
- Update `memory/ExpRecord.md` only at the experiment-preparation boundary, recording the cloud command and expected artifacts without claiming launch.

### Task 1: Add Selected-Worker Subprocess Stepping

**Files:**
- Modify: `ha_ctse_process/collectors.py:112-185`
- Create: `tests/r27_parallel_collector_test.py`

**Interfaces:**
- Consumes: ordered `Sequence[tuple[int, Any]]` of `(env_id, action)` pairs.
- Produces: `SubprocEnvCollector.step_selected(indexed_actions) -> dict[int, EnvStep]`.
- Preserves: existing `SubprocEnvCollector.step(actions) -> list[EnvStep]` unchanged.

- [ ] **Step 1: Write failing selected-step tests**

Create fake remotes and instantiate the collector with `__new__` so no process is spawned. Cover selected send/receive, omitted-worker inactivity, duplicate IDs, negative/out-of-range IDs, and existing `step()` behavior:

```python
def test_step_selected_only_touches_requested_workers():
    collector = make_fake_collector(4)
    result = collector.step_selected([(3, "a3"), (1, "a1")])
    assert list(result) == [3, 1]
    assert collector.remotes[0].sent == []
    assert collector.remotes[2].sent == []
    assert collector.remotes[3].sent == [("step", "a3")]
    assert collector.remotes[1].sent == [("step", "a1")]


@pytest.mark.parametrize(
    "indexed_actions, message",
    [
        ([(1, "a"), (1, "b")], "duplicate env_id"),
        ([(-1, "a")], "out of range"),
        ([(4, "a")], "out of range"),
    ],
)
def test_step_selected_rejects_invalid_ids(indexed_actions, message):
    collector = make_fake_collector(4)
    with pytest.raises(ValueError, match=message):
        collector.step_selected(indexed_actions)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_parallel_collector_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-step-selected
```

Expected: FAIL because `step_selected` does not exist.

- [ ] **Step 3: Implement the minimal additive API**

Add to `SubprocEnvCollector` without changing `step()`:

```python
def step_selected(self, indexed_actions):
    pairs = [(int(env_id), action) for env_id, action in indexed_actions]
    env_ids = [env_id for env_id, _action in pairs]
    if len(env_ids) != len(set(env_ids)):
        raise ValueError("step_selected received duplicate env_id")
    if any(env_id < 0 or env_id >= self.num_envs for env_id in env_ids):
        raise ValueError("step_selected env_id out of range")
    for env_id, action in pairs:
        self.remotes[env_id].send(("step", action))
    return {
        env_id: self._recv(self.remotes[env_id])
        for env_id, _action in pairs
    }
```

The caller owns ascending scheduling. The method preserves caller order in the returned dictionary but scientific consumers must sort keys explicitly.

- [ ] **Step 4: Run selected-step and collector regressions**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_parallel_collector_test.py tests/r26_g1_collector_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-collector
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```powershell
git add -- ha_ctse_process/collectors.py tests/r27_parallel_collector_test.py
git commit -m "feat: add selected subprocess env stepping"
```

### Task 2: Implement Frozen Step-Major Parallel Snapshot Collection

**Files:**
- Modify: `scripts/audit_r27_low_actor_capacity.py:603-900`
- Modify: `tests/r27_low_actor_capacity_cli_test.py`

**Interfaces:**
- Consumes: collector with `reset_all(base_seed)` and `step_selected(indexed_actions)`; one 64-slot frozen agent.
- Produces: `collect_capacity_parallel(...) -> tuple[dict[int, CapacitySnapshotBatch], SnapshotCollectorStats, dict[str, object]]`.
- Metadata keys: `env_id_to_reset_id`, `env_id_to_reset_seed`, `active_steps_by_env`, `termination_reason_by_env`.

- [ ] **Step 1: Write a deterministic four-env failing fixture test**

Add `FakeParallelCollector` and a multi-slot fake agent. Make env 1 terminate at step 1, env 3 truncate at step 2, and the rest reach the step limit. Assert:

```python
batches, stats, evidence = collector.collect_capacity_parallel(
    fake_collector,
    fake_agent,
    base_seed=1,
    n_resets=4,
    skill_interval=10,
    episode_max_steps=3,
    checkpoint_id="fixture",
    checkpoint_update=25,
)
assert sorted(batches) == [0, 1, 2, 3]
assert evidence["env_id_to_reset_id"] == {"0": 0, "1": 1, "2": 2, "3": 3}
assert evidence["env_id_to_reset_seed"] == {"0": 1, "1": 2, "2": 3, "3": 4}
assert evidence["active_steps_by_env"] == {"0": 3, "1": 1, "2": 3, "3": 2}
assert evidence["termination_reason_by_env"] == {
    "0": "step_limit",
    "1": "terminated",
    "2": "step_limit",
    "3": "truncated",
}
assert fake_collector.step_orders == [[0, 1, 2, 3], [0, 2, 3], [0, 2]]
```

Also assert every snapshot row satisfies `env_id == reset_id`, `reset_seed == 1 + env_id`, and no ended environment is stepped again.

- [ ] **Step 2: Run the fixture and verify failure**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py -k "parallel" -q --basetemp tests/.pytest_tmp/r27-cloud-parallel-red
```

Expected: FAIL because `collect_capacity_parallel` does not exist.

- [ ] **Step 3: Implement parallel collection without changing the actor path**

Implement one `preserve_agent_runtime(agent)` scope around all environments. Reset each agent slot once, then use ascending active IDs each step:

```python
active = set(range(int(n_resets)))
for step in range(int(episode_max_steps)):
    indexed_actions = []
    for env_id in sorted(active):
        # capture pre-assignment hidden, call maybe_assign_skills, append rows
        # with reset_id=episode_id=env_id and reset_seed=base_seed+env_id
        with torch.no_grad():
            actions, _, _ = agent.act_low(
                observations[env_id],
                env_id=env_id,
                deterministic=False,
                state=states[env_id],
            )
        indexed_actions.append((env_id, actions))
    results = collector.step_selected(indexed_actions)
    for env_id in sorted(results):
        env_step = results[env_id]
        # update observation/state and deactivate on terminated/truncated
```

Use `_rows_to_batch` for every env, including valid empty shards. Count one reset per env and keep task fields out of `CapacitySnapshotBatch`.

- [ ] **Step 4: Run fixture twice and verify deterministic artifacts**

Run the fixture twice with identical fake inputs, serialize all four shards, and compare `_snapshot_shards_sha256` values. Expected: identical hashes and PASS.

- [ ] **Step 5: Run R27 CLI regressions**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_low_actor_capacity_cli_test.py tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-parallel-green
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```powershell
git add -- scripts/audit_r27_low_actor_capacity.py tests/r27_low_actor_capacity_cli_test.py
git commit -m "feat: collect R27 snapshots across parallel envs"
```

### Task 3: Bind the 64-Environment Scientific and Artifact Contract

**Files:**
- Modify: `scripts/audit_r27_low_actor_capacity.py:80-220, 396-490, 760-900, 1516-1740, 1850-1915`
- Modify: `tests/r27_low_actor_capacity_cli_test.py`

**Interfaces:**
- New collect-static CLI options: `--num-envs`, `--collector-backend`, `--collector-start-method`.
- New configuration helper: `_configure_parallel_agent(args) -> tuple[config, metadata, collector, agent, loaded_update]`.
- Scientific contract includes `num_envs=64`, `collector_backend="subproc"`, `collector_start_method="spawn"`, and `parallel_collection_schedule="step_major_env_id_ascending"`.

- [ ] **Step 1: Write failing pre-output validation tests**

Parameterize invalid scientific values and assert validation fails before `_configure_parallel_agent` or output creation:

```python
@pytest.mark.parametrize(
    "flag,value,message",
    [
        ("--num-envs", "32", "num_envs must equal 64"),
        ("--collector-backend", "sync", "collector_backend must equal"),
        ("--collector-start-method", "fork", "collector_start_method must equal"),
    ],
)
def test_scientific_parallel_contract_rejects_override(flag, value, message):
    args = scientific_collect_args(flag, value)
    with pytest.raises(ValueError, match=message):
        collector.validate_scientific_args(args)
```

- [ ] **Step 2: Add contract fields and CLI defaults**

Add the four fixed fields to `SCIENTIFIC_CONTRACT`, parser defaults, and `validate_scientific_args`. Because the contract SHA is derived from the full contract, this intentionally creates the amended sole execution identity.

- [ ] **Step 3: Configure one CUDA agent from collector spec**

Build the subprocess collector first, call `reset_all` only inside collection, and create a read-only spec adapter:

```python
env_spec = SimpleNamespace(**collector.spec)
agent = train_mod.create_agent(
    config,
    args,
    env_spec,
    num_envs=int(args.num_envs),
    state_dim=int(collector.spec["state_dim"]),
)
```

Load the checkpoint once with `load_optimizers=False`, set eval mode, and return the collector as the owned closeable. Do not route synthetic through this helper.

- [ ] **Step 4: Switch collect-static to the parallel path and write all shards**

Call `collect_capacity_parallel`, then write `reset_0000.npz` through `reset_0063.npz`. Put the fixed collector fields and returned mappings/counters into `collector_manifest.json`.

- [ ] **Step 5: Add strict shard and mapping validation**

Add a helper that validates exact shard names and each shard's row identity. It must return structured errors for missing/duplicate/cross-mapped evidence and aggregate must classify them as `INVALID`. Empty shards remain valid if their filename and manifest identity are correct.

- [ ] **Step 6: Extend synthetic-source and aggregate identity checks**

Require the amended contract SHA and all fixed collector fields in each manifest and the synthetic source binding. Add tests that mutate each field independently and assert `classification == "INVALID"` with the matching reason.

- [ ] **Step 7: Run all R27 tests**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_parallel_collector_test.py tests/r27_low_actor_capacity_cli_test.py tests/r27_low_actor_capacity_audit_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-contract
```

Expected: PASS.

- [ ] **Step 8: Commit Task 3**

```powershell
git add -- scripts/audit_r27_low_actor_capacity.py tests/r27_low_actor_capacity_cli_test.py
git commit -m "fix: bind R27 parallel collection identity"
```

### Task 4: Add the Self-Contained Linux Cloud Runner

**Files:**
- Create: `scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh`
- Create: `tests/r27_cloud_runner_test.py`

**Interfaces:**
- Inputs: `PYTHON_BIN`, `DEVICE`, `NUM_ENVS`, `N_RESETS`, `CHECKPOINT_DIST_ROOT`, `RUN_ROOT`.
- Modes: normal execution, `--dry-run`, `--continue-on-error`.
- Outputs: run-local command files, phase logs, status files, three static reports/manifests, synthetic report, aggregate report.

- [ ] **Step 1: Write the failing Bash runner contract test**

Run the script with `bash --dry-run`, capture stdout, and assert:

```python
assert output.count("PHASE collect-static") == 3
assert output.count("PHASE synthetic") == 1
assert output.count("PHASE aggregate") == 1
assert "--device cuda" in output
assert "--num-envs 64" in output
assert "--n-resets 64" in output
assert "--collector-backend subproc" in output
assert "--collector-start-method spawn" in output
assert not run_root.exists()
```

- [ ] **Step 2: Run the test and verify failure**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_cloud_runner_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-runner-red
```

Expected: FAIL because the Bash runner does not exist.

- [ ] **Step 3: Implement the runner**

Mirror the PowerShell runner's 3+1+1 ordering and status semantics. Resolve checkpoint paths from `CHECKPOINT_DIST_ROOT`, verify all three files and exact SHA256 before `mkdir -p "$RUN_ROOT"`, and include the exact parallel flags in every collect-static command. `--dry-run` prints all commands without checking checkpoint presence or creating output.

- [ ] **Step 4: Verify parser and no-write behavior**

```powershell
bash -n scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_cloud_runner_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-runner-green
```

Expected: both PASS.

- [ ] **Step 5: Commit Task 4**

```powershell
git add -- scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh tests/r27_cloud_runner_test.py
git commit -m "feat: add R27 cloud 64-env runner"
```

### Task 5: Verify, Review, and Register the Cloud Handoff

**Files:**
- Modify: `memory/ExpRecord.md`
- Modify: `.superpowers/sdd/progress.md` if executing through Superpowers progress tracking.
- Create runtime reports under: `logs/r27_g1_cloud64_build_20260712/`

**Interfaces:**
- Produces: verified launch command and artifact checklist; does not launch the scientific run.

- [ ] **Step 1: Run compile and focused regression checks**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile ha_ctse_process/collectors.py scripts/audit_r27_low_actor_capacity.py tests/r27_parallel_collector_test.py tests/r27_low_actor_capacity_cli_test.py tests/r27_cloud_runner_test.py
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests/r27_parallel_collector_test.py tests/r27_low_actor_capacity_cli_test.py tests/r27_low_actor_capacity_audit_test.py tests/r26_g1_collector_test.py -q --basetemp tests/.pytest_tmp/r27-cloud-final
bash -n scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh
```

Expected: all commands PASS.

- [ ] **Step 2: Run the no-write scientific dry-run**

```powershell
bash scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh --dry-run
```

Expected: exactly 3 collect-static, 1 synthetic, and 1 aggregate command; CUDA, 64 envs, 64 resets; no run directory created.

- [ ] **Step 3: Check forbidden core-file and artifact hygiene**

Verify the implementation diff does not touch actor, critic, PPO, reward, environment, or checkpoint files, and no root-level runtime artifacts or pytest scratch directories remain.

- [ ] **Step 4: Obtain standard and Frontier implementation reviews**

Review package must cover collector concurrency/error handling, frozen scientific identity, mapping validation, synthetic-path isolation, runner checkpoint SHA enforcement, and no-write dry-run behavior. Both reviews must PASS before launch.

- [ ] **Step 5: Register the launch-ready experiment facts**

Update the R27 row in `memory/ExpRecord.md` with:

```text
status=ready_not_launched
device=cuda
num_envs=64
n_resets=64
schedule=step_major_env_id_ascending
expected_wall_clock=1-2h initial estimate
runner=scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh
required_checkpoint_root=CHECKPOINT_DIST_ROOT
expected_final_artifact=<RUN_ROOT>/r27_capacity_autopsy.json
```

- [ ] **Step 6: Commit verification bookkeeping**

```powershell
git add -- memory/ExpRecord.md .superpowers/sdd/progress.md
git commit -m "docs: register R27 cloud capacity audit"
```

Do not include unrelated pre-existing memory, agent-config, or workflow files.

## Cloud Launch Command After Verification

The implementation prepares, but does not automatically execute, this command:

```bash
CHECKPOINT_DIST_ROOT="$HOME/HMASD/dist" \
RUN_ROOT="logs/r27_g1_capacity_autopsy_cloud64_$(date +%Y%m%d_%H%M%S)" \
bash scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh
```

Expected cloud wall time: initially 1--2 hours on CUDA. The runner must fail rather than use CPU.
