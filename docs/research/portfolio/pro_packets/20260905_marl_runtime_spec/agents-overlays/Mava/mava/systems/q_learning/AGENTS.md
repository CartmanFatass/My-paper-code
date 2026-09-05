# `mava/systems/q_learning/` navigation overlay

This directory contains recurrent independent Q-learning runners and their data contracts.

## Navigation

- `types.py`: transition stores `obs`, `next_obs`, terminal and truncation flags.
- `anakin/rec_iql.py`: device-replicated trajectory replay and compiled act/train loop.
- `sebulba/rec_iql.py`: actor-thread rollouts, per-actor CPU replay, rate-limited sampling.

## Boundary

Replay data is `(B,T,...)`; the recurrent network consumes `(T,B,...)`, so axis swapping is
intentional. `real_next_obs` is retained because auto-reset replaces the visible terminal
observation. The terminal/term-or-trunc distinction, target-network update, replay sequence
length, and sampling ratio are semantic choices. Device sharding or CPU replay placement may be
optimized only while preserving those choices.

