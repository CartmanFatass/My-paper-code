# `mava/systems/sac/` navigation overlay

Current SAC code is under `anakin/`; there is no Sebulba SAC runner in this checkout.

## Navigation and boundary

`anakin/ff_isac.py` initializes actor, twin online/target Q networks, entropy parameters, and a
Flashbax item buffer. `act` scans environment steps and appends transitions; `train` scans replay
updates with delayed actor/alpha updates; outer `pmap` and update-batch `vmap` carry device/batch
replicas. Preserve action/reward/done/next-observation semantics, target-network Polyak updates,
and exploration fill before treating a buffer or transform as a performance substitution.

