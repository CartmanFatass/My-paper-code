# JaxMARL core performance evidence

## Scope and identity

This packet is a read-only inspection of `C:/Projects/ref-lib/JaxMARL` at exact commit
`b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9`. Local Git reports that `HEAD` equals this SHA and the
remote is `https://github.com/FLAIROx/JaxMARL.git`. The official GitHub page redirects that project
to [`bold-lab-ai/JaxMARL`](https://github.com/bold-lab-ai/JaxMARL), describes it as “Multi-Agent
Reinforcement Learning with JAX”, lists the `baselines` and `jaxmarl` trees, and describes the
agent-keyed parallel API. The fixed commit page identifies the same SHA as the merge adding a sixth
Hanabi colour: [`b0c4d77`](https://github.com/bold-lab-ai/JaxMARL/commit/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9).
Every source link below uses that full SHA, so links do not drift with `main`.

The source declares Apache License 2.0 in [`LICENSE`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/LICENSE#L1-L5); `pyproject.toml` repeats the license and package requirements. This packet quotes only short code fragments and does not copy source into HMASD. The upstream tree had no `AGENTS.md` or `CLAUDE.md`; the navigation files are local overlays and are backed up under `agents-overlays/`.

Tags used below: **Observation** is directly visible in the pinned source; **Inference** is a
performance or engineering consequence of that source; **Unmeasured** was not run or timed here.

## Short source excerpts

The following short excerpts anchor the main mechanisms in literal source text (the surrounding
analysis remains an observation/inference split):

- Auto-reset and tree selection: `key, key_reset = jax.random.split(key)` followed by
  `jax.lax.select(dones["__all__"], x, y)` ([`multi_agent_env.py` lines 100–115](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/multi_agent_env.py#L100-L115)).
- Batch axis: `keys = jax.random.split(key, self.batch_size)` and
  `jax.vmap(self.wrapped_reset, in_axes=0)(keys)` ([`baselines.py` lines 397–400](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L397-L400)).
- SMAX inner time: `jax.lax.scan(... length=self.world_steps_per_env_step)` ([`smax_env.py`
  lines 380–385](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L380-L385)).
- Actor flattening: `config["NUM_ACTORS"] = env.num_agents * config["NUM_ENVS"]`
  ([`ippo_rnn_smax.py` lines 119–127](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L119-L127)).
- Timing boundary: `.lower(rng).compile()` occurs before `block_until_ready` and the timer
  ([`speed.py` lines 196–203](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/speed.py#L196-L203)).

## Core call chain

The common API is `reset(key) -> (obs, state)` and `step(key, state, actions) ->
(obs, state, reward, done, info)`. [`MultiAgentEnv`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/multi_agent_env.py#L43-L49) documents the contract and marks `reset`, `step`, and `get_avail_actions` as JIT methods with the environment object static. [`step`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/multi_agent_env.py#L79-L116) splits a reset key, calls `step_env`, computes a reset candidate, then uses `jax.lax.select(dones["__all__"], ...)` across the state and observation trees. **Inference:** terminal transitions are still part of the compiled call and auto-reset can change the amount of work and returned state; callers should not separately reset unless they intentionally bypass this method.

For the principal RNN policy path, the chain is:

`ippo_rnn_smax.main` -> `make_train` -> `train_jit` -> outer update `lax.scan` -> rollout
`lax.scan` -> `vmap(env.step)` -> SMAX `step_env` -> inner world-step `lax.scan` -> `vmap` over
units; after rollout, reverse GAE `scan`, update-epoch `scan`, minibatch `scan`, and a host logging
  callback. The exact links are [`main`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L472-L490), [`make_train` and init](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L119-L180), [`rollout`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L184-L237), [`GAE/update`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L254-L405), and [`metrics/callback`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L409-L466).

The simpler VDN path is [`make_train`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L57-L108). Its chain initializes `CTRolloutManager`, Q network, optimizer, and replay buffer; scans `NUM_STEPS` for collection, flattens time/environment before `buffer.add`, then scans replay `NUM_EPOCHS` and conditionally tests. The outer call is [`single_run`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L459-L508), which creates `jax.jit(jax.vmap(make_train(...)))` and blocks its result before parameter saving.

## Batching and dimensions

[`CTRolloutManager`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L308-L395) is the key batching adapter. It records `batch_size`, computes maximum flattened observation/action dimensions, pads observations, and appends a one-hot agent ID. For SMAX it uses the environment world state as global state and the first training agent's reward as global reward. The actual parallel calls are [`batch_reset`/`batch_step`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L397-L405): split one key into `batch_size` keys, then `vmap` over keys, states, and actions. The wrapper's `wrapped_step` zeroes observations of done agents, adds `obs["__all__"]`, and adds `rewards["__all__"]` ([lines 421–441](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L421-L441)).

In IPPO, [`batchify`/`unbatchify`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L109-L116) stack dictionaries in `agent_list` order and reshape to `(num_actors, ...)`, where `NUM_ACTORS = num_agents * NUM_ENVS` ([lines 119–128](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L119-L128)). **Inference:** the learner's actor axis is a flattened agent/environment product; it is not an independent environment-only axis. Static agent order and fixed shapes are part of the compiled program.

The selected transforms are `vmap` for independent environments, agents, action keys, and network
calls; `lax.scan` for rollout time, GAE, update epochs, and replay epochs; and outer `vmap` across
seed keys. The recurrent policy uses Flax [`nn.scan`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L25-L50) with parameters broadcast and sequence axis 0. A source-wide search found no `pmap`, `pjit`, or explicit sharding in these core baseline paths; IPPO SMAX pins the JIT to `jax.devices()[0]` ([lines 487–490](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L487-L490)). **Inference:** parallelism is vectorization and process-level GPU slotting, not multi-device SPMD.

## Pure environment state and cost drivers

The MPE base state is a Flax dataclass with `p_pos[num_entities,2]`, `p_vel[num_entities,2]`,
`c[num_agents,dim_c]`, and scalar base fields ([`simple.py` lines 40–55](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/mpe/simple.py#L40-L55)). Its JIT step splits world and communication keys and then calls a nested pairwise force function ([`lines 253–293`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/mpe/simple.py#L253-L293)). `_apply_environment_force` has outer and inner `vmap` over `entity_range` and builds pair forces ([`lines 423–450`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/mpe/simple.py#L423-L450)). **Inference:** collision/interactions have quadratic entity-pair intermediates; this is a shape-based cost risk, not a measured bottleneck. `SimpleSpreadMPE.get_obs` vmaps common statistics over agents and constructs relative landmark/other-agent/communication features ([`simple_spread.py` lines 66–105](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/mpe/simple_spread.py#L66-L105)).

SMAX's state stores unit arrays indexed allies then enemies: positions, alive flags, teams, health,
types, cooldowns, and previous actions ([`smax_env.py` lines 31–48](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L31-L48)). Reset creates fixed arrays and explicit `uint8`, `bool`, and `int32` fields ([`lines 282–338`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L282-L338)). `step_env_no_decode` scans `world_steps_per_env_step`, default 8, before reward/observation output ([`lines 340–411`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L340-L411)). Each world step vmaps unit actions and splits one key per unit ([`lines 734–776`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L734-L776)). `_push_units_away` materializes an `N x N` distance/overlap matrix ([`lines 507–531`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L507-L531)). **Inference:** SMAX learner workload scales with outer `NUM_ENVS`, agent count, nested world steps, and unit-pair/observation shapes.

## RNG, dtype, and action semantics

JAX keys are explicitly threaded. IPPO splits for reset, action sampling, and per-environment step keys ([`ippo_rnn_smax.py` lines 177–217](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L177-L217)); VDN splits separate exploration/step keys and per-agent exploration keys ([`vdn_ff.py` lines 194–224](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L194-L224)). The top level creates one key then `jax.random.split` maps `NUM_SEEDS` ([`vdn_ff.py` lines 482–486](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L482-L486)). **Observation:** the source provides distinct split keys; **Unmeasured:** statistical independence or cross-device reproducibility was not tested.

SMAX action masks are `uint8` arrays produced by vmapped per-agent legality logic ([`smax_env.py` lines 965–1010](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/smax_env.py#L965-L1010)); the IPPO policy subtracts `1e10` from unavailable logits ([`ippo_rnn_smax.py` lines 70–82](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L70-L82)). The local `Discrete` space defaults to `jnp.int32` ([`spaces.py` lines 29–49](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/spaces.py#L29-L49)); do not infer action dtype from Python integers.

## Compile, steady state, transfers, and timing

The standalone SMAX speed harness constructs a batched environment, uses `vmap` reset/step and a
temporal scan ([`speed.py` lines 94–176](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/speed.py#L94-L176)). It explicitly lowers and compiles before starting its timer, then wraps the timed invocation in `jax.block_until_ready` ([`lines 181–206`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/smax/speed.py#L181-L206)). Its printed `num_steps = NUM_ENVS * NUM_STEPS`; it does not multiply by agents or SMAX world substeps. This is a valid source-level timing design, but **Unmeasured:** it was not executed here.

Selected paths contain no explicit `jax.device_put`, `device_get`, or host copy in the rollout
kernel. JAX arrays are created in `jnp` operations and placed according to the selected JAX device;
IPPO SMAX selects `jax.devices()[0]`. **Inference:** the source does not establish transfer-free
end-to-end execution for a future host/UAV workload; data movement and backend placement require a
real measurement. The generic VDN entry blocks before saving, whereas IPPO SMAX's `main` calls
`jax.vmap(train_jit)(rngs)` without an explicit `block_until_ready` ([`lines 487–490`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L487-L490)). Do not use that entry point as a wall-clock benchmark.

## Evaluation and logging

VDN's test path creates a separate `CTRolloutManager` with `TEST_NUM_ENVS`, runs a greedy policy in
a `lax.scan`, and computes `nanmean` only over `infos["returned_episode"]` ([`vdn_ff.py` lines 373–416](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L373-L416)). The test is conditionally called by update interval ([`lines 338–348`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L338-L348)). `LogWrapper` accumulates per-agent episode return and length in the JAX state and writes returned metrics to `info` ([`baselines.py lines 67–115`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L67-L115)). `MPELogWrapper` multiplies the logged reward by `num_agents` ([`lines 197–231`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/wrappers/baselines.py#L197-L231)).

WandB reporting is inside traced loops: VDN uses `jax.debug.callback` ([`vdn_ff.py lines 350–363`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/QLearning/vdn_ff.py#L350-L363)); IPPO SMAX uses `jax.experimental.io_callback` ([`ippo_rnn_smax.py lines 431–450`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/IPPO/ippo_rnn_smax.py#L431-L450)). **Inference:** callbacks are host-side synchronization/serialization candidates and should be included or disabled consistently in any timing experiment. No callback overhead was measured.

## Combination enumeration and host-side work

- STORM creates `list(itertools.combinations(AGENT_SPAWNS, 8))` and then a JAX array at module import ([`storm_env.py lines 182–186`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/storm/storm_env.py#L182-L186)). **Observation:** this startup memory/time cost is outside a compiled step; **Unmeasured:** its magnitude.
- Overcooked V2 enumerates unique three-ingredient recipes with Python `itertools.combinations` when recipes are omitted ([`layouts.py lines 213–240`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/overcooked_v2/layouts.py#L213-L240)). This is configuration construction, not an evidence of per-step cost.
- Hanabi builds fixed action encodings in Python at construction ([`hanabi.py lines 74–111`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/hanabi/hanabi.py#L74-L111)); its human-readable belief formatter uses `itertools.product` ([`lines 777–787`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/hanabi/hanabi.py#L777-L787)). Legal moves themselves are vmapped and fixed width ([`lines 266–336`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/jaxmarl/environments/hanabi/hanabi.py#L266-L336)).

These are concrete host or shape-risk candidates, not measured bottleneck findings. The source has
no basis for promising GPU or VNFC acceleration.

## Process-level launcher and limits

The baseline launcher deliberately reads the package version without importing JAX because its
docstring records import-time CUDA preallocation risk ([`run_minimal_baseline_set.py lines 44–64`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/run_minimal_baseline_set.py#L44-L64)). It assigns a GPU slot per seed, sets `CUDA_VISIBLE_DEVICES` and `XLA_PYTHON_CLIENT_PREALLOCATE=false`, runs seed subprocesses concurrently, logs each stdout/stderr to a file, and times the combo with `time.monotonic` ([`lines 241–301`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/run_minimal_baseline_set.py#L241-L301)). Combos themselves are iterated sequentially ([`lines 348–368`](https://github.com/bold-lab-ai/JaxMARL/blob/b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9/baselines/run_minimal_baseline_set.py#L348-L368)). **Inference:** process-level seed concurrency is an orchestration choice with memory interference risk; it is not a JAX multi-device speedup measurement.

## Limits for HMASD use

The evidence is source inspection only. No dependencies were installed; no environment, training,
benchmark, timing, GPU, transfer, callback, or scaling run was performed. Do not turn the README's
“GPU-enabled efficiency” wording into a claim for HMASD. For future toy workloads exceeding 45
minutes or UAV workloads exceeding 12 hours, use those thresholds only to trigger engineering
validation of launch, memory, transfer, logging, and resume behavior; they are not scientific speed
acceptance criteria. Preserve dtype, RNG split structure, reset semantics, agent order, action
masks, and metric definitions when creating a comparable implementation.

## Static verification record

- `git rev-parse HEAD`: `b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9`.
- `git remote -v`: `https://github.com/FLAIROx/JaxMARL.git` for fetch and push.
- `git ls-tree -r --name-only <SHA> | rg '(^|/)(AGENTS|CLAUDE)\\.md$'`: no upstream instruction file.
- `git status --short --untracked-files=all`: only the local `AGENTS.md` overlays listed in
  [`AGENTS_INDEX.json`](AGENTS_INDEX.json); no source file is modified.
- All fixed source paths cited above were resolved with `git show <SHA>:<path>` while collecting
  line-numbered excerpts. This packet does not claim runtime validity beyond those static checks.
