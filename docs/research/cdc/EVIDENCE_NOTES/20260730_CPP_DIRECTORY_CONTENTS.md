# What is actually in `cpp/`, checked rather than assumed

Date: 2026-07-30
Status: untracked directory supplied by the user, left in place and untouched.

Two files were reported elsewhere as "a byte-identical copy of the tracked kernel,
delete it". Half right, and the other half matters more.

## `cpp/uav_geometry_backend.cpp`

**Byte-identical** to the tracked `ha_ctse_process/native/uav_geometry_backend.cpp`
(SHA-256 equal). No loader reads the `cpp/` copy -- `uav_cpp_backend.py` builds from
the tracked path. So it is a duplicate, and the only hazard is editing the wrong
one.

**Not deleted.** It is user-supplied material sitting outside version control, and
removing someone else's file to tidy a duplicate is not a call to make unasked.

## `cpp/continuous_roster_toy_backend.cpp` -- a DIFFERENT environment

This one has **no tracked counterpart**, and it is the more interesting file. It
exposes exactly the shape the toy-env profile says would pay:

```text
observe_six_batch(capabilities, priorities, loads, target_mixes,
                  active_mask, log_counts, time_fraction)
reward_batch(...)
```

Batched observation and reward, one boundary crossing for a whole batch.

**But it is not our toy environment, and adopting it would be a category error.**
Checked before reporting it as a find:

```text
                        continuous_roster_toy      generic_short_dynamic_roster
observation width       6   ({batch, capacity, 6})  15  (OBSERVATION_DIM)
critic/state width      6                            8  (state_dim)
inputs                  capabilities, priorities,    owner flag, short_streak,
                        loads, target_mixes,         contributed_current_wave,
                        log_counts, time_fraction    active_steps, previous_action
```

The "six" in the name is the observation width, not the lifecycle count -- which is
the coincidence that made it look like a match, since our env has
`MAX_LIFECYCLES = 6`.

## What is worth taking from it

The **pattern**, not the code: batched observe and reward computed in one native
call. The measured toy-env profile
(`20260730_TOY_ENV_PROFILE_BATCHING_DECISION.md`) says the cost is per-member and
per-env Python call count -- `_float_array` validation and `active_keys` signature
rebuilds -- which is precisely what a single batched native call retires and what
cross-env Python batching does not.

That raises, but does not settle, whether a native `observe_batch` for
`generic_short_dynamic_roster` is worth building. It would need the same discipline
the UAV kernel got: a bitwise oracle against the Python implementation over the
whole matrix before any use, and the pinned digest
`50f7385f916d0445a79f6b067a65a6ba308455e3d97adef81af8b2a1f00445e7` unchanged.

Not started, not recommended here -- recorded so the next reader does not have to
re-derive that these two files are not interchangeable.
