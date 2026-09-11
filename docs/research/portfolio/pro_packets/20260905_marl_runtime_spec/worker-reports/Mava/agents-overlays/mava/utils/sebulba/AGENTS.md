# `mava/utils/sebulba/` navigation overlay

The shared Sebulba coordination layer is in `pipelines.py`, `rate_limiters.py`, and `utils.py`.

## Navigation and boundary

`Pipeline` serializes trajectory stacking, device placement, and bounded queue handoff.
`OffPolicyPipeline` owns one CPU Flashbax buffer per actor, rate-limited insertion/sampling, and
learner-sharded batches. `RecordTimeTo` records host monotonic durations; `ParamsSource` publishes
learner parameters to actor devices. Queue time, CPU replay time, host/device transfer, learner
compute, and readiness synchronization must be reported as distinct components.
