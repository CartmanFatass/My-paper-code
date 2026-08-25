# CCIC B1 revision-08 prospective resource reconciliation intake

```text
direction=covariance_calibrated_information_clock
treatment_revision=CCIC-B1-SCIENCE-20260813-08
owner=EM_covariance_calibrated_information_clock
source=same_direction_CM_read_only_static_reconciliation
scientific_activity_started=false
result_observed=false
provider_contacted=false
compute_authorized=false
```

## Conclusion

The inherited 90-minute wall envelope is not a credible static bound for the
frozen Stage-1 object. Same-direction review estimates 9--13 single-CPU hours
and uses 12--16 hours as the conservative planning interval for exactly 240,000
updates, at most 53,084,160 rollout ticks, and about 7.23 million replay tuples.
Even the conservative ideal eight-way lower bound is 1.5--2 hours before serial
reference/certificate/inference work and process, I/O, and replay overhead.

This does not terminate the direction and exposes no causal contradiction.
Counter-addressed random tapes, seed-block estimators, and complete-block
retention make scheduling irrelevant across seed blocks. Parallelism is
science-neutral only when the complete seed block is indivisible.

## Exact prospective resource and concurrency law

- Wall time is at most 180 minutes from fresh-root creation through durable
  terminal finalization.
- Aggregate process-tree CPU use is at most 20 hours, defined as the sum of
  user-plus-kernel CPU seconds of the coordinator and all live or exited child
  processes divided by 3,600.
- Aggregate process-tree peak RSS is at most 16 GiB, defined as the maximum over
  time of the simultaneous resident-byte sum for the coordinator and all live
  descendants.
- At most eight numerical CPU execution slots may be active simultaneously.
  There is one worker process per seed block, at most eight workers concurrent,
  and exactly one numerical thread per worker. `OMP_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` equal `1`
  in every worker. The coordinator performs no numerical work while workers are
  active.
- Temporary plus retained disk use is at most 2 GiB, defined as the sum of
  logical regular-file lengths below the fresh output root, including staging.
- Each worker owns one fixed block's models, state, snapshot bank, complete
  evaluation, diagnostics, and offline work replay. It preserves every frozen
  within-seed module/update/minibatch-slot/row/cell/arm/episode/reduction order.
- PID, worker identity, launch order, completion order, and concurrency never
  enter an RNG address, input, endpoint, or estimator. Arms stay paired inside
  the block. A replay tuple's shared `PREVALIDATE` object and both fusions stay
  inside one worker. Neither arms nor tuples may be split across workers.
- The reference is either one deterministic read-only memory-mapped object or
  bitwise-identical immutable copies. Sharing cannot change values or order.
- After the preactivity certificate, all workers wait on a coordinator-owned
  interprocess barrier. The coordinator durably records and releases the first-
  update boundary before any update zero. If that record exists but no update
  completes, activity is conservatively treated as begun.
- Each complete block is retained atomically at its fixed `(b,seed)` address.
  Inference begins only after blocks `0,...,31` all exist and are consumed in
  increasing `b` order. Partial, missing, failed, reordered, or substituted
  blocks yield no estimator. The coordinator does not retain all 32 full seed
  objects in memory.
- Monitoring covers the entire process tree and fails closed on any wall,
  aggregate CPU-hour, aggregate RSS, numerical-slot, or disk violation.
  Scheduler, process, serialization, and monitoring overhead is not matched
  fusion work and cannot pad either arm.

## Boundaries and remaining unknown

The DGP, treatment, comparators, axes, seeds, tapes, per-seed estimators,
bootstrap, multiplicity, work-replay formulas, activity criterion, result
branches, claim ceiling, second surface, and UAV bridge are unchanged. Static
resource estimates are not runtime evidence. Whether this implementation fits
the expanded envelope remains a CM technical measurement question after Pro
closure and a separate Root compute lease. No benchmark, test, construction,
provider action, training, evaluation, or result-bearing computation occurred.
