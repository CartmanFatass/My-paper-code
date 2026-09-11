# Mava core evidence at fixed source

## Scope and provenance

This is a read-only static scan of `C:\Projects\ref-lib\Mava` at
`83f7f0d19d6fdbe07264bb226a64baf8a0b17514` (the checkout's `HEAD`, branch `develop`). The package
declares `__version__ = "0.2.0"` in
[`mava/__init__.py:1-14`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/__init__.py#L1-L14).
The official primary identity check is the public
[instadeepai/Mava fixed tree](https://github.com/instadeepai/Mava/tree/83f7f0d19d6fdbe07264bb226a64baf8a0b17514)
and its [fixed commit page](https://github.com/instadeepai/Mava/commit/83f7f0d19d6fdbe07264bb226a64baf8a0b17514),
which identifies the public `instadeepai/Mava` repository and commit message
“refactor: standardize prev and final terminology” (18 files changed). The local source checkout
was clean before this report's additive overlays. No package installation, training, benchmark, or
runtime probe was performed.

The fixed commit matters: its refactor standardizes `prev` for the preceding environment step and
`final` for rollout endpoint values. All observations below come from this tree; older Mava
layouts must not be substituted.

## Observed source facts

### Entry points and Anakin execution

The README describes Anakin as the JAX-environment path and Sebulba as the non-JAX path, and says
Anakin can JIT the full training loop ([`README.md:31-39`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/README.md#L31-L39);
[`README.md:113-113`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/README.md#L113-L113)).
The concrete FF-IPPO Anakin chain is:

```text
Hydra entry -> run_experiment -> environments.make -> learner_setup
  -> get_learner_fn -> pmap(device) -> vmap(batch) -> scan(time/update)
  -> evaluator -> logger/checkpointer
```

In the source, `_env_step` splits a key, applies actor/critic, samples an action, and vmaps
`env.step` over the environment axis ([`ppo/anakin/ff_ippo.py:82-110`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L82-L110)).
The rollout is `jax.lax.scan` over `config.system.rollout_length` (T). PPO then scans epochs and
minibatches; each minibatch merges the first two leading axes, shuffles `T * num_envs`, and
reshapes into `num_minibatches` ([`ppo/anakin/ff_ippo.py:237-264`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L237-L264)).
The learner wraps one update step in `jax.vmap(..., axis_name="batch")`, scans
`num_updates_per_eval`, and is then wrapped in `jax.pmap(..., axis_name="device")`
([`ppo/anakin/ff_ippo.py:270-296`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L270-L296);
[`ppo/anakin/ff_ippo.py:354-356`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L354-L356)).
Gradients and loss information are pmean-reduced first over `batch`, then over `device`
([`ppo/anakin/ff_ippo.py:193-209`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L193-L209)).

At initialization, reset keys are generated for
`n_devices * update_batch_size * num_envs`, vmapped, and reshaped to
`(device, update_batch, num_envs, ...)` ([`ppo/anakin/ff_ippo.py:358-370`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L358-L370)).
The default Anakin config documents `num_envs: 16` per device
([`configs/arch/anakin.yaml:1-15`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/configs/arch/anakin.yaml#L1-L15));
the FF-IPPO default has `update_batch_size: 2`, `rollout_length: 128`, four PPO epochs and two
minibatches ([`configs/system/ppo/ff_ippo.yaml:3-24`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/configs/system/ppo/ff_ippo.yaml#L3-L24)).
The runner's reported environment-step denominator is explicitly
`D * updates_per_eval * T * update_batch_size * num_envs`
([`ppo/anakin/ff_ippo.py:442-450`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L442-L450)).

Recurrent PPO carries hidden states through rollout, passes `(observation, done)` to the RNN, and
chunks the rollout into `recurrent_chunk_size` before shuffling chunks and scanning minibatches
([`ppo/anakin/rec_ippo.py:92-164`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/rec_ippo.py#L92-L164);
[`ppo/anakin/rec_ippo.py:293-324`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/rec_ippo.py#L293-L324)).
`ScannedRNN` itself declares `nn.scan(in_axes=0, out_axes=0)` and resets carries from done flags
([`networks/base.py:121-149`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/networks/base.py#L121-L149)).

The shared axis helpers say that leading dimensions are merged by reshape and that
`unreplicate_batch_dim` selects `x[:, 0, ...]` because the second axis is the update-batch copy
([`utils/jax_utils.py:56-72`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/jax_utils.py#L56-L72);
[`utils/jax_utils.py:91-108`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/jax_utils.py#L91-L108)).

### Sebulba execution and device sharding

The current FF-IPPO Sebulba actor runs a CPU `GymToJumanji` vector environment. Its action/value
function is `@jax.jit`; each step moves the observation to the actor device, samples on device,
gets the action back to CPU, then calls `env.step` ([`ppo/sebulba/ff_ippo.py:66-155`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L66-L155)).
`Pipeline._stack_trajectory` stacks actor lists and swaps to `(num_envs, rollout_length, ...)`,
then `Pipeline.put` device-places the trajectory under learner sharding
([`utils/sebulba/pipelines.py:37-42`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/pipelines.py#L37-L42);
[`utils/sebulba/pipelines.py:83-123`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/pipelines.py#L83-L123)).
The bounded queue blocks actors while the learner catches up; its comments explicitly tie this to
avoiding stale/off-policy data and wasted samples.

The learner creates a one-dimensional `Mesh` named `learner_devices`, declares
`model_spec = PartitionSpec()` and `data_spec = PartitionSpec("learner_devices")`, and wraps the
learner in `jax.jit(shard_map(...))` with those specs
([`ppo/sebulba/ff_ippo.py:421-500`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L421-L500)).
The update pmean is over `learner_devices`; minibatch size is based on
`num_envs / len(learner_device_ids)` ([`ppo/sebulba/ff_ippo.py:171-172`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L171-L172);
[`ppo/sebulba/ff_ippo.py:274-341`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L274-L341)).
`ppo_sebulba_checks` requires `num_envs` to be divisible by learner-device count and requires
learner samples to be divisible by minibatches ([`utils/config.py:21-45`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/config.py#L21-L45)).

The runner asserts local and global devices are identical and explicitly says multihost is not
supported, selects actor and learner device IDs, seeds JAX and NumPy, and starts actor threads
([`ppo/sebulba/ff_ippo.py:530-628`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L530-L628)).
The default Sebulba config says `num_envs: 32` per thread, two executor threads, actor/learner
device lists, and queue size five ([`configs/arch/sebulba.yaml:1-25`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/configs/arch/sebulba.yaml#L1-L25)).
After every learner update the code calls `jax.block_until_ready` on parameters and publishes them
through `ParamsSource`; the main loop blocks on `eval_queue.get()` before logging/evaluation
([`ppo/sebulba/ff_ippo.py:375-418`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L375-L418);
[`ppo/sebulba/ff_ippo.py:633-658`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L633-L658)).

The same explicit `jax.jit(shard_map(...))` pattern is present in current Sable Sebulba, with
agent chunking and hidden-state initialization configured before learner compilation
([`sable/sebulba/ff_sable.py:392-510`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/sable/sebulba/ff_sable.py#L392-L510)).

### Environment and batch contracts

`MarlEnv` is a Jumanji-like protocol: `reset(key)`, `step(state, action)`, per-agent counts,
specs, and a state that may carry randomness
([`mava/types.py:45-123`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/types.py#L45-L123)).
The canonical `Observation` stores `agents_view` `(N, features)`, `action_mask` `(N, actions)`,
and optional per-agent `step_count`; global-state observations add `(N, N * features)`
([`mava/types.py:126-156`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/types.py#L126-L156)).

JaxMARL dictionaries are stacked/unstacked along the agent axis and the wrapper splits a JAX key
on reset and every step; its specs make agent-first observations, masks, rewards, and discounts
explicit ([`wrappers/jaxmarl.py:77-84`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/jaxmarl.py#L77-L84);
[`wrappers/jaxmarl.py:208-243`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/jaxmarl.py#L208-L243);
[`wrappers/jaxmarl.py:262-313`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/jaxmarl.py#L262-L313)).
Jumanji wrappers can aggregate individual rewards into repeated team rewards and can tile a global
state per agent ([`wrappers/jumanji.py:43-83`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/jumanji.py#L43-L83)).
`make_env.add_extra_wrappers` applies optional agent IDs/graph conversion, then auto-reset and
episode metrics to JAX environments ([`utils/make_env.py:96-120`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/make_env.py#L96-L120)).

Sebulba creates Gymnasium `AsyncVectorEnv` workers and wraps them with `GymToJumanji`
([`utils/make_env.py:248-283`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/make_env.py#L248-L283)).
`GymToJumanji` formats observations as a vector batch with agent axis, stacks masks, repeats
step-count across agents, stores `real_next_obs`, and maps `discount = 1 - terminated`
([`wrappers/gym.py:273-361`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/gym.py#L273-L361)).
Its `step` marks `StepType.LAST` when either terminated or truncated, but repeats only
`terminated` for the discount; truncation therefore remains bootstrappable in the returned
discount. This is a current semantic detail, not a layout guess.

`AutoResetWrapper` preserves the terminal observation under `extras["real_next_obs"]` and derives
the reset key from the environment state's key
([`wrappers/auto_reset_wrapper.py:29-37`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/auto_reset_wrapper.py#L29-L37);
[`wrappers/auto_reset_wrapper.py:60-99`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/wrappers/auto_reset_wrapper.py#L60-L99)).
Its docstring warns against vmapping this wrapper because reset and step would both be processed
per call; the current Anakin runners still call `jax.vmap(env.step)`. That combination is an
explicit follow-up verification point rather than grounds to assume an older dedicated vmap
wrapper.

### Replay and rollout buffers

On-policy PPO stores `PPOTransition` trees produced by the rollout scan and hands them directly to
the learner ([`systems/ppo/types.py:46-98`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/types.py#L46-L98)).
Anakin recurrent IQL instead creates a Flashbax trajectory buffer with configured sequence length,
period, environment add batch, sample batch, and time-axis capacity, then replicates its state
([`q_learning/anakin/rec_iql.py:143-154`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/q_learning/anakin/rec_iql.py#L143-L154)).
Each action step adds a one-time-axis transition containing `obs`, action, reward, terminal,
term-or-trunc, and `real_next_obs`; training samples `.experience`, aligns current/next time
slices, and swaps replay `(B,T,...)` into RNN `(T,B,...)`
([`q_learning/anakin/rec_iql.py:239-279`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/q_learning/anakin/rec_iql.py#L239-L279);
[`q_learning/anakin/rec_iql.py:283-298`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/q_learning/anakin/rec_iql.py#L283-L298);
[`q_learning/anakin/rec_iql.py:404-423`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/q_learning/anakin/rec_iql.py#L404-L423)).

Anakin FF-ISAC uses a Flashbax item buffer (`max_length`, `min_length=explore_steps`,
`sample_batch_size`, `add_batches=True`), scans acting steps that add transitions, and scans replay
epochs after the exploration fill ([`sac/anakin/ff_isac.py:163-200`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/sac/anakin/ff_isac.py#L163-L200);
[`sac/anakin/ff_isac.py:370-418`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/sac/anakin/ff_isac.py#L370-L418);
[`sac/anakin/ff_isac.py:433-490`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/sac/anakin/ff_isac.py#L433-L490)).

Sebulba recurrent IQL uses `OffPolicyPipeline`: it allocates one Flashbax trajectory buffer per
actor, adds and samples on CPU-jitted functions, concatenates the per-actor samples, and
device-places the result under learner sharding
([`utils/sebulba/pipelines.py:148-206`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/pipelines.py#L148-L206);
[`utils/sebulba/pipelines.py:223-284`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/pipelines.py#L223-L284)).
The runner derives `sample_per_insert` from configured replay ratio, sequence length, actor count,
and epochs, then selects `SampleToInsertRatio` or `BlockingRatioLimiter`
([`q_learning/sebulba/rec_iql.py:581-621`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/q_learning/sebulba/rec_iql.py#L581-L621)).
The limiter blocks insertion/sampling until its ratio and minimum-size conditions are met
([`utils/sebulba/rate_limiters.py:23-118`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/rate_limiters.py#L23-L118)).

The optional advanced FF-IPPO example makes storage layout explicit: it reshapes
`(D, NU, UB, T, NE, ...)` to a flat-buffer batch and jits `buffer.add` with donated state
([`examples/advanced_usage/ff_ippo_store_experience.py:503-551`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/examples/advanced_usage/ff_ippo_store_experience.py#L503-L551);
[`examples/advanced_usage/ff_ippo_store_experience.py:563-593`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/examples/advanced_usage/ff_ippo_store_experience.py#L563-L593)).
Vault writes are optional side effects and must not be folded into core learner throughput.

### RNG, compilation, synchronization, and timing

Anakin seeds one JAX PRNGKey from `config.system.seed`, splits network keys and reset/action
streams, and stores the evolving key in learner state
([`ppo/anakin/ff_ippo.py:311-313`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L311-L313);
[`ppo/anakin/ff_ippo.py:416-429`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L416-L429)).
Sebulba additionally seeds a NumPy generator and draws int32 environment seeds per actor thread;
its JAX actor keys are placed on actor devices
([`ppo/sebulba/ff_ippo.py:542-544`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L542-L544);
[`ppo/sebulba/ff_ippo.py:588-614`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L588-L614)).
The Gym evaluator likewise uses NumPy seeds, while its action function is jitted on the first
actor device ([`evaluator.py:231-244`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L231-L244);
[`evaluator.py:264-307`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L264-L307)).

Anakin training starts a wall timer immediately before `learn`, calls `jax.block_until_ready`,
and then reports `steps_per_second`; the JAX evaluator similarly times `pmap(eval_fn)` and waits
before calculating SPS ([`ppo/anakin/ff_ippo.py:465-495`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/anakin/ff_ippo.py#L465-L495);
[`evaluator.py:160-170`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L160-L170)).
There is no explicit warm-up exclusion, so first-call compilation is included in this code-level
measurement. Sebulba records `time.monotonic()` durations for parameter fetch, device action,
environment step, queue put/get, learning, and the per-evaluation learner interval
([`utils/sebulba/utils.py:27-39`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/sebulba/utils.py#L27-L39);
[`ppo/sebulba/ff_ippo.py:114-155`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L114-L155)).
The Sebulba main loop logs pipeline size and uses a blocking learner result queue
([`ppo/sebulba/ff_ippo.py:633-653`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/systems/ppo/sebulba/ff_ippo.py#L633-L653)).

### Evaluation and logging

The JAX evaluator chooses vmapped evaluation environments from device count and configured episode
count, scans each environment to `time_limit + 1`, extracts the first done metrics, then scans
episode loops inside `pmap` ([`evaluator.py:67-80`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L67-L80);
[`evaluator.py:116-169`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L116-L169)).
Sebulba evaluation loops CPU vector environments until all parallel episodes finish, moves each
action back to CPU, stacks host timesteps, and extracts first-done metrics
([`evaluator.py:255-319`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/evaluator.py#L255-L319)).

`MavaLogger` distinguishes ACT, TRAIN, EVAL, ABSOLUTE, and MISC events; TRAIN values are reduced
to means while other arrays receive mean/std/min/max summaries
([`utils/logger.py:42-48`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/logger.py#L42-L48);
[`utils/logger.py:124-150`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/logger.py#L124-L150)).
Neptune is async for Anakin and sync for Sebulba because the source notes async logging can deadlock
Sebulba ([`utils/logger.py:242-269`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/logger.py#L242-L269)).
The JSON sink keeps only `episode_return/mean`, `win_rate`, and `steps_per_second`, and writes only
EVAL/ABSOLUTE events ([`utils/logger.py:312-370`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/mava/utils/logger.py#L312-L370)).

## Observed versus inferred performance implications

The following are inferences from the observed code, not measurements:

1. Anakin concentrates action, environment, rollout, GAE, optimization, and repeated updates
   inside a compiled transform with explicit device, update-batch, environment, and time axes.
   Its gradient pmeans imply cross-device and update-batch reductions. The denominator counts all
   selected environment replicas, so any comparison must preserve `D`, `UB`, `NE`, `T`, and update
   count.
2. Sebulba exposes a different cost model: CPU vector environment work and host/device transfers
   are outside the learner `shard_map`; bounded queue waits and parameter publication control
   freshness. More actor threads or devices can change both overlap and waiting, so source layout
   alone cannot predict a speedup.
3. Replay memory and data movement scale with configured environment/actor counts, sequence or
   item capacity, rollout length, sample batch, and queue size. Exact peak memory is absent from
   this source scan; no memory claim is made.
4. The timer waits for asynchronous JAX work, but the first invocation is not warmed up. The
   reported SPS is therefore a code-level wall-time statistic whose compile/logging/evaluation
   boundaries must be recorded, not a steady-state or cross-library speedup.
5. The auto-reset warning and current `vmap(env.step)` call require a targeted reproduction before
   declaring an optimization opportunity. Changing that wrapper or terminal observation behavior
   would change semantics.

The README reports a historical 45-scenario/6-suite benchmark and ten seeds
([`README.md:124-151`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/README.md#L124-L151));
this task did not reproduce it and does not claim any measured speedup.

`toy45min` and `UAV12h` are pending normalization-investigation thresholds supplied by the study
request. No current source line guarantees either duration or task scale, and neither threshold
may be made “reachable” by silently changing environment semantics, precision, RNG, rollout,
buffer, or comparison definitions.

## License evidence

The repository includes Apache License 2.0. The short relevant grant is “perpetual, worldwide,
non-exclusive, no-charge, royalty-free, irrevocable copyright license” (local [`LICENSE:66-71`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/LICENSE#L66-L71)).
The notice in source files identifies InstaDeep Ltd and points to the Apache 2.0 text
([`LICENSE:1-5`](https://github.com/instadeepai/Mava/blob/83f7f0d19d6fdbe07264bb226a64baf8a0b17514/LICENSE#L1-L5)).
This is a license observation, not legal advice.

