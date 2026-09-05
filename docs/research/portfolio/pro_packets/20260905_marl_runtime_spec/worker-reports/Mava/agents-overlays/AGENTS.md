# Mava navigation overlay

This is a local, additive navigation overlay for the fixed checkout at
`83f7f0d19d6fdbe07264bb226a64baf8a0b17514` (`id-mava` 0.2.0). It records where the current
source exposes execution and performance semantics for the HMASD study. It does not change
upstream source, and any upstream `AGENTS.md` must be retained if one is added later.

## Navigation

- `README.md`, `pyproject.toml`, `mava/__init__.py`: project identity, dependencies, and version.
- `mava/systems/ppo/`: on-policy PPO Anakin and Sebulba entry points.
- `mava/systems/q_learning/`: recurrent IQL with Flashbax replay, in both architectures.
- `mava/systems/sac/anakin/`: continuous-control SAC with a JAX item buffer.
- `mava/systems/sable/`: Sable policy, including explicit Sebulba `shard_map`.
- `mava/evaluator.py`, `mava/utils/logger.py`: evaluation, timing, and output contracts.
- `mava/utils/sebulba/`: actor/learner pipelines, queues, sharding, and rate limiting.
- `mava/wrappers/`, `mava/utils/make_env.py`: environment API, vectorization, reset, metrics.
- `mava/configs/`: architecture, system, environment, and logger defaults.
- `reports/Mava/CORE_EVIDENCE.md` and `reports/Mava/ROOT_RETURN.md`: study outputs.

## Entry and boundary map

Anakin entry points are Hydra scripts under `mava/systems/*/anakin/`. The normal data path is
device `pmap`, update-batch `vmap`, and time `lax.scan`; environment batches are shaped per
device as `(update_batch, num_envs, ...)`. Sebulba entry points are under `*/sebulba/`: CPU
`AsyncVectorEnv` actor threads send rollout data through a bounded pipeline to a learner whose
data axis is `shard_map`-partitioned across `learner_devices`. Off-policy paths add Flashbax
buffers and, for Sebulba, a sample/insert rate limiter.

The semantic boundary is the current source contract: observation/action-mask layout, reward and
termination/discount meaning, `real_next_obs` under auto-reset, PRNG split order, rollout and
replay sampling semantics, and evaluation/logging definitions. Performance notes may describe
these semantics but must not silently tune or replace them. `toy45min` and `UAV12h` are pending
normalization thresholds; this overlay does not claim either is reachable without a specified
semantic change.


