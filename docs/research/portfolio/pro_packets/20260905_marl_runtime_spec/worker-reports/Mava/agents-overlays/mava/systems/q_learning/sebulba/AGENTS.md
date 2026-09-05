# `mava/systems/q_learning/sebulba/` navigation overlay

`rec_iql.py` uses the shared Sebulba off-policy pipeline.

## Navigation and layout

Actor threads collect `(num_envs, rollout_length, ...)` transition sequences. `OffPolicyPipeline`
keeps one Flashbax trajectory buffer per actor, adds/samples on CPU, concatenates sampled batches,
and places the result on a learner `NamedSharding`. `SampleToInsertRatio` or
`BlockingRatioLimiter` controls when insertion and sampling proceed. The learner uses
`shard_map` and scans epochs over `(B,T,...)` replay data after converting it to `(T,B,...)`.

## Boundary

Actor count, buffer-per-actor ownership, minimum sequence length, replay ratio, limiter error
tolerance, CPU/device transfers, and latest-parameter publication are runtime semantics. A
throughput specification must preserve the limiter and report queue/learner wait time rather than
folding it into environment compute.


