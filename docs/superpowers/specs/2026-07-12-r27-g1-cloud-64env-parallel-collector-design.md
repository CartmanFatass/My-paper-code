# R27-G1 Cloud 64-Environment Parallel Collector Design

Date: 2026-07-12  
Status: proposed design, user selected Approach 1  
Branch: `aggressive`  
Experiment: `EXP-20260711-r27-g1-low-actor-capacity-autopsy`

## 1. Purpose

Replace the unlaunched sequential R27-G1 snapshot collection schedule with a
Linux/cloud schedule that advances exactly 64 environments in parallel while
preserving exactly 64 reset groups and every existing scientific threshold.

This is an execution-throughput amendment, not a larger experiment:

```text
old: 1 environment x 64 sequential reset groups
new: 64 environments x 1 reset group per environment
total: 64 reset groups in both cases
```

The existing R27 scientific audit has not run, so this amendment supersedes the
pre-launch sequential execution schedule. It does not reinterpret observed
data, change a gate after seeing results, or create a second treatment arm.

## 2. Scientific Boundary

The causal edge remains:

```text
individual skill z_i -> persistent executable low-level behavior
```

The diagnostic remains reward-off and frozen. It may not modify:

- actor, critic, PPO, advantage, optimizer, or loss semantics;
- skill, duration, team-intent, or recurrent-state update rules;
- task reward, intrinsic reward, q_A, q_d, or q_D;
- environment dynamics or source checkpoint parameters;
- the static, recurrent-washout, synthetic, inactive, parity, bootstrap, or
  two-of-three thresholds accepted by the R27-G1 design.

Only environment execution and snapshot scheduling may change.

## 3. Selected Architecture

Use the existing `SubprocEnvCollector` with 64 environment worker processes
and one shared main-process CUDA agent:

```text
64 CPU environment workers
        |
        | observations / actions
        v
one main-process StandaloneProcessAgent (num_envs=64, checkpoint loaded once)
        |
        v
one CUDA policy copy
```

Do not create 64 CUDA processes or load 64 checkpoint copies. Environment
simulation remains in CPU subprocesses, as in existing 64-env training, while
all policy inference remains on the selected CUDA device. CPU policy fallback
is forbidden.

### Why this approach

- Reuses the repository's established 64-env subprocess collector.
- Loads the checkpoint and CUDA modules once.
- Keeps agent runtime indexed by `env_id`, which the live agent already
  supports.
- Avoids shard merging across independent policy processes.
- Avoids a new fully batched actor API and therefore minimizes diagnostic-path
  divergence from the inspected live actor.

## 4. Fixed Parallel Contract

Scientific collection must resolve to:

```text
num_envs = 64
n_resets = 64
collector_backend = subproc
collector_start_method = spawn
reset_id = env_id in [0, 63]
reset_seed = base_seed + env_id
episode_id = reset_id
one episode/reset group per environment
episode_max_steps = 500
skill_interval = 10
```

The scientific contract SHA must include these values and the schedule label:

```text
parallel_collection_schedule = step_major_env_id_ascending
```

Natural stochastic assignments are executed in ascending active `env_id` at
each primitive step. This is deterministic for the parallel implementation but
is not claimed to be bitwise identical to the unrun episode-major sequential
schedule. It preserves the same checkpoint, base seed, reset-seed set, natural
assignment mechanism, sample count, and gate definitions. Because no sequential
scientific result exists, the parallel schedule becomes the sole registered
R27-G1 execution schedule.

Scientific mode must reject any `num_envs != 64`, `n_resets != 64`, non-subproc
backend, non-spawn start method, or CPU device before creating output.

Reduced non-scientific fixtures may use fewer environments only when explicitly
marked ineligible for aggregate classification.

## 5. Parallel Data Flow

For each registered checkpoint:

1. Validate checkpoint path, update, metadata, total steps, and SHA256 before
   creating the run directory.
2. Create a `SubprocEnvCollector` with 64 environments in eval scale mode.
3. Reset all environments once using seeds `base_seed + env_id`.
4. Create one agent with `num_envs=64`, load the checkpoint once without
   optimizers, set eval mode, and hash checkpoint/policy parameters.
5. Initialize all 64 agent runtime slots and mark all environments active.
6. For primitive steps `0..499`:
   - process active environments in ascending `env_id`;
   - capture each environment's actor hidden state immediately before natural
     assignment;
   - call the existing `maybe_assign_skills` and detect newly opened segments;
   - append renewal rows with that environment's fixed reset identity;
   - call the existing `act_low` without gradients;
   - step only active environments in parallel;
   - permanently deactivate environments that terminate or truncate.
7. Write exactly one shard per environment:
   `reset_0000.npz` through `reset_0063.npz`. An environment with no renewal
   rows still writes a valid empty shard.
8. Read and validate all 64 shards, run the unchanged static audit, and write
   the existing manifest/JSON/Markdown artifacts.
9. Close all workers in `finally`, then verify checkpoint and policy hashes are
   unchanged.

