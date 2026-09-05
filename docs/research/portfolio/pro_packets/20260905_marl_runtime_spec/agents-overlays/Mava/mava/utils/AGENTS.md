# `mava/utils/` navigation overlay

This directory holds shared environment construction, axis helpers, logging, checkpointing, and
Sebulba coordination utilities. Preserve upstream source and treat this file as local guidance.

## Navigation and boundary

- `make_env.py`: registry, wrapper order, JAX environments, and Gym vector construction.
- `jax_utils.py`: merge/swap/unreplicate leading axes; these helpers do not alter semantics.
- `sebulba/pipelines.py`, `sebulba/rate_limiters.py`, `sebulba/utils.py`: queues, replay, timing,
  parameter publication, and stop behavior.
- `logger.py`, `checkpointing.py`: observable outputs and optional persistence.

Environment reward/discount/terminal and `real_next_obs`, PRNG split order, queue backpressure,
replay ratio, device placement, and timing boundaries are part of the study contract. Utility
refactors must preserve them or be called a semantic change.
