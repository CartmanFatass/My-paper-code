# `mava/systems/ppo/` navigation overlay

Current PPO variants are split by runtime architecture. Keep source files and any upstream
guidance intact.

## Entrypoints

- `anakin/ff_ippo.py`, `anakin/ff_mappo.py`, `anakin/rec_ippo.py`, `anakin/rec_mappo.py`.
- `sebulba/ff_ippo.py`, `sebulba/ff_mappo.py`, `sebulba/rec_ippo.py`, `sebulba/rec_mappo.py`.
- `types.py`: `PPOTransition`, recurrent hidden states, and learner-state records.

## Boundary

PPO Anakin is end-to-end JAX for JAX environments: action/value, environment `vmap`, rollout
`scan`, GAE, minibatch/epoch scans, and outer update scans are compiled and pmean over batch and
device axes. PPO Sebulba keeps Gym interaction on actor threads, transfers observations/actions
between CPU and actor devices, and pmean-reduces gradients across `learner_devices`. The two
paths have different timing and staleness boundaries; do not compare their SPS as if they were
the same execution path.
