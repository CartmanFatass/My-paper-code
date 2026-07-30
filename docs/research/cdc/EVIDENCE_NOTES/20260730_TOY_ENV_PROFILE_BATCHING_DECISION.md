# Toy env: where the time is after 1.92x, and why batching is not the next move

Date: 2026-07-30
Measured on a quiet box, `DynamicRosterEventEnv`, all-zero actions, 4000 steps
after a 200-step warm-up.

```text
throughput   6269 steps/s   (159.5 us/step)
```

## The question

Cross-env batching was authorized ("允许batching") and was the obvious next
acceleration step. Batching amortizes **per-step** overhead across B environments.
It does nothing for **per-env sequential bookkeeping**. So the decision needs the
self-time distribution, not a guess.

## Self-time profile

```text
                                                  tottime   cumtime    calls
{method 'reduce' of 'numpy.ufunc'}                  0.123              72426
_observation_matrix                                 0.120     0.232    12002
numpy fromnumeric _wrapreduction                    0.091     0.248    72426
active_keys                                         0.087     0.146    40356
{method 'copy' of 'numpy.ndarray'}                  0.078             143220
_shared_observation_prefix                          0.064     0.104    11951
numpy fromnumeric all                               0.059     0.303    71916
_event_snapshot                                     0.041     1.126     8002
                                          (total profiled 1.584 s)
```

`_event_snapshot` is **71% cumulative**. The two identifiable consumers inside it,
resolved by walking the profiler's caller graph rather than guessing:

```text
np.all       35,810 of 35,966 calls  <-  variable_roster_event.py:88(_float_array)
             = 18 calls per step, 0.158 s cumulative  (~20% of step time)

active_keys  20,181 calls = 10 per step, 0.072 s cumulative, from SEVEN sites:
             _shared_observation_prefix 5976, _critic_global_features 4002,
             _event_snapshot 4002, observe 2000, _update_persistent_duty 2000,
             _update_short_duty 2000, _open_wave_if_due 201
```

## Decision: do NOT implement batching next

Both dominant costs are **per-member and per-env Python call counts** --
`_float_array` validating one observation row at a time, and `active_keys`
rebuilding its cache signature per call. Stepping B environments in lockstep does
not reduce either: B envs perform B times the validations and B times the signature
builds. Batching would add real complexity to the snapshot path for a share of the
time that it cannot touch.

This is recorded because the opposite was about to be implemented on the assumption
that batching is generically the next win. The assumption was untested, and the
measurement contradicts it.

## The two measured candidates, with their risk

**1. Validate the observation matrix once instead of once per row (~20%).**
`_observation_matrix` already builds the whole `(n, OBSERVATION_DIM)` array, and
then each row is passed separately through `_float_array`, which runs
`np.all(np.isfinite(row))`. One `np.all` over the matrix checks **exactly the same
values** -- identical coverage, `n` numpy call overheads collapsed to 1. This is a
pure call-count change, not a weakening of the guard.

The care required: `_float_array` lives in `variable_roster_event.py` and is
presumably shared with other environments, so the per-row check cannot simply be
deleted. It needs an explicit "already validated" path, and the guard must be
watched failing on a non-finite value under both paths.

**Do not "optimize" this by arguing the values are finite by construction.** They
are, and that is exactly the reasoning that produces a silent corruption years
later. The point of the change is fewer calls at equal coverage, nothing else.

**2. `active_keys` called 10x per step from seven sites (~9%).** The cache added
earlier avoids recomputing the key tuple, but it rebuilds its signature --
`(self.time, tuple(state.status for state in self.lifecycles.values()))` -- on
every call, which is why the line-313 generator shows 282,492 calls. Hoisting
`active_keys` to once per snapshot and threading it through the seven call sites
removes nine of the ten.

Lower risk than (1), smaller payoff, and it touches more call sites.

## Constraint on any of it

The toy env has a pinned bit-exact equivalence digest,
`50f7385f916d0445a79f6b067a65a6ba308455e3d97adef81af8b2a1f00445e7`
(`tests/dynamic_roster_testbed_equivalence_test.py`, 40 episodes / 3200 steps).
Any change here must leave it unchanged, and must also keep
`test_handed_out_transaction_arrays_are_independent` green -- the digest reads
values and cannot see aliasing, which is why `_float_array`'s `.copy()` is
load-bearing and must survive whatever happens to its validation.

Nothing in this note is implemented. It exists so the next attempt starts from the
measurement instead of from the assumption.