The final checkpoint's combined snapshots feed the unchanged synthetic
active-versus-sham phase. That synthetic phase keeps its existing disposable
single-agent/single-fixture execution path; it consumes the collected snapshot
artifact and must not instantiate 64 environments or recollect trajectories.
The aggregate phase remains unchanged except for validating the amended
parallel contract SHA.

## 6. Active-Environment Stepping

Add an additive `step_selected` operation to `SubprocEnvCollector`:

```text
input: mapping env_id -> action for currently active environments
output: mapping env_id -> EnvStep
```

It sends and receives commands only for selected workers. Existing `step()` and
training behavior remain unchanged. This prevents stepping an environment after
termination and avoids resetting it into an unintended second episode.

Every returned key must be one of the requested `env_id` values, and every
requested `env_id` must produce exactly one result or a structured worker
failure. Callers consume results in ascending `env_id`; dictionary insertion
order is not part of the scientific contract.

The method must reject duplicate/out-of-range IDs and close workers safely after
partial failures. A worker exception fails the collection phase; partial shards
may remain for diagnosis but cannot enter aggregate classification.

## 7. Artifact And Identity Contract

Existing artifact names remain authoritative. New manifest evidence adds:

```text
num_envs
collector_backend
collector_start_method
parallel_collection_schedule
env_id_to_reset_id
env_id_to_reset_seed
active_steps_by_env
termination_reason_by_env
```

Aggregate validation must require:

- exactly 64 named shards;
- exactly reset IDs `0..63` and seeds `1..64` for base seed 1;
- exactly one reset group per environment;
- no row whose `env_id`, `reset_id`, or `reset_seed` violates the registered
  mapping;
- the amended scientific-contract SHA in static manifests and synthetic output;
- unchanged source checkpoint and policy hashes.

Any mismatch produces structured `INVALID`; it cannot be downgraded to a
warning or accepted as partial evidence.

## 8. Linux Cloud Runner

Add:

```text
scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh
```

Fixed scientific defaults:

```text
PYTHON_BIN=python
DEVICE=cuda
NUM_ENVS=64
N_RESETS=64
COLLECTOR_BACKEND=subproc
COLLECTOR_START_METHOD=spawn
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

The runner preserves the existing exact `3 collect-static + 1 synthetic + 1
aggregate` phase order, status files, commands, transcripts, failure handling,
and no-write dry-run behavior.

Checkpoint files are not Git-tracked. The runner accepts
`CHECKPOINT_DIST_ROOT`, defaulting to `<repo>/dist`, and constructs paths whose
suffix remains the registered `dist/logs_cloud_r25_qa_verification_1m/...`
identity. It must fail before output creation when a file is missing or its
SHA256 differs. Relocating the parent directory is allowed; changing the
registered arm/update/file suffix or hash is not.

## 9. Testing And Verification

Required tests before launch:

1. `step_selected` returns only selected environment results and leaves the
   existing `step()` contract unchanged.
2. A deterministic fake 4-env fixture creates one shard per env with exact
   env/reset/seed mapping and stops terminated envs without a second episode.
3. Repeated parallel fixture runs use the same step-major env order and produce
   identical artifacts.
4. Missing, duplicate, out-of-range, or cross-mapped reset evidence produces
   `INVALID`.
5. Scientific CLI rejects non-64 cardinality/backend/start method/CPU before
   output creation.
6. Non-scientific reduced fixtures are marked aggregate-ineligible.
7. Bash runner `--dry-run` prints exactly 3+1+1 phases, CUDA, 64 envs, 64 resets,
   and creates no output root.
8. `bash -n`, Python compile/AST checks, focused R27/R26 regression tests, and
   forbidden-core-file diff checks pass.
9. Final standard and Frontier implementation reviews pass before cloud launch.

No scientific run may launch from implementation tests or dry-run output.

## 10. Expected Cost And Decision Rule

The previous sequential estimate was 2.5--3.5 hours. The parallel cloud path is
expected to reduce collection wall time, but main-process per-env policy calls
and the synthetic phase remain. Use a conservative initial estimate of 1--2
hours on CUDA until measured. Never silently fall back to CPU.

The experiment's interpretation and decision tree are unchanged. Parallel
execution does not authorize reward, actor redesign, hidden reset, post-GRU
FiLM, action-head residuals, q_A, q_d, or q_D. Those actions remain blocked
until the completed R27 classification is reviewed.

## 11. Rejected Alternatives

- **Eight independent 8-env shards:** rejected because multiple checkpoint
  loads and shard/manifest merging enlarge the artifact-identity surface.
- **Sixty-four CUDA policy processes:** rejected because CUDA context and model
  replication create avoidable memory/OOM risk.
- **New fully batched actor API:** rejected because it changes the inspected
  actor invocation path and adds a second causal variable to a frozen audit.
- **64 env x 64 resets:** rejected by user selection; it would increase sample
  size to 4096 reset groups and require a new scientific design.
